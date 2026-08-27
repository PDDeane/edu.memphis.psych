# PLAN — subgoal 8: make the artifact record what the model answered

**Not implemented.** This is a plan, written while a Q1 sweep is in flight, and
nothing here touches a scoring function or a prompt, so none of it can disturb
that run or invalidate a recorded number. Verification is entirely offline: no
model calls at any step.

## What subgoal 8 said, and what is actually true

The subgoal describes two Q1 slots recording `""`. The real picture, measured:

**34 slots across 13 items** carry an answer that `verdict_of()` cannot read.
They split into two very different groups:

* **30 PICK slots — already recoverable, just not from `checks`.** Every
  handout-2 classification (`observed_type`, `named_type`, `trigger_expects`,
  `restricts`, `restriction_authored`, `stimulus_move`, `defines_type`,
  `trigger_behavior`). `checks` shows `""`, but the `answers` field holds the
  value (`observed_type: "NR"`), because `answer_of` reads `refers_to`. Awkward —
  a reader must know to consult a second field — but nothing is lost.
* **4 COUNT slots — genuinely lost.** Q1's `harms_listed` and `benefits_listed`,
  Q2's `reasons_listed` and `reasons_failing`. A count answers neither `verdict`
  nor `refers_to`, so BOTH `checks` and `answers` drop it and only the prose in
  `evidence` survives. These four are the operands of the rule subgoal 6 is
  revising, which is why the whole Q1/p9-p10-p14 diagnosis had to be
  reconstructed from `evidence` fragments.

So the subgoal's scope was understated in count and overstated in severity.

## A third defect, found while scoping this

The per-item scorer fingerprint hashes 9 functions for Q1 and **does not hash
`verdict_of`, `answer_of`, or `is_satisfied`** — all three on the scoring path,
reached from `satisfied_map` and `apply_computed`, which ARE hashed. Hashing a
function does not hash its callees, so editing any of those three changes scores
with nothing flagging a single item stale.

That is the same class of hole as the one closed today (a scorer that parses a
rule and ignores it), and it is directly in this plan's way: the obvious fix for
the count slots is to teach `answer_of` about `count`, and that edit would be
invisible to the guard.

## The plan

### Step 1 — fix the RECORDING site only, never the scoring path

Add a recording-only helper beside `measure_one` and use it in the `checks`
comprehension:

    def recorded_answer(slot, checks):
        """What the model answered, for the ARTIFACT. Not used in scoring."""
        got = checks.get(slot["key"])
        if not isinstance(got, dict):
            return ""
        if slot.get("count_max") and got.get("count") is not None:
            return str(got["count"])
        ...then refers_to, then verdict

Recording a count as its number is what `reasons_given` already does (`"1"`,
`"3"` appear in today's artifacts), so this makes the four missing slots read the
way the counted ones already do rather than inventing a convention.

**Do NOT touch `answer_of`, `verdict_of`, `is_satisfied`, `expand_counted`,
`satisfied_map` or any scorer.** `measure_one` is not hashed by any item's
fingerprint, so this step must leave every `scorer_sha(item)` byte-identical —
which is a checkable claim, not a hope:

    for it in _jobs(): assert scorer_sha(it) == <value recorded before the edit>

If any fingerprint moves, the fix has strayed onto the scoring path and must be
reverted, because 26 items would need ~3000 calls of re-sweeping to recover a
number that did not change.

### Step 2 — a check that fails when the artifact loses an answer

Behavioural, in the shape the audit now uses: build a synthetic sheet answering
EVERY authored slot, run it through the recording path, and assert that no slot
records `""`. Wire it into `enforcement_audit` and the pre-sweep gate.

This is the check that would have caught all three groups at once, and its
absence is why the gap survived a count-recording fix last session: that fix
repaired `expand_counted` for rubric-named counters and nothing asked whether
the OTHER slots recorded anything.

### Step 3 — a selftest injection, since a recording fix cannot prove itself

Revert `recorded_answer` to verdict-only inside the selftest and require the new
check to fire. A recording fix that is never exercised is indistinguishable from
one that does nothing — and unlike a scoring change, it moves no score, so
nothing else in the harness would ever notice its absence.

### Step 4 — close the fingerprint hole, deliberately and at a known cost

Add `verdict_of`, `answer_of` and `is_satisfied` to `_ALWAYS`. This changes every
per-item fingerprint once, with no behaviour change, so re-stamp all 26 entries
with a note saying exactly that — the precedent set earlier today when the
fingerprint went prose-blind. The alternative is leaving three scoring-path
functions unguarded, which is the more expensive choice the first time one of
them is edited.

Do this LAST, so that step 1's "no fingerprint moved" assertion is a real test
rather than one performed against a moving target.

## What is deliberately NOT in scope

Making `checks` complete for the 30 pick slots. It would let a reader stop
consulting two fields, but it changes the recorded semantics of 30 slots on 13
items, and downstream readers (`compare_runs`, `measured.record`, the reporters)
treat `""` as "not answered". That is a separate change with its own regression
risk and no diagnostic urgency, since the values are already in `answers`.
Recommend instead a one-line comment at the recording site naming the asymmetry,
so the next reader does not rediscover it as a bug.

## Cost and order

Steps 1-3 are free: synthetic sheets, no calls, no prompt change, no scoring
change. Step 4 is free in calls but re-stamps the ledger, so it wants its own
commit and a clear message. None of it blocks or is blocked by the Q1 sweep.
