#!/usr/bin/env python3
"""COURSE METADATA, as authored -- a builder, outside the pipeline.

Category II of `MATERIAL_CLASSIFICATION.md`: facts about THIS COURSE, as opposed
to records of how it was measured. Split out of `declaration_source.py` and
`generator_source.py` on 2026-09-23 because each of those held two categories at
once, which is why every "does this move to the OLX?" question needed a per-table
answer instead of a per-file one. These are the tables that MOVE toward the OLX
and `course.json`; what stayed behind in those two modules is category III and
stays put.

Same reason for existing as its parents had, and it is worth restating:
`rubric_export.py` must read the authored tables to WRITE the course file, and
reading them from a module that reads the course file would make regenerating
the file depend on the file being regenerated.

`CONTEXT_SOURCE` came from `declaration_source`, where its section header
introduced it alongside `PAPER_ITEM_NOTES`; that header now describes only what
remains there. `RESPONSE`, `CONTEXT` and `SHEET_ONLY` came from
`generator_source` and kept the "Fixtures" header that documents the first two.
"""
from __future__ import annotations


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


# ---------------------------------------------------------------------------
# STAGE 4, from `handouts.py`. THE THREE FIELDS OF `HANDOUTS` THAT ARE
# COURSE DATA, and only those. The table holds five different kinds of
# thing and only this kind belongs in the course file:
#
#   course data   blurb, capture_tail, exemplar_items,
#                 repair_orphans, join_aware                <- here
#   resolved path template, submissions, outdir            <- stay computed
#                 from paths.py; storing a resolved path bakes in one
#                 machine, which is what check_filesystem_locations_
#                 come_from_paths_py exists to stop
#   duplicate     markers, already in the course file as SEGMENT_MARKERS
#                 and verified identical -- derived, never stored twice
#   wiring        gold (a function), rubric (a module) -- not data at all
#   participants  cited_participants, exemplar_participants,
#                 suspect_participants                      -> the gold
#                 file under C1b
#
# THE THREE HANDOUTS DO NOT SHARE A SCHEMA, which is why each was read
# rather than one being taken as the pattern: h2 alone has
# `repair_orphans` and `suspect_participants`, h3 alone has `join_aware`,
# h1 alone has `exemplar_items`. Assuming uniformity would have left two
# course-data flags behind and carried neither.
# ---------------------------------------------------------------------------
HANDOUT_FIELDS = {'1': {'blurb': 'Handout 1 of the Behavior Modification Assignment: defining behaviours, the ABCs of a functional behavioural analysis, and SMART goals.', 'capture_tail': False, 'exemplar_items': []}, '2': {'blurb': "Handout 2 of the Behavior Modification Assignment: applying the four types of operant conditioning to the student's own behaviour-change plan.", 'capture_tail': True, 'repair_orphans': True}, '3': {'blurb': 'Handout 3 of the Behavior Modification Assignment: presenting and graphing the data collected during the intervention, and analysing the result.', 'capture_tail': True, 'join_aware': True}}


# Items scored from a slot sheet with NO prompt: every verdict is derived from
# the page, so there is no <LLMAction> and nothing for `--prompts` to compare.
# They are still audited for arithmetic (`--scoring`) and enforcement.
SHEET_ONLY = {"1b": "bmod_h3_data_checks",
              "T1": "bmod_h2_t1_checks", "T2": "bmod_h2_t2_checks"}


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
