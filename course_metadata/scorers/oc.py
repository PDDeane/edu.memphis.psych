#!/usr/bin/env python3
"""The OPERANT-CONDITIONING scorer, as a plugin. Goal E, step 1.

WHAT THIS IS. `score.py` dispatched on a rubric flag -- `derive_from_criteria`
vs `derive_from_credit` -- so the boundary between "this course's subject matter"
and "the engine" already existed and was already declaration-driven. This module
is one side of it, named. The engine keeps `credit`, which is slot-sheet driven
and subject-neutral; the eight criteria items (PR, NR, PP, NP, DAY1, WK1, DAY2,
WK2) come here.

WHAT IT IS NOT. It is not yet SUBJECT-NEUTRAL: the fact vocabulary, the gate
structure and the PR/NR/PP/NP taxonomy are still operant conditioning's. Making
the capability reusable is goal M, and M's own section records why that is a much
larger job. E moves it out; M makes it general. Do not conflate them here.

STEP 1 IS A VERBATIM MOVE. The bodies below are the source text that was in
`score.py` and `agreement.py`, unchanged, because `enforcement` compares the two
engines BY READING THEIR SOURCE -- `check_selectors_govern_something` greps this
text for `yes("...")` and `"..." in keys`. Reformatting here would change a
check's answer without changing any behaviour, so the only edits are the `def`
lines, the function-local imports that replace what used to be module globals,
and this header.

The names the engine still owns, imported per call rather than at module level so
that `score` can import this module without a cycle:

    SCHEMA, _slot_options, _gate_keys, _expect_operand, _forbid_operands
    _expect_rule, _forbid_rule        generic rubric-primitive readers
    REQUIRED_MOVE                     OC data; moves here when M declares it

THE WEB MIRROR MOVES TOO. `agreement.score_oc` and `score_oc_cadence` are
hand-written mirrors of this logic, and `enforcement.py` compares all three by
source. Moving one side without the other would break the comparison the project
rests on, so both are here and the old names alias to these.
"""
from __future__ import annotations

import json


def schema_fragment(item: dict) -> dict:
    """The schema for a criteria item: `build_schema`'s `derive_from_criteria` arm."""
    from score import (SCHEMA, _expect_operand, _forbid_operands, _gate_keys,
                       _slot_options)
    # The five definitional criteria are REQUIRED schema properties, so the
    # model cannot credit an example without first stating what the
    # behaviour is, what the stimulus is, and whether the stimulus is
    # contingent, subsequent, and arranged. Participant 13 was credited for
    # [[corpus WK1/p13 wk1 0:51 sha=848ae9e56f72]] — no behaviour,
    # no contingency — precisely because prose guidance let that step be
    # skipped.
    props = {
        "behavior": {"type": "string"},
        "stimulus": {"type": "string"},
        "contingent": {"type": "boolean"},
        "follows_behavior": {"type": "boolean"},
        "stimulus_is_arranged": {"type": "boolean"},
        "observed_type": {
            "type": "string",
            "enum": ["PR", "NR", "PP", "NP", "none"],
        },
        "avoidance_frame": {"type": "boolean"},
    }
    # The three barrier readings, on whichever items answer them. Hoisted
    # OUT of the cadence branch: NR needs the same readings, and leaving them
    # inside meant widening the selector changed nothing.
    # ASK FOR WHAT THE DECLARATIONS CONSUME. The three barrier readings are
    # exactly the slots this item's `forbid` conjunction names in its
    # conditions, so the sheet follows the rule instead of a tuple of item ids
    # -- and the old failure it guards against cannot recur: scoping the third
    # reading differently from the other two left NR answering two of three
    # and the conjunction never firing, and a conjunction now brings its own
    # operands.
    for _slot in _forbid_operands(item):
        props[_slot] = {"type": "string", "enum": _slot_options(_slot)}

    if item.get("cadence"):
        props["named_type"] = {
            "type": "string",
            "enum": ["PR", "NR", "PP", "NP", "unclear"],
        }
        props["cadence_ok"] = {"type": "boolean"}
        # WK1 derives this from a CLASSIFICATION, mirroring
        # the web's pick + expect: the model names which behaviour the trigger
        # identifies and the engine compares it against the student's own.
        # Judged directly, the slot answered `met` on every pass of the cells
        # gold charges, because their own behaviour is in the sentence as the
        # PRIZE rather than as the trigger. It was WK1 alone until 2026-09-05,
        # which left the other three declaring WRONG_BEHAVIOR at 1.0 with no
        # answer able to reach it — DAY2/p7 is that gap, measured at 0/12.
        # DAY2 only. Derived by reading all 64 counted cadence answers: the
        # nine over-credited cells that are not valence inversions share one
        # property — they state no contingency. They describe what the
        # student will do, or why, or offer one activity instead of another.
        # Every credited cell states a condition on the behaviour AND a
        # clause in which something is granted or withheld.
        if "states_a_contingency" in _gate_keys(item):
            props["states_a_contingency"] = {"type": "boolean"}
        # The two halves of the direction test, answered separately. The
        # engine compares them; the model is never asked to weigh both at
        # once, which is what the composite clause did and why it never
        # fired. Mirrors the web's pick(valence) + pick(valence_or_none)
        # and its `equals` rule, lenient on `none`.
        _parsed = _expect_operand(item, "targets_own_behavior")
        if _parsed:
            props[_parsed] = {"type": "string", "enum": _slot_options(_parsed)}
        else:
            props["targets_own_behavior"] = {"type": "boolean"}
        # WK2 only, mirroring a question the TYPE items have always asked and
        # the cadence items never did. There, `targets_intended_behavior`
        # charges WRONG_TYPE when the arrangement is the right type but
        # pointed the wrong way; here, `targets_own_behavior` asks only WHOSE
        # behaviour it is. So an answer that delivers an aversive for SUCCESS
        # — punishing the goal behaviour — passes every check on the sheet.
        if "aimed_correctly" in _gate_keys(item):
            props["aimed_correctly"] = {"type": "boolean"}
        # WK1 only, and asked as a PARSE rather than a judgement — see the
        # guidance in rubric_h2. Two earlier versions asked "is a consequence
        # delivered?" and the model answered inconsistently on the two cells
        # that matter; the cue it can actually apply is syntactic.
        if "agent_delivers_consequence" in _gate_keys(item):
            props["agent_delivers_consequence"] = {"type": "boolean"}
        # The item's fourth point. rubric_h2 has carried this slot and its
        # LINK_NOT_ASSERTED deduction for a while, but nothing here asked for
        # it, so on the paper-scorer path it was inert: 0 of 80 cadence cells
        # scored it and the deduction was never charged once. The web app and
        # agreement.py both charge it from the OLX sheet's `@1`, so leaving it
        # out made the two implementations score identical answers
        # differently — the divergence class this project exists to close.
        props["consequence_asserted"] = {"type": "boolean"}
    else:
        props["targets_intended_behavior"] = {"type": "boolean"}
        # The type is a two-bit function -- added/taken x desirable/not -- so
        # ask for the pair and derive it. A single pick makes it impossible to
        # assert a type contradicting the reading it rests on, which is what
        # `observed_type` kept doing: NP/p14 answered "taken away" and
        # "desirable" and then called the example PR.
        if item.get("move_pick"):
            props["stimulus_move"] = {
                "type": "string", "enum": _slot_options("stimulus_move")}
    schema = json.loads(json.dumps(SCHEMA))
    del schema["properties"]["credit_checks"]
    del schema["properties"]["deductions"]
    schema["properties"]["oc_analysis"] = {
        "type": "object",
        "properties": props,
        "required": list(props),
        "additionalProperties": False,
    }
    schema["required"] = [
        r for r in schema["required"] if r not in ("credit_checks", "deductions")
    ] + ["oc_analysis"]
    return schema


def derive_ledger(item: dict, raw: dict) -> tuple[list[dict], list[dict], list[str], str | None]:
    """Turn the criteria sheet into a deduction ledger.

    Criteria 1-3 of the definition (an operant, a contingency, correct temporal
    order) plus the arranged-stimulus rule gate everything: fail any and the
    answer is not operant conditioning, whatever it looks like. Only if it
    passes do we ask which of the four types it is.
    """
    from score import REQUIRED_MOVE, _expect_rule, _forbid_rule
    a = raw.get("oc_analysis") or {}
    codes = {d["code"]: d for d in item["deductions"]}
    ledger, unknown = [], []
    advisory = None

    def add(code: str, note: str = "") -> None:
        spec = codes.get(code)
        if spec is None:
            unknown.append(code)
            return
        ledger.append({"code": spec["code"], "pts": spec["pts"], "note": note})

    has_behavior = bool((a.get("behavior") or "").strip())
    has_stimulus = bool((a.get("stimulus") or "").strip())
    is_oc = (
        has_behavior
        and has_stimulus
        and bool(a.get("contingent"))
        and bool(a.get("follows_behavior"))
    )
    arranged = bool(a.get("stimulus_is_arranged"))

    checks = [
        {"what": "operant_behavior", "met": has_behavior, "evidence": a.get("behavior", "")},
        {"what": "stimulus", "met": has_stimulus, "evidence": a.get("stimulus", "")},
        {"what": "contingent_on_behavior", "met": bool(a.get("contingent")), "evidence": ""},
        {"what": "follows_behavior", "met": bool(a.get("follows_behavior")), "evidence": ""},
        {"what": "stimulus_is_arranged", "met": arranged, "evidence": ""},
    ]

    # THE DEFINITIONAL GATES ARE DECLARED NOW. Goal M step 3. What stayed here
    # after M-3 was WHICH checks each conjunction reads and what it says; both
    # are `<Conjunction code= note= list= over=/>` on the item, so adding or
    # moving a definitional reading is an edit to the OLX and nothing else.
    #
    # The declaration names the SLOTS -- the same ones the web's sheet is
    # generated from -- and `check_named` resolves each to the check this scorer
    # records, through the course's own `SIDE_ALIAS`. Declaring them in the
    # paper's vocabulary would have made the rubric speak a language only one of
    # the two engines uses.
    import scorer_criteria as _crit
    for _c in (item.get("oc_conjunctions") or ()):
        _have = {c["what"] for c in checks}
        _over = [check_named(k, _have) for k in _c["over"]]
        _led, _unk, _stop = _crit.apply_conjunction_gate(
            checks, _over, _c["code"], codes,
            note=_c["note"], list_missing=_c["list"])
        if _stop:
            ledger.extend(_led)
            unknown.extend(_unk)
            return ledger, checks, unknown, advisory

    observed = a.get("observed_type", "none")
    if item.get("cadence"):
        named = a.get("named_type", "unclear")
        # RECORD WHAT IS CHARGED. `met` was a bare `observed == named`, which
        # contradicts the very next branch: an `unclear` naming is deliberately
        # NOT charged (no type was chosen, so nothing can mismatch), yet the
        # check went on record as failed. The web says the same thing the other
        # way round -- its `equals` rule carries `lenient: ["unclear"]` on all
        # four cadence items and resolves the slot to `met` -- so both engines
        # already agreed to excuse it and only this line dissented.
        #
        # It cost exactly one cell, WK1/p6, and it read as the two scoring
        # implementations disagreeing 4 against 2 when they do not disagree at
        # all. The leniency stays visible in `evidence`, which names both types.
        lenient_type = named == "unclear"
        checks.append({"what": "matches_chosen_type",
                       "met": lenient_type or observed == named,
                       "verdict": "met" if (lenient_type or observed == named)
                                  else "absent",
                       "evidence": f"observed {observed}, named {named}"
                                   + (" (unclear: not charged)" if lenient_type else "")})
        # CADENCE gates and TYPE charges, through the interpreter. M-3b.
        # The first short-circuits on a fact that is deliberately not a recorded
        # check; the second is an enum comparison whose `"unclear"` naming is a
        # declared lenient value that must not charge.
        _led, _unk, _stop = _crit.apply_fact_gate(a, "cadence_ok",
                                                  "CADENCE_MISMATCH", codes)
        ledger.extend(_led); unknown.extend(_unk)
        if _stop:
            return ledger, checks, unknown, advisory
        _led, _unk = _crit.apply_enum_mismatch(
            a, "observed_type", "named_type", "TYPE_MISMATCH", codes,
            note="This example is {observed}, but you chose {named}.",
            lenient=("unclear",))
        ledger.extend(_led); unknown.extend(_unk)
        # `targets_own_behavior` is either ASKED as a boolean or COMPUTED from a
        # parse of which behaviour the trigger names -- WK1 does the latter,
        # declared as `expect` in rubric_h2 and generated into the web's sheet
        # from the same declaration. Asked as a parse because two earlier versions
        # asked the judgement directly and the model answered inconsistently on
        # the two cells that matter; the cue it can apply is syntactic.
        spec = _expect_rule(item, "targets_own_behavior")
        if spec:
            left, value, lenient = spec
            got = str(a.get(left, value)).strip()
            aimed = got == value or got in lenient
        else:
            aimed = a.get("targets_own_behavior", True)
        checks.append({"what": "targets_own_behavior", "met": bool(aimed),
                       "evidence": ""})
        _led, _unk = _crit.apply_charge(checks, "targets_own_behavior",
                                        "WRONG_BEHAVIOR", codes)
        ledger.extend(_led); unknown.extend(_unk)
        # Charged additively alongside TYPE_MISMATCH and WRONG_BEHAVIOR, and in
        # the same order as agreement.py's score_oc_cadence, so the two paths
        # reach the same total from the same criteria sheet.
        # WK2 only, and it GATES, because gold's charge on the cell that
        # exposed the gap is the whole 4 and nothing smaller reaches it: the
        # scored slots on this item top out at 2 + 1 + 1.
        #
        # The gap: an aversive delivered for SUCCESS punishes the goal behaviour,
        # which is not a usable arrangement whatever else is well-formed about
        # it — and every other check passes such an answer. The behaviour is the
        # student's own, the consequence is arranged, contingent and subsequent,
        # and the cadence is right. The TYPE items have always asked this
        # question as `targets_intended_behavior`; the cadence items never did.
        # THE ITEM'S DECLARED GATES, in declared order. This replaced three
        # `if item["id"] == ...` branches that did the same thing for
        # `aimed_correctly` (WK2), `agent_delivers_consequence` (WK1) and
        # `states_a_contingency` (DAY1/DAY2/WK2). Each check is marked `!` on the
        # sheet for the web, so the rule was a declaration on one side and code on
        # the other -- and the enforcement audit compares declarations, so nothing
        # compared them. See rubric_h2.OC_GATES.
        #
        # `a.get(key, True)` keeps the old default: a gate the model was not asked
        # cannot fail. Order and short-circuiting are preserved exactly, which the
        # synthetic grid in oc_grid.py checks against the pre-change scorer.
        # THE SHARED LOOP, not a second copy. Goal M-3: this is the one rule in
        # `derive_ledger` that is already a conjunction of declared booleans, so
        # it is the one that could move to the generic interpreter unchanged.
        # `scorer_criteria.apply_declared_gates` runs it for both scorers, which
        # is what the comment above asked for -- two declarations of the same
        # thing were agreeing only by habit.
        import scorer_criteria as _crit
        _led, _unk, _stopped = _crit.apply_declared_gates(
            item, a, checks, codes, answer=resolve_operand)
        ledger.extend(_led)
        unknown.extend(_unk)
        if _stopped:
            return ledger, checks, unknown, advisory

        spec = _forbid_rule(item, "consequence_not_a_setup")
        if spec:
            # IS the web's `forbid` primitive now, from the same rubric
            # declaration that generates the web's attribute: FAILS only when
            # every named condition holds, and passes when any operand is
            # unanswered. A deprivation the plan CREATES is not a fault on its
            # own — an ordinary punishment contingency creates one too — it is a
            # fault only when the student's SUCCESS is what lifts it. The
            # conditions, and gold's `other_thing` exception, are documented
            # where they are declared: rubric_h2.FORBID.
            conds = spec
            hit = _crit.forbid_hit(a, conds)   # the rubric's `forbid` primitive
            checks.append({"what": "consequence_not_a_setup", "met": not hit,
                           "evidence": ", ".join(
                               f"{k}={a.get(k) or '?'}" for k, _ in conds)})
            if hit:
                add("NOT_OC", "The plan sets up a restriction that performing "
                              "the behaviour removes. That restriction stands in "
                              "front of the behaviour rather than following it.")
                return ledger, checks, unknown, advisory

        # Reported, never scored: the reading the conjunction above consumed,
        # surfaced so the sheet shows what it was given. Selected by the same
        # declaration, so it cannot drift away from the rule it reports on.
        if _forbid_rule(item, "consequence_not_a_setup") and a.get("restriction_authored"):
            checks.append({"what": "restriction_authored", "met": True,
                           "reported": True,
                           "evidence": a["restriction_authored"]})

        asserted = a.get("consequence_asserted", True)
        checks.append({"what": "consequence_asserted", "met": bool(asserted),
                       "evidence": ""})
        _led, _unk = _crit.apply_charge(checks, "consequence_asserted",
                                        "LINK_NOT_ASSERTED", codes)
        ledger.extend(_led); unknown.extend(_unk)
    else:
        expected = item.get("expected_type")
        want_move = REQUIRED_MOVE.get(str(expected))
        move = a.get("stimulus_move")
        # Derived, not judged: the reading decides the type rather than the type
        # deciding the reading.
        # INLINE, DELIBERATELY. This was briefly `_crit.meets_expectation(...)`,
        # and that was over-abstraction: one caller, and a `fallback_fact` /
        # `fallback_want` pair that encodes THIS rule's shape under a general
        # name. A primitive implies a contract a second course can meet; this is
        # one course's conditional, and the honest place for it is here.
        # WHICH FACT DECIDES THIS IS THE ITEM'S OWN DECLARATION, not a preference
        # order hardcoded here. The rubric is NOT uniform about it: PR declares
        # `<Expect key="demonstrates_type" left="stimulus_move"
        # value="given_desirable"/>` and NR/PP/NP declare `left="observed_type"`
        # -- one named check computed from a different fact per item, matched by
        # only PR declaring a `stimulus_move` slot at all.
        #
        # Reading the operand from the item makes that difference the rubric's to
        # state. The previous form always PREFERRED the move when present, which
        # happened to agree only because `stimulus_move` is asked exclusively on
        # PR (`if item.get("move_pick")`); had the fact ever reached NR/PP/NP the
        # scorer would have scored them on an operand those items do not declare.
        #
        # THE FALLBACK IS KEPT AND IS DELIBERATE: an operand the model did not
        # answer falls back to `observed == expected` rather than charging, which
        # is what the hand-written form did. Declaring the rule should not also
        # decide, silently, that an unanswered fact is a wrong answer.
        _spec = _expect_rule(item, "demonstrates_type")
        if _spec:
            _left, _want, _lenient = _spec
            _got = str(a.get(_left, "")).strip()
            demonstrates = (_got == _want or _got in _lenient) if _got \
                else (observed == expected)
        else:
            demonstrates = (move == want_move) if (want_move and move) \
                else (observed == expected)
        # PUBLISHED UNDER THE DECLARED NAME. The rubric's `<Onlyif cond=...>`
        # names this reading `demonstrates_type`; it is COMPUTED here rather than
        # asked, so it has to be put where the declaration can find it. Scoped to
        # a local view -- `a` is the model's answers and this is not one.
        a = dict(a, demonstrates_type=demonstrates)
        checks.append({"what": f"is_{str(expected).lower()}", "met": demonstrates,
                       "evidence": f"move {move or observed}, {expected} needs {want_move}"})
        # The cadence barrier conjunction, on NR. Same three independent readings
        # as the cadence items, different charge: there a created barrier is not
        # operant conditioning and zeroes the item; here it is simply not
        # NEGATIVE REINFORCEMENT, which needs an UNDESIRABLE thing taken away,
        # and gold charges 2. Guarded by `demonstrates` so it cannot stack on top
        # of a WRONG_TYPE already charged for the same reading -- two charges
        # would take the cell to 0 where gold says 2.
        # NR/p8 is spared because its chore pre-exists the plan, so
        # `restriction_authored` reads `relieved` rather than `created`.
        spec = _forbid_rule(item, "barrier_is_not_this_type")
        if spec:
            conds = spec
            hit = _crit.forbid_hit(a, conds)   # the rubric's `forbid` primitive
            checks.append({"what": "barrier_is_not_this_type", "met": not hit,
                           "evidence": ", ".join(
                               f"{k}={a.get(k) or '?'}" for k, _ in conds)})
            if hit and not _crit.charge_suppressed(
                    item, "barrier_is_not_this_type", a, resolve_operand):
                add("WRONG_TYPE", "The plan sets up a restriction that performing "
                                  "the behaviour removes; that is not "
                                  f"{expected}, which needs an undesirable thing "
                                  "taken away.")

        # THE OPERAND IS THE RUBRIC'S NAME, resolved to this scorer's through the
        # course's SIDE_ALIAS: the slot is declared `targets_goal_behavior` and
        # asked here as `targets_intended_behavior`.
        aimed = resolve_operand(a, "targets_goal_behavior")
        checks.append({"what": "targets_intended_behavior", "met": bool(aimed), "evidence": ""})
        if not demonstrates:
            add("WRONG_TYPE", f"The thing is {move or observed}; "
                                f"{expected} needs {want_move}.")
        # TWO INDEPENDENT CHARGES, AND THE DECLARATION KEEPS THEM FROM STACKING.
        # This was an `elif`, and the `elif` WAS the rule: one charge for either
        # cause, never two. Written that way the precedence lived in Python
        # control flow and nothing declared it -- and a guard bolted onto the
        # `elif` would have been DEAD, since the `elif` already implies
        # `demonstrates`. Measured: with the guard on the `elif`, deleting
        # `<Onlyif>` from the item changed nothing, which is the definition of
        # not being read.
        #
        # As a separate `if`, the suppression is what the declaration does:
        # remove `<Onlyif key="targets_goal_behavior" cond="demonstrates_type"/>`
        # and a wrong-type answer aimed at the wrong behaviour charges 4 instead
        # of 2. Same rule the web's generated `onlyif=` attribute carries.
        if not aimed and not any(
                _crit.charge_suppressed(item, k, a, resolve_operand)
                for k in declared_names("targets_intended_behavior")):
            # Right type, wrong target: the handout says reinforcement examples
            # increase the WGB and punishment examples decrease the UTB. An NR
            # that reinforces the unwanted behaviour is not a usable answer.
            add("WRONG_TYPE", "This reinforces the unwanted behaviour rather than the goal behaviour.")

    # THE FINAL-STAGE GATES, at the position the avoidance rule occupies. M.
    # Presentational gates run HERE, after the type rules have charged, because
    # that is where the hand-written one ran; the stage declaration makes the
    # position a property of the rubric rather than of this function's layout.
    _led, _unk, _stopped = _crit.apply_declared_gates(
        item, a, checks, codes, stage="final", answer=resolve_operand)
    ledger.extend(_led)
    unknown.extend(_unk)
    if _stopped:
        return ledger, checks, unknown, advisory

    # THE DAY1 AVOIDANCE CHARGE IS NOW DECLARED, and the final-stage loop above
    # applies it: `<Slot key="phrased_directly_gate" gate="final" charge="NOT_OC"
    # .../>` on DAY1 alone, which is exactly the set `item.get("avoidance_scores")`
    # selected -- DAY1 is the only item carrying that condition. The operand is
    # the WEB's name; `resolve_operand` reads it from this scorer's
    # `avoidance_frame`, INVERTED, through the course's declared `SIDE_ALIAS`.
    #
    # Migrating it RECORDS A CHECK that the hand-written form never did: on 100
    # of DAY1's 6400 swept answers a `phrased_directly_gate` entry now appears in
    # `checks`. The ledger, the advisory and the unknown list are byte-identical
    # on all 6400 -- the score does not move -- and the judgement behind a NOT_OC
    # charge stops being invisible on the paper side, which is the side that was
    # missing it.
    #
    # WHY IT CHARGES AT ALL, kept because the decision was measured and reversed
    # an earlier one. The standing rule was to flag and never deduct: an
    # avoidance-framed contingency is structurally sound, so zeroing it looked
    # like punishing phrasing. The cohort disagrees on THIS item. Of the five
    # DAY1 cells where `phrased_directly_gate` ever answers `absent`, gold scores
    # four of them 0 and the fifth we already miss for other reasons, so `absent`
    # predicts gold's zero and honouring it costs nothing. Measured: DAY1
    # 15/18 -> 16/18, p8 from wrong in every run to right in six of six probe
    # passes, p14 recovering to 6/6, both controls holding.
    #
    # Deliberately NOT extended to the other items -- now enforced by the
    # declaration being ABSENT from them rather than by an `if` here: WK1's p8
    # answer is not avoidance-framed at all, and PR/NR/PP/NP were never measured
    # for this, three of them being perfect as they stand.

    if a.get("avoidance_frame"):
        # Everywhere else, the original decision stands: valid contingency,
        # stated as avoidance ("so I don't have to X if I miss"). Structurally
        # sound but easy to misread. Flag for review, never deduct.
        advisory = (
            "This is stated as an avoidance contingency — the consequence is framed by "
            "what is avoided when the behaviour occurs, rather than what is added or "
            "removed after it. It is a valid arrangement, but state it directly "
            "(\"if I miss my goal, I will add ___\") so the type is unambiguous."
        )
    return ledger, checks, unknown, advisory


def passing_sheet(item: dict) -> dict:
    """A criteria sheet for `item` on which nothing fails.

    Built from `build_schema`'s own required properties, so a criterion added
    there is covered here without being named twice.
    """
    req = schema_fragment(item)["properties"]["oc_analysis"]
    a: dict = {}
    for key, prop in req["properties"].items():
        if key in ("observed_type", "named_type"):
            continue                        # set together below, so they agree
        if prop["type"] == "string":
            a[key] = f"a {key}"
        else:
            # avoidance_frame is advisory: True costs nothing but adds a note, so
            # False keeps this sheet a clean pass.
            a[key] = key != "avoidance_frame"
    kind = item.get("expected_type") or "PR"
    a["observed_type"] = kind
    if "named_type" in req["properties"]:
        a["named_type"] = kind
    return a


def check_names(item: dict) -> list[str]:
    """The credit_checks names `derive_oc_ledger` writes when nothing fails.

    Obtained by running the real ledger over a passing sheet rather than by
    listing the names, because a hand-kept list is exactly what went wrong
    before: stale_check.py could not audit these items at all, assumed the
    rubric's credit list stood in for them, and reported all eight of handout
    2's operant-conditioning items as stale when none were.
    """
    _, checks, _, _ = derive_ledger(item, {"oc_analysis": passing_sheet(item)})
    return [c["what"] for c in checks]


def _ded(item: dict, code: str, note: str | None = None) -> dict:
    """One coded deduction, shaped exactly as `scoreSlotSheet` returns them.

    `pts` comes from the item's own `<Deduction>` table, which is where both
    engines have always read it; the CODE is the part that was being discarded.
    """
    pts = {d["code"]: d["pts"] for d in item["deductions"]}[code]
    out = {"code": code, "pts": pts}
    if note:
        out["note"] = note
    return out


def web_deductions(spec: dict, item: dict, checks: dict) -> list[dict]:
    """The four 'write an example of X' items.

    Mirrors derive_oc_ledger(): the definitional criteria gate everything — fail
    any and the answer is not operant conditioning whatever it looks like — then
    the type is checked, and an avoidance frame never deducts.
    """
    from agreement import answer_of, satisfied_map
    # Satisfaction is read through satisfied_map, NOT by comparing the verdict to
    # a literal. This compared it to "yes", which was the vocabulary before the
    # verdicts were standardised on met/absent — so after that change every
    # definitional criterion read as unmet, `is_oc` was false for every student,
    # and all four items charged NOT_OC in full and scored 0. cli_v7 predates the
    # standardisation, which is why the last CLI sweep did not show it.
    #
    # Asking satisfied_map is what stops it happening again: it mirrors
    # isSatisfied(), so the rule is "whatever the web counts as satisfied",
    # whatever the vocabulary becomes.
    sat = satisfied_map(spec, checks)
    yes = lambda k: bool(sat.get(k))
    codes = {d["code"]: d["pts"] for d in item["deductions"]}

    is_oc = yes("names_behavior") and yes("names_stimulus") and yes("contingent") and yes("follows_behavior")
    if not is_oc:
        return [_ded(item, "NOT_OC")]
    if not yes("you_arrange_it"):
        return [_ded(item, "NOT_EXTERNAL_STIMULUS")]

    # The classification answers `refers_to` since pick(); reading the verdict
    # returned "" and made every example look like the wrong type.
    observed = answer_of(checks, "observed_type")
    aimed_key = "targets_goal_behavior" if "targets_goal_behavior" in {s["key"] for s in spec["slots"]} \
        else "targets_unwanted_behavior"
    # `demonstrates_type` is now derived from `stimulus_move`, so read the
    # SATISFACTION of the derived check rather than comparing a classification.
    # Asking satisfied_map keeps this correct whichever primitive computes it.
    if "demonstrates_type" in {s["key"] for s in spec["slots"]}:
        if not yes("demonstrates_type"):
            return [_ded(item, "WRONG_TYPE")]
    elif observed != item["expected_type"]:
        return [_ded(item, "WRONG_TYPE")]
    if not yes(aimed_key):
        return [_ded(item, "WRONG_TYPE")]
    # A weighted slot this hand-written mirror does not name is INVISIBLE here:
    # the model answers it, the sheet records it, and the score ignores it. That
    # is how `barrier_is_not_this_type` fired 6/6 on NR/p14 and the cell still
    # read 4.0. Guarded on presence in the sheet, because absent means the slot
    # is not authored on this item, not that it failed.
    keys = {s["key"] for s in spec["slots"]}
    if "barrier_is_not_this_type" in keys and not yes("barrier_is_not_this_type"):
        return [_ded(item, "WRONG_TYPE")]
    return []


def score_web(spec: dict, item: dict, checks: dict) -> tuple[float, int]:
    """Score and deduction-count, DERIVED from the coded deductions above.

    One enumeration, two readings. Before this the codes were known inline --
    `codes["WRONG_TYPE"]` -- and thrown away at the `return`, so the web mirror
    could say how much it took and never which rule took it. Deriving the pair
    here means the number and the name cannot drift apart.
    """
    deds = web_deductions(spec, item, checks)
    lost = sum(d["pts"] for d in deds)
    return max(0.0, min(item["max"], item["max"] - lost)), len(deds)


def web_deductions_cadence(spec: dict, item: dict, checks: dict) -> list[dict]:
    """The daily/weekly example items — as above plus cadence, and the type is
    whatever the student chose rather than a fixed one."""
    from agreement import satisfied_map
    sat = satisfied_map(spec, checks)          # see score_oc: never a literal
    yes = lambda k: bool(sat.get(k))
    codes = {d["code"]: d["pts"] for d in item["deductions"]}

    is_oc = yes("names_behavior") and yes("names_stimulus") and yes("contingent") and yes("follows_behavior")
    if not is_oc:
        return [_ded(item, "NOT_OC")]
    if not yes("you_arrange_it"):
        return [_ded(item, "NOT_EXTERNAL_STIMULUS")]

    # Resolved against the item's OWN slot keys rather than named outright,
    # the same mechanism enforcement.web_name uses for the avoidance_frame and
    # observed_type aliases, and for the same reason: the daily pair no longer
    # shares one name. DAY1 keeps `cadence_is_daily`; DAY2 carries
    # `cadence_is_daily_counted`, which asks the counting question. Candidates are
    # mutually exclusive across the sheets, so the order is not load-bearing --
    # but the fallback is, and it is the FIRST candidate so an item whose sheet
    # has neither still raises on a missing slot instead of silently ungating.
    # FROM THE RUBRIC, NOT FROM THE BLOCK ENTRY. Both facts were carried on the
    # BLOCKS declaration too, agreeing with the rubric on all eight items --
    # which is the state a drift starts from. `item` here IS the rubric row.
    _cad = (("cadence_is_daily", "cadence_is_daily_counted")
            if item["cadence"] == "daily" else ("cadence_is_weekly",))
    _have = {s["key"] for s in spec["slots"]}
    cadence_key = next((k for k in _cad if k in _have), _cad[0])
    if not yes(cadence_key):
        return [_ded(item, "CADENCE_MISMATCH")]

    # Any OTHER slot the sheet marks as gating, honoured generically. lo-blocks'
    # failedGate walks every slot and zeroes the item on the first unsatisfied
    # gate, so a `!` added to a slots= list changes the app's behaviour with no
    # code change anywhere — while this mirror knew only the gates hardcoded
    # above and would have scored the same answer differently. The three keys
    # already handled are excluded because each maps to its OWN deduction code,
    # which is the distinction this function exists to make.
    _handled = {"names_behavior", "names_stimulus", "contingent",
                "follows_behavior", "you_arrange_it", cadence_key}
    for _s in spec["slots"]:
        if _s.get("gates") and _s["key"] not in _handled and not yes(_s["key"]):
            # THE SLOT'S OWN DECLARED CHARGE when it has one. This loop used to
            # hardcode NOT_OC for any gate it did not recognise; the rubric now
            # says which code each gate charges and carries the wording with it,
            # so read that and fall back only for a gate that declares neither.
            return [_ded(item, _s.get("charge") or "NOT_OC", _s.get("because"))]

    out = []
    if not yes("matches_chosen_type"):
        out.append(_ded(item, "TYPE_MISMATCH"))
    if not yes("targets_own_behavior"):
        out.append(_ded(item, "WRONG_BEHAVIOR"))
    # The item's fourth point, previously reachable only by a gate. `scoreSlotSheet`
    # charges this automatically from the sheet's `@1`, so omitting it here would
    # make the two sides score the same verdicts differently — the exact class of
    # divergence this harness exists to detect.
    if "consequence_asserted" in {s["key"] for s in spec["slots"]} \
            and not yes("consequence_asserted"):
        out.append(_ded(item, "LINK_NOT_ASSERTED"))
    return out


def score_web_cadence(spec: dict, item: dict, checks: dict) -> tuple[float, int]:
    """As `score_web`: score and count DERIVED from the coded deductions."""
    deds = web_deductions_cadence(spec, item, checks)
    lost = sum(d["pts"] for d in deds)
    return max(0.0, min(item["max"], item["max"] - lost)), len(deds)

# ── THE PROBE BUILDERS, moved from `enforcement.py`. Goal P, 2026-09-24 ──────
#
# The enforcement audit proves a rule FIRES by building a hypothetical answer
# that passes and then failing one field at a time. Those answers are this
# course's: they name `observed_type`, `named_type` and the PR/NR/PP/NP taxonomy,
# which is the one thing M's own analysis calls irreducibly course-specific.
# They sat in the engine, so the audit could only construct a probe for a course
# whose subject it already knew.
#
# The TABLES they read moved to the course file in the same goal
# (`PROBE_PASS`, `PROBE_FAIL`, `PROBE_TYPE_FIELDS`); these are the code that
# reads them, and it belongs on the same side.


def _probe_value(table: dict, key: str, item_id: str):
    """A probe-table value, resolved per item where the table says so.

    Most fields have one passing value everywhere. The valence fields do not:
    what a type REQUIRES differs by screen, so a flat value would make the
    probe's own all-satisfied baseline charge on some of them. A dict value is
    read as {item_id: value}.
    """
    v = table[key]
    return v.get(item_id) if isinstance(v, dict) else v


def probe_baseline(item: dict) -> dict:
    """An analysis that earns full marks."""
    import coursedata
    PASS = coursedata.declaration("PROBE_PASS")
    req = set(schema_fragment(item)["properties"]["oc_analysis"]["required"])
    a = {k: _probe_value(PASS, k, item["id"]) for k in PASS if k in req}
    if item.get("cadence"):
        a["observed_type"] = "PR"
        a["named_type"] = "PR"          # agreeing, so no mismatch
    else:
        a["observed_type"] = item["expected_type"]
    return a


def probe_fail(item: dict, a: dict, key: str, other: str = "") -> dict:
    """`a` with `key` failing. Type fields fail to a value that stays wrong."""
    import coursedata
    FAIL = coursedata.declaration("PROBE_FAIL")
    TYPE_FIELDS = tuple(coursedata.declaration("PROBE_TYPE_FIELDS"))
    a = dict(a)
    if key in TYPE_FIELDS:
        # Pick a type that differs from the one the item wants AND from whatever
        # the co-field was flipped to, so flipping both does not re-agree.
        wrong = [t for t in ("PR", "NR", "PP", "NP")
                 if t != a.get("observed_type") and t != a.get("named_type")]
        a[key] = wrong[1] if (other in TYPE_FIELDS and len(wrong) > 1) else wrong[0]
    else:
        a[key] = _probe_value(FAIL, key, item["id"])
    return a

# ── WHAT THIS SCORER CONTRIBUTES BACK. Goal P, final two sites ──────────────
#
# The plugin contract said what a scorer READS (an item and an answer) and what
# it RETURNS (a ledger). It said nothing about what it contributes to the PROMPT
# or to the RESULT RECORD, so those two stayed in `score.py` -- the engine
# naming `consequence_asserted`, `avoidance_scores` and `avoidance_frame`
# because there was nowhere else to say them.


def prompt_section(item: dict, asked: dict) -> str:
    """This scorer's section of the item's prompt.

    `_criteria_section` is SHARED with the web deliberately, so the two cannot
    drift; what was course-specific was not the composer but the three arguments
    chosen for it -- which slots this course asks and whether the item gates on
    an avoidance frame. Those choices are the scorer's, and they live here now.
    """
    from olx_prompts import _criteria_section

    return _criteria_section(
        item,
        trigger_slot="trigger_behavior" in asked,
        consequence_slot="consequence_asserted" in asked,
        avoidance_scores=bool(item.get("avoidance_scores")),
    )


def record_fields(item: dict, raw: dict) -> dict:
    """Extra fields this scorer contributes to the result record.

    `avoidance_frame` is advisory -- it costs nothing and is surfaced so a reader
    can see the framing -- but it is an operant-conditioning concept, and the
    engine was writing it into every record by name. A scorer that has no such
    concept contributes nothing here, which is why the default is an empty dict
    rather than a required key.
    """
    a = raw.get("oc_analysis") or {}
    return {"avoidance_frame": bool(a.get("avoidance_frame"))}

# ── RESOLVING A RULE OPERAND ACROSS THE TWO SIDES' NAMES ────────────────────
#
# The declared rules name the WEB's slots -- `phrased_directly_gate`,
# `targets_goal_behavior`, `demonstrates_type` -- while this scorer asks its own
# (`avoidance_frame`, `targets_intended_behavior`, `stimulus_move`). Both names
# are THIS COURSE'S, and the course declares the mapping in `SIDE_ALIAS` and
# which of them inverts in `SIDE_INVERTED`.
#
# THE ALTERNATIVE WAS TO RENAME, AND IT WAS WITHDRAWN. The fact names live in
# authored teaching prose -- "5. `stimulus_is_arranged` -- is the consequence
# something the student arranges" -- so a rename meant rewriting the course's own
# text, ~90 sites, plus a 2,068-cell re-sweep because it changes what the model
# is asked. Resolving costs nothing and changes no prompt. Once the course names
# its slots, two names for one fact is the course's business and the engine's job
# is to resolve them.


def _side_map():
    """{other side's name: (this scorer's fact, inverted)}, as declared."""
    import coursedata

    alias = coursedata.declaration("SIDE_ALIAS")
    inverted = set(coursedata.declaration("SIDE_INVERTED"))
    out = {}
    for mine, theirs in alias.items():
        for name in ([theirs] if isinstance(theirs, str) else theirs):
            out[name] = (mine, mine in inverted)
    return out


def declared_names(mine: str) -> tuple:
    """Every name the OTHER side may use for this scorer's fact, from the alias.

    A fact can have more than one name over there and the course says so:
    `targets_intended_behavior -> ['targets_goal_behavior',
    'targets_unwanted_behavior']`, because reinforcement items aim at the GOAL
    behaviour and punishment items at the UNWANTED one -- one reading of the
    answer, named for what the item is about. A rule declared on PP under the
    second name is invisible to a lookup that knows only the first, which is how
    PP and NP came to charge twice for one fault.
    """
    import coursedata

    theirs = coursedata.declaration("SIDE_ALIAS").get(mine)
    if theirs is None:
        return (mine,)
    return tuple([theirs] if isinstance(theirs, str) else theirs)


def check_named(theirs: str, among=()) -> str:
    """The CHECK name this scorer records for the other side's slot key.

    The inverse of `declared_names`, and it exists for the same reason: the
    rubric declares its conjunctions over the SLOTS it also generates the web's
    sheet from (`names_behavior`, `contingent`, `you_arrange_it`), while this
    scorer records `operant_behavior`, `contingent_on_behavior`,
    `stimulus_is_arranged`. One declaration, two vocabularies, and the course
    already states the mapping.

    THE INVERSE IS AMBIGUOUS AND `among` IS HOW IT IS RESOLVED. Two of this
    scorer's names alias to one of the web's: `behavior` AND `operant_behavior`
    both map to `names_behavior` -- the first is the FACT the model answers, the
    second is the CHECK this scorer records from it. Returning whichever came
    first in the table dropped `operant_behavior` from the conjunction, and the
    feedback stopped naming a missing reading it had always named. Resolving
    against the names actually present picks the one the caller can use.

    Falls through to the name given, which is right for the several facts both
    sides call the same thing -- `follows_behavior` among them.
    """
    import coursedata

    pool = set(among)
    fallback = None
    for mine, theirs_names in coursedata.declaration("SIDE_ALIAS").items():
        names = [theirs_names] if isinstance(theirs_names, str) else theirs_names
        if theirs not in names:
            continue
        if mine in pool:
            return mine
        if fallback is None:
            fallback = mine
    if theirs in pool:
        return theirs
    return fallback or theirs


def resolve_operand(a: dict, key: str):
    """The model's answer for `key`, under EITHER side's name.

    NOT `agreement.answer_of`, which this module also imports (locally, in the
    paper-ledger path) -- that one reads a check's `refers_to ?? verdict` out of
    a raw artifact. This one resolves a RULE OPERAND's name across the two sides.
    Two different jobs; the names collided, so this one changed.

    ABSENT IS TRUE, the same rule as everywhere: a fact the model was never
    asked cannot have failed. An INVERTED fact is negated on the way through --
    `phrased_directly` met means NOT avoidance-framed, and reading one as the
    other is the divergence this mapping exists to close.
    """
    if key in a:
        return a[key]
    mine, inverted = _side_map().get(key, (None, False))
    if mine is None or mine not in a:
        return True
    v = a[mine]
    return (not v) if inverted else v
