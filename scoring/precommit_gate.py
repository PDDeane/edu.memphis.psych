#!/usr/bin/env python3
"""Refuse a commit while the two scorers differ in a way nobody has declared.

Installed as .git/hooks/pre-commit. It exists because the rule "run the
enforcement audit before committing" was followed by hand and then not: a change
that WIRED TWO NEW GATES into the scoring path was committed after running the
structural and leakage gates only, and `--enforcement` -- the one that compares
the two sides -- was skipped. It would have refused the commit: the change made
the web compute two checks the CLI still asks the model for, and put a gate on
one side only. Under a goal whose name is enforcing equivalence.

WHAT IT REFUSES: any enforcement finding that is not a measurement-state flag.
`ITEM UNMEASURED AS CONFIGURED` is excluded on purpose -- it says a recorded
number is stale, which is a fact about the ledger rather than a difference
between the scorers, and stale items are a deliberate state here (prompts are
cleaned immediately and swept later, so the ledger stays honest in between).

OVERRIDE: `ALLOW_UNDECLARED="<reason>" git commit ...`. The reason is printed and
required to be non-trivial. An override with no reason is refused, because a
switch that is easier to flip than to explain gets flipped.

AND THE OVERRIDE IS RECORDED, added 2026-09-04. Until then the reason was printed
to stderr and then gone: not in the commit, not in a file, not in git. Seven
commits were waved through in one day and the only way to answer "what did we
wave through, and why?" was to ask the person who had typed it. A gate careful
enough to demand a non-trivial reason and then discard it is keeping the ceremony
and losing the evidence.

The record goes into OVERRIDES.md and is STAGED INTO THE SAME COMMIT it excuses,
so the exception travels with the change rather than sitting beside it -- `git
log -p OVERRIDES.md` then reads as the history of what the audit was asked to
ignore. It records the findings VERBATIM, not just the reason: a reason written
about four findings is not evidence about a fifth that appeared with it.
"""
import json as _json
import os
import re as _re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_ONLY = ("ITEM UNMEASURED AS CONFIGURED",)
LOG = os.path.join(HERE, "OVERRIDES.md")


def _record(blocking: list[str], state: list[str], reason: str) -> str:
    """Append the override to OVERRIDES.md and stage it. Returns a status line.

    Staging is deliberate: an override recorded in the WORKING TREE only would be
    committed later, or never, and would drift away from the change it excuses.
    If staging fails the commit still proceeds -- refusing here would turn a
    bookkeeping problem into a blocked commit, which is the wrong trade -- but it
    says so loudly, because an unrecorded override is the state this exists to end.
    """
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True, cwd=HERE).stdout.strip()
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = [f"\n## {stamp}  (parent {head or 'unknown'})\n",
             f"\n**Reason given:** {reason}\n",
             f"\n**Findings waved through ({len(blocking)}):**\n\n"]
    entry += [f"- `{l.strip()}`\n" for l in blocking]
    if state:
        entry.append(f"\n{len(state)} non-blocking measurement-state flag(s) also "
                     f"present; those are excluded by design and are not overrides.\n")
    try:
        new = not os.path.exists(LOG)
        with open(LOG, "a") as fh:
            if new:
                fh.write("# Overrides of the enforcement gate\n\nEvery commit that "
                         "used `ALLOW_UNDECLARED`, with the findings it waved through "
                         "and the reason given. Entries are written by "
                         "precommit_gate.py and are never rewritten.\n\nA reason can "
                         "turn out to be wrong -- the first one recorded here was -- "
                         "so CORRECTIONS ARE APPENDED as their own dated section "
                         "under the entry they correct. What was believed at the time "
                         "and what turned out to be true both stay on the record; "
                         "editing an entry to make it right afterwards would destroy "
                         "the only evidence that anyone was ever mistaken.\n")
            fh.writelines(entry)
        add = subprocess.run(["git", "add", LOG], capture_output=True, text=True, cwd=HERE)
        if add.returncode:
            return f"WARNING: recorded in {os.path.basename(LOG)} but could not stage it"
        return f"recorded in {os.path.basename(LOG)} and staged into this commit"
    except OSError as exc:
        return f"WARNING: could NOT record this override ({exc})"



# ---------------------------------------------------------------------------
# STUDENT TEXT, RATCHETED.
#
# `.gitignore` blocks the corpus by PATH and says so in its own header: those
# rules are "a backstop for an accidental `cp` or `git add -A`, not the primary
# control". They cannot see a student sentence QUOTED INTO PROSE, and that is
# how 434 of them accumulated -- 371 in `scoring/`, across twenty files, none of
# it caught by anything. A write-up quoting the answer it is reasoning about is
# the most natural thing in the world to write and the easiest to not notice.
#
# This does NOT demand zero. Removing what is already there is a separate job
# with a real hazard in it -- 99 of those strings are FIXTURE DATA that the
# ledger was measured on, and rewording one silently changes what was scored.
# So the rule is the one the other budgets here use: the count may fall and may
# not rise. A commit that adds a quote to a file is refused; a commit that
# removes one lowers the bar behind itself and stages the new bar with the
# change, so the ratchet cannot be quietly let out later.
#
# .olx IS EXCLUDED EVERYWHERE, BY FILE TYPE AND NOT BY LOCATION. An .olx file
# is course content: it is what gets rendered TO the student, so student-facing
# language in it is the point. "I continue to [UTB] because X" and "My goal is
# Specific because..." are authored templates, not anybody's answer. The rule is
# about the file type rather than a directory on purpose -- scoping it to
# `psychology/` would start refusing the day course content is authored anywhere
# else, which is exactly what the refactor plan proposes to do.
#
# EXCLUDED_SUFFIXES is the one place to say this. The allowlist below already
# happened to skip .olx, but only as a side effect of naming the three types it
# does read, which is the kind of correct-by-accident that trap T32 was about.
# OUR OWN FIRST-PERSON PROSE, DECLARED.
#
# The detector looks for a quoted sentence in a student's voice, and we write in
# that voice too -- about our own work. "did my change make it do X", "built
# somewhere I did not look" and "is this DIFFERENT from what I already credited"
# are methodology, not anybody's answer, and a gate that cries leakage over them
# teaches people to reach for the override.
#
# Declared one at a time WITH A REASON, never widened into a pattern: a rule
# loose enough to exempt our prose would exempt a student sentence that happens
# to resemble it. And the entries are GUARDED -- `_launders()` refuses any entry
# whose text is findable in the corpus, so this table cannot be used, by accident
# or otherwise, to wave a real quote through. That guard is what makes the table
# safe to have at all. Measured when it was written: of the eight candidates in
# QUALITY_CONTROL.md, five are ours and THREE ARE REAL -- one of them
# ([[corpus WK1/p1 wk1 48:87 sha=9acb583a85f7]]) sits in the file precisely because a
# rule we authored had quoted it. Exempting by eye would have cleared it.
# A SEGMENT SHORTER THAN THIS IS NEVER A CANDIDATE, so a needle shorter than
# this can never be one either -- see `_too_short_to_declare`.
MIN_QUOTE_WORDS = 5


NOT_STUDENT_TEXT: dict[str, str] = {
    # "Another consequence" IS COURSE TEXT AND IS DELIBERATELY NOT LISTED HERE.
    # It is the placeholder of the box it is written in -- bmod_h1_q4c_second
    # carries placeholder="Another consequence is..." -- and twelve Q4c cells
    # echo it (p2 p3 p4 p5 p6 p10 p11 p12 p14 p16 p18 p20), which is a prompt
    # echo rather than anyone's writing. It was declared here on 2026-09-15 and
    # REMOVED the same day: at two words it can never be a flagged segment, so
    # it exempted nothing it was meant to, and by substring it cleared a
    # first-person sentence that opens with the placeholder and continues into
    # the student's own words -- which the gate had been flagging correctly.
    # (The illustration is described and not quoted: the sentence written to
    # demonstrate the hole was itself classified as student text, because an
    # invented completion of a real stem collides with real completions of it.)
    # `_too_short_to_declare`
    # refuses the shape now. The phrase needs no entry; nothing flags it. What
    # it did need was removing from the history-rewrite substitution table, so
    # a course placeholder is not replaced by a reference naming one student.
    "did my change make it do X":
        "QUALITY_CONTROL.md's identical-result principle -- the question a test "
        "asks of a fix, not a sentence anybody wrote",
    "built somewhere I did not look":
        "one of three readings an inconclusive search is consistent with; ours",
    "is this DIFFERENT from what I already credited":
        "the per-slot form of the double-credit question, written by us",
    # "wording, not the split" REMOVED 2026-09-15, with the guard that found it.
    # Four words, so it could never be a flagged segment itself; measured across
    # the whole tree it changed nothing, with or without -- INERT. What it could
    # still do was clear a longer first-person sentence that happened to contain
    # it. An entry that exempts nothing and can only launder is worth less than
    # the risk it carries.
    "My goal is specific because":
        "THE HANDOUT'S OWN SENTENCE STARTER, and the only place it survives the "
        "history rewrite is a code comment describing the SHAPE a response "
        "takes -- written with a placeholder, `\"{{corpus:Q3/p1:specific:10:37:sha=32a1b1a0f56c}} X\"`, "
        "precisely so it names no one's completion. It is the stem printed on "
        "the page for every student, not anything a student added to it",
    "instead of drinking water, I am drinking soda":
        "THE INSTRUMENT'S OWN EXAMPLE, not a response: LEAKAGE_REVIEWED.json "
        "records it as B_NOT_ACTIVE's description in the instructor's guide. "
        "Course material we are allowed to quote, and the reason the leakage "
        "review cleared it rather than charging it",
    "have to do 30 pushups if I miss it":
        "OUR PROMPT's text, quoted in GOALS.md to record that criterion 7's "
        "`avoidance_frame` had reproduced DAY1/p8 ALMOST word for word. It is "
        "the rule we wrote, kept verbatim because the entry's whole point is "
        "what the rule said -- paraphrasing it would destroy the evidence of "
        "the leak. Not identical to p8, which is why no span resolves it. "
        "KEYED ON THE SHORT FORM: the detector treats an apostrophe as a quote "
        "delimiter, so `so I don't have to ...` reaches it as `t have to ...`, "
        "and a declaration carrying the apostrophe never matches what is "
        "actually flagged",
    "I will read rather than scroll":
        "OUR REWRITE, not a response. GOALS.md records that p4's own wording had "
        "leaked into a shared block and was replaced by this -- 'Rewritten, not "
        "excused'. Quoting the replacement is how the entry shows what the block "
        "says now; the student's original is referenced separately",
    "These are not examples of why you continue to engage in the UTB":
        "the ITEM'S OWN instructional text, telling a student what the box is "
        "not for. Authored scaffolding that ships to the grader as context",
    "My Unwanted Target Behavior is":
        "A HANDOUT HEADING, verbatim in the .olx. segment.py matches it to split "
        "a submission and it ships because the student reads it -- load-bearing "
        "twice, so it must stay byte-exact. It is also in the corpus, at Q1/p3, "
        "because a student typing into the template carries the heading along; "
        "that is what the .olx check in `_launders` exists to tell apart",
    "My Wanted Goal Behavior is":
        "the sibling heading, same role in segment.py and the same reason it is "
        "course content rather than anybody's answer",
    "this should help me reach my goal":
        "leakage.py's own invented example. Its docstring calls it a coincidence "
        "'colliding with DAY2/p17', but `_implausible_coincidence` showed the "
        "phrase is in NO cell: p17 reads 'Losing {{corpus:DAY2/p17:day2:126:152:sha=c26703d77e07}} "
        "decrease {{corpus:DAY2/p17:day2:162:182:sha=24089ed3b4de}} exercise', so the overlap is the two "
        "words 'should help'. Ours outright, and the docstring overstates it",
    "my goal OF 8 HOURS OF SLEEP":
        "OUR phrasing in an olx_prompts rule, not a quotation: `_miscategorised` "
        "refused it as an accepted exposure because NO CELL CONTAINS IT. It reads "
        "like a student sentence and it ships, so leakage.py may still want it "
        "rewritten -- echoing the cohort's register is a validity question -- but "
        "nobody's words are being stored",
    "My goal is Specific because":
        "VERBATIM IN THE HANDOUT .olx -- the SMART-goal stub each item asks the "
        "student to complete. Course content, and the .olx check in `_launders` "
        "confirms it rather than taking my word",
    "My goal is specific because X":
        "the same stub with OUR placeholder X standing in for the completion; "
        "written in a comment to show the shape a rule matches. No student "
        "typed an X there",
    "I plan to use: positive reinforcement":
        "a worked example in agreement_app's own commentary, naming a mechanism "
        "from the instrument's vocabulary. Not in any cell",
    "this file has an entry I do not understand":
        "cross_path's docstring describing the state a reader is in when the "
        "table disagrees with itself; ours",
    "no definition disappeared that I did not say I was deleting":
        "editguard's docstring stating its own invariant, in the first person "
        "because that is whose intent the guard checks; ours",
    "is a self-test mutating THE SOURCE I AM ABOUT TO READ":
        "olx_prompts' question about its own selftest seam; ours",
    "an answer keyed to `if I meet my goal` is daily":
        "rubric_h2's note on how a cadence answer is read -- our analysis of a "
        "phrasing, not a quotation of one",
    "because it leaves me irritable and behind on everything":
        "an INVENTED example in an authored block, and LEAKAGE_REVIEWED.json "
        "says so from its own measurement: 'Checked against the corpus before "
        "filing, not assumed ... neither appears anywhere in the 63 submission "
        "files'. The review that cleared it is the evidence",
    "lie there wishing I had started earlier":
        "a second invented example from the same reviewed block, absent from "
        "the corpus by the same check",
    "yawning through my morning classes":
        "authored example text -- it is in the handout .olx itself, which the "
        "`_launders` course check confirms independently of the leakage review",
    "I will go to sleep on time":
        "a DIFFERENT COURSE's text: psych_sba_activities_part2.olx uses it as a "
        "positive-punishment example -- make the child write it 100 times. Filed "
        "as a coincidence first, and `_implausible_coincidence` refused it: the "
        "corpus has `IF {{corpus:NR/p20:nr:3:19:sha=0bf01d763ca7}} time` (NR/p20, about not needing naps), "
        "not `I WILL go to sleep on time`. Nothing collided, so it is simply ours",
    "I will be able to get X":
        "OUR template, in rubric_h2's `_OC_FRAME` -- the course's own definition "
        "of the four operant-conditioning types, with X standing for whatever "
        "the student names. The classifier reached it through the fragment "
        "`{{corpus:PR/p11:pr:22:43:sha=26a7f88a4cb9}}`, which p11 wrote in both PR and WK1; the X is "
        "what makes the whole string ours",
    "49 cases and the two SKIP lines I remembered":
        "a note about the SELFTEST's own case count and what was recalled of it "
        "-- about this repo's test suite, not about anybody's behaviour",
    "I want more than a declaration":
        "the USER's instruction on a subgoal: a fix is wanted, not a declared "
        "divergence. Their words about our work, quoted back in the entry",
    "own scaffolding, so any rule that keeps the escape credits p20":
        "our analysis of what an item's own template forces; the sentence is "
        "about a RULE's reach, and the detector caught it only because the "
        "apostrophe in `item's` splits it into a first-person-looking fragment",
    "is it reading or writing THE SOURCE I AM ABOUT TO TOUCH":
        "the question the migration plan tells a reader to ask before editing; "
        "ours, in RUBRIC_MIGRATION_PLAN.md",
    "I continue to [UTB] because X":
        "the handout's TEMPLATE, with its placeholder still in it -- [UTB] is "
        "the scaffold's own token and no student ever typed it",
    "if I meet my goal, I will ...":
        "a template STUB quoted in README.md to show the contingency shape the "
        "items ask for; the trailing ellipsis marks it as a form, not an answer",
    "When I am not exercising, I am ...":
        "Q4b's authored TEMPLATE STUB, quoted in the table of regex attempts to "
        "show what the item's own scaffolding says. THE TRAILING ELLIPSIS IS "
        "LOAD-BEARING and was added after `_launders` refused the entry without "
        "it: `When I am not exercising, I am` alone IS in the corpus, at "
        "Q4b/p3 second, because a student completed that very stub. The stub "
        "with its ellipsis is the handout's; the same words without it are "
        "somebody's answer, and one substring cannot stand for both",
}


# STUDENT TEXT WE KNOWINGLY KEEP, AND WHY.
#
# A SEPARATE TABLE FROM `NOT_STUDENT_TEXT` ON PURPOSE. That one asserts a quote
# is NOT a student's, and `_launders` proves it by asking the corpus. If an
# accepted exposure were parked there the assertion would be false, the guard
# would refuse it, and the pressure would be to weaken the guard -- which is the
# one mechanism here that has already caught two wrong calls. So the two claims
# get two tables, and the guards point in OPPOSITE directions:
#
#   NOT_STUDENT_TEXT     -- must NOT be findable in the corpus (_launders)
#   ACCEPTED_STUDENT_TEXT -- must BE findable in it (_miscategorised)
#
# An entry that fails its own guard is in the wrong table, and each check says so.
#
# EVERY ENTRY HERE IS ALSO A LEAKAGE FINDING. These two are student sentences
# inside rules that SHIP to a grader, which is what `leakage.py` exists to catch:
# a rule quoting the cohort is an answer key for one cell, and the gain it
# reports is circular. Accepting the exposure is a decision about privacy; it
# does not settle the validity question, and neither phrase appears in
# LEAKAGE_REVIEWED.json yet.
ACCEPTED_STUDENT_TEXT: dict[str, str] = {
}


# COLLISIONS THAT ARE NOT QUOTATIONS.
#
# leakage.py's own docstring names this case: "an invented example landing on a
# stock phrasing a student also used ... Usually one student, usually one short
# pair." Its example was written independently and collides with DAY2/p17. No
# corpus check can tell that apart from a quotation -- the text is identical --
# so the distinction is an authored claim, and the guard below is about
# PLAUSIBILITY rather than provenance.
#
# THE GUARD IS LENGTH, for leakage.py's own stated reason: a short stock clause
# is the kind of thing two people write independently, and a long exact match is
# not a coincidence, it is a copy. An entry over the limit is refused, so this
# table cannot grow into a way of excusing real quotation.
COINCIDENCE_MAX_WORDS = 8
COINCIDENTAL_TEXT: dict[str, str] = {
}


# corpus-refs-resolved
#
# THE KEYS OF THE THREE TABLES ABOVE MAY BE CORPUS REFERENCES, AND ARE RESOLVED
# HERE. Each key is a NEEDLE: the gate matches it against a file being committed
# and against the corpus. A `{{corpus:...}}` reference left unresolved matches
# nothing, so every exemption it carries silently stops applying -- and this is
# the gate that keeps student text OUT of the repository, so a silent failure
# here is the worst-placed one in the package.
#
# IT HAPPENED. The 2026-09-21 adoption of the rewritten history put references
# into 11 of these keys, and nothing reported it: the file still parsed, still
# imported, and the gate still ran -- against needles that could not match.
#
# NOT CIRCULAR, WHICH IS WHY THIS IS THE RIGHT PLACE FOR IT. The gate already
# calls `corpus_ref._index()` in three checks; resolving its own needles asks the
# same source for the same data it was always going to load.
#
# FAILS LOUDLY. A reference that cannot be resolved raises rather than leaving a
# needle that matches nothing -- the alternative is the silent failure above.
def _resolve_needles(table: dict) -> dict:
    """Expand any corpus reference standing in a table KEY."""
    if not any("{{corpus:" in k for k in table):
        return table
    import corpus_resolve as _CR
    out = {}
    for k, why in table.items():
        if "{{corpus:" in k:
            expanded = _CR.expand(k)
            if "{{corpus:" in expanded:
                raise SystemExit(
                    f"precommit_gate: a needle carries a corpus reference that "
                    f"does not resolve: {k[:60]!r}. The gate would run with a "
                    f"needle that matches nothing, so it refuses to run at all.")
            k = expanded
        out[k] = why
    return out


NOT_STUDENT_TEXT = _resolve_needles(NOT_STUDENT_TEXT)
ACCEPTED_STUDENT_TEXT = _resolve_needles(ACCEPTED_STUDENT_TEXT)
COINCIDENTAL_TEXT = _resolve_needles(COINCIDENTAL_TEXT)


def _implausible_coincidence(idx=None) -> list:
    """Any COINCIDENTAL_TEXT entry too long to be a coincidence, or not in the
    corpus at all.

    Two ways an entry can be wrong. Too LONG: a nine-word exact match is a
    quotation whatever the author believed, and this is the only table with no
    provenance check, so the length limit is what keeps it honest. Not in the
    CORPUS: then nothing collided, and the entry belongs in NOT_STUDENT_TEXT
    where it costs nothing to say so.
    """
    if idx is None:
        sys.path.insert(0, HERE)
        import corpus_ref as CR
        idx = CR._index()
    bad = []
    for needle, why in COINCIDENTAL_TEXT.items():
        n = needle.lower()
        if len(needle.split()) > COINCIDENCE_MAX_WORDS:
            bad.append(f"COINCIDENTAL_TEXT[{needle!r}] is "
                       f"{len(needle.split())} words, over the limit of "
                       f"{COINCIDENCE_MAX_WORDS}. A match that long is a copy, "
                       f"not a collision -- reference it instead")
        elif not any(n in text.lower() for text in idx.values()):
            bad.append(f"COINCIDENTAL_TEXT[{needle!r}] is not in the corpus, so "
                       f"nothing collided with it -- it belongs in "
                       f"NOT_STUDENT_TEXT ({why[:36]}...)")
    return bad


def _miscategorised(idx=None) -> list:
    """Any ACCEPTED_STUDENT_TEXT entry that is NOT in the corpus.

    The mirror of `_launders`. An entry here claims "this IS a student's words
    and we are keeping them anyway"; if the corpus does not contain it, the
    claim is wrong and the entry belongs in NOT_STUDENT_TEXT, where it would
    cost nothing. Without this check the table would quietly become a second,
    unguarded exemption list -- which is exactly what it was created not to be.
    """
    if idx is None:
        sys.path.insert(0, HERE)
        import corpus_ref as CR
        idx = CR._index()
    bad = []
    for needle, why in ACCEPTED_STUDENT_TEXT.items():
        n = needle.lower()
        if not any(n in text.lower() for text in idx.values()):
            bad.append(f"ACCEPTED_STUDENT_TEXT[{needle!r}] is NOT in the corpus -- "
                       f"it is not student text, so it belongs in "
                       f"NOT_STUDENT_TEXT ({why[:40]}...)")
    return bad


def _too_short_to_declare() -> list:
    """Any NOT_STUDENT_TEXT entry too short to be the thing it exempts.

    THE TABLE MATCHES BY SUBSTRING, which is what makes it useful: our phrase
    sits inside a longer sentence of our prose and the exemption finds it there.
    It is also what makes a SHORT entry dangerous. The scanner only considers
    segments of `MIN_QUOTE_WORDS` or more, so a needle below that length can
    never be the segment being exempted -- it can only ever swallow a longer one
    that contains it.

    Measured when this was written. "Another consequence" is the placeholder of
    the box it is written in, so declaring it looked exactly right; two words
    cannot be flagged, so it exempted nothing it was meant to, and by substring
    it silently cleared a first-person sentence opening with that placeholder
    and continuing into the student's own words -- gone from the gate. The
    entry was removed and this guard written so the next one is refused rather
    than reasoned about. The demonstrating sentence is described rather than
    quoted here: written to be fictional, it was classified as student text
    anyway, an invented completion of a real stem colliding with real ones.

    Course text this short needs no entry: the scanner never sees it.
    """
    bad = []
    for needle, why in NOT_STUDENT_TEXT.items():
        n = len(needle.split())
        if n < MIN_QUOTE_WORDS:
            bad.append(f"NOT_STUDENT_TEXT[{needle!r}] is {n} word(s); the "
                       f"scanner only considers segments of {MIN_QUOTE_WORDS} "
                       f"or more, so this entry cannot exempt itself and can "
                       f"only exempt longer text that contains it. If the "
                       f"phrase is course content it needs no entry -- nothing "
                       f"flags it")
    return bad


def _launders(idx=None) -> list:
    """Any NOT_STUDENT_TEXT entry that is findable in the corpus.

    The exemption table's one real danger: an entry added because a quote
    "looked like ours" when it is in fact a student's. This asks the CORPUS
    rather than the author. It needs the corpus, so it runs deliberately
    (`--audit-exemptions`) rather than on every commit -- but an entry that has
    never been through it is an assertion, not a declaration.
    """
    if idx is None:
        sys.path.insert(0, HERE)
        import corpus_ref as CR
        idx = CR._index()
    # AUTHORED TEXT STAYS AUTHORED WHEN A STUDENT COPIES IT BACK. A handout
    # heading is in the corpus for a reason that has nothing to do with
    # authorship: the student typed into a template that carries it. Checking the
    # .olx first is what separates the two -- if the course says it, it is the
    # course's, however many submissions echo it. Without this the guard refuses
    # every heading, which would push real course content into being treated as
    # somebody's answer.
    course = ""
    try:
        import olx_prompts as _O
        course = " ".join(_O._src(h) for h in (1, 2, 3)).lower()
    except Exception:
        course = ""
    bad = []
    for needle, why in NOT_STUDENT_TEXT.items():
        n = needle.lower()
        if course and n in course:
            continue                      # the handout says it; it is course content
        for (item, pid, fld), text in idx.items():
            if n in text.lower():
                bad.append(f"NOT_STUDENT_TEXT[{needle!r}] IS in the corpus at "
                           f"{item}/p{pid} {fld}, and NOT in the course .olx -- "
                           f"it is a student's sentence, so the reason given "
                           f"({why[:40]}...) is wrong")
                break
    return bad


BUDGET = os.path.join(HERE, "STUDENT_TEXT_BUDGET.json")
EXCLUDED_SUFFIXES = (".olx",)          # course content: student-facing by design
SCANNED_SUFFIXES = (".py", ".md", ".json")
_VOICE = _re.compile(r"\b(I |I'm|I am|my |My |me |myself)")
_TECH = _re.compile(r"[_{}=<>|\\]|\b(sha|slot|item|check|audit|rubric|verdict|"
                    r"gold|cell|sweep|prompt|olx|py|json|md)\b", _re.I)


def _quotes(raw: str) -> set:
    """Quoted first-person sentences, found across line breaks.

    Normalised before matching, and that is the whole trick. A line-based grep
    for these missed most of them: the quotes wrap, and in .py they are split
    across adjacent string literals, so `"I {{corpus:Q5/p4:second:2:23:sha=b3d29f15848a:shape=S1-20222022}} enough"`
    contains neither half as a searchable phrase. Joining the seams first took
    one file's count from 1 to 3.
    """
    n = _re.sub(r'"\s*(?:#[^\n]*)?\n\s*"', "", raw)    # "abc" \n "def" -> "abcdef"
    n = _re.sub(r"\s*\n\s*(?:#\s*)?", " ", n)          # unwrap, drop comment marks
    n = _re.sub(r"\s+", " ", n)
    n = _re.sub(r'\\+(["\'])', r"\1", n)                # an ESCAPED quote is still a quote
    out = set()
    # EVERY INTER-QUOTE SEGMENT, not alternate pairs. The first version matched
    # `"..."` with a regex, which pairs quote characters ALTERNATELY -- and that
    # made text at an odd position in the sequence structurally invisible. In
    #     "rule": "same rule. \\"By the end of the month I was down to about one\\" covers it"
    # match 1 runs from the opening quote to the first escaped one (its content
    # ends in a backslash, so the TECH filter killed it) and match 2 starts at
    # the second escaped quote. The student's sentence was the GAP BETWEEN two
    # candidates and could never be a candidate itself. Measured when this was
    # found: 62 pieces of student text hidden repo-wide, four of them in rubric
    # files whose text SHIPS to a grader, while the old scan reported zero.
    #
    # Splitting on quotes instead of pairing them has no odd/even blind spot. It
    # costs false positives -- unquoted prose between two quoted spans is now a
    # candidate -- and that is the right trade: a false positive is declared once
    # in NOT_STUDENT_TEXT, a false negative is invisible forever.
    # AND SPLIT WHAT THE LAYOUT BROKE. A quote can be interrupted by inline
    # annotation without any quote character closing it:
    #
    #     "<a student's effect clause>   <- our note, in the right-hand gutter
    #                                         continuing onto the next line
    #      AND <their second clause>      <- another note"
    #
    # (Shown in outline, not quoted. The first version of this comment carried
    # the real sentences, and the widened scanner immediately flagged its own
    # explanation -- which is the correct answer.)
    #
    # Unwrapping turns that into ONE segment carrying the student's two clauses
    # and four clauses of ours. The words are all there and `is_student` still
    # refused it, because coverage is measured over the whole segment and the
    # commentary diluted the corpus run below MIN_COVERAGE. Found on 2026-09-15
    # in GOALS.md, in a passage that had already cited the same span correctly
    # two lines above -- referenced in the argument, quoted in the illustration.
    #
    # So the annotation gutters are seams too. Splitting on them costs more
    # candidates, which is the trade this scanner already makes everywhere else.
    _SEAMS = r'["\u201c\u201d]|<-|->|\u2190|\u2192'
    for _seg in _re.split(_SEAMS, n):
        s = _seg.strip()
        if not (_VOICE.search(s) and not _TECH.search(s)
                and len(s.split()) >= MIN_QUOTE_WORDS):
            continue
        if any(ours in s for ours in NOT_STUDENT_TEXT):
            continue                      # declared ours, and guarded by _launders
        if any(co in s for co in COINCIDENTAL_TEXT):
            continue                      # independently authored, guarded by length
        if any(kept in s for kept in ACCEPTED_STUDENT_TEXT):
            continue                      # student text kept on purpose, guarded
                                          # by _miscategorised and owed a leakage fix
        out.add(s[:160])
    return out


def _classifier():
    """(is_student, why) -- decided against the CORPUS, not against a pattern.

    The regex above is a CANDIDATE GENERATOR and nothing more. Segment scanning
    removed its blind spot at the cost of false positives: 114 of them against 63
    real quotes, and a gate that cries wolf twice for every true call teaches
    people to reach for the override. But every one of those 114 was decidable by
    two questions this repo can actually answer:

        is the text in the STUDENT CORPUS at all?   if not, nobody's words
        is it also in the COURSE .olx?              if so, authored scaffolding
                                                     a student echoed back

    So the corpus does the classifying and the regex only proposes. That is the
    same pair of questions `_launders` asks of a declaration, applied one step
    earlier so the declaration is not needed at all.

    WHEN THE CORPUS IS ABSENT THIS FAILS CLOSED. No corpus means no way to tell
    a student's sentence from ours, and the safe answer is to flag every
    candidate and say why -- noisy, but a false positive costs a declaration and
    a false negative costs a disclosure.
    """
    try:
        sys.path.insert(0, HERE)
        import corpus_ref as CR
        idx = CR._index()
    except Exception as e:
        return None, f"corpus unreadable ({type(e).__name__}); flagging every candidate"
    if not idx:
        return None, "corpus resolved to zero cells; flagging every candidate"
    norm = lambda s: _re.sub(r"\s+", " ", _re.sub(r"['\u2019]", "'", s)).strip().lower()
    cells = {k: norm(v) for k, v in idx.items()}
    try:
        import olx_prompts as _O
        course = norm(" ".join(_O._src(h) for h in (1, 2, 3)))
    except Exception:
        course = ""

    # COVERAGE: how much of the candidate is the student's words. A sentence of
    # ours can contain a run a student also wrote -- the handout's own question,
    # echoed back into an answer, matches on 14% of itself -- and flagging that
    # as a quotation is the false alarm this threshold removes.
    #
    # 0.20, AND THE EVIDENCE IS THINNER THAN IT LOOKS. Measured over 16 confirmed
    # quotations and 114 false positives: at 0.20 nothing real is lost and 44 of
    # the 114 go quiet; at 0.30 a real one is lost. But the two distributions
    # OVERLAP -- the false-positive median is 0.30, above the real minimum of
    # 0.29 -- so this is a partial filter and never a classifier. It is set low
    # on purpose: 0.20 keeps a 0.09 margin under the lowest real quotation,
    # where 0.25 would keep 0.04. (The 518 references in the tree all measure
    # 1.00, which confirms none is malformed and proves nothing about the
    # threshold: a reference resolves to exact corpus text by construction.)
    MIN_COVERAGE = 0.20

    def is_student(q):
        w = q.split()
        longest = 0
        for i in range(len(w)):
            for j in range(len(w), i + 2, -1):
                n = norm(" ".join(w[i:j]))
                if len(n) < 18:
                    continue
                if not any(n in v for v in cells.values()):
                    continue
                if course and n in course:
                    return False          # the handout says it; a student echoed it
                longest = max(longest, len(n))
                break
        if not longest:
            return False
        # A HANDOUT QUESTION IS NOT STUDENT TEXT, however much of it a student
        # copied into an answer. The exact-substring test above misses it when we
        # PARAPHRASE the question in our own prose -- reflowed, abbreviated, or
        # quoted in part -- so ask the same longest-run question of the course
        # text and attribute the candidate to whichever source explains more of
        # it. The handout's own SMART-goal question matched a cell on 14% of
        # itself and the handout on far more; it is the course's sentence.
        if course:
            course_longest = 0
            for i in range(len(w)):
                for j in range(len(w), i + 2, -1):
                    n = norm(" ".join(w[i:j]))
                    if len(n) < 18:
                        continue
                    if n in course:
                        course_longest = max(course_longest, len(n))
                        break
            if course_longest >= longest:
                return False
        return longest / max(1, len(norm(q))) >= MIN_COVERAGE
    return is_student, "classified against the corpus"


def _staged_counts() -> dict:
    """Per-file counts of what is ABOUT TO BE COMMITTED, not what is on disk.

    Reads each blob from the index (`git show :path`). Checking the working tree
    would let an unstaged edit hide a quote that the commit still carries.
    """
    files = subprocess.run(["git", "diff", "--cached", "--name-only",
                            "--diff-filter=ACMR"],
                           capture_output=True, text=True, cwd=HERE).stdout.split()
    is_student, _why = _classifier()
    counts = {}
    for f in files:
        if f.endswith(EXCLUDED_SUFFIXES) or not f.endswith(SCANNED_SUFFIXES):
            continue
        blob = subprocess.run(["git", "show", f":{f}"],
                              capture_output=True, text=True, cwd=HERE)
        if blob.returncode:
            continue
        qs = _quotes(blob.stdout)
        if is_student is not None:
            qs = {q for q in qs if is_student(q)}
        if qs:
            counts[f] = len(qs)
    return counts


def _student_text_gate() -> int:
    """0 to proceed. Runs BEFORE the audit: it is instant and the audit is not."""
    try:
        with open(BUDGET) as fh:
            base = _json.load(fh)
    except FileNotFoundError:
        return 0                      # not yet baselined; `--baseline` writes it
    now = _staged_counts()
    grew = {f: (base.get(f, 0), n) for f, n in now.items() if n > base.get(f, 0)}
    if grew:
        print("REFUSING the commit: it adds student text to the repo.\n",
              file=sys.stderr)
        for f, (was, is_) in sorted(grew.items()):
            print(f"    {f}: {was} -> {is_}", file=sys.stderr)
            blob = subprocess.run(["git", "show", f":{f}"], capture_output=True,
                                  text=True, cwd=HERE).stdout
            for s in sorted(_quotes(blob))[:3]:
                print(f"        {s[:110]!r}", file=sys.stderr)
        print("\nQuote the CELL, not the answer -- `Q5/p4's first entry` says "
              "everything\n`\"{{corpus:Q5/p4:first:0:23:sha=d62be9bed4ca}}...\"` says, without "
              "carrying a student's words.\nTo commit anyway, say why:\n"
              '    ALLOW_STUDENT_TEXT="..." git commit ...', file=sys.stderr)
        why = (os.environ.get("ALLOW_STUDENT_TEXT") or "").strip()
        if len(why) < 15:
            if why:
                print(f"\npre-commit: override refused, the reason given is "
                      f"{len(why)} characters.", file=sys.stderr)
            return 1
        print(f"\npre-commit: student-text gate OVERRIDDEN -- {why}",
              file=sys.stderr)
    # The ratchet only ever tightens. A commit that REMOVES quotes lowers the
    # bar and stages the new bar with it, so the reduction cannot be undone by a
    # later commit without tripping the gate.
    lowered = {f: (base[f], now.get(f, 0)) for f in base
               if now.get(f, base[f]) < base[f]}
    if lowered:
        new = dict(base)
        for f, (_, n) in lowered.items():
            if n:
                new[f] = n
            else:
                new.pop(f, None)
        for f, n in now.items():
            new[f] = max(n, new.get(f, 0)) if f in grew else new.get(f, n)
        with open(BUDGET, "w") as fh:
            _json.dump(dict(sorted(new.items())), fh, indent=1)
            fh.write("\n")
        subprocess.run(["git", "add", BUDGET], cwd=HERE)
        total = sum(lowered[f][0] - lowered[f][1] for f in lowered)
        print(f"pre-commit: student-text budget lowered by {total} across "
              f"{len(lowered)} file(s)", file=sys.stderr)
    return 0


def main() -> int:
    if "--audit-exemptions" in sys.argv:
        bad = _launders()
        print(f"NOT_STUDENT_TEXT: {len(NOT_STUDENT_TEXT)} entr(ies), {len(bad)} "
              f"laundering student text", file=sys.stderr)
        for b in bad:
            print(f"    {b}", file=sys.stderr)
        co = _implausible_coincidence()
        print(f"COINCIDENTAL_TEXT: {len(COINCIDENTAL_TEXT)} entr(ies), {len(co)} "
              f"implausible", file=sys.stderr)
        for c in co:
            print(f"    {c}", file=sys.stderr)
        mis = _miscategorised()
        print(f"ACCEPTED_STUDENT_TEXT: {len(ACCEPTED_STUDENT_TEXT)} entr(ies), "
              f"{len(mis)} in the wrong table", file=sys.stderr)
        for m in mis:
            print(f"    {m}", file=sys.stderr)
        return 1 if (bad or mis or co) else 0
    if _student_text_gate():
        return 1
    reason = (os.environ.get("ALLOW_UNDECLARED") or "").strip()
    r = subprocess.run([sys.executable, os.path.join(HERE, "equivalence.py"),
                        "--enforcement"], capture_output=True, text=True, cwd=HERE)
    lines = [l for l in (r.stdout + r.stderr).splitlines() if l.startswith("! ")]
    blocking = [l for l in lines if not any(k in l for k in STATE_ONLY)]
    if not blocking:
        state = len(lines) - len(blocking)
        print(f"pre-commit: enforcement audit clean"
              + (f" ({state} stale-measurement flag(s), not blocking)" if state else ""),
              file=sys.stderr)
        return 0
    print("REFUSING the commit: the CLI and web scorers differ and it is not "
          "declared.\n", file=sys.stderr)
    for l in blocking:
        print(f"    {l.strip()}", file=sys.stderr)
    print("\nDeclare it in olx_prompts.SCORING_DIVERGENCES with a reason, or fix "
          "the difference.\nTo commit anyway, say why:\n"
          '    ALLOW_UNDECLARED="..." git commit ...', file=sys.stderr)
    if len(reason) >= 15:
        state = [l for l in lines if l not in blocking]
        status = _record(blocking, state, reason)
        print(f"\npre-commit: OVERRIDDEN — {reason}", file=sys.stderr)
        print(f"pre-commit: {status}", file=sys.stderr)
        return 0
    if reason:
        print(f"\npre-commit: override refused, the reason given is {len(reason)} "
              f"characters. Say what makes this acceptable.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
