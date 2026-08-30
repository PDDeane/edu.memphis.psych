"""Handout 1 rubric as data: 8 scored items, 45 points.

Sources, in priority order:
  1. "Handout 1 - Scoring & Feedback Dictionary_.docx" — point splits and the
     canonical feedback wording (the dictionary is literally a phrase bank).
  2. The graders' 20 rows in "Handout 1 - Scoring & Feedback.xlsx" — which
     reveal criteria the dictionary never states. Those are marked IMPLICIT
     below; they are the difference between full and zero credit on several
     items, so they are written out explicitly rather than left to inference.

The remaining 5 points of the 50-point handout are for uploading handwritten
photos plus a typed copy. That is a Canvas submission fact, not a property of
the response text, so it is out of scope here and passed through separately.
"""

from __future__ import annotations

# Scoring granularity. The dictionary implies clean increments (1.25 on Q6,
# 1.5 on Q4b), but the graders took off-grid amounts when they judged it fair
# — participant 4 scored 6.0 on Q6 via "-2.5 ... -1.5". So `increment` is
# advisory metadata for reviewers, NOT enforced: enforcing it would overwrite
# scores the gold data shows are legitimate. Scores are clamped to [0, max]
# and rounded to 2dp instead.

ITEMS: list[dict] = [
    {
        "id": "Q1",
        "label": "Question 1",
        "max": 5.0,
        "increment": 1.0,
        "question": (
            "Define your unwanted target behavior (UTB) and explain WHY you chose this "
            "particular UTB for intervention. Requires 1 sentence describing the UTB and "
            "at least 3 sentences explaining why you chose to change this behavior."
        ),
        # Derived, but the three reasons come from ONE count rather than three
        # independent judgements — see `counts` in score.py for the measurement that
        # forced that shape.
        "derive_from_credit": True,
        # Unreachable on purpose: the web's UTB is a closed choice, so an off-list
        # one cannot be submitted, and it was never emitted here either.
        "unreachable_codes": ["UTB_NOT_ON_LIST"],
        "counts": [{"key": "reasons_given",
                    "slots": ["reason_1", "reason_2", "reason_3"]}],
        "credit": [
            {
                "what": "utb_stated",
                "pts": 2.0,
                "verdicts": ["met", "absent", "unclear"],
                # `unclear` no longer charges. It fires on exactly ONE cell in the
                # corpus — p17, 2 of 62 observations across both sides — and gold
                # gives p17 full credit, so charging 2 points for "could not tell"
                # was wrong on the only answer that ever produces it. p20, the cell
                # this check exists to catch, answers `absent` in 11 of 11 runs, so
                # nothing it should catch escapes.
                "codes": {"absent": "UTB_NOT_STATED"},
                # OPEN DECISION. Removing `derived=` made both sides ANSWER this
                # check, but they still see different evidence: the web/agreement.py
                # Q1 prompt carries `REF:bmod_h1_q1_ref_utb`, handing the model the
                # student's SELECTED UTB as context, so "is the UTB stated?" is
                # nearly vacuous there — `met` on p17 in 3/3 CLI and 2/3 web runs.
                # score.py has no such field, judges the prose, and answers `absent`
                # on p17 in 8 of 8 runs. Same words, different evidence.
                #
                # To finish the job the check must be SCOPED — "judge only the
                # response text, not the UTB shown in context above" — which would
                # make all three agree and all three deduct p17, where gold does
                # not. That trades one cell of gold agreement for identical
                # algorithms. Not done unilaterally: it changes what a real student
                # is scored on.
                # BOTH sides now read the PROSE. The web used to derive this from
                # the closed choice (`derived="utb_stated:present:bmod_h1_utb"`),
                # which made the check unfailable there — `met` on 57 of 57
                # cell-runs — while its own screen asks the student to "write one
                # sentence describing your unwanted target behavior". So the web
                # asked for something it never checked, and p20, who skipped that
                # sentence and went straight into effects, kept 2 points there and
                # lost them on paper. That was recorded as a gold divergence, but it
                # was not a judgement disagreement at all: the two sides were
                # scoring different FIELDS for the same criterion. Removed, so the
                # two algorithms are identical here.
                #
                # The cost is symmetric and known: gold applied this rule
                # inconsistently, crediting p17 and deducting p20 on materially
                # identical answers, so any consistent scorer loses one of them.
                # Both now answer `absent` on both, matching gold on p20 and not on
                # p17. That is a CEILING, recorded in handouts.GOLD_CEILINGS, not a
                # divergence — a divergence would imply we chose to disagree.
                "desc": "The unwanted target behavior is identified as the student's "
                        "own target, not merely mentioned as the cause of some effect. "
                        "Judge ONLY the response text the student wrote. Where the UTB "
                        "also appears in this prompt as a separate field or context "
                        "line, that does NOT satisfy this check — the question is "
                        "whether the RESPONSE names the behaviour as its target. "
                        "The test is OWNERSHIP, not first-person pronouns, and "
                        "it can be satisfied anywhere in the response: naming the "
                        "behaviour as theirs (\"My unwanted target behavior is "
                        "X\"), choosing it (\"I chose X\"), or saying what they "
                        "want instead of it. A clause that says only what the "
                        "behaviour DOES TO them — it makes them tired, it leaves "
                        "them behind — is an EFFECT and is not ownership, however "
                        "many times \"me\" appears in it. A response built "
                        "entirely of such clauses is `absent`"
            },
            # Q1 HAS NO GOLD CEILING. It had an entry in handouts.GOLD_CEILINGS
            # claiming `reasons_given` was unwinnable on p6 and p10 "for every model
            # tried"; that entry is gone, because gold's rule turned out to be
            # LOCATABLE and merely conditional — see below — and the scaffold now
            # scores both cells. A `utb_stated` sub-entry went with it: p17/p20 look
            # alike and gold splits them, but gpt-5-mini matches gold on BOTH
            # (reading p17's "I want to be in fit" as claiming the behaviour), so the
            # line is locatable there too and only Opus misses it, answering `absent`
            # on both in 8 of 8 runs. A cell one model misses is a MODEL limit and
            # does not belong in a table about gold's inconsistency.
            #
            # MEASURED, this scaffold (four configurations; --backend lo isolates the
            # model, agreement.py --backend cli isolates the prompt):
            #
            #   paper prompt + Opus        85% -> 90%   MAE 0.25 -> 0.15
            #   paper prompt + gpt-5-mini  75% -> 85%   MAE 0.35 -> 0.15, +/-tol 100%
            #   shipped, CLI (mini)        15.0 -> 15.0 mean, spread 2 -> 4
            #   shipped, web (mini)        15.3 -> 15.7 mean, spread 2 -> 3
            #
            # The CONDITIONAL never misfires: `given` == harms-if-any-else-benefits in
            # 42 of 42 single-cell runs. p6 is right on both models (1/2 -> 1) and p10
            # is right on Opus. Opus's only remaining errors are p9 (benefits counted
            # 3 where gold wants 2) and p17.
            #
            # WHAT TO ATTACK NEXT, if the shipped paths matter more than the paper
            # scorer: the two CLASSIFICATION counts, not the rule. gpt-5-mini executes
            # the conditional but is unstable underneath it — `benefits_listed`
            # flickers 2<->3 on p10 (the goal restatement "my goal for this year is
            # more active" leaking in) and `harms_listed` 2<->3 on p19 (the coordinate
            # "tired and unmotivated" splitting only half the time). That instability
            # is why the shipped means are flat and their spreads grew: the scaffold
            # gives a weaker model two things to get wrong instead of one.
            #
            # TRIED AND REVERTED, so it is not re-run: attacking the same count from
            # the LENIENT side, shipped-side only, by crediting an expected benefit as
            # a reason outright. It fixed p16 (6/6 CLI, 3/3 web) and over-counted
            # every cell wanting 2 — p5 to 9/12, p9 to 4/12, p18 3/3 -> 0/3 — and a
            # BACKGROUND exclusion that fixed p16 did not recover them. Web mean 15.3
            # before, 15.3 after. That was one tier applied uniformly, which is the
            # thing this scaffold replaces. Beware small samples throughout: 6-run
            # measurements here read as +1.3 cells where 12-run ones read as zero.
            #
            # STABILISING THE TWO COUNTS — one half kept, one half reverted, both
            # measured at 8 runs per cell.
            #
            # KEPT, on `benefits_listed`: the GETS-versus-DOES test. A benefit is
            # something the student GETS; a statement of what they intend to DO names
            # the goal behaviour and is not a benefit of it. p10 went 2/6 -> 8/8 and
            # no control moved. Naming p10's goal restatement as an example was not
            # enough on its own — it was already quoted in the desc and still leaked
            # in on 4 of 6 runs; the general test is what fixed it.
            #
            # REVERTED, on `harms_listed`: a coordinate-scope clause saying two
            # DIFFERENT effects joined by "and" are two while one effect in two
            # settings is one. It fixed p19 outright (3/6 -> 8/8) and cost more than
            # it bought: p6 fell 6/6 -> 4/8 because "my muscles become sore and achy"
            # started splitting, and p5 fell 6/6 -> 1/8 because the clause overrode
            # the knock-on rule on "snacking ... which causes me to gain weight".
            # Net about -0.45 cells. To keep p19 it would have to separate two
            # genuinely different effects from two adjectives for one effect
            # ("tired and unmotivated" = 2, "sore and achy" = 1), which is the same
            # distinctness judgement handouts.GOLD_CEILINGS records as unlocatable on
            # Q2. After the revert p19 still sits at 6/8, better than the 3/6 it
            # started at, so the clause was not what carried it.
            #
            # p6 IS FIXED BUT MARGINAL. Two observations that have to be held
            # together: on isolated single-cell runs after the revert it sits at 4 of
            # 8, `harms_listed` flickering 1<->2 on "my muscles become sore and achy";
            # in the item runs that followed it is not an error on either model. So it
            # lands on the right answer when scored as part of the item, but it is
            # close enough to the boundary that repeated single-cell measurement
            # catches it falling off. Do not read the 4/8 as an open regression — an
            # earlier version of this note called it one, which was too pessimistic —
            # and do not read the item runs as proof it is solid either. p9 is
            # also unstable for a different reason: the model reads "have unwanted
            # complications to have to with my health" as a harm, so harms_listed is 1
            # and tier one applies, giving 1 where gold wants 2. Its text is garbled
            # enough that the reading is defensible.
            #
            # TWO-TIER SCAFFOLD. Gold's rule for this count is CONDITIONAL, which is
            # why no prompt wording ever found it: reasons are HARMS of the unwanted
            # behaviour, but where a response offers none at all the graders fall
            # back to crediting the student's stated benefits, and gold never
            # returns 0 anywhere in the corpus. Classifying every cell with gold < 3
            # confirms it: p1/p2/p5/p15 have 2 harms and score 2; p6 has exactly one
            # harm among four background statements and two goal-benefits and scores
            # 1; p9/p10 have no harms and 2 benefits each and score 2; p16 has none
            # and one benefit and scores 1; p19's harms alone reach 3.
            #
            # Every model tried applies ONE tier uniformly and so misses both ends —
            # lenient on p6 (counts a benefit alongside the harm, 2 for 1) and strict
            # on p10 (rejects all three benefits, 0 for 2). p6 and p10 are wrong on
            # both prompts and both models, four configurations agreeing.
            #
            # So the two classifications are asked separately and the conditional is
            # stated where the count is made. Same shape as Q2's reasons_listed /
            # reasons_failing scaffold, whose arithmetic held on 120 of 120 cell-runs
            # — which is why this is not worth teaching a new derived primitive to
            # seven consumers.
            {
                "what": "harms_listed",
                "reported": True,
                "verdicts": ["3", "2", "1", "0"],
                "desc": "HOW MANY statements name a NEGATIVE EFFECT of the unwanted "
                        "behaviour — something that goes wrong because of it, or a "
                        "symptom of it. A single statement tying the behaviour to one "
                        "thing that goes wrong — the behaviour, then what it costs "
                        "them — is one. A reason is a whole STATEMENT: a "
                        "clause that merely continues one is part of it, so a named "
                        "effect followed by \"which causes\" and its downstream result "
                        "is ONE, while two effects merely joined by "
                        "\"and\" are two. A statement naming what the behaviour "
                        "EXPOSES the student to — a susceptibility it worsens — is a "
                        "negative effect even when written as what the goal "
                        "behaviour would protect against. A clause carried along "
                        "within a statement of what the student expects to GET from "
                        "changing belongs to that statement and is not a negative "
                        "effect of its own, however unwanted the thing it names. "
                        "Do NOT count a restatement that the student "
                        "struggles with the behaviour, and do not count a behaviour "
                        "performed DURING it. Answer 3 for three or more",
            },
            {
                "what": "benefits_listed",
                "reported": True,
                "verdicts": ["3", "2", "1", "0"],
                "desc": "HOW MANY statements name a BENEFIT the student expects from "
                        "changing. The test is GETS versus DOES: a benefit is "
                        "something the student GETS — a state, a feeling, a "
                        "capacity they expect to have once the change has "
                        "taken hold. A statement of what they intend to DO names the "
                        "goal behaviour itself and is NOT a benefit of it, however "
                        "much it sounds like a wish. Do NOT count a restatement of the goal, "
                        "a remark about how hard the behaviour has been to "
                        "change, or background explaining how it came about. "
                        "Answer 3 for three or more",
            },
            {
                "what": "reasons_given",
                "reported": True,
                "verdicts": ["3", "2", "1", "0"],
                # The thematic generosity is RIGHT here and is kept: gold really
                # does count "makes me tired" / "makes me grumpy" / "it shows
                # through my emotions" as three. What was missing is the
                # STRUCTURAL boundary — p5 was counted 3 by splitting one sentence
                # at its `which`: "makes me turn to snacking on unhealthy things,
                # like candy" + "which causes me to gain weight". Gold counts that
                # sentence once, so p5 is 2. Same shape as Q2 p19; see the
                # knock-on rule on Q2's `reasons_given`.
                # WAS a harms-dominate conditional: "if `harms_listed` is 1 or
                # more the answer IS `harms_listed`, and benefits do not add to
                # it". Measured wrong against gold on Q1/p9 and Q1/p14, where the
                # shortfall was exactly the benefits it discarded -- on p9 the
                # model obeyed the old rule to the letter and scored 1 where gold
                # counts 2. The larger defect was that the score DEPENDED on the
                # harm/benefit split, which the model cannot make reliably: p14
                # flipped purely on which counter one sentence landed in, and on
                # p10 benefit text was filed under `harms_listed` in 4 of 6 runs.
                # Counting statements towards one total makes the number invariant
                # to that split. See drafts/q1q2_reasons_rule.md for the evidence,
                # the per-cell predictions, and why this cannot be computed
                # arithmetic (a sum over the two counters scores p9 3 against
                # gold 2, because one clause is counted under both headings).
                # TWO-TIER CONDITIONAL, RESTORED. The flat "count both kinds towards
                # one total" that replaced it was measured over eleven
                # configurations and never beat this item's 17/20, while costing
                # p6 (4/6 -> 0/6) and p16. The comment above records why the
                # conditional is right: gold credits HARMS of the unwanted
                # behaviour, and falls back to stated benefits only where a
                # response offers no harms at all. Deleting it was the error.
                # The remaining failures are CLASSIFICATION, not arithmetic:
                # p9 is correct in exactly the runs where harms_listed reads 0
                # ("unwanted complications to have to with my health" is not a
                # harm gold sees), and p14 needs the heart-disease clause read AS
                # a harm to reach three.
                "desc": "HOW MANY reasons count. The rule is CONDITIONAL on the two "
                        "counts above. If `harms_listed` is 1 or more the answer IS "
                        "`harms_listed`, and benefits do not add to it — a response with "
                        "one harm and two benefits counts 1. Only when `harms_listed` "
                        "is 0 does the answer become `benefits_listed` instead. "
                        "Never answer 0 when the student offered anything "
                        "of either kind. Answer 3 for three or more",
            },
            {"what": "reason_1", "pts": 1.0, "codes": {"absent": "REASON_MISSING"},
             # Matches the authored slot label in bmod_handout1.olx. It said
             # "First reason for choosing it" while the web's label said what a
             # reason has to BE; the two systems were describing the same credit
             # component differently, which equivalence.py counted as a gap.
             # Aligned on the web's wording because it is the more specific of
             # the two: "a negative effect" is the rule REASON_MISSING enforces.
             "desc": "First reason — a negative effect of the behavior"},
            {"what": "reason_2", "pts": 1.0, "codes": {"absent": "REASON_MISSING"},
             "desc": "Second reason"},
            {"what": "reason_3", "pts": 1.0, "codes": {"absent": "REASON_MISSING"},
             "desc": "Third reason"},
        ],
        "deductions": [
            {
                "code": "UTB_NOT_ON_LIST",
                "pts": 5.0,
                "text": (
                    "You did not choose an UTB from the provided list (lack of sleep, lack "
                    "of exercise, insufficient consumption of fruits and vegetables, spending "
                    "too much time on electronics). Please choose one of these behaviors for "
                    "you to modify."
                ),
            },
            {
                "code": "UTB_NOT_STATED",
                "pts": 2.0,
                "text": "What is your UTB? This needs to be explicitly stated.",
            },
            {
                "code": "REASON_MISSING",
                "pts": 1.0,
                "text": (
                    "You did not provide 3 separate reasons as to why you chose to change "
                    "this UTB. These should be negative consequences of engaging in the UTB."
                ),
                "repeatable": True,
            },
        ],
        # Slot-specific rules do NOT live here: this list is read before every
        # slot, so anything in it colours all of them. The UTB_NOT_STATED,
        # COUNTING-reasons and JUDGING-reasons bullets moved into the `desc` of
        # the slots they govern, which is also where the verdict is committed.
        # Leaving them here is what let a scoping clause added for `utb_stated`
        # drift the reasons count on cells it had nothing to do with.
        "guidance": [
            "The UTB must be one of the four from the closed list.",
        ],
        "context": [],
    },
    {
        "id": "Q2",
        "label": "Question 2",
        "max": 5.0,
        "increment": 1.0,
        "question": (
            "Define your wanted goal behavior (WGB) that you hope to strengthen. Requires 1 "
            "sentence describing the WGB and at least 3 sentences explaining why you chose "
            "to strengthen it."
        ),
        # Derived, not model-authored: one slot, one deduction.
        # The gate mirrors the web's `wgb_is_counterpart`. Unlike Q1's, this
        # whole-item code IS live: it was emitted once and gold puts two
        # rows at 0 on Q2, so a path to zero has to exist.
        "derive_from_credit": True,
        # Q1's shape exactly — three interchangeable reasons behind one code — so
        # counted the same way. It was not, for as long as it took someone to ask
        # whether the primitives were applied evenly; `check_countable_families_
        # converted` now fails the audit rather than waiting for the question.
        "counts": [{"key": "reasons_given",
                    "slots": ["reason_1", "reason_2", "reason_3"]}],
        "credit": [
            {
                "what": "wgb_is_counterpart",
                "gates": True,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "WGB_UNRELATED", "unclear": "WGB_UNRELATED"},
                # The rubric's THREE tiers, and this gate is only the third. A goal
                # in the right territory that merely fails to invert the behaviour is
                # WGB_NOT_OPPOSITE on `wgb_inverts_utb` (-2), NOT this. Written as tier (a)
                # first — "is the direct positive counterpart" — it zeroed p10 (gold 3)
                # and p18 (gold 4) while correctly zeroing only p17.
                "desc": "The goal behaviour concerns the SAME behaviour as the Q1 UTB. "
                        "Fail this ONLY when it is a different behaviour altogether: the "
                        "goal names activities the student will take up instead, and "
                        "never says to do less of the behaviour the UTB names. "
                        "A goal in the right territory that simply "
                        "does not invert the behaviour still passes this: that is "
                        "WGB_NOT_OPPOSITE on `wgb_inverts_utb`, worth 2, not the whole item. "
                        "When this DOES fail the goal is unstated and its reasons cannot "
                        "count either, so WGB_UNRELATED stands INSTEAD of "
                        "WGB_NOT_OPPOSITE plus reason deductions, never alongside them. "
                        "Where it fires it costs the whole item",
                            # MIGRATED from olx_prompts.SLOT_NOTES 2026-08-29 (E11), verbatim.
                # ITS HISTORY, carried over from the note it replaced rather than
                # lost with it: the note once read "is it the direct positive
                # counterpart, or a different behavior altogether?" -- the tier (a)
                # question, which is NOT what this gate tests. The desc was rewritten
                # to tier (c) after it zeroed p10 and p18; the note was missed, so the
                # web prompt carried BOTH framings while the CLI carried one. A
                # web-only note contradicting the shared desc is the worst shape a
                # deviation can take, and moving it here is what makes that
                # impossible: one string, rendered by both generators.
                "rule": "the WGB_UNRELATED test, and only that: is the goal behavior about "
                         "a DIFFERENT behavior altogether from the unwanted one? A goal in "
                         "the right territory that simply fails to invert the behavior still "
                         "satisfies this — that is WGB_NOT_OPPOSITE on `wgb_inverts_utb`, "
                         "worth 2, not the whole item. Not satisfied means the whole item is "
                         "that finding",
},
            {
                "what": "wgb_inverts_utb",
                "pts": 2.0,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "WGB_NOT_OPPOSITE", "unclear": "WGB_NOT_OPPOSITE"},
                # Was "WGB explicitly stated", which asked a DIFFERENT question
                # from the one this slot charges. It charges WGB_NOT_OPPOSITE —
                # tier (b) — but every answer states some goal, so it returned
                # `met` on 20 of 20 cells on both implementations and tier (b)
                # could never fire. Gold deducts for it on three. The deduction's
                # own text covers both halves ("What is your WGB? This needs to be
                # explicitly stated. Your WGB should be the opposite..."), so the
                # description now covers both too, with the reachable half named.
                # DO NOT add the shipped prompt's "instead of" clause here. That
                # clause exists because the .olx reaches p7 through THIS slot: its
                # gate note asks only "a DIFFERENT behavior altogether?" with no
                # worked example, so the gate passes and `wgb_inverts_utb` has to
                # catch "reading books INSTEAD OF spending hours on games".
                #
                # This path reaches the same answer by the OTHER route. The gate
                # above names p7's text as its own worked example, so the gate
                # fires and short-circuits: measured 8 of 8 runs, score 0.00,
                # `wgb_inverts_utb` never even asked. Both implementations are
                # right on p7 and stable; they are not required to fire the same
                # slot, only to reach gold.
                #
                # So there is nothing to gain here and something to lose: on the
                # shipped side the first draft of that clause carried a general
                # cue ("judge what the goal asks the student to do") which bled
                # two slots away and pushed the reasons count stricter — p20 went
                # 3,2,3 -> 2,2,2, item mean 18.3 -> 17.3. Adding prose to a path
                # for a cell it already gets 8/8 is risk with no measurable payoff.
                #
                # The four cells that turn on this, with gold's verdict on each,
                # because the boundary is not derivable from the words alone. The
                # UTB is a ChoiceInput of four fixed values, so what the UTB names
                # is KNOWN — the only judgement is what the goal names.
                #   p7  screen time -> "connect with people, read books"  ABSENT
                #   p10 lack of exercise -> "gain a consistent routine"   ABSENT
                #   p17 lack of exercise -> "loose twenty pounds"         ABSENT
                #   p18 lack of exercise -> "get back in shape"           MET
                # p18 is why "an outcome or state never counts" is too strict: a
                # state in the SAME behaviour as the UTB is the inversion, stated
                # as a state. p17 fails because pounds are a different measure.
                "desc": "The WGB is explicitly stated AND inverts the behaviour the "
                        "UTB names — not merely a goal in the same territory, and "
                        "not an outcome of the behaviour. Judge the BEHAVIOUR it "
                        "concerns against the behaviour the UTB names: a goal that "
                        "names a different activity fails (reading and socialising "
                        "against a UTB of screen time), and so does one that names a "
                        "different measure — an outcome the behaviour is meant to "
                        "produce, counted in units the behaviour is not. A goal "
                        "stating the same behaviour's positive STATE PASSES: the "
                        "condition of having done it is the inversion, phrased as "
                        "a state. Full credit is the same behaviour turned "
                        "around — the UTB names a behaviour there is too much or "
                        "too little of, and the goal says to do that same "
                        "behaviour less, or more. What FAILS is a goal naming "
                        "something the student would acquire rather than the "
                        "behaviour itself — a habit, a routine, a discipline — "
                        "because it never says to do the goal behaviour more",
                            # MIGRATED from olx_prompts.SLOT_NOTES 2026-08-29 (E11), verbatim -- the web checklist looks up `rule` first, so its prompt does not move.
                "rule": "TWO ways to fail, and the second is the common one. (i) no goal "
                         "behavior is stated at all. (ii) a goal IS stated but does not "
                         "invert the behaviour the Q1 UTB names — the WGB_NOT_OPPOSITE test. "
                         "Tier (a) full credit needs the SAME behaviour turned around: the "
                         "UTB names a behaviour there is too little or too much of, and the "
                         "goal says to do that same behaviour more, or less. `absent` when "
                         "the goal is in the right territory but never says to do the "
                         "behaviour more or less. Two shapes fail this way. A goal naming a "
                         "general CONDITION or ROUTINE the behaviour would contribute to "
                         "does not say to perform it. A goal naming a DIFFERENT MEASURE — an "
                         "outcome the behaviour is supposed to produce, in units the "
                         "behaviour is not counted in — is not the behaviour either. But the "
                         "same behaviour's own positive STATE is `met`: a goal naming the "
                         "condition of HAVING DONE the behaviour is the inversion phrased as "
                         "a state, and the graders charged nothing for it. So a different "
                         "measure of the right behaviour fails; the right behaviour's state "
                         "passes. A goal naming a DIFFERENT ACTIVITY fails here too — one "
                         "that describes what the student will do INSTEAD never says to do "
                         "less of the behaviour the UTB names. Answer `absent` for that here "
                         "even though the `wgb_is_counterpart` gate above may also catch it; "
                         "do not pass this check assuming the gate will",
},
            # A `reasons_listed` / `reasons_failing` scaffold in front of this
            # count was measured and REVERTED. The idea was sound and the model
            # executed it perfectly: `listed - failing == given` held on 120 of
            # 120 cell-runs across both sides, and it produced the graders' own
            # decomposition on the hard cell (p18: 3 listed, 1 restating the
            # problem, 2 counting). It fixed p19 outright on the CLI, 3/5 wrong
            # to 5/5 right. But the SCORE went nowhere: cli 86.0 -> 89.0% while
            # web 90.0 -> 88.0%, because the scaffold makes the count stricter
            # and the web was already at zero bias. Net across both sides, 88.0
            # -> 88.5%.
            #
            # It also settles the expensive version: a `present - failing`
            # primitive would have to be taught to seven consumers to enforce
            # arithmetic that never failed once, for an effect that nets to zero.
            # RESTORED, with the reason its first measurement looked worthless.
            # The scaffold works: `listed - failing == given` held on 120 of 120
            # cell-runs, it fixed p19 outright (3/5 wrong -> 5/5 right) and it
            # reproduced the graders' own decomposition on p18 — 3 listed, 1
            # restating the problem, 2 counting, which is gold's 2 exactly.
            #
            # It was reverted because "the score went nowhere" (web 90 -> 88%).
            # That measurement could not show the benefit: on p18 the web's 3.00
            # is TWO COMPENSATING ERRORS — the count is 3 where gold wants 2, and
            # `wgb_inverts_utb` is `absent` where gold charges nothing. Getting
            # the count right ALONE moves p18 from 3.00 (error 1) to 2.00 (error
            # 2). Measured over the whole item: fixing this slot alone leaves MAE
            # at 0.235, unchanged, because p18 worsens by exactly what p19
            # improves. Fixing both together is 100% exact, MAE 0.000, n=17.
            #
            # So this slot may not be measured or reverted on its own again. Its
            # partner is `wgb_inverts_utb`; Q2's MAE is provably insensitive to
            # this one in isolation.
            {
                "what": "reasons_listed",
                "reported": True,
                "verdicts": ["3", "2", "1", "0"],
                "desc": "HOW MANY statements the response offers as reasons, before "
                        "judging any of them. Count what is on the page",
            },
            {
                "what": "reasons_failing",
                "reported": True,
                "verdicts": ["0", "1", "2", "3"],
                "desc": "Of those, HOW MANY are not a benefit of the goal behaviour — "
                        "because they restate the UTB's harm, or repeat another one",
                            # MIGRATED from olx_prompts.SLOT_NOTES 2026-08-29 (E11), verbatim -- the web checklist looks up `rule` first, so its prompt does not move.
                "rule": "of those, how many are NOT a benefit of the goal behaviour — "
                         "either because the statement restates the harm of the unwanted "
                         "behaviour rather than naming something the goal gets you, or "
                         "because it repeats another statement already counted. Not scored; "
                         "the second half of the count below",
},
            {
                "what": "reasons_given",
                "reported": True,
                "verdicts": ["3", "2", "1", "0"],
                # The old text said to count "as generously as the guidance says:
                # statements naming a benefit count separately even when
                # thematically related". That instructs the WRONG answer. The
                # handout does print "at least 3 sentences", but gold does not
                # score it that way: on p18 it rejects "sometimes I feel like I'm
                # getting big but that's only because I'm out of shape" as
                # restating the problem and counts 2 of 3. The rule below is read
                # off gold's own comments — p3 states the kind test in as many
                # words, "The reasons listed are why you chose to intervene on
                # your UTB, not reasons why you chose your WGB" — and it
                # reproduces gold on all 6 cells that carry a reasons deduction
                # (p3 0, p6 2, p7 0, p17 0, p18 2, p19 2).
                "desc": "HOW MANY of the listed statements are a real benefit of the "
                        "GOAL behaviour: `reasons_listed` minus `reasons_failing`. "
                        "A statement that restates the harm of the unwanted "
                        "behaviour is not a benefit of the goal — \"not exercising "
                        "makes me feel lazy\" is a reason to drop the UTB, not a "
                        "benefit of exercising. Whether one sentence holds one "
                        "benefit or two is STRUCTURAL: a second half that is a "
                        "knock-on effect of the first is ONE (a benefit, then "
                        "\"WHICH WILL\" and what follows from it), while two "
                        "independent benefits merely joined by \"and\" are TWO (one "
                        "about the body, say, AND one about mood). A restatement of "
                        "the GOAL is not a benefit of "
                        "it either: saying they will become the kind of person who "
                        "does the goal behaviour names the goal again and earns "
                        "nothing. Statements about why the UTB is bad belong to Q1 and "
                        "earn nothing here either — a response whose reasons are all "
                        "of that kind scores 0. Answer 3 for three or more",
                            # MIGRATED from olx_prompts.SLOT_NOTES 2026-08-29 (E11), verbatim -- the web checklist looks up `rule` first, so its prompt does not move.
                "rule": "HOW MANY separate BENEFITS of the goal behaviour — "
                         "`reasons_listed` minus `reasons_failing`, the two counts above. "
                         "Thematic overlap alone does not merge two benefits. Whether one "
                         "sentence holds one benefit or two is STRUCTURAL, not a matter of "
                         "degree. A second half that is a KNOCK-ON EFFECT of the first is "
                         "ONE benefit — a benefit followed by \"which will\" and the further "
                         "good it leads to is one, not two, and counting such a chain as two "
                         "costs a point. Two INDEPENDENT benefits merely joined by \"and\" are "
                         "TWO — one about the body and one about mood, in a single sentence, "
                         "is two benefits and counting it as one costs a point. Three kinds "
                         "of statement do not count at all. (i) A reason the UNWANTED "
                         "behaviour is bad, rather than a benefit of the wanted one. A "
                         "sentence built on the NEGATIVE — what NOT doing the goal behaviour "
                         "costs them — is a reason to stop the UTB however it is phrased, "
                         "and the graders counted such sentences as ZERO benefits, even "
                         "where the same fact stated positively would have counted. (ii) A "
                         "restatement of the goal or of the problem it solves: saying they "
                         "will become the kind of person who does the goal behaviour names "
                         "the goal again, not a benefit of it; so is a remark that "
                         "attributes their present condition to not having done the goal "
                         "behaviour. (iii) A statement that says the same thing as one "
                         "already counted. Answer 3 for three or more that survive all three "
                         "tests",
},
            {"what": "reason_1", "pts": 1.0,
             "codes": {"absent": "REASON_MISSING"},
             "desc": "First reason — a benefit of the goal behaviour"},
            {"what": "reason_2", "pts": 1.0,
             "codes": {"absent": "REASON_MISSING"},
             "desc": "Second reason"},
            {"what": "reason_3", "pts": 1.0,
             "codes": {"absent": "REASON_MISSING"},
             "desc": "Third reason"},
        ],
        "deductions": [
            {
                "code": "WGB_UNRELATED",
                "pts": 5.0,
                "text": (
                    "Your WGB should be the opposite of your UTB. You also need three reasons "
                    "why you chose the WGB."
                ),
            },
            {
                "code": "WGB_NOT_OPPOSITE",
                "pts": 2.0,
                "text": (
                    "What is your WGB? This needs to be explicitly stated. Your WGB should be "
                    "the opposite of your UTB (e.g., UTB = not drinking enough water; "
                    "WGB = drinking more water)."
                ),
            },
            {
                "code": "REASON_MISSING",
                "pts": 1.0,
                "text": (
                    "You did not provide 3 separate reasons as to why you chose to strengthen "
                    "this WGB. These should be the benefits of engaging in the WGB."
                ),
                "repeatable": True,
            },
        ],
        # Empty on purpose: all five bullets were SLOT-SPECIFIC (three WGB
        # tiers plus a reasons rule) and are now in the desc of the slot each
        # governs, which is also where the verdict is committed. On Q1 the same
        # move was worth +2 cells on the paper scorer, 75% -> 85%.
        "guidance": [],
        "context": ["Q1"],
    },
    {
        "id": "Q3",
        "label": "Question 3",
        "max": 5.0,
        "increment": 1.0,
        "question": (
            "Use the SMART goal acronym to further define your WGB. Each aspect must be "
            "discussed AND labeled: Specific, Measurable, Actionable/Action-Oriented, "
            "Realistic, Time-Bound."
        ),
        # Derived, not model-authored: one slot, one deduction.
        # Q3 has no whole-item code: five independent letters, so a blank answer loses all five one at a time.
        "derive_from_credit": True,
        "credit": [
            {
                "what": "specific",
                "pts": 1.0,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "SPECIFIC_NOT_QUANTIFIED", "unclear": "SPECIFIC_NOT_QUANTIFIED"},
                "desc": "Names a specific target, quantified",
            },
            {
                "what": "measurable",
                "pts": 1.0,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "MEASURABLE_NO_METHOD", "unclear": "MEASURABLE_NO_METHOD"},
                "desc": "Says how it will be measured",
            },
            {
                "what": "action_oriented",
                "pts": 1.0,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "ACTION_MISSING", "unclear": "ACTION_MISSING"},
                # IMPLICIT (from gold). "States the action to be taken" on its own
                # left this slot nearly inverted — refused on two cells gold
                # credits and credited on the one gold charges. Gold's own test is
                # in its comment: "what do you have to actively do to achieve your
                # goal?" It accepts an enabling CIRCUMSTANCE as readily as an
                # activity, and refuses a response that grounds actionability in
                # another SMART letter instead of in any doing.
                # NARROWED, from all twenty rows rather than the three misses.
                # Gold credits an ACTIVITY or ACCESS TO A PLACE OR THING, and
                # never available time on its own: p9 (a car), p14 (a gym near
                # the house), p18 (access to the university gym) all keep the
                # point, while p8 and p16 -- whose whole justification is hours
                # they have or can make -- lose it, as do p19 (grounds it in
                # measurability) and p20 (a bare capability, methods admittedly
                # absent). "or time they already have" was crediting exactly the
                # two the graders docked.
                "desc": "Names something the student will DO, or a concrete "
                        "circumstance that lets them do it — an activity "
                        "— a step they will physically carry out, at a stated "
                        "time or not — or access to a PLACE or EQUIPMENT that "
                        "lets them do it. Be generous about the doing: a plain "
                        "statement of what they will physically perform counts, "
                        "and so does naming somewhere they can go or something "
                        "they can use. TIME ALONE IS NOT ENOUGH, and this is "
                        "where the graders drew the line: hours they could "
                        "give to it, or expect to clear, name neither a doing "
                        "nor any means of doing it. An answer that leans entirely on "
                        "how much of the week it could occupy loses this point; "
                        "an answer naming somewhere to go or something to use "
                        "keeps it, whatever it says about hours. A bare capability with no activity and no "
                        "place or equipment named fails for the same reason. "
                        "What FAILS is a response that "
                        "justifies actionability by pointing at another letter of "
                        "SMART instead of at any doing — and "
                        "names no doing of its own, or that only re-labels the "
                        "goal as actionable without saying what is done",
            },
            {
                "what": "realistic",
                "pts": 1.0,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "REALISTIC_MISSING", "unclear": "REALISTIC_MISSING"},
                "desc": "Is realistic, or says why it is",
            },
            {
                "what": "time_bound",
                "pts": 1.0,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "TIME_BOUND_WRONG", "unclear": "TIME_BOUND_WRONG"},
                # IMPLICIT (from gold). The guidance's "near-verbatim expected
                # answer" was read as requiring the canonical phrasing, and cost
                # the point on a response that gave the split in the REVERSE order
                # and on one that gave the total with no split at all — both of
                # which gold credits. The only duration gold charges is one that
                # does not total four weeks.
                "desc": "FOUR WEEKS TOTAL is the test. One week of baseline and "
                        "three of intervention is how most students phrase it, "
                        "and any wording that comes to four weeks satisfies this "
                        "check — the two halves in either order, or a bare \"four "
                        "weeks\" with no split named. A duration that does not "
                        "total four weeks loses the point, whatever else it says",
            },
        ],
        "deductions": [
            {
                "code": "SPECIFIC_NOT_QUANTIFIED",
                "pts": 1.0,
                "text": (
                    "-1 pt: For specific, you should have a specific, quantifiable goal. "
                    "(ex. 30 minutes a day)."
                ),
            },
            {
                "code": "MEASURABLE_NO_METHOD",
                "pts": 1.0,
                "text": (
                    "-1 pt: For measurable, how are you tracking your goal? (ex. in a notebook)."
                ),
            },
            {
                "code": "ACTION_MISSING",
                "pts": 1.0,
                "text": (
                    "-1 pt: For action, what do you have to actively do to achieve your goal?"
                ),
            },
            {"code": "REALISTIC_MISSING", "pts": 1.0, "text": "-1 pt: missing realistic."},
            {
                "code": "TIME_BOUND_WRONG",
                "pts": 1.0,
                "text": (
                    "-1 pt: For time-bound, you have one week of baseline data and three weeks "
                    "of intervention, or 4 weeks total."
                ),
            },
        ],
        "guidance": [
            "Award each of the five letters independently, 1 point each.",
            "Time-Bound has a near-verbatim expected answer: four weeks total, one week of "
            "baseline data collection and three weeks of intervention data collection. Any "
            "other duration loses the point.",
            "IMPLICIT (from gold): Measurable must name a tracking METHOD or LOCATION (a "
            "notebook, a phone app). Restating the goal is not measuring it. Specific must "
            "carry a NUMBER.",
        ],
        "context": ["Q1", "Q2"],
    },
    {
        "id": "Q4a",
        "label": "Question 4a",
        "max": 5.0,
        "increment": 1.0,
        "question": (
            "What are the ANTECEDENTS (triggers) for your engagement in your UTB? List and "
            "describe two examples. You must use the word antecedent or trigger."
        ),
        # Derived, not model-authored: one slot, one deduction.
        # A_NONE becomes unreachable, matching the web: it was never emitted and
        # no gold row sits at 0 on Q4a. Listing nothing costs both slots, 4 of 5.
        "derive_from_credit": True,
        # Unreachable on purpose: listing nothing costs both antecedent slots, and
        # A_NONE was never emitted across the cohort.
        "unreachable_codes": [],
        # Declared on BOTH sides, like `counts` and `equals`: the OLX carries
        # the attribute for the web, this carries it for score.py. Without it
        # the CLI ASKED the model "were no antecedents listed?" -- a
        # question answerable from two verdicts the model has already given,
        # so it cost a judgement and invited the model to contradict itself.
        "forbid": [{"key": "no_antecedents",
                    "conds": [{"slot": "antecedent_1", "value": "absent"},
                              {"slot": "antecedent_2", "value": "absent"}]}],
        "credit": [
            {
                "what": "antecedent_1",
                "pts": 2.0,
                "verdicts": ["met", "absent", "not_antecedent"],
                "codes": {"absent": "A_ONLY_ONE", "not_antecedent": "A_NOT_ANTECEDENT"},
                "desc": "First valid antecedent",
            },
            {
                "what": "antecedent_2",
                "pts": 2.0,
                "verdicts": ["met", "absent", "not_antecedent"],
                "codes": {"absent": "A_ONLY_ONE", "not_antecedent": "A_NOT_ANTECEDENT"},
                "desc": "Second valid antecedent",
            },
            # MEASURED at six runs, and left charging. Dropping the point takes p9
            # (0/6 -> 5/6) and p15 (0/6 -> 6/6) to gold exactly and costs p2
            # (6/6 -> 4/6), median 16.0 -> 17.5. It also removes 4.0 from the
            # item's ATTAINABLE set, and p17's gold IS 4.0, so the
            # unreachable-gold allowance in scores_as_exact would forgive our 5
            # there -- turning a real one-point disagreement into a silent pass,
            # on an allowance whose docstring says it is "deliberately not a
            # tolerance". The unreachability would be ours, not the rubric's.
            # THE SPLIT WAS INVESTIGATED AND IS NOT ATTRIBUTABLE. Three rows omit
            # the word: p9, p15, p17. p15 and p17 are the SAME case structurally
            # -- two antecedents gold accepted, no keyword, nothing else at
            # fault -- and gold charged p17 while waiving p15. p9's -2 is for
            # its second example, not the keyword. Neither writing quality nor
            # "was anything else deducted" separates them (p15 drew the clarity
            # comment and no charge; p17 is the roughest written and drew the
            # charge). The gold rows carry only `score` and `feedback`, with no
            # rater identity, so different-grader cannot be shown either way.
            # The one textual difference that does separate all three is that
            # the waived rows state the relation with a causal VERB ("makes me",
            # "causing me to") and p17 uses only "so" -- a rule on that could
            # only ever be validated on the three cells that generated it, which
            # is corpus-fitting, so it is refused. Charging stands: it follows
            # the written dictionary and takes the hit on two rows.
            {
                "what": "keyword",
                "pts": None,
                "reported": True,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "A_NO_KEYWORD", "unclear": "A_NO_KEYWORD"},
                "desc": "Uses 'antecedent' or 'trigger' at least once. A_NO_KEYWORD applies whenever neither \"antecedent\" nor \"trigger\" appears anywhere in the response. The graders enforced this inconsistently — one row lost the point and two others kept it — but the dictionary is explicit, so apply it. This is a deliberate divergence from the rows that kept it.",
            },
            {
                "what": "no_antecedents",
                "gates": True,
                "codes": {"absent": "A_NONE"},
                "pts": None,
                # Computed by `forbid`, so the model is never asked it: the check
                # FAILS exactly when both entries are `absent`, which is what
                # A_NONE names -- nothing listed at all. That is DISTINCT from
                # entries written but of the wrong kind, which the -2 codes charge:
                # Q4a/p20 is wrong_kind twice, gold 1, and is untouched by this.
                # Measured before wiring: NO cell in the corpus has both entries
                # `absent`, across 180 observations, so no recorded score moves.
                # It exists because gold's dictionary specifies the code and the
                # item could not otherwise reach 0.
                "desc": "No antecedents were listed at all",
            },
        ],
        "deductions": [
            {"code": "A_NONE", "pts": 5.0, "text": "No antecedents listed."},
            {"code": "A_ONLY_ONE", "pts": 2.0, "text": "Only one antecedent listed."},
            {
                "code": "A_NOT_ANTECEDENT",
                "pts": 2.0,
                "text": (
                    "These examples are not antecedents. An antecedent/trigger is something "
                    "that causes you to engage in the UTB."
                ),
                "repeatable": True,
            },
            {
                "code": "A_NO_KEYWORD",
                "pts": 0.0,
                "text": 'Did not use the word "antecedent" or "trigger".',
            },
        ],
        "guidance": [
            "An antecedent happens BEFORE the UTB and plausibly leads to it.",
            "ACCEPT generously when the example precedes the UTB and a reader can see how "
            "it leads there. A circumstance or a state of mind qualifies as readily as an "
            "event — a mood, a belief about the behaviour, an unstructured stretch of "
            "time, an interruption from someone else. Do not demand an elaborate causal "
            "chain; plausible precedence is enough. But PRECEDENCE IS THE TEST, and it "
            "depends on which UTB the example is offered for: the same words can be a "
            "trigger for one behaviour and an aftermath of another, so check the direction "
            "against the student's own UTB before crediting.",
            "REJECT decisively in three cases. (a) The example is an AFTERMATH of the UTB "
            "— phrased as happening afterwards or as its result, such as a pain or a "
            "difficulty the behaviour left behind. "
            "(b) The example is what the student does INSTEAD of the goal behaviour, which "
            "belongs to 4b — a substitute activity, or a different way of pursuing the same "
            "end. (c) The example is a consequence already listed in 4c.",
            # MEASURED AND REVERTED: EQUIVALENCE_DEF imported here as
            # MATCH_DEF["Q4a"], on the reading that "does this lead to the UTB?"
            # is a matching question -- gold's own rejections all turn on it
            # (p3 "how not eating is an antecedent of lack of exercise", p4 "how
            # does grumpy emotions lead to lack of sleep", p20 "something that
            # CAUSES you to engage in the UTB"). The clause said the stated
            # effect must BE the UTB, with things that merely cause, accompany,
            # amount to or evidence it excluded as a second thing. Six runs over
            # seven cells: p14's `antecedent_1` stayed `met` 6/6 -- "so I tend to
            # bed rot" still reads as leading to lack of exercise -- so the
            # target never moved. And p9's `antecedent_2` flipped from
            # `wrong_kind` to `met` 5/6, costing 0.67 cells: its example NAMES
            # the behaviour ("Not going on a run..."), which is exactly why it
            # is not an antecedent, and a clause requiring the effect to BE the
            # UTB reads as licence for an example that names the UTB outright.
            # Five guards (p3, p4, p15, p18, p20) were untouched, so the
            # definition transfers without collateral damage -- it simply does
            # not bite on this slot, and its wording backfires where the example
            # is the destination. Net -0.67. Do not re-import without solving
            # the names-the-destination case first.
            "Where the link is genuinely opaque rather than merely brief, the graders did "
            "deduct. The test they applied was whether a reader can see how this leads to "
            "THIS behaviour: a mood or an omission that could precede almost anything is "
            "opaque, and asking \"how does that lead to the UTB?\" of the entry is the "
            "check. Brevity alone is not opacity.",
        ],
        "context": ["Q1"],
    },
    {
        "id": "Q4b",
        "label": "Question 4b",
        "max": 5.0,
        "increment": 0.5,
        "question": (
            "What ARE you actively doing during your unwanted target BEHAVIOR? List and "
            "describe two examples. Additionally, state whether this behavior is a good "
            "choice for you to modify AND why."
        ),
        # Derived, not model-authored: one slot, one deduction.
        #
        # `modify_stated` carries B_NO_MODIFY's full 2 points and `modify_why` is
        # suppressed when it fails, because that code already covers both halves.
        # Two independent 1-point slots would charge the same 2 under two codes,
        # neither at the value the graders' phrase bank gives it.
        "derive_from_credit": True,
        # Unreachable on purpose, as A_NONE on Q4a.
        "unreachable_codes": ["B_NONE"],
        # No `unclear` on the two modify slots. "Does the response say whether this
        # is a good choice?" is a presence question, and once `modify_stated` carries
        # B_NO_MODIFY's full 2 points a hedge there costs the whole sub-area: p14 and
        # p17 both went to 3.0 against a gold of 5.0 on `unclear` alone. The sheet's
        # `uncertain` check is where doubt belongs.
        "onlyif": [{"key": "modify_why", "cond": "modify_stated"}],
        "credit": [
            {
                "what": "behavior_1",
                "pts": 1.5,
                "verdicts": ["met", "absent", "wrong_kind"],
                "codes": {"absent": "B_ONLY_ONE", "wrong_kind": "B_NOT_ACTIVE"},
                "desc": "First example of what they do INSTEAD OF the goal behavior",
                # MOVED to `b1_basis`/`b2_basis` on 2026-08-28. This check is
                # COMPUTED by `maps` now, so it is never asked and a rule here
                # would render nowhere. Dead prose in a rubric is how two copies
                # of one judgement start, which is the drift this item was the
                # demonstrated cost of. The five cases are stated once, on the pick.
            },
            {
                "what": "behavior_2",
                "pts": 1.5,
                "verdicts": ["met", "absent", "wrong_kind"],
                "codes": {"absent": "B_ONLY_ONE", "wrong_kind": "B_NOT_ACTIVE"},
                "desc": "Second example of what they do INSTEAD OF the goal behavior",
                # MOVED to `b1_basis`/`b2_basis` on 2026-08-28. This check is
                # COMPUTED by `maps` now, so it is never asked and a rule here
                # would render nowhere. Dead prose in a rubric is how two copies
                # of one judgement start, which is the drift this item was the
                # demonstrated cost of. The five cases are stated once, on the pick.
            },
            # THE TWO PICKS. `behavior_1` and `behavior_2` are no longer asked:
            # `maps` below computes each from its pick, so the composite
            # judgement the two scorers used to weigh separately is now
            # arithmetic and cannot be read differently by each.
            #
            # The prose is MOVED, not rewritten. It is already leakage-reviewed,
            # and rewording a rule while changing its mechanism would leave the
            # sweep unable to say which of the two moved a cell.
            {
                "what": "b1_basis",
                "verdicts": ["activity", "consequence", "goal_behaviour",
                             "not_doing", "none"],
                "desc": "What the first example IS",
                "rule": 'ONE ANSWER, and it says what the entry IS. The engine turns it into this example\'s verdict, so do not judge whether the example earns credit -- classify it and the arithmetic follows.\n  `activity` -- something they did INSTEAD of the goal behaviour. This is the answer that earns the point.\n  `none` -- the box is empty, or names nothing at all.\n  `consequence` -- cases (1) and (3) below.\n  `goal_behaviour` -- case (2) below.\n  `not_doing` -- case (5) below.\nWHERE THE ENTRY OFFERS ALTERNATIVES, case (4): classify by the FAILING alternative, because one qualifying alternative does not rescue the rest.\nThe cases, unchanged: (1) (1) The entry names a CONSEQUENCE of the unwanted behaviour — a state they ended up in, or something they then had to do — rather than something they did INSTEAD of the goal behaviour. (2) The entry IS the goal behaviour, done at the wrong time, in the wrong place, or badly: you cannot do something instead of itself. If the goal is to sleep enough, sleeping in the car is not something done instead of sleeping — it is that sleep, displaced. Keep this apart from a RIVAL choice, which IS a substitute: if the goal is to eat fruit, eating chips counts, because chips are not fruit. The question is whether they did a different thing that crowded the goal out, or the goal itself gone wrong. (3) The entry names an ordinary activity that CARRIES a state the unwanted behaviour produced — an everyday activity reported together with the discomfort or dullness it is being carried out under. The activity is incidental there: they would be doing it anyway, and what the sentence actually reports is the state, which is a consequence. Test it by asking whether the activity would have happened regardless of the goal behaviour. If it would, nothing was displaced and the entry is not a substitute — an activity that is LIKELY A CONSEQUENCE of not doing the goal behaviour cannot also be what replaced it. (4) Where the entry offers ALTERNATIVES — two or more things joined by "or", either of which might be what they did — every alternative must pass the tests above. One qualifying alternative does not rescue the rest: "I am tired in class OR catching up on chores" fails, because being tired is a state the behaviour produced. This applies only to genuine alternatives. A sentence that names an activity AND THEN what came of it is judged on the activity: a snack eaten and the fruit left to spoil is one substitute with its result attached, not two alternatives — and several near-synonyms for the same choice are one substitute described three ways. (5) NAMING A FAILURE TO ACT IS NOT NAMING A SUBSTITUTE. "I procrastinate", "I avoid going", "I neglect it", "I put it off" all describe the goal behaviour NOT happening; they do not say what the student was doing in that time, which is what the question asks. Credit the concrete activity if the entry names one alongside the avoidance, and treat the not-doing as failing the test — including when it is one alternative among several',
            },
            {
                "what": "b2_basis",
                "verdicts": ["activity", "consequence", "goal_behaviour",
                             "not_doing", "none"],
                "desc": "What the second example IS",
                "rule": 'ONE ANSWER, on the same terms as the first example: `activity` for something done INSTEAD of the goal behaviour, `none` for an empty box, and otherwise the case it falls under -- `consequence` for a consequence of the unwanted behaviour or an ordinary activity carrying a state that behaviour produced, `goal_behaviour` for the goal behaviour itself done at the wrong time or place, `not_doing` for a naming of the goal behaviour NOT happening rather than of what they did instead. Where the entry offers ALTERNATIVES, classify by the failing one.',
            },
            {
                "what": "modify_stated",
                "pts": 2.0,
                "verdicts": ["met", "absent"],
                "codes": {"absent": "B_NO_MODIFY"},
                "desc": "States whether modifying this behaviour is a good idea",
            },
            {
                "what": "modify_why",
                "pts": 1.0,
                "verdicts": ["met", "absent"],
                "codes": {"absent": "B_NO_MODIFY_WHY"},
                "desc": "States why it is or is not. B_NO_MODIFY_WHY applies only when the response says it is/isn't a good choice to modify and gives NO reason whatsoever. Any reason, however brief, earns the point — a single clause naming why the behaviour is or is not within their control is enough.",
            },
        ],
        "deductions": [
            {"code": "B_NONE", "pts": 5.0, "text": "No active behaviors listed."},
            {"code": "B_ONLY_ONE", "pts": 1.5, "text": "Only one active behavior listed."},
            {
                "code": "B_NOT_ACTIVE",
                "pts": 1.5,
                "text": (
                    "These examples are not what you’re actively doing during your UTB. "
                    "Think about it like this: what are you doing *instead of* engaging in "
                    "your WGB? (e.g., instead of drinking water, I am drinking soda)."
                ),
                "repeatable": True,
            },
            {
                "code": "B_NO_MODIFY",
                "pts": 2.0,
                "text": "No statement of if the behavior is a good choice to modify and why.",
            },
            {
                "code": "B_NO_MODIFY_WHY",
                "pts": 1.0,
                "text": "Did not say why it is a good choice to modify.",
            },
        ],
        "guidance": [
            "THE TEST IS THE DICTIONARY'S, and it is one question: what is the student "
            "doing INSTEAD OF engaging in their wanted goal behaviour? The dictionary "
            "puts it that way and gives its own example — \"instead of drinking water, I "
            "am drinking soda\". Their goal behaviour is quoted above from question 2; "
            "read each entry against THAT. An entry earns its 1.5 points when it names "
            "something they do in the time the goal behaviour would have taken.",
            "ACCEPT — and accept broadly, once that test is met. Three kinds all earn "
            "full credit. ORDINARY ACTIVITIES that occupied the time: \"I am playing "
            "cards with my roommates\", \"I am reorganising my desk\". INTERNAL "
            "STATES AND THOUGHTS, where the state or the thought is itself what "
            "occupied them instead of the goal behaviour: \"my head keeps telling me "
            "to get up but I cannot make myself move\", \"I lie there wishing I had "
            "started earlier\". These count even though nothing was physically done, "
            "and it does not matter whether the state was chosen or simply arrived — "
            "what matters is that the entry names what filled that time rather than a "
            "consequence of the behaviour. And COPING BEHAVIOURS standing in for the "
            "goal "
            "behaviour, where something is consumed or leaned on to get through the "
            "day the goal behaviour was supposed to serve: \"I lean on energy drinks "
            "to make it to the evening\". Do not judge how insightful "
            "the entry is; judge only whether it is an alternative to the goal "
            "behaviour.",
            "REJECT when the entry is not something the student did INSTEAD OF the "
            "goal behaviour. Two shapes. (a) It is not an example of doing anything at "
            "all — meta-commentary about whether the behaviour is worth modifying, or a "
            "recital of consequences. (b) It names something the unwanted behaviour "
            "CAUSED rather than something that REPLACED the goal behaviour — a state "
            "they ended up in, or something they then had to do. The test is "
            "substitution, not grammar: \"I am yawning through my morning classes\" "
            "names an activity but is what the lost sleep left them with, while \"I am "
            "watching TV\" genuinely replaces the workout. Ask of each entry: could "
            "they have done this INSTEAD of the goal behaviour, or did it happen "
            "BECAUSE they did not? When neither entry is an example, deduct "
            "B_NOT_ACTIVE twice rather than B_ONLY_ONE.",
        ],
        "context": ["Q1", "Q2", "Q4a"],
    },
    {
        "id": "Q4c",
        "label": "Question 4c",
        "max": 5.0,
        "increment": 1.0,
        "question": (
            "What are the CONSEQUENCES of engaging in your UTB? List and describe two "
            "examples. You must use the word consequence(s)."
        ),
        # Derived, not model-authored: one slot, one deduction.
        # C_NONE likewise: never emitted, no gold row at 0 on Q4c.
        "derive_from_credit": True,
        # Unreachable on purpose, as A_NONE on Q4a. C_NO_KEYWORD joins it: the
        # keyword slot no longer maps a verdict to it, so nothing can emit it.
        "unreachable_codes": ["C_NO_KEYWORD"],
        # Declared on BOTH sides, like `counts` and `equals`: the OLX carries
        # the attribute for the web, this carries it for score.py. Without it
        # the CLI ASKED the model "were no consequences listed?" -- a
        # question answerable from two verdicts the model has already given,
        # so it cost a judgement and invited the model to contradict itself.
        "forbid": [{"key": "no_consequences",
                    "conds": [{"slot": "consequence_1", "value": "absent"},
                              {"slot": "consequence_2", "value": "absent"}]}],
        "credit": [
            {
                "what": "consequence_1",
                "pts": 2.0,
                "verdicts": ["met", "absent", "not_consequence", "duplicate"],
                "codes": {"absent": "C_ONLY_ONE", "not_consequence": "C_NOT_CONSEQUENCE", "duplicate": "C_DUPLICATE"},
                "desc": "First valid consequence",
            },
            {
                "what": "consequence_2",
                "pts": 2.0,
                "verdicts": ["met", "absent", "not_consequence", "duplicate"],
                "codes": {"absent": "C_ONLY_ONE", "not_consequence": "C_NOT_CONSEQUENCE", "duplicate": "C_DUPLICATE"},
                "desc": "Second valid consequence",
            },
            {
                # Reported but NOT charged, unlike Q4a's keyword. The slot is
                # kept so the feedback can still mention the omission, which is
                # what the graders did with it: advisory, never a deduction.
                #
                # Measured, not assumed. Across all 20 gold rows there is no
                # Q4c deduction for the missing word — indeed no 1-point
                # deduction of any kind on this item; every one is 2 or 4. The
                # charge cost three cells (p15 and p17 docked at full credit,
                # p13 charged it on top of a correct -2) and recovered none.
                # Q4a WAS the opposite case, keeping its charge because p17's
                # gold row reads `-1 pt: did not use the word "antecedent" or
                # "trigger"`. That is no longer true: A_NO_KEYWORD now costs 0.0,
                # after the charge was measured firing on one row in seven where
                # gold charged nothing, and p17's gold was corrected instead (see
                # handouts.CORRECTED_GOLD). The two items now agree in EFFECT --
                # neither charges for the keyword — by different mechanisms: Q4a's
                # code is reachable and worth nothing, Q4c's is unreachable.
                #
                # REVISITED under the equivalence goal, which asks that a code
                # gold specifies be made reachable rather than declared away. The
                # answer here is unchanged, and the fresh measurement agrees with
                # the one above to the cell: the keyword reads absent or unclear
                # in 12 of 60 recorded observations across p9, p13, p15 and p17,
                # every run, while gold charges a keyword deduction NOWHERE on
                # either item. Reachable-at-zero would be cosmetic; the code stays
                # in `unreachable_codes` with this note as its reason.
                "what": "keyword",
                "pts": None,
                # `reported`, not merely unpointed. pts=None already stops the
                # ledger charging it, but build_prompt formats `pts` for any slot
                # that is neither a gate nor reported, so the missing flag made
                # `score.py --handout 1` (no --items) die with "unsupported format
                # string passed to NoneType.__format__" on every participant. It
                # went unseen because every run since has used --items on other
                # items; the full-handout sweep is what surfaced it.
                "reported": True,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {},
                "desc": "Uses 'consequence' at least once (advisory, not scored). The word \"consequence\" is NOT worth a point here, unlike the keyword on Q4a. Report `keyword: absent` when it appears nowhere — the feedback may mention it — but it costs nothing. IMPLICIT (from gold): no Q4c row in the corpus deducts for it, and none carries a 1-point deduction at all — rows that omit the word keep full credit. Q4a differs and keeps its charge, because a Q4a row there does deduct for the missing keyword.",
            },
            {
                "what": "no_consequences",
                "gates": True,
                "codes": {"absent": "C_NONE"},
                "pts": None,
                # Computed by `forbid`, so the model is never asked it: the check
                # FAILS exactly when both entries are `absent`, which is what
                # C_NONE names -- nothing listed at all. That is DISTINCT from
                # entries written but of the wrong kind, which the -2 codes charge:
                # Q4a/p20 is wrong_kind twice, gold 1, and is untouched by this.
                # Measured before wiring: NO cell in the corpus has both entries
                # `absent`, across 180 observations, so no recorded score moves.
                # It exists because gold's dictionary specifies the code and the
                # item could not otherwise reach 0.
                "desc": "No consequences were listed at all",
            },
        ],
        "deductions": [
            {"code": "C_NONE", "pts": 5.0, "text": "No consequences listed."},
            {"code": "C_ONLY_ONE", "pts": 2.0, "text": "Only one consequence listed."},
            {
                "code": "C_NOT_CONSEQUENCE",
                "pts": 2.0,
                "text": "These are not consequences of engaging in the UTB.",
                "repeatable": True,
            },
            {
                "code": "C_DUPLICATE",
                "pts": 2.0,
                "text": "Listed the same consequence twice.",
            },
            {
                "code": "C_NO_KEYWORD",
                "pts": 1.0,
                "text": 'Did not use the word "consequence".',
            },
        ],
        "guidance": [
            "A consequence happens AFTER the UTB and results directly from it.",
            "ACCEPT downstream effects of any kind, including behavioural ones. A "
            "consequence may name something the student ends up DOING as a result — "
            "turning to a worse alternative, or falling into a further habit — and that "
            "counts as readily as a state they end up in. Do not reject a consequence "
            "merely because it names an action rather than a state.",
            "REJECT a statement that is really a BENEFIT of the goal behaviour rather than "
            "a result of the UTB. Naming the healthy weight, fitness or wellbeing the "
            "student would have HAD by doing the goal behaviour describes what they "
            "forfeited, not what engaging in the UTB produced, and two such statements "
            "cost a whole item.",
            "DEDUCT when the causal link is left for the reader to guess: a consequence "
            "that is real but whose connection to THIS unwanted behaviour the reader has "
            "to supply. An entry that restates the behaviour in other words, without "
            "saying what it COSTS the student, is the usual shape — the grader's question "
            "there is what the restated phrase actually means for them.",
            "The two consequences must be distinct; listing the same one twice costs the "
            "second.",
        ],
        "context": ["Q1", "Q4a", "Q4b"],
    },
    {
        "id": "Q5",
        "label": "Question 5",
        "max": 5.0,
        "increment": 2.5,
        "question": (
            "Why do you think you continue to engage in the UTB even though it results in "
            "undesired consequences? (To gain something, to escape a task, to receive "
            "attention, or something else.) List and describe two examples."
        ),
        # Derived, not model-authored: one slot, one deduction.
        "derive_from_credit": True,
        "blank_code": "W_NONE",
        "credit": [
            {
                "what": "example_1",
                "pts": 2.5,
                # `duplicate` mirrors Q4c, the same shape of item, which has had
                # met/absent/not_consequence/duplicate all along. Without it the
                # guidance below asks for a state the schema cannot express —
                # "W_ONLY_ONE also covers two statements that collapse into the
                # SAME reason" — and both implementations had to fake it. p6's two
                # entries are both well-formed and both populated, so the CLI
                # answered `absent` (false, but it carries the right penalty) and
                # the web answered `met` (true, and therefore 2.5 over gold).
                # Mapped to W_ONLY_ONE, not a new code: the guidance says that code
                # covers it, and the dictionary has no separate duplicate wording.
                "verdicts": ["met", "absent", "not_reason", "duplicate"],
                "codes": {"absent": "W_ONLY_ONE", "not_reason": "W_NOT_REASON",
                          "duplicate": "W_ONLY_ONE"},
                "desc": "First way the goal behavior is worth strengthening",
            },
            {
                "what": "example_2",
                "pts": 2.5,
                # `duplicate` mirrors Q4c, the same shape of item, which has had
                # met/absent/not_consequence/duplicate all along. Without it the
                # guidance below asks for a state the schema cannot express —
                # "W_ONLY_ONE also covers two statements that collapse into the
                # SAME reason" — and both implementations had to fake it. p6's two
                # entries are both well-formed and both populated, so the CLI
                # answered `absent` (false, but it carries the right penalty) and
                # the web answered `met` (true, and therefore 2.5 over gold).
                # Mapped to W_ONLY_ONE, not a new code: the guidance says that code
                # covers it, and the dictionary has no separate duplicate wording.
                "verdicts": ["met", "absent", "not_reason", "duplicate"],
                "codes": {"absent": "W_ONLY_ONE", "not_reason": "W_NOT_REASON",
                          "duplicate": "W_ONLY_ONE"},
                "desc": "Second way",
},
            {
                # Reported, never scored — the same shape as `avoidance_frame` on
                # the operant-conditioning items.
                #
                # It exists because the guidance below asks for a state the schema
                # could not express. "A THIN REASON IS AN ADVISORY, NOT A
                # DEDUCTION" — but example_1/example_2 offered only met, absent
                # and not_reason, and BOTH non-met options cost 2.5, half the
                # item. A model that judged a reason weak had one place to put
                # that judgement, and it deducted. All three of this item's error
                # cells are that: p9 and p20 lost 2.5 for reasons gold credited
                # with a written note, and p4 lost both where gold refused one.
                #
                # Q5 has no spare point (2.5 + 2.5 = 5 = max), so this cannot be
                # a scored slot even if that were wanted. Unscored is also the
                # right answer on the evidence: the graders left the score at full
                # and wrote a note.
                "what": "reasons_substantial",
                "reported": True,
                "verdicts": ["met", "absent"],
                "desc": "Whether both reasons are substantial — `absent` reports "
                        "a present-but-weak reason so it can be said in the "
                        "feedback, never deducted",
},
        ],
        "deductions": [
            {"code": "W_NONE", "pts": 5.0, "text": "did not answer"},
            {"code": "W_ONLY_ONE", "pts": 2.5, "text": "Only one example listed."},
            {
                "code": "W_NOT_REASON",
                "pts": 2.5,
                "text": (
                    "These are not examples of why you continue to engage in the UTB. It "
                    "should be something like, ‘I continue to not drink enough water "
                    "because soda tastes so good, and I get my sugar fix.’"
                ),
                "repeatable": True,
            },
        ],
        "guidance": [
            "The answer is about FUNCTION — what the student gains, escapes, or gets from "
            "continuing the UTB.",
            "CREDIT ON FORM, NOT ON QUALITY. This is the most forgiving item on the "
            "handout. Any statement shaped like \"I continue to [UTB] because X\" earns its "
            "2.5 points, essentially regardless of how insightful X is. Getting absorbed "
            "in something, not making time, a substance that keeps them up, preferring "
            "an easier way to spend the evening — all of these earn full marks, and so "
            "does any other payoff named however plainly.",
            "A THIN REASON IS AN ADVISORY, NOT A DEDUCTION. When a reason is present but "
            "weak, the graders wrote a note and left the score at full: a second reason "
            "that restates the first, or that gestures at the behaviour without saying "
            "what it does for the student, drew \"explain how this is a reason you are "
            "choosing to [UTB]\" as FEEDBACK on a full score. Put that kind of remark in "
            "advisory_note; do not emit W_NOT_REASON for it.",
            "W_NOT_REASON is for a statement that is not a reason for CONTINUING at all — "
            "most often a consequence wearing a reason's clothes. \"I continue to [UTB] "
            "because it leaves me irritable and worn out\" names an EFFECT of the "
            "behaviour, not a payoff from it, and loses the 2.5 even though its form is "
            "perfect.",
            "THE LINE BETWEEN THIN AND ABSENT. The two rules above overlap, and the example "
            "just given has perfect form, so apply this test per entry and in this order. "
            "Deduct W_NOT_REASON ONLY when the statement (a) names a CONSEQUENCE of the "
            "unwanted behaviour rather than something gained by continuing it, or (b) is "
            "about a DIFFERENT behaviour than the UTB. Everything else that is present — "
            "vague, circular, shallow, clumsily worded, or a reason you find unconvincing — "
            "is THIN: credit it and write an advisory. Vagueness is never a deduction on "
            "this item; only the wrong KIND of statement is.",
            "W_ONLY_ONE also covers two statements that collapse into the SAME reason — "
            "two entries that both amount to escaping the same effort or discomfort are "
            "one reason described twice, and the row reads \"missing a reason you "
            "continue to engage in [the UTB]\".",
            "If the response is empty, this is W_NONE and the feedback is exactly "
            "'did not answer'.",
        ],
        "context": ["Q1", "Q4c"],
    },
        # ------------------------------------------------------------------
    # Q6, REWRITTEN FROM THE DICTIONARY.
    #
    # Everything here traces to "Handout 1 - Scoring & Feedback Dictionary_.docx"
    # or to the question itself. The previous version had accreted three worked
    # student examples, five participant citations, an operational test for the
    # change slots, a lecture on working the slots in order, and a cohort
    # statistic — none of which is in the dictionary, and all of which had to be
    # excluded from the measurement because it quoted the cells being scored.
    # Seven of Q6's twenty cells were unscoreable as a result.
    #
    # The dictionary's own content, in full:
    #   "Stating each antecedent is worth 1.25 points each."
    #   "Stating how each antecedent is being changed is worth 1.25 points each."
    #   "Stating each consequence is worth 1.25 points each."
    #   "Stating how each consequence is being affected is worth 1.25 points each."
    #   plus the four deduction wordings below and the template.
    # So the 8 x 1.25 decomposition was always right; the guidance around it was
    # the part we invented.
    #
    # (The dictionary's header says "(5 points)" while its own four credit lines
    # sum to 10 and every gold row is out of 10. Treated as a typo in the source.)
    #
    # Two earlier experiments are recorded so they are not silently repeated: a
    # FOURTH exemplar (participant 15) measured Q6 62% -> 44%, MAE 0.56 -> 0.80;
    # a fifth and sixth (participants 5 and 17) measured 60% -> 47%, MAE 0.60 ->
    # 0.85. Three was the best of {3,4,5} — but none of those trials tested ZERO,
    # which is what this version is.
    {
        "id": "Q6",
        "label": "Question 6",
        "max": 10.0,
        "increment": 1.25,
        "question": (
            "Describe how you could change each of your two antecedents (from 4a) to get "
            "closer to your WGB. Then include how those changes may impact your "
            "consequences (from 4c)."
        ),
        "derive_from_credit": True,
        "blank_code": "Q6_NONE",
        # The matching requirement, and the only mechanism for it. The dictionary
        # says the antecedents and consequences "must match up" with 4a and 4c,
        # and the question says "each of your TWO antecedents" — so each box
        # reports WHICH of the two listed items it names, and the grader works
        # out from the pair whether both were addressed. Reporting an identity is
        # one question; asking met/absent/mismatch as well was two questions for
        # one fact and admitted contradictions.
        "cover": [
            {"keys": ["state_a1", "state_a2"], "labels": ["first", "second"], "of": "4a",
             "verdicts": ["first", "second", "neither", "absent"]},
            {"keys": ["state_c1", "state_c2"], "labels": ["first", "second"], "of": "4c",
             "verdicts": ["first", "second", "neither", "absent"]},
        ],
        "credit": [
            {
                "what": "state_a1",
                "pts": 1.25,
                "desc": "States the first antecedent being changed, and it matches 4a",
                "codes": {"absent": "A_NOT_STATED", "neither": "A_MISMATCH"},
            },
            {
                "what": "change_a1",
                "pts": 1.25,
                "desc": "States HOW the first antecedent is being changed",
                "codes": {"absent": "A_NO_CHANGE", "not_described": "A_NO_CHANGE"},
            },
            {
                "what": "state_a2",
                "pts": 1.25,
                "desc": "States the second antecedent being changed, and it matches 4a",
                "codes": {"absent": "A_NOT_STATED", "neither": "A_MISMATCH"},
            },
            {
                "what": "change_a2",
                "pts": 1.25,
                "desc": "States HOW the second antecedent is being changed",
                "codes": {"absent": "A_NO_CHANGE", "not_described": "A_NO_CHANGE"},
            },
            {
                "what": "state_c1",
                "pts": 1.25,
                "desc": "States the first consequence being affected, and it matches 4c",
                "codes": {"absent": "C_NOT_STATED", "neither": "C_MISMATCH"},
            },
            {
                "what": "affect_c1",
                "pts": 1.25,
                # The dictionary's wording, restored in full. The desc used to
                # read "Describes HOW the first consequence will be affected" and
                # stopped there, dropping "by changing the antecedent(s)" — the
                # clause that makes this a different question from `state_c1`.
                # Without it the check did not discriminate: across the cohort it
                # copied `state_c1`'s verdict in 18 of 20 responses and its
                # not-described verdict never fired once, which made the
                # graders' commonest charge on this item unreachable.
                "desc": "States HOW the first consequence is being affected BY CHANGING "
                        "the antecedent",
                "codes": {"absent": "C_NO_EFFECT", "not_described": "C_NO_EFFECT"},
                "rule": (
                    "What becomes of the consequence is the whole question, and a student who says it STOPS has answered it. Credit a box that says the consequence will not happen any more, will happen less, or has been replaced by the improved state — the causal link does NOT have to be spelled out, because the question already frames everything here as a result of changing the antecedent, and demanding the link costs credit the graders gave. Be as generous about phrasing as everywhere else on this item. `{fail}` is for a box that says nothing about what becomes of the consequence at all — a benefit that never refers back to it — or one that only restates the arrangement the student has just described instead of its effect."' The two effect boxes must be about DIFFERENT consequences. Where both describe the same effect on the same consequence, the student has addressed one consequence twice and only the FIRST of the two can count; the second is `{fail}`. Judge the CONSEQUENCE, not the wording — where 4c lists two consequences of a similar kind, two similar-sounding effects can both be genuine, and a box is only a repeat when it is the same consequence again.'
                    "One arrangement in particular keeps reading as an effect and "
                    "is not one: a box that says WHEN the student may do something "
                    "— kept off it `until`, allowed it `only after`, permitted `as "
                    "long as` — is stating the timing of the plan, not what becomes "
                    "of the consequence. The consequence may well shrink as a result, "
                    "but the box has not said so, and this check is about what the "
                    "box says."
                ),
            },
            {
                "what": "state_c2",
                "pts": 1.25,
                "desc": "States the second consequence being affected, and it matches 4c",
                "codes": {"absent": "C_NOT_STATED", "neither": "C_MISMATCH"},
            },
            {
                "what": "affect_c2",
                "pts": 1.25,
                "desc": "States HOW the second consequence is being affected BY CHANGING "
                        "the antecedent",
                "codes": {"absent": "C_NO_EFFECT", "not_described": "C_NO_EFFECT"},
                "rule": (
                    "The same test as `affect_c1` above, applied to this box on its own: credit it when it says the second consequence stops, lessens, or is replaced by the improved state, without requiring the causal link to be spelled out; `{fail}` when it says nothing about what becomes of that consequence, or only restates the arrangement."' The two effect boxes must be about DIFFERENT consequences. Where both describe the same effect on the same consequence, the student has addressed one consequence twice and only the FIRST of the two can count; the second is `{fail}`. Judge the CONSEQUENCE, not the wording — where 4c lists two consequences of a similar kind, two similar-sounding effects can both be genuine, and a box is only a repeat when it is the same consequence again.'
                    "One arrangement in particular keeps reading as an effect and "
                    "is not one: a box that says WHEN the student may do something "
                    "— kept off it `until`, allowed it `only after`, permitted `as "
                    "long as` — is stating the timing of the plan, not what becomes "
                    "of the consequence. The consequence may well shrink as a result, "
                    "but the box has not said so, and this check is about what the "
                    "box says."
                ),
            },
        ],
        # The four dictionary wordings, verbatim. A_NOT_STATED and C_NOT_STATED
        # have no canonical text there — the dictionary prices "stating each
        # antecedent" and "stating each consequence" without giving feedback for
        # their absence — so those two are phrased from the credit lines they
        # enforce, and are the only wordings here not lifted from the source.
        "deductions": [
            {"code": "Q6_NONE", "pts": 10.0, "text": "did not answer"},
            {"code": "A_NOT_STATED", "pts": 1.25, "repeatable": True,
             "text": "Did not state the antecedent from question 4a that is being changed."},
            {"code": "A_MISMATCH", "pts": 1.25, "repeatable": True,
             "text": "This is a different antecedent from what you listed in question 4a. "
                     "The antecedents must match up."},
            {"code": "A_NO_CHANGE", "pts": 1.25, "repeatable": True,
             "text": "You do not describe how the antecedent(s) from question 4a will be "
                     "changed."},
            {"code": "C_MISMATCH", "pts": 1.25, "repeatable": True,
             "text": "This is a different consequence from what you listed in question 4c. "
                     "The consequences must match up."},
            {"code": "C_NO_EFFECT", "pts": 1.25, "repeatable": True,
             "text": "You do not describe how the consequence(s) will be affected by "
                     "changing the antecedent(s)."},
            {"code": "C_NOT_STATED", "pts": 1.25, "repeatable": True,
             "text": "Did not state the consequence being affected."},
        ],
        "guidance": [
            # BEFORE ADDING A MATCHING RULE HERE, READ THIS.
            #
            # Every remaining Q6 error is in the `refers_to` channel, and eight
            # rule wordings have now been built, measured and reverted trying to
            # fix it. The failure is always the same shape: the rule helps two
            # cells and costs two, inside a slot family where only 5 of 20 cells
            # return the same judgement across three identical passes. A 2-cell
            # move is inside the noise, so a 3-pass sweep cannot tell whether the
            # rule worked.
            #
            # The largest single semantic pattern is NOT inversion, which the
            # eighth attempt targeted. It is the reverse error: a consequence box
            # that describes the ANTECEDENT going away being credited as a
            # consequence -- "I will no longer suffer from being fulfilled by
            # unhealthy and fatty foods" against a listed consequence of
            # worsening health, where stopping the snacking is the plan, not its
            # consequence. Four boxes across three cells.
            #
            # And it CANNOT be fixed on its own. All four are score-neutral today:
            # one is already demoted as a cover duplicate, two are offset by an
            # inversion false-refusal in the same cover group, and p4's gold is
            # off the 1.25 grid so we sit at the nearest attainable value already.
            # Refusing them without also crediting the inversions unmasks the
            # error each one was cancelling and REGRESSES three cells by 1.25
            # each. The two rules are complements: landed together they are worth
            # about one cell (p9) plus three cells right for the right reasons;
            # landed separately either one loses ground.
            #
            # THE PAIR WAS BUILT AND SWEPT. It does not work, and neither does
            # any of the four wordings tried. Measured 2026-08-19, all reverted,
            # all against the same fixtures and the same corrected gold as the
            # 17/20 baseline in out/q6_boxbounds_full:
            #
            #   v1  flip clauses + boundary as a veto     probe only; broke p4
            #   v2  boundary sharpened into a test        17/20, MAE 0.25
            #   v3  boundary reordered as a fallback      17/20, MAE 0.25
            #   v4  flip clauses alone, no boundary       16/20, MAE 0.31
            #
            # Nothing beat leaving the rule out. Read the failures, not the totals:
            #
            # THEY DID NOT EVEN FIX p9, though all four looked like they had, and
            # that is the most important correction to this whole account. Measured
            # afterwards at NINE passes on the unmodified committed state, p9 is
            # exact 5 of 9 -- 56%, 95% CI [27%, 81%] -- a coin flip that already
            # lands right more often than not. It appears in the error table only
            # because the 3-pass baseline happened to draw it 2-of-3 the wrong way.
            # A rule that takes a 56% cell to exact-on-three-passes has told you
            # nothing, so every claim below that a variant "fixed p9" is withdrawn:
            # the honest scorecard for all four is that they broke cells and gained
            # nothing. p9 is not a target. There is nothing consistent there to fix.
            #
            # EVERY variant appeared to fix p9 and broke p1 or p4. p9's flip -- a box naming
            # bad health against a listed better health -- is unambiguous and all
            # four wordings caught it. p1 (more time to sleep, against consequences
            # about mood and falling asleep in class) and p4 (happier, against
            # getting mad and sleepy) sit at the edge of same-attribute, and no
            # wording separated them from p9. In v4 the clause written to hold p1
            # -- a general benefit is not an attribute -- held it in pass 1 and
            # failed in passes 2 and 3 on identical input. So the boundary is not
            # being drawn by the rule text at all; it moves with the draw. The
            # discrimination p9-yes / p1-no / p4-no may simply not be expressible
            # as prompt text, because the three differ by degree of semantic
            # distance and not by any structural feature a rule can name.
            #
            # THE TWO HALVES ARE IN TENSION, which is why the pair fails as a pair.
            # Tighten the boundary and it swallows a box that names an antecedent
            # AND a listed consequence under one negation: v2 cost p6 3.75 points
            # in one pass, on a cell that had been 6.25 in three straight passes,
            # because its box reads "no longer be filled with no motivation and
            # stiffness" -- "no longer" scoping over both, so the stiffness half
            # names 4c's second consequence and the box is creditable. Loosen the
            # boundary to a fallback and the flip clauses over-fire instead (v3:
            # p1's median regressed, c-family errors went 2 -> 3).
            #
            # A STABILITY FINDING THAT DID NOT REPLICATE. v3 cut cells taking more
            # than one value across three passes from 6/20 to 3/20, the largest
            # such gain anything has produced here. v4 was built to keep it without
            # the boundary test and lost it, so it came from the combination or it
            # was noise in a 3-pass sample. Do not cite it as a reason to try again.
            #
            # A FIFTH AND SIXTH ATTEMPT, on a different rule, established the
            # sharpest constraint of the lot: EDITING A LONG SLOT NOTE HAS
            # NON-LOCAL EFFECTS. The target was the duplicate-effect tie-break in
            # the `affect_c*` notes, which credits the FIRST of two boxes describing
            # the same effect and is arbitrary where the boxes differ in content.
            # Replacing it with "credit whichever describes the consequence more
            # directly", written as free-standing sentences, broke p14, p15 and p16
            # in a single pass. Rewritten as ONE sentence wholly inside the "where
            # both describe the same effect" conditional, with no imperative
            # escaping the clause, it still scored 14/20 against 17/20.
            #
            # p15 is the case that generalises. Both its effect boxes are EMPTY, so
            # a clause about choosing between two FILLED effect boxes cannot apply
            # to it -- and both its `state_c` verdicts moved anyway, costing the
            # cell a point. The clause was logically scoped and the behaviour was
            # not. These notes are past the length at which a local edit stays
            # local, so the risk attaches to editing them at all rather than to
            # what the edit says, and an incumbent wording is worth more than its
            # content: it is the only one carrying none of that risk. This applies
            # to every item with a note this size, not just Q6.
            #
            # p4 IS Q6's ONLY REAL RESIDUAL, and it is deliberately not pursued.
            # Nine passes put it exact 1 of 9 -- 11%, 95% CI [2%, 44%] -- so unlike
            # p9 it is a genuine, near-stable miss. ITS CAUSE IS UNKNOWN. Two
            # accounts were written here and both were wrong: the box does name an
            # antecedent that 4a puts in the effect half, which made the
            # trigger/effect rule the obvious culprit, and removing that rule leaves
            # p4 at exactly the same rate. Something else refuses `state_a2` about
            # 89% of the time. A correct reading of the text is not a cause.
            #
            # Verification, not invention, is the binding constraint on fixing it:
            # separating 11% from a fixed rate needs about nine passes on p4 AND
            # nine on every cell a candidate rule perturbs, and every
            # judgement-level rule tried has perturbed several. That is an order of
            # magnitude more measurement than one cell worth 1.25 points can justify.
            #
            # THE RULE IS KEPT, and the "measures neutral" verdict that briefly
            # stood here is WITHDRAWN. Removing it was tried and measured at CORPUS
            # scale, and it costs real cells:
            #
            #     rule present   17, 16, 16                  mean 16.3/20
            #     rule removed   15, 15, 14, 12, 15, 16      mean 14.5/20
            #
            # About 1.8 cells. The per-cell A/B below could not see this because the
            # effect is DISTRIBUTED: no single cell shows a difference its own
            # confidence interval can resolve, and the four cells that changed
            # status at 3 passes were the wrong place to look. A four-cell probe
            # cannot measure a corpus-scale effect spread thinly across twenty
            # cells, however many passes it runs -- which is the mirror image of the
            # earlier lesson that three passes cannot support a per-cell claim.
            # Match the measurement to the SCOPE of the claim, in both directions.
            #
            # HOW THE COUNTERFACTUAL WAS RUN, since the design is reusable: rule
            # removed, 20 cells x 3 passes to find what moved, then 9 passes on the
            # four cells that did, then -- because that probe could not see a
            # distributed effect -- 20 cells x 9 passes, stopped at six complete
            # passes once the arms separated.
            #
            # On the FOUR CELLS measured at 9 passes each way the rule looks
            # neutral -- p4 11% both ways, p5 100% vs 89%, p6 67% vs 56%, p18 78%
            # vs 100%, every interval overlapping. That reading was published here
            # and is superseded by the corpus figures at the top of this note: the
            # rule is worth ~1.8 cells even though no single cell can demonstrate
            # it. Keep both numbers in view. They are not contradictory, they are
            # measurements of different things, and taking either for the other is
            # how this rule was twice mis-assessed in one day.
            # See out/q6_noTErule_stage1, _stage2, _9pass and q6_TErule_present_9.
            #
            # AND A LESSON ABOUT PROBING. v2 was probed on 8 cells chosen from the
            # error list and looked clean; the full sweep found p6, which no error
            # list named. A rule keyed on a RELATION BETWEEN BOXES can fire on any
            # cell exhibiting the relation, so the affected set cannot be predicted
            # from where the errors are. Sweep these, do not probe them.
            #
            # The dictionary's own suggested framing, quoted as it stands. It is
            # the source of the sentence shape many students follow, and it is
            # the only worked material the graders were given.
            "The dictionary offers students this framing, and it is the shape most "
            "answers take: \"I can change my first antecedent of ___ by ___. This will "
            "impact my first consequence of ___ by ___. I can change my second antecedent "
            "of ___ by ___. This will impact my second consequence of ___ by ___.\"",
            # From the question, not from us: "each of your TWO antecedents".
            "The question asks about EACH OF THE TWO antecedents from 4a and EACH OF THE "
            "TWO consequences from 4c. Report which of the two listed items each box "
            "names; the grader pairs them. A response that names the same one twice has "
            "addressed one and left the other out.",
            # Some 4a and 4c entries state the element and then what it leads to,
            # joined by ";" or "so I" or "which" -- 10 of the corpus's 78 non-empty
            # reference boxes, about one in eight. Matching a Q6 box against the
            # whole entry lets it match on the EFFECT half instead of the element.
            # This is a statement about how the reference text is SHAPED, not a
            # judgement of how close two things are.
            #
            # TWO CLAIMS THAT USED TO BE HERE WERE WRONG, and both are the same
            # error as the p10 paragraph in handouts.GOLD_CEILINGS -- a plausible
            # reading written up as data. Corrected 2026-08-18 after measuring:
            #
            # It said "A THIRD of the 4a entries (13 of 39 boxes)". The real figure
            # is the 13% above. 39 is the 4a box count, so the original may have
            # counted one family with a looser marker set, but nothing reproduces
            # a third and the rule does not need it -- one entry in eight is still
            # worth a rule.
            #
            # It also named two examples, "not attending the gym" against a trigger
            # of "not being motivated; I miss workout days" and "going to bed late"
            # against "scrolling through tiktok, so I forget to go to bed early",
            # and said "Gold refuses both". Gold refuses ONE. Measured on per-family
            # counts against corrected gold: on the first cell we and gold both
            # credit one antecedent of two, so the refusal is consistent with gold;
            # on the second, gold credits one antecedent and we credit none. An
            # earlier version of this note blamed that on the rule. It is not the
            # rule: removing it leaves that cell at exactly the same rate (see the
            # counterfactual below). So one of the two examples offered in support
            # of the rule is a cell the rule does not in fact decide.
            #
            # WHAT IT COSTS AND EARNS, both now measured. Cost: nothing that can be
            # located. The cell this note used to call the rule's price is exact
            # 1 of 9 with the rule and 1 of 9 without it -- identical rate, identical
            # values -- so the rule does not decide it and no other cell shows a
            # per-cell loss either. Earns: about 1.8 cells corpus-wide.
            #
            #     rule present   17, 16, 16                  mean 16.3/20
            #     rule removed   15, 15, 14, 12, 15, 16      mean 14.5/20
            #
            # Those two findings look contradictory and are not. The benefit is
            # DISTRIBUTED -- no single cell moves by more than its own confidence
            # interval, while the total moves by nearly two cells -- so a per-cell
            # A/B cannot see it however many passes it runs, and a corpus sweep
            # cannot say which cells produced it. Read both, and do not substitute
            # one for the other; doing exactly that had this rule recorded as
            # "costs one cell, earns nothing" and then as "measures neutral", within
            # a day, before either was measured at the right scope.
            #
            # A static detector was also tried, to find where the rule bites without
            # running anything, and does not work: it misses the first cell above,
            # where the box matches NEITHER half, and reports three cells whose only
            # link is a shared common word.
            #
            # SCOPING CONSTRAINT FOR ANY INVERSION RULE ADDED LATER. The two rules
            # reach for the SAME textual relation from opposite directions, and the
            # cell where the rule costs us is exactly the cell where they collide.
            # p4's 4a reads "scrolling through tiktok, so I forget to go to bed
            # EARLY" and its Q6 box says "going to bed LATE" -- the same state with
            # the polarity flipped. This rule refuses it on POSITION, because it is
            # the Y half; an inversion rule would credit it on MEANING, because the
            # attribute matches and only the sign differs. Surveyed across the
            # corpus, p4 is the ONLY one of the eight trigger/effect cells where the
            # relation in play is an inversion -- p6's box matches Y by near-synonymy
            # ("miss workout days" / "not attending the gym") and p15's matches X --
            # so this collision accounts for the whole of this rule's measured cost.
            #
            # They are compatible only if inversion names its comparison target
            # explicitly: the LISTED ELEMENT, never the entry. "Is the box this
            # element with the polarity flipped?" refuses p4, because Y is a
            # DIFFERENT ATTRIBUTE from X -- it is what X causes -- so inverting Y
            # still has not named X. Stated loosely enough to apply to any text in
            # the entry, inversion makes Y fair game, credits p4, and silently
            # undoes this rule. That is the back-reference failure again: a rule
            # scoped in the notes to one slot family leaked in EFFECT because the
            # phrase it keyed on sat in 22 antecedent boxes across 14 cells.
            #
            # What this does NOT settle is whether refusing p4 is right. Gold
            # credits it, and the student does treat "going to bed late" as their
            # own antecedent -- re-describing an antecedent at one remove between
            # items is ordinary. Our rule refuses that re-description. One cell,
            # with off-grid gold and a truncated `state_c2`, cannot decide it.
            "HOW TO READ A 4a OR 4c ENTRY WHEN YOU MATCH AGAINST IT. Students "
            "often write the element and then what it leads to, in one entry: "
            "\"my trigger is X; I end up Y\", \"my antecedent is X, so I Y\", "
            "\"X, which leads to Y\". WHEN Y IS OF THE THIRD KIND in the "
            "definition at the top of this item — a consequence, meaning the "
            "unwanted behaviour itself or something following from it — match the "
            "Q6 box against X, not against Y. A box naming that kind of Y has "
            "named the consequence of the trigger rather than the trigger, so it "
            "does not refer to that 4a entry, and that holds however closely the "
            "wording of Y is echoed. Echoing Y closely is exactly the case to "
            "watch for. It is also the case to match against 4c instead, where "
            "that consequence is listed. "
            "Kinds 1 and 2 are not affected: a Y that restates the antecedent, or "
            "that still leads to the unwanted behaviour, IS part of the antecedent, "
            "and the definition at the top governs. Decide the kind first. "
            "The same reading applies to a 4c entry that names a consequence and "
            "then what follows from it.",
        ],
        "context": ["Q1", "Q2", "Q4a", "Q4c"],
    },
]

# Items that read the student's UNDERLINED UTB choice from the document's
# formatting. Q1 defines the UTB and Q2 defines its counterpart, so the marked
# choice corroborates both; no other item is judged against it. Declared here
# because score.build_prompt used to select these two by item id, which the
# enforcement audit reads as a rule it cannot compare -- and the hint IS
# scoring-relevant: it is evidence handed to the model.
# Q4b's two examples are COMPUTED from a pick each, not judged directly. `absent`
# and `wrong_kind` charge different codes -- "you only gave one example" against a
# repeatable "that is not something done instead" -- so this needs the one primitive
# that can give a check more than one kind of failure. `equals`, `expect` and
# `forbid` each offer a single failing verdict, and two `forbid` rules on one key
# credit a wrong entry rather than refusing it.
#
# WHY AT ALL: the INSTEAD-OF test was prose on both sides, the two scorers read it
# differently, and no primitive existed for the audit to compare -- Q4b/p4 and p12
# are the measured cost. Computing it from one declared map means both engines reach
# the same verdict from the same pick, so the disagreement has nowhere left to live
# except the classification itself, which is one named question instead of five
# weighed at once.
#
# THE REFERENT TEST IS DELIBERATELY NOT HERE. An entry naming the same THING as one
# of the student's own 4a antecedents would be a sixth option, and it was measured
# once in prose form and rejected for THREE TIMES THE VARIANCE. Adding it here would
# confound that experiment with this mechanism change; it stays subgoal 10.
MAPS: dict[str, list[dict]] = {
    "Q4b": [
        {"key": "behavior_1", "pick": "b1_basis",
         "pairs": [{"value": "activity", "verdict": "met"},
                   {"value": "none", "verdict": "absent"}],
         "fallback": "wrong_kind"},
        {"key": "behavior_2", "pick": "b2_basis",
         "pairs": [{"value": "activity", "verdict": "met"},
                   {"value": "none", "verdict": "absent"}],
         "fallback": "wrong_kind"},
    ],
}
for _it in ITEMS:
    if _it["id"] in MAPS:
        _it["maps"] = MAPS[_it["id"]]


READS_UTB_CHOICE = ("Q1", "Q2")
for _it in ITEMS:
    if _it["id"] in READS_UTB_CHOICE:
        _it["reads_utb_choice"] = True


BY_ID = {it["id"]: it for it in ITEMS}
TOTAL = sum(it["max"] for it in ITEMS)  # 45.0 scored; +5 upload = 50
