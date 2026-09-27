see: qc:QC.0 end

**Worked from this course.**

Written 2026-08-20 after a full QC pass on one item, H1 Q6, which went from a partly-understood 16/20 to 17/20 with every remaining disagreement declared and explained.

**`leakage.py` runs before every sweep, and `agreement.py` REFUSES to sweep handout 2 while any rule block echoes the cohort without a recorded verdict.** A rule that borrows a student's sentence scores the cell it was copied from and proves nothing about the criterion; worse, the sentence is almost always taken from the very cell the rule was written to fix, so the gain it reports is circular. This is not hypothetical here. Two recorded gains were found to rest on quoted prose *after* they had been measured, reported and committed:

* DAY1's avoidance-framing rule contained [[corpus DAY1/p8 day1 75:104 sha=3d615ba39d28]] — DAY1/p8 with "30 pushups" changed to "the extra chore". p8 is the cell that rule took from 0/9 to 9/9. * WK1's agent rule contained [[corpus WK1/p1 wk1 48:87 sha=9acb583a85f7]], which is WK1/p1 verbatim, and "the extra laps will keep stacking up", which is WK1/p8 with the noun swapped. The item had been recorded as perfect on that rule.

The two cases then came apart under measurement, and the difference is the lesson. DAY1 held its number with the borrowed sentence replaced by an invented one: that rule was a real criterion. WK1 did not — it lost p7, and p7 is the cell whose configuration a `trigger_behavior` note had described in PARAPHRASE. p1, whose sentence was reproduced word for word, held. So the verbatim quote was not the load-bearing one; the described cell was. That is the form neither the n-gram check nor the bigram check can see, and it is the one that mattered.

WK1's agent rule had "the extra laps will keep stacking up" swapped in for the student's noun, and "stacking" is WK1/p8's own verb, in the verb list the gate matches on, in the cell the gate was built for. The same sweep found "my brother will..." (DAY2/p12) and "procrastinating" (the word whose paraphrase had already cost WK1/p7).

The single-word check flags a word that (a) appears in a few students' answers, (b) is absent from the handout and the type definitions, and (c) appears nowhere else in our own prose — that last clause being what separates "phone" from "activity". It is noisier than the bigram check by design: of 26 blocks flagged on its first run, 2 were faults and 24 were ordinary English or the instrument's own examples.

The worst form is not a quoted phrase but a described cell WITH ITS GRADE attached: "against a screen-time goal, gating the screen activity on finishing coursework earned full credit", or "cost participant 10 two points".

None watched what they stopped saying, and that is how NR/p14 was lost: `barrier_is_not_this_type` was added in the morning to win that cell (14 -> 16), removed the same day as superseded by `stimulus_move`, and the cell fell from 6/6 to 0/6 with every remaining check on its sheet passing. The loss appeared only as a median two cells down, three sweeps later.

Exit 0 from the wrong command was reported as a clean gate more than once in this project.

Every other stable miss in this corpus is off by one deduction step, which is what a criterion boundary looks like; these two shapes are what a box holding the wrong text looks like. That check removed four of seven candidates on first run, including one this session had already called a probable fixture defect out loud. It found three rows nobody had looked at, after D2/p11 and DAY2/WK1 p7 were found by hand.

It happened on 2026-08-23, on this guide, by someone who had read it. Seven handout-1 items were worked and closed — two criteria rewritten and measured, five declared — before any exclusion was retested. The audit then took minutes, because excluded cells are still run and still scored, and found EIGHT cells across five items that were wrong in 3 of 3 runs with the answer and the grader's decision sitting in their prompt. Q4c and Q5 had been reported as perfect items; they are 12/14 and 14/15. Every number reported before the audit was computed over a denominator the audit shrank.

A `CORRECTED_GOLD` entry was once argued partly on the grounds that an item's gold was incoherent, citing the very byte-identical pair whose contradiction is *why* both are excluded.

The expired-declaration check went in and within minutes offered to un-exclude PR/p2, a known mis-transcription, because it scored 3 of 3. The check now reads the kind and skips `suspect` entirely; `unscoreable` and `self_graded` still fire, verified both ways at 6/6.

Measured the hard way on 2026-08-24. Un-excluding Q1/p1 and Q2/p6 lit up quotes that had sat there legally for months.

**Measured on Q1, and it is worth knowing which direction the answer went.** Its five citations were bare attributions with a decision attached — "(participant 1)", "which is what participant 6 scored", "which is how participants 10 and 16 were credited". Deleting the attributions left every rule intact, which is the common shape and the reason the test is usually cheap. Three runs with the citations gone:

| | before | after |
|---|---|---|
| the 15 cells already counted | 13, 13, 13 | 13, 13, 13 |
| the five cited cells | 3/3 each | four still 3/3 |
| the whole item, 20 cells | not measurable | **18, 17, 18** |

So the citations were load-bearing for nothing, and the honest rate is 18/20 against a reported 13/15. **Five cells we score correctly had been subtracted from every rate on an untested claim.** An audit that only looks for exclusions hiding misses would never have found them, because there was no miss to find.

Of 34 exclusions audited on 2026-08-23, the 8 hiding misses were found and fixed the same hour; the 21 that were merely unnecessary were dismissed in a sentence, and finding them took a second pass and a second prompt.

see: qc:QC.what-is-computed end

**Worked from this course.**

The reliable/unreliable line in this project does not fall between the scorer and the reporter.

see: qc:QC.1 end

**Worked from this course.**

On 2026-08-24 a survey of WK1 was built with `sed -n '7p'` — the first response line of each cell — and p5 came back as [[corpus WK1/p5 wk1 0:61 sha=0b73ad1bff21]] On that basis it was reported as an answer gold credits with 4 while stating no consequence, no conditional and no contingency at all, and that single "fact" was used to argue that gold on this item was not reproducible by any rule, that no gate could ever match it, and that a declared divergence was therefore correct. The argument was written up and stated to the user.

p5 has a second sentence: [[corpus WK1/p5 wk1 61:164 sha=6473c5fa76bc]] A textbook weekly contingency. Read in full, the item's ten gold-bearing cells separate PERFECTLY on a single feature, and the rule that had just been declared unreachable was sitting in plain view.

**An item answered with a chart or a table is read by PROVENANCE, not by position.** There is no prose to locate a box in, so the question changes from "is this box cut in the right place" to "is this the student's value, or is it somebody's account of their value". 1c's three label boxes held the paper scorer's sentence about the label — `"Weeks" appears as a bolded axis title centred beneath the day tick values.` — in ten of twenty cells, which is the answer to the grader's own question sitting in the field it reads.

The last is the one worth the most and the one a per-cell fix list loses: 2a's audit repaired two boxes and its real finding was that every miss left in the item is the same +2.0 over-credit, which is a one-directional target rather than three unrelated cells.

see: qc:QC.a-rubric-edit-can end

**Worked from this course.**

**Handout 3's on-screen boxes are a reconstruction, and the rubric drives it.** The answer is one prose block; `score.py`'s counted-group distribution pulls the quoted spans out of the count slot's evidence and deals them to the members, writing the placeholder `f"{n} found"` where there are fewer spans than the count.

2a's first structural attempt removed that group. The distribution stopped, the placeholders were never overwritten, and five cells' boxes became the literal string `"2 found"`. A 120-call sweep then measured the item at 10 of 20 against a baseline of 15 and the change read as refuted — **it had never been tested.**

see: qc:QC.2 end

**Worked from this course.**

Pre-filling `matches_chosen_type` produced a confident report of a dead `equals` on D1/D2, and a "fix" to a scorer that was correct throughout -- the gate zeroes the item, as `before_after.py` then showed by refusing to call an identical result evidence.

Zero probes reads exactly like zero faults: two pick slots with empty `options` once made this check run no probes at all on D1 and D2 while reporting clean.

Both errors happened here on the same day. Q1's baseline had p17 wrong in 3 of 3 and a criterion rewrite was drafted for it; six passes said 4 of 6, the rubric had already recorded that cell as a model limit, and the "fix" would have re-litigated a settled question against an unlucky draw. In the other direction, Q4a's numerator fell by one in one run of three after eight citations were removed, on a single cell — small enough to wave through, except that this item's baseline spread was 0 cells, which makes a stable-right cell going 2 of 3 a change in the item's STABILITY rather than in its score.

On 2026-08-24 a scratch comparison of 1a printed `<-- LOST` for a cell that went 3/3 to 2/3 and `<-- gained` for one that went 1/3 to 3/3, and both were written up immediately — one as "a wobble inside the item's variance band", the other as "the rewrite fixed it" — with no probe run and this paragraph already in the guide.

Q2's p17 retired it within the hour. Across six sweeps that cell scores 10 of 18, and it has produced 0/3, 2/3 and 3/3 in both directions — three consecutive identical runs each way.

1a was reported at 18/20 off a sweep whose runs were 17, 17, 18 — the median was 17, and 18 was the flattering pick.

Corollary worth its own line: **check a suspicious cell against every artifact that ever measured it, not just the previous sweep.** p17's six-sweep history took one query and settled in seconds what a fresh probe would have spent 24 calls on — and it answers a question a probe cannot, which is whether the cell was ever stable in the first place.

**Compare against the RECORDED state, not only the old baseline.** A diff against a stale baseline cannot see a gain being undone: DAY2/p8 was 0 of 3 in the baseline, was fixed to 5 of 6 by a committed change, and was knocked back to 0 of 3 by a later edit that never mentioned the gate it moved — and the comparison read "no change", because both ends were 0 of 3.

A question about the PLAN invites the model to weigh the whole answer: "is a consequence delivered?", "does this target the student's own behaviour?", "is this really operant conditioning?". A question about the SENTENCE has one: "find the clause that states the consequence; is a person in its subject position, and does its verb say that person brings the thing about or takes it away?" That is a parse, and parses do not wobble.

The same criterion asked syntactically put the target at 6 of 6 and the neighbour at 6 of 6, both correct, controls holding, and the item went 15/18 to 17/18.

- **A closed list in a rule is a boundary you are promising to defend.** The first syntactic version listed transfer verbs — give, buy, treat, withhold — and so excluded [[corpus WK1/p1 wk1 48:87 sha=9acb583a85f7]], a student granting themselves a privilege, putting a correct cell at 3 of 6.

Eight `self_graded` exclusions were removed and the citations that justified them came out of the prompts, which meant deleting worked examples from Q4a, Q4c and Q5. Re-deriving from the pre-change runs put the numerators at 12, 12 and 14 — unchanged BY CONSTRUCTION, since the newly counted cells were the ones already known to be wrong.

Done on 2026-08-24, by someone who had deliberately waited for two earlier runs to clear for precisely this reason. Handout 3's 1a baseline was 40 cells of old prompt and 20 of new, and the two items queued behind it would have measured the NEW prompt as their baseline.

Swapping a real quote for an invented one of the same shape is a rewrite of the only concrete example the grader has for that slot, and concrete examples are what these prompts run on — handout 1's Q4b lost six cells to a rewrite that replaced examples with abstractions, and got them back only when invented examples went in. Cleaning three leaked quotes out of 1a's period slots is the same operation on an item whose own code comment records those slots as variance-sensitive.

Q1 had five exclusions removed and six citations rewritten into rules in one commit and was never swept afterwards; its number was carried forward by re-derivation from a sweep that predated both changes, and an audit five commits later is what found it.

An item may declare `pending` with a reason instead of a measurement — the usual bargain in this project. What it may not be is absent, which is the state Q1 was in, and the state the check refuses.

see: qc:QC.2a-1 end

**Worked from this course.**

| the edit | what it ate | how it was found |
|---|---|---|
| rewrite `GOLD_CODE_KNOWN`'s NR/11 entry, sliced to "the next dict key" | the closing brace, a comment, and `GOLD_SLOT_BOUNDS_KNOWN`'s declaration | a NameError in `--preflight`, days later |
| the same slice | `GOLD_SLOT_BOUNDS_BUDGET` | the next `--preflight` run, after the table had been "restored" |
| replace `probe.py`'s helpers, sliced by index to the next anchor | `_slot_aliases`, `_OPERANT_GATE` | seconds, by luck: the next command imported the module |

see: qc:QC.2a-4 end

**Worked from this course.**

This caught the same person twice on 2026-09-07: subgoal E45's closure dropped Q5/p9 that way, and subgoal Q19's dropped six cells, TWO OF THEM WRONG.

**And do not answer it with a regex over the entry's prose.** Tried the same day, repeatedly, and wrong every time: a pattern over `Item/pN` citations said Q16, Q18 and Q33 named 1, 2 and 6 cells and that none of ten at-risk cells was among them -- preflight named all ten within minutes; it said only WK2/p15 was sole-owned by E55 and missed PR/p15, a WRONG cell; and it said WK2/p8 was sole-owned by Q40 when subgoal Q55 names it too.

**A cell can also be orphaned by getting BETTER.** Q4b/p1 improved from 6 of 12 to 11 of 12 in a re-sweep and lost its owner, because the entries discussing it were discussing a 6-of-12 cell.

see: qc:QC.2a-3 end

**Worked from this course.**

Do not write a regex over prose to re-derive what a checked, fire-tested reader already computes. The user made this standing procedure on 2026-09-07, after three nonce classifiers of mine were wrong in a single afternoon and each one produced a confident, actionable, false answer:

| nonce classifier | what it said | what was true |
|---|---|---|
| regex for gold's change-box charges (`did not say how`) | Q6/p1 and p6 are charged on that axis | neither is -- p1's four charges are all about CONSEQUENCES, p6's are matching-4a. p6 is the exact cell a clause of mine had broken, and the classifier would have justified breaking it |
| regex for "avoidance wording" in Q4b's behaviour boxes | 14 of 19 cells name an avoidance | the item's own TEMPLATE is "When I am not exercising, I am ..." -- the flag was matching the scaffold, not the entry |
| regex for `Item/pN` citations, to find which goal owns a cell | Q16, Q18 and Q33 named 1, 2 and 6 cells, none of them the ten at risk | entries cite cells in per-item TABLES ("p10  gold ...") under an item heading, which the pattern cannot see. Closing those three orphaned TEN cells, and `--preflight` step 5e named all ten within minutes |

**A PRE-REGISTERED SET IS A CLASSIFIER TOO, and typing it out by hand is the nonce version.** Added 2026-09-07, after a Q4c probe hand-typed its own falsifier set and its own excluded list as literals in the script and got two things wrong at once:

* It called **`handouts.suspect(1)`** for the dropped cells. That reader answers *"participants whose input cannot be trusted, **whatever the item**"* and returns `[]`. Q4c/p16 is dropped PER ITEM, and only `exclusions(item)` sees it, so the probe ran 20 cells while calling it 19 and quoted an excluded cell. **Across all of handout 1, Q4c is the only item where the two readers disagree** — which is exactly why this survived: it is invisible on every other item. * It listed **Q4c/p4's first box as gold-credited**, so the rule firing there read as a cost. Gold charges that box in its own words — *"specify what spending too much time awake means as a consequence"* — and we already answer `wrong_kind` on it 9 of 12 runs.

**Pass the slot.** `probe_falsifiers(item)` alone still lists the TARGET cell whenever some *other* slot of it is credited — Q4c/p9 is a key there, because gold charges both consequence boxes while its two remaining slots are fine.

see: qc:QC.2a-1c end

**Worked from this course.**

**What it cost, 2026-09-07.** A script listing the queued probes did `sys.path.insert(0, SCRATCHPAD)` then `import enforcement`, and got a 09-05 copy **1425 lines shorter** than the live module.

see: qc:QC.2a-1b end

**Worked from this course.**

**None of them asks "is this the right PROMPT."** On Q4c the shipped assembled prompt is 9438 characters carrying twelve checklist lines — both consequence slots, the `keyword` advisory, the `no_consequences` gate, five deduction codes including the `C_NOT_CONSEQUENCE` charge gold actually levies on the target cell, and a `confident` slot. The `consequence_1` rule text is 1085 of those characters: **eleven per cent.** A probe that hand-builds an envelope around the correct string is asking a different question, and it will answer it confidently.

**What it cost before the guard existed, all on 2026-09-07.** A retrospective gate over the recent probes (`scratchpad/retro_gate.py`, no calls) put **six of seven readable ones VOID**:

| probe | non-target cell-slots that disagree with the ledger |
|---|---|
| Q44 route 5, subtract duplicate reasons | 8 of 19 — and the TARGET too: its envelope counted p6 at 4 where the shipped prompt counts 3 (8/12), so "does subtracting one duplicate take p6 from 3 to 2" was untestable in it |
| Q44 earlier, the reasons count | 3 of 19, two at 12/12 |
| Q40's `aimed_correctly` first text | 2 of 17, both at 12/12 — **but a SWEEP settled Q40** (WK2/p11 4/11 → 12/12), so the conclusion stands on sweep evidence, not on this probe |
| Q47 engagement wording, 1st | 4 of 38 |
| Q47 engagement wording, 2nd | 2 of 38 |
| Q47 `change_a*` mirroring `affect_c*` | 2 of 10 |
| Q47 engagement wording, 3rd | **0 of 38 — clean** |
| Q56's habit head | 1 of 38 — p11/`consequence_2` `met` against the ledger's `duplicate` 12/12, on a cell no candidate touched. Independent of the A/B that first exposed it |
| Q19's consequence boundary | 1 of 17 — the same p11 duplicate |
| Q19's two Q4b report-slot arms | **NOT GATEABLE** — they probe CANDIDATE slots reverted out of the tree, so the ledger has no baseline (36 cell-slots of `None`). A probe of a NEW slot must be gated on an EXISTING slot measured in the same call |

Q44's fifth route is **unmeasured, not dead**.

see: qc:QC.2a-2 end

**Worked from this course.**

**Read gold's charge on EVERY valid cell of the item and write the two sets down -- the cells gold charges on your criterion, and the cells it credits -- before you word anything.** It costs no calls, it is the only thing that tells you what the rule is allowed to do, and on 2026-09-07 the user made it standing procedure after three edits in one day were measured against hand-picked cell sets.

**What a hand-picked set hides.** Q19's report slot was probed on six cells, passed, swept, and fired on FOUR MORE the probe had never looked at -- p13, p16, p20, p8 -- one of which (p13) fell 4/12 to 0/12. And the same free readout showed gold names that criterion exactly ONCE in the item, on p4, which is a standard no probe can give you.

**Read the FULL gold text, never a summary and never a keyword match.** Two errors in one hour, both mine, both from not doing this: * Reading truncated one-line notes, I told the user "gold never charges that the change is inadequate" on Q6 -- and Q6/p2's full note says the opposite in gold's own words: *"{{corpus:Q6/p2:affect_c2:3:39:sha=7bc493d62ecd:shape=C1}} does not change your {{corpus:Q6/p2:state_a2:17:69:sha=e9b581bb54c5}} stop."* * A regex for change-box charges matched `"did not say how"`, which also appears in CONSEQUENCE charges, so p1 and p6 were reported as charged when neither is. p6 is the exact cell a clause of mine had broken; the classifier would have justified breaking it.

**Bought on 2026-09-07, in the same hour.** A rescore was proposed for Q6/p8 to bring it to gold's 2.5 -- and `A_NO_CHANGE` already declares OUR credit to be the reading we endorse, gold having applied the item's pedagogical point beyond the literal text. The proposal would have contradicted a standing declaration to chase a number, and it would have made a declared cell into a defect. Its neighbour p2 IS live, because p2 sits only in the ratchet table, which records a disagreement rather than blessing it.

see: qc:QC.2a end

**Worked from this course.**

Retyping is what cost the Q19 sweep: a probe passed 23 of 24, the slot then shipped with a `desc` that dropped the question's comparison clause and turned a yes/no into a which-one, and the sweep over-fired on nine cells.

**The failure a probe catches is REACH, and it is the common one.** On 2026-09-06 three edits were measured and reverted in one day, and none of them was wrong about the text:

| edit | what happened |
|---|---|
| Q45, `targets_goal_behavior` clause | target cell 5/12 → **5/12**; the clause never fired |
| Q47's 11th, `change_a*_does` pick | fired, answered sensibly, sorted both targets into CREDITING categories |
| Q19, the repeats_antecedent value | target answered `activity` **12/12**; the new value never chosen, and it was reverted -- the name is unbackticked here because it no longer exists |

On 2026-09-06 subgoal Q19's report slot was probed with a carefully written question and then built with a `desc` that dropped its comparison clause and turned a yes/no into a which-one.

see: qc:QC.2b end

**Worked from this course.**

Structural fixes have worked in this project; wording changes mostly have not. Reach for prose only after a structural option has been tried or ruled out, and say which.

* **Q6** was fixed by ADDING A REQUIRED SLOT, after prose attempts failed. * **DAY1's `you_arrange_it`** absorbed four measured prose attempts, all neutral, all reverted. * **DAY2/p14** was fixed by the `forbid` PRIMITIVE -- a new rule shape -- not by re-describing the judgement. * **Q1's `reasons_given`** cost EIGHT configurations and ~550 calls of wording changes. p14 was won early (v1, 2/6 -> 6/6) and p9 never landed: 1/6, 3/6, 6/6, 3/6, 4/6, 2/6, 1/6, 1/6. The structural option -- ask `reason_1/2/3` SEPARATELY instead of collapsing them into one count -- sat unexamined the whole time.

Q1 is the clearest case: `counts=` forces one aggregate answer, so two cells needing opposite thresholds cannot both be satisfied by any wording -- that is arithmetic, not rhetoric.

* **2a** is now the longest record of this, and it confirms the rule while correcting two things about how to apply it. Seven measured attempts took the item from 15 of 20 to a 19.7 mean.

see: qc:QC.the-recipe-book-which end

**Worked from this course.**

**The OR recipe is the one worth spelling out**, because it is not obvious and it is what 2a needed.

On 2a it produced the item's best measured result.

see: qc:QC.choosing-between-them-and end

**Worked from this course.**

It cost Q1 eight configurations and ~550 calls and 2a five cells. **And on handout 3 it also drives the FIXTURE**: score.py's counted-group distribution rebuilds the on-screen boxes, so removing a `counts` group changes the INPUT. On 2a it made `BLANK`'s −6 impossible and the arithmetic audit reported `CANNOT ZERO`. This is the single distinction that cost 2a an attempt. * **Check the item's MARGIN before trusting a slot's stability.** Every gold row on 2a is 6 or 4, so a gold-4 cell tolerates exactly ONE charge: a second one overshoots however defensible it is. p14's `verdict` slot is 83% stable and that was enough to lose the cell in 2 of 12 runs, because `how_2` was already correctly charged.

see: qc:QC.read-the-excludeskeys-column end

**Worked from this course.**

On 2a I needed to add a computed condition to a slot the model judges, reached for `forbid`, found it would stop the model being asked that slot at all, and concluded the composition was impossible -- then fell back on prose.

see: qc:QC.a-disjunction-is-not end

**Worked from this course.**

2a's compound slot held a **disjunction of three alternative grounds**, and splitting it made the item WORSE the first time -- 20 to 19, with effective `how_2` accuracy falling from 96.7% to 93.3%, twelve false denials against six.

see: qc:QC.2c end

**Worked from this course.**

The case that produced this rule: Q1 was worked for a day on its merge rule, across eleven configurations and roughly 900 calls, because three misses looked like merge failures.

see: qc:QC.and-profile-the-grounds end

**Worked from this course.**

2a is the case, and it cost two attempts.

p16 (gold 4, must be charged): absent 12/12 on EVERY ground p10 (gold 6, must be credited): 3/11, 1/12, 4/12 — no ground at all

Asked separately the model was **unanimous and correct** about p16, which the compound question got wrong 5 times in 12. What the split actually cost was p10, whose only real ground is a bare directional change that `states_size` did not admit.

That last one is the p10 check, and it is the one that says a split is unsafe before it costs a cell.

see: qc:QC.its-companion-refusals-which end

**Worked from this course.**

Q4c's second box had 15 refusals and all 15 sat in wrong cells, which reads as a rule that never fires correctly — but 12 of them are one participant where gold charges BOTH boxes, so the refusal is right and merely incomplete, and crediting the box moves the cell further from gold.

On Q4a, Q4b and Q4c it returns ZERO contradicted refusals: every refusal gold has an opinion about, gold agrees with, and the apparent collapse is entirely gradient cells plus silent full-marks rows.

see: qc:QC.2d end

**Worked from this course.**

2a recorded **20 of 20** on a sweep whose twelve runs scored `18 18 18 18 18 18 19 19 20 20 20 20`: median over actual runs **18.5**, mean **18.8**, six runs at 18, only four perfect, and two cells right in 7 of 12.

**Quote the range and the mean beside any median.** They differ by 1.2 cells on 2a, and the mean is what a student would actually get. 2a's honest progression is 15 → 18.8 mean, not 15 → 20.

see: qc:QC.2e end

**Worked from this course.**

The case: Q1's `reasons_given` absorbed ELEVEN configurations and ~900 calls in one day, aimed at a merge rule.

* gold's rule is **CONDITIONAL** -- reasons are HARMS of the unwanted behaviour, and stated benefits are credited only where a response offers no harms at all; * every cell with gold < 3 was already classified: "p6 has exactly one harm among four background statements and two goal-benefits and scores 1; p9/p10 have no harms and 2 benefits each and score 2; p16 has none and one benefit and scores 1"; * **p9 was already diagnosed and not as a merge problem** -- "the model reads 'have unwanted complications...' as a harm, so `harms_listed` is 1 and tier one applies, giving 1 where gold wants 2".

The first change of the day replaced that conditional with a flat sum, which is why p6 went 4/6 -> 0/6 and never recovered under any later wording: a measured reconstruction of gold's structure was deleted as if it were a defect.

see: qc:QC.2f end

**Worked from this course.**

Its first automated run found five cells the python gets right and the OLX gets wrong — DAY2/p8, PR/p15, Q2/p18, Q4a/p9, WK2/p8, all six runs on each side — which no amount of diligence on a one-sided reading could have surfaced.

This arm closed Q11, whose `realistic` over-charge had gone.

Body mentions are routinely history or controls — Q19 names 1a/p15, Q4a/p20 and Q4b/p8 BECAUSE we score them right — so the strict form is used for the "evidence has moved" arm and the generous form for ownership.

see: qc:QC.2g end

**Worked from this course.**

Q32 was filed as "five cells the python gets right and the olx gets wrong" and measured out as ONE divergence and four coin flips:

cell gold python matches olx matches medians DAY2/p8 4.0 3 of 6 2 of 6 python 4 / olx 0 PR/p15 4.0 3 of 6 2 of 6 python 4 / olx 2 Q2/p18 4.0 3 of 6 2 of 6 python 4 / olx 2 WK2/p8 0.0 5 of 6 3 of 6 python 0 / olx 2 Q4a/p9 3.0 0 of 6 6 of 6 python 5 / olx 3

* **Compare `refers_to` as well as the verdicts.** WK2/p8's olx runs have IDENTICAL verdicts and scores of 0, 0, 2, 0, 2, 4: the movement is entirely in the classification answers, `observed_type` and `restriction_authored`. * **The direction can invert.** Q4a/p9 was python-right/olx-wrong until an unrelated slot left the sheet under E25, and is now olx-right/python-wrong, 6/6 stable both ways.

see: qc:QC.2h end

**Worked from this course.**

`agreement.cheap_checks_gate` is the structural suite and both harnesses now run it -- the app side did NOT until 2026-09-03, which meant a finding that stopped one engine silently let the other through.

see: qc:QC.2i end

**Worked from this course.**

On Q22 the list of eighteen cells where the gate fired turned out to be:

**NAME THE CELL AND THE SLOT, NOT THE COUNT.** A subgoal entry that says "we fail `you_arrange_it` on p11" cannot go stale. One that says "34 refusals, 71% precision" always can, because it is a claim about what a program computed and the program changes. Fourteen such figures in this project were left standing by a single instrument fix, and the only record of why they were suspect was a paragraph inside one subgoal -- which would have died when that subgoal closed.

Reading "you should state what you take away at the end of the week" as a cadence objection invented a false negative that was not there; the charge was "this is not an example of operant conditioning" and nothing else.

see: qc:QC.2k end

**Worked from this course.**

This project keeps most of its facts in several parallel sources of the same shape -- three gold sheets, four ledger sides, two scoring artifacts, a rubric and the .olx generated from it and the idmap dumped from that.

see: qc:QC.2l end

**Worked from this course.**

**Q22's cadence rule died in the BREAKS column, on the fourth item read.** The rule was "a period coarser than the item's frame contradicts it; a finer one does not; a period on the consequence is not the behaviour's cadence; no period stated is not a contradiction". It was derived from the eight cells where gold's comment speaks to cadence and it classified all eight correctly -- which is exactly why it looked finished.

* broke **DAY2/p9** ([[corpus DAY2/p9 day2 0:95 sha=4f42e6b8fa63]]), where gold gives FULL credit and the current check answers `met` in 12 of 12. The rule reads "out of the 5 days" as coarser than daily and would refuse it -- turning a perfect cell into a wrong one. Its near-twin DAY1/p9, by the SAME participant, is the rule's proof case. * risked **WK1/p6**, right in 12 of 12 today and held there by a cadence refusal gold never asked for -- gold objects to the contingency's direction.

On Q22 that question had an answer, and it took about ten minutes. The directional rule died on DAY2/p9 against DAY1/p9 -- and those two cells are the SAME PARTICIPANT writing on two items, which is what made the comparison sharp. "5 times out of the week" cannot be judged until occurrences are COUNTED across the week; "out of the 5 days" names no count and is judgeable on any one day.

see: qc:QC.2m end

**Worked from this course.**

* **the arithmetic audit refused an `onlyif`** with `2a CANNOT ZERO`: the guard capped the slot floor so `BLANK`'s −6 became unreachable.

* the slot-set audit reported `1a/p15` as disagreeing with gold on a GATE that gold's phrase table cannot name -- a difference guaranteed before the cell was read (see §2k).

**A GATE'S SILENCE IS NOT A CLEARANCE, which is the converse and the easier half to forget.** On 2026-09-04 two examples were written into the cadence rule that paraphrased the very two cells the rule targets — a numeral spelled out, a preposition swapped — and `leakage.py` passed them.

see: qc:QC.2n end

**Worked from this course.**

Two of the nine self-test fixture declarations were tested as CLAIMS on 2026-09-20, and both were false while their keys were perfectly valid:

see: qc:QC.3 end

**Worked from this course.**

Q3's `action_oriented` is the case that earned the rule. The three misses -- p8 "hours I can make", p16 "hours I have", p19 grounds it in measurability -- all justify actionability with something that is not a doing, which points straight at demanding a doing. That change would have cost THREE cells: p9 is credited on "a car", p14 on [[corpus Q3/p14 action 90:114 sha=d4443bb53f34]], p18 on "{{corpus:Q3/p18:action:71:97:sha=4b1ed59f418c:shape=S2-0a}} gym", none of which names a doing either. The sixteen credited rows are what contain the actual rule -- an activity OR access to a place or thing, never available time -- and narrowing to that took the item from 16/20 to 18/20 with all five guards holding at 6/6.

The same reading was what closed Q4a: gold's rejections there quote their own test ("how does grumpy emotions LEAD TO lack of sleep?"), and it was the credited rows that showed p14 and p19 to be gold departing from that test in opposite directions -- a pair no criterion can satisfy, so a declaration rather than a rule.

And it prints the grader's comment, because the grouping is a heuristic on the criterion's own words: Q4a/p17 says 'did not use the word "antecedent"' and lands in the CHARGED group while being a KEYWORD charge.

The `restricts` block, about twelve lines, cost DAY1/p11 and DAY1/p14 a run each. Removing `consequence_valence` and the twenty-line put-on/taken-off block that existed to answer it gave both back — 2/3 to 3/3 each — and moved WK2/p15 1/3 to 2/3 as well.

Every failed attempt on the four cadence items added words; the change that finally recovered two cells removed them.

**Distinguish three kinds of "and then what follows" in a reference entry.** For "X, so I Y": Y restating X, Y an INTERMEDIATE step that still leads to the unwanted behaviour, or Y a consequence.

**A quote is necessary and not sufficient; the equivalence rule must be CLOSED.** WK1/p7 took five measured versions and the sequence is the lesson. Its trigger is "{{corpus:WK1/p7:wk1:12:43:sha=5e1f6a6d53e1}}"; the student's UTB {{corpus:Q1/p15:response:28:56:sha=05cc40e7a636:shape=R3-1-2253}} electric devices"; gold charges -1 and says so outright. `trigger_behavior` answered `utb` for eleven attempts.

p7 3/3 -- the first version to hold the cell while admitting paraphrase. But hoisted to the front of the prompt it reached criteria it should not govern and cost three cells: "{{corpus:WK1/p17:wk1:18:42:sha=a4f361ff9914:shape=S1-0a2020}}" stopped matching "exercising 3-4 times a week", and it swallowed the pointer rule whole.

18/18, no cell changed against v3, p7 3/3.

**Placement cuts both ways.** Section 3 has long said position beats content, on Q6's evidence. WK1 shows the cost side: `MATCH_DEF` is emitted immediately before the components that use the term, and moving the equivalence rule there from a slot note is what let it override the pointer rule.

What it caught immediately: of eight moved cells across DAY1/DAY2/WK2, six came back 4/6 to 6/6 -- noise -- one improved from 0/3 to 4/6, and the only genuinely unstable one had measured 3/6 under the PREVIOUS configuration too.

**State a matching rule ONCE.** `olx_prompts.EQUIVALENCE_DEF` is now shared: Q6 asking whether a box matches a listed entry and WK1 asking whether a trigger names the activity the student chose are one operation. Q6 is not yet migrated onto it -- that changes a measured prompt and needs its own sweep.

see: qc:QC.4 end

**Worked from this course.**

**Qualifies:** a second antecedent that does not exist in the document; an antecedent appearing in no listed entry; a consequence equivalence supplied by the student's own answer.

**Gold's ordinals are tallies, not indices.** "Second antecedent" means "the second one you named", not "box 2".

see: qc:QC.read-the-declaration-tables end

**Worked from this course.**

Three of five corrections written in one session landed on cells already declared: DAY1/p1 in `BEHAVIOR_NEVER_STATED`, NR/p4 in `NP_SHAPE_CREDITED_AS_NR`, Q4a/p19 in two entries. Each correction was built from comparator evidence by someone who did not read the declaration tables first — and `NP_SHAPE_CREDITED_AS_NR` is *named* for the finding the NR/p4 correction wrote up at length as new.

see: qc:QC.nothing-can-host-this end

**Worked from this course.**

This is the most repeated error in this project's records, and it always looks like a finished piece of reasoning:

* `keyword` was to be converted to `derived`, and the note read "score.py cannot compute a keyword match". * `named_type` was recorded as unmigratable because "no credit component exists to carry a `rule`".

"Migratable, costs a re-measurement of Q5" is a decision someone can take; "blocked" is one they cannot.

see: qc:QC.the-rule-every-declaration end

**Worked from this course.**

* `SCORING_DIVERGENCES` declared "Q4a's assignable slot points sum to 4 against an item max of 5" for hours after `max="5"` made it false.

Q6/p9 read "the error here is exactly -2.50" through every run that measured -1.25.

- the fixture hands the grader the wrong text, or splits it at the wrong boundary, so the two sides are not judging the same answer at all; - the box the rule reads is empty, or holds a neighbour's words; - gold's row does not reconcile with its own comment, making it a wrong NUMBER rather than a different judgement — D2/p11, DAY2/p7 and WK1/p7 were all found this way, and two of them had been declared or ceilinged first; - the criterion is unreachable as written — a verdict token the slot does not offer, a rule parked where only one generator reads it; - the item's own scoring layer makes the rule inert, which no amount of prose about it will fix.

WK1's divergence was defended on the strength of a neighbouring cell that appeared to have no contingency, read from its first line alone — and that cell's second sentence is a textbook contingency.

p7's DAY2 and WK1 cells were carried through four measured attempts and 0 of 36 passes, and looked exactly like a divergence. What the reading actually produced was better: gold's rows did not reconcile and became CORRECTED_GOLD, the criterion turned out to be present but unreachable on one layer, and PR/NP were found not to carry `targets_own_behavior` at all — which dissolved an apparent gold inconsistency that a divergence would have enshrined as ours.

Q6/p9 was `PER_ITEM_EXCLUDE` with `expect_error` -1.25 and became `CORRECTED_GOLD[("Q6", 9)]`, because the exclusion "dropped a perfectly scoreable cell from every rate in order to absorb an error that was gold's".

**Declaring beats excluding wherever the choice exists, because an exclusion silences questions nobody asked it to.** 2a/p18 was `unscoreable`, and `check_consensus_spans_are_disjoint` skips those — so its `verdict`/`how1` overlap sat exempt for as long as the exclusion stood, never judged by anyone.

Q6/p4 left `GOLD_CEILINGS` for precisely that reason once `scores_as_exact` credited its off-grid gold — "a note here would tell a reader there is unwinnable ground where there is none."

The ceiling on Q6/p9 was retired by a definition written for the item as a whole: the cell went from 56% at nine passes to 9 of 9, and "it was never an unwinnable criterion; it was an undefined term."

see: qc:QC.every-declaration-table-needs end

**Worked from this course.**

`GOLD_SLOT_BOUNDS_KNOWN` had none, and it showed: three 2a entries stood asserting "gold charges one how_* slot; we charge none" on the very day the rule made us charge the box gold NAMED in 12 of 12 runs, and two of them said only "same as 2a/p1" so the stale claim propagated by cross-reference. Adding the ratchet retired those three and then found **two more that had been stale for longer** — Q4a/p6 and Q4a/p9, where Q20's own text already recorded that p6 agreed while this table was never updated to match.

see: qc:QC.6 end

**Worked from this course.**

- **Concluding a distinction is unstatable after testing only SINGLE features.** Twice on 2a. p1's two boxes matched on every individual predicate — payload type, causal link, direction, subject — and I reported that no clause could separate them. Then p5 versus p16 was called "a boundary at the noise floor" and stopping was recommended; the per-ground data showed one of the two was answered correctly 12 times out of 12 when asked on its own. - **Refreshing a ledger on one side only.** Re-recording DAY1's olx half while its python artifact was refused manufactured a path asymmetry the audit immediately reported as a declaration true on one path and false on the other.

see: qc:QC.6c end

**Worked from this course.**

The history rewrite reported **0 student sentences remaining**, twice, by two instruments that looked independent. Scanned against the whole student response space afterwards, it still carried **915 distinct student 4-grams** (3123 in the original — so it had removed 71%, not all).

*Those are the numbers from the rewrite that was current when this was written. Rebuilding the table against the whole response space took the same history to **27** against a control of **2107**. The figures below are kept as measured, because the lesson is what they showed at the time; the residue itself has moved.*

What it missed was not an edge case but the normal shape of the data: the repo carries whole student *responses*, so replacing the cited fragments left the student's connecting sentences sitting verbatim between the references:

{{corpus:Q6/p8:state_a1:0:103}} Which then makes me wish I would have just gone to the gym. {{corpus:Q6/p8:change_a1:0:53}} {{corpus:Q6/p8:change_a1:54:108:sha=bc805c563129:shape=S6-0a20202020}} {{corpus:Q6/p8:state_a2:0:47:sha=ce81132d390c:shape=S7-0a20202020}} {{corpus:Q6/p8:state_a2:48:67}}, {{corpus:Q6/p8:state_a2:69:98:sha=86e03b170080}} ...

A later correction, from the same rule: **a numeral is not a content word.** Handout 3 asks for a week of counts, so student fields hold runs like `3, 4, 2, 5, 3, 4, 6`, and those match ordinary code — a ten-character span of one student's baseline data was substituted into `errs, exact, within, esc, n = [], {}, 0, 0, 0`, breaking `baseline.py` at eight commits and the generator at 108 states.

see: qc:QC.first-can-the-example end

**Worked from this course.**

**Usually yes, and that is the fix.** Handout 2 taught that a reinforcer must be an outside thing you control, and its worked NON-example was a real student's sentence, carried in by reference.

**And the quote came from a question in that same handout.** `PR/p1` is participant 1's answer to the Positive Reinforcement item — `bmod_h2_pr`, whose box sits twenty-five lines BELOW the instructions that quoted it.

A replacement must clear the same bar: the invented sentence that replaced this one is a sleep example, while the box it precedes asks "{{corpus:NR/p1:nr:0:20:sha=2850093cabf3}} will..." — it does not pattern the answer to its own question.

Scan the candidate against the whole response space with course text subtracted (`scripts/history_rewrite/scan_full_corpus.py`); three candidates were checked for that handout and all three came back clean, which is what licensed picking one.

see: qc:QC.and-do-not-stop end

**Worked from this course.**

2a was proposed for closure at "20 of 20" while its mean was 18.8, six of twelve runs scored 18, and the two cells that decided the boundary sat at 7 of 12 in OPPOSITE directions.

2a/p14 went to Q35 before Q2 closed for exactly this reason.

see: qc:QC.0 end

**The leakage gate's scope.** It is armed for HANDOUT 2 specifically -- `agreement.py` tests `args.handout == 2` before consulting `leakage.py`, so handouts 1 and 3 sweep without it.

see: qc:QC.2a-1b end

**What each probe found on the cell-slots it was not aimed at.**

| probe | non-target cell-slots that disagree with the ledger |
|---|---|
| a subtract-duplicates route | 8 of 19 — and the TARGET too: its envelope counted the target cell higher than the shipped prompt does, so the question the probe was built to ask was untestable in it |
| the same probe earlier, counting reasons | 3 of 19, two at 12/12 |
| a gate's first text | 2 of 17, both at 12/12 — **but a SWEEP settled that subgoal**, so the conclusion stands on sweep evidence, not on this probe |
| a wording candidate, 1st | 4 of 38 |
| a wording candidate, 2nd | 2 of 38 |
| one slot group mirroring another | 2 of 10 |
| a wording candidate, 3rd | **0 of 38 — clean** |
| a habit-head candidate | 1 of 38 — one cell/slot reading `met` against the ledger's `duplicate` 12/12, on a cell no candidate touched. Independent of the A/B that first exposed it |
| a boundary candidate on one slot group | 1 of 17 — the same duplicate |
| two report-slot arms | **NOT GATEABLE** — they probe CANDIDATE slots reverted out of the tree, so the ledger has no baseline (36 cell-slots of `None`). A probe of a NEW slot must be gated on an EXISTING slot measured in the same call |

see: qc:QC.2a end

**Edits whose diagnosis was sound and whose effect was nil.**

| edit | what happened |
|---|---|
| a clause added to a gate | target cell 5/12 → **5/12**; the clause never fired |
| a new pick offered on a slot | fired, answered sensibly, sorted both targets into CREDITING categories |
| a new value added to an existing pick | target answered its old value **12/12**; the new value never chosen, and it was reverted |

see: qc:QC.and-profile-the-grounds end

**What the split measured, in runs.** Cell A: `absent 12/12` on every ground. Cell B: `3/11, 1/12, 4/12` -- no ground at all. Asked separately the model was unanimous and correct about cell A, which the compound question got wrong 5 times in 12.

see: qc:QC.2 end

**The stale-figure incident, in numbers.** The published figure was `17/20`; on current gold the same run was `16/20`.

see: qc:QC.2a-2 end

**What the hand-picked set hid, in numbers.** The cell that fell went `4/12 -> 0/12`. The all-cells probe cost 76 calls; the sweep that would have found them, ~230. The same free readout showed gold naming that criterion exactly ONCE in the whole item.

see: qc:QC.2b end

**The counted slot's eight configurations.** The won cell went `2/6 -> 6/6`. The cell that never landed scored `1/6, 3/6, 6/6, 3/6, 4/6, 2/6, 1/6, 1/6` -- and the one `6/6` was never replicated.

see: qc:QC.2d end

**The three headline mistakes, in numbers.** The run series was `18 18 18 18 18 18 19 19 20 20 20 20`: median over actual runs **18.5**, mean **18.8**, six runs at 18, only four perfect, two cells right in 7 of 12. The three were a single-side median of `17/20` whose two failing cells had medians the increment cannot score; a `20/20`; and a `15 -> 17 -> 18 -> 19 -> 20` progression reported while run-level scores moved 15 -> 18.8.

see: qc:QC.2e end

**The collapse, in numbers.** The cell went `4/6 -> 0/6`. Six further configurations then argued with the consequences.

see: qc:QC.2g end

**The inverting cell.** Cell E, `6/6` stable both ways after the flip.

see: qc:QC.3 end

**Reading the credited rows, in numbers.** Narrowing to the broader disjunction took the item from `16/20` to `18/20`, with all five guards holding at `6/6`.

see: qc:QC.3 end

**The eight moved cells, in numbers.** Six came back `4/6` to `6/6` (noise); one improved `0/3 -> 4/6`; the unstable one had measured `3/6` under the previous configuration too; two "regressions" of `3/3 -> 2/3` were `6/6` on probing.

