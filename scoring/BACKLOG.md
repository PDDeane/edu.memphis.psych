# Jobs we need to do

Work items, not enforced declarations. The enforced backlogs — `SLOT_NOTES`
`BACKLOG`, `FIXTURE_GAP_BACKLOG`, `CONSENSUS_OVERLAP_BACKLOG`,
`CORPUS_QUOTE_BACKLOG` — live in `enforcement.py` and are keyed by cell or slot,
so a check fails when one goes stale. Nothing here is checked; it is a list of
things a person has to decide to do.

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

## Q5 `example_2` names a token the web enum does not have

`bmod_handout1.olx:1072` tells the web grader to answer `not_reason` when the
second entry is a real, distinct entry that is not a reason for CONTINUING. The
same line's `slots=` offers that check `wrong_kind/duplicate`. So the test is
inert: the model is asked for a token it cannot return, and the diagnosis the
rule exists to draw never gets drawn. It has to be reading through to `absent` or
`met` instead, which are different findings.

This is the exact failure the `{fail}` placeholder was built to prevent —
`olx_prompts.py:1682` records the last instance of it, where the paper scorer was
told when to answer `wrong_kind` while being offered `met/absent/not_active`, and
"every test was inert and it credited p8's 'avoiding going the gym' that the web
and CLI both reject." Same slot family, same year.

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

Not measured. Fixing it CHANGES A PROMPT for Q5, so it needs a sweep, and Q5 has
no measurements against current inputs.

`not_reason` in `rubric_h1.py:979` is NOT part of this — that is the paper
scorer's own vocabulary, bridged by `enforcement.ALIAS`, and it is correct there.

## 2a: what the fixture audit left behind

The fixture itself is done — all 20 cells read out box by box, two repaired
(p16's unstripped `"Sentence 3:"` label, p20's comma-initial `how1`), and the
split declared in `enforcement.MULTI_BLOCK_DECLARED`. Everything below is what
the readout found that a fixture fix cannot reach.

**Re-baseline first: the numbers here predate the two repairs.** Derived from
`out/web_v8` and `out/web_v9`, three passes each, honouring `cell_exclusions`:
**14-15 of 17 counted** (15-17 of 20 with exclusions in the denominator). p16 is
one of the cells whose fixture just changed, so its six passes no longer
describe what would be served. Re-derive before attributing anything to a
change.

### The over-credit is one shape, and it is the only shape

Every miss in the item is **+2.0, crediting a second `how` gold withheld** — and
that holds on all six passes, in both directions of the split cells:

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

### p18's `unscoreable` exclusion is stale

`handouts.py:811` says gold's 6.0 is unreachable because `join_aware` strips the
template verdict the student copied, so "no verdict of p18's own survives". The
record says otherwise: `verdict` came back **`met` in 6 of 6 passes**, every one
citing "My exercise intake increased from 0 to 3 session a week, as shown by the
data" — the student's own surviving sentence — and the cell scores gold's 6.0 in
5 of the 6. The item's own guidance licenses that reading in terms ("a verdict
that cites the data as its evidence ... covers the verdict and both
explanations").

So this is QUALITY_CONTROL.md §5's second rule exactly: an exclusion on a cell
the scorer gets RIGHT. Two ways out, and the entry cannot stay as written:
remove it, so an agreeing cell counts and n goes 17 → 18; or keep it and declare
`expect_error`, which is what would have caught this without anyone looking —
this entry is one of the four live ones that declare no number.

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
`EQUIVALENCE.md:1763` already invalidated 2a's web numbers once for exactly this
reason, and Q6 was frozen from a 10-run consensus after its spans moved on 47%
of slots per rerun. Until 2a is frozen or hash-pinned, any comparison spanning a
paper re-run is not like-for-like.

Related: `EQUIVALENCE.md:487` still lists 2a among the eleven items that "agree
on every single cell". That is the superseded web_v2 sweep; on web_v8/v9 the
item is 14-15 of 17. The line sits in a dated section, but it is the kind of
stale headline §5 warns about and should be annotated where it stands.
