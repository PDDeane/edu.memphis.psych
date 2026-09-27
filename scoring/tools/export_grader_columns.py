"""Export the graders' workbook COLUMN HEADINGS as a record.

WHY A RECORD AND NOT A READ. The workbooks are source documents: they hold
student work, and the participant ids beside it are the key that makes it
identifiable. The engine must never open one. But the column HEADINGS are not
student work -- they are the join between the graders' sheet and the rubric,
and `check_gold_columns_are_the_item_labels` needs exactly them and nothing
else. So python reads the source document and exports the headings; the engine
reads the record. The same shape as `export_grader_marks.py`.

HEADERS ONLY, AND THE ROW IS NOT SAMPLED. The exporter takes the first row of
each sheet and no other, so a data row cannot reach the record even by mistake.

FILED WITH THE INSTRUMENT. A workbook is the graders' marking of one HANDOUT;
a second rubric written for the same handout joins to the same sheet and reads
the same headings. Under `rubrics/<id>/` it would have to be duplicated.

AN UNREADABLE WORKBOOK IS RECORDED AS UNREADABLE, never as an empty heading
list. The check it feeds says so in its own words -- *a check that cannot run
is not the same as one that passes* -- and an empty list would read as a sheet
with no columns, which is a finding about the workbook rather than about this
machine.

    python3 tools/export_grader_columns.py [--print]
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import paths  # noqa: E402

FILENAME = "grader_columns.json"


def columns() -> dict:
    """`{handout: {"headings": [...]}}`, or `{"unreadable": "why"}` per handout."""
    import gold

    books = {1: gold.H1_XLSX, 2: gold.H2_XLSX, 3: gold.H3_XLSX}
    out: dict[str, dict] = {}
    for form, path in sorted(books.items()):
        try:
            grid = gold._grid(path)
        except Exception as exc:
            out[str(form)] = {"unreadable": f"{exc}"}
            continue
        header_row = min((r for r, _ in grid), default=None)
        if header_row is None:
            out[str(form)] = {"headings": []}
            continue
        # SORTED, so the record is stable across runs. A dict iteration order
        # that varies makes every export a diff and hides the one that matters.
        out[str(form)] = {"headings": sorted(
            {str(v).strip() for (r, _), v in grid.items()
             if r == header_row and str(v).strip()})}
    return out


def out_path() -> str:
    return str(paths.roots().instrument_dir / "derived" / FILENAME)


def main(argv: list[str]) -> int:
    doc = {"schema_version": 1, "handouts": columns()}
    if "--print" in argv:
        print(json.dumps(doc, indent=1, sort_keys=True))
        return 0
    target = out_path()
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "w") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True)
        fh.write("\n")
    n = sum(len(v.get("headings") or []) for v in doc["handouts"].values())
    bad = [h for h, v in doc["handouts"].items() if "unreadable" in v]
    print(f"  wrote {target}: {len(doc['handouts'])} handout(s), {n} heading(s)"
          + (f"; UNREADABLE: {', '.join(bad)}" if bad else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
