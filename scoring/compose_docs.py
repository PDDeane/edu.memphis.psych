#!/usr/bin/env python3
"""Compose a split document from its generic half and its course-specific half.

THE SPLIT, and why composition exists at all. A procedure document states general
principles and grounds them in measured cases. The principles belong to the
machinery and the cases belong to the course, so they are stored apart: the generic
half in `scoring/`, the course-specific half in `$COURSE_LOCATION`. Everything that
READS a document reads the composed artifact, so the split is invisible downstream
and no reader has to know that its source is two files.

HOW A HALF SAYS WHERE IT GOES. The generic half anchors a section with
`<!-- qc:NAME -->`, which is the existing cross-file alias `anchors.py` already
gates. The specific half is a run of blocks, each opening `see: qc:NAME`, and each
is placed immediately after the anchored section it names -- so a case is read in
the context of the principle it evidences, which is the point of splitting them
rather than merely separating them.

IDENTITY WHILE NOTHING IS SPLIT, which is the property that makes this safe to build
first. With no specific half, composition returns the generic half unchanged, byte
for byte. So the composer can be proved correct against all six documents BEFORE a
single paragraph moves -- the cheapest possible moment to discover it wrong. Every
split afterwards is checked the same way: compose the two halves and require the
result to equal the document as it stood before the cut.

ORDER IS DETERMINED, NOT INCIDENTAL. Blocks for one anchor are emitted in the order
they appear in the specific half, and anchors are visited in the order of the
generic half. Two files, one arrangement, so composing twice gives the same bytes
and a diff means a real change.
"""
from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import paths

# The documents that are split, or will be. A name here is composed; anything else
# is read as it lies.
SPLIT_DOCS: tuple[str, ...] = (
    "GOALS.md",
    "QUALITY_CONTROL.md",
    "EQUIVALENCE.md",
    "README.md",
)

ANCHOR = re.compile(r"^<!--\s*qc:([A-Za-z0-9_.-]+)\s*-->\s*$")
# A block in the specific half opens with the reference naming where it belongs.
BLOCK_OPENS = re.compile(r"^see:\s*qc:([A-Za-z0-9_.-]+)\s*$")


def generic_path(name: str) -> str:
    """The half that states the principles: tracked, in the machinery."""
    return os.path.join(HERE, name)


def specific_path(name: str) -> str:
    """The half that carries this course's cases: tracked, with the course."""
    return os.path.join(str(paths.COURSE_LOCATION), name)


def _blocks(text: str) -> dict:
    """{anchor: [block, ...]} from a specific half, in file order.

    A block runs from its `see: qc:NAME` line to the next one, or to the end. Text
    before the first reference is a PREAMBLE and is returned under the empty key:
    it belongs to no anchor, and dropping it silently is how a split loses content.
    """
    out: dict = {}
    current = ""
    buf: list = []
    for line in text.splitlines(keepends=True):
        m = BLOCK_OPENS.match(line.rstrip("\n"))
        if m:
            if buf:
                out.setdefault(current, []).append("".join(buf))
            current, buf = m.group(1), []
            continue
        buf.append(line)
    if buf:
        out.setdefault(current, []).append("".join(buf))
    return out


def compose(name: str) -> str:
    """The whole document: the generic half with each case placed at its anchor."""
    with open(generic_path(name), encoding="utf-8") as fh:
        generic = fh.read()
    sp = specific_path(name)
    if not os.path.exists(sp):
        return generic                      # nothing split yet: the identity
    with open(sp, encoding="utf-8") as fh:
        blocks = _blocks(fh.read())
    if not blocks:
        return generic

    out: list = []
    pending: str | None = None
    for line in generic.splitlines(keepends=True):
        out.append(line)
        m = ANCHOR.match(line.rstrip("\n"))
        if m:
            pending = m.group(1)
            continue
        # Place a case after the anchored section's own line, not after the anchor
        # comment: the anchor sits above the heading or entry it names.
        if pending is not None and line.strip():
            for block in blocks.get(pending, ()):
                out.append(block)
            pending = None
    return "".join(out)


def unplaced(name: str) -> list:
    """Cases whose anchor the generic half does not define -- content that would
    vanish. Composition must never drop a block, so this is checked, not hoped."""
    sp = specific_path(name)
    if not os.path.exists(sp):
        return []
    with open(sp, encoding="utf-8") as fh:
        blocks = _blocks(fh.read())
    with open(generic_path(name), encoding="utf-8") as fh:
        have = {m.group(1) for m in (ANCHOR.match(l.rstrip("\n"))
                                     for l in fh) if m}
    bad = []
    for anchor in sorted(blocks):
        if anchor == "":
            bad.append(f"{name}: the course half has text before its first "
                       f"`see: qc:` line, which belongs to no anchor and would be "
                       f"dropped")
        elif anchor not in have:
            bad.append(f"{name}: the course half cites `qc:{anchor}`, which the "
                       f"generic half does not anchor -- {len(blocks[anchor])} "
                       f"block(s) would be dropped")
    return bad


def main(argv: list) -> int:
    for name in SPLIT_DOCS:
        if not os.path.exists(generic_path(name)):
            print(f"  {name:<24} absent")
            continue
        bad = unplaced(name)
        text = compose(name)
        with open(generic_path(name), encoding="utf-8") as fh:
            same = fh.read() == text
        split = os.path.exists(specific_path(name))
        print(f"  {name:<24} {len(text.splitlines()):>6} lines  "
              f"{'split' if split else 'unsplit'}"
              f"{'  IDENTITY' if same and not split else ''}"
              + (f"  {len(bad)} UNPLACED" if bad else ""))
        for b in bad:
            print(f"      {b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
