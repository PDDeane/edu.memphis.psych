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

- [ ] 1. **Q3's `action` criterion.** The clearest target on the board. Five
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
- [ ] 2. **Handout 3's 2a, 15/20 with runs [15,15,15].** The worst cell count in
      the corpus and never once examined. Perfectly stable, which usually means
      a systematic mis-rule rather than noise -- the shape that made NR/p14
      diagnosable. Six runs first, then read the failing checks.
- [ ] 3. **Re-measure the 3-run items at six runs, cheapest-first.** H1: Q1, Q2,
      Q4c, Q5, Q6. H3: 1a, 1b, 1c, 2a, 2b, 3. H2: PP, NP, T1, D1, T2, D2 -- the
      four definition items sit at 18/18 and are the least likely to move, so
      they go last. 120 calls each; do not batch more than two items at once,
      because two sweeps sharing the endpoint halved throughput today.
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

## DONE — the three non-reconciling gold rows

One was a slip, one never failed to reconcile, one had been settled upstream and
the checker did not know. `gold_rows_that_do_not_reconcile()` returns NONE and
`--preflight` reports nothing outstanding.

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
