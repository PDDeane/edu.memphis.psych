#!/usr/bin/env python3
"""Compare what the CLI and the web ENFORCE, by exercising both.

The gap this closes. `equivalence.py` has two modes and neither can see an
enforcement rule: `--prompts` compares prompt elements verbatim, `--scoring`
compares item totals and reachable costs. Q6's distinctness rule sat between
them — the web refused to credit two boxes naming the same 4a item, the CLI
credited both, and nothing failed. It was found by hand. This is the mode that
would have found it.

Method: probe, do not mirror. Where a rule is data on both sides (`cover`) it is
compared directly. Where one side keeps it in Python — `derive_oc_ledger`
computes its type comparison and uses `elif` for charge-once — the rule is
inferred from BEHAVIOUR: flip one input at a time, then in pairs, and read the
rules off the losses. A hand-maintained table of "what the code does" would rot
exactly the way index-keyed guidance omissions did.

Two facts are read per item, per side:

  gates        an input whose failure alone costs the whole item
  charge-once  two inputs that together cost less than they do apart
  computed     a check the model is not asked for, because code derives it

Run via `equivalence.py --enforcement`, which drives the web half through
probe.test.ts and diffs the two.
"""
from __future__ import annotations

import functools
import pathlib
import inspect
import re
import sys
import jsoncache
import sourcecache

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from forms import config
# `paths` FIRST: it puts this course's `scoring/<course>/` and the general
# `scorers/` on `sys.path`, and the imports just below are modules that live
# there. Importing them before `paths` raises ModuleNotFoundError -- measured
# on 13 modules the day those directories were split out.
import paths  # noqa: F401  (import order is load-bearing; see above)
from score import _computed_keys, build_schema, derive_ledger


def _oc_scorer():
    """This course's CRITERIA scorer, through the registry. Goal E step 4.

    Was `from score import derive_oc_ledger` -- an import of a name the engine
    no longer owns. The scorer is course-supplied now, so it is RESOLVED, and a
    course that ships none gets None here rather than an ImportError at the top
    of the audit. The checks below turn that None into their own refusal, which
    is the designed message ("is gone -- retarget this check") rather than a
    traceback that the gate would have to interpret.
    """
    import scorers
    return scorers.optional("oc")
import paths as _p7   # J-7b: this course's handout file names


def _gold_declaration(name: str):
    """One gold declaration, read from the gold file.

    The gold twin of the `_declaration` helper, and separate from it because the
    two files differ in AVAILABILITY: the course file ships inside this public
    repository and is always present, gold does not (C1b). So this module now
    fails to import when the gold file is UNREACHABLE, where before the data was
    inline and it did not. See `coursedata.gold_declaration` for what that does
    and does not mean.

    The reasoning that used to sit INSIDE these tables as comments went with
    them -- `coursedata.gold_notes(table, key)` returns it, per entry, verbatim.
    It is course-specific gold reasoning and a public repository was the wrong
    home for it; it is not gone, and it is not optional reading.
    """
    import coursedata

    return coursedata.gold_declaration(name)


# ---------------------------------------------------------------------------
# The criteria sheet's inputs, and what makes each one fail.
#
# This is the one place the audit names the CLI's internals, and it is guarded:
# `check_criteria_table_is_complete` asserts it covers EXACTLY the schema's
# required properties, so adding an oc_analysis field without deciding how it
# fails breaks the audit instead of being silently unprobed.
# THE PROBE FIXTURES AND THE SIDE MAP ARE THE COURSE'S. Goal P, 2026-09-24.
#
# These four tables named ten of this course's facts -- `avoidance_frame`,
# `cadence_ok`, `targets_own_behavior` and seven more -- in ENGINE code. A second
# course met an engine that already knew this course's psychology: the
# `bmod_handout1` defect one level in, naming not a file but a question the model
# is asked. They now live in the course file, and the reasoning for every value
# travels with them in `course_metadata_source.py`.
#
# Read ONCE at import, as before, so nothing downstream changes shape.
def _course_vocab(name: str):
    """A course-declared vocabulary table, with its TUPLE VALUES restored.

    JSON HAS NO TUPLE, and that is not cosmetic here. `ALIAS` maps a name to
    EITHER one alternative (a string) or several (a tuple), and `web_name` does
    `if cand in web_keys` over them -- a list is unhashable, so the audit died
    with `TypeError: unhashable type: 'list'` the first time it ran after these
    tables moved to the course file. `segment._markers` records the same rule for
    the same reason: "Tuples, not the lists JSON gives back ... a reader should
    not change a published shape while moving where it is stored."

    The equality check that was supposed to catch this could not: comparing
    through `json.dumps(..., default=str)` serialises a tuple and a list
    identically, so it reported the tables IDENTICAL while the types had changed.
    """
    import coursedata

    raw = coursedata.declaration(name)
    if isinstance(raw, dict):
        return {k: (tuple(v) if isinstance(v, list) else v) for k, v in raw.items()}
    return raw


_PASS = _course_vocab("PROBE_PASS")
_FAIL = _course_vocab("PROBE_FAIL")
# The two type fields are handled separately: their failing value depends on the
# other one, and a naive flip can make them agree again.
_TYPE_FIELDS = tuple(_course_vocab("PROBE_TYPE_FIELDS"))

# The same rule wears different names on the two sides. Kept explicit and small;
# an unmapped key is REPORTED, never assumed equivalent.
# The same rule under its two names. An unmapped key is REPORTED, never assumed
# equivalent -- that rule stays HERE because it is about how to treat a gap, not
# about which names exist.
ALIAS = _course_vocab("SIDE_ALIAS")


# `_tbl`, `_oc_baseline` and `_oc_fail` MOVED TO THE COURSE SCORER. Goal P.
# They built this course's hypothetical answers -- naming `observed_type`,
# `named_type` and the PR/NR/PP/NP taxonomy -- so the audit could only construct
# a probe for a subject it already knew. They are `probe_baseline`, `probe_fail`
# and `_probe_value` in the course's own `scorers/oc.py` now, beside the tables
# they read, and are reached the same way the scorer is: through the registry.


def _oc_probe():
    """This course's probe builders, or None when it ships no criteria scorer."""
    return _oc_scorer()


def web_name(cli_key: str, web_keys: set[str]) -> str | None:
    """The web check corresponding to a CLI input, or None if unmatched."""
    # An explicit alias wins over the identity match. The two used to be the
    # other way round, which was fine while a CLI key never named a web slot of
    # a different kind. It does now, and identity-first quietly resolved a
    # deduction to a check that does not charge.
    a = ALIAS.get(cli_key)
    if a is not None:
        # An alias entry is AUTHORITATIVE: falling through to identity when none
        # of its candidates is present would quietly re-admit the same-name match
        # the alias exists to override, and could hide a removal the selftest is
        # supposed to catch. A key that legitimately matches itself says so by
        # listing itself as a candidate, the way `observed_type` does.
        for cand in (a if isinstance(a, tuple) else (a,)):
            if cand in web_keys:
                return cand
        return None
    if cli_key in web_keys:
        return cli_key
    return None


def _forms() -> tuple:
    """Which forms this course has -- never a count written out here.

    `(1, 2, 3)` appeared at 39 sites in this file alone: THIS COURSE'S SHAPE,
    spelled inside the audit. `course.json` declares it, and
    `forms.declared()` reads that declaration and REFUSES rather than
    returning an empty tuple -- a loop handed `()` runs zero times, finds
    nothing and reports clean, which is the failure this whole file exists to
    prevent.

    A function rather than a module constant because the import is local: this
    module has no module-level `handouts` import and 28 function-local ones, so
    a constant would have to pick a moment to resolve and every site would then
    depend on import order.
    """
    import forms as _H

    return _H.declared()


def check_criteria_table_is_complete(items: list[dict]) -> list[str]:
    """Every oc_analysis property must have a pass and a fail value.

    "Path-specific" is COMPUTED rather than listed. The criteria items come in
    two shapes — the four example screens and the four daily/weekly ones — and a
    field required by one shape and not the other is not stale, it is just on the
    other path. That used to be a hardcoded tuple of four names, which meant a
    fifth such field (`consequence_asserted`, required by all four DAY/WK items
    and none of the examples) was reported as stale on four items forever. The
    list could only ever be as current as the last person to notice.

    What is still a finding: a probe-table key required by NO item, which really
    is dead, and a schema property the probe table has no values for, which is a
    field nobody decided how to fail.
    """
    problems = []
    known = set(_PASS) | set(_TYPE_FIELDS)
    derive = [it for it in items if it.get("derive_from_criteria")]
    required_somewhere: set[str] = set()
    for it in derive:
        required_somewhere |= set(build_schema(it)["properties"]["oc_analysis"]["required"])

    for it in derive:
        req = set(build_schema(it)["properties"]["oc_analysis"]["required"])
        for extra in sorted(req - known):
            problems.append(f"{it['id']}: oc_analysis has `{extra}`, not in the probe table")
        for stale in sorted(known - req):
            if stale in required_somewhere:
                continue          # on the other path, not dead
            problems.append(f"{it['id']}: probe table has `{stale}`, required by no item")
    return problems


@functools.lru_cache(maxsize=1)
def _sheet_slots() -> dict:
    """item id -> its SLOT_SPEC entry, across all three rubrics.

    SLOT_SPEC has been the PRIMARY definition of the slot sheet since 2026-09-08;
    before that the sheet was a hand-authored `slots=` attribute and there was no
    table to consult, which is why the checks below reached for the credit list.

    A plain function on purpose. This was first written as a dict subclass filling
    itself from `__missing__`, which never ran: `__missing__` fires for `d[key]`
    and NOT for `d.get(key, default)`, so every lookup returned the default and
    the check went on reporting all ten names as unknown. Nothing distinguished
    that from a real finding.
    """
    rubric_h1, rubric_h2, rubric_h3 = _rubric_views()
    out = {}
    for mod in (rubric_h1, rubric_h2, rubric_h3):
        for iid, spec in (getattr(mod, "SLOT_SPEC", {}) or {}).items():
            out.setdefault(iid, spec)
    return out


def check_slot_codes_exist(items: list[dict]) -> list[str]:
    """Every code a slot maps a verdict to must be in that item's deduction list.

    Nothing checked this. `derive_ledger` puts whatever the map says straight into
    the ledger, so a typo'd code name would be emitted, carry a slot's points, and
    reach the student's feedback with no wording behind it — a misspelling
    presenting as a rubric finding. It also checks `blank_code`, which the collapse
    now depends on entirely.
    """
    # A name used somewhere must be declared somewhere; the names are the
    # course's.
    #
    # PYTHON KEEPS THE FETCH, and passes the items it was HANDED rather than
    # letting the runner re-read the rubric. The self-test injects by mutating
    # the in-memory view and forking -- its case "a slot points at a code that
    # does not exist" writes `NO_VERDIKT` into a credit map that exists only in
    # memory -- so a payload assembled from disk would be blind to it. Two
    # earlier ports were converted that way and both went silent; see
    # `check_codes_reachable`. The sheet comes from `_sheet_slots()` for the
    # same reason, and `onlyif` is keyed on the SHEET, not the credit list.
    import lo_enforce

    sheet = _sheet_slots()
    return lo_enforce.run("slot_codes_exist", {"items": [
        {"id": it["id"],
         "deductions": [d["code"] for d in it["deductions"]],
         "credit": [{"what": c["what"], "codes": c.get("codes") or {}}
                    for c in it.get("credit") or []],
         "blankCode": it.get("blank_code"),
         "counts": [{"key": cr["key"], "slots": list(cr["slots"])}
                    for cr in it.get("counts") or []],
         "onlyif": [{"key": r["key"], "cond": r["cond"]}
                    for r in it.get("onlyif") or []],
         "sheet": [s["key"] for s in sheet.get(it["id"], ())]}
        for it in items]})


def check_codes_reachable(items: list[dict]) -> list[str]:
    """Every deduction code must be producible, or declared unreachable.

    The conversion silently retired live codes. Q4a's slots were given only
    met/absent/unclear, so "present but not an antecedent" — A_NOT_ANTECEDENT,
    emitted 6 times before — became `absent` under A_ONLY_ONE. Same points, so no
    accuracy number moved; the student was simply told the wrong thing, and Q6 then
    lost its 4a context because `scorer_evidence` empties a box on `absent`.

    A code with no path to it is either a bug or a decision. This makes it say
    which.
    """
    # PORTED (goal K, step 8); the judgement is `enforce/codesReachable.ts` and
    # is generic -- "a penalty no verdict can emit is either a bug or a decision,
    # and the rubric must say which".
    #
    # PYTHON KEEPS THE FETCH, AND IT MUST. This passed `None` and let the runner
    # assemble from the rubric FILE, which was measured identical and was still
    # wrong: the self-test injects by MUTATING THE IN-MEMORY rubric view and
    # forking, so a payload re-read from disk cannot see the injection. Measured
    # 2026-09-26 -- the case "a verdict is dropped, retiring its code" went from
    # detected to SILENT, and the audit reported clean either way. The assembler
    # stays for callers inside lo-blocks, which have no python to ask; it is
    # reached only when the payload is null, and python never sends null now.
    import lo_enforce

    return lo_enforce.run("codes_reachable", {"items": [
        {"id": it["id"],
         "deriveFromCredit": bool(it.get("derive_from_credit")),
         "blankCode": it.get("blank_code"),
         "unreachableCodes": list(it.get("unreachable_codes") or []),
         "credit": [{"codes": c.get("codes") or {}} for c in it.get("credit") or []],
         "deductions": [{"code": d["code"], "pts": d["pts"]}
                        for d in it.get("deductions") or []]}
        for it in items]})


# Repeated families that are countable in shape but must NOT be converted, with
# the reason, because an unexplained exemption is how the inconsistency below got
# in. Keyed by (item, family stem).
# COUNTABLE_EXEMPT IS BOUND FURTHER DOWN, immediately after `_declaration` is
# defined -- a reader call cannot precede its reader. Its entries and their
# reasons live in the course file, authored in `declaration_source.py`.


def check_countable_families_converted(items: list[dict]) -> list[str]:
    """Do items with the SAME repeated-slot shape use the same primitive?

    `primitives.json` says what each primitive is; nothing said which items should
    use one. So `counts` landed on Q1 and not on Q2 — the same item with a
    different noun, same three interchangeable `reason_N@1` slots, same
    REASON_MISSING — and no audit noticed for as long as it took someone to ask.

    Countable means the family's members share ONE code: they are instances, so a
    number expresses everything a per-slot verdict would. Two codes means they do
    not — Q4a's `A_ONLY_ONE` and `A_NOT_ANTECEDENT` are different findings with
    different feedback, and a count cannot tell "gave one" from "gave two, one of
    them not an antecedent". Both directions are checked: an unconverted countable
    family, and a `counts` rule over members that carry more than one code — the
    second being the shape that silently retired live codes once already.
    """
    # PORTED (goal K, step 8). "Interchangeable slots sharing one code are a
    # COUNT, and a count cannot say which of several codes applies" is a
    # statement about rubric authoring, so the judgement is generic; the items,
    # codes and exemptions are data.
    #
    # PYTHON KEEPS THE FETCH, for the reason recorded on `check_codes_reachable`:
    # self-assembly reads the rubric and `COUNTABLE_EXEMPT` from disk, and this
    # check's self-test case mutates the IN-MEMORY table. Measured 2026-09-26 --
    # "a stale exemption outlives its conversion" was silent.
    import lo_enforce

    return lo_enforce.run("countable_families_converted", {
        "items": [
            {"id": it["id"],
             "deriveFromCredit": bool(it.get("derive_from_credit")),
             "counted": sorted({k for cr in it.get("counts") or []
                                for k in cr["slots"]}),
             "credit": [{"what": c["what"], "codes": c.get("codes") or {}}
                        for c in it.get("credit") or []]}
            for it in items],
        "exempt": [list(k) for k in COUNTABLE_EXEMPT],
    })


def check_scorer_behaviour_is_unchanged() -> list[str]:
    """Sweep the criteria scorer's whole input space against its recorded digest.

    TRACKED IS NOT PROTECTED. This lived in a scratchpad for the whole of goals E
    and M -- fourteen rules moved between modules with the ledger held identical
    at every step -- which meant the only thing standing between a refactor and a
    silent scoring change was a file that would not survive the session. The
    definition inventory would report it VANISHING; nothing at all would report
    it FAILING.

    1.9 seconds for 51,200 cases, because the ledger is a pure function of
    `(item, raw)` and needs no model call. That is cheap enough to run every time
    rather than when someone remembers to.

    Its comparison goes through `evidence.certify` with a live control, so
    "identical" can only be reported by a test that was capable of saying
    otherwise -- the property whose absence produced three wrong answers on
    2026-09-24.
    """
    try:
        from tools import scorer_fingerprint      # the package form, like editguard
    except Exception as exc:                      # pragma: no cover
        return [f"the scorer fingerprint cannot be imported: {exc}"]
    return scorer_fingerprint.check()


def check_criteria_primitives_hold_their_contracts() -> list[str]:
    """Run `scorer_criteria`'s own contract cases. M-3b.

    THE SELF-TEST WAS TRACKED BUT NOT RUN, which is only half of protected: the
    definition inventory would report it VANISHING, and nothing at all would
    report it FAILING. A check nobody runs rots silently, and this one guards the
    claims a SECOND COURSE relies on -- an undeclared code charging nothing, an
    absent fact that cannot fail, a lenient verdict that must not charge, a
    charge that must not short-circuit. The 51,200-case fingerprint proves none
    of those, because the OC scorer never sends them.

    Output is captured: a check reports findings, it does not print.
    """
    import contextlib
    import io

    try:
        import scorer_criteria
    except Exception as exc:                      # pragma: no cover
        return [f"the criteria interpreter cannot be imported: {exc}"]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = scorer_criteria.self_test()
    if not rc:
        return []
    return [f"scorer_criteria contract case failed -- {l.strip()}"
            for l in buf.getvalue().splitlines() if l.strip().startswith("FAIL")]


def check_primitive_conformance() -> list[str]:
    """Does the PROMPT honour every schema-excluding primitive on every live sheet?

    Checked empirically, not by trusting the registry. For each primitive whose keys
    leave the response schema, the generated body must (a) not list those keys in the
    checklist the model fills, and (b) carry a line telling it not to answer them.

    This is the check that was missing twice. `derived` shipped, and later `counts`,
    with their keys still in the web checklist while the schema refused them — the
    model asked for answers it could not return, alongside the thing that replaced
    them. Neither showed up in any score, because the grader ignored the surplus.
    """
    # PORTED to `enforce/primitiveConformance.ts` (goal K).
    #
    # IT NEEDED THE REAL RUNTIME PROMPT, and that is why it moved only now.
    # `promptAssembler.webPrompts` reproduces `build_web_prompt` byte for byte
    # on all 23 -- the engine has been the designed producer since item C, and
    # this check was classified as blocked on a generator python had and the
    # engine did not, which was never true.
    #
    # PYTHON STILL PASSES WHAT IT READS, so this path asks about the prompts
    # THIS process builds; the self-test substitutes `build_web_prompt`, and a
    # payload the runner assembled from the staged inputs would not see it.
    from olx_prompts import (ACTION, FORM, SHEET_ONLY, sheet_id, _sheet_tag,
                             build_web_prompt, primitive_attrs, primitives)

    import lo_enforce

    tags = {}
    for item in sorted({**ACTION, **SHEET_ONLY}):
        try:
            tags[item] = _sheet_tag(FORM[item], sheet_id(item))
        except BaseException:
            continue
    return lo_enforce.run("primitive_conformance", {
        "excluding": sorted(primitive_attrs(excluding_keys=True)),
        "excludes": {p["attr"]: p.get("excludes")
                     for p in primitives()["primitives"]},
        "tags": tags,
        "inAction": sorted(ACTION),
        "prompts": {i: build_web_prompt(i) for i in sorted(ACTION)},
    })

def check_harness_schema_conformance() -> list[str]:
    """Does the SCHEMA the measurement harness sends honour the same exclusions?

    The prompt check above passes on a prompt that is generated correctly. It says
    nothing about the JSON schema agreement.py pairs with that prompt, and for a
    long time the two disagreed: the body said "DO NOT ANSWER `matches_chosen_type`"
    while the schema made it required, across 27 keys and 14 items. A model resolves
    that in the schema's favour, so the instruction was simply overridden.

    Probed, not read: this builds the real schema from the real sheet and looks in
    it, because the last three versions of "agreement.py mirrors the web" were all
    wrong while claiming otherwise in a docstring.
    """
    import agreement as AG
    from olx_prompts import ACTION, FORM, SHEET_ONLY, sheet_id

    problems = []
    for item in sorted({**ACTION, **SHEET_ONLY}):
        if item not in ACTION:
            continue          # a DerivedChecks sheet: no model call, so no schema
        try:
            action = AG.load_action(_p7.handout_olx(FORM[item]), sheet_id(item))
        except SystemExit as e:
            problems.append(f"{item}: the harness cannot read its own sheet — {e}")
            continue
        schema = AG.build_schema(action["slots"], action["excluded"])
        asked = set(schema["properties"]["checks"]["properties"])
        for k in sorted(action["excluded"] & asked):
            problems.append(f"{item}: `{k}` is excluded from the web's schema but the "
                            f"harness still requires it, so the model answers what the "
                            f"prompt forbids")
        for slot in action["slots"]:
            for opt in slot["options"]:
                if "@" in opt:
                    problems.append(f"{item}: `{slot['key']}` offers `{opt}` as a legal "
                                    f"verdict — the @pts suffix was not stripped")
    return problems


def check_derived_fields_resolve() -> list[str]:
    """Does every `derived` rule name a field the harness can actually read?

    A `derived` check reads a FIELD id; the harness's texts are keyed by SECTION,
    and the two are joined through the item's refs map. Look the field up directly
    and every lookup misses — and the miss is silent, because an unresolvable field
    is indistinguishable from an empty one. Both mean "no text", both score the
    check unmet, and the run still prints a table.

    That cost `utb_stated` on all 17 of Q1's cells: 2 points each, an item that
    measures 76% reporting 6%. Nothing failed, nothing was skipped, and the number
    was simply wrong. The harness now raises on an unresolvable field; this makes
    the same mistake fail the audit before a sweep is spent on it.
    """
    # PORTED (goal K). `derived=` is an attribute of the action's OPENING TAG,
    # not its body -- reading the body found nothing at all, and an assembler
    # returning zero rules agrees with python's clean answer for entirely the
    # wrong reason. Fire-tested by adding an unresolvable field to a real rule
    # on both sides: byte-identical, same item, same key.
    import lo_enforce

    return lo_enforce.run("derived_fields_resolve", None)

def check_ref_targets_resolve() -> list[str]:
    """Does every <Ref> in a measured prompt point at a field the harness can fill?

    `build_prompt` substitutes an unmapped target with "(not collected on the paper
    version)" — a sentence that reads like a deliberate statement about the corpus
    and is in fact a lookup that missed. The model then reports, accurately, that
    the box is empty; the item scores 0; the run prints a full table with no
    failures. Q6 measured 6% that way, on all 17 cells, because its sheet was
    rewritten into eight boxes (`q6_state_a1`, `q6_change_a1`, ...) and the _CTX
    map still named the two it used to have.

    Third instance today of one shape: a lookup that misses and returns something
    innocuous. The other two — a derived field read against the wrong key space,
    and a prose mention of <LLMAction> swallowing a real element — cost an item's
    entire score and an item's measurability respectively, and neither raised.
    """
    # PORTED (goal K). The assembler reads the FROZEN RESPONSE RECORD per item
    # rather than the 8-item fixture summary -- reading the summary saw 8 items
    # of 23 and reported zero refs, an empty payload wearing a clean answer's
    # clothes. Fire-tested with an unresolvable target on both sides:
    # byte-identical.
    import lo_enforce

    return lo_enforce.run("ref_targets_resolve", None)

def all_items() -> list[dict]:
    return [it for h in _forms() for it in config(h)["rubric"].ITEMS]


# ---------------------------------------------------------------------------




def _score(item: dict, raw: dict) -> float:
    # Deliberately passes a NON-blank response. This audit probes what a sheet
    # scores, and every probe is a hypothetical answer that exists — a blank one
    # would collapse to the item's blank_code and score the same 0 for a reason
    # the probe is not testing. Leaving the argument out would default to "" and
    # do exactly that.
    _oc = _oc_scorer()
    if item.get("derive_from_criteria") and _oc is not None:
        ledger, *_ = _oc.derive_ledger(item, raw)
    else:
        ledger, *_ = derive_ledger(item, raw, response="(probe answer)")
    off = sum(d["pts"] for d in ledger)
    return round(max(0.0, min(item["max"], item["max"] - off)), 4)


def _credit_baseline(item: dict) -> dict:
    """A slot sheet that earns full marks, honouring any cover group.

    A grouped slot's verdict IS its identity, so labels are handed out one per
    slot PER GROUP — reusing one would leave a duplicate, and the all-satisfied
    baseline would silently stop being full marks.
    """
    claimed: dict[int, list[str]] = {}
    slots = {}
    for c in item["credit"]:
        k = c["what"]
        lab = None
        for gi, g in enumerate(item.get("cover", [])):
            if k in g["keys"]:
                taken = claimed.setdefault(gi, [])
                free = [l for l in g["labels"] if l not in taken]
                lab = free[0] if free else g["labels"][0]
                taken.append(lab)
        # The slot's OWN first verdict is the passing one. Defaulting to "met"
        # made a counted slot read `met`, which parses as a count of zero — every
        # member came back absent and the all-pass baseline was not full marks.
        vocab = c.get("verdicts")
        slots[k] = {"verdict": lab or (vocab[0] if vocab else "met"), "evidence": "e"}
    return {"slots": slots}


def _credit_fail(item: dict, base: dict, key: str, avoid: str = "") -> dict:
    """`base` with `key` failing, in that slot's OWN vocabulary.

    A slot whose verdicts are the four OC types has no "absent": forcing that
    string made two flipped operands both read `absent`, so a computed comparison
    between them came back EQUAL and the rule it expresses looked absent from the
    CLI. `avoid` keeps a second flip off the value the first one took.
    """
    raw = {"slots": {k: dict(v) for k, v in base["slots"].items()}}
    comp = next(c for c in item["credit"] if c["what"] == key)
    vocab = comp.get("verdicts")
    # A slot in a cover group must fail to a value OUTSIDE the group's labels.
    # The labels are all valid answers, so swapping `first` for `second` does not
    # fail the check — it re-answers it, and on a two-member group that makes the
    # SIBLING a duplicate and knocks it out too. The web's probe already picks a
    # non-label value, so the two harnesses disagreed about what "failed" meant
    # and every pair containing a cover member came back sublinear on one side.
    labels = {l for g in item.get("cover", []) if key in g["keys"] for l in g["labels"]}
    # A LENIENT verdict on a `requires` condition is not a failure either, and for
    # the same reason the labels are excluded: it establishes nothing and so
    # denies nothing. Q6's link_c2 is the case. Failing it alone picked `absent`
    # and cost 2.5 -- both dependents demoted -- but in a PAIR, `avoid` pushed the
    # choice to `unclear`, which costs nothing, so every pair containing link_c2
    # came back sublinear and the audit reported six charge-once divergences
    # against a rule that has none. The probe has to fail the slot, not re-answer
    # it in a way the primitive is written to forgive.
    labels |= {v for r in item.get("requires", []) or ()
               if r.get("cond") == key for v in (r.get("lenient") or ())}
    if vocab:
        now = raw["slots"][key]["verdict"]
        cands = [v for v in vocab if v not in labels] or list(vocab)
        alt = ([v for v in cands if v != now and v != avoid]
               or [v for v in cands if v != now]
               or [v for v in vocab if v != now])
        raw["slots"][key]["verdict"] = alt[0]
    else:
        raw["slots"][key]["verdict"] = "absent"
    return raw


def signature(item: dict) -> dict:
    """What this item enforces, read off its behaviour."""
    criteria = bool(item.get("derive_from_criteria"))
    if criteria:
        _p = _oc_probe()
        if _p is None:
            return {"inputs": [], "note": "this course ships no criteria scorer"}
        base = _p.probe_baseline(item)
        inputs = sorted(build_schema(item)["properties"]["oc_analysis"]["required"])
        mk_base = lambda: {"oc_analysis": base}
        mk_one = lambda k: {"oc_analysis": _p.probe_fail(item, base, k)}

        def mk_two(a, b):
            x = _p.probe_fail(item, base, a, other=b)
            return {"oc_analysis": _p.probe_fail(item, x, b, other=a)}
    else:
        base = _credit_baseline(item)
        # A computed slot is NOT a model input — it is excluded from the schema, so
        # counting it as one made the audit report the CLI as still asking for it.
        #
        # Sourced from `score._computed_keys`, which reads primitives.json, rather
        # than the hand-written `equals` + `counts` pair this used to be. That pair
        # was the same mirror-of-the-registry-kept-by-memory that score.py's own
        # docstring records having had to fix, and it had already fallen behind by
        # four primitives: the first `derived` check authored on the CLI path was
        # reported as ASKED ON CLI ONLY while the schema had correctly dropped it.
        # The audit was wrong about the code, which is the worst way for it to be
        # wrong.
        computed = set(_computed_keys(item))
        inputs = [c["what"] for c in item["credit"] if c["what"] not in computed]
        mk_base = lambda: base
        mk_one = lambda k: _credit_fail(item, base, k)

        def mk_two(a, b):
            first = _credit_fail(item, base, a)
            took = first["slots"][a]["verdict"]
            return _credit_fail(item, first, b, avoid=took)

    mx = item["max"]
    full = _score(item, mk_base())
    single = {k: round(mx - _score(item, mk_one(k)), 4) for k in inputs}

    gates = sorted(k for k, v in single.items() if v >= mx)
    ignored = sorted(k for k, v in single.items() if v == 0)
    plain = [k for k in inputs if k not in gates and k not in ignored]

    charge_once = []
    for i, a in enumerate(plain):
        for b in plain[i + 1:]:
            both = round(mx - _score(item, mk_two(a, b)), 4)
            if both + 1e-9 < single[a] + single[b] and both < mx:
                charge_once.append(tuple(sorted((a, b))))

    return {
        "item": item["id"],
        "max": mx,
        "baseline_is_full": abs(full - mx) < 1e-9,
        "inputs": inputs,
        "gates": gates,
        "ignored": ignored,
        "charge_once": sorted(charge_once),
        "single_loss": single,
        "cover": [{"keys": g["keys"], "labels": g["labels"]} for g in item.get("cover", [])],
        # The verdict vocabulary a grouped slot accepts. Both sides declare one
        # now, so a drift in it is comparable rather than invisible.
        "cover_vocab": {k: g["verdicts"]
                        for g in item.get("cover", []) for k in g["keys"]},
        # Declared as DATA on the credit path, the way the web declares it. The
        # criteria path still keeps its comparison in `derive_oc_ledger`, so there
        # it stays something to infer from behaviour rather than to read off.
        # What the CLI derives rather than asks — the mirror of the web's `computed`,
        # without which "the CLI computes it and the web asks" was invisible.
        "derived_keys": sorted({r["key"] for r in item.get("equals", [])}
                               | {k for cr in item.get("counts", []) for k in cr["slots"]}),
        "equals": [{"key": r["key"], "operands": [r["left"], r["right"]],
                    "lenient": r.get("lenient") or []}
                   for r in item.get("equals", [])],
    }


def cli_signatures() -> dict[str, dict]:
    """Every item whose score the CLI derives from checks."""
    out = {}
    for h in _forms():
        for it in config(h)["rubric"].ITEMS:
            if it.get("derive_from_criteria") or it.get("derive_from_credit"):
                out[it["id"]] = signature(it)
    return out


def all_derive_items() -> list[dict]:
    return [it for h in _forms() for it in config(h)["rubric"].ITEMS
            if it.get("derive_from_criteria") or it.get("derive_from_credit")]


def _harness_source(fname: str) -> str:
    """The text of one sweep harness, wherever it lives.

    BY IMPORT, NOT BY A SIBLING'S DIRECTORY. This joined `fname` onto
    `dirname(handouts.__file__)` -- the engine package -- which was right only
    while every harness sat in it. The general scorers moved to `scorers/` on
    2026-09-27 and the whole audit died on `FileNotFoundError: agreement.py`
    before a single check ran. Asking the import system where a module is
    cannot go stale: it answers wherever `paths` has put it on the path.
    """
    return _p7.module_source(fname)


def check_exclusions_agree() -> list[str]:
    """Do the three harnesses exclude the SAME cells, from the same source?

    A rate is only comparable to another rate over the same denominator, and
    this project has already published two that were not: `PER_ITEM_EXCLUDE`
    lived in agreement.py and agreement_app.py as two hand-kept mirrors, and in
    baseline.py not at all — so the paper scorer counted 1c p4/p19/p20, Q4c p16
    and Q6 p9, which both other harnesses drop as unreachable. Nothing compared
    the two tables, because they happened to agree; nothing noticed the third
    had none, because nothing looked.

    Identity, not equality: two dicts that are equal today are still two dicts,
    and the point is that there is ONE. A harness that reintroduces a local copy
    fails here even while the contents match.
    """
    import forms as H
    problems = []

    for name in ("agreement", "agreement_app"):
        mod = __import__(name)
        tbl = getattr(mod, "PER_ITEM_EXCLUDE", None)
        if tbl is None:
            problems.append(f"{name}.py no longer exposes PER_ITEM_EXCLUDE")
        elif tbl is not H.PER_ITEM_EXCLUDE:
            same = tbl == H.PER_ITEM_EXCLUDE
            problems.append(
                f"{name}.py keeps its OWN PER_ITEM_EXCLUDE"
                + (" (equal to handouts' today, which is how the last one survived"
                   " — it will drift)" if same
                   else f"; it DIFFERS: {sorted(tbl)} vs {sorted(H.PER_ITEM_EXCLUDE)}"))

    # Every harness that reports a rate must decide what it counts through the
    # one function. A grep, because the alternative is calling each harness's
    # main() to find out.
    for fname in ("agreement.py", "agreement_app.py", "baseline.py"):
        try:
            src = _harness_source(fname)
        except Exception as e:
            problems.append(f"cannot read {fname}: {e}")
            continue
        if "cell_exclusions(" not in src:
            problems.append(
                f"{fname} does not call handouts.cell_exclusions() — it is deciding "
                f"what to count some other way, so its denominator is its own")

    # The kinds must stay in step with what the reporters know how to explain: a
    # new kind that no harness has a sentence for prints as a bare label.
    for fname in ("agreement.py", "agreement_app.py", "baseline.py"):
        src = _harness_source(fname)
        for kind in H.EXCLUSION_KINDS:
            if f'"{kind}"' not in src:
                problems.append(f"{fname} has no wording for exclusion kind "
                                f"`{kind}` — it would report it unlabelled")
    return problems


def check_backend_deviations_declared() -> list[str]:
    """Does every backend declare whether it can use tools, and is that true?

    score.py passes `allow_tools=["Read"]` for items flagged `graph_item`. A
    backend that does not forward the list scores those blind, and blind on a
    graph item is a systematic zero rather than noise: paper+gpt-5-mini returned
    0.00 on 11 of 20 cells of 1c where gold is 6-10, which read as a 5/17 score
    for the model until the cause was found. So the capability is a declaration
    the audit checks, not a comment.
    """
    import inspect
    import backends as B
    import forms as H

    problems = []
    classes = [(n, c) for n, c in vars(B).items()
               if inspect.isclass(c) and n.endswith("Backend") and n != "BackendError"]
    if not classes:
        return ["no *Backend classes found in backends.py — this audit is stale"]

    for name, cls in sorted(classes):
        if not hasattr(cls, "SUPPORTS_TOOLS"):
            problems.append(
                f"{name} does not declare SUPPORTS_TOOLS. Every backend must say "
                f"whether it forwards allow_tools, or a graph item scored blind "
                f"is reported as a model result")
            continue
        try:
            src = inspect.getsource(cls)
        except OSError:
            continue
        # Claimed True has to be visible in the source: the parameter is in every
        # signature, so accepting it proves nothing — it has to be USED.
        body = src.split("def complete", 1)[-1]
        uses = ("allowedTools" in body or "allow_tools" in body.split("\n", 1)[-1]
                .replace("allow_tools: list[str] | None = None,", ""))
        if cls.SUPPORTS_TOOLS and not uses:
            problems.append(
                f"{name} declares SUPPORTS_TOOLS=True but its complete() never "
                f"uses allow_tools — it would score graph items blind while "
                f"claiming otherwise")

    # And the derivation must actually find the items, or the deviation is empty
    # and nothing is ever excluded.
    for h in _forms():
        items = [it["id"] for it in H.config(h)["rubric"].ITEMS if it.get("graph_item")]
        got = H.not_comparable_items(h, supports_tools=False)
        if set(items) != set(got):
            problems.append(
                f"handout {h}: graph items {sorted(items)} but "
                f"not_comparable_items() returns {sorted(got)}")
        if H.not_comparable_items(h, supports_tools=True):
            problems.append(
                f"handout {h}: not_comparable_items() excludes items even when the "
                f"backend HAS tools; it would drop a measurable item")
    return problems


def check_blank_collapse_is_gated() -> list[str]:
    """Does "did not answer" require an answer that is actually missing?

    Every item with a `blank_code` collapses an all-slots-failed ledger into that
    one code, so a blank page reports the way a grader wrote it rather than as
    eight separate slot failures. The collapse used to fire on ANY all-failed
    sheet, including one where the student wrote something and every part of it
    was judged wrong — and the feedback they read then opened with "did not
    answer" about an answer they had written.

    Invisible in the numbers, which is why it needs a check rather than a
    measurement: for every item carrying one, the blank code's points equal the
    sum of the scorable components, so both ledgers clamp to the same score. Only
    the code and the prose differ, and the prose is the half a student reads.

    Stated as a RELATIVE invariant on purpose: whatever sheet is built below, if
    the blank-response call collapses then the written-response call must not.
    An earlier version asserted that a hand-built sheet WOULD collapse, which
    meant it was really testing whether the probe modelled derive_ledger's gates,
    suppressions and verdict vocabularies correctly — it did not, and reported
    six items that were behaving perfectly. A guard that cannot tell its own bugs
    from the code's is worse than none.
    """
    rubric_h1, rubric_h2, rubric_h3 = _rubric_views()
    from score import derive_ledger

    problems = []
    for h, mod in ((1, rubric_h1), (2, rubric_h2), (3, rubric_h3)):
        for item in mod.ITEMS:
            blank = item.get("blank_code")
            if not blank:
                continue
            # Only items where the COLLAPSE can fire. T1 and T2 have a single
            # credit component whose own `absent` code is BLANK, so they report
            # it as that component's verdict and never through the collapse —
            # which derive_ledger requires more than one scorable slot for.
            # Reporting them here was a false positive on a correct design.
            scorable = [c for c in item["credit"]
                        if not c.get("reported") and c.get("pts") is not None]
            if len(scorable) < 2:
                continue
            slots = {}
            for c in item["credit"]:
                verdicts = c.get("verdicts") or ["met", "absent"]
                if c.get("gates") or c.get("reported") or c.get("pts") is None:
                    slots[c["what"]] = {"verdict": "met" if "met" in verdicts
                                        else verdicts[0], "evidence": "probe"}
                else:
                    bad = [v for v in verdicts if v != "met"]
                    slots[c["what"]] = {"verdict": bad[0] if bad else "absent",
                                        "evidence": "probe"}
            raw = {"slots": slots}
            blank_led, *_ = derive_ledger(item, raw, response="   \n  ")
            wrote_led, *_ = derive_ledger(item, raw, response="the student wrote this")
            collapsed_blank = any(d["code"] == blank for d in blank_led)
            collapsed_wrote = any(d["code"] == blank for d in wrote_led)
            if collapsed_blank and collapsed_wrote:
                text = next((d["text"] for d in item["deductions"]
                             if d["code"] == blank), blank)
                problems.append(
                    f"H{h} {item['id']}: the same sheet reports {blank} whether or "
                    f"not the student wrote anything — they would read "
                    f"\"{text[:40]}\" about an answer they wrote")
    return problems


# Participants named in an item's own prompt, e.g. "cost participant 20 three
# points". Attributed citations only — a few-shot exemplar is reproduced in FULL
# and never attributed, which is why `exemplar_participants` is a separate
# mechanism and is not checked against this.
_CITED_RE = re.compile(r"participants?\s+((?:\d+)(?:\s*(?:,|and)\s*\d+)*)", re.I)


def _prompt_text(item: dict) -> str:
    """Every field of a rubric item that reaches the generated prompt."""
    out = []
    for key in ("guidance", "question", "label"):
        v = item.get(key)
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, list):
            out += [x for x in v if isinstance(x, str)]
    for c in item.get("credit", []) or []:
        if isinstance(c.get("desc"), str):
            out.append(c["desc"])
    for d in item.get("deductions", []) or []:
        if isinstance(d.get("text"), str):
            out.append(d["text"])
    return "\n".join(out)


def check_citations_match_exclusions() -> list[str]:
    """Does every `cited_participants` entry still have a citation to justify it?

    A cell is registered because the item's prompt names that participant and
    states the grader's decision, which makes scoring them recall rather than
    judgement. Edit the guidance and that justification can vanish while the
    registration stays — and then the item reports a rate over cells chosen for a
    reason that no longer exists, which is the exact flattery the registry was
    built to remove.

    Both directions are wrong and both are reported:

      registered, no longer cited   the cell is dropped from the rate for
                                    nothing. Re-count it.
      cited, not registered         the prompt hands the model the answer and
                                    the rate counts it anyway.

    Deliberately narrow. It compares against `cited_participants` ONLY, not the
    merged view from cell_exclusions(): `exemplar_participants` are reproduced in
    full and never attributed, so no regex can find them, and `unscoreable` cells
    are about a gold row rather than a prompt. An earlier version of this check
    compared against the merged set and reported both of those as faults — two
    false alarms out of two findings, on a corpus with no real ones.
    """
    # Participant numbers are student data; the registry lives in the record,
    # not in code.
    # PYTHON KEEPS THE FETCH. The self-test injects by adding a participant to
    # `FORMS[1]["cited_participants"]` IN MEMORY, and a payload the runner
    # rebuilds from `course.json` cannot see it. The registry's VALUES still
    # come from the record -- `FORMS` merges `HANDOUT_FIELDS` at import -- so
    # this reads the record too, just through the object the injection touches.
    from forms import FORMS

    import lo_enforce

    items = []
    for h, mod in zip(_forms(), _rubric_views()):
        registry = FORMS[h].get("cited_participants") or {}
        for item in mod.ITEMS:
            items.append({
                "form": h, "id": item["id"],
                "promptText": _prompt_text(item),
                "registered": sorted(registry.get(item["id"], []) or []),
            })
    return lo_enforce.run("citations_match_exclusions", {
        "items": items,
        "exemplars": {str(h): sorted(FORMS[h].get("exemplar_participants") or [])
                      for h in _forms()},
    })


def _handsplit_tables() -> dict[str, dict]:
    """{path: table} for every hand-split fixture a measured item declares.

    A seam, not a convenience: the selftest replaces this to inject a bad row,
    which is the only way to prove the check below still detects one.
    """
    import json
    import os
    import agreement_app as APP

    out = {}
    for spec in APP.JOBS.values():
        path = spec.get("handsplit")
        path = str(_p7.record_path(path)) if path else path
        if not path or not os.path.exists(path):
            continue                 # corpus absent on this machine — see below
        try:
            with open(path) as fh:
                out[path] = json.load(fh)
        except (OSError, ValueError) as e:
            out[path] = {"__error__": str(e)}
    return out


def check_handsplit_rows_are_disjoint() -> list[str]:
    """Does any hand-split row put the same text in two fields?

    A hand-split table says which of a paper block's sentences belongs in which
    of the web's boxes. The boxes are disjoint by construction — one sentence
    cannot be both the first active-behaviour example AND the statement about
    whether the behaviour is worth modifying — so a row where one field contains
    another is a transcription fault, and it feeds the model an answer the
    student did not give in that box.

    Q4b p7 is why this exists. The student left `Modify:` blank on the page and
    wrote their modify answer in example box 1. The table put that sentence in
    BOTH `bmod_h1_q4b_modify` and `bmod_h1_q4b_first`, so the harness showed the
    model a modify statement where the student had written nothing, and the model
    scored it as an example — 5.00 against a gold of 2.00, stable across every
    run and every prompt wording tried. It was found by chance, from an evidence
    quote that read oddly.

    Skips silently when the corpus is not on this machine. The tables live in
    $COURSE_DATA, outside both repositories by design, so a checkout without the
    student data must not fail this audit — it simply has nothing to check.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K: python reads the hand-split
    # tables -- they are source documents and knowing where they live is
    # python's half -- and `enforce/handsplitDisjoint.ts` judges containment.
    #
    # PROVEN WITH A CONTROL: one box's text copied into a sibling box of the
    # same row produced the same single finding on both sides.
    # SELF-ASSEMBLED. Subgoal E63: the runner builds this payload, and the
    # assembler was proven to build what python built -- payload-identical, or
    # order-only with the finding SET shown unchanged on data mutated until
    # the rule fires. `runner.SELF_ASSEMBLING` is that cleared list.
    import lo_enforce

    # PYTHON KEEPS THE FETCH. Self-assembly reads this from DISK; the
    # self-test injects into the IN-MEMORY table and forks, so a rebuilt
    # payload cannot see it and the case goes silent. Measured 2026-09-26.
    # `_handsplit_tables` says so in its own docstring: "A seam, not a
    # convenience: the selftest replaces this to inject a bad row, which is the
    # only way to prove the check below still detects one." Self-assembly walked
    # straight past that seam.
    import os

    import lo_enforce

    return lo_enforce.run("handsplit_rows_are_disjoint", {"tables": [
        {"name": os.path.basename(path),
         "rows": [{"pid": pid, "fields": fields}
                  for pid, fields in (doc or {}).items()
                  if isinstance(fields, dict)]}
        for path, doc in _handsplit_tables().items()]})



def _declaration_list(name: str) -> list:
    """A list-shaped declaration, through the accessor.

    THE FIRST VERSION REACHED `coursedata._load()` and the schema check refused
    it in the same breath: obligation 3 is that no module crosses the boundary,
    and a raw read is exactly that crossing. `coursedata.declaration_list` is
    the accessor.
    """
    import coursedata

    return coursedata.declaration_list(name)



# Slot rules that reach the web and CLI and NOT score.py. PRE-EXISTING, and
# declared rather than hidden: these predate the `rule` field and each one is a
# real divergence. They are listed so a NEW one fails the audit immediately
# instead of joining a backlog nobody can see. Migrating one means moving its text
# to the credit component's `rule` field, which both generators render, and
# re-measuring the paper scorer on that item -- a scoring change per item, which
# is why they are not done in a batch.
#
# NOT THEORETICAL, and the cost is now measured. The five `1a:*` notes carry 129
# to 494 characters of judging text each, reach the web prompt and not the CLI's,
# and 1a/p6 scores 0.0 on the paper path against 6.0-8.0 on the web -- the whole
# item, stably, in 3 of 3 runs. Confirmed fragment by fragment on 2026-08-28. The
# `1a:*` entries are therefore the ones to migrate first: they are the only group
# with a measured price attached.
#
# Hoisted out of the check so the ratchet below reads the same list the check
# does. Two copies of this would drift, which is the failure the whole
# equivalence goal is about.
# MOVED TO THE RECORDS 2026-09-25: this course's backlog, not the
# engine's. While it lived here the ratchet rule could be run from
# python and from nowhere else.
SLOT_RULE_BACKLOG = _declaration_list("SLOT_RULE_BACKLOG")

def _budget(name: str) -> int:
    """A ratchet ceiling, from the course's records rather than from here.

    Moved 2026-09-25 on the user's instruction, beside the tables they bound.
    A budget is a fact about THIS COURSE -- `PROSE_ONLY_BUDGET` is 27 because
    this rubric has 27 prose-only slots -- so it was course data sitting in the
    engine, and it left every ratchet rule unfeedable from inside lo-blocks.
    """
    import coursedata

    return coursedata.declared_number(name)



# How many may remain. It may only go DOWN. Same ratchet as HANDCODED_BUDGET, for
# the same reason and on the evidence of the same day: a declared backlog with no
# ceiling reads as coverage while enforcing nothing about its own size, and this
# one had grown to seventeen entries costing at least one item its whole score.
SLOT_RULE_BACKLOG_BUDGET = _budget("SLOT_RULE_BACKLOG_BUDGET")


# The three programs that write scoring artifacts, and the field each must stamp.
ARTIFACT_WRITERS = (("agreement.py", "the python harness"),
                    ("agreement_app.py", "the app harness"),
                    ("score.py", "the paper scorer"),
                    # score.py writes one file per (run, handout, participant).
                    # paper_runs.py folds those into the per-item runs shape the
                    # ledger records and stamps the era on the way -- including
                    # the MODEL, which matters most here: the paper scorer is
                    # swept on gpt-5-mini AND on Opus, and only the first is
                    # comparable to the web and cli columns.
                    ("paper_runs.py", "the paper sweep folder"))


def slot_basis(item: dict) -> dict:
    """What DECIDES each of an item's slots: arithmetic, or the model reading prose.

    A cross-path divergence means something different depending on which. On a
    computed slot the two sides ran different ARITHMETIC and that is a bug with a
    single right answer. On a prose-judged slot they ran the same instruction and
    the model landed differently, which no static check can see, because both
    sides are given the same text verbatim.

    Computed rather than listed. A hand-written table of prose-judged slots would
    drift from the rubric the moment a slot changed, and drift is the failure this
    whole goal is about.
    """
    computed = {}
    # Every key-excluding primitive, `maps` included. Leaving it out reported
    # Q4b's behavior_* as prose-judged on the day they stopped being judged at all.
    for kind in ("equals", "forbid", "expect", "derived", "maps"):
        for r in item.get(kind) or ():
            if isinstance(r, dict) and r.get("key"):
                computed[r["key"]] = f"computed:{kind}"
    counted = set()
    for cr in item.get("counts") or ():
        counted.update(cr.get("slots") or ())
        if cr.get("key"):
            counted.add(cr["key"])

    out = {}
    for c in item.get("credit") or ():
        key = c["what"]
        if key in computed:
            out[key] = computed[key]
        elif key in counted:
            out[key] = "counted"
        elif c.get("rule"):
            out[key] = "prose+rule"
        else:
            out[key] = "prose"
    return out


# Slots whose verdict rests on a per-slot RULE and on nothing computable: the
# prose channel, enumerated so it is known rather than merely suspected.
#
# Why declared and not just computed. The computation above tells you a slot is
# prose-judged; this says someone LOOKED. Q4b/p4 is why it matters: paper 2.0
# against web 3.5, gold 2.0, the two paths reading the same REJECT test
# differently, and nothing in the audit able to object because there is no textual
# difference to find. When the sweep's divergence table names one of these slots,
# the answer is "prose, and we knew"; when it names a slot NOT on this list, the
# arithmetic diverged and that is a bug.
#
# The budget ratchets like the others. A tenth entry means a new rule was written
# as prose where it could have been a primitive -- which is the choice subgoal 3
# spent seven conversions undoing -- so it has to be a decision, not a default.
# Each reason must answer ONE question: why is this not a primitive? A reason that
# merely describes the rule leaves the entry looking settled when it is a work
# item. CONVERTIBLE marks the ones that could become declarations -- those are the
# list's whole point, because a declaration is something the enforcement audit can
# compare between the two scorers and prose is not.
# ---------------------------------------------------------------------------
# STAGE 4. Seven scoring DECLARATION tables were module-level data here, which
# made the enforcement module carry course content. They are declarations about
# THIS COURSE -- which slots are prose-only, which text was deliberately
# designed, which verdicts go uncharged -- and are read from the course file now.
#
# The authored tables live in `declaration_source.py`, a builder outside the
# scoring path, for the reason `generator_source.py` exists: the export must read
# them from somewhere that does not read the file it is writing.
#
# CONSENSUS_OVERLAP_BACKLOG did NOT move. It is keyed by participant -- ('2a',
# 18, 'how1', 'verdict') -- and C1b puts anything keyed by a participant in the
# gold file, outside this public repository.
#
# Five more did not move either, and for a different reason:
# `table_sensitivity.py` measured that emptying them moves no check that reads
# them, so nothing would report the loss if the migration went wrong.
# ---------------------------------------------------------------------------
def _declaration(name: str) -> dict:
    import coursedata

    return coursedata.declaration(name)


COUNTABLE_EXEMPT = _declaration("COUNTABLE_EXEMPT")
SELFTEST_NAMED_FIXTURES = _declaration("SELFTEST_NAMED_FIXTURES")
PROBE_UNREACHABLE_PAIRS = _declaration("PROBE_UNREACHABLE_PAIRS")
# AUTHORED IN `declaration_source.py`, like every other declaration with a
# reason attached: it has to reach the ENGINE, and the engine reads the course
# file. A copy here would be the second statement of one fact.
HAND_AUTHORED_SHEET_ATTRS = _declaration("HAND_AUTHORED_SHEET_ATTRS")
# WHICH BOX ROLES MAY SHARE A CLAUSE. Declared, because the rule is generic and
# the vocabulary is this instrument's -- see `declaration_source`.
OVERLAP_SIBLING_ROLES = _declaration_list("OVERLAP_SIBLING_ROLES")
# What gold CALLS each box. E58 moved it out of the check below, where it was a
# dict literal keyed by this course's item ids. Its reasoning travelled with it.
GOLD_BOX_WORDS = _declaration("GOLD_BOX_WORDS")
import coursedata as _CD

# FROM THE RUBRIC since 4a: `<Item family="...">`. It was a declaration naming
# eight item ids, which is course content in an enforcement module.
SLOT_STRUCTURE_FAMILIES = _CD.slot_structure_families()
HAND_AUTHORED_ATTRS = _declaration("HAND_AUTHORED_ATTRS")
PROSE_ONLY_SLOTS = _declaration("PROSE_ONLY_SLOTS")
# RAISED 25 -> 27 on 2026-09-12 for two slots the audit had been reporting as
# UNDECLARED, not for two new prose rules: `1c.series_box_holds` and
# `DAY2.targets_own_behavior` were already judged by prose and by nothing
# computable, and the budget moves because the DECLARATION was written, not
# because the corpus grew. Lower it whenever one converts to a primitive.
PROSE_ONLY_BUDGET = _budget("PROSE_ONLY_BUDGET")


# WHICH PRIMITIVE SET each "NOT CONVERTIBLE" claim was judged against.
#
# Convertibility is not an absolute property of a rule; it is a claim about what
# the available primitives can express, and the primitive set grows. `maps` did
# not exist a week ago, and when it landed it CHANGED what was convertible about
# Q4b's picks -- behavior_1/behavior_2 left this table entirely and the picks'
# reasons were rewritten to say so. Nothing forced that rewrite. It happened
# because one person was holding both pieces at once, which does not scale.
#
# So each entry records the set it was judged against, and the check fails when
# the registry no longer matches. It fires exactly once per primitive added,
# which is precisely when the answer can have changed.
#
# THIS IS NOT PRESSURE TO CONVERT. A re-judged entry that is still not
# convertible gets a new stamp and the budget stays 9. The point is that the
# claim is re-made deliberately rather than inherited.
_PRIMS_2026_08_29 = "counts,cover,derived,equals,expect,forbid,maps,onlyif,requires"

PROSE_ONLY_JUDGED_AGAINST = _declaration("PROSE_ONLY_JUDGED_AGAINST")


# Items built from ONE pattern, whose shared slot names should therefore mean the
# same thing. Scoped by family rather than corpus-wide on purpose: `keyword`
# legitimately differs between Q4a and Q4c (one deduction zeroed by decision, the
# other declared unreachable), and 1a's week_* slots are not siblings of these.
# SLOT_STRUCTURE_FAMILIES IS BOUND FURTHER DOWN, after `_declaration` is defined. Its
# entries live in the course file, authored in `declaration_source.py`.

# A slot whose gate/points structure is deliberately not uniform in its family.
# The budget ratchets: an entry is either a decision with a reason or a defect
# waiting to be fixed, and it must not sit here being neither.
# Declared in the course file since E63, 2026-09-25, so that
# `sibling_slots_share_their_structure` can be fed from lo-blocks: the families
# already derive from the rubric and the budget already lives in the course
# file, and this was the last input still on the python side. Its reasoning --
# why it is empty and meant to stay so -- travelled with it and is quoted in
# `declaration_source`.
SLOT_STRUCTURE_DIVERGENCES: dict[tuple[str, str], str] = _declaration(
    "SLOT_STRUCTURE_DIVERGENCES")
# ZERO, and it is meant to stay there. The single entry was DAY1's
# `phrased_directly`, retired 2026-09-04 by RENAMING the gated variant
# `phrased_directly_gate` rather than exempting it: if two sheets price a
# question differently they are not asking the same question, and the shared name
# is what made a recorded claim about the slot wrong (subgoal Q21's precision
# table). A new entry here now means someone chose an exemption over a name.
SLOT_STRUCTURE_BUDGET = _budget("SLOT_STRUCTURE_BUDGET")


def _family_slot_structure() -> dict:
    """(family, slot) -> {item: (gates, pts)} read from the OLX slot specs.

    From the OLX and not from a run artifact: the artifacts only exist after a
    sweep, and a structural check should not need one. `!key` gates; `@n` carries
    points.
    """
    import re as _re
    import pathlib as _pl

    import agreement_app as _A

    olx = {f.name: f.read_text() for f in _p7.handout_olx_paths()}
    out: dict = {}
    for fam, items in SLOT_STRUCTURE_FAMILIES.items():
        for item in items:
            g = (_A.JOBS.get(item) or {}).get("grader") or ""
            if not g:
                continue
            act = g.replace("_grader", "_llm")
            tag = None
            for txt in olx.values():
                m = _re.search(r"<LLMAction\b(?:(?!</?LLMAction)[^>])*?(?:^|\s)id=\""
                               + _re.escape(act) + r"\"(?:(?!</?LLMAction)[^>])*>",
                               txt, _re.S)
                if m:
                    tag = m.group(0)
                    break
            if tag is None:
                continue
            sm = _re.search(r'slots="([^"]*)"', tag, _re.S)
            for part in (sm.group(1).split("|") if sm else []):
                key = part.split(":")[0].strip()
                gates = key.startswith("!")
                key = key.lstrip("!")
                pts = _re.search(r"@([0-9.]+)", part)
                out.setdefault((fam, key), {})[item] = (
                    gates, float(pts.group(1)) if pts else None)
    return out


def check_sibling_slots_share_their_structure() -> list[str]:
    """Does a slot NAME mean the same thing across the items built from one pattern?

    Eight H2 items are one family authored from one template. A slot that GATES in
    one of them and is advisory in the other seven is either a decision or a typo,
    and until this check the audit could not tell those apart: both scorers honour
    whatever the OLX says, identically, so nothing in the equivalence machinery
    objects. That is the blind spot -- it is a RUBRIC defect, and the equivalence
    audit is not looking for those.

    The instance that prompted it: `phrased_directly` is `!phrased_directly` on
    DAY1 and plain on the other seven, so on DAY1 alone it can zero the item.
    Undeclared anywhere, and found only because DAY1's error profile looked unlike
    its siblings'.

    THE OUTPUT IS A QUESTION, NOT A NORMALISATION. "These seven agree and this one
    does not" may well resolve in favour of the odd one. A declaration with a
    reason is the product; a sweep that makes every slot identical is not.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K: python fetches the structure --
    # `_family_slot_structure()` walks the rubric view -- and reports;
    # `enforce/siblingSlots.ts` decides. "Sibling items built from one pattern
    # should give a slot name one meaning" is a statement about authoring under
    # SlotSheetGrader, so the judgement is generic and only the families and the
    # declared exceptions are ours.
    #
    # PROVEN AGAINST THIS RUBRIC with a control, because the families currently
    # agree and a clean corpus makes any port look right: flipping one item's
    # shape produced one finding, byte-identical on both sides.
    # SELF-ASSEMBLED. E63: the last input on the python side -- the
    # divergence table -- moved to the course file, and the assembler then
    # built an IDENTICAL payload on the first attempt. Fired identically
    # with one item's gate flipped.
    import lo_enforce

    return lo_enforce.run("sibling_slots_share_their_structure", None)


def check_prose_only_claims_are_current() -> list[str]:
    """Was each "NOT CONVERTIBLE" claim judged against TODAY's primitive set?

    See PROSE_ONLY_JUDGED_AGAINST. A rule is prose-only relative to what the
    primitives can express, so the claim expires when the registry grows -- and
    it expires silently, because a stale claim looks exactly like a live one.

    Q4b's picks are the worked example: `maps` made part of that slot's judging
    arithmetic, two entries left the table, and the remaining reasons had to be
    rewritten. If `requires` lands on Q6 (subgoal 15), the two Q6 `affect_*`
    entries are due the same way -- their reasons turn on what `cover` already
    constrains, and `requires` is the primitive that acts on what cover sees.

    The key sets must match exactly, in both directions: an unstamped entry is a
    claim nobody dated, and a stamp with no entry is a claim that has already
    gone.
    """
    # PORTED to `enforce/proseOnlyClaimsCurrent.ts` (goal K).
    #
    # THE REGISTRY IS THE ENGINE'S. `primitives.json` says what a rule CAN be
    # expressed as, and the claim this check tests is about exactly that -- so
    # the check belongs beside the registry. Python still passes what it reads,
    # so this path answers about the tree it resolves.
    from olx_prompts import primitives

    import lo_enforce

    return lo_enforce.run("prose_only_claims_are_current", {
        "now": sorted(p["attr"] for p in primitives()["primitives"]),
        "slots": ["|".join(k) for k in PROSE_ONLY_SLOTS],
        "judgedAgainst": {"|".join(k): v
                          for k, v in PROSE_ONLY_JUDGED_AGAINST.items()},
    })



# Items whose rubric entry genuinely carries no substantial comment block, so
# §2e has nothing to push for them. Verified, not assumed: 1c's and 3's longest
# comment runs are three lines against a threshold of four.
# 1c LEFT this set on 2026-08-30: the E11 migration gave `legend` a `rule`, and
# the comment recording why it moved is a comment block §2e now finds. The set is
# for items whose rubric genuinely carries no rationale, and 1c is no longer one.
# EMPTIED 2026-09-12: §2d now finds comment blocks for item 3, so the exemption
# describes nothing. An entry for an item that HAS comments reads as coverage of
# a gap that has closed -- the same fault as a spent SCORER_NEUTRAL pair -- and
# would suppress a real finding if item 3's comments were ever removed again.
NO_RUBRIC_COMMENTS: set[str] = set()


# A key-excluding primitive the CLI cannot compute, with the reason. `derived` is
# declared only on 1c, where it reads the four typed data fields the web page
# collects and draws its chart from; there is no way to ask a .docx that question,
# which is the platform-forced 1c deviation already in EQUIVALENCE.md.
# Scoped BY KIND, not by attribute, since score.py started computing part of
# `derived`. An attribute-level entry had exactly two settings once that happened
# -- keep it and the audit stops looking, or drop it and the audit stops knowing
# that `complete` is still uncomputed on the paper path. Neither states the truth,
# which is that one kind crossed over and three did not.
COMPUTE_EXEMPT = {"derived": {
    "kinds": ("plots", "complete", "present"),
    "why": "platform-forced: these read the web page's typed data fields, which "
           "the paper submission has no equivalent of. `contains` is not exempt "
           "-- it asks whether a word appears in the response text, which the "
           "paper path does have. See EQUIVALENCE.md's 1c deviation.",
}}


def _exempt_kinds_are_still_uncomputed(attr: str) -> list[str]:
    """Is a kind-scoped COMPUTE_EXEMPT still telling the truth?

    Two ways it can rot, and both are reported:

      * a kind the exemption calls uncomputable that score.py now computes --
        the exemption is stale and is hiding a check the audit should be making;
      * a kind AUTHORED in the OLX that is neither exempt nor implemented -- the
        web computes it, the paper path silently does not, and no declaration
        says so. This is the gap the attribute-level entry used to cover for the
        whole primitive.
    """
    if attr != "derived":
        return []
    spec = COMPUTE_EXEMPT.get(attr)
    spec = spec if isinstance(spec, dict) else {}
    import score as S

    implemented = getattr(S, "DERIVED_KINDS_IMPLEMENTED", frozenset())
    exempt = set(spec.get("kinds", ()))
    out = []
    for kind in sorted(exempt & set(implemented)):
        out.append(f"COMPUTE_EXEMPT excuses `{attr}`:`{kind}` as uncomputable on "
                   f"the CLI, but score.py implements it -- drop that kind from "
                   f"the exemption")
    for kind in sorted(_authored_derived_kinds() - exempt - set(implemented)):
        out.append(f"`{attr}`:`{kind}` is authored in the OLX and computed by the "
                   f"web, but score.py neither implements nor exempts it, so on "
                   f"the paper path the check is never set and nothing reports it")
    return out


def _authored_derived_kinds() -> set:
    """Every `derived` kind actually used by an authored sheet."""
    import olx_prompts as OP

    out = set()
    for form in _forms():
        src = OP._src(form)
        for m in re.finditer(r'\bderived="([^"]*)"', src, re.S):
            for entry in m.group(1).split("|"):
                parts = entry.strip().split(":")
                if len(parts) > 1 and parts[1].strip():
                    out.add(parts[1].strip())
    return out


def check_fails_verdict_is_mirrored_in_the_app() -> list[str]:
    """Does the RUNTIME understand `key->verdict` too?

    Three implementations parse these attributes: score.py, agreement.py, and
    lo-blocks' slotSheet.ts, which is the one students meet. A syntax the first two
    understand and the third does not is worse than a syntax nobody understands,
    because the arrow becomes part of the KEY: no slot matches
    `behavior_1->not_active`, so the check it names is never computed, never
    charged, and nothing reports it. The app's own test asserts exactly that
    failure mode.

    Checks the SOURCE rather than running node: the mirror is a fact about the
    file, and the app's test suite already exercises the behaviour.
    """
    # PORTED to `enforce/runtimeParsesFailsVerdict.ts` (goal K).
    #
    # THE READER MOVED TO THE RIGHT SIDE. Python reached across the repository
    # boundary to grep an ENGINE file for ENGINE function names -- exactly the
    # coupling this goal removes. `slotSheet.ts` belongs to lo-blocks and so does
    # the check on it; python still passes the source it read, so the answer here
    # is about the file this process can see rather than whichever tree the
    # runner happens to resolve.
    import pathlib

    import lo_enforce
    import paths

    ts = pathlib.Path(paths.SLOTSHEET_TS)
    try:
        src = ts.read_text()
    except OSError as e:
        return [f"cannot read {ts} to confirm the app understands `->`: {e}"]
    return lo_enforce.run("fails_verdict_is_mirrored_in_the_app",
                          {"name": ts.name, "src": src})

def check_both_engines_compute_the_same_primitives() -> list[str]:
    """If a primitive removes a key from the schema, BOTH engines must compute it.

    A key that leaves the response schema is a key the model is not asked, so
    whichever side does not compute it has no value for that check at all. The
    consequences differ by side but both are silent: the web would score a check it
    never set, and score.py simply never sets it -- the check does not fire, its
    code is never charged, and nothing reports a problem.

    That was live, latently: `expect` was computed by agreement.apply_computed for
    any item and by score.py only inside derive_oc_ledger, so an `expect` declared
    on a credit-path item was honoured on one side and ignored on the other. No
    credit-path item declared one, so it cost nothing -- it was found by needing one
    for Q4b, which is the wrong way to find it.

    Reads the REGISTRY rather than a list of primitive names, so a primitive added
    to primitives.json is covered the day it lands.
    """
    import inspect
    import olx_prompts as OP

    try:
        import agreement as A
        import score as S
    except Exception as exc:
        return [f"could not import both engines to compare their computation: {exc}"]

    # THE COMPUTATION ENTRY POINTS, not the modules. Scanning whole modules made
    # this check inert: score.py mentions "expect" in helper functions, so removing
    # the computation loop entirely left the check silent -- it would have missed
    # the very gap it was written for. And scanning one function per side is wrong
    # the other way: `counts` is expanded by agreement.expand_counted, not by
    # apply_computed, so a single-function scan reports a mismatch that is not one.
    WEB_FNS = ("apply_computed", "expand_counted")
    # THE ENGINE'S OWN DERIVER, plus the plugin's, read from where each now
    # lives. Goal E step 4: `derive_oc_ledger` is not a `score` name any more.
    CLI_FNS = ("derive_ledger",)

    def _src(mod, names):
        out = []
        for n in names:
            fn = getattr(mod, n, None)
            if fn is None:
                return None, f"{mod.__name__}.{n} is gone -- retarget this check"
            try:
                out.append(inspect.getsource(fn))
            except Exception as exc:
                return None, f"cannot read {mod.__name__}.{n}: {exc}"
        return "\n".join(out), None

    web, err = _src(A, WEB_FNS)
    if err:
        return [err]
    cli, err = _src(S, CLI_FNS)
    if err:
        return [err]
    _oc = _oc_scorer()
    if _oc is None:
        return ["this course ships no `oc` scorer, so the criteria side of the "
                "comparison is missing -- retarget this check"]
    oc_src, err = _src(_oc, ("derive_ledger",))
    if err:
        return [err]
    cli = cli + "\n" + oc_src

    out = []
    for attr in OP.primitive_attrs(excluding_keys=True):
        # A READ of the declaration, not a mention of the word.
        pats = (f'get("{attr}"', f"get('{attr}'", f'["{attr}"]', f"['{attr}']")
        w = any(x in web for x in pats)
        c = any(x in cli for x in pats)
        if w and not c and attr not in COMPUTE_EXEMPT:
            out.append(f"`{attr}` removes keys from the schema and the web computes "
                       f"it, but score.py never reads item[{attr!r}]. The model is "
                       f"not asked for those keys, so on the CLI the check is never "
                       f"set, its code is never charged, and nothing reports it")
        if c and not w:
            out.append(f"`{attr}` is computed by score.py and not by agreement.py, "
                       f"so the web scores a check it never set")
        # A kind-scoped exemption is checked per KIND, because the attribute-level
        # question ("does score.py mention it?") stopped separating the kind that
        # crossed over from the three that did not.
        #
        # NOT guarded on `attr in COMPUTE_EXEMPT`. It was, and that made the table
        # unprobeable: emptying it left score.py still reading `derived`, so the
        # branch above could not fire either, and deleting the whole declaration
        # produced no finding at all. Every authored kind must be accounted for
        # whether or not an exemption exists -- the exemption says WHICH kinds are
        # excused, not whether the question gets asked.
        out += _exempt_kinds_are_still_uncomputed(attr)
    return out


def check_computed_rules_do_not_share_a_key() -> list[str]:
    """Two computed rules writing the SAME check: the second silently wins.

    Both engines compute `forbid` and `expect` in a loop that ASSIGNS the check --
    `checks[rule["key"]] = ...` in agreement.apply_computed, `slots[rule["key"]] =
    ...` in score.derive_ledger. So two rules on one key are not an OR, which is
    how anyone would read them; the last one decides and the first is dead.

    Both sides do it identically, so it is not a divergence -- it is a trap. It was
    found while designing a disjunction for Q4b's INSTEAD-OF test, which needed
    exactly that OR and would have silently got "whichever rule I wrote last".

    Nothing authors a duplicate today. This makes the day someone does an audit
    failure rather than a wrong number, and it belongs here rather than in a
    comment because the loop reads correct.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K. Python reads the three rubric
    # views and hands over each item's computed-rule KEYS, in authored order;
    # `enforce/computedKeys.ts` counts the collisions. Which primitives ASSIGN
    # is named there rather than inferred from the payload, so a primitive
    # added to the engines and not to that list is unwatched loudly.
    # SELF-ASSEMBLED. Subgoal E63: the runner builds this payload, and the
    # assembler was proven to build what python built -- payload-identical, or
    # order-only with the finding SET shown unchanged on data mutated until
    # the rule fires. `runner.SELF_ASSEMBLING` is that cleared list.
    import lo_enforce

    return lo_enforce.run("computed_rules_do_not_share_a_key", None)



def check_prior_record_reaches_every_item() -> list[str]:
    """Does the §2e hook actually find the record, for every item?

    It did not, for twelve of them, for as long as rubric_h2 has been a factory.
    `prior_record` located an item's comments by searching for a literal
    `"id": "DAY1"` line; rubric_h2 builds its items from `_example_use_item(...)`,
    so no H2 item ever matched and the hook printed "could not read rubric_h2.py:
    StopIteration" on every H2 --write. It was visible and nobody read it, which is
    the only kind of failure a printed warning produces.

    §2e is the discipline that the record gets pushed at the moment a rule changes
    -- it exists because ~900 calls were spent rewriting a rule whose comment
    already contained the answer. A hook that silently finds nothing on the handout
    with the most recorded dead ends is worse than no hook, because the empty
    output reads as "nothing recorded".

    So this asserts coverage per item, with the genuinely-empty ones declared.
    """
    import olx_prompts as O

    out = []
    for item in sorted(getattr(O, "ACTION", {})):
        try:
            text = O.prior_record(item)
        except Exception as e:
            out.append(f"prior_record({item}) raised {type(e).__name__}: {e}")
            continue
        if "no recorded comments found" in text:
            out.append(f"§2e cannot read {item}'s rubric: the hook reports a lookup "
                       f"failure, so its output reads as 'nothing recorded' when the "
                       f"record may be there")
            continue
        # EITHER SOURCE COUNTS. The hook reads the course file for items whose
        # record was carried there and the module's factory bodies for the rest,
        # so asserting the `rubric_hN.py:` label alone would report every
        # carried item as having no record -- and would start doing so on the
        # day Stage 5 deletes the files, which is precisely when this check is
        # the thing standing between §2e and silence.
        blocks = [l for l in text.splitlines()
                  if (".py:" in l and "rubric_h" in l) or "course file," in l]
        if not blocks and item not in NO_RUBRIC_COMMENTS:
            out.append(f"§2e finds no rubric comment block for {item}. Either the "
                       f"lookup broke for its rubric's shape, or the item genuinely "
                       f"has none -- if the latter, add it to NO_RUBRIC_COMMENTS so "
                       f"the silence is declared rather than assumed")
    for item in sorted(NO_RUBRIC_COMMENTS):
        try:
            text = O.prior_record(item)
        except Exception:
            continue
        if [l for l in text.splitlines() if ".py:" in l and "rubric_h" in l]:
            out.append(f"NO_RUBRIC_COMMENTS names {item}, but §2e now finds comment "
                       f"blocks for it -- drop it from the set")
    return out


# A primitive is code in two engines. Code that has never run against a live item
# is a claim, not a capability -- and a goal retired on unit tests alone retires
# the claim. Every entry names WHY there is no live app measurement yet.
#
# The budget ratchets like the others. It must fall as the two-sided sweep
# reaches each primitive's items; an entry that outlives the sweep is a real
# defect, not a pending measurement, and must become a subgoal.
# EMPTY as of 2026-08-31. `requires` was the last entry: E15 bound it to Q6 --
# a new `link_c2` slot plus
# `requires="state_c2:link_c2:unclear|affect_c2:link_c2:unclear"` -- and it is
# EXERCISED LIVE, not merely wired. Q6 web 18/20 and cli 17/20 against a 16/20
# baseline on both sides, 6 runs each, era-checked, 0 cells never agreeing;
# out/q6_e15_cli and out/q6_e15_web. Every primitive in the registry now has an
# item that justifies it.
UNEXERCISED_PRIMITIVES: dict[str, str] = {}
UNEXERCISED_PRIMITIVES_BUDGET = _budget("UNEXERCISED_PRIMITIVES_BUDGET")


def _primitives_with_live_app_evidence() -> dict:
    """Which primitives has a LIVE APP run actually exercised?

    The app, not the python harness. `maps` is why the distinction is not
    pedantic: it had CLI evidence -- Q4b scored 16/19 through agreement.py --
    while the app could not build the sheet at all. A primitive computed
    identically by both engines can still be dead in one of them, and the CLI
    column cannot see that.
    """
    import json as _json
    import re as _re
    import pathlib as _pl

    import agreement_app as _A
    from olx_prompts import primitives as _prims

    attrs = {q["attr"] for q in _prims()["primitives"]}
    olx = [f.read_text() for f in _p7.handout_olx_paths()]
    try:
        # THROUGH `paths`, NOT THIS FILE'S POSITION. This built the
        # ledger's path independently of `measured.LEDGER`, so it would
        # have gone on reading `scoring/` after the move.
        import paths as _pth_led
        led = _json.loads(_pth_led.COURSE_LEDGER.read_text())["items"]
    except Exception:
        led = {}
    users = {a: set() for a in attrs}
    for item, J in _A.JOBS.items():
        g = J.get("grader") or ""
        if not g:
            continue
        act = g.replace("_grader", "_llm")
        for txt in olx:
            m = _re.search(r"<LLMAction[^>]*id=\"" + _re.escape(act) + r"\"[^>]*>", txt)
            if not m:
                continue
            for a in attrs:
                if a + "=" in m.group(0):
                    users[a].add(item)
    # The web record must be CURRENT, not merely present. An item can carry an
    # attribute the measurement never ran: Q6 gained `requires` on 2026-08-30 and
    # its web number dated from before the attribute existed, so this reported
    # `requires` as live-exercised on a run that could not have exercised it --
    # the exact fiction the rule was written against, arriving through the check
    # meant to enforce it. Staleness is decided the way the ledger decides it, by
    # comparing the recorded prompt fingerprint against the prompt on disk.
    def _current(item: str) -> bool:
        rec = (led.get(item) or {}).get("olx")
        if not rec:
            return False
        try:
            import measured as _M
            was = rec.get("prompt_sha")
            # THE SAME DEMOTION, THROUGH THE SAME PREDICATE. This compared
            # `prompt_sha` itself, which made it a THIRD place deciding
            # is-it-current and so a third way to get it wrong: a tag-only edit
            # made every live artifact read as history here, while
            # `_artifact_prompt_state` had already been taught the difference.
            return bool(was) and (was == _M.prompt_sha(item)
                                  or _ask_equivalent(item, "olx", was))
        except Exception:
            return False        # cannot prove it is current, so do not claim it

    return {a: sorted(i for i in its if _current(i))
            for a, its in users.items()}


# Modules that read gold RAW, on purpose, with the reason. Everything else that
# compares a prediction to gold must go through the corrected loader, the 1c
# rebuild, `scored_exactly` and the ledger's exclusions -- the accounting every
# published rate uses.
GOLD_ALPHABET_EXEMPT = {
    # Functions that read BOTH a gold-prose slot set and our slot-sheet set
    # without restricting to gold's vocabulary, on purpose. See
    # measured._gold_nameable_slots for why that restriction is normally
    # required: the two sets are drawn from different alphabets, and a slot no
    # grader phrase can name will differ EVERY time, whatever the cell says.
}


FORM_KEYED_GOLD_READERS = {
    # Sites that pick a gold loader by HANDOUT NUMBER rather than by item, which
    # is legitimate only when the handout is not being derived from an item. See
    # measured.gold_cell for the failure this table exists to bound: naming the
    # wrong handout for an item loads a real sheet, misses the row, and returns
    # `{}` -- which reads exactly like "this cell has no gold row".
    "cross_path": "iterates all three handouts; no item is in scope",
    "compare_runs": "takes the handout from the command line, alongside the item",
    "forms": "builds the per-handout config; this is where the mapping LIVES",
    "measured": "_corrected_gold IS the handout-keyed cache gold_cell derives "
                "onto, and error_profile takes its handout from _jobs()[item]",
    "enforcement": "audits the sheets themselves, one handout at a time",
    # baseline_h1 and self_graded_misses were in this table on the day it was
    # written and EXEMPTED NOTHING -- the first references only load_h1 (one
    # handout is not a pick) and the second never touches the loaders at all.
    # Found by firing the check once per entry, the same reverse pass that found
    # RAW_GOLD_READERS naming a function that had never existed. An entry that
    # excuses nothing reads as coverage and holds no line.
}


RAW_GOLD_READERS = {
    # RENAMED 2026-08-31: this entry said `check_corrections_still_match_the_sheet`,
    # which has never existed. The function is `check_corrected_gold_matches_the
    # _sheet`, and its exemption is legitimate -- it reads gold raw on purpose.
    # The name had been wrong for as long as nobody read the table, which is E31:
    # the verifier mentioned RAW_GOLD_READERS only in an error message and never
    # consulted it, so an entry naming nothing exempted nothing and read as
    # coverage. Found the day the check started being driven by the table.
    "enforcement.check_corrected_gold_matches_the_sheet":
        "audits the CORRECTIONS themselves; comparing a correction against its "
        "own output would always agree",
    "measured.gold_rows_that_do_not_reconcile":
        "audits the graders' original rows against their own comments; a "
        "corrected row would hide the row that needed correcting",
    "baseline_h1":
        "unreferenced by any script or module. Give it the canonical accounting "
        "or retire it; it is listed so it cannot quietly become someone's source "
        "of a number",
}


def check_gold_accounting_is_uniform() -> list[str]:
    """Does every prediction-vs-gold comparison use the SAME accounting?

    Four things separate a published rate from a naive comparison:
    `apply_corrected_gold`, `rebuild_declared_gold` for 1c, `scored_exactly` (which
    carries the unreachable-gold allowance), and the ledger's exclusions. A tool
    that skips any of them produces numbers that look authoritative and disagree
    with the ledger about the same artifact.

    Both known cases were live and both produced wrong published figures:

      * `measured.error_profile` omitted the 1c rebuild, so 1c read as 18
        over-credits and 78% correct when it has ZERO over-credits -- the 18 were
        three cells scored against gold the rebuild removes. That figure reached
        a corpus-wide over-credit ranking as "1c +9" before a per-cell readout
        contradicted it.
      * `cross_path.against_gold` used raw gold AND float equality AND no
        exclusions, so its "closer to gold" column counted H2's suspect cells and
        charged both paths for gold the rubric cannot reach.

    Checked by import, not by grepping source: a module that loads gold and
    compares it to a prediction must reach the corrected loader. Declared raw
    readers are listed with a reason in RAW_GOLD_READERS.
    """
    import importlib
    import inspect
    import pathlib
    import re

    CANON = (("apply_corrected_gold", "corrected gold rows"),
             ("rebuild_declared_gold", "1c's rebuilt gold"),
             ("scored_exactly", "the unreachable-gold allowance"))
    LOADER = re.compile(r"\bload_h[123]?\b")
    here = pathlib.Path(__file__).resolve().parent
    problems = []

    # PART ONE: the DECLARATIONS themselves. This is what the table is for and
    # what nothing did -- the loop below used to walk a hard-coded list of three
    # module names and mention RAW_GOLD_READERS only in its error text, so an
    # entry was never verified. It named
    # `enforcement.check_corrections_still_match_the_sheet`, which does not
    # exist; the function is `check_corrected_gold_matches_the_sheet`. The
    # exemption was legitimate and its name had been wrong for as long as nobody
    # looked. See E31.
    exempt_modules: set = set()
    for name, why in sorted(RAW_GOLD_READERS.items()):
        mod_name, _, fn_name = name.rpartition(".")
        if not mod_name:                        # a bare module, exempt entire
            exempt_modules.add(name)
            try:
                f = _p7.module_path(f"{name}.py")
            except Exception:
                f = None
            if f is None or not f.exists():
                problems.append(
                    f"RAW_GOLD_READERS declares {name} as a raw gold reader, but "
                    f"there is no {name}.py -- the module was renamed or removed "
                    f"and its exemption was not")
            elif not LOADER.search(f.read_text()):
                problems.append(
                    f"RAW_GOLD_READERS exempts {name} from the canonical gold "
                    f"accounting, but it does not load gold at all, so the "
                    f"exemption protects nothing. Drop it")
            continue
        try:
            obj = getattr(importlib.import_module(mod_name), fn_name, None)
        except Exception as exc:
            problems.append(f"RAW_GOLD_READERS declares {name}, but {mod_name} "
                            f"will not import ({type(exc).__name__})")
            continue
        if obj is None:
            problems.append(
                f"RAW_GOLD_READERS declares {name} as a raw gold reader, but "
                f"{mod_name} has no `{fn_name}` -- the function was renamed or "
                f"removed and its exemption was not. An exemption naming nothing "
                f"exempts nothing, and reads as coverage")
            continue
        try:
            src = inspect.getsource(obj)
        except Exception:
            continue
        if not LOADER.search(src):
            problems.append(
                f"RAW_GOLD_READERS exempts {name}, but it does not appear to load "
                f"gold directly. Either it reaches gold through a helper -- in "
                f"which case say so in the reason -- or the exemption is stale")
        elif "apply_corrected_gold" in src:
            problems.append(
                f"RAW_GOLD_READERS exempts {name} as a RAW reader, but it now "
                f"calls `apply_corrected_gold`. The exemption is stale: it is "
                f"using the canonical accounting and no longer needs excusing")

    # PART TWO: every CONSUMER, discovered rather than listed. The hard-coded
    # three missed four -- enforcement, handouts, baseline_h1 and gold itself --
    # so a new module comparing gold raw was invisible to this check.
    for f in sorted(here.glob("*.py")):
        src = f.read_text()
        if not LOADER.search(src):
            continue
        mod_name = f.stem
        # The module that DEFINES the loaders is the source of gold, not a
        # consumer of it: requiring `gold.py` to apply its own corrections would
        # be circular. Structural, not a declaration, so it is not in the table.
        if any(f"def {l}" in src for l in ("load_h1", "load_h2", "load_h3")):
            continue
        if mod_name in exempt_modules:
            continue
        for needed, why in CANON:
            if needed not in src:
                problems.append(
                    f"{mod_name} compares against gold but never calls "
                    f"`{needed}` -- so its numbers do not carry {why}, and will "
                    f"disagree with the ledger about the same artifact. Use the "
                    f"canonical accounting, or declare the module in "
                    f"RAW_GOLD_READERS with a reason")
    return problems


def check_closed_goals_that_changed_code_were_exercised() -> list[str]:
    """Was the code a retired goal introduced ever RUN against a live item?

    A goal that changed code and was closed on unit tests alone has retired a
    claim, not a capability. The two are indistinguishable from inside the test
    suite, which is the point: every test the code has was written by the same
    person who wrote the code, against the same understanding of what the app
    does.

    Audit subgoal 10 is the recorded case. It introduced the `maps` primitive to
    move Q4b's referent test from the model's judgement to the engine's
    arithmetic, and closed as "declaration RETIRED" on eight passing unit tests
    in maps.test.ts, a probe taught the new attribute, a clean enforcement run
    and a self-test detecting 49 of 49. Not one of those drives a cell through
    the running app. The first time a live item met the code -- the two-sided
    sweep, weeks later -- Q4b failed EVERY cell and could not be scored at all.
    The retirement was real in the rubric and fictional in the app, and the
    divergence the goal existed to close was still unmeasured.

    A closed subgoal that names a primitive in backticks is treated as
    code-inducing, since a primitive IS code in two engines. It must then carry
    an `EXERCISED:` line naming the item that ran it and where the result lives.
    Cheap to satisfy honestly and impossible to satisfy by accident, which is
    the property that matters: the failure mode here is not writing a false
    line, it is never asking the question.
    """
    import pathlib
    import re as _re

    import compose_docs

    goals = pathlib.Path(compose_docs.composed_path("GOALS.md"))
    try:
        text = goals.read_text()
    except OSError:
        return ["GOALS.md cannot be read, so closed goals cannot be checked for "
                "a live run"]

    from olx_prompts import primitives
    attrs = {p["attr"] for p in primitives()["primitives"]}
    evidence = _primitives_with_live_app_evidence()
    # Split into subgoal blocks: a marker line and everything up to the next one.
    blocks = _re.split(r"\n(?=- \[[ x]\] )", text)
    problems = []
    for b in blocks:
        head = b.split("\n", 1)[0]
        if not head.startswith("- [x]"):
            continue                      # only CLOSED goals make a claim
        named = sorted({a for a in attrs if f"`{a}`" in b})
        if not named:
            continue                      # no primitive named: not code-inducing
        if _re.search(r"^\s*EXERCISED:", b, _re.M):
            continue
        # Only a primitive with NO live app run is a problem. Naming one that
        # has already run end to end is just prose, and demanding a line for it
        # would turn the rule into bookkeeping nobody reads.
        dead = [a for a in named
                if not evidence.get(a) and a not in UNEXERCISED_PRIMITIVES]
        if not dead:
            continue
        title = head[:88]
        problems.append(
            f"{title} is CLOSED and names {', '.join(dead)}, which no live APP "
            f"run has ever exercised. Closing on unit tests alone retires a "
            f"claim, not a capability -- `maps` passed 8 unit tests and could "
            f"not score a single cell. Add `EXERCISED: <item> -- <where the "
            f"live result lives>`, declare it in UNEXERCISED_PRIMITIVES with a "
            f"reason, or reopen the goal")

    n = len(UNEXERCISED_PRIMITIVES)
    if n > UNEXERCISED_PRIMITIVES_BUDGET:
        problems.append(
            f"UNEXERCISED_PRIMITIVES holds {n} against a budget of "
            f"{UNEXERCISED_PRIMITIVES_BUDGET} -- a primitive was added without a "
            f"live app run")
    elif n < UNEXERCISED_PRIMITIVES_BUDGET:
        problems.append(
            f"UNEXERCISED_PRIMITIVES is down to {n} but the budget still says "
            f"{UNEXERCISED_PRIMITIVES_BUDGET} -- lower it to {n}, or the slack "
            f"lets an unexercised primitive in unnoticed")
    for a, why in sorted(UNEXERCISED_PRIMITIVES.items()):
        if evidence.get(a):
            problems.append(
                f"UNEXERCISED_PRIMITIVES still lists `{a}` (\"{why[:60]}...\") but "
                f"{evidence[a][0]} has now measured it live on the app -- drop the "
                f"entry and lower the budget, or the table stops meaning anything")
    return problems


def check_convertible_prose_rules_have_subgoals() -> list[str]:
    """Does every CONVERTIBLE prose rule have a subgoal, or just a label?

    The registry's second job is to be a WORK LIST, and a work list whose items
    live only in a comment is a list nobody works. So the rule, set on 2026-08-28:
    a PROSE_ONLY_SLOTS entry whose reason says CONVERTIBLE becomes a subgoal under
    the equivalence goal, and this fails the audit until it is one.

    It looks for `ITEM.slot` or `` `slot` `` alongside the item id in GOALS.md,
    which is loose on purpose -- the check exists to make sure the work was
    WRITTEN DOWN, not to police how a subgoal is phrased. A stricter match would
    fail on the first reworded heading and teach people to route around it.
    """
    import pathlib

    import compose_docs

    goals = pathlib.Path(compose_docs.composed_path("GOALS.md"))
    try:
        text = goals.read_text()
    except OSError as e:
        return [f"GOALS.md cannot be read, so CONVERTIBLE prose rules cannot be "
                f"checked: {e}"]

    out = []
    for (item, slot), why in sorted(PROSE_ONLY_SLOTS.items()):
        if "CONVERTIBLE" not in why or why.strip().startswith("NOT CONVERTIBLE"):
            continue
        named = f"{item}.{slot}" in text or (f"`{slot}`" in text and item in text)
        if not named:
            out.append(f"PROSE_ONLY_SLOTS marks {item}.{slot} CONVERTIBLE but no "
                       f"subgoal in GOALS.md names it. A convertible rule is work, "
                       f"not a label: add it as a subgoal under the equivalence "
                       f"goal, or change the reason to argue why it cannot convert")
    return out


def check_prose_only_slots_are_declared() -> list[str]:
    """Is the prose channel's surface known, and is it growing?

    THE LIST HAS THREE JOBS, and they are why it is enforced rather than filed.
    It GATES authoring: a new per-slot rule that nothing computes fails this check
    until someone either expresses it as a primitive -- which the enforcement audit
    can then compare between the two scorers -- or declares here why it cannot be
    one. It is a WORK LIST: entries marked CONVERTIBLE are the ones to turn into
    declarations, and the budget falls as they go, exactly as HANDCODED_BUDGET
    does. And it makes a sweep divergence ATTRIBUTABLE: `cross_path.py --slots`
    prints each divergent slot's basis, so prose-and-declared, prose-and-new, and
    different-arithmetic stop looking alike.

    Unlike HANDCODED_BUDGET this does not target zero. Q6's "does it state HOW"
    and 1a's arc-not-label coverage have no operands to compare; the honest end
    state is that every remaining entry argues, in its reason, why it cannot be a
    primitive.

    Three ways to fail. A slot carrying a rule that nothing computes and that is
    NOT declared -- the surface grew and nobody decided. A declaration naming a
    slot that no longer qualifies -- it was converted to a primitive, or its rule
    was removed, and the list is rotting. And the count against its budget.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K: python reads which slots are
    # judged by a per-slot `rule` and by nothing computable;
    # `enforce/proseOnlySlots.ts` does the three-way comparison and the ratchet.
    #
    # PROVEN WITH A CONTROL: with the declarations stripped, both sides reported
    # the SAME 28 findings in the same order.
    # SELF-ASSEMBLED. Subgoal E63: the runner builds this payload itself,
    # from the same course records python would have read. The assembler was
    # compared against the payload python used to send and found IDENTICAL
    # before this fetch was deleted; `runner.SELF_ASSEMBLING` names the rules
    # that comparison has cleared, and the runner refuses any other.
    import lo_enforce

    return lo_enforce.run("prose_only_slots_are_declared", None)



def check_artifacts_record_their_era() -> list[str]:
    """Does every artifact writer stamp WHAT IT RAN AGAINST?

    A sweep's .json used to say what it scored and never what it scored against,
    so two directories could be told apart only by file mtime -- which is not a
    version. That made prompt version indistinguishable from scoring path, and it
    cost a real answer: the first cross-path scoping found 18 cells diverging in
    both of two comparisons and 17 in only one, and those 17 could not be
    attributed to version or to path, because nothing recorded which prompt each
    run used.

    So all three writers stamp `era` from measured.era_stamp, and this asserts
    they still do. It reads the SOURCE rather than the artifacts on disk: the
    corpus is full of legitimately unstamped older runs, and flagging those would
    be thousands of findings about the past instead of one about the code.
    """
    out = []
    for fname, what in ARTIFACT_WRITERS:
        try:
            src = _p7.module_source(fname)        # wherever it lives; see paths
        except OSError as e:
            out.append(f"{fname} ({what}) cannot be read, so its era stamp "
                       f"cannot be checked: {e}")
            continue
        if "era_stamp" not in src:
            out.append(f"{fname} ({what}) does not call measured.era_stamp -- the "
                       f"artifacts it writes will not say which prompt they ran "
                       f"against, and cross_path.py cannot then tell a version "
                       f"difference from a path difference")
        elif '"era"' not in src:
            out.append(f"{fname} ({what}) computes an era stamp but does not write "
                       f"it under the `era` key that cross_path.py reads")
    return out


def check_slot_rules_backlog_is_being_cleared() -> list[str]:
    """Is the olx-only slot-rule backlog shrinking, or accumulating?

    Every entry is a rule two scorers apply and a third does not. `--prompts`
    counts only rubric elements the WEB is missing and has no notion of the web
    carrying something the paper scorer does not, so nothing else in the audit
    objects to this list growing.

    Two-sided, like HANDCODED_BUDGET. Over budget means an entry was added. Under
    budget means one was migrated and the ceiling was not lowered, which leaves
    room for a replacement to arrive unnoticed.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K. Same ratchet, different noun --
    # see `check_handcoded_rules_are_being_cleared`.
    import lo_enforce

    return lo_enforce.run("ratchets_only_tighten", {"ratchets": [{
        "table": "SLOT_RULE_BACKLOG", "budgetName": "SLOT_RULE_BACKLOG_BUDGET",
        "count": len(SLOT_RULE_BACKLOG), "budget": SLOT_RULE_BACKLOG_BUDGET,
        "unit": "olx-only slot rule",
        "advice": "Put the text in the credit component's `rule` field, which "
                  "both generators render, rather than in SLOT_NOTES, which the "
                  "paper scorer never sees",
    }]})



def _note_reaches(note: str, prompt: str) -> bool:
    """Is `note`'s text present in `prompt`, allowing for placeholder filling?

    A head-match is NOT good enough and the false answers it gave are on the
    record: it reported Q1's `benefits_failing` and DAY1's `consequence_asserted`
    as missing from prompts that carry them in full, because each generator
    prefixes the text differently. Match on the note's own literal SEGMENTS
    instead -- the spans between `{fail}`-style placeholders, which each side
    fills with its own vocabulary -- so what is compared is the wording neither
    generator is free to change.
    """
    import re

    norm = lambda s: " ".join(s.split())
    hay = norm(prompt)
    segs = [norm(s) for s in re.split(r"\{[^}]*\}", note)]
    segs = [s for s in segs if len(s) >= 40]
    if not segs:                     # a short note, or all placeholder
        segs = [norm(note)]
    return all(s in hay for s in segs)


def check_slot_rules_reach_both_prompts() -> list[str]:
    """Does per-slot judging text reach the PAPER prompt as well as the web's?

    The web checklist and the paper component list are each a slot-specific
    field, and only the rubric is read by both generators. Text parked in
    `olx_prompts.SLOT_NOTES` used to reach the web and the CLI harness and
    silently leave score.py behind — the two sides going on applying different
    rules while every existing audit stayed green, because `--prompts` only ever
    counts rubric elements the WEB is MISSING. It has no notion of the web
    carrying something the paper does not.

    That is not hypothetical. Q4b's five substitution tests lived in SLOT_NOTES
    for a day: the web and CLI moved from 69% to 88% on them and the paper
    scorer never saw them, with `--item Q4b` reporting "missing 0/4, 0/5, 0/3".

    THIS CHECK MEASURES REACH; IT USED TO MEASURE LOCATION. Until 2026-09-09 it
    asked "is this text in SLOT_NOTES?" and called that a gap, because SLOT_NOTES
    was olx-only and the two questions had the same answer. They no longer do:
    score.py's `_slot_body` now reads SLOT_NOTES through the same
    `rule or SLOT_NOTES[item:key] or SLOT_NOTES[key] or desc` chain the web uses,
    so text can sit in SLOT_NOTES and reach both prompts. A location check would
    have gone on reporting six migrations as owed after they were delivered, and
    -- worse in the other direction -- it never saw Q6's four `state_*` notes at
    all, which were real judging text that reached only the web while sitting
    below the mapping-length threshold. Build both prompts and look.

    Both directions are findings. A note the PAPER carries and the web does not
    is the same defect wearing the other hat, and neither generator is the
    privileged one.

    Mapping notes are exempt. SLOT_NOTES' documented job is to point a web check
    at its numbered paper criterion, and such a note carries no judging text of
    its own — it is short and refers to a criterion. The heuristic is length,
    which is crude but errs the right way: a long note is doing more than
    mapping. It is the reason Q6's four were invisible here, so it buys its
    exemption at a known price.
    """
    import olx_prompts as OP
    rubric_h1, rubric_h2, rubric_h3 = _rubric_views()
    import score as SC

    MAPPING_MAX = 220        # a "see criterion N" pointer, not a rule
    BACKLOG = SLOT_RULE_BACKLOG

    problems = []
    scored, by_id = {}, {}
    for mod in (rubric_h1, rubric_h2, rubric_h3):
        for item in mod.ITEMS:
            by_id[item["id"]] = item
            for c in item.get("credit", []) or []:
                scored.setdefault(item["id"], set()).add(c["what"])

    built: dict[str, tuple] = {}

    # A BUILD FAILURE IS A FINDING, NOT A HAYSTACK. The first run of this check
    # passed the item DICT to build_web_prompt, which takes an id; the exception
    # was caught and its text used as the prompt to search, so every entry came
    # back "paper only" or "dead text" and all four lines were reports on the
    # bug. Failures are collected and raised as their own problems.
    failed: list[str] = []

    def prompts(item_id):
        if item_id not in built:
            item = by_id[item_id]
            try:
                web = OP.build_web_prompt(item_id)
            except Exception as exc:
                web, _ = None, failed.append(
                    f"{item_id}: the WEB prompt does not build ({type(exc).__name__}: "
                    f"{exc}), so no reach can be measured on it")
            try:
                paper = SC.build_prompt(item, "STUDENT RESPONSE", {}, None)
            except Exception as exc:
                paper, _ = None, failed.append(
                    f"{item_id}: the PAPER prompt does not build ({type(exc).__name__}: "
                    f"{exc}), so no reach can be measured on it")
            built[item_id] = (web, paper)
        return built[item_id]

    seen_backlog = set()
    for key, note in sorted((getattr(OP, "SLOT_NOTES", {}) or {}).items()):
        if len(note) <= MAPPING_MAX:
            continue
        item_id, _, slot = key.partition(":")
        if not slot:                       # unscoped note, applies by slot name
            item_id, slot = None, key
        # The keys the criteria machinery renders IN ITS OWN WORDS, via
        # `_criterion_11` and `_C10_TRIGGER`. A verbatim reach test cannot see a
        # paraphrase, and fuzzy matching here would be a guess machine: this is
        # what olx_prompts.CLI_CRITERIA_NOTES declares, and reading it is how the
        # exception stays in one place.
        if slot in getattr(OP, "CLI_CRITERIA_NOTES", ()):
            continue
        owners = ([item_id] if item_id and item_id in scored
                  else [i for i, s in scored.items() if slot in s])
        if not owners:
            continue                       # not a scored slot — nothing to share

        short = []
        for owner in sorted(owners):
            web, paper = prompts(owner)
            if web is None or paper is None:
                continue               # reported by `failed`, not guessed at
            in_web = _note_reaches(note, web)
            in_paper = _note_reaches(note, paper)
            if in_web and in_paper:
                continue
            if in_web:
                short.append(f"{owner}: web only, paper scorer never sees it")
            elif in_paper:
                short.append(f"{owner}: paper only, the web never sees it")
            else:
                short.append(f"{owner}: NEITHER prompt carries it — dead text")
        if not short:
            if key in BACKLOG:
                problems.append(
                    f"BACKLOG names SLOT_NOTES[{key!r}], which now reaches BOTH "
                    f"prompts on every item that scores it. Drop it from BACKLOG")
            continue
        if key in BACKLOG:
            seen_backlog.add(key)
            continue
        problems.append(
            f"SLOT_NOTES[{key!r}] is {len(note)} chars of judging text on a scored "
            f"slot, and it does not reach both prompts — {'; '.join(short)}. Put it "
            f"on that credit component's `rule` field, which both generators "
            f"render, or declare it in SLOT_RULE_BACKLOG with the reason")

    # A backlog entry that has gone means the list is rotting: either it was
    # migrated (good — remove it from BACKLOG) or its note shrank below the
    # mapping threshold (also worth knowing).
    for stale in sorted(set(BACKLOG) - seen_backlog):
        if any(stale in p for p in problems):
            continue                       # already reported as reaching both
        problems.append(
            f"BACKLOG names SLOT_NOTES[{stale!r}], which no longer qualifies. If it "
            f"was migrated to a `rule` field, drop it from BACKLOG")
    return sorted(set(failed)) + problems


def _olx_slot_verdicts(item_id: str, slot: str):
    """Verdicts the OLX slot spec declares for this slot, e.g. `key:label:fail@2`.

    RETURNS `None` WHEN THE SLOT IS NOT FOUND, a set when it is -- and the empty
    set is a real answer meaning "this slot offers met/absent and nothing else".

    THE TWO WERE ONE VALUE UNTIL E63, 2026-09-25, and the conflation quietly
    reintroduced the fault subgoal E52 exists to stop. Its caller wrote
    `sorted({"met","absent"} | extra) if extra else None`, so a slot offering
    only the defaults sent `offered: null`, and the rule then falls back to the
    RUBRIC's verdict list -- which is exactly what E52 records as having "let
    the exact fault this check was built for survive a whole sweep". The sheet
    is the authority; an empty extras set is the sheet SPEAKING, not the sheet
    being unreadable.

    One mapped slot is affected today (`Q2/wgb_inverts_utb`), and its rubric
    list happens to equal the sheet's defaults, so nothing was misreported --
    the defect was latent, waiting for a slot where the two differ.
    """
    import re as _re
    import pathlib as _pl

    import agreement_app as _A

    J = _A.JOBS.get(item_id) or {}
    g = J.get("grader") or ""
    if not g:
        return set()
    act = g.replace("_grader", "_llm")
    for f in _p7.handout_olx_paths():
        txt = f.read_text()
        m = _re.search(r"<LLMAction\b(?:(?!</?LLMAction)[^>])*?(?:^|\s)id=\"" +
                       _re.escape(act) + r"\"(?:(?!</?LLMAction)[^>])*>", txt, _re.S)
        if not m:
            continue
        sm = _re.search(r'slots="([^"]*)"', m.group(0), _re.S)
        for part in (sm.group(1).split("|") if sm else []):
            bits = part.split(":")
            if bits[0].lstrip("!").strip() != slot:
                continue
            out = set()
            for b in bits[2:]:
                for tok in b.split("/"):
                    out.add(_re.sub(r"@[0-9.]+$", "", tok).strip())
            return {o for o in out if o}          # may be empty: it SPOKE
    return None                                   # the slot was never found


def check_prompt_prose_names_only_offered_verdicts() -> list[str]:
    """Does any prompt prose tell the model to answer a verdict its slot lacks?

    `check_slot_rules_are_vocabulary_neutral` polices the rubric's shared `rule`,
    where the answer is `{fail}`. But `rule` is not the only source of prompt
    prose: SLOT_NOTES is a SECOND one, olx-only, and it gets no substitution. So
    the guard covered one source and the other went unwatched, which is how
    Q5:example_2 sat in the live web prompt naming `not_reason` -- a token from
    the RUBRIC's vocabulary -- while its sheet offered `wrong_kind`. The test was
    inert: the model was asked for a token it could not return, so the
    distinction the note existed to draw was never drawn. It dated to the
    original import and was found by reading, not by any check.

    BACKLOG.md:94 recorded it and named two fixes: put `{fail}` in the note, or
    lint the class. This is the lint, which is the one that closes it -- the note
    itself has since migrated to `rule`, but nothing stopped the next one.

    Two things this must get right, both of which a naive version gets wrong:

    * `pick(NAME)` options live in the sheet's `choices=` map, not in the slot
      spec. Without resolving them, D1/D2:named_type read as naming `unclear`
      against a slot offering only met/absent -- two false positives on prose
      that is correct, since `operant_or_unclear` is `PR,NR,PP,NP,unclear`.
    * A GLOBAL note reaches a slot only when that slot has no `rule` and no
      item-scoped note, so the precedence here mirrors the generator's at the
      emit site rather than assuming every note reaches every matching slot.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K. Python resolves the four views
    # this needs -- the sheet's slots, its `choices=` map, SLOT_NOTES and the
    # rubric's credit list -- because those are still python-side readers; the
    # JUDGEMENT is `enforce/offeredVerdicts.ts`, where vitest holds both of the
    # cases a naive version gets wrong: a `pick(NAME)` group supplying the
    # verdict, and a `rule` slot that belongs to a different check.
    # SELF-ASSEMBLED. E63: this was `NATIVE_BLOCKED` on the grounds that
    # porting the verdict vocabulary would make a third copy -- which
    # stopped being true when `verdictVocabulary.ts` became the single
    # source and this side started reading it. The assembler builds the
    # same 217 slots; proven on firing data, not on a clean tree.
    import lo_enforce

    # PYTHON OWNS THE NOTES, AND ONLY THE NOTES. Self-assembly rebuilt the whole
    # payload from disk, and the self-test injects by appending a sentence to the
    # IN-MEMORY `olx_prompts.SLOT_NOTES` -- so the case went silent. Measured
    # 2026-09-26: before=0, after=0.
    #
    # ASKING FOR THE PAYLOAD AND PATCHING ONE FIELD, rather than rebuilding it
    # here. Rebuilding would restore in python the slot-sheet reading this port
    # removed -- the duplicate implementation the whole goal exists to end. The
    # `assemble` probe hands back what the assembler built; this replaces the
    # single field python holds and sends it back, so the assembler stays the
    # one definition of the payload's shape and the seam is one line long.
    #
    # THE RESOLUTION IS THE ASSEMBLER'S: `item:key`, then bare `key`, then none.
    # Checked before relying on it -- python reproduces the assembler's `note`
    # on all 217 slots.
    import coursedata as _cd_pp
    import lo_enforce
    import olx_prompts as _O_pp

    try:
        payload = lo_enforce.probe(
            "assemble", {"rule": "prompt_prose_names_only_offered_verdicts",
                         "ns": _cd_pp.course_id()})
    except Exception as exc:
        return [f"the prompt-prose payload could not be assembled: "
                f"{type(exc).__name__}: {exc}"]
    notes = _O_pp.SLOT_NOTES
    for s in payload.get("slots") or []:
        s["note"] = (notes.get(f"{s['item']}:{s['key']}")
                     or notes.get(s["key"]) or None)
    return lo_enforce.run("prompt_prose_names_only_offered_verdicts", payload)



# The two scorers' verdict SPACES differ on 48 slots, and they differ in a small
# number of SHAPES. Declared by shape rather than per slot: 48 entries would be
# mostly noise, and what is worth catching is a NEW kind of asymmetry appearing,
# not the 17th instance of one already understood.
#
# Filed 2026-08-30 under E27, after `unclear` was found exempted corpus-wide by
# SHARED_EXTRAS while the two sides disagree about it on seventeen slots. That
# hole is closed in the neutrality check; this table is the other half -- the
# asymmetries themselves, written down, so a new one has to be looked at.
#
# Key: (frozenset olx-only tokens, frozenset paper-only tokens) -> why.
# MOVED TO THE RECORDS 2026-09-25. Which verdict-space asymmetries this
# COURSE has declared is course data, and while the table lived here the
# two rules that read it could be run from python and from nowhere else.
# Its keys are tuples of FROZENSETS, which the records already carry via
# `__frozenset__` -- the same tagging gold uses.
VERDICT_SPACE_DIVERGENCES = _declaration("VERDICT_SPACE_DIVERGENCES")


def check_verdict_spaces_are_declared() -> list[str]:
    """Does any slot's two verdict spaces differ in an UNDECLARED shape?

    The neutrality check stops a shared `rule` naming a token one side lacks.
    This is the other half: the asymmetries themselves, so a new one is looked at
    rather than absorbed. Declared by SHAPE -- (olx-only, paper-only) -- because
    the same asymmetry recurs across many slots and 48 per-slot entries would
    read as coverage while enforcing nothing.

    A slot the web does not carry is skipped, not reported: paper-only checks are
    a different kind of difference and have their own declarations.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K: python fetches both spaces --
    # the web's from the shipped SHEET, the paper side's from the rubric -- and
    # `enforce/verdictSpaces.ts` compares them. Declared BY SHAPE, so one entry
    # covers every slot that differs in exactly that way.
    #
    # PROVEN WITH A CONTROL: the live corpus is clean, so agreement there proves
    # nothing. With the declarations stripped, both sides reported the SAME 44
    # findings in the same order.
    # SELF-ASSEMBLED. Subgoal E63: the runner builds this payload, and the
    # assembler was proven to build what python built -- payload-identical, or
    # order-only with the finding SET shown unchanged on data mutated until
    # the rule fires. `runner.SELF_ASSEMBLING` is that cleared list.
    import lo_enforce

    return lo_enforce.run("verdict_spaces_are_declared", None)



def _web_slot_options(item_id: str, key: str) -> set | None:
    """What the WEB sheet offers for one slot, `pick(NAME)` enums resolved.

    None when the item has no action or the slot is not on the sheet -- a slot
    that exists only on the rubric side cannot be compared, and reporting it as
    a mismatch would flag every paper-only check.
    """
    import olx_prompts as O
    form, action = O.FORM.get(item_id), O.ACTION.get(item_id)
    if form is None or action is None:
        return None
    try:
        spec, defaults = O._slots_attr(form, action)
        choices = O._choices_attr(form, action)
        slots = O.parse_slots(spec, defaults)
    except Exception:
        return None
    for s in slots:
        if s["key"] == key:
            opts = set(s["options"] or ()) | {"met", "absent"}
            if s.get("picks") is not None:
                opts |= set(choices.get(s["picks"], []) or ())
            return opts
    return None


def check_slot_rules_are_vocabulary_neutral() -> list[str]:
    """Does any shared `rule` name a verdict token literally?

    A `rule` is rendered into BOTH prompts, and the two sides do not share a
    verdict vocabulary: on Q5's example slots the web sheet says `wrong_kind`
    where the rubric says `not_reason`, and on 1c's legend `incomplete` against
    `not_described`. So a rule that names one side's token is unreadable on the
    other — and unreadable in the worst way, because it still looks like an
    instruction.

    ALIAS does NOT record those pairs. It maps slot KEY names (`behavior` ->
    `names_behavior`) and contains no verdict token at all; two comments claimed
    it was the verdict bridge, which sent a reader looking for something that has
    never existed. The bridge is `{fail}`, resolved per side at render time.

    That is not hypothetical either. Q4b's five substitution tests were written
    while they lived in SLOT_NOTES, where `wrong_kind` is correct, and moving
    them to the shared field carried that token into the paper prompt. Opus was
    told when to answer `wrong_kind` while being offered met/absent/not_active,
    so every test was inert: it credited p8's "{{corpus:Q4b/p8:first:53:79:sha=824d9f001c44}} gym"
    that the web and CLI both reject, and scored 5.00 against a gold of 2.00.
    Three runs reproduced it exactly, so it read as a stable model difference
    rather than a broken prompt.

    Rules must therefore use the `{fail}` placeholder, which each generator
    fills with the verdict IT offers. This checks for the literal tokens.
    """
    # A rule naming a literal verdict instructs one side about a token it cannot
    # emit.
    # PYTHON KEEPS THE FETCH. The self-test injects by rewriting a credit
    # entry's `rule` IN MEMORY -- it replaces `{fail}` with a literal verdict --
    # and forks. A payload the runner rebuilds from the rubric FILE cannot see
    # that: measured 2026-09-26, before=0 and after=0 on the case's own
    # injection. `tools/injection_reach.py` is the standing guard for this.
    #
    # The assembler stays for callers inside lo-blocks; the runner reaches it
    # only when the payload is null, which python no longer sends.
    from forms import config
    from slot_vocab import known_verdicts

    import lo_enforce

    slots = []
    for h in _forms():
        for item in config(h)["rubric"].ITEMS:
            for c in item.get("credit") or []:
                if not c.get("rule"):
                    continue
                paper = (set(c.get("verdicts") or [])
                         | set((c.get("codes") or {}).keys())
                         | {"met", "absent"})
                for grp in item.get("cover") or []:
                    if c["what"] in (grp.get("keys") or ()):
                        paper |= set(grp.get("verdicts") or ())
                web = _web_slot_options(item["id"], c["what"])
                slots.append({
                    "form": h, "item": item["id"], "what": c["what"],
                    "rule": c["rule"],
                    "offeredPaper": sorted(paper),
                    "offeredWeb": None if web is None else sorted(web),
                })
    return lo_enforce.run("slot_rules_are_vocabulary_neutral",
                          {"slots": slots, "known": list(known_verdicts())})


def check_rule_fail_tokens_agree() -> list[str]:
    """Do the two generators fill `{fail}` with tokens that mean the same thing?

    The sibling check above stops a rule NAMING one side's token. This one
    covers the other half of the same hazard: the rule is correctly written
    with `{fail}`, both prompts render, every existing audit stays green — and
    the two sides are nevertheless told to answer differently, because the
    substitution itself diverged.

    Not hypothetical. Q6's `state_c1`/`state_c2` take their vocabulary from
    their `cover` group (an IDENTITY — first/second/neither/absent) rather than
    from a `verdicts` list on the credit entry, and score.py read only the
    credit entry. So a rule about the box naming the WRONG consequence reached
    the web as `mismatch` and the paper scorer as `absent` — "the box was
    empty" — which is a different finding, and one the response it is about
    plainly contradicts.

    Two invariants, both cheap:
      1. Each side's token must be a verdict THAT side actually offers for the
         slot. A token outside the vocabulary is uninterpretable.
      2. Neither side may fall back to the generic `absent` while the other
         substitutes a specific extra. `absent` means nothing was written;
         every extra means something was written and is wrong. They can never
         be the same instruction.
    """
    rubric_h1, rubric_h2, rubric_h3 = _rubric_views()
    import olx_prompts as O
    from score import _fail_verdict

    problems = []
    for h, mod in ((1, rubric_h1), (2, rubric_h2), (3, rubric_h3)):
        for item in mod.ITEMS:
            action = O.ACTION.get(item["id"])
            if not action:
                continue               # no <LLMAction>: nothing to compare against
            web_opts = {s["key"]: (s.get("options") or [])
                        for s in O.parse_slots(*O._slots_attr(h, action))}
            for c in item.get("credit", []) or []:
                if not c.get("rule") or "{fail}" not in c["rule"]:
                    continue
                slot = c["what"]
                opts = web_opts.get(slot)
                if opts is None:
                    continue           # computed/derived slot, not on the sheet
                extras = [o for o in opts if o not in ("met", "absent")]
                web = extras[0] if extras else "absent"
                paper = _fail_verdict(item, c)

                where = f"H{h} {item['id']}.{slot}"
                if paper not in _rubric_vocab(item, c):
                    problems.append(
                        f"{where}: `rule` renders {paper!r} into the paper prompt, "
                        f"which is not a verdict that slot offers there")
                if ("absent" in (web, paper)) and web != paper:
                    problems.append(
                        f"{where}: `{{fail}}` becomes {web!r} on the web and "
                        f"{paper!r} on paper. One side is being told the box was "
                        f"left empty and the other that its content is wrong — "
                        f"the same rule, firing on different evidence")
    return problems


_CORPUS_MEMO: dict[tuple[str, int], str] | None = None


def _corpus_cells() -> dict[tuple[str, int], str]:
    """{(item_id, pid): the student's text for that cell}, normalised.

    A seam, like `_handsplit_tables`: the selftest replaces it so the check
    below can be proved to still fire. Empty when the corpus is absent — it
    lives outside this repo and most machines will not have it.
    """
    import warnings

    # Memoised: the selftest runs the whole audit once per injected breakage, and
    # rebuilding 520 fixtures each time turned a fast check into five minutes.
    global _CORPUS_MEMO
    if _CORPUS_MEMO is not None:
        return _CORPUS_MEMO

    out: dict[tuple[str, int], str] = {}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            from agreement import fixture_for
            import forms as H
            for h in _forms():
                for item in H.config(h)["rubric"].ITEMS:
                    for pid in range(1, 21):
                        try:
                            fx = fixture_for(item["id"], pid)
                        except Exception:
                            continue
                        # SORTED BY FIELD, so the join is reproducible. It
                        # was dict order, which is the insertion order of
                        # whatever built the fixture -- fine while one reader
                        # existed, and a silent divergence the moment a second
                        # reads the same cells from a record whose keys are
                        # sorted. The joins are where grams cross a box
                        # boundary, so the order decides which 6-grams exist.
                        out[(item["id"], pid)] = _norm(
                            " ".join(str(fx[k]) for k in sorted(fx)))
    except Exception:
        _CORPUS_MEMO = {}
        return _CORPUS_MEMO            # corpus absent — nothing to check against
    _CORPUS_MEMO = out
    return out


def _norm(s: str) -> str:
    """Lowercased, whitespace-collapsed, punctuation removed.

    Punctuation is STRIPPED, not merely folded, and that matters more than it
    looks. `_grams` tokenises on whitespace, so a comma or a quote mark rides
    along on the word it touches. A worked example in a prompt is always written
    inside quotation marks — that is what makes it an example — so its first and
    last tokens were `"i` and `friday"`, matching nothing in a student's answer,
    and any interior comma broke the run again. An 8-gram could only land if it
    threaded between both ends and every mark in between.

    So `check_rule_examples_are_not_corpus` was close to blind to the one thing
    it exists to catch. WK1's agent rule quoted WK1/p1's answer word for word,
    p1 was counted on that item, and the check passed at every commit.

    Intra-word apostrophes survive, so "don't" stays one token.
    """
    s = s.lower().replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"').replace("—", "-")
    s = re.sub(r"[^a-z0-9' ]+", " ", s)
    s = re.sub(r"(^|\s)'+|'+(\s|$)", " ", s)
    return " ".join(s.split())


# Prompts that quote a COUNTED participant's own words without attribution, as
# found the day `check_rule_examples_are_not_corpus` landed. Declared, not fixed:
# each one needs its example rewritten and the item re-measured, and doing that
# to seventeen items in one change would make every number in the project move
# at once for reasons nobody could separate. Same treatment as the SLOT_NOTES
# BACKLOG above, and with the same rule attached — an entry that stops firing
# must be REMOVED, so the list cannot quietly outlive the problem.
#
# The point of declaring them is that a NEW leak fails immediately. The one that
# prompted the check was written this session, into Q6's `affect_c*` rule, and
# would have sat here unnoticed among the others.
# AUTHORED IN `declaration_source.py` and exported, so the engine can read it.
# It was a bare `set()` here, which left a native caller nothing to consult.
CORPUS_QUOTE_BACKLOG: set = {tuple(p) for p in
                             _declaration_list("CORPUS_QUOTE_BACKLOG")}
# (
    # Empty. All 21 entries were the same mistake, made 21 times: a rule
    # illustrated with a counted student's own words, so the prompt handed the
    # model the answer to a cell still in the denominator. 2a's bullet was the
    # extreme — it quoted two answers and attached the grade ("was scored 6/6"),
    # and p20 shared THIRTY distinct 8-word runs with it.
    #
    # Each was rewritten to abstract the pattern and keep the deduction: "ADDING
    # a privilege for staying within a limit is PR, not NR (-2)" in place of the
    # student sentence that made the point. What the guidance loses is the
    # ability to say "the graders credited THIS"; what it keeps is the shape they
    # credited, which is the part that generalises.
    #
    # The alternative — registering all 21 in `cited_participants` and excluding
    # them — was priced and rejected: 21 cells out of the denominator, and NR
    # alone would have dropped from 18 counted cells to 14.
# )



# Length of the shared run that counts as a quotation. Was 8, which on a
# cleaned tree finds NOTHING while n=6 still finds four genuine leaks: an
# 8-word run has to survive both ends of the quotation marks and every comma
# in between. Measured on this corpus, the knee is at 6 — n=5 starts admitting
# handout vocabulary ("the end of the week", "{{corpus:Q1/p10:response:0:31:sha=f748d9d9ddd6:shape=C1}}")
# that happens to appear in only one student's answer for an item, and n=4 is
# unusable at 39 hits. Two filters keep 6 honest: a run appearing in MORE THAN
# ONE student's answer is the assignment talking, and a run appearing in the
# ITEM'S OWN QUESTION is the student quoting the form back at us.
_QUOTE_N = 6


def _grams(text: str, n: int = _QUOTE_N) -> set[tuple[str, ...]]:
    w = text.split()
    return {tuple(w[i:i + n]) for i in range(len(w) - n + 1)}


def check_rule_examples_are_not_corpus() -> list[str]:
    """Does any prompt reproduce a student's own words without declaring it?

    `check_citations_match_exclusions` polices citations that name a participant
    BY NUMBER, because those are what `cited_participants` can record. It cannot
    see an UNATTRIBUTED reproduction — and that gives the answer away just as
    completely while leaving the cell in the counted denominator.

    Not hypothetical. The mechanism rule written for Q6's `affect_c*` slots
    illustrated its test with a positive example lifted verbatim from p14, a
    counted cell scoring exact. Both examples were written from the evidence
    while reading it, which is how it will happen again.

    Method: an 8-word sequence shared between an item's prompt and one
    participant's answer to that item. Two filters keep it honest. A sequence
    that appears in MORE THAN ONE student's answer is the assignment's own
    language — "baseline data collection and three weeks of intervention" is the
    handout talking, not a student — so only sequences unique to one answer
    count. And a participant already excluded on that item is declared, which is
    what `exemplars` and `cited_participants` are for.

    What it CANNOT catch, stated plainly so nobody trusts it too far: a
    PARAPHRASE. The other half of the same Q6 mistake described p15's answer in
    different words while naming p15's own 4c and the verdict, which is a
    complete answer key and shares no 8-word run with anything. This check is a
    floor, not a guarantee — writing examples from a participant's answer is
    still the thing not to do.
    """
    # PORTED to `enforce/ruleExamplesNotCorpus.ts` (goal K).
    #
    # PYTHON KEEPS THE FETCH: `_corpus_cells` is a SEAM the self-test replaces
    # to prove this still fires, and a payload rebuilt from the record would not
    # see the substitution.
    #
    # IT READS THE RECORD NOW. The corpus comes from `derived/responses/`, so no
    # submission is opened on either side; the prompt text comes from the rubric
    # and the slot notes, both of which the engine already parses.
    import forms as H
    import lo_enforce
    import olx_prompts as O

    corpus: dict[str, dict[str, str]] = {}
    for (iid, pid), body in _corpus_cells().items():
        corpus.setdefault(iid, {})[str(pid)] = body

    items = []
    for h in _forms():
        for item in H.config(h)["rubric"].ITEMS:
            iid = item["id"]
            # Prompt-bearing text, MINUS the worked examples: an item's
            # `exemplars` field reproduces whole answers on purpose, and those
            # participants are registered and excluded.
            guidance = item.get("guidance") or ""
            parts = list(guidance) if isinstance(guidance, list) else [guidance]
            for c in item.get("credit", []) or []:
                parts += [c.get("desc") or "", c.get("rule") or ""]
            for key, note in O.SLOT_NOTES.items():
                owner, _, slot = key.partition(":")
                if not slot or owner == iid:
                    parts.append(note)
            items.append({"h": h, "id": iid, "parts": parts,
                          "question": str(item.get("question") or ""),
                          "excluded": sorted(H.cell_exclusions(h, iid))})

    return lo_enforce.run("rule_examples_are_not_corpus", {
        "corpus": corpus, "items": items,
        "backlog": sorted(f"{i}|{p}" for i, p in CORPUS_QUOTE_BACKLOG),
    })


def _attr(form: int, item_id: str, attr: str) -> str:
    """One sheet attribute, or "" — the reader the slot guard needs."""
    import re
    import olx_prompts as O
    m = re.search(r'\b%s="([^"]*)"' % attr, O._sheet_tag(form, O.ACTION[item_id]))
    return m.group(1) if m else ""


def _prose_source_of_the_scorer() -> list[str]:
    """The same two rules, applied where the composing call actually lives.

    A scorer composing its own section must still SOURCE the prose from
    `_criteria_section` and hold no block of authored text of its own. Reading
    the RESOLVED scorer rather than a fixed path keeps this working for a course
    that ships its own.
    """
    import ast
    import inspect

    import scorers

    oc = scorers.optional("oc")
    if oc is None or not hasattr(oc, "prompt_section"):
        return ["the resolved scorer has no prompt_section, so the criteria "
                "prose has no traceable source -- retarget this check"]
    try:
        tree = ast.parse(inspect.getsource(oc.prompt_section))
    except Exception as exc:                        # pragma: no cover
        return [f"the scorer's prompt_section cannot be read: {exc}"]
    calls = {ast.unparse(n.func) for n in ast.walk(tree) if isinstance(n, ast.Call)}
    bad = []
    if not any("_criteria_section" in c for c in calls):
        bad.append("the scorer's prompt_section does not call _criteria_section "
                   "-- the criteria prose has a second source again")
    # THE DOCSTRING IS NOT AUTHORED PROMPT TEXT. The original rule counted
    # literals inside an `if` BRANCH, where no docstring can appear; a whole
    # function has one, and counting it made this fire at 421 characters on a
    # `prompt_section` that pastes nothing. Same error as reading prose as code,
    # one level up -- strip it before measuring.
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.body \
           and isinstance(node.body[0], ast.Expr) \
           and isinstance(node.body[0].value, ast.Constant) \
           and isinstance(node.body[0].value.value, str):
            node.body.pop(0)
    total = sum(len(n.value) for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str))
    if total > 300:
        bad.append(f"the scorer's prompt_section holds {total} characters of "
                   f"authored text -- a pasted-back copy looks exactly like this")
    return bad


def check_criteria_prose_has_one_source() -> list[str]:
    """Is the criteria prose still stated ONCE, or has a second copy grown back?

    It was stated twice for months. score.py:build_prompt held the block, and
    olx_prompts._criteria_section held a copy whose docstring called it
    "score.py:build_prompt's derive_from_criteria block, verbatim". By the time
    anyone compared them they were not verbatim: criterion 5's example, criterion
    7's example and criterion 10's WK1 rule had each drifted, so the two scorers
    put materially different words to the model on all eight OC items and every
    audit passed, because each side was internally consistent.

    Nothing detected that. The prompt audit compares the RUBRIC's elements
    against the web prompt, and this prose is authored in the scorers rather than
    the rubric, so it fell between the two.

    The fix was structural -- score.py calls the same function the web calls --
    and this check is what keeps it that way. It fails if that branch stops
    delegating, or if a long string literal reappears inside it, which is what a
    pasted-back copy looks like. It deliberately does not compare the two texts:
    once there is one source there is nothing to compare, and a check that
    compares a thing with itself passes forever.
    """
    import ast, pathlib
    # By import; see `_harness_source`. This was `with_name("score.py")`.
    src = _harness_source("score.py")
    try:
        tree = ast.parse(src)
    except SyntaxError as exc:
        return [f"score.py does not parse, so the criteria prose cannot be checked: {exc}"]

    fn = next((n for n in ast.walk(tree)
               if isinstance(n, ast.FunctionDef) and n.name == "build_prompt"), None)
    if fn is None:
        return ["score.py has no build_prompt(), so the criteria branch cannot be found"]

    branch = None
    for node in ast.walk(fn):
        if not isinstance(node, ast.If):
            continue
        t = ast.unparse(node.test)
        if "derive_from_criteria" in t:
            branch = node
            break
    if branch is None:
        return ["score.py:build_prompt has no `derive_from_criteria` branch -- if the "
                "shape changed, retarget this check rather than deleting it"]

    out: list[str] = []
    # BODY ONLY. `ast.walk` on the If node descends into `orelse` as well, which
    # is the `elif derive_from_credit` chain -- a different branch with prose of
    # its own, and walking it made this check fire on two innocent literals the
    # first time it ran.
    body = [n for stmt in branch.body for n in ast.walk(stmt)]
    calls = {ast.unparse(n.func) for n in body if isinstance(n, ast.Call)}
    # FOLLOW THE DELEGATION. Goal P moved the composing call out of this branch
    # and into the SCORER's `prompt_section`, because which slots a course asks
    # is the scorer's choice and the engine was making it by name. The invariant
    # is unchanged -- the prose must have ONE source -- so this FOLLOWS rather
    # than relaxes: the branch may call `_criteria_section` directly or delegate
    # to a scorer that does, and that scorer's body is then held to the same two
    # rules, delegation and the literal budget.
    delegated = any("prompt_section" in c for c in calls)
    if not any("_criteria_section" in c for c in calls) and not delegated:
        out.append("score.py's derive_from_criteria branch no longer calls "
                   "_criteria_section -- the criteria prose has a second source "
                   "again, and the two copies will drift the way they did before")
    if delegated:
        out += _prose_source_of_the_scorer()

    # TOTAL authored text in the branch, not the longest single literal. Adjacent
    # string literals are concatenated at parse time, so the original block was
    # one huge Constant and a per-literal threshold would have caught it -- but a
    # copy reassembled with `+` or an f-string is a dozen short ones, and the
    # first version of this check passed a synthetic paste built that way. Sum
    # them, and the shape of the copy stops mattering.
    LIMIT = 300
    prose = [n.value for n in body
             if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    total = sum(len(t) for t in prose)
    if total > LIMIT:
        longest = max(prose, key=len)
        out.append(f"score.py's derive_from_criteria branch holds {total} characters "
                   f"of string literal across {len(prose)} of them "
                   f"({longest[:60].strip()!r}...) -- criteria prose belongs in "
                   "olx_prompts._criteria_section, which both scorers read")
    return out


def check_every_check_is_invoked() -> list[str]:
    """Does every check in this file actually RUN?

    A check nobody calls is worse than no check: it reads as coverage, it is
    maintained as coverage, and it enforces nothing. Six were found this way,
    among them `check_weighted_slots_are_scored` -- written the same morning to
    catch a weighted slot the arithmetic ignored, never wired to the runner, and
    so silent through the very regression it was built for.

    The audit that found them was itself wrong first: it searched for
    `check_x(` across the sources, which every definition satisfies on its own
    `def` line, so all 38 looked reached. Hence the `def` lines are stripped
    here before the call sites are counted -- a check must be called from
    SOMEWHERE THAT IS NOT ITSELF.
    """
    import re
    here = pathlib.Path(__file__).parent
    src = pathlib.Path(__file__).read_text()
    defined = set(re.findall(r"^def (check_\w+)", src, re.M))
    called = set(re.findall(r"\b(check_\w+)\s*\(",
                            re.sub(r"^def check_\w+.*$", "", src, flags=re.M)))
    for name in ("equivalence.py", "measured.py", "agreement.py", "compare_runs.py",
                 "olx_prompts.py", "leakage.py"):
        try:
            called |= set(re.findall(r"\b(check_\w+)\s*\(", (here / name).read_text()))
        except OSError:
            continue
    return [f"enforcement.{n}() is defined but never invoked -- it reads as "
            f"coverage and enforces nothing" for n in sorted(defined - called)]


def check_web_scorer_exercises_its_sheet() -> list[str]:
    """RETIRED 2026-09-24 with the python web engine. ALWAYS RETURNS [].

    It watched: whether the PYTHON MIRROR behaved as its sheet says rather than
    merely parsing it -- it drove `agreement.SCORERS`, so the scorer under test
    was the copy, not the app.

    THE APP IS STILL WATCHED, by a better instrument: `web_signatures` drives
    `probe.test.ts` against the real engine and reports what each sheet
    ENFORCES. That is the same question asked of the side that ships.

    THAT QUESTION NO LONGER HAS TWO SIDES. The python mirror of
    `scoreSlotSheet` was eliminated in goal O, so this would compare a
    thing against itself or against nothing. O's own text named the
    class: "a check that exists to catch drift between two
    implementations is dead weight once there is one implementation".

    KEPT AS A RECORD rather than deleted, so what STOPPED being watched
    stays legible -- the same treatment as
    `check_no_slot_is_both_asked_and_computed`.
    """
    return []

# Item-keyed branches in score.py that implement RULE BEHAVIOUR by hand instead of
# reading it from a declaration both sides share. Each needs a reason, and a new
# one is a finding until someone writes one.
#
# They matter more than they look. A declared primitive is compared between the
# two scorers by the enforcement audit; a hand-written branch is compared by
# nobody, so the sides drift silently and the audit reports clean. Q4a and Q4c hit
# this exactly: `forbid` existed as a general web primitive and as a hand-written
# POLARITY_GATE_ITEMS branch here, so declaring a forbid rule on a new item made
# the CLI ASK the model a question the web computed -- and the only reason it
# surfaced is that the prompt-text audit noticed the extra question.
# MOVED TO THE RECORDS 2026-09-25: this course's backlog, not the
# engine's. While it lived here the ratchet rule could be run from
# python and from nowhere else.
HANDCODED_ITEM_RULES = _declaration("HANDCODED_ITEM_RULES")


# How many hand-coded item rules are still declared. It may only go DOWN.
#
# A declaration is a promise to convert, not a licence to keep. The existing
# check compares the table against score.py and is silent about an entry that is
# accurately declared -- so seven of them could sit there indefinitely, each one
# individually justified, and the table would read as coverage while enforcing
# nothing about its own size. That is how the SLOT_NOTES backlog got to eighteen.
#
# Lower this as entries go. Raising it is the finding.
# RAISED 0 -> 1 on 2026-09-12, deliberately and once. The table reached zero on
# 2026-08-28 and the ratchet exists so it does not quietly refill; this entry is
# the exception that was argued rather than assumed -- the alternative fix was
# built, measured and reverted because it moved a paper-only string into the
# shared rubric. Lower it the moment a paper-side per-item declaration exists
# that the rubric does not have to carry.
HANDCODED_BUDGET = _budget("HANDCODED_BUDGET")


def check_handcoded_rules_are_being_cleared() -> list[str]:
    """Is the hand-coded table shrinking, or accumulating?

    Every entry is outstanding work: a rule one scorer states as a declaration
    and the other reimplements in Python, which the enforcement audit cannot
    compare because it compares declarations. Seven of these were closed on
    2026-08-28 and each one turned up something the declaration had got wrong --
    a rule described backwards, a conjunction with four implementations rather
    than two, an exemption gone stale.

    The ratchet is two-sided on purpose. Over budget means an entry was ADDED and
    the table is growing. Under budget means work landed and the budget was not
    lowered, which would silently leave room for a new entry to take its place.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K, and `enforce/ratchet.ts` serves
    # MORE THAN ONE of these checks: "a ratchet may only tighten" was the same
    # fifteen lines in each, with different nouns. Python supplies the count,
    # the budget and the noun.
    import lo_enforce

    return lo_enforce.run("ratchets_only_tighten", {"ratchets": [{
        "table": "HANDCODED_ITEM_RULES", "budgetName": "HANDCODED_BUDGET",
        "count": len(HANDCODED_ITEM_RULES), "budget": HANDCODED_BUDGET,
        "unit": "hand-coded rule",
        "advice": "A declaration is a promise to convert it, not a licence to "
                  "keep it: convert the rule, or lower the budget only when one "
                  "goes",
    }]})



def check_no_undeclared_handcoded_rules() -> list[str]:
    """Rule behaviour keyed by item id in score.py, rather than declared.

    The enforcement audit compares what the two sides DECLARE. A branch written
    as `if item["id"] in SOME_SET` is invisible to it, so the two implementations
    can diverge with the audit reporting clean -- which is what happened when
    `forbid` existed as a general web primitive and a hand-written CLI branch at
    the same time.

    This does not forbid hand-coding: some rules genuinely have no primitive.
    It forbids hand-coding SILENTLY. Every branch needs a line in
    HANDCODED_ITEM_RULES saying why, and a new one fails until it gets one.
    """
    import ast
    import score as _score

    def is_item_id(node):
        if (isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name)
                and node.value.id == "item"):
            k = node.slice
            return isinstance(k, ast.Constant) and k.value == "id"
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "get" and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "item" and node.args
                and isinstance(node.args[0], ast.Constant)):
            return node.args[0].value == "id"
        return False

    try:
        tree = ast.parse(inspect.getsource(_score))
    except Exception as e:
        return [f"cannot parse score.py: {type(e).__name__}: {e}"]

    out, seen = [], set()
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        for n in ast.walk(fn):
            if isinstance(n, ast.Compare) and is_item_id(n.left):
                rhs = n.comparators[0]
                # A comparison against RUNTIME DATA is not a rule. `--only Q1 Q4b`
                # filters which items to score, so `item["id"] not in only` compares
                # the id against a user-supplied list -- categorically unlike
                # comparing it against an authored constant, which is what makes a
                # rule uncomparable between the two scorers. A bare name that is not
                # a module-level attribute of score.py is a local or a parameter, so
                # that is the test. Without it the table had to carry an entry that
                # was never a rule, and a table about rules that contains a
                # non-rule teaches its readers to skim.
                if isinstance(rhs, ast.Name) and not hasattr(_score, rhs.id):
                    continue
                tag = ast.unparse(rhs)
                key = (fn.name, tag)
                seen.add(key)
                if key not in HANDCODED_ITEM_RULES:
                    out.append(
                        f"score.py:{n.lineno} `{fn.name}` branches on the item id "
                        f"against {tag} — rule behaviour keyed by item, which the "
                        f"enforcement audit cannot compare against the web. Declare "
                        f"it in HANDCODED_ITEM_RULES with a reason, or express it as "
                        f"a primitive both sides read")
    for key in sorted(set(HANDCODED_ITEM_RULES) - seen):
        out.append(f"HANDCODED_ITEM_RULES declares {key}, which no longer exists in "
                   f"score.py — a stale exemption silences a real finding later")
    return out


# Item kinds whose score comes from a SLOT SHEET. Was `agreement.SCORERS`
# until the python web engine was eliminated; the set is the same.
_WEB_SHEET_KINDS = frozenset({"slots", "oc", "oc_cadence"})


def check_recorded_answers_are_complete() -> list[str]:
    """Does the artifact record what the model answered, for every slot?

    A recorded number is only as good as the record. `verdict_of` reads
    `checks[k]["verdict"]`, which a COUNT slot has not got -- it answers `count` --
    so four count slots recorded "" in every artifact, in every run: Q1's
    `harms_listed` and `benefits_listed`, Q2's `reasons_listed` and
    `reasons_failing`. Reading the artifact said those checks were never answered.
    They were, every time. The entire Q1 diagnosis had to be rebuilt from prose
    fragments in `evidence` because the numbers were not where numbers go.

    Nothing else in the harness notices: a recording fault moves no score, so no
    sweep, gate or audit reacts to it. That is why this check exists and why it
    RUNS the recording path over a synthetic sheet rather than reading it.

    Two assertions, and the second matters as much as the first:

      COMPLETE   every slot the model can answer must record something.
      NOT SCORING   `recorded_answer` must not appear on any item's scoring
                    fingerprint. Recording and scoring have to stay separable, or
                    the next fix to one silently invalidates every measurement
                    taken under the other.

    PICK slots are exempt BY DECLARATION, not by oversight: they record "" here
    and their values live in `answers`, and changing that would alter the recorded
    semantics of 30 slots on 13 items where readers treat "" as unanswered.
    """
    import agreement as A
    import measured as M

    out = []
    for h, blocks in sorted(A.BLOCKS.items()):
        try:
            rub = config(h)["rubric"]
        except Exception:
            continue
        for aid, job in sorted(blocks.items()):
            # THE KINDS THAT CARRY A WEB SHEET, named rather than discovered
            # from `A.SCORERS` -- that registry was the python web engine's and
            # went with it (goal O). This check is NOT about that engine: it
            # asks whether the ARTIFACT records what the model answered, which
            # is a question about the olx and paper columns and outlives the
            # comparison entirely.
            if not job.get("olx") or job["kind"] not in _WEB_SHEET_KINDS:
                continue
            iid = job["item"]
            try:
                act = A.load_action(job["olx"], aid)
            except Exception:
                continue
            counted = {k for cr in (rub.BY_ID[iid].get("counts") or []) for k in [cr["key"]]}
            sheet = {}
            for sl in act["slots"]:
                if sl.get("count_max") is not None:
                    sheet[sl["key"]] = {"count": sl["count_max"]}
                elif sl.get("picks"):
                    vs = (act.get("choices") or {}).get(sl["picks"]) or ["x"]
                    sheet[sl["key"]] = {"refers_to": vs[0]}
                else:
                    sheet[sl["key"]] = {"verdict": (sl.get("options") or ["met"])[0]}
            for sl in act["slots"]:
                if sl.get("picks"):
                    continue                      # declared: recoverable from `answers`
                if sl["key"] in (act.get("excluded") or ()):
                    continue                      # computed, not answered
                got = A.recorded_answer(sl, sheet)
                if got in ("", None):
                    kind = "count" if sl.get("count_max") else "verdict"
                    out.append(
                        f"H{h} {iid}: the artifact records nothing for `{sl['key']}` "
                        f"(a {kind} slot the model answers), so a reader of the "
                        f"artifact cannot tell an unanswered check from an answered one")

    # Recording must not be scoring.
    for item in sorted(M._jobs()):
        try:
            parts = {n for _, n in M._parts_for(item)}
        except Exception:
            continue
        if "recorded_answer" in parts:
            out.append(f"{item}: `recorded_answer` is on the scoring fingerprint — "
                       f"a recording fix would now invalidate this item's measurement")
    return out



def check_the_record_is_pushed_at_the_change() -> list[str]:
    """Does `--write` still print the prior record for every item it changes?

    QUALITY_CONTROL.md §2e is the only discipline of the three that a machine can
    enforce, and it is enforced in ONE place: `olx_prompts.main` calls
    `prior_record` for each item whose prompt text moved. Delete that call and the
    guide's paragraph stays true-looking while nothing happens -- which is the
    exact shape of the failure §2e was written about.

    It matters because §2e cost the most to learn. A day went into rewriting Q1's
    `reasons_given` while the comment above the component already named gold's
    conditional structure, classified every cell with gold < 3, and diagnosed the
    failing cell as a `harms_listed` misclassification. Eleven configurations,
    ~900 calls, and the answer was in the file.

    Three things are asserted: the writer calls the hook, the hook still reports
    the three sources it promises, and it does not swallow its own failures --
    the first version raised NameError on every lookup into a bare `except: pass`
    and reported an empty record.
    """
    import inspect
    import olx_prompts as O

    out = []
    try:
        src = inspect.getsource(O.main)
    except Exception as e:
        return [f"cannot read olx_prompts.main: {type(e).__name__}: {e}"]
    if "prior_record(" not in src:
        out.append("olx_prompts.main no longer calls prior_record(): a rule can be "
                   "changed and regenerated without the record being shown, which "
                   "is QUALITY_CONTROL.md §2e unenforced")
    if "_items_whose_prompt_changed(" not in src:
        out.append("olx_prompts.main no longer computes which items changed, so the "
                   "record cannot be scoped to them")

    try:
        body = inspect.getsource(O.prior_record)
    except Exception as e:
        return out + [f"cannot read prior_record: {type(e).__name__}: {e}"]
    for needle, what in (("rubric_h", "the comment blocks in the rubric"),
                         ("GOALS.md", "the goal entries"),
                         ("drafts", "the item drafts"),
                         ("PRIMITIVES in use", "the structural inventory (§2b)")):
        if needle not in body:
            out.append(f"prior_record no longer reports {what}")
    if "except Exception:\n            pass" in body:
        out.append("prior_record swallows a lookup failure silently — it did exactly "
                   "that once and reported an empty record for every item")

    # And it must actually produce something for a real item.
    try:
        got = O.prior_record("Q1")
        if got.count("\n") < 4:
            out.append(f"prior_record('Q1') returned {got.count(chr(10))+1} line(s): "
                       f"it is reporting an empty record")
        if "failed:" in got:
            out.append(f"prior_record('Q1') reports a failed lookup: "
                       f"{[l for l in got.splitlines() if 'failed:' in l][:1]}")
    except Exception as e:
        out.append(f"prior_record('Q1') raised {type(e).__name__}: {e}")
    return out


def check_scorer_fingerprint_covers_its_callees() -> list[str]:
    """Does the fingerprint hash everything the hashed code CALLS?

    Hashing a function does not hash its callees, and for a long time three of
    them -- `verdict_of`, `answer_of`, `is_satisfied` -- decided verdicts for
    every item while being reachable only through `satisfied_map` and
    `apply_computed`. Editing any of the three changed scores while all 26 items
    still read current.

    `measured._closure` takes the transitive closure so the CLASS is fixed rather
    than those three names, and this asserts the closure is actually closed: for
    every function hashed, every local function it calls is hashed too. It is a
    check on the closure's own resolver -- an alias it fails to follow, a depth it
    stops at -- because a closure that quietly stops early looks exactly like a
    closure that is complete.

    It also asserts the two tables cannot disagree. `SCORER_PARTS` was authored by
    hand beside `_ALWAYS` and had drifted: it omitted `agreement.expand_counted`,
    so the whole-path fingerprint -- the ledger header's, and the fallback for an
    item whose shape cannot be read -- was NARROWER than every per-item one.
    """
    import measured as M

    out: list[str] = []
    if not set(M._ALWAYS) <= set(M.SCORER_PARTS):
        missing = sorted(set(M._ALWAYS) - set(M.SCORER_PARTS))
        out.append(f"SCORER_PARTS is missing {missing}, which _ALWAYS includes -- "
                   f"the whole-path fingerprint is narrower than the scoped one, so "
                   f"the conservative fallback is not conservative")

    whole = set(M._closure(M.SCORER_PARTS))
    gaps = sorted({(mod, name, c) for mod, name in whole
                   for c in M._local_callees(mod, name) if c not in whole})
    for mod, name, callee in gaps:
        out.append(f"{mod}.{name} calls {callee[0]}.{callee[1]}, which the "
                   f"fingerprint does not hash -- editing it would change "
                   f"scores while every item still read current")

    # And the scoping must not drop something unconditional. A part is allowed out
    # only by being item-dependent by design; anything else must survive scoping.
    for item in sorted(M._jobs()):
        roots = M._parts_for(item)
        dropped = set(M._closure(roots)) - set(M._scoped_closure(roots))
        stray = sorted(p for p in dropped if p not in M._SCOPED_PARTS)
        if stray:
            out.append(f"{item}: the scoping dropped {stray}, which is not an "
                       f"item-dependent part -- only a per-kind scorer or a "
                       f"per-primitive parser may be scoped out")
    return out


def check_scorer_fingerprint_is_scoped_and_prose_blind() -> list[str]:
    """Does STALE SCORER mean what it says?

    The ledger stamps each recorded number with a fingerprint of the code that
    produced it, and refuses to call the number current when that code moves.
    A fingerprint is only useful between two failures: it must move when
    BEHAVIOUR moves, and it must not move otherwise.

    Both halves were broken. Correcting one docstring in `parse_counts` --
    retracting a misdiagnosis, changing no code -- marked twenty-one of
    twenty-six items STALE SCORER, and the blast radius was guessed from "does
    this sheet author any computed primitive", which is true of twenty-one items
    and so indistinguishable from a global flag. Between them that is roughly
    1800 calls of re-sweeping to reconfirm numbers nothing had touched, and a
    flag that would be ignored inside a day.

    So this asserts the two properties directly, and one more: an item that
    fingerprints the WHOLE path is the signature of the scoping having silently
    fallen back, which is how it read for every item while a KeyError was being
    swallowed.
    """
    import measured as M

    out = []
    doc = "def f(x):\n    'doc'\n    # a comment\n    return x + 1\n"
    prose = "def f(x):\n    'another docstring entirely, much longer'\n    return  x+1\n"
    behave = "def f(x):\n    'doc'\n    return x + 2\n"
    try:
        if M._behaviour_src(doc) != M._behaviour_src(prose):
            out.append("the fingerprint MOVES on a docstring or comment edit, so "
                       "documenting the scorer marks the corpus stale")
        if M._behaviour_src(doc) == M._behaviour_src(behave):
            out.append("the fingerprint does NOT move when a return value "
                       "changes, so a real scorer change would be recorded as "
                       "current -- the guard is inert")
    except Exception as e:
        out.append(f"the fingerprint's prose stripper raised "
                   f"{type(e).__name__}: {e}")
        return out

    shas = {it: M.scorer_sha(it) for it in M._jobs()}
    if len(set(shas.values())) < 2:
        out.append(f"all {len(shas)} items share one fingerprint, so any scorer "
                   f"edit stales the whole corpus -- the per-item scoping is not "
                   f"in effect")
    whole = sorted(it for it in shas if len(M._parts_for(it)) >= len(M.SCORER_PARTS))
    if whole:
        out.append(f"{', '.join(whole)} fingerprint the ENTIRE scoring path, "
                   f"which is the scoping's fallback, not a scope -- something "
                   f"in _parts_for is failing for them")
    return out


def check_action_attributes_are_declared_in_the_block() -> list[str]:
    """Does the WEB BLOCK accept every attribute the OLX authors on <LLMAction>?

    `check_olx_attributes_are_read` asks whether the PYTHON harness parses an
    attribute. This asks the other half, and the other half is where the corpus
    broke: LLMAction's zod schema is `.strict()`, so an attribute it does not
    declare does not degrade the block -- it REPLACES it with an ErrorNode. The
    button still renders, with nothing behind it. Clicking does nothing, no
    status is ever written, and the runner waits out its 300s and reports
    `no-cell`.

    That cost seven items of a two-sided sweep: Q4a, Q4b, Q4c, NR, DAY1, DAY2 and
    WK2, every cell, silently. `forbid` was implemented in slotSheet.ts, parsed
    in LLMAction.ts, declared in primitives.json, parsed by agreement.py, covered
    by unit tests, and never added to the block's attribute schema. `maps` was
    the same and was additionally never even passed to buildSlotSchema. Every
    existing check passed, because every existing check looked at one side.

    The error is baked into the idmap DUMP at parse time, so it survives a
    re-dump and is invisible to a prompt-text freshness check -- which is why the
    STALE IDMAP guard reported those items as fine.
    """
    # PORTED to `enforce/actionAttributesDeclared.ts` (goal K).
    #
    # THE READER MOVED TO THE RIGHT SIDE, as it did for
    # `check_fails_verdict_is_mirrored_in_the_app`: python was crossing the
    # repository boundary to grep an ENGINE file for an ENGINE schema. The block
    # belongs to lo-blocks and so does the check on it.
    #
    # PYTHON STILL PASSES BOTH HALVES IT READS -- the schema source and the
    # attributes the handouts author -- so this path answers about the tree this
    # process can see rather than whichever one the runner resolves.
    import re as _re

    import lo_enforce
    import paths as _p

    block = _p.LO / "packages/shared/components/blocks/action/LLMAction.ts"
    try:
        src = block.read_text()
    except OSError:
        return []                      # lo-blocks absent on this machine

    used: dict[str, list] = {}
    for f in _p7.handout_olx_paths():
        try:
            txt = f.read_text()
        except OSError:
            continue
        for tag in _re.findall(r"<LLMAction\b[^>]*>", txt, _re.S):
            tid = _re.search(r'(?:^|\s)id="([^"]+)"', tag)
            site = tid.group(1) if tid else f.name
            for a in _re.findall(r'(?:^|\s)(\w+)="', tag):
                at = used.setdefault(a, [])
                if site not in at:
                    at.append(site)

    return lo_enforce.run("action_attributes_are_declared_in_the_block",
                          {"blockName": block.name, "blockSrc": src,
                           "used": {k: sorted(v) for k, v in used.items()}})

def check_olx_attributes_are_read() -> list[str]:
    """Is every attribute authored on an <LLMAction> actually PARSED?

    An attribute the harness never reads is a rule that exists in the sheet, is
    maintained, is visible to whoever edits the OLX -- and does nothing. The
    failure is silent in both directions: the attribute looks live, and the
    consumer looks correct, because `item.get("counts", [])` over an empty list
    raises nothing and simply never charges.

    THE STORY THIS DOCSTRING USED TO TELL WAS WRONG, and it is corrected here
    rather than deleted, because the wrong version was stated out loud and cost
    140 calls. It claimed `counts=` had gone unparsed on five items and 22 points,
    with 2a's five gold-4 cells scoring 6 on checks that were never asked. It had
    not: every one of those items carries its own `counts` key on its RUBRIC item,
    `score_slots` reads it from there, and the counted members were scoring all
    along. 2a's misses are a judgement about how many `hows` the response gives,
    not a plumbing fault.
    What the episode actually demonstrates is the failure mode this check exists
    for -- an attribute can be authored, maintained and visible while nothing
    reads it, in either direction -- and the failure mode of the diagnosis:
    "verified" against the fixed code only, which is why a harness fix must now
    be run against the pre-fix code (`before_after.py`).

    `check_weighted_slots_are_scored` cannot see this: it asks whether a scorer
    NAMES the slot, and `how_1` is named -- inside a loop over a list that is
    always empty. Named but unreachable.
    """
    import re
    import agreement as A
    import forms as H

    # Structural, or consumed by a path other than the attribute parser.
    KNOWN = {
        "id": "names the action; looked up by ACTION",
        "target": "the feedback field, read when the tag is located",
        "max": "the item total, taken from the rubric rather than the tag",
        "showChecks": "read as a substring test, not through the parser",
        "slots": "parsed by parse_slots with the verdicts default",
        "verdicts": "the default vocabulary, read alongside slots",
    }
    src = inspect.getsource(A)
    # Only the real parse sites: `_attr(open_tag, "x")` and an explicit regex
    # over the tag. A looser match (any `"word="` literal in the source) let an
    # attribute count as read because its name appeared in a comment.
    read = set(re.findall(r'_attr\(open_tag,\s*"(\w+)"\)', src))
    read |= set(re.findall(r"r'(\w+)=", src))
    read |= set(re.findall(r'search\(r.(\w+)=', src))

    # A RUBRIC-SIDE DECLARATION IS COVERAGE. Several primitives are declared
    # twice -- once as an OLX attribute for the runtime, once as a key on the
    # rubric item for the Python scorers -- and the scorers read the rubric.
    # Judging "unread" from agreement.py alone reported `counts=` as a live
    # 22-point hole across five items when every one of those items carries its
    # own `counts` key and had been scoring correctly all along. That false
    # alarm cost 140 calls, so the second source is consulted here.
    import olx_prompts as O
    rubric_keys = set()
    for hh in _forms():
        try:
            for it in config(hh)["rubric"].ITEMS:
                rubric_keys |= {k for k, v in it.items() if v}
        except Exception:
            continue

    problems = []
    for h in _forms():
        try:
            text = pathlib.Path(O.OLX % h).read_text()
        except Exception:
            continue                    # corpus absent on this machine
        for tag in re.findall(r"<LLMAction\b[^>]*>", text, re.S):
            for attr in re.findall(r'\s(\w+)="', tag):
                if attr in KNOWN or attr in read or attr in rubric_keys:
                    continue
                problems.append(
                    f"H{h}: <LLMAction> authors `{attr}=`, and neither "
                    f"agreement.py nor any rubric item carries it -- the rule "
                    f"is in the sheet and reaches no scorer")
    return sorted(set(problems))


def check_selectors_govern_something() -> list[str]:
    """Does every ITEM SELECTOR still select something?

    rubric_h2 keeps tuples of item ids -- CONTINGENCY_GATE_ITEMS,
    POLARITY_GATE_ITEMS, TYPE_BARRIER_ITEMS -- and each one exists to decide
    which items get a particular slot or paragraph. Delete the thing it governs
    and the tuple survives: still defined, still imported, now deciding nothing,
    and reading in the source exactly like a live feature.

    It happened, and it cost a measured cell. `TYPE_BARRIER_ITEMS` governed
    `barrier_is_not_this_type`, the slot commit 71ac1d7 added to win NR/p14 and
    take the item 14 -> 16. The `stimulus_move` work dropped that slot as
    superseded and left the tuple behind. p14 went from 6/6 to 0/6 while EVERY
    remaining check on its sheet passed, so no verdict was wrong, no gate fired,
    and the loss surfaced only as a median two cells down.

    The sibling `check_weighted_slots_are_scored` cannot see this. It polices a
    slot the arithmetic ignores; this is a slot that no longer exists, so there
    is nothing for the arithmetic to ignore. The mistake leaves a trace at both
    ends and both are checked:

      A. a selector consulted NOWHERE outside its own definition and the import
         lines that carry it between modules;
      B. a slot key still named by the scorers that no item's sheet emits, which
         is the same deletion seen from the reading end.
    """
    import inspect
    import agreement as A
    import olx_prompts as O
    # THE MODULE, NOT A VIEW, and this is the one place that is right. This
    # check reads rubric_h2's SOURCE -- it looks for selector tuples that are
    # still defined and no longer consulted -- so it is a check about the
    # AUTHORING ARTIFACT, not about the rubric data. `inspect.getsource` on a
    # view raises TypeError, which is how this was found: converting it with the
    # other nine broke the whole audit.
    #
    # IT WAS PLANNED TO DIE WITH THE MODULES AT STAGE 5, on the reasoning that
    # when there is no module source there are no stale selectors in it to find.
    # That premise did not survive Stage 6c. Handout 2's module was not deleted,
    # it was RENAMED to `rubric_h2_source.py` and moved out of the scoring path,
    # because `rubric_export` has to read its four factories to write the course
    # file. The authoring artifact still exists, so stale selectors in it are
    # still possible and this check still has something to find -- it is
    # repointed rather than retired. It expires when that file does, not before.
    import rubric_h2_source as R2
    import score as S

    problems = []
    src_r2 = inspect.getsource(R2)
    selectors = {
        n: v for n, v in vars(R2).items()
        if re.fullmatch(r"[A-Z][A-Z0-9_]*_ITEMS", n)
        and isinstance(v, tuple) and all(isinstance(x, str) for x in v)
    }

    # A selector's own definition is not a consultation, and neither is an alias
    # (`BARRIER_PICK_ITEMS = CADENCE_BARRIER_ITEMS`) nor the import that hands it
    # to another module. Strip all three, then anything left is a real use.
    consulting = re.sub(r"^[A-Z][A-Z0-9_]*_ITEMS\s*=.*$", "", src_r2, flags=re.M)
    for mod in (S, O, A):
        text = inspect.getsource(mod)
        text = re.sub(r"from rubric_h2(?:_source)? import \([^)]*\)", "", text)
        text = re.sub(r"from rubric_h2(?:_source)? import .*$", "", text,
                      flags=re.M)
        consulting += text
    for name in sorted(selectors):
        if name not in consulting:
            problems.append(
                f"{R2.__name__}.{name} = {selectors[name]} is defined and "
                f"imported but "
                f"consulted nowhere: it governs no slot and no paragraph. Either "
                f"the thing it selected was deleted -- in which case a measured "
                f"cell may have gone with it -- or the tuple is dead and should go")

    # B. every slot key the scorers read must still be emitted by some sheet.
    emitted = set()
    for h in _forms():
        for item in config(h)["rubric"].ITEMS:
            iid = item["id"]
            if iid not in O.ACTION:
                continue
            try:
                emitted |= {s["key"] for s in O.parse_slots(*O._slots_attr(h, O.ACTION[iid]))}
            except Exception:
                continue
            for parse, attr in ((O.parse_equals, "equals"), (O.parse_expect, "expect"),
                                (O.parse_forbid, "forbid")):
                try:
                    emitted |= {r["key"] for r in parse(_attr(h, iid, attr))}
                except Exception:
                    continue
    _oc = _oc_scorer()
    if _oc is None:
        return ["this course ships no `oc` scorer, so the three-way source "
                "comparison has nothing to read -- retarget this check"]
    # THROUGH THE DELEGATION. The `yes("...")` reads this scans for moved into
    # `web_deductions`/`web_deductions_cadence` when the mirrors were split so
    # the score could be DERIVED from the coded deductions; reading the entry
    # points alone found ZERO slot names against ten, and a check whose input is
    # empty reports nothing and looks clean. Fourth instance of that shape in one
    # day, which is why the helper exists rather than another hand-listed tuple.
    scorer_src = _source_through_delegates(
        (_oc.score_web, _oc.score_web_cadence, _oc.derive_ledger), _oc)
    # Only the two unambiguous slot accessors, so a `.get` on some other dict
    # cannot be mistaken for a check being read.
    read = set(re.findall(r'yes\("(\w+)"\)', scorer_src))
    read |= set(re.findall(r'"(\w+)" in keys', scorer_src))
    for key in sorted(read - emitted):
        problems.append(
            f"the scorers read check `{key}`, which no item's slot sheet emits any "
            f"more -- a deleted slot still being consulted, so its deduction is "
            f"silently never charged")
    return problems


def _source_through_delegates(fns, module, depth: int = 3) -> str:
    """Source of `fns` plus every module-level function they reach, transitively.

    A check that greps a scorer's body for the names it consults is one refactor
    away from reading a wrapper and finding nothing. Following the delegation
    makes the check about WHAT THE SCORER DOES rather than about how its body
    happens to be split up today.
    """
    import inspect

    seen, out, queue = set(), [], list(fns)
    while queue and depth >= 0:
        nxt = []
        for fn in queue:
            name = getattr(fn, "__name__", None)
            if not name or name in seen:
                continue
            seen.add(name)
            try:
                body = inspect.getsource(fn)
            except (OSError, TypeError):
                continue
            out.append(body)
            for ident in set(re.findall(r"\b([A-Za-z_]\w*)\s*\(", body)):
                got = getattr(module, ident, None)
                if inspect.isfunction(got) and ident not in seen:
                    nxt.append(got)
        queue, depth = nxt, depth - 1
    return "\n".join(out)


def check_weighted_slots_are_scored() -> list[str]:
    """Does every POINT-BEARING slot reach a scorer?

    `agreement.score_oc` and `score_oc_cadence` are hand-written mirrors of
    `derive_oc_ledger`, naming each check they consult. A slot authored with `@n`
    that neither names is answered by the model, recorded in the sheet, and then
    ignored by the arithmetic -- which is not a wrong number but a silent one.

    It happened: `barrier_is_not_this_type@2` fired on all six runs of NR/p14 and
    the cell still scored 4.0, because nothing read it. The verdict was right and
    the score did not move, which is the hardest kind of gap to notice.
    """
    import inspect
    import agreement as A
    import olx_prompts as O
    _oc = _oc_scorer()
    if _oc is None:
        return ["this course ships no `oc` scorer, so its web mirrors cannot be "
                "read -- retarget this check"]
    # THROUGH THE DELEGATION, not just the entry point. `score_web` used to hold
    # the rules; it now derives its pair from `web_deductions`, so reading only
    # the wrapper found NO slot name and reported all 21 weighted slots
    # unscored. That is the same wrapper-shaped blindness that made
    # `check_selectors_govern_something` pass vacuously on 112 characters --
    # here it failed loudly instead, which is the better direction, but the
    # remedy is the same: follow the calls.
    src = _source_through_delegates((_oc.score_web, _oc.score_web_cadence), _oc)
    problems = []
    for h in _forms():
        for item in config(h)["rubric"].ITEMS:
            iid = item["id"]
            if not item.get("derive_from_criteria") or iid not in O.ACTION:
                continue          # only the items those two scorers handle
            try:
                slots = O.parse_slots(*O._slots_attr(h, O.ACTION[iid]))
            except Exception:
                continue
            # A DERIVED slot may be honoured under another name: `demonstrates_type`
            # is an `expect` over `observed_type`, and score_oc implements it as
            # `observed != expected_type` without naming the key. So a derived key
            # counts as reached when the key OR any operand it reads appears.
            derived_ops = {}
            for r in O.parse_equals(_attr(h, iid, "equals")):
                derived_ops[r["key"]] = {r["left"], r["right"]}
            for r in O.parse_expect(_attr(h, iid, "expect")):
                derived_ops[r["key"]] = {r["left"]}
            for r in O.parse_forbid(_attr(h, iid, "forbid")):
                derived_ops[r["key"]] = {c["slot"] for c in r["conds"]}
            for s in slots:
                if s.get("pts") is None or s["key"] in src:
                    continue
                if any(op in src for op in derived_ops.get(s["key"], set())):
                    continue
                problems.append(
                    f"H{h} {iid}: slot `{s['key']}` carries {s['pts']:g} point(s) and "
                    f"is named by neither score_oc nor score_oc_cadence, so the "
                    f"harness ignores its verdict")
    return problems


def check_rubric_items_are_unique() -> list[str]:
    """Is each rubric table a well-formed set of distinct items?

    Structural invariants that nothing else asserts, because nothing else has
    reason to: every other check reads `BY_ID[...]` and trusts it.

    Added after a bad edit to rubric_h1.py spliced from the wrong offset — an
    index search matched Q1's `credit` list instead of Q6's — and re-included
    everything from Q1 onward. The file grew from 1424 lines to 2376 with TWO
    entries apiece for seven items, and `BY_ID` silently resolved to the second
    copy, so the next edit was verified against a different dict than the one it
    had changed. Every audit here stayed green throughout: they all went through
    `BY_ID`, which is exactly the thing that had gone wrong.

    Three invariants, all cheap:
      1. Item ids are distinct, and `BY_ID` reaches every item.
      2. A slot name appears once in an item's credit list.

    NOT checked here: whether the credit slots' points sum to the item's max.
    The same bad splice left a Q6 summing to 5.0 against a max of 10.0, so it
    would have caught this too — but `onlyif` legitimately lets a sum EXCEED the
    max (Q4b sums to 6 of 5, by design, because one slot's charge is suppressed
    when another fails) and Q4c sums to 4 of 5 for reasons `--scoring` already
    flags separately. Without a rule that tells a real shortfall from those, the
    invariant reports two standing findings and teaches people to ignore it.
    """
    # PORTED TO LO-BLOCKS (goal K, step 8). Python keeps the FETCH -- it knows
    # which forms this course declares and how to reach each rubric view -- and
    # the JUDGEMENT is `enforce/rubricItemsUnique.ts`. The invariants assume
    # nothing about any course: a list of items must not carry the same id
    # twice, and an index over it must reach every one.
    # SELF-ASSEMBLED. Subgoal E63: the runner builds this payload itself,
    # from the same course records python would have read. The assembler was
    # compared against the payload python used to send and found IDENTICAL
    # before this fetch was deleted; `runner.SELF_ASSEMBLING` names the rules
    # that comparison has cleared, and the runner refuses any other.
    # PYTHON KEEPS THE FETCH, and it must. E63 made this self-assembling --
    # measured payload-identical, and still wrong, because the self-test injects
    # by APPENDING A DUPLICATE ITEM TO THE IN-MEMORY `ITEMS` list and forking.
    # A payload the runner rebuilds from the rubric FILE cannot see that, so the
    # case went silent and the audit reported clean either way. Measured
    # 2026-09-26: before=0, after=0, against a rule that fires correctly when a
    # duplicated id is placed in its payload by hand.
    #
    # The assembler stays for callers inside lo-blocks, which have no python to
    # ask; the runner reaches it only when the payload is null, and python no
    # longer sends null.
    import lo_enforce

    by_form: dict = {}
    for h in _forms():
        for it in config(h)["rubric"].ITEMS:
            by_form.setdefault(h, []).append(
                {"id": it["id"],
                 "slots": [c["what"] for c in it.get("credit") or []]})
    return lo_enforce.run("rubric_items_are_unique", {"forms": [
        {"form": form,
         "ids": [i["id"] for i in items],
         "byIdCount": len({i["id"] for i in items}),
         "credit": items}
        for form, items in sorted(by_form.items(), key=lambda kv: str(kv[0]))]})


# Cells where a fixture box is empty AND the response still has unassigned text,
# and that is CORRECT: gold says the element was never stated, so an empty box is
# a faithful transcription and the leftover words are elaboration the clause-level
# split rightly discards. Declared so a NEW one fails. An entry that stops firing
# must be removed, like every other backlog here.
FIXTURE_GAP_BACKLOG: dict[tuple[str, int], str] = {
    # Empty. Both entries said "the fixture is correct here", which is not a fact
    # about a cell — it is a check firing where it should not, and the fix
    # belonged in the check.
    #
    # 1c/p9: 1c has no prose-derived box at all. Its title/x/y are read off the
    # GRAPH, so they are extractions, not quotations, and `_value_derived` now
    # says so for the item instead of the cell.
    #
    # Q6/p17: the unassigned runs sat BETWEEN two filled boxes. A lost element
    # runs to the end of the response or stands alone; it does not come bracketed
    # by two spans that were both assigned. The check now steps over interstitial
    # text.
}


# Items whose response is deliberately carried in more than one box, with why.
MULTI_BLOCK_DECLARED = _declaration("MULTI_BLOCK_DECLARED")


def check_single_box_fixtures_are_verbatim() -> list[str]:
    """For a one-box item, is the student's text reproduced EXACTLY?

    Where a response is one block, there is no segmentation judgement to make and
    the only thing that can go wrong is corruption in transit — a smart quote
    mangled by an encoding round-trip, a replacement character, text silently
    truncated. So the test is simply: does the box match the response verbatim?

    Two families are reported.

      * NOT VERBATIM. The box is not the response, ignoring whitespace. Either
        it lost characters or it gained them.
      * CORRUPT. The text carries mojibake ("â€™" for an apostrophe, "Â" for a
        non-breaking space) or U+FFFD, the sign of a decode that failed and was
        papered over. These survive every other check in this file, because the
        fixture and the response agree — both are wrong together.

    An item carried in MORE than one box is reported separately, for analysis
    rather than as a defect: splitting a response is a judgement, and the
    multi-box checks are the ones that examine it. Declaring it in
    MULTI_BLOCK_DECLARED says the split is intended.
    """
    import warnings
    import forms as H
    import segment as SEG

    MOJIBAKE = ("\u00e2\u0080\u0099", "\u00e2\u0080\u009c", "\u00e2\u0080\u009d",
                "\u00e2\u0080\u0093", "\u00c2\u00a0", "\ufffd")
    problems, multi = [], {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for h in _forms():
            cfg = H.config(h)
            try:
                subs = dict(H.find_submissions(h))
            except Exception:
                continue
            for pid, path in sorted(subs.items()):
                try:
                    segs = _segment_as_scored(h, pid)
                except Exception:
                    continue
                for item in cfg["rubric"].ITEMS:
                    iid = item["id"]
                    boxes = _fixture_boxes(iid, pid)
                    if len(boxes) > 1:
                        multi.setdefault(iid, len(boxes))
                        continue
                    # A lone box that holds a PARSED VALUE is not a quotation,
                    # so "is it reproduced verbatim" is not a question about it.
                    if set(boxes) & _value_derived(iid):
                        continue
                    if len(boxes) != 1:
                        continue
                    box = " ".join(next(iter(boxes.values())).split())
                    raw = " ".join((segs.get(iid) or "").split())
                    for bad in MOJIBAKE:
                        if bad in box or bad in raw:
                            problems.append(
                                f"H{h} {iid}/p{pid}: text carries {bad!r} — a "
                                f"decode that failed and was papered over, not a "
                                f"character any student typed")
                            break
                    if not box or not raw:
                        continue
                    # Compared directly, not through _locate: that helper bails
                    # on anything under ten non-space characters, which reported
                    # NP/p13's "I take away" as differing from itself.
                    b = "".join(box.split()).lower()
                    r = "".join(raw.split()).lower()
                    if b == r:
                        continue
                    if b in r:
                        # The box is a PREFIX or substring of the segment. That is
                        # usually the segment being over-inclusive rather than the
                        # box being truncated: D2/p19 holds exactly the definition
                        # while segment.py failed to find the DAY2 boundary and
                        # swept the daily example into D2's segment too — DAY2's
                        # segment is empty and its box holds that text. Reported
                        # as what it is, because the repair is in segment.py.
                        problems.append(
                            f"H{h} {iid}/p{pid}: the segment holds MORE than the "
                            f"box ({len(raw)} chars vs {len(box)}); the extra text "
                            f"is {raw[len(box):][:44]!r}... Check whether the next "
                            f"item's marker fired — an empty neighbouring segment "
                            f"means the boundary was missed, not that this box "
                            f"lost text")
                    else:
                        problems.append(
                            f"H{h} {iid}/p{pid}: the box is not the response "
                            f"verbatim ({len(box)} chars vs {len(raw)}) — a "
                            f"one-block answer has no segmentation judgement to "
                            f"make, so any difference is corruption in transit")
    for iid, n in sorted(multi.items()):
        if iid in MULTI_BLOCK_DECLARED:
            continue
        problems.append(
            f"{iid} is carried in {n} boxes, not one. Splitting a response is a "
            f"judgement — read it out with `--fixture {iid}` and either confirm "
            f"the split or declare it in MULTI_BLOCK_DECLARED")
    return problems


# Overridable so the selftest can point the check at a source it controls;
# the check reads a FILE, so there is no loaded object to patch instead.
_CONSENSUS_SOURCE: str | None = None


# Every `{{corpus:...}}` still standing in a served .olx. The count may FALL and
# may not RISE, like the other budgets here.
# 0 as of 2026-09-16. Handout 2's worked non-example was a real student's
# sentence, carried into the page through a reference -- which kept the words
# out of the FILE but still made a student's writing the thing every reader is
# taught from, and made the page unrenderable without $COURSE_DATA. It is now an
# invented sentence with the same defect being taught ("Going to bed earlier
# will reward me with feeling rested" -- the reward is just what the behaviour
# does), checked against the whole response space for collisions.
#
# The budget ratchets DOWN and never up: a new reference in an .olx is a
# finding, not a precedent.
OLX_CORPUS_REF_BUDGET = _budget("OLX_CORPUS_REF_BUDGET")


def check_olx_corpus_references() -> list[str]:
    """A served .olx that cannot be rendered without the student corpus.

    THE MECHANISM IS A CONCESSION, NOT A SOLUTION, and this check exists to keep
    saying so. A `{{corpus:...}}` reference takes a student's sentence out of the
    repo -- which is the point -- but it leaves the handout DEPENDENT on
    `$COURSE_DATA` to render at all, and it leaves the sentence itself still being
    shown to whoever reads the page. It buys privacy in the repository and buys
    nothing about whether a real answer should be the worked example in the first
    place.

    THE FIX EACH ONE IS WAITING FOR is an invented example that teaches the same
    point, at which case the reference disappears and the dependency with it.
    That is why the budget ratchets DOWN only: a reference removed is progress
    and must not be spendable on a new one somewhere else.

    Reported per reference, with its cell named, so the readout says which
    student's words are still load-bearing rather than only how many.
    """
    # A reference leaves the page dependent on the corpus to render; the budget
    # ratchets down.
    import lo_enforce

    return lo_enforce.run("olx_corpus_references", None)


def check_consensus_fixes_have_no_duplicate_cells() -> list[str]:
    """Two entries for the same (item, pid) in CONSENSUS_FIXES.

    `check_consensus_fixes_are_unique` guards duplicate BOXES inside one entry.
    It cannot see this one: CONSENSUS_FIXES is a dict LITERAL, so a repeated key
    is resolved by Python before any check runs — the later entry wins and the
    earlier one vanishes without a trace. Reading the loaded dict can never find
    it; only the source can.

    Not hypothetical. Q6/p8 already had an entry extending `change_a2`, and a
    second entry assigning its two consequence boxes was added further up the
    file. The dict kept the change_a2 one, the consequence assignment silently
    did nothing, and the boxes it was meant to fill read as empty — which looked
    exactly like the repair having been considered and correctly skipped.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K: python locates and reads the file
    # -- `_CONSENSUS_SOURCE` STAYS, because it is the selftest's injection point
    # -- and `enforce/consensusDuplicates.ts` compares the RAW TEXT against the
    # parsed object. Reading the loaded object can never find a duplicate: the
    # parser has already discarded one of them.
    #
    # THE PARSE-ERROR ARM STAYS HERE, DELIBERATELY. Its message embeds the
    # PARSER'S own words, and python's differ from V8's. A ported check whose
    # finding text differs is indistinguishable, in a baseline diff, from a new
    # fault, so python parses first and the rule is only asked about text that
    # already parsed. Found by a control that accidentally produced invalid JSON.
    # SELF-ASSEMBLED. Subgoal E63: the runner builds this payload itself,
    # from the same course records python would have read. The assembler was
    # compared against the payload python used to send and found IDENTICAL
    # before this fetch was deleted; `runner.SELF_ASSEMBLING` names the rules
    # that comparison has cleared, and the runner refuses any other.
    import lo_enforce

    # PYTHON KEEPS THE FETCH. Self-assembly reads this from DISK; the
    # self-test injects into the IN-MEMORY table and forks, so a rebuilt
    # payload cannot see it and the case goes silent. Measured 2026-09-26.
    import os

    import lo_enforce
    import paths as _p_cs

    src = _CONSENSUS_SOURCE or os.path.join(
        str(_p_cs.roots().fixture_data), "CONSENSUS_SPANS.json")
    try:
        raw = open(src, encoding="utf-8").read()
    except OSError:
        return []                    # an absent fixture is another check's finding
    return lo_enforce.run("consensus_fixes_have_no_duplicate_cells",
                          {"raw": raw, "name": os.path.basename(src)})



# Whether each registered citation was MEASURED to be load-bearing. Keyed
# (item, pid) -> "necessary" | "untested".
#
# A registration says the prompt hands the grader that participant's answer, so
# scoring the cell measures recall. That is a claim about the PROMPT, and the way
# to test it is to rewrite the citation as the rule it illustrates and re-run the
# cell: if it still scores right without the answer in front of it, the citation
# was never load-bearing and both it and the registration go.
#
# Only two states belong here. A citation measured as UNNECESSARY is removed, and
# its cell counts — there is nothing left to record. `untested` is a promise with
# a name on it, and `check_citation_necessity_is_recorded` makes the silence
# impossible.
CITATION_NECESSITY: dict[tuple[str, int], str] = {}


def check_citation_necessity_is_recorded() -> list[str]:
    """Has anyone asked whether a citation is doing work, not just whether it exists?

    `check_citations_match_exclusions` holds the pair together: registered implies
    cited, cited implies registered. Neither direction asks the question that
    decides whether the registration is EARNED — does the citation actually hand
    the grader that participant's answer? A cell excluded on a citation that turns
    out to teach nothing is a cell subtracted from every rate for no reason, and
    nothing about it ever looks wrong, because the cell scores fine.

    The test is measurement, not inspection: rewrite the citation as the rule it
    illustrates, re-measure, and see whether the cell still scores right. That
    cannot run here — it needs the corpus and an endpoint. What CAN be enforced is
    that the answer was written down, so a registration cannot sit untested
    indefinitely while the guide claims step 0 was done.

    So: every registered cell needs an entry in CITATION_NECESSITY saying what the
    measurement showed. `unnecessary` cells should not be registered at all — they
    are removed, not recorded — so the table holds only `necessary` and `untested`,
    and `untested` is a backlog item with a name on it rather than a silence.
    """
    from forms import FORMS

    problems = []
    for h in _forms():
        registry = (FORMS[h].get("cited_participants") or {})
        for item, pids in sorted(registry.items()):
            for pid in sorted(pids):
                state = CITATION_NECESSITY.get((item, pid))
                if state is None:
                    problems.append(
                        f"H{h} {item}/p{pid} is registered in cited_participants "
                        f"with no CITATION_NECESSITY entry. Either measure whether "
                        f"the citation is load-bearing — rewrite it as its rule and "
                        f"re-run the cell — or record it as 'untested' so the "
                        f"backlog can see it")
                elif state not in ("necessary", "untested"):
                    problems.append(
                        f"H{h} {item}/p{pid}: CITATION_NECESSITY says {state!r}. "
                        f"Only 'necessary' and 'untested' belong here — a citation "
                        f"measured as unnecessary is REMOVED along with the "
                        f"registration, not recorded")
    for stale in sorted(CITATION_NECESSITY):
        item, pid = stale
        if not any(pid in (FORMS[h].get("cited_participants") or {}).get(item, [])
                   for h in _forms()):
            problems.append(
                f"CITATION_NECESSITY lists {item}/p{pid}, which is no longer "
                f"registered in cited_participants. Remove it")
    return problems


def check_items_are_measured_as_configured() -> list[str]:
    """Is each item's recorded number still the number of the CURRENT setup?

    A published rate means nothing apart from the prompt the grader was sent and
    the cells the rate was computed over, and both can change without leaving
    anything that looks changed. A rule rewrite is a diff among many in the same
    commit. Removing an exclusion DELETES the only record that the cell was ever
    in question. So an item whose prompt was rewritten and whose denominator grew
    is, in the tree, indistinguishable from an item nobody touched.

    Q1, on 2026-08-24: five exclusions removed and six citations rewritten into
    rules in one commit, no sweep afterwards, its number carried forward by
    re-derivation from a sweep that predated both. Two guards had landed that
    same day and neither could see it — `olx_prompts --write` warns at write time
    and prints to stderr, `compare_runs.py` only fires if someone runs it. The
    guide had said to measure, and had been read.

    This compares the ledger against the working tree: the SHA of the item's own
    OLX section, and its exclusion set. Either one moving makes the recorded
    number stale, and stale is reported as a difference rather than a warning,
    because the failure mode being defended against is precisely a true statement
    that nobody acted on.

    A gap may be DECLARED — `pending` with a reason — which is listed, not failed
    on, the same bargain the rest of this file offers. What it may not be is
    absent: an item with no entry at all is the Q1 state, and it fails.
    """
    import measured as MEAS

    # EVERY side that has recorded anything, not just the cli default. The two
    # can genuinely disagree, because `prompt_sha` is side-aware: `_olx_only_visible`
    # neutralises the open-tag attributes the python harness never reads, so a
    # change to one of THOSE leaves the cli fingerprint identical while the web's
    # moves. Read from the cli alone, this gate would then call an item current
    # while the number the web column publishes was measured against a different
    # prompt -- the exact statement it exists to prevent, and unsayable.
    #
    # No item is in that state today; the gap is structural, not observed. It is
    # closed now rather than after, because the failure is silent by construction:
    # a stale web number looks like a good one.
    problems = []
    seen: dict[str, str] = {}
    for side in MEAS.SIDES:
        try:
            rows = MEAS.status(side)
        except Exception:
            continue
        for item, state in rows:
            if state.startswith("ABSENT"):
                # ABSENT is reported for the DEFAULT side only. Every item is
                # expected to have a cli number; the paper sides are swept
                # separately and their absence is E28's business, not a gap here.
                if side != MEAS.DEFAULT_SIDE:
                    continue
                problems.append(
                    f"{item} has no entry in MEASURED.json. Sweep it and run "
                    f"`measured.py --record {item} OUT/{item}.runs.json`, or declare "
                    f"`pending` with a reason saying when it will be measured")
            elif state.startswith("STALE PROMPT"):
                if seen.get(item) == state:
                    continue          # both sides stale the same way: say it once
                seen[item] = state
                problems.append(
                    f"{item} [{side}]: {state}. Its prompt text changed since the "
                    f"recorded measurement, so the recorded number is not this "
                    f"prompt's number — re-sweep and re-record")
            elif state.startswith("STALE CELLS"):
                if seen.get(item) == state:
                    continue
                seen[item] = state
                problems.append(
                    f"{item} [{side}]: {state}. Its denominator changed since the "
                    f"recorded measurement, so the recorded number was computed "
                    f"over a different set of cells — re-sweep and re-record")
    return problems


# EVERY DECLARATION TABLE, AND THE CHECK THAT RE-TESTS IT.
#
# A declaration is a claim that something is true and will stay true. The claim
# is checkable or it is not; if it is, the check belongs here and not in
# somebody's memory. Coverage is what this registry enforces -- adding a table
# without naming a verifier fails the audit, which {{corpus:Q4b/p13:modify:42:58:sha=ed0e48693398}} prose
# guidance cannot do for itself.
#
# Written after a divergence asserting "the slot points sum to 4 against a max of
# 5" outlived the fix that made it false, with the whole audit green: no check
# owned it, and nothing said one was missing.
DECLARATION_TABLES: dict[str, tuple[str, tuple[str, ...]]] = {
    "enforcement.CARRIED_NOTES": (
        "the shape of the recorded reasoning carried out of the rubric modules "
        "and now living as OLX comments -- runs and lines per tag, so an edit is "
        "free and a loss is reported",
        ("check_carried_notes_are_intact",)),
    "enforcement.ASK_EQUIVALENT_PROMPTS": (
        "prompts whose served tag moved while the model's question did not, so "
        "artifacts stamped with the superseded sha are still evidence",
        ("check_ask_equivalences_still_hold",)),
    "enforcement.PROBE_UNREACHABLE_PAIRS": (
        "charge-once pairs the web declares and the CLI probe cannot discover",
        ("check_probe_unreachable_pairs_still_apply",)),
    # Registered 2026-09-16 with the check that re-tests it. The entries are
    # absolute literals that are PATTERNS -- globs a check searches FOR --
    # rather than locations anything reads from, which is the whole reason
    # they are exempt from the no-hard-coded-paths rule.
    "enforcement.ABSOLUTE_PATH_EXCEPTIONS": (
        "absolute literals that are patterns, not locations",
        ("check_filesystem_locations_come_from_paths_py",)),
    "forms.PER_ITEM_EXCLUDE": (
        "cells dropped from every rate",
        ("check_exclusion_claims_are_data", "check_citations_match_exclusions",
         "check_declarations_still_have_evidence")),
    "forms.CORRECTED_GOLD": (
        "the target a cell is measured against",
        ("check_corrected_gold_matches_the_sheet",
         "check_no_declaration_cites_a_suspect_cell")),
    "forms.GOLD_DIVERGENCES": (
        "cells we knowingly disagree with gold about",
        ("check_declarations_still_have_evidence",
         "check_no_declaration_cites_a_suspect_cell")),
    "forms.GOLD_CEILINGS": (
        "why an item cannot reach 100%",
        ("check_declarations_still_have_evidence",)),
    "enforcement.UNCHARGED_VERDICTS": (
        "verdicts the paper ledger deliberately does not charge",
        ("check_every_failing_verdict_has_a_charge",)),
    # TEN REGISTERED 2026-09-12. Every one already had a check that re-tests it;
    # what was missing was the registration saying WHICH, so a reader could not
    # tell a watched table from an unwatched one. Three of them --
    # ITEM_GATED_MECHANISMS, PARKED_UNDECLARED and ITEM_NOTES_WHY -- were created
    # in recent sessions and never registered, which is how the debt accrues:
    # the table gets a check on the day it is written and the registry does not.
    #
    # Only checks that genuinely RE-TEST each table are listed. Several others
    # merely mention one in passing (check_no_module_shadow_in_scratchpad reads
    # DESIGNED_TEXT, check_scorer_neutrality_is_verified reads
    # HAND_AUTHORED_ATTRS) and listing those would make the registry claim
    # coverage it does not have -- the same fault as a spent SCORER_NEUTRAL pair.
    "enforcement.APP_ONLY_SLOTS": (
        "slots the app asks that the rubric deliberately does not define",
        ("check_scored_slots_are_answered_by_both_engines",
         "check_sheet_slots_reach_the_rubric")),
    "enforcement.DECOMPOSITION_DIVERGENCES": (
        "slots one engine decomposes and the other does not",
        ("check_scored_slots_are_answered_by_both_engines",)),
    "enforcement.DESIGNED_TEXT": (
        "the prompt text a design decision put there, by field",
        ("check_designed_text_is_the_measured_text", "check_every_designed_entry_ships",
         "check_shipped_text_matches_design", "check_probed_fields_keep_their_text")),
    "enforcement.HAND_AUTHORED_ATTRS": (
        "sheet attributes written by hand rather than generated",
        ("check_generated_attributes_have_a_declaration",
         "check_hand_authored_attrs_still_suppress_something")),
    "enforcement.ITEM_GATED_MECHANISMS": (
        "mechanisms that vary by item, which the uniformity rule forbids",
        ("check_engine_mechanisms_are_not_item_dependent",)),
    "enforcement.SELFTEST_NAMED_FIXTURES": (
        "the self-test fixtures that name their target, each with the reason it "
        "is named rather than picked by shape",
        ("check_named_fixtures_still_name_something",)),
    "enforcement.RUBRIC_BUILDERS": (
        "the modules allowed to import the rubric -- the builder that writes "
        "the course file and the two tools that prove it reproduces them",
        ("check_only_builders_read_the_rubric",)),
    "enforcement.COURSE_DATA_REENTRY": (
        "a count re-recorded once after an exemption was removed, with the "
        "number it re-entered at and why",
        ("check_course_data_reentries_are_current",
         "check_module_has_no_course_data")),
    "enforcement.DATA_MODULES": (
        "modules that ARE authored course data, exempt from the engine ratchet",
        ("check_module_has_no_course_data",)),
    # KEYED `enforcement.`, like every other `_declaration`-backed table
    # (`COUNTABLE_EXEMPT`, `PROBE_UNREACHABLE_PAIRS`). The key names the module
    # the check READS it from, not the one that authors it -- authoring lives in
    # `declaration_source.py` for all of them.
    "enforcement.CORPUS_QUOTE_BACKLOG": (
        "cells whose prompt reproduces that participant's own words",
        ("check_rule_examples_are_not_corpus",)),
    "enforcement.OVERLAP_SIBLING_ROLES": (
        "box roles that may legitimately hold the same clause",
        ("check_consensus_spans_are_disjoint",)),
    "enforcement.RECORD_DESTINATIONS": (
        "where each record writer puts its output, and the class it must be in",
        ("check_record_writers_target_the_right_place",)),
    "enforcement.HAND_AUTHORED_SHEET_ATTRS": (
        "sheet attributes no generator produces, and why each may be",
        ("check_olx_attributes_are_all_generated",)),
    "enforcement.OLD_ENV_NAMES_ALLOWED": (
        "the one place the pre-Stage-9 environment names may still appear",
        ("check_no_old_environment_names",)),
    "enforcement.MIGRATED_MODULES": (
        "modules declared free of course data, and what makes the claim true",
        ("check_module_has_no_course_data",)),
    "enforcement.PARKED_UNDECLARED": (
        "findings deliberately deferred rather than declared",
        ("check_parked_entries_still_apply",)),
    "enforcement.VERDICT_ABSENCE_ENCODING": (
        "how each engine spells 'no verdict here'",
        ("check_engines_encode_an_unrecorded_verdict_alike",)),
    "enforcement.VERDICT_PAIRS": (
        "verdict tokens that mean the same thing on the two sides",
        ("check_verdict_vocabularies_correspond",)),
    "measured.DECLARED_CEILING_CELLS": (
        "cells declared unreachable, with the reason",
        ("check_closure_ceilings_are_declared",)),
    "olx_prompts.ITEM_NOTES_WHY": (
        "why an item carries a web-only note",
        ("check_side_notes_are_side_specific",)),
    # Verified by the probe ITSELF, which is the only thing that can: a
    # provocation that stops provoking makes its table read INCONCLUSIVE, and a
    # PROBE_IMPOSSIBLE reason that stops being true makes the table probeable and
    # its entry stale. The verifier runs on demand (`--probe-declarations`) rather
    # than in the default audit, because three passes over every table is minutes.
    "enforcement.PROBE_PROVOCATIONS": (
        "an entry each verifier must object to, so the table can be probed",
        ("probe_declaration_tables",)),
    "enforcement.PROBE_IMPOSSIBLE": (
        "tables no provocation can move, with the reason",
        ("probe_declaration_tables",)),
    "measured.GOLD_SLOT_CHARGES": (
        "which slots each grader phrasing charges",
        ("check_slot_sets_match_gold",)),
    "measured.GOLD_SLOT_DISAGREEMENTS_KNOWN": (
        "cells failing different slots from the ones gold charged",
        ("check_slot_sets_match_gold",
         "check_no_declaration_cites_a_suspect_cell")),
    # FOUR TABLES IN THIS MODULE that were invisible until E36 made the scan see
    # EMPTY containers. All four are empty today and all four have a real check
    # already reading them -- so they were unregistered rather than unverified,
    # and the registry could not say so.
    "enforcement.CITATION_NECESSITY": (
        "what each registered citation is necessary FOR",
        ("check_citation_necessity_is_recorded",)),
    "enforcement.FIXTURE_GAP_BACKLOG": (
        "fixture gaps accepted for now, with the reason",
        ("check_fixture_covers_the_response",)),
    "enforcement.FIXTURE_GOLD_OVERRIDES": (
        "cells where the fixture and gold disagree on purpose",
        ("check_fixture_agrees_with_gold",)),
    "enforcement.FIXTURE_STRUCTURE_OVERRIDES": (
        "boxes deliberately cut against the response's structure",
        ("check_fixture_follows_response_structure",)),
    # olx_prompts' OWN DOCSTRING calls these declared deviations: "everything the
    # web sends that the CLI does not, or vice versa, is a DEVIATION. Each is
    # declared here -- in WEB_SYSTEM's rule table, RESPONSE / CONTEXT,
    # OMIT_CREDIT / OMIT_DEDUCTION / OMIT_GUIDANCE, or ITEM_NOTES." They are
    # registered on that authority rather than exempted against it.
    "olx_prompts.RESPONSE": (
        "how each item's response is presented to the web grader",
        ("check_prompt_deviation_tables_are_current",)),
    "olx_prompts.CONTEXT": (
        "context the web is given that the CLI is not",
        ("check_prompt_deviation_tables_are_current",)),
    "olx_prompts.ITEM_NOTES": (
        "per-item prose the web carries and the CLI does not",
        ("check_prompt_deviation_tables_are_current",)),
    "olx_prompts.OMIT_CREDIT": (
        "credit components deliberately left out of the web prompt",
        ("check_prompt_deviation_tables_are_current",)),
    "olx_prompts.OMIT_DEDUCTION": (
        "deduction codes deliberately left out of the web prompt",
        ("check_prompt_deviation_tables_are_current",)),
    "olx_prompts.OMIT_GUIDANCE": (
        "guidance lines deliberately not carried to the web, with reasons",
        ("check_prompt_deviation_tables_are_current",)),
    "measured.GOLD_CODE_CHARGES": (
        "which deduction code each grader phrasing charges on a criteria item",
        ("check_slot_sets_match_gold",)),
    "measured.SILENT_GOLD_DIVERGENCES": (
        "silent-gold full marks we refuse, read out and declared",
        ("check_no_declaration_cites_a_suspect_cell",)),
    "measured.GOLD_CODE_KNOWN": (
        "criteria cells where our deduction code differs from gold's",
        ("check_slot_sets_match_gold",
         "check_no_declaration_cites_a_suspect_cell")),
    "measured.GOLD_SLOT_BOUNDS_KNOWN": (
        "cells whose ambiguous gold charge disagrees with us on every reading",
        ("check_slot_sets_match_gold",
         "check_no_declaration_cites_a_suspect_cell")),
    "measured.GOLD_SLOT_UNMAPPABLE": (
        "grader deductions no slot set can account for",
        ("check_slot_sets_match_gold",)),
    "enforcement.VERDICT_SPACE_DIVERGENCES": (
        "shapes in which the two scorers' verdict spaces differ",
        ("check_verdict_spaces_are_declared",)),
    "olx_prompts.SCORING_DIVERGENCES": (
        "where the two scorers deliberately differ",
        ("check_divergence_arithmetic_is_still_true",
         "check_declarations_still_have_evidence")),
    "enforcement.UNEXERCISED_PRIMITIVES": (
        "primitives no live app run has exercised",
        ("check_closed_goals_that_changed_code_were_exercised",)),
    "enforcement.SLOT_RULE_BACKLOG": (
        "rules the paper scorer cannot see",
        ("check_slot_rules_backlog_is_being_cleared",)),
    "enforcement.HANDCODED_ITEM_RULES": (
        "rules hand-written in python rather than declared",
        ("check_handcoded_rules_are_being_cleared",)),
    "enforcement.PROSE_ONLY_SLOTS": (
        "rules the audit cannot compare because they are prose",
        ("check_prose_only_slots_are_declared",
         "check_prose_only_claims_are_current")),
    "enforcement.PROSE_ONLY_JUDGED_AGAINST": (
        "the primitive set each NOT CONVERTIBLE claim was judged against",
        ("check_prose_only_claims_are_current",)),
    "enforcement.GOLD_ALPHABET_EXEMPT": (
        "functions comparing our slot set against gold's without a vocabulary "
        "guard, on purpose",
        ("check_gold_comparisons_share_an_alphabet",)),
    "enforcement.FORM_KEYED_GOLD_READERS": (
        "modules that pick a gold loader by handout number instead of by item",
        ("check_gold_is_read_by_item",)),
    "enforcement.RAW_GOLD_READERS": (
        "modules that read gold uncorrected, on purpose",
        ("check_gold_accounting_is_uniform",)),
    "measured.SCORER_NEUTRAL": (
        "scorer changes verified not to move any recorded score",
        ("check_scorer_neutrality_is_verified",)),
    "measured.WEB_CODE_NEUTRAL": (
        "web rendering-code changes verified not to move any recorded score",
        ("check_web_code_neutrality_is_verified",)),
    "measured.SIDE_CONTRACT": (
        "which program and model each ledger side is allowed to be recorded from",
        ("check_side_contract_is_enforced",)),
    "olx_prompts.PROBE_REACH_LIMITS": (
        "rules neither instrument can cross-check, so their cross-engine "
        "agreement is asserted rather than probed",
        ("check_probe_reach_limits_still_apply",)),
    "enforcement.COMPUTE_EXEMPT": (
        "primitives one engine cannot compute",
        ("check_both_engines_compute_the_same_primitives",)),
    # Found by this check's own reverse pass on the day it was written: three
    # tables that were being enforced but not registered, so nothing said whether
    # anything watched them. All three did have a verifier; none of them said so.
    "enforcement.CONSENSUS_OVERLAP_BACKLOG": (
        "overlapping consensus spans accepted as faithful",
        ("check_consensus_spans_are_disjoint",)),
    "enforcement.COUNTABLE_EXEMPT": (
        "countable families deliberately not converted to `counts`",
        ("check_countable_families_converted",)),
    "enforcement.GOLD_BOX_WORDS": (
        "what the graders CALL each box, and what their wording must not say",
        ("check_fixture_agrees_with_gold",)),
    "enforcement.MULTI_BLOCK_DECLARED": (
        "items whose response is split across blocks on purpose",
        ("check_single_box_fixtures_are_verbatim",)),
    "enforcement.SYSTEM_PROMPT_DIVERGENCES": (
        "system-prompt rules the two scorers must state differently",
        ("check_system_prompts_are_parallel",)),
    "enforcement.SLOT_STRUCTURE_DIVERGENCES": (
        "slots whose gate/points structure is deliberately not uniform in a family",
        ("check_sibling_slots_share_their_structure",)),
    "enforcement.SLOT_STRUCTURE_FAMILIES": (
        "which items count as siblings for the structure check",
        ("check_sibling_slots_share_their_structure",)),
}


# The numbered system-prompt rules that MUST differ between the two scorers,
# with the mechanism that forces each difference. A rule not listed here has to
# be identical on both sides.
#
# The two prompts ask for different SHAPES -- the web returns a `checks` sheet
# and student-facing feedback, the paper scorer returns a deduction ledger -- so
# the rules describing that shape cannot be shared. What must not differ is the
# GRADING STANCE: how generous to be, what counts as absent, how to treat an
# empty response. Rule 5 carries that and is byte-identical on both sides today.
SYSTEM_PROMPT_DIVERGENCES: dict[str, str] = {
    "1": "output shape: the web judges check-by-check and fills each check's "
         "`evidence`; the paper scorer awards credit component-by-component. "
         "There is no checks sheet on the paper side to judge against",
    "2": "the web is told the deduction table is NOT a ledger to fill in, "
         "because it writes prose feedback from it; the paper scorer's entire "
         "output IS that ledger, keyed by code",
    "3": "same rule, different noun -- the score is computed from `checks` on "
         "the web and from the deduction ledger on paper",
    "4": "consistency is stated against the artifact each side produces: "
         "feedback-vs-checks on the web, deductions-vs-unmet-components on paper",
    "6": "an empty response marks every check unsatisfied on the web, and takes "
         "the item's none/did-not-answer CODE on paper -- the web has no code to "
         "take",
    "7": "safety: the web has no `safety_flag` field, so the remark goes in "
         "`feedback`; the paper scorer sets the flag. Same trigger list, "
         "different destination",
    "8": "escalation: the paper schema has `escalate` and the web's does not, so "
         "the web routes the same situation into `feedback` and sets `confident` "
         "absent. The web's rule 8 states that mapping in terms",
}


def check_system_prompts_are_parallel() -> list[str]:
    """Do the two scorers' SYSTEM prompts still say the same things?

    `score.SYSTEM_TMPL` and `olx_prompts.WEB_SYSTEM` are two hand-maintained
    prompts, and until this check nothing compared them. equivalence.py imports
    SYSTEM_TMPL only to PRINT it. So a substantive rule added to one side --
    about hedged answers, or what counts as naming a thing -- would reach one
    scorer and silently not the other, with every audit green.

    That is the SLOT_NOTES failure in a different file, and it is the one this
    codebase has already paid for once: Q4b's five substitution tests reached the
    web and CLI and left score.py behind while `--item Q4b` reported "missing 0".

    The two prompts ask for different SHAPES and always will -- a checks sheet
    and student feedback on one side, a deduction ledger on the other -- so
    difference is not the finding. An UNDECLARED difference is, and so is a
    declaration that has gone stale because the two sides converged.
    """
    import re as _re

    import olx_prompts as _OP
    import score as _S

    def _rules(text: str) -> dict:
        return {m.group(1): " ".join(m.group(2).split())
                for m in _re.finditer(r"^(\d+)\. (.*?)(?=^\d+\. |\Z)",
                                      text, _re.S | _re.M)}

    web, paper = _rules(_OP.WEB_SYSTEM), _rules(_S.SYSTEM_TMPL)
    problems = []
    for n in sorted(set(web) | set(paper), key=int):
        w, p = web.get(n), paper.get(n)
        declared = n in SYSTEM_PROMPT_DIVERGENCES
        if w is None or p is None:
            side = "the paper scorer" if w is None else "the web"
            if not declared:
                problems.append(
                    f"system prompt rule {n} exists only on {'the web' if p is None else 'the paper side'} "
                    f"-- a rule one scorer is told and the other is not. Add it to "
                    f"the other prompt, or declare it in "
                    f"SYSTEM_PROMPT_DIVERGENCES with the mechanism that forces it")
            continue
        if w == p:
            if declared:
                problems.append(
                    f"SYSTEM_PROMPT_DIVERGENCES declares rule {n} must differ "
                    f'("{SYSTEM_PROMPT_DIVERGENCES[n][:60]}...") but the two '
                    f"prompts now say it identically -- retire the entry, or the "
                    f"table stops meaning anything")
            continue
        if not declared:
            problems.append(
                f"system prompt rule {n} DIFFERS between the two scorers and is "
                f"not declared.\n      web  : {w[:110]}\n      paper: {p[:110]}\n"
                f"      If the difference is forced by the output shape, declare "
                f"it in SYSTEM_PROMPT_DIVERGENCES; if not, make them agree")
    return problems


def check_prompt_deviation_tables_are_current() -> list[str]:
    """Do the declared web/CLI deviations still name things that exist?

    olx_prompts' module docstring makes these six tables the contract -- "a
    difference that is in neither place is a bug" -- and until E36 not one of them
    was registered, so nothing re-tested a single entry. An omission that names a
    guidance line the rubric no longer has, or a note for an item that has left
    JOBS, reads as a standing reason for a difference that no longer exists.

    Three things are checkable without judging any prose:
      * every key names a live item;
      * every OMIT_CREDIT / OMIT_DEDUCTION key names a credit component or
        deduction code the rubric still has;
      * every OMIT_GUIDANCE phrase still matches a guidance line -- which
        resolve_guidance_omissions already enforces at generation time, so this
        is the same test asked before a sweep rather than during one.
    """
    # Course data the engine can read for itself.
    import lo_enforce

    return lo_enforce.run("prompt_deviation_tables_are_current", None)


def check_every_declaration_table_has_a_verifier() -> list[str]:
    """Is every declaration table re-tested by something?

    THE PRINCIPLE, stated once here and in QUALITY_CONTROL.md section 5: a
    declaration that asserts something mechanically checkable must carry that
    assertion as DATA, so the audit can re-test it -- and every table of
    declarations must be named in DECLARATION_TABLES against the check that does
    the re-testing.

    Prose cannot enforce itself. The failure this exists for is not a wrong
    declaration; it is a declaration nobody is looking at, which is invisible
    precisely because everything is green. Two of those turned up in one day:
    a divergence whose arithmetic had been fixed under it, and -- outside the
    audit entirely -- a shell mitigation that went on killing four sweep items
    for an hour after the defect it guarded against was repaired.

    Named checks must EXIST. A table pointing at a function that has been renamed
    or deleted is the same hole with a comment over it.
    """
    import forms as _H
    import importlib
    import measured as _MEAS
    import olx_prompts as _OP

    # `measured` was absent, so a declaration table living there could not be
    # resolved and the registry reported it as a table nobody has -- which is
    # indistinguishable from the failure this check exists to catch. Found by
    # registering GOLD_SLOT_CHARGES and being told it did not exist.
    mods = {"forms": _H, "olx_prompts": _OP, "measured": _MEAS,
            "enforcement": sys.modules[__name__]}
    problems = []
    for path, (what, verifiers) in sorted(DECLARATION_TABLES.items()):
        mod_name, _, attr = path.partition(".")
        mod = mods.get(mod_name)
        if mod is None or not hasattr(mod, attr):
            problems.append(
                f"DECLARATION_TABLES names {path} ({what}) but it does not "
                f"exist -- the table was renamed or removed and its entry was "
                f"not, so the registry is describing a table nobody has")
            continue
        if not verifiers:
            problems.append(
                f"{path} ({what}) is declared with NO verifier. A declaration "
                f"nobody re-tests subtracts itself from every rate for as long "
                f"as it survives")
            continue
        for fn in verifiers:
            if not callable(globals().get(fn)):
                problems.append(
                    f"{path} names `{fn}` as its verifier and no such check "
                    f"exists -- renamed or deleted, leaving the table unwatched")

    # And the other direction: a declaration table that nobody registered.
    # `measured` TOO. This scanned only this module, so a declaration table added
    # to measured.py, forms.py or olx_prompts.py was never reported as
    # unregistered -- and that is not hypothetical: four tables were added to
    # measured.py on 2026-08-31 and the audit asked for none of them. Three were
    # registered by hand and the fourth was forgotten, with nothing complaining.
    #
    # ALL FOUR MODULES as of E36. The scan covered enforcement only, then
    # enforcement and measured; handouts and olx_prompts hold registered
    # declarations already -- CORRECTED_GOLD, GOLD_DIVERGENCES, PER_ITEM_EXCLUDE,
    # SCORING_DIVERGENCES -- so they were exactly the files most likely to gain
    # an unregistered one.
    for mod_name in ("enforcement", "measured", "forms", "olx_prompts"):
        mod = (sys.modules[__name__] if mod_name == _SELF_MODULE
               else importlib.import_module(mod_name))
        for attr in dir(mod):
            if attr.startswith("_") or not attr.isupper() or attr.endswith("_BUDGET"):
                continue
            val = getattr(mod, attr)
            # EMPTY COUNTS. `not val` used to skip here, so an emptied table could
            # also be unregistered with nothing noticing -- and olx_prompts'
            # OMIT_CREDIT and OMIT_DEDUCTION are empty right now, so the two
            # tables its own docstring calls declarations were doubly invisible.
            if not isinstance(val, (dict, list)):
                continue
            path = f"{mod_name}.{attr}"
            if path in DECLARATION_TABLES or path in _NOT_DECLARATIONS:
                continue
            problems.append(
                f"{path} looks like a declaration table and is not in "
                f"DECLARATION_TABLES -- register it with the check that "
                f"re-tests it, or add it to _NOT_DECLARATIONS saying why it is "
                f"not a declaration")
    return problems


# Upper-case module data that is NOT a declaration, WITH THE REASON EACH TIME.
#
# This was a flat set of bare NAMES under one blanket comment -- "constants,
# vocabularies and lookup tables assert nothing about the corpus". Two problems,
# both found by E36:
#
#   EXEMPTION BY BARE NAME leaks across modules. "RESPONSE" exempted the name
#   everywhere, so if one module's CONTEXT were a declaration and another's data,
#   a single entry would silence both. Keyed by `module.ATTR` now.
#
#   NO PER-ENTRY REASON meant the blanket claim covered entries it does not fit.
#   olx_prompts' own module docstring says "everything the web sends that the CLI
#   does not is a DEVIATION. Each is declared here -- in WEB_SYSTEM's rule table,
#   RESPONSE / CONTEXT, OMIT_CREDIT / OMIT_DEDUCTION / OMIT_GUIDANCE, or
#   ITEM_NOTES". So the docstring calls seven tables declarations while this set
#   exempted two of them as data. Two statements in the tree, disagreeing, and no
#   recorded reason for either.
_NOT_DECLARATIONS: dict[str, str] = {
    # enforcement: vocabularies and lookups.
    "enforcement.ALIAS": "maps a CLI slot key to its web name; a naming table, "
                         "not a claim about the corpus",
    "enforcement.DEFAULT_VERDICTS": "the verdict list a slot gets when it names "
                                    "none; a default, not a claim",
    "enforcement.KNOWN_ACTION_ATTRS": "the attribute allowlist; its own check "
                                      "(check_action_attributes_are_declared_in"
                                      "_the_block) reads it as INPUT",
    "enforcement.KNOWN_VERDICTS": "the scan vocabulary for verdict tokens",
    "enforcement.EXCLUSION_KINDS": "the kinds an exclusion may have; a schema",
    "enforcement.ARTIFACT_WRITERS": "which programs write artifacts and what "
                                    "each must stamp; read as input by the era "
                                    "check",
    "enforcement.GENERATED_ATTRS": "which OLX attributes the generator writes",
    "enforcement.SCORER_PARTS": "the source spans the scorer fingerprint covers",
    "enforcement.DECLARATION_TABLES": "the registry itself, not a declaration in "
                                      "it",
    # handouts / olx_prompts / rubric: structural data.
    "forms.MATERIALS": "where the submission files are",
    "forms.FORMS": "the form numbers",
    "forms.H1_MARKERS": "the section markers that split a .docx into items. "
                           "Parsing configuration -- a marker that stops matching "
                           "breaks the FIXTURE, which the fixture checks own",
    "forms.H2_MARKERS": "as H1_MARKERS",
    "forms.H3_MARKERS": "as H1_MARKERS, and regexes rather than literals",
    "olx_prompts.ACTION": "item id -> LLMAction id; a lookup",
    "olx_prompts.SHEET_ONLY": "items whose grader is a sheet with no action",
    "olx_prompts.FORM": "item id -> form number",
    "olx_prompts.SUBS": "text substitutions applied to generated prose",
    "olx_prompts.TOTAL": "the points wording",
    "olx_prompts.MAPS": "parsed `maps` rules; derived from the OLX, not authored",
    "olx_prompts.READS_UTB_CHOICE": "which items read the chosen UTB",
    "olx_prompts.VERBATIM_RULES": "prose reproduced identically on both sides -- "
                                  "the OPPOSITE of a deviation, so there is "
                                  "nothing to declare",
    "olx_prompts.PRIMITIVES_JSON": "the path to primitives.json",
    "olx_prompts.REF_IDS": "minted <Ref> ids, generated and checked by --refs",
    "olx_prompts.EVIDENCE": "the evidence bundle text for 1c; prompt content",
    "olx_prompts.MATCH_DEF": "the matching definitions rendered into prompts; "
                             "prompt content, and its equivalence is covered by "
                             "the prompt-text checks",
    "olx_prompts.SLOT_NOTES": "olx-only judging prose. NOT waved through: it "
                              "reaches a prompt and its entries ARE declared -- "
                              "by enforcement.SLOT_RULE_BACKLOG, which lists them "
                              "and carries the budget. The BACKLOG is the "
                              "declaration and this is the data it declares, so "
                              "registering both would be two names for one claim",
    "olx_prompts.FRAGMENTS": "the prompt's own prose, READ from the rubric -- "
                             "`<Frame name=\"fragment:KEY\">` -- and not a claim "
                             "about this course at all. A declaration says "
                             "something is knowingly true of these items; this "
                             "says what a section heading is called. Nothing here "
                             "can be right or wrong about the corpus, so there is "
                             "no check that could re-test it. It is the same "
                             "shape as SLOT_NOTES above and exempt for a "
                             "DIFFERENT reason: that one IS declared elsewhere, "
                             "this one is not a declaration",
    "rubric_h1.ITEMS": "the rubric itself", "rubric_h2.ITEMS": "the rubric itself",
    "rubric_h3.ITEMS": "the rubric itself",
    "rubric_h1.BY_ID": "an index of the rubric",
    "rubric_h2.BY_ID": "an index of the rubric",
    "rubric_h3.BY_ID": "an index of the rubric",
}


def check_divergence_arithmetic_is_still_true() -> list[str]:
    """Declared divergences that assert ARITHMETIC the sheet no longer does.

    `check_declarations_still_have_evidence` retires a declaration whose CELLS
    stopped erroring. It cannot see this class: a divergence that asserts a fact
    about the sheet's own configuration -- "the assignable slot points sum to 4
    against an item max of 5" -- predicts no per-cell miss at all. Q4a's entry
    even carries `enforcement: "none"`, so nothing was looking at it from any
    direction.

    That entry went false the moment `max="5"` was added to Q4a, and the whole
    audit stayed green: the sheet now reaches 5, which is precisely what the
    declaration says it cannot. A stale declaration of this kind is worse than a
    stale per-cell one, because it reads as a standing reason not to fix
    something that is already fixed.

    So the arithmetic is recomputed from the OLX and the rubric and compared
    against the claim. `web_max` is the `max=` attribute when the action declares
    one and the sum of the scored slots otherwise -- the same rule the app
    applies.
    """
    import re as _re
    import pathlib as _pl

    import agreement_app as _A
    import olx_prompts as _OP
    rubric_h1, rubric_h2, rubric_h3 = _rubric_views()

    RB = {1: rubric_h1, 2: rubric_h2, 3: rubric_h3}
    olx = {f.name: f.read_text() for f in _p7.handout_olx_paths()}

    def _maxes(item):
        J = _A.JOBS.get(item) or {}
        g = J.get("grader") or ""
        if not g:
            return None, None
        act = g.replace("_grader", "_llm")
        tag = None
        for txt in olx.values():
            m = _re.search(r"<LLMAction\b(?:(?!</?LLMAction)[^>])*?(?:^|\s)id=\""
                           + _re.escape(act) + r"\"(?:(?!</?LLMAction)[^>])*>", txt, _re.S)
            if m:
                tag = m.group(0)
                break
        if tag is None:
            return None, None
        sm = _re.search(r'slots="([^"]*)"', tag, _re.S)
        slot_sum = sum(float(x.group(1)) for part in (sm.group(1).split("|") if sm else [])
                       for x in [_re.search(r"@([0-9.]+)", part)] if x)
        mx = _re.search(r'(?:^|\s)max="([^"]*)"', tag)
        web_max = float(mx.group(1)) if mx else slot_sum
        rb = RB[J["handout"]].BY_ID.get(item) or {}
        return web_max, rb.get("max")

    # "sum to 4 against an item max of 5", "web_max ... is 4 while the rubric max is 5"
    CLAIM = _re.compile(r"sum to (\d+(?:\.\d+)?)\b.*?max of (\d+(?:\.\d+)?)", _re.S | _re.I)
    problems = []
    for entry in getattr(_OP, "SCORING_DIVERGENCES", []):
        blob = " ".join(str(entry.get(k) or "") for k in ("what", "why"))
        m = CLAIM.search(blob)
        if not m:
            continue
        claimed_web, claimed_rubric = float(m.group(1)), float(m.group(2))
        for item in entry.get("items") or []:
            web_max, rubric_max = _maxes(item)
            if web_max is None:
                continue
            if (web_max, rubric_max) != (claimed_web, claimed_rubric):
                problems.append(
                    f"SCORING_DIVERGENCES declares for {item}: "
                    f'"{str(entry.get("what"))[:70]}" -- claiming web_max '
                    f"{claimed_web:g} against rubric max {claimed_rubric:g}. The "
                    f"sheet now computes web_max {web_max:g} against rubric max "
                    f"{rubric_max:g}. The divergence was FIXED and the declaration "
                    f"outlived it; retire the entry")
    return problems


def check_slot_sets_match_gold() -> list[str]:
    """Do we fail the slots gold charged, or just the right NUMBER of them?

    E30. Every rate compares totals, so a cell failing the wrong slots in the
    right quantity agrees with gold everywhere it is looked at. Q6/p5 is the
    demonstration and 8 of Q6's 12 mappable cells do it.

    Thresholds and the phrase table live in measured.GOLD_SLOT_CHARGES, next to
    the gold reading they interpret.
    """
    import measured as MEAS
    return MEAS.gold_slot_disagreements()


def check_declarations_still_have_evidence() -> list[str]:
    """Declarations the recorded measurements have outgrown.

    A declaration is a prediction: a divergence predicts a miss we mean to keep,
    a ceiling predicts an item cannot be perfect, an exclusion predicts a cell
    should not count. Predictions expire, and an expired one leaves no trace —
    the cell has stopped producing an error, so there is nothing to notice. It
    just subtracts itself from every rate, indefinitely.

    Section 5's reduce-the-declarations schedule is the manual version of this
    check, and running it by hand is how 25 unnecessary registrations survived
    several passes of a guide that told someone to look. So the ledger's per-cell
    record — which includes the EXCLUDED cells, since those are still run and
    still scored — is compared against the declaration tables on every audit.

    Thresholds live in `measured.declaration_conflicts`, and follow Q2/p17:
    fewer than six recorded runs buys a demand for a probe, not a retirement.
    """
    import measured as MEAS

    return MEAS.declaration_conflicts()


def check_prose_numbers_match_the_ledger() -> list[str]:
    """A score written into the repo's prose that the ledger contradicts.

    A measurement travels as a sentence — in a guide, a backlog entry, a note in
    forms.py — and the sentence outlives the configuration it was computed
    over. Q4c and Q5 were described in writing as perfect items while they stood
    at 12/14 and 14/15, because their denominators had grown underneath the
    prose. Nothing about a stale sentence looks stale.

    Guarding this with advice was tried first, on the day 1a was reported at
    18/20 off runs of 17, 17, 18 — the median was 17 and 18 was the flattering
    pick. Advice is what the reader already agreed with before misreading the
    table, so the number now comes from `measured.py --report` and this check
    verifies the prose against the same ledger.

    Narrow on purpose (see `measured.prose_claims`): an item name, a fraction
    beside it, the CURRENT denominator, and a disagreeing numerator. History
    keeps its old figures.
    """
    import measured as MEAS

    return MEAS.prose_claims()


def check_contains_matcher_agrees_across_engines() -> list[str]:
    """The Python and TypeScript `contains` matchers, on one shared table.

    The matcher exists twice on purpose. It cannot be imported into the browser,
    and it cannot depend on a dictionary or a spell-checker, because the engine
    the student actually meets has neither -- which is why the rule compares a
    typed token against the TARGET WORD rather than asking whether it is English.

    Two implementations of one rule is the divergence class this whole project
    exists to close, so neither side owns the cases: both read
    `containsCases.json`. The vitest suite asserts the TS side against it and this
    asserts Python against the identical file, so a change to either engine that
    is not made to the other fails here.
    """
    import json

    import olx_prompts as OP
    import paths as P

    path = P.LO / "packages/shared/lib/llm/containsCases.json"
    try:
        cases = jsoncache.load(path)
    except Exception as e:
        return [f"the shared `contains` case table cannot be read at {path}: "
                f"{type(e).__name__}: {e} -- the TS side is still asserting "
                f"against it, so Python is now unchecked"]
    if len(cases) < 10:
        return [f"the shared `contains` table has only {len(cases)} case(s), too "
                f"few to have exercised the matcher -- it is reporting clean "
                f"because it is barely asking anything"]
    out = []
    for c in cases:
        hit, _typed = OP.contains_hit(c["text"], c["words"])
        if bool(hit) != bool(c["met"]):
            out.append(f"`contains` disagrees across engines on {c['why']}: "
                       f"{c['text']!r} against {c['words']} -- TS says "
                       f"{'met' if c['met'] else 'absent'}, Python says "
                       f"{'met' if hit else 'absent'}")
    return out


def check_side_contract_is_enforced() -> list[str]:
    """Does `record` still refuse an artifact from the wrong program or model?

    The contract is the thing that keeps a ledger column meaning one comparison.
    `cli` is the python scorer on the SAME model as the web, so a web/cli
    difference isolates the PROGRAM; `paper_opus` exists so that varying the
    model is never folded into a column that also varies the path.

    Both halves failed on 2026-09-01, undetected at the time: an Opus run was
    recorded as `cli` and an agreement.py run as `web`. The analysis built on top
    then concluded the web/cli axis was model-versus-model, which was an artifact
    of the mislabelling and nothing else. Advice would not have caught it -- the
    sweep commands looked right -- so it is enforced at the point of recording.

    This asks whether that enforcement is still wired in, rather than re-testing
    the comparison: the selftest injects the breakages.
    """
    import inspect

    import measured as MEAS

    out = []
    for side in MEAS.SIDES:
        if side not in MEAS.SIDE_CONTRACT:
            out.append(f"side {side!r} is recordable but SIDE_CONTRACT does not "
                       f"say which program and model it may come from")
    try:
        src = inspect.getsource(MEAS.record)
    except Exception as e:
        return out + [f"cannot read measured.record: {type(e).__name__}: {e}"]
    if "_check_side_contract" not in src:
        out.append("measured.record no longer consults _check_side_contract, so "
                   "an artifact from the wrong model or the wrong program can be "
                   "recorded into a ledger column in silence")
    return out


def check_recorded_sides_are_readable() -> list[str]:
    """Every recorded side must have a findable artifact.

    The ownership check walks cells, so a side whose artifact cannot be read
    contributes no findings -- identical, in its output, to a side that scores
    everything right. On 2026-09-01 the first `paper` column recorded was
    unreadable (its `out` pointer named "runs" rather than "e25_paper/runs",
    because the pointer stored a basename and sweep_paper.sh folds one level
    deeper), and the ownership check reported a clean corpus with five Q4a cells
    wrong. Readability is therefore asserted, not inferred from silence.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K, and this one answers the user's
    # correction directly: a MEASUREMENT question can be generic. "Is the
    # artifact behind a recorded column readable?" is about the shape of what
    # was recorded, not about this course.
    #
    # PYTHON STILL RESOLVES WHICH ARTIFACT. The ledger owns that -- its `out`
    # pointer and goal O's `folded_from` -- and a second resolver in TypeScript
    # is the divergence this project exists to close. TS reads the file through
    # `courseData`, which refuses a path outside $COURSE_DATA.
    # SELF-ASSEMBLED. Subgoal E63: the runner builds this payload itself,
    # from the same course records python would have read. The assembler was
    # compared against the payload python used to send and found IDENTICAL
    # before this fetch was deleted; `runner.SELF_ASSEMBLING` names the rules
    # that comparison has cleared, and the runner refuses any other.
    import lo_enforce

    return lo_enforce.run("recorded_sides_are_readable", None)



@functools.lru_cache(maxsize=4)
def _idmap_parsed(path: str, mtime: float, size: int) -> dict:
    """The idmap dump's idMap, parsed once per (file, mtime, size).

    The dump is 5.8 MB and json.loads of it costs ~0.18s, which the prompt check
    paid on every call -- ~9s across the 51 audits the self-test runs. Keyed on
    mtime AND size rather than path alone, so re-taking the dump invalidates it:
    the whole point of that check is to notice when the served prompt has moved,
    and a cache that outlived a re-take would defeat it.

    Safe to cache without a seam, unlike the GOALS.md parse: the self-test
    injects its breakages into SOURCE, never into this dump.
    """
    import json

    return json.loads(pathlib.Path(path).read_text()).get("idMap") or {}


def check_engines_score_identical_verdicts_alike() -> list[str]:
    """RETIRED 2026-09-24 with the python web engine. ALWAYS RETURNS [].

    It watched: identical verdicts produced identical scores on both engines.

    THAT QUESTION NO LONGER HAS TWO SIDES. The python mirror of
    `scoreSlotSheet` was eliminated in goal O, so this would compare a
    thing against itself or against nothing. O's own text named the
    class: "a check that exists to catch drift between two
    implementations is dead weight once there is one implementation".

    KEPT AS A RECORD rather than deleted, so what STOPPED being watched
    stays legible -- the same treatment as
    `check_no_slot_is_both_asked_and_computed`.
    """
    return []


def engine_scoring_agreement_line() -> str:
    """Coverage for the check above, as audit context rather than a finding."""
    import measured as MEAS

    d = MEAS.scoring_logic_agreement()
    if not d["matched"]:
        # RETIRED, NOT EMPTY. `scoring_logic_agreement` went with the python
        # web engine (goal O); reporting its empty result as "no signature was
        # produced" describes a data gap that does not exist.
        return ("engine scoring: NOT COMPARED -- the python web engine was "
                "eliminated (goal O), so a verdict signature has only one "
                "engine to produce it.")
    return (f"engine scoring: {d['matched']} verdict signature(s) produced by "
            f"BOTH engines, {len(d['differing'])} of them scored differently. "
            f"Evidence that the two implementations agree, proportional to that "
            f"coverage -- not proof, since it says nothing about combinations "
            f"neither engine reached.")


def check_paper_scorer_agrees_on_identical_verdicts() -> list[str]:
    """RETIRED 2026-09-24 with the python web engine. ALWAYS RETURNS [].

    It watched: score.py's arithmetic matched the web mirror's on the same verdicts.

    THAT QUESTION NO LONGER HAS TWO SIDES. The python mirror of
    `scoreSlotSheet` was eliminated in goal O, so this would compare a
    thing against itself or against nothing. O's own text named the
    class: "a check that exists to catch drift between two
    implementations is dead weight once there is one implementation".

    KEPT AS A RECORD rather than deleted, so what STOPPED being watched
    stays legible -- the same treatment as
    `check_no_slot_is_both_asked_and_computed`.
    """
    return []


def paper_scorer_agreement_line() -> str:
    """Coverage for the check above, as audit context rather than a finding."""
    import measured as MEAS

    d = MEAS.paper_scorer_agreement()
    if not d["items"]:
        # RETIRED, NOT EMPTY -- and this one read as FALSE. All 26 items have
        # a recorded paper artifact with six runs each; what went is
        # `paper_scorer_agreement`, which re-scored them through the python web
        # mirror. The arithmetic question it asked is answered instead by
        # `paper_reproduces_web_line`, which holds the judgments fixed and runs
        # them through the paper scorer -- 6268 of 6268 cells identical.
        return ("paper scoring: NOT COMPARED -- the python web mirror it "
                "re-scored through was eliminated (goal O). See the "
                "paper-vs-web arithmetic line below, which asks the same "
                "question against a side that still exists.")
    return (f"paper scoring: {d['agree']} paper cell(s) across {len(d['items'])} "
            f"item(s) ({', '.join(d['items'])}) re-scored through the web mirror's "
            f"arithmetic on their own recorded verdicts, {len(d['differing'])} "
            f"differing. The other {len(MEAS._jobs()) - len(d['items'])} items have "
            f"no paper artifact and are UNCOMPARED -- sweep the paper side to widen "
            f"this.")


# A MECHANISM MAY NOT VARY BY ITEM. Only rubric CONTENT may. An engine that
# behaves differently on Q4a than on Q6 is two engines, and every divergence
# this file exists to catch becomes unfalsifiable: a number measured on one item
# stops being evidence about the scorer at all.
#
# WHAT COUNTS AS A VIOLATION: a module-level container of ITEM IDS in an engine
# module, or a comparison of an item's id against a literal id. Both gate
# behaviour on WHICH item is being scored rather than on what the item declares.
#
# WHAT DOES NOT: a per-item value read from the rubric or the sheet. `maps`,
# `derived`, SLOT_SPEC, RESPONSE and the rest differ by item BY DESIGN -- that
# is content, and the engine treats all of it the same way.
#
# DECLARED, WITH THE REASON EACH ONE GIVES FOR ITSELF, and ratcheted: the budget
# only goes down. Two of these call themselves temporary in their own comments,
# which is the point of writing them down here -- an experiment that is never
# generalised is just an item-dependent engine with a comment.
ITEM_GATED_MECHANISMS: dict[tuple[str, str], str] = {
    # RETIRED 2026-09-10, both FIXED rather than declared:
    #   olx_prompts.UTB_CHOICE   -> derived from the rubric's own
    #       `reads_utb_choice`, already True on Q1 AND Q2. The list said Q1,
    #       score.py honoured the flag for both, so the sides disagreed on Q2
    #       because the engine contradicted the rubric.
    #   olx_prompts.TERSE_CREDIT -> deleted. Q1 alone got a credit list with no
    #       descriptions, an "experiment" never generalised, and score.py never
    #       implemented it -- so Q1 was the one item whose two sides were asked
    #       different questions.
    #   olx_prompts.RELAX_UTB_AUTHORITY -> deleted, heading uniform as "from the
    #       list". Its own declaration already judged "(authoritative)" WRONG --
    #       it asserts authority over the judgement and contradicts
    #       `utb_stated`'s rule -- and scoped the correction to Q1 "to keep the
    #       measurement clean", which is how wording known to be wrong stayed
    #       shipped on the other 25. It was inert until UTB_CHOICE was derived
    #       from the rubric, at which point Q2 started receiving the word Q1 had
    #       been spared: fixing one item-gated mechanism activated the next.
    #   score.LABELLED_PARTS_ITEMS -> deleted, the clause now ships on every
    #       item that asks for more than one answer. It was gated to Q3 because
    #       that is where it was measured, which is the same score-optimising
    #       argument the other three used. It stays conditional on what the
    #       STUDENT did -- "where they label nothing, read the whole response"
    #       -- which is decided per submission and is the legitimate kind of
    #       gate. Q6 is the known risk and is being measured, not designed
    #       around.
}
ITEM_GATED_BUDGET = _budget("ITEM_GATED_BUDGET")

_ENGINE_MODULES = ("score", "agreement", "agreement_app", "olx_prompts")


# Counted references, for the arm below. `both` is the one that matters: it is
# the only word that asserts a number without naming it.
# PLURAL ONLY, and only these words. The first version also took "either",
# "neither" and the singular, and 7 of its 8 findings were noise: "either
# answer" and "neither answer" are idiomatic for "whichever one" rather than
# references to a structure, and "the two you DO answer" matches `answer` as a
# VERB. What survives the tightening is the one real case, WK2's "READ BOTH
# BOXES" on a one-box item.
_COUNT_WORDS = {"both": 2, "all three": 3, "all four": 4,
                "the two": 2, "the three": 3, "the four": 4}


def check_paper_prompt_has_no_box_deixis() -> list[str]:
    """The paper grader must never be told to read a BOX. It has none.

    THE WEB HAS BOXES AND THIS SCORER DOES NOT, BY DESIGN -- the paper
    submission arrives as one block. `score._describe_boxes` translates the
    deixis, and for a long time it translated only the forms that point at a
    PARTICULAR box, leaving 25 distinct phrases across six items untouched:
    indefinite ("a box"), plural ("all three boxes"), named by role ("the type
    box"), and definite ones whose slot could not resolve its own box.

    THE COST WAS CONCENTRATED WHERE IT HURT MOST. Six of the corpus's fourteen
    worst-agreeing slots carried one -- 1c/series_box_holds 33%, Q6/affect_c2
    52%, Q6/state_c2 63%, Q6/link_c2 66%, Q6/affect_c1 82%, 2a/states_size 82%
    -- which is all four of Q6's worst on the item with a documented ceiling.
    A bar attached to nothing is just a lower bar, and this check exists so
    that stops being something a person has to notice.

    TWO ARMS. The first is absolute: no `box` survives into a paper prompt. The
    second catches what the translation cannot -- a phrase naming MORE answers
    than the item asks for. WK2's `named_type` says "READ BOTH BOXES" and WK2
    has ONE box, so it points outside the box structure entirely; translating
    it to "READ BOTH ANSWERS" keeps the arithmetic wrong, and
    `_describe_boxes`' own docstring says such a phrase "needs rewording or a
    declaration" rather than a silent substitution.
    """
    # PORTED (goal K). PYTHON ASSEMBLES, TYPESCRIPT JUDGES: the paper prompt is
    # built by the paper generator, which stays here, so the payload carries the
    # shipped text and the number of answers each item asks for. Fire-tested by
    # injecting box deixis into a real prompt on both sides: byte-identical.
    import lo_enforce
    from olx_prompts import RESPONSE
    import score as _SC
    import coursedata as _CD

    items = []
    for it in _CD.items():
        iid = str(it.get("id") or "")
        if not iid:
            continue
        try:
            prompt = _SC.build_prompt(it, "x", {"(fingerprint)": ""}, "(fingerprint)")
        except Exception:
            continue
        items.append({"item": iid, "prompt": prompt,
                      "answers": len(RESPONSE.get(iid) or [])})
    return lo_enforce.run("paper_prompt_has_no_box_deixis", {"items": items})


def check_prompts_carry_no_process_history() -> list[str]:
    """Shipped prose must not tell the grader about OUR process.

    THE SIBLING OF leakage.py's ORIGINAL PROBLEM. There, the cohort's words get
    into a rule and the rule stops generalising. Here the MAINTAINER'S words get
    in: the grader is told about a sweep, a date, a cell count or an earlier
    draft of the rubric -- none of which it can act on, all of which it must
    read and weigh, and none of which anybody decided to say to it.

    FOUND BY ACCIDENT, while tracing box deixis. 2a's second guidance bullet
    ended "A rule that charged boxes of that shape was measured on 2026-09-02
    and broke three cells the graders credit." The RULE is complete in the two
    sentences before it; that one is the ARGUMENT FOR it, addressed to whoever
    next edits the rubric, and it shipped to BOTH sides.

    Scanned over `leakage.authored`, which is exactly what a grader sees, and
    deduplicated per (item, kind, phrase) because a bullet appears both on its
    own and inside the assembled prompt. The pervasive CONVENTIONS -- "the
    graders", "IMPLICIT (from gold)", "the rubric" -- are declared in
    `leakage.PROMPT_CONVENTIONS_DECLARED` rather than reported: each is a
    corpus-wide rewrite needing its own measurement, and burying one real
    accident under 174 deliberate uses is how a check gets ignored.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K: python fetches the authored
    # prose -- `leakage.authored` is exactly what a grader sees -- and reports;
    # `enforce/processHistory.ts` decides what counts as process language. The
    # patterns are ENGINE vocabulary (our dates, our sweeps, our filenames), so
    # they are generic for any course maintained the way this one is.
    #
    # PROVEN AGAINST THIS CORPUS, not merely unit-tested: python and TypeScript
    # returned byte-identical findings in identical order, and because the live
    # corpus is clean that agreement was re-run on a SPIKED corpus carrying the
    # sentence 2a actually shipped -- 5 findings, identical on both sides. An
    # agreement that cannot fail is not evidence.
    # SELF-ASSEMBLED. Subgoal E63: the runner builds this payload, and the
    # assembler was proven to build what python built -- payload-identical, or
    # order-only with the finding SET shown unchanged on data mutated until
    # the rule fires. `runner.SELF_ASSEMBLING` is that cleared list.
    import lo_enforce

    return lo_enforce.run("prompts_carry_no_process_history", None)


def check_side_notes_are_side_specific() -> list[str]:
    """A side's item notes must be that side's ONLY, and must need to be.

    TWO TABLES, EACH SIDE-ONLY BY CONSTRUCTION: `olx_prompts.ITEM_NOTES` for
    the web and `score.PAPER_ITEM_NOTES` for paper. The mechanism is uniform --
    every item is offered a note and the ones that declare content get it --
    and what differs between items is what they SAY, which is content and may
    vary. That distinction is the same one
    `check_engine_mechanisms_are_not_item_dependent` draws.

    THE RULE THIS ENFORCES: a note earns a side table only by saying something
    true of THAT side and not the other. A note that could be said to both
    graders is not a side note at all -- it is rubric content, and belongs in
    `guidance`, where both sides get it. Without this, a side table becomes the
    place where anything measured on one side and not the other quietly lands,
    and the two engines drift apart one convenience at a time.

    THREE ARMS, and the first two are exact. (1) NEITHER MODULE MAY READ THE
    OTHER'S TABLE -- side-only means side-only. (2) A note's text must not turn
    up in the other side's built prompt for that item. (3) Every key must carry
    a WHY beside it, in `ITEM_NOTES_WHY` / `PAPER_ITEM_NOTES_WHY`, saying what
    makes it side-specific; prose cannot be judged mechanically, so the
    requirement is that the reason is written down and can be read.
    """
    import ast
    import pathlib as _pl

    import olx_prompts as _O
    import score as _SC

    out = []
    pairs = (("web", "ITEM_NOTES", _O.ITEM_NOTES, getattr(_O, "ITEM_NOTES_WHY", {}),
              "score.py", "PAPER_ITEM_NOTES"),
             ("paper", "PAPER_ITEM_NOTES", _SC.PAPER_ITEM_NOTES,
              getattr(_SC, "PAPER_ITEM_NOTES_WHY", {}), "olx_prompts.py", "ITEM_NOTES"))

    for side, name, table, why, foreign_mod, foreign_name in pairs:
        # (1) the other side's module must not read this table
        try:
            src = _pl.Path(foreign_mod).read_text()
        except Exception:
            src = ""
        # PARSED, NOT SCANNED, and two bugs of mine are why. A substring test
        # reports PAPER_ITEM_NOTES as a reference to ITEM_NOTES because the one
        # contains the other. A word-boundary test then still fires on PROSE --
        # score.py's own comment says "the mirror of `olx_prompts.ITEM_NOTES`",
        # which is a citation, not a use. Only a NAME or ATTRIBUTE node is a
        # reference; comments and docstrings never reach the AST.
        try:
            tree = ast.parse(src)
        except Exception:
            tree = None
        used = tree is not None and any(
            (isinstance(n, ast.Name) and n.id == name)
            or (isinstance(n, ast.Attribute) and n.attr == name)
            for n in ast.walk(tree))
        if used:
            out.append(f"{foreign_mod} READS {name}, which is {side}-only "
                       f"by construction -- a side note must not reach the "
                       f"other engine")
        # (3) every key needs a stated reason
        for iid in sorted(table):
            if not (why.get(iid) or "").strip():
                out.append(f"{name}[{iid!r}] has no entry in {name}_WHY. Say "
                           f"what makes it true of the {side} and not the other "
                           f"side, or move it to the rubric's `guidance` where "
                           f"both graders get it")
        for iid in sorted(why):
            if iid not in table:
                out.append(f"{name}_WHY[{iid!r}] explains a note that no longer "
                           f"exists -- drop it")

    # (2) no note's text may appear in the other side's prompt
    for iid, text in sorted(_SC.PAPER_ITEM_NOTES.items()):
        probe = " ".join(text.split())[:60]
        try:
            web = " ".join(_O.build_web_prompt(iid).split())
        except Exception:
            continue
        if probe and probe in web:
            out.append(f"PAPER_ITEM_NOTES[{iid!r}] also appears in the WEB "
                       f"prompt -- it is not paper-specific")
    for iid, text in sorted(_O.ITEM_NOTES.items()):
        probe = " ".join(text.split())[:60]
        it = next((x for x in all_items() if x["id"] == iid), None)
        if it is None:
            continue
        try:
            paper = " ".join(_SC.build_prompt(
                it, "x", {"(fingerprint)": ""}, "(fingerprint)").split())
        except Exception:
            continue
        if probe and probe in paper:
            out.append(f"ITEM_NOTES[{iid!r}] also appears in the PAPER prompt "
                       f"-- it is not web-specific")
    return out


# ISSUES SET ASIDE ON PURPOSE — KNOWN, NOT NOW.
#
# There were three things you could do with a finding and none of them fit
# "we have seen this and are not dealing with it today":
#
#   fix it        — the finding goes away because the defect does
#   DECLARE it    — SCORING_DIVERGENCES, GOLD_DIVERGENCES and the rest, each of
#                   which asserts the difference is INTENDED. Declaring a thing
#                   you mean to fix later is a lie that outlives the intention,
#                   and this project has already found declarations that "were
#                   stale precisely because they described an intention" rather
#                   than a behaviour.
#   OVERRIDE it   — ALLOW_UNDECLARED, which is per-COMMIT, not per-issue. It
#                   records the reason to OVERRIDES.md and lets one commit
#                   through; the next commit must say it again. Used habitually
#                   it turns the gate advisory, which is how detection power is
#                   lost quietly.
#
# PARKED is the missing fourth: per-ISSUE, persistent, visible, and silent. A
# parked finding is still computed and still printed -- tagged [PARKED] with its
# reason -- but it does not carry the `! ` prefix, so it does not count toward
# the undeclared total and does not block a commit. The difference from a
# declaration is the claim being made: a declaration says "this is right"; a
# park says "this is wrong and we are not fixing it yet".
#
# KEYED (item, kind) to match the audit's own finding shape, so an entry is
# greppable and reads in the same vocabulary as the line it silences.
#
# WHAT PARKING DOES NOT DO, and this is deliberate. It silences the AGGREGATE
# alarm -- the undeclared count and the commit gate. It does NOT reach inside an
# individual check's own budget or ratchet (ITEM_GATED_BUDGET,
# SELFTEST_EXPECTED, a check's internal `len(out) > N`). Those are each a
# contract that check makes about itself, and a mechanism that could quietly
# relax any of them from one table would be a master key to the whole audit.
# Parking something whose check also ratchets means raising that budget too,
# deliberately and visibly.
# EMPTY as of 2026-09-16, and the entry that used to be here left instructions
# for its own removal: "the fix is an invented example that teaches the same
# point, and then the reference and this park go together". Handout 2's worked
# non-example is now invented, the reference is gone, and the `corpus_data:`
# frontmatter went with it -- so the page renders without the corpus again.
# A park that outlives its finding is a declaration nobody reviewed.
# MOVED TO THE RECORDS 2026-09-25. Parked findings are this COURSE's, and
# while the table lived here the rule could be run from python and from
# nowhere else -- a native caller could read the budget but not the entries
# it bounds. Its reasons travel with it, as the `why` of each entry.
PARKED_UNDECLARED = _declaration("PARKED_UNDECLARED")

# Ratcheted like every other table here. A park is cheap to add and easy to
# forget, which is the failure mode: a parking lot nobody empties becomes a
# second declaration table with none of the review. Raise this only with the
# entry, and lower it when one is retired.
PARKED_BUDGET = _budget("PARKED_BUDGET")


# How far a side's own verdicts may fail to reproduce its own score before the
# comparison built on them is untrustworthy. Not zero: an artifact can carry a
# cell the scorer no longer accepts. But a harness reproducing a THIRD of a
# side's own scores is measuring itself.
MIRROR_CONTROL_FLOOR = 0.90


def check_mirror_reproduces_its_own_scores() -> list[str]:
    """RETIRED 2026-09-24 with the python web engine. ALWAYS RETURNS [].

    It watched: each side's arithmetic reproduced its own recorded scores.

    THAT QUESTION NO LONGER HAS TWO SIDES. The python mirror of
    `scoreSlotSheet` was eliminated in goal O, so this would compare a
    thing against itself or against nothing. O's own text named the
    class: "a check that exists to catch drift between two
    implementations is dead weight once there is one implementation".

    KEPT AS A RECORD rather than deleted, so what STOPPED being watched
    stays legible -- the same treatment as
    `check_no_slot_is_both_asked_and_computed`.
    """
    return []


def check_parked_entries_still_apply() -> list[str]:
    """A parked issue that no longer occurs, or has outgrown its budget.

    Two ways a parking lot rots. An entry whose finding has since been fixed
    goes on silencing a line nobody produces any more -- harmless until the same
    (item, kind) recurs for a different reason and is silenced on sight. And a
    table that grows without the budget moving is a table nobody is reading.

    The first arm needs the audit's live finding set, which `equivalence.py`
    owns, so it is checked there and reported here; this function covers the
    budget and the shape.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K. The parking lot is course data;
    # "an override needs a budget raised deliberately and a reason that says
    # what would unpark it" is generic.
    # SELF-ASSEMBLED. Subgoal E63: the runner builds this payload, and the
    # assembler was proven to build what python built -- payload-identical, or
    # order-only with the finding SET shown unchanged on data mutated until
    # the rule fires. `runner.SELF_ASSEMBLING` is that cleared list.
    import lo_enforce

    return lo_enforce.run("parked_entries_still_apply", None)



def check_no_module_defines_names_after_its_main_guard() -> list[str]:
    """Nothing that DEFINES a name may sit below `if __name__ == "__main__":`.

    A MODULE RUN AS A SCRIPT NEVER REACHES IT. Execution goes top to bottom, and
    `raise SystemExit(main())` inside the guard ends the process; anything below
    is defined only when the module is IMPORTED. So a definition placed there is
    live on one path and dead on the other, and the two paths disagree silently.

    THE COST, MEASURED. The history rewrite appended a wrapper to
    `olx_prompts.py` that converts a corpus reference on its way into the .olx,
    and appended it below the guard. `--write` and `--check` are exactly the
    script path, so the wrapper never ran there -- while `measured._olx`, which
    imports the module, got it. `--check` then compared a file holding
    references against a generator emitting words and called 42 of 113 states out
    of date. That was recorded as an unavoidable trade between byte-reversibility
    and generator consistency, with a persuasive explanation, and it was neither:
    the code that would have reconciled them was never executed.

    Imports and `__all__` are fine -- they bind nothing new that a script path
    would miss in a way that changes behaviour. What this catches is a `def`, a
    `class`, or an assignment appearing after the guard.
    """
    import ast
    from pathlib import Path as _P
    out = []
    for path in sorted(_P(__file__).resolve().parent.glob("*.py")):
        f = path.name
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue                      # a separate check owns parse failures
        guard_line = None
        for node in tree.body:
            if (isinstance(node, ast.If) and isinstance(node.test, ast.Compare)
                    and isinstance(node.test.left, ast.Name)
                    and node.test.left.id == "__name__"):
                guard_line = node.lineno
        if guard_line is None:
            continue
        for node in tree.body:
            if node.lineno <= guard_line:
                continue
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                out.append(f"{f}: `{node.name}` is defined at line {node.lineno}, "
                           f"BELOW the main guard at {guard_line} -- it never exists "
                           f"when the module is run as a script")
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                tgt = getattr(node, "target", None) or (node.targets[0] if getattr(node, "targets", None) else None)
                name = getattr(tgt, "id", "<expr>")
                if name.startswith("_") or name == "<expr>":
                    continue
                out.append(f"{f}: `{name}` is assigned at line {node.lineno}, "
                           f"BELOW the main guard at {guard_line} -- dead on the "
                           f"script path")
    return out


# An absolute literal that is a PATTERN rather than a location. Declared here
# with its reason, in the same spirit as NOT_STUDENT_TEXT: the exception is
# visible and argued, not silent.
ABSOLUTE_PATH_EXCEPTIONS = {
    "/tmp/claude-*/*/*/scratchpad":
        "a GLOB used to find scratchpad copies of these modules, not a location "
        "anything is read from or written to; the check that owns it is looking "
        "for stray edits, so the pattern IS the subject",
    "/tmp/claude-*/*/scratchpad": "the same glob, one directory shallower",
}


def _run_grammar_script(name: str, what: str) -> list[str]:
    """Run a standalone equivalence script and report what it says.

    THE SCRIPTS EXISTED AND NOTHING RAN THEM. `check_ref_grammars.py` was
    invoked only by the migration's stage 03b gate and
    `check_slot_grammars.py` only by hand, so between migrations the two
    resolvers could drift for weeks with nothing to notice. A check nobody
    invokes is the same defect as a check that never ran -- see
    `check_every_check_is_invoked`, which catches it one level down and could
    not see these, because they are files rather than functions.
    """
    import os as _os
    import subprocess
    import sys as _sys
    from pathlib import Path as _P

    import paths as _p

    script = _P(__file__).resolve().parent / name
    if not script.exists():
        return [f"{name} is missing -- nothing compares {what}"]

    # HAND THE CHILD THE LOCATION THIS PROCESS ALREADY KNOWS. `corpus_resolve`
    # refuses to guess where the export lives -- deliberately, because it carries
    # student text and must never default to somewhere inside a checkout -- so it
    # reads $CORPUS_REFS or $COURSE_DATA and exits if neither is set. The child
    # inherited whatever the invoking shell happened to have, so running the
    # audit from a shell without $COURSE_DATA made this check fail EVERY time,
    # on an unset variable rather than on anything about the two grammars.
    #
    # THAT IS NOT A BASELINE, IT IS A CHECK THAT CANNOT PASS. `paths.DATA`
    # resolves the same directory with a fallback and is what the rest of the
    # codebase uses; passing it down gives the comparison a fair chance to run
    # while leaving `corpus_resolve` as strict as it was. An explicit setting in
    # the environment still wins, so a deliberate override is not overridden.
    env = dict(_os.environ)
    env.setdefault("COURSE_DATA", str(_p.DATA))
    if not env.get("CORPUS_REFS") and not (_p.DATA / "corpus_refs.json").exists():
        return [f"{name} cannot run: no export at {_p.DATA / 'corpus_refs.json'} "
                f"and $CORPUS_REFS is unset, so {what} was NOT compared -- which "
                f"is not the same as their agreeing"]

    r = subprocess.run([_sys.executable, str(script)], cwd=str(script.parent),
                       capture_output=True, text=True, timeout=1800, env=env)
    txt = (r.stdout or "") + (r.stderr or "")
    if r.returncode == 0:
        return []
    lines = [l.strip() for l in txt.splitlines() if l.strip()]
    return [f"{name}: {l[:150]}" for l in lines[:6]] or [f"{name} failed with no output"]


# Charge-once pairs the WEB reader declares and the CLI probe cannot discover.
#
# NOT A DIFFERENCE IN WHAT THE ENGINES SCORE. The probe finds a sublinear pair
# by arithmetic: it fails each slot singly, then in pairs, and calls the pair
# charge-once when `both < single[a] + single[b]`. A pair produces no observable
# sublinearity when one side is already a gate, or ignored, or its loss is
# masked by another deduction -- so the probe cannot see a rule the web declares
# outright. The two engines agree; one instrument reaches the rule and the other
# does not.
#
# DECLARED RATHER THAN TOLERATED IN A COMMENT. Both of these were accepted
# already -- the selftest names NR's as a legitimate declared divergence when it
# computes its clean baseline -- but that acceptance lived in a sentence inside
# a different module. A reader meeting the finding could not tell an accepted
# limit of the probe from a new defect, which is the distinction
# DECOMPOSITION_DIVERGENCES exists to preserve, one instrument over.
#
# EACH ENTRY NAMES WHY THE PROBE CANNOT REACH IT, so a THIRD one shows up as
# new rather than joining a list nobody re-reads. The table ratchets: it may
# shrink, and an addition wants the same measurement these had.
# PROBE_UNREACHABLE_PAIRS IS BOUND FURTHER DOWN, after `_declaration` is
# defined. Entries and their measurements live in the course file, authored
# in `declaration_source.py`.


def check_probe_unreachable_pairs_still_apply() -> list[str]:
    """Every declared probe gap must still be a gap, and still be real.

    A DECLARATION WITHOUT A VERIFIER IS A SILENCER. `PROBE_UNREACHABLE_PAIRS`
    stops a finding being reported, so it has to be re-tested or it becomes a
    place where a real divergence can hide: the entry would go on suppressing
    the finding long after the reason for it had gone.

    Two ways an entry can rot, and they fail in opposite directions:

      * THE PROBE LEARNS TO REACH IT. If the CLI probe now discovers the pair,
        the gap has closed and the entry is stale -- it should be deleted so the
        instruments are known to agree, which is a stronger claim than the
        declaration made.
      * THE WEB STOPS DECLARING IT. Then there is no pair to be unreachable, and
        the entry is describing a rule that no longer exists.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K: python reads the CLI probe's
    # signatures, `enforce/probeUnreachable.ts` decides whether each declared
    # pair is still out of reach. A declaration that has COME TRUE is reported,
    # because from that moment it suppresses a real answer rather than a gap.
    #
    # PROVEN WITH A CONTROL: a pair declared unreachable that the probe does
    # reach produced the same single finding on both sides.
    import lo_enforce

    try:
        cli = cli_signatures()          # defined here, not in equivalence
    except Exception as e:
        return [f"cannot read the CLI probe ({type(e).__name__}: {e}) -- these "
                f"declarations cannot be re-tested, which is not the same as "
                f"their being sound"]
    return lo_enforce.run("probe_unreachable_pairs_still_apply", {
        "signatures": {it: {"charge_once": [list(x) for x in (c.get("charge_once") or ())]}
                       for it, c in cli.items()},
        "declarations": [{"item": it, "pair": sorted(pair)}
                         for (it, pair) in PROBE_UNREACHABLE_PAIRS],
    })



def check_every_item_has_a_findable_slot_sheet() -> list[str]:
    """Every item's slot sheet must be reachable by id, or checks go blind on it.

    SLOTS HANG OFF TWO DIFFERENT ELEMENTS. Twenty-three items are graded by an
    `<LLMAction>` and are listed in `olx_prompts.ACTION`; three more -- 1b, T1
    and T2 -- carry their sheet on a `<DerivedChecks>` and are listed in
    `SHEET_ONLY`. A reader that walks only `<LLMAction>` sees 23 of 26 items and
    reports nothing about the rest.

    THAT IS NOT HYPOTHETICAL. `check_scored_slots_are_answered_by_both_engines`
    built its points map from `<LLMAction>` elements alone, so 1b's own slots
    were invisible to it; `week_1` resolved instead to the SAME-NAMED slot on
    1a, inheriting 2 points and a derivation that belong to a different item.
    Three findings resulted, wrong in every particular, and nothing flagged the
    blindness itself -- the check simply never saw the sheet it needed.

    So this asks the prior question: for each item, is there an element in the
    handouts carrying its sheet, under the id the mapping gives? An item whose
    sheet cannot be found is not a scoring fault; it is a hole in what every
    sheet-reading check can see, and it should be loud rather than silent.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K. Python supplies the item-to-
    # element map and the handout text; `enforce/sheetDiscovery.ts` looks for
    # each id. An empty corpus is a REFUSAL there, not a pass.
    # SELF-ASSEMBLED. Subgoal E63: the runner builds this payload itself,
    # from the same course records python would have read. The assembler was
    # compared against the payload python used to send and found IDENTICAL
    # before this fetch was deleted; `runner.SELF_ASSEMBLING` names the rules
    # that comparison has cleared, and the runner refuses any other.
    import lo_enforce

    return lo_enforce.run("every_item_has_a_findable_slot_sheet", None)



def check_no_file_points_into_a_developers_notes() -> list[str]:
    r"""No file in this repository may cite a Claude memory.

    A POINTER ONLY ONE PERSON CAN FOLLOW IS NOT A CITATION. Those notes live
    outside every checkout, under one developer's home directory, private to that
    machine and rewritten whenever they learn something. A comment in
    `forms.py` saying the evidence is "recorded in" one of them tells a second
    reader that evidence exists and gives them no way to reach it, and tells a
    future reader nothing at all once the note is renamed.

    WHAT TO DO INSTEAD, AND IT IS NOT A WHOLESALE COPY. Move the PART the pointer
    is actually about into the document that owns it -- the guide section, the
    backlog entry, the item's own record -- and cite that. Of the nine notes cited
    here, seven resolved to a QUALITY_CONTROL.md section that already said the
    same thing; one needed a new file, `Q6_MATCHING_CEILING.md`, because
    twenty-four call sites cited it and nothing in the repository held it.

    SCREEN BEFORE YOU COPY. This repository is public and those notes are not
    written with that in mind: one of the nine carried a 29-word student sentence.
    Run the text through the corpus scan before it lands, as any other prose would.

    THE FOUR FORMS ARE THE PATTERNS BELOW, AND ARE DELIBERATELY NOT SPELLED OUT
    IN THIS DOCSTRING. Prose naming them literally is itself a file pointing at
    that store, so the first version of this check reported its own explanation --
    five findings, every one of them this function. The handouts use the same
    trick for the frontmatter marker, and for the same reason.

    A bare slug inside an HTML anchor is a section anchor in this repository's own
    documents and is NOT flagged: the defect is a pointer out of the tree, not a
    word that resembles one.
    """
    import re as _re
    import paths as _p

    root = _p.REPO
    pats = [
        # WRITTEN AS A CHARACTER CLASS SO THIS LINE DOES NOT MATCH ITSELF.
        # Spelled plainly, the pattern IS an instance of what it looks for, and
        # this function reports its own source as a finding.
        (_re.compile(r"\.claude[/]projects"), "a path into a developer's Claude directory"),
        (_re.compile(r"\bmemory/[a-z0-9-]+\.md"), "a memory file path"),
        (_re.compile(r"\bmemory\s+`[a-z0-9-]+`"), "a memory cited by name"),
        (_re.compile(r"\[\[[a-z0-9]+(?:-[a-z0-9]+)+\]\]"), "a memory wiki-link"),
    ]
    exts = (".py", ".md", ".olx", ".json", ".ts", ".tsx", ".sh", ".txt", ".yaml", ".yml")
    out, scanned = [], 0
    # PRUNED: see `paths.repo_files`. An in-repository data store would
    # otherwise be scanned as if it were source.
    for f in _p7.repo_files(root=root):
        if not f.is_file() or f.suffix.lower() not in exts:
            continue
        if ".git" in f.parts or "node_modules" in f.parts:
            continue
        try:
            text = f.read_text(errors="replace")
        except OSError:
            continue
        scanned += 1
        for rx, what in pats:
            for m in rx.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                out.append(f"{f.relative_to(root)}:{line}: {what} "
                           f"({m.group(0)!r}) -- move the part this is about into "
                           f"a document in this repository and cite that")
    if not scanned:
        return [f"no text files found under {root}; nothing was scanned, which "
                f"is not the same as nothing pointing outside the tree"]
    return out


def check_every_reference_has_the_data_that_resolves_it() -> list[str]:
    """A `{{corpus:...}}` in an .olx requires `corpus_data:` in that file's frontmatter.

    THE REFERENCE AND ITS POINTER ARE ONE UNIT, AND NOTHING ELSE HOLDS THEM
    TOGETHER. A reference names a span; `corpus_data:` names the export the span
    lives in. Split them and the build cannot resolve the file at all -- it stops
    with "carries {{corpus:...}} references and no `corpus_data:` in its
    frontmatter", which is a hard failure of the whole content build, not of one
    page. So the cost of the omission is paid by every handout at once.

    WHY THIS IS NOT COVERED BY THE BUILT-PAGE CHECK. Its sibling,
    `check_no_unresolved_reference_reaches_the_page`, reads the BUILT output. A
    file that fails to build produces no output to read, so the reference never
    reaches a page and that check is silent -- correctly, on its own terms. The
    two findings are opposite shapes: one is a reference that got through, this
    is a reference that cannot get through. Neither implies the other.

    MEASURED, NOT HYPOTHETICAL. Found 2026-09-16 by the first comparative build
    run against the rewritten history: `consent.olx` carried one reference and no
    frontmatter, and a census across all 506 commits found five such blobs in
    four paths. The earlier by-hand check had printed only the three handouts, so
    the file was never in view -- which is why this reads EVERY .olx in the tree
    rather than a named list.

    AN EMPTY TREE IS NOT A CLEAN TREE. If no .olx can be found, the scan proves
    nothing and says so, rather than returning the same `[]` a healthy repo does.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW, AND THAT DELETED A COPY. Goal K. This
    # carried the build's rule TRANSCRIBED BY HAND under a comment saying so. A
    # transcription is correct only while someone keeps it in step, and this one
    # had already been wrong once: it demanded a `---` fence at byte 0, every
    # .olx here wraps its frontmatter in an HTML comment, and all fifteen
    # reference-carrying files reported missing data, three of which plainly
    # carried it. `enforce/referenceData.ts` IMPORTS `corpusDataPath` and asks
    # it, so the check can no longer disagree with what it predicts.
    # SELF-ASSEMBLED. Subgoal E63: the runner builds this payload itself,
    # from the same course records python would have read. The assembler was
    # compared against the payload python used to send and found IDENTICAL
    # before this fetch was deleted; `runner.SELF_ASSEMBLING` names the rules
    # that comparison has cleared, and the runner refuses any other.
    import lo_enforce

    return lo_enforce.run("every_reference_has_the_data_that_resolves_it", None)



def check_rewritten_artifacts_still_parse() -> list[str]:
    """Every .json parses and every .py compiles. Reference-substitution is
    text-level, and text-level replacement can land where syntax matters.

    FOUND BY THIS BEING ABSENT, 2026-09-21. A substitution replaced
    `run_totals: [8, 10, 11, 11, 11, 13]` -- the repo's own sweep counts -- with a
    corpus reference, because the digit run coincidentally matched a student's
    week-2 series. The reference went in as a BARE JSON ARRAY ELEMENT, so
    `MEASURED.json` stopped parsing and `measured.load()` raised before the
    self-test could run one case.

    WHY NOTHING ELSE SEES IT, and why this is a separate question rather than a
    stronger version of an existing one:

      * the byte proof compares bytes AFTER expansion, and `expand()` restores
        the digits exactly -- 41,861 of 41,861 file-versions passed while the
        file would not parse;
      * corpus scans use WORD 8-grams, and `"10, 11, 11, 11"` yields none;
      * the substitution itself is reversible and therefore "correct" by every
        definition the rewrite had.

    Expansion fidelity and USABILITY are different properties. This asks the
    second one: can the code that reads the artifact still read it?

    SEVEN OF 1,635 TABLE ENTRIES ARE PURE DIGIT RUNS (`0, 0, 30, 0,` and the
    like). They are genuine student series and belong in the table, but as search
    keys they carry no lexical anchor, so they match any file holding those
    numbers in that order. Measured the same day: references from those keys
    reached five other files -- agreement.py, enforcement.py, forms.py,
    GOALS.md, course.json -- and were harmless in every one, because they landed
    inside strings and prose. Placement is the whole difference, and only a
    parser can tell.
    """
    import json as _json

    import paths as _paths_pp
    out = []
    root = _paths_pp.REPO
    for f in _p7.repo_files(".json", root=root):
        if ".git" in f.parts or "node_modules" in f.parts:
            continue
        try:
            _json.loads(f.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            continue
        except OSError:
            continue
        except ValueError as exc:
            out.append(f"{f.relative_to(root)} does not parse as JSON: {exc}. "
                       f"A substitution most likely landed in a structural "
                       f"position -- a bare number or key -- rather than inside "
                       f"a string.")
    for f in _p7.repo_files(".py", root=root):
        if ".git" in f.parts or "node_modules" in f.parts:
            continue
        try:
            compile(f.read_text(encoding="utf-8"), str(f), "exec")
        except (UnicodeDecodeError, OSError):
            continue
        except SyntaxError as exc:
            out.append(f"{f.relative_to(root)} does not compile: line "
                       f"{exc.lineno}: {exc.msg}.")
    return out


def check_no_unresolved_reference_reaches_the_page() -> list[str]:
    """No `{{corpus:...}}` may survive into what a student is served.

    THE GRAMMAR CHECKS TEST THE PARSERS. THIS TESTS THE ARTEFACT. When the two
    resolvers last diverged the build did not fail -- the TypeScript regex simply
    did not match a reference carrying a shape, so the build reported "0 file(s)
    with references", passed, and would have copied a literal `{{corpus:...}}`
    onto the page. A probe-based equivalence check makes that unlikely; only
    reading the built output makes it visible.

    Both stages are read: `.stage/content`, which the resolver writes, and
    `static-content`, the JSON the page loads. A reference surviving into either
    is a disclosure of the citation and a rendering failure at once.

    THREE OUTCOMES, AND TWO OF THEM ARE NOT PASSES. An unresolved reference is
    the finding this exists for. But a build directory that is ABSENT means the
    page was never built, and one OLDER than the content it claims to render is
    not evidence about that content -- reporting either as clean is how a check
    becomes decoration.
    """
    # A reference must be resolved before anybody sees it; the artefacts are lo-
    # blocks' own.
    import lo_enforce

    return lo_enforce.run("no_unresolved_reference_reaches_the_page", None)


def check_reference_grammars_agree() -> list[str]:
    """The two corpus-reference resolvers must accept and produce the same thing.

    Python resolves when the scorer reads a file; the engine resolves when the
    page is built. When they last diverged the failure was SILENT in the worst
    direction: the TypeScript regex required `}}` straight after `sha=`, so a
    reference carrying a shape did not match at all, the build reported "0
    file(s) with references" and passed -- and would have copied a literal
    `{{corpus:...}}` onto a page a student reads.
    """
    return _run_grammar_script("check_ref_grammars.py",
                               "the two corpus-reference grammars")


def check_slot_grammars_agree() -> list[str]:
    """The two slot-sheet parsers must read the same attribute the same way.

    `olx_prompts.parse_slots` says in its own docstring that it mirrors
    `slotSheet.ts`, which was a promise nothing checked. A corpus reference's
    colons collide with `name:description:verdicts@weight`, and when only the
    Python side was fixed the grader and the student saw DIFFERENT verdict
    vocabularies for the same slot -- each internally consistent, neither
    complaining.
    """
    return _run_grammar_script("check_slot_grammars.py",
                               "the two slot-sheet grammars")


def check_filesystem_locations_come_from_paths_py() -> list[str]:
    """No module may spell a filesystem location. `paths.py` resolves them.

    A LITERAL PATH DOES NOT FAIL ON THE WRONG MACHINE OR THE WRONG TREE -- IT
    SUCCEEDS ON IT. That is the whole problem: `paths.LO` is
    `os.environ.get("LO_BLOCKS", ...)` so a sandbox, a second checkout or a
    backup can be measured deliberately, and a module that spells the path
    instead ignores that choice in silence. Every gate passes, against the wrong
    thing.

    THE FAILURES THIS CLASS HAS ALREADY CAUSED, all of which looked like success:

      * the migration dry run's own scripts named their sandbox literally --
        eleven of them. Run against the live tree they would have edited the
        sandbox and reported every stage green;
      * seventeen TypeScript verifiers imported the assembler by absolute path
        into that sandbox, and would have broken silently the day it was deleted;
      * `MEDIA_DIR = "/tmp/claude-1000/..."` bakes in a numeric UID, so it is
        correct for exactly one account on one machine.

    A FALLBACK IS THE SAME DEFECT WEARING A SAFER FACE.
    `getattr(_paths, "OUT", "/home/<user>/molly_data/out")` fires precisely when
    the configuration is missing, and then reads the developer's own artifact
    directory rather than saying so. Use `paths.require()`, which names the
    environment variable it wants. Failing loudly is the point.

    Patterns that are the SUBJECT of a check rather than a location it uses are
    declared in `ABSOLUTE_PATH_EXCEPTIONS` above, with their reason.
    """
    import ast
    from pathlib import Path as _P
    ROOTS = ("/home/", "/Users/", "/tmp/", "/var/", "/opt/", "~/")
    out = []
    for path in sorted(_P(__file__).resolve().parent.glob("*.py")):
        if path.name == "paths.py":
            continue
        try:
            src = path.read_text()
            tree = ast.parse(src)
        except (SyntaxError, OSError):
            continue
        prose = set()
        for n in ast.walk(tree):
            if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef)):
                if ast.get_docstring(n, clean=False) is not None:
                    f = n.body[0]
                    prose.update(range(f.lineno, (f.end_lineno or f.lineno) + 1))
        for n in ast.walk(tree):
            if not (isinstance(n, ast.Constant) and isinstance(n.value, str)):
                continue
            v = n.value
            root = next((r for r in ROOTS if v.startswith(r)), None)
            # A BARE PREFIX IS NOT A LOCATION. `"/home/"` with nothing after it
            # is a prefix being tested against, and the first version of this
            # check reported its OWN `ROOTS` tuple six times.
            if n.lineno in prose or root is None or len(v) <= len(root):
                continue
            if v in ABSOLUTE_PATH_EXCEPTIONS:
                continue
            # THE HINT IS DERIVED FROM THE ROOTS, not from their values on one
            # machine. This tested for a literal data-directory name -- one
            # user's: a tree whose data root is declared elsewhere, as the dry
            # run's is inside the repository, was told to "add an accessor" for
            # a path that already had one, and the check that exists to push
            # machine paths out of the engine carried one itself. Longest root
            # first, so a nested root wins over the one containing it.
            hint = "paths.py (add an accessor there)"
            roots = [("paths.OUT", str(getattr(_p7, "OUT", ""))),
                     ("paths.LO", str(getattr(_p7, "LO", ""))),
                     ("paths.DATA", str(getattr(_p7, "DATA", "")))]
            for const, root_val in sorted(roots, key=lambda r: -len(r[1])):
                if root_val and root_val != "/" and root_val in v:
                    hint = const
                    break
            out.append(f"{path.name}:{n.lineno} spells a filesystem location "
                       f"{v!r} -- use {hint}, or declare it in "
                       f"ABSOLUTE_PATH_EXCEPTIONS with a reason")

        # INSIDE THIS LOOP, not after it. Placed at function level the first
        # time, where `tree` and `path` still hold whatever the LAST file left:
        # it ran once, over one arbitrary module, and a probe carrying the exact
        # pattern went unreported. Caught by injecting that probe instead of
        # reading the 0 as proof.
        # AN ABSOLUTE PATH WITH NO ABSOLUTE LITERAL. `Path.home() / "code/update/..."`
        # spells a location exactly as `"/home/<user>/code/update/..."` does, and the
        # prefix scan above cannot see it: the only literal is RELATIVE. Measured
        # 2026-09-20 -- this check reported 0 findings while two modules resolved
        # lo-blocks themselves, so the dry run's own gate read the live tree.
        #
        # NARROW ON PURPOSE: only `<something>.home() / "literal"`. `expanduser(var)`
        # normalising an input is not this defect, and a guard that cries wolf is one
        # people learn to ignore.
        for n in ast.walk(tree):
            if not (isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div)):
                continue
            left, right = n.left, n.right
            if not (isinstance(right, ast.Constant) and isinstance(right.value, str)):
                continue
            if not (isinstance(left, ast.Call) and isinstance(left.func, ast.Attribute)
                    and left.func.attr == "home"):
                continue
            if n.lineno in prose:
                continue
            out.append(f"{path.name}:{n.lineno} composes an absolute path from "
                       f"`.home() / {right.value!r}` -- no literal starts with a root, "
                       f"so the prefix scan cannot see it. Use paths.py.")


    # THE SECOND SHAPE, and it is not the spelled one. Everything above catches
    # a location WRITTEN DOWN -- `/home/...`, a sibling guess, a duplicated
    # root. It cannot see a path resolved against the WORKING DIRECTORY, which
    # fails differently: the module is correct from one directory and broken
    # from every other, so it passes every test anyone runs from `scoring/`.
    #
    # MEASURED 2026-09-25: `check_engine_mechanisms_are_not_item_dependent` read
    # `Path(f"{mod}.py")`. Running the audit from the repo root instead of
    # `scoring/` made all four engine modules unreadable, and the check reported
    # four findings saying it could not run. It was right to say so rather than
    # pass -- but nothing had ever told it the location was wrong, because the
    # location was never written down.
    import ast as _ast

    _SAFE = re.compile(r"\bpaths\b|\b_p\w*\.|\bHERE\b|_HERE|\bREPO\b|\bOUT\b"
                       r"|\bLO\b|SCORING|COURSE_|__file__|tempfile|argv|sys\.")
    # THE SAME ENUMERATION THE ARM ABOVE USES, not a second one.
    for path in sorted(_P(__file__).resolve().parent.glob("*.py")):
        try:
            text = path.read_text()
            t = _ast.parse(text)
        except Exception:
            continue
        for node in _ast.walk(t):
            if not isinstance(node, _ast.Call):
                continue
            fn = node.func
            if isinstance(fn, _ast.Name) and fn.id == "open" and node.args:
                expr = _ast.get_source_segment(text, node.args[0]) or ""
            elif isinstance(fn, _ast.Attribute) and fn.attr in (
                    "read_text", "write_text", "read_bytes", "write_bytes"):
                expr = _ast.get_source_segment(text, fn.value) or ""
            else:
                continue
            expr = expr.strip()
            if not expr or _SAFE.search(expr):
                continue
            if re.match(r'^f?["\'][^/][^"\']*["\']$', expr) or re.match(
                    r'^(pathlib\.)?Path\(\s*f?["\'][^/][^"\']*["\']\s*\)$', expr):
                out.append(
                    f"{path.name}:{node.lineno} opens {expr} -- a path "
                    f"resolved against the WORKING DIRECTORY. It works from "
                    f"`scoring/` and fails everywhere else, silently. Resolve it "
                    f"through `paths`")

    return out


def check_the_export_is_not_used_to_decide_whose_words_these_are() -> list[str]:
    """`corpus_refs.json` RESOLVES references. It does not classify text.

    THE TWO ARE DIFFERENT CORPORA AND THE DIFFERENCE IS NOT SMALL. The export
    holds only the spans something already CITED -- 715 entries, 40,766
    characters. The response space is `corpus_ref._index()`: every box of every
    cell for all 20 participants, 1023 entries and 118,804 characters, about
    three times larger. A sentence a student wrote that reached this repository
    and that nobody ever referenced is absent from the export entirely.

    SO A SCAN BUILT ON THE EXPORT CANNOT FIND IT. The history rewrite's leak
    scans were built that way, and reported zero student sentences remaining on a
    history that still carried 653 distinctive 4-grams. The check that got it
    right -- `precommit_gate.is_student` -- decides against `_index()`, and the
    difference between those two reference sets is the entire gap between "the
    quotes we knew about are gone" and "nobody's words are here".

    Reading the export to RESOLVE a reference is correct and is what it is for;
    `corpus_resolve` and `corpus_ref` own that. Any other module reaching for it
    is almost certainly about to classify with it.
    """
    import ast
    from pathlib import Path as _P
    out = []
    OWNED = {"corpus_resolve.py", "corpus_ref.py"}
    for path in sorted(_P(__file__).resolve().parent.glob("*.py")):
        if path.name in OWNED:
            continue
        try:
            src = path.read_text()
            ast.parse(src)
        except (SyntaxError, OSError):
            continue
        # PROSE IS NOT USE. A docstring explaining the rule names the export by
        # necessity -- this check's own docstring does -- and flagging that makes
        # the check fire on its own explanation.
        tree = ast.parse(src)
        prose = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                prose.update(range(node.lineno, (node.end_lineno or node.lineno) + 1))
        for i, line in enumerate(src.splitlines(), 1):
            if line.lstrip().startswith("#") or i in prose:
                continue
            if "corpus_refs.json" in line or "CORPUS_REFS" in line:
                out.append(f"{path.name}:{i} reaches for the reference EXPORT. "
                           f"To resolve a reference call corpus_resolve.load(); to "
                           f"decide whether text is a student's use "
                           f"corpus_ref._index(), which is the whole response space")
    return out


def check_one_definition_of_what_counts_as_student_text() -> list[str]:
    """The scrubber and the scan must not each decide what a quotation is.

    TWO INSTRUMENTS WITH ONE BLIND SPOT AGREE WITH EACH OTHER. The history
    rewrite's leak scan shared the substitution matcher's pattern, so both missed
    sentences written across string-literal seams and both reported a clean
    history that still held 137 of them. The same shape recurred at a different
    layer: the table was seeded from the quotes our prose had CITED, the scan
    matched against that same table, and "no student text remains" could only
    ever mean "the ones we already knew about are gone" -- 653 distinctive
    4-grams were still there.

    So the rule lives in ONE place. `precommit_gate` decides against the corpus
    (`corpus_ref._index()`, every box of every cell), and any other component
    that has to judge whether a run of words is somebody's writing imports that
    decision rather than reimplementing it. What this check refuses is a SECOND
    definition: a module that grows its own stopword list, its own minimum word
    count, or its own corpus path.
    """
    import ast
    from pathlib import Path as _P
    out = []
    OWNED = {"precommit_gate.py", "corpus_ref.py"}
    SIGNS = ("FUNCTION_WORDS", "STOPWORDS", "MIN_CONTENT", "MIN_QUOTE_WORDS")
    for path in sorted(_P(__file__).resolve().parent.glob("*.py")):
        f = path.name
        if f in OWNED:
            continue
        try:
            tree = ast.parse(path.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id in SIGNS:
                        out.append(f"{f}:{node.lineno} defines `{t.id}` -- a SECOND "
                                   f"definition of what counts as student text. "
                                   f"Import the one in precommit_gate instead")
    return out


def check_engine_mechanisms_are_not_item_dependent() -> list[str]:
    """No engine mechanism may be gated on WHICH item is being scored.

    THE RULE IS THE USER'S AND IT IS ABOUT EVIDENCE, not tidiness: if the engine
    behaves differently per item, a measurement on one item says nothing about
    the engine, and "paper agrees with the web" stops being a claim that can be
    tested corpus-wide.

    IT WAS BROKEN THE DAY IT WAS STATED. `ASK_MAPPED_VERDICT_ITEMS = ("Q4a",)`
    gated whether a mapped verdict is ASKED -- the web asks all six, uniformly --
    and was scoped to one item because only that item measured a gain. Scoping a
    MECHANISM to where it happens to pay is how an engine becomes item-shaped.
    It was made uniform; this check is what stops the next one.

    Two patterns are caught: a module-level container of item ids, and a
    comparison of an item's `id` against a literal id.

    WHAT IS NOT A VIOLATION, and the distinction is the whole point: a table
    mapping an item to its CONTENT. `olx_prompts.ITEM_NOTES` and
    `score.PAPER_ITEM_NOTES` are dicts of item -> text, offered to every item by
    one uniform rule -- "if this item declares a note, emit it" -- and what
    differs between items is what they say, exactly as `guidance`, `credit` and
    `maps` differ. Content may vary by item; that is what a rubric IS. A
    MECHANISM may not, and an id list switching behaviour on and off is a
    mechanism wearing content's clothes, which is why only the list forms are
    matched here and a dict is left alone.
    """
    import ast

    import forms as _H

    ids = {it["id"] for h in _forms() for it in _H.config(h)["rubric"].ITEMS}
    out, found = [], set()
    for mod in _ENGINE_MODULES:
        try:
            # THROUGH `paths`, NOT THE WORKING DIRECTORY. This read
            # `Path(f"{mod}.py")`, which resolves against CWD -- so running the
            # audit from the repo root instead of `scoring/` made all four
            # modules unreadable and the check reported four findings saying it
            # could not run. It was right to say so rather than pass, but a
            # check that only works from one directory is a check that will
            # eventually be run from another. `check_filesystem_locations_come_
            # _from_paths_py` exists for exactly this.
            import paths as _pth_mod
            src = _pth_mod.module_source(mod)     # wherever it lives; see paths
            tree = ast.parse(src)
        except Exception as e:
            out.append(f"{mod}.py: cannot be parsed for item-gating "
                       f"({type(e).__name__}: {e}) -- the check cannot run, "
                       f"which is not the same as passing")
            continue
        for node in tree.body:            # module level only
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            val = node.value
            if not isinstance(val, (ast.Tuple, ast.List, ast.Set)):
                continue
            elts = [e.value for e in val.elts
                    if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            if not elts or not all(e in ids for e in elts):
                continue
            targets = ([node.target] if isinstance(node, ast.AnnAssign)
                       else node.targets)
            for tgt in targets:
                if not isinstance(tgt, ast.Name):
                    continue
                found.add((mod, tgt.id))
                if (mod, tgt.id) not in ITEM_GATED_MECHANISMS:
                    out.append(
                        f"{mod}.{tgt.id} = {elts} gates a MECHANISM on which "
                        f"item is being scored. Only rubric CONTENT may vary by "
                        f"item. Make it uniform, derive it from what the item "
                        f"declares, or declare it in ITEM_GATED_MECHANISMS with "
                        f"what would retire it")
        for node in ast.walk(tree):       # `item["id"] == "Q4a"` and friends
            if not isinstance(node, ast.Compare):
                continue
            lits = [c.value for c in [node.left, *node.comparators]
                    if isinstance(c, ast.Constant) and isinstance(c.value, str)
                    and c.value in ids]
            if not lits:
                continue
            seg = sourcecache.segment(src, node) or ""
            if '"id"' in seg or "'id'" in seg or ".id" in seg:
                out.append(
                    f"{mod}.py:{node.lineno}: `{seg[:70]}` branches on a "
                    f"literal item id. A mechanism may not vary by item")
    stale = [k for k in ITEM_GATED_MECHANISMS if k not in found]
    for k in sorted(stale):
        out.append(f"ITEM_GATED_MECHANISMS declares {k[0]}.{k[1]}, which no "
                   f"longer exists -- drop the declaration")
    n = len(found & set(ITEM_GATED_MECHANISMS))
    if n > ITEM_GATED_BUDGET:
        out.append(f"ITEM_GATED_MECHANISMS holds {n} against a budget of "
                   f"{ITEM_GATED_BUDGET}; an item-gated mechanism was added")
    return out


def _runs_files(root, pattern: str) -> list:
    """Every artifact matching `pattern`, in BOTH layouts a sweep writes.

    A sweep driven by `--out foo` writes `foo/<item>.runs.json`; one driven by a
    sweep script writes `foo/runs/<item>.runs.json`, and `measured.record`
    reaches the second only because the out path is handed to it explicitly. The
    audit had no such help: every check globbed `*/<item>.runs.json`, one level,
    so the nested layout was invisible to all of them.

    That is the shape of a check going quiet rather than wrong. On 2026-09-15 a
    paper sweep of all 26 items landed in `paper_0914/runs/`, correctly stamped
    with today's `paper_render_sha` -- and `check_paper_feedback_explains_its_deductions`
    reported all 26 items unattributable, because the only artifact it could see
    was an undated `pooled_paper/` from an earlier era. The freshest measurement
    on disk counted for nothing.

    Defined once so the two layouts cannot drift apart again.
    """
    return sorted(set(root.glob(pattern)) | set(root.glob(f"*/runs/{pattern.split('/')[-1]}")))


def check_paper_feedback_explains_its_deductions() -> list[str]:
    """On the PAPER side: does a deduction that costs points say why?

    THE PAPER ANALOGUE, and deliberately a different question. The web renders a
    checklist, so its failure is a tick beside no words. score.py renders a
    DEDUCTION LEDGER -- "-2 pts: reason" -- so full credit correctly prints
    nothing, and the failure is a charge whose reason is missing: the rubric has
    no text for the code and the model wrote no note, and the student reads a
    number with nothing after it.

    It also reports `unknown_codes`, which score.py records on every result and
    nothing has ever read. A code the scorer cannot interpret is dropped, so it
    costs no points -- but it means the grader answered in a vocabulary the
    rubric does not define, and dropping it silently is how that stays invisible.

    Attributed through `paper_render_sha`, for the reason the web check is: a
    wording fix moves neither the prompt nor the score, so an artifact written
    before one is otherwise indistinguishable from one written after.
    """
    import json
    import pathlib as _pl
    import re as _re

    import forms as H
    import measured as M
    import paths as _paths

    root, _why = _paths.out_root_or_reason()
    if root is None:
        return [f"{_why} -- this check cannot run, which is NOT the same as passing"]
    want = M.paper_render_sha()
    EMPTY = _re.compile(r"-\s*[\d.]+\s*pts?:\s*$")
    reasonless: dict = {}
    unknown: dict = {}
    benign: dict = {}
    unattributable: set = set()
    # ONE ATTRIBUTABLE ARTIFACT IS ENOUGH. The loop below adds an item to
    # `unattributable` on every artifact whose stamp is stale -- and the corpus
    # keeps every artifact it has ever written, so a single undated archival
    # directory condemned an item no matter how fresh its newest measurement
    # was. The message has always said "no paper artifact attributable", which
    # is the right question; the set was answering "some paper artifact is not".
    # On 2026-09-15 that reported all 26 items unattributable on the morning a
    # correctly-stamped sweep of all 26 landed. Same fault, same session, as the
    # web-side check that needed this exact set.
    attributed: set = set()
    for item in sorted(M._jobs()):
        try:
            cfg = H.config(M._jobs()[item]["handout"])["rubric"].BY_ID[item]
        except Exception:
            continue
        texts = {d["code"]: d.get("text", "") for d in cfg.get("deductions") or []}
        by_what = {c["what"]: c for c in cfg.get("credit") or []}
        for path in _runs_files(root, f"*/{item}.runs.json"):
            try:
                doc = jsoncache.load(path)
            except Exception:
                continue
            results = [r for run in (doc.get("runs") or [])
                       for r in (run.get("results") or [])]
            if not results or "item_id" not in results[0]:
                continue                       # not the paper scorer's to answer for
            era = doc.get("era") or {}
            stamp = ((era.get("items") or {}).get(item, {}) or {}).get(
                "paper_render_sha", era.get("paper_render_sha"))
            if stamp != want:
                unattributable.add(item)
                continue
            attributed.add(item)
            for r in results:
                if r.get("item_id") != item:
                    continue
                for d in r.get("deductions") or []:
                    if not (texts.get(d.get("code")) or "").strip() \
                            and not (d.get("note") or "").strip():
                        k = (item, str(d.get("code")))
                        reasonless[k] = reasonless.get(k, 0) + 1
                for line in str(r.get("feedback") or "").splitlines():
                    if EMPTY.search(line.strip()):
                        k = (item, "<a charge with no words after it>")
                        reasonless[k] = reasonless.get(k, 0) + 1
                for code in r.get("unknown_codes") or []:
                    # ONLY WHERE A CHARGE WAS POSSIBLE. `unknown_codes` is
                    # dominated by structure, not defect: a CLASSIFICATION slot
                    # is a credit component with no `codes`, no points and no
                    # met/absent vocabulary, so it is never "met", reaches the
                    # unknown branch on every cell, and is recorded harmlessly --
                    # 594 entries across the corpus, every one of them an
                    # unscored component. Reporting those would make this check
                    # permanently red and bury the case that matters: a slot
                    # that COULD have cost points failing in a way the rubric
                    # has no words for, where the student is charged nothing and
                    # told nothing about a real miss.
                    comp = by_what.get(str(code).split(":")[0])
                    if not comp or not (comp.get("pts") or comp.get("gates")):
                        benign[item] = benign.get(item, 0) + 1
                        continue
                    k = (item, str(code))
                    unknown[k] = unknown.get(k, 0) + 1
    out = []
    for (item, code), n in sorted(reasonless.items(), key=lambda kv: -kv[1]):
        out.append(f"{item}: a deduction charged points as {code!r} and the "
                   f"student read no reason for it -- x{n}")
    for (item, code), n in sorted(unknown.items(), key=lambda kv: -kv[1]):
        out.append(f"{item}: the paper scorer answered {code!r}, which the "
                   f"rubric defines no code for, so it was dropped -- x{n}. It "
                   f"cost nothing; it means the grader is answering in a "
                   f"vocabulary the rubric does not share")
    unattributable -= attributed
    if unattributable:
        out.append(f"{len(unattributable)} item(s) have no paper artifact "
                   f"attributable to today's feedback wording, so what their "
                   f"students read cannot be checked ({', '.join(sorted(unattributable))})")
    return out


def _render_code_unchanged_since(artifact: "pathlib.Path") -> bool:
    """Has the RENDERING SOURCE stood still since this artifact was written?

    THE FALLBACK FOR ARTIFACTS WITH NO PARTS MAP, and the reason it is needed.
    `web_code_sha("render")` hashes the functions named by `measured._web_parts`,
    so the fingerprint moves when OUR LIST changes as well as when lo-blocks
    does. Measured 2026-09-14: `slotSheet.ts` was byte-identical in both trees
    and untouched since 2026-09-13 14:05, the shipped `.olx` was unchanged, and
    the render stamp had still moved -- so 25 of 26 artifacts written AFTER that
    edit were reported unattributable to a renderer that had not changed. The
    remedy the finding implied was a ~3,100-call sweep to chase our own
    bookkeeping.

    This asks the question the fingerprint was standing in for, with evidence
    that does not route through the ledger at all: if the rendering source has
    not been modified since the artifact was written, the code that produced it
    IS the code running now, whatever our list says.

    MTIME OF THE SOURCE, WHICH IS WHAT MTIME IS GOOD FOR. The same session
    learned that an ARTIFACT's mtime is a poor proxy for when its runs happened,
    because a pooled file is dated by its assembly. That objection does not apply
    to a source file being asked when it last changed. It is still weaker than a
    stamp -- `era.web_parts` is the real fix and applies to everything written
    from now on -- so this is the fallback, not the primary.
    """
    import pathlib as _pl

    import paths as _P

    try:
        return _pl.Path(_P.SLOTSHEET_TS).stat().st_mtime < artifact.stat().st_mtime
    except OSError:
        return False                      # undeterminable stays unattributable


def check_students_see_what_each_check_decided() -> list[str]:
    """Does the student read a REASON beside every check that scored them?

    THE AUDIT COMPARES ENGINES, DECLARATIONS AND SCORES, and never once asked
    what reached the student. It is a different question with a different answer:
    a check can score perfectly and still render `- ✓ **Matches your first chosen
    type** — not reported`, a tick against no words, on a check carrying half the
    item. Scoring reads an operand as `refers_to ?? verdict`; three DISPLAY paths
    read only `.verdict`, and every shipped `equals`, `expect` and `maps` operand
    is a classification, which answers `refers_to`. The score was right and the
    explanation was blank, on 1046 recorded lines across 11 checks and 11 items.

    READ FROM THE ARTIFACTS, not from the renderer, for the reason subgoal E43
    gives: what a student SAW is a fact about a recorded run, and re-deriving it
    from today's code would report what they would see now. Aggregated per
    (item, check) rather than per line, because 1046 standing findings is a list
    nobody reads and 11 is one somebody fixes.

    Live artifacts only, via _artifact_prompt_state: a blank line under a prompt
    that no longer exists is history, and this is a defect report, not an archive.
    """
    import json
    import pathlib as _pl
    import re as _re

    import measured as M
    import paths as _paths

    MARKED = _re.compile(r"^- ([\u2713\u00b7]) \*\*(.+?)\*\* \u2014 (.*)$")
    root, _why = _paths.out_root_or_reason()
    if root is None:
        return [f"{_why} -- this check cannot run, which is NOT the same as passing"]
    def _app_wrote_it(doc: dict) -> bool:
        """Did the APP write this artifact? `cell` is its key, as result_cell says.

        The check gates on the WEB renderer, so a paper or harness artifact can
        never match and would be counted unattributable for ever -- conservative,
        but it conflates sides and pads the one line this check emits with items
        whose web column is fine. The paper scorer composes its own feedback and
        gets its own check; see check_paper_feedback_explains_its_deductions.
        """
        for run in doc.get("runs") or []:
            for r in run.get("results") or []:
                return "cell" in r
        return False
    tally: dict = {}
    looked = 0
    unattributable: set = set()
    attributed: set = set()
    for item in sorted(M._jobs()):
        for path in _runs_files(root, f"*/{item}.runs.json"):
            try:
                doc = jsoncache.load(path)
            except Exception:
                continue
            if _artifact_prompt_state(doc, item) is False:
                continue                       # prompt superseded: history
            # ATTRIBUTABLE TO TODAY'S RENDERER, OR NOT AT ALL. A display fix
            # moves neither `prompt_sha` nor the score, so an artifact written
            # before one looks exactly like an artifact written after it. Saying
            # "the student saw this" about text produced by code that has since
            # been repaired is a false report: `counts` members rendered "not
            # reported" until the app was fixed, and those artifacts still do.
            if not _app_wrote_it(doc):
                continue                       # not the web's renderer to answer for
            era = doc.get("era") or {}
            stamp = ((era.get("items") or {}).get(item, {}) or {}).get(
                "web_render_sha", era.get("web_render_sha"))
            if stamp != M.web_code_sha("render", item) and \
                    not _render_code_unchanged_since(path):
                unattributable.add(item)
                continue
            # ONE ATTRIBUTABLE ARTIFACT IS ENOUGH. The message says an item has
            # NO artifact attributable to today's renderer, and the set was
            # accumulating on the FIRST artifact that failed -- so an item with a
            # current sweep was still reported because some older artifact of the
            # same item did not attribute. Every item has many artifacts and most
            # are old, which is why this reported the whole corpus.
            attributed.add(item)
            looked += 1
            for run in doc.get("runs") or []:
                for r in run.get("results") or []:
                    for line in str(r.get("feedback") or "").splitlines():
                        m = MARKED.match(line.strip())
                        if m and m.group(3).strip().startswith("not reported"):
                            key = (item, m.group(2))
                            tally[key] = tally.get(key, 0) + 1
    out = []
    # ONE attributable artifact is enough: the message says an item has NO
    # artifact attributable, and the set accumulates on every artifact that
    # fails. Every item has many and most are old.
    unattributable -= attributed
    if unattributable:
        out.append(
            f"{len(unattributable)} item(s) have no artifact attributable to "
            f"today's renderer, so what their students see cannot be checked at "
            f"all ({', '.join(sorted(unattributable))}). Each is answered by its "
            f"next sweep, which stamps `web_render_sha`; until then this check is "
            f"silent about them rather than guessing from text an older renderer "
            f"produced")
    if not looked:
        return out or ["no readable artifact carries rendered feedback, so what "
                       "the student saw cannot be checked -- sweep, or say why not"]
    return out + [
        f"{item}: the student read a tick or a cross beside "
        f"'{label}' with the words 'not reported' -- x{n}. That check scored "
        f"them and told them nothing. A computed check has no verdict of its "
        f"own, so its line must render what it was computed FROM"
        for (item, label), n in sorted(tally.items(), key=lambda kv: -kv[1])
    ]


def _request_capture() -> tuple:
    """({cell: {prompt, schema}}, why_not). Captured from the APP, then cached.

    Runs lo-blocks' promptcapture.test.ts, which renders each real screen, seeds
    the fixture and clicks the real button with `callLLMJson` MOCKED -- so it
    records the assembled request and spends no tokens and no endpoint. 26 items
    in one vitest run, ~26s.

    CACHED AGAINST WHAT COULD CHANGE IT: the app's schema-building fingerprint,
    the .olx files and the idmap dump. An ordinary audit re-reads the cache and
    costs nothing; the capture re-runs only when one of those moves. Without a
    cache this would put ~26s on every commit for an answer that changes rarely.
    """
    import hashlib
    import json
    import os
    import subprocess

    import measured as M
    import paths as P

    lo = P.LO
    runner = lo / "packages/shared/lib/llm/promptcapture.test.ts"
    if not runner.exists():
        return {}, f"{runner} is missing, so the app's own request cannot be read"
    if not (lo / "node_modules").is_dir():
        return {}, f"{lo}/node_modules is absent, so the capture cannot be run"
    dumps = sorted(P.OUT.glob("idmap*.json"))
    if not dumps:
        return {}, ("no idmap dump under out/, so the app cannot be rendered -- "
                    "take one with `curl -s 'http://localhost:8888/api/olxjson?id=all'`")
    idmap = max(dumps, key=lambda f: f.stat().st_mtime)
    try:
        key = hashlib.sha256("|".join([
            M.web_code_sha("ask"), str(idmap), str(int(idmap.stat().st_mtime)),
            *(str(int((P.OLX % h and __import__("pathlib").Path(P.OLX % h)).stat().st_mtime))
              for h in _forms()),
        ]).encode()).hexdigest()[:16]
    except Exception as e:
        return {}, f"the capture key cannot be computed: {type(e).__name__}: {e}"
    cache = P.OUT / "request_capture.json"
    if cache.exists():
        try:
            got = jsoncache.load(cache)
            if got.get("key") == key:
                return got.get("capture") or {}, ""
        except Exception:
            pass                            # unreadable cache: re-capture
    # BUILD THE JOBS HERE, one cell per item, because the capture needs a real
    # fixture to render and the fixture is this package's job, not lo-blocks'.
    try:
        import agreement_app as AA
        jobs = []
        for item in sorted(AA.JOBS):
            excl = set(M.exclusions(item) or [])
            pid = next((p for p in range(1, 21) if p not in excl), 1)
            jobs += AA.build_jobs(item, [pid])
    except Exception as e:
        return {}, f"the capture jobs cannot be built: {type(e).__name__}: {e}"
    import tempfile
    tmp = tempfile.mkdtemp(prefix="reqcap_")
    jf, of = os.path.join(tmp, "jobs.json"), os.path.join(tmp, "out.json")
    json.dump(jobs, open(jf, "w"))
    env = {**os.environ, "RUN_PROMPT_CAPTURE": "1", "JOBS_JSON": jf,
           "IDMAP_JSON": str(idmap), "PROMPT_OUT": of}
    try:
        r = subprocess.run(
            ["npx", "vitest", "run", "packages/shared/lib/llm/promptcapture.test.ts"],
            cwd=lo, env=env, capture_output=True, text=True, timeout=900)
    except Exception as e:
        return {}, f"the capture run failed: {type(e).__name__}: {e}"
    if not os.path.exists(of):
        tail = (r.stderr or r.stdout or "")[-300:]
        return {}, f"the capture produced no file (exit {r.returncode}): {tail}"
    capture = json.load(open(of))
    try:
        cache.write_text(json.dumps({"key": key, "capture": capture}))
    except Exception:
        pass
    return capture, ""


def _recorded_payloads():
    """RETIRED 2026-09-24 with the python web engine. ALWAYS RETURNS ({}, []).

    It rebuilt every recorded response so BOTH engines could be run over it.
    `check_engines_read_a_response_the_same_way` was retired with the mirror;
    this fed it and was left behind -- still selecting items by
    `agreement.SCORERS`, the eliminated registry. So the AUDIT ITSELF raised
    `AttributeError` inside `engine_interpretation_line` and stopped early, and
    two audits on 2026-09-25 were read as complete before that was noticed. A
    retirement is not finished until the things that CALLED the retired check
    are retired too.

    Kept as a stub rather than deleted: `_interpretation_comparison` is
    monkeypatched by equivalence.py's selftest, and a name that vanishes from
    under a patch fails in a way that says nothing about why.
    """
    return {}, []


def _app_scores(sheets: dict, payloads: list) -> tuple:
    """({id: {score,max}}, why_not) from the APP'S OWN scorer, cached.

    Cached against what could change the answer: the app's scoring fingerprint
    and the artifacts the payloads come from. An ordinary audit re-reads the
    cache; the capture re-runs when the app's scorer or a sweep moves.
    """
    import hashlib
    import json
    import os
    import subprocess
    import tempfile

    import measured as M
    import paths as P

    lo = P.LO
    runner = lo / "packages/shared/lib/llm/scorecapture.test.ts"
    if not runner.exists():
        return {}, f"{runner} is missing, so the app's own scorer cannot be run"
    if not (lo / "node_modules").is_dir():
        return {}, f"{lo}/node_modules is absent, so the app's scorer cannot be run"
    try:
        # THE PAYLOADS THEMSELVES, not their count. Keyed on the count alone,
        # a change to how a payload is RECONSTRUCTED -- the count/verdict fix
        # below, say -- leaves the key identical and the stale capture is served
        # back as if it had been re-scored.
        key = hashlib.sha256("|".join([
            M.web_code_sha("score"),
            hashlib.sha256(json.dumps(
                [[p["id"], p["checks"], p["max"]] for p in payloads],
                sort_keys=True).encode()).hexdigest(),
            # THE SHEETS TOO. Keyed on the payloads alone, a change to the RULES
            # -- a slot gaining a `free` list, say -- leaves the key identical
            # and the stale capture is served back as though it had been
            # re-scored, which reports the app disagreeing with a rule it was
            # never given.
            hashlib.sha256(json.dumps(sheets, sort_keys=True,
                                      default=str).encode()).hexdigest(),
            *(f"{i}:{sd}:{mt}:{sz}" for i, sd, mt, sz in M._artifact_fingerprint()),
        ]).encode()).hexdigest()[:16]
    except Exception as e:
        return {}, f"the score-capture key cannot be computed: {type(e).__name__}: {e}"
    cache = P.OUT / "score_capture.json"
    if cache.exists():
        try:
            got = jsoncache.load(cache)
            if got.get("key") == key:
                return got.get("scores") or {}, ""
        except Exception:
            pass
    tmp = tempfile.mkdtemp(prefix="scorecap_")
    inp, outp = os.path.join(tmp, "in.json"), os.path.join(tmp, "out.json")
    json.dump({"sheets": sheets,
               "payloads": [{k: p[k] for k in ("id", "item", "checks", "max")}
                            for p in payloads]}, open(inp, "w"))
    env = {**os.environ, "RUN_SCORE_CAPTURE": "1",
           "SCORE_IN": inp, "SCORE_OUT": outp}
    try:
        r = subprocess.run(
            ["npx", "vitest", "run",
             "packages/shared/lib/llm/scorecapture.test.ts"],
            cwd=lo, env=env, capture_output=True, text=True, timeout=1800)
    except Exception as e:
        return {}, f"the score capture failed: {type(e).__name__}: {e}"
    if not os.path.exists(outp):
        tail = (r.stderr or r.stdout or "")[-300:]
        return {}, f"the score capture produced no file (exit {r.returncode}): {tail}"
    scores = json.load(open(outp))
    try:
        cache.write_text(json.dumps({"key": key, "scores": scores}))
    except Exception:
        pass
    return scores, ""


def _interpretation_comparison() -> dict:
    """See `_interpretation_comparison_cached`; cached on the artifacts' fingerprint.

    MEMOISED because the audit's own selftest calls it once per case. It re-scores
    every recorded response through the harness -- 5,668 of them -- and that side
    has no cache of its own, so an uncached call took the suite from ~40 minutes
    to ~80 as soon as this check joined it. Keyed on the artifacts exactly as
    `scoring_logic_agreement` is, so a re-sweep still invalidates it; a copy is
    returned so a caller that mutates the result cannot poison the next one.
    """
    import measured as M

    d = _interpretation_comparison_cached(M._artifact_fingerprint())
    return {"n": d["n"], "differ": list(d["differ"]), "errors": list(d["errors"]),
            "control": {k: list(v) for k, v in d["control"].items()},
            "rules_moved": d.get("rules_moved", 0), "stale": d.get("stale", 0),
            "why_not": d.get("why_not", "")}


@functools.lru_cache(maxsize=4)
def _interpretation_comparison_cached(_fingerprint: tuple) -> dict:
    """RETIRED 2026-09-24 with the python web engine. NEVER COMPARES.

    It re-scored all 5,668 recorded responses through both engines. With one
    engine there is no second side, so it reports `why_not` -- the shape its
    readers already handle for "this could not be compared" -- rather than an
    agreement it never measured.
    """
    return {"n": 0, "differ": [], "errors": [], "control": {},
            "rules_moved": 0, "stale": 0,
            "why_not": "the python web engine was eliminated (goal O), so a "
                       "recorded response has only one engine to read it"}


def _app_envelope() -> tuple:
    """(body, why_not) -- the POST body the APP builds, captured from its own code.

    `fetch` is mocked, so nothing is sent. A FIXED probe prompt, because the
    envelope does not depend on the content and the content is already compared
    by `check_engines_send_the_same_request`; this isolates everything AROUND it.
    """
    import json
    import os
    import subprocess
    import tempfile

    import paths as P

    lo = P.LO
    runner = lo / "packages/shared/lib/llm/envelopecapture.test.ts"
    if not runner.exists():
        return {}, f"{runner} is missing, so the app's envelope cannot be read"
    if not (lo / "node_modules").is_dir():
        return {}, f"{lo}/node_modules is absent, so the app's envelope cannot be read"
    out = os.path.join(tempfile.mkdtemp(prefix="envcap_"), "env.json")
    env = {**os.environ, "RUN_ENVELOPE_CAPTURE": "1", "ENVELOPE_OUT": out}
    try:
        r = subprocess.run(
            ["npx", "vitest", "run",
             "packages/shared/lib/llm/envelopecapture.test.ts"],
            cwd=lo, env=env, capture_output=True, text=True, timeout=600)
    except Exception as e:
        return {}, f"the envelope capture failed: {type(e).__name__}: {e}"
    if not os.path.exists(out):
        tail = (r.stderr or r.stdout or "")[-300:]
        return {}, f"the envelope capture produced no file (exit {r.returncode}): {tail}"
    return json.load(open(out)), ""


def _harness_envelope(prompt: str, schema: dict) -> tuple:
    """(body, why_not) -- the POST body the HARNESS builds, captured from its own code.

    `urlopen` is replaced, so nothing is sent: the backend is driven exactly as a
    sweep drives it and the request is taken at the boundary. Reading the payload
    out of the source by eye is what this replaces -- the same distinction that
    made `_request_capture` necessary.
    """
    import json
    import urllib.request

    import agreement as A

    seen = {}

    class _Stop(Exception):
        pass

    def _fake(req, *a, **k):
        seen["body"] = json.loads(req.data.decode())
        seen["url"] = req.full_url
        seen["headers"] = dict(req.headers)
        raise _Stop()

    real = urllib.request.urlopen
    urllib.request.urlopen = _fake
    try:
        A.LoBlocksBackend().complete(prompt, schema, retries=0)
    except Exception:
        pass                               # _Stop, or the retry loop giving up
    finally:
        urllib.request.urlopen = real
    if "body" not in seen:
        return {}, "the harness backend built no request to capture"
    return seen, ""

# A key one engine sends and the other does not is a difference UNLESS the
# server strips it before forwarding. Each entry names the key and is checked
# against `routes/llm.ts` actually deleting it -- a declaration that stops being
# true stops being accepted.
_ENVELOPE_STRIPPED = ("activity", "profile")


# A verdict a scored slot can answer, that the paper ledger deliberately does
# NOT charge. The web fails anything that is not the satisfying verdict, so an
# entry here is a real difference between the engines -- it is declared, with the
# measurement that settled it, rather than repaired.
UNCHARGED_VERDICTS = _declaration("UNCHARGED_VERDICTS")


def check_every_failing_verdict_has_a_charge() -> list[str]:
    """Can a scored slot answer something the paper ledger charges nothing for?

    THE AUTHORING FORM of a difference that otherwise waits for the model to
    produce it. The web fails anything that is not the satisfying verdict; the
    paper ledger charges only what a deduction CODE names. So a third verdict
    with no code is scored by one engine and forgiven by the other -- and it
    stays invisible until the model happens to answer it, which for Q1's
    `unclear` took 62 observations and one cell.

    Read off the RUBRIC rather than the artifacts, so a new verdict added to a
    slot is caught when it is authored instead of a sweep later. That is the
    difference between this and `check_paper_reproduces_web_scores`, which finds
    the same fault only where a run happened to exercise it.

    An entry in UNCHARGED_VERDICTS is a decision, not a silence: Q1's is there
    because gold sides with the paper scorer, so charging would be the defect.
    """
    # A verdict one engine scores and the other forgives is a difference
    # authored into the rubric.
    # PYTHON KEEPS THE FETCH. The self-test injects by CLEARING
    # `UNCHARGED_VERDICTS` in memory and forking -- "a forgiven verdict loses
    # its declaration" -- and a payload the runner rebuilds from `course.json`
    # cannot see that. Measured 2026-09-26: before=0, after=0.
    import forms as _H_fv
    import measured as _M_fv

    import lo_enforce

    items = []
    for item_id in sorted(_M_fv._jobs()):
        try:
            it = _H_fv.config(_M_fv._jobs()[item_id]["handout"])["rubric"].BY_ID.get(item_id)
        except Exception:
            it = None
        credit = []
        for c in (it or {}).get("credit") or []:
            try:
                offered = _olx_slot_verdicts(item_id, c.get("what"))
            except Exception:
                offered = set()
            credit.append({
                "what": c.get("what"), "pts": c.get("pts"),
                "verdicts": list(c.get("verdicts") or []),
                "codes": dict(c.get("codes") or {}),
                "offered": None if offered is None else sorted(offered),
            })
        items.append({"id": item_id, "credit": credit})
    return lo_enforce.run("every_failing_verdict_has_a_charge", {
        "items": items,
        "divergences": [[sorted(w), sorted(p)]
                        for w, p in VERDICT_SPACE_DIVERGENCES],
        "uncharged": [list(t) for t in sorted(UNCHARGED_VERDICTS)],
    })


def check_engines_reach_the_model_identically() -> list[str]:
    """Do the app and the harness put the SAME request on the wire?

    THE LAST PLACE A DIFFERENCE COULD HIDE. The prompt and schema are compared
    by `check_engines_send_the_same_request`. The other two siblings named here
    -- `check_engines_read_a_response_the_same_way` and
    `check_engines_score_identical_verdicts_alike` -- were RETIRED with the
    python web engine in goal O, because reading a response and scoring it were
    the mirror's half of the comparison. Those compared CONTENT.
    None compares the envelope around it -- `model`, `max_completion_tokens`,
    `temperature`, `top_p`, `seed`, the endpoint -- and a difference in any of
    those moves every score on every item while leaving the prompt audit
    perfectly clean. It is the explanation that would have survived every check
    this package had, which is why it needed one of its own.

    Both bodies are CAPTURED from the two code paths, not read out of the source
    by eye: `fetch` is mocked on one side and `urlopen` on the other, so nothing
    is sent and nothing is spent.

    Server-side injection is compared too, because the body that leaves the
    process is not the body that reaches the provider: the route deletes
    `activity` and `profile`, injects `max_completion_tokens` from the resolved
    profile, and sets `model`. Those are identical for both paths only while
    neither sends `profile` and no PMSS rule keyed on the guest/authorized class
    sets a generation property -- both of which are checked here rather than
    assumed, since the app may carry a session the harness does not.

    "THE TWO ENGINES" IS NOW THE APP AND THE HARNESS ASK PATH (2026-09-25).
    Goal O eliminated the python mirror of `scoreSlotSheet`, so `engine` no
    longer denotes one of two scorers. Both sides of this check are still
    live code and it still compares them; only the word was wrong, and a
    reader who takes it at face value concludes the check is dead.
    """
    import json
    import re

    import paths as P

    app, why_app = _app_envelope()
    if why_app:
        return [f"the two engines' requests could not be compared: {why_app}"]
    body_app = app.get("body") or {}
    probe = (body_app.get("messages") or [{}])[0].get("content") or "PROBE"
    schema = (((body_app.get("response_format") or {}).get("json_schema") or {})
              .get("schema") or {})
    mine, why_mine = _harness_envelope(probe, schema)
    if why_mine:
        return [f"the two engines' requests could not be compared: {why_mine}"]
    body_mine = mine.get("body") or {}

    out = []
    route = P.LO / "apps/server/src/routes/llm.ts"
    src = route.read_text() if route.exists() else ""
    for key in _ENVELOPE_STRIPPED:
        if not re.search(rf"delete\s+body\.{re.escape(key)}\b", src):
            out.append(f"`{key}` is declared as stripped by the server, but "
                       f"{route.name} no longer deletes it -- so it now reaches "
                       f"the provider on one engine and not the other")

    for key in sorted(set(body_app) | set(body_mine)):
        a, b = body_app.get(key, "<absent>"), body_mine.get(key, "<absent>")
        if a == b or key in _ENVELOPE_STRIPPED:
            continue
        # The PROMPT and SCHEMA are compared by their own check, against every
        # item rather than one probe; reporting them here would duplicate it.
        if key in ("messages", "response_format"):
            continue
        out.append(f"the engines send a different `{key}`: app "
                   f"{json.dumps(a)[:90]}, harness {json.dumps(b)[:90]}. Same "
                   f"model, same prompt -- and a different request")

    if str(app.get("url", "")).split("/api/")[-1] != \
       str(mine.get("url", "")).split("/api/")[-1]:
        out.append(f"the engines post to different routes: app "
                   f"{app.get('url')}, harness {mine.get('url')}")

    # `profile` decides max_completion_tokens and the model. Neither engine sends
    # one, so both resolve the same default -- a check rather than a comment,
    # because one engine gaining a profile would silently re-point the other.
    for name, b in (("app", body_app), ("harness", body_mine)):
        if b.get("profile"):
            out.append(f"the {name} now sends profile={b['profile']!r}, which "
                       f"selects the model and token cap; the other engine does "
                       f"not, so they no longer resolve the same configuration")

    pmss = P.LO / "config/server.pmss"
    if pmss.exists():
        txt = re.sub(r"/\*.*?\*/", "", pmss.read_text(), flags=re.S)
        for sel, block in re.findall(r"([^{}]+)\{([^}]*)\}", txt):
            if not re.search(r"\.(guest|authorized)\b", sel):
                continue
            for prop in ("llm-model", "llm-provider", "llm-max-tokens"):
                if re.search(rf"\b{prop}\s*:", block):
                    out.append(
                        f"PMSS rule `{sel.strip()}` sets `{prop}`, which is a "
                        f"GENERATION property keyed on authentication. The app "
                        f"carries a session the harness does not, so the two "
                        f"engines would resolve different ones and every "
                        f"comparison between them would be measuring that")
    return out


def _side_is_stale(item: str, side: str) -> bool:
    """Is this side's recorded artifact a measurement of the CURRENT tree?"""
    import measured as M

    try:
        e = M.entry(item, side)
        if not e:
            return False
        return (e.get("prompt_sha") not in (None, M.prompt_sha(item, side))
                or e.get("scorer_sha") not in (None, M.scorer_sha(item, side)))
    except Exception:
        return False


def check_engines_read_a_response_the_same_way() -> list[str]:
    """RETIRED 2026-09-24 with the python web engine. ALWAYS RETURNS [].

    It watched: the two engines read a recorded response alike.

    THAT QUESTION NO LONGER HAS TWO SIDES. The python mirror of
    `scoreSlotSheet` was eliminated in goal O, so this would compare a
    thing against itself or against nothing. O's own text named the
    class: "a check that exists to catch drift between two
    implementations is dead weight once there is one implementation".

    KEPT AS A RECORD rather than deleted, so what STOPPED being watched
    stays legible -- the same treatment as
    `check_no_slot_is_both_asked_and_computed`.
    """
    return []


def engine_interpretation_line() -> str:
    """Coverage for the check above, as audit context rather than a finding."""
    d = _interpretation_comparison()
    if d.get("why_not"):
        return f"engine reading: NOT COMPARED -- {d['why_not']}"
    ctl = ", ".join(f"{s} {ok}/{n}" for s, (ok, n) in sorted(d["control"].items()) if n)
    moved = (d.get("rules_moved") or 0) + (d.get("stale") or 0)
    moved_s = (f" {moved} cell(s) left OUT of the control, where a side scored a "
               f"recorded verdict its own rules now recompute." if moved else "")
    return (f"engine reading: {d['n']} recorded response(s) scored by BOTH "
            f"engines, {len(d['differ'])} of them scored differently. Controls "
            f"(each engine reproducing its own recorded score): {ctl}.{moved_s} This is "
            f"every recorded response, not only the verdict combinations both "
            f"engines reached.")


def check_engines_send_the_same_request() -> list[str]:
    """Do the app and the harness send the SAME prompt and the SAME schema?

    THE DEEP FORM of check_engines_offer_the_same_verdicts, and the one that
    found the divergence in the first place. Everything else compares a PART:
    the served body, the rubric elements, the schema's property names read out of
    buildSlotSchema's source. This compares the strings that actually go on the
    wire -- the app's, captured out of the running blocks, against the harness's,
    built by agreement.py -- because a difference can live in the assembly rather
    than in any part.

    NEVER SILENTLY CLEAN. A capture that returns nothing looks exactly like "no
    difference", which is the failure mode this check is most at risk of: the
    same shape cost me an hour when a hand-rolled idmap reader returned 0 chars
    and I nearly reported it as evidence. So a capture that cannot run says so
    and names what is missing, rather than passing.

    WHITESPACE IS REPORTED SEPARATELY from text, because they are different
    facts: the two assemblers indent wrapped lines differently (58 characters on
    Q4b), which is worth knowing and is not the same as asking a different
    question.

    "THE TWO ENGINES" IS NOW THE APP AND THE HARNESS ASK PATH (2026-09-25).
    Goal O eliminated the python mirror of `scoreSlotSheet`, so `engine` no
    longer denotes one of two scorers. Both sides of this check are still
    live code and it still compares them; only the word was wrong, and a
    reader who takes it at face value concludes the check is dead.
    """
    import json

    import agreement as A
    import olx_prompts as O

    capture, why_not = _request_capture()
    if why_not:
        return [f"the two engines' actual requests could not be compared: {why_not}"]
    out = []
    for cell, got in sorted(capture.items()):
        pid_s, item = cell.split("/", 1)
        if str(got.get("schema", "")).startswith("__ERROR__"):
            out.append(f"{item}: the app could not be driven to a request: "
                       f"{got['schema'][:120]}")
            continue
        try:
            pid = int(pid_s.lstrip("p"))
            h = O.FORM[item]
            act = A.load_action(_p7.handout_olx(h), O.ACTION[item])
            mine = (A.build_prompt(act["body"], A.fixture_for(item, pid))
                    + A.checklist_guidance(act["show_checks"]))
            my_schema = A.build_schema(act["slots"], act["excluded"],
                                       act["show_checks"], act["cover"], act["choices"])
        except Exception as e:
            out.append(f"{item}: the harness's own request cannot be built: "
                       f"{type(e).__name__}: {e}")
            continue
        theirs = got.get("prompt") or ""
        if theirs != mine:
            same_words = theirs.split() == mine.split()
            kind = ("identical apart from WHITESPACE" if same_words
                    else "DIFFERENT TEXT")
            out.append(
                f"{item}: the app and the harness send different prompts -- "
                f"{kind} ({len(theirs)} chars vs {len(mine)}). The body, the "
                f"rubric elements and the schema's property names can all match "
                f"while the assembled string does not")
        norm = lambda o: json.dumps(o, sort_keys=True)
        try:
            if norm(json.loads(got.get("schema") or "{}")) != norm(my_schema):
                out.append(
                    f"{item}: the app and the harness send different SCHEMAS. "
                    f"A verdict one side offers and the other does not is a "
                    f"different question, and the answers are not comparable")
        except Exception as e:
            out.append(f"{item}: the captured schema cannot be read: "
                       f"{type(e).__name__}: {e}")
    return out


def check_engines_offer_the_same_verdicts() -> list[str]:
    """Do the app and the harness offer the SAME verdict list, slot by slot?

    FOUND 2026-09-12 BY CAPTURING WHAT EACH ENGINE ACTUALLY SENDS, and invisible
    to every instrument that existed. The three that look like they cover it do
    not: `check_app_and_harness_send_the_same_prompt` compares the BODY TEXT,
    `equivalence.py --item` compares which RUBRIC ELEMENTS appear, and
    `schema_divergences` compares `build_schema` against a REGEX READING OF
    `buildSlotSchema`'s SOURCE -- property names and order. A verdict enum is
    built from runtime slot data and appears in none of those, so all three were
    clean while the two engines were asking different questions.

    THE DIVERGENCE THEY MISSED. A slot that names no verdicts of its own falls
    back to a DEFAULT, and the two defaults disagree:

        slotSheet.ts   DEFAULT_VERDICTS = ['met', 'absent']
        agreement.py   "met,absent,unclear"        (the `verd_m else` literal)

    So on every item with no `verdicts=` attribute, the harness offers `unclear`
    and the app does not. On Q4b that is `modify_stated` (2 pts), `modify_why`
    (1 pt) and `confident`; `is_satisfied` requires exactly `met`, so an
    `unclear` COSTS THE POINTS on one side and cannot be said on the other.
    goals.py records the same mechanism doing real damage on Q2's
    `wgb_inverts_utb` -- "an extra option to reach for", five divergences in 120.

    CHEAP ON PURPOSE, because it runs on every audit: each side's own code path
    supplies its own default, the slots are parsed twice in Python, and nothing
    is launched. The deeper instrument -- capturing the assembled prompt and the
    real schema out of the running app -- is
    lo-blocks/packages/shared/lib/llm/promptcapture.test.ts, which mocks the
    provider call and so costs nothing but is too heavy for an audit.

    "THE TWO ENGINES" IS NOW THE APP AND THE HARNESS ASK PATH (2026-09-25).
    Goal O eliminated the python mirror of `scoreSlotSheet`, so `engine` no
    longer denotes one of two scorers. Both sides of this check are still
    live code and it still compares them; only the word was wrong, and a
    reader who takes it at face value concludes the check is dead.
    """
    import re as _re

    import agreement as A
    import olx_prompts as O
    import paths as P

    try:
        ts = open(P.SLOTSHEET_TS).read()
    except OSError as e:
        return [f"cannot read {P.SLOTSHEET_TS}: {e}"]
    m = _re.search(r"export const DEFAULT_VERDICTS\s*=\s*\[([^\]]*)\]", ts)
    if not m:
        return ["DEFAULT_VERDICTS not found in slotSheet.ts -- this audit is stale"]
    app_default = [v.strip().strip("'\"") for v in m.group(1).split(",") if v.strip()]

    out = []
    for item, action_id in sorted(O.ACTION.items()):
        try:
            h = O.FORM[item]
            olx = open(P.OLX % h).read()
            el = _re.search(r"<LLMAction\b[^>]*\bid=\"%s\".*?</LLMAction>"
                            % _re.escape(action_id), olx, _re.S)
            if not el:
                continue
            open_tag = el.group(0)[:el.group(0).index(">") + 1]
            spec = _re.search(r'slots="([^"]*)"', open_tag, _re.S)
            if not spec:
                continue
            verd = _re.search(r'verdicts="([^"]*)"', open_tag, _re.S)
            # The app's own fallback, and the harness's own, each via its own path.
            app_defaults = ([v.strip() for v in verd.group(1).split(",") if v.strip()]
                            if verd else app_default)
            app_slots = {s["key"]: s.get("options") or []
                         for s in O.parse_slots(spec.group(1), app_defaults)}
            py_slots = {s["key"]: s.get("options") or []
                        for s in A.load_action(_p7.handout_olx(h), action_id)["slots"]}
        except Exception as e:
            out.append(f"{item}: cannot compare verdict lists: {type(e).__name__}: {e}")
            continue
        # ONLY WHAT THE GRADER IS ASKED. A COMPUTED slot -- an `equals`, `maps`,
        # `derived`, `expect` or `forbid` target -- is excluded from both sides'
        # response schemas, so the two sheets can declare different verdict lists
        # for it and no grader will ever see either. Verified against the real
        # captured requests: of 76 slots where the declarations differ, 19 are
        # computed and absent from the app's schema; the other 57 are genuinely
        # offered, 13 of them on slots that carry points. Reporting the 19 would
        # be claiming a difference in a question nobody is asked.
        try:
            excluded = set(A.load_action(_p7.handout_olx(h), action_id)["excluded"])
        except Exception:
            excluded = set()
        silent = 0
        for key in sorted(set(app_slots) & set(py_slots)):
            a, p = app_slots[key], py_slots[key]
            if a != p and key in excluded:
                silent += 1
                continue
            if a != p:
                out.append(
                    f"{item}.{key}: the app offers {a} and the harness offers {p}. "
                    f"The two engines are asking the grader a different question, "
                    f"so their answers are not comparable on this slot -- and a "
                    f"verdict only one side can say is one only that side can be "
                    f"charged for")
        if silent:
            out.append(
                f"{item}: {silent} computed slot(s) also declare different "
                f"verdict lists on the two sides. No grader is asked them, so "
                f"nothing can answer differently -- recorded rather than "
                f"reported as a divergence, so the count is not silently lost")
    return out


def check_every_sweep_is_recorded() -> list[str]:
    """Is there a NEWER measurement on disk than the one the ledger records?

    THE GAP THIS CLOSES, measured 2026-09-14 and paid for the same day. A
    fifteen-item re-sweep finished, nothing recorded it, and the next audit read
    the OLD artifacts: eleven cells reported as "PAPER AND WEB SCORE THE SAME
    JUDGMENTS DIFFERENTLY", ten of which had already been resolved by the sweep,
    plus a 26-item aggregate saying no column could be dated against the app's
    own code -- because the columns pointed at artifacts written before that
    stamp existed. Every one of those findings was about a STALE POINTER, not
    about the tree, and nothing in the audit said so.

    Recording is not bookkeeping that can wait. Until it happens the ledger
    describes a measurement that has been superseded, and every check reading
    `_runs_doc` is reading the superseded one. The failure is silent and it
    points AWAY from the cause: it invites you to debug a scoring difference
    that no longer exists.

    WHAT COUNTS AS NEWER, and why mtime rather than the shas. An artifact whose
    stamps match today's could still be the one already recorded, and an
    artifact whose stamps differ could be an older run that is legitimately
    superseded. What makes a sweep unrecorded is that it was WRITTEN after the
    artifact the ledger points at, for the same column, by the program that side
    contracts to. Mtime says exactly that and nothing else.
    """
    import json

    import measured as M
    import paths as P

    out = []
    for item in sorted(M._jobs()):
        for side in ("olx", "paper", "paper_opus"):
            rec = M.entry(item, side)
            if not rec:
                continue
            recorded = M._runs_path(item, side)
            # DATE THE RUNS, NOT THE FILE. `era.measured_at` says when the
            # grader ran; mtime says when someone last wrote the file, and for a
            # pooled or folded artifact those are different dates. Preferring
            # mtime made `pooled_paper` -- an assembly containing a FAILED
            # cell-fill -- look newer than the clean measurement it superseded.
            # Fall back to mtime only when there is no stamp, and say so.
            floor, floor_dated = 0.0, False
            if recorded:
                rp = pathlib.Path(recorded)
                floor = rp.stat().st_mtime
                try:
                    rdoc = jsoncache.load(rp)
                    at = ((rdoc.get("era") or {}).get("measured_at") or "")
                    if at:
                        import datetime as _dt
                        floor = _dt.datetime.fromisoformat(at).timestamp()
                        floor_dated = True
                except Exception:
                    pass
            # THE CONTRACT IS A PAIR, (shape, model), and comparing only the
            # shape advised recording an OPUS artifact into the `paper` column:
            # `pooled_paper_opus` has the right shape and the wrong model, and
            # `--record` would refuse it on the same contract. Decision 11.3
            # excludes paper_opus from acceptance outright, so the advice was
            # not merely useless -- it pointed at work that must not be done.
            want_shape, want_model = M.SIDE_CONTRACT[side]
            newer, incomplete = [], []
            for cand in _runs_files(P.OUT, f"*/{item}.runs.json"):
                try:
                    doc = jsoncache.load(cand)
                    at = ((doc.get("era") or {}).get("measured_at") or "")
                    if at:
                        import datetime as _dt
                        when = _dt.datetime.fromisoformat(at).timestamp()
                    else:
                        # UNDATEABLE. It cannot show it is newer, so it does not
                        # get to displace a dated measurement -- and if the
                        # RECORDED one is itself undated, neither can claim
                        # recency and mtime is all there is.
                        if floor_dated:
                            continue
                        when = cand.stat().st_mtime
                    if when <= floor:
                        continue
                except Exception:
                    continue
                if M._artifact_program(doc) != want_shape:
                    continue
                got_model = (doc.get("era") or {}).get("model") or ""
                if want_model not in got_model:
                    continue        # right shape, wrong model: another column's
                # A SWEEP WITH FAILED CELLS IS NOT A RECORDABLE SWEEP, and
                # saying "record this" about one sends the reader at a refusal.
                # `pooled_paper` is newer than the NP/PP columns and carries six
                # cells the provider never returned JSON for -- the recorded
                # 3-run artifacts are CLEAN, so the newer one is worse, not
                # later. Report it as needing a cell-fill, not as a backlog.
                dead = sum(1 for run in (doc.get("runs") or [])
                           for c in (run.get("results") or [])
                           if c.get("score") is None
                           and not (c.get("checks") or c.get("verdicts")))
                (incomplete if dead else newer).append(
                    f"{cand.parent.name} ({dead} failed cell(s))" if dead
                    else cand.parent.name)
            if incomplete:
                out.append(
                    f"{item} [{side}]: a NEWER sweep exists and cannot be "
                    f"recorded -- {', '.join(incomplete[:3])}. The provider "
                    f"returned nothing parseable for those cells, so the run "
                    f"judged nothing there. Fill them with a cell-level sweep "
                    f"and re-fold BEFORE recording; until then the older, "
                    f"complete artifact is the better measurement and is "
                    f"correctly the one recorded")
            if newer:
                out.append(
                    f"{item} [{side}]: {len(newer)} sweep artifact(s) on disk are "
                    f"NEWER than the one recorded"
                    + (f" ({rec.get('out')})" if rec.get("out") else " (none recorded)")
                    + f" -- {', '.join(newer[:3])}"
                    + (" ..." if len(newer) > 3 else "")
                    + ". Record it: until then every check reads the superseded "
                      "measurement, and the findings it produces describe a tree "
                      "that has already moved on")
    return out


def check_web_code_neutrality_is_verified() -> list[str]:
    """RETIRED 2026-09-24 with the python web engine. ALWAYS RETURNS [].

    It watched: every WEB_CODE_NEUTRAL entry still reproduced the scores it excused.

    THAT QUESTION NO LONGER HAS TWO SIDES. The python mirror of
    `scoreSlotSheet` was eliminated in goal O, so this would compare a
    thing against itself or against nothing. O's own text named the
    class: "a check that exists to catch drift between two
    implementations is dead weight once there is one implementation".

    KEPT AS A RECORD rather than deleted, so what STOPPED being watched
    stays legible -- the same treatment as
    `check_no_slot_is_both_asked_and_computed`.
    """
    return []


def _archive_reading(M, era: dict, kind: str) -> str:
    """WHAT moved, read off the text archive, or why it cannot be read.

    A stale stamp used to be two hex strings. `measured.archive_stamp` keeps the
    source text behind every fingerprint it records, so once both ends of a move
    are archived this names the function that changed and shows the diff. Until
    then it says the pair is unreadable, which is the truth and not a pass.
    """
    was = ((era.get("web_parts") or {}).get(kind) or {})
    if not was:
        return ("\n      (the recorded artifact predates per-function stamping, "
                "so what moved cannot be localised)")
    try:
        now = M.web_code_parts(kind)
    except Exception:                                       # pragma: no cover
        return ""
    moved = [n for n in sorted(set(was) & set(now)) if was[n] != now[n]]
    gone = sorted(set(was) - set(now))
    added = sorted(set(now) - set(was))
    bits = [M.web_part_diff(n, was[n], now[n]) for n in moved]
    if gone or added:
        bits.append(f"list changed: -{', '.join(gone) or 'none'} "
                    f"+{', '.join(added) or 'none'}")
    if not bits:
        return "\n      (no per-function stamp moved; the aggregate alone did)"
    return "\n      " + "\n      ".join(bits)


def check_web_code_is_stamped_by_its_own_sha() -> list[str]:
    """Does every recorded WEB column say which app code produced it?

    THE THIRD BORROWED-STAMP HOLE, and the same shape as the first two. The
    `.olx` says what the grader is shown; it does not say how lo-blocks turns
    that into a SCHEMA or a SCORE. `buildSlotSchema` decides what is asked and
    `scoreSlotSheet` and its call sites decide what it is worth, and no stamp
    covered either -- so an edit to the app could change every web prompt, or
    every web score, and leave 26 columns reading `ok`.

    ASK AND SCORE ARE REPORTED SEPARATELY because the remedies differ. A changed
    ASK invalidates the recorded ANSWERS: nothing but a re-sweep can fix it. A
    changed SCORE invalidates only the arithmetic over answers that still stand,
    which re-scoring can settle and SCORER_NEUTRAL can absorb.

    Columns recorded before the stamp existed are reported ONCE, in aggregate.
    They are a backfill debt, not 26 separate defects, and burying a live
    mismatch under two dozen standing lines is how a list stops being read.
    """
    import measured as M

    try:
        want_ask, want_score = M.web_code_sha("ask"), M.web_code_sha("score")
    except SystemExit as e:
        return [f"the web-code fingerprint cannot be computed: {e}"]

    out, unstamped = [], []
    for item in sorted(M._jobs()):
        doc = M._runs_doc(item, "olx")
        if not doc:
            continue
        era = doc.get("era") or {}
        # PER ITEM first: the stamps moved into `era.items[<id>]` when they were
        # scoped by primitive. The top-level pair is the corpus-wide view and is
        # read only as a fallback, for artifacts written in between.
        per = (era.get("items") or {}).get(item, {}) or {}
        got_ask = per.get("web_ask_sha", era.get("web_ask_sha"))
        got_score = per.get("web_score_sha", era.get("web_score_sha"))
        if not got_ask and not got_score:
            unstamped.append(item)
            continue
        want_ask = M.web_code_sha("ask", item)
        want_score = M.web_code_sha("score", item)
        if got_ask and got_ask != want_ask:
            out.append(
                f"{item}: recorded against app schema code {got_ask}, now "
                f"{want_ask}. `buildSlotSchema` has changed, so the ANSWERS in "
                f"this column were given to a different question -- re-sweep; "
                f"re-scoring cannot reach it")
        if got_score and got_score != want_score and \
                (got_score, want_score) not in M.WEB_CODE_NEUTRAL:
            out.append(
                f"{item}: recorded against app scoring code {got_score}, now "
                f"{want_score}. The answers still stand; the numbers computed "
                f"from them may not -- re-sweep."
                + _archive_reading(M, era, "score"))
    if unstamped:
        out.append(
            f"{len(unstamped)} web column(s) predate the app-code stamp and "
            f"cannot be dated against lo-blocks at all ({', '.join(unstamped)}). "
            f"Each is re-stamped by its next sweep; until then a change to "
            f"`buildSlotSchema` or `scoreSlotSheet` is invisible to them")
    return out


def check_paper_prompt_is_stamped() -> list[str]:
    """The paper column's prompt sha must be the PAPER prompt's.

    WHAT WENT WRONG. `measured.prompt_sha` hashes the .olx section a web grader
    is served and had no paper branch, so it returned the WEB's hash for
    `side="paper"` -- Q3's paper and olx shas were the same twelve characters.
    Nothing the paper scorer alone decides was stamped by anything: not
    `_answer_inventory`, not `LABELLED_PARTS_ITEMS`, not `_slot_body`'s
    desc+rule merge, not the verdict enums in `build_schema`. On 2026-09-10 all
    of those changed, none moved a sha, and the labelled-parts clause shipped
    GLOBALLY for a day without staling a single paper column. `scorer_sha` does
    not cover it either: its closure holds no part from score.py, and it is
    prose-insensitive by design -- right for behaviour, wrong for a prompt.

    THREE THINGS ARE CHECKED, and the second is the one that would have caught
    it: the fingerprint must BUILD for every item, no item's paper sha may equal
    its olx sha, and no recorded paper column may be stamped with the hash the
    olx side currently reports. That last one only catches a FRESH borrowed
    stamp -- once the .olx moves, a historical borrowed stamp is
    indistinguishable from an honestly stale one, which is why the invariant is
    enforced at the source instead of being left to the ledger to notice.
    """
    import measured as M
    import score as SC

    out = []
    for it in all_items():
        item = it["id"]
        try:
            SC.fingerprint_text(item)
        except Exception as e:
            out.append(f"{item}: score.fingerprint_text does not build "
                       f"({type(e).__name__}: {e}) -- the paper prompt cannot "
                       f"be stamped, so a paper sweep would record unstamped")
            continue
        try:
            paper, olx = M.prompt_sha(item, "paper"), M.prompt_sha(item, "olx")
        except Exception as e:
            out.append(f"{item}: prompt_sha failed ({type(e).__name__}: {e})")
            continue
        if paper == olx:
            out.append(f"{item}: the paper and olx prompt shas are both "
                       f"{paper} -- the paper side is borrowing the web's "
                       f"stamp, so a paper-only prompt change stales nothing")
        for side in ("paper", "paper_opus"):
            rec = (M.load().get("items", {}).get(item, {}) or {}).get(side)
            if rec and rec.get("prompt_sha") == olx:
                out.append(f"{item} [{side}]: recorded at prompt_sha {olx}, "
                           f"which is the OLX side's current hash -- that "
                           f"column is stamped with the web's prompt and "
                           f"cannot say what produced it; re-record it")
    return out


def check_paper_reproduces_web_scores() -> list[str]:
    """The web's own judgments, run through PAPER's arithmetic. Do they score alike?

    THE WIDE HALF OF THE SCORER COMPARISON.
    `check_paper_scorer_agrees_on_identical_verdicts` asks this the other way
    round and is limited to items with a recorded PAPER artifact -- two of them.
    Every item has an olx sweep, so this direction covers 26 items and ~3,100
    cells. The model is held fixed either way, so a difference is the two
    implementations of the scoring rules disagreeing, not sampling.

    See measured.web_judgments_through_paper for the translation and for the
    three reader bugs that had to be fixed before its numbers meant anything --
    each one dropped a slot, and a dropped slot is charged rather than skipped.
    """
    import measured as MEAS

    d = MEAS.web_judgments_through_paper()
    out = []
    for item, pid, web, paper in d["differing"]:
        out.append(
            f"{item}/p{pid}: the web's own judgments score {web:g} on the web and "
            f"{paper:g} through the paper scorer's arithmetic. The judgments are "
            f"held fixed, so this is the two scoring implementations disagreeing")
    for e in d["errors"]:
        out.append(f"the web's judgments could not be scored by the paper path -- {e}")
    return out


def paper_reproduces_web_line() -> str:
    """Coverage for the check above, as audit context rather than a finding."""
    import measured as MEAS

    d = MEAS.web_judgments_through_paper()
    n = d["agree"] + len(d["differing"])
    if not n:
        return "paper-vs-web arithmetic: no olx artifact could be replayed."
    return (f"paper-vs-web arithmetic: {d['agree']} of {n} cell(s) across "
            f"{len(d['items'])} item(s) score IDENTICALLY when the web's own "
            f"judgments are run through the paper scorer "
            f"({100 * d['agree'] / n:.2f}%). Holding the judgments fixed removes "
            f"the model, so what is left is the arithmetic.")


def check_engine_rate_divergence() -> list[str]:
    """RETIRED 2026-09-24 with the python web engine. ALWAYS RETURNS [].

    It asked whether the two engines' per-cell agreement RATES differed beyond
    chance. There is one web engine (goal O), so there is one rate.

    Deliberately not repointed at `paper`: that side scores a DIFFERENT INPUT,
    so a rate difference against it is not evidence about either engine's
    arithmetic -- which is what this measured.
    """
    return []


def engine_rate_power_line() -> str:
    """One line of CONTEXT for the audit, not a finding.

    The power fact has to be visible on every run -- a rate check that is silent
    because it cannot fire reads as evidence the engines agree -- but it is not
    a defect anyone can fix by editing code, so reporting it as a finding would
    leave the audit permanently red, and a check that is always red is one
    nobody reads. It goes where the coverage lines go.
    """
    import measured as MEAS

    d = MEAS.rate_divergence()
    if d["min_p_possible"] is None:
        # RETIRED, NOT EMPTY. True as written, but it reads as a coverage
        # gap a sweep could close, and no sweep can: there is one engine.
        return ("engine rates: NOT COMPARED -- the python web engine was "
                "eliminated (goal O), so no cell can have two sides.")
    blind = d["min_p_possible"] > d["bonferroni"]
    return (f"engine rates: {d['cells']} cell(s) compared by exact test; "
            f"{len(d['flagged'])} at uncorrected p<0.05 where chance predicts "
            f"~{0.05 * d['cells']:.0f}. "
            + (f"NO POWER at this run count -- smallest possible p "
               f"{d['min_p_possible']:.5f} against a corrected threshold of "
               f"{d['bonferroni']:.5f}, so no divergence claim is supportable "
               f"until the sides are swept deeper (nine runs each would let a "
               f"PERFECT split register, and nothing less than perfect)."
               if blind else
               f"Corrected threshold p<{d['bonferroni']:.5f}."))


def check_app_and_harness_send_the_same_request() -> list[str]:
    """Do the app and the harness post the same FIELDS to the provider?

    The prompt check settles the text; this settles everything around it. A
    difference in `response_format`, in tools, or in a sampling field would leave
    both sides grading identical text under different conditions, and the only
    symptom would be verdicts that disagree for no visible reason -- which is
    exactly what Q1/p17 looked like before this pair of checks existed.

    READ FROM SOURCE, both sides:
      * `backends.LoBlocksBackend.complete` builds the harness payload.
      * `reduxClient.tsx` builds the app's, and `routes/llm.ts` then DELETES the
        fields that are the server's own -- `profile` and `activity` -- before
        dispatch, and fills `max_completion_tokens` from the resolved profile.
        Both sides omit `profile`, so both resolve `interactive` and receive the
        same token ceiling.

    So the provider-visible field sets must match once the deleted ones are
    removed. This does not compare VALUES -- the schema is compared by
    `equivalence.py --prompts` against buildSlotSchema, and the messages by
    check_app_and_harness_send_the_same_prompt -- it asks whether one side has
    started sending a field the other does not.

    "THE TWO ENGINES" IS NOW THE APP AND THE HARNESS ASK PATH (2026-09-25).
    Goal O eliminated the python mirror of `scoreSlotSheet`, so `engine` no
    longer denotes one of two scorers. Both sides of this check are still
    live code and it still compares them; only the word was wrong, and a
    reader who takes it at face value concludes the check is dead.
    """
    import re as _re

    import paths as P

    try:
        be = (P.SCORING / "backends.py").read_text()
        rc = (P.LO / "packages/shared/lib/llm/reduxClient.tsx").read_text()
        rt = (P.LO / "apps/server/src/routes/llm.ts").read_text()
    except Exception as e:
        return [f"cannot read both request builders: {type(e).__name__}: {e}"]

    m = _re.search(r"class LoBlocksBackend.*?payload = json\.dumps\(\{(.*?)\}\)\.encode",
                   be, _re.S)
    if not m:
        return ["backends.LoBlocksBackend no longer builds its payload with "
                "`payload = json.dumps({...}).encode`, so the harness's request "
                "fields cannot be read and this check is blind"]
    # TOP-LEVEL keys only. Matching every `"key":` in the block pulled in
    # `role`, `content`, `schema` and the rest of the nested json_schema, and
    # reported them all as fields the app fails to send.
    def _top_keys(src: str, quote: str) -> set:
        depth, keys = 0, set()
        for mm in _re.finditer(r'[{}\[\]]|' + quote + r'(\w+)' + quote + r'\s*:', src):
            tok = mm.group(0)
            if tok in "{[":
                depth += 1
            elif tok in "}]":
                depth -= 1
            elif depth == 0 and mm.group(1):
                keys.add(mm.group(1))
        return keys

    ours = _top_keys(m.group(1), '"')

    m2 = _re.search(r"fetch\(LLM_ENDPOINT.*?body: JSON\.stringify\(\{(.*?)\}\),",
                    rc, _re.S)
    if not m2:
        return ["reduxClient no longer posts with `body: JSON.stringify({...})`, "
                "so the app's request fields cannot be read and this check is blind"]
    body = m2.group(1)
    theirs = _top_keys(body, "")
    theirs |= set(_re.findall(r"&&\s*\{\s*(\w+)", body))
    theirs = {k for k in theirs if k not in ("type",)}   # `type` is inside tools.map

    deleted = set(_re.findall(r"delete body\.(\w+)", rt))
    visible = {f for f in theirs if f not in deleted}
    out = []
    only_app = visible - ours
    only_harness = ours - visible
    if only_app:
        out.append(f"the app posts {sorted(only_app)} to the provider and the "
                   f"harness does not, so the two engines grade under different "
                   f"request conditions")
    if only_harness:
        out.append(f"the harness posts {sorted(only_harness)} and the app does "
                   f"not")
    if not deleted:
        out.append("routes/llm.ts deletes no fields before dispatch, which it used "
                   "to do for `profile` and `activity`; if that stopped, the "
                   "provider now sees fields the harness never sends")

    # THE MESSAGES ARRAY IS COMPARED BY NAME ABOVE, NOT BY CONTENTS, and that is
    # only safe while it cannot grow. reduxClient extends it inside
    # `if (toolCalls?.length)` and nowhere else, and the grader is given no
    # tools, so the app sends the same two messages the harness does. Both
    # halves of that are asserted, because if either changed the field sets
    # would still match while the app sent a longer conversation.
    grew = _re.search(r"if \(toolCalls\?\.length\)\s*\{(.*?)\n      \}", rc, _re.S)
    extends = _re.findall(r"newMessages = \[", rc)
    if len(extends) > 1 and not grew:
        out.append("reduxClient extends `newMessages` outside the tool-call "
                   "branch, so the app may now send a longer conversation than "
                   "the harness's two messages while the field sets still match")
    # SEARCHED IN THE PAYLOAD BLOCK, not the whole file. backends.py line ~208
    # documents the behaviour in a comment that reads `"tools": []`, so a
    # file-wide search matched the DOCUMENTATION and stayed quiet when the real
    # payload was changed -- the check was green by construction until an
    # injection test broke the payload and nothing happened.
    if not _re.search(r'"tools":\s*\[\s*\]', m.group(1)):
        out.append("backends.LoBlocksBackend no longer sends `tools: []`, so the "
                   "app's tool-call branch could extend the message array and the "
                   "two engines would send different conversations")

    # THE FIXTURE IS SHARED, AND MUST STAY SHARED. agreement.fixture_for exists
    # because a SECOND reconstruction was the original defect -- it mapped every
    # field of an item onto the same section and wrote "(continued above)" into
    # the rest, showing the model empty boxes. It now delegates to
    # agreement_app.build_jobs, which is what makes the assembled-prompt
    # comparison meaningful: both engines fill the template from one source.
    try:
        ag = (P.SCORING / "agreement.py").read_text()
    except Exception:
        ag = ""
    fc = _re.search(r"def _fixture_cached\(.*?\n(?=def |\Z)", ag, _re.S)
    if fc and "import agreement_app" not in fc.group(0):
        out.append("agreement._fixture_cached no longer imports agreement_app, so "
                   "the harness may be reconstructing the student's fields "
                   "separately from the app -- the two engines would assemble "
                   "identical templates around DIFFERENT text, which the prompt "
                   "check cannot see because it fills both sides from one fixture")
    return out


def check_app_and_harness_send_the_same_prompt() -> list[str]:
    """Do agreement_app.py and agreement.py send the SAME prompt body?

    THE DIRECT QUESTION, and the audit did not ask it. Everything else compares
    declarations, or scores, or verdicts -- all of them downstream of the text
    that actually reaches the model. Q1/p17 was diagnosed on 2026-09-01 by
    reading per-cell verdicts backwards, three inferential steps from the thing
    that might have differed, when a body comparison settles it directly and
    costs nothing.

    THE BODY IS SPLIT AROUND EACH `<Ref>`, and that is the trap. The app serves
    it as a `kids` array -- 3 segments on Q1, 9 on Q4b, SIXTEEN on Q6 -- and the
    freshness guard inside agreement_app read `kids[0]` only, so it inspected a
    fraction of the prompt and ignored the rest, including the box wrapper and
    the closing instructions that sit nearest the student's own answer. Every
    string kid is joined here, and the same fix was made there.

    NEEDS A DUMP, and says so rather than passing quietly when there is none: a
    check that reports clean because it could not look is the failure mode this
    audit has hit twice in one day (the unreadable `paper` column, and the
    ownership check reading no data as no problem).

    "THE TWO ENGINES" IS NOW THE APP AND THE HARNESS ASK PATH (2026-09-25).
    Goal O eliminated the python mirror of `scoreSlotSheet`, so `engine` no
    longer denotes one of two scorers. Both sides of this check are still
    live code and it still compares them; only the word was wrong, and a
    reader who takes it at face value concludes the check is dead.
    """
    import difflib
    import glob
    import json
    import re as _re

    import agreement as AG
    import olx_prompts as OP
    import paths as P

    dumps = sorted(glob.glob(str(P.OUT / "idmap*.json")))
    if not dumps:
        return ["no idmap dump under out/, so the app's served prompt cannot be "
                "compared with the harness's. Produce one with `curl -s "
                "'http://localhost:8888/api/olxjson?id=all' -o out/idmap.json` "
                "while the dev server runs"]
    newest = max(dumps, key=lambda f: pathlib.Path(f).stat().st_mtime)
    # A DUMP OLDER THAN THE OLX PROVES NOTHING, and saying so once beats
    # reporting a divergence per item that is really one stale file. The check
    # would otherwise be red on every ordinary day -- prompts are regenerated far
    # more often than dumps are taken -- and a check that is always red is a
    # check nobody reads.
    # THE DUMP'S AGE ONLY MATTERS IF SOMETHING DIFFERS. Returning early on mtime
    # made the check fire whenever the .olx was merely REWRITTEN -- an injection
    # test restoring a file byte-for-byte was enough, since content-identical
    # rewrites move the mtime. Age is now used to EXPLAIN a difference rather
    # than to pre-empt the comparison: if every body matches, a dump older than
    # the .olx has told us what we needed anyway.
    dump_at = pathlib.Path(newest).stat().st_mtime
    olx_at = max(pathlib.Path(P.OLX % h).stat().st_mtime for h in _forms())
    stale_dump = dump_at < olx_at
    try:
        st = pathlib.Path(newest).stat()
        idmap = _idmap_parsed(newest, st.st_mtime, st.st_size)
    except Exception as e:
        return [f"{newest} cannot be read as an idmap: {type(e).__name__}: {e}"]
    strip = lambda s: [l.strip() for l in _re.sub(r"<[^>]+>", "", s or "").splitlines()
                       if l.strip()]
    # `<Ref id=... target=...>` straight from the authored OLX, which is what
    # tells us which field a ref block in the dump resolves to.
    refmap = {}
    for h in _forms():
        try:
            refmap.update(dict(_re.findall(
                r'<Ref\s+id="([^"]+)"\s+target="([^"]+)"',
                pathlib.Path(P.OLX % h).read_text())))
        except Exception:
            pass
    # Three participants per item, not twenty: assembly is a property of the
    # template and the ref set, so it does not vary cell by cell, and the audit
    # runs on every commit.
    pids = (1, 9, 17)
    out = []
    for item, action in sorted(OP.ACTION.items()):
        served = None
        for key, entry in idmap.items():
            if not key.endswith("/" + action):
                continue
            for _loc, val in (entry or {}).items():
                joined = "".join(k for k in ((val or {}).get("kids") or [])
                                 if isinstance(k, str))
                if joined:
                    served = joined
            break
        if served is None:
            continue                     # item not in this dump; --prompts covers that
        try:
            h = OP.FORM[item]
            mine = AG.load_action(_p7.handout_olx(h), action)["body"]
        except Exception as e:
            out.append(f"{item}: cannot read the harness body: {type(e).__name__}: {e}")
            continue
        a, b = strip(served), strip(mine)
        diff = [l for l in difflib.unified_diff(a, b, lineterm="", n=0)
                if l[:1] in "+-" and l[:3] not in ("---", "+++")]
        if diff:
            why = ("the dump predates the current .olx, so re-take it with `curl "
                   "-s 'http://localhost:8888/api/olxjson?id=all' -o "
                   "out/idmap.json' and re-run before reading this as a divergence"
                   if stale_dump else
                   "the dump is NOT older than the .olx, so this is a real "
                   "difference in what the two engines grade")
            out.append(f"{item}: the app serves a prompt body the harness does not "
                       f"send -- {len(diff)} differing line(s), first: "
                       f"{diff[0][:90]!r}. {why}")
            continue
        # THE ASSEMBLED PROMPT, not just the template. Matching bodies do not
        # settle it: the body is a template with `<Ref>` holes, and the two sides
        # fill them separately -- the harness from its reconstructed fixture, the
        # app by resolving each ref block. A difference in ORDER, in separators,
        # or in which ref resolves to what would leave the templates identical
        # and the model reading different text.
        #
        # WHAT THIS DOES NOT TEST, stated because the check would otherwise be
        # read as proving more than it does: both sides are filled from the SAME
        # fixture here, so this compares ASSEMBLY, not whether the app's page
        # state holds the same student text the corpus does.
        for pid in pids:
            try:
                fx = AG.fixture_for(item, pid)
            except Exception:
                continue                 # item does not cover this participant
            try:
                theirs = _assemble_like_the_app(idmap, action, fx, refmap)
                ours = AG.build_prompt(mine, fx)
            except Exception as e:
                out.append(f"{item}/p{pid}: cannot assemble both prompts: "
                           f"{type(e).__name__}: {e}")
                break
            if theirs is None:
                break
            x, y = strip(theirs), strip(ours)
            d2 = [l for l in difflib.unified_diff(x, y, lineterm="", n=0)
                  if l[:1] in "+-" and l[:3] not in ("---", "+++")]
            if d2:
                out.append(f"{item}/p{pid}: the two engines ASSEMBLE the same "
                           f"template differently -- {len(d2)} differing line(s), "
                           f"first: {d2[0][:80]!r}")
                break
    return out


def _assemble_like_the_app(idmap: dict, action: str, fixture: dict,
                           refmap: dict) -> str | None:
    """The prompt the app builds: string kids joined, ref blocks resolved.

    Mirrors what the runtime does with the `kids` array -- text segments in
    order, each `{type: block, id: ...}` replaced by the value of the field its
    `<Ref>` targets. AN EMPTY FIELD RESOLVES TO NOTHING, which is what the app
    does; captured from the running blocks to be sure of it.

    IT USED TO PAD WITH `(left blank)`, and the reason given was "matching
    agreement.build_prompt so an empty box does not read as a difference" -- i.e.
    this model of the APP was calibrated to agree with the HARNESS. That is why
    it never found the divergence it exists to find: the harness padded, the app
    did not, and the check had been taught the harness's answer. A model of the
    thing under test, tuned to the thing it is tested against, can only ever
    report clean. Fixed 2026-09-12 when a capture of the real app showed the two
    assembled prompts differ on 60 cells across 18 items.
    """
    for key, entry in idmap.items():
        if not key.endswith("/" + action):
            continue
        for _loc, val in (entry or {}).items():
            parts = []
            for k in (val or {}).get("kids") or []:
                if isinstance(k, str):
                    parts.append(k)
                else:
                    rid = str((k or {}).get("id", "")).split("/")[-1]
                    tgt = refmap.get(rid)
                    parts.append((fixture.get(tgt) or "").strip())
            return "".join(parts)
    return None


def check_scorer_neutrality_is_verified() -> list[str]:
    """Every SCORER_NEUTRAL entry must still reproduce the scores it excuses.

    THE ENTRY IS A CLAIM, NOT A PERMISSION. `measured.SCORER_NEUTRAL` suppresses
    STALE SCORER for a fingerprint pair on the grounds that the code change
    between them cannot move a recorded number. That is checkable without
    spending anything: the verdicts are on disk, so re-score every cell the entry
    covers through today's scorer and require the score the artifact stored.

    So the approval cannot rot in either direction. If the claim was wrong, this
    says which cell moved. If the scorer later changes in a way that DOES move a
    score, the fingerprints move with it, the pair stops matching, and the
    staleness returns on its own -- the same reason `prompt_sha` is keyed the way
    it is.

    An entry naming a pair no item is recorded at is reported too: it excuses
    nothing, and an exemption that protects nothing reads as coverage.
    """
    import measured as M

    bad: list[str] = []
    covered = 0
    unreachable: list[str] = []
    for (rec, now), why in sorted(M.SCORER_NEUTRAL.items()):
        items = []
        for side in M.POOLED_OLX_PROMPT:
            try:
                rows = M.records(side)
            except Exception:
                continue
            for item, s in rows.items():
                if s.get("scorer_sha") == rec:
                    items.append((item, side))
        if not items:
            bad.append(
                f"SCORER_NEUTRAL declares {rec} -> {now} ({why[:48]}...), but no "
                f"recorded item sits at {rec}. The pair is spent -- drop it, or it "
                f"reads as coverage of something")
            continue
        # DOES THE DECLARED TARGET STILL EXIST? A pair names a transition
        # `rec -> now`. Items recorded at `rec` are found above, so the pair does
        # not read as spent -- but if NONE of them now sits at `now`, every one is
        # skipped below and the pair verifies NOTHING while the audit reports
        # clean. Measured 2026-09-14: both live pairs declare
        # `6526989cd34f -> ...` over three columns whose scorer has since moved to
        # a third sha entirely, so `cells covered` was 0 and no finding said so.
        #
        # That is C1's failure mode wearing a different hat. The usual one is a
        # check whose SOURCE vanished; this is a check whose TARGET vanished, and
        # it is quieter, because the declaration still looks live in the table.
        if items and not any(M.scorer_sha(i, sd) == now for i, sd in items):
            at = sorted({M.scorer_sha(i, sd) for i, sd in items})
            bad.append(
                f"SCORER_NEUTRAL declares {rec} -> {now} ({why[:48]}...), and "
                f"{len(items)} recorded item(s) DO sit at {rec} -- but none of "
                f"them is at {now} any more; they are at {', '.join(at)}. The "
                f"pair is not spent, it is UNTESTABLE: every item is skipped and "
                f"the claim is verified against nothing. Re-point it at the sha "
                f"the tree actually reached, or retire it")
            continue
        for item, side in items:
            if M.scorer_sha(item, side) != now:
                continue                      # a different pair's business
            n, moved, why = M.rescore_recorded(item, side)
            covered += n
            if why:
                # NOT COMPARABLE IS NOT DISAGREEMENT. 1b, T1 and T2 have no slot
                # sheet -- they are scored deterministically from the fixture, so
                # there are no model verdicts to re-score. Their neutrality is
                # established by RE-RUNNING them, which costs nothing, and the
                # entry says so.
                unreachable.append(f"{item} [{side}]: {why}")
                continue
            for line in moved:
                bad.append(
                    f"SCORER_NEUTRAL claims {rec} -> {now} moves no score, but "
                    f"{line}. The claim is false: either the change is not "
                    f"neutral, or the recorded number predates something else")
    check_scorer_neutrality_is_verified.cells = covered
    check_scorer_neutrality_is_verified.unreachable = unreachable
    return bad


# Generated attributes that are HAND-AUTHORED on purpose, with the reason. An
# attribute in the .olx whose `*_attr_for` returns None is otherwise an ORPHAN --
# see check_generated_attributes_have_a_declaration. Keep this table small: every
# entry is a place where the rubric is NOT the single source, which is the thing
# the generator conversions exist to remove.
# HAND_AUTHORED_ATTRS IS BOUND FURTHER DOWN, after `_declaration` is defined. Its
# entries live in the course file, authored in `declaration_source.py`.


def check_generated_attributes_have_a_declaration() -> list[str]:
    """An .olx attribute the generator OWNS, with no rubric rule behind it.

    SUBGOAL E44. `olx_prompts.GENERATED_ATTRS` names three attributes the
    generator writes -- `forbid`, `expect`, `maps` -- each from a `*_attr_for`
    that returns None when the rubric declares no rule. The writer then does
    `if want is None: continue`, which LEAVES the attribute alone rather than
    clearing it. That is right while an attribute is hand-authored and the rubric
    has never claimed it. It is wrong the moment a declaration is REMOVED: the
    attribute was generated, nothing backs it now, and nothing removes it.

    WHAT IT COST. Reverting the cadence edit on 2026-09-05 deleted `EXPECT` for
    DAY1/DAY2/WK2 and removed the picks those rules parsed. The .olx kept
    `expect="targets_own_behavior:trigger_behavior=...|cadence_is_daily:
    trigger_settles=..."`, so both the aim slot and the cadence gate were computed
    from operands that no longer existed -- never satisfiable -- and the items
    could not reach 4.00 at all. `olx_prompts.py --check` reported "up to date"
    throughout, because the generator does not own an attribute it did not write.
    Eight queued sweeps then woke into that tree and exited without spending a
    call, which was luck: the cheap-checks gate caught it only because the orphan
    happened to make a GATE unsatisfiable.

    THAT LUCK IS THE REASON THIS EXISTS. An orphaned `expect` on a slot that
    merely SCORES, or an orphaned `maps` whose pick survives but whose rule has
    changed, leaves the arithmetic reachable and passes in silence. `maps` is the
    newest of the three and two items gained one on 2026-09-05, so the exposure is
    live and growing.

    Reports an attribute PRESENT with no rule and no HAND_AUTHORED_ATTRS entry.
    The reverse -- a rule with no attribute to write into -- is already a hard
    error in the writer, and drift between the two is what `--check` compares.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K. Python must stay on this side of
    # "is it backed?": the answer comes from calling the GENERATOR for the item,
    # which is python. What moves is the judgement -- an owned attribute with no
    # rule behind it, and not exempt, is an orphan.
    import re

    import lo_enforce
    import olx_prompts as OP

    attrs = []
    for item_id, action in sorted(OP.ACTION.items()):
        try:
            tag = OP._sheet_tag(OP.FORM[item_id], action)
        except SystemExit:
            continue                      # a missing sheet is another check's
        for name, fn in OP.GENERATED_ATTRS:
            m = re.search(r'%s="([^"]*)"' % name, tag)
            if m is None:
                continue
            attrs.append({"item": item_id, "name": name, "value": m.group(1),
                          "backed": fn(item_id) is not None,
                          "exempt": (item_id, name) in HAND_AUTHORED_ATTRS})
    if not attrs:
        # NOT SILENCE. No sheet carried a generated attribute at all, which
        # means nothing was examined rather than nothing being wrong.
        return ["no generated attribute was found on any sheet, so none was "
                "checked for having a rubric rule behind it"]
    return lo_enforce.run("generated_attributes_have_a_declaration",
                          {"attrs": attrs})



def _maps_specs() -> list[tuple]:
    """(item, spec) for every `maps` entry in every rubric. Subgoal E46."""
    out = []
    # THE VIEWS, NOT THE MODULES. `__import__(name)` with a constant is a third
    # spelling of the same dependence, and one the consumer ratchet cannot see:
    # it counts a FILE, and this file already counted once for the source-reading
    # check that cannot be converted. Three of these loops were hiding behind
    # that single tally.
    for mod in _rubric_views():
        for item, specs in (getattr(mod, "MAPS", None) or {}).items():
            for s in specs:
                out.append((item, mod, s))
    return out


def _maps_emits(spec: dict) -> set:
    """Every verdict a map can produce: its pairs, plus its fallback."""
    e = {p["verdict"] for p in spec.get("pairs") or []}
    if spec.get("fallback"):
        e.add(spec["fallback"])
    return e




# WHAT IS DESIGNED MUST BE WHAT SHIPS. Exact prompt text a subgoal committed to,
# keyed (item, slot, field), compared against the live rubric before any call.
#
# THIS TABLE EXISTS BECAUSE OF ONE WASTED SWEEP AND A WRONG EXPLANATION. On
# 2026-09-06 subgoal Q19 designed a report slot and recorded its `desc` as PROSE
# IN A GOAL ENTRY. At build time the string was RE-TYPED into the rubric, and the
# re-typing dropped the question's comparison clause and turned a yes/no into a
# which-one:
#     DESIGNED  "does this box name, as the thing the student is doing, THE SAME
#                ACT THAT AN ANTECEDENT BOX NAMES AS ITS TRIGGER?"
#     SHIPPED   "WHICH ANTECEDENT, IF ANY, does this box name as the thing the
#                student is doing?"
# The probe passed 23 of 24 on the designed wording. The sweep over-fired on nine
# cells and cost ~230 calls. The first explanation offered was a "prompt-load
# effect" -- a hand-wave that would have ended the investigation -- and a
# re-probe with the SHIPPED string reproduced the failure standalone in 24 calls.
#
# NOTHING COULD HAVE CAUGHT IT. Every other gate here asks whether the shipped
# text is WELL-FORMED -- that the slot reaches the sheet, that its verdicts are
# reachable, that no map dangles, that no cohort words leak. None asks whether it
# is THE TEXT SOMEBODY DECIDED ON, because the decision lived in prose and prose
# is not comparable. A design recorded where no check can read it is a design
# that ships by memory.
#
# HOW TO USE IT: when a subgoal commits to exact prompt wording, put the string
# HERE, verbatim, and have the entry point at this table instead of restating the
# words. Then the build cannot drift, and if the design is deliberately revised
# the revision happens in one place and is visible in the diff.
DESIGNED_TEXT = _declaration("DESIGNED_TEXT")


DESIGNED_SHA_FILE = "DESIGNED_TEXT_SHA.json"


def _designed_shas() -> dict:
    import json
    try:
        import paths as _pth_d
        raw = json.loads(_pth_d.COURSE_DESIGNED_TEXT_SHA.read_text())
    except Exception:
        return {}
    return raw.get("fields") or {}


def check_every_prompt_field_is_designed() -> list[str]:
    """MANDATORY: every rubric desc/rule the graders read must match its
    design-of-record sha. Reported as PROMPT FIELD IS NOT THE DESIGNED TEXT.

    THE OPT-IN VERSION WAS NOT ENOUGH, and the user said so: DESIGNED_TEXT only
    guards wording somebody chose to enter, so it cannot police a field nobody
    thought to write down -- which is exactly the case that cost a sweep. This
    covers ALL 145 desc/rule fields across the three rubrics.

    SHA RATHER THAN FULL TEXT, and the reason is reviewability. 47KB of duplicated
    prose in a table is not read; 145 short lines are, and a change shows up as
    one line in a diff. The cost is that a sha detects drift without recovering
    the original, which is why DESIGNED_TEXT still exists for wording a subgoal
    explicitly commits to -- that tier keeps the words.

    THREE FAILURE KINDS, reported separately because they mean different things:
      CHANGED  -- the field exists and its text no longer matches. Either an
                  intended edit that has not been accepted, or a drift.
      MISSING  -- a new field with no design of record. A slot added without a
                  decision recorded is the Q19 case in embryo.
      STALE    -- a sha for a field that no longer exists, usually after a
                  revert. Harmless, reported so the file does not silently rot.

    There is deliberately NO bulk regenerate. `measured.py
    --accept-design-change ITEM SLOT FIELD` rewrites ONE sha and prints what
    changed. Bulk regeneration would make the file agree with anything.
    """
    # PORTED to `enforce/promptFieldsAreDesigned.ts` (goal K).
    #
    # PYTHON KEEPS BOTH FETCHES. `_designed_shas` is the seam the self-test and
    # `--accept-design-change` both work through, and `_field_sha` resolves a
    # corpus reference before hashing -- hand the runner nothing and it rebuilds
    # both from disk, seeing neither an in-memory patch nor python's own
    # resolver. The assembler stays for a native caller, which has its own.
    import forms as H
    import lo_enforce

    want = _designed_shas()
    live: dict[str, str] = {}
    for h in _forms():
        try:
            items = H.config(h)["rubric"].ITEMS
        except Exception:
            continue
        for it in items:
            for c in it.get("credit") or []:
                for f in ("desc", "rule"):
                    v = c.get(f)
                    if v:
                        live[f"{it['id']}|{c['what']}|{f}"] = _field_sha(v)
    return lo_enforce.run("every_prompt_field_is_designed", {
        "want": want, "live": live, "shaFile": DESIGNED_SHA_FILE,
    })

def _field_sha(text) -> str:
    """Fingerprint a prompt field by its WORDS, not by how they are encoded.

    RESOLVED FIRST, because since the history rewrite a field that quotes a
    student holds `{{corpus:...}}` where the registered design held the sentence.
    Hashing the raw text made every such field report CHANGED without acceptance
    on 2026-09-21 -- seven of them, spread across all three handouts, none with a
    word altered. (Named nowhere here on purpose: naming them would embed course
    data in a migrated module, which is its own ratchet and the reason this
    sentence counts rather than lists.)

    ACCEPTING THEM WOULD HAVE BEEN WORSE than a false alarm. `--accept-design-
    change` records the SHIPPED string, so the reference itself would become the
    design: a later wording edit inside that field would move no sha at all,
    because the reference would not change. The check would go quiet exactly
    where it is most needed.

    Same correction as `migrated_tables.same_shape`, and for the same reason:
    compare what the text MEANS, not how it is spelled.
    """
    import hashlib
    t = str(text)
    if "{{corpus:" in t:
        try:
            import corpus_resolve as _CR
            t = _CR.expand(t)
        except Exception:                   # no export configured: hash it raw
            pass
    return hashlib.sha256(re.sub(r"\s+", " ", t).strip().encode()).hexdigest()[:12]


def check_no_definition_vanished() -> list[str]:
    """A definition the inventory records and the tree no longer defines.
    Reported as DEFINITION VANISHED FROM THE PACKAGE.

    THE GUARD AGAINST A SLICE-BOUNDED EDIT TAKING A SLICE OUT OF THE WRONG
    THING. Three times in two days an edit bounded by "the next brace" or "the
    next definition" ate a neighbouring declaration; the file still parsed every
    time, which is why nothing caught it. Twice it went unnoticed until a
    NameError -- once in `--preflight`, days later, and the deleted name was
    `GOLD_SLOT_BOUNDS_BUDGET`, whose absence had already been SEEN as "this
    table loads 7 keys instead of 5" and moved past unexplained.

    `editguard.safe_write` prevents it at write time. This catches it at gate
    time, whatever route the edit took, because a plain Write or a hand-run
    script bypasses the writer and not this. See `editguard.py` for the full
    account and `DEFINITIONS.json` for the inventory.
    """
    from tools import editguard
    return editguard.vanished()


def check_no_module_appends_to_the_repository() -> list[str]:
    """A module opens a repository path in APPEND mode.
    Reported as AN APPEND-ONLY LOG IS BEING WRITTEN INTO THE REPOSITORY.

    WHY THIS EXISTS, in one measurement. The gate's override log lived in
    `scoring/` and was machine-appended, so every commit rewrote the whole blob:
    80 versions, 2,838 MB of history, 82 PER CENT of every blob this repository
    had ever stored -- against 18 MB of tracked content. A blob is permanent once
    committed, so deleting the file reclaims nothing. The log now lives in
    `$COURSE_DATA`; this keeps the next one from starting.

    APPEND MODE IS THE SIGNAL, and it is a precise one. A record REWRITTEN whole
    is bounded by its key space -- items, slots, cells -- and cannot grow with
    time; `MEASURED.json` carries one `previous` per item and side, not a chain,
    and sits at 46 KB per version across 83 of them. A record APPENDED to is
    bounded by nothing. When this was written the package contained exactly ONE
    append-mode write, and it had already produced the problem above.

    It reads the source rather than running anything: an `open(..., "a")` whose
    path is built from a module-relative anchor. A log written to `$COURSE_DATA`
    is fine and is the point -- what is refused is appending INSIDE the tree.
    """
    import ast as _ast
    import pathlib as _pl

    out = []
    for path in sorted(_pl.Path(str(_HERE_DIR)).glob("*.py")):
        try:
            tree = _ast.parse(path.read_text())
        except (SyntaxError, OSError):
            continue
        for node in _ast.walk(tree):
            if not (isinstance(node, _ast.Call)
                    and isinstance(node.func, _ast.Name) and node.func.id == "open"):
                continue
            mode = None
            if len(node.args) > 1 and isinstance(node.args[1], _ast.Constant):
                mode = node.args[1].value
            for kw in node.keywords:
                if kw.arg == "mode" and isinstance(kw.value, _ast.Constant):
                    mode = kw.value.value
            if not (isinstance(mode, str) and "a" in mode):
                continue
            target = _ast.unparse(node.args[0]) if node.args else "?"
            # A path resolved through `coursedata`/`paths` leaves the repository;
            # anything anchored on this module's own directory does not. FOLLOW A
            # BARE NAME to the expression it was assigned from: the first version
            # of this check read the CALL SITE only, so `open(log, "a")` was
            # reported even though `log = _log_path()` two lines above resolves
            # under $COURSE_DATA. A variable defeated the whole test.
            resolved = target
            if isinstance(node.args[0] if node.args else None, _ast.Name):
                want = node.args[0].id
                for other in _ast.walk(tree):
                    if (isinstance(other, _ast.Assign) and len(other.targets) == 1
                            and isinstance(other.targets[0], _ast.Name)
                            and other.targets[0].id == want):
                        resolved = _ast.unparse(other.value)
            if any(t in resolved for t in
                   ("coursedata.", "paths.", "_log_path", "OUT", "DATA")):
                continue
            out.append(
                f"{path.name}:{node.lineno} opens {target} in mode {mode!r}. An "
                f"append-only file inside the repository grows its history without "
                f"bound and cannot be reclaimed -- every version is a permanent "
                f"blob. Write it under $COURSE_DATA and resolve the path there")
    return out


def check_no_composed_document_repeats_itself() -> list[str]:
    """A composed document states the same prose twice.
    Reported as A COMPOSED DOCUMENT SAYS IT TWICE.

    The failure mode of splitting a section that is mostly record but states a rule
    in passing: the rule is lifted into the generic half and the record moves, and
    if the sentence is not deleted from the record the document says it twice.
    Nothing else reports it, because the result reads as emphasis.
    """
    # PORTED (goal K). Fire-tested by appending one sentence to both halves:
    # byte-identical to python's finding, including python's `repr` of the
    # truncated quote.
    import lo_enforce

    return lo_enforce.run("no_composed_document_repeats_itself", None)


def check_every_document_is_where_its_readers_look() -> list[str]:
    """A document named by a reader is not at the path that reader resolves.
    Reported as A DOCUMENT IS NOT WHERE ITS READERS LOOK.

    MOVING A DOCUMENT BREAKS ITS READERS QUIETLY. A reader joins a name onto a
    directory, the path does not exist, and the well-behaved ones skip it -- so the
    record reads as empty rather than as broken. Measured twice in one sitting:
    `olx_prompts`' written-record scan reported NO RECORD for every item after
    GOALS.md was split, while the composed document held 249 mentions of Q6 alone;
    and `goals`' citation check would have stopped reading BACKLOG.md, which cites
    dozens of subgoals, the moment it moved.
    """
    # PORTED (goal K). The generic halves moved into lo-blocks beside the rules
    # they document, so both halves and the composed copy are readable from
    # there and this became portable. Fire-tested against python's own answer
    # with a course half hidden: byte-identical.
    import lo_enforce

    return lo_enforce.run("every_document_is_where_its_readers_look", None)


def check_the_forms_agree_with_the_assembler() -> list[str]:
    """A shipped prompt body or sheet attribute is not what the rubric produces.
    Reported as A HANDOUT DISAGREES WITH THE RUBRIC.

    GOAL B'S FRESHNESS STEP, and the reason it had to change. `olx_prompts.py
    --check` compares the handouts against what PYTHON's `render()` would write --
    a second opinion from the producer that retired with item C. It answers "would
    this generator write what is on disk", which is no longer the question. The
    question is whether the handouts agree with THE RUBRIC, and the assembler is
    what answers it: `build:assemble-prompts` reads the rubric, assembles all 23
    bodies and 109 attribute values, and exits non-zero on any difference.

    IT SHELLS OUT, like the two grammar checks, and for the same reason they do:
    the thing being compared is produced by the other language, and re-implementing
    it here would make this a third opinion rather than a check.

    CANNOT RUN IS NOT THE SAME AS PASSING. A missing lo-blocks, a missing
    node_modules, a build error -- each returns a FINDING naming what could not be
    done, never silence. The grammar checks state that rule; this one obeys it.
    """
    import re
    import subprocess

    import paths as _p

    lo = _p.LO
    if not (lo / "package.json").exists():
        return [f"no lo-blocks at {lo}, so the handouts were NOT compared against "
                f"the rubric -- which is not the same as their agreeing"]
    try:
        r = subprocess.run(["npm", "run", "--silent", "build:assemble-prompts"],
                           cwd=str(lo), capture_output=True, text=True, timeout=1800)
    except Exception as exc:                        # pragma: no cover
        return [f"the assembler could not be run ({type(exc).__name__}: {exc}), so "
                f"the handouts were NOT compared against the rubric"]
    out = (r.stdout or "") + (r.stderr or "")
    m = re.search(r"BODIES: (\d+) identical, (\d+) differing\s+ATTRS: (\d+) "
                  r"identical, (\d+) differing", out)
    if not m:
        return [f"the assembler produced no verdict, so the handouts were NOT "
                f"compared against the rubric: {out.strip()[-160:]}"]
    _, bodies_bad, _, attrs_bad = (int(x) for x in m.groups())
    if bodies_bad or attrs_bad:
        return [f"{bodies_bad} prompt body(ies) and {attrs_bad} attribute value(s) "
                f"on disk differ from what the rubric produces. The handout is a "
                f"projection of the rubric; where they disagree the rubric is right "
                f"and the handout is stale -- `npm run build:assemble-prompts -- "
                f"--write` in {lo}"]
    return []


def check_composed_documents_are_current() -> list[str]:
    """A composed document no longer matches the halves it was built from.
    Reported as A COMPOSED DOCUMENT IS STALE.

    Every reader of a split document opens the COMPOSED copy, so a stale one is
    read by everything and noticed by nothing: the document is whole, every check
    runs, and they all run against prose nobody is editing. The rubric's expansion
    carries the same check for the same reason, and states the failure exactly --
    "every item still parses, every slot still reads, and the scores describe a
    rubric nobody is editing".

    It also reports a document that has NEVER been composed, which is the same
    failure on a fresh checkout: readers open the composed copy, so an unbuilt one
    is a document that does not exist.
    """
    # PORTED (goal K). The composition itself is ported too --
    # `enforce/composeDocument.ts` reproduces `compose_docs.compose` byte for
    # byte on all four documents, including the 1.2 MB ledger. A check that
    # normalised whitespace would never fire, so it does not.
    import lo_enforce

    return lo_enforce.run("composed_documents_are_current", None)


def check_generic_documents_are_generic() -> list[str]:
    """A document declared to carry no course content carries some.
    Reported as COURSE CONTENT IN A GENERIC DOCUMENT.

    THE PROSE HALF OF `check_module_has_no_course_data`, and it did not exist:
    `course_inventory` parses with `ast` and therefore sees only `.py`, so 25
    markdown files had never been examined at all. Item G2 splits the procedure
    documents from the course written through them; this is what says when a
    split is FINISHED, rather than leaving it to someone's reading.

    IT NEVER KEYS ON A BARE ITEM ID. Several of a course's ids can be ordinary
    words in a generic document -- a two-letter id collides with the abbreviations
    an engine doc lists in a `verdicts=` attribute, and a short question id reads
    as "question one" in a layout example -- and an id scan reported seven clean
    lo-blocks files as contaminated.
    The four signals it does use (a corpus reference, an item beside a participant
    number, the `ITEM/pNN` cell notation, a rate over a known run count) fire
    thousands of times in this repository's records and NOT ONCE in lo-blocks.

    LO-BLOCKS IS IN SCOPE, every markdown file of it, and not by declaration: the
    engine is course-neutral by constitution (C2), so ANY course content in its
    documentation is a finding wherever it appears. THIS repository is checked
    against the declared `GENERIC_DOCS` set instead, because most of its documents
    are SUPPOSED to carry course content.
    """
    from tools import course_inventory as CI
    import paths

    out = []
    try:
        ids = {i for i in CI.item_ids() if not CI._ambiguous(i)}
    except Exception as exc:                      # pragma: no cover
        return [f"cannot read the item ids: {type(exc).__name__}: {exc}"]

    repo = pathlib.Path(str(_HERE_DIR)).parent
    for rel in CI.GENERIC_DOCS:
        f = repo / rel
        if not f.exists():
            out.append(f"{rel} is declared generic in course_inventory.GENERIC_DOCS "
                       f"and does not exist -- drop the entry or restore the file")
            continue
        hits = CI.course_prose(f.read_text(errors="ignore"), ids)
        # A DECLARED ALLOWANCE COVERS ONE SIGNAL AND RATCHETS. See
        # `course_inventory.ANONYMOUS_RATE_ALLOWANCE`: a bare rate identifies no
        # cell, so a document may declare how many it carries -- and that number
        # may fall and may not rise. Any OTHER signal is reported regardless,
        # because a named cell is a named cell whatever the allowance says.
        allow = getattr(CI, "ANONYMOUS_RATE_ALLOWANCE", {}).get(rel) or {}
        for sig, cap in allow.items():
            if sig == "why" or sig not in hits:
                continue
            if hits[sig] > cap:
                out.append(
                    f"{rel} carries {hits[sig]} {sig} signals and declares {cap} "
                    f"-- the allowance ratchets, so this may fall and may not "
                    f"rise. Either the new one names a cell (move it to the "
                    f"course half) or lower nothing and justify the raise")
            hits.pop(sig)
        if hits:
            out.append(f"{rel} is declared generic and carries course content: "
                       + ", ".join(f"{k} x{v}" for k, v in sorted(hits.items())))

    lo = pathlib.Path(str(paths.LO))
    if lo.exists():
        for f in sorted(lo.rglob("*.md")):
            sp = str(f)
            if "/node_modules/" in sp or "/.git/" in sp or "/.stage/" in sp:
                continue
            hits = CI.course_prose(f.read_text(errors="ignore"), ids)
            if hits:
                out.append(f"{f.relative_to(lo)} is ENGINE documentation and carries "
                           f"course content: "
                           + ", ".join(f"{k} x{v}" for k, v in sorted(hits.items()))
                           + ". The engine is course-neutral by constitution (C2)")
    return out


def check_every_definition_is_recorded() -> list[str]:
    """A definition the tree defines and the inventory does not record.
    Reported as DEFINITION IS NOT IN THE INVENTORY.

    THE THIRD GAP IN ONE FAMILY, and each was invisible to the others.
    `check_no_definition_vanished` asks whether a RECORDED name still exists.
    `check_every_module_is_tracked` asks whether a MODULE is recorded at all.
    This asks whether a tracked module's recorded set is CURRENT -- because a
    name outside it cannot be reported lost, nothing having known it was there.

    MEASURED WHEN THIS WAS WRITTEN: 1769 definitions live, 1419 recorded, 350
    unguarded across 21 modules -- `enforcement.py` 130, `measured.py` 46,
    `olx_prompts.py` 26. The ledger had been frozen at its seed because
    `safe_write` reported what it added and recorded none of it.

    The sharpest instance: `editguard.py`'s own `track_new` and
    `UNTRACKED_BY_DESIGN`, added by item G to close the MODULE gap, were
    themselves unrecorded. A cleanup with nothing holding it is a gap with a
    date on it, which is why this check ships with the mechanism that fixes it
    rather than after.
    """
    from tools import editguard
    return editguard.unrecorded()


def check_no_definition_is_named_for_an_item() -> list[str]:
    """A definition named for a course item, undeclared.
    Reported as DEFINITION IS NAMED FOR AN ITEM.

    `check_no_module_is_named_for_a_course_artifact` is §10.7 category 4 over the
    repository's FILE LIST. This is the same rule over the names INSIDE the files,
    and nothing enforced it: item F removed the last item-id LOOKUPS from
    `agreement.py` and `agreement_app.py` and what survived was the item-id NAME.
    `rebuild_gold_1c` no longer rebuilt 1c -- it rebuilt whatever the rubric
    declared -- so the name described the caller's history rather than the
    function's behaviour.

    THE EXCEPTION SET IS NOT EMPTY, which is why the declaration table ships with
    the check rather than after it: `measured._1C_GATE_CEILING` stays by decision,
    because a DECLARATION ABOUT one cell may name that cell where a FUNCTION that
    no longer touches it may not. A check with nowhere to record that would fire
    on it forever and be waved through, which is how a check stops being read.
    """
    from tools import editguard
    return editguard.item_named()


def check_every_module_is_tracked() -> list[str]:
    """A module the inventory does not record, and has not excused.
    Reported as MODULE IS NOT IN THE INVENTORY.

    THE COMPLEMENT OF `check_no_definition_vanished`, and the reason that one
    could read clean while a third of this package was unwatched. `vanished()`
    iterates the INVENTORY's keys: a module absent from it cannot report a loss.
    It is silent, and silence is indistinguishable from intact -- the same
    "unwired check reads as coverage" failure that retired `gold_slots_q6.py`,
    reached by a different route.

    MEASURED WHEN THIS WAS WRITTEN, 2026-09-23: 40 modules of 73 were tracked,
    leaving 33 modules and 400 definitions watched by nothing -- among them
    `coursedata.py`, `rubric_export.py` and `rubric_component.py`. Nothing is
    known to have been lost from them, and that is exactly the point: nobody
    could have said so either way.

    Found because splitting `declaration_source` and `generator_source` created
    two modules and NEITHER entered the inventory. New modules never did. This
    check is what stops the gap reopening on the next new file, which is why it
    ships with the seeding rather than after it -- a one-off cleanup with nothing
    holding it is a gap with a date on it.

    An exemption is legitimate but must be declared, with its reason, in
    `editguard.UNTRACKED_BY_DESIGN`. That table is empty today, deliberately.
    """
    from tools import editguard
    return editguard.untracked()


def _verdict_hedges() -> frozenset:
    """Verdicts that HEDGE rather than judge, from lo-blocks' own vocabulary.

    WAS A SET LITERAL HERE, which made it the third copy of a vocabulary this
    project had already been burned by duplicating -- `verdictVocabulary.ts`
    exists because `EXTRA_VERDICTS` was transcribed once and drifted. `score.py`
    reads this too, so it could not simply move; it is read from THERE now,
    through the same probe `slot_vocab` uses for `KNOWN_VERDICTS`.

    REFUSES RATHER THAN DEFAULTING. A vocabulary that silently falls back to a
    stale copy is how a scan stops recognising a token that is still in use.
    """
    import lo_enforce

    got = lo_enforce.probe("verdict_vocabulary", {})
    if not isinstance(got, dict) or "HEDGES" not in got:
        raise SystemExit(
            "enforcement: the hedge vocabulary could not be read from "
            "lo-blocks, so the audit cannot tell a hedge from a charge")
    return frozenset(got["HEDGES"])


VERDICT_HEDGES = _verdict_hedges()
"""Verdicts offered so a grader can decline, which carry no charge either side.

Exempt from the pairing below BY DESIGN: the web offers `unclear` on 26 slots
whose `codes` map has no entry for it, and that is a hedge with no deduction
rather than a missing code.
"""

# THE WEB->RUBRIC TOKEN BRIDGE, per slot -- DECLARED, not held here.
#
# Sixty-three entries keyed by this course's `item/slot` lived in this module
# until step 7, 2026-09-25. The table and every line of its reasoning are in
# `declaration_source.VERDICT_PAIRS` now and reach the course file from there;
# `check_verdict_tokens_pair` below still reports the slot that is not forced.
VERDICT_PAIRS: dict[str, dict[str, str]] = _declaration("VERDICT_PAIRS")


def check_no_recorded_run_is_an_api_error() -> list[str]:
    """A run whose FEEDBACK IS AN ERROR, recorded in the ledger as a score.

    FOUND 2026-09-08 while asking why six of subgoal Q57's cells had five or more
    fields varying at once. They did not: each had ONE run in which a rate-limit
    rejection was recorded as a scored run --

        feedback: 'Error: LLM error (429): Azure API error: 429 ("Your requests
                   to gpt-5-mini for gpt-5-mini in eastus have exceeded ...'

    247 characters where a real run carries 2,500-4,900, no verdicts returned,
    and the scorer produced a number anyway.

    IT DOES NOT FAIL SAFE, which is why this is a refusal and not a note. Across
    the 18 such runs the recorded score was 0.00 seven times, 4.00 NINE TIMES --
    full marks -- 2.00 once and None once. So the error biases in BOTH
    directions: it zeroes some cells and CREDITS others. A defect that only
    zeroed would at least be conservative.

    ALL 18 WERE ON THE `olx` SIDE, all HTTP 429, one per affected cell, 0.30% of
    5,907 recorded cell-runs. That is small enough to have hidden for weeks and
    large enough to have invented an entire tier of subgoal Q57 and one of
    subgoal Q50's cells (WK1/p1, whose 8-of-9 was this and nothing else).

    An error is not a measurement. `measured.record` should refuse an artifact
    carrying one, the way it refuses an off-contract artifact; this check is what
    catches any that are already recorded.
    """
    # PORTED (goal K). `cross_path.result_cell` is ported with it, as
    # `enforce/resultCell.ts`, and for the same reason it is one function
    # here: the app stores `grader.score` as a FRACTION of `sheet_max` while
    # every other writer stores absolute points. Reading `score` directly gave
    # `None` for every app result -- which is also what an unscored cell looks
    # like. Fire-tested by injecting a 429 into a real recorded run on both
    # sides: byte-identical.
    import lo_enforce

    return lo_enforce.run("no_recorded_run_is_an_api_error", None)


VERDICT_ABSENCE_ENCODING = {
    # HOW EACH ENGINE WRITES "NO VERDICT HERE", measured 2026-09-08 over every
    # recorded run: olx `None` 7,080 times and NOTHING ELSE, python the empty
    # string 3,535 times and NOTHING ELSE. Each side is perfectly consistent
    # with itself and perfectly divergent from the other.
    #
    # BOTH SPELLINGS NOW LIVE IN THE `olx` COLUMN. The python web engine was
    # eliminated (goal O) and its runs were FOLDED INTO `olx`, so an artifact
    # read from that column may carry either -- `None` from the app's own runs,
    # `""` from the folded ones. This map is kept for exactly that reason: it is
    # not a comparison between two live engines any more, it is how a reader
    # recognises an absent verdict in either shape of recorded run.
    "olx": None,
    "python": "",
}

# (item, slot) pairs where both sides recorded an absent verdict and therefore
# disagree on its spelling. 32 pairs across 13 items, measured 2026-09-08. This
# is ONE encoding difference manifesting 32 times, not 32 defects, which is why
# the scope is declared rather than reported cell by cell.
# RE-MEASURED 2026-09-11: 37, up from the 32 measured on 2026-09-08. Not five
# new defects and not a new encoding -- the same single difference (olx `None`,
# python `""`) manifesting in five more places. Every one of the 37 is a
# CLASSIFICATION slot: `observed_type`, `named_type`, `stimulus_move`,
# `antecedent_kind_1/2`, `b1_basis`, `b2_basis`, `b2_names_besides`, `wgb_names`,
# `trigger_expects`, `trigger_behavior`, `restricts`, `restriction_authored`.
# A pick answers `refers_to`, so its `verdict` is absent on BOTH sides by
# construction, and the two sides spell that absence differently -- which is why
# the count tracks how many picks have been recorded on both sides rather than
# anything about agreement. Re-measure and restate when it moves again; a number
# that drifts without explanation is what this declaration exists to prevent.
VERDICT_ABSENCE_SCOPE = 37


def check_engines_encode_an_unrecorded_verdict_alike() -> list[str]:
    """RETIRED 2026-09-24 with the python web engine. ALWAYS RETURNS [].

    It watched whether the two engines spelled "no verdict here" the same way --
    `olx` wrote None and `python` wrote "". That is a difference between two
    ENCODINGS of one column, and there is one encoding now (goal O).

    THE ASYMMETRY IT GUARDED IS STILL HANDLED, by `cross_path.result_picks` and
    `enforcement.VERDICT_ABSENCE_ENCODING`, which read either spelling wherever a
    recorded artifact is opened -- including the folded runs the retired engine
    wrote, which are still in the ledger.
    """
    return []


def no_verdict(x) -> bool:
    """Is this value one of the two spellings of "no verdict here"?

    THE ONE PLACE THAT RULE LIVES. olx writes `None`, python writes `""` --
    see `VERDICT_ABSENCE_ENCODING`. Every reader that compares verdicts across
    the two sides must go through this, or it will report a difference that is
    only a spelling.
    """
    return x is None or (isinstance(x, str) and not x.strip())


def check_no_recorded_run_is_verdictless() -> list[str]:
    """A recorded run that judged NOTHING, whatever the provider said about it.

    THE PROVIDER-INDEPENDENT SIBLING of
    `check_no_recorded_run_is_api_error`, which is string-based and so can only
    catch a failure that says so in English. This one asks the structural
    question instead: did the run come back with any verdicts at all?

    WHY IT IS WORTH HAVING FOR ONE ROW. WK1/p1's HTTP 429 was the ONLY row in
    6,147 with `score` null AND an empty verdict set -- the loud version of a
    defect whose seventeen other instances recorded a plausible NUMBER and a
    full verdict set. The pass that found WK1/p1 found exactly one because it
    was looking for the failure mode it already knew. A future failure carrying
    no error text would slip the string test and land here.

    NOT the same as empty feedback, which is NOT a defect: 528 recorded rows
    have none, almost all on the derived items, which make no LLM call.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K, and this one answers the user's
    # correction that measurement checks are python's by nature: "did this run
    # judge anything at all?" is a question about the SHAPE of a recorded
    # result, generic for any course scored by SlotSheetGrader.
    #
    # PYTHON STILL RESOLVES *WHICH* ARTIFACTS. The ledger owns that -- its `out`
    # pointers and goal O's `folded_from`, where one column is the union of two
    # files -- and duplicating that resolution in TypeScript would be a second
    # reader of the ledger. TS reads the files it is handed, through
    # `enforce/courseData.ts`, which refuses a path outside $COURSE_DATA.
    # SELF-ASSEMBLED. Subgoal E63: the runner builds this payload, and the
    # assembler was proven to build what python built -- payload-identical, or
    # order-only with the finding SET shown unchanged on data mutated until
    # the rule fires. `runner.SELF_ASSEMBLING` is that cleared list.
    import lo_enforce

    return lo_enforce.run("no_recorded_run_is_verdictless", None)



def check_one_writer_per_computed_key() -> list[str]:
    """A slot whose verdict two computed primitives both write.

    WHY IT IS A DEFECT AND NOT A PREFERENCE. `expect` does not override a verdict
    on failure -- it REPLACES it. So a key written by both `maps` and `expect`
    resolves by LOOP ORDER, and on 2026-09-08 the two engines ordered them
    oppositely: `slotSheet.satisfiedMap` runs equals, expect, forbid, MAPS LAST
    ("so a mapped check may read a pick that an earlier rule wrote"), while
    `agreement.apply_computed` ran expect last. Same rubric, same answers, two
    different scores -- and on the python side a box correctly failing as
    `consequence` came out `met`, because the expect clause overwrote the mapped
    verdict wholesale. The mirror was reordered to match the app the same day;
    this check is what stops the collision being authored in the first place.

    FOUND BY TESTING A DESIGN RATHER THAN BY AUDIT: subgoal Q19's Q4b pointing
    proposal needed `expect="behavior_1:b1_points_at=neither"` layered over the
    existing `maps` from `b1_basis`. Reading the primitive answered the design
    question (no) and exposed the divergence (yes) for zero calls.

    ALSO REPORTS THE READ-AFTER-WRITE CASE, which order decides just as much: an
    `expect` or `equals` clause whose OPERAND is a key another primitive writes
    reads a different value depending on where its loop sits. Both engines now
    agree on the order -- the app's, which the mirror was reordered to match
    before it was eliminated -- so this is a warning rather than a divergence; but a
    rubric that relies on it is relying on the order, and the order should not be
    load-bearing in authored data.
    """
    # Two computed primitives on one key resolve by loop order; order must not
    # be load-bearing.
    import lo_enforce

    return lo_enforce.run("one_writer_per_computed_key", None)


def check_verdict_vocabularies_correspond() -> list[str]:
    """A failing verdict one engine can express and the other cannot.

    WHAT THIS IS NOT, because the obvious version is 48 false positives. A
    `codes` key that the prompt never offers is NOT a dead code, and a prompt
    verdict with no `codes` entry is NOT unmapped: the two engines have
    DIFFERENT verdict vocabularies on purpose, and `codes` IS the paper
    vocabulary. Scanning for equality reports 22 "dead codes" and 26 "unmapped
    verdicts" that are all by design -- measured 2026-09-08 before this check
    was written, which is why it is written against a declared pairing instead.

    WHAT IT IS: every failing verdict on each side must have a counterpart on
    the other, via `VERDICT_PAIRS`, with `VERDICT_HEDGES` exempt. A web verdict
    with no paper counterpart is a charge the paper scorer CANNOT EXPRESS -- the
    shape that once told score.py when to answer `wrong_kind` while offering it
    met/absent/not_active, so every test was inert and it credited a Q4b box
    both other engines reject.
    """
    # Every failing verdict on each side must have a declared counterpart on the
    # other.
    import lo_enforce

    return lo_enforce.run("verdict_vocabularies_correspond", None)


# WHERE EACH RECORD WRITER PUTS ITS OUTPUT, and the class that destination must
# be in. `module:accessor -> class`, and the class is one of the four the store
# declares. Registered by hand because a writer's INTENT cannot be derived from
# its code -- the whole question is whether the code agrees with the intent.
RECORD_DESTINATIONS = {
    "coursedata:gold_path": "rubric/derived",
    "coursedata:overrides_path": "rubric/authored",
    "gold_export:default_path": "rubric/derived",
    "tools.export_grader_marks:default_path": "rubric/derived",
    "tools.export_grader_columns:out_path": "instrument/derived",
    "tools.export_response_fixtures:out_dir": "instrument/derived",
}


def check_record_writers_target_the_right_place() -> list[str]:
    """Every record writer's destination is where its class says it goes.
    Reported as A RECORD WRITER AIMS SOMEWHERE ELSE.

    THE GAP THIS CLOSES, asked by the user 2026-09-26: *"Do we have a guard to
    make sure the destination write locations of scripts are the right ones?"*
    There was none. `writescope.sh` says what may be written AT ALL -- a
    security boundary, run by hand -- and nothing said whether a writer aims at
    the right owner or the right class within it.

    IT FOUND TWO THE MOMENT IT EXISTED, and they were mine: repointing the
    exporters at `derived/` left `gold_export` and `export_grader_marks` calling
    `paths.roots()` without importing `paths`. Both destinations raised
    NameError, both scripts still imported cleanly, and nothing reported it
    until one was run. A destination is not exercised by a unit test and not
    checked by a linter; it fails at the moment someone needs the export.

    THREE THINGS ARE ASKED, and they fail differently:
      RAISES   -- the accessor does not survive being called. That is the
                  NameError case, and it is invisible until use.
      OUTSIDE  -- it resolves somewhere no declared root covers, so a record
                  lands where no reader looks.
      WRONG    -- it resolves under the wrong owner or class: a derived record
                  written into `source/` is the one that matters, because
                  `source/` is what nothing may rewrite.
    """
    import importlib

    out: list[str] = []
    r = _p7.roots()
    classes = {
        "instrument/source": r.instrument_dir / "source",
        "instrument/derived": r.instrument_dir / "derived",
        # THE AUTHORED CLASS IS BACK, with the directory it names. A rubric's
        # hand-authored documents spent an afternoon in a `<rubric id>_qc/`
        # directory in the course tree before the user returned them to the
        # store; the override log is written here and this is what checks it.
        "rubric/authored": r.rubric_dir / "authored",
        "rubric/derived": r.rubric_dir / "derived",
    }
    for spec, want in sorted(RECORD_DESTINATIONS.items()):
        mod_name, _, attr = spec.partition(":")
        try:
            got = getattr(importlib.import_module(mod_name), attr)()
        except Exception as exc:
            out.append(
                f"{spec} RAISES {type(exc).__name__}: {exc} -- a writer whose "
                f"destination cannot even be computed fails at the moment "
                f"someone needs the export, and nothing before then says so")
            continue
        if got is None:
            continue                  # declared unavailable, e.g. no data root
        p = _p7.Path(got).resolve()
        base = _p7.Path(classes[want]).resolve()
        if p == base or base in p.parents:
            continue
        where = next((k for k, v in classes.items()
                      if _p7.Path(v).resolve() in p.parents
                      or _p7.Path(v).resolve() == p), None)
        out.append(
            f"{spec} writes to {str(p)!r}, which is {where or 'outside every '
            'declared root'} -- it is declared {want}. A record written to the "
            f"wrong class is read by nobody, and one written under a `source/` "
            f"is rewriting material that cannot be regenerated.")
    return out


def check_records_carry_no_machine_path() -> list[str]:
    """A record that names a directory on THIS machine.
    Reported as A RECORD CARRIES A MACHINE PATH.

    AN ABSOLUTE PATH IN A RECORD IS PINNED TO ONE DISK, and worse, to one DAY's
    layout. Measured 2026-09-26: `PROBED.json` held fifteen paths under the old
    shared `out/` root, every one broken by that morning's move, and nothing
    reported it -- the file still parsed, the fields were still strings, and a
    reader that could not find an artifact simply found none. That is the
    project's signature failure: an empty result reading as a clean one.

    THE FIX IS A ROOT TOKEN, not a tidier absolute path. `{rubric}/...` and
    `{instrument}/...` name the OWNER and let the reader resolve, so the record
    survives a move and travels to another machine. `paths.record_path` resolves
    one; `paths.as_record_path` produces one.

    IT SCANS VALUES, NOT PROSE. A path inside a `why` or a comment is a
    quotation -- the declarations quote paths when explaining an incident -- and
    rewriting those would make the explanation describe something that never
    happened. Only string VALUES at a non-prose key are checked.
    """
    # PORTED to `enforce/recordsCarryNoMachinePath.ts` (goal K).
    #
    # PYTHON PASSES THE PARSED RECORDS it can see. The engine assembles the same
    # four for a native caller; this path answers about the tree THIS process
    # resolves, which is the one a developer is editing.
    import json as _json

    import lo_enforce

    records = []
    for label, p in (("course.json", COURSE_FILE_PATH()),
                     ("PROBED.json", _p7.COURSE_PROBED),
                     ("PROBE_RECEIPTS.json", _p7.COURSE_PROBE_RECEIPTS),
                     ("MEASURED.json", _p7.COURSE_LEDGER)):
        try:
            records.append({"label": label, "doc": _json.loads(open(p).read())})
        except (OSError, ValueError):
            continue
    return lo_enforce.run("records_carry_no_machine_path", {"records": records})


def COURSE_FILE_PATH():
    return _p7.COURSE_FILE


def check_response_fixtures_are_intact() -> list[str]:
    """Every item's reconstruction is recorded, and its shas still describe it.
    Reported as A RESPONSE FIXTURE IS NOT WHAT ITS SHA SAYS.

    THE SHA IS THE WHOLE POINT OF FREEZING. For 24 of 26 items the fixture was
    recomputed from the `.docx` on every run, so a change in the segmenter
    silently changed what every sweep scored -- no stamp, no diff, just a rate
    that moved. Extracting the boxes with a sha per cell makes that visible; a
    sha nobody verifies makes it decoration again.

    IT NEEDS NO CORPUS, deliberately. This asks only whether the record is
    internally consistent and complete: that is the question a machine without
    the submissions can still answer, and it is the one that catches a silent
    re-extraction. Whether the record still matches the SOURCE is a different
    question, answered by `export_response_fixtures.py --verify`, which is the
    one operation that opens a submission.

    A MISSING RECORD IS A FINDING, not silence. An item with neither a frozen
    source nor an extraction falls back to live segmentation, which is exactly
    the arrangement this replaced -- and it would do so without saying so.
    """
    import lo_enforce

    try:
        import agreement_app as AA
        from tools import export_response_fixtures as RF
    except Exception as exc:                      # pragma: no cover
        return [f"the response fixtures cannot be read: {exc}"]

    frozen_elsewhere = sorted(RF.frozen_items())
    items = []
    for item in sorted(AA.JOBS):
        if item in frozen_elsewhere:
            continue
        doc = RF.load(item)
        if doc is None:
            items.append({"item": item, "missing": True})
            continue
        cells = doc.get("cells") or {}
        items.append({
            "item": item,
            "sha": doc.get("sha"),
            "computed": RF.cell_sha({p: c.get("boxes") or {}
                                     for p, c in cells.items()}),
            "cells": [{"pid": p, "sha": c.get("sha"),
                       "computed": RF.cell_sha(c.get("boxes") or {})}
                      for p, c in sorted(cells.items(),
                                         key=lambda kv: int(kv[0]))],
        })
    return lo_enforce.run("response_fixtures_are_intact",
                          {"items": items, "frozenElsewhere": frozen_elsewhere})


def check_olx_attributes_are_all_generated() -> list[str]:
    """A sheet attribute in the .olx that the RUBRIC does not produce.

    STRICT, and it is the guarantee the 2026-09-08 conversion exists to make: an
    item's slot sheet must be derivable from the design, so a design change is a
    rubric edit and never a hand edit to a generated file. Two failures are
    reported, and they are different faults:

      UNACCOUNTED -- the attribute is on the tag and NO generator claims it. That
        is a hand-authored attribute, and it means some behaviour has no design
        of record. Eight such clauses were found this way on 2026-09-08 (`equals`
        on the four cadence items, `onlyif` on NP/NR/PP/PR) -- shipping, scoring,
        and undeclared, so `--write` could not regenerate them and no design
        change could express them.
      DIVERGED -- a generator claims it and produces something else. That is the
        window between a rubric edit and `--write`, which is where 32 probe calls
        were lost measuring a five-option menu while the rule described six.

    WHY IT IS NOT MERELY `--check`. `olx_prompts.py --check` compares the file to
    what `render()` WOULD write, so it goes quiet the moment the file is
    regenerated -- including for an attribute render() copies through untouched.
    This asks the different question: is every attribute PRODUCED BY A GENERATOR
    from the rubric? An attribute nobody generates passes --check forever.
    """
    # PORTED to `enforce/olxAttributesGenerated.ts` (goal K).
    #
    # THE ENGINE HAS THE GENERATORS, which is why this could move at all. It was
    # classified as blocked on `olx_prompts.GENERATED_ATTRS` until the user
    # asked the obvious question -- *"Doesn't web already have its own
    # generators?"* -- and it does: `attributeAssembler.generatedAttrs` is the
    # producer item C installed, verified against these sixteen attribute values
    # and reproducing all of them. Measured again at port time: 368 generator
    # outputs across 23 items compared identical.
    #
    # PYTHON STILL PASSES ITS OWN, so this path compares the .olx against
    # PYTHON's generators and the native path against the engine's. They agree
    # today; the day they stop, `check_the_forms_agree_with_the_assembler` is
    # what says so, and this check keeps answering its own question on each side.
    import re

    import lo_enforce
    import measured as M
    import olx_prompts as OP

    gens = dict(OP.GENERATED_ATTRS)
    items = []
    for item in sorted(M._jobs()):
        action = OP.ACTION.get(item)
        if not action:
            continue
        try:
            tag = OP._sheet_tag(OP.FORM[item], action)
        except BaseException:
            continue
        # `[A-Za-z_]+`, WIDENED 2026-09-26 on both sides together. It was
        # `[a-z_]+`, which excluded every camelCase attribute from a check whose
        # whole purpose is catching an attribute no generator produces --
        # `showChecks` was authored, unclaimed and invisible. Widening ONE side
        # would have been worse than the hole: the two would then disagree about
        # which attributes are in SCOPE, and both would still report zero.
        attrs = [[m.group(1), m.group(2)]
                 for m in re.finditer(r'\b([A-Za-z_]+)="([^"]*)"', tag)]
        generated, errors = {}, {}
        for name, fn in gens.items():
            try:
                generated[name] = fn(item)
            except BaseException as exc:
                errors[name] = f"{type(exc).__name__}: {str(exc)[:80]}"
        entry = {"item": item, "attrs": attrs, "generated": generated}
        if errors:
            entry["errors"] = errors
        items.append(entry)

    return lo_enforce.run("olx_attributes_are_all_generated",
                          {"known": sorted(gens), "skip": ["id", "target"],
                           "handAuthored": dict(HAND_AUTHORED_SHEET_ATTRS),
                           "items": items})

def check_no_judging_field_states_what_a_verdict_costs() -> list[str]:
    """A JUDGING field that explains its own ARITHMETIC to the grader.

    SUBGOAL Q41 NAMED THIS CHECK AND DELIBERATELY DID NOT FILE IT: "no judging
    field may state what a verdict costs is a cheap structural check over the
    three rubrics, it would have caught this at authoring time, and it is
    machinery". Filed 2026-09-08 because the entry's OBSERVATION SITE IS GONE --
    after subgoal Q17's edit (c) the Q2 gate fails on one cell in twenty and that
    cell lists no reasons, so there is no longer a configuration in which the
    contamination can be watched. A structural check settles the general question
    without observing the behaviour at all, which is the only route left that
    costs nothing.

    THE DEFECT IT GENERALISES. `Q2/wgb_is_counterpart`'s desc tells a JUDGING
    grader "its reasons cannot count either, so WGB_UNRELATED stands INSTEAD of
    WGB_NOT_OPPOSITE plus reason deductions, never alongside them". Every word is
    true of the arithmetic and it is addressed to the wrong reader: the model
    EXECUTES it, and on Q2/p10 `reasons_listed` answered 0 on a response holding
    three statements, against that slot's own "Count what is on the page". The
    model said so in all five runs where it happened -- "I did not count reasons
    because ... THE ITEM'S GATE THEREFORE FAILS."

    WHY A PHRASE SCAN IS THE RIGHT INSTRUMENT HERE, when scanning prose usually
    is not: the target is AUTHORED text we control, not student writing or gold
    comments, so the vocabulary is finite and a false positive is a sentence
    worth re-reading anyway. It is fire-tested against the known site, which it
    must flag, and against the rest of the corpus, which it must not.
    """
    # PORTED AND SELF-ASSEMBLED (goal K, step 8). Arithmetic in a judging prompt
    # is executed by the model (subgoal Q41); the pattern and its lookahead
    # carried over alternative for alternative. 146 fields, payload identical.
    import lo_enforce

    return lo_enforce.run("no_judging_field_states_what_a_verdict_costs", None)


def check_pick_choices_match_rubric() -> list[str]:
    """A pick slot whose RUBRIC options are not the menu the grader is offered.

    `slots=` binds a slot to a choice-set -- `b1_basis:...:pick(instead_of_basis)`
    -- and `choices=` lists that set's members. `choices` is now generated
    (`olx_prompts.choices_attr_for`), so this check exists to catch the state
    BETWEEN a rubric edit and a `--write`, which is exactly where 32 probe calls
    were lost on 2026-09-08: Q4b shipped a rule describing `a_listed_trigger`
    while the checklist head still read "one of activity/consequence/
    goal_behaviour/not_doing/none". The grader was told about an option it was
    forbidden to pick, every answer came back from the old five, and the probe
    read as "the mechanism does not fire" when the mechanism was never offered.

    A slot with NO rubric source is not a finding: `named_type` and
    `observed_type` -- twelve instances across the cadence items -- keep their
    sets in the .olx alone, and `_pick_verdicts` returns None for them so the
    generator preserves rather than deletes. Silence about those is deliberate;
    the day one gains a rubric home, this check starts comparing it.
    """
    # A pick menu that has drifted from the rubric is a question the grader
    # cannot answer.
    import lo_enforce

    return lo_enforce.run("pick_choices_match_rubric", None)


def check_no_module_shadow_in_scratchpad() -> list[str]:
    """A scratchpad file whose basename SHADOWS a package module.

    WHY THIS IS A REAL DEFECT AND NOT TIDINESS. On 2026-09-07 a listing script
    did `sys.path.insert(0, SCRATCHPAD)` and then `import enforcement`. It got a
    09-05 copy 1425 lines shorter than the live module, and `DESIGNED_TEXT` --
    added after that copy was taken -- simply did not exist. The traceback said
    "module 'enforcement' has no attribute 'DESIGNED_TEXT'", which reads like a
    clobbered table. THE STALE COPIES WERE agreement.py (55 lines behind),
    enforcement.py (1425), olx_prompts.py (138) and oc_grid.py (an old
    `derive_oc_ledger` signature) -- so a script that imported any of them would
    have MEASURED OLD CODE and said nothing.

    This is the same family as a stale idmap or an unregenerated .olx: the thing
    you consulted was not the thing that ships. Those two are enforced already
    (`check_idmap_is_current`, `prompt_sha`); this closes the third door.

    REVERT SNAPSHOTS ARE NOT FLAGGED and must not be: they are named
    `<module>.before_<tag>.py` or `<module>.pre_<tag>.py`, so their basename
    cannot satisfy an `import <module>`. Only an EXACT basename match can, and
    only that is reported. A cycle legitimately holds a snapshot open until it
    keeps or reverts its edit -- see QUALITY_CONTROL.md 2b-1c.
    """
    import glob

    here = pathlib.Path(__file__).resolve().parent
    mine = {p.name for p in here.glob("*.py")}
    out = []
    for pat in ("/tmp/claude-*/*/*/scratchpad", "/tmp/claude-*/*/scratchpad"):
        for d in glob.glob(pat):
            for f in sorted(glob.glob(d + "/*.py")):
                b = pathlib.Path(f).name
                if b in mine:
                    live = here / b
                    same = (live.read_bytes() == pathlib.Path(f).read_bytes()
                            if live.exists() else False)
                    out.append(
                        f"{f} shadows the package module {b}"
                        + ("" if same else " AND DIFFERS FROM IT")
                        + " -- any script putting that directory first on "
                          "sys.path imports this instead of the live module. "
                          "Delete it; rename a snapshot to "
                          f"{b[:-3]}.before_<tag>.py if it is still needed.")
    return out


def check_closure_ceilings_are_declared() -> list[str]:
    """A closure note calls a cell a CEILING and no table says so.
    Reported as CEILING RECORDED ONLY IN PROSE.

    THE USER'S QUESTION, 2026-09-07: "Should ceilings ever only be recorded in a
    closure note? When we close a goal, shouldn't ceilings be declared
    somewhere?" No, and 2a/p14 is the proof. Subgoal Q35 closed it as a ceiling
    with three good reasons, wrote them in its closure note, and for days the
    cell passed `unstable_cells_without_an_owner` ONLY BECAUSE subgoal Q50
    happened to name it. Being owned by accident is not being declared: if Q50
    closes, a check re-litigates a decision a human already made, and the only
    protection is that somebody remembers reading the note.

    A CLOSURE NOTE IS NOT A DECLARATION. It is prose in a table keyed by goal
    label; nothing indexes it by cell, so no check can consult it and no reader
    diagnosing that cell will find it unless they already know which closed goal
    to read.

    ACCEPTED HOMES, any one of which satisfies this: `DECLARED_CEILING_CELLS`
    (cell-level), `GOLD_CEILINGS` (item-level), `GOLD_DIVERGENCES`,
    `GOLD_SLOT_DISAGREEMENTS_KNOWN`, `SILENT_GOLD_DIVERGENCES`,
    `GOLD_CODE_KNOWN`, `GOLD_SLOT_BOUNDS_KNOWN`, `PER_ITEM_EXCLUDE`. The point is
    that the cell is findable FROM THE CELL, not which table holds it.

    DELIBERATELY NARROW MATCHING. It wants a cell citation within 200 characters
    of ceiling language OF THE CLOSING KIND -- "as a CEILING", "recorded as a
    ceiling" -- not every use of the word, because these notes discuss ceilings
    constantly ("the item's own subgoal already closed at its ceiling"). A
    hand-rolled pattern over prose is what QUALITY_CONTROL.md 2b-3 warns about;
    there is no prepared reader for this question, so this one is written once,
    kept narrow, and fire-tested.
    """
    import ast
    import re

    import goals as GO
    import forms as H
    import measured as M

    declared = set(getattr(M, "DECLARED_CEILING_CELLS", {}))
    for name in ("GOLD_SLOT_DISAGREEMENTS_KNOWN", "SILENT_GOLD_DIVERGENCES",
                 "GOLD_CODE_KNOWN", "GOLD_SLOT_BOUNDS_KNOWN"):
        for k in (getattr(M, name, {}) or {}):
            if isinstance(k, tuple) and len(k) >= 2:
                declared.add((k[0], k[1]))
    for d in getattr(H, "GOLD_DIVERGENCES", []):
        try:
            for it, pid in ast.literal_eval(str(d.get("cells") or "[]")):
                declared.add((it, pid))
        except Exception:
            pass
    items_ceiled = {k[1] for k in (getattr(H, "GOLD_CEILINGS", {}) or {})
                    if isinstance(k, tuple) and len(k) >= 2}
    for item, cells in (getattr(H, "PER_ITEM_EXCLUDE", {}) or {}).items():
        for pid in cells or {}:
            declared.add((item, pid))

    ceil = re.compile("as a CEILING|as a ceiling|recorded as a ceiling"
                      "|closes as a ceiling|closed as a ceiling")
    cell = re.compile(r"\b(1[abc]|2[ab]|3|Q\d[abc]?|D[12]|DAY[12]|WK[12]"
                      r"|N[RP]|P[RP])/p(\d+)\b")
    out = []
    for label, note in sorted((getattr(GO, "CLOSURES_APPROVED", {}) or {}).items()):
        # See measured._live_subgoal_owners: a corpus reference names a cell
        # whose words are quoted, and must not read as a citation of it.
        text = re.sub(r"\[\[corpus[^\]]*\]\]", " ", str(note))
        for m in ceil.finditer(text):
            window = text[max(0, m.start() - 200): m.end() + 200]
            for c in cell.finditer(window):
                item, pid = c.group(1), int(c.group(2))
                if (item, pid) in declared or item in items_ceiled:
                    continue
                out.append(
                    f"{label} closed calling {item}/p{pid} a ceiling and NO table "
                    f"says so -- the reason lives only in that closure note, "
                    f"where no check can read it and no reader of the cell will "
                    f"find it. Add it to measured.DECLARED_CEILING_CELLS with the "
                    f"note's own reasoning")
    return sorted(set(out))


def check_probed_fields_keep_their_text() -> list[str]:
    """A field with probe evidence whose wording is detectable but not
    RECOVERABLE. Reported as PROBED WORDING IS NOT RECORDED IN FULL.

    E56(d), decided 2026-09-07. `DESIGNED_TEXT_SHA.json` holds 145 field shas and
    `DESIGNED_TEXT` holds full text for a handful, so for most fields a drift is
    DETECTABLE and the original is not recoverable. Recording all 145 verbatim
    was rejected: 47KB of duplicated prose nobody reads, and a table that big
    goes stale in a way a sha cannot.

    THE SET THAT EARNS FULL TEXT IS THE SET WITH EVIDENCE. A field somebody
    probed has a measured result attached to one exact string; if that string is
    only a sha, the result cannot be reproduced or compared and the probe's ~30
    calls buy nothing durable. So: any field with a probe receipt must also have
    its text in DESIGNED_TEXT. Everything else stays sha-only, deliberately.

    Silent today, because the Q4b revert removed the only two receipts on record
    -- which is the honest state, not a passing grade. It speaks the moment a
    probe is run and its wording is not written down.
    """
    # PORTED AND SELF-ASSEMBLED (goal K, step 8). A sha detects drift but cannot
    # reproduce the string a result belongs to. The port also DERIVES the sha-
    # only count that this body hardcoded as 145, a literal that had drifted
    # from the file's 146 fields.
    import lo_enforce

    return lo_enforce.run("probed_fields_keep_their_text", None)


def check_no_slot_is_both_asked_and_computed() -> list[str]:
    """WITHDRAWN 2026-09-09, the same day it was written. ALWAYS RETURNS [].

    Its premise was false. It reported a slot listed in `slots=` that also has a
    `maps=` entry as contradictory, and proposed dropping it from `slots=`.
    THE DESIGN REQUIRES BOTH: `slots=` supplies the SPEC -- vocabulary, points,
    gating -- and `maps=` supplies the COMPUTATION. `slotSheet.ts` reads
    `out[r.key] = spec ? isSatisfied(spec, mappedVerdict(r, checks)) : false`, so
    a mapped slot removed from `slots=` has no spec, resolves to FALSE, and has
    its points CHARGED. Acting on this check would have cost `legend`'s 2 points
    on every 1c cell, and the same on Q2, Q4a and Q4b's mapped slots.

    WHAT THE 19 OFF-MAP OBSERVATIONS ACTUALLY WERE. The dev server had run since
    2026-08-29 11:55 under a plain tsx loader with no --watch, while
    `slotSheet.ts` was modified 2026-08-31 22:23. It served CURRENT content on
    STALE code, which no check could see: the idmap check verifies content, and
    the content was fresh. Run against 1c/p8's real payload the current code
    returns `met` and awards the points, scoring 8.0 = gold; the server returned
    6.0. NOT A BUG IN EITHER REPO.

    KEPT AS A FUNCTION RATHER THAN DELETED so that anyone who finds the idea
    plausible again reads why it is wrong before re-deriving it. The real guard
    is `agreement_app.server_code_is_stale`.
    """
    return []


def check_every_designed_entry_ships() -> list[str]:
    """A DESIGNED_TEXT entry whose text is NOT in the prompt its item ships.

    THE GAP THIS CLOSES, found 2026-09-09: SIX OF TWELVE ENTRIES DID NOT SHIP,
    and nothing said so. The three existing links all key off
    `DESIGNED_TEXT_SHA.json`, which holds the rubric's own desc/rule FIELDS --
    so a FRAGMENT key (`rule_addition`, `desc_addition`, `refers_to_addition`,
    `rule_replacement`) never enters that inventory, and
    `check_designed_text_is_the_measured_text` skips it at `if want is None:
    continue`. That check also looks up only the literal field "desc", so an
    entry registered against `rule` was never compared either. The result was
    half the table holding reverted attempts' designs of record, indistinguishable
    from live ones.

    WHY THAT IS NOT COSMETIC. A design of record is what a later reader BUILDS
    FROM. Three times on 2026-09-08/09 a stale or malformed entry was read back
    as live: a Q4c registration read cycle 2's reverted text, and a fragment
    registered under a whole-field key refused the probes on Q1, Q3 AND Q2 at
    once, because preflight is handout-global. An entry that does not ship is
    either a revert nobody finished or a build that silently did not land, and
    those are the two cases this reports.

    Compares on WHITESPACE-NORMALISED text: the rubric wraps its literals across
    source lines, so the shipped prompt never matches a registered string
    character-for-character. Built from `olx_prompts.build_web_prompt`, the same
    call `probe.question_for` and the sweep render from, so what is checked is
    what ships rather than a copy of it.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K. Python builds each item's shipped
    # prompt -- that is `olx_prompts`' job -- and `enforce/designedText.ts`
    # decides whether the designed wording is in it. An item whose prompt cannot
    # be built is REPORTED there, not skipped.
    # SELF-ASSEMBLED. E63: python REBUILDS the prompt and the assembler reads
    # the SHIPPED body, so the payloads differ in reference rendering and
    # whitespace. Proven immaterial on firing data, not on a clean tree.
    import lo_enforce

    return lo_enforce.run("every_designed_entry_ships", None)



def check_designed_text_is_the_measured_text() -> list[str]:
    """A slot with a probe receipt whose DESIGNED_TEXT is not what was probed.
    Reported as DESIGN IS A PARAPHRASE OF ITS OWN EVIDENCE.

    E56(c). THE FAILURE THIS EXISTS FOR, on 2026-09-07: Q4b's two report slots
    were registered in `DESIGNED_TEXT` from GOALS.md's condensed ACCOUNT of the
    design rather than from `probe_q4b_report.py`, the file that was run. The
    entry kept the comparison target and dropped the two clauses that make the
    test work -- the two-part antecedent instruction and the occasion exclusion --
    so a build FAITHFUL TO THE DESIGN OF RECORD would still have over-fired, and
    the design-sha check would have certified it. A design taken from a SUMMARY
    of the evidence is not the evidence.

    The other three checks in this family all compare the tree against a
    DECLARATION. This one compares the DECLARATION against the MEASUREMENT, which
    is the only direction that catches a design nobody measured:

      check_every_prompt_field_is_designed   shipped == designed
      probe.question_for                     probed == shipped, at probe time
      check_probe_receipts_match_shipping    probed == shipped, at sweep time
      THIS CHECK                             designed == probed

    Silent when a slot has no receipt: most fields were never probed and this is
    not a demand that they be. It speaks only where evidence EXISTS and the
    design disagrees with it.
    """
    import probe as PR

    out = []
    for r in PR.receipts():
        key = (r.get("item"), r.get("slot"), "desc")
        want = DESIGNED_TEXT.get(key)
        if want is None:
            continue
        # COMPARE AGAINST THE DESIGNED FIELD AS PROBED, which is the receipt's
        # `checklist_sha`, NOT its `sha`. Those were the same thing until
        # 2026-09-08, when `probe.question_for` was changed to return BOTH
        # prompt sections -- the rubric summary line as well as the checklist
        # line -- because 56 of 179 asked slots were under-reported by the
        # checklist alone. That fix moved `sha` onto the ASSEMBLED question and
        # left this check comparing a raw rubric field against a two-section
        # string, which can never be equal: the design became a "paraphrase" of
        # its own evidence BY ARITHMETIC, for every slot registered after that
        # change. WK2/aimed_correctly still passed only because its receipt
        # predates it.
        #
        # So each check now compares what it actually means:
        #   check_probe_receipts_match_shipping   the ASSEMBLED question, which
        #       is what the grader saw -- `sha`
        #   THIS CHECK                            the DESIGNED FIELD as probed
        #       -- `checklist_sha`, which is `_field_sha` of the rubric text
        # Falling back to `sha` keeps receipts written before the split honest
        # rather than silently unchecked.
        probed = r.get("checklist_sha") or r.get("sha")
        if _field_sha(want) != probed:
            out.append(
                f"{r['item']}/{r['slot']}: DESIGNED_TEXT is {_field_sha(want)} but "
                f"the probe that is its only evidence asked {probed}. The design "
                f"was not lifted from the artifact that measured it -- take it from "
                f"the probe script, not from a summary of the result")
    return out


def check_new_slots_were_probed() -> list[str]:
    """An answerable slot the ledger has never seen, with no probe receipt.
    Reported as NEW SLOT ABOUT TO BE SWEPT UNPROBED.

    E56(a). The vacuous-pass half: with no receipt on record
    `check_probe_receipts_match_shipping` is clean because there is nothing to
    compare, and a clean result there reads exactly like a verified one. Asked
    directly -- "are we sweeping the same prompt as the one we last probed?" --
    the gate could not answer and its silence looked like a yes.

    DELIBERATELY NARROW. It does NOT ask every changed field for a probe: the
    criterion-8 leak fix changed every prompt in the corpus for a good reason and
    a check demanding a probe per field would have refused all of it. What it
    asks about is a slot that is ANSWERABLE, is not in the last recording's cell
    data, and has no receipt -- a brand new question about to be measured for the
    first time. That is the Q19 shape precisely, and it is the one case where the
    probe is nearly free and the sweep is ~230 calls.
    """
    # PORTED to `enforce/newSlotsProbed.ts` (goal K).
    #
    # WEB SIDE ONLY, which is what made it portable: it reads the `olx` column
    # and no other. A ledger check is not unportable for being a ledger check;
    # it is unportable if it touches the PAPER side, which the engine has no
    # counterpart for -- see `measured.web_sides`.
    #
    # PYTHON PASSES WHAT IT READS. The self-test hides the RECEIPTS to prove
    # this still fires, and a payload the runner rebuilt from disk would not
    # see that.
    import agreement_app as _A
    import measured as M
    import probe as PR
    import olx_prompts as O
    import lo_enforce

    asked, seen, probed = {}, {}, {}
    for item in sorted(_A.JOBS):
        if item not in O.ACTION:
            continue              # no judging prompt: no answerable slot to probe
        try:
            asked[item] = sorted(PR._entries(O.build_web_prompt(item)))
        except Exception:
            continue
        names = set()
        # THE WEB SIDE IS `olx`, taken from the contract rather than spelled.
        for side in M.web_sides():
            try:
                doc = M._runs_doc(item, side)
            except Exception:
                continue
            if not doc:
                continue          # nothing recorded on this side
            for run in doc.get("runs") or []:
                for c in run.get("results") or []:
                    names |= set(c.get("checks") or c.get("verdicts") or {})
                    names |= set(c.get("answers") or c.get("refers_to") or {})
        seen[item] = sorted(names)
        probed[item] = sorted({r["slot"] for r in PR.receipts(item)})

    return lo_enforce.run("new_slots_were_probed",
                          {"asked": asked, "seen": seen, "probed": probed})

def check_probe_receipts_match_shipping() -> list[str]:
    """A probe was run, read, and acted on -- and the string it asked no longer
    ships. Reported as PROBE MEASURED TEXT THAT NO LONGER SHIPS.

    THE BACKSTOP UNDER `probe.question_for`. That function makes probe/sweep
    identity structural: it lifts the question out of `build_web_prompt`, so a
    probe cannot ask a string the sweep does not render. What construction cannot
    cover is TIME -- probe on Monday, edit the desc on Tuesday, sweep on
    Wednesday citing Monday's result. The receipt records the sha actually asked;
    this compares it against the sha shipping now.

    That is the Q19 failure exactly, and it is worth being precise about which
    half each mechanism catches, because they are not interchangeable:

      DESIGNED_TEXT_SHA  shipped == designed. Silent on Q19: the shipped desc
                         WAS the designed desc. The probe was the odd one out.
      probe.question_for probed == shipped, by construction, at probe time.
      THIS CHECK         probed == shipped, at SWEEP time.

    A receipt for a slot that no longer exists is reported too, at lower stakes:
    a reverted slot's probe is stale by definition, and the entry should be
    dropped rather than left to look like evidence for the next attempt.
    """
    # PORTED to `enforce/probeReceiptsShipping.ts` (goal K), together with
    # `probe.question_for` and `_derivation` as `enforce/probeQuestion.ts` --
    # measured identical on all 116 credit slots, asked, derived and composite.
    #
    # PYTHON PASSES ITS OWN REFUSALS. `question_for` RAISES for a slot nothing
    # asks, and the message is the finding: it distinguishes "no grader of any
    # kind for a scored criterion" from "not on this sheet at all". Recomputing
    # that text on the other side would be a second copy of a judgement, so it
    # travels with the payload.
    import probe as PR
    import olx_prompts as O
    import lo_enforce

    receipts, refusals = [], {}
    prompts = {i: O.build_web_prompt(i) for i in sorted(O.ACTION)}
    tags = {}
    for i in sorted({**O.ACTION, **O.SHEET_ONLY}):
        try:
            tags[i] = O._sheet_tag(O.FORM[i], O.sheet_id(i))
        except BaseException:
            continue
    aliases = {}
    for r in PR.receipts():
        item, slot = r.get("item"), r.get("slot")
        receipts.append({"item": item, "slot": slot, "sha": r.get("sha"),
                         "verdict": r.get("verdict") or "(none)"})
        aliases[slot] = PR._slot_aliases(slot)
        try:
            PR.question_for(item, slot)
        except LookupError as e:
            refusals[f"{item}|{slot}"] = str(e).splitlines()[0]
        except Exception as e:
            refusals[f"{item}|{slot}"] = f"{type(e).__name__}: {e}"

    return lo_enforce.run("probe_receipts_match_shipping", {
        "prompts": prompts, "tags": tags, "aliases": aliases,
        "answeredUnder": {f"{k[0]}|{k[1]}": list(v)
                          for k, v in PR.ANSWERED_UNDER.items()},
        "receipts": receipts, "refusals": refusals,
    })

def check_shipped_text_matches_design() -> list[str]:
    """A slot whose live text differs from the wording its subgoal designed.

    Reported as SHIPPED TEXT DIFFERS FROM DESIGN.

    Compares DESIGNED_TEXT against the rubric, on normalised whitespace so
    re-wrapping is not a finding. A slot named here and ABSENT from the rubric is
    NOT reported: designs are filed before they are built, and after a revert the
    entry should keep its text so the next attempt starts from the decision
    rather than from memory. What is refused is a slot that EXISTS and says
    something else.
    """
    # PORTED to `enforce/shippedTextMatchesDesign.ts` (goal K).
    #
    # PYTHON PASSES WHAT IT READS rather than letting the runner assemble from
    # `course.json`. The record is exported FROM `DESIGNED_TEXT`, so the two
    # agree until somebody registers a design and does not re-export -- and the
    # one moment this check most needs to be right is the moment a design is
    # being registered. The assembler stays for a native caller, which has no
    # python table to read and no such window.
    import forms as H
    import lo_enforce

    credit: dict[str, list[dict]] = {}
    for h in _forms():
        try:
            by_id = H.config(h)["rubric"].BY_ID
        except Exception:
            continue
        for item, spec in by_id.items():
            if item in credit:
                continue                  # the FIRST form that carries it wins
            credit[item] = [
                {"what": c.get("what"),
                 # EVERY FIELD BY NAME. `DESIGNED_TEXT` is keyed by (item, slot,
                 # field) and `field` is whatever the design named, so narrowing
                 # this to the fields this function happens to know about would
                 # make an unrecognised one read as "designed, not yet built".
                 "attrs": {k: v for k, v in c.items() if isinstance(v, str)}}
                for c in (spec.get("credit") or [])]

    return lo_enforce.run("shipped_text_matches_design", {
        "designed": [{"item": it, "slot": slot, "field": field, "want": want}
                     for (it, slot, field), want in sorted(DESIGNED_TEXT.items())],
        "credit": credit,
    })

def check_verdict_paths_drop_excluded_cells() -> list[str]:
    """A cell excluded from the RATE must not appear in a REVERT decision.

    Reported as EXCLUDED CELL REACHES A VERDICT PATH.

    WHY, and it is a user instruction rather than an inference: "We should not
    have let results on any exclusion affect a revert decision." On 2026-09-06
    subgoal Q30's 1c readout printed p4, p19 and p20 as movers -- all three
    declared in `handouts.PER_ITEM_EXCLUDE` as unreachable on the web, because
    their typed data DRAWS the chart and the paper's "no graph" failure cannot
    occur there. `sweep_readout` dropped `handouts.suspect` and had never heard
    of PER_ITEM_EXCLUDE. The item TOTALS were exclusion-aware so the verdict was
    not numerically wrong, but three cells were listed as findings and were then
    reasoned about as live ones.

    THE PRINCIPLE: a number that cannot count toward the rate cannot count toward
    keeping or reverting an edit, and printing it in a verdict report invites
    exactly that. Suspect cells already had this rule --
    `check_no_declaration_cites_a_suspect_cell` enforces the same thing for
    declarations -- and per-item exclusions did not.

    This asserts it by RUNNING the reporter, not by reading it: for every item
    with exclusions, call `sweep_readout.readout` and check that no excluded
    cell's row appears. A check that greps the source would pass on a reporter
    that consults the table and then ignores it.
    """
    import contextlib
    import io
    import forms as H
    out: list[str] = []
    try:
        import sweep_readout as SR
    except Exception as e:
        return [f"(sweep_readout unavailable: {e})"]
    table = getattr(H, "PER_ITEM_EXCLUDE", {}) or {}
    for item, cells in sorted(table.items()):
        before = {str(p): 12 for p in range(1, 21)}
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                SR.readout(item, before)
        except Exception as e:
            out.append(f"{item}: readout raised {type(e).__name__}: {e}")
            continue
        lines = [ln.strip() for ln in buf.getvalue().splitlines()]
        for pid in sorted(cells):
            if any(ln.startswith(f"p{pid} ") for ln in lines):
                out.append(
                    f"{item}/p{pid} is PER_ITEM_EXCLUDEd yet sweep_readout prints "
                    f"it as a mover -- an excluded cell must not reach a "
                    f"keep/revert decision")
    return out


def check_maps_tables_are_attached() -> list[str]:
    """A rubric module defines MAPS and never hangs it on the item spec.

    Reported as MAPS TABLE IS NOT ATTACHED.

    WHY THIS EXISTS, and it is the cheapest check in the file. Defining `MAPS`
    does nothing on its own -- the generator reads `maps` off the ITEM SPEC, so
    the table has to be attached by the `for _it in ITEMS` loop at the bottom of
    the module. rubric_h1 has carried that loop for as long as maps have
    existed. rubric_h3 was given a MAPS table under subgoal Q30 on 2026-09-06 and
    NOT the loop, and every surface stayed green: the sheet declared the slot,
    the rubric declared the map, `olx_prompts.py --check` reported H3 "up to
    date" -- correctly, because the generator was emitting nothing and the empty
    `maps=""` in the sheet was exactly what it should produce from an item spec
    with no `maps` key.

    NOTHING ELSE COULD HAVE CAUGHT IT. E46's unreachable-verdict check compares a
    map against a verdict list; with no map attached there is nothing to compare,
    so it passes. E48 and E49 ask whether SLOTS reach the sheet and the rubric,
    and both slots did. The defect is in the wiring BETWEEN two things that are
    each individually well-formed, which is the shape no per-side check sees.

    It was found by subgoal Q30's own sweep script asserting that the pick, the
    choices group and the maps rule all live in ONE action -- a bespoke guard in
    a scratchpad file, which is precisely the arrangement `sweep_gate.py` exists
    to replace. The guard refused before spending ~230 calls; this check moves
    that knowledge into the repo so the next module to grow a MAPS table does not
    depend on someone having written the same assertion by hand.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW -- AND IT COULD NOT REPORT BEFORE.
    # Goal K. Both message arms interpolated `name`, a variable that stopped
    # being bound when this loop moved from `for name, mod in (("rubric_h1",
    # rubric_h1), ...)` to `for mod in _rubric_views()`. Either arm raised
    # `NameError: name 'name' is not defined` the moment it fired, so the check
    # returned [] for the only reason that never counts: it was incapable of
    # returning anything else. Found by writing the fire test the port requires.
    # The rubric is identified by its HANDOUT now, which the view order gives.
    # SELF-ASSEMBLED. Subgoal E63: the runner builds this payload, and the
    # assembler was proven to build what python built -- payload-identical, or
    # order-only with the finding SET shown unchanged on data mutated until
    # the rule fires. `runner.SELF_ASSEMBLING` is that cleared list.
    import lo_enforce

    return lo_enforce.run("maps_tables_are_attached", None)



def check_mapped_slots_have_no_unreachable_verdict() -> list[str]:
    """A mapped slot offering a verdict its map can never emit. Subgoal E46.

    AN AUTHORING-TIME CHECK, and it costs nothing to see before a sweep. When
    `maps` computes a slot's verdict from a pick, the slot's own verdict list is
    what the APP still offers the grader. Any value in that list the map cannot
    produce is an answer the grader CAN give and the map cannot account for:
    the app answers the slot directly whenever the map does not determine it,
    so the token is live on the wire and orphaned in the rule.

    THE RATIONALE WAS REWRITTEN 2026-09-25, AND THE INVARIANT WAS NOT. This
    argued from a DIVERGENCE -- the verdict was "dead on the python mirror,
    live on the app" -- and goal O eliminated the mirror, which would have left
    the check standing on a side that no longer exists. What made the orphan
    worth catching was never that two engines disagreed about it; it is that
    the sheet offers an answer the map has no rule for. One engine less does
    not give the token a meaning.

    FOUND BY MEASUREMENT FIRST, which is why the check exists. Q2's
    `wgb_inverts_utb` carries `met`/`absent`/`unclear` while MAPS["Q2"] emits only
    `met` and `absent`. Over 120 olx observations the orphan was used four times.
    The python side disagreed with its map ZERO times in the same 120.

    THE OTHER MAPPED SLOTS PASS, and they are the evidence the invariant is the
    project's own practice rather than a new rule: Q4a's `antecedent_1`/`_2` and
    Q4b's `behavior_1`/`_2` each carry exactly three verdicts and their map emits
    exactly those three, the third being the fallback. None has ever diverged.

    A THIRD VERDICT IS NOT THE PROBLEM -- AN UNREACHABLE ONE IS. Q4a's
    `not_antecedent` and Q4b's `wrong_kind` do real work and carry their own
    deduction codes, distinct from `absent`'s. Q2's `unclear` shares
    `WGB_NOT_OPPOSITE` with `absent`, is never named in the slot's rule or desc,
    and cannot be reached from the pick. It is a duplicate the app can still pick.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K: python reads the slot, what the
    # SHEET offers and what the map emits; `enforce/mappedVerdicts.ts` decides.
    # The sheet is the authority on what the grader may answer -- subgoal E52,
    # where reading the RUBRIC's list instead let the exact fault this check was
    # built for survive a whole sweep.
    #
    # PROVEN WITH A CONTROL: with the counterpart declarations stripped, both
    # sides reported the SAME 2 findings in the same order.
    # SELF-ASSEMBLED. E63: identical once python stopped conflating "the
    # sheet was not found" with "the sheet offers nothing extra" -- see
    # `_olx_slot_verdicts`, and subgoal E52 for why the distinction matters.
    import lo_enforce

    return lo_enforce.run("mapped_slots_have_no_unreachable_verdict", None)



def _same_verdict(a, b) -> bool:
    """Are these two verdicts the SAME judgement under a different name?

    Subgoal E52. The engines' vocabularies differ by design and subgoal E27
    recorded every pair in VERDICT_SPACE_DIVERGENCES -- the app's `wrong_kind`
    is the mirror's `not_antecedent` on Q4a, its `not_consequence` on Q4c, its
    `not_reason` on Q5. Comparing the names alone reported SEVEN counterpart
    shapes as divergences on top of the real ones, which is the false-positive
    class this family keeps falling into: 37 of 39 rubric-vs-sheet mismatches in
    the corpus are E27's design, not defects.
    """
    if a == b:
        return True
    for web, paper in VERDICT_SPACE_DIVERGENCES:
        if (a in web and b in paper) or (a in paper and b in web):
            return True
    return False


# A TAG-ONLY EDIT DOES NOT SUPERSEDE AN ARTIFACT, and the rows live in the course
# file because they name this course's items. `prompt_sha` hashes the served
# `.olx` tag ENTIRE, attributes included, so adding an attribute moves it for every
# item while the model's question is byte for byte what it was. `ask_sha` exists
# for that distinction and `_staleness_lines` already demoted on it; artifact
# attribution did not, and one question-neutral edit made 181 live artifacts read
# as history, producing 45 findings whose implied remedy was a re-sweep that could
# not change a number. The same fault on the other instrument cost ~3,100 calls on
# 2026-09-14: "a measurement instrument moving is not evidence about what students
# saw."
ASK_EQUIVALENT_PROMPTS = _declaration("ASK_EQUIVALENT_PROMPTS")


def _ask_equivalent(item_id: str, side: str, stamp: str) -> bool:
    """Is `stamp` a superseded prompt whose QUESTION is still the current one?

    SELF-CHECKING, NOT TRUSTED: the row carries the `ask_sha` observed when it was
    declared and is honoured only while the current one still equals it.
    """
    import measured as M
    for key in ASK_EQUIVALENT_PROMPTS:
        it, sd, was, ask = key
        if it == item_id and sd == side and was == stamp:
            try:
                return M.ask_sha(item_id, side) == ask
            except Exception:
                return False
    return False


def check_ask_equivalences_still_hold() -> list[str]:
    """Every declared tag-only edit still has the question it was declared for.

    The declaration says "this superseded prompt asked the same thing". That is
    true when written and can stop being true: change the wording afterwards and
    the row would go on excusing artifacts recorded against a DIFFERENT question.
    `_ask_equivalent` already refuses such a row silently; this says so out loud,
    because a declaration that has quietly stopped applying is one nobody removes.
    """
    import measured as M
    out = []
    for key, why in sorted(ASK_EQUIVALENT_PROMPTS.items()):
        item, side, was, ask = key
        try:
            now = M.ask_sha(item, side)
        except Exception as exc:
            out.append(f"{item}/{side}: cannot re-derive ask_sha to check the "
                       f"declared equivalence for {was}: {type(exc).__name__}")
            continue
        if now != ask:
            out.append(
                f"{item}/{side}: the equivalence declared for prompt {was} names "
                f"ask_sha {ask}, but the question is now {now} -- the row no "
                f"longer applies and artifacts stamped {was} are genuinely "
                f"history. Remove it ({why}).")
    return out


def _artifact_prompt_state(doc: dict, item_id: str):
    """Is this artifact's prompt the CURRENT one FOR THE SIDE THAT WROTE IT?

    True, False, or None when the file cannot be dated at all.

    PER SIDE, because an era carries three prompt stamps and an artifact is only
    comparable against its own. Both liveness tests read `era['prompt_sha']` --
    the OLX stamp -- whatever wrote the file, so a paper artifact was dated by
    the WEB's prompt: it read LIVE while its own prompt had moved on, and could
    read historical for a `.olx` edit that never touched the paper scorer. That
    is the same borrowed-sha fault `prompt_sha` itself carried until 2026-09-10,
    surviving in the one place that still hard-coded the side.

    The writer is told apart exactly as cross_path.result_cell tells it apart --
    `cell` is the app, `item_id` is score.py, `participant_id` is the harness --
    because a second way of making that distinction is a second way to get it
    wrong. UNDATABLE IS NOT HISTORICAL: an artifact with no stamp for its own
    side returns None, and each caller decides, so a missing field can never
    silence an alarm.
    """
    import measured as M

    era = (doc.get("era") or {}).get("items", {}).get(item_id, {})
    first = None
    for run in doc.get("runs") or []:
        for r in run.get("results") or []:
            first = r
            break
        if first is not None:
            break
    if first is None:
        return None
    if "cell" in first:
        side, stamp = "olx", era.get("prompt_sha")
    elif "item_id" in first:
        side, stamp = "paper", era.get("prompt_sha_paper")
    else:
            # AN OLD ERA STAMPED FOR THE RETIRED SIDE IS AN `olx` STAMP: its
            # runs were folded into that column (goal O), so the artifact it
            # describes lives there now.
        side, stamp = "olx", era.get("prompt_sha_python")
    if not stamp:
        return None
    try:
        if stamp == M.prompt_sha(item_id, side):
            return True
        return _ask_equivalent(item_id, side, stamp) or False
    except Exception:
        return None


def historical_map_divergences() -> list[str]:
    """Map divergences in artifacts the prompt has moved past. Subgoal E52.

    Kept reachable so the evidence is not lost when the alarm is silenced. These
    are facts about prompts that no longer exist: real when recorded, and not
    something anyone can act on now.
    """
    import json
    import pathlib as _pl

    import measured as M
    import paths as _paths

    root, _why = _paths.out_root_or_reason()
    if root is None:
        return [f"{_why} -- this check cannot run, which is NOT the same as passing"]
    out: list[str] = []
    for item, _mod, s in _maps_specs():
        for path in _runs_files(root, f"*/{item}.runs.json"):
            try:
                doc = jsoncache.load(path)
                if _artifact_prompt_state(doc, item) is not False:
                    continue              # current, or undatable: not historical
            except Exception:
                continue
            for run in doc.get("runs") or []:
                for r in run.get("results") or []:
                    pick = M.slot_answer(r, s["pick"])
                    v = M.slot_verdict(r, s["key"])
                    if pick is None or v is None:
                        continue
                    want = next((q["verdict"] for q in s["pairs"]
                                 if q["value"] == pick), s.get("fallback"))
                    if v == want or _same_verdict(v, want):
                        continue
                    out.append(f"{path.parent.name}: {item}/{s['key']} "
                               f"recorded {v!r} on pick {pick!r}, map said {want!r} "
                               f"(prompt superseded)")
    return out


def check_mapped_slots_agree_with_their_map() -> list[str]:
    """An artifact where a mapped slot's verdict is not what its map computes.

    THE HALF WITH TEETH, and the reason the authoring check above is not enough.
    A grader can override the map using a verdict the map CAN emit, and no
    authoring check can see that. Measured on Q2's olx side: of five
    disagreements in 120 observations, one was `doing -> absent` where the map
    says `met` -- a value squarely inside the map's range. The authoring check
    would have passed it.

    IT READS ARTIFACTS, NOT THE LIVE LEDGER, for subgoal E43's reason: a fault
    that appears in one run and is superseded by the next sweep disappears from
    the ledger while remaining true of what was recorded. The ledger is where a
    number lives; the artifacts are where the behaviour is.

    IT IS A SCORING FAULT. THIS DOCSTRING TWICE SAID OTHERWISE AND WAS WRONG.
    The claim was that both engines score from the map, so only the RECORD is
    damaged. It was based on reading lo-blocks' `satisfiedMap`, which assigns
    `out[r.key] = isSatisfied(spec, mappedVerdict(r, checks))` and looks
    decisive. MEASUREMENT SAYS OTHERWISE, and measurement wins:
        Q2/p1   run 0  recorded `unclear`, map says `met`  -> scored 3.0 / gold 5.0
        Q2/p3   run 3  recorded `unclear`, map says `met`  -> scored 0.0 / gold 2.0
        Q2/p19  run 1  recorded `absent`,  map says `met`  -> scored 2.0 / gold 4.0
        Q2/p10  runs 1,5 recorded `unclear`, map says `absent` -> UNCHANGED
    Every divergent run is a wrong run, and p10 is the control: there the mapped
    verdict was `absent` too, `unclear` is score-equivalent to `absent` on that
    slot, and nothing moved.

    THE MEASUREMENT ABOVE STANDS; ITS EXPLANATION WAS REWRITTEN 2026-09-25. It
    read "the app scores from the RECORDED verdict and the mirror from the MAP,
    and the two genuinely differ" -- and goal O eliminated the mirror. The four
    rows are a record of what was measured and are untouched. What they show
    without any second engine is simpler and no weaker: the app scores the
    RECORDED verdict, so where the map disagrees the run scored something the
    map would never have produced, and the gold column shows what it cost.
    THE LESSON IS ABOUT METHOD, NOT ABOUT MAPS. A source reading that looks
    conclusive was preferred over a measurement that could have been run in one
    command, and the false conclusion was reported as settled. Where the two are
    available, align verdicts to scores PER RUN before believing either.
    """
    import json
    import pathlib as _pl
    import measured as _M
    import paths as _paths

    specs = _maps_specs()
    if not specs:
        return []
    _seen_item: dict = {}
    by_item: dict = {}
    for item, _mod, s in specs:
        by_item.setdefault(item, []).append(s)
    root, _why = _paths.out_root_or_reason()
    if root is None:
        return [f"{_why} -- this check cannot run, which is NOT the same as passing"]
    if not root.is_dir():
        return []
    tally: dict = {}
    for path in _runs_files(root, "*/*.runs.json"):
        item = path.name[: -len(".runs.json")]
        if item not in by_item:
            continue
        try:
            doc = jsoncache.load(path)
        except Exception:
            continue
        # ATTRIBUTABLE TO TODAY'S APP CODE, OR NOT EVIDENCE OF TODAY'S BEHAVIOUR.
        # This check retains a fault a later sweep did not reproduce, which is
        # right -- the artifacts are where the behaviour is. It only holds while
        # the old observation is COMPARABLE: the map is applied by lo-blocks'
        # scoring path, so an artifact that cannot say which app code produced it
        # cannot distinguish "it happened once" from "it happened under code that
        # no longer exists".
        #
        # Measured 2026-09-14: all four surviving findings came from
        # `rr_1c_olx` and `pooled_olx`, which carry NO `web_score_sha` at all and
        # sit on different commits, while today's sweep of the same two items on
        # stamped, current code reproduces none of them. The prompt filter below
        # already refuses an artifact answering a prompt that no longer ships;
        # this is the same rule for the code that scores the answer.
        era = doc.get("era") or {}
        per = (era.get("items") or {}).get(item, {}) or {}
        got_score = per.get("web_score_sha", era.get("web_score_sha"))
        if not got_score or got_score != _M.web_code_sha("score", item):
            continue
        for ri, run in enumerate(doc.get("runs") or [], 1):
            for r in run.get("results") or []:
                for s in by_item[item]:
                    # SUBGOAL E47: the canonical readers, not a hand-rolled
                    # lookup. `slot_answer` tries the PICK fields first because a
                    # python result stores a pick's value in `answers` and an
                    # EMPTY STRING for the same key in `checks`; `slot_verdict`
                    # never accepts a pick, which is what this check requires.
                    pick = _M.slot_answer(r, s["pick"])
                    if pick is None:
                        continue
                    v = _M.slot_verdict(r, s["key"])
                    if v is None:
                        continue
                    want = next((q["verdict"] for q in s["pairs"]
                                 if q["value"] == pick), s.get("fallback"))
                    if v == want or _same_verdict(v, want):
                        continue
                    k = (path.parent.name, item, s["key"], pick, v, want)
                    tally[k] = tally.get(k, 0) + 1
                    _seen_item[path.parent.name] = item
    # LIVE OR HISTORICAL, and the check decides rather than the reader. Subgoal
    # E43 argued -- rightly -- that this must read ARTIFACTS and not the ledger,
    # because a fault superseded by the next sweep vanishes from the ledger while
    # remaining true of what was recorded. The cost of that is a finding list
    # that never shrinks: on 2026-09-06 all ten were in artifacts whose prompt had
    # since changed, and an audit that reports ten permanent "defects" is one
    # nobody reads.
    # SO A DIVERGENCE IS REPORTED WHEN ITS ARTIFACT STILL DESCRIBES THE CURRENT
    # PROMPT. Anything older is a fact about a prompt that no longer exists; it is
    # not deleted -- `historical_map_divergences()` lists it on demand -- but it
    # is not an open issue either. The evidence stays, the alarm stops.
    def _is_live(dirname: str, item_id: str) -> bool:
        import json as _j
        try:
            doc = _j.loads((root / dirname / f"{item_id}.runs.json").read_text())
        except Exception:
            return True          # unreadable: report it rather than hide it
        # Not `is True`: an artifact that cannot be dated stays an open finding,
        # the same way an unreadable one does. Only a prompt shown to have MOVED
        # silences the alarm.
        return _artifact_prompt_state(doc, item_id) is not False

    out: list[str] = []
    for (d, item, key, pick, got, want), n in sorted(tally.items(),
                                                     key=lambda kv: -kv[1]):
        if not _is_live(d, item):
            continue
        out.append(
            f"{d}: {item}/{key} was RECORDED {got!r} on pick {pick!r} where "
            f"MAPS computes {want!r}, x{n}. THE SCORE FOLLOWS THE RECORDED "
            f"VERDICT ON THE APP AND THE MAP ON THE MIRROR, so the two engines "
            f"score the same answer differently -- measured per run, every "
            f"divergent run is a wrong run unless the recorded verdict happens "
            f"to be score-equivalent to the mapped one")
    return out


# SLOTS THE SHEET ASKS AND THE RUBRIC DELIBERATELY DOES NOT DEFINE. Subgoal E49.
# The reverse-direction check reports a sheet slot with no rubric element,
# because the app would otherwise be putting a question to the grader that the
# python scorer never reads. That is usually a defect. It is not always one: an
# UNSCORED slot whose only job is to shape FEEDBACK has nothing for the mirror to
# mirror, since the mirror does not produce feedback at all.
# Keep this table small, and require the two facts that make the claim checkable:
# the slot carries NO points, and something in the generator consumes it.
ONE_SIDED_SCORED_SLOTS_BUDGET = _budget("ONE_SIDED_SCORED_SLOTS_BUDGET")

# Subgoal E53. Slots where the two engines score the SAME judgement through a
# different DECOMPOSITION -- one enumerates per item, the other counts -- so
# neither an alias nor a derivation rule can reconcile the names, and there is
# nothing to fix. Declared rather than excluded silently, because "the app does
# not answer this scored slot" is exactly the shape of a real defect and a reader
# who meets it undeclared cannot tell the two apart.
#
# EVERY ENTRY WAS MEASURED BEFORE IT WAS WRITTEN, per-cell medians on both
# sides. If a future change makes one of these diverge, the declaration is wrong
# and the check will not catch it -- the per-cell comparison is what catches it,
# and it lives in the sweep readouts.
DECOMPOSITION_DIVERGENCES = _declaration("DECOMPOSITION_DIVERGENCES")


def check_scored_slots_are_answered_by_both_engines() -> list[str]:
    """RETIRED 2026-09-24 with the python web engine. ALWAYS RETURNS [].

    It watched: a point-bearing slot answered by one engine and never the other.

    THAT QUESTION NO LONGER HAS TWO SIDES. The python mirror of
    `scoreSlotSheet` was eliminated in goal O, so this would compare a
    thing against itself or against nothing. O's own text named the
    class: "a check that exists to catch drift between two
    implementations is dead weight once there is one implementation".

    KEPT AS A RECORD rather than deleted, so what STOPPED being watched
    stays legible -- the same treatment as
    `check_no_slot_is_both_asked_and_computed`.
    """
    return []


APP_ONLY_SLOTS = _declaration("APP_ONLY_SLOTS")


def _criteria_derived() -> frozenset:
    """The criteria-derived items, READ FROM THE RUBRIC rather than listed.

    Subgoal E35 established that these items' rubric holds COMPOSITES
    (`is_operant_conditioning`, `is_nr`) while the sheet enumerates the
    sub-checks, so nearly every slot on them looks orphaned in the reverse
    direction. That asymmetry is the design, not a defect, and a check that does
    not know it is useless on a third of the corpus.

    IT WAS A LIST OF EIGHT IDS AND IT DID NOT NEED TO BE. The property that
    makes an item criteria-derived is written on the item: its rubric entry
    carries `derive_from_criteria`. Measured across all three rubric modules --
    26 items -- the set carrying that field is exactly the eight that were
    listed, and the four handout-2 items that are NOT in it (D1, D2, T1, T2)
    carry `derive_from_credit` instead. So under A2a this is derived, not
    stored: the engine stops naming this course's items, and an item that gains
    or loses the field is picked up instead of drifting from a tuple nobody
    revisits.

    NOT CACHED, DELIBERATELY. `enforcement_selftest` injects by mutating
    `rubric_h*.BY_ID` in memory, and a cache would hand back the pre-injection
    answer -- the same shape that made the inventory memo serve a stale scan
    until its key learned about the ids. This walks 26 entries; it is cheaper
    than the list it replaces was to maintain.
    """
    out = set()
    # The views: see `_rubric_views`. This function was written hours before the
    # rubric channel moved and reached for the modules directly, which made it a
    # NEW dependence on the files Stage 5 deletes -- added while clearing others.
    for mod in _rubric_views():
        for item, entry in (getattr(mod, "BY_ID", {}) or {}).items():
            if isinstance(entry, dict) and "derive_from_criteria" in entry:
                out.add(str(item))
    return frozenset(out)


def check_sheet_slots_reach_the_rubric() -> list[str]:
    """A slot the SHEET asks that no rubric element defines. Subgoal E49.

    THE REVERSE OF E48, and the direction nothing checked. E48 asserts every
    rubric slot has an entry in `slots=`; this asserts the sheet asks nothing the
    rubric has never heard of. If the two sides are meant to be parallel in
    content and logic, both directions have to hold.

    WHY IT IS THE HARDER DIRECTION, measured before it was built: a naive version
    reports 119 orphans of which ONE is real. A check whose false positives
    outnumber its true ones by 118 is switched off within a day and takes the
    real finding with it -- the same trap as E48's first cut (12 findings, 10
    false) and E52's (39 mismatches, ~37 by design). The three exclusions are
    therefore load-bearing, and each was measured rather than assumed:

      `confident` -- present on all 22 items, a meta-slot with no rubric element
      and no points. By design.
      THE CRITERIA-DERIVED ITEMS -- see `_criteria_derived` above.
      ALIASED NAMES -- a CLI key need not carry its web name; `web_name` is the
      authority, as it is for E48.

    THE ONE REAL FINDING it was built to catch: Q1's `matches_selected`, spelled
    in the sheet as "Same behavior you selected above:matches/differs" and
    appearing ZERO times in rubric_h1, score.py and agreement.py. The app asks
    the grader a question the python scorer never reads and no rubric element
    defines. Whether that is dead weight in the prompt or a check the mirror is
    missing is a disposition this check does not make -- it reports.
    """
    # A slot the sheet asks and no rubric element defines is a question the
    # scorer never reads.
    import lo_enforce

    return lo_enforce.run("sheet_slots_reach_the_rubric", None)


def check_rubric_slots_reach_the_sheet() -> list[str]:
    """A rubric slot with no entry in its item's `slots=` list. Subgoal E48.

    THE GENERATOR OWNS THE PROSE; THE SHEET OWNS THE SLOT LIST. `GENERATED_ATTRS`
    covers `forbid`, `expect` and `maps` -- attributes the rubric fully
    determines -- and deliberately leaves `slots=` authored, because that
    attribute carries four things the rubric has no field for: a short
    grader-facing LABEL, the `!` gate marker, an `@` points override, and the
    `pick(group)` binding to `choices=`. Neither file is derivable from the
    other, so the boundary is right.
    WHAT WAS MISSING IS THE ASSERTION THAT THEY AGREE. Nothing checked that a
    rubric slot has anywhere to land, so adding one produced a prompt that
    INSTRUCTS THE GRADER TO READ A SLOT IT IS NEVER ASKED TO ANSWER.

    MEASURED, and it cost a sweep. On 2026-09-05 subgoal Q18 added
    `b2_names_besides` to Q4b's rubric and rewrote `b2_basis`'s rule to say
    "FIRST READ `b2_names_besides`". The slot never reached `slots=`. The sweep
    ran, spent ~240 calls, and recorded Q4b at 17/19 on both sides against a
    prompt with a dangling reference -- its own targets moved incoherently
    (p12 2/12 -> 6/12 while p6, p8, p14 and p20 all broke) because the rule asked
    for an answer that did not exist. `enforcement.py` exited 0 throughout and
    `check_slot_rules_reach_both_prompts` reported nothing.
    THE SWEEP'S OWN GUARD WAS TOO WEAK AND IS THE LESSON. It asserted
    `olx.count("b2_names_besides") > 0`, which PASSED -- on the two prose
    mentions the generator had just written. Presence in the FILE is not presence
    in the SLOT LIST, and a guard that cannot tell them apart certifies the fault
    it exists to stop.
    """
    # A rubric slot the sheet never asks for is a rule pointing at an answer
    # that cannot exist.
    import lo_enforce

    return lo_enforce.run("rubric_slots_reach_the_sheet", None)


def _rubric_views():
    """The three rubrics as the rest of the audit sees them: views, not modules.

    Nine checks in this file did `import rubric_h1, rubric_h2, rubric_h3` and
    read them directly -- a path neither the `config(h)["rubric"]` swap nor the
    self-test's rebinding touched. Two cases went straight to FAIL because of
    it: a case mutated the view and `check_slot_rules_are_vocabulary_neutral`
    read the module, so the injection was real and the check was looking
    somewhere else.

    There were FIVE paths to the rubric in this codebase and I found them one
    failure at a time. This is the fourth; `_rubric_module` was the third.
    """
    import forms as _H

    return tuple(_H.config(h)["rubric"] for h in _forms())


def _rubric_module(item_id: str):
    """The rubric an item is defined in. Subgoal E48.

    A VIEW ONTO THE COURSE FILE, not the `rubric_h*` module. This imported the
    modules directly, which made it a THIRD path to the rubric alongside the
    `import` statements and `forms.config(h)["rubric"]` -- and the one that
    kept the self-test's injections working after the other two moved. Popping
    `cover` through the view changed nothing the checks using this function
    could see, so the case would have reported VACUOUS: an injection that lands
    somewhere nothing reads.
    """
    import forms as _H

    for form in _forms():
        try:
            view = _H.config(form)["rubric"]
        except Exception:
            continue
        if item_id in getattr(view, "BY_ID", {}):
            return view
    return None


# A COHORT CASE NAME IN A SHIPPED PROMPT. Subgoal E50. `pN` is how this project
# names a participant everywhere -- goals, ledger, artifacts, readouts -- so it
# is one careless paste away from a rule, and a rule naming a case is a rule
# TUNED TO THAT CASE. `leakage.py` catches borrowed WORDS; nothing caught a
# borrowed CELL. The corpus was clean when this was written (0 of 26 SLOT_NOTES
# blocks, 0 rubric rule/desc fields), which is the right moment to nail it down:
# an invariant installed while it already holds costs nothing and never has to
# be argued about afterwards.
# THE PATTERN MOVED TO `enforce/caseNames.ts` with the rule (goal K). It is not
# kept here as a second copy: two regexes for one rule is the divergence class
# this project exists to close, and the TS side is the one under test.


def check_no_case_names_in_prompts() -> list[str]:
    """A participant id in text the grader is shown. Subgoal E50.

    READS THE RENDERED PROMPT, not the sources, because that is what ships and
    it catches every route in -- a SLOT_NOTES block, a rubric `rule` or `desc`, a
    criteria note, or a hand-authored line in the sheet. Checking the sources
    would leave whichever route nobody thought of.

    WHY IT MATTERS MORE THAN IT LOOKS. A rule that names p10 is not merely untidy:
    it is evidence the rule was written against one cell, which is the failure
    mode this project has measured over and over -- ten reverted wordings on Q6,
    three on Q2's inversion boundary, each one a clause aimed at a cell it could
    see. A case name in the prompt is that habit reaching the student-facing side.

    IT IS NOT THE SAME AS LEAKAGE. `leakage.py` asks whether a rule echoes the
    cohort's WORDS. This asks whether it names a cohort MEMBER. A rule can be
    perfectly free of borrowed vocabulary and still say "unlike p10" -- and no
    check saw that until this one.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K: python fetches the prompts and
    # reports; `enforce/caseNames.ts` decides. The judgement sits beside the
    # assembler that produces what it judges, and vitest exercises it against
    # six fixtures -- including the two details the python regex got right and
    # a naive port gets wrong: a `p10` inside a corpus-reference PATH, and a
    # three-digit run no cohort of twenty can contain.
    # SELF-ASSEMBLED. E63: python REBUILDS the prompt and the assembler reads
    # the SHIPPED body, so the payloads differ in reference rendering and
    # whitespace. Proven immaterial on firing data, not on a clean tree.
    import lo_enforce

    return lo_enforce.run("no_case_names_in_prompts", None)


def check_count_scaffolds_are_arithmetic() -> list[str]:
    """A count scaffold that reports a triple its own definition forbids.

    `reasons_given` is DEFINED as `reasons_listed` minus `reasons_failing` -- all
    three slots say so in as many words -- and the engine takes all three from the
    model and scores the third. So the model can return a triple that cannot be
    arithmetic, and has: Q2/p11 reported 0 listed, 0 failing and 3 given, with the
    student's whole answer quoted as evidence for BOTH counting slots. It read the
    response, said it had listed nothing, and then found three benefits in the
    nothing.

    THE SCORE WAS RIGHT, WHICH IS WHY NOTHING NOTICED. Only `reasons_given` is
    scored; `listed` and `failing` are `reported: True`, earning nothing and
    changing nothing, so an impossible triple costs zero points and appears in no
    rate. It was found by reading a cell for an unrelated reason, which is not a
    method -- hence this.

    WHY CHECK RATHER THAN RECOMPUTE, which was subgoal E43's open question. The
    scaffold exists so the model DECOMPOSES its judgement, and that decomposition
    does real work: on Q2/p18 it reproduced the graders' own reading, 3 listed, 1
    restating the problem, 2 counting. Deriving `given` from the other two would
    make the arithmetic unbreakable and throw that away -- a model that miscounts
    the parts would silently get the total computed from them, which is worse than
    one that reports a triple you can see is impossible. Checking keeps the
    decomposition and makes the contradiction loud.

    IT READS EVERY ARTIFACT, NOT THE LIVE LEDGER, and that is deliberate. When
    this was measured on 2026-09-05 the CURRENT Q2 artifacts held 0 violations in
    240 observations -- the run carrying p11's triple had been superseded by a
    later sweep -- while the full set of recorded artifacts held FOUR in 1,260,
    in three distinct shapes:
        q17b_olx   run2 p11   0 - 0 != 3   listed nothing, credited three
        cli_v7     run2 p6    2 - 1 != 2   off by one
        q17_python run1 p6    2 - 1 != 2   the same cell, the other engine
        twoside_cli run6 p10  3 - 0 != 0   listed three, credited none
    A check reading only the live ledger would have reported clean and the defect
    would have vanished with the next sweep, as it already had once.
    """
    import json
    import pathlib as _pl

    import measured as _MEAS
    import paths as _paths

    stems = ("reasons", "benefits", "harms")
    out: list[str] = []
    root, _why = _paths.out_root_or_reason()
    if root is None:
        return [f"{_why} -- this check cannot run, which is NOT the same as passing"]
    if not root.is_dir():
        return []
    for path in _runs_files(root, "*/*.runs.json"):
        try:
            doc = jsoncache.load(path)
        except Exception:
            continue                      # an unreadable artifact is another check's
        # ATTRIBUTABLE TO TODAY'S APP CODE, as `check_mapped_slots_agree_with_
        # their_map` now requires. The count scaffold is computed by the app's
        # scoring path, so an artifact that cannot say which app code produced it
        # cannot distinguish "the arithmetic was wrong" from "the arithmetic was
        # different then". Measured 2026-09-14: the only surviving finding came
        # from `twoside_cli`, which carries no `web_score_sha`, no model and no
        # `measured_at` -- undateable by anything but file mtime.
        _item = path.name[: -len(".runs.json")]
        _era = doc.get("era") or {}
        _per = (_era.get("items") or {}).get(_item, {}) or {}
        _got = _per.get("web_score_sha", _era.get("web_score_sha"))
        try:
            _want = _MEAS.web_code_sha("score", _item)
        except Exception:
            continue                      # not a scored item: nothing to attribute
        if not _got or _got != _want:
            continue
        for ri, run in enumerate(doc.get("runs") or [], 1):
            for r in run.get("results") or []:
                a = r.get("answers") or r.get("refers_to") or {}
                v = r.get("checks") or r.get("verdicts") or {}

                def _n(key):
                    x = a.get(key)
                    if x is None and isinstance(v, dict):
                        y = v.get(key)
                        x = y.get("verdict") if isinstance(y, dict) else y
                    try:
                        return int(str(x))
                    except Exception:
                        return None

                for stem in stems:
                    L, F, G = _n(f"{stem}_listed"), _n(f"{stem}_failing"), _n(f"{stem}_given")
                    if None in (L, F, G) or L - F == G:
                        continue
                    cell = r.get("participant_id") or r.get("cell")
                    out.append(
                        f"{path.parent.name}/{path.name} run {ri} cell {cell}: "
                        f"`{stem}_listed` {L} minus `{stem}_failing` {F} is not "
                        f"`{stem}_given` {G}, and the slots define it as exactly "
                        f"that. Only the third is scored, so this costs nothing and "
                        f"shows in no rate -- which is why it needs a check rather "
                        f"than a reader")
    return out


def check_computed_slot_recovery_is_faithful() -> list[str]:
    """Does recovering an unrecorded slot reproduce the one that WAS recorded?

    A primitive's key is stripped from the web response schema -- the model must
    not be asked a question a rule answers -- so agreement_app.py computes it
    locally and the artifact stores null in both `verdicts` and `evidence`. Same
    for a counted group's members, which are derived from the count the model
    does answer. So the olx artifacts are missing verdicts the python ones carry,
    and `measured._our_failing_slots` was blind to every one of them: NR's
    `demonstrates_type` and `barrier_is_not_this_type` simply did not appear, so
    a caller pooling both sides and taking a majority under-weighted them with
    nothing saying so. It now RECOVERS them, via apply_computed and
    expand_counted, which is the same pair agreement.py runs on its own path.

    Recovery is only legitimate if it is faithful, and that is checkable without
    trusting it: the PYTHON artifacts record both the answered fields AND the
    computed verdicts. So strip the recoverable keys from a python record,
    recompute them from what remains, and require the recorded values back. At
    the time of writing that is 4200 of 4200, exactly.

    THE CHECK EXISTS BECAUSE THE FIRST TWO ATTEMPTS WERE WRONG, and neither
    announced itself. Passing nulls straight through made satisfied_map read
    "never asked" as "failed" and invented failures -- which was then reported
    out loud as an engine divergence on NR/p20, where the two sides in fact agree
    unanimously. Rebuilding from the verdicts alone dropped CLASSIFICATION
    operands whose verdict is null beside a real `refers_to`, so an `expect` rule
    compared against nothing and invented the same failure one level down. And
    recovering with apply_computed alone reproduced 2640 of 4200, every miss a
    counted member. Each attempt looked plausible and produced a clean-looking
    number; only reconstructing against a recorded answer separated them.
    """
    import agreement as A
    import measured as MEAS
    import olx_prompts as O

    tot = ok = 0
    bad: list[str] = []
    for item in sorted(MEAS._jobs()):
        h = MEAS._jobs()[item]["handout"]
        try:
            spec = A.load_action(_p7.handout_olx(h), O.ACTION[item])
        except Exception:
            continue
        recover = set(MEAS._computed_slots(spec)) | {
            k for cr in (spec.get("counts") or []) for k in cr["slots"]}
        if not recover:
            continue
        # THE SURVIVING WEB COLUMN. Was `python`; that column went with its
        # engine (goal O). The question -- does recovering an unrecorded slot
        # reproduce the one that WAS recorded? -- is about the artifact, so it
        # repoints rather than retiring.
        doc = MEAS._runs_doc(item, "olx")
        if doc is None:
            continue
        for run in doc.get("runs") or []:
            for r in (run.get("results") or []):
                pid = r.get("participant_id")
                if pid is None:
                    continue
                ch = {k: v for k, v in (r.get("checks") or {}).items()
                      if v is not None}
                ans = {k: v for k, v in (r.get("answers") or {}).items()
                       if v is not None}
                # Route by the SLOT SPEC, not by the column the artifact
                # happens to use: the artifact flattens `count` and `verdict`
                # into one column, so a counting group's number arrives under
                # `checks`. Wrapping it as `verdict` leaves expand_counted
                # reading no count at all, which silently recovers every member
                # as unmet. Fourth site to need this after the 2026-09-13
                # fallback removal -- the other three are mirror_self_control,
                # _recorded_payloads and probe.
                count_keys = {cr["key"] for cr in (spec.get("counts") or [])}
                full = {k: dict(**({("count" if k in count_keys else "verdict"):
                                    ch[k]} if k in ch else {}),
                                **({"refers_to": ans[k]} if k in ans else {}))
                        for k in set(ch) | set(ans)}
                stripped = {k: v for k, v in full.items() if k not in recover}
                try:
                    back = A.apply_computed(spec, dict(stripped),
                                            MEAS._fixture_cached(item, pid))
                    back = A.expand_counted(dict(spec, _slots=spec["slots"]),
                                            back)
                except Exception as e:
                    bad.append(f"{item}/p{pid}: recovery raised "
                               f"{type(e).__name__}: {e}")
                    continue
                for k in sorted(recover):
                    if k not in ch:
                        continue            # python did not record it either
                    tot += 1
                    got = (back.get(k) or {}).get("verdict")
                    if str(got) == str(ch[k]):
                        ok += 1
                    else:
                        bad.append(f"{item}/p{pid} `{k}`: recorded {ch[k]!r}, "
                                   f"recovered {got!r}")
    if not tot:
        return ["computed-slot recovery was checked against NOTHING -- no python "
                "artifact carries a recoverable slot, so the reconstruction "
                "`measured._our_failing_slots` depends on for every olx cell is "
                "unverified. A check that examines nothing reports clean."]
    if bad:
        head = (f"recovering a computed or counted slot no longer reproduces the "
                f"recorded verdict: {ok} of {tot} match, {len(bad)} do not. "
                f"measured._our_failing_slots reconstructs exactly these keys for "
                f"every olx cell, where nothing is recorded to compare against, so "
                f"a drift here is invisible on that side. Fix the recovery or the "
                f"primitive it mirrors")
        return [head] + [f"    {b}" for b in bad[:8]]
    return []


def computed_recovery_line() -> str:
    """How much of the reconstruction is verified, for the audit's summary."""
    import agreement as A
    import measured as MEAS
    import olx_prompts as O

    tot = 0
    items = 0
    for item in sorted(MEAS._jobs()):
        h = MEAS._jobs()[item]["handout"]
        try:
            spec = A.load_action(_p7.handout_olx(h), O.ACTION[item])
        except Exception:
            continue
        recover = set(MEAS._computed_slots(spec)) | {
            k for cr in (spec.get("counts") or []) for k in cr["slots"]}
        if not recover:
            continue
        # THE SURVIVING WEB COLUMN. Was `python`; that column went with its
        # engine (goal O). The question -- does recovering an unrecorded slot
        # reproduce the one that WAS recorded? -- is about the artifact, so it
        # repoints rather than retiring.
        doc = MEAS._runs_doc(item, "olx")
        if doc is None:
            continue
        items += 1
        for run in doc.get("runs") or []:
            for r in (run.get("results") or []):
                ch = r.get("checks") or {}
                tot += sum(1 for k in recover if ch.get(k) is not None)
    return (f"computed-slot recovery: {tot} recorded verdict(s) across {items} "
            f"item(s) reproduced from the answered fields alone. That is what "
            f"licenses reconstructing the same keys for the olx artifacts, which "
            f"store null for every primitive-answered and counted slot.")


def check_probe_reach_limits_still_apply() -> list[str]:
    """A PROBE_REACH_LIMITS entry whose rule the probe could now reach.

    Each entry claims one thing: the CLI probe cannot construct the state that
    would reveal a sublinear pair. That claim rests on the SHEET, not on the run
    data, so it is checkable without re-running the audit -- which matters, since
    this check runs inside the audit and could not call it back.

    TWO SHAPES MAKE A PAIR UNREACHABLE, and an entry is justified only while its
    item still has one of them:

      a `forbid` with THREE OR MORE conditions -- the probe flips answered fields
      in PAIRS, and no pair of flips satisfies a three-condition rule while the
      third field holds its passing value; or

      a `requires` whose condition is a COMPUTED key -- a computed operand is not
      an answered field, so no flip can set it at all.

    If an item has neither, the probe can reach its pairs by flipping, and the
    entry is excusing a finding that would no longer appear. A declaration that
    outlives its reason is worse than none: it silently claims the audit checked
    something it did not. Retiring one is cheap -- NR's own entry says it "will
    stop applying if the rule ever becomes a gate", and this is what notices.
    """
    import agreement as A
    import measured as MEAS
    import olx_prompts as O

    out: list[str] = []
    for entry in getattr(O, "PROBE_REACH_LIMITS", []) or []:
        for item in (entry or {}).get("items") or ():
            h = (MEAS._jobs().get(item) or {}).get("handout")
            if h is None:
                continue
            try:
                spec = A.load_action(_p7.handout_olx(h), O.ACTION[item])
            except Exception:
                continue
            wide = any(len(r.get("conds") or ()) >= 3
                       for r in (spec.get("forbid") or ()))
            computed = set(MEAS._computed_slots(spec))
            unflippable = any(r.get("cond") in computed
                              for r in (spec.get("requires") or ()))
            if wide or unflippable:
                continue
            out.append(
                f"olx_prompts.PROBE_REACH_LIMITS excuses {item} on the grounds "
                f"that the CLI probe cannot reach its sublinear pair, but {item} "
                f"now has no `forbid` of three or more conditions and no "
                f"`requires` on a computed key -- so a pairwise flip CAN reach "
                f"it and the excuse no longer holds. Drop the item from the "
                f"entry and let the audit probe it")
    return out


def check_goals_record_is_intact() -> list[str]:
    """GOALS.md's entries: unique labels, resolving citations, nothing deleted or
    quietly closed.

    THE LABELS HERE ARE NAMES, NOT POSITIONS, which is why this is not the guide's
    check with a different regex. `Q22` is cited in commits, memory notes, other
    subgoals' prose and QUALITY_CONTROL.md, and it has to mean the same entry
    forever -- so renumbering GOALS.md would be the defect rather than the repair,
    and `goals.py --next` allocates from the maximum in use so a retired number is
    never reissued.

    Four things it refuses, each one an error this project has actually made or
    come close to:

      a DUPLICATE label      leaves every citation of it ambiguous
      a DANGLING citation    a cited subgoal number with no such entry -- a typo,
                             or an entry deleted instead of closed. (No example
                             is spelled out here on purpose: writing one would
                             BE a dangling citation, and this check found the
                             first draft of this very docstring.)
      a DELETED entry        the record is what stops work being redone
      an UNAPPROVED closure  GOALS.md's own first rule is "NEVER CLOSE A GOAL
                             WITHOUT ASKING THE USER FIRST", and it was broken by
                             closing a subgoal inside a recording step. A rule
                             stated in the file it governs and enforced nowhere
                             depends on whoever read it last.

    Citations must carry the word `subgoal`/`goal`, and that is load-bearing:
    `Q1`, `Q2` and `Q4a` are RUBRIC ITEM ids too, so a bare `Q1` in prose is
    usually an item. Requiring the word is what makes the citation check possible
    on this corpus.
    """
    try:
        import goals
    except Exception as e:
        return [f"goals.py will not import: {type(e).__name__}: {e}"]
    return goals.check()


def check_guide_lessons_are_approved() -> list[str]:
    """A lesson goes into the guide only with the user's agreement.

    THE GUIDE IS THE PROJECT'S STANDING INSTRUCTIONS. Adding to it is not the
    same kind of act as recording a measurement or filing a subgoal: it changes
    what everyone is told to do next time. Standing instruction, 2026-09-04, after
    a lesson was added without asking: "Asking for permission before adding
    lessons to the guide should be enforced, not rely on you to remember."

    So it is state. `guide.unapproved_lessons` compares the working guide against
    the COMMITTED one and requires every new lesson -- a bold-led paragraph or a
    heading, which is the house style for a claim the reader is meant to act on --
    to appear in `guide.LESSONS_APPROVED`, keyed by the sha of its prose. Editing
    a lesson lapses its approval on purpose: the sha changes because the claim
    changed, which is the rule leakage.py already applies to its waivers.

    Reflowing a paragraph or correcting a figure inside one does not trip this;
    only adding or rewriting a lesson's own claim does.
    """
    try:
        from tools import guide
    except Exception as e:
        return [f"guide.py will not import: {type(e).__name__}: {e}"]
    return guide.unapproved_lessons()


def check_guide_structure_is_sound() -> list[str]:
    """The quality-control guide's own structure, checked the way it asks code to be.

    THE GUIDE IS AN INSTRUCTION MANUAL THAT OTHER FILES CITE BY SECTION, so a
    duplicated or renamed label breaks a reference the same way a renamed function
    does -- silently, and only for the reader who follows it. On 2026-09-03 six
    sections were inserted with hand-typed labels, three collided with labels that
    already existed, and section 2 ran 2b1, 2b3, 2c, 2d, 2e, 2f, 2a, 2b, 2b2, 2c,
    2d, 2e. It was found by eye, two commits after the guide gained the line "what
    is COMPUTED is likelier to be right than what is WRITTEN".

    Delegates to guide.check(), which settles five things without model calls:
    duplicate labels, subsection ORDER against document order, every §-citation in
    the tree resolving, every backticked identifier still existing in the tree,
    and emphasis balance per PARAGRAPH (per LINE reported 140 issues in a
    hard-wrapped document and every one was the checker's).

    `python3 tools/guide.py --renumber --write` is the repair: it derives labels from
    document order and rewrites every citation to match, so inserting a section
    no longer requires anyone to know what the labels currently are.
    """
    try:
        from tools import guide
    except Exception as e:
        return [f"guide.py will not import: {type(e).__name__}: {e}"]
    return guide.check()


def check_gold_comparisons_share_an_alphabet() -> list[str]:
    """No function may diff OUR slot set against GOLD'S without a vocabulary guard.

    THE TWO SETS COME FROM DIFFERENT ALPHABETS. Ours is read off the slot sheet;
    gold's is reconstructed from grader prose through GOLD_SLOT_CHARGES. A slot
    no phrase maps to cannot appear on gold's side for ANY cell -- gates are the
    whole class, since they carry no points and graders never name them -- so
    comparing the sets raw reports a difference that was settled before any data
    was read.

    FOUR SITES HAD IT, found the day gates were added to the slot profile, and
    each failed differently, which is why this is a static rule rather than a
    number to watch:

      gold_slot_disagreements  reported 1a/p15 as differing on a gate, on a cell
                               where both sides score 0.0 and gold's comment
                               asserts what the gate asserts.
      refusal_precision        scored 1a's `distinguishes_periods` 11 refusals,
                               11 CONTRADICTED, 0 corroborated -- the worst
                               instrument on the item, on a slot that agrees with
                               gold every time it fires.
      sweep_summary            would have defaulted every gate to expected-to-
                               pass on partial-credit cells, turning correct
                               refusals into false charges in the per-check table
                               that prints on every recording.
      bounds_declarations      counted gates against a charge COUNT taken from
                               prose, so len(maj) could never equal it and the
                               ratchet JAMMED -- entries that can never expire.

    Two raised a false alarm and two silently lost a signal, so neither "the
    audit is clean" nor "nothing changed" would have surfaced any of them.

    The rule: a function naming a gold-prose set AND our slot set must also name
    `_gold_nameable_slots`, or be declared in GOLD_ALPHABET_EXEMPT with why the
    comparison is legitimate without it.
    """
    import re
    from pathlib import Path as _P

    GOLD = re.compile(r"gold_charged_slots|gold_charge_bounds|gold_charged_code")
    OURS = re.compile(r"_our_failing_slots|_charging_slots")
    GUARD = re.compile(r"_gold_nameable_slots")

    # AST SPANS, NOT LINE SCANNING. The first version took a function to end
    # where the next `def` began, which is wrong for a NESTED def: the body it
    # built for `measured.split_verdict` ran on into its enclosing function and
    # picked up names that were never in it. The check's only finding on its
    # first run was that false positive -- a check whose one alarm is its own
    # parsing is worse than no check, because it trains you to dismiss it.
    import ast

    bad: list[str] = []
    for path in sorted(_P(__file__).resolve().parent.glob("*.py")):
        src = path.read_text()
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            bad.append(f"{path.stem} will not parse: {e}")
            continue
        hits = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            body = sourcecache.segment(src, node) or ""
            if GOLD.search(body) and OURS.search(body) and not GUARD.search(body):
                hits.append((node.lineno, node.end_lineno, node.name))
        # innermost only: an enclosing function that merely CONTAINS a guarded
        # helper should not be reported for its child's names.
        for lo, hi, fn in hits:
            if any(l2 > lo and h2 <= hi for l2, h2, _ in hits if (l2, h2) != (lo, hi)):
                continue
            if f"{path.stem}.{fn}" in GOLD_ALPHABET_EXEMPT or fn in GOLD_ALPHABET_EXEMPT:
                continue
            bad.append(
                f"{path.stem}.{fn} compares our slot set against gold's without "
                f"restricting to the slots gold's phrase table can NAME. A gate "
                f"is in ours and can never be in gold's, so it will differ on "
                f"every cell. Intersect with measured._gold_nameable_slots(item), "
                f"or declare {path.stem}.{fn} in GOLD_ALPHABET_EXEMPT with why "
                f"the raw comparison is sound here")
    return bad


def check_written_rules_reach_the_shipped_prompt() -> list[str]:
    """A rule edited in the rubric is not delivered until the .olx carries it.

    THE PROMPT REACHES A SWEEP THROUGH THREE STAGES -- rubric_hN.py, then the
    .olx that olx_prompts generates, then the idmap dumped off the dev server --
    and until 2026-09-04 only the LAST TWO were checked. `check_idmap_is_current`
    covers .olx -> dump and refuses to measure against a stale dump.
    `olx_prompts.py --check` covers rubric -> .olx. Nothing joined them, so
    "is every written rule actually delivered?" was not answerable from the
    audit, and the staleness reading answered it WRONG.

    HOW IT READS WRONG, which is the reason this exists. `measured._staleness_lines`
    compares each recording's `prompt_sha` against the CURRENT SHIPPED prompt. A
    rule edited in the rubric and not yet regenerated leaves that sha untouched --
    so the item does not look stale, because the thing the sha measures has not
    moved. Found live: Q3's and Q4b's rules were written and committed, the
    staleness reading showed 8 flags across four OTHER items, and the two items
    carrying undelivered rules read clean. The only thing that knew was the person
    who had queued the sweep.

    IT IS NOT A DUPLICATE OF `--check`. That command answers "does the tree
    differ" for a whole handout and is run by hand; this answers "is a RECORDED
    item's number now describing a prompt the rubric has moved past", per item,
    every time the audit runs. The recording condition is what makes it a finding
    rather than noise: editing a rubric and regenerating a moment later is normal
    work, and an item with no recording has no number to invalidate.

    DERIVED, NOT MAPPED. The generated prompt comes from `build_web_prompt` and
    the handout from `measured._jobs`, both existing authorities. `_changed_sections`
    already computes almost this -- its own docstring says it answers "which items
    are now unmeasured" -- but it runs only at --write time and prints to stderr,
    so the answer is transient. It also reports Vertical TITLES rather than item
    ids, on purpose, and turning titles into ids would be the second copy of a
    mapping that its comment warns against. So this compares per ITEM instead,
    by the line-presence test `check_idmap_is_current` uses one stage later.

    WITH ONE DELIBERATE DIFFERENCE FROM THAT TEST, found by fire-testing rather
    than by reasoning: it caps line length at 130 and this must NOT. A rule
    renders as ONE line, and the two undelivered rules this check was written for
    were 1452 and 1227 characters -- so borrowing the cap verbatim made the check
    report nothing on the exact drift it exists to catch. The cap belongs to the
    idmap check because a server dump re-wraps text and a long line cannot be
    matched whole; here the comparison is against the GENERATOR'S OWN output, so
    a long line either matches exactly or has drifted. Only the lower bound is
    kept, to skip markup.
    """
    # PORTED to `enforce/writtenRulesShipped.ts` (goal K).
    #
    # NARROWED TO THE WEB SIDES, which is the split applied at this call site
    # rather than a new idea: a PAPER recording is not invalidated by the web
    # prompt drifting, because the paper scorer never sees it. Measured before
    # changing it -- 26 items recorded on any side, 26 on the web, none on
    # paper alone -- so the set is the same today and the intent is now stated
    # instead of inferred.
    import olx_prompts as _OP
    import measured as _M
    import lo_enforce

    try:
        recorded = sorted({it for side in _M.web_sides() for it in _M.records(side)})
    except Exception as exc:                      # pragma: no cover
        return [f"cannot read the ledger to find recorded items ({type(exc).__name__}: {exc})"]

    prompts, shipped = {}, {}
    for item in sorted(_OP.ACTION):
        try:
            prompts[item] = _OP.build_web_prompt(item)
            shipped[item] = _OP._src(_M._jobs()[item]["handout"])
        except Exception:
            prompts.pop(item, None)               # SHEET_ONLY items and the like
            continue
    return lo_enforce.run("written_rules_reach_the_shipped_prompt",
                          {"prompts": prompts, "shipped": shipped,
                           "recorded": recorded})

def check_gold_is_read_by_item() -> list[str]:
    """Reading gold for an ITEM must derive the handout, not name it.

    THE MISTAKE THIS REMOVES was made live on 2026-09-03, mid-readout: item 1a
    was looked up with `gold.load_h1()`. 1a is a HANDOUT 3 item. The sheet loaded,
    the row lookup missed, and the readout printed `gold 1a/p15: {}` -- which is
    the same thing a genuinely ungraded cell prints. It was caught only because
    an empty row looked wrong on a cell under discussion; in a corpus-wide scan
    the same silence reads as "nothing to see", and a disagreement disappears.

    Two guarantees, because the accessor is only safe if its premise holds:

      1. EVERY JOBS ITEM IS GRADED BY THE HANDOUT JOBS ASSIGNS IT. This is what
         lets `gold_cell` derive the sheet at all. If JOBS and the sheet ever
         disagree the accessor raises rather than returning `{}`, and this check
         says so before any readout depends on it.
      2. THE ACCESSOR RAISES ON A BAD PAIRING rather than returning empty. Tested
         by asking for an item no sheet grades.

    And the hand-rolled `{1: load_h1, 2: load_h2, 3: load_h3}[h]` sites are held
    to FORM_KEYED_GOLD_READERS, so a new one has to say why it is not using
    the accessor. Several existing sites are legitimate -- they are handed a
    handout, or sweep all three -- which is why this is a declared allowlist and
    not a ban.
    """
    import re
    import measured as M
    from pathlib import Path as _P

    bad: list[str] = []

    # 1. the accessor's premise, item by item
    try:
        jobs = M._jobs()
    except Exception as e:
        return [f"cannot read agreement_app.JOBS: {type(e).__name__}: {e}"]
    for item in sorted(jobs):
        h = jobs[item].get("handout")
        try:
            graded = M._form_gold_items(h)
        except Exception as e:
            bad.append(f"handout {h} (item {item}): gold sheet unreadable: "
                       f"{type(e).__name__}: {e}")
            continue
        if item not in graded:
            bad.append(
                f"JOBS puts {item} on handout {h}, but handout {h}'s gold sheet "
                f"grades no such item. measured.gold_cell derives the sheet from "
                f"JOBS, so this makes every gold read for {item} a bug rather "
                f"than a missing cell")

    # 2. RAISE, not {}. A wrong pairing must be distinguishable from an ungraded
    #    cell, which is the entire point of the accessor.
    try:
        got = M.gold_cell("\x00 no such item \x00", 1)
    except KeyError:
        pass
    except Exception as e:
        bad.append(f"measured.gold_cell raised {type(e).__name__} for an unknown "
                   f"item; it must raise KeyError so callers can tell a bug from "
                   f"a missing cell")
    else:
        bad.append(f"measured.gold_cell returned {got!r} for an unknown item "
                   f"instead of raising -- the silent-{{}} failure it exists to "
                   f"remove is back")

    # 3. the ratchet on hand-rolled loader picks.
    #    FORM-INDEPENDENT ON PURPOSE. The first version matched the dict spelling
    #    `{1: load_h1, 2: ...}` and nothing else, so `cross_path`'s tuple form
    #    `((1, G.load_h1), (2, G.load_h2), ...)` slipped straight past it and the
    #    arm was GREEN BY CONSTRUCTION -- it reported a clean tree with the
    #    allowlist emptied. Caught by firing it, which is the only reason it is
    #    not still passing. Referencing two or more of the three loaders IS
    #    picking by handout, whatever the syntax around it.
    pat = re.compile(r"\bload_h([123])\b")
    for path in sorted(_P(__file__).resolve().parent.glob("*.py")):
        mod = path.stem
        src = path.read_text()
        if re.search(r"^def load_h[123]\b", src, re.M):
            continue          # gold.py, which DEFINES them
        if len(set(pat.findall(src))) < 2:
            continue          # single-handout reference; nothing to pick
        if mod in FORM_KEYED_GOLD_READERS:
            continue
        if any(k.startswith(mod + ".") for k in FORM_KEYED_GOLD_READERS):
            continue
        bad.append(
            f"{mod} picks a gold loader by handout number. Use "
            f"measured.gold_cell(item, pid), which derives the handout, or "
            f"declare {mod} in FORM_KEYED_GOLD_READERS with why the form "
            f"is not coming from an item")
    return bad


def check_no_cell_is_both_corrected_and_declared() -> list[str]:
    """A cell claimed by CORRECTED_GOLD and by GOLD_DIVERGENCES at once.

    The two tables say OPPOSITE things. A correction says gold's number was
    wrong -- against the dictionary, or against the graders' own practice on
    comparable rows -- so the target moves and the cell is then scored against
    the corrected figure. A divergence says gold's number STANDS, that it is a
    coherent decision, and that we knowingly differ from it. A cell cannot be
    both wrong and coherent, and booking it twice double-counts one finding.

    THREE CELLS WERE DOUBLE-BOOKED ON 2026-09-03, which is why this exists:
    DAY1/p1 in BEHAVIOR_NEVER_STATED, NR/p4 in NP_SHAPE_CREDITED_AS_NR, and
    Q4a/p19 in both ANTECEDENT_RULE_APPLIED_AGAINST_ITSELF and A_NOT_ANTECEDENT.
    All three were corrected that day from comparator evidence, by someone who
    did not read the declaration tables first -- and NP_SHAPE_CREDITED_AS_NR is
    NAMED for the very finding the correction wrote up at length as new.

    NOTHING CAUGHT IT FOR A DAY, and the reason is worth keeping. Every existing
    declaration check compares a table against RECORDED data, so while the
    ledger still held pre-correction numbers "we knowingly miss this cell"
    remained TRUE of what was recorded. The contradiction only surfaced on
    re-recording the item against the corrected gold. This check needs no run
    data at all: it is table against table, so it fires the moment the second
    entry is written, whatever the ledger says.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K. The two tables are course data;
    # the rule that one cell may not be both corrected and diverged-from is
    # generic. Python reads the tables, `enforce/goldTables.ts` judges.
    # SELF-ASSEMBLED. Subgoal E63: the runner builds this payload, and the
    # assembler was proven to build what python built -- payload-identical, or
    # order-only with the finding SET shown unchanged on data mutated until
    # the rule fires. `runner.SELF_ASSEMBLING` is that cleared list.
    import lo_enforce

    # PYTHON KEEPS THE FETCH. Self-assembly reads this from DISK; the
    # self-test injects into the IN-MEMORY table and forks, so a rebuilt
    # payload cannot see it and the case goes silent. Measured 2026-09-26.
    import forms as _H_gold
    import lo_enforce

    # READ THROUGH THE MODULE, not through a name bound at import time: the
    # self-test mutates `forms.GOLD_DIVERGENCES`, and a local alias captured
    # earlier would be a different object on the day one of these is reassigned
    # rather than mutated in place.
    return lo_enforce.run("no_cell_is_both_corrected_and_declared", {
        "corrected": sorted(
            [{"item": c[0], "pid": c[1],
              "was": v.get("was"), "score": v.get("score")}
             for c, v in _H_gold.CORRECTED_GOLD.items()],
            key=lambda e: f"{e['item']}{e['pid']}"),
        "divergences": [{"code": d.get("code"),
                         "cells": [list(c) for c in d.get("cells") or []]}
                        for d in _H_gold.GOLD_DIVERGENCES],
    })



def check_no_declaration_cites_a_suspect_cell() -> list[str]:
    """A declaration that argues from a cell whose INPUT is untrusted.

    `handouts.suspect` drops a participant from a whole handout because the
    SUBMISSION cannot be attributed -- handout 2's p2 and p3 carry byte-identical
    transcriptions with different gold rows, so at least one is mis-transcribed.
    Those cells are not weak evidence, they are NO evidence: nothing about the
    marking can be inferred from a row whose input is wrong, in either direction.
    They cannot show gold is careful and they cannot show gold is incoherent.

    This check exists because a CORRECTED_GOLD entry was written that leaned on
    exactly that pair. It argued NR's gold was internally incoherent because p2
    and p3 disagree on identical text, and concluded the item could not be the
    yardstick for a consistency argument. The contradiction is real and is
    precisely WHY both are excluded; it says nothing about how the graders mark.
    The user caught it, having to point out that suspect cells are never
    evidence. The replacement argument -- NR/p9, same item, same structural
    error, charged by gold at the same score the correction assigns -- was both
    simpler and stronger. That is the pattern worth remembering: an argument
    resting on a suspect cell is usually standing in for a better one that was
    never looked for, so this check's finding is a prompt to go and find it.

    PROSE is scanned, not structure, because that is where the reasoning lives.
    A declaration's KEY is already dropped from scoring by `exclusions()`, so the
    leak can only enter through the WHY. A citation inside a sentence that names
    the cell as suspect or excluded is allowed -- that is an entry recording the
    rule rather than breaking it, which this very entry now does.
    """
    # PORTED to `enforce/suspectCellCitation.ts` (goal K).
    #
    # PYTHON KEEPS THE FETCH. The self-test injects by appending a citation to a
    # live `CORRECTED_GOLD` entry IN MEMORY and forking; a payload the runner
    # rebuilt from `gold.json` on disk would not see it, and the check would
    # report clean while the condition it exists for was present.
    import forms as H
    import measured as M
    import lo_enforce

    home_of: dict[str, int] = {}
    for hnd in _forms():
        try:
            for it in H.config(hnd)["rubric"].ITEMS:
                # ITEMS holds dicts, not id strings. Writing str(it) here keyed
                # the map on dict reprs, so nothing ever matched and the check
                # was green by construction -- caught only by the fire test.
                iid = it.get("id") if isinstance(it, dict) else it
                if iid:
                    home_of.setdefault(str(iid), hnd)
        except Exception:
            continue

    entries: list[dict] = []
    for (it, pid), v in getattr(H, "CORRECTED_GOLD", {}).items():
        entries.append({"table": "forms.CORRECTED_GOLD", "label": f"{it}/p{pid}",
                        "home": str(it), "why": (v or {}).get("why", "")})
    for d in getattr(H, "GOLD_DIVERGENCES", []):
        cells = list((d or {}).get("cells") or [])
        home = str(cells[0][0]) if cells else ""
        entries.append({"table": "forms.GOLD_DIVERGENCES",
                        "label": str((d or {}).get("code") or (home or "?")),
                        "home": home, "why": (d or {}).get("why", "")})
    for name in ("GOLD_SLOT_DISAGREEMENTS_KNOWN", "GOLD_SLOT_BOUNDS_KNOWN",
                 "GOLD_CODE_KNOWN"):
        for (it, pid), why in (getattr(M, name, {}) or {}).items():
            entries.append({"table": f"measured.{name}", "label": f"{it}/p{pid}",
                            "home": str(it), "why": why})

    return lo_enforce.run("no_declaration_cites_a_suspect_cell", {
        "entries": entries,
        "homeOf": home_of,
        "suspect": {str(hnd): sorted(H.suspect(hnd)) for hnd in _forms()},
    })

def check_every_wrong_cell_has_an_owner() -> list[str]:
    """A cell we score wrong that no open subgoal and no declaration accounts for.

    The accounting this automates was built by hand over a long session: itemise
    gold's comment for all 109 cells, list every cell wrong at the median, and
    check each one against the subgoals until nothing is unowned. It worked, and
    the reason it is a CHECK now rather than a note saying "do that again" is
    that its product decays silently. Cells move as prompts change. A subgoal
    closes and takes the only home a cell had. The accounting reads as current
    long after it stops being true, because a finished list looks the same
    whether or not it still describes the corpus.

    The hand pass also had a defect no amount of care would have caught: it read
    the CLI median only. Its very first automated run found five cells the cli
    gets right and the web gets wrong -- DAY2/p8, PR/p15, Q2/p18, Q4a/p9, WK2/p8
    -- invisible to a one-sided reading and now carried as Q32.

    Both directions are reported, because the accounting decays both ways:

      * a wrong cell no OPEN subgoal names -- work with nowhere to be recorded;
      * a cell a subgoal is ABOUT that now scores RIGHT -- evidence that has
        moved out from under a subgoal still being worked. That arm closed Q11,
        whose `realistic` over-charge was gone.

    Three exemptions, each a real distinction rather than a way to reach zero.
    A cell in GOLD_DIVERGENCES is a DECLARED miss and is not an orphan. A cell
    declared at slot or code level stays live even when its total agrees, since
    compensating slot errors summing to the right total is the whole reason that
    accounting exists. And only a TITLE mention makes a subgoal ABOUT a cell --
    body mentions are routinely history or controls, and Q19 names cells
    precisely because we score them RIGHT.

    MUST BE CHEAP, since it runs on every audit: it reads the recorded ledger and
    GOALS.md, spawns nothing, and costs about half a second.
    """
    import measured as MEAS

    return MEAS.wrong_cells_without_an_owner()


def check_gold_tables_have_no_duplicate_keys(src: str | None = None) -> list[str]:
    """A key written twice in one of forms.py's declaration tables.

    Same failure as `check_consensus_fixes_have_no_duplicate_cells`, on the
    tables that decide what a cell is measured against: GOLD_CEILINGS,
    CORRECTED_GOLD and PER_ITEM_EXCLUDE.

    THE HAZARD MOVED WITH THE TABLES AND DID NOT GO AWAY. They were dict
    LITERALS in forms.py, so Python resolved a repeated key before any check
    ran — the later entry won and the earlier vanished, invisible in the loaded
    dict and findable only in the source. Since C1b they live in the gold file
    as `{"__dict__": [[key, value], ...]}` pair-lists, and a pair-list carries
    the same key twice just as easily; `json.load` collapses it the same way,
    for the same reason.

    So this reads the FILE, and reads the RAW PAIRS rather than the decoded
    dict, because the decoded dict is the thing that has already lost the
    evidence. When the tables migrated this check reported itself stale rather
    than passing clean, which is the only reason the gap was visible.

    Not hypothetical, and the way it happened is the reason to check it. Q3
    already had a GOLD_CEILINGS entry for `action_oriented`, written from five
    cells. A second ("1", "Q3") entry was added for the same criterion after a
    fresh measurement, by someone who had read the item's error list rather than
    this table, and one of the two became dead text instantly. Both described a
    real ceiling, so nothing looked wrong: the file simply carried two accounts
    of one phenomenon and served whichever came last.
    """
    # A duplicate key is one account silently doing nothing; only the raw text
    # sees it.
    import lo_enforce

    return lo_enforce.run("gold_tables_have_no_duplicate_keys", None)


def check_corrected_gold_matches_the_sheet() -> list[str]:
    """Does every CORRECTED_GOLD entry still correct the row it claims to?

    A correction rewrites the number we are scored against, which makes it the
    most dangerous declaration in the project: if the workbook is revised and a
    correction stays behind, every rate silently measures against a score no
    grader ever gave. So each entry states the value it is replacing, and that
    `was` is checked against the RAW sheet on every run.

    Read through gold.load_hN directly rather than config(h)["gold"](), which is
    the corrected loader — comparing a correction against its own output would
    always agree.
    """
    # A correction records the value it corrects from; the sheet must still read
    # it.
    # PYTHON KEEPS THE FETCH. The self-test injects by rewriting a
    # `CORRECTED_GOLD` entry's `was` IN MEMORY -- "a CORRECTED_GOLD entry no
    # longer matches the sheet" -- and a payload the runner rebuilds from
    # `gold.json` cannot see it.
    #
    # AND THE RAW SHEET IS READ HERE TOO, from the uncorrected loaders, because
    # that is the value a correction's `was` is asserted against. The exported
    # record carries it as `score_raw`, but reading it here keeps this check
    # reading the same sheet the injection would have to change.
    import forms as _H_cg
    import gold as _G_cg

    import lo_enforce

    loaders = {1: _G_cg.load_h1, 2: _G_cg.load_h2, 3: _G_cg.load_h3}
    raw = []
    for h in _forms():
        fn = loaders.get(h)
        if fn is None:
            continue
        try:
            rows = fn()
        except Exception:
            continue                      # corpus absent on this machine
        raw.append({"form": str(h), "rows": {
            str(pid): {str(i): (c.get("score") if isinstance(c, dict) else None)
                       for i, c in (cells or {}).items()}
            for pid, cells in rows.items()}})
    fixes = [{"item": item, "pid": str(pid), "was": float(fix["was"]),
              "score": float(fix["score"]), "why": str(fix.get("why") or "")}
             for (item, pid), fix in sorted(_H_cg.CORRECTED_GOLD.items())]
    return lo_enforce.run("corrected_gold_matches_the_sheet",
                          {"raw": raw, "fixes": fixes})


def check_the_audit_read_the_corpus() -> list[str]:
    """Did the fixture checks actually LOOK at anything?

    Every segment-reading check wraps its read in `except Exception: continue`,
    because a corpus is not present on all machines and one unreadable .docx
    should not stop an audit. That is the right behaviour and it has a sharp
    edge: a bug in the shared reader raises for EVERY submission, every check
    skips every cell, and an audit that examined nothing reports the same clean
    result as an audit that examined everything and found nothing.

    That is not hypothetical either. Moving the four bare `segment()` calls onto
    a shared helper put the helper at module scope, where the `import segment as
    SEG` that each check does locally was not in scope. It raised `NameError` on
    all 60 submissions, and the audit's answer changed from six real findings to
    zero — reported as SUCCESS. Only diffing against the previous run caught it.

    So: if the corpus is here, the checks must have read it. The corpus itself is
    the control — when it is absent there is nothing to assert and this passes.
    """
    present = []
    for h in _forms():
        try:
            import forms as H

            if H.find_submissions(h):
                present.append(h)
        except Exception:
            continue
    if not present:
        return []                          # no corpus on this machine

    problems = []
    for h in present:
        try:
            segs = _segment_as_scored(h, sorted(dict(__import__("forms")
                                                     .find_submissions(h)))[0])
        except Exception as exc:
            problems.append(
                f"H{h}: the fixture checks cannot read this corpus — "
                f"{type(exc).__name__}: {exc}. Every check that reads a segment "
                f"silently skips every cell and reports no findings, which is "
                f"indistinguishable from a clean audit")
            continue
        if not any((v or "").strip() for v in segs.values()):
            problems.append(
                f"H{h}: segmentation returned nothing for the first submission. "
                f"The checks will examine no cells and report no findings")
    if not problems and not _fixture_cells():
        problems.append(
            "the corpus is present but no multi-box cell was collected, so "
            "every fixture check examined nothing and reported nothing")
    return problems



def _gold_corroborates_absence(h: int, iid: str, pid: int, empty: list[str]) -> bool:
    """Does GOLD say the elements whose boxes are empty are themselves absent?

    This check's own premise, from its docstring: gold's wording separates a
    faithful empty box from a lost transcription. "Did not state" or "did not
    address" means the element really is missing, so an empty box is right;
    "does not MATCH" means the grader read something there, so an empty box lost
    it. That test used to be applied by hand, one FIXTURE_GAP_BACKLOG entry per
    cell, each restating what the gold row already says.

    Q6/p8 is the case that made it worth reading directly. Its gold reads "-5
    pts: did not state each consequence being affected and how it is being
    affected", which corroborates all four empty consequence boxes. Two clauses
    of the response were once assigned into them on the argument that an empty
    box lets the FIXTURE do the scoring; measured, that credited `state_c1` and
    moved the cell from its declared divergence alone to a second, undeclared
    disagreement. Gold's bundled deduction is the evidence that those boxes are
    meant to be empty.

    Deliberately narrow: the absence wording must name the KIND of element whose
    box is empty. Gold saying an antecedent is missing does not excuse an empty
    consequence box.
    """
    import forms as H

    try:
        row = H.config(h)["gold"]().get(pid, {}).get(iid, {}) or {}
    except Exception:
        return False
    fb = _norm(row.get("feedback") or "")
    if not fb:
        return False
    if "does not match" in fb or "not the same as" in fb:
        return False                    # the grader read something there
    absent = ("did not state", "did not address", "did not include",
              "did not provide", "missing", "did not say")
    if not any(a in fb for a in absent):
        return False
    kinds = {("consequence" if k.rstrip("12").endswith(("_c", "c")) else "antecedent")
             for k in empty}
    return all(kind in fb for kind in kinds)


def _counts_sig(form: int, item: str) -> tuple:
    """The rubric's counted-group shape for one item.

    Part of the fixture cache key, and that is the whole point rather than a
    detail: handout 3's boxes are rebuilt by score.py's counted-group
    distribution, so the fixture DEPENDS on this declaration. Caching on
    (item, pid) alone would have returned the clean fixture after the self-test
    dropped 2a's `counts`, and the case that proves this check works would have
    failed while looking like a passing cache.
    """
    from forms import config

    try:
        spec = config(form)["rubric"].BY_ID.get(item) or {}
    except Exception:
        return ()
    return tuple((cr.get("key"), tuple(cr.get("slots") or ()))
                 for cr in (spec.get("counts") or ()))


@functools.lru_cache(maxsize=None)
def _sections_cached(form: int, pid: int) -> tuple:
    """One participant's transcribed sections, as a hashable tuple of pairs.

    Independent of any rubric declaration -- it is the .docx transcription -- so
    unlike the fixture cache this one needs no signature in its key.
    """
    import agreement_app as AA

    try:
        return tuple(sorted((AA.sections_for(form, pid) or {}).items()))
    except (Exception, SystemExit):
        return ()


@functools.lru_cache(maxsize=None)
def _fixture_built(side: str, item: str, pid: int, _sig: tuple):
    """One assembled fixture, cached. None when it cannot be built.

    Uncached, this check cost the self-test dearly: it assembles a fixture per
    (item, participant, harness), and the self-test runs the whole audit once per
    injected breakage, so the same ~500 builds were repeated 55 times.
    """
    import agreement as A
    import agreement_app as AA

    try:
        if side == "olx":
            return AA.build_jobs(item, [pid])[0].get("fixture") or {}
        return A.fixture_for(item, pid) or {}
    except (Exception, SystemExit):
        return None


def check_fixture_boxes_hold_the_students_words(items=None) -> list[str]:
    """A fixture box filled with something the student never wrote.

    Handout 3's answer is ONE prose block, and its on-screen boxes are
    reconstructed by score.py's counted-group distribution: it reads the count
    slot's evidence, pulls the quoted spans out, and deals them to the members.
    When there are fewer spans than the count it writes a PLACEHOLDER instead --
    `score.py`'s `f"{raw_n or '0'} found"`, which is the literal string "2 found".

    So the reconstruction is only as good as the count group being declared. Take
    `counts` off an item and the distribution stops running, the placeholders are
    never overwritten, and every scorer-sourced box silently becomes a 7-character
    stub. The scorers then grade "2 found" as if the student had written it.

    THAT HAPPENED, and it is why this check exists. Subgoal Q2's structural
    experiment un-derived 2a's two `how` slots so each box could be judged on its
    own. The rubric edit also removed the count group, which removed the fixture
    reconstruction with it, and 2a/p4's two boxes went from 246 and 193 characters
    of the student's answer to "2 found" and "2 found". A 120-call sweep then
    measured the item at 10/20 against a baseline of 15/20 and the change looked
    refuted. It had never been tested. The corruption was diagnosed afterwards
    from the returned rows, which is the wrong end: the user's point was that this
    belongs BEFORE the calls, and it is now a preflight in both sweep harnesses as
    well as an audit check.

    NOTHING ELSE CAUGHT IT, and each near-miss is instructive.
    `check_fixture_covers_the_response` looks for an EMPTY box beside a long
    unassigned run of the response; a box holding a placeholder is not empty, so
    the conjunction never fired. `agreement_app.context_value` DOES guard this
    exact string -- its comment names "2 found" and how it once reached items 3
    and 2b as read-only context -- but only on the CONTEXT path, and the guard
    itself asks `counted_members`, so removing the count group disabled the guard
    and the corruption in one stroke.

    The test is the student's own words: a box sourced from the scorer must appear
    in the transcribed response for that participant. Real spans are quoted OUT of
    it and always do; a placeholder never does.
    """
    import re as _re

    import agreement as A
    import agreement_app as AA

    out: list[str] = []
    norm = lambda t: " ".join(str(t or "").split()).lower()
    want = set(items or ()) or None
    for item in sorted(AA.JOBS):
        if want is not None and item not in want:
            continue
        spec = AA.JOBS[item]
        h = spec.get("handout")
        boxes = sorted(spec.get("from_scorer") or {})
        if not boxes:
            continue
        for pid in range(1, 21):
            sec = dict(_sections_cached(h, pid))
            if not sec:
                continue
            # THE SOURCE ITEM'S SECTION, not this item's. A box in `from_scorer`
            # can belong to ANOTHER item shown as read-only context -- Q5 seeds
            # Q4c's two consequence boxes -- and comparing those against Q5's own
            # text reported 72 false positives on a clean tree. CONTEXT_SOURCE
            # holds the owner.
            owner = {c: src[1] for c, src in AA.CONTEXT_SOURCE.items()
                     if src[0] == "scorer"}
            # THE ASSEMBLED FIXTURE, not the raw evidence. `scorer_evidence`
            # legitimately holds placeholders and its callers guard them; what
            # matters is the value that reaches a prompt. Both harnesses are read,
            # because they assemble independently and either could drift.
            built = {}
            # SystemExit, not just Exception. A fixture builder RAISES SystemExit
            # on an unrelated defect -- Q6/p9's duplicate CONSENSUS_FIXES span is
            # one -- and SystemExit does not inherit from Exception, so an
            # `except Exception` here let it escape and killed the whole audit
            # mid-run. A check that cannot examine a cell must skip it quietly,
            # never take the harness down with it.
            for name in ("olx",):
                got = _fixture_built(name, item, pid, _counts_sig(h, item))
                if got is not None:
                    built[name] = got
            for side, fx in built.items():
                for comp in boxes:
                    whole = norm(sec.get(owner.get(comp, item)))
                    val = str(fx.get(comp) or "")
                    v = norm(val)
                    if not whole or not v or v in whole:
                        continue
                    # A DISTRIBUTED NEGATION IS STILL THE STUDENT'S WORDS. Q6/p6
                    # wrote [[corpus Q6/p6 state_a2 3:38 sha=d7d19592b8a2]] and the hand split has to repeat the "not" to
                    # make the second box stand alone, so the box is a faithful
                    # reading that is not a verbatim substring. Allowing only a
                    # LEADING negator keeps the test exact for everything else.
                    if _re.sub(r"^(not|no|never)\s+", "", v) in whole:
                        continue
                    out.append(
                        f"{item}/p{pid} [{side}]: the fixture box `{comp}` holds "
                        f"{val[:40]!r}, which does not appear in the student's "
                        f"transcribed answer. A scorer-sourced box is a SPAN "
                        f"QUOTED OUT of the response, so text that is not in it "
                        f"is not the student's -- most likely score.py's "
                        f"`N found` placeholder, which means this item's "
                        f"counted-group distribution is not running. Every "
                        f"scorer reading this box grades what nobody wrote")
    return out


def check_fixture_covers_the_response() -> list[str]:
    """Does the split fixture still contain the student's whole answer?

    Q6's eight boxes are a RECONSTRUCTION — a frozen consensus table with
    tie-breaks — and it is the input every scorer sees. `check_handsplit_rows_are_disjoint`
    asserts no row swallows another, but nothing asserted that a split PRESERVES
    the response.

    It does not always. p5's Q6 ends "[[corpus Q6/p5 state_c2 0:112 sha=6d2b4490a7d6]]
    {{corpus:Q6/p5:state_c2:113:141:sha=dc7614fc70b7}} {{corpus:Q6/p5:affect_c2:0:49:sha=c20b853f77bc:shape=S7-0a20202020}} often" — a complete second consequence, and both of its boxes are
    EMPTY. About 200 characters never reach the scorer, which then correctly
    reports what it was given (`absent`) and disagrees with a grader who read
    the whole answer. We spent this session treating that cell as evidence that
    gold under-counted, and recommended declaring it unscoreable.

    Lexical coverage alone cannot find this: a clause-level split discards
    connective and elaborative text everywhere, and the longest unassigned run
    is 22-27 words on several perfectly good cells. The signal is the
    CONJUNCTION — an EMPTY box while a long run of the response is unassigned.
    That flags four cells on Q6, of which three are correct and declared above:
    gold's own wording separates them. "Did not state" or "did not address"
    means the element really is missing and the empty box is faithful; "does not
    MATCH" means the grader read something there, so an empty box is a lost
    transcription.
    """
    import forms as H
    import segment as SEG

    problems = []
    seen: set[tuple[str, int]] = set()
    for h in _forms():
        cfg = H.config(h)
        try:
            subs = H.find_submissions(h)
        except Exception:
            continue                       # corpus absent on this machine
        if not subs:
            continue
        for pid, path in subs:
            try:
                segs = _segment_as_scored(h, pid)
            except Exception:
                continue
            for item in cfg["rubric"].ITEMS:
                iid = item["id"]
                raw = _norm(segs.get(iid, ""))
                if len(raw.split()) < 20:
                    continue               # too short for a gap to mean anything
                if H.cell_exclusions(h, iid).get(pid, ("", ""))[0] == "unscoreable":
                    # No gold to corrupt. An `unscoreable` cell has had its gold
                    # withdrawn — rebuild_declared_gold nulls 1c/p20 outright — so it
                    # reaches no comparison and a fixture gap in it cannot move a
                    # number. 1c/p20 was carrying a backlog entry that restated,
                    # word for word, the exclusion already recorded against it.
                    # Declaring the same fact twice means it can go stale in one
                    # place and not the other.
                    continue
                boxes = _span_boxes(iid, pid)
                if len(boxes) < 2 or not any(not v for v in boxes.values()):
                    continue               # no empty box: nothing to lose text to
                # Measure over UNCLAIMED SENTENCES only. A lost element is a
                # sentence, or a run of them, that no box reaches into; text
                # inside a sentence some box already claims is the connective
                # tissue a clause-level split necessarily leaves behind.
                #
                # Q6/p17 is all of the second kind — the student's own "(UTB)"
                # and "(WGB)" labelling and a lead-in clause, each wedged inside
                # a sentence whose other half is in a box — and it carried a
                # per-cell note saying exactly that.
                #
                # Sentence granularity, not "between the first and last box":
                # masking the whole middle would hide a dropped interior
                # sentence, which is the very thing this check is for (Q6/p5's
                # missing second consequence, and Q5/p11's dropped third
                # sentence, both found that way).
                spans = [(at, at + len(t)) for at, t in
                         ((_locate(raw, _norm(v)), _norm(v))
                          for v in boxes.values() if v) if at >= 0]
                unclaimed, pos = [], 0
                for sent in re.split(r"(?<=[.!?])\s+", raw):
                    lo, hi = pos, pos + len(sent)
                    pos = hi + 1
                    if not any(a < hi and lo < b for a, b in spans):
                        unclaimed.append(sent)
                run, text = _longest_unassigned(
                    " ".join(unclaimed), [_norm(v) for v in boxes.values()])
                if run < 10:
                    continue
                if (iid, pid) in FIXTURE_GAP_BACKLOG:
                    seen.add((iid, pid))
                    continue
                empty = sorted(k for k, v in boxes.items() if not v)
                if _gold_corroborates_absence(h, iid, pid, empty):
                    continue
                problems.append(
                    f"H{h} {iid}/p{pid}: {', '.join(empty)} empty while {run} words "
                    f"of the response are assigned to no box — \"...{text}...\". "
                    f"Either the split lost them, or add the cell to "
                    f"FIXTURE_GAP_BACKLOG with the gold wording that says the "
                    f"element really is absent")
    for stale in sorted(FIXTURE_GAP_BACKLOG.keys() - seen):
        problems.append(
            f"FIXTURE_GAP_BACKLOG lists {stale[0]}/p{stale[1]}, which no longer "
            f"has an empty box with unassigned text. Remove it")
    return problems


def _locate(raw: str, box: str) -> int:
    """Where `box` starts in `raw`, ignoring whitespace differences, or -1.

    A hand-split or a scorer quote can differ from the response by a space that
    nobody typed: Q4b/p7's `second` box reads [[corpus Q4b/p7 first 0:18 sha=1608aa905e2c]] where
    the student wrote "2)Also". An exact search misses it, the box counts as
    unlocated, and its whole 33-word sentence is reported as belonging to no box
    — a fixture defect that is really a matching defect.
    """
    b = "".join((box or "").split()).lower()
    if len(b) < 10:
        return -1
    idx, squashed = [], []
    for i, ch in enumerate(raw):
        if not ch.isspace():
            squashed.append(ch.lower())
            idx.append(i)
    at = "".join(squashed).find(b[:40])
    return idx[at] if at >= 0 else -1


_BOXES_MEMO: dict[tuple[str, int], dict[str, str]] = {}
# Which spec key filled each box, recorded by `_fixture_boxes` as it labels them
# so nothing has to re-derive the label. Read it with `_box_provenance`.
_PROV_MEMO: dict[tuple[str, int], dict[str, str]] = {}


def _fixture_boxes(item_id: str, pid: int) -> dict[str, str]:
    """The item's OWN input boxes from the fixture — not its read-only context.

    Read from the JOBS spec, not from the field names. A name heuristic
    (`_<item>_<box>`) covered handout 1, where fields are `bmod_h1_q6_state_a1`,
    and silently returned NOTHING for handout 2's `bmod_h2_pr` or handout 3's
    `bmod_h3_success_verdict`. Both handouts were therefore absent from every
    fixture check — reported as "no multi-box cells" when the truth was "not
    looked at". The spec says which fields carry this item's response:
    `fields` entries whose source is the item itself, everything in
    `from_scorer`, and a hand-split row's own keys.
    """
    import warnings
    if (item_id, pid) in _BOXES_MEMO:
        return dict(_BOXES_MEMO[(item_id, pid)])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from agreement import fixture_for
        import agreement_app as APP
        try:
            fx = fixture_for(item_id, pid)
        except Exception:
            return {}
        spec = APP.JOBS.get(item_id) or {}

    own = {f for f, src in (spec.get("fields") or {}).items() if src == item_id}
    own |= set(spec.get("from_scorer") or {})
    own |= set(spec.get("sim") or {})
    hs = spec.get("handsplit")
    hs_keys: set[str] = set()
    hs = str(_p7.record_path(hs)) if hs else hs
    if hs:
        import json, os
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), hs)) as fh:
                hs_keys = set(json.load(fh).get(str(pid), {}))
        except Exception:
            pass
        own |= hs_keys
    key = f"_{item_id.lower()}_"
    own |= {k for k in fx if key in k and "ref" not in k}

    # `from_scorer` carries CONTEXT as well as the item's own response, and the
    # context is another item's field. Q5's spec pulls `bmod_h1_q4c_first` and
    # `_second` so the Q5 grader can see the consequences — and those label to
    # `first`/`second`, exactly like Q5's OWN `bmod_h1_q5_first`/`_second`. The
    # labels collided, set iteration decided the winner, and Q5's boxes came out
    # holding Q4c's text: every one of its 20 cells was being read out and
    # checked against a different item's answer. It raised no finding because
    # the borrowed boxes were never EMPTY, which is the coverage check's trigger.
    #
    # A field cannot be keyed on this item's name alone — handout 3's fields are
    # `bmod_h3_success_verdict`, with no `_2a_` in them. So the test is the other
    # way round: a field belongs to another item when it carries THAT item's key
    # and not this one's.
    others = {f"_{o.lower()}_" for o in APP.JOBS if o != item_id}
    own = {f for f in own
           if key in f or not any(o in f for o in others)}

    def label(field):
        tail = field.split(key)[-1] if key in field else field
        return tail.rsplit("_", 1)[-1] if key not in field else tail

    src = {}
    for f in (spec.get("sim") or {}):
        src[f] = "sim — parsed from the data table or the chart"
    for f in (spec.get("from_scorer") or {}):
        src[f] = "from_scorer — the paper scorer's extracted value"
    for f, origin in (spec.get("fields") or {}).items():
        if origin == item_id:
            src[f] = "fields — a span of the response segment"
    for f in hs_keys:
        src[f] = "handsplit — read by hand"

    out = {label(f): str(fx.get(f, "")).strip() for f in own if f in fx or True}
    out = {k: v for k, v in out.items() if k}
    _BOXES_MEMO[(item_id, pid)] = out
    _PROV_MEMO[(item_id, pid)] = {
        label(f): src.get(f, "field") for f in own if label(f)}
    return dict(out)


def _box_provenance(item_id: str, pid: int) -> dict[str, str]:
    """{box: which spec key filled it}, for a cell with no prose to locate it in.

    Recorded by `_fixture_boxes` as it labels the fields, rather than derived
    again here: the labelling rule has two corrections in it already (a field
    belonging to ANOTHER item, and the `first`/`second` collision that had Q5's
    boxes holding Q4c's text), and a second copy would drift away from both.
    """
    _fixture_boxes(item_id, pid)
    return dict(_PROV_MEMO.get((item_id, pid)) or {})



def _value_derived(item_id: str) -> set[str]:
    """Boxes holding PARSED VALUES rather than quoted spans of the response.

    Handout 3's 1b is answered with a data table and 1c with a drawing, not with
    prose. Their `sim` boxes hold what simulate_h3 parsed out: 1b/p15's `wk1` is
    `8, {{corpus:1a/p15:wk1:3:19:sha=7b2512f124b3}} 9` for a student who typed "Sunday - 8 hours Monday -
    11 hours ...". The value is right and the box is right, but it appears
    nowhere as a SUBSTRING of what the student wrote, so every check that works
    by locating a box inside the response calls the entire response unassigned.

    That is what flagged 1b/p15 and three 1c cells. All four fixtures were
    faithful; 1b/p15's empty `baseline` and `wk3` are the student's own "none"
    and "Week Three Data: Lost", which gold's 2.0 agrees with. The locator-based
    checks only make sense for boxes that quote the response, so they ask here
    which boxes those are.

    Provenance decides it, so read it off the JOBS spec — the same rule
    `_fixture_boxes` uses to name a box — rather than guessing from box names.
    """
    import agreement_app as APP

    spec = APP.JOBS.get(item_id) or {}
    key = f"_{item_id.lower()}_"
    out = set()
    # BOXES THE SPEC DECLARES VALUE-DERIVED. 1c's three are read off the GRAPH,
    # not off the prose segment — the paper scorer takes them from the chart,
    # which is why p11's `title` arrives filled while its prose segment is
    # empty. They are extractions of named elements, not quotations, and the
    # item has no prose-derived box at all. The one cell where a title IS
    # locatable is p9, whose chart flattened INTO the text; that is a property
    # of the transcription, not of the item.
    #
    # THIS READ `if item_id == "1c"` UNTIL E58, 2026-09-25 -- the one fact the
    # docstring above says should come off the spec. It is a `value_derived`
    # key on the job now, beside the rest of that item's provenance.
    #
    # AND IT IS NOT `from_scorer`, which is the generalisation that suggests
    # itself and is wrong: eight items carry a `from_scorer` block and seven
    # hold boxes a locator CAN find. Deriving it that way would have silently
    # dropped Q6's eight boxes, Q3's five and four items' pairs from every
    # locator-based check. Measured before it was written, not after.
    out |= set(spec.get("value_derived") or ())
    for field in (spec.get("sim") or {}):
        tail = field.split(key)[-1] if key in field else field
        out.add(tail if key in field else tail.rsplit("_", 1)[-1])
    return out


def _span_boxes(item_id: str, pid: int) -> dict[str, str]:
    """`_fixture_boxes` minus the boxes that hold values instead of quotations."""
    drop = _value_derived(item_id)
    return {k: v for k, v in _fixture_boxes(item_id, pid).items() if k not in drop}


def _longest_unassigned(raw: str, boxes, n: int = 5) -> tuple[int, str]:
    """Longest run of response words appearing in no box, and that run.

    `boxes` is the list of box texts (a single joined string is accepted too).
    The list form matters. Coverage is computed from n-grams, so a box SHORTER
    than n words can never match one, and its text reads as unassigned however
    faithfully it was transcribed. Q6/p6's `change_a1` is three words — "while
    stretching daily." — and the moment it was correctly split out of a box that
    had swallowed the whole sentence, the check called it lost text. A short box
    is located whole instead.
    """
    rw = raw.split()
    texts = [boxes] if isinstance(boxes, str) else [t for t in boxes if t]
    bw = " ".join(texts).split()
    have = {tuple(bw[i:i + n]) for i in range(len(bw) - n + 1)}
    cov = [False] * len(rw)
    for i in range(len(rw) - n + 1):
        if tuple(rw[i:i + n]) in have:
            for j in range(i, i + n):
                cov[j] = True
    for t in texts:
        tw = t.split()
        if not tw or len(tw) >= n:
            continue
        for i in range(len(rw) - len(tw) + 1):
            if rw[i:i + len(tw)] == tw:
                for j in range(i, i + len(tw)):
                    cov[j] = True
    best = cur = at = 0
    for i, c in enumerate(cov):
        cur = cur + 1 if not c else 0
        if cur > best:
            best, at = cur, i - cur + 1
    return best, " ".join(rw[at:at + best])[:70]


# Cross-element containments in the Q6 consensus table that are FAITHFUL: the
# student really did write the same words twice, so two boxes holding them is a
# true transcription and the grader's own machinery handles it.
# Entries and their reasoning: `coursedata.gold_notes("CONSENSUS_OVERLAP_BACKLOG", key)` (28 lines).
CONSENSUS_OVERLAP_BACKLOG = _gold_declaration("CONSENSUS_OVERLAP_BACKLOG")


def _cover_groups(item_id: str) -> list[set[str]]:
    """Boxes the slot sheet declares as covering ONE list between them.

    Q6's LLMAction carries cover="state_a1,state_a2:first,second|state_c1,
    state_c2:first,second". That means the two boxes answer between them a list
    of two items: the grader asks WHICH each box refers to and demotes one that
    names an item already claimed. Two boxes in such a group holding the same
    text is an expected input, not a defect — it is the case the mechanism was
    built to resolve.

    Q6/p6 is that case. One conjoined phrase, [[corpus Q6/p6 state_a1 0:21 sha=641b355f6e09]] & [[corpus Q6/p6 state_a2 0:38 sha=53450ef3ac65]], names both of 4a's triggers under a
    single "not", so neither half can be split off without inverting it. The
    scorer labelled both boxes `first` and cover demoted the second, as
    designed. That carried a per-cell declaration; the fact is in the slot
    sheet, so it is read from there.

    Matched by SLOT NAMES rather than by the grader id: `cover` sits on the
    <LLMAction>, thousands of characters from the grader it feeds, and a
    proximity search silently found nothing.
    """
    import re

    import paths

    boxes = set(_fixture_boxes(item_id, 1)) or set()
    for h in _forms():
        try:
            src = open(paths.OLX % h).read()
        except Exception:
            continue
        # PER TAG, NOT PER ADJACENT PAIR. This matched `cover="..."` only when
        # `slots="..."` was the very next attribute, which made it depend on the
        # ORDER the assembler happens to write. `requires=` landed between them
        # and the scan silently matched nothing from that day on: every caller
        # got `[]`, the cover exemption stopped applying, and the only reason
        # nothing failed is that the boxes it exempts do not currently overlap.
        # A helper that returns empty where the data exists is green by
        # construction -- the shape this file documents in three other places.
        for tag in re.findall(r"<LLMAction\b[^>]*>", src):
            cm = re.search(r'cover="([^"]*)"', tag)
            sm = re.search(r'slots="([^"]*)"', tag)
            if not cm or not sm:
                continue
            keys = {sl.split(":")[0].strip() for sl in sm.group(1).split("|")}
            if not boxes or not (boxes & keys) or len(boxes & keys) < 2:
                continue
            return [{b.strip() for b in g.split(":")[0].split(",") if b.strip()}
                    for g in cm.group(1).split("|")]
    return []


def check_consensus_spans_are_disjoint() -> list[str]:
    """Do Q6's eight fixture boxes hold text belonging to DIFFERENT elements?

    `check_handsplit_rows_are_disjoint` enforces exactly this invariant — and
    only over the hand-split JSON files, which is Q4b alone. Q6's fixture comes
    from a frozen consensus table built from per-component evidence quotes the
    scorer chose INDEPENDENTLY, so nothing has ever required those eight spans
    to partition the response: not to be ordered, not to be disjoint, not to be
    complete. The coverage check now covers completeness; this covers the rest.

    ONE overlap is permitted, and it is not merely tolerated -- it is a STRATEGY
    the fixtures rely on. `state_cN` names which consequence and `affect_cN` says
    what becomes of it, and where the student wrote one clause doing both jobs,
    putting that clause in BOTH boxes is what lets each be judged on it. Four
    cells do this: p4, p5, p15, p18, and in at least two the duplication is what
    earns a slot GOLD ALSO CREDITS, because gold charges a naming miss once and
    does not re-charge the effect (see the no-double-jeopardy note in
    handouts.CORRECTED_GOLD).

    Measured, on p4, 2026-08-19. Its `state_c2` held [[corpus Q6/p4 state_c1 0:39 sha=1fa67f2118a0]] and `affect_c2` the whole sentence that is a superset of it. Split
    faithfully -- the conjunction broken and the negation repeated on the second
    conjunct, so it reads as a negation and not an assertion -- `affect_c2` fell
    from `met` 9 of 9 to `incomplete` 7 of 9, and the cell lost 1.25 in every
    pass. Reframing the fragment as a full clause did not recover it. The box had
    been earning its credit on the phrase it shared with `state_c2`, not on its
    own words, so removing the redundancy made the fixture more faithful and less
    scoreable, and made our scoring stricter than gold's.

    So the exemption below is deliberate on two counts: the containment is usually
    faithful, AND removing it costs credit gold gives. What it hides is the pair
    being cut in the WRONG PLACE, which is a different defect and the one the
    blind-spot note further down is about. Splitting them was also measured as
    worse (Q6 fell 11/17 to 3/17 when an anchored split sliced those
    sentences into fragments). The same holds for `state_aN`/`change_aN`. Twenty
    such containments exist across fifteen cells and all are faithful.

    What is NOT permitted is one element's words appearing in another element's
    box: p10's `state_c2` is a substring of its `change_a1`, so one clause serves
    as both "how the first antecedent is changed" and "the second consequence" —
    and p10 carries `change_a1`'s only error in the item.

    KNOWN BLIND SPOT, and it is the permitted overlap that creates it. Because a
    containment between `state_cN` and `affect_cN` is exempt, this check cannot
    see the defect that actually recurs: the pair being cut in the WRONG PLACE.
    Three cells were repaired after this check passed them, all found by reading
    the eight boxes out one at a time against the submission --

      p14  `affect_c2` held a fragment lifted out of `change_a2`'s sentence
      p15  one sentence sat in BOTH `state_c1` and `affect_c1`
      p10  `state_a1` held a mid-sentence fragment; `change_a1` held two sentences

    -- and each had been read, before that, as evidence about the SCORER: p10 as
    a criterion gold decides inconsistently, p14 as a borderline flip. All three
    were the fixture. See the p10 note in `handouts.GOLD_CEILINGS`.

    A check for this would have to know where the clause boundary SHOULD fall,
    which is the judgement the split is making, so it is not obviously
    automatable and no attempt is recorded here. What is recorded is the cost of
    not having one: a defect in this class costs points, survives every check,
    and reads as a fact about gold or about the model. When a Q6 cell misbehaves,
    print its eight boxes and read them against the .docx before theorising.
    """
    # PORTED to `enforce/consensusSpansDisjoint.ts` (goal K).
    #
    # PYTHON KEEPS THE FETCH. `_fixture_cells` is memoised on the SEGMENTATION
    # only, deliberately, so the checks stay sensitive to a patched
    # `_fixture_boxes` -- which is exactly how the self-test injects a defect
    # here. A payload the runner rebuilt from the record would not see it.
    #
    # IT READS THE RECORD NOW, NOT THE CORPUS. `build_jobs` prefers the frozen
    # reconstruction, so these boxes come from
    # `instruments/<id>/derived/responses/` and no submission is opened.
    import forms as H
    import lo_enforce

    cells, items = [], set()
    for h, iid, pid, _raw, boxes in _fixture_cells():
        cells.append({"h": h, "item": iid, "pid": pid,
                      "boxes": {k: v for k, v in boxes.items() if v}})
        items.add((h, iid))

    exclusions = {}
    for h, iid in sorted(items):
        ex = H.cell_exclusions(h, iid)
        if ex:
            exclusions[f"{h}|{iid}"] = {str(p): list(v) for p, v in ex.items()}

    return lo_enforce.run("consensus_spans_are_disjoint", {
        "cells": cells,
        "exclusions": exclusions,
        "cover": {iid: [sorted(g) for g in _cover_groups(iid)]
                  for _h, iid in sorted(items)},
        "backlog": [[k[0], k[1], k[2], k[3], v]
                    for k, v in CONSENSUS_OVERLAP_BACKLOG.items()],
        "siblingRoles": [list(p) for p in OVERLAP_SIBLING_ROLES],
    })


# Cells whose fixture deliberately departs from the response's own structure.
# Keyed (item, pid, box) -> why. This check REPORTS mismatches; it does not
# decide them, because "which clause is this box" is sometimes a judgement about
# the answer and not a fact about its punctuation.
FIXTURE_STRUCTURE_OVERRIDES: dict[tuple[str, int, str], str] = {
    # Empty, and worth recording why all three entries went rather than being
    # renewed. Every one was the dangling-word test misfiring, not a fixture
    # departing from its response on purpose.
    #
    # Q6/p15 and Q3/p17 ended on `me` and `do` one character before the NEXT BOX
    # began. Nothing was severed; the box handed on. The check now sees that.
    #
    # Q6/p2 was the opposite — a real cut wearing an override. Its note claimed
    # extending `change_a1` would swallow "the next sentence, which no box
    # needs". It is not the next sentence: it is the rest of the SAME one, the
    # clause [[corpus Q6/p2 change_a1 173:222 sha=c8f08b0233f6]], which belonged
    # to no box at all. The box now runs to its own full stop.
}


def _response_parts(raw: str) -> list[int]:
    """Offsets where the response's numbered parts begin.

    Students mark the two halves of Q6 explicitly more often than not — "1)",
    "2)", sometimes with OCR damage ("o I am going to change ..."). Where no
    marker survives, the second antecedent statement opens the second part.
    """
    import re
    starts = [0]
    for m in re.finditer(r"(?<![\d.])\s*\b2\s*\)", raw):
        starts.append(m.start())
        break
    if len(starts) == 1:
        m = list(re.finditer(r"I (?:am going to|will) change my (?:antecedent|downfall|trigger)", raw))
        if len(m) > 1:
            starts.append(m[1].start())
    return starts


# Words a clause does not end on. A box finishing here was cut mid-clause: p5's
# `state_a1` ended "... I hope that I", its `state_c1` trailed off into [[corpus Q6/p5 affect_c1 0:27 sha=7e72ce8b5a47]], p4's `state_a2` stopped at [[corpus Q6/p4 state_a2 55:76 sha=9b1ec9750da6]] and its
# `state_c1` at "everywhere. o I". Function words only — a clause ending on a
# noun, verb or adjective is finished, whether or not a full stop follows.
_DANGLING = {
    "a", "an", "the", "my", "me", "i", "to", "of", "in", "on", "at", "and", "or",
    "but", "that", "which", "will", "would", "can", "could", "not", "is", "are",
    "was", "were", "be", "been", "for", "with", "from", "so", "then", "this",
    "it", "he", "she", "they", "we", "you", "have", "has", "had", "do", "does",
    "did", "if", "when", "while", "as", "by", "into", "than", "there", "their",
}


_SEGMENTS_MEMO = None


_BOXES_MEMO: dict = {}


def _fixture_cells():
    """(handout, item, pid, raw response, boxes) for every multi-box fixture.

    The structural checks were written against Q6 and hardcoded to it. Q6 turned
    out to have defects in twelve of its twenty cells, so "we have not looked at
    the others" is not a statement about their condition. This is the seam that
    lets all three look everywhere.

    ONLY the segmentation is memoised. Caching the boxes as well would make the
    checks blind to a patched `_fixture_boxes`, which is exactly how the selftest
    injects a defect — the probes would pass while testing nothing, the failure
    mode this project has already shipped twice.
    """
    global _SEGMENTS_MEMO
    import warnings
    import forms as H
    import segment as SEG

    if _SEGMENTS_MEMO is None:
        segs_by_cell = []
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for h in _forms():
                cfg = H.config(h)
                try:
                    subs = dict(H.find_submissions(h))
                except Exception:
                    continue
                for pid, path in sorted(subs.items()):
                    try:
                        segs = _segment_as_scored(h, pid)
                    except Exception:
                        continue
                    for item in cfg["rubric"].ITEMS:
                        raw = " ".join((segs.get(item["id"]) or "").split())
                        if len(raw) >= 40:
                            segs_by_cell.append((h, item["id"], pid, raw))
        _SEGMENTS_MEMO = segs_by_cell

    # THE BOXES ARE CACHED TOO NOW, but keyed on the `_fixture_boxes` FUNCTION
    # OBJECT, which is the evidence that they could have changed. The docstring
    # above is right that a plain cache would make these checks blind to a
    # patched `_fixture_boxes` -- that is how the self-test injects a defect, and
    # a probe passing while testing nothing is a failure this project has shipped
    # twice. Keying on the function means a patch MISSES the cache by
    # construction: setattr installs a different object, the key changes, and the
    # boxes are rebuilt against the patched version.
    #
    # Worth 20 of the audit's 29 seconds, because three checks each asked for
    # every cell and rebuilt the same boxes three times over.
    key = _fixture_boxes
    cached = _BOXES_MEMO.get(key)
    if cached is None:
        cached = {}
        for h, iid, pid, raw in _SEGMENTS_MEMO:
            boxes = _span_boxes(iid, pid)
            if len(boxes) >= 2:
                cached[(h, iid, pid)] = boxes
        _BOXES_MEMO.clear()          # one patched version at a time is enough
        _BOXES_MEMO[key] = cached
    return [(h, iid, pid, raw, cached[(h, iid, pid)])
            for h, iid, pid, raw in _SEGMENTS_MEMO if (h, iid, pid) in cached]


def _segment_as_scored(form: int, pid: int) -> dict[str, str]:
    """Segment one submission through the SCORER'S OWN entry point.

    `agreement_app.sections_for` is that entry point, and its docstring records
    this exact bug happening once already: the web scorer segmented without
    `repair_orphans` while the CLI segmented with it, so the two read DIFFERENT
    INPUT on H2 p19 and their comparison for that cell became meaningless rather
    than merely wrong.

    The audit then reintroduced it. It called `segment()` bare at four sites,
    dropping both `repair_orphans` (H2) and `join_aware` (H3), and so judged
    fixtures against text no scorer ever sees. Every accusation that followed
    was false: D2/p19 was reported as holding less than the response (the audit
    was looking at the unrepaired definition with the daily example still stuck
    to its end), and 1c/p11 and 1c/p20 were reported as DROPPING the template's
    own printed instruction — "Ensure the graph title, both axes' labels, and
    the legend ... are labeled appropriately" — which no student wrote.

    So this delegates rather than reimplementing. An audit that reads its
    subject through a different lens than the scorer is not measuring the
    scorer, and the only durable way to guarantee one lens is to have one.
    """
    import warnings

    import agreement_app as APP

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return APP.sections_for(form, pid)


def _siblings(box: str) -> str:
    """The box that may legitimately overlap this one: same element, other role.

    Q6 pairs `state_cN` with `affect_cN` and `state_aN` with `change_aN` — one
    clause answering "which consequence" and "what becomes of it". Items whose
    box names share no element suffix have no siblings, and every overlap counts.
    """
    head, _, tag = box.rpartition("_")
    if not head or not tag or tag == box:
        return ""
    return ("affect" if head == "state" else "state") + "_" + tag


def check_fixture_follows_response_structure() -> list[str]:
    """Do the boxes hold WHOLE clauses, laid out by the response's own structure?

    Lay a response out by its parts and then its clauses and the assignment is
    forced — which is how p4, p5 and p10 were each settled after two other
    checks had passed them. Those ask whether text went missing
    (check_fixture_covers_the_response) and whether two boxes share words
    (check_consensus_spans_are_disjoint). Neither can see a box holding a
    FRAGMENT, and that is what the consensus spans mostly got wrong.

    Sentence boundaries are the wrong test: `state_aN` and `change_aN` routinely
    split ONE sentence at "by ...", which is correct. So this looks for two
    things a clause-level layout rules out:

      * a box ENDING on a function word — cut mid-clause. p5's `state_a1` ended
        "... I hope that I"; p4's `state_a2` stopped at [[corpus Q6/p4 state_a2 55:76 sha=9b1ec9750da6]].
      * a box CROSSING a part boundary — p4's `state_c1` held [[corpus Q6/p4 affect_c1 90:128 sha=dae67124dfc9]], the tail of part one plus the opening of part two.

    A box contained in its same-element sibling is exempt from the first: a
    `state_cN` that is the opening of `affect_cN`'s sentence is the permitted
    overlap, and splitting those measured worse (11/17 -> 3/17).

    REPORTED, NOT DECIDED. Which clause a box should hold is sometimes a
    judgement about the answer — p4's part two has one consequence sentence
    serving as both `state_c2` and `affect_c2`, which is faithful because that is
    all the student wrote. Anything deliberate goes in
    FIXTURE_STRUCTURE_OVERRIDES with a reason, and a stale entry fails.
    """
    problems = []
    seen: set[tuple] = set()
    for _h, iid, pid, raw, boxes in _fixture_cells():
        parts = _response_parts(raw)
        low = raw.lower()
        located = {}
        for k, v in boxes.items():
            v = " ".join((v or "").split())
            if len(v) < 12:
                continue
            at = _locate(raw, v)
            if at >= 0:
                located[k] = (at, at + len(v), v)

        for k, (a, b, v) in sorted(located.items()):
            key = (iid, pid, k)
            note = []
            sib = located.get(_siblings(k))
            inside = sib and sib[0] <= a and b <= sib[1] + 2
            tail = v.rstrip()
            # A clause that closes with terminal punctuation is finished, whatever
            # its last word: "... by doing this.", "... about it.", "... get
            # exercise in." all end on a function word and all are complete.
            finished = tail.endswith((".", "!", "?"))
            # A boundary the NEXT box starts at is a deliberate hand-off, not a
            # severed clause: nothing is lost, and where the two should divide is
            # a question about the split, which the readout answers. Q6/p15's
            # `state_a2` ends one character before `change_a2` begins, and
            # Q3/p17's `realistic` one before `timebound` — both were carrying
            # hand-written overrides for a dangling `me` and `do` that only ever
            # meant "this box hands on here".
            handed_on = any(0 <= st - b <= 3 for st, _e, _t in located.values())
            last = tail.rstrip(".,;:").split()[-1].lower() if tail.split() else ""
            if not inside and not finished and not handed_on and last in _DANGLING:
                note.append(f"ends mid-clause on {last!r}")
            crossed = [p for p in parts[1:] if a < p < b]
            if crossed:
                note.append(f"crosses the part boundary at {crossed[0]}")
            if not note:
                continue
            if key in FIXTURE_STRUCTURE_OVERRIDES:
                seen.add(key)
                continue
            problems.append(
                f"{iid}/p{pid} `{k}` {' and '.join(note)}: {v[-58:]!r} — lay the "
                f"response out by parts then clauses and give the box a whole "
                f"clause, or declare it in FIXTURE_STRUCTURE_OVERRIDES")
    for stale in sorted(FIXTURE_STRUCTURE_OVERRIDES.keys() - seen):
        problems.append(
            f"FIXTURE_STRUCTURE_OVERRIDES lists {stale}, which no longer "
            f"mismatches. Remove it")
    return problems


# Cells where gold's wording and the fixture legitimately disagree, with why.
# Entries and their reasoning: `coursedata.gold_notes("FIXTURE_GOLD_OVERRIDES", key)` (6 lines).
FIXTURE_GOLD_OVERRIDES = _gold_declaration("FIXTURE_GOLD_OVERRIDES")


def check_consensus_fixes_are_unique() -> list[str]:
    """One declared span correction per box.

    `agreement_app.CONSENSUS_FIXES` applies its entries in order, so a second fix
    naming the same box silently overwrites the first. p9's corrected assignments
    were prepended to its existing trims and clobbered by them, and the tail
    recovery then dropped the orphaned sentence into `state_a2` — a box it has
    nothing to do with. build_jobs raises on this now, but that only fires when a
    fixture is built; this reports it without a run.

    There is no legitimate reason to state two different spans for one box.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K. `CONSENSUS_FIXES` is course
    # data; "one declared correction per box" is generic.
    # SELF-ASSEMBLED. E63: payload proven identical to python's -- after
    # python stopped sending the student spans the rule never reads.
    import lo_enforce

    # PYTHON KEEPS THE FETCH. Self-assembly re-reads CONSENSUS_SPANS.json from
    # disk; the self-test appends a second fix to the IN-MEMORY
    # `agreement_app.CONSENSUS_FIXES` and forks, so the case went silent.
    # Measured 2026-09-26. The verbs are already RESOLVED in this table, which
    # is why only `swap` keeps its shape -- everything else is a `set` on a box.
    import agreement_app as _APP_cf
    import lo_enforce

    return lo_enforce.run("consensus_fixes_are_unique", {"entries": sorted(
        [{"item": cell[0], "pid": cell[1],
          "fixes": [list(f) if f[0] == "swap" else ["set", f[1]] for f in fixes]}
         for cell, fixes in _APP_cf.CONSENSUS_FIXES.items()],
        key=lambda e: e["item"] + str(e["pid"]).zfill(3))})



def check_fixture_agrees_with_gold() -> list[str]:
    """Does the text in each box make sense in the light of gold's comment?

    The graders read the whole response, so their wording says whether an element
    was THERE. Two families of phrase, and they imply opposite things about the
    fixture:

      "did not state" / "missing" / "did not address"  -> nothing was written,
          so the box should be EMPTY. A box with text means we are asking the
          scorer to judge words the grader says do not exist.

      "is not the same as" / "does not match" / "a different"  -> something WAS
          written and it was the wrong item, so the box should NOT be empty. An
          empty box means we lost the words the grader marked down.

    This is the discriminator that settled p5: gold said its second consequence
    "does not match 4c" while both c2 boxes were empty, which is how a dropped
    200-character clause was finally identified after two checks had passed it.
    It is the one signal that reaches OUTSIDE the response — the other checks
    compare the fixture against the student's text, this one against the
    grader's reading of it.

    Heuristic and therefore overridable: gold's prose is written to a student,
    not to a checklist, and where two slots cover one element its wording does
    not always distinguish them. FIXTURE_GOLD_OVERRIDES carries the exceptions.
    """
    # PORTED to `enforce/fixtureAgreesWithGold.ts` (goal K).
    #
    # PYTHON KEEPS THE FETCH, because the self-test injects through
    # `_fixture_boxes` and `_fixture_cells` is memoised on the segmentation so
    # that a patch is still seen. It reads the RECORD now, not the corpus: the
    # boxes come from `derived/responses/` and the graders' comments from
    # `gold_rows.json`, so no workbook and no submission is opened on either
    # side.
    #
    # EMPTY BOXES ARE PASSED THROUGH. The whole question is whether a box is
    # empty or filled; dropping the empty ones makes a box unjudgeable rather
    # than empty, and costs every finding of one of the two kinds.
    import forms as H
    import lo_enforce

    cells, feedback = [], {}
    for h, iid, pid, _raw, boxes in _fixture_cells():
        cells.append({"h": h, "item": iid, "pid": pid, "boxes": dict(boxes)})
        fb = " ".join(((H.config(h)["gold"]().get(pid) or {}).get(iid) or {})
                      .get("feedback", "").split())
        if fb:
            feedback[f"{h}|{pid}|{iid}"] = fb

    box_words = {}
    for item, per_box in GOLD_BOX_WORDS.items():
        out = {}
        for box, words in per_box.items():
            if words and isinstance(words[0], tuple):
                out[box] = {"want": list(words[0]),
                            "forbid": list(words[1] if len(words) > 1 else ())}
            else:
                out[box] = {"want": list(words), "forbid": []}
        box_words[item] = out

    return lo_enforce.run("fixture_agrees_with_gold", {
        "cells": cells,
        "feedback": feedback,
        "boxWords": box_words,
        "overrides": {f"{k[0]}|{k[1]}|{k[2]}": v
                      for k, v in FIXTURE_GOLD_OVERRIDES.items()},
    })


def _form_of(item: str) -> int:
    """Which handout an item belongs to, read off the specs rather than guessed.

    It replaces `1 if item.startswith("Q") else 3`, which sent all twelve of
    handout 2's items — PR, NR, PP, NP, T1, D1, DAY1, WK1 and the rest — to
    handout 3, where they have no segment. `--fixture PR` therefore answered
    "empty response" for all twenty cells of an item whose fixture is fine, and
    nearly half the corpus could not be read out at all.
    """
    import agreement_app as APP
    import forms as H

    spec = APP.JOBS.get(item) or {}
    if spec.get("handout"):
        return int(spec["handout"])
    for h in _forms():
        try:
            if any(i["id"] == item for i in H.config(h)["rubric"].ITEMS):
                return h
        except Exception:
            continue
    return 1


def _boxes_only_readout(item: str, pid: int, boxes: dict) -> str:
    """The cell laid out for reading where there is no prose to read it against.

    1c is answered with a chart and 1b with a data table, so 18 of 1c's 20 cells
    have an empty prose segment. This used to print one line — "empty response"
    — and stop, which meant the procedure QUALITY_CONTROL.md section 1 calls
    irreplaceable silently did nothing on exactly the items whose boxes no other
    check can read. What it was hiding sat in ten cells of a counted item: 1c's
    `title`, `x` and `y` held the paper scorer's SENTENCE about the label rather
    than the label, and the web grader was being handed its own answer.

    Nothing can be located here, so PROVENANCE replaces position — which spec
    key filled each box, and therefore what to read it against. A parsed value
    is checked against the table or the chart; a `from_scorer` value against
    what the scorer was looking at. Read it as: is this the student's value, or
    is it the scorer's account of their value?
    """
    prov = _box_provenance(item, pid)
    filled = {k: " ".join((v or "").split()) for k, v in boxes.items()}
    if not any(filled.values()):
        return (f"{item}/p{pid}: empty cell — no prose response and no filled "
                f"box ({len(boxes)} box(es) declared)")

    out = [f"{'=' * 78}", f"{item} / p{pid}", "=" * 78, "",
           "NO PROSE RESPONSE. This item is not answered in prose, so there is",
           "nothing to locate a box in. Read each box against the source its",
           "provenance names.", "", "-" * 78, "", "BOXES, by provenance:", ""]
    values = _value_derived(item)
    for k in sorted(filled, key=lambda k: (prov.get(k, ""), k)):
        v = filled[k]
        why = prov.get(k, "field")
        if k in values:
            why += "; a parsed value, not a quotation"
        out.append(f"  [{k}] {why}")
        out.append(f"     {v if v else '(EMPTY)'}")
        out.append("")
    out += ["-" * 78, ""]
    return "\n".join(out + [_readout_flags(pid)])


def _readout_flags(pid: int) -> str:
    """The audit flags for one participant, as the readout prints them."""
    import warnings

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        flags = [f for f in (check_fixture_follows_response_structure()
                             + check_consensus_spans_are_disjoint()
                             + check_fixture_covers_the_response())
                 if f"/p{pid}:" in f or f"/p{pid} " in f]
    lines = ["AUDIT FLAGS: " + (f"{len(flags)}" if flags else "none")]
    lines += [f"  - {f.split(' — ')[0]}" for f in flags]
    return "\n".join(lines)


def fixture_readout(item: str, pid: int) -> str:
    """The cell laid out for reading: response, then every box, in order.

    The three fixture checks each answer one question — did text go missing, do
    two boxes share it, is any box cut mid-clause — and every one of them passed
    on defects that reading the cell out loud found in a minute. p18's boxes all
    ended on clean clause boundaries and two of them held clauses from the WRONG
    HALF of the response, with part two's own consequence sentence belonging to
    nothing. p5's `state_a1` ran 289 characters and its `state_c1` began
    mid-sentence. p10's `state_c2` still holds a slice of `change_a1`.

    So this is the procedure itself, not another check: print the response with
    its parts and sentences, then the boxes with their positions, and let a
    person see whether the mapping respects what the student wrote. Three of the
    four cells that needed a structural rewrite were found this way and by
    nothing else.

    Read it as: does each box hold ONE whole clause, do the boxes run in
    document order, and does each half of the response fill its own boxes?

    Two bugs kept it from reaching 237 of the 520 cells, both fixed and both
    silent — it answered "empty response" and a reader concluded there was
    nothing to see.

      * The handout was GUESSED from the item name, `1 if item.startswith("Q")
        else 3`, which sent all twelve of handout 2's items to handout 3 where
        they have no segment. 220 cells, every one of them a fixture nobody
        could read out. `_form_of` reads the spec instead.
      * A cell answered with a CHART or a TABLE has no prose to locate a box in,
        which is normal for 1c and 1b rather than a dead end. Those go to
        `_boxes_only_readout`, which prints the boxes by provenance. The defect
        that was hiding behind the old one line sat in ten cells of a counted
        item — 1c's `title`/`x`/`y` holding the scorer's sentence about the
        label instead of the label.

    "Empty response" now means only what it says: no prose AND no filled box.
    """
    import re
    import forms as H

    h = _form_of(item)
    try:
        subs = dict(H.find_submissions(h))
    except Exception:
        subs = {}
    if pid not in subs:
        return f"p{pid}: no submission on this machine"
    raw = " ".join(_segment_as_scored(h, pid).get(item, "").split())
    boxes = _fixture_boxes(item, pid) or {}
    if not raw:
        # No prose is the NORMAL case for a chart or table item, not a dead end.
        return _boxes_only_readout(item, pid, boxes)

    out = [f"{'=' * 78}", f"{item} / p{pid}", "=" * 78, "", "RESPONSE:", ""]
    parts = re.split(r"(?=\b2\s*\))", raw)
    for i, part in enumerate(parts, 1):
        if len(parts) > 1:
            out.append(f"  PART {i}")
        for sent in [x.strip() for x in re.split(r"(?<=[.!?])\s+", part) if x.strip()]:
            out.append(f"    @{raw.find(sent):<4} {sent}")
    out += ["", "-" * 78, "", "BOXES, in document order:", ""]

    placed, unplaced = [], []
    for k, v in boxes.items():
        v = " ".join((v or "").split())
        if not v:
            unplaced.append((k, "(empty)"))
            continue
        at = _locate(raw, v)
        (placed if at >= 0 else unplaced).append((at, k, v) if at >= 0 else (k, v))
    for at, k, v in sorted(placed):
        out.append(f"  [{k}] @{at}")
        out.append(f"     {v}")
        out.append("")
    values = _value_derived(item)
    for k, v in unplaced:
        why = ("(a parsed value, not a quotation)" if k in values
               else "(not located in the response)")
        out.append(f"  [{k}] {why}")
        out.append(f"     {v}")
        out.append("")

    cov = [False] * len(raw)
    for at, _k, v in placed:
        for i in range(at, min(at + len(v), len(raw))):
            cov[i] = True
    gaps, i = [], 0
    while i < len(raw):
        if not cov[i]:
            j = i
            while j < len(raw) and not cov[j]:
                j += 1
            if raw[i:j].strip():
                gaps.append(f"@{i}-{j} {raw[i:j].strip()!r}")
            i = j
        else:
            i += 1
    out += ["-" * 78, "",
            "ASSIGNED TO NO BOX: " + ("; ".join(gaps) if gaps else "nothing"), ""]

    return "\n".join(out + [_readout_flags(pid)])


def check_reporters_execute() -> list[str]:
    """Do the harnesses' report paths actually RUN?

    Twice now a name has been used in `report()` that was never bound, and twice
    it survived every check in this project: `py_compile` sees valid syntax, the
    audits import the module without calling it, and a measurement only reaches
    the failing line after the last cell has been scored. The first cost a
    finished 26-item web sweep; the second shipped in a commit and crashed the
    CLI at the end of a full three-run Q6 measurement.

    So this executes them, on synthetic rows, with output swallowed. It proves
    nothing about the numbers — the audits above do that — only that the code
    path runs at all, which is exactly what nothing else here checks.
    """
    import contextlib
    import io

    problems = []
    rows = [{"participant_id": 1, "item": "Q6", "score": 8.75, "max": 10.0,
             "failed_slots": 1, "checks": {}},
            {"participant_id": 9, "item": "Q6", "score": 3.75, "max": 10.0,
             "failed_slots": 5, "checks": {}}]
    gold = {1: {"Q6": {"score": 8.75, "feedback": ""}},
            9: {"Q6": {"score": 5.0, "feedback": ""}}}
    try:
        import agreement as A
        with contextlib.redirect_stdout(io.StringIO()):
            A.report(1, rows, [], gold)
    except Exception as e:
        problems.append(
            f"agreement.report() raised {type(e).__name__}: {e}. A measurement "
            f"reaches this only after every cell is scored, so the run is lost")
    try:
        import agreement as A2
        with contextlib.redirect_stdout(io.StringIO()):
            A2._print_not_counted([("unscoreable", "Q6", 9, 5.0, 3.75),
                                   ("self_graded", "Q6", 2, 8.75, 8.75)])
    except Exception as e:
        problems.append(
            f"agreement._print_not_counted() raised {type(e).__name__}: {e}")
    return problems


def check_exclusion_claims_are_data() -> list[str]:
    """Does any exclusion rationale assert a point figure only in prose?

    An `unscoreable` reason is an argument that no correct scorer can reach the
    gold, and those arguments are quantitative — they say how far off the cell
    lands and why. A number written into the sentence is checked by nobody, and
    Q6's p9 proved what that costs: it read "the CLI's error here is exactly
    -2.50" through every run that measured -1.25, and because the sentence
    blamed the fixture reconstruction, the actual cause — a declared A_MISMATCH
    divergence, the one slot of eight where the scorer disagrees with gold — sat
    unstated in an exclusion whose whole job was to state it.

    So a reason that names a point figure must also declare `expect_error`,
    which the harnesses assert against the measurement on every run. Prose may
    still explain the number; it may not be the only place it lives.
    """
    # PORTED AND SELF-ASSEMBLED (goal K, step 8). Generic: a claim about a
    # NUMBER left in prose goes stale without anything noticing. Payload proven
    # identical and findings identical on a firing control (every expect_error
    # stripped).
    import lo_enforce

    # PYTHON KEEPS THE FETCH. Self-assembly reads this from DISK; the
    # self-test injects into the IN-MEMORY table and forks, so a rebuilt
    # payload cannot see it and the case goes silent. Measured 2026-09-26.
    import forms as _H_excl
    import lo_enforce

    return lo_enforce.run("exclusion_claims_are_data", {"cells": [
        {"item": item, "pid": int(pid),
         "why": str(e.get("why", "") if isinstance(e, dict) else e),
         "declared": bool(isinstance(e, dict)
                          and e.get("expect_error") is not None)}
        for item, per in _H_excl.PER_ITEM_EXCLUDE.items()
        for pid, e in (per or {}).items()]})


def _rubric_vocab(item: dict, c: dict) -> set[str]:
    """Every verdict the PAPER prompt offers for `c`, from all THREE homes.

    Kept in step with score._fail_verdict: a vocabulary can be declared on the
    credit entry, on the `cover` group a slot belongs to, or — the common case on
    Q6, where no credit entry declares `verdicts` at all — only by the `codes`
    map, whose keys name the failures the slot can report.
    """
    if c.get("verdicts"):
        return set(c["verdicts"])
    for grp in item.get("cover", []) or []:
        if c["what"] in grp["keys"]:
            return set(grp.get("verdicts") or []) | set(grp.get("labels") or [])
    return {"met", "absent"} | set(c.get("codes") or {})


def check_unreachable_gold_is_allowed() -> list[str]:
    """Do all three harnesses forgive a gold score the item cannot produce?

    An item's score is max minus a subset of its component costs, so it can only
    land on certain values. Where a gold row names a value outside that set, the
    nearest reachable one is the best any correct scorer can do, and counting it
    wrong measures the rubric's arithmetic rather than the scorer's judgement.
    Q6 p4 asks for 6.00 from an item that moves in steps of 1.25.

    Every harness that reports an exact-match rate must apply the same
    allowance, or their rates stop being comparable — the same failure the
    exclusion checks exist for, and the same fix: one helper, called by all.
    """
    import os
    import forms as H

    problems = []
    for fname in ("agreement.py", "agreement_app.py", "baseline.py"):
        try:
            src = _harness_source(fname)          # by import; see its docstring
        except Exception as e:
            problems.append(f"cannot read {fname}: {e}")
            continue
        if "scores_as_exact" not in src and "scored_exactly" not in src:
            problems.append(
                f"{fname} reports an exact-match rate without calling "
                f"handouts.scores_as_exact(), so it penalises a scorer for missing "
                f"a score the item cannot produce")
        # Presence is NOT use. This check passed for a long time while
        # agreement.py called the helper in its per-item row and re-derived
        # exactness as a raw comparison in the ALL aggregate, in the not-counted
        # block, and in the MEDIAN-RUN SELECTOR — so the run chosen for
        # publication was picked by one rule and printed under another, and a
        # single table showed 67% and 58% for the same twelve cells. What the
        # audit can see statically is the anti-pattern: a float equality against
        # gold, which is the shape every one of those four sites had.
        for m in re.finditer(r"abs\(\s*([^)]*?)\s*\)\s*[<>]=?\s*1e-9", src):
            expr = m.group(1)
            # Either shape counts: a difference taken inline (`p - g`) or an
            # error already in a variable (`e`), which is what the ALL aggregate
            # used. A tolerance test reads `<= tol + 1e-9` and does not match,
            # because the bound here must be 1e-9 exactly.
            if not re.search(r"\bg\b|gold|pred|\be\b|err|delta", expr):
                continue          # not an exactness test
            line = src[: m.start()].count("\n") + 1
            problems.append(
                f"{fname}:{line} decides exactness as `abs({expr}) < 1e-9`. That "
                f"is the raw-equality rule, which penalises a gold the item "
                f"cannot produce. Route it through handouts.scored_exactly()")

    # And the helper must stay an allowance for UNREACHABLE gold only. If it ever
    # forgives a near miss on a reachable one it becomes a tolerance, and every
    # rate in the project silently loosens.
    for h in _forms():
        for item in H.config(h)["rubric"].ITEMS:
            scores = H.attainable_scores(item)
            if len(scores) < 2:
                continue
            a, b = scores[0], scores[1]
            if H.scores_as_exact(item, a, b):
                problems.append(
                    f"H{h} {item['id']}: scores_as_exact() accepts {b:g} against a "
                    f"REACHABLE gold of {a:g} — it has become a tolerance")
    return problems


def check_gold_corrections_land_on_attainable_scores() -> list[str]:
    """Every CORRECTED_GOLD entry sets a score the item can actually produce.

    An item's score is its max minus a subset of its component costs, so only
    certain values exist. `check_unreachable_gold_is_allowed` covers the OTHER
    side of that fact -- a harness must FORGIVE a gold the item cannot produce --
    and nothing covered this one. A correction is the one place we choose a gold
    number ourselves, and choosing an unreachable one writes a score no scorer
    can ever match while reading as a fix.

    Three of the entries exist BECAUSE gold was off-grid: 1c/p11 at 7.00,
    Q4a/p17 at 4.00, and Q6/p4 at 6.00 on an item that moves in steps of 1.25.
    Landing the correction back on the grid is the point of those three, so the
    rule they are held to is the rule they were written to satisfy.

    The costs come from the RUBRIC, so this names no item and fires on every
    entry written later. That is the whole reason it replaces a Q6-shaped check:
    an item-specific one never fires for content written after it.
    """
    # PORTED AND SELF-ASSEMBLED (goal K, step 8). The attainable grid is
    # computed from the item's own points on both sides. Payload proven
    # identical and findings identical on an off-grid control.
    import lo_enforce

    return lo_enforce.run("gold_corrections_land_on_attainable_scores", None)


def check_gold_scores_are_attainable() -> list[str]:
    """After corrections, every gold cell lands on a score its item can produce.

    The REPORTING half of `check_unreachable_gold_is_allowed`. That check makes
    the three harnesses forgive an off-grid gold so their rates stay comparable;
    forgiveness with nothing reporting it means the next one is absorbed in
    silence and never looked at -- which is the same failure as a check nobody
    calls, arriving by a different route. The allowance was built for one known
    cell; it does not know how to say when it has acquired a second.

    Measured when this was written: 519 gold cells carry a score and 0 are
    off-grid, because the three that were are the three corrections above. So
    this is a ratchet at zero, not a backlog -- it fires on new content only.

    Reads the rubric's costs and gold's numbers, and nothing else.
    """
    # Course data the engine can read for itself.
    import lo_enforce

    return lo_enforce.run("gold_scores_are_attainable", None)


def check_response_boxes_are_bounded() -> list[str]:
    """Are the student's boxes DELIMITED in the prompt the grader is sent?

    SPLIT OUT OF `check_empty_fields_are_absent` (goal K). That check asked two
    questions on two sides: whether the generated PROMPT bounds the boxes, and
    whether python's `_normalize_empty_fields` still corrects an empty one. The
    first is about the web prompt and belongs with the engine that assembles
    it; the second exercises a python function with no counterpart there. The
    user's rule -- something that touches both should be split -- is why they
    are now two checks rather than one that could only ever half-move.

    AN EMPTY BOX'S `<Ref>` RENDERS TO NOTHING, and for the LAST box on an item
    there was no following heading to bound it -- so the guidance the app
    appends after our prompt fell where the box's contents belong, and was
    quoted to the student as their own words. Two instruction-level fixes were
    measured and neither moved the rate; the bounds are what fixed it, so the
    bounds are what this checks. Every item on every handout, because the last
    box of any item is the one exposed.
    """
    # PORTED to `enforce/responseBoxesBounded.ts`. Python passes the prompts it
    # builds; the self-test substitutes `build_web_prompt`, and a payload the
    # runner assembled from the staged inputs would not see the substitution.
    import lo_enforce

    try:
        import olx_prompts as OLX
        items = sorted(OLX.RESPONSE)      # every item that shows the student's boxes
    except Exception as exc:
        return [f"could not enumerate the generated prompts: {exc}"]
    prompts = {}
    for item_id in items:
        try:
            prompt = OLX.build_web_prompt(item_id)
        except Exception:
            continue
        if "## Student response to grade" in prompt:
            prompts[item_id] = prompt
    return lo_enforce.run("response_boxes_are_bounded", {"prompts": prompts})


def check_empty_fields_are_absent() -> list[str]:
    """An empty input field must be `absent`, with nothing quoted against it.

    `incomplete` is a verdict about text that is present and falls short. Handed
    an EMPTY field it is not a harsh judgement, it is an impossible one, and it
    has a specific cost: `incomplete` obliges the grader to quote the text that
    falls short, so when there is none it quotes whatever is nearest. On the
    3-pass Q6 sweep of 2026-08-18 that was the string "WRITING TO THE STUDENT",
    a heading out of the prompt itself, reproduced to the student as their own
    words six times across five cells.

    Nothing caught it, and nothing could have: the two verdicts score
    identically, so the leak never moved a number. It was found by reading a
    record, which is the same way the p14, p15 and p10 fixture defects were
    found. `agreement_app._normalize_empty_fields` now corrects it on the way in
    and rule 1 of the shared prompt preamble forbids it at the source; this
    checks that both halves are still there and still work, because a guard that
    reads the wrong key is indistinguishable from no guard -- the first cut of
    this one read `job["values"]` where the jobs carry `job["fixture"]`, silently
    corrected nothing, and passed.
    """
    # THE SETUP THE SPLIT TOOK WITH IT. `out` and the `agreement_app` import
    # opened the original function, ahead of the structural half that moved --
    # so cutting at the section marker removed the retained half's own
    # prologue. The parse survived it; a NameError at call time did not.
    out: list[str] = []
    try:
        import agreement_app as APP
    except Exception as exc:
        return [f"could not import the scorer modules to check the guard: {exc}"]

    # 2. the guard half, exercised rather than merely imported
    probe = {"cell": "p0/Q6",
             "verdicts": {"slot_a": "incomplete", "slot_b": "met", "slot_c": "absent"},
             "evidence": {"slot_a": "WRITING TO THE STUDENT", "slot_b": "real text"}}
    job = {"cell": "p0/Q6",
           "fixture": {"x_slot_a": "", "x_slot_b": "real text", "x_slot_c": ""}}
    try:
        got = APP._normalize_empty_fields(probe, job)
    except Exception as exc:
        return out + [f"_normalize_empty_fields raised on a synthetic record: {exc}"]
    if got["verdicts"]["slot_a"] != "absent":
        out.append("_normalize_empty_fields left `incomplete` on an EMPTY field "
                   f"(got {got['verdicts']['slot_a']!r}) -- check it reads the same key "
                   "the jobs are built with (`fixture`, not `values`)")
    if (got.get("evidence") or {}).get("slot_a"):
        out.append("_normalize_empty_fields corrected the verdict but kept the "
                   "quotation that cannot exist -- drop the evidence too")
    if got["verdicts"]["slot_b"] != "met":
        out.append("_normalize_empty_fields overwrote a verdict on a FILLED field -- "
                   "it must only touch fields that are empty")
    return out


def check_the_cli_sends_the_apps_prompt() -> list[str]:
    """Does the CLI path send the same prompt the app sends, bar mapped vocabulary?

    The two paths are built to share their text rather than to resemble it. Both
    read the SAME OLX action body -- same file, same action id -- so the body
    cannot drift. Then each appends the slot-sheet guidance, and that is the one
    seam: the app composes it in `slotSheetGuidance`, and `agreement`'s Python
    mirror lifts each block's literal text out of slotSheet.ts rather than keeping
    a copy, because a copy is the thing that drifts (three times, per the mirror's
    own docstring, each found by chasing a score).

    Lifting the blocks is not the whole job, though, and this is the gap it leaves.
    `checklist_guidance` HARDCODES which blocks it composes and in what order --
    studentFacingGuidance, then checklistGuidance or terseFeedbackGuidance. If the
    app grows a third block, or reorders, or renames, every individual lift still
    succeeds and the composed prompts silently differ. Nothing was checking that,
    so this compares the composition itself, read out of the app's source.

    What it does NOT do, and why: it does not diff the composed prompts token by
    token. The web's prompt is served from a dump and the CLI's is assembled in
    Python, and the only sanctioned difference between them is the cover
    vocabulary -- `neither` for `refers_to: none`, `absent` for `verdict: absent`
    -- which `COVER VOCAB DIFFERS` in equivalence.py already polices per slot with
    that mapping written into it. Duplicating that here would put the same bridge
    in two places, which is how a bridge stops being one.
    """
    out: list[str] = []
    import re as _re
    try:
        import paths as _paths
        ts = open(_paths.SLOTSHEET_TS).read()
    except Exception as exc:
        return [f"could not read slotSheet.ts to compare the prompt paths: {exc}"]

    m = _re.search(r"export function slotSheetGuidance\b[^{]*\{(.*?)\n\}", ts, _re.S)
    if not m:
        return ["slotSheetGuidance() not found in slotSheet.ts -- the CLI mirrors a "
                "composition that no longer exists, so the two paths cannot be compared"]
    body = m.group(1)
    called = _re.findall(r"\b([a-z][A-Za-z]*Guidance)\s*\(", body)
    # What agreement.checklist_guidance composes, in its own order.
    expected = ["studentFacingGuidance", "checklistGuidance", "terseFeedbackGuidance"]
    if called != expected:
        out.append(
            "slotSheetGuidance() now composes "
            f"{called} but agreement.checklist_guidance composes {expected}. Every "
            "individual block still lifts cleanly, so the prompts differ silently: "
            "fix the mirror in agreement.checklist_guidance to match this order")
    # And each block must still be liftable, in BOTH branches.
    try:
        import agreement as _AG
        for show in (True, False):
            txt = _AG.checklist_guidance(show)
            if len(txt.strip()) < 200:
                out.append(f"checklist_guidance(show_checks={show}) lifted only "
                           f"{len(txt.strip())} chars -- a block matched empty, so the "
                           "CLI is sending less guidance than the app")
    except SystemExit as exc:
        out.append(f"a guidance block no longer lifts out of slotSheet.ts: {exc}")
    except Exception as exc:
        out.append(f"could not compose the CLI guidance: {exc}")
    return out


# ---------------------------------------------------------------------------
# E32. Does a registered verifier actually READ its table?
#
# check_every_declaration_table_has_a_verifier confirms that a NAMED verifier
# exists and that the table exists. It cannot see whether the verifier consults
# the table, so a declaration can be registered, pass that check, and still be
# inert -- the "reads as coverage and enforces nothing" failure the registry was
# built to prevent, one level up. RAW_GOLD_READERS was found that way.
#
# GREPPING DOES NOT WORK, tried and rejected. Matching the table's name in the
# verifier's source gives false NEGATIVES where the name appears only inside an
# error string -- exactly how RAW_GOLD_READERS looked checked -- and false
# POSITIVES where the verifier legitimately delegates to another module that does
# read it. On this tree a grep flagged 5 of 22 tables and every one was a
# delegation; the one genuinely inert table was not among them.
#
# So the table is MOVED and the verifier re-run. If emptying it and corrupting it
# both leave the output unchanged, nothing is reading it. Delegation is handled
# correctly, because a delegated read still changes the output.
#
# NOT IN THE DEFAULT AUDIT. Three runs of every verifier over twenty-two tables
# is minutes, not seconds, and the pre-commit path has to stay usable. Run it with
# `python3 enforcement.py --probe-declarations`, beside the self-test.
def _empty_like(obj):
    """An empty container of the same kind, for the tables that cannot mutate."""
    if isinstance(obj, dict):
        return {}
    if isinstance(obj, list):
        return []
    if isinstance(obj, tuple):
        return ()
    if isinstance(obj, (set, frozenset)):
        return type(obj)()
    return None


def _bogus_key(sample):
    """A key of the same SHAPE as an existing one, naming nothing real.

    Shape matters: the cell tables key on ("Q6", 5) and the module tables on a
    string, and a probe that fed the wrong shape would raise inside the verifier
    and be recorded as "cannot probe" -- a false pass for the table.
    """
    if isinstance(sample, tuple):
        return tuple(_bogus_key(x) for x in sample)
    if isinstance(sample, str):
        return "zz_not_a_real_declaration"
    if isinstance(sample, bool):
        return not sample
    if isinstance(sample, int):
        return -987654
    if isinstance(sample, float):
        return -987654.0
    return None


# E32, the per-table half. A nonsense KEY is not enough to prove a table is read:
# a verifier that only objects to a WELL-FORMED but WRONG entry will ignore
# garbage and look inert. So each table declares a provocation -- an entry the
# verifier MUST object to -- and the probe adds that instead of guessing a shape.
#
# This also makes an EMPTY table probeable, which emptying never could.
#
# Two entries below are NOT provocations but recorded limitations, and they are
# the reason this work was worth doing rather than forcing every row green.
PROBE_PROVOCATIONS: dict[str, object] = {
    # A data-module exemption naming a file that does not exist: the verifier
    # objects that an exemption for an absent file exempts nothing. Declared
    # after `--probe-declarations` reported DATA_MODULES INERT -- emptying it
    # changed nothing, because the budget records those modules' counts anyway,
    # so the exemption had nothing to prove by its absence. It is proved by its
    # CONTENTS instead.
    # A (key, value) TUPLE, because the table is a dict -- the same shape
    # `handouts.GOLD_CEILINGS` uses. A bare dict raised `not enough values to
    # unpack` inside the probe: the format is per-table-type and is not guessable
    # from the neighbouring list-valued entries.
    # A re-entry naming a module the scan never reports: the verifier objects
    # that the entry describes nothing. Emptying the table is invisible -- no
    # re-entry means nothing to be wrong about -- so it is proved by its
    # CONTENTS, exactly as DATA_MODULES is.
    # HAND_AUTHORED_ATTRS IS EMPTY NOW -- its four entries were stale and were
    # removed -- so the probe's usual lever, emptying it, does nothing. The
    # provocation is an entry that excuses an attribute the RUBRIC ALREADY
    # BACKS, which is exactly what the four removed entries had become and what
    # `check_hand_authored_attrs_still_suppress_something` objects to.
    # A family of two items that are NOT siblings: `3` and `Q5` both carry
    # `example_1` and weight it differently (advisory @3 against advisory @2.5),
    # so declaring them one family makes the check object that a shared slot
    # name does not mean one thing. Found by trying every pair rather than by
    # guessing -- the first guess, (Q1, 1a), shares no slot at all, so the check
    # had nothing to compare and stayed silent, which reads exactly like a table
    # nobody reads.
    "enforcement.SLOT_STRUCTURE_FAMILIES": ("probe-family", ("3", "Q5")),
    "enforcement.HAND_AUTHORED_ATTRS": (("NR", "expect"),
                                        "probe: excuses an attribute the rubric "
                                        "backs"),
    # A builder that does not exist: the verifier objects that the permission
    # names no file. Emptying the table is ALSO visible -- every builder then
    # counts as a consumer and the budget is exceeded -- so this one is proved
    # from both directions.
    # A fixture naming an item this course does not have: the verifier objects
    # that the case injects into nothing. Emptying the table is visible too --
    # nine declarations disappearing is nine named fixtures with no stated
    # reason -- so it is proved from both directions.
    "enforcement.SELFTEST_NAMED_FIXTURES": (("probe: a fixture", "NO_SUCH_ITEM"),
                                            "probe: names an item that is gone"),
    "enforcement.RUBRIC_BUILDERS": ("probe_no_such_builder.py",
                                    "probe: a builder that does not exist"),
    "enforcement.COURSE_DATA_REENTRY": ("probe_no_such_module.py",
                                        (1, "probe: a re-entry for a file that "
                                            "does not exist")),
    "enforcement.DATA_MODULES": ("probe_no_such_module.py",
                                 "probe: declared a data module, does not exist"),
    # THE TWO NEUTRALITY TABLES, both empty and both reported CANNOT PROBE for
    # want of a provocation. Emptiness is why they need one: a table with no
    # entries cannot be emptied, so the probe's usual lever does nothing and the
    # check behind it has never been shown to fire at all.
    #
    # A neutrality entry CLAIMS that scoring did not move between two
    # fingerprints, and its verifier re-scores every cell the pair covers. A
    # pair of shas no recorded item sits at is therefore a claim about nothing,
    # which is exactly the objection the tables' own comments say it produces:
    # the entry reads as SPENT the moment it is written. Measured 2026-09-14 by
    # trying it, and that observation is what makes it a usable provocation
    # rather than a guess.
    "measured.SCORER_NEUTRAL": (("probe_sha_before", "probe_sha_after"),
                                "probe: a neutrality claim for a pair no "
                                "recorded item sits at"),
    "measured.WEB_CODE_NEUTRAL": (("probe_sha_before", "probe_sha_after"),
                                  "probe: a neutrality claim for a pair no "
                                  "recorded item sits at"),
    # A ceiling on an item recorded PERFECT: 1b is 20/20 on both sides, so
    # "cannot be perfect" is contradicted the moment it is claimed.
    "forms.GOLD_CEILINGS": (("1", "1b"),
                               ("probe: 1b cannot be perfect", "probe")),
    # A divergence naming a cell we get right in every run.
    "forms.GOLD_DIVERGENCES": {"code": "PROBE_ONLY", "cells": [("1b", 1)],
                                  "why": "probe: 1b/p1 is right every run"},
    # A divergence claiming the web COMPUTES a check it does not: the arithmetic
    # verifier reads web_computes and must object.
    # The arithmetic verifier parses a claim of the form "sum to N ... max of M"
    # out of `what` + `why` and recomputes it. A provocation therefore has to
    # STATE a false claim in that form -- an entry asserting no arithmetic gives
    # the check nothing to contradict, which is how the first attempt at this
    # provocation looked like an unread table.
    "olx_prompts.SCORING_DIVERGENCES": {
        "what": "probe: the slot points sum to 999 against a max of 998",
        # Q6 and not 1b: `_maxes` returns None for a SHEET_ONLY item with no
        # LLMAction grader, and the check then skips the entry -- so a provocation
        # aimed at 1b was silently unexaminable rather than false.
        "items": ["Q6"], "necessary": False,
        "enforcement": "probe", "why": "probe"},
    # A primitive named unexercised while it is bound to a live item.
    "enforcement.UNEXERCISED_PRIMITIVES": ("cover", "probe: cover is bound to Q6"),
    "enforcement.HANDCODED_ITEM_RULES": ("probe_item", "probe: not a real rule"),
    # PROBE_IMPOSSIBLE is EMPTY as of 2026-08-31 -- E31 and E33 fixed the two
    # checks whose tables could not be provoked, so both entries were retired and
    # every declaration table is now probeable. An empty table cannot be moved by
    # emptying, so it needs a provocation of its own: adding an entry makes the
    # named table report BY DESIGN instead of READ, which changes the output.
    "enforcement.PROBE_IMPOSSIBLE": ("forms.CORRECTED_GOLD",
                                     "probe: not a real impossibility"),

    # RAW_GOLD_READERS became probeable on 2026-08-31 when E31 drove its
    # verifier's loop from the table. A bogus module name is now objected to, so
    # the default shape-derived provocation suffices and no entry is needed here.
    # An exclusion on a cell that HAS gold and is absent from the last recorded
    # run's excluded cells: E33 made the verifier read the table, so this now
    # fires as "no evidence either way". A shape-derived bogus key would NOT --
    # the loop iterates real items, so a nonsense item name is skipped.
    "forms.PER_ITEM_EXCLUDE": ("1b", {1: "probe: not a real exclusion"}),
    # Removing a declared bounded finding makes it report again; adding a cell
    # that agrees does nothing, so the provocation has to be a DELETION -- which
    # emptying already tests. A bogus key is enough here because the check reports
    # any key naming a cell it cannot bound.
    "measured.GOLD_SLOT_BOUNDS_KNOWN": (("zz", 999), "probe"),
    "measured.GOLD_CODE_KNOWN": (("zz", 999), "probe"),
}

# Why a table has no provocation. An entry here is a claim that the table CANNOT
# be probed behaviourally, which is stronger than "the probe could not tell", so
# it carries its reason and is reported as UNPROBEABLE BY DESIGN rather than
# quietly passing.
PROBE_IMPOSSIBLE: dict[str, str] = {
    # enforcement.RAW_GOLD_READERS was here until 2026-08-31. Its reason -- "its
    # verifier NEVER reads it" -- was true and is now false: E31 rewrote
    # check_gold_accounting_is_uniform to drive its loop from the table and to
    # verify each entry, which is what made the stale function name visible.
    # A PROBE_IMPOSSIBLE reason that stops being true is exactly the staleness
    # this table has to be able to lose, so the entry goes rather than being
    # softened.
    # handouts.PER_ITEM_EXCLUDE was here until 2026-08-31. Its reason -- that the
    # staleness verifier reads the ledger snapshot and not the table -- was true
    # and is now false: E33 made it read both. The entry goes rather than being
    # reworded, which is the whole point of this table being able to lose one.
}


_SELF_MODULE = "enforcement"


_PROBE_RUNNING = False


def probe_declaration_tables() -> list[str]:
    """Which registered declarations enforce nothing, tested by moving them.

    RE-ENTRANT BY CONSTRUCTION, so it guards. PROBE_PROVOCATIONS and
    PROBE_IMPOSSIBLE are themselves registered declaration tables and this
    function is their verifier -- the only thing that can check them -- so probing
    them runs the probe, which probes them again. Unguarded that ran until it was
    killed. The inner call returns a cheap marker derived from the two tables
    instead, which still differs between the emptied and restored states, so both
    tables remain tested.
    """
    global _PROBE_RUNNING
    import copy
    import importlib
    import sys

    if _PROBE_RUNNING:
        return [f"__NESTED__{len(PROBE_PROVOCATIONS)}:{len(PROBE_IMPOSSIBLE)}"]
    _PROBE_RUNNING = True

    def run(names):
        """The verifiers' combined output, sorted, so it compares structurally.

        By CONTENT and not by count: emptying a table produces findings of its
        own -- a budget constant that no longer matches, a ratchet reading "down
        to 0" -- and a count comparison would read those as evidence the table is
        read, which is the opposite of the truth.
        """
        import inspect as _i

        out = []
        for n in names:
            fn = globals().get(n)
            if fn is None:
                out.append(f"__MISSING__{n}")
                continue
            # SOME VERIFIERS TAKE ARGUMENTS. check_countable_families_converted
            # takes `items`, and calling it bare raised TypeError -- identically
            # in every state, so its table read as INERT when the probe had simply
            # never run it. A raising verifier looks exactly like an unread table,
            # which is why the argument list is filled rather than defaulted.
            try:
                need = [q for q in _i.signature(fn).parameters.values()
                        if q.default is _i.Parameter.empty
                        and q.kind not in (q.VAR_POSITIONAL, q.VAR_KEYWORD)]
            except (TypeError, ValueError):
                need = []
            try:
                out.extend((fn(*[all_items() for _ in need]) if need else fn())
                           or [])
            except Exception as exc:
                # Recorded distinctly: a verifier this probe cannot call is a gap
                # in the PROBE, not evidence about the table, and the caller below
                # must not read the two as the same thing.
                out.append(f"__UNCALLABLE__{n}:{type(exc).__name__}")
        return sorted(out)

    report: list[str] = []
    inert: list[str] = []
    _base_cache: dict = {}
    for path, (what, verifiers) in sorted(DECLARATION_TABLES.items()):
        mod_name, _, attr = path.partition(".")
        # THIS module, when the probe runs as a script, is `__main__` -- and
        # importlib.import_module("enforcement") then builds a SECOND module
        # object with its own copy of every table. The first version of this probe
        # mutated that copy while the verifiers read __main__'s, so all twelve
        # enforcement.* tables reported INERT and the summary said 16 of 22
        # "enforce nothing". PROSE_ONLY_SLOTS was among them, which is provably
        # false: emptying it takes its verifier from 0 findings to 18.
        try:
            mod = (sys.modules[__name__] if mod_name == _SELF_MODULE
                   else importlib.import_module(mod_name))
        except Exception as exc:
            report.append(f"  CANNOT PROBE  {path}: {mod_name} will not import "
                          f"({type(exc).__name__})")
            continue
        table = getattr(mod, attr, None)
        if table is None:
            report.append(f"  CANNOT PROBE  {path}: attribute is absent")
            continue
        if path in PROBE_IMPOSSIBLE:
            report.append(f"  BY DESIGN     {path}: no provocation exists -- "
                          f"{PROBE_IMPOSSIBLE[path]}")
            continue
        prov = PROBE_PROVOCATIONS.get(path)
        if not table and prov is None:
            report.append(f"  CANNOT PROBE  {path}: empty, and no provocation is "
                          f"declared in PROBE_PROVOCATIONS, so nothing can be "
                          f"moved. Declare one")
            continue

        # The BASELINE is cached per verifier set. It is the output with nothing
        # mutated, so it is identical for every table sharing those verifiers --
        # and recomputing it per table tripled the cost of a probe that already
        # runs every verifier three times. That mattered the moment E36 took the
        # registry from 25 tables to 35, four of them fixture checks that read
        # every submission: the run stopped finishing inside ten minutes.
        key = tuple(verifiers)
        if key not in _base_cache:
            _base_cache[key] = run(verifiers)
        base = _base_cache[key]
        saved = copy.deepcopy(table)
        emptied = bogused = None
        try:
            # IN PLACE where the type allows, because a verifier may hold its own
            # reference to the object; setattr alone would leave that reference
            # pointing at the original and the probe would report a false INERT.
            if isinstance(table, (dict, list, set)):
                table.clear()
                emptied = run(verifiers)
                if isinstance(table, dict):
                    table.update(saved)
                elif isinstance(table, list):
                    table.extend(saved)
                else:
                    table.update(saved)
            else:
                setattr(mod, attr, _empty_like(table))
                emptied = run(verifiers)
                setattr(mod, attr, saved)

            # Corrupt rather than empty: a verifier that only ever asks "is this
            # table non-empty" would pass the emptying test and still not read
            # what is IN it.
            if isinstance(table, dict):
                if prov is not None:
                    k, v = prov
                else:
                    k, v = _bogus_key(next(iter(saved))), next(iter(saved.values()))
                if k is not None:
                    table[k] = v
                    bogused = run(verifiers)
                    table.pop(k, None)
            elif isinstance(table, list):
                table.append(copy.deepcopy(prov if prov is not None else saved[0]))
                bogused = run(verifiers)
                table.pop()
        finally:
            if isinstance(table, dict):
                table.clear(); table.update(saved)
            elif isinstance(table, list):
                table.clear(); table.extend(saved)
            elif isinstance(table, set):
                table.clear(); table.update(saved)
            else:
                setattr(mod, attr, saved)

        moved = [x for x in (emptied, bogused) if x is not None]
        # NO SIGNAL IS NOT INERTNESS. If the verifier reports nothing on the real
        # table, emptying it also reports nothing, and a bogus key naming nothing
        # real is correctly ignored -- three empty outputs prove only that the
        # table is currently clean. Saying INERT there would have condemned
        # GOLD_DIVERGENCES and PER_ITEM_EXCLUDE, both of which are read.
        if any(x.startswith("__UNCALLABLE__") for x in base):
            report.append(
                f"  CANNOT PROBE  {path}: this probe cannot call "
                f"{[x.split(':')[0][15:] for x in base if x.startswith('__UNCALLABLE__')]}"
                f" -- teach it the arguments before believing anything about "
                f"this table")
        elif not base and moved and all(not x for x in moved):
            report.append(
                f"  INCONCLUSIVE  {path} ({what}): its verifier(s) report nothing "
                f"on the real table, so emptying and corrupting it cannot be "
                f"distinguished. Probe it again from a state where it has "
                f"something to say")
        elif moved and all(x == base for x in moved):
            inert.append(path)
            report.append(
                f"  INERT         {path} ({what}): its verifier(s) "
                f"{list(verifiers)} produce identical output with the table "
                f"emptied{' and corrupted' if bogused is not None else ''} -- "
                f"nothing reads it, and the registry says it is checked")
        else:
            which = []
            if emptied is not None and emptied != base:
                which.append("emptying")
            if bogused is not None and bogused != base:
                which.append("corrupting")
            report.append(f"  READ          {path}: {' and '.join(which)} it "
                          f"changes the output")
    report.append("")
    report.append(f"  {len(inert)} of {len(DECLARATION_TABLES)} registered "
                  f"declaration table(s) enforce nothing"
                  + (": " + ", ".join(inert) if inert else ""))
    report.append("  INCONCLUSIVE is not a pass: it means the probe could not "
                  "tell, and those tables are still unverified.")
    _PROBE_RUNNING = False
    return report


# MOVED TO THE END. This block sat mid-module, so every function defined below it
# was invisible to it -- adding a flag that called one raised NameError, because a
# script runs top to bottom and the guard fires before the rest of the file is
# read. Nothing depended on its position.
# ---------------------------------------------------------------------------
# GOAL C / §10.7 -- a module declared MIGRATED holds no course data. (T4.1)
#
# C3c's gate half; T1.1 (`course_inventory`) is the metric half. Three checks,
# because §10.7's four categories do not all belong to the same question:
# categories 1-3 are about a module's CONTENTS and are gated per module here;
# category 4 is about the repository's FILE LIST and is its own check, since
# renaming `q6_consensus.py` changes the file's identity and no edit to its
# contents could ever satisfy a rule about its name.
#
# THE SCAN IS RUN, NOT READ. An earlier draft had this read T1.1's JSON. A gate
# reading a cached measurement passes while the thing it measures changes
# underneath -- add a course table to a module and yesterday's JSON still says
# zero. This project has already paid for that shape once: a dev server that
# reloaded CONTENT but not CODE mis-scored every mapped slot for 19 observations
# while looking healthy. So T1.1 is imported and called; its JSON stays the
# interface for humans and for T3.2, and the gate never trusts it.
# ---------------------------------------------------------------------------
_HERE_DIR = pathlib.Path(__file__).resolve().parent
_HERE_MODULE = sys.modules[__name__]
COURSE_DATA_BUDGET = _p7.SCORING_METADATA / "COURSE_DATA_BUDGET.json"

# WHICH MODULES ARE DECLARED MIGRATED. This is engine STATE -- a fact about the
# engine's own progress, not about psychology -- so it lives here beside the
# check and never in the course file. §0's rule decides it: the course file may
# not be where the engine records how far it has got.
#
# Empty at Stage 4's start, and that emptiness is why the ratchet below exists.
MIGRATED_MODULES: dict[str, str] = {}

# Modules that ARE authored course data, by design. The ratchet exists to stop
# course content accumulating in ENGINE code; a declared data module is not
# engine code, and counting it made the ratchet refuse the migration it was
# written to enable -- `generator_source.py` went 11 -> 14 because three marker
# tables arrived there FROM `segment.py`, which is the work succeeding.
#
# Their contents are still COUNTED and REPORTED, just not ratcheted: the point
# is to see how much course data exists and where, not to pretend a data module
# holds none.
def _data_modules() -> dict[str, str]:
    """Modules that ARE authored course data, by design.

    The ratchet exists to stop course content accumulating in ENGINE code; a
    declared data module is not engine code, and counting it made the ratchet
    refuse the migration it was written to enable -- `generator_source.py` went
    11 -> 14 because three marker tables arrived there FROM `segment.py`, which
    is the work succeeding.

    Their contents are still COUNTED and REPORTED, just not ratcheted: the point
    is to see how much course data exists and where, not to pretend a data
    module holds none.

    DERIVED, AND THAT IS THE FIX. This was a hand-written dict of three, and on
    2026-09-25 `--tighten` refused on `course_metadata_source.py: 4 -> 7` -- a
    Stage 4 authoring builder being ratcheted while two of its siblings were
    exempt. Nobody decided that. The dict was last edited 2026-09-19 (f5830d44)
    listing the two builders that existed then; on 2026-09-23 (011f641e) the
    source modules were SPLIT BY CATEGORY into four, `migrated_tables.BUILDERS`
    was updated, and this dict was not touched at all. The two new builders
    entered the budget at their then-counts and have been ratcheted since.

    THE SAME DRIFT, ONE TABLE OVER, AND ITS OWN COMMENT SAYS SO. `BUILDERS`
    carries this: "it was two names until 2026-09-23 ... moving eight tables
    into new modules made this check report all of them as having NO builder,
    because it was looking in the wrong two files." A hard-coded pair was a
    liability there and was replaced by a list of record; the identical pair
    here was left, and broke the identical way. So this reads that list rather
    than restating it, and a builder added to it is exempt here at once.

    NOT A WIDENING. Every name this returns is a module the engine does not
    import at scoring time -- the builders are read by `rubric_export` to WRITE
    the course file -- or course-side code the engine reaches only by name. The
    entries are still checked below: a declared data module must exist and must
    actually carry course data.

    THE COST, STATED. `editguard` sees literal table entries, so a derived table
    is invisible to it: nothing will report an entry here "vanishing". What
    replaces that is the check below, which refuses a declared module that is
    absent or that carries no course data -- and, for the builders, the fact
    that the list of record is the one `rubric_export` reads to find them at all.
    """
    import migrated_tables

    out: dict[str, str] = {}

    # (1) THE STAGE 4 AUTHORING BUILDERS, from the list of record.
    for mod in migrated_tables.BUILDERS:
        out[f"{mod}.py"] = (
            "a Stage 4 authoring builder (`migrated_tables.BUILDERS`): authored "
            "tables the export reads to WRITE the course file, kept outside the "
            "scoring path. Course data is what it is for, and it GROWS as "
            "modules are migrated INTO it")

    # (2) THE RUBRIC SOURCES, by the same name pattern `rubric_export` resolves
    # them with -- `rubric_h{form}_source`. Stage 6c renamed handout 2's rubric
    # to `rubric_h2_source.py` and moved it out of the scoring path to sit with
    # the builders; its data is the course file's and is served from there, and
    # what stays is the four factories the export reads to WRITE that file.
    for path in sorted(_HERE_DIR.glob("rubric_h*_source.py")):
        out[path.name] = (
            "a handout's authored rubric, read by `rubric_export` to WRITE the "
            "course file and kept outside the scoring path")

    # (3) THE COURSE'S OWN CODE, which is NOT a builder and is named one file at
    # a time on purpose. These RUN -- `scorers.resolve` loads the scorer during
    # scoring and `segment.course_hook` reads the hook -- so unlike the builders
    # above they are reachable from the scoring path, and a glob over those
    # directories would exempt anything anyone dropped into them. Each earns its
    # own line with its own reason.
    #
    # RATCHETING `oc.py` WOULD REFUSE THE MIGRATION. Subgoal E58 moves course
    # facts OUT of engine modules and INTO it: `probe.ANSWERED_UNDER`'s operant
    # half and its gate arrived on 2026-09-25, and probe.py's vocabulary count
    # fell by the same work.
    out["oc.py"] = (
        "this course's operant-conditioning scorer, shipped in the course "
        "repository's own scorers/ and loaded by name: authored course knowledge "
        "that runs, and that GROWS as E58 moves facts out of engine modules")
    out["course_segment.py"] = (
        "this course's segmentation hook, shipped in the course repository's "
        "own fixture/ and read through `segment.course_hook`: one function, "
        "whose content is the four behaviours Handout 1 names")
    return out


DATA_MODULES = _data_modules()

# FIXTURES THAT NAME THEIR TARGET, AND WHY EACH IS NAMED RATHER THAN DERIVED.
#
# D2a converted eleven of twelve case clusters in `enforcement_selftest` to pick
# by shape -- the first item with `counts`, the first job with a `dealt` group.
# These nine did not convert, and the reason matters more than the count: a
# named fixture with a stated justification is honest, while a contrived
# predicate that selects the wrong cell passes quietly on the wrong thing.
#
# THAT IS NOT HYPOTHETICAL. One conversion picked "the first cell carrying a
# consensus fix", landed on a cell whose fixes named other boxes, and detected
# NOTHING while looking exactly like a passing case. A case that names its
# target at least breaks loudly when the target changes shape.
#
# Each entry is checked: the id must still be an item this course has. A
# fixture naming something that no longer exists is the drift D2a was written
# to catch, and it is caught here for the nine that stayed behind.
# Entries and their reasons: the course file. Authored in
# `declaration_source.py`, which is what the export reads.
# BOUND BELOW, after `_declaration` is defined.


# WHO MAY IMPORT THE RUBRIC MODULES, and why. A1c keeps `rubric_h*` as an
# AUTHORING tool that generates the course file; Stage 5 deletes them as scoring
# inputs. The difference between those two sentences is this table: a builder
# and the tools that PROVE the build may read them, and the scoring path may
# not.
#
# The boundary is declared rather than assumed because the plan's own sequence
# does not say it. Stage 5's deletion is gated on C1b, which landed 2026-09-19,
# so the gate is open and what is left is consumers -- and a consumer that
# cannot be found is a consumer that breaks on the day the files go.
RUBRIC_BUILDERS = {
    "rubric_export.py":
        "THE builder: it reads the modules to WRITE the course file. A1c -- the "
        "builders survive outside the pipeline.",
    "rubric_equivalence.py":
        "T5.1, the licensing tool: it proves the file reproduces the modules "
        "while they are still the oracle. Its last run is what permits the "
        "deletion, so it must read both sides until then.",
    "reader_equivalence.py":
        "T3.2, the same proof through `coursedata`. Reads both sides for the "
        "same reason and for exactly as long.",
}

# Scoring-path modules that STILL import the rubric, which is the remaining
# Stage 5 work. A number, not a list of excuses: it may fall and it may not
# rise, and when it reaches zero the modules can go.
#
# `course_inventory.py` is in here rather than in RUBRIC_BUILDERS deliberately.
# It reads the modules only to learn this course's item ids, and it already
# prefers a course file when given one -- `_inventory_now()` simply does not
# pass one. That makes it the cheapest of the twelve, not an exception to them.
# ONE, and it is the one that cannot be converted:
# `check_selectors_govern_something` reads handout 2's module SOURCE to find
# selector tuples that are defined and no longer consulted. `inspect.getsource`
# on a data view raises TypeError, so it is a check about the AUTHORING
# ARTIFACT, not about the rubric data. Every other consumer reaches the rubric
# through `forms.config(h)["rubric"]`, a view onto the course file.
#
# IT WAS TO BE DELETED WITH THE MODULES AT STAGE 5, on the reasoning that a
# check for stale selectors in a file that no longer exists has nothing to find.
# Stage 6c falsified the premise rather than the check: handout 2's module was
# RENAMED to `rubric_h2_source.py`, not deleted, because `rubric_export` reads
# its four factories to write the course file. The artifact still exists, so
# this budget stays at 1 and the import it counts is now that name. That required
# adding `rubric_h2_source` to the RUBRIC set the counter matches on: the set
# holds EXACT module names, not a `rubric_h` substring, so without it the count
# fell to 0 and this ceiling would have sat un-lowered over a guard that had
# stopped counting anything. The audit caught it; the assumption did not.
RUBRIC_CONSUMER_BUDGET = _budget("RUBRIC_CONSUMER_BUDGET")


# A COUNT THAT ROSE BECAUSE AN EXEMPTION WAS REMOVED, not because course data
# was added. The ratchet refuses a rise, and it is right to: baselining a
# regression records history instead of enforcing it. But removing D2d made
# `equivalence.py` go 0 -> 27 without a single new embedding, and until that is
# recorded the budget CANNOT BE WRITTEN AT ALL -- which blocks bookkeeping that
# has nothing to do with it. It blocked this within the hour: migrating
# COUNTABLE_EXEMPT grew `declaration_source.py` 11 -> 12, exactly the growth a
# declared data module is supposed to show, and the write was refused.
#
# So a rise may be recorded ONCE, and only with a reason and a number stated
# here. It is not an exemption: the 27 stay counted, stay printed, and the
# ratchet resumes from them -- it can fall and never rise again without another
# entry. An entry whose number no longer matches the count is reported, so this
# cannot quietly become a second budget.
COURSE_DATA_REENTRY: dict[str, tuple[int, str]] = {
    "equivalence.py": (
        # 27 -> 24 -> 17 on 2026-09-20 as D2a proceeds. Converted so far: the
        # `dealt` fixture (first job with a `dealt` group), the `equals` case
        # (first h2 item declaring `equals`), the coded-antecedent case (first
        # h1 item with coded `antecedent_*` slots), the broken-code case (first
        # h3 item whose first credit carries codes) and the `expect` case
        # (first h2 item with both an `expect` rule and an EXPECT entry).
        #
        # Reviewed here each time rather than re-baselined silently -- which is
        # what this check is for, and it has now caught the drop twice.
        # 27 -> 24 -> 17 -> 13 on 2026-09-20. Added since: the `cover` and
        # cover-vocabulary cases (first h1 item with a labelled `cover` rule),
        # the duplicated-item case (any item proves it; the first h1 item), and
        # the two-fixes case (first cell carrying a consensus fix, duplicating a
        # box THAT CELL already fixes rather than a name typed into the case).
        # 27 -> 24 -> 17 -> 13 -> 10 on 2026-09-20. Added since: the
        # computed-check case (first item a divergence says the web computes),
        # the exclusion-prose case (first exclusion cell carrying an
        # `expect_error` -- a case that had ALREADY drifted once, from Q6/p9 to
        # Q4c/p16, and was re-pointed by hand), and the unjustified-citation
        # case (the item is incidental; pid 99 is what makes it unjustified).
        # 27 -> 9 over 2026-09-20. D2a is DONE, and it did not reach zero:
        # eleven of twelve case clusters now pick their target by shape, and the
        # 9 that remain are NAMED ON PURPOSE, each with its reason in
        # `SELFTEST_NAMED_FIXTURES` and each checked to still name a real item.
        #
        # Stopping here is the finding, not a shortfall. One forced predicate
        # already picked a cell where the injection created no duplicate and the
        # case detected nothing while reporting PASS. A named fixture with a
        # stated reason fails loudly; a contrived predicate fails silently, and
        # silence is what D2a exists to remove.
        # 9 -> 7 on 2026-09-20, after the nine declared reasons were tested as
        # CLAIMS rather than re-read. Two did not survive: one said its item was
        # the only one with a shape the case actually INJECTS, and one said it
        # "follows" a case it merely coincided with. Both are shape-picked now.
        # Five of the remaining seven were confirmed by measurement.
        7,
        "D2d's exemption was removed 2026-09-19. These 27 embeddings were always "
        "there and were subtracted before anyone looked; nothing was added. D2a "
        "(fixtures that select their target by shape) is the work that removes "
        "them, and the finding is parked under MIGRATED MODULE HOLDS COURSE DATA "
        "until it lands."),
}


# D2d'S EXEMPTION IS GONE, removed 2026-09-19 after the expiry check had been
# reporting it for a day. It excused the course-bound embeddings in
# `equivalence.py::enforcement_selftest` from the course-data rule, conditional
# on two self-test defects; both closed on 2026-09-18 and the check said so
# rather than letting the exemption drift on unexamined.
#
# WHAT REPLACES IT IS NOT NOTHING, AND NOT A RE-BASELINE. Those embeddings are
# still there -- D2a (fixtures that select their target BY SHAPE and report the
# target they chose) is the work that removes them, and it is owed. So the count
# is COUNTED now: `equivalence.py` rises from 0 to its real number, the ratchet
# refuses to baseline a rise, and the resulting finding is PARKED with D2a named
# as the scheduled fix. Exempt-and-invisible became counted-and-declared: the
# same amount of course data, a different amount of honesty.
#
# THE LESSON FROM THE MECHANISM, KEPT BECAUSE IT OUTLIVES IT. `_exempt` began as
# `entry.get("in") == <exemption>.get(module)`, and for any module NOT in the
# exemption both sides were `None` -- so every module-level embedding in every
# module compared equal and was excused. Measured when the totals refused to
# reconcile: 117 of 230 embeddings silently exempt, in modules the exemption had
# nothing to do with. A `None == None` comparison is how a narrow exemption
# becomes a general one, and the next exemption written here should start there.


_INVENTORY_MEMO: dict = {}


def _inventory_now() -> dict:
    """T1.1's scan, run fresh. See the header: never the cached JSON.

    STILL FRESH. The memo below is keyed on everything the scan reads, so it
    returns a previous result only when re-running would produce the same one.
    "Never the cached JSON" is about the artifact on disk, which can be stale
    against the tree; this cannot, because a stale key cannot be hit.

    WHY IT IS WORTH IT: the scan costs 4.5s and `enforcement_audit()` calls it
    TWICE, so it was 9.1s of a 63s audit -- and the audit runs once per
    self-test case, 71 times.

    THE ID SET IS PART OF THE KEY, AND THAT IS THE WHOLE SUBTLETY. The scan
    needs this course's item ids, and with no course file argument
    `course_inventory.item_ids` falls back to `rubric_h*.BY_ID` -- IN-MEMORY
    state, which is exactly what the self-test mutates when it injects. A memo
    keyed on file mtimes alone would have served a pre-injection scan to a
    post-injection audit, and the case would have gone undetected while
    reporting clean. That is the one failure this instrument must never have,
    so the ids are read (cheap: dict keys) and hashed into the key alongside
    the source fingerprint.
    """
    import os

    from tools import course_inventory
    # NARROW, AND NOT `except Exception`. The first version of this caught
    # everything and fell back to a full scan -- and the fallback fired every
    # time, because the `os` helpers it called had never been defined. A
    # NameError was swallowed into "the cache is disabled", the memo stayed
    # empty, and the timing looked almost unchanged rather than broken. That is
    # the same swallowed-NameError shape that made `keyrepr` report all fifteen
    # gold keys unreadable earlier in this same migration. An unreadable tree is
    # a real reason to fail open; a bug in this function is not.
    fingerprint = []
    try:
        here = str(_HERE_DIR)
        for name in sorted(f for f in os.listdir(here) if f.endswith(".py")):
            st = os.stat(os.path.join(here, name))
            fingerprint.append((name, st.st_mtime_ns, st.st_size))
        key = (tuple(fingerprint), frozenset(course_inventory.item_ids()))
    except OSError:                                 # pragma: no cover
        return course_inventory.inventory()         # fail open: scan, never guess

    hit = _INVENTORY_MEMO.get(key)
    if hit is None:
        hit = course_inventory.inventory()
        _INVENTORY_MEMO.clear()                     # one entry: the current tree
        _INVENTORY_MEMO[key] = hit
    return hit


def _course_data_counts(inv: dict) -> dict[str, int]:
    """Per module, how many category 1-3 embeddings survive the exemption."""
    out = {}
    for rec in inv.get("modules", []):
        mod = rec["module"]
        n = 0
        for cat in ("tables", "literal_ids", "vocabulary"):
            # EVERY embedding, with no exemption to subtract: see the note above
            # `DATA_MODULES` for why D2d's is gone and what replaced it.
            n += len(rec.get(cat, []))
        out[mod] = n
    return out


def check_module_has_no_course_data() -> list[str]:
    """A module declared MIGRATED carries no course table, id or vocabulary.

    TWO MECHANISMS, BECAUSE THEY CATCH DIFFERENT FAILURES. `MIGRATED_MODULES` is a
    whitelist and whitelists rot: a module can be cleaned and never declared, and
    nothing notices. So the counts are ALSO ratcheted, in the idiom
    `STUDENT_TEXT_BUDGET.json` already uses here -- they may fall and may not rise.
    The whitelist proves a specific module is done; the ratchet catches a
    regression anywhere, including in the modules nobody has declared yet, which
    is most of them for most of Stage 4.
    """
    import json as _json

    out: list[str] = []
    inv = _inventory_now()
    counts = _course_data_counts(inv)
    by_name = {r["module"]: r for r in inv.get("modules", [])}

    # ---- the whitelist ----------------------------------------------------
    for mod, claim in sorted(MIGRATED_MODULES.items()):
        rec = by_name.get(mod)
        if rec is None:
            out.append(f"{mod} is declared MIGRATED but the scan never saw it -- "
                       f"a declaration naming a file that is not there proves "
                       f"nothing and hides that the module was never checked")
            continue
        if counts.get(mod):
            detail = ", ".join(
                f"{cat}={sum(1 for e in rec.get(cat, []) if not _exempt(mod, e))}"
                for cat in ("tables", "literal_ids", "vocabulary")
                if sum(1 for e in rec.get(cat, []) if not _exempt(mod, e)))
            out.append(f"{mod} is declared MIGRATED ({claim}) but still holds "
                       f"course data: {detail}")

    # ---- the exemption itself is checked ----------------------------------
    # DATA_MODULES was INERT when `--probe-declarations` measured it: emptying it
    # changed nothing, because the budget records the data modules' counts too,
    # so removing the exemption found no growth to complain about. An exemption
    # nothing verifies is an exemption anyone can widen.
    #
    # So its ENTRIES are checked: a declared data module must exist, and must
    # actually carry course data -- otherwise the exemption is either stale or
    # covering a module that never needed it.
    for mod, why in sorted(DATA_MODULES.items()):
        if mod not in counts:
            out.append(f"{mod} is declared a DATA module ({why[:40]}...) and the "
                       f"scan never saw it -- an exemption for a file that is not "
                       f"there exempts nothing and hides that it is gone")
        elif not counts[mod]:
            out.append(f"{mod} is declared a DATA module and carries NO course "
                       f"data. The declaration exists to keep authored content out "
                       f"of the engine ratchet; a module with none does not need "
                       f"it, and keeping it invites widening the exemption")

    # ---- the ratchet ------------------------------------------------------
    try:
        budget = jsoncache.load(COURSE_DATA_BUDGET)
    except FileNotFoundError:
        out.append(f"{COURSE_DATA_BUDGET.name} is missing, so the ratchet cannot "
                   f"run -- and a ratchet that cannot run is not the same as one "
                   f"that passes. Write it with `course_inventory.py --tighten`.")
        budget = None
    except ValueError as exc:
        out.append(f"{COURSE_DATA_BUDGET.name} is unreadable: {exc}")
        budget = None

    if budget is not None:
        base = budget.get("modules", {})
        for mod, n in sorted(counts.items()):
            if mod in DATA_MODULES:
                continue                          # counted, reported, not ratcheted
            was = base.get(mod)
            if was is None:
                out.append(f"{mod} carries {n} course-data embedding(s) and is not "
                           f"in the budget -- a NEW module enters at its own count "
                           f"or not at all; run `course_inventory.py --tighten`")
            elif n > was:
                out.append(f"{mod} course data grew {was} -> {n}; the ratchet only "
                           f"tightens")
    # A RE-ENTERED COUNT STAYS REPORTED. Recording `equivalence.py`'s 27 in the
    # budget stopped the ratchet complaining -- and with that, the only thing
    # saying those embeddings exist would have been a number in a JSON file.
    # That is the exact condition the D2d exemption was removed to escape: the
    # data subtracted before anyone looked. A declared re-entry buys the budget
    # the right to be WRITTEN, not the right to go quiet.
    for mod, (_declared, why) in sorted(COURSE_DATA_REENTRY.items()):
        n = counts.get(mod, 0)
        if n:
            out.append(f"{mod} holds {n} course-data embedding(s) under a "
                       f"declared re-entry -- {why}")

    # Report what the data modules hold, so excluding them from the ratchet does
    # not also hide them.
    held = {m: counts.get(m, 0) for m in sorted(DATA_MODULES) if counts.get(m)}
    if held and budget is not None:
        recorded = budget.get("data_modules", {})
        if recorded != held:
            out.append(f"the declared DATA modules hold {held}, and the budget "
                       f"records {recorded} -- re-tighten so the amount of course "
                       f"data and where it sits stays visible")

    return out


def check_no_module_is_named_for_a_course_artifact() -> list[str]:
    """§10.7 category 4 -- a generic engine has no module named for a question,
    a handout or a course.

    ITS OWN CHECK, NOT A CATEGORY FOLDED INTO THE ONE ABOVE. This rule is about
    the repository's file list, not about any module's contents: `q6_consensus.py`
    cannot satisfy it by editing itself, only by being renamed. Folded in, it
    would make a per-module gate fail for a reason that module's own contents can
    never fix.
    """
    inv = _inventory_now()
    out = []
    for rec in sorted(inv.get("modules", []), key=lambda r: r["module"]):
        for hit in rec.get("name_names_course", []):
            marker = hit.get("marker") if isinstance(hit, dict) else hit
            out.append(f"{rec['module']} is named for a course artifact "
                       f"({marker!r}) -- GOAL E; renaming is the only fix")
    # RATCHETED, LIKE THE COUNTS. GOAL E is Stage 7 work and these nine modules
    # are still named for questions and handouts today, so a check that simply
    # reported them would fail the audit from the moment it was added -- which
    # means it could only be added AFTER the work it exists to gate, and would
    # gate nothing. Baselined instead: the population may shrink and may not grow.
    import json as _json
    try:
        allowed = jsoncache.load(COURSE_DATA_BUDGET).get("named_modules", [])
    except (FileNotFoundError, ValueError):
        return out + [f"{COURSE_DATA_BUDGET.name} is missing or unreadable, so the "
                      f"course-named-module ratchet cannot run -- which is not the "
                      f"same as passing"]
    known = set(allowed)
    fresh = [f for f in out if f.split(" is named")[0] not in known]
    stale = sorted(known - {f.split(" is named")[0] for f in out})
    return fresh + [f"{m} is in the course-named-module budget but no longer "
                    f"matches -- re-tighten so the reduction cannot be undone"
                    for m in stale]


def check_gold_shared_prose_has_not_drifted() -> list[str]:
    """A gold note that was ONE string in python, and is now several in JSON.

    `DECLARED_CEILING_CELLS` named `_1C_GATE_CEILING` in four of its five
    entries, so python guaranteed by construction that the four said the same
    thing. JSON has no names: the export writes the 492 characters out five
    times over, and an edit to one copy leaves the others quietly stale. That is
    a real loss of an invariant the migration could not carry, so it is checked
    instead of assumed.

    THE TEST IS NEAR-MISS, NOT EQUALITY. Requiring every entry to equal the
    canonical text would be wrong -- the fifth entry is a different declaration
    and always was. What cannot be legitimate is a value that is ALMOST the
    canonical text: nobody writes 95% of a 492-character paragraph by accident,
    so a close-but-unequal copy is a drifted one. An entry that shares nothing
    with it is simply a different note and is not this check's business.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K: python reads the two declarations
    # from gold and `enforce/goldSharedProse.ts` compares them.
    #
    # ITS SIMILARITY MEASURE IS CPYTHON'S, TRANSCRIBED. The threshold is
    # `difflib.SequenceMatcher(...).ratio() >= 0.90`, and JavaScript has no
    # equivalent: Levenshtein, Dice and LCS all return a DIFFERENT number, so a
    # port using one reports a different SET of cells at the same threshold.
    # `enforce/sequenceRatio.ts` reproduces the algorithm -- autojunk, both
    # extension passes and all -- verified against CPython on 266 pairs with a
    # worst delta of zero.
    #
    # THE KEYS ARE RENDERED THERE TOO, from the tagged form the records store.
    # An earlier draft had python pre-render them, which made the rule
    # uncallable from inside lo-blocks.
    # SELF-ASSEMBLED. Subgoal E63: the runner builds this payload itself,
    # from the same course records python would have read. The assembler was
    # compared against the payload python used to send and found IDENTICAL
    # before this fetch was deleted; `runner.SELF_ASSEMBLING` names the rules
    # that comparison has cleared, and the runner refuses any other.
    import lo_enforce

    return lo_enforce.run("gold_shared_prose_has_not_drifted", None)



def check_source_cache_matches_the_stdlib() -> list[str]:
    """`sourcecache.segment` still returns exactly what `ast.get_source_segment` does.

    THE CACHE SITS UNDER SIX CHECKS THAT JUDGE CODE BY READING IT. If its
    segments drift from the stdlib's by even a byte -- a `\r\n` split
    differently, a column offset counted in characters instead of bytes -- those
    checks start judging text that is not quite the code, and every one of them
    would still pass. That is a worse failure than the 5,776x slowness the cache
    removes, so the speedup is only acceptable while this holds.

    ADVERSARIAL, NOT BULK, AND FOR A MEASURED REASON. The first version of this
    sampled 500 nodes out of nine real modules and cost 13 SECONDS -- per audit,
    times 71 self-test cases, which is fifteen minutes added to the run the cache
    was written to shorten. A check that eats the saving it guards is not a
    check, it is a tax. Volume was never what made this safe anyway: the ways
    `segment` can diverge are all about ENCODING -- multibyte columns, `\r\n`
    kept together, a form feed the parser ignores, an empty last line -- and
    each is provoked by a few lines of source rather than found by chance in a
    thousand well-behaved ones. The real-file tail stays small, just enough that
    a wholesale breakage cannot hide behind tidy synthetic inputs.
    """
    import ast as _ast
    import os as _os

    import sourcecache

    CASES = (
        "x = 1\n",                                     # trivial
        "x = 1",                                        # no trailing newline
        "def f():\r\n    return 1\r\n",               # CRLF kept together
        "def f():\n\x0c    return 1\n",                # form feed the parser ignores
        "s = '\u00e9\u00e9\u00e9'\nt = s + '\u4e2d\u6587'\n",  # multibyte columns
        "d = {\n 'a': 1,\n 'b': 2,\n}\n",              # multi-line, indented
        "def g(a,\n      b):\n    return (a +\n            b)\n",
        "class C:\n    x = [1,\n         2]\n    def m(self): pass\n",
        "# leading comment\n\n\nq = f'{1 + 2}'\n",
        "x = 1\n\n",                                   # empty final line
    )
    out = []
    checked = 0
    for text in CASES:
        try:
            tree = _ast.parse(text)
        except SyntaxError:                         # pragma: no cover
            out.append("the source-cache fixture does not parse -- fix the fixture")
            continue
        for node in _ast.walk(tree):
            if not hasattr(node, "lineno"):
                continue
            for padded in (False, True):
                checked += 1
                if sourcecache.segment(text, node, padded=padded) != \
                        _ast.get_source_segment(text, node, padded=padded):
                    return [f"sourcecache.segment disagrees with the stdlib on "
                            f"{text!r} at line {node.lineno} "
                            f"({type(node).__name__}, padded={padded}) -- the six "
                            f"checks that read code through it are judging text "
                            f"that is not the code"]

    # A REAL FILE TOO, small and bounded: the fixtures above are all tiny, and a
    # cache that broke only past some size would pass every one of them.
    try:
        path = _os.path.join(str(_HERE_DIR), "enforcement.py")
        text = open(path, errors="ignore").read()
        tree = _ast.parse(text)
    except (OSError, SyntaxError):                  # pragma: no cover
        return out
    # TWENTY, because each of these costs ~9ms: the stdlib call re-splits all
    # 738KB every time, which is the very cost being removed. The fixtures above
    # carry the correctness argument; this tail only has to notice a wholesale
    # breakage, and twenty nodes from three places in the file does that.
    nodes = [n for n in _ast.walk(tree) if isinstance(n, _ast.stmt)]
    for node in nodes[:7] + nodes[len(nodes) // 2:len(nodes) // 2 + 7] + nodes[-6:]:
        checked += 1
        if sourcecache.segment(text, node) != _ast.get_source_segment(text, node):
            return [f"sourcecache.segment disagrees with the stdlib on "
                    f"enforcement.py:{node.lineno} -- the six checks that read "
                    f"code through it are judging text that is not the code"]
    # A FLOOR ON THE FIXTURES, not on the total. Ten synthetic sources yield
    # ~106 node/padding pairs, so anything under a hundred means the loop above
    # stopped early or the fixture list was emptied -- which is the failure this
    # guards, a comparison that ran on nothing and reported clean.
    if checked < 100:
        out.append(f"the source-cache comparison only managed {checked} nodes -- "
                   f"it is not exercising the cache and proves nothing")
    return out


def check_json_cache_is_not_mutated() -> list[str]:
    """Nobody has written into a document `jsoncache` is still handing out.

    `jsoncache.load` returns the SHARED parsed object rather than a copy -- that
    sharing is the whole saving, since a deepcopy of these documents costs about
    what parsing them costs. The price is that a caller which mutates what it
    receives silently corrupts every later reader in the process, and the
    corruption would surface as some unrelated check reporting something odd
    much later.

    So the read-only contract is checked instead of trusted, here, at the end of
    an audit, where a mutation is attributed to the run that caused it.

    SAMPLED, AND SAYING SO. Fingerprinting every held document means `json.dumps`
    over 282 MB, which is what made an earlier version of this cache SLOWER than
    no cache at all. One document in 32 is watched -- about 29 per audit -- and
    the audit runs once per self-test case, so over a full run a mutation has
    many chances to land on a watched document. That is detection, not proof: a
    clean result here means no watched copy changed, not that none did.
    """
    import jsoncache

    return [f"{path} was mutated after jsoncache handed it out -- jsoncache.load "
            f"returns a SHARED object and its callers must treat it as read-only. "
            f"Copy before writing, or read the file directly."
            for path in jsoncache.mutated()]


def check_course_data_reentries_are_current() -> list[str]:
    """Every declared re-entry still states the number the module actually holds.

    `COURSE_DATA_REENTRY` lets a count be recorded once after an exemption is
    removed, so that a rise nobody caused does not freeze the whole budget. That
    is a hole in a ratchet, and a hole needs a door that closes: an entry whose
    number has drifted from the real count is a second budget with none of the
    review, and an entry whose count has fallen to zero is work that FINISHED
    and left its paperwork behind.

    Both directions are reported. The one that matters most is the fall: when
    D2a lands and `equivalence.py` stops embedding course ids, this is what says
    the entry can go.
    """
    import json as _json

    reentry = COURSE_DATA_REENTRY
    if not reentry:
        return []
    try:
        counts = _course_data_counts(_inventory_now())
    except Exception as exc:                        # pragma: no cover
        return [f"cannot scan to verify the re-entry declarations: {exc}"]
    out = []
    for mod, (declared, why) in sorted(reentry.items()):
        now = counts.get(mod)
        if now is None:
            out.append(f"COURSE_DATA_REENTRY names {mod}, which the scan does not "
                       f"report at all -- the entry describes nothing")
        elif now == 0:
            out.append(f"COURSE_DATA_REENTRY still carries {mod}, whose count has "
                       f"reached ZERO. The work it was waiting on is done; remove "
                       f"the entry so the ratchet has no hole left in it.")
        elif now != declared:
            out.append(f"COURSE_DATA_REENTRY says {mod} holds {declared} "
                       f"embedding(s) and it holds {now}. A re-entry records a "
                       f"number ONCE; if the count moved, it moved for a reason "
                       f"that has not been reviewed.")
        if not str(why).strip():
            out.append(f"the re-entry for {mod} carries no reason")
    return out


def check_hand_authored_attrs_still_suppress_something() -> list[str]:
    """Every HAND_AUTHORED_ATTRS entry still excuses a finding that would fire.

    An entry says: this generated attribute is authored by hand ON PURPOSE, so
    do not report it as an orphan. It only means anything while the attribute is
    PRESENT and the rubric does NOT back it. The moment a generator conversion
    lands for that attribute, the rubric backs it, the entry suppresses nothing,
    and what is left is a declaration asserting a state of affairs that ended.

    THAT IS NOT HYPOTHETICAL AND IS WHY THIS EXISTS. All four entries -- PR, NR,
    PP and NP's `expect` -- were stale when this was written: the rubric backs
    every one of them. The table's own note says to keep it small because "every
    entry is a place where the rubric is NOT the single source, which is the
    thing the generator conversions exist to remove". The conversion happened
    and the paperwork stayed, and nothing said so: emptying the whole table
    changed no output, because none of its entries was doing any work.

    A stale entry is worse than an untidy one. It is standing permission for an
    orphan that nobody has re-examined, and it would silently swallow a REAL
    orphan if one appeared at the same (item, attribute).
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K. Python reads the sheet and the
    # generator registry; the judgement -- an exemption for an attribute that is
    # not there excuses nothing -- is generic.
    import re

    import lo_enforce
    import olx_prompts as OP

    gen = dict(OP.GENERATED_ATTRS)
    entries = []
    for (item_id, name), why in sorted(HAND_AUTHORED_ATTRS.items()):
        present = False
        if name in gen:
            try:
                tag = OP._sheet_tag(OP.FORM[item_id], OP.ACTION[item_id])
                m = re.search(r'%s="([^"]*)"' % name, tag)
                present = bool(m and m.group(1).strip())
            except Exception:
                continue                  # a missing sheet is another check's
        entries.append({"item": item_id, "name": name, "why": str(why),
                        "isGenerated": name in gen, "present": present})
    if not entries:
        return []                         # an empty exemption table excuses nothing
    return lo_enforce.run("hand_authored_attrs_still_suppress_something",
                          {"entries": entries})



def check_only_builders_read_the_rubric() -> list[str]:
    """The scoring path's remaining dependence on `rubric_h*`, counted.

    Stage 5 deletes the rubric modules as scoring inputs. Everything that still
    imports them breaks on that day, so the number is tracked the way every
    other debt here is: declared, ratcheted, and allowed to fall only.

    FOUND BY AST, NOT BY GREP. Four of these import dynamically --
    `__import__(f"rubric_h{h}")` and `importlib.import_module(f"rubric_h{h}")`
    -- which a `rubric_h[123]` pattern never matches. Counting by grep gave 11
    and the real number was 16. A migration sized against the smaller number
    would have declared victory with four importers still live.
    """
    import ast as _ast
    import os as _os

    # `rubric_h2_source` IS IN THIS SET, and leaving it out was a real bug for
    # the length of one audit. Stage 6c renamed handout 2's module rather than
    # deleting it, and this set matches EXACT names -- so the count silently fell
    # from 1 to 0 and the audit reported the ceiling as un-lowered. Lowering it to
    # 0 was the wrong repair: the renamed module still holds the whole handout 2
    # rubric, so a scoring module importing it is precisely the regression this
    # budget exists to catch. Counting the new name keeps that guard live.
    RUBRIC = {"rubric_h1", "rubric_h2", "rubric_h3", "rubric_h2_source"}
    here = str(_HERE_DIR)
    consumers = []
    try:
        names = sorted(f for f in _os.listdir(here) if f.endswith(".py"))
    except OSError as exc:                          # pragma: no cover
        return [f"cannot list {here}: {exc}"]
    for fn in names:
        try:
            tree = _ast.parse(open(_os.path.join(here, fn), errors="ignore").read())
        except (OSError, SyntaxError):
            continue
        # EVERY SITE, NOT THE FIRST. This counted a FILE and stopped at its first
        # import, so three `__import__` loops inside `enforcement.py` hid behind
        # the one source-reading import that file is allowed to keep -- the
        # count read 1 with four dependencies live. That is the SECOND blind
        # spot this check has had: it also missed the whole
        # `config(h)["rubric"]` channel, 101 sites, until that was measured by
        # hand. A number nobody can hide behind is the only kind worth ratcheting.
        sites = 0
        for n in _ast.walk(tree):
            if isinstance(n, _ast.Import):
                sites += sum(1 for a in n.names if a.name in RUBRIC)
            elif isinstance(n, _ast.ImportFrom):
                sites += 1 if n.module in RUBRIC else 0
            elif isinstance(n, _ast.Call):
                fname = (n.func.id if isinstance(n.func, _ast.Name)
                         else getattr(n.func, "attr", None))
                if fname in ("__import__", "import_module") and n.args:
                    a = n.args[0]
                    if isinstance(a, _ast.Constant) and a.value in RUBRIC:
                        sites += 1
                    elif isinstance(a, _ast.JoinedStr) and any(
                            isinstance(v, _ast.Constant) and "rubric_h" in str(v.value)
                            for v in a.values):
                        sites += 1
        if sites and fn not in RUBRIC_BUILDERS:
            consumers.extend([fn] * sites)

    # AND THE INDIRECT CHANNEL, which counting imports alone does not see.
    # `forms.config(h)["rubric"]` used to hand out the MODULE OBJECT, and 101
    # call sites in 18 modules reach the rubric through it. This check, counting
    # `import` statements, would have read ZERO with every one of those still
    # live. The channel now serves a view onto the course file; this makes sure
    # it stays that way, because re-pointing one dict entry at a module would
    # silently restore all 101 dependencies and move no number.
    out = []
    try:
        import forms as _H

        for _h in _forms():
            served = _H.config(_h)["rubric"]
            if getattr(served, "__name__", "").startswith("rubric_h"):
                out.append(
                    f"forms.config({_h})['rubric'] serves the MODULE "
                    f"{served.__name__} again, not a view onto the course file. "
                    f"That is 101 call sites depending on a module Stage 5 "
                    f"deletes, and not one of them says so.")
    except Exception as exc:                        # pragma: no cover
        out.append(f"cannot check what config()['rubric'] serves: {exc}")

    n = len(consumers)
    if n > RUBRIC_CONSUMER_BUDGET:
        out.append(
            f"{n} rubric import SITE(S) outside the builders, against a budget "
            f"of "
            f"{RUBRIC_CONSUMER_BUDGET} -- a NEW dependence on modules Stage 5 "
            f"deletes: {', '.join(sorted(set(consumers))[:6])}")
    elif n < RUBRIC_CONSUMER_BUDGET:
        out.append(
            f"only {n} rubric import site(s) remain, against a budget of "
            f"{RUBRIC_CONSUMER_BUDGET} -- one was converted and the "
            f"ceiling was not lowered, which leaves room for a replacement to "
            f"arrive unnoticed")
    for fn in RUBRIC_BUILDERS:
        if not _os.path.exists(_os.path.join(here, fn)):
            out.append(f"RUBRIC_BUILDERS names {fn}, which does not exist")
    return out


def check_named_fixtures_still_name_something() -> list[str]:
    """Every fixture that names its target names an item this course still has.

    D2a's point is that a fixture naming a target stops testing anything the day
    that target changes, and says nothing. Nine fixtures stayed named, each for
    a reason recorded in `SELFTEST_NAMED_FIXTURES` -- a gold-bound cell, a
    filter inside a stub, a pairing that must match its mirror. The reasons are
    good; the exposure is the same. This is what closes it for them.

    THE WEAKER CHECK ON PURPOSE. It asks whether the id is still an item, not
    whether the item still has the shape the case needs -- that varies per case
    and is what the shape-picked conversions express directly. An id that has
    stopped existing is the failure that actually happened here: a case
    hard-coded a site, a conversion removed it, and the suite died before its
    first case.
    """
    # THE RULE LIVES IN LO-BLOCKS NOW. Goal K. The declaration is course data;
    # "a named target must still exist, and must say why it is named" is generic.
    # SELF-ASSEMBLED. Subgoal E63: the runner builds this payload itself,
    # from the same course records python would have read. The assembler was
    # compared against the payload python used to send and found IDENTICAL
    # before this fetch was deleted; `runner.SELF_ASSEMBLING` names the rules
    # that comparison has cleared, and the runner refuses any other.
    import lo_enforce

    return lo_enforce.run("named_fixtures_still_name_something", None)



# WHERE THE CARRIED-NOTE RATCHET LIVES, and it is a FILE rather than a table here
# for a measured reason: the tags are item ids, so a dict of them in this module
# is course data in engine code, and `course_inventory` said so the moment it was
# written -- "course data grew 10 -> 11; the ratchet only tightens". The counts
# belong beside the other budgets, in JSON, for the same reason
# `COURSE_DATA_BUDGET.json` is not a literal either.
import paths as _paths_cn

CARRIED_NOTES = _paths_cn.COURSE_CARRIED_NOTES


def check_carried_notes_are_intact() -> list[str]:
    """The carried commentary lost a block, or a tag.
    Reported as CARRIED COMMENTARY IS MISSING.

    THE SUCCESSOR TO `check_rubric_notes_match_the_modules`, which retired with
    the modules it compared against. Its subject moved; its purpose did not.

    SHAPE, NOT CONTENT. Recording the prose would make this a second copy and put
    it straight back in the position the move just ended. Recording the counts
    makes editing a note free -- which it should be, these are comments -- while a
    block that disappears is reported by name.

    FEWER IS A FAILURE AND MORE IS FINE: new reasoning gets written, and a check
    that objected to that would train its readers to update the number without
    reading why it moved.
    """
    # The rubric's carried commentary is a pair of counts; the tags are the
    # course's.
    import lo_enforce

    return lo_enforce.run("carried_notes_are_intact", None)


def check_rubric_notes_match_the_modules() -> list[str]:
    """The reasoning carried in the course file is still what the modules say.

    1,567 comment lines from the rubric's `ITEMS` literals, and 548 from the
    module headers, now live in the course file so that Stage 5 takes the DATA
    and not the record of why it is that data. Until the modules go, the same
    words exist in two places -- and two copies of anything drift.

    THIS RETIRES WITH THE MODULES, and deliberately: once `rubric_h1.py` and
    `rubric_h3.py` are gone there is nothing to compare against and the file is
    the only copy, which is the whole point of carrying them. While both exist,
    a comment edited in the module and not re-exported is exactly the silent
    divergence the export was written to prevent.
    """
    import ast as _ast

    import rubric_export as RX

    # STANDS DOWN WHEN THE MODULES GO, which is what "retires with them" has to
    # mean in code. It read them through `rubric_notes` and so crashed with
    # ModuleNotFoundError on the first deletion rehearsal -- a check whose whole
    # purpose is to expire, failing loudly at the moment it should fall silent.
    #
    # IT HAS EXPIRED, and its purpose has NOT. The modules are gone, so this
    # returns nothing on every run; the two copies it compared became one when the
    # commentary moved into `bmod_rubric.olx` as comments, which ends the drift it
    # watched for by construction. What survives the move is the other half of the
    # risk -- 2,115 lines of recorded reasoning going missing -- and
    # `check_carried_notes_are_intact` is where that lives now. A check whose
    # subject is deleted must hand its purpose on rather than take it with it.
    import os as _os

    present = [h for h in _forms()
               if _os.path.exists(_os.path.join(str(_HERE_DIR), f"rubric_h{h}.py"))]
    if not present:
        return []
    try:
        carried = RX.rubric_notes()
    except SystemExit as exc:                       # its own no-loss assertion
        return [f"the rubric notes cannot be lifted: {exc}"]
    except Exception as exc:                        # pragma: no cover
        return [f"rubric_export.rubric_notes raised {type(exc).__name__}: {exc}"]

    import coursedata

    # THROUGH THE ACCESSORS, not `_load()`. Reaching into the raw document is
    # the escape `check_course_schema_is_complete` exists to catch, and it
    # caught this one the first time it ran -- the third module to try it.
    out = []
    for iid, lines in sorted(carried["items"].items()):
        got = coursedata.rubric_notes(iid)
        if not got:
            out.append(f"the course file carries no notes for {iid}, and the "
                       f"rubric module has {len(lines)} line(s) of them")
        elif list(got) != list(lines):
            out.append(f"the notes for {iid} differ between the rubric module "
                       f"({len(lines)} lines) and the course file ({len(got)}) "
                       f"-- a comment was edited and not re-exported")
    for h, lines in sorted(carried["handouts"].items()):
        if list(coursedata.form_notes(h)) != list(lines):
            out.append(f"handout {h}'s header prose differs between the module "
                       f"and the course file -- re-export")
    return out


def check_every_enforcement_check_is_registered() -> list[str]:
    """Every `check_*` defined here is actually called by the audit.

    A check nobody calls is worse than no check: it reads as coverage, it passes
    review, and it never runs. The two counts have matched by discipline alone --
    nothing enforced it, and this module gained three checks on the day this was
    written, any one of which could have been left unwired with nothing to notice.
    """
    import ast as _ast

    out = []
    here = _ast.parse((_HERE_DIR / "enforcement.py").read_text())
    defined = {n.name for n in here.body
               if isinstance(n, _ast.FunctionDef) and n.name.startswith("check_")}
    try:
        audit_src = (_HERE_DIR / "equivalence.py").read_text()
    except OSError as exc:                       # pragma: no cover
        return [f"cannot read equivalence.py to verify registration: {exc}"]
    called = set(re.findall(r"ENF\.(check_\w+)", audit_src))
    for name in sorted(defined - called):
        out.append(f"{name} is defined but the audit never calls it -- an "
                   f"unregistered check reads as coverage and never runs")
    for name in sorted(called - defined):
        out.append(f"the audit calls {name}, which is not defined here")
    return out


def check_grader_input_pairings_are_declared() -> list[str]:
    """The grader/input pairing table still agrees with the corpora, both ways.

    lo-blocks declares no pairing -- a grader says `inputType` and whether it
    infers from children, and nothing says which inputs it takes -- so the table
    in `grader_inputs.py` is a hand declaration, and a hand declaration rots. It
    is held to evidence in both directions: a pairing declared with no example
    anywhere is a guess with a table around it, and a pairing DEMONSTRATED in a
    course and absent from the table is new evidence being absorbed instead of
    forcing a decision.

    This is the table the intake program will be steered by, which is why it is
    gated rather than left as a document.
    """
    try:
        import grader_inputs as GI
        import paths as _paths
        import shape_inventory as _SI
    except Exception as exc:                      # pragma: no cover
        return [f"the pairing declaration cannot be read: {exc}"]
    import os
    inv_path = os.path.join(_p7.SCORING_METADATA, "SHAPE_INVENTORY.json")
    if not os.path.exists(inv_path):
        return [f"{os.path.basename(inv_path)} is missing, so the pairing table "
                f"has nothing to check itself against -- which is not the same as "
                f"agreeing with it"]
    import json as _json
    inv = _json.load(open(inv_path))
    import olx_corpus
    roots = olx_corpus.default_roots()
    gone = olx_corpus.missing_roots()
    if not roots:
        return ["no corpus to mine: neither the lo-blocks checkout nor the course "
                "content is present, so the pairing table is unverifiable here"]
    # A DECLARED CORPUS THAT SHRANK IS A FINDING. Four course trees are declared;
    # if one is not checked out the evidence base quietly narrows and the table
    # passes against a smaller world than it claims to describe.
    return (gone + olx_corpus.roots_inside_the_data_store()
            + GI.verify(inv, GI.mine(roots, inv)))


def check_container_contents_are_declared() -> list[str]:
    """The containment table still agrees with the corpora.

    The structural half of the same problem `check_grader_input_pairings_are_
    declared` gates: **no block declares what it may contain** -- there is no
    `childTags`, no `allowedChildren`, no schema of permitted kids anywhere in
    lo-blocks. Containment is decided by each block's parser and runtime, so the
    declaration in `structure_kids.py` is made by hand against mined evidence and
    has to be held to it.

    It checks NESTING and REFERENCE separately. Conflating them made `Ref` look
    like the largest container in the corpus -- 431 TextAreas "inside" a block
    that holds nothing and points at everything.
    """
    try:
        import paths as _paths
        import structure_kids as SK
    except Exception as exc:                      # pragma: no cover
        return [f"the containment declaration cannot be read: {exc}"]
    import json as _json
    import os
    inv_path = os.path.join(_p7.SCORING_METADATA, "SHAPE_INVENTORY.json")
    if not os.path.exists(inv_path):
        return [f"{os.path.basename(inv_path)} is missing, so the containment "
                f"table has nothing to check itself against -- which is not the "
                f"same as agreeing with it"]
    inv = _json.load(open(inv_path))
    import olx_corpus
    roots = olx_corpus.default_roots()
    if not roots:
        return ["no corpus to mine, so the containment table is unverifiable here"]
    return (olx_corpus.missing_roots() + olx_corpus.roots_inside_the_data_store()
            + SK.verify(inv, SK.mine(roots, inv)))


def check_peg_authoring_formats_are_declared() -> list[str]:
    """The PEG content formats still agree with the engine's registry.

    The authoring surface a teacher actually writes in. Unlike the grader and
    containment tables, this mapping IS declared by the engine -- `generated/
    parserRegistry.ts` gives every extension its grammar, a display name and a
    `creatable` flag -- so the check reads that registry and holds three things
    to it: that every registered format says what a teacher writes in it, that no
    course uses an extension the engine does not register, and that no authored
    peg file is left unreachable.

    It caught `.textHighlightpeg` on its first run: three psych files in an
    extension lo-blocks registers NOWHERE, each byte-identical to a
    `.textSelectionpeg` beside it.
    """
    try:
        import olx_corpus
        import paths as _paths
        import peg_formats as PF
    except Exception as exc:                      # pragma: no cover
        return [f"the PEG declaration cannot be read: {exc}"]
    import os
    roots = olx_corpus.default_roots()
    if not roots:
        return ["no corpus to mine, so the PEG table is unverifiable here"]
    try:
        reg = PF.registry(str(_paths.LO))
    except SystemExit as exc:
        return [str(exc)]
    lo = os.path.abspath(str(_paths.LO))
    course_roots = [r for r in roots if os.path.abspath(r) != lo]
    return olx_corpus.missing_roots() + PF.verify(
        reg, PF.course_files(roots), PF.referenced_files(roots),
        PF.course_files(course_roots))


def check_gold_columns_are_the_item_labels() -> list[str]:
    """The gold sheets join to the rubric BY LABEL, and two tables say so.

    Measured 2026-09-18 against the graders' workbooks: for all 26 items,
    `label + " Score"` and `label + " Feedback"` are columns in that handout's
    sheet -- 52 of 52. The rubric's `label` field IS the teacher's column
    heading, which is how gold reaches an item at all.

    IT USED TO COMPARE TWO COPIES, and E58 step 3 (2026-09-25) removed the
    second one. `gold.HN_HEADER_TO_ITEM` was a hardcoded header->id table
    restating this same correspondence; this check held it to the rubric, and
    its own text said what should happen instead -- *"Under A2a the header map
    is DERIVABLE and should not be a stored table at all; until it is removed,
    this check holds the copy to the original."* `gold.header_to_item(form)`
    derives it now.

    SO THE CHECK ASKS THE WORKBOOK. Comparing a derivation to itself is worse
    than no check: it passes by construction and looks like coverage. What the
    copy was hiding is the question that was only ever measured by hand, once,
    on 2026-09-18 -- do these headings EXIST in the graders' sheet? A label
    edited for wording still breaks the join, and now the sheet is what says so.

    It does NOT read a data row. Headers only: the workbooks hold student work,
    and the participant ids beside it are the key that makes it identifiable.
    """
    # PORTED to `enforce/goldColumnsAreItemLabels.ts` (goal K).
    #
    # PYTHON KEEPS THE WORKBOOK READ, and that is the whole division of labour:
    # the graders' sheets are source documents holding student work, so the
    # engine must never open one. `tools/export_grader_columns.py` exports the
    # HEADINGS ALONE for a native caller; this path reads the live sheet, so a
    # workbook edited since the last export is still compared against.
    #
    # THE SELF-TEST SUBSTITUTES `gold._grid`, in memory, to make a sheet
    # unreadable -- another reason the read stays here.
    try:
        import coursedata as _C
        import gold as _G
    except Exception as exc:                      # pragma: no cover
        return [f"the gold header tables cannot be read: {exc}"]
    import lo_enforce

    labels: dict[str, dict[str, str]] = {}
    for it in _C.items():
        form, label = it.get("handout"), it.get("label")
        if form and label:
            labels.setdefault(str(form), {})[label] = it["id"]

    sheets: dict[str, dict] = {}
    for form, path in sorted({1: _G.H1_XLSX, 2: _G.H2_XLSX, 3: _G.H3_XLSX}.items()):
        try:
            grid = _G._grid(path)
        except Exception as exc:
            sheets[str(form)] = {"unreadable": f"{exc}"}
            continue
        header_row = min((r for r, _ in grid), default=None)
        if header_row is None:
            sheets[str(form)] = {"headings": []}
            continue
        # HEADERS ONLY. No data row is read, here or in the exporter: the rows
        # below hold student work and the ids that identify it.
        sheets[str(form)] = {"headings": sorted(
            {str(v).strip() for (r, _), v in grid.items()
             if r == header_row and str(v).strip()})}

    return lo_enforce.run("gold_columns_are_the_item_labels",
                          {"labels": labels, "sheets": sheets})

def rubric_parallel_widths() -> dict:
    """`{(item, stem): width}` for every enumerated slot family the RUBRIC has.

    A PARALLEL FAMILY is a criterion asked more than once -- `reason_1/2/3`,
    `antecedent_1/2`, `example_1/2`. The width is how many the rubric actually
    declares, read off the slots themselves rather than assumed.
    """
    import re
    import coursedata

    out: dict = {}
    for it in coursedata.items():
        iid = str(it.get("id"))
        names = set()
        for g in (it.get("counts") or ()):
            names |= {str(s) for s in (g.get("slots") or ())}
        for c in (it.get("credit") or ()):
            if c.get("what"):
                names.add(str(c["what"]))
        for n in names:
            m = re.fullmatch(r"(.+?)_(\d+)", n)
            if m:
                key = (iid, m.group(1))
                out[key] = max(out.get(key, 0), int(m.group(2)))
    return out


def check_enumerated_slots_cover_the_rubric() -> list[str]:
    """A declaration table built by `for n in (1, 2, 3)` that the rubric outgrew.
    Reported as ENUMERATION SHORTER THAN THE RUBRIC.

    SUBGOAL E60, and it exists because of a FALSE POSITIVE. Removing the
    hardcoded form count scanned for `(1, 2, 3)` and classified sixty-nine sites
    as form iterations; four were not. They enumerate SLOTS -- `sentence_{n}`,
    `example_{n}`, `reason_{n}` -- and encode a different claim entirely: that a
    criterion has at most three parallel checks.

    THE CEILING IS NOT WRONG TODAY, which is why this is a check and not a fix.
    It matches the corpus: eleven families, widths 2 and 3. Raising it to five
    would be the same mistake one number further out. What was missing is
    anything that NOTICES when the rubric outgrows the enumeration -- a
    criterion with a fourth parallel slot would simply not be built, and the
    table would be silently SHORT rather than loudly wrong. That is the form
    count's shape exactly: a hardcoded range does not fail on a longer course,
    it stops early and reports clean on the rest.

    CONTIGUOUS-FROM-ONE IS THE DISCRIMINATOR, and it is a heuristic stated as
    one. A table that enumerates `1..k` for a family looks like a loop that ran
    out; a table naming a SELECTION -- slots 1 and 3, or slot 2 alone -- is a
    deliberate choice about which entries diverge, and is left alone. Only the
    first shape is reported, so a partial declaration is never mistaken for a
    truncated one.

    EVERY DECLARATION TABLE, not a named one. The tables are read from
    `rubric_export.DECLARATION_TABLES`, so a new table keyed by `(item, slot)`
    is covered the day it is added -- the same reason `DATA_MODULES` and
    `GENERIC_DOCS` were made to read their lists of record rather than restate
    them.
    """
    # A table short of the rubric is correct as far as it goes and governs
    # nothing past its end.
    import lo_enforce

    return lo_enforce.run("enumerated_slots_cover_the_rubric", None)


def check_property_vocabulary_has_not_grown() -> list[str]:
    """D1x-c's ratchet: how much course SHAPE the flag vocabulary carries.

    A single branch on a property is not a defect -- `if caps["boxes"] == 8:`
    reads a value and a second course with six boxes works. The harm is
    ACCUMULATION: forty narrow booleans mean the engine is course-shaped
    again in a new vocabulary. So the count of DISTINCT properties reached in a
    branch may fall and may not rise without a declaration.

    NARROW ON PURPOSE, and it says so in its own output. It matches subscripts
    only, because `coursedata` returns dicts -- an earlier version matched
    attributes too and every attribute hit was a false positive (`args.handout`,
    Python's own `node.value.id`). It cannot see indirection through a local.
    A gate that caught only naive violations while announcing the rule enforced
    would turn "be careful here" into "the check passed".
    """
    try:
        import property_ratchet as PR
    except Exception as exc:                      # pragma: no cover
        return [f"the property ratchet cannot be read: {exc}"]
    premise = PR.premise_holds()
    if premise:
        return premise
    return PR.verify(PR.scan())


def check_course_schema_is_complete() -> list[str]:
    """Every item field is in a declared group, and no module crosses the boundary.

    §9.2a obligations 1 and 3. Obligation 2 belongs to `coursedata`, which cannot
    gate itself. Obligation 3 had been assigned to no tool at all, and a rule with
    no tool is a comment.

    Part A reports an undeclared field as a VIOLATION and a stale declaration as a
    CLEANUP, separately -- merging them would let a real violation hide in a list
    of tidying. Part B catches a GENERATOR field read off a rubric result, and the
    raw-entry escape, which defeats the boundary while still calling the reader.

    Until Stage 4 fills GENERATOR_FIELDS this cannot fail on real data, which is
    why `course_schema.py --self-test` constructs all four conditions itself.
    """
    try:
        import course_schema as CS
    except Exception as exc:                      # pragma: no cover
        return [f"the course schema check cannot be read: {exc}"]
    return CS.check()["violations"]


def check_cross_file_anchors_resolve() -> list[str]:
    """G1c: a course file's pointer into the general prose still lands.

    Anchors exist because `guide.renumber()` derives labels from DOCUMENT ORDER,
    so inserting a section renumbers everything after it. `_cited_by()` finds and
    fixes every citer it can see -- and a course file in `courses/<id>/` is a
    citer it CANNOT see, so a renumber would silently invalidate its pointers.

    A dangling `see: qc:NAME` FAILS. An unused alias is summarised, not failed:
    one anchor per GOALS.md entry means "pointed at by nothing yet" is the normal
    state until courses exist to do the pointing.

    It also checks anchors sit on their OWN LINE, which is what makes them
    survive renumbering -- a property that can be verified, rather than a promise
    about `renumber()` that cannot.
    """
    try:
        from tools import anchors as A
    except Exception as exc:                      # pragma: no cover
        return [f"the anchor gate cannot be read: {exc}"]
    failures, _warnings = A.verify(A.scan())
    return failures + A.anchors_are_renumber_safe()


def check_general_prose_has_no_course_vocabulary() -> list[str]:
    """F1's PRECONDITION: no course vocabulary in the engine's general prose.

    It enforces the condition that makes F1 checkable, not F1 itself. §10.3.2
    sorts a course-derived sentence into specification, incident or split, and a
    word list cannot tell those apart -- which remedy applies is a human
    decision.

    INERT UNTIL STAGE 7'S SPLIT, and it says so rather than reporting clean:
    before the split there is no general half, and the course halves are supposed
    to be full of course vocabulary. It REFUSES outright if the changelog is missing,
    because a gate that strips sentences while their destination is undefined
    produces deletions rather than moves.

    `behaviour` must be unambiguous -- `code behaviour`, a named function's
    behaviour. A bare `behaviour` is the single most likely course word to slip
    through, and excluding it by WORD (as the measurement does) would be a false
    negative exactly where the risk is highest.
    """
    try:
        import prose_vocabulary as PV
    except Exception as exc:                      # pragma: no cover
        return [f"the prose vocabulary check cannot be read: {exc}"]
    got = PV.check()
    return got["blocked"] + got["findings"]


# The ONE place the old environment names may still appear: the table in
# `paths.py` that honours them. Everything else was renamed in Stage 9.
OLD_ENV_NAMES_ALLOWED = {
    "scoring/paths.py": "the fallback table itself -- it is what honours the old "
                        "names, so it has to know them",
    "SCORING_REFACTOR_PLAN.md": "it DOCUMENTS the rename, so it has to name what "
                                "was renamed. The same shape as the anchor gate "
                                "failing on the plan's own `see: qc:NAME` "
                                "example: a convention's specification uses the "
                                "convention.",
    "RUBRIC_MIGRATION_PLAN.md": "the earlier plan, a historical record of when "
                                "the old names were current",
    "ADOPTION_POSTMORTEM.md": "it RECORDS a defect whose symptom was the literal "
                              "the old data-directory variable appearing where "
                              "it should not -- one "
                              "instrument hardcoded it and one frontmatter line "
                              "carried it. Rewriting those two mentions to "
                              "COURSE_* would make the post-mortem describe a bug "
                              "that could not have happened. Same shape as "
                              "SCORING_REFACTOR_PLAN.md above.",
    "migration/goldens/audit_baseline.json": "THE FREEZE CANNOT PASS ITS OWN "
        "CHECK. This file is the frozen finding SET, stored verbatim, and the "
        "findings quote the paths and names they are about -- including this "
        "check's own message, which necessarily spells the old name out. So "
        "writing "
        "the baseline CREATED a finding that the baseline does not contain, and "
        "the number was stale the instant it was written: 52 frozen against a tree "
        "that then read 53. It is also gitignored, so 'must not return to the "
        "repo' was never about it. Declared rather than scoping the walk to "
        "tracked files, because an allowlist entry is visible and a silent scope "
        "change is not.",
}


def check_the_staged_rubric_is_current() -> list[str]:
    """The rubric the scorer reads is the rubric that was authored.

    THIS ONE WATCHES THE SERVED COPY, the one a learner's page is built from.
    `coursedata.items()` reads the EXPANDED, UNRESOLVED artifact instead --
    `check_the_expanded_rubric_is_current` is the check on that link. Both exist
    because the two copies go stale independently: a build that expands but does
    not resolve leaves the pages stale, and the reverse leaves the scorer stale.

    IT COMPARES AGAINST THE AUTHORED FILE, not against the view. It is now one of
    only two checks on this chain: `check_the_component_reproduces_the_view`
    retired at step 3d with the course file's rubric fields, because a check
    comparing the component against a copy that no longer exists reports zero and
    tests nothing.

    THE AUTHORED SIDE IS RESOLVED BEFORE COMPARING, because the staged copy has
    had its corpus references expanded and the authored one has not. Comparing raw
    would report every referenced span as a difference.
    """
    import os as _os
    out = []
    try:
        import corpus_resolve as CR
        import rubric_component as RC
    except Exception as exc:                            # pragma: no cover
        return [f"cannot check the staged rubric: {type(exc).__name__}: {exc}"]

    # THE COURSE'S OWN NAME FOR IT. `paths.RUBRIC_COMPONENT` is declared in the
    # content manifest; spelling the stem here put one course's filename in
    # engine code.
    authored = _os.path.join(str(_p7.roots().location), _p7.RUBRIC_COMPONENT)
    if not _os.path.exists(authored):
        return [f"{_os.path.relpath(authored)} is missing: there is no authored "
                f"rubric to stage"]
    staged = RC.staged_path()
    if not _os.path.exists(staged):
        return [f"the rubric has not been staged ({staged}); run "
                f"`npm run build:stage-content`. The scorer reads the staged copy, "
                f"so an unbuilt tree scores against nothing"]

    def resolved(x):
        if isinstance(x, str):
            return CR.expand(x) if "{{corpus:" in x else x
        if isinstance(x, list):
            return [resolved(v) for v in x]
        if isinstance(x, dict):
            return {k: resolved(v) for k, v in x.items()}
        return x

    try:
        want = [resolved(i) for i in RC.as_view_items(authored)]
        have = RC.as_view_items(staged)
    except Exception as exc:
        return [f"cannot compare the authored rubric with the staged one: "
                f"{type(exc).__name__}: {exc}"]
    if [i["id"] for i in want] != [i["id"] for i in have]:
        return [f"the staged rubric holds different items from the authored one "
                f"({len(have)} staged, {len(want)} authored) -- rebuild"]
    byid = {i["id"]: i for i in have}
    for w in want:
        h = byid.get(w["id"])
        if h != w:
            diff = sorted(k for k in set(w) | set(h) if w.get(k) != h.get(k))
            out.append(
                f"{w['id']}: the staged rubric differs from the authored one on "
                f"{diff[:4]} -- the scorer is reading a rubric that was edited "
                f"since the last build. Run `npm run build:stage-content`.")
    return out


def check_the_expanded_rubric_is_current() -> list[str]:
    """The rubric the SCORER reads is the rubric that was authored.

    `coursedata.items()` reads `.stage/expanded`, which is a build product, so
    scoring now depends on a build having run -- it did not before, and
    RUBRIC_MIGRATION_PLAN's END STATE accepted that when it named this
    artifact as owed.
    A stale expansion means a stale rubric silently: every item still parses,
    every slot still reads, and the scores describe a rubric nobody is editing.

    IT COMPARES THE BYTES, and that is exact only while no template exists. With
    nothing to expand, `materialiseRubrics` copies the file through unchanged --
    it is written not to reformat, and its own test asserts byte-identity -- so
    any difference at all is staleness.

    THE COMPARISON EXPIRES THE DAY A TEMPLATE LANDS, and says so rather than
    quietly becoming wrong: an expanded file SHOULD differ from its source then,
    and this check would read that as staleness on every run. Upgrading it means
    running the expander and comparing its output, which is a node call from
    python -- deliberately not built today, because a check nothing exercises is
    a check nobody finds out is broken. The refusal below is what makes the
    upgrade unavoidable instead of merely noted.
    """
    # A stale expansion is a stale rubric, silently; the bytes must match while
    # no template exists.
    import lo_enforce

    return lo_enforce.run("the_expanded_rubric_is_current", None)


# `check_the_component_reproduces_the_view` STOOD HERE AND RETIRED AT STEP 3D,
# on the expiry its own docstring set: "only runnable while BOTH sources exist".
# It compared the component field-for-field against `course.json`'s `items[]`,
# after resolution, and passing is what licensed deleting those fields. With them
# gone there is nothing on the course side to compare against, so keeping it would
# have left a check that runs, reports zero, and tests nothing -- the vacuity this
# file fails a ratchet over. Its last passing run is the one recorded in the
# commit that re-pointed `coursedata`.
#
# WHAT GUARDS THE COMPONENT NOW. Not a second copy -- there isn't one, which was
# the point. `check_the_staged_rubric_is_current` watches the build link,
# `check_the_course_links_the_rubric_and_every_handout` the structure, and the
# scoring equivalence suite exercises the rubric through 5,668 re-scored responses
# and 3,120 paper-vs-web cells: a rubric that changed meaning changes scores.


def check_sheet_matches_the_rubric_it_names() -> list[str]:
    """Each `<LLMAction rubricDef=>` names a rubric entry, and they agree.

    The generated sheet and the rubric component are TWO PROJECTIONS of one
    definition. The attribute names the source so a consumer can derive its own
    projection instead of restating it -- and this is the consumer that makes the
    naming worth anything: it compares the sheet's slot keys against the rubric
    entry's, and reports a divergence rather than letting two descriptions of one
    rule drift apart in silence.

    IT READS THE STAGED, EXPANDED RUBRIC, not the authored file. Templates are
    expanded by the build on purpose -- "a second implementation of one rule is
    the drift this whole model exists to end" -- so a reader that understood the
    template grammar would be that second implementation.

    A MISSING BUILD IS NOT A PASS. If the artifact has not been staged this says
    so and returns a finding, because a reader that quietly finds nothing is how
    an empty result comes to look like a clean one.
    """
    out = []
    try:
        import agreement as A
        import olx_prompts as O
        import rubric_component as RC
    except Exception as exc:                            # pragma: no cover
        return [f"cannot compare the sheet against the rubric: "
                f"{type(exc).__name__}: {exc}"]
    try:
        rubric = RC.load()
    except FileNotFoundError:
        return [f"the rubric component has not been staged ({RC.staged_path()}); "
                f"run `npm run build:stage-content` -- an unbuilt artifact is not "
                f"evidence that the sheet and the rubric agree"]
    except Exception as exc:
        return [f"the staged rubric component will not parse: "
                f"{type(exc).__name__}: {exc}"]
    # A SKIP IS NOT A PASS, and the first version of this check was proof. It said
    # `HANDOUT[item]`, which does not exist in this module -- the name lives in
    # `olx_prompts` -- so every item raised NameError, a bare `except: continue`
    # swallowed it, and the check reported 0 findings while comparing NOTHING. Two
    # injected failures, a dropped slot and a rubricDef naming no item, both came
    # back clean. So the exception is REPORTED now: an item whose action cannot be
    # loaded is a finding, because the alternative is a check that cannot fail.
    for item in sorted(O.ACTION):
        try:
            act = A.load_action(_p7.handout_olx(O.FORM[item]), O.ACTION[item])
        except Exception as exc:
            out.append(f"{item}: cannot load its action to compare against the "
                       f"rubric: {type(exc).__name__}: {exc}")
            continue
        named = act.get("rubric_def")
        if not named:
            out.append(f"{item}: its <LLMAction> names no rubricDef, so nothing "
                       f"ties the sheet to a rubric entry")
            continue
        entry = rubric.get(named)
        if entry is None:
            out.append(f"{item}: rubricDef={named!r} names no <Item> in the "
                       f"staged rubric -- the sheet points at nothing")
            continue
        sheet = {s.get("key") for s in (act.get("slots") or [])
                 if isinstance(s, dict) and s.get("key")}
        declared = {s.get("key") for s in entry.get("slots", []) if s.get("key")}
        if sheet and declared and sheet != declared:
            only_sheet = sorted(sheet - declared)
            only_rubric = sorted(declared - sheet)
            out.append(
                f"{item}: the sheet and rubric entry {named!r} describe different "
                f"slots -- sheet only {only_sheet}, rubric only {only_rubric}")
    return out


def check_the_course_links_the_rubric_and_every_form() -> list[str]:
    """The rubric is IN the course, beside the three handouts it scores.

    This is the shape the migration exists to reach, and it is one `<Use ref>`
    away from silently not holding. The handouts reached students as three
    independent routes for months while `course.json` described them as one
    course -- the data said "course" and the content said "three activities", and
    nothing compared the two. A rubric that is not linked still builds, still
    resolves, and still scores nothing.
    """
    # PORTED AND SELF-ASSEMBLED (goal K, step 8). The component, rubric and
    # handout filenames are manifest keys now, not engine defaults; the
    # assembler reads them and the wanted links match python's course_links()
    # exactly.
    import lo_enforce

    return lo_enforce.run("the_course_links_the_rubric_and_every_form", None)


# `check_the_rubric_component_is_current` STOOD HERE AND RETIRED AT STEP 3D, on
# the expiry it wrote for itself: "Retire it in the same commit that stops
# generating the file... On that day this check is not merely obsolete, it is
# WRONG -- it would refuse the first hand edit, which is the entire point of the
# change." `rubric_export --olx` retired in the same commit, and the course file
# it rendered from no longer carries a rubric, so the check could only have
# compared the component against an empty render of itself.
#
# Kept as a note because the last check to carry an expiry --
# `check_selectors_govern_something`, "it dies with the modules at Stage 5" -- is
# the reason anyone noticed its premise had changed. An expiry that is honoured
# silently teaches nothing.


def check_no_old_environment_names() -> list[str]:
    """`MOLLY_*` does not come back after Stage 9's rename.

    Without this the old name returns by copy-paste from a runbook and nobody
    notices until the fallback is removed -- at which point the failure is an
    EMPTY RESULT, and empty results in this project look like clean passes.

    The fallback in `paths.py` is deliberately not a transition courtesy: these
    variables live in shells, cron entries and the command lines of jobs already
    running, where a repo-wide rename cannot reach. This check governs the repo;
    the fallback governs everything else.
    """
    import os
    import re

    repo = os.path.dirname(_HERE_DIR)
    pat = re.compile(r"\bMOLLY_(?:DATA|OUT|MEDIA)\b")
    out = []
    _skip = {str(s) for s in _p7.walk_prune_dirs(repo)}
    for dirpath, dirnames, filenames in os.walk(repo):
        dirnames[:] = [d for d in dirnames
                       if os.path.realpath(os.path.join(dirpath, d)) not in _skip]
        dirnames[:] = [d for d in dirnames
                       if d not in (".git", "node_modules", "__pycache__")]
        for fn in filenames:
            if not fn.endswith((".py", ".md", ".sh", ".json", ".yaml", ".olx")):
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, repo)
            if rel in OLD_ENV_NAMES_ALLOWED:
                continue
            try:
                hits = pat.findall(open(path, errors="ignore").read())
            except OSError:
                continue
            if hits:
                out.append(
                    f"{rel} uses {sorted(set(hits))} -- Stage 9 renamed these to "
                    f"COURSE_*. The old name is still honoured at runtime by "
                    f"paths.env_renamed, but it must not return to the repo: when "
                    f"the fallback goes, the failure is an empty result, and empty "
                    f"results here look like clean passes.")
    return out


def check_declaration_tables_are_verified() -> list[str]:
    """RETIRED. `probe_declaration_tables` already answers this, and better.

    This compared against a record produced by `table_sensitivity.py`, which was
    written without noticing that the established probe existed. The probe solves
    three defects that tool had, each named in its own comments:

      * verifiers that TAKE ARGUMENTS -- it fills them from `all_items()`, where
        the newer tool excluded them as "uncallable". Its comment is the bug
        verbatim: "a raising verifier looks exactly like an unread table";
      * comparison BY CONTENT, not by count -- "emptying a table produces
        findings of its own ... a count comparison would read those as evidence
        the table is read, which is the opposite of the truth". The newer tool
        compared counts;
      * emptying IN PLACE, not by `setattr` -- "a verifier may hold its own
        reference to the object; setattr alone would leave that reference
        pointing at the original and the probe would report a false INERT". The
        newer tool used setattr.

    It is also registry-driven, so it covers 61 tables across four modules where
    the newer tool saw only `enforcement`; and it is re-entrancy guarded, because
    two of the tables it probes are its own.

    Measured difference: the newer tool reported four or five tables "verified by
    nothing". The probe reports ONE, and it is `DATA_MODULES` -- added the same
    night the newer tool was.

    Run `python3 enforcement.py --probe-declarations`. It is deliberately not in
    the default audit: three passes of every verifier over every table is
    minutes, and the pre-commit path has to stay usable.
    """
    return []


def check_migrated_tables_match_their_source() -> list[str]:
    """Every table read from the course file equals the authored table it came from.

    A MIGRATION NEEDS A TEST PER TABLE. Three tables moved on 2026-09-19 behind
    ONE behavioural test -- 26 paper prompts, identical -- and it passed while
    `agreement_app.CONTEXT_SOURCE`'s values had turned from tuples into lists,
    because no paper prompt reads that table. Four more in `olx_prompts` had
    drifted the same way and nothing had noticed.

    The pairs are discovered by AST, not listed: a migrated table is an
    assignment whose value calls one of the reader helpers, so a table moved
    tomorrow is covered tomorrow without editing anything.

    It compares the two sides and does not know which is right: an authored copy
    edited to match a bad migration would pass.
    """
    try:
        import migrated_tables as MT
    except Exception as exc:                      # pragma: no cover
        return [f"the migrated-table check cannot be read: {exc}"]
    return MT.verify()


if __name__ == "__main__":
    import json
    import sys

    if "--probe-declarations" in sys.argv:
        # E32. Deliberately NOT part of the default run: three passes of every
        # verifier over every table is minutes, and the pre-commit path has to
        # stay usable. Exits 1 when a registered declaration enforces nothing.
        lines = probe_declaration_tables()
        print("DECLARATION PROBE — does each verifier actually read its table?\n")
        print("\n".join(lines))
        raise SystemExit(1 if any(l.startswith("  INERT") for l in lines) else 0)

    print(json.dumps(cli_signatures(), indent=1))
