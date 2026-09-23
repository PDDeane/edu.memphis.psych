#!/usr/bin/env python3
"""T2.2 — every item field belongs to a declared group, and no module crosses the boundary.

§9.2a sets three obligations. Obligation 2 (accessors expose each group
separately) belongs to `coursedata` itself, which cannot gate itself. This
carries obligations 1 and 3; obligation 3 had been assigned to nothing, and **a
rule with no tool is a comment.**

PART A — the declaration, reported in BOTH directions and NOT merged.
  * an item field that NO group names is a VIOLATION. §9.2a says a new field
    naming no group fails validation rather than defaulting to one.
  * a group naming a field that does not exist is a CLEANUP. Reported
    separately and not a failure by itself.
They are kept apart because they mean different things, and merging them lets a
real violation hide in a list of tidying.

PART B — the boundary. No module may read a GENERATOR field off a rubric result,
or a RUBRIC field off a generator result, and none may take a raw item entry from
anything but an accessor. **The raw-entry escape is the one to watch**: it
defeats the boundary while appearing to honour it, because the code still calls
into `coursedata`.

WHY IT SHIPS WITH ITS OWN CASES. At Stage 2 there are no GENERATOR fields, so
Part A is satisfied by tagging everything RUBRIC and **the check passes while
proving nothing** until Stage 4. A check whose first real exercise is two stages
away is one nobody has watched fail, so the four conditions are constructed here
and injected -- none depends on the tree happening to contain an example, which
is how the neutrality case became vacuous.
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

SCHEMA_VERSION = 1

# The accessors, and which group each hands back.
ACCESSORS = {"items": "rubric", "rubric_for": "rubric", "generator_for": "generator"}

# Names inside `coursedata` that hand out a RAW entry -- the whole dict, before
# `_group` narrows it. Reaching one from outside defeats the boundary.
RAW_ENTRY = {"_load", "_DOC", "_group"}

EXEMPT_MODULES = {
    "coursedata.py": "the reader IS the boundary; it must touch both groups",
    "course_schema.py": "this module names the accessors in order to find them",
    "rubric_export.py": "the export reads whole entries by design, before the "
                        "groups exist to narrow them",
}


def groups() -> dict[str, set[str]]:
    import coursedata

    return {"rubric": set(coursedata.RUBRIC_FIELDS),
            "generator": set(coursedata.GENERATOR_FIELDS)}


def part_a(entries: list[dict], declared: dict[str, set[str]]) -> tuple[list, list]:
    """-> (violations, cleanups). Two lists, never one."""
    known = declared["rubric"] | declared["generator"]
    present: set[str] = set()
    for e in entries:
        present |= set(e)
    violations = [
        f"item field {f!r} belongs to no declared group. §9.2a: a field naming no "
        f"group FAILS rather than defaulting -- add it to RUBRIC_FIELDS or "
        f"GENERATOR_FIELDS, whichever the engine actually reads it through"
        for f in sorted(present - known)]
    cleanups = [
        f"{f!r} is declared in {'RUBRIC' if f in declared['rubric'] else 'GENERATOR'}"
        f"_FIELDS and appears on no item -- stale, not a violation"
        for f in sorted(known - present)]
    return violations, cleanups


def _accessor_of(node: ast.AST) -> str | None:
    """If this expression is an accessor CALL, which group does it return?"""
    if not isinstance(node, ast.Call):
        return None
    fn = node.func
    name = fn.attr if isinstance(fn, ast.Attribute) else (
        fn.id if isinstance(fn, ast.Name) else None)
    return ACCESSORS.get(name)


def part_b(directory: str, declared: dict[str, set[str]]) -> list[str]:
    """Boundary crossings, by AST. Direct and one-hop-through-a-local."""
    out = []
    other = {"rubric": "generator", "generator": "rubric"}
    for fn in sorted(os.listdir(directory)):
        if not fn.endswith(".py") or fn in EXEMPT_MODULES:
            continue
        try:
            tree = ast.parse(open(os.path.join(directory, fn), errors="ignore").read())
        except SyntaxError:
            continue

        # raw entry taken from outside the reader
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr in RAW_ENTRY:
                base = node.value
                if isinstance(base, ast.Name) and base.id in ("coursedata", "cd", "C"):
                    out.append(
                        f"{fn}: takes a RAW item entry via {base.id}.{node.attr} -- "
                        f"that is the whole dict before either group narrows it, so "
                        f"the boundary is defeated while the code still calls into "
                        f"the reader. Use items()/rubric_for()/generator_for().")

        # a subscript on an accessor call, or on a local holding one
        for fnode in [n for n in ast.walk(tree)
                      if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                                        ast.Module))]:
            holds: dict[str, str] = {}
            for node in ast.walk(fnode):
                if isinstance(node, ast.Assign) and len(node.targets) == 1:
                    tgt = node.targets[0]
                    grp = _accessor_of(node.value)
                    if isinstance(tgt, ast.Name) and grp:
                        holds[tgt.id] = grp
                if isinstance(node, ast.Subscript) and isinstance(
                        node.slice, ast.Constant) and isinstance(node.slice.value, str):
                    field = node.slice.value
                    grp = _accessor_of(node.value)
                    if grp is None and isinstance(node.value, ast.Name):
                        grp = holds.get(node.value.id)
                    if grp and field in declared[other[grp]]:
                        out.append(
                            f"{fn}:{getattr(node, 'lineno', 0)} reads {field!r}, a "
                            f"{other[grp].upper()} field, off a {grp.upper()} "
                            f"result. Use {('generator_for' if other[grp] == 'generator' else 'rubric_for')}"
                            f"(), or declare {field!r} in the group the engine "
                            f"actually reads it through.")
    return out


def gold_check() -> list[str]:
    """Gold is in scope. A missing data root is an ALARM, not a skip."""
    import coursedata

    root = coursedata.data_root()
    if not root or not os.path.isdir(root):
        return [f"$COURSE_DATA is unset or absent ({root!r}), so GOLD COULD NOT BE "
                f"VALIDATED. A check that cannot run is not a check that passed, "
                f"and scoring without the gold data is not a state to proceed "
                f"quietly from."]
    path = coursedata.gold_path()
    if not os.path.exists(path):
        # C1b's export has not run yet. Reported, not failed: the file is
        # SCHEDULED, and failing here would gate Stage 2 on Stage 5's work.
        return []
    try:
        doc = json.load(open(path))
    except ValueError as exc:
        return [f"gold at {path} is not readable JSON: {exc}"]
    if not isinstance(doc, dict):
        return [f"gold at {path} is {type(doc).__name__}, expected an object"]
    return []


def check(directory: str | None = None) -> dict:
    import coursedata

    directory = directory or HERE
    declared = groups()
    # BOTH SIDES OF THE SPLIT, since 3d. The rubric fields left `course.json`
    # when the rubric became a component, so `items[]` alone no longer shows
    # where a declared field lives -- comparing against it would have reported
    # all 28 rubric names as stale declarations, which is the opposite of true.
    # `coursedata.items()` serves the component's rows and `_load()["items"]`
    # the generator's, and a field declared in neither really is stale.
    entries = list(coursedata._load()["items"]) + list(coursedata.items())
    violations, cleanups = part_a(entries, declared)
    return {"violations": violations + part_b(directory, declared) + gold_check(),
            "cleanups": cleanups,
            "fields_declared": sum(len(v) for v in declared.values()),
            "generator_fields": len(declared["generator"])}


def self_test() -> int:
    """Four conditions, each constructed here and injected. See the docstring."""
    import textwrap

    import coursedata

    print("  %-52s %s" % ("induced", "result"))
    ok = 0
    cases = []

    def note(name, good, detail=""):
        nonlocal ok
        ok += bool(good)
        cases.append(name)
        print("  %-52s %s  %s" % (name, "caught" if good else "MISSED", detail[:40]))

    declared = groups()

    # 1 a field in NEITHER group
    v, c = part_a([{"id": "X", "not_in_any_group": 1}], declared)
    note("a field in neither group -> VIOLATION",
         any("not_in_any_group" in x for x in v), v[0] if v else "")

    # 2 a declared member that does not exist -> cleanup, and NOT a violation
    v2, c2 = part_a([{"id": "X"}], {"rubric": {"id", "ghost_field"}, "generator": set()})
    note("a declared field nothing has -> CLEANUP only",
         any("ghost_field" in x for x in c2) and not any("ghost_field" in x for x in v2),
         c2[0] if c2 else "")

    # 3 and 4 need a module on disk; write one, scan, remove it
    probe = os.path.join(HERE, "_t22_probe.py")
    src = textwrap.dedent('''
        import coursedata
        def a(i):
            r = coursedata.rubric_for(i)
            return r["GEN_ONLY"]
        def b(i):
            return coursedata._load()["items"]
    ''')
    open(probe, "w").write(src)
    try:
        d = {"rubric": {"id"}, "generator": {"GEN_ONLY"}}
        found = part_b(HERE, d)
        mine = [x for x in found if "_t22_probe.py" in x]
        note("a GENERATOR field read off a rubric result",
             any("GEN_ONLY" in x for x in mine),
             next((x for x in mine if "GEN_ONLY" in x), ""))
        note("a RAW entry taken from outside the reader",
             any("RAW item entry" in x for x in mine),
             next((x for x in mine if "RAW" in x), ""))
    finally:
        os.unlink(probe)

    print(f"\n  {ok}/{len(cases)} conditions behave as designed")
    return 0 if ok == len(cases) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", default=HERE)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()

    got = check(args.dir)
    print(f"  {got['fields_declared']} fields declared "
          f"({got['generator_fields']} generator), "
          f"{len(got['violations'])} violation(s), {len(got['cleanups'])} cleanup(s)")
    if got["generator_fields"] == 0:
        print("  NOTE: GENERATOR_FIELDS is empty, so Part A cannot yet fail on real "
              "data and Part B has no cross-group field to find. The self-test is "
              "what exercises this check until Stage 4.")
    for c in got["cleanups"]:
        print(f"    cleanup: {c}")
    for v in got["violations"]:
        print(f"    VIOLATION: {v}")
    return 1 if got["violations"] else 0


if __name__ == "__main__":
    sys.exit(main())
