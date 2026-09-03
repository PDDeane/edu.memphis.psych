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
    ("1a", 11): {
        "was": 8.0, "score": 6.0,
        "why":
            "one of the four weeks is undiscussed ON EITHER READING of the "
            "response, so 8.00 is unsupportable whichever way it is read, and "
            "that robustness is the whole argument. The item's rule is to discuss "
            "the data for each week. p11 writes \"Before {{corpus:1a/p11:response:126:150:sha=58f90d956d21:shape=R24-0-20}}"
            "{{corpus:1a/p11:response:151:219:sha=a4d658a95741:shape=R52-5-5457494345,R58-1-41,R60-4-5745454b,R65-3-464f5220}}"
            "{{corpus:1a/p11:response:220:232:sha=8c9fbcde23f1:shape=Cf7b}} TIME\", then discusses week two and week three by name "
            "and correctly. But the baseline data is 0,30,0,0,30,0,30 -- three "
            "sessions of thirty minutes -- while WEEK 1 is 0-60,0,0,0,0,0-60: "
            "twice, an hour each, exactly. So either the baseline sentence is "
            "about the baseline and WEEK 1 is missing, or it reports week 1's "
            "numbers under a baseline label and the BASELINE is missing. Both "
            "readings cost one week. Both give 6.00. "
            "TWO SOURCES, the D2/p11 standard. The item's rule is a per-week "
            "presence check, four weeks against eight points, so one missing week "
            "is 2. And the graders' practice on this very item charges exactly "
            "that: p6 is \"-2 pts: did not have a sentece pertaining to the "
            "baseline week\", landing on 6.00 for one missing week. Same item, "
            "same defect, same amount. "
            "OUR SCORE IS RIGHT AND OUR SLOT MAY NOT BE, which is recorded here "
            "rather than left for someone to find. We fail `week_1` in all twelve "
            "pooled runs, unanimously on both engines -- that is the label "
            "reading. Under the data reading the correct slot is `baseline_week`. "
            "The correction is to the SCORE, which both readings agree on; which "
            "week is actually missing is a separate live question and belongs to "
            "the subgoal that owns 1a's week-presence rule. Do not cite this cell "
            "as evidence that `week_1` specifically is judged correctly. "
            "AN EARLIER PASS DECLINED THIS CORRECTION, and the reason it was wrong "
            "is worth keeping. The argument against was that p11's only comparator "
            "is p6, and p6 is SIMULTANEOUSLY one of our own misses -- gold charged "
            "it and we credit 8.00 in 11 of 12 runs -- so the pattern looked like "
            "mutual carelessness rather than a gold outlier. That reasoning was "
            "made from a summary of the response instead of the response. Reading "
            "it out showed the two-reading structure above, which does not depend "
            "on the comparator at all: no reading of p11 discusses four weeks. p6 "
            "remains a real error OF OURS and is now owned as one. "
            "STATED AGAINST ITSELF: the correction GAINS us the cell, and the "
            "asymmetry recorded in the DAY1/p1 entry applies -- this readout can "
            "produce no candidate that would not. What carries it is that gold's "
            "own p6 charge fixes the amount, and that both readings of the "
            "response agree on it.",
    },
    ("DAY1", 1): {
        "was": 4.0, "score": 0.0,
        "why":
            "the example contradicts the definition the STUDENT THEMSELF wrote "
            "two boxes earlier, so this needs no reading of intent at all. They "
            "chose Positive Reinforcement and defined it: \"I {{corpus:D1/p1:d1:2:19:sha=3d91e26d23c3:shape=R17-0-20}}"
            "{{corpus:D1/p1:d1:20:83:sha=187e742405e5:shape=R24-6-414444494e47,R31-17-534f4d455448494e472044455349524544,R63-0-20}}"
            "{{corpus:D1/p1:d1:84:95:sha=7a24cb8a766d}} behavior.\" Their example is \"{{corpus:DAY1/p1:day1:0:25:sha=082e912927ab:shape=R25-0-20}}"
            "{{corpus:DAY1/p1:day1:26:65:sha=4ee225a7f0ea:shape=S5-20}} daily\" -- which REMOVES an "
            "aversive, the opposite operation, and names no contingency: \"daily\", "
            "not \"{{corpus:NR/p2:nr:0:17:sha=bd6ad50ff8db:shape=C1}}\". Both defects are stated on the page. "
            "TWO SOURCES, the D2/p11 standard, and both of gold's own comments "
            "spell out the rules p1 breaks. p6, charged to 0.00: \"Remember that "
            "what you take away or add has to happen AFTER THE BEHAVIOR IS "
            "EXHIBITED\" -- p1's reward is daily and follows nothing. p8, charged "
            "to 0.00: \"This is not an example of operant conditioning. For PP, "
            "you should state what undesirable [consequence]...\" -- that is the "
            "example-does-not-match-the-chosen-type charge, which is p1's other "
            "defect exactly. "
            "THE CONTROL SET IS THE WHOLE ITEM AND IT IS UNANIMOUS. Gold charged "
            "seven DAY1 cells to 0.00 -- p6, p8, p9, p13, p14 with substantive "
            "comments and p10, p18 as non-answers -- and OUR SCORER SCORES 0.00 "
            "ON ALL SEVEN. There is not one cell on this item where gold charged "
            "and we credited, so DAY1 contributes nothing to the mirror direction "
            "described below. Against that, p1 is the single row where gold "
            "awarded the maximum in silence, and we refuse it in all twelve "
            "pooled runs, failing `consequence_asserted` 12 of 12 unanimously "
            "across both engines. "
            "STATED AGAINST ITSELF: the correction GAINS us the cell, and this "
            "table's preamble warns that the reason to make a correction is the "
            "standard and never the score. THAT WARNING CANNOT DO ITS JOB HERE "
            "AND THE REASON IS WORTH WRITING DOWN. The readout that finds these "
            "cells, `measured.silent_full_marks_we_refuse`, only ever examines "
            "cells where gold is silent AND we refuse, so EVERY candidate it can "
            "possibly produce would gain us a cell if corrected. The fact carries "
            "no information and cannot discriminate. What can: whether gold "
            "charged the same defect elsewhere on the same item, and whether our "
            "scorer AGREES WITH GOLD on those cells. Here it is seven for seven. "
            "The measured counterweight, for scale: across the corpus 16 cells "
            "have gold charging where we credit more, against 15 where we score "
            "below gold. Disagreement is very nearly symmetric, so no general "
            "claim that the raters were careless is available -- only the "
            "item-level comparator argument above.",
    },
    ("NR", 20): {
        "was": 4.0, "score": 0.0,
        "why":
            "what is removed is a FEELING, not an outside stimulus the student "
            "arranges, and the student says so in their own summary sentence. The "
            "answer is \"If {{corpus:NR/p20:nr:3:54:sha=33d7962a0412:shape=R51-0-20}}"
            "{{corpus:NR/p20:nr:55:121:sha=adfeedddf330:shape=R44-7-454d4f56494e47,R52-3-544845,R56-7-4645454c494e47,R64-2-4f4620}}"
            "{{corpus:NR/p20:nr:122:172:sha=85ae0ce5d696:shape=C1ff}} sleep.\" Negative "
            "reinforcement requires that the thing withdrawn be an external "
            "stimulus under the student's control; tiredness lifts by itself once "
            "they sleep, so nobody arranges its removal. We fail the "
            "`you_arrange_it` gate in all twelve pooled runs, unanimously on both "
            "engines, and a failed gate takes the item to 0.00. "
            "THE COMPARATOR IS p1, ON THIS ITEM, AND IT IS NEARLY THE SAME "
            "SENTENCE. p1 answers \"If {{corpus:NR/p1:nr:3:32:sha=f6f8c75bcf69}} tired\" and "
            "gold charged it to 0.00 with the rule written out: \"Rememeber that "
            "what you take away after your wanted goal behavior has to be EASILY "
            "CONTROLLED BY YOU and be an OUTSIDE STIMULUS.\" Same item, same "
            "removed thing, same defect, and we score p1 at 0.00 too -- agreeing "
            "with gold. p20 is p1 with an explanatory sentence attached, and the "
            "explanation makes the defect MORE explicit rather than less. "
            "THE ONE READING THAT COULD SAVE IT, considered and rejected: \"not "
            "have to take naps\" could be called a controllable outside "
            "consequence, since napping is a behaviour the student performs. It "
            "does not save the cell, because the student's own closing sentence "
            "identifies what is being removed -- \"the feeling of tiredness\" -- "
            "and because not needing a nap is a downstream effect of having slept, "
            "not an arrangement. This is the same shape as Q4a/p19: where the "
            "response states its own causal direction, that statement governs. "
            "STATED AGAINST ITSELF: the correction GAINS us the cell, and the "
            "asymmetry recorded in the DAY1/p1 entry above applies here in full "
            "-- this readout can produce no candidate that would not gain us a "
            "cell, so that fact discriminates nothing. Two things carry it "
            "instead. Gold's own comment on p1 states the rule p20 breaks, and we "
            "agree with gold on p1. And subgoal Q34 had already read this cell "
            "out independently, before any comparator was in hand, and concluded "
            "that everything is `met` except `you_arrange_it` and that \"not "
            "feeling tired is a natural consequence the student does not arrange, "
            "which is what that gate asks\". "
            "A RETRACTION BELONGS HERE. This cell was first reported as splitting "
            "between the engines -- olx charging scored slots, python failing the "
            "gate. That was false, and it was an artifact of "
            "`measured._our_failing_slots` reading a NULL verdict as a failure "
            "when null means the slot was never asked. Both engines answer "
            "`you_arrange_it` absent in all twelve runs. The two sides are pooled "
            "because they are the same program on the same model, so a difference "
            "between them is never a premise.",
    },
    ("Q4a", 19): {
        "was": 5.0, "score": 3.0,
        "why":
            "box 1 is a CONSEQUENCE of the UTB and the item asks for antecedents, "
            "and the student's own words settle the direction. p19's UTB is \"lack "
            "of sleep\"; box 1 reads \"{{corpus:Q4a/p19:first:0:40:sha=58375fafed4a:shape=R40-0-20}}"
            "{{corpus:Q4a/p19:first:41:48:sha=1e8abffb973c}} motivated\", while their Q1 says \"Not {{corpus:Q1/p19:response:50:70:sha=344a5f4af0a7:shape=R20-0-20}}"
            "{{corpus:Q1/p19:response:71:94:sha=62f27dc64a74}} unmotivated\". So the response itself states "
            "that {{corpus:Q1/p20:response:0:17:sha=a7b4edcc777c}} causes the lack of motivation, which is the "
            "opposite of the relation Q4a asks for. This needs no reading of "
            "intent -- it is the student's own causal claim, quoted back. "
            "TWO SOURCES, the D2/p11 standard. Gold's own comments state the rule: "
            "p9 and p20 both spell out that \"an antecedent/trigger is something "
            "that causes you to engage in the UTB\". And the graders' practice on "
            "this item charges exactly this slot, at exactly this amount: p4 "
            "(\"how does grumpy emotions lead to lack of sleep?\") and p6 (\"how "
            "does not stretching lead to lack of exercise?\") are both -2 on box "
            "1, both land on 3.00, and OUR SCORER AGREES WITH GOLD EXACTLY ON "
            "BOTH. Those two defects are WEAKER than p19's: their boxes plausibly "
            "precede the UTB and merely fail to explain how. p19's does not "
            "precede it at all. "
            "THE SAME-UTB COMPARATOR IS p20, and it is the strongest of them. p20 "
            "also answers on \"lack of sleep\", and both its boxes run in the "
            "consequence direction -- \"i {{corpus:Q4a/p20:first:25:59:sha=eba6c9aecdf7:shape=R34-0-20}}"
            "{{corpus:Q4a/p20:first:60:81:sha=2e07aeae757e}} lazy\" and \"waking {{corpus:Q4a/p20:second:28:50:sha=86cdd47c358a:shape=R22-0-20}}"
            "{{corpus:Q4a/p20:second:51:103:sha=1bf773b2a1fd}} forgotten\". "
            "Gold charged it -4, both boxes, with the rule written out. Same item, "
            "same UTB, same error, and the row that states it explicitly was "
            "charged double while p19 was passed in silence. "
            "WHY 3.00 AND NOT 1.00, which is the test that this correction is set "
            "by the standard rather than by what helps us. Applied strictly, "
            "p20's precedent charges BOTH of p19's boxes and gives 1.00 -- and "
            "1.00 would leave this cell WRONG, since we score 3.00. It is not "
            "proposed, for a substantive reason: p20's box 2 states its direction "
            "outright (\"by {{corpus:Q4a/p20:second:72:103:sha=68ba6541d719}} forgotten\"), whereas "
            "p19's box 2, \"{{corpus:Q4a/p19:second:21:72:sha=35b0f73327de}} "
            "day\", supports a legitimate forward reading -- forget the work, do "
            "it late, lose sleep -- and Q4a's own guidance instructs \"ACCEPT "
            "generously when the example precedes the UTB and a reader can see how "
            "it leads there\". So box 1 is charged because the student stated the "
            "direction, box 2 is credited on the generous reading the prompt asks "
            "for, and 3.00 is where the standard lands. Note what follows: p19's "
            "one recorded run at 1.00 is the p20-STRICT score, not the noise "
            "subgoal Q34 read it as. "
            "STATED AGAINST ITSELF: the correction GAINS us the cell, and this "
            "table's preamble warns that the reason to make a correction is the "
            "standard and never the score. Two things answer that here. The "
            "strict reading of the same precedent gives 1.00 and does NOT gain us "
            "the cell, and it was set aside on the prompt's own generosity "
            "instruction rather than on the total. And the item's control set is "
            "as strong as it gets: our scorer and gold agree on 18 of Q4a's 20 "
            "cells, including every cell where gold charged box 1, so p19 is one "
            "of two exceptions rather than a lucky pick from a noisy item. "
            "FOUND BY `measured.silent_full_marks_we_refuse` plus the slot-level "
            "read of the whole item, not by hand. Q4a has no suspect cells, so "
            "every comparator above is a counted one.",
    },
    ("Q3", 8): {
        "was": 4.0, "score": 3.0,
        "why": "the comment carries TWO explicit \"-1 pt\" markers -- measurable (\"how "
               "will you track your goal?\") and actionable (\"what specific actions will "
               "you take?\") -- against a max of 5, which implies 3.00; the row wrote "
               "4.00. THE CONTROL SET IS THE WHOLE ITEM. Q3 has five 1-point criteria, "
               "and every other row's arithmetic follows exactly: one itemised deduction "
               "scores 4 (p1, p17, p18), two score 3 (p3, p6, p7, p10, p13, p16, p19), "
               "three score 2 (p9, p20), none scores 5 (p2, p4, p5, p11, p12, p14, p15). "
               "p19 is the exact control -- the SAME pair, measurable and action -- and "
               "scores 3. p8 is the only row in twenty where the sum does not match. "
               "The submission supports both deductions: \"I {{corpus:Q3/p8:measurable:47:74:sha=1953a79ffdab:shape=R27-0-20}}"
               "{{corpus:Q3/p8:measurable:75:81:sha=866ab23f0299}} gym\" names no method, and \"This {{corpus:Q3/p8:action:33:64:sha=37e96844d3a4:shape=R31-0-20}}"
               "{{corpus:Q3/p8:action:65:77:sha=d31a15770b5a}} time\" describes achievability rather than any action. A "
               "SLIP, not an unwritten deduction -- the grader wrote both charges and "
               "subtracted one. THE CORRECTION COSTS US THE CELL: we score 4.00, which "
               "matched the uncorrected row 3/3, and against 3.00 we are now wrong. It "
               "makes gold coherent; it does not move our number.",
    },
    ("Q4a", 17): {
        "was": 4.0, "score": 5.0,
        "why": "the row docks the keyword point -- \'-1 pt: did not use the word "
               "\"antecedent\" or \"trigger\"\' -- and is INTERNALLY COHERENT, which "
               "makes this correction different in kind from the others here: the ground "
               "is not the row\'s own arithmetic but its inconsistency with every "
               "comparable row. COUNTED ACROSS ALL THREE HANDOUTS, seven responses omit a "
               "required course term and the graders charged ONE. Q4a p9, p15 and p17 "
               "omit antecedent/trigger; only p17 was charged. Q4c p9, p13, p15 and p17 "
               "omit consequence; none was charged, which is why Q4c\'s keyword already "
               "carries no points. p15 is p17\'s structural twin -- two antecedents gold "
               "accepted, no keyword, nothing else at fault -- and kept the point. The "
               "same two students present four opportunities between them: three waived, "
               "one charged. The check is purely lexical (two words, anywhere, once), so "
               "there is no gradation in it a grader could have been grading, and nothing "
               "in the responses separates p17 from p15. THE ARITHMETIC MATTERS TOO: with "
               "the keyword not charged, Q4a can produce {0,1,3,5} and 4.00 is "
               "unreachable, so leaving the row at 4.00 would have had the unreachable-"
               "gold allowance forgive our 5.00 -- a tolerance where the unreachability "
               "was OURS. Corrected, every gold value in the item is attainable, no "
               "allowance fires anywhere in the corpus outside Q6/p4 and 1c/p11, and no "
               "divergence is needed. We score 5.00 and the corrected row is 5.00.",
    },
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
    # DAY2/p7 and WK1/p7, both 1.00 -> 3.00, found by generalising ("D2", 11)
    # below: when a grader itemises their arithmetic, the itemisation can be
    # checked against the score.
    #
    # Every OTHER itemised row in the four example items reconciles exactly —
    # seven rows of "-4 pts: This example is not Operant Conditioning" landing on
    # 0.00, four rows of "-2 pts: This is an example of PP/NP" landing on 2.00.
    # Nine for nine. The only two that do not are these, both "-1 pt", both
    # landing on 1.00 where the comment implies 3.00, both written by the same
    # grader on the same student. Against a nine-row control set the itemisation
    # is the reliable half and the score field is the slip.
    #
    # The deduction each comment describes is WRONG_BEHAVIOR, which our own
    # dictionary charges at exactly 1.0 — "The behavior you target in this
    # example is not your chosen behavior." p7's daily example rewards reading a
    # chapter, and their UTB is screen time; their weekly example is correctly NP
    # ("This is an example of NP" AFFIRMS the type) but again targets the wrong
    # behaviour. So gold's comments and our dictionary agree to the point, and
    # only the two score fields disagree with both.
    #
    # This correction gains us NOTHING, which is why it is safe to make: we score
    # 4.00 on both cells and are still wrong at 3.00. What it changes is the
    # diagnosis. Both cells were declared under GOLD_CEILINGS ('2','DAY2') as
    # gold that no scorer charging the stated deduction could reach — true of the
    # row as written, and it made an unreachable target out of what is really a
    # live bug: WRONG_BEHAVIOR never fires on either cell. Correcting the rows
    # turns two declared-unreachable cells into two cells we miss for a reason,
    # which is worth more than the ceiling was.
    ("DAY2", 7): {
        "was": 1.0, "score": 3.0,
        "why": "comment itemises \"-1 pt\" against a max of 4, which implies "
               "3.00; the row wrote 1.00. The deduction described is "
               "WRONG_BEHAVIOR (their example targets reading a chapter, their "
               "UTB is screen time), which our dictionary also charges at 1.0. "
               "Nine other itemised rows in these items reconcile exactly. We "
               "score 4.00 and remain wrong at 3.00 — the correction makes gold "
               "coherent, it does not move our number.",
    },
    ("WK1", 7): {
        "was": 1.0, "score": 3.0,
        "why": "same shape as (\"DAY2\", 7), same student, same grader. \"-1 pt: "
               "This is an example of NP, however your UTB is not "
               "procrastination\" — the first clause AFFIRMS the type (p7's first "
               "type IS NP), so the only deduction described is WRONG_BEHAVIOR at "
               "1.0, implying 3.00 against the 1.00 written. Was read as a "
               "concealed TYPE_MISMATCH (2.0 + 1.0 = the 1.00 gold wrote) until "
               "the type was checked; it is not.",
    },
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
    ("NR", 4): {
        "was": 4.0, "score": 2.0,
        "why":
            "the answer is NEGATIVE PUNISHMENT and the item asks for negative "
            "reinforcement. \"I {{corpus:NR/p4:nr:2:50:sha=988f89687cbc:shape=R48-0-20}}"
            "{{corpus:NR/p4:nr:51:58:sha=ba240b73251f}} hours\" withdraws something DESIRABLE when the behaviour "
            "FAILS; negative reinforcement removes something AVERSIVE when it "
            "succeeds. TWO SOURCES, the D2/p11 standard. The dictionary: "
            "WRONG_TYPE (-2), \"This is not Negative Reinforcement\", which on a "
            "max of 4 gives 2.00. "
            "THE DECISIVE COMPARATOR IS p9, on this same item. It answers "
            "\"if {{corpus:NR/p9:nr:56:119:sha=39f9f1a28880:shape=R63-0-20}}"
            "{{corpus:NR/p9:nr:7:9:sha=663ea1bfffe5}} eat\" -- also a consequence applied when the behaviour FAILS -- "
            "and the graders charged it: \"-2 pts: This is an example of PP\", "
            "landing on 2.00. That is the same item, the same structural error "
            "(the student described a different quadrant), the same charge, and "
            "the SAME SCORE this correction assigns p4. The only difference is "
            "which wrong quadrant was named: PP for p9, NP for p4. Gold charged "
            "one and was silent on the other. "
            "THE GRADERS ARE NOT BLANKET-CREDITING failure-contingent answers, "
            "which is what would otherwise explain p4's 4.00. Read across the "
            "four operant-type items, they credit that form exactly where it is "
            "the CORRECT form -- on PP (p1, p4, p5, p9, p17) and on NP (p4, p5, "
            "p6, p8, p12, p19), where the consequence belongs on failure -- and "
            "they charged it on NR, at p9. That is a coherent system applied "
            "consistently, and p4 is the single row inconsistent with it. "
            "THE OUTLIER TEST agrees: every other silent full-marks row on this "
            "item has the form \"if I DO the wanted behaviour, something aversive "
            "is removed\" -- all NINE of them, p5, p6, p7, p8, p12, p17, p18, p19 "
            "and p20. p4 is the only one phrased on FAILING. (p5 was missing from "
            "this list until `measured.silent_full_marks_we_refuse` was written "
            "and the rows were read out again. The list was assembled by hand and "
            "the omission changed nothing, but an outlier argument is only as good "
            "as the completeness of the set it calls p4 an outlier OF.) "
            "2.00 IS THE LENIENT END OF GOLD'S OWN RANGE for this defect, which "
            "matters because a correction that invented a harsher charge than the "
            "graders use would be the table overreaching. Where an NR comment "
            "says the example is the wrong type, gold lands on 2.00 four times "
            "(p9, p11, p14, p15) and on 0.00 twice (p13, p16). The correction "
            "takes the majority treatment and the more generous of the two. "
            "STATED AGAINST ITSELF: the correction GAINS us the cell. We score "
            "2.00, so this cell moves from wrong to right, and this table's "
            "preamble warns that the reason to make a correction is the standard "
            "and never the score. The standard here is the dictionary plus p9; "
            "the gain is a consequence, not the ground. No item total is quoted "
            "here on purpose: a rate drifts as prompts change and this sentence "
            "would not, which is the failure "
            "`check_prose_numbers_match_the_ledger` exists to catch -- it caught "
            "the first draft of this line. "
            "NO SUSPECT CELL IS CITED ABOVE, and an earlier draft of this entry "
            "did cite two: it argued from p2 and p3 -- byte-identical answers "
            "with opposite gold rows -- as evidence that this item's gold is "
            "incoherent, when both are EXCLUDED as suspect precisely because "
            "identical transcriptions with different gold rows mean at least one "
            "is MIS-TRANSCRIBED, making them untrustworthy INPUT that is evidence "
            "for nothing in either direction. `enforcement."
            "check_no_declaration_cites_a_suspect_cell` now enforces that.",
    },
    ("Q6", 4): {
        "was": 6.0, "score": 6.25,
        "why":
            "the comment charges \"-1.5; missing one antecedent\" and Q6 HAS NO "
            "1.5 DEDUCTION. Every antecedent code in the item's dictionary is "
            "1.25 -- A_NOT_STATED (\"Did not state the antecedent from question "
            "4a that is being changed\"), A_MISMATCH, A_NO_CHANGE -- and "
            "A_NOT_STATED is this defect verbatim. Every other Q6 comment in the "
            "corpus charges an antecedent miss at 1.25. Two independent sources, "
            "which is the D2/p11 standard: the dictionary and the same defect's "
            "treatment elsewhere. "
            "THE TOTAL IS CORRECTED WITH IT. The row as written reconciles -- 6.0 "
            "= 10 - 2.5 - 1.5 -- so this is not a row contradicting itself; the "
            "grader applied an amount the item does not have and then totalled it "
            "faithfully. Correcting the deduction alone would break the "
            "arithmetic, so both move: 10 - 2.5 - 1.25 = 6.25. "
            "AND 6.0 IS NOT REACHABLE ON THIS ITEM, which is the strongest "
            "evidence and is independent of both the dictionary and our scoring. "
            "Q6 is eight slots at 1.25, so every attainable total is a multiple "
            "of 1.25: 0, 1.25, 2.5, 3.75, 5.0, 6.25, 7.5, 8.75, 10. The 1.5 put "
            "gold OFF the item's own grid; 6.25 is on it. "
            "IT BUYS NO CELL, checked before filing. The unreachable-gold "
            "allowance already made 6.25-against-6.0 count as exact, so p4 was "
            "scored correct before this and is scored correct after: Q6 stays "
            "17/20 cli and 18/20 web. What changes is the strict direction "
            "profile -- 16 fewer false over-credit observations across the two "
            "sides -- and that gold no longer needs the allowance here. The "
            "flattering direction was the reason to check, not a reason to "
            "refuse; compare CORRECTED_GOLD[(\"Q6\", 9)], where the rate DID "
            "rise \"because a cell we score correctly finally counted\". "
            "CORROBORATION, not the basis: we fail exactly ONE antecedent slot on "
            "p4, state_a1, stably in 6 of 6 runs -- the shape a single 1.25 "
            "antecedent charge describes. It does not tell us WHICH antecedent "
            "the grader meant, so p4 stays in measured.GOLD_SLOT_UNMAPPABLE for "
            "the slot comparison; what is settled here is the AMOUNT.",
    },
    ("Q6", 9): {
        "was": 5.0, "score": 3.75,
        "why":
            "gold credits `state_a1`, which names a THIRD antecedent p9 never "
            "listed. Their 4a gives \"{{corpus:Q4a/p9:first:0:45:sha=61a3572fe501:shape=R45-0-20}}"
            "{{corpus:Q4a/p9:first:46:57:sha=c8721314956d}} gym\" and \"Not {{corpus:Q4a/p9:second:4:47:sha=51aa08720e1c:shape=R43-0-20}}"
            "{{corpus:Q4a/p9:second:48:64:sha=98c7d83be08c}} easily\"; Q6 says \"my {{corpus:Q6/p9:state_a1:24:56:sha=1569107a8807:shape=R32-0-20}}"
            "{{corpus:Q6/p9:state_a1:57:83:sha=f115e31bd80e}} show\". Watching a movie in bed appears in "
            "neither entry, so the box names an antecedent that is not on the list "
            "at all -- not a reworded one, which is the distinction this item's own "
            "rule turns on. The scoring dictionary is explicit that the antecedents "
            "must match up, and the lo-blocks prompt returned a mismatch in five "
            "runs of five. "
            "THE EVIDENCE CITED HERE WAS WRONG UNTIL 2026-08-19, and the way it was "
            "wrong is worth keeping. It quoted p9's 4a as \"wanting {{corpus:Q4a/p8:first:30:44:sha=c662a8e2ce0f:shape=R14-0-20}}"
            "{{corpus:Q4a/p8:first:45:58:sha=99f7dbdeb779}} gym\" and \"{{corpus:Q4a/p8:second:26:60:sha=b6dda568cd34}} any "
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
               "lazy and am not productive\"; Q6 says \"my {{corpus:Q6/p17:state_c1:32:54:sha=e4c2d3c739bb:shape=R22-0-20}}"
               "{{corpus:Q6/p17:state_c1:55:93:sha=57f42152d2a2}} enough\". Weight gain LEADS "
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
               "{{corpus:Q4c/p19:second:0:25:sha=d4d526f38996:shape=C1}} being affected\", we agree with and "
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
            # "{{corpus:Q4a/p3:second:25:67:sha=5c4b20801855}}" do-instead example, gold's
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
        "code": "GARBLED_CLAUSE_READ_LITERALLY",
        "cells": [("Q1", 9)],
        "why": "The cell turns on ONE ungrammatical clause whose literal sense is the "
               "opposite of what the student meant, and both readings are defensible. "
               "THE TEXT: \"I {{corpus:Q1/p9:response:151:208:sha=a25ae64edefd:shape=R57-0-20}}"
               "{{corpus:Q1/p9:response:209:278:sha=1e08e9034878}}\" "
               "Read literally it says exercising will HAVE unwanted complications; gold "
               "reads the intended \"avoid having\". "
               "WHY IT DECIDES THE CELL: gold counts p9 as offering NO harms and two "
               "benefits (free time, health), so the two-tier rule falls through to "
               "`benefits_listed` = 2 and scores 4. When the model reads the clause as a "
               "harm, `harms_listed` = 1, tier one applies, and the cell scores 3. Its "
               "`benefits_listed` is a stable 2 in every run measured; nothing else in "
               "the cell moves. "
               "MEASURED ACROSS TWELVE CONFIGURATIONS, rates in order: 1/6, 3/6, 6/6, "
               "3/6, 4/6, 2/6, 1/6, 1/6, 4/6, 4/6, 3/6, 1/6. The single 6/6 came from a "
               "prompt that cost p7 four of six runs, and three probes built to isolate "
               "what produced it (the sentence-unit instruction alone, that instruction "
               "with `count DISTINCT CONTENT`, and making the and-joined split "
               "conditional) each scored p9 WORSE than the baseline they were derived "
               "from -- 2/6, 1/6, 1/6. "
               "ROUTES CLOSED, each measured, none free: a mirror-pair rule at four "
               "lengths (v2 759 chars, v3 508, v4 560, v5 600); the same criterion inside "
               "the aggregate rule (2/6); splitting the counted family so each reason is "
               "judged on its own (4/6, and the item swept 16); and an "
               "assertion-versus-avoidance clause on `harms_listed` written for exactly "
               "this shape -- a bad outcome named only as something the goal behaviour "
               "would spare the student is not a negative effect -- which left the clause "
               "quoted as a harm in 5 of 6 runs, took p9 to 1/6, and cost p14 and p6 a "
               "run each. "
               "The prior record predicted this before the work started: \"its text is "
               "garbled enough that the reading is defensible\". While this cell "
               "stands the item cannot exceed nineteen of its twenty cells; it records "
               "18/20, the other miss being p10's goal restatement, which the model "
               "excludes correctly in some runs.",
    },
    {
        "code": "ANTECEDENT_RULE_APPLIED_AGAINST_ITSELF",
        # Q4a/p19 LEFT THIS ENTRY 2026-09-03: it is in CORRECTED_GOLD, and a cell
        # cannot be both corrected and declared. p14 remains, and note that the
        # "OPPOSITE directions" this entry is built on now has only one side of
        # the pair left in it -- read the why below with that in mind.
        "cells": [("Q4a", 14)],
        "why": "Two cells, deterministic at 0/6 each, where gold departs from the rule "
               "gold itself states -- in OPPOSITE directions, which is why no single "
               "criterion reaches both. "
               "THE RULE, in the graders' own words on three other rows of this item: "
               "p3 is docked \"Need further explanation for how not eating is an "
               "antecedent of lack of exercise\"; p4 \"how does grumpy emotions lead to "
               "lack of sleep?\"; p20 \"An antecedent/trigger is something that causes "
               "you to engage in the UTB\". All three demand that the example show how "
               "it leads to THE UTB, and we score all three exactly right, 6/6 each. "
               "p14 (gold 1, we score 3): \"{{corpus:Q4a/p14:first:20:62:sha=6aa43933fa47:shape=R42-0-20}}"
               "{{corpus:Q4a/p14:first:63:66:sha=c5052532c220}} rot\" STATES that link and names the UTB as its effect -- bed-rotting "
               "{{corpus:Q1/p10:response:29:48:sha=36c47ef0c375}} -- so by the rule above it qualifies, and our "
               "`antecedent_1` reads `met` 6/6. Gold rejected both examples for -4. "
               "p19 (gold 5, we score 3): \"{{corpus:Q4a/p19:first:23:58:sha=ca9d4ea70d5d:shape=S4-20}}\" states "
               "NO link at all, which is what p3 was docked two points for, and our "
               "`antecedent_1` reads `wrong_kind` 6/6. Gold credited it in full with no "
               "feedback. "
               "MEASURED, NOT ASSUMED, and the routes are closed. (1) EQUIVALENCE_DEF was "
               "imported to make the stated effect have to BE the UTB by semantic "
               "equivalence -- six runs, seven cells: p14's `antecedent_1` stayed `met` "
               "6/6 and p9's `antecedent_2` flipped to `met` 5/6, net -0.67, reverted "
               "(see the note in rubric_h1 beside the Q4a guidance). (2) Crediting an "
               "unexplained state on the ground that these behaviours are CYCLICAL -- a "
               "state that follows one occurrence and precedes the next -- would reach "
               "p19, but p20's second example is the same shape (\"waking {{corpus:Q4a/p20:second:28:39:sha=397f8fcdc8bf:shape=R11-0-20}}"
               "{{corpus:Q4a/p20:second:40:60:sha=f6d8ac32f3ce}} school\" against lack of sleep) and gold REJECTS it; "
               "p20 is 6/6 correct at gold 1, and crediting both its examples would score "
               "it 5. One cell won, one worth four points lost. "
               "NOT FIXTURE FAULTS: both responses are complete and neither student is "
               "among handout 1's suspect submissions. NOT GOLD ERRORS: p14's row "
               "itemises -4 against a max of 5 and reconciles at 1; p19's carries no "
               "feedback, which is normal for full credit. Each is defensible read alone "
               "-- it is the PAIR that cannot both be right under one rule. Ours is the "
               "reading that follows the criterion the graders wrote down.",
    },
    # NP_SHAPE_CREDITED_AS_NR NAMED ("NR", 4) AND WAS REMOVED 2026-09-03. The cell is in
    # CORRECTED_GOLD, and the two tables make CONTRADICTORY claims: a correction
    # says gold's number was wrong against the graders' own practice, a
    # divergence says gold's number stands and we knowingly differ from a
    # coherent decision. It cannot be both. The correction is the treatment
    # kept, at the user's direction. Three of the five corrections made that day
    # landed on cells already declared here -- this one, NP_SHAPE_CREDITED_AS_NR on NR/p4 and BEHAVIOR_NEVER_STATED on DAY1/p1 -- because I
    # built each from comparator evidence without checking the declaration
    # tables first, and nothing caught it: the audit compares declarations
    # against RECORDED data, so while the ledger still held pre-correction
    # numbers "we knowingly miss this" stayed consistent with what was recorded.
    # enforcement.check_no_cell_is_both_corrected_and_declared now forbids the
    # overlap outright, with no run data needed.

    # BEHAVIOR_NEVER_STATED NAMED ("DAY1", 1) AND WAS REMOVED 2026-09-03. The cell is in
    # CORRECTED_GOLD, and the two tables make CONTRADICTORY claims: a correction
    # says gold's number was wrong against the graders' own practice, a
    # divergence says gold's number stands and we knowingly differ from a
    # coherent decision. It cannot be both. The correction is the treatment
    # kept, at the user's direction. Three of the five corrections made that day
    # landed on cells already declared here -- this one, NP_SHAPE_CREDITED_AS_NR on NR/p4 and BEHAVIOR_NEVER_STATED on DAY1/p1 -- because I
    # built each from comparator evidence without checking the declaration
    # tables first, and nothing caught it: the audit compares declarations
    # against RECORDED data, so while the ledger still held pre-correction
    # numbers "we knowingly miss this" stayed consistent with what was recorded.
    # enforcement.check_no_cell_is_both_corrected_and_declared now forbids the
    # overlap outright, with no run data needed.

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
        "why": "p4's first entry reads \"{{corpus:Q5/p4:first:0:40:sha=5adbcff99c0f:shape=R40-0-20}}"
               "{{corpus:Q5/p4:first:41:78:sha=dbee47176fe2}}\" — it names the OPPOSITE of "
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
            "antecedent is \"{{corpus:Q6/p8:state_a1:38:87:sha=2abb3dabb60a}}\" and "
            "the change is \"{{corpus:Q6/p8:change_a1:10:31:sha=59e2c4a3daa0}} from Tuesday-Friday\"; the second "
            "is \"staying {{corpus:Q6/p8:state_a2:39:93:sha=92366fb71e73}} gym\" "
            "and the change is \"{{corpus:Q6/p8:change_a2:9:52:sha=02595bb7f918}} week\". "
            "Read literally each change DOES negate the antecedent as the student "
            "framed it, because the student framed the antecedent as the absence of "
            "the goal behaviour. The graders applied the item's pedagogical point "
            "instead: an antecedent change alters what triggers the unwanted "
            "behaviour, it does not resolve to do the wanted one.\n\n"
            "Declared rather than chased because p6 is the same shape and gold "
            "CREDITS it. p6's antecedent is \"{{corpus:Q6/p6:state_a1:0:21:sha=641b355f6e09}} & {{corpus:Q6/p6:state_a2:4:17:sha=8fe41cf2d613:shape=R13-0-20}}"
            "{{corpus:Q6/p6:state_a2:18:35:sha=410129fe5640}}\" and its change is \"I {{corpus:Q6/p6:change_a1:14:40:sha=dda548773f8f:shape=R26-0-20}}"
            "{{corpus:Q6/p6:change_a1:41:88:sha=bd5bdfabcb36}} week\" — an absence-framed "
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
               "entry is \"I {{corpus:Q4b/p12:second:2:51:sha=f2201f319b22:shape=R49-0-20}}"
               "{{corpus:Q4b/p12:second:52:112:sha=eead74115ae9:shape=R60-0-20}}"
               "{{corpus:Q4b/p12:second:113:126:sha=b9ba0a5dbbd1}} bad\" — it names no activity that displaced the "
               "goal, which is what the question asks for, and `behavior_*`'s "
               "fifth test refuses it in terms. Gold gives 5.0. "
               "THE REASON THIS ENTRY USED TO GIVE WAS FALSE and is corrected "
               "here rather than deleted, because a declaration trusted for the "
               "wrong reason is worse than none. It said \"we give 3.5, 0 of 3\", "
               "which is true of the WEB path only, and not even there: across "
               "every artifact that measured this cell the web scores 3.5 in 11 "
               "of 12 runs (leak_fix 0/6, scorer_fix_6run 1/6 — one run at 5.0), "
               "while the CLI scores 5.0 in SIX of six (cli_v7 3/3, cli_v8 3/3). "
               "The cell is not unreachable; the two paths disagree about it. "
               "THAT ASYMMETRY IS NOT DECLARED ANYWHERE. It is absent from "
               "olx_prompts.SCORING_DIVERGENCES and the enforcement audit reports "
               "nothing for Q4b, because the rule doing the refusing lives in "
               "GUIDANCE PROSE — \"REJECT when the entry is not something the "
               "student did INSTEAD OF the goal behaviour\" — rather than in a "
               "primitive the audit can compare. A scoring-relevant rule enforced "
               "on one side only is exactly what that audit exists to catch, and "
               "it cannot see this one. "
               "The divergence itself STANDS: the web result differs from gold "
               "for the stated reason, and the test that refuses the entry was "
               "measured at +1 cell a run against deleting it. What changes is "
               "that the reason no longer claims we never match gold here.",
    },
    # A_NOT_ANTECEDENT NAMED "cells": [("Q4a", 19)] AND WAS REMOVED 2026-09-03. The cell is in
    # CORRECTED_GOLD, and the two tables make CONTRADICTORY claims: a correction
    # says gold's number was wrong against the graders' own practice, a
    # divergence says gold's number stands and we knowingly differ from a
    # coherent decision. It cannot be both. The correction is the treatment
    # kept, at the user's direction. Three of the five corrections made that day
    # landed on cells already declared here -- this one, NP_SHAPE_CREDITED_AS_NR on NR/p4 and BEHAVIOR_NEVER_STATED on DAY1/p1 -- because I
    # built each from comparator evidence without checking the declaration
    # tables first, and nothing caught it: the audit compares declarations
    # against RECORDED data, so while the ledger still held pre-correction
    # numbers "we knowingly miss this" stayed consistent with what was recorded.
    # enforcement.check_no_cell_is_both_corrected_and_declared now forbids the
    # overlap outright, with no run data needed.

    {
        "code": "A_NOT_ANTECEDENT", "cells": [("Q4a", 14)],
        "why": "gold refused both of p14's examples (-4 = two refusals) while its "
               "commentary accounts for only one, and the first — \"not seeing "
               "immediate results\" — is the state-of-mind case the item's own "
               "guidance says to accept. Credited in five runs of five.",
    },
    # ADDED_AVERSIVE_NAMED RETIRED IN FULL, 2026-08-24. It began the day covering
    # DAY1/p8, WK1/p8 and WK2/p8 under one rationale that fitted one of them, and
    # ends with no cells at all. Each left for a different and better reason:
    #
    #   WK2/p8  removed first — gold is RIGHT there and we were wrong, crediting a
    #           contingency that runs backwards (the chore arrives for SUCCESS).
    #           Not a disagreement to declare; a miss to count. See BACKLOG.md.
    #   DAY1/p8 fixed by making avoidance framing GATE on that item. Of the five
    #           DAY1 cells where that check answers `absent`, gold scores four of
    #           them 0, so honouring it cost nothing and gained the cell. 9 of 9.
    #   WK1/p8  fixed last, after eight attempts, by asking the grader for a PARSE
    #           instead of a judgement. The cue is syntactic: every gold-4 cell on
    #           the item puts an animate agent in subject position governing a verb
    #           that brings the thing about ("I will treat myself to a movie"),
    #           while p8 puts the PENALTY in subject position with an accumulation
    #           verb ("the press-ups will just keep stacking") — nobody imposes
    #           anything. 6 of 6 probed, controls holding, WK1 up from 15 to 17.
    #
    # The lesson those eight attempts bought, now in QUALITY_CONTROL.md: ask for a
    # PARSE, not a judgement. "Is a consequence delivered?" and "does this target
    # their own behaviour?" wobble, because they are questions about the PLAN.
    # "What is the subject of the consequence clause, and does its verb say a
    # person brings the thing about?" is a question about the SENTENCE, and does
    # not wobble.
    # WK2/p8 REMOVED from this entry 2026-08-24, and NOT declared anywhere else.
    # It was carried as a third instance of avoidance framing and is not that at
    # all: "{{corpus:WK2/p8:wk2:0:69:sha=873e2962dff1}}
    # week for 1 hour" puts the chore AFTER SUCCESS, so meeting the goal earns
    # yard work. Their daily answer for the same type is the correct inverse
    # ("...{{corpus:DAY2/p8:day2:39:82:sha=3333e8a83a54}}"), which is what makes the
    # weekly one a slip rather than a style. The submission was checked against
    # the source .docx line by line: the text is transcribed faithfully, no "not"
    # was lost, so there is nothing to fix in the fixture.
    #
    # Gold's 0 is therefore CORRECT and our 2 to 4 is a real over-credit: we
    # credit a contingency that runs backwards. It stays counted and wrong, with
    # the criterion gap recorded in BACKLOG.md, because a divergence on a cell we
    # simply get wrong is the thing section 5's rule was written to stop —
    # "we knowingly disagree" is the most flattering thing that can be said about
    # a miss short of dropping it.
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
        "which gold refuses in terms — \"{{corpus:Q6/p2:affect_c2:3:39:sha=7bc493d62ecd}} does "
        "not change your antecedent of {{corpus:Q6/p2:state_a2:31:69:sha=953a77829719:shape=R38-0-20}}"
        "{{corpus:Q6/p2:state_a2:70:74:sha=6c45cb72a36e}}\" — while both scorers credit it. "
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
        "{{corpus:Q6/p9:affect_c1:12:55:sha=4d22cd16d125:shape=R9-0-20,R10-1-6f}} health\" against a listed "
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
        "goals; its `state_c1` says the student {{corpus:Q6/p5:state_c1:91:123:sha=ae4f07a6cbe4:shape=R32-0-20}}"
        "{{corpus:Q6/p5:state_c1:124:156:sha=d238f0609a87}} foods, which is their own 4a antecedent. "
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
        "4c-1 reads \"worsening {{corpus:Q4c/p5:first:87:128:sha=754dd07fec1d:shape=Cc0000}} "
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
        "than by naming an action, and gold splits them — p14 (\"my {{corpus:Q3/p14:action:63:77:sha=e1ed3fd8af96:shape=R14-0-20}}"
        "{{corpus:Q3/p14:action:78:108:sha=6ffe1a32e5b6}} house\") and p18 (\"{{corpus:Q3/p18:action:64:84:sha=a23e8ae750f0:shape=R20-0-20}}"
        "{{corpus:Q3/p18:action:85:101:sha=0fddaf85b380}}\") are CREDITED, while p8 (\"I will be able to make time\"), "
        "p16 (\"{{corpus:Q3/p16:action:58:90:sha=d23f7525fb29}}\") and p20 (\"{{corpus:Q3/p20:action:80:97:sha=3664422a464d}} "
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
        "carries — with p13's \"{{corpus:Q3/p13:action:58:101:sha=0eb12399ea3c}}\" as "
        "the control that must keep its credit. Untried.",
    ),
    # ("2", "DAY2") RETIRED 2026-08-24. It read: p7's gold is 1.00 while its
    # comment itemises only "-1 pt", which implies 3.00, so 1.00 is unreachable
    # by any scorer that charges the stated deduction — and WK1 p7 is the same
    # shape. Both halves were correct about the ROWS and drew the wrong
    # conclusion from them. "Unreachable" was a statement about gold as written,
    # and the nine other itemised rows in these items reconcile exactly, which
    # makes the two score fields slips rather than a target we cannot hit. Both
    # rows are now in CORRECTED_GOLD at 3.00, and the cells remain misses,
    # because WRONG_BEHAVIOR — the 1.0 deduction both comments describe and our
    # own dictionary carries — never fires on either. A ceiling that says a cell
    # is unreachable ends the inquiry; the truth was a bug with two symptoms.
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
#   necessarily plotted — p11's `baseline` field holds "{{corpus:1a/p6:baseline:0:19:sha=66e4f9120272}} 30",
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
            "why": "gold 3.0 for \"did not say if {{corpus:Q4b/p15:modify:0:30:sha=431b4811e0ab:shape=R0-1-74,R30-0-20}}"
                   "{{corpus:Q4b/p15:modify:31:34:sha=10c22bcf4c76}} you modify and why\" — but the handout asks that under 4b, "
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
        # ("{{corpus:2a/p18:how1:0:68:sha=b61bccd5f38c}}
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
            "\"Title: {{corpus:1c/p20:title:0:27:sha=d794c8f137de}} X-axis label: Days (or "
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
