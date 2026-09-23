#!/usr/bin/env python3
"""The generator tables, as authored — a BUILDER, outside the scoring pipeline.

STAGE 4 / A1c. These eleven tables were module-level data inside
`olx_prompts.py`, which made that module carry course content: 11 tables and 190
item ids by T1.1's count. The data now lives in the course file, and
`olx_prompts` reads it through `coursedata`.

WHY THE TABLES STILL EXIST HERE. `rubric_export.py` has to read them from
somewhere to WRITE the course file, and if it read them from `olx_prompts` --
which now reads the course file -- regenerating the course file would depend on
the course file it is regenerating. Stage 5 already anticipates this: *"Builders
survive OUTSIDE the pipeline as the tool that generates the expanded canonical
JSON."* This is that builder.

So: nothing in the scoring path imports this module. Only the export does. It is
authored input, kept in the form it was authored in, and the tables are carried
VERBATIM -- comments and all -- because a comment explaining why an item is in a
table is part of the authored record.
"""
from __future__ import annotations

# CARRIED WITH THE TABLES, because MATCH_DEF is built from it. The extraction
# took the tables and left this behind, and the module failed to import on its
# first run -- a NameError, which is the loud version of this mistake. A table
# is not self-contained just because it is a table.
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

# RULES NEITHER PROBE CAN CROSS-CHECK, which is NOT a list of scoring
# divergences and used to be filed as one.
#
# The enforcement audit verifies a rule two different ways. The web side READS
# declared rules off the .olx attributes; the CLI side PROBES, flipping answered
# fields and watching the score move. Those instruments have different reach, so
# each can find a rule the other cannot -- and when that happens the audit used
# to report it as "CHARGE-ONCE OLX ONLY" or "PYTHON ONLY", filed in
# SCORING_DIVERGENCES beside genuine prompt-and-scoring differences.
#
# BOTH HALVES OF THAT WERE WRONG. The name reads as a claim that a rule is
# enforced on one engine only, which would contradict the engine equivalence the
# whole pooled column rests on -- identical prompt bodies, identical request
# parameters, and 221 shared verdict signatures scoring identically. It is not a
# claim about the engines at all. Every entry that was ever filed here says so in
# its own words: "The behaviour is identical; what differs is what the instrument
# can reach." And the filing compounded the name: an audit-coverage gap listed as
# a scoring divergence gets read as one. It got read as one by the assistant that
# wrote it, twice in a day -- once reporting a probe gap to the user as a possible
# engine divergence and spending an hour disproving it.
#
# So an entry here records ONE fact: this rule's cross-engine agreement is
# ASSERTED, not probed. That is weaker than a probed rule and the entry should be
# read as the weaker thing. What backs it instead is
# enforcement.check_engines_score_identical_verdicts_alike, over the verdict
# signatures both engines have actually produced.
PROBE_REACH_LIMITS = [
    # NARROWED TO NR ALONE 2026-09-03. It listed NR, PR, PP and NP, and
    # check_probe_reach_limits_still_apply found on its first run that only NR
    # has the three-way `forbid` the excuse describes -- PR, PP and NP carry no
    # forbid at all, raise no charge-once finding, and were being excused for
    # nothing. An excuse wider than its justification silently claims the audit
    # checked three items it never had to.
    dict(items=["NR"],
         enforcement=[("NR", "CHARGE-ONCE PROBE GAP (cli)")],
         what="a three-way conjunction is invisible to the pairwise "
              "charge-once probe",
         why="`barrier_is_not_this_type` fails only when THREE readings coincide -- "
             "`restriction_authored`=created, `trigger_expects`=gain, "
             "`restricts`=other_thing -- and `onlyif` keeps it from charging on top "
             "of `demonstrates_type`, so both sides charge 2 once. The web reader "
             "sees that pair because it reads slot keys; the CLI probe discovers "
             "charge-once by flipping answered fields in PAIRS, and no pair of flips "
             "can satisfy a three-condition rule while the third field holds its "
             "passing value. So the CLI probe never reaches it. "
             "The behaviour is identical; what differs is what the instrument can "
             "reach. The cadence items carry the same conjunction and raise no such "
             "finding only because there it drives a GATE, and gates are discovered by "
             "single flips. Widening the probe to triples would multiply its cost by "
             "the number of inputs and is not worth it for one rule; this entry is "
             "the cheaper honest option, and it will stop applying if the rule ever "
             "becomes a gate."),
    dict(items=["2a"],
         enforcement=[("2a", "CHARGE-ONCE PROBE GAP (cli)")],
         what="a COMPUTED operand cannot be flipped, so the pair it makes "
              "sublinear is unreachable by probing",
         why="`requires` ties how_2 to `mechanism_named`, which carries no points of "
             "its own and costs something only by denying how_2. So the two share one "
             "2-point charge: failing either costs 2 and failing both still costs 2, "
             "which is what makes the pair sublinear. The web reader takes that "
             "straight from the declared `requires` rule. The CLI probe cannot: "
             "`mechanism_named` is computed by `forbid` from three answered grounds, "
             "so it is not an answered field and no flip can set it, and the state "
             "that would reveal the pair is never constructed. "
             "Same shape as the NR entry above and the mirror of its cause -- there a "
             "conjunction was too wide for a pairwise probe, here an operand is not "
             "probeable at all. Teaching the probe to synthesise computed-operand "
             "states would mean a second implementation of `forbid` living inside the "
             "instrument, which is how an instrument starts disagreeing with the thing "
             "it measures."),
]


# `ACTION` STOOD HERE AND IS DERIVED NOW -- `olx_prompts._action_from_rubric()`.
# It named the <LLMAction> each item is asked through, which is exactly what
# `<Item asks=...>` says in the rubric. The two agreed on all 23 items and
# nothing tied them, so one of them had to go; the rubric keeps it, because
# which component an item judges is a fact about the ITEM.

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
    # RETIRED 2026-08-28, the same day it was written. It declared that the
    # INSTEAD-OF test was prose on both sides with no primitive for the audit to
    # compare -- and that is no longer true: `behavior_1` and `behavior_2` are
    # COMPUTED from one declared `maps` rule each, which the enforcement audit
    # compares like any other primitive.
    #
    # Verified before retiring, 0 model calls: both engines return the same verdict
    # for every classification -- activity>met, none>absent, and consequence /
    # goal_behaviour / not_doing > wrong_kind -- and the codes follow, B_ONLY_ONE for
    # an empty box and the repeatable B_NOT_ACTIVE for a wrong entry. The two paths
    # no longer have a composite to read differently.
    #
    # WHAT IS NOT CLAIMED: that p4 and p12 now match gold. The classification is
    # still a judgement, so the paths can still differ on it -- one named question
    # instead of five weighed at once. That residual is declared as
    # enforcement.PROSE_ONLY_SLOTS Q4b.b1_basis/b2_basis, and the sweep measures the
    # numbers. REOPEN THIS if the sweep shows the two paths disagreeing on Q4b by
    # more than the pick can explain.
    #
    # The referent test is deliberately NOT part of this: it was measured in prose
    # form and rejected for three times the variance, and it stays subgoal 10 so the
    # mechanism change and the accuracy experiment are not confounded.
    {
        "what": "the web COMPUTES the nothing-listed gate; the CLI asks the model",
        "items": ["Q4a", "Q4c"],
        "necessary": True,
        "web_computes": {"Q4a": ["no_antecedents"], "Q4c": ["no_consequences"]},
        "enforcement": "same gate, reached differently: computed on the web, asked on the CLI",
        "why": "A_NONE and C_NONE -- 'no antecedents/consequences listed' -- take "
               "the whole item and could not be charged at all: `absent` on both "
               "entry slots maps to two -2 codes, so the item could not reach 0 "
               "where gold's dictionary says 0. They are now wired with `forbid`, "
               "which fails a check exactly when a COMBINATION holds: both entries "
               "`absent`. That is distinct from entries written but of the wrong "
               "kind, which the -2 codes charge -- Q4a/p20 is wrong_kind twice, "
               "gold 1, and is untouched. "
               "THE DIFFERENCE IS WHERE THE ANSWER COMES FROM, not what it does. "
               "`forbid` keys are stripped from the web response schema, so the "
               "web computes the check; the CLI's ledger is model-authored from "
               "the rubric, so it asks for it. Both then gate the item to 0. Same "
               "shape as 1b, T1/T2 and 1c, declared the same way. "
               "The web gate is real, not modelled: lo-blocks' pickGate requires "
               "`slot.gates && !sat[key] && charged[key]`, and chargedMap sets "
               "every slot true unless an `onlyif` suppresses it -- neither item "
               "has one -- so the third condition is a no-op here and the gate "
               "fires. Verified by scoring a synthetic both-absent sheet: 0.0 on "
               "both items. "
               "MEASURED INERT on the corpus: all 180 recorded sheets rescored "
               "through the new rules, 120 of 120 on Q4a and 60 of 60 on Q4c "
               "unchanged. No cell has both entries `absent`.",
    },
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
# WHY EACH ENTRY IS WEB-ONLY. Required beside every key in ITEM_NOTES: this
# table is WEB-ONLY BY CONSTRUCTION, and a note earns its place here only by
# saying something that is true of the web and not of paper. A note that could
# be said to BOTH graders is not a side note at all -- it is rubric content,
# and it belongs in `guidance` where both sides get it. Enforced by
# enforcement.check_side_notes_are_side_specific.
ITEM_NOTES_WHY: dict[str, str] = {
    "Q1": "Governs the FIRST SENTENCE of the `feedback` field on a "
          "`matches_selected` mismatch. Paper has neither: its schema has no "
          "`feedback` property (score.compose_feedback builds feedback in code "
          "from the deduction ledger) and `matches_selected` is not one of its "
          "Q1 slots.",
    "Q6": "Explains the web's TWO-FIELD encoding -- a `verdict` and a separate "
          "`refers_to` that takes `first`/`second`/`none`. Paper has one field "
          "and is told so in its own words by score._paper_vocab: 'Answer with "
          "ONE value from `first`, `second`, `neither`, `absent` -- there is no "
          "separate field on this side.' Mirrored in substance, not copied.",
    "1c": "Describes SelfMonitorPlot drawing the chart live from 1b's data, and "
          "the worked example sitting on the same screen. The paper student "
          "draws their own figure; there is no component and no screen.",
}


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
        "it. What IS yours is when only the WORDING is copied — a title of 'Water Consumption Over "
        "{{corpus:1c/p5:title:22:32:sha=65ebb904a388:shape=R10-0-27}} from a student who did not track water, or a y-axis of 'Ounces of "
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


# ---------------------------------------------------------------------------
# STAGE 4, from `agreement.py`. Per-handout REFERENCE MAPS: the OLX component
# ids whose values are handed to the grader as context for an item, keyed by
# component id rather than by item, because one component can be context for
# several items and several components can be context for one.
#
# Carried whole and course-level for that reason: a map keyed by something
# other than an item id has no item entry to live on.
# ---------------------------------------------------------------------------
_H1_CTX = {
    "bmod_h1_utb": "Q1",
    "bmod_h1_q1_response": "Q1",
    "bmod_h1_q2_response": "Q2",
    # The five SMART boxes are one blob on paper; the first ref takes it and the
    # rest say so (see CONTINUED).
    "bmod_h1_q3_specific": "Q3", "bmod_h1_q3_measurable": "Q3",
    "bmod_h1_q3_action": "Q3", "bmod_h1_q3_realistic": "Q3",
    "bmod_h1_q3_timebound": "Q3",
    "bmod_h1_q4a_first": "Q4a", "bmod_h1_q4a_second": "Q4a",
    "bmod_h1_q4b_first": "Q4b", "bmod_h1_q4b_second": "Q4b",
    "bmod_h1_q4b_modify": "Q4b",
    "bmod_h1_q4c_first": "Q4c", "bmod_h1_q4c_second": "Q4c",
    "bmod_h1_q5_first": "Q5", "bmod_h1_q5_second": "Q5",
    "bmod_h1_q6_first": "Q6", "bmod_h1_q6_second": "Q6",
}

_H2_CTX = {
    "bmod_h1_utb": "_utb",
    "bmod_h1_q2_response": "_wgb",
    "bmod_h2_t1": "T1", "bmod_h2_d1": "D1",
    "bmod_h2_t2": "T2", "bmod_h2_d2": "D2",
    "bmod_h2_pr": "PR", "bmod_h2_nr": "NR",
    "bmod_h2_pp": "PP", "bmod_h2_np": "NP",
    "bmod_h2_day1": "DAY1", "bmod_h2_wk1": "WK1",
    "bmod_h2_day2": "DAY2", "bmod_h2_wk2": "WK2",
}

# A value of the form "hN:ITEM" comes from a DIFFERENT handout's submission by
# the same participant. Handout 3's assessment item asks the student to reflect
# on the operant-conditioning types they chose back in handout 2, and on paper
# those live in a different file.
_H3_CTX = {
    "bmod_h3_baseline": "1b", "bmod_h3_wk1": "1b",
    "bmod_h3_wk2": "1b", "bmod_h3_wk3": "1b",
    "bmod_h3_overview_response": "1a",
    "bmod_h3_success_verdict": "2a", "bmod_h3_success_how1": "2a",
    "bmod_h3_success_how2": "2a",
    "bmod_h3_assessment_response": "2b",
    "bmod_h3_improve_first": "3", "bmod_h3_improve_second": "3",
    "bmod_h3_graph_title": "1c", "bmod_h3_graph_x": "1c", "bmod_h3_graph_y": "1c",
    "bmod_h2_t1": "h2:T1", "bmod_h2_t2": "h2:T2",
    "bmod_h1_q2_response": "h1:Q2",
}
