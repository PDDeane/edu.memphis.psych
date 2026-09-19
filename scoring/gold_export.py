#!/usr/bin/env python3
"""C1b — the gold file: everything keyed by a participant, in a SECOND file.

WHY A SECOND FILE AND NOT A SECTION OF `course.json`. Because of what these
tables are keyed by. `CORRECTED_GOLD[("NR", 4)]`, `GRAPH_UNREACHABLE_1C = (4, 19,
20)`, `DECLARED_CEILING_CELLS[("1c", 12)]` -- every one names a PARTICIPANT, and
this repository's own rule says the gold sheets are "the key that makes those IDs
meaningful". `course.json` ships in a public repository; this file does not.

WHERE IT GOES. `$COURSE_DATA/courses/<course-id>/gold.json`, beside the
submissions it describes and outside the repo. `--out` overrides, which is how
this tool is tested without writing to the data store.

WHAT IT IS NOT. Not the graders' scores -- those live in the three
`Scoring & Feedback` workbooks and are read by `gold.py`. This carries the
DECLARATIONS ABOUT gold: which cells are corrected and why, which diverge, which
ceilings are declared unreachable, which slots cannot be mapped. They are
judgements this project made about the graders' marks, and they are
participant-keyed because a judgement is about one person's answer.

THE TUPLE KEYS ARE TAGGED, the same way `rubric_export` tags them: JSON has
string keys only, and `("NR", 4)` joined with a separator would round-trip until
a key contained the separator. A key stored as a LIST comes back the tuple it was.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

SCHEMA_VERSION = 1

# module -> the gold declarations it holds. Named rather than discovered: a
# table's being about gold is a judgement, and `GOLD` in the name is a
# convention, not a guarantee -- `DECLARED_CEILING_CELLS` and
# `CONSENSUS_OVERLAP_BACKLOG` carry participants and say nothing about gold in
# their names, while a table could be called GOLD_* and hold none.
GOLD_TABLES = {
    "handouts": ("CORRECTED_GOLD", "GOLD_DIVERGENCES", "GOLD_CEILINGS",
                 "PER_ITEM_EXCLUDE"),
    "measured": ("GOLD_SLOT_CHARGES", "GOLD_CODE_KNOWN",
                 "GOLD_SLOT_BOUNDS_KNOWN", "GOLD_SLOT_UNMAPPABLE",
                 "GOLD_SLOT_DISAGREEMENTS_KNOWN", "SILENT_GOLD_DIVERGENCES",
                 "DECLARED_CEILING_CELLS", "_1C_GATE_CEILING"),
    "agreement": ("GRAPH_UNREACHABLE_1C", "UNSCORED_GOLD_CRITERIA"),
    "enforcement": ("CONSENSUS_OVERLAP_BACKLOG", "FIXTURE_GOLD_OVERRIDES"),
}

# Per-handout participant lists, which live inside `handouts.HANDOUTS` and were
# left there when the rest of that table was split.
HANDOUT_PARTICIPANT_FIELDS = ("cited_participants", "exemplar_participants",
                              "suspect_participants")


def _jsonable(x, path=""):
    if isinstance(x, dict):
        # A DICT WITH NON-STRING KEYS IS TAGGED, not stringified. JSON has string
        # keys only, and `{16: {...}}` written as `{"16": {...}}` comes back with
        # a STRING where a participant id was -- which is a silent type change in
        # the one field that identifies a person. `PER_ITEM_EXCLUDE` nests
        # exactly that, two levels down, and the round-trip assertion caught it
        # on this tool's first run.
        if any(not isinstance(k, str) for k in x):
            return {"__dict__": [[_jsonable(k, f"{path}.key"),
                                  _jsonable(v, f"{path}.{k}")]
                                 for k, v in x.items()]}
        return {str(k): _jsonable(v, f"{path}.{k}") for k, v in x.items()}
    if isinstance(x, tuple):
        return {"__tuple__": [_jsonable(v, f"{path}[{i}]") for i, v in enumerate(x)]}
    if isinstance(x, (list, set, frozenset)):
        return [_jsonable(v, f"{path}[{i}]") for i, v in enumerate(x)]
    if isinstance(x, (str, int, float, bool)) or x is None:
        return x
    raise SystemExit(
        f"gold_export: {path or '<root>'} holds {type(x).__name__}, which this "
        f"tool cannot represent. That is an ERROR, not an omission -- a gold "
        f"declaration quietly dropped is a declaration lost.")


def _pairs(table):
    """A dict with tuple keys as JSON can hold it: a list of [key, value]."""
    if not isinstance(table, dict):
        return _jsonable(table)
    return [[list(k) if isinstance(k, tuple) else k, _jsonable(v)]
            for k, v in table.items()]


def build() -> dict:
    import importlib

    doc = {"schema_version": SCHEMA_VERSION, "course": None, "declarations": {},
           "handout_participants": {}}
    import coursedata

    doc["course"] = coursedata.course_id()
    for module_name, names in sorted(GOLD_TABLES.items()):
        mod = importlib.import_module(module_name)
        for name in names:
            value = getattr(mod, name, None)
            if value is None:
                continue
            doc["declarations"][name] = _pairs(value)
    import handouts

    for h, cfg in sorted(handouts.HANDOUTS.items()):
        got = {f: _jsonable(cfg[f], f"h{h}.{f}")
               for f in HANDOUT_PARTICIPANT_FIELDS if f in cfg}
        if got:
            doc["handout_participants"][str(h)] = got
    return doc


def round_trip(doc: dict) -> list[str]:
    """Every table comes back exactly what it was. Asserted, not assumed."""
    import importlib

    def detag(x):
        if isinstance(x, dict):
            if set(x) == {"__tuple__"}:
                return tuple(detag(v) for v in x["__tuple__"])
            if set(x) == {"__dict__"}:
                return {detag(k): detag(v) for k, v in x["__dict__"]}
            return {k: detag(v) for k, v in x.items()}
        if isinstance(x, list):
            return [detag(v) for v in x]
        return x

    problems = []
    for module_name, names in sorted(GOLD_TABLES.items()):
        mod = importlib.import_module(module_name)
        for name in names:
            source = getattr(mod, name, None)
            if source is None:
                continue
            stored = doc["declarations"].get(name)
            if isinstance(source, dict):
                back = {tuple(k) if isinstance(k, list) else k: detag(v)
                        for k, v in stored}
            else:
                back = detag(stored)
                if isinstance(source, tuple):
                    back = tuple(back)
                elif isinstance(source, (set, frozenset)):
                    back = type(source)(back)
            if back != source:
                problems.append(
                    f"{module_name}.{name} does not round-trip: stored form "
                    f"rebuilds to {type(back).__name__}, source is "
                    f"{type(source).__name__}")
    return problems


def default_path() -> str | None:
    import coursedata

    root = coursedata.data_root()
    if not root:
        return None
    return os.path.join(root, "courses", coursedata.course_id(), "gold.json")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=None,
                    help="where to write; defaults to $COURSE_DATA/courses/<id>/")
    ap.add_argument("--dry-run", action="store_true",
                    help="build and verify, write nothing")
    args = ap.parse_args(argv)

    doc = build()
    problems = round_trip(doc)

    n_tables = len(doc["declarations"])
    n_entries = sum(len(v) if isinstance(v, list) else 1
                    for v in doc["declarations"].values())
    parts = sum(len(v) for v in doc["handout_participants"].values())
    print(f"  {n_tables} gold declaration table(s), {n_entries} entries, "
          f"{parts} per-handout participant field(s)")
    if problems:
        print(f"\n  {len(problems)} ROUND-TRIP FAILURE(S):")
        for p in problems:
            print(f"    {p}")
        return 1
    print("  every table round-trips exactly.")

    out = args.out or default_path()
    if out is None:
        print("  REFUSING: $COURSE_DATA is unset, so there is nowhere this file "
              "belongs. It must NOT fall back into the repository -- that is the "
              "one place it may not go.")
        return 2

    # THE GUARD THAT CAN ACTUALLY FIRE. The refusal above is unreachable:
    # `coursedata.data_root()` falls back to `paths.DATA`, which always has a
    # value, so `out` is never None. A refusal that cannot happen is a sentence,
    # not a protection -- and while this was being written, a test with
    # `--out ../courses/<id>/gold.json` WROTE 97 KB of participant-keyed
    # declarations into the repository. It was deleted unstaged and uncommitted,
    # and this is why the check is by PATH rather than by intention.
    repo = os.path.dirname(HERE)
    if os.path.abspath(out).startswith(os.path.abspath(repo) + os.sep):
        print(f"  REFUSING to write {out}\n"
              f"  That is inside the repository ({repo}). This file is keyed by "
              f"PARTICIPANT and the repository is public: a 'Participant ID NNN' "
              f"filename is not de-identification. It belongs under $COURSE_DATA "
              f"and nowhere else.")
        return 2
    if args.dry_run:
        print(f"  dry run: would write {out}")
        return 0
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w").write(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    print(f"  written: {out} ({os.path.getsize(out):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
