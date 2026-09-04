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
CLOSURES_APPROVED: dict[str, str] = {
    "Q37": "closed 2026-09-04 on the user's confirmation. Its three items were "
           "done, and its WARNING became structural rather than narrative: "
           "stale_slot_claims dates every slot figure in an open goal against "
           "the profile that produced it, so closing the entry no longer loses "
           "the knowledge that a figure may predate its instrument",
}


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
    if "--slot-claims" in argv:
        s = stale_slot_claims()
        print("\n".join(f"  ! {x}" for x in s) if s
              else "  no open goal quotes a slot figure older than the instrument")
        return 1 if s else 0
    bad = check()
    if bad:
        print("\n".join(f"  ! {b}" for b in bad))
        return 1
    e = entries(GOALS.read_text())
    op = sum(1 for s, _t in e.values() if s == " ")
    print(f"  {GOALS.name}: {len(e)} goals ({op} open, {len(e) - op} closed), "
          f"labels unique, citations resolve, none deleted or newly closed")
    return 0



# ------------------------------------------------- slot claims vs the instrument

# THE FUNCTIONS A SLOT-LEVEL FIGURE IS COMPUTED THROUGH. A claim written before
# any of these last changed was produced by a different instrument, and the two
# were unlinked until 2026-09-04: the knowledge that a figure came from a BLIND
# profile lived as narrative in one subgoal entry, which meant it would die when
# that entry closed. This is the `prompt_sha` treatment applied to prose --
# exactly the STALE PROMPT idea, for claims about slots instead of items.
_PROFILE_TOKENS = ("_our_failing_slots", "_charging_slots", "_gold_nameable_slots")

# A count, in the forms this file actually uses.
_COUNT = re.compile(r"\b\d+\s*(?:of|/)\s*\d+\b|\b\d+ refusals?\b|\b\d+%")

# An era record, marked as one on purpose. The same vocabulary
# `measured._HISTORICAL` uses, so an author marks a figure historical once and
# both checks honour it.
_HISTORICAL = re.compile(
    r"\b(was|were|had been|previously|prior|before|earlier|then|originally|"
    r"superseded|stale|no longer|as measured|as filed|at the time)\b", re.I)


def _slot_keys() -> frozenset:
    """Every real slot key in the corpus, from the OLX sheets.

    Restricting to REAL keys is what keeps this from firing on every backticked
    identifier: `error_profile` and `sweep_summary` are function names, not
    slots, and a claim mentioning them is not a slot-level claim.
    """
    try:
        import agreement as A
        import agreement_app as AA
        import olx_prompts as O
    except Exception:
        return frozenset()
    keys: set = set()
    for item, job in AA.JOBS.items():
        try:
            spec = A.load_action(f"bmod_handout{job['handout']}.olx", O.ACTION[item])
        except Exception:
            continue
        keys |= {s["key"] for s in spec.get("slots") or []}
    return frozenset(k for k in keys if len(k) > 4)


def stale_slot_claims(instrument_at: int | None = None) -> list[str]:
    """Slot-level figures in OPEN goals that predate the instrument that made them.

    A figure like "34 refusals, 71% precision" is a claim about what a program
    computed. When that program changes, the claim does not -- and nothing linked
    the two, so the only record of "these numbers came from a blind profile" was
    a paragraph inside one subgoal. Paragraphs close.

    Scoped and exempted so it stays readable:
      OPEN entries only -- a closed goal's figures are its record, not a claim
        about the present, and 42 of the corpus's 49 slot claims are in closed
        entries.
      HISTORICAL lines are skipped, on the marker vocabulary `prose_claims`
        already uses, so a figure can be kept deliberately as an era record.
      REAL SLOT KEYS only, read from the OLX sheets rather than pattern-matched,
        so a backticked function name is not mistaken for a slot.

    The honest alternative to this check is not to write the numbers: prose that
    names a CELL and a SLOT cannot go stale, prose that quotes a count always
    can. This exists for the ones already written.
    """
    keys = _slot_keys()
    if not keys:
        return ["cannot read the corpus's slot keys, so slot claims cannot be dated"]
    if instrument_at is None:
        stamps = []
        for tok in _PROFILE_TOKENS:
            try:
                r = subprocess.run(["git", "log", "-1", "--format=%at", "-S", tok,
                                    "--", "measured.py"], cwd=HERE,
                                   capture_output=True, text=True, timeout=30)
                if r.returncode == 0 and r.stdout.strip():
                    stamps.append(int(r.stdout.split()[0]))
            except Exception:
                pass
        if not stamps:
            return []
        instrument_at = max(stamps)

    try:
        bl = subprocess.run(["git", "blame", "--line-porcelain", "GOALS.md"],
                            cwd=HERE, capture_output=True, text=True, timeout=120)
        if bl.returncode != 0:
            return []
    except Exception:
        return []

    lines: list[tuple[int, str]] = []          # (author_time, text)
    at = 0
    for row in bl.stdout.splitlines():
        if row.startswith("author-time "):
            at = int(row.split()[1])
        elif row.startswith("\t"):
            lines.append((at, row[1:]))

    out: list[str] = []
    label, state = None, "x"
    for n, (when, text) in enumerate(lines, 1):
        m = ENTRY.match(text)
        if m:
            label, state = f"{m.group(2)}{m.group(3)}", m.group(1)
        if state != " " or label is None:
            continue                            # closed entry, or preamble
        if when >= instrument_at:
            continue
        if _HISTORICAL.search(text):
            continue
        named = [k for k in re.findall(r"`([a-z][a-z0-9_]+)`", text) if k in keys]
        if not named or not _COUNT.search(text):
            continue
        out.append(
            f"GOALS.md:{n} (goal {label}) quotes a slot figure for "
            f"{', '.join(named[:3])} that was written BEFORE the slot profile last "
            f"changed, so it is not a figure the current instrument produced: "
            f"\"{text.strip()[:70]}\". Re-derive it with `measured.py --errors "
            f"<item> <artifact>` or `--refusals <item>`, mark the line historical "
            f"if it is meant as an era record, or drop the count and name the cell "
            f"and slot instead")
    return out

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
