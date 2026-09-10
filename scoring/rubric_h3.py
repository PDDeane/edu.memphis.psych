"""Handout 3 rubric as data: 6 items, 40 points.

Sources as before: the Handout 3 scoring dictionary for point splits and
canonical wording, plus the graders' 20 rows for criteria the dictionary omits.

What makes this handout different: **item 1c is scored from a graph, not from
text**, and it is 10 of the 40 points. A submission can carry its graph three
ways — as an OOXML chart part, as an embedded image, or as grouped drawing
shapes whose labels arrive as ordinary document text — and the blank template
ships its own worked example graph ("Water Consumption Over Four Weeks") that
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
            # and p14 only "Week One and Week Three"; gold gave both the full 8,
            # and both systems docked 2 for the week that went unnamed. The label
            # is not the evidence -- the arc is.
            {
                "what": "baseline_week",
                "pts": 2.0,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "MISSING_WEEK", "unclear": "MISSING_WEEK"},
                "desc": "Discusses the baseline week",
                "rule": "is the BEFORE state given — the level the behaviour ran at prior to the intervention? A sentence that looks back before the plan began and gives the rate the behaviour ran at then is `met`; so is any pre-intervention figure or description. `absent` when the answer opens at the intervention and never says what came before: an answer beginning \"in the first week of my plan I was still up past midnight most nights\" starts the clock at the intervention, and loses exactly this slot and no other. AND THE BEFORE STATE MUST BE LOCATED IN TIME, not merely implied by contrast. It is `met` when the sentence SITUATES the figure in the period before the plan — by naming that period, or by naming the first week as a period of its own, which is enough on its own even with no figure attached. It is `absent` when a former quantity appears only as the contrast a later figure is set against, with nothing saying WHEN it held: a clause that sets what used to be done against what came later names no period at all, and the graders charged an answer of exactly that shape. The test is whether a reader can tell WHICH STRETCH the figure belongs to",
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
            "One point per week of data present: baseline, week 1, week 2, week 3.",
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
        # ADOPTED FROM THE .olx 2026-09-08, the twelfth and last hand-authored
        # sheet attribute. `template` is the WORKED EXAMPLE'S OWN DATA, one row
        # per field: `agreement.apply_computed` answers `mismatch` when the
        # student's plotted numbers equal it exactly, because that means they
        # graphed the example instead of their own weeks. `complete` also
        # answers `absent` when SOME but not all of the fields hold numbers.
        # The numbers were transcribed from what ships, so generating this
        # attribute changed no prompt.
        "derived": [
            {"key": "has_own_graph", "kind": "complete",
             # `fields`, the name `agreement.apply_computed` reads. score.py
             # cannot compute a `complete` check at all (its
             # DERIVED_KINDS_IMPLEMENTED covers `contains` only), so there is
             # no second consumer to scope this key away from.
             "fields": ["bmod_h3_baseline", "bmod_h3_wk1",
                        "bmod_h3_wk2", "bmod_h3_wk3"],
             "template": [[8, 10, 8, 12, 6, 10, 0],
                          [32, 20, 22, 28, 30, 32, 10],
                          [30, 28, 26, 30, 32, 32, 30],
                          [25, 26, 30, 32, 32, 28, 32]]},
        ],
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
                     "\"Sunday, Monday, ...\" along the bottom is tick data; \"Days "
                     "of the Week\" is the label. This distinction is the single most "
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
                "what": "series_box_holds",
                "reported": True,
                "verdicts": ["period_names", "other_real_names",
                             "software_placeholders", "nothing"],
                # SUBGOAL Q30, 2026-09-06. The reading moves into a PICK and the
                # VERDICT becomes computed -- the split subgoals Q33 and Q43 made.
                # WHY: read out over all twenty cells, `legend` recognises THE
                # FOUR PERIOD NAMES AND NOTHING ELSE --
                #   14 cells  "Baseline, Week 1..." (incl. "Baselline",
                #             "BaseLine", "Week One")        -> met 12/12
                #    4 cells  empty box                      -> absent 12/12
                #    1 cell   "Series1, Series2" (p12)       -> incomplete 12/12
                #    1 cell   "Sunday, Monday, ..." (p11)    -> absent 12/12
                # The rule's general clause -- any real names the student chose,
                # "including one that shows the chart was plotted the other way
                # round" -- has EXACTLY ONE cell to prove itself on and fails
                # there. It was reworded and measured; 1c has been swept since and
                # p11 is unmoved at 0/12.
                # A PICK PASSES THE TEST THE Q6 RECORD SETS: the categories
                # separate mechanically. A list of weekday names is plainly real
                # names, not placeholders, not empty -- no honest competing
                # classification, unlike Q6/p2 where `met_differently` was
                # defensible and the pick credited the cell anyway.
                # THE 14 PERIOD CELLS ARE SAFE BY CONSTRUCTION: period_names maps
                # to `met`, which is what they already answer.
                "desc": "What the series box holds",
                "rule": (
                    "ONE ANSWER, naming what is in the box. Do not judge whether "
                    "it makes a good legend -- say what it holds and the "
                    "arithmetic follows.\n"
                    "  `period_names` -- the four periods the assignment asks "
                    "for: baseline and the three weeks, however spelled or "
                    "abbreviated.\n"
                    "  `other_real_names` -- any OTHER names the student chose and "
                    "typed themselves. Days of the week, session numbers, "
                    "activity names all count. This is the answer when the chart "
                    "was plotted the other way round, with the periods along the "
                    "bottom and something else as the series.\n"
                    "  `software_placeholders` -- names the spreadsheet supplies "
                    "when nobody typed any: `Series1`, `Series2`, `Column1` and "
                    "the like.\n"
                    "  `nothing` -- the box is empty."
                ),
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
                # SUBGOAL Q30, 2026-09-05. The rule used to require the series names
                # to be the four PERIODS, and the item's question does not: it asks
                # for "a title, both axis labels, and a legend". p11 labels its
                # series with day names -- a real legend of the student's own, on a
                # chart plotted the other way round -- and gold charged x, y and the
                # baseline week while leaving the legend alone. We charged it 2, and
                # that is the whole of the cell's 4.00-against-6.00 gap.
                #
                # THE FIXTURE IS NOT THE CAUSE and this was checked before the rule
                # was touched: `series` comes from `sim` and holds the student's
                # literal legend, which is exactly what the box is for. handouts.py
                # and BACKLOG.md both record it, the second having already corrected
                # a stale note that explained the cell away.
                #
                # p12 IS THE SUPPORTING CELL and it is why the failing verdict stays:
                # its series read "Series1, Series2", the software's own placeholders,
                # gold charges it, and we agree 12 of 12. So the line gold draws is
                # between a legend that NAMES the student's series and one that names
                # nothing -- not between naming the periods and naming anything else.
                "rule": "the NO_LEGEND test. `met` when the box holds the student's "
                     "own names for the series they plotted, whatever those names "
                     "refer to — the four periods ('Baseline, Wk1, Wk2, Wk3') are "
                     "the common case and count, and so does any other set of real "
                     "names the student chose, including one that shows the chart "
                     "was plotted the other way round. The question asks for a "
                     "legend, not for particular names. `{fail}` when the names are "
                     "the SOFTWARE'S PLACEHOLDERS rather than the student's — "
                     "'Series1', 'Series2' and the like name nothing and are what "
                     "appears when no names were ever typed; `absent` when the box "
                     "is empty or holds something that is not a set of series names "
                     "at all. Judge the series names, not the heading",
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
            "titled 'Water Consumption Over Four Weeks', with axes 'Days of the Week' and "
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
             # data -- and refused p10's "endurance increased over time" 11 times
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
                    "-2 pts: did not answer if the implementation of your behavior "
                    "modification plan successfully modified your behavior or not"
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
            # WHY THE SECOND GROUND IS HERE, kept OUT of the bullet. This
            # guidance used to close with a sentence citing an older draft of
            # the rubric and then reporting a dated sweep -- the date, a cell
            # count, and our own vocabulary -- as the ARGUMENT FOR the rule.
            # It shipped to BOTH graders, neither of which can act on any of
            # it, and the rule itself is complete in the two sentences before.
            # Paraphrased rather than quoted here on purpose: reproducing the
            # sentence verbatim would leave the very text the edit removes
            # sitting in the file, which is what editguard refused twice.
            # The finding that caught it:
            # enforcement.check_prompts_carry_no_process_history.
            "A How BOX IS MET ON EITHER OF TWO GROUNDS, and the second is the one "
            "to get right. First, a cause or a circumstance: why or when the plan "
            "did or did not work. A qualified explanation is still an explanation, "
            "and it need not be circumstantial at all — naming the techniques the "
            "student leaned on, with no situation attached, counts. Second, the "
            "change REPORTED WITH ITS SIZE: a figure, a comparison against the "
            "earlier week, or a citation of the data. That is an explanation on "
            "this item, not a bare outcome.",
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


MAPS: dict[str, list] = {
    # SUBGOAL Q30. Emits the SHEET's vocabulary -- met/absent/INCOMPLETE -- not
    # the rubric's `codes` key `not_described`. Subgoal E27 declares that pair as
    # counterparts by design ("the web's `incomplete` is the paper's
    # `not_described`, 5 slots, 1c's chart parts"), and subgoal E52's rule is that
    # a map emits what the GRADER is offered, which is the sheet's vocabulary.
    "1c": [
        {"key": "legend", "pick": "series_box_holds",
         "pairs": [{"value": "period_names", "verdict": "met"},
                   {"value": "other_real_names", "verdict": "met"},
                   {"value": "software_placeholders", "verdict": "incomplete"},
                   {"value": "nothing", "verdict": "absent"}],
         "fallback": "absent"},
    ],
}

# ATTACHING IT IS A SEPARATE STEP, AND IT WAS MISSING. Defining MAPS does
# nothing on its own: the generator reads `maps` off the ITEM SPEC, so the table
# has to be hung on the item. rubric_h1 has carried this loop since maps existed;
# this module got the table under subgoal Q30 and not the loop, so `maps=""` in
# the sheet stayed empty, `olx_prompts.py --check` reported H3 "up to date"
# because the generator correctly emitted nothing, and the pick `series_box_holds`
# had no route to the `legend` verdict at all.
#
# NOTHING WOULD HAVE CAUGHT IT. The sheet declared the slot, the rubric declared
# the map, both halves passed every static gate, and E46's unreachable-verdict
# check compares a map against a verdict list -- with no map attached there is
# nothing for it to compare. It was found only because subgoal Q30's own sweep
# script asserted that the pick, the choices group and the maps rule all live in
# ONE action, and refused at that step before spending ~230 calls.
for _it in ITEMS:
    if _it["id"] in MAPS:
        _it["maps"] = MAPS[_it["id"]]

# THE SLOT SHEET, ADOPTED FROM THE .olx ON 2026-09-08 so that a design change
# never needs a hand edit to the generated file. `slots=` was the LAST large
# hand-authored attribute: 217 clauses, 14,159 characters, and 159 of those
# clauses carried an option list the rubric could not supply -- so this is not a
# reconciliation like `equals` or `onlyif` were, it MOVES the slot sheet's
# primary definition here. Transcribed field-wise (never as a raw string) after
# proving the parse round-trips losslessly on all 23 items, so
# `olx_prompts.slots_attr_for` reproduces every attribute byte-for-byte and the
# switch-on changed no prompt and moved no prompt_sha.
#   key   the slot id            gate  True where the .olx wrote a `!` prefix
#   label the short prose the grader sees beside the id
#   seg   field 3: an option list, `pick(set)` or `count(n)`
#   pts   the `@N` suffix
# ORDER IS PART OF THE DESIGN and is the order of this list -- see the
# SLOT_OPTIONS note above; a reorder is a real prompt change with its own sweep.
SLOT_SPEC: dict[str, list[dict]] = {
    '1a': [
        {'key': 'distinguishes_periods', 'label': 'Separates the time periods at all', 'gate': True, 'seg': 'unclear'},
        {'key': 'baseline_week', 'label': 'Covers the baseline week', 'seg': 'unclear', 'pts': '2'},
        {'key': 'week_1', 'label': 'Covers week 1', 'seg': 'unclear', 'pts': '2'},
        {'key': 'week_2', 'label': 'Covers week 2', 'seg': 'unclear', 'pts': '2'},
        {'key': 'week_3', 'label': 'Covers week 3', 'seg': 'unclear', 'pts': '2'},
        {'key': 'confident', 'label': 'All judgments confident'},
    ],
    '1c': [
        {'key': 'has_own_graph', 'label': 'Your 1b data produces a graph of your own', 'gate': True, 'seg': 'mismatch', 'pts': '2'},
        {'key': 'title', 'label': 'Title saying what is measured and over what period', 'seg': 'generic', 'pts': '2'},
        {'key': 'x_axis_label', 'label': 'X-axis label naming what the axis represents', 'seg': 'tick_values', 'pts': '2'},
        {'key': 'y_axis_label', 'label': 'Y-axis label naming what the axis represents', 'seg': 'tick_values/generic', 'pts': '2'},
        {'key': 'series_box_holds', 'label': 'What your series box holds', 'seg': 'pick(series_kind)'},
        {'key': 'legend', 'label': 'Legend naming all four series you plotted', 'seg': 'incomplete', 'pts': '2'},
        {'key': 'confident', 'label': 'All judgments confident'},
    ],
    '2a': [
        {'key': 'verdict', 'label': 'States whether the plan worked', 'seg': 'unclear', 'pts': '2'},
        {'key': 'how_1', 'label': 'Whether the How (1) box explains how', 'seg': 'unclear', 'pts': '2'},
        {'key': 'how_2', 'label': 'Whether the How (2) box explains how', 'seg': 'unclear', 'pts': '2'},
        {'key': 'names_enabler', 'label': 'Whether the response names something put in place', 'seg': 'unclear'},
        {'key': 'states_size', 'label': 'Whether the response states the size or direction of the change', 'seg': 'unclear'},
        {'key': 'names_plan_content', 'label': 'Whether the response says anything about the plan beyond the behaviour', 'seg': 'unclear'},
        {'key': 'mechanism_named', 'label': 'Whether any mechanism ground holds'},
        {'key': 'confident', 'label': 'All judgments confident'},
    ],
    '2b': [
        {'key': 'sentences_given', 'label': 'How many substantive assessment sentences you give', 'seg': 'count(3)'},
        {'key': 'sentence_1', 'label': 'First substantive assessment sentence', 'seg': 'unclear', 'pts': '2'},
        {'key': 'sentence_2', 'label': 'Second substantive sentence', 'seg': 'unclear', 'pts': '2'},
        {'key': 'sentence_3', 'label': 'Third substantive sentence', 'seg': 'unclear', 'pts': '2'},
        {'key': 'confident', 'label': 'All judgments confident'},
    ],
    '3': [
        {'key': 'changes_given', 'label': 'How many distinct changes you propose', 'seg': 'count(2)'},
        {'key': 'example_1', 'label': 'First specific change', 'seg': 'unclear', 'pts': '3'},
        {'key': 'example_2', 'label': 'Second, different change', 'seg': 'unclear', 'pts': '3'},
        {'key': 'confident', 'label': 'All judgments confident'},
    ],
}
