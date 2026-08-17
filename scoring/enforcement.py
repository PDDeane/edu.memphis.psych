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
}
_FAIL = {
    "behavior": "",
    "stimulus": "",
    "contingent": False,
    "follows_behavior": False,
    "stimulus_is_arranged": False,
    "avoidance_frame": True,          # advisory only; must show zero loss
    "cadence_ok": False,
    "targets_own_behavior": False,
    "targets_intended_behavior": False,
    "consequence_asserted": False,
}
# The two type fields are handled separately: their failing value depends on the
# other one, and a naive flip can make them agree again.
_TYPE_FIELDS = ("observed_type", "named_type")

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
    """Lowercased, whitespace-collapsed, with smart punctuation folded."""
    s = s.lower().replace("’", "'").replace("‘", "'")
    s = s.replace("“", '"').replace("”", '"').replace("—", "-")
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
CORPUS_QUOTE_BACKLOG = {
    ("1a", 11),
    ("1a", 14),
    ("1a", 19),
    ("2a", 18),
    ("2a", 20),
    ("D2", 9),
    ("DAY1", 1),
    ("DAY1", 15),
    ("DAY1", 16),
    ("DAY2", 13),
    ("NP", 14),
    ("NR", 7),
    ("NR", 14),
    ("NR", 15),
    ("NR", 20),
    ("PR", 10),
    ("Q1", 5),
    ("Q2", 18),
    ("Q2", 19),
    ("WK1", 13),
    ("WK2", 15),
}


def _grams(text: str, n: int = 8) -> set[tuple[str, ...]]:
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
            excluded = set(H.cell_exclusions(h, iid))
            for pid, gs in sorted(per.items()):
                if pid in excluded:
                    continue
                own = [g for g in (prompt & gs) if shared[g] == 1]
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
FIXTURE_GAP_BACKLOG = {
    ("Q6", 8):  "gold: did not state each consequence being affected",
    ("Q6", 17): "gold: did not address your second antecedent ... or second consequence",
    # Both 1c cells below are graphs flattened into text, where the unassigned
    # run is chart FURNITURE, not an answer the fixture mislaid.
    ("1c", 9):  "the empty x and y are faithful: p9's chart carries tick values "
                "(2.5 2 1.5 1 0.5 0), day names and series names, but no axis "
                "TITLES. Gold's 6.0 is partial credit for exactly that",
    ("1c", 20): "the unassigned run is the student's WRITTEN DESCRIPTION of a "
                "graph they never drew (\"Title: ... X-axis label: ...\"), so "
                "the empty title/x/y are faithful to the paper. This cell is "
                "already declared unscoreable in cell_exclusions for the same "
                "reason: gold scored it 0, while on the web that description "
                "IS the answer",
}


# Items whose response is deliberately carried in more than one box, with why.
MULTI_BLOCK_DECLARED: dict[str, str] = {
    # Examined box by box in this session and confirmed against each response's
    # own structure. The web version presents these as separate input fields, so
    # the split is the form's, not an artefact of reconstruction.
    "Q6": "eight boxes: two antecedents, each with its change, consequence and "
          "effect. Every cell read out and corrected; all fixture checks clean",
    "Q3": "five boxes, one per SMART aspect, and the students label them "
          "themselves. Anchored on the aspect's own name where the scorer gave "
          "no quote; 9 cells with an empty box reduced to 1, and that one is "
          "correct — p9 never mentions realistic",
    "Q4b": "three boxes: the modify statement and two examples. p7 read out and "
           "assigned; the rest carry no findings",
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
                boxes = _span_boxes(iid, pid)
                if len(boxes) < 2 or not any(not v for v in boxes.values()):
                    continue               # no empty box: nothing to lose text to
                run, text = _longest_unassigned(raw, _norm(" ".join(boxes.values())))
                if run < 10:
                    continue
                if (iid, pid) in FIXTURE_GAP_BACKLOG:
                    seen.add((iid, pid))
                    continue
                empty = sorted(k for k, v in boxes.items() if not v)
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
    if hs:
        import json, os
        try:
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), hs)) as fh:
                own |= set(json.load(fh).get(str(pid), {}))
        except Exception:
            pass
    key = f"_{item_id.lower()}_"
    own |= {k for k in fx if key in k and "ref" not in k}

    def label(field):
        tail = field.split(key)[-1] if key in field else field
        return tail.rsplit("_", 1)[-1] if key not in field else tail

    out = {label(f): str(fx.get(f, "")).strip() for f in own if f in fx or True}
    out = {k: v for k, v in out.items() if k}
    _BOXES_MEMO[(item_id, pid)] = out
    return dict(out)



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
    for field in (spec.get("sim") or {}):
        tail = field.split(key)[-1] if key in field else field
        out.add(tail if key in field else tail.rsplit("_", 1)[-1])
    return out


def _span_boxes(item_id: str, pid: int) -> dict[str, str]:
    """`_fixture_boxes` minus the boxes that hold values instead of quotations."""
    drop = _value_derived(item_id)
    return {k: v for k, v in _fixture_boxes(item_id, pid).items() if k not in drop}


def _longest_unassigned(raw: str, boxes: str, n: int = 5) -> tuple[int, str]:
    """Longest run of response words appearing in no box, and that run."""
    rw, bw = raw.split(), boxes.split()
    have = {tuple(bw[i:i + n]) for i in range(len(bw) - n + 1)}
    cov = [False] * len(rw)
    for i in range(len(rw) - n + 1):
        if tuple(rw[i:i + n]) in have:
            for j in range(i, i + n):
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
CONSENSUS_OVERLAP_BACKLOG = {
    ("Q6", 6, "state_a1", "state_a2"):
        "p6 names the same antecedent in both boxes verbatim; gold charges the "
        "second as a mismatch and `cover` demotes it, which is the correct result",
    ("Q6", 6, "change_a1", "change_a2"):
        "the same sentence answers both, for the same reason",
}


def check_consensus_spans_are_disjoint() -> list[str]:
    """Do Q6's eight fixture boxes hold text belonging to DIFFERENT elements?

    `check_handsplit_rows_are_disjoint` enforces exactly this invariant — and
    only over the hand-split JSON files, which is Q4b alone. Q6's fixture comes
    from a frozen consensus table built from per-component evidence quotes the
    scorer chose INDEPENDENTLY, so nothing has ever required those eight spans
    to partition the response: not to be ordered, not to be disjoint, not to be
    complete. The coverage check now covers completeness; this covers the rest.

    ONE overlap is permitted and is not a defect. `state_cN` and `affect_cN`
    describe the same consequence — the box for "which consequence" and the box
    for "what becomes of it" are cut from one clause — and splitting them was
    measured as worse (Q6 fell 11/17 to 3/17 when an anchored split sliced those
    sentences into fragments). The same holds for `state_aN`/`change_aN`. Twenty
    such containments exist across fifteen cells and all are faithful.

    What is NOT permitted is one element's words appearing in another element's
    box: p10's `state_c2` is a substring of its `change_a1`, so one clause serves
    as both "how the first antecedent is changed" and "the second consequence" —
    and p10 carries `change_a1`'s only error in the item.
    """
    problems = []
    seen: set[tuple] = set()

    def norm(x):
        return " ".join((x or "").split()).lower()

    for _h, iid, pid, _raw, boxes in _fixture_cells():
        bx = {k: norm(v) for k, v in boxes.items() if v}
        keys = sorted(bx)
        for i, a in enumerate(keys):
            for b in keys[i + 1:]:
                # same element: "state_c1"/"affect_c1" -> both end "c1"
                if _siblings(a) == b or _siblings(b) == a:
                    continue
                if len(bx[a]) < 25 or len(bx[b]) < 25:
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
    ("Q3", 17, "realistic"):
        "\"... {{corpus:Q3/p17:realistic:40:83:sha=cac3674d624e}} do\" is a complete "
        "clause ending on a main verb; p17 writes the whole passage without "
        "sentence terminators, so the dangling-word test sees an auxiliary where "
        "there is none. The five aspects are each in their own labelled box",
    ("Q6", 2, "change_a1"):
        "\"... {{corpus:Q6/p2:change_a1:132:170:sha=21acf3047fe0}} to\" is a complete phrase "
        "that happens to close on a function word; extending it swallows the "
        "next sentence, which no box needs",
    ("Q6", 15, "state_a2"):
        "\"{{corpus:Q6/p15:state_a2:21:67:sha=7015ae7a2915}} me\" is a complete noun "
        "phrase; the words after it are the CHANGE clause and belong to change_a2",
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
            last = tail.rstrip(".,;:").split()[-1].lower() if tail.split() else ""
            if not inside and not finished and last in _DANGLING:
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
    """
    import re
    import warnings
    import handouts as H
    import segment as SEG

    cfg = H.config(1 if item.startswith("Q") else 3)
    subs = dict(H.find_submissions(cfg is not None and (1 if item.startswith("Q") else 3)))
    if pid not in subs:
        return f"p{pid}: no submission on this machine"
    raw = " ".join(_segment_as_scored(
        1 if item.startswith("Q") else 3, pid).get(item, "").split())
    if not raw:
        return f"{item}/p{pid}: empty response"

    out = [f"{'=' * 78}", f"{item} / p{pid}", "=" * 78, "", "RESPONSE:", ""]
    parts = re.split(r"(?=\b2\s*\))", raw)
    for i, part in enumerate(parts, 1):
        if len(parts) > 1:
            out.append(f"  PART {i}")
        for sent in [x.strip() for x in re.split(r"(?<=[.!?])\s+", part) if x.strip()]:
            out.append(f"    @{raw.find(sent):<4} {sent}")
    out += ["", "-" * 78, "", "BOXES, in document order:", ""]

    boxes = _fixture_boxes(item, pid)
    low = raw.lower()
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

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        flags = [f for f in (check_fixture_follows_response_structure()
                             + check_consensus_spans_are_disjoint()
                             + check_fixture_covers_the_response())
                 if f"/p{pid}:" in f or f"/p{pid} " in f]
    out.append("AUDIT FLAGS: " + (f"{len(flags)}" if flags else "none"))
    out += [f"  - {f.split(' — ')[0]}" for f in flags]
    return "\n".join(out)


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
