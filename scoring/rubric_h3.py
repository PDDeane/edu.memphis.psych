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
        "credit": [
            {
                "what": "distinguishes_periods",
                "gates": True,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "NO_WEEKLY_BREAKDOWN", "unclear": "NO_WEEKLY_BREAKDOWN"},
                "desc": "Separates the baseline period from the intervention weeks at all. NO_WEEKLY_BREAKDOWN (-8) is for an answer that never distinguishes any time periods — no before/after, no weeks. That took the full 8 from participants 1 and 15. Do not use it when some periods are discussed; deduct per missing period instead.",
            },
            {
                "what": "baseline_week",
                "pts": 2.0,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "MISSING_WEEK", "unclear": "MISSING_WEEK"},
                "desc": "Discusses the baseline week",
            },
            {
                "what": "week_1",
                "pts": 2.0,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "MISSING_WEEK", "unclear": "MISSING_WEEK"},
                "desc": "Discusses week 1",
            },
            {
                "what": "week_2",
                "pts": 2.0,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "MISSING_WEEK", "unclear": "MISSING_WEEK"},
                "desc": "Discusses week 2",
            },
            {
                "what": "week_3",
                "pts": 2.0,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "MISSING_WEEK", "unclear": "MISSING_WEEK"},
                "desc": "Discusses week 3",
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
            "the before/baseline state at all: participant 6 began \"During the first week "
            "of my data collection intervention...\" and lost 2 points for having no "
            "sentence pertaining to the baseline week.",
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
                     "never types one, and that counts as missing. Participant 8's "
                     "graph carries the literal text \"Chart Title\" and the grader "
                     "deducted the title point",
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
                "what": "legend",
                "pts": 2.0,
                "desc": "The graph has a legend — the key naming the plotted series "
                     "(Baseline / Week 1 / Week 2 / Week 3). A single-series graph with "
                     "no key has no legend",
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
            "`mismatch` and the whole item is 0 — participant 4 was scored 'Did not "
            "provide a graph' on a file that contains a chart. A student's own graph plots "
            "THEIR behaviour (hours of sleep, minutes of exercise, servings) over their "
            "four weeks.",
            "The bundle marks each piece of evidence as `student` or `template`. Trust "
            "those labels for chart parts; for an image you are shown, judge the content.",
            "Shape-drawn graphs arrive as run-together text with the axis tick values "
            "jammed against the labels ('Excersing Over Four Weeks2.521.510.50 Sunday "
            "Monday...'). Read the title and any series names out of it; series names "
            "(Baseline / Week 1 / Week 2 / Week 3) appearing together indicate a legend.",
            "A WRITTEN DESCRIPTION OF A GRAPH IS NOT A GRAPH. Tidy label prose — "
            "'Title: Sleep Duration Over 4 Weeks / X-axis label: Days / Y-axis label: "
            "Hours of Sleep / Legend: Baseline, Week 1...' — is the student listing what "
            "their graph WOULD contain, with no plotted data. Participant 20 wrote exactly "
            "that and was scored 'did not include'. A real shape-drawn graph carries "
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
        # The guidance is "COUNT CONTENT, NOT SENTENCES", so the model counts and
        # the arithmetic stays here. The two `how` slots are interchangeable
        # instances behind one code; the verdict slot is a distinct judgement and
        # stays a judgement.
        "counts": [{"key": "hows_given", "slots": ["how_1", "how_2"]}],
        "credit": [
            {
                "what": "verdict",
                "pts": 2.0,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "NO_VERDICT", "unclear": "NO_VERDICT"},
                "desc": "States whether the plan was successful",
            },
            {
                "what": "hows_given",
                "reported": True,
                "verdicts": ["2", "1", "0"],
                "desc": "HOW MANY separate pieces of explanation of HOW the plan "
                        "succeeded or failed the response gives — count CONTENT, not "
                        "sentences: one compound sentence that states the outcome and "
                        "explains it can carry two. Ignore any stretch that does not "
                        "bear on how the plan succeeded or failed. Answer 2 for two or "
                        "more",
            },
            {"what": "how_1", "pts": 2.0,
             "codes": {"absent": "MISSING_HOW"},
             "desc": "First explanation of HOW it succeeded or failed"},
            {"what": "how_2", "pts": 2.0,
             "codes": {"absent": "MISSING_HOW"},
             "desc": "Second explanation of HOW it succeeded or failed"},
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
            "Three 2-point slots: the verdict, then two pieces of explanation of HOW.",
            "COUNT CONTENT, NOT SENTENCES. A compound sentence that states the outcome and "
            "explains it satisfies more than one slot. Two sentences can earn all six "
            "points, and three shapes did. A verdict that cites the data as its "
            "evidence, followed by one concrete circumstance under which the plan "
            "worked, covers the verdict and both explanations. So does a verdict "
            "citing the data, followed by an admission of inconsistency and the "
            "progress made anyway — a qualified explanation is still an "
            "explanation. And an explanation need not be circumstantial at all: "
            "naming the techniques the student relied on, with no situation "
            "attached, counts. All three earned 6/6.",
            "DEDUCT when a stretch of the answer does NOT bear on how the plan succeeded "
            "or failed. Participant 1 lost 2 points because a sentence about their stomach "
            "being unsettled explained nothing about the plan working — the grader wrote "
            "'your third sentence does not explain how your plan was successful'. "
            "Participant 14 lost 2 for an answer that could not settle on whether it "
            "worked ('I do not know how to determine the success rate') — 'need more "
            "explanation on how it was or was not successful'.",
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
