# Three decisions the work is waiting on

Written 2026-09-20 at the end of the overnight refactor session. The commit log
records what was DONE; this records what is not mine to decide, with the
measurement behind each so the choice can be made without re-deriving it.

---

## 1. Stage 5 — ~~delete `rubric_h1.py` and `rubric_h3.py`?~~ **DONE 2026-09-20, commit 9e603be**

DECIDED: delete. Rehearsed first by moving both modules aside and running the
whole procedure, so the real run had no surprises — every number matched,
including `course.json`'s byte count (561,179). Certified in the deleted state:
72 detected, 0 failed, 0 skipped, 72 of 72, 0 vacuous.

The evidence that mattered was not the pass. All 13 shape-picked targets chose
the SAME items with the modules gone, including four that select by handout 1
and 3 shape — Q6, Q4a, Q1 (three cases) and 1a. Those predicates interrogate h1
and h3 content and answered from the course file. Zero skipped is the other
half: an incomplete migration would have left them finding nothing and
degrading to counted shape-skips.

The question below is kept as it was asked.

**Everything mechanical is done.** No scoring-path module reads the rubric: one
import site remains and it is `check_selectors_govern_something`, which reads
rubric_h2's SOURCE and is retired WITH the modules rather than converted. Both
equivalence gates are EQUIVALENT and their last run is recorded in
`scoring/STAGE5_LICENCE.md`, because after the modules go there is no oracle and
that result cannot be reproduced.

**The measurement that divides the plan's two sentences.** "Stage 5 deletes the
rubric modules" and A1c's "the builders survive" do not conflict:

    rubric_h1.py  2,948 lines  0 builder functions   pure data
    rubric_h3.py    829 lines  0 builder functions   pure data
    rubric_h2.py  1,355 lines  4 builder functions   _example_item, _type_item,
                                                     _definition_item,
                                                     _example_use_item

The data is deleted and the builders survive; all four builders happen to live
in one file.

**Nothing is lost either way, and that took work to become true.** The rubric was
49% comments in h1 and 25% in h3. 1,567 lines written about specific items and
548 of module header prose are now carried in the course file, readable through
`coursedata.rubric_notes(item)` and `handout_notes(h)`. Measured after the
export: ZERO authored comment lines from h1 or h3's ITEMS are unretrievable.
`check_rubric_notes_match_the_modules` keeps the two copies honest and retires
with the modules.

**So the question is only this:** are handout 1 and 3 rubrics acceptable to edit
as JSON, with `rubric_notes()` as the commentary channel? If not, Stage 5 is a
CONVERSION for them rather than a deletion, and the plan's wording needs
amending rather than executing.

---

## 2. ~~Should the certifying self-test reset fixture caches?~~ **YES — DONE 2026-09-20, commit 52301ad**

DECIDED: reset. All six audits the suite takes now clear both caches first, so a
case is compared against a baseline measured the same way. Measured cost: 49s
against 37s warm, +12s per audit versus the 13s the note predicted. The
uninjected baseline is unchanged at 2 findings, exactly as the note said it
would be. `SELFTEST_WARM_FIXTURES=1` restores the old behaviour.

The question below is kept as it was asked.

`agreement._fixture_cached` and `enforcement._fixture_built` are not invalidated
by an injection, so an INJECTED audit's findings depend on what ran in that
process before it. Clearing either adds exactly two findings to the case that
diverges, and they are the two the parallel mode reported.

**What reproduces:** the +2, and which two findings. **What does not:** the
absolute count -- two runs of the same sequence gave 52 -> 54 and 223 -> 225.

**What is NOT affected:** the clean audit. Five alternating cold/warm runs gave
3 findings every time. Nothing recorded against the serial suite is touched by
this; the staleness reaches only the collateral findings of an injected state,
which exist solely inside the self-test.

Resetting before each audit makes the paths agree exactly and costs ~13s per
audit, about fifteen minutes on a full run. Not taken by default: serial is what
every recorded result was measured against, and changing what the certifying run
REPORTS is a larger decision than making it faster.

---

## 3. ~~The staleness check is GREEN AND UNINFORMATIVE~~ **CLOSED 2026-09-20, commits 361e463 + d8b3b5b**

CLOSED TWO WAYS, and the first is the one that mattered: the check now tests
PROVENANCE, not just age — every `.olx` in `OLX_DIR` must appear by name in the
staged output. That made it honest again without rebuilding anything. Then the
dry run grew its own lo-blocks (`npm install` + build) and `paths.LO` learned to
read a `.lo-blocks` marker, so the check now passes because all 23 source files
are staged, `psych_highlight_quizzes.olx` among them.

The record of how the green came to be misleading is kept below, because the
mistake — predicting a false pass for one remedy, refusing it, then producing
the same false pass by another route — is the useful part.

**Read this before trusting `check_no_unresolved_reference_reaches_the_page`.**
It reports 0 findings and that is not evidence of anything.

The check compares MTIMES: the newest `.olx` under `paths.OLX_DIR` against the
newest file under `paths.LO`. In a normal checkout those are one tree. Here they
are not:

    source it measures : refactor_dry_run/edu.memphis.psych/psychology   (dry run)
    artifacts it reads : update/lo-blocks/.stage/content                 (live)
    what the build staged from
                       : /home/pdeane/code/edu.memphis.psych             (live)

On 2026-09-20 the live artifacts were rebuilt from LIVE content. That made them
newer than the dry run's `.olx` files, so the mtime comparison is satisfied and
the check fell silent — while the artifacts do not contain the dry run's content
at all. `.stage/content` holds `psych_bedtime_strategies.*`, which exists only in
the live tree, and lacks `psych_highlight_quizzes.olx`, which exists only in the
dry run and is the newest file — the one that made the check fire in the first
place.

So the green is the mtime heuristic being satisfied, not the artifacts becoming
evidence. I predicted this outcome for one remedy, refused that remedy for it,
and then produced it by another route because I had assumed the check compared
more than dates. It does not.

**What would make it informative again:** rebuild after pointing lo-blocks'
`config/content-sources.local.yaml` at the dry run's content, or merge the dry
run so the two trees are one again. Until then this check says nothing about the
tree it is run from, in either direction.

The two findings it used to report were real and are not fixed; they are hidden.

### PARTLY REPAIRED, same day — the check now tests PROVENANCE as well as age

`check_no_unresolved_reference_reaches_the_page` no longer relies on dates
alone. It now also asks whether the staged output was built from *this* tree:

    every .olx in OLX_DIR must appear by name under .stage/content

ONE DIRECTION ONLY. A staged file this tree lacks is ordinary — the stage
carries demos and other courses, 12 of them here. A file this tree HAS and the
stage lacks means the stage is not about this tree.

With that in place the check reports 1 finding again, naming
`psych_highlight_quizzes.olx`, and says in as many words that the artifact's age
is not evidence. The audit baseline is 2 findings, not 0. **The green described
above is gone; the honest signal is back without a rebuild.**

This does not close the section. The mtime half is still satisfied by any build
from any tree, and the remedies above are still the remedies. What changed is
that the check can no longer be silent about the split while the split exists.

## 4. ~~Owed: a self-test case for the provenance branch~~ **WRITTEN 2026-09-20, commit d8b3b5b**

It could not fail while the headline was firing at baseline; once §3 closed, it
could. Written with its precondition ASSERTED, so if the artifacts ever go
cross-tree again it degrades to a COUNTED skip rather than a silent pass — which
is what the `_shape_skips` counting fix (3cd569d) bought. `SELFTEST_EXPECTED`
71 -> 72, and the suite reports 0 vacuous, so it tests something.

The reasoning for deferring it is kept below.

NOT WRITTEN, deliberately, and this is the reason rather than an oversight.

A case is "detected" when its headline appears in the injected audit. The
provenance finding fires at BASELINE right now, so a case keyed on
`AN UNRESOLVED REFERENCE REACHED THE BUILT PAGE` would report itself detected
without testing anything — the vacuous shape the suite exists to catch, and the
shape that let the neutrality case run empty while the suite printed
`72 of 72 expected`.

The injection itself is known to work; it was measured on 2026-09-20. Writing
one `.olx` into `psychology/` moved the audit 2 findings -> 4, adding all three
arms (provenance, and both mtime arms, since a new source file is newer than the
artifacts). It is a DISK case and would need naming in `_DISK_CASES`.

**Write it when the trees are one again** — after the rebuild or the merge in
§3, when the baseline no longer carries the finding. Then it can fail.

### Found while sizing that: shape skips are not counted

`_shape_skips` entries go into NEITHER `cases` NOR `_conditional_skips`, so a
shape-conditional skip subtracts from `total` and the two-sided ratchet reports
`THE SUITE LOST 1 CASE(S)` — the message for a case someone deleted, not for a
corpus that stopped carrying a shape. The other conditional skips (`plain`,
`_site`) ARE counted, via `skips`, for exactly this reason.

LATENT, not firing: every shape the cases pick is currently present, so the
suite reads 71/71. It would misreport the first time one is not. Read alongside
the comment at the `_conditional_skips` assignment, which sets out the counting
rule this case does not follow.

## 3b. The original note, kept — two stale build artifacts

    .stage/content                        40h older than the newest .olx
    apps/static/public/static-content     52h older

Both are under `/home/pdeane/code/update/lo-blocks`, which the overnight write
scope forbids; `scoring/writescope.sh` refuses the path. They need a content
rebuild there by someone who is allowed to run it. Until then
`check_no_unresolved_reference_reaches_the_page` reports them, and that is the
check working rather than a defect to absorb.

---

## State at the end of the session

171 checks: 169 clean, 2 with findings -- both of them item 3. 0 errored.
Probe: 49 READ, 0 INERT, 0 of 63 registered declaration tables enforce nothing.
Self-test: 71 detected, 0 failed, 0 skipped, 0 vacuous, restored state clean.
Both Stage 5 gates EQUIVALENT.
