"""Compare two measurements of one item, and refuse to call a move a result.

    python3 compare_runs.py 3 1a BEFORE/1a.runs.json AFTER/1a.runs.json

Every QC change ends in the same arithmetic: two sweeps of the same item, same
denominator, and the question of what moved. That arithmetic kept being
rewritten inline — once per experiment, in a scratch script, each time with a
slightly different idea of what counts — and the versions did not agree, which
is the failure this project keeps re-learning (see `scored_exactly`, which had
six implementations and two printed answers).

So the arithmetic lives here, and it calls the project's own definitions rather
than re-deriving them: `scored_exactly` for whether a cell is right,
`apply_corrected_gold` for which gold row is authoritative, `cell_exclusions`
for the denominator, `rebuild_gold_1c` for the one item whose gold is rebuilt.

The part that matters more than the arithmetic: this tool does NOT print a
directional verdict for a cell that moved, at all. It prints PROBE REQUIRED and
the command that settles it. Not even a clean 3/3-to-0/3 flip is exempt — see
the note in `compare`, where Q2's p17 retired that exemption.

That is not a style preference. QUALITY_CONTROL.md has said "when a 3-run
measurement moves ONE cell, probe that cell before believing it in either
direction" since the day a probe overturned two such moves — and on 2026-08-24 a
scratch comparison printed `<-- LOST` and `<-- gained` for two single-run moves,
and both were written up as conclusions ("a wobble inside the variance band",
"the rewrite fixed it") with no probe run. The rule was in the guide, had been
read, and lost to a script whose output format asserted a result. A comparison
that hands you a verdict it has not earned will be believed, so this one does
not offer the option.
"""
from __future__ import annotations

import json
import sys
import warnings

warnings.filterwarnings("ignore")

import gold
import handouts as H

_LOADERS = {1: gold.load_h1, 2: gold.load_h2, 3: gold.load_h3}


def gold_for(handout: int, item: str) -> dict:
    g = H.apply_corrected_gold(_LOADERS[handout](), handout)
    if item == "1c":
        import agreement_app as APP
        g, _ = APP.rebuild_gold_1c({p: dict(v) for p, v in g.items()})
    return g


def tally(path: str, handout: int, item: str, g: dict) -> dict[int, list[bool]]:
    """Per participant, was the cell right in each run? Excluded cells omitted."""
    ex = set(H.cell_exclusions(handout, item))
    out: dict[int, list[bool]] = {}
    for run in json.load(open(path))["runs"]:
        for c in run["results"]:
            pid, s = c["participant_id"], c.get("score")
            row = (g.get(pid) or {}).get(item) or {}
            if row.get("score") is None or pid in ex:
                continue
            out.setdefault(pid, []).append(
                s is not None and H.scored_exactly(item, row["score"], s))
    return out


def compare(handout: int, item: str, before_path: str, after_path: str) -> int:
    g = gold_for(handout, item)
    before = tally(before_path, handout, item, g)
    after = tally(after_path, handout, item, g)
    shared = sorted(set(before) & set(after))
    if not shared:
        print("no cells in common — different denominators?")
        return 1
    nb = min(len(before[p]) for p in shared)
    na = min(len(after[p]) for p in shared)

    totals = lambda d, n: [sum(1 for p in shared if d[p][i]) for i in range(n)]
    print(f"{item}: {len(shared)} counted cells")
    print(f"  before  {totals(before, nb)}   ({nb} runs)")
    print(f"  after   {totals(after, na)}   ({na} runs)")

    moved, probe = [], []
    for p in shared:
        b = sum(1 for v in before[p][:nb] if v)
        a = sum(1 for v in after[p][:na] if v)
        if b / nb == a / na:
            continue
        # There is no such thing as a decisive per-cell move in three passes,
        # in either direction, however clean it looks.
        #
        # This function used to exempt a cell that was uniform before and
        # uniform after — 3/3 to 0/3 reads like a fact rather than an estimate.
        # Q2's p17 is why it does not: across six sweeps it scores 10 of 18, and
        # it produced 0/3, 2/3 and 3/3 readings in both directions, including
        # three consecutive uniform runs each way. A 50/50 cell throws uniform
        # triples about a quarter of the time, so uniformity IS the thing three
        # passes cannot distinguish from a real flip. Exempting those cells put
        # the exemption exactly where acting on noise is most tempting, because a
        # clean flip is what looks worth chasing.
        #
        # So every move goes to the probe list, and `moved` stays only to carry
        # cells whose probe has already been run and recorded elsewhere.
        probe.append((p, b, a))

    if moved:
        print("\n  decisive moves (uniform before, uniform after):")
        for p, b, a in moved:
            print(f"    p{p:<3} gold {g[p][item]['score']:<4g} "
                  f"{b}/{nb} -> {a}/{na}  {'REGRESSED' if a == 0 else 'FIXED'}")
    if probe:
        stable = [p for p in shared
                  if all(before[p][:nb]) and all(after[p][:na])
                  and p not in [q for q, _, _ in probe + moved]]
        controls = " ".join(str(p) for p in stable[:2])
        print("\n  PROBE REQUIRED — a three-pass rate cannot tell a real change "
              "from the\n  item's own variance, and a clean 3/3-to-0/3 flip least "
              "of all (see p17):")
        for p, b, a in probe:
            print(f"    p{p:<3} gold {g[p][item]['score']:<4g} {b}/{nb} -> {a}/{na}")
        pids = " ".join(str(p) for p, _, _ in probe)
        print(f"\n    python3 agreement.py --handout {handout} --items {item} \\\n"
              f"        --participants {pids} {controls} --runs 6 --workers 4 \\\n"
              f"        --out OUT/{item}.json")
        print(f"    (the trailing {controls or 'control'} are CONTROLS: cells "
              f"stable in both sweeps. If they\n     wobble too, the item's "
              f"variance moved and the target was never the story.)")
        print("\n  NOT REPORTABLE until the probe above is run.")
    if not moved and not probe:
        print("\n  no cell changed.")

    # A sweep is also the moment to ask whether this item's DECLARATIONS still
    # describe it. The enforcement suite asks the same question, but the review
    # of a fresh sweep is when someone is actually looking at the item.
    try:
        import measured as MEAS
        mine = [c for c in MEAS.declaration_conflicts()
                if f"{item}/" in c or f"{item!r}" in c]
        if mine:
            print("\n  DECLARATIONS THIS SWEEP CONTRADICTS:")
            for c in mine:
                print(f"    {c}")
    except Exception as e:                                  # never block a review
        print(f"\n  (declaration check unavailable: {e})")
    return 2 if probe else 0


def main() -> int:
    if len(sys.argv) != 5:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 1
    handout, item, before_path, after_path = sys.argv[1:]
    return compare(int(handout), item, before_path, after_path)


if __name__ == "__main__":
    raise SystemExit(main())
