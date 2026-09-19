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
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

BUILDERS = ("generator_source", "declaration_source")
READER_CALLS = {"_declaration", "_generator_table", "_generator_value",
                "_markers", "_context_refs"}


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
        if got != source:
            detail = ""
            if isinstance(got, dict) and isinstance(source, dict):
                if set(got) != set(source):
                    detail = (f" keys differ: only-read {sorted(set(got)-set(source))[:3]}, "
                              f"only-authored {sorted(set(source)-set(got))[:3]}")
                else:
                    k = next(k for k in source if got[k] != source[k])
                    detail = (f" at {k!r}: read {type(got[k]).__name__} "
                              f"{got[k]!r:.60}, authored {type(source[k]).__name__} "
                              f"{source[k]!r:.60}")
            out.append(f"{module_name}.{table} does NOT match its authored copy."
                       f"{detail}")
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
