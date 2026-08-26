"""The measurement ledger: which items were measured, at which prompt, on which cells.

    python3 measured.py --status                 what is stale, what is pending
    python3 measured.py --record Q1 OUT/Q1.runs.json    after a sweep of Q1

An item's published number is only meaningful against two things: the prompt the
grader was sent, and the set of cells the rate was computed over. Change either
and the number is stale — but nothing in the tree LOOKED different, because both
changes are invisible after the fact. A rewritten rule is a diff that landed
weeks ago; a removed exclusion deletes the only record that the cell was ever in
question. An item whose denominator moved and whose prompt was rewritten is
byte-identical, in git, to an item nobody has touched.

That is not hypothetical. On 2026-08-24 an audit found Q1 had five exclusions
removed and its six citations rewritten into rules in the same commit, with no
sweep afterwards — its last item-level measurement predated both changes, and
its reported number rested on re-derivation. Two other guards had gone in that
same day (`olx_prompts --write` naming UNMEASURED sections, `compare_runs.py`
refusing unprobed verdicts) and neither could have caught it: one fires at write
time and prints to stderr, the other only if someone runs it. Guard prose in
QUALITY_CONTROL.md could not catch it either, because the guide had said to
measure and had been read.

So the ledger records, per item, the SHA of the prompt text that was measured
and the exact exclusion set it was measured over. `check_items_are_measured_as_configured`
in enforcement.py recomputes both from the working tree and fails when they
disagree — which turns "someone must remember to re-measure" into a check that
names the item and what changed under it.

Recording is deliberate and mechanical: `--record` reads the run artifact and
writes the entry, so an entry cannot claim a measurement that was not run, and
nobody hand-types a SHA.

A gap may be DECLARED rather than closed, in this project's usual idiom: an
entry may say `pending` with a reason, which the check lists instead of failing
on. What it may not do is be absent. An item that is neither recorded nor
declared is a hard failure, because silence is what let Q1 through.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

LEDGER = Path(__file__).resolve().parent / "MEASURED.json"


def _jobs() -> dict:
    import agreement_app as APP
    return APP.JOBS


def _olx(handout: int) -> str:
    import paths
    return (paths.OLX_DIR / f"bmod_handout{handout}.olx").read_text()


def _section_bounds(text: str, screen_ids: set[str]) -> dict[str, tuple[int, int]]:
    """Slice the OLX into per-item sections, keyed by screen id.

    A section runs from its own <Vertical> to the next <Vertical> that is ALSO an
    item screen — not merely the next <Vertical>, since an item's own tabs are
    Verticals too and slicing at those would cut an item's prompt in half.
    """
    starts: list[tuple[int, str]] = []
    for m in re.finditer(r'<Vertical id="([^"]+)"', text):
        if m.group(1) in screen_ids:
            starts.append((m.start(), m.group(1)))
    out: dict[str, tuple[int, int]] = {}
    for i, (pos, sid) in enumerate(starts):
        end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
        out[sid] = (pos, end)
    return out


def prompt_sha(item: str) -> str:
    """SHA-256 of the OLX text that item's grader is served, to 12 hex chars."""
    jobs = _jobs()
    job = jobs[item]
    sid = job["screen"].split("/")[-1]
    text = _olx(job["handout"])
    screen_ids = {j["screen"].split("/")[-1] for j in jobs.values()
                  if j["handout"] == job["handout"]}
    bounds = _section_bounds(text, screen_ids)
    if sid not in bounds:
        raise KeyError(f"{item}: no <Vertical id=\"{sid}\"> in handout "
                       f"{job['handout']}'s OLX")
    a, b = bounds[sid]
    return hashlib.sha256(text[a:b].encode()).hexdigest()[:12]


def exclusions(item: str) -> list[int]:
    import handouts as H
    return sorted(H.cell_exclusions(_jobs()[item]["handout"], item))


def load() -> dict:
    if not LEDGER.exists():
        return {"items": {}}
    return json.loads(LEDGER.read_text())


def save(led: dict) -> None:
    LEDGER.write_text(json.dumps(led, indent=2, sort_keys=True) + "\n")


def status() -> list[tuple[str, str]]:
    """Per item, one of: ok, pending (declared), stale-prompt, stale-cells, absent."""
    led = load().get("items", {})
    out = []
    for item in sorted(_jobs()):
        rec = led.get(item)
        if rec is None:
            out.append((item, "ABSENT — never recorded, and not declared pending"))
            continue
        if rec.get("pending"):
            out.append((item, f"pending: {rec['pending']}"))
            continue
        if rec.get("prompt_sha") != prompt_sha(item):
            out.append((item, f"STALE PROMPT — measured at "
                              f"{rec.get('prompt_sha')}, now {prompt_sha(item)}"))
            continue
        if rec.get("exclusions") != exclusions(item):
            out.append((item, f"STALE CELLS — measured over "
                              f"{rec.get('exclusions')}, now {exclusions(item)}"))
            continue
        out.append((item, f"ok  {rec.get('numerator')}/{rec.get('denominator')} "
                          f"in {rec.get('runs')} run(s)  {rec.get('out', '')}"))
    return out


def record(item: str, runs_path: str) -> None:
    """Write item's entry FROM a run artifact, so it cannot claim what was not run."""
    import handouts as H
    import gold
    import agreement_app as APP

    h = _jobs()[item]["handout"]
    g = H.apply_corrected_gold(
        {1: gold.load_h1, 2: gold.load_h2, 3: gold.load_h3}[h](), h)
    if item == "1c":
        g, _ = APP.rebuild_gold_1c({p: dict(v) for p, v in g.items()})
    ex = set(exclusions(item))
    per: dict[int, list[bool]] = {}
    exc: dict[int, list[bool]] = {}
    for run in json.loads(Path(runs_path).read_text())["runs"]:
        for c in run["results"]:
            pid, s = c["participant_id"], c.get("score")
            row = (g.get(pid) or {}).get(item) or {}
            if row.get("score") is None:
                continue
            right = s is not None and H.scored_exactly(item, row["score"], s)
            # Excluded cells are still run and still scored, so recording them
            # costs nothing and is what lets a declaration be caught outliving
            # its evidence: an exclusion whose cell now agrees, every run, is a
            # cell being subtracted from every rate for a reason that expired.
            (exc if pid in ex else per).setdefault(pid, []).append(right)
    if not per:
        raise SystemExit(f"{item}: no counted cells in {runs_path}")
    n = min(len(v) for v in per.values())
    totals = sorted(sum(1 for p in per if per[p][i]) for i in range(n))
    led = load()
    led.setdefault("items", {})[item] = {
        "prompt_sha": prompt_sha(item),
        "exclusions": exclusions(item),
        "runs": n,
        "numerator": totals[n // 2],
        "denominator": len(per),
        "run_totals": totals,
        "out": str(Path(runs_path).parent.name),
        # Per cell, how many of the recorded runs scored it right. Keyed by str
        # because JSON keys are strings; read back through `_cells`.
        "cells": {str(p): sum(1 for v in per[p][:n] if v) for p in sorted(per)},
        "excluded_cells": {str(p): sum(1 for v in exc[p] if v)
                           for p in sorted(exc)},
    }
    save(led)
    print(f"{item}: {totals[n // 2]}/{len(per)} recorded at prompt "
          f"{prompt_sha(item)} over {len(per)} cells (runs {totals})")


def declaration_conflicts() -> list[str]:
    """Declarations the recorded measurements no longer support.

    Every declaration in handouts.py is a PREDICTION about a cell or an item: a
    divergence predicts we miss this cell and mean to; a ceiling predicts the
    item cannot be perfect because gold is incoherent; an exclusion predicts the
    cell should not be counted. Predictions can expire — the model improves, a
    fixture defect is repaired, a rule is rewritten — and an expired declaration
    is invisible, because a cell that has stopped being a problem produces no
    error to notice. It just quietly costs a cell in every rate, forever.

    Section 5's "reduce the declarations" schedule exists for this and was run by
    hand, which is why 25 unnecessary registrations survived several passes. So
    the ledger, which records every cell's per-run outcome INCLUDING the excluded
    ones, is compared against the declarations automatically.

    The threshold follows Q2/p17: three uniform passes prove nothing, in either
    direction. So a declaration contradicted by fewer than six recorded runs
    yields a demand for a probe, not a retirement; only 6+ runs of unbroken
    agreement asks for the declaration to go. Nothing is flagged from a partial
    rate, because a declaration about a cell the model gets right half the time
    is doing exactly the job it was written for.
    """
    import handouts as H

    led = load().get("items", {})
    out: list[str] = []

    def verdict(what: str, right: int, runs: int, action: str) -> str:
        if runs >= 6:
            return (f"{what} is contradicted by {right}/{runs} recorded runs. "
                    f"{action}")
        lead = action[:1].lower() + action[1:]   # not .lower(): "Q6/p5" is a name
        return (f"{what} is contradicted by {right}/{runs} recorded runs, but "
                f"{runs} runs cannot settle a per-cell claim (see Q2/p17). Probe "
                f"it at six passes with controls; if it holds, {lead}")

    for entry in getattr(H, "GOLD_DIVERGENCES", []) or []:
        for item, pid in entry.get("cells", []):
            rec = led.get(item)
            if not rec or rec.get("pending"):
                continue
            right = (rec.get("cells") or {}).get(str(pid))
            runs = rec.get("runs") or 0
            if right is None or runs == 0 or right < runs:
                continue
            out.append(verdict(
                f"GOLD_DIVERGENCES {entry['code']} says we knowingly miss "
                f"{item}/p{pid}, but the recorded measurement scores it RIGHT "
                f"every run — the divergence",
                right, runs, f"Retire the {item}/p{pid} cell from that entry"))

    for (h, item), _why in (getattr(H, "GOLD_CEILINGS", {}) or {}).items():
        rec = led.get(item)
        if not rec or rec.get("pending"):
            continue
        num, den, runs = (rec.get("numerator"), rec.get("denominator"),
                          rec.get("runs") or 0)
        if not den or num != den or runs == 0:
            continue
        out.append(verdict(
            f"GOLD_CEILINGS ({h!r}, {item!r}) says this item cannot be perfect, "
            f"but it recorded {num}/{den} — the ceiling",
            runs, runs, f"Retire the ({h!r}, {item!r}) ceiling"))

    for item, rec in sorted(led.items()):
        if rec.get("pending"):
            continue
        runs = rec.get("runs") or 0
        kinds = H.cell_exclusions(_jobs()[item]["handout"], item)
        for pid_s, right in sorted((rec.get("excluded_cells") or {}).items(),
                                   key=lambda kv: int(kv[0])):
            if runs == 0 or right < runs:
                continue
            kind = (kinds.get(int(pid_s)) or ("", ""))[0]
            # Not every exclusion is a hypothesis about the model, and only the
            # ones that are can be retired by measuring it.
            #
            # `suspect` is a fact about the INPUT: the submission was
            # mis-transcribed and the prompt carries another participant's data.
            # A cell like that agreeing with gold is a coincidence between the
            # wrong student's answer and this student's score — the one reading
            # that must NOT be taken as evidence the cell is fine. PR/p2 hit this
            # within minutes of the check going in, offering to count a cell
            # whose input is known to belong to someone else.
            #
            # `self_graded` and `unscoreable` are claims that measurement can
            # contradict: the first says the prompt gives the answer away, the
            # second says gold's row is unreachable, and a cell that agrees
            # anyway refutes both.
            if kind == "suspect":
                continue
            out.append(verdict(
                f"{item}/p{pid_s} is EXCLUDED as {kind or 'excluded'}, yet scores "
                f"right every recorded run — the exclusion",
                right, runs,
                f"Remove {item}/p{pid_s} from its exclusion and let it count"))
    return out


# Fractions first, item names second — NOT one pattern anchored on the name.
# Anchoring on the name meant any word in front of it was consumed as the
# candidate and the real name never got its turn: "Item 3 is 20/20" matched
# "Item", found it absent from JOBS, and moved past the fraction without ever
# testing "3", because finditer does not retry overlapping starts.
_FRAC_RE = re.compile(r"\b(?P<num>\d{1,2})\s*(?:/|\s+of\s+)\s*(?P<den>\d{1,2})\b")
_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
_WINDOW = 45

# Prose legitimately cites superseded numbers; those sentences say so. A claim
# framed as history is not a claim about the present.
_HISTORICAL = re.compile(
    r"\b(was|were|had been|used to|previously|prior|before|earlier|once|"
    r"then|originally|superseded|stale|reported as|no longer)\b"
    # A fraction attributed to a NAMED artifact is a claim about that run, not
    # about the present configuration, however present-tense the verb.
    # EQUIVALENCE.md line 491 reads "On web_v8/v9, 2a is 14-16 of 18 and 3 is 20
    # of 20" inside a block that already says "Do not quote this list as
    # current" — correct prose that the first version of this check called stale.
    r"|\b(web_v|cli_v|qc_v|qc_h|opusweb|baseline_)\w*", re.I)

# Words that make a fraction a COUNT of cells rather than a score over them.
# "Q6 excludes 10 of 20" and "2a flags 18 of 20" are both true and neither is a
# rate; each produced a confident false positive before this list existed.
_COUNTING = re.compile(r"exclud|flag|cells|participants|of the rest|"
                       r"rows|boxes|slots|passes|runs", re.I)


def prose_claims(paths: list[str] | None = None) -> list[str]:
    """Numbers written into the repo that disagree with the recorded measurement.

    A figure in prose is the form a measurement actually travels in — a guide,
    a backlog entry, a note in handouts.py — and it goes stale silently. This
    project has done it: Q4c and Q5 were described in writing as perfect items
    and were 12/14 and 14/15, because the sentences outlived the denominators
    they were computed over.

    The rule is deliberately narrow, so it fires on real staleness rather than on
    every number in the tree. A finding needs all of: an item name from JOBS, a
    fraction within 40 characters of it, a DENOMINATOR equal to that item's
    currently recorded one — and a numerator that disagrees. Matching the
    denominator is what makes it a claim about the present configuration; a
    fraction over the old denominator is history and is left alone, as is any
    sentence framed in the past tense.
    """
    import paths as _paths

    files = paths or [str(p) for p in (
        list((_paths.SCORING).glob("*.md")) + [_paths.SCORING / "handouts.py"])]
    led = load().get("items", {})
    jobs = set(_jobs())
    out: list[str] = []
    for path in files:
        try:
            text = Path(path).read_text()
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if _HISTORICAL.search(line):
                continue
            for m in _FRAC_RE.finditer(line):
                window = line[max(0, m.start() - _WINDOW):m.start()]
                # The NEAREST item name before the fraction owns it.
                names = [t for t in _TOKEN_RE.findall(window) if t in jobs]
                if not names:
                    continue
                item = names[-1]
                rec = led.get(item)
                if not rec or rec.get("pending"):
                    continue
                num, den = int(m.group("num")), int(m.group("den"))
                if den != rec["denominator"] or num == rec["numerator"]:
                    continue
                # The denominator is the same 20 whether the fraction counts
                # cells or scores them, so the surrounding words are the only
                # way to tell, and getting it wrong yields a confident lie.
                if _COUNTING.search(window):
                    continue
                out.append(
                    f"{Path(path).name}:{lineno} says {item} {num}/{den}, but the "
                    f"recorded measurement is {rec['numerator']}/{rec['denominator']}"
                    f" — update the sentence, or re-record if the sweep is newer")
    return out


_DEDUCT_RE = re.compile(r"-\s*(\d+(?:\.\d+)?)\s*(?:pt|point)", re.I)


def gold_rows_that_do_not_reconcile() -> list[str]:
    """Rows whose own comment itemises deductions that do not reach their score.

    D2/p11 was found this way by hand: the grader named one defect, charged 1
    point for it, and the deduction dictionary plus the same grader's own
    treatment of the identical defect one item earlier both said 2. That is a
    wrong NUMBER — CORRECTED_GOLD — rather than a disagreement to declare.

    The generalisation is mechanical wherever a comment itemises its arithmetic:
    take the item's maximum, subtract the deductions the comment names, and
    compare with the score written. A row that does not reconcile is a gold
    question, and gold questions come BEFORE model work (step 2 before step 3),
    because tuning a criterion against an incoherent row measures the row.

    Reported, never auto-corrected. A row can fail to reconcile because the
    grader slipped OR because they applied a deduction they did not write down,
    and only reading the submission distinguishes those. What this removes is the
    part that was left to memory: noticing that the row is worth reading.
    """
    import gold as _gold
    import handouts as H

    out: list[str] = []
    loaders = {1: _gold.load_h1, 2: _gold.load_h2, 3: _gold.load_h3}
    jobs = _jobs()
    for h in (1, 2, 3):
        try:
            g = loaders[h]()
        except Exception:
            continue
        items = [i for i in sorted(jobs) if jobs[i]["handout"] == h]
        maxes = {i: max(((g.get(p) or {}).get(i) or {}).get("score") or 0
                        for p in g) for i in items}
        for item in items:
            for pid in sorted(g):
                row = (g.get(pid) or {}).get(item) or {}
                score, fb = row.get("score"), (row.get("feedback") or "").strip()
                if score is None or not fb:
                    continue
                named = [float(x) for x in _DEDUCT_RE.findall(fb)]
                if not named:
                    continue
                implied = maxes[item] - sum(named)
                if abs(implied - score) < 1e-9:
                    continue
                # A cell already declared has had this argument had about it.
                if H.gold_divergence(item, pid) or H.corrected_gold(item, pid):
                    continue
                out.append(
                    f"{item}/p{pid}: gold {score:g}, but its comment itemises "
                    f"{'+'.join(f'{n:g}' for n in named)} off a max of "
                    f"{maxes[item]:g}, which implies {implied:g}. Read the "
                    f"submission: a slip is CORRECTED_GOLD, an unwritten "
                    f"deduction is not")
    return out


def fixture_suspects() -> list[str]:
    """Cells whose miss looks like a mis-parsed box rather than a judgement.

    Two signatures, both requiring the cell to be wrong in EVERY recorded run,
    since an intermittent miss is a judgement wobbling:

      * we award NOTHING where gold awarded full marks — the grader found no
        creditable content in an answer the paper scorer credited completely
      * we award something where gold awarded ZERO — credit found in an answer
        judged empty of it

    Every other stable miss in this corpus is off by one deduction step, which is
    what a criterion boundary looks like. These two are what a box holding the
    wrong text looks like, and §1 puts a fixture read-out before any rubric work,
    because a criterion tuned against a mis-cut box measures the box.

    Declared cells are skipped: a divergence or correction means the disagreement
    has already been examined.
    """
    import gold as _gold
    import handouts as H

    led = load().get("items", {})
    loaders = {1: _gold.load_h1, 2: _gold.load_h2, 3: _gold.load_h3}
    jobs = _jobs()
    out: list[str] = []
    for item, rec in sorted(led.items()):
        if rec.get("pending") or not rec.get("cells"):
            continue
        h = jobs[item]["handout"]
        try:
            g = H.apply_corrected_gold(loaders[h](), h)
        except Exception:
            continue
        if item == "1c":
            import agreement_app as APP
            g, _ = APP.rebuild_gold_1c({p: dict(v) for p, v in g.items()})
        top = max(((g.get(p) or {}).get(item) or {}).get("score") or 0 for p in g)
        runs_path = _runs_path(item)
        for pid_s, right in sorted(rec["cells"].items(), key=lambda kv: int(kv[0])):
            if right != 0:
                continue
            pid = int(pid_s)
            gs = ((g.get(pid) or {}).get(item) or {}).get("score")
            if gs is None or H.gold_divergence(item, pid):
                continue
            got = _scores_for(item, pid, runs_path)
            if not got or any(s is None for s in got):
                continue
            # Three runs cannot distinguish a stable miss from a coin, and
            # sending someone to read a fixture for a cell that is merely
            # unstable wastes the expensive step. Q2/p17 read 0/3 here and is
            # 10/18 across six sweeps. So ask every artifact that ever measured
            # this cell — the corollary in QUALITY_CONTROL.md, and cheaper than
            # either a probe or a fixture read.
            if _ever_right(item, pid, gs):
                continue
            if gs == top and all(s == 0 for s in got):
                out.append(f"{item}/p{pid}: gold {gs:g} (full marks) and we award "
                           f"0 in every run — read the fixture before the rubric")
            elif gs == 0 and all(s > 0 for s in got):
                out.append(f"{item}/p{pid}: gold 0 and we award "
                           f"{'/'.join(f'{s:g}' for s in got)} in every run — "
                           f"read the fixture before the rubric")
    return out


def _runs_path(item: str) -> str | None:
    """Where the recorded sweep's artifact is, derived from the ledger entry.

    The ledger stores the output DIRECTORY name it recorded from, so the artifact
    is findable without a second registry to keep in step.
    """
    import paths

    rec = (load().get("items", {}) or {}).get(item) or {}
    out = rec.get("out")
    if not out:
        return None
    p = paths.OUT / out / f"{item}.runs.json"
    return str(p) if p.exists() else None


def _ever_right(item: str, pid: int, gold_score: float) -> bool:
    """Has this cell EVER agreed with gold, in any artifact on disk?

    A cell that has been right before is unstable, not mis-parsed. Reading its
    fixture will find nothing, because the fixture did not change between the
    run that scored it right and the one that did not.
    """
    import glob

    import handouts as H
    import paths

    for path in glob.glob(str(paths.OUT / "*" / f"{item}.runs.json")):
        try:
            data = json.loads(Path(path).read_text())
        except (OSError, ValueError):
            continue
        for run in data.get("runs", []):
            for c in run.get("results", []):
                if not isinstance(c, dict) or c.get("participant_id") != pid:
                    continue
                s = c.get("score")
                if s is not None and H.scored_exactly(item, gold_score, s):
                    return True
    return False


def _scores_for(item: str, pid: int, runs_path: str | None) -> list:
    if not runs_path:
        return []
    try:
        data = json.loads(Path(runs_path).read_text())
    except OSError:
        return []
    return [c.get("score") for run in data["runs"] for c in run["results"]
            if c.get("participant_id") == pid]


def preflight() -> dict[str, list[str]]:
    """Everything outstanding, in the order the guide says to address it.

    Probes are the last step, not the next one. A probe costs 24 calls to settle
    one cell, and settling a cell is worthless while the item's fixture is
    unread, its gold incoherent, or its declarations unexamined — the guide's
    step order exists because work done out of order measures the wrong thing.
    Leaving that ordering to memory is how a session spends an afternoon probing
    cells on an item whose gold row does not add up.
    """
    return {
        "1. fixture — read these boxes before any rubric work":
            fixture_suspects(),
        "2. gold — these rows do not reconcile with their own comments":
            gold_rows_that_do_not_reconcile(),
        "3. declarations — contradicted by a recorded measurement":
            declaration_conflicts(),
        "4. staleness — items not measured as currently configured":
            [f"{i}: {s}" for i, s in status()
             if s.startswith(("ABSENT", "STALE", "pending"))],
        "5. record — prose that disagrees with the ledger":
            prose_claims(),
        "6. leakage — rule blocks echoing the cohort, with no verdict filed":
            _leakage_pending(),
        "7. probes — items whose recorded prompt has unprobed moved cells":
            _unprobed_movers(),
    }


def _unprobed_movers() -> list[str]:
    """Items measured at a prompt whose moved cells were never probed.

    `compare_runs` withholds its verdict on these, so they are decisions that
    cannot honestly be made yet — neither keeping a change nor reverting it. They
    belong on the same list as an unread fixture for the same reason: work done
    on top of one is work done on a number nobody has established.
    """
    try:
        import compare_runs as CR
    except Exception:
        return []
    out = []
    for item, rec in (load().get("items", {}) or {}).items():
        pending = rec.get("unprobed_movers") or []
        if not pending:
            continue
        have = CR.probed_cells(item, rec.get("prompt_sha", ""))
        left = [p for p in pending if p not in have]
        if left:
            out.append(f"{item}: moved cell(s) {', '.join('p%s' % p for p in left)} "
                       f"never probed at prompt {rec.get('prompt_sha')}")
    return out


def _leakage_pending() -> list[str]:
    """Rule prose that shares wording with the responses it is meant to judge.

    Listed here as well as gated in agreement.py because preflight is what a
    session reads to decide what to do next, and "our rule quotes the cell it
    was written to fix" belongs on that list — it invalidates a measurement
    rather than merely delaying one.
    """
    try:
        import leakage
        return leakage.unreviewed()
    except Exception:
        return []


def report() -> str:
    """The canonical table, generated. Paste this rather than retyping figures.

    Every number here is the median of the recorded runs over the recorded
    denominator, because those are the two things a reported figure is most
    easily wrong about: the best run instead of the median, and a denominator
    that has since grown. Handout 1's items were once reported as 12/14 and
    14/15 while their denominators were 19 and 20.
    """
    led = load().get("items", {})
    lines, tot_n, tot_d = [], 0, 0
    for h in (1, 2, 3):
        rows = [(i, led.get(i, {})) for i in sorted(_jobs())
                if _jobs()[i]["handout"] == h]
        lines.append(f"Handout {h}")
        for item, rec in rows:
            if not rec or rec.get("pending"):
                lines.append(f"  {item:<5} pending")
                continue
            n, d = rec["numerator"], rec["denominator"]
            tot_n += n
            tot_d += d
            ex = f"  excl {rec['exclusions']}" if rec["exclusions"] else ""
            lines.append(f"  {item:<5} {n:>3}/{d:<3} {100.0 * n / d:5.1f}%  "
                         f"median of {rec['runs']} runs {rec['run_totals']}{ex}")
    if tot_d:
        lines.append(f"\nTOTAL {tot_n}/{tot_d} = {100.0 * tot_n / tot_d:.1f}% "
                     f"(sum of per-item medians; not a run of the whole corpus)")
    return "\n".join(lines)


def main() -> int:
    a = sys.argv[1:]
    if a[:1] == ["--status"]:
        worst = 0
        for item, s in status():
            print(f"  {item:<5} {s}")
            worst = max(worst, 2 if s.startswith(("ABSENT", "STALE")) else 0)
        return worst
    if a[:1] == ["--record"] and len(a) == 3:
        record(a[1], a[2])
        for c in declaration_conflicts():
            print(f"  DECLARATION EXPIRED? {c}")
        return 0
    if a[:1] == ["--report"]:
        print(report())
        return 0
    if a[:1] == ["--preflight"]:
        # The active objective, printed wherever the gate is consulted. A goal
        # kept only in someone's head is a goal that gets swapped for a
        # different one mid-task without anything noticing.
        goals = LEDGER.parent / "GOALS.md"
        if goals.exists():
            lines = goals.read_text().splitlines()
            for i, line in enumerate(lines):
                if line.startswith("## ACTIVE"):
                    print(line[3:].strip())
                    for nxt in lines[i + 1:]:
                        if nxt.startswith("## "):
                            break
                        if nxt.strip().startswith("- [ ]"):
                            print(f"  {nxt.strip()}")
                    print()
                    break
        blockers = preflight()
        n = sum(len(v) for v in blockers.values())
        for heading, items in blockers.items():
            if not items:
                continue
            print(f"\n{heading}")
            for x in items:
                print(f"    {x}")
        if n:
            print(f"\n{n} outstanding item(s). Probes are the LAST step: settling "
                  f"one cell is worthless while an item's fixture is unread or its "
                  f"gold does not reconcile.")
        else:
            print("nothing outstanding — probes are the right next step")
        return 2 if n else 0
    if a[:1] == ["--conflicts"]:
        conflicts = declaration_conflicts()
        for c in conflicts:
            print(f"  {c}")
        if not conflicts:
            print("  no declaration is contradicted by a recorded measurement")
        return 2 if conflicts else 0
    print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
    print(__doc__.strip().splitlines()[3].strip(), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
