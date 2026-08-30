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

# Items carrying the four-clause contingency gate (states_a_contingency).
# One tuple, imported by score.py and consulted by olx_prompts.py, so the
# rule can be switched on, off, or scoped for a measurement WITHOUT the
# three definitions drifting apart — which is how an earlier edit patched
# DAY1 while believing it had patched DAY2.
CONTINGENCY_GATE_ITEMS = ('DAY1', 'DAY2', 'WK2')

# Items carrying the DERIVED direction gate: `direction_ok` is satisfied when
# `consequence_valence` equals `trigger_expects`, both answered separately by
# the model. It replaces the composite clause that asked one judgement to weigh
# both at once — measured inert, because all 13 of the contingency gate's
# `absent` verdicts across DAY1/DAY2/WK2 were attributable to its clause (a).
#
# A SEPARATE tuple from CONTINGENCY_GATE_ITEMS on purpose. The two gates were
# measured independently and must stay independently togglable; assuming one
# selector governed several sources is what patched DAY1 while believing it had
# patched DAY2.
# Items carrying the polarity pair, and with it the barrier gate: that gate's
# second operand IS `trigger_expects`, so it cannot exist where the pair does
# not. One selector for both, because the dependency is structural rather than
# coincidental — authoring the gate on an item without the pair produced a rule
# that could never fire, which is how this was found.
POLARITY_GATE_ITEMS = ('DAY1', 'DAY2', 'WK2')

# Items that answer the three barrier readings. NR joins the cadence three
# because the same structure appears there -- a self-imposed screen lock the
# behaviour lifts -- and the same decomposition catches it. What differs is the
# CHARGE: on the cadence items a created barrier is not operant conditioning at
# all and zeroes the item; on NR it is simply not NEGATIVE REINFORCEMENT, which
# gold charges at 2. Same readings, different consequence, so a separate tuple.
CADENCE_BARRIER_ITEMS = ('DAY1', 'DAY2', 'WK2')
# The four type screens. `restricts` -- is the held-back thing the student's own
# unwanted behaviour -- cannot work here: p14 holds back a phone on NR, going
# out on NP and a snack on PP, all desirable, all unrelated to their exercise
# UTB, and gold reads 2, 4 and 2. The discriminator is the VALENCE of the
# held-back thing against what the target type removes: NR removes something
# undesirable, NP removes something desirable.
# The valence that CONTRADICTS each type when something is held back. Only NP's
# operation IS removing a desirable thing, so only NP is contradicted by an
# undesirable one.
# The pair each type IS. Four types, two bits: added/taken x desirable/not.
REQUIRED_MOVE = {'PR': 'given_desirable', 'NR': 'taken_undesirable',
                 'PP': 'given_undesirable', 'NP': 'taken_desirable'}
# NR joins the cadence three: the same structure appears there -- a self-imposed
# barrier the behaviour lifts -- and the same three readings catch it. What
# differs is the CHARGE. On the cadence items a created barrier is not operant
# conditioning at all and zeroes the item; on NR it is simply not NEGATIVE
# REINFORCEMENT, which gold charges at 2. Removing this in the `stimulus_move`
# work cost NR/p14, which went 6/6 -> 0/6 with every other check passing.
BARRIER_PICK_ITEMS = CADENCE_BARRIER_ITEMS + ('NR',)

# Items answering the `stimulus_move` pair. NR is NOT among them: measured over
# four sweeps it scored 15.0-15.5 there against 16.0 for the observed_type build
# that preceded it, and its gains (p11, p20) never covered p15. PR keeps it on a
# measured +1.0; PP and NP are level.
# PR only. Measured at six runs twice over: PR 18.0 against a recorded 17 in
# both move_v3 and move_v4, while PP and NP each came in half a cell BELOW their
# recorded 18 and NR lost a full cell. The pair-and-derive reading earns its
# place on one item, not on the four that share the question.
MOVE_PICK_ITEMS = ('PR',)



# The four operant-conditioning types, as the course defines them.
_OC_FRAME = (
    "Operant conditioning has exactly four types, defined by two questions: is "
    "the target behaviour being INCREASED (reinforcement) or DECREASED "
    "(punishment), and is a stimulus being ADDED (positive) or TAKEN AWAY "
    "(negative)?\n"
    "  - Positive Reinforcement: add something desirable to increase a behaviour.\n"
    "  - Negative Reinforcement: take away something undesirable to increase a behaviour.\n"
    "  - Positive Punishment: add something undesirable to decrease a behaviour.\n"
    "  - Negative Punishment: take away something desirable to decrease a behaviour."
)

# Criteria the graders applied on every example item but the dictionary never
# states. These are the difference between 0 and 4 on the four example items —
# five of the twenty students scored 0 on PR and NP for precisely these.
_EXPECTS_RULE = (
"WHICH WAY WOULD A WORKING PLAN RUN FROM YOUR CONDITION? Read the "
               "CONDITION only — the clause saying when the consequence "
               "arrives — and answer `trigger_expects` from it alone.\n"
               "  Answer `gain` when the condition describes the student DOING "
               "WELL: meeting the goal, hitting the target, performing the "
               "wanted behaviour.\n"
               "  Answer `loss` when it describes them DOING BADLY: missing the "
               "goal, falling short, performing the unwanted behaviour.\n"
               "  Answer `none` when the sentence puts no condition on their "
               "behaviour at all.\n"
               "This is a reading of the condition, not a judgement of the plan."
)

_AUTHORED_RULE = (
"WAS THE UNDESIRABLE THING CREATED BY THE PLAN, OR ALREADY "
               "THERE? A question about how the sentence is built, not about "
               "whether the plan is a wise one.\n"
               "  Answer `created` when the answer describes the student "
               "BRINGING A DEPRIVATION INTO BEING as part of the plan — "
               "putting something beyond use, going without it, or "
               "setting it aside — which performing the "
               "behaviour then lifts.\n"
               "  Answer `relieved` when it describes the student being LET "
               "OFF something that would have been required of them anyway: a "
               "chore, an obligation, a task they would otherwise have had to "
               "do whether or not this plan existed.\n"
               "  The two are usually built differently. Creating a "
               "deprivation is stated in the POSITIVE — setting something "
               "aside, keeping it beyond use, having only the one thing. "
               "Being let off is usually stated as a NEGATED REQUIREMENT — not "
               "having to do it, one less than usual, skipping it this time.\n"
               "  Answer `neither` when no undesirable thing figures on either "
               "side. Report what the sentence shows; this answer does not by "
               "itself decide anything."
)

_RESTRICTS_RULE = (
"WHAT IS BEING HELD BACK? Answer only about the thing the plan "
               "restricts, withholds, or puts out of reach — if it restricts "
               "nothing, this does not apply and either answer will do.\n"
               "  Answer `target_behavior` when the thing held back IS the "
               "student's own unwanted behaviour, or the activity that "
               "behaviour consists of. Holding back the very thing they are "
               "trying to do less of is a real plan.\n"
               "  Answer `other_thing` when what is held back is something "
               "else — an unrelated comfort, possession or activity that has "
               "nothing to do with the behaviour being changed.\n"
               "This is about WHICH thing, not about whether the plan works."
)

_HELD_BACK_RULE = (
    "WHAT IS HELD BACK, AND IS IT WANTED? If the plan withholds, blocks or puts "
    "something out of reach, answer `held_back_is` about THAT thing: is it "
    "DESIRABLE to the student -- something they want or enjoy -- or UNDESIRABLE, "
    "something they would rather avoid? Answer about the thing held back, not "
    "about the behaviour and not about whether the plan is a good one. If the "
    "plan withholds nothing, either answer will do.\n"
    "Read it off the thing itself. A phone, a snack, an evening out, music are "
    "wanted; a chore, an early start, an obligation are not. The grader compares "
    "your answer with what this type of conditioning requires, so do not adjust "
    "it to fit the type -- answer what the thing is."
)

_MOVE_RULE = (
    "WHICH WAY, AND IS IT WANTED? `stimulus_move` is one answer combining two "
    "readings of the SAME thing -- the thing your example adds or takes away.\n"
    "  FIRST, the direction. Is that thing GIVEN to the student, or TAKEN AWAY "
    "from them? Read it about the thing itself, not about the plan's machinery: "
    "a restriction placed on something TAKES AWAY that thing, however the "
    "sentence words it, and a privilege allowed on a condition GIVES that "
    "privilege.\n"
    "  SECOND, the valence. Is that thing DESIRABLE to the student -- something "
    "they would choose for its own sake -- or UNDESIRABLE, something they would "
    "only do or accept because they had to?\n"
    "  Judge the thing, NOT whether having it is good for them. A pleasure that "
    "works against their goal is still desirable; that is precisely why taking "
    "it away can change behaviour. Do not call something undesirable because the "
    "student is trying to do less of it.\n"
    "  A thing the student must SPEND -- their time, their effort, their money, "
    "their comfort -- is UNDESIRABLE, even where the same activity would be a "
    "pleasure had they chosen it freely and at a moment of their own choosing. "
    "Being required to do it is what makes it a cost, so ask what it costs them "
    "at the moment it happens, not whether people enjoy such things. A thing "
    "they RECEIVE, or are PERMITTED, at no cost to themselves, is DESIRABLE.\n"
    "  It follows that an obligation LIFTED -- required effort or time struck "
    "off, a duty they no longer owe -- is an undesirable thing TAKEN AWAY, and "
    "not a desirable thing given, however much better off they end up.\n"
    "Then answer the one option combining the two: `given_desirable`, "
    "`given_undesirable`, `taken_desirable` or `taken_undesirable`.\n"
    "Answer what the sentence describes. The grader works out from your answer "
    "which of the four types this is, so do not reason backwards from the type "
    "the question asks about -- that is the arithmetic's job, not yours."
)

_EXAMPLE_RULES = [
    "TEST 1 — IS THERE AN EXPLICIT CONTINGENCY? This is the primary test and it "
    "is about FORM. A creditable answer links the behaviour to the consequence "
    "conditionally: \"If I [do / fail to do the behaviour], I will [gain / "
    "lose Y]\". An answer that names a reward without tying it to the behaviour "
    "fails even though a reward is present. Naming the behaviour to be increased "
    "and then a reward on a FIXED SCHEDULE — one given every so many weeks, "
    "rather than after the behaviour — scored 0, the grader asking the student "
    "to state the exact behaviour and what is added once it is exhibited. A "
    "bare prediction with no plan at all (\"skipping practice will "
    "set me back\") also scores 0.",
    "TEST 2 — DOES THE CONSEQUENCE ARRIVE AFTER THE BEHAVIOUR? \"Remember that "
    "what you take away or add has to happen after the behavior is exhibited.\" "
    "Judge the DELIVERY, not the wording. A privilege WITHHELD until a weekly "
    "goal is met passes: it is delivered once the goal is met, which is the "
    "ordinary shape of a reinforcement contingency, and the graders credited "
    "it. What fails is a plan where nothing is ever delivered contingent on the "
    "behaviour — leaving a temptation somewhere else, or putting it out of "
    "reach beforehand, are antecedent manipulations that remove the temptation in "
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
    "conditional plan is stated: the answer says the behaviour will leave "
    "them better off in the way the behaviour itself produces, and arranges "
    "nothing. If the answer is phrased as an if/then "
    "arrangement the student sets up, this code does not apply; judge it on "
    "tests 2 and 3 instead.",
    # WAS an enumerated list -- food, sleep, medical care, exercise-as-punishment
    # -- with a grader's note quoted verbatim. Two faults. The list is NARROWER
    # than what it reconstructs: the graders flagged whatever could harm the
    # student and left the score at full, so a plan harmful in some other way was
    # not covered at all. And the verbatim quotation hard-coded one incident into
    # a general rule, and was where most of this block's shared vocabulary came
    # from. Stated as the principle instead.
    "SAFETY: flag, but do not deduct for, any example whose arrangement could "
    "harm the student or put their wellbeing at stake — going without something "
    "the body needs, forgoing care, or using the goal behaviour itself as a "
    "punishment are the common shapes, but the judgement is whether the plan "
    "could do harm, not whether it matches that list. Say so in the feedback and "
    "leave the score at full: the graders did exactly this, flagging the "
    "arrangement while awarding every point.",
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
        # The three barrier readings need their DEFINITIONS here, not only in the
        # cadence builder: NR answers the same picks, and a pick asked for with no
        # vocabulary explained is answered from its label alone. Restoring
        # BARRIER_PICK_ITEMS without this put the slots on NR's sheet and left the
        # conjunction unable to fire -- measured, at 16 probe calls, p14 scoring 4
        # in both runs with the slots present and their meanings absent.
        "guidance": [_OC_FRAME] + _EXAMPLE_RULES
        + ([_MOVE_RULE] if item_id in MOVE_PICK_ITEMS else [])
        + ([_EXPECTS_RULE, _AUTHORED_RULE, _RESTRICTS_RULE]
           if item_id in BARRIER_PICK_ITEMS else []) + [
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
                # MIGRATED out of olx_prompts.SLOT_NOTES on 2026-08-29 (E11), for
                # D1 and D2 at once -- both come from this factory.
                # The `desc` above already carried the first clause, so score.py
                # was told WHAT to judge and not the operative half: do not look
                # at what they chose. That matters more here than most, because
                # `defines_type` and `named_type` feed the `matches_chosen_type`
                # comparison -- a grader who reads the choice while judging the
                # definition collapses two checks that have to stay independent.
                # VERBATIM from the note, so the web prompt does not move: its
                # checklist looks up `rule` before SLOT_NOTES and finds the same
                # string.
                "rule": "which of the four types this DEFINITION describes, judged on "
                        "its content alone: something added or removed, behaviour "
                        "increased or decreased. Do not look at what they chose "
                        "\u2014 that is the other check, and the grader does the "
                        "comparison",
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
                # statable property: "screen locked until I am in a gym" (gold 0)
                # and "I will only start watching shows when I am caught up"
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
               "toward it or does not. An answer keyed to \"if I meet my goal\" is "
               "daily even when the goal itself is a weekly total. Answer that "
               "the cadence is wrong only when the student must WAIT FOR THE WEEK "
               "TO END before the contingency can fire at all — a whole-week "
               "tally scored on Sunday, one weekend reward for the week's "
               "performance."] if item_id == "DAY2" else []),
            # DAY2 only, for now. Derived by reading all 64 counted answers on
            # the four cadence items, not from one cell: of the gold-zero cells
            # that are not valence inversions, EVERY ONE states no contingency,
            # and EVERY credited cell states one. The "desirable / escape from
            # something undesirable" half is what keeps negative-reinforcement
            # answers safe — several credited cells reward the student by sparing
            # them a chore rather than by giving them a thing, and a bare "grants
            # or withholds something" could be read to exclude those.
            *(["IS A WORKABLE CONTINGENCY STATED? Look for three things.\n"
               "  (a) A CONDITION ON THE STUDENT'S BEHAVIOUR — \"if I...\", "
               "\"when I...\", \"every day that I...\", \"once I reach...\", "
               "or a statement of what they did followed by \"so\". The "
               "condition may be their doing well or their doing badly.\n"
               "  (b) A MAIN CLAUSE IN WHICH SOMEONE GRANTS OR WITHHOLDS "
               "SOMETHING DESIRABLE, OR OFFERS ESCAPE FROM SOMETHING "
               "UNDESIRABLE. Giving a treat, buying a thing, allowing an "
               "activity, taking away a privilege, imposing a chore, or sparing "
               "one all qualify — being let off an obligation counts exactly as "
               "much as receiving a thing.\n"
               "  (c) THE CONSEQUENCE MUST COME AFTERWARDS, AS A SEPARATE "
               "EVENT. Operant conditioning needs TWO MOMENTS: first the "
               "student behaves, then, afterwards, the consequence is "
               "delivered. Escape from something undesirable still counts — "
               "being let off a chore, an obligation lifted — provided the "
               "relief arrives once the behaviour is complete and is a step "
               "distinct from it. What does not count is a restriction "
               "standing IN FRONT OF the behaviour that is simply lifted at "
               "the moment of doing it: a restriction that ends exactly when "
               "the behaviour begins, so that beginning it IS the lifting. "
               "There the lifting IS the "
               "behaviour's own occurrence, not something that follows it. "
               "Ask: once the student has behaved, is anything still left to "
               "happen? If nothing is, (c) fails.\n"
               "Answer `met` when all three hold. Answer `absent` when any is "
               "missing, however sensible the plan is. A missing (a) or (b) "
               "usually looks like one of these: a sentence that only says what "
               "the student will DO (\"I will get up at six and go for a "
               "run\"); a PURPOSE clause giving the reason for the behaviour "
               "rather than a consequence of it (\"I go for a run to feel "
               "healthier\"); one activity offered INSTEAD OF another (\"I "
               "will do the other one instead\"); or a bare statement of intent "
               "or hope (\"this should help me reach my goal\"). A missing (c) "
               "looks well formed: \"the kitchen "
               "stays off limits until I have finished studying, and I go in "
               "as soon as I do\" describes one moment, not two — going in IS "
               "having finished, not a consequence delivered for it."]
              if item_id in CONTINGENCY_GATE_ITEMS else []),
            # `direction_ok` was measured redundant: it fired on three cells and
            # the barrier gate caught all three, plus DAY2/p14 that it could not.
            # Removed with `consequence_valence`, its only operand. What is left
            # is the one reading the barrier gate still needs.
            *([_EXPECTS_RULE] if item_id in BARRIER_PICK_ITEMS else []),
            # DIAGNOSTIC ONLY — this slot gates nothing and scores nothing.
            # The barrier cases (a self-imposed deprivation lifted by the
            # behaviour) are gold 0, and the legitimate escapes (an obligation
            # that exists anyway, cancelled by success) are gold 4, but there
            # are only three of the former and they come from two students. A
            # gate built on that would be fitted to the corpus rather than to
            # the criterion — which is the same error as quoting a response,
            # and it would pass every leakage check. So the question is asked
            # and REPORTED first: measure how it answers on all 72 cells, and
            # gate later only if it separates the contrast set cleanly.
            #
            # "until" was tested as a cheap marker and rejected: it appears in
            # all three barrier answers and in DAY2/p8, a gold 4, as "till".
            *([_AUTHORED_RULE] if item_id in BARRIER_PICK_ITEMS else []),
            # The exception gold draws, and the reason the barrier rule needs a
            # third condition rather than more prose. DAY1/p6 (gold 0) holds
            # back MUSIC to drive gym attendance; DAY1/p15 (gold 4) holds back
            # the screen time that IS its own unwanted behaviour. Structurally
            # identical — a restriction the student's compliance lifts — and
            # gold splits them on WHAT is restricted. Gating the unwanted
            # behaviour itself is a real plan; gating something unrelated to it
            # is a setup that never consequates anything.
            *([_RESTRICTS_RULE] if item_id in CADENCE_BARRIER_ITEMS else []),
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
               "those zero. \"I will make myself practise so that I never have to "
               "face the fine\" asserts an intention and mentions a penalty in "
               "passing; \"if I skip a practice session I pay the fine\" states "
               "the contingency. Judge the sentence's own claim: "
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
            # WK1 only, and asked as a PARSE. Two earlier versions of this gate
            # asked the semantic question — "is a consequence delivered?" — and
            # the model answered inconsistently on the only two cells that
            # separate: it called a self-accumulating penalty delivered two times
            # in three, and a straightforward "I will be able to get X" undelivered
            # one time in three. Making the slot binary removed the hedge and did
            # not fix the wobble.
            #
            # The cue that actually separates the cells is syntactic, and a parse
            # is something the model does crisply. Every gold-4 cell puts an
            # ANIMATE AGENT in subject position governing a verb of transfer — "I
            # will treat myself to a movie", "I will buy one piece of a workout
            # set", "I will allow myself to skip one chore". The gold-0 cell this
            # gate is for puts the CONSEQUENCE ITSELF in subject position with an
            # aspectual verb: the penalty "will just keep stacking". No agent, no
            # transfer verb. The other gold-0 cells are already caught elsewhere —
            # one has no finite clause at all, and the other fails `contingent`.
            *(["WHO IS NAMED AS DOING IT? This is a question about the sentence, "
               "not about the plan. Find the clause that states the consequence, "
               "then look at two things.\n"
               "  (a) Its SUBJECT. Answer `met` only if a person appears in an "
               "agentive position — the subject of an active verb (\"I will...\", "
               "\"my flatmate will...\"), or the agent of a passive marked with "
               "`by` (\"my phone is taken away BY my flatmate\"). A person "
               "mentioned elsewhere in the sentence does not count; the agent must "
               "govern the consequence.\n"
               "  (b) Its VERB. Read this BROADLY: it must say that the agent "
               "brings the thing about or takes it away. Transfer verbs qualify — "
               "give, buy, treat, reward, allow, let, withhold, remove, take "
               "away, hand over, lose, pay — and so does an agent GRANTING "
               "THEMSELVES a privilege or an activity, however it is worded: "
               "staying up later, sleeping in, having a lie-in, skipping a chore, "
               "taking the evening off, going out. \"I will take myself to the "
               "cinema on Sunday\" is the student granting themselves something, and "
               "counts. So does a privilege denied — \"I will not go out this "
               "weekend\". The test is whether a PERSON makes the thing happen or "
               "stop happening, not whether the verb is on a list.\n"
               "Answer `absent` in these cases.\n"
               "  * The subject of the consequence clause is the CONSEQUENCE "
               "ITSELF — a penalty, a tally, a debt, an amount — with a verb of "
               "existing, growing or accumulating: piling up, mounting, adding "
               "up, building, getting bigger. \"The extra laps will keep piling "
               "up\" names no one who imposes them, and a rule about how a debt "
               "grows is not a person delivering a consequence.\n"
               "  * The consequence appears in no finite clause at all — a bare "
               "gerund or noun phrase with nobody acting.\n"
               "  * The answer does not describe a consequence for this "
               "student's behaviour at all: it is off the point, discusses "
               "something else entirely, restates the question, comments on the "
               "task or the handout, is too vague to identify any thing or any "
               "actor, or is empty. If you cannot point to a clause and say who "
               "acts and what they do to what, the answer is `absent` — do not "
               "search the sentence for the most consequence-like fragment in it "
               "and credit that."]
              if item_id == "WK1" else []),
            "WRONG_BEHAVIOR (-1) is for an example aimed at a CLEARLY DIFFERENT behaviour "
            "from the student's UTB/WGB: the plan would change some other habit "
            "entirely, and carrying it out would leave the stated goal untouched. "
            "Do not deduct it merely because the phrasing is loose or the link is "
            "indirect. In particular, a plan that gates the unwanted activity itself "
            "on completing some other task IS controlling the target behaviour, even "
            "though the other task is what the sentence foregrounds. It stacks with "
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
                  "adding something desirable to increase a behavior"),
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

# THE GATES EACH ITEM APPLIES, in the order it applies them.
#
# Declared here rather than written into score.py as `if item["id"] == ...`
# branches. The same checks are marked `!` on the sheet for the web, so the rule
# existed on one side as a declaration and on the other as code -- and the
# enforcement audit compares DECLARATIONS, so nothing compared these at all.
#
# Order is part of the declaration: the first gate that fails is the one whose
# message the student sees, and each short-circuits the rest of the ledger. The
# order below reproduces the branch order it replaces exactly -- WK2 asked
# `aimed_correctly` before `states_a_contingency`.
OC_GATES: dict[str, list[dict]] = {
    "WK1": [{"key": "agent_delivers_consequence", "code": "NOT_OC",
             "text": "No one is named as adding or removing anything: the "
                     "consequence clause has no agent."}],
    "WK2": [{"key": "aimed_correctly", "code": "NOT_OC",
             "text": "The consequence is pointed the wrong way: an aversive for "
                     "meeting the goal, or a reward for missing it."},
            {"key": "states_a_contingency", "code": "NOT_OC",
             "text": "No contingency is stated: nothing is granted or withheld "
                     "on a condition."}],
    "DAY1": [{"key": "states_a_contingency", "code": "NOT_OC",
              "text": "No contingency is stated: nothing is granted or withheld "
                      "on a condition."}],
    "DAY2": [{"key": "states_a_contingency", "code": "NOT_OC",
              "text": "No contingency is stated: nothing is granted or withheld "
                      "on a condition."}],
}
for _it in ITEMS:
    if _it["id"] in OC_GATES:
        _it["oc_gates"] = OC_GATES[_it["id"]]

# Items where an avoidance-framed contingency COSTS the item rather than merely
# being noted. Declared, because both scorers must say the same thing about it
# and they were not: the shared criteria prose says criterion 7 "never changes
# the score", which is true everywhere except here, where this item's own
# guidance says avoidance framing takes the whole item and the graders scored
# those zero. The web prompt carried both sentences and contradicted itself; the
# CLI suppressed the first. This declaration is what the CLI was doing, read by
# both sides, so neither has to know an item id.
AVOIDANCE_SCORES = ("DAY1",)
for _it in ITEMS:
    if _it["id"] in AVOIDANCE_SCORES:
        _it["avoidance_scores"] = True

# The `forbid` conjunctions, declared once. Same three readings on all four
# items, different charges: on DAY1/DAY2/WK2 a restriction the plan CREATES,
# which the student's SUCCESS lifts, and which restricts something UNRELATED, is
# not operant conditioning and gates the item; on NR the identical reading is
# simply not NEGATIVE REINFORCEMENT, which needs an undesirable thing taken away,
# and gold charges 2 rather than the whole item.
#
# It was written three times: as this conjunction in score.py's polarity branch,
# again in its barrier branch, and a third time as a hand-authored `forbid="..."`
# attribute in bmod_handout2.olx. The rubric is the channel both scorers read, so
# it is declared here and the OLX attribute is GENERATED from it -- see
# olx_prompts.forbid_attr_for.
#
# `restricts: other_thing` is gold's own exception: gating the unwanted behaviour
# itself earns credit, so only a restriction on something unrelated is a setup.
_BARRIER_CONDS = [{"slot": "restriction_authored", "value": "created"},
                  {"slot": "trigger_expects", "value": "gain"},
                  {"slot": "restricts", "value": "other_thing"}]

FORBID: dict[str, list[dict]] = {
    **{i: [{"key": "consequence_not_a_setup", "conds": _BARRIER_CONDS}]
       for i in POLARITY_GATE_ITEMS},
    "NR": [{"key": "barrier_is_not_this_type", "conds": _BARRIER_CONDS}],
}
for _it in ITEMS:
    if _it["id"] in FORBID:
        _it["forbid"] = FORBID[_it["id"]]

# WK1's `expect`, declared once. The model names WHICH behaviour the trigger
# identifies -- `utb`, `wgb` or `other` -- and the engine decides whether that
# counts as the student's own; asked as a parse rather than as a judgement,
# because two earlier versions asked "is it aimed at your own behaviour?" and the
# model answered inconsistently on the two cells that matter.
#
# `utb` with `wgb` lenient: either the behaviour they are cutting or the one they
# are building is their own. Only `other` is not.
#
# The other four `expect` rules on this handout (`demonstrates_type` on
# NP/NR/PP/PR) are deliberately NOT declared here: the CLI reaches that fact
# through `expected_type` and REQUIRED_MOVE, which are already rubric
# declarations, and a second declaration of one fact is what this work removes.
EXPECT: dict[str, list[dict]] = {
    "WK1": [{"key": "targets_own_behavior", "left": "trigger_behavior",
             "value": "utb", "lenient": ["wgb"]}],
}
for _it in ITEMS:
    if _it["id"] in EXPECT:
        _it["expect"] = EXPECT[_it["id"]]

# The answer VOCABULARY for slots the engine reads rather than scores: which
# options the model may pick from. Keyed by SLOT, not by item, because the
# vocabulary is a property of the question and not of who asks it -- and because
# an item-keyed table is the thing this conversion is removing.
#
# score.build_schema used to carry these lists inline behind `item["id"] in ...`
# branches, which the enforcement audit cannot compare between the two scorers
# because it compares declarations. WHICH items ask each slot is now derived from
# the declaration that consumes the answer: `forbid` names the three barrier
# readings in its conditions, `oc_gates` names its own gate keys, `expect` names
# the slot it parses, and `move_pick` is declared below.
SLOT_OPTIONS: dict[str, list[str]] = {
    "restriction_authored": ["created", "relieved", "neither"],
    "trigger_expects": ["gain", "loss", "none"],
    "restricts": ["target_behavior", "other_thing"],
    "trigger_behavior": ["utb", "wgb", "other"],
    "stimulus_move": ["given_desirable", "given_undesirable",
                      "taken_desirable", "taken_undesirable"],
}

# Items that answer the two-bit move pick instead of naming the type directly.
# DELIBERATELY NARROWER than REQUIRED_MOVE, which has an entry for all four types:
# only PR asks it, so deriving membership from REQUIRED_MOVE would put a new
# required field on NR, PP and NP -- a change to what the model is ASKED, not a
# refactor. Declared as an attribute so the code needs no item id.
for _it in ITEMS:
    if _it["id"] in MOVE_PICK_ITEMS:
        _it["move_pick"] = True

BY_ID = {it["id"]: it for it in ITEMS}
TOTAL = sum(it["max"] for it in ITEMS)  # 40.0 scored; +10 upload = 50
