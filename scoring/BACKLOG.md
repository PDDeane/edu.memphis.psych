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
"waking up and not feeling motivated" — which is the phrase the item's own
guidance lists in its ACCEPT bullet, in the sentence that says those examples
"all earned full credit" (`rubric_h1.py:683`). So this is not an
under-specified criterion. The grader is refusing an example the prompt tells
it to accept, verbatim, and the cell loses exactly the 2 points that refusal
costs.

Two things follow, and the second is the one to act on.

* **The prompt reproduces a counted cell's own answer, undetected.**
  `check_rule_examples_are_not_corpus` needs an 8-word shared run; this phrase
  is six, and its neighbours in the same bullet ("long spans of time that need
  to be filled", "friends calling or texting me") are p15's. p15 is declared,
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

### p18's second box: the fix is agreed and deliberately NOT applied

p18 wrote one antecedent and repeated it verbatim as its second, so `second` is
empty and 153 characters of the response belong to no box. The agreed repair is
to fill `second` with that duplicate, which is what the student actually
submitted; it is held pending release and must not be applied as a side effect
of anything else.

Recorded so the reason survives: the cell currently agrees with gold at 3.0 in
6 of 6 passes, gold's row is "-2 pts: only provided one antecedent", and
filling the box invites the grader to credit two. Releasing the fix therefore
probably costs the agreement, and the honest landing place would be a
divergence or a ceiling rather than an empty box that scores well.

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
student's enumerator inside them ("1) I end up facing ...", "1. One consequence
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
  "I would of reached my goal weight, better health, and maintaining a healthy
  weight and body", and `consequence_2` comes back `wrong_kind` on exactly that
  text, 6 of 6. A benefit of the goal behaviour is being caught.
* **The sufficiency test does not.** The DEDUCT bullet quotes p20's
  "finishing
  my homework late" and records that the grader wrote "need more explanation on
  how your second example is a direct consequence". Our grader answers `met` on
  that sentence in 6 of 6 passes. "The causal link is left for the reader to
  guess" is a different judgement from "this is not a consequence at all", and
  only the second one is reaching the model.

So the work here is the sufficiency test, not the category test. It is also the
test with no counted cell behind it, so any change to it must be measured on the
excluded cells as a diagnostic and swept corpus-wide for damage elsewhere.

### p9's residual gap is a gold shape that is already declared elsewhere

Our 3.0 against gold's 1.0 is not the cited example: `consequence_2` is refused
as designed. It is `consequence_1`, "Gaining bad eating habits, while not
exercising", which gold also refused — its -4 is two refusals while its
commentary accounts for one. That is the same shape as Q4a/p14, which
`handouts.GOLD_DIVERGENCES` already declares in those words. Q4c/p9 has no such
entry, and should get one if its citation is ever removed; while the citation
stands, the `self_graded` exclusion covers it.

For the record, the fixture is not the cause: p9 is one run-on line with a
single comma, and the split leaves "while not exercising" with the clause that
comma attaches it to. Splitting the other way leaves `first` as a bare
"Gaining bad eating habits", which is creditable too.

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

`EQUIVALENCE.md:562` reads Q4c at "CLI 76%, web 65% over 17 cells" and closes
"Nothing to fix. Left alone." All three parts have moved: the denominator is 12
counted, not 17; its web-only p13 gap was `keyword: absent` on "conequence",
which cannot arise now that Q4c's keyword slot is advisory with `pts=None`; and
three boxes were in fact fixed above.
