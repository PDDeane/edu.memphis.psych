#!/usr/bin/env python3
"""Re-run cells whose LLM call never came back, before anything reads the sweep.

WHY THIS IS A CERTIFICATION STEP AND NOT AN AFTERTHOUGHT. A cell the provider
never answered is not a low score -- it is an ABSENT measurement, and every
number computed over it is computed over a denominator that quietly shrank.
`check_every_sweep_is_recorded` already refuses to call such a sweep recordable
and says why: "a sweep with FAILED cells is not a recordable sweep ... Fill them
with a cell-level sweep and re-fold BEFORE recording". This does the filling, so
a certification either ends with a complete measurement or says plainly that it
could not get one.

WHAT A MISSED CALL LOOKS LIKE. On a clean run every web cell carries `ok: true`
with `status` either LLM_RESPONSE_READY or `derived` -- measured across 520
cells of the 2026-09-27 run, all 520 clean, `attempts` 1 throughout. So the
predicate is the negative of that, and it is deliberately BROAD: any cell that
is not affirmatively ok, or that carries no verdicts and no score, counts as
missed. Over-reporting costs a re-run; under-reporting corrupts the ledger.

IT RETRIES ONCE, THEN REPORTS. A loop that keeps re-running until everything
passes would hide a provider that is down, and would do it while spending money.
One pass, then the truth.
"""

import glob
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _missed(cell: dict) -> bool:
    if cell.get("ok") is not True:
        return True
    if cell.get("status") in (None, "", "ERROR", "LLM_ERROR"):
        return True
    # A derived cell has no LLM call to miss; anything else must have answered.
    if cell.get("status") != "derived" and not (cell.get("verdicts")
                                                or cell.get("checks")
                                                or cell.get("score") is not None):
        return True
    return False


def _paper_missed(item: dict) -> bool:
    """A paper item whose call did not come back.

    THE PAPER SHAPE IS NOT THE WEB SHAPE, which is the whole reason this
    function exists separately. score.py writes one `participant_NNN.json` per
    participant per handout, each holding an `items` array; there is no `cell`,
    no `ok`, and no `status`. A missed call shows up as a null `score`, usually
    with an `error` like "no JSON object in output: ''" and `escalate: true`.
    """
    return item.get("score") is None or bool(item.get("error"))


def scan_paper(paper_dir: str) -> dict:
    """-> {handout: [(participant, item_id), ...]} for calls that did not return.

    KEYED BY HANDOUT because that is the unit score.py re-runs: it scores a
    whole handout per invocation, so a refill re-runs `--handout N`, exactly as
    the web side re-runs an item.
    """
    out: dict = {}
    pat = re.compile(r"(?:^|/)r(\d+)/h(\d+)/participant_(\d+)\.json$")
    for path in sorted(glob.glob(os.path.join(
            paper_dir, "r*", "h*", "participant_*.json"))):
        m = pat.search(path)
        if not m:
            continue
        run, handout, pid = m.group(1), m.group(2), m.group(3)
        try:
            doc = json.load(open(path, encoding="utf8"))
        except Exception:
            continue
        for item in (doc.get("items") or []):
            if _paper_missed(item):
                out.setdefault((run, handout), []).append((pid, item.get("item_id")))
    return out


def scan(web_dir: str) -> dict:
    """-> {item: [cell, ...]} for cells whose call did not come back."""
    out = {}
    for path in sorted(glob.glob(os.path.join(web_dir, "*.json"))):
        item = os.path.basename(path)[:-len(".json")]
        try:
            doc = json.load(open(path, encoding="utf8"))
        except Exception:
            continue
        bad = [r.get("cell") for r in (doc.get("results") or []) if _missed(r)]
        if bad:
            out[item] = bad
    return out


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: fill_missed_calls.py <one-run-dir> <idmap.json>")
        return 2
    one, idmap = sys.argv[1], sys.argv[2]
    web = os.path.join(one, "web")
    if not os.path.isdir(web):
        print(f"  no web sweep at {web}; nothing to fill")
        return 0

    paper = os.path.join(one, "paper")
    missed = scan(web)
    pmissed = scan_paper(paper) if os.path.isdir(paper) else {}
    total = sum(len(v) for v in missed.values())
    ptotal = sum(len(v) for v in pmissed.values())

    # BOTH SIDES, and the paper half was missing until 2026-09-30. This scanned
    # only `one-run/web` and reported "the sweep is complete" while two paper
    # item-scores of 520 had come back with no score at all, one of them
    # carrying `no JSON object in output`. A step written to stop a denominator
    # shrinking quietly was itself blind to an entire side.
    if pmissed:
        print(f"  {ptotal} missed paper call(s) across "
              f"{len(pmissed)} handout-run(s):")
        for (run, handout), cells in sorted(pmissed.items()):
            names = ", ".join(f"p{p}/{i}" for p, i in cells[:6])
            print(f"    r{run} h{handout}: {len(cells)} -- {names}")
        print("  Re-run those handouts through sweep_paper.sh and re-fold "
              "before recording: score.py scores a whole handout per "
              "invocation, so the handout is the unit to refill.")

    if not missed and not pmissed:
        print("  0 missed LLM call(s) on either side; the sweep is complete")
        return 0
    if not missed:
        return 1

    print(f"  {total} missed call(s) across {len(missed)} item(s): "
          f"{', '.join(sorted(missed))}")
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sweep = os.path.join(os.path.dirname(here), "scorers", "shell_scripts", "sweep_app.sh")

    # RE-RUN THE WHOLE ITEM, by removing its output so the sweep's own resume
    # picks it up. Merging a cell-level result back into the item document by
    # hand would be a second writer of that file, and the sweep is already the
    # one that knows its shape.
    for item in sorted(missed):
        p = os.path.join(web, f"{item}.json")
        try:
            os.remove(p)
        except OSError:
            pass
    env = dict(os.environ, ITEMS=" ".join(sorted(missed)))
    subprocess.run(["bash", sweep, web, idmap, "1"], env=env, check=False)

    still = scan(web)
    left = sum(len(v) for v in still.values())
    if left:
        print(f"  STILL {left} missed call(s) after one refill: "
              f"{', '.join(sorted(still))}")
        print("  The provider did not answer these on a second pass. Every number "
              "computed over them is computed over a denominator that shrank, so "
              "this certification does not carry a complete measurement.")
        return 1
    print(f"  refilled {total} cell(s); the sweep is now complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
