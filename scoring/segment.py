"""Segment a submission into {item_id: student_response} by diffing the template.

Every submission in this corpus is the blank handout with typed answers
inserted, so the reliable way to isolate student text is to subtract the
template. This matters beyond tidiness: Handout 1's template carries a worked
"fruit-flavored water" example and Handout 3's carries an example data table
AND an example graph. A scorer that reads those as student work scores them.
"""

from __future__ import annotations

import difflib
import re

from docx_text import doc_lines

# Section markers, in document order. The first regex that matches a line
# opens that item; every non-template line after it belongs to that item.
H1_MARKERS: list[tuple[str, str]] = [
    ("preamble", r"Choose an unwanted target behavior"),
    ("Q1", r"Define your unwanted target behavior and explain WHY"),
    ("Q2", r"Next,\s*define your wanted goal behavior"),
    ("Q3", r"Use the SMART goal acronym"),
    ("_q4_intro", r"Perform a functional behaviora?l? analysis"),
    ("Q4a", r"^\W*4a[.)]"),
    ("Q4b", r"^\W*4b[.)]"),
    ("Q4c", r"^\W*4c[.)]"),
    ("Q5", r"Why do you think that you continue to engage"),
    ("Q6", r"One way we can try to change our unwanted target behavior"),
]

# Items the rubric actually scores (order = report order).
H1_ITEMS = ["Q1", "Q2", "Q3", "Q4a", "Q4b", "Q4c", "Q5", "Q6"]

# Handout 2. Two structural differences from H1: the student's answer sits on
# the SAME line as the prompt label ("Example of Positive Reinforcement: ..."),
# so these markers are used with capture_tail=True; and three labels repeat
# (Definition / Daily Example / Weekly Example, once per chosen OC type),
# which the ordered marker walk resolves without needing distinct patterns.
#
# The typed submissions contain only this applied section — the 20 scenario
# items from the paper handout were never transcribed (0 of 20 files) and are
# ungraded in the gold workbook.
H2_MARKERS: list[tuple[str, str]] = [
    ("_utb", r"{{corpus:Q1/p3:response:0:27:sha=c8e59699d1a0:shape=C81008}} is"),
    ("_wgb", r"{{corpus:Q2/p3:response:0:23:sha=d743f1f68d1a:shape=C8408}} is"),
    ("PR", r"Example of Positive Reinforcement"),
    ("NR", r"Example of Negative Reinforcement"),
    ("PP", r"Example of Positive Punishment"),
    ("NP", r"Example of Negative Punishment"),
    # Loose on the trailing verb phrase: participant 9's transcription reads
    # "Second type of Operant Conditioning I pan to use".
    ("T1", r"First type of Operant Conditioning"),
    ("D1", r"^\W*Definition"),
    ("DAY1", r"^\W*Daily Example"),
    ("WK1", r"^\W*Weekly Example"),
    ("T2", r"Second type of Operant Conditioning"),
    ("D2", r"^\W*Definition"),
    ("DAY2", r"^\W*Daily Example"),
    ("WK2", r"^\W*Weekly Example"),
]

# Handout 3. Prose answers follow their prompts, but the DATA (1b) and the
# GRAPH (1c) live at the end of the document under "YOUR 1b." / "YOUR 1c."
# headings — after the template's own worked "EXAMPLE OF 1b." and
# "EXAMPLE OF 1c." sections, whose content is template text and is therefore
# subtracted. That subtraction is load-bearing here: participant 4 kept the
# template's example chart and nothing else, and the grader scored 1c at 0.
# Note the repeated ids: 1b's data can legitimately appear under the "1b."
# prompt (participant 16 rewrote the handout), under "EXAMPLE OF 1b."
# (participant 13 typed over the worked example), or under "YOUR 1b." — all
# three feed the same bucket, and template subtraction removes whatever of the
# worked example the student left behind. The Q3 pattern does not require the
# "3." prefix because participant 8's transcription dropped it.
H3_MARKERS: list[tuple[str, str]] = [
    # Tolerate "1.a" as well as "1a." — participant 16 rewrote the handout
    # with the dot inside the numbering.
    ("1a", r"^\W*1\W?a\b"),
    ("1b", r"^\W*1\W?b\b"),
    ("1c", r"^\W*1\W?c\b"),
    ("2a", r"^\W*2\W?a\b"),
    ("2b", r"^\W*2\W?b\b"),
    ("3", r"^\W*3[.)]|What could be done differently"),
    ("1b", r"EXAMPLE OF 1b"),
    # Whatever survives template subtraction between "EXAMPLE OF 1c." and
    # "YOUR 1c." is misplaced DATA, not a graph — participant 6 omitted the
    # "YOUR 1b." heading and typed their four weeks of data here.
    ("1b", r"EXAMPLE OF 1c"),
    ("1b", r"YOUR 1b"),
    ("1c", r"YOUR 1c"),
]

H3_ITEMS = ["1a", "1b", "1c", "2a", "2b", "3"]

H2_ITEMS = [
    "PR", "NR", "PP", "NP",
    "T1", "D1", "DAY1", "WK1",
    "T2", "D2", "DAY2", "WK2",
]

_UNDERSCORE = re.compile(r"_+")
_WS = re.compile(r"\s+")
_BULLET = re.compile(r"^[-•·*]\s*")


def clean(line: str) -> str:
    """Strip the template's underscore fill-rules from retained student text.

    Students typed onto the ruled lines, so answers arrive padded with long
    inline underscore runs. Two or more underscores are always rule, never
    content.
    """
    s = re.sub(r"_{2,}", " ", line)
    return _WS.sub(" ", s).strip()


def norm(line: str) -> str:
    s = _BULLET.sub("", line)
    s = _UNDERSCORE.sub(" ", s)
    s = _WS.sub(" ", s).strip().lower()
    return s


_NUMBERING = re.compile(r"^\W*\d+[a-c]?[.)]\s*")


def template_index(template_path: str) -> tuple[set[str], list[str], list[str]]:
    """Normalized template lines.

    Returns (exact set, long lines for fuzzy matching, stems). A "stem" is a
    template line with its leading item numbering removed: students sometimes
    type their answer onto the end of the question line, and the stem is what
    lets us cut the question off and keep only the answer.

    The template's own example CHART text is folded in as boilerplate too. Some
    submissions carry that chart as grouped shapes rather than a chart part, so
    its title and axis labels arrive as ordinary document text and would
    otherwise be read as the student's graph.
    """
    lines = [norm(ln) for ln in doc_lines(template_path)]
    kept = [ln for ln in lines if ln]
    try:
        from docx_text import graph_evidence

        for ch in graph_evidence(template_path)["charts"]:
            joined = norm("".join(ch["texts"]))
            if joined:
                kept.append(joined)
                for t in ch["texts"]:
                    if norm(t):
                        kept.append(norm(t))
    except Exception:
        pass
    stems = [_NUMBERING.sub("", ln) for ln in kept]
    stems = [st for st in stems if len(st) >= 25]
    # Several transcriptions collapse the template's example data onto one
    # line ("Sunday - 8 oz Monday - 10 oz ..."), which matches no single
    # template line. Concatenating the whole template lets a joined run be
    # recognised as a substring of it.
    blob = "".join(ln.replace(" ", "") for ln in kept)
    return set(kept), [ln for ln in kept if len(ln) >= 40], stems, blob


def strip_template_prefix(text: str, stems: list[str]) -> str:
    """Drop a leading template question from text the student appended to it.

    Participant 8's question-3 line is the whole printed prompt followed by
    their answer on the same line. Matching the prompt as a stem and cutting
    at its end leaves just the answer.
    """
    low = norm(text)
    best = ""
    for st in stems:
        if low.startswith(st) and len(st) > len(best):
            best = st
    if not best:
        return text
    return text[len(best):].lstrip(" :.–-\t")


def _is_boilerplate(nline: str, exact: set[str], longs: list[str], blob: str = "") -> bool:
    if nline in exact:
        return True
    # Transcription typos mean boilerplate is not always byte-identical.
    # Only fuzzy-match long lines; short student answers must never be eaten.
    if len(nline) >= 40:
        if difflib.get_close_matches(nline, longs, n=1, cutoff=0.88):
            return True
    squashed = nline.replace(" ", "")
    if blob and len(squashed) >= 30 and squashed in blob:
        return True
    return False


def segment(
    submission_path: str,
    template_path: str,
    markers: list[tuple[str, str]] = None,
    capture_tail: bool = False,
    join_aware: bool = False,
) -> dict[str, str]:
    """Return {item_id: student text} for one submission.

    capture_tail: keep whatever follows the marker on the marker's own line.
    Handout 2 needs this (answers are written inline after the label);
    Handout 1 must not use it (its marker lines carry only question prose).
    """
    markers = markers or H1_MARKERS
    compiled = [(item, re.compile(rx, re.I)) for item, rx in markers]
    # Tail-scan variants: several markers are anchored with ^\W* so they only
    # fire at the start of a line. When chasing a second label further along
    # the same line, that anchor has to come off or it can never match.
    tail_compiled = [
        (item, re.compile(rx[4:] if rx.startswith(r"^\W*") else rx, re.I))
        for item, rx in markers
    ]
    exact, longs, stems, blob = template_index(template_path)
    # Recognising a run of template lines collapsed onto one line is needed for
    # Handout 3's example data block, but it is too blunt for Handouts 1 and 2,
    # where it swallowed 628 characters of genuine student text.
    if not join_aware:
        blob = ""

    sections: dict[str, list[str]] = {item: [] for item, _ in markers}
    current: str | None = None
    next_marker = 0

    for raw in doc_lines(submission_path):
        line = raw.strip()
        if not line:
            continue
        # Advance through markers in order; allow skipping a missing one.
        advanced = False
        for idx in range(next_marker, len(compiled)):
            item, rx = compiled[idx]
            m = rx.search(line)
            if m:
                current = item
                next_marker = idx + 1
                advanced = True
                if capture_tail:
                    tail = line[m.end():]
                    # Strip the printed question from BOTH ends of the match, not
                    # just after it. A marker can fire INSIDE a question, and then
                    # what follows is the REST OF THE QUESTION rather than an
                    # answer — but the stem can no longer match it, because the
                    # marker just consumed the stem's opening words.
                    #
                    # Participant 8's handout 3 is the case. Their transcription
                    # dropped the "3." prefix, so the item-3 marker matched on
                    # "What could be done differently" instead, mid-stem. The tail
                    # began "next time to improve your behavior modification
                    # intervention plan? ..." — no stem starts there — so 320
                    # characters of printed question went into the section and
                    # every scorer read the question as p8's answer.
                    #
                    # Measuring from the WHOLE LINE finds the stem again. Any stem
                    # that matches is template text by construction, so taking
                    # whichever candidate removed the most is safe.
                    tail = min((tail,
                                strip_template_prefix(tail, stems),
                                strip_template_prefix(line, stems)), key=len)
                    # Two labels can share one line — participant 15 has
                    # "Second type of Operant Conditioning I plan to use:
                    # \t Definition:" with the answer on the line below. Keep
                    # consuming markers out of the tail so the text that
                    # follows lands on the right item.
                    while True:
                        nxt = None
                        for j in range(next_marker, len(tail_compiled)):
                            m2 = tail_compiled[j][1].search(tail)
                            if m2:
                                nxt = (j, m2)
                                break
                        if not nxt:
                            break
                        j, m2 = nxt
                        head = clean(tail[: m2.start()].lstrip(" :.–-"))
                        # What sits between two labels on one line is the rest
                        # of the first label ("I plan to use:"), not an answer.
                        # A real answer does not end in a colon, and text
                        # between two labels is often the rest of the printed
                        # question rather than anything the student wrote.
                        if (
                            head
                            and not head.endswith(":")
                            and not _is_boilerplate(norm(head), exact, longs, blob)
                        ):
                            sections[current].append(head)
                        current = compiled[j][0]
                        next_marker = j + 1
                        tail = tail[m2.end():]
                    rest = clean(tail.lstrip(" :.–-"))
                    # The tail of an untouched question line is just the rest of
                    # the printed question — drop it rather than scoring it.
                    if rest and not _is_boilerplate(norm(rest), exact, longs, blob):
                        sections[current].append(rest)
                break
        if advanced:
            continue
        if current is None:
            continue
        nline = norm(line)
        if not nline or _UNDERSCORE.fullmatch(raw.strip()):
            continue
        if _is_boilerplate(nline, exact, longs, blob):
            continue
        cleaned = clean(line)
        if cleaned:
            sections[current].append(cleaned)

    return {item: "\n".join(v).strip() for item, v in sections.items()}


def repair_orphans(
    sections: dict[str, str], order: list[str]
) -> tuple[dict[str, str], list[dict]]:
    """Move an answer typed ABOVE its label down to where it belongs.

    Participant 19 wrote their second daily example on the line above the
    "Daily Example:" label, leaving the label empty and the answer stranded at
    the end of the definition. Nothing in the marker ordering can recover that,
    because the text genuinely appears before its heading.

    The repair is deliberately narrow: it fires only when an item is EMPTY, the
    item immediately before it has more than one line, and that trailing line
    looks like a self-contained answer. Every repair is reported so the caller
    can flag the affected item for human review rather than trusting it
    silently.
    """
    repairs: list[dict] = []
    for prev_id, cur_id in zip(order, order[1:]):
        if sections.get(cur_id, "").strip():
            continue
        prev_lines = [l for l in sections.get(prev_id, "").split("\n") if l.strip()]
        if len(prev_lines) < 2:
            continue
        candidate = prev_lines[-1].strip()
        # A stranded answer is a sentence, not a fragment or a stray label.
        if len(candidate) < 30 or candidate.endswith(":"):
            continue
        sections[prev_id] = "\n".join(prev_lines[:-1]).strip()
        sections[cur_id] = candidate
        repairs.append({"moved_from": prev_id, "moved_to": cur_id, "text": candidate})
    return sections, repairs


def utb_hint(submission_path: str) -> str | None:
    """Formatting-marked UTB choice, when the transcription preserved it.

    Present in only 6 of 20 Handout 1 files, so this is a hint for the
    prompt, never a substitute for reading the UTB out of Q1's prose.
    """
    from docx_text import marked_runs

    choices = [
        "lack of sleep",
        "lack of exercise",
        "{{corpus:Q1/p12:response:31:69:sha=67aefa440274}} vegetables",
        "spending too much time on electronic devices",
    ]
    for txt in marked_runs(submission_path, lambda f: f["u"] or f["highlight"] or f["b"]):
        low = txt.strip().lower()
        for c in choices:
            if low.startswith(c[:18]):
                return c
    return None
