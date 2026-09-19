#!/usr/bin/env python3
"""The scoring DECLARATIONS, as authored — a builder, outside the pipeline.

STAGE 4. These eight tables were module-level data inside `enforcement.py`, which
made the enforcement module carry course content. They are declarations ABOUT
THIS COURSE -- which slots are prose-only, which text was deliberately designed,
which verdicts go uncharged -- so they belong in the course file, and they are
read from it now.

WHY THEY STILL EXIST HERE, and it is the same reason `generator_source.py` does:
`rubric_export.py` must read the authored tables to WRITE the course file, and
reading them from `enforcement` -- which now reads the course file -- would make
regenerating the file depend on the file being regenerated.

THE ONES THAT DID NOT MOVE, AND WHY THAT LIST SHRANK. This used to read: five
tables stay in `enforcement.py` because `table_sensitivity.py` measured that
emptying them moves no check. That tool was retired on 2026-09-19 and its
figures withdrawn -- it reported a verifier that RAISES as an unread table,
compared finding COUNTS instead of contents, and emptied by `setattr` where a
verifier holding its own reference never saw the change. The established
`--probe-declarations` had solved all three.

Re-measured with it, of those five:

    COUNTABLE_EXEMPT         READ -- emptying it changes the output. MOVED.
    PROBE_UNREACHABLE_PAIRS  READ, and staying until the encoder can hold it:
                             its keys are (item, FROZENSET) pairs, and
                             `json.dumps` refuses a frozenset outright. Measured
                             rather than assumed -- an earlier note here said it
                             would "silently change every key type", which is
                             what the RAW `_jsonable` path does; the declaration
                             path raises TypeError and exports nothing. A loud
                             failure, not a quiet one, and a change to the
                             encoder rather than to this file.
    PROBE_PROVOCATIONS       READ, and staying: it is the probe's own fixtures.
                             It names items, but it is a fact about testing the
                             engine, not a declaration about the course.
    SLOT_STRUCTURE_FAMILIES  INCONCLUSIVE -- its verifier reports nothing on the
    HAND_AUTHORED_ATTRS      real table, so emptying and corrupting cannot be
                             told apart. The original caution stands for these
                             two: a migration nothing can check is a migration
                             nobody can trust.
"""
from __future__ import annotations

# `JOBS` composes screen ids from `paths.NS`, so the builder needs it. Noted
# rather than passed over: those ids therefore embed the course id --
# `edu.memphis.psych/bmod_h1_q1` -- which the course file already carries in its
# own `course` field. De-namespacing them is a real Goal-D improvement and a
# SEPARATE change: a move and a reshape done together cannot be attributed when
# one of them breaks.
import paths

# CARRIED WITH THE TABLES. DECOMPOSITION_DIVERGENCES is built from it, and the
# extraction left it behind -- a NameError on the first import, which is the
# loud version of this mistake. The same thing happened moving MATCH_DEF out of
# olx_prompts: a table is not self-contained just because it is a table.
# WHICH PRIMITIVE SET each "NOT CONVERTIBLE" claim was judged against.
#
# Convertibility is not an absolute property of a rule; it is a claim about what
# the available primitives can express, and the primitive set grows. `maps` did
# not exist a week ago, and when it landed it CHANGED what was convertible about
# Q4b's picks -- behavior_1/behavior_2 left this table entirely and the picks'
# reasons were rewritten to say so. Nothing forced that rewrite. It happened
# because one person was holding both pieces at once, which does not scale.
#
# So each entry records the set it was judged against, and the check fails when
# the registry no longer matches. It fires exactly once per primitive added,
# which is precisely when the answer can have changed.
#
# THIS IS NOT PRESSURE TO CONVERT. A re-judged entry that is still not
# convertible gets a new stamp and the budget stays 9. The point is that the
# claim is re-made deliberately rather than inherited.
_PRIMS_2026_08_29 = "counts,cover,derived,equals,expect,forbid,maps,onlyif,requires"

# Slots whose verdict rests on a per-slot RULE and on nothing computable: the
# prose channel, enumerated so it is known rather than merely suspected.
#
# Why declared and not just computed. The computation above tells you a slot is
# prose-judged; this says someone LOOKED. Q4b/p4 is why it matters: paper 2.0
# against web 3.5, gold 2.0, the two paths reading the same REJECT test
# differently, and nothing in the audit able to object because there is no textual
# difference to find. When the sweep's divergence table names one of these slots,
# the answer is "prose, and we knew"; when it names a slot NOT on this list, the
# arithmetic diverged and that is a bug.
#
# The budget ratchets like the others. A tenth entry means a new rule was written
# as prose where it could have been a primitive -- which is the choice subgoal 3
# spent seven conversions undoing -- so it has to be a decision, not a default.
# Each reason must answer ONE question: why is this not a primitive? A reason that
# merely describes the rule leaves the entry looking settled when it is a work
# item. CONVERTIBLE marks the ones that could become declarations -- those are the
# list's whole point, because a declaration is something the enforcement audit can
# compare between the two scorers and prose is not.
PROSE_ONLY_SLOTS = {
    # DECLARED 2026-09-12. Both are judged by a per-slot `rule` and by nothing
    # computable, which is what this table is for: saying so, rather than leaving
    # the audit to ask whether a primitive was forgotten.
    ("1c", "series_box_holds"):
        "A CLASSIFICATION OF WHAT THE STUDENT WROTE, which no page datum can "
        "supply. Its rule says `ONE ANSWER, naming what is in the box. Do not "
        "judge whether it makes a good legend -- say what it holds and the "
        "arithmetic follows`, and the four values it picks between -- "
        "period_names, other_real_names, software_placeholders, nothing -- are "
        "distinctions about the WORDS in the box, not about the data behind the "
        "chart. The arithmetic that does follow is already a primitive: `legend` "
        "is a `maps` target computed from this pick, so the computable half is "
        "expressed and this is the irreducible half. It is `reported: True` and "
        "carries no points, so nothing is charged on it directly.",
    ("DAY2", "targets_own_behavior"):
        "A TWO-CASE READING OF THE STUDENT'S CONDITION, stated in prose because "
        "the cases are about what the condition NAMES: `met` when the condition "
        "names the unwanted behaviour itself, OR when it names the goal "
        "behaviour and that goal is the unwanted one's counterpart. The second "
        "case needs the two behaviours compared for opposition, which is a "
        "judgement about meaning and not a comparison any field supports. WK1 "
        "expresses the same question as an `expect` over `trigger_behavior` "
        "because THERE the sheet asks for a parse of which behaviour the trigger "
        "names; DAY2's sheet has no such pick, so on this item there is nothing "
        "for a primitive to read. Worth 1 point.",
    ("Q3", "realistic"):
        "NOT CONVERTIBLE, and a FIRST DEFINITION rather than a conversion. "
        "`realistic` shipped THIRTY-ONE characters with no rule at all, while "
        "its scored siblings carried specific 35, time_bound 329, measurable "
        "731 and action_oriented 1404. A 351-character rule added 2026-09-09 "
        "took Q3 from 19/20 to 20/20 on BOTH sides, Q3/p13 crossing 5 of 12 to "
        "12 of 12 PERFECT. WHAT IT TESTS IS WHETHER A GROUND FOR REALISM WAS "
        "OFFERED AT ALL, at a deliberately low bar -- a thin or circular one "
        "still counts -- which is a judgement about the presence and shape of "
        "prose, not a relation between slots. No primitive expresses \"a reason "
        "was given, however weak\": `expect` compares answers, `equals` compares "
        "two picks, `counts` counts members, `maps` translates one pick. "
        "Declared because the check is right that it is prose-only.",
    ("Q4b", "b2_names_besides"):
        "NOT CONVERTIBLE. Asking what a box names BESIDES the goal behaviour's "
        "absence -- an act, a result, or nothing -- is a reading of what the "
        "sentence contains. There is no operand: the question is whether "
        "anything beyond the absence is present at all.",
    # behavior_1 and behavior_2 LEFT this list on 2026-08-28: they are computed by
    # `maps` now, not judged, so they are no longer prose-only. The prose did not
    # disappear -- it moved to the picks below, which is where the residual
    # divergence risk now lives, and it is one named classification instead of five
    # tests weighed at once.
    ("Q4b", "b1_basis"):
        "NOT CONVERTIBLE, and it is the operand rather than the rule: `maps` turns "
        "this classification into behavior_1's verdict arithmetically, so the "
        "COMBINING is declared and only the classification is read. What an entry "
        "IS -- an activity, a consequence, the goal behaviour displaced, a "
        "not-doing -- has no operands to compare, so it stays a judgement.",
    ("Q4b", "b2_basis"):
        "NOT CONVERTIBLE, same as b1_basis for the second example.",
    # SUBGOAL Q10, 2026-09-05. Same shape as the entries below: the slot was
    # given a rule at all for the first time, and a rule is what makes it
    # prose+rule.
    # SUBGOAL Q19, 2026-09-05. `consequence_1` and `consequence_2` were given a
    # rule for the first time; a rule is what makes them prose+rule.
    ("Q4c", "consequence_1"):
        "NOT CONVERTIBLE. The test has three heads -- a STATE the student ends "
        "up in, another ACTIVITY rescued by being taken up in the behaviour's "
        "place or by a stated endpoint, and a restatement of the behaviour -- and "
        "each is a reading of what a sentence NAMES. There is no operand to "
        "compare against: the endpoint head turns on whether a clause carries the "
        "reader on to a state, which no primitive expresses.",
    ("Q4c", "consequence_2"):
        "NOT CONVERTIBLE, same as consequence_1 for the second box.",
    # SUBGOAL Q33, 2026-09-05. The antecedent VERDICTS became primitives -- they
    # are computed by `maps` from these picks -- and the reading moved here.
    ("Q4a", "antecedent_kind_1"):
        "NOT CONVERTIBLE. Naming WHICH KIND of thing a box states -- something "
        "before the behaviour, something whose link to it cannot be seen, an "
        "aftermath, the goal behaviour not happening, a consequence already "
        "listed, or nothing -- is a reading of the sentence. The `unlinked` "
        "option in particular asks whether a reader can see how the entry leads "
        "to THIS behaviour, which has no operand anywhere. The verdict it feeds "
        "IS now computable, which is the point of the split.",
    ("Q4a", "antecedent_kind_2"):
        "NOT CONVERTIBLE, same as antecedent_kind_1 for the second box.",
    ("Q3", "measurable"):
        "NOT CONVERTIBLE. The question is whether the box NAMES something that "
        "holds the record, as against merely saying a count will be kept. That "
        "is a reading of what a sentence names and there is nothing to compare "
        "it against: no list of acceptable holders can be authored without "
        "quoting the cohort, which the leakage gate forbids and which would "
        "make the rule a lookup of this year's answers.",
    # `change_a1`/`change_a2` were listed here by subgoal Q47 on 2026-09-05 and
    # removed the same day: the rule that put them here was measured, lost six
    # perfect cells, never fired on its target, and was reverted. With no rule
    # they are bare descs again and not prose+rule. The record is in rubric_h1.
    ("Q6", "affect_c1"):
        "NOT CONVERTIBLE. `cover` already constrains WHICH listed entry is referred "
        "to; what is left is whether the answer states HOW the consequence is "
        "affected, which is a reading of a sentence's claim and has no operands to "
        "compare. Seven measured rule attempts are recorded in "
        "Q6_MATCHING_CEILING.md; none of them was arithmetic.",
    ("Q6", "affect_c2"):
        "NOT CONVERTIBLE, same as affect_c1 for the second consequence.",
    ("1a", "distinguishes_periods"):
        "NOT CONVERTIBLE as it stands. The test is whether the answer reports more "
        "than one point in time SEPARATELY -- a property of the whole response, not "
        "a relation between two answers. `counts` was considered and is exempted in "
        "COUNTABLE_EXEMPT: the weeks are named, not interchangeable, so `3 of 4` "
        "cannot say which is missing.",
    ("1a", "baseline_week"):
        "NOT CONVERTIBLE, same COUNTABLE_EXEMPT reason. Migrated out of SLOT_NOTES "
        "on 2026-08-28, where it reached the web and not the paper scorer and cost "
        "1a/p6 the whole item in 3 of 3 runs.",
    ("1a", "week_1"):
        "NOT CONVERTIBLE, same reason: arc-not-label coverage is judged over the "
        "narrative, and no operand pair expresses it.",
    ("1a", "week_2"): "NOT CONVERTIBLE, same as week_1 for the middle stretch.",
    # ARRIVED 2026-08-29 with the E11 migration of five Q2/Q5 notes, and the trade
    # is deliberate: the rule used to reach two scorers of three SILENTLY, and now
    # reaches all three and is declared as prose the audit cannot compare.
    # PROSE_ONLY_SLOTS growing is the price of that visibility, not a regression --
    # an undeclared asymmetry became a declared symmetry.
    ("Q2", "wgb_is_counterpart"):
        "NOT CONVERTIBLE. The WGB_UNRELATED test asks whether the goal behaviour "
        "is about a DIFFERENT behaviour from the unwanted one -- a judgement about "
        "what two pieces of prose are ABOUT, with no operand pair that expresses "
        "it. `cover` cannot help: there is no list to pair against.",
    # ("Q2", "wgb_inverts_utb") REPLACED 2026-09-05 by ("Q2", "wgb_names").
    # Subgoal Q43 converted the slot itself into a PRIMITIVE: its verdict is now
    # computed by `maps` from the `wgb_names` pick, so it no longer carries a
    # prose-only rule and the audit can compare it between the two scorers. The
    # prose moved one slot along rather than disappearing, which is why the
    # budget does not fall -- but the judging is now a classification the engine
    # scores, which is what this list exists to encourage.
    ("Q2", "wgb_names"):
        "NOT CONVERTIBLE. Naming WHICH KIND of thing a goal states -- a doing, "
        "the condition that doing it produces, a general condition, a countable "
        "target, a different activity, or nothing -- is a reading of what the "
        "sentence names, and there is no operand to compare it against. The "
        "verdict it feeds IS now computable, which is the point of the split.",
    ("Q2", "reasons_failing"):
        "NOT CONVERTIBLE as it stands, and it is a COUNT of judgements rather than "
        "a judgement: how many listed statements are not a benefit of the goal "
        "behaviour. `counts` already expands the members; what it cannot express "
        "is the test each member is counted against.",
    # Q1's twin of the entry above, added 2026-09-05 with subgoal Q14's structural
    # fix. The two are the SAME SLOT on two items by construction: Q1's
    # `benefits_listed` was counting AND judging, and the remedy was to give it the
    # split Q2 already had. So the argument transfers verbatim rather than being
    # re-derived, and if one of them ever converts, both should.
    ("Q1", "benefits_failing"):
        "NOT CONVERTIBLE as it stands, for exactly the reason Q2.reasons_failing "
        "is not: it is a COUNT of judgements rather than a judgement -- how many "
        "of the statements counted as benefits name the GOAL instead of a good it "
        "brings. `counts` expands the members; what no primitive expresses is the "
        "test each member is counted against.",
    ("D1", "defines_type"):
        "NOT CONVERTIBLE. The slot classifies a DEFINITION into PR/NR/PP/NP by "
        "reading what it says -- something added or removed, behaviour increased "
        "or decreased. That is a reading of prose, with no operands to compare. "
        "What IS computed is the next step: `equals` pairs this verdict against "
        "`named_type` to derive `matches_chosen_type`, so the COMBINING is already "
        "a primitive and only the classification is judged. The rule's operative "
        "half -- do not look at what they chose -- exists to keep the two inputs "
        "independent, which no primitive can enforce about a model's attention.",
    ("D2", "defines_type"):
        "NOT CONVERTIBLE, same as D1: one factory builds both.",
    ("1a", "week_3"): "NOT CONVERTIBLE, same as week_1 for the final stretch.",
    # ARRIVED 2026-08-30, closing E11's last three entries. Same trade again, and
    # this time the asymmetry it ended was the widest: all three rules had reached
    # the WEB ONLY, from SLOT_NOTES, so the paper scorer was never given them.
    # These three appearing here is the audit seeing a judgement it could not see
    # before, not a new judgement being made.
    ("Q5", "example_2"):
        "NOT CONVERTIBLE, and on two counts. Whether a second entry is genuinely "
        "DIFFERENT from the first is a semantic relation between two free-text "
        "spans -- the same shape as Q2:wgb_inverts_utb and the `refers_to` channel "
        "that Q6_MATCHING_CEILING.md records seven failed wordings against. "
        "Whether an entry is a payoff for CONTINUING or an EFFECT of the behaviour "
        "is a second reading, of one span against no operand at all. `cover` "
        "cannot pair them: both spans are free text, and neither is a list.",
    ("Q5", "reasons_substantial"):
        "NOT CONVERTIBLE, and it is a judgement of DEGREE, which is the one shape "
        "no primitive here expresses: whether a reason that is present, distinct "
        "and a real payoff is nonetheless thin. There is nothing to compare it "
        "against -- not a list, not a sibling verdict, not a count. It is also "
        "`reported`, never scored, so no arithmetic depends on it; what it feeds "
        "is the feedback sentence.",
    # ARRIVED 2026-08-30 with E15, and it is the SLOT the `requires` rule needs:
    # link_c2 is what the sheet asks so `requires` has something to act on.
    ("Q6", "link_c2"):
        "NOT CONVERTIBLE, and it is the OPERAND rather than the rule -- the same "
        "shape as Q4b's b1_basis. `requires` turns this answer into a denial of "
        "state_c2 and affect_c2 arithmetically, so the COMBINING is declared and "
        "only the reading is judged. What is judged is whether two effect boxes "
        "are about the same consequence: a semantic relation between two "
        "free-text spans, with no operands to compare. `cover` cannot stand in "
        "for it -- it says which 4c entry each STATE box names and cannot speak "
        "for the effect boxes. Until 2026-08-30 this test lived as prose on "
        "affect_c1 and affect_c2, reaching every scorer as a request none could "
        "act on.",
}


PROSE_ONLY_JUDGED_AGAINST: dict[tuple[str, str], str] = {
    # Stamped 2026-09-12 against the registry as it stands today, which is the
    # same nine attributes as 2026-08-29 -- no primitive has been added since, so
    # these two claims are judged against everything that exists. If one is added,
    # both expire and must be re-read rather than assumed to survive it.
    ("1c", "series_box_holds"): _PRIMS_2026_08_29,
    ("DAY2", "targets_own_behavior"): _PRIMS_2026_08_29,
    ("Q3", "realistic"): "counts,cover,derived,equals,expect,forbid,maps,onlyif,requires",
    # Stamped 2026-09-06 against the registry as it stands. Subgoal
    # Q18: each of these is a READING that survives every primitive above --
    # the computable half of the change family moved OUT into `maps`, and what
    # is left is the classification the map reads.
    ("Q4b", "b2_names_besides"): "counts,cover,derived,equals,expect,forbid,maps,onlyif,requires",
    ("Q4b", "b1_basis"): _PRIMS_2026_08_29,
    ("Q4b", "b2_basis"): _PRIMS_2026_08_29,
    ("Q4c", "consequence_1"): _PRIMS_2026_08_29,
    ("Q4c", "consequence_2"): _PRIMS_2026_08_29,
    ("Q4a", "antecedent_kind_1"): _PRIMS_2026_08_29,
    ("Q4a", "antecedent_kind_2"): _PRIMS_2026_08_29,
    ("Q3", "measurable"): _PRIMS_2026_08_29,
    ("Q6", "affect_c1"): _PRIMS_2026_08_29,
    ("Q6", "affect_c2"): _PRIMS_2026_08_29,
    ("1a", "distinguishes_periods"): _PRIMS_2026_08_29,
    ("1a", "baseline_week"): _PRIMS_2026_08_29,
    ("1a", "week_1"): _PRIMS_2026_08_29,
    ("1a", "week_2"): _PRIMS_2026_08_29,
    ("1a", "week_3"): _PRIMS_2026_08_29,
    ("D1", "defines_type"): _PRIMS_2026_08_29,
    ("D2", "defines_type"): _PRIMS_2026_08_29,
    ("Q2", "wgb_is_counterpart"): _PRIMS_2026_08_29,
    ("Q2", "wgb_names"): _PRIMS_2026_08_29,
    ("Q2", "reasons_failing"): _PRIMS_2026_08_29,
    ("Q1", "benefits_failing"): _PRIMS_2026_08_29,
    # Judged on 2026-08-30 against the SAME registry -- `requires` was the last
    # primitive added and it predates both dates -- so they carry the same
    # constant rather than a new one spelling out an identical string. The check
    # compares SETS, not dates: a second name for one set would be a mirror, and
    # mirrors here drift.
    ("Q5", "example_2"): _PRIMS_2026_08_29,
    ("Q5", "reasons_substantial"): _PRIMS_2026_08_29,
    # `requires` is not a new primitive, only a newly USED one, so the same set.
    ("Q6", "link_c2"): _PRIMS_2026_08_29,
}


# Items whose response is deliberately carried in more than one box, with why.
MULTI_BLOCK_DECLARED: dict[str, str] = {
    # Examined box by box in this session and confirmed against each response's
    # own structure. The web version presents these as separate input fields, so
    # the split is the form's, not an artefact of reconstruction.
    "Q6": "eight boxes: two antecedents, each with its change, consequence and "
          "effect. Every cell read out and corrected; all fixture checks clean. "
          "p18\'s two antecedent boxes are DECLARED as sentence fragments and "
          "are correct that way: `state_a1` ends on its comma ([[corpus Q6/p18 state_a1 0:50 sha=c9250d345b28]]) and `state_a2` opens "
          "lowercase ([[corpus Q6/p18 state_a2 0:60 sha=c6293ae612e6]]), because p18 names each antecedent in a subordinate "
          "clause and puts the change in the main one. A clause-level split has "
          "to cut there; both boxes name their antecedent, which is what "
          "`state_a*` is scored on; and gold\'s 7.5 charges only the second "
          "consequence\'s fate. Both halves of one sentence being fragments is "
          "fine — do not re-cut them. Not in FIXTURE_STRUCTURE_OVERRIDES "
          "because no check fires on it, and an entry there that stops firing "
          "is reported stale",
    "Q3": "five boxes, one per SMART aspect, and the students label them "
          "themselves. Anchored on the aspect's own name where the scorer gave "
          "no quote; 9 cells with an empty box reduced to 1, and that one is "
          "correct — p9 never mentions realistic. NOT read box by box when it "
          "was declared, and p19 is what that cost: `measurable` held the "
          "printed instruction \"You must discuss and label each aspect of the "
          "SMART goal for full credit.\" and `specific` held the printed "
          "question plus two aspects, with the student's own measurable "
          "sentence inside it. Repaired; the two lines of template scaffolding "
          "now belong to no box. p6 still opens all four of its boxes with the "
          "student's \"- \" bullet, which is the corpus-wide residue and "
          "enumerator work in scoring/BACKLOG.md",
    "Q4b": "three boxes: the modify statement and two examples. p7 read out and "
           "assigned; the rest carry no findings",
    "1c": "eight boxes and not one of them a quotation, which is why the "
          "box-by-box readout is BLIND here: 18 of 20 cells have no prose at "
          "all, so `--fixture 1c` prints \"empty response\" and shows nothing. "
          "Audited by reading the eight boxes against the chart instead. Four "
          "come from `sim` (the four weeks of data) plus `series`, all parsed "
          "values; three — title/x/y — are read off the GRAPH by the paper "
          "scorer. Those three were the defect: in 10 of 20 cells they held the "
          "scorer\'s own sentence about the label (\"Weeks\" appears as a bolded "
          "axis title centred beneath the day tick values.) or its extracted "
          "text RUNS ([\'Time\', \' {{corpus:1c/p6:title:5:27:sha=951281e2eda4}} Weeks\']) instead of "
          "the label. Fixed in `_quoted_span`, not per cell, and verified "
          "against the served fixtures of all 26 items: exactly 20 boxes move, "
          "all of them 1c\'s. p15 and p18 are empty by right (gold \"did not "
          "include\"), and p11\'s day-name `series` is the student\'s own "
          "legend",
    "3": "two boxes, one proposed change each, and the count is judged over the "
         "whole response, so an empty `second` costs nothing by itself. All 20 "
         "read out; five repaired (p4, p6, p9, p16, p19), all one defect — "
         "`second` opened with a sentence elaborating the FIRST change, so box "
         "2 began before change 2 did. Boundaries moved to the sentence that "
         "opens change 2; the union of each pair is unchanged. Four cells hold "
         "everything in `first` with `second` empty: p5, p8 and p15 propose one "
         "change or none, which is what gold charges, but p3 is a real gap — its "
         "two changes sit in ONE sentence and no anchor separates them, so a "
         "6.0 is being earned from box 1 alone. 15 of 20 `first` boxes still "
         "open with the printed question\'s own \") \", which is template "
         "residue and NOT the student\'s word; it is corpus-wide and fixed "
         "upstream, not here (see scoring/BACKLOG.md)",
    "Q5": "two boxes, one reason each. All 20 read out; three boxes repaired, "
          "the same enumerator defect as Q4c — p1 kept \"1) \"/\"2) \" and p16 "
          "the \"2. \" it alone writes. Two cells are BLANK (p13, p17), so both "
          "boxes are empty and gold\'s \"did not answer\" is what the split "
          "reproduces. Three cells are run-ons split where the student\'s own "
          "sentence boundary is missing (p9, p15, and p3, whose orphaned full "
          "stop is left where the scorer\'s quote ended). p5 and p6 keep each "
          "reason\'s parenthetical function label (\"(Gaining something.)\", "
          "[[corpus Q5/p6 first 118:142 sha=9a07ac713b57]]) with the reason it labels, which is what "
          "the question asks the student to supply. p4\'s first box reads \"{{corpus:Q5/p4:first:0:1:sha=a83dd0ccbffe:shape=R1-0-20}}"
          "{{corpus:Q5/p4:first:2:23:sha=400cd580a803}}\" — checked against the submission, that is the "
          "student\'s own missing negation, not a transcription loss",
    "Q4c": "two boxes, one consequence each, and like Q4a the student usually "
           "does the splitting. All 20 read out; three boxes repaired, all one "
           "defect — p13\'s `first` and both of p16\'s kept the enumerator "
           "inside them while the item\'s other eight enumerated cells strip "
           "theirs. Three cells are split with no marker at all, and each is a "
           "run-on where the student\'s sentence boundary is simply missing "
           "(p5, p6, p15); p9\'s is the one genuine judgement — one comma, and "
           "\"while not exercising\" is left with the clause the comma attaches "
           "it to. p13\'s `second` is empty and faithful: gold charges the "
           "missing second consequence. p11\'s boxes follow DOCUMENT order, not "
           "the student\'s own labels, which run \"Another\" then \"One\"",
    "Q4a": "two boxes, one antecedent each, and in 12 of 20 cells the STUDENT "
           "does the splitting — \"1)\"/\"2)\", \"1.\"/\"2.\", or \"My first "
           "antecedent\"/\"My second trigger\". All 20 read out; no repairs. The "
           "only text belonging to no box anywhere in the item is enumerators "
           "and OCR debris (\"1)_\", \"2 )_\", \"-\", a bare \"o\", a leading "
           "\"_\"), and every box is whole sentences in document order. p15 is "
           "the one cell split with no marker at all — one run-on line, cut "
           "before its second antecedent — and both halves are phrases the "
           "item\'s own guidance quotes as accepts. p18 is a DECLARED DIVERGENCE "
           "from verbatim reproduction, not an oversight: it wrote one "
           "antecedent and repeated it word for word as its second, and the "
           "fixture deliberately leaves `second` EMPTY rather than serving the "
           "duplicate. Gold charges the missing one, so "
           "`_gold_corroborates_absence` licenses the gap on every run and no "
           "check fires; the divergence is from faithfulness, not from gold, "
           "which is why it is not in GOLD_DIVERGENCES. Filling the box would "
           "invite the grader to credit two antecedents on one, against a cell "
           "that agrees with gold at 3.0 in 6 of 6 passes. The keyword point "
           "survives every split, including the "
           "three cells that misspell it in one box and spell \"trigger\" in the "
           "other",
    "2a": "three boxes: the verdict and two explanations, which the screen asks "
          "for as three separate fields. All 20 cells read out against the "
          "response. Two repaired here — p16's how2 still carried the "
          "\"Sentence 3:\" label the other two boxes had stripped, and p20's "
          "how1 was a comma-initial adjunct sliced out of the verdict's own "
          "sentence (now the whole sentence, overlap declared). Everything else "
          "confirmed, including the boxes that hold text gold says is not an "
          "explanation: p13's how2 holds its \"{{corpus:2a/p13:how2:0:28:sha=2fa2e12271d7:shape=R28-0-20}}"
          "{{corpus:2a/p13:how2:29:46:sha=aaccc09e897f}}\" because the student wrote it, and gold charges "
          "that sentence rather than a missing one. The item's remaining error "
          "is almost all one shape and none of it is the fixture: 14-16 of 18 "
          "counted over six passes, and every miss but one is +2.0 for a "
          "second how gold withheld. The exception is p18, which flipped "
          "to 4.0 in one pass of six once its exclusion was removed",
    # Declared on PROVENANCE, not on a cell-by-cell reading, and the distinction
    # is the whole reason these two are cheap. Neither item's response was ever
    # PARTITIONED: nothing decided where one box ends and the next begins, so
    # there is no boundary to misplace. Contrast Q6, Q3, Q4b above, and the five
    # items still undeclared — each of those carves several boxes out of one
    # prose block, which is what put how1's sentence in 2a/p18's verdict box.
    "1a": "five boxes, but only ONE is this item's own response — a single "
          "field. The other four are the shared data table, `sim`-parsed values "
          "carried as context. Nothing here was split",
    "1b": "four boxes, all four `sim`-parsed values: the student's weekly data "
          "read out of a table, not spans cut from prose. p15 shows the shape — "
          "`wk1` is `8, {{corpus:1a/p15:wk1:3:19:sha=7b2512f124b3}} 9` for a table reading \"Sunday - 8 "
          "hours Monday - 11 hours ...\", and its empty `baseline`/`wk3` are the "
          "student's own \"none\" and \"Week Three Data: Lost\", which gold's "
          "2.0 agrees with",
}


# WHAT IS DESIGNED MUST BE WHAT SHIPS. Exact prompt text a subgoal committed to,
# keyed (item, slot, field), compared against the live rubric before any call.
#
# THIS TABLE EXISTS BECAUSE OF ONE WASTED SWEEP AND A WRONG EXPLANATION. On
# 2026-09-06 subgoal Q19 designed a report slot and recorded its `desc` as PROSE
# IN A GOAL ENTRY. At build time the string was RE-TYPED into the rubric, and the
# re-typing dropped the question's comparison clause and turned a yes/no into a
# which-one:
#     DESIGNED  "does this box name, as the thing the student is doing, THE SAME
#                ACT THAT AN ANTECEDENT BOX NAMES AS ITS TRIGGER?"
#     SHIPPED   "WHICH ANTECEDENT, IF ANY, does this box name as the thing the
#                student is doing?"
# The probe passed 23 of 24 on the designed wording. The sweep over-fired on nine
# cells and cost ~230 calls. The first explanation offered was a "prompt-load
# effect" -- a hand-wave that would have ended the investigation -- and a
# re-probe with the SHIPPED string reproduced the failure standalone in 24 calls.
#
# NOTHING COULD HAVE CAUGHT IT. Every other gate here asks whether the shipped
# text is WELL-FORMED -- that the slot reaches the sheet, that its verdicts are
# reachable, that no map dangles, that no cohort words leak. None asks whether it
# is THE TEXT SOMEBODY DECIDED ON, because the decision lived in prose and prose
# is not comparable. A design recorded where no check can read it is a design
# that ships by memory.
#
# HOW TO USE IT: when a subgoal commits to exact prompt wording, put the string
# HERE, verbatim, and have the entry point at this table instead of restating the
# words. Then the build cannot drift, and if the design is deliberately revised
# the revision happens in one place and is visible in the diff.
DESIGNED_TEXT: dict[tuple[str, str, str], str] = {
    ("Q4a", "antecedent_kind_1", "rule_addition"): '`aftermath` COVERS THE GOAL BEHAVIOUR TOO, not only the unwanted one. An entry naming what follows from DOING the goal behaviour -- its payoff not yet showing, or a cost incurred by having done it -- names something a behaviour left behind, so answer `aftermath` rather than `before`, even though the next episode of the unwanted behaviour comes after it. THIS IS NARROW BY DESIGN: it turns on the entry naming a result OF THE GOAL BEHAVIOUR. A state the student is simply in, however it arose, is a `before` in the ordinary way.',
    ("Q4a", "antecedent_kind_2", "rule_addition"): '`aftermath` COVERS THE GOAL BEHAVIOUR TOO, not only the unwanted one. An entry naming what follows from DOING the goal behaviour -- its payoff not yet showing, or a cost incurred by having done it -- names something a behaviour left behind, so answer `aftermath` rather than `before`, even though the next episode of the unwanted behaviour comes after it. THIS IS NARROW BY DESIGN: it turns on the entry naming a result OF THE GOAL BEHAVIOUR. A state the student is simply in, however it arose, is a `before` in the ordinary way.',
    # Q2 `reasons_given` desc, registered 2026-09-09 BEFORE the build. Q44's
    # seventh route, and the FIRST that is a repair rather than a new test.
    # Q2/p6: band 3/12, gold 4.00, python 1/6 and olx 2/6, Q2's only wrong cell.
    #
    # THE DEFECT IS TWO SHIPPED CLAUSES CONTRADICTING EACH OTHER ACROSS THE TWO
    # PROMPT SECTIONS, which is why reading either field alone looked consistent
    # and why six earlier routes missed it. The desc illustrated the `and`-split
    # with "(one about the body, say, AND one about mood)" -- UNQUALIFIED. The
    # rule qualifies the same split: "BUT ONLY WHERE EACH HALF NAMES A GOOD OF
    # ITS OWN, some particular thing that gets better, each with its own
    # predicate." And p6's sentence IS the desc's example verbatim in shape --
    # a body good AND a mood good -- on a cell gold counts as ONE. The concrete
    # example instructed the split, the abstract qualification forbade it, and
    # the example won in 8 of 12 runs. Q44 suspected the clause was generalised
    # from p6 during the 2026-08-24 de-citation campaign (whose own summary
    # lists `Q2/p6 2/3 -> 3/3`); what it missed is that the surviving text is
    # the EXAMPLE, sitting in the other section from the qualification.
    #
    # SO THIS REMOVES A MIS-CHOSEN ILLUSTRATION AND ADDS NO TEST. That is the
    # opposite of route 3, which added a distinct-content test and broke p11,
    # p16 and p18. What the slot tests is unchanged; the qualification already
    # shipped in the rule can now operate instead of being contradicted.
    # GOLD IS SELF-CONSISTENT ON THIS BOUNDARY, which is why p6 is fixable and
    # not declarable: p9 splits four conjuncts, each naming a distinct thing
    # with its own predicate, and takes 5.00; p11 splits three at 12/12; p6's
    # second half names no object at all and gold folds it into the first.
    #
    # ABORT IF ANY OF p9, p11, p14, p18, p19 LOSES A COUNT. Compare all twenty
    # cells and read by SCORE via probe.score_impact, never by verdict count --
    # Q2 is 18/20 and 19/20, so a one-cell move in the item total is not
    # evidence either way, and two probes today mis-reported by counting flips.
    # The replacement paraphrases the structural shape and quotes neither p9's
    # nor p11's wording; screened clean at the three-or-fewer-students mark.
    ("Q2", "reasons_given", "desc"): 'HOW MANY of the listed statements are a real benefit of the GOAL behaviour: `reasons_listed` minus `reasons_failing`. A statement that restates the harm of the unwanted behaviour is not a benefit of the goal — "not exercising makes me feel lazy" is a reason to drop the UTB, not a benefit of exercising. What decides this is what the statement NAMES: one whose subject is the unwanted behaviour, or going without the goal behaviour, and whose predicate is a cost of that, names no benefit. One that NAMES a good the goal behaviour brings and then supports it by the cost avoided has named its benefit and COUNTS. Two goods in one area of life are still two. Whether one sentence holds one benefit or two is STRUCTURAL: a second half that is a knock-on effect of the first is ONE (a benefit, then "WHICH WILL" and what follows from it), while two independent benefits merely joined by "and" are TWO -- BUT ONLY WHERE EACH HALF NAMES A GOOD OF ITS OWN, its own subject with its own predicate, as the counting rule below requires. A second half that names no thing of its own, and only says matters will generally improve, extends the first half, and the pair is ONE. A restatement of the PROBLEM the goal solves is not a benefit of it either: a remark attributing their present condition to not having done the goal behaviour names the harm again and earns nothing. Two things resemble that and are NOT it. A good does not become a restatement by being described as LASTING: saying a benefit will continue, or that the behaviour will become settled practice, says how long the good holds, and a benefit that lasts is still a benefit. Nor does a good become a restatement by being a CHANGE IN THE STUDENT rather than in their circumstances: a capacity or a disposition the behaviour builds in the one who does it is a benefit the graders credited. Statements about why the UTB is bad belong to Q1 and earn nothing here either — a response whose reasons are all of that kind scores 0. Answer 3 for three or more',
    # Q3 `realistic`, registered 2026-09-09 BEFORE the build. Aimed at Q3/p13,
    # 5 of 12, gold 3.00 and we score 2.00 -- the ONLY median-wrong cell in the
    # corpus with NO history of failed attempts and no declaration.
    #
    # THE SLOT IS UNDER-SPECIFIED RELATIVE TO EVERY SCORED SIBLING. Q3's slots
    # carry: specific 35 chars, measurable 731, action_oriented 1404,
    # time_bound 329, and `realistic` THIRTY-ONE -- "Is realistic, or says why
    # it is", with no rule at all. So this is NORMALISATION, not load-adding:
    # 351 chars puts it between time_bound and measurable. (The 63 chars a
    # reader sees is `probe.question_for` returning BOTH prompt sections, which
    # for a desc this short are the same string twice -- not a duplication bug.)
    #
    # THE DIRECTION IS GENEROUS, WHICH IS WHAT GOLD REQUIRES. `realistic`
    # answers `met` 12 of 12 on EIGHTEEN of twenty cells. Only two move: p9,
    # blank justification, `absent` 12/12 and correctly refused; and p13, which
    # splits THREE WAYS -- met 5 / unclear 3 / absent 4. Gold gives p13 3.00 and
    # the met reading is what produces 3.00, so OUR REFUSALS ARE THE ERROR and
    # the slot's own wording already licenses crediting: "or says why it is".
    # WHY p13 IS THE ONE THAT SPLITS: every credited justification names a
    # capability or a resource -- control over the behaviour, a paid membership,
    # a gym on campus, produce in every grocery store, thirty minutes that fit.
    # p13's is the only one in twenty that instead asserts the OUTCOME is
    # likely: [[corpus Q3/p13 realistic 36:83 sha=9e97e908c0fe]] With
    # 31 characters of instruction the grader has no basis to choose, so it
    # splits. The clause says the thin reason still counts.
    #
    # FALSIFIER: p9 must stay `absent` -- it offers no reason at all and gold
    # charges it. CONTROLS: the eighteen cells at `met` 12/12 must not move.
    # Leakage-screened: no content word in the clause is used by three or fewer
    # students, which is the pattern the gate flags.
    # AND A SIBLING GAP WORTH RECORDING: `specific` carries 35 characters, the
    # same near-empty shape. It has not flapped yet, so it is a latent case of
    # this defect rather than a live one.
    ("Q3", "realistic", "rule"): 'THE BAR IS LOW, AND THE TWO ARMS ARE ALTERNATIVES: `met` where the goal is plainly workable as stated, OR where any reason for thinking so is given. DO NOT WEIGH THE REASON -- a thin or circular one counts, since this asks whether a reason was given and not whether it persuades. `absent` only where none is given and the goal is not plainly workable.',
    # WK2's `named_type`, registered 2026-09-07 (subgoal Q55). Lifted from
    # `scratchpad/candidate_wk2_named.txt` -- the same file the probe read and
    # the same file the build read, so design, probe and shipped text are one
    # string by construction and not by inspection.
    # IT ALSO REPLACES NOTHING: sha e3b0c44298fc, the empty string, exactly as
    # `aimed_correctly` did below. D1 and D2 carry text for the same key and
    # WK2 and DAY1 do not -- and D1/D2's text says "`unclear` only if it is
    # blank or unreadable", which on WK2/p15 prescribes the WRONG answer, so
    # this is written from the cells rather than copied from the sibling.
    # DAY1 STILL SHIPS THE EMPTY STRING for this slot and is NOT touched here:
    # nothing has measured a DAY1 cell of p15's shape, and a second item is a
    # second measurement, not a free ride on this one.
    # UPDATED 2026-09-10 with the rewording that removed "read both
    # boxes" from a one-box item. The design is LIVE -- the note still
    # ships, it just names the type and the definition instead of
    # counting boxes -- so the design of record follows it. Left under
    # the "desc" key it was registered with: `named_type` is a CRITERION
    # and has no desc, which is why --accept-design-change refuses it,
    # and re-keying the fragment is its own cleanup.
    ("WK2", "named_type", "desc"): 'WHICH of the four types the student CLAIMS -- not whether the claim is right, which another check decides.\nREAD BOTH THE TYPE THEY NAMED AND THE DEFINITION THEY WROTE. The type may be named outright, or it may be named only by the DEFINITION: a definition that describes adding an unpleasant thing after a behaviour, or taking a wanted thing away, names a type as surely as writing its name does. Where the two disagree, report what the NAMED TYPE says.\nAnswer `unclear` ONLY when NEITHER names a type -- both empty, or a bare label with nothing after it. A blank type is not by itself an absent type.',
    # WK2's `aimed_correctly` gate, REGISTERED BEFORE THE BUILD on 2026-09-07 --
    # the order this table exists to enforce, and the order Q4b's report slot did
    # not follow. Lifted from `scratchpad/candidate_wk2_aimed.txt`, the file the
    # probe read; nothing retyped.
    # WHAT IT REPLACES IS NOTHING AT ALL. `probe.question_for` returned the EMPTY
    # STRING for this slot -- sha e3b0c44298fc -- because it is absent from WK2's
    # rubric credit list and carries no desc, no rule and no SLOT_NOTES. A gate
    # that takes the whole 4-point item shipped as its own identifier:
    #   - `aimed_correctly` **GATE** -- `met`/`absent`/`unclear`
    # Sentence 1 is `rubric_h2.OC_GATES`' own declared message for this gate,
    # turned from feedback into a question. Sentence 2 is the reading BACKLOG.md
    # records the slot ALREADY using on WK2/p8 -- "answers `aimed_correctly: met`
    # because the fault is already accounted for". Sentence 3 covers the blanks.
    # PROBED ON ALL 20 CELLS BEFORE BUILDING: target p11 `met` 4/4 (it refuses in
    # 5 of 11 today), p3/p15 held, no gold-4.00 cell moved, and every gold-0 cell
    # still refuses. scratchpad/probe_wk2_aimed.json.
    ("WK2", "aimed_correctly", "desc"):
        "Does the consequence point the RIGHT WAY for the arrangement this answer actually describes -- something added or taken away AFTER the behaviour, in the direction that would change it? Answer `absent` when it is pointed the wrong way: an aversive for MEETING the goal, or a reward for MISSING it.\nJUDGE THE ARRANGEMENT DESCRIBED, NOT THE TYPE THE STUDENT NAMED. An answer that describes a sound arrangement but labels it with the wrong type is `met` here. The mismatch between the two is a different check's charge, and taking the whole item for it here would charge one fault twice.\nAnswer `unclear` only when the answer names no consequence to judge at all.",
    # SUBGOAL Q19's REPORT SLOT IS GONE FROM HERE, 2026-09-07, and the reason
    # matters because this table's standing policy is the opposite. A design is
    # normally KEPT after a revert so the next attempt starts from the decision
    # rather than from memory -- right when the DESIGN was sound and the BUILD
    # drifted, which is what happened to this slot the first time round.
    # IT IS WRONG HERE. The design itself was then measured TWICE and refuted
    # both times: the probed wording fired on p13, p20 and p8, where gold charges
    # nothing on the behaviour boxes; a second wording adding a disposition
    # clause and a sameness clause fixed p16 and still fired on those three.
    # Gold names this criterion exactly ONCE in the item, on p4 -- "your
    # behaviors cannot be the same as your antecedents" -- so the standard is
    # fire-on-p4-and-nowhere-else, and neither wording met it.
    # A design of record pointing the next attempt at a wording measured to
    # contradict gold on three cells is worse than no entry. Both texts and both
    # results live in GOALS.md under Q19, where a FAILURE can be recorded beside
    # them. Nothing is lost; what is removed is the false suggestion that this
    # wording is ready to build.
}


# Subgoal E53. Slots where the two engines score the SAME judgement through a
# different DECOMPOSITION -- one enumerates per item, the other counts -- so
# neither an alias nor a derivation rule can reconcile the names, and there is
# nothing to fix. Declared rather than excluded silently, because "the app does
# not answer this scored slot" is exactly the shape of a real defect and a reader
# who meets it undeclared cannot tell the two apart.
#
# EVERY ENTRY WAS MEASURED BEFORE IT WAS WRITTEN, per-cell medians on both
# sides. If a future change makes one of these diverge, the declaration is wrong
# and the check will not catch it -- the per-cell comparison is what catches it,
# and it lives in the sweep readouts.
DECOMPOSITION_DIVERGENCES: dict[tuple[str, str], str] = {
    **{("2b", f"sentence_{n}"):
       "The mirror enumerates the three sentences as `sentence_1/2/3`; the app "
       "answers the COUNT `sentences_given` and charges from it. Measured: 2b is "
       "20/20 on both sides with identical medians on all twenty cells."
       for n in (1, 2, 3)},
    **{("3", f"example_{n}"):
       "The mirror enumerates the examples as `example_1/2`; the app answers the "
       "COUNT `changes_given`. Measured: python 19/20, olx 20/20, and the single "
       "cell whose medians differ (p15) is one the APP gets right and the mirror "
       "does not -- so the decomposition is not costing the app anything."
       for n in (1, 2)},
    **{(item, f"reason_{n}"):
       "The mirror enumerates the reasons as `reason_1/2/3`; the app scores the "
       "reasons scaffold in aggregate. Measured: Q1 18/20 and Q2 19/20 on BOTH "
       "sides, with Q2 identical on every cell and Q1 differing on two (p6, p17) "
       "for reasons subgoals Q16 and Q44 own, not this one."
       for item in ("Q1", "Q2") for n in (1, 2, 3)},
    ("NR", "barrier_is_not_this_type"):
        "NR-only slot the mirror answers and the app never does. Measured: NR is "
        "18/18 python and 17/18 olx with the per-cell medians IDENTICAL on all "
        "twenty cells, so the app reaches the same judgement through the type "
        "criterion it does answer. Kept declared rather than aliased because "
        "there is no app-side name to alias it to.",
}


# CONSENSUS_OVERLAP_BACKLOG IS NOT HERE, AND THAT IS THE POINT. It is keyed by
# ('2a', 18, 'how1', 'verdict') -- participants 18 and 20 -- and C1b puts
# anything keyed by a participant in the GOLD file, outside this public
# repository. It stays in `enforcement.py` with the other gold-linked tables
# until that file exists. Seven tables moved; this is the eighth and it is
# held back deliberately.


# A verdict a scored slot can answer, that the paper ledger deliberately does
# NOT charge. The web fails anything that is not the satisfying verdict, so an
# entry here is a real difference between the engines -- it is declared, with the
# measurement that settled it, rather than repaired.
UNCHARGED_VERDICTS: dict[tuple[str, str, str], str] = {
    ("Q1", "utb_stated", "unclear"):
        "GOLD BACKS THE PAPER SIDE, so aligning the engines here would make the "
        "scorer wrong. `unclear` fires on exactly one cell in the corpus -- p17 "
        "-- and gold gives p17 full marks (5.00), which is what the paper scorer "
        "returns and the web does not: the web charges the full 2 points for "
        "\"could not tell\". p20, the cell this check exists to catch, answers "
        "`absent` in 11 of 11 runs, so nothing it should catch escapes. Charging "
        "`unclear` was measured and reverted; see rubric_h1.py's note on the "
        "`codes` entry.",
}


APP_ONLY_SLOTS: dict[tuple[str, str], str] = {
    ("Q1", "matches_selected"):
        "UNSCORED, and it drives FEEDBACK rather than a score. The sheet spells "
        "it `Same behavior you selected above:matches/differs` with no @pts, and "
        "olx_prompts instructs the grader that when it answers `differs` the "
        "FIRST sentence of `feedback` must address the mismatch. The python "
        "mirror produces no feedback, so there is nothing for it to define. "
        "Wiring it into the rubric would add a slot that can never change a "
        "number, which is the opposite of what the rubric is for.",
}


# ---------------------------------------------------------------------------
# STAGE 4, from `score.py` and `agreement_app.py`. Per-item notes the PAPER
# scorer carries, and the component-id -> context map the app builds jobs
# from. Both are course content; `CONTEXT_SOURCE` is the same shape as the
# `_H*_CTX` maps already moved, keyed by component rather than by item.
# ---------------------------------------------------------------------------
PAPER_ITEM_NOTES: dict[str, str] = {
    # JUDGE EACH ANSWER ON ITS OWN LABELLED PART. Q3's paper divergences were
    # one error: an answer credited from text belonging to a DIFFERENT answer,
    # with the evidence quoting the wrong heading verbatim -- p8 credited
    # action_oriented while quoting [[corpus Q3/p8 specific 10:80 sha=2aaae6fc2b69]]. The web cannot make this error: each answer
    # has its own box.
    #
    # MEASURED HERE AND NOWHERE ELSE: paper 16.5 -> 17.8 over six runs, the gap
    # to the web -3.4 -> -2.1, cross-aspect evidence quoting 6/598 -> 1/600.
    #
    # WHY Q3 AND NOT THE OTHER EIGHT >=2-ANSWER ITEMS. It keys on the student
    # LABELLING their parts, and the label rate decides whether it can act at
    # all -- Q3 19/20, 2a 15/20, 1c 7/19, Q4c 2/20, and Q4b, Q6, Q5 and `3` at
    # ZERO of ~20. Shipped to all nine on 2026-09-10 it cost about four cells:
    # Q4b -2, Q5 -1, 2a -1, with Q4c, 1c and `3` flat and Q6 unchanged at 10/20.
    # On the four zero-label items it is INERT BY CONSTRUCTION -- its own
    # fallback is "read the whole response for each" -- so what it bought there
    # was a hundred words of instruction that cannot apply, and the picks
    # drifted under them: Q4b/p12 lost its occasional `activity` and stuck at
    # 3.5, while p6 and p20 gained one and started over-crediting.
    #
    # 2a AND 1c ARE THE UNMEASURED CANDIDATES, at 15/20 and 7/19 labels. 2a lost
    # a cell in that sweep but also took the deixis change, so its loss is not
    # attributed. Add either only with its own six runs.
    "Q3": (
        "Where the student has labelled parts of their answer to match the "
        "names above, judge each answer on the part they labelled for it, and "
        "never on what they wrote for another -- a sentence that opens by "
        "naming a different one of these answers belongs to that one. Where "
        "they label nothing, read the whole response for each.\n\n"
        "The evidence you quote for an answer must come from that answer's own "
        "part of the response."
    ),
}

# PAPER-ONLY text an item needs because of how a PAPER submission arrives.
# The mirror of `olx_prompts.ITEM_NOTES`, which does the same job for the web
# and says of itself: "Web-only text an item needs because of how its screen is
# built. Additions, not paraphrases: they say something about the web that the
# rubric cannot know." There was no paper counterpart, so a paper-side
# instruction had nowhere to live except an id list gating a mechanism -- which
# is the thing that must never vary by item.
#
# THE MECHANISM IS UNIFORM AND THE CONTENT IS PER ITEM. Every item is offered
# the same slot; what goes in it differs because the ITEMS differ, exactly as
# `guidance`, `credit` and `maps` differ. That is content, and content may vary.
# An id list that switches a mechanism on and off is not, and
# `enforcement.check_engine_mechanisms_are_not_item_dependent` still refuses it.
#
# EACH ENTRY IS A DECLARED WEB/PAPER DIVERGENCE and needs its own measurement.
# WHY EACH ENTRY IS PAPER-ONLY. Required beside every key below, for the same
# reason its web twin requires one: a note earns a side table only by saying
# something true of THIS side and not the other. Anything sayable to both is
# rubric content and belongs in `guidance`.
PAPER_ITEM_NOTES_WHY: dict[str, str] = {
    "Q3": "Tells the grader to judge each answer on the part the student "
          "labelled for it. The WEB CANNOT NEED THIS: there each answer has "
          "its own input box, so the partition is structural and no "
          "instruction can improve it. Paper receives one continuous block and "
          "must infer the partition, which is the divergence this note exists "
          "for -- and the defect it treats was measured only here (16.5 -> "
          "17.8 over six runs).",
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


# ---------------------------------------------------------------------------
# STAGE 4, from `agreement_app.py`. The per-item JOB definitions the app
# builds its run list from -- which screen, which grader, which fields,
# which button. Course content: another course would have its own.
# ---------------------------------------------------------------------------
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
        # DEALT HERE, not read off the rubric's `counts`. See _dealt_members.
        "dealt": [{"count": "hows_given", "members": ["how_1", "how_2"]}],
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
        "dealt": [{"count": "changes_given",
                   "members": ["example_1", "example_2"]}],
    },
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


# Repeated families that are countable in shape but must NOT be converted, with
# the reason, because an unexplained exemption is how the inconsistency below got
# in. Keyed by (item, family stem).
COUNTABLE_EXEMPT = {
    ("1a", "week"): "the weeks are NAMED, not interchangeable. The guidance deducts "
                    "only when a period is 'clearly and specifically absent' and names "
                    "the observed case — an answer that opens at the intervention and "
                    "never mentions baseline. `3 of 4` cannot say which is missing.",
    ("2a", "how"): "MEASURED, not preferred. The count WAS the design and it cost "
                   "the item 5 of 20 cells: subgoal Q2 recorded one error profile "
                   "-- `said 2, scored 6 against gold 4`, 29 of 29 -- while the "
                   "DEDUCT guidance already described both shapes the graders "
                   "charge. An aggregate answer never has to confront a particular "
                   "box, so correct prose had nothing to bind to. The graders "
                   "themselves judge per box and name it ('your third sentece'), "
                   "against three labelled fields on screen that all 20 cells "
                   "fill, so nothing relies on content spanning them. The FIXTURE "
                   "no longer depends on the group either -- the dealing groups "
                   "live in agreement_app.JOBS `dealt` -- which is what made this "
                   "conversion testable at all.",
}


# Charge-once pairs the WEB reader declares and the CLI probe cannot discover.
#
# NOT A DIFFERENCE IN WHAT THE ENGINES SCORE. The probe finds a sublinear pair
# by arithmetic: it fails each slot singly, then in pairs, and calls the pair
# charge-once when `both < single[a] + single[b]`. A pair produces no observable
# sublinearity when one side is already a gate, or ignored, or its loss is
# masked by another deduction -- so the probe cannot see a rule the web declares
# outright. The two engines agree; one instrument reaches the rule and the other
# does not.
#
# DECLARED RATHER THAN TOLERATED IN A COMMENT. Both of these were accepted
# already -- the selftest names NR's as a legitimate declared divergence when it
# computes its clean baseline -- but that acceptance lived in a sentence inside
# a different module. A reader meeting the finding could not tell an accepted
# limit of the probe from a new defect, which is the distinction
# DECOMPOSITION_DIVERGENCES exists to preserve, one instrument over.
#
# EACH ENTRY NAMES WHY THE PROBE CANNOT REACH IT, so a THIRD one shows up as
# new rather than joining a list nobody re-reads. The table ratchets: it may
# shrink, and an addition wants the same measurement these had.
PROBE_UNREACHABLE_PAIRS: dict[tuple[str, frozenset], str] = {
    ("2a", frozenset({"how_2", "mechanism_named"})):
        "The web charges the pair once. In the CLI ledger `mechanism_named` is "
        "already carried by the deduction that `how_2` triggers, so failing both "
        "loses exactly what failing one loses and the arithmetic shows no "
        "sublinearity for the probe to find. Declared 2026-09-16.",
    ("NR", frozenset({"barrier_is_not_this_type", "demonstrates_type"})):
        "The web charges the pair once. `demonstrates_type` is DERIVED on NR -- "
        "the sheet declares `expect=\"demonstrates_type:observed_type=NR\"` -- so "
        "the CLI probe never fails it independently and the pair cannot appear "
        "in its arithmetic. Named in equivalence.py's selftest as a legitimate "
        "declared divergence since before this table existed; moved here so it "
        "is a decision with a reason rather than a remark. Declared 2026-09-16.",
}
