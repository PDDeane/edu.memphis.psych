#!/usr/bin/env python3
"""The GENERIC criteria scorer. Goal M.

WHAT IT IS. `derive_oc_ledger` does five things, and only the fourth names a
subject: it asks the model for structured FACTS rather than judgements, computes
GATES as conjunctions of those facts, SHORT-CIRCUITS at the first definitional
failure, emits the failed gate's DEDUCTION CODE, and returns
`(ledger, checks, unknown, advisory)` -- keeping "could not tell" apart from "did
not meet". None of that is about operant conditioning. This is that shape with
the subject taken out: the facts and the gates come from the RUBRIC.

WHAT A COURSE DECLARES, in vocabulary the rubric already had before goal M:

    <Slot key="answered"  label="..."                       />   a FACT
    <Slot key="on_topic"  label="..." gate="true"
          charge="STUB_MISS" because="why this fails"       />   a fact that GATES

`rubric_component` already reads the second form into `oc_gates` -- "an oc_gate
is a SLOT THAT CHARGES, not merely one that gates" -- so nothing new is parsed.
Every slot is a boolean the model answers; a slot carrying `charge` also gates.

ORDER IS DECLARATION ORDER, and that is a real decision. `derive_oc_ledger`'s
short-circuit order is implicit in Python control flow, which M records as
load-bearing and undeclared. Here the rubric's own order is the order, so the
precedence is visible in the file a person edits rather than in the interpreter.

WHAT IT DOES NOT DO YET. The OC scorer's TYPE TAXONOMY (PR/NR/PP/NP and the moves
between them) and its counted/cadence rules are not expressible as a conjunction
of booleans, so `oc.py` still implements them. M's step 3 is migrating those onto
this interpreter item by item, with the 51,200-case fingerprint proving each step
byte-identical. This module is step 1-2: the declarations, and something that
reads them.
"""
from __future__ import annotations


def _facts(item: dict) -> list[str]:
    """The fact keys this item declares, in declaration order, de-duplicated.

    DERIVED FROM THE GATES, and that is a limit worth stating rather than hiding.
    A rubric's non-gating `<Slot>`s are served in the rubric view's `SLOT_SPEC`,
    keyed by item, NOT on the item dict a scorer receives -- so this interpreter
    can only see a fact that some gate reads. That is sound as far as it goes: a
    fact no gate consults cannot change the ledger, so asking the model for it
    would be asking a question whose answer is discarded.

    It is also why this is M step 1-2 and not all of M. The OC scorer's counted
    and typed facts (`observed_type`, `stimulus_move`, the cadence readings) are
    consulted by rules that are NOT conjunctions of booleans, and migrating those
    means giving a scorer access to `SLOT_SPEC` and declaring their vocabularies.
    `item.get("facts")` is honoured first so a rubric can declare them explicitly
    when that lands, without this function changing again.
    """
    declared = item.get("facts")
    if declared:
        return [f["key"] if isinstance(f, dict) else str(f) for f in declared]
    out = []
    for g in (item.get("oc_gates") or ()):
        if g.get("key") and g["key"] not in out:
            out.append(g["key"])
    return out


def _gates(item: dict) -> list[dict]:
    """The facts that GATE, in declaration order, as {key, code, text}."""
    return list(item.get("oc_gates") or [])


def schema_fragment(item: dict) -> dict:
    """One boolean per declared fact, all REQUIRED.

    Required, not optional, for the reason `build_schema`'s own docstring gives
    about the credit path: "did the model remember to check slot 7" stops being a
    prompt-following question and becomes a schema constraint.
    """
    props = {k: {"type": "boolean"} for k in _facts(item)}
    return {"type": "object",
            "properties": {"oc_analysis": {
                "type": "object", "properties": props,
                "required": list(props), "additionalProperties": False}},
            "required": ["oc_analysis"],
            "additionalProperties": False}


def derive_ledger(item: dict, raw: dict):
    """-> (ledger, checks, unknown, advisory). The plugin contract.

    SHORT-CIRCUITS at the first failed gate, so a rule below an unmet gate is
    never consulted -- which is why a control that already fails one gate makes
    everything under it invisible, and why the order is declared rather than
    inferred.
    """
    a = raw.get("oc_analysis") or {}
    codes = {d["code"]: d for d in (item.get("deductions") or [])}
    checks = [{"what": k, "met": bool(a.get(k, True)), "evidence": ""}
              for k in _facts(item)]
    ledger, unknown, _ = apply_declared_gates(item, a, checks, codes)
    return ledger, checks, unknown, None


def charge(code: str, codes: dict, note: str = ""):
    """Charge one declared code. -> (ledger, unknown).

    THE ONE PLACE THE RULE LIVES. Looking a code up and either charging it or
    dropping it into `unknown` was implemented twice -- here and as `add()` inside
    the OC scorer -- and it is the subtle rule, not the obvious one: an UNDECLARED
    code charges NOTHING and is reported instead, which is how the stub kept full
    marks by accident before goal E. Two copies of a rule like that agree until
    one is edited.

    Every other primitive in this module is a CONDITION plus this.
    """
    spec = codes.get(code)
    if spec is None:
        return [], [code]
    return [{"code": spec["code"], "pts": spec["pts"], "note": note}], []


def charge_suppressed(item: dict, key: str, a: dict, answer=None) -> bool:
    """Is a charge for `key` suppressed because its condition did not hold?

    THE `onlyif` PRIMITIVE, and the web has had it all along -- `slotSheet.ts`
    parses `onlyif="key:cond"` and documents itself against
    `score.py:derive_oc_ledger` BY NAME, because both sides implement one rule:
    a deduction charged for either of two causes is charged ONCE, not twice.
    The case it exists for: an example of the wrong type loses 2, a right-type
    example aimed at the wrong behaviour loses 2, and a wrong-type example aimed
    at the wrong behaviour still loses only 2 -- the second finding is already
    accounted for by the first.

    Written in Python as `if not demonstrates: ... elif not aimed: ...`, the
    ordering carried the rule and nothing declared it. This reads the same
    `<Onlyif key= cond=/>` the web's attribute is generated from, so the two
    engines stop agreeing by habit.

    ABSENT IS SATISFIED, as everywhere else: a condition the model was never
    asked cannot have suppressed anything.
    """
    look = answer or (lambda facts, k: facts.get(k, True))
    for rule in (item.get("onlyif") or ()):
        if rule.get("key") != key:
            continue
        if not look(a, rule.get("cond")):
            return True
    return False


def apply_declared_gates(item: dict, a: dict, checks: list, codes: dict,
                         stage: str = "definitional", answer=None):
    """The DECLARED-GATE loop, shared. -> (ledger, unknown, stopped).

    Extracted so the OC scorer and this one run the SAME loop rather than two
    copies that agree by habit -- which is the failure `oc.py`'s own comment
    beside it records: two declarations of the same thing where "the enforcement
    audit compares declarations, so nothing compared them".

    `a.get(key, True)` IS THE ESTABLISHED DEFAULT and is deliberate: a gate the
    model was never asked cannot have failed. This interpreter first defaulted
    absent facts to FALSE, which charges for a question nobody put -- caught by
    reading `oc.py` before delegating to it rather than after.

    `checks` is APPENDED TO, not returned fresh, because the caller's earlier
    checks precede these in the record and order is part of the output.
    """
    # THE RESOLVER IS THE COURSE'S. A rule may name a slot by the OTHER side's
    # name -- the declared rules here name the web's, while the scorer asks its
    # own -- and a course that declares both names plus which of them inverts is
    # entitled to have them resolved rather than renamed. Default is a plain
    # lookup, so a course with one vocabulary supplies nothing.
    look = answer or (lambda facts, key: facts.get(key, True))
    ledger, unknown = [], []
    seen = {c["what"] for c in checks}
    for g in (item.get("oc_gates") or []):
        # ONLY THIS STAGE. A gate declared `final` is presentational and runs
        # after the type rules; one declared `true` is definitional and runs
        # before them. An entry with no stage is definitional, so a rubric
        # written before this existed behaves exactly as it did.
        if (g.get("stage") or "definitional") != stage:
            continue
        ok = look(a, g["key"])
        if g["key"] not in seen:
            checks.append({"what": g["key"], "met": bool(ok), "evidence": ""})
        if ok:
            continue
        _l, _u = charge(g.get("code"), codes, g.get("text") or "")
        ledger.extend(_l); unknown.extend(_u)
        return ledger, unknown, True        # short-circuit: first failure decides
    return ledger, unknown, False


def apply_conjunction_gate(checks: list, over: list, code: str, codes: dict,
                           note: str = "", list_missing: bool = False):
    """A gate that fails when ANY of `over` is unmet. -> (ledger, unknown, stopped).

    THE DEFINITIONAL SHAPE, which M names as generic: "computes definitional
    GATES as conjunctions of those facts" and "SHORT-CIRCUITS at the first
    definitional failure". `derive_ledger` in the OC scorer opens with two of
    these -- the four-part `is_oc` test and the one-part `arranged` test -- and
    they differ only in which checks they read and what they say.

    `list_missing` reproduces the OC note exactly: `"Missing: "` followed by the
    UNMET check names in the order `over` gives them. That ordering is part of
    the output, not a presentation detail, so it is taken from the caller's list
    rather than from a set.

    Reads CHECK names, not fact names. The two differ in the OC scorer --
    `behavior` is the fact, `operant_behavior` the check -- and the note is
    written in check names because that is what a reader of the ledger sees.
    """
    by = {c["what"]: c["met"] for c in checks}
    missing = [k for k in over if not by.get(k, True)]
    if not missing:
        return [], [], False
    text = (note + ", ".join(missing) + ".") if list_missing else note
    _l, _u = charge(code, codes, text)
    return _l, _u, True


def apply_charge(checks: list, key: str, code: str, codes: dict, note: str = ""):
    """A check that CHARGES but does not GATE. -> (ledger, unknown).

    THE DISTINCTION IS THE POINT, and it is one M's "what is generic" list does
    not yet name. A GATE short-circuits: a rule below an unmet gate is never
    consulted, which is why a control failing one gate makes everything under it
    invisible. A CHARGE accumulates: the OC scorer's `WRONG_BEHAVIOR` and
    `LINK_NOT_ASSERTED` are both written `if not x: add(...)` with NO return, and
    their own comment says so -- "charged additively alongside TYPE_MISMATCH and
    WRONG_BEHAVIOR, and in the same order as agreement.py's score_oc_cadence".

    Reading them as gates would silently truncate every ledger that reached them,
    because the first one to fire would stop the rest. Same signature shape as
    `apply_conjunction_gate` deliberately, minus the `stopped` flag it must not
    have.
    """
    by = {c["what"]: c["met"] for c in checks}
    if by.get(key, True):
        return [], []
    return charge(code, codes, note)


def apply_fact_gate(a: dict, key: str, code: str, codes: dict, note: str = ""):
    """A gate on a FACT the model answered, not on a recorded check.
    -> (ledger, unknown, stopped).

    Distinct from `apply_conjunction_gate`, which reads `checks`. Some rules gate
    on a fact that is deliberately NOT recorded as a check -- the OC scorer's
    `cadence_ok` is one: it short-circuits before the type comparison and never
    appears in the ledger's check list. Reading it through `checks` would mean
    ADDING it there, which changes the output; this reads the answer directly and
    leaves the record alone.

    Same absent-fact rule as everywhere: `a.get(key, True)`, because a fact the
    model was never asked cannot have failed.
    """
    if a.get(key, True):
        return [], [], False
    _l, _u = charge(code, codes, note)
    return _l, _u, True


def apply_enum_mismatch(a: dict, observed_key: str, named_key: str, code: str,
                        codes: dict, note: str = "", lenient=()):
    """Charge when two DECLARED enum answers disagree. -> (ledger, unknown).

    The comparison M could not express before items carried `slot_options`: not
    "is this boolean true" but "did the model's reading match its own naming".

    LENIENT VALUES ARE FIRST-CLASS, not an edge case. The OC scorer's `"unclear"`
    naming is a declared verdict that deliberately does NOT charge -- its own
    comment says a bare `observed == named` "contradicts the very next branch: an
    `unclear` naming is deliberately not charged". A generic version that dropped
    that would quietly start charging a cell the rubric says to let pass.

    ADDITIVE, like `apply_charge`: a type mismatch does not stop the rest of the
    ledger being computed.
    """
    observed = a.get(observed_key, "none")
    named = a.get(named_key, "unclear")
    if named in lenient or observed == named:
        return [], []
    text = note.format(observed=observed, named=named) if note else ""
    return charge(code, codes, text)


def forbid_hit(a: dict, conditions) -> bool:
    """Does EVERY named condition hold? The rubric's `forbid` primitive.

    Fails only when all operands match, and passes when any one does not -- the
    semantics `_forbid_rule`'s call sites describe, and the same declaration the
    web side generates its attribute from. Generic: it is a conjunction over
    declared (key, value) pairs and reads no subject.
    """
    return all((a.get(k) or "") == v for k, v in (conditions or ()))


def passing_sheet(item: dict) -> dict:
    """A sheet on which every declared fact is true."""
    return {k: True for k in _facts(item)}


def check_names(item: dict) -> list:
    """The check names `derive_ledger` writes, obtained by RUNNING it.

    Not by listing them: a hand-kept list is what `oc_check_names` records going
    wrong before -- `stale_check` "reported all eight of handout 2's
    operant-conditioning items as stale when none were".
    """
    _, checks, _, _ = derive_ledger(item, {"oc_analysis": passing_sheet(item)})
    return [c["what"] for c in checks]

def self_test() -> int:
    """Every primitive against its DOCUMENTED contract. 0 when all pass.

    SHIPPED WITH THE MODULE, for the reason `course_schema` gives about its own:
    a check whose cases live somewhere else is one nobody has watched fail. The
    51,200-case fingerprint proves the OC scorer's particular USAGE reproduces;
    it says nothing about inputs that scorer never sends -- an undeclared code,
    an absent fact, a lenient value, a charge that must not short-circuit. Those
    are exactly the claims a SECOND course would rely on, so they are asserted
    here rather than inferred from the fingerprint.

        python3 scorer_criteria.py --self-test
    """
    ok = fail = 0

    def check(label, got, want):
        nonlocal ok, fail
        good = got == want
        ok, fail = ok + good, fail + (not good)
        print("  " + ("PASS" if good else "FAIL") + "  " + label)
        if not good:
            print("        got  " + repr(got))
            print("        want " + repr(want))

    CODES = {"X": {"code": "X", "pts": 2.0}}
    # charge -- the one rule, five callers
    check("charge: declared code -> ledger",
          charge("X", CODES, "why"), ([{"code": "X", "pts": 2.0, "note": "why"}], []))
    check("charge: UNDECLARED code -> unknown, charges nothing",
          charge("NOPE", CODES, "why"), ([], ["NOPE"]))

    # apply_declared_gates -- short-circuit, absent=pass, checks appended once
    item = {"oc_gates": [{"key": "a", "code": "X", "text": "ta"},
                         {"key": "b", "code": "X", "text": "tb"}]}
    ch = []
    check("gates: first failure decides, second not consulted",
          apply_declared_gates(item, {"a": False, "b": False}, ch, CODES),
          ([{"code": "X", "pts": 2.0, "note": "ta"}], [], True))
    check("gates: only the reached gate is recorded", [c["what"] for c in ch], ["a"])
    ch = []
    check("gates: ABSENT fact cannot fail",
          apply_declared_gates(item, {}, ch, CODES), ([], [], False))
    check("gates: a pre-existing check is not duplicated",
          (lambda c: (apply_declared_gates(item, {"a": True, "b": True}, c, CODES),
                      [x["what"] for x in c])[1])([{"what": "a", "met": True}]),
          ["a", "b"])

    # apply_conjunction_gate -- AND, missing listed in `over` order
    checks = [{"what": "p", "met": True}, {"what": "q", "met": False},
              {"what": "r", "met": False}]
    check("conjunction: lists MISSING in the caller's order",
          apply_conjunction_gate(checks, ["p", "q", "r"], "X", CODES,
                                   note="Missing: ", list_missing=True),
          ([{"code": "X", "pts": 2.0, "note": "Missing: q, r."}], [], True))
    check("conjunction: all met -> no charge, no stop",
          apply_conjunction_gate([{"what": "p", "met": True}], ["p"], "X", CODES),
          ([], [], False))

    # apply_charge -- ADDITIVE: never reports a stop
    check("charge-check: unmet charges",
          apply_charge([{"what": "p", "met": False}], "p", "X", CODES, "n"),
          ([{"code": "X", "pts": 2.0, "note": "n"}], []))
    check("charge-check: met is silent",
          apply_charge([{"what": "p", "met": True}], "p", "X", CODES), ([], []))
    check("charge-check: absent cannot fail",
          apply_charge([], "p", "X", CODES), ([], []))

    # apply_fact_gate -- gates on a fact, does not touch checks
    check("fact gate: false fact charges and STOPS",
          apply_fact_gate({"f": False}, "f", "X", CODES, "n"),
          ([{"code": "X", "pts": 2.0, "note": "n"}], [], True))
    check("fact gate: absent fact cannot fail",
          apply_fact_gate({}, "f", "X", CODES), ([], [], False))

    # apply_enum_mismatch -- lenient values are first-class
    check("enum: mismatch charges, note formatted",
          apply_enum_mismatch({"o": "PR", "n": "NR"}, "o", "n", "X", CODES,
                                note="is {observed}, chose {named}."),
          ([{"code": "X", "pts": 2.0, "note": "is PR, chose NR."}], []))
    check("enum: LENIENT value does not charge",
          apply_enum_mismatch({"o": "PR", "n": "unclear"}, "o", "n", "X", CODES,
                                lenient=("unclear",)), ([], []))
    check("enum: agreement does not charge",
          apply_enum_mismatch({"o": "PR", "n": "PR"}, "o", "n", "X", CODES), ([], []))

    # forbid_hit -- fails only when EVERY condition holds
    check("forbid: all conditions hold -> hit",
          forbid_hit({"k": "v", "j": "w"}, [("k", "v"), ("j", "w")]), True)
    check("forbid: any condition differs -> no hit",
          forbid_hit({"k": "v", "j": "x"}, [("k", "v"), ("j", "w")]), False)
    check("forbid: no conditions -> vacuously true",
          forbid_hit({}, []), True)

    print("\n  " + str(ok) + " passed, " + str(fail) + " failed")
    return 1 if fail else 0


if __name__ == "__main__":
    import sys as _sys
    raise SystemExit(self_test() if "--self-test" in _sys.argv else 0)
