#!/usr/bin/env python3
"""Every migrated table still equals the authored table it came from.

WHY THIS EXISTS. On 2026-09-19 three tables were moved behind ONE behavioural
test -- 26 paper prompts, which hashed identically. The test passed while
`agreement_app.CONTEXT_SOURCE`'s shape had quietly changed: its values are
tuples, JSON has no tuple, and `("section", "Q1")` came back `["section", "Q1"]`.
No paper prompt reads that table, so the test could never have caught it.

It was found by comparing the table against its authored copy -- a check done out
of habit. **This is that habit, made mechanical.** One behavioural test covering
three tables from two modules exercised one of them; a migration needs a test per
table, and this is per table by construction.

HOW THE PAIRS ARE FOUND. Not by a hand-written list, which would drift from the
migrations it describes. A migrated table is a module-level assignment whose
value is a CALL to one of the reader helpers -- `_declaration("X")`,
`_generator_table("X")`, `_generator_value("X")`, `_markers(n)`,
`_context_refs(n)` -- so the consumers are discovered by AST, and a table moved
tomorrow is covered tomorrow without editing anything here.

WHAT IT CANNOT SEE, stated rather than left to be discovered: a table read
through a wrapper this does not recognise, and a table whose authored copy has
been edited to match a bad migration. It compares the two sides; it does not
know which is right.
"""
from __future__ import annotations

import argparse
import ast
import importlib
import re
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# THE AUTHORED-TABLE MODULES, and the list of record for them: `rubric_export`
# imports this rather than keeping a second copy, so a builder added here is
# found by the exporter and by this check at once. It was two names until
# 2026-09-23, when each of those modules was split along the category seam --
# and the split is exactly what proved a hard-coded pair to be a liability:
# moving eight tables into new modules made this check report all of them as
# having "NO builder", because it was looking in the wrong two files.
BUILDERS = ("generator_source", "declaration_source",
            "course_metadata_source", "submission_markers_source")
READER_CALLS = {"_declaration", "_generator_table", "_generator_value",
                "_markers", "_context_refs"}
# `_gold_declaration` IS DELIBERATELY NOT IN THAT SET. This module proves a
# migrated table still equals its AUTHORED twin, and the twins live in the two
# BUILDERS above -- inside this repository. Gold has no such twin and must not
# grow one: a repo-resident `gold_source.py` would put participant-keyed scores
# back into a public repository, which is the whole of what C1b moved them out
# of. Adding the helper here would therefore report fifteen tables as having a
# missing source, every run, forever.
#
# What replaced the check is not nothing. The fifteen were proved equal to their
# pre-migration literals ONCE, order-sensitively, at the moment they moved; the
# export refuses to rebuild afterwards (`gold_export.unmigrated`) so that proof
# cannot be quietly invalidated; and the invariants that survive migration are
# checked in `enforcement` against the gold file itself.


# A TABLE THE READER ENRICHES, and the field it adds. `agreement.BLOCKS` is
# authored WITHOUT `refs`: that map is derived from the .olx by `_context_refs`
# and is attached on read, because storing a derived value in the course file is
# what A2a exists to prevent. The module value therefore cannot equal its
# authored copy, and without this it reported as a mismatch on all 26 entries,
# for ever.
#
# DECLARED RATHER THAN SNIFFED. "Ignore a key the module has and the source does
# not" would hide the failure this check is for -- a migration that quietly
# grew a field. The enrichment is named, with the reason, and only the named
# field is set aside.
ENRICHED = {
    ("agreement", "BLOCKS"): ("refs", "derived by `_context_refs` from the .olx; "
                                      "attached on read so the course file holds "
                                      "no derived value (A2a)"),
}


def _strip_enrichment(mod: str, name: str, value):
    """`value` with a declared enrichment field removed, at any depth of nesting."""
    field = (ENRICHED.get((mod, name)) or (None, None))[0]
    if field is None or not isinstance(value, dict):
        return value

    def strip(v):
        if isinstance(v, dict):
            return {k: strip(x) for k, x in v.items() if k != field}
        if isinstance(v, list):
            return [strip(x) for x in v]
        return v

    return strip(value)


def pairs() -> list[tuple[str, str]]:
    """[(module, table)] for every table read back through a reader helper."""
    found = []
    for fn in sorted(os.listdir(HERE)):
        if not fn.endswith(".py") or fn[:-3] in BUILDERS:
            continue
        try:
            tree = ast.parse(open(os.path.join(HERE, fn), errors="ignore").read())
        except SyntaxError:
            continue
        for node in tree.body:
            targets = (node.targets if isinstance(node, ast.Assign)
                       else [node.target] if isinstance(node, ast.AnnAssign) else [])
            name = next((t.id for t in targets if isinstance(t, ast.Name)), None)
            if not name:
                continue
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) \
                        and sub.func.id in READER_CALLS:
                    found.append((fn[:-3], name))
                    break
    return sorted(set(found))


def same_shape(a, b, path="") -> list[str]:
    """Equal AND in the same order, at every depth.

    `==` IGNORES DICT ORDER, and that is not a detail here. The export
    alphabetised every dict it wrote, `JOBS[item]["fields"]` maps component ->
    paper section IN THE ORDER THE BOXES ARE READ, and the fixture extracted
    different text as a result. This module compared with `==` throughout and
    passed -- the gate written to catch silent drift was blind to the drift.

    A scoring check found it instead. This closes the hole rather than relying on
    that happening again.
    """
    out = []
    if type(a) is not type(b):
        return [f"{path or '<root>'}: {type(a).__name__} vs {type(b).__name__}"]
    if isinstance(a, dict):
        if list(a) != list(b):
            only_a = [k for k in a if k not in b]
            only_b = [k for k in b if k not in a]
            if only_a or only_b:
                out.append(f"{path or '<root>'}: keys differ -- only-read "
                           f"{only_a[:3]}, only-authored {only_b[:3]}")
            else:
                out.append(f"{path or '<root>'}: SAME KEYS, DIFFERENT ORDER -- "
                           f"read {list(a)[:4]}, authored {list(b)[:4]}. `==` "
                           f"calls these equal; the order is the data.")
            return out
        for k in a:
            out += same_shape(a[k], b[k], f"{path}.{k}")
        return out
    if isinstance(a, (list, tuple)):
        if len(a) != len(b):
            return [f"{path}: {len(a)} entries vs {len(b)}"]
        for i, (x, y) in enumerate(zip(a, b)):
            out += same_shape(x, y, f"{path}[{i}]")
        return out
    if a != b:
        # TWO COPIES OF ONE STRING, SUBSTITUTED INDEPENDENTLY, STOP BEING
        # COMPARABLE. The history rewrite replaces a student's sentence with a
        # `{{corpus:...}}` reference wherever it appears, and the reference records
        # the WHITESPACE SHAPE of the span it replaced -- which differs between a
        # .py dict value and a JSON string holding the same sentence at a different
        # indent. Measured 2026-09-21: MULTI_BLOCK_DECLARED and ITEM_NOTES both
        # reported a mismatch at the first `shape=` suffix, `:shape=R28-0-275d}}`
        # against `}}`, with every other byte identical.
        #
        # Each substitution is individually correct and both expand to the same
        # text; only the encodings differ. So compare what they MEAN -- expand both
        # and re-test -- rather than what they spell.
        #
        # THE CHECK KEEPS ITS TEETH. Expansion is applied to BOTH sides and only
        # when a reference is present, so a genuine drift between the copies still
        # differs after expanding. This forgives a difference in encoding, not a
        # difference in content.
        if "{{corpus:" in f"{a}{b}":
            try:
                import corpus_resolve as _CR
                if _CR.expand(str(a)) == _CR.expand(str(b)):
                    return out
            except Exception:
                pass
        out.append(f"{path}: {a!r:.50} != {b!r:.50}")
    return out


# AUTHORED UNDER A NAME THE RECORDS DO NOT CARRY, deliberately. Subgoal E61.
#
# The unpaired-table scan below asks whether anything still reads each authored
# table BY NAME. A table can legitimately fail that: goal N moved the three
# marker tables off the `H1/H2/H3_MARKERS` aliases and onto a per-handout
# `markers` FIELD, which `forms.py` assembles through `_markers(h)`. The data
# migrated; the name did not survive the trip, and that was the point.
#
# Declared rather than exempted silently, so the decision stays visible -- and
# so that the day one of these is genuinely orphaned, the entry is the thing
# somebody has to delete.
AUTHORED_WITHOUT_READER: dict[str, str] = {
    "H1_MARKERS": "goal N: read as the per-handout `markers` field via "
                  "`forms._markers(h)`, not by this name",
    "H2_MARKERS": "as H1_MARKERS",
    "H3_MARKERS": "as H1_MARKERS",
}


def verify() -> list[str]:
    out = []
    builders = {}
    for b in BUILDERS:
        try:
            builders[b] = importlib.import_module(b)
        except Exception as exc:                  # pragma: no cover
            out.append(f"the builder {b} cannot be imported: {exc}")
    for module_name, table in pairs():
        try:
            mod = importlib.import_module(module_name)
        except Exception as exc:                  # pragma: no cover
            out.append(f"{module_name} cannot be imported: {exc}")
            continue
        got = getattr(mod, table, None)
        source = next((getattr(b, table) for b in builders.values()
                       if getattr(b, table, None) is not None), None)
        if source is None:
            out.append(
                f"{module_name}.{table} is read from the course file and NO "
                f"builder holds the authored copy -- so nothing can say whether "
                f"the migration was faithful")
            continue
        problems = same_shape(_strip_enrichment(module_name, table, got), source)
        if problems:
            out.append(f"{module_name}.{table} does NOT match its authored copy: "
                       f"{problems[0]}"
                       + (f" (+{len(problems) - 1} more)" if len(problems) > 1 else ""))

    # THE OTHER DIRECTION, AND IT IS THE ONE THAT WENT QUIET. Subgoal E61.
    #
    # Everything above walks the READERS and asks whether each has an authored
    # twin. An authored table that NO reader reads never enters that loop at
    # all, so it is not reported as mismatched -- it simply drops out, and
    # silence reads as agreement.
    #
    # MEASURED, 2026-09-25: the E58 identifier pass renamed `HANDOUT_FIELDS` to
    # `FORM_FIELDS` in `course_metadata_source`. The record still said
    # `HANDOUT_FIELDS`, `forms.py` still read that key, and the export still
    # named it -- the authored table and its record were completely unpaired,
    # and this function returned ZERO findings throughout.
    #
    # A builder table with no reader is not always a fault: a table may be
    # authored before anything consumes it. So it is reported as UNPAIRED
    # rather than as a mismatch, and it names both possibilities.
    # WHAT COUNTS AS READ, and the first draft of this got it wrong. `pairs()`
    # recognises a table only when a module BINDS it -- `NAME = _declaration(...)`
    # -- and several are read by NAMING them at the call site instead:
    # `forms.py` does `coursedata.declaration("HANDOUT_FIELDS")`. Counting only
    # the bound ones reported twelve healthy tables as unpaired.
    #
    # So a table is read if its NAME appears as a quoted string anywhere outside
    # the builders. That is deliberately loose: the question here is whether
    # ANYTHING still refers to it, and a rename -- the fault this exists for --
    # leaves the new name unmentioned everywhere, which this still catches.
    read = {table for _, table in pairs()}
    for fn in sorted(os.listdir(HERE)):
        if not fn.endswith(".py") or fn[:-3] in BUILDERS:
            continue
        try:
            text = open(os.path.join(HERE, fn), errors="ignore").read()
        except OSError:                           # pragma: no cover
            continue
        for quoted in re.findall(r'["\']([A-Z][A-Z0-9_]{2,})["\']', text):
            read.add(quoted)
    for name, mod in builders.items():
        for attr in sorted(vars(mod)):
            if attr.startswith("_") or not attr.isupper() or attr in read:
                continue
            if attr in AUTHORED_WITHOUT_READER:
                continue
            value = getattr(mod, attr)
            if not isinstance(value, (dict, list, tuple, set, frozenset)):
                continue
            out.append(
                f"{name}.{attr} is AUTHORED and nothing reads it back from the "
                f"course file. Either the migration has not happened yet, or the "
                f"reader names it differently -- which is how a renamed table "
                f"stops being compared to its record without anything saying so")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.parse_args(argv)
    found = pairs()
    bad = verify()
    by_mod: dict[str, int] = {}
    for m, _t in found:
        by_mod[m] = by_mod.get(m, 0) + 1
    print(f"  {len(found)} migrated table(s) across {len(by_mod)} module(s)")
    for m, n in sorted(by_mod.items()):
        print(f"    {m:<20} {n}")
    if bad:
        print(f"\n  {len(bad)} MISMATCH(ES):")
        for b in bad:
            print(f"    {b}")
        return 1
    print("  every migrated table equals the authored table it came from.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
