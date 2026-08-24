"""Per-handout wiring: where the files are, how to split them, what scores them."""

from __future__ import annotations

import glob
import os
import re

import gold as gold_mod
import rubric_h1
import rubric_h2
import rubric_h3
from segment import H1_MARKERS, H2_MARKERS, H3_MARKERS

import paths

# ROOT used to be one directory. It is now three: the blank templates ship
# with the code (MATERIALS), the filled-in submissions never enter git
# (SUBS), and run output is scratch (OUT). See paths.py.
MATERIALS = paths.MATERIALS
SUBS = paths.SUBS
OUT = paths.OUT

# ── Gold rows the grader got wrong, corrected ────────────────────────────────
#
# A FIFTH kind of gold caveat, and the narrowest. The four already here say what
# to do when gold is unreachable or inconsistent; none of them changes the number
# we are scored against. This one does, and only where the gold row contradicts
# a FACT ESTABLISHED IN THE STUDENT'S OWN SUBMISSION — not where we merely judge
# differently.
#
#   GOLD_DIVERGENCES   we disagree on purpose; the cell is still scored as gold
#                      has it, and the miss stands
#   PER_ITEM_EXCLUDE   the cell is dropped, because nothing correct can score it
#   GOLD_CEILINGS      a criterion gold decides inconsistently, so some cells are
#                      unwinnable whichever rule you pick
#   UNSCORED_GOLD_CRITERIA
#                      criteria neither system scores at all
#   CORRECTED_GOLD     the gold NUMBER is wrong on the submission's own evidence,
#                      and the corrected number is what we score against
#
# A CORRECTION HERE INVALIDATES EVERY EARLIER MEASUREMENT OF THAT CELL, and the
# stored figure does not know it. out/q6_boxbounds_full published "17/20 (85%)"
# for Q6 and was cited as the baseline all through 2026-08-19; it ran before the
# p4 entry below, when p4's gold was the unreachable 6.00 and our 6.25 counted
# exact by nearest_attainable. Against p4 = 7.50 that same run is 16/20. Nothing
# recomputes a stored .json when a row is corrected, so the published number and
# a fresh recomputation of the same data differed by a cell, which I spent part
# of that day attributing to a bug in the reporter. Re-derive a baseline from its
# .runs.json after touching this table, or compare only figures computed on the
# same gold.
#
# The bar is deliberately high, and `was` is asserted against the sheet on every
# run so a correction cannot outlive the row it corrects.
#
# WHAT DOES NOT QUALIFY, with the worked example that nearly got in. On 2026-08-19
# these rows looked like they contradicted themselves: p5, p4 and p17 each charge a
# consequence for not matching 4c and then CREDIT the effect slot for that same
# consequence, which reads as crediting a description of what becomes of something
# gold has just said was never named. Correcting it was proposed and would have
# moved three rows and four slots, 5.00 points.
#
# It is not a contradiction. Surveyed across all twenty rows, gold charges an
# effect slot when NO EFFECT IS DESCRIBED -- p1 "did not say how the first
# consequence is being affected", p15 and p16 "did not clarify ... being affected",
# p8 "did not state each consequence being affected and how" -- and never merely
# because the naming missed. p5's row reads: the wrong consequence was named, which
# is 1.25 off, and a change WAS described, so that is not charged twice. One
# mistake, charged once. Gold is applying no-double-jeopardy, consistently, on
# every row.
#
# So the principle behind the proposed correction -- that effect credit should be
# contingent on naming credit -- is a RUBRIC-DESIGN OPINION, and gold holds a
# defensible opposing one. That is exactly the line this table draws: p18's entry
# rests on a second antecedent that does not exist in the document, p9's on an
# antecedent that appears in no 4a item, p4's on a consequence equivalence the
# student's own 4c supplies. Those are facts about a submission. "We would charge
# this differently" is not, however consistently we would do it, and it belongs in
# GOLD_DIVERGENCES if anywhere.
#
# Worth knowing which way the money went, since it is not the flattering direction:
# applying it would have made p4 exact and turned p5 and p17 into misses, costing
# us a cell. The reason to refuse it is the standard, not the score.
CORRECTED_GOLD: dict[tuple[str, int], dict] = {
    # ("Q6", 4) RETIRED 2026-08-19. It raised p4 from 6.00 to 7.50 on the reading
    # that gold had missed one of two consequences the student named. The second
    # naming was not the student's: `state_c2` held "I hope that I will no longer
    # be up late" and `affect_c2` held the whole sentence it is a prefix OF, so one
    # clause was occupying two boxes and the correction was reasoning from our own
    # duplication. Assign the sentence to one pair and leave the other empty --
    # which is what the response supports, one consequence addressed and one not --
    # and the deserved total is five slots, 6.25. Gold wrote 6.00, which is off the
    # 1.25 grid, and `nearest_attainable` maps it to 6.25. Gold was right as
    # written; the entry was chasing a fixture artifact, and p4 measures 6.25 in
    # seven of nine passes on the repaired fixture.
    #
    # The general lesson, since it applies to this whole table: an entry that
    # reasons from BOX CONTENTS inherits every judgement in the split. Check the
    # spans before correcting the row.
    ("D2", 11): {
        "was": 1.0, "score": 0.0,
        "why": "p11 chose Negative Reinforcement and wrote the definition of "
               "Negative Punishment, and the grader said so: \"This is the "
               "definition of NP.\" They then charged 1 point, not 2. Three "
               "independent sources say 2 is the charge for writing another "
               "quadrant's definition. The deduction dictionary puts "
               "WRONG_DEFINITION at -2. The SAME grader charged the same defect "
               "-2 one item earlier, on D1/p7 — \"This is not the correct "
               "definition for NP\" — taking that row to 0.00. And the five other "
               "definition rows in this handout (D1/D2 for p9, p13, p16) are all "
               "the DIFFERENT, lesser defect, \"did not provide the entire "
               "definition\", each charged exactly -1. So -1 is the settled "
               "charge for an incomplete definition and -2 for a wrong one, with "
               "this row the lone place the two are confused.\n"
               "\n"
               "This was a GOLD_DIVERGENCE (WRONG_DEFINITION) until 2026-08-24, "
               "declared on the reasoning that both implementations score 0 and "
               "are therefore 1 point under gold — the only divergence in the "
               "corpus running downward, which should have been the tell. A "
               "divergence says we disagree with a coherent gold decision; an "
               "isolated arithmetic slip against the grader's own practice "
               "elsewhere is a wrong NUMBER, which is this table. D1/p7 is the "
               "control that makes it decidable: same defect, same model answer "
               "of 0, and gold agrees there.",
    },
    ("Q6", 9): {
        "was": 5.0, "score": 3.75,
        "why":
            "gold credits `state_a1`, which names a THIRD antecedent p9 never "
            "listed. Their 4a gives \"Thinking about exercising makes me want to go "
            "less to the gym\" and \"Not going on a run with a friend because I know "
            "I will get tired easily\"; Q6 says \"my antecedent of using my free time "
            "in bed watching a movie or show\". Watching a movie in bed appears in "
            "neither entry, so the box names an antecedent that is not on the list "
            "at all -- not a reworded one, which is the distinction this item's own "
            "rule turns on. The scoring dictionary is explicit that the antecedents "
            "must match up, and the lo-blocks prompt returned a mismatch in five "
            "runs of five. "
            "THE EVIDENCE CITED HERE WAS WRONG UNTIL 2026-08-19, and the way it was "
            "wrong is worth keeping. It quoted p9's 4a as \"wanting to do anything "
            "but go to the gym\" and \"being a little lazy and not having any "
            "motivation\" -- which are P8's antecedents, not p9's. Neither phrase "
            "occurs anywhere in p9's 4a. The conclusion survived the correction "
            "because p9's real entries are about thinking-about-exercising and "
            "skipping-a-run-with-a-friend, and a movie in bed is no more one of "
            "those than of p8's; but an entry whose stated basis is another "
            "student's text cannot be checked, and being checkable is where this "
            "table's authority comes from. Quote the row you are correcting. "
            "PREVIOUSLY EXCLUDED as unscoreable with expect_error -1.25, which "
            "dropped the cell from every rate. Correcting the row is better: the "
            "exclusion threw away a scoreable cell to avoid an error that was "
            "gold's, and p9 now counts. 5.00 -> 3.75. Gold's own charges, \"-2.5 "
            "pts: missing second antecedent\" and \"-2.5 pts: missing second "
            "consequences\", we agree with and reproduce.",
    },
    ("Q6", 17): {
        "was": 5.00,
        "score": 3.75,
        "why": "gold credits `state_c1`, which names a consequence p17 never "
               "listed. Their 4c gives \"gaining weight quickly\" and \"becoming "
               "lazy and am not productive\"; Q6 says \"my consequence of feeling "
               "unhealthy and stressed from not moving enough\". Weight gain LEADS "
               "TO feeling unhealthy rather than being a kind of it, \"stressed\" "
               "appears nowhere in 4c, and \"not moving enough\" is the behaviour "
               "rather than a consequence. "
               "This was declared C_MISMATCH and measured five times. Gold itself "
               "applies the matching rule elsewhere in its own words — refusing "
               "p1's first consequence \"(from 4c)\", charging p5's \"first "
               "antecedent does not match antecedents listed in 4a\" — and a "
               "substitution test built to honour those refusals (is one a KIND OF "
               "the other, or does one LEAD TO the other) refused p17 too. So no "
               "consistent rule can credit it, which makes the 1.25 an error in "
               "the row rather than a disagreement about judgement. "
               "5.00 -> 3.75. Gold's own charge, \"-5 pts: did not address your "
               "second antecedent being changed and how it will affect your second "
               "consequence\", we agree with and reproduce.",
    },
    ("Q6", 18): {
        "was": 7.50,
        "score": 6.25,
        "why": "gold credits a SECOND ANTECEDENT that p18 never listed. Their 4a "
               "writes two numbered items whose text is verbatim identical — the "
               "after-school fatigue trigger, twice — so `bmod_h1_q4a_second` is "
               "empty and there is no second antecedent to change. Q6's "
               "`state_a2` names \"phone distractions\", which appears in NEITHER "
               "4a item, and no arrangement of p18's own words can put a "
               "matchable antecedent in that box. "
               "Gold says so itself on the same row: Q4a scores 3.0, \"-2 pts: "
               "only provided one antecedent\". Then Q6 credits the second one. "
               "The two judgements cannot both be right, and the 4a one is the "
               "one supported by the document. "
               "So 1.25 comes off: 7.50 -> 6.25, which is what a scorer that "
               "honours the student's own 4a can reach. Everything else in the "
               "row stands — gold's other charge, \"-2.5 pts: did not address how "
               "the second consequence is being affected\", we agree with and "
               "reproduce.",
    },
}


def corrected_gold(item: str, pid: int) -> dict | None:
    """The correction for one cell, or None. See CORRECTED_GOLD."""
    return CORRECTED_GOLD.get((item, pid))


def apply_corrected_gold(rows: dict, handout: int) -> dict:
    """Overwrite the gold score wherever CORRECTED_GOLD names a cell.

    Applied inside the gold LOADER rather than at each call site, because eight
    places load gold — the app, the CLI, the paper baseline, interim, the audit,
    self_graded_misses — and a correction applied in some of them would make the
    columns stop being a comparison. Every consumer goes through
    config(h)["gold"](), so this is the one place that reaches all of them.
    """
    for (item, pid), fix in CORRECTED_GOLD.items():
        cell = (rows.get(pid) or {}).get(item)
        if not cell:
            continue                    # different handout, or no such row
        cell["score"] = fix["score"]
        cell["corrected_from"] = fix["was"]
    return rows


def _gold_loader(fn, handout: int):
    def load(*a, **kw):
        return apply_corrected_gold(fn(*a, **kw), handout)
    return load


HANDOUTS: dict[int, dict] = {
    1: {
        "rubric": rubric_h1,
        "template": f"{MATERIALS}/BMod Handout #1 - Defining Behaviors, ABCs, and SMART Goals.docx",
        "submissions": f"{SUBS}/Handout 1 Submissions with Scoring and Feedback",
        "markers": H1_MARKERS,
        "capture_tail": False,
        "outdir": f"{OUT}/h1",
        "gold": _gold_loader(gold_mod.load_h1, 1),
        "blurb": (
            "Handout 1 of the Behavior Modification Assignment: defining behaviours, "
            "the ABCs of a functional behavioural analysis, and SMART goals."
        ),
        # Participants whose responses appear as few-shot exemplars in the
        # rubric, so scoring them would be self-grading.
        # p6 is an UNSTABLE exemplar and is kept as a diagnostic. Its whole
        # answer and its 6.25 are printed in Q6's prompt, and the scorer
        # reproduces that score in only 6 of 12 runs — unanimous one way in one
        # pass and the other way in the next. It is not a step-1 removal: taking
        # the citation out would mean deleting a worked example the prompt is
        # built around. Watch it while tuning Q6's slot judgements; it should
        # stop flipping when they stabilise, which reads independently of the
        # counted rate. See EQUIVALENCE.md, "Cleaning up an item".
        "exemplar_participants": [10, 8, 6],
        # ...but only on the items whose PROMPT actually embeds them. Verified
        # against the rubric: Q6 is the sole item with an `exemplars` field, and
        # the three bodies reproduce p10, p8 and p6 verbatim. Their Q1..Q5
        # answers appear in no prompt, so dropping them there discarded 21 cells
        # for nothing. See exemplar_drops() below.
        # Empty since Q6 was rewritten from the dictionary: it no longer
        # reproduces anyone's answer, so no cell on it is self-graded. The
        # handout-wide `exemplar_participants` list above is now inert for
        # handout 1 and kept only so a future item can opt in by naming itself.
        "exemplar_items": [],
        # A SECOND way a prompt can give the answer away, found by auditing every
        # item's prompt-bearing text for a participant cited by number.
        #
        # `exemplar_items` covers a response reproduced in full as a worked
        # example. This covers a response CITED as calibration — "falling asleep
        # in the car ... cost participant 20 three points" — which quotes the
        # answer AND states the grader's decision. That is an answer key for that
        # cell just as surely, so scoring the cited participant on that item is
        # self-grading too.
        #
        # Per item, because the sets differ: Q6 embeds p10/p8/p6, Q4b cites eight
        # entirely different participants. The handout-wide `exemplar_participants`
        # list cannot express that, which is why registering Q4b needed this.
        #
        # All ten qualifying items, registered together after the evidence came
        # in. Q4b was registered first, alone; measuring it then showed the whole
        # 21-point web/paper gap on that item was Opus reproducing answers held
        # in its prompt (7/7 on cited cells) where gpt-5-mini did not (4/7),
        # while on the cells that should be judged the three scorers were
        # equivalent — 12, 11 and 10 of 12. Leaving the other nine unregistered
        # would have kept that distortion in every handout-1 and handout-3 number.
        #
        # Reproduce with the audit in EQUIVALENCE.md: search each item's
        # prompt-bearing text for a participant cited by number. Handout 2 has
        # none — its guidance quotes answers without attributing them.
        # EIGHT CELLS CAME OUT 2026-08-23, on the same principle Q4b's note below
        # records, after the exclusion audit that step 1 of the cleanup procedure
        # asks for and that this campaign had skipped. Every excluded cell in the
        # handout was retested against its item's current configuration — free,
        # because excluded cells are still run and still scored — and eight were
        # WRONG in 3 of 3 runs with the answer and the grader's decision sitting in
        # the prompt. An exclusion there buys a flattering denominator and nothing
        # else, so the citation and the registration moved together:
        #
        #   Q1 p9   Q2 p7   Q4a p9, p14, p15   Q4c p9, p20   Q5 p4
        #
        # Each citation was rewritten as the RULE it was illustrating rather than
        # deleted, so the guidance keeps its content and loses the answer key.
        # Three of the eight (Q4a's) already carry declared divergences, so their
        # misses were always intentional and now simply count. EXPECT THESE FIVE
        # ITEMS' RATES TO FALL; that is what the step is for.
        #
        # The 21 cells that stayed are right in 3 of 3, which is what a
        # `self_graded` exclusion is FOR: with the answer in the prompt, getting it
        # right proves nothing, so the cell is uninformative rather than stale.
        # Section 5's retest-until-removed rule bites on `unscoreable` claims, not
        # on these.
        "cited_participants": {
            # Q1 IS GONE FROM THIS MAP, and it is the worked example of the second
            # half of step 0: an exclusion can be correct and still be unnecessary.
            # All five of its registrations rested on bare attributions — "(participant
            # 1)", "which is what participant 6 scored", "which is how participants 10
            # and 16 were credited" — so deleting the attributions left every rule
            # intact and the claim became testable.
            #
            # MEASURED, 3 runs with the citations gone: the 15 cells already counted
            # held at 13, 13, 13, and four of the five cited cells stayed right 3 of 3.
            # The citations were load-bearing for nothing, and the whole item scores
            # 18, 17, 18 of 20 against the 13/15 it had been reporting. FIVE CELLS WE
            # SCORE CORRECTLY had been subtracted from every rate on an untested claim.
            #
            # p10 is the exception and was kept out deliberately anyway. Probed at 6
            # passes it is right 4 of 6 without its citation, against 3 of 3 with it —
            # so that citation WAS doing work, and what it was doing was holding a
            # coin-flip cell at 100%. Keeping the exclusion would mean keeping an answer
            # key in the prompt to make one cell look stable, which is the opposite of
            # what the registry is for. It counts, and it flips.
            # Q2 IS GONE TOO, and its citations were the harder kind: quote plus
            # verdict, not bare attribution. `wgb_inverts_utb` quoted p10's own goal
            # and the two points it lost; `reasons_given` quoted p6's restatement and
            # named p3 as having lost all three. Rewriting them as rules — a goal that
            # names something ACQUIRED rather than the behaviour fails; a restatement
            # of the goal is not a benefit of it — kept the teaching:
            #
            #   numerator, 17 counted cells   16, 14, 15  ->  15, 15, 17
            #   whole item, 20 cells          18, 17, 18  ->  17, 17, 20
            #
            # p3 held at 3/3 and p6 IMPROVED, 2/3 -> 3/3, without the answer in front
            # of it. p10 read 1/3 in the sweep, which looked like a load-bearing
            # citation, and probed 5 of 6 with both controls at 6/6 — its scores are
            # 3,3,3,3,0,3 against a gold of 3, so the failure is a rare zeroing gate
            # rather than a steady refusal. Six of nine passes overall: a two-thirds
            # cell, treated like Q1's p10 and counted.
            #
            # This item is genuinely noisy — a 3-cell spread before and after — so read
            # its floor, not its mean.
            # Q4a IS GONE, all four. Its citations were quote-bearing: the
            # "instead of exercising I would just not eat" do-instead example, gold's
            # own two opacity questions with p4 and p6 named, and the keyword
            # inconsistency naming p17. Rewritten as rules — refuse a substitute
            # activity or another route to the same end; ask whether a reader can see
            # how THIS entry leads to THIS behaviour, an omission that could precede
            # anything being the opaque shape — the numerator did not move at all:
            #
            #   numerator, 16 counted cells   12, 12, 12  ->  12, 12, 12
            #   whole item, 20 cells          16, 16, 15  ->  15, 16, 15
            #
            # p3, p4 and p17 all held at 3/3 with no citation. p6 read 1/3 in the sweep
            # and probed 5 of 6 — BETTER than the 2/3 it managed WITH its citation,
            # which is the second cell in this pass to improve when its answer key was
            # taken away (Q2's p6 went 2/3 -> 3/3). A citation naming one participant's
            # verdict does not merely fail to help; it can pull the grader toward the
            # wrong reading of a neighbouring judgement.
            #
            # p6's scores are 3,3,3,3,5,3 against a gold of 3: gold charges the opacity
            # of "not stretching" leading to lack of exercise, and we now agree with it
            # five times in six.
            # Q4b IS GONE, and its three were the hardest of the pass. Its ACCEPT
            # bullet quoted p13's own second entry and BOTH of p19's as the internal-state
            # and coping-behaviour examples — three of the four accepted shapes lifted
            # from two students the item then excluded, which is the circularity this
            # registry exists to break. (An earlier round had already removed 2, 4, 6, 7
            # and 20 for the opposite reason: the item could not score them even with the
            # answer beside them. See EQUIVALENCE.md.)
            #
            # Three configurations, MEASURED, p15 at 6/6 as control throughout:
            #
            #                        p13    p19    numerator (17 counted)
            #   quoting their words  67%    100%   14, 13, 13
            #   my abstractions       0%      0%   13, 14, 14
            #   invented examples    33%    100%   14, 14, 14
            #
            # The first rewrite replaced EXAMPLES with category descriptions and broke
            # both cells outright — and it was narrower than what it replaced, excluding
            # a state that "befell" the student when the original bullet accepted exactly
            # that. The guide says examples must be INVENTED, not that they should become
            # abstractions; reading it the second way cost two cells and two measurements.
            #
            # With concrete invented examples the item is steadier than it ever was with
            # the quotes — 14 flat against 13-14 — so what those quotes contributed was
            # CONCRETENESS, not the students' particular words. p19 recovered fully.
            #
            # p13 sits at 67% with its own words in the prompt and 33% with an invented
            # near-equivalent: a coin-flip cell either way across nine passes. Counted,
            # like Q1's and Q2's p10, and recorded as a cell whose apparent stability was
            # its own answer key.
            #
            # Whole item, 20 cells: 16, 17, 16 — against the 13/16 this campaign opened
            # with.
            # Q4c IS GONE, all five, and it is the cleanest result of the pass: not one
            # cell moved. Its citations were quote-bearing — p12's junk-food consequence
            # as the ACCEPT example, gold's question to p4, p11's duplicate charge, p15
            # and p17 named in the keyword note — and rewriting them as rules changed
            # nothing whatsoever:
            #
            #   numerator, 14 counted cells   12, 12, 12  ->  12, 12, 12
            #   whole item, 20 cells          17, 17, 17  ->  17, 17, 17
            #   p4, p11, p12, p15, p17        3/3 each, before and after
            #
            # Five cells recovered at zero cost. p16 stays out as `unscoreable` — that is
            # a claim about its gold row, not about the prompt, and its expect_error still
            # matches its measurement — so the honest denominator is 19, at 17 of 19.
            # Q5 IS GONE, all five, which empties this map for handout 1 entirely.
            # Four of the five were named in ONE bullet — a list of four quoted answers
            # with "every one of these scored full marks (participants 8, 9, 19, 20)" —
            # plus p6's duplicate case and p9's thin-reason advisory.
            #
            #   numerator, 15 counted cells   14, 14, 14  ->  13, 14, 14
            #   whole item, 20 cells          18, 19, 19  ->  18, 19, 19   (identical)
            #   p6, p8, p19, p20              3/3, unchanged
            #   p9                            2/3 -> 3/3, better without its answer key
            #
            # The numerator's single dip is p10, which no citation ever named: probed at
            # 3 of 6 with controls at 6/6 and 5/6, so a true coin flip that had been
            # reading 3/3 while the quoted list was in the prompt. A list of four
            # students' answers was cueing a cell it did not name — the teaching effect,
            # not recall — which is the strongest argument in this pass for writing
            # examples rather than borrowing them.
            "Q5":  [],
            # Q6 is gone from this map: rewritten from the dictionary, its
            # prompt cites no participant at all. Every cell on it is scoreable
            # now except p9, which is unreachable for a declared divergence.
        },
    },
    2: {
        "rubric": rubric_h2,
        "template": (
            f"{MATERIALS}/BMod Handout #2 - Learning Operant Conditioning and "
            "Applying It to Behavior Change.docx"
        ),
        "submissions": f"{SUBS}/Handout 2 Submissions with Scoring and Feedback",
        "markers": H2_MARKERS,
        "capture_tail": True,
        "repair_orphans": True,
        "outdir": f"{OUT}/h2",
        "gold": _gold_loader(gold_mod.load_h2, 2),
        "blurb": (
            "Handout 2 of the Behavior Modification Assignment: applying the four types "
            "of operant conditioning to the student's own behaviour-change plan."
        ),
        "exemplar_participants": [],
        # Participants 2 and 3 have byte-identical transcriptions but different
        # gold rows, so at least one is mis-transcribed and neither can be
        # attributed. Excluded from reported metrics; see README.
        "suspect_participants": [2, 3],
    },
    3: {
        "rubric": rubric_h3,
        "template": (
            f"{MATERIALS}/BMod Handout #3 - Presenting Data, Graphing Data, "
            "&amp_ Analyzing Your Intervention.docx"
        ),
        "submissions": f"{SUBS}/Handout 3 Submissions with Scoring and Feedback",
        "markers": H3_MARKERS,
        "capture_tail": True,
        "join_aware": True,
        "outdir": f"{OUT}/h3",
        "gold": _gold_loader(gold_mod.load_h3, 3),
        "blurb": (
            "Handout 3 of the Behavior Modification Assignment: presenting and graphing "
            "the data collected during the intervention, and analysing the result."
        ),
        "exemplar_participants": [],
        # See handout 1's entry. 1c is also the item that cannot be scored at all
        # by a backend without image tools — a separate problem, declared in
        # BACKEND_DEVIATIONS below.
        # Empty, and measured empty. All eight of handout 3's registrations were
        # tested the way handout 1's 25 were: rewrite the citation as a rule, sweep
        # the item three times, compare the cited cell against its own cited
        # baseline. Not one survived, though two failed for a reason handout 1
        # never produced.
        #
        # 1a  p1  3/3 cited, and 6/6 uncited when probed with two controls that
        #         both held 6/6 — the 2/3 in the sweep was noise, not a loss.
        #     p15 3/3 -> 3/3. Unnecessary.
        #     p6  0/3 -> 0/3. Wrong with its own verdict in the prompt and wrong
        #         without it; the exclusion was buying a flattering denominator and
        #         nothing else. Counts as a miss now.
        # 1c  p8  2/3 -> 2/3, unchanged. An unchanged cell needs no probe: the
        #         comparison IS the answer.
        #     p4, p20  gold withdrawn by rebuild_gold_1c, so they leave the
        #         denominator on their own and never needed a citation to do it.
        # 2a  p1  1/3 -> 0/3 and p14 2/3 -> 0/3. These are the first two cells in
        #         33 tests whose citation was genuinely load-bearing — and they
        #         still go, because a citation that lifts a cell from wrong to
        #         wrong-slightly-less-often is measuring recall of an answer key,
        #         which is the whole reason this registry exists. Both count as
        #         misses. That makes 2a's known error shape (+2.0 for a second
        #         `how` gold withheld) visible in its rate instead of hidden
        #         behind two absent cells.
        #
        # Handout 3 counted cells: 51 of 60 -> 57 of 60. What is left out is only
        # 1c's p4, p19 and p20, all excluded on grounds that have nothing to do
        # with citations.
        "cited_participants": {},
    },
}


def config(handout: int) -> dict:
    if handout not in HANDOUTS:
        raise SystemExit(f"unknown handout {handout}; have {sorted(HANDOUTS)}")
    return HANDOUTS[handout]


def find_submissions(handout: int, pids: list[int] | None = None) -> list[tuple[int, str]]:
    cfg = config(handout)
    out = []
    for f in sorted(glob.glob(os.path.join(cfg["submissions"], "*.docx"))):
        m = re.search(r"ID\s*(\d+)", os.path.basename(f))
        if not m:
            continue
        pid = int(m.group(1))
        if pids and pid not in pids:
            continue
        out.append((pid, f))
    return sorted(out)


def excluded(handout: int) -> list[int]:
    """Participants that must not count toward a reported baseline.

    Handout-wide, exemplars included. Kept as-is for baseline.py, which measures
    score.py: that engine drops per RUN rather than per item, and its Q6 prompt
    carries the same exemplars, so narrowing here would silently make its
    reported baseline self-grading.
    """
    cfg = config(handout)
    return sorted(
        set(cfg.get("exemplar_participants", [])) | set(cfg.get("suspect_participants", []))
    )


def suspect(handout: int) -> list[int]:
    """Participants whose INPUT cannot be trusted, whatever the item.

    Handout 2's p2 and p3 have byte-identical transcriptions but different gold
    rows, so at least one is mis-transcribed and neither can be attributed. That
    is a fact about the submission, so it holds for every item — unlike being an
    exemplar, which is a fact about one prompt.
    """
    return sorted(config(handout).get("suspect_participants", []) or [])


def exemplar_drops(handout: int) -> dict[str, list[int]]:
    """{item: [pid]} — exemplar participants, only on items that embed them.

    Self-grading is a property of a PROMPT, not of a handout. Scoring p10, p8 or
    p6 on Q6 grades a model on text it was shown; scoring them on Q1 does not,
    because their Q1 answers appear nowhere in Q1's prompt. Conflating the two
    cost 3 participants x 7 items = 21 cells of handout-1 evidence.
    """
    cfg = config(handout)
    out: dict[str, list[int]] = {}
    pids = sorted(cfg.get("exemplar_participants", []) or [])
    for item in cfg.get("exemplar_items", []) or []:
        if pids:
            out[item] = list(pids)
    # Per-item citations, merged rather than replacing: an item can both embed a
    # worked example and cite others as calibration.
    for item, cited in (cfg.get("cited_participants", {}) or {}).items():
        out[item] = sorted(set(out.get(item, [])) | set(cited or []))
    return out


# ── Deliberate divergences from gold ─────────────────────────────────────────
#
# Cells where the graders applied their OWN written rule inconsistently and both
# implementations apply it uniformly. These are decisions, not defects, and they
# were documented in README prose only — so every harness counted them as errors.
# That cost real conclusions: Q4a reads as one of handout 1's least accurate
# items at 80% exact / 92.8% per check, and is 94% / 98.0 once its three declared
# cells come out. And the DAY2 work was justified partly by "7 of 10 large errors
# are over-credit" when three of those were p8's declared avoidance-framing cells
# — the README says in terms, "anyone measuring the OC items should subtract them
# before concluding the criteria are too permissive."
#
# Distinct from three neighbouring ideas, all of which already exist:
#   olx_prompts.SCORING_DIVERGENCES  — where the WEB and CLI differ from each
#                                      other, not where either differs from gold
#   agreement.UNSCORED_GOLD_CRITERIA — criteria no slot scores at all
#   PER_ITEM_EXCLUDE                 — cells DROPPED, because nothing correct can
#                                      score them. A divergence is still scored;
#                                      we just knowingly disagree.
#
# Q6/9 and Q1/20 appear here for the record and are also in PER_ITEM_EXCLUDE, so
# they never reach a comparison. The other seven do.
GOLD_DIVERGENCES: list[dict] = [
    {
        "code": "DUPLICATE_EFFECT_TIE_BREAK", "cells": [("Q6", 5)],
        "why": "our sheet applies a duplicate rule to the EFFECT boxes and gold does "
               "not. p5 writes a textbook parallel answer -- six sentences, one per "
               "box, the cleanest split in the corpus -- in which both effect boxes "
               "describe the same effect on the same consequence: eating fruit and "
               "vegetables instead. `affect_c2`'s own note says that where both "
               "boxes describe the same effect on the same consequence only the "
               "FIRST can count, so we credit `affect_c1` and answer `incomplete` on "
               "`affect_c2`. Gold credits both, because gold charges the naming miss "
               "once, under the state slot, and does not charge the effect slot "
               "again -- verified across all twenty rows, where every effect slot "
               "gold DOES withhold is one whose box describes no effect. Both sides "
               "reach 6.25 by different routes; the disagreement is one slot deep "
               "and does not move the total. "
               "This is a POSITION, not an error, and it is the more faithful one: "
               "the item asks about EACH of two consequences, `cover` already "
               "enforces that on the naming slots, and this extends it to the "
               "effect slots so a response addressing one consequence twice cannot "
               "collect both effect credits. Gold's no-double-jeopardy reading is "
               "defensible and simply differs. "
               "MEASURED, and the reason it stays as it is. The rule is live on ONE "
               "cell: of the ten cells with both effect boxes filled, nine agree "
               "with gold and p16 refuses for gold's own reason. Two changes were "
               "swept and both were worse. Replacing the positional tie-break with "
               "\"credit whichever box describes the consequence more directly\" as "
               "free-standing sentences broke p14, p15 and p16 in one pass. "
               "Rewriting it as ONE sentence wholly inside the \"where both describe "
               "the same effect\" conditional -- no imperative escaping the clause -- "
               "still gave 14/20 against a 17/20 baseline, breaking p12 where the "
               "condition applies and p15 where it CANNOT: p15 has two empty effect "
               "boxes, and both its state verdicts moved anyway. So the risk lives "
               "in editing a note this long, not in what the note says, and the "
               "incumbent wording is the only one carrying none of it.",
    },
    {
        "code": "ANTECEDENT_REUSED_AS_BEHAVIOR", "cells": [("Q4b", 4)],
        "why": "p4 gave \"scrolling on tiktok\" and \"becoming grumpy\" as their "
               "active behaviours, having already named \"scrolling through "
               "tiktok\" and \"having grumpy emotions\" as their 4a triggers. Gold "
               "charged both as repeats, -3. The scoring dictionary states no such "
               "rule; it was inferred from this cell. Reading all 40 antecedents "
               "in the corpus shows why it will not generalise: students name a "
               "state, circumstance, feeling or absence as the trigger — \"too "
               "cold outside\", \"feeling exhausted\", \"not seeing immediate "
               "results\" — and p4 is the ONLY one who names an ordinary activity, "
               "which is the only shape that can collide with an active behaviour. "
               "So the rule rests on one cell. Two implementations were measured "
               "and both were worse than not having it: a `repeats_antecedent` "
               "check answered `absent` on p4 in one run and `met` in the next "
               "while misfiring on p6 and p20 (spread 4), and a guidance clause "
               "fixed p4 but broke p1, p14 and p16 on surface wording and took the "
               "spread to 5. Both times the model matched the 4a SENTENCE rather "
               "than the trigger in it.",
    },
    {
        "code": "REASON_FOR_WRONG_BEHAVIOR", "cells": [("Q5", 4)],
        "why": "p4's first entry reads \"I continue sleep enough because sleep is "
               "good for you, I am gaining something)\" — it names the OPPOSITE of "
               "the unwanted behaviour and gives a reason to change rather than a "
               "payoff for continuing. Gold credited it and charged only the second "
               "entry, so 2.5 of 5. Reproducing that needs a scorer to read through "
               "a dropped \"to not\" AND to accept \"sleep is good for you\" as a "
               "payoff for not sleeping, which contradicts the item's own "
               "W_NOT_REASON rule. All four engines — two prompts, two model "
               "families — classify it `not_reason` and score 0, in near-identical "
               "words. The rule 2 / rule 3 boundary added to the guidance places it "
               "in rule 3 as well, so this divergence is the deliberate consequence "
               "of drawing that line, not an oversight left in it.",
    },
    {
        "code": "A_NO_CHANGE",
        "cells": [("Q6", 8)],
        "why": (
            "gold charges BOTH change slots — \"did not say how each antecedent is "
            "being changed\" — for offering a scheduling commitment where the "
            "antecedent was stated as not doing the goal behaviour. p8's first "
            "antecedent is \"being lazy and not making enough time for the gym\" and "
            "the change is \"putting an hour a day from Tuesday-Friday\"; the second "
            "is \"staying home and playing video games, rather than going to the gym\" "
            "and the change is \"go out and conduct exercise multiple days a week\". "
            "Read literally each change DOES negate the antecedent as the student "
            "framed it, because the student framed the antecedent as the absence of "
            "the goal behaviour. The graders applied the item's pedagogical point "
            "instead: an antecedent change alters what triggers the unwanted "
            "behaviour, it does not resolve to do the wanted one.\n\n"
            "Declared rather than chased because p6 is the same shape and gold "
            "CREDITS it. p6's antecedent is \"not attending the gym & stretching as "
            "often as I should\" and its change is \"I will make it mandatory for "
            "myself to attend the gym at least three times a week\" — an absence-framed "
            "antecedent answered with a scheduling commitment, exactly like p8. No "
            "textual feature separates them, and three attempts confirmed it: a prose "
            "acts-on rule moved one of p8's two slots and stuck on the other; a "
            "reported-only classification probe had the model answer `antecedent` for "
            "both, which is correct on a literal reading; and a test keyed on "
            "absence-framed antecedents would flag six credited cells (p2, p3, p5, p6, "
            "p16, p19) to catch this one.\n\n"
            "The scorer treats p6 and p8 alike, which is the defensible position. "
            "p8 accounts for both of `change_a1`'s errors and `change_a2`'s only one, "
            "so with this declared those two slots are at ceiling."
        ),
    },
    # C_MISMATCH for Q6/p17 was here and is now CORRECTED_GOLD[("Q6", 17)]. A
    # divergence says the cell is scored as gold has it and the miss stands; a
    # correction says the row is wrong. Once five measured wordings showed that no
    # consistent rule can credit p17's consequence, the second is the honest
    # description, and keeping both would have claimed we disagree with a number we
    # now match. The measured history moved into the correction's reason.
    # A_MISMATCH for Q6/p9 was here and is now CORRECTED_GOLD[("Q6", 9)], for the
    # same reason C_MISMATCH moved: we no longer disagree with the number we score
    # against. Its evidence — that p6 is the same shape and gold credits it, and
    # the three attempts that failed to separate them — moved into the reason there.
    {
        # MEASURED BY REMOVAL, 3 runs with `behavior_*`'s test (5) deleted from
        # both slots and the served prompt checked to confirm it was gone. An
        # earlier version of this entry asserted the same conclusion from the
        # RECORD — p7 and p8 are right, their entries are not-doings, therefore
        # the test is what saves them — which is a hypothesis, not the arithmetic
        # the guide asks for. Deleting it and measuring says:
        #
        #   counted   [14, 13, 13] with the test   ->   [13, 12, 13] without
        #   rescued   p7 3/3 -> 0/3, p8 3/3 -> 0/3, p14 3/3 -> 2/3
        #   cost      p12 0/3 -> 3/3, p16 1/3 -> 3/3
        #
        # So it earns its place at +1 cell per run, and the substance of the
        # inference held. What the inference could NOT see is half the picture:
        # the test also costs p16, and it marginally rescues p14. Two of the five
        # cells it moves were invisible from the record.
        "code": "B_NOT_ACTIVE", "cells": [("Q4b", 12), ("Q4b", 4)],
        # p4 is a SECOND Q4b disagreement and it is NOT a ceiling, though this
        # file said it was for one commit. Gold charges a criterion the rubric
        # does not carry — "your behaviors cannot be the same as your
        # antecedents" — and p4's two entries are its own 4a antecedents with the
        # pair swapped: 4a gives "having grumpy emotions" and "scrolling through
        # tiktok", 4b gives "scrolling on tiktok instead" and "becoming grumpy".
        # We credit the first and refuse the second, 3.5 against gold's 2.0.
        #
        # The ceiling claim was that no rule can charge this without breaking the
        # cells gold credits, argued from a lexical sweep: 4b/4a overlap appears
        # in 13 of 20 cells and gold gives four of them full credit. That was a
        # prediction about a rule nobody had written, and the sweep over-reports
        # — its own key-word heuristic flagged p11 and p19, which the grader had
        # already credited.
        #
        # MEASURED, 3 runs, with a sixth test added to both slots: an entry that
        # names the same THING as one of the student's own 4a antecedents fails,
        # judged by REFERENT and not by topic.
        #
        #   counted   [14, 13, 13] baseline   ->   [15, 12, 14] with the test
        #   p4        0/3 -> 1/3              the target does move
        #   p1 p12 p15 p17                    unchanged — the four gold credits held
        #   spread    1 cell -> 3 cells
        #
        # So the rule is possible and the ceiling was wrong. It is not adopted
        # because of the SPREAD: a mean of 13.67 against 13.33 for three times the
        # variance is the trade the guide refuses, since a configuration that
        # swings three cells cannot tell you whether the next change helped.
        # p4's miss therefore stands as a divergence, with the door open to a
        # steadier formulation of the same test.
        "why": "gold credits a not-doing as an active behaviour. p12's second "
               "entry is \"I skip adding fruits or vegetables to my meals even "
               "when they are available and let them sit in the refrigerator "
               "until they go bad\" — it names no activity that displaced the "
               "goal, which is what the question asks for, and `behavior_*`'s "
               "fifth test refuses it in terms. Gold gives 5.0; we give 3.5, 0 of "
               "3. The test that refuses it is worth +1 cell a run against "
               "deleting it, measured, so it stays and this miss stands.",
    },
    {
        # MEASURED, and the measurement is what this entry is FOR. The item's own
        # ACCEPT bullet quoted p19's phrase as an example that "earned full
        # credit", so the miss looked like an accept-side gap in the criterion.
        # Defining both antecedent slots from gold — internal states qualify,
        # refuse only aftermath / do-instead / a 4c consequence — left p19 at 0 of
        # 3 and cost p16 a run, so it was reverted. The criterion was never the
        # cause. The DIRECTION was, and the guidance now states that test instead
        # of quoting the cell.
        "code": "A_NOT_ANTECEDENT", "cells": [("Q4a", 19)],
        "why": "gold credits an antecedent that is an AFTERMATH of the UTB. p19's "
               "UTB is lack of sleep and its first example is \"waking up and not "
               "feeling motivated\", which happens after sleeping too little and "
               "so cannot precede the behaviour it results from. Both scorers "
               "refuse it — 0 of 3 here, 0 of 6 in the stored web runs — and the "
               "refusal is correct on the criterion both sides share, that an "
               "antecedent happens BEFORE the UTB.",
    },
    {
        "code": "A_NO_KEYWORD", "cells": [("Q4a", 9), ("Q4a", 15)],
        "why": "the dictionary requires the word \"antecedent\" or \"trigger\". "
               "p17 lost the point for omitting it; p9 and p15 did not. Applied "
               "uniformly. Contrast Q4c, whose equivalent charge was REMOVED "
               "today because no gold row applies it at all — the difference is "
               "evidence, not consistency for its own sake.",
    },
    {
        "code": "A_NOT_ANTECEDENT", "cells": [("Q4a", 14)],
        "why": "gold refused both of p14's examples (-4 = two refusals) while its "
               "commentary accounts for only one, and the first — \"not seeing "
               "immediate results\" — is the state-of-mind case the item's own "
               "guidance says to accept. Credited in five runs of five.",
    },
    {
        "code": "AVOIDANCE_FRAMING", "cells": [("DAY1", 8), ("WK1", 8), ("WK2", 8)],
        "why": "p8's contingencies are stated by what is AVOIDED (\"so I don't "
               "have to do an extra 30 pushups if...\"), which is structurally "
               "sound: a consequence is still arranged and still contingent. The "
               "graders read the phrasing as a failure; score.py flags for review "
               "and never deducts, and the lo-blocks sheet reaches the same "
               "verdict. Both sides are 4, 4 and 2 points over gold BY DESIGN — "
               "the largest of these by cell count.",
    },
    # WRONG_DEFINITION (D2/p11) RETIRED 2026-08-24, moved to CORRECTED_GOLD.
    # It was the only divergence in this list running DOWNWARD — both
    # implementations scoring 1 point UNDER gold rather than over — and that
    # asymmetry was the tell. A divergence is a disagreement with a COHERENT
    # gold decision; p11's row is an isolated arithmetic slip against the same
    # grader's own practice, since D1/p7 has the identical defect, the identical
    # model answer of 0, and gold agrees there. Wrong number, not wrong
    # judgement, so it belongs in the table for wrong numbers. See CORRECTED_GOLD.
]


def gold_divergence(item: str, pid: int) -> str | None:
    """The divergence code for one cell, or None. See GOLD_DIVERGENCES."""
    for d in GOLD_DIVERGENCES:
        if (item, pid) in d["cells"]:
            return d["code"]
    return None


def gold_divergence_cells() -> dict[tuple[str, int], str]:
    """{(item, pid): code} for every declared cell."""
    return {c: d["code"] for d in GOLD_DIVERGENCES for c in d["cells"]}


# ── Measurement ceilings ─────────────────────────────────────────────────────
#
# Why no correct scorer reaches 100%, per item, with the evidence. A FOURTH kind
# of gold caveat, and the distinctions matter:
#
#   GOLD_DIVERGENCES         we disagree with a grader on purpose, on named cells
#   PER_ITEM_EXCLUDE         cells dropped, nothing correct can score them
#   agreement.UNSCORED_GOLD_CRITERIA
#                            criteria NO slot scores at all
#   GOLD_CEILINGS (here)     criteria that ARE scored, on cells gold itself does
#                            not decide consistently — so some are unwinnable
#                            whichever consistent rule you adopt, and which ones
#                            depends on the rule
#
# The practical use is to stop a ceiling reading as headroom. Q3 sits at 75% and
# looks like 25% of work available; about 10% of it does not exist.
#
# Q6 p4 was listed here and is NOT any more. Its gold of 6.00 implies 3.2 slots
# of 1.25, so no slot-derived score can land on it — but that is now HANDLED
# rather than merely explained: scores_as_exact() credits the nearest reachable
# value, so a scorer returning 6.25 is counted correct and the cell is neither a
# ceiling nor headroom. A note here would tell a reader there is unwinnable
# ground where there is none.
#
# Contrast DAY2 p7 below, which stays. Its gold of 1.00 IS reachable; it just
# does not reconcile with its own itemised comment. Nothing computes that away,
# so it remains a real ceiling.
GOLD_CEILINGS: dict[tuple[str, str], tuple[str, ...]] = {
    ("1", "Q6"): (
        "`change_a1`/`change_a2`: whether a stated action actually CHANGES the "
        "antecedent it is paired with, rather than improving the goal behaviour, "
        "cannot be scored consistently against gold, and the cells that go wrong "
        "depend on which rule you adopt. p2 is over-credited: its second "
        "antecedent is a pastime and its change makes the exercise more pleasant, "
        "which gold refuses in terms — \"listening to music while working out does "
        "not change your antecedent of playing video games and not wanting to "
        "stop\" — while both scorers credit it. "
        "MEASURED, three wordings, none of which separates it. A rule asking "
        "whether the action improves the goal behaviour instead of the trigger "
        "fixed p2 and cost p3 and p5, both of which state a real action followed "
        "by a purpose clause (\"by X, which will help me Y\") that reads as goal "
        "language. Ignoring the purpose clause and testing the trigger's object, "
        "occasion and supply held p3 and p5 and lost p2. Naming p2's shape "
        "concretely — an action improving the conditions of the exercise while the "
        "trigger is a different activity — held p3 and lost p5. "
        "The reason is that p5's credited action changes the SUPPLY at the trigger "
        "moment while p2's changes a different activity, and both read as "
        "providing something more pleasant. A_NO_CHANGE predicted exactly this: it "
        "records that a test of this shape \"would flag six credited cells (p2, "
        "p3, p5, p6, p16, p19) to catch this one\", and p2, p3 and p5 are the "
        "three that moved. Six attempts across the project now, three of them "
        "measured here. "
        "p10 WAS listed here as the same criterion in its other form — a borderline "
        "flip on `change_a1`, answering `incomplete` on 1 of 3 passes and `met` on "
        "3 of 3 in the next sweep. That reading was WRONG, and it is left here "
        "because the way it was wrong is the useful part. The instability was real "
        "but it was not a close judgement: p10's fixture was defective. Its "
        "`state_a1` held a mid-sentence fragment and its `change_a1` held two whole "
        "sentences, so the grader was being asked to judge a method statement "
        "against a box that had been cut in the wrong place. Repaired, p10 scores "
        "10.00 — five consecutive probes, then 3 of 3 in each of the two sweeps "
        "since. Nothing about the criterion changed. "
        "The lesson is about attribution, not about p10. An unstable cell reads "
        "exactly like a genuinely close judgement, and \"the criterion cannot be "
        "scored consistently\" is the more flattering of the two explanations, "
        "because it puts the fault in gold. Three of the cells once explained that "
        "way — p10, p14, p15 — turned out to be fixtures that had cut the student's "
        "sentences in the wrong place, and each was found by reading the boxes out "
        "one at a time, never by a check. Suspect the fixture before the criterion. "
        "So p2 sits alone on this ceiling. The item HAD a second one of a different "
        "kind -- `p9`, measured at nine passes as exact 5 of 9, 56% with a 95% "
        "interval of [27%, 81%], flipping between 2.50 and 3.75 on identical input "
        "-- and it is RETIRED as of 2026-08-20. Defining \"matches\" before the "
        "credit components that use the word, with antonym pinned to the two ends "
        "of ONE scale, took p9 to 9 of 9 at nine passes. Its `state_c1` reads \"I "
        "hope I do not suffer the consequences of bad health\" against a listed "
        "\"better health\": resolve the negation and those are the SAME state, not "
        "opposite ones, and the flipping was the grader having no rule that said "
        "so. It was never an unwinnable criterion; it was an undefined term. "
        "Two things worth keeping from having been wrong about it. Four rule "
        "variants were credited with fixing p9 before its base rate was known, and "
        "a 56% cell reaches exact-on-three-passes unaided -- which is why a "
        "per-cell claim needs nine passes. And an instability is not evidence that "
        "a criterion cannot be scored: it can equally mean the prompt never told "
        "the grader how to decide. "
        "Q6's practical maximum is therefore 19 of its 20 counted cells, p2 being "
        "the one. See scoring/QUALITY_CONTROL.md for the method.",
        "`state_c1`/`state_c2`: a consequence box that describes the ANTECEDENT "
        "going away, credited as though it named a listed consequence. p5 is the "
        "cell. Its 4c lists worsening overall health and harder-to-reach fitness "
        "goals; its `state_c1` says the student will no longer suffer from being "
        "fulfilled by unhealthy and fatty foods, which is their own 4a antecedent. "
        "We credit one listed consequence, gold credits none. Unlike the two "
        "ceilings above this one is OURS, not gold\'s -- gold is right to refuse "
        "it -- and it is here rather than in GOLD_DIVERGENCES because we do not "
        "think our reading is defensible. It is recorded as a ceiling because it "
        "has been measured and cannot be removed at proportionate cost. "
        "IT DOES NOT COST A CELL, which is why the item\'s practical maximum stays "
        "at 18 of 20: p5 lands on gold\'s 6.25 anyway, because this over-credit is "
        "cancelled by the `affect_c2` refusal declared in GOLD_DIVERGENCES as "
        "DUPLICATE_EFFECT_TIE_BREAK. Two errors, opposite directions, one cover "
        "group, right total. That cancellation is also why it cannot be fixed "
        "alone: refusing the box without also crediting the flip takes p5 to 5.00. "
        "THREE FURTHER ATTEMPTS, 2026-08-20, all reverted, and the last of them "
        "closes the most promising hypothesis. The diagnosis looked exact: p5's "
        "4c-1 reads \"worsening my overall health BY turning to unhealthy "
        "alternatives\", so the CONSEQUENCE is the health clause and the trailing "
        "\"by ...\" names the behaviour -- and both c-state boxes were matching "
        "that trailing clause, which is exactly why the family reads 1 against "
        "gold's 0. A clause was added to the match definition saying so: an entry "
        "may name the element and then the MEANS by which it comes about, and a box "
        "matching only the means has named the behaviour. It made no difference. "
        "p5's c-family stayed [1, 1, 1] in every pass of a 3-pass sweep, on the "
        "cell it was written for. The structural reading was right and telling the "
        "grader about it changed nothing. "
        "Also tried, bundled with a narrowing of the duplicate-effect tie-break so "
        "that it fires only where both effect boxes tie to the SAME listed "
        "consequence -- the bundle scored 15/20 against 17/20 and took p14 from 10 "
        "x3 and p16 from 8.75 x3. Isolating the two showed the tie-break was the "
        "cause; the means clause alone was cell-neutral. Do not re-run either "
        "without reading out/q6_means_tiebreak and out/q6_means_only first. "
        "So the ceiling now rests on three independent failures rather than one, "
        "and on a diagnosis that is textually correct and behaviourally inert. "
        "MEASURED, four wordings, all reverted. Crediting the flips and refusing "
        "the antecedent-improvement forms was tried as a veto (broke p4), as a "
        "sharpened test (cost p6 3.75 on a previously stable cell, because a box "
        "can name an antecedent AND a listed consequence under one negation), as a "
        "fallback ordered after the flip clauses (broke p1 and p4, c-family errors "
        "2 -> 3), and as flip clauses with no boundary at all (16/20 against a "
        "17/20 baseline). The pattern across all four: whatever fixes this "
        "over-credit moves cells the rule was never scoped to touch. See the Q6 "
        "guidance comment in rubric_h1 for the full account.",
    ),
    ("1", "Q3"): (
        "`action_oriented`: five answers justify the goal by CAPABILITY rather "
        "than by naming an action, and gold splits them — p14 (\"my early mornings "
        "are free and my gym is near my house\") and p18 (\"I have access to the "
        "university's gym\") are CREDITED, while p8 (\"I will be able to make time\"), "
        "p16 (\"I have a lot of time on my hands\") and p20 (\"i am able to full "
        "asleep\") are DEDUCTED. Same claim, opposite verdicts. Any consistent rule "
        "gets at most 3 of those 5, so >=2 cells are unwinnable and 18/20 is the "
        "ceiling. Measured: the other four SMART slots are 0-2 errors each, this "
        "one is 4-5, and a 'labelled Action section' rule matches gold on only "
        "12/20 — worse than the models manage without it. "
        "MEASURED AGAIN 2026-08-23, and the ceiling holds with the cells "
        "redistributed. Defining the slot from gold's own decisions — an activity "
        "or a concrete enabling circumstance counts, grounding actionability in "
        "another SMART letter does not — took p14 and p18 from 0-1 of 3 to 3 of 3 "
        "and left p16 credited, which is the direction that keeps four cells "
        "right and one wrong rather than the reverse. p19 is the one cell in this "
        "family that is NOT part of the ceiling: it grounds actionability in "
        "measurability while naming the goal behaviour itself as the doing, so "
        "the grader finds an action and credits it, 0 of 3. A clause saying that "
        "the goal RESTATED is not the action would separate it — the same \"you "
        "cannot do something instead of itself\" logic Q4b's `behavior_*` rule "
        "carries — with p13's \"I can take my medication before I go to bed\" as "
        "the control that must keep its credit. Untried.",
    ),
    ("2", "DAY2"): (
        "p7's gold is 1.00 while its comment itemises only \"-1 pt\", which implies "
        "3.00. The row does not reconcile with itself, so 1.00 is unreachable by "
        "any scorer that charges the stated deduction. WK1 p7 is the same shape.",
    ),
}


def gold_ceiling(handout: int, item: str) -> tuple[str, ...]:
    """Why this item cannot reach 100% — one entry per ceiling, () if none.

    A tuple rather than a string because an item can hit more than one ceiling
    for unrelated reasons: Q2 has both `reasons_given` (an uncountable
    distinctness judgement) and `wgb_inverts_utb` (substitution vs outcome
    decided both ways). Joined into one string, every caller's summary line
    would show the first and silently drop the rest.
    """
    got = GOLD_CEILINGS.get((str(handout), item)) or ()
    return (got,) if isinstance(got, str) else tuple(got)


# Gold criteria that neither system scores, declared rather than left to be
# rediscovered. An omission that is SYMMETRIC costs the head-to-head nothing —
# both columns miss it identically — but an undeclared one is indistinguishable
# from a bug, which is the whole reason this list exists.
#
#   1c, "missing baseline data week" (p11, -1): the only instance in 20 rows,
#   and unreachable on the web by construction. The chart is drawn by
#   SelfMonitorPlot from the four data fields, so a populated baseline series is
#   necessarily plotted — p11's `baseline` field holds "0, 30, 0, 0, 30, 0, 30",
#   which is why their 1b scored a full 4.0. The grader is marking a series
#   absent from a hand-drawn paper graph whose data table contained it. Adding a
#   slot for it would have no reachable failing state: with baseline data present
#   the web always plots it, and with baseline data absent 1b already takes the
#   point, so the slot could only double-count or misfire. Note also that p11's
#   row does not self-reconcile — it itemises -2/-2/-1 against a score of 7.0 —
#   so rebuild_gold_1c derives from the itemised deductions, not the total.
# Cells where the gold row cannot be scored on the item it sits in, dropped from
# that item only. Mirrors PER_ITEM_EXCLUDE in agreement_app.py; the two sides
# must drop the SAME cells or the item's two columns stop being a comparison.
PER_ITEM_EXCLUDE: dict[str, dict[int, str | dict]] = {
    "Q6": {
        # Rewritten after measurement contradicted the original reason, which said
        # the fixture tie-break decided 2 of 8 slots and that "the CLI's error here
        # is exactly -2.50". Both halves were false. The tie-break DID put the text
        # in state_c2 and leave affect_c2 empty — and the scorer answers `mismatch`
        # on state_c2 and `absent` on affect_c2, which is exactly what gold charges
        # ("-2.5 pts: missing second consequences"). The arbitrary split landed on
        # gold's own answer and cost nothing.
        #
        # The real reason is the divergence, and it is a clean one: the scorer
        # agrees with gold on SEVEN of eight slots, and the eighth is `state_a1`,
        # where it answers `mismatch` and gold credits. That is the declared
        # A_MISMATCH divergence — p9's Q6 changes a third antecedent not listed in
        # their 4a, and the dictionary is explicit that the antecedents must match
        # up. Gold is unreachable because gold is lenient there and we are not, so
        # a miss stays EXPECTED; the error is one slot, not two.
        # p9 was excluded here as unscoreable with expect_error -1.25. It is now
        # CORRECTED_GOLD[("Q6", 9)] instead: the exclusion dropped a perfectly
        # scoreable cell from every rate in order to absorb an error that was
        # gold's, and correcting the row lets the cell count. Its measured
        # behaviour is unchanged at 3.75.
    },
    "Q4c": {
        16: {
            "why": "gold 3.0 for \"did not say if this behavior is a good choice "
                   "for you modify and why\" — but the handout asks that under 4b, "
                   "which has its own `Modify:` field and carries "
                   "modify_stated/modify_why for 3 of its 5 points. 4c asks only "
                   "for two consequences plus the keyword. The deduction is "
                   "misfiled: p16's Q4b row is a clean 5.0, so the point was taken "
                   "off the wrong item. No correct 4c scorer can reach 3.0 here, "
                   "and both systems return 5.0.",
            # VERIFIED against 61 handout-1 runs on disk: 58 return 5.0, which
            # is this +2.00. The three that return 3.0 are all pre-refactor
            # snapshots (h1_preconv, h1_precover, h1_prevocab), and they reach
            # gold's NUMBER by a route gold never took — charging
            # C_NOT_CONSEQUENCE on the second example, where gold's stated
            # reason is a misfiled 4b criterion. Hitting the total on a
            # different criterion is not scoring the cell; the claim that no
            # correct 4c scorer reaches 3.0 stands. Still asserted every run,
            # and reported in the not-counted block if it drifts.
            "expect_error": +2.00,
        },
    },
    "2a": {
        # Empty. p18 was excluded here as unscoreable with expect_error -2.00,
        # on the argument that gold's 6.0 credits a verdict the student copied
        # from the template's worked example, which `join_aware` strips, so no
        # correct scorer could reach it.
        #
        # The record never agreed. Six passes over web_v8 and web_v9 return
        # `verdict: met` every time, cited to a sentence the student DID write
        # ("My exercise intake increased from 0 to 3 session a week, as shown by
        # the data"), and the cell scores gold's 6.0 in five of the six. The
        # item's own guidance licenses that reading in terms: "a verdict that
        # cites the data as its evidence, followed by one concrete circumstance
        # under which the plan worked, covers the verdict and both
        # explanations", one of three shapes it says earned 6/6. The copied
        # sentence was never load-bearing for the credit; the student's own
        # first sentence carries it.
        #
        # So the exclusion was hiding a cell we score correctly, which is the
        # one kind QUALITY_CONTROL.md section 5 says must go: it "dropped a
        # perfectly scoreable cell from every rate", exactly as Q6/p9's did
        # above. Removed rather than re-argued, and the cell's measured
        # behaviour does not change at all — the counted n goes 17 to 18. The
        # rate rises in five of the six stored passes and FALLS in the sixth
        # (web_v8 run 1, where p18 answered `hows_given: 1` and scored 4.0), so
        # 14-15 of 17 becomes 14-16 of 18. That sixth pass is the honest cost of
        # counting a cell that flips once in six.
        #
        # What the exclusion was also doing, silently: `check_consensus_spans_are_disjoint`
        # skips `unscoreable` cells, so p18's `verdict`/`how1` overlap was
        # exempt by side effect. It is now declared where the other one is, in
        # enforcement.CONSENSUS_OVERLAP_BACKLOG.
    },
    "1c": {
        4: "gold 0 (\"Did not provide a graph\") but all four weeks of data "
           "supplied — on the web that data DRAWS the chart, so the paper "
           "failure is unreachable rather than missed",
        19: "the same: gold 0 for no graph, four complete weeks of data",
        20: "the same failure in its third form — a written DESCRIPTION of a "
            "graph, which on the web IS the answer: the labels are typed into "
            "fields and the chart is drawn from the four complete weeks. Both "
            "halves of that are now true. The chart was always drawn from the "
            "four weeks, but the three label fields were EMPTY until the "
            "fixture audit found it: there is no chart for the paper scorer to "
            "read a title off, so it recorded none, and the student's own "
            "\"Title: Sleep Duration Over 4 Weeks X-axis label: Days (or "
            "Weeks) Y-axis label: Hours of Sleep\" belonged to no box. Seeded "
            "from that description in agreement_app.CONSENSUS_FIXES",
        # p11 is NOT a fourth: asked twice now, settled both times. Its "-1 pt:
        # missing baseline data week" never reaches a comparison, because
        # rebuild_gold_1c restates the row from its labelling verdicts and the
        # improvised charge drops out — effective gold 6.0, not the sheet's 7.0.
        # The scorer reads title from the graph (not the prose, which is empty)
        # and faults x and y exactly as gold does. See
        # agreement.UNSCORED_GOLD_CRITERIA, which is where that criterion is
        # declared.
        #
        # The "and returns 6.0, exact match" that used to end this note is NOT
        # what happens, and the fixture audit measured it: six passes over
        # web_v8 and web_v9 return 4.0. The extra 2.0 is `legend: absent`, on a
        # legend of day names ("Sunday, Monday, ... Satureday") that gold did
        # not fault. Still nothing to EXCLUDE — the row is reachable and the
        # fixture is faithful, `series` holding the student's literal legend —
        # but it is a live disagreement on a criterion this note never named,
        # and it is the item's only counted miss. See scoring/BACKLOG.md.
    },
}


# ── One place that answers "is this cell counted?" ──────────────────────────
#
# Three reasons a cell is not counted, and they mean DIFFERENT things when the
# model gets one wrong, which is why the kind travels with the pid:
#
#   suspect      the SUBMISSION cannot be trusted (mis-transcribed), so the
#                input is not what the student wrote. A miss says nothing.
#   self_graded  the PROMPT contains this participant's answer and the grader's
#                decision. A miss here is a RED FLAG: the answer was supplied
#                and the model missed it anyway.
#   unscoreable  the GOLD ROW cannot be reproduced by any correct scorer. A miss
#                is EXPECTED — the documented behaviour, not a defect.
#
# All three harnesses must read this, or their rates are computed over different
# denominators and the columns stop being a comparison. Not theoretical: the
# table above lived in agreement.py and agreement_app.py as two hand-kept mirrors
# and in baseline.py not at all, so the paper scorer counted five cells the other
# two dropped.

EXCLUSION_KINDS = ("suspect", "self_graded", "unscoreable")


def unscoreable(item: str) -> dict[int, str]:
    """{pid: why} — cells whose gold no correct scorer can reach."""
    return {pid: (e["why"] if isinstance(e, dict) else e)
            for pid, e in PER_ITEM_EXCLUDE.get(item, {}).items()}


def unscoreable_expectation(item: str) -> dict[int, float]:
    """{pid: pred - gold} for unscoreable cells that declare what the miss IS.

    An `unscoreable` reason says a correct scorer CANNOT reach the gold, which is
    a claim about a number. Left in prose that number goes stale without anything
    noticing: Q6's p9 asserted "the CLI's error here is exactly -2.50" while every
    run measured -1.25, and the sentence went on pointing future work at the
    fixture reconstruction when the whole story was a declared divergence.

    Declaring it here makes it an assertion the harnesses check on every run, so
    the cell either behaves as documented or says so.
    """
    return {pid: float(e["expect_error"])
            for pid, e in PER_ITEM_EXCLUDE.get(item, {}).items()
            if isinstance(e, dict) and e.get("expect_error") is not None}


def scored_exactly(item_id: str, gold: float, pred: float) -> bool:
    """Did this cell score exactly right, by ITEM ID rather than rubric record?

    The same decision as `scores_as_exact`, reachable from the places that have
    an item id and a number and nothing else — which turned out to be most of
    them. Every rate in this project is a count of cells that "scored exactly
    right", and that phrase had SIX implementations: two called
    `scores_as_exact`, and four re-derived it as `abs(pred - gold) < 1e-9`. The
    four included the ALL aggregate on both the CLI and paper harnesses and, worse,
    the median-run SELECTOR — so the run chosen for publication was picked by a
    rule the published table then disagreed with. One table printed 67% and 58%
    for the same twelve cells.

    `check_unreachable_gold_is_allowed` did not catch it: it tested that the
    string "scores_as_exact" appeared in each file, and it did — in the one code
    path that used it.
    """
    for h in (1, 2, 3):
        rec = config(h)["rubric"].BY_ID.get(item_id)
        if rec is not None:
            return scores_as_exact(rec, gold, pred)
    raise KeyError(f"no rubric item {item_id!r} in any handout")


def stale_claim(item: str, pid: int, gold: float, pred: float) -> str | None:
    """The warning line for a cell that stopped behaving as its exclusion says.

    Lives here rather than in the three reporters because they are three copies
    of one block already — the same mirror-keeping this module exists to end.
    """
    want = unscoreable_expectation(item).get(pid)
    if want is None or abs((pred - gold) - want) < 1e-9:
        return None
    return (f"<-- CLAIM STALE: declared expect_error={want:+.2f}, measured "
            f"{pred - gold:+.2f}. Fix the reason in "
            f"handouts.PER_ITEM_EXCLUDE or the exclusion")


def cell_exclusions(handout: int, item: str) -> dict[int, tuple[str, str]]:
    """{pid: (kind, why)} for one item — every cell that must not be COUNTED.

    Not a work list. Excluded cells are still RUN and still scored: whether the
    model gets them right is evidence in its own right, and suppressing the call
    threw that evidence away. Only the RATE excludes them.
    """
    out: dict[int, tuple[str, str]] = {}
    for pid in suspect(handout):
        out[pid] = ("suspect", "mis-transcribed submission; the input is not "
                               "what the student wrote")
    for pid in exemplar_drops(handout).get(item, []):
        out[pid] = ("self_graded", "this item's prompt contains their response "
                                   "and the grader's decision")
    for pid, why in unscoreable(item).items():
        out[pid] = ("unscoreable", why)
    return out


# ── Items a backend cannot score at all ─────────────────────────────────────

def not_comparable_items(handout: int, supports_tools: bool) -> dict[str, str]:
    """{item: why} — items the PAPER scorer cannot score from this backend.

    Scoped to score.py, and only baseline.py consults it. The web and CLI are
    NOT affected and must not be filtered by this: they never look at an image.
    1c on those sides is scored from the four weeks of data the student typed,
    through `derived="has_own_graph:complete:..."` in the OLX, and web_v8 scores
    it 16/17 with no tool involved. It is score.py's handout-3 prompt that asks
    the model to Read the graph as an IMAGE, because on paper a graph is a
    picture — so the deviation belongs to that prompt, not to the item.

    COMPUTED from the rubric rather than listed, so it cannot go stale: score.py
    passes `allow_tools=["Read"]` for exactly the items flagged `graph_item`, and
    a backend that does not forward tools scores those blind. Blind on a graph
    item is not noise, it is a systematic zero — the model reports no graph
    because it cannot see one.

    Observed, not hypothesised: paper+gpt-5-mini returned 0.00 on 11 of 20 cells
    of 1c where gold is 6-10, against paper+Opus scoring the same cells correctly
    through the Read tool. Reporting that as 5/17 would publish a missing tool as
    a model deficiency.

    Excluded from the RATE and reported as not comparable — a different thing
    from cell_exclusions(), which drops individual cells of an item that is
    otherwise fine.
    """
    if supports_tools:
        return {}
    return {
        it["id"]: ("needs an image tool to read the student's graph; this backend "
                   "sends no tools, so the item scores blind and returns 'no graph'")
        for it in config(handout)["rubric"].ITEMS
        if it.get("graph_item")
    }


# ── Scores gold asks for that the item cannot produce ────────────────────────

def attainable_scores(item: dict) -> list[float]:
    """Every score this item can actually produce.

    A score is max minus the sum of some subset of the scorable components,
    clamped at 0, plus 0 itself where a gate can take the whole item. Computed
    from the rubric rather than listed, so an item whose point values change
    cannot leave a stale table behind.
    """
    from itertools import combinations
    pts = [c["pts"] for c in item["credit"]
           if not c.get("reported") and c.get("pts") is not None]
    out = {float(item["max"])}
    for r in range(1, len(pts) + 1):
        for combo in combinations(pts, r):
            out.add(max(0.0, round(item["max"] - sum(combo), 4)))
    if any(c.get("gates") for c in item["credit"]):
        out.add(0.0)
    return sorted(out)


def nearest_attainable(item: dict, gold: float) -> set[float]:
    """The reachable score(s) closest to `gold` — the whole tie, if it is one.

    Empty when gold is itself reachable, which is the ordinary case: only one
    cell in the corpus is not (Q6 p4, whose 6.00 implies 3.2 slots of 1.25).
    """
    scores = attainable_scores(item)
    if any(abs(gold - a) < 1e-9 for a in scores):
        return set()
    best = min(abs(gold - a) for a in scores)
    return {a for a in scores if abs(abs(gold - a) - best) < 1e-9}


def scores_as_exact(item: dict, gold: float, pred: float) -> bool:
    """Does `pred` count as exact against `gold`?

    Normally that means equality. But where gold names a score the item CANNOT
    produce, the closest reachable value is the best any correct scorer can do,
    and penalising it measures the rubric's arithmetic rather than the scorer's
    judgement. Q6 p4 asks for 6.00 from an item that moves in steps of 1.25; a
    scorer returning 6.25 has done everything right.

    Deliberately not a tolerance. Only an UNREACHABLE gold opens the allowance,
    and only to the nearest reachable value(s) — a cell whose gold is reachable
    is still judged on equality, so this cannot quietly forgive a near miss.
    """
    if abs(pred - gold) < 1e-9:
        return True
    return pred in nearest_attainable(item, gold)
