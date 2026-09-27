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
for the denominator, `rebuild_declared_gold` for the one item whose gold is rebuilt.

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
import os
import sys
import warnings

warnings.filterwarnings("ignore")

# `paths` FIRST: it puts this course's `scoring/<course>/` and the general
# `scorers/` on `sys.path`, and the imports just below are modules that live
# there. Importing them before `paths` raises ModuleNotFoundError -- measured
# on 13 modules the day those directories were split out.
import paths  # noqa: F401  (import order is load-bearing; see above)
import gold
import forms as H

_LOADERS = {1: gold.load_h1, 2: gold.load_h2, 3: gold.load_h3}



import paths as _paths_probed

PROBED = str(_paths_probed.COURSE_PROBED)


def _probe_ledger() -> list[dict]:
    try:
        with open(PROBED) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return []


def record_probe(item: str, after_sha: str, cells: list[int], artifact: str,
                 runs: int) -> None:
    """File a probe against the exact prompt it was run on.

    ONE ENTRY PER ARTIFACT, not per prompt. `probed_cells` unions across
    entries, so several probes of the same prompt are meant to accumulate --
    a change that moves five cells is often covered by two runs of different
    subsets. Keying the replacement on (item, sha) alone discarded the earlier
    probe every time a second was filed, so the gate asked for cells that had
    already been probed and no sequence of probes could ever satisfy it.
    Re-filing the SAME artifact still replaces rather than duplicates.
    """
    # NORMALISED TO A ROOT TOKEN. `artifact` is an IDENTITY here, compared by
    # equality to replace an earlier probe of the same run -- so an absolute
    # path and its token form are two different artifacts, and a re-probe would
    # append rather than replace. The ledger's fifteen existing entries were
    # converted on 2026-09-26, after every one of them was found broken by the
    # data-root move that morning with nothing reporting it.
    artifact = _paths_probed.as_record_path(artifact)
    led = _probe_ledger()
    led = [e for e in led if not (e["item"] == item and e["after_sha"] == after_sha
                                  and e.get("artifact") == artifact)]
    led.append({"item": item, "after_sha": after_sha, "cells": sorted(set(cells)),
                "artifact": artifact, "runs": runs})
    with open(PROBED, "w") as fh:
        json.dump(led, fh, indent=1, sort_keys=True)
        fh.write("\n")


def probed_cells(item: str, after_sha: str) -> set[int]:
    """Cells covered by a >=6-run probe of THIS prompt. A probe of a different
    prompt proves nothing about this one, which is why the sha is the key."""
    return {c for e in _probe_ledger()
            if e["item"] == item and e["after_sha"] == after_sha and e["runs"] >= 6
            for c in e["cells"]}


def _verdict(item: str, movers: list[int]) -> int:
    """The line that makes the rule automatic rather than remembered.

    `compare_runs` has always printed PROBE REQUIRED and exited 2, and a 1-cell
    median drop across three items was still read as a loss and reverted without
    a probe. The message was advisory because the READER draws the verdict. So
    the verdict is printed here, and it is withheld unless probe evidence for
    this exact prompt is on file.
    """
    if not movers:
        print("\n  VERDICT PERMITTED — no cell moved; the medians speak for themselves.")
        return 0
    try:
        import measured as _m
        sha = _m.prompt_sha(item)
    except Exception as e:
        print(f"\n  VERDICT WITHHELD — cannot resolve this item's prompt sha ({e}).")
        return 2
    have = probed_cells(item, sha)
    missing = [p for p in movers if p not in have]
    if missing:
        print(f"\n  ##### VERDICT WITHHELD on {item} #####")
        print(f"  {len(missing)} moved cell(s) have no 6-run probe of prompt {sha}: "
              + ", ".join(f"p{p}" for p in missing))
        print("  KEEP and REVERT are both unsupported until those are probed. A")
        print("  three-pass rate cannot separate a real change from this item's")
        print("  own variance, so a median that moved by one or two cells is not")
        print("  yet evidence of anything in either direction.")
        print("  Run the probe above, then:")
        print(f"    python3 compare_runs.py --record-probe {item} "
              f"OUT/<probe>/{item}.runs.json")
        return 2
    print(f"\n  VERDICT PERMITTED on {item} — all {len(movers)} moved cell(s) "
          f"probed at prompt {sha}.")
    return 0


def gold_for(form: int, item: str) -> dict:
    g = H.apply_corrected_gold(_LOADERS[form](), form)
    if H.rebuilds_gold(item):
        import agreement_app as APP
        g, _ = APP.rebuild_declared_gold({p: dict(v) for p, v in g.items()})
    return g


def tally(path: str, form: int, item: str, g: dict) -> dict[int, list[bool]]:
    """Per participant, was the cell right in each run? Excluded cells omitted."""
    ex = set(H.cell_exclusions(form, item))
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


def _regressions_against_recorded(form, item, after, na, g) -> None:
    """Cells that are right in the RECORDED state and wrong now.

    A comparison against an old baseline cannot see a gain being undone. DAY2/p8
    was 0 of 3 in the baseline, was fixed to 5 of 6 by a committed change, and
    was knocked back to 0 of 3 by a later edit that never mentioned the gate it
    moved — and the diff against the baseline read "no change", because both ends
    were 0 of 3. It was found only by printing per-cell detail and remembering.

    So every comparison also diffs against whatever the ledger currently records
    for this item, which is the best state anyone has measured. A committed gain
    being silently undone becomes a line of output instead of something you have
    to hold in your head.
    """
    try:
        import measured as MEAS
        # Through MEAS.entry, not the raw ledger: the ledger grew a per-side
        # dimension on 2026-08-28 and the accessor owns that shape.
        rec = MEAS.entry(item)
        path = MEAS._runs_path(item)
        if rec.get("pending") or not path:
            return
        recorded = tally(path, form, item, g)
    except Exception as e:                       # never block a comparison
        print(f"\n  (recorded-state check unavailable: {e})")
        return

    nr = min((len(v) for v in recorded.values()), default=0)
    if not nr:
        return
    lost = []
    for p, runs in sorted(recorded.items()):
        if p not in after:
            continue
        was = sum(1 for v in runs[:nr] if v) / nr
        now = sum(1 for v in after[p][:na] if v) / na
        if now < was:
            lost.append((p, sum(1 for v in runs[:nr] if v), nr,
                         sum(1 for v in after[p][:na] if v), na))
    if lost:
        print(f"\n  REGRESSION AGAINST THE RECORDED STATE ({rec.get('out')}, "
              f"{rec.get('numerator')}/{rec.get('denominator')}) — these are "
              f"cells\n  an EARLIER change had already won, and this one gives "
              f"back:")
        for p, wb, wn, ab, an in lost:
            print(f"    p{p:<3} gold {g[p][item]['score']:<4g} {wb}/{wn} "
                  f"recorded -> {ab}/{an} now")
        print("  A flat median can hide this: a gain and a regression of similar "
              "size cancel.")


def compare(form: int, item: str, before_path: str, after_path: str) -> int:
    g = gold_for(form, item)
    before = tally(before_path, form, item, g)
    after = tally(after_path, form, item, g)
    shared = sorted(set(before) & set(after))
    if not shared:
        print("no cells in common — different denominators?")
        return 1
    nb = min(len(before[p]) for p in shared)
    na = min(len(after[p]) for p in shared)

    totals = lambda d, n: [sum(1 for p in shared if d[p][i]) for i in range(n)]
    tb, ta = totals(before, nb), totals(after, na)
    med = lambda t: sorted(t)[len(t) // 2]
    # The median first and labelled, the runs second and labelled as runs. A bare
    # three-run array invites the reader to quote its best line, especially when
    # the best line agrees with the change just made: 1a was reported at 18/20
    # off runs of 17, 17, 18. The number to report is the median, so it is the
    # number printed first.
    print(f"{item}: {len(shared)} counted cells")
    print(f"  before  MEDIAN {med(tb)}/{len(shared)}   (runs {tb})")
    print(f"  after   MEDIAN {med(ta)}/{len(shared)}   (runs {ta})")
    if med(ta) != med(tb):
        print(f"  median moved {med(tb)} -> {med(ta)}; the per-cell picture below "
              f"decides whether that is real")

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
        print(f"\n    python3 agreement.py --handout {form} --items {item} \\\n"
              f"        --participants {pids} {controls} --runs 6 --workers 4 \\\n"
              f"        --out OUT/{item}.json")
        print(f"    (the trailing {controls or 'control'} are CONTROLS: cells "
              f"stable in both sweeps. If they\n     wobble too, the item's "
              f"variance moved and the target was never the story.)")
        print("\n  NOT REPORTABLE until the probe above is run.")
    if not moved and not probe:
        print("\n  no cell changed.")

    verdict = _verdict(item, [p for p, _, _ in probe])

    _regressions_against_recorded(form, item, after, na, g)

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
    return 2 if (probe or verdict) else 0


def main() -> int:
    if sys.argv[1:2] == ["--record-probe"]:
        if len(sys.argv) != 4:
            print("usage: compare_runs.py --record-probe ITEM PROBE.runs.json",
                  file=sys.stderr)
            return 1
        import measured as _m
        item, art = sys.argv[2], sys.argv[3]
        doc = json.loads(open(art).read())
        cells = sorted({c["participant_id"] for r in doc["runs"] for c in r["results"]})
        record_probe(item, _m.prompt_sha(item), cells, art, len(doc["runs"]))
        print(f"probe filed: {item} at {_m.prompt_sha(item)}, {len(doc['runs'])} runs, "
              f"cells {cells}")
        return 0
    if len(sys.argv) != 5:
        print(__doc__.strip().splitlines()[2].strip(), file=sys.stderr)
        return 1
    form, item, before_path, after_path = sys.argv[1:]
    return compare(int(form), item, before_path, after_path)


if __name__ == "__main__":
    raise SystemExit(main())
