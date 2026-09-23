# Agenda items arising from the material classification, 2026-09-23
# To be folded into RUBRIC_MIGRATION_PLAN.md when the tree is free.

## A · Split `declaration_source.py` and `generator_source.py` along the seam

Each file holds TWO categories, and that is why every "does this move to the OLX?"
question needed a per-table answer instead of a per-file one.

  declaration_source.py
    -> COURSE METADATA (II):  HANDOUT_FIELDS, CONTEXT_SOURCE,
                              SLOT_STRUCTURE_FAMILIES
    -> DEVIATION RECORDS (II(a)/III): UNCHARGED_VERDICTS,
       DECOMPOSITION_DIVERGENCES, PROSE_ONLY_SLOTS, APP_ONLY_SLOTS,
       COUNTABLE_EXEMPT, PROSE_ONLY_JUDGED_AGAINST, HAND_AUTHORED_ATTRS,
       MULTI_BLOCK_DECLARED
    -> MEASUREMENT HISTORY (III): ASK_EQUIVALENT_PROMPTS, DESIGNED_TEXT, JOBS,
       STAGE, SELFTEST_NAMED_FIXTURES, PROBE_UNREACHABLE_PAIRS, PAPER_ITEM_NOTES*

  generator_source.py
    -> COURSE METADATA (II):  ACTION, RESPONSE, CONTEXT, SHEET_ONLY
    -> CROSS-SCORER DEVICES (III): EVIDENCE, OMIT_GUIDANCE, ITEM_NOTES,
       ITEM_NOTES_WHY, MATCH_DEF/EQUIVALENCE_DEF, SCORING_DIVERGENCES,
       PROBE_REACH_LIMITS
    -> SUBMISSION PARSING (IX): H1_MARKERS, H2_MARKERS, H3_MARKERS

Once split, the rule becomes mechanical: category II moves toward the OLX/
course.json, category III stays, category IX stays. No table needs arguing about
twice. `COURSE_DATA_BUDGET.json` counts per module, so the split changes those
counts and the ratchet must be re-tightened deliberately in the same commit.

## B · The handouts should be AUTHORED, not generated

Today `bmod_handout1|2|3.olx` are BUILD PRODUCTS of `olx_prompts.py`. That is why
category I currently contains both a source and a build product, and why "the OLX
is the source" is true of the rubric but not of the handouts.

Target: the handouts are hand-authored OLX, and `course.json` says which items
belong to each handout, keyed to the OLX ids, so a scorer can find what to score.

What that requires, in the order it has to happen:
  1. the generated prose in the handouts (`<LLMAction>` prompt bodies and the
     sheet attributes) has to come from somewhere at RUN time rather than being
     baked in at generate time -- or be accepted as authored and checked against
     the rubric instead of rewritten from it
  2. `olx_prompts --write` stops writing the handouts, and
     `check_idmap_is_current` / the prompt-freshness checks change meaning from
     "regenerate matches disk" to "disk agrees with the rubric"
  3. `prompt_sha` currently hashes the SERVED tag; a hand edit to a handout then
     moves it legitimately, so the freshness story needs restating
  4. course.json keeps item -> handout (it already does) and item -> OLX id

## RESOLVED: the item-to-component link lives in the RUBRIC

Decided 2026-09-23. `<Item asks="bmod_h1_q1_llm">` stays where step 3b put it, and
step B's fourth bullet is corrected to match: **course.json keeps item -> handout
and nothing more**; the item -> OLX id link is the rubric's `asks`.

The question was live because the alternative had a real precedent behind it --
`handout` was deliberately kept OFF `<Item>` on the ground that "which handout an
item belongs to is course structure", and the same argument could be made of a
component id. It does not hold, and the reason is worth keeping:

  WHICH HANDOUT an item sits in is a fact about the COURSE -- move the item to a
  different handout and nothing about how it is judged changes. WHICH COMPONENT it
  judges is a fact about the ITEM: change it and the item is judging different
  text. The first is placement, the second is identity, and only the second
  belongs beside the checks that do the judging.

It also keeps the property 3b bought: with `asks` authored on the item, `BLOCKS`
is DERIVED rather than declared, and the link that used to be written twice --
once in `BLOCKS`, once as `prompt_action` -- is written once.

So the division of labour is:
    rubric OLX    what is judged, how, and WHICH COMPONENT it judges  (`asks`)
    course.json   where the item sits in the course                   (`handout`)
                  plus the generator fields that shape the prompt


## C · No part of OLX prompt generation may depend on python

Stated 2026-09-23. For the OLX scorer, what shapes a prompt belongs either (a) in
the OLX rubric, or (b) in a generation chain run by `npm build` -- not in python.

WHERE THE DEPENDENCY ACTUALLY IS, stated precisely because it is narrower than it
sounds: at RUN time the OLX scorer needs no python, because the prompt bodies are
already baked into `bmod_handout*.olx`. The dependency is at BUILD time --
`olx_prompts.py` is what bakes them. So this is not a runtime coupling to break,
it is a PRODUCER to replace.

THE TS HALF ALREADY EXISTS AND IS UNWIRED, which is the important discovery:

    packages/shared/lib/llm/promptAssembler.ts     327 lines -- the prose half
    packages/shared/lib/llm/attributeAssembler.ts  222 lines -- the scoring half
    packages/shared/lib/llm/slotSheet.ts           the answer schema
    packages/shared/lib/llm/materialiseRubric.ts   template expansion -- WIRED
                                                   2026-09-23 as build:expand-rubrics

`promptAssembler` and `attributeAssembler` have NO CALLERS outside their own
tests. They are in exactly the state `materialiseRubric` was in this morning:
written, tested, and producing nothing. Meanwhile `olx_prompts.py` (~3,000 lines)
is what actually writes the shipped prompts. That is one rule with two
implementations, and the python one wins by being the only one plugged in.

WHY IT IS NOW TRACTABLE, and it was not before tonight:
  * the WORDS moved into the rubric -- oc_criteria's frame, the 27 `note:` frames,
    guidance, questions, credit and deduction text. `promptAssembler`'s design
    already assumes this: `Fragments` is supplied by the CALLER and NEVER
    defaulted, because "the KEYS are engine concepts; the WORDS are not".
  * `.stage/expanded` exists -- templates expanded, references intact -- which is
    the artifact an assembler has to read.
  * `renderFrame` in TS and `as_view_frame` in python already implement the SAME
    selection rule, deliberately spelled the same way.

THE SHAPE OF THE WORK
  1. a build step -- `build:assemble-prompts` -- that reads `.stage/expanded`,
     runs the two assemblers, and writes the handouts' `<LLMAction>` bodies and
     sheet attributes
  2. the fragments (the prose keys the assembler needs) sourced from the rubric,
     not from a TS default -- the assembler already refuses to default them
  3. `olx_prompts.py` keeps ONLY what feeds the PAPER scorer; its OLX-generation
     role retires
  4. the freshness checks change meaning with it, exactly as in item B:
     `prompt_sha` hashes the SERVED tag, so "regenerate matches disk" becomes
     "disk agrees with what the assembler produces from the rubric"

RELATION TO ITEM B. B asked for hand-authored handouts; C asks for npm-generated
ones. They are the two answers to the same question -- who produces the handout --
and both satisfy "no python". C is the cheaper one, because the TS assembler is
already written and the rubric already holds the words. B remains right for the
parts of a handout that are PAGE (layout, prose, figures) rather than PROMPT.
The likely end state is both: authored pages, assembled prompts.

PROOF OBLIGATION, and it is the same one used all night: the assembler's output
must reproduce the current handouts byte for byte before the python producer is
retired. Anything else is a prompt change wearing a refactor's clothes, and
`prompt_sha` will say so.

## C(i) · WHAT THE PRIOR DRY RUN ALREADY SETTLED about item C

Checked in `migration_reference` on the user's prompt, and it changes C from "new
work" to "work that was designed, built, and never wired".

THE PRIOR RUN'S README SAYS IT OUTRIGHT:
    "This is stages 02 and 03. The rubric moves into `.olx` as these blocks, and
     `promptAssembler` is what rebuilds the 26 prompt bodies from them byte-exact.
     Without it the migration cannot run at all."

So `promptAssembler.ts` and `attributeAssembler.ts` are not speculative utilities
that happened to go unused. They ARE the designed producer, and the reason they
sit unwired in our tree is that we ported the block family and the assemblers but
never the wiring that drives them.

THE HARNESS AND THE GATE ALREADY EXIST in `migration/`:
    stage02_assembler_surface.py   measures what the assembler must be GIVEN:
        "THE INTERFACE IS NOT A DESIGN CHOICE, it is a measurement... its input is
         whatever the current generator reads -- no more, and provably no less."
        It also feeds stage 03: every `item[...]` key it finds is a field the
        rubric object must carry, "or the assembler cannot be driven from the
        rubric at all".
    stage02_gate.py                the byte oracle
    stage03a_gate.py / stage03b_gate.py   blocks parse and validate; the engine
        stays content-neutral

THE ACCEPTANCE CRITERION, from the gate's own docstring, and it is exact:
    23 BODIES AND 26 ITEMS' ATTRIBUTES -- three items carry no `<LLMAction>`.
    And WHICH bytes: the GENERATOR's output, not the .olx element text, because
    the element carries a leading newline from the XML.
That 23/26 split is the same one measured independently tonight: 23 items carry
`asks`, 3 are deterministic.

WHAT THIS MEANS FOR SEQUENCING. C is not a new design. It is: run stage 02, then
03a/03b, against the rubric as it now stands -- which is in better shape for it
than the prior run's was, because the WORDS have since moved into the rubric and
`.stage/expanded` exists for the assembler to read. The proof obligation I wrote
independently ("reproduce byte for byte before the python producer retires") is
the gate that was already built for it.

## D · `gold_slots_q6.py` -- a CHECK that nothing runs

Separate from C, and it predates the migration: the prior run's patch touches it
by only 8 lines, so it was already there.

277 lines, imported by nothing. It defines `gold_slots_q6()`, `gold_view()`,
`unresolved_slots()`, `reconcile()` -- and
`check_corrected_slots_account_for_the_totals()`, whose docstring reads:
    "Each row's family changes plus its grid term must explain its total exactly.
     Signed, so a row that RAISES gold is checked as strictly as one that lowers
     it -- Q6/p4 is the only raising row and it is the one most in need of the
     check, since its correction mixes a slot (+1.25) with an off-grid regrade."
Referenced 0 times in equivalence.py, enforcement.py and precommit_gate.py.

A check that is not wired reports nothing forever, which is indistinguishable from
passing -- the exact failure this project fails a vacancy ratchet over. And its
subject is Q6, the item with the known matching ceiling, where the SAME PRINCIPLE
is wired for item 1c (`agreement.gold_slots_1c`, called at agreement.py:1828).

RESOLVED 2026-09-23: GENERALISE IT, do not wire it as it stands.

The first recommendation here was "wire the check as-is, scoped to Q6, which is
what it always was", on the measurement that only 2 of 15 CORRECTED_GOLD entries
carry itemised amounts and 4 of the 15 are Q6 -- so generalising appeared to buy
nothing. That reasoning was wrong, and the correction is the principle:

    AN ITEM-SPECIFIC CHECK IS ITEM CONTENT IN ANALYTIC MACHINERY. It is the same
    embedding this migration removes everywhere else, and `course_inventory`
    already counts it -- gold_slots_q6.py scores 3 ids and 2 named modules. The
    payoff is not today's coverage: a GENERAL check fires for content written
    later, and an item-specific one never will. Writing the specific one is
    choosing to miss the next item silently.

WHAT IT CAN BE MADE GENERAL ON, without inventing a declaration nobody fills in:

  (i) A CORRECTION MUST MOVE GOLD TO A REACHABLE VALUE. An item's score is max
      minus a subset of its component costs, so only certain values exist -- which
      `check_unreachable_gold_is_allowed` already relies on, for the OTHER side of
      the same fact (harnesses must forgive an unreachable gold). Nothing checks
      that a CORRECTION lands on a reachable one. The costs come from the rubric,
      so the check reads no item ids at all and fires on all 15 entries and on
      every future one. Q6/p4 is the case that motivated it: gold 6.00 on an item
      moving in steps of 1.25, corrected to 6.25.

  (ii) WHERE A CORRECTION STATES AMOUNTS, THEY MUST EXPLAIN ITS DELTA. This is the
      Q6 check's actual content, generalised: parse the amounts out of the
      reasoning the declaration already carries, and require them to sum. It
      covers 2 entries today and costs nothing per new entry.

  Both read slot costs FROM THE RUBRIC, which is now the single source for them --
  so this is only possible after tonight's work, and was not before.

THE Q6-SPECIFIC PARTS GO: `CORRECTED_FAMILY` (a table of Q6 pids), and the
per-slot reading (`gold_slots_q6`, `gold_view`, `unresolved_slots`). The reading
solves a problem Q6 does not have -- its wired analogue `gold_slots_1c` exists
because 1c's gold must be REBUILT from feedback, one of the four accounting steps
`check_gold_accounting_is_uniform` names. Q6's gold is taken from the sheet and
corrected where unreachable; there is nothing to rebuild.

So: delete the module, add the two general checks, and record the deletion reason.

## F · `1c`'s gold rebuild -- 16 embeddings, implemented TWICE, no owner

Measured with `course_inventory.py` (the prepared tool; it reports populations and
refuses to guess them). Item ids embedded in ANALYTIC machinery, outside the three
declared DATA modules:

    1c   16      <- this item
    Q6    8      3 in gold_slots_q6.py (item D); 4 in enforcement_selftest (D2a)
    Q1    4      reader_equivalence._mutations                          (D2a)
    Q4a/1b/1a  1 each   equivalence.py                                  (D2a)

MOST OF IT IS ALREADY OWNED. `equivalence.py`'s seven ARE the audit's one parked
finding -- "D2a (fixtures that select their target by shape) is the work that
removes them" -- and `reader_equivalence._mutations` is the same class: a
fault-injection fixture NAMING its target instead of selecting it by shape.

`1c` HAS NO OWNER, and it is the worst-shaped of the set:

    agreement.py       gold_slots_1c()  +  rebuild_gold_1c()
    agreement_app.py   rebuild_gold_1c()  AGAIN

and `agreement_app`'s copy says so itself:
    "Mirrors gold_slots_1c in agreement.py. The two must agree: a row scored on
     one side and dropped on the other is not a comparison."

A comment asserting that two implementations must agree, with nothing enforcing
it, is the exact shape removed from `oc_criteria` and from `SLOT_NOTES` tonight.
The remaining hits -- `GRAPH_UNREACHABLE_1C`, and `1c` in measured.py,
enforcement.py, compare_runs.py, olx_prompts.py -- are that special case leaking
outward across six modules.

IT GENERALISES EXACTLY AS ITEM D DOES. The fact is "this item's gold must be
REBUILT from the grader's itemisation, because the sheet's number cannot be
trusted for it". That is an item property -> it belongs in the rubric. The
arithmetic (`10.0 - 2.0 * failures`) is slot costs -> the rubric now holds those.
So: one rebuild, declared on the item, driven from the rubric, serving both
engines -- replacing two hand-kept copies and a comment hoping they agree.

RANK IT ABOVE D: the same generalisation, four times the footprint, and unlike D
it currently sits astride the two scorers' comparison, which is the one place a
silent divergence is most expensive.

`check_gold_accounting_is_uniform` already names `rebuild_gold_1c` as one of the
four things separating a published rate from a naive comparison -- so the rebuild
is load-bearing and must keep working byte-for-byte through the move. Same proof
obligation as everything else tonight.
