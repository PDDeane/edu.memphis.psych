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

import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GUIDE = HERE / "QUALITY_CONTROL.md"

# `## 2a. TITLE` / `## 2b2. TITLE` / `## 3. TITLE`. The label is what other files
# cite, so it is the thing that must stay unique and ordered.
HEAD = re.compile(r"^(#{2,3}) (\d+)([a-z]\d?|[a-z]?)\. (.+)$", re.M)

# How the rest of the tree cites a section. Kept deliberately narrow: a bare "2c"
# in prose is not a citation, and rewriting one would corrupt a sentence.
REF = re.compile(r"(§ ?|QUALITY_CONTROL(?:\.md)? |[Ss]ection )(\d+[a-z]\d?)\b")

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


def _letters():
    """a, b, c ... z, then aa, ab ... — enough for any section this will see."""
    import string
    for c in string.ascii_lowercase:
        yield c
    for a in string.ascii_lowercase:
        for b in string.ascii_lowercase:
            yield a + b


def plan(text: str) -> dict[str, str]:
    """old label -> new label, deriving letters from document order.

    A parent section (`2`) keeps its number. Its subsections are lettered in the
    order they physically appear, which is the whole point: the label stops being
    an assertion about position and becomes a reading of it.
    """
    out: dict[str, str] = {}
    per_parent: dict[str, list[str]] = {}
    for label, _title, _h in headings(text):
        m = re.fullmatch(r"(\d+)([a-z]\d?)?", label)
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
        m = re.fullmatch(r"(\d+)([a-z]\d?)?", label)
        if m and m.group(2):
            by_parent.setdefault(m.group(1), []).append(m.group(2))
    for parent, suffixes in by_parent.items():
        if suffixes != sorted(suffixes):
            bad.append(
                f"{GUIDE.name}: section {parent}'s subsections are out of order — "
                f"{' '.join(suffixes)}. Renumber, or move the sections")

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
