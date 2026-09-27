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
# STAGE 4, from `forms.py`. THE THREE FIELDS OF `HANDOUTS` THAT ARE
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
# Handout-level course facts. J-4 widened this from three fields to eight:
# the three PATH fields are stored as LEAVES -- the file name and the
# directory name -- because the bases (`MATERIALS`, `SUBS`, `OUT`) are where
# THIS MACHINE keeps course data, not a fact about the course. `forms.py`
# joins them. Storing absolute paths would mean relocating $COURSE_DATA
# required a course-file edit.
#
# `markers` is deliberately NOT here: `forms.py` takes it from `segment`,
# which already reads it from the course file, so the two are the same
# object rather than two copies.
# NOT RENAMED TO `FORM_FIELDS`, AND THE REVERT IS THE POINT. This name is
# simultaneously an identifier and a PERSISTED RECORD KEY: `course.json` stores
# the table under `HANDOUT_FIELDS`, `forms.py` reads
# `coursedata.declaration("HANDOUT_FIELDS")`, and `rubric_export` exports it by
# that name. The E58 identifier pass renamed it because a token scan sees only
# an identifier, and renaming it here silently unpaired the authored table from
# its record -- which `check_migrated_tables_match_their_source` did NOT report,
# because it pairs by name and an unpaired table simply drops out.
#
# Record keys move in E58 step 3, with a reader that accepts both spellings.
# ── WHY HANDOUT 1 CITES WHOM, and why nine of the entries are now empty ─────
#
# MOVED HERE FROM `forms.FORMS` BY E58 STEP 3, 2026-09-25. It was 173 lines of
# comment wrapped around a `cited_participants` map inside the engine's handout
# table -- and the map itself is served from the course file, so what stood in
# `forms.py` was a shadow of this data with all of its reasoning attached to the
# copy nobody reads. The user's rule decides where it goes: comments about a
# table live with the table unless the table is generic, and nothing below is
# generic. Every sentence names this cohort's participants, this course's items
# and the probe numbers they were measured at.
#
# THE MAP IS `HANDOUT_FIELDS['1']['cited_participants']` below. This is its
# reasoning, verbatim, including the trailing per-item notes for the entries
# that were emptied -- an entry that went to `[]` is a decision with evidence
# behind it, not an absence.
#
# # A SECOND way a prompt can give the answer away, found by auditing every
# # item's prompt-bearing text for a participant cited by number.
# #
# # `exemplar_items` covers a response reproduced in full as a worked
# # example. This covers a response CITED as calibration — "falling asleep
# # in the car ... cost participant 20 three points" — which quotes the
# # answer AND states the grader's decision. That is an answer key for that
# # cell just as surely, so scoring the cited participant on that item is
# # self-grading too.
# #
# # Per item, because the sets differ: Q6 embeds p10/p8/p6, Q4b cites eight
# # entirely different participants. The handout-wide `exemplar_participants`
# # list cannot express that, which is why registering Q4b needed this.
# #
# # All ten qualifying items, registered together after the evidence came
# # in. Q4b was registered first, alone; measuring it then showed the whole
# # 21-point web/paper gap on that item was Opus reproducing answers held
# # in its prompt (7/7 on cited cells) where gpt-5-mini did not (4/7),
# # while on the cells that should be judged the three scorers were
# # equivalent — 12, 11 and 10 of 12. Leaving the other nine unregistered
# # would have kept that distortion in every handout-1 and handout-3 number.
# #
# # Reproduce with the audit in EQUIVALENCE.md: search each item's
# # prompt-bearing text for a participant cited by number. Handout 2 has
# # none — its guidance quotes answers without attributing them.
# # EIGHT CELLS CAME OUT 2026-08-23, on the same principle Q4b's note below
# # records, after the exclusion audit that step 1 of the cleanup procedure
# # asks for and that this campaign had skipped. Every excluded cell in the
# # handout was retested against its item's current configuration — free,
# # because excluded cells are still run and still scored — and eight were
# # WRONG in 3 of 3 runs with the answer and the grader's decision sitting in
# # the prompt. An exclusion there buys a flattering denominator and nothing
# # else, so the citation and the registration moved together:
# #
# #   Q1 p9   Q2 p7   Q4a p9, p14, p15   Q4c p9, p20   Q5 p4
# #
# # Each citation was rewritten as the RULE it was illustrating rather than
# # deleted, so the guidance keeps its content and loses the answer key.
# # Three of the eight (Q4a's) already carry declared divergences, so their
# # misses were always intentional and now simply count. EXPECT THESE FIVE
# # ITEMS' RATES TO FALL; that is what the step is for.
# #
# # The 21 cells that stayed are right in 3 of 3, which is what a
# # `self_graded` exclusion is FOR: with the answer in the prompt, getting it
# # right proves nothing, so the cell is uninformative rather than stale.
# # Section 5's retest-until-removed rule bites on `unscoreable` claims, not
# # on these.
# "cited_participants": {
#     # Q1 IS GONE FROM THIS MAP, and it is the worked example of the second
#     # half of step 0: an exclusion can be correct and still be unnecessary.
#     # All five of its registrations rested on bare attributions — "(participant
#     # 1)", "which is what participant 6 scored", "which is how participants 10
#     # and 16 were credited" — so deleting the attributions left every rule
#     # intact and the claim became testable.
#     #
#     # MEASURED, 3 runs with the citations gone: the 15 cells already counted
#     # held at 13, 13, 13, and four of the five cited cells stayed right 3 of 3.
#     # The citations were load-bearing for nothing, and the whole item scores
#     # 18, 17, 18 of 20 against the 13/15 it had been reporting. FIVE CELLS WE
#     # SCORE CORRECTLY had been subtracted from every rate on an untested claim.
#     #
#     # p10 is the exception and was kept out deliberately anyway. Probed at 6
#     # passes it is right 4 of 6 without its citation, against 3 of 3 with it —
#     # so that citation WAS doing work, and what it was doing was holding a
#     # coin-flip cell at 100%. Keeping the exclusion would mean keeping an answer
#     # key in the prompt to make one cell look stable, which is the opposite of
#     # what the registry is for. It counts, and it flips.
#     # Q2 IS GONE TOO, and its citations were the harder kind: quote plus
#     # verdict, not bare attribution. `wgb_inverts_utb` quoted p10's own goal
#     # and the two points it lost; `reasons_given` quoted p6's restatement and
#     # named p3 as having lost all three. Rewriting them as rules — a goal that
#     # names something ACQUIRED rather than the behaviour fails; a restatement
#     # of the goal is not a benefit of it — kept the teaching:
#     #
#     #   numerator, 17 counted cells   16, 14, 15  ->  15, 15, 17
#     #   whole item, 20 cells          18, 17, 18  ->  17, 17, 20
#     #
#     # p3 held at 3/3 and p6 IMPROVED, 2/3 -> 3/3, without the answer in front
#     # of it. p10 read 1/3 in the sweep, which looked like a load-bearing
#     # citation, and probed 5 of 6 with both controls at 6/6 — its scores are
#     # 3,3,3,3,0,3 against a gold of 3, so the failure is a rare zeroing gate
#     # rather than a steady refusal. Six of nine passes overall: a two-thirds
#     # cell, treated like Q1's p10 and counted.
#     #
#     # This item is genuinely noisy — a 3-cell spread before and after — so read
#     # its floor, not its mean.
#     # Q4a IS GONE, all four. Its citations were quote-bearing: the
#     # [[corpus Q4a/p3 second 24:67 sha=7ccb6f502905]] do-instead example, gold's
#     # own two opacity questions with p4 and p6 named, and the keyword
#     # inconsistency naming p17. Rewritten as rules — refuse a substitute
#     # activity or another route to the same end; ask whether a reader can see
#     # how THIS entry leads to THIS behaviour, an omission that could precede
#     # anything being the opaque shape — the numerator did not move at all:
#     #
#     #   numerator, 16 counted cells   12, 12, 12  ->  12, 12, 12
#     #   whole item, 20 cells          16, 16, 15  ->  15, 16, 15
#     #
#     # p3, p4 and p17 all held at 3/3 with no citation. p6 read 1/3 in the sweep
#     # and probed 5 of 6 — BETTER than the 2/3 it managed WITH its citation,
#     # which is the second cell in this pass to improve when its answer key was
#     # taken away (Q2's p6 went 2/3 -> 3/3). A citation naming one participant's
#     # verdict does not merely fail to help; it can pull the grader toward the
#     # wrong reading of a neighbouring judgement.
#     #
#     # p6's scores are 3,3,3,3,5,3 against a gold of 3: gold charges the opacity
#     # of "not stretching" leading to lack of exercise, and we now agree with it
#     # five times in six.
#     # Q4b IS GONE, and its three were the hardest of the pass. Its ACCEPT
#     # bullet quoted p13's own second entry and BOTH of p19's as the internal-state
#     # and coping-behaviour examples — three of the four accepted shapes lifted
#     # from two students the item then excluded, which is the circularity this
#     # registry exists to break. (An earlier round had already removed 2, 4, 6, 7
#     # and 20 for the opposite reason: the item could not score them even with the
#     # answer beside them. See EQUIVALENCE.md.)
#     #
#     # Three configurations, MEASURED, p15 at 6/6 as control throughout:
#     #
#     #                        p13    p19    numerator (17 counted)
#     #   quoting their words  67%    100%   14, 13, 13
#     #   my abstractions       0%      0%   13, 14, 14
#     #   invented examples    33%    100%   14, 14, 14
#     #
#     # The first rewrite replaced EXAMPLES with category descriptions and broke
#     # both cells outright — and it was narrower than what it replaced, excluding
#     # a state that "befell" the student when the original bullet accepted exactly
#     # that. The guide says examples must be INVENTED, not that they should become
#     # abstractions; reading it the second way cost two cells and two measurements.
#     #
#     # With concrete invented examples the item is steadier than it ever was with
#     # the quotes — 14 flat against 13-14 — so what those quotes contributed was
#     # CONCRETENESS, not the students' particular words. p19 recovered fully.
#     #
#     # p13 sits at 67% with its own words in the prompt and 33% with an invented
#     # near-equivalent: a coin-flip cell either way across nine passes. Counted,
#     # like Q1's and Q2's p10, and recorded as a cell whose apparent stability was
#     # its own answer key.
#     #
#     # Whole item, 20 cells: 16, 17, 16 — against the 13/16 this campaign opened
#     # with.
#     # Q4c IS GONE, all five, and it is the cleanest result of the pass: not one
#     # cell moved. Its citations were quote-bearing — p12's junk-food consequence
#     # as the ACCEPT example, gold's question to p4, p11's duplicate charge, p15
#     # and p17 named in the keyword note — and rewriting them as rules changed
#     # nothing whatsoever:
#     #
#     #   numerator, 14 counted cells   12, 12, 12  ->  12, 12, 12
#     #   whole item, 20 cells          17, 17, 17  ->  17, 17, 17
#     #   p4, p11, p12, p15, p17        3/3 each, before and after
#     #
#     # Five cells recovered at zero cost. p16 stays out as `unscoreable` — that is
#     # a claim about its gold row, not about the prompt, and its expect_error still
#     # matches its measurement — so the honest denominator is 19, at 17 of 19.
#     # Q5 IS GONE, all five, which empties this map for handout 1 entirely.
#     # Four of the five were named in ONE bullet — a list of four quoted answers
#     # with "every one of these scored full marks (participants 8, 9, 19, 20)" —
#     # plus p6's duplicate case and p9's thin-reason advisory.
#     #
#     #   numerator, 15 counted cells   14, 14, 14  ->  13, 14, 14
#     #   whole item, 20 cells          18, 19, 19  ->  18, 19, 19   (identical)
#     #   p6, p8, p19, p20              3/3, unchanged
#     #   p9                            2/3 -> 3/3, better without its answer key
#     #
#     # The numerator's single dip is p10, which no citation ever named: probed at
#     # 3 of 6 with controls at 6/6 and 5/6, so a true coin flip that had been
#     # reading 3/3 while the quoted list was in the prompt. A list of four
#     # students' answers was cueing a cell it did not name — the teaching effect,
#     # not recall — which is the strongest argument in this pass for writing
#     # examples rather than borrowing them.
#     "Q5":  [],
#     # Q6 is gone from this map: rewritten from the dictionary, its
#     # prompt cites no participant at all. Every cell on it is scoreable
#     # now except p9, which is unreachable for a declared divergence.
# },

HANDOUT_FIELDS = {'1': {'blurb': 'Handout 1 of the Behavior Modification Assignment: defining '
                'behaviours, the ABCs of a functional behavioural analysis, '
                'and SMART goals.',
       'capture_tail': False,
       'cited_participants': {'Q5': []},
       'exemplar_items': [],
       'exemplar_participants': [10, 8, 6],
       'outdir_name': 'h1',
       'submissions_dir': 'Handout 1 Submissions with Scoring and Feedback',
       'template_file': 'BMod Handout #1 - Defining Behaviors, ABCs, and '
                        'SMART Goals.docx'},
 '2': {'blurb': 'Handout 2 of the Behavior Modification Assignment: applying '
                "the four types of operant conditioning to the student's own "
                'behaviour-change plan.',
       'capture_tail': True,
       'exemplar_participants': [],
       'outdir_name': 'h2',
       'repair_orphans': True,
       'submissions_dir': 'Handout 2 Submissions with Scoring and Feedback',
       'suspect_participants': [2, 3],
       'template_file': 'BMod Handout #2 - Learning Operant Conditioning and '
                        'Applying It to Behavior Change.docx'},
 '3': {'blurb': 'Handout 3 of the Behavior Modification Assignment: '
                'presenting and graphing the data collected during the '
                'intervention, and analysing the result.',
       'capture_tail': True,
       'cited_participants': {},
       'exemplar_participants': [],
       'join_aware': True,
       'outdir_name': 'h3',
       'submissions_dir': 'Handout 3 Submissions with Scoring and Feedback',
       'template_file': 'BMod Handout #3 - Presenting Data, Graphing Data, '
                        '&amp_ Analyzing Your Intervention.docx'}}


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

# ── The operant vocabulary's SIDE MAP and PROBE FIXTURES (goal P) ────────────
#
# Moved out of `enforcement.py` 2026-09-24. They were engine code naming THIS
# COURSE'S FACTS -- `avoidance_frame`, `cadence_ok`, `targets_own_behavior` and
# seven more, across 60 code sites in five engine modules. A second course would
# have met an engine that already knew this course's psychology, which is the
# `bmod_handout1` defect one level in: not a file name this time, but the name of
# a thing the model is asked.
#
# The ENGINE may not name a fact. A COURSE must, and this is where it does it.
#
# SIDE_ALIAS: the same rule under its two names, web value second. An unmapped
# key is REPORTED, never assumed equivalent -- that rule stays in the engine
# because it is about how to treat a gap, not about which names exist.
SIDE_ALIAS = {'avoidance_frame': ('phrased_directly_gate', 'phrased_directly'),
 'baseline': ('baseline', 'baseline_data'),
 'behavior': 'names_behavior',
 'cadence_ok': ('cadence_is_daily',
                'cadence_is_daily_counted',
                'cadence_is_weekly'),
 'contingent_on_behavior': 'contingent',
 'is_np': 'demonstrates_type',
 'is_nr': 'demonstrates_type',
 'is_pp': 'demonstrates_type',
 'is_pr': 'demonstrates_type',
 'observed_type': ('demonstrates_type', 'observed_type'),
 'operant_behavior': 'names_behavior',
 'stimulus': 'names_stimulus',
 'stimulus_is_arranged': 'you_arrange_it',
 'stimulus_move': ('demonstrates_type', 'stimulus_move'),
 'targets_intended_behavior': ('targets_goal_behavior',
                               'targets_unwanted_behavior'),
 'week_1': ('week_1', 'week_1_data'),
 'week_2': ('week_2', 'week_2_data'),
 'week_3': ('week_3', 'week_3_data')}

# The one field whose SENSE flips between the sides. `SIDE_ALIAS` carries the
# NAME mapping and always could; the inversion was the half that was not
# machine-readable, so it was named in `measured.py` "here and nowhere else".
# Declared beside the names it belongs with, so both halves travel together.
SIDE_INVERTED = ['avoidance_frame']

# The synthetic probe sheets: the value of each fact on an answer that PASSES and
# on one that FAILS. The enforcement audit builds hypothetical sheets from these
# to prove a rule fires -- so they are this course's answers to this course's
# questions, and the comments explaining each choice travel with them.
PROBE_PASS = {'agent_delivers_consequence': True,
 'aimed_correctly': True,
 'avoidance_frame': False,
 'behavior': 'walking to class',
 'cadence_ok': True,
 'consequence_asserted': True,
 'contingent': True,
 'follows_behavior': True,
 'restriction_authored': 'relieved',
 'restricts': 'target_behavior',
 'states_a_contingency': True,
 'stimulus': 'a coffee',
 'stimulus_is_arranged': True,
 'stimulus_move': {'NP': 'taken_desirable',
                   'NR': 'taken_undesirable',
                   'PP': 'given_undesirable',
                   'PR': 'given_desirable'},
 'targets_intended_behavior': True,
 'targets_own_behavior': True,
 'trigger_expects': 'gain'}

PROBE_FAIL = {'agent_delivers_consequence': False,
 'aimed_correctly': False,
 'avoidance_frame': True,
 'behavior': '',
 'cadence_ok': False,
 'consequence_asserted': False,
 'contingent': False,
 'follows_behavior': False,
 'restriction_authored': 'created',
 'restricts': 'target_behavior',
 'states_a_contingency': False,
 'stimulus': '',
 'stimulus_is_arranged': False,
 'stimulus_move': {'NP': 'taken_undesirable',
                   'NR': 'taken_desirable',
                   'PP': 'given_desirable',
                   'PR': 'given_undesirable'},
 'targets_intended_behavior': False,
 'targets_own_behavior': False,
 'trigger_expects': 'loss'}

# Handled separately by the audit: their failing value depends on the other, and
# a naive flip can make them agree again.
PROBE_TYPE_FIELDS = ['observed_type', 'named_type', 'trigger_behavior']
