#!/usr/bin/env python3
"""Generate the lo-blocks <LLMAction> prompt bodies from the CLI rubric.

EQUIVALENCE.md is the why. In short: `agreement_app.py` measures the web
version against the same gold rows `baseline.py` uses, and that comparison only
means something if both run the SAME rubric. Until now the web prompts were
hand-written paraphrases, so the measurement compared "the rubric" with "a
summary of the rubric".

This module is the fix. Every one of the 23 <LLMAction> prompt bodies in
`content/psychology/bmod_handout{1,2,3}.olx` is now generated from
`rubric_hN.py`, following `score.py:build_prompt`'s skeleton — item header,
question as asked, credit components with points, deduction code table, all
guidance bullets, exemplars, context — copied verbatim.

    python3 olx_prompts.py --print Q4a   # one generated prompt, to stdout
    python3 olx_prompts.py --check       # do the .olx files match? (exit 1 if not)
    python3 olx_prompts.py --write       # regenerate the three .olx files

DO NOT HAND-EDIT the prompt bodies in the .olx files. Change `rubric_hN.py`, or
change this module, and re-run `--write`. `--check` fails if someone has.

Everything the web sends that the CLI does not, or vice versa, is a DEVIATION.
Each is declared here — in WEB_SYSTEM's rule table, RESPONSE / CONTEXT,
OMIT_CREDIT / OMIT_DEDUCTION / OMIT_GUIDANCE, or ITEM_NOTES — and written up in
EQUIVALENCE.md. That is the contract: a difference that is in neither place is a
bug, and `equivalence.py` counts it as an undeclared gap.
"""
from __future__ import annotations

import argparse
import difflib
import functools
import os
import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from handouts import config
import paths

OLX = paths.OLX

# The slot-sheet primitives, shared with the TypeScript side. Adding one has to be
# taught to five consumers and this generator was missed twice; the file says which
# they are and `equivalence.py --enforcement` checks each is actually honoured here.
PRIMITIVES_JSON = paths.PRIMITIVES_JSON


def primitives() -> dict:
    import json as _json
    with open(PRIMITIVES_JSON) as fh:
        return _json.load(fh)


def primitive_attrs(excluding_keys: bool | None = None) -> list[str]:
    """Attribute names, optionally only those whose keys leave the schema."""
    return [p["attr"] for p in primitives()["primitives"]
            if excluding_keys is None or p["excludesKeys"] == excluding_keys]

# Which rubric item each <LLMAction> carries. (equivalence.py holds the same
# map; it imports this one so the two cannot drift.)
ACTION = {
    "Q1": "bmod_h1_q1_llm", "Q2": "bmod_h1_q2_llm", "Q3": "bmod_h1_q3_llm",
    "Q4a": "bmod_h1_q4a_llm", "Q4b": "bmod_h1_q4b_llm", "Q4c": "bmod_h1_q4c_llm",
    "Q5": "bmod_h1_q5_llm", "Q6": "bmod_h1_q6_llm",
    "PR": "bmod_h2_pr_llm", "NR": "bmod_h2_nr_llm", "PP": "bmod_h2_pp_llm",
    "NP": "bmod_h2_np_llm", "D1": "bmod_h2_d1_llm", "DAY1": "bmod_h2_day1_llm",
    "WK1": "bmod_h2_wk1_llm", "D2": "bmod_h2_d2_llm", "DAY2": "bmod_h2_day2_llm",
    "WK2": "bmod_h2_wk2_llm",
    "1a": "bmod_h3_overview_llm", "1c": "bmod_h3_graph_llm",
    "2a": "bmod_h3_success_llm", "2b": "bmod_h3_assessment_llm",
    "3": "bmod_h3_improve_llm",
}
# Items scored from a slot sheet with NO prompt: every verdict is derived from
# the page, so there is no <LLMAction> and nothing for `--prompts` to compare.
# They are still audited for arithmetic (`--scoring`) and enforcement.
SHEET_ONLY = {"1b": "bmod_h3_data_checks",
              "T1": "bmod_h2_t1_checks", "T2": "bmod_h2_t2_checks"}

HANDOUT = {i: (1 if a.startswith("bmod_h1") else 2 if a.startswith("bmod_h2") else 3)
           for i, a in {**ACTION, **SHEET_ONLY}.items()}


def sheet_id(item: str) -> str:
    """The element carrying this item's slot sheet."""
    return ACTION.get(item) or SHEET_ONLY[item]


# ---------------------------------------------------------------------------
# The inlined system prompt.
#
# DEVIATION 2 (permitted): LLMAction has no system-message channel, so
# score.py's SYSTEM_TMPL heads the user prompt instead. Rules 3 and 5 are
# verbatim; the rest are re-pointed at the fields that actually exist here,
# because the web returns {checks, feedback} rather than a deduction ledger
# (DEVIATION 3). `_check_rules_still_match` asserts the verbatim ones really
# are verbatim, so a change to SYSTEM_TMPL cannot silently desynchronise this.
# ---------------------------------------------------------------------------

VERBATIM_RULES = [
    # (rule number, the text that must still appear verbatim in SYSTEM_TMPL)
    (3, "Do NOT output a score."),
    (5, "Grade what is written, generously but not charitably: these are first-year\n"
        "   students, so clumsy phrasing that clearly conveys the required idea earns\n"
        "   credit, but a required element that is absent is absent."),
]

WEB_SYSTEM = """You are an experienced teaching assistant grading {blurb}
This is PSYC 1030 (General Psychology, intro level, first-year students).

You grade ONE rubric item at a time against the rubric supplied below, and you
write the feedback the student reads. Return the JSON object the schema
requires: the `checks` sheet first, then `feedback`.

Rules you must follow:
1. Judge the item check by check. For every check on the sheet below, decide
   its verdict and quote the span of the response that settles it in that
   check's `evidence`. Quote verbatim; never paraphrase into the evidence
   field. For an unsatisfied check, say briefly what you looked for.
2. The deduction table below is the course's canonical wording for each way
   this item goes wrong. It is not a ledger for you to fill in — name any gap
   in `feedback` using that table's own words, so a student who fixes what you
   flagged meets the same phrasing if the same gap is graded later. The CODE
   beside each entry is an internal label: use the wording, and never put the
   code or its point value in front of the student.
3. Do NOT output a score. The score is computed from your checks.
4. `feedback` must be consistent with `checks`: do not praise something you
   marked unsatisfied, and do not fault something you marked satisfied.
5. Grade what is written, generously but not charitably: these are first-year
   students, so clumsy phrasing that clearly conveys the required idea earns
   credit, but a required element that is absent is absent.
6. If the response is empty, mark every check unsatisfied and say so plainly.
7. If the student describes something that could harm them (skipping meals,
   punishing themselves by withholding food or sleep, etc.), say so warmly in
   `feedback` and suggest a safer version. That is a safety note, not a fault
   in their work, and it never changes a verdict.
8. Where the grading guidance below tells you to set `escalate` or to write an
   `advisory_note`, there is no such field here: put the remark in `feedback`
   instead, and where the sheet carries a `confident` check, set it to `absent`.

Write `feedback` to the student, in the second person, warm and specific. Say
which requirements are met, name any that are missing, and quote their own
words when you point something out. It must read as prose written to them: no
deduction codes, no point values, no score, and no check keys."""


def _check_rules_still_match() -> list[str]:
    """SYSTEM_TMPL is the source; report any verbatim rule that has drifted."""
    from score import SYSTEM_TMPL

    bad = []
    for n, text in VERBATIM_RULES:
        if text not in SYSTEM_TMPL:
            bad.append(f"rule {n} no longer appears verbatim in score.py:SYSTEM_TMPL")
        if text not in WEB_SYSTEM:
            bad.append(f"rule {n} no longer appears verbatim in WEB_SYSTEM")
    return bad


# ---------------------------------------------------------------------------
# Fixtures: which on-screen field carries what.
#
# DEVIATION 1 (permitted): the student's response arrives per-field. The CLI
# parses one prose block; the web gives one box per judgement. RESPONSE lists
# those boxes, in the order they appear on the screen.
#
# CONTEXT maps each rubric record's `context` key to the web component(s)
# holding the same material. The paper Q1 block contains both the chosen UTB
# and the prose about it, so `Q1` maps to the closed choice AND the text area;
# the same split explains `_utb` / `_wgb`.
# ---------------------------------------------------------------------------

RESPONSE: dict[str, list[tuple[str, str]]] = {
    # item -> [(label shown above the field, component id)]
    "Q1":  [("", "bmod_h1_q1_response")],
    "Q2":  [("", "bmod_h1_q2_response")],
    "Q3":  [("Specific", "bmod_h1_q3_specific"),
            ("Measurable", "bmod_h1_q3_measurable"),
            ("Action-Oriented", "bmod_h1_q3_action"),
            ("Realistic", "bmod_h1_q3_realistic"),
            ("Time-Bound", "bmod_h1_q3_timebound")],
    "Q4a": [("First antecedent", "bmod_h1_q4a_first"),
            ("Second antecedent", "bmod_h1_q4a_second")],
    "Q4b": [("First active behavior", "bmod_h1_q4b_first"),
            ("Second active behavior", "bmod_h1_q4b_second"),
            ("Is it a good choice to modify, and why", "bmod_h1_q4b_modify")],
    "Q4c": [("First consequence", "bmod_h1_q4c_first"),
            ("Second consequence", "bmod_h1_q4c_second")],
    "Q5":  [("First reason", "bmod_h1_q5_first"),
            ("Second reason", "bmod_h1_q5_second")],
    "Q6":  [("state_a1 — the first antecedent being changed", "bmod_h1_q6_state_a1"),
            ("change_a1 — how it will be changed", "bmod_h1_q6_change_a1"),
            ("state_c1 — the first consequence being affected", "bmod_h1_q6_state_c1"),
            ("affect_c1 — how it will be affected", "bmod_h1_q6_affect_c1"),
            ("state_a2 — the second antecedent being changed", "bmod_h1_q6_state_a2"),
            ("change_a2 — how it will be changed", "bmod_h1_q6_change_a2"),
            ("state_c2 — the second consequence being affected", "bmod_h1_q6_state_c2"),
            ("affect_c2 — how it will be affected", "bmod_h1_q6_affect_c2")],
    "PR":  [("", "bmod_h2_pr")],
    "NR":  [("", "bmod_h2_nr")],
    "PP":  [("", "bmod_h2_pp")],
    "NP":  [("", "bmod_h2_np")],
    "D1":  [("", "bmod_h2_d1")],
    "DAY1": [("", "bmod_h2_day1")],
    "WK1": [("", "bmod_h2_wk1")],
    "D2":  [("", "bmod_h2_d2")],
    "DAY2": [("", "bmod_h2_day2")],
    "WK2": [("", "bmod_h2_wk2")],
    "1a":  [("", "bmod_h3_overview_response")],
    "1c":  [("Title", "bmod_h3_graph_title"),
            ("X-axis label", "bmod_h3_graph_x"),
            ("Y-axis label", "bmod_h3_graph_y"),
            ("Legend — the series names they typed, comma-separated",
             "bmod_h3_graph_series")],
    "2a":  [("Verdict", "bmod_h3_success_verdict"),
            ("How (1)", "bmod_h3_success_how1"),
            ("How (2)", "bmod_h3_success_how2")],
    "2b":  [("", "bmod_h3_assessment_response")],
    "3":   [("First change", "bmod_h3_improve_first"),
            ("Second change", "bmod_h3_improve_second")],
}

CONTEXT: dict[str, list[tuple[str, str]]] = {
    # rubric context key -> [(label, component id)]
    # The behaviour as the student WROTE it, not the one they ticked. Every later
    # item is graded against what they actually described — a student who picks
    # "lack of sleep" and then writes about exercise is doing the exercise
    # project, and Q4a's antecedents are antecedents of that. `bmod_h1_utb_observed`
    # is a SheetValue over `utb_stated`'s evidence, and falls back to the choice
    # until question 1 has been checked, so this line is never blank.
    #
    # Q1 itself is NOT routed through here: it keeps the raw choice, because
    # comparing the two is its own `matches_selected` check.
    "Q1":   [("Their unwanted target behavior, as they described it", "bmod_h1_utb_observed"),
             ("What they wrote about it", "bmod_h1_q1_response")],
    "Q2":   [("", "bmod_h1_q2_response")],
    "Q4a":  [("First antecedent", "bmod_h1_q4a_first"),
             ("Second antecedent", "bmod_h1_q4a_second")],
    "Q4b":  [("First active behavior", "bmod_h1_q4b_first"),
             ("Second active behavior", "bmod_h1_q4b_second")],
    "Q4c":  [("First consequence", "bmod_h1_q4c_first"),
             ("Second consequence", "bmod_h1_q4c_second")],
    "_utb": [("", "bmod_h1_utb")],
    "_wgb": [("", "bmod_h1_q2_response")],
    "T1":   [("", "bmod_h2_t1")],
    "D1":   [("", "bmod_h2_d1")],
    "T2":   [("", "bmod_h2_t2")],
    "D2":   [("", "bmod_h2_d2")],
    "1a":   [("", "bmod_h3_overview_response")],
    "2a":   [("Verdict", "bmod_h3_success_verdict"),
             ("How (1)", "bmod_h3_success_how1"),
             ("How (2)", "bmod_h3_success_how2")],
    "2b":   [("", "bmod_h3_assessment_response")],
}

# Q1 and Q2 are the two items where score.py adds a "## Weak hint" section,
# read out of the .docx's underline formatting and correct in only 6 of 20
# transcriptions. The web asks for the UTB as a closed choice before question
# 1, so the same fact arrives authoritatively. This replaces that section.
#
# Q2 was dropped from this list when the later items moved onto the behaviour the
# student DESCRIBED. It was getting both: the raw choice under "the behavior they
# chose", and the described one under context — two different answers to the same
# question, under two headings, which is exactly what the `seen` guard below
# exists to prevent. That guard keys on component id, so pointing context at a
# different component walked straight past it. Q1 keeps the section because
# comparing the two IS its job (`matches_selected`).
UTB_CHOICE = ("Q1",)

# Ref ids already in the .olx, kept so component ids stay stable across the
# rewrite: (action id, target) -> ref id. Anything not here is minted below.
REF_IDS = {
    "bmod_h1_q1_llm": {
        "bmod_h1_utb": "bmod_h1_q1_ref_utb",
        "bmod_h1_q1_response": "bmod_h1_q1_ref",
    },
    "bmod_h1_q2_llm": {
        "bmod_h1_utb": "bmod_h1_q2_llm_ref_utb",
        "bmod_h1_q1_response": "bmod_h1_q2_ref_q1_response",
        "bmod_h1_q2_response": "bmod_h1_q2_ref",
    },
    "bmod_h1_q3_llm": {
        "bmod_h1_utb": "bmod_h1_q3_ref_utb",
        "bmod_h1_q1_response": "bmod_h1_q3_ref_q1_response",
        "bmod_h1_q2_response": "bmod_h1_q3_ref_wgb",
        "bmod_h1_q3_specific": "bmod_h1_q3_ref_s",
        "bmod_h1_q3_measurable": "bmod_h1_q3_ref_m",
        "bmod_h1_q3_action": "bmod_h1_q3_ref_a",
        "bmod_h1_q3_realistic": "bmod_h1_q3_ref_r",
        "bmod_h1_q3_timebound": "bmod_h1_q3_ref_t",
    },
    "bmod_h1_q4a_llm": {
        "bmod_h1_utb": "bmod_h1_q4a_ref_utb",
        "bmod_h1_q1_response": "bmod_h1_q4a_ref_q1_response",
        "bmod_h1_q4a_first": "bmod_h1_q4a_ref1",
        "bmod_h1_q4a_second": "bmod_h1_q4a_ref2",
    },
    "bmod_h1_q4b_llm": {
        "bmod_h1_utb": "bmod_h1_q4b_ref_utb",
        "bmod_h1_q1_response": "bmod_h1_q4b_ref_q1_response",
        "bmod_h1_q2_response": "bmod_h1_q4b_ref_q2_response",
        "bmod_h1_q4a_first": "bmod_h1_q4b_llm_ref_a1",
        "bmod_h1_q4a_second": "bmod_h1_q4b_llm_ref_a2",
        "bmod_h1_q4b_first": "bmod_h1_q4b_ref1",
        "bmod_h1_q4b_second": "bmod_h1_q4b_ref2",
        "bmod_h1_q4b_modify": "bmod_h1_q4b_ref_m",
    },
    "bmod_h1_q4c_llm": {
        "bmod_h1_utb": "bmod_h1_q4c_ref_utb",
        "bmod_h1_q1_response": "bmod_h1_q4c_ref_q1_response",
        "bmod_h1_q4a_first": "bmod_h1_q4c_ref_a1",
        "bmod_h1_q4a_second": "bmod_h1_q4c_ref_a2",
        "bmod_h1_q4b_first": "bmod_h1_q4c_ref_b1",
        "bmod_h1_q4b_second": "bmod_h1_q4c_ref_b2",
        "bmod_h1_q4c_first": "bmod_h1_q4c_ref1",
        "bmod_h1_q4c_second": "bmod_h1_q4c_ref2",
    },
    "bmod_h1_q5_llm": {
        "bmod_h1_utb": "bmod_h1_q5_ref_utb",
        "bmod_h1_q1_response": "bmod_h1_q5_ref_q1_response",
        "bmod_h1_q4c_first": "bmod_h1_q5_ref_c1",
        "bmod_h1_q4c_second": "bmod_h1_q5_ref_c2",
        "bmod_h1_q5_first": "bmod_h1_q5_ref1",
        "bmod_h1_q5_second": "bmod_h1_q5_ref2",
    },
    "bmod_h1_q6_llm": {
        "bmod_h1_utb": "bmod_h1_q6_ref_utb",
        "bmod_h1_q1_response": "bmod_h1_q6_ref_q1_response",
        "bmod_h1_q2_response": "bmod_h1_q6_ref_q2_response",
        "bmod_h1_q4a_first": "bmod_h1_q6_llm_ref_a1",
        "bmod_h1_q4a_second": "bmod_h1_q6_llm_ref_a2",
        "bmod_h1_q4c_first": "bmod_h1_q6_llm_ref_c1",
        "bmod_h1_q4c_second": "bmod_h1_q6_llm_ref_c2",
        "bmod_h1_q6_state_a1": "bmod_h1_q6_ref_sa1",
        "bmod_h1_q6_change_a1": "bmod_h1_q6_ref_ca1",
        "bmod_h1_q6_state_c1": "bmod_h1_q6_ref_sc1",
        "bmod_h1_q6_affect_c1": "bmod_h1_q6_ref_ac1",
        "bmod_h1_q6_state_a2": "bmod_h1_q6_ref_sa2",
        "bmod_h1_q6_change_a2": "bmod_h1_q6_ref_ca2",
        "bmod_h1_q6_state_c2": "bmod_h1_q6_ref_sc2",
        "bmod_h1_q6_affect_c2": "bmod_h1_q6_ref_ac2",
    },
    "bmod_h2_pr_llm": {
        "bmod_h1_utb": "bmod_h2_pr_ref_utb",
        "bmod_h1_q2_response": "bmod_h2_pr_ref_wgb",
        "bmod_h2_pr": "bmod_h2_pr_ref",
    },
    "bmod_h2_nr_llm": {
        "bmod_h1_utb": "bmod_h2_nr_ref_utb",
        "bmod_h1_q2_response": "bmod_h2_nr_ref_wgb",
        "bmod_h2_nr": "bmod_h2_nr_ref",
    },
    "bmod_h2_pp_llm": {
        "bmod_h1_utb": "bmod_h2_pp_ref_utb",
        "bmod_h1_q2_response": "bmod_h2_pp_ref_wgb",
        "bmod_h2_pp": "bmod_h2_pp_ref",
    },
    "bmod_h2_np_llm": {
        "bmod_h1_utb": "bmod_h2_np_ref_utb",
        "bmod_h1_q2_response": "bmod_h2_np_ref_wgb",
        "bmod_h2_np": "bmod_h2_np_ref",
    },
    "bmod_h2_d1_llm": {
        "bmod_h1_utb": "bmod_h2_d1_ref_utb",
        "bmod_h1_q2_response": "bmod_h2_d1_ref_q2_response",
        "bmod_h2_t1": "bmod_h2_d1_ref_t",
        "bmod_h2_d1": "bmod_h2_d1_ref",
    },
    "bmod_h2_day1_llm": {
        "bmod_h1_utb": "bmod_h2_day1_ref_utb",
        "bmod_h1_q2_response": "bmod_h2_day1_ref_wgb",
        "bmod_h2_t1": "bmod_h2_day1_ref_t",
        "bmod_h2_d1": "bmod_h2_day1_ref_d",
        "bmod_h2_day1": "bmod_h2_day1_ref",
    },
    "bmod_h2_wk1_llm": {
        "bmod_h1_utb": "bmod_h2_wk1_ref_utb",
        "bmod_h1_q2_response": "bmod_h2_wk1_ref_wgb",
        "bmod_h2_t1": "bmod_h2_wk1_ref_t",
        "bmod_h2_d1": "bmod_h2_wk1_ref_d",
        "bmod_h2_wk1": "bmod_h2_wk1_ref",
    },
    "bmod_h2_d2_llm": {
        "bmod_h1_utb": "bmod_h2_d2_ref_utb",
        "bmod_h1_q2_response": "bmod_h2_d2_ref_q2_response",
        "bmod_h2_t2": "bmod_h2_d2_ref_t",
        "bmod_h2_d2": "bmod_h2_d2_ref",
    },
    "bmod_h2_day2_llm": {
        "bmod_h1_utb": "bmod_h2_day2_ref_utb",
        "bmod_h1_q2_response": "bmod_h2_day2_ref_wgb",
        "bmod_h2_t2": "bmod_h2_day2_ref_t",
        "bmod_h2_d2": "bmod_h2_day2_ref_d",
        "bmod_h2_day2": "bmod_h2_day2_ref",
    },
    "bmod_h2_wk2_llm": {
        "bmod_h1_utb": "bmod_h2_wk2_ref_utb",
        "bmod_h1_q2_response": "bmod_h2_wk2_ref_wgb",
        "bmod_h2_t2": "bmod_h2_wk2_ref_t",
        "bmod_h2_d2": "bmod_h2_wk2_ref_d",
        "bmod_h2_wk2": "bmod_h2_wk2_ref",
    },
    "bmod_h3_overview_llm": {
        "bmod_h3_overview_response": "bmod_h3_ov_ref",
    },
    "bmod_h3_graph_llm": {
        "bmod_h3_baseline": "bmod_h3_graph_ref_baseline",
        "bmod_h3_wk1": "bmod_h3_graph_ref_wk1",
        "bmod_h3_wk2": "bmod_h3_graph_ref_wk2",
        "bmod_h3_wk3": "bmod_h3_graph_ref_wk3",
        "bmod_h3_graph_title": "bmod_h3_g_ref_t",
        "bmod_h3_graph_x": "bmod_h3_g_ref_x",
        "bmod_h3_graph_y": "bmod_h3_g_ref_y",
    },
    "bmod_h3_success_llm": {
        "bmod_h3_overview_response": "bmod_h3_su_ref_ov",
        "bmod_h3_success_verdict": "bmod_h3_su_ref_v",
        "bmod_h3_success_how1": "bmod_h3_su_ref_1",
        "bmod_h3_success_how2": "bmod_h3_su_ref_2",
    },
    "bmod_h3_assessment_llm": {
        "bmod_h3_success_verdict": "bmod_h3_assessment_ref_success_verdict",
        "bmod_h3_success_how1": "bmod_h3_assessment_ref_success_how1",
        "bmod_h3_success_how2": "bmod_h3_assessment_ref_success_how2",
        "bmod_h3_assessment_response": "bmod_h3_as_ref",
    },
    "bmod_h3_improve_llm": {
        "bmod_h3_success_verdict": "bmod_h3_improve_ref_success_verdict",
        "bmod_h3_success_how1": "bmod_h3_improve_ref_success_how1",
        "bmod_h3_success_how2": "bmod_h3_improve_ref_success_how2",
        "bmod_h3_assessment_response": "bmod_h3_improve_ref_assessment_response",
        "bmod_h3_improve_first": "bmod_h3_im_ref_1",
        "bmod_h3_improve_second": "bmod_h3_im_ref_2",
    },
}


# ---------------------------------------------------------------------------
# Declared omissions. Everything the CLI sends is sent, EXCEPT these.
# Each entry needs a reason; equivalence.py reads this table so its coverage
# figures count an omission as accounted-for rather than as a gap.
# ---------------------------------------------------------------------------

OMIT_CREDIT: dict[str, dict[str, str]] = {}

# Guidance is matched by OPENING TEXT, never by list position. An earlier draft
# keyed these by index; inserting one bullet at the top of 1c's list silently
# moved the omission set onto the axis-titles-vs-tick-values bullet — the single
# most common deduction on the item, and one of the three the web CAN judge —
# while equivalence.py went on reporting zero gaps, because it read the same
# indices. `resolve_guidance_omissions` now fails loudly instead.
OMIT_GUIDANCE: dict[str, dict[str, str]] = {
    "1c": {
        "The bundle marks each piece of evidence":
            "the CLI evidence bundle's student/template labels do not exist here",
        "Shape-drawn graphs arrive as run-together text":
            "shape-drawn graph text is a .docx artifact",
        "A WRITTEN DESCRIPTION OF A GRAPH IS NOT A GRAPH":
            "the web asks only for the labels; the plotted data comes from 1b",
        # Now that `has_own_graph` is derived from the 1b data fields, this bullet
        # asks the model to decide something it is no longer given a slot for —
        # the same incoherence as a criterion with no verdict to report it in.
        # Both of its halves are code: no plottable numbers is `absent`, the
        # worked example's own numbers are `mismatch`. What survives is copied
        # WORDING, which stays a judgement and is still described in ITEM_NOTES.
        "FIRST DECIDE WHOSE GRAPH IT IS":
            "the grader derives `has_own_graph` from the 1b data fields, so this is "
            "not a judgement the prompt makes; copied wording is still judged on "
            "the label checks",
    },
}


def resolve_guidance_omissions(item_id: str, guidance: list[str]) -> dict[int, str]:
    """Turn OMIT_GUIDANCE's text keys into indices, or refuse to guess.

    A fragment that matches no bullet, or more than one, means the rubric moved
    under the omission. Silently dropping the wrong bullet is the failure this
    guards, so it raises rather than carrying on.
    """
    out: dict[int, str] = {}
    for frag, why in OMIT_GUIDANCE.get(item_id, {}).items():
        hits = [i for i, g in enumerate(guidance) if g.startswith(frag)]
        if len(hits) != 1:
            raise SystemExit(
                f"{item_id}: OMIT_GUIDANCE fragment {frag!r} matches {len(hits)} "
                f"guidance bullet(s), expected 1. rubric_hN.py changed — re-read "
                f"the bullet and update the fragment or drop the omission."
            )
        out[hits[0]] = why
    return out

OMIT_DEDUCTION: dict[str, dict[str, str]] = {}

# ---------------------------------------------------------------------------
# Scoring divergences: places where the two implementations can return
# DIFFERENT SCORES for the same judgement. These are arithmetic, not prompt
# text, and they live in the .olx `slots=` attributes. `equivalence.py
# --scoring` checks the mechanical part and reports anything not declared here.
#
# `necessary` is the load-bearing field. False means the web COULD express the
# CLI's rule and does not — a candidate fix, to be made and measured on its own,
# never folded into a prompt change.
# ---------------------------------------------------------------------------

SCORING_DIVERGENCES = [
    dict(items=["Q1"], what="a no-penalty check compares the prose against the UTB choice",
         necessary=False,
         why="the web asks 'Which behavior will you work on?' as a closed ChoiceInput "
             "before the box, which the paper version has no equivalent of. But "
             "`utb_stated` is still ASKED of the model on BOTH sides — the prose has to "
             "name the target, and UTB_NOT_STATED costs the same 2 points for the same "
             "reason — so the scoring does not diverge. What the web adds is "
             "`matches_selected`, an UNSCORED check reporting whether the prose names "
             "the same behaviour the student selected, shown first in the feedback. It "
             "carries no points precisely so a mismatch prompts a rewording rather than "
             "charging twice for one fact. "
             "THIS ENTRY USED TO DECLARE THE OPPOSITE: that the web read utb_stated "
             "from the choice and derived it, so the prose need not state it. That was "
             "never implemented here — no version of the content back to the initial "
             "import carries a `derived` rule for it — and the design was later settled "
             "the other way. The audit had been reporting the declaration as stale ever "
             "since; it was describing an intention, not the sheet."),

    {
        "items": ["1b"],
        "what": "every check is derived from the data fields",
        "necessary": True,
        "web_computes": {"1b": ["baseline_data", "week_1_data",
                                "week_2_data", "week_3_data"]},
        "why": "1b scores a point per week of data present, which the rubric is explicit "
               "is \"a presence check, not a quality judgement\". The CLI reads a .docx "
               "and must judge presence from transcribed prose; the web has one field per "
               "week, so presence is a property of the fields and is decided with the same "
               "parser the chart draws with. There is no prompt and no LLM call. "
               "Platform-forced in the same way as 1c's has_own_graph.",
    },
    {
        "items": ["T1", "T2"],
        "what": "NOT_A_TYPE (-2) is unreachable, and `type_stated` is derived",
        "necessary": True,
        "web_computes": {"T1": ["type_stated"], "T2": ["type_stated"]},
        "why": "the web asks for the type as a closed ChoiceInput whose four options ARE "
               "the four types, so a student cannot name something that is not one of "
               "them — the same shape as Q1's UTB_NOT_ON_LIST. What remains reachable is "
               "BLANK: the item is a `present` check over the choice field, worth the "
               "same 2 points, so a student who answers scores 2 and one who does not "
               "scores 0, exactly as on paper.",
    },
    {
        "items": ["1c"],
        "what": "`has_own_graph` is derived from the data fields, not asked of the model",
        "necessary": True,
        # The machine-checkable core of the prose below. `--enforcement` asserts
        # the web really does compute these, so the declaration cannot outlive the
        # thing it declares — a stale exemption is worse than none, because it
        # silences the audit for a difference that has changed shape.
        "web_computes": {"1c": ["has_own_graph"]},
        "why": "the CLI reads a .docx — an embedded chart, an image, or prose describing "
               "a graph that is not there — so whether the student produced one is a "
               "judgement over document evidence. On the web the chart is DRAWN from the "
               "four 1b fields, so the runtime already knows: no plottable numbers is "
               "`absent`, and the worked example's own numbers (it sits on the same "
               "screen) are `mismatch`. Both are computed with the chart's own parser, so "
               "the grader cannot disagree with what the student sees. Copied WORDING is "
               "still judged by the model, on the label checks. Platform-forced: there is "
               "no way to ask the CLI's .docx the question the web's fields answer.\n\n"
               "The kind is `complete`, not `plots`: it is satisfied only when EVERY "
               "week is present, so a partial month fails the gate and costs the whole "
               "item, which is what the paper rubric charges for not supplying a graph. "
               "That recovers p15 (two of four weeks, gold 0) and keeps p18 (nothing at "
               "all, gold 0). What it cannot recover is a student whose data is COMPLETE "
               "and who simply never drew the chart — p4 and p19, both gold 0 — because "
               "on the web that data draws it for them. Those two are excluded from the "
               "web measurement as unreachable (agreement_app.PER_ITEM_EXCLUDE).",
    },
    dict(items=["1c"], what="a legend keyed by DAY cannot be reproduced",
         necessary=True,
         why="the web's chart has one orientation — series are the four weeks, "
             "the x-axis is the seven days. A paper student who plotted it the "
             "other way round has a legend naming days, which the graders "
             "accepted (p11) and which the web scores as not naming the four "
             "series. One corpus row, structural, not a prompt defect."),
]

# Web-only text an item needs because of how its screen is built. Additions,
# not paraphrases: they say something about the web that the rubric cannot
# know, and each is a deviation recorded in EQUIVALENCE.md.
ITEM_NOTES: dict[str, str] = {
    # A mismatch reframes everything after it: the rest of the feedback is about
    # a behavior the student may not think they are being asked about, and a
    # student who reads three paragraphs before being told which behavior was
    # graded has to re-read all three. So it leads, and the checklist puts the
    # check first for the same reason.
    "Q1": (
        "## Say this before anything else\n"
        "If `matches_selected` is `differs`, the FIRST sentence of `feedback` says "
        "so: name the behavior they ticked, name the one they wrote about, and say "
        "that the rest of this feedback is about what they wrote. Then give the "
        "normal feedback.\n\n"
        "It is not a fault and nothing is deducted for it — most often they simply "
        "changed their mind — so say it plainly and without warning them off. If it "
        "is `matches`, say nothing about it at all: confirming a match the student "
        "never doubted spends their attention on nothing.\n"
    ),
    # The eight boxes are POSITIONAL and the rubric's matching is not. The CLI
    # reads one undivided block, so it pairs the student's antecedents against
    # 4a's set-wise; splitting the answer into `state_a1`/`state_a2` makes
    # position part of the test, which the rubric never asks for. p12 addressed
    # both of 4c's consequences in the opposite order and lost 5 of 10 on four
    # `mismatch` verdicts, where gold and the CLI both gave full marks — against
    # this item's own rule that "Mismatch means a DIFFERENT item, not a reworded
    # one". The final clause preserves the whole-missing-half rule.
    # The paragraph below used to describe ONE answer with four values --
    # first/second/neither/absent -- which is how this looked before the verdict
    # and the identity were split into two fields. Post-split the web takes a
    # verdict of met/absent/mismatch and a SEPARATE `refers_to` whose enum the app
    # builds as [...labels, "none"], so `neither` and `absent` are values that
    # field rejects and the model cannot emit them. It was telling the grader to
    # answer in the CLI's vocabulary on the one channel every remaining Q6
    # disagreement lives in.
    #
    # The CLI's vocabulary is NOT wrong and is not changed: rubric_h1's cover spec
    # declares verdicts ["first","second","neither","absent"] because that is what
    # the CLI accepts, and equivalence.py bridges it -- `neither` maps to
    # `refers_to: none`, `absent` to `verdict: absent`. COVER VOCAB DIFFERS exists
    # to police exactly that bridge. Only the web-facing instruction was at fault.
    "Q6": (
        "## What the four `state_` checks report\n"
        "These four do NOT report a match. They report an IDENTITY, and they report "
        "it in a FIELD OF ITS OWN, separate from the verdict. The two fields take "
        "different values and neither accepts the other's.\n"
        "`verdict` says whether the box names an antecedent (or a consequence) at "
        "all: `met` if it does, `absent` if it does not.\n"
        "`refers_to` says WHICH of the two listed items it is: `first`, `second`, or "
        "`none`. `none` is the value for \"not either of the two\" -- it is the only "
        "one, so do not answer `neither`, and do not put `absent` here. Those are "
        "not values this field takes.\n\n"
        "Say what you see and nothing more. Whether the pair covers both listed "
        "items is worked out from your two answers by the grader, so you do not need "
        "to reason about the other box, and a student who addresses 4a's second "
        "antecedent first has still addressed it — report `second` and it will be "
        "credited. One distinction matters for the feedback rather than the score: "
        "`met` with `refers_to: none` says they named an antecedent but not one of "
        "4a's, while `absent` says they named none at all. The points are the same "
        "either way; the difference decides whether the student is told their "
        "antecedent does not match 4a or that they did not state one.\n\n"
        "ONE THING TO CARRY INTO `feedback`. Each of the two listed items can be "
        "credited once, so if you report the SAME label for both boxes — `first` "
        "twice, say — the student has named one antecedent twice and left the other "
        "unaddressed, and only one of the two boxes can count. Your verdicts already "
        "handle the scoring; what you must not do is congratulate them on both boxes "
        "in that case. Say that the second repeats the first and name the item from "
        "4a they have not yet addressed.\n"
    ),
    "1c": (
        "## How this item reaches you\n"
        "The student does not upload a figure. SelfMonitorPlot draws their chart live "
        "from the four weeks of data they entered in 1b and the three labels they type "
        "here. Everything the paper rubric asks of a graph is theirs: the data that "
        "produces it, the three labels, and the legend — they name the four plotted "
        "series themselves, and until they do their chart's key reads 'Series 1, "
        "Series 2, ...', which is not a legend. Judge `legend` on the series names "
        "only.\n\n"
        "THE WORKED EXAMPLE IS ON THIS SCREEN, immediately above their boxes, and "
        "reproducing it is the live form of the paper item's template failure. It is a "
        "water-drinking chart titled 'Water {{corpus:1c/p5:title:5:32:sha=97ca3baaf650:shape=R27-0-27}}, with axes "
        "'{{corpus:1c/p2:x:0:16:sha=f1f5ac605348:shape=R12-1-57,R16-0-27}} and 'Ounces of Water per Day', plotting:\n"
        "  Baseline 8, 10, 8, 12, 6, 10, 0\n"
        "  Week 1   32, 20, 22, 28, 30, 32, 10\n"
        "  Week 2   30, 28, 26, 30, 32, 32, 30\n"
        "  Week 3   25, 26, 30, 32, 32, 28, 32\n"
        "Two distinct failures come out of that, and only one of them is yours. If the "
        "DATA is those numbers, the GRADER detects it: it compares the fields against "
        "the example itself and sets `has_own_graph` to `mismatch`, zeroing the item "
        "exactly as on paper. You are not asked about that, and you should not discuss "
        "it. What IS yours is when only the WORDING is copied — a title of 'Water {{corpus:1c/p5:title:5:32:sha=97ca3baaf650:shape=S1-20220a202020202020202022,R38-0-27}} from a student who did not track water, or a y-axis of 'Ounces of "
        "Water per Day' — that is `generic` on the label, like an untouched 'Chart "
        "Title'. Their own graph names their own behaviour: hours of sleep, minutes of "
        "exercise, servings.\n\n"
        "The x-axis is the exception: '{{corpus:1c/p2:x:0:16:sha=f1f5ac605348:shape=R12-1-57,R16-0-27}} is the example's label, the "
        "placeholder, AND the correct answer for nearly every student, since all four "
        "weeks are plotted Sunday to Saturday. Do not treat it as copied.\n"
    ),
}

# The web stand-in for score.py's graph_bundle. On the CLI, `has_own_graph` is
# judged from an evidence bundle dug out of the .docx (chart XML, embedded
# images, grouped shape text). Here the chart is generated, so the equivalent
# evidence is the data it is generated FROM — blank or non-numeric weeks render
# no graph. build_prompt puts this section last before the response; so do we.
EVIDENCE: dict[str, tuple[str, list[tuple[str, str]]]] = {
    "1c": (
        "## Graph evidence for this submission\n"
        "The four weeks of data the student entered in 1b. SelfMonitorPlot plots "
        "exactly these, so they are what decides whether a graph exists at all.",
        [("Baseline week", "bmod_h3_baseline"),
         ("Week 1", "bmod_h3_wk1"),
         ("Week 2", "bmod_h3_wk2"),
         ("Week 3", "bmod_h3_wk3")],
    ),
}


# ---------------------------------------------------------------------------
# The checklist. DEVIATION 3 (permitted): the web returns a slot sheet, so the
# the paper scorer's credit_checks + deductions + advisory_note + safety_flag +
# escalate collapse into {checks, feedback}. The sheet is authored in the .olx
# `slots` attribute; this reads it so prompt and schema cannot drift.
#
# DEVIATION 7 (permitted), a consequence of 3: LLMAction appends
# `slotSheet.slotSheetGuidance()` to every slot-sheet prompt, and the schema
# gains a field on some. None of it is in the .olx, and the CLI sends none of it.
# Two parts, only one conditional:
#
#   * ALL 23 items — `studentFacingGuidance()`: spell out the rubric's
#     abbreviations and check keys, because the prose is read by someone who has
#     not seen the rubric. Also restated in the `feedback` and `note` schema
#     descriptions, which are read at a different moment.
#   * The 20 items whose checklist the student SEES — `checklistGuidance()` plus
#     `buildSlotSchema(..., perCheckNotes=true)`, which adds a REQUIRED `note`
#     (capped at two sentences) to every non-computed check and tightens the
#     `evidence` description, because the web DISPLAYS evidence under its check
#     while the CLI keeps it as an internal audit field.
#
#   * The 3 items with showChecks="false" (bmod_h1_q5, bmod_h3_assessment,
#     bmod_h3_improve) — `terseFeedbackGuidance()` instead, capping `feedback`
#     at four sentences. Hiding the checklist removes the structure that was
#     bounding length, and these items are the ones graded most gently.
#
# So all 23 differ from the CLI; none of them by the same amount. Tying the spell-out rule to showChecks would have exempted
# exactly the items whose output is nothing BUT prose.
#
# It is a display difference, not a grading one: `note` is prose shown under its
# own check, is never scored, and no verdict, point value or deduction wording
# depends on it. `equivalence.py --enforcement` is unmoved by it, because that
# audit compares scoring behaviour rather than prompt text — which is precisely
# why this has to be written down rather than left for the audit to catch.
#
# What it DOES affect is output length: 8-11 notes per item, against an
# `interactive` budget of 16384 covering reasoning and output together. Re-run
# `agreement_app.py` before trusting a web-vs-gold figure measured before this.
#
# NOT reproduced here on purpose. This module generates the prompt BODIES that
# live in the .olx; the guidance is appended at runtime, so writing it into the
# generated text would send it twice on the web and would make `--check` demand
# it in files the runtime already supplements.
# ---------------------------------------------------------------------------

def parse_forbid(spec: str) -> list[dict]:
    """Mirror of lo-blocks parseForbid (packages/shared/lib/llm/slotSheet.ts).

    `key:slot=value,slot=value`, rules separated by `|`. The named check FAILS
    only when EVERY condition holds, and like `equals` it is COMPUTED, so it must
    not appear in the prompt's checklist or the response schema.

    Why a primitive rather than one composite slot: `equals` asks whether two
    answers agree and `expect` compares one against an authored value, and
    neither says "fail when A is this AND B is that". Written as a single slot the
    question becomes composite, and the rule this replaces failed four times
    exactly that way — asked one answer at a time it was stable, asked as one
    judgement the model resolved the tension by re-reading which clause was which.
    """
    out = []
    for entry in (spec or "").split("|"):
        entry = entry.strip()
        if not entry:
            continue
        key, _, rest = entry.partition(":")
        conds = []
        for cond in rest.split(","):
            slot, _, value = (x.strip() for x in cond.partition("="))
            if slot and value:
                conds.append({"slot": slot, "value": value})
        if key.strip() and conds:
            out.append({"key": key.strip(), "conds": conds})
    return out


def parse_equals(spec: str) -> list[dict]:
    """Mirror of lo-blocks parseEquals (packages/shared/lib/llm/slotSheet.ts).

    A check named here is COMPUTED by the grader from two others, so it must not
    appear in the prompt's checklist: `buildSlotSchema` leaves it out of the
    response schema, and asking for an answer the model cannot return is the same
    incoherence as a criterion with no slot.
    """
    out = []
    for entry in (spec or "").split("|"):
        entry = entry.strip()
        if not entry:
            continue
        parts = [p.strip() for p in entry.split(":")]
        key = parts[0] if parts else ""
        ops = parts[1] if len(parts) > 1 else ""
        lenient = parts[2] if len(parts) > 2 else ""
        left, _, right = (x.strip() for x in (ops.partition(",")))
        if key and left and right:
            out.append({"key": key, "left": left, "right": right,
                        "lenient": [x.strip() for x in lenient.split(",") if x.strip()]})
    return out


# ---------------------------------------------------------------------------
# The verdict vocabulary, read from lo-blocks rather than copied.
#
# A copy here is the thing that drifts, and this one would drift silently: the
# generated "## The checklist to return" section LISTS each check's verdicts, so
# a stale copy writes a prompt describing a schema the app does not send. Same
# reasoning as agreement._ts_literal, same failure it prevents.
# ---------------------------------------------------------------------------
def _slotsheet_ts() -> str:
    try:
        return open(paths.SLOTSHEET_TS).read()
    except OSError as e:                       # pragma: no cover - config error
        raise SystemExit(f"cannot read {paths.SLOTSHEET_TS}: {e}")


def _ts_string_array(name: str) -> list[str]:
    """Lift `export const NAME = [ ... ];` out of slotSheet.ts."""
    m = re.search(rf"export const {name}\s*=\s*\[(.*?)\]", _slotsheet_ts(), re.S)
    if not m:
        raise SystemExit(f"{name} not found in {paths.SLOTSHEET_TS} — "
                         "the verdict vocabulary mirror in olx_prompts is stale")
    return re.findall(r"'([^']+)'", m.group(1))


@functools.lru_cache(maxsize=None)
def default_verdicts() -> list[str]:
    return _ts_string_array("DEFAULT_VERDICTS")


@functools.lru_cache(maxsize=None)
def extra_verdicts() -> list[str]:
    return _ts_string_array("EXTRA_VERDICTS")


def parse_choices(spec: str | None) -> dict[str, list[str]]:
    """Mirror of slotSheet.ts:parseChoices — named sets of categories."""
    out: dict[str, list[str]] = {}
    for grp in (spec or "").split("|"):
        name, _, members = grp.partition(":")
        vals = [v.strip() for v in members.split(",") if v.strip()]
        if name.strip() and vals:
            out[name.strip()] = vals
    return out


def pick_set(segment: str | None) -> str | None:
    """Mirror of slotSheet.ts:parsePick — `pick(operant_type)` -> the set name."""
    m = re.fullmatch(r"pick\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)", (segment or "").strip())
    return m.group(1) if m else None


def parse_expect(spec: str | None) -> list[dict]:
    """Mirror of slotSheet.ts:parseExpect."""
    out = []
    for rule in (spec or "").split("|"):
        parts = [x.strip() for x in rule.split(":")]
        if len(parts) < 2:
            continue
        key, lhs = parts[0], parts[1]
        left, _, value = lhs.partition("=")
        if not key or not left.strip() or not value.strip():
            continue
        out.append({"key": key, "left": left.strip(), "value": value.strip(),
                    "lenient": [v.strip() for v in (parts[2] if len(parts) > 2 else "").split(",")
                                if v.strip()]})
    return out


def parse_requires(spec: str | None) -> list[dict]:
    """Mirror of slotSheet.ts:parseRequires — `key:condition[:lenient,...]`.

    The third segment lists verdicts on the CONDITION that establish nothing and
    so deny nothing, exactly as `equals`/`expect` use the word.
    """
    out = []
    for rule in (spec or "").split("|"):
        parts = [x.strip() for x in rule.split(":")]
        if len(parts) >= 2 and parts[0] and parts[1]:
            out.append({"key": parts[0], "cond": parts[1],
                        "lenient": [v.strip() for v in
                                    (parts[2] if len(parts) > 2 else "").split(",")
                                    if v.strip()]})
    return out


def count_max(segment: str | None) -> int | None:
    """Mirror of slotSheet.ts:parseCountMax — `count(3)` -> 3."""
    m = re.fullmatch(r"count\(\s*(\d+)\s*\)", (segment or "").strip())
    return int(m.group(1)) if m else None


def resolve_options(segment: str | None, defaults: list[str]) -> list[str]:
    """Mirror of slotSheet.ts:resolveOptions."""
    if count_max(segment) is not None:
        return []                      # a measurement, not a verdict list
    if pick_set(segment) is not None:
        return []                      # a classification, not a verdict list
    tokens = [t.strip() for t in (segment or "").split("/") if t.strip()]
    if not tokens:
        return list(defaults)
    if all(t in extra_verdicts() for t in tokens):
        return default_verdicts() + tokens
    return tokens


def parse_slots(spec: str, defaults: list[str]) -> list[dict]:
    """Mirror of lo-blocks parseSlots (packages/shared/lib/llm/slotSheet.ts)."""
    out = []
    for entry in (spec or "").split("|"):
        entry = entry.strip()
        if not entry:
            continue
        pts = None
        m = re.search(r"@(-?\d+(?:\.\d+)?)\s*$", entry)
        if m:
            pts = float(m.group(1))
            entry = entry[: m.start()].strip()
        parts = [p.strip() for p in entry.split(":")]
        raw_key = parts[0]
        label = parts[1] if len(parts) > 1 and parts[1] else raw_key
        seg = parts[2] if len(parts) > 2 else None
        opts = resolve_options(seg, defaults)
        cmax = count_max(seg)
        picks = pick_set(seg)
        out.append({
            "key": raw_key.lstrip("!").strip(),
            "label": label,
            "options": [o for o in opts if o],
            "gates": raw_key.startswith("!"),
            "pts": pts,
            "count_max": cmax,
            "picks": picks,
        })
    return [s for s in out
            if s["key"] and (s["options"] or s["count_max"] is not None
                             or s["picks"] is not None)]


# What a check means where the rubric's credit list does not already say.
# Keyed by slot key, or by "item:slot key" where the same key means different
# things on different items.
SLOT_NOTES = {
    "confident": "`absent` if any judgement above was a close call — this is rule 8's channel",
    # Web-only, and unscored on purpose. The web asks for the unwanted target
    # behavior twice — once as a closed choice before question 1, once in the
    # student's own words inside it — so the two can disagree in a way the paper
    # version cannot. The rubric has no deduction for that because on paper there
    # is nothing to disagree with, so this reports the fact and costs nothing.
    "Q1:matches_selected":
        "`matches` if the behavior the student writes about is the one they picked "
        "from the list above, `differs` if they write about a different behavior. "
        "Judge the BEHAVIOR, not the wording: '{{corpus:Q1/p19:response:46:70:sha=f4d8dbbfd800:shape=C1}}' matches "
        "the choice 'lack of sleep'. This check carries no points and never changes "
        "another verdict — everything else is judged on what they WROTE, whichever "
        "box they ticked",
    "Q2:wgb_is_counterpart":
        # Was "is it the direct positive counterpart, or a different behavior
        # altogether?" — the tier (a) question, which is NOT what this gate tests.
        # The desc was rewritten to tier (c) after it zeroed p10 and p18; this line
        # was missed, so the web prompt carried both framings while the CLI's carried
        # only one. A web-only note that contradicts the shared desc is the worst
        # shape a deviation can take.
        "the WGB_UNRELATED test, and only that: is the goal behavior about a DIFFERENT "
        "behavior altogether from the unwanted one? A goal in the right territory that "
        "simply fails to invert the behavior still satisfies this — that is "
        "WGB_NOT_OPPOSITE on `wgb_inverts_utb`, worth 2, not the whole item. Not satisfied "
        "means the whole item is that finding",
    # The other half of the same defect the note above describes. This slot charges
    # WGB_NOT_OPPOSITE — tier (b) — but asked only "WGB explicitly stated", which
    # every answer satisfies, so tier (b) was UNREACHABLE: `wgb_inverts_utb` — then named `wgb_stated`, which is the whole defect — came back
    # `met` on 20 of 20 cells on both sides while gold deducted for "opposite of
    # your UTB" on three. That is the whole of Q2's positive bias, the largest in
    # handout 1. The rule was never missing — guidance tiers (a)/(b)/(c) name p10
    # and p7 with their own words — it was asked of the wrong question.
    # An "instead of" clause was TRIED HERE AND REVERTED. p7 says "restart reading
    # {{corpus:Q2/p7:response:114:153:sha=053f7e52ad9f:shape=C1bf800}} games", naming the UTB only as the
    # thing displaced; a clause saying so is the obvious fix and it does work on
    # the cell it targets. It still did not pay:
    #
    #                       item mean exact (20 cells, 3 runs)      p7
    #   shipped-prompt CLI   18.3 -> 18.3  (no change)            9/12 -> 15/15
    #   web                  19.0 -> 18.3  (worse)                2/3  -> 3/3
    #
    # On the web it bought p7 and lost p17: "{{corpus:Q2/p17:response:10:42:sha=efb4fb832473}} stay
    # fit" started coming back `met` (1/3, from 3/3). That is the p17/p18 pair —
    # the carve-out below says a STATE of the same behaviour passes, and any extra
    # pressure on the different-activity side leaks across to make p17 a state too.
    # The two cells are close enough that this slot cannot be tightened for one
    # without loosening the other.
    #
    # A first draft also carried a general cue ("judge what the goal asks the
    # student to do, not what it mentions"), which bled TWO SLOTS AWAY into the
    # reasons count: p20 went 3,2,3 -> 2,2,2 and the CLI item mean 18.3 -> 17.3.
    # A general strictness cue in one slot's note does not stay in that slot.
    #
    # p7 does not need it: 9 of 12 single-cell CLI runs are already correct, and
    # score.py reaches p7 through the GATE instead, 8 of 8 (see rubric_h1.py).
    "Q2:wgb_inverts_utb":
        "TWO ways to fail, and the second is the common one. (i) no goal behavior is "
        "stated at all. (ii) a goal IS stated but does not invert the behaviour the "
        "Q1 UTB names — the WGB_NOT_OPPOSITE test. Tier (a) full credit needs the SAME "
        "behaviour turned around: the UTB names a behaviour there is too little or "
        "too much of, and the goal says to do that same behaviour more, or less. "
        "`absent` when the goal "
        "is in the right territory but never says to do the behaviour more or less. "
        "Two shapes fail this way. A goal naming a general CONDITION or ROUTINE the "
        "behaviour would contribute to does not say to perform it. A goal naming a "
        "DIFFERENT MEASURE — an outcome the behaviour is supposed to produce, in "
        "units the behaviour is not counted in — is not the behaviour either. "
        "But the same behaviour's own positive STATE is `met`: a goal naming the "
        "condition of HAVING DONE the behaviour is the inversion phrased as a "
        "state, and the graders charged nothing for it. "
        "So a different measure of the right behaviour fails; the right behaviour's "
        "state passes. A goal naming a DIFFERENT ACTIVITY fails here too — one that "
        "describes what the student will do INSTEAD never says to do less of the "
        "behaviour the UTB names. Answer "
        "`absent` for that here even though the `wgb_is_counterpart` gate above may "
        "also catch it; do not pass this check assuming the gate will",
    "1a:distinguishes_periods":
        "the NO_WEEKLY_BREAKDOWN test: does the answer distinguish any time periods at "
        "all? A single AGGREGATE verdict over the whole span does not, even when it "
        "mentions weeks — \"my three weeks of tracking prove the plan worked\" and "
        "\"looking at the whole month, nothing really changed\" both score 0: each "
        "delivers ONE verdict covering the entire span. What distinguishes periods is "
        "reporting more than one "
        "point in time separately, so that a reader can see the behaviour CHANGE",
    # The four period slots. Written out because the observed failure is not the one
    # the guidance anticipated: it warns against requiring one sentence per week, but
    # the model's actual mistake is treating a PARTIAL list of week names as
    # exhaustive. p11 names only "week two" and p14 only "{{corpus:1a/p14:response:293:316:sha=3df2d6dade26}}";
    # gold gave both the full 8, and both systems docked 2 for the week that went
    # unnamed. The label is not the evidence — the arc is.
    "1a:baseline_week":
        "is the BEFORE state given — the level the behaviour ran at prior to the "
        "intervention? A sentence that looks back before the plan began and gives "
        "the rate the behaviour ran at then is `met`; so is any pre-intervention "
        "figure or description. `absent` when the answer opens at the intervention and "
        "never says what came before: an answer beginning \"in {{corpus:1a/p6:response:7:27:sha=ffb845e9e43e}} "
        "plan I was still up past midnight most nights\" starts the clock at the "
        "intervention, and loses exactly this slot and no other",
    "1a:week_1":
        "does the answer's account of change COVER this stretch of the intervention? "
        "Judge the arc, not the label. Naming some weeks does NOT make the unnamed ones "
        "absent: an answer that runs from the before state through to the end covers all "
        "three intervention weeks even if it names one of them or none. Answer `absent` "
        "only when a period is clearly and specifically skipped",
    # Measured, and NOT extended further. Propagating the aggregate test from
    # `distinguishes_periods` into these three slots — plus a plea to keep the two
    # consistent — held the mean at 90% but put the variance back: over three runs
    # p6 swung 8.0/0.0/6.0 and p7, correct in every run before it, dropped to 6.0
    # once. Stability at the same accuracy beats a wider spread around the same
    # mean, because a measurement that moves cannot tell you whether the next
    # change helped. Reverted; do not re-add without three runs to compare.
    "1a:week_2":
        "same question for the middle stretch — and the same rule: a week the answer "
        "does not name by number is still covered if the account of change runs through "
        "it. An answer that names only its first and last weeks by number, but "
        "describes a change carrying continuously from one to the other, covers the "
        "middle week too, and gold credits all four slots",
    "1a:week_3":
        "same question for the final stretch, same rule. \"By the end of the month I "
        "was down to about one\" covers it without naming a week",
    # These four answer TWO things, in two fields. The verdict says whether an
    # antecedent (or consequence) is named at all; `refers_to` says WHICH of the
    # earlier item's two it is. They used to share one field, which is why the
    # verdict list read `first/second/neither/absent` — a set of pointers where
    # every other check has a judgement.
    'Q6:state_a1':
        "`met` if this box names an antecedent at all, `absent` if it names none. "
        "Then set `refers_to` to WHICH of 4a's two it is — `first`, `second`, or "
        "`none` if it is neither of them",
    'Q6:state_a2':
        'same for the other box. `second` is the expected `refers_to` but `first` '
        'is credited too if that is what it names, because the grader pairs them',
    'Q6:state_c1':
        "`met` if this box names a consequence at all, `absent` if it names none. "
        "Then set `refers_to` to WHICH of 4c's two it is — `first`, `second`, or "
        "`none` if it is neither of them",
    'Q6:state_c2':
        "same for the other box — either label is credited; the grader checks that "
        "between the two boxes both of 4c's consequences are named",
    "1c:legend":
        "the NO_LEGEND test. `met` when the series names name all four plotted "
        "periods — the baseline and the three intervention weeks — in any reasonable "
        "wording ('Baseline, Wk1, Wk2, Wk3' counts). `incomplete` when some are named "
        "and some are not, or the count does not match the four series; `absent` when "
        "the box is empty or holds something that is not a set of series names. "
        "Judge the series names, not the heading",
    "1c:has_own_graph":
        "the NO_GRAPH and TEMPLATE_GRAPH_ONLY tests, asked of the data rather than of "
        "a file. `met` when the four weeks under `Graph evidence` hold numbers "
        "SelfMonitorPlot can plot and they are the student's own. `absent` when they "
        "are empty or plainly not numeric — a whole-item gate should not turn on a "
        "miscount, and the plot itself already warns about a short or unreadable week; "
        "partial data still draws a graph, so judge the labels on their merits. "
        "`mismatch` when the numbers are the WORKED EXAMPLE'S, listed in the note "
        "above: that is the template graph reproduced, and it takes the whole item "
        "exactly as it does on paper",
    # The operant-conditioning criteria sheet, slot by slot.
    # "quote such a behavior" alone reads too literally, and this is a GATE, so a
    # literal reading costs the whole item. Students routinely point at the
    # behaviour instead of restating it — it is already named elsewhere on the
    # handout — and the graders accept that: participant 15's "{{corpus:NR/p2:nr:0:17:sha=bd6ad50ff8db}}
    # {{corpus:WK1/p15:wk1:18:82:sha=0f68e1c460d0}} want"
    # earned full credit on WK1, and their "{{corpus:WK2/p15:wk2:0:32:sha=4d06a923d530}}
    # {{corpus:WK2/p15:wk2:33:58:sha=c9e195b27719}}" lost 2 on WK2 for being the wrong TYPE, not for
    # failing to name a behaviour. Left literal, the verdict is a coin flip: the
    # same answer drew `no` from one run and `yes` from another, and each `no`
    # zeroed 4 points.
    "names_behavior": "criterion 1 (`behavior`) — `yes` when you can quote such a behavior; "
                      "put the quote in `evidence`. A REFERENCE to the student's own "
                      "behaviour counts as naming it: \"my goal\", \"my target behavior\", "
                      "\"my UTB\", \"my weekly goal\" all satisfy this, because the behaviour "
                      "is named elsewhere on the handout and the student is pointing at it. "
                      "Quote the reference. Answer `no` only when NO behaviour of the "
                      "student's is identified at all, even by reference",
    "names_stimulus": "criterion 2 (`stimulus`) — `yes` when you can quote it; put the quote in `evidence`",
    # Left as bare cross-references DELIBERATELY, having tried the alternative.
    #
    # TEST 1 and TEST 2 were relocated into these two lines from the guidance
    # block, on the hypothesis that moving a rule to the point of decision is what
    # fixed 1a p14. It does not transfer. Measured over all eight items that share
    # these gates, pooled exact went 129/144 -> 128/144, and the composition is the
    # reason to stop rather than tune: of four verdicts that moved, ONE was the
    # intended target (DAY2 p13, `contingent` yes->no, which corrected it to gold
    # 0.0) and three were collateral on checks the edit never mentioned — DAY2 p12
    # `you_arrange_it`, PP p6 `observed_type`, WK1 p19 `targets_own_behavior`, all
    # breaking a previously correct cell. The added strictness bled sideways.
    # `follows_behavior`'s half did not move its own target (p14) at all.
    #
    # Two lessons worth keeping. Relocation is not a general lever: it worked on 1a
    # where the slot text was silent on a case the guidance covered, and failed here
    # where the guidance is already emphatic and the gates already fire often. And
    # these five definitional gates are coupled — emphasis on any one of them shifts
    # the others, so they cannot be calibrated singly. If this is retried, isolate
    # ONE gate, and measure all eight items, because DAY2 alone reports no change.
    "contingent": "criterion 3 (`contingent`)",
    "follows_behavior": "criterion 4 (`follows_behavior`)",
    "you_arrange_it": "criterion 5 (`stimulus_is_arranged`)",
    "observed_type": "criterion 6 (`observed_type`) — which of the four it ACTUALLY is, "
                     "independently of what the student called it. Report what you see; "
                     "which one the item wanted is stated by the rule that reads this, not "
                     "by the order these are listed in",
    # The same criterion on the four example screens, where the type asked for is
    # AUTHORED — each screen names it — so there is nothing to identify against
    # and the check is an ordinary judgement. It used to be spelled as the
    # identity with the expected type placed first, which made the option ORDER
    # the answer key.
    #
    # The diagnosis that the identity carried is not dropped, it moves to prose:
    # `wrong_kind` is told to name the type the example actually shows, which is
    # what a student needs to read anyway.
    # Computed by `expect` now, so it is not asked and carries no note of its
    # own — the DO NOT ANSWER block generated for the rule says what it means and
    # names the expected type out loud. Left here as a marker so the next person
    # does not re-add a note for a check the model never sees.
    "phrased_directly": "criterion 7 (the CLI calls this input `avoidance_frame`) — `absent` "
                        "when the contingency is phrased by what is AVOIDED, `met` when it is "
                        "phrased directly. Never changes a verdict; it earns a comment on "
                        "phrasing. It is the ONLY check that judges this phrasing: no other "
                        "check may fail an answer for it",
    # These two carry the SECOND half of WRONG_TYPE. The rubric charges that code
    # once, for either cause: an example of the wrong type, OR the right type
    # aimed at the wrong behaviour (score.py:derive_oc_ledger uses `elif`, so at
    # most one -2 lands). Two scored checks would charge it twice.
    #
    # This used to be handled by telling the model "if `observed_type` is not the
    # type this item asks for, set this `yes`" — buying the arithmetic with a
    # verdict that is false about the student's answer, and shown to the student
    # in the checklist. The grader now suppresses the charge itself (the sheet's
    # `onlyif` attribute), so both checks are answered honestly.
    "targets_goal_behavior":
        "is the plan aimed at INCREASING their wanted goal behavior, rather than "
        "reinforcing the unwanted one? Answer what is true of the example even if it "
        "turned out to be a different type than this item asks for — where that makes "
        "this finding redundant the grader drops it, and it charges nothing twice",
    "targets_unwanted_behavior":
        "is the plan aimed at DECREASING their unwanted target behavior, rather than "
        "the wrong behaviour? Answer what is true of the example even if it turned out "
        "to be a different type than this item asks for — where that makes this finding "
        "redundant the grader drops it, and it charges nothing twice",
    "named_type": "criterion 8 (`named_type`) — which of the four the student SAID they "
                  "would use. Read the type slot in the context below; if it is blank or "
                  "garbled, fall back to their DEFINITION, which usually states the type "
                  "plainly. `unclear` only when neither says. Reported, never scored — but "
                  "the grader compares it against the type the example actually is, so "
                  "report it accurately rather than helpfully",
    "D1:defines_type": "which of the four types this DEFINITION describes, judged on its "
                       "content alone: something added or removed, behaviour increased or "
                       "decreased. Do not look at what they chose — that is the other "
                       "check, and the grader does the comparison",
    "D2:defines_type": "which of the four types this DEFINITION describes, judged on its "
                       "content alone: something added or removed, behaviour increased or "
                       "decreased. Do not look at what they chose — that is the other "
                       "check, and the grader does the comparison",
    "D1:named_type": "which of the four the student chose, read from the type slot in the "
                     "context below. `unclear` only if it is blank or unreadable",
    "D2:named_type": "which of the four the student chose, read from the type slot in the "
                     "context below. `unclear` only if it is blank or unreadable",
    # The rubric will not charge a mismatch it cannot establish: derive_oc_ledger
    # guards TYPE_MISMATCH with `named != "unclear"`, so an unreadable type slot
    # costs nothing. Without this the web charges 2 for the model's own hedge.
    "matches_chosen_type": "criteria 6 and 8 compared — does `observed_type` match "
                           "`named_type`? Both are already on this sheet above; this check "
                           "is only the comparison, and it is what carries TYPE_MISMATCH. "
                           "If `named_type` came out `unclear`, answer `yes`: there is no "
                           "established mismatch to charge",
    "targets_own_behavior": "criterion 10 (`targets_own_behavior`)",
    # Version C. Two earlier drafts each fixed one cell and broke the other, and
    # the reason was an authoring bug rather than a limit on the grader: the
    # second said to answer `other` ONLY when the trigger names an activity "not
    # pointing at either", which contradicted the first draft's own worked
    # example, where a cause named in the UTB paragraph IS `other`. The model
    # followed the more absolute clause, which is the right thing to do with
    # contradictory rules.
    #
    # The two cases differ in the KIND of expression, not in degree, so one rule
    # with two branches covers both and no `only` is needed.
    "trigger_behavior":
        "name which behaviour has to happen, or fail to happen, before the "
        "consequence arrives — quote it — then classify it `utb`, `wgb` or "
        "`other`. Decide by WHAT KIND OF PHRASE it is.\n"
        "  * A POINTER — \"my goal\", \"my daily goal\", \"my target this "
        "week\", \"my plan\" — has no content of its own. Classify it as "
        "whatever it points at: `wgb` for a goal they are building, `utb` for "
        "the behaviour they are cutting.\n"
        "  * A NAMED ACTIVITY — \"tidying the kitchen\", \"walking the dog\", "
        "\"{{corpus:Q4c/p8:second:23:39:sha=eddaae950aa8}}\" — has content, so judge it on its own terms "
        "against the behaviour the student CHOSE. Their paragraph also explains "
        "why they chose it, and the causes, effects and knock-on habits it "
        "mentions are not the chosen behaviour: a student explaining what their "
        "behaviour costs them will name several other activities in passing, "
        "and a plan triggered on one of THOSE is `other`. Being mentioned in "
        "that paragraph does not make an activity theirs; being the behaviour "
        "they chose does.\n"
        "  DO THIS BEFORE YOU CLASSIFY, and put it in `evidence`: quote the "
        "words THE STUDENT used for the behaviour, from their own unwanted-behaviour or goal statement, beside the trigger you quoted, and say "
        "whether they are equivalent by the definition given above. If they are "
        "not, answer `other`.",
    # The whole point of this slot is to stop `not_reason` absorbing weak reasons,
    # so it says so, and says where the boundary is with the case that DOES deduct.
    # Three non-`met` verdicts now, so the boundaries have to be drawn or the new
    # one sits unused — which is exactly how tier (b) on Q2 stayed unreachable.
    # This line used to carry the generosity rule and NOTHING ELSE — "count
    # separately even when thematically related" — while both exclusions sat in
    # guidance[4]. p18's three statements ARE thematically related, so the model
    # answered 3 in 5 runs of 5 on both sides, exactly as instructed, against a
    # gold of 2. The generosity rule stays; it is why p6 counts correctly. What it
    # needed was its two boundaries, with the cases quoted.
    # MEASURED, and the trade is recorded because it did not move the item rate.
    # The one-sentence rule below started as a blanket "ONE SENTENCE IS ONE
    # BENEFIT", added for p19 ("{{corpus:Q2/p19:response:299:347:sha=b7788ea9f103:shape=C1ef8000000}}
    # learning" — a knock-on chain, correctly one). That over-generalised: it also
    # collapsed p6's "{{corpus:Q2/p6:response:169:198:sha=23d76ae5248d:shape=Ce00000}} better", two independent
    # benefits, and took p6 from sometimes-right to 0/3. Splitting the rule on
    # STRUCTURE (knock-on = one, coordinated = two) fixed it: p6 8/8 and p19 8/8
    # on single-cell runs, and p6's decomposition became the graders' own,
    # listed 3 / failing 1 / given 2.
    #
    # It cost p20, stably, on both measured paths (CLI 2/3 -> 0/3, web 1/3 ->
    # 0/3), and the item mean did not move: 17.3-18.3 across all four prompt
    # variants tried, which is inside what a 3-run 20-cell measurement resolves.
    #
    # p20 IS DIAGNOSED AND THE FIX IS NOT APPLIED. Its three statements each NAME
    # a benefit and then explain it by contrast — "strengthen my intelligence
    # {{corpus:Q2/p20:response:142:180:sha=7718d04e03c8}} sleep...", "{{corpus:Q2/p20:response:371:388:sha=949f1763fb21}} bank",
    # "{{corpus:Q2/p20:response:419:450:sha=9b9c33768505}} deprive...". Gold credits all three. Test
    # (i) below rejects one of them as harm-framing, but (i) should fire only when
    # a statement names NO benefit at all: that is p3, "{{corpus:Q2/p3:response:45:70:sha=f60c7d9ca83d}}
    # me feel lazy", which gold credits ZERO. Sharpening (i) to "names no benefit
    # at all" reconciles p3 with p20 and conflicts with none of p6, p14, p17, p18,
    # p19. It was left undone deliberately: Q2's count has four or five borderline
    # cells and every refinement so far has traded some for others, so the next
    # attempt should be measured PER CELL at power (8+ runs on p3 and p20) rather
    # than by another full sweep.
    # The opener USED to be "Count generously about theme", which the model reads
    # before the tests that follow and which undercuts them: on p18 it returned 3
    # on two runs of three while the note already named p18's own failing sentence
    # under (ii). p19's failure was not covered at all — one sentence with a
    # knock-on clause counted as two benefits, stably in 3 of 3 runs.
    "Q2:reasons_given":
        "HOW MANY separate BENEFITS of the goal behaviour — `reasons_listed` minus "
        "`reasons_failing`, the two counts above. Thematic overlap alone does not "
        "merge two benefits. Whether one sentence holds one benefit or two is "
        "STRUCTURAL, not a matter of degree. A second half that is a KNOCK-ON "
        "EFFECT of the first is ONE benefit — a benefit followed by \"which will\" "
        "and the further good it leads to is one, not two, and counting such a "
        "chain as two costs a point. Two INDEPENDENT "
        "benefits merely joined by \"and\" are TWO — one about the body and one "
        "about mood, in a single sentence, is two benefits and counting it as one "
        "costs a point. Three kinds of statement do not count at all. (i) A reason the UNWANTED "
        "behaviour is bad, rather than a benefit of the wanted one. A sentence "
        "built on the NEGATIVE — what NOT doing the goal behaviour costs them — "
        "is a reason to stop the UTB however it is phrased, and the graders "
        "counted such sentences as ZERO benefits, even where the same fact "
        "stated positively would have counted. (ii) A restatement of the goal or of the problem it "
        "solves: saying they will become the kind of person who does the goal "
        "behaviour names the goal again, not a benefit of it; so is a remark "
        "that attributes their present condition to not having done the goal "
        "behaviour. (iii) A statement that says the same thing as one "
        "already counted. Answer 3 for three or more that survive all three tests",
    "Q5:example_2":
        "`met` for a second reason that is genuinely DIFFERENT from the first. "
        "`duplicate` when both entries are well-formed but amount to the SAME "
        "reason — two entries that each avoid the same discomfort, one naming the "
        "distance and one the aching afterwards, are one reason twice, and the "
        "graders wrote \"missing a reason\". `absent` only "
        "when there is no second entry at all. `not_reason` when there IS a second, "
        "distinct entry but it is not a reason for CONTINUING — an EFFECT of the "
        "behaviour rather than a payoff from it. When it is present, distinct and a "
        "real payoff but merely thin, that is `met` plus `reasons_substantial: absent`",
    "reasons_substantial":
        "`absent` when a reason is PRESENT but weak — thin, vague, or barely "
        "explained. This costs NOTHING; it exists so you can say it in the "
        "feedback instead of reaching for `wrong_kind`. A reason that gestures at "
        "the student's own neglect without naming what they get out of it — \"I "
        "keep doing it because I am not looking after myself\" — is thin, and the "
        "graders left that kind at FULL marks with a written note. Reserve "
        "`wrong_kind` for a statement that is not a reason for CONTINUING at all "
        "— most often an EFFECT of the behaviour wearing a reason's clothes, like "
        "\"because it leaves me irritable and behind on everything\", which is "
        "what the behaviour causes rather than what the student gets out of it",
    # The scaffold in front of the count. Its arithmetic held on 120 of 120
    # cell-runs the first time it was tried, so the two parts are asked as
    # reported slots and the count stays the scored one, rather than teaching a
    # `present - failing` primitive to seven consumers.
    "reasons_listed":
        "how many statements the response OFFERS as reasons, counted off the page "
        "before judging any of them. This is not scored; it is the first half of "
        "the count below",
    "reasons_failing":
        "of those, how many are NOT a benefit of the goal behaviour — either "
        "because the statement restates the harm of the unwanted behaviour rather "
        "than naming something the goal gets you, or because it repeats another "
        "statement already counted. Not scored; the second half of the count below",

    # Narrow on purpose, and the pattern is quoted because near-twins of it earn
    # full credit: "{{corpus:DAY1/p15:day1:40:72:sha=e23fe0094031}} when I am caught up on
    # assignments" is `yes`, so nothing about withholding or about "until"/"when"
    # may trigger this. Only bare juxtaposition does.
    #
    # It USED to charge a second pattern — a "consequence" that is only the absence
    # of a penalty, quoting p8's "so I don't have to {{corpus:DAY1/p8:day1:105:132:sha=f154f6b814a1}}
    # miss it". That was withdrawn, because it collided with criterion 7:
    # `avoidance_frame` claims the same shape and its decision is to FLAG AND NEVER
    # DEDUCT, a decision handouts.GOLD_DIVERGENCES declares as
    # ADDED_AVERSIVE_NAMED on p8's DAY1/WK1 — renamed from AVOIDANCE_FRAMING and
    # narrowed on 2026-08-24, WK2 having been removed because gold is right there
    # ("score.py flags for review and never deducts, and the
    # lo-blocks sheet reaches the same verdict"). With the same sentence serving as
    # the worked example for two criteria with opposite outcomes, the two
    # implementations split on it: the web answered `yes` on all three runs while
    # the CLI charged the point, which both broke equivalence and made score.py
    # contradict its own declared divergence. The exclusion below is now explicit,
    # and the pushups example appears under criterion 7 ONLY.
    "consequence_asserted":
        "one point, and it charges ONLY this: the answer merely JUXTAPOSES behaviour "
        "and consequence without asserting one follows from the other. Two facts "
        "strung together with a bare AND — the behaviour performed, the reward "
        "taken — are `no`; the same two facts joined by SO, or by any word that "
        "makes the reward follow FROM the behaviour, are `yes`. Anything with "
        "if / when / for each / every time / until / once, naming something actually "
        "given or taken away, is `yes` — including withholding a reward until the "
        "behaviour happens, which is a normal reinforcement shape. This check does NOT "
        "judge phrasing: a consequence stated by what is AVOIDED asserts the link "
        "perfectly well and is `yes` here. Criterion 7 (`avoidance_frame`) is the only "
        "place that phrasing is recorded, and it never changes the score",
    # Criterion 9's caveat is repeated here, not just pointed at. This gate takes
    # the WHOLE item, and the measured failure was the model reading "till the end
    # of the week" as a weekly cadence on a plainly daily trigger — the exact case
    # the criterion pre-empts. The criteria section is far from the point of
    # decision; the checklist is where the verdict is committed.
    "cadence_is_daily":
        "criterion 9 (`cadence_ok`). Judge how often the BEHAVIOUR IS CHECKED, not "
        "how long the consequence lasts — a daily trigger whose reward runs to the "
        "end of the week is still daily. This gate takes the whole item, so answer "
        "`no` only when the contingency is plainly settled on the weekly schedule, "
        "e.g. a daily slot answered with a whole-week tally. When it could be read "
        "either way, it is daily",
    "cadence_is_weekly":
        "criterion 9 (`cadence_ok`). Judge how often the BEHAVIOUR IS CHECKED, not "
        "how long the consequence lasts. This gate takes the whole item, so answer "
        "`no` only when the contingency is plainly settled on the daily schedule. "
        "When it could be read either way, it is weekly",
}


# ---------------------------------------------------------------------------
# Building one prompt.
# ---------------------------------------------------------------------------

_REF = "\x00REF:%s:%s\x00"


def _ref(action: str, target: str, minted: dict) -> str:
    rid = REF_IDS.get(action, {}).get(target)
    if rid is None:
        # A ref the hand-written prompt did not have. Deterministic id so a
        # regeneration produces the same file.
        base = action[: -len("_llm")] if action.endswith("_llm") else action
        rid = "%s_ref_%s" % (base, re.sub(r"^bmod_h\d_", "", target))
        minted[(action, target)] = rid
    return _REF % (rid, target)


# What "matches" means, stated once, before the first component that uses the
# word. Per item, because only the items whose components say "matches" need it.
# Semantic equivalence, stated once. Q6 asks whether a box MATCHES a listed entry
# and WK1 asks whether a trigger names the SAME ACTIVITY the student chose; those
# are one operation, and two definitions of it would drift. Kept here so it can be
# placed EARLY on either prompt shape.
#
# The parity framing is what this adds, and it is measured: "semantically
# equivalent" on its own licenses open judgement, and WK1/p7 held 3/3 under this
# closed construction where an open test fenced after the fact held only 1/3.
EQUIVALENCE_DEF = (
    "The two things being compared are semantically equivalent. That "
    "includes equivalence established by combinations of negations and "
    "antonyms: failing to do a thing early is doing it late, forgetting "
    "to do a thing is not doing it, not suffering a bad state is being in "
    "the good one.\n"
    "ANTONYMS, precisely. Two words are antonyms when they name the OPPOSITE "
    "ENDS OF ONE SCALE -- more and less of a single property, so that naming one "
    "and negating it gives you the other. Early and late are one scale. Poor "
    "health and good health are one scale. Words that are merely both "
    "unpleasant, or both pleasant, or that name DIFFERENT properties, are not "
    "antonyms and do not establish equivalence: being tired and being cheerful "
    "are two properties, not two ends of one. Ask what single property is being "
    "measured before you call two words opposites."
)


MATCH_DEF = {
    "DAY1": ("## Definition of 'the same behaviour' below:\n"
              + EQUIVALENCE_DEF + "\n"),
    "DAY2": ("## Definition of 'the same behaviour' below:\n"
              + EQUIVALENCE_DEF + "\n"),
    "WK2": ("## Definition of 'the same behaviour' below:\n"
              + EQUIVALENCE_DEF + "\n"),
    "WK1": ("## Definition of 'the same activity' below:\n"
            + EQUIVALENCE_DEF + "\n"
            "Two phrases that are NOT equivalent by that test name two "
            "activities, however close the connection between them. An activity "
            "that another might cause, accompany, amount to, or be evidence of "
            "is a SECOND thing, not a point on the same scale.\n"
            "DEGREE AND DETAIL ARE NOT DIFFERENCES OF ACTIVITY. The same doing "
            "with a different number, frequency, duration or extra particular "
            "attached is still that doing. Compare WHAT IS BEING DONE, not how "
            "much of it is being done or how precisely it is specified.\n"
            "A phrase with NO CONTENT OF ITS OWN -- a pointer, such as \"my "
            "goal\" or \"my target this week\" -- is not compared by this test "
            "at all. Classify it by what it points at, as the check itself "
            "directs.\n"),
    "Q6": ("## Definition of 'matches' below:\n"
           + EQUIVALENCE_DEF + "\n"
           "A listed 4a or 4c entry often states one thing and then what follows "
           "from it -- \"X, so I Y\". Decide which of THREE kinds Y is before you "
           "compare, because it decides what the entry can be matched against.\n"
           "1. Y RESTATES THE ANTECEDENT in other words. Part of the antecedent; a "
           "box equivalent to Y matches that 4a entry.\n"
           "2. Y IS AN INTERMEDIATE ANTECEDENT -- a further step that still LEADS "
           "TO the unwanted behaviour rather than following from it. Also part of "
           "the antecedent, described one link nearer; a box equivalent to Y "
           "matches that 4a entry.\n"
           "3. Y IS A CONSEQUENCE -- the unwanted behaviour itself, or something "
           "that follows from it. Not part of the antecedent: a box equivalent to "
           "Y does NOT match that 4a entry. It may still match a 4c entry that "
           "lists that same consequence, and should be matched there.\n"
           "The test between 2 and 3 is direction: does Y lead to the unwanted "
           "behaviour, or follow from it? The unwanted behaviour is named in the "
           "Q1 answer in the context below.\n"),
}

# Items whose "## Credit components" section lists slots WITHOUT restating their
# rules. The rules still ship — once, in the checklist, which is where the verdict
# is committed and which also carries the verdict vocabulary.
#
# The shipped prompt otherwise prints every slot's `desc` TWICE, once here and
# once in the checklist, where score.py prints it once on a single line carrying
# points, verdicts and rule together. On Q1 that doubling lines up with a
# systematic difference: with identical rule text and byte-identical response
# text, score.py scores 85% while the shipped prompt scores 70-75%, and its
# errors are all UNDER-counts (p9 1 where gold wants 2, p10 0 where gold wants 2,
# p16 0 where gold wants 1, p11 and p19 2 where gold wants 3) — the shape you get
# if a strictness rule stated twice reads as emphasis.
#
# Q1 only, as an experiment. If it pays, the same is worth trying corpus-wide;
# note the opposite result is on record for `cadence_is_daily`, where repeating a
# caveat NEAR THE DECISION POINT was measured as a win. Repetition close to the
# verdict helped there; duplication across two sections may not be the same thing.
TERSE_CREDIT = {"Q1"}


# Items where the chosen-behaviour section drops the word "authoritative".
#
# That word was aimed at a comparison the model never sees: score.py reads a
# "weak hint" out of the .docx's underline formatting, right in only 6 of 20
# transcriptions, and the closed choice is reliable by contrast. As prompt text
# it instead asserts authority over the JUDGEMENT, which now contradicts
# `utb_stated`'s own rule that the field does not satisfy the check. Nothing
# slot-specific is added here to compensate — the rule stays in the slot's desc.
#
# Q1 only, to keep the measurement clean; Q2 carries the same section and would
# need its own re-measurement if this is generalised.
RELAX_UTB_AUTHORITY = {"Q1"}


def build_web_prompt(item_id: str, minted: dict | None = None) -> str:
    minted = {} if minted is None else minted
    h = HANDOUT[item_id]
    cfg = config(h)
    item = cfg["rubric"].BY_ID[item_id]
    action = ACTION[item_id]
    slots = parse_slots(*_slots_attr(h, action))

    p: list[str] = [WEB_SYSTEM.format(blurb=cfg["blurb"]), ""]
    p.append(f"# Rubric item {item['id']} — {item['max']:g} points\n")
    p.append(f"## Question asked of the student\n{item['question']}\n")

    if item.get("derive_from_criteria"):
        # Same placement rule as the credit-component path below: immediately
        # BEFORE the criteria that use the term. This branch had no such channel,
        # which is why WK1's equivalence rule lived in SLOT_NOTES to begin with.
        if MATCH_DEF.get(item_id):
            p.append(MATCH_DEF[item_id])
        p.append(_criteria_section(item))
    else:
        # Placed HERE, immediately before the components that use the word, and
        # kept to two sentences. Sixteen wording variants of this idea were built
        # and reverted on 2026-08-19, all of them added to the grading guidance
        # forty-odd lines further down; the hypothesis this tests is that the
        # position and the length were the problem rather than the content. The
        # components themselves say "matches 4a" and "matches 4c", so this defines
        # the term at its first use instead of qualifying it later.
        if MATCH_DEF.get(item_id):
            p.append(MATCH_DEF[item_id])
        p.append("## Credit components")
        omitted = OMIT_CREDIT.get(item_id, {})
        for c in item["credit"]:
            if c["what"] in omitted:
                continue
            # Not every component carries points. A reported-only slot exists so a
            # later check can use it, and a gating one costs the whole item rather
            # than a share of it — labelling either "(n pt)" would misstate it.
            worth = (" **GATE**" if c.get("gates")
                     else "" if c.get("pts") is None
                     else f" ({c['pts']:g} pt)")
            if item_id in TERSE_CREDIT:
                p.append(f"- `{c['what']}`{worth}")
            else:
                p.append(f"- `{c['what']}`{worth}: {c['desc']}")
        p.append("")

    # The deduction table goes to EVERY item, including the two shapes where
    # score.py omits it. DEVIATION: the CLI applies this wording after the call
    # (score.py:compose_feedback); the web has no post-processing step, so the
    # model must see the canonical phrasing to be able to use it.
    p.append("## Deduction codes — the course's canonical wording for each gap")
    omitted_d = OMIT_DEDUCTION.get(item_id, {})
    for d in item["deductions"]:
        if d["code"] in omitted_d:
            continue
        rep = " [repeatable]" if d.get("repeatable") else ""
        p.append(f"- `{d['code']}` (-{d['pts']:g}){rep}: {d['text']}")
    p.append("")

    # An item whose guidance is entirely slot-specific has none left here, and a
    # bare header invites the model to look for instructions that are not there.
    omitted_g = resolve_guidance_omissions(item_id, item["guidance"])
    kept_g = [g for i, g in enumerate(item["guidance"]) if i not in omitted_g]
    if kept_g:
        p.append("## Grading guidance")
        for g in kept_g:
            p.append(f"- {g}")
        p.append("")

    if item.get("exemplars"):
        p.append(
            "## Worked examples\n"
            "Three responses from other students in this cohort, with the verdict sheet "
            "the human grader's marks imply. Match your judgements to these. They are "
            "reference material only — never grade them."
        )
        for ex in item["exemplars"]:
            p.append(f"\n### {ex['label']}")
            p.append(f"Their 4a: {ex['four_a']}")
            p.append(f"Their 4c: {ex['four_c']}")
            p.append(f"Their answer: {ex['response']}")
            p.append("Verdicts: " + ", ".join(f"{k}={v}" for k, v in ex["slots"].items()))
            p.append(f"Why: {ex['note']}")
        p.append("")

    if item_id in ITEM_NOTES:
        p.append(ITEM_NOTES[item_id])

    p.append(_checklist_section(item, slots, item_id, _equals_attr(h, action),
                                _derived_attr(h, action), _counts_attr(h, action),
                                _choices_attr(h, action), _expect_attr(h, action),
                                _forbid_attr(h, action)))

    # One component, one <Ref>: the same value twice under two headings reads
    # as two different answers.
    seen: set[str] = set()

    if item_id in UTB_CHOICE:
        p.append(
            ("## The behavior they chose from the list\n"
             if item_id in RELAX_UTB_AUTHORITY else
             "## The behavior they chose (authoritative)\n")
            + "Chosen from the four on the list, before question 1."
        )
        p.append(_ref(action, "bmod_h1_utb", minted) + "\n")
        seen.add("bmod_h1_utb")

    ctx: list[tuple[str, list[tuple[str, str]]]] = []
    for k in item["context"]:
        fields = [(l, t) for l, t in CONTEXT.get(k, ()) if t not in seen]
        seen.update(t for _, t in fields)
        if fields:
            ctx.append((k, fields))
    if ctx:
        p.append("## Context from this student's other answers (read-only)")
        p.append(
            "Use these only where the rubric requires cross-item consistency. "
            "Do not grade them here."
        )
        for k, fields in ctx:
            p.append(f"\n### {k}")
            for label, target in fields:
                lead = f"{label}: " if label else ""
                p.append(lead + _ref(action, target, minted))
        p.append("")

    if item_id in EVIDENCE:
        note, refs = EVIDENCE[item_id]
        p.append(note)
        for label, target in refs:
            p.append(f"{label}: " + _ref(action, target, minted))
        p.append("")

    p.append(f"## Student response to grade (item {item['id']})")
    # The headings name the on-screen field, and are written so they cannot be
    # read as a claim about what arrived in it. A bare "### How (2)" asserts the
    # box IS a second explanation of how — which is the very thing the check
    # decides. The CLI has no such headings: it sends one undivided block and
    # asserts nothing, so an asserting heading is deviation 1 leaking a
    # judgement into the prompt. Measured on 2a p1, whose third sentence the
    # rubric names as a deduction case: the CLI marks `how_2` unmet, the web
    # marked it met.
    if any(label for label, _ in RESPONSE[item_id]):
        p.append(
            "Each heading is the on-screen field label — what the student was ASKED "
            "to put in that box, never a claim about what they actually wrote. Judge "
            "every box on its contents."
        )
    # Each box's content is DELIMITED, and the response section is CLOSED.
    #
    # A `<Ref>` to an empty box renders to nothing, so a heading was followed by
    # blank space and then by whatever came next. For every box but the last,
    # what came next was the next heading, and the emptiness was legible. For the
    # LAST box there is no next heading: the app appends its own grading guidance
    # after this prompt, so an empty final box put that guidance directly under
    # the field's heading, where it reads as the contents of the box.
    #
    # It was read that way. Measured across three passes of Q6, whose last box is
    # `affect_c2`: where that box was empty the grader quoted "WRITING TO THE
    # STUDENT" -- a heading from the app's appended guidance -- as the student's
    # own sentence, and the student read it back in their feedback. It was never
    # any other slot, on any item, which is the tell: not a model that invents
    # quotations, a model quoting what the prompt showed it. Two attempts to
    # instruct it out of this changed nothing (11 of 15 cell-passes, then 10 of
    # 15), because the instruction contradicted what the page appeared to say.
    #
    # So the fix is here, in what we generate, and it is structural: bounds
    # around every box so an empty one is visibly empty rather than absent, and a
    # terminator so nothing appended after this prompt can fall inside the last
    # box. Both are content-agnostic -- no rule here knows what the guidance that
    # follows says, which is why this does not belong in the app's shared sheet
    # module either.
    for label, target in RESPONSE[item_id]:
        if label:
            p.append(f"\n### Asked for: {label}")
        p.append("[box begins] " + _ref(action, target, minted) + " [box ends]")
    p.append(
        "\n## End of the student response\n"
        "Everything the student wrote is above this line, inside a "
        "`[box begins]`/`[box ends]` pair. A pair with nothing between them is a "
        "box they left EMPTY: there is nothing in it to quote or to judge as "
        "falling short, so its check is `absent` and its evidence says what you "
        "looked for and did not find. Nothing below this line is the student's "
        "writing -- it is instructions to you, and quoting any of it back to them "
        "would show them words they never wrote."
    )

    return "\n".join(p).rstrip() + "\n"


def _criteria_section(item: dict) -> str:
    """score.py:build_prompt's derive_from_criteria block, verbatim."""
    parts = [
        "## How to judge this item\n"
        "Do NOT output a score or a deduction list. Fill in the criteria sheet; the "
        "score is computed from it.\n\n"
        "Operant conditioning means: the future probability of a VOLUNTARY BEHAVIOUR "
        "is changed by a CONSEQUENCE that is contingent on it. Answer these in order "
        "and answer them literally about what the student wrote:\n"
        "1. `behavior` — quote the voluntary behaviour of the student that the plan "
        "acts on. If the answer names no behaviour of theirs, leave this an empty "
        "string.\n"
        "2. `stimulus` — quote the thing being added or taken away. Empty string if "
        "none is named.\n"
        "3. `contingent` — is the stimulus delivered BECAUSE of that behaviour (or its "
        "absence)? A statement of something the student will just do, with no link to "
        "performing the behaviour, is not contingent.\n"
        "4. `follows_behavior` — does the CONSEQUENCE EVENT (gaining or losing the "
        "thing) occur after the behaviour? Judge the delivery, not the wording. "
        "\"I am not allowed X until I do B\" DOES satisfy this: X is delivered once B "
        "happens, which is the ordinary shape of a reinforcement contingency. It fails "
        "only when nothing is ever delivered contingent on the behaviour — the plan is "
        "purely to remove a temptation or set up the environment in advance, which is "
        "an antecedent manipulation rather than a consequence.\n"
        "5. `stimulus_is_arranged` — is the consequence something the student arranges, "
        "as opposed to the behaviour's own automatic result? Removing an obligation or "
        "chore IS arranged; a rested body, or fitness itself, following the behaviour that produces it is not.\n"
        "6. `observed_type` — given increase-or-decrease and add-or-remove, which of "
        "PR/NR/PP/NP is it actually? Use `none` only if 1-4 fail.\n"
        "   DUAL DESCRIPTIONS: an arrangement of the form \"I am not allowed X until I "
        "do B\" is genuinely describable two ways — as PR of B (X is granted once B "
        "happens) and as NP of not-B (X is withheld while B is absent). Both are "
        "correct readings. When the arrangement admits both and one of them is the "
        "type under discussion, report that one; do not mark it a mismatch.\n"
        "7. `avoidance_frame` — true if the contingency is phrased by what is AVOIDED "
        "when the behaviour occurs (\"so I don't have to do {{corpus:DAY1/p8:day1:117:137:sha=aa91092efc87}} it\") "
        "rather than by what is added or removed after it. This never changes the "
        "score; it flags the answer for a phrasing comment. It is the ONLY criterion "
        "that judges this phrasing — no other check may deduct for it.\n"
    ]
    if item.get("cadence"):
        parts.append(
            "8. `named_type` — which of the four the student SAID they would use. Read "
            "the type slot in the context below; if it is blank or garbled, fall back to "
            "their DEFINITION, which usually states the type plainly (\"{{corpus:D2/p15:d2:28:41:sha=561e03f6a586:shape=R13-0-20}}"
            "{{corpus:D2/p15:d2:42:110:sha=bd23c4b2e196}}\" is "
            "Positive Punishment). Use `unclear` only when neither says.\n"
            f"9. `cadence_ok` — is the TRIGGER evaluated {item['cadence']}? Judge only "
            "how often the behaviour is checked, not how long the consequence lasts: a "
            "daily trigger whose reward runs to the end of the week is still daily. Set "
            "this false only when the contingency is plainly settled on the other "
            "schedule — e.g. a daily slot answered with a whole-week tally.\n"
            "10. `targets_own_behavior` — is it aimed at this student's own UTB/WGB "
            "rather than some clearly different behaviour?\n"
        )
    parts.append("")
    return "\n".join(parts)


def _checklist_section(item: dict, slots: list[dict], item_id: str,
                       equals: list[dict] | None = None,
                       derived: list[dict] | None = None,
                       counts: list[dict] | None = None,
                       choices: dict[str, list[str]] | None = None,
                       expect: list[dict] | None = None,
                       forbid: list[dict] | None = None) -> str:
    """The sheet the model must fill, generated from the .olx `slots` attribute.

    Checks the grader COMPUTES are listed separately and explicitly NOT asked for:
    they are absent from the response schema, so requesting them would be asking
    for something the model cannot supply.
    """
    equals = equals or []
    derived = derived or []
    counts = counts or []
    choices = choices or {}
    expect = expect or []
    computed = {r["key"]: r for r in equals}
    from_page = {r["key"]: r for r in derived}
    # Counted members are derived from the count and are NOT in the response schema.
    # Listing them anyway asked the model for answers it could not return, alongside
    # the count that replaces them — two framings of the same judgement at once.
    counted = {k: cr for cr in counts for k in cr["slots"]}
    # An `expect` key is computed from a classification, so it is out of the
    # response schema exactly as an `equals` key is. Leaving it in the answerable
    # list made the prompt say "answer this" and "DO NOT ANSWER this" about the
    # same check.
    expected = {r["key"]: r for r in expect}
    # A `forbid` key is computed from a COMBINATION of answers, so like `equals`
    # and `expect` it is out of the response schema and must not be asked for.
    forbid = forbid or []
    forbidden_keys = {r["key"]: r for r in forbid}
    desc = {c["what"]: c["desc"] for c in item["credit"]}
    # `{fail}` is filled with the verdict THIS side offers. The rule text is
    # shared with score.py, whose vocabulary differs — web `wrong_kind` maps to
    # paper `not_active`, as enforcement.ALIAS records — so a rule naming one
    # side's token literally is unreadable on the other. It was: the paper
    # scorer was told when to answer `wrong_kind` while being offered
    # met/absent/not_active, so every test was inert and it credited p8's
    # "avoiding going the gym" that the web and CLI both reject.
    def _fail_token(slot_key: str) -> str:
        for sl in slots:
            if sl["key"] == slot_key:
                # The item-specific EXTRA verdict, not merely the first non-`met`
                # one: options run [met, absent, <extra>], and `absent` means the
                # box was empty, which is a different finding from wrong-kind.
                opts = [o for o in (sl.get("options") or []) if o not in ("met", "absent")]
                return opts[0] if opts else "absent"
        return "absent"
    rule = {c["what"]: c["rule"].replace("{fail}", _fail_token(c["what"]))
            for c in item["credit"] if c.get("rule")}
    lines = [
        "## The checklist to return (`checks`)",
        "Return a verdict for EVERY one of these, in this order, BEFORE you write",
        "`feedback` — a response can fail most of them and still read fluently. Each",
        "check's verdicts are listed with the satisfied one first, unless a note above",
        "says the check reports an identity rather than a judgement.",
        "",
    ]
    for s in slots:
        if (s["key"] in computed or s["key"] in from_page
                or s["key"] in counted or s["key"] in expected
                or s["key"] in forbidden_keys):
            continue
        # The rubric's own per-component `rule` comes FIRST. Slot-specific judging
        # text belongs in a slot-specific field on BOTH sides, and only the rubric
        # is read by both — SLOT_NOTES is web-only, so a rule parked there reaches
        # the web and CLI and silently leaves the paper scorer behind. That is
        # exactly what happened to Q4b's five substitution tests.
        note = (rule.get(s["key"])
                or SLOT_NOTES.get(f"{item_id}:{s['key']}")
                or SLOT_NOTES.get(s["key"])
                or desc.get(s["key"]))
        gate = " **GATE**" if s["gates"] else ""
        if s.get("picks") is not None:
            members = "/".join("`%s`" % o for o in choices.get(s["picks"], []))
            head = (f"- `{s['key']}`{gate} — one of {members} in `refers_to` "
                    f"(WHICH it is, not whether it is right)")
        elif s.get("count_max") is not None:
            head = (f"- `{s['key']}`{gate} — a NUMBER from 0 to {s['count_max']} "
                    f"(how many, not a judgement)")
        else:
            head = f"- `{s['key']}`{gate} — {'/'.join('`%s`' % o for o in s['options'])}"
        lines.append(f"{head}: {note}" if note else head)
    for key, r in forbidden_keys.items():
        spec = next((x for x in slots if x["key"] == key), None)
        gate = " **GATE**" if spec and spec["gates"] else ""
        pairs = ", ".join(f"`{c['slot']}` is `{c['value']}`" for c in r["conds"])
        lines += ["", f"DO NOT ANSWER `{key}`{gate}. The grader computes it from the "
                      f"checks above: it FAILS only when ALL of {pairs}, and passes "
                      f"otherwise — including when any of them is left unanswered. "
                      f"Answer each of those on its own terms and do not adjust one to "
                      f"suit another; the combination is arithmetic, not a judgement."]
    for key, r in computed.items():
        spec = next((x for x in slots if x["key"] == key), None)
        gate = " **GATE**" if spec and spec["gates"] else ""
        lines += ["", f"DO NOT ANSWER `{key}`{gate}. The grader computes it by comparing "
                      f"`{r['left']}` with `{r['right']}` — the two checks above that you "
                      f"DO answer. It is not in your schema, and the comparison is not a "
                      f"judgement you can make more accurately than the arithmetic can."
                  + (f" Where either is `{'` or `'.join(r['lenient'])}`, no mismatch is "
                     f"established and nothing is charged." if r["lenient"] else "")]
    for r in expect:
        spec = next((x for x in slots if x["key"] == r["key"]), None)
        gate = " **GATE**" if spec and spec["gates"] else ""
        lines += ["", f"DO NOT ANSWER `{r['key']}`{gate}. The grader computes it: it holds "
                      f"when `{r['left']}` is `{r['value']}`, which is the answer THIS item "
                      f"asks for. Report what you actually see in `{r['left']}` — if it is a "
                      f"different one of the four, say so there and say which in your note; "
                      f"the deduction follows from the arithmetic, not from your judgement "
                      f"about whether it is right."
                  + (f" `{'` or `'.join(r['lenient'])}` establishes nothing and is not charged."
                     if r["lenient"] else "")]
    for cr in counts:
        members = ", ".join(f"`{k}`" for k in cr["slots"])
        lines += ["", f"DO NOT ANSWER {members} individually. Answer `{cr['key']}` — HOW "
                      f"MANY you found — and the grader awards that many of them. Count "
                      f"them the way the guidance above says to, in one judgement over "
                      f"the whole response, rather than deciding each in isolation."]
    for key, r in from_page.items():
        spec = next((x for x in slots if x["key"] == key), None)
        gate = " **GATE**" if spec and spec["gates"] else ""
        if r.get("kind") == "present":
            body = ("The grader reads it off the page: it is satisfied when the "
                    "student has filled the field it names — a closed choice they "
                    "selected, which states the answer more reliably than prose "
                    "restating it would.")
        else:
            body = ("The grader reads it off the page, using the same code that draws "
                    "the chart: satisfied when EVERY week of data is present, `absent` "
                    "when a week is missing or they hold no numbers at all, and "
                    "`mismatch` when they are the worked example's own numbers rather "
                    "than a record of this student's behaviour. Copied WORDING is still "
                    "yours to judge, on the label checks.")
        lines += ["", f"DO NOT ANSWER `{key}`{gate}. {body} It is not in your schema, "
                      f"and none of it is a judgement — the runtime already knows."]
    if any(s["gates"] for s in slots):
        lines += [
            "",
            "A GATE that is not satisfied is the whole story for this item: report that "
            "finding and do not dress it up with the checks underneath it.",
        ]
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reading and rewriting the .olx.
# ---------------------------------------------------------------------------

_ACTION_RE = r'(<LLMAction\b[^>]*?\bid="%s"[^>]*>)(.*?)(</LLMAction>)'
# Any element that can carry a gradeable slot sheet. `DerivedChecks` carries one
# with no prompt at all, for items whose verdicts are facts about the student's
# fields rather than judgements about their prose.
_SHEET_RE = r'<(?:LLMAction|DerivedChecks)\b[^>]*?\bid="%s"[^>]*?/?>'


def _src(handout: int) -> str:
    with open(OLX % handout) as fh:
        return fh.read()


def _sheet_tag(handout: int, element: str) -> str:
    """The opening tag of whichever element carries `element`'s slot sheet."""
    m = re.search(_SHEET_RE % re.escape(element), _src(handout), re.S)
    if not m:
        raise SystemExit(f"no slot-sheet element id={element} in handout {handout}")
    return m.group(0)


def _slots_attr(handout: int, action: str) -> tuple[str, list[str]]:
    m = re.search(_ACTION_RE % re.escape(action), _src(handout), re.S)
    if m is None:
        tag = _sheet_tag(handout, action)
        spec = re.search(r'\bslots="([^"]*)"', tag)
        verd = re.search(r'\bverdicts="([^"]*)"', tag)
        return ((spec.group(1) if spec else ""),
                ([v.strip() for v in verd.group(1).split(",") if v.strip()]
                 if verd else default_verdicts()))
    if not m:
        raise SystemExit(f"no <LLMAction id={action}> in handout {handout}")
    tag = m.group(1)
    spec = re.search(r'\bslots="([^"]*)"', tag)
    verd = re.search(r'\bverdicts="([^"]*)"', tag)
    defaults = ([v.strip() for v in verd.group(1).split(",") if v.strip()]
                if verd else default_verdicts())
    return (spec.group(1) if spec else ""), defaults


# Mirrors slotSheet.ts:DERIVED_KINDS. A rule naming anything else is dropped on
# both sides, and DerivedChecks then reports the scored check left without a rule.
DERIVED_KINDS = tuple(next(p for p in primitives()["primitives"]
                           if p["attr"] == "derived")["kinds"])


def _counts_attr(handout: int, action: str) -> list[dict]:
    """`counts="key:member,member"` — one count standing in for its member checks."""
    m = re.search(r'\bcounts="([^"]*)"', _sheet_tag(handout, action))
    out = []
    for entry in (m.group(1) if m else "").split("|"):
        key, _, members = entry.strip().partition(":")
        ms = [x.strip() for x in members.split(",") if x.strip()]
        if key.strip() and ms:
            out.append({"key": key.strip(), "slots": ms})
    return out


def _derived_attr(handout: int, action: str) -> list[dict]:
    """`derived="key:ref,ref"` — checks read off the page, not asked of the model."""
    # `_sheet_tag`, not `_ACTION_RE`: a DerivedChecks element carries these rules
    # too, and matching only <LLMAction> returned silently empty for those.
    d = re.search(r'\bderived="([^"]*)"', _sheet_tag(handout, action))
    out = []
    for entry in (d.group(1) if d else "").split("|"):
        parts = [p.strip() for p in entry.strip().split(":")]
        key = parts[0] if parts else ""
        kind = parts[1] if len(parts) > 1 else ""
        targets = [t.strip() for t in (parts[2] if len(parts) > 2 else "").split(",")
                   if t.strip()]
        template = [[float(n) for n in g.split(",") if n.strip()]
                    for g in (parts[3] if len(parts) > 3 else "").split(";") if g.strip()]
        if key and kind in DERIVED_KINDS and targets:
            out.append({"key": key, "kind": kind, "targets": targets,
                        "template": template})
    return out


def check_scorer_voice_in_labels() -> list[str]:
    """A slot label the STUDENT reads must not address the scorer as "you".

    Slot labels are rendered verbatim by composeSlotFeedback — the model never
    rewrites them — so no amount of prompt guidance can fix one. That makes the
    voice of a label an AUTHORING property, and this the only place it can be
    enforced.

    The rubric's own voice is second-person-to-the-student throughout ("something
    you will physically do", "your unwanted target behavior"), which is correct
    and is why this cannot simply forbid "you". What it forbids is second person
    in the checks that are about the SCORER's own work: `confident` is the
    grader's self-report channel for WEB_SYSTEM rule 8, and it shipped reading
    "Any judgement you were unsure about" on all 23 sheets — telling the student
    they were unsure of a judgement they never made.

    (It was `uncertain`, answered no/yes with `no` as the good state, until the
    verdict standardisation un-inverted it: `met` now means every judgement was
    confident, which is what the rest of the vocabulary already meant by `met`.)
    """
    scorer_facing = ("confident", "uncertain")
    second_person = re.compile(r"\b(you|your|yours|yourself)\b", re.I)
    out = []
    for h in (1, 2, 3):
        src = _src(h)
        for m in re.finditer(r'slots="([^"]*)"', src, re.S):
            for entry in m.group(1).split("|"):
                parts = entry.split(":")
                if len(parts) < 2:
                    continue
                key = parts[0].lstrip("!").strip()
                label = parts[1].split("@")[0]
                if key in scorer_facing and second_person.search(label):
                    out.append(f"H{h}: `{key}` addresses the scorer as \"you\" in a "
                               f"label the student reads: {label!r} — use the first "
                               f"person (\"a judgement I was unsure about\")")
    return out


def check_template_matches_example(handout: int = 3) -> list[str]:
    """The `derived` template must be the worked example's own numbers.

    Those numbers live twice — in `bmod_h3_example_plot`'s data and in the
    attribute the grader compares against — because the plot is authored YAML and
    the attribute is a flat list. A copy is acceptable only if something binds it,
    so this fails `--check`/`--write` the moment they disagree; otherwise the
    grader would quietly stop recognising the example it is meant to catch.
    """
    src = _src(handout)
    m = re.search(r'<ObservablePlot\b[^>]*\bid="bmod_h3_example_plot".*?</ObservablePlot>',
                  src, re.S)
    if not m:
        return ["bmod_h3_example_plot not found; cannot verify the derived template"]
    by_week: dict[str, list[float]] = {}
    for wk, oz in re.findall(r'week:\s*"([^"]+)",\s*oz:\s*(-?[\d.]+)', m.group(0)):
        by_week.setdefault(wk, []).append(float(oz))
    plot = [by_week[k] for k in ("Baseline", "Week 1", "Week 2", "Week 3") if k in by_week]
    for r in _derived_attr(handout, ACTION["1c"]):
        if r["template"] and r["template"] != plot:
            return [f"derived template {r['template']} != example plot {plot}"]
    return []


def _forbid_attr(handout: int, action: str) -> list[dict]:
    fb = re.search(r'\bforbid="([^"]*)"', _sheet_tag(handout, action))
    return parse_forbid(fb.group(1) if fb else "")


def _equals_attr(handout: int, action: str) -> list[dict]:
    eq = re.search(r'\bequals="([^"]*)"', _sheet_tag(handout, action))
    return parse_equals(eq.group(1) if eq else "")


def _choices_attr(handout: int, action: str) -> dict[str, list[str]]:
    ch = re.search(r'\bchoices="([^"]*)"', _sheet_tag(handout, action))
    return parse_choices(ch.group(1) if ch else "")


def _expect_attr(handout: int, action: str) -> list[dict]:
    ex = re.search(r'\bexpect="([^"]*)"', _sheet_tag(handout, action))
    return parse_expect(ex.group(1) if ex else "")


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;")


def _to_xml(body: str) -> str:
    """Escape the prose, then expand the ref placeholders into <Ref> elements."""
    out = _escape(body)
    return re.sub(
        r"\x00REF:([^:]+):([^\x00]+)\x00",
        lambda m: '<Ref id="%s" target="%s" />' % (m.group(1), m.group(2)),
        out,
    )


def render(handout: int) -> tuple[str, dict]:
    """The .olx source with every generated prompt body substituted in."""
    src = _src(handout)
    minted: dict = {}
    for item_id, action in ACTION.items():
        if HANDOUT[item_id] != handout:
            continue
        body = _to_xml(build_web_prompt(item_id, minted))
        pat = re.compile(_ACTION_RE % re.escape(action), re.S)
        if not pat.search(src):
            raise SystemExit(f"no <LLMAction id={action}> in handout {handout}")
        src = pat.sub(lambda m: m.group(1) + "\n" + body + "      " + m.group(3), src, count=1)
    return src, minted


_REF_TAG = re.compile(r'<Ref\b[^>]*?id="([^"]+)"[^>]*?target="([^"]+)"[^>]*?/>')


def ref_delta(handout: int) -> tuple[list[str], list[str], list[str]]:
    """(dropped, added, duplicated) <Ref> ids between the file and the generation.

    A dropped ref is context the hand-written prompt passed and the rubric does
    not ask for; every one belongs in EQUIVALENCE.md's deviation list.
    """
    old = dict(_REF_TAG.findall(_src(handout)))
    new_src, _ = render(handout)
    new_pairs = _REF_TAG.findall(new_src)
    new = dict(new_pairs)
    dupes = [rid for rid in new if [r for r, _ in new_pairs].count(rid) > 1]
    return (
        sorted(f"{rid} -> {tgt}" for rid, tgt in old.items() if rid not in new),
        sorted(f"{rid} -> {tgt}" for rid, tgt in new.items() if rid not in old),
        sorted(set(dupes)),
    )


def _measurements_in_flight() -> list[str]:
    """Command lines of any harness process that is currently scoring cells.

    Both harnesses read the generated .olx per call, so rewriting it under a
    running one changes the prompt mid-measurement. Matched by module name rather
    than by a lock file: a lock is only as good as the last process to release it,
    and these runs are killed by hand often enough that a stale lock would train
    everyone to pass --force.
    """
    import subprocess

    try:
        out = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True,
                             text=True, check=False).stdout
    except Exception:                                   # pragma: no cover
        return []
    mine = str(os.getpid())
    busy = []
    for line in out.splitlines()[1:]:
        pid, _, args = line.strip().partition(" ")
        if pid == mine or "olx_prompts" in args:
            continue
        if ("agreement.py" in args or "agreement_app.py" in args) and "--items" in args:
            busy.append(" ".join(args.split()[:9]))
    return busy


_SECTION_RE = re.compile(r'<Vertical id="[^"]*" title="([^"]*)"')


def _changed_sections(old: str, new: str) -> list[str]:
    """Which handout sections does this regeneration change the text of?

    The in-flight guard above stops a write from CORRUPTING a run. This answers
    the question that comes after it: the write succeeded, so which items are now
    unmeasured? A prompt edit is not finished until its item has been swept and
    compared, and {{corpus:Q4b/p13:modify:45:63:sha=1d18e2ec5cf4}} reliably goes wrong is sweeping from memory —
    editing four SLOT_NOTES entries, remembering three, and reporting a baseline
    for an item whose prose moved underneath it.

    So attribute every changed line to the nearest enclosing <Vertical> title and
    report those. Titles rather than agreement item keys, deliberately: the keys
    differ per handout (Q1..Q6, S1..S10, 1a/1c/2a) and the mapping is another copy
    that can drift, whereas the title is read straight out of the text that
    changed and is unambiguous to the person who has to run the sweep.
    """
    def sections(text: str) -> list[str]:
        here, out = "(preamble)", []
        for line in text.splitlines():
            m = _SECTION_RE.search(line)
            if m:
                here = m.group(1)
            out.append(here)
        return out

    a_sec, b_sec = sections(old), sections(new)
    hit: list[str] = []
    sm = difflib.SequenceMatcher(None, old.splitlines(), new.splitlines())
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        for s in a_sec[i1:i2] + b_sec[j1:j2]:
            if s not in hit:
                hit.append(s)
    return hit


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", dest="show", choices=sorted(ACTION),
                    help="print one generated prompt (refs shown as <Ref .../>)")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the .olx files differ from what this generates")
    ap.add_argument("--write", action="store_true", help="rewrite the three .olx files")
    ap.add_argument("--diff", action="store_true", help="show what --write would change")
    ap.add_argument("--refs", action="store_true",
                    help="report <Ref> ids this generation drops, adds or duplicates")
    ap.add_argument("--force", action="store_true",
                    help="write even while a measurement is running (see the refusal)")
    a = ap.parse_args()

    # A --write while a run is IN FLIGHT silently splits that run across two
    # prompts. The cells already sent used the old text and the rest use the new,
    # so the .runs.json is a mixture of two configurations that nothing in it
    # records — and it reads exactly like a clean measurement.
    #
    # Done on 2026-08-24, on handout 3, by someone who had waited for two earlier
    # runs to clear for precisely this reason: 1a's baseline was 40 cells old
    # prompt and 20 new, and the two items behind it in the queue would have
    # measured the NEW prompt as their baseline. All three discarded.
    if a.write:
        busy = _measurements_in_flight()
        if busy and not a.force:
            print("REFUSING to write: a measurement is in flight and would be "
                  "split across two prompts.", file=sys.stderr)
            for b in busy:
                print(f"  {b}", file=sys.stderr)
            print("Wait for it, or re-run with --force if you know the run is "
                  "being discarded.", file=sys.stderr)
            return 1

    drift = _check_rules_still_match()
    for d in drift:
        print(f"WARNING: {d}", file=sys.stderr)
    # A copied constant with nothing binding it is the failure mode this project
    # keeps re-learning, so this one is fatal rather than a warning.
    bad = check_template_matches_example() + check_scorer_voice_in_labels()
    for b in bad:
        print(f"ERROR: {b}", file=sys.stderr)
    if bad:
        return 1

    if a.show:
        print(_to_xml(build_web_prompt(a.show)))
        return 0

    if a.refs:
        for h in (1, 2, 3):
            dropped, added, dupes = ref_delta(h)
            print(f"--- H{h}")
            for r in dropped:
                print(f"  DROPPED  {r}")
            for r in added:
                print(f"  ADDED    {r}")
            for r in dupes:
                print(f"  DUPLICATE ID  {r}")
        return 0

    if not (a.check or a.write or a.diff):
        ap.error("one of --print, --check, --write, --diff, --refs is required")

    rc = 0
    for h in (1, 2, 3):
        new, minted = render(h)
        old = _src(h)
        if minted:
            print(f"H{h}: minted {len(minted)} new ref id(s): "
                  + ", ".join(sorted(minted.values())), file=sys.stderr)
        if new == old:
            print(f"H{h}: up to date", file=sys.stderr)
            continue
        rc = 1 if a.check else rc
        if a.diff:
            sys.stdout.writelines(difflib.unified_diff(
                old.splitlines(True), new.splitlines(True),
                fromfile=f"h{h} current", tofile=f"h{h} generated"))
        if a.write:
            touched = _changed_sections(old, new)
            with open(OLX % h, "w") as fh:
                fh.write(new)
            print(f"H{h}: rewritten", file=sys.stderr)
            if touched:
                print(f"H{h}: UNMEASURED — prompt text changed under "
                      + "; ".join(touched), file=sys.stderr)
                print(f"H{h}: sweep those items and compare numerators against "
                      f"the last baseline BEFORE committing", file=sys.stderr)
        elif a.check:
            print(f"H{h}: OUT OF DATE — run olx_prompts.py --write", file=sys.stderr)
    return rc if a.check else 0


# --- corpus reference resolution (backdated) ---
# CONVERT HERE, DO NOT RESOLVE. What `--write` emits goes INTO the .olx, and the
# .olx is the file the reference mechanism exists to keep the words out of. This
# wrapper resolved, on the reasoning that the emitted text is what a web grader
# is sent -- but the grader is sent the BUILT page, and the build resolves on the
# way through, exactly as `_olx` does when the scorer reads the same file.
#
# Resolving here also does the very thing its old comment warned against: the
# generator writes words, the .olx holds a reference, and `--check` compares the
# two forms and reports every item out of date. Measured across the rewritten
# history: 42 of 113 generator+content states. Converting makes both sides carry
# the reference, so the comparison is like with like.
# A REFERENCE'S COLONS COLLIDE WITH THE SLOT-SHEET GRAMMAR, and the generator
# then misreads what it wrote itself. `slots=` is `name:description:verdicts@w`
# split on EVERY colon, so a description carrying
# `{{corpus:Q4b/p20:modify:17:40:sha=...}}` shifts every later field and the
# verdict list comes out as `Q4b`/`p20` instead of `met`/`absent`. Measured
# across the rewritten history before this shim: 107 of 114 generator states.
#
# Fixed HERE, backdated into every commit, because each commit runs its OWN
# generator and the old parser cannot otherwise be reached. The wrapper hides
# the colons INSIDE a reference while the original parser runs, then puts them
# back -- so the grammar is unchanged for everything that is not a reference,
# which is the narrowest fix that works.
try:                                            # pragma: no cover
    import re as _corpus_re
    _corpus_orig_parse_slots = parse_slots
    _CORPUS_REF_RE = _corpus_re.compile("[{][{]corpus:[^}]*[}][}]")
    _CORPUS_COLON = chr(0)   # no escape: this text is embedded in a non-raw string

    def parse_slots(spec, defaults, _orig=_corpus_orig_parse_slots):
        safe = _CORPUS_REF_RE.sub(
            lambda m: m.group(0).replace(":", _CORPUS_COLON), spec or "")
        out = _orig(safe, defaults)

        def _restore(v):
            if isinstance(v, str):
                return v.replace(_CORPUS_COLON, ":")
            if isinstance(v, list):
                return [_restore(x) for x in v]
            if isinstance(v, dict):
                return {k: _restore(x) for k, x in v.items()}
            return v

        return [_restore(d) for d in out]
except Exception:
    pass


try:                                            # pragma: no cover
    import corpus_resolve as _corpus_resolve
    _corpus_orig_web_prompt = build_web_prompt

    def build_web_prompt(*a, _orig=_corpus_orig_web_prompt, **kw):
        return _corpus_resolve.to_olx(_orig(*a, **kw), _corpus_resolve.load())
except Exception:
    pass


if __name__ == "__main__":
    raise SystemExit(main())
