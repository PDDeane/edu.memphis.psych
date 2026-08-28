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
                if "cell" in r:                       # the app
                    kind = "app"
                    cell = str(r.get("cell") or "")
                    if "/" not in cell:
                        continue
                    pid_s, item = cell.split("/", 1)
                    try:
                        pid = int(pid_s.lstrip("pP"))
                    except ValueError:
                        continue
                    raw = (r.get("grader") or {}).get("score")
                    mx = r.get("sheet_max")
                    if raw is None or mx is None:
                        continue
                    # A FRACTION of the sheet, unlike every other shape.
                    scores[(item, pid)].append(float(raw) * float(mx))
                    verdicts[(item, pid)].append(dict(r.get("verdicts") or {}))
                else:                                 # the python harness
                    pid = r.get("participant_id")
                    if r.get("score") is None or pid is None:
                        continue
                    key = (r["item"], pid)
                    scores[key].append(float(r["score"]))
                    ch = r.get("checks") or {}
                    verdicts[key].append(dict(ch) if isinstance(ch, dict) else {})
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
        for it in set(le["items"]) & set(re_["items"]):
            a = (le["items"][it] or {}).get("prompt_sha")
            b = (re_["items"][it] or {}).get("prompt_sha")
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
            for slot, lval, rval in _slot_diffs(lv.get(k, []), rv.get(k, [])):
                print(f"{'':12}  slot `{slot}`: {lname} {lval} / {rname} {rval}")
    return 0


def _slot_diffs(lvs: list, rvs: list) -> list:
    """Slots whose majority verdict differs, which names the responsible rule.

    Majority rather than any-run, so one flapping run does not implicate a slot
    that both sides mostly agree on.
    """
    def majority(dicts: list, slot: str) -> str | None:
        vals = [d.get(slot) for d in dicts if d.get(slot) is not None]
        if not vals:
            return None
        return collections.Counter(vals).most_common(1)[0][0]

    slots = {s for d in lvs for s in d} & {s for d in rvs for s in d}
    out = []
    for s in sorted(slots):
        a, b = majority(lvs, s), majority(rvs, s)
        if a is not None and b is not None and a != b:
            out.append((s, a, b))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Compare two scoring paths cell by cell.")
    ap.add_argument("left")
    ap.add_argument("right")
    ap.add_argument("--item", help="only this item, listing every cell")
    ap.add_argument("--slots", action="store_true",
                    help="for each divergent cell, name the slots whose majority "
                         "verdict differs")
    ap.add_argument("--min-runs", type=int, default=1,
                    help="ignore cells with fewer runs than this on either side")
    a = ap.parse_args()

    import paths
    def resolve(d: str) -> str:
        return d if os.path.isdir(d) else os.path.join(str(paths.OUT), d)

    return compare(resolve(a.left), resolve(a.right), a.item, a.slots, a.min_runs)


if __name__ == "__main__":
    raise SystemExit(main())
