# Q6's matching ceiling

THE RECORD OF WHAT HAS BEEN TRIED ON Q6's `refers_to`, AND WHY A FIFTEENTH
ATTEMPT NEEDS AN ARGUMENT. Every attempt below was built, measured against a
baseline, and reverted. The point of keeping them is that the failures are not
interchangeable: several were sound about the text and failed on REACH, which
leaves nothing to read afterwards except that nothing happened.

This file is cited from `handouts.py`, `rubric_h1.py`, `olx_prompts.py`,
`measured.py`, `enforcement.py` and `GOALS.md`. It lives in the repository
because a pointer into one developer's notes is unreadable to everyone else.

Q6 asks which of 4a's two antecedents and
4c's two consequences each box refers to (`refers_to`), and **that channel is
where every remaining Q6 error lives.** FOURTEEN attempts have been built,
measured and reverted — ten wordings, **one schema change**, one reorder and
**two segmentation designs**. Do not propose a fifteenth without reading this,
and especially not without reading the eleventh, which is the only one that
removed the grader's room to dodge the question, and the fourteenth, which
tried to remove the ambiguity the flat response creates rather than judge it.

**What has been tried** (each measured against a 3-pass baseline, each reverted):
loose "improves the goal behaviour" (fixed p2, broke p3/p5); tight
object/occasion/supply (held p3/p5, lost p2); concrete "conditions of the
exercise" (held p3, lost p5); back-reference latitude scoped to `state_c1`
(netted zero AND leaked into antecedent slots — the trigger phrase sits in 22
antecedent boxes across 14 cells, so **scoping a rule to one slot family in the
NOTES does not scope its EFFECT**); the substitution test (held all three
refusals but refused p17 too, pass 1 = 12/19); and the **inversion rule**
(same attribute + flipped polarity → accept), withdrawn after pass 1 of 3 at
14/20 vs a 16/20 baseline, with two (A)-class cells regressing that the rule was
never scoped to touch.

**The eighth, 2026-08-25, and the first measured at 6 passes.** Q6's
`MATCH_DEF` was migrated onto `olx_prompts.EQUIVALENCE_DEF`, the shared
definition written for WK1 that day: equivalence is what negation and same-scale
antonyms establish when the reversals CANCEL in an even number. It replaced one
paragraph -- "That INCLUDES equivalence established by combinations of negations
and antonyms" (open-ended) with a closed construction -- and left Q6's ANTONYMS
paragraph, byte-identical in both, and its "X, so I Y" section untouched. +268
chars.

It went 18/20 to a 6-run median of **16/20**, totals [13, 14, 16, 16, 16, 17],
mean 15.3 against the baseline's 17.3, spread 4 cells.

The instructive part: **the predicted win happened and the item still lost.** p2,
which over-credits +1.25 in every recorded run, improved 0/3 to 3/6 -- a
narrower rule fixes it, as the first attempt in this list also found. p19, named
in advance as the likeliest casualty, went 2/3 to 6/6. And ten cells that had
been stable moved anyway: p1, p3, p4, p6, p9, p10, p12, p14, p15, p18. Reverted.

**The ninth, same day, testing why the eighth failed.** Normalised per run, the
eighth's damage was NOT over-matching: over-credits held flat at 2.00 to 2.33 per
run while under-credits went 0.67 to 2.33. The closed rule was refusing matches
it should accept. WK1 had shown the same failure and been fixed by a carve-out --
"degree and detail are not differences of kind; the same thing named with a
different number or extra particular is still that thing" -- which Q6 never
received, because it sat in WK1's own entry rather than in the shared definition.
So the carve-out was moved into `EQUIVALENCE_DEF` and Q6 re-measured with it.

It got WORSE: median 15/20, under-credits UP to 3.67 per run, over-credits down
to 1.50. The clause meant to loosen matching tightened it. p10 collapsed 4/6 to
1/6 and p15 3/6 to 1/6, against gains on p3, p6 and p12.

So the diagnosis was refuted, and the refutation is the useful part: adding
qualifying prose to this item does not steer it in the direction the prose
names. Both attempts reverted. WK1 held 18/18 with zero spread throughout, so
the carve-out KEPT its place in `EQUIVALENCE_DEF` -- that half is measured
neutral and is where a general truth about matching belongs.

**The generalisation runs one way, and Q6's wording is the good one.** Tried in
reverse the same day: Q6's own definition -- "semantically equivalent... that
INCLUDES equivalence established by combinations of negations and antonyms",
open-ended, with three concrete examples -- was put into WK1 in place of the
closed parity framing. WK1 held 18/18, no cell changed, and WK1/p7 stayed 3/3.

So Q6's wording works on both items while WK1's works only on WK1, and it is 303
chars shorter. `olx_prompts.EQUIVALENCE_DEF` now holds Q6's text and BOTH items
use it; migrating Q6 onto it left its prompt sha byte-identical, so that half
needed no measurement at all. WK1 keeps its own additions (the two-activities
gloss, degree/detail, the pointer rule) in its own entry.

The bearing on this note: Q6's definition is not what limits Q6. It is good
enough to carry another item unchanged. The ceiling is in the ITEM -- in how
`refers_to` is answered -- not in how matching is worded.

So the ceiling is not a wording problem waiting for the right words. A closed,
principled definition that measurably fixed the target cell still cost two cells
elsewhere, which is the same trade every earlier attempt made.

Caveat on reading those per-cell rates: the baseline is 3 passes and this was 6,
so 3/3 to 5/6 may be sampling rather than damage. The medians and means are the
sound comparison, and both fell two cells.

**The tenth, 2026-09-05 (subgoal Q47), and the ONLY STRUCTURAL one.** Every
earlier attempt was a wording of a discriminator asking whether a change is
ADEQUATE. This one was not. `change_a1`/`change_a2` had **no rule at all** —
just the bare desc — while their sibling `affect_c1` carried a worked-out one,
and the measured behaviour followed exactly: over 240 cell-runs `change_a2`
answered `absent` 60 times, **the same 60 as `state_a2`'s `absent`**. The pair
refused only EMPTY boxes, never an inadequate one, because nothing had ever told
it how. So the fix was to give it the sibling's SHAPE: the reading question
"what becomes of the antecedent?", generous on phrasing, failing verdict
reserved for a box that says nothing about the antecedent or only restates the
plan, plus one named trap.

It lost on both sides — python 17/20 → **15/20**, olx 18/20 → **16/20** — and
**six perfect cells moved**: p1, p3, p9, p12, p14, p20, with p4 11/12→7/12, p6
11/12→7/12, p16 9/12→6/12 against gains on p15 (10→12) and p18 (7→10).

**The part that matters: it never fired on its target.** p2 was pre-registered
0/12 → 8.75 = gold and stayed **0/12**, `change_a1`/`change_a2` answering
`met`/`met` in all twelve runs. It damaged six cells it was not aimed at and did
not touch the one it was aimed at — the *opposite* of `A_NO_CHANGE`'s predicted
failure mode (over-flagging credited cells to catch p2).

**What this does to the "structural beats wording" heuristic.** That heuristic
is real and has won here repeatedly (`benefits_failing`, `wgb_names`+maps,
`measurable`). This is its clearest measured counter-example: a genuine
structural asymmetry, correctly diagnosed, fixed in the sibling's own shape, and
it still lost — and lost without reaching its cell. Structure beats wording when
the GROUNDS are confusable; it does not help when the slot cannot see the cell
at all. Establish that the rule can reach the target before spending a sweep on
its shape.

**Correction to the drift claim below.** The 2026-08-18 measurement that drift
sits on "zero of twenty cells in `change_*`/`affect_*`" is **no longer true**.
Under Q47, `affect_c2` flipped on p16 and p5 and `change_a2` on p16, and the
revert sweep is the check on whether that was the rule or the item. Read the
next paragraph with that in mind.

**The eleventh, 2026-09-06, and the only one that changed the SCHEMA.** Every
previous attempt was prose. This added **picks** — `change_a1_does` /
`change_a2_does`, six values (`gone`, `swapped`, `met_differently`,
`other_thing`, `restates`, `nothing`) — mapped to the verdict, so the grader had
to **name what the box does before any verdict existed**. That is the move that
won twice the same day: Q10's `measurable` took p10 from 4/12 to 12/12 by naming
the *holder*, Q43's `wgb_names` took p18 from 3/12 to 12/12 by naming the *kind*.

**It failed, and the manner of failure is the whole value.** The pick fired, was
answered sensibly, and **sorted both targets into crediting categories**:

- p2 → `met_differently` on the second box, **9 runs of 12** (0/12 → 1/12)
- p8 → `gone/swapped`, **10 runs of 12** (0/12 → 0/12)
- `restates`, the value written for p8, was chosen on **neither** target

So this is not the grader ignoring a rule, which is what the previous ten looked
like. **Forced to name what the box does, it names something that earns credit.**
The distinction claimed as "a reading, not a judgement" is a judgement after all —
a stronger refutation than any wording test can give, because the schema removed
the room to avoid the question. Cost: python 16→16, olx 18→16, **net −2**; one
real gain (p18 6/12→12/12) against losses on p4, p6, p14, p16.

**What this changes for the next attempt.** "Structural beats wording" has three
wins on this project and now one clean loss, and the loss says where the boundary
is: a pick helps when its categories genuinely separate the cases, and does
nothing when the hard part is *which category the case belongs to*. Before
proposing a twelfth, show that the intended value would actually be chosen — on
Q46's parallel problem the pick's categories separate the cells cleanly
(`other_activity` 9/12 on one cell against `doing` 12/12 on another); here they
did not.

**The twelfth, 2026-09-10: ORDER.** `link_c2` asked before `state_c2`/`affect_c2`,
on the theory that the linking judgement should be made before the ones that
depend on it. The rubric's own comment warns that "ORDER IS PART OF THE DESIGN
... a reorder is a real prompt change with its own sweep", and it was: **olx
−1.9**, reverted. Paper was killed mid-run rather than finished, so the reorder
has a web number and no paper number — if it is ever retried, that half is owed.

**The thirteenth and fourteenth, same day: SEGMENTATION, and both lost to doing
nothing.** These attacked the PAPER side's version of the problem — paper gets
one flat block and must find eight answers in it, which is why `affect_c2` reads
the first pair's sentence twice. An LLM was asked to segment the response into
the eight expected parts, and the segments fed to the scorer:

- **thirteenth, two-step** (segment, then judge the segments): **8.7/20**
- **fourteenth, integrated** (one prompt doing both): **9.7/20**
- baseline, the short box inventory alone: **10.3/20**

So both designs scored WORSE than the plain inventory, and the integrated one
only recovered most of what the two-step lost. The inventory was KEPT (it is
`score._answer_inventory`, mechanical from `olx_prompts.RESPONSE`); the
segmentation was not. **Telling the grader the structure to expect beats handing
it a structure**, at least at this quality of segmentation.

**Q6 is the argument against the labelled-parts clause, 2026-09-10.** Q3's paper
side gained +1.3 cells from "judge each answer on the part the student labelled
for it". It shipped globally for a day and is now scoped to Q3 alone
(`score.LABELLED_PARTS_ITEMS`), and Q6 is why: only **5 of its 19 responses
label anything**, and **p19 labels "(New C)" over the very text gold charges**,
so keying on labels here would confine the grader to a mislabel. Any attempt to
extend it needs Q6's own six runs first. See `paper-columns-before-2026-09-10`.

**Not in GOLD_CEILINGS, deliberately.** That table is for criteria *gold* decides
inconsistently, and none of this is about gold — gold's position on p2 is
specific and has never wavered. The tally of attempts belongs here.

**Why it resists.** Of 18 cells with a consequence box, 7 name the consequence
and negate it, 5 give the inverted attribute without naming it, 3 restate it
directly. So inversion is how the item is normally answered, not an edge case —
which means any rule about it moves most of the corpus at once, and the cells it
helps and hurts are decided by wording too fine to state.

**The instability underneath.** On the sweep of 2026-08-18 only **5 of 20 cells
returned the same judgement in all three passes**; drift sits ENTIRELY in the
four `state_*` slots (the ones carrying `refers_to`) and on zero of twenty cells
in `change_*`/`affect_*`. A 2-cell move is inside the noise, so a 3-pass sweep
cannot resolve a rule that trades two cells for two.

**Do this instead of writing a rule.** Suspect the FIXTURE first — three cells
once explained as gold or model faults (p10, p14, p15) were boxes cut in the
wrong place, each found by printing the eight boxes and reading them against the
.docx. See `fixture-defects-found-by-readout` and the blind-spot note in
`enforcement.check_consensus_spans_are_disjoint`.

Related: `q4a-p18-duplicate-antecedent` (held), `olx-python-equivalence`.
