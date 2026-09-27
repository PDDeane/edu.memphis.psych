"""Reconstruct a lo-blocks Handout 3 session from a paper submission.

Why this exists. The web version of Handout 3 does not ask for a graph — it
DRAWS one, from seven numbers per week that the student types into four fields
plus three labels they type into three more. So the paper corpus and the web
version are not measuring different things after all; they are the same student
work recorded at different points. What a paper submission holds as a finished
chart, the web version holds as the seven text fields that produced it.

This module recovers those fields, so the lo-blocks prompts can be measured on
real student work:

    baseline, week_1, week_2, week_3   seven daily numbers each, Sunday first
    graph_title, graph_x_axis, graph_y_axis, graph_series (the legend)

Sources, in order of trust:

  1. The chart part's XML. Both the labels (c:title on the chart and on each
     axis) and the plotted series (c:numCache) are literal recorded values —
     no inference at all. Four of the twenty submissions carry one.
  2. The 1b data table, read by an LLM. Deterministic parsing is not viable
     here and it is not worth pretending otherwise: across the corpus the data
     arrives as prose with units in parentheses ("Monday- 1:30am- 10:00am (9
     hours)"), as a table with weeks in rows and Monday first, and as a table
     with days in rows and weeks in columns. This is the same judgement call
     the scorer makes on item 1b, which it grades with a model for the same
     reason.
  3. The embedded image, read by the same model with vision. Ten submissions
     carry their graph only as a picture, and its labels are legible there and
     nowhere else.

Every field records where it came from, and `--show` prints the reconstruction
for eye-checking, because a measurement resting on an extraction step should be
inspectable rather than trusted.

What is NOT reconstructed, deliberately: whether the student supplied a graph at
all. Five submissions have none — four blank, one keeping only the template's
worked example. In the web version that state is unreachable, since the page
draws a chart from whatever data is entered. Those participants are marked
`had_own_graph: false` and excluded from the comparison rather than scored
against a gold row for a task the web version cannot fail.

Usage:
    python3 simulate_h3.py                 # all participants, cached
    python3 simulate_h3.py --show          # print the reconstruction
    python3 simulate_h3.py --refresh       # re-run the extraction
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from backends import BackendError, make_backend
from docx_text import chart_labels, extract_media
from forms import config, find_submissions
from segment import segment
import paths

OUTDIR = f"{paths.roots().out}/h3_sim"
MEDIA_DIR = str(paths.media_dir())
TEMPLATE_MARKERS = ("water consumption", "ounces of water")

DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

SYSTEM = """You recover structured data from a student's coursework document.

You are given one student's Handout 3 submission for a behavior-modification
project: four weeks of daily self-monitoring data, and a graph of it.

A different version of this assignment asks the student to TYPE their data and
their graph's labels, and draws the graph for them. Your job is to report what
that student would have typed, reading it off what they actually submitted.

Rules:
1. Report data as SEVEN numbers per week, Sunday first, comma-separated. Convert
   to the plain number the student was tracking — "(9 hours)" is 9, "0 min" is 0,
   "1.3" is 1.3. If a single DAY within a provided week is missing or blank, use 0.
2. A WEEK THE STUDENT NEVER PROVIDED is different from a week they recorded as
   zeros, and the difference is scored. Return an EMPTY STRING only for a week
   that is genuinely absent — missing, or written as "none", or carrying no
   figures at all. Return the zeros when the student actually recorded zeros: a
   baseline week of no exercise is data. Never invent zeros to fill a week that
   is not there.
3. Some students log a WEEKLY TOTAL rather than seven daily figures ("Week 1: 3
   days met goal"). Report that single number as the week's value and set
   data_granularity to "weekly_total". Do not invent seven daily readings and do
   not return an empty string — they had data, recorded more coarsely.
4. Re-order days if the source lists them Monday-first. Sunday always comes
   first in your output.
5. There are four weeks in this order: the baseline week, then weeks 1, 2 and 3.
   If a table's columns are weeks and its rows are days, read down the columns.
6. Report labels as the LITERAL text the student used. If the graph has no title,
   or an axis has no title, return an empty string for it — do not invent one and
   do not copy a value from the other axis.
7. Axis labels are the axis TITLES, not the tick values. "Sunday, Monday, ..."
   along the bottom is tick data, not an x-axis label.
8. A default placeholder counts as the literal text: if a chart says the words
   "Chart Title", report "Chart Title".
9. The blank handout ships a worked example titled "Water {{corpus:1c/p5:title:5:32:sha=97ca3baaf650:shape=S2-0a202020,R30-0-22}} with axes "Days of the Week" and "Ounces of Water per Day". That is NOT
   the student's work. If the only graph is that one, set had_own_graph false.
10. graph_series is the LEGEND: the key naming the plotted series, reported as a
   comma-separated list in the order the series are plotted (baseline first).
   Report the student's own wording — "Baseline, Wk 1, Wk 2, Wk 3" if that is
   what the key says. Return an empty string when the graph has no key at all,
   and report only the names that ARE there when the key is partial: a legend
   naming two of four series is scored differently from one naming all four, so
   do not complete it for them. A legend is a KEY naming series, not the axis
   tick values and not the chart title.

Return only the JSON object required by the schema."""

SCHEMA = {
    "type": "object",
    "properties": {
        "had_own_graph": {"type": "boolean"},
        "graph_title": {"type": "string"},
        "graph_x_axis": {"type": "string"},
        "graph_y_axis": {"type": "string"},
        "graph_series": {"type": "string"},
        "baseline": {"type": "string"},
        "week_1": {"type": "string"},
        "week_2": {"type": "string"},
        "week_3": {"type": "string"},
        "data_granularity": {
            "type": "string",
            "enum": ["daily", "weekly_total", "none"],
        },
        "notes": {"type": "string"},
    },
    "required": [
        "had_own_graph", "graph_title", "graph_x_axis", "graph_y_axis",
        "graph_series",
        "baseline", "week_1", "week_2", "week_3", "data_granularity", "notes",
    ],
    "additionalProperties": False,
}

_NUM = re.compile(r"-?\d+(?:\.\d+)?")

# Every field a cached reconstruction must carry to be reusable. Adding a field
# here invalidates the cache for it, which is the point — see load_all.
REQUIRED_FIELDS = (
    "baseline", "week_1", "week_2", "week_3",
    "graph_title", "graph_x_axis", "graph_y_axis", "graph_series",
)


def student_chart(path: str) -> dict | None:
    """The student's own chart part, if the file has one."""
    for ch in chart_labels(path):
        if ch["origin"] == "student":
            return ch
    return None


def chart_series(path: str) -> list[list[str]]:
    """The plotted series of the student's chart, straight out of numCache.

    Literal recorded numbers — the one part of this reconstruction that involves
    no inference whatsoever.
    """
    import zipfile
    import xml.etree.ElementTree as ET

    C = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"
    A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    out: list[list[str]] = []
    with zipfile.ZipFile(path) as z:
        for name in sorted(n for n in z.namelist()
                           if re.match(r"word/charts/chart\d+\.xml$", n)):
            root = ET.fromstring(z.read(name))
            el = root.find(f".//{C}chart/{C}title")
            title = "".join(t.text or "" for t in el.iter(A + "t")).strip() if el is not None else ""
            if any(m in title.lower() for m in TEMPLATE_MARKERS):
                continue
            for ser in root.iter(C + "ser"):
                vals = [v.text or "" for v in ser.findall(f".//{C}val//{C}pt/{C}v")]
                if vals:
                    out.append(vals)
    return out


def chart_series_names(path: str) -> list[str]:
    """The series NAMES of the student's chart — i.e. its legend, from c:ser/c:tx.

    The names are what a legend displays, so where the document carries a chart
    part this is the legend recorded literally, with no inference. Charts whose
    series were never named have no c:tx and yield nothing, which is the same
    state as having no key at all.
    """
    import zipfile
    import xml.etree.ElementTree as ET

    C = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"
    A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
    out: list[str] = []
    with zipfile.ZipFile(path) as z:
        for name in sorted(n for n in z.namelist()
                           if re.match(r"word/charts/chart\d+\.xml$", n)):
            root = ET.fromstring(z.read(name))
            el = root.find(f".//{C}chart/{C}title")
            title = "".join(t.text or "" for t in el.iter(A + "t")).strip() if el is not None else ""
            if any(m in title.lower() for m in TEMPLATE_MARKERS):
                continue
            for ser in root.iter(C + "ser"):
                tx = ser.find(f"{C}tx")
                if tx is None:
                    continue
                label = "".join(v.text or "" for v in tx.iter(C + "v")).strip()
                if label:
                    out.append(label)
    return out


def spread_total(total: str) -> str:
    """Turn one weekly total into seven daily values that sum to it.

    A student who recorded "3 days met goal" has data, but not in the shape the
    web version's fields take. Left as a single number it would plot as one bar
    and trip the chart's own "expected 7 values" warning, and that mismatch would
    then show up in the measurement as though the prompt had misjudged something.

    Spreading the total evenly across the seven days keeps the one quantity the
    student actually reported — the weekly total — exactly intact, and produces a
    well-formed series. The daily distribution is arithmetic, not evidence, which
    is why it is recorded as synthesised provenance.
    """
    try:
        t = float(total)
    except (TypeError, ValueError):
        return ""
    whole = int(t) if float(t).is_integer() else None
    if whole is None:
        each = t / 7.0
        vals = [f"{each:.2f}".rstrip("0").rstrip(".") for _ in range(7)]
        return ", ".join(vals)
    base, extra = divmod(abs(whole), 7)
    sign = -1 if whole < 0 else 1
    vals = [base + (1 if i < extra else 0) for i in range(7)]
    return ", ".join(str(sign * v) for v in vals)


def normalise_week(raw: str) -> str:
    """Seven comma-separated numbers, as the web field wants them.

    An empty result means the week was never provided — which is NOT the same as
    a week of zeros, and item 1b scores the difference. Padding an absent week
    with zeros would have made p15 (baseline written as "none", one week never
    typed) and p18 (nothing at all) look like complete datasets, while p3's
    genuinely zero baseline has to survive as zeros.
    """
    nums = _NUM.findall(raw or "")
    if not nums:
        return ""
    # Do NOT pad to seven. A student who logged a weekly total has one number,
    # and padding it with zeros would both invent data and hide the mismatch
    # between what they recorded and what the fields ask for.
    return ", ".join(nums[:7])


def build_evidence(path: str, pid: int, sections: dict[str, str]) -> tuple[str, list[str], dict]:
    """Everything known about this submission, plus what came from XML."""
    parts: list[str] = []
    hard: dict = {}
    images: list[str] = []

    ch = student_chart(path)
    if ch:
        hard["graph_title"] = ch["title"]
        hard["graph_x_axis"] = ch["x_axis_label"]
        hard["graph_y_axis"] = ch["y_axis_label"]
        parts.append(
            "CHART PART (the student's own, read from the document XML):\n"
            f"  title: {ch['title']!r}\n"
            f"  x-axis title: {ch['x_axis_label']!r}\n"
            f"  y-axis title: {ch['y_axis_label']!r}\n"
            f"  legend present: {ch['has_legend']}"
        )
        names = chart_series_names(path)
        if names:
            hard["graph_series"] = ", ".join(names)
            parts.append(f"  series names (the legend): {', '.join(names)!r}")
        series = chart_series(path)
        if len(series) >= 4:
            keys = ["baseline", "week_1", "week_2", "week_3"]
            for k, vals in zip(keys, series[:4]):
                hard[k] = normalise_week(", ".join(vals))
            parts.append(
                "PLOTTED SERIES, in order, straight from the chart XML — these are\n"
                "the numbers the graph was drawn from:\n"
                + "\n".join(f"  {k}: {hard[k]}" for k in keys)
            )

    data = (sections.get("1b") or "").strip()
    parts.append(
        "THEIR 1b DATA as it appears in the document:\n"
        + (data[:2000] if data else "(nothing under the 1b heading)")
    )

    tail = (sections.get("1c") or "").strip()
    if tail:
        parts.append(
            "TEXT under their 1c heading. This may be a graph drawn as grouped\n"
            "shapes, in which case the title and tick values arrive run together,\n"
            f"or a written description of a graph:\n{tail[:1200]!r}"
        )

    if not ch:
        try:
            images = extract_media(path, os.path.join(MEDIA_DIR, f"p{pid:03d}"))
        except Exception:
            images = []
        for p in images:
            parts.append(
                f"IMAGE at {p} — use the Read tool to look at it. Decide whether it is\n"
                "the student's own graph or the template's 'Water Consumption Over Four\n"
                "Weeks' example, then read off its title and axis titles."
            )
    if not parts:
        parts.append("NOTHING: no chart, no image, no data.")
    return "\n\n".join(parts), images, hard


def simulate_one(backend, pid: int, path: str) -> dict:
    cfg = config(3)
    sections = segment(path, cfg["template"], cfg["markers"], cfg["capture_tail"],
                       cfg.get("join_aware", False))
    evidence, images, hard = build_evidence(path, pid, sections)

    prompt = (
        f"# Participant {pid}\n\n"
        "Report what this student would have typed into the web version of this\n"
        "assignment: four weeks of seven daily numbers, and their graph's three\n"
        "labels.\n\n" + evidence
    )
    kw = {"allow_tools": ["Read"], "max_turns": 8} if images else {}
    raw = backend.complete(SYSTEM, prompt, SCHEMA, **kw)

    granularity = raw.get("data_granularity", "daily")
    week_of = (
        (lambda v: spread_total(normalise_week(v)))
        if granularity == "weekly_total" else normalise_week
    )
    fields = {
        "baseline": week_of(raw.get("baseline", "")),
        "week_1": week_of(raw.get("week_1", "")),
        "week_2": week_of(raw.get("week_2", "")),
        "week_3": week_of(raw.get("week_3", "")),
        "graph_title": (raw.get("graph_title") or "").strip(),
        "graph_x_axis": (raw.get("graph_x_axis") or "").strip(),
        "graph_y_axis": (raw.get("graph_y_axis") or "").strip(),
        "graph_series": (raw.get("graph_series") or "").strip(),
    }
    # XML beats inference wherever we have it.
    provenance = {k: "model" for k in fields}
    if granularity == "weekly_total":
        for k in ("baseline", "week_1", "week_2", "week_3"):
            if fields[k]:
                provenance[k] = "weekly_total_spread"
    for k, v in hard.items():
        fields[k] = v
        provenance[k] = "chart_xml"

    return {
        "participant_id": pid,
        "had_own_graph": bool(raw.get("had_own_graph")),
        "data_granularity": granularity,
        "graph_source": ("chart_part" if hard else
                         "image" if images else
                         "drawn_shapes_or_text" if (sections.get("1c") or "").strip() else
                         "none"),
        "fields": fields,
        "provenance": provenance,
        "notes": raw.get("notes", ""),
    }


def load_all(refresh: bool = False, backend_kind: str = "cli", workers: int = 4) -> dict[int, dict]:
    os.makedirs(OUTDIR, exist_ok=True)
    targets = find_submissions(3, None)
    out: dict[int, dict] = {}
    todo = []
    for pid, path in targets:
        fp = os.path.join(OUTDIR, f"participant_{pid:03d}.json")
        if os.path.exists(fp) and not refresh:
            with open(fp) as fh:
                rec = json.load(fh)
            # A cache written before a field existed is not a cache hit. Serving
            # it would hand the harness an empty legend for all twenty and read
            # as a prompt that never scores one — so re-extract instead.
            if all(k in rec.get("fields", {}) for k in REQUIRED_FIELDS):
                out[pid] = rec
                continue
            todo.append((pid, path))
        else:
            todo.append((pid, path))
    if todo:
        backend = make_backend(backend_kind)
        print(f"reconstructing {len(todo)} participant(s)", file=sys.stderr)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futs = {pool.submit(simulate_one, backend, pid, path): pid for pid, path in todo}
            for fut in as_completed(futs):
                pid = futs[fut]
                try:
                    rec = fut.result()
                except BackendError as e:
                    print(f"  p{pid}: FAILED {e}", file=sys.stderr)
                    continue
                out[pid] = rec
                with open(os.path.join(OUTDIR, f"participant_{pid:03d}.json"), "w") as fh:
                    json.dump(rec, fh, indent=2)
                print(f"  p{pid}: {rec['graph_source']}", file=sys.stderr)
    return dict(sorted(out.items()))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("Usage:")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--backend", default="cli", choices=["cli", "api"])
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--show", action="store_true", help="Print the reconstruction.")
    args = ap.parse_args()

    sims = load_all(args.refresh, args.backend, args.workers)
    if args.show:
        for pid, s in sims.items():
            f = s["fields"]
            src = s["graph_source"]
            own = "own graph" if s["had_own_graph"] else "NO OWN GRAPH"
            print(f"\np{pid:<3} [{src}, {own}]")
            print(f"   title  {f['graph_title']!r:<50} ({s['provenance']['graph_title']})")
            print(f"   x-axis {f['graph_x_axis']!r:<50} ({s['provenance']['graph_x_axis']})")
            print(f"   y-axis {f['graph_y_axis']!r:<50} ({s['provenance']['graph_y_axis']})")
            print(f"   legend {f['graph_series']!r:<50} ({s['provenance']['graph_series']})")
            for k in ("baseline", "week_1", "week_2", "week_3"):
                print(f"   {k:<9} {f[k]:<42} ({s['provenance'][k]})")
    else:
        n_own = sum(1 for s in sims.values() if s["had_own_graph"])
        print(f"{len(sims)} reconstructed; {n_own} with their own graph")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
