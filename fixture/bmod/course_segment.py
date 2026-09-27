#!/usr/bin/env python3
"""The COURSE half of segmentation. Goal N.

`segment.py` moved to the engine: 413 lines of which only these ~26 were about
THIS COURSE. What remains is the part that names the subject -- the four target
behaviours `utb_hint` looks for.

ONE HOOK, AND IT IMPORTS NOTHING FROM THE ENGINE. It used to also publish
`H1/H2/H3_MARKERS` and `H1/H2/H3_ITEMS`, aliases onto `segment._markers` and
`segment._handout_items` kept for "the names seven modules have always used".
Goal N had already moved every one of those modules onto `_markers(h)` directly,
so by 2026-09-25 the aliases had NO consumer anywhere -- and the import that fed
them is what broke this file. See below.

THE FAILURE THIS FILE RECORDS, 2026-09-25. E58 step 1 renamed
`segment._handout_items` to `_form_items`. This module's `from segment import
_handout_items, _markers` then raised ImportError at line 18 -- and
`segment.course_hook` catches ImportError and returns the default, because a
course that ships no hook is a real answer and not a failure. So `utb_hint`
became `lambda _path: None` for `score.py`, `score_h1.py` and `agreement_app.py`
at once, silently, and nothing failed. A rename in the engine turned off a
course's hook and no check said so.

Two things changed because of it: the dead aliases are gone, so this file
imports from the engine not at all; and `course_hook` now distinguishes "no such
module" from "the module is there and is broken", which is the part that
generalises.

NOT A HOME FOR NEW ENGINE CODE. Anything added here that does not name this
course's subject matter is in the wrong directory, and goal N exists because that
had stopped being obvious.
"""


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
