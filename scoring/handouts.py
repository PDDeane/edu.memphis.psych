"""Per-handout wiring: where the files are, how to split them, what scores them."""

from __future__ import annotations

import glob
import os
import re

import gold as gold_mod
import rubric_h1
import rubric_h2
import rubric_h3
from segment import H1_MARKERS, H2_MARKERS, H3_MARKERS

import paths

# ROOT used to be one directory. It is now three: the blank templates ship
# with the code (MATERIALS), the filled-in submissions never enter git
# (SUBS), and run output is scratch (OUT). See paths.py.
MATERIALS = paths.MATERIALS
SUBS = paths.SUBS
OUT = paths.OUT

HANDOUTS: dict[int, dict] = {
    1: {
        "rubric": rubric_h1,
        "template": f"{MATERIALS}/BMod Handout #1 - Defining Behaviors, ABCs, and SMART Goals.docx",
        "submissions": f"{SUBS}/Handout 1 Submissions with Scoring and Feedback",
        "markers": H1_MARKERS,
        "capture_tail": False,
        "outdir": f"{OUT}/h1",
        "gold": gold_mod.load_h1,
        "blurb": (
            "Handout 1 of the Behavior Modification Assignment: defining behaviours, "
            "the ABCs of a functional behavioural analysis, and SMART goals."
        ),
        # Participants whose responses appear as few-shot exemplars in the
        # rubric, so scoring them would be self-grading.
        # p6 is an UNSTABLE exemplar and is kept as a diagnostic. Its whole
        # answer and its 6.25 are printed in Q6's prompt, and the scorer
        # reproduces that score in only 6 of 12 runs — unanimous one way in one
        # pass and the other way in the next. It is not a step-1 removal: taking
        # the citation out would mean deleting a worked example the prompt is
        # built around. Watch it while tuning Q6's slot judgements; it should
        # stop flipping when they stabilise, which reads independently of the
        # counted rate. See EQUIVALENCE.md, "Cleaning up an item".
        "exemplar_participants": [10, 8, 6],
        # ...but only on the items whose PROMPT actually embeds them. Verified
        # against the rubric: Q6 is the sole item with an `exemplars` field, and
        # the three bodies reproduce p10, p8 and p6 verbatim. Their Q1..Q5
        # answers appear in no prompt, so dropping them there discarded 21 cells
        # for nothing. See exemplar_drops() below.
        # Empty since Q6 was rewritten from the dictionary: it no longer
        # reproduces anyone's answer, so no cell on it is self-graded. The
        # handout-wide `exemplar_participants` list above is now inert for
        # handout 1 and kept only so a future item can opt in by naming itself.
        "exemplar_items": [],
        # A SECOND way a prompt can give the answer away, found by auditing every
        # item's prompt-bearing text for a participant cited by number.
        #
        # `exemplar_items` covers a response reproduced in full as a worked
        # example. This covers a response CITED as calibration — "falling asleep
        # in the car ... cost participant 20 three points" — which quotes the
        # answer AND states the grader's decision. That is an answer key for that
        # cell just as surely, so scoring the cited participant on that item is
        # self-grading too.
        #
        # Per item, because the sets differ: Q6 embeds p10/p8/p6, Q4b cites eight
        # entirely different participants. The handout-wide `exemplar_participants`
        # list cannot express that, which is why registering Q4b needed this.
        #
        # All ten qualifying items, registered together after the evidence came
        # in. Q4b was registered first, alone; measuring it then showed the whole
        # 21-point web/paper gap on that item was Opus reproducing answers held
        # in its prompt (7/7 on cited cells) where gpt-5-mini did not (4/7),
        # while on the cells that should be judged the three scorers were
        # equivalent — 12, 11 and 10 of 12. Leaving the other nine unregistered
        # would have kept that distortion in every handout-1 and handout-3 number.
        #
        # Reproduce with the audit in EQUIVALENCE.md: search each item's
        # prompt-bearing text for a participant cited by number. Handout 2 has
        # none — its guidance quotes answers without attributing them.
        "cited_participants": {
            "Q1":  [1, 2, 6, 9, 10, 16],
            "Q2":  [3, 6, 7, 10],
            "Q4a": [3, 4, 6, 9, 14, 15, 17],
            # Q4b cites only its ACCEPT cases now. 2, 4, 6, 7 and 20 came OUT of the
            # guidance rather than staying in it and being excluded: the item could
            # not score them right even with the answer written beside them, so
            # excluding them reported a rate over the cells it can do. They are
            # counted now, and expected to be wrong. See EQUIVALENCE.md.
            "Q4b": [13, 15, 19],
            "Q4c": [4, 9, 11, 12, 15, 17, 20],
            "Q5":  [4, 6, 8, 9, 19, 20],
            # Q6 is gone from this map: rewritten from the dictionary, its
            # prompt cites no participant at all. Every cell on it is scoreable
            # now except p9, which is unreachable for a declared divergence.
        },
    },
    2: {
        "rubric": rubric_h2,
        "template": (
            f"{MATERIALS}/BMod Handout #2 - Learning Operant Conditioning and "
            "Applying It to Behavior Change.docx"
        ),
        "submissions": f"{SUBS}/Handout 2 Submissions with Scoring and Feedback",
        "markers": H2_MARKERS,
        "capture_tail": True,
        "repair_orphans": True,
        "outdir": f"{OUT}/h2",
        "gold": gold_mod.load_h2,
        "blurb": (
            "Handout 2 of the Behavior Modification Assignment: applying the four types "
            "of operant conditioning to the student's own behaviour-change plan."
        ),
        "exemplar_participants": [],
        # Participants 2 and 3 have byte-identical transcriptions but different
        # gold rows, so at least one is mis-transcribed and neither can be
        # attributed. Excluded from reported metrics; see README.
        "suspect_participants": [2, 3],
    },
    3: {
        "rubric": rubric_h3,
        "template": (
            f"{MATERIALS}/BMod Handout #3 - Presenting Data, Graphing Data, "
            "&amp_ Analyzing Your Intervention.docx"
        ),
        "submissions": f"{SUBS}/Handout 3 Submissions with Scoring and Feedback",
        "markers": H3_MARKERS,
        "capture_tail": True,
        "join_aware": True,
        "outdir": f"{OUT}/h3",
        "gold": gold_mod.load_h3,
        "blurb": (
            "Handout 3 of the Behavior Modification Assignment: presenting and graphing "
            "the data collected during the intervention, and analysing the result."
        ),
        "exemplar_participants": [],
        # See handout 1's entry. 1c is also the item that cannot be scored at all
        # by a backend without image tools — a separate problem, declared in
        # BACKEND_DEVIATIONS below.
        "cited_participants": {
            "1a": [1, 6, 15],
            "1c": [4, 8, 20],
            "2a": [1, 14],
        },
    },
}


def config(handout: int) -> dict:
    if handout not in HANDOUTS:
        raise SystemExit(f"unknown handout {handout}; have {sorted(HANDOUTS)}")
    return HANDOUTS[handout]


def find_submissions(handout: int, pids: list[int] | None = None) -> list[tuple[int, str]]:
    cfg = config(handout)
    out = []
    for f in sorted(glob.glob(os.path.join(cfg["submissions"], "*.docx"))):
        m = re.search(r"ID\s*(\d+)", os.path.basename(f))
        if not m:
            continue
        pid = int(m.group(1))
        if pids and pid not in pids:
            continue
        out.append((pid, f))
    return sorted(out)


def excluded(handout: int) -> list[int]:
    """Participants that must not count toward a reported baseline.

    Handout-wide, exemplars included. Kept as-is for baseline.py, which measures
    score.py: that engine drops per RUN rather than per item, and its Q6 prompt
    carries the same exemplars, so narrowing here would silently make its
    reported baseline self-grading.
    """
    cfg = config(handout)
    return sorted(
        set(cfg.get("exemplar_participants", [])) | set(cfg.get("suspect_participants", []))
    )


def suspect(handout: int) -> list[int]:
    """Participants whose INPUT cannot be trusted, whatever the item.

    Handout 2's p2 and p3 have byte-identical transcriptions but different gold
    rows, so at least one is mis-transcribed and neither can be attributed. That
    is a fact about the submission, so it holds for every item — unlike being an
    exemplar, which is a fact about one prompt.
    """
    return sorted(config(handout).get("suspect_participants", []) or [])


def exemplar_drops(handout: int) -> dict[str, list[int]]:
    """{item: [pid]} — exemplar participants, only on items that embed them.

    Self-grading is a property of a PROMPT, not of a handout. Scoring p10, p8 or
    p6 on Q6 grades a model on text it was shown; scoring them on Q1 does not,
    because their Q1 answers appear nowhere in Q1's prompt. Conflating the two
    cost 3 participants x 7 items = 21 cells of handout-1 evidence.
    """
    cfg = config(handout)
    out: dict[str, list[int]] = {}
    pids = sorted(cfg.get("exemplar_participants", []) or [])
    for item in cfg.get("exemplar_items", []) or []:
        if pids:
            out[item] = list(pids)
    # Per-item citations, merged rather than replacing: an item can both embed a
    # worked example and cite others as calibration.
    for item, cited in (cfg.get("cited_participants", {}) or {}).items():
        out[item] = sorted(set(out.get(item, [])) | set(cited or []))
    return out


# ── Deliberate divergences from gold ─────────────────────────────────────────
#
# Cells where the graders applied their OWN written rule inconsistently and both
# implementations apply it uniformly. These are decisions, not defects, and they
# were documented in README prose only — so every harness counted them as errors.
# That cost real conclusions: Q4a reads as one of handout 1's least accurate
# items at 80% exact / 92.8% per check, and is 94% / 98.0 once its three declared
# cells come out. And the DAY2 work was justified partly by "7 of 10 large errors
# are over-credit" when three of those were p8's declared avoidance-framing cells
# — the README says in terms, "anyone measuring the OC items should subtract them
# before concluding the criteria are too permissive."
#
# Distinct from three neighbouring ideas, all of which already exist:
#   olx_prompts.SCORING_DIVERGENCES  — where the WEB and CLI differ from each
#                                      other, not where either differs from gold
#   agreement.UNSCORED_GOLD_CRITERIA — criteria no slot scores at all
#   PER_ITEM_EXCLUDE                 — cells DROPPED, because nothing correct can
#                                      score them. A divergence is still scored;
#                                      we just knowingly disagree.
#
# Q6/9 and Q1/20 appear here for the record and are also in PER_ITEM_EXCLUDE, so
# they never reach a comparison. The other seven do.
GOLD_DIVERGENCES: list[dict] = [
    {
        "code": "ANTECEDENT_REUSED_AS_BEHAVIOR", "cells": [("Q4b", 4)],
        "why": "p4 gave \"scrolling on tiktok\" and \"becoming grumpy\" as their "
               "active behaviours, having already named \"scrolling through "
               "tiktok\" and \"having grumpy emotions\" as their 4a triggers. Gold "
               "charged both as repeats, -3. The scoring dictionary states no such "
               "rule; it was inferred from this cell. Reading all 40 antecedents "
               "in the corpus shows why it will not generalise: students name a "
               "state, circumstance, feeling or absence as the trigger — \"too "
               "cold outside\", \"feeling exhausted\", \"not seeing immediate "
               "results\" — and p4 is the ONLY one who names an ordinary activity, "
               "which is the only shape that can collide with an active behaviour. "
               "So the rule rests on one cell. Two implementations were measured "
               "and both were worse than not having it: a `repeats_antecedent` "
               "check answered `absent` on p4 in one run and `met` in the next "
               "while misfiring on p6 and p20 (spread 4), and a guidance clause "
               "fixed p4 but broke p1, p14 and p16 on surface wording and took the "
               "spread to 5. Both times the model matched the 4a SENTENCE rather "
               "than the trigger in it.",
    },
    {
        "code": "REASON_FOR_WRONG_BEHAVIOR", "cells": [("Q5", 4)],
        "why": "p4's first entry reads \"{{corpus:Q5/p4:first:0:40:sha=5adbcff99c0f:shape=R40-0-20}}"
               "{{corpus:Q5/p4:first:41:78:sha=dbee47176fe2}}\" — it names the OPPOSITE of "
               "the unwanted behaviour and gives a reason to change rather than a "
               "payoff for continuing. Gold credited it and charged only the second "
               "entry, so 2.5 of 5. Reproducing that needs a scorer to read through "
               "a dropped \"to not\" AND to accept \"sleep is good for you\" as a "
               "payoff for not sleeping, which contradicts the item's own "
               "W_NOT_REASON rule. All four engines — two prompts, two model "
               "families — classify it `not_reason` and score 0, in near-identical "
               "words. The rule 2 / rule 3 boundary added to the guidance places it "
               "in rule 3 as well, so this divergence is the deliberate consequence "
               "of drawing that line, not an oversight left in it.",
    },
    {
        "code": "A_NO_CHANGE",
        "cells": [("Q6", 8)],
        "why": (
            "gold charges BOTH change slots — \"did not say how each antecedent is "
            "being changed\" — for offering a scheduling commitment where the "
            "antecedent was stated as not doing the goal behaviour. p8's first "
            "antecedent is \"{{corpus:Q6/p8:state_a1:38:87:sha=2abb3dabb60a}}\" and "
            "the change is \"{{corpus:Q6/p8:change_a1:10:31:sha=59e2c4a3daa0}} from Tuesday-Friday\"; the second "
            "is \"staying {{corpus:Q6/p8:state_a2:39:93:sha=92366fb71e73}} gym\" "
            "and the change is \"{{corpus:Q6/p8:change_a2:9:52:sha=02595bb7f918}} week\". "
            "Read literally each change DOES negate the antecedent as the student "
            "framed it, because the student framed the antecedent as the absence of "
            "the goal behaviour. The graders applied the item's pedagogical point "
            "instead: an antecedent change alters what triggers the unwanted "
            "behaviour, it does not resolve to do the wanted one.\n\n"
            "Declared rather than chased because p6 is the same shape and gold "
            "CREDITS it. p6's antecedent is \"{{corpus:Q6/p6:state_a1:0:21:sha=641b355f6e09}} & {{corpus:Q6/p6:state_a2:4:17:sha=8fe41cf2d613:shape=R13-0-20}}"
            "{{corpus:Q6/p6:state_a2:18:35:sha=410129fe5640}}\" and its change is \"I {{corpus:Q6/p6:change_a1:14:40:sha=dda548773f8f:shape=R26-0-20}}"
            "{{corpus:Q6/p6:change_a1:41:88:sha=bd5bdfabcb36}} week\" — an absence-framed "
            "antecedent answered with a scheduling commitment, exactly like p8. No "
            "textual feature separates them, and three attempts confirmed it: a prose "
            "acts-on rule moved one of p8's two slots and stuck on the other; a "
            "reported-only classification probe had the model answer `antecedent` for "
            "both, which is correct on a literal reading; and a test keyed on "
            "absence-framed antecedents would flag six credited cells (p2, p3, p5, p6, "
            "p16, p19) to catch this one.\n\n"
            "The scorer treats p6 and p8 alike, which is the defensible position. "
            "p8 accounts for both of `change_a1`'s errors and `change_a2`'s only one, "
            "so with this declared those two slots are at ceiling."
        ),
    },
    {
        "code": "C_MISMATCH", "cells": [("Q6", 17)],
        "why": "p17 writes \"my {{corpus:Q6/p17:state_c1:32:82:sha=ef8f2e007fd6:shape=R50-0-20}}"
               "{{corpus:Q6/p17:state_c1:83:110:sha=e4aa52e14baa}} C)\" against a 4c listing weight gain "
               "and becoming unproductive. The scorer answers that this matches "
               "neither; gold credits it, deducting only for the second pair. The "
               "student is pointing at their own 4c — the phrasing is the "
               "template's own scaffold, which they filled — but they never name "
               "either consequence they listed, and one element (\"stressed\") is "
               "new. "
               "Declared rather than fixed, and the attempt is worth recording. "
               "Loosening `refers_to` to credit a paraphrase was implemented and "
               "MEASURED: Q6 went 16/19 -> 12/19. p5, p10 and p15 each moved off "
               "an exact score with no fixture change, so the loss is the rule's "
               "alone, and bias rose +0.14 -> +0.34. That is the A_MISMATCH "
               "warning coming true — crediting this paraphrase means teaching "
               "the check to credit real mismatches. "
               "Note gold applies the matching rule elsewhere in its own words: "
               "it refuses p1's first consequence \"(from 4c)\" when nothing is "
               "named, and charges p6 because the \"second antecedent is not the "
               "same as mentioned in 4a\". Gold is not ignoring the requirement "
               "here; it is drawing the line more generously on one paraphrase, "
               "and we draw it where the dictionary does. "
               "ASKED SEPARATELY whether gold could be made reachable at no cost "
               "to other cells, and it cannot. p17 needs a FOURTH credited slot "
               "to reach 5.00, and state_c1 is the only candidate — the second "
               "pair's boxes are empty and gold deducts them too. Three routes "
               "reach it, all priced: loosening `refers_to` to credit a "
               "paraphrase was measured at 16/19 -> 12/19; dropping the matching "
               "requirement from the c-slots would credit p1's \"{{corpus:Q6/p1:state_c1:0:14:sha=c5af2a053212:shape=R14-0-20}}"
               "{{corpus:Q6/p1:state_c1:15:56:sha=65b7abc7c7e3}} this\", which names no "
               "consequence and which gold refuses in terms (\"did not state the "
               "first consequence (from 4c)\"), so p1 gains 1.25 it should not "
               "have; and the only fixture route is to move the clause the "
               "student labelled (UTB) — sitting at home scrolling on their "
               "phone, which does resemble 4c's second entry — into a consequence "
               "box, which is putting text in a box against the student's own "
               "labelling, the error reverted twice already on 2a/p18 and Q6/p8. "
               "So the cell stays a declared miss. Excluding it would raise the "
               "rate to 15/18 without making anything reachable, and that is a "
               "denominator decision, not a fix",
    },
    {
        "code": "A_MISMATCH", "cells": [("Q6", 9)],
        "why": "p9's Q6 changes a third antecedent not listed in their 4a. The "
               "dictionary is explicit that the antecedents must match up, so "
               "`state_a1` is a mismatch; gold scored it met. The lo-blocks "
               "prompt returned `mismatch` in five runs of five — matching gold "
               "would mean teaching the check to credit real mismatches.",
    },
    {
        "code": "A_NO_KEYWORD", "cells": [("Q4a", 9), ("Q4a", 15)],
        "why": "the dictionary requires the word \"antecedent\" or \"trigger\". "
               "p17 lost the point for omitting it; p9 and p15 did not. Applied "
               "uniformly. Contrast Q4c, whose equivalent charge was REMOVED "
               "today because no gold row applies it at all — the difference is "
               "evidence, not consistency for its own sake.",
    },
    {
        "code": "A_NOT_ANTECEDENT", "cells": [("Q4a", 14)],
        "why": "gold refused both of p14's examples (-4 = two refusals) while its "
               "commentary accounts for only one, and the first — \"not seeing "
               "immediate results\" — is the state-of-mind case the item's own "
               "guidance says to accept. Credited in five runs of five.",
    },
    {
        "code": "AVOIDANCE_FRAMING", "cells": [("DAY1", 8), ("WK1", 8), ("WK2", 8)],
        "why": "p8's contingencies are stated by what is AVOIDED (\"so I don't "
               "have to {{corpus:DAY1/p8:day1:105:127:sha=902613cf68e4}} if...\"), which is structurally "
               "sound: a consequence is still arranged and still contingent. The "
               "graders read the phrasing as a failure; score.py flags for review "
               "and never deducts, and the lo-blocks sheet reaches the same "
               "verdict. Both sides are 4, 4 and 2 points over gold BY DESIGN — "
               "the largest of these by cell count.",
    },
    {
        "code": "WRONG_DEFINITION", "cells": [("D2", 11)],
        "why": "p11 chose Negative Reinforcement and defined Negative Punishment. "
               "The grader diagnosed it correctly but charged -1 and left the "
               "score at 1.0; the dictionary puts WRONG_DEFINITION at -2. Both "
               "implementations score 0, so both are 1 point UNDER gold — the "
               "only one of these where the divergence is downward.",
    },
]


def gold_divergence(item: str, pid: int) -> str | None:
    """The divergence code for one cell, or None. See GOLD_DIVERGENCES."""
    for d in GOLD_DIVERGENCES:
        if (item, pid) in d["cells"]:
            return d["code"]
    return None


def gold_divergence_cells() -> dict[tuple[str, int], str]:
    """{(item, pid): code} for every declared cell."""
    return {c: d["code"] for d in GOLD_DIVERGENCES for c in d["cells"]}


# ── Measurement ceilings ─────────────────────────────────────────────────────
#
# Why no correct scorer reaches 100%, per item, with the evidence. A FOURTH kind
# of gold caveat, and the distinctions matter:
#
#   GOLD_DIVERGENCES         we disagree with a grader on purpose, on named cells
#   PER_ITEM_EXCLUDE         cells dropped, nothing correct can score them
#   agreement.UNSCORED_GOLD_CRITERIA
#                            criteria NO slot scores at all
#   GOLD_CEILINGS (here)     criteria that ARE scored, on cells gold itself does
#                            not decide consistently — so some are unwinnable
#                            whichever consistent rule you adopt, and which ones
#                            depends on the rule
#
# The practical use is to stop a ceiling reading as headroom. Q3 sits at 75% and
# looks like 25% of work available; about 10% of it does not exist.
#
# Q6 p4 was listed here and is NOT any more. Its gold of 6.00 implies 3.2 slots
# of 1.25, so no slot-derived score can land on it — but that is now HANDLED
# rather than merely explained: scores_as_exact() credits the nearest reachable
# value, so a scorer returning 6.25 is counted correct and the cell is neither a
# ceiling nor headroom. A note here would tell a reader there is unwinnable
# ground where there is none.
#
# Contrast DAY2 p7 below, which stays. Its gold of 1.00 IS reachable; it just
# does not reconcile with its own itemised comment. Nothing computes that away,
# so it remains a real ceiling.
GOLD_CEILINGS: dict[tuple[str, str], tuple[str, ...]] = {
    ("1", "Q6"): (
        "`change_a1`/`change_a2`: whether a stated action actually CHANGES the "
        "antecedent it is paired with, rather than improving the goal behaviour, "
        "cannot be scored consistently against gold, and the cells that go wrong "
        "depend on which rule you adopt. p2 is over-credited: its second "
        "antecedent is a pastime and its change makes the exercise more pleasant, "
        "which gold refuses in terms — \"{{corpus:Q6/p2:affect_c2:3:39:sha=7bc493d62ecd}} does "
        "not change your antecedent of {{corpus:Q6/p2:state_a2:31:69:sha=953a77829719:shape=R38-0-20}}"
        "{{corpus:Q6/p2:state_a2:70:74:sha=6c45cb72a36e}}\" — while both scorers credit it. "
        "MEASURED, three wordings, none of which separates it. A rule asking "
        "whether the action improves the goal behaviour instead of the trigger "
        "fixed p2 and cost p3 and p5, both of which state a real action followed "
        "by a purpose clause (\"by X, which will help me Y\") that reads as goal "
        "language. Ignoring the purpose clause and testing the trigger's object, "
        "occasion and supply held p3 and p5 and lost p2. Naming p2's shape "
        "concretely — an action improving the conditions of the exercise while the "
        "trigger is a different activity — held p3 and lost p5. "
        "The reason is that p5's credited action changes the SUPPLY at the trigger "
        "moment while p2's changes a different activity, and both read as "
        "providing something more pleasant. A_NO_CHANGE predicted exactly this: it "
        "records that a test of this shape \"would flag six credited cells (p2, "
        "p3, p5, p6, p16, p19) to catch this one\", and p2, p3 and p5 are the "
        "three that moved. Six attempts across the project now, three of them "
        "measured here. "
        "p10 is the same criterion in its other form: a BORDERLINE FLIP rather than "
        "a stable error. Its change_a1 states what changing the antecedent will do "
        "for the student — give them discipline, produce a routine — without ever "
        "naming a method, and \"produce a routine\" is arguably itself a method, so "
        "the judgement is genuinely close. The scorer answers `incomplete` "
        "sometimes and `met` sometimes: 1 of 3 passes in one sweep, 3 of 3 in the "
        "next, on identical input. Gold credits it. Do not read a change in p10 as "
        "a change in the system — it moved from exact to a miss between two sweeps "
        "with no fixture and no prompt difference between them, purely on which "
        "way the flip landed. "
        "So both cells sit on the same unwinnable criterion, one stably and one by "
        "coin-flip, and this is a ceiling rather than headroom: Q6's practical "
        "maximum is 18 of 19 cells, not 19.",
    ),
    ("1", "Q3"): (
        "`action_oriented`: five answers justify the goal by CAPABILITY rather "
        "than by naming an action, and gold splits them — p14 (\"my {{corpus:Q3/p14:action:63:77:sha=e1ed3fd8af96:shape=R14-0-20}}"
        "{{corpus:Q3/p14:action:78:108:sha=6ffe1a32e5b6}} house\") and p18 (\"{{corpus:Q3/p18:action:64:84:sha=a23e8ae750f0:shape=R20-0-20}}"
        "{{corpus:Q3/p18:action:85:101:sha=0fddaf85b380}}\") are CREDITED, while p8 (\"I will be able to make time\"), "
        "p16 (\"{{corpus:Q3/p16:action:58:90:sha=d23f7525fb29}}\") and p20 (\"{{corpus:Q3/p20:action:80:97:sha=3664422a464d}} "
        "asleep\") are DEDUCTED. Same claim, opposite verdicts. Any consistent rule "
        "gets at most 3 of those 5, so >=2 cells are unwinnable and 18/20 is the "
        "ceiling. Measured: the other four SMART slots are 0-2 errors each, this "
        "one is 4-5, and a 'labelled Action section' rule matches gold on only "
        "12/20 — worse than the models manage without it.",
    ),
    ("2", "DAY2"): (
        "p7's gold is 1.00 while its comment itemises only \"-1 pt\", which implies "
        "3.00. The row does not reconcile with itself, so 1.00 is unreachable by "
        "any scorer that charges the stated deduction. WK1 p7 is the same shape.",
    ),
}


def gold_ceiling(handout: int, item: str) -> tuple[str, ...]:
    """Why this item cannot reach 100% — one entry per ceiling, () if none.

    A tuple rather than a string because an item can hit more than one ceiling
    for unrelated reasons: Q2 has both `reasons_given` (an uncountable
    distinctness judgement) and `wgb_inverts_utb` (substitution vs outcome
    decided both ways). Joined into one string, every caller's summary line
    would show the first and silently drop the rest.
    """
    got = GOLD_CEILINGS.get((str(handout), item)) or ()
    return (got,) if isinstance(got, str) else tuple(got)


# Gold criteria that neither system scores, declared rather than left to be
# rediscovered. An omission that is SYMMETRIC costs the head-to-head nothing —
# both columns miss it identically — but an undeclared one is indistinguishable
# from a bug, which is the whole reason this list exists.
#
#   1c, "missing baseline data week" (p11, -1): the only instance in 20 rows,
#   and unreachable on the web by construction. The chart is drawn by
#   SelfMonitorPlot from the four data fields, so a populated baseline series is
#   necessarily plotted — p11's `baseline` field holds "{{corpus:1a/p6:baseline:0:19:sha=66e4f9120272}} 30",
#   which is why their 1b scored a full 4.0. The grader is marking a series
#   absent from a hand-drawn paper graph whose data table contained it. Adding a
#   slot for it would have no reachable failing state: with baseline data present
#   the web always plots it, and with baseline data absent 1b already takes the
#   point, so the slot could only double-count or misfire. Note also that p11's
#   row does not self-reconcile — it itemises -2/-2/-1 against a score of 7.0 —
#   so rebuild_gold_1c derives from the itemised deductions, not the total.
# Cells where the gold row cannot be scored on the item it sits in, dropped from
# that item only. Mirrors PER_ITEM_EXCLUDE in agreement_app.py; the two sides
# must drop the SAME cells or the item's two columns stop being a comparison.
PER_ITEM_EXCLUDE: dict[str, dict[int, str | dict]] = {
    "Q6": {
        # Rewritten after measurement contradicted the original reason, which said
        # the fixture tie-break decided 2 of 8 slots and that "the CLI's error here
        # is exactly -2.50". Both halves were false. The tie-break DID put the text
        # in state_c2 and leave affect_c2 empty — and the scorer answers `mismatch`
        # on state_c2 and `absent` on affect_c2, which is exactly what gold charges
        # ("-2.5 pts: missing second consequences"). The arbitrary split landed on
        # gold's own answer and cost nothing.
        #
        # The real reason is the divergence, and it is a clean one: the scorer
        # agrees with gold on SEVEN of eight slots, and the eighth is `state_a1`,
        # where it answers `mismatch` and gold credits. That is the declared
        # A_MISMATCH divergence — p9's Q6 changes a third antecedent not listed in
        # their 4a, and the dictionary is explicit that the antecedents must match
        # up. Gold is unreachable because gold is lenient there and we are not, so
        # a miss stays EXPECTED; the error is one slot, not two.
        9: {
            "why": "gold credits `state_a1`, which is a third antecedent not "
                   "listed in this participant's 4a — the declared A_MISMATCH "
                   "divergence, where the scorer is right and gold is lenient. "
                   "Note HOW that now shows up: the verdict on `state_a1` is "
                   "`met`, and it is `refers_to: none` — matching neither listed "
                   "antecedent — that makes the cover logic demote it. Reading "
                   "verdicts alone would say the scorer agrees with gold here, "
                   "and it does not. The fixture is also reconstructed (the "
                   "state_c2/affect_c2 split came from a 5/5 tie-break across "
                   "ten runs, the SAME split on both sides), but that is not "
                   "what makes the cell unscoreable: the tie-break agrees with "
                   "gold on both slots. "
                   "One slot, not two. `affect_c1` used to disagree as well, "
                   "answering `incomplete` where gold credits, and that was a "
                   "FIXTURE fault rather than a scoring one: the clause saying "
                   "what becomes of the consequence — \"{{corpus:Q6/p9:affect_c1:10:31:sha=cb9713afcc59:shape=R12-1-27,R21-0-20}}"
                   "{{corpus:Q6/p9:affect_c1:32:55:sha=374f94f40fd7}} health\" — is inseparable from the "
                   "naming of it, so affect_c1 was left holding only the "
                   "sentence after, which states a NEW state rather than the "
                   "fate of the old one. Given the clause, it answers `met`",
            # Measured, not predicted: p9 re-run after the fixture repair
            # returns 3.75 against a gold of 5.00. state_a1 is the only slot
            # that disagrees, through the cover demotion described above.
            "expect_error": -1.25,
        },
    },
    "Q4c": {
        16: {
            "why": "gold 3.0 for \"did not say if {{corpus:Q4b/p15:modify:0:30:sha=431b4811e0ab:shape=R0-1-74,R30-0-20}}"
                   "{{corpus:Q4b/p15:modify:31:34:sha=10c22bcf4c76}} you modify and why\" — but the handout asks that under 4b, "
                   "which has its own `Modify:` field and carries "
                   "modify_stated/modify_why for 3 of its 5 points. 4c asks only "
                   "for two consequences plus the keyword. The deduction is "
                   "misfiled: p16's Q4b row is a clean 5.0, so the point was taken "
                   "off the wrong item. No correct 4c scorer can reach 3.0 here, "
                   "and both systems return 5.0.",
            # VERIFIED against 61 handout-1 runs on disk: 58 return 5.0, which
            # is this +2.00. The three that return 3.0 are all pre-refactor
            # snapshots (h1_preconv, h1_precover, h1_prevocab), and they reach
            # gold's NUMBER by a route gold never took — charging
            # C_NOT_CONSEQUENCE on the second example, where gold's stated
            # reason is a misfiled 4b criterion. Hitting the total on a
            # different criterion is not scoring the cell; the claim that no
            # correct 4c scorer reaches 3.0 stands. Still asserted every run,
            # and reported in the not-counted block if it drifts.
            "expect_error": +2.00,
        },
    },
    "2a": {
        18: "gold gives a full 6.0, crediting a verdict the student COPIED from "
            "the template's worked example — \"{{corpus:2a/p17:verdict:0:30:sha=4f8cdaa536cd:shape=R30-0-20}}"
            "{{corpus:2a/p17:verdict:31:34:sha=b63b99f6383b}} successful.\" is the example's own first line. join_aware "
            "strips it as boilerplate, correctly and load-bearingly: the same "
            "subtraction is what stops p4's kept example chart being scored as "
            "their graph. After it no verdict of p18's own survives, so no "
            "correct scorer can reach the 2.0 gold awarded for one. The paper "
            "scorer then quotes the nearest sentence, which is how1's — that "
            "overlap is the scorer coping with an absent element, not a "
            "transcription that lost one, and there is nothing to repair in the "
            "fixture",
    },
    "1c": {
        4: "gold 0 (\"Did not provide a graph\") but all four weeks of data "
           "supplied — on the web that data DRAWS the chart, so the paper "
           "failure is unreachable rather than missed",
        19: "the same: gold 0 for no graph, four complete weeks of data",
        20: "the same failure in its third form — a written DESCRIPTION of a "
            "graph, which on the web IS the answer: the labels are typed into "
            "fields and the chart is drawn from the four complete weeks",
        # p11 is NOT a fourth: asked twice now, settled both times. Its "-1 pt:
        # missing baseline data week" never reaches a comparison, because
        # rebuild_gold_1c restates the row from its labelling verdicts and the
        # improvised charge drops out — effective gold 6.0, not the sheet's 7.0.
        # The scorer reads title from the graph (not the prose, which is empty),
        # faults x and y exactly as gold does, and returns 6.0. Exact match, so
        # there is nothing here to exclude. See agreement.UNSCORED_GOLD_CRITERIA,
        # which is where that criterion is declared.
    },
}


# ── One place that answers "is this cell counted?" ──────────────────────────
#
# Three reasons a cell is not counted, and they mean DIFFERENT things when the
# model gets one wrong, which is why the kind travels with the pid:
#
#   suspect      the SUBMISSION cannot be trusted (mis-transcribed), so the
#                input is not what the student wrote. A miss says nothing.
#   self_graded  the PROMPT contains this participant's answer and the grader's
#                decision. A miss here is a RED FLAG: the answer was supplied
#                and the model missed it anyway.
#   unscoreable  the GOLD ROW cannot be reproduced by any correct scorer. A miss
#                is EXPECTED — the documented behaviour, not a defect.
#
# All three harnesses must read this, or their rates are computed over different
# denominators and the columns stop being a comparison. Not theoretical: the
# table above lived in agreement.py and agreement_app.py as two hand-kept mirrors
# and in baseline.py not at all, so the paper scorer counted five cells the other
# two dropped.

EXCLUSION_KINDS = ("suspect", "self_graded", "unscoreable")


def unscoreable(item: str) -> dict[int, str]:
    """{pid: why} — cells whose gold no correct scorer can reach."""
    return {pid: (e["why"] if isinstance(e, dict) else e)
            for pid, e in PER_ITEM_EXCLUDE.get(item, {}).items()}


def unscoreable_expectation(item: str) -> dict[int, float]:
    """{pid: pred - gold} for unscoreable cells that declare what the miss IS.

    An `unscoreable` reason says a correct scorer CANNOT reach the gold, which is
    a claim about a number. Left in prose that number goes stale without anything
    noticing: Q6's p9 asserted "the CLI's error here is exactly -2.50" while every
    run measured -1.25, and the sentence went on pointing future work at the
    fixture reconstruction when the whole story was a declared divergence.

    Declaring it here makes it an assertion the harnesses check on every run, so
    the cell either behaves as documented or says so.
    """
    return {pid: float(e["expect_error"])
            for pid, e in PER_ITEM_EXCLUDE.get(item, {}).items()
            if isinstance(e, dict) and e.get("expect_error") is not None}


def scored_exactly(item_id: str, gold: float, pred: float) -> bool:
    """Did this cell score exactly right, by ITEM ID rather than rubric record?

    The same decision as `scores_as_exact`, reachable from the places that have
    an item id and a number and nothing else — which turned out to be most of
    them. Every rate in this project is a count of cells that "scored exactly
    right", and that phrase had SIX implementations: two called
    `scores_as_exact`, and four re-derived it as `abs(pred - gold) < 1e-9`. The
    four included the ALL aggregate on both the CLI and paper harnesses and, worse,
    the median-run SELECTOR — so the run chosen for publication was picked by a
    rule the published table then disagreed with. One table printed 67% and 58%
    for the same twelve cells.

    `check_unreachable_gold_is_allowed` did not catch it: it tested that the
    string "scores_as_exact" appeared in each file, and it did — in the one code
    path that used it.
    """
    for h in (1, 2, 3):
        rec = config(h)["rubric"].BY_ID.get(item_id)
        if rec is not None:
            return scores_as_exact(rec, gold, pred)
    raise KeyError(f"no rubric item {item_id!r} in any handout")


def stale_claim(item: str, pid: int, gold: float, pred: float) -> str | None:
    """The warning line for a cell that stopped behaving as its exclusion says.

    Lives here rather than in the three reporters because they are three copies
    of one block already — the same mirror-keeping this module exists to end.
    """
    want = unscoreable_expectation(item).get(pid)
    if want is None or abs((pred - gold) - want) < 1e-9:
        return None
    return (f"<-- CLAIM STALE: declared expect_error={want:+.2f}, measured "
            f"{pred - gold:+.2f}. Fix the reason in "
            f"handouts.PER_ITEM_EXCLUDE or the exclusion")


def cell_exclusions(handout: int, item: str) -> dict[int, tuple[str, str]]:
    """{pid: (kind, why)} for one item — every cell that must not be COUNTED.

    Not a work list. Excluded cells are still RUN and still scored: whether the
    model gets them right is evidence in its own right, and suppressing the call
    threw that evidence away. Only the RATE excludes them.
    """
    out: dict[int, tuple[str, str]] = {}
    for pid in suspect(handout):
        out[pid] = ("suspect", "mis-transcribed submission; the input is not "
                               "what the student wrote")
    for pid in exemplar_drops(handout).get(item, []):
        out[pid] = ("self_graded", "this item's prompt contains their response "
                                   "and the grader's decision")
    for pid, why in unscoreable(item).items():
        out[pid] = ("unscoreable", why)
    return out


# ── Items a backend cannot score at all ─────────────────────────────────────

def not_comparable_items(handout: int, supports_tools: bool) -> dict[str, str]:
    """{item: why} — items the PAPER scorer cannot score from this backend.

    Scoped to score.py, and only baseline.py consults it. The web and CLI are
    NOT affected and must not be filtered by this: they never look at an image.
    1c on those sides is scored from the four weeks of data the student typed,
    through `derived="has_own_graph:complete:..."` in the OLX, and web_v8 scores
    it 16/17 with no tool involved. It is score.py's handout-3 prompt that asks
    the model to Read the graph as an IMAGE, because on paper a graph is a
    picture — so the deviation belongs to that prompt, not to the item.

    COMPUTED from the rubric rather than listed, so it cannot go stale: score.py
    passes `allow_tools=["Read"]` for exactly the items flagged `graph_item`, and
    a backend that does not forward tools scores those blind. Blind on a graph
    item is not noise, it is a systematic zero — the model reports no graph
    because it cannot see one.

    Observed, not hypothesised: paper+gpt-5-mini returned 0.00 on 11 of 20 cells
    of 1c where gold is 6-10, against paper+Opus scoring the same cells correctly
    through the Read tool. Reporting that as 5/17 would publish a missing tool as
    a model deficiency.

    Excluded from the RATE and reported as not comparable — a different thing
    from cell_exclusions(), which drops individual cells of an item that is
    otherwise fine.
    """
    if supports_tools:
        return {}
    return {
        it["id"]: ("needs an image tool to read the student's graph; this backend "
                   "sends no tools, so the item scores blind and returns 'no graph'")
        for it in config(handout)["rubric"].ITEMS
        if it.get("graph_item")
    }


# ── Scores gold asks for that the item cannot produce ────────────────────────

def attainable_scores(item: dict) -> list[float]:
    """Every score this item can actually produce.

    A score is max minus the sum of some subset of the scorable components,
    clamped at 0, plus 0 itself where a gate can take the whole item. Computed
    from the rubric rather than listed, so an item whose point values change
    cannot leave a stale table behind.
    """
    from itertools import combinations
    pts = [c["pts"] for c in item["credit"]
           if not c.get("reported") and c.get("pts") is not None]
    out = {float(item["max"])}
    for r in range(1, len(pts) + 1):
        for combo in combinations(pts, r):
            out.add(max(0.0, round(item["max"] - sum(combo), 4)))
    if any(c.get("gates") for c in item["credit"]):
        out.add(0.0)
    return sorted(out)


def nearest_attainable(item: dict, gold: float) -> set[float]:
    """The reachable score(s) closest to `gold` — the whole tie, if it is one.

    Empty when gold is itself reachable, which is the ordinary case: only one
    cell in the corpus is not (Q6 p4, whose 6.00 implies 3.2 slots of 1.25).
    """
    scores = attainable_scores(item)
    if any(abs(gold - a) < 1e-9 for a in scores):
        return set()
    best = min(abs(gold - a) for a in scores)
    return {a for a in scores if abs(abs(gold - a) - best) < 1e-9}


def scores_as_exact(item: dict, gold: float, pred: float) -> bool:
    """Does `pred` count as exact against `gold`?

    Normally that means equality. But where gold names a score the item CANNOT
    produce, the closest reachable value is the best any correct scorer can do,
    and penalising it measures the rubric's arithmetic rather than the scorer's
    judgement. Q6 p4 asks for 6.00 from an item that moves in steps of 1.25; a
    scorer returning 6.25 has done everything right.

    Deliberately not a tolerance. Only an UNREACHABLE gold opens the allowance,
    and only to the nearest reachable value(s) — a cell whose gold is reachable
    is still judged on equality, so this cannot quietly forgive a near miss.
    """
    if abs(pred - gold) < 1e-9:
        return True
    return pred in nearest_attainable(item, gold)
