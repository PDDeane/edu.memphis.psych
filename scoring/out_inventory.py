#!/usr/bin/env python3
"""What is in `$COURSE_DATA/out`, and which decision records name it.

READ-ONLY, AND IT DECIDES NOTHING. `cited_by` lists the ledger entries that name a
directory through the ledger's OWN reference field -- `MEASURED.json`'s
`items[item][side].out`, the only such field any ledger carries today. An empty
`cited_by` means NO LEDGER NAMES IT. That is not the same as unused: other readers
build run paths at call time, and `measured`, `compare_runs`, `probe`,
`sweep_readout` and the paper tooling all reach into `out/`. An uncited entry is a
CANDIDATE FOR REVIEW, never junk.

WHY IT EXISTS. 826 entries and 1.66 GB had accumulated with no list of what they
were, and the link between a decision and the run that supported it was never
recorded -- `goals.py` cites the finding, never the artifact, so 32 of 826 runs are
named anywhere at all. Archiving them is cheap (measured 17-23x compression) and
adjudicating them is not, so the inventory exists to make the archive navigable
rather than to justify deletions. RUBRIC_MIGRATION_PLAN section 13 H carries the
reasoning; G2 owns the fix, which is to record the link on the decision record.

A COUNT TAKEN BY SUBSTRING SEARCH IS WRONG HERE, and was: scanning four ledgers for
each directory name reported 26 cited where the reference field reports 17, because
names matched inside unrelated text. Ask the structure, not the text.
"""
from __future__ import annotations

import collections
import datetime
import json
import os
import pathlib
import sys

import paths


def cited_dirs() -> dict:
    """Directories named by a ledger, through the ledger's own reference field."""
    out: dict = collections.defaultdict(set)
    # FROM `paths`, not from this file's position -- see `editguard.HERE`.
    ledger = paths.SCORING / "MEASURED.json"
    doc = json.loads(ledger.read_text())
    for item, sides in (doc.get("items") or {}).items():
        for side, v in (sides or {}).items():
            named = (v or {}).get("out")
            if named:
                out[str(named).split("/")[0]].add(f"MEASURED.json:{item}/{side}")
    return out


def _bytes_and_files(p: pathlib.Path) -> tuple[int, int]:
    if not p.is_dir():
        return p.stat().st_size, 1
    total = files = 0
    for root, _dirs, names in os.walk(p):
        for n in names:
            files += 1
            try:
                total += os.path.getsize(os.path.join(root, n))
            except OSError:
                pass
    return total, files


def inventory() -> dict:
    cites = cited_dirs()
    rows = []
    for p in sorted(pathlib.Path(paths.OUT).iterdir()):
        if p.name.startswith("."):
            continue
        size, files = _bytes_and_files(p)
        rows.append({
            "name": p.name,
            "kind": "dir" if p.is_dir() else "file",
            "bytes": size,
            "files": files,
            "mtime": datetime.datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d"),
            "cited_by": sorted(cites.get(p.name, ())),
        })
    return {
        "_what": __doc__.strip().split("\n\n")[1],
        "_generated_by": "scoring/out_inventory.py",
        "_totals": {"entries": len(rows),
                    "bytes": sum(r["bytes"] for r in rows),
                    "cited": sum(1 for r in rows if r["cited_by"]),
                    "uncited": sum(1 for r in rows if not r["cited_by"])},
        "entries": rows,
    }


def main(argv: list) -> int:
    doc = inventory()
    dest = argv[1] if len(argv) > 1 else str(pathlib.Path(paths.OUT) / "OUT_INVENTORY.json")
    pathlib.Path(dest).write_text(json.dumps(doc, indent=1, sort_keys=False) + "\n")
    t = doc["_totals"]
    print(f"  {t['entries']} entries, {t['bytes'] / 1e9:.2f} GB; "
          f"{t['cited']} cited by a ledger, {t['uncited']} not")
    print(f"  written: {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
