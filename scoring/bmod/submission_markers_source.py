#!/usr/bin/env python3
"""The per-handout SUBMISSION LOCATORS, as authored -- a builder, outside the pipeline.

Category IX of `MATERIAL_CLASSIFICATION.md`: how a PAPER submission is taken
apart, which is neither course metadata nor a record of measurement. Split out of
`generator_source.py` on 2026-09-23, where it sat beside cross-scorer devices it
has nothing to do with.

These are read by `rubric_export.py` and exported course-level as
`generator.SEGMENT_MARKERS`, keyed by handout -- course-level because the ORDER is
load-bearing and the lists carry non-item keys, so no item entry can hold them.
`segment.py` consumes them from the exported file.

The `_H*_CTX` reference maps deliberately did NOT come with them. Those are
component-id -> item maps handed to the grader, which is a cross-scorer device
(category III); being per-handout is not the same as being about parsing.
"""
from __future__ import annotations


# ---------------------------------------------------------------------------
# STAGE 4, from `segment.py`. The per-handout LOCATORS: an ordered list of
# (key, regex) pairs matching the handout's own printed prose, by which a
# student answer is found inside a submission.
#
# ORDER IS LOAD-BEARING -- the segmenter walks them in sequence -- and the
# lists carry keys that are NOT items: `preamble` and `_q4_intro` in handout
# 1, `_utb` and `_wgb` in handout 2. So they are carried as ordered
# course-level lists and NOT folded onto item entries: an item entry cannot
# hold a position in a sequence it shares with non-items.
# ---------------------------------------------------------------------------
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

# Handout 2. Two structural differences from H1: the student's answer sits on
# the SAME line as the prompt label ("Example of Positive Reinforcement: ..."),
# so these markers are used with capture_tail=True; and three labels repeat
# (Definition / Daily Example / Weekly Example, once per chosen OC type),
# which the ordered marker walk resolves without needing distinct patterns.
#
# The typed submissions contain only this applied section — the 20 scenario
# items from the paper handout were never transcribed (0 of 20 files) and are
# ungraded in the gold workbook.
# THESE TWO ARE LITERALS ON PURPOSE, and were corpus references until 2026-09-22.
# They are the handout's OWN section headings -- authored text, in
# "Handout 2 - Scoring & Feedback Dictionary_.docx" -- and the history rewrite
# substituted them because a student had copied the heading verbatim, so the span
# matched. A marker is matched against the .docx as a LITERAL: `segment.py` does no
# reference resolution, so the substituted marker matched nothing, handout 2's box
# split fell back to the whole response, and `bmod_h1_utb` started carrying the
# student's entire Q1 answer instead of the extracted phrase. Nothing failed; the
# wrong text was simply fed to the model. Stage 08's frozen oracle caught it as a
# single moved sha (WK2), and restoring these two literals restores that sha
# exactly. A marker must never be a reference.
H2_MARKERS: list[tuple[str, str]] = [
    ("_utb", r"My Unwanted Target Behavior is"),
    ("_wgb", r"My Wanted Goal Behavior is"),
    ("PR", r"Example of Positive Reinforcement"),
    ("NR", r"Example of Negative Reinforcement"),
    ("PP", r"Example of Positive Punishment"),
    ("NP", r"Example of Negative Punishment"),
    # Loose on the trailing verb phrase: participant 9's transcription reads
    # [[corpus 3/p9 second 7:30 sha=1dadc902fe5c]].
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
