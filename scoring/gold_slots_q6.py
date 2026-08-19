"""Q6's per-slot gold verdicts, read out of the grader's comment.

Same principle as agreement.gold_slots_1c: these graders itemise what they took
off, so a criterion they never mention passed. Q6 differs in being ARITHMETICALLY
CHECKABLE -- its eight slots are 1.25 each -- and the amount is not merely a
check, it is part of the reading. "Missing second antecedent" at -2.5 charges the
naming AND the how-half; the same words at -1.25 charge one of them. Reading the
words without the number cannot tell those apart, so the number decides how many
slots a clause reaches, and a clause whose amount is not a multiple of 1.25 is
reported rather than guessed at.
"""
import re

SLOTS = ["state_a1","change_a1","state_a2","change_a2",
         "state_c1","affect_c1","state_c2","affect_c2"]

# Advice and the fill-in-the-blank template these graders paste under a comment.
# It names EACH antecedent and EACH consequence, so read as deductions it charges
# the whole sheet -- it was doing exactly that on p4, p5 and p8.
_BOILER = re.compile(
    r"remember you are saying|format is something like|let's break down"
    r"|antecedents lead to behaviors|_{3,}", re.I)
# Everything from the first boilerplate marker onward is advice, not deductions.
_BOILER_SPLIT = re.compile(
    r"remember you are saying|format is something like|let's break down"
    r"|antecedents lead to behaviors", re.I)


def _clauses(feedback: str):
    """(amount, text) per itemised deduction, boilerplate dropped."""
    f = (feedback or "").replace("\n", " ")
    # Boilerplate is STRIPPED, not used to drop the chunk it sits in. Dropping the
    # chunk lost p5's third deduction, which the grader had written on the line
    # above a pasted "Antecedents lead to behaviors..." aside.
    f = _BOILER_SPLIT.split(f)[0] if _BOILER_SPLIT.search(f) else f
    # Split before each "-N" / "-N.N" that opens a deduction.
    for part in re.split(r"(?=-\s?\d+(?:\.\d+)?)", f):
        p = " ".join(part.split())
        if not p or _BOILER.fullmatch(p.strip()):
            continue
        m = re.match(r"-\s?(\d+(?:\.\d+)?)", p)
        yield (float(m.group(1)) if m else None), p


def gold_slots_q6(feedback: str) -> tuple[set[str], list[str]]:
    f = " ".join((feedback or "").lower().split())
    if not f.strip():
        return set(), []
    if "did not answer" in f:
        return set(SLOTS), []

    out: set[str] = set()
    notes: list[str] = []
    for amount, text in _clauses(feedback):
        p = text.lower()
        ante, cons = "antecedent" in p, "consequence" in p
        # A purpose clause names the consequence the change is FOR, and charges
        # nothing on it: "did not say how you would change your second antecedent
        # to affect {{corpus:Q6/p14:affect_c1:91:117:sha=8f379fadb8bd}} weight" is one deduction, not two.
        # ...and it suppresses whichever side is the MEANS, not a fixed one.
        # "by changing your antecedents" makes the antecedent the means of a
        # deduction charged on the consequence; "to affect the consequence of X"
        # makes the consequence the purpose of one charged on the antecedent.
        if ante and cons:
            if re.search(r"by changing your|by changing my", p):
                ante = False
            elif re.search(r"to affect|to impact", p):
                cons = False
        if not (ante or cons):
            continue
        every = bool(re.search(r"\b(each|both)\b", p))
        ordinals = ({"1", "2"} if every else
                    {"2"} if re.search(r"\bsecond\b", p) else
                    {"1"} if re.search(r"\bfirst\b", p) else set())
        if not ordinals:
            notes.append(f"no ordinal in {text!r}")
            continue
        # Which half the words charge. "how"/"being changed"/"being affected" is
        # the how-half; naming words are the state-half. A clause can carry both.
        how_half = bool(re.search(r"\bhow\b|being changed|being affected", p))
        state_half = bool(re.search(r"did not state|missing|did not address"
                                    r"|does not match|is not the same|not the same"
                                    r"|did not clarify", p))
        # "did not clarify X being affected" / "did not say how X" charge only the
        # how-half despite carrying a naming word.
        if re.search(r"did not say how|did not clarify", p):
            state_half = False
        if not (how_half or state_half):
            continue

        fams = ([("state_a", "change_a")] if ante else []) + \
               ([("state_c", "affect_c")] if cons else [])
        wanted: list[str] = []
        for state_fam, how_fam in fams:
            for o in sorted(ordinals):
                if state_half:
                    wanted.append(f"{state_fam}{o}")
                if how_half:
                    wanted.append(f"{how_fam}{o}")
        # The amount decides the reach. More points than the named halves account
        # for means the clause covers the pair; fewer means it does not.
        if amount is not None:
            n = amount / 1.25
            if abs(n - round(n)) > 1e-6:
                notes.append(f"{amount} is not a multiple of 1.25 in {text!r}")
                out |= set(wanted)
                continue
            n = int(round(n))
            if n > len(wanted):
                for state_fam, how_fam in fams:
                    for o in sorted(ordinals):
                        for k in (f"{state_fam}{o}", f"{how_fam}{o}"):
                            if k not in wanted:
                                wanted.append(k)
            wanted = wanted[:n] if n < len(wanted) else wanted
        out |= set(wanted)
    return out, notes


def reconcile(withheld: set[str], score: float) -> str | None:
    """Do the parsed slots account for the points the grader took off?

    Measured against the NEAREST ATTAINABLE score, not the sheet's number, by the
    same rule as handouts.scores_as_exact: where gold names a total the item
    cannot produce, the closest reachable value is what a correct scorer returns,
    and apportioning the unreachable figure would charge slots that do not exist.
    Q6/p4 is the case -- gold says 6.00 on an item moving in steps of 1.25, so
    the reading is against 6.25 and three withheld slots, not 4.00 worth of them.
    """
    import handouts as _H, rubric_h1 as _R
    item = _R.BY_ID["Q6"]
    targets = _H.nearest_attainable(item, float(score)) or {float(score)}
    implied = round(1.25 * len(withheld), 2)
    for t in targets:
        if abs(implied - round(10.0 - t, 2)) < 0.01:
            return None
    lost = ", ".join(f"{round(10.0 - t, 2):.2f}" for t in sorted(targets))
    return f"parse={len(withheld)} slot(s)={implied:.2f}, reachable={lost}"


def unresolved_slots(feedback: str, score: float) -> tuple[int, set[str]]:
    """How many withheld slots the comment does NOT pin down, and the candidates.

    Q6/p4 says "missing one antecedent" without saying WHICH, so the count of
    withheld slots is recoverable and one identity is not. Reported rather than
    apportioned: an arbitrary pick would read downstream as gold's own verdict.
    """
    import handouts as _H, rubric_h1 as _R
    named, _ = gold_slots_q6(feedback)
    item = _R.BY_ID["Q6"]
    targets = _H.nearest_attainable(item, float(score)) or {float(score)}
    want = max(int(round((10.0 - t) / 1.25)) for t in targets)
    missing = want - len(named)
    if missing <= 0:
        return 0, set()
    f = " ".join((feedback or "").lower().split())
    # Boilerplate stripped here too: the pasted template says "HOW you will change
    # EACH antecedent", which makes every unpinned slot look like a how-half.
    if _BOILER_SPLIT.search(f):
        f = _BOILER_SPLIT.split(f)[0]
    side = ("state_a", "change_a") if "antecedent" in f else ("state_c", "affect_c")
    # The half is usually still legible even when the ordinal is not: "missing one
    # antecedent" carries no `how` language, so it charges the naming half.
    if re.search(r"\bhow\b|being changed|being affected", f):
        fam = side
    else:
        fam = (side[0],)
    cands = {f"{k}{o}" for k in fam for o in ("1", "2")} - named
    return missing, cands


# How each CORRECTED_GOLD row changes gold's per-family credit counts.
#
# handouts.CORRECTED_GOLD records a total plus a prose reason; the reason is where
# the affected slot is named ("gold credits `state_a1`, which names a THIRD
# antecedent ..."), so the structured form lives here and is asserted against the
# totals rather than trusted.
#
# `families` is the change to the number of LISTED entries gold credits, per
# family -- negative where gold was lenient, positive where it was harsh. `grid`
# is any part of the correction that is NOT a slot: Q6/p4 charges "-1.5" for one
# antecedent on an item whose step is 1.25, so regularising that arithmetic moves
# the total 0.25 without changing whether any slot is credited.
CORRECTED_FAMILY = {
    9:  {"families": {"a": -1}, "grid": 0.0,  "slot": "state_a1"},
    17: {"families": {"c": -1}, "grid": 0.0,  "slot": "state_c1"},
    18: {"families": {"a": -1}, "grid": 0.0,  "slot": "state_a2"},
    4:  {"families": {"c": +1}, "grid": 0.25, "slot": "state_c2"},
}

# HOW GOLD ITEMISES AN EFFECT SLOT, because reading it wrong sends you the wrong
# way. Gold charges `affect_cN` when the box describes NO EFFECT, and not when the
# effect is described but the consequence named alongside it is the wrong one. So a
# row can withhold both `state_c` slots and credit both `affect_c` slots without
# contradicting itself: the naming error is charged once, under the naming slot.
# Verified on all twenty rows -- the rows that DO withhold an effect slot say so in
# those terms ("did not say how", "did not clarify"), every time.
#
# The consequence for anything comparing our verdicts against gold's: an
# `affect_cN` disagreement is about whether an effect was DESCRIBED, never about
# whether it attached to the right consequence. Q6/p5 is where this matters --
# gold credits both its effect boxes, we refuse one, and the gap is ours.

AFAM = ("state_a1", "state_a2")
CFAM = ("state_c1", "state_c2")
PER_BOX = ("change_a1", "change_a2", "affect_c1", "affect_c2")


def gold_view(pid: int, feedback: str, score: float, corrected: bool = True) -> dict:
    """Gold's verdicts in the two shapes that are comparable to ours.

    `families` is the number of LISTED entries gold says were named, per family.
    That is the measure to compare on, because gold's ordinals are tallies rather
    than indices and because a cover group scores the count, not which box holds
    it -- see BACKLOG.md. Box-level attribution for the state slots is deliberately
    NOT returned: it would be an inference gold never made.

    `boxes` is per-slot for `change_*`/`affect_*`, where there is no cover group
    and the box really is the unit. It comes from the same amount-driven withheld
    set as everything else: an ad-hoc reading of the words alone had gold crediting
    `change_a2` on a row whose "-2.5 pts: missing second antecedent" pays for the
    naming AND the how-half, and got two cells wrong in the same way.

    With `corrected` (the default) the three rows in CORRECTED_SLOT give up the
    credit our own analysis found they should never have had. Pass False to see
    the raw sheet.
    """
    withheld, _ = gold_slots_q6(feedback)
    missing, cands = unresolved_slots(feedback, score)
    fam = {"a": 2 - len(withheld & set(AFAM)), "c": 2 - len(withheld & set(CFAM))}
    # An unpinned withholding still costs its family a credit even though the box
    # is unknown -- which is the whole reason for counting families.
    if missing and cands:
        side = "a" if all(c.endswith(("a1", "a2")) for c in cands) else "c"
        fam[side] -= missing
    if corrected and pid in CORRECTED_FAMILY:
        for side, d in CORRECTED_FAMILY[pid]["families"].items():
            fam[side] += d
    return {"families": fam,
            "boxes": {s: s not in withheld for s in PER_BOX},
            "unpinned": (missing, sorted(cands)) if missing else (0, [])}


def check_corrected_slots_account_for_the_totals() -> list[str]:
    """Each row's family changes plus its grid term must explain its total exactly.

    Signed, so a row that RAISES gold is checked as strictly as one that lowers it
    -- Q6/p4 is the only raising row and it is the one most in need of the check,
    since its correction mixes a slot (+1.25) with an off-grid regrade (+0.25).
    """
    out = []
    try:
        import handouts as _H
    except Exception as exc:
        return [f"could not import handouts: {exc}"]
    for (item, pid), fix in _H.CORRECTED_GOLD.items():
        if item != "Q6":
            continue
        delta = round(float(fix["score"]) - float(fix["was"]), 2)      # signed
        spec = CORRECTED_FAMILY.get(pid)
        if spec is None:
            out.append(f"Q6/p{pid} is corrected by {delta:+.2f} but CORRECTED_FAMILY "
                       f"does not say which family it moves -- the family view "
                       f"silently ignores it")
            continue
        explained = round(1.25 * sum(spec["families"].values()) + spec["grid"], 2)
        if abs(explained - delta) > 0.01:
            out.append(f"Q6/p{pid}: the sheet moves {delta:+.2f} but CORRECTED_FAMILY "
                       f"explains {explained:+.2f} "
                       f"(families {spec['families']}, grid {spec['grid']:+.2f}) -- "
                       f"one of the two is out of date")
    for pid in CORRECTED_FAMILY:
        if ("Q6", pid) not in _H.CORRECTED_GOLD:
            out.append(f"CORRECTED_FAMILY names p{pid}, which handouts.CORRECTED_GOLD "
                       f"no longer corrects -- drop it")
    return out
