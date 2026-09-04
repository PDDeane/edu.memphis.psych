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

    python3 guide.py --check                 structure + references + identifiers
    python3 guide.py --renumber              dry run: print the mapping
    python3 guide.py --renumber --write      apply it, rewriting references too
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GUIDE = HERE / "QUALITY_CONTROL.md"

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
        [p for p in HERE.glob("*.py") if p.name != "guide.py"]
        + list(HERE.glob("*.md"))
        + list((HERE.parent / "psychology").glob("*.olx"))
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
        text = GUIDE.read_text()
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
                f"ambiguous; run `python3 guide.py --renumber --write`")
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
                f"`python3 guide.py --renumber --write`, or move the sections")

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
    """Derive labels from document order; rewrite headings and every citation."""
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
               f"({len(headings(GUIDE.read_text()))} headings, references and "
               f"identifiers resolve)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))


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
    # Keyed on the LEAD PARAGRAPH, which is what _lesson_leads hashes: the lead
    # carries the claim, so editing it lapses the approval while re-wrapping the
    # supporting paragraphs does not.
    "e7b934bfa4f1": "name the cell and the slot, not the count — approved "
                    "2026-09-04, after fourteen slot figures in open goals were "
                    "left standing by one instrument fix",
    "dc4dba1edfb5": "a gate's silence is not a clearance — approved 2026-09-04, "
                    "with the closing clause reworded to 'not ... by itself as "
                    "definitive proof' at the user's direction",
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
        head = subprocess.run(["git", "show", "HEAD:./QUALITY_CONTROL.md"],
                              cwd=HERE, capture_output=True, text=True,
                              timeout=30)
        if head.returncode != 0:
            return []                      # no git, or no committed guide yet
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
