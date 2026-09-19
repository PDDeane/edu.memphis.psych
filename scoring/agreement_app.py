"""Measure the lo-blocks prompts by driving the app, not by imitating it.

This supersedes agreement.py, which called the model itself and carried its own
copy of the scoring rules. Everything substantive now lives where it belongs:

  the prompt and its schema   -> the LLMAction in the .olx
  the call                    -> the app's own LLM client
  the scoring rule            -> SlotSheetGrader / scoreSlotSheet in lo-blocks

What is left here is the two things a harness should do: prepare fixtures from
the paper corpus, and compare the app's output against the graders' rows.

The only arithmetic performed here is turning the grader's fraction into points
(fraction x the sheet's own total). That is arithmetic over what the app
published, not a rule about what anything is worth.

Run:
    python3 agreement_app.py --item Q6                 # all participants
    python3 agreement_app.py --item Q6 --participants 1 5 8

Requires the dev server on 8888. Only items whose slot sheet carries point
values (@n) are gradeable; --list shows which.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile

import simulate_h3
import handouts as _handouts
from handouts import config, exemplar_drops, find_submissions, suspect
from segment import repair_orphans, segment, utb_hint
import paths


# ---------------------------------------------------------------------------
# STAGE 4. These tables were module-level course data here and are read from the
# course file now. The authored copies live in `declaration_source.py`, outside
# the scoring path, because the export must read them from somewhere that does
# not read the file it is writing.
# ---------------------------------------------------------------------------
def _declaration(name: str) -> dict:
    import coursedata

    return coursedata.declaration(name)


# TUPLE VALUES, RESTORED HERE. JSON has no tuple, so `("section", "Q1")` comes
# back as `["section", "Q1"]`. The keys round-trip because `coursedata.
# declaration` restores those; the VALUES do not, and nothing in the file records
# that they were tuples.
#
# The module that knows the contract restores it. This one does: the pairs are
# unpacked positionally and a tuple is what this table has always held. It was
# found by comparing the table against its authored copy after the migration --
# NOT by the behavioural test, which built 26 paper prompts identically while
# this table's shape had quietly changed, because no paper prompt reads it.
# The per-consumer conversion that used to be here is gone: the export TAGS
# tuples now and `coursedata` untags them, so the round trip is exact by
# construction and no consumer has to remember its own value shapes. This was the
# first place the drift was caught; `migrated_tables.py` then found four more in
# `olx_prompts` that nobody had noticed.
CONTEXT_SOURCE = _declaration("CONTEXT_SOURCE")



# Ordinal cues the students actually use.
_SECOND = re.compile(r"\b(my\s+)?(second|2nd|another|other)\b|\b2\s*[).:]", re.I)


def split_two(text: str) -> tuple[str, str, str]:
    """Split one paper answer into the two entries the web version asks for.

    The paper corpus holds each answer as a single block; the web version gives
    the student two boxes. Putting the whole block in the first box and leaving
    the second empty is not neutral — it biases exactly the "is the second one
    there" slots this measures — so the block is split.

    Returns (first, second, how). `how` is reported rather than discarded,
    because the three methods are not equally trustworthy: an explicit "2)" is
    the student's own boundary, one-entry-per-line is nearly as good, and a
    sentence midpoint is a guess that can cut one entry's discussion in half.
    """
    t = (text or "").strip()
    if not t:
        return "", "", "empty"
    m2 = _SECOND.search(t, 1)
    if m2 and m2.start() > 20:
        return t[:m2.start()].strip(), t[m2.start():].strip(), "ordinal"
    lines = [l.strip() for l in t.split("\n") if l.strip()]
    if len(lines) >= 2:
        half = (len(lines) + 1) // 2
        return " ".join(lines[:half]), " ".join(lines[half:]), "lines"
    # No ordinal marker and no line break means the student wrote ONE entry.
    # Splitting at a sentence midpoint invents a second one, which is worse than
    # leaving it empty: an empty second box is a real state the graders penalise
    # ("missing second antecedent"), whereas a fabricated entry is student work
    # that does not exist. Both p9 and p17 were mis-scored this way.
    return t, "", "single"

# How much of the consensus vote must agree on a slot's verdict before the frozen
# span is treated as a reading rather than a coin toss. 0.8 is set just under the
# observed floor: on the current table 158 of 160 slots sit at 1.0 and the other
# two at 0.5, so this separates the real gap without being tuned to it.
CONSENSUS_MIN_SHARE = 0.8

# Cells with no stable ground truth to compare against, per item. Unlike
# handouts.suspect() — which drops a PARTICIPANT from a whole handout because its
# submission cannot be trusted at all — these are single cells where the
# comparison itself is not defined. handouts.exemplar_drops() is a third kind:
# per-item, because self-grading follows the prompt. Passing --exclude explicitly
# overrides all of them.
# The canonical table lives in handouts.py so this side, agreement.py and
# baseline.py cannot drift apart. It was two hand-kept mirrors that happened
# to agree, plus a third harness that had none at all.
PER_ITEM_EXCLUDE = _handouts.PER_ITEM_EXCLUDE

LO = str(paths.lo_root())
RUNNER = paths.RUNNER

# Which screen carries each item, and which paper section feeds each field.
# Fixtures only — no judgement about what anything is worth.
def _namespaced_jobs() -> dict:
    """JOBS with `ns` and the namespaced `screen` recomposed from the course id.

    The file holds the bare screen id and no `ns`, because both repeated the
    course id the file already carries -- and `measured.py` stripped the prefix
    straight back off. Recomposed here so every consumer sees exactly what it saw
    before: this is a change to what is STORED, not to what is read.
    """
    import coursedata

    ns = coursedata.course_id()
    out = {}
    for item, spec in coursedata.declaration("JOBS").items():
        spec = dict(spec)
        spec["ns"] = ns
        if isinstance(spec.get("screen"), str) and "/" not in spec["screen"]:
            spec["screen"] = f"{ns}/{spec['screen']}"
        out[item] = spec
    return out


JOBS = _namespaced_jobs()

# The web version asks for the unwanted behaviour as a closed choice, so the
# fixture has to carry one of its four values — not the paper student's prose,
# which is an input the block cannot hold.
UTB_CHOICES = {
    "lack of sleep": ("sleep",),
    "lack of exercise": ("exercis", "gym", "workout", "work out"),
    "insufficient consumption of fruits and vegetables": ("fruit", "vegetable", "veggie"),
    "spending too much time on electronic devices": (
        "electronic", "phone", "screen", "device", "social media", "tiktok", "video game"),
}


def detect_utb(path: str, q1: str) -> str:
    """Which of the four choices this student picked.

    Prefers the formatting the handout asked for (underline the choice), which
    survives in only some transcriptions, and otherwise reads it from the prose
    the same way the scorer does.
    """
    hint = utb_hint(path)
    if hint:
        return hint
    low = (q1 or "").lower()
    best, score = "", 0
    for value, cues in UTB_CHOICES.items():
        n = sum(low.count(c) for c in cues)
        if n > score:
            best, score = value, n
    return best


SCORER_OUT = str(paths.OUT)


# The shapes the paper scorer writes an extracted value in. `_ANNOTATED` was the
# first of them — `"…" — prose` — and matching only that left 1c's three label
# boxes holding the scorer's own sentences: `"Weeks" appears as a bolded axis
# title centred beneath the day tick values.` went into the field the web grader
# is asked to judge, verdict and all. Twenty boxes across ten cells, and the
# note in EQUIVALENCE.md saying Q6 "is the only `from_scorer` item affected" was
# wrong about that.
_ANNOTATED = re.compile(r'^\s*["“](?P<q>[^"”]*)["”]')
_RUN_LIST = re.compile(r"^\s*\[(?P<inner>[^\]]*)\]")
_RUN = re.compile(r"""('[^']*'|"[^"]*")""")
_RUN_SQ = re.compile(r"^\s*'(?P<q>[^']*)'")


def _quoted_span(ev: str) -> str:
    """A quote the scorer annotated, reduced to the quote.

    Four shapes, all of them seen in `out/h3`'s 1c records:

      "Label" — prose            the original case
      "Label" appears as ...     a sentence, no dash
      "Label" (where it sits)    a parenthetical
      ['A', ' B'] — prose        the chart's text RUNS, as extracted
      'A', ' B'                  the same runs without the brackets

    The runs are joined, not comma-separated: `['Time', ' {{corpus:1c/p6:title:5:33:sha=90d22ddc95fc:shape=S4-0a20202020}}']` is one title the spreadsheet split in two, and the student typed
    "Time {{corpus:1c/p6:title:5:33:sha=90d22ddc95fc}}".

    Only the FIRST double-quoted run is taken, because the scorer's commentary
    quotes things too — p1's title annotation ends "not the default \"Chart
    Title\" placeholder", and joining every run would hand the student a title
    they did not write. A value that does not START with a quote or a bracket is
    returned untouched: the aim is to drop the scorer's commentary, not to
    reformat what the student wrote.

    Measured against the served fixtures of all 26 items before landing: exactly
    the 20 boxes of 1c move, and nothing else in the corpus does. Q6's two
    annotated evidence strings do NOT move, because its boxes come from the
    frozen consensus rather than from this path.
    """
    s = (ev or "").strip()
    if not s:
        return ""
    # A `from_scorer` value inherits whatever template punctuation the scorer was
    # reading, because it quotes the same segmented response: item 3's fifteen
    # boxes opened with the printed question's own `")"`, and Q6/p19's `state_a1`
    # with a `"_"`. `segment.strip_orphan_head` fixes the sections; these strings
    # are stored scorer output and never pass through it, so they are stripped
    # here with the same rule.
    from segment import strip_orphan_head as _head
    m = _RUN_LIST.match(s)
    if m:
        runs = [r[1:-1] for r in _RUN.findall(m.group("inner"))]
        if runs:
            return "".join(runs).strip()
    if _RUN_SQ.match(s):
        runs, rest = [], s
        while True:
            m2 = _RUN_SQ.match(rest)
            if not m2:
                break
            runs.append(m2.group("q"))
            rest = rest[m2.end():]
            m3 = re.match(r"^\s*,\s*(?=')", rest)
            if not m3:
                break
            rest = rest[m3.end():]
        if runs:
            return "".join(runs).strip()
    m4 = _ANNOTATED.match(s)
    if m4:
        return _head(m4.group("q").strip())
    return _head(s)


def counted_members(handout: int, item: str) -> dict[str, tuple[str, list[str]]]:
    """{member component: (count slot, all members)} for this item's counted groups.

    Read from the rubric rather than listed here, so adding a counted group cannot
    silently bypass the guard below.
    """
    from handouts import config
    spec = config(handout)["rubric"].BY_ID.get(item) or {}
    out: dict[str, tuple[str, list[str]]] = {}
    for cr in spec.get("counts", []) or []:
        for m in cr["slots"]:
            out[m] = (cr["key"], list(cr["slots"]))
    return out


def scorer_verdict(handout: int, pid: int, item: str, comp: str) -> str:
    """One component's stored verdict, for reading a counted group's count."""
    path = os.path.join(SCORER_OUT, f"h{handout}", f"participant_{pid:03d}.json")
    if not os.path.exists(path):
        return ""
    with open(path) as fh:
        rec = json.load(fh)
    for it in rec.get("items", []):
        if it.get("item_id") == item:
            for c in it.get("credit_checks", []):
                if re.split(r"\s*\(", c.get("what", ""))[0].strip() == comp:
                    return str(c.get("verdict") or "")
    return ""


PLACEHOLDER_EV = re.compile(r"^\d+ found$")


def _dealt_members(spec: dict) -> dict[str, tuple[str, list[str]]]:
    """{member component: (count slot, ordered members)} from JOBS `dealt`.

    Exactly the shape counted_members() returned, so the dealing code below is
    unchanged; what differs is where it comes from. Members are named by SCORER
    COMPONENT, the same vocabulary `from_scorer` already uses -- that is a stable
    contract with the artifact, not a scoring decision, so depending on it does
    not reintroduce the coupling this removes.

    A group that stops being declared here does not fail quietly: every member
    field falls back to the scorer's placeholder evidence, which
    enforcement.check_fixture_boxes_hold_the_students_words rejects and both
    sweep harnesses refuse to run on.
    """
    out: dict[str, tuple[str, list[str]]] = {}
    for grp in spec.get("dealt") or ():
        members = list(grp.get("members") or ())
        for m in members:
            out[m] = (grp.get("count"), members)
    return out


def distribute_counted(block: str, claimed: list[str], fields: list[str], n: int) -> dict[str, str]:
    """Deal a block across the first `n` of a counted group's member fields.

    A counted group's members are DERIVED: score.py records the count in the
    group's own slot and writes a placeholder as each member's evidence
    ("2 found"), because there is no per-member quote to record. Feeding that
    placeholder into the field put the literal string "2 found" into the
    student's box — 2a fell from 90% to 5% and item 3 from 95% to 10%, on both
    shipped scorers, and the model's own feedback named it ("both are just
    '2 found'"). The paper scorer was unaffected because it reads the .docx.
    stale_check.py could not see it either: the records match the rubric
    exactly, since a placeholder IS correct evidence for a derived member.

    Before the `counts` refactor score.py asked for each member separately and
    did record a span per member, which is what this reconstruction was built
    on; stale predictions masked the change until they were refreshed.

    So the members are filled mechanically instead: strip whatever a
    non-counted field already claimed, then deal the remaining sentences into
    the first `n` boxes as contiguous runs. That reproduces what the count
    grades — how many separate things the student said — without depending on
    an evidence format that varies cell to cell ("(1) ... (2) ...", "HOW #1:
    ...", or free prose, all three of which occur).
    """
    text = " ".join((block or "").split())
    for c in claimed:
        c = " ".join((c or "").split())
        if c and c in text:
            text = text.replace(c, " ", 1)
    text = " ".join(text.split())
    out = {f: "" for f in fields}
    if n <= 0 or not text:
        return out
    sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+", text) if x.strip()]
    if not sents:
        return out
    n = min(n, len(fields))
    per = max(1, len(sents) // n)
    for i in range(n):
        chunk = sents[i * per:] if i == n - 1 else sents[i * per:(i + 1) * per]
        out[fields[i]] = " ".join(chunk).strip()
    return out


def scorer_evidence(handout: int, pid: int, item: str) -> dict[str, str]:
    """The per-component spans score.py already extracted for this cell.

    The item-by-item scorer quotes, for every credit component, the span of the
    student's response that earns it — and it has done that for all 20
    participants of all three handouts, with its agreement against the graders
    measured. That is exactly the decomposition the web version's separate
    fields need, and it was on disk in out/hN the whole time: two regex
    splitters and a hand-read table went into rediscovering it.

    An unmet component sometimes carries a note about what was looked for
    instead of a quote ("Looked for any mention of 4c's other consequence ...").
    Those are dropped — an empty field is the right fixture for something the
    student did not write, and a description of an absence is not their words.

    It also sometimes annotates a real quote: `[[corpus Q6/p9 state_c1 9:62 sha=03879cc80fbe]] — loosely worded, but this is the 4c
    consequence`. The commentary is the scorer's reasoning, not the student's
    words, so only the quoted span is kept. Leaving it in put the CLI's own
    analysis into the student's box on 10 of Q6's 117 filled fields, and the
    leading quote mark also stopped `anchored_split` locating the span at all,
    which sent it down the fallback path that keeps the annotation verbatim.
    """
    path = os.path.join(SCORER_OUT, f"h{handout}", f"participant_{pid:03d}.json")
    if not os.path.exists(path):
        return {}
    with open(path) as fh:
        rec = json.load(fh)
    for it in rec.get("items", []):
        if it.get("item_id") != item:
            continue
        out = {}
        for c in it.get("credit_checks", []):
            name = re.split(r"\s*\(", c.get("what", ""))[0].strip()
            ev = (c.get("evidence") or "").strip()
            # Where the scorer recorded a VERDICT, trust it: only `absent` means
            # the student wrote nothing, so only `absent` earns an empty box. A
            # `mismatch` or `not_described` is their words and belongs in the
            # field — emptying it made the web's `mismatch` verdict unreachable,
            # which is this item's most common deduction. Plain-path items carry
            # no verdict, so they keep the prose heuristic.
            verdict = c.get("verdict")
            if verdict is not None:
                if verdict == "absent":
                    ev = ""
            elif not c.get("met") and re.match(
                    r"(looked for|no |nothing|not |absent|none)", ev, re.I):
                ev = ""
            out[name] = _quoted_span(ev)
        return out
    return {}


# Declared corrections to the frozen consensus spans.
#
# The table is built from per-component evidence quotes the scorer chose
# INDEPENDENTLY, so nothing required the eight spans to be ordered, disjoint or
# complete — see check_consensus_spans_are_disjoint and
# check_fixture_covers_the_response, which now assert the last two.
#
# Only MECHANICAL corrections belong here: a swap where both clauses are
# correctly identified and correctly bounded and merely sit in the wrong boxes.
# A span that is mis-assigned (p10's `state_c2` holds a slice of `change_a1`) or
# a response with no second consequence to assign at all (p18) is a judgement
# about the answer, not a reordering, and must not be patched here.
# Two forms. ("swap", a, b) exchanges two boxes whose spans are both correct and
# merely sit in the wrong places. ("set", field, text) assigns a span outright,
# quoted in full so the correction is auditable against the response.
class _ConsensusFixes:
    """The cell corrections, resolved from the corpus instead of copied from it.

    This was 877 lines of dict literal whose values were 102 student sentences --
    the largest single store of response text in the repo. They are not edits:
    measured, 91 of the 93 that carry text are an exact substring of the RAW
    SECTION the fixture was split from, one more once whitespace is normalised,
    and the last is two spans of one section joined. Every one is a
    RE-SEGMENTATION -- a person read the submission, saw the split had put the
    wrong clause in the wrong box, and typed the right clause out by hand.

    So `CONSENSUS_SPANS.json` names the spans and the text is read from
    `$COURSE_DATA` at build time. The same bytes reach the scorer; none of them
    live here. `fixture_edits.py --verify` re-resolves every span, and each one
    carries the sha of the text it was written against, so a corpus that moves
    under a span is a refusal rather than a silent re-scoring.

    LAZY, PER CELL. Resolving everything at import would make every consumer of
    this module require the corpus, including the ones that only want JOBS.

    A DECLARED CELL THAT CANNOT BE RESOLVED IS FATAL, not empty. Returning `[]`
    would build the fixture WITHOUT its correction -- a cell that scores, and
    scores the mis-segmented text, with nothing in the output saying so. That is
    the failure mode this file exists to prevent, so it raises instead.
    """

    def __init__(self, path):
        self._path = path
        self._raw = None
        self._cache: dict = {}

    def _spans(self) -> dict:
        if self._raw is None:
            import json
            with open(self._path) as fh:
                self._raw = json.load(fh)
        return self._raw

    def _resolve(self, key):
        item, pid = key
        entries = self._spans().get(f"{item}/p{pid}")
        if entries is None:
            return None
        import fixture_edits as FE
        sections = FE._sections(item, pid)
        out = []
        for e in entries:
            text, status = FE.resolve(e, item, pid, sections)
            if status != "ok":
                raise SystemExit(
                    f"CONSENSUS_SPANS[{item}/p{pid}] {e[1]}: {status}\n"
                    f"The correction cannot be resolved, so the fixture would be "
                    f"built from the very text this span was written to replace. "
                    f"Read the cell; do not re-derive the span from a guess.")
            out.append(("set", e[1], text))
        return out

    def get(self, key, default=None):
        if key not in self._cache:
            got = self._resolve(key)
            if got is None:
                return default
            self._cache[key] = got
        return self._cache[key]

    def __getitem__(self, key):
        got = self.get(key)
        if got is None:
            raise KeyError(key)
        return got

    def __contains__(self, key):
        return f"{key[0]}/p{key[1]}" in self._spans()

    def __iter__(self):
        for cell in self._spans():
            item, pid = cell.split("/p")
            yield (item, int(pid))

    def __len__(self):
        return len(self._spans())

    def keys(self):
        return list(self)

    def items(self):
        for key in self:
            yield key, self[key]

    def values(self):
        for key in self:
            yield self[key]


CONSENSUS_FIXES = _ConsensusFixes(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                  "CONSENSUS_SPANS.json"))


def _unclaimed_tail(raw: str, boxes: list[str]) -> str:
    """The end of the response that no box claims, or "" if nothing is missing.

    Located by the LAST box text that can be found in the response: everything
    after it belongs to the student and to no field. Deliberately conservative —
    a gap in the middle is left alone, because splitting it would be guessing,
    while a tail is unambiguous.
    """
    text = raw or ""
    if not text.strip():
        return ""
    low = text.lower()
    end = 0
    for b in boxes:
        b = " ".join((b or "").split())
        if len(b) < 12:
            continue
        at = low.find(b[:40].lower())
        if at >= 0:
            end = max(end, at + len(b))
    rest = text[end:].strip() if end else ""
    return rest if len(rest.split()) >= 8 else ""


# Tolerant of how these students actually spell the aspects. "Measureable" is
# not a typo worth ignoring: p13 and p20 both label the aspect that way, and a
# strict pattern left their `measurable` box empty while the sentence sat in a
# neighbour's slice — the same silent loss this fallback exists to end.
_ASPECT_WORDS = {
    "specific": r"specific",
    "measurable": r"measur\w*able",
    "action": r"action[\s-]?oriented|action",
    "realistic": r"realistic|attainable",
    "timebound": r"time[\s-]?bound|timebound",
}


def _keyword_anchor(text: str, field: str) -> int | None:
    """Where the aspect `field` names is introduced, or None.

    Used only when the scorer produced no evidence span at all. Anchors on the
    START of the sentence carrying the aspect's own word, so the box takes a
    whole clause; a bare keyword offset would cut mid-sentence, which is the
    defect check_fixture_follows_response_structure exists to catch.
    """
    import re
    pat = _ASPECT_WORDS.get(field.rsplit("_", 1)[-1])
    if not pat:
        return None
    m = re.search(r"\b(?:" + pat + r")\b", text, re.I)
    if not m:
        return None
    starts = [0] + [x.end() for x in re.finditer(r"[.!?]\s+|\n+", text)]
    return max((s for s in starts if s <= m.start()), default=0)


def anchored_split(raw: str, spans: list[tuple[str, str]]) -> dict[str, str]:
    """Partition a block using the scorer's evidence quotes as ANCHORS.

    `credit_checks[].evidence` is a justification, not a segmentation. Where a
    component maps to a discrete answer — one of Q6's eight slots, one of Q4a's
    two antecedents — the quote is the whole answer and can be used directly.
    Where it maps to a stretch of discursive prose, the quote is only the
    sentence that earned the point, and using it as the field value throws the
    rest away: Q3 lost over 20% of the student's words on 7 of 20 cells, up to
    41%, and its three discursive aspects carry every disagreement with the CLI
    scorer while its one crisp aspect carries none.

    So locate each quote in the original and slice from one anchor to the next.
    The boundaries come from the scorer's own extraction rather than a pattern
    guessing where an aspect begins, which is what made the earlier splitters
    unreliable, and nothing the student wrote is dropped.
    """
    text = raw or ""
    low = text.lower()
    hits = []
    for field, quote in spans:
        q = " ".join((quote or "").split())
        if not q:
            # NO QUOTE AT ALL. scorer_evidence drops evidence that is a note
            # about an absence rather than a span, so this field is empty
            # whenever the paper scorer declined to quote that aspect — and the
            # web and CLI are then handed an empty box and correctly report what
            # they were given. That is circular: their input is built from the
            # paper scorer's output, so its failures arrive as their missing
            # evidence.
            #
            # These responses label themselves. Q3's students write "My goal is
            # Specific because ...", "Measurable: ...", one sentence per aspect,
            # so the aspect's own name is a better anchor than a neighbour's
            # slice. Fall back to it, and to the START of the sentence carrying
            # it, so the box gets a whole clause rather than a mid-sentence cut.
            at = _keyword_anchor(text, field)
            hits.append((at, field, None) if at is not None else (None, field, ""))
            continue
        at = low.find(q[:40].lower())
        if at < 0:                      # quote reworded or absent: fall back to it
            hits.append((None, field, q))
        else:
            hits.append((at, field, None))
    # Every anchor snaps back to the START of the sentence carrying it. A quote
    # located mid-sentence otherwise cuts the PRECEDING slice mid-clause: p6's
    # `realistic` was found at [[corpus Q3/p6 realistic 10:36 sha=7158f61cd68d]], so `action` ran
    # up to it and ended "... then exercise. - Adding on,". Snapping moves the
    # boundary to the sentence break, which gives each box whole clauses on both
    # sides and drops nothing.
    import re as _re
    _starts = [0] + [m.end() for m in _re.finditer(r"[.!?]\s+|\n+", text)]
    hits = [((max((st for st in _starts if st <= at), default=0)
              if at is not None else None), f, q) for at, f, q in hits]
    located = sorted([h for h in hits if h[0] is not None])
    out = {field: "" for field, _ in spans}
    for i, (start, field, _) in enumerate(located):
        # The FIRST slice begins at 0, not at its own anchor. The loop used to
        # run anchor-to-anchor, so nothing ever covered the text BEFORE the first
        # located quote — and the docstring's claim that "nothing the student
        # wrote is dropped" was false whenever the scorer gave no quote for the
        # aspect the student happened to write first. On Q3/p3 that discarded the
        # opening 110 characters, the whole "{{corpus:Q3/p1:specific:10:37:sha=32a1b1a0f56c:shape=C800}} ..."
        # sentence, and the same prefix loss runs through nine of Q3's twenty
        # cells. The two defects compound: a missing `specific` quote moves the
        # first anchor to `measurable`, which puts the specific text in the
        # dropped prefix.
        begin = 0 if i == 0 else start
        end = located[i + 1][0] if i + 1 < len(located) else len(text)
        out[field] = text[begin:end].strip()
    for start, field, q in hits:        # unlocated quotes keep the quote itself
        if start is None:
            out[field] = q
    return out


def gold_labels_1c(feedback: str) -> dict[str, bool]:
    """The grader's verdict on all five of 1c's slots, from their comment.

    Includes the graph gate, and no longer returns None for a row that zeroed on
    it. The previous version dropped all five zero rows on the grounds that they
    "state no labelling verdicts" — but its own reasoning said the web can reach
    zero "where the data is absent", and p15 and p18 are exactly that: their 1b
    data is incomplete, the `has_own_graph` gate fires on it, and both systems
    score them 0.00 against a gold of 0.00. Excluding them threw away two cells
    the comparison can use, and left 1c measured over 15 cells on this side
    against 17 on the CLI's.

    The three rows that genuinely cannot fail here — data complete, no figure on
    paper — are p4, p19 and p20, and they are dropped upstream by
    PER_ITEM_EXCLUDE["1c"], which never puts them in the work list at all. This
    function no longer needs to know about them.

    Mirrors gold_slots_1c in agreement.py. The two must agree: a row scored on
    one side and dropped on the other is not a comparison.
    """
    f = (feedback or "").lower()
    no_graph = "did not include" in f or "did not provide a graph" in f
    return {
        "has_own_graph": not no_graph,
        "title": not no_graph and "missing graph title" not in f,
        "x": not no_graph and "missing x-axis" not in f,
        # The dictionary text is "missing the legend"; the graders wrote
        # "missing legend". Match either.
        "y": not no_graph and "missing y-axis" not in f,
        "legend": not no_graph and re.search(r"missing (the )?legend", f) is None,
    }


def rebuild_gold_1c(gold: dict) -> tuple[dict, list[int]]:
    """Restate gold's 1c from its labelling verdicts, on the same 10 points.

    The paper item is 10: having a graph, a title, two axis labels and a legend,
    2 each. The web sheet now carries all five, so the totals agree and this no
    longer rescales anything — a row that states labelling verdicts is scored
    10 minus 2 per element the grader faulted.

    It still exists because p11's gold carries an improvised "-1 pt: missing
    baseline data week" that no slot on either side scores; rebuilding from the
    verdicts drops it cleanly, where subtracting from the raw score would not.
    (p11's row does not self-reconcile anyway: it itemises -2/-2/-1 against a
    score of 7.0.) It no longer drops anything — a gate failure is a score of
    zero, not an absent gold — and the rows that cannot fail on the web are held
    out upstream by PER_ITEM_EXCLUDE["1c"].
    """
    # Nulled as well as held out of the work list, matching agreement.py: the
    # work-list drop stops the call, and nulling the gold stops the row counting
    # if that drop is bypassed — which `--exclude` with explicit values does.
    # Read off PER_ITEM_EXCLUDE so the two drops cannot disagree.
    unreachable = set(PER_ITEM_EXCLUDE.get("1c", {}))
    dropped: list[int] = []
    for pid, items in gold.items():
        cell = items.get("1c")
        if not cell:
            continue
        if pid in unreachable:
            items["1c"] = {"score": None, "feedback": cell.get("feedback", "")}
            dropped.append(pid)
            continue
        labels = gold_labels_1c(cell.get("feedback"))
        # The gate takes the whole item, exactly as scoreSlotSheet computes it.
        score = 0.0 if not labels["has_own_graph"] else \
            10.0 - 2.0 * sum(1 for ok in labels.values() if not ok)
        items["1c"] = {"score": score, "feedback": cell.get("feedback", "")}
    return gold, sorted(dropped)


def sections_for(handout: int, pid: int) -> dict[str, str]:
    """The paper sections, repaired the same way score.py repairs them.

    `repair_orphans` moves a block the segmenter filed under the wrong heading to
    the item it belongs to. score.py has always applied it; this did not, so the two
    systems read DIFFERENT INPUT wherever it fires — which makes the comparison for
    that cell meaningless rather than merely wrong. H2 p19 is the only case in the
    corpus: its DAY2 answer was filed under D2, so the web scored DAY2 with an empty
    box (correctly reporting nothing, and gating to 0 against a gold of 4) while the
    CLI read the 82 characters the student wrote.
    """
    cfg = config(handout)
    path = dict(find_submissions(handout, [pid]))[pid]
    sec = segment(path, cfg["template"], cfg["markers"], cfg["capture_tail"],
                  cfg.get("join_aware", False))
    if cfg.get("repair_orphans"):
        sec, _ = repair_orphans(sec, [i["id"] for i in cfg["rubric"].ITEMS])
    return sec


_MODIFY = re.compile(r"^\s*modify\s*[:.]", re.I | re.M)


def split_labelled(text: str, labels: list[tuple[str, str]]) -> dict[str, str]:
    """Cut one block into its labelled parts, LINE BY LINE.

    Students write these two ways, and both are common. Some label explicitly
    ("Specific: my goal is..."); others put one aspect per line as prose ("{{corpus:Q3/p1:specific:10:29:sha=ce92eedf2d96:shape=S0-0a20202020}} because..."). An earlier version required a colon after the
    aspect word and so found nothing in the prose form — which left four of five
    fields empty for 12 of 20 participants, while a greedy pattern quietly
    assigned one aspect's line to the previous field.

    So: walk the lines, and whichever aspect word a line mentions first claims
    that line. Lines before any aspect word attach to nothing; lines after one
    attach to it, which keeps a wrapped answer with its own aspect.
    """
    out: dict[str, str] = {field: [] for field, _ in labels}
    current: str | None = None
    for raw in (text or "").split("\n"):
        line = raw.strip()
        if not line:
            continue
        hit, at = None, len(line) + 1
        for field, pattern in labels:
            m = re.search(pattern, line, re.I)
            if m and m.start() < at:
                hit, at = field, m.start()
        if hit:
            current = hit
            # keep the whole line: "{{corpus:Q3/p1:specific:10:37:sha=32a1b1a0f56c}} X" is the answer,
            # not just the tail after the word
            out[current].append(line)
        elif current:
            out[current].append(line)
    return {k: " ".join(v).strip() for k, v in out.items()}


def split_modify(text: str) -> tuple[str, str, str]:
    """Separate Q4b's two behaviours from its "is this a good choice" statement.

    Most students label it ("Modify: ..."), and where they do the boundary is
    theirs. Eight of twenty do not, and returning the whole block as the
    behaviours then feeds their good-choice statement in as a second behaviour —
    which the model correctly rejects, costing a slot for a fixture error. They
    did write the statement; it is simply unlabelled and last.

    So without a label, take the trailing sentence when it reads like the
    statement — it argues about whether the behaviour is worth changing, rather
    than describing what they do instead. Position alone is not enough, because a
    student who never wrote one at all must still come back empty.
    """
    t = (text or "").strip()
    m = _MODIFY.search(t)
    if m:
        return t[:m.start()].strip(), t[m.end():].strip(" :\n\t"), "labelled"

    # The statement argues about the choice; a behaviour describes an activity.
    cues = ("good choice", "good behavior", "good behaviour", "great behavior",
            "great behaviour", "worth modif", "to modify", "modify because",
            "change because", "good to change", "good one to",
            # the other way students argue it: that the behaviour is theirs to
            # change, which is the criterion the item actually asks about
            "under my control", "in my control", "i can choose", "i can control",
            "is an issue for me", "genuinely an issue")
    pieces = [x.strip() for x in re.split(r"(?<=[.!?])\s+|\n", t) if x.strip()]
    if len(pieces) >= 2:
        low = pieces[-1].lower()
        if any(c in low for c in cues):
            # a mid-line "Modify:" that the line-anchored pattern missed, and
            # any list bullet the transcription left in front of it
            tail = re.sub(r"^[\s\-o•*]*modify\s*[:.]\s*", "", pieces[-1], flags=re.I)
            return " ".join(pieces[:-1]).strip(), tail.strip(" -o•*\t"), "recovered"
    return t, "", "none"


def split_n(text: str, n: int) -> list[str]:
    """Cut a block into n parts on the student's own line breaks, else sentences.

    Returns fewer non-empty parts than asked for when the student wrote fewer —
    an empty box is a real state the graders score, so it is never padded.
    """
    t = (text or "").strip()
    if not t:
        return [""] * n
    parts = [x.strip() for x in t.split("\n") if x.strip()]
    if len(parts) < 2:
        parts = [x.strip() for x in re.split(r"(?<=[.!?])\s+", t) if x.strip()]
    if len(parts) <= n:
        return parts + [""] * (n - len(parts))
    # more pieces than boxes: distribute, keeping order
    per = (len(parts) + n - 1) // n
    return [" ".join(parts[i * per:(i + 1) * per]) for i in range(n)]


def fallback_from(spec: dict, pid: int, section: str) -> str:
    """A section this handout left empty, taken from another handout's submission.

    Handout 2 asks students to restate their behaviour and goal at the top, and
    7 of 20 transcriptions have those lines empty. Their answers are not lost —
    they are in Handout 1 — and without them the model is asked to judge a
    contingency against a goal it cannot see. Every such cell failed for that
    reason and not because anything was wrong with the prompt.
    """
    src = spec.get("fallback", {}).get(section)
    if not src:
        return ""
    handout, other = src
    found = dict(find_submissions(handout, [pid]))
    if pid not in found:
        return ""
    cfg = config(handout)
    sec = segment(found[pid], cfg["template"], cfg["markers"], cfg["capture_tail"],
                  cfg.get("join_aware", False))
    return (sec.get(other) or "").strip()


# Where each context component's text comes from in the paper corpus.
#   ("section", name)          the paper answer, whole
#   ("scorer", item, comp)     one component the scorer already separated
# Keyed by web component id, so it is stated once however many prompts use it.
# The OLX `fallback=` attributes, mirrored. A `<SheetValue>` resolves from a
# graded sheet and falls back to a plain component until that sheet exists, so in
# the app these are never blank. The harness drives one item directly and grades
# no other, so the sheet never exists and the SheetValue resolved to nothing --
# `bmod_h1_utb_observed` was EMPTY on all 20 H1 cells, which made every item that
# echoes it print a labelled context line with no value after it. That is a
# harness artifact, not a prompt defect: production shows the student's own words
# there. Seeding the fallback here makes a run see what production sees.
CONTEXT_FALLBACK = {
    # <SheetValue id="bmod_h1_utb_observed" ... fallback="bmod_h1_utb" />
    "bmod_h1_utb_observed": "bmod_h1_utb",
}
def context_targets(item: str) -> list[str]:
    """The components this item's prompt reads as cross-item context."""
    import olx_prompts
    h = olx_prompts.HANDOUT[item]
    rub = config(h)["rubric"].BY_ID[item]
    out = []
    for key in rub["context"]:
        for _, target in olx_prompts.CONTEXT.get(key, ()):
            out.append(target)
    return out


def context_value(handout: int, pid: int, sec: dict, target: str) -> str:
    src = CONTEXT_SOURCE.get(target)
    if src is None:
        return ""
    if src[0] == "section":
        return (sec.get(src[1]) or "").strip()
    _, other, comp = src
    # A counted member's evidence is a placeholder, not the student's words, so it
    # must not be seeded here either — that is how "2 found" reached items 3 and
    # 2b, which read 2a's boxes as read-only context. Empty is also wrong (an
    # unseeded ref reads as an EMPTY answer), so fall back to the whole source
    # section: context needs the student's words, not per-box fidelity.
    if comp in counted_members(handout, other):
        return (sec.get(other) or "").strip()
    return scorer_evidence(handout, pid, other).get(comp, "").strip()


# The four options of H2's type ChoiceInput, exactly as authored.
TYPE_CHOICES = ["Positive Reinforcement", "Negative Reinforcement",
                "Positive Punishment", "Negative Punishment"]


def detect_type(text: str) -> str:
    """Which of the four types this student wrote, as the option's own value.

    The paper form is a stem the student completes — "I plan to use: positive
    reinforcement" — so the stem itself names no type and cannot produce a false
    positive. An unfinished stem is an unanswered item, which is exactly the three
    zeros in gold (p10, p15, p18 on both T1 and T2). Transcriptions carry the
    underline as a stray leading underscore and vary in case; neither changes
    which type was named.
    """
    # Not \b: the underline survives transcription as a stray leading underscore
    # ("_Positive Reinforcement"), and `_` is a word character, so \b would find
    # no boundary and read p20 as unanswered.
    m = re.search(r"(?<![A-Za-z])(positive|negative)\s+(reinforcement|punishment)"
                  r"(?![A-Za-z])", text or "", re.I)
    if not m:
        return ""
    return f"{m.group(1).capitalize()} {m.group(2).capitalize()}"


def _era_for(items) -> dict:
    """The era stamp, or why it could not be taken. Never fails a sweep."""
    try:
        import measured
        return measured.era_stamp(items)
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}


def build_jobs(item: str, pids: list[int]) -> list[dict]:
    spec = JOBS[item]
    jobs = []
    for pid in pids:
        sec = sections_for(spec["handout"], pid)
        path = dict(find_submissions(spec["handout"], [pid]))[pid]
        fixture, fell_back = {}, []
        for field, section in spec.get("fields", {}).items():
            if section == "_utb_choice":
                fixture[field] = detect_utb(path, sec.get("Q1", ""))
                continue
            if section.startswith("_type_choice:"):
                fixture[field] = detect_type(sec.get(section.split(":", 1)[1], ""))
                continue
            value = (sec.get(section) or "").strip()
            if not value:
                value = fallback_from(spec, pid, section)
                if value:
                    fell_back.append(section)
            fixture[field] = value
        how = {}
        for section, labels in spec.get("labelled", {}).items():
            parts = split_labelled(sec.get(section, ""), labels)
            fixture.update(parts)
            how[section] = "labelled" if any(parts.values()) else "empty"
        for section, (f1, f2, fmod) in spec.get("modify", {}).items():
            head, mod, prov = split_modify(sec.get(section, ""))
            a, b, method = split_two(head)
            fixture[f1], fixture[f2], fixture[fmod] = a, b, mod
            how[section] = f"{method}, modify {prov}"
        for section, (n, fields) in spec.get("splitn", {}).items():
            for field, part in zip(fields, split_n(sec.get(section, ""), n)):
                fixture[field] = part
            how[section] = f"{n}-way"
        # A hand-read fixture beats any rule. Q4b asks for three things and most
        # students wrote them as continuous prose; three heuristic passes each
        # traded one error for another, so its 20 cells were read by hand once.
        # Recorded as data next to the code, so what was measured is inspectable.
        # Components the scorer already separated, one per field. A tuple joins
        # several into one field, for the rare box that holds more than one
        # judgement.
        fs = spec.get("from_scorer")
        if fs and spec.get("anchored"):
            ev = scorer_evidence(spec["handout"], pid, item)
            raw_block = (sec.get(item) or "")
            parts = anchored_split(raw_block, [(f, ev.get(c, "")) for f, c in fs.items()])
            fixture.update(parts)
            how["_anchored"] = item
        elif fs:
            ev = scorer_evidence(spec["handout"], pid, item)
            # A counted group's member evidence is a placeholder, never a span —
            # see distribute_counted(). Those fields are dealt from the block.
            #
            # WHICH FIELDS ARE DEALT IS DECLARED IN `dealt`, NOT READ OFF THE
            # RUBRIC. It used to come from counted_members(), i.e. from the live
            # scoring structure, and that made the INPUT depend on a scoring
            # decision: dropping an item's `counts` group silently sent every
            # member field down the plain path, where `ev.get(comp)` is the
            # placeholder, so the student's answer became the literal string
            # "2 found". Q2's structural attempt did exactly that and a 120-call
            # sweep measured a placeholder. A fixture reconstructs what the
            # student wrote; it must not move when a scoring rule is edited.
            cm = _dealt_members(spec)
            plain = {f: c for f, c in fs.items()
                     if isinstance(c, tuple) or c not in cm}
            for field, comp in plain.items():
                if isinstance(comp, tuple):
                    fixture[field] = " ".join(
                        x for x in (ev.get(c, "").strip() for c in comp) if x)
                else:
                    fixture[field] = ev.get(comp, "").strip()
            grouped: dict[str, list[tuple[str, str]]] = {}
            for field, comp in fs.items():
                if not isinstance(comp, tuple) and comp in cm:
                    grouped.setdefault(cm[comp][0], []).append((field, comp))
            for count_key, pairs in grouped.items():
                order = cm[pairs[0][1]][1]
                pairs.sort(key=lambda fc: order.index(fc[1]))
                raw_n = scorer_verdict(spec["handout"], pid, item, count_key)
                try:
                    n = int(raw_n)
                except ValueError:
                    n = 0
                member_fields = [f for f, _ in pairs]
                # score.py stores the model's quoted span per member now, so the
                # ordinary evidence lookup is right whenever it produced one. It
                # still writes "N found" where the model quoted nothing (item 3's
                # evidence is free prose in every cell), and that must never
                # reach a field — hence the placeholder test and the fallback.
                vals = [ev.get(c, "").strip() for _, c in pairs]
                usable = [v for v in vals if v and not PLACEHOLDER_EV.match(v)]
                if len(usable) == len(vals) and vals:
                    for f, v in zip(member_fields, vals):
                        fixture[f] = v
                    how[f"_counted:{count_key}"] = f"{n}-way from scorer spans"
                else:
                    fixture.update(distribute_counted(
                        sec.get(item) or "",
                        [fixture[f] for f in plain],
                        member_fields, n))
                    how[f"_counted:{count_key}"] = f"{n}-way dealt"
            how["_from_scorer"] = item
        # Cross-item context. Every prompt is passed the neighbouring answers its
        # rubric record names in `context`, so those components have to be seeded
        # too — an unseeded ref is not "no context", it is an EMPTY answer, and
        # the model reads it as one. Q6 is the cautionary case: its prompt says
        # to check each stated antecedent against 4a before crediting the slot,
        # so with 4a blank every state slot came back `mismatch` and the item
        # measured 24%. Derived from olx_prompts.CONTEXT rather than listed per
        # item, so adding a context ref to a prompt cannot silently go unfed.
        for target in context_targets(item):
            if (fixture.get(target) or "").strip():
                continue                       # already seeded by `fields` etc.
            val = context_value(spec["handout"], pid, sec, target)
            if not val:
                # Mirror the OLX fallback rather than leaving the ref unfed: an
                # unseeded ref reads to the model as an EMPTY answer, which is the
                # same failure the loop above exists to prevent.
                val = (fixture.get(CONTEXT_FALLBACK.get(target, "")) or "").strip()
            fixture[target] = val
        # A frozen consensus table overrides the single-run spans it was built
        # from. Keyed by rubric component, so it is mapped back through
        # `from_scorer` rather than duplicating the field names.
        cons = spec.get("consensus")
        if cons:
            path_c = os.path.join(os.path.dirname(os.path.abspath(__file__)), cons)
            with open(path_c) as fh:
                table = json.load(fh)
            row = table["participants"].get(str(pid))
            if row is None:
                raise SystemExit(f"{cons} has no entry for p{pid}; "
                                 f"run q6_consensus.py --build")
            for field, comp in spec["from_scorer"].items():
                if comp in row["fields"]:
                    fixture[field] = row["fields"][comp]
            n_runs = table["n_runs"].get(str(pid)) or 0
            how["_consensus"] = f"{n_runs} runs"

            # NO STUDENT TEXT MAY BE DROPPED.
            #
            # The spans come from `credit_checks[].evidence`, and an unmet
            # component carries a note instead of a quote, which scorer_evidence
            # discards on the reasoning that "an empty field is the right fixture
            # for something the student did not write". That reasoning fails
            # whenever the scorer was WRONG about the absence. p5's Q6 ends with
            # a complete second consequence — [[corpus Q6/p5 state_c2 55:141 sha=ae4cfd7ffee1]] — and the scorer called
            # both c2 slots `absent` in all ten runs, so the consensus froze two
            # empty boxes and about 200 characters never reached ANY scorer. The
            # graders read the whole answer and charged "does not MATCH".
            #
            # That is a circular dependency: the input the web and CLI see is
            # built from the paper scorer's output, so its mistakes arrive as
            # their missing evidence, and a three-way comparison is partly
            # measuring one scorer against its own prior failures.
            #
            # So any TAIL of the response that no box claims is handed to the
            # first empty box after the last one that was filled. Only the tail,
            # and only into an empty box: this recovers what was dropped without
            # re-segmenting anything the consensus did assign.
            tail = _unclaimed_tail(sec.get(item) or "",
                                   [fixture.get(f, "") for f in spec["from_scorer"]])
            if tail:
                for field in spec["from_scorer"]:
                    if not (fixture.get(field) or "").strip():
                        fixture[field] = tail
                        how["_tail_recovered"] = f"{len(tail.split())} words -> {field}"
                        break

            # A vote can be reproducible and still be arbitrary. Freezing the
            # table made every fixture byte-identical run to run, which is what
            # the churn described in q6_consensus.py needed — but it does not
            # make a 5/5 split MEAN anything, it just means the same coin lands
            # the same way every time. Audited over the current table, 158 of 160
            # slots agree on at least 80% of runs; the two that do not are p9's
            # state_c2 and affect_c2, tied 5/5, and p9 is declared in
            # PER_ITEM_EXCLUDE. So the invariant holds today by virtue of a good
            # build, and nothing was checking it. A rebuild with fewer runs, or a
            # new participant whose answer splits the vote, would be measured as
            # solid and silently decide points before the model reads anything —
            # p9's tie-break fixes 2 of 8 slots, 2.5 of 10 marks.
            #
            # So: a weak cell must be DECLARED, exactly as an unreachable
            # deduction code must be. Warn rather than raise, because the right
            # response is a judgement (exclude it, or hand-split it as Q4b is),
            # and a hard failure here would block a run over a cell that may
            # already be excluded downstream.
            weak = []
            for comp, det in (row.get("detail") or {}).items():
                votes = (det or {}).get("verdicts") or {}
                if not votes or not n_runs:
                    continue
                share = max(votes.values()) / n_runs
                if share < CONSENSUS_MIN_SHARE:
                    weak.append((comp, dict(votes), round(share, 2)))
            # A slot that CONSENSUS_FIXES sets by hand is no longer decided by
            # the vote, so a tie on it is moot — "hand-split it" is one of the
            # three remedies this warning names. p9's state_c2 and affect_c2 are
            # the tied pair, and both are hand-set to empty, so the tie-break
            # fixes nothing. Before this, the warning was satisfied only by
            # PER_ITEM_EXCLUDE, and it fired the moment p9's exclusion was
            # replaced by a gold correction — while the slots it names had been
            # hand-split all along.
            declared = {f[1] for f in CONSENSUS_FIXES.get((item, pid), [])
                        if f[0] == "set"}
            weak = [w for w in weak if w[0] not in declared]
            if weak and pid not in PER_ITEM_EXCLUDE.get(item, {}):
                print(f"*** p{pid}/{item}: consensus fixture is WEAK on "
                      f"{len(weak)} slot(s) and this cell is not declared in "
                      f"PER_ITEM_EXCLUDE — the split, and the points that follow "
                      f"from it, are close to arbitrary:", file=sys.stderr)
                for comp, votes, share in weak:
                    print(f"      {comp}: {votes} (top share {share:.2f} < "
                          f"{CONSENSUS_MIN_SHARE})", file=sys.stderr)
                print(f"    Exclude it, hand-split it, or rebuild with more runs.",
                      file=sys.stderr)

        hs = spec.get("handsplit")
        if hs:
            path_hs = os.path.join(os.path.dirname(os.path.abspath(__file__)), hs)
            with open(path_hs) as fh:
                table = json.load(fh)
            row = table.get(str(pid))
            if row is None:
                raise SystemExit(f"{hs} has no entry for p{pid}")
            fixture.update(row)
            how["_handsplit"] = os.path.basename(hs)

        if spec.get("sim"):
            simrec = simulate_h3.load_all().get(pid)
            if simrec is None:
                raise SystemExit(f"no Handout 3 reconstruction for p{pid}; "
                                 f"run simulate_h3.py first")
            prov = simrec.get("provenance") or {}
            for field, key in spec["sim"].items():
                fixture[field] = (simrec["fields"].get(key) or "").strip()
            how["_reconstructed"] = simrec["graph_source"]
            # WHERE each seeded value came from, not just whether one exists.
            # `spread_total` turns a weekly total into seven daily values that sum
            # to it — arithmetic, not evidence — and the result is indistinguishable
            # from a student who logged seven numbers unless the provenance is read.
            # Uniform-looking reconstructed data is exactly what invites a
            # conclusion about the students that is really a conclusion about the
            # reconstruction, so the sources are reported with the rates.
            for field, key in spec["sim"].items():
                src = prov.get(key)
                if src:
                    how[f"_prov:{field}"] = src
        # DECLARED SPAN CORRECTIONS, applied once, after every branch has filled
        # the fixture. They used to live inside the `consensus` and `handsplit`
        # branches, which left `from_scorer` items — 2a among them — unreachable:
        # the only way to repair one was to edit data outside the repo, which is
        # how an earlier p7 fix ended up invisible to anyone who clones this.
        fixes = CONSENSUS_FIXES.get((item, pid), [])
        if fixes:
            key = f"_{item.lower()}_"

            def _field_of(box):
                # The item's OWN fields first. A fixture carries context fields
                # too, and Q4b's includes 4a's `bmod_h1_q4a_first` — matching on
                # the trailing word alone resolved `first` to the NEIGHBOUR's box
                # and silently left Q4b/p7's own `first` empty. Only fall back to
                # the trailing word when nothing carries the item's key.
                for k in fixture:
                    if key in k and k.split(key)[-1] == box:
                        return k
                for k in fixture:
                    if key not in k and k.rsplit("_", 1)[-1] == box:
                        return k
                raise SystemExit(f"CONSENSUS_FIXES[{(item, pid)}] names box "
                                 f"`{box}`, which this fixture has no field for")

            # One fix per box: the entries apply in order, so a second naming the
            # same box silently overwrites the first. p9's corrections were
            # clobbered by its own earlier trims exactly this way.
            touched: dict[str, str] = {}
            for fix in fixes:
                for box in (fix[1:] if fix[0] == "swap" else fix[1:2]):
                    if box in touched:
                        raise SystemExit(
                            f"CONSENSUS_FIXES[{(item, pid)}] has two fixes for "
                            f"`{box}` ({touched[box]} then {fix[0]}). The later "
                            f"one silently wins; state a single span per box.")
                    touched[box] = fix[0]
            for fix in fixes:
                if fix[0] == "set":
                    fixture[_field_of(fix[1])] = fix[2]
                else:
                    fa, fb = _field_of(fix[1]), _field_of(fix[2])
                    fixture[fa], fixture[fb] = fixture.get(fb, ""), fixture.get(fa, "")
                how["_span_fix"] = how.get("_span_fix", "") + f" {fix[1]}"

        for section, (f1, f2) in spec.get("split", {}).items():
            a, b, method = split_two(sec.get(section, ""))
            fixture[f1], fixture[f2] = a, b
            how[section] = method
        jobs.append({
            "cell": f"p{pid}/{item}",
            "screen": spec["screen"], "ns": spec["ns"],
            **({"button": spec["button"]} if spec.get("button") else {}),
            "feedback": spec["feedback"], "grader": spec["grader"],
            "fixture": fixture, "split_how": how, "fell_back": fell_back,
        })
    return jobs


def _idmap_extra_lines(idmap: str, item_id: str, want: str) -> list[str]:
    """Lines the DUMP's prompt has that the rubric no longer generates.

    The freshness check began as a one-directional test — is every line of the
    generated prompt present in the dump — which catches a dump taken BEFORE a
    change. It cannot catch a dump taken DURING one. A dump is a superset then,
    every generated line is still in it, and it passes while serving rule text
    that has since been reverted.

    That is not hypothetical: after five experimental Q6 wordings were built,
    measured and reverted, two saved dumps still carried them and both were
    reported as matching HEAD. The mirror image of the failure this check was
    written for, and it survived because the original only looked one way.

    Needs the prompt body out of the dump rather than a substring test over the
    whole file, since the file legitimately holds every other item's text too.
    The body sits at idMap["<ns>/<action>"]["<locale>"]["kids"][0].
    """
    import json
    import re as _re

    import paths

    try:
        with open(idmap) as fh:
            m = json.load(fh).get("idMap") or {}
    except Exception:
        return []
    action = (JOBS.get(item_id) or {}).get("grader", "").replace("_grader", "_llm")
    # EVERY string kid, not `kids[0]`. The body is SPLIT around each <Ref>: Q1
    # has 3 string segments, Q4b 9 and Q6 SIXTEEN, so reading the first one
    # inspected a fraction of the prompt and silently ignored the rest. That is
    # the half where the box wrapper and the closing instructions live -- the
    # text nearest the student's own answer -- and a change to any of it passed
    # this guard. Found 2026-09-01 when a hand comparison using the same kids[0]
    # shortcut reported four lines missing from the app that were present in the
    # OLX all along.
    body = None
    for key, entry in m.items():
        if not key.endswith("/" + action):
            continue
        for _loc, val in (entry or {}).items():
            kids = (val or {}).get("kids") or []
            joined = "".join(k for k in kids if isinstance(k, str))
            if joined:
                body = joined
        break
    if not body:
        return []                       # cannot locate it; stay silent rather than block

    # SENTENCES, not lines, and with no upper length bound. A line-based test with
    # a 130-character ceiling missed the very text this is for: a slot note is
    # rendered as one long bullet, so the rule wordings all sat above the ceiling
    # and passed. Ref markup is stripped from both sides, since the server resolves
    # it into the student's own text and the generated copy still carries the tag.
    # NUL IS PART OF THE MARKUP. olx_prompts renders a Ref as
    # "\x00REF:<id>:<target>\x00" (olx_prompts._REF), and stripping only the
    # REF: body left the two sentinels behind -- `\s` does not match NUL, so the
    # generated side flattened to "[box begins] \x00 \x00 [box ends]" while the
    # served side has "[box begins] [box ends]". No substring test could ever
    # match, so EVERY handout-3 item read as a superset dump and refused to
    # sweep: 1a, 2a, 2b and 3 alike. Only items whose Ref sits inside a 60-char
    # run were affected, which is why it looked item-specific.
    def _sentences(text: str) -> set[str]:
        text = _re.sub(r"\x00REF:[^\x00]*\x00|<Ref\b[^>]*/?>|REF:[\w.:-]+",
                       " ", text)
        text = _re.sub(r"[\s\x00]+", " ", text)
        return {t.strip() for t in _re.split(r"(?<=[.!?])\s+", text)
                if len(t.strip()) >= 60}

    # Substring, not set membership. Resolving a Ref removes a line break, so a
    # heading and the label beneath it merge into one "sentence" in the served copy
    # and would read as extra text on every correct dump.
    flat = _re.sub(r"[\s\x00]+", " ",
                   _re.sub(r"\x00REF:[^\x00]*\x00|<Ref\b[^>]*/?>|REF:[\w.:-]+",
                           " ", want))
    return [t for t in _sentences(body) if t not in flat]


def _idmap_searchable_text(raw: str) -> str:
    """The dump's text as the PROMPT reads, not as the file stores it.

    The dump is JSON, so a prompt line that quotes a word is stored with `\\"`
    and a raw substring test can never match it. That is not a rare shape: Q4a's
    `A_NO_KEYWORD` and Q4c's `C_NO_KEYWORD` lines quote the very words they are
    about, and both items were refused as STALE IDMAP while the dump was serving
    them perfectly. Q4a lost its slot in a six-run sweep to it.

    A false STALE reading is costly in the wrong direction. A missed staleness
    measures the wrong prompt, which is what this check exists to prevent; a
    false one blocks an item from being measured AT ALL, and reads as evidence
    that the dump needs replacing when nothing is wrong with it. Decoding is
    strictly more faithful, not more permissive: it compares the same lines the
    server will render.
    """
    import json as _json

    def walk(o):
        if isinstance(o, str):
            yield o
        elif isinstance(o, dict):
            for v in o.values():
                yield from walk(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk(v)

    try:
        return "\n".join(walk(_json.loads(raw)))
    except Exception:
        return raw          # unparseable: fall back rather than pass silently


def check_fixture_is_not_corrupt(items: list) -> None:
    """Refuse to spend calls on a fixture the student did not write.

    THE SWEEP IS THE EXPENSIVE PART, so an input defect has to be caught before
    it and not diagnosed out of the rows afterwards. 2a's structural experiment
    removed the item's `counts` group, which also removed score.py's span
    distribution -- the thing that rebuilds handout 3's boxes -- so every
    scorer-sourced box collapsed to the placeholder "2 found". 120 calls then
    measured the item at 10/20 against a baseline of 15/20 and the change read as
    refuted when it had never been tested at all.
    """
    import enforcement

    bad = enforcement.check_fixture_boxes_hold_the_students_words(items)
    if not bad:
        return
    shown = "\n".join(f"    {b}" for b in bad[:4])
    more = f"\n    ... and {len(bad) - 4} more" if len(bad) > 4 else ""
    raise SystemExit(
        f"CORRUPT FIXTURE: {len(bad)} box(es) hold text the student never "
        f"wrote.\n{shown}{more}\n  Nothing is measured until this is fixed -- a "
        f"sweep over these inputs produces a number about the placeholder, not "
        f"about the prompt."
    )


LOBLOCKS = str(paths.LO)


def server_code_is_stale() -> list[str]:
    """Source files newer than the dev server that is about to be measured.

    THE IDMAP CHECK BELOW GUARDS THE CONTENT. Nothing guarded the CODE, and on
    2026-09-09 that cost 19 mis-scored observations across four items.

    WHAT HAPPENED. `slotSheet.ts` computes a mapped check from its pick --
    `out[r.key] = spec ? isSatisfied(spec, mappedVerdict(r, checks)) : false` --
    and `mappedVerdict` reads `refers_to ?? verdict`, so a migrated pick resolves
    correctly. Run against 1c/p8's real payload the current code returns `met`
    and AWARDS legend's 2 points, scoring the cell 8.0, which is gold. The
    running server scored it 6.0: it charged the model's raw `absent` instead.
    The server had been up since 2026-08-29 11:55, `slotSheet.ts` was modified
    2026-08-31 22:23, and the process runs a plain tsx loader with NO watch flag.
    So the code was three days behind the repo while serving CURRENT content --
    which is exactly the combination the idmap check cannot see, because the
    content it verifies was fresh.
    THE COST FELL ONLY ON MAPPED SLOTS, which is why it hid so long: `maps=`
    appears on four LLMActions (Q2 wgb_inverts_utb, Q4a antecedent_1/_2, Q4b
    behavior_1/_2, 1c legend) and nowhere in handout 2. Every other slot the app
    answers directly, so every other number was right.
    AND THE PYTHON SIDE WAS UNAFFECTED, which is what made it look like an
    engine disagreement: `agreement.py` parses and applies `maps` itself, so it
    read 0 off-map where the app read 19. That difference was a stale server, not
    two engines -- the trap QUALITY_CONTROL.md §2g names.

    Compares mtimes against the process start time, so it costs nothing and needs
    no request. Returns a list of findings; the caller decides whether to refuse.
    """
    import glob
    import os
    import pathlib

    procs = glob.glob("/proc/[0-9]*/cmdline")
    started = None
    for path in procs:
        try:
            with open(path, "rb") as fh:
                cmd = fh.read().decode("utf-8", "replace")
        except OSError:
            continue
        # MATCH ON THE EXECUTABLE, NOT THE COMMAND TEXT. Testing only the command
        # string matched THIS SESSION'S OWN SHELL -- a bash process that had just
        # grepped for those words -- and reported that shell's start time as the
        # server's, so the check read fresh while a three-day-old process held
        # the port. A cmdline substring is not a process identity. And the
        # missing `import pathlib` below made every real candidate raise inside
        # the try and fall through to "no server found", which is how a wired
        # check can be confidently wrong in both directions at once.
        try:
            exe = os.path.realpath(pathlib.Path(path).with_name("exe"))
        except OSError:
            continue
        if os.path.basename(exe) != "node":
            continue
        if "apps/server/src/index.ts" in cmd and "lo-blocks" in cmd:
            # THE PROCESS START TIME, not the mtime of /proc/<pid> -- that
            # directory's mtime is not the start time and the first version of
            # this check read 0 findings against a server known to be three days
            # stale. field 22 of /proc/<pid>/stat is starttime in clock ticks
            # since boot; boot itself is `btime` in /proc/stat.
            try:
                stat = pathlib.Path(path).with_name("stat").read_text()
                ticks = float(stat.rsplit(")", 1)[1].split()[19])
                hz = os.sysconf("SC_CLK_TCK")
                btime = next(
                    float(ln.split()[1])
                    for ln in pathlib.Path("/proc/stat").read_text().splitlines()
                    if ln.startswith("btime "))
                started = btime + ticks / hz
            except Exception:
                continue
            break
    if started is None:
        return ["no lo-blocks server process found, so its code cannot be dated "
                "-- start one, or measure knowing the code is unverified"]
    newer = []
    for pat in ("packages/shared/lib/llm/*.ts", "apps/server/src/**/*.ts"):
        for f in glob.glob(os.path.join(LOBLOCKS, pat), recursive=True):
            if f.endswith((".test.ts", ".d.ts")):
                continue
            if os.path.getmtime(f) > started:
                newer.append(os.path.relpath(f, LOBLOCKS))
    if not newer:
        return []
    return [f"THE DEV SERVER IS RUNNING STALE CODE: {len(newer)} source file(s) "
            f"are newer than the process that will answer this sweep -- "
            f"{', '.join(sorted(newer)[:4])}"
            f"{' ...' if len(newer) > 4 else ''}. It runs a plain tsx loader with "
            f"no watch flag, so nothing reloaded them. Restart it before "
            f"measuring: the last time this went unnoticed the server was three "
            f"days behind and silently charged every MAPPED slot from the model's "
            f"raw answer instead of computing it from its pick."]


def check_idmap_is_current(idmap: str, item_id: str) -> None:
    """Refuse to measure against a dump that predates the current prompt.

    The prompt reaches the scorer through THREE stages — rubric_hN.py, then the
    .olx files that olx_prompts.py generates, then the idmap dumped out of the
    dev server — and only the third is what a run actually measures. Reverting
    the source and confirming `olx_prompts.py --check` says "up to date" leaves
    the first two in agreement and says nothing about the third.

    That gap cost a whole sweep. A loosened Q6 matching rule was implemented,
    measured at 16/19 -> 12/19, and reverted; the re-baseline run was then
    launched against the idmap dumped WHILE the loosened rule was live, so it
    silently re-measured the reverted change. Two cells looked like regressions
    caused by unrelated fixture repairs, and one of those repairs was very nearly
    reverted on the strength of it.

    Lines carrying a `REF:` marker are skipped: the server resolves those into
    the student's own text, so they cannot appear in a dump verbatim. Everything
    else in the generated prompt must be present in the dump.
    """
    import olx_prompts as _OP

    # TWO REASONS THIS CAN FAIL, AND THEY ARE NOT THE SAME FACT. Found
    # 2026-09-09: T1 and T2 printed an unverifiable-freshness notice carrying a
    # bare KeyError on their own id, and the run continued UNVERIFIED -- the
    # exact silence this check exists to end.
    #
    # (1) THE ITEM HAS NO GENERATED LLM PROMPT. `olx_prompts.ACTION` holds 23
    #     items; T1, T2 and 1b are not among them, because they are TYPE-CHOICE
    #     items graded by a sheet grader (`bmod_h2_t1_sheet_grader`) rather than
    #     by an <LLMAction> with a slot sheet. There is nothing in the dump for
    #     this check to compare, so skipping is CORRECT -- but it must SAY that,
    #     rather than implying a verification was attempted and failed.
    # (2) ANYTHING ELSE is a real failure of a check whose own docstring records
    #     that an unverified dump cost a whole sweep. Skipping quietly there is
    #     the dangerous case, so it REFUSES.
    if item_id not in getattr(_OP, "ACTION", {}):
        print(f"(no idmap check for {item_id}: it has no generated LLMAction "
              f"prompt -- a type-choice item graded by its sheet grader, so the "
              f"dump carries no prompt text to compare)", file=sys.stderr)
        return
    try:
        want = _OP.build_web_prompt(item_id)
    except Exception as exc:
        raise SystemExit(
            f"CANNOT CHECK THE DUMP for {item_id}: building its prompt raised "
            f"{type(exc).__name__}: {exc}\n"
            f"  {item_id} IS in olx_prompts.ACTION, so a prompt is expected and "
            f"this is a real failure, not an item without one. Refusing rather "
            f"than measuring against an unchecked dump -- see this check's "
            f"docstring for the sweep that cost.")
    lines = [ln.strip() for ln in want.split("\n")
             if 40 < len(ln.strip()) < 130
             and "REF:" not in ln and "<Ref" not in ln]
    if not lines:
        return
    try:
        with open(idmap) as fh:
            blob = _idmap_searchable_text(fh.read())
    except OSError as exc:
        raise SystemExit(f"cannot read --idmap {idmap}: {exc}")
    missing = [ln for ln in lines if ln not in blob]
    extra = _idmap_extra_lines(idmap, item_id, want)
    if not missing and not extra:
        print(f"(idmap checked: it serves the current {item_id} prompt, "
              f"{len(lines)} lines matched, nothing extra)", file=sys.stderr)
        return
    if extra and not missing:
        sample = "\n".join(f"    + {ln[:100]}" for ln in extra[:3])
        raise SystemExit(
            f"SUPERSET IDMAP: the {item_id} prompt in {idmap} carries "
            f"{len(extra)} line(s) the rubric no longer generates.\n{sample}\n"
            f"  The dump was taken while extra rule text was live and that text "
            f"was later reverted, so this run would measure a rule the repo does "
            f"not contain. Re-dump it:\n"
            f"    curl -s 'http://localhost:8888/api/olxjson?id=all' > <newfile>")
    sample = "\n".join(f"    - {ln[:100]}" for ln in missing[:3])
    raise SystemExit(
        f"STALE IDMAP: {len(missing)} of {len(lines)} lines of the {item_id} "
        f"prompt that rubric/olx_prompts generate are ABSENT from {idmap}.\n"
        f"{sample}\n"
        f"  The dump predates the current prompt, so this run would measure "
        f"something the repo no longer says. Re-dump it:\n"
        f"    curl -s 'http://localhost:8888/api/olxjson?id=all' > <newfile>\n"
        f"  (run `python3 olx_prompts.py --write` first if the .olx files are "
        f"themselves behind the rubric.)")


def _normalize_empty_fields(rec: dict, job: dict) -> dict:
    """An empty input field is `absent`, and it has nothing to quote.

    Measured on the 3-pass Q6 sweep of 2026-08-18: six times across five cells
    the grader returned `incomplete` for a box that was EMPTY, and since
    `incomplete` obliges it to quote the text that falls short, it quoted the
    nearest thing to hand -- the string "WRITING TO THE STUDENT", a heading in
    the prompt itself. That put words in the student's feedback that the student
    never wrote. The prompt now forbids it (rule 1 in olx_prompts), but a prompt
    is a request; this is the invariant, so it is also enforced here.

    `incomplete` means text is present and falls short, so it cannot describe an
    empty field -- there is no gradient between "wrote nothing" and "wrote
    something inadequate". The verdict is corrected to `absent` and the evidence
    dropped.

    This corrects the verdicts WE store and read back; the published score is
    computed inside the app (`grader.score`) and this function cannot and does
    not touch it. That is fine because the two verdicts score the same, which is
    measurable rather than assumed: p7 and p8 each took `incomplete` in one pass
    and `absent` in the other two with no other field moving, and scored 5.00 in
    all three. That equality is also why the leak survived three full passes
    without disturbing a single number -- it was only ever visible in the prose
    the student reads.
    """
    vals = job.get("fixture") or {}
    empty = {k for k, v in vals.items() if not (v or "").strip()}
    if not empty:
        return rec
    for slot in list((rec.get("verdicts") or {}).keys()):
        # slots are named by the component id's suffix (affect_c2 <- bmod_h1_q6_affect_c2)
        if not any(k == slot or k.endswith("_" + slot) for k in empty):
            continue
        if rec["verdicts"][slot] in ("absent", None):
            continue
        rec.setdefault("_corrected", []).append(
            f"{slot}: {rec['verdicts'][slot]} -> absent (field is empty)")
        rec["verdicts"][slot] = "absent"
        ev = rec.get("evidence")
        if isinstance(ev, dict) and ev.get(slot):
            ev[slot] = ""
    return rec


def run_jobs(jobs: list[dict], idmap: str, on_cell=None) -> list[dict]:
    tmp = tempfile.mkdtemp(prefix="agreement_app_")
    jf, rf = os.path.join(tmp, "jobs.json"), os.path.join(tmp, "results.json")
    with open(jf, "w") as fh:
        json.dump(jobs, fh)
    env = {
        **os.environ, "RUN_LLM_RUNNER": "1",
        "JOBS_JSON": jf, "RESULTS_JSON": rf, "IDMAP_JSON": idmap,
    }
    print(f"driving {len(jobs)} cell(s) through the app", file=sys.stderr)
    # STREAMED, not captured. `subprocess.run(capture_output=True)` held the
    # runner's stdout in memory until vitest exited, so the per-cell "[runner]"
    # lines it prints all arrived in one burst at the end of a ~12-minute pass:
    # a run in progress was indistinguishable from a run that had hung, and
    # diagnosing one meant walking down four levels of child process to find the
    # node worker actually doing the work.
    proc = subprocess.Popen(
        ["npx", "vitest", "run", "--reporter=dot", RUNNER],
        cwd=LO, env=env, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=1,
    )
    by_cell = {j.get("cell"): j for j in jobs}
    tail: list[str] = []
    seen: set[str] = set()
    for line in proc.stdout:                       # type: ignore[union-attr]
        tail.append(line)
        del tail[:-40]
        if "[runner]" not in line:
            continue
        print("  " + line.strip(), file=sys.stderr)
        if on_cell is None:
            continue
        # The runner rewrites its results file after every cell, so the record
        # for the cell just announced is already on disk.
        try:
            with open(rf) as fh:
                done = json.load(fh)
        except Exception:
            continue
        for rec in done:
            if rec.get("cell") and rec["cell"] not in seen:
                seen.add(rec["cell"])
                _normalize_empty_fields(rec, by_cell.get(rec["cell"], {}))
                try:
                    on_cell(rec)
                except Exception as exc:           # never let reporting kill a run
                    print(f"  (cell report failed: {exc})", file=sys.stderr)
    proc.wait()
    if not os.path.exists(rf):
        print("".join(tail)[-2000:], file=sys.stderr)
        raise SystemExit("runner produced no results")
    with open(rf) as fh:
        out = json.load(fh)
    for rec in out:
        _normalize_empty_fields(rec, by_cell.get(rec.get("cell"), {}))
    return out


def main() -> int:
    # NOT WHILE THE AUDIT SELF-TEST IS RUNNING. It injects breakages into the
    # rubric and enforcement source this process reads live, so an overlapping
    # sweep scores some cells against a rule nobody wrote -- and says nothing.
    # The mirror of olx_prompts._measurements_in_flight, which guards the other
    # direction. See refuse_if_selftest_running for the escape.
    import olx_prompts as _OP_GUARD
    _OP_GUARD.refuse_if_selftest_running("this app sweep")

    ap = argparse.ArgumentParser(description=__doc__.split("Run:")[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--item", default="Q6", choices=sorted(JOBS))
    ap.add_argument("--participants", type=int, nargs="*", default=None)
    ap.add_argument("--idmap", default=None, help="Cached /api/olxjson?id=all dump.")
    ap.add_argument("--exclude", type=int, nargs="*", default=None,
                    help="Participants to drop. Omit for this handout's defaults "
                         "(exemplar and mis-transcribed rows); pass with no values "
                         "to include everyone — the exemplar exclusion is specific "
                         "to Q6's prompt and does not apply to other items.")
    ap.add_argument("--out", default=None, help="Write per-cell JSON here.")
    ap.add_argument("--baseline", default=None,
                    help="A previous --out file. Each cell is reported as "
                         "same/improvement/regression against it as it lands.")
    ap.add_argument("--force-checks", action="store_true",
                    help="Run despite the call-free structural gate, for the case "
                         "where this sweep is what settles a finding the checks "
                         "are reporting. Same meaning as agreement.py's flag.")
    ap.add_argument("--runs", type=int, default=3,
                    help="How many times to drive the item (default 3). One run is "
                         "not a measurement on this side: Q3 measured 16/20, 12/20 "
                         "and 15/20 over three runs — a 4-cell spread, against a "
                         "5-point apparent gap to the CLI that turned out to be 0.3 "
                         "cells. `--runs 1` is available for a quick look but its "
                         "number should not be quoted.")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    if args.runs < 1:
        raise SystemExit("--runs must be at least 1")

    if args.list:
        for k, v in JOBS.items():
            print(f"{k}: screen={v['screen']} grader={v['grader']}")
        return 0

    spec = JOBS[args.item]
    handout = spec["handout"]
    # Excluded cells are RUN and only kept out of the RATE — see
    # handouts.cell_exclusions(). Skipping them used to save the calls; it also
    # discarded the one piece of evidence a counted cell cannot give, namely
    # whether the model gets a cell whose answer is sitting in its own prompt.
    per_item = ({} if args.exclude is not None
                else _handouts.cell_exclusions(handout, args.item))
    drop = set(args.exclude or ()) if args.exclude is not None else set()
    pids = [p for p, _ in find_submissions(handout, args.participants) if p not in drop]
    if drop:
        print(f"(excluding {sorted(drop)} outright — explicit --exclude)", file=sys.stderr)
    for pid, (kind, why) in sorted(per_item.items()):
        print(f"(not counted: p{pid} on {args.item} [{kind}] — {why}; run anyway)",
              file=sys.stderr)

    idmap = args.idmap
    if not idmap:
        raise SystemExit("--idmap is required: curl the dev server's "
                         "/api/olxjson?id=all to a file and pass it")
    check_idmap_is_current(idmap, args.item)
    check_fixture_is_not_corrupt([args.item])
    # THE CALL-FREE STRUCTURAL GATE, which this harness did not run at all until
    # 2026-09-03 while agreement.py did. Both spend the same money on the same
    # corpus, so a check worth running before one sweep is worth running before
    # the other; the asymmetry meant a finding that stopped the python side
    # silently let the app side through. Same `--force-checks` override.
    if not getattr(args, "force_checks", False):
        import agreement as _A
        if _A.cheap_checks_gate():
            return 1

    jobs = build_jobs(args.item, pids)
    how_by_cell = {j["cell"]: j["split_how"] for j in jobs}
    fb_by_cell = {j["cell"]: j["fell_back"] for j in jobs if j["fell_back"]}

    # Report each cell as it lands, against gold AND against a previous run, so
    # a sweep says whether it is same / better / worse WHILE it runs instead of
    # only in a table 36 minutes later. `--baseline` takes a prior --out file.
    _gold_now = config(handout)["gold"]()
    _base: dict[int, float] = {}
    if args.baseline:
        # Compare against the PER-CELL MEDIAN of the baseline sweep, which is what
        # its table reported. --out holds one run: the `published` index in the
        # sibling .runs.json, chosen by "median by exact count". That run is the
        # median by TOTAL, so any individual cell in it can sit at either
        # extreme — and reading it as the baseline mislabels cells. It called p15
        # an IMPROVEMENT against a baseline whose median was already exact, and
        # left me comparing single draws on an item where 9 of 20 cells take more
        # than one value across identical passes.
        _runs_path = re.sub(r"\.json$", ".runs.json", args.baseline)
        _how = None
        try:
            if os.path.exists(_runs_path):
                _vals: dict[int, list[float]] = {}
                with open(_runs_path) as fh:
                    for _r in json.load(fh).get("runs", []):
                        for rec in _r.get("results", []):
                            frac = (rec.get("grader") or {}).get("score")
                            if frac is None or not rec.get("ok"):
                                continue
                            _bp = int(re.match(r"p(\d+)/", rec["cell"]).group(1))
                            _vals.setdefault(_bp, []).append(
                                round(float(frac) * float(rec["sheet_max"]), 2))
                _base = {p: statistics.median(v) for p, v in _vals.items() if v}
                _n = max((len(v) for v in _vals.values()), default=0)
                _how = f"per-cell median of {_n} run(s) in {os.path.basename(_runs_path)}"
            else:
                with open(args.baseline) as fh:
                    for rec in json.load(fh).get("results", []):
                        frac = (rec.get("grader") or {}).get("score")
                        if frac is None or not rec.get("ok"):
                            continue
                        _bp = int(re.match(r"p(\d+)/", rec["cell"]).group(1))
                        _base[_bp] = round(float(frac) * float(rec["sheet_max"]), 2)
                _how = (f"ONE RUN from {os.path.basename(args.baseline)} — no "
                        f".runs.json beside it, so single-draw labels")
            print(f"(comparing against {len(_base)} cell(s), {_how})",
                  file=sys.stderr)
        except Exception as exc:
            print(f"(cannot read --baseline: {exc})", file=sys.stderr)
            _base = {}

    def _report_cell(rec: dict) -> None:
        m = re.match(r"p(\d+)/", rec.get("cell") or "")
        if not m:
            return
        pid = int(m.group(1))
        frac = (rec.get("grader") or {}).get("score")
        if not rec.get("ok") or frac is None:
            print(f"      p{pid:<3} FAILED — {rec.get('status')}", file=sys.stderr)
            return
        pred = round(float(frac) * float(rec["sheet_max"]), 2)
        g = (_gold_now.get(pid, {}).get(args.item, {}) or {}).get("score")
        if g is None:
            print(f"      p{pid:<3} pred={pred:.2f}  (no gold row)", file=sys.stderr)
            return
        exact = _handouts.scored_exactly(args.item, g, pred)
        mark = "exact" if exact else f"{pred - g:+.2f}"
        note = ""
        if pid in _base:
            b = _base[pid]
            was_exact = _handouts.scored_exactly(args.item, g, b)
            if abs(b - pred) < 0.005:
                note = "  SAME as baseline"
            elif exact and not was_exact:
                note = f"  IMPROVEMENT (was {b - g:+.2f})"
            elif was_exact and not exact:
                note = f"  REGRESSION (was exact)"
            elif abs(pred - g) < abs(b - g):
                note = f"  improvement (was {b - g:+.2f})"
            else:
                note = f"  regression (was {b - g:+.2f})"
        print(f"      p{pid:<3} gold={g:5.2f} pred={pred:5.2f}  {mark:>6s}{note}",
              file=sys.stderr)

    results = run_jobs(jobs, idmap, on_cell=_report_cell)
    # --out is written AFTER the median is chosen, further down. It used to be
    # written here, from run 1, while the table below reported the median — so the
    # two disagreed whenever the median was not run 1, and anything reading the
    # .json for per-slot verdicts was reading a different run than the scores it
    # was being compared against.
    gold = config(handout)["gold"]()
    dropped_1c: list[int] = []
    if args.item == "1c":
        gold, dropped_1c = rebuild_gold_1c(gold)
        print("(item 1c is compared on all five slots, 10 points — the graph gate, "
              "the title, both axis labels and the legend. It was once a 3-slot "
              "6-point subtotal on the reasoning that the web cannot fail "
              "has_own_graph or legend; it can, and does)", file=sys.stderr)
        if dropped_1c:
            print(f"(excluding {dropped_1c} from 1c — gold 0 for no graph, but four "
                  f"complete weeks of data, which on the web DRAWS the chart, so the "
                  f"failure is unreachable rather than missed. p15 and p18 are KEPT: "
                  f"their data is incomplete and the gate does fire)", file=sys.stderr)

    def tabulate(res):
        """-> (comparable rows, real failures, cells with no gold to compare to).

        A missing GOLD row is not a harness failure. The harness ran the cell,
        the app scored it, and there is simply nothing on the other side of the
        comparison — 1c's p4/p19/p20 are registered `unscoreable` for exactly
        that reason, and Q4b's p2 has no gold row at all. Counting them as
        failures made those items exit non-zero on every run, which is the state
        a REAL failure has to be visible against.

        A missing GRADER score is still a failure: the cell was supposed to
        produce one and did not.
        """
        rows, failures, no_gold = [], [], []
        for r in res:
            pid = int(re.match(r"p(\d+)/", r["cell"]).group(1))
            if not r["ok"]:
                failures.append((pid, r["status"],
                                 (r.get("error") or r["feedback"])[:120]))
                continue
            g = gold.get(pid, {}).get(args.item, {}).get("score")
            frac = (r.get("grader") or {}).get("score")
            if frac is None:
                failures.append((pid, "no grader score", f"gold={g} grader=None"))
                continue
            if g is None:
                no_gold.append((pid, round(float(frac) * float(r["sheet_max"]), 2)))
                continue
            pred = round(float(frac) * float(r["sheet_max"]), 2)
            rows.append((pid, g, pred, r["verdicts"]))
        return rows, failures, no_gold

    # Runs 2..N. The FIRST run is `results`, already driven above so that a
    # fixture or server failure surfaces before spending on repeats.
    all_runs = [tabulate(results)]
    all_results = [results]
    for i in range(2, args.runs + 1):
        print(f"(run {i} of {args.runs})", file=sys.stderr)
        extra = run_jobs(jobs, idmap, on_cell=_report_cell)
        all_results.append(extra)
        all_runs.append(tabulate(extra))

    def counted(rows):
        """The rows the RATE is computed over — excluded cells are run, not counted."""
        return [r for r in rows if r[0] not in per_item]

    _spec = config(handout)["rubric"].BY_ID[args.item]

    def _hit(g, p):
        """Exact, or the nearest reachable score where gold is unreachable."""
        return _handouts.scores_as_exact(_spec, g, p)

    def exact_of(rows):
        return sum(1 for _, g, p, _ in counted(rows) if _hit(g, p))

    # MEDIAN by exact count, ties to the lowest run index. Fixed here, in code,
    # deliberately: choosing which run to publish after seeing the numbers is how
    # a best-of-three got promoted into a report earlier and read as a real
    # 6-point difference between the two implementations.
    order = sorted(range(len(all_runs)), key=lambda i: (exact_of(all_runs[i][0]), i))
    pick = order[len(order) // 2]
    rows, failures, no_gold = all_runs[pick]
    results = all_results[pick]

    # PER-CELL MEDIAN, not a published run — the same change as agreement.py, and
    # it has to happen on both sides or the two harnesses stop being comparable.
    # Publishing one run reports every cell at whatever THAT run gave it, so a
    # bistable cell lands wherever the winning run fell and a cell-by-cell diff
    # between two configurations invents differences. The run selection survives
    # only to source the non-score fields from one coherent pass.
    if len(all_runs) > 1:
        by_pid: dict[object, list[float]] = {}
        for r, *_ in all_runs:
            for row in r:
                by_pid.setdefault(row[0], []).append(row[2])
        rows = [(row[0], row[1], statistics.median(by_pid[row[0]])) + tuple(row[3:])
                for row in rows]
    # Split BEFORE anything reads either half. This lived next to the table it
    # feeds, which put it AFTER the `uncounted` report that consumes it: every
    # item ran its three runs and then died on an unbound name, losing a finished
    # 26-item sweep to a line ordering.
    kept = [r for r in rows if r[0] not in per_item]
    uncounted = [r for r in rows if r[0] in per_item]
    rows = kept

    if args.runs > 1:
        counts = [exact_of(r) for r, *_ in all_runs]
        sizes = [len(counted(r)) for r, *_ in all_runs]
        per_run = ", ".join(f"{c}/{s}" for c, s in zip(counts, sizes))
        spread = max(counts) - min(counts)
        print(f"\n{args.runs} runs — exact {per_run}   mean {statistics.fmean(counts):.1f}"
              f"   spread {spread} cell(s)")
        print("publishing the PER-CELL median across runs; non-score fields come "
              f"from run {pick + 1}")
        # This spread is the spread of SCORES, and it understates how much moves
        # underneath them. Audited on the Q6 sweep of 2026-08-18, which reported a
        # spread of one cell: only 5 of 20 cells returned the same JUDGEMENT in all
        # three passes. The other 15 drifted on 24 verdict fields and 8 `refers_to`
        # fields, and most of that drift is invisible here -- one cell swung a slot
        # across `mismatch`/`absent`/`met` in three passes and scored exact every
        # time, and three cells flipped a `confident` that carries no points.
        #
        # Two consequences worth keeping in mind when reading any table below.
        # A cell that is "stably exact" may be stably exact for a reason that is
        # not stable, so a later prompt change can move it without having touched
        # what it appears to be about. And the drift is not spread evenly: on Q6 it
        # sits entirely in the four `state_*` slots, the ones carrying `refers_to`
        # -- the `change_*` and `affect_*` slots drifted on zero cells out of
        # twenty. Deciding WHETHER the student described something is stable;
        # deciding WHICH listed item they described is not.
        # AND THREE PASSES CANNOT SUPPORT A PER-CELL CLAIM. The median is sound
        # for the ITEM total; "cell X is wrong" is a different assertion and needs
        # more passes than this. Measured on Q6 at nine passes: p9 is exact 5 of 9,
        # 56% with a 95% interval of [27%, 81%], while p4 is exact 1 of 9, 11%
        # [2%, 44%]. Both look identical in a 3-pass table -- each shows as a
        # -1.25 miss -- and they are not remotely the same cell. p9 has nothing
        # consistent to fix; p4 does.
        #
        # The cost of not knowing that was four rule variants each credited with
        # "fixing p9", which a 56% cell does for free. Before concluding anything
        # about a single cell, or about a change that turns on one, re-run it at
        # nine passes; see out/q6_baserate.
        if spread and sizes[0]:
            print(f"read the table below as +/-{spread} cell(s) "
                  f"({100 * spread / sizes[0]:.0f} points): a single run of this item "
                  f"cannot resolve a difference smaller than that")

    if args.out:
        # THE SAME GUARD agreement.py CARRIES, and this harness never got it.
        # Its comment there records that a missing output directory cost 720
        # calls, and a trailing slash another 720. On 2026-09-01 it cost twelve
        # more runs here: both Q4a and Q4c completed all six passes and then died
        # on `FileNotFoundError: .../e25_fix_web/Q4a.json` because the directory
        # did not exist. Every cell had been scored and every result was thrown
        # away at the last statement. A run's artifact must not depend on someone
        # having run mkdir.
        import os as _os
        out = args.out
        if out.endswith(("/", _os.sep)) or _os.path.isdir(out):
            out = _os.path.join(out, f"{args.item}.json")
            print(f"--out named a directory; writing {out}", file=sys.stderr)
        _os.makedirs(_os.path.dirname(_os.path.abspath(out)), exist_ok=True)
        args.out = out
        with open(args.out, "w") as fh:
            json.dump({"item": args.item, "results": results}, fh, indent=2)
        print(f"wrote {args.out}", file=sys.stderr)
        # EVERY run, not just the published one. Keeping only the median made the
        # two sides incomparable at the verdict level: the CLI stores one file per
        # run, so its firing rates could be counted over 5 or 8 runs, while this
        # side offered a single median and its siblings were discarded. A "3 of 3"
        # on the web therefore hid six unrecorded runs, and the web-vs-CLI gap on
        # Q2's `wgb_is_counterpart` could not be told from sampling for want of a
        # denominator.
        if args.runs > 1:
            side = args.out[:-5] if args.out.endswith(".json") else args.out
            path = f"{side}.runs.json"
            with open(path, "w") as fh:
                json.dump({
                    "item": args.item,
                    "rule": "median by exact count, ties to lowest index",
                    "published": pick + 1,
                    # See measured.era_stamp: an artifact that does not say what
                    # it ran against cannot be compared with another artifact.
                    "era": _era_for([args.item] if args.item else None),
                    "runs": [{"run": i + 1,
                              "exact": exact_of(all_runs[i][0]),
                              "n": len(all_runs[i][0]),
                              "results": all_results[i]}
                             for i in range(len(all_results))],
                }, fh, indent=2)
            print(f"wrote {path} ({len(all_results)} runs)", file=sys.stderr)

    print(f"\nlo-blocks {args.item} via the app — {len(rows)} cell(s)\n")
    print(f"{'pid':>4} {'gold':>6} {'pred':>6} {'diff':>6}")
    print("-" * 26)
    for pid, g, pred, _ in sorted(rows):
        print(f"{pid:>4} {g:>6.2f} {pred:>6.2f} {pred-g:>+6.2f}")
    if rows:
        errs = [p - g for _, g, p, _ in rows]
        exact = sum(1 for _, g, p, _ in rows if _hit(g, p))
        print("-" * 26)
        print(f"exact {exact}/{len(errs)} ({exact/len(errs):.0%})  "
              f"MAE {statistics.mean(map(abs, errs)):.2f}  "
              f"bias {statistics.mean(errs):+.2f}")

    if uncounted:
        print("\nnot counted in the rate, but run — how they scored:")
        meaning = {
            "self_graded": "the prompt contains the answer and the grader's decision "
                           "— a miss here is evidence of a problem with the model",
            "unscoreable": "no correct scorer can reach this gold — a miss is EXPECTED",
            "suspect":     "the submission is mis-transcribed — a miss says nothing",
        }
        for kind in _handouts.EXCLUSION_KINDS:
            mine = [r for r in uncounted if per_item[r[0]][0] == kind]
            if not mine:
                continue
            ok = sum(1 for _, g, p, _ in mine
                     if _handouts.scored_exactly(args.item, g, p))
            print(f"  {kind:<12} {ok}/{len(mine)} scored correctly — {meaning[kind]}")
            for pid, g, pred, _ in sorted(mine):
                if not _handouts.scored_exactly(args.item, g, pred):
                    flag = "  <-- MISSED" if kind == "self_graded" else ""
                    print(f"      p{pid:<3} gold={g:.2f} pred={pred:.2f}{flag}")
                stale = _handouts.stale_claim(args.item, pid, g, pred)
                if stale:
                    print(f"      p{pid:<3} {stale}")

    if fb_by_cell:
        print("\ncells where a field this handout left empty was taken from another "
              "handout's submission by the same student:")
        for cell, secs in sorted(fb_by_cell.items()):
            print(f"      {cell}: {', '.join(secs)}")

    from collections import Counter
    methods = Counter(m for k, c in how_by_cell.items() for kk, m in c.items()
                      if not kk.startswith("_prov:"))
    print(f"\nfixture reconstruction: {dict(methods)}")

    # Provenance of every reconstructed field this item was seeded from. A source
    # that is COMPUTED rather than recorded is named separately: the rate above is
    # then partly a measurement of arithmetic, and that belongs next to it.
    SYNTHESISED = ("weekly_total_spread",)
    prov = Counter(m for c in how_by_cell.values()
                   for k, m in c.items() if k.startswith("_prov:"))
    if prov:
        print(f"reconstructed field provenance: {dict(prov)}")
        # simulate_h3's own trust ordering, worth restating where the numbers are
        # read: `chart_xml` is literal recorded values, `model` is a reading of the
        # student's data table or image (transcription, so fallible), and anything
        # in SYNTHESISED was computed from something they wrote rather than read.
        print("  trust: chart_xml (literal) > model (transcribed) > "
              "weekly_total_spread (computed)")
        synth = {c: sorted(m for k, m in h.items()
                           if k.startswith("_prov:") and m in SYNTHESISED)
                 for c, h in how_by_cell.items()}
        synth = {c: v for c, v in synth.items() if v}
        if synth:
            n = sum(len(v) for v in synth.values())
            print(f"*** {n} field(s) across {len(synth)} cell(s) are SYNTHESISED, not "
                  f"recorded — those cells score computed values:")
            for c, v in sorted(synth.items()):
                print(f"      {c}: {Counter(v)}")
        else:
            print("  every reconstructed field is a recorded value, none computed")
    weak = sorted(c for c, h in how_by_cell.items()
                  if any(m in ("single", "empty")
                         for k, m in h.items() if not k.startswith("_prov:")))
    if weak:
        print("cells where a paper answer held one entry, so the second field is "
              f"empty (a state the graders score): {weak}")

    if no_gold:
        print(f"\n{len(no_gold)} cell(s) ran but have no gold to compare against — "
              f"not a failure, and not in the rate:")
        for pid, pred in sorted(no_gold):
            why = per_item.get(pid, (None, None))[1]
            print(f"      p{pid}: scored {pred:.2f}, gold has no row"
                  + (f" — {why}" if why else ""))

    if failures:
        print(f"\n*** {len(failures)} cell(s) did not produce a score — the rates "
              f"above cover a biased subset:")
        for pid, why, detail in failures:
            print(f"      p{pid}: {why} — {detail}")
        return 1
    print("\nfailed cells: 0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
