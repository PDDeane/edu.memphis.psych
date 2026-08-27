# LIVE AND MEASURED. `reasons_given`: count statements, not counters

**Landed and kept**, on a measured +1: Q1 **16/20 -> 17/20**, six runs
[15,16,16,17,18,19], mean 16.2 -> 16.8, artifact `reasons_rule_v1`, probe filed
at prompt `fa105e57b2c0`, verdict permitted. Kept on a WEAK result -- read
"What the measurement actually said" at the bottom before building on this.

Applies to **Q1 ONLY**. An earlier version of this file said the rule was
"shared by Q1 and Q2" because both items carry
`counts="reasons_given:reason_1,reason_2,reason_3"`. The COUNTER is shared; the
RULE is not. Q2 has its own 921-character text asking a different question --
how many statements are a real benefit of the GOAL behaviour, `reasons_listed`
minus `reasons_failing`, with harms of the unwanted behaviour explicitly excluded
as belonging to Q1 -- and it contains neither the old harms-dominate clause nor
the new one. Changing Q1's desc cannot reach it, which the generator confirmed by
reporting exactly one changed section and a one-line OLX diff.

Consequence: **Q2 is not a regression test for this change and does not need
re-sweeping.** The decision rule below is amended accordingly -- there is no
Q2 column to lose. Q2's own misses (p10 at 1/6, p20 at 2/6, p18 at 4/6) are a
separate question against its own rule, which is worth reading later; its
structural test for whether one sentence holds one or two benefits is the same
idea as the "single clause counts ONCE" clause, so the two items are now
conceptually aligned rather than divergent.

## What the current rule does

    If `harms_listed` is 1 or more the answer IS `harms_listed`, and benefits
    do not add to it -- a response with one harm and two benefits counts 1.
    Only when `harms_listed` is 0 does the answer become `benefits_listed`.

Harms dominate; benefits are discarded whenever a single harm is present.

## The evidence (Q1, 6 runs, `scorer_fix_6run`)

| cell | gold | model | who is right | why |
|---|---|---|---|---|
| p9  | 2 | **1** in 5/6 | gold | one clause was split across both counters, then harms-dominate discarded the benefits |
| p14 | 3 | **2** in 4/6 | gold | one statement filed as a benefit, so harms-dominate discarded it; the one run that filed it as a harm scored gold exactly |
| p10 | 2 | **3** in 5/6 | rule AND gold agree at 2 | the model counted a restatement of the goal, which `benefits_listed` already excludes; the two runs that applied the rule properly scored gold |

Two findings, not one:

1. **The rule is wrong against gold on p9 and p14.** In both, the shortfall is
   exactly the benefits the rule threw away. Gold counts distinct statements that
   supply a reason, harm or benefit alike.
2. **The score currently depends on a split the model cannot make reliably.**
   p14 flipped purely on which counter one sentence landed in; on p10 the model
   filed benefit text under `harms_listed` in 4 of 6 runs. The rewrite below
   makes the total INVARIANT to that split, which is the larger prize -- it
   removes a source of variance rather than re-describing a judgement.

## The proposed replacement for `reasons_given`

Corpus-free by construction: no phrase below is taken from any response, so
`leakage.py` and `check_rule_examples_are_not_corpus` have nothing to catch.

    HOW MANY separate reasons the student gives. Count STATEMENTS, and count
    both kinds towards the SAME total: a statement naming a NEGATIVE EFFECT of
    the behaviour and a statement naming a BENEFIT of changing each count one.
    A single clause counts ONCE however many ways it can be read -- one clause
    that names both a gain and the trouble avoided by it is one reason, not two,
    and a clause already counted under one heading is never counted again under
    the other. Two DISTINCT effects merely joined by "and" are two. Do NOT count
    a restatement of the goal or of the behaviour itself, a remark about how hard
    the behaviour has been to change, or background about how it came about.
    Answer 3 for three or more.

`harms_listed` and `benefits_listed` keep their current text and stay in the
sheet, but become DIAGNOSTIC rather than load-bearing: `reasons_given` no longer
reads them. That is deliberate -- they are what made the p14 coin-flip visible,
and they cost nothing to keep asking.

Volume: **389 -> 614 characters, +58%**, measured in both trees with
`before_after.py`. An earlier version of this paragraph claimed the replacement
was "within a few characters" and volume-neutral; that was wrong, caught by
measuring instead of asserting, and it matters, because §3's coupling tax scales
with volume. A first draft ran to 769 chars (+98%) and was tightened to this
without dropping a load-bearing clause. So collateral movement on cells with no
diagnosed problem is a LIVE risk here, not a remote one -- which raises the value
of the guard list below rather than lowering confidence in the rule itself.

## Why NOT computed arithmetic

The obvious alternative is to make `reasons_given` a computed check --
`harms_listed + benefits_listed`, capped at 3 -- so the count is arithmetic
rather than prose. **It fails on p9.** The model saw 1 harm and 2 benefits
because ONE clause was counted under both headings; the sum is 3 and gold is 2.
The "same clause counted once" sentence is doing the work, and no sum over the
two counters can express it while the model is the thing filling them in.

## An instrument fix to land alongside

`harms_listed` and `benefits_listed` record as `""` in every artifact. A count
slot that is not named in the rubric's `counts` never gets its verdict written,
so only `evidence` preserves what the model answered -- and these two are the
operands of the rule that decides the score. Same shape as the count-recorded-
as-blank bug fixed last session: reading the artifact tells you the checks were
never answered when in fact they were.

## Test plan

Baselines to beat, both recorded at six runs against this scorer sha:

* **Q1 16/20**, runs [15, 16, 16, 16, 17, 17], artifact `scorer_fix_6run`
* **Q2 18/20**, runs [16, 17, 17, 18, 18, 18], artifact `scorer_fix_6run`

Six runs each, one at a time or two at most (`agreement.py --handout 1 --items
Q1 --runs 6`), then `compare_runs.py`, `--record-probe`, `measured.py --record`.

Per-cell predictions, stated in advance so the result is judged against them:

* **Q1/p9** 1 -> 2, score 3 -> 4, matching gold. The clearest test of the change.
* **Q1/p14** 2 -> 3, score 4 -> 5, matching gold.
* **Q1/p10** unchanged at 3 (score 5, gold 4). The exclusion it violates is
  already in `benefits_listed` and the model ignores it, so the rewrite is not
  expected to reach this cell. If p10 improves, that is a bonus and its cause
  should be read, not assumed.
* **Guards:** the sixteen Q1 cells currently correct must hold. There is no Q2
  column -- see the correction at the top of this file. With no second item to
  cross-check against, the guard cells ARE the whole regression test, which the
  +58% volume increase makes more important rather than less.

Decision rule, agreed in advance: keep if Q1 gains and no currently-correct cell
is lost; revert if Q1 does not gain, or if it gains p9/p14 while losing two or
more guard cells -- trading diagnosed cells for undiagnosed ones is not progress,
and with the block 58% longer that is the failure mode to watch for.


## What the measurement actually said

Predictions were half right, and the half that failed is the more interesting
one.

| cell | before | after | prediction |
|---|---|---|---|
| p14 | 2/6 | **6/6** | predicted 6/6 — CORRECT, and the strongest result here |
| p9  | 1/6 | 3/6 | predicted 6/6 — WRONG; improved but its misses now OVERSHOOT |
| p10 | 1/6 | 2/6 | predicted unchanged — correct |
| p6  | 4/6 | **0/6** | GUARD LOST, stable, over-credits 5 against gold 3 |
| p16 | 6/6 | 4/6 | guard degraded |
| p5  | 6/6 | 5/6 | guard degraded |
| p7, p18, p19 | 5/6 | 6/6 | guards firmed up |
| p17 | 3/6 | 4/6 | unstable before and after |

**p14 validates the actual thesis.** Its score used to depend on which counter
one sentence landed in, and counting statements towards one total made it
invariant to that split. 2/6 -> 6/6 is that argument working.

**p9 refutes the diagnosis.** Harms-dominance was never p9's problem. One
sentence -- a gain and the trouble avoided by it, joined by "and" -- is read as
TWO reasons under the new rule and as ONE harm under the old, and gold counts it
once. The "a single clause counts ONCE" sentence did not control it. Moving from
a stable undershoot to a partial overshoot is not a fix.

**p6 is the same failure in reverse.** A stable 0/6 over-crediting by two points
says the rule is now too generous somewhere the old one was not.

Spread widened 2 -> 4 cells, which is the opposite of the invariance the change
was bought for. The item gained a cell and got noisier.

### Where the next attempt goes

At CLAUSE BOUNDARIES, not at which counter dominates. p6 and p9 are the paired
test: p9 must stop reading one "and"-joined clause as two reasons, and p6 must
stop over-counting, without giving back p14. Both rules so far have legislated
about the harm/benefit distinction, and neither has said anything precise about
where one reason ends and the next begins -- which is what both remaining cells
turn on. Q2's own rule already has a structural test of exactly this shape ("a
second half that is a knock-on effect of the first is ONE"), and it is the
obvious thing to borrow.


---

# v2 — the MIRROR PAIR, derived from all twenty cells (MEASURED AND REVERTED)

> **THE STUDENT TEXT QUOTED BELOW MUST NEVER BE COPIED INTO A PROMPT.** It is
> evidence for a rule, not material for one. Every illustration that goes into
> the rule itself is ABSTRACT, and the wording is checked word-by-word against
> the whole handout-1 corpus before it lands: v2's first cut said "stated as a
> loss and as a gain", and `gain` appears in three scored responses as "weight
> gain", so it became "a drawback and an advantage" — both absent from the
> corpus. `leakage.py --gate` is not sufficient on its own here; it has the
> shared-prose blind spot recorded as subgoal 4.

v1 was built from the three cells that missed. v2 is built from reading **all
twenty**, which is what §3 of QUALITY_CONTROL.md asks for and what v1 skipped.

## A correction to how gold's count was derived

Score alone does NOT give gold's reason count: some deductions are for the UTB
statement rather than the reasons. p20's `-2 pt: did not have one sentence
describing your UTB` means all three of its reasons WERE credited; deriving the
count from the score alone scores it as one. Gold's notes have to be read.

## What gold does with multi-item sentences

**Two independent items in one sentence -> TWO.** p13 (depression / lose
appetite), p19 (tired / unmotivated), p7 (sleep / productivity), p11 (weight gain
/ weaker muscles) — each joined by "and", each counted twice.

**A harm paired with its mirror-image benefit -> ONE.** p9, p3 (three such
sentences, three reasons), p17, p19 (its tired-clause against "want more
energy"), p6. THIS IS THE CLASS BOTH EARLIER RULES MISSED. v0 discarded the
benefit outright and undercounted when it was genuinely separate; v1 counted both
and overcounted when they were mirrors.

**A knock-on chain -> ONE.** p5's snacking clause and its "which causes"
consequence. Already Q2's structural test.

## The rule v2 adds

> Count DISTINCT CONTENT. A harm and a benefit that is merely its inverse are ONE
> reason — the same fact stated as a loss and as a gain — and so are a statement
> and a knock-on effect of it. Two items joined by "and" are TWO when they name
> different things and ONE when they are two ways of saying the same thing.
> Neither the sentence nor the clause is the unit: one sentence may hold two
> reasons, and three sentences may hold one.

Plus the exclusion list, now carrying "a behaviour performed DURING the unwanted
one" explicitly: `reasons_given` no longer reads `harms_listed`, where that
exclusion used to live, and gold states it in p2's own note.

The worked example is ABSTRACT on purpose. The natural illustration was p19's
own wording, and quoting a scored cell in a prompt is what
`check_rule_examples_are_not_corpus` exists to catch. Verified by tokenising the
rule against all eight handout-1 items x 20 responses: the only shared words are
function words already present in v0.

## Paper check against all twenty, before spending a call

    p1  2v  p2  2v  p3  3v  p4  3v  p5  2v  p6  1v  p7  3v  p8  >=3v  p9  2v  p10 2v
    p11>=3v p12 3v  p13 3v  p14 3v  p15 2v  p16 1v  p17 3v  p18 >=3v p19 3v  p20 3v

Reproduces gold on **all twenty**. Gold's own notes corroborate three exclusions
in its own words (p1 "struggling with it" is not a reason; p2's third item is a
behaviour done during the UTB; p16 credits only health).

Four cells — p8, p11, p18 and arguably p4 — are at or above the cap of 3, so they
cannot discriminate. The rule is really being tested on sixteen.

## Predictions

* **p9** 3/6 -> 6/6, score 5 -> 4, matching gold. The mirror pair is its whole
  problem.
* **p6** 0/6 -> 6/6, score 5 -> 3, recovering the guard v1 lost.
* **p14** holds at 6/6. It was v1's win and nothing in v2 removes the reason it
  works.
* **p10** unchanged at ~2/6. Its problem is the model ignoring an exclusion, not
  misapplying the count, and v2 does not change that exclusion.
* **Guards:** the seventeen cells correct at v1 must hold; p16 and p5, which v1
  degraded to 4/6 and 5/6, should recover if anything.

Volume: **759 chars, +95% over v0's 389 and +24% over v1's 614.** Stated plainly
because v1's paragraph got this wrong: the block keeps growing, and if v2 lands
neutral-to-worse while the paper check says it should be perfect, volume is the
first suspect and the next move is to cut rather than add.

Decision rule: keep if p9 AND p6 both recover and p14 holds; revert to v1 if p14
breaks; revert to v0 if neither p9 nor p6 recovers, since two measured attempts
at this rule would then have failed and the problem is not the wording.


## v2: measured, reverted

**Q1 median 16/20**, six runs [18,16,14,14,16,16], mean 15.7, spread 4 cells,
artifact `reasons_rule_v2`. Worse than v1's 17 and no better than v0's 16.
Reverted to v1 byte-exactly (`git checkout` of the v1 commit, OLX regenerated,
diff against the committed state EMPTY, Q1 re-recorded 17/20 at prompt
`fa105e57b2c0` — the same sha the v1 measurement was taken at).

            v0    v1    v2
    p9     1/6   3/6   6/6    the mirror-pair rule: FULLY FIXED
    p14    2/6   6/6   6/6    v1's win, preserved
    p6     4/6   0/6   0/6    lost at v1, not recovered
    p7     5/6   6/6   2/6    new collateral damage
    p17    3/6   4/6   2/6    degraded
    p16    6/6   4/6   3/6    degrading across all three
    p4      --    --   3/6    new; had never missed
    p11     --    --   5/6    new
    p10    1/6   2/6   1/6
    p5, p18, p19               held

### THE FINDING SURVIVES THE REVERT

p9 went **1/6 -> 3/6 -> 6/6** as the mirror-pair rule was stated more
explicitly. That is a dose-response on the cell the analysis targeted, and it
confirms what reading all twenty responses showed: **gold treats a harm and its
inverse benefit as ONE reason.** Keep this. What failed was the wording, not the
content.

### Why it went wrong

Every new miss over-credits by ONE, the spread widened to 4 cells, and the paper
check had predicted a perfect twenty. That is not a rule that is wrong; it is a
rule too long to apply consistently. v2 ran +95% over v0.

Two lessons worth more than the cell:

* **A paper check is necessary but not sufficient.** Reproducing gold on all
  twenty by hand established that the CONTENT was right. It said nothing about
  whether the model would execute 759 characters the same way twice, and it
  cannot -- that is a property of the model, not of the rule.
* **A per-cell decision rule is not enough on this item.** The rule agreed in
  advance ("revert to v1 if p14 breaks; revert to v0 if neither p9 nor p6
  recovers") did not fire: p14 held and p9 recovered, yet the item got worse.
  Future decision rules here need a MEDIAN clause.

# v3 — the mirror pair at LESS length than v1 (MEASURED AND REVERTED)

The room was hiding in plain sight. v1 DUPLICATED the exclusion list into
`reasons_given` when it stopped reading `harms_listed` and `benefits_listed`, and
those two components state the exclusions already, immediately above it in the
same prompt. v0 proved a pointer works: it said "CONDITIONAL on the two counts
above" and the model followed that faithfully -- p9's wrong answer was the rule
being obeyed, not ignored.

    HOW MANY separate reasons the student gives. Count DISTINCT CONTENT, harms
    and benefits alike, towards ONE total, and apply the exclusions stated in the
    two counts above. A harm and a benefit that is merely its inverse are ONE
    reason — the same fact stated as a drawback and as an advantage — and so are
    a statement and a knock-on effect of it. Two items joined by "and" are TWO
    only when they name different things. Never answer 0 when the student offered
    anything of either kind. Answer 3 for three or more

**508 characters: 106 SHORTER than the live v1, and only +119 over v0** — while
carrying the mirror-pair rule that v1 lacks entirely. Corpus-checked against all
eight handout-1 items x 20 responses: the only shared word is "only".

Dropped from v2, deliberately:

* the duplicated exclusion list -> replaced by the pointer (-1 sentence);
* "Neither the sentence nor the clause is the unit" -> redundant once "two items
  joined by `and` are TWO only when they name different things" is stated;
* v1's "a clause counted under one heading is never counted again under the
  other" -> that is the mirror rule said clumsily, and the mirror sentence
  replaces it.

### The dependency this reintroduces, and why it is safe

v3 points at the two counts again, which is what v0 did. The difference is WHAT
depends on them. v0 made the SCORE depend on the harm/benefit split -- the fatal
choice, because the model cannot make that split (p14 flipped on it, p10 filed
benefits as harms in 4 of 6 runs). v3 makes only the EXCLUSIONS depend on their
definitions, and the exclusions are identical for both kinds: a goal restatement
is not a reason whether you call it a harm or a benefit. So the arithmetic stays
invariant to the split while the prose stops repeating itself.

### Prediction and decision rule, in advance

* p9 6/6 and p14 6/6 both hold -- the mirror sentence is intact and its wording
  barely changes from v2.
* p7, p16, p17, p4, p11 recover toward their v1 rates -- this is the test of the
  volume hypothesis, and the only reason to expect it is that v3 is SHORTER than
  the version those cells were healthy under.
* p6 stays lost at 0/6. Nothing in v3 addresses the conditional goal-restatement
  clause that is over-crediting it. If p6 recovers, the volume hypothesis is
  stronger than argued here.
* **Median must reach 18** to be kept: 17 ties v1 and would mean the mirror rule
  is buying p9 and paying for it elsewhere, which is not worth a longer rule.
  Below 17, revert to v1 and stop rewriting this paragraph -- three measured
  attempts would then say the problem is not the wording.


## v3: measured, reverted — and the finding that ends this line of attack

**Q1 median 16/20**, six runs [17,15,17,14,16,16], mean 15.8, artifact
`reasons_rule_v3`. Below v1's 17. Reverted byte-exactly; OLX diff against the
committed v1 state is empty and Q1 re-records 17/20 at prompt `fa105e57b2c0`.

    cell    v1    v2    v3
    p9     3/6   6/6   3/6    the mirror fix did NOT survive compression
    p16    4/6   3/6   1/6    pointer weaker than an inline exclusion list
    p7     6/6   2/6   5/6
    p17    4/6   2/6   3/6
    p14    6/6   6/6   6/6    stable across all three
    p4      -    3/6   5/6
    p11     -    5/6   6/6
    p19    6/6   6/6   5/6

### The two things v3 establishes

**1. The mirror rule needs LENGTH to work.** p9 is 3/6 at v1, 6/6 at v2, and
3/6 again at v3. The concept was identical in v2 and v3; only the scaffolding
differed — v2 carried "a single clause counts ONCE", "never counted again under
the other" and "neither the sentence nor the clause is the unit", while v3
compressed all of it into one sentence. The compressed form does not reach p9.
So the choice is NOT between a good wording and a bad one: stating the mirror rule
strongly enough to fix p9 costs the volume that damages p7, p16 and p17, and
stating it briefly enough to protect them fails to fix p9. That is a genuine
trade-off, and three measured attempts have now priced it.

**2. The pointer costs exclusion strength.** p16 ran 4/6 with v1's inline
exclusion list, 3/6 with v2's, and 1/6 with v3's pointer to "the exclusions
stated in the two counts above". The length v3 bought back was paid for in the
exclusions, on precisely the cells that turn on them. v0's pointer worked for the
COUNTING rule; it does not work for the exclusions.

### What this does NOT license

Concluding that p9 is unfixable. It was 6/6 under v2 — the cell is reachable. What
is unproven is whether it can be reached without dragging the item down.

### The one untried idea, and why it is different

Merge only when both halves name the **SAME OBJECT**. Every mirror pair gold
merges in Q1 has that property (p9 health/health, p3 weight/weight, p17
muscles/muscles, p19 tiredness, p6 body), and every pair gold counts TWICE names
different objects (p13 depression/appetite, p7 sleep/productivity, p11
weight/muscles, p19 tired/unmotivated). The condition is mechanical, so it can be
stated in one clause rather than three — and it is the only form that fixes p9
while explicitly forbidding p7's merge, which is the failure v2 and v3 share.

That is a different idea, not a fourth restatement. But the decision rule agreed
before v3 said to stop rewriting this paragraph after three attempts, so trying
it is a deliberate exception to be taken knowingly, with the inline exclusion list
RESTORED (finding 2) and its cost in length accepted.


# THE GENERALIZATION (five versions measured, all twenty cells)

    cell gold impl   v0    v1    v2    v3    v4
    p1   4    2     6/6   6/6   6/6   6/6   6/6    stable in every version
    p2   4    2     6/6   6/6   6/6   6/6   6/6    stable
    p3   5    3     6/6   6/6   6/6   6/6   6/6    stable (three mirror pairs!)
    p4   5    3     6/6   6/6   3/6   5/6   5/6
    p5   4    2     6/6   5/6   6/6   5/6   6/6
    p6   3    1     4/6   0/6   0/6   0/6   0/6
    p7   5    3     5/6   6/6   2/6   5/6   6/6
    p8   5    3     6/6   6/6   6/6   6/6   6/6    stable
    p9   4    2     1/6   3/6   6/6   3/6   4/6
    p10  4    2     1/6   2/6   1/6   2/6   1/6
    p11  5    3     5/6   5/6   5/6   6/6   6/6
    p12  5    3     6/6   6/6   6/6   6/6   6/6    stable
    p13  5    3     6/6   6/6   6/6   6/6   6/6    stable
    p14  5    3     2/6   6/6   6/6   6/6   6/6
    p15  4    2     6/6   6/6   6/6   6/6   6/6    stable
    p16  3    1     6/6   4/6   3/6   1/6   4/6
    p17  5    3     3/6   4/6   2/6   3/6   3/6    (utb_stated, not counting)
    p18  5    3     5/6   6/6   6/6   6/6   6/6
    p19  5    3     5/6   6/6   6/6   5/6   6/6
    p20  3    3     6/6   6/6   6/6   6/6   6/6    stable

## 1. TWO POPULATIONS PULLING OPPOSITE WAYS

                       gold wants FEWER      gold wants ALL THREE
                       (p6,p16,p10,p9)       (p14,p7,p4)          total
    v0 harms dominate       12/24                 13/18           25/42
    v1 count both            9/24                 18/18           27/42
    v2 distinct content     10/24                 11/18           21/42
    v3 compressed            6/24                 16/18           22/42
    v4 same-object           9/24                 17/18           26/42

Every version trades one group against the other and the total sticks at 25-27.
v0's harms-dominance was the BEST rule for the low-count cells (12/24) and the
worst for the high-count ones; v1 reversed it exactly. That is not a wording
problem. `reasons_given` is ONE NUMBER, so prose can only move the model's
threshold, and the two populations need it moved in opposite directions.

**The structural fix nobody has tried: stop asking for an aggregate.**
`reason_1/2/3` already exist as separate 1-point credit components; `counts=`
collapses them into a single judgement. Asked one at a time, the exclusions would
be applied PER STATEMENT instead of as a threshold on a count. This is the
project's own recorded lesson from Q6 -- "add a NEW required slot rather than
re-describing an existing gate" -- and four prose attempts on this paragraph are
what it costs to ignore it.

## 2. WHY p9 IS 6/6 UNDER v2 AND 4/6 UNDER v4: GRAMMATICAL SCOPE

The two rules quantify over different things.

* v2: "Two ITEMS joined by `and` are TWO when they name different things and ONE
  when they are two ways of saying the same thing."  -> p9 6/6
* v4: "Two STATEMENTS are ONE reason when they name the SAME THING..."  -> p9 4/6

p9 is ONE sentence with a compound predicate: a benefit and the trouble avoided,
joined by `and`, both naming the same object. Those are two ITEMS inside one
STATEMENT, so v4's rule -- quantified over statements -- may not apply at all,
and the model falls back on counting both. The content was never the problem.

Note p3, which carries THREE such pairs and is 6/6 in every version: when a
mirror pair sits in its own sentence the model merges it unprompted. The rule is
only needed for pairs sharing one clause.

## v5 PROPOSAL: widen the quantifier, keep everything else

One phrase swap on the live v4:

    Two mentions are ONE reason when they name the SAME THING, including both
    halves of a single clause, one as a drawback and one as an advantage — and
    TWO when they name DIFFERENT things, even when joined by "and".

600 chars, still under v1's 614. Vocabulary corpus-checked: "mentions",
"halves", "clause", "drawback", "advantage" appear in NO student response;
only "even" and "including" are shared, both function words. (v4's "statements"
was replaced partly for this reason -- "items", "sentence", "whether" and
"inside" all appear in real responses.)

Why it should not repeat v2's damage: v2 lost p7 and p4 through a CROSS-STATEMENT
merge licence ("neither the sentence nor the clause is the unit; three sentences
may hold one"). v5 adds no such licence -- it widens the rule DOWNWARD into a
single clause, and keeps v4's explicit "TWO when they name DIFFERENT things".
p7's sleep/productivity pair names different things and stays two.

Predictions: p9 -> 6/6 (v2 proves this wording reaches it); p7, p14, p4 hold;
p6, p10, p16 unchanged, since nothing here touches the exclusions they fail on.
Median must stay at 17 or better, and cannot exceed 17 while p6, p10 and p17 all
miss -- so this is a p9 fix inside a fixed median, not a median improvement.


# THE STRUCTURAL ATTEMPTS, AND THE ERROR PROFILE THAT SHOULD HAVE COME FIRST

Three further configurations, all reverted:

* **split** — `counts=` removed, `reason_1/2/3` judged individually. Probed well;
  swept **16, 13** and was killed.
* **split + attribute criterion** — "the same attribute predicated of the same
  subject". p9 6/6 and p3 6/6 in an 18-call probe. Swept **median 16**.
* **split + attribute + EXPLICIT exclusions** (v10) — probe p9 6/6, p16 6/6,
  p10 4/6. Swept **median 16**, runs [14,16,15,16,17,16]. In the sweep p9 fell to
  4/6, p16 to 4/6, p10 to 1/6, and p18 dropped 6/6 -> 3/6.
* **v9**, the criterion inside v1's aggregate with no split: p9 **2/6**, worse
  than v1. The criterion needs per-slot judgement to bite.

`COUNTABLE_EXEMPT["Q1","reason"]` was added for the split and REMOVED when the
split was reverted; the audit flagged it stale within one run, which is the check
working as designed.

## PROBES OVER-READ. Three times.

split probe -> sweep, v10 probe -> sweep, and p9 specifically in both. A probe of
3-6 cells consistently reported rates the full sweep did not reproduce, always in
the optimistic direction. **A probe can REFUTE a hypothesis cheaply. It cannot
forecast an item median.** Treat a probe result as a lower bound on the work
remaining, never as a preview of the sweep.

## THE PROFILE THAT REFRAMES THE WHOLE ITEM

Run over the v1 artifact — which existed before any of this work:

    DIRECTION   correct 101 (84%)   over-credit 16 (13%)   under 3 (2%)
                one-sided: a threshold is set wrong, not unstable
    COUNTS      said 3, gold 2  x8      the merge problem
                said 3, gold 1  x6      an EXCLUSION problem
                said 2, gold 1  x2      the same
    DRIFT       confident 15 cells, reasons_given 5 cells

**Sixteen of seventeen count errors are OVER-counts, and eight sit on cells where
gold credits ONE reason.** The exclusion problem is roughly twice the size of the
merge problem, and eleven configurations aimed at merging left it untouched. That
is subgoal 12, and it is where Q1's remaining points are.

This profile is now printed by `measured.py --record` automatically (§2b of
QUALITY_CONTROL.md), because it was available all along and nobody looked.
