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

import json
import pathlib
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import compose_docs
import paths as _p7   # J-7b: this course's handout file names

HERE = Path(__file__).resolve().parent

# THE COMPOSED DOCUMENT, not the generic half beside this module. GOALS.md is split:
# the rules that would govern any course's ledger stay in `scoring/`, and THIS
# course's 112 entries live with the course. Every reader opens the composed copy,
# so this module sees the whole document exactly as it always did -- which is why
# the split needed no change to any of the checks below.
GOALS = Path(compose_docs.composed_path("GOALS.md"))

# WHERE THE ENTRIES ARE VERSIONED, which is no longer where this module lives. The
# deletion check below compares today's entries against the committed ones, and it
# must ask git about the half that HOLDS entries; asking about the generic half
# would compare an empty set against an empty set and pass while a goal vanished.
_TRACKED = Path(compose_docs.specific_path("GOALS.md"))

# `- [ ] Q22. **title**` / `- [x] E30. **title**`. A CAPITAL prefix and an
# INTEGER, unlike the guide's lowercase-letter suffixes -- the two files are
# deliberately not interchangeable.
ENTRY = re.compile(r"^- \[([ x])\] ([A-Z]+)(\d+)\. (.*?)(?:\s*<!--@\d{4}-\d\d-\d\d-->)?$", re.M)

# THE DATE AN ENTRY WAS WRITTEN, carried IN the entry rather than inferred from git.
# `<!--@YYYY-MM-DD-->` at the end of an entry line: invisible in rendered markdown,
# and excluded from the title by the `ENTRY` pattern above.
#
# WHY IT EXISTS. Two readers -- this module and `measured` -- dated entries with
# `git blame --line-porcelain GOALS.md`, which works only while the file is TRACKED.
# That made the record's own history a dependency on its STORAGE, and the file was
# then moved out of the repository, as the override log already had been. The
# stamps were harvested from blame in the moment before that move, which was the
# only moment they could be; `measured`'s own comment states what they were bought
# against: "no blame available means no exemption, which errs toward reporting".
#
# THE FILE IS TRACKED AGAIN, 2026-09-26, filed with its three fellow halves in
# `<course>/<rubric id>_qc/` on the user's decision. Blame is therefore available once more.
# THAT DOES NOT MAKE THE STAMPS REDUNDANT, and they are not being removed: their
# whole point is that a date carried IN the record does not depend on where the
# record is stored, and this move is the second storage change in a month. An
# entry written while the file was outside git has no blame to fall back on, so
# the stamps are the only complete source and remain the primary one.
#
# BLAME REMAINS THE FALLBACK, so the two agree while both are available and nothing
# breaks on an unstamped line. The stamps were harvested FROM blame while the file
# was still tracked, which was the only moment they could be.
_STAMP = re.compile(r"\s*<!--@(\d{4}-\d\d-\d\d)-->\s*$")


def entry_dates(text: str | None = None) -> dict:
    """{label: 'YYYY-MM-DD'} for every entry carrying a stamp."""
    src = text if text is not None else GOALS.read_text()
    out = {}
    for line in src.splitlines():
        m = ENTRY.match(line)
        s = _STAMP.search(line)
        if m and s:
            out[f"{m.group(2)}{m.group(3)}"] = s.group(1)
    return out


# How a goal is cited. The `subgoal `/`goal ` prefix is REQUIRED, and that is not
# pedantry: `Q1`, `Q2`, `Q4a` are also RUBRIC ITEM ids, so a bare `Q1` in prose
# is usually an item and not a subgoal. Requiring the word is what makes a
# citation check possible on this corpus at all.
CITE = re.compile(r"\b(?:sub)?goal ([A-Z]+)(\d+)\b")

# CLOSURES THE USER HAS AGREED TO, by label. GOALS.md's own first rule is that a
# goal is never closed without asking; this is where the asking is recorded.
# Re-opening and re-closing needs a fresh entry, because the second closure is a
# second decision.
# GOALS MOVED FROM ONE SERIES TO THE OTHER, old label -> (new label, why). A
# refile is not a deletion, but it looks exactly like one to the deletion check,
# so it has to say so -- and the check verifies the new label EXISTS, which is
# what stops "refiled" becoming a way to make an entry disappear.
#
# A REFILED LABEL IS ALSO SPENT. `next_label` allocates from the maximum in use,
# and a refiled number is cited in commits and in the new entry's own history
# note, so reissuing it would make two different subgoals answer to one name.
REFILED: dict[str, tuple[str, str]] = {
    "Q42": ("E43",
            "the THIRD misfiling of 2026-09-04, after Q38 -> E40 and Q39 -> E41, "
            "and the `--next` reminder printed the test before each one. Its "
            "FINDING is a scoring fault -- the reasons scaffold reporting "
            "listed=0, failing=0, given=3, which cannot be arithmetic -- but its "
            "DELIVERABLE is a check plus a decision about whether the engine "
            "should recompute a `reported: True` slot rather than trust it, which "
            "is the audit's own machinery. Three of one kind in a day is the "
            "argument for either the content discriminator E41 measured and "
            "rejected, or for accepting that this judgement has no mechanical "
            "guard: `misfiled_series` compares a label against its SECTION, and a "
            "Q sitting in the quality-control section is consistent however wrong "
            "the series is."),
    "Q39": ("E41", "the second misfiling of 2026-09-04, and the `--next` reminder "
                   "had already printed the test. Its FINDING is 63 unstable "
                   "cells inside the numerator; its DELIVERABLE is a derived "
                   "instability band, which is audit machinery like E37's "
                   "wrong-cell accounting and E40's owner map."),
    "Q38": ("E40", "filed in the wrong series on 2026-09-04 and moved the same "
                   "day. The deliverable decides the series, not the finding "
                   "(subgoal E25 states the test): this one's deliverable is a "
                   "change to measured._live_subgoal_owners plus a fire test, "
                   "which is audit machinery, and subgoal E37 introduced that "
                   "map in the first place."),
}


# WHICH SECTION EACH SERIES LIVES IN. Exact across the corpus: 35 Q-goals are in
# the quality-control section and 32 E-goals in the equivalence one, with no
# exceptions -- so a label filed into the other section is a mistake rather than a
# style.
SERIES_SECTION: dict[str, str] = {
    "Q": "quality control",
    "E": "enforcing equivalence",
}

# WHAT THE SERIES MEANS, quoted where the allocator will be read. Subgoal E25's
# entry states the test and it is not mechanisable: "its FINDING is about accuracy
# but its DELIVERABLE is a primitive conversion ... That is the audit's own
# direction of travel." A CONTENT DISCRIMINATOR WAS BUILT AND REJECTED: scoring
# audit-vocabulary against QC-vocabulary across all 67 entries, Q tops out at 0.42
# and E's median is 0.35, and the case that motivated it -- E40, misfiled as Q38 --
# scores 0.30, BELOW the highest Q. It would have confirmed the mistake it was
# written to catch, so it is not shipped. The judgement stays with the reader; what
# the code enforces is that the label and the section agree.
SERIES_TEST = ("the DELIVERABLE decides the series, not the finding: a subgoal "
               "whose deliverable is a check, a declaration table or the audit's "
               "own machinery is an E, however much it discusses cells and gold")


# THE APPROVED CLOSURES LIVE WITH THE LEDGER THEY ARE ABOUT.
#
# Moved out of this module by E58 step 3, 2026-09-25, on the user's ruling:
# *"goals.CLOSURES_APPROVED goes with the goal ledger."* It was 233 lines of
# this course's goal history -- 52 approval notes naming its participants, its
# items and its measurements -- sitting in the module that CHECKS the ledger.
# GOALS.md is already split that way: the rules that would govern any course's
# ledger stay in `scoring/`, this course's 112 entries live with the course.
# The approvals are about those entries, so they go where the entries are.
#
# NOT PARSED OUT OF THE MARKDOWN, which is the other thing "with the ledger"
# could have meant. A reader that scrapes prose for data is the shape the user
# rejected outright on 2026-09-25 -- *"The reader shouldn't do that!"* -- so it
# is a JSON sidecar beside `GOALS.md`, and this reads it.
#
# ABSENT IS A REAL ANSWER. A course that has approved no closures ships no file,
# and the checks below then find nothing to verify rather than failing. That is
# the same judgement `segment.course_hook` makes about an absent hook -- and, as
# that function records, absent must not be confused with BROKEN: a file that
# exists and will not parse raises here.
CLOSURES_FILE = Path(compose_docs.specific_path("GOALS.md")).parent / "CLOSURES_APPROVED.json"


def _closures_approved() -> dict[str, str]:
    """`{goal label: the note recording that the user agreed to close it}`."""
    if not CLOSURES_FILE.is_file():
        return {}
    try:
        doc = json.loads(CLOSURES_FILE.read_text())
    except ValueError as exc:
        raise ValueError(
            f"{CLOSURES_FILE} exists and will not parse: {exc}. An unreadable "
            f"ledger is not an empty one -- returning nothing here would let "
            f"every closure check pass while the record of approval was gone"
        ) from exc
    return dict(doc.get("approvals") or {})


CLOSURES_APPROVED: dict[str, str] = _closures_approved()


def entries(text: str) -> dict[str, tuple[str, str]]:
    """label -> (state, title), in document order. state is ' ' or 'x'."""
    out: dict[str, tuple[str, str]] = {}
    for m in ENTRY.finditer(text):
        out[f"{m.group(2)}{m.group(3)}"] = (m.group(1), m.group(4)[:88])
    return out


# THE PRIOR STATE IS THE COMMITTED LEDGER AGAIN, 2026-09-26.
#
# WHAT WAS HERE. While GOALS.md lived outside the repository there was no
# committed file to compare against, and two of the checks below compare against
# the entries AS THEY STOOD. `git show HEAD` would have returned nothing and both
# checks would have passed every time, so the STATE was versioned separately --
# a sidecar of labels and their open/closed flags, rewritten by an explicit
# `--record` whenever a goal was opened or closed.
#
# WHY IT GOES. The ledger is tracked again, filed with the rest of the
# quality-control cycle in `<course>/<rubric id>_qc/`, so the thing the sidecar stood in for
# exists once more. The recording command's own docstring named what it was
# imitating: it "is what says this closure was agreed and this deletion was
# intended -- exactly what committing the file used to mean". Committing means
# that again, and two records of one fact is how they come to disagree.
#
# NO PRIOR STATE IS NOW REPORTED, NOT SKIPPED, and this is the part that must not
# be lost with the sidecar. `check()` read `before is None` and returned early,
# which is precisely the silent pass the sidecar was built to prevent -- it was
# safe only because the sidecar almost always answered first. With git as the
# only source that branch is reachable whenever the ledger is uncommitted, so it
# says so instead of certifying by silence.
def _before() -> dict | None:
    """The entries as last committed, or None if there is no committed state."""
    text = _committed()
    return entries(text) if text is not None else None


def _committed() -> str | None:
    try:
        r = subprocess.run(["git", "show", "HEAD:./" + _TRACKED.name],
                           cwd=_TRACKED.parent,
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
    # SPENT LABELS COUNT TOO. A refiled number no longer appears as an entry, so
    # the maximum drops and the allocator offers it again -- it offered Q38 back
    # the moment Q38 became E40, while Q38 was still cited in a commit message
    # and in E40's own history note. Two subgoals answering to one name is the
    # thing this function exists to prevent.
    used += [int(l[len(prefix):]) for l in REFILED
             if l.startswith(prefix) and l[len(prefix):].isdigit()]
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
    # THE COURSE'S OWN DOCUMENTS CITE SUBGOALS TOO, and they are no longer under
    # HERE. BACKLOG.md alone cites dozens; globbing `scoring/` after the move would
    # check the modules and quietly stop checking the record.
    cited_in = [pathlib.Path(compose_docs.doc_path(n))
                for n in sorted(set(compose_docs.SPLIT_DOCS) | set(compose_docs.WHOLE_DOCS))]
    for path in sorted(set(list(HERE.glob("*.md")) + list(HERE.glob("*.py")) + cited_in)):
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

    before = _before()
    if before is None:
        bad.append(
            f"{GOALS.name}: no committed prior state to compare against -- "
            f"`git show HEAD:{_TRACKED.name}` in {_TRACKED.parent} returned "
            f"nothing. The deletion and unapproved-closure checks below cannot "
            f"run, which is NOT the same as their passing. Commit the ledger.")
        return bad

    # 3. DELETIONS. A goal is closed, never removed: its number is cited
    #    elsewhere and its record is the reason the work is not redone.
    for label, (_state, title) in before.items():
        if label not in now:
            moved = REFILED.get(label)
            if moved:
                if moved[0] in now:
                    continue                  # declared, and the target exists
                bad.append(
                    f"{GOALS.name}: goal {label} is declared REFILED to "
                    f"{moved[0]}, but {moved[0]} is not an entry in the file. A "
                    f"refile that points nowhere is a deletion with a note on it")
                continue
            bad.append(
                f"{GOALS.name}: goal {label} ('{title[:60]}') was in the recorded "
                f"state and is GONE. Goals are closed with `- [x]`, never deleted — "
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


def misfiled_series() -> list[str]:
    """Entries whose label series does not match the section they are filed in."""
    out: list[str] = []
    sec = None
    for n, line in enumerate(GOALS.read_text().splitlines(), 1):
        if re.match(r"^## ", line):
            sec = line[3:]
            continue
        m = ENTRY.match(line)
        if not m:
            continue
        want = SERIES_SECTION.get(m.group(2))
        if want and sec is not None and want not in sec:
            out.append(
                f"{GOALS.name}:{n} {m.group(2)}{m.group(3)} is filed under "
                f"'{sec[:44]}' but the {m.group(2)} series lives in the "
                f"'{want}' section. Move the entry, or the label is wrong -- "
                f"{SERIES_TEST}")
    return out


def main(argv: list[str]) -> int:
    if "--next" in argv:
        i = argv.index("--next")
        pre = argv[i + 1] if len(argv) > i + 1 else "Q"
        print(next_label(pre))
        print(f"  ({pre} lives in the '{SERIES_SECTION.get(pre, '?')}' section. "
              f"{SERIES_TEST}.)")
        return 0
    if "--list" in argv:
        for label, (state, title) in entries(GOALS.read_text()).items():
            print(f"  [{state}] {label:5} {title[:70]}")
        return 0
    if "--rank" in argv:
        for i, (lab, _f, why) in enumerate(rank(), 1):
            print(f"  {i:>2}. {lab:5} {why}")
        return 0
    if "--slot-claims" in argv:
        s = stale_slot_claims()
        print("\n".join(f"  ! {x}" for x in s) if s
              else "  no open goal quotes a slot figure older than the instrument")
        return 1 if s else 0
    bad = check() + misfiled_series()
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
            spec = A.load_action(_p7.handout_olx(job['handout']), O.ACTION[item])
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
        # `-L :func:file`, NOT `-S token`. The pickaxe matches TEXTUAL
        # occurrences, so a docstring that merely NAMES one of these functions
        # moved the instrument date and back-dated a figure re-derived hours
        # earlier -- which is how this check produced its first false alarm, on a
        # line the same session had just corrected. `-L` follows the function's
        # own definition, which is the thing whose behaviour matters.
        stamps = []
        for tok in _PROFILE_TOKENS:
            try:
                r = subprocess.run(["git", "log", "-1", "--format=%at",
                                    "-L", f":{tok}:measured.py"], cwd=HERE,
                                   capture_output=True, text=True, timeout=60)
                if r.returncode == 0 and r.stdout.strip():
                    stamps.append(int(r.stdout.splitlines()[0].strip()))
            except Exception:
                pass
        if not stamps:
            return []
        instrument_at = max(stamps)

    lines = line_times()                       # (write_time, text), stamps first
    if not lines:
        return []

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


# ------------------------------------------------------------------- ranking

def rank() -> list[tuple[str, dict, str]]:
    """Open goals in priority order, DERIVED rather than remembered.

    Standing instruction, 2026-09-04: "Knowing what the rank order of goals is,
    and redoing it when something happens that would affect the ranking, is
    something that ought to be happening automatically." So there is no stored
    ranking to go stale -- it is recomputed from the ledger and the goal file
    every time it is asked for, and it prints the FACTS it ordered on rather than
    a score, because a score cannot be argued with.

    The ordering follows this project's own guide (§0): a DETERMINISTIC miss with
    a named failing check is worth more than a larger gap of unknown shape,
    "because it can be fixed or declared; a wobbling cell cannot be either". So,
    in order:

      deterministic wrong cells    a cell wrong in EVERY pooled run
      cells the TITLE claims       ownership stated rather than mentioned in passing
      citations from other OPEN    how many other subgoals are waiting on it
      items to sweep               fewer is cheaper to settle
      unstable cells               counted, but last: they cannot be measured against

    What it deliberately does NOT do is decide anything. It cannot read whether a
    candidate fix exists, and that has decided more of this project's priorities
    than any count -- so the output is an ordering to argue with, not an answer.
    """
    import re as _re
    try:
        import measured as M
    except Exception as e:
        return [("", {}, f"cannot rank: measured will not import: {type(e).__name__}")]

    text = GOALS.read_text()
    open_labels = [l for l, (st, _t) in entries(text).items() if st == " "]
    try:
        owners = M._live_subgoal_owners()
    except Exception as e:
        return [("", {}, f"cannot rank: {type(e).__name__}: {e}")]

    # PER CELL, POOLED OVER THE OLX-PROMPT SIDES. `records()` takes a SIDE and
    # defaults to one, so `records()[item]["olx"]` is None rather than an error --
    # the trap measured.py records at its own declaration_conflicts, where reading
    # one side made a declaration the other side had refuted invisible. The first
    # version of this ranking hit it and reported that NO open goal owned a wrong
    # cell, which degenerated the whole order into citation counts and looked
    # plausible. Ask for each side by name.
    # BANDS COME FROM measured.cell_bands, not from thresholds repeated here.
    # Subgoal E41 made the band derivable and E40's lesson is why this consumes
    # it rather than recomputing: two implementations of one rule is the
    # divergence class this project exists to close, and this function has now
    # been the second copy twice.
    bands = M.cell_bands()
    state = {c: (r, n) for c, (r, n, _b) in bands.items()}

    # citations between OPEN goals
    cited: dict[str, int] = {l: 0 for l in open_labels}
    label = None
    for line in text.splitlines():
        m = ENTRY.match(line)
        if m:
            label = f"{m.group(2)}{m.group(3)}"
        for pre, num in CITE.findall(line):
            tgt = f"{pre}{num}"
            if tgt in cited and label != tgt and label in open_labels:
                cited[tgt] += 1

    # PRIMARY OWNERSHIP, NOT MENTION. `owners["any"]` repeats a label once per
    # MENTION and is generous on purpose -- it exists so no wrong cell can be
    # left with nobody looking at it. For ranking that is the wrong instrument:
    # the first version credited DAY2/p7 to four subgoals at once and gave Q26,
    # which is about one character of DAY1's OLX, two deterministic cells it has
    # nothing to do with. A subgoal that mentions a cell five times is discussing
    # it; one that mentions it once in an aside is not. So the owner is whoever
    # mentions it MOST among open goals, ties shared.
    # AND AN ENTRY ENDS WHERE THE NEXT ENTRY *OR* THE NEXT HEADING BEGINS. Bounding
    # only at the next entry makes the LAST labelled entry of a section swallow
    # everything after it: Q26's body measured 8223 characters that way and
    # contained other subgoals' cells, which is how a subgoal about one character
    # of DAY1's OLX came to own a Q4b cell. Counted here rather than by changing
    # measured._live_subgoal_owners, which is generous ON PURPOSE -- it exists so
    # that no wrong cell is left unlooked-at, and narrowing it would weaken the
    # audit that depends on it.
    all_items = set(M._jobs())
    ITEM_TOK = _re.compile(r"(?<![\w/])(" + "|".join(sorted(
        (_re.escape(i) for i in all_items), key=len, reverse=True)) + r")(?![\w/])")
    # Corpus references cite TEXT, not cells: `[[corpus Q5/p4 ...]]` would be
    # read as a citation of Q5/p4 by the CELL pattern below. Stripped for the
    # same reason measured._live_subgoal_owners strips them.
    text = _re.sub(r"\[\[corpus[^\]]*\]\]", " ", text)
    CELL = _re.compile(r"\b([A-Za-z0-9]+)/p(\d+)\b")
    lines = text.splitlines()
    bounds: dict[str, list[str]] = {}
    cur = None
    for line in lines:
        m = ENTRY.match(line)
        if m:
            cur = f"{m.group(2)}{m.group(3)}"
            bounds[cur] = [line]
            continue
        if _re.match(r"^#{1,3} ", line):
            cur = None                      # a heading ends the entry
            continue
        if cur:
            bounds[cur].append(line)

    # OWNERSHIP COMES FROM THE SHARED MAP, not from a second copy of the rule.
    # This function carried its own bare-`pN` resolution while subgoal E40 was
    # open, because the ranking was the thing visibly wrong and the shared map is
    # read by several checks. E40 landed the resolution there -- with the entry
    # boundary and the `subject` map -- so the copy is deleted. Two
    # implementations of one rule is the divergence class this project exists to
    # close, and E40's own entry required this deletion.
    #
    # `subject` means the entry's TITLE names the item and the cell appears in
    # the entry: it is about the cell. `any` is every mention and is generous on
    # purpose, so it decides only when nothing claims the cell as its subject.
    owned = M._live_subgoal_owners()
    primary: dict[str, tuple] = {}
    for cell, labs in owned["any"].items():
        # AND OWNERSHIP MUST BE FOR THE SIDE THE FIGURES COME FROM. The cells
        # counted wrong here are the POOLED OLX-PROMPT ones, so a subgoal about
        # the paper scorer is not a home for them -- which is the whole reason
        # the shared map carries `by_side`. Without this, Q33 ("Q4a on the PAPER
        # scorer") claimed Q4a/p14 and Q4a/p19 the moment bare-`pN` resolution
        # landed, and rose to second place on cells that are wrong on a side it
        # is not about.
        for_side = {l for s in ("olx",)
                    for l in (owned["by_side"].get(cell, {}).get(s) or [])}
        subj = [l for l in dict.fromkeys(owned["subject"].get(cell, []))
                if l in open_labels and l in for_side]
        if subj:
            primary[cell] = tuple(sorted(subj))
            continue
        counts: dict[str, int] = {}
        for l in labs:
            if l in open_labels:
                counts[l] = counts.get(l, 0) + 1
        if not counts:
            continue
        top = max(counts.values())
        primary[cell] = tuple(sorted(l for l, c in counts.items() if c == top))

    # NEVER MEASURED OUTRANKS EVERYTHING, because it is the one state where there
    # is nothing to rank ON. An item with no number has no wrong cells, so it looks
    # from the ledger exactly like an item with nothing owed -- which is how E28
    # sat at the bottom of the first ranking while 24 of 26 items had no `paper`
    # figure at all. A gap is not an absence of work; it is work nobody has
    # started.
    #
    # SIDE-AWARE, via measured._sides_named, which the owner map already uses to
    # decide which side a goal speaks about. A goal naming the paper side is asking
    # about paper numbers; one that mentions olx in passing is not asking for a
    # fresh sweep of the corpus. And a goal that names a side but NO item is
    # corpus-wide by construction -- E28's deliverable IS the corpus -- while one
    # that names items is scoped to them.

    def _measured_on(item: str, side: str) -> bool:
        try:
            if side == "olx":
                return any(item in M.records(s) for s in M.POOLED_OLX_PROMPT)
            return item in M.records(side)
        except Exception:
            return True                       # unknown is not a gap

    def _unmeasured_for(lab: str) -> list[str]:
        # THE SIDE COMES FROM THE TITLE, not the body. Reading the body put
        # `[paper]` gaps on Q17, Q19, Q20 and Q36, none of which is asking for a
        # paper sweep -- they mention the word once in passing. A goal whose
        # SUBJECT is a side says so where it says what it is about: E28 is "A
        # PAPER sweep the ledger can record", Q33 is "Q4a on the PAPER scorer".
        body = bounds.get(lab) or []
        title = body[0] if body else ""
        sides = M._sides_named(title)
        if not sides:
            return []                        # not a side-scoped goal; nothing owed
        # SCOPE FROM THE TITLE TOO, for the same reason as the side. Scoping from
        # the BODY undercounted E28 at 7 gaps instead of 24: its deliverable is
        # the whole corpus and its title names no item, but its prose mentions a
        # handful, so the scope collapsed onto those. A title that names items is
        # scoped to them (Q33 is "Q4a on the PAPER scorer" and Q4a HAS a paper
        # number, so it owes nothing there); a title that names none, while naming
        # a side, is corpus-wide.
        named = ((set(ITEM_TOK.findall(title)) | {
            c.split("/")[0] for c in primary if lab in primary[c]}) & all_items)
        # `& all_items` on BOTH halves: the cell-derived set was not filtered, so
        # prose like "p10/p18" produced an "item" called p10, which is measured
        # nowhere and therefore counted as a gap.
        scope = sorted(named) if named else sorted(all_items)
        return [f"{i}[{s}]" for s in sorted(sides) for i in scope
                if not _measured_on(i, s)]

    rows = []
    for lab in open_labels:
        det, stab, unst, items, titled = [], [], [], set(), 0
        for cell in primary:
            if lab not in primary[cell]:
                continue
            st = state.get(cell)
            if st is None:
                continue
            right, runs = st
            if right == runs:
                continue                      # cell is correct; nothing owed
            items.add(cell.split("/")[0])
            # THREE BUCKETS, NOT TWO. `right == 0` alone bucketed a cell that
            # reaches gold ONCE in twelve with genuine coin-flips -- Q1/p10 is
            # right 1 of 12 and its own subgoal makes the distinction that
            # matters: "stably wrong ... not a coin flip, and it is worth a rule
            # question rather than more runs". A cell that almost never reaches
            # gold can be fixed or declared; one that lands half the time cannot.
            band = bands[cell][2]
            if band == "always_wrong":
                det.append(cell)
            elif band == "wrong_by_median" or (band == "on_the_line"
                                               and right * 2 < runs):
                # counted wrong and rarely right: fixable or declarable
                stab.append(cell)
            else:
                unst.append(cell)
        for cell, labs in owners["title"].items():
            st = state.get(cell)
            if lab in labs and st is not None and st[0] != st[1]:
                titled += 1
        gaps = _unmeasured_for(lab)
        # COST IN SWEEPS, the unit that actually gets spent: an item measured on
        # both sides is two. Reported rather than folded into a score, because a
        # cost estimate is the part of a ranking most worth arguing with -- E28's
        # own entry puts its real figure at ~3,100 calls, which one sweep of the
        # whole corpus buys more cheaply than 24 separate ones.
        # A WRONG CELL needs the item swept on BOTH sides; a GAP already names the
        # one side it is missing, so counting it twice overstated E28 at 48 when
        # the work is 24 item-sides -- and its own entry puts the real figure at
        # ~3,100 calls, because one paper sweep covers every item at once.
        n_items = len({c.split("/")[0] for c in det + stab + unst}) * 2 + len(gaps)
        facts = {"deterministic": sorted(det), "stably_wrong": sorted(stab),
                 "unstable": sorted(unst),
                 "items": sorted(items), "titled": titled, "cited_by": cited[lab],
                 "unmeasured": gaps, "sweeps": n_items * 2}
        rows.append((lab, facts))

    # TIERS, because cost is not commensurable with evidence and pretending it is
    # means inventing weights. A DETERMINISTIC miss on one or two items can be
    # fixed or declared for a few hundred calls; a corpus-wide gap cannot be
    # touched for less than thousands. So: cheap-and-deterministic first, then
    # deterministic at any price, then the gaps, then cells that only wobble.
    #
    # THE FIRST VERSION PUT never-measured FIRST OUTRIGHT, which sent a ~3,100
    # call job to the top of a list whose next four entries cost a few hundred
    # each. Surfacing a gap and preferring it are different things.
    CHEAP = 4                                # sweeps, i.e. two items on two sides

    def _tier(f: dict) -> int:
        fixable = f["deterministic"] + f["stably_wrong"]
        if fixable and f["sweeps"] <= CHEAP:
            return 0
        if fixable:
            return 1
        if f["unmeasured"]:
            return 2
        if f["unstable"]:
            return 3
        # NOTHING ATTRIBUTED RANKS LAST, and it took a fix to get there: tier 3
        # sorted on COST, so goals owning no cells at all (cost 0) came out above
        # goals owning unstable ones. Cheap is only a virtue when something is
        # being bought.
        return 4

    # WITHIN A DETERMINISTIC TIER, COST LEADS. Sorting on evidence first put a
    # 28-sweep subgoal above an 8-sweep one on the strength of having more wrong
    # cells, which is the opposite of "cheap deterministic wins above expensive
    # calls": five cells settled for 28 sweeps is worse value than two settled
    # for eight, and the cheap one also gets answered sooner. Evidence still
    # breaks ties, and it still leads in the tiers where nothing is cheap.
    def _key(r):
        lab, f = r
        tier = _tier(f)
        if tier in (0, 1):
            return (tier, f["sweeps"],
                    -len(f["deterministic"]) - len(f["stably_wrong"]),
                    -len(f["deterministic"]), -f["titled"], -f["cited_by"], lab)
        return (tier, -len(f["unmeasured"]), -len(f["unstable"]),
                f["sweeps"], -f["titled"], -f["cited_by"], lab)

    rows.sort(key=_key)
    out = []
    for lab, f in rows:
        why = []
        if f["unmeasured"]:
            why.append(f"{len(f['unmeasured'])} NEVER MEASURED "
                       f"({', '.join(f['unmeasured'][:3])})")
        if f["deterministic"]:
            why.append(f"{len(f['deterministic'])} deterministic ({', '.join(f['deterministic'][:3])})")
        if f["stably_wrong"]:
            why.append(f"{len(f['stably_wrong'])} stably wrong "
                       f"({', '.join(f['stably_wrong'][:3])})")
        if f["titled"]:
            why.append(f"{f['titled']} claimed by title")
        if f["cited_by"]:
            why.append(f"{f['cited_by']} open goal(s) cite it")
        if f["unstable"]:
            why.append(f"{len(f['unstable'])} unstable ({', '.join(f['unstable'][:3])})")
        if f["sweeps"]:
            why.append(f"~{f['sweeps']} sweep(s) to settle")
        out.append((lab, f, "; ".join(why) or "no wrong cell currently attributed"))
    return out


def line_times(text: str | None = None) -> list:
    """[(epoch, line)] for GOALS.md -- from the STAMPS, blame as the fallback.

    A line inherits the date of the entry it belongs to, which is the granularity
    both readers actually walk: each already tracks the current entry as it scans.
    Blame gave per-line times, which was finer than anything used them for.

    STAMPS FIRST, BLAME SECOND, so this works whether or not the file is tracked.
    That is the point: dating the record must not depend on where the record is
    stored. Blame stays as the fallback rather than being deleted, so the two can
    be compared while both are available.
    """
    import datetime
    import subprocess

    src = text if text is not None else GOALS.read_text()
    dates = entry_dates(src)
    if dates:
        rows, cur = [], 0
        for line in src.splitlines():
            m = ENTRY.match(line)
            if m:
                d = dates.get(f"{m.group(2)}{m.group(3)}")
                if d:
                    y, mo, dy = (int(x) for x in d.split("-"))
                    cur = int(datetime.datetime(y, mo, dy).timestamp())
            rows.append((cur, line))
        return rows
    try:
        bl = subprocess.run(["git", "blame", "--line-porcelain", GOALS.name],
                            cwd=str(GOALS.parent), capture_output=True,
                            text=True, timeout=300)
        if bl.returncode != 0:
            return []
    except Exception:
        return []
    rows, at = [], 0
    for row in bl.stdout.splitlines():
        if row.startswith("author-time "):
            at = int(row.split()[1])
        elif row.startswith("\t"):
            rows.append((at, row[1:]))
    return rows


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
