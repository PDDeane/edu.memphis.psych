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
3a. **Leakage.** Does the prompt QUOTE the answers it is meant to judge?
4. **Declare** whatever is left.
5. **Reduce** the declarations, on the schedule in section 5.

**`leakage.py` runs before every sweep, and `agreement.py` REFUSES to sweep
handout 2 while any rule block echoes the cohort without a recorded verdict.**
A rule that borrows a student's sentence scores the cell it was copied from and
proves nothing about the criterion; worse, the sentence is almost always taken
from the very cell the rule was written to fix, so the gain it reports is
circular. This is not hypothetical here. Two recorded gains were found to rest
on quoted prose *after* they had been measured, reported and committed:

* DAY1's avoidance-framing rule contained "I will push myself to meet my goal so
  I don't have to do the extra chore" — DAY1/p8 with "30 pushups" changed to
  "the extra chore". p8 is the cell that rule took from 0/9 to 9/9.
* WK1's agent rule contained "I will stay up an extra hour on Friday", which is
  WK1/p1 verbatim, and "the extra laps will keep stacking up", which is WK1/p8
  with the noun swapped. The item had been recorded as perfect on that rule.

The two cases then came apart under measurement, and the difference is the
lesson. DAY1 held its number with the borrowed sentence replaced by an invented
one: that rule was a real criterion. WK1 did not — it lost p7, and p7 is the
cell whose configuration a `trigger_behavior` note had described in PARAPHRASE.
p1, whose sentence was reproduced word for word, held. So the verbatim quote was
not the load-bearing one; the described cell was. That is the form neither the
n-gram check nor the bigram check can see, and it is the one that mattered.

Neither was noticed by reading. Both are obvious the moment the prose and the
responses are diffed, which is all the tool does.

A shared phrase is not automatically a fault, and the tool cannot tell the three
cases apart — DOMAIN VOCABULARY that both sides must use, COINCIDENCE where an
invented example lands on a stock phrasing, and QUOTATION. A person judges, and
records the judgement with `--review`. **Verdicts are keyed to the sha of the
prose**, so re-wording a block lapses its waiver and the gate asks again — which
is the property that matters, because a rule gets re-worded at exactly the
moment someone is tempted to paste a student's sentence into it.

The worst form is not a quoted phrase but a described cell WITH ITS GRADE
attached: "against a screen-time goal, gating the screen activity on finishing
coursework earned full credit", or "cost participant 10 two points". That tells
the grader the answer for one identifiable row. State the criterion, never the
row.

**`measured.py --preflight` enumerates what is outstanding, in this order, and
`agreement.py` REFUSES a probe while anything is.** A probe is a participant
subset run six or more times: ~24 calls to settle one cell, and a settled cell
is worth nothing while that item's fixture is unread or its gold row does not
reconcile with its own comment. `--force-probe` overrides it, for the case where
the probe IS what settles a blocker.

The gate is code rather than a paragraph because this section already told
someone to check exclusions first and seven items were worked before any
exclusion was retested. A step order that is only written down is a step order
that gets skipped under momentum, and probes are exactly where momentum
gathers — they feel like progress and cost a fraction of a sweep.

Two of its detectors are worth knowing about, since both were built from
mistakes made here:

- **Fixture suspects.** A cell wrong in every run where we award NOTHING against
  full-marks gold, or award something against gold 0. Every other stable miss in
  this corpus is off by one deduction step, which is what a criterion boundary
  looks like; these two shapes are what a box holding the wrong text looks like.
  It consults EVERY artifact before flagging, because a cell that was ever right
  is unstable rather than mis-parsed, and reading its fixture will find nothing.
  That check removed four of seven candidates on first run, including one this
  session had already called a probable fixture defect out loud.
- **Non-reconciling gold rows.** Where a grader itemises their arithmetic, the
  itemisation can be checked against the score. It found three rows nobody had
  looked at, after D2/p11 and DAY2/WK1 p7 were found by hand.

Every step that edits prompt prose ends with a sweep of the items it touched,
compared against the last baseline on the same denominator, BEFORE the commit —
including steps 0 and 5, where the edit is a deleted citation rather than a new
rule. See "No prompt edit is finished until it has been measured" in section 2.

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

**Both questions only apply to exclusions that are claims about the MODEL.**
`cell_exclusions` returns a kind with every cell, and the kind decides whether
measurement can say anything at all:

| kind | what it claims | can a sweep refute it? |
|---|---|---|
| `self_graded` | the prompt hands over the answer and the grader's decision | yes — that is the necessity test |
| `unscoreable` | gold's row cannot be reached by any correct answer | yes — a cell that reaches it refutes the claim |
| `suspect` | the submission was mis-transcribed; the input is another participant's data | **no, ever** |

A `suspect` cell agreeing with gold is a coincidence between the wrong
student's answer and this student's score, and it is the single reading that
must not be taken as reassurance. There is nothing to be right about: the input
is not what the student wrote. No number of passes can retire it — only
re-transcribing the submission can.

This was not hypothetical for long. The expired-declaration check went in and
within minutes offered to un-exclude PR/p2, a known mis-transcription, because
it scored 3 of 3. The check now reads the kind and skips `suspect` entirely;
`unscoreable` and `self_graded` still fire, verified both ways at 6/6.

**For the two kinds that ARE claims about the model, step 0 asks TWO questions,
and the second is the one that gets skipped: is this exclusion CORRECT, and is
it NECESSARY?** They have different answers and opposite consequences.

| | the cell scores WRONG | the cell scores RIGHT |
|---|---|---|
| **correct?** | the exclusion is hiding a miss — remove it, take the miss | the exclusion is consistent with itself |
| **necessary?** | — | UNTESTED until you remove the citation and measure |

An exclusion on a cell that scores right is not thereby justified. It rests on
a claim — that the prompt hands the grader this answer — and that claim is
testable: rewrite the citation as the RULE it was illustrating, measure the
cell again, and see whether it still scores right without the answer in front
of it. If it does, the citation was never load-bearing, and BOTH the citation
and the exclusion go: the cell counts, and the denominator grows.

This is the direction the reduction pressure usually misses, because nothing
about a correct cell looks wrong. Section 5's two rules both start from a
problem — a miss being hidden, a stale claim reporting unwinnable ground — so
an exclusion whose cell behaves can sit undisturbed forever while quietly
costing the rate a cell it has earned. The audit that found the eight wrong
ones also left 21 right ones untouched with the words "the exclusion is doing
its job", which was an assumption dressed as a verdict: what its job REQUIRES
is that the citation be doing work, and none of the 21 had been asked.

Both halves are cheap and neither is optional. The wrong ones cost you a rate
you did not earn; the unnecessary ones cost you cells you did.

**Un-excluding a cell turns every existing quote of that student into a live
answer key, so sweep ALL items and ALL prompt sources afterwards — and keep
sweeping until the check is clean.** An exclusion licenses the prompts to quote
that participant freely. Remove it and every one of those quotes becomes what
`check_rule_examples_are_not_corpus` exists to catch: the model reading a
counted cell's own words with the verdict attached. The quotes are not where
you left them, either. They accumulate in two places — a rubric `desc` or a
`guidance` bullet, and `olx_prompts.SLOT_NOTES`, which is a second source of
prompt prose that a scan of the rubric alone will not see.

Measured the hard way on 2026-08-24. Un-excluding Q1/p1 and Q2/p6 lit up quotes
that had sat there legally for months. Fixing the rubric copy surfaced a second
copy in SLOT_NOTES; fixing that surfaced a THIRD copy of the same student's
sentence in a different note. Three passes of the same check to reach clean, on
one exclusion change. So: run the check as the last step of every exclusion
change, not the first, and run it again after each fix.

**Measured on Q1, and it is worth knowing which direction the answer went.**
Its five citations were bare attributions with a decision attached —
"(participant 1)", "which is what participant 6 scored", "which is how
participants 10 and 16 were credited". Deleting the attributions left every
rule intact, which is the common shape and the reason the test is usually
cheap. Three runs with the citations gone:

| | before | after |
|---|---|---|
| the 15 cells already counted | 13, 13, 13 | 13, 13, 13 |
| the five cited cells | 3/3 each | four still 3/3 |
| the whole item, 20 cells | not measurable | **18, 17, 18** |

So the citations were load-bearing for nothing, and the honest rate is 18/20
against a reported 13/15. **Five cells we score correctly had been subtracted
from every rate on an untested claim.** An audit that only looks for exclusions
hiding misses would never have found them, because there was no miss to find.

**Why this half gets skipped, stated plainly so the next reader recognises
it.** A wrong-and-excluded cell eventually attracts attention: the item reads
as perfect and someone asks why. A right-and-excluded cell produces no symptom
at all — the rate is merely smaller than it should be, and a smaller
denominator looks like rigour. Of 34 exclusions audited on 2026-08-23, the 8
hiding misses were found and fixed the same hour; the 21 that were merely
unnecessary were dismissed in a sentence, and finding them took a second pass
and a second prompt.

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

**READ EVERY RESPONSE IN FULL. A truncated readout is not a readout.** Print the
whole box and the whole document region it came from — every line, to the end —
whenever a response is being read for any purpose: a fixture audit, a
disagreement with gold, a decision about a declaration, or a claim in a report.
Never sample a response with a line-limited command, never quote from the first
sentence, and never let a table of one-line excerpts stand in for the text. The
`--fixture ITEM:PID` readout prints every line for exactly this reason.

The failure is not hypothetical and it is not cheap. On 2026-08-24 a survey of
WK1 was built with `sed -n '7p'` — the first response line of each cell — and
p5 came back as "I will plan out my meals of when I eat fruits and vegetables."
On that basis it was reported as an answer gold credits with 4 while stating no
consequence, no conditional and no contingency at all, and that single "fact"
was used to argue that gold on this item was not reproducible by any rule, that
no gate could ever match it, and that a declared divergence was therefore
correct. The argument was written up and stated to the user.

p5 has a second sentence: "For every week that I stick to the meal plan, I will
allow myself to skip one chore for the next week." A textbook weekly
contingency. Read in full, the item's ten gold-bearing cells separate PERFECTLY
on a single feature, and the rule that had just been declared unreachable was
sitting in plain view.

So: the cost of a truncated readout is not a missed detail, it is a confident
conclusion in the wrong direction, defended with evidence that does not exist.
If a response is worth reading, it is worth reading to the end.

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

Both errors happened here on the same day. Q1's baseline had p17 wrong in 3 of
3 and a criterion rewrite was drafted for it; six passes said 4 of 6, the
rubric had already recorded that cell as a model limit, and the "fix" would
have re-litigated a settled question against an unlucky draw. In the other
direction, Q4a's numerator fell by one in one run of three after eight
citations were removed, on a single cell — small enough to wave through, except
that this item's baseline spread was 0 cells, which makes a stable-right cell
going 2 of 3 a change in the item's STABILITY rather than in its score.

Knowing the rule is not complying with it, and the way it fails is through the
output format of whatever script did the comparison. On 2026-08-24 a scratch
comparison of 1a printed `<-- LOST` for a cell that went 3/3 to 2/3 and
`<-- gained` for one that went 1/3 to 3/3, and both were written up
immediately — one as "a wobble inside the item's variance band", the other as
"the rewrite fixed it" — with no probe run and this paragraph already in the
guide. Two labels in a report were enough to skip it, because a line that reads
like a verdict gets used as one.

So the arithmetic moved into `compare_runs.py`, which prints PROBE REQUIRED and
the exact command instead of a direction, marks the comparison NOT REPORTABLE,
and exits non-zero so a chained script stops rather than continuing. Use it
rather than writing the tally inline — that is also how the two definitions of
`scored_exactly` came to disagree in print.

**A clean 3/3-to-0/3 flip is not decisive either, and that exemption is the
dangerous one.** `compare_runs.py` shipped with one: a cell uniform before and
uniform after was reported as REGRESSED or FIXED without a probe, on the
reasoning that three-and-three is more than a rate. Q2's p17 retired it within
the hour. Across six sweeps that cell scores 10 of 18, and it has produced 0/3,
2/3 and 3/3 in both directions — three consecutive identical runs each way. A
coin throws uniform triples about a quarter of the time, so uniformity is
precisely what three passes cannot separate from a real flip, and the exemption
sat exactly where acting on noise is most tempting, because a clean flip is what
looks worth chasing. Had that REGRESSED line been believed, the next hours would
have gone to hunting a regression in a prompt that never caused one.

**Quote the ledger's number, not the run table's best line.** `--record`
publishes the median run; reading a three-run table by eye invites the best one,
especially when it agrees with the change just made. 1a was reported at 18/20
off a sweep whose runs were 17, 17, 18 — the median was 17, and 18 was the
flattering pick. A same-prompt repeat then produced 18, 18, 19, so the figure
happened to survive; the reasoning did not, and it is the same optimistic-read
reflex that put a decisive-move exemption in `compare_runs.py`.

Corollary worth its own line: **check a suspicious cell against every artifact
that ever measured it, not just the previous sweep.** p17's six-sweep history
took one query and settled in seconds what a fresh probe would have spent 24
calls on — and it answers a question a probe cannot, which is whether the cell
was ever stable in the first place.

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

**Compare against the RECORDED state, not only the old baseline.** A diff
against a stale baseline cannot see a gain being undone: DAY2/p8 was 0 of 3 in
the baseline, was fixed to 5 of 6 by a committed change, and was knocked back to
0 of 3 by a later edit that never mentioned the gate it moved — and the
comparison read "no change", because both ends were 0 of 3. `compare_runs.py`
now diffs against the ledger's recorded run as well, and prints REGRESSION
AGAINST THE RECORDED STATE for any cell an earlier change had already won.

The companion habit: **when an edit measures neutral, ask whether it is neutral
or COMPENSATING.** That same sweep held its median at 15 while one cell gained
two runs and another lost three. Only the per-cell table shows it, and a median
is exactly the statistic that hides it.

**Ask the grader for a PARSE, not a judgement.** This is the difference between
a rule that works and the same rule that wobbles, and it cost eight attempts on
one cell to find.

A question about the PLAN invites the model to weigh the whole answer: "is a
consequence delivered?", "does this target the student's own behaviour?", "is
this really operant conditioning?". On easy cells it agrees with you; on the
cells that matter it returns different verdicts run to run, because the question
has no procedure in it. A question about the SENTENCE has one: "find the clause
that states the consequence; is a person in its subject position, and does its
verb say that person brings the thing about or takes it away?" That is a parse,
and parses do not wobble.

Measured on WK1/p8. Four semantic framings failed, including a well-formed
binary gate that still flipped the two decisive cells — the target read
delivered two times in three, and a correct neighbour read undelivered one time
in three. The same criterion asked syntactically put the target at 6 of 6 and
the neighbour at 6 of 6, both correct, controls holding, and the item went 15/18
to 17/18. Nothing about the criterion changed; only what the model was asked to
look at.

Two corollaries worth the words:

- **A closed list in a rule is a boundary you are promising to defend.** The
  first syntactic version listed transfer verbs — give, buy, treat, withhold —
  and so excluded "I will stay up an extra hour on Friday", a student granting
  themselves a privilege, putting a correct cell at 3 of 6. The case had been
  noticed on paper, marked "marginal", and waved through. Widening from "is the
  verb on this list" to "does a person make the thing happen or stop happening"
  fixed it at 6 of 6. Prefer the criterion the list was approximating.
- **Give a gate no hedge.** `!key:Label:unclear` ADDS `unclear` to `met`/`absent`,
  and a gate fails on anything but satisfied — so the hedge becomes a 4-point
  coin flip on every cell. Omit the segment for a binary gate. Removing the hedge
  is necessary and not sufficient: it was the reframing that fixed the judgement.

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
the numerators at 12, 12 and 14 — unchanged BY CONSTRUCTION, since the newly
counted cells were the ones already known to be wrong. That number could not
answer the only question that mattered: whether the deleted examples had been
doing work for the OTHER cells. Only a fresh sweep of the three items can say,
and the answer is a numerator, not a rate.

**Never regenerate the prompt while a run is in flight, and do not trust
yourself to remember.** Both harnesses read the generated `.olx` per call, so a
`--write` part-way through splits that run across two prompts: the cells
already sent used the old text, the rest use the new, and the `.runs.json`
records nothing about it. It reads exactly like a clean measurement, and it is
the one contamination that cannot be detected afterwards — the before and the
after differ by an unknown mixture.

Done on 2026-08-24, by someone who had deliberately waited for two earlier runs
to clear for precisely this reason. Handout 3's 1a baseline was 40 cells of old
prompt and 20 of new, and the two items queued behind it would have measured
the NEW prompt as their baseline. All three discarded.

`olx_prompts.py --write` now REFUSES while a harness process is scoring cells,
naming the process, with `--force` for the case where the run is knowingly
being thrown away. The check is at the point of the mistake rather than in the
audit, because an audit that runs afterwards can only tell you the measurement
was worthless.

**No prompt edit is finished until it has been measured, and a commit is not
the place to find that out.** Every change to prompt prose — a rubric rule, a
`SLOT_NOTES` entry, an invented example replacing a quote — needs its item swept
before it lands, compared against the last baseline on the same denominator. An
edit that merely satisfies an enforcement check is the most dangerous kind,
because the check going green feels like the work finishing. It isn't: the check
proves the prompt no longer leaks an answer, and says nothing whatever about
whether the replacement still teaches the rule.

This bites hardest on exactly the edits that look safest. Swapping a real quote
for an invented one of the same shape is a rewrite of the only concrete example
the grader has for that slot, and concrete examples are what these prompts run
on — handout 1's Q4b lost six cells to a rewrite that replaced examples with
abstractions, and got them back only when invented examples went in. Cleaning
three leaked quotes out of 1a's period slots is the same operation on an item
whose own code comment records those slots as variance-sensitive.

So: sweep, compare numerators, THEN commit. If the numbers drop, the leak still
has to go — but it goes together with a rewrite that holds, or with the loss
declared, and either way the commit says what the change cost.

`olx_prompts.py --write` now names the sections whose text it changed and calls
them UNMEASURED, because the thing that actually goes wrong is not disagreeing
with this rule, it is sweeping from memory: editing four `SLOT_NOTES` entries,
remembering three, and publishing a baseline for an item whose prose moved
underneath it. The generator knows exactly which sections it rewrote, so it says
so, at the point of the mistake rather than in an audit afterwards.

**End every sweep by recording it: `measured.py --record <item> OUT/<item>.runs.json`.**
This is the step that makes the two rules above enforceable rather than
aspirational. The ledger stores the SHA of the item's own OLX section and the
exact exclusion set the number was computed over, and
`check_items_are_measured_as_configured` fails the suite when either has moved
since — so a rewritten rule or a removed exclusion turns the item's recorded
number red instead of leaving it to be noticed.

It exists because it was needed. Q1 had five exclusions removed and six
citations rewritten into rules in one commit and was never swept afterwards; its
number was carried forward by re-derivation from a sweep that predated both
changes, and an audit five commits later is what found it. Nothing looked wrong,
because nothing WAS visibly wrong: a removed exclusion deletes the record that
the cell was ever in question, and a rule rewrite is one diff among many.

An item may declare `pending` with a reason instead of a measurement — the usual
bargain in this project. What it may not be is absent, which is the state Q1 was
in, and the state the check refuses.

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

**WORKING HYPOTHESIS: the coupling tax scales with VOLUME, not content.** That
adding prose to one slot moves gates the text never mentions has been observed
repeatedly here, and was treated as an unavoidable toll on any edit. One
measurement suggests it is a toll on SIZE. The `restricts` block, about twelve
lines, cost DAY1/p11 and DAY1/p14 a run each. Removing `consequence_valence` and
the twenty-line put-on/taken-off block that existed to answer it gave both back —
2/3 to 3/3 each — and moved WK2/p15 1/3 to 2/3 as well. The cells that recovered
were the same ones the earlier addition had cost, and neither block mentions
them or anything they turn on.

If it holds, it inverts the usual move. Every failed attempt on the four cadence
items added words; the change that finally recovered two cells removed them. So
before writing a new rule, ask what can come OUT — a gate a later one subsumes,
a diagnostic whose question is answered, an operand with no consumer — and
measure that removal on its own. A removal is also the cheaper experiment: it
cannot introduce a false positive, only withdraw a behaviour you already have
measured.

Stated as a hypothesis because it rests on one observation. It would be
CONFIRMED by adding and removing a block of similar size on an item with no rule
change at all, twice, and seeing the same cells move both ways. It would be
REFUTED by a large addition that costs nothing, or a removal that costs cells it
never mentions. Until then, do not spend a sweep on volume alone when a real
rule is waiting to be measured — but when a sweep is going to run anyway, prefer
the version with less text in it.

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

**The sharpest form of that: ask for a QUOTE, not a decision.** WK1/p7 is the
cleanest case in the corpus. Gold says "-1 pt: This is an example of NP, however
your UTB is not procrastination", the student's UTB reads "Spending too much time
on electric devices", and `trigger_behavior` answered `utb` on every pass for
eleven attempts across two sessions — including one written the same day that
told it, in as many words, that an activity the chosen behaviour "might plausibly
cause, or lead to, or be a form of" is `other`. It did not move a single run.

The failure was not that the model inferred a RELATION between procrastination
and device use. It treated them as ONE activity under two descriptions, so every
instruction about relations missed. What worked, first time and 3/3:

> Quote the words THE STUDENT used for the behaviour, from their own
> unwanted-behaviour or goal statement, beside the trigger you quoted. If you
> cannot find words of theirs naming the SAME activity, answer `other` — and
> answer it even when you judge the two to mean the same thing.

p7 went 0/3 to 3/3 and WK1 to 18/18. The evidence field shows why: it now writes
both phrases side by side and answers from their difference, never adjudicating
what they mean. A word the student never wrote cannot be quoted, so the answer is
forced rather than argued.

The generalisation worth trying elsewhere: when a slot keeps reaching a defensible
but wrong judgement, stop refining the criterion and give it a MECHANICAL test it
must show its working for. "Find me the words" has no room for an opinion; "decide
whether these are the same" is all room. Guard it with "a paraphrase of their own
wording is fine", which is what keeps WK1/p8 — trigger "I do not attend the gym"
against a UTB naming "the gym" — from being caught by it.

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

**NEVER DECLARE A GOLD DIVERGENCE UNTIL EVERY ALTERNATIVE IS EXHAUSTED — and
the first alternative to check is the FIXTURE and its alignment with gold.** A
divergence says "we understand this cell and choose to disagree", which is the
most flattering thing that can be said about a miss short of dropping it: it
closes the question, reads as understanding, and costs nothing to write. It is
also the easiest thing to be wrong about, because a cell can look like a
principled disagreement for any number of duller reasons:

- the fixture hands the grader the wrong text, or splits it at the wrong
  boundary, so the two sides are not judging the same answer at all;
- the box the rule reads is empty, or holds a neighbour's words;
- gold's row does not reconcile with its own comment, making it a wrong NUMBER
  rather than a different judgement — D2/p11, DAY2/p7 and WK1/p7 were all found
  this way, and two of them had been declared or ceilinged first;
- the criterion is unreachable as written — a verdict token the slot does not
  offer, a rule parked where only one generator reads it;
- the item's own scoring layer makes the rule inert, which no amount of prose
  about it will fix.

So the order is: read the fixture out box by box **and in full — every line of
every response, see section 1** — check gold's arithmetic against its own
comment, confirm the rule reaches both generators and the layer that decides the
score, and only then — with the attempts and their numbers written down — ask
whether what remains is a genuine disagreement.

The in-full requirement earns its capitals here specifically. A truncated
readout does not merely fail to find the answer; it manufactures an argument FOR
declaring. WK1's divergence was defended on the strength of a neighbouring cell
that appeared to have no contingency, read from its first line alone — and that
cell's second sentence is a textbook contingency. Read whole, the item's cells
separated perfectly and the rule was obvious. A declaration argued from partial
text is the worst outcome this section exists to prevent, because it is
indistinguishable, afterwards, from a declaration that was earned.

The cost of skipping this is not hypothetical. p7's DAY2 and WK1 cells were
carried through four measured attempts and 0 of 36 passes, and looked exactly
like a divergence. What the reading actually produced was better: gold's rows
did not reconcile and became CORRECTED_GOLD, the criterion turned out to be
present but unreachable on one layer, and PR/NP were found not to carry
`targets_own_behavior` at all — which dissolved an apparent gold inconsistency
that a divergence would have enshrined as ours.

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
