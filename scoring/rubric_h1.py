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
            "particular UTB for intervention. Requires 1 sentence describing the UTB {{corpus:Q2/p15:response:62:65:sha=6201111b83a0:shape=R3-0-20}}"
            "{{corpus:Q2/p15:response:66:114:sha=9a660f49e81b:shape=S5-20}} change this behavior."
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
                "desc": "{{corpus:Q1/p10:response:0:31:sha=f748d9d9ddd6}} identified as the student's "
                        "own target, not merely mentioned as the cause of some effect. "
                        "Judge ONLY the response text the student wrote. Where the UTB "
                        "also appears in this prompt as a separate field or context "
                        "line, that does NOT satisfy this check — the question is "
                        "whether the RESPONSE names the behaviour as its target. A "
                        "response that opens straight into effects (\"{{corpus:Q1/p20:response:0:11:sha=4b138919e041:shape=R11-0-20}}"
                        "{{corpus:Q1/p20:response:12:36:sha=5d2f3521dd7e}} tired...\") fails; a sentence of "
                        "the form \"{{corpus:Q1/p3:response:0:30:sha=c5fd6758ccc7}} X\" satisfies it"
            },
            # Q1 HAS NO GOLD CEILING. It had an entry in handouts.GOLD_CEILINGS
            # claiming `reasons_given` was unwinnable on p6 and p10 "for every model
            # tried"; that entry is gone, because gold's rule turned out to be
            # LOCATABLE and merely conditional — see below — and the scaffold now
            # scores both cells. A `utb_stated` sub-entry went with it: p17/p20 look
            # alike and gold splits them, but gpt-5-mini matches gold on BOTH
            # (reading p17's "{{corpus:Q1/p17:response:45:64:sha=9b9dc5f41af2}}" as claiming the behaviour), so the
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
            # flickers 2<->3 on p10 (the goal restatement "{{corpus:Q1/p10:response:117:141:sha=e4f5396e86db}}
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
            # it bought: p6 fell 6/6 -> 4/8 because "{{corpus:Q1/p6:response:521:547:sha=fbf0b3dad913}} achy"
            # started splitting, and p5 fell 6/6 -> 1/8 because the clause overrode
            # the knock-on rule on "snacking ... {{corpus:Q1/p5:response:220:243:sha=a56d4f5cc177}} weight".
            # Net about -0.45 cells. To keep p19 it would have to separate two
            # genuinely different effects from two adjectives for one effect
            # ("tired and unmotivated" = 2, "sore and achy" = 1), which is the same
            # distinctness judgement handouts.GOLD_CEILINGS records as unlocatable on
            # Q2. After the revert p19 still sits at 6/8, better than the 3/6 it
            # started at, so the clause was not what carried it.
            #
            # p6 IS FIXED BUT MARGINAL. Two observations that have to be held
            # together: on isolated single-cell runs after the revert it sits at 4 of
            # 8, `harms_listed` flickering 1<->2 on "{{corpus:Q1/p6:response:521:547:sha=fbf0b3dad913}} achy";
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
                        "symptom of it. \"{{corpus:Q1/p1:response:280:321:sha=552f19bc3c86:shape=R41-0-20}}"
                        "{{corpus:Q1/p1:response:322:337:sha=45dff12ade2b}} class\" is one. A reason is a whole STATEMENT: a "
                        "clause that merely continues one is part of it, so a named "
                        "effect followed by \"which causes\" and its downstream result "
                        "is ONE, while two effects merely joined by "
                        "\"and\" are two. Do NOT count a restatement that the student "
                        "struggles with the behaviour (participant 1) or a behaviour "
                        "performed DURING it (participant 2). Answer 3 for three or more",
            },
            {
                "what": "benefits_listed",
                "reported": True,
                "verdicts": ["3", "2", "1", "0"],
                "desc": "HOW MANY statements name a BENEFIT the student expects from "
                        "changing. The test is GETS versus DOES: a benefit is "
                        "something the student GETS — \"{{corpus:Q1/p10:response:155:176:sha=c36cf8a4ad7a:shape=R21-0-20}}"
                        "{{corpus:Q1/p10:response:177:189:sha=adfde6a8386a}} myself\", \"{{corpus:Q1/p16:response:256:285:sha=30187edf82d0}} "
                        "person\". A statement of what they intend to DO names the "
                        "goal behaviour itself and is NOT a benefit of it, however "
                        "much it sounds like a wish. Do NOT count a restatement of the goal "
                        "(\"{{corpus:Q1/p10:response:117:146:sha=be46148ce74e}} active\"), the struggle "
                        "(\"something I have been struggling with\"), or background "
                        "about how the behaviour came about (\"I used to exercise {{corpus:Q1/p16:response:6:7:sha=ca978112ca1b:shape=R1-0-20}}"
                        "{{corpus:Q1/p16:response:92:102:sha=984c54eb4011}} sports\"). Answer 3 for three or more",
            },
            {
                "what": "reasons_given",
                "reported": True,
                "verdicts": ["3", "2", "1", "0"],
                # The thematic generosity is RIGHT here and is kept: gold really
                # does count "makes me tired" / "makes me grumpy" / "it shows
                # through my emotions" as three. What was missing is the
                # STRUCTURAL boundary — p5 was counted 3 by splitting one sentence
                # at its `which`: "{{corpus:Q1/p5:response:161:207:sha=302325c46580}}
                # like candy" + "{{corpus:Q1/p5:response:220:243:sha=a56d4f5cc177}} weight". Gold counts that
                # sentence once, so p5 is 2. Same shape as Q2 p19; see the
                # knock-on rule on Q2's `reasons_given`.
                "desc": "HOW MANY reasons count. The rule is CONDITIONAL on the two "
                        "counts above. If `harms_listed` is 1 or more the answer IS "
                        "`harms_listed`, and benefits do not add to it — a response with "
                        "one harm and two benefits counts 1, which is what participant 6 "
                        "scored. Only when `harms_listed` is 0 does the answer become "
                        "`benefits_listed` instead, which is how participants 9, 10 and 16 "
                        "were credited. Never answer 0 when the student offered anything "
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
                    "of exercise, {{corpus:Q1/p12:response:31:69:sha=67aefa440274}} vegetables, {{corpus:Q1/p7:response:9:17:sha=c2c7ae2ad923:shape=R0-1-73,R8-0-20}}"
                    "{{corpus:Q1/p7:response:18:34:sha=6d2b932a45df}} electronics). Please choose one of these behaviors for "
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
            "sentence describing the WGB {{corpus:Q2/p15:response:62:111:sha=dd7a8b7daac8:shape=R39-1-20,R49-0-20}}"
            "{{corpus:Q2/p15:response:112:125:sha=6258e0ec68f2}} it."
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
                        "Fail this ONLY when it is a different behaviour altogether — "
                        "\"connect more with people and restart reading books\" against a "
                        "UTB of screen time. A goal in the right territory that simply "
                        "does not invert the behaviour still passes this: that is "
                        "WGB_NOT_OPPOSITE on `wgb_inverts_utb`, worth 2, not the whole item. "
                        "When this DOES fail the goal is unstated and its reasons cannot "
                        "count either, so WGB_UNRELATED stands INSTEAD of "
                        "WGB_NOT_OPPOSITE plus reason deductions, never alongside them — "
                        "it cost participant 7 the whole item",
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
                # catch "reading {{corpus:Q2/p7:response:119:153:sha=9da42b146750:shape=Cdfc0}} games".
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
                #   p10 lack of exercise -> "{{corpus:Q2/p10:response:31:56:sha=2bd894e2eb1a}}"   ABSENT
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
                        "different measure (losing twenty pounds against a UTB of "
                        "lack of exercise). A goal stating the same behaviour's "
                        "positive state PASSES — \"get back in shape\" against a UTB "
                        "of {{corpus:Q3/p10:action:42:61:sha=00b9bd1557d3}} the inversion, phrased as a state. Full "
                        "credit is the same behaviour turned around: UTB lack of sleep -> "
                        "\"get eight hours of sleep\"; UTB lack of exercise -> \"{{corpus:Q2/p6:response:30:36:sha=192f9a06d1dd:shape=R6-0-20}}"
                        "{{corpus:Q2/p6:response:37:57:sha=7322fa55fef0}} week\". \"{{corpus:Q2/p10:response:31:56:sha=2bd894e2eb1a:shape=C1}}\" "
                        "against lack of exercise cost participant 10 two points — it "
                        "never says exercise more",
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
            },
            {
                "what": "reasons_given",
                "reported": True,
                "verdicts": ["3", "2", "1", "0"],
                # The old text said to count "as generously as the guidance says:
                # statements naming a benefit count separately even when
                # thematically related". That instructs the WRONG answer. The
                # handout does print "at least 3 sentences", but gold does not
                # score it that way: on p18 it rejects "{{corpus:Q2/p18:response:122:147:sha=123ca2f427fe}}
                # {{corpus:Q2/p18:response:148:194:sha=688640edf4ec}} shape" as
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
                        "knock-on effect of the first is ONE (\"{{corpus:Q2/p19:response:290:303:sha=8ba2dbe0fbec:shape=R13-0-20}}"
                        "{{corpus:Q2/p19:response:304:311:sha=b0185429c6b9}} in {{corpus:Q2/p19:response:319:347:sha=c5e6c468e8bc:shape=C1ef80}} learning\"), while "
                        "two independent benefits merely joined by \"and\" are TWO "
                        "(\"{{corpus:Q2/p6:response:147:198:sha=0b68cb252d17:shape=R43-3-414e44,R51-0-20}}"
                        "{{corpus:Q2/p6:response:169:175:sha=d7d5dcc36942}} also\"). A restatement of the GOAL is not a benefit of "
                        "it either — \"{{corpus:Q2/p6:response:275:320:sha=447eb5403401}}\" "
                        "against a goal of being more active cost participant 6 a point. "
                        "Statements about why the UTB is bad belong to Q1 and earn "
                        "nothing here; participant 3 lost all three that way. Answer 3 "
                        "for three or more",
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
                    "You did not provide 3 separate reasons as to {{corpus:Q2/p15:response:98:125:sha=77b0c1a2cd0c:shape=R3-1-20,R27-0-20}}"
                    "{{corpus:Q2/p15:response:126:130:sha=1eb79602411e}} WGB. These should be the benefits of engaging in the WGB."
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
                "desc": "States the action to be taken",
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
                "desc": "Has a time frame for the goal",
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
                    "-1 pt: For time-bound, you have one week of baseline data {{corpus:Q3/p1:timebound:166:181:sha=d6aa9b9705f2:shape=R15-0-20}}"
                    "{{corpus:Q3/p1:timebound:109:111:sha=28391d3bc64e}} intervention, or 4 weeks total."
                ),
            },
        ],
        "guidance": [
            "Award each of the five letters independently, 1 point each.",
            "Time-Bound has a near-verbatim expected answer: four weeks total, {{corpus:Q3/p1:timebound:129:140:sha=0a0e842023db:shape=R11-0-20}}"
            "{{corpus:Q3/p1:timebound:141:214:sha=6664d8edc53e}} Any "
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
        "unreachable_codes": ["A_NONE"],
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
            {
                "what": "keyword",
                "pts": 1.0,
                "verdicts": ["met", "absent", "unclear"],
                "codes": {"absent": "A_NO_KEYWORD", "unclear": "A_NO_KEYWORD"},
                "desc": "Uses 'antecedent' or 'trigger' at least once. A_NO_KEYWORD applies whenever neither \"antecedent\" nor \"trigger\" appears anywhere in the response. The graders enforced this inconsistently — participant 17 lost the point, participants 9 and 15 did not — but the dictionary is explicit, so apply it. This is a deliberate divergence from those two gold rows.",
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
                "pts": 1.0,
                "text": 'Did not use the word "antecedent" or "trigger".',
            },
        ],
        "guidance": [
            "An antecedent happens BEFORE the UTB and plausibly leads to it.",
            "ACCEPT generously when the example precedes the UTB and a reader can see how "
            "it leads there. A circumstance or state of mind qualifies — \"{{corpus:Q4a/p19:first:23:36:sha=273533e4c2ad:shape=R13-0-20}}"
            "{{corpus:Q4a/p19:first:37:58:sha=e48b74e6c289:shape=S1-20}}\", \"long {{corpus:Q4a/p15:first:14:43:sha=7d2e226fbc73}} filled\", "
            "\"{{corpus:Q4a/p15:second:0:26:sha=b39ebb0b59d3:shape=C1}} me\" all earned full credit. Do not demand an "
            "elaborate causal chain; plausible precedence is enough.",
            "REJECT decisively in three cases. (a) The example is an AFTERMATH of the UTB "
            "— phrased as happening afterwards or as a result (\"{{corpus:Q4a/p14:second:21:46:sha=44ac4c79e876:shape=R25-0-20}}"
            "{{corpus:Q4a/p14:second:47:61:sha=3aef819f1371}} that I can't function\" cost participant 14 four points). "
            "(b) The example is what the student does INSTEAD of the goal behaviour, which "
            "belongs to 4b (\"{{corpus:Q4a/p3:second:25:67:sha=5c4b20801855}}\" cost participant "
            "3 two points). (c) The example is a consequence already listed in 4c.",
            "Where the link is genuinely opaque rather than merely brief, the graders did "
            "deduct — \"how does grumpy emotions lead to lack of sleep?\" (participant 4), "
            "\"how does not stretching lead to lack of exercise?\" (participant 6).",
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
            "describe two examples. Additionally, state whether {{corpus:Q4b/p15:modify:0:23:sha=6fa65a43725e:shape=R0-1-74,R23-0-20}}"
            "{{corpus:Q4b/p15:modify:24:34:sha=0de60378f0ff}} you to modify AND why."
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
                "verdicts": ["met", "absent", "not_active"],
                "codes": {"absent": "B_ONLY_ONE", "not_active": "B_NOT_ACTIVE"},
                "desc": "First example of what they do INSTEAD OF the goal behavior",
                "rule": (
                    "`{fail}` in two cases. (1) The entry names a CONSEQUENCE of the "
                    "unwanted behaviour — a state they ended up in, or something they then had "
                    "to do — rather than something they did INSTEAD of the goal behaviour. (2) "
                    "The entry IS the goal behaviour, done at the wrong time, in the wrong "
                    "place, or badly: you cannot do something instead of itself. If the goal is "
                    "to sleep enough, sleeping in the car is not something done instead of "
                    "sleeping — it is that sleep, displaced. Keep this apart from a RIVAL "
                    "choice, which IS a substitute: if the goal is to eat fruit, eating chips "
                    "counts, because chips are not fruit. The question is whether they did a "
                    "different thing that crowded the goal out, or the goal itself gone wrong. "
                    "(3) The entry names an ordinary activity that CARRIES a state the unwanted "
                    "behaviour produced — \"{{corpus:Q4b/p6:second:41:72:sha=ca4722977c72}} muscles\", \"I sit "
                    "in lecture unable to focus\". The activity is incidental there: they would "
                    "be doing it anyway, and what the sentence actually reports is the state, "
                    "which is a consequence. Test it by asking whether the activity would have "
                    "happened regardless of the goal behaviour. If it would, nothing was "
                    "displaced and the entry is not a substitute — an activity that is LIKELY A "
                    "CONSEQUENCE of not doing the goal behaviour cannot also be what replaced "
                    "it. (4) Where the entry offers ALTERNATIVES — two or more things joined by "
                    "\"or\", either of which might be what they did — every alternative must "
                    "pass the tests above. One qualifying alternative does not rescue the rest: "
                    "\"I am tired in class OR catching up on chores\" fails, because being "
                    "tired is a state the behaviour produced. This applies only to genuine "
                    "alternatives. A sentence that names an activity AND THEN what came of it "
                    "is judged on the activity — \"I eat chips and let the fruit go bad\" is "
                    "one substitute with its result attached, not two alternatives — and "
                    "several words for the same choice (chips, candy, cookies) are one "
                    "substitute described three ways. (5) NAMING A FAILURE TO ACT IS NOT NAMING "
                    "A SUBSTITUTE. \"I procrastinate\", \"I avoid going\", \"I neglect it\", "
                    "\"I put it off\" all describe the goal behaviour NOT happening; they do "
                    "not say what the student was doing in that time, which is what the "
                    "question asks. Credit the concrete activity if the entry gives one (\"{{corpus:Q4b/p8:first:5:9:sha=afa497455f37:shape=R4-0-20}}"
                    "{{corpus:Q4b/p8:first:31:46:sha=8dd0997741e5}} games\"), and treat the not-doing as failing the test — "
                    "including when it is one alternative among several"
                ),
            },
            {
                "what": "behavior_2",
                "pts": 1.5,
                "verdicts": ["met", "absent", "not_active"],
                "codes": {"absent": "B_ONLY_ONE", "not_active": "B_NOT_ACTIVE"},
                "desc": "Second example of what they do INSTEAD OF the goal behavior",
                "rule": (
                    "`{fail}` on the same four tests as the first example: a consequence of "
                    "the unwanted behaviour; the goal behaviour itself done at the wrong time "
                    "or place; an ordinary activity carrying a state that behaviour produced; a "
                    "set of ALTERNATIVES joined by \"or\" in which any one alternative fails "
                    "those tests; or a naming of the goal behaviour NOT happening "
                    "(procrastinating, avoiding, neglecting) rather than of what they did "
                    "instead"
                ),
            },
            {
                "what": "modify_stated",
                "pts": 2.0,
                "verdicts": ["met", "absent"],
                "codes": {"absent": "B_NO_MODIFY"},
                "desc": "States whether it is a good choice to modify",
            },
            {
                "what": "modify_why",
                "pts": 1.0,
                "verdicts": ["met", "absent"],
                "codes": {"absent": "B_NO_MODIFY_WHY"},
                "desc": "States why it is or is not. B_NO_MODIFY_WHY applies only when the response says it is/isn't a good choice to modify and gives NO reason whatsoever. Any reason, however brief — \"{{corpus:Q4b/p19:modify:39:76:sha=f40f8f6bab49}} go to bed\" — earns the point.",
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
            "ACCEPT — and accept broadly, once that test is met. Ordinary activities "
            "(\"I am scrolling social media\", \"{{corpus:Q4b/p15:second:38:72:sha=8493013dd8ed:shape=R34-0-20}}"
            "{{corpus:Q4b/p15:second:73:78:sha=45569da57f4b}}\", \"{{corpus:Q4b/p16:first:0:21:sha=4b5ab94038d3}} TV\", \"{{corpus:Q4b/p13:first:19:39:sha=771ed2fbc3ad:shape=C1}} "
            "multitask\"), INTERNAL STATES AND THOUGHTS that are themselves what they "
            "are doing instead (\"{{corpus:Q4b/p13:second:25:56:sha=6a68567defb7}} sleep {{corpus:Q4b/p13:second:64:78:sha=a57ca598fd79:shape=R4-1-49,R12-1-27,R14-0-20}}"
            "{{corpus:Q4b/p13:second:79:92:sha=d13f8875e1b2}} it\", \"{{corpus:Q4b/p19:first:28:69:sha=ac83b3561af9}} night\"), "
            "and COPING BEHAVIOURS standing in for the goal behaviour (\"{{corpus:Q4b/p19:second:35:44:sha=232aaf968f26:shape=R9-0-20}}"
            "{{corpus:Q4b/p19:second:45:74:sha=b28fcda7c6f4}} day\") all earned full credit — participants "
            "13, 15 and 19 each scored 5.0 on responses of exactly these kinds. Do not "
            "judge how insightful the entry is; judge only whether it is an alternative "
            "to the goal behaviour.",
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
        "unreachable_codes": ["C_NONE", "C_NO_KEYWORD"],
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
                # Q4a is the opposite case and keeps its charge: p17's gold row
                # reads `-1 pt: did not use the word "antecedent" or "trigger"`.
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
                "desc": "Uses 'consequence' at least once (advisory, not scored). The word \"consequence\" is NOT worth a point here, unlike the keyword on Q4a. Report `keyword: absent` when it appears nowhere — the feedback may mention it — but it costs nothing. IMPLICIT (from gold): no Q4c row in the corpus deducts for it, and none carries a 1-point deduction at all; participants 15 and 17 kept full credit while omitting the word. Q4a differs and keeps its charge, because participant 17's Q4a row does deduct for the missing keyword.",
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
            "ACCEPT downstream effects of any kind, including behavioural ones. \"{{corpus:Q4c/p12:second:28:38:sha=fea76a662bd4:shape=R10-0-20}}"
            "{{corpus:Q4c/p12:second:39:90:sha=4e89e021ca3d}} health\" is a valid "
            "{{corpus:Q4c/p12:first:4:29:sha=55300e3c92df}} fruits and vegetables — participant 12 had full "
            "credit for it. Do not reject a consequence merely because it names an action "
            "rather than a state.",
            "REJECT a statement that is really a BENEFIT of the goal behaviour rather than "
            "a result of the UTB. \"I would have {{corpus:Q4c/p9:second:11:53:sha=c5630be947d7}} "
            "maintained a healthy weight\" is not a consequence of failing to exercise; "
            "participant 9 lost 4 points for two statements of that kind.",
            "DEDUCT when the causal link is left for the reader to guess. \"{{corpus:Q4c/p20:second:54:66:sha=aa80b04b6cf8:shape=R0-1-46,R12-0-20}}"
            "{{corpus:Q4c/p20:second:67:80:sha=c0099a8efaec}}\" against a UTB of lack of sleep cost participant 20 two points "
            "— \"need more explanation on how your second example is a direct consequence\". "
            "Participant 4 lost 2 for \"specify what spending too much time awake means\".",
            "The two consequences must be distinct — participant 11 lost 2 points for "
            "listing the same one twice.",
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
            "2.5 points, essentially regardless of how insightful X is. \"{{corpus:Q5/p8:first:42:56:sha=e157da34f477:shape=R14-0-20}}"
            "{{corpus:Q5/p8:first:57:84:sha=98a6b8fd7ee9}} away\", \"{{corpus:Q5/p8:second:40:69:sha=909af5c79e7a:shape=C100}} it\", "
            "\"{{corpus:Q5/p19:second:25:80:sha=6f1903ee04a1}} enough\", \"because "
            "I'd {{corpus:Q5/p9:first:37:77:sha=dcb8f14dd6be}}\" — every one of these scored "
            "full marks (participants 8, 9, 19, 20).",
            "A THIN REASON IS AN ADVISORY, NOT A DEDUCTION. When a reason is present but "
            "weak, the graders wrote a note and left the score at full. Participant 9's "
            "second reason drew \"Explain how your second reason is a reason you are "
            "choosing to not exercise\" — as feedback, on a 5.0. Put that kind of remark in "
            "advisory_note; do not emit W_NOT_REASON for it.",
            "W_NOT_REASON is for a statement that is not a reason for CONTINUING at all — "
            "most often a consequence wearing a reason's clothes. \"{{corpus:Q5/p4:second:0:23:sha=1416fe6d0f1a:shape=R23-0-20}}"
            "{{corpus:Q5/p4:second:24:83:sha=f2c3b6afc33a:shape=A51}} tired\" describes "
            "an effect of the UTB, not a payoff from it, and cost participant 4 2.5 points.",
            "THE LINE BETWEEN THIN AND ABSENT. The two rules above overlap, and the example "
            "just given has perfect form, so apply this test per entry and in this order. "
            "Deduct W_NOT_REASON ONLY when the statement (a) names a CONSEQUENCE of the "
            "unwanted behaviour rather than something gained by continuing it, or (b) is "
            "about a DIFFERENT behaviour than the UTB. Everything else that is present — "
            "vague, circular, shallow, clumsily worded, or a reason you find unconvincing — "
            "is THIN: credit it and write an advisory. Vagueness is never a deduction on "
            "this item; only the wrong KIND of statement is.",
            "W_ONLY_ONE also covers two statements that collapse into the SAME reason. "
            "Participant 6 gave two entries both amounting to escaping physical effort and "
            "was marked \"missing a reason you continue to engage in lack of exercise\".",
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
                "desc": "States HOW the {{corpus:Q4a/p16:second:3:29:sha=964504f85774}} changed",
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
                "desc": "States HOW {{corpus:Q4c/p19:second:0:25:sha=d4d526f38996:shape=C1}} being affected BY CHANGING "
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
        ],
        "context": ["Q1", "Q2", "Q4a", "Q4c"],
    },
]

BY_ID = {it["id"]: it for it in ITEMS}
TOTAL = sum(it["max"] for it in ITEMS)  # 45.0 scored; +5 upload = 50
