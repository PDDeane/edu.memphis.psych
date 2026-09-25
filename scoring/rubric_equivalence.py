#!/usr/bin/env python3
"""Prove the course JSON reproduces the rubric modules, while they are still the oracle.

T5.1. The rubric modules are deleted at Stage 5, and the last run of this tool is
what licenses removing them. Until then they are the truth and this file is the
copy.

IT DOES NOT READ THROUGH `coursedata.py`, AND THAT IS THE POINT. T3.2 compares the
READER against the modules; this compares the DATA against the modules. A reader
bug and an export bug produce the same symptom, and only two independent proofs
separate them -- so loading the JSON through the reader here would make both tools
fail identically on a reader bug and hide the very thing the second proof exists to
isolate. (The first draft of this design specified exactly that, which is the same
class of error as an accessor returning a raw entry: a stated boundary and an
implementation that quietly disagree.)

DEEP EQUALITY IS IMPOSSIBLE AND ITS ABSENCE IS NOT A DEFECT. A2a removes derived
values on purpose, so the modules carry fields the file does not. A blanket
equality assertion would fail on every item for a designed reason. The scopes are
therefore split and do not overlap:

    T5.1 -- the AUTHORED fields, JSON against modules, directly
    T3.2 -- the DERIVED values, through the reader, where the rules live

Between them every field is proved once, by the tool that can prove it without
borrowing the thing under test.

MEASURED 2026-09-18: 2 of 18 candidates are derivable (`BY_ID`, `TOTAL`); the rest
are authored literals. So "the authored fields" is very nearly everything, and this
tool carries almost the whole proof.
"""
from __future__ import annotations

import argparse
import json
import os

import paths
import sys
import handouts as _handouts   # forms are declared by the course, not counted here

HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUTS = _handouts.declared()

# Rebuilt by the reader rather than stored, so their absence from the file is
# correct. Named here INDEPENDENTLY of the reader: this tool must not import the
# thing it is proving the file against.
DERIVED_BY_DESIGN = {"BY_ID", "TOTAL"}

# Fields on an item entry that are AUTHORED SOMEWHERE ELSE. Stage 4 folded
# `olx_prompts`' item-keyed tables onto the item entries as generator fields, so
# a field like `prompt_action` is in the file, is correct, and is not in any
# rubric module -- and this tool reported 82 of them as "ONLY IN FILE".
#
# The claim being proved is "the file reproduces the AUTHORED modules", and since
# Stage 4 the authored modules include the builders. So those fields are checked
# against `generator_source` instead of being called extra.
#
# Named by prefix rather than by importing `coursedata.GENERATOR_FIELDS`, which
# would make this proof borrow the reader it exists to be independent of.
GENERATOR_PREFIX = "prompt_"
GENERATOR_BUILDER = "generator_source"
# builder table -> the item field the export writes it to
GENERATOR_FIELD_OF = {
    "ACTION": "prompt_action", "RESPONSE": "prompt_response",
    "CONTEXT": "prompt_context", "SHEET_ONLY": "prompt_sheet_only",
    "EVIDENCE": "prompt_evidence", "OMIT_GUIDANCE": "prompt_omit_guidance",
    "MATCH_DEF": "prompt_match_def", "ITEM_NOTES": "prompt_notes",
    "ITEM_NOTES_WHY": "prompt_notes_why",
}


def _detag(x):
    """Undo the export's tuple tagging: `{"__tuple__": [...]}` -> a tuple.

    THIS IS FORMAT DECODING, NOT BORROWING THE READER. The file stores a tuple
    tagged, because JSON has none, and a tool that reads the file DIRECTLY has to
    understand the file's format -- that is not the same as reading through
    `coursedata`, which is what this proof must not do. Implemented here rather
    than imported, for the reason the canonicaliser is: a decoding bug shared
    between the two sides would cancel out in both.
    """
    if isinstance(x, dict):
        if set(x) == {"__tuple__"}:
            return tuple(_detag(v) for v in x["__tuple__"])
        return {k: _detag(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_detag(v) for v in x]
    return x


def _canonical(x):
    """T2.1's pinned form: sorted keys within an entry, lists in place."""
    if isinstance(x, dict):
        return {str(k): _canonical(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    if isinstance(x, (list, tuple)):
        return [_canonical(v) for v in x]
    return x


def _diff(a, b, path="") -> list[str]:
    """Every difference, with its path. Not a bool: 'they differ' is unactionable."""
    out = []
    if type(a) is not type(b) and not (isinstance(a, (int, float))
                                       and isinstance(b, (int, float))):
        return [f"{path or '<root>'}: module has {type(a).__name__}, "
                f"file has {type(b).__name__}"]
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b), key=str):
            if k not in a:
                out.append(f"{path}.{k}: ONLY IN FILE")
            elif k not in b:
                out.append(f"{path}.{k}: ONLY IN MODULE -- the export lost it")
            else:
                out += _diff(a[k], b[k], f"{path}.{k}")
    elif isinstance(a, list):
        if len(a) != len(b):
            out.append(f"{path}: module has {len(a)} entries, file has {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            out += _diff(x, y, f"{path}[{i}]")
    elif a != b:
        out.append(f"{path}: module {a!r:.60} != file {b!r:.60}")
    return out


def compare(course_file: str) -> tuple[list[str], dict]:
    sys.path.insert(0, HERE)
    doc = _detag(json.load(open(course_file)))  # DIRECT. No reader.
    by_id = {str(it["id"]): it for it in doc.get("items", [])}
    problems, counts = [], {"items": 0, "fields": 0, "authored_values": 0}

    # ONLY THE HANDOUTS THAT STILL HAVE A MODULE. Stage 5 deletes h1 and h3 and
    # KEEPS h2, whose four builders A1c preserves -- so "all gone" and "all
    # present" are both easier than the state this actually lands in. Checking
    # for a total absence and otherwise iterating (1, 2, 3) crashed on exactly
    # the configuration Stage 5 produces.
    for h in _modules_present():
        mod = __import__(f"rubric_h{h}")
        for it in list(getattr(mod, "ITEMS", []) or []):
            iid = str(it["id"])
            counts["items"] += 1
            if iid not in by_id:
                problems.append(f"item {iid}: IN MODULE, ABSENT FROM FILE")
                continue
            want = _canonical(it)
            entry = _canonical(by_id[iid])
            got = {k: v for k, v in entry.items()
                   if k != "handout" and not k.startswith(GENERATOR_PREFIX)}
            counts["fields"] += len(want)
            problems += _diff(want, got, f"item {iid}")

            # the generator fields, against the BUILDER that authored them
            builder = __import__(GENERATOR_BUILDER)
            for table, field in sorted(GENERATOR_FIELD_OF.items()):
                authored = (getattr(builder, table, None) or {}).get(iid)
                stored = entry.get(field)
                if authored is None and stored is None:
                    continue
                counts["generator_fields"] = counts.get("generator_fields", 0) + 1
                if authored is None:
                    problems.append(
                        f"item {iid}.{field}: in the file and {table} does not "
                        f"name this item -- a generator field with no author")
                elif stored is None:
                    problems.append(
                        f"item {iid}.{field}: {table} names this item and the "
                        f"file does not carry it -- the export lost it")
                else:
                    problems += _diff(_canonical(authored), _canonical(stored),
                                      f"item {iid}.{field}")

        # the module-level authored values the export carried
        block = doc.get("handouts", {}).get(str(h), {}).get("authored", {})
        exports = {n: getattr(mod, n) for n in dir(mod)
                   if n.isupper() and not n.startswith("_") and n != "ITEMS"}
        for name, value in sorted(exports.items()):
            if name in DERIVED_BY_DESIGN:
                if name in block:
                    problems.append(f"h{h} {name}: stored in the file although it is "
                                    f"rebuilt by the reader -- A2a says do not store it")
                continue
            counts["authored_values"] += 1
            if name not in block:
                problems.append(f"h{h} {name}: IN MODULE, ABSENT FROM FILE -- "
                                f"neither carried nor derivable")
                continue
            problems += _diff(_canonical(value), _canonical(block[name]), f"h{h}.{name}")

    # The reverse direction over the modules that remain: an id the file holds
    # and no SURVIVING module does is only a finding if every module survives.
    extra = set(by_id) - {str(it["id"]) for h in _modules_present()
                          for it in (getattr(__import__(f"rubric_h{h}"), "ITEMS", []) or [])}
    if len(_modules_present()) < 3:
        extra = set()
    for iid in sorted(extra):
        problems.append(f"item {iid}: IN FILE, ABSENT FROM MODULES")
    return problems, counts


def _modules_present() -> list:
    """Which rubric modules still exist. Stage 5 deletes h1 and h3.

    T5.1 compares the course file against the MODULES, so once they are gone
    it has no oracle and cannot run. It used to find that out as a
    ModuleNotFoundError traceback; the last run that still had an oracle is
    recorded in STAGE5_LICENCE.md, and that record is what licenses the
    deletion. Saying so is the difference between a retired tool and a broken
    one.
    """
    import os

    here = os.path.dirname(os.path.abspath(__file__))
    return [h for h in _handouts.declared()
            if os.path.exists(os.path.join(here, f"rubric_h{h}.py"))]


def main(argv: list[str]) -> int:
    if not _modules_present():
        print("  the rubric modules are gone, so this tool has no oracle to "
              "compare against.\n  Its last run with one is recorded in "
              "STAGE5_LICENCE.md, and that run is what\n  licensed removing "
              "them. Nothing to do.")
        return 0

    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--course-file", default=str(paths.COURSE_FILE))
    args = ap.parse_args(argv)

    if not os.path.exists(args.course_file):
        print(f"  REFUSING: no course file at {args.course_file}. A missing file is "
              f"not an equivalent one.")
        return 2

    problems, counts = compare(args.course_file)
    print(f"  compared {counts['items']} items, {counts['fields']} item fields, "
          f"{counts.get('generator_fields', 0)} generator fields, "
          f"{counts['authored_values']} module-level authored values")
    if not problems:
        print("  EQUIVALENT — the file reproduces the modules on every authored field.")
        print("  (Derived values are T3.2's, through the reader: "
              f"{sorted(DERIVED_BY_DESIGN)})")
        return 0
    print(f"  {len(problems)} DIFFERENCE(S):")
    for p in problems[:40]:
        print(f"    {p}")
    if len(problems) > 40:
        print(f"    ... and {len(problems) - 40} more")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
