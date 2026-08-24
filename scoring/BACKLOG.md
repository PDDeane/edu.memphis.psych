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

Fixing it CHANGES A PROMPT for Q5, so it needs a sweep. Six passes now exist
(`out/web_v8`, `out/web_v9`) and the fixture audit below measured what the dead
note does and does not cost: refusals still happen, under `wrong_kind`, so what
is lost is the DISTINCTION the note draws rather than the deduction itself — and
no COUNTED cell exercises a refusal at all, so the fix cannot be validated on
the rate. Read that section before sweeping.

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
citing "{{corpus:2a/p18:how1:0:72:sha=83a2672f3aa9}}
data" — a sentence the student did write — and the cell scores gold's 6.0 in 5
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
"{{corpus:Q4a/p19:first:23:58:sha=ca9d4ea70d5d:shape=S4-20}}" — which is the phrase the item's own
guidance lists in its ACCEPT bullet, in the sentence that says those examples
"all earned full credit" (`rubric_h1.py:683`). So this is not an
under-specified criterion. The grader is refusing an example the prompt tells
it to accept, verbatim, and the cell loses exactly the 2 points that refusal
costs.

Two things follow, and the second is the one to act on.

* **The prompt reproduces a counted cell's own answer, undetected.**
  `check_rule_examples_are_not_corpus` needs an 8-word shared run; this phrase
  is six, and its neighbours in the same bullet ("long {{corpus:Q4a/p15:first:14:43:sha=7d2e226fbc73:shape=S4-0a2020}} filled", "{{corpus:Q4a/p15:second:0:26:sha=b39ebb0b59d3:shape=C1}} me") are p15's. p15 is declared,
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
  "{{corpus:Q4c/p9:second:0:86:sha=ffcd2e47f756:shape=S12-0a2020}} body", and `consequence_2` comes back `wrong_kind` on exactly that
  text, 6 of 6. A benefit of the goal behaviour is being caught.
* **The sufficiency test does not.** The DEDUCT bullet quotes p20's
  "{{corpus:Q4c/p20:second:54:80:sha=106b406ee2c5:shape=S0-0a2020}}" and records that the grader wrote "need more explanation on
  how your second example is a direct consequence". Our grader answers `met` on
  that sentence in 6 of 6 passes. "The causal link is left for the reader to
  guess" is a different judgement from "this is not a consequence at all", and
  only the second one is reaching the model.

So the work here is the sufficiency test, not the category test. It is also the
test with no counted cell behind it, so any change to it must be measured on the
excluded cells as a diagnostic and swept corpus-wide for damage elsewhere.

### p9's residual gap is a gold shape that is already declared elsewhere

Our 3.0 against gold's 1.0 is not the cited example: `consequence_2` is refused
as designed. It is `consequence_1`, "{{corpus:Q4c/p9:first:0:47:sha=649fd6c0427a:shape=S5-0a}}", which gold also refused — its -4 is two refusals while its
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

The existing item above is confirmed and can be sharpened. Q5's web slots offer
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
  `W_NOT_REASON` bullet says p4's second entry — "{{corpus:Q5/p4:second:31:83:sha=342a4d43bd2e:shape=S4-0a2020,A46}} tired" — "cost participant 4 2.5 points". Gold's row
  reads "-2.5 pts: missing one reason why you continue to engage in lack of
  sleep", which is `W_ONLY_ONE`'s wording, not `W_NOT_REASON`'s. Both cost 2.5,
  so no score can separate them, and the guidance is describing a charge gold's
  own words do not make.
* **p4's first box is the student's text, checked.** It reads "{{corpus:Q5/p4:first:0:78:sha=f7407ff462b1:shape=S1-0a2020}}" — a
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
line begins "{{corpus:3/p1:first:0:29:sha=29ebb0f7a822}} room", so the character was the
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
punishment); p6's "{{corpus:3/p6:first:303:352:sha=bbf115c1a2ba}}
effective."; p9's "{{corpus:3/p9:first:275:323:sha=77075afddf4e:shape=A11}} ..."; p16's
"{{corpus:3/p16:first:129:148:sha=28364ff781d5:shape=A8}} ... {{corpus:3/p16:first:180:204:sha=cad7a69987aa}}"; p19's two sentences about
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
changes sit inside ONE sentence — "{{corpus:3/p3:first:455:581:sha=008fda0a2efa:shape=S6-0a,S22-0a}}" — and nothing anchors a second box. Gold gives 6.0 and so do we, in every
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
    p6/title  ['Time', ' {{corpus:1c/p6:title:5:33:sha=90d22ddc95fc:shape=R28-0-275d}} — a typed title naming
            the student's behaviour and time span, not the default 'Chart
            Title' placeholder.
    p17/x   "Days of the Week" (axis title beneath the Sunday–Saturday tick
            values)

The web grader's question for those slots is whether the student labelled the
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
`legend: absent`, on `"{{corpus:1c/p11:series:0:63:sha=bb9a6fb8ffd3:shape=S5-0a}}"` — the student labelled their series with day names, and gold
charged x, y and the missing baseline week without charging the legend.

The conclusion may survive (nothing here needs excluding), but the reason given
does not, and the cell is a live disagreement on a criterion the note never
mentions. The fixture is not the cause: `series` comes from `sim` and holds the
student's literal legend, which is exactly what the box is for.

### p20's labels are now seeded from its own description — SETTLED

The `unscoreable` entry reads: "a written DESCRIPTION of a graph, which on the
web IS the answer: the labels are typed into fields and the chart is drawn from
the four complete weeks". Only the second half was happening. The four weeks
were seeded; `title`, `x` and `y` were all EMPTY, because there is no chart for
the paper scorer to read a title off, and p20's whole description belonged to no
box.

Closed by seeding the three labels from the student's own words — "{{corpus:1c/p20:title:0:27:sha=d794c8f137de:shape=S0-0a}}", "Days (or Weeks)", "Hours of Sleep" — in
`agreement_app.CONSENSUS_FIXES`, which is what they would have typed into the
three fields. The scaffolding they wrote around them ("Title:", "X-axis label:",
"Y-axis label:", "Legend:") stays out of the boxes, like every other label in
the corpus, and `series` was already right from `sim`. All three now locate
inside the response (@7, @49, @79), the cell carries no audit flag, and the
exclusion entry says what actually happens.

The cell stays `unscoreable`: gold's 0 is for a graph that was never drawn, and
seeding the labels is what makes that failure unreachable on the web rather
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
                  {{corpus:Q3/p19:specific:0:78:sha=9156e5c27e31:shape=S11-0a202020202020202020202020202020202020}} ... Measureable: My {{corpus:Q3/p19:measurable:16:83:sha=77e770a31945:shape=S2-0a202020202020202020202020202020202020}} ..."

So `measurable` holds a printed INSTRUCTION, `specific` holds the printed
QUESTION plus two of the five aspects, and the student's real measurable
sentence is inside the specific box. `action`, `realistic` and `timebound` are
correct. Nothing is unassigned, which is why no check sees it: the response is
fully covered, just covered wrongly.

It matters more than the enumerators for two reasons. The grader is asked
whether the goal is measurable and shown an instruction, so a refusal there is
guaranteed and means nothing. And gold docks p19 exactly that point — "-1 pt:
For measurable, how are you tracking your goal? (ex. in a notebook)" — while the
student's own sentence says "{{corpus:Q3/p19:measurable:43:145:sha=504d8ac8b9af:shape=S10-0a}} time". Whatever our scorer
returns for `measurable`, it is not returning it about the student's answer, and
if it agrees with gold it agrees for the wrong reason.

**Repaired.** `measurable` now holds the student's own "{{corpus:Q3/p19:measurable:0:83:sha=4148ed277c0c:shape=S2-0a}} ..." and `specific`
holds only "{{corpus:Q3/p19:specific:0:100:sha=10eaefa02315:shape=S13-0a}}" Both lines of template scaffolding drop out and
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

    [state_a1]  "{{corpus:Q6/p18:state_a1:0:50:sha=c9250d345b28}}"
    [change_a1] "{{corpus:Q6/p18:change_a1:0:106:sha=e8781011c827:shape=S14-0a2020202020202020202020202020202020}}"
    [state_a2]  "{{corpus:Q6/p18:state_a2:0:60:sha=c6293ae612e6}}"

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
actually decides the score — the five definitional gates the web reads as slots
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
describing it better: the model's reading of "{{corpus:DAY1/p13:day1:26:48:sha=0a299977f146}} playing
video games" as an arranged removal is stable across every phrasing tried, and
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

**WK2 is a real over-credit and is no longer declared.** "{{corpus:WK2/p8:wk2:0:80:sha=b1483eea3dd9:shape=S4-0a}} hour" puts the chore
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
out four days a week, and the penalty they set for {{corpus:Q4c/p8:first:19:42:sha=7ac6426f11ad}} extra
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
must stay correct names BOTH SIDES in one canonical conditional — "{{corpus:PR/p2:pr:0:48:sha=6c9624661ff5:shape=S3-0a,C1}} the movies". TEST 1 and the two gates added on
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
contingency: "{{corpus:WK1/p5:wk1:62:164:sha=bcb2f8e5c91b:shape=S5-20,S13-0a}}" p5 is correctly scored by everyone, and
proves nothing about gates.

Read in full, WK1's countable cells separate perfectly on one feature — whether
the answer names SOMEONE WHO DELIVERS the consequence:

    gold 4   p1  "{{corpus:WK1/p1:wk1:49:87:sha=8d68ef1ac8b9:shape=S5-20}}"
             p4  "{{corpus:WK1/p4:wk1:56:91:sha=50343f5b996f}}"
             p5  "{{corpus:WK1/p5:wk1:108:135:sha=deaa7bffadae}} one chore"
             p9  "{{corpus:WK1/p9:wk1:46:83:sha=441a5dbfab7f}}"
             p11 "{{corpus:PR/p11:pr:22:49:sha=44f5be7c8687}} alo set"
             p12 "{{corpus:WK1/p12:wk1:51:87:sha=1601ce28c9c1}} day"
             p14 "{{corpus:WK1/p14:wk1:86:132:sha=364885d56dfc}} nice"

    gold 0   p6  "{{corpus:WK1/p6:wk1:0:50:sha=465f4decda26}} pops..."
                 — a substitution; nobody delivers anything
             p8  "{{corpus:WK1/p8:wk1:107:136:sha=8740f4342e10}} stacking"
                 — no agent; the tally grows by itself
             p13 "{{corpus:WK1/p13:wk1:0:51:sha=848ae9e56f72}}"
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
"{{corpus:WK1/p8:wk1:107:136:sha=8740f4342e10}} stacking" (no agent) from "{{corpus:PR/p11:pr:22:49:sha=44f5be7c8687:shape=S6-0a}} alo set" (an agent, but modal and passive-ish), which is the distinction the
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

WK1 rose from 15 to **17 of 18**, and the divergence is retired.

Every version up to attempt 8 asked a question about the PLAN — "is a consequence
delivered?" — and the model wobbled on the only two cells that separate. The cue
I had actually found by reading the texts was SYNTACTIC, and a parse is something
the model does crisply. So the slot asks two mechanical things about the clause
that states the consequence:

  (a) its SUBJECT — is a person there, as the subject of an active verb or the
      agent of a `by`-passive?
  (b) its VERB — does it say that person brings the thing about or takes it away,
      read broadly enough to include granting oneself a privilege ("{{corpus:WK1/p1:wk1:56:72:sha=d6d0e13bdc92:shape=S2-0a202020202020}} hour", "skip one chore")?

and answers `absent` when the subject is the CONSEQUENCE ITSELF with a verb of
accumulation ("the press-ups will just keep stacking"), when there is no finite
clause, or when the answer is off the point entirely.

    sweep   15/15/16 -> 17/17/16, seventeen of eighteen cells at 3/3
    probe   p8 absent 6/6, scoring 0 against gold 0
            p1 met 6/6 — the boundary case the first verb list broke, at 3/6
            controls p4 and p11 6/6

**The verb list is where the first version went wrong, and it is a general
warning.** Written as a list of transfer verbs, it excluded "{{corpus:WK1/p1:wk1:49:87:sha=8d68ef1ac8b9:shape=S4-0a,S5-20}}" — a student granting themselves a privilege — and put a
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

Mirrored on the CLI as an enum property with the same derivation, so the paths
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
UTB response is "{{corpus:Q1/p7:response:0:27:sha=fd875dec0a64:shape=R8-1-27}}{{corpus:Q1/p7:response:27:54:sha=e207b8a916a2:shape=A26}} {{corpus:Q1/p7:response:55:128:sha=90fbce1afce7:shape=S1-0a,R0-5-53494e4345,R8-3-454e44,R12-2-5550,R15-15-50524f4352415354494e4154494e47,R73-0-22}} The grader is
handed that whole paragraph as `_utb`. So when the weekly answer triggers on "{{corpus:WK1/p7:wk1:0:38:sha=6faf4f5c97b3:shape=S0-0a,C1}} week", a rule asking whether the trigger
names the student's UTB can answer `utb` on good evidence — the word is in the
text it compares against. Gold's "your UTB is not procrastination" is true of the
CHOSEN BEHAVIOUR and false of the paragraph we supply. That is a context
question, not a criterion one: it would be settled by passing the grader the
chosen behaviour rather than the whole Q1 response, which is a fixture change
with its own blast radius across every item that reads `_utb`.
