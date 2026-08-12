"""Read the graders' scores and feedback out of the Scoring & Feedback workbooks.

Stdlib only. Parsed cell-by-cell from sheet1.xml rather than line-oriented text,
because several feedback cells contain embedded newlines and a text-based parse
silently splits those rows (which produced a spurious "12 missing scores" count
on a first pass — the real number is one).
"""

from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET
import paths

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
COLS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

H1_XLSX = (
    f"{paths.SUBS}/"
    "Handout 1 Submissions with Scoring and Feedback/Handout 1 - Scoring & Feedback.xlsx"
)

# Gold column header -> rubric item id
H1_HEADER_TO_ITEM = {
    "Question 1": "Q1",
    "Question 2": "Q2",
    "Question 3": "Q3",
    "Question 4a": "Q4a",
    "Question 4b": "Q4b",
    "Question 4c": "Q4c",
    "Question 5": "Q5",
    "Question 6": "Q6",
}


H2_XLSX = (
    f"{paths.SUBS}/"
    "Handout 2 Submissions with Scoring and Feedback/Handout 2 - Scoring & Feedback.xlsx"
)

H2_HEADER_TO_ITEM = {
    "PR Example": "PR",
    "NR Example": "NR",
    "PP Example": "PP",
    "NP Example": "NP",
    "First Type": "T1",
    "First Type Definition": "D1",
    "First Daily Example": "DAY1",
    "First Weekly Example": "WK1",
    "Second Type": "T2",
    "Second Type Definition": "D2",
    "Second Daily Example": "DAY2",
    "Second Weekly Example": "WK2",
}


H3_XLSX = (
    f"{paths.SUBS}/"
    "Handout 3 Submissions with Scoring and Feedback/Handout 3 - Scoring & Feedback_.xlsx"
)

# Item ids are the handout's own printed numbering, deliberately WITHOUT a "Q"
# prefix: Handout 1 already uses Q1-Q6, and a shared "Q3" between the two
# handouts is genuinely confusing to read in a report.
H3_HEADER_TO_ITEM = {
    "1a": "1a", "1b": "1b", "1c": "1c",
    "2a": "2a", "2b": "2b", "3": "3",
}


def _grid(path: str) -> dict[tuple[int, str], str]:
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
    return load(path, H1_HEADER_TO_ITEM)


def load_h3(path: str = H3_XLSX) -> dict[int, dict[str, dict]]:
    return load(path, H3_HEADER_TO_ITEM)


def load_h2(path: str = H2_XLSX) -> dict[int, dict[str, dict]]:
    return load(path, H2_HEADER_TO_ITEM)


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
