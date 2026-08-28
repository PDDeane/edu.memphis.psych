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
any rule written as guidance prose (subgoal 15, under the parked goal). Q4b/p12
is the demonstrated cost: the CLI scores it 5.0 in six runs of six and the web
3.5 in eleven of twelve, and nothing anywhere declares that.

- [x] 1. **Declare the mechanical flags -- or wire them up.** Three findings, all
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
      subgoal 2's list, which is now TEN items.
- [ ] 2. **A full two-sided sweep: every item, six runs, BOTH scorers.**
      Replaces "clear the stale H2 items", which would have measured one side of
      ten items. This measures both sides of all of them, and it is the only
      thing that can answer the question the whole goal is about: do the CLI and
      the web give comparable scores now?
      Ten items are stale from the leakage rewrite and the A_NONE/C_NONE wiring,
      subgoals 3-5 will move more, and every declared divergence in the tree is a
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
      as in the DAY1 contradiction subgoal 6 found and fixed.
- [x] 6. **The criteria prose was written twice, and the copies had drifted.**
      Found while establishing subgoal 2's precondition. `score.py:build_prompt`
      held the `derive_from_criteria` block and `olx_prompts._criteria_section`
      held a copy whose docstring called it "score.py:build_prompt's
      derive_from_criteria block, verbatim". It was not verbatim: criterion 5's
      example ("sleeping more will reward me with a rested body" against "a
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
- [ ] 7. **§2c's recorded-comment lookup is blind to all twelve H2 items.**
      Found in passing: `olx_prompts.prior_record` locates an item's rubric
      comments by grepping for the literal `"id": "DAY1"`, but `rubric_h2.py`
      builds its items from a factory, so no H2 item ever matches and the hook
      reports `could not read rubric_h2.py: StopIteration`. It has been reporting
      that, visibly, on every H2 `--write`. §2c is a discipline the record is
      supposed to enforce automatically, and on the handout with the most
      recorded dead ends it enforces nothing. Pre-existing, not caused by the
      subgoal 6 work.

- [x] 3. **Seven scoring rules the two sides implement separately.** Widened
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
      SIX OF THE SEVEN ITEMS ARE ALREADY STALE (subgoal 2), so this can ride that
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

- [x] 4. **Hash the scoring-path helpers, then re-stamp.** DONE. The three named
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
- [ ] 8. **Clear the seven entries left in HANDCODED_ITEM_RULES.** Set 2026-08-28
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

      ENFORCED, as of 2026-08-28: `enforcement.HANDCODED_BUDGET` is a two-sided
      ratchet at 7. Adding an entry fails the audit, and so does landing a
      conversion WITHOUT lowering the budget -- the slack would otherwise leave
      room for a replacement entry to arrive unnoticed. So this subgoal closes by
      the budget reaching 0, not by an argument that the remainder is acceptable.

ORDER, set 2026-08-28: 5, then 7, then 8, then the sweep. Subgoal 8 is the only
one of the three that can move a score, so it lands last and its effect is
measured BY the sweep rather than by a separate run. Nothing goes to the sweep
until all three are closed.
- [ ] 5. **The enforcement audit cannot see a rule written as guidance prose.**
      MOVED here from quality control, where it was subgoal 15: it is an
      equivalence-enforcement defect, not an item's scoring problem, and it
      sits directly beside subgoal 3. Both are the same failure in different
      clothing -- a rule the audit cannot compare because it is not declared.
      Subgoal 3 is rules hand-written in Python; this is rules written in
      PROSE. Found closing quality-control subgoal 5. The audit compares PRIMITIVES between the two
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
           That is subgoal 2, which is another reason it goes last.
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
        (a) land the cross-path cell comparison as a reusable tool rather than the
            throwaway script this scoping used, so the sweep produces the
            divergence table automatically instead of by hand;
        (b) give the SLOT_NOTES backlog the same two-sided ratchet the hand-coded
            table now has -- 18 entries with no ceiling is the same accumulation
            failure, and 1a/p6 shows it is not theoretical;
        (c) migrate the five `1a:*` notes to the rubric `rule` field, which both
            generators render, and measure 1a -- this is a scoring change on one
            item, so it belongs in the sweep;
        (d) for the prose channel, declare rather than compare: a registry of
            scoring-relevant prose rules, so the surface is KNOWN, with the sweep's
            divergence table as the detector.
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
- [x] 4. **The leakage detector's shared-prose blind spot.** Found twice today:
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
      p14/NR's "screen lock on my phone until I exercise" had become our canonical
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
- [x] 5. **Q4b/p12's declared divergence.** Accurate today, but its stated reason
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
      is a NEW gap, wider than this cell, and it is subgoal 15.
      The divergence itself stands: the web result differs from gold for the
      stated reason, and the refusing test measured +1 cell a run against deleting
      it. Only the false claim is gone.

- [x] 6. **Make the `reasons_given` rewrite live, then measure it.** DRAFTED,
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
      started at 17/20 before subgoal 12 took it to 18 by a different route.
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
- [x] 8. **A count slot outside the rubric's `counts` records nothing.**
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
      rather than a fix, and ten items are already stale. Carried as subgoal 16.
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
      restatement of the goal (p10 counts "my goal for this year is more
      active"), and a CONDITIONAL goal restatement (p6 counts "if I discipline
      myself ... I'll feel better about myself"). Gold rejects all three, and says
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
      counts "my goal for this year is more active" as a reason. That is a
      restatement of the goal, excluded in as many words by BOTH `reasons_given`
      and `benefits_listed`, and the model applies the exclusion correctly in
      only one or two runs. Its two real reasons (confidence, a balanced routine)
      are read correctly throughout, so nothing else in the cell moves.
      **p18, gold 5, correct in 3 of 6 runs -- a drift, not damage.** Its
      `harms_listed` counts "makes me become lazy and out of shape" as ONE effect
      in half the runs and TWO in the other half; the rule already says "two
      effects merely joined by `and` are two". Under the flat sum this was
      invisible because the student's benefit padded the total to three; the
      two-tier conditional made the harm count load-bearing and exposed a wobble
      that predates it. Fixing it means making the and-split deterministic, which
      is a classification question like p14's, not a counting rule.

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
