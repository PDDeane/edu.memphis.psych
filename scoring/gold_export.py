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

SCHEMA_VERSION = 2

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


# `_pairs` WAS HERE, AND WAS LOSSY. It turned a tuple-keyed dict into a bare
# list of [key, value] -- which is indistinguishable from a table that was
# AUTHORED as a list. Three of these sixteen are not mappings at all
# (`GOLD_DIVERGENCES` is a list of dicts, `GRAPH_UNREACHABLE_1C` a tuple,
# `_1C_GATE_CEILING` a prose string), so a reader inverting the pair-list form
# had no way to know which it was holding, and the round-trip raised
# "too many values to unpack" on the first table that was genuinely a list.
#
# `_jsonable` already encodes every one of these shapes self-describingly: it
# tags tuples `__tuple__` and non-string-key dicts `__dict__`, and preserves
# insertion order for the rest. `_pairs` was redundant with it -- its own
# fallthrough called it for anything that was not a dict -- so the encoder is
# now `_jsonable` alone and the decoder is `coursedata._detag`, which already
# inverts both tags. The course file keeps its bare pair-lists: all seven of its
# declarations ARE mappings, so the ambiguity this removes cannot arise there.


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
            doc["declarations"][name] = _jsonable(value)
    import handouts

    for h, cfg in sorted(handouts.HANDOUTS.items()):
        got = {f: _jsonable(cfg[f], f"h{h}.{f}")
               for f in HANDOUT_PARTICIPANT_FIELDS if f in cfg}
        if got:
            doc["handout_participants"][str(h)] = got
    return doc


def _serialize(doc: dict) -> str:
    """The bytes that go to disk. ONE definition, used by the writer and by the
    assertion that the writer is faithful.

    NO `sort_keys`. AUTHORED ORDER IS DATA -- the same rule `rubric_export`
    already carries, and this file was the unfixed twin. It wrote
    `sort_keys=True` while `round_trip` compared the IN-MEMORY doc, which is
    built in insertion order, so the assertion passed and the file on disk was
    alphabetised anyway. Four tables came back reordered to an independent
    reader while the exporter reported "every table round-trips exactly".

    That gap is why this function exists rather than a second `json.dumps` call:
    a round-trip proved against anything other than the actual bytes is proof
    about a thing nobody reads.
    """
    return json.dumps(doc, indent=1, sort_keys=False) + "\n"


def round_trip(doc: dict) -> list[str]:
    """Every table comes back exactly what it was. Asserted, not assumed.

    ONE DECODER, AND IT IS THE READER'S. This function used to carry its own
    tag-inverter and its own shape reconstruction, so it proved that the stored
    form inverts under THIS code -- not under `coursedata`, which is what
    actually reads the file. The two drifted the moment the pair-list encoding
    was retired: the exporter's copy still inverted pair-lists and raised "too
    many values to unpack" on `GOLD_DIVERGENCES`, a table that was always a
    list. Calling the real reader means a round-trip proved here is a round-trip
    the consumer gets.

    ORDER-SENSITIVE COMPARISON. The old test was `back != source`, and `==` on
    dicts IGNORES KEY ORDER. That blindness has already cost this project a day:
    `JOBS[item]["fields"]` decides the order boxes are read in, a sorted export
    silently reordered it, and six hypotheses were ruled out before the
    comparison itself turned out to be the thing that could not see it.
    `same_shape` reports order differences as differences.
    """
    import importlib
    import coursedata
    import migrated_tables

    # THE FILE, NOT THE DOCUMENT. Everything below compares against what
    # `_serialize` produces, so a defect introduced on the way to disk -- key
    # sorting, a tag that does not survive, a type JSON cannot hold -- is caught
    # here rather than by whoever reads the file next.
    written = json.loads(_serialize(doc))

    problems = []
    for module_name, names in sorted(GOLD_TABLES.items()):
        mod = importlib.import_module(module_name)
        for name in names:
            source = getattr(mod, name, None)
            if source is None:
                continue
            if name not in written["declarations"]:
                problems.append(f"{module_name}.{name} is not in the export")
                continue
            back = coursedata._detag(written["declarations"][name])
            # Tuples are restored by the tag. A set has no JSON form and is
            # stored as a list, so its type is restored here, from the source.
            if isinstance(source, (set, frozenset)) and isinstance(back, list):
                back = type(source)(back)
            for diff in migrated_tables.same_shape(source, back):
                problems.append(f"{module_name}.{name} does not round-trip: {diff}")
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
    open(out, "w").write(_serialize(doc))
    print(f"  written: {out} ({os.path.getsize(out):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
