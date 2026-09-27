"""Read the graders' scores and feedback out of the Scoring & Feedback workbooks.

Stdlib only. Parsed cell-by-cell from sheet1.xml rather than line-oriented text,
because several feedback cells contain embedded newlines and a text-based parse
silently splits those rows (which produced a spurious "12 missing scores" count
on a first pass — the real number is one).
"""

from __future__ import annotations

import re
import functools
import zipfile
import xml.etree.ElementTree as ET
import paths

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
COLS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

H1_XLSX = (
    f"{paths.roots().submissions}/"
    "Handout 1 Submissions with Scoring and Feedback/Handout 1 - Scoring & Feedback.xlsx"
)



H2_XLSX = (
    f"{paths.roots().submissions}/"
    "Handout 2 Submissions with Scoring and Feedback/Handout 2 - Scoring & Feedback.xlsx"
)



H3_XLSX = (
    f"{paths.roots().submissions}/"
    "Handout 3 Submissions with Scoring and Feedback/Handout 3 - Scoring & Feedback_.xlsx"
)

# Item ids are the handout's own printed numbering, deliberately WITHOUT a "Q"
# prefix: Handout 1 already uses Q1-Q6, and a shared "Q3" between the two
# handouts is genuinely confusing to read in a report.


@functools.lru_cache(maxsize=None)
def header_to_item(form: int) -> dict[str, str]:
    """This handout's gold column headings, mapped to rubric item ids.

    DERIVED, NOT STORED, since E58 step 3 (2026-09-25). The rubric's `label`
    field IS the teacher's column heading -- that is how gold reaches an item at
    all -- so a stored table restated the same correspondence a second time and
    nothing made the two agree. A label edited for wording would have left the
    gold join working off the old heading, scores still loading, against the
    item they used to describe.

    `check_gold_columns_are_the_item_labels` was written to hold the copy to the
    original and said outright what should happen instead: *"Under A2a the
    header map is DERIVABLE and should not be a stored table at all; until it is
    removed, this check holds the copy to the original."* It is removed, and
    that check now asks the question the copy was hiding: do these headings
    exist in the graders' workbook?

    VERIFIED BEFORE THE LITERALS WENT, all three handouts, both directions:
    8, 12 and 6 entries, identical.
    """
    import coursedata

    return {it["label"]: it["id"] for it in coursedata.items()
            if it.get("handout") == form and it.get("label")}


@functools.lru_cache(maxsize=None)
def _grid(path: str) -> dict[tuple[int, str], str]:
    """The workbook as {(row, column): text}, parsed ONCE per file.

    Memoised because the callers ask per CELL while this reads a whole workbook:
    check_fixture_agrees_with_gold walks 157 multi-box fixture cells and calls
    handouts.load for each, so this ran 157 times -- four million regex
    substitutions and eight million XML element lookups -- for twenty of the
    audit's twenty-nine seconds. Three handouts, three parses.

    Keyed on the PATH alone, which is the whole input: a workbook edited during a
    run would not be re-read, and that is correct here because every caller is a
    read-only audit. The self-test's own source fingerprint is what notices a tree
    that moved underneath it.

    Returning the cached dict rather than a copy is deliberate. `load` builds a
    fresh result from it and no caller mutates the grid; making a copy per call
    would give back most of what the cache saves.
    """

    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            sr = ET.fromstring(z.read("xl/sharedStrings.xml"))
            shared = ["".join(t.text or "" for t in si.iter(NS + "t")) for si in sr]
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    g: dict[tuple[int, str], str] = {}
    for row in sheet.iter(NS + "row"):
        rn = int(row.get("r"))
        for c in row.findall(NS + "c"):
            col = re.sub(r"\d", "", c.get("r", ""))
            t, v, isel = c.get("t"), c.find(NS + "v"), c.find(NS + "is")
            if t == "s" and v is not None:
                val = shared[int(v.text)]
            elif isel is not None:
                val = "".join(x.text or "" for x in isel.iter(NS + "t"))
            elif v is not None:
                val = v.text or ""
            else:
                val = ""
            g[(rn, col)] = val
    return g


def load(path: str, header_map: dict[str, str]) -> dict[int, dict[str, dict]]:
    """{participant_id: {item_id: {"score": float|None, "feedback": str}}}"""
    g = _grid(path)
    headers = {col: g.get((1, col), "").strip() for col in COLS}

    # Score column -> item id; the feedback column is the next letter over.
    score_cols: dict[str, str] = {}
    for col, head in headers.items():
        if not head.endswith("Score"):
            continue
        stem = head[: -len("Score")].strip()
        item = header_map.get(stem)
        if item:
            score_cols[col] = item

    out: dict[int, dict[str, dict]] = {}
    rows = sorted({r for (r, c) in g if r > 1 and g.get((r, "A"), "").strip()})
    for r in rows:
        try:
            pid = int(float(g[(r, "A")]))
        except ValueError:
            continue
        rec = {}
        for col, item in score_cols.items():
            raw = str(g.get((r, col), "")).strip()
            fb_col = COLS[COLS.index(col) + 1]
            rec[item] = {
                "score": float(raw) if raw else None,
                "feedback": str(g.get((r, fb_col), "")).strip(),
            }
        out[pid] = rec
    return out


def load_h1(path: str = H1_XLSX) -> dict[int, dict[str, dict]]:
    return load(path, header_to_item(1))


def load_h3(path: str = H3_XLSX) -> dict[int, dict[str, dict]]:
    return load(path, header_to_item(3))


def load_h2(path: str = H2_XLSX) -> dict[int, dict[str, dict]]:
    return load(path, header_to_item(2))


if __name__ == "__main__":
    gold = load_h1()
    missing = [
        (pid, item)
        for pid, items in gold.items()
        for item, v in items.items()
        if v["score"] is None
    ]
    print(f"participants: {len(gold)}")
    print(f"missing score cells: {len(missing)} -> {missing}")
    for pid in sorted(gold)[:3]:
        tot = sum(v["score"] for v in gold[pid].values() if v["score"] is not None)
        print(f"  {pid}: total {tot:g}")
