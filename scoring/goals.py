"""Structural checks and label allocation for GOALS.md.

WHY THIS IS NOT guide.py. Both files carry labelled entries, but the labels mean
opposite things. A guide section's label is its POSITION, so it is derived from
document order and renumbering is the repair. A goal's label is its NAME: `Q22`
is cited in commits, in memory notes, in other subgoals' prose and in
QUALITY_CONTROL.md, and it must mean the same entry forever. Renumbering GOALS.md
would be the defect, not the fix.

So the automation here is the other half of the same idea: labels are ALLOCATED
rather than guessed (`--next`), and the things that would quietly corrupt the
record are refused rather than trusted to care:

    a DUPLICATE label      two entries answering to one citation
    a DANGLING citation    "subgoal Q40" where no Q40 exists
    a DELETED entry        a goal that was in the committed file and is now gone
    an UNAPPROVED closure  `- [ ]` -> `- [x]` without the user agreeing

That last one is GOALS.md's own standing rule -- "NEVER CLOSE A GOAL WITHOUT
ASKING THE USER FIRST" -- which was broken in this project by closing a subgoal
inside a recording step. A rule stated in the file it governs and enforced
nowhere is a rule that depends on whoever reads it last.

    python3 goals.py --check          duplicates, citations, deletions, closures
    python3 goals.py --next Q         the next free label, so ids are not guessed
    python3 goals.py --list           labels with their state, in document order
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
GOALS = HERE / "GOALS.md"

# `- [ ] Q22. **title**` / `- [x] E30. **title**`. A CAPITAL prefix and an
# INTEGER, unlike the guide's lowercase-letter suffixes -- the two files are
# deliberately not interchangeable.
ENTRY = re.compile(r"^- \[([ x])\] ([A-Z]+)(\d+)\. (.*)$", re.M)

# How a goal is cited. The `subgoal `/`goal ` prefix is REQUIRED, and that is not
# pedantry: `Q1`, `Q2`, `Q4a` are also RUBRIC ITEM ids, so a bare `Q1` in prose
# is usually an item and not a subgoal. Requiring the word is what makes a
# citation check possible on this corpus at all.
CITE = re.compile(r"\b(?:sub)?goal ([A-Z]+)(\d+)\b")

# CLOSURES THE USER HAS AGREED TO, by label. GOALS.md's own first rule is that a
# goal is never closed without asking; this is where the asking is recorded.
# Re-opening and re-closing needs a fresh entry, because the second closure is a
# second decision.
CLOSURES_APPROVED: dict[str, str] = {}


def entries(text: str) -> dict[str, tuple[str, str]]:
    """label -> (state, title), in document order. state is ' ' or 'x'."""
    out: dict[str, tuple[str, str]] = {}
    for m in ENTRY.finditer(text):
        out[f"{m.group(2)}{m.group(3)}"] = (m.group(1), m.group(4)[:88])
    return out


def _committed() -> str | None:
    try:
        r = subprocess.run(["git", "show", "HEAD:./GOALS.md"], cwd=HERE,
                           capture_output=True, text=True, timeout=30)
        return r.stdout if r.returncode == 0 else None
    except Exception:
        return None


def next_label(prefix: str = "Q") -> str:
    """The next free label for a prefix, so a new subgoal's id is not guessed.

    Allocated from the MAXIMUM in use rather than the first gap: a retired number
    must not be reissued, because citations of it survive in commits and memory
    long after the entry is closed.
    """
    text = GOALS.read_text()
    used = [int(m.group(3)) for m in ENTRY.finditer(text) if m.group(2) == prefix]
    return f"{prefix}{(max(used) + 1) if used else 1}"


def check() -> list[str]:
    """Everything about GOALS.md's entries that a program can settle."""
    bad: list[str] = []
    try:
        text = GOALS.read_text()
    except OSError as e:
        return [f"{GOALS.name} cannot be read: {type(e).__name__}: {e}"]

    # 1. DUPLICATES. Two entries answering to one citation.
    seen: dict[str, str] = {}
    for m in ENTRY.finditer(text):
        label = f"{m.group(2)}{m.group(3)}"
        if label in seen:
            bad.append(
                f"{GOALS.name}: duplicate goal label {label} — '{seen[label]}' and "
                f"'{m.group(4)[:60]}'. Every citation of {label} is now ambiguous; "
                f"`python3 goals.py --next {m.group(2)}` allocates a free one")
        else:
            seen[label] = m.group(4)[:60]

    now = entries(text)

    # 2. DANGLING CITATIONS, across the tree.
    for path in sorted(list(HERE.glob("*.md")) + list(HERE.glob("*.py"))):
        if path.name == "goals.py":
            continue
        try:
            src = path.read_text()
        except OSError:
            continue
        for n, line in enumerate(src.splitlines(), 1):
            for pre, num in CITE.findall(line):
                if f"{pre}{num}" not in now:
                    bad.append(
                        f"{path.name}:{n} cites subgoal {pre}{num}, which is not an "
                        f"entry in {GOALS.name} — the label is wrong, or the entry "
                        f"was deleted rather than closed")

    before_text = _committed()
    if before_text is None:
        return bad
    before = entries(before_text)

    # 3. DELETIONS. A goal is closed, never removed: its number is cited
    #    elsewhere and its record is the reason the work is not redone.
    for label, (_state, title) in before.items():
        if label not in now:
            bad.append(
                f"{GOALS.name}: goal {label} ('{title[:60]}') was in the committed "
                f"file and is GONE. Goals are closed with `- [x]`, never deleted — "
                f"the entry is what stops the work being redone, and its number is "
                f"cited elsewhere. Restore it")

    # 4. UNAPPROVED CLOSURES. GOALS.md's own first rule, enforced.
    for label, (state, title) in now.items():
        was = before.get(label)
        if was and was[0] == " " and state == "x" and label not in CLOSURES_APPROVED:
            bad.append(
                f"{GOALS.name}: goal {label} ('{title[:60]}') is being CLOSED and the "
                f"user has not agreed. This file's own first rule is never to close "
                f"a goal without asking. Ask, then record it in "
                f"goals.CLOSURES_APPROVED as \"{label}\"")
    return bad


def main(argv: list[str]) -> int:
    if "--next" in argv:
        i = argv.index("--next")
        print(next_label(argv[i + 1] if len(argv) > i + 1 else "Q"))
        return 0
    if "--list" in argv:
        for label, (state, title) in entries(GOALS.read_text()).items():
            print(f"  [{state}] {label:5} {title[:70]}")
        return 0
    bad = check()
    if bad:
        print("\n".join(f"  ! {b}" for b in bad))
        return 1
    e = entries(GOALS.read_text())
    op = sum(1 for s, _t in e.values() if s == " ")
    print(f"  {GOALS.name}: {len(e)} goals ({op} open, {len(e) - op} closed), "
          f"labels unique, citations resolve, none deleted or newly closed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
