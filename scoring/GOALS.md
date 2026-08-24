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

## ACTIVE — the three non-reconciling gold rows

From `--preflight`. This is also the FIRST alternative the new section-5 policy
demands before any divergence is contemplated: check gold's arithmetic against
its own comment. Read each submission; a slip is CORRECTED_GOLD, an unwritten
deduction is not, and the D2/p11 precedent needs a control set before
correcting — nine rows reconciling exactly is what earned that one.

- [ ] Q3/p8: comment itemises 1+1 off max 5, implies 3, row says 4.
- [ ] Q6/p1: itemises 1.25 x3 off max 10, implies 6.25, row says 5.
- [ ] 1c/p11: itemises 2+2+1 off max 10, implies 5, row says 7.
- [ ] For each: find the control set (other rows with the same itemisation
      shape) before deciding. No correction without one.

## THEN

- The two remaining fixture suspects: DAY1/p1 (gold 4, we award 0 every run) and
  DAY2/p14 (gold 0, we award 4/2/2). Read the boxes; both fixtures were read
  once and found clean, so the next step is the record, not the rubric.
- The probe backlog from the baseline: Q1 (p6/p7/p17) and Q3 (seven cells)
  crossed a real prompt change. The same-prompt flags are noise samples.
- Q4b/p12's declared divergence: accurate today, but its stated reason says we
  never matched gold there, and cli_v7/cli_v8 both scored it 3/3.

## LATER

- Three non-reconciling gold rows from `--preflight`: Q3/p8 (implies 3, says 4),
  Q6/p1 (implies 6.25, says 5), 1c/p11 (implies 5, says 7). Read each
  submission; a slip is CORRECTED_GOLD, an unwritten deduction is not.
- The probe backlog from the full baseline: Q1 (p6/p7/p17) and Q3 (seven cells)
  crossed a real prompt change and deserve six passes. The same-prompt flags in
  Q2/Q4a/Q4b/Q4c/Q5 are noise samples, not regression candidates.
- Q4b/p12's declared divergence: 3/3 right in cli_v7 and cli_v8, 0/3 in every
  sweep since. The declaration is accurate today but its stated reason says we
  never matched gold there, and we did.

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
