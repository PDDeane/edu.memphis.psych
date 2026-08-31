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

## ACTIVE — enforcing equivalence between the CLI and web scorers

The whole project rests on the two sides running the same rubric: every recorded
number is a comparison, and a comparison is meaningless while the scorers differ
about the rules. A full audit run in all three modes found the picture is not what
had been reported all session.

`--enforcement` alone was being run and called clean. `--scoring` carries THREE
undeclared mechanical flags, and `--enforcement` itself is structurally blind to
any rule written as guidance prose (subgoal E15, under the parked goal). Q4b/p12
is the demonstrated cost: the CLI scores it 5.0 in six runs of six and the web
3.5 in eleven of twelve, and nothing anywhere declares that.

- [x] E1. **Declare the mechanical flags -- or wire them up.** Three findings, all
      pre-existing except the first, none declared:
      **Q4a TOTAL, web 4 vs CLI 5.** The two antecedent slots carry 2 points each
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
          honoured by the web and silently ignored by the CLI: the check simply
          never got set, its code never charged, nothing reported. Now computed in
          derive_ledger, and `check_both_engines_compute_the_same_primitives`
          asserts the parity from the REGISTRY rather than from a list of names.
        - score.py's schema exclusion named `equals` and `forbid` by hand -- a
          mirror of primitives.json kept by memory, already behind: `expect`
          excludes keys and was missing, so an `expect` key would have been ASKED
          on the CLI while the web computed it. Now registry-driven. `counts` is
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
      the code distinction is a CLI-ledger concept. What the app actually needed was
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
      too. Target p4 (gold 2.0, web 3.5); controls p1, p12, p15, p17 -- the four
      gold credits that held last time -- and p6, where the web already matches gold
      and the CLI does not.
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

      IT IS A WEB-SIDE CHANGE, consistent with the tie-break: Q4b ties on
      gold-matching, so the web is the reference and this improves the reference
      side's own accuracy rather than importing the CLI's reading.

- [x] E11. **Empty SLOT_RULE_BACKLOG: thirteen rules the paper scorer cannot see.** DONE
      CLOSED 2026-08-30, budget 13 -> 1. The one entry left is `Q1:matches_selected`,
      which is not work: the paper sheet has no such SLOT, because a .docx has no
      closed choice to compare against, and the asymmetry is declared in
      SCORING_DIVERGENCES. The list IS the declaration of web-only notes, so the
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
      MEASURED, which is what makes this closable rather than claimed. Q5's web
      prompt changed by exactly one token -- `not_reason` -> `wrong_kind`, verified
      by --diff as a one-line change -- and 1c and reasons_substantial rendered
      BYTE-IDENTICAL on the web, so only the paper scorer gained anything there.
      EXERCISED: Q5 swept at 6 runs on BOTH sides against the regenerated prompt
      f933e0876c3b, on a freshly dumped idmap_v97 proven to carry the new line:
          Q5 cli 19/20 (was 19/20)     Q5 web 19/20 (was 19/20)
          era CHECKED, 0 cells never agree, out/q5_e11_cli and out/q5_e11_web
      Neutral is the RIGHT result and was predicted: the change buys the ability to
      draw a distinction, not a higher score, and BACKLOG.md recorded that no
      counted cell exercises a refusal at all.
      Created 2026-08-28 because there was no subgoal for it -- only the ratchet,
      which stops the list GROWING and never asked it to shrink. Unlike
      HANDCODED_BUDGET, now at 0, `SLOT_RULE_BACKLOG_BUDGET` sits at 13 with no
      target. That is the difference between a declared problem and a tracked one.
      WHAT THEY ARE: judging text parked in `olx_prompts.SLOT_NOTES`, which the web
      generator and the agreement.py harness both read and `score.py` does not. So
      the rule reaches two of the three scorers and the paper one grades without it.
        1c:has_own_graph   1c:legend        D1:defines_type   D2:defines_type
        Q1:matches_selected                 Q2:reasons_given
        Q2:wgb_inverts_utb                  Q2:wgb_is_counterpart
        Q5:example_2       matches_chosen_type   named_type
        reasons_failing    reasons_substantial
      NOT THEORETICAL, and the price is on record: five `1a:*` notes were in this
      list until today, and while they were, 1a/p6 scored 0.0 on the paper path
      against 6.0-8.0 on the web -- the WHOLE item, stably, in 3 of 3 runs.
      Migrating them fixed it and cost nothing elsewhere.
      AND THE SWEEP IMPLICATES FIVE MORE. From the CLI column's error profiles:
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
      `rule` field VERBATIM -- both generators render it, and the web prompt does
      not move because its checklist looks up `rule` BEFORE SLOT_NOTES and finds
      the same string. Then re-run the leakage gate, which re-asks because a
      verdict is keyed to the prose, and refile with an attribution rather than a
      rubber stamp. Drop the entry, lower the budget, and let the ratchet confirm.
      PROGRESS 2026-08-29: D1/D2:defines_type MIGRATED, 13 -> 11. One edit served
      both, because rubric_h2 builds them from a `_definition_item` factory. Web
      prompts byte-identical before and after; the paper prompt GAINED 94 chars,
      and what it gained is the point -- its `desc` already carried "which of the
      four types this DEFINITION describes", so score.py was told what to judge
      and NOT the operative half, "do not look at what they chose". That clause is
      what keeps `defines_type` independent of `named_type`, and the two feed the
      `matches_chosen_type` comparison, so a paper grader reading the choice while
      judging the definition collapses two checks that must stay separate.
      No item's web prompt_sha moved, so the two-sided sweep stays valid.
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
      paths that resolved elsewhere and reported all 23 web prompts as changed.
      TWO REVERTED, and they define the remaining work: `Q5:example_2` and
      `reasons_substantial` name verdict tokens literally -- duplicate/not_reason
      and wrong_kind. Safe in a web-only note, refused in a shared `rule` by
      check_slot_rules_are_vocabulary_neutral, because the paper scorer would be
      instructed about tokens it cannot emit. `{fail}` fills with ONE verdict and
      example_2 distinguishes two. Rewriting the prose to avoid the tokens changes
      the WEB prompt on a measured item, so these are a scoring change to be
      measured, not a refactor.
      THIRD PASS, same day, prompted by asking WHY the Q5 rewrites would touch the
      web at all. They would not, and the revert that assumed they would was
      unnecessary: check_slot_rules_are_vocabulary_neutral was flagging every
      literal verdict token on the blanket premise that "the two vocabularies
      differ". That is true of the DEFAULT vocabulary -- the web's `wrong_kind`
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
      is in the WEB prompt today. Left in the backlog: fixing the text changes a
      measured prompt, so it is a scoring change to be measured, not a migration.
      THE TRADE, again: PROSE_ONLY_SLOTS rises as the backlog falls.
      FOURTH PASS, 5 -> 3, and the 1c pair split rather than moving together:
        `1c:legend` MIGRATED -- its note reached the web only and 1c has a credit
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
      WEB prompt too. That is a measured scoring change on items with a recorded
      six-run baseline on both sides -- exactly what E2 exists to make possible,
      and exactly what must not be slipped in as a refactor.
      THE THREE THAT REMAIN:
        `Q1:matches_selected` -- not a paper-blind RULE at all. The paper sheet
        has no such SLOT, because a .docx has no closed choice to compare against,
        and the asymmetry is already declared in SCORING_DIVERGENCES. It stays
        listed because this list IS the declaration of web-only notes; striking it
        out just made the reach check demand it back.
        `named_type` -- MIGRATABLE, via a criterion renderer on the pattern of
        `_criterion_11`, adding the key to CLI_CRITERIA_NOTES. Not blocked; the
        cost is that `_criteria_section` is shared, so the web gains a criterion
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
      `1c:has_own_graph` and `1c:legend` belong to the item whose web chart is
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
      parses every attribute; nothing asked whether the WEB BLOCK accepts it, and
      that is the half the corpus broke on.
      RESULT, all seven on the web side, era-checked, 0 cells never agreeing:
          Q4a web 18/20     Q4b web 16/19     Q4c web 17/19
          NR  web 16/18     DAY1 web 17/18    DAY2 web 16/18    WK2 web 18/18 Q4b/p12, the
      (WK2's web figure is the 2026-08-30 RE-MEASUREMENT on the clean tree. The
      run recorded here measured 17/18, but it ran from a tree we could not
      certify, so DAY1/DAY2/WK1/WK2 were swept again at 6 runs; DAY1 and DAY2
      came back unchanged, WK1 web 18/18, WK2 web 18/18. The ledger holds the
      re-measure; the cli side of the same sweep has WK1 18/18 and WK2 17/18.)
      divergence this whole goal was opened over, now returns 3.5 on BOTH engines
      where it was CLI 5.0 / web 3.5. The equivalence half of that cell is closed;
      the gold half is Q18.
      Found 2026-08-29 by the two-sided sweep, which is the job it was for. The
      affected items fail EVERY cell on the web side with
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
      -- is still unmeasured on the web side. Do not quote a web figure for any
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
      "and a rule may legitimately mention neither". `wrong_kind` is the web's
      token, `not_reason` the rubric's counterpart. Nothing is stale.
      HOW THE MISREADING COST A CELL: taking the rubric list as "what this slot
      offers", I renamed reasons_substantial's `wrong_kind` to `not_reason` as a
      dangling reference. The CLI column lost a cell, 0 over-credits and 12 under,
      because the rename pointed a LIVE instruction at a token that side cannot
      emit. Reverted; Q5 is 19/20 on both sides with both shas matching.
      AND I WEAKENED THE CHECK THAT WOULD HAVE STOPPED IT, twice: first to "only a
      token this slot does not offer", then unioning the rubric list with the OLX
      spec. Both were built on the same false premise, and the second actively
      hid the case the check exists for. RESTORED to its original strictness --
      any literal token from either list, in a shared `rule`, is a finding.
      THREE MIGRATIONS REVERTED as a consequence, and they are web-only BY DESIGN
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
        web offers it and the paper has only met/absent. Exempting it globally
        left a shared rule free to name it on any of those. No rule did, so it was
        LATENT -- which is how the Q4b instance started.
        Not a renaming, checked: those slots declare no third token under any
        name, unlike Q5's `wrong_kind`/`not_reason` and 1c's
        `incomplete`/`not_described`, which are genuine counterparts. It is a
        three-valued web slot against a two-valued paper one. Score impact is NIL
        -- `unclear` is not satisfied, so it deducts exactly as `absent` does --
        so the asymmetry is diagnostic, not arithmetic. Undeclared all the same.
        `wrong_kind` IS THE SAME SHAPE IN REVERSE: shared on Q4b's behavior_*,
        which declare it in the rubric, and web-only on Q4a's antecedent_*, Q4c's
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
        shared rule naming one would have instructed the WEB about a token it
        cannot emit and passed everything. Added. `not_active` is kept and marked
        HISTORICAL: no slot declares it any more, since Q4b's now declare
        `wrong_kind`, which is why the pair in every docstring citing that
        incident no longer exists anywhere else.
        `desc` IS A THIRD PROSE SOURCE and was unguarded. When a slot has no
        `rule` and no note, the web falls through to the credit component's
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
                artifacts. Correct for harness-vs-app, which share the web's
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
      The third scorer could be RUN and not RECORDED. `cross_path.result_cell`
      read the app's `cell` shape and the harness's `participant_id` shape;
      score.py writes `rN/hM/participant_NNN.json` with an `items[]` list, which
      neither. So `measured.record` failed on a paper artifact exactly as it
      failed on a web one before the reader was shared -- the same gap, still open
      for the third path, and the reason no paper number has ever entered the
      ledger.
      BUILT 2026-08-30, and verified end to end against the old corpus before it
      was discarded: Q1 18/20, PR 17/18, 1a 18/20 recorded on a `paper` side
      beside the existing cli and web columns.
        result_cell   reads the paper shape too, folding `credit_checks` to
                      met/absent so nothing downstream knows which scorer it came
                      from.
        paper_runs.py folds a sweep into the per-item `.runs.json` the ledger
                      records, one file per item, matching sweep_cli/sweep_app.
        sweep_paper.sh drives the runs score.py has no --runs for, into rN/hM/,
                      resumable per slice via a .done marker.
      TWO SIDES, NOT ONE: `paper` is score.py on gpt-5-mini (`--backend lo`,
      through the dev server) and `paper_opus` is score.py on Opus (`--backend
      api`/`cli`). Only the first is comparable to the web and cli columns, both
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
      STILL BLOCKING A SWEEP: E11's remaining `{fail}` rewrites, E15 and E25 all
      change prompts on Q4a, Q4c, Q5, Q6 and 1c. Sweeping first and doing them
      after costs a re-sweep of five of twenty-six items on every side.

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
          WK1 cli  2 over / 1 under      WK1 web  2 over / 0 under
          WK2 cli  5 over / 4 under      WK2 web  4 over / 2 under
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
          web 8/0 -> 2/0; WK2 11/4 -> 5/4; WK2 web 10/2 -> 4/2. The one-sided
          flag correctly stops firing on all of them. Nothing to investigate,
          exactly as the recomputation predicted.
        It REVEALED a true one it had been masking. DAY1 cli read 7 over / 8
          under -- two-sided, "the judgement is unstable" -- and is actually
          1 over / 8 under, now flagged one-sided. The two excluded cells were
          contributing 6 of the 7 over-credits. DAY1 web is 0 over / 7 under.
          So DAY1 UNDER-credits on both sides, one-sided, and the masking hid it.
          Its BY SLOT table names `matches_chosen_type` as tracking the errors
          (6 in wrong cells against 6 in right). That is a QC question and wants
          its own subgoal; do not fold it in here.
      CROSS-CHECKED against the other accounting path: 1c now profiles 17 of 20
      cells (excluding p4, p19, p20), agreeing with its 16/17 ledger figure, and
      still reports the ZERO over-credits the rebuild_gold_1c note demands.

- [ ] E15. **`requires` is implemented on BOTH engines and bound to nothing. Q6 is why it exists.**
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
      (b) Baseline first: Q6's CLI six-run median is 16/20, runs
          [15,15,15,16,16,16]. The web column does not exist yet.
      (c) Measure at SIX runs. The note is explicit that a 3-pass sweep cannot
          resolve a two-cell move on this item: only 5 of 20 cells returned the
          same judgement across three passes.
      (d) Predict per cell before measuring. p5 is the target. p2 over-credits
          +1.25 in every recorded run and is the cell a narrower rule has fixed
          twice. p19 and p10 are the historical casualties.
      IF IT FAILS, the honest outcome is to RETIRE `requires` from
      primitives.json rather than leave a primitive in the registry that nothing
      uses and nothing can use. A registry entry no item can justify is a claim
      about the system that is not true.

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

- [ ] E25. **The `keyword` check is 100% accurate and cannot move a score. Convert it to `derived`.**
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
      case-folded substring search of the student's own text, over the 6-run web
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
      Remaining flags checked: equivalence.py's --item/--cli/--scoring/--fixture
      and agreement_app.py's are each read in their own dispatch branch, so none
      has this shape.
      Found 2026-08-28, during the web sweep, by running it wrong and believing
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
          CLI  451/491 = 91.9%        WEB  457/491 = 93.1%
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
      thing that can answer the question the whole goal is about: do the CLI and
      the web give comparable scores now?
      Ten items are stale from the leakage rewrite and the A_NONE/C_NONE wiring,
      subgoals E3-5 will move more, and every declared divergence in the tree is a
      claim about a difference between the sides that has never been measured
      end to end -- only probed per rule. Q4b/p12 is the warning: CLI 5.0 six
      times of six, web 3.5 eleven of twelve, and nothing declared it.
      COST, stated plainly: 23 items take model calls (1b, T1 and T2 are
      deterministic), so six runs is about 2,760 calls a side and ~5,500 for
      both. Do it LAST, after 3, 4 and 5, so it measures the finished state
      rather than a state that is about to change.
      Record each side, then compare per item AND per cell: an item can agree on
      the number while disagreeing on which cells it got right, and that is
      exactly the shape a per-item comparison hides.

      OUTSTANDING BEFORE THE SWEEP, checked 2026-08-28:
        1. THE LEDGER HAS NO SIDE. `measured.py --record ITEM ARTIFACT` stores one
           number per item and it is the web-prompt path; MEASURED.json has no
           per-side dimension. A two-sided sweep has nowhere to put the CLI's
           numbers, so this is a hard prerequisite, not a nicety. Either add a side
           to the ledger or record the CLI in its own.
        2. TWELVE OF 26 ITEMS ARE RECORDED AT 3 RUNS: 1a 1b 1c D1 D2 NP PP Q4c Q5
           Q6 T1 T2. The sweep at 6 fixes it by construction, but their current
           numbers cannot referee a 2-cell move, so nothing should be compared
           against them in the meantime.
        3. THREE ITEMS' CLI PROMPTS MOVED TODAY and are unmeasured on that side:
           1a, Q4b and Q6, from `rule` replacing `desc` in the CLI render. 1a also
           gained five migrated rules. All three are web-unchanged, so only the CLI
           half of the sweep is affected.
        4. TEN ITEMS ARE STALE PROMPT, which the sweep clears; that is its job.
        5. cross_path reports 25 divergent cells against cli_v8, 15 of them 1c and
           declared. The rest cannot be attributed until both sides are era-matched,
           which the sweep's artifacts will be -- era stamping landed today.
        6. Q4b/p12 needs a decision of its own, independent of subgoal E9: the web
           applies a deliberate divergence there and gold sides with the CLI.

      PRECONDITION, set 2026-08-28: before the sweep runs, the two sides must put
      the SAME RULE LOGIC AND THE SAME RULE LANGUAGE to the model. Byte-identical
      prompts were considered and RETRACTED the same day, on the right grounds:
      the two sides are fed the student's work differently -- the web has one box
      per field, the CLI has one segmented block per item -- so a shared document
      would have meant rewriting the CLI's whole prompt path to serve a
      difference in plumbing. Measured before retracting, and worth keeping: the
      generator IS the shipped artifact (`build_web_prompt` reproduces all 23 OLX
      bodies byte-for-byte once its `\x00REF:` sentinel is expanded), and
      `agreement_app.build_jobs` reconstructs the web's per-box fixture from the
      same paper block the CLI segments. So identity was reachable; it just was
      not worth what it cost.
      Where the wordings differ, the WEB's wins -- unless the difference is
      forced by how the response text is presented, or the web is CLEARLY WRONG,
      as in the DAY1 contradiction subgoal E6 found and fixed.
      AND THE RULE IS ABOUT WORDING, NOT SCORING (user, 2026-08-28). "Web wins"
      settles which of two ways of SAYING the same rule to use; it never settles
      which of two ANSWERS is right. Gold does, and SYMMETRICALLY: whichever side
      matches gold better is the one kept, and the other moves. If the web matches
      gold better, prefer the web; if the CLI does, prefer the CLI.
      MEASURED, 0 calls, `cross_path.py --gold` over paper_mini_v8 against cli_v8:
      the WEB-PROMPT path matches gold better overall, 456 cells of 519 against
      440. It wins 10 items, ties 15, and loses exactly one -- Q1, where the paper
      scorer is 19 of 20 against the web's 17. So the web is the right DEFAULT on
      scoring too, and Q1 is the standing exception.
      ON A TIE, PREFER THE WEB (user, 2026-08-28) and resolve the divergence that
      way: the web's reading is the reference and the CLI converges. It does NOT
      freeze the web's accuracy -- improving the web's own rule against gold is
      still the right work, and a change there is a change to the reference side,
      which is where changes belong. What the tie-break forbids is adopting the
      CLI's reading as the target merely because it lands on gold in the cells
      someone happened to write a declaration about. Q4b is the live case: 15
      against 15, so the web wins it.
      A NAMING TRAP worth stating: the artifact directory called `cli_v8` is
      agreement.py, the WEB prompt scored in python, and `paper_mini_v8` is
      score.py, the path this goal calls the CLI. Reading the directory names as
      sides inverts the conclusion, so cross_path now prints each side's KIND.
- [x] E6. **The criteria prose was written twice, and the copies had drifted.**
      Found while establishing subgoal E2's precondition. `score.py:build_prompt`
      held the `derive_from_criteria` block and `olx_prompts._criteria_section`
      held a copy whose docstring called it "score.py:build_prompt's
      derive_from_criteria block, verbatim". It was not verbatim: criterion 5's
      example ("{{corpus:PR/p1:pr:0:42:sha=34e8b80f4178:shape=C1}} body" against "a
      rested body, or fitness itself, following the behaviour that produces
      it"), criterion 7's example ("the extra chore" against "30 pushups"), and
      criterion 10's WK1 rule, which the web had grown and the CLI had not. All
      eight OC items were affected and every audit was green, because each side
      was internally consistent and this prose is authored in the SCORERS rather
      than in the rubric -- so it fell between the prompt audit, which compares
      rubric elements to the web, and the enforcement audit, which compares
      declarations.
      The CLI's copy had never been leakage-scanned either: `leakage.py` reads
      rubric `guidance`/`rule` strings and `SLOT_NOTES`, not `score.py`. The two
      drifted examples were the ones the web-side leakage rewrite had already
      replaced.
      FIXED STRUCTURALLY: score.py calls `_criteria_section`, so there is one
      source and nothing left to keep in step. The web's wording won everywhere
      except one case where the web was clearly wrong (below). Three
      substitutions remain, each forced by the CLI's ANSWER SHEET and each
      declared in EQUIVALENCE.md: `evidence` -> `behavior` (its criteria object
      has no evidence field), `yes`/`no` -> true/false (its criteria are
      booleans), and dropping "one point, and it charges ONLY this" (the engine
      computes the score; its model never sees points).
      THE WEB WAS CLEARLY WRONG ON DAY1, in two places, and was fixed to match
      what the CLI had: its criterion 7 said the avoidance reading "never changes
      the score" while its own guidance said "AVOIDANCE FRAMING TAKES THE WHOLE
      ITEM HERE ... the graders scored those zero", and its `consequence_asserted`
      note repeated the false half. Now declared once, on the rubric, as
      `rubric_h2.AVOIDANCE_SCORES`, and read by both generators.
      VERIFIED, 0 model calls: the 56-row `oc_grid` is IDENTICAL across the change
      (prompt text moved, scoring logic did not); 191 of 200 CLI criteria
      sentences match the web verbatim after the declared substitutions and the
      other 9 are numbered-list prefixes and a trailing period, each rule body
      confirmed character-identical to the web's note; exactly one web prompt
      moved (DAY1) and the other 22 are byte-unchanged.
      GUARDED: `enforcement.check_criteria_prose_has_one_source` fails the build
      if that branch stops delegating or if prose reappears in it, counting TOTAL
      literal length rather than the longest literal -- the first version passed a
      synthetic paste assembled from `+`-joined pieces. Both halves were proved to
      fire before being trusted.
      Two stale exemptions fell out of the change and were removed, and
      `consequence_asserted` left `check_slot_rules_reach_both_prompts`' BACKLOG
      by being FIXED rather than by rotting: score.py reads it now, so the
      "SLOT_NOTES is web-only" premise no longer holds for it. Which keys those
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
      cross-path divergence: Q4b/p4 paper 2.0 against web 3.5 with gold at 2.0,
      and cross_path localises it to these two slots. A `forbid` declaration is
      something `equivalence.py --enforcement` can compare between the scorers;
      the prose it replaces is not, which is why the divergence went undeclared.
      CONVERT THE PAIR TOGETHER. behavior_2 restates behavior_1's conditions for
      the second entry, so converting one alone would have the two entries judged
      by different machinery on the same item.
      DIRECTION: THE WEB MOVES TO THE CLI HERE. On p4 the paper path scores 2.0,
      which IS gold, and the web scores 3.5. So this is not a case of "web wording
      wins" -- that rule is about which way to SAY a shared rule, and it does not
      decide which of two answers is right. Gold does, and gold is with the CLI.
      The `forbid` declaration should reproduce the CLI's refusal and the web
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
          gold is 2.0, the CLI gives 2.0, the web 3.5 -- the web must charge MORE.
          On p12 gold is 5.0, the CLI gives 5.0, the web 3.5 -- the web must charge
          LESS, and what it applies there is the fifth test, a DELIBERATE divergence
          measured at +1 cell a run. So "make the web match the CLI on Q4b" is two
          changes in opposite directions, and the referent test addresses only p4.
          CORRECTION to what this entry first said. Both DECLARED cells favour the
          CLI, and I read that as the CLI being the better side on Q4b. Measured, it
          is not: `cross_path --gold --item Q4b` puts the item at 15 against 15,
          because p6 goes the other way -- gold 3.5, web 3.5, paper 5.0. Two
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
      all. Every one is DECLARED on the web and HAND-WRITTEN in `score.py` as an
      `if item["id"] in ...` branch, which the enforcement audit cannot compare
      because it compares declarations:

          key                          web declares          CLI does
          states_a_contingency         GATE (DAY1,DAY2,WK2)  branch -> NOT_OC
          agent_delivers_consequence   GATE (WK1)            branch -> NOT_OC
          aimed_correctly              GATE (WK2)            branch -> NOT_OC
          consequence_not_a_setup      forbid (DAY1,DAY2,WK2) hand-written conjunction
          barrier_is_not_this_type     forbid (NR)           hand-written conjunction
          targets_own_behavior         slot (all)            WK1 maps a pick by hand
          avoidance_frame              --                    DAY1 gates on it in code

      THREE ARE PLAIN GATES the web already marks with `!`. Nothing needs
      inventing: the declaration exists and the CLI does not read it. Those are
      the cheapest and should go first.
      TWO ARE THE SAME CONJUNCTION under different names -- both test
      `restriction_authored=created`, `trigger_expects=gain`,
      `restricts=other_thing` -- written out twice in score.py and declared as two
      separate `forbid` rules on the web. One rule, four implementations.
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
            `expect`-shaped. Now `rubric_h2.EXPECT`, generated into the web's
            `expect=` attribute by `olx_prompts.expect_attr_for` and read by
            `score._expect_rule`. The four `demonstrates_type` expects on
            NP/NR/PP/PR are deliberately NOT declared: the CLI reaches that fact
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
      CLI flag filter. The `build_schema` five are the obvious next candidates --
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
      one CLI flag filter (`score_participant`/`only`).
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
        (b) `score_participant`/`only` is a CLI flag filter, not a rule at all.
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
CLI 451/491, WEB 457/491, zero cells where the paths never agree.

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
      to it in both directions. Q4b/p12 is the demonstrated case: the web refuses
      an entry the CLI credits, six runs to six, and nothing flags it.
      SCOPED, 2026-08-28, at 0 model calls. The scoping was going to be a census
      of prose bullets; it turned into a MEASUREMENT, which is better, because the
      hazard surface and the actual damage are different sizes.

      THE HAZARD SURFACE: 70 of 150 authored prose blocks carry directive scoring
      language (REJECT / no credit / only when / takes the whole), concentrated in
      the OC items -- DAY1, DAY2, WK2 at 8 each, WK1 at 7. That is an upper bound
      from a deliberately loose regex, not a count of rules.

      THE MEASURED DAMAGE, from artifacts already on disk -- paper_mini_v8
      (score.py, 3 runs) against the web-prompt path, 520 cells present on both:
        18 cells NEVER agree in both of two independent comparisons ("robust")
        17 more diverge in one comparison and not the other ("era-only"): Q6 7,
           Q3 4, Q4a 2, Q4b 2, 2a 1, Q5 1. These are NOT attributable -- the two
           comparisons span different prompt versions, so version is confounded
           with path, and only an era-matched two-sided sweep separates them.
           That is subgoal E2, which is another reason it goes last.
      Of the 18 robust: 15 are 1c and 1 is Q4a, both DECLARED. Exactly TWO are
      undeclared, and both are stable in 3 of 3 runs rather than noise:

        1a/p6   paper 0.0 vs web 6.0-8.0. The paper scorer refuses the WHOLE item
                -- "-8 pts: did not discuss data for each week" -- on a 512-char
                answer with no error. CAUSE CONFIRMED: five `1a:*` SLOT_NOTES
                entries, 129 to 494 chars of judging text each, reach the web
                prompt and NOT the CLI's. Verified fragment by fragment.
        Q4b/p4  paper 2.0 vs web 3.5, and GOLD IS 2.0. The paper path charges what
                the graders charged and the web path does not. The rule doing the
                refusing is the guidance-prose REJECT test.

      SO THE BLINDNESS HAS TWO CHANNELS, not one. This subgoal was written about
      guidance prose; SLOT_NOTES is the other, and it is the one with a measured
      price tag -- 8 points on 1a/p6, every run. It already has a declared
      18-entry backlog in `check_slot_rules_reach_both_prompts` whose own comment
      says these "reach the web and CLI and silently leave the paper scorer
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
            web-only `1a:*` SLOT_NOTES entries -- and Q4b/p4 to
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
            rubric_h3's per-component `rule` fields. The web prompt did not move --
            byte-identical across all 23, because the web checklist looks up `rule`
            BEFORE SLOT_NOTES and finds the same string -- so every recorded web
            number stands and 1a did not go stale. Only the CLI gained text, which
            is the entire point.
            THE CLI NOW RENDERS SHARED RULES AS THE WEB DOES: `rule` REPLACES
            `desc` rather than being appended to it. The web has always done that
            (`rule or SLOT_NOTES or desc`), so the one field written to be read by
            both scorers was being rendered differently by each -- and since these
            rules are written to continue from the web's `— `, appending them after
            a desc produced "Discusses the baseline week is the BEFORE state
            given". No audit compared the two RENDERINGS, because both sides
            carried the text and the audit asks only whether it is carried. Blast
            radius is the only three items with rules: 1a, Q4b, Q6, whose CLI
            prompts change (the web's do not).
            The two measured findings in those notes' comments -- the partial-week
            failure the guidance did not anticipate, and the reverted experiment
            where p6 swung 8.0/0.0/6.0 -- moved into rubric_h3 beside the rules
            they describe. Deleting them would have destroyed the record.
            Backlog 17 -> 13, budget lowered with it, so the ratchet stays clean.
            The text is still leakage-scanned: leakage.py reads rubric `rule`
            strings as well as SLOT_NOTES, and the gate passes.
            NOT YET MEASURED, deliberately. This should fix 1a/p6's 8-point gap and
            it may move other 1a cells; three items' CLI prompts changed. The sweep
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
              slot `behavior_1`: paper not_active / cli met  [prose+rule, declared]
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
## PARKED — quality control on the remaining items

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

- [ ] Q27. **DAY1/p1 scores 0.0 against a gold of 4.0, deterministically, on both sides.**
      Filed 2026-08-30. DAY1 UNDER-credits one-sided -- cli 1 over / 8 under, web
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

- [ ] Q20. **The SHEET CANNOT REFUSE: over-credit with every check passing.**
      Two views of one phenomenon, merged 2026-08-28: cells where every scoring
      check passes and gold still docks, and the observation-level rate that says
      how much of our over-crediting works that way. Subgoal 22 held the second
      view and is folded in here.

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
      Measured 2026-08-28 over the CLI sweep's fourteen scored items, 6 runs each,
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
      AND CHECK IT ON THE WEB COLUMN. If the same 32 appear there, the sheet is
      missing a check and both scorers inherit it. If they do not, the CLI's
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

- [ ] Q23. **`matches_chosen_type` on WK2, and across the cadence family.**
      Measured 2026-08-28 over the CLI sweep, 6 runs, exclusions AND corrected gold
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
      MEASURED ON THE APP 2026-08-29, the first time NR has ever scored there --
      it was one of the seven items `forbid` made unrunnable (subgoal Q14). Web
      16/18, runs [14,15,15,16,16,16], against the CLI's 15/18. Era checked, 0 of
      20 cells never agreeing, so `forbid` -- the primitive that broke the item --
      computes identically on both engines. Direction 8 over / 14 under, so NR
      under-credits and is NOT a `requires` candidate (subgoal E15).
      THE GATE'S PRECISION REPRODUCES: `you_arrange_it` refused 32 times with 8 in
      wrong cells (75%) on the web against 34/10 (71%) on the CLI. Same
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
      web too (60 refusals, 12 in wrong cells), and every one of those 12 is
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
      ALREADY DECLARED: NR carries "CHARGE-ONCE WEB ONLY (barrier_is_not_this_type,
      demonstrates_type) cost less together on the web". Read it before changing
      either of those two, since the charge interaction is the declared part.

- [ ] Q19. **The LATER-BOX gradient, corpus-wide. Read this before any numbered slot.**
      Placed ahead of the item-specific subgoals because six of them are about a
      numbered box, and this says which part of that is one problem and which is
      six. Measured 2026-08-28 over the CLI sweep's first seven items, 6 runs each.
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
      AND CHECK IT AGAINST THE WEB COLUMN before acting: if the gradient is the
      same on both sides it is the prompt or the corpus, and if it differs it is
      the scorer. That comparison costs nothing once the app sweep lands.

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
      scored this cell: the WEB gives 3.5 in 11 of 12 runs (leak_fix 0/6,
      scorer_fix_6run 1/6 — one run reached 5.0), and the CLI gives 5.0 in SIX of
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
      The divergence itself stands: the web result differs from gold for the
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
- [ ] Q7. **Q4b's per-cell instability, which the item median hides.** Two cells
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
- [ ] Q11. **Q3/p13: `realistic` over-charged.** We charge where gold passed the
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
      their judging text in SLOT_NOTES, the web-only channel, and are three of the
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
      there at all until subgoal Q14. Web 16/19, EXACTLY the CLI's 16/19, era
      checked, 0 of 20 cells never agreeing. p12 returns 3.5 in all six runs on
      BOTH engines where it used to be CLI 5.0 / web 3.5 in eleven of twelve.
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
        `reason_2`    unmet 16, 4 in wrong cells.
        `reason_3`    unmet 47, 39 of them in cells that scored CORRECTLY -- so it
                      fires far more often than it explains. Treat a change here as
                      likely to move right cells, and control for them.
      DO NOT CHASE `confident`. Unmet in 92 of 120 observations with 79 of those in
      cells that scored correctly, and the top drifter at 14 cells changing verdict
      across runs. It fires constantly and predicts nothing; it is the noise floor,
      not a lever.
      WAIT FOR THE APP COLUMN. The two sides share this prompt and differ only in
      whose rules score it, so the same profile on the web side separates "the
      prompt asks badly" from "one scorer applies it differently". Acting on the CLI
      column alone would be tuning a prompt against one of its two readers.
      ALREADY RECORDED, do not rediscover: Q1/p9 is a declared divergence
      (GARBLED_CLAUSE_READ_LITERALLY, twelve configurations); p10 and p18 are
      subgoal Q14; the `harms_listed` ASSERTION-vs-AVOIDANCE clause and the two-tier
      `reasons_given` conditional are both live and measured. `python3
      olx_prompts.py --write` prints Q1's recorded comment blocks, and since
      2026-08-28 it prints the LATEST three, which is where the counting rule sits.

- [ ] Q14. **Q1's two live misses: p10 and p18.** Lifted out of subgoal Q12's
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

- [ ] Q24. **Q4a's `antecedent_2`: the slot that carries the item's remaining error.**
      Opened 2026-08-29, on the FIRST measurement of Q4a on the app -- it could
      not run at all before the LLMAction attribute fix (subgoal E14), and the
      web-only `max` defect had to be cleared before any cell scored on the right
      scale. So this is a channel nobody has ever been able to look at.
      THE SLOT PROFILE NAMES IT. Over 120 observations, web:
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
      DO NOT START FROM THE MEDIAN. The item sits at 18/20 web / 17/20 cli, which
      hides four cells that are wrong in two unrelated ways; and the by-slot
      table alone would have pointed the whole effort at wording, which p19 and
      p14 say cannot work. This is memory/error-profile-by-slot.md's rule and
      memory/fixture-defects-found-by-readout.md's rule applying at once.
      Direction is BALANCED -- 9 over, 9 under -- so unlike Q6 and Q4c this is
      not a `requires` candidate (subgoal E15): denying credit would fix the
      over-credits and worsen the under-credits by the same count.

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

The quality-control goal is PARKED, not closed: nine subgoals remain open under
it (2, 3, 7, 8, 9, 10, 11, 14, 15) and its section below is unchanged. It was
displaced rather than finished, because equivalence is the precondition for every
number it produces -- a per-item rate compared against gold means nothing while
the two scorers disagree about what the rules are.

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
