#!/usr/bin/env python3
"""The graders' MARKS, as a record the engine can read.

NOT NAMED FOR THE ARTIFACT IT EXPORTS. `check_no_module_is_named_for_a_course_
artifact` is a RATCHET: the modules already named for a question, a handout or
a course are baselined and the population may shrink, never grow. This began
life as `export_gold_rows.py` and was renamed rather than added to that budget
-- "renaming is the only fix", and adding a tenth would have undone a reduction
somebody had to make. The RECORD it writes keeps the name `gold_rows.json`,
beside `gold.json`: records under `$COURSE_DATA` ARE course data, and naming
them for the course is what they are for.

WHY THIS EXISTS. `gold_export.py` writes the DECLARATIONS ABOUT gold -- which
cells are corrected, which diverge, which ceilings are unreachable -- and says
outright what it is not: "Not the graders' scores -- those live in the three
`Scoring & Feedback` workbooks and are read by `gold.py`." So the marks
themselves had no record, and every reader of them had to open a workbook.

THAT MADE THE MARKS UNREADABLE TO THE ENGINE, and it should not have. Gold for
a course's own items is course DATA; the workbooks are merely where it was
first written down. Twelve enforcement checks were python-only for no better
reason than the channel -- reading `.xlsx` is not something a content engine
should learn, but reading a record is exactly what it already does for
`course.json` and `gold.json`.

SO PYTHON STAYS THE ONLY READER OF THE WORKBOOKS, and exports what it read.
One direction, one reader, and the engine sees a record like every other.

WHERE IT GOES, and the reasoning is `gold_export`'s own: every row names a
PARTICIPANT, and a participant-keyed table does not ship in a public
repository. `$COURSE_DATA/courses/<course-id>/gold_rows.json`, beside the
submissions it describes. `--out` overrides, which is how this is tested
without writing to the data store.

WHAT IS IN A ROW: the `score` and the `feedback` as
`forms.config(h)["gold"]()` returns them -- which means CORRECTIONS ARE ALREADY
APPLIED. `handouts._gold_loader` folds `CORRECTED_GOLD` in as it reads, so
`1a/p11` comes out 6.0 where the workbook says 8.0.

THAT IS DELIBERATE, AND IT IS THE VIEW EVERY READER WANTS: the checks that
consume gold all read the corrected view, because a correction is this
project's considered judgement about a marking error and reading round it would
re-litigate each one. The raw marks remain in the workbooks, and every
correction is declared, with its reason, in `gold.json`'s `CORRECTED_GOLD` --
so the uncorrected value is never lost, only never the default.

An earlier draft of this docstring claimed the opposite. It was wrong: the
export calls the same loader the checks do, and a record that misdescribes what
it holds is worse than no record.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SCHEMA_VERSION = 1


def rows() -> dict:
    """{handout: {participant: {item: {score, score_raw, feedback}}}}.

    BOTH VIEWS, because the two answer different questions and a record that
    carried one could not be asked the other. `score` is what
    `forms.config(h)["gold"]()` returns -- CORRECTIONS APPLIED, which is what
    every consumer of gold wants. `score_raw` is what the workbook says, from
    the uncorrected loader, and it is what a check comparing a declared
    correction against the sheet needs: `CORRECTED_GOLD` records the value it
    corrected FROM, and comparing that to the corrected value would report a
    mismatch on every entry.

    They are equal on all but the corrected cells. Carried explicitly rather
    than only where they differ, so no reader has to know to fall back.
    """
    import enforcement
    import forms
    import gold

    loaders = {1: gold.load_h1, 2: gold.load_h2, 3: gold.load_h3}
    out: dict = {}
    for h in enforcement._forms():
        cfg = forms.config(h)
        try:
            grid = cfg["gold"]()
        except Exception as exc:                       # pragma: no cover
            raise SystemExit(
                f"export_grader_marks: handout {h}'s workbook could not be read "
                f"({type(exc).__name__}: {exc}). An export that silently omitted "
                f"a handout would read as a course with no gold for it.")
        try:
            uncorrected = loaders[h]() if h in loaders else {}
        except Exception:                              # pragma: no cover
            uncorrected = {}
        per: dict = {}
        for pid in sorted(grid):
            cells = {}
            for item_id, cell in sorted(grid[pid].items()):
                if not isinstance(cell, dict):
                    continue
                bare = (uncorrected.get(pid) or {}).get(item_id) or {}
                cells[str(item_id)] = {
                    "score": cell.get("score"),
                    "score_raw": bare.get("score", cell.get("score")),
                    "feedback": cell.get("feedback"),
                }
            if cells:
                per[str(pid)] = cells
        out[str(h)] = per
    return out


def document() -> dict:
    body = rows()
    return {
        "schema_version": SCHEMA_VERSION,
        "note": ("The graders' marks, exported from the Scoring & Feedback "
                 "workbooks so readers other than python can see them. "
                 "CORRECTED_GOLD is already applied, as forms.config(h)['gold']() "
                 "applies it; the uncorrected marks stay in the workbooks and "
                 "every correction is declared in gold.json."),
        "handouts": body,
        "counts": {h: {"participants": len(p),
                       "cells": sum(len(c) for c in p.values())}
                   for h, p in body.items()},
    }


def default_path() -> str:
    """`$COURSE_DATA/courses/<course-id>/gold_rows.json`.

    THE SAME ROOT `gold_export.default_path` USES, and deliberately not
    `paths.roots().data`. On a course declaring `shared_data_layout` that root
    is the SHARED `$COURSE_DATA` itself, so writing there puts a
    participant-keyed file beside every course's data instead of inside this
    one's -- which is both wrong and, on this machine, outside the write scope
    for this work. Asking `coursedata` for the course directory keeps the two
    gold records in one place.
    """
    import coursedata
    import paths

    if not coursedata.data_root():
        raise SystemExit(
            "export_grader_marks: no $COURSE_DATA, so there is nowhere outside the "
            "repository to put a participant-keyed record")
    return str(paths.roots().rubric_dir / "derived" / "gold_rows.json")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--check", action="store_true",
                    help="compare the record against the workbooks, write nothing")
    args = ap.parse_args(argv)
    doc = document()
    path = args.out or default_path()
    if args.check:
        if not os.path.exists(path):
            print(f"  MISSING: {path} has never been written")
            return 1
        have = json.load(open(path, encoding="utf8"))
        if have.get("handouts") != doc["handouts"]:
            print(f"  STALE: {path} disagrees with the workbooks")
            return 1
        print(f"  current: {path}")
        return 0
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf8") as fh:
        json.dump(doc, fh, indent=1, sort_keys=False)
        fh.write("\n")
    for h, c in doc["counts"].items():
        print(f"  handout {h}: {c['participants']} participants, {c['cells']} cells")
    print(f"  written: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
