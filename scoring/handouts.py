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
        "exemplar_participants": [10, 8, 6],
        # ...but only on the items whose PROMPT actually embeds them. Verified
        # against the rubric: Q6 is the sole item with an `exemplars` field, and
        # the three bodies reproduce p10, p8 and p6 verbatim. Their Q1..Q5
        # answers appear in no prompt, so dropping them there discarded 21 cells
        # for nothing. See exemplar_drops() below.
        "exemplar_items": ["Q6"],
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
            # Merged with `exemplar_items` above, not replacing it: Q6 both
            # reproduces p10/p8/p6 in full AND cites seven others.
            "Q6":  [2, 3, 5, 10, 11, 17, 19],
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
        "code": "REASON_FOR_WRONG_BEHAVIOR", "cells": [("Q5", 4)],
        "why": "p4's first entry reads \"I continue sleep enough because sleep is "
               "good for you, I am gaining something)\" — it names the OPPOSITE of "
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
               "have to do an extra 30 pushups if...\"), which is structurally "
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
GOLD_CEILINGS: dict[tuple[str, str], tuple[str, ...]] = {
    ("1", "Q3"): (
        "`action_oriented`: five answers justify the goal by CAPABILITY rather "
        "than by naming an action, and gold splits them — p14 (\"my early mornings "
        "are free and my gym is near my house\") and p18 (\"I have access to the "
        "university's gym\") are CREDITED, while p8 (\"I will be able to make time\"), "
        "p16 (\"I have a lot of time on my hands\") and p20 (\"i am able to full "
        "asleep\") are DEDUCTED. Same claim, opposite verdicts. Any consistent rule "
        "gets at most 3 of those 5, so >=2 cells are unwinnable and 18/20 is the "
        "ceiling. Measured: the other four SMART slots are 0-2 errors each, this "
        "one is 4-5, and a 'labelled Action section' rule matches gold on only "
        "12/20 — worse than the models manage without it.",
    ),
    ("1", "Q6"): (
        "p4's gold of 6.00 implies 3.2 slots of 1.25 — not a whole number of "
        "slots, so no slot-derived score can land on it. The row itemises "
        "\"-2.5: missing both consequences\" and \"-1.5; missing one antecedent\", "
        "and 1.5 is not a multiple of this item's slot value.",
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
#   necessarily plotted — p11's `baseline` field holds "0, 30, 0, 0, 30, 0, 30",
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
PER_ITEM_EXCLUDE: dict[str, dict[int, str]] = {
    "Q6": {
        9: "the eight-box fixture for this cell is arbitrary, and it is the SAME "
           "arbitrary fixture on both sides: fixture_for() imports "
           "agreement_app.build_jobs, so this harness feeds its prompt the frozen "
           "q6_consensus table rather than building its own split — verified "
           "byte-identical. p9 tied 5/5 across ten runs on state_c2 and affect_c2, "
           "so the vote had to break the tie, and the break put the text in "
           "state_c2 and left affect_c2 empty. That decides 2 of the 8 slots — 2.5 "
           "of 10 points — before the model reads anything, and the CLI's error "
           "here is exactly -2.50. Measuring either side on it measures the "
           "tie-break. Also one of the four documented gold divergences "
           "(A_MISMATCH on state_a1). Both reasons are side-agnostic, which is why "
           "the web-only exclusion this mirrors was incomplete.",
    },
    "Q4c": {
        16: "gold 3.0 for \"did not say if this behavior is a good choice for you "
            "modify and why\" — but the handout asks that under 4b, which has its "
            "own `Modify:` field and carries modify_stated/modify_why for 3 of "
            "its 5 points. 4c asks only for two consequences plus the keyword. "
            "The deduction is misfiled: p16's Q4b row is a clean 5.0, so the "
            "point was taken off the wrong item. No correct 4c scorer can reach "
            "3.0 here, and both systems return 5.0.",
    },
    "1c": {
        4: "gold 0 (\"Did not provide a graph\") but all four weeks of data "
           "supplied — on the web that data DRAWS the chart, so the paper "
           "failure is unreachable rather than missed",
        19: "the same: gold 0 for no graph, four complete weeks of data",
        20: "the same failure in its third form — a written DESCRIPTION of a "
            "graph, which on the web IS the answer: the labels are typed into "
            "fields and the chart is drawn from the four complete weeks",
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
    return dict(PER_ITEM_EXCLUDE.get(item, {}))


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
