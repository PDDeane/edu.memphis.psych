#!/usr/bin/env python3
"""Measure how much of this course is embedded in the engine's own source.

§2.1 counted TABLES and called itself a floor. §10.7 redefined a clean module as
FOUR counts, and nothing measured all four. This does.

WHY THE NUMBERS MATTER MORE THAN THE SCAN. Two ad-hoc measurements taken while
writing the plan were wrong in the same direction, both inflating the problem: 53
"literal id branches" were really 13 plus three unrelated populations, and 188
"course words in docstrings" were ~30 once `handout` (127 uses, a structural noun)
and software-sense `behaviour` (35) were removed. A migration sized against either
figure would have been sized against nothing.

THE IDS ARE AN INPUT, NEVER A PATTERN IN THIS FILE. To find `Q1`, `WK2` and `1c`
the scan needs this course's item ids — and a hard-coded
`Q\\d+[a-c]?|WK[12]|DAY[12]|...` is EXACTLY the embedding this tool exists to
detect. Such a scan passes its own test forever and finds nothing in a second
course. So ids are read from the rubric (and later from the course file), and this
module carries no id pattern of its own.

IT REPORTS POPULATIONS; IT DOES NOT GUESS THEM. "Is this hit inside
`enforcement_selftest`?" is decidable. "Is this a data builder or an engine
branch?" is not. Where it cannot decide it reports the raw hit with its enclosing
function and leaves the classification to a person: a wrong split is worse than
none, because the per-module proof would then count the wrong things and report
clean modules that are not.

ITS JSON IS AN INTERFACE. T4.1 gates Stage 4 on these counts, so the shape carries
a `schema_version` and a reader must refuse an unknown one. A gate that reads a
changed shape may report zero findings, and zero findings looks like success.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys

SCHEMA_VERSION = 1
HERE = os.path.dirname(os.path.abspath(__file__))

# Every term carries its justification. A term added without one fails
# `self_test()` -- the vocabulary is the part of this tool most able to invent a
# problem, so it is the part that must argue for itself.
VOCABULARY: dict[str, str] = {
    "psycholog": "names the discipline; no engine concept needs it",
    "operant": "a behaviour-modification term; the engine has no operants",
    "utb": "unwanted target behaviour -- this course's construct",
    "reinforc": "behaviour-modification vocabulary",
    "punish": "behaviour-modification vocabulary",
    "behavior_1": "a course SLOT name, not English",
    "behavior_n": "a course SLOT name, not English",
}

# Excluded by declaration, with the measurement that justifies the exclusion.
# Both were counted by an earlier regex and between them made the problem look
# five times larger than it is.
EXCLUDED: dict[str, str] = {
    "handout": "127 uses. A STRUCTURAL unit the engine has whatever the course "
               "is, and most uses are usage documentation (`--handout 1`).",
    "behaviour": "35 uses, mostly ordinary software English -- `_behaviour_src` "
                 "hashes a function's behaviour; 'the caller keeps its existing "
                 "behaviour'. F1 requires surviving uses to be unambiguous "
                 "(`code behaviour`), which is enforced by T7.3, not here.",
}


# An id short or plain enough to collide with an ordinary string. `'3'` is an
# item id AND the string "3": it matched `enforcement.VERDICT_SPACE_DIVERGENCES`,
# which is about verdict spaces and mentions no item. Hits resting ONLY on an
# ambiguous id are reported separately and NOT counted -- per the design, where
# this tool cannot decide it hands the hit to a person rather than guessing.
def _ambiguous(i: str) -> bool:
    return len(i) < 2 or i.isdigit()


# Course artifacts that appear in MODULE NAMES but are not item ids. §10.7's
# fourth category is "a course artifact in its own name", and an id-only rule
# finds 2 of the 9 such modules -- it cannot see `rubric_h1.py` or `score_h1.py`,
# which name a HANDOUT, or `handouts.py` and `gold.py`, which name course data.
# Declared with justification, like VOCABULARY.
NAME_MARKERS: dict[str, str] = {
    "h1": "handout 1 -- a course artifact, not an engine concept",
    "h2": "handout 2",
    "h3": "handout 3",
    "handouts": "the course's handouts as a set",
    "gold": "the graders' scores for this course",
}


def item_ids(source: str | None = None) -> set[str]:
    """This course's item ids, from DATA. Never a pattern.

    Reads the course file when one exists; the rubric modules until then. A
    second course supplies its own ids and this module is unchanged.
    """
    if source and os.path.exists(source):
        doc = json.load(open(source))
        return {str(i["id"]) for i in doc.get("items", []) if "id" in i}
    ids: set[str] = set()
    sys.path.insert(0, HERE)
    for h in (1, 2, 3):
        try:
            mod = __import__(f"rubric_h{h}")
        except Exception:
            continue
        ids |= {str(k) for k in (getattr(mod, "BY_ID", {}) or {})}
    if not ids:
        raise SystemExit(
            "course_inventory: no item ids available. The rubric modules did not "
            "import and no course file was given -- scanning with an EMPTY id set "
            "would report every module clean, which is not the same as clean.")
    return ids


def _enclosing(tree: ast.AST) -> dict[int, str]:
    """line -> enclosing function name, for hits this tool will not classify."""
    owner: dict[int, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for ln in range(node.lineno, (node.end_lineno or node.lineno) + 1):
                owner.setdefault(ln, node.name)
    return owner


def scan_module(path: str, ids: set[str]) -> dict:
    """The four counts for one module, with every hit carrying its context."""
    src = open(path, errors="replace").read()
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return {"module": os.path.basename(path), "unparsed": str(exc)}
    owner = _enclosing(tree)
    name = os.path.basename(path)

    tables, literals, vocab, unclassified = [], [], [], []

    for node in tree.body:
        target = None
        if isinstance(node, ast.Assign) and node.targets:
            target = getattr(node.targets[0], "id", None)
        elif isinstance(node, ast.AnnAssign):
            target = getattr(node.target, "id", None)
        if not target:
            continue
        seg = ast.get_source_segment(src, node) or ""
        named = sorted({i for i in ids if re.search(rf"[\"']{re.escape(i)}[\"']", seg)})
        if named:
            entry = {"name": target, "lines": (node.end_lineno or node.lineno)
                     - node.lineno + 1, "ids": named[:8]}
            if all(_ambiguous(i) for i in named):
                entry["ambiguous_only"] = True
                unclassified.append(entry)
            else:
                tables.append(entry)

    for node in ast.walk(tree):
        found = None
        if isinstance(node, ast.Compare):
            for c in [node.left] + list(node.comparators):
                if isinstance(c, ast.Constant) and str(c.value) in ids:
                    found = str(c.value)
        if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant) \
                and str(node.slice.value) in ids:
            found = str(node.slice.value)
        if found:
            literals.append({"id": found, "line": node.lineno,
                             "in": owner.get(node.lineno, "<module level>")})

    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.ClassDef,
                             ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node)
            if not doc:
                continue
            for term in VOCABULARY:
                for m in re.finditer(rf"\b{term}\w*", doc, re.I):
                    vocab.append({"term": term, "in": getattr(node, "name", "<module>"),
                                  "text": " ".join(doc[max(0, m.start() - 40):
                                                       m.start() + 60].split())[:100]})

    stem = name[:-3].lower()
    named_for = sorted({i for i in ids
                        if re.search(rf"(^|[_-]){re.escape(i.lower())}([_-]|$)", stem)}
                       | {k for k in NAME_MARKERS
                          if re.search(rf"(^|[_-]){k}([_-]|$)", stem)})
    return {"module": name, "tables": tables, "literal_ids": literals,
            "vocabulary": vocab, "name_names_course": named_for,
            "unclassified_tables": unclassified,
            "counts": {"tables": len(tables), "literal_ids": len(literals),
                       "vocabulary": len(vocab), "named": len(named_for),
                       "unclassified": len(unclassified)}}


def inventory(directory: str | None = None, course_file: str | None = None) -> dict:
    directory = directory or HERE
    ids = item_ids(course_file)
    mods = sorted(f for f in os.listdir(directory) if f.endswith(".py"))
    per = [scan_module(os.path.join(directory, f), ids) for f in mods]
    totals = {k: sum(m.get("counts", {}).get(k, 0) for m in per)
              for k in ("tables", "literal_ids", "vocabulary", "named",
                        "unclassified")}
    return {"schema_version": SCHEMA_VERSION, "id_count": len(ids),
            "modules_scanned": len(per), "totals": totals, "modules": per,
            "vocabulary_declared": VOCABULARY, "vocabulary_excluded": EXCLUDED}


def self_test() -> list[str]:
    """What this tool must not get wrong about itself."""
    bad = []
    for term, why in VOCABULARY.items():
        if not why.strip():
            bad.append(f"vocabulary term {term!r} carries no justification")
    for term, why in EXCLUDED.items():
        if not why.strip():
            bad.append(f"exclusion {term!r} carries no justification")
    for term, why in NAME_MARKERS.items():
        if not why.strip():
            bad.append(f"name marker {term!r} carries no justification")
    overlap = set(VOCABULARY) & set(EXCLUDED)
    if overlap:
        bad.append(f"terms both counted and excluded: {sorted(overlap)}")
    src = open(os.path.abspath(__file__), errors="replace").read()
    body = src.split('"""', 2)[-1]
    for pat in (r"Q\\d", r"WK\[12\]", r"DAY\[12\]"):
        if re.search(pat, body):
            bad.append(f"this tool carries an item-id PATTERN ({pat}); ids are an input")
    return bad


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dir", default=HERE)
    ap.add_argument("--course-file", default=None)
    ap.add_argument("--json", metavar="PATH")
    args = ap.parse_args(argv)

    problems = self_test()
    if problems:
        for p in problems:
            print(f"  REFUSING: {p}")
        return 2

    inv = inventory(args.dir, args.course_file)
    t = inv["totals"]
    print(f"  {inv['modules_scanned']} modules, {inv['id_count']} item ids from data\n")
    print(f"  {'module':<26} {'tables':>7} {'ids':>5} {'vocab':>6} {'named':>6}")
    for m in sorted(inv["modules"], key=lambda m: -sum(m.get("counts", {}).values())):
        c = m.get("counts")
        if not c or not sum(c.values()):
            continue
        print(f"  {m['module']:<26} {c['tables']:>7} {c['literal_ids']:>5} "
              f"{c['vocabulary']:>6} {c['named']:>6}")
    print(f"\n  {'TOTAL':<26} {t['tables']:>7} {t['literal_ids']:>5} "
          f"{t['vocabulary']:>6} {t['named']:>6}")
    if args.json:
        json.dump(inv, open(args.json, "w"), indent=1)
        print(f"\n  written: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
