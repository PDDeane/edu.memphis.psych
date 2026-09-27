"""Freeze each item's RECONSTRUCTED response boxes as a record, with shas.

WHAT THIS IS, AND WHAT IT IS NOT. It is the same move `handsplit/Q4b.json` and
`q6_consensus/consensus.json` already made, applied to the other 24 items: the
segmented boxes the scorer actually sees, written down. It is NOT a general
accessor for student text. Nothing here exposes a submission; it exposes the
reconstruction, which is the thing every sweep and every fixture check consumes.

WHY. For 24 of 26 items the fixture was RECOMPUTED from the `.docx` on every
run. Change the segmenter and every past sweep becomes incomparable to every
future one, with nothing to say so -- no sha, no stamp, and the numbers move for
a reason nothing records. The two items already frozen were frozen because their
segmentation was argued about; the other 24 were recomputed because nobody had
looked, which per the fixture-defect record is not a statement about their
condition.

THE SHA IS THE POINT. Each cell carries the sha of its own boxes and each file
the sha of all of them, so a silent re-extraction is visible as a diff rather
than as a rate that moved.

FILED WITH THE INSTRUMENT, beside `handsplit/` and `fixture/`: the boxes follow
the HANDOUT's structure and are identical for every rubric that scores it.

    python3 tools/export_response_fixtures.py [--verify] [--item ID]

`--verify` re-segments live and compares against the record, cell by cell. That
is the extraction's correctness proof and the only thing that needs the corpus.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import paths  # noqa: E402

DIRNAME = "responses"


def sha12(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def cell_sha(boxes: dict) -> str:
    """Over the boxes, key-sorted, so the sha is about content and not order."""
    return sha12(json.dumps(boxes, sort_keys=True, ensure_ascii=False))


def frozen_items() -> set:
    """Items whose RECONSTRUCTION comes from a hand-made source, not a split.

    THEY ARE EXTRACTED TOO, and the first version of this tool skipped them on
    the grounds that re-freezing would duplicate a corpus. That was the wrong
    reading of what this record is. `responses/` is DERIVED -- from whatever
    source each item happens to have: a `.docx` for most, a hand-split row for
    one, a hand-adjudicated consensus for another. The relationship is the same
    in all three cases, and `--verify` holds every item to its own source.

    Skipping them left the record covering 24 of 26 items, so anything reading
    it had to know which two were missing and go somewhere else -- which is how
    a native assembler came to enumerate a different cell set from python's.
    The set is still returned, because the two are worth NAMING in the summary.
    """
    import agreement_app as AA

    return {i for i, spec in AA.JOBS.items()
            if spec.get("handsplit") or spec.get("consensus")}


def extract(item: str) -> dict:
    """`{pid: {ref: text}}` for one item, from the live reconstruction."""
    import agreement_app as AA
    from forms import find_submissions

    spec = AA.JOBS[item]
    pids = [p for p, _ in find_submissions(spec["handout"], None)]
    out = {}
    for pid in sorted(pids):
        try:
            jobs = AA.build_jobs(item, [pid])
        except SystemExit:
            # A cell the reconstruction refuses is NOT written as empty: an
            # empty box is a scoreable value and would be frozen as one.
            continue
        if not jobs:
            continue
        out[str(pid)] = {k: v for k, v in (jobs[0]["fixture"] or {}).items()}
    return out


def document(item: str, cells: dict) -> dict:
    return {
        "schema_version": 1,
        "item": item,
        "sha": cell_sha({p: b for p, b in cells.items()}),
        "cells": {p: {"sha": cell_sha(b), "boxes": b}
                  for p, b in sorted(cells.items(), key=lambda kv: int(kv[0]))},
    }


CELLS_FILE = "fixture_cells.json"


def cell_set() -> dict:
    """`{item: {handout, pids}}` -- exactly the cells the fixture checks walk.

    WHY THIS IS A RECORD AND NOT A DERIVATION. `_fixture_cells` keeps a cell
    when the item's own response SECTION is at least 40 characters after
    whitespace collapse -- a property of the SEGMENTATION, not of the boxes. The
    boxes are frozen; the section text is not, and should not be. So a reader
    without the corpus cannot recompute which cells are in scope, and a native
    assembler that guessed produced 169 cells against python's 157, 40 differing
    box maps and 4 findings against 0.

    IT CARRIES NO STUDENT TEXT -- item, handout and participant number only. The
    enumeration is what is missing on the other side; the words already have a
    home.
    """
    import enforcement as E

    out: dict[str, dict] = {}
    for h, item, pid, _raw, _boxes in E._fixture_cells():
        entry = out.setdefault(str(item), {"handout": h, "pids": []})
        if pid not in entry["pids"]:
            entry["pids"].append(pid)
    for entry in out.values():
        entry["pids"].sort()
    return out


def cells_path() -> str:
    return os.path.join(os.path.dirname(out_dir()), CELLS_FILE)


def load_cells() -> dict | None:
    try:
        with open(cells_path()) as fh:
            return json.load(fh)
    except (FileNotFoundError, ValueError):
        return None


def out_dir() -> str:
    return str(paths.roots().instrument_dir / "derived" / DIRNAME)


def path_for(item: str) -> str:
    return os.path.join(out_dir(), f"{item}.json")


def load(item: str) -> dict | None:
    try:
        with open(path_for(item)) as fh:
            return json.load(fh)
    except (FileNotFoundError, ValueError):
        return None


def boxes_for(item: str, pid) -> dict | None:
    """The frozen boxes for one cell, or None when nothing is recorded."""
    doc = load(item)
    if not doc:
        return None
    cell = (doc.get("cells") or {}).get(str(pid))
    return None if cell is None else cell.get("boxes")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true",
                    help="re-segment live and compare against the record")
    ap.add_argument("--item", help="one item only")
    a = ap.parse_args(argv)

    import agreement_app as AA

    skip = frozen_items()
    items = [a.item] if a.item else sorted(AA.JOBS)

    if a.verify:
        bad = 0
        for item in items:
            doc = load(item)
            if doc is None:
                print(f"  {item}: NO RECORD -- nothing to verify against")
                bad += 1
                continue
            live = extract(item)
            rec = {p: c["boxes"] for p, c in (doc.get("cells") or {}).items()}
            if live != rec:
                only_live = sorted(set(live) - set(rec))
                only_rec = sorted(set(rec) - set(live))
                moved = sorted(p for p in set(live) & set(rec) if live[p] != rec[p])
                print(f"  {item}: DIFFERS -- live-only {only_live}, "
                      f"record-only {only_rec}, changed {moved}")
                bad += 1
                continue
            for p, c in doc["cells"].items():
                if c["sha"] != cell_sha(c["boxes"]):
                    print(f"  {item}/p{p}: recorded sha does not match its boxes")
                    bad += 1
        rec = load_cells()
        if rec is None:
            print("  NO CELL-SET RECORD -- the fixture checks' scope is not "
                  "recorded, so a reader without the corpus cannot know it")
            bad += 1
        else:
            live = cell_set()
            if live != (rec.get("items") or {}):
                only_live = sorted(set(live) - set(rec.get("items") or {}))
                only_rec = sorted(set(rec.get("items") or {}) - set(live))
                moved = sorted(i for i in set(live) & set(rec["items"])
                               if live[i] != rec["items"][i])
                print(f"  cell set DIFFERS -- live-only {only_live}, "
                      f"record-only {only_rec}, changed {moved}")
                bad += 1
            elif rec.get("sha") != cell_sha(live):
                print("  cell set matches but its sha does not describe it")
                bad += 1
        print(f"  {len(items)} item(s) verified, {bad} problem(s)")
        return 1 if bad else 0

    os.makedirs(out_dir(), exist_ok=True)
    if not a.item:
        cs = cell_set()
        doc = {"schema_version": 1, "sha": cell_sha(cs), "items": cs}
        with open(cells_path(), "w") as fh:
            json.dump(doc, fh, indent=1, sort_keys=True)
            fh.write("\n")
        print(f"  wrote {cells_path()}: {len(cs)} item(s), "
              f"{sum(len(v['pids']) for v in cs.values())} cell(s)")
    cells_total = 0
    for item in items:
        cells = extract(item)
        cells_total += len(cells)
        with open(path_for(item), "w") as fh:
            json.dump(document(item, cells), fh, indent=1,
                      sort_keys=True, ensure_ascii=False)
            fh.write("\n")
    print(f"  wrote {len(items)} item file(s), {cells_total} cell(s) -> {out_dir()}")
    print(f"  ({len(skip)} of them reconstruct from a hand-made source: "
          f"{sorted(skip)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
