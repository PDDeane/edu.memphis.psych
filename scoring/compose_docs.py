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

# THE DOCUMENTS THAT ARE SPLIT -- declared in lo-blocks, read from here.
#
# THE LIST OF RECORD IS `enforce/splitDocuments.ts`, on the user's instruction
# of 2026-09-27, because the GENERIC halves live there now: the list belongs
# with the documents it names. This reads it through the `split_documents`
# probe and caches the answer, exactly as `slot_vocab` reads the verdict
# vocabulary from the same bridge.
#
# IT REFUSES RATHER THAN FALLING BACK, for `slot_vocab`'s reason: a list that
# quietly reverts to a stale copy is how a document stops being checked while
# still looking checked. There is no hardcoded fallback here on purpose -- a
# fallback IS the second copy this change exists to remove.
#
# LAZY, because it is read at import time by `course_inventory.GENERIC_DOCS`
# and a probe spawns node. Nothing pays for the bridge until something actually
# asks which documents are split. Module `__getattr__` (PEP 562) keeps
# `compose_docs.SPLIT_DOCS` working for every existing caller unchanged.
_SPLIT: dict = {}


def _split_declaration() -> dict:
    """`{SPLIT_DOCS, NO_COURSE_HALF}` from lo-blocks, cached for the process."""
    if not _SPLIT:
        import lo_enforce

        got = lo_enforce.probe("split_documents", {})
        if not isinstance(got, dict) or "SPLIT_DOCS" not in got:
            raise SystemExit(
                "compose_docs: the split-document list could not be read from "
                "lo-blocks, so composition cannot tell which documents have two "
                "halves")
        _SPLIT["SPLIT_DOCS"] = tuple(got["SPLIT_DOCS"])
        _SPLIT["NO_COURSE_HALF"] = dict(got.get("NO_COURSE_HALF") or {})
    return _SPLIT


def __getattr__(name: str):
    """`SPLIT_DOCS` and `NO_COURSE_HALF` on first use. See above."""
    if name in ("SPLIT_DOCS", "NO_COURSE_HALF"):
        return _split_declaration()[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


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
    """The half that states the principles -- WITH THE ENGINE, beside `enforce/`.

    IT HAS BEEN IN THREE PLACES, and each move was decided by evidence rather
    than by taste, so the reasoning is kept rather than replaced:

      `scoring/`         where it began, loose among the modules
      the engine         the user's instruction was to move the non-rubric-specific
                         QC documents to lo-blocks. The move was REVERTED, because
                         `check_generic_documents_are_generic` reported `run_score
                         x37` in QUALITY_CONTROL.md the moment it arrived -- a
                         signal matching THIS rubric's measured scores. (A
                         hand-written scan for the course's name had reported zero,
                         which is the prepared-classifier lesson again.)
      the rubric         filed beside the `.olx`, on the conclusion the engine move
                         had forced: these were not in fact course-neutral.

    WHY IT MOVED AGAIN. That conclusion rested on contamination that has since
    been REMOVED. The user's instruction to clean QUALITY_CONTROL.md moved the
    course's measurements into the course half, and all four generic halves now
    read clean through `course_inventory.course_prose` -- the same prepared
    classifier that caught them. The premise for filing them with the rubric
    expired when the evidence for it did, so they sit with the machinery whose
    procedure they describe.

    AND NOW THEY ARE IN THE ENGINE, 2026-09-27, on the user's instruction: they
    are the documentation for the enforce rules, and lo-blocks files a module's
    documentation BESIDE it -- `slotSheet.md`, `promptAssembler.md`. These four
    describe what the rules are for and how a scoring model is brought under
    them, so they sit in `enforce/` with the rules.

    THE OBJECTION THAT SENT THEM BACK LAST TIME HAS EXPIRED. The first attempt
    was reverted because `check_generic_documents_are_generic` found `run_score
    x37` in QUALITY_CONTROL.md the moment it arrived -- this rubric's measured
    scores, in a document declared course-neutral. The user's instruction to
    clean it moved those measurements to the course half, and all four now read
    clean through `course_prose`. lo-blocks holds every one of its markdown
    files to course-neutrality by constitution, so the engine's own check is
    what keeps them honest from here.
    """
    import paths as _p
    return os.path.join(str(_p.LO), "packages", "shared", "lib", "llm",
                        "enforce", name)


# DOCUMENTS THAT ACCUMULATE -- a rule that governed nothing as of 2026-09-26,
# kept because it states a real cost and the decision that overrode it.
#
# THE RULE. A guide's course half is AUTHORED: it changes when someone rewrites
# it, and its history is worth keeping. A ledger's or a log's course half GROWS
# WITH COURSE WORK, is rewritten whole on every entry, and its history is the
# cost `coursedata.overrides_path` measured: 2,838 MB, 82% of every blob this
# repository has ever stored, against 18 MB of tracked content. On that measure
# GOALS.md, BACKLOG.md and OVERRIDES.md were filed outside the repository.
#
# THE DECISION THAT ENDED IT, the user's, 2026-09-26, with the size put to them
# and explicitly set aside -- *"I really don't care about the size"*. These are
# the documents of one quality-control cycle: the goals, the backlog they feed,
# the closures approved against them, the overrides the gate wrote when a
# finding was waived, and the guides that say how all of it is judged. They are
# read together and decided together, and filing three of them elsewhere for a
# storage reason made the set unreadable as a set. They are all in
# `<course>/<rubric id>_qc/` and all tracked.
#
# WHAT IT COSTS, so that the next person is not surprised by it. Every commit
# touching one of these rewrites its whole blob. OVERRIDES.md alone is 3.4 MB
# and machine-written by `precommit_gate.py` on every waived finding. The
# measurement above is what that grows into; nothing about it has been
# disproved, and the trade was made with it in view.
#
# THE TUPLE IS EMPTY, NOT DELETED. `paths._accumulating_docs` and this module's
# `specific_path` both read it, and an empty list of record keeps saying "none"
# where a deleted one would make the two readers silently disagree about
# whether the question still exists.
ACCUMULATING: tuple[str, ...] = ()

# Documents that live ENTIRELY with the course: no generic half, nothing to
# compose. A split document has a rule in it worth keeping behind; these do not --
# they are this course's outstanding work and one item's measured dead ends.
WHOLE_DOCS: tuple[str, ...] = ("BACKLOG.md", "Q6_MATCHING_CEILING.md")


def specific_path(name: str) -> str:
    """The half that carries this course's cases -- in `<course>/<rubric id>_qc/`.

    Tracked with the course, unless it ACCUMULATES -- see above, and `coursedata.
    overrides_path` for the measurement that set this rule.

    `qc/` ON BOTH SIDES, which is the whole point of the subdirectory. The generic
    half sits in `scoring/qc/` and the course half in `<course>/<rubric id>_qc/`, so the two
    are recognisable as the same kind of document from their paths alone and
    neither needs a declaration to say what it is. A `WHOLE_DOCS` entry has no
    generic half but is the same kind of thing, and is filed here too.
    """
    if name in ACCUMULATING:                  # empty since 2026-09-26; see above
        return str(paths.roots().rubric_dir / "authored" / name)
    return str(paths.rubric_docs_dir() / name)


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


def doc_path(name: str) -> str:
    """WHERE A DOCUMENT ACTUALLY IS. Every reader should ask this rather than
    joining a name onto `scoring/`.

    Moving a document does not break its readers loudly; it breaks them QUIETLY,
    because a reader that joins a name onto a directory gets a path that simply
    does not exist, and the well-behaved ones skip a missing file. Measured: after
    GOALS.md was split, `olx_prompts`' "anything naming this item in the written
    record" scan went on reading `scoring/GOALS.md` -- by then the 53-line charter
    -- and reported NO RECORD for every item. The composed document has 249
    mentions of Q6 alone. Nothing failed; the record just went blank.
    """
    if name in _split_declaration()["SPLIT_DOCS"]:
        return composed_path(name)
    if name in WHOLE_DOCS:
        return specific_path(name)
    return os.path.join(HERE, name)


# A SPLIT DOCUMENT WITH NO COURSE HALF, declared rather than sniffed.
#
# `missing()` checked only that the COMPOSED path existed, so "no course half
# because nothing moved" and "course half lost in a checkout" were
# indistinguishable -- the exact failure that function's own docstring says it
# exists to prevent. Declaring the absence makes silence mean something again.
#
# EMPTY TODAY, and that is the point: all four split documents have a course
# half, so this is a pure ratchet. An entry may only be added with a reason.
# NO_COURSE_HALF is declared in lo-blocks with _split_declaration()["SPLIT_DOCS"]; see the top of
# this module. Reading it here goes through `_split_declaration`.


def missing() -> list:
    """Documents a reader would look for and not find.

    The other half of doc_path's lesson: a resolver only helps the readers that
    use it, and a document that is simply GONE -- moved by hand, lost in a
    checkout -- reads as an empty record to every one of them.
    """
    out = []
    for name in sorted(set(_split_declaration()["SPLIT_DOCS"]) | set(WHOLE_DOCS)):
        if name in _split_declaration()["SPLIT_DOCS"] and not os.path.exists(generic_path(name)):
            continue                     # not split here; nothing to find
        if name in _split_declaration()["SPLIT_DOCS"] and not os.path.exists(specific_path(name)) \
                and name not in _split_declaration()["NO_COURSE_HALF"]:
            out.append(f"{name} is split here but has NO COURSE HALF at "
                       f"{specific_path(name)}, and its absence is not declared. "
                       f"Either the split moved nothing -- say so in "
                       f"NO_COURSE_HALF with the reason -- or the half is gone "
                       f"and the composed document is quietly the generic one")
        path = doc_path(name)
        if not os.path.exists(path):
            out.append(f"{name} is not at {path}, where its readers look. A reader "
                       f"that cannot find a document does not fail -- it reports an "
                       f"empty record")
    return out


def composed_path(name: str) -> str:
    """The built document: what every READER opens."""
    return os.path.join(str(paths.roots().composed_docs), name)


def build() -> list:
    """Write every composed document. Returns what was written."""
    os.makedirs(str(paths.roots().composed_docs), exist_ok=True)
    out = []
    for name in _split_declaration()["SPLIT_DOCS"]:
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


# A SENTENCE, beginning like prose rather than like a row of data. The length floor
# is 30 CHARACTERS, measured rather than guessed: the seam scoping does the work of
# excluding coincidence, so the floor only has to exclude fragments, and at 30, 40,
# 50, 60 and 80 the false-positive count across every split document is the same --
# zero. A floor of 80 was tried first and missed the real case, whose two sentences
# are 40 and 61 characters.
_SENTENCE = re.compile(r"(?<=[.!?])\s+")
_PROSE_LINE = re.compile(r"^[A-Za-z*`\[(]")


def _sentences(text: str) -> set:
    flat = re.sub(r"\s+", " ", text)
    return {s.strip() for s in _SENTENCE.split(flat)
            if len(s.strip()) > 30 and _PROSE_LINE.match(s.strip())}


def duplicated() -> list:
    """Prose that the split left in BOTH halves.

    LIFTING A RULE OUT OF A RECORD IS A MOVE, AND IT IS EASY TO MAKE IT A COPY.
    When a section is mostly record but states a general rule in passing, the rule
    belongs in the generic half and the record in the course half -- and if the
    sentence is not also deleted from the record, the composed document says it
    twice. That reads as emphasis rather than as a mistake. Three passages were
    duplicated this way in one sitting.

    SCOPED TO THE SEAM, and that is what makes it usable. Checking the composed
    document for repeated prose reports eight sentences in GOALS.md, every one a
    deliberate cross-reference between ledger entries -- a log restating an earlier
    finding is not a defect. A sentence present in BOTH HALVES cannot arise that
    way: the halves are disjoint by construction, so an overlap is always a copy
    that should have been a move.

    Compared after collapsing whitespace, because the two copies are wrapped
    differently -- the lifted one is re-wrapped in its new home. A line-window
    version of this check missed all three real cases for exactly that reason.
    """
    out = []
    for name in _split_declaration()["SPLIT_DOCS"]:
        sp = specific_path(name)
        if not os.path.exists(generic_path(name)) or not os.path.exists(sp):
            continue
        with open(generic_path(name), encoding="utf-8") as fh:
            g = _sentences(fh.read())
        with open(sp, encoding="utf-8") as fh:
            c = _sentences(fh.read())
        for sent in sorted(g & c):
            out.append(f"{name} has this sentence in BOTH halves -- {sent[:70]!r}..."
                       f" A rule lifted out of a record must be DELETED from the "
                       f"record; copied instead of moved, the composed document "
                       f"says it twice and it reads as emphasis")
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
    for name in _split_declaration()["SPLIT_DOCS"]:
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
    for name in _split_declaration()["SPLIT_DOCS"]:
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
