"""Handout 2 rubric as data: 12 scored items, 40 points.

Sources, same priority as Handout 1:
  1. "Handout 2 - Scoring & Feedback Dictionary_.docx" — point splits and the
     canonical feedback wording.
  2. The graders' 20 rows in "Handout 2 - Scoring & Feedback.xlsx", which
     carry criteria the dictionary never states (marked IMPLICIT).

Shape of this handout, and how it differs from Handout 1:

  * Scoring is close to BINARY. Across the gold rows PR and NP take only the
    values 0 or 4, and most other items sit at 0 / half / full. The dictionary
    prescribes a 2-point partial credit for "right operant-conditioning family,
    wrong type", but the graders used it sparingly. Encode both and let the
    ledger decide; do not expect a smooth distribution.
  * The 20 scenario items from the paper handout are NOT scored here. They were
    never transcribed into the typed submissions (0 of 20 files contain them)
    and have no gold column. The recovered answer key for them lives outside
    this scorer.
  * The remaining 10 points of the 50-point handout are for submitting the
    written and the typed version. Out of scope — see README.
"""

from __future__ import annotations

# The four operant-conditioning types, as the course defines them.
_OC_FRAME = (
    "Operant conditioning has exactly four types, defined by two questions: is "
    "the target behaviour being INCREASED (reinforcement) or DECREASED "
    "(punishment), and is a stimulus being ADDED (positive) or TAKEN AWAY "
    "(negative)?\n"
    "  - Positive Reinforcement: add something desirable to increase a behaviour.\n"
    "  - Negative Reinforcement: take away something undesirable to increase a behaviour.\n"
    "  - Positive Punishment: {{corpus:D1/p8:d1:32:60:sha=60e5588ab7ff}} decrease a behaviour.\n"
    "  - Negative Punishment: take away something desirable to decrease a behaviour."
)

# Criteria the graders applied on every example item but the dictionary never
# states. These are the difference between 0 and 4 on the four example items —
# five of the twenty students scored 0 on PR and NP for precisely these.
_EXAMPLE_RULES = [
    "TEST 1 — IS THERE AN EXPLICIT CONTINGENCY? This is the primary test and it "
    "is about FORM. A creditable answer links the behaviour to the consequence "
    "conditionally: \"If I [do / fail to do the behaviour], I will [gain / "
    "lose Y]\". An answer that names a reward without tying it to the behaviour "
    "fails even though a reward is present. Naming the behaviour to be increased "
    "and then a reward on a FIXED SCHEDULE — one given every so many weeks, "
    "rather than after the behaviour — scored 0, the grader asking the student "
    "to state the exact behaviour and what is added once it is exhibited. A "
    "bare prediction with no plan at all (\"{{corpus:NP/p1:np:0:17:sha=868176d33c58:shape=R17-0-20}}"
    "{{corpus:NP/p1:np:18:29:sha=88dbce75bea2}} tired\") also scores 0.",
    "TEST 2 — DOES THE CONSEQUENCE ARRIVE AFTER THE BEHAVIOUR? \"Remember that "
    "what you take away or add has to happen after the behavior is exhibited.\" "
    "Judge the DELIVERY, not the wording. A privilege WITHHELD until a weekly "
    "goal is met passes: it is delivered once the goal is met, which is the "
    "ordinary shape of a reinforcement contingency, and the graders credited "
    "it. What fails is a plan where nothing is ever delivered contingent on the "
    "behaviour — leaving a temptation somewhere else, or putting a device away "
    "beforehand, are antecedent manipulations that remove the temptation in "
    "advance and never tie anything to performing the behaviour.",
    "TEST 3 — WHICH OF THE FOUR TYPES IS IT? Before crediting a type, answer the "
    "two questions explicitly: is the behaviour being INCREASED or DECREASED, "
    "and is something being ADDED or TAKEN AWAY? Then compare with the type "
    "under discussion. Well-formed contingencies of the WRONG type are the most "
    "commonly missed deduction on this handout, and three shapes recur. ADDING a "
    "privilege for staying within a limit is PR, not NR (-2). ADDING a loss for "
    "missing the goal is NP, not NR (-2). A barrier the student must clear "
    "before performing the behaviour removes nothing once it is performed, so "
    "it is not NR either (-2).",
    "WHAT COUNTS AS THE ADDED OR REMOVED THING — BE BROAD. It does not have to "
    "be a physical object. Removing an unpleasant OBLIGATION, chore, or "
    "requirement is a perfectly good negative reinforcer. The graders gave full "
    "credit wherever meeting the goal SPARED the student something they would "
    "otherwise have had to do — an early start to make up procrastinated work, "
    "a compensating nap, getting out of bed at once. Do NOT deduct these as "
    "intrinsic outcomes.",
    "NOT_EXTERNAL_STIMULUS is reserved for the narrow case where the named "
    "consequence is simply the behaviour's own automatic result AND no "
    "conditional plan is stated — the canonical zero is \"{{corpus:PR/p1:pr:0:18:sha=04923497e5d4:shape=R18-0-20}}"
    "{{corpus:PR/p1:pr:19:42:sha=d177395a37c4}} body\". If the answer is phrased as an if/then "
    "arrangement the student sets up, this code does not apply; judge it on "
    "tests 2 and 3 instead.",
    "SAFETY: flag, but do not deduct for, any example that withholds food, "
    "sleep, or medical care, or that punishes with exercise in a way that could "
    "harm the student. The graders wrote notes like \"Please change this example "
    "to remove something not related to meals. It is important to us that you "
    "are safe and healthy throughout this behavior modification!\" while leaving "
    "the score at full.",
]


def _example_item(item_id: str, label: str, type_name: str, abbrev: str, definition: str) -> dict:
    """One of the four 'write an example of X' items, worth 4 points each."""
    return {
        "id": item_id,
        "label": label,
        "max": 4.0,
        "increment": 2.0,
        "question": (
            f"Write an example of {type_name} that you could use to attempt to change "
            f"your behavior. ({type_name} = {definition}.) For reinforcement examples the "
            "student should be trying to increase their wanted goal behaviour; for "
            "punishment examples, to decrease their unwanted target behaviour."
        ),
        "derive_from_criteria": True,
        "expected_type": abbrev,
        "credit": [
            {
                "what": "is_operant_conditioning",
                "pts": 2.0,
                "desc": "Describes a real operant-conditioning contingency: an external "
                "stimulus added or removed after the behaviour",
            },
            {
                "what": f"is_{abbrev.lower()}",
                "pts": 2.0,
                "desc": f"That contingency is specifically {type_name}",
            },
        ],
        "deductions": [
            {
                "code": "NOT_OC",
                "pts": 4.0,
                "text": "This example is not Operant Conditioning.",
            },
            {
                "code": "WRONG_TYPE",
                "pts": 2.0,
                "text": (
                    f"This is not {type_name}. Remember, {type_name} involves "
                    f"{definition}. (Correct example of one of the four types, just not "
                    f"{abbrev}.)"
                ),
            },
            {
                "code": "NOT_EXTERNAL_STIMULUS",
                "pts": 4.0,
                "text": (
                    "Remember that what you add or take away after your behavior has to "
                    "be easily controlled by you and be an outside stimulus."
                ),
            },
            {"code": "BLANK", "pts": 4.0, "text": "did not answer"},
        ],
        "guidance": [_OC_FRAME] + _EXAMPLE_RULES + [
            "Award the two credit components separately: a valid contingency that names "
            "the wrong type keeps its first 2 points and loses the second (WRONG_TYPE). "
            "Something that is not a contingency at all loses all 4 (NOT_OC or "
            "NOT_EXTERNAL_STIMULUS — use whichever the grader would have written).",
        ],
        "context": ["_utb", "_wgb"],
    }


def _type_item(item_id: str, label: str, ordinal: str) -> dict:
    return {
        "id": item_id,
        "label": label,
        "max": 2.0,
        "increment": 2.0,
        "question": (
            f"State the {ordinal} type of Operant Conditioning you plan to use in your "
            "actual behavior modification intervention."
        ),
        # Derived, not model-authored: one slot, one deduction. The only slot, so
        # failing it costs the whole item either way — `absent` is BLANK and
        # `not_a_type` is NOT_A_TYPE, and the distinction is the feedback wording,
        # not the score.
        "derive_from_credit": True,
        "blank_code": "BLANK",
        "credit": [
            {
                "what": "type_stated",
                "pts": 2.0,
                "verdicts": ["met", "absent", "not_a_type"],
                "codes": {"absent": "BLANK", "not_a_type": "NOT_A_TYPE"},
                "desc": "Names one of the four operant-conditioning types",
            }
        ],
        "deductions": [
            {"code": "BLANK", "pts": 2.0, "text": "did not answer"},
            {
                "code": "NOT_A_TYPE",
                "pts": 2.0,
                "text": "This is not one of the four types of Operant Conditioning.",
            },
        ],
        "guidance": [
            _OC_FRAME,
            "This item asks only that a type be NAMED. Any of the four, spelled out or "
            "abbreviated, in any capitalisation, earns the full 2 points. Whether the "
            "choice is well matched to the student's behaviour is judged on the "
            "definition and example items, not here.",
            "Do not deduct here for a definition or example that contradicts the named "
            "type — that is scored on those items.",
        ],
        "context": ["_utb", "_wgb"],
    }


def _definition_item(item_id: str, label: str, ordinal: str, type_ctx: str) -> dict:
    return {
        "id": item_id,
        "label": label,
        "max": 2.0,
        "increment": 1.0,
        "question": (
            f"Define the {ordinal} type of Operant Conditioning you chose. A complete "
            "definition says whether something is being ADDED or TAKEN AWAY, and whether "
            "the behaviour is being INCREASED or DECREASED."
        ),
        # Derived, not model-authored, so that WRONG_DEFINITION stops being a
        # judgement the model makes and becomes the comparison it already has both
        # halves of. The web version has computed this since Tier 1; until now the
        # CLI asked for it, which was the last FIXABLE divergence on the books.
        "derive_from_credit": True,
        "blank_code": "BLANK",
        "equals": [
            {"key": "matches_chosen_type", "left": "defines_type",
             "right": "named_type", "lenient": ["unclear"],
             # A definition that cannot be pinned to a type, or a type slot left
             # blank, establishes no mismatch — the same guard `derive_oc_ledger`
             # puts on TYPE_MISMATCH.
             },
        ],
        "credit": [
            {
                "what": "defines_type",
                "reported": True,
                "verdicts": ["PR", "NR", "PP", "NP", "unclear"],
                "desc": "Which of the four types this DEFINITION describes, judged on its "
                        "content alone: something added or removed, behaviour increased or "
                        "decreased",
            },
            {
                "what": "named_type",
                "reported": True,
                "verdicts": ["PR", "NR", "PP", "NP", "unclear"],
                "desc": f"Which of the four the student CHOSE, read from {type_ctx} in the "
                        "context below; `unclear` only if it is blank or unreadable",
            },
            {
                "what": "matches_chosen_type",
                "gates": True,
                "verdicts": ["met", "absent"],
                "codes": {"absent": "WRONG_DEFINITION"},
                "desc": f"The definition describes the type the student named in "
                        f"{type_ctx}. A definition that is correct for a DIFFERENT "
                        f"type than the one they chose is WRONG_DEFINITION (-2), not "
                        f"merely incomplete",
            },
            {
                "what": "add_or_remove",
                "pts": 1.0,
                "verdicts": ["met", "absent"],
                "codes": {"absent": "INCOMPLETE_DEFINITION"},
                "desc": "States whether something is added or taken away",
            },
            {
                "what": "increase_or_decrease",
                "pts": 1.0,
                "verdicts": ["met", "absent"],
                "codes": {"absent": "INCOMPLETE_DEFINITION"},
                "desc": "States whether the behaviour increases or decreases",
            },
        ],
        "deductions": [
            {"code": "BLANK", "pts": 2.0, "text": "did not answer"},
            {
                "code": "WRONG_DEFINITION",
                "pts": 2.0,
                "text": "This is not the correct definition for the Operant Conditioning "
                "type you chose.",
            },
            {
                "code": "INCOMPLETE_DEFINITION",
                "pts": 1.0,
                "text": (
                    "-1 point: Did not provide the entire definition (Is something being "
                    "added or taken away? Is the behavior increasing or decreasing?)"
                ),
            },
        ],
        "guidance": [
            _OC_FRAME,
            "INCOMPLETE_DEFINITION is for a definition that is right as far as it goes "
            "but omits one of the two halves — e.g. says something is removed but never "
            "says the behaviour decreases.",
            "IMPLICIT (from gold): graders accepted textbook phrasing and the student's "
            "own words equally. A definition given in the course's technical register — "
            "naming the stimulus, its removal, and the behaviour it follows — earned "
            "full credit, and so did the same idea in ordinary words. Do not require "
            "the course's exact wording.",
        ],
        "context": ["_utb", "_wgb", type_ctx],
    }


def _example_use_item(
    item_id: str, label: str, ordinal: str, cadence: str, type_ctx: str, def_ctx: str
) -> dict:
    return {
        "id": item_id,
        "label": label,
        "max": 4.0,
        "increment": 1.0,
        "question": (
            f"Give a {cadence} example of how you will use your {ordinal} chosen type of "
            "Operant Conditioning during your intervention."
        ),
        "derive_from_criteria": True,
        "expected_type": None,  # must match whatever the student named in T1/T2
        "cadence": cadence,
        "credit": [
            {
                "what": "is_operant_conditioning",
                "pts": 2.0,
                "desc": "A real contingency: external stimulus added or removed after "
                "the behaviour",
            },
            {
                "what": "matches_chosen_type",
                "pts": 1.0,
                "desc": f"Matches the type named in {type_ctx}",
            },
            {
                "what": "targets_own_behavior",
                "pts": 1.0,
                "desc": "Targets the student's own UTB or WGB",
            },
            {
                # Added to spend the item's one unchargeable point. These four
                # items are worth 4 but only 3 were reachable by a scored slot
                # (TYPE_MISMATCH 2 + WRONG_BEHAVIOR 1); the 4th could be lost
                # ONLY by a gate, all-or-nothing. That is why the dominant error
                # here is over-credit — 7 of the 10 errors beyond tolerance are
                # cells where every gate passed and gold had deducted 3 or 4,
                # and nothing existed to take a partial bite out of them.
                #
                # Deliberately NARROW. The over-credited cells do not share one
                # statable property: "{{corpus:DAY2/p14:day2:22:55:sha=e4b4855d80e6}}" (gold 0)
                # and "{{corpus:DAY1/p15:day1:40:72:sha=e23fe0094031}} when I am caught up"
                # (gold 4) are structurally alike, so no criterion separates
                # them. What IS statable is the pair of patterns below, and the
                # slot claims only those.
                #
                # It claimed a SECOND pattern until it was measured: a
                # "consequence" that is only the absence of a penalty. That was
                # withdrawn. It collided with criterion 7 `avoidance_frame`,
                # which claims the same shape and whose decision is to FLAG AND
                # NEVER DEDUCT — a decision GOLD_DIVERGENCES declares as
                # ADDED_AVERSIVE_NAMED on p8's DAY1/WK1 (renamed from
                # AVOIDANCE_FRAMING 2026-08-24, and WK2 dropped from it), in the
                # words "score.py
                # flags for review and never deducts, and the lo-blocks sheet
                # reaches the same verdict". With one sentence serving as the
                # worked example for two criteria with opposite outcomes, the two
                # implementations split on it: the web answered `yes` on 3 of 3
                # runs while score.py charged the point. That broke equivalence
                # AND made score.py contradict its own declared divergence, so
                # the pattern went and criterion 7 now owns the shape outright.
                #
                # MEASURED, both before and after that withdrawal. Wired in at
                # all, the slot fired on 1 of 62 non-gated cells — and that one
                # cell was p8 DAY1, i.e. the collision. Counterfactually, over
                # identical model sheets with only the charge switched off and
                # on, exact match was 87.5% either way and MAE moved 0.347 ->
                # 0.333. So the only thing it ever charged was the thing it
                # should not have.
                #
                # What remains is the juxtaposition pattern, which fires nowhere
                # on this cohort. Keep it anyway: it is a real failure mode, it
                # is the item's only route to a partial deduction, and it costs
                # nothing when it does not fire. Do NOT widen it hoping for the
                # six genuinely over-credited cells — that is the prose-rewording
                # experiment this project has run four times and measured
                # neutral-to-negative each time. Reclaiming them needs a
                # criterion that separates them, which nobody has found.
                "what": "consequence_asserted",
                "pts": 1.0,
                "codes": {"no": "LINK_NOT_ASSERTED"},
                "desc": "The consequence is asserted to follow FROM the behaviour, "
                        "and is something added or taken away rather than the mere "
                        "absence of a penalty",
            },
        ],
        "deductions": [
            {"code": "BLANK", "pts": 4.0, "text": "did not answer"},
            {
                "code": "NOT_OC",
                "pts": 4.0,
                "text": "This example is not Operant Conditioning.",
            },
            {
                "code": "NOT_EXTERNAL_STIMULUS",
                "pts": 4.0,
                "text": (
                    "Remember that what you add or take away after your behavior has to "
                    "be easily controlled by you and be an outside stimulus."
                ),
            },
            {
                "code": "TYPE_MISMATCH",
                "pts": 2.0,
                "text": (
                    f"Your {cadence} example does not match the type of Operant "
                    "Conditioning that you previously chose."
                ),
            },
            {
                "code": "WRONG_BEHAVIOR",
                "pts": 1.0,
                "text": "The behavior you target in this example is not your chosen behavior.",
            },
            {
                "code": "CADENCE_MISMATCH",
                "pts": 4.0,
                "text": f"This is a {'weekly' if cadence == 'daily' else 'daily'} example.",
            },
            {
                "code": "LINK_NOT_ASSERTED",
                "pts": 1.0,
                "text": (
                    "Say that the consequence happens BECAUSE of the behavior, and make "
                    "it something you add or take away — not just the absence of a "
                    "penalty you would otherwise apply."
                ),
            },
        ],
        "guidance": [_OC_FRAME] + _EXAMPLE_RULES + [
            f"The example must match the type named in {type_ctx}. A correct example of a "
            "DIFFERENT one of the four types is TYPE_MISMATCH (-2), not NOT_OC. Apply "
            "test 3 above before crediting the match — do not assume the student's example "
            "is the type they named.",
            f"CADENCE: this item asks for a {cadence} example, and answering it at the "
            "wrong cadence voids it. A daily slot answered with a week-long contingency "
            "scored 0, the grader writing only \"This is a weekly example.\" Check that the "
            f"contingency actually operates {cadence}.",
            # DAY2 only. In the rubric rather than SLOT_NOTES because the gate has
            # no credit component to host a `rule`, and SLOT_NOTES reaches the web
            # alone — the enforcement check said so and was right.
            #
            # The cell: gold 4, we score 0 in every run, cadence_is_daily
            # `absent`, feedback "this is a weekly". The bare slot note already
            # says duration is not cadence and that a tie goes to daily, so the
            # model is not treating this as a tie — it thinks the answer is
            # PLAINLY weekly, and it has a second ground the note never rebuts:
            # this student's goal is stated as a weekly quantity, so "if I meet my
            # goal" looks weekly on its face.
            *(["CADENCE, TWO THINGS THAT DO NOT MAKE AN ANSWER WEEKLY. First, "
               "duration: a consequence that runs to the end of the week is how "
               "LONG the reward lasts, not how often the behaviour is checked, "
               "and a trigger checked each day whose reward lasts until Sunday is "
               "daily. Second, and the one that is missed: a goal expressed as a "
               "weekly QUANTITY — \"four days a week\", \"five sessions a week\" — "
               "is still checked day by day, because each day either counts "
               "toward it or does not. An answer keyed to \"{{corpus:NR/p2:nr:0:17:sha=bd6ad50ff8db:shape=C1}}\" is "
               "daily even when the goal itself is a weekly total. Answer that "
               "the cadence is wrong only when the student must WAIT FOR THE WEEK "
               "TO END before the contingency can fire at all — a whole-week "
               "tally scored on Sunday, one weekend reward for the week's "
               "performance."] if item_id == "DAY2" else []),
            # DAY1 only, and it reverses this project's standing decision on
            # avoidance framing FOR THIS ITEM. Here rather than in SLOT_NOTES so
            # both generators render the same words — the enforcement check calls
            # a rule parked web-only SLOT RULE WEB ONLY, and the CLI gates on this
            # too (score.derive_oc_ledger, keyed on the item id).
            #
            # The decision was to flag and never deduct, because a contingency
            # stated by what is avoided is structurally sound. The cohort says
            # gold disagrees on this item: of the five DAY1 cells where the check
            # ever answers `absent`, gold scores FOUR of them 0, and the fifth we
            # already miss for unrelated reasons. Measured — the item's median
            # rose by one, one cell went from wrong in every run to right in six
            # of six probe passes, a second recovered to 6/6, and both controls
            # held.
            *(["AVOIDANCE FRAMING TAKES THE WHOLE ITEM HERE. An answer whose only "
               "claim is about dodging a penalty has not said what will be added "
               "or taken away when the behaviour happens, and the graders scored "
               "those zero. \"I will push myself to {{corpus:DAY1/p8:day1:76:104:sha=140d96680ba2}} "
               "to do the extra chore\" asserts an intention and mentions a "
               "penalty in passing; \"if I miss my goal I will do the extra "
               "chore\" states the contingency. Judge the sentence's own claim: "
               "answer that the phrasing is direct whenever the consequence is "
               "stated as something added or removed after the behaviour, however "
               "plainly worded, and only call it avoidance-framed when the "
               "avoidance IS the claim. This is the only check that judges the "
               "phrasing; no other may deduct for it."]
              if item_id == "DAY1" else []),
            # WK2 only. The gap this closes: the TYPE items ask whether the
            # arrangement is pointed the right way (`targets_intended_behavior`,
            # charging WRONG_TYPE), and the cadence items only ask whose
            # behaviour it is (`targets_own_behavior`). So an answer that delivers
            # an aversive for SUCCESS passes every check on the sheet — the
            # behaviour is the student's own, the consequence is arranged,
            # contingent and subsequent, the cadence is right — and we credited
            # one 2 to 4 where gold scored 0.
            #
            # A gate because gold's charge is the whole 4 and the scored slots
            # here top out at 2 + 1 + 1. That makes every cell on this item a
            # 4-point bet on a single cell's evidence, which is thinner than the
            # four-of-five pattern that justified DAY1's gate — measured with the
            # item's correct cells as controls, and reverted if any of them move.
            *(["IS THE CONSEQUENCE POINTED THE RIGHT WAY? A plan earns nothing "
               "if its consequence works against the behaviour it follows. "
               "Reinforcement must make the WANTED behaviour more likely, so the "
               "thing that arrives when the student succeeds has to be desirable "
               "(or an aversive lifted); punishment must make the UNWANTED "
               "behaviour less likely, so the thing that arrives when they slip "
               "has to be aversive (or a privilege withdrawn). Answer `no` when "
               "the pairing is inverted — a chore, a loss or a penalty delivered "
               "for MEETING the goal, or a treat delivered for missing it — even "
               "when the sentence is otherwise a well-formed contingency about "
               "the student's own behaviour, and even when the wording is only a "
               "slip. Judge which side of the contingency the consequence sits "
               "on, not whether it is describable as a consequence."]
              if item_id == "WK2" else []),
            "WRONG_BEHAVIOR (-1) is for an example aimed at a CLEARLY DIFFERENT behaviour "
            "from the student's UTB/WGB — a plan about procrastination when the UTB is {{corpus:Q1/p15:response:49:53:sha=336074805fc8:shape=R4-0-20}}"
            "{{corpus:Q1/p15:response:54:76:sha=019d6dc324ea}} Do not deduct it merely because the phrasing is loose "
            "or the link is indirect: against a screen-time goal, gating the screen "
            "activity itself on finishing coursework earned full credit, even though "
            "the coursework is what the sentence foregrounds. It stacks with "
            "TYPE_MISMATCH when both are true.",
            "IMPLICIT (from gold): advisory notes without deduction are common on these "
            "items — \"I suggest changing your punisher to something not related to "
            "exercise\" was written on a 4.0. Put that kind of remark in advisory_note.",
        ],
        # The definition is in context because the type slot is sometimes left
        # blank (participant 15 scored 0 on T2) while the definition still says
        # plainly which type was intended.
        "context": ["_utb", "_wgb", type_ctx, def_ctx],
    }


ITEMS: list[dict] = [
    _example_item("PR", "PR Example", "Positive Reinforcement", "PR",
                  "{{corpus:D1/p9:d1:0:38:sha=73aaf2022862}} a behavior"),
    _example_item("NR", "NR Example", "Negative Reinforcement", "NR",
                  "taking away something undesirable to increase a behavior"),
    _example_item("PP", "PP Example", "Positive Punishment", "PP",
                  "adding something undesirable to decrease a behavior"),
    _example_item("NP", "NP Example", "Negative Punishment", "NP",
                  "taking away something desirable to decrease a behavior"),
    _type_item("T1", "First Type", "first"),
    _definition_item("D1", "First Type Definition", "first", "T1"),
    _example_use_item("DAY1", "First Daily Example", "first", "daily", "T1", "D1"),
    _example_use_item("WK1", "First Weekly Example", "first", "weekly", "T1", "D1"),
    _type_item("T2", "Second Type", "second"),
    _definition_item("D2", "Second Type Definition", "second", "T2"),
    _example_use_item("DAY2", "Second Daily Example", "second", "daily", "T2", "D2"),
    _example_use_item("WK2", "Second Weekly Example", "second", "weekly", "T2", "D2"),
]

BY_ID = {it["id"]: it for it in ITEMS}
TOTAL = sum(it["max"] for it in ITEMS)  # 40.0 scored; +10 upload = 50
