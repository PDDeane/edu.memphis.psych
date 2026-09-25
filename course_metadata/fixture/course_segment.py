#!/usr/bin/env python3
"""The COURSE half of segmentation. Goal N.

`segment.py` moved to the engine: 413 lines of which only these ~26 were about
THIS COURSE. What remains is the part that names the subject -- the four target
behaviours `utb_hint` looks for -- and the per-handout aliases, whose real value
is the REASONING in the comments below. That reasoning is course knowledge and
belongs with the course; the machinery it describes does not.

`_markers` and `_handout_items` are imported from the engine, which reads them
from the course file. Nothing is duplicated: these are the same objects under the
names seven modules have always used.

NOT A HOME FOR NEW ENGINE CODE. Anything added here that does not name this
course's subject matter is in the wrong directory, and goal N exists because that
had stopped being obvious.
"""
from segment import _handout_items, _markers   # the engine's, reading the course file

H1_MARKERS: list[tuple[str, str]] = _markers(1)

# Items the rubric actually scores (order = report order).
H1_ITEMS = _handout_items(1)

# Handout 2. Two structural differences from H1: the student's answer sits on
# the SAME line as the prompt label ("Example of Positive Reinforcement: ..."),
# so these markers are used with capture_tail=True; and three labels repeat
# (Definition / Daily Example / Weekly Example, once per chosen OC type),
# which the ordered marker walk resolves without needing distinct patterns.
#
# The typed submissions contain only this applied section — the 20 scenario
# items from the paper handout were never transcribed (0 of 20 files) and are
# ungraded in the gold workbook.
H2_MARKERS: list[tuple[str, str]] = _markers(2)

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
H3_MARKERS: list[tuple[str, str]] = _markers(3)

H3_ITEMS = _handout_items(3)

H2_ITEMS = _handout_items(2)

def utb_hint(submission_path: str) -> str | None:
    """Formatting-marked UTB choice, when the transcription preserved it.

    Present in only 6 of 20 Handout 1 files, so this is a hint for the
    prompt, never a substitute for reading the UTB out of Q1's prose.
    """
    from docx_text import marked_runs

    choices = [
        "lack of sleep",
        "lack of exercise",
        "insufficient consumption of fruits and vegetables",
        "spending too much time on electronic devices",
    ]
    for txt in marked_runs(submission_path, lambda f: f["u"] or f["highlight"] or f["b"]):
        low = txt.strip().lower()
        for c in choices:
            if low.startswith(c[:18]):
                return c
    return None
