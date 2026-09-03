"""Handout 3 rubric as data: 6 items, 40 points.

Sources as before: the Handout 3 scoring dictionary for point splits and
canonical wording, plus the graders' 20 rows for criteria the dictionary omits.

What makes this handout different: **item 1c is scored from a graph, not from
text**, and it is 10 of the 40 points. A submission can carry its graph three
ways — as an OOXML chart part, as an embedded image, or as grouped drawing
shapes whose labels arrive as ordinary document text — and the blank template
ships its own worked example graph ("Water {{corpus:1c/p5:title:5:32:sha=97ca3baaf650:shape=R27-0-22}}) that
several students left in place. Participant 4's file contains a chart and
scored 0 because that chart was the template's. See `graph_evidence()` in
docx_text.py and the 1c item below.

The remaining 10 points of the 50-point handout are for submitting the written
and typed versions. Out of scope — see README.
"""

from __future__ import annotations

ITEMS: list[dict] = [
    {
        "id": "1a",
        "label": "1a",
        "max": 8.0,
        "increment": 2.0,
        "question": (
            "Give a brief overview of the data you collected in at least 4 sentences. How "
            "did your behavior change over time? You do not need to discuss every day — "
            "one sentence per week is the expectation, covering the baseline week and the "
            "three intervention weeks."
        ),
        # Derived, not model-authored: one slot, one deduction, so the
        # stacking the plain path allowed is unrepresentable.
        "derive_from_credit": True,
        "blank_code": "BLANK",
        # THE FIVE JUDGING RULES BELOW LIVED IN olx_prompts.SLOT_NOTES, which only
        # the web generator reads, so score.py never saw them. That was not
        # theoretical: 1a/p6 scored 0.0 on the paper path against 6.0-8.0 on the
        # web -- the whole item, stably, in 3 of 3 runs -- and cross_path.py
        # localised it to `distinguishes_periods`, one of these five. Moved here
        # VERBATIM on 2026-08-28, so the web's rendering of them did not move: its
        # checklist looks up `rule` before SLOT_NOTES and finds the same string.
        "credit": [
            {
                "what": "distinguishes_periods",
                "gates": True,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "NO_WEEKLY_BREAKDOWN", "unclear": "NO_WEEKLY_BREAKDOWN"},
                "desc": "Separates the baseline period from the intervention weeks at all. NO_WEEKLY_BREAKDOWN (-8) is for an answer that never distinguishes any time periods — no before/after, no weeks. An answer of that kind loses the whole 8. Do not use it when some periods are discussed; deduct per missing period instead.",
                "rule": "the NO_WEEKLY_BREAKDOWN test: does the answer distinguish any time periods at all? A single AGGREGATE verdict over the whole span does not, even when it mentions weeks — \"my three weeks of tracking prove the plan worked\" and \"looking at the whole month, nothing really changed\" both score 0: each delivers ONE verdict covering the entire span. What distinguishes periods is reporting more than one point in time separately, so that a reader can see the behaviour CHANGE",
            },
            # THE FOUR PERIOD SLOTS. Written out because the observed failure is
            # not the one the guidance anticipated: it warns against requiring one
            # sentence per week, but the model's actual mistake is treating a
            # PARTIAL list of week names as exhaustive. p11 names only "week two"
            # and p14 only "{{corpus:1a/p14:response:293:316:sha=3df2d6dade26}}"; gold gave both the full 8,
            # and both systems docked 2 for the week that went unnamed. The label
            # is not the evidence -- the arc is.
            {
                "what": "baseline_week",
                "pts": 2.0,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "MISSING_WEEK", "unclear": "MISSING_WEEK"},
                "desc": "Discusses the baseline week",
                "rule": "is the BEFORE state given — the level the behaviour ran at prior to the intervention? A sentence that looks back before the plan began and gives the rate the behaviour ran at then is `met`; so is any pre-intervention figure or description. `absent` when the answer opens at the intervention and never says what came before: an answer beginning \"in {{corpus:1a/p6:response:7:27:sha=ffb845e9e43e}} plan I was still up past midnight most nights\" starts the clock at the intervention, and loses exactly this slot and no other",
            },
            {
                "what": "week_1",
                "pts": 2.0,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "MISSING_WEEK", "unclear": "MISSING_WEEK"},
                "desc": "Discusses week 1",
                "rule": "does the answer's account of change COVER this stretch of the intervention? Judge the arc, not the label. Naming some weeks does NOT make the unnamed ones absent: an answer that runs from the before state through to the end covers all three intervention weeks even if it names one of them or none. Answer `absent` only when a period is clearly and specifically skipped",
            },
            # MEASURED, AND NOT EXTENDED FURTHER. Propagating the aggregate test
            # from `distinguishes_periods` into these three slots -- plus a plea to
            # keep the two consistent -- held the mean at 90% but put the variance
            # back: over three runs p6 swung 8.0/0.0/6.0 and p7, correct in every
            # run before it, dropped to 6.0 once. Stability at the same accuracy
            # beats a wider spread around the same mean, because a measurement that
            # moves cannot tell you whether the next change helped. Reverted; do
            # not re-add without three runs to compare.
            {
                "what": "week_2",
                "pts": 2.0,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "MISSING_WEEK", "unclear": "MISSING_WEEK"},
                "desc": "Discusses week 2",
                "rule": "same question for the middle stretch — and the same rule: a week the answer does not name by number is still covered if the account of change runs through it. An answer that names only its first and last weeks by number, but describes a change carrying continuously from one to the other, covers the middle week too, and gold credits all four slots",
            },
            {
                "what": "week_3",
                "pts": 2.0,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "MISSING_WEEK", "unclear": "MISSING_WEEK"},
                "desc": "Discusses week 3",
                "rule": "same question for the final stretch, same rule. \"By the end of the month I was down to about one\" covers it without naming a week",
            },
        ],
        "deductions": [
            {"code": "BLANK", "pts": 8.0, "text": "did not answer"},
            {
                "code": "MISSING_WEEK",
                "pts": 2.0,
                "text": "-2 pts: you are missing one sentence",
                "repeatable": True,
            },
            {
                "code": "NO_WEEKLY_BREAKDOWN",
                "pts": 8.0,
                "text": "-8 pts: did not discuss data for each week",
            },
        ],
        "guidance": [
            "Four 2-point slots, one per week. The graders count WEEKS COVERED, not "
            "sentences.",
            "THE BAR IS THE ARC, NOT A SENTENCE COUNT. This item is graded generously. If "
            "the answer gives the BEFORE state and then describes how the behaviour "
            "changed across the intervention, award all four slots — even when the weeks "
            "are not enumerated one per sentence. All of these earned full marks: a "
            "before-and-after pair giving one range for the baseline and another for "
            "the intervention; a baseline average followed by each later week's figure "
            "given in turn; and a summary that names two weeks and states the direction "
            "they moved without a figure for either. A week referred to collectively "
            "(\"after I began, it increased\") counts when the others are named.",
            "DEDUCT A WEEK only when a period is clearly and specifically absent. The "
            "observed case is an answer that opens at the intervention and never mentions "
            "the before/baseline state at all — it begins with the first week of data "
            "collection and carries no sentence about how things stood beforehand, which "
            "costs the baseline week's 2 points.",
        ],
        "context": [],
    },
    {
        "id": "1b",
        "label": "1b",
        "max": 4.0,
        "increment": 1.0,
        "question": (
            "Include the data you collected during the baseline period and each of the "
            "three intervention weeks, on its own page at the end of the handout."
        ),
        # Derived, not model-authored: one slot, one deduction, so the
        # stacking the plain path allowed is unrepresentable.
        "derive_from_credit": True,
        "blank_code": "BLANK",
        "credit": [
            {
                "what": "baseline_data",
                "pts": 1.0,
                "verdicts": ["met", "absent"],
                "codes": {"absent": "MISSING_WEEK_DATA", "unclear": "MISSING_WEEK_DATA"},
                "desc": "Baseline week's data present",
            },
            {
                "what": "week_1_data",
                "pts": 1.0,
                "verdicts": ["met", "absent"],
                "codes": {"absent": "MISSING_WEEK_DATA", "unclear": "MISSING_WEEK_DATA"},
                "desc": "Week 1 data present",
            },
            {
                "what": "week_2_data",
                "pts": 1.0,
                "verdicts": ["met", "absent"],
                "codes": {"absent": "MISSING_WEEK_DATA", "unclear": "MISSING_WEEK_DATA"},
                "desc": "Week 2 data present",
            },
            {
                "what": "week_3_data",
                "pts": 1.0,
                "verdicts": ["met", "absent"],
                "codes": {"absent": "MISSING_WEEK_DATA", "unclear": "MISSING_WEEK_DATA"},
                "desc": "Week 3 data present",
            },
        ],
        "deductions": [
            {"code": "BLANK", "pts": 4.0, "text": "-4 pts: did not provide data"},
            {
                "code": "MISSING_WEEK_DATA",
                "pts": 1.0,
                "text": "-1 pt: missing a week of data",
                "repeatable": True,
            },
        ],
        "guidance": [
            "One point per week of data present: {{corpus:1c/p1:series:0:32:sha=d1f3e922817c:shape=C4040401}}.",
            "This is a presence check, not a quality judgement. Any legible daily figures "
            "for a week earn its point — hours, minutes, ounces, servings, tallies, a "
            "table, or a prose list. Do not deduct for formatting, units, or gaps within "
            "a week.",
            "The text you are shown has already had the template's worked example data "
            "(the 'oz' water figures) subtracted, so anything here is the student's own. "
            "If a week's heading is present but its days are empty, that week is missing.",
        ],
        "context": ["1a"],
    },
    {
        "id": "1c",
        "label": "1c",
        "max": 10.0,
        "increment": 2.0,
        # Scored from the graph evidence bundle, not from prose. Five
        # independent 2-point slots — the same shape as Handout 1's Q6, so it
        # uses the slot-walk derivation.
        "derive_from_credit": True,
        "graph_item": True,
        "question": (
            "Present your data in a figure/graph at the end of the handout. The graph "
            "needs a title, both axis labels, and a legend."
        ),
        "credit": [
            {
                "what": "has_own_graph",
                "pts": 2.0,
                "desc": "The student supplied their OWN graph of their OWN data",
                "codes": {"absent": "NO_GRAPH", "mismatch": "TEMPLATE_GRAPH_ONLY"},
                # No graph means no title, axes or legend either — the whole
                # item is lost on this one slot rather than 2 points of it.
                "gates": True,
            },
            {
                "what": "title",
                "pts": 2.0,
                "desc": "The graph has a title, and A DEFAULT PLACEHOLDER IS NOT ONE: "
                     "spreadsheet software inserts \"Chart Title\" when the student "
                     "never types one, and that counts as missing. A graph carrying "
                     "that literal text has no title, and the graders deducted the "
                     "point for it",
                "codes": {"absent": "NO_TITLE", "not_described": "NO_TITLE"},
            },
            {
                "what": "x_axis_label",
                "pts": 2.0,
                "desc": "The x-axis is labelled — an AXIS TITLE, not the tick values. "
                     "\"Sunday, Monday, ...\" along the bottom is tick data; \"{{corpus:1c/p2:x:0:4:sha=e08c0aa8f558:shape=R4-0-20}}"
                     "{{corpus:1c/p2:x:5:16:sha=93a929ee8ebb:shape=C80}}\" is the label. This distinction is the single most "
                     "common deduction on this item: nine of the twenty gold rows lost "
                     "points for a missing axis title. A default placeholder is not a "
                     "label either — spreadsheet software inserts \"Axis Title\" when "
                     "the student never types one, and that counts as missing",
                "codes": {"absent": "NO_X_AXIS", "not_described": "NO_X_AXIS"},
            },
            {
                "what": "y_axis_label",
                "pts": 2.0,
                "desc": "The y-axis is labelled — same test as `x_axis_label`: an axis "
                     "TITLE naming what the axis represents, not its tick values, and "
                     "not the software's default \"Axis Title\" placeholder",
                "codes": {"absent": "NO_Y_AXIS", "not_described": "NO_Y_AXIS"},
            },
            {
                "what": "legend",
                "pts": 2.0,
                "desc": "The graph has a legend — the key naming the plotted series "
                     "(Baseline / Week 1 / Week 2 / Week 3). A single-series graph with "
                     "no key has no legend",
                # MIGRATED 2026-08-30 from web-only SLOT_NOTES['1c:legend'],
                # verbatim except for the verdict token: the note said
                # `incomplete`, which is the web's extra for this slot, and the
                # paper's counterpart is `not_described` (see the `codes` below,
                # which is where score.py reads it from). `{fail}` renders each.
                # `absent` is named literally on purpose — it is universal, and
                # it means something DIFFERENT here from the failing verdict:
                # empty box, not a mis-described legend.
                "rule": "the NO_LEGEND test. `met` when the series names name all "
                     "four plotted periods — the baseline and the three intervention "
                     "weeks — in any reasonable wording ('Baseline, Wk1, Wk2, Wk3' "
                     "counts). `{fail}` when some are named and some are not, or the "
                     "count does not match the four series; `absent` when the box is "
                     "empty or holds something that is not a set of series names. "
                     "Judge the series names, not the heading",
                "codes": {"absent": "NO_LEGEND", "not_described": "NO_LEGEND"},
},
        ],
        "deductions": [
            {"code": "NO_GRAPH", "pts": 10.0, "text": "did not include"},
            {
                "code": "TEMPLATE_GRAPH_ONLY",
                "pts": 10.0,
                "text": "Did not provide a graph.",
            },
            {"code": "NO_TITLE", "pts": 2.0, "text": "-2 pts: missing the graph title"},
            {"code": "NO_X_AXIS", "pts": 2.0, "text": "-2 pts: missing the x-axis label"},
            {"code": "NO_Y_AXIS", "pts": 2.0, "text": "-2 pts: missing the y-axis label"},
            {"code": "NO_LEGEND", "pts": 2.0, "text": "-2 pts: missing the legend"},
        ],
        "guidance": [
            "Five independent 2-point slots: having a graph at all, a title, an x-axis "
            "label, a y-axis label, and a legend. Judge each from the evidence bundle.",
            "FIRST DECIDE WHOSE GRAPH IT IS. The blank handout ships a worked example "
            "titled 'Water {{corpus:1c/p5:title:5:32:sha=97ca3baaf650:shape=R27-0-27}}, with axes '{{corpus:1c/p2:x:0:16:sha=f1f5ac605348:shape=R12-1-57,R16-0-27}} and "
            "'Ounces of Water per Day'. Several students left it in place and added "
            "nothing. If the ONLY graph present is that one, `has_own_graph` is "
            "`mismatch` and the whole item is 0 — the graders scored 'Did not "
            "provide a graph' on files that contain a chart, because the chart was not "
            "the student's. A student's own graph plots "
            "THEIR behaviour (hours of sleep, minutes of exercise, servings) over their "
            "four weeks.",
            "The bundle marks each piece of evidence as `student` or `template`. Trust "
            "those labels for chart parts; for an image you are shown, judge the content.",
            "Shape-drawn graphs arrive as run-together text with the axis tick values "
            "jammed against the labels ('Excersing Over Four Weeks2.521.510.50 Sunday "
            "Monday...'). Read the title and any series names out of it; series names "
            "(Baseline / Week 1 / Week 2 / Week 3) appearing together indicate a legend.",
            "A WRITTEN DESCRIPTION OF A GRAPH IS NOT A GRAPH. Tidy label prose — a "
            "'Title:' line, an 'X-axis label:' line, a 'Y-axis label:' line, a "
            "'Legend:' line, each with its value written after it — is the student "
            "listing what their graph WOULD contain, with no plotted data, and the "
            "graders scored that 'did not include'. A real shape-drawn graph carries "
            "numeric tick values run together with the labels; a description carries none. "
            "If the only evidence is such a description, `has_own_graph` is `absent`.",
            "If a slot cannot be determined from the evidence, mark it `absent` and set "
            "escalate — do not guess in the student's favour.",
        ],
        "context": [],
    },
    {
        "id": "2a",
        "label": "2a",
        "max": 6.0,
        "increment": 2.0,
        "question": (
            "Did the implementation of your behavior modification plan successfully modify "
            "your behavior? Answer in 1 sentence, then describe HOW it was successfully or "
            "unsuccessfully modified in at least 2 further sentences. The level of success "
            "does not affect the grade."
        ),
        # Derived, not model-authored: one slot, one deduction, so the
        # stacking the plain path allowed is unrepresentable.
        "derive_from_credit": True,
        "blank_code": "BLANK",
        # THE COUNT WAS REMOVED 2026-09-02 (second attempt), and this is what the
        # comment here said: "The guidance is COUNT CONTENT, NOT SENTENCES, so the
        # model counts and the arithmetic stays here. The two `how` slots are
        # interchangeable instances behind one code." Subgoal Q2 measured that
        # design at 15/20 with a single error profile -- `said 2, scored 6 against
        # gold 4`, 29 of 29 -- while the DEDUCT guidance below already described
        # both shapes the graders charge. An aggregate answer never has to
        # confront a particular box, so correct prose had nothing to bind to.
        # The graders judge per box and say which one ("your third sentece",
        # "your second sentece") against three labelled fields on screen.
        # The fixture no longer depends on this declaration: the dealing groups
        # live in agreement_app.JOBS `dealt` since the first attempt corrupted
        # 2a's boxes to the placeholder "2 found" and cost a 120-call sweep.
        # NO `onlyif` HERE, AND THE REASON IS MEASURED. One was added to stop the
        # whole-response test stacking on a How (1) refusal, and the arithmetic
        # audit refused it: gating how_2 on how_1 caps the slot floor at 2.0, so
        # BLANK's -6 became unreachable and the item CANNOT ZERO. It also created
        # a transitive charge-once pair (how_1, mechanism_named) that the web's
        # declared pairs do not model, reported as an engine divergence. Both
        # findings are the guard's, not the rule's, so the guard went. The
        # exposure it covered is one cell: p15 already fails how_1, so if the
        # model also read its mechanism as absent the cell would drop to 2.0
        # against a gold of 4.0. Its second box names an arrangement the student
        # set for themself, which the test should read as `met` -- and the sweep
        # is what says whether it does.
        # `requires` is the MIRROR of the onlyif above: that one says what may be
        # CHARGED, this one what may be CREDITED. It is why the whole-response
        # test does not have to be a `forbid` -- forbid computes a verdict and so
        # strips its key from the web schema, which would stop the model judging
        # how_2 at all and lose the two-way rule. `requires` conditions a verdict
        # the model still gives, and `excludesKeys` is False for exactly that
        # reason. `unclear` is lenient: doubt about the mechanism establishes
        # nothing, so it denies nothing.
        "forbid": [{"key": "mechanism_named",
                    "conds": [{"slot": "names_enabler", "value": "absent"},
                              {"slot": "states_size", "value": "absent"},
                              {"slot": "names_plan_content", "value": "absent"}]}],
        "requires": [{"key": "how_2", "cond": "mechanism_named",
                      "lenient": ["unclear"]}],
        "credit": [
            {
                "what": "verdict",
                "pts": 2.0,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "NO_VERDICT", "unclear": "NO_VERDICT"},
                "desc": "States whether the plan was successful",
            },
            {"what": "how_1", "pts": 2.0,
             "codes": {"absent": "MISSING_HOW"},
             "desc": "The box asked for How (1), judged ON ITS OWN. It is MET on "
                     "EITHER of two grounds: it names a cause or a circumstance — "
                     "why or when the plan did or did not work, or a technique "
                     "leaned on — OR it reports the change with its SIZE: a "
                     "figure, a comparison against the earlier week, or the data. "
                     "`absent` when it offers NEITHER, a bare claim that it worked "
                     "or did not with no reason and no measure behind it. "
                     "`absent` ALSO on one COMBINATION, and only when BOTH halves "
                     "hold together: what the box reports is a bodily or personal "
                     "state rather than the behaviour itself, AND the condition it "
                     "attaches that state to is the behaviour NOT being done. "
                     "Either half ALONE is met: a state attributed to DOING the "
                     "behaviour explains the outcome, and a box whose subject is "
                     "the behaviour is met whichever direction it runs"},
            {"what": "how_2", "pts": 2.0,
             "codes": {"absent": "MISSING_HOW"},
             "desc": "The box asked for How (2), judged on its own by the same "
                     "two-way test as How (1). Either box can fail, both can, and "
                     "one failing says nothing about the other"},
            # SPLIT AGAIN 2026-09-03, second attempt, with the two fixes the first
            # split's per-ground data named. That attempt took the item 20 -> 19 and
            # was reverted; the reason was NOT the split. Asked separately the model
            # is UNANIMOUS that p16 has no enabler, no size and no plan content --
            # 12 of 12 on each -- which is correct and which the compound question
            # gets wrong 5 times in 12. What the split cost was p10, whose only real
            # ground is a bare directional change that `states_size` did not admit:
            # it answered absent 11 of 12 there. Effective how_2 accuracy went 96.7%
            # -> 93.3%, twelve false denials against six, and `states_size` sat at
            # 43.8% met while the other two grounds ran near 60%.
            {"what": "names_enabler",
             "reported": True,
             "verdicts": ["met", "absent", "unclear"],
             "desc": "Read all three boxes. Does the response name something the "
                     "student PUT IN PLACE so the behaviour would happen — an "
                     "arrangement, a routine, a stand-in activity, a chosen hour "
                     "or location? `absent` when it names only the conditions it "
                     "found itself in, or only the behaviour the plan targeted"},
            {"what": "states_size",
             "reported": True,
             "verdicts": ["met", "absent", "unclear"],
             # WIDENED to admit a bare DIRECTION of change. The first split asked
             # this against a literal list -- a figure, a week comparison, or the
             # data -- and refused p10's "{{corpus:2a/p10:how1:49:78:sha=b3bf32bf0304}}" 11 times
             # in 12, which cost the cell, while the compound question had accepted
             # the same words 12 of 12. A stated rise or fall over the period is a
             # report of the change and belongs here.
             "desc": "Read all three boxes. Does the response state the change with "
                     "its SIZE — a figure, a comparison against the earlier week, "
                     "or the data — OR state a DIRECTION of change over the period, "
                     "that something rose or fell, even with no number attached?"},
            {"what": "names_plan_content",
             "reported": True,
             "verdicts": ["met", "absent", "unclear"],
             # A CONTRAST QUESTION, not a category one. The first split asked whether
             # the response named the plan's content "in particulars" and left
             # `particulars` undefined -- the enumeration had been stripped for
             # leakage -- so p5, the only cell this ground exists for, answered met
             # just 8 times in 12. Folding the exclusion into the question gives the
             # model something to compare against.
             "desc": "Read all three boxes. Does the response say anything about the "
                     "plan BEYOND naming the behaviour it targeted — what was to be "
                     "done, in what fixed form, or in what quantity? It counts even "
                     "where the response raises that as a burden rather than as "
                     "something that worked. Naming only the targeted behaviour is "
                     "not this ground"},
            # COMPUTED from the three above, never asked: absent exactly when all
            # three are absent. `forbid` strips its key from the schema, which is
            # right for an operand and is why it cannot be used on how_2 itself.
            {"what": "mechanism_named",
             "reported": True,
             "verdicts": ["met", "absent"],
             "desc": "Whether the response accounts for HOW the plan produced its "
                     "result, on any of the three grounds above"},
        ],
        "deductions": [
            {"code": "BLANK", "pts": 6.0, "text": "did not answer"},
            {
                "code": "NO_VERDICT",
                "pts": 2.0,
                "text": (
                    "-2 pts: did not answer if the implementation of your {{corpus:2a/p1:verdict:25:33:sha=08bf2418cca9:shape=R8-0-20}}"
                    "{{corpus:2a/p1:verdict:34:73:sha=01bf2bdf0aa5}} your behavior or not"
                ),
            },
            {
                "code": "MISSING_HOW",
                "pts": 2.0,
                "text": "-2 pts: missing one sentence describing how your behavior was "
                "or was not successfully modified",
                "repeatable": True,
            },
        ],
        "guidance": [
            "Three 2-point slots, judged INDEPENDENTLY: the verdict box, then each "
            "of the two How boxes. Do not ask how many explanations the answer "
            "contains.",
            "A How BOX IS MET ON EITHER OF TWO GROUNDS, and the second is the one "
            "to get right. First, a cause or a circumstance: why or when the plan "
            "did or did not work. A qualified explanation is still an explanation, "
            "and it need not be circumstantial at all — naming the techniques the "
            "student leaned on, with no situation attached, counts. Second, the "
            "change REPORTED WITH ITS SIZE: a figure, a comparison against the "
            "earlier week, or a citation of the data. That is an explanation on "
            "this item, not a bare outcome, and the earlier wording of this rubric "
            "said so — \"a verdict that cites the data as its evidence ... covers "
            "the verdict and both explanations\". A rule that charged boxes of that "
            "shape was measured on 2026-09-02 and broke three cells the graders "
            "credit.",
            "ONE COMBINATION IS ALSO ABSENT, and it must be read as a "
            "conjunction rather than as either half. A box is absent when what it "
            "reports is a bodily or personal state rather than the behaviour, AND "
            "the condition it attaches that state to is the behaviour NOT being "
            "done. NEITHER HALF WORKS ALONE, which is why the pair is stated: a "
            "state attributed to DOING the behaviour is an explanation and the "
            "graders credit it, and a box that says when things went badly is an "
            "explanation too whenever its subject is the behaviour, which the "
            "graders also credit. Only the two together — a symptom, tied to not "
            "doing the thing — fail to say how the plan itself fared.",
            "DEDUCT ONLY WHEN A BOX OFFERS NEITHER — no reason and no measure. Two "
            "shapes were charged. A sentence reporting a bodily or "
            "circumstantial detail that explains nothing about the plan working: the "
            "graders wrote 'your third sentence does not explain how your plan was "
            "successful' and took 2 points. And an answer that cannot settle whether it "
            "worked at all, hedging the verdict instead of explaining either outcome: "
            "'need more explanation on how it was or was not successful', also 2.",
            "Success or failure is irrelevant to the score; only whether it is stated and "
            "explained.",
        ],
        "context": ["1a"],
    },
    {
        "id": "2b",
        "label": "2b",
        "max": 6.0,
        "increment": 2.0,
        "question": (
            "Write an overall assessment of your intervention: which aspects were "
            "effective and which were not, including personal observations about your "
            "execution (for example, how your reinforcements or punishments worked). At "
            "least 3 sentences."
        ),
        # Derived, not model-authored: one slot, one deduction, so the
        # stacking the plain path allowed is unrepresentable.
        "derive_from_credit": True,
        "blank_code": "BLANK",
        # The most literal case in the set: the guidance says the graders "counted
        # substantive sentences ... and deducted only when fewer than three were
        # present". That is a count and a threshold, so the model supplies the
        # count and the threshold lives in code.
        "counts": [{"key": "sentences_given",
                    "slots": ["sentence_1", "sentence_2", "sentence_3"]}],
        "credit": [
            {
                "what": "sentences_given",
                "reported": True,
                "verdicts": ["3", "2", "1", "0"],
                "desc": "HOW MANY substantive sentences about the intervention the "
                        "response gives — count generously: sentences about what "
                        "worked, what did not, and how the student executed the plan "
                        "all count, and quality of insight is not judged. Answer 3 for "
                        "three or more",
            },
            {"what": "sentence_1", "pts": 2.0,
             "codes": {"absent": "MISSING_SENTENCE"},
             "desc": "First substantive sentence about the intervention"},
            {"what": "sentence_2", "pts": 2.0,
             "codes": {"absent": "MISSING_SENTENCE"},
             "desc": "Second substantive sentence"},
            {"what": "sentence_3", "pts": 2.0,
             "codes": {"absent": "MISSING_SENTENCE"},
             "desc": "Third substantive sentence"},
        ],
        "deductions": [
            {"code": "BLANK", "pts": 6.0, "text": "did not answer"},
            {
                "code": "MISSING_SENTENCE",
                "pts": 2.0,
                "text": "-2 pts: missing a sentence",
                "repeatable": True,
            },
        ],
        "guidance": [
            "Three 2-point slots, one per assessment sentence. This item is graded "
            "generously: the graders counted substantive sentences about the intervention "
            "and deducted only when fewer than three were present.",
            "Sentences about what worked, what did not, and how the student executed the "
            "plan all count. Do not deduct for quality of insight.",
        ],
        "context": ["2a"],
    },
    {
        "id": "3",
        "label": "3",
        "max": 6.0,
        "increment": 3.0,
        "question": (
            "What could be done differently next time to improve your intervention plan? "
            "Give at least 2 specific examples. ('Nothing would change' is not acceptable "
            "— every intervention can be improved.)"
        ),
        # Derived, not model-authored: one slot, one deduction, so the
        # stacking the plain path allowed is unrepresentable.
        "derive_from_credit": True,
        "blank_code": "BLANK",
        # "Count DISTINCT proposed changes, generously" — so count them once. The
        # two slots are interchangeable instances behind ONLY_ONE; which of the two
        # is missing was never a distinction this item could express.
        "counts": [{"key": "changes_given", "slots": ["example_1", "example_2"]}],
        "credit": [
            {
                "what": "changes_given",
                "reported": True,
                "verdicts": ["2", "1", "0"],
                "desc": "HOW MANY DISTINCT changes the response proposes — count "
                        "generously: a change to the reinforcer and a change to the "
                        "schedule are two even in one sentence, and any concrete "
                        "alternative counts without justification or feasibility. A "
                        "statement that nothing needs changing counts as none. Answer 2 "
                        "for two or more",
            },
            {"what": "example_1", "pts": 3.0,
             "codes": {"absent": "ONLY_ONE"},
             "desc": "First specific change they would make"},
            {"what": "example_2", "pts": 3.0,
             "codes": {"absent": "ONLY_ONE"},
             "desc": "Second specific change"},
        ],
        "deductions": [
            {
                "code": "BLANK",
                "pts": 6.0,
                "text": (
                    "-6 pts: Every intervention and study can be improved! You did not "
                    "provide two examples of what could be done differently next time to "
                    "improve your intervention plan"
                ),
            },
            {
                "code": "ONLY_ONE",
                "pts": 3.0,
                "text": "-3 pts: only provided one example of a change",
            },
        ],
        "guidance": [
            "Two 3-point slots. Count DISTINCT proposed changes, generously — a change to "
            "the reinforcer and a change to the schedule are two, even in one sentence.",
            "A statement that nothing needs changing is not a proposed change, and "
            "does not add to the count.",
            "IMPLICIT (from gold): the graders accepted any concrete alternative the "
            "student would try; they did not require justification or feasibility.",
        ],
        "context": ["2a", "2b"],
    },
]

BY_ID = {it["id"]: it for it in ITEMS}
TOTAL = sum(it["max"] for it in ITEMS)  # 40.0 scored; +10 upload = 50
