# Building a first-version scoring model: a quality-control guide

Written 2026-08-20 after a full QC pass on one item, H1 Q6, which went from a
partly-understood 16/20 to 17/20 with every remaining disagreement declared and
explained. The point of that pass was not the score. It was to get the FIXTURE
exactly right, build a scoring model that works for the right reasons, and
correct gold only where the submission itself contradicts it.

With 20 responses per item this produces a **first model, not a validated
one**. Everything below is about how to spend that small sample well.

---

## 0. The order of operations

Work in this order. Most of the wasted effort in the session that produced this
guide came from doing step 3 while step 1 was still wrong.

0. **Exclusions.** Does every cell this item drops still deserve to be dropped?
1. **Fixture.** Does each box hold what the template says it holds?
2. **Gold.** Is the row right, and is its own itemisation coherent?
3. **Model.** Does the prompt tell the grader how to decide?
4. **Declare** whatever is left.
5. **Reduce** the declarations, on the schedule in section 5.

A scoring model tuned against a bad fixture measures the fixture. A model whose
declarations only ever grow measures the declarations.

**Step 0 is not a typo for step 5, and running one is not running the other.**
Section 5 sweeps the whole set of declarations when an item closes out; step 0
audits THIS item's exclusions before any work on it begins, which is also step
1 of EQUIVALENCE.md's cleanup procedure ("Remove exclusions the item gets wrong
anyway... Expect the reported number to FALL; that is the point"). The two are
easy to conflate and the cost of conflating them is one-directional: you spend
the session improving a rate computed over cells that were chosen to make it
look good.

It happened on 2026-08-23, on this guide, by someone who had read it. Seven
handout-1 items were worked and closed — two criteria rewritten and measured,
five declared — before any exclusion was retested. The audit then took minutes,
because excluded cells are still run and still scored, and found EIGHT cells
across five items that were wrong in 3 of 3 runs with the answer and the
grader's decision sitting in their prompt. Q4c and Q5 had been reported as
perfect items; they are 12/14 and 14/15. Every number reported before the audit
was computed over a denominator the audit shrank.

**Every step ends by writing down what it found and did not fix, in
`scoring/BACKLOG.md`.** Nothing in that file is enforced, which is exactly why
the entry has to be written: a finding that lives only in a session log is
gone, and several of a fixture audit's findings are visible nowhere else — the
readout that produced them costs an hour to reproduce. The declarations in
`enforcement.py` record what the audit SETTLED; the backlog records what it
opened.

---

## 1. Fixture first

**Read the boxes out one at a time against the document.** This finds defects
no check catches. Four found this way in one item: two boxes cut
mid-construction, one clause occupying two boxes, one box holding a purpose
clause that belonged to its neighbour. Each had previously been explained as a
fault in gold or in the model.

**An item answered with a chart or a table is read by PROVENANCE, not by
position.** There is no prose to locate a box in, so the question changes from
"is this box cut in the right place" to "is this the student's value, or is it
somebody's account of their value". 1c's three label boxes held the paper
scorer's sentence about the label — `"Weeks" appears as a bolded axis title
centred beneath the day tick values.` — in ten of twenty cells, which is the
answer to the grader's own question sitting in the field it reads. Ask of every
parsed or extracted box: could this text only have come from the student?

**Suspect the fixture before gold or the model.** Three cells once written up
as "a criterion gold decides inconsistently" or "a borderline flip" were our
own splits. "Gold is wrong" is the more flattering hypothesis; check the
cheaper one first.

**Know which overlaps are devices and which are defects.** A naming box and an
effect box cut from one clause may legitimately hold the same text: the
duplication is what lets each be judged. Removing it can make the fixture more
faithful and less scoreable — measured, one such split took an effect box from
`met` 9/9 to `incomplete` 7/9, because the box had been earning its credit on
the phrase it shared with its neighbour. What the exemption HIDES is the pair
being cut in the wrong place, which is the real defect.

**If a sentence splits across boxes at a conjunction inside the scope of a
negation, repeat the negation on the later conjunct.** "No longer X and Y"
split naively leaves "Y" asserting the opposite of what the student wrote. Two
non-verbatim words in the corpus so far, both one negation carried across one
split. Note that repeating it does not guarantee the box still scores: if the
phrase that ties to the reference text lives in only one conjunct, the other
conjunct may be too thin to be judged.

**An empty box renders as nothing, and the LAST box is exposed.** A `<Ref>` to
an empty field produces blank space; for the final box there is no following
heading, so whatever the app appends lands where its contents belong. That
produced a grader quoting a section heading of the prompt back to the student
as their own sentence, six times across five cells, invisible in every score
because the two verdicts involved score the same. Delimit every box and
terminate the response section.

**Close the audit with a backlog entry, and put five things in it.** The
repairs are in the fixture and the confirmations are in `MULTI_BLOCK_DECLARED`;
what needs the entry is (1) the cells whose miss the readout has now EXCLUDED
the fixture from explaining, with the passes behind them, (2) any exclusion the
readout retested and found stale, (3) the re-baseline the repairs themselves
require, since every stored number for a repaired cell now describes a fixture
that is no longer served, (4) published claims about the item the readout
contradicts, and (5) the shape the remaining error has, if it has one. The last
is the one worth the most and the one a per-cell fix list loses: 2a's audit
repaired two boxes and its real finding was that every miss left in the item is
the same +2.0 over-credit, which is a one-directional target rather than three
unrelated cells.

**Seed the fallbacks the OLX declares.** A `<SheetValue>` resolves from a
graded sheet and falls back to a plain component; a harness that grades one
item sees neither. Left unseeded it renders a labelled context line with
nothing after it — a harness artifact that looks exactly like a prompt defect.

---

## 2. Measurement discipline

This is where the leverage is. Nearly every wrong conclusion in the session
came from comparing two numbers computed on different bases.

**Match the measurement to the SCOPE of the claim, in both directions.**

| claim | needs |
|---|---|
| "the item is at N/20" | 3 passes |
| "cell X is wrong" | ~9 passes |
| "cell X improved from 11% to 44%" | ~30 passes per arm |
| "this rule helps overall" | a 9-pass CORPUS sweep |

Both errors are easy. A 3-pass table cannot distinguish a 56% coin flip from a
stable 11% miss — both print as one `-1.25`. And a 4-cell probe cannot see an
effect distributed thinly across twenty cells: one rule measured as worth ~1.8
cells corpus-wide showed nothing on any single cell.

**Establish base rates before attributing anything.** Four rule variants were
each credited with "fixing" a cell that turned out to be 56% exact unaided.

**When a 3-run measurement moves ONE cell, probe that cell before believing it
in either direction — and put stable cells in the probe with it.** The scope
table says a per-cell claim needs about nine passes; this is what that means in
practice, because the situation arises constantly and neither instinct is safe.
Accepting the move invents a defect; dismissing it as noise hides a real
regression. A probe is a handful of calls against the sixty an item costs, so
the answer is always to measure rather than to decide.

The controls are what make it worth running. One or two cells that were stable
and are not the target separate a SPECIFIC regression from item-wide wobble: if
the target moves and the controls hold, the change did it; if everything
wobbles, the item's variance did, and the target was never the story.

Both errors happened here on the same day. Q1's baseline had p17 wrong in 3 of 3
and a criterion rewrite was drafted for it; six passes said 4 of 6, the rubric
had already recorded that cell as a model limit, and the "fix" would have
re-litigated a settled question against an unlucky draw. In the other direction,
Q4a's numerator fell by one in one run of three after eight citations were
removed, on a single cell — small enough to wave through, except that this
item's baseline spread was 0 cells, which makes a stable-right cell going 2 of 3
a change in the item's STABILITY rather than in its score.

**Land a declaration correction and a denominator change as SEPARATE steps.**
Both are cheap and both are tempting to do in one commit, and then the next
measurement mixes them: a rate that moved because two entries were rewritten is
indistinguishable from a rate that moved because six cells started counting.
Correct the declarations first — they are text, and their numbers are already
in hand — then change the denominator, then measure. This is the bundling rule
from section 6 applied to declarations rather than to rules, and declarations
are where it is easiest to forget, because neither half feels like an
experiment.

**Pre-register the prediction and name a CONTROL cell.** A control is a cell
whose answer the change must NOT alter. Controls caught what totals hid, twice:
a rule that looked clean on its targets had broken a cell no error list named.

**Sweep, don't probe, for rules keyed on relations between boxes.** Such a rule
can fire on any cell exhibiting the relation, so the affected set cannot be
predicted from where the errors are.

**A stored result does not recompute when gold changes.** Correcting a row
invalidates every earlier measurement of that cell. Re-derive baselines from
`.runs.json` after touching the gold caveats, or compare only figures computed
on the same gold. A published "17/20" was cited for a whole day; on current
gold the same run was 16/20, and the difference got blamed on the reporter.

**Re-derivation is valid for a change to what a run is COMPARED AGAINST, and
invalid for a change to what the grader was SENT.** The distinction is the
whole of it: a corrected gold row, a new exclusion, a different definition of
exact — none of those change what the model saw, so the stored verdicts still
stand and recomputing them is honest. A prompt or fixture edit changes the
input, and every stored verdict was produced by a grader that never read it.
Re-deriving there is not a cheap measurement; it is an assumption that the edit
did nothing, dressed up as a result.

**When the denominator moves and the prompt moved with it, compare
NUMERATORS.** Removing exclusions raises the denominator, and a rate can hold
steady while the count of cells you actually get right falls — the arithmetic
hides the loss exactly where you are least likely to look for it. State the
threshold as a count, before measuring: "the numerator must not fall below 12."

Worked, 2026-08-23. Eight `self_graded` exclusions were removed and the
citations that justified them came out of the prompts, which meant deleting
worked examples from Q4a, Q4c and Q5. Re-deriving from the pre-change runs put
the numerators at
12, 12 and 14 — unchanged BY CONSTRUCTION, since the newly counted cells were
the ones already known to be wrong. That number could not answer the only
question that mattered: whether the deleted examples had been doing work for the OTHER
cells. Only a fresh sweep of the three items can say, and the answer is a
numerator, not a rate.

**Validate the served prompt every run.** The prompt reaches the grader through
three stages — rubric, generated OLX, dumped idmap — and only the third is what
a run measures. The guard must be BIDIRECTIONAL: a dump taken while an
experimental rule was live is a superset, passes a one-way check, and silently
re-measures the reverted change.

**Read the record, not the score.** Some defects cost nothing and are still
wrong: a leak into student-facing prose, a verdict of `incomplete` on an empty
field, a box credited for its neighbour's words. Print a whole record
occasionally.

---

## 3. Building the model

**Position and brevity beat content.** Sixteen wording variants of one matching
rule were built, measured and reverted; every one was added to the grading
guidance forty lines below the components that use the term. Two sentences
placed immediately BEFORE those components did what none of the rewrites could
— one target cell went from 11% to 78%, another from 56% to 100%.

**Define a term at its first use.** If the credit components say "matches", the
definition of "matches" belongs directly above them.

**Audit for language that overrides the definition.** A categorical instruction
elsewhere silently wins, especially one that pre-emptively dismisses the
exception ("this holds however closely the wording is echoed"). Soften what is
load-bearing rather than deleting it, and make it defer explicitly.

**Be precise about relations.** "Antonym" must mean *the two ends of one
scale*, or a grader will match "happier" to a listed "mad", which is two
properties rather than two poles. Tightening that one word removed an
over-credit and moved two cells up.

**Prefer one-directional rules.** A rule that can only turn a refusal into a
match cannot disturb a box that already matched, so most cells are structurally
immune rather than merely lucky.

**Distinguish three kinds of "and then what follows" in a reference entry.**
For "X, so I Y": Y restating X, Y an INTERMEDIATE step that still leads to the
unwanted behaviour, or Y a consequence. The first two are part of X. The third
is not, and should be matched against the consequence list instead. Getting
this wrong in either direction costs cells.

**Structural changes beat judgement changes.** Changes to what the grader SEES
have worked and stuck. Changes to how it JUDGES mostly have not.

**Editing a long slot note has non-local effects.** Clauses with airtight
logical scope moved cells whose preconditions they could not satisfy. An
incumbent wording is worth something purely for carrying no edit risk.

**Match the schema.** An instruction naming a value the enum rejects is dead
text — and worse, it is dead text on the channel you are trying to influence.

---

## 4. Correcting gold

The bar is a **fact established in the submission**, not a difference of
judgement. Four caveat kinds already exist for the rest: declare a deliberate
disagreement, a criterion gold decides inconsistently, a criterion neither side
scores, or drop the cell.

**Qualifies:** a second antecedent that does not exist in the document; an
antecedent appearing in no listed entry; a consequence equivalence supplied by
the student's own answer.

**Does not qualify:** a rubric-design opinion. Gold applies
**no-double-jeopardy** — it charges a naming miss once and does not re-charge
the effect — which looks like crediting an effect on something it says was
never named. Verified across all twenty rows: every effect slot gold withholds
is one whose box describes no effect. "We would charge this differently" is a
divergence, not a correction.

**Gold's ordinals are tallies, not indices.** "Second antecedent" means "the
second one you named", not "box 2". One cell needs opposite index readings for
its two families to make gold true; as tallies both are ordinary. Compare
per-family COUNTS, which is also what a cover group scores. Box-level
attribution invents disagreements gold never asserted — it manufactured four
across two cells that in fact agreed.

**An entry reasoning from box contents inherits every judgement in the split.**
One correction raised a row by reasoning from a clause that occupied two boxes;
repair the fixture and gold's original number was right. Check the spans first.

**Quote the row you are correcting.** One rationale cited a different student's
answer as its evidence. The conclusion survived; the entry was unverifiable.

**Assert the old value against the sheet on every run**, so a correction cannot
outlive the row it corrects.

---

## 5. Reducing exclusions

A caveat is a promise to stop looking, and they accumulate. Each one is
defensible at the moment it is written, and nothing afterwards asks it to
justify itself again. Left to grow, the headline rate stops measuring how well
the model scores and starts measuring how much has been excused.

**They do not all cost the same, and only two of the five move the number.**

| Caveat | What it does to the rate |
| --- | --- |
| `PER_ITEM_EXCLUDE` | **drops the cell from every rate** — the most flattering thing you can write |
| `CORRECTED_GOLD` | **moves the target** the cell is measured against |
| `GOLD_DIVERGENCES` | nothing. "A divergence is still scored; we just knowingly disagree." |
| `GOLD_CEILINGS` | nothing. Prose whose only job is to stop a ceiling reading as headroom. |
| `agreement.UNSCORED_GOLD_CRITERIA` | nothing head-to-head; the omission is symmetric by construction. |

The two rules below therefore bite on the first two. The safe landing place for
a real disagreement is one of the last three, which leaves the miss **counted
and visible** while still saying what it is.

**An exclusion on a cell the scorer gets WRONG must be removed.** That is
exactly the exclusion buying accuracy nobody earned, and it is the one that
will never remove itself, because the cell it hides is the cell that would
otherwise ask for work. There are two honest ways out and neither keeps the
exclusion: if the miss is ours, take it and let it show; if it is gold's, name
it — a correction, a divergence, a ceiling — so the cell counts again. Q6/p9
was `PER_ITEM_EXCLUDE` with `expect_error` -1.25 and became
`CORRECTED_GOLD[("Q6", 9)]`, because the exclusion "dropped a perfectly
scoreable cell from every rate in order to absorb an error that was gold's".
Its measured behaviour did not change at all; the rate went up because a cell
we score correctly finally counted.

**Declaring beats excluding wherever the choice exists, because an exclusion
silences questions nobody asked it to.** 2a/p18 was `unscoreable`, and
`check_consensus_spans_are_disjoint` skips those — so its `verdict`/`how1`
overlap sat exempt for as long as the exclusion stood, never judged by anyone.
Removing the exclusion surfaced it the same minute, and it turned out to be
faithful and declarable. An exclusion is written about the SCORE; it silences
every other question about the cell.

**An exclusion on a cell the scorer gets RIGHT must be retested until it is
removed.** It is not doing the job it was opened for, so what remains is the
claim, and the claim is now false in a way that misleads in the expensive
direction: a stale ceiling reports unwinnable ground where there is none, and
hides real headroom behind it. Q6/p4 left `GOLD_CEILINGS` for precisely that
reason once `scores_as_exact` credited its off-grid gold — "a note here would
tell a reader there is unwinnable ground where there is none."

**The retest trigger is a change, not a calendar.** In practice an exclusion is
retired by work done for some other reason, so retest every excluded cell that
a prompt or fixture change could plausibly reach, and sweep the whole set when
an item closes out. The ceiling on Q6/p9 was retired by a definition written
for the item as a whole: the cell went from 56% at nine passes to 9 of 9, and
"it was never an unwinnable criterion; it was an undefined term."

**Retesting is already free — the machinery exists, so use it.** Excluded cells
are still run and still scored; `cell_exclusions` says so in terms — "Not a
work list. Excluded cells are still RUN and still scored... Only the RATE
excludes them." On top of that, an `unscoreable` entry may declare
`expect_error`, the size of the miss it claims to absorb, and `stale_claim`
then asserts it on every run and prints `<-- CLAIM STALE` when the cell stops
behaving as documented. That is the retest, automatic and per-run. **It only
fires where the number is declared: 1 of the 5 live entries declares
`expect_error`, so the other four are retested only when a person remembers
to.** Declaring it on every one of them is the cheapest way to make this
section self-enforcing.

**The commonest bad reason to open one is instability.** A cell that flips
between two scores on identical input looks like a criterion that cannot be
scored, and "cannot be scored consistently" is the more flattering of the two
explanations, because it puts the fault in gold. Three cells once explained
that way were fixtures cut in the wrong place, and a fourth was a term the
prompt had never defined. An instability is evidence that the grader was given
no rule, not evidence that no rule exists.

---

## 6. What wastes time

- Tuning a rule while the fixture is wrong.
- Ranking variants inside the noise floor. Six variants, all intervals
overlapping, read as a progression.
- Treating a plausible reading of the text as a demonstrated cause. One cell's
miss was attributed twice to a rule whose removal left it unchanged. A correct
reading of the text is not a cause.
- Bundling several changes and reading the net result. You learn that the bundle
is bad.
- Fixing in the prompt what is broken in the harness.
- Running an experiment whose predicted outcome is failure without saying so
first.

---

## 7. When to stop

Stop when what remains is **declared**. For the item this guide came from:
seven slot disagreements, six of them a deliberate divergence, a gold ceiling,
or a corrected row — and the seventh explained. That is a finished first model.

Do not stop because a rule failed. Sixteen failures on one channel turned out
to be sixteen instances of one mistake about where the text went.
