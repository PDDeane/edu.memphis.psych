"""Find student response language smuggled into the rules we author.

A rule that quotes the cohort is not a rule; it is an answer key for one cell.
It scores that cell correctly and teaches us nothing about whether the criterion
generalises, and because the borrowed sentence is usually taken from the very
cell the rule was written to fix, the gain it reports is circular. Two of this
project's recorded gains were found to rest on quoted prose AFTER they had been
measured, reported and committed — DAY1's avoidance rule reproducing DAY1/p8
almost word for word, WK1's agent rule quoting WK1/p1 verbatim.

That is why this runs as a GATE before a sweep rather than as advice in a guide.
A sweep launched over quoted prose spends its calls proving that we can copy.

    python3 leakage.py                     # report on the four cadence items
    python3 leakage.py --items ALL         # every item in handout 2
    python3 leakage.py --gate --items DAY1,WK1     # exit 1 if anything unreviewed
    python3 leakage.py --review <sha> --verdict vocabulary --note "..."

WHAT IT COMPARES. Every block of authored prose a grader sees — rubric
`guidance` and `rule` strings, and `olx_prompts.SLOT_NOTES` — against every
response field in the fixtures, reporting the content bigrams they share.

WHAT A SHARED BIGRAM MEANS. Three different things, and the tool cannot tell
them apart; a person must.

  DOMAIN VOCABULARY ("positive reinforcement", "take away", "target behavior")
  is what the handout is about. Both sides must use it. Spread across many
  students, which is the signal that it is vocabulary and not a quotation.

  COINCIDENCE — an invented example landing on a stock phrasing a student also
  used. "this should {{corpus:NR/p12:nr:123:139:sha=d881672437f8}} goal" was written here independently and
  collides with DAY2/p17. Usually one student, usually one short pair.

  QUOTATION — a rule example traceable to one student, often the very cell the
  rule was written for. This is the fault. The tell is a RUN of shared bigrams
  concentrated in a single student.

So the report ranks by concentration among distinct STUDENTS (participants are
the same people across DAY1/DAY2/WK1/WK2, so counting item-participant pairs
would score one student's recurring phrase as four).

THE REVIEW LEDGER. Judgement is not automatable, so it is recorded instead.
`--review` files a verdict against the SHA OF THE PROSE ITSELF. Edit the block
and its sha changes, the waiver lapses, and the gate asks again — which is the
property that matters, because a rule is usually re-worded at exactly the moment
someone is tempted to paste a student's sentence into it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import warnings

warnings.filterwarnings("ignore")

HERE = os.path.dirname(os.path.abspath(__file__))
REVIEWS = os.path.join(HERE, "LEAKAGE_REVIEWED.json")

CADENCE = ("DAY1", "DAY2", "WK1", "WK2")
VERDICTS = ("vocabulary", "coincidence", "rewritten")

# Words too common to carry evidence of copying. Deliberately short: the point
# is to catch content, and an over-long stoplist hides the very runs we want.
STOP = set("""
a an and the to of for i my me it that this is are be will would can could
in on at as so then with when if do does did have has had not no or but you
your they them something anything one two up out off from by about into over
under than there here what which who whom whose all any each every some more
most less least good bad well badly been being was were am
""".split())

# A block is flagged when this many of its shared bigrams are EXCLUSIVE to one
# student — present in that student's responses and in no other student's.
#
# Exclusivity, not frequency, is what separates a quotation from vocabulary, and
# getting this wrong the first time is instructive. Ranking by "how many of the
# shared bigrams does one student account for" flagged Q3's Time-Bound rule at
# 9 of 9 "from p1 alone" — but every one of those nine ("baseline data", "four
# weeks", "week baseline") appears in ten to sixteen students, because the
# assignment prescribes that structure. One student merely happened to contain
# all nine. Filtering to bigrams NO OTHER student used drops Q3 to zero and
# leaves the real quotations standing, which is the same filter
# `enforcement.check_rule_examples_are_not_corpus` applies to its 6-grams.
MIN_EXCLUSIVE = 2

# A SINGLE word can leak, and the bigram rule cannot see it. Two cases found by
# hand after passing every check: "procrastinating" left in `trigger_behavior`'s
# example list, which is WK1/p7's own trigger word; and "a phone, a snack, an
# evening out, music" offered as valence examples, which are the objects in
# NR/p14, PP/p14, NP/p14 and DAY1/p6 -- the four cells that rule scores.
#
# Neither is EXCLUSIVE to one student, so the bigram filter is blind to both:
# "phone" is in three students' answers. What makes them leak is being CONCRETE
# and CORPUS-SPECIFIC while the rule judges the very cells they come from.
#
# Rarity is the usable proxy. A word the assignment itself uses is shared by
# necessity; a word a handful of students happen to use is theirs. The threshold
# is a fraction of the cohort rather than a count, so it survives a corpus of a
# different size. See the correction above: 4 of 20, not 6.
# LOWERED 6 -> 4 on 2026-09-06. The user's objection was that the detector fired
# on "words, bigrams and verbatim sequences that are nothing but high frequency,
# utterly ordinary words", and the measurement agreed: at 6 the word report gave
# 24 findings, at 4 it gives 1. The 23 that went were words a QUARTER of the
# cohort used -- food (5 students), goals (6), commonly, completing, leaving,
# average, turn. A word five students wrote is the assignment's subject matter,
# not one student's phrasing.
#
# 4 IS THE FLOOR THE KNOWN CASES SET, not a round number: `procrastinating` is 2
# students and the valence objects `snack` and `music` are 4 each, so anything
# below 4 loses the leak this filter was built for.
#
# AND THE EXAMPLE JUSTIFYING IT WAS WRONG. The note below said "'phone' is in
# three students' answers"; phone is in FIFTEEN, so this filter never could have
# caught it and never did. Corrected rather than deleted, because the reasoning
# it was offered for still holds -- it just needed a case that is true.
MAX_STUDENTS_FOR_INFORMATIVE = 4


# LANGUAGE FROM OUR OWN PROCESS, LEAKING INTO THE PROMPT. The sibling problem to
# the one this module was built for. There, the cohort's words get into a rule
# and the rule stops generalising; here, the MAINTAINER'S words get in and the
# grader is told about our sweeps, our dates and our ledger -- none of which it
# can act on, and all of which it must nonetheless read and weigh.
#
# The case that prompted this: 2a's second guidance bullet ended "A rule that
# charged boxes of that shape was measured on 2026-09-02 and broke three cells
# the graders credit." The RULE is stated completely in the two sentences before
# it; that sentence is the ARGUMENT FOR the rule, addressed to whoever next
# edits the rubric. It shipped to both sides.
PROCESS_PATTERNS = {
    "a dated measurement":      r"\b20\d\d-\d\d-\d\d\b",
    "a measurement reported":   (r"\b(was|were) measured\b|\bmeasured on\b"
                                 r"|\bre-?measured\b|\bbroke \w+ cells?\b"
                                 r"|\b\w+ cells the graders\b|\b\d+ ?/ ?\d+ cells?\b"),
    "our process vocabulary":   (r"\bsub-?goal\b|\bsweeps?\b|\bswept\b"
                                 r"|\bre-?sweep\b|\breverted\b|\bthe ledger\b"),
    "our code or artefacts":    (r"\bscore\.py\b|\bagreement\.py\b|\bolx_prompts\b"
                                 r"|\bslotSheet\b|\bprompt sha\b|\bthe \.olx\b"),
    "this rubric's own history": (r"\bearlier wording\b|\bthis rubric (said|used to)\b"
                                  r"|\ban earlier version of this rubric\b"),
}

# CONVENTIONS, NOT ACCIDENTS -- deliberate and pervasive, so they are declared
# rather than reported. Each is maintainer vocabulary by origin, and each is a
# CORPUS-WIDE prompt change to remove, needing its own measurement on both
# sides. Listed so the decision stays visible instead of being lost in the
# noise floor of a check that reports a hundred hits.
PROMPT_CONVENTIONS_DECLARED = {
    r"\bthe graders\b":
        "~104 uses. Refers to the human raters whose practice the rubric "
        "encodes -- 'the graders charged nothing for it'. Arguably it conveys "
        "the STANDARD to the model rather than our process, which is why it is "
        "declared and not condemned. Removing it is a corpus-wide rewrite.",
    r"\bIMPLICIT \(from gold\)\b":
        "~23 uses. A provenance annotation marking a rule read off gold rather "
        "than authored. 'From gold' names OUR artefact and means nothing to a "
        "grader; the rule after the colon is what it needs. A candidate for "
        "removal, measured.",
    r"\bthis rubric\b|\bthe rubric\b":
        "~47 uses, mostly self-reference to the criteria the grader is being "
        "given, which is legible to it. The HISTORY uses -- 'the earlier "
        "wording of this rubric' -- are caught separately above.",
}


def process_findings(items: tuple) -> list[dict]:
    """Authored prose carrying language from our process rather than the task.

    Reuses `authored`, so it sees exactly what a grader sees: rubric `guidance`
    and `rule` strings and `olx_prompts.SLOT_NOTES`. A hit is reported with the
    block it came from and the phrase in context; the declared conventions above
    are not reported.
    """
    import re as _re

    out = []
    for key, text in authored(items).items():
        for name, pat in PROCESS_PATTERNS.items():
            for m in _re.finditer(pat, text, _re.I):
                s, e = max(0, m.start() - 70), min(len(text), m.end() + 70)
                out.append({"block": str(key), "kind": name,
                            "phrase": m.group(0),
                            "context": " ".join(text[s:e].split())})
    return out


def _content(text: str) -> list[str]:
    return [w for w in re.findall(r"[a-z']+", (text or "").lower())
            if w not in STOP and len(w) > 3]


def _bigrams(words: list[str]) -> set[str]:
    return {f"{a} {b}" for a, b in zip(words, words[1:])}


def sha(text: str) -> str:
    """Identity of a block is its prose. Re-word it and the waiver lapses."""
    return hashlib.sha256(" ".join((text or "").split()).encode()).hexdigest()[:12]


def load_reviews() -> dict:
    try:
        with open(REVIEWS) as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def save_reviews(data: dict) -> None:
    with open(REVIEWS, "w") as fh:
        json.dump(data, fh, indent=1, sort_keys=True)
        fh.write("\n")


def cohort(items: tuple[str, ...]) -> dict[tuple[str, int, str], str]:
    """Every non-empty response field the graders read, keyed by where it came from."""
    import agreement as A
    out: dict[tuple[str, int, str], str] = {}
    for item in items:
        for pid in range(1, 21):
            try:
                fixture = A.fixture_for(item, pid)
            except Exception:
                continue
            for field, value in (fixture or {}).items():
                if (value or "").strip():
                    out[(item, pid, field)] = value.strip()
    return out


def _specs() -> dict[str, dict]:
    """Every rubric item across the three handouts, keyed by id."""
    import handouts as H
    out: dict[str, dict] = {}
    for h in (1, 2, 3):
        try:
            for item in H.config(h)["rubric"].ITEMS:
                out[item["id"]] = item
        except Exception:
            continue
    return out


def authored(items: tuple[str, ...]) -> dict[str, str]:
    """Every block of prose we wrote that reaches a grader."""
    specs = _specs()
    blocks: dict[str, str] = {}
    for item in items:
        spec = specs.get(item) or {}
        guidance = spec.get("guidance") or []
        for g in (guidance if isinstance(guidance, list) else [guidance]):
            blocks[f"{item} guidance :: {str(g)[:52]}"] = str(g)
        for r in spec.get("rules") or []:
            blocks[f"{item} rule :: {str(r)[:52]}"] = str(r)
        # `desc` and `rule` on a credit line are prompt text too, and three of
        # the leaks found here lived there rather than in guidance.
        for c in spec.get("credit") or []:
            for field in ("desc", "rule"):
                if c.get(field):
                    blocks[f"{item} credit.{field} :: {str(c[field])[:52]}"] = str(c[field])
    try:
        import olx_prompts as OP
        for key, note in (getattr(OP, "SLOT_NOTES", {}) or {}).items():
            blocks[f"SLOT_NOTES {key}"] = str(note)
    except Exception:
        pass
    # EVERYTHING ELSE THE GRADER READS. Subgoal E54. The four containers above
    # are where prompt prose is AUTHORED; they are not where it all ENDS UP. The
    # numbered criteria list is built by olx_prompts._criteria_section and is in
    # none of them, so about 40% of each cadence prompt was never compared with
    # the corpus -- and two verbatim student quotations were living in it, one of
    # them the DAY1/p8 leak this module's own docstring cites as its founding
    # case and treats as fixed. It was fixed in the prose scanned here and
    # survived in the prose that was not, so the repair and the blind spot were
    # the same event.
    #
    # THE FIX DERIVES THE CORPUS FROM THE RENDERED PROMPT rather than from the
    # sources, which is the move `enforcement.check_no_case_names_in_prompts`
    # already makes for cohort names and for the same stated reason: reading the
    # sources leaves whichever route nobody thought of. Safe to do here because
    # `build_web_prompt` renders responses as REF placeholders and embeds no
    # student text -- verified over both handouts before this was written.
    #
    # The remainder is added as its OWN block rather than replacing the granular
    # ones, so every existing review sha keeps its verdict.
    # AGAINST A SNAPSHOT, NOT THE GROWING DICT. Computed in place, each item's
    # remainder landed in `blocks` and then counted as "already covered" for the
    # next item, so DAY1 got 13,602 chars and WK2 got 496 of the SAME shared
    # criteria text -- coverage that silently depended on which items were passed
    # and in what order. The shared prose is now reported once per item; that is
    # deliberate duplication, and it costs nothing, because the review ledger
    # keys on the sha of the prose itself, so identical text takes ONE verdict to
    # clear on all four.
    baseline = dict(blocks)
    for item in items:
        for label, text in _prompt_remainder(item, baseline):
            blocks[f"{item} prompt :: {label}"] = text
    return blocks


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", str(s)).strip().lower()


MIN_VERBATIM_WORDS = 6


def coverage_gaps() -> list[str]:
    """Lines of a SHIPPED prompt that look like prose and are scanned by nothing.

    THE PROOF E54 ASKED FOR, rather than the assertion. Widening the corpus to
    `build_web_prompt` is only worth anything if the widening is COMPLETE, and
    "I derived it from the prompt" is not a measurement -- the first version of
    that derivation dropped every numbered criterion by splitting on sentence
    boundaries, and looked fine.

    Measured over all 26 items, 2,199 prompt lines: 1,871 sit in a scanned
    block, 127 are the item's own question or deduction text (excluded on
    purpose -- a student echoing the question is the instrument working), 120 are
    short headings, and 81 are headings and `REF:` placeholders. ZERO carry
    prose. This function keeps that true.

    A line counts as prose if it has six or more words and is not a heading, a
    section label or a REF placeholder -- deliberately loose, because a false
    positive here costs a glance and a false negative costs the whole point of
    the widening.
    """
    import olx_prompts as OP
    out: list[str] = []
    for item in sorted(_specs().keys()):
        try:
            prompt = OP.build_web_prompt(item)
        except Exception:
            continue
        scanned = _norm(" ".join(authored((item,)).values()))
        spec = _specs()[item]
        own = [_norm(spec.get("question") or "")]
        own += [_norm(d.get("text") or "") for d in (spec.get("deductions") or [])]
        own = [x for x in own if x]
        for raw in prompt.splitlines():
            line = raw.strip()
            s = _norm(line)
            if not s or s in scanned:
                continue
            if any(s in o or o in s for o in own):
                continue
            if line.startswith("#") or "REF:" in line or line.endswith(":"):
                continue
            if len(s.split()) >= 6:
                out.append(f"{item}: prose line scanned by nothing -- {line[:90]!r}")
    return out


def verbatim_findings(items: tuple[str, ...]) -> list[dict]:
    """Blocks sharing a long VERBATIM word-span with exactly one student.

    THE BIGRAM METHOD CANNOT SEE THIS SHAPE, and the leak that founded this
    module is the proof. Criterion 7 quoted DAY1/p8 as "so I don't have to do {{corpus:DAY1/p8:day1:117:137:sha=aa91092efc87:shape=S0-0a20202020}} it" against p8's "{{corpus:DAY1/p8:day1:89:137:sha=df3811e737eb:shape=S9-0a20202020}} it". Run that through `_content` -- which drops stopwords and words of
    three letters or fewer -- and the prompt keeps ["don't","pushups","miss"] and
    p8 keeps ["don't","extra","pushups","miss"]. ONE shared bigram, "pushups
    miss", against MIN_EXCLUSIVE = 2. The tool could never have flagged it at any
    granularity or any scope, and it did not: that leak was found BY HAND.

    So this is not a coverage gap like the corpus one -- it is a DETECTOR gap. A
    quotation whose distinctive content is stopwords, numbers and short words is
    invisible to a content-bigram filter, and quoted EXAMPLES are exactly the
    place such phrasing lives, because they are written to sound like a student.

    Raw spans, no stopword filter, no length filter: the longest run of words
    appearing verbatim in both an authored block and one student's response.
    Six words is the threshold `enforcement.check_rule_examples_are_not_corpus`
    already uses for the same purpose on a narrower corpus.
    """
    blocks = authored(items)
    responses = cohort(items)
    by_student: dict[int, str] = {}
    for (item, pid, field), text in responses.items():
        by_student[pid] = by_student.get(pid, "") + " " + text

    def words(s: str) -> list[str]:
        return re.findall(r"[a-z0-9']+", (s or "").lower())

    student_spans: dict[int, set[str]] = {}
    for pid, text in by_student.items():
        w = words(text)
        student_spans[pid] = {" ".join(w[i:i + MIN_VERBATIM_WORDS])
                              for i in range(len(w) - MIN_VERBATIM_WORDS + 1)}

    out: list[dict] = []
    for label, text in blocks.items():
        w = words(text)
        spans = {" ".join(w[i:i + MIN_VERBATIM_WORDS])
                 for i in range(len(w) - MIN_VERBATIM_WORDS + 1)}
        for pid, ss in student_spans.items():
            shared = spans & ss
            if not shared:
                continue
            # Exclusive to this student, same rule the bigram filter uses: a span
            # several students wrote is the assignment's phrasing, not a quotation.
            excl = [s for s in shared
                    if sum(1 for q in student_spans if s in student_spans[q]) == 1]
            if excl:
                out.append({"label": label, "sha": sha(text), "student": pid,
                            "spans": sorted(excl)[:3], "n": len(excl)})
    return out


def _prompt_remainder(item: str, blocks: dict[str, str]) -> list[tuple[str, str]]:
    """The shipped prompt minus what `blocks` covers, cut into PASSAGES.

    Returns [(label, text), ...] -- one entry per contiguous passage, not one
    per prompt. Subgoal E54.

    WHY PASSAGES AND NOT ONE BLOCK. The first version returned the whole
    remainder as a single ~13KB string. That re-hashes on ANY edit anywhere
    inside it, so its review verdict lapses immediately and a finding points at
    a third of a prompt. Neither is reviewable: a verdict on 13KB says almost
    nothing and survives almost nothing.

    AND THE FIRST VERSION SHREDDED THE STRUCTURE IT NEEDED. It split on
    `(?<=[.!?])\\s+`, which cuts "7. `avoidance_frame` -- true if..." at the
    period after the 7, so not one numbered criterion survived intact and the
    natural boundaries were invisible. Splitting is LINE-based now: the shipped
    prompt is already line-structured, and a line is never half a sentence.

    A passage starts at a numbered criterion, a heading, an ALL-CAPS lead-in, a
    lettered sub-clause, or a blank line -- the places the prompt itself changes
    subject. Edit one criterion and only that criterion's sha moves.
    """
    try:
        import olx_prompts as OP
        prompt = OP.build_web_prompt(item)
    except Exception:
        return []
    covered = _norm(" ".join(blocks.values()))
    spec = (_specs().get(item) or {})
    own = [spec.get("question") or ""]
    own += [d.get("text") or "" for d in (spec.get("deductions") or [])]
    own = [_norm(x) for x in own if _norm(x)]

    BOUNDARY = re.compile(r"^\s*(\d+\.\s|#{1,4}\s|\([a-z]\)|[A-Z][A-Z ,\'`-]{11,})")
    passages: list[list[str]] = []
    for raw in prompt.splitlines():
        line = raw.rstrip()
        s = _norm(line)
        if not s:
            passages.append([])          # blank line ends a passage
            continue
        if len(s) < 25 or s in covered or any(s in o or o in s for o in own):
            continue
        if not passages or BOUNDARY.match(line):
            passages.append([])
        passages[-1].append(line.strip())

    out: list[tuple[str, str]] = []
    for lines in passages:
        if not lines:
            continue
        text = "\n".join(lines)
        # A PASSAGE TOO SHORT TO CARRY A BIGRAM RUN IS MERGED, NOT DROPPED.
        # Dropping it was the first behaviour and it silently un-scanned prose:
        # `coverage_gaps` found Q1's "- The UTB must be one of the four from the
        # closed list.", which is a bullet standing alone between boundaries and
        # falls just under the threshold. The threshold exists so tiny fragments
        # do not each become a block, not so text escapes the corpus -- so it
        # joins the passage above it and the corpus stays whole.
        if out and len(_norm(text)) < 60:
            label, prev = out[-1]
            out[-1] = (label, prev + "\n" + text)
            continue
        label = re.sub(r"\s+", " ", lines[0]).strip()[:46]
        out.append((label, text))
    return out


def _domain_words(items: tuple[str, ...]) -> set[str]:
    """Words the ASSIGNMENT uses, which authored prose cannot avoid re-using.

    Drawn from the items' own question text and the four type definitions rather
    than a hand-kept list, so it cannot go stale: if the handout says it, both
    sides must say it, and it is not a leak however specific it looks.
    """
    specs = _specs()
    txt = " ".join(str((specs.get(i) or {}).get("question") or "") for i in items)
    try:
        import rubric_h2 as R2
        txt += " " + R2._OC_FRAME
    except Exception:
        pass
    return set(_content(txt))


def _segments(text: str) -> list[str]:
    """Sentence-ish units, normalised, for deciding what counts as OUR OTHER prose.

    The unit matters: with the block as the unit, a paragraph duplicated across
    two blocks is "elsewhere" for both and neither copy is ever checked. With the
    sentence as the unit, a shared sentence is excluded from the evidence of every
    block that contains it, so it has to be vouched for by prose that is genuinely
    somewhere else.
    """
    import re as _re
    out = []
    for s in _re.split(r"(?<=[.!?])\s+|\n+", text or ""):
        s = " ".join(s.split())
        if len(s) > 12:
            out.append(s)
    return out or ([" ".join((text or "").split())] if text else [])


# Quoted and parenthesised spans -- where WORKED EXAMPLES live, and where every
# leak this project has actually found was hiding: "procrastinating" in
# trigger_behavior's example list, "a phone, a snack, an evening out, music" in
# the valence examples, DAY1/p8's sentence in criterion 7, WK2/p15's definition
# in criterion 8. All four were quoted illustrations, because an illustration is
# written to sound like a student and that is exactly when someone reaches for a
# student's words.
#
# Backticks are NOT example delimiters here: `activity`, `met`, `wrong_kind` are
# slot and verdict names, our own vocabulary, and including them put the whole
# controlled vocabulary into the detector's mouth.
#
# WHY NARROW AT ALL. The word and bigram reports fire on RARITY AMONG STUDENTS,
# and with twenty short answers that flags ordinary English -- "analysis",
# "food", "goals", "average", "turn", "commonly", "leaving". Measured over the
# corpus, 83% of authored prose is outside any example span, and none of the
# known leaks is out there. Narrowing to examples keeps every real case and
# drops most of the noise.
_EXAMPLE_SPAN = re.compile(r'"[^"]{6,}"|\u201c[^\u201d]{6,}\u201d|\([^)]{6,}\)')


def _examples_only(blocks: dict[str, str]) -> dict[str, str]:
    """Each block reduced to its worked-example spans; empty ones dropped."""
    out: dict[str, str] = {}
    for label, text in blocks.items():
        spans = " ".join(_EXAMPLE_SPAN.findall(text or ""))
        if spans.strip():
            out[label] = spans
    return out


def _assignment_words() -> set:
    """Every word the instrument itself says -- questions, deduction texts,
    guidance, rules. A student using these is echoing the assignment, so their
    appearing in our prose is not a borrowing. 1,222 words, and they accounted
    for 56 of the 90 words flagged before this existed."""
    pool: list[str] = []
    for spec in _specs().values():
        pool.append(str(spec.get("question") or ""))
        pool += [str(d.get("text") or "") for d in (spec.get("deductions") or [])]
        g = spec.get("guidance") or []
        pool += [str(x) for x in (g if isinstance(g, list) else [g])]
        pool += [str(r) for r in (spec.get("rules") or [])]
    return set(re.findall(r"[a-z']+", " ".join(pool).lower()))


def word_findings(items: tuple[str, ...]) -> list[dict]:
    """Authored blocks re-using a CONCRETE word from a few students' answers.

    Complements `findings`, which needs a shared PAIR. A rule that lists the very
    objects the cohort wrote about is teaching to the test one noun at a time.
    """
    responses = cohort(items)
    students: dict[str, set[int]] = {}
    for (_item, pid, _f), text in responses.items():
        for w in set(_content(text)):
            students.setdefault(w, set()).add(pid)
    domain = _domain_words(items) | _assignment_words()
    reviews = load_reviews()
    blocks = _examples_only(authored(items))
    # OUR OWN vocabulary, derived rather than hand-kept: every word used in some
    # OTHER authored block. Rarity alone is not informativeness -- with twenty
    # students and short answers, ordinary English words like "already" or
    # "cannot" appear in only a handful, and flagging those buried the real cases
    # 196 blocks deep. A word we use elsewhere in our own prose is ours; a word
    # that appears NOWHERE else in it, and does appear in a few students'
    # answers, is theirs. That is what separates "phone" and "procrastinating"
    # from "activity".
    # OUR OWN prose has to be prose THIS BLOCK DOES NOT CONTAIN, or duplicated
    # text vouches for itself and can never be flagged. Measured before fixing:
    # 139 of 301 blocks carry a full text that also appears verbatim in another
    # block, and 114 sentences appear in more than one block, filling 526 block
    # slots -- the four-type operant definition alone sits in twelve. Under the
    # old per-block union every word of all of that was "elsewhere", so nearly
    # half the authored prose was exempt from the check that exists to police it.
    # `_MOVE_RULE` sat unchecked in four prompts for exactly this reason.
    #
    # Sentence granularity, not block: a paragraph shared between two otherwise
    # different blocks would still vouch for itself if the unit were the block.
    seg_words: dict[str, set[str]] = {}
    block_segs: dict[str, set[str]] = {}
    for lbl, t in blocks.items():
        ss = _segments(t)
        block_segs[lbl] = set(ss)
        for sg in ss:
            seg_words.setdefault(sg, set()).update(_content(sg))
    out: list[dict] = []
    for label, text in blocks.items():
        mine = block_segs.get(label, set())
        elsewhere = set().union(*(w for sg, w in seg_words.items() if sg not in mine)) \
            if any(sg not in mine for sg in seg_words) else set()
        rare = sorted(
            w for w in set(_content(text)) & set(students)
            if w not in domain and w not in elsewhere
            and len(students[w]) <= MAX_STUDENTS_FOR_INFORMATIVE)
        if len(rare) < 2:
            continue
        h = sha(text)
        out.append({"label": label, "sha": h, "text": text, "kind": "word",
                    "shared": rare, "hits": len(rare),
                    "owners": {w: sorted(students[w]) for w in rare},
                    "review": reviews.get(h)})
    out.sort(key=lambda f: -f["hits"])
    return out


def findings(items: tuple[str, ...]) -> list[dict]:
    """Flagged blocks, worst concentration first, each tagged with its review."""
    responses = cohort(items)
    students: dict[str, set[int]] = {}      # bigram -> distinct participant ids
    where: dict[str, set[str]] = {}         # bigram -> "ITEM/pN" labels
    for (item, pid, _field), text in responses.items():
        for b in _bigrams(_content(text)):
            students.setdefault(b, set()).add(pid)
            where.setdefault(b, set()).add(f"{item}/p{pid}")

    # A BIGRAM OF TWO ORDINARY WORDS IS NOT EVIDENCE. Exclusivity alone let
    # 'fixed schedule', 'many times', 'look like', 'keep doing' and 'whole week'
    # stand as findings -- stock English that one student happened to be the only
    # one to write. So a shared bigram now counts only if at least ONE of its two
    # words is itself informative: rare across the cohort, and not part of the
    # assignment's own vocabulary or the item's domain words. The verbatim
    # detector carries the long-quotation cases, so tightening here loses nothing
    # the tool can otherwise see.
    per_word: dict[str, set[int]] = {}
    for (item, pid, _field), text in responses.items():
        for w in set(_content(text)):
            per_word.setdefault(w, set()).add(pid)
    ordinary = _domain_words(items) | _assignment_words()

    def _informative_pair(bigram: str) -> bool:
        return any(w not in ordinary
                   and 0 < len(per_word.get(w, ())) <= MAX_STUDENTS_FOR_INFORMATIVE
                   for w in bigram.split())

    reviews = load_reviews()
    out: list[dict] = []
    for label, text in _examples_only(authored(items)).items():
        shared = {b for b in _bigrams(_content(text)) & set(students)
                  if _informative_pair(b)}
        # Only bigrams no other student used. Anything two students wrote is the
        # handout's language, however striking it looks.
        exclusive: dict[int, list[str]] = {}
        for b in shared:
            if len(students[b]) == 1:
                exclusive.setdefault(next(iter(students[b])), []).append(b)
        if not exclusive:
            continue
        top_pid, own = max(exclusive.items(), key=lambda kv: len(kv[1]))
        if len(own) < MIN_EXCLUSIVE:
            continue
        h = sha(text)
        out.append({
            "label": label, "sha": h, "text": text,
            "shared": sorted(own),
            "owners": {b: sorted(where[b]) for b in sorted(own)},
            "top_participant": top_pid, "hits": len(own),
            "review": reviews.get(h),
        })
    out.sort(key=lambda f: -f["hits"])
    return out


def unreviewed(items: tuple[str, ...] = CADENCE) -> list[str]:
    """One line per flagged block with no standing verdict. The gate's payload.

    AUDITS EVERY ITEM and ignores `items`, for the reason spelled out on `gate`:
    both filters that decide a flag are computed over the scope given, so a
    narrow scope makes ordinary English look borrowed. Every enforcement caller
    -- the sweep gate and `measured.py --preflight` -- comes through here, so
    they cannot disagree about whether the same prose is clean.
    """
    items = tuple(_specs())
    pending = [f"{f['label']}  [sha {f['sha']}] — {f['hits']} bigram(s) "
               f"used by p{f['top_participant']} and no other student"
               for f in findings(items) if not f["review"]]
    pending += [f"{f['label']}  [sha {f['sha']}] — {f['hits']} concrete word(s) "
                f"from few students' answers: "
                + ", ".join(f"{w} (p{'/p'.join(str(x) for x in f['owners'][w][:3])})"
                            for w in f["shared"][:4])
                for f in word_findings(items) if not f["review"]]
    return pending


def gate(items: tuple[str, ...], stream=sys.stderr) -> int:
    """0 to proceed, 1 to refuse. Called before a sweep spends anything.

    AUDITS EVERY ITEM, whatever is being swept. The `items` argument is kept for
    the caller's convenience and deliberately ignored, because both filters that
    decide a flag are computed OVER THE SCOPE GIVEN: `_domain_words` from the
    items' question text, and `ours` from the other authored blocks in scope.
    Narrow the scope and ordinary English stops looking ordinary -- auditing WK1
    alone flagged "work", "food", "healthy" and "should" as concrete borrowings,
    because no other block in scope used them. The same prose passes at ALL.
    A leak is a leak whatever is being measured, so the audit does not narrow.
    """
    # THE VERBATIM CHECK REFUSES OUTRIGHT, unlike the bigram report. It has no
    # review ledger and needs none: a six-word span appearing verbatim in a
    # prompt and in exactly ONE student's answer is not vocabulary and not
    # coincidence, and measured over all 26 items on a clean tree it finds
    # NOTHING. So a hit is a fault, not a judgement call, and there is nobody to
    # ask about it -- rewrite the example.
    for v in verbatim_findings(items or CADENCE):
        print(f"REFUSING: {v['label']} shares a {MIN_VERBATIM_WORDS}-word verbatim "
              f"span with p{v['student']} AND NO OTHER STUDENT: "
              f"{v['spans'][0]!r}", file=stream)
        return 1

    pending = unreviewed()
    # THE NEW CORPUS REPORTS BUT DOES NOT YET REFUSE. Subgoal E54 widened the
    # scanned prose by about 40% (olx_prompts._criteria_section and everything
    # else that reaches the shipped prompt), and that first pass raises 23
    # findings on blocks nobody has ever read. Promoting them straight to a
    # refusal would have blocked five queued sweeps behind an unscoped check --
    # the exact failure this series keeps recording: E48's first cut was 12
    # findings with 10 false, E49's 119 with 1 real, E52's 39 with ~37 by design,
    # and a check whose false positives outnumber its true ones gets switched off
    # and takes the real finding with it.
    #
    # NOT A SUPPRESSION: every remainder finding is PRINTED, under its own label
    # and sha, so the report shows exactly what the old corpus was blind to. What
    # is deferred is only the exit code.
    #
    # TO PROMOTE IT, and this is the remaining work on E54: the blocks are far
    # too coarse to verdict honestly. One remainder block is ~13KB of a whole
    # prompt, so it re-hashes on ANY edit anywhere inside it and its waiver
    # lapses immediately -- a verdict on a block that large says almost nothing
    # and survives almost nothing. Split the remainder into contiguous passages
    # first, so a finding points at a passage and a verdict outlives an unrelated
    # edit; THEN flip this to gating.
    # PROMOTED TO GATING 2026-09-06, once there was nothing to promote OVER.
    # These reported without refusing while 57 passages stood unread -- blocking
    # every sweep behind an unscoped check is the failure this series keeps
    # recording. After the example-span narrowing, the assignment-vocabulary
    # exclusion, the 6->4 threshold and the bigram informativeness test, the
    # count is ZERO, so gating them costs nothing today and catches the next one.
    # They keep the review ledger: a passage finding can be dispositioned like
    # any other block. Only `verbatim_findings` refuses without appeal.
    if not pending:
        return 0
    print(f"REFUSING to sweep: {len(pending)} rule block(s) share wording with "
          f"the cohort and have no recorded verdict.", file=stream)
    for line in pending:
        print(f"    {line}", file=stream)
    print("\nRead each one against the responses it echoes "
          f"(python3 leakage.py --items {','.join(items)}), then either rewrite "
          "the borrowed example or file a verdict:\n"
          "    python3 leakage.py --review <sha> --verdict vocabulary "
          "--note 'why this is not a quotation'\n"
          "Verdicts are keyed to the prose, so re-wording the block asks again.",
          file=stream)
    return 1


def report(items: tuple[str, ...], show_all: bool = False) -> int:
    found = findings(items)
    print(f"{len(cohort(items))} response fields over {len(items)} item(s); "
          f"{len(authored(items))} authored blocks; {len(found)} flagged\n")
    for f in found:
        if f["review"] and not show_all:
            continue
        mark = f"reviewed:{f['review']['verdict']}" if f["review"] else "UNREVIEWED"
        print(f"[{mark}] {f['label']}")
        print(f"    sha {f['sha']} — {f['hits']} bigram(s) used by "
              f"p{f['top_participant']} and by no other student")
        for b in f["shared"]:
            owners = f["owners"][b]
            tail = "" if len(owners) <= 6 else f" (+{len(owners) - 6} more)"
            print(f"      {b!r:32} {', '.join(owners[:6])}{tail}")
        if f["review"]:
            print(f"    verdict: {f['review'].get('note', '')}")
        print()
    pending = [f for f in found if not f["review"]]
    print(f"{len(pending)} unreviewed; {len(found) - len(pending)} with a "
          f"standing verdict.")
    return 1 if pending else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--items", default=",".join(CADENCE),
                    help="comma-separated item ids, or ALL")
    ap.add_argument("--gate", action="store_true",
                    help="exit 1 with the refusal message if anything is unreviewed")
    ap.add_argument("--all", action="store_true",
                    help="show blocks that already have a verdict too")
    ap.add_argument("--review", metavar="SHA",
                    help="file a verdict against a flagged block")
    ap.add_argument("--verdict", choices=VERDICTS,
                    help="vocabulary | coincidence | rewritten")
    ap.add_argument("--note", default="",
                    help="why this is not a quotation — required with --review")
    args = ap.parse_args()

    if args.items.upper() == "ALL":
        items = tuple(_specs())
    else:
        items = tuple(x.strip() for x in args.items.split(",") if x.strip())

    if args.review:
        if not args.verdict or not args.note.strip():
            ap.error("--review needs --verdict and a --note saying why")
        # BOTH checks, not just the bigram one. The word check can flag a block
        # and the gate refuses on it, but `--review` looked only at `findings()`,
        # so a word finding could block every sweep with no way to file a verdict
        # for it. It never bit while the word check was suppressing duplicated
        # prose; widening that check surfaced 43 findings and the jam with them.
        known = {f["sha"]: f["label"] for f in findings(items) + word_findings(items)}
        if args.review not in known:
            ap.error(f"no flagged block with sha {args.review} in {','.join(items)}")
        data = load_reviews()
        data[args.review] = {"label": known[args.review],
                             "verdict": args.verdict, "note": args.note.strip()}
        save_reviews(data)
        print(f"recorded {args.verdict} for {known[args.review]}")
        return 0

    return gate(items) if args.gate else report(items, args.all)


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    raise SystemExit(main())
