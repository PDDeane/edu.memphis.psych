# Jobs we need to do

Work items, not enforced declarations. The enforced backlogs — `SLOT_NOTES`
`BACKLOG`, `FIXTURE_GAP_BACKLOG`, `CONSENSUS_OVERLAP_BACKLOG`,
`CORPUS_QUOTE_BACKLOG` — live in `enforcement.py` and are keyed by cell or slot,
so a check fails when one goes stale. Nothing here is checked; it is a list of
things a person has to decide to do.

## The history rewrite holds BOTH properties; the trade was a bug, not a trade

**SETTLED 2026-09-16.** Every commit's python generates its paired `.olx`, and
every version still expands byte-for-byte to its original. Measured across the
whole history:

| | result |
|---|---|
| student sentences in history (concatenation-aware, 803 `.py` blobs) | **0** |
| every version expands to its original | **35126 / 35126** |
| `olx_prompts.py --check` at each generator+content state | **0 regressions** (107 clean, 6 error identically in the original, 1 no generator) |
| python + olx still compile | **0 regressions** across 29341 file-version pairs |

**THIS WAS FIRST RECORDED AS A TRADE, AND THAT WAS WRONG.** The entry here used
to say we had chosen byte-reversibility and accepted `--check` failing at 42 of
113 states, explaining it as an unavoidable disagreement: the generator and the
mechanical substitution segmenting the same sentence differently, one taking
`Q6/p8:change_a1:0:36` and leaving "Tuesday-Friday." as literal text while the
other took `0:53`. That story was coherent, matched the evidence, and was false.
There were two ordinary bugs underneath it.

**1. The shim never ran on the path that matters.** The wrapper that converts a
reference on its way into the .olx was APPENDED to `olx_prompts.py` -- below
`if __name__ == "__main__": raise SystemExit(main())`. A module run as a script
executes top to bottom and exits inside `main()`, so the wrapper below it was
never defined. `--write` and `--check` are exactly that path. The two sibling
shims sit on modules nobody runs directly, which is why they worked and this one
silently did nothing. Moving it above the guard took most of the states clean on
its own.

**2. A literal seam collapsed to a space instead of to nothing.** Python's
implicit concatenation joins adjacent string literals with NOTHING between them;
the only bytes that survive are the ones INSIDE the quotes. The rule collapsed a
quote-bearing separator to a single space, which is right whenever the source
reads `"... word "` -- nearly everywhere -- and wrong where a line wrapped
immediately after a hyphen, with no space in either literal. It turned
`Tuesday-Friday.` into `Tuesday- Friday.`: one character, and it was the entire
byte-for-byte proof.

**WHAT ACTUALLY RESOLVES THE SEGMENTATION DIFFERENCE.** With those repaired, each
commit's own generator writes its handouts, and the result is kept ONLY if it
still expands to the original blob; a handout that fails that test is thrown away
and the filtered bytes are restored for that file alone. 37 handout-versions are
the generator's, 44 kept their filtered bytes, and the proof cannot regress in
either case. Where a state still reports out of date -- commits #437-#441 among
them -- **the original history reports out of date too**, verified side by side.
A rewrite reproduces history's verdicts; it does not improve them.

**THE LESSON IS ABOUT THE EXPLANATION, NOT THE BUG.** A plausible account of why
something cannot be fixed is the most expensive thing to be wrong about, because
it stops the search. Two failures had merged into one symptom and the symptom
had a tidy story. What broke it was not more analysis but one control: does the
ORIGINAL survive its own `--write` unchanged? It did, exactly, which meant
nothing about regeneration was inherently lossy and the loss was ours.


## Five definitions sit below a main guard, and are dead on the script path

**FOUND 2026-09-16** by `check_no_module_defines_names_after_its_main_guard`,
added after the same mistake cost the history rewrite a day:

| module | name | guard |
|---|---|---|
| `guide.py` | `LESSONS_APPROVED`, `_lesson_leads`, `unapproved_lessons` | 276 |
| `probe.py` | `recorded_answers`, `control_gate` | 569 |

A module run as a script executes top to bottom and exits inside
`raise SystemExit(main())`, so a definition below that line exists **only when
the module is imported**. `probe.control_gate` is the guard that voided two
probes for measuring their own envelopes; run `probe.py` directly and it is not
there at all.

**FIXED 2026-09-16 — this entry was simply never updated.** All five moved above
their guards the same day they were found; both modules carry a
`MOVED ABOVE THE MAIN GUARD` note saying so. The guards now sit at
`guide.py:517` and `probe.py:717`, below every one of the five, and
`check_no_module_defines_names_after_its_main_guard` reports 0.

The deferral argument above never applied to the dry run in any case: it is a
separate tree whose commits travel with the refactor rather than being replaced.

READ THIS BEFORE TRUSTING THE NEXT BACKLOG ENTRY. Checked 2026-09-20 by grepping
for the names and comparing line numbers against the string
`if __name__ == "__main__":` — and the lines that matched were the COMMENT
quoting that string inside the fix's own note, not the guards. The reading said
"all five still sit below their guards", which is the opposite of the truth. What
caught it was this entry claiming the audit carries five findings while the
measured baseline is 1: two instruments disagreeing, and the wrong one was the
fresh reading, not the old record.


## Nine hard-coded paths that `paths.py` already resolves

**FOUND 2026-09-16** by `check_no_module_hardcodes_a_path_that_paths_py_resolves`.
`paths.LO` is `os.environ.get("LO_BLOCKS", ...)` so the tree being measured can
be chosen; these ignore that:

| where | literal | should be |
|---|---|---|
| `agreement_app.py:1648` | `/home/pdeane/code/update/lo-blocks` | `paths.LO` — **unconditional** |
| `enforcement.py:4304` | `/home/pdeane/code/update/lo-blocks` | `paths.LO` — **unconditional** |
| `enforcement.py` ×5, `measured.py` ×2 | `/home/pdeane/molly_data/out` | `paths.OUT` — fallback for a missing attribute |

**Why this is not cosmetic.** The migration runs on THIS tree, with a copy kept
for rollback — so these literals are right today, **by coincidence**. They stay
right only while nobody points the harness at a sandbox, a second checkout, or
the backup copy; the moment someone does, the literal wins over `$LO_BLOCKS` and
the run succeeds against the wrong tree while every gate passes. That is exactly
what the dry run's own scripts did: eleven named their sandbox literally, and on
a live tree they would have migrated the sandbox and reported success.

The seven fallbacks deserve a second look rather than a mechanical fix: if
`paths` has no `OUT`, silently reading the developer's own artifact directory is
the least safe available behaviour. Failing closed is the right default.

**DONE 2026-09-20.** All nine are gone. The last two were
`check_ref_grammars.py` and `check_slot_grammars.py`, each carrying its own copy
of `paths.LO` as it stood before the `.lo-blocks` marker — so this checkout's
gate read TypeScript out of the LIVE tree and ran live's `node_modules/.bin/tsx`
with `cwd` at the live root, right only because both checkouts happened to sit at
the same commit. The only `molly_data/out` strings left are inside the check's own
docstring and its message-building logic, declared in `ABSOLUTE_PATH_EXCEPTIONS`.
`check_filesystem_locations_come_from_paths_py` reports 0.

AND THE CHECK HAD A HOLE THAT HID TWO OF THEM: it scanned string constants
beginning `/home/`, `/Users/`, `/tmp/`, `~/`, while
`Path.home() / "code/update/lo-blocks"` spells an absolute location whose only
literal is RELATIVE. A new arm matches `<x>.home() / "literal"`. It did not work
when first written — placed at function level, after the per-file loop, where
`tree` and `path` hold whatever the last file left — and the 0 it returned looked
like a pass. Found by injecting a probe carrying the exact pattern rather than by
reading the 0 as proof.

## Generalise the per-slot gold summary to every item

`agreement.gold_slots_1c(feedback)` reads the grader's verdict on all five of
1c's slots out of their comment, on the principle that these graders itemise what
they took off, so a criterion they never mention passed. It exists for 1c only.
`gold_slots_q6.py` now does the same for Q6. **Both are per-item, and the pattern
should be one function that works for any item.**

Why it is worth doing: gold ships `score` plus deduction prose and nothing else,
so without this there is no way to ask WHICH slot a disagreement is on — only
whether the total matched. With it, the 20 Q6 cells resolve to 14 slot errors of
152 judgements, 7 false credits against 7 false refusals, concentrated in
`state_c1`. That is the analysis that says what to fix next, and it is currently
impossible for 24 of the 26 items.

What the Q6 version establishes about the design:

- **The deduction amount is part of the reading, not just a check on it.**
  "Missing second antecedent" at -2.5 charges the naming AND the how-half; the
  same words at -1.25 charge one of them. Words alone cannot separate those. Any
  generalisation needs each item's per-slot point value to do this, which
  `publishedSheet`/`slots=` already carries.
- **It is self-validating, and that is the reason to trust it.** The slots a parse
  says were withheld must account for exactly the points deducted. Q6 reconciles
  on 19 of 20 cells; the drafts before it reconciled on 14 and then 17, and each
  failure was a real bug (boilerplate read as deductions, a purpose clause read
  as a second charge, the amount ignored). A per-item parser without this check
  would have shipped all three silently.
- **Gold's pasted advice must be stripped, not skipped.** These comments often end
  with a fill-in-the-blank template naming EACH antecedent and EACH consequence;
  read as deductions it charges the whole sheet. Dropping the chunk it sits in is
  not enough either — it cost p5's third deduction, written on the line above one.
- **Reconcile against the nearest ATTAINABLE score, not the sheet's number.**
  Q6/p4 deducts -1.5 for "missing one antecedent" on an item moving in steps of
  1.25. Read against the sheet's 6.00 that cell looks unrecoverable; read against
  the 6.25 that `handouts.nearest_attainable` already licenses -- the same rule
  `scores_as_exact` applies at score level, whose docstring names this very cell
  -- it is three withheld slots and reconciles like every other cell. A
  generalisation that skipped this would drop cells it could read.
- **Count and identity are separable, and only the count is always recoverable.**
  p4 names two of its three withheld slots and says "one antecedent" without
  saying which. The half is still legible (no `how` language, so the naming
  half), which narrows it to `state_a1`/`state_a2` -- and since our scorer refuses
  both, the ERROR COUNT is the same whichever gold meant. Report the ambiguity;
  never pick one, because downstream an arbitrary pick reads as gold's verdict.

- **Compare per-family COUNTS, not box attribution -- gold's ordinals are
  TALLIES, not indices.** This is the one that changes the design rather than
  refining it. Gold writes "second antecedent is not the same as mentioned in 4a"
  and "did not state a second consequence", and the natural reading is that
  "second" indexes something. It does not, and Q6/p6 proves it: its two families
  need OPPOSITE index readings for gold to be true. The antecedent clause is true
  only if "second" means the second thing the student NAMED (the box holding the
  unlisted item), because the second BOX holds text that is in 4a. The consequence
  clause is true only if "second" means the second BOX (which is empty), because
  the second listed consequence IS addressed -- in the first box. No single index
  reading satisfies both. Read as tallies -- "you named two antecedents but one is
  not in 4a", "you named only one consequence" -- both are true and ordinary.
  Measured across the 20 cells: as indices 13 of 20 agree with our scorer, as
  tallies 14 of 20, and p6 is the cell that separates them.

  This also matches what the rubric SCORES. `cover="state_a1,state_a2:first,
  second"` asks that the two boxes between them cover both listed entries in
  either order; it has never required box 1 to address entry 1. The rubric is
  count-based within a family, so counts are the commensurable quantity, and an
  index reading imports a pairing constraint that neither the rubric nor the
  graders apply.

  So: report per-family counts as the measure. Any box-level attribution the
  summary produces is a HYPOTHESIS to check against the student's text, never
  gold's verdict -- reported as such, or not at all. Attribution that gold never
  asserted invented two slot errors on p6 and two on p15, and both cells were in
  fact in complete agreement.

  The cost of the tally reading is real and should be stated wherever it is used:
  it says a family is short by one without saying WHICH entry went unaddressed, so
  it cannot on its own drive a rule about which match failed. That question needs
  the student's text and the 4a/4c entries side by side, not gold's prose.

Open questions for whoever does it: where it lives (`agreement.py` beside
`gold_slots_1c`, or its own module both harnesses import); whether the
item-specific phrase-to-slot vocabulary can be derived from each item's slot
labels rather than hand-written per item; and whether `gold_slots_1c` should be
re-expressed in terms of it, which would be the proof that it generalises.

## ~~Q5 `example_2` names a token the olx enum does not have~~ FIXED 2026-08-30

`bmod_handout1.olx:1072` tells the olx grader to answer `not_reason` when the
second entry is a real, distinct entry that is not a reason for CONTINUING. The
same line's `slots=` offers that check `wrong_kind/duplicate`. So the test is
inert: the model is asked for a token it cannot return, and the diagnosis the
rule exists to draw never gets drawn. It has to be reading through to `absent` or
`met` instead, which are different findings.

This is the exact failure the `{fail}` placeholder was built to prevent —
`olx_prompts.py:1682` records the last instance of it, where the paper scorer was
told when to answer `wrong_kind` while being offered `met/absent/not_active`, and
"every test was inert and it credited p8's 'avoiding going the gym' that the olx
and python both reject." Same slot family, same year.

Why the guard missed it: `{fail}` is substituted into the rubric's `rule` text
only (`olx_prompts.py:1698`). The offending string is a SLOT_NOTES entry
(`olx_prompts.py:1245`), which is a SECOND source of prompt prose and gets no
substitution. Two candidate fixes, and the second is the one that closes the
class:

1. Put `{fail}` in the note and run the same substitution over SLOT_NOTES.
2. Lint it: no prompt prose may name a verdict token that the slot it describes
   does not offer. That is the content lint stage 08 of the verdict-vocabulary
   plan calls for (`../VERDICT_VOCABULARY_PLAN.md`), and it would have caught
   both instances without anyone having to think of `{fail}`.

Fixing it CHANGES A PROMPT for Q5, so it needs a sweep. Six passes now exist
(`out/web_v8`, `out/web_v9`) and the fixture audit below measured what the dead
note does and does not cost: refusals still happen, under `wrong_kind`, so what
is lost is the DISTINCTION the note draws rather than the deduction itself — and
no COUNTED cell exercises a refusal at all, so the fix cannot be validated on
the rate. Read that section before sweeping.

FIXED 2026-08-30, by route 1 AND route 2 -- the instance and the class.

The note MIGRATED out of SLOT_NOTES into the rubric's `rule` on Q5's `example_2`
component, where `{fail}` is substituted per side: the olx now renders
`wrong_kind` and the paper scorer `not_reason`, each its own vocabulary. The
olx prompt changed by exactly that one token and nothing else, confirmed by
`olx_prompts.py --diff` showing a single changed line. `duplicate` stayed
literal, which is correct -- slot_vocab.SHARED_EXTRAS shows both sides offer it.

The CLASS is closed too, by the lint this entry asked for:
`enforcement.check_prompt_prose_names_only_offered_verdicts` reads every source
of prompt prose that is NOT a `rule` -- SLOT_NOTES today -- and reports any
verdict token the slot cannot return. Two things it has to get right, both of
which a naive version gets wrong: `pick(NAME)` options come from the sheet's
`choices=` map (without resolving them D1/D2:named_type read as naming `unclear`
against a met/absent slot, two false positives on correct prose), and a GLOBAL
note reaches a slot only when that slot has no `rule` and no item-scoped note,
so the precedence mirrors the generator's. A scan of all 24 SLOT_NOTES entries
found no other instance.

The lint is itself guarded: the audit self-test injects the historical defect and
requires the check to fire ("prompt prose asks for a verdict the slot cannot
return" -> PROMPT ASKS FOR AN IMPOSSIBLE VERDICT), with the site and the token
chosen at run time so it does not die silently the day a note migrates.
SELFTEST_EXPECTED 50 -> 51.

MEASURED AT THE TIME, on the regenerated prompt f933e0876c3b and a fresh
idmap_v97 proven to carry the new line: Q5 python WAS 19/20 and olx WAS 19/20,
both unchanged from 19/20 at the time, era checked, 0 cells never agreeing. That prompt has since
been superseded and both sides now read 18/20 on the 2026-09-14 sweeps; the
figures above are the record of what f933e0876c3b measured, not a claim about the
current configuration. Neutral, as this entry predicted it would be --
no counted cell exercises a refusal, so what the fix buys is the distinction
being drawable, not a different score.

`not_reason` in `rubric_h1.py:979` is NOT part of this — that is the paper
scorer's own vocabulary, bridged by `enforcement.ALIAS`, and it is correct there.

## 2a: what the fixture audit left behind

The fixture itself is done — all 20 cells read out box by box, two repaired
(p16's unstripped `"Sentence 3:"` label, p20's comma-initial `how1`), and the
split declared in `enforcement.MULTI_BLOCK_DECLARED`. Everything below is what
the readout found that a fixture fix cannot reach.

**Re-baseline first: the numbers here predate the two repairs.** Derived from
`out/web_v8` and `out/web_v9`, three passes each, honouring `cell_exclusions`:
**14-16 of 18 counted** (15-17 of 20 with exclusions in the denominator) — it
was 14-15 of 17 until p18's exclusion was removed, leaving only the
`self_graded` p1 and p14 outside the rate. p16 is one of the cells whose fixture
just changed, so its six passes no longer describe what would be served.
Re-derive before attributing anything to a change.

### The over-credit is one shape, and it is the only shape

Almost every miss is **+2.0, crediting a second `how` gold withheld**, and on
the three cells below that holds in both directions across all six passes. The
exception is p18, which is neither this shape nor a consistent miss — it agrees
at 6.0 in five passes and dropped to 4.0 in one. So the item still has a single
target, and it is these three:

| cell | gold | ours | passes wrong | gold's stated reason |
| --- | --- | --- | --- | --- |
| p13 | 4.0 | 6.0 | 6 of 6 | "your third sentece does not explain how your plan was successful" |
| p16 | 4.0 | 6.0 | 6 of 6 | none — the row deducts 2 and says nothing |
| p15 | 4.0 | 6.0 | 4 of 6 | "your second sentece does not explain how" |

No cell in the item errs the other way, which makes this a one-directional
target: a rule that can only refuse a `how` cannot disturb the twelve cells that
already agree.

The hypothesis the readout supports is POSITIONAL, not a wording problem.
`rubric_h3.py:342` opens the guidance with "COUNT CONTENT, NOT SENTENCES ... Two
sentences can earn all six points, and three shapes did", enumerates the three
shapes that earned 6/6, and only then, at `rubric_h3.py:352`, says to DEDUCT for
a stretch that does not bear on how the plan succeeded. That is the shape
QUALITY_CONTROL.md §3 names twice over — a categorical instruction that
pre-emptively dismisses the exception, sitting above the components that need
it. The thing to try is not another rewrite of either bullet: it is to put the
deduct test immediately before the `hows_given` component that applies it,
and to make the permissive bullet defer to it explicitly.

**Choose the target before measuring.** p13 is the honest one: gold names the
sentence it charged, the fixture holds that sentence in `how2`, and our grader
credits it anyway. p16's gold deducts 2 with no reason recorded at all, and its
three sentences are a verdict and two explanations on any reading — so decide
whether p16 is a target or a `GOLD_DIVERGENCES` entry BEFORE tuning toward it,
or the rule gets fitted to an unexplained row. Changing this guidance changes a
prompt, so it needs a corpus sweep, not a 2a probe.

### p18's exclusion was stale and is REMOVED — settled

`handouts.py` said gold's 6.0 was unreachable because `join_aware` strips the
template verdict the student copied, so "no verdict of p18's own survives". The
record never agreed: `verdict` came back **`met` in 6 of 6 passes**, every one
citing [[corpus 2a/p18 verdict 0:77 sha=6d41c38a4671]] — a sentence the student did write — and the cell scores gold's 6.0 in 5
of the 6. The item's own guidance licenses that reading in terms ("a verdict
that cites the data as its evidence ... covers the verdict and both
explanations", one of three shapes it says earned 6/6). The copied sentence was
never what carried the credit.

So it was QUALITY_CONTROL.md §5's second rule exactly — an exclusion on a cell
the scorer gets RIGHT — and it is gone. `expect_error: -2.00` went with it. The
counted n is 17 → 18, and the rate rises in five of the six stored passes and
falls in the sixth (web_v8 run 1, where p18 answered `hows_given: 1`), which is
the honest cost of counting a cell that flips once in six.

Two things it leaves behind, both worth keeping:

* **The exclusion was silencing a second question.**
  `check_consensus_spans_are_disjoint` skips `unscoreable` cells, so p18's `verdict`/`how1` overlap had been exempt
  by side effect for as long as the cell was excluded — nobody had ever judged
  it. Removing the exclusion surfaced it the same minute, and it is now declared
  on its own merits in `CONSENSUS_OVERLAP_BACKLOG`, beside p20's identical case.
  An exclusion written about the SCORE silences every other question about the
  cell, and that is an argument for declaring rather than excluding wherever the
  choice exists.
* **p18 is now the item's only unstable cell**, at 5 of 6. If it flips again,
  the thing to read is `hows_given` — the one bad pass answered 1 where the
  other five answered 2, on an unchanged fixture.

### p1 is the self-graded red flag, and it is the same shape

p1 and p14 are registered in handout 3's `cited_participants`
(`handouts.py:322`) and excluded as `self_graded`, which is correct — 2a's
guidance quotes p1's answer AND the grader's -2. But p1 comes back **wrong in 6
of 6 passes**, over-crediting by exactly the +2.0 above, with the deduction
printed in the prompt it was given. Per the rule in EQUIVALENCE.md, that is a
diagnostic rather than a rate: the item's judgement is unstable, and p1 is the
cell that should flip first if the positional fix above works. Watch it; do not
count it.

### 2a's fixture is not frozen, and one published claim about it is stale

`from_scorer` builds these three boxes from `out/h3/participant_NNN.json`, so
they move whenever the paper scorer is re-run — the reference re-run recorded at
`EQUIVALENCE.md:1763` already invalidated 2a's olx numbers once for exactly this
reason, and Q6 was frozen from a 10-run consensus after its spans moved on 47%
of slots per rerun. Until 2a is frozen or hash-pinned, any comparison spanning a
paper re-run is not like-for-like.

Related: `EQUIVALENCE.md:487` still lists 2a among the eleven items that "agree
on every single cell". That is the superseded web_v2 sweep; on web_v8/v9 the
item is 14-15 of 17. The line sits in a dated section, but it is the kind of
stale headline §5 warns about and should be annotated where it stands.

## Q4a: what the fixture audit left behind

The fixture needed **no repairs** — all 20 cells read out, every box whole
sentences in document order, and the only unassigned text in the item is
enumerators and OCR debris. Declared in `enforcement.MULTI_BLOCK_DECLARED`. So
unlike 2a, nothing here invalidates a stored number: the figures below still
describe what would be served.

**Where the item stands.** `out/web_v8` and `out/web_v9`, three passes each,
honouring `cell_exclusions`: **12 of 13 counted, identical in all six passes**,
and **16 of 20** with the exclusions in the denominator. Seven cells are
`self_graded` — the guidance cites p3, p4, p6, p9, p14, p15 and p17 by number —
so a third of the item is outside the rate, which is worth remembering before
reading 92%.

Note for anyone comparing: `EQUIVALENCE.md:919` and `:1233` quote Q4a at 76-82%
over **n=17**, which predates the citation registration. Those figures and the
current 12/13 are different denominators, not a change in the item.

### p19 is the item's only remaining error, and the prompt contains its answer

`antecedent_1` comes back `wrong_kind` in **6 of 6 passes**, every one citing
"{{corpus:Q4a/p19:first:23:58:sha=ca9d4ea70d5d:shape=S4-20}}" — which is the phrase the item's own
guidance lists in its ACCEPT bullet, in the sentence that says those examples
"all earned full credit" (`rubric_h1.py:683`). So this is not an
under-specified criterion. The grader is refusing an example the prompt tells
it to accept, verbatim, and the cell loses exactly the 2 points that refusal
costs.

Two things follow, and the second is the one to act on.

* **The prompt reproduces a counted cell's own answer, undetected.**
  `check_rule_examples_are_not_corpus` needs an 8-word shared run; this phrase
  is six, and its neighbours in the same bullet ("{{corpus:Q6/p15:state_a1:42:60:sha=62509878f808}} that need
  to be filled", [[corpus Q4a/p15 second 0:29 sha=ee91313d5faa]]) are p15's. p15 is declared,
  p19 is not — and p19 is the cell that misses. The check's docstring already
  says it is a floor rather than a guarantee; this is what falls through it.
* **`antecedent_1` and `antecedent_2` carry no `rule` field at all.** Every
  accept and reject test for this item lives in `guidance`, which both
  generators render as prose well below the components that use it. That is the
  configuration QUALITY_CONTROL.md §3 says to change first — Q6 moved a target
  cell 11% → 78% by putting two sentences immediately BEFORE the components
  rather than rewriting the guidance forty lines above them. The test to move is
  the accept side: a circumstance or state of mind qualifies, and plausible
  precedence is enough without a causal chain.

Predict before measuring, and name a control: the twelve cells that already
agree must not move, and p14's `antecedent_1` — the same state-of-mind shape,
credited on purpose against gold — is the cell that says whether the change
widened acceptance too far.

### p18's second box: DECLARED, an intentional divergence — settled

p18 wrote one antecedent and repeated it verbatim as its second, so `second` is
empty and 153 characters of the response belong to no box. The fixture
deliberately leaves it empty rather than serving the duplicate, and that is now
a declared divergence from verbatim reproduction rather than a decision waiting
to be taken. Do not "fix" it.

Why: gold's row is "-2 pts: only provided one antecedent", the cell agrees with
it at 3.0 in 6 of 6 passes, and filling the box invites the grader to credit two
antecedents on one sentence. The divergence is from FAITHFULNESS, not from gold,
which is why it is not in `GOLD_DIVERGENCES` — we and the graders agree about
this answer.

It is also self-enforcing, which is the part worth knowing. Nothing had to be
added to a table: `check_fixture_covers_the_response` sees the empty box and the
unassigned run, asks `_gold_corroborates_absence`, and gold's "only provided
one" licenses the gap on every run. If gold's wording were ever restated as
"does not match", the check would start failing and this decision would come
back up on its own. The declaration itself lives in Q4a's
`MULTI_BLOCK_DECLARED` entry, next to the split it is about.

### Everything else in the item is already declared

Stated so a future pass does not re-open it. The three cells that differ from
gold besides p19 are all in `handouts.GOLD_DIVERGENCES` and all three were
confirmed against the readout and six passes: p9 and p15 lose the keyword point
the dictionary requires and the graders did not charge (`kw=absent` in every
pass, and the responses genuinely never use either word — nothing was lost in
the split), and p14's `antecedent_1` is credited against a gold row that
refused both examples while its commentary accounts for only one. No stale
exclusion surfaced: of the seven cited cells, none is wrong beyond those
declarations, so none of them is buying a flattering denominator.

## Q4c: what the fixture audit left behind

Three boxes repaired, all one defect: p13's `first` and both of p16's kept the
student's enumerator inside them ("1) {{corpus:Q4c/p13:first:0:15:sha=f2014335e974}} ...", "1. One consequence
...", "2. Another consequence ...") while the item's other eight enumerated
cells strip theirs — p12, whose response has p16's exact "1."/"2." shape, starts
after the marker. That is 2a/p16's "Sentence 3:" defect in a second item.
Everything else confirmed and declared in `enforcement.MULTI_BLOCK_DECLARED`.

**Re-baseline p13 and p16.** p13 is a COUNTED cell whose served text just
changed, so its stored passes no longer describe what the grader would see. p16
is excluded, but its `expect_error` is asserted every run, so it needs the same
treatment.

**Where the item stands.** `out/web_v8` and `out/web_v9`, three passes each:
**12 of 12 counted, identical in all six passes**; **17 of 20** with exclusions
in the denominator. Eight of the twenty cells are outside the rate — seven
`self_graded` (the guidance cites p4, p9, p11, p12, p15, p17 and p20 by number)
and p16 `unscoreable`.

### 12 of 12 does not mean the item is finished

Read the counted set: **eleven of the twelve cells have a gold row of 5.0**, and
the twelfth is p13, whose deduction is a missing second consequence. So no
counted cell in this item requires REFUSING a consequence the student stated.
Every cell that tests that — p4, p9, p11, p20, p16 — sits in the excluded eight.
The rate measures the accept side and is silent on the criterion the item exists
to apply, which is why 12/12 should not be read as a finished item the way Q4a's
12/13 can be.

What the excluded cells say when read as diagnostics, six passes each, is that
the two reject channels behave differently — and the prompt quotes the very
cells that test them:

* **The category test works.** The REJECT bullet's example is p9's own
  [[corpus Q4c/p9 second 0:91 sha=12edb7359b67]], and `consequence_2` comes back `wrong_kind` on exactly that
  text, 6 of 6. A benefit of the goal behaviour is being caught.
* **The sufficiency test does not.** The DEDUCT bullet quotes p20's
  [[corpus Q4c/p20 second 53:80 sha=28c59f23b412]] and records that the grader wrote "need more explanation on
  how your second example is a direct consequence". Our grader answers `met` on
  that sentence in 6 of 6 passes. "The causal link is left for the reader to
  guess" is a different judgement from "this is not a consequence at all", and
  only the second one is reaching the model.

So the work here is the sufficiency test, not the category test. It is also the
test with no counted cell behind it, so any change to it must be measured on the
excluded cells as a diagnostic and swept corpus-wide for damage elsewhere.

### p9's residual gap is a gold shape that is already declared elsewhere

Our 3.0 against gold's 1.0 is not the cited example: `consequence_2` is refused
as designed. It is `consequence_1`, [[corpus Q4c/p9 first 0:47 sha=649fd6c0427a]], which gold also refused — its -4 is two refusals while its
commentary accounts for one. That is the same shape as Q4a/p14, which
`handouts.GOLD_DIVERGENCES` already declares in those words. Q4c/p9 has no such
entry, and should get one if its citation is ever removed; while the citation
stands, the `self_graded` exclusion covers it.

For the record, the fixture is not the cause: p9 is one run-on line with a
single comma, and the split leaves [[corpus Q4c/p9 first 26:47 sha=5a8116110b45]] with the clause that
comma attaches it to. Splitting the other way leaves `first` as a bare
[[corpus Q4c/p9 first 0:25 sha=3b3d3ba759d6]], which is creditable too.

### Two cited cells the scorer misses anyway

p9 and p20 are cited in the guidance AND wrong in every pass — which is exactly
the case EQUIVALENCE.md's cleanup procedure says to close: "if the scorer misses
it even so, the exclusion is buying a flattering denominator and nothing else",
and the citation and the exclusion have to move together
(`check_citations_match_exclusions` enforces the pair). The other five cited
cells are scored correctly and their exclusions are doing their job.

Two things make this more than a deletion. The examples being removed are the
item's ONLY reject and deduct illustrations, so they have to be REPLACED with
invented ones rather than dropped — writing them from a participant's answer is
the mistake that created this. And the reported rate will FALL, from 12/12 to
12/14 on current behaviour. That is the point of doing it.

### A superseded section to annotate

`EQUIVALENCE.md:562` reads Q4c at "python 76%, olx 65% over 17 cells" and closes
"Nothing to fix. Left alone." All three parts have moved: the denominator is 12
counted, not 17; its olx-only p13 gap was `keyword: absent` on "conequence",
which cannot arise now that Q4c's keyword slot is advisory with `pts=None`; and
three boxes were in fact fixed above.

## Q5: what the fixture audit left behind

Three boxes repaired, the same enumerator defect Q4c had: p1 kept "1) " and "2)
" inside both boxes and p16 kept the "2. " it is the only cell to write, while
p8, p10, p12, p18, p19 and p20 all start after their markers. Third item to
carry this, after 2a/p16 and Q4c/p13+p16. Everything else confirmed and
declared in `enforcement.MULTI_BLOCK_DECLARED`.

**Re-baseline p1 and p16.** Both are COUNTED cells whose served text changed.

**Where the item stands.** `out/web_v8` and `out/web_v9`, three passes each:
**14 of 14 counted, identical in all six passes**; 19 of 20 with the six
`self_graded` cells in the denominator (the guidance cites p4, p6, p8, p9, p19
and p20 by number). Note for comparisons: `EQUIVALENCE.md:492` has Q5 at "100
vs 88" from web_v2, a different denominator and a superseded fixture.

### 14 of 14 is a rate over twelve free cells and two blanks

Of the fourteen counted cells, **twelve have a gold row of 5.0 and two are
blank** — p13 and p17 wrote nothing, so both boxes are empty and gold's "did
not answer" is reproduced by the blank path rather than by any judgement. So no
counted cell requires refusing an entry or calling two entries the same. Both
cells that exercise this item's only two deductions are excluded: p4 for
`W_NOT_REASON` and p6 for the duplicate that maps to `W_ONLY_ONE`.

This is the same shape as Q4c, and on this item it is sharper, because the
guidance calls itself "the most forgiving item on the handout" and says any
statement of the right form earns its 2.5 "essentially regardless of how
insightful X is". A rate built from twelve such cells plus two blanks cannot
move when the refusal rules change, in either direction. Any work on them has
to be read on the excluded cells as diagnostics plus a corpus sweep for damage.

### The dead `not_reason` note, now with evidence

The existing item above is confirmed and can be sharpened. Q5's olx slots offer
`wrong_kind/duplicate` (`bmod_handout1.olx:1001`) and nothing else, so the
SLOT_NOTES sentence telling the grader to answer `not_reason` is unreachable —
but refusals are NOT lost: p4 comes back `wrong_kind` on both entries in 6 of 6
passes. What the dead token costs is the DISTINCTION, since a real-but-not-a-
reason-for-continuing entry and a wrong-kind entry now collapse into one token
at one price. That also means the fix is unmeasurable on the rate, per the
section above — the lint in option 2 is the part worth doing, because it is a
correctness guarantee rather than a score claim.

### p4, read from the record rather than the score

We refuse both entries (`wrong_kind` twice, 0.0 in every pass); gold deducts
2.5. Two things are worth having written down before anyone re-opens it.

* **The guidance's account of gold's row does not match the row.** The
  `W_NOT_REASON` bullet says p4's second entry — [[corpus Q5/p4 second 30:89 sha=066bb253c410]] — "cost participant 4 2.5 points". Gold's row
  reads "-2.5 pts: missing one reason why you continue to engage in lack of
  sleep", which is `W_ONLY_ONE`'s wording, not `W_NOT_REASON`'s. Both cost 2.5,
  so no score can separate them, and the guidance is describing a charge gold's
  own words do not make.
* **p4's first box is the student's text, checked.** It reads [[corpus Q5/p4 first 0:78 sha=f7407ff462b1]] — a
  missing negation that inverts the sentence. The submission itself says that
  (`doc_lines`, line 51), so this is not a transcription loss and the cell is
  not `suspect`. Our refusal and gold's credit are both defensible on those
  words, which makes this a divergence rather than a defect — the same landing
  place as Q4a/p14 and Q4c/p9, and it needs an entry if p4's citation is ever
  removed.

p4 is also the only cited Q5 cell the scorer misses, so it is the
cleanup-procedure step-1 candidate here. The same caution as Q4c applies twice
over: its example is the item's only `W_NOT_REASON` illustration, and
un-excluding it puts a cell we get wrong into a count that would go 14/14 to
14/15.

## Template residue reached the grader in 47 boxes across 13 items — FIXED

Found by item 3's fixture audit, but never an item-3 problem. Template
subtraction leaves an orphan punctuation run at the head of a response, and
where a box starts at the beginning of the response that run was served to the
grader as the student's first characters.

| item | boxes | residue |
| --- | --- | --- |
| H3/3 | 15 | `") "` — the printed question's own closing parenthesis |
| H2/PP, NR, NP, D2, PR, D1, DAY1, DAY2 | 23 | `"_ "`, `"; "` — the blank rule the student typed on |
| H1/Q3 | 5 | `"- "` (four of them one cell, p6) |
| H1/Q1, Q2, Q6 | 4 | `"_"` |

Item 3's was the clearest to read: its question ends `... so you should not
say, "Nothing will be changed"). (6 points: 3 points per example)`, the stem
strip takes the words, and the `")"` that closed the parenthetical survived
into 15 of 20 `first` boxes. Checked against the submission — the student's own
line begins [[corpus 3/p1 first 0:34 sha=c74f9db00506]], so the character was the
template's.

**Fixed at the seam, in `segment.strip_orphan_head`.** One normalisation where
a section's text is finalised, so every harness gets the same input. `(`, `"`,
`'` and `[` are deliberately NOT stripped — those open student text, and
"(Gaining something.)" is an answer — and digits are not either, because `"1)"`
is the student's own numbering, which the fixtures strip per box while the
response keeps it.

Four boxes needed a second pass, and the reason is worth keeping: a value the
paper scorer STORED never goes through segmentation.
`agreement_app._quoted_span` strips those with the same rule, which covered
item 3's `from_scorer` boxes and left exactly four — Q6/p19's `state_a1`, which
comes from the frozen consensus, and item 3's p4, p6 and p19, whose `first`
boxes this audit had itself set from residue-bearing text. All four now carry
declared corrections.

Verified box by box across the corpus: **38 boxes and 46 response texts
changed, and every single change is a pure leading strip** — the before-value
ends with the after-value in all 84 cases, so nothing anywhere else moved.
Residue boxes corpus-wide: 0.

Why no check had caught it: for a one-box item
`check_single_box_fixtures_are_verbatim` compares the box against the response
and both carried the residue, which is the blind spot its own docstring records
for mojibake — "the fixture and the response agree, because both are wrong
together". Items whose boxes are anchored to a scorer quote were immune by
accident.

**Re-measure everything on the list.** This touched 26 boxes that ARE the
response for H2's one-box items, which had never been repaired before, plus
item 3, Q1, Q2, Q3 and Q6. Nothing here was measurably costing a point, but it
changes served text in twelve items.

One row in the original survey was a false positive worth remembering: H3/1c
`p6/title` started `['Time', ' Spent a...` because it is a PARSED VALUE, not a
quotation. `_value_derived` already says so for the item, and `_quoted_span`
now joins those runs.

## Item 3: what the fixture audit left behind

Five cells repaired — p4, p6, p9, p16 and p19 — all one defect: `second` opened
with a sentence that elaborates the FIRST change, so box 2 began before change 2
did. p4's opened "I hate school!" (about change 1's extra-schoolwork
punishment); p6's [[corpus 3/p6 first 303:363 sha=c6c5c183da18]]; p9's [[corpus 3/p9 first 274:323 sha=3cd4971bdd49]]; p16's
[[corpus 3/p16 first 128:204 sha=33fcf121734d]]; p19's two sentences about
the screen-time limit it had just proposed. Each boundary moved to the sentence
that opens change 2, and the union of each pair is unchanged — asserted cell by
cell before the entries were written. Declared in
`enforcement.MULTI_BLOCK_DECLARED`.

**Re-baseline all five.** This is the item's whole risk. Item 3 records **19 of
20 counted, identical across three passes, with NO exclusions and no
declarations** — its one miss is p15, a stable over-credit of 3 against a gold
of 0, unrelated to these five cells, which all still agree with gold. (This
paragraph read "20 of 20" until 2026-08-24, written when the item was believed
perfect; `check_prose_numbers_match_the_ledger` caught it against the ledger.)
So the repair can only be checked by measuring. The reason the mis-cut cost nothing
is that `changes_given` is one count over the whole response, so a sentence in
the wrong box does not change the total; that is also why the repair is expected
to be inert. Expected, not shown. If a cell moves, revert that cell — the
entries are per-cell and independent.

### p3 earns its 6.0 from one box, and that is a real gap

p3's `second` is empty and `first` holds the entire response, because its two
changes sit inside ONE sentence — [[corpus 3/p3 first 454:581 sha=836b9bc148af]] — and nothing anchors a second box. Gold gives 6.0 and so do we, in every
pass, but the credit comes from a count made inside box 1 while the box the
rubric calls "Second specific change" is empty.

Two other cells have an empty `second` and are NOT this: p5 and p15 propose one
change or none, and gold charges them 3.0 and 0.0 respectively; p8 likewise at
3.0. p3 is the only cell where an empty box coexists with full credit.

A repair would split that sentence at ", I will also", which is a within-
sentence cut of the kind EQUIVALENCE.md warns about — Q6 lost eight cells to
exactly that. Left alone deliberately, and recorded here so the next reader does
not have to re-derive why.

### Nothing else is open

No exclusions to retest: this item has none, on any of the three grounds. No
published claim contradicted, with one qualification — `EQUIVALENCE.md:471`
cites item 3 as the case that "retention does not predict harm", keeping 64% of
the student's words and scoring 95%. On the current fixture nothing is dropped
in any of the 20 cells ("ASSIGNED TO NO BOX: nothing" everywhere), so the 64%
belongs to an older reconstruction. The lesson it illustrates still stands; the
number no longer describes this item.

## 1c: what the fixture audit left behind

One fix, in shared code rather than in a fixture table: `_quoted_span` now
handles every shape the paper scorer writes an extracted value in, so 1c's
three label boxes hold the label instead of the scorer's sentence about it.
Declared in `enforcement.MULTI_BLOCK_DECLARED`. With that, **all 26 items pass
every fixture check** and none is left undeclared.

### The readout was blind on this item — FIXED

`--fixture 1c` used to print "empty response" for 18 of 20 cells, because 1c is
answered with a chart and the readout was anchored on the prose segment. The
step QUALITY_CONTROL.md §1 calls irreplaceable therefore did nothing on exactly
the items whose boxes no other check can read, and the defect below — ten cells
of a counted item — would never have shown up in it.

Fixed, and it turned out to be two bugs reaching **237 of the 520 cells**:

* The handout was GUESSED from the item name (`1 if item.startswith("Q") else
  3`), so all twelve of handout 2's items resolved to handout 3, where they have
  no segment. **220 cells** of readable fixture that answered "empty response"
  — PR, NR, PP, NP, T1, T2, D1, D2, DAY1, DAY2, WK1, WK2, every cell of every
  one. `_handout_of` reads the spec now.
* A cell answered with a chart or a table has nothing to locate a box in, which
  is normal rather than a dead end. Those go to `_boxes_only_readout`, which
  prints each box with the spec key that filled it — `sim`, `from_scorer`,
  `fields`, `handsplit` — so it can be read against the table or the chart.
  **17 cells** of 1c.

"Empty response" now means only what it says, and prints as "empty cell — no
prose response and no filled box": 26 cells of the corpus, all genuinely blank.
Swept over all 520 cells with no errors: 477 prose readouts, 17 by provenance,
26 empty. The rule is in QUALITY_CONTROL.md §1 as well, since the question a
chart item asks of a box is a different one.

### The scorer's verdict was inside the field the grader is asked to judge

In 10 of 20 cells, `title`/`x`/`y` held the paper scorer's own prose:

    p3/x    "Weeks" appears as a bolded axis title centred beneath the day
            tick values.
    p13/y   "Hours of sleep" appears as the rotated axis title to the left of
            the numeric tick values in image1.png.
    p6/title  ['Time', ' {{corpus:1c/p6:title:5:27:sha=951281e2eda4}} Weeks'] — a typed title naming
            the student's behaviour and time span, not the default 'Chart
            Title' placeholder.
    p17/x   "Days of the Week" (axis title beneath the Sunday–Saturday tick
            values)

The olx grader's question for those slots is whether the student labelled the
axis. The old text answers it, in the scorer's words, inside the student's
field — the `cited_participants` failure arriving through the fixture instead
of the prompt. `_ANNOTATED` only matched `"…" — prose`, so a sentence, a
parenthetical or a bracketed run-list all passed through whole.

**Re-measure 1c before quoting its rate again, and expect this one to move.**
Every other repair in this audit series removed something inert; this one
removed a leak that was HELPING. 1c is 15 of 16 counted over six passes
(`out/web_v8`, `out/web_v9`, effective gold via `rebuild_gold_1c`), and those
passes were scored with the scorer's verdict in the field. Now the grader sees
`Weeks` and must decide for itself. The precedent says the effect is small —
EQUIVALENCE.md records the first `_quoted_span` change as 8/12 → 7/12, "nothing
outside noise", kept on correctness grounds — but it is the direction that
matters here, and it is the harder one.

Related annotation: that same section says of the leak "It is the only
`from_scorer` item affected — all eight were checked." It was not; 1c's twenty
boxes were affected the whole time. The check that would have caught it does
not exist, and the shapes are now enumerated in `_quoted_span`'s docstring.

### p11 is the one counted miss, and the note explaining it away is stale

`handouts.py`'s 1c comment says of p11: "The scorer reads title from the graph
(not the prose, which is empty), faults x and y exactly as gold does, and
returns 6.0. Exact match, so there is nothing here to exclude." Six passes
return **4.0** against an effective gold of 6.0. The extra deduction is
`legend: absent`, on `[[corpus 1c/p11 series 0:63 sha=bb9a6fb8ffd3]]` — the student labelled their series with day names, and gold
charged x, y and the missing baseline week without charging the legend.

The conclusion may survive (nothing here needs excluding), but the reason given
does not, and the cell is a live disagreement on a criterion the note never
mentions. The fixture is not the cause: `series` comes from `sim` and holds the
student's literal legend, which is exactly what the box is for.

### p20's labels are now seeded from its own description — SETTLED

The `unscoreable` entry reads: "a written DESCRIPTION of a graph, which on the
olx IS the answer: the labels are typed into fields and the chart is drawn from
the four complete weeks". Only the second half was happening. The four weeks
were seeded; `title`, `x` and `y` were all EMPTY, because there is no chart for
the paper scorer to read a title off, and p20's whole description belonged to no
box.

Closed by seeding the three labels from the student's own words — [[corpus 1c/p20 title 0:27 sha=d794c8f137de]], "Days (or Weeks)", "Hours of Sleep" — in
`agreement_app.CONSENSUS_FIXES`, which is what they would have typed into the
three fields. The scaffolding they wrote around them ("Title:", "X-axis label:",
"Y-axis label:", "Legend:") stays out of the boxes, like every other label in
the corpus, and `series` was already right from `sim`. All three now locate
inside the response (@7, @49, @79), the cell carries no audit flag, and the
exclusion entry says what actually happens.

The cell stays `unscoreable`: gold's 0 is for a graph that was never drawn, and
seeding the labels is what makes that failure unreachable on the olx rather
than missed, which is the entry's whole point. It is excluded, so nothing in any
rate moves.

p4 and p19 never had this problem: their entries claim only that the DATA draws
the chart, and their data is seeded with their labels empty, which is what the
fixture does.

### Confirmed, not changed

p15 and p18's empty boxes are right — gold "did not include", and p15's two
present weeks are its own partial data. p9's response is OCR'd chart furniture
(tick values and day names, duplicated), so 217 characters belong to no box and
should not; its `title` box holds the real title. p12's `series` of "Series1,
Series2" is the spreadsheet default the student left in place, which is why
gold charges the legend. p2, p10 and p11's titles are plain text and were left
untouched by the extractor, as intended.

## Q6/p1's c-boxes hold the wrong item's consequence — NOT repaired, note it against the next re-freeze

Found 2026-09-07 by subgoal Q49's fixture readout, reading all 20 Q6 cells' boxes
against the `.docx`. It is the only real mis-assignment the readout found; the
other eight boxes it flagged turned out to be the declared same-element overlap or
faithfully empty.

The student wrote two numbered items. As cut:

| box | holds |
| --- | --- |
| `state_a1` | [[corpus Q6/p1 state_a1 0:47 sha=03f77acdb76b]] |
| `change_a1` | [[corpus Q6/p1 change_a1 0:34 sha=125e26254d77]] |
| `state_c1` | [[corpus Q6/p1 state_c1 0:62 sha=547f7670047a]] — **item 2's sentence** |
| `state_c2` | EMPTY — although item 2 has exactly that sentence |
| `change_a2` | repeats `state_a2`'s sentence before adding its own |

So item 1's own consequence is welded into `change_a1`, and item 2's consequence
sits in item 1's c-box while item 2's is empty.

**Why it is not being fixed.** Q6/p1 is **perfect, 12 of 12**: the scrambled boxes
produce the right score, and gold's charge is on the FIRST consequence twice
(-1.25 state, -1.25 affect) which our engine lands. All four fixture audits pass
clean on Q6 — disjointness, coverage, agrees-with-gold, holds-the-students-words —
because coverage holds: item 1's consequence IS assigned, just to `change_a1`.
Only the assignment is arguable, and Q6's fixture is the frozen 10-run consensus
whose churn already invalidated two published comparisons. Right for the wrong
reason is worth writing down; it is not worth risking a perfect cell on the item
with nine reverted wordings behind it.

Same disposition, and the same reasoning, as project memory
BACKLOG.md (Q4a/p18).

## The enumerator defect survives in 20 boxes of three declared items

Swept after the six-item audit closed, with a pattern that catches what the
punctuation-residue survey missed: a box opening `"1) "`, `"2. "`, `"- "` or
`"Sentence 3: "` starts with an alphanumeric, so nothing above saw it.

| item | boxes | cells |
| --- | --- | --- |
| H1/Q4b | 14 | p1, p8, p10, p13, p17, p18, p19, p20 |
| H1/Q3 | 4 | p6 (all four SMART boxes, `"- "`) |
| H1/Q6 | 2 | p10 `state_a2`, p18 `state_a1` |

Same defect fixed in 2a/p16, Q4c/p13+p16 and Q5/p1+p16: the student's list
numbering served back as the opening of their answer, inconsistently, since the
other cells of each item strip theirs. All three items were declared BEFORE this
audit pass, which is how they escaped it — a declaration records that the split
was read, not that every box was normalised.

Two of them are not simple edits, and that is the point of writing them down:

* **Q6's are frozen.** Its fixture comes from the 10-run consensus in
  `out/q6_consensus`, adopted specifically so the fixture could not move and
  comparisons stayed valid (`EQUIVALENCE.md:1884`). Two boxes is not worth
  re-freezing an item whose churn already invalidated two published
  comparisons; note it against the next re-freeze instead.
* **Q4b's are hand-authored.** `handsplit/Q4b.json` is read by hand, so its
  fourteen are typed in, not extracted — the fix is in that file and touches
  more cells than any other item here.

Q3/p6 is the only cheap one, and its four bullets are the same cell the residue
survey already lists.

None of this is measurably costing a point. It is the same faithfulness argument
as the other three items: scaffolding is not the student's words, and serving
one cell's numbering and not another's makes the boxes inconsistent inputs.

## Q3/p19's boxes were misaligned by one — FIXED, and it needs measuring

Found while writing up the enumerator sweep above, in the same three items that
were declared before the audit pass. A worse defect than the enumerators, and
one cell.

p19 typed the handout's own scaffolding above their answer, and the split took
it for content:

    [measurable] "You must discuss and label each aspect of the SMART goal
                  for full credit."
    [specific]   "(How is your wanted goal behavior: Specific, Measurable,
                  Actionable/Action-Oriented, Realistic, and Time-Bound?)
                  {{corpus:Q3/p19:specific:0:78:sha=9156e5c27e31:shape=S11-0a202020202020202020202020202020202020}} ... Measureable: {{corpus:Q3/p19:measurable:13:55:sha=5201a18c372b:shape=S3-0a202020202020202020202020202020202020}} how long I sleep each night ..."

So `measurable` holds a printed INSTRUCTION, `specific` holds the printed
QUESTION plus two of the five aspects, and the student's real measurable
sentence is inside the specific box. `action`, `realistic` and `timebound` are
correct. Nothing is unassigned, which is why no check sees it: the response is
fully covered, just covered wrongly.

It matters more than the enumerators for two reasons. The grader is asked
whether the goal is measurable and shown an instruction, so a refusal there is
guaranteed and means nothing. And gold docks p19 exactly that point — "-1 pt:
For measurable, how are you tracking your goal? (ex. in a notebook)" — while the
student's own sentence says [[corpus Q3/p19 measurable 43:150 sha=6d860c05da6a]]. Whatever our scorer
returns for `measurable`, it is not returning it about the student's answer, and
if it agrees with gold it agrees for the wrong reason.

**Repaired.** `measurable` now holds the student's own "Measureable:_{{corpus:Q3/p19:measurable:13:55:sha=5201a18c372b:shape=S2-0a}} how long I sleep each night ..." and `specific`
holds only [[corpus Q3/p19 specific 0:100 sha=10eaefa02315]] Both lines of template scaffolding drop out and
belong to no box, which is correct; the other three boxes were already right,
and all five now hold their own aspect in document order with no audit flag.

**It is a counted cell, so measure it.** Two slots change what the grader sees,
and one of them is the slot gold docks. Before the repair the `measurable`
verdict was about an instruction, so whatever it was, it was not about p19's
answer — which means this cell's stored passes tell you nothing about how it
will behave now, in either direction.

The `"_"` after "Measureable:" is kept on purpose: it is the fill-in rule the
student typed over, `timebound` has the same one, and stripping it here alone
would make the cell inconsistent with itself. It goes with the corpus-wide
residue fix.

Checked while looking: p11 is NOT a second case. Its `specific` box carries
tracking prose that reads like `measurable`'s job, but both boxes hold the
student's own words, and gold gives the cell full credit.

## Q6/p18's antecedent boxes are sentence halves — DECLARED, settled

Surfaced by the marker strip, which took the "1) " off `state_a1` and left what
was underneath visible:

    [state_a1]  [[corpus Q6/p18 state_a1 0:50 sha=c9250d345b28]]
    [change_a1] [[corpus Q6/p18 change_a1 0:106 sha=e8781011c827]]
    [state_a2]  [[corpus Q6/p18 state_a2 0:60 sha=c6293ae612e6]]

`state_a1` ends on its comma and `state_a2` opens lowercase mid-sentence, so
both antecedent-naming boxes are fragments of sentences whose main clauses live
in the `change_a*` boxes.

**That is correct and declared. Do not re-cut them.** p18 names each antecedent
in a subordinate clause and puts the change in the main one, so a clause-level
split has to cut exactly there; both boxes do name their antecedent, which is
what `state_a*` is scored on; and gold's 7.5 charges only the second
consequence's fate, so nothing on the antecedent half is in dispute. Both
halves of one sentence being fragments is fine.

Where it is written down: Q6's `MULTI_BLOCK_DECLARED` entry, beside the split
it describes, and the `("Q6", 18)` note in `CONSENSUS_FIXES`. It is NOT in
`FIXTURE_STRUCTURE_OVERRIDES` — no check fires on it (the dangling-word test
reads "fatigue)," as a finished noun, correctly), and an entry there that stops
firing is reported stale.

Note for anyone tempted later: this is not the marker (stripped) and not a lost
element (nothing is unassigned). It is one sentence split at the boundary
between naming and changing, which is the boundary this item's slots ask for.

---

## DAY1/DAY2/WK1/WK2 — the NOT_OC boundary is misaligned, in both directions

Found by `measured.py --preflight`'s fixture-suspect detector and settled by
reading the three cells it named. **All three fixtures are clean** — each box
holds exactly what the student typed, whole, nothing unassigned, no flags. So
none of them is a fixture repair. They are one defect with three faces:

| cell | gold | us | direction |
|---|---|---|---|
| DAY1/p1 | 4, no comment | 0, every run | we fire NOT_OC, gold does not |
| DAY1/p13 | 0, "-4 pts: not Operant Conditioning" | 4, all slots pass | gold fires it, we do not |
| DAY2/p14 | 0, "-4 pts: not Operant Conditioning" | 4 / 2 / 2 | gold fires it, we do not |

The same criterion is firing where gold is silent and staying silent where gold
fires. Two specifics from the readout worth keeping:

* **p13 reverses cause and effect.** The removal happens AT a time of day rather
  than BECAUSE the target behaviour occurred, and the thing removed is the
  behaviour the plan exists to reduce — the goal, not a consequence of reaching
  it. Gold's zero is right, and our feedback claims the opposite in as many
  words ("linked them as contingent and occurring after the behaviour"), which
  is a misreading of the sentence's temporal structure.
* **p14 is an antecedent manipulation** — the device is made unavailable in
  advance — which TEST 2 already says is not a contingency. It also scores
  4/2/2, so it is partly a stability problem.

**What was tried, and why it did not work.** A severity rule reserving NOT_OC
(-4) for answers with no consequence at all, and directing the grader to
LINK_NOT_ASSERTED (-1) where only the if-clause is missing. Scoped to these four
items after the ledger showed the natural home, `_EXAMPLE_RULES`, would have
changed EIGHT items' prompts including three that are perfect at 18/18.

Measured, 240 calls: medians 15/14/15/16 -> 15/14/16/15, a sum of 60 either way.
WK1 gained a cell (p19, 1/3 -> 3/3, its spread collapsing to zero) and WK2 lost
one; DAY1 and DAY2 were flat with wobbles in both directions. Reverted.

The reason it could not have worked is the thing to carry forward: these items
set `derive_from_criteria`, so the score comes from the `oc_analysis` gate in
`score.derive_oc_ledger` and the deduction codes are feedback vocabulary. Prose
about which code to prefer changes what a student reads, not what they score.
DAY1/p1's feedback DID improve — it stopped telling a student with a
full-marks answer that their example is not Operant Conditioning — and the
score stayed 0, so the student is still failed, in better words.

**Where the real fix lives:** `names_behavior`, `contingent` and
`follows_behavior` in the oc_analysis gate. p1 fails all three because the
behaviour earning the reward is implicit; gold credited it because the behaviour
is the one the whole handout is about. Loosening the gate is the change that
would move the number — and it is the change that risks p13 and p14, which are
already over-credited and would be credited harder. Anyone attempting it should
measure DAY1, DAY2, WK1, WK2 together and watch p13/p14 as controls.

**A gold question, noted not acted on.** p1's own row deserves a second look:
their example removes an obligation (negative reinforcement) while they had
chosen Positive Reinforcement, and gold gave 4.0 with no comment — no
TYPE_MISMATCH charged. There is no itemisation to check it against, so it is not
CORRECTED_GOLD material under the rule that a correction needs the row's own
evidence.

### Attempt 2 on the same four items: the gate itself, and why it also failed

After the prose attempt above measured neutral, the fix moved to the layer that
actually decides the score — the five definitional gates the olx reads as slots
(`names_behavior`, `names_stimulus`, `contingent`, `follows_behavior`,
`you_arrange_it`). Target: DAY1/p13, gold 0 with "-4 pts: not Operant
Conditioning", which we credit 4/4/4 with every gate `met`, although the
sentence ends screen time {{corpus:Q6/p4:change_a1:0:15:sha=34c6623e37c8}} — nothing is arranged, so
`you_arrange_it` looked like the gate that should catch it.

Isolated exactly as `olx_prompts.SLOT_NOTES`' own comment prescribes for a
retry: ONE gate, and via an item-scoped key (`DAY1:you_arrange_it`, which beats
the bare key at the lookup) so PR/NR/PP/NP kept their text and stayed out of it.
The ledger confirmed the blast radius was DAY1 alone — 60 calls, not 240.

Result: median 15/18 -> 15/18, and the mechanism did not engage AT ALL.

    p13  run1 score 4   you_arrange_it=met  contingent=met  follows=met
         run2 score 4   you_arrange_it=met  contingent=met  follows=met
         run3 score 0   you_arrange_it=met  contingent=met  follows=unclear

`you_arrange_it` stayed `met` in every run. The single correct run came from
`follows_behavior` drifting to `unclear` — a field the note never mentions —
while p7 (previously 3/3) fell to 2/3 and p14 and p15 each rose one. Aimed at
one gate; it did not move, and three neighbours did. That is the coupling the
SLOT_NOTES comment already recorded from the 129/144 -> 128/144 attempt, now
observed a second time on a single-gate, single-item edit. Reverted.

**What this establishes.** The criteria layer IS where the score is decided —
that part of the diagnosis held. What does not work is steering a NAMED FIELD by
describing it better: the model's reading of [[corpus DAY1/p13 day1 25:71 sha=bc1027d1ef92]] as an arranged removal is stable across every phrasing tried, and
sharpening the field's description moves other fields instead. Two measured
attempts, opposite layers, same neutral result.

**The untried lever, for whoever picks this up.** Every attempt so far has
edited the DESCRIPTION of an existing gate. Nobody has added a NEW required
slot — e.g. one asking whether the consequence exists independently of the
behaviour, answered before the five gates are judged. That is the shape README's
v5 note actually recommends ("a step the model must not skip belongs in the
schema, not in prose") and the shape that fixed Q6: a required property, not
better prose about an existing one. It is a structural change to the slot list
for these items, so it needs all eight measured, and it should be attempted with
DAY1/p13 and DAY2/p14 as targets and DAY2/p12, DAY1/p2, DAY2/p3, DAY2/p5,
WK2/p12 as the named controls.

### Attempts 3 and 4, and what reading the cells actually produced

Attempt 3 added a NEW required gate (`separate_consequence`) to DAY1 — the
structural lever, not another re-description. It engaged (9 `absent` verdicts of
60) but answered `met` on the target in every pass, and the probe then dissolved
the whole result: the target cell DAY1/p13 is 3 of 6, not the stable 0/3 the
3-run baseline showed, and the apparent collateral on p11 probed 6/6. Reverted.

Attempt 4 aimed at `targets_own_behavior` for p7 on DAY2 and WK1 — the
best-evidenced target of the four: 0 of 24 pooled, the field answering `met`
every pass, gold naming the defect in both rows, our dictionary charging exactly
the 1 point gold charges, and the corrected rows making 4-1=3 an EXACT match.
A scored slot, so no cell was a 4-point bet. WK1 read 15 -> 17 with the field
flipping to `absent` on the target; the probe put it at 0 of 6 with `met` six
times, so the flip was a three-pass fluke. DAY2/p12's apparent fall probed 6/6.
Neutral, no harm, reverted.

**What the reading produced, which is worth more than the four attempts.**

* **PR and NP do not carry `targets_own_behavior` at all** — their criteria are
  `is_operant_conditioning` + `is_pr`/`is_np`, full stop. That dissolves what
  looked like a gold inconsistency: the same student p7 wrote a reading-based
  example on PR and got 4, and a reading-based example on DAY2 and was charged.
  Gold is coherent — the type items ask only for a valid example of the type,
  while the cadence items ask how the student will use it "during your
  intervention", which is why they alone require the plan to act on the
  student's own UTB/WGB. Anyone comparing a cadence cell against a type cell is
  comparing items with different criteria.
* **The guidance's counter-example does not describe a cadence cell.** "Gating
  the screen activity itself on finishing coursework earned full credit" is used
  in `_EXAMPLE_RULES` as the brake on WRONG_BEHAVIOR, and no full-credit cadence
  cell has that shape — the nearest, schoolwork rewarded with video games, scores
  ZERO in gold. It is a type-item observation applied to eight items, four of
  which score the criterion it argues against.
* **p7's disagreement is a real ambiguity, not a defect.** Their daily answer
  gates game time on reading a chapter, and games ARE their UTB, so the plan
  does regulate the UTB — via a third behaviour as the trigger. Gold reads the
  trigger; the model reads the thing regulated. Four levers failed to move it
  because both readings are defensible.

**NOT declared as a divergence, deliberately** — see the rule in
QUALITY_CONTROL.md section 5. The cells stay counted and wrong, and the next
person gets the readings above plus four numbers instead of a closed question.
The untried alternative nobody has checked: whether the CADENCE items' question
text should say the example must act on the student's own behaviour, since that
requirement is currently only in the grader's criteria and never in what the
student is asked.

### p8's four cadence cells, read out in full — and a backwards contingency we credit

Prompted by the observation that three declared divergences on ONE student looks
suspicious. It was, though not in the direction expected.

**The fixture is faithful.** All four boxes were checked against
`Participant ID 008 - Handout 2.docx` line by line (source lines 44, 50, 66, 73
-> day1, wk1, day2, wk2). The text matches exactly, the boxes are in the right
order, and only trailing template underscores are stripped. No fixture
correction is warranted, which is worth recording because the readout was
undertaken expressly to look for one.

p8's first chosen type is PP, their second NR (gold's own comments say so).

| cell | gold | us | who is right |
|---|---|---|---|
| DAY1 | 0 | 4 | us — the aversive gold asks for is in the sentence |
| WK1 | 0 | 4 | us — same, and stated directly rather than by avoidance |
| DAY2 | 4 | 0 | **gold** — cadence misjudged, see below |
| WK2 | 0 | 2/2/4 | **gold** — the contingency runs backwards |

**WK2 is a real over-credit and is no longer declared.** [[corpus WK2/p8 wk2 0:85 sha=7c5a9ef6a6ad]] puts the chore
AFTER SUCCESS: meeting the goal earns yard work. Their daily answer for the same
type is the correct inverse, which is what makes this a slip rather than a
style. We score 2 or 4 because `matches_chosen_type` goes absent in some runs and
nothing catches the reversal at all.

**The criterion gap:** no check asks whether the consequence's VALENCE matches
its position — an aversive delivered for success, or a reward delivered for
failure, is not the type named however well-formed the contingency is. TEST 3
asks which of the four types it is, and the model answers by looking at what is
added or removed rather than at which side of the contingency it sits on. Worth
attempting on `observed_type` rather than on a new gate, and worth measuring on
all four cadence items with the correctly-inverted daily answer as the control.

**DAY2 is our clearest live defect on these items.** Gold 4, we score 0 in every
run, and the cause is `cadence_is_daily` answering `absent` because the reward
lasts to the end of the week — while that gate's own rule in the served prompt
says "Judge how often the BEHAVIOUR IS CHECKED, not how long the consequence
lasts — a daily trigger whose reward runs to the end of the week is still
daily". The rule is present, precise, and ignored. Pooled 1 of 12.

### WK2's direction gap is closed, and p8's residual is severity not reading

The gap was real and locatable: the TYPE items have always asked whether the
arrangement is pointed the right way (`targets_intended_behavior`, charging
WRONG_TYPE), while the cadence items only ask whose behaviour it is
(`targets_own_behavior`). So nothing on WK2 asked which side of the contingency
the consequence sits on.

`aimed_correctly` now does, gating on WK2 on both paths — the OLX slot, the
rubric guidance both generators render, `score.derive_oc_ledger`, and the probe
table's pass/fail pair, which the enforcement suite demanded the moment the
schema field appeared.

Measured: median 16/18 -> 16/18, no cell moved. It fires `absent` or `unclear`
on exactly three cells — p10, p13, p18 — and ALL THREE are gold 0, so where it
speaks it agrees with gold three times out of three. Kept on that basis: a
correct criterion with no measured harm, closing an asymmetry between items that
ask the same question of the same kind of answer.

**Why it does not fix the cell that exposed it, which is the interesting part.**
p8's answer adds a chore after SUCCESS. The model reads that exactly right — its
feedback says "adds a task after success (an added stimulus), so if you meant
Negative Reinforcement you should instead remove an unpleasant obligation" — and
charges it under `matches_chosen_type` as a type mismatch, -2, giving 2. It
answers `aimed_correctly: met` because the fault is already accounted for.

That reading is arguably better than gold's. Adding an aversive after success IS
an operant arrangement — positive punishment of the goal behaviour — so it is
self-defeating and mistyped, but not "not operant conditioning". Gold charges the
whole 4; we charge 2. The disagreement is SEVERITY, and closing it would mean
telling the grader something false.

So for WK2/p8 the alternatives are now exhausted in the order section 5 asks:
the fixture was verified faithful against the source .docx, gold's row carries a
reasoned comment rather than an itemisation to check, the missing criterion has
been added and measured, and our reading has been confirmed the sounder one. It
stays COUNTED AND WRONG rather than declared — the cost is one cell, and what is
recorded here is worth more than a line saying we disagree.

### WK1/p8, attempt 6: the punisher-made-of-the-goal-behaviour reading, refuted

The most promising hypothesis yet about gold's zero on WK1/p8, and it is wrong.

The reading: p8's unwanted behaviour is a lack of exercise, their goal is to work
out four days a week, and the penalty they set for {{corpus:Q4c/p8:first:19:39:sha=d9e32b32668d}} is extra
press-ups — which is exercise. So the punisher is made of the goal behaviour and
is not aversive TO THEM, which is exactly what gold's comment asks for ("state
what UNDESIRABLE thing will you add"). It also explained why the same plan earns
4 on the TYPE item: that item asks only for a valid example of PP, where
press-ups as an aversive is fine in the abstract, while the cadence items ask how
it will be used in this intervention. Same asymmetry as `targets_own_behavior`.

Implemented as `consequence_distinct_from_goal`, gating on WK1 on both paths.
Measured: median 15/18 -> 15/18, and the gate answered `met` on the target in
every run. It never fired where it was aimed. It DID fire 15 times elsewhere and
broke p1, a previously correct cell, twice — the 4-point bet a gate makes of
every cell, realised as a loss. Reverted.

Why the reading fails, which is worth keeping: the model does not accept that
press-ups ARE the goal behaviour, and that is defensible. The goal is gym
attendance four days a week; extra press-ups imposed as a penalty is a distinct
imposition, and a common one. Reading it as "more of the goal behaviour" was an
inference the text does not compel.

So gold's "undesirable thing" objection remains UNEXPLAINED rather than explained,
and WK1/p8 stays declared as ADDED_AVERSIVE_NAMED. Six attempts now stand behind
that entry: deduction severity, `you_arrange_it`, a new separateness gate,
`targets_own_behavior`, cadence-by-accumulation, and this. The fixture was
verified faithful against the source .docx, gold's row carries a reasoned comment
rather than an itemisation to check, and two of the six attempts produced
criteria worth keeping on OTHER items.

**And then the comment turned out not to be evidence.** The sentence "you should
state what undesirable thing will you add..." appears NOWHERE else in handout 2 —
only on p8's three cells, with the type and cadence slotted in. On the third,
WK2, it reads "For NR, you should state what undesirable thing will you take away
at the end of the week IF YOU DO NOT MEET your weekly goal", which is wrong for
NR: negative reinforcement removes an aversive when the behaviour OCCURS, and
removing one for failing rewards failure. The clause was carried over from the two
PP versions unadjusted.

So the operative judgement is the FIRST sentence, "This is not an example of
operant conditioning", and the second is per-student boilerplate written once and
pasted. Its words cannot be mined for a criterion — which retires the
"undesirable thing" reading on evidence rather than on a failed measurement.

**What does account for the three zeros**: p8 never states a fresh, complete,
correctly-oriented contingency in any of these boxes, but keeps adjusting the one
plan established in their earlier type items. Each fails a different half —
DAY1's consequence lives only in an avoidance clause under an intention (fixed,
the avoidance gate, 9 of 9); WK2's is attached to success instead of failure
(charged as a type mismatch); and WK1's is named, oriented and stated directly,
so nothing is wrong with it.

**The distinguishing feature, for anyone tempted by a new rule**: every cell that
must stay correct names BOTH SIDES in one canonical conditional — [[corpus PR/p2 pr 0:48 sha=6c9624661ff5]] / [[corpus PR/p3 pr 0:48 sha=6c9624661ff5]]. TEST 1 and the two gates added on
2026-08-24 already enforce that. The rule tried here reached past it for a defect
WK1 does not have, which is why it broke p1.

That leaves the likeliest account of WK1's zero as a VERDICT CARRIED ACROSS a run
of three cells for one student — a claim about gold's process, not about the
answer. Which is what a divergence is for, and what no rule should chase.

### WK1/p8 IS reachable: the consequence needs someone to deliver it

Recorded after a false negative of my own making. I first concluded no gate could
match gold here, on the grounds that WK1/p5 scores 4 while stating "no
contingency at all" — and that was an artifact of reading only the FIRST LINE of
each response. p5 has two sentences, and the second is a textbook weekly NR
contingency: [[corpus WK1/p5 wk1 61:164 sha=6473c5fa76bc]] p5 is correctly scored by everyone, and
proves nothing about gates.

Read in full, WK1's countable cells separate perfectly on one feature — whether
the answer names SOMEONE WHO DELIVERS the consequence:

    gold 4   p1  [[corpus WK1/p1 wk1 48:87 sha=9acb583a85f7]]
             p4  [[corpus WK1/p4 wk1 56:91 sha=50343f5b996f]]
             p5  [[corpus WK1/p5 wk1 108:145 sha=9b3b1f7b12b6]]
             p9  [[corpus WK1/p9 wk1 46:83 sha=441a5dbfab7f]]
             p11 [[corpus WK1/p11 wk1 43:78 sha=d8be473a6345]]
             p12 [[corpus WK1/p12 wk1 51:91 sha=b0273f13aefa]]
             p14 [[corpus WK1/p14 wk1 86:137 sha=112a104d8d8c]]

    gold 0   p6  "{{corpus:WK1/p6:wk1:0:50:sha=465f4decda26}} pops..."
                 — a substitution; nobody delivers anything
             p8  [[corpus WK1/p8 wk1 106:145 sha=18320b482a21]]
                 — no agent; the tally grows by itself
             p13 [[corpus WK1/p13 wk1 0:51 sha=848ae9e56f72]]
                 — a plan; nothing is delivered contingently

Seven of seven credited, three of three zeroed. The rule is not grammatical
pedantry: it is TEST 2's "judge the DELIVERY, not the wording" turned into a
positive requirement, and it says an accumulating tally is not a delivered
consequence any more than a substitution or a plan is.

The lesson about method, which is the more expensive one: a one-line extraction
of a multi-line response produced a confident argument that gold was
unreproducible, and I committed to it in conversation before checking. The
fixture readout prints every line for a reason. `sed -n '7p'` is not reading a
response.

Measured, and it failed for a reason worth knowing: **the gate never answered a
confident `absent` on any cell.** It answered `unclear`, and a gating slot
treats anything other than satisfied as a failure, so `unclear` zeroes the item.

    p8   gold 0, was 0/3   ->  2/3   verdicts met, unclear, unclear
    p11  gold 4, was 3/3   ->  1/3   verdicts unclear, unclear, met

Both cells came back uncertain twice out of three, and the median rose only
because p8's coin landed better than p11's. The model cannot reliably separate
[[corpus WK1/p8 wk1 106:145 sha=18320b482a21]] (no agent) from [[corpus WK1/p11 wk1 43:78 sha=d8be473a6345]] (an agent, but modal and passive-ish), which is the distinction the
paper reading rests on. Reverted.

**The design trap, which generalises past this item.** Writing a slot as
`!key:Label:unclear` makes `unclear` GATE — the third field lists the extra
verdict, and the engine satisfies only the first. So a gate fires on the model's
UNCERTAINTY as well as on its judgement, and a criterion the model finds hard to
call becomes a 4-point coin flip on every cell. That is the opposite of what a
gate is for: gates belong on judgements the model makes crisply. Before gating a
new slot, check the verdict DISTRIBUTION on a sweep — if `unclear` appears at
all, the slot is not gate material. WK2's `aimed_correctly` has the same
exposure; it answered `unclear` on three cells, all of them gold 0, so it costs
nothing there today, but the same coin is in it.

**Where this left WK1/p8 after seven attempts, and why that conclusion was
wrong.** The separation on paper was real, and I closed the entry saying the rule
was "identifiable but not operationalisable at this model's precision". It was
operationalisable. I had been asking for it in the wrong currency — see the
SOLVED section at the end of this entry.

**Attempt 8: the same gate, binary.** The `unclear` verdict was mine to remove —
`DEFAULT_VERDICTS` is `['met','absent']`, and writing `!key:Label:unclear` ADDS
the hedge; omitting the third field gives a two-valued gate, which is how
`cadence_is_weekly` is written and one reason it behaves. Re-run that way:

    verdict distribution   met 52, absent 8, unclear 0
    p8   gold 0, was 0/3  ->  1/3   absent, met, met
    p11  gold 4, was 3/3  ->  2/3   met, met, absent

So the hedge was real and removable, and removing it did not make the judgement
correct: the model calls p8 delivered twice in three and p11 undelivered once in
three. Median 15 -> 15, p8 +1, p11 -1. A two-sided coin instead of a three-sided
one. No collateral beyond p11. Reverted.

Two things worth keeping from it. **Binary is the right shape for a gate** —
offer no hedge on a judgement that zeroes an item, and check the distribution of
an existing gate before trusting it (WK2's `aimed_correctly` still offers
`unclear`, and should be made binary the next time that item is measured). And
**the hedge was only half the fault**: a well-formed gate still wobbled, which is
what pointed at the real problem — the QUESTION, not the verdict set.

### SOLVED, attempt 9: ask for a parse, not a judgement

WK1 rose from 15 to **17 counted cells** at that point, and the divergence is retired. It reached **18/18** later the same day — see the trigger-classification entry at the end of this file.

Every version up to attempt 8 asked a question about the PLAN — "is a consequence
delivered?" — and the model wobbled on the only two cells that separate. The cue
I had actually found by reading the texts was SYNTACTIC, and a parse is something
the model does crisply. So the slot asks two mechanical things about the clause
that states the consequence:

  (a) its SUBJECT — is a person there, as the subject of an active verb or the
      agent of a `by`-passive?
  (b) its VERB — does it say that person brings the thing about or takes it away,
      read broadly enough to include granting oneself a privilege ([[corpus WK1/p1 wk1 55:77 sha=4c2bef145233]], "skip one chore")?

and answers `absent` when the subject is the CONSEQUENCE ITSELF with a verb of
accumulation ("the press-ups will just keep stacking"), when there is no finite
clause, or when the answer is off the point entirely.

    sweep   15/15/16 -> 17/17/16, seventeen of eighteen cells at 3/3
    probe   p8 absent 6/6, scoring 0 against gold 0
            p1 met 6/6 — the boundary case the first verb list broke, at 3/6
            controls p4 and p11 6/6

**The verb list is where the first version went wrong, and it is a general
warning.** Written as a list of transfer verbs, it excluded [[corpus WK1/p1 wk1 48:87 sha=9acb583a85f7]] — a student granting themselves a privilege — and put a
correct cell at 3/6. I had noticed that case on paper, marked it "marginal", and
waved it through. Widening the test from "is the verb on this list" to "does a
person make the thing happen or stop happening" fixed it at 6/6. A closed list
in a rule is a boundary you are promising to defend; prefer the criterion the
list was trying to approximate.

### p7 on WK1 and DAY2: where "ask for a parse" stops working

The parse framing that solved WK1/p8 was applied to the other open cell on these
items, and failed on both. The failure is informative, so it is recorded rather
than merely reverted.

**The cells.** p7's UTB is screen time. Their weekly answer triggers on
procrastinating and withholds their games; their daily answer triggers on reading
a chapter and grants their games. Both times the UTB is in the sentence — as the
PRIZE — and `targets_own_behavior` answers `met` on seeing it, so the 1-point
WRONG_BEHAVIOR gold charges never fires. With both rows corrected to 3.00, a
firing deduction would land exactly on gold rather than merely closer.

**What was tried.** The criterion rewritten as a procedure: locate the clause
saying what must happen for the consequence to arrive, quote its verb phrase,
compare THAT PHRASE and nothing else against the UTB and WGB in context, and
answer `no` when it names neither. Scoped to WK1 and DAY2, in the credit
component's `rule` so both generators render it.

    WK1   p7 fired once in three — 4, 4, 3, and the 3 is exactly gold — while
          p19 took a spurious `absent` and lost a run. Median unchanged at 17.
    DAY2  p7 never fired at all: `met` in every run, 4, 4, 4.

**Why it does not transfer, which is the finding.** `agent_delivers_consequence`
is a PURE parse: find a clause, look at its subject, classify its verb. Nothing
in it requires knowing what the answer is about. `targets_own_behavior` only
BEGINS with a parse; its decisive step is comparing the quoted trigger against
the student's stated UTB and WGB, which is a semantic comparison. The framing
sharpened the locating half and left the wobble in the comparing half. So: ask
for a parse where the whole test is syntactic. A criterion whose core is a
comparison is not rescued by telling the grader which clause to compare.

### The coupling tax: an edit moves gates it never mentions

Fourth observation of this today, and the first where it cost a COMMITTED gain.

Adding the p7 rule to DAY2 — text about which behaviour a trigger names, saying
nothing whatever about cadence — flipped `cadence_is_daily` on DAY2/p8 from `met`
in two runs of three (5 of 6 on its probe) to `absent` in all three:

    DAY2/p8   after the cadence fix   4/met, 0/abs, 4/met
              with the p7 rule added  0/abs, 0/abs, 0/abs

`olx_prompts.SLOT_NOTES` already recorded this for the five definitional gates —
"these five definitional gates are coupled, emphasis on any one shifts the
others" — and today it has been seen on `you_arrange_it`, on `separate_consequence`
firing where it was not aimed, on `targets_own_behavior` disturbing p12, and now
on `cadence_is_daily`, which the edit does not mention at all.

The practical consequences, both cheap:

* **A committed gain is not safe from a later unrelated edit on the same item.**
  Re-measure the WHOLE item after any change to it, never just the target cell —
  which is what caught this, since the sweep covers all 18.
* **When an edit measures neutral, check whether it is neutral or COMPENSATING.**
  DAY2's median was unchanged at 15 here, and underneath it p9 gained two runs
  while p8 lost three. A flat median can hide a gain and a regression of similar
  size, and only the per-cell table shows it.

### p7, attempt 10: the criterion as a CLASSIFICATION, and a blind spot in the artifacts

`targets_own_behavior` was restructured to work the way `matches_chosen_type`
already works on these items: the model emits a classification and the engine
derives the verdict, rather than judging the slot directly.

    choices="trigger_target:utb,wgb,other"
    slots=...|trigger_behavior:Which behaviour must happen, or fail to happen,
              for the consequence to arrive:pick(trigger_target)|...
    expect="targets_own_behavior:trigger_behavior=utb:wgb"

Mirrored on the python as an enum property with the same derivation, so the paths
stay in step; the enforcement suite confirmed no divergence. Deliberately short
on prose, since the previous attempt's ~1000 characters were what knocked a
committed cadence gain off DAY2/p8.

**It failed on both items and cost DAY2 two cells.**

    WK1   p7 unmoved at 0/3 (4, 4, 4); median 17, unchanged from recorded;
          p6 3/3 -> 2/3
    DAY2  p7 unmoved at 0/3; median 14 against a RECORDED 15, with p12 3/3 -> 1/3
          and p13 3/3 -> 1/3

The regression-against-recorded check added an hour earlier named p12 and p13 by
itself. Without it the median moving 15 -> 14 would have looked like ordinary
noise rather than two committed cells being handed back.

**The blind spot, which matters more than the result.** `trigger_behavior` reads
EMPTY in every cell of every run — exactly as `observed_type` and `named_type`
do — because a pick answers in `refers_to` and `agreement.py` stores only
verdicts in the artifact. So it cannot be determined whether the model classified
`other` and the expect rule failed to apply, or classified `utb` and the rule
worked exactly as designed. The experiment is negative on the SCORE and
undiagnosable on the MECHANISM.

Anyone retrying this must first make the harness persist `refers_to` alongside
`verdict`. Three experiments on pick-valued slots are uninterpretable until it
does, and the same blind spot has been sitting under `observed_type` all along.

**A real reason WK1/p7 may be unfixable, found while reading its context.** p7's
UTB response is [[corpus Q1/p7 response 17:128 sha=f09523e1e6f4]] The grader is
handed that whole paragraph as `_utb`. So when the weekly answer triggers on [[corpus WK1/p7 wk1 0:43 sha=6dcf7407edcc]], a rule asking whether the trigger
names the student's UTB can answer `utb` on good evidence — the word is in the
text it compares against. Gold's "your UTB is not procrastination" is true of the
CHOSEN BEHAVIOUR and false of the paragraph we supply. That is a context
question, not a criterion one: it would be settled by passing the grader the
chosen behaviour rather than the whole Q1 response, which is a fixture change
with its own blast radius across every item that reads `_utb`.

### The blind spot fixed, and what it then showed about p7

`agreement.py` now stores `answers` and `evidence` beside the verdicts in every
run artifact. Both were computed at run time and thrown away at write time: a
pick answers `refers_to` and carries no verdict, so it stored as `""`, and
`apply_computed` writes the operands of every `equals` and `expect` rule into
`evidence` ("trigger_behavior=other, wanted utb") — the only record of what a
derived check was derived FROM. `answer_of()` already existed to read the first;
nothing needed inventing. This retroactively un-blinds `observed_type` and
`named_type`, which have read `""` in every artifact ever written.

With it, the classification experiment became readable, and it had never failed:

    p7   trigger_behavior = 'utb'   quote: [[corpus WK1/p7 wk1 11:43 sha=ea8a643dda0e]]
    p12  trigger_behavior = 'wgb'   quote: [[corpus WK1/p12 wk1 5:37 sha=121d9d3fe5b0]]

The model located each trigger exactly, quoted it, and the expect rule computed
correctly. It classified procrastination as p7's UTB because THEIR OWN UTB
PARAGRAPH SAYS SO — [[corpus Q1/p7 response 17:90 sha=64e183613be0]] — and `_utb` hands the grader that whole
paragraph. Not a criterion failure and not a plumbing failure: a context one.

**DAY2/p7 is not a `targets_own_behavior` failure at all, and this is the finding
to keep.** Its trigger is "having {{corpus:DAY2/p7:day2:10:28:sha=d9dd77c5e534}} read", and p7's stated goal
is [[corpus Q2/p7 response 88:159 sha=e2f81bb708fb]]. So
the trigger IS their wanted goal behaviour; the model classifies `wgb` 6 of 6 and
is RIGHT. Gold's "-1 pt: make sure the behavior you are targeting is spending
less time on electronic devices" asks them to target the UTB, while the item's
own question says the opposite for reinforcement — "the student should be trying
to increase their wanted goal behaviour". The real defect in that answer is that
it rewards with the UNWANTED behaviour (games), which is a different criterion
and not the one gold's comment names. Any future attempt should target THAT, and
should not touch `targets_own_behavior`.

**WK1/p7 is reachable, but only by trading p19 for it.** Two instructions are
each independently correct and cannot both be held:

    narrow reading only            p7 5/6 `other`   p19 3/6 (over-corrected)
    + "a reference counts as naming"  p7 2/6 `utb`   p19 6/6 `wgb`

p19's trigger is [[corpus WK1/p19 wk1 0:38 sha=5e7c12c5248e]], a pure reference, so
the reference rule is needed for it; p7's is "{{corpus:WK1/p7:wk1:12:43:sha=5e1f6a6d53e1}}",
which the narrow rule is needed to exclude. Adding the second — "answer `other`
ONLY when the trigger names a different activity outright" — made the model
reluctant to answer `other` at all, and p7 swung back to the reading its UTB
paragraph invites. Reverted; the criterion sits at the edge of what this model
holds at once.

### WK1 to 18/18: the trigger classification, and why "one rule at a time" was wrong

WK1/p7 is fixed and WK1 is the first perfect LLM-scored item in handout 2.
`targets_own_behavior` is now DERIVED on that item, the way `matches_chosen_type`
always has been: the model classifies which behaviour the trigger names and the
engine compares.

    choices="trigger_target:utb,wgb,other"
    slots=...|trigger_behavior:Which behaviour must happen, or fail to happen,
              for the consequence to arrive:pick(trigger_target)|...
    expect="targets_own_behavior:trigger_behavior=utb:wgb"

Mirrored on the python as an enum with the same derivation and the same wording, so
both generators put the same question.

**The rule that works, after three drafts.** Classify by WHAT KIND OF PHRASE the
trigger is:

  * a POINTER — "my goal", "my daily goal", "my plan" — has no content of its
    own, so classify it as whatever it points at;
  * a NAMED ACTIVITY — "procrastinating", "reading a chapter" — has content, so
    judge it against the behaviour the student CHOSE. Their paragraph also says
    WHY they chose it, and the causes and knock-on habits it names are not the
    chosen behaviour.

**"The model can only hold one rule at a time" was wrong, and worth correcting
in the open.** Draft A (narrow reading only) fixed p7 at 5/6 and over-corrected
p19 to 3/6. Draft B added the pointer rule and inverted it — p19 6/6, p7 2/6 —
and the conclusion drawn was that the two could not coexist. They can. Draft B
had said to answer `other` "ONLY when the trigger names a different activity
outright, one that is NOT POINTING AT EITHER", which contradicted draft A's own
worked example, where an activity named in the UTB paragraph IS `other`. The
model followed the more absolute clause, which is the correct thing to do with
contradictory instructions. Splitting by kind of phrase, with no `only` anywhere,
holds both: p7 5/6 `other`, p19 6/6 `wgb`, controls 6/6.

    sweep   runs 15, 15, 16 -> 17, 18, 18. Median 15 -> 18. The one cell not at
            3/3 is p7 itself, at 2/3, consistent with its 5/6 probe.

The failure mode to remember is not a capacity limit: it is AN ABSOLUTE QUALIFIER
IN A LATER CLAUSE SILENTLY REPEALING AN EARLIER CARVE-OUT. From outside it looks
exactly like a model that cannot hold two rules.

**NOT extended to DAY2, on measurement.** DAY2's p7 classifies `wgb` 6 of 6 and
is RIGHT to: its trigger is "having {{corpus:DAY2/p7:day2:10:28:sha=d9dd77c5e534}} read" and the student's
stated goal is [[corpus Q2/p7 response 88:159 sha=e2f81bb708fb]]. So the criterion has nothing to fix there, and the sweep priced what it
would cost anyway — median 15 (recorded) -> 14, with p9, p12 and p13 all handed
back, each named by the regression-against-recorded check. The slot was removed
from DAY2 and the OLX restored from HEAD so that item is byte-identical to what
it recorded.

DAY2/p7's real defect is that the answer rewards with the UNWANTED behaviour,
which no criterion covers and which gold's comment does not name. Gold asks them
to target the UTB while the item's own question asks reinforcement examples to
target the GOAL behaviour, so that cell is a gold question, not a criterion one.

### DAY2/p14: the note was aimed at the wrong cell (CORRECTED)

`you_arrange_it` was given an item-scoped note on DAY2 stating the
automatic-result test as a question about WHO ACTS — the framing that worked for
the agent parse and the trigger classification. It did not fire. The slot read
`met` in all three runs and the cell scored 2, 4, 4 against a gold of 0. Median
matched the recorded 15, and one coupling regression appeared on p8. Reverted.

**CORRECTION, same day.** The paragraphs below identified DAY2/p14 as [[corpus DAY2/p16 day2 0:54 sha=d4b2d634e70d]]. That is DAY2/p16. DAY2/p14 reads
[[corpus DAY2/p14 day2 0:130 sha=9e1912b9c1a4]] — the antecedent-
manipulation case, not an automatic-result one. The cell id was carried from
memory instead of re-read, so the note was aimed at a cell whose defect it does
not describe, which is why it never fired. The rule-collision analysis below is
sound as a reading of DAY2/p16 and says nothing about p14.

The cell sits on a CONTRADICTION INSIDE THE RUBRIC, and no sharper note can
resolve it:

  * `WHAT COUNTS AS THE ADDED OR REMOVED THING — BE BROAD` credits a consequence
    that SPARES the student something — "the graders gave full credit wherever
    meeting the goal SPARED the student something they would otherwise have had
    to do".
  * `NOT_EXTERNAL_STIMULUS` zeroes a consequence that is "simply the behaviour's
    own automatic result", canonical zero [[corpus PR/p1 pr 0:47 sha=543798ac2cea]].

Walking to avoid weight gain satisfies BOTH descriptions. Gold applies the
second; the model applies the first, which the rubric states just as plainly.
Resolving it means narrowing one of the two rules, and both live in
`_EXAMPLE_RULES`, shared by all eight items that use these gates — four of which
are perfect today. That is a much larger and riskier change than the cell is
worth, and it should not be attempted without measuring all eight.

**Where the four cadence items stood after that day's work**: 65 of 72, up five
cells on the morning's baseline. SUPERSEDED TWICE, so the figures are deliberately
not repeated here — `measured.py --status` holds the current ones, and quoting
them in prose is what this file keeps getting wrong. First the de-specification
pass showed WK1's perfect score rested partly on prose describing p7 (see the
leakage section of QUALITY_CONTROL.md); then the derived direction gate moved two
of the four again. The residue is 23 wrong
cell-runs of 216, and the slot breakdown says two thirds of them are
OVER-CREDITS, of which the largest group is cells where every check passes and
gold still says zero. `observed_type` answering `none` predicts a correct zero
perfectly; the over-credited cells all have it naming a quadrant instead, and
each does so for a different upstream reason — a consequence made of the target
behaviour, a backwards contingency, and this rule collision. They do not share a
criterion, which is why five separate attempts at a single new gate found
nothing.

## Owed when the 2026-09-13 sweep finishes — two items, both deferred because
## editing them mid-sweep could invalidate the run silently

Found 2026-09-13 while mutation-testing the lo-blocks changes. Seven of eight
mutations were caught; these two are what the eighth exposed. Both touch files a
running sweep depends on, so neither was done at the time.

**1. The grader's call site is untested, and it is the defect that actually
happened.** `SlotSheetGrader.gradeSlotSheet` forwards eleven arguments to
`scoreSlotSheet`, and `maps` -- the eleventh -- was once not passed at all: the
scorer defaulted it to `[]`, no mapped check was ever computed, and every cell
scored flat. Deleting `payload.maps` from that call TODAY still passes the whole
suite. `sheetRoundTrip.test.ts` exercises `sheetFromJson` (the hand-copied
payload, which is how `expect` was lost) and then calls `scoreSlotSheet` ITSELF,
so the grader's own argument list is never exercised.

*Fix:* export `gradeSlotSheet` and assert it forwards every rule -- score a sheet
whose result DEPENDS on each rule family in turn, so dropping any argument moves
a number. A rendering test would also work and is slower.

*Why deferred:* `SlotSheetGrader.ts` lives under `components/`, which
`server_code_is_stale` does not glob (item 2), so editing it mid-sweep makes the
tree diverge from the running server with NOTHING to report it.

**2. `server_code_is_stale` has a blind spot: `components/blocks/**`.** It globs
`packages/shared/lib/llm/*.ts` and `apps/server/src/**/*.ts` only. That omits
`components/blocks/action/LLMAction.ts` (builds the request) and
`components/blocks/grading/SlotSheetGrader.ts` (scores it) -- both squarely "code
that decides a score". On 2026-09-13 all of them happened to predate the server
start, so the sweep was honest; a mid-sweep edit to either would have been
invisible. Widen the glob, then re-check that no item is stale.

**Recreating the mutation harness** (removed because its 17 copied test files
polluted the default run, 105 -> 122):

    cp -r packages/shared/lib/llm packages/shared/lib/llm_mut
    rm -f packages/shared/lib/llm_mut/{runner,promptcapture}.test.ts
    # vitest.mut.config.ts: spread ./vitest.config, then resolve.alias
    #   '@/lib/llm/slotSheet' -> packages/shared/lib/llm_mut/slotSheet.ts
    #   '@/components/blocks/grading/SlotSheetGrader' -> a copy of it
    #   '@' -> packages/shared
    npx vitest run --config vitest.mut.config.ts packages/shared/lib/llm_mut/

Mutate the COPY, never live source: restoring a file byte-identically still moves
its mtime, which is exactly what `server_code_is_stale` compares -- doing that on
2026-09-13 made the guard cry stale for about a minute while a sweep was running.

## `legendRender.test.ts` gets as far as "Loading…" — 2026-09-13

OUR test, for OUR component (`SelfMonitorPlot`, added in `dc23a594`). It is
`skipIf(!IDMAP)`, so it has never run in CI and rotted unnoticed — a skipped test
cannot tell you it has stopped working.

**Three real defects found and fixed** while trying to exercise it:

1. the content namespace was renamed `psych` -> `edu.memphis.psych`; the test kept
   the old one, so `RenderOLX` matched nothing
2. `initConfig()` was never called, so rendering threw "Config not initialized"
3. the idMap was dispatched into the store but never passed to `RenderOLX` as
   `baseIdMap`, so it reported "No content source provided"

**Still blocked.** With all three fixed it renders
`Loading edu.memphis.psych/bmod_h3_graph...` and stays there past a 3s wait, so
both cases see 0 figures where they expect 2.

**Ruled out, each measured rather than assumed:**

- *jsdom cannot render plots* — FALSE. A real `Plot.plot()` call renders an `<svg>`
  under jsdom. (Note it returns a bare `<svg>`, not a `<figure>`; Plot only wraps
  in `<figure>` when there is a legend or caption, which may matter for the
  assertion once the screen renders.)
- *the idmap is stale* — no: identical failure on v143, v144 and v145.
- *the LOAD_OLXJSON dispatch shape is stale* — no: `runner.test.ts` uses the same
  shape and renders these very screens on every sweep.
- *a missing locale* — the content IS locale-keyed (`{'en-Latn-US': block}`), but
  dispatching SET_LOCALE did not change the symptom. That dispatch was removed
  rather than left in as an unproven fix.

**Further eliminated 2026-09-13, second pass:**

- *the ids are wrong* — no. `agreement_app.build_jobs('1c')` returns exactly
  `ns='edu.memphis.psych'`, `screen='edu.memphis.psych/bmod_h3_graph'`, the same
  pair this test now uses, and the sweep renders it every run.
- *it needs longer* — no. Polling for a `<figure>` every 250ms for 15 SECONDS
  leaves it on "Loading ...". The gate either resolves at once or never.
- *an import side-effect* — no. The only import `runner.test.ts` has and this does
  not is `@/lib/llm/reduxClient`; adding it changes nothing.
- *the store dispatch reaches RenderOLX* — NO, and this is the sharp end. Without
  `baseIdMap` the render says "No content source provided" even though
  LOAD_OLXJSON was dispatched exactly as `runner.test.ts` dispatches it. With
  `baseIdMap` it gets to "Loading" and stops.

**APPROVED 2026-09-13, to be done WHEN THE SWEEP FINISHES:** instrument
`useRenderedBlock`'s `depsReady` (and `olxResult.loading` beside it) to find which
of the two is holding the spinner. Deferred only because it edits
`lib/player/client/useRenderedBlock.tsx` -- live render code the dev server has
loaded -- and a mid-sweep edit would leave the tree diverged from the process
being measured. Note `components/` and `lib/player/` are BOTH outside
`server_code_is_stale`'s glob (see the guard item above), so nothing would warn.

**The one suspect left** is `useRenderedBlock`: the spinner is returned when
`olxResult.loading || !depsReady`, where `depsReady` comes from
`useBlocksReadyForSources([source], blockRegistry)` -- lazy block-chunk readiness.
1c's screen carries `SelfMonitorPlot`/`ObservablePlot`, the heaviest chunks in the
content. Instrument those two booleans and the answer falls out; that needs an
edit to `lib/player/client/useRenderedBlock.tsx`, which is why it stopped here
while a sweep was running.

**Worth keeping in mind for when it renders:** the assertion counts `<figure>`
elements, but Plot returns a bare `<svg>` unless there is a legend or caption. If
the screen renders and the count is still 0, that is the next thing to check, not
a second bug.

## Every artifact glob was one level deep, and the audit could not see a sweep's own output — FIXED 2026-09-15

A sweep writes `<dir>/runs/<item>.runs.json`. Every check that looked for
artifacts globbed `<dir>/<item>.runs.json` — **one level** — so the nested layout
was invisible to all of them. `measured.record` reaches it only because the out
path is handed to it explicitly; nothing that goes LOOKING for artifacts had that
help.

**How it surfaced.** The paper sweep of 2026-09-15 covered all 26 items and
landed in `paper_0914/runs/`, correctly stamped with the day's
`paper_render_sha`. `check_paper_feedback_explains_its_deductions` then reported
**all 26 items unattributable** — on the morning the freshest paper measurement
in the corpus arrived. The only artifact it could see was an undated
`pooled_paper/` from an earlier era, so the newest evidence on disk counted for
nothing and the oldest decided the finding.

**The shape worth keeping.** This is a check going QUIET rather than wrong. The
finding it emitted was real in form — those items genuinely had no *visible*
attributable artifact — and the sentence gave no hint that the search had missed
a directory. Nothing about a glob that is one level too shallow looks shallow.

**Fixed** by `enforcement._runs_files(root, pattern)`, which unions both layouts
and is defined ONCE so they cannot drift apart again. Applied at all nine sites:
six in `enforcement.py` (`check_paper_feedback_explains_its_deductions`,
`check_students_see_what_each_check_decided`, `check_every_sweep_is_recorded`,
`historical_map_divergences`, `check_mapped_slots_agree_with_their_map`,
`check_count_scaffolds_are_arithmetic`) and three in `measured.py`
(`_ever_right`, `unrecorded_artifacts`, `criterion_rows`).

**A SECOND defect sat underneath it, and the glob fix alone did not clear the
finding.** The check added an item to `unattributable` on EVERY artifact whose
stamp was stale, while its message said the items had *no* attributable artifact.
Those are different claims, and the corpus keeps every artifact it has ever
written — so one undated archival directory condemned an item no matter how fresh
its newest measurement was. The same fault, in the same session, as the web-side
check that needed an `attributed` set; this one now keeps that set too and
reports only items with nothing attributable at all.

**Fire-tested both ways rather than assumed:** move the feedback wording and all
26 items report; restore it and the check is clean. The repair did not blind it.

**Scope measured before the change, not after:** 895 artifacts sit at one level
in 339 directories, 29 at `<dir>/runs/` in three — `opus_1c_0915/runs`,
`paper_0914/runs`, `e25_paper/runs`, all recent. Widening surfaced no new
findings anywhere, which is why the fix went in as a widening rather than as a
narrowing of what counts as an artifact.

**Owed:** the nested layout is now read by nine call sites and written by the
sweep scripts, and nothing asserts the two agree. A check that a sweep's declared
out-path is reachable by `_runs_files` would have caught this the day the layout
was introduced, and belongs with whatever owns sweep plumbing.
