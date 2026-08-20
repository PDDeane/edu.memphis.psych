# Building a first-version scoring model: a quality-control guide

Written 2026-08-20 after a full QC pass on one item, H1 Q6, which went from a
partly-understood 16/20 to 17/20 with every remaining disagreement declared and
explained. The point of that pass was not the score. It was to get the FIXTURE
exactly right, build a scoring model that works for the right reasons, and
correct gold only where the submission itself contradicts it.

With 20 responses per item this produces a **first model, not a validated one**.
Everything below is about how to spend that small sample well.

---

## 0. The order of operations

Work in this order. Most of the wasted effort in the session that produced this
guide came from doing step 3 while step 1 was still wrong.

1. **Fixture.** Does each box hold what the template says it holds?
2. **Gold.** Is the row right, and is its own itemisation coherent?
3. **Model.** Does the prompt tell the grader how to decide?
4. **Declare** whatever is left.

A scoring model tuned against a bad fixture measures the fixture.

---

## 1. Fixture first

**Read the boxes out one at a time against the document.** This finds defects no
check catches. Four found this way in one item: two boxes cut mid-construction,
one clause occupying two boxes, one box holding a purpose clause that belonged
to its neighbour. Each had previously been explained as a fault in gold or in
the model.

**Suspect the fixture before gold or the model.** Three cells once written up as
"a criterion gold decides inconsistently" or "a borderline flip" were our own
splits. "Gold is wrong" is the more flattering hypothesis; check the cheaper one
first.

**Know which overlaps are devices and which are defects.** A naming box and an
effect box cut from one clause may legitimately hold the same text: the
duplication is what lets each be judged. Removing it can make the fixture more
faithful and less scoreable — measured, one such split took an effect box from
`met` 9/9 to `incomplete` 7/9, because the box had been earning its credit on
the phrase it shared with its neighbour. What the exemption HIDES is the pair
being cut in the wrong place, which is the real defect.

**If a sentence splits across boxes at a conjunction inside the scope of a
negation, repeat the negation on the later conjunct.** "No longer X and Y" split
naively leaves "Y" asserting the opposite of what the student wrote. Two
non-verbatim words in the corpus so far, both one negation carried across one
split. Note that repeating it does not guarantee the box still scores: if the
phrase that ties to the reference text lives in only one conjunct, the other
conjunct may be too thin to be judged.

**An empty box renders as nothing, and the LAST box is exposed.** A `<Ref>` to an
empty field produces blank space; for the final box there is no following
heading, so whatever the app appends lands where its contents belong. That
produced a grader quoting a section heading of the prompt back to the student as
their own sentence, six times across five cells, invisible in every score
because the two verdicts involved score the same. Delimit every box and
terminate the response section.

**Seed the fallbacks the OLX declares.** A `<SheetValue>` resolves from a graded
sheet and falls back to a plain component; a harness that grades one item sees
neither. Left unseeded it renders a labelled context line with nothing after it
— a harness artifact that looks exactly like a prompt defect.

---

## 2. Measurement discipline

This is where the leverage is. Nearly every wrong conclusion in the session came
from comparing two numbers computed on different bases.

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

**Pre-register the prediction and name a CONTROL cell.** A control is a cell
whose answer the change must NOT alter. Controls caught what totals hid, twice:
a rule that looked clean on its targets had broken a cell no error list named.

**Sweep, don't probe, for rules keyed on relations between boxes.** Such a rule
can fire on any cell exhibiting the relation, so the affected set cannot be
predicted from where the errors are.

**A stored result does not recompute when gold changes.** Correcting a row
invalidates every earlier measurement of that cell. Re-derive baselines from
`.runs.json` after touching the gold caveats, or compare only figures computed
on the same gold. A published "17/20" was cited for a whole day; on current gold
the same run was 16/20, and the difference got blamed on the reporter.

**Validate the served prompt every run.** The prompt reaches the grader through
three stages — rubric, generated OLX, dumped idmap — and only the third is what a
run measures. The guard must be BIDIRECTIONAL: a dump taken while an
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

**Be precise about relations.** "Antonym" must mean *the two ends of one scale*,
or a grader will match "happier" to a listed "mad", which is two properties
rather than two poles. Tightening that one word removed an over-credit and moved
two cells up.

**Prefer one-directional rules.** A rule that can only turn a refusal into a
match cannot disturb a box that already matched, so most cells are structurally
immune rather than merely lucky.

**Distinguish three kinds of "and then what follows" in a reference entry.** For
"X, so I Y": Y restating X, Y an INTERMEDIATE step that still leads to the
unwanted behaviour, or Y a consequence. The first two are part of X. The third
is not, and should be matched against the consequence list instead. Getting this
wrong in either direction costs cells.

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

**Does not qualify:** a rubric-design opinion. Gold applies **no-double-jeopardy**
— it charges a naming miss once and does not re-charge the effect — which looks
like crediting an effect on something it says was never named. Verified across
all twenty rows: every effect slot gold withholds is one whose box describes no
effect. "We would charge this differently" is a divergence, not a correction.

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

## 5. What wastes time

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

## 6. When to stop

Stop when what remains is **declared**. For the item this guide came from: seven
slot disagreements, six of them a deliberate divergence, a gold ceiling, or a
corrected row — and the seventh explained. That is a finished first model.

Do not stop because a rule failed. Sixteen failures on one channel turned out to
be sixteen instances of one mistake about where the text went.
