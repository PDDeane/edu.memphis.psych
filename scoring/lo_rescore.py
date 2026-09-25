#!/usr/bin/env python3
"""Re-score every recorded web cell through the SHIPPED scorer. Goal O's tail.

WHAT IT SETTLES. A recorded web column is stamped with the app's scoring sha.
When that code changes, the audit reports 26 columns as measured against code
that has moved -- correctly, because nothing said whether the change touched a
number. `WEB_CODE_NEUTRAL` used to settle it by re-scoring every covered cell
through agreement.py's python mirror of `scoreSlotSheet`; goal O eliminated the
mirror and the table retired with it.

THIS IS NOT THE MIRROR COMING BACK. It calls `scoreSlotSheet` itself, through
the goal-K bridge, with the eleven arguments `SlotSheetGrader` passes. Nothing
on this side decides anything about scoring: python reconstructs what the model
ANSWERED and hands it over.

THE RECONSTRUCTION IS `_recorded_payloads`', not a new one. That function was
retired with the comparison it fed, but its payload-building carried two facts
that were each paid for:

  * COMPUTED KEYS ARE EXCLUDED -- maps/equals/expect/forbid keys are recomputed
    by the scorer, and feeding them back in hands it its own prior conclusion.
  * A COUNT IS DECIDED BY THE SLOT SPEC, never by the value's type. The record
    flattens `count` and `verdict` into one column and the two sides flattened
    differently; a type test caught one and missed the other, and 454 cells
    across Q1, Q2, 2b and 3 failed their own control that way.

AND IT CARRIES ITS OWN POSITIVE CONTROL. A comparison that cannot fail reports
agreement it did not measure: an options bag once reached `explicitMax`, every
score came back NaN, `Math.abs(NaN - x) > 1e-9` was false, and every cell
"matched". `--control` adds 0.5 to every recorded value and requires EVERY cell
to move. If it does not, the run is refused rather than reported.
"""
from __future__ import annotations

import sys
from pathlib import Path


def _sheets_and_payloads(items=None, side="olx"):
    """({item: sheet}, [payload]) for every recorded cell on `side`."""
    import agreement as A
    import cross_path as X
    import measured as M
    import olx_prompts as O

    jobs = {j["item"]: j for _h, b in A.BLOCKS.items() for j in b.values()}
    sheets, payloads, skipped = {}, [], []
    for item in sorted(items or M._jobs()):
        job = jobs.get(item) or {}
        # EXCLUDED BY KIND, as `_recorded_payloads` excluded them: `1b`, `T1`
        # and `T2` are `data_presence` / `type_stated`, carry a slot sheet that
        # is NOT an `<LLMAction>`, and have no `olx` on their job. `load_action`
        # assembles its nine tables from an `<LLMAction>` opening tag, so there
        # is nothing here for it to read, and mirroring its assembly for these
        # three would be a SECOND sheet reader -- the divergence class this
        # project exists to close.
        #
        # THEIR NEUTRALITY RESTS ON DIFFERENT EVIDENCE, and it is not weaker:
        # all three are derived, with ZERO spread across twelve recorded runs
        # (20-20, 18-18, 18-18), and the 2026-09-25 confirmation reproduced each
        # recorded value exactly. A deterministic item that reproduces is not a
        # gap in the rescore; it is the same fact established another way.
        if item not in O.ACTION:
            skipped.append((item, f"{job.get('kind')!r}: a slot sheet that is "
                                  f"not an <LLMAction>; see the note in "
                                  f"_sheets_and_payloads"))
            continue
        try:
            act = A.load_action(job["olx"], O.ACTION[item])
        except Exception as e:
            skipped.append((item, f"sheet unreadable: {type(e).__name__}"))
            continue
        sheets[item] = {k: (act.get(k) or []) for k in
                        ("slots", "cover", "equals", "onlyif", "counts",
                         "expect", "requires", "forbid", "maps")}
        computed = {r["key"] for f in ("maps", "equals", "expect", "forbid")
                    for r in (act.get(f) or [])}
        counted = {sl["key"] for sl in act["slots"]
                   if sl.get("count_max") is not None}
        doc = M._runs_doc(item, side)
        for ri, run in enumerate((doc or {}).get("runs") or []):
            for ci, r in enumerate(run.get("results") or []):
                c = X.result_cell(r)
                if not c or c[2] is None:
                    continue
                picks = dict(X.result_picks(r) or {})
                ev = r.get("evidence") or {}
                checks = {}
                for k, v in (c[3] or {}).items():
                    if k in computed:
                        continue
                    d = {}
                    if k in counted:
                        d["count"] = v
                    elif v not in (None, ""):
                        d["verdict"] = v
                    if picks.get(k) is not None:
                        d["refers_to"] = picks[k]
                    if ev.get(k):
                        d["evidence"] = ev[k]
                    if d:
                        checks[k] = d
                smax = r.get("sheet_max") or r.get("max")
                if not smax:
                    continue
                payloads.append({"id": f"{item}|{ri}|{ci}|{c[1]}", "item": item,
                                 "checks": checks, "max": float(smax),
                                 "recorded": round(float(c[2]), 4)})
    return sheets, payloads, skipped


def rescore(items=None, side="olx", control=0.0):
    """Rows from the shipped scorer, one per recorded cell."""
    import lo_enforce

    sheets, payloads, skipped = _sheets_and_payloads(items, side)
    if control:
        payloads = [dict(p, recorded=round(p["recorded"] + control, 4))
                    for p in payloads]
    rows = lo_enforce.probe("score_recorded_sheets",
                            {"sheets": sheets, "payloads": payloads})
    return rows, skipped


def evidence_path():
    """Where a rescore's result is kept. Measurement evidence, so it lives in
    `$COURSE_DATA/out` beside the sweeps -- not in the repo, and not in
    `$COURSE_METADATA`, which holds what the course DECLARES rather than what a
    run measured."""
    import paths
    return Path(paths.OUT) / "rescore_evidence.json"


def record_evidence(rows, skipped, control_moved, control_total) -> dict:
    """Write what this rescore proved, per item, with its sha pair.

    THIS IS WHAT REPLACES `WEB_CODE_NEUTRAL`. That table was a hand-written
    claim that a pair of scoring shas could not have moved a number, and it was
    only ever as good as whoever wrote it. This is the same claim DERIVED: the
    sha it was measured from, the sha it was measured to, how many cells were
    re-scored and how many reproduced -- and the control, without which a run
    of zeroes reads exactly like perfect agreement.
    """
    import json as _json

    import measured as M

    by_item: dict = {}
    for r in rows:
        e = by_item.setdefault(r["item"], {"cells": 0, "reproduced": 0})
        e["cells"] += 1
        e["reproduced"] += 1 if r["same"] else 0
    for item, e in by_item.items():
        rec = (M.entry(item, "olx") or {})
        e["from"] = rec.get("scorer_sha")
        e["to"] = M.scorer_sha(item, "olx")
        e["ask_recorded"] = rec.get("ask_sha")
        e["ask_now"] = M.ask_sha(item, "olx")
    doc = {
        "measured_at": __import__("datetime").datetime.now()
                       .astimezone().isoformat(timespec="seconds"),
        "control_moved": control_moved, "control_total": control_total,
        "skipped": {i: w for i, w in skipped},
        "items": by_item,
    }
    p = evidence_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(_json.dumps(doc, indent=1, sort_keys=True))
    return doc


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", nargs="*", default=None)
    ap.add_argument("--side", default="olx")
    ap.add_argument("--show", type=int, default=12)
    ap.add_argument("--record", action="store_true",
                    help="Write the evidence `append_runs` consults.")
    a = ap.parse_args()

    # THE CONTROL FIRST, and the run is refused if it fails. A comparison that
    # cannot report a difference is not evidence of agreement.
    ctl, _ = rescore(a.items, a.side, control=0.5)
    moved = sum(1 for r in ctl if not r["same"])
    print(f"  control (+0.5 on every recorded value): {moved}/{len(ctl)} moved")
    if not ctl or moved != len(ctl):
        print("  REFUSING to report: the control did not move every cell, so a "
              "'match' here would not mean the scores agree")
        return 2

    rows, skipped = rescore(a.items, a.side)
    same = [r for r in rows if r["same"]]
    diff = [r for r in rows if not r["same"]]
    if a.record:
        doc = record_evidence(rows, skipped, moved, len(ctl))
        print(f"  evidence written to {evidence_path()} "
              f"({len(doc['items'])} item(s))")
    print(f"  re-scored {len(rows)} recorded cell(s) through the shipped scorer")
    print(f"  reproduce exactly: {len(same)}   differ: {len(diff)}")
    for s, why in skipped:
        print(f"    skipped {s}: {why}")
    by_item = {}
    for r in diff:
        by_item.setdefault(r["item"], []).append(r)
    for item in sorted(by_item):
        rs = by_item[item]
        print(f"    {item}: {len(rs)} cell(s) differ, e.g. "
              f"{rs[0]['id']} recorded {rs[0]['recorded']} -> "
              f"{rs[0]['rescored']}{'  (' + rs[0]['why'] + ')' if rs[0].get('why') else ''}")
    return 0 if not diff else 1


if __name__ == "__main__":
    sys.path.insert(0, ".")
    sys.path.insert(0, "tools")
    raise SystemExit(main())
