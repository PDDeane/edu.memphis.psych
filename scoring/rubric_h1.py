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
                        "clause that merely continues one is part of it, so \"{{corpus:Q1/p5:response:161:169:sha=7fc24b87e3f5:shape=R8-0-20}}"
                        "{{corpus:Q1/p5:response:170:232:sha=68f227b24df0:shape=R50-5-5748494348,R56-6-43415553455320}}"
                        "{{corpus:Q1/p5:response:233:243:sha=1baf8ec21bc7}} weight\" is ONE, while two effects merely joined by "
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
                "desc": "First active behavior",
            },
            {
                "what": "behavior_2",
                "pts": 1.5,
                "verdicts": ["met", "absent", "not_active"],
                "codes": {"absent": "B_ONLY_ONE", "not_active": "B_NOT_ACTIVE"},
                "desc": "Second active behavior",
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
            "An active behavior happens DURING the UTB — what the student does instead of "
            "the WGB.",
            "THE TEST IS FRAMING, NOT CATEGORY. The graders accept almost anything the "
            "student presents as happening during the UTB episode. Judge how the sentence "
            "is framed, not whether the content is technically a 'behaviour'.",
            "ACCEPT — and accept broadly. Ordinary activities (\"I am scrolling social "
            "media\", \"{{corpus:Q4b/p15:second:38:78:sha=834b72be96f6}}\", \"{{corpus:Q4b/p16:first:0:21:sha=4b5ab94038d3}} "
            "TV\", \"{{corpus:Q4b/p13:first:19:39:sha=771ed2fbc3ad:shape=C1}} multitask\"), INTERNAL STATES AND THOUGHTS "
            "occurring in the episode (\"{{corpus:Q4b/p13:second:25:56:sha=6a68567defb7}} sleep {{corpus:Q4b/p13:second:64:69:sha=20d82428425b:shape=R4-1-4920}}"
            "{{corpus:Q4b/p13:second:70:92:sha=ada4d124385d:shape=A6}} it\", \"{{corpus:Q4b/p19:first:28:69:sha=ac83b3561af9}} "
            "night\"), and COPING BEHAVIOURS in the same period (\"{{corpus:Q4b/p19:second:35:56:sha=8b16de8fb795:shape=R21-0-20}}"
            "{{corpus:Q4b/p19:second:57:74:sha=0570c82c125d}} day\") all earned full credit — participants 13, 15 and 19 "
            "each scored 5.0 on responses of exactly these kinds. A sentence opening \"{{corpus:Q4b/p15:first:0:4:sha=cf9c7aa24a26:shape=R4-0-20}}"
            "{{corpus:Q4b/p15:first:5:42:sha=cd9c4f449b3d}} ...\" is almost always creditable.",
            "REJECT in ONE shape: the sentence is not an example of doing anything at "
            "all — meta-commentary about whether the behaviour is worth modifying, or a "
            "recital of consequences. When neither entry is an example, deduct "
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
        # Q6's ledger is DERIVED, not model-authored: the model answers one
        # met/absent/mismatch/not_described question per slot and the code
        # below turns unmet slots into deductions. See `derive_from_credit`.
        "derive_from_credit": True,
        "blank_code": "Q6_NONE",
        # The question says "change EACH OF YOUR TWO antecedents", so the two
        # state slots must name DIFFERENT 4a items — and until this existed
        # nothing checked it. The met/absent/mismatch vocabulary carries no
        # identity, so a student who addressed one antecedent twice was credited
        # for both slots: participant 18 named the same 4c consequence in both
        # boxes and scored 8.75 where the graders gave 7.5 ("did not address how
        # {{corpus:Q4c/p19:second:0:25:sha=d4d526f38996:shape=C1}} being affected").
        #
        # So the model now also reports WHICH of the two it named, and the code
        # does the pairing. Order-free by construction: a student who addresses
        # 4a's second antecedent first is not penalised (worked example 2 is
        # exactly that), and naming the same one twice is unrepresentable rather
        # than merely discouraged. Ported from the web version's `cover`, where
        # the same reasoning already applies.
        # `verdicts` replaces the generic met/absent/mismatch vocabulary on these
        # four slots: for a slot whose whole job is "which of the two is this?",
        # the identity IS the verdict. Asking met/absent/mismatch AND a separate
        # identity was two questions for one fact, and it admitted contradictions
        # (`met` + `neither`) that code then had to resolve. Same four values as
        # the web sheet, so the two are now the same shape.
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
                # Q6's central judgement, moved here from item-level `guidance`, where
             # it was read before all eight slots while the two it governs carried
             # one-line descs. Same move as Q1 (+2 cells on the paper scorer) and
             # Q2 (+1 Opus / +2 gpt-5-mini). Made self-contained on the way: it
             # used to open "the qualification on the rule above", meaning the
             # generosity-about-wording bullet, and to cite the worked example
             # "below" — neither reference survives a move.
             "desc": "Describes HOW the first antecedent will be changed. Be generous "
                     "about loose phrasing but strict about WHAT THE CHANGE ACTS ON: "
                     "judge that, not how neatly it is put. Where the words after "
                     "\"by ...\" describe the student performing their WGB, or "
                     "improving some other habit, the antecedent itself is untouched "
                     "and this is `not_described`. \"{{corpus:Q6/p2:state_a2:0:30:sha=fdc086c0791a:shape=R30-0-20}}"
                     "{{corpus:Q6/p2:state_a2:31:74:sha=390c925db937}} {{corpus:Q6/p2:change_a2:0:15:sha=fc91fd9d8fde:shape=R15-0-20}}"
                     "{{corpus:Q6/p2:change_a2:16:35:sha=6b00a360f5ed}}\" leaves the video games exactly as they "
                     "were — participant 2 lost 1.25 for it, the grader writing "
                     "\"{{corpus:Q6/p2:affect_c2:3:39:sha=7bc493d62ecd}} does not change your "
                     "{{corpus:Q6/p2:state_a2:17:50:sha=7f56e7f06c95}}\", and the 2.5/10 worked "
                     "example is the same failure twice over. But the test is NOT "
                     "whether the goal behaviour is mentioned — it is whether "
                     "anything in the clause OPERATES ON the antecedent, and the goal "
                     "behaviour is very often named as the change's expected RESULT. "
                     "Participant 10's \"{{corpus:Q6/p10:state_a1:0:38:sha=9aad2e64744a:shape=R0-1-63,R38-0-20}}"
                     "{{corpus:Q6/p10:state_a1:39:80:sha=f413b225ecc0}} gym\" counts: vague, "
                     "but it acts on the laziness. So does participant 3's \"{{corpus:Q6/p3:change_a1:0:2:sha=125466b821c6:shape=R0-1-62,R2-0-20}}"
                     "{{corpus:Q6/p3:change_a1:3:66:sha=ae10618ca6a3:shape=R63-0-20}}"
                     "{{corpus:Q6/p3:change_a1:67:70:sha=e326cff641fb}}\" against an antecedent of thinking exercise is "
                     "unnecessary — the motivation acts on that belief and the gym is "
                     "what follows from it; that response earned 10/10",
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
                "desc": "Describes HOW the second antecedent will be changed — the same "
                     "test as `change_a1` above: judge what the change ACTS ON, and "
                     "answer `not_described` when the clause only has the student "
                     "doing their goal behaviour instead of touching the antecedent",
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
                "desc": "Describes HOW the first consequence will be affected",
                "codes": {"absent": "C_NO_EFFECT", "not_described": "C_NO_EFFECT"},
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
                "desc": "Describes HOW the second consequence will be affected",
                "codes": {"absent": "C_NO_EFFECT", "not_described": "C_NO_EFFECT"},
            },
        ],
        "deductions": [
            {"code": "Q6_NONE", "pts": 10.0, "text": "did not answer"},
            {
                "code": "A_NOT_STATED",
                "pts": 1.25,
                "text": "Did not state the antecedent from question 4a that is being changed.",
                "repeatable": True,
            },
            {
                "code": "A_MISMATCH",
                "pts": 1.25,
                "text": (
                    "This is a different antecedent from what you listed in question 4a. The "
                    "antecedents must match up."
                ),
                "repeatable": True,
            },
            {
                "code": "A_NO_CHANGE",
                "pts": 1.25,
                "text": "You do not describe how the antecedent(s) from question 4a will be changed.",
                "repeatable": True,
            },
            {
                "code": "C_MISMATCH",
                "pts": 1.25,
                "text": (
                    "This is a different consequence from what you listed in question 4c. The "
                    "consequences must match up."
                ),
                "repeatable": True,
            },
            {
                "code": "C_NO_EFFECT",
                "pts": 1.25,
                "text": (
                    "You do not describe how the consequence(s) will be affected by changing "
                    "the antecedent(s)."
                ),
                "repeatable": True,
            },
            {
                "code": "C_NOT_STATED",
                "pts": 1.25,
                "text": "Did not state the consequence being affected.",
                "repeatable": True,
            },
        ],
        "guidance": [
            "WORK THE EIGHT SLOTS IN ORDER. This item is a checklist, not an impression. "
            "Walk them one at a time and decide each independently: "
            "(1) is antecedent 1 stated, and does it match 4a? "
            "(2) is the change to antecedent 1 described? "
            "(3) is antecedent 2 stated, and does it match 4a? "
            "(4) is the change to antecedent 2 described? "
            "(5) is consequence 1 stated, and does it match 4c? "
            "(6) is the effect on consequence 1 described? "
            "(7) is consequence 2 stated, and does it match 4c? "
            "(8) is the effect on consequence 2 described?",
            "ANSWER ALL EIGHT, INDEPENDENTLY. You must return a verdict for every slot, "
            "even after you have found several failures. Do not stop early: a response can "
            "fail six of eight and still read fluently. Across this cohort the graders "
            "found 50 failed slots in 20 responses — an average of 2.5 per student — so a "
            "verdict sheet with only one or two failures is more likely to be an incomplete "
            "reading than a strong answer.",
            "PRESENCE IS NOT WORDING. Be generous about how loosely something is phrased "
            "and strict about whether it is there at all. \"{{corpus:Q6/p10:state_a1:0:30:sha=9b7a726ad937:shape=R30-0-20}}"
            "{{corpus:Q6/p10:state_a1:31:80:sha=4b7ea6c60a23}} gym\" describes a change "
            "(participant 10, full credit) — loose but present. A paragraph that flows well "
            "while never naming the second consequence has an absent slot, however polished "
            "it reads.",
            "Slot verdicts: `met` when the element is present; `absent` when it is not there "
            "at all; `mismatch` when it IS there but is a different antecedent/consequence "
            "from the one in 4a/4c; `not_described` for a change/effect slot where the "
            "element is named but nothing is said about how it changes or is affected.",
            "Mismatch means a DIFFERENT item, not a reworded one. Participant 11 restated "
            "theirs in the template's own phrasing and earned 10/10. But participant 5's "
            "first antecedent was genuinely a different one from 4a and cost 1.25.",
            "A whole missing half — second antecedent and second consequence never "
            "addressed — is four absent slots and therefore 5.0, which is what participants "
            "17 and 19 lost.",
            "Cross-item matching is still the most common deduction in the corpus (14 of 20 "
            "gold rows carry Q6 feedback), so check each stated antecedent against 4a and "
            "each stated consequence against 4c before crediting the slot.",
            # REVERTED — a fifth Q6 attempt added four bullets here tightening the
            # consequence slots ("a hoped-for improvement is not a stated
            # consequence"; "work the halves as pairs"). Measured on the held-out
            # 17 it made things worse: exact 59% -> 47%, MAE 0.60 -> 0.75, two
            # cells lost and none gained. It did nudge slot detection 37 -> 39 of
            # 41 and bias +0.31 -> +0.16, so the diagnosis was not wrong — the
            # extra failures simply landed on the wrong slots. Recorded so the
            # experiment is not repeated; see README for the full Q6 history.
            "The grader's model answer template: \"I can change my first antecedent of ___ "
            "by ___. This will impact my first consequence of ___ by ___. I can change my "
            "second antecedent of ___ by ___. This will impact my second consequence of ___ "
            "by ___.\"",
        ],
        # Worked slot sheets taken from gold rows whose feedback pins every
        # verdict unambiguously. These three participants are excluded from
        # the reported baseline (`baseline_h1.py --exclude 10 8 6`) so the
        # numbers are not self-graded.
        "exemplars": [
            {
                "label": "Full credit (10/10) — loose phrasing still counts",
                "four_a": "1) One antecedent {{corpus:Q4a/p10:first:15:56:sha=fd3248412832:shape=R4-1-27,R22-1-27,R41-0-20}}"
                "{{corpus:Q4a/p10:first:57:80:sha=51e84f140771}} 2) {{corpus:Q4a/p10:second:0:44:sha=e27e50ead11b:shape=R23-1-27,R44-0-20}}"
                "{{corpus:Q4a/p10:second:45:116:sha=132419e793e8:shape=A41}}",
                "four_c": "1) The consequences ... {{corpus:Q4c/p10:first:75:108:sha=37a8e37cae81:shape=R33-0-20}}"
                "{{corpus:Q4c/p10:first:109:125:sha=91da0769130d}} doing {{corpus:Q4c/p10:first:132:173:sha=954012fdd8ff}} "
                "2) Another consequence ... {{corpus:Q4c/p10:second:78:118:sha=becf00cba25e}}",
                "response": "1) {{corpus:Q6/p10:state_a1:0:52:sha=8c66e1c1fbd7:shape=R52-0-20}}"
                "{{corpus:Q6/p10:state_a1:53:85:sha=40713632e5d9}} {{corpus:Q6/p10:change_a1:0:41:sha=f7dbb3eed805:shape=R41-0-20}}"
                "{{corpus:Q6/p10:change_a1:42:92:sha=ef453b54b9fc}} {{corpus:Q6/p10:affect_c1:0:20:sha=c4f7d36e7b67:shape=R1-1-27,R20-0-20}}"
                "{{corpus:Q6/p10:affect_c1:21:78:sha=2e524bba1c6d}} 2) {{corpus:Q6/p10:state_a2:0:14:sha=29d5a2355160:shape=R14-0-20}}"
                "{{corpus:Q6/p10:state_a2:15:86:sha=68e97c683c8a:shape=R71-0-20}}"
                "{{corpus:Q6/p10:state_a2:87:91:sha=71397d8edad6}} This will help reduce {{corpus:Q6/p10:change_a2:23:49:sha=865ea5a35836}} confidence. {{corpus:Q6/p10:affect_c2:0:9:sha=b59d06570e99:shape=R9-0-20}}"
                "{{corpus:Q6/p10:affect_c2:10:83:sha=0711056b4030}}",
                "slots": {
                    "state_a1": "first",
                    "change_a1": "met",
                    "state_a2": "second",
                    "change_a2": "met",
                    "state_c1": "first",
                    "affect_c1": "met",
                    "state_c2": "second",
                    "affect_c2": "met",
                },
                "note": "Every slot is loosely worded and every slot counts. "
                "\"{{corpus:Q6/p10:state_a1:0:49:sha=e50c84f0c5e6}}\" is a described "
                "change. \"Good standing mentally\" is the 4c mental-health consequence "
                "being affected. Do not demand the template's phrasing.",
            },
            {
                "label": "2.5/10 — antecedents named, but NO change to them described",
                "four_a": "My first antecedent {{corpus:Q4a/p8:first:19:58:sha=07eee26c9712}} gym. "
                "{{corpus:Q4a/p8:first:80:120:sha=ca075a14481c}} instead. {{corpus:Q4a/p14:second:0:20:sha=53ee3e1ca1b7:shape=R20-0-20}}"
                "{{corpus:Q4a/p14:second:21:26:sha=85574fa07dae}} {{corpus:Q4a/p8:second:32:60:sha=5b52d61bab20}} {{corpus:Q4a/p8:second:65:101:sha=2e6b1979b4e7}}",
                "four_c": "{{corpus:Q4c/p8:first:0:65:sha=ddc3d5d5b61a:shape=R65-0-20}}"
                "{{corpus:Q4c/p8:first:66:117:sha=e3c5e939f9a8}} One consequence ... is "
                "that I have 0 motivation {{corpus:Q4c/p8:second:83:135:sha=d1b9021dfddc}}",
                "response": "{{corpus:Q6/p8:state_a1:0:63:sha=a97f185e6b29:shape=R63-0-20}}"
                "{{corpus:Q6/p8:state_a1:64:103:sha=b43718edaa81}} Which then makes me wish I would "
                "have just gone to the gym. {{corpus:Q6/p8:change_a1:0:45:sha=fd39aa6d7171}}"
                "{{corpus:Q6/p8:change_a1:46:108:sha=38547eb33304}} {{corpus:Q6/p8:state_a2:0:13:sha=86103d589b67:shape=R13-0-20}}"
                "{{corpus:Q6/p8:state_a2:14:89:sha=24b11e6ff583:shape=R75-0-20}}"
                "{{corpus:Q6/p8:state_a2:90:98:sha=781c69a55b23}} which can lead to {{corpus:Q1/p8:response:206:236:sha=a6fc82d76be7}} {{corpus:Q6/p8:change_a2:0:15:sha=75cbe638b990:shape=R15-0-20}}"
                "{{corpus:Q6/p8:change_a2:16:82:sha=9ca39f0393b5}} {{corpus:Q6/p8:change_a2:94:103:sha=c8acaba8410c:shape=R9-0-20}}"
                "{{corpus:Q6/p8:change_a2:104:127:sha=2f7d05e17f5c}} progress.",
                "slots": {
                    "state_a1": "second",
                    "change_a1": "not_described",
                    "state_a2": "first",
                    "change_a2": "not_described",
                    "state_c1": "absent",
                    "affect_c1": "absent",
                    "state_c2": "absent",
                    "affect_c2": "absent",
                },
                "note": "THE MOST IMPORTANT CASE. Both antecedents are named, so both "
                "state slots are met. But \"{{corpus:Q6/p8:change_a1:10:31:sha=59e2c4a3daa0}} Tuesday-Friday\" and "
                "\"{{corpus:Q6/p8:change_a2:9:52:sha=02595bb7f918}} week\" describe DOING THE "
                "GOAL BEHAVIOUR, not changing the antecedent of laziness or of playing "
                "video games. A plan to perform the WGB is not a change to the antecedent, "
                "so both change slots are not_described. Neither 4c consequence is named "
                "at all, so all four consequence slots are absent. The grader wrote "
                "\"did not say how each antecedent is being changed\" and \"did not state "
                "each consequence being affected\".",
            },
            {
                "label": "6.25/10 — a mismatch plus a missing second consequence",
                "four_a": "{{corpus:Q4a/p6:first:0:63:sha=e72260775380}} "
                "{{corpus:Q4a/p6:second:0:56:sha=653e13080568}} days.",
                "four_c": "One consequence ... {{corpus:Q4c/p6:first:47:91:sha=0e6aa9251262}} "
                "distances. Another consequence ... {{corpus:Q4c/p6:second:51:88:sha=240afc732327:shape=R37-0-20}}"
                "{{corpus:Q4c/p6:second:89:122:sha=cad40cfd81e8}}",
                "response": "I will be changing my antecedent of {{corpus:Q6/p6:state_a1:0:21:sha=641b355f6e09}} & "
                "{{corpus:Q6/p6:state_a2:4:38:sha=56244251ed73}}, which results in muscle soreness and "
                "little to no flexibility. {{corpus:Q6/p6:change_a1:0:47:sha=aed3edbee4fd:shape=R47-0-20}}"
                "{{corpus:Q6/p6:change_a1:48:93:sha=e20ad9ff6cb3}} while stretching daily. When "
                "I start to become more active within myself, {{corpus:Q6/p6:state_c1:0:28:sha=181ea9bc0d48:shape=R28-0-20}}"
                "{{corpus:Q6/p6:state_c1:29:91:sha=5d81e93589a7}} {{corpus:Q6/p6:affect_c1:0:10:sha=c6c0397c55b7:shape=R10-0-20}}"
                "{{corpus:Q6/p6:affect_c1:11:57:sha=e908dbb31d95}}",
                "slots": {
                    "state_a1": "first",
                    "change_a1": "met",
                    "state_a2": "neither",
                    "change_a2": "met",
                    "state_c1": "second",
                    "affect_c1": "met",
                    "state_c2": "absent",
                    "affect_c2": "absent",
                },
                "note": "The second antecedent addressed here is \"{{corpus:Q6/p6:state_a1:0:21:sha=641b355f6e09}}\", "
                "which is not 4a's \"not being motivated\" — that is a mismatch, not an "
                "absence. Only one 4c consequence (stiffness) is picked up; the second is "
                "never named, so both of its slots are absent.",
            },
            # REVERTED — a FOURTH exemplar (participant 15: both antecedents
            # handled, all three losses on the consequence side) was added to
            # demonstrate the one failure mode the other three do not show. It
            # was chosen to hold the demonstration set's balance at exactly 62.5%
            # met, addressing the suspected cause of the v8 failure. It still
            # made things worse on an identical held-out 16: Q6 exact 62% -> 44%,
            # MAE 0.56 -> 0.80, bias +0.25 -> +0.33. Three exemplars appears to
            # be the working number for this item; a fourth dilutes rather than
            # adds, regardless of which failure mode it demonstrates.
            # REVERTED — two further exemplars (participants 5 and 17) were tried
            # here and measured WORSE on an identical held-out 15: Q6 exact fell
            # 60% -> 47%, MAE rose 0.60 -> 0.85, bias rose +0.43 -> +0.52. Both
            # were heavily "met"-weighted (24 met vs 16 unmet across five
            # exemplars, against 12 vs 12 across three), which appears to have
            # pushed the item further toward the leniency it already had, and
            # diluted the decisive participant-8 case. Kept as a comment so the
            # experiment is not silently repeated. Do not re-enable without
            # re-measuring held-out.
        ],
        "context": ["Q1", "Q2", "Q4a", "Q4c"],
    },
]

BY_ID = {it["id"]: it for it in ITEMS}
TOTAL = sum(it["max"] for it in ITEMS)  # 45.0 scored; +5 upload = 50
