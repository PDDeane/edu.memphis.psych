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
