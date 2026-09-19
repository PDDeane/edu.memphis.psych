#!/usr/bin/env python3
"""Would a migration of this table be NOTICED if it went wrong?

THE TEST A MOVE NEEDS BEFORE IT HAPPENS, not after. Three tables migrated on
2026-09-19 each had a decisive equivalence test -- 23 prompts hashing the same,
60 submissions segmenting the same, `BLOCKS` reassembling the same. The thirteen
declaration tables in `enforcement.py` have no such test: they feed enforcement
checks, the audit returns 4 findings, and **a table silently emptied produces the
same 4 findings wherever the checks it feeds already pass**.

That is T0.1's vacancy problem one level up. 4 findings cannot distinguish 13
faithful moves from 13 losses.

SO THIS MEASURES SENSITIVITY. For each table it empties the table, re-runs only
the checks that CONSUME it, and reports whether any of them moved. A table whose
emptying changes nothing cannot be migrated safely by this route -- not because
the migration would be wrong, but because nothing would tell us if it were.

WHAT A "NOT SENSITIVE" RESULT MEANS, and it is not one thing:

  * the table may be genuinely inert -- its entries all describe conditions that
    no longer arise, in which case the table is a candidate for deletion rather
    than migration;
  * or the checks that read it may be passing for unrelated reasons, in which
    case the table is load-bearing and the CHECK is the weak instrument.

The report does not guess between them. It says which checks were exercised and
what they returned, so the difference can be read.

IT DOES NOT RUN `check_engines_send_the_same_request`, which caches a 672 KB
capture under `$COURSE_DATA/out`. Nothing here is worth a write outside the tree
being worked on.
"""
from __future__ import annotations

import argparse
import ast
import copy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

WRITES_OUTSIDE = {"check_engines_send_the_same_request"}


def consumers(tables: list[str]) -> dict[str, list[str]]:
    """{table: [checks that reach it]}, DIRECTLY or through one helper.

    ONE HOP, BECAUSE DIRECT REFERENCE WAS NOT ENOUGH. The first version looked
    only inside each `check_*` body and reported `SLOT_STRUCTURE_FAMILIES` and
    `PROBE_PROVOCATIONS` as read by NO check -- both are read by module-level
    HELPERS that checks call, and both are registered with the table watcher.
    "No consumer" would have been a false finding about two live tables, and the
    kind that reads as a discovery.

    Still bounded at one hop, and that bound is stated rather than hidden: a
    table reached through two helpers is invisible here and would be reported as
    unconsumed.
    """
    tree = ast.parse(open(os.path.join(HERE, "enforcement.py")).read())
    funcs = {fn.name: fn for fn in tree.body if isinstance(fn, ast.FunctionDef)}

    def names_in(fn):
        return {n.id for n in ast.walk(fn) if isinstance(n, ast.Name)}

    def calls_in(fn):
        out = set()
        for n in ast.walk(fn):
            if isinstance(n, ast.Call):
                f = n.func
                if isinstance(f, ast.Name):
                    out.add(f.id)
                elif isinstance(f, ast.Attribute):
                    out.add(f.attr)
        return out

    reads = {name: names_in(fn) for name, fn in funcs.items()}
    out: dict[str, list[str]] = {t: [] for t in tables}
    for name, fn in funcs.items():
        if not name.startswith("check_") or name in WRITES_OUTSIDE:
            continue
        reachable = set(reads[name])
        for helper in calls_in(fn) & set(funcs):
            reachable |= reads[helper]
        for t in tables:
            if t in reachable:
                out[t].append(name)
    return out


def _empty_like(value):
    """An empty value of the same shape -- the loss a bad migration would cause."""
    if isinstance(value, dict):
        return {}
    if isinstance(value, (list, set)):
        return type(value)()
    if isinstance(value, tuple):
        return ()
    return None


def sensitivity(tables: list[str]) -> list[dict]:
    import enforcement as ENF

    rows = []
    mapping = consumers(tables)
    for table in tables:
        checks = mapping.get(table) or []
        original = getattr(ENF, table, None)
        if original is None:
            rows.append({"table": table, "checks": [], "sensitive": False,
                         "note": "not defined"})
            continue
        before = {}
        for name in checks:
            try:
                before[name] = len(getattr(ENF, name)())
            except Exception as exc:
                before[name] = f"<{type(exc).__name__}>"
        setattr(ENF, table, _empty_like(original))
        try:
            after = {}
            for name in checks:
                try:
                    after[name] = len(getattr(ENF, name)())
                except Exception as exc:
                    after[name] = f"<{type(exc).__name__}>"
        finally:
            setattr(ENF, table, original)
        moved = sorted(n for n in checks if before.get(n) != after.get(n))
        rows.append({"table": table, "entries": len(original) if hasattr(original, "__len__") else None,
                     "checks": checks, "moved": moved,
                     "sensitive": bool(moved),
                     "before": before, "after": after})
    return rows


DEFAULT_TABLES = ["PROSE_ONLY_SLOTS", "PROSE_ONLY_JUDGED_AGAINST",
                  "MULTI_BLOCK_DECLARED", "SLOT_STRUCTURE_FAMILIES",
                  "DESIGNED_TEXT", "DECOMPOSITION_DIVERGENCES",
                  "HAND_AUTHORED_ATTRS", "COUNTABLE_EXEMPT",
                  "PROBE_UNREACHABLE_PAIRS", "CONSENSUS_OVERLAP_BACKLOG",
                  "PROBE_PROVOCATIONS", "UNCHARGED_VERDICTS", "APP_ONLY_SLOTS"]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--table", action="append", default=None)
    args = ap.parse_args(argv)

    rows = sensitivity(args.table or DEFAULT_TABLES)
    ok = [r for r in rows if r.get("sensitive")]
    print(f"  {len(ok)} of {len(rows)} table(s) are SENSITIVE -- emptying them "
          f"moves a check that reads them\n")
    print(f"  {'table':<28} {'n':>3}  {'checks':>6}  verdict")
    for r in rows:
        mark = "sensitive" if r.get("sensitive") else "NOT sensitive"
        print(f"  {r['table']:<28} {str(r.get('entries','-')):>3}  "
              f"{len(r.get('checks') or []):>6}  {mark}"
              + (f"  ({', '.join(x[6:36] for x in r['moved'][:2])})" if r.get("moved") else ""))
    blind = [r["table"] for r in rows if not r.get("sensitive")]
    if blind:
        print(f"\n  {len(blind)} table(s) whose loss NOTHING would report:")
        for t in blind:
            print(f"    {t}")
        print("  Either inert (delete rather than migrate) or read by a check that "
              "passes\n  for unrelated reasons (the check is the weak instrument). "
              "This does not\n  guess between them -- but neither may be MIGRATED on "
              "the strength of a\n  check that would not notice the loss.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
