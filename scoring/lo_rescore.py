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
    sheets, payloads, skipped, unscoreable = {}, [], [], []
    for item in sorted(items or M._jobs()):
        job = jobs.get(item) or {}
        # SHEET-ONLY ITEMS GO THROUGH THE PREPARED READERS. `1b`, `T1` and `T2`
        # carry a `<DerivedChecks>` element rather than an `<LLMAction>`, and
        # `load_action` matches only the latter -- so all three were skipped and
        # their neutrality went unproven while the run looked complete.
        #
        # NOT A SECOND READER, and not a change to `load_action`. `_SHEET_RE`
        # already names BOTH element types, `_slots_attr` already falls back to
        # `_sheet_tag` when the action regex misses, and the slot spec is parsed
        # by `agreement.parse_slots` -- the same function `load_action` uses, so
        # the slot shape is identical. Teaching `load_action` the second element
        # would have been tidier and costs more than it is worth here: it sits in
        # `_ALWAYS`, so editing it moves EVERY item's `scorer_sha` and re-stales
        # twenty-six columns that were just settled.
        #
        # THE EIGHT OTHER TABLES ARE CHECKED, NOT ASSUMED. A `<DerivedChecks>`
        # carries `derived`, `id`, `max` and `slots` today. If one ever gains a
        # `forbid=` or a `maps=`, silently passing empty tables would re-score it
        # against rules the app applies and call the difference a scoring change.
        # It refuses instead.
        if item in O.ACTION:
            try:
                act = A.load_action(job["olx"], O.ACTION[item])
            except Exception as e:
                skipped.append((item, f"sheet unreadable: {type(e).__name__}"))
                continue
        else:
            sid = getattr(O, "SHEET_ONLY", {}).get(item)
            if not sid:
                skipped.append((item, f"{job.get('kind')!r}: no slot sheet id"))
                continue
            try:
                tag = O._sheet_tag(O.HANDOUT[item], sid)
                carried = [a for a in ("cover", "equals", "onlyif", "counts",
                                       "expect", "requires", "forbid", "maps")
                           if f'{a}="' in tag]
                if carried:
                    skipped.append((item, f"its sheet element carries "
                                          f"{carried}, which this path does not "
                                          f"assemble -- read it through "
                                          f"load_action instead"))
                    continue
                spec, defaults = O._slots_attr(O.HANDOUT[item], sid)
                act = {"slots": A.parse_slots(spec, defaults),
                       "cover": [], "equals": [], "onlyif": [], "counts": [],
                       "expect": [], "requires": [], "forbid": [], "maps": []}
            except Exception as e:
                skipped.append((item, f"sheet unreadable: {type(e).__name__}: "
                                      f"{str(e)[:60]}"))
                continue
        sheets[item] = {k: (act.get(k) or []) for k in
                        ("slots", "cover", "equals", "onlyif", "counts",
                         "expect", "requires", "forbid", "maps")}
        computed = {r["key"] for f in ("maps", "equals", "expect", "forbid")
                    for r in (act.get(f) or [])}
        counted = {sl["key"] for sl in act["slots"]
                   if sl.get("count_max") is not None}
        slot_keys = {sl["key"] for sl in act["slots"]}
        # THE COURSE'S OWN NAME MAP, not a guess. `SIDE_ALIAS` declares "the same
        # rule under its two names, web value second", and four of its entries
        # exist for exactly this item: 1b's folded python-era runs record
        # `baseline`/`week_1..3` where today's sheet asks `baseline_data`/
        # `week_1_data..`. Subgoal Q56 measured those four before declaring them.
        #
        # `probe._slot_aliases` is the prepared reader for this and its docstring
        # names 1b; re-deriving the pairing here would be a second reader of one
        # table. AMBIGUITY IS REFUSED, not resolved: if two slots on one sheet
        # claim the same alias, the mapping is dropped and the run falls through
        # to the not-re-scoreable arm rather than being attached to a guess.
        alias_of: dict = {}
        try:
            import probe as _P
            for sl in act["slots"]:
                for nm in _P._slot_aliases(sl["key"]):
                    if nm in slot_keys and nm != sl["key"]:
                        continue                # a real slot of its own
                    if alias_of.get(nm, sl["key"]) != sl["key"]:
                        alias_of[nm] = None     # claimed twice: refuse it
                    else:
                        alias_of.setdefault(nm, sl["key"])
        except Exception:
            alias_of = {}
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
                    if k not in slot_keys and alias_of.get(k):
                        k = alias_of[k]         # the same rule, its other name
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
                # A RUN RECORDED UNDER A DIFFERENT SLOT VOCABULARY CANNOT BE
                # RE-SCORED, AND IS NOT A SCORING DIFFERENCE.
                #
                # 1b's folded python-era runs (goal O pooled them into `olx`)
                # name their slots `baseline`, `week_1`, `week_2`, `week_3`;
                # today's sheet asks `baseline_data`, `week_1_data` and so on.
                # `scoreSlotSheet` finds nothing it recognises, satisfies no
                # slot and returns 0 -- so 114 cells recorded at full marks read
                # as "the scoring changed", when what actually differs is the
                # vocabulary the eliminated engine wrote.
                #
                # THE TEST IS NO OVERLAP AT ALL, deliberately. A run MISSING some
                # keys is a real defect and must still be re-scored and reported;
                # only a run sharing NONE of the sheet's keys is describing a
                # different sheet. Excluded loudly rather than counted either way,
                # because both a false `differ` and a silent pass would be wrong.
                if checks and not (set(checks) & slot_keys):
                    unscoreable.append((item, f"{ri}|{ci}"))
                    continue
                payloads.append({"id": f"{item}|{ri}|{ci}|{c[1]}", "item": item,
                                 "checks": checks, "max": float(smax),
                                 "recorded": round(float(c[2]), 4)})
    return sheets, payloads, skipped, unscoreable


def rescore(items=None, side="olx", control=0.0):
    """Rows from the shipped scorer, one per recorded cell."""
    import lo_enforce

    sheets, payloads, skipped, unscoreable = _sheets_and_payloads(items, side)
    if control:
        payloads = [dict(p, recorded=round(p["recorded"] + control, 4))
                    for p in payloads]
    rows = lo_enforce.probe("score_recorded_sheets",
                            {"sheets": sheets, "payloads": payloads})
    return rows, skipped, unscoreable


def _paper_rows(items=None, control=0.0):
    """Re-score recorded PAPER cells through score.py's own `score_item`.

    THE SAME QUESTION AS THE WEB RESCORE, on the side score.py scores. Eight
    columns -- DAY1, DAY2, NP, NR, PP, PR, WK1, WK2, all of them `oc` items --
    read STALE SCORER because `oc.derive_ledger` moved. Whether that move
    touched a number is arithmetic over answers that were already recorded.

    NOTHING IS REIMPLEMENTED HERE. `score_item` owns the whole path -- the
    scorer registry dispatch, the over-specified cap that trims a ledger to the
    number of credit components, and `max(0, min(max, max - total_off))`. Copying
    those five lines would be a second implementation of the paper arithmetic,
    which is the mirror goal O spent itself removing. So the RECORDED answer is
    fed back in through a stub backend and `score_item` runs unchanged.
    """
    import enforcement as E
    import measured as M
    import score as SC

    class _Recorded:
        """A backend that returns what the model already said."""
        SUPPORTS_TOOLS = False

        def __init__(self, raw):
            self._raw = raw

        def complete(self, *a, **k):
            return self._raw

    by_id = {it["id"]: it for it in E.all_items()}
    rows, skipped = [], []
    for item in sorted(items or M._jobs()):
        spec = by_id.get(item)
        if spec is None:
            skipped.append((item, "no rubric item")); continue
        doc = M._runs_doc(item, "paper")
        for ri, run in enumerate((doc or {}).get("runs") or []):
            for ci, r in enumerate(run.get("results") or []):
                if r.get("score") is None:
                    continue
                raw = {k: r.get(k) for k in
                       ("oc_analysis", "credit_checks", "deductions",
                        "advisory_note", "safety_flag", "slots")
                       if r.get(k) is not None}
                if not raw:
                    skipped.append((item, f"run {ri} cell {ci}: nothing recorded "
                                          f"to re-score from"))
                    continue
                want = round(float(r["score"]) + control, 2)
                try:
                    got = SC.score_item(_Recorded(raw), "", spec, "", {}, None)
                except Exception as e:
                    rows.append({"id": f"{item}|{ri}|{ci}", "item": item,
                                 "recorded": want, "rescored": None,
                                 "same": False, "why": f"{type(e).__name__}: {e}"})
                    continue
                s = got.get("score")
                ok = (s is not None and isinstance(s, (int, float))
                      and abs(float(s) - want) < 1e-9)
                rows.append({"id": f"{item}|{ri}|{ci}", "item": item,
                             "recorded": want, "rescored": s, "same": ok})
    return rows, skipped


def _paper_answer_control(items=None, limit=5):
    """Does the scorer actually READ the recorded answer? `(moved, total)`.

    THE +0.5 CONTROL IS NOT ENOUGH HERE, and the difference matters. Adding half
    a point to the recorded value proves the COMPARISON can fail; it says
    nothing about whether `derive_ledger` ever looked at the recorded fields. On
    the OC items that gap is live: a `derive_ledger` handed an analysis it did
    not recognise fails its definitional gates, charges NOT_OC and returns 0.0 --
    and DAY1's recorded score IS 0.0 on many cells, so an unread answer would
    reproduce it exactly and the run would report perfect agreement.

    So this perturbs the ANSWER instead: every boolean in `oc_analysis` is
    flipped and the score must move. It was worth writing -- the user's remark
    that the OC items went to rubric naming is exactly the shape of fault that
    would have slipped through, and checking the schema's fields against the
    recorded ones (15 of 15, no drift) is how it was cleared.
    """
    import enforcement as E
    import measured as M
    import score as SC

    class _Recorded:
        SUPPORTS_TOOLS = False

        def __init__(self, raw):
            self._raw = raw

        def complete(self, *a, **k):
            return self._raw

    by_id = {it["id"]: it for it in E.all_items()}
    moved = total = 0
    for item in sorted(items or M._jobs()):
        spec = by_id.get(item)
        doc = M._runs_doc(item, "paper")
        if spec is None or not doc:
            continue
        for run in (doc.get("runs") or [])[:1]:
            for r in (run.get("results") or [])[:limit]:
                a = r.get("oc_analysis") or {}
                if not a:
                    continue
                flip = {k: (not v if isinstance(v, bool) else v)
                        for k, v in a.items()}
                try:
                    base = SC.score_item(_Recorded({"oc_analysis": dict(a)}),
                                         "", spec, "", {}, None)["score"]
                    got = SC.score_item(_Recorded({"oc_analysis": flip}),
                                        "", spec, "", {}, None)["score"]
                except Exception:
                    continue
                total += 1
                moved += abs(float(base) - float(got)) > 1e-9
    return moved, total


def evidence_path():
    """Where a rescore's result is kept. Measurement evidence, so it lives in
    `$COURSE_DATA/out` beside the sweeps -- not in the repo, and not in
    `$COURSE_METADATA`, which holds what the course DECLARES rather than what a
    run measured."""
    import paths
    return Path(paths.OUT) / "rescore_evidence.json"


def record_evidence(rows, skipped, control_moved, control_total,
                    side: str = "olx") -> dict:
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
        rec = (M.entry(item, side) or {})
        e["from"] = rec.get("scorer_sha")
        e["to"] = M.scorer_sha(item, side)
        e["ask_recorded"] = rec.get("ask_sha")
        e["ask_now"] = M.ask_sha(item, side)
    # PER SIDE, because the sides are scored by different code and a neutrality
    # claim is about ONE scorer. Writing both into one `items` map would let
    # evidence measured on the web excuse a stale paper column.
    p = evidence_path()
    try:
        doc = _json.loads(p.read_text())
    except Exception:
        doc = {}
    doc.setdefault("sides", {})
    doc["sides"][side] = {
        "measured_at": __import__("datetime").datetime.now()
                       .astimezone().isoformat(timespec="seconds"),
        "control_moved": control_moved, "control_total": control_total,
        "skipped": {i: w for i, w in skipped},
        "items": by_item,
    }
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(_json.dumps(doc, indent=1, sort_keys=True))
    return doc["sides"][side]


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
    ctl, _, _ = rescore(a.items, a.side, control=0.5)
    moved = sum(1 for r in ctl if not r["same"])
    print(f"  control (+0.5 on every recorded value): {moved}/{len(ctl)} moved")
    if not ctl or moved != len(ctl):
        print("  REFUSING to report: the control did not move every cell, so a "
              "'match' here would not mean the scores agree")
        return 2

    rows, skipped, unscoreable = rescore(a.items, a.side)
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
    if unscoreable:
        from collections import Counter as _C
        for it, n in sorted(_C(i for i, _ in unscoreable).items()):
            print(f"    {it}: {n} run-cell(s) recorded under a slot vocabulary "
                  f"this sheet does not have -- NOT re-scoreable, and not a "
                  f"scoring difference")
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
