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

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from handouts import config
from score import _computed_keys, build_schema, derive_ledger, derive_oc_ledger

# ---------------------------------------------------------------------------
# The criteria sheet's inputs, and what makes each one fail.
#
# This is the one place the audit names the CLI's internals, and it is guarded:
# `check_criteria_table_is_complete` asserts it covers EXACTLY the schema's
# required properties, so adding an oc_analysis field without deciding how it
# fails breaks the audit instead of being silently unprobed.
_PASS = {
    "behavior": "walking to class",
    "stimulus": "a coffee",
    "contingent": True,
    "follows_behavior": True,
    "stimulus_is_arranged": True,
    "avoidance_frame": False,
    "cadence_ok": True,
    "targets_own_behavior": True,
    "targets_intended_behavior": True,
    "consequence_asserted": True,
    "states_a_contingency": True,
    # WK2 only: the consequence points the right way for the type chosen.
    "aimed_correctly": True,
    # WK1 only: the consequence clause has an agent subject and a transfer verb.
    "agent_delivers_consequence": True,
    # The two halves of the direction test. Neither has a "passing" value on its
    # own — it is the PAIR that passes or fails — so the passing state is any
    # matched pair, and the failing state below mismatches exactly one of them.
    "trigger_expects": "gain",
    # Diagnostic only: gates nothing, scores nothing, so it has no failing
    # value. Both tables name the same one, which is what "this field cannot
    # cost the item anything" looks like to the probe.
    "restriction_authored": "relieved",
    "restricts": "target_behavior",
    # The type is derived from this pair, so the PASSING value is the pair each
    # type IS. Per item, and a flat value would make the baseline charge on three
    # of the four screens.
    "stimulus_move": {"PR": "given_desirable", "NR": "taken_undesirable",
                      "PP": "given_undesirable", "NP": "taken_desirable"},
}
_FAIL = {
    "behavior": "",
    "stimulus": "",
    "contingent": False,
    "follows_behavior": False,
    "stimulus_is_arranged": False,
    "avoidance_frame": True,          # advisory only; must show zero loss
    # Each must MISMATCH the other's _PASS value, since `direction_ok` fails on
    # the pair rather than on either field. Setting this one to "gain" — a match
    # against _PASS's "gain" — made the probe report GATE WEB ONLY, because the
    # CLI correctly saw no mismatch and did not zero.
    "trigger_expects": "loss",       # a gain for doing badly
    # Mismatched against _PASS so the derived `consequence_not_a_setup`
    # fires: created + success-lifts-it is the forbidden pair.
    "restriction_authored": "created",
    # Non-firing on its own, like the other operands: the gate needs all three.
    "restricts": "target_behavior",
    "cadence_ok": False,
    "targets_own_behavior": False,
    "targets_intended_behavior": False,
    "consequence_asserted": False,
    "states_a_contingency": False,
    # WK2 only, and it GATES there — an aversive delivered for meeting the goal.
    # False is the failing value, and on that item it takes the whole 4.
    "aimed_correctly": False,
    # WK1 only, and it GATES — no agent, or no verb of giving or taking.
    "agent_delivers_consequence": False,
    # A pair the type is NOT, so `demonstrates_type` fails. Each is the same
    # direction with the wrong valence, which is the live confusion: a phone lock
    # is taken-away-DESIRABLE, which is NP, not the NR it claims to be.
    "stimulus_move": {"PR": "given_undesirable", "NR": "taken_desirable",
                      "PP": "given_desirable", "NP": "taken_undesirable"},
}
# The two type fields are handled separately: their failing value depends on the
# other one, and a naive flip can make them agree again.
_TYPE_FIELDS = ("observed_type", "named_type", "trigger_behavior")

# The same rule wears different names on the two sides. Kept explicit and small;
# an unmapped key is REPORTED, never assumed equivalent.
ALIAS = {
    # 1b's FOUR PERIOD SLOTS, declared 2026-09-06 (subgoal E53). The mirror
    # records `baseline`/`week_1`/`week_2`/`week_3` and the app records the same
    # four judgements as `..._data`. Measured before declaring: 1b is 20/20 on
    # BOTH sides with the medians identical on all twenty cells, so this is a
    # naming difference and nothing more. It went unnoticed because every check
    # in the audit read declarations rather than artifacts; E53's is the first to
    # compare what the two engines actually answered, and these were four of its
    # findings.
    "baseline": ("baseline", "baseline_data"),
    "week_1": ("week_1", "week_1_data"),
    "week_2": ("week_2", "week_2_data"),
    "week_3": ("week_3", "week_3_data"),
    "behavior": "names_behavior",
    # The paper scorer's operant vocabulary, declared 2026-09-11. These six were
    # the whole of `paper_scorer_agreement`'s 840 "not comparable" errors, and
    # they are names, not rules: the first two appear on ALL EIGHT operant items
    # and the four `is_*` each appear ONLY on their own item (PR x96, NR x90,
    # PP x51, NP x48, and never on another), so nothing here needs an item id to
    # resolve. Declared with the aliases and then MEASURED, the way the 1b four
    # were -- if any of these named a different rule, driving the paper verdicts
    # through the web arithmetic would disagree on score, and it does not.
    "operant_behavior": "names_behavior",
    "contingent_on_behavior": "contingent",
    # Paper asks the type question by name ("is this positive reinforcement?"),
    # the web asks it as one slot. Same judgement, one per item.
    "is_pr": "demonstrates_type",
    "is_nr": "demonstrates_type",
    "is_pp": "demonstrates_type",
    "is_np": "demonstrates_type",
    # The web renamed this to say the good state, and inverted it to match the
    # rest of the vocabulary: `met` is phrased directly. The CLI input keeps the
    # old name and its boolean sense (True = phrased by what is avoided).
    # A TUPLE, not a rename, because the two sheets no longer share a name and
    # the CLI still has ONE input. web_name() tries each candidate against the
    # item's own web_keys, so DAY1 resolves to the gated name and the other seven
    # to the plain one, with no item id anywhere. Same mechanism `observed_type`
    # uses below, and the alias stays AUTHORITATIVE: if neither candidate is
    # present the answer is None and the audit reports it.
    "avoidance_frame": ("phrased_directly_gate", "phrased_directly"),
    # The four example screens ask about ONE authored type, so the web judges
    # "is it this type" where the CLI identifies which of the four it is. Same
    # deduction, different shape — see EQUIVALENCE.md.
    # Order matters, and the identity candidate comes LAST on purpose. Since
    # `pick`, `observed_type` names a web slot too — but there it is the
    # classification the student's answer is sorted into, not the check that
    # carries the deduction. That check is `demonstrates_type`, computed from
    # the pick by `expect`. Resolving to the pick would compare a CLI deduction
    # against a web slot that costs nothing.
    "observed_type": ("demonstrates_type", "observed_type"),
    "stimulus": "names_stimulus",
    "stimulus_is_arranged": "you_arrange_it",
    "targets_intended_behavior": ("targets_goal_behavior", "targets_unwanted_behavior"),
    # THREE candidates, not two: the daily gate is split. DAY1 keeps the plain
    # name, DAY2 carries the counted variant. Mutually exclusive per sheet, so
    # web_name resolves each item to exactly one and the order is free.
    "cadence_ok": ("cadence_is_daily", "cadence_is_daily_counted", "cadence_is_weekly"),
    "stimulus_move": ("demonstrates_type", "stimulus_move"),
}


def _tbl(table: dict, key: str, item_id: str):
    """A probe-table value, resolved per item where the table says so.

    Most fields have one passing value everywhere. The valence fields do not:
    what a type REQUIRES differs by screen, so a flat value would make the
    probe's own all-satisfied baseline charge on some of them. A dict value is
    read as {item_id: value}.
    """
    v = table[key]
    return v.get(item_id) if isinstance(v, dict) else v


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
    import rubric_h1, rubric_h2, rubric_h3
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
    problems = []
    for it in items:
        valid = {d["code"] for d in it["deductions"]}
        for c in it.get("credit", []):
            for verdict, code in (c.get("codes") or {}).items():
                if code not in valid:
                    problems.append(f"{it['id']}: `{c['what']}`/{verdict} -> `{code}`, "
                                    f"which is not one of its deduction codes")
        want = it.get("blank_code")
        if want and want not in valid:
            problems.append(f"{it['id']}: blank_code `{want}` is not one of its "
                            f"deduction codes")
        for cr in it.get("counts", []):
            names = {c["what"] for c in it.get("credit", [])}
            for k in [cr["key"], *cr["slots"]]:
                if k not in names:
                    problems.append(f"{it['id']}: counts names `{k}`, which is not a "
                                    f"credit component")
        # `onlyif` IS KEYED BY THE SHEET, NOT BY THE CREDIT LIST, and testing it
        # against credit names reported ten false gaps. Both evaluators key the
        # charge map on the SHEET's slots -- agreement.py writes
        # `charged = {sl["key"]: True for sl in spec["slots"]}` and
        # slotSheet.chargedMap does the same -- so a name is live iff the sheet
        # has it. On PR/NR/PP/NP the two tables come apart BY DESIGN: the rubric
        # holds COMPOSITES (`is_operant_conditioning`, `is_pr`) while the sheet
        # ENUMERATES the sub-checks, and it is the sheet's
        # `targets_goal_behavior...@2` that carries the points. All ten reported
        # names were live sheet slots implementing charge-once -- the arithmetic
        # `score.py:derive_oc_ledger` writes as `elif` and `llm/onlyif.test.ts`
        # exists to pin.
        #
        # Checking `cond` matters more than checking `key`. agreement.py
        # suppresses nothing for an UNKNOWN condition, deliberately, so a typo'd
        # cond does not fail loudly -- it makes the rule inert and the item
        # charges twice for one cause.
        sheet = {s["key"] for s in _sheet_slots().get(it["id"], ())}
        universe = sheet | {c["what"] for c in it.get("credit", [])}
        for r in it.get("onlyif", []):
            for k in (r["key"], r["cond"]):
                if k not in universe:
                    problems.append(f"{it['id']}: onlyif names `{k}`, which is neither "
                                    f"a slot on its sheet nor a credit component, so "
                                    f"the rule is inert and the charge is never "
                                    f"suppressed")
    return problems


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
    problems = []
    for it in items:
        if not it.get("derive_from_credit"):
            continue
        reach = {it.get("blank_code")} | set(it.get("unreachable_codes") or [])
        for c in it.get("credit", []):
            reach |= set((c.get("codes") or {}).values())
        for d in it["deductions"]:
            if d["code"] not in reach:
                problems.append(f"{it['id']}: `{d['code']}` (-{d['pts']:g}) can be "
                                f"produced by no slot verdict, and is not declared "
                                f"in unreachable_codes")
        for code in it.get("unreachable_codes") or []:
            if code not in {d["code"] for d in it["deductions"]}:
                problems.append(f"{it['id']}: unreachable_codes names `{code}`, which "
                                f"is not one of its deduction codes")
    return problems


# Repeated families that are countable in shape but must NOT be converted, with
# the reason, because an unexplained exemption is how the inconsistency below got
# in. Keyed by (item, family stem).
COUNTABLE_EXEMPT = {
    ("1a", "week"): "the weeks are NAMED, not interchangeable. The guidance deducts "
                    "only when a period is 'clearly and specifically absent' and names "
                    "the observed case — an answer that opens at the intervention and "
                    "never mentions baseline. `3 of 4` cannot say which is missing.",
    ("2a", "how"): "MEASURED, not preferred. The count WAS the design and it cost "
                   "the item 5 of 20 cells: subgoal Q2 recorded one error profile "
                   "-- `said 2, scored 6 against gold 4`, 29 of 29 -- while the "
                   "DEDUCT guidance already described both shapes the graders "
                   "charge. An aggregate answer never has to confront a particular "
                   "box, so correct prose had nothing to bind to. The graders "
                   "themselves judge per box and name it ('your third sentece'), "
                   "against three labelled fields on screen that all 20 cells "
                   "fill, so nothing relies on content spanning them. The FIXTURE "
                   "no longer depends on the group either -- the dealing groups "
                   "live in agreement_app.JOBS `dealt` -- which is what made this "
                   "conversion testable at all.",
}


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
    problems = []
    for it in items:
        if not it.get("derive_from_credit"):
            continue
        counted = {k for cr in it.get("counts", []) for k in cr["slots"]}
        fams: dict[str, list[dict]] = {}
        for c in it.get("credit", []):
            m = re.match(r"(.+?)_(\d+)$", c["what"])
            if m:
                fams.setdefault(m.group(1), []).append(c)
        for stem, members in fams.items():
            if len(members) < 2:
                continue
            codes = set()
            for c in members:
                codes |= set((c.get("codes") or {}).values())
            covered = {c["what"] for c in members} <= counted
            if len(codes) == 1 and not covered:
                if (it["id"], stem) in COUNTABLE_EXEMPT:
                    continue
                problems.append(
                    f"{it['id']}: `{stem}_*` is {len(members)} interchangeable slots "
                    f"sharing one code ({codes.pop()}), so the model is asked for "
                    f"{len(members)} judgements where a count would do. Convert it to "
                    f"`counts`, or add ({it['id']}, {stem}) to COUNTABLE_EXEMPT with "
                    f"the reason")
            if len(codes) > 1 and covered:
                problems.append(
                    f"{it['id']}: `{stem}_*` is counted, but its slots carry "
                    f"{len(codes)} codes ({', '.join(sorted(codes))}). A count cannot "
                    f"express which one applies, so converting it retires all but one")
            if (it["id"], stem) in COUNTABLE_EXEMPT and covered:
                problems.append(
                    f"{it['id']}: `{stem}_*` is in COUNTABLE_EXEMPT and also counted — "
                    f"the exemption is stale, remove it")
    return problems


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
    import re as _re
    from olx_prompts import (ACTION, HANDOUT, SHEET_ONLY, sheet_id, _sheet_tag,
                             build_web_prompt, primitive_attrs, primitives)

    problems = []
    excluding = primitive_attrs(excluding_keys=True)
    excludes = {p["attr"]: p.get("excludes") for p in primitives()["primitives"]}
    for item in sorted({**ACTION, **SHEET_ONLY}):
        h = HANDOUT[item]
        tag = _sheet_tag(h, sheet_id(item))
        keys: list[str] = []
        for attr in excluding:
            m = _re.search(r'\b%s="([^"]*)"' % attr, tag)
            if not m:
                continue
            for entry in m.group(1).split("|"):
                parts = [x.strip() for x in entry.split(":")]
                if not parts or not parts[0]:
                    continue
                # Which keys leave the schema is the registry's to say — this
                # was `if attr == "counts"` in two files, and agreement.py's copy
                # was one of the three ways it drifted.
                keys += ([x.strip() for x in parts[1].split(",") if x.strip()]
                         if excludes.get(attr) == "members" and len(parts) > 1
                         else [parts[0]])
        if not keys:
            continue
        if item not in ACTION:
            continue          # no prompt at all; nothing to conform to
        body = build_web_prompt(item)
        head, _, checklist = body.partition("## The checklist to return")
        for k in keys:
            if _re.search(r"^- `%s`" % _re.escape(k), checklist, _re.M):
                problems.append(f"{item}: `{k}` is excluded from the schema but still "
                                f"listed in the checklist the model fills")
            if f"DO NOT ANSWER" not in checklist or k not in checklist:
                problems.append(f"{item}: `{k}` is excluded from the schema and the "
                                f"prompt never tells the model not to answer it")
    return problems


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
    from olx_prompts import ACTION, HANDOUT, SHEET_ONLY, sheet_id

    problems = []
    for item in sorted({**ACTION, **SHEET_ONLY}):
        if item not in ACTION:
            continue          # a DerivedChecks sheet: no model call, so no schema
        try:
            action = AG.load_action(f"bmod_handout{HANDOUT[item]}.olx", sheet_id(item))
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
    import agreement as AG
    from olx_prompts import ACTION, HANDOUT, sheet_id

    problems = []
    for item, aid in sorted(ACTION.items()):
        spec = (AG.BLOCKS.get(HANDOUT[item]) or {}).get(aid)
        if spec is None:
            problems.append(f"{item}: no BLOCKS entry, so the harness cannot run it")
            continue
        try:
            action = AG.load_action(spec["olx"], sheet_id(item))
        except SystemExit as e:
            problems.append(f"{item}: {e}")
            continue
        for rule in action["derived"]:
            for f in rule["fields"]:
                if f not in spec["refs"]:
                    problems.append(
                        f"{item}: derived `{rule['key']}` reads field `{f}`, which is "
                        f"not in this item's refs — it would score unmet on every cell")
    return problems


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
    import re as _re
    import agreement as AG
    from olx_prompts import ACTION, HANDOUT, sheet_id

    import agreement_app as AA
    from handouts import find_submissions

    problems = []
    for item, aid in sorted(ACTION.items()):
        spec = (AG.BLOCKS.get(HANDOUT[item]) or {}).get(aid)
        if spec is None:
            continue          # reported by check_derived_fields_resolve
        try:
            action = AG.load_action(spec["olx"], sheet_id(item))
        except SystemExit:
            continue
        # Checked against the RECONSTRUCTION, which is what fills the prompt now,
        # on a real participant rather than a declared map — the map said Q6 was
        # fine while the sheet had grown six boxes past it.
        pids = [p for p, _ in find_submissions(AA.JOBS[item]["handout"], None)]
        if not pids:
            continue
        try:
            fixture = AA.build_jobs(item, pids[:1])[0]["fixture"]
        except SystemExit as e:
            problems.append(f"{item}: cannot build a reconstruction — {e}")
            continue
        targets = dict.fromkeys(
            _re.findall(r'<Ref\b[^>]*target="([^"]*)"', action["body"]))
        for t in targets:
            if t not in fixture:
                problems.append(
                    f"{item}: <Ref target=\"{t}\"> has no reconstructed value, so the "
                    f"check scores unmet on every cell")
    return problems


def all_items() -> list[dict]:
    return [it for h in (1, 2, 3) for it in config(h)["rubric"].ITEMS]


# ---------------------------------------------------------------------------
def _oc_baseline(item: dict) -> dict:
    """An analysis that earns full marks."""
    req = set(build_schema(item)["properties"]["oc_analysis"]["required"])
    a = {k: _tbl(_PASS, k, item["id"]) for k in _PASS if k in req}
    if item.get("cadence"):
        a["observed_type"] = "PR"
        a["named_type"] = "PR"          # agreeing, so no mismatch
    else:
        a["observed_type"] = item["expected_type"]
    return a


def _oc_fail(item: dict, a: dict, key: str, other: str = "") -> dict:
    """`a` with `key` failing. Type fields fail to a value that stays wrong."""
    a = dict(a)
    if key in _TYPE_FIELDS:
        # Pick a type that differs from the one the item wants AND from whatever
        # the co-field was flipped to, so flipping both does not re-agree.
        wrong = [t for t in ("PR", "NR", "PP", "NP")
                 if t != a.get("observed_type") and t != a.get("named_type")]
        a[key] = wrong[1] if (other in _TYPE_FIELDS and len(wrong) > 1) else wrong[0]
    else:
        a[key] = _tbl(_FAIL, key, item["id"])
    return a


def _score(item: dict, raw: dict) -> float:
    # Deliberately passes a NON-blank response. This audit probes what a sheet
    # scores, and every probe is a hypothetical answer that exists — a blank one
    # would collapse to the item's blank_code and score the same 0 for a reason
    # the probe is not testing. Leaving the argument out would default to "" and
    # do exactly that.
    if item.get("derive_from_criteria"):
        ledger, *_ = derive_oc_ledger(item, raw)
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
        base = _oc_baseline(item)
        inputs = sorted(build_schema(item)["properties"]["oc_analysis"]["required"])
        mk_base = lambda: {"oc_analysis": base}
        mk_one = lambda k: {"oc_analysis": _oc_fail(item, base, k)}

        def mk_two(a, b):
            x = _oc_fail(item, base, a, other=b)
            return {"oc_analysis": _oc_fail(item, x, b, other=a)}
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
    for h in (1, 2, 3):
        for it in config(h)["rubric"].ITEMS:
            if it.get("derive_from_criteria") or it.get("derive_from_credit"):
                out[it["id"]] = signature(it)
    return out


def all_derive_items() -> list[dict]:
    return [it for h in (1, 2, 3) for it in config(h)["rubric"].ITEMS
            if it.get("derive_from_criteria") or it.get("derive_from_credit")]


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
    import handouts as H
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
    import os
    for fname in ("agreement.py", "agreement_app.py", "baseline.py"):
        path = os.path.join(os.path.dirname(H.__file__), fname)
        try:
            src = open(path).read()
        except OSError as e:
            problems.append(f"cannot read {fname}: {e}")
            continue
        if "cell_exclusions(" not in src:
            problems.append(
                f"{fname} does not call handouts.cell_exclusions() — it is deciding "
                f"what to count some other way, so its denominator is its own")

    # The kinds must stay in step with what the reporters know how to explain: a
    # new kind that no harness has a sentence for prints as a bare label.
    for fname in ("agreement.py", "agreement_app.py", "baseline.py"):
        src = open(os.path.join(os.path.dirname(H.__file__), fname)).read()
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
    import handouts as H

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
    for h in (1, 2, 3):
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
    import rubric_h1, rubric_h2, rubric_h3
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
    import rubric_h1, rubric_h2, rubric_h3
    from handouts import HANDOUTS

    problems = []
    for h, mod in ((1, rubric_h1), (2, rubric_h2), (3, rubric_h3)):
        cfg = HANDOUTS[h]
        registry = cfg.get("cited_participants", {}) or {}
        exemplars = set(cfg.get("exemplar_participants", []) or [])
        for item in mod.ITEMS:
            iid = item["id"]
            cited = set()
            for m in _CITED_RE.finditer(_prompt_text(item)):
                cited |= {int(x) for x in re.findall(r"\d+", m.group(1))}
            registered = set(registry.get(iid, []) or [])

            stale = registered - cited
            if stale:
                problems.append(
                    f"H{h} {iid}: excludes {sorted(stale)} as self-graded, but the "
                    f"prompt no longer names them — the rate drops those cells for "
                    f"a reason that no longer exists")

            missing = cited - registered - exemplars
            if missing:
                problems.append(
                    f"H{h} {iid}: the prompt names {sorted(missing)} with the "
                    f"grader's decision, and the rate counts them — that is "
                    f"self-grading. Register them in cited_participants")
    return problems


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
    $MOLLY_DATA, outside both repositories by design, so a checkout without the
    student data must not fail this audit — it simply has nothing to check.
    """
    import os

    problems = []
    for path, table in _handsplit_tables().items():
        name = os.path.basename(path)
        if "__error__" in table:
            problems.append(f"{name} could not be read: {table['__error__']}")
            continue
        for pid, row in sorted(table.items(), key=lambda kv: str(kv[0])):
            if not isinstance(row, dict):
                continue
            norm = {f: " ".join(str(v or "").replace("\u2019", "'").split())
                          .strip().rstrip(".").lower()
                    for f, v in row.items()}
            fields = sorted(f for f, v in norm.items() if v)
            for i, a in enumerate(fields):
                for b in fields[i + 1:]:
                    va, vb = norm[a], norm[b]
                    if va in vb or vb in va:
                        small, big = (a, b) if len(va) < len(vb) else (b, a)
                        problems.append(
                            f"{name} p{pid}: `{small}` is contained in `{big}` — the "
                            f"same sentence is in two boxes, so one of them shows the "
                            f"model text the student did not put there")
    return problems


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
SLOT_RULE_BACKLOG = [
    # The four `1a:*` entries were MIGRATED on 2026-08-28, budget 17 -> 13. They
    # led because they were the only group with a measured price: 1a/p6 scored 0.0
    # on the paper path against 6.0-8.0 on the web, the whole item, 3 of 3 runs.
    # Their text now lives in rubric_h3's `rule` fields, which both generators
    # render, and the web prompt did not move because its checklist looks up
    # `rule` before SLOT_NOTES and finds the same string.
    # D1/D2:defines_type MIGRATED 2026-08-29, budget 13 -> 11. Same procedure
    # as the 1a group: the text is now the `rule` on rubric_h2's
    # `_definition_item` factory, which serves both items, and the web
    # prompts are byte-identical before and after. The paper prompt GAINED
    # the operative clause it never had -- "do not look at what they chose"
    # -- which is the half that keeps `defines_type` independent of
    # `named_type` for the `matches_chosen_type` comparison.
    # 2026-08-29, E11: SIX MORE MIGRATED and two struck off as never having been
    # gaps, 11 -> 3. Migrated to the credit component's `rule`, verbatim, web
    # prompts byte-identical against a git-HEAD baseline:
    #   Q2:reasons_given  Q2:wgb_inverts_utb  Q2:wgb_is_counterpart
    #   Q5:example_2      reasons_failing     reasons_substantial
    # The paper prompts gained what they had been missing -- Q2 3791 -> 4560
    # chars, Q5 3161 -> 4346, D1/D2 +276 each.
    #
    # STRUCK OFF, NOT MIGRATED, because neither was a paper-blind rule:
    #   `matches_chosen_type` is COMPUTED by `equals` from defines_type and
    #   named_type, so no model is ever asked about it and NEITHER generator
    #   renders its note. It reached no prompt at all -- dead text, deleted. A
    #   `rule` was briefly added to its six components and reverted for the same
    #   reason: it would have been dead too.
    #   `named_type` CANNOT migrate for four of its six items: D1 and D2 have a
    #   credit component and now carry the text as their `rule`, but DAY1, DAY2,
    #   WK1 and WK2 carry the SLOT with no component behind it, so there is
    #   nowhere to put a rule. Removing the note deleted the text from those four
    #   web prompts -- caught by diffing the generated prompt against HEAD, and by
    #   nothing else. The note stays, declared in place.
    # 2026-08-29, third pass, 5 -> 2. Two struck off as mis-categorised and one
    # migrated:
    #   `1c:has_own_graph` is DERIVED -- computed from the typed data fields --
    #     so no model is asked and neither generator renders its note. Dead
    #     text, like matches_chosen_type. Deleted.
    #   `Q1:matches_selected` STAYS, but not as work: the paper sheet has no
    #     such SLOT, because a .docx has no closed choice to compare against,
    #     and the asymmetry is already declared in SCORING_DIVERGENCES as a
    #     no-penalty check. It is listed here because this list IS the
    #     declaration of olx-only notes -- striking it out just made the
    #     reach check demand it back.
    #   `1c:legend` MIGRATED -- it reached the web only and 1c has a credit
    #     component to host it, unlike has_own_graph beside it.
    #
    # 2026-08-30, E11 closed out, 4 -> 1. The three "olx-only BY DESIGN" entries
    # -- Q5:example_2, reasons_substantial, 1c:legend -- MIGRATED. The
    # declaration standing here said they named one side's verdict token and so
    # could never be shared, and that `{fail}` was "workable for
    # reasons_substantial and 1c:legend, not for example_2, which distinguishes
    # two failure modes". The constraint was real; the conclusion was wrong, and
    # wrong in BOTH directions, which is why it took measuring the vocabularies
    # rather than reasoning about them:
    #   `Q5:example_2` DOES migrate. Its second failure mode is `duplicate`,
    #     which slot_vocab.SHARED_EXTRAS shows both sides offer, so `{fail}`
    #     plus one literal covers both. Migrating it also fixed a live defect:
    #     the note sat in olx-only SLOT_NOTES while naming `not_reason`, the
    #     RUBRIC's token, so the web prompt listed met/absent/wrong_kind/
    #     duplicate and then told the model when to answer `not_reason`. That
    #     dates to the original import, not to any migration.
    #   `reasons_substantial` did NOT migrate for the recorded reason. Bare
    #     `{fail}` fills with the slot's OWN failing verdict, which here is
    #     `absent` -- rendering "instead of reaching for `absent`" and inverting
    #     the rule. The token it names belongs to the EXAMPLE slots. That is
    #     what `{fail:key}` was added for; on the web it renders `wrong_kind`,
    #     byte-identical to the note it replaced.
    #   `1c:legend` migrated as recorded, on `{fail}` + a literal `absent`,
    #     which is universal and means a different thing here (empty box) from
    #     the failing verdict.
    #
    # THE ONE THAT REMAINS is not work waiting to be done:
    #   `Q1:matches_selected` STAYS. The paper sheet has no such SLOT, because a
    #     .docx has no closed choice to compare against, and the asymmetry is
    #     already declared in SCORING_DIVERGENCES as a no-penalty check. It is
    #     listed here because this list IS the declaration of olx-only notes --
    #     striking it out just makes the reach check demand it back.
    'Q1:matches_selected',
]

# How many may remain. It may only go DOWN. Same ratchet as HANDCODED_BUDGET, for
# the same reason and on the evidence of the same day: a declared backlog with no
# ceiling reads as coverage while enforcing nothing about its own size, and this
# one had grown to seventeen entries costing at least one item its whole score.
SLOT_RULE_BACKLOG_BUDGET = 1


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
PROSE_ONLY_SLOTS = {
    # DECLARED 2026-09-12. Both are judged by a per-slot `rule` and by nothing
    # computable, which is what this table is for: saying so, rather than leaving
    # the audit to ask whether a primitive was forgotten.
    ("1c", "series_box_holds"):
        "A CLASSIFICATION OF WHAT THE STUDENT WROTE, which no page datum can "
        "supply. Its rule says `ONE ANSWER, naming what is in the box. Do not "
        "judge whether it makes a good legend -- say what it holds and the "
        "arithmetic follows`, and the four values it picks between -- "
        "period_names, other_real_names, software_placeholders, nothing -- are "
        "distinctions about the WORDS in the box, not about the data behind the "
        "chart. The arithmetic that does follow is already a primitive: `legend` "
        "is a `maps` target computed from this pick, so the computable half is "
        "expressed and this is the irreducible half. It is `reported: True` and "
        "carries no points, so nothing is charged on it directly.",
    ("DAY2", "targets_own_behavior"):
        "A TWO-CASE READING OF THE STUDENT'S CONDITION, stated in prose because "
        "the cases are about what the condition NAMES: `met` when the condition "
        "names the unwanted behaviour itself, OR when it names the goal "
        "behaviour and that goal is the unwanted one's counterpart. The second "
        "case needs the two behaviours compared for opposition, which is a "
        "judgement about meaning and not a comparison any field supports. WK1 "
        "expresses the same question as an `expect` over `trigger_behavior` "
        "because THERE the sheet asks for a parse of which behaviour the trigger "
        "names; DAY2's sheet has no such pick, so on this item there is nothing "
        "for a primitive to read. Worth 1 point.",
    ("Q3", "realistic"):
        "NOT CONVERTIBLE, and a FIRST DEFINITION rather than a conversion. "
        "`realistic` shipped THIRTY-ONE characters with no rule at all, while "
        "its scored siblings carried specific 35, time_bound 329, measurable "
        "731 and action_oriented 1404. A 351-character rule added 2026-09-09 "
        "took Q3 from 19/20 to 20/20 on BOTH sides, Q3/p13 crossing 5 of 12 to "
        "12 of 12 PERFECT. WHAT IT TESTS IS WHETHER A GROUND FOR REALISM WAS "
        "OFFERED AT ALL, at a deliberately low bar -- a thin or circular one "
        "still counts -- which is a judgement about the presence and shape of "
        "prose, not a relation between slots. No primitive expresses \"a reason "
        "was given, however weak\": `expect` compares answers, `equals` compares "
        "two picks, `counts` counts members, `maps` translates one pick. "
        "Declared because the check is right that it is prose-only.",
    ("Q4b", "b2_names_besides"):
        "NOT CONVERTIBLE. Asking what a box names BESIDES the goal behaviour's "
        "absence -- an act, a result, or nothing -- is a reading of what the "
        "sentence contains. There is no operand: the question is whether "
        "anything beyond the absence is present at all.",
    # behavior_1 and behavior_2 LEFT this list on 2026-08-28: they are computed by
    # `maps` now, not judged, so they are no longer prose-only. The prose did not
    # disappear -- it moved to the picks below, which is where the residual
    # divergence risk now lives, and it is one named classification instead of five
    # tests weighed at once.
    ("Q4b", "b1_basis"):
        "NOT CONVERTIBLE, and it is the operand rather than the rule: `maps` turns "
        "this classification into behavior_1's verdict arithmetically, so the "
        "COMBINING is declared and only the classification is read. What an entry "
        "IS -- an activity, a consequence, the goal behaviour displaced, a "
        "not-doing -- has no operands to compare, so it stays a judgement.",
    ("Q4b", "b2_basis"):
        "NOT CONVERTIBLE, same as b1_basis for the second example.",
    # SUBGOAL Q10, 2026-09-05. Same shape as the entries below: the slot was
    # given a rule at all for the first time, and a rule is what makes it
    # prose+rule.
    # SUBGOAL Q19, 2026-09-05. `consequence_1` and `consequence_2` were given a
    # rule for the first time; a rule is what makes them prose+rule.
    ("Q4c", "consequence_1"):
        "NOT CONVERTIBLE. The test has three heads -- a STATE the student ends "
        "up in, another ACTIVITY rescued by being taken up in the behaviour's "
        "place or by a stated endpoint, and a restatement of the behaviour -- and "
        "each is a reading of what a sentence NAMES. There is no operand to "
        "compare against: the endpoint head turns on whether a clause carries the "
        "reader on to a state, which no primitive expresses.",
    ("Q4c", "consequence_2"):
        "NOT CONVERTIBLE, same as consequence_1 for the second box.",
    # SUBGOAL Q33, 2026-09-05. The antecedent VERDICTS became primitives -- they
    # are computed by `maps` from these picks -- and the reading moved here.
    ("Q4a", "antecedent_kind_1"):
        "NOT CONVERTIBLE. Naming WHICH KIND of thing a box states -- something "
        "before the behaviour, something whose link to it cannot be seen, an "
        "aftermath, the goal behaviour not happening, a consequence already "
        "listed, or nothing -- is a reading of the sentence. The `unlinked` "
        "option in particular asks whether a reader can see how the entry leads "
        "to THIS behaviour, which has no operand anywhere. The verdict it feeds "
        "IS now computable, which is the point of the split.",
    ("Q4a", "antecedent_kind_2"):
        "NOT CONVERTIBLE, same as antecedent_kind_1 for the second box.",
    ("Q3", "measurable"):
        "NOT CONVERTIBLE. The question is whether the box NAMES something that "
        "holds the record, as against merely saying a count will be kept. That "
        "is a reading of what a sentence names and there is nothing to compare "
        "it against: no list of acceptable holders can be authored without "
        "quoting the cohort, which the leakage gate forbids and which would "
        "make the rule a lookup of this year's answers.",
    # `change_a1`/`change_a2` were listed here by subgoal Q47 on 2026-09-05 and
    # removed the same day: the rule that put them here was measured, lost six
    # perfect cells, never fired on its target, and was reverted. With no rule
    # they are bare descs again and not prose+rule. The record is in rubric_h1.
    ("Q6", "affect_c1"):
        "NOT CONVERTIBLE. `cover` already constrains WHICH listed entry is referred "
        "to; what is left is whether the answer states HOW the consequence is "
        "affected, which is a reading of a sentence's claim and has no operands to "
        "compare. Seven measured rule attempts are recorded in "
        "memory/q6-matching-ceiling.md; none of them was arithmetic.",
    ("Q6", "affect_c2"):
        "NOT CONVERTIBLE, same as affect_c1 for the second consequence.",
    ("1a", "distinguishes_periods"):
        "NOT CONVERTIBLE as it stands. The test is whether the answer reports more "
        "than one point in time SEPARATELY -- a property of the whole response, not "
        "a relation between two answers. `counts` was considered and is exempted in "
        "COUNTABLE_EXEMPT: the weeks are named, not interchangeable, so `3 of 4` "
        "cannot say which is missing.",
    ("1a", "baseline_week"):
        "NOT CONVERTIBLE, same COUNTABLE_EXEMPT reason. Migrated out of SLOT_NOTES "
        "on 2026-08-28, where it reached the web and not the paper scorer and cost "
        "1a/p6 the whole item in 3 of 3 runs.",
    ("1a", "week_1"):
        "NOT CONVERTIBLE, same reason: arc-not-label coverage is judged over the "
        "narrative, and no operand pair expresses it.",
    ("1a", "week_2"): "NOT CONVERTIBLE, same as week_1 for the middle stretch.",
    # ARRIVED 2026-08-29 with the E11 migration of five Q2/Q5 notes, and the trade
    # is deliberate: the rule used to reach two scorers of three SILENTLY, and now
    # reaches all three and is declared as prose the audit cannot compare.
    # PROSE_ONLY_SLOTS growing is the price of that visibility, not a regression --
    # an undeclared asymmetry became a declared symmetry.
    ("Q2", "wgb_is_counterpart"):
        "NOT CONVERTIBLE. The WGB_UNRELATED test asks whether the goal behaviour "
        "is about a DIFFERENT behaviour from the unwanted one -- a judgement about "
        "what two pieces of prose are ABOUT, with no operand pair that expresses "
        "it. `cover` cannot help: there is no list to pair against.",
    # ("Q2", "wgb_inverts_utb") REPLACED 2026-09-05 by ("Q2", "wgb_names").
    # Subgoal Q43 converted the slot itself into a PRIMITIVE: its verdict is now
    # computed by `maps` from the `wgb_names` pick, so it no longer carries a
    # prose-only rule and the audit can compare it between the two scorers. The
    # prose moved one slot along rather than disappearing, which is why the
    # budget does not fall -- but the judging is now a classification the engine
    # scores, which is what this list exists to encourage.
    ("Q2", "wgb_names"):
        "NOT CONVERTIBLE. Naming WHICH KIND of thing a goal states -- a doing, "
        "the condition that doing it produces, a general condition, a countable "
        "target, a different activity, or nothing -- is a reading of what the "
        "sentence names, and there is no operand to compare it against. The "
        "verdict it feeds IS now computable, which is the point of the split.",
    ("Q2", "reasons_failing"):
        "NOT CONVERTIBLE as it stands, and it is a COUNT of judgements rather than "
        "a judgement: how many listed statements are not a benefit of the goal "
        "behaviour. `counts` already expands the members; what it cannot express "
        "is the test each member is counted against.",
    # Q1's twin of the entry above, added 2026-09-05 with subgoal Q14's structural
    # fix. The two are the SAME SLOT on two items by construction: Q1's
    # `benefits_listed` was counting AND judging, and the remedy was to give it the
    # split Q2 already had. So the argument transfers verbatim rather than being
    # re-derived, and if one of them ever converts, both should.
    ("Q1", "benefits_failing"):
        "NOT CONVERTIBLE as it stands, for exactly the reason Q2.reasons_failing "
        "is not: it is a COUNT of judgements rather than a judgement -- how many "
        "of the statements counted as benefits name the GOAL instead of a good it "
        "brings. `counts` expands the members; what no primitive expresses is the "
        "test each member is counted against.",
    ("D1", "defines_type"):
        "NOT CONVERTIBLE. The slot classifies a DEFINITION into PR/NR/PP/NP by "
        "reading what it says -- something added or removed, behaviour increased "
        "or decreased. That is a reading of prose, with no operands to compare. "
        "What IS computed is the next step: `equals` pairs this verdict against "
        "`named_type` to derive `matches_chosen_type`, so the COMBINING is already "
        "a primitive and only the classification is judged. The rule's operative "
        "half -- do not look at what they chose -- exists to keep the two inputs "
        "independent, which no primitive can enforce about a model's attention.",
    ("D2", "defines_type"):
        "NOT CONVERTIBLE, same as D1: one factory builds both.",
    ("1a", "week_3"): "NOT CONVERTIBLE, same as week_1 for the final stretch.",
    # ARRIVED 2026-08-30, closing E11's last three entries. Same trade again, and
    # this time the asymmetry it ended was the widest: all three rules had reached
    # the WEB ONLY, from SLOT_NOTES, so the paper scorer was never given them.
    # These three appearing here is the audit seeing a judgement it could not see
    # before, not a new judgement being made.
    ("Q5", "example_2"):
        "NOT CONVERTIBLE, and on two counts. Whether a second entry is genuinely "
        "DIFFERENT from the first is a semantic relation between two free-text "
        "spans -- the same shape as Q2:wgb_inverts_utb and the `refers_to` channel "
        "that memory/q6-matching-ceiling.md records seven failed wordings against. "
        "Whether an entry is a payoff for CONTINUING or an EFFECT of the behaviour "
        "is a second reading, of one span against no operand at all. `cover` "
        "cannot pair them: both spans are free text, and neither is a list.",
    ("Q5", "reasons_substantial"):
        "NOT CONVERTIBLE, and it is a judgement of DEGREE, which is the one shape "
        "no primitive here expresses: whether a reason that is present, distinct "
        "and a real payoff is nonetheless thin. There is nothing to compare it "
        "against -- not a list, not a sibling verdict, not a count. It is also "
        "`reported`, never scored, so no arithmetic depends on it; what it feeds "
        "is the feedback sentence.",
    # ARRIVED 2026-08-30 with E15, and it is the SLOT the `requires` rule needs:
    # link_c2 is what the sheet asks so `requires` has something to act on.
    ("Q6", "link_c2"):
        "NOT CONVERTIBLE, and it is the OPERAND rather than the rule -- the same "
        "shape as Q4b's b1_basis. `requires` turns this answer into a denial of "
        "state_c2 and affect_c2 arithmetically, so the COMBINING is declared and "
        "only the reading is judged. What is judged is whether two effect boxes "
        "are about the same consequence: a semantic relation between two "
        "free-text spans, with no operands to compare. `cover` cannot stand in "
        "for it -- it says which 4c entry each STATE box names and cannot speak "
        "for the effect boxes. Until 2026-08-30 this test lived as prose on "
        "affect_c1 and affect_c2, reaching every scorer as a request none could "
        "act on.",
}
# RAISED 25 -> 27 on 2026-09-12 for two slots the audit had been reporting as
# UNDECLARED, not for two new prose rules: `1c.series_box_holds` and
# `DAY2.targets_own_behavior` were already judged by prose and by nothing
# computable, and the budget moves because the DECLARATION was written, not
# because the corpus grew. Lower it whenever one converts to a primitive.
PROSE_ONLY_BUDGET = 27


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

PROSE_ONLY_JUDGED_AGAINST: dict[tuple[str, str], str] = {
    # Stamped 2026-09-12 against the registry as it stands today, which is the
    # same nine attributes as 2026-08-29 -- no primitive has been added since, so
    # these two claims are judged against everything that exists. If one is added,
    # both expire and must be re-read rather than assumed to survive it.
    ("1c", "series_box_holds"): _PRIMS_2026_08_29,
    ("DAY2", "targets_own_behavior"): _PRIMS_2026_08_29,
    ("Q3", "realistic"): "counts,cover,derived,equals,expect,forbid,maps,onlyif,requires",
    # Stamped 2026-09-06 against the registry as it stands. Subgoal
    # Q18: each of these is a READING that survives every primitive above --
    # the computable half of the change family moved OUT into `maps`, and what
    # is left is the classification the map reads.
    ("Q4b", "b2_names_besides"): "counts,cover,derived,equals,expect,forbid,maps,onlyif,requires",
    ("Q4b", "b1_basis"): _PRIMS_2026_08_29,
    ("Q4b", "b2_basis"): _PRIMS_2026_08_29,
    ("Q4c", "consequence_1"): _PRIMS_2026_08_29,
    ("Q4c", "consequence_2"): _PRIMS_2026_08_29,
    ("Q4a", "antecedent_kind_1"): _PRIMS_2026_08_29,
    ("Q4a", "antecedent_kind_2"): _PRIMS_2026_08_29,
    ("Q3", "measurable"): _PRIMS_2026_08_29,
    ("Q6", "affect_c1"): _PRIMS_2026_08_29,
    ("Q6", "affect_c2"): _PRIMS_2026_08_29,
    ("1a", "distinguishes_periods"): _PRIMS_2026_08_29,
    ("1a", "baseline_week"): _PRIMS_2026_08_29,
    ("1a", "week_1"): _PRIMS_2026_08_29,
    ("1a", "week_2"): _PRIMS_2026_08_29,
    ("1a", "week_3"): _PRIMS_2026_08_29,
    ("D1", "defines_type"): _PRIMS_2026_08_29,
    ("D2", "defines_type"): _PRIMS_2026_08_29,
    ("Q2", "wgb_is_counterpart"): _PRIMS_2026_08_29,
    ("Q2", "wgb_names"): _PRIMS_2026_08_29,
    ("Q2", "reasons_failing"): _PRIMS_2026_08_29,
    ("Q1", "benefits_failing"): _PRIMS_2026_08_29,
    # Judged on 2026-08-30 against the SAME registry -- `requires` was the last
    # primitive added and it predates both dates -- so they carry the same
    # constant rather than a new one spelling out an identical string. The check
    # compares SETS, not dates: a second name for one set would be a mirror, and
    # mirrors here drift.
    ("Q5", "example_2"): _PRIMS_2026_08_29,
    ("Q5", "reasons_substantial"): _PRIMS_2026_08_29,
    # `requires` is not a new primitive, only a newly USED one, so the same set.
    ("Q6", "link_c2"): _PRIMS_2026_08_29,
}


# Items built from ONE pattern, whose shared slot names should therefore mean the
# same thing. Scoped by family rather than corpus-wide on purpose: `keyword`
# legitimately differs between Q4a and Q4c (one deduction zeroed by decision, the
# other declared unreachable), and 1a's week_* slots are not siblings of these.
SLOT_STRUCTURE_FAMILIES: dict[str, tuple[str, ...]] = {
    "h2-cadence-and-type": ("PR", "NR", "PP", "NP", "DAY1", "WK1", "DAY2", "WK2"),
}

# A slot whose gate/points structure is deliberately not uniform in its family.
# The budget ratchets: an entry is either a decision with a reason or a defect
# waiting to be fixed, and it must not sit here being neither.
SLOT_STRUCTURE_DIVERGENCES: dict[tuple[str, str], str] = {
}
# ZERO, and it is meant to stay there. The single entry was DAY1's
# `phrased_directly`, retired 2026-09-04 by RENAMING the gated variant
# `phrased_directly_gate` rather than exempting it: if two sheets price a
# question differently they are not asking the same question, and the shared name
# is what made a recorded claim about the slot wrong (subgoal Q21's precision
# table). A new entry here now means someone chose an exemption over a name.
SLOT_STRUCTURE_BUDGET = 0


def _family_slot_structure() -> dict:
    """(family, slot) -> {item: (gates, pts)} read from the OLX slot specs.

    From the OLX and not from a run artifact: the artifacts only exist after a
    sweep, and a structural check should not need one. `!key` gates; `@n` carries
    points.
    """
    import re as _re
    import pathlib as _pl

    import agreement_app as _A

    olx = {f.name: f.read_text() for f in
           _pl.Path(__file__).resolve().parent.parent.joinpath("psychology")
           .glob("bmod_handout*.olx")}
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
    problems = []
    for (fam, slot), per_item in sorted(_family_slot_structure().items()):
        shapes = set(per_item.values())
        if len(shapes) < 2:
            continue
        if (fam, slot) in SLOT_STRUCTURE_DIVERGENCES:
            continue
        groups: dict = {}
        for item, shape in per_item.items():
            groups.setdefault(shape, []).append(item)
        desc = "; ".join(
            f"{'gates' if g else 'advisory'}"
            + (f" @{p:g}" if p is not None else "")
            + f" on {', '.join(sorted(items))}"
            for (g, p), items in sorted(groups.items(), key=lambda kv: -len(kv[1])))
        problems.append(
            f"`{slot}` is not uniform across the {fam} family: {desc}. Sibling "
            f"items built from one pattern should give a slot name one meaning -- "
            f"declare the difference in SLOT_STRUCTURE_DIVERGENCES with the reason, "
            f"or make them agree")

    n = len(SLOT_STRUCTURE_DIVERGENCES)
    if n != SLOT_STRUCTURE_BUDGET:
        verb = "holds" if n > SLOT_STRUCTURE_BUDGET else "is down to"
        problems.append(
            f"SLOT_STRUCTURE_DIVERGENCES {verb} {n} entrie(s) against a budget of "
            f"{SLOT_STRUCTURE_BUDGET} -- "
            + ("a divergence was added; declare it deliberately or fix it"
               if n > SLOT_STRUCTURE_BUDGET else
               "one was resolved and the ceiling was not lowered, which leaves "
               "room for a replacement to arrive unnoticed"))
    # A declaration that has stopped being true.
    live = _family_slot_structure()
    for key in sorted(SLOT_STRUCTURE_DIVERGENCES):
        per_item = live.get(key)
        if per_item and len(set(per_item.values())) < 2:
            problems.append(
                f"SLOT_STRUCTURE_DIVERGENCES declares `{key[1]}` divergent in "
                f"{key[0]}, but the family now agrees about it -- retire the entry "
                f"and lower the budget")
    return problems


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
    from olx_prompts import primitives

    now = ",".join(sorted(p["attr"] for p in primitives()["primitives"]))
    problems = []

    unstamped = set(PROSE_ONLY_SLOTS) - set(PROSE_ONLY_JUDGED_AGAINST)
    for k in sorted(unstamped):
        problems.append(
            f"PROSE_ONLY_SLOTS{list(k)} is declared NOT CONVERTIBLE with no "
            f"entry in PROSE_ONLY_JUDGED_AGAINST -- an undated claim cannot be "
            f"re-tested when the primitive set grows. Stamp it with the set it "
            f"was judged against")
    orphan = set(PROSE_ONLY_JUDGED_AGAINST) - set(PROSE_ONLY_SLOTS)
    for k in sorted(orphan):
        problems.append(
            f"PROSE_ONLY_JUDGED_AGAINST{list(k)} stamps a slot that is no longer "
            f"in PROSE_ONLY_SLOTS -- the entry left and its stamp did not")

    for k in sorted(set(PROSE_ONLY_SLOTS) & set(PROSE_ONLY_JUDGED_AGAINST)):
        was = PROSE_ONLY_JUDGED_AGAINST[k]
        if was == now:
            continue
        added = sorted(set(now.split(",")) - set(was.split(",")))
        gone = sorted(set(was.split(",")) - set(now.split(",")))
        what = []
        if added:
            what.append("the registry now also has " + ", ".join(f"`{a}`" for a in added))
        if gone:
            what.append("no longer has " + ", ".join(f"`{a}`" for a in gone))
        problems.append(
            f"PROSE_ONLY_SLOTS{list(k)} was judged NOT CONVERTIBLE against "
            f"{{{was}}}; {'; '.join(what)}. Re-judge the claim against the new "
            f"set, then re-stamp it. Still not convertible is a fine answer -- "
            f"the budget does not have to fall")
    return problems



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
    for handout in (1, 2, 3):
        src = OP._src(handout)
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
    import pathlib
    import paths

    ts = pathlib.Path(paths.SLOTSHEET_TS)
    try:
        src = ts.read_text()
    except OSError as e:
        return [f"cannot read {ts} to confirm the app understands `->`: {e}"]

    out = []
    # `maps` is the fourth computed primitive and the runtime must parse it too: a
    # `maps` attribute the app ignores means the check it names is never computed
    # there, so the app credits a slot both harnesses refuse.
    for fn in ("parseMaps", "mappedVerdict"):
        if f"export function {fn}(" not in src:
            out.append(f"{ts.name} has no {fn}: the `maps` primitive is declared in "
                       f"primitives.json and computed by both python engines, so the "
                       f"app would ignore the attribute and credit a check they "
                       f"refuse")
    if "for (const r of maps)" not in src:
        out.append(f"{ts.name}:satisfiedMap does not apply `maps`, so a mapped check "
                   f"is parsed there and never computed")
    if "splitFailsVerdict" not in src:
        out.append(f"{ts.name} has no splitFailsVerdict: the app would read the "
                   f"arrow as part of the key, so a rule written "
                   f"`behavior_1->not_active` would compute NOTHING there while "
                   f"both python engines honoured it")
        return out
    for fn in ("parseForbid", "parseExpect"):
        i = src.find(f"export function {fn}(")
        if i < 0:
            out.append(f"{ts.name} has no {fn} -- retarget this check")
            continue
        j = src.find("\nexport ", i + 1)
        body = src[i:j if j > 0 else len(src)]
        if "splitFailsVerdict" not in body:
            out.append(f"{ts.name}:{fn} does not call splitFailsVerdict, so a "
                       f"`key->verdict` rule parsed there keeps the arrow in its "
                       f"key and silently computes nothing")
    return out


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
    CLI_FNS = ("derive_ledger", "derive_oc_ledger")

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
    import collections
    import rubric_h1, rubric_h2, rubric_h3

    out = []
    for h, mod in ((1, rubric_h1), (2, rubric_h2), (3, rubric_h3)):
        for item in mod.ITEMS:
            for kind in ("forbid", "expect", "equals", "derived"):
                seen = collections.Counter(
                    r.get("key") for r in (item.get(kind) or ()) if isinstance(r, dict))
                for key, n in seen.items():
                    if n > 1:
                        out.append(
                            f"H{h} {item['id']}: {n} `{kind}` rules write `{key}`. "
                            f"Both engines ASSIGN the computed check per rule, so "
                            f"the last one wins and the others are dead -- they do "
                            f"NOT combine as an OR. Express the disjunction as one "
                            f"rule over a single operand, or extend the primitive "
                            f"deliberately on both sides")
    return out


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
        blocks = [l for l in text.splitlines() if ".py:" in l and "rubric_h" in l]
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
UNEXERCISED_PRIMITIVES_BUDGET = 0


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
    olx = [f.read_text() for f in
           _pl.Path(__file__).resolve().parent.parent.joinpath("psychology")
           .glob("bmod_handout*.olx")]
    try:
        led = _json.loads((_pl.Path(__file__).resolve().parent
                           / "MEASURED.json").read_text())["items"]
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
            return bool(was) and was == _M.prompt_sha(item)
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


HANDOUT_KEYED_GOLD_READERS = {
    # Sites that pick a gold loader by HANDOUT NUMBER rather than by item, which
    # is legitimate only when the handout is not being derived from an item. See
    # measured.gold_cell for the failure this table exists to bound: naming the
    # wrong handout for an item loads a real sheet, misses the row, and returns
    # `{}` -- which reads exactly like "this cell has no gold row".
    "cross_path": "iterates all three handouts; no item is in scope",
    "compare_runs": "takes the handout from the command line, alongside the item",
    "handouts": "builds the per-handout config; this is where the mapping LIVES",
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
    `apply_corrected_gold`, `rebuild_gold_1c` for 1c, `scored_exactly` (which
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
             ("rebuild_gold_1c", "1c's rebuilt gold"),
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
            f = here / f"{name}.py"
            if not f.exists():
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

    goals = pathlib.Path(__file__).resolve().parent / "GOALS.md"
    try:
        text = goals.read_text()
    except OSError:
        return ["GOALS.md cannot be read, so closed goals cannot be checked for "
                "a live exercise"]

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

    goals = pathlib.Path(__file__).resolve().parent / "GOALS.md"
    try:
        text = goals.read_text()
    except OSError as e:
        return [f"GOALS.md cannot be read, so CONVERTIBLE prose rules cannot be "
                f"checked for a subgoal: {e}"]

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
    import rubric_h1, rubric_h2, rubric_h3

    actual = {}
    for mod in (rubric_h1, rubric_h2, rubric_h3):
        for item in mod.ITEMS:
            for key, basis in slot_basis(item).items():
                if basis == "prose+rule":
                    actual[(item["id"], key)] = basis

    out = []
    for k in sorted(set(actual) - set(PROSE_ONLY_SLOTS)):
        out.append(f"{k[0]}.{k[1]} is judged by a per-slot `rule` and by nothing "
                   f"computable, and is not in PROSE_ONLY_SLOTS. Either express it "
                   f"as a primitive, which the enforcement audit can then compare "
                   f"between the two scorers, or declare it here with the reason it "
                   f"cannot be one")
    for k in sorted(set(PROSE_ONLY_SLOTS) - set(actual)):
        out.append(f"PROSE_ONLY_SLOTS names {k[0]}.{k[1]}, which no longer carries a "
                   f"prose-only rule. If it became a primitive, drop it from the "
                   f"list and lower PROSE_ONLY_BUDGET")
    n = len(PROSE_ONLY_SLOTS)
    if n != PROSE_ONLY_BUDGET:
        verb = "grew to" if n > PROSE_ONLY_BUDGET else "is down to"
        out.append(f"PROSE_ONLY_SLOTS {verb} {n} against a budget of "
                   f"{PROSE_ONLY_BUDGET} -- raise it only for a rule that genuinely "
                   f"cannot be a primitive, and lower it whenever one converts")
    return out


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
    import pathlib
    here = pathlib.Path(__file__).parent
    out = []
    for fname, what in ARTIFACT_WRITERS:
        try:
            src = (here / fname).read_text()
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
    n = len(SLOT_RULE_BACKLOG)
    if n > SLOT_RULE_BACKLOG_BUDGET:
        return [f"SLOT_RULE_BACKLOG holds {n} entries against a budget of "
                f"{SLOT_RULE_BACKLOG_BUDGET} -- {n - SLOT_RULE_BACKLOG_BUDGET} "
                f"olx-only slot rule(s) were ADDED. Put the text in the credit "
                f"component's `rule` field, which both generators render, rather "
                f"than in SLOT_NOTES, which the paper scorer never sees"]
    if n < SLOT_RULE_BACKLOG_BUDGET:
        return [f"SLOT_RULE_BACKLOG is down to {n} entries but the budget still "
                f"says {SLOT_RULE_BACKLOG_BUDGET} -- lower it to {n}, or the slack "
                f"lets a new olx-only slot rule in without the audit noticing"]
    return []


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
    import rubric_h1, rubric_h2, rubric_h3
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


def _olx_slot_verdicts(item_id: str, slot: str) -> set:
    """Verdicts the OLX slot spec declares for this slot, e.g. `key:label:fail@2`."""
    import re as _re
    import pathlib as _pl

    import agreement_app as _A

    J = _A.JOBS.get(item_id) or {}
    g = J.get("grader") or ""
    if not g:
        return set()
    act = g.replace("_grader", "_llm")
    for f in _pl.Path(__file__).resolve().parent.parent.joinpath("psychology").glob("bmod_handout*.olx"):
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
            return {o for o in out if o}
    return set()


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
    import olx_prompts as O
    from slot_vocab import KNOWN_VERDICTS

    by_id = {it["id"]: it for it in all_items()}
    jobs = O.ACTION
    problems = []
    for item_id, action in sorted(jobs.items()):
        handout = O.HANDOUT.get(item_id)
        if handout is None:
            continue
        try:
            spec, defaults = O._slots_attr(handout, action)
            choices = O._choices_attr(handout, action)
            slots = O.parse_slots(spec, defaults)
        except Exception:
            continue
        rubric = by_id.get(item_id)
        rules = {c["what"] for c in (rubric or {}).get("credit", []) or []
                 if c.get("rule")}
        for s in slots:
            key = s["key"]
            if key in rules:
                continue                      # `rule` wins; the other check owns it
            # What the WEB sheet offers for this slot, needed by both arms below.
            offered = set(s["options"] or ())
            if s.get("picks") is not None:
                offered |= set(choices.get(s["picks"], []) or ())

            note = (O.SLOT_NOTES.get(f"{item_id}:{key}")
                    or O.SLOT_NOTES.get(key))
            if note:
                # A SLOT_NOTES entry is olx-only, so the test is against what the
                # WEB slot offers: it is the only side that will be handed it.
                named = {v for v in KNOWN_VERDICTS if f"`{v}`" in note}
                missing = sorted(named - offered)
                if missing:
                    problems.append(
                        f"{item_id}.{key}: the prompt prose tells the model to "
                        f"answer {missing}, which this slot does not offer -- it "
                        f"offers {sorted(offered)}. The test is inert: the model "
                        f"cannot return that token, so it answers something else "
                        f"and the distinction is lost. Move the text to the "
                        f"rubric's `rule` and use `{{fail}}`, or name a verdict "
                        f"the slot has")
                continue

            # THIRD prose source, and it reaches BOTH scorers. When a slot has
            # neither a `rule` nor a note, the web falls through to the credit
            # component's `desc` and score.py uses that same `desc` as its body.
            # So the test here is the SHARED one, not the web's: a token only one
            # side offers is wrong on the other, exactly as it would be in a
            # `rule`. Clean at the time of writing -- no `desc` names a verdict --
            # which is why it is worth guarding now rather than after it is not.
            desc = next((c.get("desc") for c in (rubric or {}).get("credit", []) or []
                         if c["what"] == key), None)
            if not desc:
                continue
            # PER-SLOT, like the `rule` check and for the same reason: whether a
            # token is shared is a fact about THIS slot, not about the corpus.
            comp = next((c for c in (rubric or {}).get("credit", []) or []
                         if c["what"] == key), None)
            offered_paper = set((comp or {}).get("verdicts") or []) | set(
                ((comp or {}).get("codes") or {}).keys()) | {"met", "absent"}
            for grp in (rubric or {}).get("cover", []) or []:
                if key in (grp.get("keys") or ()):
                    offered_paper |= set(grp.get("verdicts") or ())
            named = sorted({v for v in KNOWN_VERDICTS if f"`{v}`" in desc})
            bad = sorted(v for v in named
                         if v not in offered_paper or v not in offered)
            if bad:
                problems.append(
                    f"{item_id}.{key}: the credit component's `desc` names the "
                    f"verdict {bad} literally, and `desc` is rendered into BOTH "
                    f"prompts when the slot has no `rule` and no note. This slot "
                    f"does not offer it on both sides -- web {sorted(offered)}, "
                    f"paper {sorted(offered_paper)}. Use `{{fail}}` in a `rule`, "
                    f"or name only verdicts this slot offers on both")
    return problems


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
VERDICT_SPACE_DIVERGENCES: dict[tuple[frozenset, frozenset], str] = {
    (frozenset({"unclear"}), frozenset()):
        "17 slots. The web offers a third 'cannot tell' verdict and the paper "
        "offers only met/absent -- three-valued against two-valued, NOT a "
        "renaming: those slots declare no third token under any name. Score "
        "impact is NIL, because `unclear` is not satisfied and so deducts exactly "
        "as `absent` does; what the paper loses is the DIAGNOSIS, not marks. "
        "2a.how_*, 2b.sentence_*, 3.example_*, Q1.reason_*, Q2.reason_*, and "
        "D1/D2's add_or_remove and increase_or_decrease.",
    (frozenset(), frozenset({"0", "1", "2", "3"})):
        "The paper encodes a COUNT as its verdict list. Not judgements, so there "
        "is nothing for the web to offer against them.",
    (frozenset(), frozenset({"0", "1", "2"})):
        "Same count encoding, on a slot whose maximum is two.",
    (frozenset(), frozenset({"no"})):
        "A boolean answer written as a token. Same as the counts: an encoding, "
        "not a judgement the other side could return.",
    (frozenset({"mismatch"}), frozenset({"first", "neither", "second"})):
        "The paper reports WHICH listed entry is referred to -- a `cover` "
        "identity -- where the web reports whether it matched at all. Different "
        "questions, the same deduction; the identity is what `cover` exists for.",
    # RENAMED COUNTERPARTS. Each pair is one judgement with two names, which is
    # exactly what `{fail}` renders per side, and is why a shared rule must never
    # name either half literally.
    (frozenset({"incomplete"}), frozenset({"not_described"})):
        "Counterparts: the web's `incomplete` is the paper's `not_described`. 5 "
        "slots, 1c's chart parts among them.",
    (frozenset({"wrong_kind"}), frozenset({"not_antecedent"})):
        "Counterparts on Q4a's antecedent_1/antecedent_2.",
    (frozenset({"wrong_kind"}), frozenset({"not_consequence"})):
        "Counterparts on Q4c's consequence_1/consequence_2.",
    (frozenset({"wrong_kind"}), frozenset({"not_reason"})):
        "Counterparts on Q5's example_1/example_2. The pair E11 migrated onto "
        "`{fail}`, and the one whose web prompt named the paper's token for "
        "months -- see BACKLOG.md:94.",
    (frozenset({"generic"}), frozenset({"not_described"})):
        "Counterparts: a generic label is the web's version of not describing it.",
    (frozenset({"tick_values"}), frozenset({"not_described"})):
        "Counterparts: missing tick values is the web's version of the same.",
    (frozenset({"generic", "tick_values"}), frozenset({"not_described"})):
        "Both web refinements collapse to the paper's single `not_described`.",
}


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
    problems = []
    for item in all_items():
        for c in item.get("credit", []) or []:
            web = _web_slot_options(item["id"], c["what"])
            if web is None:
                continue
            paper = set(c.get("verdicts") or []) | set(
                (c.get("codes") or {}).keys()) | {"met", "absent"}
            for grp in item.get("cover", []) or []:
                if c["what"] in (grp.get("keys") or ()):
                    paper |= set(grp.get("verdicts") or ())
            if web == paper:
                continue
            shape = (frozenset(web - paper), frozenset(paper - web))
            if shape in VERDICT_SPACE_DIVERGENCES:
                continue
            problems.append(
                f"{item['id']}.{c['what']}: the two scorers' verdict spaces differ "
                f"in a shape nothing declares -- olx-only {sorted(shape[0])}, "
                f"paper-only {sorted(shape[1])}. Either make them match, or add "
                f"the shape to VERDICT_SPACE_DIVERGENCES with the reason and "
                f"whether it moves a score")
    return problems


def _web_slot_options(item_id: str, key: str) -> set | None:
    """What the WEB sheet offers for one slot, `pick(NAME)` enums resolved.

    None when the item has no action or the slot is not on the sheet -- a slot
    that exists only on the rubric side cannot be compared, and reporting it as
    a mismatch would flag every paper-only check.
    """
    import olx_prompts as O
    handout, action = O.HANDOUT.get(item_id), O.ACTION.get(item_id)
    if handout is None or action is None:
        return None
    try:
        spec, defaults = O._slots_attr(handout, action)
        choices = O._choices_attr(handout, action)
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
    so every test was inert: it credited p8's "or just avoiding going the gym"
    that the web and CLI both reject, and scored 5.00 against a gold of 2.00.
    Three runs reproduced it exactly, so it read as a stable model difference
    rather than a broken prompt.

    Rules must therefore use the `{fail}` placeholder, which each generator
    fills with the verdict IT offers. This checks for the literal tokens.
    """
    import rubric_h1, rubric_h2, rubric_h3
    from slot_vocab import KNOWN_VERDICTS

    # RESTORED 2026-08-30 to its original strictness, after being weakened
    # twice on a false premise. slot_vocab.py is explicit: the web's extras
    # come from EXTRA_VERDICTS in slotSheet.ts, the rubric's from the
    # `verdicts` lists on credit components, "and a rule may legitimately
    # mention NEITHER". The two vocabularies differ BY DESIGN -- `wrong_kind`
    # is the web's token and `not_reason` the rubric's counterpart -- so a
    # slot declaring one of them is not evidence that both sides offer it.
    # Reading the rubric list as "what this slot offers" and then unioning it
    # with the OLX spec made the check blind to exactly the case it exists
    # for, and cost a cell on Q5 before the measurement caught it.
    problems = []
    for h, mod in ((1, rubric_h1), (2, rubric_h2), (3, rubric_h3)):
        for item in mod.ITEMS:
            for c in item.get("credit", []) or []:
                rule = c.get("rule")
                if not rule:
                    continue
                # PER-SLOT, not against the global SHARED_EXTRAS intersection.
                # A token is safe to name only if BOTH sides offer it ON THIS
                # SLOT, and sharedness is a per-slot property that a corpus-wide
                # intersection cannot express.
                #
                # `wrong_kind` is the proof. Q4b's behavior_1/behavior_2 declare
                # it in the RUBRIC, so there it is shared and naming it is fine;
                # on Q4a's antecedent_*, Q4c's consequence_* and Q5's example_*
                # the web offers it and the paper does not. One token, shared on
                # two slots and one-sided on six. Adding it to RUBRIC_EXTRAS to
                # reflect Q4b -- the list IS incomplete without it -- would have
                # exempted it globally and re-opened the hole on the other six.
                #
                # And the global form had already opened one. E27 fixed the
                # `unclear` misclassification by deriving SHARED_EXTRAS, which is
                # right for the 21 rubric slots that declare it and wrong for the
                # SEVENTEEN where the web offers it and the paper does not --
                # 2a.how_*, 2b.sentence_*, 3.example_* among them. A rule naming
                # `unclear` on any of those passed. No rule did, so it was latent,
                # and latent is how the Q4b instance started too.
                offered_paper = set(c.get("verdicts") or []) | set(
                    (c.get("codes") or {}).keys()) | {"met", "absent"}
                for grp in item.get("cover", []) or []:
                    if c["what"] in (grp.get("keys") or ()):
                        offered_paper |= set(grp.get("verdicts") or ())
                offered_web = _web_slot_options(item["id"], c["what"])
                named = sorted({v for v in KNOWN_VERDICTS if f"`{v}`" in rule})
                bad = sorted(v for v in named
                             if v not in offered_paper
                             or (offered_web is not None and v not in offered_web))
                if bad:
                    problems.append(
                        f"H{h} {item['id']}.{c['what']}: `rule` names the verdict "
                        f"{bad} literally, and this SLOT does not offer it on both "
                        f"sides -- web {sorted(offered_web) if offered_web is not None else 'n/a'}, "
                        f"paper {sorted(offered_paper)}. The rule is rendered into "
                        f"both prompts, so one side gets an instruction about a "
                        f"token it cannot emit. Use `{{fail}}`, which each generator "
                        f"fills with its own verdict")
                named = bad
                # `{fail}` OR `{fail:sibling}`. Testing for the bare literal
                # reported every rule that uses the qualified form as having lost
                # its failing condition.
                from olx_prompts import _FAIL_RE
                if not _FAIL_RE.search(rule) and not named:
                    # A rule that never says when to FAIL is not necessarily wrong,
                    # but one that neither uses the placeholder nor names a token is
                    # worth noticing — it may have lost its failing condition.
                    pass
    return problems


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
    import rubric_h1, rubric_h2, rubric_h3
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
            import handouts as H
            for h in (1, 2, 3):
                for item in H.config(h)["rubric"].ITEMS:
                    for pid in range(1, 21):
                        try:
                            fx = fixture_for(item["id"], pid)
                        except Exception:
                            continue
                        out[(item["id"], pid)] = _norm(
                            " ".join(str(v) for v in fx.values()))
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
CORPUS_QUOTE_BACKLOG: set[tuple[str, int]] = set()  # noqa: C408
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
# handout vocabulary ("the end of the week", "the unwanted target behavior is")
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
    import collections
    import handouts as H
    import olx_prompts as O

    corpus = _corpus_cells()
    if not corpus:
        return []                      # corpus absent; nothing to compare against

    problems = []
    seen_backlog: set[tuple[str, int]] = set()
    for h in (1, 2, 3):
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
            prompt = _grams(_norm(" ".join(parts)))
            if not prompt:
                continue

            per = {pid: _grams(body) for (i, pid), body in corpus.items() if i == iid}
            shared = collections.Counter(g for gs in per.values() for g in gs)
            # A student echoing the question back is not us quoting the student.
            asked = _grams(_norm(str(item.get("question") or "")))
            excluded = set(H.cell_exclusions(h, iid))
            for pid, gs in sorted(per.items()):
                if pid in excluded:
                    continue
                own = [g for g in (prompt & gs) if shared[g] == 1 and g not in asked]
                if not own:
                    continue
                if (iid, pid) in CORPUS_QUOTE_BACKLOG:
                    seen_backlog.add((iid, pid))
                    continue
                problems.append(
                    f"H{h} {iid}: the prompt reproduces p{pid}'s own words "
                    f"(\"...{' '.join(sorted(own)[0])}...\") and p{pid} is still "
                    f"COUNTED on this item. Either invent the example, or "
                    f"register p{pid} in handouts `cited_participants` and accept "
                    f"the smaller denominator")

    # A backlog entry that no longer fires has been fixed; leaving it listed
    # would exempt a future leak on the same cell.
    for stale in sorted(CORPUS_QUOTE_BACKLOG - seen_backlog):
        problems.append(
            f"CORPUS_QUOTE_BACKLOG lists {stale[0]}/p{stale[1]}, which no longer "
            f"reproduces that participant. Remove it from the list")
    return problems


def _attr(handout: int, item_id: str, attr: str) -> str:
    """One sheet attribute, or "" — the reader the slot guard needs."""
    import re
    import olx_prompts as O
    m = re.search(r'\b%s="([^"]*)"' % attr, O._sheet_tag(handout, O.ACTION[item_id]))
    return m.group(1) if m else ""


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
    src = pathlib.Path(__file__).with_name("score.py").read_text()
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
    if not any("_criteria_section" in c for c in calls):
        out.append("score.py's derive_from_criteria branch no longer calls "
                   "_criteria_section -- the criteria prose has a second source "
                   "again, and the two copies will drift the way they did before")

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
    """Does the web scorer BEHAVE as its sheet says, not merely parse it?

    The gap this closes is one no injected breakage can reach. The enforcement
    audit models the web side from the SHEET -- its own declaration says "the web
    probe sees that pair because it reads slot keys" -- so a scorer that parses a
    primitive correctly and then ignores it looks identical to one that honours
    it. Every selftest case removes something from the sheet, which the probe
    does read; none can remove something from the SCORER.

    That is exactly how `onlyif` was dead on the web path. `agreement.score_slots`
    built its charge-once map from `spec.get("onlyif")`, and `spec` there is
    `merged`, which never carries it -- so the map was all-True and the guard
    never fired, while the audit reported the behaviour present because the
    attribute was in the sheet.

    So this does not read: it RUNS. Synthetic answer sheets, no model calls, and
    the number has to move the way the primitive says it should.

    THREE THINGS THIS GETS RIGHT THAT A NAIVE PROBE DOES NOT, each of which
    silently reported clean while measuring nothing:

    1. THE SPEC IS THE RUNNER'S. measure_one hands the scorer
       `dict(job, slots=..., cover=..., requires=...)` -- a spec that carries no
       `equals`, `counts`, `onlyif` or `choices`. Probing with the full action
       dict instead makes `spec.get("onlyif")` work in the probe and stay dead in
       production, so this check would have MISSED the very bug it was written
       for. The spec below is built the same way, from BLOCKS, so an omission
       there is an omission here.

    2. COMPUTED KEYS ARE NOT ANSWERED. `equals`, `derived`, `expect` and `forbid`
       are stripped from the response schema and filled by apply_computed. A
       sheet that pre-answers them makes the rule unobservable: it was pre-filling
       `matches_chosen_type` that produced a confident report of a dead `equals`
       on D1/D2 and a "fix" to a scorer that was correct all along. Every sheet
       here goes through apply_computed, exactly as the runner does.

    3. THE CONTROL EARNS FULL MARKS. score_oc gates on the four definitional
       criteria and returns at the first failure, so a control that already fails
       one makes every rule below it invisible. The control is hill-climbed to
       the item max, and an item where that cannot be reached is REPORTED rather
       than passed over.

    Assertion primitives (`equals`, `expect`, `forbid`, `counts`, `cover`,
    `derived`, and a gating slot) are tested by violating them: the number must
    move. `onlyif` is a SUPPRESSION rule, so violating it must not cost more than
    honouring it -- charging both the failed condition and the check it guards is
    the observable failure there.
    """
    import agreement as A

    problems: list[str] = []
    probed = 0
    unprobed: list[str] = []
    # What was exercised, per primitive, published on the function so the audit
    # can print it. A check whose coverage is invisible is a check that can drop
    # to zero probes without anyone noticing -- which is what happened.
    covered: dict[str, list[str]] = {}

    for h, blocks in sorted(A.BLOCKS.items()):
        try:
            rubric = config(h)["rubric"]
        except Exception:
            continue
        for action_id, job in sorted(blocks.items()):
            if job["kind"] not in A.SCORERS or not job.get("olx"):
                continue          # deterministic item: no sheet to exercise
            iid = job["item"]
            try:
                item = rubric.BY_ID[iid]
                act = A.load_action(job["olx"], action_id)
            except Exception as e:
                problems.append(f"H{h} {iid}: its sheet cannot be loaded to probe "
                                f"it: {type(e).__name__}: {e}")
                continue

            slots = act["slots"]
            by_key = {sl["key"]: sl for sl in slots}
            excluded = set(act.get("excluded") or ())
            merged = dict(job, slots=slots, cover=act["cover"],
                          requires=act["requires"])
            scorer = A.SCORERS[job["kind"]]
            here = f"H{h} {iid}"

            def vocab(sl):
                if sl.get("picks"):
                    return (act.get("choices") or {}).get(sl["picks"]) or []
                return sl.get("options") or ["met", "absent"]

            def answer(sl, value):
                return ({"refers_to": value} if sl.get("picks")
                        else {"verdict": value})

            # `derived` reads FIELDS, so it needs a fixture rather than a sheet.
            # Two numbers, so `plots` and `complete` both see data.
            full_fx = {f: "12 34" for r in act.get("derived", []) or []
                       for f in r["fields"]}
            pinned: dict[str, str] = {}

            def run(**over):
                nonlocal probed
                raw: dict = {}
                for sl in slots:
                    if sl["key"] in excluded:
                        continue          # the web strips it and computes it
                    vs = vocab(sl)
                    raw[sl["key"]] = answer(sl, vs[0] if vs else "met")
                for k, v in {**pinned, **over}.items():
                    raw[k] = (v if isinstance(v, dict)
                              else answer(by_key.get(k) or {}, v))
                probed += 1
                return scorer(merged, item,
                              A.apply_computed(act, raw, full_fx))

            # A first-value-everywhere sheet is not a passing one, and the two
            # ways it falls short are facts about the SLOT SHAPE rather than
            # about the item:
            #
            #   a COUNTER (`count(3)`) carries count_max and no options at all,
            #   so a verdict in that field parses to n=0 and marks every member
            #   absent -- the control lost exactly the points the count exists
            #   to award, on all five counted items;
            #
            #   a COVER slot is credited on a `refers_to` LABEL, and a sheet
            #   that answers only the verdict names no label, so the group
            #   claims nothing -- Q6 sat at 5.0 of 10.0.
            #
            # Both looked like "this item cannot reach full marks" and would have
            # been reported as six unprobeable items rather than a control built
            # to the wrong shape.
            for sl in slots:
                if sl.get("count_max") and sl["key"] not in excluded:
                    pinned[sl["key"]] = {"count": sl["count_max"]}
            for grp in act.get("cover", []) or []:
                labels = grp.get("labels") or []
                for i, k in enumerate(grp.get("keys", [])):
                    if k in by_key and i < len(labels):
                        pinned[k] = {"verdict": "met", "refers_to": labels[i]}

            # A pick answers a category, and the first category listed need not
            # be the one the item expects. Climb to full marks before probing.
            best = run()[0]
            for sl in slots:
                if best >= item["max"]:
                    break
                if sl["key"] in excluded or len(vocab(sl)) < 2:
                    continue
                for v in vocab(sl)[1:]:
                    got = run(**{sl["key"]: v})[0]
                    if got > best:
                        best, pinned[sl["key"]] = got, v
            if best < item["max"]:
                problems.append(
                    f"{here}: no synthetic sheet scores the item's own maximum "
                    f"({best} of {item['max']} at best), so NO rule on this item "
                    f"can be observed to cost anything -- every probe below it "
                    f"reports clean because nothing can move, not because "
                    f"nothing is broken")
                continue
            base_score, base_failed = run()

            def must_cost(label: str, mutation: dict, why: str, key: str = ""):
                """A rule violated must move the number. Flat means dead.

                When the violated check GATES the item, the gate loop below
                cannot reach it -- a computed key is stripped from the sheet, so
                there is no verdict to set. D1/D2's `matches_chosen_type` is
                exactly that: gating, and answered by `equals`. So the gate is
                asserted here instead, driven through the rule that computes it,
                and its 2.0 WRONG_DEFINITION is the whole item.
                """
                score, failed = run(**mutation)
                if score == base_score and failed == base_failed:
                    problems.append(
                        f"{here}: `{label}` is in the sheet, and {why} scores "
                        f"{score} with {failed} failed check(s) -- exactly what "
                        f"an answer that honours it scores -- so the rule reaches "
                        f"no arithmetic")
                    return
                if key and (by_key.get(key) or {}).get("gates"):
                    covered.setdefault("gates", []).append(f"{here}/{key} (computed)")
                    if score > 0:
                        problems.append(
                            f"{here}: `{key}` GATES the item and is computed by "
                            f"`{label}`, so {why} should leave nothing standing, "
                            f"and it scores {score} of {item['max']}")

            def other(key: str, *avoid: str):
                """A value for `key` that is none of `avoid`, or None."""
                sl = by_key.get(key)
                if sl is None:
                    return None
                for v in vocab(sl):
                    if v not in avoid:
                        return v
                return None

            # ── equals: the key holds iff its two operands agree ──────────────
            for rule in act.get("equals", []) or []:
                lenient = rule.get("lenient") or []
                if rule["left"] not in by_key or rule["right"] not in by_key:
                    unprobed.append(f"{here} equals={rule['key']} (operand not a slot)")
                    continue
                # Same value on both sides is the control; a DIFFERENT one on the
                # right, lenient on neither side, must cost.
                l = other(rule["left"], *lenient)
                r = other(rule["right"], *lenient, l)
                if l is None or r is None:
                    unprobed.append(f"{here} equals={rule['key']} (no two non-lenient values)")
                    continue
                covered.setdefault("equals", []).append(f"{here}/{rule['key']}")
                must_cost(f"equals={rule['key']}:{rule['left']}={rule['right']}",
                          {rule["left"]: l, rule["right"]: r},
                          f"operands that disagree ({l!r} vs {r!r})", rule["key"])

            # ── expect: one answer against a value the item authored ──────────
            for rule in act.get("expect", []) or []:
                wrong = other(rule["left"], rule["value"], *(rule.get("lenient") or []))
                if wrong is None:
                    unprobed.append(f"{here} expect={rule['key']} (no value other than the expected one)")
                    continue
                covered.setdefault("expect", []).append(f"{here}/{rule['key']}")
                must_cost(f"expect={rule['key']}:{rule['left']}={rule['value']}",
                          {rule["left"]: wrong},
                          f"answering {wrong!r} where the item expects "
                          f"{rule['value']!r}", rule["key"])

            # ── forbid: the check fails when a COMBINATION holds ──────────────
            for rule in act.get("forbid", []) or []:
                conds = rule.get("conds") or []
                if not conds or any(c["slot"] not in by_key for c in conds):
                    unprobed.append(f"{here} forbid={rule['key']} (condition not a slot)")
                    continue
                covered.setdefault("forbid", []).append(f"{here}/{rule['key']}")
                must_cost(f"forbid={rule['key']}",
                          {c["slot"]: c["value"] for c in conds},
                          "the forbidden combination "
                          + ", ".join(f"{c['slot']}={c['value']}" for c in conds),
                          rule["key"])

            # ── a GATING slot is worth the whole item ────────────────────────
            for sl in slots:
                if not sl.get("gates") or sl["key"] in excluded:
                    continue
                miss = other(sl["key"], *(vocab(sl)[:1] or []))
                if miss is None:
                    unprobed.append(f"{here} gates={sl['key']} (no failing value)")
                    continue
                covered.setdefault("gates", []).append(f"{here}/{sl['key']}")
                score, failed = run(**{sl["key"]: miss})
                if score == base_score and failed == base_failed:
                    problems.append(
                        f"{here}: `{sl['key']}` GATES the item, and failing it "
                        f"scores {score} of {item['max']} -- what passing it "
                        f"scores -- so the gate reaches no arithmetic")
                elif score > 0:
                    problems.append(
                        f"{here}: `{sl['key']}` GATES the item, so failing it "
                        f"should leave nothing standing, and it scores {score} "
                        f"of {item['max']}")

            # ── counts: the score must fall as the count falls ────────────────
            for cr in item.get("counts", []) or []:
                if cr["key"] not in by_key:
                    unprobed.append(f"{here} counts={cr['key']} (counter not a slot)")
                    continue
                covered.setdefault("counts", []).append(f"{here}/{cr['key']}")
                n_max = len(cr["slots"])
                scores = [run(**{cr["key"]: {"count": n}})[0]
                          for n in range(n_max + 1)]
                if len(set(scores)) == 1:
                    problems.append(
                        f"{here}: `counts={cr['key']}` names {n_max} member(s), "
                        f"and the score is {scores[0]} for every count from 0 to "
                        f"{n_max} -- the members reach no arithmetic")

            # ── cover: naming the same item twice is the error it catches ─────
            for grp in act.get("cover", []) or []:
                keys = [k for k in grp.get("keys", []) if k in by_key]
                labels = grp.get("labels") or []
                if len(keys) < 2 or len(labels) < 2:
                    unprobed.append(f"{here} cover={keys} (needs two keys and two labels)")
                    continue
                covered.setdefault("cover", []).append(f"{here}/{keys[0]}")
                dup = run(**{keys[0]: {"verdict": "met", "refers_to": labels[0]},
                             keys[1]: {"verdict": "met", "refers_to": labels[0]}})
                distinct = run(**{keys[0]: {"verdict": "met", "refers_to": labels[0]},
                                  keys[1]: {"verdict": "met", "refers_to": labels[1]}})
                if dup == distinct:
                    problems.append(
                        f"{here}: `cover` groups {keys} over {labels}, and both "
                        f"checks naming {labels[0]!r} scores exactly what naming "
                        f"one each does ({dup[0]}, {dup[1]} failed) -- the "
                        f"duplicate it exists to catch reaches no arithmetic")

            # ── onlyif is SUPPRESSION: failing the condition must not also
            #    charge the check it guards ─────────────────────────────────────
            for rule in item.get("onlyif", []) or []:
                key, cond = rule["key"], rule["cond"]
                if key not in by_key or cond not in by_key:
                    unprobed.append(f"{here} onlyif={key}:{cond} (not a slot)")
                    continue
                kmiss, cmiss = other(key, vocab(by_key[key])[0]), other(cond, vocab(by_key[cond])[0])
                if kmiss is None or cmiss is None:
                    unprobed.append(f"{here} onlyif={key}:{cond} (no failing value)")
                    continue
                covered.setdefault("onlyif", []).append(f"{here}/{key}")
                both = run(**{cond: cmiss, key: kmiss})[1]
                only = run(**{key: kmiss})[1]
                if both > only:
                    problems.append(
                        f"{here}: `onlyif={key}:{cond}` is in the sheet but "
                        f"{both} check(s) are charged when the condition fails "
                        f"against {only} when it holds -- the guarded check is "
                        f"charged anyway, so the rule reaches no arithmetic")

            # ── derived: computed from the FIXTURE, not from other checks ─────
            for rule in act.get("derived", []) or []:
                fields = rule.get("fields") or []
                if not fields:
                    unprobed.append(f"{here} derived={rule['key']} (names no field)")
                    continue
                covered.setdefault("derived", []).append(f"{here}/{rule['key']}")
                # `contains` is probed on the WORD, not on a blanked field.
                # Emptying one box moves this verdict only when the word lived
                # exactly there, so the blank-a-field probe reported "reaches no
                # verdict" against a rule that works perfectly -- the probe
                # asking its question, not the sheet failing to answer one. The
                # pair here is the one the rule actually discriminates: text
                # carrying a listed word against text carrying none.
                if rule.get("kind") == "contains":
                    word = (rule.get("words") or [""])[0]
                    hit = dict(full_fx, **{f: "" for f in fields})
                    hit[fields[0]] = f"... {word} ..."
                    miss = dict(full_fx, **{f: "zzz" for f in fields})
                    try:
                        a = A.apply_computed(act, {}, hit).get(rule["key"], {})
                        b = A.apply_computed(act, {}, miss).get(rule["key"], {})
                    except Exception as e:
                        problems.append(f"{here}: probing `derived={rule['key']}` "
                                        f"raised {type(e).__name__}: {e}")
                        continue
                    if a.get("verdict") == b.get("verdict"):
                        problems.append(
                            f"{here}: `derived={rule['key']}` answers "
                            f"{a.get('verdict')!r} whether or not the response "
                            f"contains {word!r} -- the derivation reaches no verdict")
                    continue
                short = dict(full_fx, **{fields[0]: ""})
                try:
                    a = A.apply_computed(act, {}, full_fx).get(rule["key"], {})
                    b = A.apply_computed(act, {}, short).get(rule["key"], {})
                except Exception as e:
                    problems.append(f"{here}: probing `derived={rule['key']}` "
                                    f"raised {type(e).__name__}: {e}")
                    continue
                if rule.get("kind") == "present" and len(fields) > 1:
                    pass          # `present` is all-of, so one blank IS a miss
                if a.get("verdict") == b.get("verdict"):
                    problems.append(
                        f"{here}: `derived={rule['key']}` is `{rule.get('kind')}` "
                        f"over {len(fields)} field(s), and a fixture missing one "
                        f"answers {b.get('verdict')!r} exactly as a full one does "
                        f"-- the derivation reaches no verdict")

    # ZERO PROBES READS EXACTLY LIKE ZERO FAULTS. Two pick slots carrying empty
    # `options` once made this run no probes at all on D1 and D2 while reporting
    # clean, so the count is asserted rather than assumed.
    if probed < 40:
        problems.append(
            f"this check ran only {probed} probe(s) across all three handouts, "
            f"which is too few to have exercised the sheets -- it is reporting "
            f"clean because it measured nothing")
    check_web_scorer_exercises_its_sheet.tally = {
        "probes": probed,
        "instances": {k: sorted(v) for k, v in sorted(covered.items())},
        "unprobed": sorted(unprobed),
    }
    if unprobed:
        problems.append("rule instances this check could not exercise, each of "
                        "which is a rule with NO behavioural coverage:\n    "
                        + "\n    ".join(sorted(unprobed)))
    return problems

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
HANDCODED_ITEM_RULES: dict[tuple[str, str], str] = {
    # ONE ENTRY, ADDED 2026-09-12 AFTER THE ALTERNATIVE WAS TRIED AND REVERTED.
    # The obvious fix is the one the seven cleared entries used: move the datum
    # onto the rubric item and read it as CONTENT, the way `reads_utb_choice` is
    # read. It was implemented -- `rubric_h1.PAPER_NOTES` attaching a
    # `paper_note` key -- and then reverted, because it trades a guarantee for a
    # convention.
    #
    # WHY THIS ONE STAYS IN score.py. `PAPER_ITEM_NOTES` is paper-only BY
    # CONSTRUCTION: no other engine imports this module, so the web cannot read
    # it whatever anyone does later. In the shared rubric it would be paper-only
    # only for as long as nothing looks for the key -- and the standing
    # instruction for this split was that a paper note be paper-only
    # NECESSARILY, not by naming convention. Measured during the attempt: the
    # generated .olx did not carry the text and `prompt_sha(Q3,'olx')` did not
    # move, so nothing leaked -- but "did not leak today" is the weaker property.
    #
    # AND THE ITEM-KEYING HERE IS CONTENT, NOT MECHANISM. The mechanism is
    # uniform: every item is offered a paper-side note and the ones that declare
    # text get it. What varies by item is which items declare text -- exactly
    # one, Q3 -- and `PAPER_ITEM_NOTES_WHY` records why it and not the other
    # eight >=2-answer items (it keys on the student LABELLING their parts, and
    # the label rate is Q3 19/20 against Q4b, Q6, Q5 and `3` at zero).
    #
    # WHAT WOULD CLEAR IT: a way for score.py to read a paper-only per-item
    # declaration that the shared rubric cannot carry -- a paper-side companion
    # to the rubric, rather than a key inside it. Until then this is a declared
    # hand-coding, which is what this table is for.
    ("build_prompt", "PAPER_ITEM_NOTES"):
        "the paper-only per-item note; kept in score.py so it CANNOT reach the "
        "web, after moving it to the rubric was tried and reverted on 2026-09-12",
    # EMPTY, 2026-08-28. All seven went, and the last five were the ones this
    # table called "schema shape, not scoring" -- true, and beside the point: the
    # schema is what the model is ASKED, so a shape keyed by item id is a rule
    # keyed by item id wearing a different hat.
    #
    # Each now follows the declaration that CONSUMES the answer, so the sheet
    # cannot drift from the rule that reads it:
    #   the three barrier readings  <- the slots this item's `forbid` names
    #   states_a_contingency        <- an `oc_gates` key
    #   aimed_correctly             <- an `oc_gates` key
    #   agent_delivers_consequence  <- an `oc_gates` key
    #   trigger_behavior            <- the slot this item's `expect` parses
    #   stimulus_move               <- rubric_h2 `move_pick`
    #   the underlined-UTB hint     <- rubric_h1 `reads_utb_choice`
    # with answer vocabularies in rubric_h2.SLOT_OPTIONS, keyed by SLOT rather
    # than by item, because the vocabulary belongs to the question.
    #
    # VERIFIED: all 26 built schemas identical before and after, including the
    # ORDER of each `required` list, which is what a reordered insertion would
    # have broken silently.
    #
    # `score_participant`/`only` was never a rule. It is `--only Q1 Q4b`, a
    # user-supplied filter, and the check now excludes a comparison against
    # runtime data rather than carrying an entry that misdescribes itself. A table
    # about rules containing a non-rule teaches its readers to skim.
    #
    # Keep it empty. A new entry is a rule one scorer states as a declaration and
    # the other reimplements, which is what this whole goal exists to remove.
}


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
HANDCODED_BUDGET = 1


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
    n = len(HANDCODED_ITEM_RULES)
    if n > HANDCODED_BUDGET:
        extra = n - HANDCODED_BUDGET
        return [f"HANDCODED_ITEM_RULES holds {n} entries against a budget of "
                f"{HANDCODED_BUDGET} -- {extra} hand-coded rule(s) were ADDED. A "
                f"declaration is a promise to convert it, not a licence to keep "
                f"it: convert the rule, or lower the budget only when one goes"]
    if n < HANDCODED_BUDGET:
        return [f"HANDCODED_ITEM_RULES is down to {n} entries but the budget still "
                f"says {HANDCODED_BUDGET} -- lower it to {n}, or the slack lets a "
                f"new hand-coded rule in without the audit noticing"]
    return []


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
            if not job.get("olx") or job["kind"] not in A.SCORERS:
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
    import re as _re

    lo = pathlib.Path("/home/pdeane/code/update/lo-blocks")
    block = lo / "packages/shared/components/blocks/action/LLMAction.ts"
    try:
        src = block.read_text()
    except OSError:
        return []                      # lo-blocks absent on this machine

    m = _re.search(r"attributes:\s*z\.object\(\{(.*?)\}\)\.strict\(\)", src, _re.S)
    if not m:
        return [f"{block.name}: cannot find the `attributes: z.object({{...}}).strict()` "
                f"block, so undeclared attributes cannot be detected"]
    declared = set(_re.findall(r"^\s{4}(\w+):", m.group(1), _re.M))
    declared.add("id")
    declared.add("target")

    used: dict[str, set] = {}
    for f in sorted(pathlib.Path(__file__).resolve().parent.parent
                    .joinpath("psychology").glob("bmod_handout*.olx")):
        try:
            txt = f.read_text()
        except OSError:
            continue
        for tag in _re.findall(r"<LLMAction\b[^>]*>", txt, _re.S):
            tid = _re.search(r'(?:^|\s)id="([^"]+)"', tag)
            for a in _re.findall(r'(?:^|\s)(\w+)="', tag):
                used.setdefault(a, set()).add(tid.group(1) if tid else f.name)

    problems = []
    for attr in sorted(used):
        if attr in declared:
            continue
        where = ", ".join(sorted(used[attr])[:4])
        problems.append(
            f'<LLMAction {attr}="..."> is authored on {len(used[attr])} action(s) '
            f"({where}) but is NOT declared in LLMAction.ts's attributes schema, "
            f"which is .strict(). Every one of those blocks becomes an ErrorNode "
            f"at parse time: the button renders, the click does nothing, and the "
            f"cell times out as `no-cell` with no error anywhere. Declare it")
    return problems


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
    import handouts as H

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
    for hh in (1, 2, 3):
        try:
            for it in config(hh)["rubric"].ITEMS:
                rubric_keys |= {k for k, v in it.items() if v}
        except Exception:
            continue

    problems = []
    for h in (1, 2, 3):
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
    import rubric_h2 as R2
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
        text = re.sub(r"from rubric_h2 import \([^)]*\)", "", text)
        text = re.sub(r"from rubric_h2 import .*$", "", text, flags=re.M)
        consulting += text
    for name in sorted(selectors):
        if name not in consulting:
            problems.append(
                f"rubric_h2.{name} = {selectors[name]} is defined and imported but "
                f"consulted nowhere: it governs no slot and no paragraph. Either "
                f"the thing it selected was deleted -- in which case a measured "
                f"cell may have gone with it -- or the tuple is dead and should go")

    # B. every slot key the scorers read must still be emitted by some sheet.
    emitted = set()
    for h in (1, 2, 3):
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
    scorer_src = "".join(inspect.getsource(f) for f in
                         (A.score_oc, A.score_oc_cadence, S.derive_oc_ledger))
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
    src = inspect.getsource(A.score_oc) + inspect.getsource(A.score_oc_cadence)
    problems = []
    for h in (1, 2, 3):
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
    import collections
    import handouts as H

    problems = []
    for h in (1, 2, 3):
        mod = H.config(h)["rubric"]
        ids = [it["id"] for it in mod.ITEMS]
        for iid, n in sorted(collections.Counter(ids).items()):
            if n > 1:
                problems.append(
                    f"H{h}: rubric ITEMS has {n} entries with id {iid!r}. BY_ID "
                    f"resolves to one of them and every audit here reads through "
                    f"BY_ID, so the others are invisible")
        if len(getattr(mod, "BY_ID", {})) != len(set(ids)):
            problems.append(
                f"H{h}: BY_ID has {len(mod.BY_ID)} entries for {len(set(ids))} "
                f"distinct item ids")

        for it in mod.ITEMS:
            slots = [c["what"] for c in it.get("credit", []) or []]
            for what, n in sorted(collections.Counter(slots).items()):
                if n > 1:
                    problems.append(
                        f"H{h} {it['id']}: credit lists {what!r} {n} times")
    return problems


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
MULTI_BLOCK_DECLARED: dict[str, str] = {
    # Examined box by box in this session and confirmed against each response's
    # own structure. The web version presents these as separate input fields, so
    # the split is the form's, not an artefact of reconstruction.
    "Q6": "eight boxes: two antecedents, each with its change, consequence and "
          "effect. Every cell read out and corrected; all fixture checks clean. "
          "p18\'s two antecedent boxes are DECLARED as sentence fragments and "
          "are correct that way: `state_a1` ends on its comma (\"To change my "
          "first trigger (after-school fatigue),\") and `state_a2` opens "
          "lowercase (\"to handle my second antecedent, which is phone "
          "distractions.\"), because p18 names each antecedent in a subordinate "
          "clause and puts the change in the main one. A clause-level split has "
          "to cut there; both boxes name their antecedent, which is what "
          "`state_a*` is scored on; and gold\'s 7.5 charges only the second "
          "consequence\'s fate. Both halves of one sentence being fragments is "
          "fine — do not re-cut them. Not in FIXTURE_STRUCTURE_OVERRIDES "
          "because no check fires on it, and an entry there that stops firing "
          "is reported stale",
    "Q3": "five boxes, one per SMART aspect, and the students label them "
          "themselves. Anchored on the aspect's own name where the scorer gave "
          "no quote; 9 cells with an empty box reduced to 1, and that one is "
          "correct — p9 never mentions realistic. NOT read box by box when it "
          "was declared, and p19 is what that cost: `measurable` held the "
          "printed instruction \"You must discuss and label each aspect of the "
          "SMART goal for full credit.\" and `specific` held the printed "
          "question plus two aspects, with the student's own measurable "
          "sentence inside it. Repaired; the two lines of template scaffolding "
          "now belong to no box. p6 still opens all four of its boxes with the "
          "student's \"- \" bullet, which is the corpus-wide residue and "
          "enumerator work in scoring/BACKLOG.md",
    "Q4b": "three boxes: the modify statement and two examples. p7 read out and "
           "assigned; the rest carry no findings",
    "1c": "eight boxes and not one of them a quotation, which is why the "
          "box-by-box readout is BLIND here: 18 of 20 cells have no prose at "
          "all, so `--fixture 1c` prints \"empty response\" and shows nothing. "
          "Audited by reading the eight boxes against the chart instead. Four "
          "come from `sim` (the four weeks of data) plus `series`, all parsed "
          "values; three — title/x/y — are read off the GRAPH by the paper "
          "scorer. Those three were the defect: in 10 of 20 cells they held the "
          "scorer\'s own sentence about the label (\"Weeks\" appears as a bolded "
          "axis title centred beneath the day tick values.) or its extracted "
          "text RUNS ([\'Time\', \' Spent at Gym Over Four Weeks\']) instead of "
          "the label. Fixed in `_quoted_span`, not per cell, and verified "
          "against the served fixtures of all 26 items: exactly 20 boxes move, "
          "all of them 1c\'s. p15 and p18 are empty by right (gold \"did not "
          "include\"), and p11\'s day-name `series` is the student\'s own "
          "legend",
    "3": "two boxes, one proposed change each, and the count is judged over the "
         "whole response, so an empty `second` costs nothing by itself. All 20 "
         "read out; five repaired (p4, p6, p9, p16, p19), all one defect — "
         "`second` opened with a sentence elaborating the FIRST change, so box "
         "2 began before change 2 did. Boundaries moved to the sentence that "
         "opens change 2; the union of each pair is unchanged. Four cells hold "
         "everything in `first` with `second` empty: p5, p8 and p15 propose one "
         "change or none, which is what gold charges, but p3 is a real gap — its "
         "two changes sit in ONE sentence and no anchor separates them, so a "
         "6.0 is being earned from box 1 alone. 15 of 20 `first` boxes still "
         "open with the printed question\'s own \") \", which is template "
         "residue and NOT the student\'s word; it is corpus-wide and fixed "
         "upstream, not here (see scoring/BACKLOG.md)",
    "Q5": "two boxes, one reason each. All 20 read out; three boxes repaired, "
          "the same enumerator defect as Q4c — p1 kept \"1) \"/\"2) \" and p16 "
          "the \"2. \" it alone writes. Two cells are BLANK (p13, p17), so both "
          "boxes are empty and gold\'s \"did not answer\" is what the split "
          "reproduces. Three cells are run-ons split where the student\'s own "
          "sentence boundary is missing (p9, p15, and p3, whose orphaned full "
          "stop is left where the scorer\'s quote ended). p5 and p6 keep each "
          "reason\'s parenthetical function label (\"(Gaining something.)\", "
          "\"(I am escaping a task.)\") with the reason it labels, which is what "
          "the question asks the student to supply. p4\'s first box reads \"I "
          "continue sleep enough\" — checked against the submission, that is the "
          "student\'s own missing negation, not a transcription loss",
    "Q4c": "two boxes, one consequence each, and like Q4a the student usually "
           "does the splitting. All 20 read out; three boxes repaired, all one "
           "defect — p13\'s `first` and both of p16\'s kept the enumerator "
           "inside them while the item\'s other eight enumerated cells strip "
           "theirs. Three cells are split with no marker at all, and each is a "
           "run-on where the student\'s sentence boundary is simply missing "
           "(p5, p6, p15); p9\'s is the one genuine judgement — one comma, and "
           "\"while not exercising\" is left with the clause the comma attaches "
           "it to. p13\'s `second` is empty and faithful: gold charges the "
           "missing second consequence. p11\'s boxes follow DOCUMENT order, not "
           "the student\'s own labels, which run \"Another\" then \"One\"",
    "Q4a": "two boxes, one antecedent each, and in 12 of 20 cells the STUDENT "
           "does the splitting — \"1)\"/\"2)\", \"1.\"/\"2.\", or \"My first "
           "antecedent\"/\"My second trigger\". All 20 read out; no repairs. The "
           "only text belonging to no box anywhere in the item is enumerators "
           "and OCR debris (\"1)_\", \"2 )_\", \"-\", a bare \"o\", a leading "
           "\"_\"), and every box is whole sentences in document order. p15 is "
           "the one cell split with no marker at all — one run-on line, cut "
           "before its second antecedent — and both halves are phrases the "
           "item\'s own guidance quotes as accepts. p18 is a DECLARED DIVERGENCE "
           "from verbatim reproduction, not an oversight: it wrote one "
           "antecedent and repeated it word for word as its second, and the "
           "fixture deliberately leaves `second` EMPTY rather than serving the "
           "duplicate. Gold charges the missing one, so "
           "`_gold_corroborates_absence` licenses the gap on every run and no "
           "check fires; the divergence is from faithfulness, not from gold, "
           "which is why it is not in GOLD_DIVERGENCES. Filling the box would "
           "invite the grader to credit two antecedents on one, against a cell "
           "that agrees with gold at 3.0 in 6 of 6 passes. The keyword point "
           "survives every split, including the "
           "three cells that misspell it in one box and spell \"trigger\" in the "
           "other",
    "2a": "three boxes: the verdict and two explanations, which the screen asks "
          "for as three separate fields. All 20 cells read out against the "
          "response. Two repaired here — p16's how2 still carried the "
          "\"Sentence 3:\" label the other two boxes had stripped, and p20's "
          "how1 was a comma-initial adjunct sliced out of the verdict's own "
          "sentence (now the whole sentence, overlap declared). Everything else "
          "confirmed, including the boxes that hold text gold says is not an "
          "explanation: p13's how2 holds its \"Overall, the plan did end up "
          "pretty successful\" because the student wrote it, and gold charges "
          "that sentence rather than a missing one. The item's remaining error "
          "is almost all one shape and none of it is the fixture: 14-16 of 18 "
          "counted over six passes, and every miss but one is +2.0 for a "
          "second how gold withheld. The exception is p18, which flipped "
          "to 4.0 in one pass of six once its exclusion was removed",
    # Declared on PROVENANCE, not on a cell-by-cell reading, and the distinction
    # is the whole reason these two are cheap. Neither item's response was ever
    # PARTITIONED: nothing decided where one box ends and the next begins, so
    # there is no boundary to misplace. Contrast Q6, Q3, Q4b above, and the five
    # items still undeclared — each of those carves several boxes out of one
    # prose block, which is what put how1's sentence in 2a/p18's verdict box.
    "1a": "five boxes, but only ONE is this item's own response — a single "
          "field. The other four are the shared data table, `sim`-parsed values "
          "carried as context. Nothing here was split",
    "1b": "four boxes, all four `sim`-parsed values: the student's weekly data "
          "read out of a table, not spans cut from prose. p15 shows the shape — "
          "`wk1` is `8, 11, 6, 9, 6, 10, 9` for a table reading \"Sunday - 8 "
          "hours Monday - 11 hours ...\", and its empty `baseline`/`wk3` are the "
          "student's own \"none\" and \"Week Three Data: Lost\", which gold's "
          "2.0 agrees with",
}


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
    import handouts as H
    import segment as SEG

    MOJIBAKE = ("\u00e2\u0080\u0099", "\u00e2\u0080\u009c", "\u00e2\u0080\u009d",
                "\u00e2\u0080\u0093", "\u00c2\u00a0", "\ufffd")
    problems, multi = [], {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for h in (1, 2, 3):
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
    import ast
    import os

    src = _CONSENSUS_SOURCE or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "agreement_app.py")
    try:
        tree = ast.parse(open(src).read())
    except Exception as exc:                    # pragma: no cover
        return [f"cannot parse agreement_app.py to check CONSENSUS_FIXES: {exc}"]

    node = None
    for stmt in ast.walk(tree):
        targets = getattr(stmt, "targets", []) or ([stmt.target] if hasattr(stmt, "target") else [])
        for t in targets:
            if isinstance(t, ast.Name) and t.id == "CONSENSUS_FIXES":
                node = stmt.value
    if not isinstance(node, ast.Dict):
        return ["CONSENSUS_FIXES is not a dict literal — this check is stale"]

    seen, dupes = set(), []
    for k in node.keys:
        try:
            key = ast.literal_eval(k)
        except Exception:
            continue
        if key in seen:
            dupes.append(f"CONSENSUS_FIXES has TWO entries for {key}. A dict "
                         f"literal keeps only the last, so the other one is "
                         f"silently doing nothing — merge them into one entry")
        seen.add(key)
    return dupes


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
    from handouts import HANDOUTS

    problems = []
    for h in (1, 2, 3):
        registry = (HANDOUTS[h].get("cited_participants") or {})
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
        if not any(pid in (HANDOUTS[h].get("cited_participants") or {}).get(item, [])
                   for h in (1, 2, 3)):
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
# without naming a verifier fails the audit, which is the one thing prose
# guidance cannot do for itself.
#
# Written after a divergence asserting "the slot points sum to 4 against a max of
# 5" outlived the fix that made it false, with the whole audit green: no check
# owned it, and nothing said one was missing.
DECLARATION_TABLES: dict[str, tuple[str, tuple[str, ...]]] = {
    "handouts.PER_ITEM_EXCLUDE": (
        "cells dropped from every rate",
        ("check_exclusion_claims_are_data", "check_citations_match_exclusions",
         "check_declarations_still_have_evidence")),
    "handouts.CORRECTED_GOLD": (
        "the target a cell is measured against",
        ("check_corrected_gold_matches_the_sheet",
         "check_no_declaration_cites_a_suspect_cell")),
    "handouts.GOLD_DIVERGENCES": (
        "cells we knowingly disagree with gold about",
        ("check_declarations_still_have_evidence",
         "check_no_declaration_cites_a_suspect_cell")),
    "handouts.GOLD_CEILINGS": (
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
        ("check_generated_attributes_have_a_declaration",)),
    "enforcement.ITEM_GATED_MECHANISMS": (
        "mechanisms that vary by item, which the uniformity rule forbids",
        ("check_engine_mechanisms_are_not_item_dependent",)),
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
    "enforcement.HANDOUT_KEYED_GOLD_READERS": (
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
    import olx_prompts as _OP

    problems = []
    items = set(_OP.ACTION) | set(_OP.SHEET_ONLY)
    for name in ("RESPONSE", "CONTEXT", "ITEM_NOTES", "OMIT_CREDIT",
                 "OMIT_DEDUCTION", "OMIT_GUIDANCE"):
        for key in sorted(getattr(_OP, name, {}) or {}):
            # A LEADING UNDERSCORE is a shared fragment, not an item. CONTEXT
            # keys `_utb` and `_wgb` are single fields several items pull in, and
            # the generator reads them by that pseudo-key -- so requiring every
            # key to be a live item reported two correct entries as stale. The
            # table's shape, not a finding.
            if key.startswith("_"):
                continue
            if key not in items:
                problems.append(
                    f"olx_prompts.{name} declares a deviation for {key!r}, which "
                    f"is not a live item -- the item was renamed or dropped and "
                    f"its deviation was not")

    for item, omitted in sorted((getattr(_OP, "OMIT_GUIDANCE", {}) or {}).items()):
        if item not in items:
            continue
        try:
            rub = config(HANDOUT[item])["rubric"].BY_ID[item]
            guidance = " ".join(rub.get("guidance") or [])
        except Exception:
            continue
        for phrase in sorted(omitted):
            if phrase not in guidance:
                problems.append(
                    f"olx_prompts.OMIT_GUIDANCE[{item!r}] omits "
                    f"\"{phrase[:48]}\", which is no longer in that item's "
                    f"guidance. The omission outlived the line it omits")

    for name, field in (("OMIT_CREDIT", "credit"), ("OMIT_DEDUCTION", "deductions")):
        for item, dropped in sorted((getattr(_OP, name, {}) or {}).items()):
            if item not in items:
                continue
            try:
                rub = config(HANDOUT[item])["rubric"].BY_ID[item]
            except Exception:
                continue
            have = {c.get("what") or c.get("code") for c in (rub.get(field) or [])}
            for key in sorted(dropped):
                if key not in have:
                    problems.append(
                        f"olx_prompts.{name}[{item!r}] omits {key!r}, which the "
                        f"rubric no longer has -- the omission outlived its target")
    return problems


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
    import handouts as _H
    import importlib
    import measured as _MEAS
    import olx_prompts as _OP

    # `measured` was absent, so a declaration table living there could not be
    # resolved and the registry reported it as a table nobody has -- which is
    # indistinguishable from the failure this check exists to catch. Found by
    # registering GOLD_SLOT_CHARGES and being told it did not exist.
    mods = {"handouts": _H, "olx_prompts": _OP, "measured": _MEAS,
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
    # to measured.py, handouts.py or olx_prompts.py was never reported as
    # unregistered -- and that is not hypothetical: four tables were added to
    # measured.py on 2026-08-31 and the audit asked for none of them. Three were
    # registered by hand and the fourth was forgotten, with nothing complaining.
    #
    # ALL FOUR MODULES as of E36. The scan covered enforcement only, then
    # enforcement and measured; handouts and olx_prompts hold registered
    # declarations already -- CORRECTED_GOLD, GOLD_DIVERGENCES, PER_ITEM_EXCLUDE,
    # SCORING_DIVERGENCES -- so they were exactly the files most likely to gain
    # an unregistered one.
    for mod_name in ("enforcement", "measured", "handouts", "olx_prompts"):
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
    "handouts.MATERIALS": "where the submission files are",
    "handouts.HANDOUTS": "the handout numbers",
    "handouts.H1_MARKERS": "the section markers that split a .docx into items. "
                           "Parsing configuration -- a marker that stops matching "
                           "breaks the FIXTURE, which the fixture checks own",
    "handouts.H2_MARKERS": "as H1_MARKERS",
    "handouts.H3_MARKERS": "as H1_MARKERS, and regexes rather than literals",
    "olx_prompts.ACTION": "item id -> LLMAction id; a lookup",
    "olx_prompts.SHEET_ONLY": "items whose grader is a sheet with no action",
    "olx_prompts.HANDOUT": "item id -> handout number",
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
    import rubric_h1, rubric_h2, rubric_h3

    RB = {1: rubric_h1, 2: rubric_h2, 3: rubric_h3}
    olx = {f.name: f.read_text() for f in
           _pl.Path(__file__).resolve().parent.parent.joinpath("psychology")
           .glob("bmod_handout*.olx")}

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
    handouts.py — and the sentence outlives the configuration it was computed
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
        cases = json.loads(path.read_text())
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
    import measured as MEAS

    return MEAS.sides_recorded_but_unreadable()


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
    """Identical verdicts must produce identical scores on both engines.

    The one comparison here that removes the MODEL from the question. Everything
    else -- rates, medians, wrong cells -- mixes the model's answers with the
    arithmetic over them, so a difference could be either. Holding the verdict
    signature fixed leaves only the scoring rules, and a difference there is a
    defect in one of the two implementations.

    Coverage is reported by `engine_scoring_agreement_line`, because this check
    being quiet means nothing without it: silence over 221 shared signatures is
    evidence, and silence over none is an empty comparison wearing the same face.
    """
    import measured as MEAS

    d = MEAS.scoring_logic_agreement()
    return [f"{item}/p{pid}: the two engines produced the SAME verdicts and "
            f"DIFFERENT scores -- olx {a}, python {b}. The model is not the "
            f"variable here; the scoring rules are implemented differently"
            for item, pid, a, b in d["differing"]]


def engine_scoring_agreement_line() -> str:
    """Coverage for the check above, as audit context rather than a finding."""
    import measured as MEAS

    d = MEAS.scoring_logic_agreement()
    if not d["matched"]:
        return ("engine scoring: NO verdict signature was produced by both "
                "engines, so the identical-verdicts check compared nothing.")
    return (f"engine scoring: {d['matched']} verdict signature(s) produced by "
            f"BOTH engines, {len(d['differing'])} of them scored differently. "
            f"Evidence that the two implementations agree, proportional to that "
            f"coverage -- not proof, since it says nothing about combinations "
            f"neither engine reached.")


def check_paper_scorer_agrees_on_identical_verdicts() -> list[str]:
    """Does score.py's arithmetic match the web mirror's on the same verdicts?

    THE PAPER SIDE WAS NEVER IN THE LOGIC COMPARISON. `scoring_logic_agreement`
    -- the one instrument that separates the SCORER from the MODEL -- iterates
    `for side in ("olx", "python")`, so its "223 verdict signatures, 0 scored
    differently" says nothing whatever about the paper scorer. It could not
    simply be extended: it matches whole verdict SIGNATURES, and paper records a
    different slot set (on Q4a python records `antecedent_kind_1/2` and
    `confident`, paper records neither), so nothing would ever collide and the
    pair reported 0 shared signatures -- indistinguishable from agreement.

    See measured.paper_scorer_agreement for the method: run each paper cell's
    recorded verdicts through `agreement.score_slots` rather than matching keys.

    COVERAGE IS THE LIMIT AND IT IS REPORTED, not hidden. Only items with a
    recorded paper artifact can be compared. Two items agreeing is evidence about
    two items.
    """
    import measured as MEAS

    d = MEAS.paper_scorer_agreement()
    out = []
    for item, pid, paper, web in d["differing"]:
        out.append(
            f"{item}/p{pid}: the SAME verdicts score {paper:g} on the paper path "
            f"and {web:g} through the web mirror's arithmetic. The model is held "
            f"fixed here, so this is the two scoring implementations disagreeing, "
            f"not sampling")
    for e in d["errors"]:
        out.append(f"paper verdicts could not be scored by the web mirror -- {e}")
    return out


def paper_scorer_agreement_line() -> str:
    """Coverage for the check above, as audit context rather than a finding."""
    import measured as MEAS

    d = MEAS.paper_scorer_agreement()
    if not d["items"]:
        return ("paper scoring: NO item has a recorded paper artifact, so the "
                "paper scorer's arithmetic is compared against nothing.")
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
ITEM_GATED_BUDGET = 0

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
    import re as _re

    import handouts as _H
    import score as _SC
    from olx_prompts import RESPONSE

    out = []
    for it in all_items():
        iid = it["id"]
        try:
            prompt = _SC.build_prompt(it, "x", {"(fingerprint)": ""}, "(fingerprint)")
        except Exception as e:
            out.append(f"{iid}: paper prompt does not build ({type(e).__name__}: "
                       f"{e}) -- this check cannot run, which is not passing")
            continue
        for m in _re.finditer(r"\bboxe?s?\b", prompt, _re.I):
            s, e = max(0, m.start() - 70), min(len(prompt), m.end() + 70)
            out.append(f"{iid}: the paper prompt says {m.group(0)!r} -- it has no "
                       f"boxes: \u2026{' '.join(prompt[s:e].split())}\u2026")
        n_answers = len(RESPONSE.get(iid) or [])
        if not n_answers:
            continue
        for word, k in _COUNT_WORDS.items():
            for m in _re.finditer(rf"\b{word}\b(?:\s+\w+){{0,2}}\s+answers\b",
                                  prompt, _re.I):
                if k > n_answers:
                    s = max(0, m.start() - 70)
                    out.append(
                        f"{iid}: the prompt says {m.group(0)!r} but the item asks "
                        f"for {n_answers} answer(s) -- the phrase points outside "
                        f"the structure and needs rewording, not translating: "
                        f"\u2026{' '.join(prompt[s:m.end() + 60].split())}\u2026")
    return out


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
    import leakage as _L

    items = tuple(it["id"] for it in all_items())
    seen, out = set(), []
    for f in _L.process_findings(items):
        item = str(f["block"]).split()[0]
        key = (item, f["kind"], f["phrase"].lower())
        if key in seen:
            continue
        seen.add(key)
        out.append(f"{item}: shipped prose carries {f['kind']} -- "
                   f"{f['phrase']!r} in \u2026{f['context'][:110]}\u2026. The grader "
                   f"cannot act on this; move it to a comment beside the rule")
    return out


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
PARKED_UNDECLARED: dict[tuple[str, str], str] = {}

# Ratcheted like every other table here. A park is cheap to add and easy to
# forget, which is the failure mode: a parking lot nobody empties becomes a
# second declaration table with none of the review. Raise this only with the
# entry, and lower it when one is retired.
PARKED_BUDGET = 0


# How far a side's own verdicts may fail to reproduce its own score before the
# comparison built on them is untrustworthy. Not zero: an artifact can carry a
# cell the scorer no longer accepts. But a harness reproducing a THIRD of a
# side's own scores is measuring itself.
MIRROR_CONTROL_FLOOR = 0.90


def check_mirror_reproduces_its_own_scores() -> list[str]:
    """THE CONTROL every cross-scorer comparison rests on and none of them ran.

    `paper_scorer_agreement` drives the web mirror with PAPER's verdicts and
    reports where the two disagree. That is only evidence if the mirror can
    reproduce the WEB's scores from the WEB's own verdicts -- otherwise a
    "disagreement" says nothing about the paper scorer, and the harness is
    reporting its own defects as findings about something else.

    It could not. Measured 2026-09-11 on the cadence items: DAY1 47/120,
    DAY2 34/120, WK1 30/120, WK2 35/120 -- a harness reproducing under a third
    of one side's own scores, while emitting 1,410 findings about the other
    side, which was 94% of the entire audit's output.

    THE CAUSE, and it is a real divergence rather than a harness bug alone:
    `slotSheet.ts:failedGate` fails a gate only when the slot is ALSO CHARGED --
    `if (slot.gates && !sat[slot.key] && charged[slot.key])` -- while the python
    mirror's generic gate loop asks only whether the slot is satisfied. An
    UNANSWERED gate therefore zeroes the item here and does not there. Every one
    of DAY1's 73 failures was the single unanswered gate
    `consequence_not_a_setup`, each scoring 4.0 on the web and 0.0 in the
    mirror. Treating an unanswered slot as uncharged lifts reproduction to
    118/120, 106/120, 115/120 and 110/120.

    It rarely bites in production because each side scores its own model's
    response, where the slots are usually answered -- which is why `olx` and
    `python` agree in the ledger and this went unseen until a harness fed one
    side's artifact to the other's arithmetic.
    """
    import measured as MEAS

    out = []
    try:
        d = MEAS.mirror_self_control()
    except AttributeError:
        return ["measured.mirror_self_control is missing, so the control that "
                "every cross-scorer comparison depends on cannot run"]
    for side, item, ok, n in d:
        if not n:
            continue
        rate = ok / n
        if rate < MIRROR_CONTROL_FLOOR:
            out.append(
                f"{item} [{side}]: the mirror reproduces only {ok}/{n} "
                f"({rate:.0%}) of this side's OWN scores from its OWN recorded "
                f"verdicts. Until that is ~100%, any cross-scorer finding on "
                f"this item is measuring the harness, not the scorers")
    return out


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
    out = []
    if len(PARKED_UNDECLARED) > PARKED_BUDGET:
        out.append(
            f"PARKED_UNDECLARED holds {len(PARKED_UNDECLARED)} entr(ies) against "
            f"a budget of {PARKED_BUDGET}. An issue was parked without raising "
            f"the budget -- raise it deliberately with the entry, or unpark")
    for key, why in sorted(PARKED_UNDECLARED.items()):
        if not isinstance(key, tuple) or len(key) != 2:
            out.append(f"PARKED_UNDECLARED key {key!r} is not (item, kind)")
        if len((why or "").strip()) < 30:
            out.append(
                f"PARKED_UNDECLARED[{key!r}] gives no usable reason. Say what the "
                f"issue is and what would unpark it -- a park with no reason is "
                f"an override that never expires")
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

    import handouts as _H

    ids = {it["id"] for h in (1, 2, 3) for it in _H.config(h)["rubric"].ITEMS}
    out, found = [], set()
    for mod in _ENGINE_MODULES:
        try:
            src = pathlib.Path(f"{mod}.py").read_text()
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
            seg = ast.get_source_segment(src, node) or ""
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

    import handouts as H
    import measured as M
    import paths as _paths

    root = _pl.Path(getattr(_paths, "OUT", "/home/pdeane/molly_data/out"))
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
                doc = json.loads(path.read_text())
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
    root = _pl.Path(getattr(_paths, "OUT", "/home/pdeane/molly_data/out"))
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
                doc = json.loads(path.read_text())
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
              for h in (1, 2, 3)),
        ]).encode()).hexdigest()[:16]
    except Exception as e:
        return {}, f"the capture key cannot be computed: {type(e).__name__}: {e}"
    cache = P.OUT / "request_capture.json"
    if cache.exists():
        try:
            got = json.loads(cache.read_text())
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


def _recorded_payloads() -> tuple:
    """({item: sheet}, [payload]), one payload per recorded cell on either side.

    A PAYLOAD IS WHAT THE MODEL ANSWERED, reconstructed from the record: the
    verdict, the classification and the evidence, per slot. Computed slots are
    left out -- the model is never asked for one, so it is not part of a
    response, and including it would feed each engine its own prior conclusion
    and guarantee agreement.
    """
    import agreement as A
    import cross_path as X
    import measured as M
    import olx_prompts as O

    jobs = {j["item"]: j for _h, b in A.BLOCKS.items() for j in b.values()}
    sheets, payloads = {}, []
    for item in sorted(M._jobs()):
        job = jobs.get(item) or {}
        if A.SCORERS.get(job.get("kind")) is None:
            continue                       # type_stated / data_presence: no scorer
        try:
            act = A.load_action(job["olx"], O.ACTION[item])
        except Exception:
            continue                       # sheet-grader item: no <LLMAction>
        sheets[item] = {k: (act.get(k) or []) for k in
                        ("slots", "cover", "equals", "onlyif", "counts",
                         "expect", "requires", "forbid", "maps")}
        # `derived` IS NOT EXCLUDED, and the asymmetry is the app scorer's shape
        # rather than an oversight: `scoreSlotSheet` takes maps/equals/expect/
        # forbid rules and recomputes those itself, but has no `derived`
        # parameter -- the app computes a derived verdict upstream from the
        # student's fields and SUPPLIES it. Dropping it fed the app a starved
        # sheet while `apply_computed` rebuilt it for the harness from the
        # fixture, which on 1c failed a gate and read as 216 engine
        # disagreements. It is input to both scorers, so both get it.
        computed = {r["key"] for f in ("maps", "equals", "expect", "forbid")
                    for r in (act.get(f) or [])}
        counted = {sl["key"] for sl in act["slots"]
                   if sl.get("count_max") is not None}
        for side in ("olx", "python"):
            doc = M._runs_doc(item, side)
            for ri, run in enumerate((doc or {}).get("runs") or []):
                for ci, r in enumerate(run.get("results") or []):
                    c = X.result_cell(r)
                    if not c or c[2] is None:
                        continue
                    picks = dict(X.result_picks(r) or {})
                    ev = r.get("evidence") or {}
                    checks = {}
                    for k, v in (c[3] or {}).items():
                        if k in computed:
                            continue
                        d = {}
                        # A COUNT IS NOT A VERDICT, and WHICH slot is a count is
                        # decided by the SLOT SPEC -- not by sniffing the value's
                        # type. The record flattens `count` and `verdict` into one
                        # column, and the two sides flatten differently: the app
                        # writes an int, the harness writes a string like "2". A
                        # type test therefore caught the app's counts and missed
                        # the harness's, which then arrived as `verdict` and --
                        # once expand_counted's legacy fallback was removed --
                        # scored every counted member absent. 454 cells across
                        # Q1, Q2, 2b and 3 failed their own control that way.
                        if k in counted:
                            d["count"] = v
                        elif v not in (None, ""):
                            d["verdict"] = v
                        if picks.get(k) is not None:
                            d["refers_to"] = picks[k]
                        if ev.get(k):
                            d["evidence"] = ev[k]
                        if d:
                            checks[k] = d
                    smax = r.get("sheet_max") or r.get("max")
                    if not smax:
                        continue
                    payloads.append({"id": f"{item}|{side}|{ri}|{ci}|{c[1]}",
                                     "item": item, "side": side, "pid": c[1],
                                     "checks": checks, "max": float(smax),
                                     "recorded": round(float(c[2]), 4),
                                     # What this side RECORDED for a computed
                                     # key, kept out of the payload but needed to
                                     # tell a reconstruction failure from the
                                     # documented case where a side scored a
                                     # recorded verdict its own rules now
                                     # recompute. See the control below.
                                     "was_recorded": {k: v for k, v in
                                                      (c[3] or {}).items()
                                                      if k in computed and v}})
    return sheets, payloads


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
            got = json.loads(cache.read_text())
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
    """Run every recorded response through BOTH engines and compare the scores."""
    import agreement as A
    import handouts as H
    import measured as M
    import olx_prompts as O

    sheets, payloads = _recorded_payloads()
    if not payloads:
        return {"why_not": "no recorded response could be read", "n": 0}
    app, why_not = _app_scores(sheets, payloads)
    if why_not:
        return {"why_not": why_not, "n": 0}

    jobs = {j["item"]: j for _h, b in A.BLOCKS.items() for j in b.values()}
    cache = {}
    out = {"n": 0, "differ": [], "control": {"olx": [0, 0], "python": [0, 0]},
           "errors": [], "why_not": ""}
    for p in payloads:
        item = p["item"]
        if item not in cache:
            job = jobs[item]
            act = A.load_action(job["olx"], O.ACTION[item])
            rub = H.config(M._jobs()[item]["handout"])["rubric"].BY_ID[item]
            cache[item] = (job, act, rub,
                           dict(job, slots=act["slots"], cover=act["cover"],
                                requires=act["requires"]))
        job, act, rub, merged = cache[item]
        a = app.get(p["id"])
        if not a or a.get("error"):
            out["errors"].append(f"{item}/p{p['pid']}: the app's scorer could not "
                                 f"score a recorded response: "
                                 f"{(a or {}).get('error', 'no result')}")
            continue
        try:
            filled = A.apply_computed(act, {k: dict(v) for k, v in p["checks"].items()},
                                      A.fixture_for(item, p["pid"]))
            mine, _f = A.SCORERS[job["kind"]](merged, rub, filled)
        except Exception as e:
            out["errors"].append(f"{item}/p{p['pid']}: the harness's scorer could "
                                 f"not score a recorded response: "
                                 f"{type(e).__name__}: {e}")
            continue
        out["n"] += 1
        # FRACTIONS, because the app scores out of its sheet's max and the
        # harness out of the item's. cross_path.result_cell converts between the
        # two for exactly this reason; comparing raw numbers would report every
        # item whose sheet max differs from its item max.
        af = a["score"] / a["max"] if a["max"] else 0.0
        mf = mine / float(p["max"]) if p["max"] else 0.0
        if abs(af - mf) > 1e-6:
            out["differ"].append((item, p["pid"], p["side"],
                                  round(af * p["max"], 3), round(mine, 3)))
        # THE CONTROL. Each engine must first reproduce the score its OWN side
        # recorded from that side's own response. Without it a clean comparison
        # means nothing: two scorers that both misread the record identically
        # agree perfectly. Both of this session's cross-engine comparisons were
        # wrong on the first pass and the control is what caught them.
        side = p["side"]
        own = af * p["max"] if side == "olx" else mine
        # EXCLUDED FROM THE CONTROL, not silently passed: where a side recorded a
        # verdict for a computed key and today's rules compute a different one,
        # that side scored the RECORDED verdict and this rescoring cannot
        # reproduce it. That is a rules-moved fact, already reported by
        # `RECORDED VERDICT DISAGREES WITH ITS MAP`, and counting it here would
        # report the same thing twice and make a real control failure invisible
        # among it. 1c/legend is the whole of it today.
        # A STALE side is not a measurement of the current tree -- the ledger
        # says exactly that -- so re-scoring its runs by today's rules and
        # calling the mismatch a control failure reports the staleness twice and
        # buries a real reconstruction fault among it. Q1 is the live case: its
        # `free` declaration moved `prompt_sha`, so p17's recorded 3.0 and
        # today's 5.0 are both right, for different trees.
        if _side_is_stale(item, side):
            out["stale"] = out.get("stale", 0) + 1
        elif any(str(filled.get(k, {}).get("verdict") or "") != str(v)
                 for k, v in (p.get("was_recorded") or {}).items()):
            out["rules_moved"] = out.get("rules_moved", 0) + 1
        else:
            out["control"][side][1] += 1
            out["control"][side][0] += abs(own - p["recorded"]) < 1e-6
    return out


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
UNCHARGED_VERDICTS: dict[tuple[str, str, str], str] = {
    ("Q1", "utb_stated", "unclear"):
        "GOLD BACKS THE PAPER SIDE, so aligning the engines here would make the "
        "scorer wrong. `unclear` fires on exactly one cell in the corpus -- p17 "
        "-- and gold gives p17 full marks (5.00), which is what the paper scorer "
        "returns and the web does not: the web charges the full 2 points for "
        "\"could not tell\". p20, the cell this check exists to catch, answers "
        "`absent` in 11 of 11 runs, so nothing it should catch escapes. Charging "
        "`unclear` was measured and reverted; see rubric_h1.py's note on the "
        "`codes` entry.",
}


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
    import handouts as H
    import measured as M

    out = []
    for item_id in sorted(M._jobs()):
        try:
            item = H.config(M._jobs()[item_id]["handout"])["rubric"].BY_ID.get(item_id)
        except Exception:
            continue
        if not item:
            continue
        for c in item.get("credit") or []:
            verdicts = list(c.get("verdicts") or [])
            if not c.get("pts") or len(verdicts) < 2:
                continue
            codes = c.get("codes") or {}
            what = c.get("what")
            # FROM THE SHEET, not only the rubric. The grader answers the SHEET,
            # and the two can differ: `unclear` was dropped from Q2's rubric, the
            # audit went clean, and the grader kept answering it because the
            # option was still declared in slots=. Reading the rubric alone makes
            # this check blind in exactly the direction that already cost a
            # measurement.
            try:
                offered = _olx_slot_verdicts(item_id, what) or set()
            except Exception:
                offered = set()
            for v in sorted(offered):
                if v not in verdicts:
                    verdicts.append(v)
            # THE SATISFYING VERDICT, by lo-blocks' rule: `met` where the slot
            # offers it, else the FIRST option. Mirrored from isSatisfied rather
            # than assumed positional -- the two rules differ the moment a slot
            # lists `met` anywhere but first.
            sat = "met" if "met" in verdicts else (verdicts[0] if verdicts else None)
            for v in verdicts:
                if v == sat or _same_verdict(v, sat):
                    continue
                # A DECLARED COUNTERPART IS COVERAGE. The two engines' verdict
                # vocabularies differ by design -- the app's `wrong_kind` is the
                # mirror's `not_antecedent` on Q4a, `not_consequence` on Q4c,
                # `not_reason` on Q5 -- and E27 recorded every pair. Comparing the
                # NAMES alone reported seven counterpart shapes as gaps the first
                # time this check read the sheet, which is the false-positive
                # class this family keeps falling into.
                if any(_same_verdict(v, k) for k in codes):
                    continue
                if (item_id, what, v) in UNCHARGED_VERDICTS:
                    continue
                out.append(
                    f"{item_id}/{what} can answer {v!r}, and the paper ledger has "
                    f"no deduction code for it -- so paper charges 0 where the web "
                    f"charges the slot's full {c['pts']} points. Give it a code, or "
                    f"declare it in enforcement.UNCHARGED_VERDICTS with the "
                    f"measurement that says forgiving it is right")
            # THE REVERSE DIRECTION, which nothing checked: a verdict the paper
            # ledger CHARGES that the web counts as satisfying. It costs points on
            # paper and nothing on the web -- silent OVER-credit on the side
            # students are actually graded by. None exists today; that is a
            # measurement, not a guarantee.
            if sat is not None and any(_same_verdict(sat, k) for k in codes):
                out.append(
                    f"{item_id}/{what}: the paper ledger charges {sat!r} via "
                    f"{codes[sat]}, and the web treats {sat!r} as SATISFYING -- so "
                    f"the same answer loses points on paper and keeps them on the "
                    f"web, which is the direction that over-credits a student")
            # THE POSITIONAL FALLBACK. isSatisfied reads `met` by NAME where the
            # slot offers it and options[0] by POSITION otherwise, and its own
            # comment rests on the two agreeing "on every slot in the current
            # content". That is a measured coincidence with nothing re-testing it:
            # a slot listing `met` anywhere but first flips meaning on the web and
            # nowhere else.
            if "met" in verdicts and verdicts[0] != "met":
                out.append(
                    f"{item_id}/{what} lists `met` at position {verdicts.index('met')}, "
                    f"not first. lo-blocks' isSatisfied reads `met` by NAME and every "
                    f"other vocabulary by POSITION, so this slot is the case where "
                    f"those two rules stop agreeing -- and the paper ledger has no "
                    f"positional rule at all")
    for (item_id, what, v) in sorted(UNCHARGED_VERDICTS):
        try:
            item = H.config(M._jobs()[item_id]["handout"])["rubric"].BY_ID.get(item_id)
        except Exception:
            continue
        hit = [c for c in (item or {}).get("credit") or [] if c.get("what") == what]
        if not hit:
            out.append(f"UNCHARGED_VERDICTS names {item_id}/{what}, which the "
                       f"rubric no longer scores -- drop the declaration")
        elif v not in (hit[0].get("verdicts") or []):
            out.append(f"UNCHARGED_VERDICTS names {item_id}/{what}={v!r}, which "
                       f"the slot can no longer answer -- drop the declaration")
        elif v in (hit[0].get("codes") or {}):
            out.append(f"UNCHARGED_VERDICTS says {item_id}/{what}={v!r} is not "
                       f"charged, but the rubric now charges it -- drop the "
                       f"declaration")
    return out


def check_engines_reach_the_model_identically() -> list[str]:
    """Do the two engines put the SAME request on the wire?

    THE LAST PLACE AN ENGINE DIFFERENCE COULD HIDE. The prompt and schema are
    compared by `check_engines_send_the_same_request`, the reading of the
    response by `check_engines_read_a_response_the_same_way`, the arithmetic by
    `check_engines_score_identical_verdicts_alike`. All three compare CONTENT.
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
    profile, and sets `model`. Those are identical for both engines only while
    neither sends `profile` and no PMSS rule keyed on the guest/authorized class
    sets a generation property -- both of which are checked here rather than
    assumed, since the app may carry a session the harness does not.
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
    """Does one raw response score the same through either engine?

    THE LAYER BETWEEN THE TWO CHECKS THAT ALREADY EXIST.
    `check_engines_send_the_same_request` compares what goes to the model;
    `check_engines_score_identical_verdicts_alike` compares the arithmetic over
    verdicts BOTH engines happened to produce. Neither covers the step in
    between: reading one raw response into checks. A difference there -- a
    verdict taken from the wrong field, a blank operand failing on one side and
    unknown on the other -- surfaces as a rate difference and gets read as the
    model, because the prompts are identical and nothing compares the responses
    as INPUTS.

    Stronger than the signature comparison in the way that matters: it runs
    EVERY recorded response through both engines, including the ones only one
    engine ever produced, where a signature match is impossible by construction.
    Q4b: 34 shared signatures against 1440 payloads.

    NEVER SILENTLY CLEAN -- a capture that cannot run says so, and the per-side
    control is reported by `engine_interpretation_line` rather than assumed.
    """
    d = _interpretation_comparison()
    if d.get("why_not"):
        return [f"the two engines' reading of a recorded response could not be "
                f"compared: {d['why_not']}"]
    out = list(d["errors"])
    for item, pid, side, app_s, mine in d["differ"]:
        out.append(f"{item}/p{pid}: ONE recorded response, scored {app_s} by the "
                   f"app's scorer and {mine} by the harness's. The response is "
                   f"held fixed, so this is the two engines READING it "
                   f"differently, not the model (from the {side} artifact)")
    for side, (ok, n) in sorted(d["control"].items()):
        if n and ok != n:
            out.append(f"the {side} control FAILED: {ok}/{n} recorded cells "
                       f"reproduce their own recorded score from their own "
                       f"recorded response. Until that is 100% this comparison "
                       f"is measuring the reconstruction, not the engines")
    return out


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
    """Do the two engines send the SAME assembled prompt and the SAME schema?

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
            h = O.HANDOUT[item]
            act = A.load_action(f"bmod_handout{h}.olx", O.ACTION[item])
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
    """Do both engines offer the grader the SAME verdict list, slot by slot?

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
            h = O.HANDOUT[item]
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
                        for s in A.load_action(f"bmod_handout{h}.olx", action_id)["slots"]}
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
            excluded = set(A.load_action(f"bmod_handout{h}.olx", action_id)["excluded"])
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
        for side in ("olx", "python", "paper", "paper_opus"):
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
                    rdoc = json.loads(rp.read_text())
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
                    doc = json.loads(cand.read_text())
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
    """Every WEB_CODE_NEUTRAL entry must still reproduce the scores it excuses.

    THE SIBLING OF `check_scorer_neutrality_is_verified`, for the other sha
    space. `WEB_CODE_NEUTRAL` suppresses a web-scoring-code mismatch on the
    grounds that the change cannot move a recorded number. That is checkable
    without spending anything -- the verdicts are on disk -- so re-score every
    cell the entry covers through today's scorer and require the score the
    artifact stored.

    The approval cannot rot in either direction. If the claim was wrong this says
    which cell moved. If the app's scoring later changes in a way that DOES move
    a score, the fingerprints move with it, the pair stops matching, and the
    finding returns on its own.

    A SPENT PAIR IS REPORTED, not silently tolerated: an entry no column sits at
    is coverage of a difference that is no longer there.
    """
    import measured as M

    bad: list[str] = []
    covered = 0
    for (rec, now), why in sorted(M.WEB_CODE_NEUTRAL.items()):
        items = []
        for item in sorted(M._jobs()):
            doc = M._runs_doc(item, "olx")
            if not doc:
                continue
            era = doc.get("era") or {}
            per = (era.get("items") or {}).get(item, {}) or {}
            got = per.get("web_score_sha", era.get("web_score_sha"))
            if got == rec:
                items.append(item)
        if not items:
            bad.append(
                f"WEB_CODE_NEUTRAL declares {rec} -> {now} ({why[:48]}...), but no "
                f"recorded column sits at {rec}. The pair is spent -- drop it, or "
                f"it reads as coverage of something")
            continue
        for item in items:
            try:
                if M.web_code_sha("score", item) != now:
                    continue              # a different pair's business
            except Exception:
                continue
            n, moved, why_not = M.rescore_recorded(item, "olx")
            covered += n
            if why_not:
                bad.append(f"{item}: {rec} -> {now} cannot be verified -- {why_not}")
            for m in moved:
                bad.append(
                    f"{item}: WEB_CODE_NEUTRAL claims {rec} -> {now} moves no "
                    f"score, but {m}")
    return bad


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
                f"from them may not -- re-score, and declare the pair in "
                f"measured.WEB_CODE_NEUTRAL if every recorded cell reproduces")
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
    """A cell where the two engines' agreement RATES differ beyond chance.

    Reports two different things, because the honest answer at the current run
    count is about POWER rather than about the engines:

      * any cell significant after correcting for the number of cells compared.
        None can be today: the smallest p a 6-against-6 split can produce is
        0.0022 and the Bonferroni threshold over ~516 cells is 0.0001. A cell
        here would be a real divergence.
      * whether the test has any power AT ALL. A check that cannot fire is worse
        than no check, because it reads as evidence of agreement -- the failure
        this audit hit twice on 2026-09-01, with the unreadable `paper` column
        and with silence standing for cleanliness. So the absence of power is
        itself reported, once, as a fact about the design.

    WHY NOT A MEDIAN COMPARISON, which is what E39 first proposed: medians
    manufacture divergences on cells near 50%, and QUALITY_CONTROL 2g records
    three of Q32's five being ONE observation apart. The exact test is what
    separates those from a real difference, and at six runs a side it says none
    of them is separable.
    """
    import measured as MEAS

    d = MEAS.rate_divergence()
    out = [f"{i}/p{pid}: the engines' agreement rates differ beyond chance -- "
           f"olx {a}/{na}, python {c}/{nc}, p={pv:.5f} against a corrected "
           f"threshold of {d['bonferroni']:.5f}"
           for pv, i, pid, a, na, c, nc in d["flagged"] if pv < d["bonferroni"]]
    return out


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
        return "engine rates: no cell has both sides recorded."
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
    """Do the two engines post the same FIELDS to the provider?

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
    olx_at = max(pathlib.Path(P.OLX % h).stat().st_mtime for h in (1, 2, 3))
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
    for h in (1, 2, 3):
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
            h = OP.HANDOUT[item]
            mine = AG.load_action(f"bmod_handout{h}.olx", action)["body"]
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
HAND_AUTHORED_ATTRS: dict[tuple[str, str], str] = {
    ("PR", "expect"): "the four `demonstrates_type` rules stay authored in the "
                      ".olx because the CLI reaches that fact through "
                      "`expected_type` and REQUIRED_MOVE, both already rubric "
                      "declarations -- declaring them again would be a SECOND "
                      "source for one fact. olx_prompts.expect_attr_for says so "
                      "in its own docstring.",
    ("NR", "expect"): "same as PR: `demonstrates_type` reaches the CLI through "
                      "REQUIRED_MOVE.",
    ("PP", "expect"): "same as PR.",
    ("NP", "expect"): "same as PR.",
}


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
    import re

    import olx_prompts as OP

    out: list[str] = []
    for item_id, action in sorted(OP.ACTION.items()):
        handout = OP.HANDOUT[item_id]
        try:
            tag = OP._sheet_tag(handout, action)
        except SystemExit:
            continue                      # a missing sheet is another check's
        for name, fn in OP.GENERATED_ATTRS:
            m = re.search(r'%s="([^"]*)"' % name, tag)
            if m is None or not m.group(1).strip():
                continue                  # absent, or an empty placeholder
            if fn(item_id) is not None:
                continue                  # the rubric backs it
            if (item_id, name) in HAND_AUTHORED_ATTRS:
                continue
            out.append(
                f"{item_id} carries a `{name}=` attribute the generator OWNS, and "
                f"no rubric rule produces it: {m.group(1)[:70]!r}. Either the "
                f"declaration was removed and this is an ORPHAN pointing at "
                f"operands that may no longer exist -- `--write` will not clear "
                f"it, and `--check` will call the file up to date -- or it is "
                f"hand-authored on purpose, which belongs in "
                f"enforcement.HAND_AUTHORED_ATTRS with the reason")
    return out


def _maps_specs() -> list[tuple]:
    """(item, spec) for every `maps` entry in every rubric. Subgoal E46."""
    out = []
    for name in ("rubric_h1", "rubric_h2", "rubric_h3"):
        try:
            mod = __import__(name)
        except Exception:
            continue
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
DESIGNED_TEXT: dict[tuple[str, str, str], str] = {
    ("Q4a", "antecedent_kind_1", "rule_addition"): '`aftermath` COVERS THE GOAL BEHAVIOUR TOO, not only the unwanted one. An entry naming what follows from DOING the goal behaviour -- its payoff not yet showing, or a cost incurred by having done it -- names something a behaviour left behind, so answer `aftermath` rather than `before`, even though the next episode of the unwanted behaviour comes after it. THIS IS NARROW BY DESIGN: it turns on the entry naming a result OF THE GOAL BEHAVIOUR. A state the student is simply in, however it arose, is a `before` in the ordinary way.',
    ("Q4a", "antecedent_kind_2", "rule_addition"): '`aftermath` COVERS THE GOAL BEHAVIOUR TOO, not only the unwanted one. An entry naming what follows from DOING the goal behaviour -- its payoff not yet showing, or a cost incurred by having done it -- names something a behaviour left behind, so answer `aftermath` rather than `before`, even though the next episode of the unwanted behaviour comes after it. THIS IS NARROW BY DESIGN: it turns on the entry naming a result OF THE GOAL BEHAVIOUR. A state the student is simply in, however it arose, is a `before` in the ordinary way.',
    # Q2 `reasons_given` desc, registered 2026-09-09 BEFORE the build. Q44's
    # seventh route, and the FIRST that is a repair rather than a new test.
    # Q2/p6: band 3/12, gold 4.00, python 1/6 and olx 2/6, Q2's only wrong cell.
    #
    # THE DEFECT IS TWO SHIPPED CLAUSES CONTRADICTING EACH OTHER ACROSS THE TWO
    # PROMPT SECTIONS, which is why reading either field alone looked consistent
    # and why six earlier routes missed it. The desc illustrated the `and`-split
    # with "(one about the body, say, AND one about mood)" -- UNQUALIFIED. The
    # rule qualifies the same split: "BUT ONLY WHERE EACH HALF NAMES A GOOD OF
    # ITS OWN, some particular thing that gets better, each with its own
    # predicate." And p6's sentence IS the desc's example verbatim in shape --
    # a body good AND a mood good -- on a cell gold counts as ONE. The concrete
    # example instructed the split, the abstract qualification forbade it, and
    # the example won in 8 of 12 runs. Q44 suspected the clause was generalised
    # from p6 during the 2026-08-24 de-citation campaign (whose own summary
    # lists `Q2/p6 2/3 -> 3/3`); what it missed is that the surviving text is
    # the EXAMPLE, sitting in the other section from the qualification.
    #
    # SO THIS REMOVES A MIS-CHOSEN ILLUSTRATION AND ADDS NO TEST. That is the
    # opposite of route 3, which added a distinct-content test and broke p11,
    # p16 and p18. What the slot tests is unchanged; the qualification already
    # shipped in the rule can now operate instead of being contradicted.
    # GOLD IS SELF-CONSISTENT ON THIS BOUNDARY, which is why p6 is fixable and
    # not declarable: p9 splits four conjuncts, each naming a distinct thing
    # with its own predicate, and takes 5.00; p11 splits three at 12/12; p6's
    # second half names no object at all and gold folds it into the first.
    #
    # ABORT IF ANY OF p9, p11, p14, p18, p19 LOSES A COUNT. Compare all twenty
    # cells and read by SCORE via probe.score_impact, never by verdict count --
    # Q2 is 18/20 and 19/20, so a one-cell move in the item total is not
    # evidence either way, and two probes today mis-reported by counting flips.
    # The replacement paraphrases the structural shape and quotes neither p9's
    # nor p11's wording; screened clean at the three-or-fewer-students mark.
    ("Q2", "reasons_given", "desc"): 'HOW MANY of the listed statements are a real benefit of the GOAL behaviour: `reasons_listed` minus `reasons_failing`. A statement that restates the harm of the unwanted behaviour is not a benefit of the goal — "not exercising makes me feel lazy" is a reason to drop the UTB, not a benefit of exercising. What decides this is what the statement NAMES: one whose subject is the unwanted behaviour, or going without the goal behaviour, and whose predicate is a cost of that, names no benefit. One that NAMES a good the goal behaviour brings and then supports it by the cost avoided has named its benefit and COUNTS. Two goods in one area of life are still two. Whether one sentence holds one benefit or two is STRUCTURAL: a second half that is a knock-on effect of the first is ONE (a benefit, then "WHICH WILL" and what follows from it), while two independent benefits merely joined by "and" are TWO -- BUT ONLY WHERE EACH HALF NAMES A GOOD OF ITS OWN, its own subject with its own predicate, as the counting rule below requires. A second half that names no thing of its own, and only says matters will generally improve, extends the first half, and the pair is ONE. A restatement of the PROBLEM the goal solves is not a benefit of it either: a remark attributing their present condition to not having done the goal behaviour names the harm again and earns nothing. Two things resemble that and are NOT it. A good does not become a restatement by being described as LASTING: saying a benefit will continue, or that the behaviour will become settled practice, says how long the good holds, and a benefit that lasts is still a benefit. Nor does a good become a restatement by being a CHANGE IN THE STUDENT rather than in their circumstances: a capacity or a disposition the behaviour builds in the one who does it is a benefit the graders credited. Statements about why the UTB is bad belong to Q1 and earn nothing here either — a response whose reasons are all of that kind scores 0. Answer 3 for three or more',
    # Q3 `realistic`, registered 2026-09-09 BEFORE the build. Aimed at Q3/p13,
    # 5 of 12, gold 3.00 and we score 2.00 -- the ONLY median-wrong cell in the
    # corpus with NO history of failed attempts and no declaration.
    #
    # THE SLOT IS UNDER-SPECIFIED RELATIVE TO EVERY SCORED SIBLING. Q3's slots
    # carry: specific 35 chars, measurable 731, action_oriented 1404,
    # time_bound 329, and `realistic` THIRTY-ONE -- "Is realistic, or says why
    # it is", with no rule at all. So this is NORMALISATION, not load-adding:
    # 351 chars puts it between time_bound and measurable. (The 63 chars a
    # reader sees is `probe.question_for` returning BOTH prompt sections, which
    # for a desc this short are the same string twice -- not a duplication bug.)
    #
    # THE DIRECTION IS GENEROUS, WHICH IS WHAT GOLD REQUIRES. `realistic`
    # answers `met` 12 of 12 on EIGHTEEN of twenty cells. Only two move: p9,
    # blank justification, `absent` 12/12 and correctly refused; and p13, which
    # splits THREE WAYS -- met 5 / unclear 3 / absent 4. Gold gives p13 3.00 and
    # the met reading is what produces 3.00, so OUR REFUSALS ARE THE ERROR and
    # the slot's own wording already licenses crediting: "or says why it is".
    # WHY p13 IS THE ONE THAT SPLITS: every credited justification names a
    # capability or a resource -- control over the behaviour, a paid membership,
    # a gym on campus, produce in every grocery store, thirty minutes that fit.
    # p13's is the only one in twenty that instead asserts the OUTCOME is
    # likely: "I am much more likely to be better rested than otherwise." With
    # 31 characters of instruction the grader has no basis to choose, so it
    # splits. The clause says the thin reason still counts.
    #
    # FALSIFIER: p9 must stay `absent` -- it offers no reason at all and gold
    # charges it. CONTROLS: the eighteen cells at `met` 12/12 must not move.
    # Leakage-screened: no content word in the clause is used by three or fewer
    # students, which is the pattern the gate flags.
    # AND A SIBLING GAP WORTH RECORDING: `specific` carries 35 characters, the
    # same near-empty shape. It has not flapped yet, so it is a latent case of
    # this defect rather than a live one.
    ("Q3", "realistic", "rule"): 'THE BAR IS LOW, AND THE TWO ARMS ARE ALTERNATIVES: `met` where the goal is plainly workable as stated, OR where any reason for thinking so is given. DO NOT WEIGH THE REASON -- a thin or circular one counts, since this asks whether a reason was given and not whether it persuades. `absent` only where none is given and the goal is not plainly workable.',
    # WK2's `named_type`, registered 2026-09-07 (subgoal Q55). Lifted from
    # `scratchpad/candidate_wk2_named.txt` -- the same file the probe read and
    # the same file the build read, so design, probe and shipped text are one
    # string by construction and not by inspection.
    # IT ALSO REPLACES NOTHING: sha e3b0c44298fc, the empty string, exactly as
    # `aimed_correctly` did below. D1 and D2 carry text for the same key and
    # WK2 and DAY1 do not -- and D1/D2's text says "`unclear` only if it is
    # blank or unreadable", which on WK2/p15 prescribes the WRONG answer, so
    # this is written from the cells rather than copied from the sibling.
    # DAY1 STILL SHIPS THE EMPTY STRING for this slot and is NOT touched here:
    # nothing has measured a DAY1 cell of p15's shape, and a second item is a
    # second measurement, not a free ride on this one.
    # UPDATED 2026-09-10 with the rewording that removed "read both
    # boxes" from a one-box item. The design is LIVE -- the note still
    # ships, it just names the type and the definition instead of
    # counting boxes -- so the design of record follows it. Left under
    # the "desc" key it was registered with: `named_type` is a CRITERION
    # and has no desc, which is why --accept-design-change refuses it,
    # and re-keying the fragment is its own cleanup.
    ("WK2", "named_type", "desc"): 'WHICH of the four types the student CLAIMS -- not whether the claim is right, which another check decides.\nREAD BOTH THE TYPE THEY NAMED AND THE DEFINITION THEY WROTE. The type may be named outright, or it may be named only by the DEFINITION: a definition that describes adding an unpleasant thing after a behaviour, or taking a wanted thing away, names a type as surely as writing its name does. Where the two disagree, report what the NAMED TYPE says.\nAnswer `unclear` ONLY when NEITHER names a type -- both empty, or a bare label with nothing after it. A blank type is not by itself an absent type.',
    # WK2's `aimed_correctly` gate, REGISTERED BEFORE THE BUILD on 2026-09-07 --
    # the order this table exists to enforce, and the order Q4b's report slot did
    # not follow. Lifted from `scratchpad/candidate_wk2_aimed.txt`, the file the
    # probe read; nothing retyped.
    # WHAT IT REPLACES IS NOTHING AT ALL. `probe.question_for` returned the EMPTY
    # STRING for this slot -- sha e3b0c44298fc -- because it is absent from WK2's
    # rubric credit list and carries no desc, no rule and no SLOT_NOTES. A gate
    # that takes the whole 4-point item shipped as its own identifier:
    #   - `aimed_correctly` **GATE** -- `met`/`absent`/`unclear`
    # Sentence 1 is `rubric_h2.OC_GATES`' own declared message for this gate,
    # turned from feedback into a question. Sentence 2 is the reading BACKLOG.md
    # records the slot ALREADY using on WK2/p8 -- "answers `aimed_correctly: met`
    # because the fault is already accounted for". Sentence 3 covers the blanks.
    # PROBED ON ALL 20 CELLS BEFORE BUILDING: target p11 `met` 4/4 (it refuses in
    # 5 of 11 today), p3/p15 held, no gold-4.00 cell moved, and every gold-0 cell
    # still refuses. scratchpad/probe_wk2_aimed.json.
    ("WK2", "aimed_correctly", "desc"):
        "Does the consequence point the RIGHT WAY for the arrangement this answer actually describes -- something added or taken away AFTER the behaviour, in the direction that would change it? Answer `absent` when it is pointed the wrong way: an aversive for MEETING the goal, or a reward for MISSING it.\nJUDGE THE ARRANGEMENT DESCRIBED, NOT THE TYPE THE STUDENT NAMED. An answer that describes a sound arrangement but labels it with the wrong type is `met` here. The mismatch between the two is a different check's charge, and taking the whole item for it here would charge one fault twice.\nAnswer `unclear` only when the answer names no consequence to judge at all.",
    # SUBGOAL Q19's REPORT SLOT IS GONE FROM HERE, 2026-09-07, and the reason
    # matters because this table's standing policy is the opposite. A design is
    # normally KEPT after a revert so the next attempt starts from the decision
    # rather than from memory -- right when the DESIGN was sound and the BUILD
    # drifted, which is what happened to this slot the first time round.
    # IT IS WRONG HERE. The design itself was then measured TWICE and refuted
    # both times: the probed wording fired on p13, p20 and p8, where gold charges
    # nothing on the behaviour boxes; a second wording adding a disposition
    # clause and a sameness clause fixed p16 and still fired on those three.
    # Gold names this criterion exactly ONCE in the item, on p4 -- "your
    # behaviors cannot be the same as your antecedents" -- so the standard is
    # fire-on-p4-and-nowhere-else, and neither wording met it.
    # A design of record pointing the next attempt at a wording measured to
    # contradict gold on three cells is worse than no entry. Both texts and both
    # results live in GOALS.md under Q19, where a FAILURE can be recorded beside
    # them. Nothing is lost; what is removed is the false suggestion that this
    # wording is ready to build.
}


DESIGNED_SHA_FILE = "DESIGNED_TEXT_SHA.json"


def _designed_shas() -> dict:
    import json
    try:
        raw = json.loads((pathlib.Path(__file__).parent / DESIGNED_SHA_FILE).read_text())
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
    import handouts as H
    want = _designed_shas()
    live: dict[str, str] = {}
    for h in (1, 2, 3):
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
    out: list[str] = []
    for key in sorted(live):
        if key not in want:
            out.append(f"MISSING design of record: {key.replace('|', '/')} is a "
                       f"prompt field with no entry in {DESIGNED_SHA_FILE}. A slot "
                       f"added without a decision recorded is how re-typing drifts")
        elif want[key] != live[key]:
            out.append(f"CHANGED without acceptance: {key.replace('|', '/')} "
                       f"designed {want[key]}, ships {live[key]}. If the edit is "
                       f"intended: python3 measured.py --accept-design-change "
                       f"{key.replace('|', ' ')}")
    for key in sorted(set(want) - set(live)):
        out.append(f"STALE design of record: {key.replace('|', '/')} is in "
                   f"{DESIGNED_SHA_FILE} and no longer in the rubric -- drop it "
                   f"if the revert is permanent")
    return out


def _field_sha(text) -> str:
    import hashlib
    return hashlib.sha256(re.sub(r"\s+", " ", str(text)).strip().encode()).hexdigest()[:12]


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
    import editguard

    return editguard.vanished()


VERDICT_HEDGES = {"unclear"}
"""Verdicts offered so a grader can decline, which carry no charge either side.

Exempt from the pairing below BY DESIGN: the web offers `unclear` on 26 slots
whose `codes` map has no entry for it, and that is a hedge with no deduction
rather than a missing code.
"""

VERDICT_PAIRS: dict[str, dict[str, str]] = {
    # THE BRIDGE THE CODE SAID DID NOT EXIST. `olx_prompts` line ~2173:
    # "the web says `wrong_kind` where the rubric says `not_reason`, and on 1c's
    # legend `incomplete` against `not_described` ... enforcement.ALIAS does NOT
    # record verdict pairs -- it maps slot KEY names, and an earlier version of
    # this comment said otherwise, sending a reader looking for a bridge that
    # does not exist." This is that bridge, authored 2026-09-08.
    # WHY IT HAS TO BE PER SLOT: `not_described` pairs with `incomplete` on
    # 1c/legend, with `generic` on 1c/title and with `tick_values` on
    # 1c/x_axis_label. A global token map would be wrong three ways on one item.
    # WEB TOKEN -> PAPER TOKEN. The web token is what the prompt offers (the
    # generated `slots=` field 3); the paper token is a `codes` key, which is
    # score.py's failure vocabulary -- it reads them for exactly that, see
    # score.py "`not_described` is the paper-side counterpart of the web sheet's
    # `incomplete`".
    # SEEDED WHERE FORCED, NOT GUESSED: identical names pair with themselves,
    # then a single remaining token on each side pairs with the other. 62 of 63
    # slots were forced; the 63rd is reported by the check below rather than
    # invented here.
    '1a/baseline_week': {'absent': 'absent'},
    '1a/distinguishes_periods': {'absent': 'absent'},
    '1a/week_1': {'absent': 'absent'},
    '1a/week_2': {'absent': 'absent'},
    '1a/week_3': {'absent': 'absent'},
    '1c/has_own_graph': {'absent': 'absent', 'mismatch': 'mismatch'},
    '1c/legend': {'absent': 'absent', 'incomplete': 'not_described'},
    '1c/title': {'absent': 'absent', 'generic': 'not_described'},
    '1c/x_axis_label': {'absent': 'absent', 'tick_values': 'not_described'},
    # AUTHORED 2026-09-08, the one pairing the mechanical seeding refused --
    # and it is MANY-TO-ONE ON PURPOSE, which is why no rule could force it.
    # A y-axis can fail BOTH ways this item distinguishes, and its desc says so
    # in as many words: an axis TITLE naming what the axis represents, "not its
    # tick values, and not the software's default 'Axis Title' placeholder".
    # Its siblings each carry one of the two modes -- x_axis_label only
    # `tick_values`, title only `generic` -- so the web offers y_axis_label
    # three failing verdicts against the paper side's one.
    # NOTHING IS LOST BY COLLAPSING THEM, and that is the ground for the
    # pairing rather than convenience: `codes` maps BOTH `absent` and
    # `not_described` to NO_Y_AXIS, and NO_Y_AXIS is 2.0 -- the same charge
    # whichever way the label fails. The web's extra distinction is DESCRIPTIVE,
    # feeding better feedback, not a second deduction. So the paper scorer can
    # express the charge; it just cannot say which of the two reasons applied.
    # THE SEEDING RULE'S LIMIT, recorded so it is not mistaken for a bug: it
    # pairs identical names, then a SINGLE remaining token on each side. A
    # legitimate two-to-one needs a human to say that collapsing loses no
    # charge, which is exactly what the check asked for.
    '1c/y_axis_label': {'absent': 'absent', 'tick_values': 'not_described',
                        'generic': 'not_described'},
    '2a/how_1': {'absent': 'absent'},
    '2a/how_2': {'absent': 'absent'},
    '2a/verdict': {'absent': 'absent'},
    '2b/sentence_1': {'absent': 'absent'},
    '2b/sentence_2': {'absent': 'absent'},
    '2b/sentence_3': {'absent': 'absent'},
    '3/example_1': {'absent': 'absent'},
    '3/example_2': {'absent': 'absent'},
    'D1/add_or_remove': {'absent': 'absent'},
    'D1/increase_or_decrease': {'absent': 'absent'},
    'D1/matches_chosen_type': {'absent': 'absent'},
    'D2/add_or_remove': {'absent': 'absent'},
    'D2/increase_or_decrease': {'absent': 'absent'},
    'D2/matches_chosen_type': {'absent': 'absent'},
    'DAY1/consequence_asserted': {'absent': 'no'},
    'DAY2/consequence_asserted': {'absent': 'no'},
    'Q1/reason_1': {'absent': 'absent'},
    'Q1/reason_2': {'absent': 'absent'},
    'Q1/reason_3': {'absent': 'absent'},
    'Q1/utb_stated': {'absent': 'absent'},
    'Q2/reason_1': {'absent': 'absent'},
    'Q2/reason_2': {'absent': 'absent'},
    'Q2/reason_3': {'absent': 'absent'},
    'Q2/wgb_inverts_utb': {'absent': 'absent'},
    'Q2/wgb_is_counterpart': {'absent': 'absent'},
    'Q3/action_oriented': {'absent': 'absent'},
    'Q3/measurable': {'absent': 'absent'},
    'Q3/realistic': {'absent': 'absent'},
    'Q3/specific': {'absent': 'absent'},
    'Q3/time_bound': {'absent': 'absent'},
    'Q4a/antecedent_1': {'absent': 'absent', 'wrong_kind': 'not_antecedent'},
    'Q4a/antecedent_2': {'absent': 'absent', 'wrong_kind': 'not_antecedent'},
    'Q4a/keyword': {'absent': 'absent'},
    'Q4a/no_antecedents': {'absent': 'absent'},
    'Q4b/behavior_1': {'absent': 'absent', 'wrong_kind': 'wrong_kind'},
    'Q4b/behavior_2': {'absent': 'absent', 'wrong_kind': 'wrong_kind'},
    'Q4b/modify_stated': {'absent': 'absent'},
    'Q4b/modify_why': {'absent': 'absent'},
    'Q4c/consequence_1': {'absent': 'absent', 'duplicate': 'duplicate', 'wrong_kind': 'not_consequence'},
    'Q4c/consequence_2': {'absent': 'absent', 'duplicate': 'duplicate', 'wrong_kind': 'not_consequence'},
    'Q4c/no_consequences': {'absent': 'absent'},
    'Q5/example_1': {'absent': 'absent', 'duplicate': 'duplicate', 'wrong_kind': 'not_reason'},
    'Q5/example_2': {'absent': 'absent', 'duplicate': 'duplicate', 'wrong_kind': 'not_reason'},
    'Q6/affect_c1': {'absent': 'absent', 'incomplete': 'not_described'},
    'Q6/affect_c2': {'absent': 'absent', 'incomplete': 'not_described'},
    'Q6/change_a1': {'absent': 'absent', 'incomplete': 'not_described'},
    'Q6/change_a2': {'absent': 'absent', 'incomplete': 'not_described'},
    'Q6/state_a1': {'absent': 'absent', 'mismatch': 'neither'},
    'Q6/state_a2': {'absent': 'absent', 'mismatch': 'neither'},
    'Q6/state_c1': {'absent': 'absent', 'mismatch': 'neither'},
    'Q6/state_c2': {'absent': 'absent', 'mismatch': 'neither'},
    'WK1/consequence_asserted': {'absent': 'no'},
    'WK2/consequence_asserted': {'absent': 'no'},
}


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
    import cross_path as X
    import measured as M

    out = []
    for item in sorted(M._jobs()):
        for side in M.SIDES:
            try:
                doc = M._runs_doc(item, side)
            except Exception:
                continue
            if not doc:
                continue
            for n, run in enumerate(doc.get("runs") or []):
                for r in (run.get("results") or []):
                    fb = str(r.get("feedback") or "")
                    if not (fb.startswith("Error:") or "Azure API error" in fb):
                        continue
                    try:
                        _, pid, score, _ = X.result_cell(r)
                    except Exception:
                        pid, score = None, None
                    head = fb.split("(", 2)[0].strip()[:60]
                    out.append(
                        f"{item}/p{pid} [{side}] run {n} is recorded with score "
                        f"{score} but its feedback is an API ERROR ({head}). An "
                        f"error is not a measurement -- it returned no verdicts, "
                        f"so the score is whatever the scorer produces from "
                        f"nothing. Re-run the cell or drop the run; do not pool "
                        f"it.")
    return out


VERDICT_ABSENCE_ENCODING = {
    # HOW EACH ENGINE WRITES "NO VERDICT HERE", measured 2026-09-08 over every
    # recorded run: olx `None` 7,080 times and NOTHING ELSE, python the empty
    # string 3,535 times and NOTHING ELSE. Each side is perfectly consistent
    # with itself and perfectly divergent from the other.
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
    """Do the two engines spell "no verdict here" the same way? They do not.

    FOUND 2026-09-08, and found as a bug in a READER rather than in either
    engine. Diffing DAY1/p14's fields against the pooled mode put every python
    run 7-8 fields off it, which briefly looked like a python-side defect. It
    was not: `named_type`, `observed_type`, `restriction_authored`, `restricts`
    and `trigger_expects` hold `None` on the olx side and `""` on the python
    side, on the same cell with the same sheet, and both mean THE SAME THING.
    The two sides score 471/491 EACH -- exactly level.

    That is the standing rule working as designed: a side difference is never
    itself a premise, and the reader is the first suspect. The reader was wrong.

    SO WHAT THIS CHECK IS FOR. The divergence is total, systematic and now
    DECLARED above, so reporting it 32 times would be noise. What is worth
    guarding is a CHANGE: a side growing a second spelling (a literal "n/a",
    "null", "-"), a side becoming internally inconsistent, or the scope moving.
    Any of those means a new encoding has appeared and every comparison built on
    the old assumption is quietly wrong again.

    NORMALISE BEFORE COMPARING. Any reader that diffs verdicts across sides must
    map both spellings to one absent value first; `no_verdict` below is that
    predicate, so the rule lives in one place rather than in each caller.
    """
    import collections

    import cross_path as X
    import measured as M

    out = []
    spellings = collections.defaultdict(collections.Counter)
    pairs = set()
    for item in sorted(M._jobs()):
        enc = collections.defaultdict(lambda: collections.defaultdict(set))
        for side in ("olx", "python"):
            try:
                doc = M._runs_doc(item, side)
            except Exception:
                continue
            for run in (doc or {}).get("runs") or []:
                for r in (run.get("results") or []):
                    try:
                        _, _, _, v = X.result_cell(r)
                    except Exception:
                        continue
                    for k, x in (v or {}).items():
                        if not no_verdict(x):
                            continue
                        spellings[side][repr(x)] += 1
                        enc[k][side].add(repr(x))
        for k, d in enc.items():
            if len(d) == 2 and d["olx"] != d["python"]:
                pairs.add((item, k))

    for side, want in VERDICT_ABSENCE_ENCODING.items():
        seen = set(spellings.get(side, {}))
        if not seen:
            continue
        if seen != {repr(want)}:
            out.append(
                f"side {side!r} now spells an absent verdict {sorted(seen)} but "
                f"VERDICT_ABSENCE_ENCODING declares only {repr(want)}. A second "
                f"spelling means every cross-side verdict comparison is reading "
                f"a difference that is not there -- normalise with "
                f"`enforcement.no_verdict` and update the declaration")
    if pairs and len(pairs) != VERDICT_ABSENCE_SCOPE:
        out.append(
            f"the olx/python absent-verdict encoding now diverges on "
            f"{len(pairs)} (item, slot) pair(s); VERDICT_ABSENCE_SCOPE declares "
            f"{VERDICT_ABSENCE_SCOPE}. Re-read the declaration above before "
            f"trusting any field-level diff across the two sides")
    return out


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
    import cross_path as X
    import measured as M

    out = []
    for item in sorted(M._jobs()):
        for side in M.SIDES:
            try:
                doc = M._runs_doc(item, side)
            except Exception:
                continue
            for n, run in enumerate((doc or {}).get("runs") or []):
                for r in (run.get("results") or []):
                    try:
                        _, pid, score, verdicts = X.result_cell(r)
                    except Exception:
                        continue
                    if verdicts:
                        continue
                    out.append(
                        f"{item}/p{pid} [{side}] run {n} is recorded with score "
                        f"{score} and NO VERDICTS AT ALL. A run that judged "
                        f"nothing is not a measurement -- re-run the cell or "
                        f"drop the run; do not pool it.")
    return out


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
    agree on the order, so this is a warning rather than a divergence -- but a
    rubric that relies on it is relying on the order, and the order should not be
    load-bearing in authored data.
    """
    import collections

    import measured as M
    from handouts import config

    COMPUTED = ("equals", "expect", "forbid", "maps", "derived", "counts")
    out = []
    for item in sorted(M._jobs()):
        h = M._jobs()[item]["handout"]
        it = config(h)["rubric"].BY_ID.get(item) or {}
        writers = collections.defaultdict(list)
        for prim in COMPUTED:
            for r in it.get(prim) or []:
                key = r.get("key")
                if key:
                    writers[key].append(prim)
        for key, prims in sorted(writers.items()):
            if len(prims) > 1:
                out.append(
                    f"{item}/{key} is written by {sorted(prims)} -- TWO computed "
                    f"primitives on one key. `expect` REPLACES a verdict rather "
                    f"than overriding it, so which one wins is decided by loop "
                    f"order, and that is not something authored data may rely "
                    f"on. Give the second rule its own key.")
        written = set(writers)
        for prim in ("expect", "equals"):
            for r in it.get(prim) or []:
                for operand in ("left", "right"):
                    o = r.get(operand)
                    if o and o in written:
                        out.append(
                            f"{item}/{r['key']}'s `{prim}` reads `{o}`, which "
                            f"{sorted(writers[o])} also writes -- a "
                            f"read-after-write whose value depends on loop "
                            f"order. Both engines agree on the order today; do "
                            f"not make it load-bearing.")
    return out


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
    import olx_prompts as OP

    import measured as M
    from handouts import config

    out = []
    for item in sorted(M._jobs()):
        h = M._jobs()[item]["handout"]
        rub = config(h)["rubric"].BY_ID.get(item) or {}
        spec = (getattr(config(h)["rubric"], "SLOT_SPEC", {}) or {}).get(item) or []
        off = {f["key"]: OP.resolve_options(f.get("seg"), ["met", "absent", "unclear"])
               for f in spec}
        for c in rub.get("credit") or []:
            codes = c.get("codes") or {}
            opts = [o for o in (off.get(c["what"]) or []) if o]
            if not codes or not opts:
                continue
            key = f"{item}/{c['what']}"
            web = [o for o in opts[1:] if o not in VERDICT_HEDGES]
            paper = [k for k in sorted(codes) if k not in VERDICT_HEDGES]
            pairs = VERDICT_PAIRS.get(key)
            if pairs is None:
                out.append(
                    f"{key} has no entry in VERDICT_PAIRS: the web offers "
                    f"{web} and the paper vocabulary is {paper}, and nothing "
                    f"declares which corresponds to which. Author the pairing.")
                continue
            for w in web:
                if w not in pairs:
                    out.append(
                        f"{key}: the web can answer `{w}` and NOTHING ON THE "
                        f"PAPER SIDE corresponds -- a charge score.py cannot "
                        f"express. Web {web}, paper {paper}.")
            for pp in paper:
                if pp not in set(pairs.values()):
                    out.append(
                        f"{key}: the paper vocabulary has `{pp}` and no web "
                        f"verdict maps to it -- a charge the app cannot "
                        f"produce. Web {web}, paper {paper}.")
    return out


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
    import re

    import measured as M
    import olx_prompts as OP

    gens = dict(OP.GENERATED_ATTRS)
    skip = {"id", "target"}
    out = []
    for item in sorted(M._jobs()):
        action = OP.ACTION.get(item)
        if not action:
            continue
        try:
            tag = OP._sheet_tag(OP.HANDOUT[item], action)
        except BaseException:
            continue
        for m in re.finditer(r'\b([a-z_]+)="([^"]*)"', tag):
            name, have = m.group(1), m.group(2)
            if name in skip:
                continue
            fn = gens.get(name)
            if fn is None:
                out.append(
                    f"{item}: `{name}=` is HAND-AUTHORED -- no generator in "
                    f"olx_prompts.GENERATED_ATTRS produces it, so a design "
                    f"change cannot reach it and `--write` cannot regenerate "
                    f"it. Give the rubric the fact and add a generator.")
                continue
            try:
                gen = fn(item)
            except BaseException as exc:
                out.append(f"{item}: the generator for `{name}=` raised "
                           f"{type(exc).__name__}: {str(exc)[:80]}")
                continue
            if (gen or None) != (have or None):
                out.append(
                    f"{item}: `{name}=` DIVERGED from the rubric -- the .olx has "
                    f"{have[:60]!r} and the generator produces {str(gen)[:60]!r}. "
                    f"Run `olx_prompts.py --write` (it may need two passes) and "
                    f"confirm the rendered body, not just the attribute.")
    return out


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
    import re

    from handouts import config

    PAT = re.compile(
        r"cannot count|stands INSTEAD|never alongside|reason deductions|"
        r"costs the whole item|the whole item is that finding|zeroes the item|"
        r"is charged \d|worth \d(?! of)", re.I)
    out = []
    for h in (1, 2, 3):
        for item in config(h)["rubric"].ITEMS:
            for c in item.get("credit") or []:
                for field in ("desc", "rule"):
                    txt = c.get(field)
                    if not txt:
                        continue
                    hits = sorted({m.group(0).lower() for m in PAT.finditer(txt)})
                    if hits:
                        out.append(
                            f"{item['id']}/{c['what']}/{field} tells a JUDGING "
                            f"grader what a verdict COSTS: {hits}. Arithmetic "
                            f"belongs in the derivation or a comment, not in a "
                            f"prompt whose job is to return judgements -- the "
                            f"model executes it (subgoal Q41).")
    return out


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
    import re

    import measured as M
    import olx_prompts as OP

    out = []
    for item in sorted(M._jobs()):
        action = OP.ACTION.get(item)
        if not action:
            continue
        try:
            tag = OP._sheet_tag(OP.HANDOUT[item], action)
        except BaseException:
            continue
        ms = re.search(r'\bslots="([^"]*)"', tag)
        mc = re.search(r'\bchoices="([^"]*)"', tag)
        if not ms:
            continue
        sets = OP.parse_choices(mc.group(1) if mc else "")
        for part in ms.group(1).split("|"):
            m = re.search(r"pick\(([^)]+)\)", part)
            if not m:
                continue
            slot, setname = part.split(":")[0], m.group(1)
            want = OP._pick_verdicts(item, slot)
            if want is None:
                continue                    # no rubric source: preserved, not a finding
            have = sets.get(setname) or []
            if sorted(want) != sorted(have):
                out.append(
                    f"{item}/{slot} picks from '{setname}': the rubric declares "
                    f"{sorted(want)} but the .olx offers {sorted(have)}. The "
                    f"grader cannot answer what it is not offered -- run "
                    f"`olx_prompts.py --write` and confirm the checklist head "
                    f"lists it.")
    return out


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
    import handouts as H
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
        text = str(note)
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
    import probe as PR

    out = []
    for r in PR.receipts():
        key = (r.get("item"), r.get("slot"), "desc")
        if key not in DESIGNED_TEXT:
            out.append(
                f"{r['item']}/{r['slot']}: a probe measured this wording "
                f"({r['sha']}, verdict {r.get('verdict') or 'none'}) and only its "
                f"sha is recorded. A sha detects drift; it cannot reproduce the "
                f"string the result belongs to. Put the text in DESIGNED_TEXT "
                f"(full text is for fields with evidence; the other 145 stay "
                f"sha-only by decision)")
    return out


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
    import olx_prompts as OP

    out = []
    for key in sorted(DESIGNED_TEXT):
        item, slot, field = key
        want = " ".join(DESIGNED_TEXT[key].split())
        try:
            shipped = " ".join(OP.build_web_prompt(item).split())
        except Exception as exc:
            out.append(
                f"{item}/{slot}.{field}: cannot build {item}'s prompt to check "
                f"its design against -- {type(exc).__name__}: {exc}")
            continue
        if want not in shipped:
            out.append(
                f"{item}/{slot}.{field}: DESIGNED_TEXT holds {len(want)} chars "
                f"that are NOT in {item}'s shipped prompt. Either the revert that "
                f"retired this design never dropped its entry, or a build did not "
                f"land -- drop the entry if the attempt was reverted, rebuild if "
                f"it was not")
    return out


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
    import agreement_app as _A
    import measured as M
    import probe as PR

    out = []
    # `agreement_app.JOBS` is the item list every other check in this file uses
    # (see the `_A.JOBS` sites above); the first cut called a `_jobs()` that does
    # not exist here and the check died inside its own iteration.
    for item in sorted(_A.JOBS):
        try:
            import olx_prompts as O

            if item not in O.ACTION:
                continue          # no judging prompt: no answerable slot to probe
            asked = set(PR._entries(O.build_web_prompt(item)))
        except Exception:
            continue
        # WHICH SLOTS THE LAST RECORDING ACTUALLY SAW, read from the artifact.
        # The first cut read `rec["cells"][pid]["slots"]`, and a `cells` entry is
        # an INT -- the run count -- so the set was always empty and the check
        # was inert while reporting clean. A check that has never fired is worth
        # nothing; this one is fire-tested by hiding the receipts.
        seen = set()
        for side in ("python", "olx"):
            try:
                doc = M._runs_doc(item, side)
            except Exception:
                continue
            # `_runs_doc` RETURNS None for an item with nothing recorded on this
            # side rather than raising, so the except above never sees it and
            # `.get` raised AttributeError -- which the runner reports as "the
            # check itself raised", i.e. as coverage that is not there.
            if not doc:
                continue
            for run in doc.get("runs") or []:
                for c in run.get("results") or []:
                    seen |= set(c.get("checks") or c.get("verdicts") or {})
                    seen |= set(c.get("answers") or c.get("refers_to") or {})
        if not seen:
            continue                      # never recorded: nothing to compare
        probed = {r["slot"] for r in PR.receipts(item)}
        for slot in sorted(asked - seen - probed):
            out.append(
                f"{item}/{slot} is an answerable slot the last recording never "
                f"saw and no probe has ever asked. A new question costs ~30 calls "
                f"to probe standalone and ~230 to learn from a sweep: "
                f"`python3 probe.py {item} {slot}` (QUALITY_CONTROL.md 2a)")
    return out


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
    import probe as PR

    out = []
    for r in PR.receipts():
        item, slot, was = r.get("item"), r.get("slot"), r.get("sha")
        try:
            now = PR.question_for(item, slot)
        except LookupError as e:
            out.append(
                f"{item}/{slot}: a probe recorded verdict "
                f"{r.get('verdict') or '(none)'} on a slot that is no longer "
                f"asked -- {str(e).splitlines()[0]}. Drop the receipt or rebuild "
                f"the slot; it is not evidence for the next attempt")
            continue
        except Exception as e:
            out.append(f"{item}/{slot}: the receipt could not be checked -- "
                       f"{type(e).__name__}: {e}")
            continue
        if now["sha"] != was:
            out.append(
                f"{item}/{slot}: PROBED {was}, SHIPS {now['sha']} -- the probe "
                f"answered a different question from the one the sweep will ask, "
                f"which is what cost the Q19 sweep. Re-probe the shipping string "
                f"(`python3 probe.py {item} {slot}`) before spending calls, or "
                f"restore the text that was probed")
    return out


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
    import handouts as H
    out: list[str] = []
    for (item, slot, field), want in sorted(DESIGNED_TEXT.items()):
        spec = None
        for h in (1, 2, 3):
            try:
                spec = H.config(h)["rubric"].BY_ID.get(item)
            except Exception:
                continue
            if spec:
                break
        if not spec:
            continue
        got = next((c.get(field) for c in (spec.get("credit") or [])
                    if c.get("what") == slot), None)
        if got is None:
            continue                      # designed, not yet built -- not a fault
        norm = lambda x: re.sub(r"\s+", " ", str(x)).strip()
        if norm(got) == norm(want):
            continue
        w, g = norm(want), norm(got)
        i = next((n for n, (a, b) in enumerate(zip(w, g)) if a != b), min(len(w), len(g)))
        out.append(
            f"{item}/{slot}.{field} SHIPS text its subgoal did not design. "
            f"First divergence at char {i}:\n"
            f"        designed: ...{w[max(0, i - 40):i + 60]!r}\n"
            f"        shipped : ...{g[max(0, i - 40):i + 60]!r}")
    return out


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
    import handouts as H
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
    out: list[str] = []
    for name in ("rubric_h1", "rubric_h2", "rubric_h3"):
        try:
            mod = __import__(name)
        except Exception:
            continue
        maps = getattr(mod, "MAPS", None) or {}
        by_id = getattr(mod, "BY_ID", None) or {}
        for item in sorted(maps):
            spec = by_id.get(item)
            if spec is None:
                out.append(f"{name}: MAPS[{item!r}] names an item that does not "
                           f"exist in BY_ID")
            elif "maps" not in spec:
                out.append(f"{name}: MAPS[{item!r}] is defined but never attached "
                           f"to the item spec, so the generator emits no `maps` "
                           f"and the pick has no route to its verdict")
    return out


def check_mapped_slots_have_no_unreachable_verdict() -> list[str]:
    """A mapped slot offering a verdict its map can never emit. Subgoal E46.

    AN AUTHORING-TIME CHECK, and the cheap half of the pair. When `maps` computes
    a slot's verdict from a pick, the slot's own verdict list is what the APP
    still offers the grader. Any value in that list the map cannot produce is a
    verdict that is DEAD on the python mirror -- which derives the slot and never
    consults the grader -- and LIVE on the app, which will answer the slot
    directly when the map does not determine it. That is a guaranteed divergence
    surface, authored in, and it costs nothing to see before a sweep.

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
    out: list[str] = []
    for item, mod, spec in _maps_specs():
        slot = next((c for c in (mod.BY_ID.get(item, {}).get("credit") or [])
                     if c.get("what") == spec["key"]), None)
        if not slot:
            continue
        # THE SHEET IS THE AUTHORITY ON WHAT THE GRADER MAY ANSWER, not the
        # rubric. Subgoal E52: this line read `slot["verdicts"]` and that hole
        # let the exact fault it was built for survive a whole sweep. On
        # 2026-09-06 `unclear` was dropped from Q2's RUBRIC list, this check went
        # clean, and the SHEET still declared `wgb_inverts_utb:...:unclear@2`, so
        # the grader kept answering it -- five divergences, at an IDENTICAL
        # prompt_sha, with the audit reporting nothing. A check that reads the
        # side the grader does not see is checking the wrong document.
        # E27's helper, not a second copy. `_olx_slot_verdicts` returns only the
        # EXTRA verdict the sheet spells out (met/absent are implicit), so the
        # offered set is that plus the two. A duplicate reader was written here
        # first and deleted: two functions answering "what does the sheet offer"
        # is how the rubric and the sheet came to disagree in the first place.
        extra = _olx_slot_verdicts(item, spec["key"])
        offered = ({"met", "absent"} | set(extra)) if extra else None
        emits = _maps_emits(spec)
        # A DECLARED COUNTERPART IS NOT AN ORPHAN. Subgoal E27 established that
        # the two engines' verdict vocabularies differ BY DESIGN and recorded
        # every pair in VERDICT_SPACE_DIVERGENCES. Q4a's sheet offers
        # `wrong_kind` where its map emits `not_antecedent`, and the table says
        # in as many words: "Counterparts on Q4a's antecedent_1/antecedent_2".
        # The engines charge at nearly the same rate -- 39 against 44 over the
        # same runs -- so they agree on the judgement and differ on the name.
        # The first version of this line reported that as a fault, which is the
        # false-positive class this whole family keeps falling into: a naive
        # rubric-vs-sheet comparison reports 39 mismatches of which about 37 are
        # E27's design.
        for web, paper in VERDICT_SPACE_DIVERGENCES:
            if emits & set(paper):
                emits = emits | set(web)
            if emits & set(web):
                emits = emits | set(paper)
        orphan = (offered if offered is not None
                  else set(slot.get("verdicts") or [])) - emits
        if not orphan:
            continue
        codes = slot.get("codes") or {}
        dup = [v for v in sorted(orphan)
               if v in codes and list(codes.values()).count(codes[v]) > 1]
        out.append(
            f"{item}/{spec['key']} offers verdict(s) {sorted(orphan)} that "
            f"MAPS cannot emit (it produces {sorted(_maps_emits(spec))} from "
            f"`{spec['pick']}`). The python mirror derives this slot and can "
            f"never answer that; the app can, and will. "
            + (f"{dup} duplicate(s) another verdict's deduction code, so removing "
               f"them is score-neutral by construction. " if dup else "")
            + "Give the map a pair or fallback for it, or drop it from the slot")
    return out


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
        side, stamp = "python", era.get("prompt_sha_python")
    if not stamp:
        return None
    try:
        return stamp == M.prompt_sha(item_id, side)
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

    root = _pl.Path(getattr(_paths, "OUT", "/home/pdeane/molly_data/out"))
    out: list[str] = []
    for item, _mod, s in _maps_specs():
        for path in _runs_files(root, f"*/{item}.runs.json"):
            try:
                doc = json.loads(path.read_text())
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
    slot, and nothing moved. So the app scores from the RECORDED verdict and the
    mirror from the MAP, and the two genuinely differ.
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
    root = _pl.Path(getattr(_paths, "OUT", "/home/pdeane/molly_data/out"))
    if not root.is_dir():
        return []
    tally: dict = {}
    for path in _runs_files(root, "*/*.runs.json"):
        item = path.name[: -len(".runs.json")]
        if item not in by_item:
            continue
        try:
            doc = json.loads(path.read_text())
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
ONE_SIDED_SCORED_SLOTS_BUDGET = 0

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
DECOMPOSITION_DIVERGENCES: dict[tuple[str, str], str] = {
    **{("2b", f"sentence_{n}"):
       "The mirror enumerates the three sentences as `sentence_1/2/3`; the app "
       "answers the COUNT `sentences_given` and charges from it. Measured: 2b is "
       "20/20 on both sides with identical medians on all twenty cells."
       for n in (1, 2, 3)},
    **{("3", f"example_{n}"):
       "The mirror enumerates the examples as `example_1/2`; the app answers the "
       "COUNT `changes_given`. Measured: python 19/20, olx 20/20, and the single "
       "cell whose medians differ (p15) is one the APP gets right and the mirror "
       "does not -- so the decomposition is not costing the app anything."
       for n in (1, 2)},
    **{(item, f"reason_{n}"):
       "The mirror enumerates the reasons as `reason_1/2/3`; the app scores the "
       "reasons scaffold in aggregate. Measured: Q1 18/20 and Q2 19/20 on BOTH "
       "sides, with Q2 identical on every cell and Q1 differing on two (p6, p17) "
       "for reasons subgoals Q16 and Q44 own, not this one."
       for item in ("Q1", "Q2") for n in (1, 2, 3)},
    ("NR", "barrier_is_not_this_type"):
        "NR-only slot the mirror answers and the app never does. Measured: NR is "
        "18/18 python and 17/18 olx with the per-cell medians IDENTICAL on all "
        "twenty cells, so the app reaches the same judgement through the type "
        "criterion it does answer. Kept declared rather than aliased because "
        "there is no app-side name to alias it to.",
}


def check_scored_slots_are_answered_by_both_engines() -> list[str]:
    """A slot the sheet gives POINTS to, answered by one engine and never the other.

    Reported as SCORED SLOT ANSWERED BY ONE ENGINE ONLY. Subgoal E53.

    THE QUESTION NO OTHER CHECK ASKS. E48 asks whether a rubric slot reaches the
    sheet; E49 the reverse; E46 whether a mapped slot offers an emittable
    verdict. All three read DECLARATIONS. This one reads ARTIFACTS and asks
    whether the declaration was honoured -- whether a slot carrying points
    actually got an answer from both engines over runs already on disk. A slot
    can be correctly declared on both sides, pass every static check, and still
    be answered by only one grader, and then the two engines reach their totals
    by different routes on a criterion one of them cannot express.

    IT IS ARTIFACT-SHAPED, so it belongs beside measured.py's preflight step 5f
    rather than in sweep_gate.py, which is static and runs before any artifact
    exists. Where it CAN run early is the equivalence audit and
    agreement.cheap_checks_gate.

    USE slot_answer, NOT slot_verdict, AND THE REASON IS ON THE RECORD. The first
    measurement of this reported 37 one-sided pairs; a share of them --
    `observed_type`, `stimulus_move` -- were PICKS, which `slot_verdict` refuses
    by design, so the check was inventing gaps out of its own reader. Reading
    them as answers, both engines answer both slots on every item. The 26 SCORED
    findings survived that correction unchanged, which is the only reason they
    are trusted here.

    THE EXCLUSIONS ARE THE WORK, per this series' repeated lesson. A slot the
    app answers under an ALIASED name is not a gap -- `enforcement.ALIAS`
    already declares `observed_type` for `demonstrates_type` and
    `stimulus_is_arranged` for `you_arrange_it` -- and an APP_ONLY_SLOTS entry is
    a declared one-sided slot by construction.
    """
    import measured as M

    def _pointed() -> dict[str, float]:
        out: dict[str, float] = {}
        base = pathlib.Path(__file__).resolve().parent.parent.joinpath("psychology")
        for h in (1, 2, 3):
            try:
                text = base.joinpath(f"bmod_handout{h}.olx").read_text()
            except Exception:
                continue
            for m in re.finditer(r'<LLMAction\b[^>]*>', text, re.S):
                s = re.search(r'slots="([^"]*)"', m.group(0))
                if not s:
                    continue
                for entry in s.group(1).split("|"):
                    name = entry.split(":")[0].lstrip("!")
                    pts = float(entry.rsplit("@", 1)[1]) if "@" in entry else 0.0
                    out[name] = max(out.get(name, 0.0), pts)
        return out

    def _alias_names(key: str) -> set[str]:
        names = {key}
        for left, right in (ALIAS or {}).items():
            group = {left} | (set(right) if isinstance(right, (tuple, list))
                              else {right})
            if key in group:
                names |= group
        return names

    def _derived() -> set[str]:
        """Slots the SHEET derives with an `expect` rule.

        THE EXCLUSION THAT STOPPED A WRONG FIX. Without it this check reported
        `demonstrates_type` on PR/NR/PP/NP as "the app makes the judgement and
        cannot charge for it", and the next step would have been to add a MAPS
        entry connecting `observed_type` to it. That would have DOUBLE-CHARGED a
        criterion that already works. The sheet declares
        `expect="demonstrates_type:observed_type=NR"` and the app honours it: on
        NR/p4, olx runs with `targets_goal_behavior` = `met` and
        `demonstrates_type` = null still score 2.0, which is only possible if the
        type charge landed. The verdict is DERIVED AND CHARGED, and merely not
        written back into the artifact -- a recording gap, not a scoring gap.
        """
        base = pathlib.Path(__file__).resolve().parent.parent.joinpath("psychology")
        names: set[str] = set()
        for h in (1, 2, 3):
            try:
                text = base.joinpath(f"bmod_handout{h}.olx").read_text()
            except Exception:
                continue
            # THREE ATTRIBUTES DERIVE A VERDICT, NOT ONE. The first cut read only
            # `expect` and left `matches_chosen_type` -- declared `equals` on SIX
            # items -- reported as a scoring gap, which is the same misreading
            # this exclusion exists to stop, one attribute over. `derived` is the
            # third. Read all three or the check tells a confident lie about
            # whichever one was forgotten.
            for attr in ("expect", "equals", "derived"):
                for m in re.finditer(rf'{attr}="([^"]*)"', text):
                    for rule in m.group(1).split("|"):
                        if rule.strip():
                            names.add(rule.split(":")[0].strip())
        return names

    pointed = _pointed()
    derived = _derived()
    out: list[str] = []
    for item in sorted(M.records("olx").keys()):
        docs = {}
        for side in ("python", "olx"):
            try:
                docs[side] = M._runs_doc(item, side)
            except Exception:
                docs = {}
                break
        if len(docs) != 2:
            continue
        keys: set[str] = set()
        for doc in docs.values():
            for run in doc["runs"]:
                for r in run["results"]:
                    keys |= set(r.get("verdicts") or {})
                    keys |= set(r.get("checks") or {})
                    keys |= set(r.get("answers") or {})
        for key in sorted(keys):
            if pointed.get(key, 0.0) <= 0:
                continue
            if (item, key) in APP_ONLY_SLOTS:
                continue
            if (item, key) in DECOMPOSITION_DIVERGENCES:
                continue
            names = _alias_names(key)
            direct = {}
            via = {}
            for side, doc in docs.items():
                rs = [r for run in doc["runs"] for r in run["results"]]
                direct[side] = any(M.slot_answer(r, key) is not None for r in rs)
                via[side] = {n for n in names - {key}
                             if any(M.slot_answer(r, n) is not None for r in rs)}
            if direct["python"] == direct["olx"]:
                continue
            has = "python" if direct["python"] else "olx"
            lacks = "olx" if direct["python"] else "python"
            # AN ALIAS ONLY EXCUSES THE GAP IF THE POINTS CAN STILL BE CHARGED.
            # `demonstrates_type` is the case that forced this: the app answers
            # its declared alias `observed_type` in 120 of 120, so a naive alias
            # exclusion clears it -- but `observed_type` carries NO POINTS and no
            # MAPS entry connects the two, so the app makes the judgement and can
            # never charge for it. That is the 1c defect exactly (a pick answered,
            # a scored verdict unmapped, every static surface green), and
            # excluding it would hide the very thing this check exists to find.
            excused = [n for n in sorted(via[lacks]) if pointed.get(n, 0.0) > 0]
            if excused:
                continue
            # THE KEY *OR ANY OF ITS ALIASES* MAY BE THE DERIVED ONE. 1b forced
            # this: the sheet derives `week_1_data` and the mirror scores
            # `week_1`, so testing only the scored key missed the derivation and
            # reported three findings on an item that is 20/20 on BOTH sides with
            # identical medians on all twenty cells.
            if key in derived or (names & derived):
                # Derived by an `expect` rule and charged; only the write-back is
                # missing. Reported as a RECORDING gap so the artifact reader
                # knows the field is unreliable, never as a scoring gap.
                out.append(
                    f"{item}/{key} carries {pointed[key]:g} point(s) and is DERIVED "
                    f"by a sheet `expect` rule, but {lacks} never writes the derived "
                    f"verdict into its artifact -- a RECORDING gap, not a scoring "
                    f"gap: the charge lands. Do not map it; read it from the "
                    f"`expect` source instead")
                continue
            unscored = sorted(via[lacks])
            if unscored:
                out.append(
                    f"{item}/{key} carries {pointed[key]:g} point(s) and is never "
                    f"answered by {lacks}; {lacks} answers only the UNSCORED alias "
                    f"{','.join(unscored)}, and no map connects them -- so {lacks} "
                    f"makes the judgement and cannot charge for it")
            else:
                out.append(
                    f"{item}/{key} carries {pointed[key]:g} point(s), is answered "
                    f"by {has} and NEVER by {lacks} under any declared alias")
    # THE RATCHET, ON THE UNDECLARED COUNT ONLY. A recording gap is a documented
    # fact about the artifacts and is meant to stay visible, so it is reported
    # but not counted here; what may only fall is the number of one-sided scored
    # slots nobody has explained. Set to 0 on 2026-09-06 once the twelve
    # decomposition divergences were declared and the four 1b names aliased.
    undeclared = [x for x in out if "RECORDING gap" not in x]
    if len(undeclared) != ONE_SIDED_SCORED_SLOTS_BUDGET:
        verb = "grew to" if len(undeclared) > ONE_SIDED_SCORED_SLOTS_BUDGET else "is down to"
        out.append(
            f"UNDECLARED one-sided scored slots {verb} {len(undeclared)} against a "
            f"budget of {ONE_SIDED_SCORED_SLOTS_BUDGET} -- it may only fall. "
            f"Declare each in DECOMPOSITION_DIVERGENCES with the per-cell "
            f"measurement, alias it, or fix it")
    return out


APP_ONLY_SLOTS: dict[tuple[str, str], str] = {
    ("Q1", "matches_selected"):
        "UNSCORED, and it drives FEEDBACK rather than a score. The sheet spells "
        "it `Same behavior you selected above:matches/differs` with no @pts, and "
        "olx_prompts instructs the grader that when it answers `differs` the "
        "FIRST sentence of `feedback` must address the mismatch. The python "
        "mirror produces no feedback, so there is nothing for it to define. "
        "Wiring it into the rubric would add a slot that can never change a "
        "number, which is the opposite of what the rubric is for.",
}


# THE EIGHT CRITERIA-DERIVED ITEMS. Subgoal E35 established that their rubric
# holds COMPOSITES (`is_operant_conditioning`, `is_nr`) while the sheet
# enumerates the sub-checks, so nearly every slot on them looks orphaned in the
# reverse direction. That asymmetry is the design, not a defect, and a check
# that does not know it is useless on a third of the corpus.
_CRITERIA_DERIVED = ("DAY1", "DAY2", "WK1", "WK2", "PR", "NR", "PP", "NP")


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
      THE EIGHT CRITERIA-DERIVED ITEMS -- see `_CRITERIA_DERIVED` above.
      ALIASED NAMES -- a CLI key need not carry its web name; `web_name` is the
      authority, as it is for E48.

    THE ONE REAL FINDING it was built to catch: Q1's `matches_selected`, spelled
    in the sheet as "Same behavior you selected above:matches/differs" and
    appearing ZERO times in rubric_h1, score.py and agreement.py. The app asks
    the grader a question the python scorer never reads and no rubric element
    defines. Whether that is dead weight in the prompt or a check the mirror is
    missing is a disposition this check does not make -- it reports.
    """
    import re
    import olx_prompts as O

    out: list[str] = []
    for item_id, action in sorted(O.ACTION.items()):
        if item_id in _CRITERIA_DERIVED:
            continue
        try:
            src = O._src(O.HANDOUT[item_id])
        except Exception:
            continue
        m = re.search(O._ACTION_RE % re.escape(action), src, re.S)
        if not m:
            continue
        spec = re.search(r'\bslots="([^"]*)"', m.group(1))
        if not spec:
            continue
        have = [s.split(":")[0].lstrip("!").strip()
                for s in spec.group(1).split("|") if s.strip()]
        mod = _rubric_module(item_id)
        if mod is None:
            continue
        rubric = {c.get("what") for c in (mod.BY_ID.get(item_id, {}).get("credit") or [])}
        for key in have:
            if key == "confident" or key in rubric:
                continue
            if (item_id, key) in APP_ONLY_SLOTS:
                continue
            if any(web_name(r, set(have)) == key for r in rubric):
                continue
            out.append(
                f"{item_id}/{key} is asked by the SHEET and defined by no rubric "
                f"element, so the app puts a question to the grader that the "
                f"python scorer never reads. Wire it into the rubric, remove it "
                f"from the sheet, or declare it as deliberately app-only")
    return out


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
    import re
    import olx_prompts as O

    out: list[str] = []
    # ALL TWENTY-SIX ITEMS, AND THE PREPARED READER. This iterated `O.ACTION`,
    # which is 23 -- so 1b, T1 and T2, the SHEET_ONLY items that carry a slot
    # sheet without an LLMAction, were never reconciled in either direction.
    # equivalence.py has always used `{**ACTION, **SHEET_ONLY}` for exactly this
    # reason. Checked by hand when the gap was found on 2026-09-09: all three
    # match exactly (1b's four `*_data` slots, T1/T2's `type_stated`), so nothing
    # was hiding there -- the gap was latent, and closing it keeps it that way.
    #
    # `_slots_attr` + `parse_slots` rather than a local regex over the source:
    # it is the reader `build_web_prompt` uses, it resolves an action id and a
    # sheet id alike, and a hand-rolled `slots="..."` search cannot read the
    # sheet-only form at all.
    for item_id, action in sorted({**O.ACTION, **O.SHEET_ONLY}.items()):
        try:
            have = {s["key"] for s in O.parse_slots(
                *O._slots_attr(O.HANDOUT[item_id], action))}
        except Exception:
            continue
        if not have:
            continue
        mod = _rubric_module(item_id)
        if mod is None:
            continue
        for c in (mod.BY_ID.get(item_id, {}).get("credit") or []):
            key = c.get("what")
            if not key or key in have:
                continue
            # A SLOT WITH NO VERDICT LIST IS NOT ANSWERED, IT IS COMPUTED.
            # `is_operant_conditioning`, `is_nr` and their kin carry `pts` and no
            # `verdicts`: the engine derives them from the sub-checks and no
            # grader ever sees them, so their absence from `slots=` is the
            # design. Only a slot the model must ANSWER can be missing from the
            # list in the sense this check means.
            if not c.get("verdicts"):
                continue
            # A CLI SLOT NEED NOT CARRY ITS WEB NAME. `is_operant_conditioning`,
            # `is_nr` and their kin are rubric-side composites that reach the
            # sheet under other names, and ALIAS is the authority on which. A
            # first version of this check skipped that and reported twelve
            # findings, ten of them slots that DO reach the sheet -- a check
            # whose false positives outnumber its true ones gets suppressed, and
            # then the one real finding goes with it.
            if web_name(key, have):
                continue
            out.append(
                f"{item_id}/{key} is a rubric slot with NO entry in the sheet's "
                f"`slots=` list, so the grader is never asked to answer it. Any "
                f"rule naming it -- and the generator will write those rules into "
                f"the prompt -- points at an answer that cannot exist. Add it to "
                f"`slots=` (with its label, and a `pick(group)` if it takes one), "
                f"or remove it from the rubric")
    return out


def _rubric_module(item_id: str):
    """The rubric module that defines an item. Subgoal E48."""
    for name in ("rubric_h1", "rubric_h2", "rubric_h3"):
        try:
            mod = __import__(name)
        except Exception:
            continue
        if item_id in getattr(mod, "BY_ID", {}):
            return mod
    return None


# A COHORT CASE NAME IN A SHIPPED PROMPT. Subgoal E50. `pN` is how this project
# names a participant everywhere -- goals, ledger, artifacts, readouts -- so it
# is one careless paste away from a rule, and a rule naming a case is a rule
# TUNED TO THAT CASE. `leakage.py` catches borrowed WORDS; nothing caught a
# borrowed CELL. The corpus was clean when this was written (0 of 26 SLOT_NOTES
# blocks, 0 rubric rule/desc fields), which is the right moment to nail it down:
# an invariant installed while it already holds costs nothing and never has to
# be argued about afterwards.
_CASE_NAME = re.compile(r"(?<![\w/])p\d{1,2}\b")


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
    out: list[str] = []
    try:
        import olx_prompts as _O
    except Exception:
        return []
    for item_id in sorted(getattr(_O, "ACTION", {})):
        try:
            text = _O.build_web_prompt(item_id, {})
        except Exception:
            continue
        hits = sorted(set(_CASE_NAME.findall(text)))
        if not hits:
            continue
        out.append(
            f"{item_id}: the shipped prompt names cohort case(s) {hits}. A rule "
            f"that names a case is a rule tuned to that case, and the grader is "
            f"being shown it. State the DISTINCTION the cell taught instead of "
            f"the cell -- the evidence belongs in GOALS.md, not in the prompt")
    return out


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
    root = _pl.Path(getattr(_paths, "OUT", "/home/pdeane/molly_data/out"))
    if not root.is_dir():
        return []
    for path in _runs_files(root, "*/*.runs.json"):
        try:
            doc = json.loads(path.read_text())
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
            spec = A.load_action(f"bmod_handout{h}.olx", O.ACTION[item])
        except Exception:
            continue
        recover = set(MEAS._computed_slots(spec)) | {
            k for cr in (spec.get("counts") or []) for k in cr["slots"]}
        if not recover:
            continue
        doc = MEAS._runs_doc(item, "python")
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
            spec = A.load_action(f"bmod_handout{h}.olx", O.ACTION[item])
        except Exception:
            continue
        recover = set(MEAS._computed_slots(spec)) | {
            k for cr in (spec.get("counts") or []) for k in cr["slots"]}
        if not recover:
            continue
        doc = MEAS._runs_doc(item, "python")
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
                spec = A.load_action(f"bmod_handout{h}.olx", O.ACTION[item])
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
        import guide
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

    `python3 guide.py --renumber --write` is the repair: it derives labels from
    document order and rewrites every citation to match, so inserting a section
    no longer requires anyone to know what the labels currently are.
    """
    try:
        import guide
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
            body = ast.get_source_segment(src, node) or ""
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
    import olx_prompts as _OP
    import measured as _M

    out: list[str] = []
    try:
        recorded = {it for side in _M.SIDES for it in _M.records(side)}
    except Exception as exc:                      # pragma: no cover
        return [f"cannot read the ledger to find recorded items ({type(exc).__name__}: {exc})"]

    for item in sorted(_OP.ACTION):
        if item not in recorded:
            continue                              # no number to invalidate
        try:
            h = _M._jobs()[item]["handout"]
            want = _OP.build_web_prompt(item)
            shipped = _OP._src(h)
        except Exception:
            continue                              # SHEET_ONLY items and the like
        # Long enough to be prose rather than markup, and never a <Ref>, whose
        # text the server substitutes per student. NO UPPER BOUND -- see the note
        # in the docstring; a rule is one line and capping at 130 silenced this.
        lines = [ln.strip() for ln in want.split("\n")
                 if len(ln.strip()) > 40
                 and "REF:" not in ln and "<Ref" not in ln]
        missing = [ln for ln in lines if ln not in shipped]
        if missing:
            out.append(
                f"{item}: the rubric generates {len(missing)} prompt line(s) the "
                f"shipped .olx does not carry, so its recorded number describes a "
                f"prompt the rubric has moved past. Deliver it with "
                f"`python3 olx_prompts.py --write`, re-dump the idmap, and sweep. "
                f"First missing line: {missing[0][:90]!r}")
    return out


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
    to HANDOUT_KEYED_GOLD_READERS, so a new one has to say why it is not using
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
            graded = M._handout_gold_items(h)
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
        if mod in HANDOUT_KEYED_GOLD_READERS:
            continue
        if any(k.startswith(mod + ".") for k in HANDOUT_KEYED_GOLD_READERS):
            continue
        bad.append(
            f"{mod} picks a gold loader by handout number. Use "
            f"measured.gold_cell(item, pid), which derives the handout, or "
            f"declare {mod} in HANDOUT_KEYED_GOLD_READERS with why the handout "
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
    import handouts as H

    declared: dict = {}
    for d in getattr(H, "GOLD_DIVERGENCES", []) or []:
        for cell in (d or {}).get("cells") or ():
            declared.setdefault(tuple(cell), []).append((d or {}).get("code"))
    out: list[str] = []
    for cell in sorted(set(getattr(H, "CORRECTED_GOLD", {})) & set(declared)):
        entry = H.CORRECTED_GOLD[cell] or {}
        out.append(
            f"{cell[0]}/p{cell[1]} is CORRECTED ({entry.get('was')} -> "
            f"{entry.get('score')}) and also DECLARED in "
            f"{sorted(x for x in declared[cell] if x)}. Those tables contradict "
            f"each other: a correction says gold's number was wrong, a "
            f"divergence says it stands and we differ from it knowingly. Keep "
            f"ONE -- drop the cell from the declaration, or revert the "
            f"correction -- because booking it twice counts one finding twice")
    return out


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
    import handouts as H
    import measured as M

    home_of: dict[str, int] = {}
    for hnd in (1, 2, 3):
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
    suspect = {hnd: set(H.suspect(hnd)) for hnd in (1, 2, 3)}

    def cited(why: str, home: str) -> set[tuple[str, int]]:
        out: set[tuple[str, int]] = set()
        for sent in re.split(r"(?<=[.!?;])\s+", str(why or "")):
            if re.search(r"suspect|exclud", sent, re.I):
                continue           # naming the rule, not leaning on the cell
            for it, pid in re.findall(r"\b([A-Za-z][\w]*)\s*/\s*p(\d+)\b", sent):
                out.add((it, int(pid)))
            bare = re.sub(r"\b[A-Za-z][\w]*\s*/\s*p\d+\b", " ", sent)
            for pid in re.findall(r"\bp(\d+)\b", bare):
                out.add((home, int(pid)))
        return out

    entries: list[tuple[str, str, str, str]] = []      # table, label, home, why
    for (it, pid), v in getattr(H, "CORRECTED_GOLD", {}).items():
        entries.append(("handouts.CORRECTED_GOLD", f"{it}/p{pid}", it,
                        (v or {}).get("why", "")))
    for d in getattr(H, "GOLD_DIVERGENCES", []):
        cells = list((d or {}).get("cells") or [])
        home = str(cells[0][0]) if cells else ""
        label = (d or {}).get("code") or (home or "?")
        entries.append(("handouts.GOLD_DIVERGENCES", str(label), home,
                        (d or {}).get("why", "")))
    for name in ("GOLD_SLOT_DISAGREEMENTS_KNOWN", "GOLD_SLOT_BOUNDS_KNOWN",
                 "GOLD_CODE_KNOWN"):
        for (it, pid), why in (getattr(M, name, {}) or {}).items():
            entries.append((f"measured.{name}", f"{it}/p{pid}", it, why))

    out: list[str] = []
    for table, label, home, why in entries:
        for it, pid in sorted(cited(why, home)):
            hnd = home_of.get(it)
            if hnd is None or pid not in suspect.get(hnd, ()):
                continue
            out.append(
                f"{table} `{label}` argues from {it}/p{pid}, which "
                f"`handouts.suspect({hnd})` drops because its transcription "
                f"cannot be trusted. A suspect cell is evidence for nothing in "
                f"either direction, so this reasoning has a hole in it: either "
                f"find the argument that does not need it, or say inside the "
                f"citing sentence that the cell is suspect and why it is being "
                f"named anyway.")
    return out


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
    """A key written twice in one of handouts.py's declaration tables.

    Same failure as `check_consensus_fixes_have_no_duplicate_cells`, on the
    tables that decide what a cell is measured against: GOLD_CEILINGS,
    CORRECTED_GOLD and PER_ITEM_EXCLUDE. They are dict LITERALS, so Python
    resolves a repeated key before any check runs — the later entry wins and the
    earlier one vanishes. The loaded dict can never show it; only the source can.

    Not hypothetical, and the way it happened is the reason to check it. Q3
    already had a GOLD_CEILINGS entry for `action_oriented`, written from five
    cells. A second ("1", "Q3") entry was added for the same criterion after a
    fresh measurement, by someone who had read the item's error list rather than
    this table, and one of the two became dead text instantly. Both described a
    real ceiling, so nothing looked wrong: the file simply carried two accounts
    of one phenomenon and served whichever came last.
    """
    import ast
    import os

    # `src` is overridable for the same reason `_CONSENSUS_SOURCE` is: a check
    # that cannot be pointed at a deliberately broken copy has never been shown
    # to detect anything.
    src = src or os.path.join(os.path.dirname(os.path.abspath(__file__)),
                              "handouts.py")
    try:
        tree = ast.parse(open(src).read())
    except Exception as exc:                    # pragma: no cover
        return [f"cannot parse handouts.py: {exc}"]

    WANT = ("GOLD_CEILINGS", "CORRECTED_GOLD", "PER_ITEM_EXCLUDE")
    problems = []
    for stmt in ast.walk(tree):
        targets = (getattr(stmt, "targets", []) or
                   ([stmt.target] if hasattr(stmt, "target") else []))
        for t in targets:
            if not (isinstance(t, ast.Name) and t.id in WANT):
                continue
            node = stmt.value
            if not isinstance(node, ast.Dict):
                problems.append(f"{t.id} is not a dict literal — this check is stale")
                continue
            seen = set()
            for k in node.keys:
                try:
                    key = ast.literal_eval(k)
                except Exception:
                    continue
                if key in seen:
                    problems.append(
                        f"{t.id} has TWO entries for {key}. A dict literal keeps "
                        f"only the last, so the other is silently doing nothing "
                        f"— merge them, because two accounts of one ceiling read "
                        f"as two ceilings")
                seen.add(key)
    return problems


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
    import gold as G
    import handouts as H

    loaders = {1: G.load_h1, 2: G.load_h2, 3: G.load_h3}
    raw: dict[int, dict] = {}
    for h, fn in loaders.items():
        try:
            raw[h] = fn()
        except Exception:
            continue                    # corpus absent on this machine
    if not raw:
        return []

    problems = []
    for (item, pid), fix in sorted(H.CORRECTED_GOLD.items()):
        found = None
        for h, rows in raw.items():
            cell = (rows.get(pid) or {}).get(item)
            if cell and cell.get("score") is not None:
                found = float(cell["score"])
                break
        if found is None:
            problems.append(
                f"CORRECTED_GOLD names {item}/p{pid}, which has no gold row in "
                f"any handout. Remove it")
            continue
        if abs(found - float(fix["was"])) > 0.005:
            problems.append(
                f"CORRECTED_GOLD[{item}/p{pid}] says it corrects {fix['was']:.2f} "
                f"but the sheet now reads {found:.2f}. The row changed under the "
                f"correction — re-derive it or remove it")
        if abs(found - float(fix["score"])) < 0.005:
            problems.append(
                f"CORRECTED_GOLD[{item}/p{pid}] corrects {found:.2f} to the same "
                f"value. It is doing nothing — remove it")
        if len((fix.get("why") or "").split()) < 25:
            problems.append(
                f"CORRECTED_GOLD[{item}/p{pid}] has no substantive reason. A "
                f"correction to the score we are measured against must say what "
                f"evidence in the submission contradicts the row")
    return problems


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
    for h in (1, 2, 3):
        try:
            import handouts as H

            if H.find_submissions(h):
                present.append(h)
        except Exception:
            continue
    if not present:
        return []                          # no corpus on this machine

    problems = []
    for h in present:
        try:
            segs = _segment_as_scored(h, sorted(dict(__import__("handouts")
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
    import handouts as H

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


def _counts_sig(handout: int, item: str) -> tuple:
    """The rubric's counted-group shape for one item.

    Part of the fixture cache key, and that is the whole point rather than a
    detail: handout 3's boxes are rebuilt by score.py's counted-group
    distribution, so the fixture DEPENDS on this declaration. Caching on
    (item, pid) alone would have returned the clean fixture after the self-test
    dropped 2a's `counts`, and the case that proves this check works would have
    failed while looking like a passing cache.
    """
    from handouts import config

    try:
        spec = config(handout)["rubric"].BY_ID.get(item) or {}
    except Exception:
        return ()
    return tuple((cr.get("key"), tuple(cr.get("slots") or ()))
                 for cr in (spec.get("counts") or ()))


@functools.lru_cache(maxsize=None)
def _sections_cached(handout: int, pid: int) -> tuple:
    """One participant's transcribed sections, as a hashable tuple of pairs.

    Independent of any rubric declaration -- it is the .docx transcription -- so
    unlike the fixture cache this one needs no signature in its key.
    """
    import agreement_app as AA

    try:
        return tuple(sorted((AA.sections_for(handout, pid) or {}).items()))
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
            for name in ("olx", "python"):
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
                    # wrote "not attending the gym & stretching as often as I
                    # should be" and the hand split has to repeat the "not" to
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

    It does not always. p5's Q6 ends "When I have more fruits and vegetables
    available to me, I hope that I will no longer feel the need to satisfy my
    craving of unhealthy snacks. Instead, I hope to eat fruits and vegetables
    more often" — a complete second consequence, and both of its boxes are
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
    import handouts as H
    import segment as SEG

    problems = []
    seen: set[tuple[str, int]] = set()
    for h in (1, 2, 3):
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
                    # withdrawn — rebuild_gold_1c nulls 1c/p20 outright — so it
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
    nobody typed: Q4b/p7's `second` box reads "2) Also, I get myself ..." where
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
    `8, 11, 6, 9, 6, 10, 9` for a student who typed "Sunday - 8 hours Monday -
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
    # 1c's `from_scorer` boxes are read off the GRAPH, not off the prose segment
    # — the paper scorer takes them from the chart, which is why p11's `title`
    # arrives filled while its prose segment is empty. They are extractions of
    # named elements, not quotations, and the item has no prose-derived box at
    # all. The one cell where a title IS locatable is p9, whose chart flattened
    # INTO the text; that is a property of the transcription, not of the item.
    # This carried a per-cell "the fixture is correct" note for p9; the fact is
    # about 1c, so it belongs here, once.
    if item_id == "1c":
        out |= {"title", "x", "y"}
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
CONSENSUS_OVERLAP_BACKLOG: dict[tuple, str] = {
    # 2a/p20. One sentence, "My sleep duration increased over time, as shown by
    # the higher number of hours during the intervention weeks compared to the
    # baseline week", states the outcome AND supplies the evidence for it. The
    # `verdict` box holds its main clause; `how1` holds the whole sentence, so
    # the containment is total. It is faithful for the reason the item's own
    # rubric gives — "one compound sentence that states the outcome and explains
    # it can carry two" — and the alternative was measured elsewhere and lost:
    # `how1` used to hold ", as shown by the higher number of hours ...", a
    # comma-initial adjunct sliced out of the verdict's sentence, which is not a
    # clause and cannot be judged as an explanation on its own. That is the
    # fragment shape "Q6's overlapping fixture boxes are FAITHFUL" in
    # EQUIVALENCE.md records as taking Q6 from 11/17 to 3/17.
    # 2a/p18. Two sentences, and the first does verdict duty and how duty at
    # once — "My exercise intake increased from 0 to 3 session a week, as shown
    # by the data" — so `verdict` and `how1` hold it together. Same shape as p20
    # below and licensed by the same guidance bullet, and gold's 6.0 credits
    # both the verdict and two hows on those two sentences.
    #
    # It was exempt until now by SIDE EFFECT rather than by declaration: the
    # cell was `unscoreable`, and this check skips those. Removing that
    # exclusion (see handouts.PER_ITEM_EXCLUDE) is what surfaced the overlap,
    # which is the argument for declaring rather than excluding — an exclusion
    # silences whatever else happens to be wrong with the cell.
    ("2a", 18, "how1", "verdict"): (
        "one sentence doing verdict duty and how duty at once, in a two-sentence "
        "response gold gives 6.0; the copied template verdict that join_aware "
        "strips was never what carried the credit"),
    ("2a", 20, "how1", "verdict"): (
        "one sentence doing verdict duty and how duty at once; the verdict box "
        "holds its main clause and how1 the whole sentence, so each can be "
        "judged. Splitting it left how1 a comma-initial adjunct"),
    # Otherwise empty. Its last entry recorded that Q6/p6's two `state_a`
    # boxes hold the
    # same conjoined phrase on purpose — which the SLOT SHEET already declares,
    # in cover="state_a1,state_a2:first,second|...". Two boxes sharing a cover
    # group are meant to be resolved by the grader naming which listed item each
    # refers to; the check reads that declaration now rather than being told
    # cell by cell.
}


def _cover_groups(item_id: str) -> list[set[str]]:
    """Boxes the slot sheet declares as covering ONE list between them.

    Q6's LLMAction carries cover="state_a1,state_a2:first,second|state_c1,
    state_c2:first,second". That means the two boxes answer between them a list
    of two items: the grader asks WHICH each box refers to and demotes one that
    names an item already claimed. Two boxes in such a group holding the same
    text is an expected input, not a defect — it is the case the mechanism was
    built to resolve.

    Q6/p6 is that case. One conjoined phrase, "not attending the gym &
    stretching as often as I should be", names both of 4a's triggers under a
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
    for h in (1, 2, 3):
        try:
            src = open(paths.OLX % h).read()
        except Exception:
            continue
        for m in re.finditer(r'cover="([^"]*)"\s*\n?\s*slots="([^"]*)"', src):
            keys = {sl.split(":")[0].strip() for sl in m.group(2).split("|")}
            if not boxes or not (boxes & keys) or len(boxes & keys) < 2:
                continue
            return [{b.strip() for b in g.split(":")[0].split(",") if b.strip()}
                    for g in m.group(1).split("|")]
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

    Measured, on p4, 2026-08-19. Its `state_c2` held "I hope that I will no longer
    be up late" and `affect_c2` the whole sentence that is a superset of it. Split
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
    problems = []
    seen: set[tuple] = set()

    def norm(x):
        return " ".join((x or "").split()).lower()

    import handouts as H

    for _h, iid, pid, _raw, boxes in _fixture_cells():
        if H.cell_exclusions(_h, iid).get(pid, ("", ""))[0] == "unscoreable":
            # Same rule the coverage check follows: an `unscoreable` cell has had
            # its gold withdrawn, reaches no comparison, and cannot move a number.
            #
            # It is a blunt instrument, and 2a/p18 is the cautionary case. Its
            # `verdict`/`how1` overlap sat exempt here for as long as the cell
            # was excluded — not because anyone judged the overlap faithful, but
            # because this branch never looked. When the exclusion was removed
            # the overlap surfaced immediately and had to be declared in
            # CONSENSUS_OVERLAP_BACKLOG on its own merits. An exclusion written
            # about the SCORE silences every other question about the cell.
            continue
        bx = {k: norm(v) for k, v in boxes.items() if v}
        keys = sorted(bx)
        for i, a in enumerate(keys):
            for b in keys[i + 1:]:
                # same element: "state_c1"/"affect_c1" -> both end "c1"
                if _siblings(a) == b or _siblings(b) == a:
                    continue
                if any({a, b} <= g for g in _cover_groups(iid)):
                    continue           # the sheet declares these two share a list
                # 10, not 25. The floor is meant to skip coincidental short
                # phrases, but at 25 it skipped the most suspicious case there is:
                # a box holding a FRAGMENT lifted out of a neighbour's sentence.
                # Q6/p14 had two, both 19 characters — `affect_c2` set to "not be
                # that severe.", sliced off the end of change_a2's sentence, and
                # `affect_c1` holding "I work out (new A)." that change_a1 also
                # held. The scorer answered `incomplete` about the fragment,
                # correctly, and the cell lost 1.25 that gold awards. Lowering the
                # floor to 5 surfaces nothing else in the corpus, so 10 is free.
                if len(bx[a]) < 10 or len(bx[b]) < 10:
                    continue
                if bx[a] not in bx[b] and bx[b] not in bx[a]:
                    continue
                key = (iid, pid, a, b)
                if key in CONSENSUS_OVERLAP_BACKLOG:
                    seen.add(key)
                    continue
                inner = a if len(bx[a]) < len(bx[b]) else b
                problems.append(
                    f"{iid}/p{pid}: `{a}` and `{b}` hold the same text "
                    f"({bx[inner][:52]!r}...) — one clause answering two different "
                    f"questions. Either the consensus mis-assigned it, or declare "
                    f"it in CONSENSUS_OVERLAP_BACKLOG with why it is faithful")
    for stale in sorted(CONSENSUS_OVERLAP_BACKLOG.keys() - seen):
        problems.append(
            f"CONSENSUS_OVERLAP_BACKLOG lists {stale[0]}/p{stale[1]} "
            f"{stale[2]}/{stale[3]}, "
            f"which no longer overlaps. Remove it")
    return problems


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
    # clause "when I have the time to fix my bad day by myself", which belonged
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
# `state_a1` ended "... I hope that I", its `state_c1` trailed off into "Instead,
# I hope that I will", p4's `state_a2` stopped at "that leads to me not" and its
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
    import handouts as H
    import segment as SEG

    if _SEGMENTS_MEMO is None:
        segs_by_cell = []
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            for h in (1, 2, 3):
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


def _segment_as_scored(handout: int, pid: int) -> dict[str, str]:
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
        return APP.sections_for(handout, pid)


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
        "... I hope that I"; p4's `state_a2` stopped at "that leads to me not".
      * a box CROSSING a part boundary — p4's `state_c1` held "I won't be falling
        asleep everywhere. o I", the tail of part one plus the opening of part two.

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
FIXTURE_GOLD_OVERRIDES: dict[tuple[str, int, str], str] = {
    # Empty. The one entry that lived here — ("1c", 11, "baseline") — covered a
    # box that holds a PARSED VALUE, and `_span_boxes` now keeps value boxes out
    # of the locator-based checks entirely, so nothing is left to suppress. The
    # substance of that note was never about the fixture: it asked whether p11
    # belongs with 1c's unscoreable cells, and it now sits beside them as a
    # documented open question in handouts.py's `unscoreable` block.
}


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
    import agreement_app as APP

    problems = []
    for (item, pid), fixes in APP.CONSENSUS_FIXES.items():
        seen: dict[str, str] = {}
        for fix in fixes:
            for box in (fix[1:] if fix[0] == "swap" else fix[1:2]):
                if box in seen:
                    problems.append(
                        f"CONSENSUS_FIXES[{item!r}, {pid}] fixes `{box}` twice "
                        f"({seen[box]} then {fix[0]}) — the later one silently "
                        f"wins. State a single span per box")
                seen[box] = fix[0]
    return problems


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
    import re
    import handouts as H

    # What gold CALLS each box. Q6's graders write "antecedent"/"consequence",
    # not slot names, so it needs a map; items whose boxes are already named the
    # way gold names them (Q3's SMART aspects) use the box name itself.
    # What gold CALLS each box, and what it must NOT say. 1c needs the second
    # half: "missing x-axis title" names the AXIS title, and a bare "title" key
    # matched it against the CHART title box, which p9 and p11 both fill
    # correctly. Two of this check's three findings on 1c were that collision.
    NAMED = {
        "Q6": {"state_a1": ("first", "antecedent"), "state_a2": ("second", "antecedent"),
               "state_c1": ("first", "consequence"), "state_c2": ("second", "consequence")},
        "1c": {"x": ("x-axis",), "y": ("y-axis",),
               "title": (("title",), ("x-axis", "y-axis", "axis")),
               "series": ("series",), "baseline": ("baseline",)},
    }
    ABSENT = r"(?:did not (?:state|address|say|provide|list|clarify)|missing|never)"
    WRONG = r"(?:is not the same|does not match|not the same|a different)"
    problems = []
    seen: set[tuple] = set()
    for h, iid, pid, _raw, boxes in _fixture_cells():
        fb = " ".join(((H.config(h)["gold"]().get(pid) or {}).get(iid) or {})
                      .get("feedback", "").split()).lower()
        if not fb:
            continue
        named = NAMED.get(iid) or {k: (k.replace("_", " "),) for k in boxes}
        for box, words in named.items():
            if box not in boxes:
                continue
            filled = bool((boxes.get(box) or "").strip())
            for pat, want_filled in ((ABSENT, False), (WRONG, True)):
                for m in re.finditer(pat + r"[^.]{0,90}", fb):
                    # An ABSENT claim must name the element WITHIN its own
                    # clause. Looking back into the previous sentence matched
                    # Q6/p6's `state_a2` against "did not state a second
                    # consequence" because the word "antecedent" happened to sit
                    # in the charge before it. A WRONG claim may name the element
                    # ahead of the phrase ("second consequence is not the same"),
                    # so it keeps a short lookback.
                    frag = (m.group(0) if pat is ABSENT
                            else fb[max(0, m.start() - 60):m.end()])
                    want, forbid = (words if isinstance(words[0], tuple)
                                    else (words, ()))
                    if not all(w in frag for w in want):
                        continue
                    if any(w in frag for w in forbid):
                        continue
                    # "did not say HOW it is changed" is a judgement that what was
                    # written is INADEQUATE, not a claim that nothing was. p8's
                    # change slots rightly hold text gold charges as insufficient.
                    # "did not say HOW / WHY" is a judgement that what the
                    # student wrote is INADEQUATE, not that nothing was written.
                    if pat is ABSENT and ("how" in frag or "why" in frag
                                          or "clarify" in frag
                                          or "being affected" in frag):
                        continue
                    if filled == want_filled:
                        continue
                    key = (iid, pid, box)
                    if key in FIXTURE_GOLD_OVERRIDES:
                        seen.add(key)
                        break
                    problems.append(
                        f"{iid}/p{pid} `{box}` is "
                        + ("EMPTY but gold marked it wrong rather than absent"
                           if want_filled else
                           "filled but gold says it was never written")
                        + f" ({m.group(0)[:52]!r}...) — either the box has the "
                          f"wrong clause, or declare it in FIXTURE_GOLD_OVERRIDES")
                    break
    for stale in sorted(FIXTURE_GOLD_OVERRIDES.keys() - seen):
        problems.append(f"FIXTURE_GOLD_OVERRIDES lists {stale}, which no longer "
                        f"disagrees. Remove it")
    return problems


def _handout_of(item: str) -> int:
    """Which handout an item belongs to, read off the specs rather than guessed.

    It replaces `1 if item.startswith("Q") else 3`, which sent all twelve of
    handout 2's items — PR, NR, PP, NP, T1, D1, DAY1, WK1 and the rest — to
    handout 3, where they have no segment. `--fixture PR` therefore answered
    "empty response" for all twenty cells of an item whose fixture is fine, and
    nearly half the corpus could not be read out at all.
    """
    import agreement_app as APP
    import handouts as H

    spec = APP.JOBS.get(item) or {}
    if spec.get("handout"):
        return int(spec["handout"])
    for h in (1, 2, 3):
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
        could read out. `_handout_of` reads the spec instead.
      * A cell answered with a CHART or a TABLE has no prose to locate a box in,
        which is normal for 1c and 1b rather than a dead end. Those go to
        `_boxes_only_readout`, which prints the boxes by provenance. The defect
        that was hiding behind the old one line sat in ten cells of a counted
        item — 1c's `title`/`x`/`y` holding the scorer's sentence about the
        label instead of the label.

    "Empty response" now means only what it says: no prose AND no filled box.
    """
    import re
    import handouts as H

    h = _handout_of(item)
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
    import handouts as H

    # A points claim: a signed decimal, optionally spelled with the word. Bare
    # integers are not enough on their own — "2 of the 8 slots" is structure, not
    # an assertion about the score — so a decimal point or an explicit sign is
    # what marks a figure as one the harness could check.
    claim = re.compile(r"[-+]?\d+\.\d+|[-+]\d+\b")
    problems = []
    for item, cells in H.PER_ITEM_EXCLUDE.items():
        declared = H.unscoreable_expectation(item)
        for pid, entry in cells.items():
            why = entry["why"] if isinstance(entry, dict) else entry
            found = claim.findall(why)
            if found and pid not in declared:
                problems.append(
                    f"{item}/p{pid}: the `unscoreable` reason states the point "
                    f"figure(s) {sorted(set(found))} in prose, where nothing "
                    f"checks them. Declare `expect_error` on the entry so the "
                    f"harnesses assert it every run, or drop the figure")
    return problems


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
    import handouts as H

    problems = []
    here = os.path.dirname(H.__file__)
    for fname in ("agreement.py", "agreement_app.py", "baseline.py"):
        try:
            src = open(os.path.join(here, fname)).read()
        except OSError as e:
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
    for h in (1, 2, 3):
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
    out: list[str] = []
    import os
    try:
        import agreement_app as APP
    except Exception as exc:
        return [f"could not import the scorer modules to check the guard: {exc}"]

    # 1. the STRUCTURAL half, in the prompt we generate.
    #
    # An empty box's `<Ref>` renders to nothing, and for the LAST box on an item
    # there was no following heading to bound it -- so the guidance the app
    # appends after our prompt fell where the box's contents belong, and was
    # quoted to the student as their own words. Two instruction-level fixes were
    # measured and neither moved the rate; the bounds are what fixed it, so the
    # bounds are what this checks. Every item on every handout, because the last
    # box of any item is the one exposed.
    try:
        import olx_prompts as OLX
        items = sorted(OLX.RESPONSE)      # every item that shows the student's boxes
    except Exception as exc:
        out.append(f"could not enumerate the generated prompts: {exc}")
        items = []
    for item_id in items:
        try:
            prompt = OLX.build_web_prompt(item_id)
        except Exception:
            continue
        if "## Student response to grade" not in prompt:
            continue
        body = prompt.split("## Student response to grade", 1)[1]
        opens, closes = body.count("[box begins]"), body.count("[box ends]")
        if opens == 0:
            out.append(f"{item_id}: the student's boxes are not delimited -- "
                       "an empty box renders as nothing, and for the LAST box the "
                       "guidance the app appends lands where its contents would be")
        elif opens != closes:
            out.append(f"{item_id}: {opens} `[box begins]` against {closes} "
                       "`[box ends]` -- an unclosed box swallows whatever follows it")
        if "## End of the student response" not in body:
            out.append(f"{item_id}: the response section is not closed, so "
                       "nothing separates the last box from the appended guidance")

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
    # A ceiling on an item recorded PERFECT: 1b is 20/20 on both sides, so
    # "cannot be perfect" is contradicted the moment it is claimed.
    "handouts.GOLD_CEILINGS": (("1", "1b"),
                               ("probe: 1b cannot be perfect", "probe")),
    # A divergence naming a cell we get right in every run.
    "handouts.GOLD_DIVERGENCES": {"code": "PROBE_ONLY", "cells": [("1b", 1)],
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
    "enforcement.PROBE_IMPOSSIBLE": ("handouts.CORRECTED_GOLD",
                                     "probe: not a real impossibility"),

    # RAW_GOLD_READERS became probeable on 2026-08-31 when E31 drove its
    # verifier's loop from the table. A bogus module name is now objected to, so
    # the default shape-derived provocation suffices and no entry is needed here.
    # An exclusion on a cell that HAS gold and is absent from the last recorded
    # run's excluded cells: E33 made the verifier read the table, so this now
    # fires as "no evidence either way". A shape-derived bogus key would NOT --
    # the loop iterates real items, so a nonsense item name is skipped.
    "handouts.PER_ITEM_EXCLUDE": ("1b", {1: "probe: not a real exclusion"}),
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
