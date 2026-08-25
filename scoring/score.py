"""Score Handout 1 submissions, one rubric item at a time.

Design notes:
  * One call per rubric item, not one per document. Each item has its own
    point ledger and its own feedback cell, and the gold data is per-item, so
    per-item calls are both more accurate and directly measurable.
  * The model never returns a score. It returns credit checks and a deduction
    ledger; the score is computed here as max - sum(deductions), clamped to
    [0, max]. That mirrors how these graders actually write ("-1 pt: ...") and
    makes every point auditable.
  * Items are scored in dependency order, because several are graded against
    other items: Q2's WGB against Q1's UTB, Q4b/Q4c against Q4a for
    distinctness, and Q6 against 4a and 4c for matching. Neighbours listed in
    a rubric record's `context` are passed in as read-only context.

Usage:
  python3 score_h1.py                       # score all 20, CLI backend
  python3 score_h1.py --participants 1 2 3   # subset
  python3 score_h1.py --backend api          # official SDK (needs creds)
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from backends import BackendError, make_backend
from handouts import config, find_submissions
from rubric_h2 import CONTINGENCY_GATE_ITEMS, POLARITY_GATE_ITEMS
from docx_text import extract_media, graph_evidence
from segment import repair_orphans, segment, utb_hint

SYSTEM_TMPL = """You are an experienced teaching assistant grading {blurb}
This is PSYC 1030 (General Psychology, intro level, first-year students).

You grade ONE rubric item at a time against the rubric supplied in the message.

Rules you must follow:
1. Award credit component by component. For each component in the rubric's
   credit list, decide whether the student's response earns it, and quote the
   span of the response that earns it. Quote verbatim; never paraphrase into
   the evidence field.
2. Report every failure as a deduction drawn from the supplied deduction list,
   using that list's exact `code`. The point value is the rubric's, not yours —
   you never restate it. A deduction marked repeatable may appear more than
   once (e.g. two missing reasons = two REASON_MISSING entries). Do not invent
   codes.
3. Do NOT output a score. The score is computed from your deduction ledger.
4. Total deductions must be consistent with the credit components you marked
   unmet: if you mark a 2-point component unmet, there must be a deduction
   accounting for it.
5. Grade what is written, generously but not charitably: these are first-year
   students, so clumsy phrasing that clearly conveys the required idea earns
   credit, but a required element that is absent is absent.
6. If the response is empty, mark every component unmet and use the item's
   "none"/"did not answer" deduction code.
7. Set safety_flag true only if the student describes something that could
   harm them (skipping meals, punishing themselves by withholding food or
   sleep, etc.). This never changes the score.
8. Set escalate true when no supplied deduction code fits what is wrong, when
   the response is off-topic or incoherent, or when you are genuinely unsure.

Return only the JSON object required by the schema."""

# No `item_id` and no per-deduction `pts`. Both were required properties whose
# values were then discarded — `score_item` returns `item["id"]` and replaces the
# model's points with `spec["pts"]` from the rubric — and asking for an answer
# that is thrown away is the same incoherence as listing a criterion with no slot
# to answer it in. The point VALUES stay in the prompt's deduction list, which is
# what the model needs in order to judge severity; only the echo is gone.
SCHEMA = {
    "type": "object",
    "properties": {
        "credit_checks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "what": {"type": "string"},
                    "met": {"type": "boolean"},
                    "evidence": {"type": "string"},
                },
                "required": ["what", "met", "evidence"],
                "additionalProperties": False,
            },
        },
        "deductions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "note": {"type": "string"},
                },
                "required": ["code", "note"],
                "additionalProperties": False,
            },
        },
        "advisory_note": {"type": ["string", "null"]},
        "safety_flag": {"type": "boolean"},
        "escalate": {"type": "boolean"},
    },
    "required": [
        "credit_checks",
        "deductions",
        "advisory_note",
        "safety_flag",
        "escalate",
    ],
    "additionalProperties": False,
}


def build_schema(item: dict) -> dict:
    """Schema for one item.

    For an item marked `derive_from_credit`, the model does not author a
    deduction ledger at all. It fills in one fixed slot object per credit
    component, and `score_item` derives the ledger from the unmet slots. The
    slots are *required object properties*, so "did the model remember to
    check slot 7" stops being a prompt-following question and becomes a schema
    constraint. (Q6's failure mode in baseline v3 was exactly that: gold
    implied 50 failed slots across the cohort and the model volunteered 31.)
    """
    if item.get("derive_from_criteria"):
        # The five definitional criteria are REQUIRED schema properties, so the
        # model cannot credit an example without first stating what the
        # behaviour is, what the stimulus is, and whether the stimulus is
        # contingent, subsequent, and arranged. Participant 13 was credited for
        # "{{corpus:WK1/p13:wk1:0:51:sha=848ae9e56f72}}" — no behaviour,
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
        if item.get("cadence"):
            props["named_type"] = {
                "type": "string",
                "enum": ["PR", "NR", "PP", "NP", "unclear"],
            }
            props["cadence_ok"] = {"type": "boolean"}
            # WK1 and DAY2 derive this from a CLASSIFICATION, mirroring the
            # web's pick + expect: the model names which behaviour the trigger
            # identifies and the engine compares it against the student's own.
            # Judged directly, the slot answered `met` on every pass of the cells
            # gold charges, because their own behaviour is in the sentence as the
            # PRIZE rather than as the trigger.
            # DAY2 only. Derived by reading all 64 counted cadence answers: the
            # nine over-credited cells that are not valence inversions share one
            # property — they state no contingency. They describe what the
            # student will do, or why, or offer one activity instead of another.
            # Every credited cell states a condition on the behaviour AND a
            # clause in which something is granted or withheld.
            if item.get("id") in CONTINGENCY_GATE_ITEMS:
                props["states_a_contingency"] = {"type": "boolean"}
            # The two halves of the direction test, answered separately. The
            # engine compares them; the model is never asked to weigh both at
            # once, which is what the composite clause did and why it never
            # fired. Mirrors the web's pick(valence) + pick(valence_or_none)
            # and its `equals` rule, lenient on `none`.
            if item.get("id") in POLARITY_GATE_ITEMS:
                props["consequence_valence"] = {
                    "type": "string", "enum": ["gain", "loss"]}
                props["trigger_expects"] = {
                    "type": "string", "enum": ["gain", "loss", "none"]}
            if item.get("id") == "WK1":
                props["trigger_behavior"] = {
                    "type": "string", "enum": ["utb", "wgb", "other"]}
            else:
                props["targets_own_behavior"] = {"type": "boolean"}
            # WK2 only, mirroring a question the TYPE items have always asked and
            # the cadence items never did. There, `targets_intended_behavior`
            # charges WRONG_TYPE when the arrangement is the right type but
            # pointed the wrong way; here, `targets_own_behavior` asks only WHOSE
            # behaviour it is. So an answer that delivers an aversive for SUCCESS
            # — punishing the goal behaviour — passes every check on the sheet.
            if item.get("id") == "WK2":
                props["aimed_correctly"] = {"type": "boolean"}
            # WK1 only, and asked as a PARSE rather than a judgement — see the
            # guidance in rubric_h2. Two earlier versions asked "is a consequence
            # delivered?" and the model answered inconsistently on the two cells
            # that matter; the cue it can actually apply is syntactic.
            if item.get("id") == "WK1":
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

    if not item.get("derive_from_credit"):
        return SCHEMA

    def _slot(vocab: list[str] | None) -> dict:
        # A slot in a cover group answers WHICH of the referenced items it names,
        # and that identity is its verdict — there is no second question. The
        # pairing is `derive_ledger`'s.
        return {
            "type": "object",
            "properties": {
                "verdict": {
                    "type": "string",
                    "enum": vocab or ["met", "absent", "mismatch", "not_described"],
                },
                "evidence": {"type": "string"},
            },
            "required": ["verdict", "evidence"],
            "additionalProperties": False,
        }

    grouped = {k: g["verdicts"] for g in item.get("cover", []) for k in g["keys"]}
    # A check the code COMPUTES is left out entirely: asking for an answer that is
    # then discarded is the incoherence the removed `pts`/`item_id` fields were.
    computed = {r["key"] for r in item.get("equals", [])}
    # A counted group asks HOW MANY once, instead of asking each member. The
    # members are derived, so they leave the schema the way a computed check does.
    for cr in item.get("counts", []):
        computed |= set(cr["slots"])
    slots = {c["what"]: _slot(grouped.get(c["what"]) or c.get("verdicts"))
             for c in item["credit"] if c["what"] not in computed}
    schema = json.loads(json.dumps(SCHEMA))  # deep copy
    del schema["properties"]["credit_checks"]
    del schema["properties"]["deductions"]
    schema["properties"]["slots"] = {
        "type": "object",
        "properties": slots,
        "required": list(slots),
        "additionalProperties": False,
    }
    schema["required"] = [
        r for r in schema["required"] if r not in ("credit_checks", "deductions")
    ] + ["slots"]
    return schema


def derive_ledger(item: dict, raw: dict,
                  response: str = "") -> tuple[list[dict], list[dict], list[str]]:
    """Turn a slot verdict sheet into a deduction ledger.

    One slot, one deduction, by construction — the stacking that produced
    participant 9's double-penalty in baseline v1 is unrepresentable here.
    """
    slots = raw.get("slots") or {}
    ledger, checks, unknown = [], [], []

    # Cover groups: the slots in a group must name DIFFERENT members of the list
    # they refer to. The model reports which one each names; the pairing is done
    # here, so ordering is free and a double-claim cannot be credited.
    #
    # `demoted[key] = (codes-key, note)`. Only a slot the model called `met` can
    # be demoted — anything else is already failing on its own verdict. A missing
    # `matches` demotes nothing: the field is schema-required, so its absence
    # means a provider ignored the schema, and inventing a deduction from that
    # would be worse than losing the check.
    demoted: dict[str, tuple[str, str]] = {}
    for group in item.get("cover", []):
        claimed: dict[str, str] = {}
        for key in group["keys"]:
            v = ((slots.get(key) or {}).get("verdict") or "").strip()
            if v not in group["labels"]:
                continue          # `absent` or `neither`: already failing on its own
            if v in claimed:
                demoted[key] = (
                    "absent",
                    f"Names the same {group['of']} item as `{claimed[v]}` ({v}), so "
                    f"the other one is never addressed.",
                )
            else:
                claimed[v] = key

    # A counted group: the model reports how many of a repeated element it found,
    # and the code turns that into one verdict per member slot.
    #
    # Q1 is why this exists. Asked as three independent slots — "is there a third
    # distinct reason?" — it scored 76% / MAE 0.29 against the plain path's 88% /
    # 0.18, replicated. Its rubric is the one that says to be GENEROUS about
    # distinctness, and that judgement gets worse when it is split up. The plain path
    # was already counting: it emitted REASON_MISSING repeatably. So this keeps the
    # derived structure and gives the counting back, as one question.
    # The member records carry the SPANS the model quoted, not a placeholder.
    # They used to read `evidence: "2 found"`, which is honest about a derived
    # verdict and useless to the other consumer of this field: agreement_app
    # rebuilds the web's separate input boxes from these records, and a
    # placeholder went into the student's box verbatim. 2a fell from 90% to 5%
    # and item 3 from 95% to 10% on BOTH shipped scorers, and the model's own
    # feedback named it ("both are just '2 found'"). stale_check.py could not
    # see it: a placeholder IS correct evidence for a derived member, so the
    # records matched the rubric exactly.
    #
    # The spans are already in hand. The model enumerates what it counted in the
    # GROUP slot's evidence — `HOW #1: "..." HOW #2: "..."`, or `(1) "..."
    # (2) "..."` — so they are parsed out here and distributed, and the harness
    # no longer has to reverse-engineer this record's format.
    #
    # Truncated to n on purpose: p1's 2a evidence quotes two stretches while
    # hows_given is 1, the second explicitly rejected ("No second ..."). The
    # count decides how many are real, the quotes decide which.
    #
    # This does NOT change any score. The ledger below derives from the count,
    # and evidence is never scored — measured identical on all three handouts.
    # Where the evidence carries no quotes at all (item 3's is free prose in
    # every cell) the placeholder stays and agreement_app falls back to dealing
    # the block itself.
    for cr in item.get("counts", []):
        raw_n = ((slots.get(cr["key"]) or {}).get("verdict") or "").strip()
        try:
            n = int(raw_n)
        except ValueError:
            n = 0
        group_ev = ((slots.get(cr["key"]) or {}).get("evidence") or "")
        spans = [" ".join(q.split())
                 for q in re.findall(r'"([^"]{12,})"', group_ev)][:n]
        for i, key in enumerate(cr["slots"]):
            ev = spans[i] if i < len(spans) else f"{raw_n or '0'} found"
            slots[key] = {"verdict": "met" if i < n else "absent",
                          "evidence": ev}

    # A computed check's verdict comes from comparing two answered ones. Same rule
    # as the web's `equals`: operands that mean "cannot tell" SATISFY it, because a
    # mismatch that cannot be established is not one the rubric charges.
    for rule in item.get("equals", []):
        left = ((slots.get(rule["left"]) or {}).get("verdict") or "").strip()
        right = ((slots.get(rule["right"]) or {}).get("verdict") or "").strip()
        lenient = rule.get("lenient") or []
        ok = (left in lenient or right in lenient
              or (bool(left) and bool(right) and left == right))
        spec = next(c for c in item["credit"] if c["what"] == rule["key"])
        slots[rule["key"]] = {
            "verdict": spec["verdicts"][0] if ok else spec["verdicts"][-1],
            "evidence": (f"{rule['left']}={left or '?'}, {rule['right']}={right or '?'}"
                         + (" — no mismatch established" if ok and
                            (left in lenient or right in lenient) else "")),
        }

    satisfying = {k: g["labels"] for g in item.get("cover", []) for k in g["keys"]}

    # `requires`: a check is CREDITED only while its condition holds — the mirror
    # of the charge-once rule below, and applied here, after the cover demotions,
    # so a condition may itself be a cover check. A denied slot is demoted rather
    # than rewritten, for the reason the cover block gives: the model's verdict
    # about that box was true, and the finding is about the pair.
    for rule in item.get("requires", []):
        cond = rule["cond"]
        cverdict = ((slots.get(cond) or {}).get("verdict") or "").strip()
        if cverdict in (rule.get("lenient") or []):
            continue                      # establishes nothing, so denies nothing
        held = (cverdict in satisfying[cond] if cond in satisfying
                else cverdict == "met") and cond not in demoted
        if not held and rule["key"] not in demoted:
            demoted[rule["key"]] = (
                "absent",
                f"`{cond}` did not hold, so this was never separately addressed.",
            )

    # Charge-once, ported from the web's `onlyif`. Some codes span more than one
    # slot: Q4b's B_NO_MODIFY (-2) covers "did not say IF it is a good choice AND
    # why", while B_NO_MODIFY_WHY (-1) covers only the second half. Expressed as two
    # independent 1-point slots the pair charges 2 under two codes, neither at the
    # value the graders' phrase bank gives it. Expressed as a 2-point slot plus a
    # 1-point slot suppressed when the first fails, both codes are emitted at their
    # dictionary amounts and the total is still 2.
    suppressed: set[str] = set()
    for rule in item.get("onlyif", []):
        cspec = next((c for c in item["credit"] if c["what"] == rule["cond"]), None)
        if cspec is None:
            # An unknown condition suppresses nothing. The first version read the
            # missing slot's verdict as "" and treated that as a failed condition,
            # so a typo in `cond` silently cancelled the deduction — the exact
            # inverse of the web's rule, which is written out in `chargedMap`:
            # a typo must not stop a check being charged.
            continue
        cond = ((slots.get(rule["cond"]) or {}).get("verdict") or "").strip()
        if cond not in (cspec.get("verdicts") or ["met"])[:1]:
            suppressed.add(rule["key"])

    for comp in item["credit"]:
        got = slots.get(comp["what"]) or {}
        verdict = got.get("verdict", "absent")
        evidence = got.get("evidence", "")
        dem = demoted.get(comp["what"])
        ok = verdict in satisfying[comp["what"]] if comp["what"] in satisfying \
            else verdict == "met"
        met = ok and dem is None
        # The VERDICT is kept, not just met/unmet. `absent` and `mismatch` cost
        # the same points but are different findings: a mismatch means the
        # student DID write something, it just is not the 4a/4c item. Downstream
        # (agreement_app.scorer_evidence) that distinction decides whether their
        # words are the right fixture for the web version's box or whether an
        # empty box is — and with only `met` recorded, four of Q6's boxes were
        # emptied on responses where gold says the student wrote a mismatch.
        #
        # A demotion does NOT rewrite the verdict. The model's `met` was a true
        # statement about that box — the student did name a 4a/4c item there —
        # and the finding is about the PAIR, not the box. Keeping the reported
        # verdict also keeps `scorer_evidence` correct: a demoted box still holds
        # the student's words, so it must not be emptied the way `absent` is.
        rec = {"what": comp["what"], "met": met, "verdict": verdict,
               "evidence": evidence}
        if dem is not None:
            rec["demoted"] = dem[1]
        checks.append(rec)
        # Reported-only: the model states it because a later check needs it, but it
        # is not a component of the score and can never produce a deduction.
        # Suppressed: its finding is already carried by the code that subsumes it.
        if met or comp.get("reported") or comp["what"] in suppressed:
            continue
        code = comp.get("codes", {}).get(dem[0] if dem else verdict)
        if code is None:
            # Verdict that does not apply to this slot (e.g. "mismatch" on a
            # change slot). Fall back to the slot's own primary code.
            code = next(iter(comp.get("codes", {}).values()), None)
            if code is None:
                unknown.append(f"{comp['what']}:{verdict}")
                continue
        pts = item["max"] if comp.get("gates") else comp["pts"]
        ledger.append({"code": code, "pts": pts,
                       "note": dem[1] if dem else evidence})
        if comp.get("gates"):
            # A gating slot subsumes the rest; report it alone.
            return [ledger[-1]], checks, unknown

    # Nothing at all was answered: report it the way the graders did, as a
    # single "did not answer", rather than as eight separate slot failures.
    #
    # Gated on the response ACTUALLY being blank, which is what `blank_code`
    # says. It used to fire whenever every scorable slot failed, for any reason —
    # so an answer that was written and wrong collapsed to "did not answer" too.
    # Q5 p4 wrote two sentences, both judged the wrong kind of reason, and the
    # ledger recorded W_NONE while the model's own notes said "W_NOT_REASON;
    # W_NOT_REASON"; the feedback the STUDENT reads then opened with "did not
    # answer" about an answer they had written. It was invisible in every number
    # because the arithmetic agrees — two 2.5s and one 5.0 both clamp to 0 — so
    # only the code and the prose were wrong, which is the half a student sees.
    #
    # The code is DECLARED (`blank_code`), full stop. It used to fall back to
    # matching the literal text "did not answer", which worked only while every
    # such code used that exact wording — 1b's says "did not provide data" — and an
    # item that wanted the collapse but was reworded would have lost it in silence.
    # An item with no `blank_code` simply has no collapse, which is now a property
    # of the rubric rather than of a phrase.
    # Counted against the SCORABLE slots: reported-only ones never enter the
    # ledger, so comparing with the full credit list could never match.
    scorable = [c for c in item["credit"]
                if not c.get("reported") and c["what"] not in suppressed]
    # Only worth collapsing when there is more than one failure to collapse. A
    # single-slot item would otherwise report every failure as "did not answer",
    # losing the distinction the vocabulary exists for — T1's `not_a_type` came
    # back as BLANK.
    if (len(scorable) > 1 and len(ledger) == len(scorable)
            and not (response or "").strip()):
        want = item.get("blank_code")
        none_code = next((d for d in item["deductions"] if d["code"] == want), None)
        if none_code:
            ledger = [{"code": none_code["code"], "pts": none_code["pts"], "note": ""}]
    return ledger, checks, unknown


def derive_oc_ledger(item: dict, raw: dict) -> tuple[list[dict], list[dict], list[str], str | None]:
    """Turn the criteria sheet into a deduction ledger.

    Criteria 1-3 of the definition (an operant, a contingency, correct temporal
    order) plus the arranged-stimulus rule gate everything: fail any and the
    answer is not operant conditioning, whatever it looks like. Only if it
    passes do we ask which of the four types it is.
    """
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

    if not is_oc:
        missing = [c["what"] for c in checks[:4] if not c["met"]]
        add("NOT_OC", f"Missing: {', '.join(missing)}.")
        return ledger, checks, unknown, advisory
    if not arranged:
        add("NOT_EXTERNAL_STIMULUS", "The consequence is the behaviour's own automatic result.")
        return ledger, checks, unknown, advisory

    observed = a.get("observed_type", "none")
    if item.get("cadence"):
        named = a.get("named_type", "unclear")
        checks.append({"what": "matches_chosen_type", "met": observed == named, "evidence": f"observed {observed}, named {named}"})
        if not a.get("cadence_ok", True):
            add("CADENCE_MISMATCH")
            return ledger, checks, unknown, advisory
        if named != "unclear" and observed != named:
            add("TYPE_MISMATCH", f"This example is {observed}, but you chose {named}.")
        if item.get("id") == "WK1":
            aimed = str(a.get("trigger_behavior", "utb")).strip() in ("utb", "wgb")
        else:
            aimed = a.get("targets_own_behavior", True)
        checks.append({"what": "targets_own_behavior", "met": bool(aimed),
                       "evidence": ""})
        if not aimed:
            add("WRONG_BEHAVIOR")
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
        if item.get("id") == "WK2":
            aimed_right = a.get("aimed_correctly", True)
            checks.append({"what": "aimed_correctly", "met": bool(aimed_right),
                           "evidence": ""})
            if not aimed_right:
                add("NOT_OC", "The consequence is pointed the wrong way: an "
                              "aversive for meeting the goal, or a reward for "
                              "missing it.")
                return ledger, checks, unknown, advisory

        if item.get("id") == "WK1":
            agentive = a.get("agent_delivers_consequence", True)
            checks.append({"what": "agent_delivers_consequence",
                           "met": bool(agentive), "evidence": ""})
            if not agentive:
                add("NOT_OC", "No one is named as adding or removing anything: "
                              "the consequence clause has no agent.")
                return ledger, checks, unknown, advisory

        if item.get("id") in CONTINGENCY_GATE_ITEMS:
            stated = a.get("states_a_contingency", True)
            checks.append({"what": "states_a_contingency", "met": bool(stated),
                           "evidence": ""})
            if not stated:
                add("NOT_OC", "No contingency is stated: nothing is granted or "
                              "withheld on a condition.")
                return ledger, checks, unknown, advisory

        if item.get("id") in POLARITY_GATE_ITEMS:
            # Same formula as agreement.apply_computed's `equals`, lenient on
            # `none`: a sentence stating no condition is clause (a)'s business,
            # not this gate's, so `none` on either side passes here.
            lenient = ("none",)
            cv = a.get("consequence_valence") or ""
            te = a.get("trigger_expects") or ""
            ok = (cv in lenient or te in lenient
                  or (bool(cv) and bool(te) and cv == te))
            checks.append({"what": "direction_ok", "met": bool(ok),
                           "evidence": f"consequence_valence={cv or '?'}, "
                                       f"trigger_expects={te or '?'}"})
            if not ok:
                add("NOT_OC", "The consequence runs the wrong way: a "
                              f"{cv} follows the student doing "
                              f"{'well' if te == 'gain' else 'badly'}, which "
                              "would push the behaviour in the wrong direction.")
                return ledger, checks, unknown, advisory

        asserted = a.get("consequence_asserted", True)
        checks.append({"what": "consequence_asserted", "met": bool(asserted),
                       "evidence": ""})
        if not asserted:
            add("LINK_NOT_ASSERTED")
    else:
        expected = item.get("expected_type")
        checks.append({"what": f"is_{str(expected).lower()}", "met": observed == expected, "evidence": f"observed {observed}"})
        aimed = a.get("targets_intended_behavior", True)
        checks.append({"what": "targets_intended_behavior", "met": bool(aimed), "evidence": ""})
        if observed != expected:
            add("WRONG_TYPE", f"This example is {observed}.")
        elif not aimed:
            # Right type, wrong target: the handout says reinforcement examples
            # increase the WGB and punishment examples decrease the UTB. An NR
            # that reinforces the unwanted behaviour is not a usable answer.
            add("WRONG_TYPE", "This reinforces the unwanted behaviour rather than the goal behaviour.")

    if a.get("avoidance_frame") and item.get("id") == "DAY1":
        # DAY1 GATES on this, and the CLI must gate with it or the two
        # implementations score the same answer differently — the divergence
        # class this project exists to close, and the one `equivalence.py` flags
        # as GATE WEB ONLY.
        #
        # The standing decision was to flag and never deduct: an avoidance-framed
        # contingency is structurally sound, so zeroing it looked like punishing
        # phrasing. The cohort disagrees on THIS item. Of the five DAY1 cells
        # where the web's `phrased_directly` ever answers `absent`, gold scores
        # four of them 0 and the fifth we already miss for other reasons, so
        # `absent` predicts gold's zero and honouring it costs nothing. Measured:
        # DAY1 15/18 -> 16/18, p8 from wrong in every run to right in six of six
        # probe passes, p14 recovering to 6/6, both controls holding.
        #
        # Deliberately NOT extended to the other items. WK1's p8 answer is not
        # avoidance-framed at all and stays declared; PR/NR/PP/NP were never
        # measured for this and three of them are perfect as they stand.
        add("NOT_OC", "The consequence is stated only as something avoided.")
        return ledger, checks, unknown, advisory

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


MEDIA_DIR = "/tmp/claude-1000/molly_scoring_media"


def oc_passing_sheet(item: dict) -> dict:
    """A criteria sheet for `item` on which nothing fails.

    Built from `build_schema`'s own required properties, so a criterion added
    there is covered here without being named twice.
    """
    req = build_schema(item)["properties"]["oc_analysis"]
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


def oc_check_names(item: dict) -> list[str]:
    """The credit_checks names `derive_oc_ledger` writes when nothing fails.

    Obtained by running the real ledger over a passing sheet rather than by
    listing the names, because a hand-kept list is exactly what went wrong
    before: stale_check.py could not audit these items at all, assumed the
    rubric's credit list stood in for them, and reported all eight of handout
    2's operant-conditioning items as stale when none were.
    """
    _, checks, _, _ = derive_oc_ledger(item, {"oc_analysis": oc_passing_sheet(item)})
    return [c["what"] for c in checks]


def graph_bundle(path: str, pid: int, shape_text: str) -> str:
    """Everything known about this submission's graph, in one block.

    Three representations are possible and any of them can be the student's
    graph: an OOXML chart part (labels readable from XML), an embedded image
    (needs looking at), or grouped drawing shapes whose labels arrive as
    ordinary document text. The blank template contributes one worked example
    chart, which is labelled here so it is not mistaken for the student's.
    """
    ev = graph_evidence(path)
    lines = []
    student = [c for c in ev["charts"] if c.get("origin") == "student"]
    template = [c for c in ev["charts"] if c.get("origin") != "student"]

    for c in student:
        lines.append(
            f"- CHART PART (origin: STUDENT). Text found in the chart XML: "
            f"{c['texts']}. Legend element present: {c['has_legend']}. "
            f"Axis elements: {c['n_axes']}."
        )
    for c in template:
        lines.append(
            f"- CHART PART (origin: TEMPLATE — this is the blank handout's worked "
            f"example, NOT the student's work; ignore it): {c['texts'][:2]}"
        )
    if ev["media"]:
        paths = extract_media(path, os.path.join(MEDIA_DIR, f"p{pid:03d}"))
        for p in paths:
            lines.append(
                f"- IMAGE at {p} — use the Read tool to look at it. Decide from its "
                "content whether it is the student's own graph or the template's "
                "'Water {{corpus:1c/p5:title:5:32:sha=97ca3baaf650:shape=R27-0-27}} example, then read off its title, "
                "axis labels and legend."
            )
    if shape_text.strip():
        lines.append(
            "- TEXT under the student's 1c heading. This may be a graph drawn as grouped "
            "shapes (in which case the title, tick values and series names arrive jammed "
            "together), or it may be the student merely DESCRIBING a graph they did not "
            f"actually produce. Decide which: {shape_text[:600]!r}"
        )
    if not lines:
        lines.append("- NOTHING. No chart part, no image, and no text under 1c.")
    return "\n".join(lines)


def _fail_verdict(item: dict, c: dict) -> str:
    """The verdict THIS scorer offers for a `{fail}` placeholder in a `rule`.

    The web's `_fail_token` reads the slot sheet, where every slot carries its
    own option list. Here the vocabulary can live in either of two places: on
    the credit entry's own `verdicts`, or — for a slot in a `cover` group, whose
    options are an IDENTITY (`first`/`second`/`neither`/`absent`) rather than a
    judgement — on the group. Reading only the credit entry made a cover slot
    fall through to the "absent" default, so a rule about naming the WRONG thing
    told the paper scorer to answer "the box was empty". Same class of bug as
    parking a rule in SLOT_NOTES: the rule reaches every scorer, but one of them
    is handed the wrong verdict to apply it with.
    """
    verdicts = list(c.get("verdicts") or [])
    skip = {"met", "absent"}
    if not verdicts:
        for grp in item.get("cover", []):
            if c["what"] in grp["keys"]:
                verdicts = list(grp.get("verdicts") or [])
                # `first`/`second` say WHICH one it is: those are the satisfied
                # answers here, so they are skipped alongside `met`.
                skip |= set(grp.get("labels") or [])
                break
    if not verdicts:
        # Third home, and the common one on this rubric: NO Q6 credit entry
        # declares `verdicts` at all, so a slot outside a cover group has its
        # failure vocabulary only in `codes` — `not_described` is the paper-side
        # counterpart of the web sheet's `incomplete`. Falling straight through
        # to "absent" told the paper scorer a rule about wrongly-described
        # content fires when the box is EMPTY. Reading `codes` fixes the whole
        # class rather than the two slots that happen to carry a rule today.
        verdicts = [k for k in (c.get("codes") or {}) if k != "absent"]
    return next((v for v in verdicts if v not in skip), "absent")


def build_prompt(
    item: dict,
    response: str,
    context: dict[str, str],
    hint: str | None,
    extra: str | None = None,
) -> str:
    parts = [f"# Rubric item {item['id']} — {item['max']:g} points\n"]
    parts.append(f"## Question asked of the student\n{item['question']}\n")

    if item.get("derive_from_criteria"):
        parts.append(
            "## How to judge this item\n"
            "Do NOT output a score or a deduction list. Fill in the criteria sheet; the "
            "score is computed from it.\n\n"
            "Operant conditioning means: the future probability of a VOLUNTARY BEHAVIOUR "
            "is changed by a CONSEQUENCE that is contingent on it. Answer these in order "
            "and answer them literally about what the student wrote:\n"
            "1. `behavior` — quote the voluntary behaviour of the student that the plan "
            "acts on. If the answer names no behaviour of theirs, leave this an empty "
            "string.\n"
            "2. `stimulus` — quote the thing being added or taken away. Empty string if "
            "none is named.\n"
            "3. `contingent` — is the stimulus delivered BECAUSE of that behaviour (or its "
            "absence)? A statement of something the student will just do, with no link to "
            "performing the behaviour, is not contingent.\n"
            "4. `follows_behavior` — does the CONSEQUENCE EVENT (gaining or losing the "
            "thing) occur after the behaviour? Judge the delivery, not the wording. "
            "\"I am not allowed X until I do B\" DOES satisfy this: X is delivered once B "
            "happens, which is the ordinary shape of a reinforcement contingency. It fails "
            "only when nothing is ever delivered contingent on the behaviour — the plan is "
            "purely to remove a temptation or set up the environment in advance, which is "
            "an antecedent manipulation rather than a consequence.\n"
            "5. `stimulus_is_arranged` — is the consequence something the student arranges, "
            "as opposed to the behaviour's own automatic result? Removing an obligation or "
            "chore IS arranged; '{{corpus:PR/p1:pr:0:42:sha=34e8b80f4178:shape=C1}} body' is not.\n"
            "6. `observed_type` — given increase-or-decrease and add-or-remove, which of "
            "PR/NR/PP/NP is it actually? Use `none` only if 1-4 fail.\n"
            "   DUAL DESCRIPTIONS: an arrangement of the form \"I am not allowed X until I "
            "do B\" is genuinely describable two ways — as PR of B (X is granted once B "
            "happens) and as NP of not-B (X is withheld while B is absent). Both are "
            "correct readings. When the arrangement admits both and one of them is the "
            "type under discussion, report that one; do not mark it a mismatch.\n"
            "7. `avoidance_frame` — true if the contingency is phrased by what is AVOIDED "
            "when the behaviour occurs (\"so I don't have to do the extra chore if I miss "
            "it\") rather than by what is added or removed after it. "
            + ("On THIS item a true answer takes the whole 4: an answer whose only claim "
               "is about dodging a penalty has not said what will be added or taken away "
               "when the behaviour happens, and the graders scored those zero. Answer "
               "true only when the sentence's own claim is the avoidance — not merely "
               "because a penalty is mentioned. "
               if item.get("id") == "DAY1" else
               "This never changes the score; it flags the answer for a phrasing "
               "comment. ")
            + "It is the ONLY criterion that judges this phrasing — no other check may "
            "deduct for it.\n"
        )
        if item.get("cadence"):
            parts.append(
                f"8. `named_type` — which of the four the student SAID they would use. Read "
                "the type slot in the context below; if it is blank or garbled, fall back to "
                "their DEFINITION, which usually states the type plainly (\"{{corpus:D2/p15:d2:28:41:sha=561e03f6a586:shape=R13-0-20}}"
                "{{corpus:D2/p15:d2:42:110:sha=bd23c4b2e196}}\" is "
                "Positive Punishment). Use `unclear` only when neither says.\n"
                f"9. `cadence_ok` — is the TRIGGER evaluated {item['cadence']}? Judge only "
                "how often the behaviour is checked, not how long the consequence lasts: a "
                "daily trigger whose reward runs to the end of the week is still daily. Set "
                "this false only when the contingency is plainly settled on the other "
                f"schedule — e.g. a daily slot answered with a whole-week tally.\n"
                + ("10. `trigger_behavior` — name which behaviour has to happen, or "
                   "fail to happen, before the consequence arrives, then answer "
                   "`utb`, `wgb` or `other` by WHAT KIND OF PHRASE it is. A POINTER "
                   "(\"my goal\", \"my daily goal\", \"my plan\") has no content of "
                   "its own: classify it as whatever it points at. A NAMED ACTIVITY "
                   "(\"procrastinating\", \"reading a chapter\") has content: judge it "
                   "against the behaviour the student CHOSE. Their paragraph also "
                   "explains why they chose it, and the causes and knock-on habits "
                   "it mentions are not the chosen behaviour — a plan triggered on "
                   "one of those is `other`.\n"
                   if item.get("id") == "WK1" else
                   "10. `targets_own_behavior` — is it aimed at this student's own "
                   "UTB/WGB rather than some clearly different behaviour?\n")
                # Kept near-verbatim from olx_prompts.SLOT_NOTES['consequence_asserted']
                +
                # so both implementations put the same question to the model. If
                # you retune one, retune the other and re-baseline; the wording is
                # deliberately narrow because the over-credited cells it targets do
                # not share one statable property.
                "11. `consequence_asserted` — false ONLY when the answer merely "
                "JUXTAPOSES behaviour and consequence without asserting one follows "
                "from the other: \"{{corpus:DAY2/p13:day2:0:49:sha=28fcf479970c:shape=R32-3-414e44,R49-0-20}}"
                "{{corpus:DAY2/p13:day2:50:82:sha=044c35247226}}\" is false, while \"{{corpus:DAY1/p16:day1:0:11:sha=4f4bb2cd8fe8:shape=R11-0-20}}"
                "{{corpus:DAY1/p16:day1:12:58:sha=445fd12bcc9c:shape=C180}} TV\" is true — the "
                "same two facts, but the second asserts the link. Anything with if / "
                "when / for each / every time / until / once, naming something "
                "actually given or taken away, is true — including withholding a "
                "reward until the behaviour happens, which is a normal reinforcement "
                "shape. This criterion does NOT judge phrasing: a consequence stated "
                "by what is AVOIDED asserts the link perfectly well and is true here. "
                "Criterion 7 is the only place that phrasing is recorded, and it "
                "never changes the score.\n"
            )
        parts.append("")
    elif item.get("derive_from_credit"):
        computed = {r["key"] for r in item.get("equals", [])}
        worths = {c.get("pts") for c in item["credit"] if not c.get("reported")
                  and not c.get("gates")}
        # Not `.pop()`: mutating the set here made the per-slot suffix below fire
        # as well, so every slot carried its points twice over.
        one = next(iter(worths)) if len(worths) == 1 else None
        parts.append(
            "## Slots to judge — return a verdict for EVERY one of these\n"
            + (f"Each slot is worth {one:g} point{'' if one == 1 else 's'} and is "
               "judged independently." if one is not None else
               "Each slot is judged independently; what each is worth is shown "
               "beside it.")
        )
        for c in item["credit"]:
            if c["what"] in computed:
                continue
            # `c.get("pts") is None` is checked as well as `reported`: an
            # unpointed slot that nobody flagged used to reach the format spec and
            # take the whole run down with a TypeError. Belt as well as braces —
            # the flag is the right fix, this stops the next omission crashing.
            worth = (" **GATE**" if c.get("gates") else
                     "" if c.get("reported") or c.get("pts") is None else
                     f" ({c['pts']:g} pt)" if one is None else "")
            vocab = (f" — {'/'.join('`%s`' % v for v in c['verdicts'])}"
                     if c.get("verdicts") else "")
            # The rubric's per-component `rule` is slot-specific judging text, and
            # the paper prompt's slot-specific field is this line. Without it the
            # web and CLI apply rules this scorer has never seen — which is how
            # Q4b's five substitution tests reached two scorers out of three.
            rule = f" {c['rule'].replace('{fail}', _fail_verdict(item, c))}" if c.get("rule") else ""
            parts.append(f"- `{c['what']}`{worth}{vocab}: {c['desc']}{rule}")
        for cr in item.get("counts", []):
            members = ", ".join(f"`{k}`" for k in cr["slots"])
            parts.append(
                f"\nDO NOT ANSWER {members} individually. Answer `{cr['key']}` — HOW MANY "
                f"you found — and the code awards that many of them. Count them the way "
                f"the guidance above says to, in one judgement over the whole response, "
                f"rather than deciding each in isolation."
            )
        for r in item.get("equals", []):
            parts.append(
                f"\nDO NOT ANSWER `{r['key']}`. The code computes it by comparing "
                f"`{r['left']}` with `{r['right']}` — the two you DO answer. It is not "
                f"in your schema, and the comparison is not a judgement you can make "
                f"more accurately than the arithmetic can."
                + (f" Where either is `{'` or `'.join(r['lenient'])}`, no mismatch is "
                   f"established and nothing is charged." if r.get("lenient") else "")
            )
        if not any(c.get("verdicts") for c in item["credit"]):
          parts.append(
              "\nVerdicts: `met`, `absent` (not there at all), `mismatch` (present but a "
              "different antecedent/consequence than 4a/4c lists), `not_described` (the "
              "element is named but nothing is said about how it changes or is affected). "
              "Quote the span you relied on in `evidence`; for an absent slot, say briefly "
              "what you looked for. Do not output a score or a deduction list — the score "
              "is computed from these verdicts.\n"
          )
        for g in item.get("cover", []):
            keys = ", ".join(f"`{k}`" for k in g["keys"])
            parts.append(
                f"{keys} take a DIFFERENT set of verdicts: {' / '.join(g['verdicts'])}. "
                f"Say WHICH of the two items in {g['of']} that slot names — "
                f"`{g['labels'][0]}` or `{g['labels'][1]}` — or `neither` if it names "
                f"something that is not on that list, or `absent` if nothing is named "
                f"there at all. Report what the student actually named; do NOT adjust it "
                f"to make the pair come out right. Order does not matter, and you are not "
                f"being asked whether the pair covers both: the grader does that "
                f"arithmetic, and two slots naming the SAME item is a finding it makes on "
                f"its own.\n"
            )
    else:
        parts.append("## Credit components")
        for c in item["credit"]:
            rule = f" {c['rule'].replace('{fail}', _fail_verdict(item, c))}" if c.get("rule") else ""
            parts.append(f"- `{c['what']}` ({c['pts']:g} pt): {c['desc']}{rule}")
        parts.append("")

        parts.append("## Deduction codes (use these exact codes; the points shown are applied for you)")
        for d in item["deductions"]:
            rep = " [repeatable]" if d.get("repeatable") else ""
            parts.append(f"- `{d['code']}` (-{d['pts']:g}){rep}: {d['text']}")
        parts.append("")

    # Suppressed when empty: an item whose guidance was all slot-specific has none
    # left here, and a bare header invites a hunt for absent instructions.
    if item["guidance"]:
        parts.append("## Grading guidance")
        for g in item["guidance"]:
            parts.append(f"- {g}")
        parts.append("")

    if item.get("exemplars"):
        parts.append(
            "## Worked examples\n"
            "Three responses from other students in this cohort, with the verdict sheet "
            "the human grader's marks imply. Match your judgements to these. They are "
            "reference material only — never grade them."
        )
        for ex in item["exemplars"]:
            parts.append(f"\n### {ex['label']}")
            parts.append(f"Their 4a: {ex['four_a']}")
            parts.append(f"Their 4c: {ex['four_c']}")
            parts.append(f"Their answer: {ex['response']}")
            verdicts = ", ".join(f"{k}={v}" for k, v in ex["slots"].items())
            parts.append(f"Verdicts: {verdicts}")
            parts.append(f"Why: {ex['note']}")
        parts.append("")

    if context:
        parts.append("## Context from this student's other answers (read-only)")
        parts.append(
            "Use these only where the rubric requires cross-item consistency. "
            "Do not grade them here."
        )
        for k, v in context.items():
            body = v.strip() or "(no response)"
            parts.append(f"\n### {k}\n{body}")
        parts.append("")

    if hint and item["id"] in ("Q1", "Q2"):
        parts.append(
            f"## Weak hint\nFormatting in the document marks '{hint}' as the "
            "underlined UTB choice. Only 6 of 20 transcriptions preserve this "
            "markup, so treat it as corroboration at most — read the UTB from "
            "the prose.\n"
        )

    if extra:
        parts.append(f"## Graph evidence for this submission\n{extra}\n")
        return "\n".join(parts)

    body = response.strip() or "(the student left this item blank)"
    parts.append(f"## Student response to grade (item {item['id']})\n{body}")
    return "\n".join(parts)


_LEADING_PTS = re.compile(r"^-\s*[\d.]+\s*pts?\s*:\s*", re.I)


def compose_feedback(item: dict, result: dict) -> str:
    """Build the grader-style feedback string from the deduction ledger.

    Matches the graders' house style: a "-N pts: reason" ledger, second person,
    canonical dictionary wording. Some dictionary entries already carry their
    own "-1 pt:" prefix, so strip it before adding ours rather than emitting
    "-1 pts: -1 pt: ...".
    """
    texts = {d["code"]: d["text"] for d in item["deductions"]}
    chunks = []
    for d in result.get("deductions", []):
        canonical = _LEADING_PTS.sub("", texts.get(d["code"], "")).strip()
        note = (d.get("note") or "").strip()
        if canonical == "did not answer":
            chunks.append("did not answer")
            continue
        line = f"-{float(d['pts']):g} pts: {canonical}"
        if note and note.lower() not in canonical.lower():
            line += f" {note}"
        chunks.append(line)

    # The graders leave the feedback cell blank on full credit. Carry an
    # advisory note into the visible feedback only when something was actually
    # deducted, or when it is a safety note — otherwise keep it in its own
    # field so it does not read as a criticism of a perfect answer.
    adv = (result.get("advisory_note") or "").strip()
    if adv and (chunks or result.get("safety_flag")):
        chunks.append(adv)
    return " ".join(chunks).strip()


def score_item(
    backend, system: str, item: dict, response: str, context: dict, hint,
    extra: str | None = None,
) -> dict:
    prompt = build_prompt(item, response, context, hint, extra)
    if item.get("graph_item"):
        raw = backend.complete(
            system, prompt, build_schema(item), allow_tools=["Read"], max_turns=8
        )
    else:
        raw = backend.complete(system, prompt, build_schema(item))

    forced_advisory = None
    if item.get("derive_from_criteria"):
        ledger, checks, unknown, forced_advisory = derive_oc_ledger(item, raw)
    elif item.get("derive_from_credit"):
        ledger, checks, unknown = derive_ledger(item, raw, response)
    else:
        valid = {d["code"]: d for d in item["deductions"]}
        ledger, unknown = [], []
        for d in raw.get("deductions", []):
            spec = valid.get(d.get("code"))
            if spec is None:
                unknown.append(d.get("code"))
                continue
            # Trust the rubric's point value, not the model's arithmetic.
            ledger.append(
                {"code": spec["code"], "pts": spec["pts"], "note": d.get("note", "")}
            )
        checks = raw.get("credit_checks", [])

    # An item cannot fail more slots than it has. Q6 in particular is eight
    # independent 1.25-point slots, and the failure mode observed in the first
    # baseline was stacking two codes on one slot (participant 9 drew five
    # deductions where the grader made two). Keep the largest deductions up to
    # the number of credit components and escalate rather than silently
    # over-deducting.
    over_specified = False
    if len(ledger) > len(item["credit"]):
        ledger = sorted(ledger, key=lambda d: -d["pts"])[: len(item["credit"])]
        over_specified = True

    total_off = sum(d["pts"] for d in ledger)
    score = max(0.0, min(item["max"], item["max"] - total_off))

    return {
        "item_id": item["id"],
        "label": item["label"],
        "max": item["max"],
        "score": round(score, 2),
        "deductions": ledger,
        "unknown_codes": unknown,
        "credit_checks": checks,
        "feedback": compose_feedback(
            item,
            {
                "deductions": ledger,
                "advisory_note": forced_advisory or raw.get("advisory_note"),
        "avoidance_frame": bool((raw.get("oc_analysis") or {}).get("avoidance_frame")),
                "safety_flag": raw.get("safety_flag"),
            },
        ),
        "advisory_note": forced_advisory or raw.get("advisory_note"),
        "avoidance_frame": bool((raw.get("oc_analysis") or {}).get("avoidance_frame")),
        "safety_flag": bool(raw.get("safety_flag")),
        "over_specified": over_specified,
        "escalate": (
            bool(raw.get("escalate")) or bool(unknown) or over_specified
            or forced_advisory is not None
        ),
        "response_chars": len(response.strip()),
    }


def score_participant(
    backend, handout: int, path: str, pid: int,
    only: list[str] | None = None, outdir: str | None = None,
    retry_missing: bool = False,
) -> dict:
    """Score one participant. `only` re-scores a subset of items and merges the
    results into that participant's existing file, so a guidance change can be
    re-measured without paying to re-run items it did not touch."""
    cfg = config(handout)
    items = cfg["rubric"].ITEMS
    outdir = outdir or cfg["outdir"]
    system = SYSTEM_TMPL.format(blurb=cfg["blurb"])

    sections = segment(
        path,
        cfg["template"],
        cfg["markers"],
        cfg["capture_tail"],
        cfg.get("join_aware", False),
    )
    repairs: list[dict] = []
    if cfg.get("repair_orphans"):
        sections, repairs = repair_orphans(sections, [i["id"] for i in items])
    repaired_items = {r["moved_to"] for r in repairs} | {r["moved_from"] for r in repairs}
    hint = utb_hint(path) if handout == 1 else None
    results: dict[str, dict] = {}

    prior_path = os.path.join(outdir, f"participant_{pid:03d}.json")
    if (only or retry_missing) and os.path.exists(prior_path):
        with open(prior_path) as fh:
            for it in json.load(fh)["items"]:
                results[it["item_id"]] = it
    if retry_missing:
        # Re-score exactly the cells a previous run failed to produce, so a
        # transient backend outage costs only the lost items.
        only = [k for k, v in results.items() if v.get("score") is None]
        if not only:
            return _assemble(handout, path, pid, results, hint, repairs)

    for item in items:
        if only and item["id"] not in only:
            continue
        ctx = {k: sections.get(k, "") for k in item["context"]}
        try:
            extra = (
                graph_bundle(path, pid, sections.get(item["id"], ""))
                if item.get("graph_item")
                else None
            )
            results[item["id"]] = score_item(
                backend, system, item, sections.get(item["id"], ""), ctx, hint, extra
            )
        except BackendError as e:
            results[item["id"]] = {
                "item_id": item["id"],
                "label": item["label"],
                "max": item["max"],
                "score": None,
                "error": str(e),
                "escalate": True,
                "response_chars": len(sections.get(item["id"], "").strip()),
            }

    # A relocated answer is a best-effort reading of a student layout error, so
    # surface it for review rather than trusting it silently.
    for iid in repaired_items:
        if iid in results and isinstance(results[iid], dict):
            results[iid]["escalate"] = True
            results[iid]["layout_repaired"] = True
    return _assemble(handout, path, pid, results, hint, repairs)


def _assemble(handout: int, path: str, pid: int, results: dict, hint, repairs=None) -> dict:
    items = config(handout)["rubric"].ITEMS
    scored = [
        results[it["id"]]["score"]
        for it in items
        if results.get(it["id"], {}).get("score") is not None
    ]
    return {
        "participant_id": pid,
        "handout": handout,
        "source_file": os.path.basename(path),
        "scored_total": round(sum(scored), 2),
        "scored_max": sum(it["max"] for it in items),
        "upload_points": None,  # not derivable from the response — see README
        "items": [results[it["id"]] for it in items if it["id"] in results],
        "utb_format_hint": hint,
        "layout_repairs": repairs or [],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--handout", type=int, default=1, choices=sorted(__import__("handouts").HANDOUTS))
    # `lo` sends THIS prompt to lo-blocks' endpoint, i.e. the model the web and
    # agreement.py use. Against `cli` it isolates the model; against agreement.py
    # it isolates the prompt. See backends.LoBlocksBackend.
    ap.add_argument("--backend", default="cli", choices=["cli", "api", "lo"])
    ap.add_argument("--participants", type=int, nargs="*", default=None)
    ap.add_argument(
        "--items",
        nargs="*",
        default=None,
        help="Re-score only these item ids, merging into existing output files.",
    )
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--retry-missing", action="store_true",
                    help="Re-score only items a previous run left unscored.")
    ap.add_argument("--max-budget-usd", type=float, default=None)
    ap.add_argument("--outdir", default=None)
    args = ap.parse_args()

    kw = {}
    if args.backend == "cli" and args.max_budget_usd:
        kw["max_budget_usd"] = args.max_budget_usd
    backend = make_backend(args.backend, **kw)

    cfg = config(args.handout)
    outdir = args.outdir or cfg["outdir"]
    os.makedirs(outdir, exist_ok=True)
    targets = find_submissions(args.handout, args.participants)
    n_items = len(args.items) if args.items else len(cfg["rubric"].ITEMS)
    scope = f" ({', '.join(args.items)} only, merging)" if args.items else ""
    print(
        f"H{args.handout}: scoring {len(targets)} participant(s) x {n_items} items{scope}",
        file=sys.stderr,
    )

    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {
            pool.submit(
                score_participant, backend, args.handout, path, pid, args.items, outdir,
                args.retry_missing
            ): pid
            for pid, path in targets
        }
        for fut in as_completed(futs):
            pid = futs[fut]
            try:
                rec = fut.result()
            except Exception as e:  # keep going; one bad file must not stop the run
                print(f"  participant {pid}: FAILED {e}", file=sys.stderr)
                continue
            # Provenance. Without it a results directory cannot say which backend
            # produced it, and baseline.py cannot tell a graph item scored WITH
            # image tools from one scored blind — which is the difference between
            # a real 88% and a 29% that is a missing tool. Recorded per file so a
            # directory assembled from more than one run is still readable.
            rec["backend"] = type(backend).__name__
            rec["supports_tools"] = bool(getattr(backend, "SUPPORTS_TOOLS", False))
            with open(os.path.join(outdir, f"participant_{pid:03d}.json"), "w") as fh:
                json.dump(rec, fh, indent=2)
            done += 1
            esc = sum(1 for i in rec["items"] if i.get("escalate"))
            print(
                f"  [{done}/{len(targets)}] participant {pid:>2}: "
                f"{rec['scored_total']:>5.2f}/{rec['scored_max']:g}"
                + (f"  ({esc} escalated)" if esc else ""),
                file=sys.stderr,
            )

    dt = time.time() - t0
    cost = getattr(backend, "total_cost_usd", None)
    print(
        f"done in {dt:.0f}s, {backend.calls} calls"
        + (f", ${cost:.2f}" if cost else ""),
        file=sys.stderr,
    )
    return 0


# --- corpus reference resolution (backdated) ---
# The paper prompt is assembled from rubric guidance, which may cite a cell by
# reference. Unresolved, the grader is asked to score the reference itself.
try:                                            # pragma: no cover
    import corpus_resolve as _corpus_resolve
    _corpus_orig_build_prompt = build_prompt

    def build_prompt(*a, _orig=_corpus_orig_build_prompt, **kw):
        return _corpus_resolve.expand(_orig(*a, **kw))
except Exception:
    pass


if __name__ == "__main__":
    raise SystemExit(main())
