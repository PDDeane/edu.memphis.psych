"""Structural checks and label maintenance for QUALITY_CONTROL.md.

WHY THIS EXISTS. On 2026-09-03 six new sections were inserted into the guide at
one anchor point, with their labels typed by hand. Three of them collided with
labels that already existed -- two `2c`, two `2d`, two `2e` -- and all six landed
above `2a`, so section 2 read 2b1, 2b3, 2c, 2d, 2e, 2f, 2a, 2b, 2b2, 2c, 2d, 2e.
A reader pointed at "§2d" could not tell which was meant. Nothing caught it; it
was found by eye, two commits after the guide itself gained the line "what is
COMPUTED is likelier to be right than what is WRITTEN".

So the labels stop being written. `--renumber` derives them from document order
and rewrites every reference in the tree to match, and `check()` refuses a guide
whose structure has drifted. Inserting a section is then: paste it where it
belongs with any placeholder label, run --renumber --write, commit.

    python3 tools/guide.py --check                 structure + references + identifiers
    python3 tools/guide.py --renumber              dry run: print the mapping
    python3 tools/guide.py --renumber --write      apply it, rewriting references too
"""

from __future__ import annotations

# THE PACKAGE ROOT ON THE PATH, for the direct-script spelling. `tools/__init__`
# does this for `from tools import ...`, and a file run as `python3
# tools/NAME.py` never executes it -- so the import of a sibling fails at the
# first line that needs one. Both spellings are used, so both are made to work.
import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))


import hashlib
import re

# A SIBLING TOOL, and both spellings have to reach it: as `tools.guide` the
# PACKAGE is what is on the path, and as `python3 tools/guide.py` the bootstrap
# above puts the package ROOT there. A bare-name import works only in the
# second, which is how this module ran cleanly as a script and failed as a
# package member -- the one failure a script-only check could not see.
from tools import editguard
import paths
import subprocess
import sys
from pathlib import Path

# THE PACKAGE ROOT, not this file's parent -- the same hazard goal H makes the
# rest of this move wait for. From `tools/` this resolved to `tools/`, and the
# read it feeds failed loudly here only because the file it wants is a
# document; a glob would have returned an empty set and said nothing.
HERE = paths.SCORING

# TWO RESOLUTIONS, BECAUSE TWO CONSUMERS WANT OPPOSITE THINGS.
#
# `GUIDE` is the AUTHORED half beside this module: what we write, what git
# tracks, and what `renumber()` rewrites in place. `unapproved_lessons()` must
# read it too, because it diffs against `git show HEAD:./QUALITY_CONTROL.md` and
# only this half is committed there.
#
# `GUIDE_READ` is the COMPOSED document: what a reader actually sees. `check()`
# validates section labels, §-citations and backticked identifiers, and after
# goal G2's split those can live in EITHER half -- the course half already
# carries a `§2k` citation and dozens of identifiers that nothing validated
# while this pointed only at the authored half.
#
# REPOINTING `GUIDE` WHOLESALE IS THE OBVIOUS FIX AND IS WRONG: the lesson check
# would then compare the composed document against the HEAD-committed authored
# half and report every course-half lesson as newly added.
# THROUGH THE COMPOSER, not spelled here. It was `HERE / "QUALITY_CONTROL.md"`
# -- correct while the authored half lived beside this module, and broken the
# day it moved to the rubric component. The file still existed, the path did
# not, and the check reported that it COULD NOT RUN rather than passing, which
# is the one thing that made the breakage visible. `compose_docs.generic_path`
# is the single place that knows where an authored half lives.
def _guide() -> Path:
    import compose_docs
    return Path(compose_docs.generic_path("QUALITY_CONTROL.md"))


GUIDE = _guide()


def _composed_guide():
    """The composed document, or the authored half if composition is unavailable.

    Falling back rather than raising: a structure check that cannot find the
    composed copy should still check what it can, and `compose_docs.missing()`
    is what reports the composed copy being gone.
    """
    try:
        import compose_docs
        from pathlib import Path
        p = Path(compose_docs.composed_path("QUALITY_CONTROL.md"))
        return p if p.exists() else GUIDE
    except Exception:
        return GUIDE

# `## 2a. TITLE` / `## 2b2. TITLE` / `## 3. TITLE`. The label is what other files
# cite, so it is the thing that must stay unique and ordered.
HEAD = re.compile(r"^(#{2,3}) (\d+)([a-z][0-9a-z]*|)\. (.+)$", re.M)

# How the rest of the tree cites a section. Kept deliberately narrow: a bare "2c"
# in prose is not a citation, and rewriting one would corrupt a sentence.
REF = re.compile(r"(§ ?|QUALITY_CONTROL(?:\.md)? |[Ss]ection )(\d+[a-z][0-9a-z]*)\b")

# Files that may cite the guide. The guide itself is included: it cross-references
# its own sections.
def _cited_by() -> list[Path]:
    return sorted(
        # ROOT AND TOOLS, through the one inventory that knows the package's
        # shape. Globbing the root alone stopped seeing `corpus_ref` the moment it
        # moved into `tools/`, and reported its function as renamed or removed --
        # a finding about the scan, delivered as a finding about the tree.
        [p for p in editguard.modules() if p.name != "guide.py"]
        + list(HERE.glob("*.md"))
        + list(paths.roots().olx_dir.glob("*.olx"))   # J-7b
    )


def headings(text: str) -> list[tuple[str, str, str]]:
    """(label, title, hashes) in document order."""
    return [(f"{m.group(2)}{m.group(3)}", m.group(4), m.group(1))
            for m in HEAD.finditer(text)]


# THE SUFFIX ALPHABET, and the order is the policy rather than Python's default.
# Within one position DIGITS rank before LETTERS, and a SHORTER suffix ranks
# before a longer one. So `2z` precedes `2a0`, and `2a9` precedes `2aa`. Plain
# string sorting gets both of those backwards, which is why `suffix_key` exists
# and why nothing here uses `sorted()` on the raw labels.
_DIGITS = "0123456789"
_ALPHA = "abcdefghijklmnopqrstuvwxyz"


def suffix_key(suffix: str) -> tuple:
    """Sort key for a subsection suffix, per the ordering policy."""
    return (len(suffix), tuple((0, _DIGITS.index(c)) if c in _DIGITS
                               else (1, _ALPHA.index(c)) for c in suffix))


def _letters():
    """The suffix sequence: a..z, then a0..a9 aa..az, b0..b9 ba..bz, ...

    Two characters are only reached when a section has more than 26 subsections,
    which none currently does -- the wider alphabet exists so that the day one
    does, the labels stay derivable instead of becoming a judgement call. The
    first character is always a LETTER; digits appear only in later positions.
    """
    width = 1
    while True:
        if width == 1:
            for c in _ALPHA:
                yield c
        else:
            import itertools
            for combo in itertools.product(_ALPHA, *([_DIGITS + _ALPHA] * (width - 1))):
                yield "".join(combo)
        width += 1


def plan(text: str) -> dict[str, str]:
    """old label -> new label, deriving letters from document order.

    A parent section (`2`) keeps its number. Its subsections are lettered in the
    order they physically appear, which is the whole point: the label stops being
    an assertion about position and becomes a reading of it.
    """
    out: dict[str, str] = {}
    per_parent: dict[str, list[str]] = {}
    for label, _title, _h in headings(text):
        m = re.fullmatch(r"(\d+)([a-z][0-9a-z]*)?", label)
        if not m:
            continue
        parent, suffix = m.group(1), m.group(2)
        if not suffix:                       # `## 3.` — a parent, unchanged
            out[label] = label
            continue
        per_parent.setdefault(parent, []).append(label)
    for parent, labels in per_parent.items():
        gen = _letters()
        for old in labels:
            out[old] = f"{parent}{next(gen)}"
    return out


def check(strict_identifiers: bool = True) -> list[str]:
    """Everything about the guide's structure that a program can settle."""
    bad: list[str] = []
    try:
        text = _composed_guide().read_text()
    except OSError as e:
        return [f"{GUIDE.name} cannot be read: {type(e).__name__}: {e}"]

    heads = headings(text)
    labels = [h[0] for h in heads]

    # 1. DUPLICATES. The failure that produced this file.
    seen: dict[str, str] = {}
    for label, title, _h in heads:
        if label in seen:
            bad.append(
                f"{GUIDE.name}: duplicate section label `{label}` — "
                f"'{seen[label]}' and '{title}'. A citation of §{label} is "
                f"ambiguous; run `python3 tools/guide.py --renumber --write`")
        else:
            seen[label] = title

    # 2. ORDER. Labels must ascend in document order, or the label is telling the
    #    reader something the document contradicts.
    by_parent: dict[str, list[str]] = {}
    for label in labels:
        m = re.fullmatch(r"(\d+)([a-z][0-9a-z]*)?", label)
        if m and m.group(2):
            by_parent.setdefault(m.group(1), []).append(m.group(2))
    for parent, suffixes in by_parent.items():
        if suffixes != sorted(suffixes, key=suffix_key):
            bad.append(
                f"{GUIDE.name}: section {parent}'s subsections are out of order — "
                f"{' '.join(suffixes)}, which under the ordering policy should be "
                f"{' '.join(sorted(suffixes, key=suffix_key))}. Run "
                f"`python3 tools/guide.py --renumber --write`, or move the sections")

    # 3. REFERENCES. Every citation anywhere in the tree must resolve.
    known = set(labels)
    for path in _cited_by():
        try:
            src = path.read_text()
        except OSError:
            continue
        for n, line in enumerate(src.splitlines(), 1):
            for _prefix, ref in REF.findall(line):
                if ref not in known:
                    bad.append(
                        f"{path.name}:{n} cites §{ref}, which is not a heading in "
                        f"{GUIDE.name}. Fix the citation, or the section was "
                        f"renamed without its references")

    # 3b. BARE REFERENCES. A citation with no prefix -- `(2i)`, `see 2i` -- is
    #     invisible to REF, so --renumber walks straight past it and it silently
    #     comes to mean a DIFFERENT section. That is not hypothetical: the first
    #     renumber left two of them behind, both pointing at the section that
    #     had taken the label. They cannot be repaired automatically either,
    #     because the label they carry still resolves -- to the wrong thing. So
    #     they are refused at writing time instead: use the § form.
    for n, line in enumerate(text.splitlines(), 1):
        stripped = REF.sub("", line)
        for m in re.finditer(r"\((?:see )?(\d+[a-z][0-9a-z]*)\)|\bsee (\d+[a-z][0-9a-z]*)\b",
                             stripped):
            ref = m.group(1) or m.group(2)
            if ref in known:
                bad.append(
                    f"{GUIDE.name}:{n} refers to section {ref} without a `§`, so "
                    f"--renumber cannot follow it and it will come to mean a "
                    f"different section. Write `§{ref}`")

    # 4. IDENTIFIERS. A guide naming a function that no longer exists reads as
    #    coverage of a thing nobody maintains.
    if strict_identifiers:
        hay = "\n".join(p.read_text() for p in _cited_by()
                        if p.suffix in (".py", ".olx"))
        for raw in set(re.findall(r"`([A-Za-z_][A-Za-z0-9_.]*(?:\(\))?)`", text)):
            name = raw.rstrip("()")
            if "." in name:
                name = name.split(".")[-1]
            if len(name) > 3 and ("_" in name or name[0].isupper()):
                if name not in hay:
                    bad.append(
                        f"{GUIDE.name} names `{raw}`, which does not appear "
                        f"anywhere in the tree — renamed or removed")

    # 5. EMPHASIS. Per PARAGRAPH, not per line: this document is hard-wrapped and
    #    a span crossing a line break is normal. Checking per line reported 140
    #    issues and every one was the checker's.
    body = re.sub(r"```.*?```", "", text, flags=re.S)
    for para in body.split("\n\n"):
        head = para.strip().splitlines()[0][:60] if para.strip() else ""
        if para.count("`") % 2:
            bad.append(f"{GUIDE.name}: unbalanced ` in paragraph '{head}'")
        if para.count("**") % 2:
            bad.append(f"{GUIDE.name}: unbalanced ** in paragraph '{head}'")
    return bad


def renumber(write: bool = False) -> list[str]:
    """D
    ANCHORS SURVIVE RENUMBERING. `renumber()` rewrites heading lines, and a
    `<!-- qc:NAME -->` alias sits on or beside one, so without this a renumber
    would destroy the very aliases that exist because renumbering moves labels.
    The aliases are what a COURSE file points at, and a course file is a citer
    `_cited_by()` cannot see -- which is the reason for anchors in the first
    place. See `anchors.py`.

erive labels from document order; rewrite headings and every citation."""
    text = GUIDE.read_text()
    mapping = {o: n for o, n in plan(text).items() if o != n}
    lines = [f"{len(mapping)} label(s) change:"] if mapping else ["labels already match document order"]
    for old, new in sorted(mapping.items()):
        lines.append(f"    {old:>5} -> {new}")
    if not mapping:
        return lines

    def _heads(t: str) -> str:
        def sub(m):
            label = f"{m.group(2)}{m.group(3)}"
            return f"{m.group(1)} {mapping.get(label, label)}. {m.group(4)}"
        return HEAD.sub(sub, t)

    def _refs(t: str) -> tuple[str, int]:
        n = 0
        def sub(m):
            nonlocal n
            if m.group(2) in mapping:
                n += 1
                return m.group(1) + mapping[m.group(2)]
            return m.group(0)
        return REF.sub(sub, t), n

    edits: list[tuple[Path, str]] = []
    new_guide, n_self = _refs(_heads(text))
    edits.append((GUIDE, new_guide))
    lines.append(f"  {GUIDE.name}: headings rewritten, {n_self} self-citation(s)")
    for path in _cited_by():
        if path == GUIDE:
            continue
        try:
            src = path.read_text()
        except OSError:
            continue
        out, n = _refs(src)
        if n:
            edits.append((path, out))
            lines.append(f"  {path.name}: {n} citation(s)")
    if write:
        for path, out in edits:
            path.write_text(out)
        lines.append("WRITTEN.")
    else:
        lines.append("dry run — pass --write to apply")
    return lines


def main(argv: list[str]) -> int:
    if "--renumber" in argv:
        print("\n".join(renumber(write="--write" in argv)))
        return 0
    bad = check()
    print("\n".join(f"  ! {b}" for b in bad) if bad
          else f"  {GUIDE.name}: structure clean "
               f"({len(headings(_composed_guide().read_text()))} headings, references and "
               f"identifiers resolve)")
    return 1 if bad else 0


# MOVED ABOVE THE MAIN GUARD 2026-09-16. Everything below
# `if __name__ == "__main__":` exists ONLY when this module is imported -- a
# script run ends inside `main()` and never reaches it. `probe.control_gate` is
# the guard that voids a probe measuring its own envelope, and it simply was not
# there when probe.py was run directly. Nothing reported that; the parse, the
# imports and every table survived. `check_no_module_defines_names_after_its_main_guard`
# is what reports it now.
# ---------------------------------------------------------------- approvals

# LESSONS ADDED TO THE GUIDE WITH THE USER'S EXPLICIT APPROVAL, keyed by the sha
# of the prose. Re-wording a lesson LAPSES its approval and the check asks again
# -- the same rule `leakage.py` applies to its waivers, and for the same reason:
# an approval that survives an edit is an approval of something nobody read.
#
# Standing instruction, 2026-09-04: "Asking for permission before adding lessons
# to the guide should be enforced, not rely on you to remember." So it is state,
# not a habit. To approve a lesson, paste the sha the finding prints.
LESSONS_APPROVED: dict[str, str] = {
    # ---- THE QUALITY_CONTROL GENERIC/SPECIFIC CLEAN-UP, approved 2026-09-26 on
    # the user's explicit instruction ("Approve all four"). The guide carried
    # this rubric's measured scores in twelve passages -- `run_score x37` by
    # `course_prose` -- which is what stopped it being filable with the rubric
    # component as a generic document. The numbers moved to the course half;
    # 117 run-score figures before and after, none lost.
    #
    # TWO OF THE FOUR ARE REWORDINGS whose approval lapsed because the sha
    # changed, which is the mechanism working as designed: the claim is the
    # same and the numbers are gone.
    "669345da7a52": "a stored result does not recompute when gold changes -- "
                    "reworded to drop the 17/20/16/20 figures, which moved to "
                    "the course half",
    "0123a4a6d80d": "what a hand-picked set hides -- reworded to drop the "
                    "4/12 -> 0/12 fall and the 76-vs-230 call counts",
    #
    # AND TWO ARE NEW connective sentences, written to replace a table that
    # moved out. They say where the evidence went and what shape to read it
    # for; without them the section states a lesson with its demonstration
    # silently removed.
    "fc535004c2d3": "points at the probe table now in the course half, and "
                    "names the shape worth reading it for (a probe clean on "
                    "its non-target cell-slots)",
    "200b443a91cd": "points at the edit-vs-outcome table now in the course "
                    "half: three sound diagnoses that each cost a sweep",
    # ---- THE QUALITY_CONTROL SPLIT, approved 2026-09-24 on the user's explicit
    # instruction to split this guide with "the illustrations becoming the course
    # specific part". Each of these lessons was GENERICISED, not re-argued: the
    # named cell or item was replaced by an anonymous one and the specifics moved
    # to the course half. The claim is unchanged in every case; the sha moved
    # because the sha covers the whole lead paragraph.
    #
    # REVIEWED ONE AT A TIME, and the review earned its keep on the first entry:
    # the draft had widened "REFUSES to sweep handout 2" to "an item", asserting
    # a refusal that does not exist -- `agreement.py` tests `args.handout == 2`
    # before consulting leakage.py. Corrected to "the handout its gate is armed
    # for" BEFORE approval, and the handout-2 fact moved to the course half.
    "1d2af067f1fe": "leakage gate, handout named -> scoped generically -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. They chose to move ALL THREE of the
    # cohort citations to the course half rather than keep two as form
    # illustrations, so the lead now says "a participant number, and what
    # they scored". The GENERALITY ("a citation is usually...") is not new:
    # the original asserted "which is the common shape and the reason the
    # test is usually cheap" two sentences later.
    "48414dec1dce": "citation-deletion test, Q1 measurement moved out -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. The draft had invented TWO rates the
    # evidence did not carry -- "label boxes are the usual offender" and "in
    # half the cells of an item" -- from a single item. Both removed. The
    # user then supplied the missing mechanism: the on-screen boxes are a
    # RECONSTRUCTION, because lo-blocks re-presents one paper question as
    # subquestions and the fixture deals the single response out among them.
    # The original relied on the reader already knowing that; with the course
    # example gone it had to be said, and saying it is what makes the
    # prose/chart contrast mean anything.
    "974c029ee050": "provenance over position, with the reconstruction stated -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. The draft dropped "+2.0" as course
    # data while KEEPING "two boxes" and "three unrelated cells", which are
    # equally one item's numbers -- half a genericisation. All three now go,
    # and the sentence states the thing that actually generalises: a per-cell
    # fix list gives you a scatter, reading the SHAPE gives you one target.
    "bbf81ede44c0": "close an audit with a backlog entry; shape over cell list -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. Purely a scoping change: the handout
    # named in the lead becomes the CONDITION the rule fires under, and the
    # flat "The answer is one prose block" becomes "When the answer is".
    # Every mechanical clause -- the counted-group distribution, the
    # `f"{n} found"` placeholder, the dependency on declaring `counts` -- is
    # untouched.
    "9e98888f5c9b": "a rubric edit can change the INPUT where boxes are rebuilt -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. One substantive change, the cell id,
    # plus grammar to keep the sentence running after the subject moved.
    #
    # THE FIGURES WERE KEPT ON PURPOSE, against the treatment given to
    # "bbf81ede44c0" above, and the distinction is the point: there the
    # counts decorated a contrast; here "10 of 18" and "0/3, 2/3, 3/3" ARE
    # the evidence that a cell throws three-identical runs in BOTH
    # directions. Remove them and "uniformity is what three passes cannot
    # separate from a real flip" becomes assertion. "A quarter of the time"
    # is arithmetic about a fair coin, not an observation, so it generalises.
    "73d95696ccba": "a clean 3/3-to-0/3 flip is not decisive either -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. The item id goes, and "at 18/20"
    # becomes "a cell high" -- dropping the id alone would have left a
    # figure with no denominator. Stating the ERROR rather than the score
    # is what the lesson is about, and it stays true to the arithmetic.
    # The run triples are kept for the same reason as the entry above: they
    # ARE the demonstration that the median was 17 while the eye picked 18.
    "afccefa3aea1": "quote the ledger median, not the run table best line -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. The cell id goes and the tense moves
    # from past to present, which follows necessarily: without the specific
    # cell a narrated incident becomes a described failure mode. The figures
    # stay because they ARE the mechanism -- it is the IDENTICAL endpoints
    # (0 of 3 ... 0 of 3) that make the diff read "no change" while a real
    # gain was lost between them.
    "c081156249ff": "diff against the RECORDED state, not just the baseline -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. The mechanism -- why an OPEN subgoal
    # makes both owner-checks read zero -- is byte-identical; only the date,
    # the two subgoal labels and the cell id moved out. "caught" -> "has
    # caught" is required rather than stylistic: with the date gone the
    # simple past dangles. "Twice in one day" is KEPT because it is what
    # makes this a structural trap rather than carelessness.
    "5b8b213a0e36": "why the obvious owner-check reads zero at closure -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. Three NAMED INCIDENTS become three
    # FAILURE MODES, which is what generalises; every subgoal label and cell
    # id is in the course half. The draft flattened the first mode into
    # "undercounted", which understated it: the regex reported that NONE of
    # the at-risk cells was owned and preflight then named ALL of them -- a
    # total false negative, not a rounding error. Restored at the user's
    # direction before approval.
    "a10dc1885509": "do not re-derive cell ownership with a regex over prose -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. The smallest edit in the set: the cell
    # id becomes "a cell" and the verb follows it into the present. The
    # 6-of-12 / 11-of-12 figures are STRUCTURAL, not decorative -- the second
    # clause turns on the entries having been written about "a 6-of-12 cell",
    # so the starting figure has to be the same number twice in one sentence.
    "f9ac44c4aac3": "a cell can be orphaned by getting BETTER -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. Two DELETIONS and nothing else -- the
    # date and the item id. No word added, reordered or reworded. This is a
    # lead-in; the two failures it introduces follow as bullets which are not
    # bold-led and so carry no approval of their own, though they were
    # genericised too and their specifics are in the course half.
    "b38ab42cf674": "a pre-registered set hand-typed is still a nonce classifier -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. THE THIRD TIME a draft smuggled in a
    # frequency claim: "Q4c/p9 is a key there" became "is the usual case",
    # turning one instance into a rate the original never asserts. The tic
    # recurs at a predictable seam -- where a named example is removed and
    # the sentence needs something to fill the gap. Restated as the
    # triggering CONDITION ("which happens when..."), which also fixes the
    # grammar the draft had mangled.
    "ba2888af496f": "pass the slot to probe_falsifiers, not the item alone -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. The control list and the "None of them
    # asks" turn are byte-identical; only the worked example generalised, and
    # the named rule identifiers went to the course half with the figures.
    # Two fixes before approval: "may be around a tenth" weakened the very
    # disproportion the passage exists to show, so it is now "can be as
    # little as a tenth"; and the reflow had stranded a lone "A" at a line
    # end.
    "18f17620be5d": "no control asks whether it is the right PROMPT -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. Lead byte-identical; both bullets
    # genericised. Bullet 1 had been left with a DANGLING PROMISE -- it said
    # the note "says the opposite in gold's own words" after the quotation
    # itself had moved to the course half, so it announced words it no longer
    # produced. Closed as "says the opposite outright"; the quotation still
    # reaches the reader through the composed document.
    "c417dcc3315c": "read the FULL gold text, never a summary or keyword match -- user, 2026-09-24",
    # ---- The five below were created by COMPLETING the split. The first pass
    # detected item ids, corpus refs, handout numbers and domain vocabulary,
    # but not PARTICIPANT IDS or SUBGOAL LABELS, so sixteen paragraphs kept
    # their course identifiers and the "zero references" report was wrong.
    #
    # Reviewed with the user 2026-09-24. Claim and reasoning byte-identical;
    # only the trailing example changed. It replaces a bare pointer -- opaque
    # unless you already know the route -- with the CONDITION that makes the
    # verdict inadmissible, which is what the lesson is actually about.
    "189a3ea6079c": "a VOID probe cannot be cited, including DEAD ON REACH -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. Five identifier deletions and ONE
    # addition, "whole", which is load-bearing: the original said "exactly
    # ONCE in the item, on p4", and the cell id was what told you the count
    # ranged over the WHOLE item rather than the six probed cells. Deleting
    # it alone would have quietly changed the meaning. Cost figures kept --
    # 76 calls against ~230 IS the argument for the all-cells probe.
    "3bdcd14702b8": "what a hand-picked probe set hides -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. This is the lesson whose leftover "p2"
    # exposed the participant-id blind spot. Six identifier removals and three
    # consequent repairs: "declares ... to be" -> "records ... as" now that the
    # subject is a phrase not a table name; the second "a standing declaration"
    # -> "that declaration", since replacing the name made the phrase stutter
    # across adjacent sentences and the back-reference is also more precise;
    # and both p2s go. The closing contrast -- same item, same criterion,
    # opposite dispositions -- is untouched and is what carries the lesson.
    "c51618b7ba5a": "a rescore that would contradict a standing declaration -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. ONE change in nine lines: the subgoal
    # label goes and "the Q19 sweep" becomes "a whole sweep", keeping the
    # original's emphasis that an ENTIRE sweep was the cost.
    #
    # CORPUS COUNTS WERE KEPT HERE AND THROUGHOUT ("20 of the 68 asked
    # slots", "23 of 24", "76 calls against ~230"), on the rule that a ratio
    # which IS the argument stays while an incidental count moves. These are
    # corpus sizes, not people or cells. Raised with the user as a class they
    # could move as a set if they would rather the guide carry none.
    "d65eddf90ac8": "get the question from question_for; never retype it -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. The date and subgoal label go; the full
    # accounting stays (23 of 24 passed, nine cells over-fired, ~230 calls,
    # reproduced standalone in 24) because the numbers are what make the rule
    # cost something. Paragraph reflowed at the user's direction: removing the
    # date had pulled the wrap forward and left a short line.
    "e198d23da7a3": "probe the EXACT string that ships, not a paraphrase -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. This carried the SECOND scope error the
    # review caught: the draft read "a compound slot USUALLY needs it",
    # inventing a rate from one instance. Restated as the structural condition
    # -- the recipe is what a slot holding ALTERNATIVE grounds needs -- which
    # is also more useful than the original, since "2a needed it" told a
    # reader nothing about when THEY would need it. De Morgan construction,
    # forbid/requires wiring and the OLX snippet all untouched. Reflowed.
    "8d6027c6e294": "the OR recipe, via De Morgan on an operand slot -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. Five cell ids and the subgoal label go.
    # "They are now Q32" -> "They became their own subgoal" keeps what the
    # sentence did -- record that the finding was FILED, not merely noticed --
    # which matters because the next lesson in 2g follows those same five
    # cells and shows four were coin flips. "All six runs on each side" stays:
    # it is what makes the finding a defect rather than noise. Reflowed.
    "9fb1c51b9b88": "the hand pass compared one side only -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. The draft BROKE THE SENTENCE'S SHAPE:
    # the original is a matched pair of QUOTED entries set against each other,
    # and describing the first while quoting the second collapsed the contrast.
    # Both are now described, which also removes the second course specific
    # ("34 refusals, 71% precision") that the draft had left standing.
    #
    # The user also caught "in this project" here -- a self-reference that
    # anchors the guide to one course. SEVEN such references were found and
    # removed across the document; they were a class no detector covered.
    "f6a1d3c5e96c": "name the cell and the slot, not the count -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. A three-word deletion, "in this
    # project", plus reflow; the substantive claim is byte-identical. One of
    # the seven SELF-REFERENCES the user caught -- a class no detector covered,
    # because it names no item, participant, subgoal or handout and yet
    # anchors the guide to a single project.
    "ef682be44938": "the reliable line falls between computed and written -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. The draft had CHANGED THE MEANING while
    # removing "in this project": two coordinate claims joined by a semicolon
    # ("structural fixes have worked; wording changes mostly have not") became
    # a conditional ("...have worked WHERE wording changes have not"), which
    # asserts a causal link the evidence does not carry. Semicolon restored.
    #
    # A FOURTH failure mode from the same seam: deleting a course-specific
    # phrase leaves a gap, and filling the gap is where meaning drifts. The
    # first three were invented frequencies; this one an invented link.
    "8b42cc5acb35": "change the SHAPE of the question, not its wording -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. BOTH grader quotations go to the course
    # half. The draft paraphrased the CHARGE while leaving the ADVICE verbatim --
    # an inconsistency the user first approved as it stood and then directed out,
    # so the sha moved once and the superseded entry 690cca4651ac was dropped
    # (declared to editguard, which refused the undeclared removal first).
    # The mechanism survives without the quote: the advice named a TIME PERIOD
    # and was misread as a cadence objection, so "state something WEEKLY" carries
    # what made the trap visible. No detector would have caught the quote -- it
    # holds no item, participant, subgoal, handout or scanned domain term.
    "c16a5fac6674": "read gold's CHARGE, not gold's ADVICE -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24, approved, then REOPENED by them: the
    # draft kept "cadence rule", and cadence is this course's rubric vocabulary.
    # The four-clause rule quoted in full was likewise entirely domain language
    # (period, frame, consequence, behaviour) and has gone to the course half,
    # leaving what generalises -- a rule about when one feature of an answer
    # contradicts another. Its two bullets lost "period/frame" and "cadence
    # refusal / contingency's direction" too; they are not bold-led and carry no
    # approval of their own. Superseded entry 59634b261520 dropped.
    "70378794d728": "a candidate rule died in the BREAKS column -- user, 2026-09-24",
    # ---- Below: lessons reached after the FULL RESIDUE SCAN, which covers ten
    # identifier classes (item ids, participants, subgoal labels, corpus refs,
    # handout numbers, domain vocabulary, self-references, course names, dates,
    # and the rubric's own 102 slot keys plus 58 deduction codes). All read
    # zero. `verdict`, `confident` and `BLANK` are kept by the user's decision
    # as generic engine vocabulary.
    #
    # Reviewed with the user 2026-09-24. One substitution, a date. "in one
    # pass" rather than a bare deletion, because the sentence must still say
    # the 34 were audited TOGETHER -- the point that follows is that the two
    # halves of that one audit behaved differently. 34/8/21 stay: the majority
    # being merely unnecessary rather than hiding misses IS the lesson.
    "78b46751a6ce": "why the right-and-excluded half gets skipped -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. One deletion, the date; "in a single
    # afternoon" already carries the compression that made the point. Reflowed.
    #
    # This is the rule the whole QC split review turned on. Five identifier
    # classes were missed by hand-written detectors -- participant ids, subgoal
    # labels, self-references, domain vocabulary, rubric slot names -- each
    # invisible to the check written for the one before it, and each reported
    # as "zero references" by a search that only looked for what I had already
    # thought of. The residue scan now runs against the rubric's OWN 102 slot
    # keys and 58 deduction codes rather than a list I typed.
    "000b3d663c0a": "call the prepared reader; do not re-derive it with a regex -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. TWO date removals: the ISO date in the
    # lead, and a bare "09-05" fragment the ISO pattern did not match -- the
    # residue scan now covers MM-DD as well, and both forms read zero. The
    # date cost nothing: "1425 lines shorter than the live module" already
    # says how stale the shadow was, and says it better. Module names and
    # drift counts stay -- they are engine modules, and the counts are the
    # evidence that a shadow can be arbitrarily far behind and still import.
    "d5f2aefb77cd": "what a shadowed module in the scratchpad cost -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. One substitution. "in one day" rather
    # than a plain deletion because "all on <date>" was doing work: it said the
    # failures were CONCURRENT, not spread over months, and that compression is
    # what makes the cost alarming. "Six of seven readable probes VOID" stays --
    # it is the argument for the guard existing at all.
    "247c83dae2b0": "what VOID probes cost before the gate existed -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. One deletion, the date -- safely dropped
    # here because "in one day" is ALREADY in the sentence describing the three
    # edits, so the compression survives without it. Contrast the two entries
    # above, where "all on <date>" was the only thing saying the failures were
    # concurrent and had to be replaced rather than cut. Reflowed.
    "5ca4fd13d2cd": "read gold's charge on every valid cell before wording -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. Claim byte-identical; three changes all
    # consequent on dropping the date. "once" restores the this-happened framing
    # the date carried -- without it the sentence reads as a general tendency,
    # which is exactly the unsupported generality the review caught three times
    # elsewhere. "one day" -> "a single day" only because "one" turned ambiguous
    # against "Three edits" once the sentence opened with the count.
    "f8425a6a1dc8": "the failure a probe catches is REACH -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. Date and the domain term "cadence" go;
    # "once" keeps it a recorded event rather than a general claim. What stays
    # is the whole substance: the two concrete evasions (a numeral spelled out,
    # a preposition swapped) are generic -- any paraphrase detector can be
    # walked past by exactly those -- and "four independent reasons, none of
    # them a bug" is what distinguishes this from "the gate failed". The gate
    # worked as specified, four ways, and still said nothing. Reflowed.
    "ee3cb98e3ae1": "a gate's SILENCE is not a clearance -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. Five removals -- two slot names, two
    # cell ids, and "put-on/taken-off", this course's stimulus taxonomy. The
    # measurement stays whole because it IS the hypothesis: twelve lines cost
    # two cells, twenty lines gave them back. "An unrelated slot" earns its
    # place -- the closing sentence turns on the blocks not mentioning the
    # recovered cells, which the original left the reader to infer.
    #
    # "has been observed repeatedly HERE" is KEPT. 13 bare "here"s remain, ~7
    # of them project-sense; the user ruled sweeping them out of scope. The
    # guide's voice is first-person-experiential throughout ("I told the user",
    # "three nonce classifiers of mine"), and removing them would change the
    # document's character in a way the identifier classes did not.
    "c798bc646cce": "WORKING HYPOTHESIS: the coupling tax scales with VOLUME -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. Only "unwanted behaviour" was genuinely
    # domain here and it goes. "consequence" is RESTORED as ordinary English at
    # the user's direction: this passage is about causal chains, not about the
    # rubric slot, and the draft had swept it only because it sat beside a term
    # that IS domain. The abstraction cost precision -- "a genuinely new
    # element" hedged where the original simply named a category, and left the
    # three-way split vaguer than the rule deserves.
    "b99b0c22dab4": "three kinds of \"and then what follows\" in a reference entry -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. The heaviest transformation in the set,
    # and the passage that most justified the split: it carried TWO
    # {{corpus:...}} references with verbatim student text inline, which is
    # what made the guide unrenderable without $COURSE_DATA.
    #
    # "are near-paraphrases" is the load-bearing substitution. The original
    # SHOWED the two quoted phrases and let the reader see they were nearly
    # identical; with the quotes gone the paragraph must STATE the relation or
    # the lesson collapses -- "a quote is necessary and not sufficient" means
    # nothing unless you know the slot answered wrongly eleven times anyway.
    # "-1" -> "for it": the charge size is this rubric's increment, and the
    # point is only that gold charges AND SAYS SO.
    "a8957056cf1d": "a quote is necessary and not sufficient -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. Two item ids and the constant MATCH_DEF
    # go; the closing sentence is byte-identical. FLAGGED AND ACCEPTED: the
    # original attributed the two halves to DIFFERENT items -- position-beats-
    # content from one, the cost side from another -- so they were independent
    # observations, not one reading interpreted twice. "The cost side:" keeps
    # the two-sidedness but not the independence. Judged not worth restoring:
    # the lesson is the mechanism, and the evidence now sits in the course
    # half. Reflowed.
    "728e1055fab6": "placement cuts both ways -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24 and approved as it stands, declining a
    # proposed tightening. Three item ids go. FLAGGED AND ACCEPTED: "Q6 is not
    # yet migrated" -> "Not every item is migrated" trades a specific
    # outstanding TASK for a general condition, and drops the "yet" that marked
    # it as unfinished work rather than a design choice. "One item is not yet
    # migrated" was offered and not taken. The two operations stay DESCRIBED
    # rather than named, because the point is that two differently-worded
    # questions are one operation and you need both descriptions to see it.
    "1f9b912b43aa": "state a matching rule ONCE -- user, 2026-09-24",
    # The **Qualifies:** enumeration that sat between this entry and the one below
    # was MOVED WHOLE to the course half on the user's decision, not
    # genericised: a bare three-item list of rubric-specific conditions has no
    # surrounding prose to carry meaning, so abstraction degraded it badly
    # ("a second antecedent" -> "a second instance of a repeated element").
    # It was course material in the wrong half, and moving it REMOVED a lesson
    # from the queue rather than adding one.
    #
    # Reviewed with the user 2026-09-24. ONE TOKEN. "Second X" works here where
    # the same abstraction failed in the list above, because this sentence is
    # about the grammatical FORM of gold's ordinals -- a placeholder standing
    # in for a quoted phrase pattern, not carrying an enumeration.
    "5ff9ffe998f6": "gold's ordinals are tallies, not indices -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. Cell id twice and the -1.25 error figure
    # go; the mechanism names stay (PER_ITEM_EXCLUDE, expect_error,
    # CORRECTED_GOLD are engine vocabulary, not course data). The closing line
    # is untouched and is the whole argument: removing the exclusion changed no
    # measurement, only what the denominator was honest about. Reflowed.
    "9fe25f54d59f": "an exclusion on a cell we get WRONG must be removed -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. Cell id and two slot names go; the check
    # name stays. RESTRUCTURED rather than word-swapped -- active to passive --
    # because with the cell id gone the original's "skips those" had no
    # antecedent, the same repair pattern as the stranded pronoun elsewhere.
    # FLAGGED: "verdict/how1 overlap" -> "an overlap between two of its spans"
    # thins the detail; judged acceptable because the lesson is that the
    # exclusion SUPPRESSED THE CHECK, not which spans overlapped. "Faithful and
    # declarable" survives, and it matters: the exclusion was silencing a
    # non-problem while silencing everything else too.
    "0e67edb3803d": "declaring beats excluding; an exclusion silences more -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. ONE TOKEN. Both engine names and the
    # internal quotation survive intact, and the quotation is the lesson in
    # miniature: a stale exclusion does not merely fail to help, it actively
    # misinforms in the expensive direction. "Off-grid gold" stays -- a gold
    # value off the increment grid is a property of scoring schemes generally,
    # not this course's vocabulary.
    "694400d4b3c9": "an exclusion on a cell we get RIGHT must be retested -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. One deletion and an article. The
    # measurement stays because it IS the argument: 56% at nine passes -> 9 of
    # 9. A ceiling that looked like a hard limit across nine passes evaporated
    # when a term got defined, which is exactly why a calendar is the wrong
    # trigger and a CHANGE is the right one. The closing quotation is the
    # payoff and is untouched.
    "04169da3d15d": "the retest trigger is a change, not a calendar -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. Handout number and the definition itself
    # go. THIS LESSON IS THE SPLIT'S OWN RATIONALE stated in the guide: a
    # reference kept the student's words out of the file AND STILL made a
    # student's writing the thing every reader is taught from, and made the
    # page unrenderable without the corpus. That is the case for a generic half
    # carrying no corpus references, which is now true of this document.
    # "A definitional point" is vaguer but loses nothing: the lesson turns on
    # the example being a REAL STUDENT'S SENTENCE, not on what was defined.
    "adf89f0830c0": "invent the example rather than quote a student -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. Four removals in one clause -- cell id,
    # participant number, the item's display name, and the OLX block id, which
    # carried both the course code and the handout number. Everything from "So
    # every later student..." is byte-identical, and that is the whole argument:
    # the harm was never about WHICH participant or WHICH item. "Twenty-five
    # lines BELOW" stays because the proximity IS the finding -- a quote on a
    # distant page is a disclosure; twenty-five lines above the box it is a
    # prompt. Note the irony the edit resolves: the lesson warns that naming a
    # participant beside their answer creates a re-identification context, and
    # the original did exactly that. Reflowed.
    "79e742e46558": "the quote came from a question in that same handout -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. Removes THE LAST CORPUS REFERENCE in the
    # guide -- a {{corpus:...}} span carrying verbatim student text, sitting
    # inside a lesson about not exposing student text. The rule and its test are
    # byte-identical. FAIR TRADE, not a clean win: the original let the reader
    # SEE the domain mismatch by showing both sides, and "draws on a different
    # domain" states it instead. Judged actionable because the next sentence
    # supplies the operational test -- does it pattern the answer to its own
    # question? The concrete pair is in the course half.
    "2d720e9326e0": "check the provenance of a replacement, not just the words -- user, 2026-09-24",
    # Reviewed with the user 2026-09-24. THREE WORDS -- the handout reference. The
    # scanner path stays (engine-side; a rule telling you to scan is useless
    # without naming what to scan with), and "three candidates ... all three
    # clean" stays because it sets the standard: generate several, verify each,
    # and let the clean result license the choice. Reflowed.
    #
    # LAST OF THE QUALITY_CONTROL SPLIT. Every lesson in this block was
    # reviewed one at a time with the user.
    "505838e7c88a": "check an invented replacement for collisions first -- user, 2026-09-24",
    # APPROVED 2026-09-24 ON THE USER'S EXPLICIT INSTRUCTION ("fix the editguard
    # quality control path"), and it is a PATH correction, not a claim: goal H
    # moved `editguard.py` into `scoring/tools/`, so the lesson's one command
    # named a file that is no longer there. The lead's sha changed because the
    # lead holds the command; the claim it makes -- that removing a name is one
    # declared command per name, with no bulk regenerate -- is unchanged.
    #
    # THE GATE WAS NOT WORKED AROUND WHILE IT WAITED. The correction was made and
    # REVERTED once, and the doc carried the stale path until the user agreed,
    # because a lesson is approved by the sha of its prose precisely so it cannot
    # be reworded without agreement, and self-approving would defeat that.
    "c4ccef24f98e": "the editguard command's path, after tools/ -- user, 2026-09-24",
    # Keyed on the LEAD PARAGRAPH, which is what _lesson_leads hashes: the lead
    # carries the claim, so editing it lapses the approval while re-wrapping the
    # supporting paragraphs does not.
    # ---- SECTION 6a, FIVE LESSONS, approved 2026-09-16 on the user's explicit
    # instruction, with two conditions they attached and which were applied
    # BEFORE these shas were taken:
    #   * a claim naming a RETIRED check must say so, so it does not read as a
    #     statement about anything still running;
    #   * the "137 student sentences" figure is dated to its episode, with the
    #     current measurement (27 distinctive 4-grams, control 2107) beside it.
    "19732406f345": "section 6a, Trusting an instrument — approved 2026-09-16",
    "a5d16755c6c6": "a test that cannot fail reads exactly like a test that "
                    "keeps passing — approved 2026-09-16",
    "0fa976bebb1f": "the `check_maps_tables_are_attached` tautology — approved "
                    "2026-09-16, reworded first to record that the check has "
                    "since been RETIRED. The earlier sha b25d9743f409 lapsed on "
                    "that rewording, which is the mechanism working",
    "366591905758": "a verifier must not share the scrubber's rule — approved "
                    "2026-09-16. Its lead is the heading, so dating the 137 "
                    "figure in the body did NOT lapse it; the claim is unchanged",
    "1aede813577a": "a count that holds steady can be hiding a swap — approved "
                    "2026-09-16",
    # ---- SECTION 6b, TWO LESSONS, approved 2026-09-16 on the user's explicit
    # instruction. The evidence is reproduced, not reported: the 26-of-26 green
    # scorer run on port 8899 was re-run and the UI on that port was confirmed
    # unable to boot at all, so the same green result would have come from a
    # release whose every page read "Failed to start."
    "ca23974ab235": "section 6b, a check that compares bytes cannot tell you "
                    "the thing runs — approved 2026-09-16",
    "fdffdc4d812f": "ask of each instrument what it would say if the thing were "
                    "broken; if the answer is 'the same as now' it is a "
                    "neutrality check, not an acceptance check — approved "
                    "2026-09-16",
    # ---- SECTION 6c, FIVE LESSONS, approved 2026-09-16 on the user's explicit
    # instruction. The section's figures were DATED to their episode first, at
    # the user's earlier direction, with the current measurement beside them.
    #
    # Two of these shas differ from the ones first shown, because that dating
    # edited their LEADS and so lapsed them -- the mechanism behaving exactly as
    # designed, and worth leaving on the record rather than tidying away.
    "8b64eea3c49a": "section 6c, a scan can only find what its reference set "
                    "contains — approved 2026-09-16",
    "c531700cb2c0": "the reference set was the defect: a table seeded from our "
                    "own citations can only ever confirm that what we already "
                    "knew about is gone — approved 2026-09-16",
    "8fc7967231d8": "name the reference set; run the positive control; ask which "
                    "direction the search runs — approved 2026-09-16",
    "9b86053c4670": "four words is the working threshold, not eight — approved "
                    "2026-09-16 (lead re-taken after the figures were dated)",
    "6f1648e9d943": "judge a four-gram by its CONTENT WORDS, >=2 required, with "
                    "the function words staying IN the match — the user's rule, "
                    "approved 2026-09-16. The lead now also carries the "
                    "correction that a NUMERAL is not a content word, which cost "
                    "8 SyntaxErrors and 108 generator states before it was found",
    # ---- SECTION 6d, TEN LESSONS, approved 2026-09-16 on the user's explicit
    # instruction, after a split sentence in the section was repaired -- which
    # re-flowed it and lapsed every sha first shown. The section is the standing
    # procedure for quoting a student in an .olx, and its answer is usually NO.
    "291b4bce493a": "section 6d, quoting a student in an .olx — approved 2026-09-16",
    "a1b05c20feec": "first ask whether the example can be invented instead — "
                    "approved 2026-09-16",
    "cadec605120f": "usually it can, and that is the fix — approved 2026-09-16",
    "97c9e68f0548": "the quote came from a question in the SAME handout: PR/p1 "
                    "answered `bmod_h2_pr`, whose box sits 25 lines below the "
                    "instructions that quoted it. The user found this; it is why "
                    "the section exists in its present form. Approved 2026-09-16",
    "da9896cd4107": "check the PROVENANCE, not just the words: which question "
                    "did the sentence answer, and is the reader about to answer "
                    "it — approved 2026-09-16",
    "fe5c1050c54b": "check an invented replacement for collisions before using "
                    "it; a near-paraphrase is not a replacement — approved "
                    "2026-09-16",
    "92cb2525cbc2": "the four-step procedure when a real quotation is required: "
                    "make_ref never by hand, declare corpus_data, export the "
                    "spans, lower the budget — approved 2026-09-16",
    "4dfa9c6b517a": "what the mechanism costs: the page cannot render without "
                    "the corpus, references collide with attribute grammars, and "
                    "two resolvers must agree — approved 2026-09-16",
    "81d3496d4056": "the rule in one line — approved 2026-09-16",
    "c9030d30b0e0": "a reference is for text that must be exact and is somebody "
                    "else's; everything else should be invented, and an invented "
                    "example is checked against the corpus before it is trusted "
                    "— approved 2026-09-16",
    "e7b934bfa4f1": "name the cell and the slot, not the count — approved "
                    "2026-09-04, after fourteen slot figures in open goals were "
                    "left standing by one instrument fix",
    "dc4dba1edfb5": "a gate's silence is not a clearance — approved 2026-09-04, "
                    "with the closing clause reworded to 'not ... by itself as "
                    "definitive proof' at the user's direction",
    # NINETEEN APPROVED 2026-09-12, on the user's explicit instruction, after
    # `guide.py --renumber --write` was run to fix the ordering drift the
    # structure check reported (section 2 ran `2a0 a b c ... l`, and under the
    # ordering policy a SHORTER suffix ranks first, so `2a0` belongs last).
    #
    # EIGHTEEN OF THE NINETEEN ARE LABEL CHURN, NOT NEW CLAIMS. The renumber
    # shifted every section-2 label by one place (2a0->2a, then 2a->2b ... 2l->2m)
    # and rewrote the §-citations inside five lesson paragraphs to match. The
    # lead-paragraph sha covers the label as well as the claim, so each lapsed
    # mechanically. VERIFIED BEFORE ASKING: 21 sections before and after, the
    # TITLE SEQUENCE identical, no title text changed, and all 95 genuine guide
    # citations in the tree still resolve to the SAME section title they did
    # before -- checked by resolving each citation against the committed guide
    # and the working one and comparing what it lands on, not by trusting the
    # tool's own report.
    #
    # ONE IS A REAL REWORD and is named here so the approval is not silent about
    # it: `3a02295a18f1`, the PRE-REGISTERED SET lesson, which cited
    # `NAMED_FALSIFIERS` as if it were a live identifier. It never was -- it was
    # a literal a throwaway Q4c probe script typed, which is the lesson's own
    # point -- and the structure check flags a backticked name that exists
    # nowhere in the tree. Reworded to "its own falsifier set"; the claim is
    # unchanged.
    #
    # THE INTERACTION IS WORTH FIXING RATHER THAN RE-APPROVING EVERY TIME: the
    # structure check tells you to run --renumber, and running it lapses every
    # lesson it touches. Making the lead sha label-insensitive would end that,
    # on the same reasoning as `_behaviour_src` for scorer_sha.
    "4e0888720473": "## 2a. PROBE BEFORE YOU SWEEP — label only (was 2a0)",
    "8e5dc027cff1": "## 2b. TRY THE STRUCTURAL FIX FIRST — label only (was 2a)",
    "1d2092b2f604": "## 2c. PROFILE THE ERRORS BY SLOT — label only (was 2b)",
    "21e723c6fdc6": "## 2d. REPORT THE SPREAD — label only (was 2c)",
    "140ef0130dd9": "## 2e. READ WHAT IS ALREADY RECORDED — label only (was 2d)",
    "459948c42ccc": "## 2f. EVERY WRONG CELL HAS AN OWNER — label only (was 2e)",
    "b957d13c0a15": "## 2g. A python/OLX DIFFERENCE IS NOT YET A DIVERGENCE — "
                    "label only (was 2f)",
    "d5a65db97ec8": "## 2h. SPEND NOTHING ON WHAT A FREE CHECK CAN SETTLE — "
                    "label only (was 2g)",
    "21d6caf0f291": "## 2i. RE-READ EVERY CELL A SUBGOAL OWNS — label only (was 2h)",
    "fac2991aa726": "## 2j. A SWEEP DEFAULTS TO python + olx — label only (was 2i)",
    "55a254255bc3": "## 2k. KNOW WHICH SOURCE YOU CONSULTED — label only (was 2j)",
    "038a4c230875": "## 2l. VALIDATE A CANDIDATE RULE AGAINST EVERY VALID CELL — "
                    "label only (was 2k)",
    "67780d2652b6": "## 2m. A GATE'S REFUSAL IS INFORMATION — label only (was 2l)",
    "1e692480d251": "and do not answer it with a regex over the entry's prose — "
                    "unchanged claim, its §-citation renumbered",
    "ee82bc200e36": "GATES rest on a smaller sample — unchanged claim, its "
                    "§-citation renumbered",
    "4d5c09fdf8af": "ENFORCED, not advised — unchanged claim, its §-citation "
                    "renumbered",
    "4f85adc3eac0": "why it is a check and not a procedure — unchanged claim, "
                    "its §-citation renumbered",
    "09319c21e55c": "and the cheapest check of all is reading — unchanged claim, "
                    "its §-citation renumbered",
    "3a02295a18f1": "a pre-registered set is a classifier too — THE ONE REAL "
                    "REWORD: dropped the phantom identifier `NAMED_FALSIFIERS`, "
                    "which named a throwaway probe's literal and existed nowhere "
                    "in the tree; the claim is unchanged",
}


def _lesson_leads(text: str) -> dict[str, str]:
    """The guide's LESSONS, by sha of their prose.

    A lesson in this document is a paragraph whose first line opens in bold --
    that is the house style for a claim the reader is meant to act on -- or a
    section heading. Both are what "adding a lesson" means; re-wrapping a
    paragraph or fixing a figure inside one is not, and must not trip the check.
    """
    body = re.sub(r"```.*?```", "", text, flags=re.S)
    out: dict[str, str] = {}
    for para in body.split("\n\n"):
        s = para.strip()
        if not s:
            continue
        if s.startswith("**") or re.match(r"^#{2,3} ", s):
            norm = " ".join(s.split())
            out[hashlib.sha256(norm.encode()).hexdigest()[:12]] = norm[:88]
    return out


def unapproved_lessons() -> list[str]:
    """Lessons present in the working guide that are not in HEAD and not approved.

    The comparison is against the COMMITTED guide, so this asks exactly the
    question the instruction asks: is this session adding a lesson nobody agreed
    to? Editing an existing one shows up too, because the sha changes -- which is
    intended, since a reworded claim is a different claim.
    """
    try:
        # `HEAD:./NAME` -- the `./` makes git resolve the path relative to CWD.
        # Without it git resolves from the REPO ROOT, the guide is one directory
        # down, and `git show` returns nothing with a non-zero code. The first
        # version did that and every lesson in the file looked new: 144 findings
        # if the returncode had been ignored, and a silent clean because it was
        # not. Either way the check said nothing true.
        # THE PATH FOLLOWS THE FILE. `cwd=HERE` with a literal name was right
        # while the guide sat beside this module; the day it moved to the rubric
        # component, `HEAD:./QUALITY_CONTROL.md` still resolved from `scoring/`
        # only because the move was UNCOMMITTED. On the next commit git would
        # have returned non-zero, this would have returned `[]`, and the check
        # would have gone silent exactly when the file moved -- an empty result
        # reading as a clean one, which is the failure this project keeps
        # meeting. Resolved from the guide's own directory instead.
        guide = _guide()
        head = subprocess.run(["git", "show", f"HEAD:./{guide.name}"],
                              cwd=str(guide.parent), capture_output=True,
                              text=True, timeout=30)
        if head.returncode != 0:
            # ACROSS A RENAME. The guide moved to the rubric component and the
            # move is not committed, so its new path is not in HEAD -- but the
            # committed content is, under the old path. Refusing here would
            # drop the comparison for exactly as long as a move is in flight,
            # which is when a lesson is most likely to slip in unnoticed. Find
            # it in HEAD by NAME instead; one match is unambiguous.
            # `--full-tree`, because `ls-tree` otherwise scopes to the CWD's
            # path inside the tree -- and the CWD is the directory that does
            # not exist in HEAD, so the listing came back empty and the
            # fallback found nothing.
            listing = subprocess.run(
                ["git", "ls-tree", "-r", "--full-tree", "--name-only", "HEAD"],
                cwd=str(guide.parent), capture_output=True, text=True, timeout=30)
            # THE TWO HALVES SHARE A BASENAME, so matching on the name alone
            # finds both and "exactly one match" refuses. The SPECIFIC half is
            # a different document -- diffing against it would report every
            # generic lesson as new -- so it is excluded.
            #
            # BY DIRECTORY, NOT BY ITS CURRENT PATH, and that distinction is the
            # whole of a defect measured on 2026-09-26. The exclusion named
            # `specific_path(...)` exactly; HEAD holds where the specific half
            # was COMMITTED. Consolidating the QC documents moved it one level
            # down, the old committed path no longer equalled the new resolved
            # one, both halves survived the filter, and "exactly one match"
            # refused -- reporting the guide's history as unreadable when the
            # only thing that had happened was a move. A fallback that exists
            # BECAUSE the working path is absent from HEAD cannot then assume
            # any other path still agrees with HEAD.
            #
            # The course's location is the stable fact: the specific half lives
            # somewhere beneath it, and the generic half never does.
            import compose_docs as _cd
            import paths as _pg
            top = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=str(guide.parent), capture_output=True,
                text=True, timeout=30).stdout.strip()
            course = _os.path.relpath(str(_pg.roots().location), top)
            hits = [p for p in listing.stdout.split("\n")
                    if p.rsplit("/", 1)[-1] == guide.name
                    and not p.startswith(course.rstrip("/") + "/")]
            if listing.returncode == 0 and len(hits) == 1:
                head = subprocess.run(["git", "show", f"HEAD:{hits[0]}"],
                                      cwd=str(guide.parent), capture_output=True,
                                      text=True, timeout=30)
        if head.returncode != 0:
            # NOT SILENCE. "I could not read the committed guide" and "nothing
            # was added" are different answers, and only one of them is safe to
            # print as a clean check.
            return [f"the lesson-approval check could not read the committed "
                    f"guide at {guide.parent}/{guide.name}: git show exited "
                    f"{head.returncode}. A guide whose history cannot be read "
                    f"cannot be checked for unapproved lessons, which is not "
                    f"the same as having none."]
        before = _lesson_leads(head.stdout)
    except Exception as e:
        return [f"the lesson-approval check could not read the committed guide: "
                f"{type(e).__name__}: {e}"]
    try:
        now = _lesson_leads(GUIDE.read_text())
    except Exception as e:
        # NOT `return []`. The first version swallowed a NameError here and
        # reported a clean guide -- the check was green by construction and its
        # own approval table was never consulted. A check that cannot run says so.
        return [f"the lesson-approval check could not run: "
                f"{type(e).__name__}: {e}"]
    out = []
    for sha, lead in now.items():
        if sha in before or sha in LESSONS_APPROVED:
            continue
        out.append(
            f"{GUIDE.name} adds an UNAPPROVED lesson: \"{lead}\" — the guide is "
            f"the project's standing instructions, so a lesson goes in only with "
            f"the user's agreement. Ask, then record it in "
            f"guide.LESSONS_APPROVED as \"{sha}\". (A reworded lesson lapses its "
            f"approval on purpose: the sha changes because the claim changed.)")
    return out


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
