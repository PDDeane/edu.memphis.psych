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

Open questions for whoever does it: where it lives (`agreement.py` beside
`gold_slots_1c`, or its own module both harnesses import); whether the
item-specific phrase-to-slot vocabulary can be derived from each item's slot
labels rather than hand-written per item; and whether `gold_slots_1c` should be
re-expressed in terms of it, which would be the proof that it generalises.
