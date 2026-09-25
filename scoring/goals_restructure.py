#!/usr/bin/env python3
"""T7.1 — make `GOALS.md` anchorable without changing what `goals.py` parses.

§10.4.1: 16,516 lines under **six** `##` headings, one of which runs 11,259
lines. A pointer into a section that long is a direction to go looking, not a
reference.

THE CONSTRAINT THAT DECIDES THE DESIGN. `goals.py` does not only parse entries;
`misfiled_series()` tracks the current section from `^## ` lines and checks each
entry's series against `SERIES_SECTION`. So **adding a `##` heading changes
SECTION MEMBERSHIP** for every entry beneath it — insert one mid-section and
entries nobody moved are suddenly filed under a new name and the check fires.

New granularity is therefore `###`, never `##`. `misfiled_series()` matches
`^## ` only, so `###` is invisible to it. The six top-level sections stay exactly
as they are and the anchors arrive beneath them. That is a constraint on the
result, not a preference: a restructuring that added `##` headings would look
right and would break a check that has nothing to do with it.

WHAT IT DOES, AND WHAT IT REFUSES TO DO. For each of the 112 entries it inserts,
immediately above the entry line, a `###` heading naming the entry and a
`<!-- qc:LABEL -->` anchor. The entry's own label is already the stable alias
G1c wants. **No existing line is altered.** Lines are inserted and nothing else:
a diff that touches every line cannot be reviewed, and this file is read by five
modules and by people.

THE PROOF IS ON (entry, section) PAIRS. "All 112 entries parse identically" is
necessary and weak -- `ENTRY` captures state, series, number and text, so an
entry can keep all four while moving between sections. Asserting
`misfiled_series()` returns the same list is also weak: it could return empty
before and after while entries moved, if the move stayed consistent with
`SERIES_SECTION`. So the round trip asserts the (entry, SECTION) pair for every
entry, and separately that `check`, `next_label`, `misfiled_series` and
`stale_slot_claims` return identical results.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# THE COMPOSED DOCUMENT, not the generic half beside this module -- the same
# resolution `goals.py:48` uses, and for the same reason. After the G2 split
# `os.path.join(HERE, "GOALS.md")` named the 53-line GENERIC half while the real
# document (16,722 lines) sat in $COURSE_DATA, so this tool reported "54 lines,
# 0 entries, round trip clean" over the wrong file: a FALSE CLEAN. A tool that
# resolves a split document by `__file__` cannot see the split.
import compose_docs

GOALS = compose_docs.composed_path("GOALS.md")
# The stamp is excluded from the title group; see `goals._STAMP`.
ENTRY = re.compile(r"^- \[([ x])\] ([A-Z]+)(\d+)\. (.*?)(?:\s*<!--@\d{4}-\d\d-\d\d-->)?$")
SECTION = re.compile(r"^## (.*)$")
ANCHOR = re.compile(r"^<!-- qc:([A-Za-z0-9_]+) -->$")
BOLD = re.compile(r"\*\*(.+?)\*\*")


def pairs(text: str) -> dict[str, tuple[str, str]]:
    """{label: (entry line, enclosing ## section)} -- the thing that must not move."""
    out, section = {}, "<none>"
    for line in text.split("\n"):
        m = SECTION.match(line)
        if m:
            section = m.group(1).strip()
            continue
        e = ENTRY.match(line)
        if e:
            out[f"{e.group(2)}{e.group(3)}"] = (line, section)
    return out


def _title(entry_text: str) -> str:
    """UNUSED, and kept as the record of a rejected design. See `restructure`.

    Headings once carried the entry's bolded title. That duplicated prose into
    the file, and `stale_slot_claims()` reads prose.
    """
    m = BOLD.search(entry_text)
    raw = (m.group(1) if m else entry_text).strip()
    return raw.rstrip(".").replace("`", "")


def restructure(text: str) -> tuple[str, int]:
    """-> (new text, headings added). Inserts only; idempotent."""
    lines = text.split("\n")
    out: list[str] = []
    added = 0
    for i, line in enumerate(lines):
        e = ENTRY.match(line)
        if e:
            label = f"{e.group(2)}{e.group(3)}"
            # Idempotent: if this entry already has its anchor just above, leave it.
            prior = [x for x in out[-3:] if x.strip()]
            if any(ANCHOR.match(x.strip()) and ANCHOR.match(x.strip()).group(1) == label
                   for x in prior):
                out.append(line)
                continue
            if out and out[-1].strip():
                out.append("")
            # THE LABEL AND NOTHING ELSE. The first version wrote
            # `### E1 — <the entry's bolded title>`, which reads better and was
            # REVERTED by this tool's own net: `stale_slot_claims()` scans open
            # entries' prose for slot-level figures, and duplicating the title
            # into a heading created new prose for it to read. The heading must
            # add no words of its own -- the human-readable title is on the entry
            # line immediately below, so nothing is lost but the duplication.
            out.append(f"### {label}")
            out.append(f"<!-- qc:{label} -->")
            added += 1
        out.append(line)
    return "\n".join(out), added


def verify(before: str, after: str) -> list[str]:
    """The round trip. Pairs first, then every public result `goals.py` computes."""
    problems = []
    b, a = pairs(before), pairs(after)
    if set(b) != set(a):
        problems.append(
            f"entry labels changed: only-before {sorted(set(b) - set(a))[:6]}, "
            f"only-after {sorted(set(a) - set(b))[:6]}")
    for label in sorted(set(b) & set(a)):
        if b[label] != a[label]:
            problems.append(
                f"{label}: (entry, section) moved.\n      before {b[label][1]!r}\n"
                f"      after  {a[label][1]!r}")
    if after.count("\n## ") != before.count("\n## "):
        problems.append(
            f"the number of `## ` sections changed "
            f"{before.count(chr(10) + '## ')} -> {after.count(chr(10) + '## ')}. "
            f"`misfiled_series()` reads those, so adding one refiles every entry "
            f"beneath it.")
    # no existing line may be altered: the new text must contain the old lines,
    # in order, as a subsequence
    ai = 0
    alines = after.split("\n")
    for line in before.split("\n"):
        while ai < len(alines) and alines[ai] != line:
            ai += 1
        if ai >= len(alines):
            problems.append(f"an existing line was altered or lost: {line[:60]!r}")
            break
        ai += 1
    return problems


LINEREF = re.compile(r"(GOALS\.md):\d+")


def _line_agnostic(value):
    """Results with LINE NUMBERS normalised away.

    Inserting a heading moves every line below it, so a finding reported as
    `GOALS.md:5747` becomes `GOALS.md:5856` while being the same finding about
    the same goal and the same slot. The first version of this net compared the
    raw strings and reverted a correct restructuring twice -- the count was 14
    before and 14 after, and only the numbers had moved.

    What must not change is WHICH claims are reported, so the numbers are
    normalised and everything else is compared exactly.
    """
    if isinstance(value, str):
        return LINEREF.sub(r"\1:<line>", value)
    if isinstance(value, list):
        return [_line_agnostic(v) for v in value]
    if isinstance(value, tuple):
        return tuple(_line_agnostic(v) for v in value)
    if isinstance(value, dict):
        return {k: _line_agnostic(v) for k, v in value.items()}
    return value


def live_results() -> dict:
    """What `goals.py` computes now, for a before/after comparison."""
    import goals

    out = {}
    for fn in ("check", "misfiled_series", "stale_slot_claims"):
        try:
            out[fn] = getattr(goals, fn)()
        except Exception as exc:
            out[fn] = f"<{type(exc).__name__}: {exc}>"
    try:
        out["next_label"] = goals.next_label()
    except Exception as exc:
        out["next_label"] = f"<{type(exc).__name__}: {exc}>"
    return {k: _line_agnostic(v) for k, v in out.items()}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--file", default=GOALS)
    ap.add_argument("--write", action="store_true",
                    help="apply; without it, report only")
    args = ap.parse_args(argv)

    before = open(args.file).read()
    after, added = restructure(before)
    problems = verify(before, after)

    b_pairs = pairs(before)
    print(f"  {len(before.split(chr(10)))} lines, {len(b_pairs)} entries, "
          f"{before.count(chr(10) + '## ')} `## ` sections")
    print(f"  {added} `###` heading(s) + anchor(s) to add "
          f"({len(after.split(chr(10))) - len(before.split(chr(10)))} lines inserted, "
          f"0 altered)")
    if problems:
        print(f"\n  REFUSING: {len(problems)} round-trip problem(s):")
        for p in problems:
            print(f"    {p}")
        return 1
    print("  round trip clean: every (entry, section) pair unchanged, "
          "no `## ` added, no existing line altered")

    if args.write:
        pre = live_results()
        open(args.file, "w").write(after)
        import goals
        import importlib
        importlib.reload(goals)                   # it caches the file it parsed
        post = live_results()
        drift = [k for k in pre if pre[k] != post[k]]
        if drift:
            open(args.file, "w").write(before)
            importlib.reload(goals)
            print(f"  REVERTED: goals.py results moved: {drift}")
            for k in drift:
                a, b = pre[k], post[k]
                print(f"    {k}: {len(a) if hasattr(a,'__len__') else a} -> "
                      f"{len(b) if hasattr(b,'__len__') else b}")
            return 1
        print(f"  written. goals.py agrees before and after on "
              f"{', '.join(sorted(pre))}")
    else:
        print("  (dry run -- pass --write to apply)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
