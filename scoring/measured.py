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
        for pid_s, right in sorted((rec.get("excluded_cells") or {}).items(),
                                   key=lambda kv: int(kv[0])):
            if runs == 0 or right < runs:
                continue
            out.append(verdict(
                f"{item}/p{pid_s} is EXCLUDED, yet scores right every recorded "
                f"run — the exclusion",
                right, runs,
                f"Remove {item}/p{pid_s} from its exclusion and let it count"))
    return out


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
