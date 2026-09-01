# Behavior Modification handout scorer

Scores PSYC 1030 Behavior Modification handout submissions item-by-item against
the course's own scoring dictionaries, and measures itself against the 20 rows
of human grading per handout.

| | items | scored pts | cells | item agreement | adjusted | MAE / participant |
|---|---|---|---|---|---|---|
| Handout 1 | 8 | 45 | 156 | 87% | 88% | 0.94 of 45 (n=17) |
| Handout 2 | 12 | 40 | 216 | 94% | **96%** | 1.83 of 40 (n=18) |
| Handout 3 | 6 | 40 | 120 | 94% | — | 0.75 of 40 (n=20) |

*Item agreement* is exact-match over scored cells. *Adjusted* subtracts the cells
where this scorer disagrees with a grader **on purpose**, because the graders
applied their own written rule inconsistently — `handouts.GOLD_DIVERGENCES` names
every one. Handout 3 has none declared, hence the dash. `baseline.py` prints both,
plus the ceilings in `handouts.GOLD_CEILINGS` for criteria gold itself does not
decide consistently. Participant `n` is below 20 where a participant is excluded
as a few-shot exemplar of that item or as mis-transcribed.

**These are Opus numbers.** `score.py` defaults to `--backend cli`, which is Opus;
the web app (side `olx`) and `agreement.py` (side `python`) answer as
gpt-5-mini through lo-blocks. The model is
worth roughly 5 points of corpus mean and up to 50 on one item, so a figure here is
not a figure for what students get. `--backend lo` runs this same prompt on the
shipped model, and `out/SWEEP_2026-08-12.md` has the full four-way comparison.

## Run

```bash
cd <edu.memphis.psych>/scoring

python3 score.py --handout 1                  # all 20 participants
python3 score.py --handout 2 --participants 1 5 12
python3 score.py --handout 3 --items 1c       # re-score one item, merging
python3 score.py --handout 2 --retry-missing  # recover cells a run dropped
python3 baseline.py --handout 3               # compare output to the gold rows
```

Output lands in `out/hN/participant_NNN.json`, one file per participant.

**Always check `unscored cells: 0` before reading a baseline.** The CLI backend
sheds calls under concurrency; a partial run still prints a plausible-looking
table on a biased sample. Keep `--workers` at 4 or below.

## Files

| File | Role |
|---|---|
| `docx_text.py` | Stdlib OOXML text extraction; also reads chart title/axis/legend out of `word/charts/*.xml` for a future Handout 3 item 1c |
| `segment.py` | Splits a submission into `{item_id: student text}` by subtracting the blank template |
| `rubric_h1.py` | Handout 1's 8 items as data: point splits, deduction codes, canonical feedback wording, cross-item guidance |
| `rubric_h2.py` | Handout 2's 12 items; example items are criteria-derived (see below) |
| `rubric_h3.py` | Handout 3's 6 items, including the graph item 1c |
| `handouts.py` | Per-handout wiring: paths, markers, gold loader, exclusions |
| `backends.py` | `ClaudeCliBackend` (default, no API key needed) and `AnthropicApiBackend` (official SDK, `claude-opus-5`) |
| `score.py` | The engine: builds a per-item prompt, gets a deduction ledger, computes the score |
| `gold.py` | Reads the graders' scores and feedback out of the .xlsx |
| `baseline.py` | Per-item exact-match / MAE / tolerance metrics against gold |
| `agreement.py` | Measures the **lo-blocks** on-screen feedback prompts against the same gold rows |

## Design decisions worth knowing

**One call per rubric item, not per document.** Each item has its own point
ledger and its own feedback cell, and the gold data is per-item, so per-item
calls are both more accurate and directly measurable.

**The model never returns a score.** It returns credit checks plus a deduction
ledger drawn from a closed set of codes; `score = max - Σ deductions`, computed
in Python and clamped to `[0, max]`. Point values come from the rubric record,
not from the model's arithmetic. This mirrors how these graders actually write
("`-1 pt: missing a reason`") and makes every point auditable.

**Scores are not snapped to a grid.** The dictionary implies clean increments
(1.25 on Q6, 1.5 on Q4b), but the graders took off-grid amounts when they
judged it fair — participant 4 scored 6.0 on Q6 via "-2.5 ... -1.5". Snapping
would overwrite scores the gold data shows are legitimate, so `increment` is
advisory metadata only.

**Extraction subtracts the template.** Every submission is the blank handout
with typed answers inserted, so student text is what is left after removing
template lines (exact match, plus fuzzy match for lines ≥40 chars to absorb
transcription typos). This is not cosmetic: Handout 1's template carries a
worked "fruit-flavored water" example and Handout 3's carries an example data
table *and* an example graph. Participant 4's Handout 3 file contains a chart
titled "Water Consumption Over Four Weeks" — the template's example — and the
grader correctly scored that item 0/10, "Did not provide a graph."

**Items are scored with their neighbours in context.** Several items are graded
against other items, so each rubric record declares what it needs:
Q2's WGB against Q1's UTB; Q4b/Q4c against Q4a for A≠B≠C distinctness; Q6
against 4a and 4c for matching (the most common deduction in the corpus — 14 of
20 gold rows carry Q6 feedback).

**Implicit criteria are written out.** The dictionary under-specifies. Criteria
that appear only in the graders' feedback — a Q1 "reason" must be a reason to
*intervene*; Q2's reasons must be *benefits*; an antecedent's causal link must
be explained; Measurable needs a tracking *method* — are in each item's
`guidance`, marked `IMPLICIT (from gold)`. These are the difference between 0
and full credit on several items.

**Feedback ≠ deduction.** The graders sometimes leave advisory comments at full
credit, including safety notes ("*Please change this example to remove
something not related to meals*"). So `advisory_note` and `safety_flag` are
separate fields, and an advisory note is folded into the visible `feedback`
string only when something was actually deducted or a safety flag fired —
matching the graders, who leave the cell blank on full credit.

**Abstains rather than guesses.** `escalate: true` when no dictionary code
fits, when the model returned a code outside the closed set, or when
the model is genuinely unsure. Given that per-item scores drive a 150-point graded
project, this is grader-assist, not autograding.

## Measured agreement (20 gold rows, `claude-opus-5`)

The `vN` tables in this section and the two below are HISTORY — each column is a
past calibration pass, kept so a later change can be checked against what it
replaced. **The current numbers are the table at the top of this file**, and they
have moved well past the last `vN` column: handout 1 in particular went 80% -> 87%
after the reasons-counting and guidance-placement work described in
`rubric_h1.py`.

Two calibration passes, each tightening `guidance` against observed
disagreements: pass 1 on Q1/Q4a/Q4b, pass 2 on Q2/Q4c/Q6.

| exact match | v1 | v2 | v3 | v4 | v5 | v6 |
|---|---|---|---|---|---|---|
| Q1 | 70% | **75%** | 75% | 75% | 75% | 75% |
| Q2 | 85% | 85% | **80%** | 80% | 80% | 80% |
| Q3 | 80% | 80% | 80% | 80% | 80% | 80% |
| Q4a | 75% | **85%** | 85% | 85% | 85% | 85% |
| Q4b | 58% | **74%** | 74% | 74% | **95%** | 95% |
| Q4c | 70% | 70% | **80%** | 80% | 80% | 80% |
| Q5 | 70% | 70% | 70% | 70% | 70% | **90%** |
| Q6 | 40% | 40% | **45%** | 40% | 40% | 40% |
| **all items** | 69% | 72% | 74% | 73% | 75% | **78%** |
| MAE / item | 0.54 | 0.44 | 0.43 | 0.41 | 0.37 | **0.31** |
| MAE / participant (of 45) | 2.73 | 1.82 | 1.46 | 1.56 | **1.39** | 1.64 |
| totals within 2 pts | 45% | 60% | 65% | 60% | **70%** | 60% |

v2 tightened Q1/Q4a/Q4b; v3 tightened Q2/Q4c/Q6; v4 made Q6's ledger
schema-derived; v5 recalibrated Q4b; v6 recalibrated Q5. Run `baseline_h1.py`
to reproduce.

**Read the participant-total row with care.** It got *worse* in v6 while every
item-level metric improved, and the reason is instructive: Q5 had carried a
−0.50 bias that was silently cancelling Q6's +0.51 at the total level.
Removing Q5's bias left Q6's leniency undiluted. The decomposition is exact —
summed per-item bias is +0.51, Q6 alone is +0.512, and every other item
together is −0.003. **Q6 is now the sole source of participant-level bias**,
and fixing it is the only thing standing between this scorer and roughly
±1 point on a 45-point total.

**Q6 (v7): few-shot exemplars, measured held-out.** Three worked slot sheets
(participants 10, 8, 6 — gold rows whose feedback pins every verdict) are
embedded in the Q6 prompt via the rubric's `exemplars` field. Because those
responses are now in the prompt, **those three participants are excluded from
the reported metric** (`baseline_h1.py --exclude 10 8 6`); scoring them would
be self-grading, and indeed all three come out exact.

On the held-out 17, comparing like for like against v6:

| Q6, held-out (n=17) | v6 | v7 |
|---|---|---|
| exact match | 47% | **59%** |
| MAE | 0.75 | **0.60** |
| bias | +0.46 | **+0.31** |
| failed slots detected (of 41) | 35 | **37** |

Prose guidance had twice failed to move this item; exemplars moved it 12
points. The decisive one is participant 8: its answer says "I will be putting
an hour a day from Tuesday-Friday", which reads like a described change but is
a plan to perform the *goal behaviour*, not a change to the *antecedent* — the
grader marked every change slot absent. That distinction is very hard to state
as a rule and obvious from a worked case.

**More exemplars made it worse — tried and reverted.** Two further worked
cases (participants 5 and 17) were added to cover consequence-mismatch and the
whole-missing-half pattern. Measured on an identical held-out 15, Q6 got worse
on every metric:

| Q6, held-out 15 | 3 exemplars | 5 exemplars |
|---|---|---|
| exact match | **60%** | 47% |
| MAE | **0.60** | 0.85 |
| bias | **+0.43** | +0.52 |
| slots detected (of 34) | **29** | 28 |

The likely cause is the balance of the demonstration set rather than the two
cases being wrong: three exemplars carry 12 `met` verdicts against 12 unmet,
whereas five carry 24 against 16, tilting an item that was already lenient
further toward crediting — and diluting the participant-8 case that had done
the work. Both are kept as a comment in `rubric_h1.py` so the experiment is not
silently repeated; do not re-enable without re-measuring held-out.

**Q5 (v6): 70% → 90% exact, MAE 0.75 → 0.25, bias −0.50 → 0.00.** Five of its
six errors were under-crediting. The graders score this item on *form*: any
statement shaped "I continue to [UTB] because X" earns its 2.5 points nearly
regardless of insight. Decisively, participant 9's second reason drew the
written note "Explain how your second reason is a reason you are choosing to
not exercise" — as feedback, on a 5.0. A thin reason is an `advisory_note`
here, never a deduction.

**Q4b (v5) was the largest single win: 74% → 95% exact, MAE 0.39 → 0.05.**
The fix was recognising that the graders judge *framing*, not category. They
accept anything presented as happening during the UTB episode — including
internal states ("my brain is telling me to go to sleep but I couldn't") and
coping behaviours ("I rely on caffeine") — and reject only statements framed
as outcomes of it ("I walk around campus with stiff muscles") or that are not
examples at all. A second refinement: a trigger and the student's *response*
to that trigger are distinct, so "friends calling me" in 4a and "talking with
friends" in 4b do not violate the A≠B≠C rule.

**Q6 is the weakest item and has been through two fixes.** v3 fixed a real bug
— the scorer stacked two deduction codes on one 1.25-point slot, so a response
addressing half the question was penalised twice for the same gap — but its
"be generous" guidance overshot into leniency. v4 addressed that structurally:
Q6 is marked `derive_from_credit`, so the model no longer authors a deduction
list at all. It fills a required eight-property `slots` object
(`met`/`absent`/`mismatch`/`not_described` per slot) and `derive_ledger()`
turns unmet slots into deductions. One slot, one deduction, by construction;
"did the model remember to check slot 7" became a schema constraint rather
than a prompt-following question.

That worked on the metric it targeted — **detected failed slots went 31 → 42
of the 50 the gold scores imply** — and Q6's MAE (1.01 → 0.89), within-
tolerance (75% → 85%), bias (+0.76 → +0.51) and escalation count (3 → 1) all
improved. Exact match did not: it moved 45% → 40%, because the residual error
is now per-slot *judgement* rather than coverage, and Q6 needs all eight
judgements right to match exactly. Q6 remains mildly lenient.

**Q6 history — five attempts, two of which worked.** This item resisted
calibration harder than anything else in the corpus, and the pattern is worth
recording:

| attempt | change | held-out exact | verdict |
|---|---|---|---|
| v3 | guidance rewrite | 40% → 45%* | mixed — leniency bias appeared |
| v4 | schema-derived slot walk | 47% | kept — coverage 31 → 42 of 50 |
| v7 | 3 few-shot exemplars | **59%** | kept — best result |
| v8 | 5 few-shot exemplars | 47% | reverted |
| v9 | tighten consequence slots | 47% | reverted |
| v10 | a 4th exemplar (balance-matched) | 44%* | reverted |

*v10 measured on a held-out 16; its like-for-like predecessor scored 62%.

*v3 measured on the full cohort before exemplars forced a held-out split.

The two that worked were **structural** (put the eight-slot walk in the schema)
and **demonstrative** (show worked verdict sheets). The three that failed were
all **prose rules**. v9's diagnosis was sound — every residual disagreement is
a consequence slot, and it did move slot detection 37 → 39 of 41 and bias
+0.31 → +0.16 — but the extra failures landed on the wrong slots, costing two
cells and gaining none. Both failed attempts are kept as comments in
`rubric_h1.py`.

v10 tested the last plausible lever: a fourth exemplar demonstrating the one
failure mode the other three do not show — an answer whose antecedents are all
handled and whose three losses are entirely on the consequence side. It was
chosen to hold the demonstration set's balance at exactly 62.5% met, which had
been the suspected cause of v8's failure. It still lost 18 points of exact
agreement. **Three exemplars appears to be the working number for this item**;
a fourth dilutes rather than adds, whichever failure mode it demonstrates.

Q6 sits at 59% exact, MAE 0.60, +0.31 bias, and is the sole source of
participant-level bias on this handout. Four of six calibration attempts have
now failed, three of them consecutively. I would stop tuning it and treat its
`escalate` flag as the mitigation: at 88% within-tolerance the errors are
single-slot, and a human reviewing the flagged items catches them faster than
further rubric work is finding them.

**Seventh attempt, and the advice above still holds.** A ninth guidance bullet
was added — "A CHANGE TO THE ANTECEDENT, NOT A PLAN TO DO THE GOAL BEHAVIOUR" —
because participant 2's "listening to music as I work out" against an antecedent
of playing video games is exactly the failure the 2.5/10 exemplar demonstrates,
and neither the scorer nor the lo-blocks prompt was applying it. It fixed p2.

In isolation it also pulled p4 from +1.50 to +0.25 and p19 from +2.50 to +1.25,
taking bias to +0.07 — but it cost p3, a 10/10 response whose "by motivating
myself to get up and go, this will help me go to the gym" acts on the belief
while merely NAMING the gym. Adding p3 as a contrast case recovered it and kept
p2 fixed, at the price of most of the p4/p19 calibration:

    before the bullet     13/20   MAE 0.51   bias +0.39
    bullet only           12/20   MAE 0.45   bias +0.07
    bullet + contrast     13/20   MAE 0.51   bias +0.26   <- kept

Kept with the contrast case: a correct answer losing a point is the more visible
failure than residual leniency. But exact agreement is back where it started, and
three cells (p2, p3, p4/p19) sit on the same "does this clause act on the
antecedent" boundary that each edit slides between. That is what the four failed
attempts above look like from the inside, and it is a good reason to stop.

Six known, deliberate divergences from gold, all cases where the graders
applied their own written rule inconsistently and the scorer applies it
uniformly:

* `A_MISMATCH` on Q6, participant 9 — their 4a lists "thinking about exercising
  makes me want to go less to the gym" and "not going on a run with a friend",
  while their Q6 changes "using my free time in bed watching a movie or show":
  a third antecedent. The dictionary is explicit ("This is a different
  antecedent from what you listed in question 4a. The antecedents must match
  up."), so `state_a1` is a mismatch. Gold scored it met and deducted only for
  the missing second antecedent and second consequences. Found while measuring
  the lo-blocks prompts, which returned `mismatch` in five runs out of five;
  matching gold here would mean teaching the check to credit real mismatches,
  and cross-item matching is the most common deduction in this corpus.

* `A_NO_KEYWORD` on Q4a — the dictionary requires the word "antecedent" or
  "trigger"; participant 17 lost the point for omitting it, participants 9 and
  15 did not.
* `UTB_NOT_STATED` on Q1 — participant 20 lost 2 points for never naming the
  UTB, participant 17 did not, on materially identical responses.

* `A_NOT_ANTECEDENT` on Q4a, participant 14 — their first trigger is "not seeing
  immediate results, so I tend to bed rot", which the graders rejected along with
  their second. Gold is 1.0, i.e. both examples refused at 2 points each with the
  keyword point kept. But this item's own guidance says to accept generously when
  an example precedes the UTB and a reader can see how it leads there, and that a
  state of mind qualifies — which "not seeing immediate results" is. The lo-blocks
  prompt credited it in five runs out of five, with `antecedent_1: met` every
  time, so this is a stable reading rather than noise.

  Two things make gold the weaker side here. The guidance in this file cites p14's
  SECOND example as its canonical aftermath case and attributes the whole −4 to
  it, but −4 is two refusals at 2 points each, so the commentary accounts for one
  rejection while the score reflects two. And the first example is the kind the
  same guidance tells us to accept. Recorded rather than fixed: bending the
  accept-generously rule to this cell would cost the item elsewhere.

* `AVOIDANCE FRAMING` on DAY1, WK1 and WK2, participant 8 — the largest of these
  by cell count, and it was missing from this list until an audit of the H2
  example items went looking for a calibration gap and found a decision instead.
  Their contingencies are stated by what is AVOIDED ("so I don't have to do an
  extra 30 pushups if..."), which is structurally sound: a consequence is still
  arranged and still contingent. The graders read the phrasing as a failure and
  wrote "This is not an example of operant conditioning" on all three. score.py
  refuses to follow them — "flag for review, never deduct" — and attaches an
  advisory note instead; the lo-blocks sheet reaches the same verdict through the
  same criteria. So BOTH implementations are 4, 4 and 2 points over gold on these
  three cells, by design. Anyone measuring the OC items should subtract them
  before concluding the criteria are too permissive.

* `WRONG_DEFINITION` on D2, participant 11 — they chose Negative Reinforcement
  and defined it as "When you take away something desired, to decrease a
  behavior", which is Negative Punishment. The grader diagnosed it correctly and
  wrote "This is the definition of NP", but charged −1 and left the score at
  1.0; the dictionary puts WRONG_DEFINITION at −2. Both implementations score it
  0 — the scorer through WRONG_DEFINITION, the lo-blocks sheet through its
  `matches_chosen_type` gate — so both are 1 point under gold on this cell.
  Found while auditing D1/D2's arithmetic for a suspected olx/python divergence
  that turned out not to exist; this is the only D1/D2 row where the two
  implementations agree with each other and disagree with the graders.

One gold-label defect found while calibrating: participant 16's Q4c feedback
("did not say if this behavior is a good choice for you modify and why") is a
**Q4b** criterion, and that participant's Q4b is 5.0 with a blank cell — the
deduction was filed against the wrong column. Participant 2's Q4b score cell is
also blank though its feedback reads "-1.5 pts" (so it should be 3.5).

## Handout 2

`score.py --handout 2` and `baseline.py --handout 2`. Twelve items, 40 scored
points: four "write an example of PR/NR/PP/NP", then for each of two chosen
operant-conditioning types a type, a definition, a daily example and a weekly
example.

18 participants. v1 is the uncalibrated first run; v2 adds one calibration
pass on the six contingency-judgement items; v5 makes the operant-conditioning
determination schema-enforced and adds the avoidance-frame rule.

| exact | PR | NR | PP | NP | T1 | D1 | DAY1 | WK1 | T2 | D2 | DAY2 | WK2 | **all** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1 | 94% | 72% | 100% | 100% | 100% | 100% | 72% | 89% | 100% | 89% | 78% | 83% | 90% |
| v2 | 100% | 94% | 100% | 100% | 100% | 100% | 83% | 89% | 100% | 89% | 89% | 94% | **94.9%** |
| v5 | 94% | 94% | 100% | 100% | 100% | 100% | 89% | 89% | 100% | 89% | 83% | 94% | **94.4%** |

MAE 0.28 → 0.13 → **0.14** per item; participant totals MAE 2.83 → 1.61 →
**1.72** of 40, 78% within 2 points.

### v2 — calibrating the contingency judgement

The naming/definition items (T1, D1, T2, D2) were solved from the start at
89–100%. Everything else turned on one judgement made in six places — *is this
a real operant-conditioning contingency?* — so the calibration went into the
shared `_EXAMPLE_RULES` and moved all six at once. The largest single error was
over-applying "must be an external stimulus": the graders accept **removing an
unpleasant obligation** as a negative reinforcer ("I will not have to wake up
early"), and the scorer had been zeroing those. NR alone went 72% → 94%.

### v5 — enforcing the definition, and the avoidance rule

Example items are marked `derive_from_criteria`. The model no longer writes a
deduction list; it fills a required `oc_analysis` object naming the `behavior`
and `stimulus` and judging `contingent`, `follows_behavior` and
`stimulus_is_arranged`. `derive_oc_ledger()` gates on those: fail any and the
answer is NOT_OC whatever it looks like. Same lesson as Handout 1's Q6 — a step
the model must not skip belongs in the schema, not in prose.

**Avoidance-frame rule.** A contingency phrased by what is *avoided* ("so I
don't have to do 30 pushups if I miss it") is structurally valid but easy to
misread; the graders scored two of participant 8's at 0 for what is really a
phrasing problem. `avoidance_frame` flags it, forces `escalate`, and attaches
an advisory suggesting the direct phrasing — **never deducts**. It fires 9
times across the cohort.

Three further rules recovered regressions the enforcement introduced, each
from the handout's own instructions rather than from the labels:

* **Reinforcement must act on the WGB, punishment on the UTB.** "If I don't
  work out then I won't have to study more" is formally negative reinforcement
  — of the *unwanted* behaviour. `targets_intended_behavior` catches it (-2).
* **"Withhold X until B" is dual-describable** — as PR of B and as NP of not-B.
  Both readings are correct, so credit whichever type the student named.
* **Fall back to the definition when the type slot is blank.** Participant 15
  scored 0 on T2 but their definition states Positive Punishment plainly, which
  is what their weekly example must be judged against.

Net v4 → v5: three cells gained, one lost. The loss is participant 15's PR,
where `targets_intended_behavior` fires on "only allow myself to binge my
favourite show after I finish homework" — the reward is screen time, which is
that student's UTB, and the reinforced behaviour is not their WGB. The rule is
right; gold is lenient there.

**Not recoverable:** participant 14's DAY2. The same student's identical
"until" construction is scored 2.0 and 4.0 on other items and 0 here, so
matching it would mean reproducing an inconsistency.

### Corpus defects found in Handout 2

* **Participants 2 and 3 have byte-identical transcriptions** but different
  gold rows (p2: PR/NR/PP/NP all 4.0 with both definitions marked "did not
  answer"; p3: PR/NR/NP all 0.0). The transcribed text contains both
  definitions, so p2's gold row cannot belong to the file filed under p2. At
  least one of the two is mis-transcribed and neither can be attributed —
  both are excluded from the baseline via `suspect_participants` in
  `handouts.py`.
* **Participant 19's second daily example** is typed on the line *above* its
  "Daily Example:" label, so it segments into the definition instead. Gold
  gives it 4.0. This is the one extraction cell (of 240) that no ordering rule
  recovers; it is a student layout error, not a parser bug.

### Backend note — concurrency

The 240-call H2 run at 8 workers lost **118 calls** to a transient
`claude exited 1` with empty stderr: rate limiting. `ClaudeCliBackend` now
retries 3 times with exponential backoff and jitter (the previous single
immediate retry was not enough), keeps stdout in the error when stderr is
empty, and `score.py --retry-missing` re-scores only the cells a previous run
left null. Keep `--workers` at 4–6 for a 12-item handout.

## Handout 3

`score.py --handout 3`. **Item ids are the handout's own printed numbering —
`1a`, `1b`, `1c`, `2a`, `2b`, `3` — with no `Q` prefix.** Handout 1 already
uses `Q1`–`Q6`, and an earlier scheme gave Handout 3 ids like `Q1a` and `Q3`,
which collided with Handout 1's `Q3` and made reports ambiguous to read. There
is no item 4 or 5 in this handout: its numbering is question 1 in three parts,
question 2 in two parts, and question 3. Six items, 40 scored points. v1 is the first run, v2
fixes the graph/description confusion on 1c, v3 calibrates 1a and 2a:

| exact | 1a | 1b | 1c | 2a | 2b | 3 | **all** |
|---|---|---|---|---|---|---|---|
| v1 | 75% | 100% | 85% | 70% | 100% | 95% | 88% |
| v2 | 75% | 100% | **95%** | 70% | 100% | 95% | 89% |
| v3 | **95%** | 100% | 95% | **90%** | 100% | 95% | **96%** |

MAE 0.22 → **0.08** per item, bias +0.03. Participant totals MAE 1.10 →
**0.50 of 40**, 90% within 2 points, no exclusions — at the time, comfortably
the best of the three handouts. It no longer is: handout 3 now measures 94% with
participant MAE 0.75, while handout 2 reads 96% adjusted. Handout 3's 1c and 2a
both moved after the reconstruction and counted-group work of 2026-08-12, and 1c
is also the item where the SHIPPED model does worst — 40% against Opus's 90%, the
sharpest model gap in the corpus. See `out/SWEEP_2026-08-12.md`.

**Five disagreements remain out of 120 cells.** Two are Q2a cells the graders
marked down with no stated reason or with a reason the text does not support
(participants 13 and 16); the rest are single-slot judgement calls.

### v3 — what calibrating 1a and 2a changed

Both items were over-strict, in mirrored ways.

*1a* was demanding one sentence per week. The graders grade **the arc, not the
sentence count**: an answer giving the before-state and then how the behaviour
changed across the intervention earns all four slots even when the weeks are
not enumerated. Deduct a week only when a period is specifically absent — the
observed case is an answer that opens at the intervention and never mentions
the baseline. 75% → 95%.

*2a* was counting sentences rather than content. Two sentences can earn all six
points when they state the outcome and explain it. The deduction is for a
stretch that does not bear on how the plan succeeded or failed — participant 1
lost 2 points for a sentence about their stomach being unsettled. 70% → 90%.

### Item 1c is scored from a graph, not from text

Ten of the forty points. `graph_bundle()` in `score.py` assembles whatever
evidence exists and the item is scored by the same slot-walk used for Handout
1's Q6, with five 2-point slots: having a graph, title, x-axis label, y-axis
label, legend. Four representations occur in this cohort:

* **OOXML chart part** — title, axis titles and legend read straight out of
  `word/charts/chartN.xml`. No model judgement needed for the labels.
* **Embedded image** — `Read` is enabled for this item only (`allow_tools`),
  and the model looks at the extracted PNG. It correctly reported participant
  8's title as the literal default `Chart Title`, which is why that student
  lost the title point.
* **Grouped drawing shapes** — the labels arrive as run-together document text
  (`Excersing Over Four Weeks2.521.510.50 Sunday Monday...`).
* **Nothing.**

Two traps, both of which cost points if missed:

1. **The blank handout ships its own worked example graph** ("Water
   Consumption Over Four Weeks"). Several students left it in place and added
   nothing. `graph_evidence()` labels each chart part `student` or `template`,
   and `has_own_graph` is a **gating** slot: fail it and the whole item is 0,
   matching the grader's "Did not provide a graph" on participant 4 — whose
   file *does* contain a chart.
2. **A written description of a graph is not a graph.** Participant 20 typed
   "Title: Sleep Duration Over 4 Weeks / X-axis label: Days / Y-axis label:
   Hours of Sleep / Legend: ..." with no plotted data, and their only image was
   the template's example. The first run credited this 10/10; naming the
   distinction (tidy `label:` prose versus tick values jammed into the text)
   fixed it and took 1c from 85% to 95%.

Axis *labels* versus axis *tick values* is the most common real deduction —
nine of twenty gold rows lost points for a missing axis title.

### Extraction

Handout 3 has the messiest layouts in the corpus, and three submissions needed
structural handling rather than a marker tweak: participant 16 rewrote the
handout with `1.a`-style numbering and no "YOUR" headings; participant 13 typed
over the template's worked example instead of under "YOUR 1b."; participant 8's
question 3 lost its "3." prefix and carries the answer on the question's own
line. The fixes are all in `segment.py`: repeated marker ids so `1b.`,
`EXAMPLE OF 1b.` and `YOUR 1b.` all feed the same bucket, `strip_template_prefix()`
to cut a printed question off the front of an answer, and a `join_aware` mode
that recognises a run of template lines collapsed onto one line. After them,
**zero cells extract empty where gold awarded points**, across all three
handouts.

## Measuring the lo-blocks prompts (`agreement.py`)

The handouts also exist as web activities, authored in `../psychology/`
and run by the lo-blocks engine at `$LO_BLOCKS`, where
`<LLMAction>` blocks give formative feedback on screen. Those prompts were
calibrated by copying findings out of this project, and nothing checked whether
the copy worked. `agreement.py` checks it, against these same gold rows.

It is possible because those prompts now declare their checks as a `slots`
sheet — a strict JSON schema — so the model returns a comparable verdict object
instead of prose. The harness reads each `<LLMAction>` straight out of the .olx
(so it measures what ships, not a copy), fills its `<Ref>`s from a segmented
paper submission, calls the same endpoint the browser calls, derives a score
from the verdicts using the rubric's own point values, and compares.

Scoring happens in the harness only. The student-facing blocks must not score
and do not; a score is simply the one thing gold offers to compare against.

```bash
python3 agreement.py --handout 1                 # Q6
python3 agreement.py --handout 2 --items PR NR
python3 agreement.py --handout 1 --backend cli   # same prompts, different model
```

### First results

Handout 1 Q6, the same held-out 17 this project reports v7 on:

| Q6 (n=17) | this scorer, v7 | lo-blocks prompt via python | lo-blocks prompt via the app |
|---|---|---|---|
| model | claude-opus-5 | claude-opus-5 | gpt-5-mini (Azure) |
| exact | **59%** | 47% | 47% |
| MAE | **0.60** | 0.87 | 1.09 |
| bias | +0.31 | **−0.13** | +0.38 |
| failed slots found (of 41) | 37 | 43 | 36 |

Two readings, and the second is the useful one. **Slot coverage transferred**:
36–43 of the 41 failures the gold scores imply, against 31 of 50 before this
project moved its own checklist into a schema. That was what the schema was
for, and it worked on the other codebase too.

**Exact agreement did not transfer.** 47% against this scorer's 59% — and it is
47% on *both* models, so the binding constraint is the prompt, not gpt-5-mini.
The scorer's prompt carries the full deduction table and per-slot guidance; the
OLX prompt is written for a student audience and carries less. That gap is now
a number instead of a guess.

Handout 2, PR and NR, 18 participants, via the python scorer:

| | PR | NR |
|---|---|---|
| exact | 78% | 72% |
| MAE | 0.67 | 0.56 |
| bias | −0.67 | −0.33 |

against 94% for both in this project's v5 — and the negative bias says the olx
prompt is **harsher** than the graders, the opposite of the leniency this
project fought on Q6.

One concrete bug fell out immediately. Participants 5 and 6 scored 0 on PR
against a gold 4.0, and both verdict sheets read `names_behavior: no` while
also reporting `observed_type: PR` — self-contradictory, since an example
cannot be Positive Reinforcement without a behaviour to reinforce. The
`names_behavior` gate is being read too literally against answers that refer to
the goal behaviour indirectly ("if I meet my goal, I will ..."), and because it
gates, one wrong verdict costs the whole item. Fixing it is prompt work, and it
should be re-measured here rather than assumed.

## Out of scope

**The upload points.** Handout 1 is 50 points: 45 across these 8 items plus 5
for uploading photos of the handwritten pages together with a typed copy. That
is a Canvas submission fact, not a property of the response text, and it is
recoverable from nothing in this directory — there are no handwritten scans
here (the only raster image across all 60 submissions is a 118×24px yellow
highlighter blob), and the workbooks have no upload column, hidden sheet, or
cell comment. `upload_points` is emitted as `null` for a human or a gradebook
export to fill in.

**Handout 1's "underline your UTB" instruction.** Only 6 of 20 transcriptions
preserve the markup, so `utb_format_hint` is passed to the prompt as weak
corroboration and the UTB is read from prose.

## Backend note

This machine has no `ANTHROPIC_API_KEY` and no `ant` profile, so the default
backend drives the locally authenticated `claude` CLI with `--json-schema` for
structured output. Two things that path requires: tools must be denied
(`--disallowed-tools`), or the agent reaches for one, burns its turn, and the
call dies with `error_max_turns`; and `--bare` cannot be used, because it skips
the keychain read and the CLI ends up unauthenticated.

For production use `--backend api`, which calls `claude-opus-5` through the
official SDK with adaptive thinking, `output_config.format` structured outputs,
and `cache_control` on the rubric-bearing system prompt.
