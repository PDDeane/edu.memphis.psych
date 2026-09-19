#!/usr/bin/env python3
"""T7.2 — anchors as STABLE ALIASES, and the gate over them.

G1c wants a course file to point at a section of the general prose. There is
already a machine-checked citation mechanism over one of these files:
`guide.py` maintains NUMERIC labels on `QUALITY_CONTROL.md`, derives them from
DOCUMENT ORDER in `renumber()`, and rewrites every citation it can find with
`_cited_by()`.

WHY NOT JUST USE THE NUMBERS. Because `renumber()` derives labels from order, so
inserting a section renumbers everything after it. Inside one repo that is fine
-- `_cited_by()` finds every citer and fixes it. **Across directories it is not**:
a course file in `courses/<id>/` is a citer `renumber()` cannot see, so a
renumber silently invalidates its pointers, and G1c's dangling check would then
fire on work that was correct when it was written.

WHY NOT REPLACE THE NUMBERS EITHER. Two schemes over one file is the worst
outcome -- a section carrying both, `renumber()` maintaining one, references free
to use either, and nothing to say which wins when they disagree.

So: **numbers for structure and in-file citation, anchors for cross-file
reference.** An anchor is added only to a section a course file actually points
at. `renumber()` must PRESERVE anchors, which is the change most likely to be
missed because renumbering looks unrelated to anchoring.

THE GATE. A reference to `qc:NAME` with no matching anchor FAILS -- it is a
pointer to nothing. An anchor nothing points at WARNS: an unused alias is a
section someone thought was general and no course needed, which is worth
noticing and is not an error. A deliberate orphan carries a declaration, never
an exemption list.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

# The four files Goal G covers. They are NOT alike -- `GOALS.md` is parsed by a
# different module whose heading sensitivity T7.1 had to discover -- so this is
# one rule over four documents rather than an extension of `guide.py`, which is
# shaped around exactly one.
PROSE_FILES = ("GOALS.md", "QUALITY_CONTROL.md", "BACKLOG.md", "EQUIVALENCE.md")

ANCHOR = re.compile(r"<!--\s*qc:([A-Za-z0-9_.-]+)\s*-->")
# REJECTED, and kept as the record of why. Matching a bare `qc:NAME` made every
# sentence DESCRIBING the convention into a live pointer: the plan's own
# `<!-- qc:NAME -->` example and this module's docstring both failed the gate on
# its first run. A citation form that cannot be written about is not usable in
# the document that specifies it.
_BARE_REFERENCE = re.compile(r"(?<!<!--\s)\bqc:([A-Za-z0-9_.-]+)")

# A reference is `see: qc:NAME`, and the `see:` is load-bearing.
REFERENCE = re.compile(r"see:\s*qc:([A-Za-z0-9_.-]+)")

# Anchors that are deliberately unpointed, with the reason. A declaration, never
# a list of exemptions: each entry says why the section is anchored anyway.
DECLARED_ORPHANS: dict[str, str] = {}


def _scan_text(text: str) -> tuple[set[str], set[str]]:
    return set(ANCHOR.findall(text)), set(REFERENCE.findall(text))


def scan(root: str | None = None) -> dict:
    """Anchors defined in the prose files; references made from anywhere."""
    root = root or HERE
    anchors: dict[str, str] = {}
    refs: dict[str, set[str]] = {}
    for name in PROSE_FILES:
        path = os.path.join(root, name)
        if not os.path.exists(path):
            continue
        found, _ = _scan_text(open(path, errors="ignore").read())
        for a in found:
            anchors[a] = name
    # CITERS ARE COURSE FILES, which is the whole reason anchors exist: a course
    # file is a citer `guide.renumber()` cannot see, so a renumber silently
    # invalidates its pointers. Scoped here rather than repo-wide because the
    # SPECIFICATION of the convention uses the convention -- the plan writes
    # "a `see: qc:NAME` with no matching anchor FAILS", and a repo-wide scan read
    # that sentence as a live pointer to a section called NAME.
    repo = os.path.dirname(os.path.abspath(root))
    courses = os.path.join(repo, "courses")
    for dirpath, dirnames, filenames in os.walk(courses):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules")]
        for fn in filenames:
            if not fn.endswith((".py", ".md", ".olx", ".json")):
                continue
            path = os.path.join(dirpath, fn)
            try:
                text = open(path, errors="ignore").read()
            except OSError:
                continue
            _a, found = _scan_text(text)
            for r in found:
                refs.setdefault(r, set()).add(os.path.relpath(path, repo))
    return {"anchors": anchors, "references": {k: sorted(v) for k, v in refs.items()}}


def verify(found: dict) -> tuple[list[str], list[str]]:
    """-> (failures, warnings). A dangler fails; an orphan warns."""
    anchors, refs = found["anchors"], found["references"]
    failures = [
        f"`qc:{name}` is referenced by {', '.join(where[:3])} and no prose file "
        f"defines that anchor -- a cross-file pointer to nothing"
        for name, where in sorted(refs.items()) if name not in anchors]
    # SUMMARISED PER FILE, not one line per anchor. T7.1 anchors every GOALS.md
    # entry so that any of them CAN be pointed at, which makes "unused" the
    # normal state there until courses exist to do the pointing -- 112 identical
    # warnings would bury the danglers that matter.
    unused: dict[str, int] = {}
    for name in sorted(anchors):
        if name not in refs and name not in DECLARED_ORPHANS:
            unused[anchors[name]] = unused.get(anchors[name], 0) + 1
    warnings = [
        f"{n} of {sum(1 for a in anchors.values() if a == f)} alias(es) in {f} "
        f"are pointed at by nothing yet"
        for f, n in sorted(unused.items())]
    for name in sorted(DECLARED_ORPHANS):
        if name in refs:
            failures.append(
                f"`qc:{name}` is declared a deliberate orphan and is now "
                f"referenced by {refs[name][0]} -- drop the declaration")
        elif name not in anchors:
            failures.append(
                f"`qc:{name}` is declared a deliberate orphan and is anchored "
                f"nowhere -- drop the declaration")
    return failures, warnings


def anchors_are_renumber_safe(root: str | None = None) -> list[str]:
    """Every anchor sits on its OWN LINE, so a heading rewrite cannot touch it.

    THE CHANGE MOST LIKELY TO BE MISSED, made impossible instead of promised.
    `guide.renumber()` rewrites heading lines, and an anchor sharing a heading
    line would not survive its next run.

    The first version of this check grepped `guide.py` for "qc:" and reported
    that renumbering had no anchor-preserving rule. Adding a DOCSTRING to
    `renumber()` made it pass -- a check satisfied by writing prose about the
    thing it checks. What can actually be verified is where the anchors ARE, so
    that is what is verified: off the heading line, a rewrite cannot reach them,
    and no promise about `renumber()` has to be trusted.
    """
    root = root or HERE
    bad = []
    for name in PROSE_FILES:
        path = os.path.join(root, name)
        if not os.path.exists(path):
            continue
        for n, line in enumerate(open(path, errors="ignore").read().split("\n"), 1):
            if not ANCHOR.search(line):
                continue
            if ANCHOR.sub("", line).strip():
                bad.append(
                    f"{name}:{n} puts an anchor on a line carrying other text. "
                    f"guide.renumber() rewrites heading lines, so an anchor "
                    f"sharing one does not survive its next run. Give it its own "
                    f"line.")
    return bad


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", default=HERE)
    args = ap.parse_args(argv)

    found = scan(args.dir)
    failures, warnings = verify(found)
    failures += anchors_are_renumber_safe(args.dir)

    print(f"  {len(found['anchors'])} anchor(s) across "
          f"{len(set(found['anchors'].values()))} prose file(s), "
          f"{len(found['references'])} distinct reference(s)")
    for w in warnings[:6]:
        print(f"    warn: {w}")
    if len(warnings) > 6:
        print(f"    warn: ... and {len(warnings) - 6} more unused alias(es)")
    if failures:
        print(f"\n  {len(failures)} FAILURE(S):")
        for f in failures:
            print(f"    {f}")
        return 1
    print("  every cross-file reference resolves.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
