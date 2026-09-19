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
import ast
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

SCHEMA_VERSION = 3

# module -> the gold declarations it holds. Named rather than discovered: a
# table's being about gold is a judgement, and `GOLD` in the name is a
# convention, not a guarantee -- `DECLARED_CEILING_CELLS` and
# `CONSENSUS_OVERLAP_BACKLOG` carry participants and say nothing about gold in
# their names, while a table could be called GOLD_* and hold none.
GOLD_TABLES = {
    "handouts": ("CORRECTED_GOLD", "GOLD_DIVERGENCES", "GOLD_CEILINGS",
                 "PER_ITEM_EXCLUDE"),
    # GOLD_CODE_CHARGES is here because it is gold's VOCABULARY: it maps the
    # phrases the graders wrote in their workbook comments to the codes we
    # charge against. The phrases are quoted from the marked-up sheets, so they
    # are as much a product of the submissions as the scores are.
    "measured": ("GOLD_CODE_CHARGES", "GOLD_SLOT_CHARGES", "GOLD_CODE_KNOWN",
                 "GOLD_SLOT_BOUNDS_KNOWN", "GOLD_SLOT_UNMAPPABLE",
                 "GOLD_SLOT_DISAGREEMENTS_KNOWN", "SILENT_GOLD_DIVERGENCES",
                 "DECLARED_CEILING_CELLS", "_1C_GATE_CEILING"),
    # `GRAPH_UNREACHABLE_1C` IS NOT HERE, and that is A2a rather than an
    # oversight: it is the sorted participant list of PER_ITEM_EXCLUDE's own
    # first-item entry, derived from a
    # table that IS carried. Exporting it too would put the same fact in the file
    # twice, where an edit to one copy makes the other silently wrong -- and the
    # reader rebuilds it for free the moment `PER_ITEM_EXCLUDE` is read.
    "agreement": ("UNSCORED_GOLD_CRITERIA",),
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
           "handout_participants": {}, "declaration_notes": {}}
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
    doc["declaration_notes"] = interior_notes()
    return doc



# ---------------------------------------------------------------------------
# THE REASONING, NOT JUST THE NUMBERS.
#
# These tables carried 707 comment lines INSIDE them -- one run against each
# entry it judged, recording what was measured to settle that cell: hypotheses
# that died, call counts, probe verdicts. That is the expensive half of the
# record, and it is course-specific gold reasoning, so it belongs with the
# course data rather than in this public repository.
#
# Attribution is by SPAN, not by adjacency: a comment is assigned to the entry
# whose value encloses it, because these entries are multi-line dicts whose
# comments sit inside the value they judge. Attributing by "the run immediately
# before an entry" lost 333 of the 707 on the first attempt, which is why the
# total is asserted below rather than eyeballed.
# ---------------------------------------------------------------------------
def keyrepr(node):
    """The entry key as the exported file holds it: a list for a tuple, else scalar.

    `except Exception: return None` WAS HERE, and it turned a missing module-level
    `import ast` into "every one of these fifteen keys is unreadable". All fifteen
    then collided on the same `null` bucket and the survivor held nothing. The
    total-lines assertion caught the damage, but it reported 42-of-64 -- a
    plausible-looking shortfall -- while the actual fault was a NameError being
    swallowed two frames down. Catch only what `literal_eval` raises for a
    non-literal key; anything else is a bug here and should say so.
    """
    try:
        v = ast.literal_eval(node)
    except (ValueError, SyntaxError, TypeError):
        return None
    return list(v) if isinstance(v, tuple) else v

def comments_in(lines, lo, hi):
    """Every comment line in [lo, hi), de-indented. NOTHING IS DROPPED.

    An earlier version reset the run whenever CODE appeared between comments, on
    the theory that a comment separated from an entry by code belongs to the
    code. That lost 333 of 707 lines: these tables' entries are multi-line dicts
    whose comments sit INSIDE the value, judging the very entry they are nested
    in. A comment is attributed to the entry whose span contains it, and the
    total is asserted, so the question "did any go missing" is answered by
    counting rather than by reading.
    """
    out = []
    for l in lines[lo:hi]:
        s = l.strip()
        if s.startswith("#"):
            out.append(s[1:].lstrip() if s[1:].strip() else "")
    return out



def interior_notes() -> dict:
    """Each gold table's interior comments, keyed by the entry they judge."""
    import ast
    import importlib.util

    notes, counts = {}, {}
    for mod, names in GOLD_TABLES.items():
        path = importlib.util.find_spec(mod).origin
        lines = open(path).read().splitlines()
        tree = ast.parse("\n".join(lines))
        for node in tree.body:
            tgt = (node.targets[0].id if isinstance(node, ast.Assign)
                   and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) else
                   node.target.id if isinstance(node, ast.AnnAssign)
                   and isinstance(node.target, ast.Name) else None)
            if tgt not in names:
                continue
            v, per, cursor = node.value, {}, node.lineno
            if isinstance(v, ast.Dict):
                entries = list(zip(v.keys, v.values))
            elif isinstance(v, (ast.List, ast.Tuple, ast.Set)):
                entries = [(e, e) for e in v.elts]
            else:
                entries = []
            for i, (k, val) in enumerate(entries):
                run = comments_in(lines, cursor, val.end_lineno)
                if run:
                    kk = keyrepr(k) if isinstance(v, ast.Dict) else i
                    if kk is None:
                        raise SystemExit(
                            f"gold_export: {mod}.{tgt} has an entry key this tool "
                            f"cannot read ({ast.unparse(k)!r}). Its notes have "
                            f"nowhere to go, so the export stops rather than "
                            f"quietly dropping them.")
                    slot = json.dumps(kk)
                    if slot in per:
                        raise SystemExit(
                            f"gold_export: {mod}.{tgt} has two entries keyed "
                            f"{slot} -- the second would overwrite the first's "
                            f"notes. This is how 64 lines became 0 once already.")
                    per[slot] = run
                cursor = val.end_lineno
            trailing = comments_in(lines, cursor, node.end_lineno)
            if trailing:
                per["__trailing__"] = trailing
            had = sum(1 for l in lines[node.lineno - 1:node.end_lineno]
                      if l.strip().startswith("#"))
            got = sum(len(r) for r in per.values())
            if had != got:
                raise SystemExit(
                    f"gold_export: REFUSING -- {mod}.{tgt} has {had} interior "
                    f"comment lines and only {got} were lifted. The reasoning is "
                    f"the expensive half of this record; it does not get dropped "
                    f"on the way out.")
            if per:
                notes[tgt] = per
                counts[tgt] = got
    return notes


def unmigrated() -> list[str]:
    """Tables still held as module-level literals -- the ones this tool can read.

    THE GUARD THAT STOPS THIS TOOL EATING ITS OWN OUTPUT. Once a table is
    migrated it reads `_gold_declaration(...)`, so `getattr` returns what the
    GOLD FILE holds and the interior comments are gone from the source. A
    rebuild in that state would compare the file to itself -- passing
    trivially -- and write back a document with no notes in it, silently
    deleting the 707 lines this function exists to carry. So a rebuild is
    refused unless every table is still a literal.
    """
    import ast
    import importlib.util

    still = []
    for mod, names in GOLD_TABLES.items():
        tree = ast.parse(open(importlib.util.find_spec(mod).origin).read())
        for node in tree.body:
            tgt = (node.targets[0].id if isinstance(node, ast.Assign)
                   and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) else
                   node.target.id if isinstance(node, ast.AnnAssign)
                   and isinstance(node.target, ast.Name) else None)
            if tgt in names and not any(isinstance(n, ast.Call) for n in ast.walk(node.value)):
                still.append(f"{mod}.{tgt}")
    return still


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


def add_one(spec: str, out: str | None, dry_run: bool) -> int:
    """Merge ONE table into the gold file, without rebuilding the rest.

    The rebuild guard is right and this is why it needs a companion. A table
    that is STILL a literal has never been exported, so there is nothing
    circular about reading it -- but a full rebuild would also re-read the
    fifteen that have migrated, find nothing in them, and write the file back
    empty. This does the one table and leaves the others exactly as they are.

    EXACTLY AS THEY ARE, asserted by comparing the serialized form of every
    other table before and after. A merge that quietly reformatted a neighbour
    would be indistinguishable from the rebuild the guard exists to prevent.
    """
    import importlib

    mod_name, _, table = spec.partition(".")
    if not table:
        raise SystemExit(f"gold_export: --add wants MODULE.TABLE, got {spec!r}")
    if table not in GOLD_TABLES.get(mod_name, ()):
        raise SystemExit(
            f"gold_export: {spec} is not declared in GOLD_TABLES. A table is "
            f"added to that registry first, so that what counts as gold is a "
            f"decision recorded in one place rather than a command-line "
            f"argument.")
    if spec not in unmigrated():
        raise SystemExit(
            f"gold_export: {spec} is not a literal in {mod_name}.py -- either it "
            f"has already migrated, or it is computed. Nothing to extract.")

    path = out or default_path()
    if not path or not os.path.exists(path):
        raise SystemExit(f"gold_export: no gold file at {path} to merge into.")
    doc = json.loads(open(path).read())
    before = {k: json.dumps(v) for k, v in doc["declarations"].items()}

    value = getattr(importlib.import_module(mod_name), table)
    doc["declarations"][table] = _jsonable(value)
    per = interior_notes().get(table)
    if per:
        doc.setdefault("declaration_notes", {})[table] = per

    # the neighbours, unchanged
    after = {k: json.dumps(v) for k, v in doc["declarations"].items() if k != table}
    changed = [k for k in before if k != table and before[k] != after.get(k)]
    if changed:
        raise SystemExit(f"gold_export: REFUSING -- merging {spec} would change "
                         f"{len(changed)} other table(s): {changed[:4]}")
    # and the new one round-trips, through the reader, order-sensitively
    import coursedata
    import migrated_tables
    back = coursedata._detag(json.loads(_serialize(doc))["declarations"][table])
    if isinstance(value, (set, frozenset)) and isinstance(back, list):
        back = type(value)(back)
    diffs = migrated_tables.same_shape(value, back)
    if diffs:
        raise SystemExit(f"gold_export: {spec} does not round-trip: {diffs[0]}")

    n = len(per) if per else 0
    if dry_run:
        print(f"  would add {spec}: {len(before) + 1} tables, {n} annotated entries")
        return 0
    open(path, "w").write(_serialize(doc))
    print(f"  added {spec} to {path} ({len(before) + 1} tables, "
          f"{n} annotated entries); {len(before)} others byte-identical")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=None,
                    help="where to write; defaults to $COURSE_DATA/courses/<id>/")
    ap.add_argument("--dry-run", action="store_true",
                    help="build and verify, write nothing")
    ap.add_argument("--add", metavar="MODULE.TABLE", default=None,
                    help="merge ONE still-literal table into the existing gold "
                         "file, leaving every other table byte-identical")
    args = ap.parse_args(argv)

    if args.add:
        return add_one(args.add, args.out, args.dry_run)

    doc = build()
    # THE REBUILD GUARD, and it fires from here rather than from `build()` so
    # that `--dry-run` refuses too. Once the tables are migrated this tool can no
    # longer see what it exports: `getattr` returns what the GOLD FILE holds, so
    # `round_trip` would compare the file to itself and pass trivially, and
    # `interior_notes` would find no comments and write a document with the 707
    # lines deleted. A tool that cannot tell success from having nothing left to
    # read must not be allowed to overwrite its own output.
    still = unmigrated()
    if len(still) != sum(len(v) for v in GOLD_TABLES.values()):
        migrated = sum(len(v) for v in GOLD_TABLES.values()) - len(still)
        raise SystemExit(
            f"gold_export: REFUSING to rebuild. {migrated} of "
            f"{sum(len(v) for v in GOLD_TABLES.values())} tables have already "
            f"migrated and no longer hold their entries in the source, so a "
            f"rebuild would write back a file missing them and their notes. "
            f"This tool EXTRACTED gold once; the gold file is the authored source "
            f"now, and it is edited directly.")

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
