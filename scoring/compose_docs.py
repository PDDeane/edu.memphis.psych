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
# AND THE SECOND PLACEMENT, which the documents' own shape forced. `see: qc:NAME`
# puts a case directly after the anchored heading, which is right when the whole
# section below it is that case. It cannot express "after this section" -- and a
# generic subsection sitting BETWEEN two course ones is the normal arrangement in
# these files, not an exception. Without this form each such spot needs an invented
# connective heading in the generic half, which is prose written to satisfy a tool.
BLOCK_OPENS_END = re.compile(r"^see:\s*qc:([A-Za-z0-9_.-]+)\s+end\s*$")
HEADING = re.compile(r"^(#{1,6}) ")
# WHAT A BLOCK MAY ATTACH TO. A heading, or a list entry -- GOALS.md anchors
# `- [x] E1.` lines, so headings alone would be too narrow. Anything else is a line
# of running prose, and attaching there inserts the case INSIDE a paragraph.
SECTION_LINE = re.compile(r"^(?:#{1,6} |\s*(?:[-*+]|\d+\.) )")


def generic_path(name: str) -> str:
    """The half that states the principles: tracked, in the machinery."""
    return os.path.join(HERE, name)


# SPECIFIC HALVES THAT ACCUMULATE, which is a different thing from a specific half
# that is merely long. A guide's course half is AUTHORED: it changes when someone
# rewrites it, and its history is worth keeping. A ledger's course half is a LOG --
# it grows with course work, is rewritten whole on every entry, and its history is
# the cost the override log already demonstrated at 2,838 MB, 82% of every blob this
# repository has ever stored. A log that grows with course work cannot live in a
# repository that must not grow with it, so these go beside `gold.json` and
# `OVERRIDES.md` instead of into the course tree.
#
# WHAT IS GIVEN UP, and what replaces it. Outside git there is no committed prior
# state, and `goals.check()` compared against exactly that to catch a deleted entry
# and an unapproved closure. Both now compare against `GOAL_STATES.json`, which is
# tracked: 112 labels and their states, some 15 KB, rewritten only when a goal is
# opened or closed rather than on every prose edit. The state stays versioned; the
# prose stops being.
ACCUMULATING: tuple[str, ...] = ("GOALS.md",)


def specific_path(name: str) -> str:
    """The half that carries this course's cases.

    Tracked with the course, unless it ACCUMULATES -- see above, and `coursedata.
    overrides_path` for the measurement that set this rule.
    """
    if name in ACCUMULATING:
        return os.path.join(str(paths.DATA), "courses", paths.NS, name)
    return os.path.join(str(paths.COURSE_LOCATION), name)


def _blocks(text: str) -> dict:
    """{anchor: [block, ...]} from a specific half, in file order.

    A block runs from its `see: qc:NAME` line to the next one, or to the end. Text
    before the first reference is a PREAMBLE and is returned under the empty key:
    it belongs to no anchor, and dropping it silently is how a split loses content.
    """
    out: dict = {}
    current: object = ""
    buf: list = []
    for line in text.splitlines(keepends=True):
        bare = line.rstrip("\n")
        m = BLOCK_OPENS_END.match(bare) or BLOCK_OPENS.match(bare)
        if m:
            if buf:
                out.setdefault(current, []).append("".join(buf))
            mode = "end" if BLOCK_OPENS_END.match(bare) else "line"
            current, buf = (m.group(1), mode), []
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
    placed = 0
    # An `end` block waits for the anchored section to FINISH: (anchor, level),
    # emptied at the next heading of that level or higher, or at EOF.
    holding: list = []
    for line in generic.splitlines(keepends=True):
        h = HEADING.match(line)
        # AN ANCHOR BELONGS TO THE SECTION BELOW IT, so it ends the section above
        # just as a heading does. Without this a pending `end` block is emitted
        # AFTER the next section's anchor line -- the case lands between the anchor
        # and the heading it names, which reads as the wrong section's content.
        is_anchor = ANCHOR.match(line.rstrip("\n")) is not None
        if (h or is_anchor) and holding:
            level = len(h.group(1)) if h else 1
            keep = []
            for anchor, at in holding:
                if level <= at:
                    for block in blocks.get((anchor, "end"), ()):
                        out.append(block)
                        placed += 1
                else:
                    keep.append((anchor, at))
            holding = keep
        out.append(line)
        m = ANCHOR.match(line.rstrip("\n"))
        if m:
            pending = m.group(1)
            continue
        # Place a case after the anchored section's own line, not after the anchor
        # comment: the anchor sits above the heading or entry it names.
        if pending is not None and line.strip():
            # REFUSE A MID-PARAGRAPH ATTACHMENT. Putting the anchor BELOW its
            # heading instead of above it makes the next paragraph's first line the
            # section line, and the case then lands between that line and the rest
            # of its own sentence. Done once; the composed output read as a heading
            # followed by half a sentence, and nothing else reported it.
            if blocks.get((pending, "line")) and not SECTION_LINE.match(line):
                raise SystemExit(
                    f"compose_docs: {name} anchors `qc:{pending}` above a line of "
                    f"prose -- {line.strip()[:50]!r}. A case placed there splits "
                    f"that paragraph. Move the anchor above the heading or entry "
                    f"it names")
            for block in blocks.get((pending, "line"), ()):
                out.append(block)
                placed += 1
            if (pending, "end") in blocks:
                hm = HEADING.match(line)
                holding.append((pending, len(hm.group(1)) if hm else 6))
            pending = None
    # A TRAILING ANCHOR STILL RECEIVES ITS BLOCKS. When everything below an anchor
    # moves out, the anchor ends the generic half and no section line follows it --
    # and the loop above would carry `pending` off the end and drop the blocks
    # silently. That is the exact shape of the first real split, so it is handled
    # rather than discovered.
    if pending is not None:
        for block in blocks.get((pending, "line"), ()):
            out.append(block)
            placed += 1
        for block in blocks.get((pending, "end"), ()):
            out.append(block)
            placed += 1
        holding = [x for x in holding if x[0] != pending]
    for anchor, _at in holding:
        for block in blocks.get((anchor, "end"), ()):
            out.append(block)
            placed += 1

    # NO BLOCK IS EVER DROPPED. unplaced() reports an anchor the generic half never
    # defines, which is the error a person makes; this counts what composition
    # actually emitted, which is the error the composer makes. A split that loses a
    # paragraph is invisible in the result -- the document still reads whole -- so
    # it is caught here by arithmetic instead of by someone noticing prose missing.
    want = sum(len(v) for k, v in blocks.items() if k and k[0])
    if placed != want:
        raise SystemExit(
            f"compose_docs: {name} composed {placed} of {want} block(s); "
            f"{want - placed} would have vanished")
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
    for key in sorted(blocks, key=lambda k: (k if isinstance(k, str) else k[0])):
        anchor = key if isinstance(key, str) else key[0]
        if anchor == "":
            bad.append(f"{name}: the course half has text before its first "
                       f"`see: qc:` line, which belongs to no anchor and would be "
                       f"dropped")
        elif anchor not in have:
            bad.append(f"{name}: the course half cites `qc:{anchor}`, which the "
                       f"generic half does not anchor -- {len(blocks[key])} "
                       f"block(s) would be dropped")
    return bad


def composed_path(name: str) -> str:
    """The built document: what every READER opens."""
    return os.path.join(str(paths.COMPOSED_DOCS), name)


def build() -> list:
    """Write every composed document. Returns what was written."""
    os.makedirs(str(paths.COMPOSED_DOCS), exist_ok=True)
    out = []
    for name in SPLIT_DOCS:
        if not os.path.exists(generic_path(name)):
            continue
        bad = unplaced(name)
        if bad:
            raise SystemExit("compose_docs: refusing to build -- " + "; ".join(bad))
        text = compose(name)
        dest = composed_path(name)
        prior = None
        if os.path.exists(dest):
            with open(dest, encoding="utf-8") as fh:
                prior = fh.read()
        if prior != text:
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write(text)
        out.append((name, len(text.splitlines()), prior != text))
    return out


def stale() -> list:
    """Composed documents that no longer match their sources.

    A STALE COMPOSITION IS SILENT, which is why this exists rather than being
    left to whoever remembers to rebuild: every reader still opens a whole,
    well-formed document and every check still runs -- against prose nobody is
    editing. The rubric's own expansion carries the same check for the same
    reason, and its docstring says what the failure looks like: "every item still
    parses, every slot still reads, and the scores describe a rubric nobody is
    editing".
    """
    out = []
    for name in SPLIT_DOCS:
        if not os.path.exists(generic_path(name)):
            continue
        dest = composed_path(name)
        if not os.path.exists(dest):
            out.append(f"{name} has never been composed ({dest}); run "
                       f"`python3 compose_docs.py --build`. Readers open the "
                       f"composed copy, so an unbuilt one is a document that does "
                       f"not exist")
            continue
        with open(dest, encoding="utf-8") as fh:
            have = fh.read()
        if have != compose(name):
            out.append(f"{name} was composed from sources that have since "
                       f"changed -- the composed copy is stale, and every reader "
                       f"is reading prose nobody is editing. Rebuild it")
    return out


def main(argv: list) -> int:
    if "--build" in argv:
        for name, n, changed in build():
            print(f"  {name:<24} {n:>6} lines  {'written' if changed else 'unchanged'}")
        return 0
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
