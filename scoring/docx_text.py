"""Stdlib-only OOXML text extraction (no python-docx dependency).

Reads .docx paragraph/table text, plus the machine-checkable parts of embedded
charts (title / axis titles / legend) that Handout 3 item 1c is scored on.
"""

from __future__ import annotations

import re
import zipfile
import xml.etree.ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
C = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"


def _para_text(p: ET.Element) -> str:
    out = []
    for node in p.iter():
        if node.tag == W + "t":
            out.append(node.text or "")
        elif node.tag == W + "tab":
            out.append("\t")
        elif node.tag in (W + "br", W + "cr"):
            out.append("\n")
    return "".join(out)


def _walk(el: ET.Element) -> list[str]:
    lines: list[str] = []
    for child in el:
        if child.tag == W + "p":
            lines.extend(_para_text(child).split("\n"))
        elif child.tag == W + "tbl":
            for tr in child.findall(f"{W}tr"):
                cells = [
                    " ".join(x.strip() for x in _walk(tc) if x.strip())
                    for tc in tr.findall(f"{W}tc")
                ]
                joined = " | ".join(c for c in cells if c)
                if joined:
                    lines.append(joined)
    return lines


def doc_lines(path: str) -> list[str]:
    """Paragraph-level lines of a .docx, in document order."""
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    body = root.find(W + "body")
    if body is None:
        return []
    return [ln.strip() for ln in _walk(body)]


def marked_runs(path: str, predicate) -> list[str]:
    """Text of runs carrying underline/bold/highlight formatting.

    Handout 1 asks students to underline their chosen unwanted target
    behavior. Only 6 of 20 transcriptions preserve that markup, so this is a
    weak hint, never the primary signal — the UTB is read from prose.
    """
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    hits = []
    for r in root.iter(W + "r"):
        rpr = r.find(W + "rPr")
        if rpr is None:
            continue
        fmt = {
            "u": rpr.find(W + "u") is not None,
            "b": rpr.find(W + "b") is not None,
            "highlight": rpr.find(W + "highlight") is not None,
        }
        if predicate(fmt):
            txt = "".join(t.text or "" for t in r.iter(W + "t")).strip()
            if txt:
                hits.append(txt)
    return hits


TEMPLATE_CHART_MARKERS = ("water consumption", "ounces of water")


def _is_template_chart(texts: list[str]) -> bool:
    """The blank Handout 3 ships one worked example chart; several students
    left it in place and added nothing of their own."""
    joined = " ".join(t or "" for t in texts).lower()
    return any(m in joined for m in TEMPLATE_CHART_MARKERS)


def extract_media(path: str, outdir: str) -> list[str]:
    """Write embedded images to disk so a vision-capable pass can read them."""
    import os

    os.makedirs(outdir, exist_ok=True)
    out = []
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if not n.startswith("word/media/"):
                continue
            dest = os.path.join(outdir, os.path.basename(n))
            with open(dest, "wb") as fh:
                fh.write(z.read(n))
            out.append(dest)
    return sorted(out)


def chart_labels(path: str) -> list[dict]:
    """The labels of each embedded chart, separated rather than flattened.

    `graph_evidence` hands the model a flat list of every text run in the chart
    XML and lets it work out which is the title; this reads the three labelling
    elements out of their own tags:

        c:chart/c:title            the chart title
        c:plotArea/c:catAx/c:title the x-axis title
        c:plotArea/c:valAx/c:title the y-axis title

    An absent tag means the student never typed that label, which is exactly the
    thing item 1c scores. Returned per chart, with `origin` marking the blank
    handout's own worked example so it is not mistaken for the student's.

    Added for the lo-blocks comparison: that version asks students to TYPE these
    three labels and draws the chart for them, so a paper submission's chart
    labels are what the same student would have typed.
    """
    out: list[dict] = []
    with zipfile.ZipFile(path) as z:
        for name in sorted(n for n in z.namelist()
                           if re.match(r"word/charts/chart\d+\.xml$", n)):
            root = ET.fromstring(z.read(name))

            def label(el) -> str:
                if el is None:
                    return ""
                return "".join(t.text or "" for t in el.iter(A + "t")).strip()

            title = label(root.find(f".//{C}chart/{C}title"))
            rec = {
                "source": name,
                "title": title,
                "x_axis_label": label(root.find(f".//{C}catAx/{C}title")),
                "y_axis_label": label(root.find(f".//{C}valAx/{C}title")),
                "has_legend": root.find(f".//{C}legend") is not None,
                "origin": "template" if _is_template_chart([title]) else "student",
            }
            out.append(rec)
    return out


def graph_evidence(path: str) -> dict:
    """What is machine-checkable about a graph in this .docx.

    Returns kind: "ooxml_chart" (title/axis/legend readable from XML),
    "image" (needs vision), or "none". Handout 3's blank template carries an
    EXAMPLE chart, so a positive hit here is not proof the student supplied
    one — cross-check the title against the template's example.
    """
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        charts = sorted(n for n in names if re.match(r"word/charts/chart\d+\.xml$", n))
        media = sorted(n for n in names if n.startswith("word/media/"))
        if charts:
            out = []
            for cn in charts:
                root = ET.fromstring(z.read(cn))
                texts = [t.text for t in root.iter(A + "t") if t.text]
                out.append(
                    {
                        "source": cn,
                        "texts": texts,
                        "has_legend": root.find(f".//{C}legend") is not None,
                        "n_axes": len(root.findall(f".//{C}valAx"))
                        + len(root.findall(f".//{C}catAx")),
                    }
                )
            for c in out:
                c["origin"] = "template" if _is_template_chart(c["texts"]) else "student"
            return {"kind": "ooxml_chart", "charts": out, "media": media}
        if media:
            return {"kind": "image", "charts": [], "media": media}
    return {"kind": "none", "charts": [], "media": []}
