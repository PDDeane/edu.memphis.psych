# What we are doing right now

Read and updated at every step. `measured.py --preflight` prints the ACTIVE line,
so the objective appears every time the gate is consulted — which is how it stays
in front of whoever is working, instead of living in someone's memory.

Rules for this file: one ACTIVE goal, its subgoals in order, and the reason each
finished subgoal closed. When a subgoal produces a finding that changes the plan,
rewrite the plan HERE before acting on it. Superseded goals move to DONE with the
measurement that closed them, because a goal closed without a number is a goal
that will be reopened.

**NEVER CLOSE A GOAL WITHOUT ASKING THE USER FIRST.** Not when it succeeds, and
above all not when it fails. A failed attempt is not a finished goal — it is one
ruled-out approach, and the decision about whether the goal is still worth
pursuing belongs to the person whose project it is. Closing it unilaterally
converts "this did not work" into "this cannot be done", which is a conclusion
no single measurement supports.

Done twice on 2026-08-24, on the same goal within an hour: after a neutral prose
result the next step proposed was unrelated work, and after the gate attempt also
measured neutral the goal was moved to DONE while the entry recording it named an
untried lever in its own last paragraph. Report the result, state the options,
and ask.

Written after drifting on 2026-08-24: a measured result identified the criteria
gate as the place a fix had to go, and the next thing proposed was unrelated
work on gold rows. Nothing in the tree disagreed, because nothing in the tree
knew what we were doing.

## DONE (by decision, not by success) — the four cadence items

DAY1/DAY2/WK1/WK2. The `NOT_OC` boundary is misaligned with gold in BOTH
directions. A prose fix measured neutral (60 -> 60 sum of medians, 240 calls) and
was reverted, because these items are `derive_from_criteria`: the score comes
from `score.derive_oc_ledger`'s gate over the `oc_analysis` fields, and prose
about deduction points cannot reach it. See BACKLOG.md for the full readout.

- [x] 1. Read the FIELDS, not the score. DAY1/p13 has every gate `met` in 3/3
      runs against gold 0 — including `you_arrange_it`, though going to sleep
      ends screen time by itself. DAY2/p14 has all gates met too but genuinely
      DOES arrange its stimulus; its defect is contingency. Different gates.
- [x] 2. Named the lever and the risk. olx_prompts' own comment records this
      exact experiment measuring 129/144 -> 128/144, with three collateral
      breaks including `you_arrange_it` on DAY2/p12, and prescribes the retry
      protocol: isolate ONE gate. Endangered cells named in advance: DAY2/p12
      (broke last time on this gate), DAY1/p2, DAY2/p3, DAY2/p5, WK2/p12.
- [x] 3. Landed as an item-scoped SLOT_NOTES key, `DAY1:you_arrange_it`, which
      beats the bare key at the lookup. Blast radius per the ledger: DAY1 alone.
      One gate, one item — tighter than the protocol asked for, and 60 calls
      instead of 240.
- [x] 4. Swept. PREDICTION FAILED: median 15/18 -> 15/18, `you_arrange_it`
      stayed `met` in all three runs, p13's one correct run came from
      `follows_behavior` drifting to `unclear`, and p7/p14/p15 moved instead.
      The coupling in SLOT_NOTES' comment, observed a second time.
- [x] 5. Reverted, 0 stale. Recorded in BACKLOG.md with the untried lever: add a
      NEW required slot rather than re-describing an existing gate, which is
      what README v5 actually recommends and what fixed Q6.

Four measured attempts, all neutral; reverted each time. NOT declared as a
divergence — the user's decision, now policy in QUALITY_CONTROL.md section 5:
never declare a gold divergence until every alternative, fixture accuracy and
gold alignment first, has been exhausted. The findings that survive are in
BACKLOG.md: PR/NP do not carry `targets_own_behavior`, the guidance's brake
describes a type cell not a cadence cell, and p7's cells are a genuine reading
ambiguity. The cells stay counted and wrong.

### Attempt 3 — the lever nobody had tried

Attempts 1 and 2 both EDITED THE DESCRIPTION of something that already existed:
first the deduction severity prose, then one gate's own text. Both neutral. The
untried lever is structural — add a NEW required slot the model must answer
before the five gates, which is what README v5 prescribes ("a step the model
must not skip belongs in the schema, not in prose") and what fixed Q6.

- [ ] 3a. Find how the gate slots are generated and what `!` means, so a new one
      is added the way the existing five are, not bolted on.
- [ ] 3b. Draft the slot: does the consequence exist APART from the behaviour, or
      is it just the behaviour's own by-product / the time it occupies?
- [ ] 3c. Scope it. `_example_use_item` builds the four cadence items only, so
      PR/NR/PP/NP keep their five gates. Confirm the blast radius in the ledger
      BEFORE measuring.
- [x] 3d/3e. DAY1 15 -> 14, and the probe dissolved it: DAY1/p13 is 3 of 6, not
      a stable 0/3, and p11's apparent fall probed 6/6. Reverted.

### Attempt 4 — `targets_own_behavior` on DAY2 + WK1

- [x] Best-evidenced target of the four: 0/24 pooled, field `met` every pass,
      gold naming the defect in both rows, 1 point charged by both sides, exact
      match after the morning's CORRECTED_GOLD. A scored slot, not a gate.
- [x] Rule placed in the credit component's `rule` field, not SLOT_NOTES, after
      the enforcement check caught the first draft reaching only the web.
- [x] WK1 15 -> 17 and DAY2 14 -> 13; the probe put the target at 0 of 6 on BOTH
      items with `met` six times, DAY2/p12 at 6/6, controls 6/6. Neutral.
      Reverted.

## DONE — p8's four cadence cells, and WK2's direction gap

Three of the four came out of the divergence table. DAY1/p8 fixed by gating
avoidance framing (9 of 9), DAY2/p8 by the days-per-week cadence fact (5 of 6),
WK2/p8 by reading it out and finding gold right — counted and wrong, not
declared. WK1/p8 survives six attempts and stays declared. Two new criteria kept
on their items: `aimed_correctly` on WK2, the cadence fact on DAY2. Handout 2's
cadence items went DAY1 15->16, DAY2 14->15, WK1 15, WK2 16.

## ACTIVE — quality control on the remaining items

Every item is recorded and the preflight is clean, so the work is no longer
"find the blockers" but "check the numbers we have". SEVENTEEN of twenty-six
items still rest on THREE-RUN medians, and today showed twice over what that is
worth: Q4a sat on a three-run median from runs [14,16,16], six runs gave
[16,17,17,18,18,18], and it now records 18/20 -- and NR's derive_v3 opened 17,17
before finishing at a median of 15.5.
A three-run median is not a measurement, it is a sample that happens to have a
middle.

The order below is by diagnosed tractability, not by score. A deterministic miss
with a named failing check is worth more than a larger gap of unknown shape,
because it can be fixed or declared; a wobbling cell cannot be either.

- [x] 1. **Q3's `action` criterion.** The clearest target on the board. Five
      misses, ONE cause: gold charges two criteria and we charge one, and the
      criterion we skip is `action` every time. DONE, +2: the desc credited
      "access, equipment, or TIME they already have", and gold never credits
      available time -- it credits an activity, or access to a place or thing
      (p9 a car, p14 a gym near the house, p18 the university gym), and docks
      every answer resting on hours (p8, p16), on measurability (p19) or on a
      bare capability (p20). Narrowed from all twenty rows, not the three
      misses. p8 and p16 went 0/6 -> 6/6 with `action_oriented` flipping to
      `absent` x6 on exactly those two; five guards held 6/6 including p14.
      Q3 16 -> 18/20, verdict permitted. THREE CELLS REMAIN, each a different
      question: p19 grounds actionability in measurability WHILE naming a doing,
      so neither the time clause nor "names no doing of its own" reaches it;
      p10 is ~3/6 on `measurable`, where it names tracking methods but no
      medium; p13 over-charges `realistic` on an answer gold passed silently.
      CLOSED on the measured +2, committed. The criterion this subgoal named is
      fixed; the three residual cells are NOT settled and do not stay buried in a
      closed entry -- they are subgoals 9, 10 and 11, one per criterion, because
      each needs its own readout and they must not be attempted as one change.
  Before ANY sweep: the structural checks now run automatically at the top of
  `agreement.py`, and a HARNESS fix must be shown to change something with
  `before_after.py '<snippet>'` -- an identical result is not evidence. Section 2
  of QUALITY_CONTROL.md has the case that cost 140 calls.

  Run `measured.py --criterion ITEM CHECK` on any criterion before changing it.
  Section 3 of QUALITY_CONTROL.md says why: the misses tell you a criterion is
  wrong, the CREDITED rows tell you where the line falls, and on Q3 those two
  answers pointed opposite ways -- demanding a doing would have cost p9, p14 and
  p18, all credited on access alone.

- [ ] 2. **Handout 3's 2a, 15/20 with runs [15,15,15].** The worst cell count in
      the corpus and never once examined. Perfectly stable, which usually means
      a systematic mis-rule rather than noise -- the shape that made NR/p14
      diagnosable. Six runs first, then read the failing checks.
- [ ] 3. **Re-measure the 3-run items at six runs, cheapest-first.** H1: Q1, Q2,
      Q4c, Q5, Q6. H3: 1a, 1b, 1c, 2a, 2b, 3. H2: PP, NP, T1, D1, T2, D2 -- the
      four definition items sit at 18/18 and are the least likely to move, so
      they go last. 120 calls each; do not batch more than two items at once,
      because two sweeps sharing the endpoint halved throughput today.
      IN PROGRESS. The six items the scorer fingerprint flagged are being swept
      first, two at a time, into `scorer_fix_6run`: Q1 was **16/20** at the old
      (runs [15,16,16,16,17,17], was 17/20 on three; now 17/20 at the rewritten
      prompt -- see subgoal 6) and Q2 **18/20** (runs
      [16,17,17,18,18,18], was 17/20 on three) are recorded, both probes filed,
      both verdicts permitted. Neither item actually moved: every moved cell was
      already unstable and the six-run rates mostly SHARPEN the three-run ones
      (5/6 where three runs said 3/3, 1/6 where they said 1/3), which is the
      expected result -- their `counts` machinery was working all along via the
      rubric key, and the fingerprint flagged them because `expand_counted`
      moved, not because arithmetic changed. Q4b and 2a are running; 2b and 3
      are next.
- [ ] 4. **The leakage detector's shared-prose blind spot.** Found twice today:
      the word check suppresses any word appearing in ANOTHER authored block, so
      prose duplicated across items is invisible to it -- the whole of
      `_MOVE_RULE` was unchecked while it sat in four prompts, and both times a
      block was edited an unrelated block lit up. Compute the "ours" set from
      DISTINCT prose rather than per-block. Expect a fresh backlog to triage.
- [ ] 5. **Q4b/p12's declared divergence.** Accurate today, but its stated reason
      says we never matched gold there and cli_v7/cli_v8 both scored it 3/3. A
      declaration whose reason is false is a declaration that will be trusted
      for the wrong reason.
- [ ] 6. **Make the `reasons_given` rewrite live, then measure it.** DRAFTED,
      not live: `drafts/q1q2_reasons_rule.md` holds the replacement text, the
      per-cell evidence, the rejected alternative and the test plan. Diagnosed
      from Q1's three durable misses, which turned out to be three different
      things. p9 and p14 are OUR RULE contradicting gold -- it makes harms
      dominate and discards benefits, and in both cells the shortfall is exactly
      the benefits discarded; on p9 the model obeyed the rule to the letter and
      the rule is what is wrong. p10 is the model counting a goal restatement
      that `benefits_listed` already excludes, where rule and gold agree.
      The prize is bigger than two cells: the score currently depends on the
      harm/benefit SPLIT, which the model demonstrably cannot make -- p14 flipped
      on which counter one sentence landed in, and on p10 benefit text went under
      `harms_listed` in 4 of 6 runs. Counting statements towards one total makes
      the number invariant to that split, removing a source of variance instead
      of re-describing a judgement.
      Do NOT make it a computed sum of the two counters: p9 would score 3 against
      gold 2, because one clause was counted under both headings. The reason it
      cannot be arithmetic is written down in the draft.
      Shared by Q1 AND Q2, so it needs six runs of each and Q2 is the regression
      test. Baselines and per-cell predictions are in the draft; the decision rule
      is stated there in advance. Land the artifact fix in the same change: a
      count slot absent from the rubric's `counts` records `""` , so the operands
      of this rule survive only in `evidence`.
      LANDED AND KEPT on a measured +1: Q1 was 16/20, now **17/20**, six runs
      [15,16,16,17,18,19], artifact `reasons_rule_v1`, prompt `fa105e57b2c0`,
      probe filed, verdict permitted. KEPT ON A WEAK RESULT and the draft says so
      in full. p14 went 2/6 -> 6/6, which validates the actual thesis -- its score
      used to depend on which counter one sentence landed in and is now invariant
      to that split. But p9 went only 1/6 -> 3/6 and its misses now OVERSHOOT, p6
      is a stable new loss at 0/6 over-crediting by two, and the spread widened
      2 -> 4 cells.
      TWO CORRECTIONS to what this subgoal said before measuring, both caught by
      checking rather than assuming: the rule is Q1-ONLY (the counter is shared
      with Q2, the rule is not -- Q2 has its own 921-char text asking a different
      question), so there was no Q2 regression column; and the replacement is
      +58% longer than what it replaced, not volume-neutral as first written.
      WHERE THE NEXT ATTEMPT GOES: clause boundaries, not counter dominance.
      Harms-dominance never was p9's problem -- one "and"-joined clause reads as
      two reasons under the new rule and one harm under the old, and gold counts
      it once. p6 and p9 are the paired test, and Q2's rule already carries a
      structural test of the right shape to borrow.
      v2 MEASURED AND REVERTED. Reading all twenty responses found the concept
      both earlier rules lacked -- gold treats a harm and its INVERSE BENEFIT as
      one reason -- and a paper check reproduced gold on all twenty cells. Swept:
      median fell to 16 from v1's 17, mean 15.7, spread 4 cells. Reverted to v1
      byte-exactly; the OLX diff against the committed state is empty and Q1
      re-records at the same prompt sha the v1 measurement used.
      THE FINDING SURVIVES. p9 went 1/6 -> 3/6 -> 6/6 across v0/v1/v2 as the
      mirror rule was stated more explicitly: a dose-response on the targeted
      cell. What failed was the wording -- every new miss over-credited by one,
      four cells that had never missed began to, and v2 ran +95% over v0. Too
      long to apply consistently, not wrong.
      TWO LESSONS: a paper check establishes CONTENT and can say nothing about
      whether a model executes 759 characters the same way twice; and a per-cell
      decision rule is not enough here -- the one agreed in advance did not fire
      because p14 held and p9 recovered, while the item got worse. Median clause
      next time.
      v3 PROPOSED, in the draft: the mirror rule at 508 characters, 106 SHORTER
      than the live v1, by replacing v1's duplicated exclusion list with a pointer
      to the two counts above -- which v0 proved works, since p9's old wrong
      answer was that rule being obeyed. It reintroduces a dependency on the two
      counters deliberately: v0 made the SCORE depend on the harm/benefit split
      the model cannot make, while v3 makes only the EXCLUSIONS depend on their
      definitions, and those are identical for both kinds. Must reach a median of
      18 to be kept; at 17 it merely ties v1, and below that stop rewriting this
      paragraph.
      v3 MEASURED AND REVERTED. Median fell to 16, runs [17,15,17,14,16,16],
      mean 15.8. Reverted byte-exactly; the OLX diff against the committed state
      is empty and Q1 re-records at the same prompt sha v1 used.
      THE TRADE-OFF IS NOW PRICED, which is what three attempts bought. p9 is
      3/6 at v1, 6/6 at v2, 3/6 again at v3 -- the CONCEPT was identical in v2 and
      v3, only the scaffolding differed, so the compressed form does not reach the
      cell. Stating the mirror rule strongly enough to fix p9 costs the volume
      that damages p7, p16 and p17; stating it briefly enough to protect them
      fails to fix p9. Not a wording problem.
      SECOND FINDING: the pointer costs exclusion strength. p16 ran 4/6 with v1's
      inline exclusion list, 3/6 with v2's, 1/6 with v3's pointer. v0's pointer
      worked for the COUNTING rule and does not work for the exclusions.
      This subgoal is now at its decision point, and by its own pre-agreed rule
      the paragraph should stop being rewritten. The ONE untried idea is the
      NARROW form -- merge only when both halves name the SAME OBJECT -- which is
      mechanical enough to state in one clause and is the only form that fixes p9
      while explicitly forbidding p7's merge. Every pair gold merges in Q1 has
      that property; every pair it counts twice names different objects. Taking it
      would be a deliberate exception to the stop rule, with the inline exclusion
      list restored. ASK before spending the 120 calls.
- [ ] 7. **Q4b's per-cell instability, which the item median hides.** Two cells
      went from six clean runs to intermittent across two sweeps of IDENTICAL
      prompt text: p17 6/6 -> 4/6, failing `modify_stated`, and p19 6/6 -> 3/6,
      failing `behavior_1`. Neither check had ever failed before. The item's
      median held at 16/19 throughout, so nothing at item level shows it -- and
      the `onlyif` fix cannot be the cause, because it can only ever RAISE a
      score by withholding a charge, and `modify_stated` came back absent in just
      2 of 120 observations with the guarded check passing in both.
      So this is not a mis-rule with a named failing check, which is the shape
      this project knows how to fix. It is a borderline judgement resolved
      differently on each pass, and p19's clean 3-of-6 alternation is the
      signature. Start with `measured.py --criterion Q4b behavior_1` and read the
      CREDITED rows: the question is where the line falls, not why two cells
      fail. Do not change prose before that readout -- an item at 16/19 with two
      unstable cells can be made worse by a rule that looks tighter.
- [ ] 8. **A count slot outside the rubric's `counts` records nothing.**
      `harms_listed` and `benefits_listed` store as `""` in every artifact,
      because `expand_counted` writes a verdict only for keys the RUBRIC names in
      `counts`, and `verdict_of` reads a count answer from the wrong field.
      Their values survive only in `evidence`. That matters beyond tidiness:
      those two are the operands of the rule subgoal 6 is revising, so the whole
      diagnosis of Q1/p9, p10 and p14 had to be reconstructed from prose
      fragments in `evidence` rather than read from `checks`.
      Same shape as the count-recorded-as-blank bug fixed last session, which
      cost 140 calls and a wrong diagnosis stated out loud: reading the artifact
      says the check was never answered when in fact it was. Land it with a
      before/after (`before_after.py`) and a selftest case, since a recording fix
      that is not exercised is indistinguishable from one that does nothing.
      PLANNED: `drafts/subgoal8_recording_plan.md`, four steps, no model calls.
      Scoping corrected the subgoal in both directions. THIRTY-FOUR slots on 13
      items carry an answer `verdict_of` cannot read, not two -- but 30 are PICKS
      and the `answers` field already holds their values, so only FOUR are truly
      lost: Q1's `harms_listed`/`benefits_listed` and Q2's
      `reasons_listed`/`reasons_failing`.
      A THIRD DEFECT found while scoping, and the reason step 4 exists: the
      per-item fingerprint hashes 9 functions for Q1 and hashes NEITHER
      `verdict_of`, `answer_of` nor `is_satisfied`, all three on the scoring path
      and reached from `satisfied_map` and `apply_computed`, which are hashed.
      Hashing a function does not hash its callees, so editing any of the three
      moves scores while every item still reads current. It is also directly in
      the way: the obvious fix here is to teach `answer_of` about `count`, and
      that edit would be invisible to the guard -- so the fix goes at the
      RECORDING site instead, and "no fingerprint moved" becomes the test that
      it stayed there.
- [ ] 9. **Q3/p19: actionability grounded in measurability.** The cell names a
      doing AND rests its actionability on being able to measure it, so neither
      lever that fixed p8 and p16 reaches it -- not the time clause, and not
      "names no doing of its own". Gold docks it. This is the residual cell most
      likely to be a genuine boundary question rather than a wording gap: the
      answer does the thing the criterion asks for and justifies it the wrong
      way. Read `--criterion Q3 action_oriented` credited rows FIRST; a rule that
      rejects measurability-as-justification risks p9, p14 and p18, all credited
      on access alone.
- [ ] 10. **Q3/p10: `measurable` at ~3/6.** Names tracking methods but no medium
      -- what it would be recorded in. Unstable rather than stably wrong, so it
      is the weakest of the three: six runs of the criterion before any prose
      change, since a ~3/6 cell can be moved by noise and read as a fix.
- [ ] 11. **Q3/p13: `realistic` over-charged.** We charge where gold passed the
      answer silently, so unlike 9 and 10 the defect is OURS being too strict,
      not too lenient. Gold's silence is the evidence, which makes this the one
      of the three where the credited rows matter most -- there is no gold note
      to read, only the absence of a deduction.
- [x] 12. **Q1's exclusion failures: p6, p10, p16.** Not a counting problem, and
      three rewrites of the counting rule have now been blamed for it. The model
      credits things the rubric already excludes: background about how the
      behaviour came about (p16 counts "used to exercise due to sports"), a
      restatement of the goal (p10 counts "{{corpus:Q1/p10:response:117:146:sha=be46148ce74e}}
      active"), and a CONDITIONAL goal restatement (p6 counts "if I discipline
      myself ... {{corpus:Q1/p6:response:347:369:sha=380de98ed5ad:shape=A1}} myself"). Gold rejects all three, and says
      so in its own words on p1 ("struggling with it" is not a reason) and p2 (a
      behaviour done DURING the unwanted one).
      p6 is the sharpest evidence that this is independent: it scored 4/6 under
      v0 and 0/6 under every version since, because v0's harms-dominance
      INCIDENTALLY suppressed its spurious benefit-side reasons. No counting rule
      fixed or broke it; one accidentally hid it.
      Carries the open question from subgoal 6's v3: an inline exclusion list
      beats a pointer (p16 4/6 -> 3/6 -> 1/6 as the list became a reference), so
      the fix here probably ADDS length to the exclusions rather than the counting
      rule. Measure `--criterion Q1 reasons_given` and read the credited rows
      first: p1, p2 and p15 are all credited with exclusions correctly applied.
      CLOSED, +1: **Q1 17 -> 18**, runs [15,16,17,18,18,19], artifact
      `tier_restored`. Two of the three cells recovered and the mechanism was
      confirmed, not inferred.
      WHAT FIXED THEM was not a new rule but RESTORING one this project had
      already measured and today had deleted: `reasons_given` is CONDITIONAL --
      harms of the unwanted behaviour, with stated benefits credited only where a
      response offers none. p6 went **0/6 -> 4/6** and p16 **4/6 -> 6/6**. The
      error profile confirms the mechanism at item level: v1 over-credited 16 to
      3, one-sided; the restored conditional runs 7 to 10, balanced. Letting
      benefits top up harms was what inflated both cells.
      ONE CLAUSE was added, for p14, so restoring the conditional did not cost
      v1's gain there: a statement naming what the behaviour EXPOSES the student
      to is a negative effect even when written as what the goal behaviour would
      protect against. p14 held at 5/6.
      p9 was declared (subgoal 12b). p10 did NOT recover and p18 was destabilised
      by the same change that fixed p6 -- both carried to subgoal 14 rather than
      left as prose here.
      THE COST OF NOT READING THE RECORD: eleven configurations and ~900 calls
      went into a merge rule first, while the comment above the component already
      named the conditional, classified every cell with gold < 3, and diagnosed
      p9. The restoration took ~60 calls. §2c now enforces the check that would
      have prevented it.
- [x] 12b. **Q1/p9 DECLARED: `GARBLED_CLAUSE_READ_LITERALLY`.** Twelve
      configurations, rates 1/6 3/6 6/6 3/6 4/6 2/6 1/6 1/6 4/6 4/6 3/6 1/6. The
      one 6/6 cost p7 four runs and three isolation probes each scored p9 WORSE
      than the baseline they came from. The cell turns on one ungrammatical
      clause whose literal sense is the opposite of the intent, and both readings
      are defensible -- which the record predicted before the work began. Routes
      closed and measured: mirror-pair rules at four lengths, the criterion
      inside the aggregate, splitting the counted family, and an
      assertion-versus-avoidance clause written for exactly this shape. See
      handouts.GOLD_DIVERGENCES. Q1 records 18/20 and cannot exceed nineteen of
      its twenty cells while this stands.
- [x] 13. **Q1/p17: `utb_stated` is a coin flip.** CLOSED BY DECISION, not by
      success, and with the number: p17 is **4/6** under the committed
      configuration, `utb_stated` reading absent in two runs of six and costing 2
      points each time, while `reasons_given` is 3 and correct in all six. The
      cell is CORRECT at the median, so it is not one of the item's misses.
      Two reasons for closing rather than working it. Its methodological content
      -- read WHICH check failed before blaming the rule you happen to be editing
      -- is now printed automatically after every sweep by the BY SLOT table
      (§2b), so it no longer needs a goal entry to survive. And it is not the
      best target: ranked by how often they are wrong, the non-declared cells go
      p10 1/6, p18 3/6, p6 4/6, p17 4/6, p7 5/6, p14 5/6.
      NOT SOLVED, and deliberately not buried: gold credits a UTB named inside a
      sentence about its effects rather than stated on its own, which is a
      boundary question rather than a misapplied rule, and the hardest of the
      three. If Q1 is ever pushed past its current record, this is the cell to
      look at AFTER subgoal 14.
- [x] **Q3/p8 was a slip.** Two explicit "-1 pt" markers against a max of 5
      imply 3.00; the row wrote 4.00. The control set is the whole item -- one
      charge scores 4, two score 3, three score 2 -- and p19 carries the SAME
      pair and scores 3. CORRECTED_GOLD 4 -> 3, and it cost us the cell: we
      score 4, so p8 had been "correct" only because gold's slip matched our own
      under-charge. p19 was already 0/3 the same way.
- [x] **Q6/p1 reconciled all along.** It itemises FOUR 1.25 charges, the third
      written "-1.25:" with no unit, totalling exactly its recorded 5.00.
      `_DEDUCT_RE` required "pt"/"point", so unit-less markers were invisible.
      Widening it to accept ":" and ";" cleared p1 and surfaced Q6/p4, which
      writes "-2.5:" and "-1.5;" for 4.00 off 10 and also reconciles at its
      recorded 6.00. Two rows carried as gold questions for two months were
      formatting variants.
- [x] **1c/p11 was settled upstream.** `rebuild_gold_1c` restates 1c's gold from
      its labelling verdicts so p11's improvised "-1 pt: missing baseline data
      week" is dropped rather than subtracted, putting the row at 6.00. The
      checker was reading the raw 7.00. A CORRECTED_GOLD entry written against
      the raw row was inert -- the rebuild overrode it, the re-record came back
      unchanged, and the audit caught the prose claiming 17/17 against a ledger
      saying 16/17. Entry removed; the checker now defers to the rebuild.
- [x] **Q3 re-measured at six runs against the corrected row: 16/20**, runs
      [15,15,15,16,16,17]. The check-level data the 3-run artifact lacked
      (`checks: null`) is what identified subgoal 1.

- [ ] 14. **Q1's two live misses: p10 and p18.** Lifted out of subgoal 12's
      prose so they are tracked rather than mentioned. Both are APPLICATION
      failures -- the rule already states the right principle in each case -- so
      §2a offers no structural lever and prose is the last resort, not the first.
      Run `measured.py --errors Q1 <artifact>` and read the record the `--write`
      hook prints BEFORE touching either.
      **p10, gold 4, correct in 1 of 6 runs -- the worst non-declared cell.** It
      counts "{{corpus:Q1/p10:response:117:146:sha=be46148ce74e}} active" as a reason. That is a
      restatement of the goal, excluded in as many words by BOTH `reasons_given`
      and `benefits_listed`, and the model applies the exclusion correctly in
      only one or two runs. Its two real reasons (confidence, a balanced routine)
      are read correctly throughout, so nothing else in the cell moves.
      **p18, gold 5, correct in 3 of 6 runs -- a drift, not damage.** Its
      `harms_listed` counts "{{corpus:Q1/p18:response:54:85:sha=065d40028477}} shape" as ONE effect
      in half the runs and TWO in the other half; the rule already says "two
      effects merely joined by `and` are two". Under the flat sum this was
      invisible because the student's benefit padded the total to three; the
      two-tier conditional made the harm count load-bearing and exposed a wobble
      that predates it. Fixing it means making the and-split deterministic, which
      is a classification question like p14's, not a counting rule.

## THEN

Nothing is parked here. The ACTIVE subgoals above absorbed what used to sit in
THEN and LATER, and the entries that are no longer true were deleted rather than
carried:

* The two "remaining fixture suspects" are settled. DAY1/p1 is a declared
  divergence (BEHAVIOR_NEVER_STATED); DAY2/p14 is 6/6 correct and was fixed by
  the `forbid` primitive, not by reading its boxes again.
* The three non-reconciling gold rows moved to DONE above.
* Q3's probe backlog is superseded: the item has six runs and a named cause.
* Q1's probe backlog and the 3-run flags in Q2/Q4c/Q5/Q6 are subgoal 3.
* Q4b/p12 is subgoal 5. It is 0/6 against gold and correctly declared TODAY --
  the problem is the reason written on the declaration, not the cell.

## DONE

- **Full baseline, all 26 items, 3 runs.** 444/491 = 90.4%. Every ledger entry
  recorded against a prompt SHA and exclusion set. Closed Q1's gap, which had
  five exclusions removed and six citations rewritten with no sweep after.
- **Exclusion necessity, all 41 registrations.** Handout 1 121 -> 159 of 160
  counted cells, handout 3 51 -> 57 of 60. Every one tested by sweep; none
  survived.
- **Gold corrections earned by control sets:** D2/p11 1.00 -> 0.00, DAY2/p7 and
  WK1/p7 1.00 -> 3.00. GOLD_CEILINGS ('2','DAY2') and the WRONG_DEFINITION
  divergence retired.
- **Prose fix for the NOT_OC boundary: reverted**, 60 -> 60.
