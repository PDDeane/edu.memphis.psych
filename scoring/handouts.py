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
        # Nine more items qualify on the same test and are NOT registered here —
        # Q1, Q2, Q4a, Q4c, Q5, Q6 and H3's 1a, 1c, 2a, another 45 item-cells.
        # Registering them is a measurement-policy change that moves every
        # reported denominator in the project, so it is a deliberate decision
        # rather than a side effect of this one. Run the audit to reproduce the
        # list; it is in EQUIVALENCE.md.
        "cited_participants": {"Q4b": [2, 4, 6, 7, 13, 15, 19, 20]},
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
