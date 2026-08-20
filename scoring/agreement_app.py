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
JOBS = {
    # Handout 1. `_utb_choice` resolves the closed ChoiceInput; a "split" pair is
    # fed from one paper block, which holds both entries the web version asks for.
    "Q1": {
        "handout": 1, "screen": f"{paths.NS}/bmod_h1_q1", "ns": paths.NS,
        "button": "Check my answer",
        "feedback": "bmod_h1_q1_feedback", "grader": "bmod_h1_q1_grader",
        "fields": {
                   "bmod_h1_utb": "_utb_choice",
                   "bmod_h1_q1_response": "Q1",
        },
        "split": {

        },
    },
    "Q2": {
        "handout": 1, "screen": f"{paths.NS}/bmod_h1_q2", "ns": paths.NS,
        "button": "Check my answer",
        "feedback": "bmod_h1_q2_feedback", "grader": "bmod_h1_q2_grader",
        "fields": {
                   "bmod_h1_utb": "_utb_choice",
                   "bmod_h1_q2_response": "Q2",
        },
        "split": {

        },
    },
    "Q4a": {
        "handout": 1, "screen": f"{paths.NS}/bmod_h1_q4a", "ns": paths.NS,
        "button": "Check my antecedents",
        "feedback": "bmod_h1_q4a_feedback", "grader": "bmod_h1_q4a_grader",
        "fields": {"bmod_h1_utb": "_utb_choice"},
        "from_scorer": {"bmod_h1_q4a_first": "antecedent_1",
                        "bmod_h1_q4a_second": "antecedent_2"},
    },
    "Q4c": {
        "handout": 1, "screen": f"{paths.NS}/bmod_h1_q4c", "ns": paths.NS,
        "button": "Check my consequences",
        "feedback": "bmod_h1_q4c_feedback", "grader": "bmod_h1_q4c_grader",
        "fields": {"bmod_h1_utb": "_utb_choice"},
        "from_scorer": {"bmod_h1_q4c_first": "consequence_1",
                        "bmod_h1_q4c_second": "consequence_2"},
    },
    "Q5": {
        "handout": 1, "screen": f"{paths.NS}/bmod_h1_q5", "ns": paths.NS,
        "button": "Check my answer",
        "feedback": "bmod_h1_q5_feedback", "grader": "bmod_h1_q5_grader",
        "fields": {"bmod_h1_utb": "_utb_choice"},
        "from_scorer": {"bmod_h1_q5_first": "example_1",
                        "bmod_h1_q5_second": "example_2",
                        "bmod_h1_q4c_first": "consequence_1",
                        "bmod_h1_q4c_second": "consequence_2"},
    },
    "Q6": {
        "handout": 1, "screen": f"{paths.NS}/bmod_h1_q6", "ns": paths.NS,
        "button": "Check my answer",
        "feedback": "bmod_h1_q6_feedback", "grader": "bmod_h1_q6_grader",
        "fields": {"bmod_h1_utb": "_utb_choice"},
        # The spans come from a CONSENSUS of ten CLI runs, frozen in a file, not
        # from whatever the last rescore happened to quote. The CLI's verdicts are
        # near-deterministic (156 of 160 slots unanimous across ten runs) but its
        # quotations are not (47% of spans move per rerun), and the fixture IS the
        # spans — so before this, two web runs one rescore apart were not
        # comparable. See q6_consensus.py for how the vote works and why the
        # slots are allowed to overlap.
        "consensus": str(paths.OUT / "q6_consensus" / "consensus.json"),
        # Eight components, eight boxes, NO splitting — and do not "fix" the
        # overlap between siblings. 36 of 117 filled boxes share text with a
        # sibling (`state_c1` and `affect_c1` are often one sentence, or one
        # inside the other) and that is FAITHFUL: a single sentence can both
        # name the consequence and say how it is affected, which is exactly what
        # this item's guidance tells the grader to allow ("PRESENCE IS NOT
        # WORDING"). Switching to the anchored split to remove the overlap
        # slices those sentences into fragments — p9's `affect_c1` became "With
        # this" — and took the item from 11/17 to 3/17, bias -0.13 to -0.94.
        # anchored_split's docstring was right: here the quote IS the answer.
        "from_scorer": {
            "bmod_h1_q6_state_a1": "state_a1", "bmod_h1_q6_change_a1": "change_a1",
            "bmod_h1_q6_state_c1": "state_c1", "bmod_h1_q6_affect_c1": "affect_c1",
            "bmod_h1_q6_state_a2": "state_a2", "bmod_h1_q6_change_a2": "change_a2",
            "bmod_h1_q6_state_c2": "state_c2", "bmod_h1_q6_affect_c2": "affect_c2",
        },
    },

    # Handout 2. Every item declares the same fallback: 7 of 20 transcriptions
    # leave this handout's restatement of the behaviour and goal empty, and
    # without them the model judges a contingency against a goal it cannot see.
    "PR": {
        "handout": 2, "screen": f"{paths.NS}/bmod_h2_pr_screen", "ns": paths.NS,
        "button": "Check my Positive Reinforcement example",
        "feedback": "bmod_h2_pr_feedback", "grader": "bmod_h2_pr_grader",
        "fields": {"bmod_h1_utb": "_utb", "bmod_h1_q2_response": "_wgb",
                   "bmod_h2_pr": "PR"},
        "fallback": {"_utb": (1, "Q1"), "_wgb": (1, "Q2")},
    },
    "NR": {
        "handout": 2, "screen": f"{paths.NS}/bmod_h2_nr_screen", "ns": paths.NS,
        "button": "Check my Negative Reinforcement example",
        "feedback": "bmod_h2_nr_feedback", "grader": "bmod_h2_nr_grader",
        "fields": {"bmod_h1_utb": "_utb", "bmod_h1_q2_response": "_wgb",
                   "bmod_h2_nr": "NR"},
        "fallback": {"_utb": (1, "Q1"), "_wgb": (1, "Q2")},
    },
    "PP": {
        "handout": 2, "screen": f"{paths.NS}/bmod_h2_pp_screen", "ns": paths.NS,
        "button": "Check my Positive Punishment example",
        "feedback": "bmod_h2_pp_feedback", "grader": "bmod_h2_pp_grader",
        "fields": {"bmod_h1_utb": "_utb", "bmod_h1_q2_response": "_wgb",
                   "bmod_h2_pp": "PP"},
        "fallback": {"_utb": (1, "Q1"), "_wgb": (1, "Q2")},
    },
    "NP": {
        "handout": 2, "screen": f"{paths.NS}/bmod_h2_np_screen", "ns": paths.NS,
        "button": "Check my Negative Punishment example",
        "feedback": "bmod_h2_np_feedback", "grader": "bmod_h2_np_grader",
        "fields": {"bmod_h1_utb": "_utb", "bmod_h1_q2_response": "_wgb",
                   "bmod_h2_np": "NP"},
        "fallback": {"_utb": (1, "Q1"), "_wgb": (1, "Q2")},
    },
    "D1": {
        "handout": 2, "screen": f"{paths.NS}/bmod_h2_d1_screen", "ns": paths.NS,
        "button": "Check my definition",
        "feedback": "bmod_h2_d1_feedback", "grader": "bmod_h2_d1_grader",
        "fields": {"bmod_h1_utb": "_utb", "bmod_h1_q2_response": "_wgb",
                   "bmod_h2_t1": "T1", "bmod_h2_t1": "T1",
                   "bmod_h2_d1": "D1"},
        "fallback": {"_utb": (1, "Q1"), "_wgb": (1, "Q2")},
    },
    "DAY1": {
        "handout": 2, "screen": f"{paths.NS}/bmod_h2_day1_screen", "ns": paths.NS,
        "button": "Check my daily example",
        "feedback": "bmod_h2_day1_feedback", "grader": "bmod_h2_day1_grader",
        "fields": {"bmod_h1_utb": "_utb", "bmod_h1_q2_response": "_wgb",
                   "bmod_h2_t1": "T1", "bmod_h2_d1": "D1",
                   "bmod_h2_day1": "DAY1"},
        "fallback": {"_utb": (1, "Q1"), "_wgb": (1, "Q2")},
    },
    "WK1": {
        "handout": 2, "screen": f"{paths.NS}/bmod_h2_wk1_screen", "ns": paths.NS,
        "button": "Check my weekly example",
        "feedback": "bmod_h2_wk1_feedback", "grader": "bmod_h2_wk1_grader",
        "fields": {"bmod_h1_utb": "_utb", "bmod_h1_q2_response": "_wgb",
                   "bmod_h2_t1": "T1", "bmod_h2_d1": "D1",
                   "bmod_h2_wk1": "WK1"},
        "fallback": {"_utb": (1, "Q1"), "_wgb": (1, "Q2")},
    },
    "D2": {
        "handout": 2, "screen": f"{paths.NS}/bmod_h2_d2_screen", "ns": paths.NS,
        "button": "Check my definition",
        "feedback": "bmod_h2_d2_feedback", "grader": "bmod_h2_d2_grader",
        "fields": {"bmod_h1_utb": "_utb", "bmod_h1_q2_response": "_wgb",
                   "bmod_h2_t2": "T2", "bmod_h2_t2": "T2",
                   "bmod_h2_d2": "D2"},
        "fallback": {"_utb": (1, "Q1"), "_wgb": (1, "Q2")},
    },
    "DAY2": {
        "handout": 2, "screen": f"{paths.NS}/bmod_h2_day2_screen", "ns": paths.NS,
        "button": "Check my daily example",
        "feedback": "bmod_h2_day2_feedback", "grader": "bmod_h2_day2_grader",
        "fields": {"bmod_h1_utb": "_utb", "bmod_h1_q2_response": "_wgb",
                   "bmod_h2_t2": "T2", "bmod_h2_d2": "D2",
                   "bmod_h2_day2": "DAY2"},
        "fallback": {"_utb": (1, "Q1"), "_wgb": (1, "Q2")},
    },
    "WK2": {
        "handout": 2, "screen": f"{paths.NS}/bmod_h2_wk2_screen", "ns": paths.NS,
        "button": "Check my weekly example",
        "feedback": "bmod_h2_wk2_feedback", "grader": "bmod_h2_wk2_grader",
        "fields": {"bmod_h1_utb": "_utb", "bmod_h1_q2_response": "_wgb",
                   "bmod_h2_t2": "T2", "bmod_h2_d2": "D2",
                   "bmod_h2_wk2": "WK2"},
        "fallback": {"_utb": (1, "Q1"), "_wgb": (1, "Q2")},
    },

    # ---- the last seven, each needing a split the two-way one cannot do ----
    "Q3": {
        "handout": 1, "screen": f"{paths.NS}/bmod_h1_q3", "ns": paths.NS,
        "button": "Check my SMART goal",
        "feedback": "bmod_h1_q3_feedback", "grader": "bmod_h1_q3_grader",
        "fields": {"bmod_h1_utb": "_utb_choice", "bmod_h1_q2_response": "Q2"},
        "from_scorer": {
            "bmod_h1_q3_specific": "specific",
            "bmod_h1_q3_measurable": "measurable",
            "bmod_h1_q3_action": "action_oriented",
            "bmod_h1_q3_realistic": "realistic",
            "bmod_h1_q3_timebound": "time_bound",
        },
        # Q3's aspects are discursive: the evidence quote is one sentence of a
        # longer answer, so it anchors a slice rather than replacing it.
        "anchored": True,
    },
    "Q4b": {
        "handout": 1, "screen": f"{paths.NS}/bmod_h1_q4b", "ns": paths.NS,
        "button": "Check my answer",
        "feedback": "bmod_h1_q4b_feedback", "grader": "bmod_h1_q4b_grader",
        "fields": {"bmod_h1_utb": "_utb_choice", "bmod_h1_q2_response": "Q2"},
        "split": {"Q4a": ("bmod_h1_q4a_first", "bmod_h1_q4a_second")},
        "handsplit": str(paths.HANDSPLIT / "Q4b.json"),
    },
    "1a": {
        "handout": 3, "screen": f"{paths.NS}/bmod_h3_overview", "ns": paths.NS,
        "button": "Check my overview",
        "feedback": "bmod_h3_overview_feedback", "grader": "bmod_h3_overview_grader",
        "fields": {"bmod_h3_overview_response": "1a"},
        # The four weekly boxes come from simulate_h3, which recovers what the
        # student would have typed from the chart they submitted.
        "sim": {"bmod_h3_baseline": "baseline", "bmod_h3_wk1": "week_1",
                "bmod_h3_wk2": "week_2", "bmod_h3_wk3": "week_3"},
    },
    "1c": {
        "handout": 3, "screen": f"{paths.NS}/bmod_h3_graph", "ns": paths.NS,
        "button": "Check my labelling",
        "feedback": "bmod_h3_graph_feedback", "grader": "bmod_h3_graph_grader",
        "fields": {},
        "fallback": {"_wgb": (1, "Q2")},
        # The four data fields are seeded as well as the three labels. 1c's sheet
        # gates on `has_own_graph`, which the web asks of the DATA — no numbers,
        # no chart — rather than of a submitted file. Leave them unseeded and
        # every cell gates to zero, which would read as a prompt collapse and is
        # not one. p18 (all four weeks absent) and p15 (baseline and week 3) are
        # the corpus rows where this actually fires; both are gold 0.
        # The legend comes from the reconstruction, not from `from_scorer`: the
        # scorer's `legend` evidence is a verdict in prose ("Legend element
        # present: True") for the chart-part rows, not the series names a
        # student would have typed. simulate_h3 recovers those literally.
        "sim": {"bmod_h3_baseline": "baseline", "bmod_h3_wk1": "week_1",
                "bmod_h3_wk2": "week_2", "bmod_h3_wk3": "week_3",
                "bmod_h3_graph_series": "graph_series"},
        "from_scorer": {"bmod_h3_graph_title": "title",
                        "bmod_h3_graph_x": "x_axis_label",
                        "bmod_h3_graph_y": "y_axis_label"},
    },
    "2a": {
        "handout": 3, "screen": f"{paths.NS}/bmod_h3_success", "ns": paths.NS,
        "button": "Check my answer",
        "feedback": "bmod_h3_success_feedback", "grader": "bmod_h3_success_grader",
        "fields": {"bmod_h3_overview_response": "1a"},
        "from_scorer": {"bmod_h3_success_verdict": "verdict",
                        "bmod_h3_success_how1": "how_1",
                        "bmod_h3_success_how2": "how_2"},
    },
    "2b": {
        "handout": 3, "screen": f"{paths.NS}/bmod_h3_assessment", "ns": paths.NS,
        "button": "Check my assessment",
        "feedback": "bmod_h3_assessment_feedback", "grader": "bmod_h3_assessment_grader",
        "fields": {"bmod_h3_assessment_response": "2b",
                   "bmod_h2_t1": "_t1", "bmod_h2_t2": "_t2"},
        # The types the student chose are in Handout 2, which this item asks them
        # to reflect on; `_t1`/`_t2` exist only to be filled from there.
        "fallback": {"_t1": (2, "T1"), "_t2": (2, "T2")},
    },
    # Three items whose every verdict is DERIVED from the student's fields, so
    # there is no prompt, no button and no LLM call: DerivedChecks publishes the
    # sheet as soon as the fields are seeded and SlotSheetGrader scores it. They
    # are deterministic, which is why they are worth having in the corpus —
    # whatever they measure, they measure the same way every run.
    #
    # All three were scored on the CLI and by nothing on the web until now.
    "T1": {
        "handout": 2, "screen": f"{paths.NS}/bmod_h2_first", "ns": paths.NS,
        "feedback": "bmod_h2_t1_checks", "grader": "bmod_h2_t1_sheet_grader",
        "fields": {"bmod_h2_t1": "_type_choice:T1"},
    },
    "T2": {
        "handout": 2, "screen": f"{paths.NS}/bmod_h2_second", "ns": paths.NS,
        "feedback": "bmod_h2_t2_checks", "grader": "bmod_h2_t2_sheet_grader",
        "fields": {"bmod_h2_t2": "_type_choice:T2"},
    },
    # The same four data fields 1c seeds, from the same reconstruction — 1b scores
    # their presence and 1c gates on whether they plot at all.
    "1b": {
        "handout": 3, "screen": f"{paths.NS}/bmod_h3_data", "ns": paths.NS,
        "feedback": "bmod_h3_data_checks", "grader": "bmod_h3_data_grader",
        "fields": {},
        "sim": {"bmod_h3_baseline": "baseline", "bmod_h3_wk1": "week_1",
                "bmod_h3_wk2": "week_2", "bmod_h3_wk3": "week_3"},
    },
    "3": {
        "handout": 3, "screen": f"{paths.NS}/bmod_h3_improve", "ns": paths.NS,
        "button": "Check my answer",
        "feedback": "bmod_h3_improve_feedback", "grader": "bmod_h3_improve_grader",
        "fields": {},
        "from_scorer": {"bmod_h3_improve_first": "example_1",
                        "bmod_h3_improve_second": "example_2"},
    },
}

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


_ANNOTATED = re.compile(r'^\s*["“](?P<q>.+?)["”]\s*(?:[—–]|--)\s*\S')


def _quoted_span(ev: str) -> str:
    """A quote the scorer annotated, reduced to the quote.

    Matches only `"…" — prose`: an em/en dash AFTER a closing quote mark. A
    hyphen inside the student's own words, or a dash with no quotes around the
    span, is left alone — the aim is to drop the scorer's commentary, not to
    reformat what the student wrote.
    """
    m = _ANNOTATED.match(ev or "")
    return m.group("q").strip() if m else (ev or "").strip()


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

    It also sometimes annotates a real quote: `"{{corpus:Q6/p9:affect_c1:10:55:sha=c168024a17ed:shape=S5-0a20202020,A12}} health" — loosely worded, but this is the 4c
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
CONSENSUS_FIXES: dict[tuple[str, int], list[tuple]] = {
    # p4 wrote antecedent-1 -> change -> consequence, then antecedent-2 ->
    # change -> consequence. The consensus put the FIRST pair's consequence in
    # the c2 boxes (document positions 157 and 219) and the SECOND pair's in the
    # c1 boxes (both at 389), inverting both pairs. Nothing is dropped or
    # duplicated; the two clauses are simply exchanged, which scrambles exactly
    # the antecedent-to-consequence linkage the affect_c* rules judge.
    # p4 writes part 1 in three clauses and part 2 in two, and the consensus
    # respected neither. `state_c1` held "{{corpus:Q6/p4:affect_c1:91:128:sha=f850fdd69cda:shape=A5}}
    # o I" — a slice from the MIDDLE of part 1's last sentence plus the two
    # characters that open part 2. `affect_c1` began mid-phrase at "be happier",
    # orphaning "which I hope will help me to". `state_a2` stopped at "that leads
    # to me not", orphaning "{{corpus:Q6/p4:state_a1:74:104:sha=2eb26cbe281f}}" — the same asymmetry
    # as p5, where state_a1 runs through its parallel clause and state_a2 does
    # not. Fourteen words belonged to no box, both stretches mid-sentence cuts
    # rather than the connectives a clause split rightly discards.
    #
    #   part 1  @0    antecedent   @105 change   @127 consequence   @157 effect
    #   part 2  @259  antecedent   @367 change   @389 consequence AND effect
    #
    # Part 2's c-boxes share one sentence because the student wrote only one
    # there; that is the permitted same-element overlap, not a duplication.
    # Q6/p2. `change_a1` stopped at "... {{corpus:Q6/p2:change_a1:145:170:sha=751334d2741e}} to", and the
    # rest of its own sentence — "{{corpus:Q6/p2:change_a1:174:215:sha=9feaaabd7986}}
    # myself." — belonged to NO box. It carried a structure override saying the
    # phrase was complete and that extending it would swallow the next sentence.
    # The phrase does read complete, because "to" there is a phrasal particle,
    # but the sentence does not end at it. Runs to its own full stop now, ending
    # at 307 where affect_c1 starts at 308.
    ("Q6", 2): [
        ("set", "change_a1",
         "{{corpus:Q6/p2:change_a1:0:63:sha=1bdb608deca1:shape=R63-0-20}}"
         "{{corpus:Q6/p2:change_a1:64:131:sha=a2940b547306:shape=R67-0-20}}"
         "{{corpus:Q6/p2:change_a1:132:201:sha=a50555046df8:shape=R69-0-20}}"
         "{{corpus:Q6/p2:change_a1:202:215:sha=03b8580b37c4}} myself."),
    ],

    # 2a/p1. how1 swallowed BOTH explanations — the sleep/patience one and the
    # physical-health one — leaving how2 empty. Two distinct HOWs, two boxes.
    ("2a", 1): [
        ("set", "how1",
         "{{corpus:2a/p1:how1:0:72:sha=f985dc5d569d}} getting."),
        ("set", "how2",
         "{{corpus:2a/p1:how2:0:155:sha=630d660099b1}} bit."),
    ],
    # 2a/p5. how1 began mid-sentence at "{{corpus:2a/p5:how1:78:102:sha=1a189475cd71}} slip", dropping the
    # clause it depends on. Restored to the whole sentence.
    ("2a", 5): [
        ("set", "how1",
         "{{corpus:2a/p5:how1:0:149:sha=37d5a4ba7e65}} burnout."),
    ],
    # 2a/p15. how1 held both explanations and how2 was empty, same shape as p1.
    ("2a", 15): [
        ("set", "how1",
         "{{corpus:2a/p15:how1:0:24:sha=76aa568a019e}} screentime."),
        ("set", "how2",
         "{{corpus:2a/p15:how2:0:50:sha=fbc7eed7d0f0}} unreasonable."),
    ],
    # 2a/p16. p16 labels its own sentences ("Sentence 1:", "Sentence 2:"). how1 held a
    # string that appears NOWHERE in the response — sentence 1's label welded to
    # sentence 2's text. Set to sentence 2 with the label stripped.
    ("2a", 16): [
        ("set", "how1",
         "{{corpus:2a/p16:how1:0:61:sha=4cbf58cc2e12}} exercise."),
    ],
    # Q4a/p10. `second` dropped part 2's closing clause ("{{corpus:Q4a/p10:second:117:146:sha=ee9ee342783a}}
    # the day ..."). A numbered part keeps all of its own clauses.
    ("Q4a", 10): [
        ("set", "second",
         "{{corpus:Q4a/p10:second:0:187:sha=b0c29b343081}} sorts."),
    ],
    # Q4a/p17. `first` dropped part 1's second sentence, same rule.
    ("Q4a", 17): [
        ("set", "first",
         "{{corpus:Q4a/p17:first:0:114:sha=dd1ff58cb34f}} ."),
    ],
    # Q5/p11. both boxes truncated: `first` lost part 1's third sentence, `second` was cut
    # mid-clause at "recover from stress". Each part keeps all three of its clauses.
    ("Q5", 11): [
        ("set", "first",
         "{{corpus:Q5/p11:first:0:370:sha=99b69bed3aea}} health."),
        ("set", "second",
         "{{corpus:Q5/p11:second:0:370:sha=cec57960c613}} term."),
    ],
    # 2a/p18 is NOT fixed here, and the reason is worth keeping. This entry
    # once set `verdict` to "The behavior modification plan was successful."
    # That sentence is the first line of the TEMPLATE'S WORKED EXAMPLE, which
    # p18 copied verbatim; `join_aware` strips it as boilerplate, exactly as it
    # is meant to. The fix was made while the audit was reading segments WITHOUT
    # join_aware, so the example text was still sitting in the response and read
    # as the student's own verdict — putting template prose into a scored box.
    #
    # What remains is a real disagreement, not a fixture defect. Gold gives this
    # cell a full 6.0, crediting the copied sentence the grader saw on paper.
    # After template subtraction no verdict survives, so the paper scorer quotes
    # the nearest thing — which is how1's sentence, and why `verdict` and `how1`
    # overlap. Whether that makes the cell unscoreable is a SCORING decision.

    # Q4b/p7. The student numbers two items: (1) a statement that the behaviour
    # {{corpus:Q4b/p7:modify:21:38:sha=1fa4115cf4a6}}, with its reason, and (2) procrastinating. The hand-split
    # cut item 1 in half — `modify` held only "... {{corpus:Q4b/p7:modify:69:89:sha=45cb42b10e1e}}
    # aggravated", with a full stop the student never wrote — leaving "which
    # {{corpus:Q4b/p7:modify:107:153:sha=b6c67146a35f}} ..." in no box and `first`
    # empty while `second` held item 2.
    #
    # Gold is 2.0, "-3 pts: did not provide two examples", so the grader read ONE
    # example. Reading item 1 as the modify statement and item 2 as that single
    # example assigns every word, respects the clause boundaries, and agrees with
    # the grader's own count. The alternative — splitting item 1 at "which" to
    # manufacture a first example — cuts mid-clause and credits two examples
    # where gold says one.
    ("Q4b", 7): [
        ("set", "modify",
         "{{corpus:Q4b/p7:modify:0:70:sha=6d171dcec2d9:shape=R70-0-20}}"
         "{{corpus:Q4b/p7:modify:71:137:sha=db967def76a1:shape=R66-0-20}}"
         "{{corpus:Q4b/p7:modify:138:181:sha=686b5b1951e4}} games."),
        ("set", "first",
         "{{corpus:Q4b/p7:first:0:71:sha=d0272f38969d:shape=R71-0-20}}"
         "{{corpus:Q4b/p7:first:72:136:sha=fb887340238d:shape=R64-0-20}}"
         "{{corpus:Q4b/p7:first:137:188:sha=9f0220144fbe}} handle."),
        ("set", "second", ""),
    ],

    # --- EXTENDS, worked cell by cell -------------------------------------
    # p8: change_a2 stopped at "... some progress in the". The response ends
    # "... in the near future." and nothing competes for the tail.
    #
    # The consequence boxes stay EMPTY, and the attempt to fill them is recorded
    # because the reasoning for it was half right and the measurement settled it.
    #
    # Two clauses sit in no box — "Which then makes me wish I would have just
    # gone to the gym, since at times I feel super unmotivated ..." and "which
    # can lead to {{corpus:Q1/p8:response:206:236:sha=a6fc82d76be7}}" They were assigned to state_c1
    # and state_c2 on the argument that an empty box makes the FIXTURE do the
    # scoring: the scorer's evidence read "There is no text in this box", so it
    # was reporting an absence rather than judging the student, and it landed on
    # gold's own answer for the wrong reason.
    #
    # MEASURED, and reverted. The prediction was that both clauses would read
    # `mismatch` — same score, better reasoning. Instead state_c1 came back `met`
    # with refers_to `second`, matching "I feel super unmotivated" to 4c's "0
    # motivation to do anything", in all three runs. p8 went +2.50 -> +3.75: its
    # error had been EXACTLY the declared A_NO_CHANGE divergence, and the
    # assignment added a second, undeclared disagreement.
    #
    # Gold's wording is the reason the empty boxes are right after all: "-5 pts:
    # did not state each consequence being affected AND how it is being affected
    # by changing your antecedents" — one bundled deduction over all four slots.
    # Both clauses hang off the ANTECEDENT sentences and describe what the
    # current behaviour leads to; neither says what becomes of a consequence once
    # the antecedent changes. `state_c*` asks for the consequence BEING AFFECTED,
    # so this text does not belong in it. Wrong text in the box is a worse fault
    # than a right score for a thin reason.
    ("Q6", 8): [
        ("set", "change_a2",
         "{{corpus:Q6/p8:change_a2:0:70:sha=ce49c79fb729:shape=R70-0-20}}"
         "{{corpus:Q6/p8:change_a2:71:139:sha=20b00a0f9360:shape=R68-0-20}}"
         "{{corpus:Q6/p8:change_a2:140:148:sha=d4b9d02da030}} future."),
    ],

    # p19 is ONE sentence describing ONE pair, and the student labelled every
    # element themselves: "(orig A) ... (newA), {{corpus:Q6/p19:state_c1:0:31:sha=7f5d158a453a}}
    # all day.(C) {{corpus:Q6/p19:affect_c1:0:31:sha=73a34551a5b2}} ... assignments(New C)."
    #
    # JUDGEMENT, not a mechanical repair. "(New C)" marks the NEW consequence
    # after the change, not a SECOND one, and there is no second antecedent
    # anywhere — so the c2 boxes were holding pieces of the first pair's
    # narrative. Emptying them says the student addressed one pair, which is
    # what gold says too ("-5 pts: did not address your second antecedent being
    # changed and how it will affect your second consequence"). state_c1 gives
    # back the "Instead, I" it took from the following clause, and affect_c1
    # runs to the end of the sentence it owns.
    ("Q6", 19): [
        ("set", "state_c1", "{{corpus:Q6/p19:state_c1:0:35:sha=f8a81a5a2a8b}} day.(C)"),
        ("set", "affect_c1",
         "{{corpus:Q6/p19:affect_c1:0:68:sha=fb43b827cf3f:shape=R68-0-20}}"
         "{{corpus:Q6/p19:affect_c1:69:129:sha=63dc060d6f65}} C)."),
        ("set", "state_c2", ""),
        ("set", "affect_c2", ""),
    ],

    # p18's c2 boxes were in the WRONG HALF of the response. Both held slices
    # of part one's consequence sentence — state_c2 "{{corpus:Q6/p18:affect_c1:97:118:sha=62c32824db1c}}
    # guilty.", affect_c2 "{{corpus:Q6/p18:affect_c1:26:66:sha=698264b8d1ee}} ..." — while
    # part two's own consequence sentence, at @464, belonged to no box at all.
    # That is the p5 defect again, and it is what generated all four of this
    # cell's cross-element overlap findings.
    #
    #   part 2  @296 change   @403 antecedent   @464 consequence
    #
    # It also explains the scoring. p18's 4c second consequence is "personal
    # dissatisfaction and guilt", and part one's sentence contains "guilty", so
    # the borrowed text was being credited. The student's actual part-two
    # sentence names focus and a SMART goal, not that consequence — which is
    # what the graders charged ("-2.5 pts: did not address how the second
    # consequence is being affected"). state_c2 and affect_c2 share the sentence
    # as the permitted same-element overlap, since that is all part two has.
    #
    # REVISED: both consequence pairs now put the sentence in the NAMING box and
    # leave the fate box blank. Each part of this response has exactly one
    # consequence sentence, so sharing it left the scorer unable to reproduce
    # gold's asymmetry — gold charges affect_c2 ALONE, and with the same words in
    # both boxes the scorer accepts or refuses them together. It reached gold's
    # 7.50 by refusing state_a2 and state_c2 while crediting the affect_c2 gold
    # refuses: two errors cancelling.
    #
    # Blanking the fate boxes discards no text — the sentence stays whole in the
    # naming box. Neither part says what BECOMES of a 4c consequence; both name an
    # improved state ("feeling energized", "able to focus"), which is why gold's
    # only charge is that the second consequence's fate went unaddressed. Same
    # treatment as p15.
    ("Q6", 18): [
        ("set", "change_a2",
         "{{corpus:Q6/p18:change_a2:0:52:sha=149c6db4cf7a}} \"Do Not "
         "Disturb\" {{corpus:Q6/p18:change_a2:70:101:sha=bc939cf835e6}} time"),
        ("set", "state_c1",
         "{{corpus:Q6/p18:affect_c1:0:69:sha=b7680b96169b:shape=R69-0-20}}"
         "{{corpus:Q6/p18:affect_c1:70:118:sha=c348538a114c}} guilty."),
        # affect_c1 KEEPS the sentence, shared with state_c1: gold CREDITS it.
        # p18's two consequence pairs are not the same case — gold charges the
        # SECOND pair's fate alone ("-2.5 pts" = state_c2 + affect_c2) — so
        # blanking affect_c1 here cost 1.25 gold awards. Measured 5.00 x3 before
        # this was put back. S2 earns both slots honestly: "tired and guilty"
        # echoes 4c's two consequences, and "{{corpus:Q6/p18:affect_c1:26:54:sha=fba019c56f62}}
        # consequence" is the fate.
        ("set", "affect_c1",
         "{{corpus:Q6/p18:affect_c1:0:69:sha=b7680b96169b:shape=R69-0-20}}"
         "{{corpus:Q6/p18:affect_c1:70:118:sha=c348538a114c}} guilty."),
        ("set", "state_c2",
         "{{corpus:Q6/p18:state_c2:0:68:sha=997397aa6e54:shape=R68-0-20}}"
         "{{corpus:Q6/p18:state_c2:69:99:sha=3aa7aa7e32e3}} eliminated."),
        ("set", "affect_c2", ""),
    ],

    # p10, made symmetric with its own part one. The student writes two parts,
    # and part one assigns cleanly: change_a1 spans S1+S2 (the change AND its
    # immediate result), state_c1/affect_c1 share S3 (the consequence). Part two
    # did not follow: change_a2 held only S1, state_c2 held a slice of PART
    # ONE's S1, and part two's S2 and S3 belonged to nothing.
    #
    #   part 1  S1+S2 -> change_a1     S3 -> state_c1 = affect_c1
    #   part 2  S1+S2+S3 -> change_a2  S4 -> state_c2 = affect_c2
    #
    # An earlier attempt put part two's S2 ("reduce {{corpus:Q6/p10:change_a2:23:49:sha=865ea5a35836}}
    # confidence") into state_c2 and measured 8.75 -> 6.25. That was the wrong
    # clause: by symmetry with part one, S2 belongs with the CHANGE, and the
    # consequence box takes the part's last sentence. 4c's second consequence is
    # "{{corpus:Q4c/p10:second:81:108:sha=94a4a51d6d09}} laziness", which S4's "healthier lifestyle
    # {{corpus:Q6/p10:affect_c2:38:75:sha=cfeee219cbf2}} myself" answers and S2 does not.
    #
    # REVISED, and the earlier arrangement above is what it revises. The antecedent
    # boxes now take one sentence each instead of the state box holding a fragment
    # of the change box's first sentence:
    #
    #   part 1  S1 -> state_a1   S2 -> change_a1
    #   part 2  S4 -> state_a2   S5+S6 -> change_a2
    #
    # The consequence repairs below are unchanged and load-bearing: without them
    # state_c1 begins at "hoping", orphaning "I\u2019m", and runs on to grab the
    # "2) I" opening part two, while state_c2 holds a slice of PART ONE.
    ("Q6", 10): [
        ("set", "state_a1",
         "1)_{{corpus:Q6/p10:state_a1:0:67:sha=e25cf240879f:shape=R67-0-20}}"
         "{{corpus:Q6/p10:state_a1:68:85:sha=1ff750d0f1df}}"),
        ("set", "change_a1",
         "{{corpus:Q6/p10:change_a1:0:67:sha=33f7fe95bc26:shape=R67-0-20}}"
         "{{corpus:Q6/p10:change_a1:68:92:sha=2aa25fc09046}}"),
        ("set", "state_a2",
         "2) {{corpus:Q6/p10:state_a2:0:65:sha=905fbe44a231:shape=R65-0-20}}"
         "{{corpus:Q6/p10:state_a2:66:91:sha=d91508197d5c}}"),
        ("set", "change_a2",
         "{{corpus:Q6/p10:change_a2:0:67:sha=1cb11948717a:shape=R67-0-20}}"
         "{{corpus:Q6/p10:change_a2:68:117:sha=1a05fb62a163}} steps."),
        ("set", "state_c1",
         "{{corpus:Q6/p10:affect_c1:0:66:sha=2c56a52bac2d:shape=R1-1-5c7532303139,R66-0-20}}"
         "{{corpus:Q6/p10:affect_c1:67:78:sha=ddfeab4b3e20}}"),
        ("set", "affect_c1",
         "{{corpus:Q6/p10:affect_c1:0:66:sha=2c56a52bac2d:shape=R1-1-5c7532303139,R66-0-20}}"
         "{{corpus:Q6/p10:affect_c1:67:78:sha=ddfeab4b3e20}}"),
        ("set", "state_c2",
         "{{corpus:Q6/p10:affect_c2:0:69:sha=511126de9f44:shape=R69-0-20}}"
         "{{corpus:Q6/p10:affect_c2:70:83:sha=4140a87a0a04}}"),
    ],

    # --- TRIMS -------------------------------------------------------------
    # Nine boxes that had taken the HEAD of the following sentence. Where a box
    # ends "... flexibility. To" or "... physically. 2) I", the response says
    # unambiguously where the boundary goes: cut at the stop, and the head
    # belongs to whichever box owns that sentence. Verified as a set — structure
    # mismatches 14 -> 6 with overlaps and coverage unchanged.
    #
    # The opposite direction is NOT mechanical and is not done here. Where a box
    # stops mid-clause, how far it should reach is a judgement about which box
    # owns the rest: extending them all cleared the remaining six mismatches and
    # created two new OVERLAPS, swallowing clauses their neighbours hold.
    # p6: both antecedent boxes grabbed the "To" that opens "To do that, I will
    # make it mandatory ..."; change_a1 already begins there
    #
    # The change boxes are split at "while", a clause boundary. `change_a2` used
    # to hold "{{corpus:Q6/p6:change_a1:12:36:sha=4f2bd88df1ea}} ... {{corpus:Q6/p6:change_a1:75:93:sha=d808b781e5fa:shape=R18-0-22}} — a strict
    # SUBSTRING of `change_a1`, which held the whole sentence — and both were
    # credited: 2.5 points for one commitment. `cover` cannot catch that. The
    # sheet declares cover="state_a1,state_a2:first,second|state_c1,state_c2:
    # first,second", so it governs the STATE slots only; state_a2's duplicate IS
    # demoted, the change duplicate is not, and p6 landed on gold's 6.25 with a
    # slot right for the wrong reason.
    #
    # The sentence carries two commitments, one per trigger, and 4a names them:
    # "not stretching" is the FIRST trigger, "{{corpus:Q4a/p6:second:21:56:sha=98e4d82db22b}}
    # days" the second. So the stretching clause answers a1 and the gym clause
    # answers a2 — which is what state_a1's `refers_to: first` says too. The
    # opening adjunct "To do that," goes with the main clause it modifies, which
    # is change_a2's; leaving it stranded pushed the unassigned run over the
    # coverage check's threshold for no reason a reader could act on.
    ("Q6", 6): [
        # S1 split at the ampersand, S2 split at "while", so each element carries
        # its own trigger and its own change: a1 is the gym, a2 is stretching.
        #
        # state_a2 prepends "not", the one non-verbatim word in the corpus. The
        # response reads "{{corpus:Q6/p6:state_a1:0:21:sha=641b355f6e09}} & {{corpus:Q6/p6:state_a2:4:35:sha=b9b20440de98}}
        # be" — a single negation heading the conjunction — so the stretching half
        # cannot carry it without being written out. Distributing it is what the
        # sentence means, and leaving it off would make the box read as a positive.
        #
        # The point of the split is to let the RIGHT mechanism produce gold's 6.25.
        # 4a lists "not stretching" and "not being motivated"; "not attending the
        # gym" is on neither list — it is what the motivation trigger CAUSES. So
        # state_a1 should answer `refers_to: none` and be demoted, which is gold's
        # own reason ("second antecedent is not the same as mentioned in 4a"),
        # rather than the identical-text collision that produced the right total by
        # accident.
        # MEASURED ALTERNATIVE, rejected 2026-08-18. Collapsing this back into one
        # box -- the whole conjunction verbatim in state_a1, state_a2 EMPTY, the
        # change boxes untouched -- was tried because it invents no word and needs
        # no reading of gold's ordinals. It scored 3.75, 3.75, 5.00 against gold's
        # 6.25: a regression in all three passes.
        #
        # The cause is worth more than the result. Emptying state_a2 cost BOTH
        # CHANGE SLOTS, not just the naming slot it emptied: with no second
        # antecedent named, "while stretching daily" has nothing to be the change
        # TO, and change_a1 went with it in two passes of three. The slots are not
        # independent -- a naming slot is load-bearing for the change slot beside
        # it, and emptying one box silently reprices two others. Any future fixture
        # change that empties a naming box should expect to lose its change box as
        # well, and predictions that treat slots as separable (mine did) will be
        # wrong in the same direction.
        ("set", "state_a1", "{{corpus:Q6/p6:state_a1:0:21:sha=641b355f6e09}}"),
        ("set", "change_a1",
         "{{corpus:Q6/p6:change_a1:0:68:sha=45cb3b4751e5:shape=R68-0-20}}"
         "{{corpus:Q6/p6:change_a1:69:93:sha=521aae91343f}}"),
        ("set", "state_a2", "{{corpus:Q6/p6:state_a2:0:35:sha=a504671fd814}} be"),
        ("set", "change_a2", "while stretching daily."),
    ],
    # p9: both consequence boxes grabbed "Instead I hope I", the head of the next
    # sentence, which affect_c1's own span already covers
    # p9 is one pair, like p19. The trailing "{{corpus:Q6/p9:affect_c1:64:94:sha=9a0c693733bf}}
    # {{corpus:Q6/p9:affect_c1:95:130:sha=6fd00b4d8d14}}" is the EFFECT on the first
    # consequence, not a second consequence — and gold says so outright:
    # "missing second consequences". state_c2 was holding it while affect_c1 held
    # only a slice of state_c1's sentence. Caught by
    # check_fixture_agrees_with_gold; the other four checks passed it.
    ("Q6", 9): [
        ("set", "state_c1",
         "{{corpus:Q6/p9:affect_c1:0:55:sha=ee60f3a47798:shape=R22-1-5c7532303139}} health."),
        # affect_c1 must carry the clause that says what BECOMES of the
        # consequence, and in this response that clause is inseparable from the
        # naming: "{{corpus:Q6/p9:affect_c1:10:55:sha=c168024a17ed:shape=A12}} health" states
        # the consequence and its fate in one breath. Given only the sentence
        # after it, the scorer answered `incomplete` — correctly, since "I will
        # get more motivated" names a NEW state rather than the fate of the old
        # one — and lost a slot gold credits. state_c1 and affect_c1 are
        # siblings, so one clause answering both is expected and the overlap
        # check exempts it.
        ("set", "affect_c1",
         "{{corpus:Q6/p9:affect_c1:0:63:sha=d7be8ab0f600:shape=R22-1-5c7532303139,R63-0-20}}"
         "{{corpus:Q6/p9:affect_c1:64:120:sha=abe47e0087a3}} progress."),
        ("set", "state_c2", ""),
        ("set", "affect_c2", ""),
    ],
    # p11: state_c1 ran into "{{corpus:Q6/p11:affect_c1:0:41:sha=9d084f037499}} ...", which
    # affect_c1 already holds in full
    ("Q6", 11): [
        ("set", "state_c1",
         "{{corpus:Q6/p11:state_c1:0:62:sha=1c7a5865b73a:shape=R62-0-20}}"
         "{{corpus:Q6/p11:state_c1:63:115:sha=708d51f16f11}} C)."),
    ],
    # p15's first-consequence pair came out of the consensus table holding ONE
    # sentence twice: state_c1 the whole of "{{corpus:Q6/p15:state_c1:0:35:sha=0d180e4ace72}}
    # {{corpus:Q6/p15:state_c1:36:92:sha=e26fd1bbd69d}}" and affect_c1 the
    # same minus its lead-in. Not a split error — the paper scorer was asked which
    # consequence is affected and how, had only that sentence to answer either
    # with, and quoted it for both. state_c1 and affect_c1 are siblings, so the
    # checks permit the sharing and nothing flagged it.
    #
    # It made gold's judgement unreachable. Gold credits the naming and refuses the
    # fate — "did not clarify the first consequence being affected" — which the
    # scorer cannot reproduce when both boxes show it the same words: it accepts or
    # refuses them as a unit.
    #
    # The sentence is a conjunction of two improved states, so it splits at "and"
    # and each box gets its own. Both halves verbatim, cut at a non-sentence
    # boundary.
    ("Q6", 15): [
        # Whole sentence in state_c1, affect_c1 blank: the student names improved
        # states and never says what becomes of a 4c consequence, so the fate box
        # has nothing of its own to hold.
        ("set", "state_c1",
         "{{corpus:Q6/p15:state_c1:0:66:sha=42e9bded9635:shape=R66-0-20}}"
         "{{corpus:Q6/p15:state_c1:67:86:sha=e46fcab93ee4}} time."),
        ("set", "affect_c1", ""),
    ],

    # p14 lays out as four sentences, two pairs: S1 antecedent+change, S2 the first
    # consequence and its fate, S3 the second antecedent+change, S4 the second
    # consequence and its fate. Each c-box takes the sentence that answers it;
    # state and affect of one element are siblings, so sharing a sentence is
    # expected and the overlap check exempts it.
    #
    # An earlier fix left three faults here, and its comment justified only the
    # first. `affect_c1` KEPT "{{corpus:Q6/p14:change_a1:63:82:sha=2db206dd72e6}}" — the tail of S1, which
    # change_a1 also holds, so two different elements shared it. `state_c1` began
    # mid-word at "more(WGB)". Worst, `affect_c2` was set to "not be that severe.",
    # a 19-character fragment sliced off the END OF S3 — part of change_a2's own
    # sentence — while S4, which actually states what becomes of the second
    # consequence, sat wholly in state_c2. Shown that fragment the scorer answered
    # `incomplete`, which is right about the box and wrong about the student, and
    # it cost p14 the 1.25 that gold awards.
    #
    # Both overlaps escaped the audit because the disjointness check skips any pair
    # where a box is under 25 characters, and both fragments were 19.
    ("Q6", 14): [
        ("set", "state_c1",
         "{{corpus:Q6/p14:affect_c1:0:117:sha=0b8d940aaf67}} weight."),
        ("set", "affect_c1",
         "{{corpus:Q6/p14:affect_c1:0:117:sha=0b8d940aaf67}} weight."),
        ("set", "state_c2",
         "{{corpus:Q6/p14:affect_c2:0:153:sha=0d48f0444ca7}} go."),
        ("set", "affect_c2",
         "{{corpus:Q6/p14:affect_c2:0:153:sha=0d48f0444ca7}} go."),
    ],

    ("Q6", 4): [
        ("set", "state_c1", "{{corpus:Q6/p4:affect_c1:0:31:sha=87595cd9dfc0}} happier."),
        ("set", "affect_c1",
         "{{corpus:Q6/p4:affect_c1:41:109:sha=ca4905db381e:shape=R55-1-5c7532303139,R68-0-20}}"
         "{{corpus:Q6/p4:affect_c1:110:116:sha=ea51ae6e548f}} everywhere."),
        ("set", "state_a2",
         "{{corpus:Q6/p4:state_a2:0:72:sha=d1111817d157:shape=R72-0-20}}"
         "{{corpus:Q6/p4:state_a2:73:101:sha=1789a92ce924}} hours"),
        ("set", "state_c2", "{{corpus:Q6/p4:state_c1:0:34:sha=4e032e011208}} late"),
        ("set", "affect_c2",
         "{{corpus:Q6/p4:state_c1:0:54:sha=f06a56022d3f}} tired."),
    ],

    # p5 writes the two halves in exactly parallel three-clause form:
    #   part 1  @0    antecedent + change ("... {{corpus:Q6/p5:change_a1:0:37:sha=5a4c4c317c1e:shape=C3}} by")
    #           @199  "{{corpus:Q6/p5:state_c1:0:32:sha=a5cb31d3a584}} ... no longer suffer from"
    #           @363  "{{corpus:Q6/p5:affect_c1:0:58:sha=8ca537769e96}}"
    #   part 2  @438  antecedent + change ("... {{corpus:Q6/p5:change_a2:0:28:sha=7386c8253705:shape=C3}}")
    #           @738  "{{corpus:Q6/p5:state_c2:0:51:sha=80f4a1676d53}} me ..."
    #           @880  "{{corpus:Q6/p5:affect_c2:0:49:sha=c20b853f77bc}} often ..."
    #
    # The consensus emptied BOTH c2 boxes (the scorer called them `absent` in
    # all ten runs) and the tail recovery then swept every remaining clause
    # into state_c2 as one lump, leaving affect_c2 empty. That recovered the
    # words but not the shape: the student wrote an "Instead, I hope ..."
    # effect clause at @880 exactly parallel to part 1's at @363. Split at the
    # sentence boundary, part 2 now mirrors part 1 box for box.
    ("Q6", 5): [
        ("set", "state_c2",
         "{{corpus:Q6/p5:state_c2:0:69:sha=2d5b313cec8c:shape=R69-0-20}}"
         "{{corpus:Q6/p5:state_c2:70:141:sha=a5198c07c1c7}}"),
        ("set", "affect_c2",
         "{{corpus:Q6/p5:affect_c2:0:70:sha=ae88ff0806c0:shape=R70-0-20}}"
         "{{corpus:Q6/p5:affect_c2:71:77:sha=e06e309b66b3}} healthy."),
        # ... and change_a2 runs to its sentence end, as change_a1 does. Part 1
        # keeps "{{corpus:Q6/p5:change_a1:42:90:sha=7d793a059cb2}} veggies" inside
        # the change clause; without the parallel tail here those nine words
        # belonged to no box at all.
        # Part 1 had the same three faults p4's did. `state_a1` ran 289 chars,
        # swallowing the change clause and most of the next sentence to end
        # mid-phrase at "I hope that I"; `state_c1` began mid-sentence at "and
        # {{corpus:Q6/p5:state_c1:37:72:sha=b42442d3c2e6}} me" and then ran past its own end,
        # trailing off into "Instead, I hope that I will" and duplicating the
        # opening of affect_c1. Trimmed to whole clauses so part 1 mirrors part 2.
        ("set", "state_a1",
         "{{corpus:Q6/p5:state_a1:0:68:sha=479931f088bd:shape=R68-0-20}}"
         "{{corpus:Q6/p5:state_a1:69:91:sha=8a310c57278d}} snacks"),
        ("set", "state_c1",
         "{{corpus:Q6/p5:state_c1:0:69:sha=90e91f3dbb8f:shape=R69-0-20}}"
         "{{corpus:Q6/p5:state_c1:70:136:sha=c91a4b465388:shape=R66-0-20}}"
         "{{corpus:Q6/p5:state_c1:137:156:sha=24d47e9a287e}} foods."),
        # state_a2 stopped at "in my home", while state_a1 runs through its
        # parallel "{{corpus:Q6/p5:state_a1:52:91:sha=02b653aa2b5f}} snacks". That
        # asymmetry left seven words belonging to no box; part 1's shape decides
        # the boundary.
        ("set", "state_a2",
         "{{corpus:Q6/p5:state_a2:0:62:sha=94017bc6a724:shape=R62-0-20}}"
         "{{corpus:Q6/p5:state_a2:63:131:sha=2a9f0d5783ed}} "
         "alternatives"),
        ("set", "change_a2",
         "{{corpus:Q6/p5:change_a2:0:67:sha=37cb113482cc:shape=R67-0-20}}"
         "{{corpus:Q6/p5:change_a2:68:138:sha=73f71d540754:shape=R70-0-20}}"
         "{{corpus:Q6/p5:change_a2:29:32:sha=6201111b83a0}} vegetables."),
    ],
}


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
    # `realistic` was found at "{{corpus:Q3/p6:realistic:11:36:sha=431cb737ffeb}} ...", so `action` ran
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

CONTEXT_SOURCE = {
    "bmod_h1_q1_response":      ("section", "Q1"),
    "bmod_h1_q2_response":      ("section", "Q2"),
    "bmod_h1_q4a_first":        ("scorer", "Q4a", "antecedent_1"),
    "bmod_h1_q4a_second":       ("scorer", "Q4a", "antecedent_2"),
    "bmod_h1_q4b_first":        ("scorer", "Q4b", "behavior_1"),
    "bmod_h1_q4b_second":       ("scorer", "Q4b", "behavior_2"),
    "bmod_h1_q4c_first":        ("scorer", "Q4c", "consequence_1"),
    "bmod_h1_q4c_second":       ("scorer", "Q4c", "consequence_2"),
    "bmod_h2_t1":               ("section", "T1"),
    "bmod_h2_d1":               ("section", "D1"),
    "bmod_h2_t2":               ("section", "T2"),
    "bmod_h2_d2":               ("section", "D2"),
    "bmod_h3_overview_response": ("section", "1a"),
    "bmod_h3_success_verdict":  ("scorer", "2a", "verdict"),
    "bmod_h3_success_how1":     ("scorer", "2a", "how_1"),
    "bmod_h3_success_how2":     ("scorer", "2a", "how_2"),
    "bmod_h3_assessment_response": ("section", "2b"),
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
            cm = counted_members(spec["handout"], item)
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
            # a complete second consequence — "{{corpus:Q6/p5:state_c2:56:89:sha=1a5abc3ab042}}
            # {{corpus:Q6/p5:state_c2:90:141:sha=d4c87436ee83}} Instead, I hope
            # {{corpus:1a/p12:response:276:309:sha=a5517f7d126e}} often" — and the scorer called
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
    body = None
    for key, entry in m.items():
        if not key.endswith("/" + action):
            continue
        for _loc, val in (entry or {}).items():
            kids = (val or {}).get("kids") or []
            if kids and isinstance(kids[0], str):
                body = kids[0]
        break
    if not body:
        return []                       # cannot locate it; stay silent rather than block

    # SENTENCES, not lines, and with no upper length bound. A line-based test with
    # a 130-character ceiling missed the very text this is for: a slot note is
    # rendered as one long bullet, so the rule wordings all sat above the ceiling
    # and passed. Ref markup is stripped from both sides, since the server resolves
    # it into the student's own text and the generated copy still carries the tag.
    def _sentences(text: str) -> set[str]:
        text = _re.sub(r"<Ref\b[^>]*/?>|REF:[\w.:-]+", " ", text)
        text = _re.sub(r"\s+", " ", text)
        return {t.strip() for t in _re.split(r"(?<=[.!?])\s+", text)
                if len(t.strip()) >= 60}

    # Substring, not set membership. Resolving a Ref removes a line break, so a
    # heading and the label beneath it merge into one "sentence" in the served copy
    # and would read as extra text on every correct dump.
    flat = _re.sub(r"\s+", " ",
                   _re.sub(r"<Ref\b[^>]*/?>|REF:[\w.:-]+", " ", want))
    return [t for t in _sentences(body) if t not in flat]


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

    try:
        want = _OP.build_web_prompt(item_id)
    except Exception as exc:                      # pragma: no cover
        print(f"(cannot verify idmap freshness for {item_id}: {exc})",
              file=sys.stderr)
        return
    lines = [ln.strip() for ln in want.split("\n")
             if 40 < len(ln.strip()) < 130
             and "REF:" not in ln and "<Ref" not in ln]
    if not lines:
        return
    try:
        with open(idmap) as fh:
            blob = fh.read()
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
