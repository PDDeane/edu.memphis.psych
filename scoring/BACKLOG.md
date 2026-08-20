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
citing "My exercise intake increased from 0 to 3 session a week, as shown by the
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
  `W_NOT_REASON` bullet says p4's second entry — "because I get super emotional
  and mad when I'm super tired" — "cost participant 4 2.5 points". Gold's row
  reads "-2.5 pts: missing one reason why you continue to engage in lack of
  sleep", which is `W_ONLY_ONE`'s wording, not `W_NOT_REASON`'s. Both cost 2.5,
  so no score can separate them, and the guidance is describing a charge gold's
  own words do not make.
* **p4's first box is the student's text, checked.** It reads "I continue
  sleep enough because sleep is good for you, I am gaining something)" — a
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

## Template residue reaches the grader in 47 student boxes across 13 items

Found by item 3's fixture audit, but not an item-3 problem. Template
subtraction leaves an orphan punctuation run at the head of a response, and
where a box starts at the beginning of the response that run is served to the
grader as the student's first characters.

| item | boxes | residue |
| --- | --- | --- |
| H3/3 | 15 | `") "` — the printed question's own closing parenthesis |
| H2/PP, NR, NP, D2, PR, D1, DAY1, DAY2 | 23 | `"_ "`, `"; "` — the blank rule the student typed on |
| H1/Q3 | 5 | `"- "` (four of them one cell, p6) |
| H1/Q1, Q2, Q6 | 4 | `"_"` |

Item 3's is the clearest to read: its question ends `... so you should not say,
"Nothing will be changed"). (6 points: 3 points per example)`, the stem strip
removes the matched prefix, and the `")"` that closed the parenthetical survives
into 15 of 20 `first` boxes. Checked against the submission — the student's own
line begins "Next time I will leave wiggle room", so the character is the
template's, not theirs.

Why no check catches it: for a one-box item
`check_single_box_fixtures_are_verbatim` compares the box against the response
and both carry the residue, which is the same blind spot its docstring already
records for mojibake — "the fixture and the response agree, because both are
wrong together". Items whose boxes are anchored
to a scorer quote are immune by accident: the junk falls outside the quote (Q4a
and Q4c p19 both leave a `"_"` unassigned).

The fix belongs in `segment.py`'s template subtraction — strip a leading orphan
punctuation run once, and 47 boxes in 13 items are corrected together. That
changes served text for every harness, so it needs a corpus sweep, and it is why
this was NOT done cell by cell in the fixture tables. Nothing here is measurably
costing a point today; it is prompt text inside a student's box.

One row in the survey is a false positive worth remembering: H3/1c `p6/title`
starts `['Time', ' Spent a...` because it is a PARSED VALUE, not a quotation.
`_value_derived` already says so for the item.

## Item 3: what the fixture audit left behind

Five cells repaired — p4, p6, p9, p16 and p19 — all one defect: `second` opened
with a sentence that elaborates the FIRST change, so box 2 began before change 2
did. p4's opened "I hate school!" (about change 1's extra-schoolwork
punishment); p6's "That would have made my modification results more
effective."; p9's "Some days I'm ready to go home after working out ..."; p16's
"If I don't exercise ... I would take away sweets"; p19's two sentences about
the screen-time limit it had just proposed. Each boundary moved to the sentence
that opens change 2, and the union of each pair is unchanged — asserted cell by
cell before the entries were written. Declared in
`enforcement.MULTI_BLOCK_DECLARED`.

**Re-baseline all five.** This is the item's whole risk. Item 3 is **20 of 20
counted, identical across six passes, with NO exclusions** — the only such item
audited so far — so every one of these five cells currently agrees with gold and
the repair can only be checked by measuring. The reason the mis-cut cost nothing
is that `changes_given` is one count over the whole response, so a sentence in
the wrong box does not change the total; that is also why the repair is expected
to be inert. Expected, not shown. If a cell moves, revert that cell — the
entries are per-cell and independent.

### p3 earns its 6.0 from one box, and that is a real gap

p3's `second` is empty and `first` holds the entire response, because its two
changes sit inside ONE sentence — "letting myself feel comfortable in my skin
and focus solely on my goals, I will also push myself to get my entire workout
done" — and nothing anchors a second box. Gold gives 6.0 and so do we, in every
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
    p6/title  ['Time', ' Spent at Gym Over Four Weeks'] — a typed title naming
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
`legend: absent`, on `"Sunday, Monday, Tuesday, Wednesday, Thursday, Friday,
Satureday"` — the student labelled their series with day names, and gold
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

Closed by seeding the three labels from the student's own words — "Sleep
Duration Over 4 Weeks", "Days (or Weeks)", "Hours of Sleep" — in
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

## Q3/p19's boxes are misaligned by one, and one of them holds the instructions

Found while writing up the enumerator sweep above, in the same three items that
were declared before the audit pass. It is a worse defect than the enumerators
and it is one cell.

p19 typed the handout's own scaffolding above their answer, and the split took
it for content:

    [measurable] "You must discuss and label each aspect of the SMART goal
                  for full credit."
    [specific]   "(How is your wanted goal behavior: Specific, Measurable,
                  Actionable/Action-Oriented, Realistic, and Time-Bound?)
                  Specific: My goal is specific because i plan to get 8 hours
                  of sleep per night ... Measureable: My goal is measurable
                  because i will track how long I sleep each night ..."

So `measurable` holds a printed INSTRUCTION, `specific` holds the printed
QUESTION plus two of the five aspects, and the student's real measurable
sentence is inside the specific box. `action`, `realistic` and `timebound` are
correct. Nothing is unassigned, which is why no check sees it: the response is
fully covered, just covered wrongly.

It matters more than the enumerators for two reasons. The grader is asked
whether the goal is measurable and shown an instruction, so a refusal there is
guaranteed and means nothing. And gold docks p19 exactly that point — "-1 pt:
For measurable, how are you tracking your goal? (ex. in a notebook)" — while the
student's own sentence says "i will track how long I sleep each night by going
to sleep at the same time, and waking up at the same time". Whatever our scorer
returns for `measurable`, it is not returning it about the student's answer, and
if it agrees with gold it agrees for the wrong reason.

The repair is mechanical and local: `measurable` takes the student's Measureable
sentence, `specific` keeps the question-line and its own sentence or drops the
question line too. It is a counted cell in an item at 5 of 5 aspects per cell,
so measure it.

Checked while looking: p11 is NOT a second case. Its `specific` box carries
tracking prose that reads like `measurable`'s job, but both boxes hold the
student's own words, and gold gives the cell full credit.
