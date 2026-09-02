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
      the enforcement check caught the first draft reaching only the olx.
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

## PARKED — enforcing equivalence between the olx and python scorers

  SWAPPED WITH THE QUALITY-CONTROL GOAL ON 2026-09-01, because the precondition
  this goal existed to establish is now established. The THEN section put it
  exactly: "equivalence is the precondition for every number it produces -- a
  per-item rate compared against gold means nothing while the two scorers
  disagree about what the rules are." They no longer do, as far as anything here
  can show:
    * the two engines send an IDENTICAL prompt -- template, assembled text with
      the student's work substituted, and the provider-visible request fields --
      each checked per item on every audit.
    * their scoring LOGIC agrees wherever it can be compared: 221 verdict
      signatures produced by both, none scoring differently.
    * the columns are POOLED as one process sampled twice, and the rate test
      says the ledger has no power to distinguish them.
  ONE SUBGOAL REMAINS OPEN HERE, E28, and it is not a blocker: a corpus-wide
  paper sweep is a MEASUREMENT the ledger has never held, not a disagreement
  between engines. It costs ~3,100 calls and can be taken whenever it is wanted.
  WHAT THIS GOAL LEAVES BEHIND, and what quality control now runs on top of:
  twelve checks that fire on the cause rather than the symptom -- prompt bodies,
  assembled prompts, request fields, scoring logic, side contracts, artifact
  readability, wrong-cell ownership -- plus the pooled accounting itself.


  == 2026-09-01: THE olx AND python COLUMNS ARE POOLED FROM HERE ==
  DECIDED, not proven, and the reasoning is recorded so it can be revisited.
  The two engines are now taken to be one process sampled twice: 12 runs a cell
  rather than 6 and 6. What supports it, all built the same day:
    * the prompt they SEND is identical -- template, assembled text with the
      student's own work substituted, and the provider-visible request fields.
    * the scoring LOGIC agrees where it can be compared: 221 verdict signatures
      were produced by BOTH engines and none scored differently.
    * the rate data cannot show otherwise. At six runs a side the smallest
      achievable p is 0.0022 against a corrected threshold of 0.0001, and
      exactly ONE cell reaches uncorrected p<0.05 where chance predicts 26.
  If a real divergence appears it surfaces in the scoring-logic check, which
  needs no power to fire, or in the prompt and request checks.
  PAPER IS NOT POOLED WITH THEM. It runs the RUBRIC prompt, not the OLX sheet,
  which is the whole reason it is a separate side; subgoal Q33's cells are paper
  cells and nothing here touches them.
  WHAT POOLING CHANGES. Ten cells change status. Written WITHOUT fractions
  because the ledger still records per side, and `prose_claims` reads an
  item-plus-fraction as a claim about the recorded column -- correctly, until
  the ledger itself pools:
      3    gains a cell, reaching every cell of the item
      NR   gains two           Q1   gains one          Q4a  gains one
      WK2  gains one, reaching every cell of the item
      DAY2 loses one           PR   loses one          Q2   loses one
  32 cells are wrong at the pooled median, and every one already has an owner.
  SEVEN CELLS STOP BEING WRONG, and with them the side-split framing: 3/p15,
  NR/p11, NR/p15, Q1/p17, Q4a/p9, WK2/p8, WK2/p15.
  SUBGOALS WHOSE EVIDENCE IS AFFECTED, to be worked or closed on this basis:
      E39  every cell it names is right when pooled. Its subject was the
           side-rate comparison, which pooling retires by decision. The CHECKS
           it produced stay as regression guards.
      Q28  Q6/p5 is right when pooled -- its one cell.
      Q32  keeps DAY2/p8, PR/p15 and Q2/p18, loses Q4a/p9 and WK2/p8, and its
           PREMISE -- "cells the one side gets right and the other wrong" -- is
           gone entirely. The three survivors are ordinary wrong cells.
      Q23  keeps one cell; pooled, WK2 misses nothing.
      Q19  keeps 7, loses 1a/p1, 1a/p15, 3/p15, Q4a/p20, Q4b/p8, Q4b/p20, Q4c/p12
      Q20  keeps 4, loses Q4a/p6, Q6/p6, Q6/p16
      Q26  keeps 3, loses D2/p11, DAY2/p14, WK1/p7
      Q31  keeps 11, loses Q1/p17
  DONE: `_wrong_cells` now judges an `olx+python` side built from both engines'
  runs, with `paper` and `paper_opus` evaluated on their own -- see
  `measured.POOLED_OLX_PROMPT`. It reports 32 cells wrong pooled and 8 wrong on
  paper, all owned. The reverse arm now names Q28, whose title cell Q6/p5 is
  right when pooled; the ownership check itself stays quiet there because Q6/p5
  is a DECLARED slot-level finding, which "right at the total" deliberately does
  not retire.
 — enforcing equivalence between the python and olx scorers

The whole project rests on the two sides running the same rubric: every recorded
number is a comparison, and a comparison is meaningless while the scorers differ
about the rules. A full audit run in all three modes found the picture is not what
had been reported all session.

`--enforcement` alone was being run and called clean. `--scoring` carries THREE
undeclared mechanical flags, and `--enforcement` itself is structurally blind to
any rule written as guidance prose (subgoal E15, under the parked goal). Q4b/p12
is the demonstrated cost: the python scores it 5.0 in six runs of six and the olx
3.5 in eleven of twelve, and nothing anywhere declares that.

- [x] E1. **Declare the mechanical flags -- or wire them up.** Three findings, all
      pre-existing except the first, none declared:
      **Q4a TOTAL, olx 4 vs python 5.** The two antecedent slots carry 2 points each
      and the item's fifth point lived in the `keyword` component, which was
      zeroed by decision earlier (A_NO_KEYWORD -0.0). The decision was declared;
      its ARITHMETIC CONSEQUENCE -- assignable points no longer summing to the
      item max -- was not, and that omission is this session's.
      **Q4c CANNOT ZERO.** `C_NONE` is worth the whole item and NO check can
      charge it, so an answer naming no consequences at all cannot score 0. Gold
      does award 0 on this family.
      **Q4c UNREACHABLE COST.** `C_NO_KEYWORD` is still worth 1 point and is
      equally dead. Q4a's keyword was zeroed deliberately; Q4c's was left
      live-but-unchargeable, which is the worse state because it reads as a
      working rule.
      `A_NONE` (-5) is dead on Q4a too, by the same shape as `C_NONE`.
      For each: either bind the code to a check that can charge it, or declare it
      with a reason that says why the code exists and cannot fire. Do not leave a
      deduction that looks live and is not.
      DONE, and two of the three flags were never undeclared. `unreachable_codes`
      already named Q4a's A_NONE and Q4c's C_NONE/C_NO_KEYWORD, with reasons, and
      `enforcement.check_codes_reachable` reads that field -- but the MECHANICAL
      pass in `--scoring` did not, so it reported them as undeclared and they were
      passed on as real findings. The pass now honours the field. It stays a
      declaration and not an amnesty, because check_codes_reachable independently
      flags a code declared dead that turns out reachable.
      **Q4a TOTAL was genuinely undeclared and the omission was ours**, following
      from this session's decision to zero A_NO_KEYWORD. Declared in
      SCORING_DIVERGENCES with the part that matters checkable rather than
      asserted: gold's Q4a scores are exactly {5.0 x13, 3.0 x5, 1.0 x2} and the
      charges we can express reach exactly {5, 3, 1}, so no gold row needs the
      missing point.
      **A_NONE and C_NONE are now REACHABLE**, per the rule that a code gold
      specifies should be wired rather than declared away. Done with the `forbid`
      primitive (§2a: structure before prose), which is built for "fails when a
      COMBINATION holds": the computed check fails exactly when BOTH entries are
      `absent` -- nothing listed at all -- which is what the codes name, and is
      distinct from entries written but of the wrong kind, which the -2 codes
      charge. `forbid` keys are stripped from the response schema, so the model is
      asked nothing new.
      VERIFIED INERT BY REPLAY, 0 calls: all 180 recorded sheets rescored through
      the new rules, 120 of 120 on Q4a and 60 of 60 on Q4c unchanged. No cell in
      the corpus has both entries `absent`, and Q4a/p20 -- the cell that looks
      like a candidate -- is wrong_kind twice in 6 of 6 runs, correctly scoring 1
      against gold's 1.
      **C_NO_KEYWORD stays unreachable**, and that is the record's answer, not a
      shortcut. The comment above the component already recorded the measurement:
      no Q4c gold row deducts for the missing word, there is no 1-point deduction
      of ANY kind on the item, and charging it cost three cells and recovered
      none. A fresh measurement agreed to the cell -- absent or unclear in 12 of
      60 observations across p9, p13, p15, p17, every run. Reachable-at-zero would
      be cosmetic. The revisit is recorded there so the next reader does not
      repeat it.
      A STALE CLAIM was corrected while in there: that comment said "Q4a is the
      opposite case and keeps its charge", which this session made false when
      A_NO_KEYWORD went to 0.0. The two items now agree in EFFECT by different
      mechanisms.
      Q4a and Q4c are marked STALE PROMPT and NOT swept, by instruction. They join
      subgoal E2's list, which is now TEN items.
- [x] E10. **A FIX that retires Q4b's declaration, not just the declaration.** DONE, declaration RETIRED.
      User, 2026-08-28: "I want more than a declaration. I want a fix that allows us
      to retire the declaration." The declaration says the INSTEAD-OF test is prose
      on both sides and the two paths read it differently with no primitive to
      compare. RETIRING IT MEANS THE PATHS CANNOT DISAGREE, which means the test has
      to be COMPUTED on both sides rather than judged on each.
      DESIGN, worked out and blocked on one thing. Make `behavior_1`/`behavior_2`
      computed from a single operand pick per entry -- "what IS this entry?" over
      named options (activity / consequence / the goal behaviour done badly /
      a not-doing / the same referent as one of their own 4a antecedents / nothing)
      -- with the five prose tests moved onto the OPTIONS as their descriptions.
      One classification with named answers, decided by the engine, instead of five
      prose tests weighed together: which is the documented reason these primitives
      exist ("written as a single slot the question becomes composite, and the rule
      this replaces failed four times exactly that way").
      TWO FINDINGS FROM TRYING TO BUILD IT.
      (1) A DISJUNCTION CANNOT BE WRITTEN AS SEVERAL RULES. Both engines ASSIGN the
          computed check per rule -- `checks[rule["key"]] = ...` and
          `slots[rule["key"]] = ...` -- so two `forbid` rules on one key are not an
          OR: the last one wins and the first is dead. Identical on both sides, so
          it is a trap rather than a divergence, and it is now an audit failure
          (`check_computed_rules_do_not_share_a_key`) instead of a wrong number.
          This is why the design uses ONE pick with several values rather than
          several rules.
      (2) THE BLOCKER, and it is small and specific: a computed check's FAILING
          VERDICT is hardcoded to `options[1]`. Q4b's `behavior_*` carry
          [met, absent, not_active] with DIFFERENT codes -- `absent` charges
          B_ONLY_ONE ("you only gave one example") and `not_active` charges
          B_NOT_ACTIVE (present but wrong, and repeatable). So `expect` or `forbid`
          would fail the check as `absent`, telling a student who gave two examples
          that they gave one, and charging a non-repeatable code in place of a
          repeatable one. Same points, wrong feedback, wrong repeatability.
      THE PRIMITIVE EXTENSION IS DONE, on the two python engines. A computed rule
      may now NAME the verdict it sets: `behavior_1->not_active:b1_basis=activity`,
      parsed by `parse_forbid`/`parse_expect` into a `fails` field and honoured by
      both `score.derive_ledger` and `agreement.apply_computed`.
      IT ALSO CLOSED A LATENT DIVERGENCE. The failing verdict was positional, and
      the two engines read the position DIFFERENTLY -- score.py took `vocab[-1]`,
      agreement.py took `options[1]`. Every computed check in the corpus has exactly
      two options, so those coincide and the engines agreed BY LUCK; the divergence
      would have fired on the first three-option computed check, which is precisely
      what this fix needs.
      TWO MORE GAPS FOUND AND CLOSED ON THE WAY, both of the same kind -- a
      primitive honoured on one side only:
        - `expect` was computed by agreement.apply_computed for any item and by
          score.py only inside derive_oc_ledger. A credit-path `expect` was
          honoured by the olx and silently ignored by the python: the check simply
          never got set, its code never charged, nothing reported. Now computed in
          derive_ledger, and `check_both_engines_compute_the_same_primitives`
          asserts the parity from the REGISTRY rather than from a list of names.
        - score.py's schema exclusion named `equals` and `forbid` by hand -- a
          mirror of primitives.json kept by memory, already behind: `expect`
          excludes keys and was missing, so an `expect` key would have been ASKED
          on the python while the olx computed it. Now registry-driven. `counts` is
          the one primitive whose KEY the model does answer, and over-excluding it
          moved five schemas until the baseline comparison caught it.

      STILL BLOCKED, at the last step, and the blocker moved: the APP models a
      computed check as a BOOLEAN. `slotSheet.satisfiedMap` returns
      `out[key] = true/false`, so in the runtime students meet, a computed check
      has no verdict at all and cannot distinguish `not_active` from `absent`.
      Naming the verdict in the declaration therefore reaches both harnesses and
      not the app.
      OPTION A WAS TAKEN AND IS LANDED, across all three implementations: a
      computed rule names its failing verdict, `parseForbid`/`parseExpect` in
      slotSheet.ts strip and carry it, four tests cover it in the app's own suite,
      and `check_fails_verdict_is_mirrored_in_the_app` fails the audit if the
      runtime stops honouring the syntax (proved by making parseForbid drop it).
      IT TURNED OUT SMALLER THAN BILLED, which is worth recording: the app does NOT
      map verdicts to codes at all. `scoreFromSheet` computes booleans and subtracts
      points, so `not_active` versus `absent` never changed what the app CHARGES --
      the code distinction is a python-ledger concept. What the app actually needed was
      for the key to resolve: unstripped, `behavior_1->not_active` matches no slot,
      so the check silently computes nothing. That is the failure mode its new test
      asserts.

      AND THEN A NEW LIMIT, found only by writing Q4b's declaration against it.
      `behavior_1` has TWO failure verdicts with DIFFERENT codes: `absent` for an
      empty box, charging B_ONLY_ONE ("you only gave one example"), and
      `not_active` for a wrong entry, charging the repeatable B_NOT_ACTIVE. A
      computed rule names ONE. Writing two rules on the key is the last-rule-wins
      trap -- verified, and the consequence is the wrong direction: with
      `b1_basis=consequence` the first rule fails the check and the second
      OVERWRITES it back to met, so a wrong entry would be CREDITED. The new
      `check_computed_rules_do_not_share_a_key` catches it if anyone declares it.
      THE MAP PRIMITIVE IS BUILT, 2026-08-28: `maps`, the fourth computed
      primitive, across primitives.json and all three implementations.
        maps="behavior_1:b1_basis:activity>met,none>absent,*>wrong_kind"
      `*` is the fallback, and an unmapped value leaves the check UNSATISFIED rather
      than credited: the sheet has not said what to do, and crediting on silence is
      worse than charging on it because nobody reads a credit.
      VERIFIED THREE WAYS, 0 model calls: the two python engines agree on every pick
      value tested -- activity, none, consequence, own_antecedent, blank, nonsense --
      the app's suite asserts the same mapping and that an unmapped pick is not
      satisfied, and one test asserts the trap directly: two `forbid` rules on one
      key CREDIT a wrong entry, `maps` refuses it.
      Registering it immediately failed the app's probe registry-coverage test,
      which is the guard working: a primitive added to primitives.json and not
      taught to the audit stops being seen. That is how `derived` went unnoticed
      once. probe.test.ts now parses and forwards it.
      Nothing declares `maps` yet, so all 26 schemas are unchanged and oc_grid is
      identical -- the primitive is in place and no item's behaviour has moved.
      WHAT REMAINS for the retirement itself: declare Q4b's two picks and their
      `choices`, author them into the OLX sheet with a `maps` attribute, and let
      `behavior_1`/`behavior_2` become computed. That is a scoring change on a
      measured item, so it goes to the sweep -- and it is now unblocked.
        (A-as-billed) giving the app a verdict for computed checks: DONE, and it was
            not the blocker it looked like.
        (B) STILL AVAILABLE, and now cheaper than it looked: compute the REFERENT
            half only, as a 2-option check charging B_NOT_ACTIVE. Two options means
            one failing verdict, so no map is needed and the primitive set as it now
            stands is enough. The four prose tests stay prose and the declaration
            narrows to them rather than retiring.
      Also found: `for (const r of forbid) out[r.key] = ...` in the app has the same
      last-rule-wins overwrite as both harnesses, so the trap is consistent across
      all three and `check_computed_rules_do_not_share_a_key` guards the authoring
      side of it.
      ONCE EXTENDED: declare the pick and its `choices`, declare
      `expect: behavior_1:b1_basis=activity:...` naming `not_active` as the failing
      verdict, author the OLX slots (Q4b has no picks, no `choices` and no `forbid`
      today), and the declaration retires because both engines then compute the same
      answer from the same pick.
      MEASURE IT AFTER THE SWEEP, against the 6-run baseline. The prose form of the
      referent half was measured once on 3 runs -- counted [14,13,13] ->
      [15,12,14] -- and rejected not for its mean (+0.34) but for THREE TIMES THE
      VARIANCE, on the recorded principle that "a configuration that swings three
      cells cannot tell you whether the next change helped". Judge this on variance
      too. Target p4 (gold 2.0, olx 3.5); controls p1, p12, p15, p17 -- the four
      gold credits that held last time -- and p6, where the olx already matches gold
      and the python does not.
      LANDED 2026-08-28, and the declaration is gone from SCORING_DIVERGENCES.
      `behavior_1` and `behavior_2` are COMPUTED by `maps` from one pick each --
      b1_basis / b2_basis, answering what the entry IS over
      activity / consequence / goal_behaviour / not_doing / none -- so the composite
      the two scorers used to weigh separately is now arithmetic.
      VERIFIED ON THE REAL SHEETS, 0 model calls: both engines return the same
      verdict for every classification, and the codes follow -- `none` and a blank
      box give `absent` and charge B_ONLY_ONE ("you only gave one example"), while
      consequence / goal_behaviour / not_doing give `wrong_kind` and charge the
      repeatable B_NOT_ACTIVE. That distinction is the whole reason `maps` had to
      exist: no single `forbid` or `expect` can produce two kinds of failure.
      THE PROSE MOVED, IT WAS NOT REWRITTEN. behavior_1's five cases now sit on
      b1_basis verbatim, under a framing that only names the options. The leakage
      gate re-asked -- a verdict is keyed to the prose, so moving it asks again --
      and the answer was checked rather than waved through: chips, chores, eaten and
      everyday are all in the MOVED text and none in the new framing, so the prior
      `coincidence` verdict carries over, refiled with that attribution.
      FOUR THINGS THE AUDIT CAUGHT, each a real defect in this change:
        - `slot_basis` did not count `maps` as computing a key, so it reported
          behavior_* as prose-judged on the day they stopped being judged at all;
        - `_checklist_section` still listed them as answerable, so the prompt said
          "answer this" and "DO NOT ANSWER this" about the same check;
        - the old rule text on behavior_* became DEAD prose -- a computed check's
          rule renders nowhere -- and dead prose is how two copies of a judgement
          start, so it was removed and replaced by a pointer;
        - my own removal script took FOUR literals rather than two, deleting Q6's
          affect_c1/affect_c2 rules as well. Caught by the prose-only check, restored
          from HEAD, and confirmed lossless: the regenerated OLX shows only Q4b's
          material moving.
      AND A SYNTAX BUG OF MY OWN MAKING, worth recording because it is a trap for
      any future attribute: `maps` first used `>` between a value and its verdict,
      and this project reads an opening tag as `[^>]*>`. The `>` ended the match
      early and Q4b's `slots=` became invisible -- "no slots= attribute; nothing to
      measure". XML permits `>` in a value; these readers do not. The separator is
      `~` on all three implementations now, and the `fails` marker moved from `->`
      to `~` for the same reason before it could bite.
      EVERY ITEM IS NOW STALE: 11 prompt, 15 scorer. The scorer flags are honest
      rather than alarming -- `apply_computed` gained the `maps` loop and it is in
      every item's hashed path, so the fingerprint moved even where the loop is
      inert for want of a declaration. They are NOT being re-stamped: the two-sided
      sweep re-measures all 26 at six runs, so the flags cost nothing, and marking
      a number current on an argument is exactly what the ledger exists to prevent.
      WHAT IS NOT CLAIMED: that p4 and p12 now match gold. The classification is
      still a judgement, so the paths can still differ on it -- one named question
      instead of five weighed at once. That residual is declared as
      PROSE_ONLY_SLOTS Q4b.b1_basis/b2_basis, and the reopen condition is on the
      retired entry in olx_prompts.

      IT IS A OLX-SIDE CHANGE, consistent with the tie-break: Q4b ties on
      gold-matching, so the olx is the reference and this improves the reference
      side's own accuracy rather than importing the python's reading.

- [x] E11. **Empty SLOT_RULE_BACKLOG: thirteen rules the paper scorer cannot see.** DONE
      CLOSED 2026-08-30, budget 13 -> 1. The one entry left is `Q1:matches_selected`,
      which is not work: the paper sheet has no such SLOT, because a .docx has no
      closed choice to compare against, and the asymmetry is declared in
      SCORING_DIVERGENCES. The list IS the declaration of olx-only notes, so the
      entry stays in it.
      THE LAST THREE went on 2026-08-30, and the recorded reason they could not --
      "each names one side's verdict token, workable for reasons_substantial and
      1c:legend, not for example_2, which distinguishes two failure modes" -- was
      wrong in BOTH directions. Measuring the vocabularies instead of reasoning
      about them:
        `Q5:example_2` DID migrate. Its second failure mode is `duplicate`, which
          SHARED_EXTRAS shows both sides offer, so `{fail}` plus one literal covers
          it. This also FIXED a live defect rather than moving one -- see the
          BACKLOG entry below.
        `1c:legend` migrated on `{fail}` plus a literal `absent`, which is
          universal and means a different thing here (empty box) from the failing
          verdict.
        `reasons_substantial` was the one bare `{fail}` genuinely could not carry:
          the token it names belongs to the EXAMPLE slots, and this slot's own
          failing verdict is `absent`, so `{fail}` would have rendered "instead of
          reaching for `absent`" and inverted the rule. That is why `{fail:key}`
          now exists, in olx_prompts._FAIL_RE and score.fill_fail.
      MEASURED, which is what makes this closable rather than claimed. Q5's olx
      prompt changed by exactly one token -- `not_reason` -> `wrong_kind`, verified
      by --diff as a one-line change -- and 1c and reasons_substantial rendered
      BYTE-IDENTICAL on the olx, so only the paper scorer gained anything there.
      EXERCISED: Q5 swept at 6 runs on BOTH sides against the regenerated prompt
      f933e0876c3b, on a freshly dumped idmap_v97 proven to carry the new line:
          Q5 python 19/20 (was 19/20)     Q5 olx 19/20 (was 19/20)
          era CHECKED, 0 cells never agree, out/q5_e11_cli and out/q5_e11_web
      Neutral is the RIGHT result and was predicted: the change buys the ability to
      draw a distinction, not a higher score, and BACKLOG.md recorded that no
      counted cell exercises a refusal at all.
      Created 2026-08-28 because there was no subgoal for it -- only the ratchet,
      which stops the list GROWING and never asked it to shrink. Unlike
      HANDCODED_BUDGET, now at 0, `SLOT_RULE_BACKLOG_BUDGET` sits at 13 with no
      target. That is the difference between a declared problem and a tracked one.
      WHAT THEY ARE: judging text parked in `olx_prompts.SLOT_NOTES`, which the olx
      generator and the agreement.py harness both read and `score.py` does not. So
      the rule reaches two of the three scorers and the paper one grades without it.
        1c:has_own_graph   1c:legend        D1:defines_type   D2:defines_type
        Q1:matches_selected                 Q2:reasons_given
        Q2:wgb_inverts_utb                  Q2:wgb_is_counterpart
        Q5:example_2       matches_chosen_type   named_type
        reasons_failing    reasons_substantial
      NOT THEORETICAL, and the price is on record: five `1a:*` notes were in this
      list until today, and while they were, 1a/p6 scored 0.0 on the paper path
      against 6.0-8.0 on the olx -- the WHOLE item, stably, in 3 of 3 runs.
      Migrating them fixed it and cost nothing elsewhere.
      AND THE SWEEP IMPLICATES FIVE MORE. From the python column's error profiles:
        Q2:wgb_is_counterpart   5 of its 7 refusals land in wrong cells -- the
                                sharpest single signal in the sweep so far
        Q2:wgb_inverts_utb      8 of 16
        Q2:reasons_given        drifts 4 cells
        Q5:example_2            8 of 26 refusals in wrong cells
        reasons_substantial     59 refusals, 7 wrong, and 7 drifting cells on Q5
      Five of thirteen entries turn up in the error tables of the two worst-scoring
      handout-1 items. That is not proof the notes cause the errors -- both columns
      of this sweep READ them -- but it is where to start.
      SCOPE IT HONESTLY: migrating these does NOT change either column of the
      current sweep, because agreement.py reads SLOT_NOTES. It changes score.py,
      the paper scorer, which is the side with no sweep at all. So the payoff is
      measured against the paper corpus, not here.
      THE PROCEDURE IS PROVEN, from 1a: move the text to the credit component's
      `rule` field VERBATIM -- both generators render it, and the olx prompt does
      not move because its checklist looks up `rule` BEFORE SLOT_NOTES and finds
      the same string. Then re-run the leakage gate, which re-asks because a
      verdict is keyed to the prose, and refile with an attribution rather than a
      rubber stamp. Drop the entry, lower the budget, and let the ratchet confirm.
      PROGRESS 2026-08-29: D1/D2:defines_type MIGRATED, 13 -> 11. One edit served
      both, because rubric_h2 builds them from a `_definition_item` factory. OLX
      prompts byte-identical before and after; the paper prompt GAINED 94 chars,
      and what it gained is the point -- its `desc` already carried "which of the
      four types this DEFINITION describes", so score.py was told what to judge
      and NOT the operative half, "do not look at what they chose". That clause is
      what keeps `defines_type` independent of `named_type`, and the two feed the
      `matches_chosen_type` comparison, so a paper grader reading the choice while
      judging the definition collapses two checks that must stay separate.
      No item's olx prompt_sha moved, so the two-sided sweep stays valid.
      THE TRADE THIS MAKES, and it is worth stating because the numbers move in
      opposite directions: SLOT_RULE_BACKLOG 13 -> 11 while PROSE_ONLY_SLOTS
      9 -> 11. That is not a wash. Before, the rule reached two scorers of three
      and nothing said so; after, it reaches all three and is DECLARED as prose
      the audit cannot compare. An undeclared asymmetry became a declared
      symmetry, and the audit prefers the second even though the count is the
      same -- one is a hidden difference in what gets graded, the other is a known
      limit on what can be compared.
      EXPECT THAT TRADE ON EVERY REMAINING ENTRY. Emptying this backlog will push
      PROSE_ONLY_SLOTS up by roughly the same number, unless a rule turns out to
      be expressible as a primitive. Do not read the second budget rising as
      backsliding; read it as the cost of the first one falling.
      SECOND PASS 2026-08-29, 11 -> 4. Five more migrated, two struck off as never
      having been gaps, and one bug caught by diffing the generated OLX:
        MIGRATED   Q2:reasons_given  Q2:wgb_inverts_utb  Q2:wgb_is_counterpart
                   Q5:example_2      reasons_failing     reasons_substantial
        The paper prompts gained what they lacked -- Q2 3791 -> 4560 chars,
        Q5 3161 -> 4346, measured against a git-HEAD baseline rather than a
        capture taken mid-migration, which the first attempt got wrong.
        STRUCK OFF  `matches_chosen_type` is COMPUTED by `equals` from
        defines_type and named_type, so no model is asked about it and NEITHER
        generator renders its note. It reached no prompt at all -- dead text, and
        a `rule` briefly added to its six components was reverted for the same
        reason. It was never a paper-blind rule.
        KEPT, CANNOT MIGRATE  `named_type` -- DAY1, DAY2, WK1 and WK2 carry the
        SLOT with no credit component behind it, so there is nowhere to put a
        rule. D1 and D2 have their own item-scoped notes which take precedence.
      THE BUG WORTH RECORDING: the first attempt put the GLOBAL `named_type` note
      into D1/D2's `rule`, which overrode their item-scoped notes and would have
      rewritten both prompts. Nothing caught it -- not the ledger, whose shas
      still matched because the OLX on disk had not been regenerated, and not a
      prompt-text comparison. `olx_prompts.py --check` caught it, by saying H2 was
      OUT OF DATE. Regenerate and diff the OLX after every migration; a `rule`
      that differs from the note it replaces is a prompt change wearing the
      clothes of a refactor.
      NET AFTER REVERTS: backlog 11 -> 6, PROSE_ONLY_SLOTS 11 -> 14. The only
      prompt that changed anywhere in the corpus is Q2's PAPER prompt, +769 chars,
      verified by capturing every prompt on both generators before and after with
      `git stash` -- the only comparison method here that puts both sides in an
      identical tree. Two earlier attempts at that baseline were wrong: one
      captured "before" after the migration, the other ran HEAD's modules against
      paths that resolved elsewhere and reported all 23 olx prompts as changed.
      TWO REVERTED, and they define the remaining work: `Q5:example_2` and
      `reasons_substantial` name verdict tokens literally -- duplicate/not_reason
      and wrong_kind. Safe in a olx-only note, refused in a shared `rule` by
      check_slot_rules_are_vocabulary_neutral, because the paper scorer would be
      instructed about tokens it cannot emit. `{fail}` fills with ONE verdict and
      example_2 distinguishes two. Rewriting the prose to avoid the tokens changes
      the OLX prompt on a measured item, so these are a scoring change to be
      measured, not a refactor.
      THIRD PASS, same day, prompted by asking WHY the Q5 rewrites would touch the
      olx at all. They would not, and the revert that assumed they would was
      unnecessary: check_slot_rules_are_vocabulary_neutral was flagging every
      literal verdict token on the blanket premise that "the two vocabularies
      differ". That is true of the DEFAULT vocabulary -- the olx's `wrong_kind`
      against the rubric's `not_active`, which ALIAS records -- and FALSE of a
      slot that declares its own. Both generators render the verdict list from the
      component's `verdicts`, so `example_2`, declaring
      [met, absent, not_reason, duplicate], offers all four on BOTH sides.
      The check now tests the slot's own list, and still catches the real hazard
      (verified by injection: a token the slot does NOT offer is caught, one it
      does is silent). Q5:example_2 migrated, paper 3161 -> 3780 chars.
      AND IT FOUND A CONTENT BUG. `reasons_substantial` says "instead of reaching
      for `wrong_kind`" and Q5 OFFERS NO `wrong_kind` on any slot -- the example
      slots run met/absent/not_reason/duplicate and this one runs met/absent. The
      advice names a token nobody on this item can emit, almost certainly a
      leftover from before the example slots gained their own vocabulary, and it
      is in the OLX prompt today. Left in the backlog: fixing the text changes a
      measured prompt, so it is a scoring change to be measured, not a migration.
      THE TRADE, again: PROSE_ONLY_SLOTS rises as the backlog falls.
      FOURTH PASS, 5 -> 3, and the 1c pair split rather than moving together:
        `1c:legend` MIGRATED -- its note reached the olx only and 1c has a credit
        component to host it. Paper prompt 3709 -> 3974 chars.
        `1c:has_own_graph` STRUCK OFF: it is `derived`, computed from the typed
        data fields, so no model is asked and NEITHER generator rendered its note.
        Dead text, like matches_chosen_type. The pair looked identical in the
        backlog and were not.
      RE-EXAMINED 2026-08-29 after being asked whether these are truly necessary.
      ONE IS. THE OTHER TWO ARE WORK WITH A PRICE, and calling them blockers
      overstated it -- the same error as E25's "the paper scorer cannot compute a
      keyword match", which was also a missing implementation read as a missing
      capability.
      THE HOST I SAID DID NOT EXIST DOES: `CLI_CRITERIA_NOTES` names the
      SLOT_NOTES keys the paper scorer renders anyway, via `_C10_TRIGGER` and
      `_criterion_11`, which turn a note into criterion prose. DAY1's paper prompt
      carries "11. `consequence_asserted` — ..." by exactly that route. So a note
      with no credit component is not homeless; it needs a criterion renderer.
      THE PRICE, which is why they are deferred rather than done:
      `_criteria_section` is SHARED, so adding a criterion puts the text in the
      OLX prompt too. That is a measured scoring change on items with a recorded
      six-run baseline on both sides -- exactly what E2 exists to make possible,
      and exactly what must not be slipped in as a refactor.
      THE THREE THAT REMAIN:
        `Q1:matches_selected` -- not a paper-blind RULE at all. The paper sheet
        has no such SLOT, because a .docx has no closed choice to compare against,
        and the asymmetry is already declared in SCORING_DIVERGENCES. It stays
        listed because this list IS the declaration of olx-only notes; striking it
        out just made the reach check demand it back.
        `named_type` -- MIGRATABLE, via a criterion renderer on the pattern of
        `_criterion_11`, adding the key to CLI_CRITERIA_NOTES. Not blocked; the
        cost is that `_criteria_section` is shared, so the olx gains a criterion
        line too. Re-measure the four cadence items after. Worth doing: all four
        have the slot on BOTH sheets and the guidance on neither rubric, and
        `matches_chosen_type` -- which IS scored -- is computed from it.
        `reasons_substantial` -- MIGRATABLE once a one-clause content bug is
        fixed: the text says "instead of reaching for `wrong_kind`" and Q5 offers
        `wrong_kind` on no slot. Fix the clause, then it moves like the others.
        Cost: re-measure Q5, which sits at 19/20 on both sides.
      A SECOND-ORDER EFFECT WORTH KNOWING ABOUT: deleting the dead
      `1c:has_own_graph` note broke the LEAKAGE gate on four unrelated H2 guidance
      blocks. Their text is byte-identical -- same sha at HEAD, where they passed.
      The note contained "a short or unreadable week", so removing it took "short"
      out of the prompt corpus and tipped the detector's threshold on blocks that
      merely use the ordinary idioms "hitting the target" and "falling short".
      Filed as `vocabulary` with that explanation. THE LESSON: the leakage
      detector is corpus-relative, so REMOVING prompt text can flag prose you did
      not touch. Run the leakage gate after a deletion, not only after an edit.
      TWO THAT MAY NOT BE MIGRATABLE, so check before promising 13 -> 0:
      `1c:has_own_graph` and `1c:legend` belong to the item whose olx chart is
      drawn from typed data a paper student cannot supply -- the declared,
      platform-forced 1c deviation. If they cannot move, say so on the entry and
      lower the target to 11 rather than leaving them looking unfinished.
      A `rule` is rendered into BOTH prompts, so it must not name one side's
      verdict token: use `{fail}`. check_slot_rules_are_vocabulary_neutral enforces
      it, and Q4b's five substitution tests are the recorded case of getting it
      wrong.

- [x] E14. **`forbid` and `maps` cannot score on the APP at all. Seven items.** FIXED
      2026-08-29, verified end to end, all seven re-measured and comparable.
      ROOT CAUSE, one line: LLMAction's zod attribute schema is `.strict()` and
      declared neither `forbid` nor `maps`, so every block carrying one was
      replaced by an ErrorNode at parse time. The button rendered with nothing
      behind it; the click was silent; no status was ever written; the cell timed
      out after 300s as `no-cell`. Nothing threw.
      Fixed in lo-blocks (fef13c06): both attributes declared, and `maps` also
      threaded to buildSlotSchema/composeSlotFeedback/publishedSheet, which all
      already accepted it. A SECOND defect was hiding behind the first -- Q4a's
      missing `max="5"` -- and only became visible once Q4a could run (0974736).
      THE GUARD SO IT CANNOT RECUR: enforcement.check_action_attributes_are_declared
      _in_the_block (3235dca). The audit already asked whether the PYTHON harness
      parses every attribute; nothing asked whether the OLX BLOCK accepts it, and
      that is the half the corpus broke on.
      RESULT, all seven on the olx side, era-checked, 0 cells never agreeing:
          Q4a olx 18 of 20  Q4b olx 16 of 19  Q4c olx 17 of 19   (as measured then)
          NR  olx 16/18     DAY1 olx 17/18    DAY2 olx 16/18    WK2 olx 18/18 Q4b/p12, the
      (WK2's olx figure is the 2026-08-30 RE-MEASUREMENT on the clean tree. The
      run recorded here measured 17/18, but it ran from a tree we could not
      certify, so DAY1/DAY2/WK1/WK2 were swept again at 6 runs; DAY1 and DAY2
      came back unchanged, WK1 olx 18/18, WK2 olx 18/18. The ledger holds the
      re-measure; the python side of the same sweep has WK1 18/18 and WK2 17/18.)
      divergence this whole goal was opened over, now returns 3.5 on BOTH engines
      where it was python 5.0 / olx 3.5. The equivalence half of that cell is closed;
      the gold half is Q18.
      Found 2026-08-29 by the two-sided sweep, which is the job it was for. The
      affected items fail EVERY cell on the olx side with
      `did not settle within 300s (status=undefined)`. Not a divergence between
      two answers -- an item that cannot be asked at all.
      SEVEN ITEMS: Q4a, Q4b, Q4c, NR, DAY1, DAY2, WK2. Six carry `forbid=`; Q4b
      carries `maps=`. Every other item in the corpus scores normally.
      THE CONTROLLED COMPARISON IS PR vs NR. Same handout, same five `!`-prefixed
      gate slots, same shape -- NR has `forbid=` and fails, PR does not and
      passes. That exonerates the `!` prefix, which was the first suspect and is
      used 47 times in handout 2, and it isolates the attribute.
      WHAT THE TWO SHARE, and `counts` does not. `forbid` and `maps` are the two
      primitives that BOTH declare `excludesKeys` AND synthesise a check key the
      model is never asked for. `counts` excludes keys without synthesising one,
      and Q1, which uses it, scores fine.
      MECHANISM, as far as the frozen environment allows. The button IS found and
      clicked -- `findByRole` would throw at 20s otherwise. What never happens is
      `status()` leaving undefined: it reads `comp()[k]?.state` for a redux key
      containing the feedback id, and THE FEEDBACK COMPONENT NEVER ENTERS REDUX.
      So nothing throws, nothing retries (`shouldRetry` will not retry an
      undefined status), and the cell waits out 300s and reports `no-cell`.
      RULED OUT: the idmap (clean, all nine components per item present, no
      garbage keys); the response schemas (all build, no property/required
      mismatch); `!` slots and `forbid` "in general" as categories; the LLM
      backend (Azure answers, and Q1/Q3/Q5/PR score live).
      HOW IT GOT PAST EVERYTHING. maps.test.ts passes 8 unit tests, probe.test.ts
      was taught the attribute, enforcement is clean, the self-test detects 49 of
      49, and `forbid` has been in the corpus for weeks. Every one of those
      exercises the primitive in isolation; none drives a cell through the running
      app. This is the case that `check_closed_goals_that_changed_code_were_
      exercised` was written for, and `maps` is its declared entry.
      SO SUBGOAL 10 IS NOT ACTUALLY CLOSED, whatever its checkbox says, and
      Q4b/p12 -- the 5.0-vs-3.5 divergence this whole goal was opened to explain
      -- is still unmeasured on the olx side. Do not quote a olx figure for any
      of the seven; there is none.
      FIX, in this order, and NOT while a sweep is running: slotSheet.ts IS in the
      scoring path, unlike the idmap preflight fixed the same day, so changing it
      mid-sweep would put later items in a different era from earlier ones.
      (a) reproduce with the single-cell runner, which is what surfaced the real
          error once `stderr=DEVNULL` was bypassed:
          `RUN_LLM_RUNNER=1 JOBS_JSON=<one job> RESULTS_JSON=<out> IDMAP_JSON=...
           npx vitest run packages/shared/lib/llm/runner.test.ts`
          NR and PR are the pair to run: one line of difference, opposite results.
      (b) find why a sheet carrying a synthesised check key never mounts its
          feedback component. Suspect the schema build path rejecting or
          awaiting a key that is in `required` but never answered.
      (c) add an APP-LEVEL test that drives one `forbid` cell and one `maps` cell
          end to end. The unit tests cannot catch this class and did not.
      (d) re-run the seven: `sweep_app.sh` skips items whose .json exists, so a
          plain re-run picks up exactly these.
      A TIMEOUT IS THE WRONG FAILURE for a sheet the app cannot build. 300s a
      cell, ~90s amortised, three hours an item, and the only signal is
      `no-cell`. Four of the seven were killed mid-sweep to recover ~12 hours.

- [x] E27. **The two scorers' verdict vocabularies differ BY DESIGN. Audit what respects that.** DONE
      Filed 2026-08-30 as "two sources of truth, disagreeing", which was WRONG and
      is corrected here. slot_vocab.py says it plainly: WEB_EXTRAS come from
      slotSheet.ts, RUBRIC_EXTRAS from the credit components' `verdicts` lists,
      "and a rule may legitimately mention neither". `wrong_kind` is the olx's
      token, `not_reason` the rubric's counterpart. Nothing is stale.
      HOW THE MISREADING COST A CELL: taking the rubric list as "what this slot
      offers", I renamed reasons_substantial's `wrong_kind` to `not_reason` as a
      dangling reference. The python column lost a cell, 0 over-credits and 12 under,
      because the rename pointed a LIVE instruction at a token that side cannot
      emit. Reverted; Q5 is 19/20 on both sides with both shas matching.
      AND I WEAKENED THE CHECK THAT WOULD HAVE STOPPED IT, twice: first to "only a
      token this slot does not offer", then unioning the rubric list with the OLX
      spec. Both were built on the same false premise, and the second actively
      hid the case the check exists for. RESTORED to its original strictness --
      any literal token from either list, in a shared `rule`, is a finding.
      THREE MIGRATIONS REVERTED as a consequence, and they are olx-only BY DESIGN
      rather than backlog work: `Q5:example_2` (names `not_reason`),
      `reasons_substantial` (`wrong_kind`), `1c:legend` (`incomplete`).
      THE REMAINING WORK IS `{fail}`, not migration. Each needs rewriting around
      the placeholder each generator fills with its own token. Workable for
      reasons_substantial and 1c:legend, which name ONE failure; not for
      example_2, which distinguishes `duplicate` from `not_reason` and would need
      a second placeholder that does not exist. Any rewrite changes a measured
      prompt.
      A SECOND SWEEP, asked for after the first: where else did not knowing the
      two vocabularies produce a wrong result? Two, both in the check itself:
        `unclear` WAS MISCLASSIFIED. It sat only in WEB_EXTRAS while TWENTY-ONE
        rubric slots declared it -- Q1's utb_stated, all five of Q3's, both
        keyword slots, D1/D2's type slots, 1a's four week slots, 2a's verdict. It
        is offered by both sides and always was; the list did not say so. A
        shared rule naming it would have been refused as one-side.
        `duplicate` IS IN BOTH LISTS and the restored check flagged it anyway --
        it was part of why Q5:example_2 read as doubly blocked.
        Fixed by deriving SHARED_EXTRAS = WEB_EXTRAS ∩ RUBRIC_EXTRAS and exempting
        it. Not a relaxation: naming a token BOTH sides offer instructs nobody
        about something they cannot emit. Verified by injection that wrong_kind,
        not_reason and incomplete are still caught while unclear and duplicate
        are not.
      NEITHER CHANGED A BACKLOG DECISION -- example_2 still names `not_reason`,
      reasons_substantial `wrong_kind`, 1c:legend `incomplete`, all one-side, all
      still blocked on a `{fail}` rewrite. Checked rather than assumed.
      SUPERSEDED 2026-08-30 BY E11, and the paragraph above is left standing only
      so this correction has something to point at. All three migrated. The claim
      that `{fail}` was "workable for reasons_substantial and 1c:legend, not for
      example_2" was wrong in BOTH directions: example_2's second failure mode is
      `duplicate`, which both sides offer, and reasons_substantial was the one
      that needed a new form -- `{fail:key}` -- because the token it names belongs
      to a SIBLING slot. See E11.
      THE SECOND SWEEP, 2026-08-30, and it found the exemption itself was wrong:
        SHARED_EXTRAS WAS A GLOBAL ANSWER TO A PER-SLOT QUESTION. Whether a token
        is shared is a fact about a SLOT; the intersection of two corpus-wide
        lists cannot say it. `unclear` is in both lists and the two sides DISAGREE
        on SEVENTEEN slots -- 2a.how_*, 2b.sentence_*, 3.example_*, Q1.reason_*,
        Q2.reason_*, D1/D2's add_or_remove and increase_or_decrease -- where the
        olx offers it and the paper has only met/absent. Exempting it globally
        left a shared rule free to name it on any of those. No rule did, so it was
        LATENT -- which is how the Q4b instance started.
        Not a renaming, checked: those slots declare no third token under any
        name, unlike Q5's `wrong_kind`/`not_reason` and 1c's
        `incomplete`/`not_described`, which are genuine counterparts. It is a
        three-valued olx slot against a two-valued paper one. Score impact is NIL
        -- `unclear` is not satisfied, so it deducts exactly as `absent` does --
        so the asymmetry is diagnostic, not arithmetic. Undeclared all the same.
        `wrong_kind` IS THE SAME SHAPE IN REVERSE: shared on Q4b's behavior_*,
        which declare it in the rubric, and olx-only on Q4a's antecedent_*, Q4c's
        consequence_* and Q5's example_*. So RUBRIC_EXTRAS was incomplete without
        it AND adding it would have exempted it globally, re-opening the hole on
        six slots to describe two. Neither branch of that is right, which is what
        made the global form indefensible rather than merely imprecise.
        FIXED by asking the per-slot question directly:
        check_slot_rules_are_vocabulary_neutral now reads the OLX sheet (with
        `pick(NAME)` enums resolved) and the credit component, and requires a
        literal token to be offered by BOTH for THAT slot. Verified by injection
        on all three behaviours: the latent `unclear` case is caught, Q4b's
        genuinely-shared `wrong_kind` is allowed, and Q5's one-sided `wrong_kind`
        still fires. No exemption list is needed and SHARED_EXTRAS is no longer
        load-bearing; its comment now says so, so it is not reinstated.
        THREE TOKENS WERE INVISIBLE TO EVERY CHECK. KNOWN_VERDICTS is the scan
        vocabulary, and `not_antecedent`, `not_consequence` and `not_described`
        -- the paper's failing verdicts for Q4a, Q4c and 1c -- were not in it. A
        shared rule naming one would have instructed the OLX about a token it
        cannot emit and passed everything. Added. `not_active` is kept and marked
        HISTORICAL: no slot declares it any more, since Q4b's now declare
        `wrong_kind`, which is why the pair in every docstring citing that
        incident no longer exists anywhere else.
        `desc` IS A THIRD PROSE SOURCE and was unguarded. When a slot has no
        `rule` and no note, the olx falls through to the credit component's
        `desc` and score.py uses that same `desc` -- so it reaches BOTH scorers
        under exactly the conditions a `rule` does. Clean today, no `desc` names
        a verdict, and now checked per-slot so it stays that way.
        TWO COMMENTS CLAIMED enforcement.ALIAS RECORDS THE VERDICT BRIDGE. It
        does not, and never did: ALIAS maps slot KEY names (`behavior` ->
        `names_behavior`) and contains no verdict token at all. A reader taking
        those comments at face value would go looking for a mapping that has
        never existed. Corrected in olx_prompts.py and enforcement.py; the bridge
        is `{fail}`, resolved per side at render time.
      THE ASYMMETRIES ARE NOW DECLARED, not merely described in a comment. The
      two verdict spaces differ on 48 slots, in eleven SHAPES, and
      enforcement.VERDICT_SPACE_DIVERGENCES declares them by shape with
      check_verdict_spaces_are_declared as its verifier. By shape and not per
      slot on purpose: 48 entries would read as coverage while enforcing nothing,
      and what is worth catching is a NEW kind of asymmetry, not the 17th
      instance of one already understood. Verified by injection -- an
      undeclared shape is reported, the clean tree is silent.
      NOT PUT IN SCORING_DIVERGENCES, and that is the interesting part: it looked
      like the obvious home and is the wrong one. That table's entries suppress
      findings by ITEM (`undeclared = [f for f in findings if f[0] not in
      declared]`), so declaring the `unclear` asymmetry there would have silenced
      every scoring finding on 2a, 2b, 3, Q1, Q2, D1 and D2 -- seven items -- to
      record a difference that moves no score. Its own comment says a stale
      exemption is worse than none; an overbroad one is the same failure written
      forward.
      CLOSED 2026-08-30. Gates clean (enforcement 0, equivalence 0 undeclared),
      self-test 51 of 51 with all three vocabulary cases passing, including the
      one whose mechanism was replaced underneath it.
      THE AUDIT SWEEP THE USER ASKED FOR, done 2026-08-30, is recorded in
      slot_vocab.py beside the lists themselves:
        FIXED   cross_path._slot_diffs compared RAW verdict strings between
                artifacts. Correct for harness-vs-app, which share the olx's
                vocabulary; a false-positive generator the moment a PAPER
                artifact is compared, where the counterpart tokens would report
                every such slot as divergent. It now folds to satisfied/failed
                only when the kinds differ, and keeps the raw tokens otherwise.
                It also referenced `lkind`/`rkind`, which were not parameters --
                a NameError waiting for the first divergent slot.
        SAFE    agreement.is_satisfied and slotSheet.isSatisfied compare against
                the slot's OWN options, so they are right under either
                vocabulary; measured.error_profile reads them rather than
                matching strings; head_to_head counts verdicts without comparing
                tokens across sides; _fail_token/_fail_verdict are per-side by
                design and must stay so.

- [ ] E28. **A paper sweep the ledger can record, on either model.**
      FIRST NUMBERS RECORDED 2026-09-01, on two items only: Q4a paper 15/20 and
      Q4c paper 17/19, six runs each on gpt-5-mini through `--backend lo`, folded
      by paper_runs.py and recorded on the `paper` side. So the machinery built
      on 2026-08-30 is confirmed working against the CURRENT corpus, not just the
      discarded one -- which is what left this goal open with an empty column.
      THIS DOES NOT CLOSE IT. The deliverable is the corpus, and 24 of 26 items
      still have no paper number. The scoped run used score.py --items directly
      rather than sweep_paper.sh, which sweeps all three handouts at ~519 calls a
      run; the full six-run sweep is ~3,100 calls and is the remaining work.
      ONE DEFECT FOUND BY THE FIRST REAL FOLD: measured._artifact_program read a
      folded paper artifact as unclassifiable, and an unclassifiable artifact
      skipped the side-contract program check entirely. Fixed under E25.
      The third scorer could be RUN and not RECORDED. `cross_path.result_cell`
      read the app's `cell` shape and the harness's `participant_id` shape;
      score.py writes `rN/hM/participant_NNN.json` with an `items[]` list, which
      neither. So `measured.record` failed on a paper artifact exactly as it
      failed on a olx one before the reader was shared -- the same gap, still open
      for the third path, and the reason no paper number has ever entered the
      ledger.
      BUILT 2026-08-30, and verified end to end against the old corpus before it
      was discarded: Q1 18/20, PR 17/18, 1a 18/20 recorded on a `paper` side
      beside the existing python and olx columns.
        result_cell   reads the paper shape too, folding `credit_checks` to
                      met/absent so nothing downstream knows which scorer it came
                      from.
        paper_runs.py folds a sweep into the per-item `.runs.json` the ledger
                      records, one file per item, matching sweep_cli/sweep_app.
        sweep_paper.sh drives the runs score.py has no --runs for, into rN/hM/,
                      resumable per slice via a .done marker.
      TWO SIDES, NOT ONE: `paper` is score.py on gpt-5-mini (`--backend lo`,
      through the dev server) and `paper_opus` is score.py on Opus (`--backend
      api`/`python`). Only the first is comparable to the olx and python columns, both
      of which ran on gpt-5-mini; an Opus paper run varies the model AND the path
      at once and can settle neither. Recording both under one key would make each
      overwrite the other with `previous` implying a progression that never
      happened.
      AND THE ERA NOW RECORDS THE MODEL, which it never did. Every measurement
      before today is silent about what answered it -- survivable only while
      everything ran on one deployment, and unattributable the moment two models
      are in play. `era_stamp(model=, backend=)`, defaulting to
      AZURE_DEPLOYMENT_ID, stamped by the writer because that is the only thing
      that knows.
      COST, measured from the real prompts rather than estimated: 519 scored cells
      a run, ~2,060 input and ~720 output tokens a call. Six runs is ~3,100 calls,
      6.4M in / 2.3M out -- single-digit dollars on gpt-5-mini and roughly forty
      times that on Opus.
      STILL BLOCKING A SWEEP, updated 2026-08-30: E11 is DONE -- its Q5 and 1c
      prompt changes have landed and been re-measured -- so what remains is E15
      (Q6) and E25 (Q4a, Q4c). Sweeping before those costs a re-sweep of three of
      twenty-six items on every side.
      LIVE-VERIFIED 2026-08-30 on the current tree, which the earlier end-to-end
      check no longer covered: score.py changed that day, and Q5 and 1c gained
      migrated rules the PAPER scorer had never been given. A three-call smoke
      test through `--backend lo`:
        the paper prompt for Q5 carries `not_reason` and NOT `wrong_kind`, so
          `{fail}` and the new `{fail:example_2}` resolve to the PAPER's
          vocabulary in a live run and not merely in a static render;
        `reasons_substantial` came back `absent` -- the verdict its newly-arrived
          rule describes, on the slot the paper scorer never had a rule for;
        result_cell read both artifacts, paper_runs folded them to the ledger's
          shape, and the era carried model=gpt-5-mini and the matching
          prompt_sha f933e0876c3b.
      AND IT FOUND ONE: score.py called era_stamp with no `backend`, so every
      per-participant artifact stamped "". The ledger was unaffected, because
      paper_runs passes it at fold time from sweep_paper.sh -- but the file that
      survives if a fold is ever redone by hand could not say whether it was the
      gpt-5-mini run or the Opus one, which is the single distinction `paper` and
      `paper_opus` exist to keep apart. score.py knows it (`rec["backend"]`, two
      lines above) and now passes it. Fixed and re-verified.
      THE FIRST FIX WAS HALF A FIX, caught by asking whether it was really fixed
      rather than assuming: it stamped `rec["backend"]`, the CLASS name, so the
      field read "LoBlocksBackend" from score.py and "lo" from paper_runs -- one
      field, two vocabularies, decided by which writer filled it, in the field
      the side is keyed on. It now stamps `args.backend`, the token
      sweep_paper.sh passes to both. Verified: both writers now say `lo`.
      `rec["backend"]` keeps the class name, which answers a different question
      and sits beside supports_tools.

- [x] E29. **`error_profile` ignores cell exclusions, and its one-sided flag lied.** DONE
      AN AUDIT SUBGOAL. `measured.error_profile` applies corrected gold and
      `rebuild_gold_1c` but never filters EXCLUDED cells: it profiles all 20,
      while every figure the ledger publishes is over 18. On the twelve H2 items
      that is p2 and p3 -- 10% of every profile's observations, declared suspect,
      feeding the DIRECTION verdict and the "one-sided: a threshold is set wrong,
      not unstable" line.
      FOUND 2026-08-30, and found the expensive way. The clean-tree re-sweep's
      profiles reported WK1 8 over / 1 under and WK2 11 over / 4 under, three of
      the four flagged one-sided. A subgoal was filed on that reading, claiming
      p3 carried 24 of 37 over-credits and that a threshold was set wrong. p3 is
      an EXCLUDED cell on both items. With exclusions applied:
          WK1 python  2 over / 1 under      WK1 olx  2 over / 0 under
          WK2 python  5 over / 4 under      WK2 olx  4 over / 2 under
      WK2 is balanced, not one-sided, and WK1 is two observations out of 108 on
      one cell. There was nothing to investigate. The whole finding was the
      excluded cells.
      WHY IT MATTERS beyond one wasted subgoal: this profile is the diagnostic
      memory/error-profile-by-slot.md says to run after EVERY sweep, precisely
      because a median never says which judgement is wrong. A diagnostic trusted
      that way must not be computed over a different cell set than the number it
      is diagnosing. The BY SLOT and DRIFT tables have the same defect.
      DELIVERABLE: filter excluded cells in `error_profile`, the way
      `cross_path.against_gold` already does via `_excluded_cells`; state the
      observation count as n/18-based so a reader can see which set it used; and
      re-read the four H2 profiles above afterwards to confirm nothing survives.
      DO NOT re-file the p3 subgoal on the strength of the raw numbers. If p3 is
      worth looking at, that is a question about whether its EXCLUSION is still
      justified -- a different claim, resting on the citation behind the
      exclusion, not on scores computed from a cell nobody counts.
      FIXED 2026-08-30. `error_profile` now skips excluded cells -- the same set
      `record` leaves out -- and names the set it used in its header, e.g.
      "over 108 observation(s), 18 of 20 cell(s) -- excluding p2, p3". A reader
      comparing the profile to the ledger can now see WHICH cells it covers
      without reading the code, which is the whole failure.
      RE-READ, and the fix did TWO things, not one:
        It removed false signals. WK1 8 over / 1 under -> 2 over / 1 under; WK1
          olx 8/0 -> 2/0; WK2 11/4 -> 5/4; WK2 olx 10/2 -> 4/2. The one-sided
          flag correctly stops firing on all of them. Nothing to investigate,
          exactly as the recomputation predicted.
        It REVEALED a true one it had been masking. DAY1 python read 7 over / 8
          under -- two-sided, "the judgement is unstable" -- and is actually
          1 over / 8 under, now flagged one-sided. The two excluded cells were
          contributing 6 of the 7 over-credits. DAY1 olx is 0 over / 7 under.
          So DAY1 UNDER-credits on both sides, one-sided, and the masking hid it.
          Its BY SLOT table names `matches_chosen_type` as tracking the errors
          (6 in wrong cells against 6 in right). That is a QC question and wants
          its own subgoal; do not fold it in here.
      CROSS-CHECKED against the other accounting path: 1c now profiles 17 of 20
      cells (excluding p4, p19, p20), agreeing with its 16/17 ledger figure, and
      still reports the ZERO over-credits the rebuild_gold_1c note demands.

- [x] E15. **`requires` is implemented on BOTH engines and bound to nothing. Q6 is why it exists.** DONE
      Surfaced 2026-08-29 by the new live-exercise check, which listed `requires`
      as used by NO item. It is not dead code: slotSheet.ts parses and applies it,
      agreement.py and score.py compute it, primitives.json declares it. Only the
      OLX half was never written -- `requires=` has never appeared in any handout,
      in any commit.
      ITS OWN IMPLEMENTATION NAMES THE USER. slotSheet.ts: "Q6 is why it exists.
      Its eight slots are four (element, treatment) pairs, and the sheet asked
      each box whether its consequence was named and whether an effect was
      described -- but never which antecedent's change PRODUCES that effect. A
      response addressing one antecedent in a single run-on sentence therefore
      banked both consequence pairs from one clause, where the graders charged
      the whole second half. Asking the linkage as its own check gives `cover` a
      duplicate to spot; `requires` is what lets that answer reach the pair it
      governs."
      THE WORKAROUNDS FOR ITS ABSENCE ARE STILL IN THE TREE, which is the
      evidence that the need is real and unmet:
        * `affect_c2`'s rule hand-encodes the missing constraint in prose -- "the
          two effect boxes must be about DIFFERENT consequences... only the FIRST
          of the two can count";
        * Q6/p5 is a DECLARED DIVERGENCE, DUPLICATE_EFFECT_TIE_BREAK, over
          exactly the duplicate the comment says `cover` would spot.
      WHY THIS IS THE RIGHT LEVER AND THE NINE FAILURES ARE NOT AN ARGUMENT
      AGAINST IT. memory/q6-matching-ceiling.md records nine rule wordings built,
      measured and reverted, and concludes: "the ceiling is not a wording problem
      waiting for the right words... The ceiling is in the ITEM -- in how
      `refers_to` is answered -- not in how matching is worded." Every one of the
      nine was PROSE. This is structural: a new slot and a computed dependency,
      the class memory/structural-before-wording.md says to try FIRST and which
      Q6 has never had. The note says not to propose a tenth WORDING without
      reading it; it has been read, and this is not one.
      THE DESIGN, from the parse doc, which already anticipates the hazard:
      `requires="state_c2:link_c2:unclear|affect_c2:link_c2:unclear"`. The third
      segment lists verdicts on the condition that establish nothing and so deny
      nothing -- "a condition answered `unclear` is the model declining to say;
      reading that as a denial charges the student for the grader's hesitation."
      Use it. Q6 under-credits when tightened, every time.
      A SECOND SITE, found 2026-08-29 by asking where else this is needed rather
      than assuming Q6 was alone. Ranked by over-credit, since `requires` DENIES
      credit and can only help an item that over-credits -- wiring it into an
      under-crediting item pushes it further the way it is already wrong:
        * Q6   +14 (23 over / 9 under). Has `cover` -- the duplicate SPOTTER --
          and over-credits anyway. That is direct evidence for the split the
          implementation describes: cover spots it, `requires` is what acts on it.
          Q6 has half the mechanism.
        * Q4c  +17 (18 over / 1 under), the most one-sided on the board after 2a.
          Same (element, element) pair shape as Q6 -- consequence_1/consequence_2
          -- with NO cover, NO onlyif, NO requires. Its only `forbid` fires when
          BOTH boxes are absent, the opposite end of the problem. So it has no
          way to notice that the second box restates the first, which is exactly
          the second-box collapse recorded against it and Q4b.
      THE SECOND-BOX EVIDENCE, folded in from subgoal Q18 on 2026-08-29 because
      it is the same defect seen from the other end. All three second-box items
      show the identical asymmetry -- the second slot unmet far more often, and
      far more often in a WRONG cell:
        Q4c  consequence_1  6/0    consequence_2  19/7
        Q6   state_c1      15/6    state_c2       58/17
        Q6   affect_c1     26/8    affect_c2      75/22
      That is precisely the failure `requires` was written for: "a response
      addressing one antecedent in a single run-on sentence banked both
      consequence pairs from one clause." A second box scored off the first box's
      content is a duplicate that `cover` can see and nothing acts on.
      Q4b IS EXCLUDED FROM THIS SUBGOAL, deliberately, and this is the trap the
      merge existed to create: it shows the same symptom (behavior_1 23/0 vs
      behavior_2 52/17) with the OPPOSITE direction -- 7 over / 12 under, because
      `maps` DENIES its second box credit. `requires` denies credit too, so a fix
      measured across all three would be judged partly on an item it must make
      worse. Q4b stays in subgoal Q18.
      NOT `requires` CASES, checked and rejected so the list is not padded:
        * 2a +29 -- `counts:hows_given:how_1,how_2`. "said 2, scored 6 against
          gold 4": gold counts sentences that EXPLAIN HOW, the model counts
          sentences. A counting definition, not a cross-slot dependency.
        * Q3 +10 -- bare SMART slots, no primitives. A measurable-requires-
          specific dependency is plausible but is not asserted by the rubric or
          the record; inventing one is the wording trap in a new costume.
        * WK1/WK2 +7/+6 -- already compute `matches_chosen_type` via `equals`.
        * 1c +9 -- the declared COMPUTE_EXEMPT chart item.
      SEQUENCE, and it is not first in the queue:
      (a) BLOCKED ON SUBGOAL 14. This adds a slot the model is asked, so it can
          only be judged by a live app run, and `forbid`/`maps` prove a primitive
          can pass every unit test while the app cannot build the sheet. Fix that
          first, then exercise `requires` live BEFORE closing anything -- the
          rule from subgoal E12/13's episode, now enforced.
      (b) Baseline first: Q6's python six-run median WAS 16/20, runs
          [15,15,15,16,16,16], and the olx column was 16/20 too. MEASURED
          2026-08-31 after the change: python 17/20 [16,16,16,17,17,17] and olx
          18/20 [14,17,18,18,18,18].
      (c) Measure at SIX runs. The note is explicit that a 3-pass sweep cannot
          resolve a two-cell move on this item: only 5 of 20 cells returned the
          same judgement across three passes.
      (d) Predict per cell before measuring. p5 is the target. p2 over-credits
          +1.25 in every recorded run and is the cell a narrower rule has fixed
          twice. p19 and p10 are the historical casualties.
      IMPLEMENTED 2026-08-30, unmeasured. `link_c2` is a new REPORTED slot -- "the
      second consequence pair is about a DIFFERENT consequence from the first",
      met/absent/unclear -- and
      `requires="state_c2:link_c2:unclear|affect_c2:link_c2:unclear"` denies the
      pair when it answers `absent`. The duplicate-detection prose was MOVED, not
      copied: it left affect_c1's and affect_c2's rules and became link_c2's, so
      one mechanism decides it. Leaving both would confound the measurement and,
      if they ever disagreed, the prose would silently win.
      THE E14 GUARD PASSES: check_action_attributes_are_declared_in_the_block
      reports the LLMAction schema accepts `requires`, so the failure that made
      `forbid`/`maps` unscorable on the app does not apply here. That is a static
      result and does not replace the live run.
      TWO AUDIT DEFECTS FELL OUT OF IT, both fixed:
        _credit_fail could FAIL A SLOT TO A LENIENT VERDICT. Failing link_c2
          alone picked `absent` and cost 2.5, but in a PAIR the `avoid` argument
          pushed it to `unclear` -- which `requires` is written to forgive -- so
          every pair containing link_c2 read as sublinear and the audit reported
          SIX charge-once divergences against a rule that has none. Same class as
          the cover-label case already recorded there: the probe must fail the
          slot, not re-answer it in a way the primitive forgives. Fixed; Q6's
          charge_once is now exactly the two declared `requires` pairs.
        _primitives_with_live_app_evidence ACCEPTED A STALE MEASUREMENT. It
          counted any item with a `olx` ledger entry as evidence, so Q6's number
          -- recorded before `requires` existed -- was read as proof that
          `requires` had run live. That is the precise fiction this rule exists to
          prevent, arriving through the check meant to enforce it. It now requires
          the recorded prompt_sha to match the prompt on disk. `requires`
          correctly shows NO evidence, and `cover` correctly drops to none,
          because Q6 is the only item that carries it and its measurement is now
          stale. Both are re-established by the same sweep.
      THE PREDICTION, written before measuring, and it is LESS optimistic than
      this subgoal's original framing. Q6's over-credit by cell, 6 runs, both
      sides, exclusions applied:
          p8 15.0 pts   p2 7.5   p6 3.75 (python only)   p5 1.25   p4/p16/p18 ~1.25
        p8 WILL NOT MOVE, and it is half the over-credit on the item. Its 2.5 a
          run is the two CHANGE slots, declared A_NO_CHANGE -- gold charges both
          for a scheduling commitment where the antecedent was a not-doing.
          `requires` gates the CONSEQUENCE pair and cannot reach it.
        p5 MAY GET WORSE, and this is the one to watch. DUPLICATE_EFFECT_TIE_BREAK
          says our sheet applies a duplicate rule to the effect boxes and GOLD DOES
          NOT: p5 writes the cleanest parallel answer in the corpus and gold credits
          both boxes. Making that rule computed rather than prose makes it fire
          more reliably, which entrenches the disagreement instead of settling it.
          The subgoal called p5 "the target"; the divergence record says p5 is
          where our rule already costs us. Both cannot be right, and the record is
          the older and more specific claim.
        p2 IS THE REAL CANDIDATE, and it can overshoot. It over-credits 1.25 a run
          on both sides -- HALF what `requires` denies. If the c2 pair is the
          source, the denial takes 2.5 and turns a +1.25 into a -1.25. A sign flip
          is the outcome to look for, not a win.
        p6 is the cleanest possible gain: 3.75 over on the python only, no
          declaration standing over it.
      SO THE HONEST EXPECTATION is neutral-to-small, with a real chance of losing
      p5 and flipping p2. The case for measuring is not the projected number: it
      is that the duplicate rule is currently a request no scorer can act on, and
      after this it is arithmetic the audit can compare between the two.
      IF IT FAILS, the honest outcome is to RETIRE `requires` from
      primitives.json rather than leave a primitive in the registry that nothing
      uses and nothing can use. A registry entry no item can justify is a claim
      about the system that is not true.
      CLOSED 2026-08-31. Measured at six runs on both sides against the
      regenerated prompt 3b72b21974a0, era-checked, 0 cells never agreeing:
          Q6 python 17/20 [16,16,16,17,17,17]   was 16/20 [15,15,15,16,16,16]
          Q6 olx 18/20 [14,17,18,18,18,18]   was 16/20
      out/q6_e15_cli, out/q6_e15_web. `link_c2` answered `absent` on 51 of 120
      python observations and 61 of 120 olx, so `requires` denies the pair on about
      half the corpus -- it is doing work, not sitting inert. Note the olx spread
      is 4, one run at 14: the median moved but the item is not stable.
      UNEXERCISED_PRIMITIVES is now EMPTY, budget 1 -> 0. Every primitive in the
      registry has an item that justifies it, and this one is exercised LIVE, not
      merely wired -- the standard E12/E13's episode put in place.
      THE PREDICTION SCORED 2 OF 4, and the misses were the useful part:
        p8 did not move (15.0 both before and after). Predicted exactly: its
          over-credit is the two CHANGE slots under A_NO_CHANGE and `requires`
          gates the consequence pair.
        p6 improved, 3.75 -> 1.25. Predicted as the cleanest available gain.
        p2 did not move AT ALL, 7.5 -> 7.5. Predicted to overshoot; `requires`
          never fired there, so p2's over-credit is not the duplicate-second-pair
          the prediction assumed. Its cause is still unknown and still the
          largest unexplained over-credit on the item after p8.
        p5 got much BETTER, not worse, which is the finding. Predicted to degrade
          because DUPLICATE_EFFECT_TIE_BREAK records that gold credits both
          effect boxes and our duplicate rule costs us the cell. Instead:
              p5 olx  5.0/5.0/6.25/6.25/6.25/7.5  ->  6.25 x6   (gold 6.25)
              p5 python  5.0/6.25 x4/7.5             ->  6.25 x5, one 7.5
          `link_c2` answered `absent` in ALL twelve runs. Denying the WHOLE pair
          arithmetically lands on gold; the prose version denied only affect_c2,
          and did it inconsistently. The declaration's REASONING was wrong, and
          trusting it over the mechanism is what made the prediction wrong.
      See subgoal Q28 for what that costs and what is left to do about it.

- [x] E19. **Re-test PROSE_ONLY_SLOTS' "NOT CONVERTIBLE" claims when the primitive set changes.**
      DONE 2026-08-29, implemented the same day it was filed (249655f).
      `PROSE_ONLY_JUDGED_AGAINST` stamps each of the nine entries with the
      primitive set it was judged against; `check_prose_only_claims_are_current`
      fails when the registry no longer matches, and is wired into the audit and
      registered in DECLARATION_TABLES. It fires exactly once per primitive
      added, which is when the answer can have changed.
      Injection-tested three ways: a new primitive landing flags all nine, an
      unstamped entry is caught, an orphaned stamp is caught. Key sets must match
      in both directions.
      WHAT THE BASELINE STAMP ASSERTS, recorded so it is not read as more: that
      these nine reasons stand against today's nine primitives. Verifiable for the
      three that name one -- Q4b:b1_basis argues from `maps`, Q6:affect_c1 from
      `cover` -- and the rest were last written 2026-08-28/29, after `maps`
      landed. It is NOT a re-judgement of each rule from scratch; it is the dated
      baseline the check measures drift from.
      CLOSED WITHOUT CLEARING THE TABLE, which was the original request and the
      wrong target: check_prose_only_slots_are_declared does not aim at zero, all
      nine already argue why they cannot be primitives, and the budget stays 9. A
      re-judged entry that is still not convertible just gets a new stamp.
      NEXT TIME IT FIRES: `requires` landing on Q6 under E15 will flag both Q6
      `affect_*` entries, since their reasons turn on what `cover` already
      constrains.
      Asked for as "a subgoal to clear PROSE_ONLY_SLOTS". IT SHOULD NOT BE
      CLEARED, and the record says so in terms:
      check_prose_only_slots_are_declared's own docstring -- "Unlike
      HANDCODED_BUDGET this does not target zero ... the honest end state is that
      every remaining entry argues, in its reason, why it cannot be a primitive."
      All nine entries already do, all nine read NOT CONVERTIBLE, and
      `check_convertible_prose_rules_have_subgoals` already forces a subgoal for
      any entry marked CONVERTIBLE. There are none. The table is at its intended
      end state.
      THE REAL EXPOSURE IS THAT "NOT CONVERTIBLE" IS A CLAIM THAT CAN GO STALE,
      which is the same defect class as the Q4a arithmetic divergence and the
      auto-killer: a judgement that was true when written and that nothing
      re-tests. Convertibility is judged AGAINST THE PRIMITIVE SET, and the
      primitive set grows -- `maps` did not exist a week ago.
      THREE OF THE NINE REASONS NAME A PRIMITIVE, so they are explicitly
      relative to that set rather than absolute:
        Q4b:b1_basis  "`maps` turns this classification into behavior_1's
                       verdict arithmetically, so the COMBINING is declared and
                       only the classification is read"
        Q6:affect_c1  "`cover` already constrains WHICH listed entry is referred
                       to; what is left is whether the answer states HOW"
        1a:week_1     "no operand pair expresses it"
      Q4b's entry is the proof of the mechanism: `maps` CHANGED what was
      convertible about that slot, and the entry was rewritten to say so. Nothing
      forced that rewrite -- it happened because the same person was holding both
      pieces at once, which is exactly what does not scale.
      THE FIX IS A STAMP, not a re-audit by hand. Record on each entry the
      primitive set it was judged against -- a fingerprint of the `attr` names in
      primitives.json -- and have the check fail when the current set differs:
      "`Q6:affect_c1` was declared NOT CONVERTIBLE against {cover, equals,
      onlyif, requires, derived, counts, expect, forbid}; the registry now also
      has `maps`. Re-judge it or re-stamp it." Cheap, mechanical, and it fires
      exactly once per primitive added -- which is the right cadence, because
      that is precisely when the answer can have changed.
      DO NOT let this become pressure to convert. A re-judged entry that is still
      NOT CONVERTIBLE just gets a new stamp; the budget stays 9. The check exists
      so the claim is re-made deliberately, not so the number falls.
      RELATED: subgoal E15 asks whether `requires` -- implemented on both engines
      and bound to no item -- belongs on Q6. Two of these nine entries are Q6
      `affect_*` slots whose reasons turn on what `cover` already constrains. If
      `requires` lands on Q6, both entries are due for re-judging by this rule.

- [x] E30. **Nothing compares OUR failing slots against GOLD's charged slots. Only totals.** DONE
      Filed 2026-08-31 out of Q28, which is the demonstration. Every rate in this
      project compares a cell's TOTAL against gold's total -- `scored_exactly`,
      the ledger, cross_path --gold -- so a cell that fails the WRONG SLOTS in
      the RIGHT QUANTITY reads as a match on every path that looks at it.
      THE CASE. Q6/p5, six runs, both sides. Gold's comment charges three slots:
          -1.25 First antecedent does not match antecedents listed in 4a
          -1.25 First consequence does not match 4c
          -1.25 Second consequence does not match 4a   [4c is meant]
      -- state_a1, state_c1, state_c2. WE fail state_a1, state_c2 and affect_c2.
      Same 3.75, same 6.25, two disagreements cancelling. It read as a 6-of-6
      olx success and a 5-of-6 python one, and on that reading the divergence
      DUPLICATE_EFFECT_TIE_BREAK was proposed for retirement -- wrongly, since
      gold's comment confirms its stated reason word for word.
      WHY cross_path --slots DOES NOT COVER IT: that compares the two SCORERS to
      each other. Both scorers agree with each other here and both differ from
      the grader in the same place, which is exactly the shape a scorer-to-scorer
      comparison cannot see. Nothing in the tree compares a slot set to gold's.
      WHAT EXISTS TO BUILD ON, and its limits:
        `criterion_rows(item, check)` already asks whether gold's comment charges
          one criterion, by splitting the check name into words and searching the
          comment for them. Crude by its own admission -- it prints the comment
          "so a mis-group is visible" -- but it is the right shape and it works
          well enough to group rows by hand today.
        `_DEDUCT_RE` parses the AMOUNTS. It requires `pts`/`points`/`:`/`;` after
          the number, so it misses comments written as `-1.25 <text>`: 3 of the
          183 rows with a comment, and Q6/p5 is one of them. Those rows are
          currently invisible to gold_rows_that_do_not_reconcile as well, which
          skips a row whose deductions it cannot read. Fix that first -- it is a
          regex, it is cheap, and it is a prerequisite for anything that reads
          gold's itemisation.
      THE HARD PART, stated so it is not discovered late: mapping a grader's prose
      to a SLOT KEY is not mechanical. "First consequence does not match 4c" is
      state_c1 only if you know this item's slot naming; the graders wrote for
      students, not for the sheet. So the check probably cannot be corpus-wide on
      day one. A defensible first version: only rows whose comment itemises
      deductions AND whose phrases map through a declared per-item table, with
      every unmapped row REPORTED as unmapped rather than silently passing --
      the opposite of today, where an unmappable row is simply not looked at.
      DO NOT let this become a re-scoring tool. It answers one question -- do we
      fail the slots gold charged -- and a cell that agrees on total while
      disagreeing per slot is a finding to read, not a number to adjust. Q6/p5's
      own two disagreements cannot be fixed independently: correcting state_c1
      alone moves the total off gold, which is why it wants a person.
      BUILT 2026-08-31. measured.gold_slot_disagreements, wired into the audit as
      SLOT SET DISAGREES WITH GOLD and into preflight at step 2b, beside the other
      gold work rather than after the model steps. Three tables registered in
      DECLARATION_TABLES: GOLD_SLOT_CHARGES (phrase -> slot set, per item),
      GOLD_SLOT_DISAGREEMENTS_KNOWN (budget 8, may only fall) and
      GOLD_SLOT_UNMAPPABLE (charges no slot set can account for, with reasons).
      THE PREREQUISITE IS DONE: _DEDUCT_RE now parses `-1.25 <text>` as well as
      `-1.25 pts`. Verified across all 183 commented rows -- 180 parse identically,
      the 3 newly-read rows all RECONCILE, and no row gained a deduction it did
      not name. Those three were invisible to gold_rows_that_do_not_reconcile too.
      A `deductions_named` accessor was added because the regex now returns pairs
      and its one caller would otherwise have become a TypeError.
      WHAT IT FOUND, and it is the reason the check was worth building: EIGHT of
      Q6's TWELVE mappable cells fail different slots from the ones gold charged,
      while the totals agree. Q6 records python 17/20 and olx 18/20, and most of that
      agreement is compensating error at the slot level. `affect_c2` and
      `state_a2` recur across the eight -- the `refers_to` channel again, seen
      from the GRADER's side for the first time rather than by comparing the two
      scorers to each other.
      THE AMOUNT CHECK EARNED ITS PLACE IMMEDIATELY. A phrase maps to a SET of
      slots and the charged amount validates the count, and that caught THREE
      wrong mappings in the first version of the table -- "missing both
      consequences" charged 2.5 where four slots would be 5, and two "second
      consequence" phrasings charged 2.5 where one slot would be 1.25. Without it
      the table would have been unfalsifiable prose that silently mis-attributed
      charges and blamed the scorer.
      TWO REGISTRY DEFECTS FELL OUT: check_every_declaration_table_has_a_verifier
      could not resolve a table in `measured` at all -- its module map knew only
      handouts, olx_prompts and enforcement -- so registering the new table was
      reported as "a table nobody has", indistinguishable from the failure that
      check exists to catch. And the new check was registered before it was
      invoked, which CHECK NEVER RUNS caught in the same pass. Both fixed.
      COVERAGE EXTENDED 2026-08-31 from one item to EIGHT -- Q1, Q2, Q3, Q4a, Q4b,
      Q4c, Q6 and 1c -- which is 73 of the 109 cells whose gold comment itemises
      its deductions, 66%. The check reports its own coverage rather than reading
      as thorough.
      THE EXTENSION CHANGED THE MECHANISM THREE TIMES, each because a table this
      size exposed something one item could not:
        A SEGMENT MATCHING SEVERAL PATTERNS IS AMBIGUOUS, not the first match.
          `next(...)` silently took one and dropped the rest, so Q3/p3 -- one
          -1 pt charge naming both `specific` and `measurable` -- mapped to
          `specific` alone AND PASSED THE AMOUNT CHECK, because one slot is one
          point on that item. Silently wrong is worse than unmapped.
        IT IMMEDIATELY FOUND AN OVERLAP IN THE Q6 TABLE. The narrow "did not state
          the second consequence being affected" also matched the two-slot
          "...and how it is being affected" form, and first-match ordering had
          been giving the right answer by luck. Fixed with a negative lookahead --
          and the ratchet then reported THREE of the eight known Q6 disagreements
          as stale, because they were artefacts of the mis-mapping rather than of
          the scorer. p9, p17 and p18 retired.
        THE SAME PHRASE CAN COVER DIFFERENT SCOPES, told apart by the AMOUNT. Q2's
          "your WGB should be the opposite of your UTB" is `wgb_inverts_utb` alone
          at 2 points and the whole item at 5. The table format gained an optional
          amount, and the phrase-only version had mapped the 5-point charge to a
          2-point slot -- caught by the amount check, earning its place twice.
        A CORRECTED CELL'S COMMENT MAY NOT DESCRIBE ITS SCORE. Q4a/p17's comment
          docks the keyword point and CORRECTED_GOLD takes it back, because the
          graders charged that point once in seven comparable cases. Reading the
          comment anyway reported a charge we correctly do not make. Now tested by
          arithmetic rather than another declaration: if max minus the named
          deductions does not equal the score in force, the itemisation is not
          describing that score and the cell is unread. Covers Q6/p4 too.
      WHAT THE COVERAGE FOUND: SIX more slot-level disagreements, on Q1, Q2, Q3
      (twice), Q4a and Q4b, plus two on Q4c -- and they have ONE shape. Gold
      charges a slot WE CREDIT, on every one. So the scorers are lenient relative
      to the grader at slot level even where the totals agree, on five items
      besides Q6. Thirteen cells are now declared, budget 13.
      COVERAGE, stated against the right denominator: TEN items, 78 of the 91
      COMPARABLE cells, 85%. It was first reported as "8 items, 66% of 109" and
      both halves of that were wrong -- the item count because three more items
      turned out to map cleanly, and the denominator because 18 of the 109 cells
      cannot be compared at all.
      EIGHTEEN CELLS ARE NOT COMPARABLE, and it is structural rather than a gap.
      A `derive_from_criteria` item's rubric carries the two or four checks the
      DEDUCTIONS are written against, while its olx sheet asks fourteen criteria
      the python derives them from. "Which slots we failed" and "which slots gold
      charged" are then not the same kind of thing. NR is what proved it: tabled
      on the reasonable-looking rule that naming another operant type charges
      `is_nr`, it reported gold charging `is_nr` against our failing
      `demonstrates_type` and `targets_goal_behavior` -- two naming schemes
      passing each other, dressed as a finding. The table was removed and
      _slots_are_not_comparable now refuses those eight items (DAY1, DAY2, NP,
      NR, PP, PR, WK1, WK2) structurally.
      THAT ALSO EXPLAINS WK1/WK2/DAY1/DAY2 PROPERLY. Their gold speaks about the
      operant TYPE -- "This is an example of NP" -- which is a derived conclusion,
      not a slot on the sheet. The first attempt at this note said they were
      "phrasings that name something other than a slot", which was the symptom;
      the cause is that the item derives its checks rather than carrying them.
      THIRTEEN COMPARABLE CELLS REMAIN UNTABLED, each for a stated reason and none
      of them "the vocabulary is awkward": 2b's "missing a sentence" (one of
      three, unsaid), D1/D2's "-1 point: Did not provide the entire definition"
      naming BOTH questions while charging one slot, Q5's "missing one reason" on
      two 2.5-point example slots, 1b's "missing two weeks of data" (which two).
      Every one charges fewer slots than it names, so a table could only guess --
      and guessing is what E30 exists to prevent. They want a per-cell reading,
      which is Q-subgoal work on the items, not table work.
      THE COMPLETE ACCOUNTING, 2026-08-31 -- every cell whose gold comment
      itemises its deductions, with nothing left unexplained:
          46  slots MATCH gold exactly
          15  exact slot disagreement          GOLD_SLOT_DISAGREEMENTS_KNOWN
           7  bounded disagreement             GOLD_SLOT_BOUNDS_KNOWN
          18  criteria-derived, not comparable E35
          23  ambiguous, no disagreement found
         109  total
      AMBIGUITY IS NOW BOUNDED, NOT SKIPPED, which is what closed the last real
      gap. GOLD_SLOT_UNMAPPABLE cells used to be dropped entirely -- and 6 of the
      24 dropped cells disagreed with us on the TOTAL, so the check was silent
      about the very cells most worth reading. Two statements survive ambiguity:
      if our failing set does not CONTAIN the definitely-charged slots we credit
      one gold charged, and if the SIZE differs the two disagree about how many
      slots failed. Neither needs to know WHICH.
      gold_charge_bounds derives the count from the AMOUNTS and the slot points,
      so it works on items with NO phrase table at all -- and a subset-sum over
      the slot values rather than a uniformity requirement, because Q1's 1-point
      charge can only be one of its three 1-point reason slots when utb_stated is
      2, and demanding uniform slot values threw that away.
      IT FOUND SEVEN CELLS THE EXACT COMPARISON COULD NOT SEE, and six run the
      same direction as everything else -- gold charges a slot, we charge none.
      FOUR OF THEM ARE 2a, uniform: gold docks one `how_*` slot and we dock
      nothing, 4.0 against 6.0. That is subgoal Q2's "2a over-credits hows_given"
      reached from the slot side, and the strongest confirmation of it available,
      because it says the over-credit is ONE UNCHARGED SLOT rather than something
      spread across the item.
      THE SEVENTH RUNS THE OTHER WAY AND IS THE ONLY ONE THAT DOES. Q5/p4: gold
      charges ONE example slot and we fail BOTH, 0.0 against 2.5. Every other
      disagreement in the accounting is us being lenient, which makes this the
      one piece of evidence that the leniency is not uniform -- read it before
      concluding the scorers are simply soft.
      AND THE FIRST STOPPING POINT WAS A GENERALISATION FROM THREE ITEMS. Asked
      why, the honest answer was that WK2, DAY2 and 2a had been surveyed and the
      other eight had not. Surveying them found 1a, 3 and NR looking mappable; two
      of the three were, one was the structural case above. Recorded because
      "the rest are probably like these" is exactly the reasoning that leaves
      coverage on the table.

- [x] E31. **RAW_GOLD_READERS is inert: nothing reads it, and it is registered as checked.** DONE
      Found 2026-08-31 by asking whether entries in it are checked in enforcement.
      They are not. It is registered in DECLARATION_TABLES against
      check_gold_accounting_is_uniform, and that function mentions the table only
      inside its own error MESSAGE: it walks a hard-coded list -- cross_path,
      measured, compare_runs -- and greps each for apply_corrected_gold,
      rebuild_gold_1c and scored_exactly.
      PROVED BEHAVIOURALLY, not by reading: emptying the table, and adding an
      entry naming a module that does not exist, both leave the verifier's output
      identical at 0 findings. The table is not consulted at all.
          enforcement.check_corrections_still_match_the_sheet
          measured.gold_rows_that_do_not_reconcile
          baseline_h1
      TWO CONSEQUENCES. A declared reader is never verified -- nothing checks that
      gold_rows_that_do_not_reconcile still reads RAW gold, or that its reason
      still holds; that declaration was RELIED ON on 2026-08-31 when the Q6/p4
      correction landed, and it happened to be true, confirmed by running the
      check rather than by anything enforcing it. And a NEW raw reader is
      invisible, because the loop is hard-coded rather than driven by the table.
      FIXED 2026-08-31, and it found a stale declaration in the first run.
      check_gold_accounting_is_uniform now has two halves. It VERIFIES each entry:
      a bare module must exist and must actually load gold, or the exemption
      protects nothing; a `module.function` entry must EXIST, must read gold
      directly, and must NOT call apply_corrected_gold -- because an exempt reader
      that has adopted the canonical accounting no longer needs excusing, and that
      is the staleness this table exists to be able to lose. And it DISCOVERS the
      consumers by scanning rather than listing.
      THE STALE ENTRY: the table named
      `enforcement.check_corrections_still_match_the_sheet`, which has never
      existed. The function is `check_corrected_gold_matches_the_sheet`. Its
      exemption is legitimate -- it does read gold raw -- but the NAME had been
      wrong for as long as nothing read the table, which is precisely the failure
      an inert declaration hides: an exemption naming nothing exempts nothing and
      reads as coverage. Corrected.
      THE HARD-CODED LIST MISSED FOUR MODULES. It walked cross_path, measured and
      compare_runs; scanning finds seven that load gold -- those three plus
      enforcement, handouts, baseline_h1 and gold itself. So a NEW module comparing
      gold raw was invisible to this check by construction.
      `gold.py` IS EXCLUDED STRUCTURALLY, not declared: it DEFINES load_h1/2/3, so
      requiring it to apply its own corrections would be circular. That is a fact
      about the module, not a judgement, so it does not belong in the table --
      detected by looking for `def load_h*` rather than by name.
      `baseline_h1` STAYS EXEMPT and is now verified: the file exists and does
      load gold, so the exemption protects something real. Its second claim --
      that it is "unreferenced by any script or module" -- is still untested here;
      that is a different check and worth one.
      VERIFIED BEHAVIOURALLY, per E32's method: emptying the table now produces 3
      findings and a bogus entry 1, against 0 for the table as declared. So it is
      READ, and its PROBE_IMPOSSIBLE entry was RETIRED rather than softened -- the
      probe reports 23 READ and 1 BY DESIGN, the remaining one being
      PER_ITEM_EXCLUDE under E33.

- [x] E32. **A registered verifier can enforce nothing about its table. Test it behaviourally.** DONE
      Generalised 2026-08-31 from E31. check_every_declaration_table_has_a_verifier
      confirms that a NAMED verifier exists and that the table exists. It cannot
      see whether the verifier actually reads the table, so a declaration can be
      registered, pass the registry check, and still be inert -- which is the
      "reads as coverage and enforces nothing" failure the registry was built to
      prevent, one level up. RAW_GOLD_READERS is the proven instance.
      GREPPING DOES NOT WORK, tried and rejected: matching the table's name in the
      verifier's source gives false NEGATIVES where the name appears only in an
      error string -- exactly how RAW_GOLD_READERS looked checked -- and false
      POSITIVES where the verifier legitimately delegates to another module that
      does read it. On this tree the grep flagged 5 of 22 tables and every one was
      a delegation: GOLD_CEILINGS and GOLD_DIVERGENCES through
      measured.declaration_conflicts, the two GOLD_SLOT_* tables through
      measured.gold_slot_disagreements, SLOT_STRUCTURE_FAMILIES likewise. The one
      table that IS inert was not among them.
      THE METHOD, which is the deliverable as much as the check: for each
      registered table, snapshot it, run its verifiers, then run them again with
      the table EMPTIED and again with a BOGUS entry added, restoring in between.
      If all three outputs are identical the verifier does not read it. That
      catches delegation correctly, because delegation still changes the output.
      THREE THINGS IT HAS TO HANDLE, or it will be abandoned as noisy:
        emptying a table can produce findings OF ITS OWN -- a budget constant that
          no longer matches, a ratchet that reads as "down to 0" -- so compare the
          output STRUCTURALLY against the unmodified run rather than by count;
        a bogus entry must be shaped like a real key, which differs per table
          (tuples for cell tables, strings for module tables), so the generator
          needs a per-table example or it will crash rather than report;
        some verifiers are expensive, and running each three times over 22 tables
          is not something to put in the default audit run. This belongs beside
          the self-test, on demand, not in the pre-commit path.
      CLOSED 2026-08-31 with ITS REMAINDER NAMED, not silently. The probe answers
      the question this subgoal asked -- does each REGISTERED verifier read its
      table -- and reports 25 of 25 READ. Two neighbouring gaps are E36's, and
      they are written down because closing without naming them is how a
      "0 of 25 enforce nothing" line becomes false later:
        the UNREGISTERED-table scan covers two modules of four, so a declaration
          in handouts.py or olx_prompts.py is still never asked for;
        an EMPTY table is skipped by the probe -- `if not val: continue` -- so
          registering olx_prompts' empty OMIT_CREDIT and OMIT_DEDUCTION will give
          this probe a CANNOT PROBE row again, and that row is in THIS subgoal's
          territory even though E36 creates it.
      IT IS NOT A REFACTOR. The output is a list of registered declarations that
      enforce nothing, and every one of those is a claim the project believes is
      checked. That is the same class as a SKIPped self-test case, and the same
      class as the plain-path branch that quietly stopped testing anything.
      BUILT 2026-08-31: enforcement.probe_declaration_tables, run as
      `python3 enforcement.py --probe-declarations`, deliberately off the default
      path and exiting 1 when a table is inert. Result over the 22 registered
      tables: 15 READ, 0 INERT, 5 INCONCLUSIVE, 2 unprobeable because empty.
      THE PROBE WAS WRONG THREE TIMES BEFORE IT WAS RIGHT, and that is the finding
      worth keeping. It reported, in order, "16 of 22 enforce nothing", then 1,
      then 0 -- a confident number at every stage of brokenness:
        (1) run as a script this module is `__main__`, and
            importlib.import_module("enforcement") builds a SECOND module object
            with its own copy of every table. The probe mutated the copy while the
            verifiers read __main__'s, so all twelve enforcement.* tables read
            INERT. Caught only because PROSE_ONLY_SLOTS was among them and its
            budget check had fired at me hours earlier, so the claim was known
            false: emptying it takes its verifier from 0 findings to 18.
        (2) SILENCE IS NOT INERTNESS. A verifier that reports nothing on the real
            table also reports nothing when it is emptied, and a bogus key naming
            nothing real is correctly ignored. Three empty outputs prove the table
            is currently clean, nothing more. That reading had condemned
            GOLD_DIVERGENCES and PER_ITEM_EXCLUDE, both of which are read.
        (3) SOME VERIFIERS TAKE ARGUMENTS. check_countable_families_converted
            takes `items`; calling it bare raised TypeError identically in every
            state, so COUNTABLE_EXEMPT read as INERT when the probe had simply
            never run its verifier. A raising verifier is indistinguishable from
            an unread table unless the two are recorded separately, which they now
            are -- __UNCALLABLE__ reports CANNOT PROBE, a gap in the probe rather
            than evidence about the table.
      THE METHOD IS NECESSARY AND NOT SUFFICIENT. RAW_GOLD_READERS -- the one
      table PROVEN inert, in E31 -- comes back INCONCLUSIVE here, because its
      verifier is silent on the real table. The proof there came from READING the
      function: it walks a hard-coded module list and names the table only inside
      an error string. So the behavioural probe cannot confirm E31, and a table
      whose verifier says nothing needs a reading, not a probe.
      THE PER-TABLE WORK IS DONE, and every table is now accounted for:
          22 READ      0 INERT      0 INCONCLUSIVE      2 BY DESIGN
      over 24 registered tables -- the probe's own two included, since
      PROBE_PROVOCATIONS and PROBE_IMPOSSIBLE are declarations too and it is the
      only thing that can verify them. That made the probe RE-ENTRANT: probing
      them runs the probe, which probes them again, and unguarded it ran until it
      was killed. The inner call now returns a marker derived from the two tables,
      which still differs between the emptied and restored states, so both stay
      tested.
      A nonsense KEY was never enough -- a verifier that objects only to a
      WELL-FORMED but WRONG entry ignores garbage and looks inert. So each table
      declares a PROVOCATION in PROBE_PROVOCATIONS: an entry its verifier must
      object to. That also makes an EMPTY table probeable, which emptying never
      could, and it closed both CANNOT PROBE rows.
      TWO PROVOCATIONS TOOK THREE ATTEMPTS, and the failures are informative:
        SCORING_DIVERGENCES' verifier parses a claim of the form "sum to N ...
          max of M" out of `what` + `why` and recomputes it, so an entry
          asserting no arithmetic gives it nothing to contradict. Then the claim
          was aimed at 1b, and `_maxes` returns None for a SHEET_ONLY item with no
          LLMAction grader, so the entry was skipped -- unexaminable rather than
          false. Retargeted at Q6 it fires.
      TWO TABLES CANNOT BE PROBED, declared in PROBE_IMPOSSIBLE, and both reasons
      are findings rather than excuses:
        RAW_GOLD_READERS -- its verifier never reads it, so NO entry can make it
          speak. That is E31, and it means the behavioural method is necessary and
          not sufficient: this table's inertness was provable only by READING the
          function. Fixing E31 would also make it probeable.
        PER_ITEM_EXCLUDE -- its staleness verifier reads the LEDGER's recorded
          `excluded_cells`, not the table as it stands. AN EXCLUSION ADDED AFTER
          THE LAST SWEEP IS THEREFORE UNWATCHED UNTIL THE NEXT ONE. That is a gap
          in the CHECK, not in the probe, and it is the more serious of the two:
          the whole point of that verifier is to stop an exclusion outliving its
          justification, and it cannot see one that has not been swept since being
          added. Worth its own subgoal.
      SO THE PROBE'S REAL OUTPUT IS NOT THE COUNT. It found no inert table that
      reading had not already found, and it found two structural facts about the
      checks -- one verifier that cannot be provoked at all, and one that watches
      a snapshot rather than the declaration.

- [x] E33. **An exclusion added after the last sweep is unwatched until the next one.** DONE
      Found 2026-08-31 by E32's probe, as the reason PER_ITEM_EXCLUDE could not be
      provoked. The staleness verifier -- the exclusions loop in
      measured.declaration_conflicts -- reads the LEDGER's recorded
      `excluded_cells`, which is a snapshot taken when the item was last recorded.
      It does not read handouts.PER_ITEM_EXCLUDE. So an exclusion added today is
      invisible to it until that item is swept and re-recorded.
      WHY THAT MATTERS MORE THAN IT SOUNDS. The whole purpose of that check is to
      stop an exclusion outliving its justification, and QUALITY_CONTROL.md is
      emphatic about the failure mode: "an exclusion on a cell the scorer gets
      WRONG must be removed... it is the one that will never remove itself,
      because the cell it hides is the cell that would otherwise ask for work."
      The window where a new exclusion is unwatched is exactly the window in which
      it is most likely to be wrong -- freshly added, on a cell someone has just
      decided not to look at, with no measurement yet taken against it.
      IT IS NOT A HYPOTHETICAL WINDOW. Nothing forces a sweep after adding an
      exclusion, and this project has gone weeks between sweeps of an item. An
      exclusion added mid-session and then reasoned about all day would be
      unwatched for that whole day, and the audit would report nothing.
      THE FIX, and it is not just "read the table instead": the check needs BOTH.
      The ledger snapshot is what says whether the cell scores right in every run
      -- that evidence only exists in an artifact -- and the table is what says
      the cell is currently excluded. Today it takes the intersection implicitly
      by reading only the snapshot, which silently drops any exclusion the
      snapshot predates. Read the table for WHICH cells are excluded, and the
      artifact for HOW they scored, and report a cell that is excluded now and
      scored right in the last recorded runs, whenever those runs happened.
      A CELL EXCLUDED SINCE THE LAST SWEEP has no evidence either way and must be
      reported as UNMEASURED-SINCE-EXCLUDED rather than passed: "no evidence" is
      the state this whole subgoal is about, and it {{corpus:Q4b/p13:modify:42:58:sha=ed0e48693398}} the current
      check cannot distinguish from "no problem".
      CHECK THE MIRROR CASE TOO: an exclusion REMOVED since the last sweep leaves
      the snapshot claiming a cell is excluded when the table no longer says so.
      That direction inflates nothing and costs nothing, but it means the two
      sources disagree, and a check reading only one of them cannot say which.
      FIXED 2026-08-31. The loop reads BOTH: the table for which cells are
      excluded now, the artifact for how they scored. Four states, and the
      distinctions are the work -- a check that collapsed them would either miss
      the gap or nag forever:
        in both        -- evidence exists; unchanged behaviour, report a cell that
                          scores right in every run.
        excluded now, absent from the snapshot, gold HAS a score -- no evidence
                          either way. Reported: the exclusion was added since that
                          sweep, or the scorer produced nothing for the cell.
        excluded now, absent, gold has NO score, kind `unscoreable` -- the
                          declaration and the evidence AGREE, because that kind
                          asserts gold's row is unreachable. Silent. 1c's
                          p4/p19/p20 are this: rebuild_gold_1c removes their gold
                          rows. Reporting them would nag forever about cells
                          nothing can settle, which trains the reader to skip the
                          check.
        excluded now, absent, gold has NO score, ANY OTHER kind -- inconsistent:
                          the exclusion claims something measurement could refute
                          and there is nothing to refute it with. Reported.
        in the snapshot, no longer excluded -- the two sources disagree. Reported.
      THAT DISTINCTION WAS FOUND BY READING, not designed. The first version
      reported all three 1c cells as "unmeasured", which looked like the gap being
      caught and was actually the check nagging about a permanent state. The cause
      is that `exc` is only filled when gold has a score for the cell, so a cell
      whose gold row the 1c rebuild removes can never appear in the snapshot.
      VERIFIED BY INJECTION in all three reporting states -- an exclusion added
      since the sweep, a refutable kind with no gold row, and an exclusion dropped
      since the sweep -- and silent on the clean tree.
      AND IT CLOSED THE LAST PROBE GAP. PER_ITEM_EXCLUDE was E32's remaining BY
      DESIGN row, unprobeable precisely because its verifier read the snapshot
      rather than the table. It is now READ, its PROBE_IMPOSSIBLE entry retired,
      and that table is empty: all 24 registered declaration tables are proven to
      be read, with none inert, inconclusive or exempt.

- [x] E34. **Gold charges a CATEGORY; our sheet charges members. No mechanism expresses that.** REFUTED
      Filed 2026-08-31 from E30's slot-level accounting, which is the first thing
      able to see it: the totals alone showed six unrelated over-credits.
      THE PATTERN, one charge condemning every member of a group:
          1a/p1   "did not discuss data for each week"          -8  all 4 weeks
          Q4a/p14 "Examples are not antecedents"                -4  both antecedents
          Q4b/p4  "your behaviors cannot be the same as your
                   antecedents"                                 -3  both behaviors
          Q4c/p9  "consequences are a direct result of engaging
                   in your UTB"                                 -4  both consequences
          Q6/p8   "did not say how EACH antecedent is changed"  -2.5 both change_*
                  "did not state EACH consequence ... and how"  -5  all four c-slots
          Q2/p7   "your WGB should be the opposite of your UTB" -5  inversion + 3 reasons
      In every one the grader made ONE judgement about the KIND of thing offered
      and charged the whole group. Our sheet asks each box independently and
      credits the ones that individually pass -- so we fail the second box and
      credit the first, five items over, and the arithmetic difference is the
      credited member.
      IT IS ONE MISSING MECHANISM, not six misses. There is no way on the sheet to
      say "if the KIND is wrong, no member counts". Q4b is the exception that
      proves it: `maps` turns its referent test into arithmetic across both
      behavior slots, which is exactly this shape -- and Q4b/p4 is still here,
      because `maps` fires on the referent and not on the "same as your
      antecedents" judgement gold used.
      THE CANDIDATE IS `forbid` OR A NEW GROUP-LEVEL PRIMITIVE, and the honest
      first step is neither: it is to check whether the graders APPLY the category
      charge consistently. If a category judgement is charged wholesale on some
      cells and per-box on others, a mechanism that always charges wholesale would
      fix six cells and break the rest. Count both shapes across the corpus before
      designing anything -- the phrase tables in measured.GOLD_SLOT_CHARGES make
      that countable now, which it was not before.
      DO NOT reach for prose. memory/structural-before-wording.md applies, and so
      does the Q6 record: nine measured wordings on `refers_to` and no movement.
      REFUTED 2026-08-31 BY ITS OWN FIRST STEP, which is the reason that step was
      written down before any design. The count it demanded says the mechanism is
      not missing:
        22 cells carry a GROUP charge -- one segment covering several slots -- and
          WE AGREE WITH GOLD ON SIXTEEN OF THEM. A missing mechanism would fail
          all 22.
        25 group charges against 76 single-slot charges corpus-wide, so the
          graders use both shapes about 1 in 4. A mechanism that always charged
          wholesale would have been wrong 76 times.
      THE MATCHED PAIRS SETTLE IT. Same item, same gold charge, opposite outcome:
          1a/p15  we fail all four week slots      1a/p1   we fail one
          Q4a/p20 we fail both antecedents         Q4a/p14 we fail one
          Q4b/p8  we fail both behaviors           Q4b/p4  we fail one
      The sheet can already fail every member of a group -- it does exactly that
      on p15, p20 and p8. On p1, p14 and p4 we judged the FIRST box acceptable
      where the grader did not. That is a per-response judgement, not a structural
      gap, and no primitive would change it.
      SO THE SIX CELLS BELONG TO Q19, the later-box gradient, which measured the
      same thing from the other side: "we refuse the later box roughly twice as
      often as the first". Crediting the FIRST box where gold charges both IS that
      gradient. Q19 also says "read this before any numbered slot", which is the
      guidance this subgoal skipped by reaching for a mechanism first.
      WHAT THE EXERCISE WAS WORTH ANYWAY: the six cells now have gold-side
      confirmation that Q19 did not have. Q19 measured our refusal RATE by box
      index; these cells show the grader charging both boxes on the same response
      where we charge one, which is the same claim with the grader's own
      itemisation behind it. Moved there rather than lost.

- [x] E35. **The eight criteria-derived items are outside the slot-level accounting entirely.** DONE
      Filed 2026-08-31, the one group E30's accounting cannot reach. DAY1, DAY2,
      NP, NR, PP, PR, WK1 and WK2 are `derive_from_criteria`: their rubric carries
      the two-to-four checks the DEDUCTIONS are written against, while their sheet
      asks fourteen criteria the python derives those from. So "which slots we
      failed" is a sheet fact and "which slots gold charged" is a rubric fact, and
      comparing them produced nonsense that looked like a finding -- NR reported
      gold charging `is_nr` against our failing `demonstrates_type`.
      EIGHTEEN CELLS, and FIVE of them disagree with us on the TOTAL, so they are
      not a quiet corner:
          WK2/p3   gold 2.0  ours 4.0   "-2 pts: This is NP."
          WK2/p15  gold 2.0  ours 4.0   "-2 pts: This is an example of NP."
          NR/p15   gold 2.0  ours 4.0   "-2 pts: This is an example of PR."
          NR/p11   gold 2.0  ours 0.0   "-2 pts: This is an example of NP."
          DAY2/p7  gold 3.0  ours 4.0   "-1 pt: make sure the behavior you are
                                          targeting is spending less time..."
      THE TYPE CHARGE IS WORTH 2 AND WE GET IT WRONG IN BOTH DIRECTIONS. Three
      cells credit it where gold charges (4.0 against 2.0) and one zeroes the item
      where gold charges 2 (0.0 against 2.0). Same judgement, opposite errors,
      which is the signature of an unstable derived check rather than a threshold
      set wrong -- and it is subgoal Q23's `matches_chosen_type` family seen from
      the grader's side.
      WHAT IT NEEDS IS A DIFFERENT COMPARISON, not a phrase table. Our failing
      RUBRIC checks have to be recomputed from the criteria the artifact records,
      the way agreement.py derives them at scoring time, and compared against
      gold's charge. The artifact holds the fourteen criteria, so this costs no
      API calls -- it is a second reader beside _our_failing_slots, and
      _slots_are_not_comparable is the hook it should replace.
      DO NOT table these items until that exists. NR was tabled on a
      reasonable-looking rule and had to be removed; the table is not the missing
      piece.
      DONE 2026-08-31, and the comparison turned out to be simpler than the plan.
      It is not slots at all: agreement.score_oc is a CASCADE that returns at its
      first failure and charges exactly ONE deduction code, and gold's comments on
      these items name the same judgements. So the comparison is CODE against
      CODE, and our code is recoverable from the score because every one of the
      eight has max 4 and charges once. No re-derivation of fourteen criteria was
      needed.
      GOLD_CODE_CHARGES is one table for all eight -- they share a vocabulary,
      being the same question asked about four operant types and two cadences --
      and the AMOUNT validates the phrase as everywhere else: WRONG_TYPE is 2 and
      NOT_OC is 4, so a phrase and an amount that disagree mean the table is
      wrong. `TYPE_MISMATCH` is resolved from the rubric, being the cadence items'
      name for the same judgement.
      ALL FIVE DISAGREEMENTS NOW HAVE A CODE:
          NR/p15   gold WRONG_TYPE (2)      we charge nothing
          WK2/p3   gold TYPE_MISMATCH (2)   we charge nothing
          WK2/p15  gold TYPE_MISMATCH (2)   we charge nothing
          DAY2/p7  gold WRONG_BEHAVIOR (1)  we charge nothing
          NR/p11   gold WRONG_TYPE (2)      we charge 4
      FOUR LENIENT AND ONE HARSH, on the same judgement, which is the signature of
      an unstable derived check rather than a threshold set wrong -- and it is
      subgoal Q23's `matches_chosen_type` family seen from the grader's side.
      NR/p11 IS THE ONE TO READ FIRST. Gold says the example IS operant
      conditioning but of the wrong type, worth 2; we charge 4, which is NOT_OC,
      NOT_EXTERNAL_STIMULUS or BLANK -- the score alone cannot separate them. The
      cascade returns at its FIRST failure, so a definitional criterion reading
      unmet hides the type question entirely. Read which of the four criteria
      failed before touching any type rule.
      AND IT EXPOSED A REGISTRY BLIND SPOT. check_every_declaration_table_has_a
      _verifier scanned only enforcement.py for UNREGISTERED tables, so the four
      tables added to measured.py that day were never asked for -- three were
      registered by hand and the fourth was forgotten with nothing complaining.
      The scan now covers measured as well. handouts and olx_prompts are left for
      E36, because they hold ten containers that are prompt data rather than
      declarations and each needs a reason before the scan can include it.

- [x] E36. **The unregistered-table scan covers two modules of four.** DONE
      Filed 2026-08-31 from E35. check_every_declaration_table_has_a_verifier has
      two halves: it checks that every REGISTERED table exists and names a real
      verifier, and it scans for tables nobody registered. The second half scanned
      only enforcement.py until measured was added, so a declaration table in
      handouts.py or olx_prompts.py is still invisible to it.
      NOT A THEORETICAL GAP: four tables were added to measured.py on 2026-08-31
      and the audit asked for none of them. Three were registered by hand and the
      fourth was forgotten; nothing said so until the omission was noticed by
      reading. handouts and olx_prompts hold declarations too -- CORRECTED_GOLD,
      GOLD_DIVERGENCES, PER_ITEM_EXCLUDE and SCORING_DIVERGENCES are all
      registered from those modules already -- so the blind spot is real for
      exactly the files most likely to gain one.
      WHAT IT COSTS: ten containers would be flagged that are NOT declarations --
      handouts' H1/H2/H3_MARKERS, and olx_prompts' CONTEXT, EVIDENCE, ITEM_NOTES,
      MATCH_DEF, OMIT_GUIDANCE, REF_IDS and SLOT_NOTES. Each needs a
      _NOT_DECLARATIONS entry saying why it is prompt-construction data rather
      than a claim that can go stale. That is ten short reasons, and writing them
      is the work; widening the scan without them adds ten standing false findings
      and the check gets ignored.
      SLOT_NOTES IS THE ONE TO THINK ABOUT rather than wave through. It is
      olx-only prose that reaches a prompt, and SLOT_RULE_BACKLOG exists precisely
      to declare its entries -- so the honest reason is that the BACKLOG is the
      declaration and SLOT_NOTES is the data it declares, not that SLOT_NOTES is
      uninteresting.
      DONE 2026-08-31, and it was bigger than "ten containers need reasons".
      THREE STRUCTURAL FAULTS, not one:
        the scan covered enforcement and measured, so handouts and olx_prompts --
          the files that already hold four registered declarations -- were never
          asked. Now all four.
        it SKIPPED EMPTY CONTAINERS (`if not val: continue`), so a table could be
          emptied AND unregistered with nothing noticing. That was not
          hypothetical: FOUR tables in enforcement.py itself were invisible for
          exactly that reason -- CITATION_NECESSITY, FIXTURE_GAP_BACKLOG,
          FIXTURE_GOLD_OVERRIDES and FIXTURE_STRUCTURE_OVERRIDES, each with a
          real check already reading it, so they were unregistered rather than
          unverified and the registry could not say so.
        _NOT_DECLARATIONS exempted by BARE NAME with one blanket comment. Keyed by
          `module.ATTR` now, with a reason each, because a name exempted for one
          module was exempted for all of them.
      THE CONFLICT IS RESOLVED IN THE DOCSTRING'S FAVOUR. olx_prompts says
      "everything the olx sends that the python does not is a DEVIATION. Each is
      declared here -- in WEB_SYSTEM's rule table, RESPONSE / CONTEXT,
      OMIT_CREDIT / OMIT_DEDUCTION / OMIT_GUIDANCE, or ITEM_NOTES", while
      _NOT_DECLARATIONS exempted RESPONSE and WEB_SYSTEM as data. Two statements
      in the tree, disagreeing, with no reason recorded for either. The docstring
      wins: those tables ARE the contract, and six of them are registered now.
      WEB_SYSTEM stays exempt for a different reason -- it is a str, which the
      scan cannot see and a table-shaped check cannot re-test.
      A REAL VERIFIER, not a name to satisfy the registry:
      check_prompt_deviation_tables_are_current asks three things no prose
      judgement is needed for -- every key names a live item, every omitted
      credit or deduction still exists in the rubric, and every OMIT_GUIDANCE
      phrase still matches a guidance line. An omission that outlives the line it
      omits reads as a standing reason for a difference that has gone.
      IT WAS WRONG ONCE AND THE TABLE WAS RIGHT: it reported CONTEXT's `_utb` and
      `_wgb` as stale, and those are shared FRAGMENTS several items pull in, read
      by pseudo-key. A leading underscore is now skipped.
      COST: the probe went from 25 tables to 35, four of them fixture checks that
      read every submission, and stopped finishing inside ten minutes. The
      baseline run is cached per verifier set -- it is the unmutated output, so it
      is identical for every table sharing those verifiers -- which removes a
      third of the work. It remains an on-demand check, deliberately.

- [x] E39. **Nothing compares the two engines' verdicts by FREQUENCY. Eight cells hide there.**
      Found 2026-09-01 by asking why the audit did not notice that Q1/p17 scores
      3.0 on python in 5 of 6 runs and 5.0 on olx in 6 of 6, on the same prompt
      and the same model. Three things could have caught it and each missed for
      its own reason:
        * `cross_path.py` is the cell-by-cell comparator AND THE AUDIT NEVER RUNS
          IT. Nothing in equivalence.py or enforcement.py invokes it; every
          mention is in a comment. It is a tool someone remembers to use.
        * even when run it would not report this cell. Its rule is that the two
          sides' score SETS must be DISJOINT, and that is deliberate -- it
          "excludes cells where the paths overlap and merely differ in how
          often". p17 differs in exactly that way.
        * `equivalence.py --enforcement` compares DECLARATIONS, which its own
          docstring says leaves an undeclared behavioural difference invisible.
          The ownership check saw the cell was wrong on python, but it only asks
          whether a subgoal names it, and Q16 does.
      EIGHT CELLS DIFFER BY THREE OR MORE RUNS IN SIX, and every one has
      OVERLAPPING score sets, so the disjoint rule misses all eight:
          cell      gold   olx right   python right
          Q1/p17      5      6/6          1/6
          3/p15       0      6/6          2/6
          NP/p12      4      6/6          3/6
          WK2/p11     2      6/6          3/6
          WK2/p15     2      4/6          1/6
          Q1/p11      5      3/6          6/6
          Q4a/p9      3      3/6          6/6
          Q4c/p12     5      3/6          6/6
      IT RUNS BOTH WAYS, which is why this is not a "python is worse" finding:
      five favour olx and three favour python.
      THE FIX IS A CHECK, NOT A TOOL. A rate comparison over the recorded
      artifacts costs nothing -- `_cell_scores` already has both sides -- and
      belongs beside check_every_wrong_cell_has_an_owner, which walks the same
      cells. What it must NOT do is report every cell whose medians differ:
      QUALITY_CONTROL.md 2e records that three of Q32's five "divergences" were
      one observation apart, and a check with that threshold would be noise. Three
      of six is the threshold used above and it should be justified or replaced
      before the check lands.
      READ Q16 AND Q32 FIRST. Q16 has p17 diagnosed -- the rule's "what they want
      instead" branch is not being applied on the python side -- and Q32 records
      the axis as noise plus a provider difference, which this shows is
      incomplete.
      A MORE DIRECT CHECK WAS BUILT FIRST, 2026-09-01, on the observation that
      comparing SCORES is three inferential steps from the thing that might
      differ. `check_app_and_harness_send_the_same_prompt` compares the prompt
      body the app SERVES against the body agreement.py SENDS, per item, from an
      idmap dump. With a current dump it reports ZERO differences across all 23
      items -- so the two engines grade identical text, and Q1/p17 is not a
      prompt difference. That leaves substitution or sampling, and narrows this
      subgoal accordingly.
      IT FOUND A DEFECT IN THE GUARD IT SITS BESIDE. The app serves the body as a
      `kids` array SPLIT AROUND EACH `<Ref>` -- 3 segments on Q1, 9 on Q4b, 16 on
      Q6 -- and agreement_app's own freshness guard read `kids[0]` only. It was
      therefore inspecting a fraction of the prompt and ignoring the rest,
      including the box wrapper and the closing instructions that sit nearest the
      student's answer. Both now join every string kid. My own first hand
      comparison used the same shortcut and reported four lines missing from the
      app that were in the OLX all along, which is how it surfaced.
      THE DUMP'S AGE IS REPORTED SEPARATELY from a divergence, because prompts
      are regenerated far more often than dumps are taken and a check that is red
      every ordinary day is a check nobody reads. Older than the .olx and it says
      so, once, with the curl line to fix it.
      NEXT: decide the threshold, add the rate check, and re-read Q32's five cells
      against it. The prompt half is done.
      CLOSED 2026-09-01 BY THE POOLING DECISION, not by a fix. This subgoal
      existed to compare the two engines' agreement RATES, and the corpus now
      treats those engines as one process sampled twice, so the comparison it
      asked for is no longer a question anyone wants answered. Every one of the
      eight cells it named is right at the pooled median.
      WHAT IT BUILT SURVIVES, and is the reason closing it costs nothing:
        * check_app_and_harness_send_the_same_prompt -- template AND assembled
          text, per item, from an idmap dump.
        * check_app_and_harness_send_the_same_request -- provider-visible
          request fields, plus the two assertions that keep the message array
          and the shared fixture from drifting.
        * check_engine_rate_divergence and its power line, which report an
          exact-test comparison and say plainly that six runs a side cannot
          support a divergence claim.
      Those are what make the pooling presumption checkable rather than a hope:
      if the engines ever do diverge, the scoring-logic check fires without
      needing statistical power, and the prompt and request checks fire on the
      cause rather than the symptom.
      IT ALSO FIXED A GUARD ON THE WAY: agreement_app's idmap freshness check
      read `kids[0]` and so inspected one text segment of up to sixteen,
      ignoring the box wrapper and the closing instructions nearest the
      student's answer.


- [x] E38. **The python side's staleness fingerprint ignores five attributes it reads.**
      Found 2026-09-01 while answering "why is the python side served less of the
      screen than the olx side?" -- it is NOT (both backends get the identical prompt from
      `agreement.build_prompt` and the identical schema; only `backend.complete`
      differs). But the question exposed something else.
      `measured._python_read_attrs` derives that fingerprint's keep-list by
      regexing `_attr(open_tag, "X")` out of agreement.py, and its docstring
      promises this "cannot go stale: the day that side starts reading a new
      attribute, that attribute starts counting automatically". That holds ONLY
      for attributes read through `_attr`. These are read off the same open tag by
      BESPOKE parsers and are invisible to it:
          agreement.py:257  slots=      agreement.py:369  cover=
          agreement.py:260  verdicts=   agreement.py:392  derived=
          agreement.py:338  equals=
      FIVE, not the four an earlier draft of this title said: `slots`,
      `verdicts`, `equals`, `cover` and `derived`.
      The kept set is {choices, counts, expect, forbid, maps, onlyif, requires}.
      DEMONSTRATED, not argued: `_olx_only_visible` returns a byte-identical string
      when `derived="...antecedent"` becomes `derived="...trigger"`, and when
      `slots=` gains a slot. Both change what that side sends, so its measurement
      would therefore report CURRENT while being stale.
      THE ROOT OF IT IS A NAME COLLISION. `_olx_only_visible`'s docstring says these
      attributes "reach the CLI from the RUBRIC, not the OLX" -- written before the
      side rename, and true of
      score.py -- the rubric-driven paper scorer -- and false of agreement.py,
      which is what side `python` actually is. The rationale was written about a
      different program than the one it guards.
      E25 SLIPPED THROUGH IT. That goal changed `slots=` AND `derived=` on Q4a and
      Q4c, and that side WAS flagged stale -- but only because the prompt body
      changed in the same edit. An attribute-only change would have been silent,
      and this is the exact pattern of a `derived` conversion.
      THE FIX IS SMALL AND ITS CONSEQUENCE IS NOT. Widening the derivation (union
      the `_attr` reads with the bespoke `re.search(r'X="')` reads and the
      excludesKeys primitives that `excluded_keys` reads dynamically) re-hashes
      every python-side record, so all 26 items report STALE PROMPT at once and the audit
      demands a full re-sweep of that side. The numbers themselves are not wrong -- they
      were taken under those attributes; only the hash never covered them -- so
      the honest options are:
        (a) widen the derivation and re-stamp each python record's prompt_sha
            WITHOUT re-sweeping, which is correct only where the OLX text has not
            moved since that item was measured, and needs checking per item
            against git rather than assumed;
        (b) widen it and re-sweep the python side, ~26 items x 6 runs;
        (c) widen it and declare the re-stamp, item by item, as each is next swept.
      ASK BEFORE PICKING. (a) is cheapest and is a claim about history; (b) is
      expensive and assumption-free.
      NEXT: decide between (a), (b) and (c); then fix `_python_read_attrs`, correct
      the `_olx_only_visible` docstring's score.py/agreement.py confusion, and add a
      check that every open-tag read in agreement.py is covered by the derivation.

      CLOSED 2026-09-01 BY ROUTE (a), re-stamping against git history rather than
      re-sweeping. The derivation now counts every way that side reads an
      attribute: the `_attr` helper, the five bespoke `re.search` parsers
      (`slots`, `verdicts`, `equals`, `cover`, `derived`) and the schema-excluding
      primitives `excluded_keys` reads dynamically off the registry. `target` is
      excluded -- it locates the feedback element and is not sent to the model.
      Twelve attributes now count where seven did.
      VERIFIED BY THE CASE THE OLD HASH COULD NOT SEE: an attribute-only edit to
      Q4a's `derived=`, touching no prompt-body text, moves the python-side sha
      from 3c2b1ef648a1 to f1b06e4445d9. Under the old derivation it moved
      nothing, which is how E25 nearly slipped through.
      THE RE-STAMP, and its evidence recorded PER ITEM in a `prompt_sha_basis`
      field rather than asserted wholesale:
          git-clean            14 items. The .olx section is identical at the
                               commit the artifact recorded and now, and the tree
                               was CLEAN, so the commit is provably what ran.
          git-dirty-unchanged  10 items. Section identical at that commit and now,
                               but the tree was dirty, so the sweep could in
                               principle have run on a transient section. The
                               window is narrow and the text is stable either
                               side of it; this is the weaker half of the claim.
          dirty-moved           2 items, Q5 and Q6. Here git ACTIVELY MISLEADS: the
                               section differs, and the reason is that both were
                               swept with uncommitted work live -- Q6's `requires`
                               rule was in the tree and not in the commit -- so
                               `era.git` names the state BEFORE what ran. The
                               current text is what those numbers were measured
                               against, which subgoals E11 and E15 record
                               independently. Stamped on that, not on git.
      SO THE ROUTE'S LIMIT IS WORTH RECORDING: re-stamping against git history is
      sound only for artifacts written from a clean tree, and 12 of 26 were not.
      For two of those git returns the WRONG answer rather than no answer, which
      is the failure mode to watch -- a dirty sweep's commit is a record of what
      was NOT running. If this is ever done again, prefer artifacts whose era
      says dirty=False, and fall back to the subgoal that commissioned the sweep.
      THE AUDIT IS CLEAN AFTER IT: no item reports STALE PROMPT, and the two
      genuinely uncertain ones are labelled rather than hidden.


- [x] E37. **Every wrong cell must have a live owner, and the audit must say so every run.**
      Filed 2026-08-31. The accounting built across E30/E33/E35 was done BY HAND:
      34 wrong cells found, mapped to subgoals, 16 orphans chased down to 0. None
      of that is enforced, so it is true today and unverifiable tomorrow -- and it
      is exactly the state a cell moves out of silently when a rule is edited.
      WHAT GOES STALE, in both directions, and neither is visible today:
        a cell that STARTS being wrong after an edit has no owner and nothing
          says so. It shows up as one more number in a median.
        a cell that STOPS being wrong leaves a subgoal citing evidence that has
          gone -- the same failure the GOLD_SLOT ratchets already catch for the
          declaration tables, and the same one that retired three Q6 entries the
          day the pattern overlap was fixed.
        a subgoal that CLOSES orphans every cell it named. That is not
          hypothetical: closing E35 orphaned five cells, and it was noticed by
          hand rather than reported.
      THE CHECK: for every cell wrong at the recorded median, on either side,
      require a LIVE subgoal naming it as `item/pN` -- or a standing declaration
      that says we miss it on purpose. Report orphans, and report the reverse: a
      live subgoal naming a cell that is no longer wrong.
      A DECLARED MISS IS NOT AN ORPHAN. GOLD_DIVERGENCES cells are knowingly
      missed and already carry their reason; demanding a QC subgoal as well would
      be two names for one claim, which is the mistake SLOT_NOTES/SLOT_RULE_BACKLOG
      records.
      IT MUST BE CHEAP, or it will be moved out of the default run and stop being
      a regular procedure. That is affordable now: the audit went from 80.7s to
      7.7s on 2026-08-31, and the gold and artifact loads this check needs are the
      memoised ones.
      DO NOT MAKE IT A BUDGET. The count of wrong cells is a measurement and will
      move with every sweep; what must not move is that each has somewhere to
      live. A ratchet on the NUMBER would create pressure to close subgoals rather
      than fix cells.

      DONE 2026-08-31. The accounting is now
      `enforcement.check_every_wrong_cell_has_an_owner`, called from
      `equivalence.py`'s findings list as WRONG CELL WITH NO OWNER, over
      `measured.wrong_cells_without_an_owner` /`_wrong_cells` /
      `_live_subgoal_owners`. Self-test 51/51 detected, 0 failed, 0 skipped,
      restored state clean at baseline 1. Cost 0.098s inside the audit, 0.436s
      cold, no subprocesses.
      IT EARNED ITS KEEP ON THE FIRST RUN, which is the part worth recording.
      The hand accounting it replaces was thorough and still wrong, because it
      read the python median only -- the default side. The check found five cells
      the python gets right and the OLX gets wrong (DAY2/p8, PR/p15, Q2/p18,
      Q4a/p9, WK2/p8, six runs each side), now carried as Q32, and it found one
      subgoal whose evidence had gone (Q11, `realistic` over-charge on Q3/p13,
      right on both sides), now closed. Neither was visible to the pass that
      preceded it.
      TWO FALSE-POSITIVE CLASSES WERE FOUND AND FIXED BEFORE WIRING IT IN, and
      both are recorded in the docstring because both would have made the check
      dishonest rather than merely noisy:
        * a cell can be RIGHT at the total and still be a live finding, since
          compensating slot errors summing to the right total are the whole
          reason the slot accounting exists. Declared slot/code cells are exempt
          from the "no longer wrong" arm.
        * a subgoal that MENTIONS a cell is not a subgoal ABOUT it. Q19 names
          1a/p15, Q4a/p20 and Q4b/p8 as CONTROLS, precisely because we score
          them right. Ownership takes any mention; "evidence has moved" takes
          only a TITLE mention.
      Documented as QUALITY_CONTROL.md §2d, next to §2b's after-every-sweep
      error profile, since the two are the same discipline at different grain.
      NOT DONE, deliberately: the check reads the RECORDED ledger, so it is only
      as current as the last `measured.py --record`. It cannot tell a cell that
      improved from a cell that was never re-measured. That is the right
      boundary -- making it re-measure would put a sweep inside the audit -- but
      it means a stale ledger reads as a clean accounting.

- [x] E25. **The `keyword` check is 100% accurate and cannot move a score. Convert it to `derived`.**
      AN AUDIT SUBGOAL, NOT A QC ONE, and it was filed wrong once: its FINDING is
      about accuracy (240/240) but its DELIVERABLE is a primitive conversion --
      turning a model-judged slot into `derived`. That is the audit's own
      direction of travel, governed by the primitives registry and the
      PROSE_ONLY/backlog machinery, and it makes a check comparable between
      engines. The accuracy question is already answered and closed.
      Asked for as "the accuracy of keyword matching on Q4b and elsewhere". First
      the scope: Q4B HAS NO KEYWORD SLOT. Only Q4a and Q4c carry one -- "Uses the
      word antecedent or trigger" and "Uses the word consequence".
      ACCURACY IS NOT THE PROBLEM, and it was measured rather than assumed. The
      keyword verdict has something no other slot in this corpus has: a
      MECHANICAL ground truth. Comparing every verdict against a literal
      case-folded substring search of the student's own text, over the 6-run olx
      artifacts:
          Q4a  120/120 agree (100%)
          Q4c  120/120 agree (100%)
      240 of 240. The model is not getting this wrong, and no rewording is owed.
      THE PROBLEM IS THAT IT IS INERT. Neither slot carries points, and neither
      deduction can charge:
          Q4a  slot pts none;  A_NO_KEYWORD pts 0.0  -- zeroed by decision, so
               the code fires and costs nothing.
          Q4c  slot pts none;  C_NO_KEYWORD pts 1.0  but the credit entry's
               `codes` map is EMPTY, so no verdict routes to it, and the rubric
               declares it in `unreachable_codes`.
      So a required property of a strict schema is spent, on every call, on both
      items, to obtain an answer that is always right and can never change a
      number. That is the cost side of subgoal E1's declared flags, finally
      quantified.
      TWO WAYS OUT, and the record already rules on one:
      (a) WIRE IT. Do not, on Q4c: the component's own comment records that no
          Q4c gold row deducts for the missing word, that the item has no
          1-point deduction of any kind, and that charging it COST THREE CELLS
          AND RECOVERED NONE. A fresh measurement agreed. That is settled.
      (b) CONVERT IT TO `derived`, the primitive built for exactly this -- "a
          check read off the PAGE, field contents, rather than asked of the
          model ... left out of the response schema, so the model is never asked
          to guess at something the runtime already knows." A literal word search
          is the purest case of it in the corpus, and the 240/240 result is the
          evidence that the engine and the model already agree, so the conversion
          is measurably behaviour-preserving BEFORE it is made.
      DO NOT RETIRE IT: Q4a and Q4c both default showChecks=true, so the learner
      SEES "Uses the word antecedent or trigger" in the checklist. Telling a
      first-year to use the course's term is the line's purpose, and costing no
      marks is by design. Deleting the slot deletes the feedback.
      CONVERT IT, and the route is shorter than it first looked. A WRONG TURN IS
      RECORDED HERE because it nearly closed this subgoal on a false premise:
      score.py does not implement the `derived` PRIMITIVE -- it never reads
      item["derived"] -- and I read that as "the paper scorer cannot compute a
      keyword match", which does not follow and is not true. `derive_ledger` takes
      `response: str` and ALREADY inspects it: line ~280 gates the blank-answer
      collapse on `(response or "").strip()`. The text is in hand. Nothing here is
      platform-forced, unlike 1c's typed chart fields, which is the only thing
      COMPUTE_EXEMPT's `derived` entry actually licenses.
      THE WORK, in order:
      (1) add a `contains` kind to `derived` -- the registry already declares
          kinds [plots, complete, present], so this is a fourth, not a new
          primitive;
      (2) implement that kind in all THREE engines: slotSheet.ts, agreement.py,
          and score.py, where it reads the `response` parameter already passed in;
      (3) re-author Q4a's and Q4c's `keyword` slot as a derived check;
      (4) measure. The prior is unusually strong: the model and a literal
          case-folded substring search already agree 240/240, so a divergence
          would mean the conversion is wrong rather than the rule.
      WHAT IT BUYS: two required schema properties out of every call on two items,
      and a check that moves from the model's judgement to the engine's, which is
      the direction E11 and E15 are both pushing. And it must be exercised LIVE
      before closing -- E14 is the standing proof that a primitive can pass every
      unit test while the app cannot build the sheet.
      NOTE FOR COMPUTE_EXEMPT: once `derived` is computed by score.py for this
      kind, the exemption's reason needs narrowing to the 1c `complete` case it
      actually describes, rather than the primitive as a whole. E19's stamp on
      PROSE_ONLY_SLOTS fires on the same event.
      PREFER (b) OVER DELETION unless the checklist display needs it: the student
      is shown "Uses the word antecedent or trigger" as feedback even when it
      costs nothing, and deleting the slot removes that line. Check what
      showChecks renders on both items before choosing.
      MEASURE THE SAVING, since the case for (b) is cost. Two fewer required
      properties per call across 40 cells x 6 runs, and one less thing for the
      model to be confident about -- `confident` is unmet 73 times on Q4c and 85
      on Q4a, so anything that shortens the sheet is worth pricing.

      DONE 2026-09-01. RE-MEASURED THE SAME DAY, because the first measurement
      was recorded from the wrong programs: the `python` half had been swept with
      `--backend cli`, which is Opus, and the `olx` half from agreement.py rather
      than agreement_app.py. Those four entries were reverted and both sides
      swept again on contract -- `olx` = agreement_app.py, `python` =
      agreement.py --backend lo, both gpt-5-mini. The honest numbers:
          Q4a python 18/20               Q4a olx 17/20
          Q4c python 17/19               Q4c olx 17/19
      Before the conversion the Q4a pair was the MIRROR of that -- one cell the
      other way on each side -- and Q4c stood exactly where it stands now.
      (Written without the old fractions on purpose: `prose_claims` matches any
      fraction over the current denominator near an item name, so a "was X/Y"
      beside a current figure reads to the audit as a second, contradictory
      claim. Its docstring says past-tense sentences are exempt; no such test
      exists in the code.)
      Six runs a side, denominators identical, so this is like-for-like.
      NEUTRAL OVERALL, AND ONE CELL MOVED SIDES. Q4c does not budge on either
      side. Q4a gains a cell on python and loses one on olx, and the run spreads
      overlap almost completely -- python [16,17,18,18,18,18] against olx
      [16,16,16,17,17,18]. That is the Q32 pattern rather than a finding: on a
      cell near 50% the median decides which side looks better, and a one-run
      difference flips it. The prediction stands -- the keyword verdict cannot
      charge on either item, so the sheet change could not move a score, and the
      totals confirm it.
      THE PRIOR WAS CONFIRMED BEFORE THE CONVERSION, not after. Replaying the new
      matcher over every recorded verdict on both sides agreed with the model 479
      times in 480, the single difference being Q4c/p13's "conequence".
      WHAT SHIPPED: a fourth `derived` kind, `contains`, in primitives.json and in
      all three engines -- slotSheet.ts/derivedVerdicts.ts, agreement.py, and
      score.py, which reads the `response` it was already handed. Q4a and Q4c
      carry `derived="keyword:contains:..."`; `unclear` left both verdict spaces,
      since a search either finds the word or does not.
      IT MATCHES MISSPELLINGS, which was not in the original plan and came from
      the p13 case. Optimal string alignment against the TARGET WORD, no
      dictionary -- deliberately, because derivedVerdicts.ts runs in the student's
      browser, which has no aspell and no /usr/share/dict, so a dictionary rule
      could not have been replicated in the engine students actually meet. Four
      tiers, each measured against the corpus: <=3 chars exact whole-token; 4
      chars one edit but NO transposition (`from` is one swap from `form`); 5-8
      one edit including transposition; >=9 two. It changes exactly one cell's
      feedback and no score.
      THE TWO ENGINES ARE HELD TOGETHER BY DATA, not by care:
      containsCases.json is read by the vitest suite and by
      check_contains_matcher_agrees_across_engines, so drift in either fails.
      Injection-tested both ways -- flipping a case, and gutting the table.
      FOUR DEFECTS THE AUDIT FOUND ON THE WAY, all pre-existing or self-inflicted
      and all fixed:
        * the generated prompt told the model this keyword check was "satisfied
          when EVERY week of data is present" -- the `else` branch describing the
          CHART had become a catch-all for every kind but `present`;
        * `cli_signatures` built its computed-key set from a hand-written
          `equals`+`counts` list, the same mirror-of-the-registry score.py had
          already been fixed for. It had fallen behind by four primitives and was
          reporting Q4b's `behavior_1`/`behavior_2` as model inputs -- a defect
          older than this goal;
        * the `derived` probe blanks one field and expects the verdict to move,
          which is right for `plots` and wrong for `contains`, so it reported
          "reaches no verdict" against a rule that works;
        * COMPUTE_EXEMPT needed narrowing, as this entry predicted. It is now
          scoped BY KIND rather than deleted -- deleting would have satisfied the
          check while losing the guarantee that 1c's `complete` is still
          uncomputed on the paper path. It probes READ now, where it was
          INCONCLUSIVE before, so the declaration is enforced for the first time.
      EXERCISED AS E14 DEMANDS: check_action_attributes_are_declared_in_the_block
      is clean, and llmActionSmoke.test.ts now carries the SHIPPED Q4a and Q4c
      sheets verbatim -- the synthetic shapes it tested before are exactly what
      let E14 through -- asserting that `keyword` leaves the schema on both items
      and that the verdict computes. 2135 TS tests, typecheck clean, self-test
      51/51.
      ONE CELL MOVED, AND IT IS NOT A SCORE: Q4a/p9 INVERTED. It was python-right and
      olx-wrong; it is now olx-right and python-wrong, 6/6 stable on both sides, with
      nothing about `antecedent_2` touched. Declared in GOLD_SLOT_BOUNDS_KNOWN and
      recorded in Q32, where it is now the first thing to read.
      A TRAP WORTH RECORDING: sweeping with `--items Q4a Q4c --out H1.json` writes
      ONE handout-level artifact, and `_runs_doc` looks for `{item}.runs.json`. The
      per-item lookups then returned empty and the audit reported three declared
      slot disagreements as RESOLVED -- three declarations nearly deleted on a
      false positive. Sweep per item, or split the artifact before recording.
      AND MEASURED ON THE THIRD ENGINE, 2026-09-01, which this goal implemented
      and nothing had yet exercised. score.py computes `contains` from the
      `response` it was already handed, and the paper side of both items now
      exists -- the FIRST paper column the ledger has ever held:
          Q4a olx 17/20   python 18/20   paper 15/20
          Q4c olx 17/19   python 17/19   paper 17/19
      Six runs each, all three on gpt-5-mini, so the paper figure differs from
      the other two by PROMPT (the rubric rather than the OLX sheet) and not by
      model. Q4c is identical across all three engines, which is the strongest
      statement available that the conversion is behaviour-preserving. Q4a's
      paper side is three cells below python; that gap is not this goal's -- it
      predates the conversion and belongs to whatever explains the rubric
      prompt's Q4a performance.
      A HOLE IN THE SIDE CONTRACT WAS FOUND BY DOING THIS, and it was the one
      that mattered. `_artifact_program` classified a FOLDED paper artifact as
      "" -- paper_runs.py gives it a `runs` array, so the no-runs test missed it,
      and its results are keyed `_pid`/`credit_checks` rather than `cell` or
      `participant_id`. An empty classification SKIPS the program check, so the
      single shape most likely to be filed under the wrong side was the one
      shape nothing objected to. Fixed and verified: the fold is accepted as
      `paper`, refused as `python`, refused as `paper_opus`.
      UNBLOCKS E28, which was waiting on this.


- [x] E26. **Sibling items sharing a slot NAME should share its gate structure, or declare why not.** DONE
      2026-08-29. `check_sibling_slots_share_their_structure` reads the OLX slot
      specs -- not a run artifact, so it needs no sweep -- groups slots by NAME
      within a declared family, and reports any whose (gates, points) shape is not
      uniform unless declared in SLOT_STRUCTURE_DIVERGENCES.
      THE SURVEY IT WAS BUILT ON: 27 slot names across the eight H2 items. 26 are
      uniform. Exactly one is not, and it is the one Q26 found --
      `phrased_directly`, advisory on DAY2/NP/NR/PP/PR/WK1/WK2 and gating on DAY1.
      So the check is quiet by construction and will stay quiet until something
      changes, which is what makes it worth running on every audit.
      DECLARED AS UNDECIDED, deliberately. The entry names Q26 and says the answer
      is not yet known, rather than either tolerating the divergence silently or
      going red until someone decides. It comes out either way -- replaced by a
      real reason, or by making DAY1 match -- and the budget of 1 ratchets so it
      cannot quietly become the place divergences accumulate.
      SCOPED BY FAMILY, per the subgoal: `keyword` legitimately differs between
      Q4a and Q4c (one deduction zeroed by decision, the other declared
      unreachable) and 1a's week_* slots are not siblings of H2's gates. Only the
      eight H2 cadence-and-type items are declared a family so far;
      SLOT_STRUCTURE_FAMILIES is where another would go.
      Injection-tested four ways: undeclaring the known divergence, introducing a
      new one into the OLX (`you_arrange_it` flipped), budget slack, and a
      declaration that has stopped being true because the family converged.
      WHY THE AUDIT COULD NOT SEE THIS BEFORE: both scorers honour whatever the
      OLX says, identically, so nothing in the equivalence machinery objects. It
      is a RUBRIC defect, and the equivalence audit was not looking for those.
      Split from Q26 on 2026-08-29, which found the instance: `phrased_directly`
      GATES on DAY1 and is advisory on its seven siblings, the difference being a
      single `!` in one OLX slot spec, declared nowhere. Q26 decides whether that
      one is a decision or a typo. THIS is the check, and it stands either way.
      WHY IT IS AN AUDIT SUBGOAL and not part of that decision: the eight
      cadence-and-type items are one family authored from one pattern, and the
      audit cannot presently tell a deliberate divergence in that family from a
      typo. Both scorers honour whatever the OLX says, identically, so nothing in
      the equivalence machinery objects -- which is precisely the blind spot.
      SAME SHAPE AS `check_action_attributes_are_declared_in_the_block`: read the
      published sheets, group slots by NAME across items, and report any slot
      whose `gates`/`pts` structure is not uniform across the group unless the
      pair is declared. Cheap, structural, catches a class rather than an
      instance, and needs no model call.
      SCOPE IT BY FAMILY, NOT BY CORPUS. `keyword` legitimately differs between
      Q4a and Q4c (one deduction zeroed, the other unreachable), and 1a's week_*
      slots are not siblings of H2's gates. The grouping that matters is items
      built from the same pattern; start with the eight H2 cadence-and-type items,
      where the family is unambiguous, rather than trying to define siblinghood
      corpus-wide on the first pass.
      DECLARE, DO NOT NORMALISE. The check's output is a question -- "these seven
      agree and this one does not" -- and the answer may well be that the odd one
      is right. A declaration table keyed by (family, slot) with a reason is the
      product, not a sweep that makes every slot identical.


- [x] E12. **`--selftest` without `--enforcement` silently scores nothing.** DONE
      2026-08-29 (2c87cc6). It is now a usage error naming the correct
      invocation, not a fallthrough that runs the prompt audit and exits 0. An
      ERROR rather than an implied --enforcement, because the two modes cost
      different amounts of time and someone who typed one should be told which
      they are getting.
      THE CLASS SWEEP FOUND A SECOND LIVE INSTANCE, which is why the subgoal
      asked for it: `cross_path` read `--slots` only in the non-`--gold` branch,
      so every `--slots --gold` invocation silently dropped `--slots` -- and the
      missing slot section reads exactly like "no slot diverged". It was being
      run that way all through the sweep, and the output was cited as evidence it
      had never produced. No conclusion moved (the verdicts rest on the era check
      and set-disjointness, and with zero divergent cells there were no slot bases
      to print), but the citation was wrong. Both now error.
      Remaining flags checked: equivalence.py's --item/--python/--scoring/--fixture
      and agreement_app.py's are each read in their own dispatch branch, so none
      has this shape.
      Found 2026-08-28, during the olx sweep, by running it wrong and believing
      the result. `equivalence.py --selftest` is only honoured together with
      `--enforcement`; alone, argparse accepts it, the flag is never read, the
      default prompt audit runs instead, and the process EXITS 0. So a self-test
      that never executed is indistinguishable at the shell from one where all
      49 injections were detected.
      THE COST IS ALREADY PAID, not hypothetical: it was used here to certify a
      change to the artifact-shape reader, reported as verified on the strength
      of that exit 0, and the correction had to be issued in the next message.
      Every other check in this tree can be wrong and the self-test is what says
      so; a mode where it appears to run and does not is the worst possible
      place for a silent no-op.
      FIX: make `--selftest` without `--enforcement` a usage ERROR, not a
      fallthrough -- `ap.error("--selftest requires --enforcement")`. Prefer that
      to quietly implying `--enforcement`, because the two modes take different
      amounts of time and a user who typed one and got the other should be told,
      not accommodated. Then check the same class across the other flags in
      `equivalence.py`: any flag that is read only inside another mode's branch
      has this bug, and `--slots`/`--gold` on `cross_path.py` deserve the same
      look.

- [x] E13. **The self-test degrades silently: a lost case looks like a passing run.** DONE
      2026-08-29 (2c87cc6). The denominator was `len(cases)`, so a case that
      stopped being CONSTRUCTED took the denominator down with it: 48/48 and
      49/49 are indistinguishable at a glance. `SELFTEST_EXPECTED` is now a
      two-sided ratchet over built + skipped, SKIPs are counted in the summary
      line rather than scrolling past above a confident total, and a short run
      exits non-zero.
      IT CAUGHT ITS AUTHOR ON THE FIRST RUN, which is the best evidence it works:
      I set the constant to 51 by counting from memory -- "49 cases and the two
      SKIP lines I remembered" -- and the ratchet reported a lost case. Only the
      plain-path case skips; the `{fail}` injection site still exists on Q6, so
      that case is built. Set to 50 from a measured run, with the reason recorded
      in the constant so it is not re-derived.
      Found the same way and in the same hour as 12, and the two should be read
      together -- 12 is the suite not running, this is the suite running SHORT.
      `equivalence.py --enforcement --selftest` prints `N/N injected breakages
      detected` where N is however many cases the run happened to build. A run
      that detects 48 of 48 is visually identical to one that detects 49 of 49,
      so a case that stops being constructed reports success.
      TWO WAYS A CASE DISAPPEARS, both live:
      (a) it CRASHES the suite. The `SLOT RULE NAMES A VERDICT` case hard-coded
      Q4b/`behavior_1` as its injection site; audit subgoal E10 converted that
      rule's logic into the `maps` primitive, the entry lost its `rule` key, and
      the suite died on a KeyError BEFORE ITS FIRST CASE. The guard over every
      other check was taken out by a conversion it was not watching, and stayed
      dead until something else made it run.
      (b) it SKIPs. Fixed the same day by choosing the site at run time and
      skipping when no rule carries `{fail}` -- the degradation the plain-path
      case already used. That is the right behaviour and it is still invisible:
      two SKIP lines scroll past above a confident `47/47`.
      THIS IS THE DIRECTION OF TRAVEL, which is why it matters now rather than
      later. Subgoals 3, 9, 10 and 11 all convert prose rules into primitives,
      and each conversion can remove the last site some case injects into. Only
      two `{fail}`-bearing rules are left in the whole tree, both on Q6
      (`affect_c1`, `affect_c2`) -- the same pair a removal script once destroyed
      -- so this particular case is one conversion away from permanent SKIP.
      FIX: assert the case COUNT. Record the expected number of constructed
      cases and fail the run when the suite builds fewer, so dropping one is a
      failure rather than a shorter success line. Count SKIPs explicitly in the
      summary line (`47 detected, 2 skipped, 49 expected`) instead of letting
      the denominator float. A ratchet, like HANDCODED_ITEM_RULES' budget: the
      number may only go DOWN by decision, never by accident.

- [x] E2. **A full two-sided sweep: every item, six runs, BOTH scorers.** DONE
      2026-08-29. 26 of 26 items on both scorers, six runs each, era-checked per
      item.
          python  451/491 = 91.9%        OLX  457/491 = 93.1%
      THE ANSWER TO THE QUESTION THE GOAL WAS OPENED ON IS NO: the two scorers do
      not disagree. `cross_path` finds ZERO cells out of 491 where the paths never
      agree -- every cell's score sets overlap, which is stricter than comparing
      medians. Per-item deltas are all within +/-1: seven items +1, one -1 (PR),
      eighteen identical.
      THE CONTROL THAT MAKES THAT READABLE: the three items with no model call --
      T1, T2, 1b -- are CELL-FOR-CELL IDENTICAL across both engines, 60 cells and
      720 observations without a single difference. So where no model is involved
      the two implementations compute the same thing, and the +/-1 differences
      elsewhere are model variance rather than engine disagreement.
      WHAT IT ACTUALLY FOUND was a different defect: seven items the app could not
      score AT ALL (E14). Six of those were re-measured after the fix and every
      one is comparable, which is also the evidence that `forbid` and `maps`
      compute identically on both engines.
      Do not read 91.9% against 93.1% as a quality gap without the per-item table:
      it is six cells spread over seven items, each inside the run-to-run spread.
      Replaces "clear the stale H2 items", which would have measured one side of
      ten items. This measures both sides of all of them, and it is the only
      thing that can answer the question the whole goal is about: do the python and
      the olx give comparable scores now?
      Ten items are stale from the leakage rewrite and the A_NONE/C_NONE wiring,
      subgoals E3-5 will move more, and every declared divergence in the tree is a
      claim about a difference between the sides that has never been measured
      end to end -- only probed per rule. Q4b/p12 is the warning: python 5.0 six
      times of six, olx 3.5 eleven of twelve, and nothing declared it.
      COST, stated plainly: 23 items take model calls (1b, T1 and T2 are
      deterministic), so six runs is about 2,760 calls a side and ~5,500 for
      both. Do it LAST, after 3, 4 and 5, so it measures the finished state
      rather than a state that is about to change.
      Record each side, then compare per item AND per cell: an item can agree on
      the number while disagreeing on which cells it got right, and that is
      exactly the shape a per-item comparison hides.

      OUTSTANDING BEFORE THE SWEEP, checked 2026-08-28:
        1. THE LEDGER HAS NO SIDE. `measured.py --record ITEM ARTIFACT` stores one
           number per item and it is the olx-prompt path; MEASURED.json has no
           per-side dimension. A two-sided sweep has nowhere to put the python's
           numbers, so this is a hard prerequisite, not a nicety. Either add a side
           to the ledger or record the python in its own.
        2. TWELVE OF 26 ITEMS ARE RECORDED AT 3 RUNS: 1a 1b 1c D1 D2 NP PP Q4c Q5
           Q6 T1 T2. The sweep at 6 fixes it by construction, but their current
           numbers cannot referee a 2-cell move, so nothing should be compared
           against them in the meantime.
        3. THREE ITEMS' python PROMPTS MOVED TODAY and are unmeasured on that side:
           1a, Q4b and Q6, from `rule` replacing `desc` in the python render. 1a also
           gained five migrated rules. All three are olx-unchanged, so only the python
           half of the sweep is affected.
        4. TEN ITEMS ARE STALE PROMPT, which the sweep clears; that is its job.
        5. cross_path reports 25 divergent cells against cli_v8, 15 of them 1c and
           declared. The rest cannot be attributed until both sides are era-matched,
           which the sweep's artifacts will be -- era stamping landed today.
        6. Q4b/p12 needs a decision of its own, independent of subgoal E9: the olx
           applies a deliberate divergence there and gold sides with the python.

      PRECONDITION, set 2026-08-28: before the sweep runs, the two sides must put
      the SAME RULE LOGIC AND THE SAME RULE LANGUAGE to the model. Byte-identical
      prompts were considered and RETRACTED the same day, on the right grounds:
      the two sides are fed the student's work differently -- the olx has one box
      per field, the python has one segmented block per item -- so a shared document
      would have meant rewriting the python's whole prompt path to serve a
      difference in plumbing. Measured before retracting, and worth keeping: the
      generator IS the shipped artifact (`build_web_prompt` reproduces all 23 OLX
      bodies byte-for-byte once its `\x00REF:` sentinel is expanded), and
      `agreement_app.build_jobs` reconstructs the olx's per-box fixture from the
      same paper block the python segments. So identity was reachable; it just was
      not worth what it cost.
      Where the wordings differ, the OLX's wins -- unless the difference is
      forced by how the response text is presented, or the olx is CLEARLY WRONG,
      as in the DAY1 contradiction subgoal E6 found and fixed.
      AND THE RULE IS ABOUT WORDING, NOT SCORING (user, 2026-08-28). "OLX wins"
      settles which of two ways of SAYING the same rule to use; it never settles
      which of two ANSWERS is right. Gold does, and SYMMETRICALLY: whichever side
      matches gold better is the one kept, and the other moves. If the olx matches
      gold better, prefer the olx; if the python does, prefer the python.
      MEASURED, 0 calls, `cross_path.py --gold` over paper_mini_v8 against cli_v8:
      the OLX-PROMPT path matches gold better overall, 456 cells of 519 against
      440. It wins 10 items, ties 15, and loses exactly one -- Q1, where the paper
      scorer is 19 of 20 against the olx's 17. So the olx is the right DEFAULT on
      scoring too, and Q1 is the standing exception.
      ON A TIE, PREFER THE OLX (user, 2026-08-28) and resolve the divergence that
      way: the olx's reading is the reference and the python converges. It does NOT
      freeze the olx's accuracy -- improving the olx's own rule against gold is
      still the right work, and a change there is a change to the reference side,
      which is where changes belong. What the tie-break forbids is adopting the
      python's reading as the target merely because it lands on gold in the cells
      someone happened to write a declaration about. Q4b is the live case: 15
      against 15, so the olx wins it.
      A NAMING TRAP worth stating: the artifact directory called `cli_v8` is
      agreement.py, the OLX prompt scored in python, and `paper_mini_v8` is
      score.py, the path this goal calls the python. Reading the directory names as
      sides inverts the conclusion, so cross_path now prints each side's KIND.
- [x] E6. **The criteria prose was written twice, and the copies had drifted.**
      Found while establishing subgoal E2's precondition. `score.py:build_prompt`
      held the `derive_from_criteria` block and `olx_prompts._criteria_section`
      held a copy whose docstring called it "score.py:build_prompt's
      derive_from_criteria block, verbatim". It was not verbatim: criterion 5's
      example ("{{corpus:PR/p1:pr:0:42:sha=34e8b80f4178:shape=C1}} body" against "a
      rested body, or fitness itself, following the behaviour that produces
      it"), criterion 7's example ("the extra chore" against "30 pushups"), and
      criterion 10's WK1 rule, which the olx had grown and the python had not. All
      eight OC items were affected and every audit was green, because each side
      was internally consistent and this prose is authored in the SCORERS rather
      than in the rubric -- so it fell between the prompt audit, which compares
      rubric elements to the olx, and the enforcement audit, which compares
      declarations.
      The python's copy had never been leakage-scanned either: `leakage.py` reads
      rubric `guidance`/`rule` strings and `SLOT_NOTES`, not `score.py`. The two
      drifted examples were the ones the olx-side leakage rewrite had already
      replaced.
      FIXED STRUCTURALLY: score.py calls `_criteria_section`, so there is one
      source and nothing left to keep in step. The olx's wording won everywhere
      except one case where the olx was clearly wrong (below). Three
      substitutions remain, each forced by the python's ANSWER SHEET and each
      declared in EQUIVALENCE.md: `evidence` -> `behavior` (its criteria object
      has no evidence field), `yes`/`no` -> true/false (its criteria are
      booleans), and dropping "one point, and it charges ONLY this" (the engine
      computes the score; its model never sees points).
      THE OLX WAS CLEARLY WRONG ON DAY1, in two places, and was fixed to match
      what the python had: its criterion 7 said the avoidance reading "never changes
      the score" while its own guidance said "AVOIDANCE FRAMING TAKES THE WHOLE
      ITEM HERE ... the graders scored those zero", and its `consequence_asserted`
      note repeated the false half. Now declared once, on the rubric, as
      `rubric_h2.AVOIDANCE_SCORES`, and read by both generators.
      VERIFIED, 0 model calls: the 56-row `oc_grid` is IDENTICAL across the change
      (prompt text moved, scoring logic did not); 191 of 200 python criteria
      sentences match the olx verbatim after the declared substitutions and the
      other 9 are numbered-list prefixes and a trailing period, each rule body
      confirmed character-identical to the olx's note; exactly one olx prompt
      moved (DAY1) and the other 22 are byte-unchanged.
      GUARDED: `enforcement.check_criteria_prose_has_one_source` fails the build
      if that branch stops delegating or if prose reappears in it, counting TOTAL
      literal length rather than the longest literal -- the first version passed a
      synthetic paste assembled from `+`-joined pieces. Both halves were proved to
      fire before being trusted.
      Two stale exemptions fell out of the change and were removed, and
      `consequence_asserted` left `check_slot_rules_reach_both_prompts`' BACKLOG
      by being FIXED rather than by rotting: score.py reads it now, so the
      "SLOT_NOTES is olx-only" premise no longer holds for it. Which keys those
      are is declared in `olx_prompts.CLI_CRITERIA_NOTES` rather than copied into
      the check.
- [x] E9. **Q4b's `behavior_1`/`behavior_2`: convert the referent test to `forbid`.**
      CLOSED WITHOUT IMPLEMENTING, and replaced by subgoal E10 plus a declaration.
      The asymmetry is now declared in `olx_prompts.SCORING_DIVERGENCES`, which
      closes the audit hole subgoal E5 found at zero risk and zero calls, and the
      experiment itself moved to subgoal E10 where it can be measured properly.
      Raised BY the registry, 2026-08-28, under the standing rule that any
      PROSE_ONLY_SLOTS entry marked CONVERTIBLE becomes a subgoal here rather than
      a note in a table. `enforcement.check_convertible_prose_rules_have_subgoals`
      enforces that: a CONVERTIBLE entry with no subgoal naming it fails the audit.
      WHAT CONVERTS. Both slots carry five fail conditions in prose, and one of
      them is arithmetic wearing prose: handouts.py records a sixth test measured
      into these rules -- an entry that names the same THING as one of the
      student's own 4a antecedents fails, "judged by REFERENT and not by topic".
      Two answers compared by referent is `forbid`-shaped, exactly like
      `consequence_not_a_setup`. The other four conditions judge what an entry IS
      and stay prose.
      WHY IT MATTERS MORE THAN THE OTHER SEVEN. This pair IS the demonstrated
      cross-path divergence: Q4b/p4 paper 2.0 against olx 3.5 with gold at 2.0,
      and cross_path localises it to these two slots. A `forbid` declaration is
      something `equivalence.py --enforcement` can compare between the scorers;
      the prose it replaces is not, which is why the divergence went undeclared.
      CONVERT THE PAIR TOGETHER. behavior_2 restates behavior_1's conditions for
      the second entry, so converting one alone would have the two entries judged
      by different machinery on the same item.
      DIRECTION: THE OLX MOVES TO THE python HERE. On p4 the paper path scores 2.0,
      which IS gold, and the olx scores 3.5. So this is not a case of "olx wording
      wins" -- that rule is about which way to SAY a shared rule, and it does not
      decide which of two answers is right. Gold does, and gold is with the python.
      The `forbid` declaration should reproduce the python's refusal and the olx
      should start charging it.
      NOT BEHAVIOUR-PRESERVING, unlike subgoal E3's seven: this moves a test from
      the model's judgement to the engine's arithmetic, so `oc_grid` cannot certify
      it and the sweep must measure it. Q4b sits at 16/19 over 6 runs, and p4 and
      p12 are the cells to watch -- p12 because it is where the two paths already
      disagree 6-of-6 against 11-of-12.
      STOPPED BEFORE IMPLEMENTING, 2026-08-28, on three findings from reading the
      record first (§2c). The design is ready; the decision is not mine.
      (i) THIS TEST WAS ALREADY MEASURED AND REJECTED. handouts.py records it, in
          prose form, on 3 runs: counted [14,13,13] -> [15,12,14], p4 moving 0/3 ->
          1/3 and the four gold credits holding. Not adopted, and for a reason the
          guide states: "a mean of 13.67 against 13.33 for three times the variance
          is the trade the guide refuses, since a configuration that swings three
          cells cannot tell you whether the next change helped." It leaves "the
          door open to a steadier formulation of the same test" -- which a `forbid`
          decomposition genuinely is, since asking the operands separately is the
          documented reason `forbid` exists. But it is the same test, and the
          variance is the thing to beat, not the mean.
      (ii) THE TWO DECLARED CELLS PULL OPPOSITE WAYS, AND THE ITEM IS A TIE. On p4
          gold is 2.0, the python gives 2.0, the olx 3.5 -- the olx must charge MORE.
          On p12 gold is 5.0, the python gives 5.0, the olx 3.5 -- the olx must charge
          LESS, and what it applies there is the fifth test, a DELIBERATE divergence
          measured at +1 cell a run. So "make the olx match the python on Q4b" is two
          changes in opposite directions, and the referent test addresses only p4.
          CORRECTION to what this entry first said. Both DECLARED cells favour the
          python, and I read that as the python being the better side on Q4b. Measured, it
          is not: `cross_path --gold --item Q4b` puts the item at 15 against 15,
          because p6 goes the other way -- gold 3.5, olx 3.5, paper 5.0. Two
          declared cells are the two someone wrote an entry about, not a sample of
          the item, and the symmetric gold rule has to be applied to the item and
          not to the cells that already have paperwork.
      (iii) `forbid` CANNOT TARGET A MODEL-ANSWERED SLOT. Its key is computed and
          excluded from the response schema, so making `behavior_1` the key would
          delete the four prose tests the model must still apply. The workable
          shape: two new referent PICKS, and two computed checks whose `forbid`
          conditions include `behavior_1=met` so the charge cannot stack on a
          `wrong_kind` the model already reported -- B_NOT_ACTIVE is repeatable, so
          without that second condition one bad entry would cost 3.0. Q4b today has
          no `slots` picks, no `choices` and no `forbid` attribute, so this needs
          authored OLX changes, a FORBID table for handout 1, and the schema
          derivation extended to the `derive_from_credit` path.
      WHAT I RECOMMEND, if the aim is the audit's blindness rather than p4: declare
      the asymmetry in `olx_prompts.SCORING_DIVERGENCES` now -- that closes the
      hole subgoal E5 found, at zero risk and zero calls -- and treat the referent
      test as a separate measured experiment after the sweep, when there is a
      6-run baseline to judge its variance against. The 3-run history is exactly
      why it was rejected before.
      Lower PROSE_ONLY_BUDGET from 9 to 7 if both slots leave the list; if only the
      referent test moves and the four judgement conditions stay, the entries
      REMAIN and their reasons must be rewritten to say so.

- [x] E7. **§2c's recorded-comment lookup is blind to all twelve H2 items.** FIXED
      2026-08-28. `prior_record` found an item's comments by searching for a literal
      `"id": "DAY1"` line and scanning to the next `"id":`. rubric_h2 builds its
      items from a factory, so no H2 item ever matched and the hook printed "could
      not read rubric_h2.py: StopIteration" on every H2 `--write`. Visible, and
      unread -- which is the only kind of failure a printed warning produces.
      Now found by MENTION, with the literal-dict SPAN still winning where there is
      one. That ordering matters and was measured: taking both let a file-level
      comment about scoring granularity, which merely sits near a mention of Q1,
      occupy one of only three display slots while one of Q1's own six comment runs
      dropped off the end. Widening the search made the H1 output worse before it
      made the H2 output exist.
      A FACTORY-BUILT ITEM'S RECORD IS IN ITS FACTORY. D1 and D2 are
      `_definition_item("D1", ...)` and nothing else in the file names them, so
      mention-matching alone still found nothing for either; the constructing call
      is resolved to its `def` and that body is searched too. D1, D2 and T1 went
      from 0 blocks to 1.
      1c and 3 remain at 0, verified rather than assumed: their entries' longest
      comment runs are three lines against a threshold of four. They are declared
      in `NO_RUBRIC_COMMENTS` so the silence is a statement, not an accident.
      GUARDED by `check_prior_record_reaches_every_item`, which asserts per item
      that the hook neither fails its lookup nor comes back empty undeclared.
      Proved to fire: with the pre-fix lookup restored it reports 10 findings, which
      is every H2 item in ACTION.
      AND THE CAP NOW SHOWS THE RIGHT END (user, 2026-08-28). Three blocks are
      still printed, but the LAST three rather than the first: an entry accumulates,
      general decisions written early and measured findings piling up at the bottom,
      so `block[:3]` was showing the oldest and cutting the newest. Q1 has six runs
      and now surfaces rubric_h1.py:246-279 -- the `reasons_given` counting rule,
      which is the comment §2c was written about after ~900 calls were spent
      rediscovering it. The earlier blocks are NAMED with their line spans and a
      `sed` command rather than dropped, because a later comment routinely assumes
      an earlier one: "the same rule" and "reverted again" mean nothing without
      what came before.

      AS FOUND, for the record: the hook reported `could not read rubric_h2.py:
      StopIteration` on every H2 `--write`, visibly, for as long as rubric_h2 has
      been a factory. §2c is a discipline the record is supposed to enforce
      automatically, and on the handout with the most recorded dead ends it
      enforced nothing. Pre-existing, not caused by the subgoal E6 work that
      surfaced it.

- [x] E3. **Seven scoring rules the two sides implement separately.** Widened
      from POLARITY_GATE_ITEMS once the audit's new hand-coded check listed them
      all. Every one is DECLARED on the olx and HAND-WRITTEN in `score.py` as an
      `if item["id"] in ...` branch, which the enforcement audit cannot compare
      because it compares declarations:

          key                          olx declares          python does
          states_a_contingency         GATE (DAY1,DAY2,WK2)  branch -> NOT_OC
          agent_delivers_consequence   GATE (WK1)            branch -> NOT_OC
          aimed_correctly              GATE (WK2)            branch -> NOT_OC
          consequence_not_a_setup      forbid (DAY1,DAY2,WK2) hand-written conjunction
          barrier_is_not_this_type     forbid (NR)           hand-written conjunction
          targets_own_behavior         slot (all)            WK1 maps a pick by hand
          avoidance_frame              --                    DAY1 gates on it in code

      THREE ARE PLAIN GATES the olx already marks with `!`. Nothing needs
      inventing: the declaration exists and the python does not read it. Those are
      the cheapest and should go first.
      TWO ARE THE SAME CONJUNCTION under different names -- both test
      `restriction_authored=created`, `trigger_expects=gain`,
      `restricts=other_thing` -- written out twice in score.py and declared as two
      separate `forbid` rules on the olx. One rule, four implementations.
      ONE, `avoidance_frame`, carries a comment saying it exists to stop the two
      sides scoring the same answer differently. Someone hit this divergence
      class before and fixed it by hand-coding, and the hand-coding is what now
      hides it.
      NOT A PURE SWAP for any of them: each branch also charges NOT_OC with
      item-specific wording and RETURNS, short-circuiting later checks.
      Reproducing that needs the declared check bound to a gate or a code, so do
      them ONE AT A TIME and replay the recorded sheets after each -- the replay
      costs nothing and catches a behaviour change the audit would not.
      `score.py` already has a general `forbid` reading `item["forbid"]`, so the
      two conjunctions convert the way Q4a/Q4c did.
      Delete each branch's line from `enforcement.HANDCODED_ITEM_RULES` as it
      goes; the check fires on a stale exemption, so forgetting is caught.
      SIX OF THE SEVEN ITEMS ARE ALREADY STALE (subgoal E2), so this can ride that
      sweep instead of costing its own -- but only if it lands before the sweep.

      PROGRESS, 6 of 7 converted, all verified behaviour-preserving at 0 model
      calls by the 56-row `oc_grid` being IDENTICAL across each step:
        [x] states_a_contingency, agent_delivers_consequence, aimed_correctly --
            the three plain gates, now `rubric_h2.OC_GATES`, iterated in declared
            order because the first gate to fail owns the message.  (3a8d758)
        [x] avoidance_frame -- now `rubric_h2.AVOIDANCE_SCORES`, the same
            declaration that decides whether the criteria prose promises this
            reading "never changes the score", so prompt and arithmetic cannot
            disagree about it again. The exemption it replaced described the rule
            BACKWARDS.  (b5d19fe)
        [x] consequence_not_a_setup + barrier_is_not_this_type -- one
            `rubric_h2.FORBID` declaration. It had FOUR implementations, not two:
            both score.py branches AND a hand-authored `forbid=` attribute in the
            .olx. The rubric declares it and `olx_prompts.forbid_attr_for`
            generates the attribute; regenerated OLX byte-identical, and the
            generator's ownership proved by perturbing the declaration.  (77026ed)
        [x] targets_own_behavior -- WK1's `trigger_behavior` -> boolean mapping,
            the last one, and its own exemption text had already diagnosed it as
            `expect`-shaped. Now `rubric_h2.EXPECT`, generated into the olx's
            `expect=` attribute by `olx_prompts.expect_attr_for` and read by
            `score._expect_rule`. The four `demonstrates_type` expects on
            NP/NR/PP/PR are deliberately NOT declared: the python reaches that fact
            through `expected_type` + REQUIRED_MOVE, already a rubric
            declaration, and a second declaration of one fact is the thing being
            removed. Verified by the 56-row grid AND by an exhaustive truth table
            over nine `trigger_behavior` values -- missing key, whitespace, empty,
            None, wrong case, nonsense -- because the grid does not exercise them
            all and the old branch's `.strip()` and `"utb"` default were load-
            bearing.

      SUBGOAL 3 IS COMPLETE, 7 of 7. `derive_oc_ledger` now contains no item-id
      comparison at all, asserted by walking its AST rather than by reading it.
      The seven entries left in HANDCODED_ITEM_RULES are all non-scoring and were
      already declared as such: five `build_schema` shapes, one prompt hint, one
      python flag filter. The `build_schema` five are the obvious next candidates --
      WK1's asks for `trigger_behavior` precisely because the `expect` rule reads
      it, so the declaration could drive the schema too -- but that is a separate
      question from scoring equivalence and should be decided on its own.

      Worth recording about the method: every one of these was found or kept
      honest by a check rather than by memory. Two stale exemptions surfaced the
      moment their branches went, the wrong DAY1 description was only visible
      once the code was read beside it, and the audit cannot check an exemption's
      PROSE -- only that the branch it names still exists.

- [x] E4. **Hash the scoring-path helpers, then re-stamp.** DONE. The three named
      helpers were the symptom; the fault was that the fingerprint hashed a LIST
      OF ROOTS and hashing a function does not hash its callees. `measured._closure`
      now takes the transitive closure of local callees, so the class is fixed
      rather than three names: twelve functions came in, and only three of them
      were the ones anyone had noticed.
      TWO MORE FAULTS IN THE SAME MECHANISM, both found on the way and both of the
      same kind -- a guard quietly narrower than it appeared:
        - `SCORER_PARTS` was authored by hand beside `_ALWAYS` and had drifted: it
          omitted `agreement.expand_counted`. So the WHOLE-PATH fingerprint -- the
          ledger header's, and the fallback for an item whose shape cannot be read
          -- was narrower than every per-item one, when its entire job is to be
          conservative. It is now derived from the three authored tables.
        - the primitive scoping detected `forbid`/`equals`/... by scanning the
          `<LLMAction>` open tag, but olx_prompts reads those from `_sheet_tag`,
          "whichever element carries this action's slot sheet", which is not always
          the same element. Q4a and Q4c declare `forbid` there, so `parse_forbid`
          was absent from their fingerprints while their numbers depended on it.
          Both tags are scanned now, and the effect was to make the scoping FINER:
          12 distinct fingerprints across the corpus, up from 4.
      THE FIRST ATTEMPT BROKE THE SCOPING, and measurably: `load_action` is an
      unconditional root and parses the whole sheet, so it calls every primitive
      parser, and the raw closure pulled `parse_forbid` onto all 26 items -- a
      one-line edit to it moved every fingerprint, rebuilding by the back door the
      global flag that the docstring incident cost ~1800 calls to eliminate.
      `_scoped_closure` keeps a part that is item-dependent BY DESIGN only when
      the item's roots asked for it; everything else the closure finds is
      unconditional and comes in.
      MEASURED, three properties, each proved by injection rather than argued:
        a behaviour edit to `verdict_of` (unconditional) moves 26/26;
        a behaviour edit to `parse_forbid` (item-dependent) moves exactly the 6
        items that author it -- DAY1, DAY2, NR, WK2, Q4a, Q4c;
        rewording an existing docstring moves 0/26.
      RE-STAMPED all 26 entries, and the claim on them is evidenced rather than
      asserted: `git log -L` shows none of the eleven newly-covered functions
      modified since 2026-08-18, before the oldest recorded number, so the wider
      fingerprint is safe backwards as well as forwards. The instrument was
      checked against functions known to have changed today (13, 2 and 4 commits)
      before its zeros were trusted. 0 STALE SCORER after; the same 10 STALE
      PROMPT as before.
      GUARDED by `enforcement.check_scorer_fingerprint_covers_its_callees`: for
      every hashed function, every local function it calls must be hashed too, and
      the scoping may drop only an item-dependent part. Proved to fire -- 13
      findings when `_closure` is reduced to returning its roots, naming
      `apply_computed -> answer_of` first, which is the original defect.
- [x] E8. **Clear the seven entries left in HANDCODED_ITEM_RULES.** DONE, table EMPTY, budget 0. Set 2026-08-28
      at the user's direction: do it even though all seven are non-scoring, so the
      table empties rather than settling into a permanent backlog. They are five
      `build_schema` shapes (BARRIER_PICK_ITEMS, CONTINGENCY_GATE_ITEMS,
      MOVE_PICK_ITEMS, 'WK1', 'WK2'), one `build_prompt` hint (('Q1','Q2')), and
      one python flag filter (`score_participant`/`only`).
      The schema five are the real work and WK1's is the model for it: its schema
      asks for `trigger_behavior` precisely because the `expect` rule declared in
      rubric_h2 reads that slot, so the declaration can drive the schema and the
      id disappears. The same argument applies to the barrier and move picks,
      whose slots exist because a declared conjunction or an `expect` consumes
      them.
      TWO CAUTIONS, AND BOTH MUST BE CHECKED AND CLEARED, not merely noted
      (user's direction, 2026-08-28). They are acceptance criteria for this
      subgoal, not caveats to record while closing it:
        (a) A schema change alters what the model is ASKED, so unlike the seven
            scoring conversions it is NOT automatically behaviour-preserving and
            `oc_grid` cannot certify it. Clearing it means comparing every item's
            built schema KEY FOR KEY before and after -- properties, required,
            enums, nesting -- and showing the set is identical for all 26. If any
            item's schema does move, that is a measured change and belongs in the
            sweep, declared, not waved through as a refactor.
        (b) `score_participant`/`only` is a python flag filter, not a rule at all.
            Clearing it means DECIDING: either it is expressible as a declaration,
            or it is moved out of a table about RULES. A contrived declaration
            that exists only to empty the table is worse than the entry.

      CLOSED 2026-08-28, both criteria cleared and neither waived:
        (a) ALL 26 BUILT SCHEMAS IDENTICAL before and after, including the ORDER of
            each `required` list -- the thing a reordered insertion would have
            broken silently, since `required` is a list and my snapshot compared
            content order-insensitively. Snapshot taken BEFORE the first edit.
        (b) DECIDED, not declared: `score_participant`/`only` was never a rule. It
            is `--only Q1 Q4b`, a user-supplied filter, so the CHECK was wrong
            rather than the table incomplete -- it flagged any `item["id"]`
            comparison, including one against runtime data. It now ignores a
            comparison whose right side is a local or parameter rather than a
            module-level constant. Proved narrow: an injected branch against
            BARRIER_PICK_ITEMS still fires, an injected comparison against a local
            does not. A table about rules containing a non-rule teaches its readers
            to skim, which is why this was not just left declared.
      The five "schema shape, not scoring" entries were the interesting ones, and
      that description was true but beside the point: the schema is WHAT THE MODEL
      IS ASKED, so a shape keyed by item id is a rule keyed by item id in a
      different hat. Each now follows the declaration that CONSUMES its answer --
      the barrier readings from the slots this item's `forbid` names, three gate
      keys from `oc_gates`, `trigger_behavior` from the slot its `expect` parses,
      `stimulus_move` from a new `move_pick` attribute -- so a sheet cannot drift
      from the rule that reads it. Answer vocabularies live in
      `rubric_h2.SLOT_OPTIONS`, keyed by SLOT and not by item, because the
      vocabulary belongs to the question.
      `MOVE_PICK_ITEMS` is the one that could NOT be derived: it is ('PR',) while
      `REQUIRED_MOVE` has entries for all four types, so deriving membership from
      REQUIRED_MOVE would have put a new required field on NR, PP and NP -- a
      change to what the model is asked, which criterion (a) forbids. Declared as
      an attribute instead.
      The `build_prompt` hint went the same way: `rubric_h1.READS_UTB_CHOICE`, since
      the underlined-UTB markup is evidence handed to the model and so genuinely
      scoring-relevant. Verified to reach exactly Q1 and Q2.

      ENFORCED, as of 2026-08-28: `enforcement.HANDCODED_BUDGET` is a two-sided
      ratchet, now at 0. Adding an entry fails the audit, and so does landing a
      conversion WITHOUT lowering the budget -- the slack would otherwise leave
      room for a replacement entry to arrive unnoticed. So this subgoal closes by
      the budget reaching 0, not by an argument that the remainder is acceptable.

ORDER, reset 2026-08-29 when the two-sided sweep finished. The 2026-08-28 order
(5 -> 7 -> 8 -> 9 -> the sweep) is spent: all four closed and the sweep has run
twice, so it is replaced rather than amended.

    E14 [done]  ->  E2 [done]  ->  E11  ->  E15
                                     E25  [E12, E13, E19, E26 done]

E14 AND E2 CLOSED 2026-08-29. The block-schema fix landed, all seven blocked
items were re-measured, and the sweep finished at 26 of 26 on both scorers:
python 451/491, OLX 457/491, zero cells where the paths never agree.

THE BASELINE NOW EXISTS, which is what everything below was waiting for. Any
scoring change from here is measured against a recorded six-run figure on BOTH
sides, per item, era-stamped -- so a moved cell can be attributed instead of
argued about.

E15 (`requires`) LAST of the scoring changes: it adds a slot the model is asked,
so only a live app run can judge it, and E14 is the proof that a primitive can
pass every unit test while the app cannot build the sheet. Both of its candidate
sites -- Q6 and Q4c -- also need E2's baseline.

E11 BEFORE E15 because emptying the paper-blind backlog changes what the paper
scorer sees, and doing that after a `requires` conversion would leave two
uncertified changes in one sweep, unable to say which moved a cell. That is the
same reason the old order put 8 before 9.

E26 MOVES NO SCORE -- it is audit machinery -- so it can land at any point
without disturbing a measurement. E12, E13 and E19 were the same and are done. E25 (`keyword` -> `derived`)
does touch a sheet, but it is measurably behaviour-preserving before it is made:
the model and a literal string search agree 240/240, so the conversion changes
who answers the question and not what the answer is.

NAMING, adopted 2026-08-29: audit subgoals are E<n> (equivalence), quality-control
subgoals are Q<n>. Both goals had independently numbered 1..N and six numbers
collided, so "subgoal 14" meant two different things depending on which goal the
reader had in mind. Every cross-reference in this file is now prefixed.

- [x] E5. **The enforcement audit cannot see a rule written as guidance prose.**
      MOVED here from quality control, where it was subgoal E15: it is an
      equivalence-enforcement defect, not an item's scoring problem, and it
      sits directly beside subgoal E3. Both are the same failure in different
      clothing -- a rule the audit cannot compare because it is not declared.
      Subgoal 3 is rules hand-written in Python; this is rules written in
      PROSE. Found closing quality-control subgoal E5. The audit compares PRIMITIVES between the two
      sides -- counts, equals, cover, onlyif, requires, expect, forbid, derived --
      so a rule that changes scoring but is expressed in guidance text is invisible
      to it in both directions. Q4b/p12 is the demonstrated case: the olx refuses
      an entry the python credits, six runs to six, and nothing flags it.
      SCOPED, 2026-08-28, at 0 model calls. The scoping was going to be a census
      of prose bullets; it turned into a MEASUREMENT, which is better, because the
      hazard surface and the actual damage are different sizes.

      THE HAZARD SURFACE: 70 of 150 authored prose blocks carry directive scoring
      language (REJECT / no credit / only when / takes the whole), concentrated in
      the OC items -- DAY1, DAY2, WK2 at 8 each, WK1 at 7. That is an upper bound
      from a deliberately loose regex, not a count of rules.

      THE MEASURED DAMAGE, from artifacts already on disk -- paper_mini_v8
      (score.py, 3 runs) against the olx-prompt path, 520 cells present on both:
        18 cells NEVER agree in both of two independent comparisons ("robust")
        17 more diverge in one comparison and not the other ("era-only"): Q6 7,
           Q3 4, Q4a 2, Q4b 2, 2a 1, Q5 1. These are NOT attributable -- the two
           comparisons span different prompt versions, so version is confounded
           with path, and only an era-matched two-sided sweep separates them.
           That is subgoal E2, which is another reason it goes last.
      Of the 18 robust: 15 are 1c and 1 is Q4a, both DECLARED. Exactly TWO are
      undeclared, and both are stable in 3 of 3 runs rather than noise:

        1a/p6   paper 0.0 vs olx 6.0-8.0. The paper scorer refuses the WHOLE item
                -- "-8 pts: did not discuss data for each week" -- on a 512-char
                answer with no error. CAUSE CONFIRMED: five `1a:*` SLOT_NOTES
                entries, 129 to 494 chars of judging text each, reach the olx
                prompt and NOT the python's. Verified fragment by fragment.
        Q4b/p4  paper 2.0 vs olx 3.5, and GOLD IS 2.0. The paper path charges what
                the graders charged and the olx path does not. The rule doing the
                refusing is the guidance-prose REJECT test.

      SO THE BLINDNESS HAS TWO CHANNELS, not one. This subgoal was written about
      guidance prose; SLOT_NOTES is the other, and it is the one with a measured
      price tag -- 8 points on 1a/p6, every run. It already has a declared
      18-entry backlog in `check_slot_rules_reach_both_prompts` whose own comment
      says these "reach the olx and python and silently leave the paper scorer
      behind". 1a/p6 is that sentence with a number attached.

      WHAT CAN AND CANNOT BE BUILT. The prose channel cannot be closed by any text
      comparison: both sides are given the same guidance verbatim -- the prompt
      audit already proves it, 0 undeclared gaps -- so there is no textual
      difference to find. Only running both paths over the same cell exposes it,
      which means the instrument is the sweep plus a cell-level cross-path
      comparison, not a static check. The SLOT_NOTES channel is the opposite: it
      IS statically visible, already checked, and merely unfinished.
      PLAN, in this order:
        [x] (a) DONE. `cross_path.py` compares two scoring paths CELL BY CELL --
            a different question from `head_to_head.py`, which asks how well each
            side matches gold. It normalises all three artifact shapes (score.py's
            `participant_*.json`, agreement.py's and agreement_app.py's
            `.runs.json`, the last carrying grader.score as a FRACTION of
            sheet_max that has to be multiplied back up), reports cells whose
            score sets are disjoint, marks each item declared or not, and with
            `--slots` names the slots whose majority verdict differs.
            That last part is what makes it a diagnosis rather than a symptom: it
            localises 1a/p6 to `distinguishes_periods` -- which IS one of the five
            olx-only `1a:*` SLOT_NOTES entries -- and Q4b/p4 to
            `behavior_1`/`behavior_2`, the guidance-prose REJECT test. The tool
            found the responsible rule in both cases without being told about
            either.
            AND THE ERA GAP IS CLOSED AT THE SOURCE, which was the right place: it
            was going to ship with a docstring disclaiming that era could not be
            checked, because no artifact recorded the prompt it ran against.
            `measured.era_stamp` now gives the git commit, a dirty-tree flag, and
            each item's prompt and scorer fingerprints from the same functions the
            ledger uses, and all THREE writers stamp it. cross_path compares the
            stamps per item and WITHHOLDS any item whose prompt differed, since
            such a cell cannot speak about the paths; where a side predates
            stamping it says so rather than implying it checked.
            Guarded by `enforcement.check_artifacts_record_their_era`, which reads
            the writers' source rather than the artifacts -- the corpus is full of
            legitimately unstamped older runs, and flagging those would be
            thousands of findings about the past instead of one about the code.
            Both halves proved to fire.
            Two bugs were caught by testing rather than by reading: the era check
            silently did nothing because the loaders returned a flattened item map
            while the comparison expected the full stamp, and `declared_items`
            searched each divergence entry's PROSE instead of its `items` field --
            a false `declared` hides precisely what this tool exists to surface.
        [x] (b) DONE. `SLOT_RULE_BACKLOG` is hoisted to module scope -- so the
            ratchet and the existing check read ONE list, verified by removing an
            entry and watching the existing check flag that note -- and
            `SLOT_RULE_BACKLOG_BUDGET` ratchets it two-sidedly at 17, not 18: the
            count was already one lower, because `consequence_asserted` left the
            list on 2026-08-28 by being FIXED. Both directions proved to fire. The
            comment now records which entries to migrate first and why: the five
            `1a:*` notes are the only group with a measured price, 8 points on
            1a/p6 in 3 of 3 runs.
            The list is 17 and the sibling `CORPUS_QUOTE_BACKLOG` is empty, so
            every declared backlog in the audit now has a ceiling that can only
            fall.
        [x] (c) MIGRATED, 2026-08-28. All five `1a:*` notes moved VERBATIM into
            rubric_h3's per-component `rule` fields. The olx prompt did not move --
            byte-identical across all 23, because the olx checklist looks up `rule`
            BEFORE SLOT_NOTES and finds the same string -- so every recorded olx
            number stands and 1a did not go stale. Only the python gained text, which
            is the entire point.
            THE python NOW RENDERS SHARED RULES AS THE OLX DOES: `rule` REPLACES
            `desc` rather than being appended to it. The olx has always done that
            (`rule or SLOT_NOTES or desc`), so the one field written to be read by
            both scorers was being rendered differently by each -- and since these
            rules are written to continue from the olx's `— `, appending them after
            a desc produced "Discusses the baseline week is the BEFORE state
            given". No audit compared the two RENDERINGS, because both sides
            carried the text and the audit asks only whether it is carried. Blast
            radius is the only three items with rules: 1a, Q4b, Q6, whose python
            prompts change (the olx's do not).
            The two measured findings in those notes' comments -- the partial-week
            failure the guidance did not anticipate, and the reverted experiment
            where p6 swung 8.0/0.0/6.0 -- moved into rubric_h3 beside the rules
            they describe. Deleting them would have destroyed the record.
            Backlog 17 -> 13, budget lowered with it, so the ratchet stays clean.
            The text is still leakage-scanned: leakage.py reads rubric `rule`
            strings as well as SLOT_NOTES, and the gate passes.
            NOT YET MEASURED, deliberately. This should fix 1a/p6's 8-point gap and
            it may move other 1a cells; three items' python prompts changed. The sweep
            measures it -- predicting the direction here would only make the result
            harder to read honestly.
        [x] (d) DONE, and narrower than planned, which is the finding. The plan
            said "a registry of scoring-relevant prose rules", and the first count
            put that at 70 of 150 blocks -- unmanageable, and mostly ITEM-level
            guidance that steers every slot at once.
            The tractable surface is SLOT-level: a per-slot `rule` deciding a
            verdict that nothing computes. There are NINE, and none is backed by a
            computed primitive -- Q4b's two INSTEAD-OF tests, Q6's two "X, so I Y"
            readings, and 1a's five. Both measured divergences live in that nine.
            `enforcement.slot_basis(item)` COMPUTES what decides each slot --
            computed:equals/forbid/expect/derived, counted, prose+rule, prose --
            rather than listing it, because a hand table would drift from the rubric
            and drift is what this goal is about. `PROSE_ONLY_SLOTS` then declares
            the nine WITH REASONS, on a ratchet at 9, and
            `check_prose_only_slots_are_declared` fails three ways: an undeclared
            prose-only rule appearing, a declaration that stopped qualifying, and
            the count leaving budget. All three proved to fire.
            What the declaration buys, given no static check can compare prose:
            `cross_path.py --slots` now annotates every divergent slot with its
            basis, so the sweep's table reads
              slot `behavior_1`: paper not_active / python met  [prose+rule, declared]
            A divergence on a COMPUTED slot means the two sides ran different
            arithmetic -- one right answer, a bug. On a declared prose slot it means
            they read the same instruction and landed differently: known hazard, no
            static fix. On an UNDECLARED prose slot it means the surface grew and
            nobody decided. Three different readings that used to look identical.

      WHAT THE REGISTRY IS FOR, since a list that only exists is inert. Three
      jobs, all live:
        1. IT GATES AUTHORING. A new per-slot rule that nothing computes fails the
           audit until someone either expresses it as a primitive -- which the
           enforcement audit can then compare between the two scorers -- or
           declares why it cannot be one. That forces subgoal E3's choice at the
           moment the rule is written, instead of seven conversions later.
        2. IT IS A WORK LIST, and ENFORCED AS ONE (user's direction, 2026-08-28):
           any entry marked CONVERTIBLE, in whole or in part, becomes a SUBGOAL
           here, not a note in a table.
           `check_convertible_prose_rules_have_subgoals` fails the audit while a
           CONVERTIBLE entry has no subgoal naming it, so the two cannot drift
           apart -- a work list whose items live only in a comment is a list
           nobody works. The match is deliberately loose: it checks the work was
           written down, not how a subgoal is phrased, because a stricter match
           would fail on the first reworded heading and teach people to route
           around it.
           Each reason must argue CONVERTIBILITY, not describe the rule; the first
           nine reasons described, and were rewritten. Two are marked CONVERTIBLE
           IN PART -- Q4b's `behavior_1`/`behavior_2`, whose sixth test (an entry
           naming the same THING as one of the student's own 4a antecedents) is
           `forbid`-shaped, two answers compared by referent. Those are also the
           demonstrated divergence, so they are first in line, and they are now
           subgoal E9.
           Seven argue NOT CONVERTIBLE and say why: Q6's "does it state HOW" and
           1a's arc-not-label coverage have no operands to compare, and 1a's weeks
           are already exempted from `counts` in COUNTABLE_EXEMPT because named
           weeks are not interchangeable.
        3. IT MAKES A DIVERGENCE ATTRIBUTABLE, which is the only thing that reads
           the sweep for us: prose-and-declared, prose-and-new, and
           different-arithmetic stop looking alike.
      UNLIKE HANDCODED_BUDGET THIS DOES NOT TARGET ZERO. The honest end state is
      that every remaining entry argues why it cannot be a primitive -- which is
      now true of all nine.

      SUBGOAL 5 IS COMPLETE, (a) through (d). The prose channel cannot be closed --
      both sides get the same text verbatim -- so it is instead KNOWN, BOUNDED and
      ATTRIBUTABLE, with the sweep as its only real detector. The next conversion
      it points at, Q4b's pair, is a scoring change and belongs in the sweep.
## ACTIVE — quality control on the remaining items

  MADE ACTIVE 2026-09-01, when the equivalence goal above was parked. Nineteen
  subgoals are open under it, and the pooled re-evaluation of the same day
  changed what most of them are FOR -- read the pooling note before working any
  of them, because a cell that looked unstable at six runs a side is usually
  settled at twelve, and the surviving evidence is disproportionately "we stably
  disagree with gold" rather than "we are noisy".
  WHERE THE WORK IS, in the order the evidence supports:
    Q34  six cells we deduct in EVERY one of twelve runs against a row gold
         passed in silence. The only false-positive test the corpus offers, and
         two readouts already say our refusals are defensible on the rubric as
         written -- which makes it a rubric-versus-gold decision.
    Q19, Q20  the slot-level findings, untouched by pooling because they compare
         WHICH slots gold charges against which we fail, not totals.
    Q2, Q9, Q10, Q14, Q16, Q17, Q29, Q30  per-item questions, each now one or
         two stable cells rather than a mix of noise and disagreement.
    Q24, Q33  the two ceiling-shaped entries: Q4a's opposite-direction pair, and
         the paper scorer's four cells on the rubric prompt.
  THREE PROMPT CHANGES WERE MEASURED ON 2026-09-01 AND NONE SURVIVED -- two
  reverted, one refuted before it was written. Read Q18's and Q24's entries for
  what went wrong before proposing a fourth: state the revert rule and name the
  controls BEFORE the sweep, not after.


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

- [x] Q31. **SILENT FULL MARKS: nine cells where gold wrote nothing and we deduct.**
      SPLIT INTO Q34 AND Q35 ON 2026-09-01, and this entry is superseded by them.
      Q34 holds the six cells we get wrong in every one of twelve pooled runs --
      the false-positive test -- and Q35 the five we sometimes get right, which
      are about variance. The split is measurable rather than a judgement, and
      keeping them together is what made the "nine cells" figure mean less than
      it looked. CLOSE THIS ONCE THE TWO ARE BEING WORKED; it is left open only
      so nothing is orphaned in between.
      SPLIT INTO Q34 AND Q35 ON 2026-09-01, and this entry is superseded by them.
      Q34 holds the six cells we get wrong in every one of twelve pooled runs --
      the false-positive test -- and Q35 the five we sometimes get right, which
      are about variance. The split is measurable rather than a judgement, and
      keeping them together is what made the "nine cells" figure mean less than
      it looked. CLOSE THIS ONCE THE TWO ARE BEING WORKED; it is left open only
      so nothing is orphaned in between.
      POOLED, 2026-09-01, AND THE LIST SPLITS IN TWO -- which is the useful part,
      because only one half is a false-positive test. Eleven cells are wrong at
      the pooled median, and their spreads separate them:
        STABLE, every one of twelve runs deducting where gold said nothing:
          1a/p11 6.0    DAY1/p1 0.0    NR/p4 2.0    NR/p20 0.0    Q4b/p12 3.5
        UNSTABLE, deducting only sometimes:
          D2/p3, DAY2/p8, PR/p15, Q2/p20, Q4a/p19, Q4b/p13
      THE FIVE STABLE CELLS ARE THE TEST. A cell we deduct on 12 of 12 runs,
      against a row the graders passed in silence, is a claim about our
      strictness that no amount of sampling explains. The six unstable ones are
      claims about variance and belong with the instability subgoals; counting
      them here inflates the false-positive rate with cells that are sometimes
      right.
      Q1/p17 HAS LEFT THIS LIST: it is right when pooled. Its diagnosis survives
      in Q16 as a slot-level observation -- the `utb_stated` rule's "what they
      want instead" branch going unapplied -- but it is no longer a cell we score
      wrong.
      Filed 2026-08-31, and it is the part of the corpus E30's accounting cannot
      reach BY CONSTRUCTION. That accounting compares our failing slots against
      the slots gold's comment itemises; where the grader wrote no comment there
      is nothing to compare, and only the total says anything is wrong.
      THIRTY-FOUR cells are wrong at the total. Twenty are declared in the slot
      and code tables. TEN have no gold comment at all, and NINE of those ten run
      the SAME WAY -- gold awarded FULL MARKS, silently, and we deducted:
          1a/p11    gold 8.0 = max     ours 6.0
          DAY1/p1   gold 4.0 = max     ours 0.0
          NR/p4     gold 4.0 = max     ours 2.0
          NR/p20    gold 4.0 = max     ours 0.0
          Q1/p17    gold 5.0 = max     ours 3.0
          Q2/p20    gold 5.0 = max     ours 4.0
          Q4a/p19   gold 5.0 = max     ours 3.0
          Q4b/p12   gold 5.0 = max     ours 3.5
          Q4b/p13   gold 5.0 = max     ours 3.5
      A COMMENT-LESS FULL-MARKS ROW IS A JUDGEMENT, not an absence. The graders
      itemise when they deduct -- 109 rows do -- so silence plus full marks means
      "nothing to say about this one". Nine cells where the grader had nothing to
      say and we found a defect is a claim about our strictness, and it is the
      MIRROR of everything else in the accounting: the twenty declared cells are
      almost all us being lenient.
      THAT MAKES THIS THE BEST AVAILABLE TEST OF OUR FALSE-POSITIVE RATE. Every
      other subgoal here asks why we miss what gold charges; this asks what we
      charge that gold does not, on cells gold considered unremarkable.
      DAY1/p1 IS ALREADY Q27 and is the extreme case -- 0.0 against a silent 4.0,
      every slot answered `absent` on a response that is present and readable.
      Read the other eight against it: if they share DAY1/p1's shape, this is one
      finding and Q27 is its worked example.
      2a/p16 IS THE ONE EXCEPTION and belongs to Q2, not here: gold docked 2 with
      no comment and we credit, so it is the item's usual over-credit rather than
      this pattern.
      DO NOT START FROM THE RUBRIC. A silent row gives no phrase to argue with, so
      the only evidence is the response itself -- read the boxes for two or three
      of these before forming any theory, per QUALITY_CONTROL.md and
      memory/fixture-defects-found-by-readout.md.

      == 2026-09-01: THE BOXES WERE READ, AND THE ANSWER IS NO ==
      THE LIST IS TWELVE NOW, NOT NINE, re-derived from the current ledger rather
      than carried forward: D2/p3, DAY2/p8 and PR/p15 join it, and Q1/p17 is now
      correct on olx while still wrong on python. DAY2/p8 and PR/p15 are also
      Q32's unstable cells, so they are in this list by median rather than by a
      settled judgement.
      DAY1/p1 DOES NOT SHARE ITS SHAPE WITH THE OTHERS, which is what this entry
      asked. It is the ONLY broad collapse. Classified by which slots carry the
      loss:
          DAY1/p1   gate + four more: contingent, follows_behavior,
                    matches_chosen_type, consequence_asserted -- UNIQUE
          NR/p20    ONE GATE, `you_arrange_it`, zeroing four points
          1a/p11    one slot, week_1            NR/p4    one slot, demonstrates_type
          Q1/p17    one slot, utb_stated        Q4a/p19  one slot, antecedent_1
          Q4b/p12   one slot, behavior_2        D2/p3    two slots
      So Q27 is an OUTLIER, not this pattern's worked example, and the eight
      single-slot cells are the pattern.
      AND EVERY ONE OF THOSE SLOTS IS ALREADY OWNED: you_arrange_it and
      demonstrates_type by Q21, utb_stated by Q16, antecedent_1 by Q24,
      behavior_2 by Q18. That makes this subgoal a LENS rather than a defect
      class -- it cross-cuts the slot subgoals instead of naming a mechanism of
      its own, and no fix belongs here.
      THE FALSE-POSITIVE TEST RETURNS: OUR REFUSALS ARE DEFENSIBLE. Reading the
      two extremes out, per this entry's own instruction:
          DAY1/p1 "{{corpus:DAY1/p1:day1:0:72:sha=b56fbe949d26:shape=S10-20,S12-0a202020202020202020202020202020202020}}" No behaviour is named, no contingency is stated,
                  and the reward is the REMOVAL of an aversive while the student
                  chose Positive Reinforcement. Our six `absent`s are arguable
                  on every one of those grounds.
          NR/p20  "{{corpus:NR/p20:nr:0:97:sha=4c943261f783:shape=S14-0a202020202020202020202020202020202020}}" Everything is `met`
                  except `you_arrange_it`, and not feeling tired is a natural
                  consequence the student does not arrange -- which is what that
                  gate asks.
      So this is not a harshness defect. It is the same finding B_NOT_ACTIVE
      records for Q4b: GOLD IS MORE LENIENT THAN THE WRITTEN RUBRIC, on cells it
      passed without comment. `measured.py --refusals` says the same thing from
      the other direction -- across Q4a, Q4b and Q4c not one refusal is
      contradicted by a gold comment, because these rows have no comment.
      WHAT THIS SUBGOAL IS FOR, RESTATED. Not a fix. It is the corpus's answer to
      "how often do we charge what the graders would not", and the answer is
      twelve cells, eight of them one slot each, every slot already under a
      subgoal, with the refusals defensible on the rubric as written. That is a
      LOW false-positive rate and it is the number to quote when a subgoal
      proposes loosening a rule to chase gold.
      HOW STABLE EACH SHAPE IS, checked over all twelve runs a cell has rather
      than the first -- and the check corrected a claim made here an hour before
      it was run, which had asserted the single-slot cells were all stable:
          1a/p11   STABLE 12/12  week_1
          NR/p20   STABLE 12/12  you_arrange_it
          Q4b/p12  STABLE 12/12  behavior_2
          Q4a/p19        11/12   antecedent_1
          D2/p3           7/12   add_or_remove
          NR/p4           5/12   demonstrates_type
          Q1/p17          7/12   (NO unmet scored slot at all)
      So THREE are fully stable, one nearly so, and three are not -- NR/p4 in
      particular holds its shape in fewer than half its runs, and any reading of
      it as "one slot" is a reading of a coin flip.
      Q1/p17 IS THE ODD ONE AND IS NOT EXPLAINED HERE. In 7 of 12 runs NO scored
      slot is unmet, and the cell still scores 3.0 against a gold of 5.0. A cell
      that loses two points with every scored check passing is subgoal Q20's
      shape, not this one's, and it should be read there -- but Q20's mechanism
      is "we credit a slot gold charged", which needs a gold comment, and this
      row has none. Neither entry currently accounts for it.

      CLOSED 2026-09-01, superseded by Q34 and Q35. The pattern it found is real
      and is not retired -- it is split, on a line pooling made measurable:
      whether we get the cell wrong EVERY run or only sometimes. Q34 carries the
      six that are never right, which is the false-positive test this entry was
      opened to be; Q35 carries the five that sometimes are, which are about
      variance and were quietly inflating the rate.
      ITS ONE LOOSE CELL WAS PLACED FIRST. 2a/p16 is named here as belonging to
      subgoal Q2, and nothing had acted on that, so closing without moving it
      would have orphaned it. It is now in Q2 with its evidence.
      WHAT IT GOT RIGHT, worth keeping: that a comment-less full-marks row is a
      JUDGEMENT rather than an absence, and that reading our refusals against
      those rows is the only false-positive test the corpus offers. What it got
      wrong was counting cells that are sometimes right alongside cells that are
      never right, which made "nine cells" mean less than it looked.


- [ ] Q36. **1a's week-presence rule: we credit a baseline week that is not there
      (1a/p6), and the label-versus-data question underneath it.**
      Filed 2026-09-02, split out of Q34 when 1a/p11 was corrected and its
      counterpart turned out to have no real owner.
      THE CELL: gold charges 1a/p6 "-2 pts: did not have a sentece pertaining to
      the baseline week", landing on 6.00. We score 8.00 in 11 of 12 pooled runs
      -- one olx run reaches 6.0, so the rule CAN fire and mostly does not. GOLD
      IS RIGHT HERE, checked by reading the response: the overview covers "the
      first week", "as time went on" and "the last week", and never the
      pre-intervention baseline. Its "only 40 minutes" matches nothing in the
      baseline data 0,30,0,0,30,0,0. This is our error, not a gold divergence.
      WHY IT NEEDED A HOME AT ALL, which is the part worth remembering -- and
      the first version of this paragraph got the diagnosis wrong, so both are
      recorded. It said every mention of 1a/p6 was about the PAPER scorer, and
      that a side-aware ownership rule was the fix. Neither held. The paper-side
      mentions are all in CLOSED subgoals (E5, E11), which never counted as
      owners at all. The actual claim on the cell was Q17's, whose title is "Q2:
      `wgb_is_counterpart`..." and whose body names 1a/p6 purely as HISTORY: "as
      1a's five were on 2026-08-28, which cost 1a/p6 the whole item before the
      migration". So an 11-of-12-run over-credit on the pooled OLX prompt read as
      owned because a subgoal about a different item mentioned it in an aside
      about a past migration. FIXED 2026-09-02 in
      `measured._live_subgoal_owners`: a title that names its own items can no
      longer own another item's cell, while corpus-wide subgoals that name no
      item -- Q19, Q20 -- keep their reach. It found one further cell nobody was
      chasing, DAY2/p7, now listed in Q20.
      THE QUESTION THAT DECIDES BOTH CELLS: does describing a week's numbers
      under the WRONG LABEL count as discussing that week? 1a/p11 turns on the
      same question from the other side. Its gold is now corrected 8.0 -> 6.0
      because one week is undiscussed on either reading, but WHICH week depends on
      the answer -- we fail `week_1` in all twelve runs, which is the label
      reading, while the data reading makes it `baseline_week`. The correction
      settled the score, not the slot. DO NOT cite 1a/p11 as evidence that
      `week_1` is judged correctly.
      ORDER OF WORK: read the item's authored wording first and decide whether
      presence means a labelled sentence or the numbers being described at all.
      Then check which of the two our per-week check is actually reading. Only
      then consider changing it -- and note the change would move p6 and could
      move p11's slot, so measure both.
      DO NOT REACH FOR Q19 HERE. Q19 is the later-box gradient, where gold
      charges MORE than we do; both of these run the other way.

- [x] Q34. **NEVER RIGHT on a row gold passed in silence: six cells, and the false-positive test.**
      Split from Q31 on 2026-09-01, once pooling made the distinction measurable.
      These are cells where gold awarded FULL MARKS and wrote nothing, and we
      deduct in every one of twelve pooled runs:
          1a/p11   gold 8    ours 6.0     every run
          DAY1/p1  gold 4    ours 0.0     every run
          NR/p4    gold 4    ours 2.0     every run
          NR/p20   gold 4    ours 0.0     every run
          Q4b/p12  gold 5    ours 3.5     every run
          Q4a/p19  gold 5    ours 3.0 x11, 1.0 x1 -- it VARIES and is never right
      == 2026-09-02: FOUR OF THE SIX ARE NOW CORRECTED GOLD, TWO SURVIVE. ==
      The comparator test in `measured.silent_full_marks_we_refuse`, plus a
      slot-level read of each whole item, decided them one at a time:
          NR/p4    CORRECTED 4 -> 2. Comparator p9, same item, same structural
                   error, charged "-2 pts: This is an example of PP" to 2.00.
          Q4a/p19  CORRECTED 5 -> 3. The student's own Q1 puts box 1 on the
                   consequence side; gold charges box 1 at -2 on p4 and p6 and
                   we agree with gold exactly on both.
          DAY1/p1  CORRECTED 4 -> 0. Contradicts the student's own definition of
                   the type they chose; gold charged 7 DAY1 cells and we agree
                   on all 7. See subgoal Q27, whose ordered questions this
                   answered.
          NR/p20   CORRECTED 4 -> 0. Comparator p1, nearly the same sentence,
                   charged to 0.00 with the outside-stimulus rule written out.
          1a/p11   NOT CORRECTED, and the reason is the useful one. Its only
                   comparator is p6, which is SIMULTANEOUSLY one of our own
                   misses -- gold charged p6 -2 for a missing baseline week and
                   we credit it 8.00. Both sides miss a week once each on this
                   item, so there is no outlier pattern, only mutual
                   inconsistency. Q34's own complication still stands too.
          Q4b/p12  NOT CORRECTED, and the test DEFENDS the existing declaration.
                   Gold charged behavior_2 six times, but on a different defect
                   class: p5's box 2 is a circumstance ("often not available"),
                   p6's a resulting state ("walk around with stiff muscles").
                   p12's is an OMISSION ("I skip adding fruits"), which is
                   exactly what B_NOT_ACTIVE declares. GOLD_DIVERGENCES stays.
      WHAT MAKES THIS ENTRY'S QUESTION HARDER THAN IT LOOKED, and the number to
      quote before any future correction: the readout only examines cells where
      gold is silent AND we refuse, so every candidate it can produce would gain
      us a cell. That fact discriminates nothing. The measured counterweight is
      that 16 cells have gold charging where we credit more, against 15 where we
      score below gold -- disagreement is very nearly SYMMETRIC. No general
      claim that the raters were careless is available; only same-item
      comparators plus our agreement with gold on those comparators.
      == CLOSED 2026-09-02. FIVE OF THE SIX CORRECTED, THE SIXTH DECLARED. ==
      1a/p11 was corrected too, after the reasoning above was revisited: the
      objection recorded there -- that its only comparator is simultaneously one
      of our own misses -- was made from a summary rather than from the response,
      and reading it out showed one week undiscussed on EITHER reading, so 8.00 is
      unsupportable independently of the comparator. See
      handouts.CORRECTED_GOLD[("1a", 11)].
      That leaves only Q4b/p12, which is a DECLARED divergence under
      B_NOT_ACTIVE and which this entry's own comparator test defends rather than
      overturns -- gold's six behavior_2 charges are a different defect class from
      p12's omission. A declared miss needs no QC subgoal, so nothing is orphaned
      by closing.
      WHAT THIS ENTRY ESTABLISHED, and the reason to read it before proposing any
      future gold correction: a silent full-marks row can be a grader not
      engaging, but the readout that finds such rows can only ever produce
      candidates that would gain us a cell, so that fact discriminates nothing.
      The corpus-wide counterweight is 16 cells where gold charged and we credit
      more against 15 the other way. Only same-item comparators, plus our
      agreement with gold ON those comparators, ever carried a case here.
      SUCCESSOR: subgoal Q36 owns 1a/p6 and the label-versus-data question that
      1a/p11's slot still turns on.
      Q4a/p19 IS IN THIS LIST BY A CORRECTION MADE WHEN IT WAS DRAWN UP. It moved
      here from the unstable half because "unstable" has to mean SOMETIMES RIGHT,
      not merely varying: both of its values miss gold, and the run at 1.0 is
      further from gold, not nearer. A cell that varies without ever reaching
      gold is a stable false positive wearing noise.
      THIS IS THE FALSE-POSITIVE TEST, and the only half of old Q31 that is one.
      A deduction we make EVERY time, against a row the graders passed without
      comment, is a claim about our strictness that no amount of sampling
      explains. The other half is subgoal Q35 and counting the two together
      inflated the rate with cells that are sometimes right.
      TWO OF THE SIX HAVE BEEN READ OUT, and both times our refusal was
      defensible on the rubric AS WRITTEN:
          DAY1/p1  "{{corpus:DAY1/p1:day1:0:72:sha=b56fbe949d26:shape=S10-20,S12-0a20202020202020202020202020202020202020}}" No behaviour named, no contingency stated, and
                   the reward is the REMOVAL of an aversive while the student
                   chose Positive Reinforcement.
          NR/p20   everything `met` except `you_arrange_it`, and not feeling
                   tired is a natural consequence the student does not arrange,
                   which is what that gate asks.
      SO THE QUESTION IS NOT "ARE WE TOO HARSH". It is whether a silent
      full-marks row is a JUDGEMENT to defer to or a grader not engaging, and the
      evidence so far says gold is more lenient than the written rubric -- the
      same finding B_NOT_ACTIVE records for Q4b/p12, which is one of these six.
      That makes it a rubric-versus-gold decision, not a code fix, and it is the
      number to quote when a subgoal proposes loosening a rule to chase gold.
      OVERLAPS TO RESPECT, so this does not become a second name for existing
      work: DAY1/p1 is subgoal Q27's worked example, Q4b/p12 is a DECLARED
      divergence under B_NOT_ACTIVE, Q4a/p19 is one of Q24's two ceiling cells,
      and NR/p4 and NR/p20 turn on slots subgoal Q21 owns. What this entry adds
      is the ACROSS-ITEM pattern none of them can see alone.
      == 2026-09-01: BOTH WERE READ. ALL SIX SHARE THE SHAPE. ==
      1a/p11  gold 8.0 silent, we score 6.0 on `week_1`. The response covers the
              baseline, week two and week three and never names week one. Our
              evidence says exactly that. NOTE THE COMPLICATION: the student's
              "{{corpus:1a/p11:response:203:232:sha=40fceadac0f5}} time" matches WEEK 1's data
              (60, 60), not the baseline's (30, 30, 30), so they may have
              described week one while calling it "before I started". On the rule
              as written -- discuss the data for each week -- the refusal stands.
      NR/p4   gold 4.0 silent, we score 2.0 on `demonstrates_type`. "{{corpus:NR/p4:nr:0:65:sha=71e4f739c568:shape=S2-0a2020202020202020202020202020}}" That is
              REMOVING SOMETHING DESIRABLE to decrease an unwanted behaviour,
              which is negative PUNISHMENT. The item asks for negative
              reinforcement. This is the strongest of the six: the example does
              not demonstrate the type the question names, and no reading of the
              rubric credits it.
      SO THE ANSWER TO THIS ENTRY'S QUESTION IS YES -- all six are cells where
      our refusal is defensible on the rubric AS WRITTEN, and gold passed the row
      without comment. DAY1/p1 names no behaviour and no contingency and rewards
      by removing an aversive while the student chose Positive Reinforcement;
      NR/p20 fails only `you_arrange_it` on a consequence nobody arranges;
      Q4b/p12 is a declared not-doing divergence; Q4a/p19's box 1 FOLLOWS the UTB
      rather than preceding it.
      AND THE PROMPT ALREADY INSTRUCTS LENIENCY, which is what makes this a
      finding rather than a complaint. Q4a's own guidance reads "ACCEPT
      generously when the example precedes the UTB and a reader can see how it
      leads there", and we still refuse p19 -- correctly, since its example does
      not precede the UTB. So the gap is NOT that our prompts lack a generosity
      instruction. Gold's silence encodes a threshold below even the generous
      reading the rubric asks for.
      WHAT FOLLOWS, and it is a decision rather than a fix. Three options, and
      the first is the default:
      (a) DEFER TO THE RUBRIC. Accept that these six are cells where the graders
          were more lenient than the course's own written rules, record them as
          such, and stop counting them against the scorers. This costs nothing
          and is honest, but it means six cells are permanently "wrong" against
          gold.
      (b) DECLARE THEM, cell by cell, in handouts.GOLD_DIVERGENCES with the
          reason -- which is what Q4b/p12 already has under B_NOT_ACTIVE. The
          machinery exists and the bar is a stated reason, not a number.
      (c) CORRECT THE GOLD where a row contradicts the graders' own decisions
          elsewhere in the same item. NR/p4 is the only candidate: the response
          demonstrates the wrong operant type outright, which is not a matter of
          strictness. The others are judgement calls where gold is simply more
          generous, and CORRECTED_GOLD is not for disagreeing with a judgement.
      DO NOT LOOSEN A RULE TO CLOSE THIS. Every one of the six is a refusal the
      written rubric supports, and three prompt changes measured on 2026-09-01
      failed for want of exactly that discipline.
      NEXT: pick between (a), (b) and (c) -- it is a course-owner's decision as
      much as a scorer's, so ask rather than assume. If (b) or (c), NR/p4 is the
      one to do first, because its case does not rest on a judgement.

- [ ] Q35. **SOMETIMES RIGHT on a row gold passed in silence: five cells of variance, not strictness.**
      Split from Q31 on 2026-09-01. Same population -- gold gave full marks and
      wrote nothing -- but here we reach gold in at least one of twelve pooled
      runs, so the cell is evidence about VARIANCE and not about how strict we
      are:
          D2/p3    gold 2   0.0 x4, 1.0 x7, 2.0 x1     right 1 of 12
          DAY2/p8  gold 4   0.0 x7, 4.0 x5             right 5 of 12
          PR/p15   gold 4   0.0 x1, 2.0 x6, 4.0 x5     right 5 of 12
          Q2/p20   gold 5   4.0 x11, 5.0 x1            right 1 of 12
          Q4b/p13  gold 5   3.5 x8, 5.0 x4             right 4 of 12
      WHY THIS IS A SEPARATE ENTRY AND NOT A FOOTNOTE. Old Q31 counted these
      beside the always-wrong cells and called the total a false-positive rate.
      It is not one: a cell that reaches gold in 5 of 12 runs says our rule can
      produce the right answer and does not always, which is a different defect
      with a different fix. Keeping them apart is what makes subgoal Q34's number
      mean something.
      EACH BELONGS TO ITS ITEM'S INSTABILITY WORK, and this entry's job is to
      route them rather than to hold them: DAY2/p8 flips on `cadence_is_daily`,
      which is subgoal Q22's four-point gate; PR/p15 flips on
      `targets_goal_behavior`, which subgoal Q21 profiles at its worst precision;
      Q4b/p13 is subgoal Q18's live not-doing cell. D2/p3 and Q2/p20 have no
      instability subgoal yet.
      DO NOT TREAT THE SILENCE AS THE FINDING HERE. Gold saying nothing matters
      for Q34, where we disagree every time; for these five the disagreement is
      not consistent enough for gold's silence to be the interesting variable.
      NEXT: attach D2/p3 and Q2/p20 to an instability owner or say why they need
      one of their own, then let Q22, Q21 and Q18 carry the rest.

- [ ] Q33. **Q4a on the PAPER scorer: four cells the other two engines get right.**
      Filed 2026-09-01, on the first paper numbers the ledger has ever held.
      Q4a paper 15/20 against python 18/20 and olx 17/20, six runs each, ALL
      THREE ON GPT-5-MINI -- so this is the rubric prompt against the OLX sheet,
      not a model difference. Six Q4a cells are wrong on paper and FOUR of them
      are paper-only:
          cell  gold   olx   python   paper
          p2      5     5.0    5.0     3.0    under-credits 2
          p6      3     3.0    3.0     5.0    over-credits 2
          p18     3     3.0    3.0     5.0    over-credits 2
          p20     1     1.0    1.0     5.0    over-credits 4 -- the whole item
      Named for the ownership check, which matches `item/pN` and not a bare
      `pN` in a table: Q4a/p2, Q4a/p6, Q4a/p18 and Q4a/p20 are the four.
      (Q4a/p14 and Q4a/p19 are wrong on all three sides and belong to Q19
      and Q31.)
      THE SHAPE IS THREE OVER-CREDITS AND ONE UNDER-CREDIT, and p20 is the one to
      read first: gold gives it 1 of 5 and the paper scorer gives it full marks,
      while both OLX-prompt engines score it 1.0 exactly. A four-point miss on a
      cell the other two get right is not a threshold being off by a little.
      Q4c IS THE CONTROL, and it is a strong one: its paper column is 17/19,
      identical to olx and python, and every cell it misses is missed by all
      three. So the rubric prompt is not generally worse -- something specific to
      Q4a's rubric text is.
      THIS ENTRY OWNS ALL FOUR, and it has to. When the cells were first found,
      two of them were already mentioned elsewhere -- Q4a/p6 by Q20 and Q4a/p20
      by Q19 -- so the ownership check reported only Q4a/p2 and Q4a/p18 as
      orphans and the other two looked accounted for. They were not: both of
      those subgoals are about olx/python behaviour, on cells where olx and
      python are CORRECT. A mention is enough to satisfy the check and is not
      enough to mean someone has looked at the paper side.
      Q4a/p6 has since LEFT Q20's list -- it was there as "gold charges one
      antecedent; we fail nothing", and we now fail antecedent_1 and agree with
      gold on both OLX-prompt engines -- so its paper half is held here alone.
      NEXT: diff rubric_h1's Q4a text against the OLX sheet's, and read p20's
      paper `credit_checks` and `deductions` against gold's "-2 pts" comment.
      Both engines that score the OLX sheet agree with gold there, so the
      question is what the rubric prompt asks that the sheet does not.

- [x] Q32. **ONE engine divergence and four unstable cells the median disguised.**
      Filed 2026-08-31 as "five cells the python gets right and the olx gets wrong",
      and REWRITTEN 2026-09-01 after measuring it, because that premise was wrong
      for four of the five. What the two-sided medians looked like, against how
      often each side actually matched gold over the same six runs:
          cell        gold   python matches   olx matches   medians
          DAY2/p8      4.0      3 of 6        2 of 6     python 4 / olx 0
          PR/p15       4.0      3 of 6        2 of 6     python 4 / olx 2
          Q2/p18       4.0      3 of 6        2 of 6     python 4 / olx 2
          WK2/p8       0.0      5 of 6        3 of 6     python 0 / olx 2
          Q4a/p9       3.0      0 of 6        6 of 6     python 5 / olx 3
      THREE OF THEM DIFFER BY ONE OBSERVATION. 3 of 6 puts the median on the right
      answer; 2 of 6 puts it on the wrong one. The cells are coin flips on BOTH
      engines and the median is a step function at exactly the halfway point, so a
      single run decides which side gets recorded as correct. DAY2/p8 is the
      clearest: `cadence_is_daily`, a 4-point gate, reads met/met/absent/absent/
      met/absent on the python and absent/met/absent/met/absent/absent on the olx.
      Same flip, same rubric, different luck.
      SO THERE IS ONE REAL DIVERGENCE, AND IT IS Q4a/p9 -- BUT THE FIGURES BELOW
      WERE TAKEN ON THE MISLABELLED ARTIFACTS AND ARE SUPERSEDED. Re-swept on
      contract the same day, Q4a/p9 is python 6 of 6 RIGHT and olx 3 of 6, so it
      is a RATE difference on an unstable olx side rather than the stable
      inversion this paragraph describes. It is one of the eight cells subgoal
      E39 collects. The original text is kept below because the inversion it
      records is still the reason the cell is interesting.
      SO THERE IS ONE REAL DIVERGENCE, AND IT IS Q4a/p9: 0 of 6 against 6 of 6,
      stable on both sides, the python scoring 5.0 where gold says 3.0 and the olx
      scoring 3.0. It also INVERTED on 2026-09-01 under E25's keyword conversion --
      it was python-right and olx-wrong before that, with nothing about
      `antecedent_2` touched. An unrelated slot leaving the sheet swapped which
      engine is correct. Declared in measured.GOLD_SLOT_BOUNDS_KNOWN.
      AND IT IS NOT AN ENGINE DEFECT EITHER, which took one more step to
      establish. The whole difference is one verdict:
          python  antecedent_1 met, antecedent_2 MET          -> 5.0
          olx  antecedent_1 met, antecedent_2 WRONG_KIND   -> 3.0
      Gold reads "-2 pts: The second example is not an antecedent", so the olx is
      right and the python is wrong. Both sides are served the SAME prompt body and
      the SAME slot sheet -- the two recorded prompt shas differ only because
      `measured._olx_only_visible` hashes fewer attributes for the python side, a
      staleness-detection detail and not a difference in what is sent. What
      differs is the MODEL, and backends.py names both: `--backend cli` runs
      ClaudeCliBackend at `opus`, while `--backend lo` posts to lo-blocks'
      /api/llm/chat/completions, which LoBlocksBackend's own docstring records as
      answering AS GPT-5-MINI. Same prompt, same sheet, two different models, one
      judgement they disagree on, deterministically at 6/6 each. gpt-5-mini is the
      one that agrees with gold here.
      SAY THIS PLAINLY, BECAUSE IT GOVERNS THE WHOLE AXIS: on these sweeps "olx"
      and "python" are not two engines, they are two MODELS running the same prompt
      through the same code. `measure_one` builds one prompt and one schema and
      hands both to whichever backend was selected. So a stable olx/python difference
      is evidence about the models, and an unstable one is evidence about nothing
      -- neither is an equivalence defect, which is what this subgoal was filed
      as. The engine-equivalence question is answered elsewhere, by the audit
      comparing what each SCORER computes, not by comparing two sweeps.
      NOT EXPLAINED BY E38. That subgoal is about the python fingerprint failing to
      notice attribute changes, which is a staleness-detection hole and cannot
      move a score; and both sides of p9 were swept fresh from the same tree
      minutes apart, so no stale number is involved.
      SO THE FIX IS PROMPT CLARITY, NOT CODE. There is nothing to reconcile
      between the engines here; one model reads this student's second example as
      a genuine trigger and the other does not. That makes it an
      `antecedent_2` criterion question -- the same second-box shape Q18 records
      for Q4b and Q19 records corpus-wide -- and it should be worked there rather
      than as an equivalence bug. It is the ONE cell in this subgoal that a
      wording change could move.
      THE OTHER FOUR ARE INSTABILITY, and each one's flipping slot already has a
      subgoal. They stay listed here so they keep an owner, but the work is there:
          DAY2/p8   `cadence_is_daily` flips on both sides          -> Q22
          Q2/p18    `wgb_inverts_utb` flips on both sides           -> Q17
          WK2/p8    `matches_chosen_type` flips on the python; on the
                    olx the VERDICTS are constant and `refers_to`
                    moves -- observed_type PP/PR, restriction_
                    authored created/neither                        -> Q23
          PR/p15    `targets_goal_behavior` flips on both sides     -> Q21 profiles
                    this same slot at 62% precision, its worst, but is scoped to
                    NR. PR is its sibling; widening Q21 is preferable to a new
                    subgoal.
      THE METHOD LESSON, which is bigger than these five. Comparing two sides at
      the median MANUFACTURES divergences on any cell near 50%, and four of the
      five "olx defects" here were that artifact. Before reading a python/olx
      difference as an engine defect, check the per-run agreement rate on both
      sides: if the two are within one run of each other, there is nothing to fix
      in either engine and the cell belongs to whichever subgoal owns its unstable
      slot. Recorded in QUALITY_CONTROL.md 2e.
      WHAT IS LEFT. Nothing in this subgoal is an equivalence defect: four cells
      are instability owned elsewhere, and the fifth is a provider disagreement
      about one judgement. The cells stay listed here so the 2d ownership check
      keeps finding them a home, but the work belongs to Q22, Q17, Q23, Q21 and
      the `antecedent_2` wording. This subgoal can close once those name their
      cells -- ask before closing it.
      CLOSED 2026-09-01. Its premise is gone: this was "cells one engine gets
      right and the other wrong", and the two engines are now pooled, so the
      category no longer exists. Two of its five cells -- Q4a/p9 and WK2/p8 --
      are right at the pooled median, and the other three are ordinary wrong
      cells with nothing side-specific about them.
      WHERE THE THREE WENT: DAY2/p8 and PR/p15 are already carried by Q31 as
      silent full-marks rows, and Q2/p18 moved to Q17, whose `wgb_inverts_utb`
      it is -- pooled it reads 2.0 seven times and 4.0 five times against a gold
      of 4.0, so it misses by one observation rather than by a side.
      THE SUBGOAL WAS RIGHT TO EXIST AND WRONG IN ITS READING, which is worth
      keeping. It was filed by the ownership check on its first run and found
      five cells a one-sided accounting could not see; that part held. What did
      not hold was reading a median difference as an engine difference --
      QUALITY_CONTROL 2e records three of the five being ONE observation apart,
      and the exact test later showed the whole corpus has no power to
      distinguish the sides at six runs each.


- [ ] Q30. **Where we charge MORE than gold: Q5/p4 and 1c/p11, against a corpus that is otherwise lenient.**
      Filed 2026-08-31 from E30's accounting, for being the exception. Twenty-one
      of the twenty-two declared slot disagreements are us CREDITING a slot gold
      charged; these run the other way, and are the evidence that the leniency is
      not uniform.
      THE TITLE ORIGINALLY SAID Q5/p4 WAS THE ONLY ONE. That was true of the 22
      DECLARED cells and not of the corpus: 1c/p11 does the same and was not
      declared, because its gold comment does not reconcile and the accounting
      therefore reads no slots from it. Corrected rather than left, since "the
      only cell" is exactly the kind of claim a later reader would rely on.
      1c/p11: gold 6.0, ours 4.0, stable in 6 of 6 runs. We fail `legend`,
      `x_axis_label` and `y_axis_label`; gold charges the two axis titles and adds
      "-1 pt: missing baseline data week", which is a 1b charge on a 1c row -- the
      same cross-item shape as Q4c/p16, where a Q4b comment appears on a Q4c row.
      So the disagreement is `legend`: we say it is missing and the grader did not.
      READ THE TWO TOGETHER. Q5/p4 is a RULE being stricter than the corpus;
      1c/p11 is a single slot judged present by one side and absent by the other,
      with no rule in dispute. If both hold up they are separate findings, and the
      shared title is only a filing convenience.
          gold  2.5   "-2.5 pts: missing one reason why you continue to engage"
          ours  0.0   example_1 AND example_2 both `wrong_kind`, 6 of 6 runs
      So gold credits ONE of the two boxes and we reject BOTH, stably.
      WHAT THE BOXES SAY, read out rather than inferred:
        first  -- "{{corpus:Q5/p4:first:0:78:sha=f7407ff462b1:shape=S11-0a202020202020202020202020202020202020}}". Garbled, and the reason given is a reason
                  for the GOAL behaviour, not for continuing the unwanted one.
                  `wrong_kind` looks right here.
        second -- "{{corpus:Q5/p4:second:0:90:sha=9a9ecf03c0b1:shape=S10-0a202020202020202020202020202020202020,A93}}" That is an EFFECT of the
                  behaviour, and our rule says so in as many words: `{fail}` is
                  for "an EFFECT of the behaviour rather than a payoff from it".
                  Gold credited it anyway.
      SO THE DISAGREEMENT IS THE RULE, NOT THE READING. We applied the effect-vs-
      payoff distinction exactly as written and gold does not draw it as sharply.
      That rule is the one E11 migrated on 2026-08-30 -- `example_2`'s text moved
      from olx-only SLOT_NOTES into the shared `rule` -- so this cell is now the
      only measured evidence about whether the distinction itself is too strict.
      DO NOT LOOSEN IT ON ONE CELL. Q5 records 19/20 on both sides, so the rule is
      right on the other nineteen, and the effect-vs-payoff clause exists because
      example_1/example_2 previously absorbed weak reasons -- see
      reasons_substantial's rule and the E11 history. The honest question is
      narrower: does gold EVER charge an effect-dressed-as-reason on this item? If
      it does, p4 is a grader inconsistency and stays declared; if it never does,
      the clause is stricter than the corpus and the whole item wants re-measuring
      after it changes.
      COUNT THAT FIRST. It costs no API calls: the phrase table for Q5 does not
      exist yet, but Q5 has only two cells with itemised gold, and the rest of the
      item's comments can be read directly.

- [ ] Q29. **Q2's `wgb_is_counterpart` GATES for 5 where gold charges 2, and it flips.**
      Filed 2026-08-31 from E30's accounting. Q2/p10 is the demonstration and the
      cheapest possible read: both scorers and the grader agree the WGB is not the
      opposite of the UTB, and the disagreement is entirely in what that costs.
          gold  3.0   "-2 pts: your WGB should be the opposite of your UTB"
          ours  0.0   `wgb_is_counterpart` is a GATE -- failing it takes all 5
      SO THE SAME JUDGEMENT IS WORTH 2 TO THE GRADER AND 5 TO US, on every cell
      where it fails. That is not a per-cell miss; it is the wiring.
      AND THE SLOT IS UNSTABLE, which makes the wiring maximally expensive: over
      six recorded runs it answered `met` once and `absent` five times, so the
      cell scores 3.0 in one run and 0.0 in the other five. An unstable judgement
      on a gate is the worst combination available -- Q21 and Q22 record the same
      shape on NR's and DAY2's gates, and this is a third instance.
      TWO THINGS TO SETTLE, in this order:
        Is the GATE right? Q2's own deduction dictionary is what says whether "not
          the opposite" is a whole-item failure or a 2-point one. If the
          dictionary says 2, the gate is ours and not the rubric's, and removing
          it is a sheet change measurable at 6 runs.
        Is the SLOT stable enough to gate anything? One flip in six is not a
          judgement, and `wgb_is_counterpart` is already declared
          PROSE_ONLY_SLOTS -- "a judgement about what two pieces of prose are
          ABOUT, with no operand pair that expresses it".
      DO NOT change both at once. Removing the gate and rewording the slot in one
      sweep confounds them, and this item has 20 cells to spend.

- [x] Q28. **Q6/p5: the python's one miss is `state_a1` refers_to drift, not a rule.**
      DIAGNOSED 2026-08-31, from the artifacts on disk, no API calls. Two wrong
      mechanisms were proposed and retracted first; both are recorded because the
      way they were wrong is the reusable part.
      THE ANSWER. All six python runs answer `state_c1: first` AND `state_c2: first`
      -- the same cover label twice -- so the greedy claim in
      agreement.satisfied_map always denies state_c2, and `requires` always
      denies affect_c2 because link_c2 answers `absent` every run. That is two
      failures in every run. The five runs that MATCH gold have a third:
      `state_a1: none`, which is not one of the group's labels and so earns
      nothing. Run 4 -- the only miss -- answers `state_a1: first`, claims the
      label, and banks 1.25 the other five do not:
          runs 1,2,3,5,6   failed 3   score 6.25   = gold
          run 4            failed 2   score 7.50
      The arithmetic is exactly 10 - 1.25 x failed_slots throughout.
      SO IT IS THE `refers_to` CEILING, which memory/q6-matching-ceiling.md
      already names: "Only 5 of 20 cells returned the same judgement in all three
      passes, with all the drift in the four state_* slots that carry
      `refers_to`." p5 is that drift, on state_a1, in one run of six. It is not a
      `requires` defect, not a codes defect, and not a duplicate-rule defect.
      TWO RETRACTED LEADS, so neither is tried again:
        (1) "`requires` skips a dependent already in `demoted`, so an
            independently failed slot escapes the denial." That code exists at
            score.py:535 -- but the python column is agreement.py, whose `requires`
            is a plain boolean AND (agreement.py:986) with no such skip.
        (2) "Every Q6 slot offers a verdict with no deduction code -- the olx
            answers `incomplete`/`mismatch` while the rubric's `codes` maps are
            keyed on the paper's `not_described`/`neither` -- so a failure goes
            uncharged." The gap is REAL and worth knowing, but it is not a
            scoring bug: Q6's score is points-based off failed_slots, and the
            codes carry the FEEDBACK text, not the arithmetic. Confirmed by
            scoring three verdict sets that differ only in that token and getting
            one number.
        BOTH came from reading the artifact's `checks` field and not its
        `answers` field. The cover references live in `answers`, and on this item
        they decide almost everything: two of the three failures in every run are
        cover outcomes. Read both fields before proposing a mechanism.
      DO NOT RETIRE THE DECLARATION. It was proposed for retirement here and that
      was WRONG, caught by reading gold's own comment instead of its total. Gold
      charges three slots on p5:
          -1.25 First antecedent does not match antecedents listed in 4a
          -1.25 First consequence does not match 4c
          -1.25 Second consequence does not match 4a   [4c is meant]
      so gold fails state_a1, state_c1 and state_c2. WE fail state_a1, state_c2
      and affect_c2. Same total, DIFFERENT SLOTS: we credit state_c1 where gold
      charges it, and we charge affect_c2 where gold does not.
      SO p5's AGREEMENT IS COMPENSATING ERROR, not correctness, and
      DUPLICATE_EFFECT_TIE_BREAK's stated reason -- "gold credits both effect
      boxes and our duplicate rule does not" -- is confirmed by gold's comment,
      which never charges an effect box. The declaration is TRUE and stays.
      WHICH MEANS `scored_exactly` HID IT. Every rate in this project compares
      totals, so a cell failing the wrong slots in the right quantity reads as a
      match on both sides -- and on p5 it read as a 6/6 olx success. The
      per-slot check that would catch it is cross_path --slots, which compares
      the two SCORERS to each other and not either of them to gold. Nothing
      compares our slot set against the grader's slot set, and this cell is the
      demonstration that the gap is real. E30 now does; see below.
      THE ALARM IS FIXED, NOT SILENCED, 2026-08-31. declaration_conflicts had been
      reporting DUPLICATE_EFFECT_TIE_BREAK as contradicted on the strength of that
      6/6 olx total, and refused four commits over it. It now asks
      gold_charged_slots first: where the slot sets can be compared and DIFFER, it
      draws no conclusion, because agreeing on a total while failing different
      slots is not evidence a divergence has expired. Q6/p5 stops being reported
      and the entry stays, both for the same reason.
      NOT AN EXEMPTION -- no cell, item or side is named in the change. Every
      divergence gets the same protection, and where a comment cannot be read the
      total still stands, which is the previous behaviour. Verified behaviourally
      in all three states: slots agreeing still reports, slots unreadable still
      reports, only slots differing declines.
      THE REAL WORK, then, is two cells' worth of slot-level disagreement on p5:
        state_c1 -- we say the first consequence box matches 4c first, gold says
          it does not. The box is "{{corpus:Q6/p5:state_c1:96:156:sha=448318110368:shape=S6-0a20202020202020202020}} foods"; 4c first is "{{corpus:Q4c/p5:first:68:128:sha=192652132e50:shape=S3-0a20202020202020202020}} alternatives". Gold's reading is
          defensible and ours is the looser one.
        affect_c2 -- we charge it through link_c2 and gold charges nothing on the
          effect boxes at all. That is the declared divergence, and it is doing
          exactly what it says.
      Fixing state_c1 without fixing affect_c2 would BREAK the total, taking p5
      from 6.25 to 5.0. The two are only safe to touch together, and that is a
      matching-rule question on `refers_to`, which is the Q6 ceiling. Read
      memory/q6-matching-ceiling.md before proposing anything.
      CLOSED 2026-09-01. Q6/p5, its only cell, is RIGHT at the pooled median --
      the subgoal was written from the python column alone, where the miss sat.
      READ THE CAVEAT BEFORE TREATING THIS AS SETTLED. Q6/p5 remains a DECLARED
      slot-level disagreement, and the ownership check deliberately does not
      retire those on a matching total: compensating slot errors that sum to the
      right score are the entire reason that accounting exists. So the cell's
      TOTAL is no longer wrong, and the claim that our failing slots differ from
      gold's is untouched by this closure. It lives on in the slot tables, which
      is where it can be argued with.


- [x] Q27. **DAY1/p1 scores 0.0 against a gold of 4.0, deterministically, on both sides.**
      Filed 2026-08-30. DAY1 UNDER-credits one-sided -- python 1 over / 8 under, olx
      0 over / 7 under -- and p1 carries 6 of those 8 and 6 of those 7, failing
      6 of 6 runs on BOTH scorers. Predicted 0.0 every time; gold is 4.0. The
      whole item, stably, on one cell.
      IT WAS INVISIBLE UNTIL E29. The profile counted excluded cells, and p2/p3
      contributed 6 of DAY1's 7 apparent over-credits, so the item read 7 over /
      8 under -- two-sided, "the judgement is unstable", nothing to chase. With
      exclusions applied it is one-sided and points at a single cell.
      NOT A FIXTURE DEFECT, checked first per QUALITY_CONTROL.md and
      memory/fixture-defects-found-by-readout.md. All five fields are present;
      `bmod_h2_day1` reads "{{corpus:DAY1/p1:day1:0:72:sha=b56fbe949d26:shape=S10-0a202020202020}}" The scorers are reading a real answer.
      NOT Q23's FINDING EITHER, and this is the thing to be careful about. Q23
      names DAY1/p1 as a `matches_chosen_type` error, and it is listed there as
      wrong on 4 of 6 runs. But Q23's mechanism is two PICKS that disagree, and
      here both picks come back EMPTY -- `observed_type=""` and `named_type=""`
      in all 6 runs -- with `matches_chosen_type=absent` downstream of that, not
      the cause of it. Do not re-derive Q23 here, and do not fold this into it:
      an empty pick and a disagreeing pick are different failures.
      WHAT ACTUALLY HAPPENS: every slot answers `absent` in all 6 runs --
      names_behavior, contingent, follows_behavior, states_a_contingency -- so
      the sheet finds no contingency at all and the item collapses to zero. That
      reading is not obviously wrong: "{{corpus:DAY1/p1:day1:0:65:sha=ed279714b714:shape=S7-0a202020202020,S10-20}}" states no condition on a behaviour. The graders
      credited it 4.0 anyway.
      SO THE QUESTION IS WHICH SIDE IS RIGHT, and it is worth asking because the
      answer is 4 points either way:
        1. Is the all-slots-`absent` result reaching the blank-answer collapse?
           enforcement has a check that the collapse is GATED on an actually
           blank answer -- confirm it is not firing on a non-blank one here.
        2. If not, is `states_a_contingency` too strict for a plan phrased as a
           reward-for-a-state rather than an if-then?
        3. Or is gold generous, in which case this is a CORRECTED_GOLD candidate
           and needs the citation that justifies it, not an assertion.
      Answer 1 before 2, and 2 before 3. Do not change prose before then.
      == 2026-09-02: ALL THREE ANSWERED, IN THAT ORDER. GOLD IS CORRECTED. ==
      1. NOT THE BLANK-ANSWER COLLAPSE. Six slots come back `met` --
         cadence_is_daily, names_stimulus, targets_own_behavior, you_arrange_it,
         consequence_not_a_setup, and phrased_directly on python -- so the sheet
         made DIFFERENTIATED judgements about a non-blank answer rather than
         collapsing. THIS ENTRY'S OWN PREMISE HAS EXPIRED: "every slot answers
         `absent` in all 6 runs" was true of the 2026-08-30 artifacts and is not
         true of the current ones. Read the verdicts before reusing that line.
      2. `states_a_contingency` STRICTNESS DOES NOT RESCUE THE CELL, so question
         2 is answered without needing to settle whether the rule is too strict.
         Four independent slots are absent -- names_behavior, contingent,
         follows_behavior, consequence_asserted -- and loosening one of them
         leaves the other three. The refusal is over-determined.
      3. SO GOLD IS GENEROUS, and the citation this entry demanded rather than an
         assertion is now `handouts.CORRECTED_GOLD[("DAY1", 1)]`: 4.0 -> 0.0. The
         ground is that the student CONTRADICTS THEIR OWN DEFINITION -- they chose
         Positive Reinforcement and wrote "{{corpus:D1/p1:d1:35:60:sha=1dcbd3b307d1:shape=C1ff7e00}} DESIRED",
         then rewarded themselves by REMOVING an aversive -- plus gold's own
         comments on p6 ("what you take away or add has to happen after the
         behavior is exhibited") and p8 (the example-does-not-match-the-type
         charge). Gold charged seven DAY1 cells to 0.00 and we score 0.00 on all
         seven; p1 was the one silent full-marks row.
      CLOSED 2026-09-02. The three questions above are answered in the order
      this entry set, the cell is corrected with the citation it demanded rather
      than an assertion, and DAY1 NOW SCORES 18 OF 18 at the pooled median --
      there is no residual under-credit to re-scope onto. Note for anyone reading
      the opening paragraph: its "python 1 over / 8 under, olx 0 over / 7 under"
      profile is the 2026-08-30 measurement and no longer describes the item.

- [ ] Q20. **The SHEET CANNOT REFUSE: over-credit with every check passing.**
      Two views of one phenomenon, merged 2026-08-28: cells where every scoring
      check passes and gold still docks, and the observation-level rate that says
      how much of our over-crediting works that way. Subgoal 22 held the second
      view and is folded in here.
      == THE MECHANISM, NAMED 2026-08-31 BY E30's SLOT-LEVEL ACCOUNTING ==
      "Every check passes and gold still docks" now has a mechanism rather than a
      description: WE CREDIT A SLOT GOLD CHARGED, and the comparison says which.
      Seven cells localise here, each with gold's own itemisation naming the slot:
          Q1/p10   gold charges reason_3;        we fail nothing
          Q4c/p20  gold charges consequence_2;   we fail nothing
          Q6/p2    gold charges change_a2;       we fail nothing
          Q6/p16   gold charges affect_c2;       we fail nothing
          Q4c/p16  gold charges one consequence; we fail nothing
          Q6/p6    gold charges state_a2 as well as the two we fail
          DAY2/p7  gold charges WRONG_BEHAVIOR;  we fail nothing
      DAY2/p7 ARRIVED 2026-09-02 FROM THE OWNERSHIP FIX, not from a sweep. It is
      the same mechanism as the six above with a CODE in place of a slot, because
      DAY2 is criteria-derived and has no slot to name: the student's plan rewards
      reading by "{{corpus:DAY2/p7:day2:56:83:sha=431dfd8eb891}} night" while their target behaviour
      is spending LESS time on devices, so the reward IS the unwanted behaviour.
      Gold charges 1 point -- "make sure the behavior you are targeting is
      spending less time on electronic devices" -- and every one of our checks
      passes, on both engines, in all twelve pooled runs.
      IT WAS HIDDEN BY AN OWNERSHIP BUG rather than by a median. Q26, whose title
      is "DAY1 alone gates on `phrased_directly`", mentioned the cell in passing,
      and ownership counted ANY mention -- so a subgoal about a different item
      held the only claim on it. measured.GOLD_CODE_KNOWN records the
      disagreement, and its own preamble is explicit that those entries are "NOT
      declared as acceptable", so recording it was never a substitute for a home.
      Q4a/p6 LEFT THIS LIST on 2026-09-01: it read "gold charges one antecedent;
      we fail nothing", and we now fail `antecedent_1` against gold's single
      charge -- so the two agree, and the cell scores 3.0 against gold 3.0 on
      both OLX-prompt engines. Six of the seven remain. The cell is still wrong
      on the PAPER scorer, where it over-credits to 5.0, and that half belongs to
      Q33.
      THAT IS THE SAME FINDING FROM A NEW DIRECTION, which is the reason to trust
      it: this subgoal was filed off the observation-level rate, and the slot
      comparison was built for an unrelated purpose. Q4a/p6 and Q4c/p16 are BOUNDED
      rather than exact -- gold's comment does not say which slot, only that one was
      charged -- and the finding holds on every reading.
      DO NOT read the list as seven separate cells to fix. Six of the seven are
      "gold charged one slot, we charged none", which is one behaviour.
      AND ONE CELL SITS THE OTHER WAY, recorded here because it is Q1's and has no
      better home: Q1/p9. Gold charges reason_3 and so do we, so the SLOTS agree
      -- but the total does not, 4.0 against our 3.0. The cause is a COUNT drift,
      not a slot judgement: `reasons_given` answers 2 in two runs and 1 in four,
      and the runs that answer 1 fail reason_2 as well. Gold says "only provided
      two reasons", so the two-answering runs are right. A count that cannot be
      answered twice the same way is the shape memory/error-profile-by-slot.md
      calls drift, and no rewrite of a slot rule fixes it.

      == THE GATE SLOTS ARE MOSTLY ORTHOGONAL TO CORRECTNESS ==
      Added 2026-08-29 from the completed two-sided sweep, and it bears directly
      on view one: the sheet often cannot refuse because the instruments that
      COULD refuse are not tracking the thing being scored.
      Across seven H2 items, the four structural gates -- `names_behavior`,
      `names_stimulus`, `contingent`, `follows_behavior` -- refuse constantly and
      almost never in a cell that is wrong:
          PR    1/0,  9/0, 19/0, 17/0        PP    6/0, 12/0
          NP   12/0, 18/0                    WK1  14/0, 12/0, 18/0
          NR    6/0, 12/0, 14/0, 13/0        DAY2 12/0, 23/0, 18/0
      (refusals / of which in a WRONG cell). Hundreds of refusals, essentially
      none coinciding with a miss. These are four required properties of a strict
      schema, asked on every call, doing no discriminating work.
      DAY1 IS THE EXCEPTION AND IT IS NOT A COUNTEREXAMPLE -- it is a different
      sheet. `names_behavior` 18/6, `contingent` 23/6, `follows_behavior` 26/6.
      The cause is structural and was found by looking: DAY1 is the ONLY item of
      eight where `phrased_directly` GATES (`!phrased_directly` in its OLX; the
      other seven author it plain). When any gate fires the item zeroes, so a
      second gating slot makes every other gate's unmet status co-occur with a
      wrong cell. HYPOTHESIS, NOT YET CONFIRMED: DAY1's six-apiece counts are that
      artefact rather than those gates discriminating. Test it by checking whether
      those cells are wrong on runs where `phrased_directly` is MET. Subgoal 24
      owns the asymmetry itself.
      WHAT THIS DOES NOT SAY: that the gates are useless. A gate that never fires
      wrongly may be holding a floor nobody has tried removing -- PP and NP sit at
      100% on both engines WITH these gates in place, and subgoal Q21 records a
      proposal to remove one that was withdrawn for exactly that reason. The
      finding is that they are not where this item family's errors live, so they
      are not where a fix for view one will come from.

      == VIEW ONE: the rate, and why the asymmetry is structural ==
      Measured 2026-08-28 over the python sweep's fourteen scored items, 6 runs each,
      with `cell_exclusions` applied. Counting observations where our score differs
      from gold and asking whether ANY scoring slot was unmet:
          over-credit    84 observations,  32 with NO slot unmet   (38%)
          under-credit  129 observations,   2 with no slot unmet   (1.6%)
      THE ASYMMETRY IS STRUCTURAL, and stating it plainly is most of the value: to
      UNDER-credit the sheet must refuse something, so a slot has to be unmet. To
      OVER-credit it need only fail to refuse. So a fully-satisfied sheet is almost
      never wrong in the strict direction and is wrong in the generous one 32 times
      -- and those 32 cannot be reached by tuning any existing slot, because every
      slot already passed. They need a NEW check or a declared divergence.
      WHERE THEY ARE, which is not everywhere:
          Q6   8 of 22 over-credits clean      Q4a  7 of 13
          Q4c  6 of 12                         Q1   5 of  5
          NR   3 of  3                         WK1  3 of  6
          Q2   0 of  5    Q3  0 of 11    Q4b  0 of  7
      Q1 and NR are the pure cases: EVERY over-credit they make happens with the
      sheet fully satisfied. Q3 and Q4b are the opposite -- their over-credits all
      involve a slot that fired and was wrong, which is a tuning problem and a
      different kind of work. Do not treat the two groups with one fix.
      THE TWO VIEWS AGREE: 32 observations over six runs is roughly five to six
      cells, and view two below lists four that hold in a MAJORITY of runs. The
      rate says which items carry it; the cell list says which cells to read.
      DO NOT READ THE PROFILE HINT AS A DIAGNOSIS HERE. `measured.error_profile`
      prints "one-sided: a threshold is set wrong, not unstable" whenever the
      direction is lopsided -- it says that for Q3, whose over-credits all have slot
      errors, and it would say it for Q1, whose over-credits have none. Those are
      opposite problems and the hint does not distinguish them.
      AND CHECK IT ON THE OLX COLUMN. If the same 32 appear there, the sheet is
      missing a check and both scorers inherit it. If they do not, the python's
      arithmetic is crediting something the app refuses, which is an equivalence
      defect rather than a rubric gap.


      == VIEW TWO: the individual cells ==
      Opened on PR/p3 as asked, and generalised by detector rather than by eye,
      because the first hypothesis about that cell was wrong (below).
      THE CLASS: cells where every non-pick check is `met` -- `confident` excluded,
      it is the corpus noise floor -- and gold still refuses, stably across all six
      runs. Four exist in the nine items swept so far:
          PR   p3   ours  4.00  gold 0.00   the WHOLE item, undeclared
          Q4c  p16  ours  5.00  gold 3.00   undeclared
          Q4c  p20  ours  5.00  gold 3.00   undeclared
          Q6   p2   ours 10.00  gold 8.75   DECLARED, the change_a1/change_a2 ceiling
      WHY THIS CLASS MATTERS MORE THAN A CELL: no amount of tuning an existing slot
      can reach these. The sheet is fully satisfied, so there is no verdict to flip
      -- gold is objecting to something the sheet has no check for. The options are
      a NEW check, or a declared divergence, and Q6/p2 shows the project has already
      concluded the latter once. Reading these as "the criterion is too lenient"
      would send someone tuning slots that already pass.
      PR/p3 IS THE STARKEST: gold gives ZERO on a 4-point item while we give full
      marks in 6 of 6 runs, and the model classifies it correctly on both picks --
      `observed_type` PR, `stimulus_move` given_desirable, which is exactly what a
      PR example should answer. Every one of `names_behavior`, `names_stimulus`,
      `contingent`, `follows_behavior`, `you_arrange_it`, `demonstrates_type` and
      `targets_goal_behavior` passes. Whatever gold saw, the sheet does not ask
      about. Read gold's feedback for p3 FIRST -- that is the only place the
      objection is stated.
      Q4c's two are the same shape at 2 points each, and Q4c already runs a bias of
      +0.21 with 18 over-credits against 1 under -- the most one-sided item in the
      sweep -- so this class may be most of what that bias is.
      A DEAD HYPOTHESIS, recorded so it is not re-run: PR/p3 was first read as
      "blank picks yet full credit", because `checks` shows `observed_type` and
      `stimulus_move` as empty strings. That is a RECORDING CONVENTION, not a
      defect -- a pick's value lives in `answers`/`refers_to`, and `checks` carries
      verdicts. It is blank on all 20 cells of PR and all 20 of Q4b, including
      every cell that scores correctly. Nothing is wrong with the picks.
      THE DETECTOR WAS WRONG TWICE, and the corrected class is FOUR cells, all on
      handout 1:
          Q1   p10  ours  5.00  gold 4.00     also subgoal Q14
          Q4a  p17  ours  5.00  gold 4.00
          Q4c  p20  ours  5.00  gold 3.00
          Q6   p2   ours 10.00  gold 8.75     DECLARED ceiling
      FIRST ERROR: it excluded only `confident`, so any cell with an unmet ADVISORY
      slot fell out -- and `phrased_directly` is advisory on the H2 type items
      (pts=None, gates=False, it cannot deduct). Counting only gates and
      point-carrying slots fixed that.
      SECOND ERROR, and the instructive one: it read the raw per-cell results
      WITHOUT applying `handouts.cell_exclusions`. Handout 2's p2 and p3 are
      SUSPECT on every item -- "byte-identical transcriptions but different gold
      rows, so at least one is mis-transcribed and neither can be attributed" --
      and excluded cells are still RUN and scored on purpose, so they appear in the
      artifacts looking like ordinary results. That produced PR/p3, NR/p3 and
      WK1/p3 as apparent members, and a false pattern on top of them: "three
      different H2 items, all on participant 3", which is just the one known-bad
      transcription seen three times. Q4c/p16 also dropped out on exclusion.
      THE LESSON, which is the same one three times today: compute through the
      accessors that apply the project's own accounting -- cell_exclusions,
      scores_as_exact, the ledger's numerator -- not from the raw artifacts. Every
      convention I read as a signal today (the ±tol column, blank picks, suspect
      cells) came from going around them.
      Q1/p10 is the useful survivor: subgoal Q14 has it as a live miss, and this
      says no slot on that sheet can refuse it, which is a different problem from a
      criterion set too loosely.
      MONITOR THE REST OF THE SWEEP with the corrected detector -- only gates and
      point-carrying slots count as scoring. If the class grows past a handful, or
      concentrates on one handout, that changes it from a per-cell question into a
      sheet-design one.

- [x] Q23. **`matches_chosen_type` on WK2, and across the cadence family.**
      POOLED, 2026-09-01, ONLY ONE CELL SURVIVES. WK2/p8, WK2/p11, WK2/p15,
      NR/p11 and NR/p15 are all RIGHT at the pooled median -- they were recorded
      as misses on one column each. Pooled, WK2 misses nothing at all.
      WHAT IS LEFT IS DAY2/p7, and it is not this subgoal's shape: its pooled
      spread is 0.0 and 4.0 with nothing between, a coin flip on a 4-point item
      rather than a `matches_chosen_type` threshold set wrong. Read it as an
      instability -- subgoal Q22's territory, since DAY2's flipping gate is
      `cadence_is_daily` -- before treating it as evidence here.
      SO THIS ENTRY IS A CLOSE CANDIDATE. Ask before closing: it names a family,
      and one cell of a family is thin evidence that the family is fine.
      GOLD-SIDE EVIDENCE, rehomed here 2026-08-31 when E35 closed. E35 built the
      code-level comparison for the criteria-derived items and found five
      disagreements; closing it would have left them owned by nothing, so they
      live here, where the type family already does:
          NR/p15   gold WRONG_TYPE (2)      we charge nothing
          WK2/p3   gold TYPE_MISMATCH (2)   we charge nothing
          WK2/p15  gold TYPE_MISMATCH (2)   we charge nothing
          DAY2/p7  gold WRONG_BEHAVIOR (1)  we charge nothing
          NR/p11   gold WRONG_TYPE (2)      we charge 4
      FOUR LENIENT AND ONE HARSH on the same judgement. This entry's own table
      measures `matches_chosen_type` precision from OUR side -- 73 refusals, 11
      wrong -- and these are the grader's side of the same question: cells where
      gold charges the type and we do not, or charge far more.
      NR/p11 IS THE ONE TO READ FIRST, and it is not a type-rule question yet.
      Gold says the example IS operant conditioning but of the wrong type, worth
      2; we charge 4, which is NOT_OC, NOT_EXTERNAL_STIMULUS or BLANK -- the score
      alone cannot separate them. agreement.score_oc is a cascade that returns at
      its FIRST failure, so a definitional criterion reading unmet hides the type
      question entirely. Read which of the four criteria failed before touching
      any type rule.
      Measured 2026-08-28 over the python sweep, 6 runs, exclusions AND corrected gold
      applied (see the caution at the end -- the first version of this table was
      wrong without them):
          D1    6 refusals  100%          WK1   10 refusals  100%
          D2    6 refusals  100%          DAY2   9 refusals   89%   wrong on p11
          WK2  30 refusals   80%          DAY1  12 refusals   67%   wrong on p1
                wrong on p8 x3, p11 x2, p15 x1
          ALL  73 refusals, 11 wrong
      WK2 CARRIES MOST OF THE VOLUME -- 30 of 73 refusals, more than twice any other
      item -- and 6 of the 11 errors. DAY1 has the worst RATE but on a single cell,
      p1, failing 4 of 6 runs. The definition items and WK1 never err.
      IT IS A COMPUTED CHECK, SO THE LEVER IS NOT THE CHECK. `matches_chosen_type` is
      declared as `equals`: observed_type == named_type, lenient on `unclear`. The
      arithmetic cannot be wrong -- if it fires, the two PICKS disagreed. So the
      question is which operand is misread on WK2's p8/p11/p15 and DAY1's p1: does
      the model misclassify what the student DEMONSTRATED (`observed_type`), or what
      they SAID they would use (`named_type`)? Read both picks on those four cells
      before touching any prose; the answer is in the artifacts and costs nothing.
      IT DOES NOT GATE on WK2 -- pts=2.0, gates=False -- so each error costs 2 of 4
      rather than the item. That distinguishes it from `cadence_is_weekly` and
      `you_arrange_it`, which do gate, and it means WK2's ±3 spread is NOT mostly
      this: a 2-point slot cannot produce a 3-cell swing on its own.
      A BROADER PROBLEM, AS SUSPECTED, BUT NOT A UNIFORM ONE: six items carry the
      check and three are perfect. It concentrates on the two items whose answers
      are hardest to type, which is the same shape as the cadence gate (subgoal Q22)
      and the `you_arrange_it` gate (subgoal Q21) -- an instrument that is sound where
      it fires rarely and unreliable where it fires often. Three slots now show that
      pattern; consider whether it is one finding about the H2 sheet rather than
      three about three slots.
      ALSO IN `SLOT_RULE_BACKLOG`: `matches_chosen_type` is one of the four unscoped
      entries whose judging text lives in SLOT_NOTES, so the PAPER scorer never sees
      it. Both columns of this sweep read it, so that is not causing these errors --
      but it means equivalence subgoal Q11 and this subgoal touch the same rule, and
      migrating it to the rubric `rule` field should happen once, not twice.
      CAUTION, and it cost this table two wrong entries: compute correctness with
      `H.apply_corrected_gold` and `H.scored_exactly`, never `abs(pred-gold)`. D2's
      p11 gold is CORRECTED from 1.0 to 0.0 -- the grader charged 1 point for
      writing another quadrant's definition where three independent sources say 2 --
      so a raw comparison read D2 as 0% precise on this slot when it is 100%.
      CLOSED 2026-09-01. Five of the six cells it names are RIGHT at the pooled
      median -- WK2/p8, WK2/p11, WK2/p15, NR/p11 and NR/p15 -- each having been
      recorded as a miss on one column only. Pooled, WK2 misses nothing at all,
      so the item this subgoal is named for has no error left to explain.
      THE SURVIVOR IS NOT THIS SUBGOAL'S SHAPE. DAY2/p7 scores 0.0 and 4.0 with
      nothing between across twelve runs -- a coin flip on a four-point item,
      which is `cadence_is_daily` and therefore subgoal Q22's gate, not a
      `matches_chosen_type` threshold set wrong. It stays owned: subgoal Q26
      names it too.
      WHAT IT WAS RIGHT ABOUT. The cadence family really does share a slot and
      really did carry misses; what it could not see, reading one column at a
      time, was that five of those six misses were sampling. That is the same
      lesson subgoal Q32 closed on, arrived at from a different item.


- [ ] Q22. **`cadence_is_daily`: a 4-point gate that FLIPS, worst on DAY2.**
      Raised 2026-08-28 from the sweep. Filed here rather than as a goal of its own
      because GOALS.md holds ONE active goal and that is the equivalence sweep;
      promote it if it should displace that.
      IT GATES. `cadence_is_daily` and `cadence_is_weekly` are gates=True, pts=None
      on all four cadence items, so a single unmet verdict zeroes the whole 4-point
      item. That makes its precision the item's ceiling.
      THE SAME CHECK, FOUR ITEMS, A SPREAD RATHER THAN A SPLIT:
          WK1  cadence_is_weekly  20 refusals  100% precise   no errors
          DAY1 cadence_is_daily   26 refusals   92%           wrong on p11
          WK2  cadence_is_weekly  19 refusals   84%           wrong on p15, p11
          DAY2 cadence_is_daily   17 refusals   71%           wrong on p8, p9, p11
      WRITTEN FIRST AS "the weekly form is clean and the daily form is not", on WK1
      and the two DAY items alone. WK2 landed at 84% and that reading does not
      survive it: the four points interleave, so this is a spread across all four
      cadence items and not a daily/weekly divide. Which also means the period
      substituted from the item's `cadence` field is probably NOT the variable --
      look at what the items ask before blaming the word.
      AND IT IS THE SAME KIND OF FAILURE ON WK2 AS ON DAY2 -- flipping, not a
      threshold: p15 reads [met, met, absent, met, absent, met] against gold 2.0 and
      p11 [met, met, met, met, absent, met]. p11 flips on DAY2 AND on WK2, which is
      the one cell to read first: it is the only participant appearing in three of
      the four items' error lists.
      AND ON DAY2 IT IS NOT A THRESHOLD, IT IS INSTABILITY. The verdicts flip run to
      run on cells whose input never changes:
          p8   gold 4.0   verdicts [absent, met, met, met, absent, absent]   ours 0.0 / 4.0
          p9   gold 4.0   verdicts [met, met, met, absent, met, met]         ours 0.0 / 4.0
          p11  gold 2.0   verdicts [met, absent, met, met, met, met]
      p8 is the case to work: gold gives FULL credit and says nothing, and a gate
      flips on it three times in six, taking the item from 4.0 to 0.0 each time.
      That is the largest single source of variance found in the sweep -- DAY2's
      run totals are [15,16,16,16,16,16] and p8 is most of the 15.
      WHY IT MATTERS BEYOND DAY2: a gate that flips is worse than a gate that is
      wrong, because a wrong gate can be re-scoped and a flipping one cannot be
      measured against. Any future change to DAY2 will be read through p8's coin
      flip unless this is settled first.
      WHERE TO START, and NOT with wording: the rule is `cadence_ok` in the shared
      criteria prose -- "is the TRIGGER evaluated daily? Judge only how often the
      behaviour is checked, not how long the consequence lasts" -- and it is stated
      ONCE for both cadences, with the period substituted from the item's `cadence`
      field. So the prose is identical for WK1, which never errs. Read p8's answer
      first and establish what about it is borderline; the difference between the
      daily and weekly items may be in the ANSWERS rather than the rule.
      CONTROLS: WK1's 20 refusals at 100% and DAY1's 26 at 92% both depend on this
      gate firing correctly. A change that relaxes it risks two items to fix two.
      TOTAL COST, now that all four are measured: 82 refusals across the family,
      11 of them wrong, and every one costs a full 4-point item because the check
      gates. That is the largest single pool of error in handout 2.

- [ ] Q21. **NR: a 4-point GATE running at 71% precision.**
      POOLED, 2026-09-01, AND THE HEADLINE NUMBER SURVIVES. `you_arrange_it` is
      refused 66 times across the twelve pooled runs with 18 of those in cells
      that scored wrong -- 72% precision, against the 71% this entry was opened
      on. Doubling the sample moved it by a point, so the gate really does run at
      roughly three refusals in four being right, and that was not an artefact of
      reading one column.
      ITS TWO WRONG CELLS ARE NOW SUBGOAL Q34's: NR/p4 and NR/p20 are both rows
      gold passed in SILENCE and we deduct on every run. NR/p20's readout says
      our refusal is defensible -- not feeling tired is a natural consequence the
      student does not arrange, which is what the gate asks -- so the precision
      figure and the false-positive question point at the same cells from
      different directions, and neither is a threshold problem.
      MEASURED ON THE APP 2026-08-29, the first time NR has ever scored there --
      it was one of the seven items `forbid` made unrunnable (subgoal Q14). OLX
      16/18, runs [14,15,15,16,16,16], against the python's 15/18. Era checked, 0 of
      20 cells never agreeing, so `forbid` -- the primitive that broke the item --
      computes identically on both engines. Direction 8 over / 14 under, so NR
      under-credits and is NOT a `requires` candidate (subgoal E15).
      THE GATE'S PRECISION REPRODUCES: `you_arrange_it` refused 32 times with 8 in
      wrong cells (75%) on the olx against 34/10 (71%) on the python. Same
      instrument, same imprecision, both engines -- so whatever is wrong with it
      is in the RULE, not in either implementation, which is what a structural fix
      needs to be true of.
      AND SO DOES THE ORTHOGONALITY of the four structural gates:
      `names_behavior` 6/0, `names_stimulus` 12/0, `contingent` 14/0,
      `follows_behavior` 13/0 -- 45 refusals between them, ZERO in a wrong cell.
      Read that with subgoal Q20: those four are doing no discriminating work here
      at all, while the fifth gate on the same sheet is the most expensive
      instrument on the item.
      `phrased_directly` IS NOT THE LEVER, and the precision table below already
      says why -- advisory, cannot deduct. It is the largest single channel on the
      olx too (60 refusals, 12 in wrong cells), and every one of those 12 is
      CO-OCCURRENCE: a slot that cannot deduct cannot have caused the miss. Noted
      because the size of the number invites exactly the wrong conclusion.
      NR RECORDS 15/18, runs [14,14,15,15,15,16], and carries the worst MAE (0.50)
      and bias (-0.39) in the sweep. A ONE-cell drop from the ledger's previous
      16/18, which was itself a six-run figure (`nr_barrier2`), so the comparison
      is like-for-like apart from the prompt change. Under-credit 16 against
      over-credit 9.
      NOT 14/18: that figure came from the sweep summary's `exact` column, which
      reports the PUBLISHED MEDIAN RUN's count. The ledger records
      `totals[n//2]`, the upper median of the six run totals, and that is the
      canonical number. The two differ on half the items swept so far.
      THE STRUCTURAL FINDING, and it is the whole subgoal: `you_arrange_it` GATES.
      pts=None, gates=True, so ONE unmet verdict zeroes the entire 4-point item. It
      is refused 34 times with 10 of those in wrong cells -- 71% precision -- which
      makes it simultaneously the most expensive instrument on the sheet and one of
      its least precise. Five other slots on this item are 100% precise;
      `barrier_is_not_this_type`, converted to a declaration today, is 6 refusals
      and 100%.
      PRECISION RANKING, the order to work in:
          targets_goal_behavior  13 refusals   62%
          you_arrange_it         34 refusals   71%   <-- and it GATES
          demonstrates_type      29 refusals   79%
          phrased_directly       64 refusals   80%   advisory, cannot deduct
      THE FOUR STABLY WRONG CELLS, each with a different cause:
        p20  gold 4.00, ours 0.00, 6/6. The gate fires and gold's feedback is
             EMPTY -- gold gave full credit and said nothing, so there is no stated
             objection to read. Pure gate false-positive, and the most expensive
             single error in the sweep.
        p11  gold 2.00, ours 0.00, gate fires 4/6. Gold docks TWO points, saying
             "This is an example of NP" -- so gold and we AGREE the type is wrong
             and disagree only about the PRICE. This is a charge-size mismatch, not
             a judgement one.
        p4   gold 4.00, ours 2.00. `demonstrates_type` refused 6/6, gold silent. It
             is COMPUTED, via `expect` from `observed_type`/`stimulus_move` against
             REQUIRED_MOVE's `taken_undesirable`, so the lever is the PICK, not
             prose -- check what the model answers for the move before touching any
             wording.
        p3   gold 0.00, ours 4.00. Every SCORING check passes. Gold objects that
             what is taken away "has to be easily controllable", and no check on the
             sheet asks that. This belongs to subgoal Q20's class, not here.
      THE LEAD PROPOSAL WAS WRONG, AND THE FOURTH TYPE ITEM KILLED IT. I proposed
      making `you_arrange_it` carry points instead of gating, on the grounds that
      gold prices a wrong-type answer at 2 of 4 while our gate takes 4. Then PP and
      NP landed. Across all four items that share this gate:
          PR   18 refusals   100% precise
          PP   18 refusals   100% precise
          NP   27 refusals    89% precise
          NR   34 refusals    71% precise
      PR and PP are PERFECT items -- PP is 18/18 with a zero spread, the only such
      item in the sweep -- and both depend on this gate firing 18 times without a
      single error. Removing the gate would damage them to fix NR. Do not do it.
      WHAT THE FOUR POINTS ACTUALLY SHOW is a monotone relationship: the more often
      the gate fires, the less precise it is (18 -> 100%, 27 -> 89%, 34 -> 71%).
      The instrument is sound where it fires rarely and unreliable where it fires
      often, which points at NR's ANSWERS tripping a threshold rather than at the
      threshold being wrong. So the question is why NR's cells reach it twice as
      often as PR's and PP's -- its `taken_undesirable` framing, or its prompt --
      and not whether the gate should exist.
      PROPOSALS, in leverage order, none of them a wording change:
        1. ASK WHY NR FIRES TWICE AS OFTEN. Compare the cells where NR's gate fires
           against PR's and PP's, which never misfire. NP at 89% is the useful
           middle case: three wrong refusals, few enough to read individually.
        2. p4 is arithmetic, not judgement. Read the picks.
        3. p3 goes to subgoal Q20.
        4. DO NOT TOUCH `phrased_directly` despite 64 refusals and 7 drifting cells
           -- the largest real instability in the sweep. It is advisory on this item
           and cannot deduct, so its correlation with wrong cells is a marker of
           hard cells, not a cause.
      ALREADY DECLARED: NR carries "CHARGE-ONCE OLX ONLY (barrier_is_not_this_type,
      demonstrates_type) cost less together on the olx". Read it before changing
      either of those two, since the charge interaction is the declared part.

- [ ] Q19. **The LATER-BOX gradient, corpus-wide. Read this before any numbered slot.**
      GOLD-SIDE CONFIRMATION, added 2026-08-31 from E30's slot accounting and E34's
      refutation. Everything below measures OUR refusal rate by box index. These
      six cells show the GRADER's itemisation on the same responses, charging both
      boxes where we charge one:
          1a/p1   gold all four week slots   we fail baseline_week only
          Q4a/p14 gold both antecedents      we fail antecedent_2 only
          Q4b/p4  gold both behaviors        we fail behavior_2 only
          Q4c/p9  gold both consequences     we fail consequence_2 only
          Q6/p8   gold all four c-slots      we fail two
          Q2/p7   gold inversion + 3 reasons we fail the reasons only
      3/p15 BELONGS HERE TOO, and it adds instability to the picture: gold gives
      0.0 -- "did not provide two specific examples" -- and we credit example_1,
      scoring 3.0 in four runs and 0.0 in two. So the first box is credited AND
      the judgement wobbles, on the same cell. Its comment names no amount, so
      E30's accounting never saw it; the total is the only evidence.
      AND THE CONTROL IS IN THE SAME ITEMS: 1a/p15, Q4a/p20 and Q4b/p8 carry the
      IDENTICAL gold charge and we fail every member, correctly. So the gradient is
      not a ceiling on what the sheet can express -- it is where the first box gets
      the benefit of the doubt and the later one does not.
      Placed ahead of the item-specific subgoals because six of them are about a
      numbered box, and this says which part of that is one problem and which is
      six. Measured 2026-08-28 over the python sweep's first seven items, 6 runs each.

      Q4a/p14 IS THE CELL WHERE THE GRADER'S REASONING IS VISIBLE, recorded here
      2026-09-01 after Q24 read it out. It is already in the list above; this is
      the mechanism behind that line.
          gold 1.0, and the comment is PLURAL: "-4pts: Examples are not
          antecedents. Remember that antecedents happen before the UTB is
          exhibited." Four points on a five-point item is BOTH 2-point slots.
          box 2  "{{corpus:Q4a/p14:second:21:84:sha=2da3c0df2d6f:shape=S9-0a2020202020202020202020202020202020,Cffc000}} well" -- a consequence, and the student's own
                 "afterwards" settles it. WE AGREE: `antecedent_2` is
                 `wrong_kind` in 12 of 12 observations across both sides, so the
                 whole 2-point gap is box 1.
          box 1  "{{corpus:Q4a/p14:first:20:66:sha=bcd1a76b331c}} rot" -- we
                 credit it, gold does not.
      AND NO BOX-1 RULE CAN BE WHAT SEPARATES THEM, which is the finding that
      sends this cell here rather than to an antecedent_1 subgoal. On the SAME
      utb -- lack of exercise -- gold gives full marks to two cells of the same
      shape, and we score both correctly today:
          p10  gold 5  "{{corpus:Q4a/p10:first:18:76:sha=4cd6a53ced82:shape=A1,A19}}"
          p17  gold 5  "Feeling {{corpus:Q4a/p17:first:7:31:sha=4ac4f9df70c1}} workout"
      All three are the same bidirectional state loop: not exercising leaves you
      tired, unfit and resultless, and those states then keep you from
      exercising. A rule refusing a state the behaviour produces breaks p10 and
      p17 to fix p14.
      SO THE LIKELIEST ACCOUNT IS THIS SUBGOAL'S OWN: the grader saw the
      unmistakable "afterwards" in box 2 and docked the pair, rather than making
      a separate finding about box 1. That is the gradient with the reasoning
      showing.
      STATED AS AN INFERENCE, because it is one. What is MEASURED is the p10/p17
      contrast -- same shape, same utb, opposite gold. Why the grader charged
      both boxes is read off a comment, not observed, and a later reading that
      explains the same three cells differently should be preferred if it
      predicts more than this one does.
      TWO CLAIMS, AND ONLY ONE IS UNIVERSAL.
      (1) VOLUME rises with box index, everywhere, no exceptions:
            Q1  reason_2 16 -> reason_3 47
            Q2  reason_1 21 -> reason_2 22 -> reason_3 47
            Q4a antecedent_1 23 -> antecedent_2 34
            Q4b behavior_1  23 -> behavior_2  52
            Q4c consequence_1 6 -> consequence_2 19
            Q5  example_1  18 -> example_2  26
          We refuse the later box roughly twice as often as the first.
      (2) PRECISION -- how often a refusal lands in a cell that scored RIGHT --
          collapses on only TWO items:
            Q4b box1 100% -> box2 67%
            Q4c box1 100% -> box2 63%
          and is FLAT or BETTER on the rest: Q4a 74/71, Q5 67/69, Q2 62/59/57,
          Q1 75 then 83 on the third box.
      SO THE SHAPE IS NOT "the second box is judged badly". It is "we refuse the
      later box far more often, and on Q4b and Q4c those extra refusals are wrong".
      An earlier reading of this data as "first box clean, second box carries the
      failures, four items, one shape" was WRONG: Q4a's first box has 6 wrong-cell
      refusals and Q5's has 6. Only Q4b and Q4c have a genuinely spotless first box.
      THE OBVIOUS INNOCENT EXPLANATION IS PROBABLY THE RIGHT ONE for claim (1):
      students' second examples really are weaker -- they run out of material --
      so refusing the later box more often is correct behaviour, and the flat
      precision on four of six items says exactly that. Do NOT try to flatten the
      volume gradient. The thing to explain is the precision drop on two items.
      ONE HYPOTHESIS ALREADY DEAD, so nobody re-runs it: the CONTINUED placeholder,
      which used to put the whole paper block in the first box and "(continued
      above)" in the rest. `build_jobs` replaced that with real per-box
      reconstruction, its docstring says so in the past tense, and the string
      appears in no recorded evidence in this sweep.
      WHERE TO LOOK, given the above: Q4b and Q4c are the two items whose first box
      is never wrong, and both are `*_1`/`*_2` pairs judged by ONE shared rule.
      Q4b's failures localise further to a single option value (`not_doing`, see
      subgoal Q18) -- check whether Q4c's do too, because a shared cause across the
      only two affected items is worth more than two item fixes.
      AND CHECK IT AGAINST THE OLX COLUMN before acting: if the gradient is the
      same on both sides it is the prompt or the corpus, and if it differs it is
      the scorer. That comparison costs nothing once the app sweep lands.

      == 2026-09-01: BOTH OF THOSE WERE DONE, AND THEY ANSWER DIFFERENTLY ==
      THE OLX COLUMN SAYS IT IS NOT THE SCORER. Volume and precision track each
      other closely on every item where both sides expose the slots:
          Q4a  python 24@75% -> 33@72%      olx 23@73% -> 32@65%
          Q4b  python 23@100% -> 52@67%     olx 26@92% -> 52@67%
          Q4c  python  6@100% -> 18@66%     olx  7@85% -> 20@55%
          Q5   python 18@66% -> 27@66%      olx 18@66% -> 28@60%
      By this entry's own rule that makes it the PROMPT OR THE CORPUS, and rules
      out an engine-side fix. (Q1 and Q2 show zero volume on the olx side: their
      slots are cover-grouped and do not appear under these names, so the
      comparison covers four items, not six.)
      AND THE SHARED CAUSE IS REAL: BOTH ITEMS LOCALISE TO `wrong_kind`.
          Q4c.consequence_2   wrong_kind 15 refusals, 15 in wrong cells
                              absent 12, duplicate 11 -- ZERO in wrong cells
          Q4b.behavior_2      wrong_kind 89 refusals, 34 in wrong cells
                              absent 15 -- ZERO in wrong cells
      `absent` and `duplicate` never land in a wrong cell on either item. That is
      the shared cause this entry asked for, and it is one option value.
      BUT THE STATISTIC THAT FOUND IT IS MISLEADING, WHICH IS THE REAL FINDING.
      "Refusals in wrong cells" counts a refusal against us whenever the CELL is
      wrong -- including when the refusal is CORRECT and the cell is wrong for
      the opposite reason. Decomposed per cell, the two items split the same way:
          Q4c  p9  gold 1.0, ours 3.0, 12 obs -- we are LENIENT. Gold charges
                   BOTH consequences; our box-2 refusal is RIGHT and incomplete.
                   Crediting box 2 moves it to 5.0, further from gold.
               p12 gold 5.0, ours 3.0,  3 obs -- we are STRICT. Crediting fixes it.
          Q4b  p12 gold 5.0, ours 3.5, 12 obs -- STRICT, crediting fixes
               p13 gold 5.0, ours 3.5,  8 obs -- STRICT, crediting fixes
               p4  gold 2.0, ours 3.5, 12 obs -- LENIENT, crediting is worse
               p20 gold 2.0, ours 3.5,  1 obs -- LENIENT, crediting is worse
               p17 gold 5.0, ours 2.0,  1 obs -- STRICT, crediting insufficient
      SO THE BOX-2 PRECISION COLLAPSE IS TWO PHENOMENA WEARING ONE NUMBER:
        * cells where our box-2 refusal is WRONG -- gold credits the second box.
          Every one of these is a not-doing: Q4b/p12 and Q4b/p4 are declared
          under B_NOT_ACTIVE, Q4b/p13 is subgoal Q18's live cell, Q4c/p12 is the
          same shape. This is a GOLD DISAGREEMENT, not a rule defect.
        * cells where our box-2 refusal is RIGHT but the cell is still wrong
          because gold ALSO charged box 1 -- Q4c/p9, Q4b/p4, Q4b/p20. These are
          this subgoal's own gradient, already in the list above.
      NEITHER IS FIXED BY LOOSENING `wrong_kind`, and loosening it would break
      the gradient cells in the direction they are already wrong.
      THE RECOMPUTED NUMBER IS ZERO, NOT FOUR. `measured.py --refusals ITEM
      [SIDE]` now counts refusals against gold's own itemisation, and the four
      cells named above as "refusal WRONG" turn out to be UNDECIDABLE rather than
      contradicted: gold gave them full marks and wrote NOTHING, so its
      itemisation has no opinion to contradict us with. Corrected here because
      the estimate of four was made by hand an hour earlier and the tool
      disagrees with it:
          Q4a  antecedent_2 33 refusals: 18 gold agrees, 0 CONTRADICTED, 15 undecidable
               antecedent_1 24 refusals:  6 gold agrees, 0 CONTRADICTED, 18 undecidable
          Q4b  behavior_2   52 refusals: 36 gold agrees, 0 CONTRADICTED, 16 undecidable
               behavior_1   23 refusals: 18 gold agrees, 0 CONTRADICTED,  5 undecidable
          Q4c  consequence_2 18 refusals: 18 gold agrees, 0 CONTRADICTED, 0 undecidable
      NOT ONE REFUSAL ON THESE ITEMS IS CONTRADICTED BY A GOLD COMMENT. Every
      refusal gold has an opinion about, gold agrees with. So the box-2 precision
      collapse is not evidence of a rule defect at all -- it is entirely (a)
      correct refusals in cells that are wrong for another reason, which is this
      subgoal's gradient, and (b) cells where gold awarded full marks silently,
      which is subgoal Q31 and whose only evidence is the TOTAL.
      THAT REDIRECTS THE WHOLE SUBGOAL. There is nothing here for a wording
      change to fix, because there is no cell where the grader said in writing
      that a refusal of ours was wrong. What is left is Q31's question -- whether
      a silent full-marks row is a judgement we should defer to -- and the
      gradient itself, which is about gold charging box 1 as well, not about our
      box-2 refusals being unjustified.

- [x] Q1. **Q3's `action` criterion.** The clearest target on the board. Five
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
      closed entry -- they are subgoals Q9, 10 and 11, one per criterion, because
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

- [ ] Q2. **2a over-credits `hows_given`: one rule, five cells, 29 of 29 errors.**
      2a/p16 MOVED HERE 2026-09-01 from Q31, which closed. Q31's own text said it
      belonged to this entry -- "the item's usual over-credit rather than this
      pattern" -- and nothing had acted on that, so closing Q31 would have
      orphaned it. Gold gives 4.0 with NO comment and we score 6.0 in all twelve
      pooled runs, which is this subgoal's shape exactly: a stable over-credit on
      2a. It differs from the other four only in gold's silence, and silence is
      Q34's variable, not this one's.
      Was "Handout 3's 2a, 15/20 with runs [15,15,15] ... six runs first, then read
      the failing checks". The six runs are done and the checks are read, so this
      entry is now the diagnosis rather than the plan. A NEW subgoal was asked for;
      this is it, folded into the existing 2a entry rather than opened beside it,
      because two subgoals on one item is how the same work gets done twice.
      STABLE, NOT NOISY -- the question the old entry asked. Six runs give
      [15,15,15,15,15,16] and the previous six-run figure was also 15/20, so the
      flat three-run median was not hiding movement. The item is reliably 15/20.
      EVERY ERROR IS ONE ERROR. 29 over-credits, ZERO under-credits, and the count
      profile is a single line:
          said 2, scored 6 against gold 4      x29
      That is five cells times six runs. `verdict` is unmet once in 120 observations
      and never wrongly; no scoring slot drifts. There is nothing else on this item.
      THE SLOT-LEVEL EVIDENCE, added 2026-08-31 from E30's accounting, and it says
      what the count profile could not: the over-credit is ONE UNCHARGED SLOT.
      Gold docks a single `how_*` slot on each cell -- "your third sentece does not
      explain how your plan was successful", "need more explanation on how it was
      or was not successful" -- and WE DOCK NOTHING. Gold 4.0 against our 6.0,
      identically, on 2a/p1, 2a/p13, 2a/p14 and 2a/p15. Written out in full
      because a cell-level search for "2a/p13" is how these get found, and
      "p13" alone is invisible to it.
      FOUR CELLS, NOT FIVE, at slot level. This entry's "five cells" counts the
      cells whose TOTAL is wrong; only four have a gold comment that itemises its
      deduction, so the fifth cannot be read this way. Both numbers are right about
      different things, and the discrepancy is not a defect -- but a reader
      comparing them needs the reason, which is why it is written here.
      SO THE TARGET IS NAMED: whatever rule credits a `how_*` slot that gold
      charges. The four comments agree on what gold wants -- an explanation of HOW
      the plan was or was not successful -- and the count profile says our `verdict`
      slot is sound, so the disagreement is entirely in `how_1`/`how_2`.
      THE MECHANISM, exactly: `counts` declares `hows_given` over `how_1` and
      `how_2`, each worth 2.0, with `verdict` worth 2.0 for a total of 6. The model
      answers `hows_given` = 2 in EVERY run of all five cells, both hows are
      credited, and the item pays 6. Gold pays 4 -- it credits ONE how.
      GOLD SAYS WHY, on four of the five, and says the same thing each time:
          p1   "-2 pts: missing one sentence. Your third sentece does not explain
                how your plan was successful."
          p13  identical wording
          p15  "... Your second sentece does not explain how ..."
          p14  "-2 pts: need more explanation on how it was or was not successful"
          p16  silent
      So gold is not counting SENTENCES, it is counting sentences that EXPLAIN HOW.
      The student wrote the required number of sentences and one of them does not do
      the job, and our count accepts it. That is a definition problem in what
      qualifies as a `how`, not an arithmetic one -- the counted members are derived
      from the count, so the count is the only place to fix it.
      DO IT AS A COUNT RULE, NOT PROSE ON THE MEMBERS: `how_1`/`how_2` are derived
      from `hows_given` and are never asked, so text attached to them cannot reach
      the model. The `counts` guidance is what it reads.
      ALL FIVE MOVE TOGETHER, which is the risk and the opportunity: they fail
      identically in every run, so a change either recovers five cells or none.
      15/20 -> 20/20 is the ceiling if the rule can be stated; there is no partial
      credit to collect. CONTROLS: the fifteen cells that already pass, all of which
      answer `hows_given` and would be exposed to a stricter definition.
      == 2026-09-02: STRUCTURAL ATTEMPT MEASURED. REVERTED. NOT REFUTED. ==
      The attempt was to UN-DERIVE `how_1`/`how_2` -- drop the count, ask each box
      directly -- on the reasoning that this entry's own DEDUCT guidance already
      described both shapes the graders charge and the count still came back 2 on
      every charged cell, because an aggregate answer never has to confront a
      particular box. The graders judge per box and say which one ("your third
      sentece", "your second sentece") against three labelled fields on screen.
      IT ALSO BROKE THE FIXTURE, which is the first thing to know. Handout 3's
      answer is ONE prose block and its boxes are rebuilt by score.py's
      counted-group distribution (score.py:469): it reads the count slot's
      evidence, pulls the quoted spans out and deals them to the members, writing
      the placeholder `f"{raw_n} found"` where there are fewer spans than the
      count. Removing `counts` removed that distribution, so five cells' boxes
      became the literal string "2 found" -- p4, p13, p14, p19 and p20 -- and the
      sweep graded a placeholder as if the student had written it. This entry's
      claim that "ALL FIVE MOVE TOGETHER" is also wrong for a per-box rule: it is
      true of a count, which is one judgement, and false once each box is asked.
      WHAT THE 15 UNCORRUPTED CELLS ACTUALLY MEASURED, which is the salvageable
      half. On those cells the baseline is 12 of 15 and the attempt scored 10 of
      15 -- still a net loss, but of 2 cells rather than the 5 the raw 10/20
      suggested:
          p15  FIXED, 4.0 in 5 of 5. "{{corpus:2a/p15:how1:0:24:sha=76aa568a019e}} screentime" --
               charged correctly, and the cleanest of the five targets.
          p16  unmoved at 6.0; p1 wobbles 6/4 and misses at the median.
          p2, p12, p18  BROKEN controls, each charged one box.
      AND THE BROKEN CONTROLS NAME THE DEFECT IN THE CRITERION. All three failed
      on a first box that reports the outcome WITH ITS DATA: "{{corpus:2a/p2:how1:0:88:sha=ed452dcd5f5a:shape=S4-0a202020202020}} data",
      "{{corpus:2a/p12:how1:13:115:sha=a8c1c607af1f:shape=S11-0a202020202020}} days", "{{corpus:2a/p18:how1:19:72:sha=ffdeb08c54e2:shape=S7-0a202020202020}} data". The criterion written for the attempt -- must give a
      cause, not restate the outcome -- charges those, and gold credits them. The
      old guidance says why in as many words: "a verdict that cites the data as
      its evidence ... covers the verdict and both explanations". Citing the data
      IS an explanation on this item.
      SO THE NEXT FORM OF THE RULE IS NARROWER, and p15 versus p2/p12/p18 is the
      pair that fixes it: a box is absent only when it neither gives a cause NOR
      cites the data or the magnitude. p15's "{{corpus:2a/p15:how1:6:24:sha=9e486c188464}} screentime"
      cites neither; p13's "{{corpus:2a/p13:how2:0:46:sha=446c357de928}}"
      cites neither. All three broken controls cite the magnitude.
      PREREQUISITE DONE 2026-09-02: THE FIXTURE NOW SURVIVES THE CHANGE. The
      builder already had its own dealing logic -- `agreement_app.
      distribute_counted`, which strips what the non-counted fields claimed and
      deals the remaining sentences into the first n boxes as contiguous runs, so
      it never depended on the evidence FORMAT. What it did depend on was
      `counted_members()`, i.e. on the live rubric: with no `counts` group every
      member field fell through to `ev.get(comp)`, the placeholder. The dealing
      groups are now declared in the FIXTURE layer instead, as `dealt` in
      agreement_app.JOBS -- 2a's hows_given over (how_1, how_2) and item 3's
      changes_given over (example_1, example_2), the only two in use -- named by
      scorer COMPONENT, the same vocabulary `from_scorer` already uses. Verified
      byte-identical: 240 fixtures across six handout-3 items, both harnesses,
      unchanged hash. And verified decoupled: dropping 2a's `counts` from the
      rubric now leaves every box exactly as it was.
      SO THE RETRY IS UNBLOCKED, and the rule to try is the narrower one above --
      absent only when a box gives neither a cause nor the data/magnitude. Note
      that removing `counts` still changes the PYTHON side's scoring, so the
      retry is still a real experiment on both engines; what it no longer does is
      change the input underneath them.
      == 2026-09-02, SECOND ATTEMPT: MEASURED AND KEPT. 15/20 -> 17/20. ==
      The narrower rule is in place and swept at six runs on BOTH sides, 240
      calls: python [17,17,17,18,17,17], olx [17,17,18,18,17,17], pooled median
      17 of 20. Recorded as `q2_narrower_python` and `q2_narrower_olx`. The
      fixture preflight passed this time, which is what the first attempt lacked.
      THE OUTCOME WAS PRE-REGISTERED, cell by cell, before the rule was written,
      and it came out exactly: p13 and p15 fixed, p1/p14/p16 still wrong, all
      thirteen controls held -- including p6, the one flagged in advance as the
      likeliest casualty. Zero CONTRADICTED refusals on either side, so nothing
      we now charge is a slot gold's comment denies.
      WHAT THE RULE IS: a How box is met on EITHER ground -- a cause or
      circumstance, OR the change reported with its size, a figure, a comparison
      against the earlier week, or the data. It is absent only when it offers
      NEITHER. That second ground is what the first attempt got wrong: it charged
      boxes reporting the outcome WITH its magnitude, and the graders credit
      those. p15's "{{corpus:2a/p15:how1:6:24:sha=9e486c188464}} screentime" and p13's "{{corpus:2a/p13:how2:0:46:sha=446c357de928:shape=S2-0a202020202020}}" offer neither, and both are now charged.
      THE THREE THAT REMAIN HAVE THREE DIFFERENT CAUSES, which is the useful
      part -- none of them is the how rule being too loose:
          p1   THE OFF-TOPIC CLAUSE IS NOT FIRING. how2 reports a bodily effect
               of NOT sleeping, and the plan was to sleep more, so gold wrote
               "your third sentece does not explain how your plan was
               successful". The box does carry a circumstance, so the two-way
               test credits it, and the desc's third clause -- absent when what
               the box reports bears on something other than the plan working --
               charges it in 0 of 12 runs. That clause is the next thing to work
               on, and it is a clause, not a new rule.
          p14  A VERDICT-SLOT INSTABILITY, not a how-slot miss. Its verdict box
               is "{{corpus:2a/p14:verdict:0:104:sha=f83968a50add:shape=S12-0a202020202020202020202020202020}} Three", and we fail
               `verdict` in 4 of 12 runs -- short of a median, so the cell scores
               6. Gold's comment is worded as a how-charge but its substance is
               the unsettled verdict, so the 2 points plausibly belong to
               NO_VERDICT. This belongs with subgoal Q35, which owns variance.
          p16  GOLD CHARGED 2 SILENTLY. Both boxes give clean circumstances --
               "when I had free time", "{{corpus:2a/p16:how2:61:107:sha=9a8cf65b1bf8:shape=S8-0a202020202020202020202020202020,A29}}" -- and nothing in the rubric as written charges either.
               Which box gold meant is unrecoverable, and every other charged
               cell on this item names one ("third sentece", "second sentece") or
               turns on the verdict. This is the mirror of the silent-full-marks
               pattern and a gold-versus-rubric question, not a rule defect.
      SO THE CEILING CLAIM IN THIS ENTRY IS REVISED. "15/20 -> 20/20 is the
      ceiling if the rule can be stated" assumed all five cells were one rule
      failing. They were not: two were, one was a clause of it, one is the verdict
      slot, and one is a silent gold charge nobody can localise.
      == 2026-09-02, THIRD ATTEMPT: THE p1 CLAUSE, AS A CONJUNCTION. 17 -> 18. ==
      python [18 x6], olx [19,18,18,18,18,19], pooled median 18 of 20. Recorded
      as `q2_conj_python` and `q2_conj_olx`. 240 calls.
      THE CLAUSE HAD TO BE A CONJUNCTION, and the first answer given here was that
      no clause could work at all -- recorded because the reasoning was wrong in
      an instructive way. p1's two boxes look identical on every single feature: a
      bodily or personal STATE, attributed by a causal link to the sleep
      behaviour. Direction alone does not separate them either, because p9 is
      credited on a not-doing box with an unqualified success verdict. What
      separates them is the PAIR: charge only when the payload is a state rather
      than the behaviour AND the condition is the behaviour NOT being done. p1's
      how1 is a state in the DOING direction, so it is met; p9's how2 is
      not-doing but its subject is the behaviour, so it is met. Neither half
      alone survives the corpus; together they fit every box on the item. The
      claim that the boxes were "structurally indistinguishable" was true only of
      single-feature predicates, and the user's question is what exposed it.
      IT CHARGES THE BOX GOLD NAMED, which is stronger than the total. Gold's
      comments are positional and all three fixed cells now match, 12 of 12 runs
      on BOTH sides: p1 how_2 against "your third sentece", p13 how_2 against
      "your third sentece", p15 how_1 against "your second sentece". Zero
      CONTRADICTED refusals on either side.
      TWO CELLS REMAIN AND NEITHER IS THE HOW RULE:
          p14  verdict fails 3 of 12 -- short of a median, so the cell scores 6.
               Gold's comment reads as a how-charge but its substance is the
               unsettled verdict ("{{corpus:2a/p14:verdict:0:42:sha=7ec74c73e177}}
               rate"), so the 2 points plausibly belong to NO_VERDICT. This is
               variance, and subgoal Q35 owns variance.
          p16  gold charged 2 SILENTLY and both boxes carry clean circumstances.
               Nothing in the rubric as written charges either, and which box
               gold meant is unrecoverable. A gold-versus-rubric question.
      SO THE HOW RULE IS DONE at 18/20. What is left on this item is one unstable
      verdict slot and one silent gold charge, and neither is reachable by
      editing the how prose. ASK BEFORE CLOSING.
      IT IS NOW CAUGHT BEFORE THE CALLS, not after.
      `enforcement.check_fixture_boxes_hold_the_students_words` requires every
      scorer-sourced box to appear in the participant's transcribed answer, and
      `agreement_app.check_fixture_is_not_corrupt` runs it as a PREFLIGHT in both
      sweep harnesses, so a corrupt fixture costs nothing instead of 120 calls.
- [x] Q3. **Re-measure the 3-run items at six runs, cheapest-first.** CLOSED
      2026-08-28 as SUPERSEDED, at the user's direction, not as finished:
      equivalence subgoal Q2 sweeps every item at six runs on both sides, so the
      twelve remaining three-run numbers are re-measured by construction rather
      than by a separate campaign. Running both would pay twice for one result.
      STILL AT THREE RUNS when this closed, so this is the list to check the
      sweep against: 1a, 1b, 1c, D1, D2, NP, PP, Q4c, Q5, Q6, T1, T2. The
      ledger's `runs` field per item is the test -- if any of the twelve comes
      out of the sweep at fewer than six, the need returns and this reopens.
      WHAT IT ESTABLISHED BEFORE CLOSING, worth keeping: six runs mostly SHARPEN
      three-run rates rather than overturn them. Q1 and Q2 were re-measured here
      and neither actually moved -- every moved cell was already unstable, and
      the fingerprint had flagged them because `expand_counted` moved, not
      because any arithmetic changed. That is the reason a three-run number is
      treated as coarse rather than as wrong.
      Original plan, for the record: H1: Q1, Q2,
      Q4c, Q5, Q6. H3: 1a, 1b, 1c, 2a, 2b, 3. H2: PP, NP, T1, D1, T2, D2 -- the
      four definition items sit at 18/18 and are the least likely to move, so
      they go last. 120 calls each; do not batch more than two items at once,
      because two sweeps sharing the endpoint halved throughput today.
      IN PROGRESS. The six items the scorer fingerprint flagged are being swept
      first, two at a time, into `scorer_fix_6run`: Q1 was **16/20** at the old
      [SUPERSEDED 2026-08-28: Q1 now records 17/20 and Q2 16/20 from the two-sided
      sweep; the figures in this closed entry are the state when it was written.]
      (runs [15,16,16,16,17,17], was 17/20 on three; now 17/20 at the rewritten
      prompt -- see subgoal Q6) and Q2 measured eighteen of twenty then (runs
      [16,17,17,18,18,18], was 17/20 on three) are recorded, both probes filed,
      both verdicts permitted. Neither item actually moved: every moved cell was
      already unstable and the six-run rates mostly SHARPEN the three-run ones
      (5/6 where three runs said 3/3, 1/6 where they said 1/3), which is the
      expected result -- their `counts` machinery was working all along via the
      rubric key, and the fingerprint flagged them because `expand_counted`
      moved, not because arithmetic changed. Q4b and 2a are running; 2b and 3
      are next.
- [x] Q4. **The leakage detector's shared-prose blind spot.** Found twice today:
      the word check suppresses any word appearing in ANOTHER authored block, so
      prose duplicated across items is invisible to it -- the whole of
      `_MOVE_RULE` was unchecked while it sat in four prompts, and both times a
      block was edited an unrelated block lit up. Compute the "ours" set from
      DISTINCT prose rather than per-block. Expect a fresh backlog to triage.
      FIXED AND IT CAUGHT REAL LEAKAGE ON ITS FIRST RUN. `elsewhere` is now
      computed from prose the block does NOT contain, at SENTENCE granularity so
      partial sharing is caught too, not only exact duplicates. Measured before
      the fix: 139 of 301 authored blocks carried a full text that also appears
      verbatim in another block, and 114 sentences sat in more than one block --
      the four-type operant definition in twelve. All of that was exempt.
      Findings went 26 -> 69, the new 43 collapsing to 7 distinct prose shas.
      Four were vocabulary. THREE WERE REAL:
      p14/NR's "{{corpus:NR/p14:nr:52:83:sha=658c91c9eff0}} exercise" had become our canonical
      negative example, "a lock that opens when the student arrives", in blocks
      shared by DAY1/DAY2/NR/WK2; p4's "scroll through TikTok" had become "I will
      read rather than scroll". Both are CELLS WE SCORE. Rewritten, not excused.
      The SAFETY block was wrong on its own terms as well as leaky: an enumerated
      list -- food, sleep, medical care, exercise-as-punishment -- where gold has
      a principle (the graders flagged whatever could harm the student and left
      the score at full), plus a grader's note quoted verbatim, which is where its
      shared vocabulary came from. Restated as the principle.
      A SECOND BUG surfaced with it: `--review` built its known set from
      `findings()` only, so a WORD finding could block every sweep with no way to
      file a verdict for it. It never bit while the word check was suppressing
      duplicated prose. Fixed to search both.
      OPTION 2 TAKEN: prompts are clean now, the eight handout-2 items read STALE
      PROMPT, and the ~960 calls to re-measure them are deferred rather than
      spent. The ledger tells the truth about what is unmeasured.
- [x] Q5. **Q4b/p12's declared divergence.** Accurate today, but its stated reason
      says we never matched gold there and cli_v7/cli_v8 both scored it 3/3. A
      declaration whose reason is false is a declaration that will be trusted
      for the wrong reason.
      CORRECTED, and the correction found something the subgoal did not know.
      The reason said "we give 3.5, 0 of 3". Measured across every artifact that
      scored this cell: the OLX gives 3.5 in 11 of 12 runs (leak_fix 0/6,
      scorer_fix_6run 1/6 — one run reached 5.0), and the python gives 5.0 in SIX of
      six (cli_v7 3/3, cli_v8 3/3). So the cell is not unreachable at all; the two
      PATHS disagree about it, which is a different kind of finding from the one
      declared.
      AND THAT ASYMMETRY IS DECLARED NOWHERE. Q4b is absent from
      olx_prompts.SCORING_DIVERGENCES and the enforcement audit reports nothing
      for it, because the rule doing the refusing lives in GUIDANCE PROSE --
      "REJECT when the entry is not something the student did INSTEAD OF the goal
      behaviour" -- rather than in a primitive the audit can compare. A
      scoring-relevant rule enforced on one side only is precisely what that audit
      exists to catch, and it is blind to any such rule expressed as prose. That
      is a NEW gap, wider than this cell, and it is subgoal E15.
      The divergence itself stands: the olx result differs from gold for the
      stated reason, and the refusing test measured +1 cell a run against deleting
      it. Only the false claim is gone.

- [x] Q6. **Make the `reasons_given` rewrite live, then measure it.** DRAFTED,
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
      CLOSED, SUPERSEDED BY SUBGOAL 12 -- and closed as a failure, because that is
      what it was. ELEVEN configurations, ~900 calls, and the item ended where it
      started at 17/20 before subgoal Q12 took it to 18 by a different route.
      Medians measured: v1 17 (kept and committed at the time), v2 16, v3 16,
      v4 17, the per-slot SPLIT 16 and 13, split+attribute 16, split+attribute+
      explicit exclusions 16, and the criterion inside the aggregate 2/6 on its
      target cell. Three isolation probes each scored p9 WORSE than the baseline
      they were derived from.
      THE PREMISE WAS WRONG, which is the finding worth keeping. This subgoal set
      out to replace `reasons_given`'s conditional with a flat "count both kinds
      towards one total", on the reading that harms-dominance was a defect. It was
      not: it was a measured reconstruction of gold's own structure, recorded in
      the comment directly above the component, and deleting it is what cost p6
      (4/6 -> 0/6) and p16 for the rest of the day. Subgoal 12 closed by putting
      it back.
      WHAT SURVIVES: p14's fix, which v1 genuinely won (2/6 -> 6/6) and which the
      restoration kept by adding one classification clause; the mirror-pair
      analysis, which correctly describes what gold does even though no wording of
      it ever paid for itself; and three disciplines that came out of the failure
      -- §2a structure before prose, §2b profile errors by slot after every sweep,
      §2c read what is already recorded, the last now enforced by the `--write`
      hook. The full history is in drafts/q1q2_reasons_rule.md.
- [x] Q7. **Q4b's per-cell instability, which the item median hides.** Two cells
      POOLED, 2026-09-01, THE PREMISE IS GONE. This entry exists because a single
      run could not tell a stable cell from a flickering one, and both cells it
      names are now settled: Q4b/p17 scores 5.0 in 11 of 12 pooled runs against a
      gold of 5.0, and Q4b/p19 likewise. Each has ONE outlier in twelve. At six
      runs a side that read as instability; at twelve it reads as a stable
      correct cell with a rare miss.
      SO THE ITEM'S INSTABILITY IS NOT WHERE THIS LOOKED. Q4b's live cells are
      p4, p12 and p13, and all three are stably WRONG rather than unstable -- p12
      at 3.5 in every run, which is why it sits in subgoal Q34. The median was
      not hiding instability here; it was hiding a disagreement.
      CLOSE CANDIDATE, to ask about: nothing in it is live, and its
      methodological point -- that a median hides per-cell variance -- is now
      carried by QUALITY_CONTROL.md 2e and by the pooling note at the top of this
      file, both of which say it with measurements.
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
      CLOSED 2026-09-01. Both cells it names are settled at twelve pooled runs --
      Q4b/p17 and p19 each score gold in 11 of 12, one outlier apiece -- so what
      read as instability at six runs a side is a stable correct cell. Nothing in
      the entry is live.
      AND THE ITEM'S REAL PROBLEM IS THE OPPOSITE OF WHAT THIS LOOKED FOR. Q4b's
      wrong cells -- p4, p12, p13 -- are stably WRONG, p12 at 3.5 in every one of
      twelve runs. The median was not hiding variance on this item; it was hiding
      a disagreement, which is subgoal Q34's and Q19's territory.
      ITS METHODOLOGICAL POINT SURVIVES ELSEWHERE, with measurements rather than
      as an assertion: QUALITY_CONTROL.md 2e on why a median comparison
      manufactures divergences, and the pooling note at the top of this file.

- [x] Q8. **A count slot outside the rubric's `counts` records nothing.**
      `harms_listed` and `benefits_listed` store as `""` in every artifact,
      because `expand_counted` writes a verdict only for keys the RUBRIC names in
      `counts`, and `verdict_of` reads a count answer from the wrong field.
      Their values survive only in `evidence`. That matters beyond tidiness:
      those two are the operands of the rule subgoal Q6 is revising, so the whole
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
      DONE, steps 1-3 of the plan. `recorded_answer` reads a count slot's `count`
      field for the artifact; `verdict_of` -- which reads `verdict` -- is untouched
      and still does the scoring. Four slots stop recording "" in every run: Q1's
      `harms_listed`/`benefits_listed` and Q2's `reasons_listed`/`reasons_failing`.
      RECORDING IS NOT SCORING, and that is asserted rather than hoped: every
      item's scorer fingerprint was captured before the change and compared after
      -- NONE moved, so no measurement was invalidated by a recording fix.
      `check_recorded_answers_are_complete` runs the recording path over a
      synthetic sheet for every item and fails if a slot records nothing; it also
      fails if `recorded_answer` ever appears on a scoring fingerprint. Reverting
      to the old behaviour produces 9 findings. A selftest case injects exactly
      that, because a recording fault moves no score and nothing else in the
      harness would ever notice it.
      PICK slots are left recording "" BY DECLARATION: their values are in
      `answers`, so nothing is lost, and changing them would alter the recorded
      semantics of 30 slots on 13 items where readers treat "" as unanswered.
      STEP 4 NOT DONE, deliberately and not silently: `verdict_of`, `answer_of`
      and `is_satisfied` are on the scoring path and on NO item's fingerprint, so
      editing one changes scores while every item still reads current. Closing
      that re-stamps all 26 ledger entries, which is a decision about the ledger
      rather than a fix, and ten items are already stale. Carried as subgoal Q16.
- [ ] Q9. **Q3/p19: actionability grounded in measurability.** The cell names a
      MEASURED IN THE TWO-SIDED SWEEP, 6 runs, 2026-08-28. Q3 came out 18/20 at
      100% PER CHECK with a spread of ZERO cells -- so every individual verdict was
      right and the two missed cells are arithmetic on correct judgements. The
      error profile is ONE-SIDED: over-credit 11, under-credit 1, and the tool's own
      reading is "a threshold is set wrong, not unstable". Both remaining defects
      are MISSING DEDUCTIONS -- we credit what gold docks -- which is a far more
      tractable shape than Q1's and Q2's opposed-direction errors.
      AND THE DIAGNOSIS MOVED, because gold docks TWO points on each of these cells
      and we were reading the first one only:
      CONFIRMED AND STABLE, 6 of 6. gold 3.0, we predict 4.0 every run. gold's
      note is "-1 pt: For measurable, how are you tracking your goal? -1 pt: For
      action, what do you have to actively do to achieve your goal?" -- and we fail
      `measurable` in 6 of 6 runs while NEVER failing `action_oriented`. So we
      already agree with gold on the slot the subgoal is not about, and the entire
      gap is the missing `action_oriented` deduction. This is the clearest of the
      three and the only one whose premise survives the sweep unchanged.
      doing AND rests its actionability on being able to measure it, so neither
      lever that fixed p8 and p16 reaches it -- not the time clause, and not
      "names no doing of its own". Gold docks it. This is the residual cell most
      likely to be a genuine boundary question rather than a wording gap: the
      answer does the thing the criterion asks for and justifies it the wrong
      way. Read `--criterion Q3 action_oriented` credited rows FIRST; a rule that
      rejects measurability-as-justification risks p9, p14 and p18, all credited
      on access alone.
- [ ] Q10. **Q3/p10: `measurable` at ~3/6.** Names tracking methods but no medium
      MEASURED IN THE TWO-SIDED SWEEP, 6 runs, 2026-08-28. Q3 came out 18/20 at
      100% PER CHECK with a spread of ZERO cells -- so every individual verdict was
      right and the two missed cells are arithmetic on correct judgements. The
      error profile is ONE-SIDED: over-credit 11, under-credit 1, and the tool's own
      reading is "a threshold is set wrong, not unstable". Both remaining defects
      are MISSING DEDUCTIONS -- we credit what gold docks -- which is a far more
      tractable shape than Q1's and Q2's opposed-direction errors.
      AND THE DIAGNOSIS MOVED, because gold docks TWO points on each of these cells
      and we were reading the first one only:
      RIGHT SLOT, WORSE RATE, AND NO LONGER UNSTABLE. gold 3.0 against our 4.0 in
      5 of 6 runs. gold docks `specific` AND `measurable`; we fail `specific` in 6
      of 6 and `measurable` in only ONE of 6. So the cell is not "~3/6" any more --
      we credit `measurable` five times in six, which is stably wrong rather than
      noisy. The recorded caution here was "six runs of the criterion before any
      prose change, since a ~3/6 cell can be moved by noise and read as a fix";
      those six runs now exist and the answer is that noise is not what this is.
      -- what it would be recorded in. Unstable rather than stably wrong, so it
      is the weakest of the three: six runs of the criterion before any prose
      change, since a ~3/6 cell can be moved by noise and read as a fix.
- [x] Q11. **Q3/p13: `realistic` over-charged.** We charge where gold passed the
      MEASURED IN THE TWO-SIDED SWEEP, 6 runs, 2026-08-28. Q3 came out 18/20 at
      100% PER CHECK with a spread of ZERO cells -- so every individual verdict was
      right and the two missed cells are arithmetic on correct judgements. The
      error profile is ONE-SIDED: over-credit 11, under-credit 1, and the tool's own
      reading is "a threshold is set wrong, not unstable". Both remaining defects
      are MISSING DEDUCTIONS -- we credit what gold docks -- which is a far more
      tractable shape than Q1's and Q2's opposed-direction errors.
      AND THE DIAGNOSIS MOVED, because gold docks TWO points on each of these cells
      and we were reading the first one only:
      PREMISE LARGELY RESOLVED -- CHECK BEFORE SPENDING ANYTHING ON IT. gold 3.0
      and we now predict 3.0 in 5 of 6 runs. gold docks `specific` AND `measurable`
      and we fail both in 6 of 6, which is why the cell is right. The systematic
      over-charge this subgoal was written about is gone; what is left is a single
      run where `realistic=unclear` cost a point, and that one run is the ONLY
      under-credit in the whole item (1 of 120 observations). Consider closing this
      on the sweep rather than working it, and if it stays open the target is a
      1-in-6 flicker, not a threshold.
      CLOSED 2026-08-31 ON TWO INDEPENDENT LINES. The E37 ownership check flagged
      Q3/p13 as a cell this subgoal names that now scores RIGHT at the recorded
      median -- 3.0 against gold 3.0 on BOTH the olx and the python, six runs each --
      and the note above had already reached the same verdict from the criterion
      side three days earlier without the check existing. Closing on one recovered
      cell would have been the suspect-cell mistake; what justifies it is that the
      RULE this was filed about is clean corpus-wide, with Q3's error profile
      running over-credit 11 to under-credit 1.
      THE RESIDUE, so that closing does not hide it: `realistic=unclear` cost a
      point in ONE run of six, and that is the ONLY under-credit anywhere in the
      item -- 1 of 120 observations. That is the noise floor, not a defect, and it
      is deliberately not being carried as a subgoal. If Q3 is ever measured again
      and `realistic` reads `unclear` at a rate materially above 1-in-6, THAT is
      the signal to reopen this; a single flicker is not.
      answer silently, so unlike 9 and 10 the defect is OURS being too strict,
      not too lenient. Gold's silence is the evidence, which makes this the one
      of the three where the credited rows matter most -- there is no gold note
      to read, only the absence of a deduction.
- [x] Q12. **Q1's exclusion failures: p6, p10, p16.** Not a counting problem, and
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
      Carries the open question from subgoal Q6's v3: an inline exclusion list
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
      p9 was declared (subgoal Q12b). p10 did NOT recover and p18 was destabilised
      by the same change that fixed p6 -- both carried to subgoal Q14 rather than
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
      handouts.GOLD_DIVERGENCES. Q1 records 17/20 as of the 2026-08-28 sweep
      (18/20 when this was written) and cannot exceed nineteen of
      its twenty cells while this stands.
- [x] Q13. **Q1/p17: `utb_stated` is a coin flip.** CLOSED BY DECISION, not by
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
      look at AFTER subgoal Q14.
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
      (`checks: null`) is what identified subgoal Q1.

- [ ] Q17. **Q2: `wgb_is_counterpart`, `wgb_inverts_utb`, `reason_3`.**
      Q2/p18 MOVED HERE 2026-09-01 from Q32, which closed. It is `wgb_inverts_utb`
      -- the slot this subgoal already owns -- flipping: pooled over both engines
      the cell reads 2.0 seven times and 4.0 five times against a gold of 4.0, so
      the pooled median misses by one observation. It arrived in Q32 as a
      side-split, and pooling shows it was never that: both engines flip on it at
      about the same rate. A 7-to-5 cell is the shape this entry's spread of 3
      cells is made of.
      Set 2026-08-28 from the two-sided sweep's second item. 6 runs, current
      configuration: RECORDS 16/20, runs [15,16,16,16,17,18], spread 3 cells, 0
      failures. The previous entry said 18/20 and was STALE SCORER, so this is a
      two-cell move between configurations rather than a regression against a live
      baseline. (An earlier draft said 15/20, from the summary's median-RUN column
      rather than the ledger's median-of-run-totals.)
      SAME LOPSIDEDNESS AS Q1, AND STRONGER: under-credit 17 (14%) against
      over-credit 5 (4%). Two items, both erring the direction Q1's recorded
      history says they should not. That pattern is now worth a look of its own.
      THE PROFILE NAMES ITS OWN SUSPECTS -- the tool marks two slots as tracking
      the errors:
        `wgb_is_counterpart`  unmet 7, FIVE of them in wrong cells. The sharpest
                              signal in either item so far.
        `wgb_inverts_utb`     unmet 16, 8 wrong / 8 right.
        `reason_3`            unmet 47, 20 wrong / 27 right -- fires more often
                              than it explains, exactly as Q1's reason_3 does
                              (47 unmet, 39 right). The same slot behaving the same
                              way on two items points at the counting structure
                              rather than either item's wording.
      THE TWO WORST CELLS ARE ONE RULE FAILING BOTH WAYS:
        p10  gold 3.00 -> pred 0.00  (-3.00)  gold: "your WGB should be the
                                              opposite of your UTB"
        p7   gold 0.00 -> pred 2.00  (+2.00)  gold: same criterion
      We refuse p10 where gold credits and credit p7 where gold refuses, on the
      INVERSION criterion in both cases. A rule change that fixes one will tend to
      break the other -- the shape that produced Q6's seven measured-and-reverted
      attempts -- so name both as controls before touching anything.
      WHAT THE TWO SLOTS ARE FOR, from their own recorded text: they are a
      deliberate two-tier split. `wgb_is_counterpart` is "the WGB_UNRELATED test,
      and only that: is the goal behavior about a DIFFERENT behavior altogether",
      and explicitly PASSES a goal in the right territory that fails to invert.
      `wgb_inverts_utb` then carries "TWO ways to fail, and the second is the common
      one ... a goal IS stated but does not invert the behaviour the Q1 UTB names".
      So the errors concentrate exactly on the boundary between "unrelated" and
      "related but not inverted", which is the thing the split was built to separate.
      A FINDING TO CARRY, not an action here: ALL THREE of these slots --
      `Q2:wgb_is_counterpart`, `Q2:wgb_inverts_utb`, `Q2:reasons_given` -- have
      their judging text in SLOT_NOTES, the olx-only channel, and are three of the
      thirteen entries in `enforcement.SLOT_RULE_BACKLOG`. Both columns of THIS
      sweep read them, because agreement.py loads the OLX prompt, so the reach gap
      is not what is causing these errors. But the PAPER scorer never sees them, so
      when score.py is compared these same slots will diverge further, and
      migrating them to the rubric `rule` field -- as 1a's five were on 2026-08-28,
      which cost 1a/p6 the whole item before the migration -- is the action that
      serves both problems at once. Q2's `reasons_failing` and `reasons_substantial`
      are in that backlog too, unscoped.
      DO NOT CHASE `confident`: unmet in 117 of 120 observations with 95 in cells
      that scored correctly. Same noise floor as Q1, confirmed twice.
      WAIT FOR THE APP COLUMN, for the reason on subgoal Q16: the two sides share
      this prompt and differ only in whose rules score it.

- [ ] Q18. **Q4b: the `not_doing` classification on the SECOND box.**
      MEASURED ON THE APP 2026-08-29, for the first time -- Q4b could not run
      there at all until subgoal Q14. OLX 16/19, EXACTLY the python's 16/19, era
      checked, 0 of 20 cells never agreeing. p12 returns 3.5 in all six runs on
      BOTH engines where it used to be python 5.0 / olx 3.5 in eleven of twelve.
      So the divergence the whole equivalence goal was opened over is CLOSED, and
      subgoal Q10's `maps` conversion is what closed it: the referent test is now
      arithmetic and the two engines cannot disagree about it. What is left here
      is a gold question, which is what this subgoal was always about.
      THE SECOND-BOX SYMPTOM IS SHARED WITH Q4c AND Q6; THE MECHANISM IS NOT.
      All three show the same asymmetry -- the second slot unmet far more often
      and far more often in wrong cells:
        Q4b  behavior_1   23/0    behavior_2    52/17
        Q4c  consequence_1 6/0    consequence_2 19/7
        Q6   state_c1     15/6    state_c2      58/17
      But the DIRECTION splits them, and direction decides the fix:
        Q4c  18 over / 1 under      Q6  23 over / 9 under   -> the second box
             TAKES credit it has not earned; that is subgoal E15's `requires`.
        Q4b   7 over / 12 under                             -> the second box is
             DENIED credit, by `maps` sending `not_doing` to wrong_kind.
      SO DO NOT JUDGE A `requires` FIX ON THIS ITEM. `requires` denies credit and
      Q4b already under-credits; it would move this item the wrong way while
      helping Q4c and Q6. Q4c's half of the second-box problem lives in subgoal
      15 for that reason. This subgoal keeps Q4b alone.

      Asked for as "errors on behavior_1", and the first thing to record is that
      BEHAVIOR_1 HAS NONE: unmet 23 times across 120 observations, all 23 in cells
      that scored correctly. Every one of the 17 wrong-cell observations is on
      `behavior_2`. behavior_1 is the control here, not the target -- and the
      asymmetry between the two boxes IS the question, because they are judged by
      the same rule on the same answer sheet.
      THE SWEEP, 6 runs: 16/19, which is EXACTLY the ledger's 16/19. The mechanism
      change landed today -- both boxes are now computed by `maps` from a pick --
      and it cost nothing in accuracy while making the two scorers unable to
      disagree about the combining. Drift is 1 cell per box across six runs.
      THE PICKS LOCALISE IT FURTHER THAN THE SLOT, which is what the conversion
      bought: the failing classification is one option value.
        p4   gold 2.0  ours 3.5 (6/6)   b1=activity, b2=consequence
        p12  gold 5.0  ours 3.5 (6/6)   b1=activity, b2=not_doing
        p13  gold 5.0  ours 3.5 (4/6)   b1=activity, b2=not_doing 4/6, activity 2/6
      p12 AND p13 ARE THE SAME SHAPE: we classify the second entry `not_doing` --
      the fifth test, "NAMING A FAILURE TO ACT IS NOT NAMING A SUBSTITUTE" -- and
      gold credits it anyway. p4 is the opposite: we credit box 1 where gold
      refuses both.
      WHAT IS ALREADY DECLARED, and what is not: p4 and p12 are BOTH declared gold
      divergences in handouts.GOLD_DIVERGENCES under B_NOT_ACTIVE, with p12's entry
      stating the case exactly -- "gold credits a not-doing as an active behaviour
      ... `behavior_*`'s fifth test refuses it in terms. Gold gives 5.0." P13 IS
      NOT DECLARED and is the same shape, so it is the live one. Check whether it
      is a third instance of the declared disagreement or a genuine miss before
      touching the rule.
      THE LEVER IS ONE OPTION, NOT THE PROSE: `not_doing` accounts for 16 of
      b2_basis's 120 answers and for both undeclared-shape failures, while
      `consequence` (30 answers) produces one. A change scoped to when `not_doing`
      is chosen -- or to whether it should map to `wrong_kind` at all -- is
      testable without touching the other four cases. That option-level view did
      not exist before 2026-08-28: the same judgement was buried in a five-test
      composite, and only the pick makes it countable.
      CONTROLS, named in advance: b1_basis is `activity` in 6 of 6 runs on all
      three cells, so any change that moves box 1 has broken something unrelated.
      The six `b2_basis=none` observations are the only source of `absent`
      (B_ONLY_ONE rather than B_NOT_ACTIVE) and must keep charging that.

      == 2026-09-01: THE QUESTION IS ANSWERED, AND AN ATTEMPT WAS MEASURED AND
      REVERTED ==
      P13 IS NEITHER OF THE TWO OPTIONS this entry offered. It is not a third
      instance of the declared not-doing disagreement, and it is not simply a
      miss. Read the two cells side by side:
          p12  "{{corpus:Q4b/p12:second:0:34:sha=50add6bc49ca:shape=C3c}}"      not_doing 6/6, both engines
          p13  "{{corpus:Q4b/p13:second:25:109:sha=0e7747dbc9b4:shape=S8-0a20202020202020202020202020202020,S14-0a20202020202020202020202020202020,A67}} ADHD"                      python 4/6, olx 4/6
      p12 is a chosen omission and both engines name it identically. p13 is an
      INABILITY, and both engines waver on the identical quoted text. The option
      set is `activity`/`consequence`/`goal_behaviour`/`not_doing`/`none` and
      NONE of them fits an inability, so the pick is undefined and the
      oscillation is manufactured by the vocabulary rather than by the model.
      `not_doing` IS A CATCH-ALL over at least three shapes, which is the finding
      under the finding:
          p12  a chosen omission        gold 5.0   the real not_doing
          p13  an inability            gold 5.0
          p5   an external barrier --
               "{{corpus:Q4b/p5:second:50:75:sha=e622fa24ccd8}} home"   gold 3.5, AND WE ARE RIGHT
          p10  a future intention (2/12)          gold 2.0
      p5 matters most of those: `wrong_kind` is the CORRECT answer there and gold
      agrees, so the fallback is not simply too harsh and must not be loosened.
      THE ATTEMPT: add an `inability` option to both basis slots, described in
      each rule, and to the OLX `choices`. It was predicted SCORE-NEUTRAL on the
      grounds that `inability` falls through to the same `wrong_kind` fallback as
      `not_doing`, so no verdict could change.
      THAT PREDICTION WAS WRONG, AND WRONG IN THE INSTRUCTIVE WAY. Adding an
      option to a pick is not additive: it redistributes the WHOLE
      classification, including probability that used to land on `activity`,
      which maps to `met`. Measured at six runs on the python side:
          before  16/19  [15, 16, 16, 16, 17, 17]
          after   14/19  [14, 14, 14, 14, 15, 15]
      Two cells that were right in 6 of 6 runs broke, IN OPPOSITE DIRECTIONS --
      p6 went 3.5 -> 5.0 (over-credit) and p14 went 5.0 -> 3.0 (under-credit) --
      while p13, the cell the change was for, did not move. Opposite directions
      is the signature of a prompt perturbation rather than of the vocabulary
      repair it was meant to be. The olx side was stopped after two runs at
      16/19 and 16/19, since the python median already met the revert rule.
      REVERTED, and the tree is byte-identical to the measured state: Q4b's
      prompt shas are back to 884defb56f26 (olx) and 7945bc093e62 (python), the
      values the ledger holds, so 16/19 on both sides stands unre-measured.
      FOR THE NEXT ATTEMPT. The diagnosis survives the revert -- p13 is an
      inability, the option set has no word for it, and the instability is real.
      What does not survive is the idea that a new enum value mapping to an
      existing fallback is free. If this is tried again, hold the OTHER
      classifications fixed as the control: p6 and p14 at 6/6 are the two cells
      that broke, and any future attempt should be judged on whether they stay
      put before anything is claimed about p13.

- [ ] Q16. **Diagnose Q1's wrong calls: `utb_stated`, `reason_2`, `reason_3`.**
      Set 2026-08-28 from the two-sided sweep's first item, so the numbers below are
      6 runs at the CURRENT configuration rather than a recollection.
      THE PROFILE, 120 observations: 102 correct (85%), UNDER-credit 13 (11%),
      over-credit 5 (4%). The direction is the finding. Q1's whole recorded history
      is an OVER-counting problem -- ~900 calls and eleven `reasons_given`
      configurations, ending in the restored two-tier conditional -- and this says
      the current prompt errs the other way, nearly 3 to 1. Nothing in the tree
      predicted that, so read it before assuming the old diagnosis still holds.
      EVERY WRONG CELL IS A COUNTING DISAGREEMENT, and they oppose each other:
          said 3, scored 5 against gold 4    x5   over
          said 3, scored 3 against gold 5    x5   under
          said 2, scored 4 against gold 5    x4   under
          said 1, scored 3 against gold 4    x4   under
      THE STRUCTURAL OBSERVATION, and where to start (§2a): the first two lines
      have the model saying THE SAME COUNT, 3, and the cell scoring 5 in one group
      and 3 in the other. The count is therefore not deciding the score -- the
      gating slots are. Look there before any wording, because a rule that changes
      what "3" means cannot separate two groups that both said 3.
      THE THREE SLOTS TO WORK, with their measured shape:
        `utb_stated`  unmet 11, of which 5 in wrong cells and 6 in right -- the only
                      slot whose unmet verdicts split near-evenly, so it carries
                      real signal. Subgoal 13 CLOSED BY DECISION on p17 being a coin
                      flip for this slot; that is prior work, not a settled answer.
      p17 IS NOT A COIN FLIP, 2026-09-01, and the earlier decision rested on
      pooling the two sides. Split by side it is deterministic and opposite:
          python  utb_stated absent/unclear in 5 of 6 runs -> 3.0
          olx     utb_stated met in 6 of 6 runs            -> 5.0
      Gold is 5.0, silent. Both sides quote the SAME span -- "{{corpus:Q1/p17:response:0:40:sha=9086cd1358c1:shape=S2-0a202020202020}}" -- and reach opposite verdicts on it, so this is
      not two readings of two different things.
      THE RULE DECIDES IT, AND IT DECIDES FOR `met`. The desc says ownership can
      be satisfied by "saying what they want instead of it", and that a response
      built ENTIRELY of effect clauses is absent. The response is not:
          "{{corpus:Q1/p17:response:0:40:sha=9086cd1358c1}}   <- effect clause, correctly
                                                         not ownership
           {{corpus:Q1/p17:response:41:64:sha=065142ad7b98:shape=C76dbc7}}                    <- what they want instead,
                                                         which the rule counts"
      So olx is right, gold agrees, and the python side is WRONG. Its own
      evidence gives the mechanism away: it quotes only the effect clause, and on
      one run says it "looked for an explicit statement taking ownership such as
      '{{corpus:Q1/p3:response:0:30:sha=c5fd6758ccc7}} ...' or 'I chose ...' and did not find" it
      -- two of the rule's three branches, with the third, "what they want
      instead", never applied.
      THAT MAKES p17 A DIAGNOSED UNDER-CREDIT rather than a coin flip, and it is
      the first cell found where the two OLX-prompt engines disagree
      DETERMINISTICALLY on a model-judged slot with the same prompt and the same
      model. Q32 concluded that axis was noise plus one provider difference; this
      is a third kind and Q32 should not be read as covering it.
      DO NOT FIX IT BY REWEIGHTING THE PROMPT before reading Q18 and Q24's
      2026-09-01 entries: three prompt changes were measured on this corpus that
      day, two were reverted, and the third was refuted before it was written.
      The rule here is already correct -- the branch exists and is not being
      applied -- so the lever is emphasis, which is the riskiest kind of change
      this project makes.
        `reason_2`    unmet 16, 4 in wrong cells.
        `reason_3`    unmet 47, 39 of them in cells that scored CORRECTLY -- so it
                      fires far more often than it explains. Treat a change here as
                      likely to move right cells, and control for them.
      DO NOT CHASE `confident`. Unmet in 92 of 120 observations with 79 of those in
      cells that scored correctly, and the top drifter at 14 cells changing verdict
      across runs. It fires constantly and predicts nothing; it is the noise floor,
      not a lever.
      WAIT FOR THE APP COLUMN. The two sides share this prompt and differ only in
      whose rules score it, so the same profile on the olx side separates "the
      prompt asks badly" from "one scorer applies it differently". Acting on the python
      column alone would be tuning a prompt against one of its two readers.
      ALREADY RECORDED, do not rediscover: Q1/p9 is a declared divergence
      (GARBLED_CLAUSE_READ_LITERALLY, twelve configurations); p10 and p18 are
      subgoal Q14; the `harms_listed` ASSERTION-vs-AVOIDANCE clause and the two-tier
      `reasons_given` conditional are both live and measured. `python3
      olx_prompts.py --write` prints Q1's recorded comment blocks, and since
      2026-08-28 it prints the LATEST three, which is where the counting rule sits.

- [ ] Q14. **Q1's two live misses: p10 and p18.** Lifted out of subgoal Q12's
      POOLED, 2026-09-01, THIS IS ONE MISS AND NOT TWO. Q1/p18 scores 5.0 in ALL
      TWELVE pooled runs against a gold of 5.0 -- it is not a live miss and has
      not been one since the sides were pooled. Only p10 remains.
      AND p10 IS STABLY WRONG, which is a sharper claim than the title's "live
      miss": 5.0 in 11 of 12 runs against a gold of 4.0, reaching gold once. So
      this is a cell we over-credit almost every time, not a coin flip, and it is
      worth a rule question rather than more runs.
      RETITLE WHEN IT IS NEXT WORKED -- "Q1's two live misses" names a cell that
      is not one.
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

- [ ] Q24. **Q4a's ceiling: two cells, both `antecedent_1`, deterministic and opposite.**
      RETITLED 2026-09-01. It was "Q4a's `antecedent_2`: the slot that carries the
      item's remaining error", and both halves of that turned out wrong -- the
      slot is `antecedent_1`, and pooling reduced four cells to two. The original
      entry and its measurements are kept below, because the route to here is
      most of the value.
      WHAT IS ACTUALLY LEFT, over twelve pooled runs:
          p14  gold 1.0, we score 3.0 in 12 of 12
               antecedent_1 `met` 12/12   -- we CREDIT box 1, gold charges it
               antecedent_2 `wrong_kind` 12/12
          p19  gold 5.0 silent, we score 3.0 in 11 of 12
               antecedent_1 `wrong_kind` 12/12 -- we REFUSE box 1, gold credits it
               antecedent_2 `met` 11/12
      Both cells turn entirely on `antecedent_1`, both are answered the same way
      every run, and they point OPPOSITE WAYS. No threshold on that slot moves
      one without moving the other the wrong way, and the one rule anybody
      proposed -- a consequence test, from Q4b's case (3) -- was refuted before
      it was written: p10 and p17 carry the same bidirectional state loop on the
      same utb and gold gives both full marks.
      SO THE GOAL IS NO LONGER "DIAGNOSE A SLOT". It is to decide whether either
      cell can be moved at all, and to record the ceiling if not. Two routes, one
      per cell, and neither is a Q4a rule:
      (1) p14 IS A GOLD-CONSISTENCY QUESTION. Gold charges box 1 -- "{{corpus:Q4a/p14:first:20:66:sha=bcd1a76b331c:shape=S1-0a20202020202020202020}} rot" -- and credits the same shape
          at full marks in p10 ("{{corpus:Q4a/p10:first:18:49:sha=e49b0a54724f:shape=A1,A19}} going") and p17
          ("Feeling {{corpus:Q4a/p17:first:7:31:sha=4ac4f9df70c1}} workout"), all three on `lack of
          exercise`. Its comment is plural and charges the full 4, which reads as
          the grader docking the pair on the strength of box 2's unmistakable
          "afterwards". If that reading holds, the item's gold is internally
          inconsistent on this shape, and `handouts.CORRECTED_GOLD` is the
          mechanism -- the same bar Q6/p4 was corrected on, and a high one.
          DO NOT correct gold to make a number move; the test is whether the row
          contradicts the grader's own decisions elsewhere in the same item.
      (2) p19 IS Q31's STRICTNESS QUESTION, not a Q4a one. Gold gave full marks
          in silence; we refuse "{{corpus:Q4a/p19:first:23:58:sha=ca9d4ea70d5d:shape=S4-20}}" every run.
          Q31 asks whether a silent full-marks row is a judgement to defer to,
          and this cell is one of its unstable members -- we score 1.0 once in
          twelve, charging BOTH antecedents.
      IF NEITHER ROUTE OPENS, RECORD THE CEILING AND STOP. Q4a would then be at
      its ceiling with two cells that no rule available to this project can
      reach, which is a result worth writing down rather than a subgoal worth
      leaving open. See memory/q6-matching-ceiling.md for the precedent and for
      what a ceiling entry has to contain.
      CONTROLS FOR ANY FUTURE ATTEMPT, named now: p2 and p9 are RIGHT at the
      pooled median and unstable underneath (both spread 3.0/5.0), so they will
      move under a prompt change and their movement means nothing; p10 and p17
      are the cells a box-1 rule breaks; and the thirteen cells scoring correctly
      and stably are the ones that must not move at all.

      POOLED, 2026-09-01, THIS SUBGOAL IS TWO CELLS. Of its four, p2 and p9 are
      RIGHT at the pooled median -- both unstable, spread 3.0/5.0, but landing on
      gold -- and only p14 and p19 are wrong. So the "two different failures
      wearing one slot's name" is now ONE failure: the instability half has gone,
      and what remains is the stable, opposite-direction antecedent_1 pair.
      That STRENGTHENS the refutation above rather than reopening it. There is no
      wording fix, because tightening antecedent_1 fixes p14 and breaks p19; and
      there is no longer an instability to chase either. p14's pooled spread is
      a single value, 3.0 across all twelve runs.
      Opened 2026-08-29, on the FIRST measurement of Q4a on the app -- it could
      not run at all before the LLMAction attribute fix (subgoal E14), and the
      olx-only `max` defect had to be cleared before any cell scored on the right
      scale. So this is a channel nobody has ever been able to look at.
      THE SLOT PROFILE NAMES IT. Over 120 observations, olx:
        antecedent_1   unmet 24   in wrong cells  6
        antecedent_2   unmet 31   in wrong cells 10
        keyword        unmet 18   in wrong cells  3
      `antecedent_2` is unmet more often than `antecedent_1` AND lands in wrong
      cells more often -- the SECOND-BOX shape again, on a third item. Subgoal 18
      (the second-box problem) was scoped to Q4b and Q4c; this is evidence it
      reaches Q4a, and the three should be read together before either is fixed.
      FOUR CELLS CARRY IT, and their pattern is the useful part:
        p2  3/6  a2 flips met/wrong_kind across runs (gold 5)
        p9  3/6  a2 flips wrong_kind/met across runs (gold 3)
        p19 0/6  a2 is `met` in 5 of 6 runs and the cell is STILL wrong (gold 5)
        p14 0/6  a2 is `wrong_kind` in 6 of 6 and the cell is wrong (gold 1)
      So there are TWO different failures wearing one slot's name, and a fix
      aimed at either alone will move the other the wrong way:
        * p2 and p9 are INSTABILITY -- the same box read both ways across runs.
          A sharper rule about what makes an antecedent "a genuine trigger"
          addresses these.
        * p14 and p19 are STABLE and wrong, which a wording change will not
          touch. p19 is the sharper one: `antecedent_2` is answered `met` in 5 of
          6 runs and the cell still misses, so the error is NOT in this slot's
          verdict -- it is in what the sheet does with it. Read p19's boxes out
          (`equivalence.py --fixture Q4a:19`) BEFORE proposing any rule.
      DO NOT START FROM THE MEDIAN. The item sits at 18/20 olx / 17/20 python, which
      hides four cells that are wrong in two unrelated ways; and the by-slot
      table alone would have pointed the whole effort at wording, which p19 and
      p14 say cannot work. This is memory/error-profile-by-slot.md's rule and
      memory/fixture-defects-found-by-readout.md's rule applying at once.
      Direction is BALANCED -- 9 over, 9 under -- so unlike Q6 and Q4c this is
      not a `requires` candidate (subgoal E15): denying credit would fix the
      over-credits and worsen the under-credits by the same count.

      == 2026-09-01: THE READOUT WAS DONE, AND THE SLOT IN THE TITLE IS WRONG ==
      This entry said to read p19's boxes out before proposing any rule, and
      that instruction was right in a way it did not anticipate: BOTH stable
      cells are decided by `antecedent_1`, not by `antecedent_2`, and in OPPOSITE
      directions. Twelve of twelve observations each, on both sides:
          p19  gold 5.0, silent   a1 wrong_kind 12/12   a2 met 11/12   we score 3.0
               box 1: "{{corpus:Q4a/p19:first:0:48:sha=48ddc83f5e35}} motivated"
               -- gold credits it; we refuse it. WE ARE TOO STRICT.
          p14  gold 1.0, "-4pts: Examples are not antecedents. Remember that
               antecedents happen before the UTB is exhibited."
               a1 met 12/12   a2 wrong_kind 12/12   we score 3.0
               box 1: "{{corpus:Q4a/p14:first:20:66:sha=bcd1a76b331c}} rot"
               -- gold refuses it; we credit it. WE ARE TOO LENIENT.
      NO WORDING CHANGE CAN FIX BOTH. Tightening `antecedent_1` fixes p14 and
      breaks p19; loosening it does the reverse. That is the same conclusion this
      entry reached from the by-slot table, arrived at from the cells, and it now
      names the slot correctly.
      THE OTHER TWO CELLS HAVE MOVED SINCE THE TABLE ABOVE WAS WRITTEN:
          p2  was 3/6 with a2 flipping; now 5/6 on BOTH sides, one flip each.
              Largely resolved, and not worth a rule.
          p9  was 3/6 with a2 flipping; now python 6/6 RIGHT and olx 3/6, which
              makes it the side-split cell rather than an instability. It is
              Q32's, and Q32 records that it inverted under E25.
      SO THE ITEM'S REMAINING ERROR IS TWO CELLS, BOTH ON antecedent_1, BOTH
      STABLE, POINTING OPPOSITE WAYS -- which is why 17/20 olx and 18/20 python
      have not moved despite everything else that changed today.
      A CANDIDATE, NOT YET TRIED. p14's box 1 -- "not seeing immediate results" --
      is arguably a CONSEQUENCE of the unwanted behaviour standing in for its
      antecedent: no exercise, no results, more bed-rotting. Q4b's rule already
      carries the analogous test as its case (3), that an activity which is
      likely a consequence of not doing the goal behaviour cannot also be what
      replaced it. Q4a has no such test. Adding one would address p14 without
      touching p19, which is the only shape of fix these two cells permit.
      BEFORE TRYING IT, READ Q18's 2026-09-01 ENTRY. A Q4b vocabulary change that
      was predicted score-neutral cost two 6/6 cells in opposite directions and
      was reverted the same day. Any Q4a prompt change must name p2, p9 and the
      thirteen cells that are currently right as controls, and state its revert
      rule before the sweep rather than after it.

      THE CANDIDATE IS REFUTED, 2026-09-01, BEFORE ANY CALLS WERE SPENT. Reading
      every box 1 in the item against its own UTB is what refutes it, and the
      control survey is the whole argument:
          p14  gold 1  a1 met  utb lack of exercise
               "{{corpus:Q4a/p14:first:20:66:sha=bcd1a76b331c}} rot"
          p10  gold 5  a1 met  utb lack of exercise      <- CORRECT TODAY
               "{{corpus:Q4a/p10:first:18:80:sha=62bd27efbe04:shape=A1,A19}}"
          p17  gold 5  a1 met  utb lack of exercise      <- CORRECT TODAY
               "Feeling {{corpus:Q4a/p17:first:7:31:sha=4ac4f9df70c1}} workout"
      All three are the same shape: a bidirectional state loop on the same UTB --
      not exercising leaves you tired, unfit and resultless, and those states
      then keep you from exercising. A test that refuses "a state the behaviour
      produces" cannot separate them, so it fixes one cell and breaks two. That
      is the Q6 ceiling pattern (memory/q6-matching-ceiling.md) arriving on a
      different item.
      AND THERE IS A BETTER READING OF p14 THAT NEEDS NO RULE. Gold's comment is
      PLURAL -- "Examples are not antecedents" -- and charges the whole 4, which
      is both boxes. Box 2 is "being in pain AFTERWARDS", unambiguously a
      consequence. So gold most probably judged the answer on box 2 and docked
      both, which is the later-box gradient, and Q19 already carries Q4a/p14 for
      exactly that. On that reading box 1 is not a separate defect and there is
      nothing here for an antecedent_1 rule to fix.
      SO Q4a's TWO STABLE CELLS ARE NOW BOTH ACCOUNTED FOR WITHOUT A RULE: p14
      belongs to Q19's gradient, and p19 is a silent-full-marks cell belonging to
      Q31. What is left in THIS subgoal is the question of whether our
      antecedent_1 is too strict on p19, which is Q31's false-positive question
      and not a wording one.

- [ ] Q26. **DAY1 alone gates on `phrased_directly`. One `!`, undeclared, eight sibling items.**
      Found 2026-08-29 while checking whether DAY1 contradicted subgoal Q20's
      orthogonal-gates finding. It does not contradict it; it is a different
      sheet, and the difference is one character of OLX:
          DAY1  !phrased_directly:Phrased directly rather than by what is avoided
          DAY2   phrased_directly:Phrased directly rather than by what is avoided
          WK1    phrased_directly:Phrased directly rather than by what is avoided
      The `!` makes it a gate. So on DAY1 that slot can ZERO the whole 4-point
      item; on its seven siblings -- PR, NR, PP, NP, WK1, DAY2 and (pending) WK2 --
      it is advisory and cannot deduct at all. Confirmed from the published sheets,
      not read off the OLX alone: `gates=True` on DAY1, `gates=False` on the rest.
      IT IS DECLARED NOWHERE. Not in SCORING_DIVERGENCES, not in EQUIVALENCE.md,
      not in the rubric comments. Both scorers honour it identically, so this is
      not an equivalence defect -- it is a rubric one, and the audit has no check
      that would notice it.
      FIRST DECIDE WHICH IT IS, and the two answers lead opposite ways:
      (a) INTENTIONAL -- a daily plan phrased by what is avoided is a different
          failure from a weekly one, serious enough to void the item. Then declare
          it, with the reason, and subgoal Q20's DAY1 numbers stand as real.
      (b) A SLIP -- someone typed `!` once. Then DAY1 has been scoring on a
          harsher sheet than its siblings for as long as the slot has existed, and
          its 17/18 is a number obtained under different rules from DAY2's 16/18.
      READ THE RECORD BEFORE DECIDING (memory/read-the-record-first.md): check the
      commit that introduced the `!` and the rubric comment above the component.
      The precision table in subgoal Q21 already lists `phrased_directly` as
      "advisory, cannot deduct" -- which is TRUE OF NR AND FALSE OF DAY1, so at
      least one recorded statement was written without this asymmetry in view.
      THE CHECK THIS WANTS IS SUBGOAL E26, split out because it does not depend on
      how this question is answered: whichever way DAY1 goes, sibling items that
      share a slot name should share its gate structure or declare why not.
      DO NOT "FIX" IT BY MEASUREMENT ALONE. DAY1 scores 17/18 on both engines
      WITH the gate, so removing it is not obviously free; and if it is intentional,
      removing it loses a judgement gold may be making. Decide the intent first.


## THEN

The equivalence goal is PARKED, not closed, and quality control is ACTIVE -- the
reverse of how this section read until 2026-09-01. The swap happened because the
precondition stated here was met: a per-item rate compared against gold meant
nothing while the two scorers disagreed about what the rules are, and they no
longer do. E28 remains open under equivalence and is a measurement rather than a
blocker.

Nothing else is parked here. The ACTIVE subgoals above absorbed what used to sit in
THEN and LATER, and the entries that are no longer true were deleted rather than
carried:

* The two "remaining fixture suspects" are settled. DAY1/p1 is a declared
  divergence (BEHAVIOR_NEVER_STATED); DAY2/p14 is 6/6 correct and was fixed by
  the `forbid` primitive, not by reading its boxes again.
* The three non-reconciling gold rows moved to DONE above.
* Q3's probe backlog is superseded: the item has six runs and a named cause.
* Q1's probe backlog and the 3-run flags in Q2/Q4c/Q5/Q6 are subgoal Q3.
* Q4b/p12 is subgoal Q5. It is 0/6 against gold and correctly declared TODAY --
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
