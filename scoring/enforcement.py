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

import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from handouts import config
from score import build_schema, derive_ledger, derive_oc_ledger

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
    "consequence_valence": "gain",
    "trigger_expects": "gain",
    # Diagnostic only: gates nothing, scores nothing, so it has no failing
    # value. Both tables name the same one, which is what "this field cannot
    # cost the item anything" looks like to the probe.
    "restriction_authored": "relieved",
    "restricts": "target_behavior",
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
    "consequence_valence": "loss",   # a loss for doing well
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
}
# The two type fields are handled separately: their failing value depends on the
# other one, and a naive flip can make them agree again.
_TYPE_FIELDS = ("observed_type", "named_type", "trigger_behavior")

# The same rule wears different names on the two sides. Kept explicit and small;
# an unmapped key is REPORTED, never assumed equivalent.
ALIAS = {
    "behavior": "names_behavior",
    # The web renamed this to say the good state, and inverted it to match the
    # rest of the vocabulary: `met` is phrased directly. The CLI input keeps the
    # old name and its boolean sense (True = phrased by what is avoided).
    "avoidance_frame": "phrased_directly",
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
    "cadence_ok": ("cadence_is_daily", "cadence_is_weekly"),
}


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
        for r in it.get("onlyif", []):
            names = {c["what"] for c in it.get("credit", [])}
            for k in (r["key"], r["cond"]):
                if k not in names:
                    problems.append(f"{it['id']}: onlyif names `{k}`, which is not a "
                                    f"credit component")
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
    a = {k: v for k, v in _PASS.items() if k in req}
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
        a[key] = _FAIL[key]
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
        computed = {r["key"] for r in item.get("equals", [])}
        # Counted members are derived from the count, so they are not asked either.
        for cr in item.get("counts", []):
            computed |= set(cr["slots"])
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


if __name__ == "__main__":
    import json
    print(json.dumps(cli_signatures(), indent=1))


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


def check_slot_rules_reach_both_prompts() -> list[str]:
    """Does per-slot judging text reach the PAPER prompt as well as the web's?

    The web checklist and the paper component list are each a slot-specific
    field, and only the rubric is read by both generators. Text parked in
    `olx_prompts.SLOT_NOTES` therefore reaches the web and the CLI harness and
    silently leaves score.py behind — the two sides go on applying different
    rules while every existing audit stays green, because `--prompts` only ever
    counts rubric elements the WEB is MISSING. It has no notion of the web
    carrying something the paper does not.

    That is not hypothetical. Q4b's five substitution tests lived in SLOT_NOTES
    for a day: the web and CLI moved from 69% to 88% on them and the paper
    scorer never saw them, with `--item Q4b` reporting "missing 0/4, 0/5, 0/3".

    So: any SLOT_NOTES entry naming a scored slot of an item is a finding. The
    rubric's per-component `rule` field is the shared home, and both generators
    render it into their own slot-specific position.

    Mapping notes are exempt. SLOT_NOTES' documented job is to point a web check
    at its numbered paper criterion, and such a note carries no judging text of
    its own — it is short and refers to a criterion. The heuristic is length,
    which is crude but errs the right way: a long note is doing more than
    mapping.
    """
    import olx_prompts as OP
    import rubric_h1, rubric_h2, rubric_h3

    MAPPING_MAX = 220        # a "see criterion N" pointer, not a rule

    # PRE-EXISTING, and declared rather than hidden. These predate the `rule`
    # field and each one is a real divergence: the web and CLI apply them and
    # score.py does not. They are listed so that a NEW one fails the audit
    # immediately, instead of joining a backlog nobody can see. Migrating one
    # means moving its text to the credit component's `rule` field and
    # re-measuring the paper scorer on that item — a scoring change per item,
    # which is why they are not being done in a batch.
    BACKLOG = ['1a:baseline_week', '1a:distinguishes_periods', '1a:week_1', '1a:week_2', '1c:has_own_graph', '1c:legend', 'D1:defines_type', 'D2:defines_type', 'Q1:matches_selected', 'Q2:reasons_given', 'Q2:wgb_inverts_utb', 'Q2:wgb_is_counterpart', 'Q5:example_2', 'consequence_asserted', 'matches_chosen_type', 'named_type', 'reasons_failing', 'reasons_substantial']

    problems = []
    scored = {}
    for mod in (rubric_h1, rubric_h2, rubric_h3):
        for item in mod.ITEMS:
            for c in item.get("credit", []) or []:
                scored.setdefault(item["id"], set()).add(c["what"])

    seen_backlog = set()
    for key, note in (getattr(OP, "SLOT_NOTES", {}) or {}).items():
        if len(note) <= MAPPING_MAX:
            continue
        if key in BACKLOG:
            seen_backlog.add(key)
            continue
        item_id, _, slot = key.partition(":")
        if not slot:                       # unscoped note, applies by slot name
            item_id, slot = None, key
        owners = ([item_id] if item_id and item_id in scored
                  else [i for i, s in scored.items() if slot in s])
        if not owners:
            continue                       # not a scored slot — nothing to share
        problems.append(
            f"SLOT_NOTES[{key!r}] is {len(note)} chars of judging text on a scored "
            f"slot of {', '.join(sorted(owners))}. SLOT_NOTES is web-only, so the "
            f"paper scorer never sees it. Move it to that credit component's "
            f"`rule` field, which both generators render")

    # A backlog entry that has gone means the list is rotting: either it was
    # migrated (good — remove it from BACKLOG) or its note shrank below the
    # mapping threshold (also worth knowing).
    for stale in sorted(set(BACKLOG) - seen_backlog):
        problems.append(
            f"BACKLOG names SLOT_NOTES[{stale!r}], which no longer qualifies. If it "
            f"was migrated to a `rule` field, drop it from BACKLOG")
    return problems


def check_slot_rules_are_vocabulary_neutral() -> list[str]:
    """Does any shared `rule` name a verdict token literally?

    A `rule` is rendered into BOTH prompts, and the two sides do not share a
    verdict vocabulary: the web sheet says `wrong_kind` where the rubric says
    `not_active`, which is what enforcement.ALIAS exists to record. So a rule
    that names one side's token is unreadable on the other — and unreadable in
    the worst way, because it still looks like an instruction.

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
    import rubric_h1, rubric_h2, rubric_h3
    from slot_vocab import KNOWN_VERDICTS

    problems = []
    for h, mod in ((1, rubric_h1), (2, rubric_h2), (3, rubric_h3)):
        for item in mod.ITEMS:
            for c in item.get("credit", []) or []:
                rule = c.get("rule")
                if not rule:
                    continue
                named = sorted({v for v in KNOWN_VERDICTS
                                if f"`{v}`" in rule and v not in ("met", "absent")})
                if named:
                    problems.append(
                        f"H{h} {item['id']}.{c['what']}: `rule` names the verdict "
                        f"{named} literally. The rule is rendered into both prompts "
                        f"and the two vocabularies differ, so one side gets an "
                        f"instruction about a token it cannot emit. Use `{{fail}}`, "
                        f"which each generator fills with its own verdict")
                if "{fail}" not in rule and not named:
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
          "are correct that way: `state_a1` ends on its comma (\"{{corpus:Q6/p18:state_a1:0:12:sha=108e14fe0759:shape=R12-0-20}}"
          "{{corpus:Q6/p18:state_a1:13:50:sha=5b3905f38a6c}}\") and `state_a2` opens "
          "lowercase (\"{{corpus:Q6/p18:state_a2:0:46:sha=ca9a85478c24:shape=R46-0-20}}"
          "{{corpus:Q6/p18:state_a2:47:60:sha=a4dc939bb5ba}}\"), because p18 names each antecedent in a subordinate "
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
          "text RUNS ([\'Time\', \' {{corpus:1c/p6:title:5:33:sha=90d22ddc95fc}}\']) instead of "
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
          "the question asks the student to supply. p4\'s first box reads \"{{corpus:Q5/p4:first:0:1:sha=a83dd0ccbffe:shape=R1-0-20}}"
          "{{corpus:Q5/p4:first:2:23:sha=400cd580a803}}\" — checked against the submission, that is the "
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
          "explanation: p13's how2 holds its \"{{corpus:2a/p13:how2:0:28:sha=2fa2e12271d7:shape=R28-0-20}}"
          "{{corpus:2a/p13:how2:29:46:sha=aaccc09e897f}}\" because the student wrote it, and gold charges "
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
          "`wk1` is `8, {{corpus:1a/p15:wk1:3:19:sha=7b2512f124b3}} 9` for a table reading \"Sunday - 8 "
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

    problems = []
    for item, state in MEAS.status():
        if state.startswith("ABSENT"):
            problems.append(
                f"{item} has no entry in MEASURED.json. Sweep it and run "
                f"`measured.py --record {item} OUT/{item}.runs.json`, or declare "
                f"`pending` with a reason saying when it will be measured")
        elif state.startswith("STALE PROMPT"):
            problems.append(
                f"{item}: {state}. Its prompt text changed since the recorded "
                f"measurement, so the recorded number is not this prompt's "
                f"number — re-sweep and re-record")
        elif state.startswith("STALE CELLS"):
            problems.append(
                f"{item}: {state}. Its denominator changed since the recorded "
                f"measurement, so the recorded number was computed over a "
                f"different set of cells — re-sweep and re-record")
    return problems


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


def check_fixture_covers_the_response() -> list[str]:
    """Does the split fixture still contain the student's whole answer?

    Q6's eight boxes are a RECONSTRUCTION — a frozen consensus table with
    tie-breaks — and it is the input every scorer sees. `check_handsplit_rows_are_disjoint`
    asserts no row swallows another, but nothing asserted that a split PRESERVES
    the response.

    It does not always. p5's Q6 ends "{{corpus:Q6/p5:state_c2:0:141:sha=aa2e6137e3b0:shape=S6-0a20202020,S22-0a20202020}} {{corpus:Q6/p5:affect_c2:0:49:sha=c20b853f77bc:shape=S7-0a20202020}} often" — a complete second consequence, and both of its boxes are
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
    # 2a/p20. One sentence, "{{corpus:2a/p20:how1:0:50:sha=2f8ba2be6c18}}
    # {{corpus:2a/p20:how1:51:123:sha=312f58eeb41c}}
    # baseline week", states the outcome AND supplies the evidence for it. The
    # `verdict` box holds its main clause; `how1` holds the whole sentence, so
    # the containment is total. It is faithful for the reason the item's own
    # rubric gives — "one compound sentence that states the outcome and explains
    # it can carry two" — and the alternative was measured elsewhere and lost:
    # `how1` used to hold ", {{corpus:2a/p20:how1:39:77:sha=781132f0280c}} ...", a
    # comma-initial adjunct sliced out of the verdict's sentence, which is not a
    # clause and cannot be judged as an explanation on its own. That is the
    # fragment shape "Q6's overlapping fixture boxes are FAITHFUL" in
    # EQUIVALENCE.md records as taking Q6 from 11/17 to 3/17.
    # 2a/p18. Two sentences, and the first does verdict duty and how duty at
    # once — "{{corpus:2a/p18:how1:0:65:sha=bc45c9fc7f7b}}
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

    Q6/p6 is that case. One conjoined phrase, "{{corpus:Q6/p6:state_a1:0:21:sha=641b355f6e09}} &
    {{corpus:Q6/p6:state_a2:4:38:sha=56244251ed73}}", names both of 4a's triggers under a
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

    Measured, on p4, 2026-08-19. Its `state_c2` held "{{corpus:Q6/p4:state_c1:0:34:sha=4e032e011208:shape=S6-0a20202020}} late" and `affect_c2` the whole sentence that is a superset of it. Split
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
                # `affect_c1` holding "{{corpus:Q6/p14:change_a1:63:82:sha=2db206dd72e6}}" that change_a1 also
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
    # clause "{{corpus:Q6/p2:change_a1:174:215:sha=9feaaabd7986}} myself", which belonged
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

    out = []
    for h, iid, pid, raw in _SEGMENTS_MEMO:
        boxes = _span_boxes(iid, pid)
        if len(boxes) >= 2:
            out.append((h, iid, pid, raw, boxes))
    return out


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
      * a box CROSSING a part boundary — p4's `state_c1` held "{{corpus:Q6/p4:affect_c1:91:128:sha=f850fdd69cda:shape=S3-0a2020202020202020,A5}} o I", the tail of part one plus the opening of part two.

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
