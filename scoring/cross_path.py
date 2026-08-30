"""Put two scoring paths side by side CELL BY CELL, and name where they disagree.

Not the same question as `head_to_head.py`, which asks how well each side matches
GOLD. This asks whether the two sides agree WITH EACH OTHER, which is the question
the equivalence goal actually rests on: every recorded number is a comparison, and
a comparison is meaningless while the scorers differ about the rules.

    python3 cross_path.py paper_mini_v8 cli_v8
    python3 cross_path.py paper_mini_v8 cli_v8 --slots      # name the slot
    python3 cross_path.py paper_mini_v8 cli_v8 --item Q4b   # one item, per cell

WHY IT EXISTS. `equivalence.py --enforcement` compares DECLARATIONS, so a rule one
side applies and the other does not is invisible to it whenever the rule is not
declared -- written in guidance prose, or parked in `SLOT_NOTES`, which the paper
scorer never reads. Two such divergences were found by running this comparison as
a throwaway script on 2026-08-28, both stable in 3 of 3 runs and neither declared
anywhere:

    1a/p6    paper 0.0 against web 6.0-8.0 -- the whole item, because five `1a:*`
             SLOT_NOTES entries reach the web prompt and not the CLI's
    Q4b/p4   paper 2.0 against web 3.5, and GOLD IS 2.0 -- the paper path charges
             what the graders charged and the web path does not

Neither could have been found by comparing prompt text: both sides are given the
same guidance verbatim, and the prompt audit reports 0 undeclared gaps. There is
no textual difference to find, only an effect, so the detector has to be this.

THREE ARTIFACT SHAPES, because three programs write them, and the units differ:

    paper     score.py            `participant_NNN.json`, possibly nested in
                                  r*/h*/ -- items[].score, absolute points
    harness   agreement.py        `<item>.runs.json` -- results[].score keyed by
                                  participant_id, absolute points
    app       agreement_app.py    `<item>.runs.json` -- results[].cell as
                                  "p12/Q4b", and grader.score as a FRACTION of
                                  sheet_max, so it is multiplied back up here

Getting that last one wrong would report every app cell as diverging.

WHAT "NEVER AGREE" MEANS, and what it does not. A cell is reported when the two
sides' score SETS are disjoint -- no run on either side ever reached a value the
other side reached. That is deliberately stricter than comparing medians: it
excludes cells where the paths overlap and merely differ in how often. With three
runs a side it is still a coarse test, and it says nothing about WHY.

Some divergence is correct and declared. The two paths are fed the student's work
differently -- the web has one box per field, the paper scorer one segmented block
per item -- so 1c, whose web chart is drawn from typed data a paper student cannot
supply, diverges on 15 of 20 cells BY DESIGN. Declared items are marked so they
can be read past rather than rediscovered.

ERA IS CHECKED WHEN THE ARTIFACTS RECORD ONE. Comparing two directories from
different prompt versions confounds VERSION with PATH, and that is not
hypothetical: the first scoping run found 18 cells diverging in both of two
comparisons and 17 more in only one, which is what prompt drift looks like when
you cannot see it -- those 17 were unattributable to anything.

The fix was in the writers, not here. All three now stamp `era` --
measured.era_stamp: the git commit, whether the tree was dirty, and each item's
prompt and scorer fingerprints, from the same functions the ledger uses. So this
compares the two sides' stamps per item and reports any item whose PROMPT differs
as era-confounded, separately from the divergence table, because such a cell says
nothing about the paths.

Artifacts written before that landed carry no `era`, and for those this falls back
to file mtime and says plainly that matching the eras is the caller's job. An
unstamped comparison is not wrong, it is just unverified, and it should say so.
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import time


_BASIS_CACHE: dict = {}


def slot_basis(item_id: str) -> dict:
    """slot -> what decides it, from enforcement.slot_basis. Cached per item.

    This is what makes a named slot actionable. A divergence on a COMPUTED slot
    means the two sides ran different arithmetic: one right answer, and a bug. A
    divergence on a PROSE slot means they read the same instruction and landed
    differently, which no static check can see -- and `enforcement.PROSE_ONLY_SLOTS`
    says whether that hazard was known in advance or is new.
    """
    if item_id in _BASIS_CACHE:
        return _BASIS_CACHE[item_id]
    basis: dict = {}
    try:
        import enforcement as ENF
        import handouts as H
        import olx_prompts as O
        item = H.config(O.HANDOUT[item_id])["rubric"].BY_ID[item_id]
        basis = ENF.slot_basis(item)
        declared = {k for (i, k) in getattr(ENF, "PROSE_ONLY_SLOTS", {}) if i == item_id}
        for k, v in list(basis.items()):
            if v == "prose+rule":
                basis[k] = v + (", declared" if k in declared else ", UNDECLARED")
    except Exception:
        basis = {}
    _BASIS_CACHE[item_id] = basis
    return basis


def _merge_era(acc: dict, era: dict | None) -> None:
    """Fold one artifact's era stamp into the side's stamp.

    A directory is many files and they should all carry the same stamp; if they
    do not, the FIRST wins and `mixed` records that the side is not one era. That
    is worth knowing on its own -- a directory assembled from two runs is exactly
    the case this whole mechanism exists to catch.
    """
    if not isinstance(era, dict):
        return
    if era.get("git") and not acc.get("git"):
        acc["git"] = era["git"]
        acc["dirty"] = era.get("dirty")
    elif era.get("git") and acc.get("git") != era["git"]:
        acc["mixed"] = True
    for it, st in (era.get("items") or {}).items():
        acc["items"].setdefault(it, st)


def _load_paper(root: str) -> tuple[dict, dict, dict]:
    """score.py output. Nested one level for multi-run sweeps (r*/h*/)."""
    scores: dict = collections.defaultdict(list)
    verdicts: dict = collections.defaultdict(list)
    eras: dict = {"items": {}}
    pats = (os.path.join(root, "participant_*.json"),
            os.path.join(root, "*", "*", "participant_*.json"),
            os.path.join(root, "*", "participant_*.json"))
    seen = set()
    for pat in pats:
        for f in glob.glob(pat):
            if f in seen:
                continue
            seen.add(f)
            try:
                doc = json.load(open(f))
            except Exception:
                continue
            pid = doc.get("participant_id")
            _merge_era(eras, doc.get("era"))
            for it in doc.get("items") or []:
                if it.get("score") is None or pid is None:
                    continue
                key = (it["item_id"], pid)
                scores[key].append(float(it["score"]))
                # score.py records per-component verdicts under credit_checks.
                cc = it.get("credit_checks") or []
                v = {}
                for c in cc:
                    if isinstance(c, dict) and c.get("what"):
                        v[c["what"]] = c.get("verdict") or (
                            "met" if c.get("met") else "absent")
                verdicts[key].append(v)
    return scores, verdicts, eras


def result_cell(r: dict) -> tuple | None:
    """One `results[]` entry -> (item, participant, points_or_None, verdicts).

    Returns None only when the entry cannot be KEYED at all; a readable cell
    that simply has no score comes back with points None, because "this cell
    failed to score" and "this file has an entry I do not understand" are
    different facts and the callers treat them differently -- cross_path skips
    an unscored cell, the ledger counts it against the item.

    Both artifact shapes are read here, in one place, because the app stores
    `grader.score` as a FRACTION of `sheet_max` while every other writer stores
    absolute points. A second copy of that conversion is a second chance to
    forget the multiply, which would silently read every app cell as diverging.
    """
    if "cell" in r:                                   # the app
        cell = str(r.get("cell") or "")
        if "/" not in cell:
            return None
        pid_s, item = cell.split("/", 1)
        try:
            pid = int(pid_s.lstrip("pP"))
        except ValueError:
            return None
        raw = (r.get("grader") or {}).get("score")
        mx = r.get("sheet_max")
        pts = None if raw is None or mx is None else float(raw) * float(mx)
        return item, pid, pts, dict(r.get("verdicts") or {})
    if "item_id" in r:                                # score.py, the paper scorer
        # Its file is per (run, handout, PARTICIPANT) with an `items[]` list, so
        # the participant is carried by the caller rather than the entry. Verdicts
        # live in `credit_checks` as {what, met, ...} instead of a verdict map;
        # folded to met/absent so the shape matches the other two readers and
        # nothing downstream has to know which scorer it came from.
        s = r.get("score")
        checks = {c.get("what"): ("met" if c.get("met") else "absent")
                  for c in (r.get("credit_checks") or []) if c.get("what")}
        return (r["item_id"], r.get("_pid"),
                None if s is None else float(s), checks)
    pid = r.get("participant_id")                     # the python harness
    if pid is None or not r.get("item"):
        return None
    s = r.get("score")
    ch = r.get("checks") or {}
    return (r["item"], pid, None if s is None else float(s),
            dict(ch) if isinstance(ch, dict) else {})


def _load_runs(root: str) -> tuple[dict, dict, str, dict]:
    """agreement.py or agreement_app.py output, told apart by their result keys."""
    scores: dict = collections.defaultdict(list)
    verdicts: dict = collections.defaultdict(list)
    kind = "harness"
    eras: dict = {"items": {}}
    for f in glob.glob(os.path.join(root, "*.runs.json")):
        try:
            doc = json.load(open(f))
        except Exception:
            continue
        _merge_era(eras, doc.get("era"))
        for run in doc.get("runs") or []:
            for r in run.get("results") or []:
                got = result_cell(r)
                if got is None:
                    continue
                item, pid, pts, vd = got
                if "cell" in r:
                    kind = "app"
                if pts is None:
                    continue
                scores[(item, pid)].append(pts)
                verdicts[(item, pid)].append(vd)
    return scores, verdicts, kind, eras


def load(root: str) -> tuple[dict, dict, str, dict]:
    """Whichever shape this directory holds, normalised to absolute points."""
    if glob.glob(os.path.join(root, "*.runs.json")):
        return _load_runs(root)
    s, v, e = _load_paper(root)
    if not s:
        raise SystemExit(
            f"{root}: no artifacts recognised. Expected `*.runs.json` "
            f"(agreement.py or agreement_app.py) or `participant_*.json` "
            f"(score.py), the last optionally nested in r*/h*/")
    return s, v, "paper", e


def _span(root: str) -> str:
    """The file-time span of a side, since no artifact records its prompt sha."""
    ts = []
    for pat in ("*.runs.json", "participant_*.json", "*/*/participant_*.json",
                "*/participant_*.json"):
        ts += [os.path.getmtime(f) for f in glob.glob(os.path.join(root, pat))]
    if not ts:
        return "no dated files"
    fmt = "%Y-%m-%d %H:%M"
    lo, hi = time.strftime(fmt, time.localtime(min(ts))), \
        time.strftime(fmt, time.localtime(max(ts)))
    return lo if lo == hi else f"{lo} .. {hi}"


def declared_items() -> set:
    """Items carrying a declared scoring divergence, so they read as expected.

    Read from each entry's `items` FIELD, not by searching the entry's prose. The
    first version searched the text, and it marked a synthetic Q1 as declared
    because "Q1" appears somewhere in another entry's reasoning -- a false
    `declared` hides exactly the divergence this tool exists to surface, so it is
    the one error here that must not be tolerated.
    """
    try:
        import olx_prompts as O
    except Exception:
        return set()
    out = set()
    for d in getattr(O, "SCORING_DIVERGENCES", ()) or ():
        if not isinstance(d, dict):
            continue
        got = d.get("items") or d.get("item")
        if isinstance(got, str):
            out.add(got)
        elif isinstance(got, (list, tuple, set)):
            out.update(str(x) for x in got)
    return out


def compare(left: str, right: str, item_filter: str | None = None,
            show_slots: bool = False, min_runs: int = 1) -> int:
    ls, lv, lkind, le = load(left)
    rs, rv, rkind, re_ = load(right)
    lname, rname = os.path.basename(left.rstrip("/")), os.path.basename(right.rstrip("/"))

    print(f"{lname}  ({lkind})   {_span(left)}"
          + (f"   git {le.get('git','')[:9]}" if le.get("git") else "   NO ERA STAMP"))
    print(f"{rname}  ({rkind})   {_span(right)}"
          + (f"   git {re_.get('git','')[:9]}" if re_.get("git") else "   NO ERA STAMP"))

    # Items whose PROMPT differed between the two runs. Such a cell cannot speak
    # about the paths: version and path are confounded in it.
    confounded = set()
    if le.get("items") and re_.get("items"):
        # PER SIDE, when both artifacts carry the side-aware stamp. The CLI
        # consumes only SOME of an <LLMAction>'s attributes -- it takes the item
        # max, the slots and the cover/equals/derived groups from the RUBRIC --
        # so a web-only attribute changing leaves the CLI's input untouched.
        # Comparing whole-section hashes reports those runs as confounded and
        # asks for a re-run of a side that cannot have moved. Adding `max="5"` to
        # Q4a, a web-only fix for a web-only defect, did exactly that.
        #
        # `prompt_sha_cli` is the harness's own view. Both artifacts must carry
        # it: an artifact predating the stamp falls back to the whole-section
        # comparison, which is stricter and never wrong, only sometimes coarse.
        for it in set(le["items"]) & set(re_["items"]):
            L, R = le["items"][it] or {}, re_["items"][it] or {}
            harness_pair = "harness" in (lkind, rkind) and "app" in (lkind, rkind)
            a = b = None
            if harness_pair and L.get("prompt_sha_cli") and R.get("prompt_sha_cli"):
                a, b = L["prompt_sha_cli"], R["prompt_sha_cli"]
            if a is None:
                a, b = L.get("prompt_sha"), R.get("prompt_sha")
            if a and b and a != b:
                confounded.add(it)
        if confounded:
            print(f"\nERA MISMATCH on {len(confounded)} item(s): "
                  f"{', '.join(sorted(confounded))}")
            print("Their prompts differ between the two runs, so any divergence "
                  "there is\nversion, path, or both. Excluded from the table "
                  "below; re-run one side.")
        else:
            print("\nera CHECKED: every item common to both sides ran against the "
                  "same prompt")
    else:
        print("\nERA NOT CHECKED: one or both sides predate era stamping "
              "(measured.era_stamp),\nso version cannot be told from path here. "
              "Matching the eras is yours to do.")
    print()

    common = sorted(k for k in (set(ls) & set(rs))
                    if (item_filter is None or k[0] == item_filter)
                    and k[0] not in confounded
                    and len(ls[k]) >= min_runs and len(rs[k]) >= min_runs)
    if not common:
        print("no cells measured on both sides"
              + (f" for {item_filter}" if item_filter else ""))
        return 1

    disj = [k for k in common if set(ls[k]).isdisjoint(set(rs[k]))]
    decl = declared_items()
    print(f"{len(common)} cell(s) measured on both sides; "
          f"{len(disj)} never agree ({100 * len(disj) / len(common):.1f}%)\n")

    if not disj:
        print("the two paths overlap on every cell measured on both")
        return 0

    byitem = collections.Counter(i for i, _ in disj)
    print(f"{'item':6}{'cells':>7}   status")
    print("-" * 58)
    for it, n in byitem.most_common():
        tot = sum(1 for i, _ in common if i == it)
        mark = "declared" if it in decl else "*** NOT DECLARED ***"
        print(f"{it:6}{n:>3}/{tot:<3}   {mark}")

    print(f"\n{'cell':12}{lname[:11]:>12}{rname[:11]:>12}   direction")
    print("-" * 58)
    for k in disj:
        l, r = sorted(set(ls[k])), sorted(set(rs[k]))
        if min(l) > max(r):
            d = f"{lname} HIGHER"
        elif max(l) < min(r):
            d = f"{lname} LOWER"
        else:
            d = "mixed"
        print(f"{k[0]+'/p'+str(k[1]):12}{str(l):>12}{str(r):>12}   {d}")
        if show_slots:
            basis = slot_basis(k[0])
            for slot, lval, rval in _slot_diffs(lv.get(k, []), rv.get(k, []), lkind, rkind):
                what = basis.get(slot, "unknown basis")
                print(f"{'':12}  slot `{slot}`: {lname} {lval} / {rname} {rval}"
                      f"   [{what}]")
    return 0


def _slot_diffs(lvs: list, rvs: list, lkind: str = "", rkind: str = "") -> list:
    """Slots whose majority verdict differs, which names the responsible rule.

    Majority rather than any-run, so one flapping run does not implicate a slot
    that both sides mostly agree on.
    """
    def majority(dicts: list, slot: str) -> str | None:
        vals = [d.get(slot) for d in dicts if d.get(slot) is not None]
        if not vals:
            return None
        return collections.Counter(vals).most_common(1)[0][0]

    # THE TWO SIDES DO NOT SHARE A VERDICT VOCABULARY when one of them is the
    # paper scorer. slot_vocab declares them separately -- WEB_EXTRAS come from
    # slotSheet.ts, RUBRIC_EXTRAS from the credit components' `verdicts` lists --
    # so `wrong_kind` on the web and `not_reason` in the rubric are counterparts,
    # not a disagreement. Comparing the raw strings would report every such slot
    # as divergent, which is a false positive on exactly the comparison this tool
    # exists for.
    #
    # Harness-vs-app is safe: both serve the web's vocabulary, and the raw tokens
    # carry which failure mode was chosen, which is worth keeping. So the tokens
    # are folded to satisfied/failed ONLY when a paper artifact is involved, and
    # the caller is told, because a folded comparison answers a coarser question.
    cross_vocab = "paper" in (lkind, rkind) and lkind != rkind

    def fold(v):
        if v is None or not cross_vocab:
            return v
        return "met" if v == "met" else f"<not-met:{v}>"

    slots = {s for d in lvs for s in d} & {s for d in rvs for s in d}
    out = []
    for s in sorted(slots):
        a, b = majority(lvs, s), majority(rvs, s)
        if a is None or b is None:
            continue
        fa, fb = fold(a), fold(b)
        if cross_vocab:
            # Same satisfied/failed answer under different names is agreement.
            if (a == "met") == (b == "met"):
                continue
        elif a == b:
            continue
        out.append((s, a, b))
    return out


def _gold_scores() -> dict:
    """(item, pid) -> gold score, from the graders' own spreadsheets."""
    import gold as G
    out = {}
    # THE SAME ACCOUNTING THE LEDGER USES, not a second reading of the same
    # files. Raw gold is not what any rate in this project is computed against:
    # `apply_corrected_gold` replaces rows a human re-read and corrected, and 1c
    # needs `rebuild_gold_1c` on top -- without it 1c reads as 18 over-credits
    # when it has none, which is exactly how a wrong figure reached a corpus-wide
    # ranking once already.
    import handouts as _H
    import agreement_app as _APP
    for h, loader in ((1, G.load_h1), (2, G.load_h2), (3, G.load_h3)):
        try:
            rows = _H.apply_corrected_gold(loader(), h)
            if h == 3:
                rows, _ = _APP.rebuild_gold_1c({p: dict(v) for p, v in rows.items()})
        except Exception:
            continue
        for pid, items in rows.items():
            for item, rec in (items or {}).items():
                sc = (rec or {}).get("score")
                if sc is not None:
                    out[(item, int(pid))] = float(sc)
    return out


def _excluded_cells(item: str) -> set:
    """The ledger's exclusions, read from the ledger -- never a second copy."""
    try:
        import measured
        return set(measured.exclusions(item))
    except Exception:
        return set()


def _H_scored_exactly(item, gold_score, pred) -> bool:
    try:
        import handouts as _H
        return bool(_H.scored_exactly(item, gold_score, pred))
    except Exception:
        return abs(float(pred) - float(gold_score)) < 1e-9


def against_gold(left: str, right: str, item_filter: str | None = None) -> int:
    """Which side matches GOLD more often, per item.

    The tie-break that decides direction. "Web wording wins" settles which way to
    SAY a shared rule; it never settles which of two answers is right, and gold
    does -- symmetrically. If the web matches gold better the web is kept and the
    CLI moves; if the CLI does, the reverse. This measures it instead of arguing
    it, from artifacts already on disk.

    A side MATCHES a cell when its median score equals gold. Median rather than
    any-run, so a side is not credited for having once stumbled onto the right
    answer.
    """
    ls, _, lkind, le = load(left)
    rs, _, rkind, re_ = load(right)
    lname = os.path.basename(left.rstrip("/"))
    rname = os.path.basename(right.rstrip("/"))
    goldsc = _gold_scores()
    if not goldsc:
        print("no gold could be loaded")
        return 1

    import statistics
    def med(v):
        return statistics.median(sorted(v))

    per = collections.defaultdict(lambda: [0, 0, 0])      # item -> [both, L, R]
    cells = collections.defaultdict(list)
    for k in sorted(set(ls) & set(rs) & set(goldsc)):
        if item_filter and k[0] != item_filter:
            continue
        if k[1] in _excluded_cells(k[0]):
            continue          # excluded from every rate the ledger reports
        g = goldsc[k]
        lm, rm = med(ls[k]), med(rs[k])
        # `scored_exactly`, NOT float equality: it carries the unreachable-gold
        # allowance, so a cell gold puts out of reach is not counted as a miss on
        # either side. Comparing with `==` charges both paths for the rubric's
        # arithmetic and calls it a path difference.
        lok, rok = _H_scored_exactly(k[0], g, lm), _H_scored_exactly(k[0], g, rm)
        row = per[k[0]]
        row[0] += 1
        row[1] += int(lok)
        row[2] += int(rok)
        if lok != rok:
            cells[k[0]].append((k[1], g, lm, rm, lname if lok else rname))

    print(f"{lname} ({lkind})  vs  {rname} ({rkind})   -- median against gold")
    # NAME THE SIDE BY KIND, NOT BY DIRECTORY. The corpus has a directory called
    # `cli_v8` that is agreement.py -- the harness that sends the WEB's prompt and
    # derives the score in Python -- while `paper_mini_v8` is score.py, the path the
    # equivalence goal calls the CLI. Reading the dir names as sides gets the
    # conclusion exactly backwards, so the kinds are spelled out every run.
    KIND = {"paper": "score.py, the paper/CLI scorer",
            "harness": "agreement.py, the WEB prompt scored in python",
            "app": "agreement_app.py, the web app's own grader"}
    print(f"  {lname} = {KIND.get(lkind, lkind)}")
    print(f"  {rname} = {KIND.get(rkind, rkind)}\n")
    print(f"{'item':6}{'cells':>6}{lname[:9]:>11}{rname[:9]:>11}   closer to gold")
    print("-" * 62)
    tl = tr = tc = 0
    for item in sorted(per):
        n, l, r = per[item]
        tc += n; tl += l; tr += r
        who = "tie" if l == r else (lname if l > r else rname)
        print(f"{item:6}{n:>6}{l:>11}{r:>11}   {who}")
    print("-" * 62)
    print(f"{'TOTAL':6}{tc:>6}{tl:>11}{tr:>11}   "
          f"{'tie' if tl == tr else (lname if tl > tr else rname)}")
    if item_filter and cells:
        print(f"\ncells where exactly one side matches gold, {item_filter}:")
        for pid, g, lm, rm, who in cells[item_filter]:
            print(f"   p{pid:<3} gold {g:<6} {lname} {lm:<6} {rname} {rm:<6} -> {who}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Compare two scoring paths cell by cell.")
    ap.add_argument("left")
    ap.add_argument("right")
    ap.add_argument("--item", help="only this item, listing every cell")
    ap.add_argument("--slots", action="store_true",
                    help="for each divergent cell, name the slots whose majority "
                         "verdict differs")
    ap.add_argument("--gold", action="store_true",
                    help="which side matches GOLD more often, per item -- the "
                         "tie-break that decides which way a divergence is fixed")
    ap.add_argument("--min-runs", type=int, default=1,
                    help="ignore cells with fewer runs than this on either side")
    a = ap.parse_args()

    import paths
    def resolve(d: str) -> str:
        return d if os.path.isdir(d) else os.path.join(str(paths.OUT), d)

    # SAME CLASS AS equivalence.py's `--selftest`: a flag read in one branch and
    # silently dropped in the other. `--slots` annotates each DIVERGENT slot with
    # its basis, which only `compare` produces; `--gold` returns before it. Every
    # `--slots --gold` invocation therefore ignored `--slots` without saying so,
    # and the missing slot section reads exactly like "no slot diverged".
    # An error rather than a quiet drop, for the reason E12 records: the two modes
    # answer different questions, and someone who asked for both should be told
    # which one they are getting.
    if a.gold and a.slots:
        ap.error("--slots has no effect with --gold: --gold reports which side is "
                 "closer to gold, --slots annotates divergent slots in the "
                 "path-vs-path comparison. Run them as two commands.")
    if a.gold:
        return against_gold(resolve(a.left), resolve(a.right), a.item)
    return compare(resolve(a.left), resolve(a.right), a.item, a.slots, a.min_runs)


if __name__ == "__main__":
    raise SystemExit(main())
