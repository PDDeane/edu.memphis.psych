#!/usr/bin/env python3
"""Probe a candidate rule in THE SWEEP'S OWN ENVELOPE, on a subset of cells.

    python3 faithful_probe.py ITEM 6,9,15 [--runs 4] [--side python]

WHY THIS REPLACES HAND-BUILT PROBE ENVELOPES. On 2026-09-07 eight of nine recent
probes were voided by `probe.control_gate`: each hand-built a prompt around the
correct rule text, and the prompt is not the text. Q4c's shipped prompt is 9438
characters over twelve checklist lines -- both consequence slots, the keyword
advisory, the `no_consequences` gate, five deduction codes including the
`C_NOT_CONSEQUENCE` charge gold levies, a `confident` slot -- and the rule text
under test was 1085 of them, ELEVEN PER CENT. The missing 89% is what decided
the answers, so the probes measured their own envelopes:

    Q44's route-5 probe counted p6 at 4 where the shipped prompt counts 3, so
    "does subtracting one duplicate take p6 from 3 to 2" was untestable in it.
    Q56's habit probe credited p11's duplicate that the shipped prompt catches
    12 of 12, and its CONTROL arm -- the unmodified shipped text -- answered
    p9's second box `met` where the shipped prompt answers `wrong_kind` 12/12.

THE FIX IS NOT A BETTER HAND-BUILT PROMPT. It is to stop building one.
`agreement.py --items ITEM --participants ...` runs the real assembled prompt
through the real scorer on whichever cells you name, so the envelope is the
sweep's BY CONSTRUCTION and no control arm is needed: the ledger's own numbers
are the control, because they came through this same path.

WHAT IT COSTS: the same per call as a hand-built probe, on a subset of cells
rather than all twenty. A target plus six falsifiers at 4 runs is 28 calls.

HOW TO USE IT, and the order matters:
  1. build the candidate into the rubric, in ONE file the design is read from;
  2. register it in `enforcement.DESIGNED_TEXT` so designed == shipped is checked;
  3. `leakage.gate((ITEM,))` on the BUILT tree -- a pre-build check on raw text
     is worthless, it reads clean on a student's own sentence;
  4. `olx_prompts.py --write`, then CONFIRM the text is in `measured._olx(h)`:
     the `.olx` is what both measured sides are served, and a rubric edit alone
     ships nothing;
  5. run THIS, on the target plus the falsifiers `probe_falsifiers` names;
  6. revert if it fails -- the sweep is only for a candidate that survives here.

Reports per cell: gold, what the ledger recorded BEFORE the build, and what the
candidate scores now, so a movement is read against a real baseline rather than
against a remembered one. `--side python` needs no idmap dump (the harness parses
the `.olx` directly); the olx side does, so this defaults to python.
"""
import argparse
import collections
import json
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("item")
    ap.add_argument("cells", help="comma-separated participant ids")
    ap.add_argument("--runs", type=int, default=4)
    ap.add_argument("--side", default="olx", choices=["olx"])
    ap.add_argument("--slots", default="",
                    help="comma-separated slots to print per cell")
    ap.add_argument("--force-checks", dest="force_checks", action="store_true",
                    help="pass --force-checks to agreement.py. SEPARATE from "
                         "--force, which passes --force-probe: they are "
                         "different gates and conflating them is how a probe on "
                         "one item gets forced past another item's unfinished "
                         "edit. Use this only when THIS item's structural "
                         "finding is what this probe settles -- e.g. a new slot "
                         "whose receipt this run is about to earn.")
    ap.add_argument("--force", action="store_true",
                    help="pass --force-probe to agreement.py. The preflight gate "
                         "refuses a probe while items are outstanding, and its "
                         "own message sanctions this flag when THIS PROBE is "
                         "what settles one of them. Kept explicit, per run, so "
                         "the override is a decision and not a default.")
    a = ap.parse_args()

    import cross_path as X0
    import measured as M

    cells = [int(x) for x in a.cells.split(",") if x.strip()]
    form = M._jobs()[a.item]["handout"]

    # THE BASELINE MUST BE READ BEFORE THE RUN, and it is the ledger's, not a
    # fresh measurement: the ledger came through this same envelope, which is the
    # whole point of using it.
    bands = M.cell_bands()
    unusable = M.probe_unusable(a.item)
    gold = {}
    for pid in cells:
        g = M.gold_cell(a.item, pid) or {}
        gold[pid] = g.get("score")
    dropped = [pid for pid in cells if pid in unusable
               and "dropped by exclusions" in unusable[pid]]
    if dropped:
        print(f"  REFUSING: {dropped} are excluded cells and are never evidence "
              f"(measured.exclusions). Drop them from the cell list.")
        return 1

    # CELLS WHOSE GOLD CHARGE RESEMBLES A TARGET'S, which `probe_falsifiers`
    # CANNOT name. That reader answers "does gold CREDIT this box", so it lists
    # only cells whose credit is certain -- and on Q4c that set was DISJOINT from
    # the cells shaped like the target. p9 is charged on both boxes; p4 is
    # charged on one, `charged_box_unknown`, so it was never a falsifier
    # candidate. The habit head probed PROCEED on eight cells, swept 17/19 ->
    # 16/19, and p4 -- 9/12 to 3/6 -- was the cell it cost. The most similar cell
    # in SHAPE was excluded by construction.
    # So: any cell gold charges AT ALL is a cell a stricter rule can flip, and a
    # subset that omits one cannot support a PROCEED.
    charge_shaped = {}
    for pid in range(1, 21):
        if pid in unusable and "dropped by exclusions" in unusable[pid]:
            continue
        b = M.gold_charge_bounds(a.item, pid)
        if b and b[1]:
            charge_shaped[pid] = b[1]
    omitted = sorted(set(charge_shaped) - set(cells))

    # CAN THE SLOT UNDER TEST EVEN MOVE ON THESE CELLS? Added 2026-09-08 after
    # cycle 5 spent ~52 calls on Q1 to test a `utb_stated` rule, and only TWO of
    # its thirteen cells could respond: `utb_stated` is stably `met` 12/12 on
    # eighteen of Q1's twenty cells, flaps on p17 alone, and is stably `absent`
    # on p20. Eleven of the thirteen probed were in the unresponsive set, and
    # BOTH of the probe's WORSE verdicts came from there -- 2/4 against an 8/12
    # baseline and 3/4 against 10/12, neither distinguishable from sampling, on
    # cells that flap for an unrelated reason (Q1's +-1 counting drift, which is
    # subgoal Q60's class and cannot answer a rule about this slot at all).
    #
    # So the verdict was decided by cells the rule could not reach. This is the
    # same failure as the charge-shaped omission above, from the other end: that
    # one MISSES cells a rule can flip, this one COUNTS cells it cannot.
    #
    # DIRECTION MATTERS, so this reports rather than assumes. A cell where the
    # slot sits stably on the SATISFYING verdict (the first in its list) cannot
    # GAIN -- but a tightening can still break it, so it is a control, not
    # waste. A cell stably on a non-satisfying verdict cannot LOSE. Only a cell
    # where the slot FLAPS is discriminating in both directions.
    reach = {}
    if [x for x in a.slots.split(",") if x.strip()]:
        import collections

        import enforcement as ENF
        import forms as _H_R

        want = [x.strip() for x in a.slots.split(",") if x.strip()]
        # The view, not the module: see `handouts._RubricView`.
        rubric = _H_R.config(M._jobs()[a.item]["handout"])["rubric"]
        credit = rubric.BY_ID[a.item].get("credit") or []
        first = {c["what"]: (c.get("verdicts") or [None])[0] for c in credit}
        # AN UNSCORED SLOT HAS NO GAIN OR LOSS TO CLASSIFY. `reasons_failing`
        # on Q2 is a COUNT (verdicts 0/1/2/3) with no `pts`: it feeds the scored
        # count and charges nothing itself, so "satisfied on its first verdict"
        # means only "answered 0" and says nothing about credit. Reading the
        # gain/lose table off it on 2026-09-08 produced "this list discriminates
        # on one cell", which was an artifact of the heuristic meeting a slot
        # shape it does not fit -- the list was fine and its real target, p6 at
        # 4/12, was not even in the classification.
        scored = {c["what"] for c in credit if c.get("pts") is not None}
        for slot in want:
            if slot not in first:
                continue
            if slot not in scored:
                print(f"  REACH: {slot} is UNSCORED (no pts) -- gain/lose does "
                      f"not apply to it. It feeds a scored slot; probe the cells "
                      f"whose COUNT moves, and read those instead.")
                continue
            for pid in cells:
                c = collections.Counter()
                for side in ("olx",):
                    try:
                        doc = M._runs_doc(a.item, side)
                    except Exception:
                        continue
                    for run in (doc or {}).get("runs") or []:
                        for r in (run.get("results") or []):
                            got = X0.result_cell(r)
                            if not got or got[1] != pid:
                                continue
                            x = (got[3] or {}).get(slot)
                            if not ENF.no_verdict(x):
                                c[str(x)] += 1
                if not c:
                    continue
                if len(c) > 1:
                    kind = "FLAPS"
                elif set(c) == {str(first[slot])}:
                    kind = "stably satisfying -- cannot GAIN"
                else:
                    kind = "stably unsatisfied -- cannot LOSE"
                reach[(slot, pid)] = (kind, dict(c))

    print(f"  {a.item}, cells {cells}, {a.runs} runs, side {a.side}")
    print(f"  gold charges something on: "
          f"{ {p: charge_shaped[p] for p in sorted(charge_shaped)} }")
    if omitted:
        print(f"  *** {len(omitted)} CHARGE-SHAPED CELL(S) NOT IN THIS RUN: "
              f"{omitted} -- a stricter rule can flip a charge on any of them, "
              f"and this probe cannot see it. Add them, or read the verdict as "
              f"INCOMPLETE. ***")
    if reach:
        flap = sorted({p for (s, p), (k, _) in reach.items() if k == "FLAPS"})
        nogain = sorted({p for (s, p), (k, _) in reach.items()
                         if k.startswith("stably satisfying")})
        nolose = sorted({p for (s, p), (k, _) in reach.items()
                         if k.startswith("stably unsatisfied")})
        print(f"  REACH of {a.slots} over these cells:")
        for (s, pid), (kind, c) in sorted(reach.items()):
            print(f"      p{pid}/{s}: {kind:<38}{c}")
        print(f"    discriminating (FLAPS): {flap or 'NONE'}")
        print(f"    cannot gain: {nogain or 'none'}    "
              f"cannot lose: {nolose or 'none'}")
        if not flap and not nolose:
            print(f"  *** REFUSING: not one named cell can move on {a.slots}. "
                  f"Every one sits stably on the satisfying verdict, so a "
                  f"loosening cannot show anything and only a tightening could "
                  f"-- and then these are CONTROLS, not evidence. Name the "
                  f"cells where the slot flaps or is unsatisfied. ***")
            return 1
    print(f"  prompt_sha now: {M.prompt_sha(a.item, a.side)}")
    print(f"  THE ENVELOPE IS agreement.py's OWN -- no control arm is needed, "
          f"because the ledger below came through it too.\n")

    out = pathlib.Path(tempfile.mkdtemp(prefix="faithful_")) / f"{a.item}.json"
    import agreement as _ag_mod   # by import, not by this file's folder
    cmd = [sys.executable, "-u", _ag_mod.__file__,
           "--form", str(form), "--items", a.item,
           "--participants", *[str(c) for c in cells],
           "--runs", str(a.runs), "--backend", "lo", "--out", str(out)]
    if a.force:
        cmd.append("--force-probe")
    if a.force_checks:
        cmd.append("--force-checks")
    print("  " + " ".join(cmd[3:]) + "\n", flush=True)
    rc = subprocess.call(cmd)
    if not out.exists():
        print(f"\n  agreement.py exited {rc} and wrote nothing. Read its output "
              f"above: a refusal here is usually preflight, a structural check "
              f"or leakage, and each of those is a real gate, not a nuisance.")
        return 1

    # PREFER THE RUNS FILE. agreement.py writes `--out` as the PUBLISHED median
    # and a sibling `.runs.json` holding every run. Reading only the median gave
    # one value per cell, so a 4-run probe reported "0/1" against a 12-run
    # ledger baseline -- a comparison with no spread on one side of it, which is
    # the habit `run_totals` exists to prevent.
    runs_path = out.with_suffix("").with_suffix(".runs.json")
    if not runs_path.exists():
        runs_path = pathlib.Path(str(out).replace(".json", ".runs.json"))
    rows = []
    if runs_path.exists():
        doc = json.loads(runs_path.read_text())
        for run in (doc.get("runs") if isinstance(doc, dict) else doc) or []:
            rows.extend(run.get("results") or [])
        print(f"  read {len(rows)} result(s) across "
              f"{len((doc.get('runs') if isinstance(doc, dict) else doc) or [])} "
              f"run(s) from {runs_path.name}")
    else:
        res = json.loads(out.read_text())
        rows = res if isinstance(res, list) else res.get("results") or []
        print("  NO .runs.json -- reading the PUBLISHED MEDIAN only, so the "
              "'candidate now' column below has one observation per cell")
    got: dict = collections.defaultdict(list)
    slots = collections.defaultdict(lambda: collections.Counter())
    import cross_path as X
    for r in rows:
        item, pid, score, verdicts = X.result_cell(r)
        if pid is None:
            continue
        got[pid].append(score)
        for s in [x for x in a.slots.split(",") if x.strip()]:
            slots[(pid, s)][str(M.slot_answer(r, s))] += 1

    print(f"\n  {'cell':<7}{'gold':<7}{'ledger before':<22}{'candidate now':<26}"
          f"verdict")
    moved_right, moved_wrong = [], []
    for pid in cells:
        b = bands.get(f"{a.item}/p{pid}")
        before = f"{b[0]}/{b[1]}" if b else "-"
        sc = [x for x in got.get(pid, []) if x is not None]
        right = sum(1 for x in sc if gold[pid] is not None
                    and abs(x - gold[pid]) < 1e-9)
        now = f"{right}/{len(sc)}  {sorted(set(sc))}" if sc else "no result"
        rate_b = (b[0] / b[1]) if b and b[1] else None
        rate_n = (right / len(sc)) if sc else None
        v = "-"
        if rate_b is not None and rate_n is not None:
            if rate_n > rate_b + 1e-9:
                v = "BETTER"
                moved_right.append(pid)
            elif rate_n < rate_b - 1e-9:
                v = "WORSE"
                moved_wrong.append(pid)
            else:
                v = "same"
        note = ""
        if pid in unusable:
            note = f"   [{unusable[pid][:34]}]"
        print(f"  p{pid:<6}{str(gold[pid]):<7}{before:<22}{now:<26}{v}{note}")
    for (pid, s), c in sorted(slots.items()):
        print(f"      p{pid}/{s}: {dict(c)}")

    print(f"\n  better: {moved_right or 'none'}   worse: {moved_wrong or 'none'}")
    if moved_right and not moved_wrong and omitted:
        print(f"  INCOMPLETE, NOT PROCEED -- it gained {moved_right} and cost "
              f"nothing among the cells run, but {len(omitted)} cell(s) gold "
              f"CHARGES were not run: {omitted}. That is the configuration this "
              f"harness got wrong on Q4c: probe said proceed, sweep lost a cell, "
              f"and the lost cell was a charge-shaped one left out. Re-run "
              f"including them before spending a sweep.")
    elif moved_right and not moved_wrong:
        print("  PROCEED to a full sweep -- it gained cells and cost none, and "
              "every cell gold charges was in the run. A subset still cannot see "
              "a cell you did not run, so compare all of them after the sweep.")
    elif moved_wrong:
        print("  DO NOT SWEEP -- it costs a cell in the real envelope. That is a "
              "measurement, not a probe artifact.")
    else:
        print("  NO EFFECT in the real envelope. A rule that changes no answer is "
              "prose in a prompt; revert it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
