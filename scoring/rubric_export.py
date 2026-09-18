#!/usr/bin/env python3
"""Write the rubric modules out as the course's canonical JSON.

A1c: `rubric_h2`'s four builders survive as an AUTHORING tool that GENERATES this
file. No reader ever instantiates a template, so the file carries every item in
full and the readers stay simple.

DERIVED-OR-AUTHORED IS DECIDED BY RECOMPUTATION, NEVER BY A LIST. §9.0 sorted the
module exports with a substring test -- does the assignment mention `ITEMS`, a
loop, `sum(` or `BY_ID` -- and says in as many words that it is "a starting point,
not a finding". An export that ACTS on that list can silently lose data: drop
something that is not in fact derivable and the value is gone.

So each candidate is RECOMPUTED and compared. A value is dropped only when a
known derivation reproduces it EXACTLY; everything else is carried as authored
data, whatever §9.0 guessed. The comparison is printed, so §9.0 is corrected by
this run rather than left standing.

CONSERVATIVE BY CONSTRUCTION. Carrying a value that turns out to be derivable
costs a few kilobytes. Dropping one that is not loses it. Where this tool cannot
recompute something it CARRIES it -- and says so -- rather than trusting a guess.

NO FIELD TAGGING HERE. §9.2a's RUBRIC/GENERATOR split is applied at Stage 4, when
`olx_prompts.py`'s generator fields arrive under B2a. Tagging at Stage 2 would
mark every field RUBRIC, make the classification trivially uniform, and let
T2.2's check pass while proving nothing -- the vacancy T0.1 exists to catch,
reproduced in a new place.

DETERMINISTIC MEANS A PINNED ORDER. Python dicts are insertion-ordered and the
builders construct in loops, so an unpinned file changes whenever iteration order
does: a large diff with no content, which reviewers learn to skim. Keys are sorted
within an entry; items stay in RUBRIC order, because that is how a person reads
them.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

SCHEMA_VERSION = 1
HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUTS = (1, 2, 3)

# The derivations this tool can actually perform. A candidate absent from here is
# CARRIED, not dropped -- the list is what the tool can prove, not what someone
# believed was derivable.
#
# MOVES TO THE READER AT STAGE 3, and lives there alone. A2a says the reader
# recomputes derived values; this tool decides what to drop. Those are the same
# question asked from two sides, and two implementations that must agree is the
# defect T5.1 already had to be redesigned to avoid. From Stage 3 this table is
# imported from `coursedata.py`, and the export drops exactly what the reader can
# rebuild -- no more, and never by a different rule.
#
# IT IS ALSO THE MEASURE OF A2a's PROGRESS. §9.0 called twelve names derived; this
# proves two. The other ten -- SLOT_SPEC, OC_GATES, FORBID, SLOT_OPTIONS and the
# six *_ITEMS index lists -- are carried until the reader can rebuild them, so
# A2a is two-twelfths honoured today and the file is larger than A2a intends. Each
# derivation written in the reader moves one value out of the file, with T5.1
# proving equivalence as it goes.
DERIVATIONS = {
    "BY_ID": lambda items: {it["id"]: it for it in items},
    "TOTAL": lambda items: sum(it["max"] for it in items),
}


def _load(handout: int):
    sys.path.insert(0, HERE)
    return __import__(f"rubric_h{handout}")


def _exports(mod) -> dict:
    """Module-level names a reader could want: upper-case, not private."""
    return {n: getattr(mod, n) for n in dir(mod)
            if n.isupper() and not n.startswith("_")}


def classify(mod) -> tuple[dict, list[dict]]:
    """-> (carried authored values, per-candidate report).

    Every export except ITEMS is a candidate. It is dropped only if a known
    derivation reproduces it exactly.
    """
    items = list(getattr(mod, "ITEMS", []) or [])
    carried, report = {}, []
    for name, value in sorted(_exports(mod).items()):
        if name == "ITEMS":
            continue
        fn = DERIVATIONS.get(name)
        if fn is None:
            carried[name] = value
            report.append({"name": name, "verdict": "carried",
                           "why": "no derivation this tool can perform"})
            continue
        try:
            again = fn(items)
        except Exception as exc:
            carried[name] = value
            report.append({"name": name, "verdict": "carried",
                           "why": f"derivation raised {type(exc).__name__}: {exc}"})
            continue
        if again == value:
            report.append({"name": name, "verdict": "dropped",
                           "why": "recomputation reproduced it exactly"})
        else:
            carried[name] = value
            report.append({"name": name, "verdict": "carried",
                           "why": "recomputation DIFFERED -- not derivable after all"})
    return carried, report


def _jsonable(x, path="") -> object:
    """Refuse silently dropping anything this cannot represent."""
    if isinstance(x, dict):
        return {str(k): _jsonable(v, f"{path}.{k}") for k, v in sorted(x.items(),
                                                                      key=lambda kv: str(kv[0]))}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v, f"{path}[{i}]") for i, v in enumerate(x)]
    if isinstance(x, (str, int, float, bool)) or x is None:
        return x
    raise SystemExit(
        f"rubric_export: {path or '<root>'} holds {type(x).__name__}, which this "
        f"tool cannot represent. That is an ERROR, not an omission -- a field "
        f"quietly dropped here is a field lost.")


def build(course_id: str) -> tuple[dict, list[dict]]:
    doc = {"schema_version": SCHEMA_VERSION, "course": course_id,
           "handouts": {}, "items": []}
    full_report = []
    for h in HANDOUTS:
        mod = _load(h)
        items = list(getattr(mod, "ITEMS", []) or [])
        carried, report = classify(mod)
        for r in report:
            r["handout"] = h
        full_report += report
        doc["handouts"][str(h)] = {"authored": _jsonable(carried, f"h{h}")}
        for it in items:                       # RUBRIC order, deliberately
            entry = _jsonable(it, f"h{h}.{it.get('id')}")
            entry["handout"] = h
            doc["items"].append(entry)
    return doc, full_report


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--course", default="edu.memphis.psych")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    doc, report = build(args.course)
    dropped = [r for r in report if r["verdict"] == "dropped"]
    carried = [r for r in report if r["verdict"] == "carried"]

    print(f"  items: {len(doc['items'])}   candidates: {len(report)}")
    print(f"  dropped as derived (recomputation reproduced them): {len(dropped)}")
    for r in dropped:
        print(f"    h{r['handout']} {r['name']}")
    print(f"  carried as authored: {len(carried)}")
    for r in carried:
        print(f"    h{r['handout']} {r['name']:<24} {r['why'][:52]}")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(doc, fh, indent=1, sort_keys=False)
        fh.write("\n")
    print(f"\n  written: {args.out} ({os.path.getsize(args.out):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
