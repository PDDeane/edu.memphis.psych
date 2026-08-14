#!/usr/bin/env python3
"""Audit how far the lo-blocks web prompts diverge from the CLI scorer's.

The two systems are meant to run the SAME rubric so their performance can be
compared. This reports, per item, how much of what score.py sends actually
appears in the corresponding <LLMAction> prompt.

    python3 equivalence.py            # summary table
    python3 equivalence.py --item Q4a # what is missing from one item
    python3 equivalence.py --cli Q4a  # print the CLI prompt itself

Presence is tested verbatim, on each element's opening words. Where the web
paraphrases, the meaning may be present while the text is not — so this
measures STRUCTURAL equivalence, which is the thing that has to hold before a
performance comparison means anything.

An element the web deliberately does not carry is not a gap: `olx_prompts.py`
declares those, with a reason each, and they are counted separately here as
`omit`. Anything that is neither present nor declared IS a gap.
"""
from __future__ import annotations
import argparse, re, sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from score import build_prompt, SYSTEM_TMPL
from handouts import config
from olx_prompts import primitives as _primitives
O_PRIM = _primitives()
from olx_prompts import (ACTION, HANDOUT, OLX, OMIT_CREDIT, OMIT_DEDUCTION,
                         SCORING_DIVERGENCES, parse_slots, resolve_guidance_omissions,
                         _slots_attr, _ACTION_RE, SHEET_ONLY, sheet_id, _sheet_tag)
import enforcement as ENF
import paths

def norm(t): return " ".join(str(t).split()).lower()
def frag(t, n=9): return " ".join(norm(t).split()[:n])

def web_prompt(handout, aid):
    src = open(OLX % handout).read()
    m = re.search(r'<LLMAction\b[^>]*?\bid="%s".*?</LLMAction>' % re.escape(aid), src, re.S)
    return norm(re.sub(r'<Ref\b[^>]*/>', '', m.group(0))) if m else ""

def audit(item):
    h = HANDOUT[item]
    rub = config(h)["rubric"].BY_ID[item]
    w = web_prompt(h, ACTION[item])
    oc, od = OMIT_CREDIT.get(item, {}), OMIT_DEDUCTION.get(item, {})
    og = resolve_guidance_omissions(item, rub["guidance"])
    # An item judged from the criteria sheet has no credit list in the prompt —
    # build_prompt sends the criteria instead, and so does the web. Test that.
    criteria = bool(rub.get("derive_from_criteria"))
    return {
        "question":  frag(rub["question"]) in w,
        "criteria":  None if not criteria else
                     frag("Operant conditioning means: the future probability of a "
                          "VOLUNTARY BEHAVIOUR", 9) in w,
        "credit":    [] if criteria else
                     [c["what"] for c in rub["credit"]
                      if c["what"] not in oc and frag(c["desc"], 5) not in w],
        "deductions":[d["code"] for d in rub["deductions"]
                      if d["code"] not in od and frag(d["text"], 7) not in w],
        "guidance":  [i for i, g in enumerate(rub["guidance"])
                      if i not in og and frag(g, 9) not in w],
        "exemplars": [e["label"] for e in (rub.get("exemplars") or [])
                      if frag(e["response"], 8) not in w],
        "omitted":   dict(credit=oc, deductions=od, guidance=og),
        "totals": dict(credit=0 if criteria else len(rub["credit"]) - len(oc),
                       deductions=len(rub["deductions"]) - len(od),
                       guidance=len(rub["guidance"]) - len(og),
                       exemplars=len(rub.get("exemplars") or [])),
    }

def parse_onlyif_attr(handout, action):
    """The sheet's `onlyif` rules, for items that declare charge-once."""
    from olx_prompts import _sheet_tag
    m = re.search(r'\bonlyif="([^"]*)"', _sheet_tag(handout, action))
    out = []
    for entry in (m.group(1) if m else "").split("|"):
        key, _, cond = entry.strip().partition(":")
        if key.strip() and cond.strip():
            out.append({"key": key.strip(), "cond": cond.strip()})
    return out


def subset_sums(values):
    """Every loss the scored checks can add up to."""
    out = {0.0}
    for v in values:
        out |= {round(s + v, 4) for s in out}
    return out


def scoring_audit():
    """Can the web sheet produce the same score as the CLI ledger?

    Mechanical only: item totals, and whether each deduction's cost is reachable
    at all. It cannot tell whether the RIGHT check fires — that is what the
    declared list in olx_prompts.SCORING_DIVERGENCES is for. Clean output means
    "nothing has drifted since that list was written", not "the two agree".
    """
    declared = {}
    for d in SCORING_DIVERGENCES:
        for it in d["items"]:
            declared.setdefault(it, []).append(d)

    findings = []
    for item in {**ACTION, **SHEET_ONLY}:
        action = sheet_id(item)
        h = HANDOUT[item]
        rub = config(h)["rubric"].BY_ID[item]
        slots = parse_slots(*_slots_attr(h, action))
        scored = [s for s in slots if s["pts"] is not None]
        gates = [s["key"] for s in slots if s["gates"]]

        tag = _sheet_tag(h, action)
        mx = re.search(r'\bmax="([^"]*)"', tag)
        web_max = float(mx.group(1)) if mx else sum(s["pts"] for s in scored)
        reachable = subset_sums([s["pts"] for s in scored])
        # Can the item be zeroed at all? Either a gate fails, or every scored
        # check fails. A whole-item CLI code needs that, not a cost match: the
        # two totals can differ (1c) while both still mean "no marks".
        # "Every check fails" does NOT mean every cost applies: a slot suppressed by
        # `onlyif` contributes nothing once its condition has failed. Q4b reaches 0
        # at 1.5+1.5+2 with `modify_why` subsumed, which the naive sum reads as 6.
        onlyif = parse_onlyif_attr(h, action)
        suppressed = {r["key"] for r in onlyif}
        worst = sum(s["pts"] for s in scored if s["key"] not in suppressed)
        can_zero = bool(gates) or abs(worst - web_max) < 1e-9

        if abs(web_max - rub["max"]) > 1e-9:
            findings.append((item, "TOTAL", f"web {web_max:g} vs CLI {rub['max']:g}"))
        for d in rub["deductions"]:
            if d["code"] in OMIT_DEDUCTION.get(item, {}):
                continue
            whole = abs(d["pts"] - rub["max"]) < 1e-9
            if whole and not can_zero:
                findings.append((item, "CANNOT ZERO",
                                 f"{d['code']} (-{d['pts']:g}) takes the whole item, "
                                 f"but no gate and no all-checks-fail path reaches 0"))
            elif not whole and round(d["pts"], 4) not in reachable:
                findings.append((item, "UNREACHABLE COST",
                                 f"{d['code']} (-{d['pts']:g}) — no combination of "
                                 f"checks costs that"))
        costs = {round(d["pts"], 4) for d in rub["deductions"]}
        for s in scored:
            if round(s["pts"], 4) not in costs and abs(s["pts"] - rub["max"]) > 1e-9:
                findings.append((item, "COST WITH NO CODE",
                                 f"`{s['key']}` @{s['pts']:g} matches no deduction"))
    return findings, declared


def print_scoring():
    findings, declared = scoring_audit()
    print("DECLARED scoring divergences (olx_prompts.SCORING_DIVERGENCES)\n")
    for d in SCORING_DIVERGENCES:
        tag = "forced   " if d["necessary"] else "FIXABLE  "
        print(f"  {tag} {','.join(d['items']):<18} {d['what']}")
        for line in re.findall(r".{1,72}(?:\s|$)", d["why"]):
            print(f"             {line.strip()}")
        print()
    n_fix = sum(1 for d in SCORING_DIVERGENCES if not d["necessary"])
    print(f"  {len(SCORING_DIVERGENCES)} declared, {n_fix} of them fixable "
          f"(each is a scoring change — measure it on its own).\n")

    print("MECHANICAL check — item totals and reachable costs\n")
    undeclared = [f for f in findings if f[0] not in declared]
    for item, kind, detail in findings:
        mark = "  " if item in declared else "! "
        print(f"{mark}{item:<5} {kind:<18} {detail}")
    if not findings:
        print("  nothing flagged")
    print(f"\n{len(undeclared)} flagged item(s) with no declared divergence.")
    return 1 if undeclared else 0


LO = str(paths.lo_root())
PROBE = paths.PROBE


def _web_attrs(item):
    """The sheet attributes as shipped, straight out of the .olx."""
    h = HANDOUT[item]
    tag = _sheet_tag(h, sheet_id(item))
    get = lambda a: (re.search(r'\b%s="([^"]*)"' % a, tag) or [None, ""])[1] \
        if re.search(r'\b%s="([^"]*)"' % a, tag) else ""
    mx = re.search(r'\bmax="([^"]*)"', tag)
    return {"item": item, "slots": get("slots"), "verdicts": get("verdicts"),
            "cover": get("cover"), "equals": get("equals"), "onlyif": get("onlyif"),
            "derived": get("derived"), "counts": get("counts"),
            # Forwarded like every other primitive: without them the probe sees a
            # `pick` slot with no set to draw from, answers nothing, and reports
            # the sheet's all-satisfied baseline as zero.
            "choices": get("choices"), "expect": get("expect"),
            **({"max": float(mx.group(1))} if mx else {})}


# Every attribute an <LLMAction> may carry. The enforcement ones are forwarded to
# the probe; this list exists so that ADDING a primitive cannot quietly leave the
# audit blind to it — an unlisted attribute is a finding, which is what `derived`
# should have been on the day it landed.
# Derived from the shared registry, so a new primitive cannot be invisible here.
KNOWN_ACTION_ATTRS = set(O_PRIM["sheetAttributes"]) | {
    p["attr"] for p in O_PRIM["primitives"]}


def uncovered_cli_items():
    """CLI items the web scores nowhere.

    Both misses so far came from treating the web's ITEM SET as fixed: the audits
    verified that the items they knew about agreed, and nothing verified that they
    knew about every item. 1b was scored on the CLI and nowhere here for as long
    as it existed, and so were T1/T2. This is the check that fails instead.
    """
    covered = {**ACTION, **SHEET_ONLY}
    out = []
    for h in (1, 2, 3):
        for it in config(h)["rubric"].ITEMS:
            if it["id"] not in covered:
                out.append((it["id"], h, it["max"], it["label"]))
    return out


def unmeasured_items():
    """Items the web SCORES but the harness never drives, and the reverse.

    The third instance of one blind spot. The audits checked that the items they
    knew about agreed (`--prompts`, `--scoring`, `--enforcement`), then that the
    web scored every CLI item (`uncovered_cli_items`) — and still nothing checked
    that every scored item is ever MEASURED. An item can be graded correctly on
    screen and contribute to no number at all, which is what 1b and T1/T2 were.

    `JOBS` is imported here rather than at module scope: agreement_app pulls in
    the reconstruction and the gold readers, and none of that is needed unless
    this audit runs.
    """
    from agreement_app import JOBS

    scored = set({**ACTION, **SHEET_ONLY})
    return sorted(scored - set(JOBS)), sorted(set(JOBS) - scored)


SLOTSHEET_TS = str(paths.SLOTSHEET_TS)


def schema_divergences():
    """Does the CLI's response SCHEMA match the one the web sends?

    The blind spot this closes. `--prompts` compares prompt TEXT and `--scoring`
    compares arithmetic; a JSON schema is neither, so nothing compared it — and
    the schema is instruction too. agreement.build_schema calls itself "a mirror
    of buildSlotSchema()" and has drifted from it twice. The first time it was
    missing the `exclude` argument, so the model was asked for keys the prompt
    told it not to answer, which cost two cells on 2a. The second was found while
    measuring Q2's `wgb_is_counterpart`: the web's `evidence` field carries
    description "Quote from the student, or what you looked for and did not find"
    and this side's carried none, so for a check whose right answer is "not
    there", one side offered absence somewhere to be justified and the other did
    not. The web fired that gate on p7 in 2 published runs of 2; the CLI in 1 of 8.

    Compared against the TypeScript SOURCE rather than a copy kept here, because
    a copy is the thing that drifts. Structural facts only — property names, the
    required list, additionalProperties, the description literals, and that
    `checks` precedes `feedback` (declared in that order on purpose, so verdicts
    are reached before the prose that would rationalise them).
    """
    import re as _re
    from agreement import BLOCKS, build_schema, load_action

    try:
        ts = open(SLOTSHEET_TS).read()
    except OSError as e:
        return [f"cannot read {SLOTSHEET_TS}: {e}"]
    m = _re.search(r"export function buildSlotSchema\b.*?\n}\n", ts, _re.S)
    if not m:
        return ["buildSlotSchema() not found in slotSheet.ts — this audit is stale"]
    body = m.group(0)

    problems = []

    # (a) the per-slot property names, in order. Scoped to the slot-object literal
    # — `properties[slot.key] = { ... }` — because a body-wide scan picks up the
    # TOP-level keys instead and reports a phantom mismatch. It did.
    slot_obj = _re.search(r"properties\[slot\.key\] = \{(.*?)\n {4}\};", body, _re.S)
    # Anchored on "name followed by an object literal" rather than on an exact
    # indent: a property added inside a conditional spread (`...(cond ? { note:
    # {...} } : {})`) sits two spaces deeper and an indent-anchored scan silently
    # does not see it — which is indistinguishable from the mirror being right.
    # Requiring `{` is what makes the looser indent safe: `type`, `enum` and
    # `description` are never followed by one.
    def _props_block(lit):
        """The text of the slot literal's own `properties: { ... }`.

        Brace-matched rather than indent-matched: the names inside sit at
        whatever depth a conditional spread puts them, and two of them —
        `count` and `verdict` — are written mid-line inside a ternary, where a
        line-anchored scan cannot see them at all. It could not, which is why
        the audit believed a judgement slot's `verdict` was undeclared.
        """
        at = lit.find("properties: {")
        if at < 0:
            return ""
        i = lit.index("{", at)
        depth = 0
        for j in range(i, len(lit)):
            if lit[j] == "{":
                depth += 1
            elif lit[j] == "}":
                depth -= 1
                if depth == 0:
                    return lit[i + 1:j]
        return lit[i + 1:]

    _lit = slot_obj.group(1) if slot_obj else ""
    _block = _props_block(_lit)
    # A nested key is never followed by `{` — `type`, `enum`, `minimum` and
    # `description` all take scalars — so this names exactly the properties.
    _spans = [(m.group(1), m.start()) for m in _re.finditer(r"(\w+):\s*\{", _block)]
    want_props = [n for n, _ in _spans]
    # Where each declared property's own text begins and ends, so a description
    # can be checked against the property it belongs to. The audit used to
    # compare ONE representative slot against a flat list of every name in the
    # literal, which was sound only while every slot had the same shape. It no
    # longer does: a count answers `count`, a pick answers only `refers_to`, a
    # judgement answers `verdict`. The flat comparison then demanded that a
    # plain judgement carry the description of a field it must not have.
    want_prop_descs = {}
    for i, (name, at) in enumerate(_spans):
        end = _spans[i + 1][1] if i + 1 < len(_spans) else len(_block)
        seg = _block[at:end]
        d = seg.find("description:")
        if d < 0:
            continue
        # Each maximal run of adjacent '...' + '...' literals after the
        # `description:`. A ternary yields one run per arm — alternatives, so
        # carrying either satisfies the check.
        want_prop_descs[name] = [
            " ".join("".join(_re.findall(r"'((?:[^'\\]|\\.)*)'", run.group(0))).split())
            for run in _re.finditer(
                r"(?:'(?:[^'\\]|\\.)*'\s*\+\s*)*'(?:[^'\\]|\\.)*'",
                _re.sub(r"//[^\n]*", "", seg[d:]))
        ]
    # (b) the description literals, located rather than collected. Scoped by level
    # so a description can be checked WHERE it belongs: a bag-of-descriptions
    # comparison passes when one slot loses its own and a sibling still has it,
    # which the selftest below caught it doing.
    def _lits(text):
        """Each description, with a concatenation joined as the model receives it.

        A TS description written as several '...' + '...' segments reaches the
        provider as one string. Capturing only the first segment compares a
        prefix against the whole and reports a difference that is not there —
        and would equally MISS a real one anywhere past the first segment.
        """
        out = []
        for m in _re.finditer(r"description:\s*\n?\s*((?:'(?:[^'\\]|\\.)*'\s*\+?\s*)+)", text):
            parts = _re.findall(r"'((?:[^'\\]|\\.)*)'", m.group(1))
            out.append(" ".join("".join(parts).split()))
        return out
    want_slot_descs = _lits(slot_obj.group(1)) if slot_obj else []
    want_top_descs = [d for d in _lits(body) if d not in want_slot_descs]
    # (c) required + additionalProperties. Scoped to the slot object for the same
    # reason (a) is: a body-wide search takes the first `required: [` in the
    # function, which is the TOP-level one the moment the slot's stops being a
    # bare literal. It did — a ternary on perCheckNotes made this report the slot
    # list as ['checks', 'feedback'], a phantom exactly like the one the comment
    # above describes.
    # `required` is built from conditionals on the slot's kind, so there is no
    # literal list to lift. What matters is the rule a strict provider enforces
    # and the one that actually broke — every key in `properties` is required,
    # and nothing else is — so check THAT, on every slot, rather than scraping a
    # ternary's source text and reporting a fragment of it as the expectation.
    want_addl = "additionalProperties: false" in body
    # (d) top-level ordering
    want_checks_first = body.find("checks:") < body.find("feedback:") \
        if "feedback:" in body else True

    # EVERY sheet, not a representative one. That shortcut was justified by
    # "build_schema treats every slot the same way", which stopped being true
    # the moment a slot's shape depended on its kind: one sheet of plain
    # judgements cannot show that picks and counts are built right, or built at
    # all. Reachability below is judged over the union for the same reason.
    sheets = {}
    for handout in BLOCKS.values():
        for aid, spec in handout.items():
            if not spec.get("olx"):
                continue
            act = load_action(spec["olx"], aid)
            # Built the way the RUNTIME builds it for this item: per-check notes
            # are keyed off showChecks, so comparing the no-notes schema against
            # a source that has them reports a difference the app never sends.
            sheets[aid] = build_schema(act["slots"], act["excluded"],
                                       act["show_checks"], act["cover"],
                                       act["choices"])
    got = next(iter(sheets.values()))
    checks = {f"{aid}/{k}": v
              for aid, sch in sheets.items()
              for k, v in sch["properties"]["checks"]["properties"].items()}

    for key, one in checks.items():
        got_props = list(one["properties"])
        stray = [p for p in got_props if p not in want_props]
        if stray:
            problems.append(f"slot `{key}` sends {stray}, which buildSlotSchema "
                            f"never declares")
            break
        if set(one.get("required", [])) != set(got_props):
            problems.append(f"slot `{key}`: required {sorted(one.get('required', []))} "
                            f"!= properties {sorted(got_props)} — a strict provider "
                            f"rejects the whole request")
            break
        if want_addl and one.get("additionalProperties") is not False:
            problems.append(f"web sets additionalProperties: false; cli does not "
                            f"on slot `{key}`")
            break
    # Every property the web declares has to be reachable SOMEWHERE, or the cli
    # has quietly stopped building a whole kind of check — which is exactly what
    # had happened: `pick` and `count` slots were dropped by the slot parser, so
    # neither `refers_to` nor `count` appeared on any slot at all.
    reachable = {p for one in checks.values() for p in one["properties"]}
    unreached = [p for p in want_props if p not in reachable]
    if unreached:
        problems.append(f"no slot on ANY audited sheet carries {unreached}, which the "
                        f"web declares — a whole slot kind is being dropped. This is "
                        f"how sixteen `pick` and nine `count` slots went missing.")
    def _here(obj):
        """Descriptions on THIS object's immediate properties."""
        return [" ".join(v["description"].split())
                for v in (obj.get("properties") or {}).values()
                if isinstance(v, dict) and isinstance(v.get("description"), str)]

    # EVERY slot, not a representative one: the failure this replaced was a
    # description present on some slots and absent on others.
    for key, slot_schema in checks.items():
        miss = []
        for name, prop in (slot_schema.get("properties") or {}).items():
            arms = want_prop_descs.get(name) or []
            if not arms:
                continue
            got_d = " ".join(str(prop.get("description") or "").split())
            if got_d not in arms:
                miss.append(f"{name}: {got_d or '(none)'!r} is not one of "
                            + " | ".join(repr(a) for a in arms))
        if miss:
            problems.append(f"slot `{key}` describes fields differently from the "
                            f"web: " + "; ".join(miss))
            break                      # one report is enough; they share a builder
    miss_top = [d for d in want_top_descs if d not in _here(got)]
    if miss_top:
        problems.append("top-level description(s) the web sends and the cli does not: "
                        + "; ".join(repr(d) for d in miss_top))
    got_order = list(got["properties"])
    if want_checks_first and got_order[:1] != ["checks"]:
        problems.append(f"web declares checks before feedback; cli order is {got_order}")
    return problems


def unknown_action_attrs():
    """Attributes on any graded <LLMAction> that this audit does not know about."""
    out = []
    for item in sorted({**ACTION, **SHEET_ONLY}):
        tag = _sheet_tag(HANDOUT[item], sheet_id(item))
        for name in re.findall(r'\b([A-Za-z_][\w-]*)="', tag):
            if name not in KNOWN_ACTION_ATTRS:
                out.append((item, name))
    return out


def web_signatures(items):
    """Drive probe.test.ts and return what each web sheet enforces."""
    import json, os, subprocess, tempfile
    d = tempfile.mkdtemp(prefix="probe_")
    pin, pout = os.path.join(d, "in.json"), os.path.join(d, "out.json")
    with open(pin, "w") as fh:
        json.dump([_web_attrs(i) for i in items], fh)
    env = {**os.environ, "RUN_SLOT_PROBE": "1", "PROBE_JSON": pin, "PROBE_OUT": pout}
    proc = subprocess.run(["npx", "vitest", "run", "--reporter=dot", PROBE],
                          cwd=LO, env=env, capture_output=True, text=True)
    if not os.path.exists(pout):
        sys.stderr.write(proc.stdout[-3000:] + proc.stderr[-2000:])
        raise SystemExit("probe.test.ts produced no output")
    return {r["item"]: r for r in json.load(open(pout))}


def enforcement_audit():
    """Do the two sides enforce the same rules? Probed, not mirrored.

    Only items whose score BOTH sides derive from checks are compared. For a
    plain-path CLI item the model authors the deduction ledger itself, so there
    is no check arithmetic to compare against the web sheet's — that difference
    is the slot-sheet design, stated once below rather than flagged 16 times.
    """
    cli = ENF.cli_signatures()
    # Every item is probed now, not just the ones the CLI derives. What differs is
    # what the web's answers are compared AGAINST: for a derive-path item, the
    # CLI's own probed behaviour; for a plain-path item, the CLI's rubric, because
    # there the model authors the ledger and there is no arithmetic to probe.
    # Leaving the other 16 uncompared meant a web-only enforcement rule on any of
    # them was invisible — which is how D1/D2's `equals` sat undeclared.
    allitems = sorted({**ACTION, **SHEET_ONLY})
    web = web_signatures(allitems)
    # A difference that is DECLARED is not drift. Same contract as --scoring: the
    # audit's job is to notice anything that is neither absent nor written down.
    declared = {it for d in SCORING_DIVERGENCES for it in d["items"]}
    # Declarations that state a checkable fact are checked. A stale exemption is
    # worse than none: it silences the audit for a difference that has moved.
    must_compute: dict[str, list[str]] = {}
    for d in SCORING_DIVERGENCES:
        for it, keys in (d.get("web_computes") or {}).items():
            must_compute.setdefault(it, []).extend(keys)
    findings = []

    for bad in ENF.check_criteria_table_is_complete(ENF.all_derive_items()):
        findings.append(("-", "PROBE TABLE STALE", bad))
    for bad in ENF.check_slot_codes_exist(ENF.all_items()):
        findings.append(("-", "RUBRIC REFERENCE BROKEN", bad))
    for bad in ENF.check_codes_reachable(ENF.all_items()):
        findings.append(("-", "CODE UNREACHABLE", bad))
    for bad in ENF.check_countable_families_converted(ENF.all_items()):
        findings.append(("-", "PRIMITIVE APPLIED UNEVENLY", bad))
    for bad in ENF.check_primitive_conformance():
        findings.append(("-", "PRIMITIVE NOT HONOURED", bad))
    for bad in ENF.check_harness_schema_conformance():
        findings.append(("-", "HARNESS SCHEMA DIVERGES", bad))
    for bad in ENF.check_derived_fields_resolve():
        findings.append(("-", "DERIVED FIELD UNREADABLE", bad))
    for iid, h, mx, label in uncovered_cli_items():
        findings.append((iid, "SCORED ON CLI ONLY",
                         f"H{h} {label} is worth {mx:g} on the CLI and is scored by "
                         f"nothing on the web"))
    never, orphan = unmeasured_items()
    for iid in never:
        findings.append((iid, "NEVER MEASURED",
                         "the web scores this item, but it is not in "
                         "agreement_app.JOBS, so no run ever reports it"))
    for iid in orphan:
        findings.append((iid, "MEASURED, NOT SCORED",
                         "agreement_app.JOBS drives this item, but nothing on the "
                         "web scores it — the run can only report a blank"))
    for item, name in unknown_action_attrs():
        findings.append((item, "UNKNOWN ATTRIBUTE",
                         f'`{name}="..."` is not in KNOWN_ACTION_ATTRS — if it '
                         f"changes enforcement, the audit is blind to it"))

    for item in allitems:
        w = web.get(item)
        if w is None:
            findings.append((item, "NO WEB SHEET", "item not probed"))
            continue
        rub = config(HANDOUT[item])["rubric"].BY_ID[item]

        if item not in cli:
            # PLAIN-PATH item. The CLI's ledger is model-authored, so each web
            # enforcement rule is checked against the rubric it must come from.
            whole = [d["code"] for d in rub["deductions"]
                     if abs(d["pts"] - rub["max"]) < 1e-9]
            for g in w["declaredGates"]:
                if not whole:
                    findings.append((item, "GATE NOT IN RUBRIC",
                                     f"`{g}` zeroes the item, but no CLI deduction "
                                     f"costs the whole {rub['max']:g}"))
            # A computed check has no plain-path counterpart at all: the CLI asks
            # the model. Each one must be named in a divergence's `web_computes`,
            # so the exemption is per-key and verifiable rather than a blanket
            # pass for the item.
            for k in w["computed"]:
                if k not in must_compute.get(item, []):
                    findings.append((item, "COMPUTED, UNDECLARED",
                                     f"the web derives `{k}`; the CLI asks the model, "
                                     f"and no divergence declares it"))
            for kind, rules in (("cover", w["cover"]), ("onlyif", w["chargeOnce"])):
                if rules and item not in declared:
                    findings.append((item, "WEB-ONLY MECHANISM",
                                     f"`{kind}` enforces something the CLI's "
                                     f"model-authored ledger cannot express"))
            continue

        c = cli[item]
        if not c["baseline_is_full"]:
            findings.append((item, "CLI BASELINE", "all-pass analysis is not full marks"))
        wkeys = {s["key"] for s in w["scored"]} | set(w["singleLoss"])
        for k in must_compute.get(item, []):
            if k not in w["computed"]:
                findings.append((item, "DECLARATION STALE",
                                 f"a divergence says the web computes `{k}`, but it is "
                                 f"asked of the model"))

        # 1. cover — data on both sides, so compared exactly.
        if c["cover"] != w["cover"]:
            findings.append((item, "COVER DIFFERS",
                             f"CLI {c['cover'] or 'none'} vs web {w['cover'] or 'none'}"))

        # 1b. the vocabulary a grouped slot accepts.
        #
        #     The CLI puts the whole thing in one field: `first`, `second`,
        #     `neither`, `absent`. The web now SPLITS it — `verdict` says whether
        #     a thing was named at all, `refers_to` says which of the list it is
        #     — so a value-for-value comparison of the verdict options reports a
        #     difference on every grouped slot and means nothing.
        #
        #     What still has to hold is that the web can express every
        #     distinction the CLI draws, so the CLI's vocabulary is mapped onto
        #     the split and required to be covered: `neither` is `refers_to:
        #     none`, `absent` is `verdict: absent`, and the rest are cover
        #     labels. A web slot that dropped one of them still fails here.
        wopts = {s["key"]: s["options"] for s in w["scored"] if "options" in s}
        wlabels = {}
        for grp in (w["cover"] or []):
            for k in grp.get("keys", []):
                wlabels[k] = list(grp.get("labels", []))
        for k, vocab in (c.get("cover_vocab") or {}).items():
            got = wopts.get(k)
            if got is None:
                continue
            expressible = set(got) | set(wlabels.get(k, [])) | ({"none"} if k in wlabels else set())
            missing = [v for v in vocab
                       if ("none" if v == "neither" else v) not in expressible]
            if missing:
                findings.append((item, "COVER VOCAB DIFFERS",
                                 f"`{k}`: CLI {vocab} — the web cannot express {missing} "
                                 f"(verdict {list(got)}, refers_to {wlabels.get(k, [])})"))

        # 2. computed — a check the web derives must not be a CLI model input.
        # Guarded PER KEY, not per item: an item-level exemption would silence this
        # for any future computed check on the same item, which is the blanket pass
        # the plain-path branch was already careful to avoid.
        for k in w["computed"]:
            if k in c["inputs"] and k not in must_compute.get(item, []):
                findings.append((item, "ASKED ON CLI ONLY",
                                 f"web computes `{k}`; the CLI still asks the model"))
        # The mirror. Without it, moving a check into CLI code and leaving the web
        # asking for it looked clean — which is what Q1's count derivation did.
        wasked = {s["key"] for s in w["scored"]} - set(w["computed"])
        for k in c.get("derived_keys") or []:
            if k in wasked and k not in must_compute.get(item, []):
                findings.append((item, "ASKED ON WEB ONLY",
                                 f"the CLI derives `{k}`; the web still asks the model"))

        # 3. gates, mapped through the vocabulary bridge.
        for k in c["gates"]:
            wk = ENF.web_name(k, wkeys)
            if wk is None:
                findings.append((item, "UNMAPPED KEY", f"CLI gate `{k}` has no web counterpart"))
            elif wk not in w["gates"]:
                findings.append((item, "GATE CLI ONLY",
                                 f"`{k}` zeroes the item on the CLI, not on the web (as `{wk}`)"))
        cli_gate_web_names = {ENF.web_name(k, wkeys) for k in c["gates"]}
        for wk in w["gates"]:
            if wk not in cli_gate_web_names and wk not in w["computed"]:
                findings.append((item, "GATE WEB ONLY",
                                 f"`{wk}` zeroes the item on the web, not on the CLI"))

        # 4a. `equals` where BOTH sides declare it as data — compared exactly, the
        #     way `cover` is. Only the credit path does; the criteria path keeps its
        #     comparison in Python, so there it is still inferred below.
        if c.get("equals"):
            if c["equals"] != w["equals"]:
                findings.append((item, "EQUALS DIFFERS",
                                 f"CLI {c['equals']} vs web {w['equals']}"))

        # 4b. charge-once. On the web the same fact is declared either as `onlyif`
        #     (two independent findings, billed once) or as `equals` (two inputs
        #     that jointly settle one charge); both present as one sublinear pair.
        #     A computed check that GATES is excluded: flipping either operand then
        #     costs the whole item, so the pair is not sublinear on either side and
        #     comparing it as charge-once compares nothing.
        gating = {s["key"] for s in w["scored"] if s.get("gates")} | set(w["declaredGates"])
        web_pairs = {frozenset(p) for p in w["chargeOnce"]}
        web_pairs |= {frozenset(e["operands"]) for e in w["equals"]
                      if e["key"] not in gating and not c.get("equals")}
        for a, b in c["charge_once"]:
            wa, wb = ENF.web_name(a, wkeys), ENF.web_name(b, wkeys)
            if wa is None or wb is None:
                findings.append((item, "UNMAPPED KEY",
                                 f"charge-once pair ({a}, {b}) has no web counterpart"))
            elif frozenset((wa, wb)) not in web_pairs:
                findings.append((item, "CHARGE-ONCE CLI ONLY",
                                 f"({a}, {b}) cost less together on the CLI; the web "
                                 f"charges `{wa}` and `{wb}` in full"))
        cli_pairs = {frozenset(x for x in (ENF.web_name(a, wkeys), ENF.web_name(b, wkeys)) if x)
                     for a, b in c["charge_once"]}
        for wp in web_pairs:
            if wp not in cli_pairs:
                findings.append((item, "CHARGE-ONCE WEB ONLY",
                                 f"({', '.join(sorted(wp))}) cost less together on the web"))
    return findings, cli, web


def uncompared_web_rules():
    """Web enforcement on items the CLI scores by a model-authored ledger.

    These ARE audited — each rule is checked against the rubric it has to come
    from, and each computed check against a divergence that names it — but not
    against CLI behaviour, because a model-authored ledger has none to probe.
    Listed so the weaker basis is visible rather than implied.
    """
    out = []
    for item in sorted({**ACTION, **SHEET_ONLY}):
        h = HANDOUT[item]
        rub = config(h)["rubric"].BY_ID[item]
        if rub.get("derive_from_credit") or rub.get("derive_from_criteria"):
            continue
        a = _web_attrs(item)
        for kind in ("cover", "equals", "onlyif", "derived"):
            if a.get(kind):
                out.append((item, kind, a[kind]))
    return out


def enforcement_selftest():
    """Break each rule on purpose and confirm the audit says so.

    A guard that has never failed is not known to work. These are the three
    shapes that have actually gone wrong: Q6's coverage missing on the CLI (found
    by hand, months late), and the two Handout 2 rules the web moved into the
    grader.
    """
    import rubric_h1, rubric_h2
    cases = []

    saved = rubric_h1.BY_ID["Q6"].pop("cover")
    cases.append(("CLI Q6 loses `cover`", "COVER DIFFERS", "Q6",
                  [f for f in enforcement_audit()[0]]))
    rubric_h1.BY_ID["Q6"]["cover"] = saved

    g = rubric_h1.BY_ID["Q6"]["cover"][0]
    vsaved = g["verdicts"]
    g["verdicts"] = [*g["labels"], "neither", "blank"]      # the web says `absent`
    cases.append(("CLI Q6 vocab drifts", "COVER VOCAB DIFFERS", "Q6",
                  [f for f in enforcement_audit()[0]]))
    g["verdicts"] = vsaved

    # The coverage guard. Both misses so far were items the audits did not know
    # existed, so this one is checked by removing an item from the covered set.
    tsaved = SHEET_ONLY.pop("T1")
    cases.append(("an item leaves the covered set", "SCORED ON CLI ONLY", "T1",
                  [f for f in enforcement_audit()[0]]))
    SHEET_ONLY["T1"] = tsaved

    # The equals comparison, now that both sides declare it on the credit path.
    d1 = rubric_h2.BY_ID["D1"]
    esaved = d1["equals"]
    d1["equals"] = [{**esaved[0], "lenient": []}]
    cases.append(("CLI D1 equals loses `unclear`", "EQUALS DIFFERS", "D1",
                  [f for f in enforcement_audit()[0]]))
    d1["equals"] = esaved

    # The all-items guard: a web-only enforcement rule on a plain-path item was
    # invisible until the audit covered those too.
    # Both branches of the computed-check guard: T1 is plain-path (the rule has no
    # CLI counterpart at all), 1b is derive-path (the CLI asks for it).
    import olx_prompts as _op
    # The derive-path branch: the CLI asks for what the web computes.
    for d in _op.SCORING_DIVERGENCES:
        if "1b" in (d.get("web_computes") or {}):
            wsaved = d.pop("web_computes")
            cases.append(("1b computed check loses its declaration",
                          "ASKED ON CLI ONLY", "1b",
                          [f for f in enforcement_audit()[0]]))
            d["web_computes"] = wsaved
            break
    # The plain-path branch. No live item exercises it now that T1/T2 and 1b are
    # derived, so one is injected onto a plain item — the guard has to stay tested
    # even while nothing happens to trip it.
    plain = next((i for i in sorted({**ACTION, **SHEET_ONLY})
                  if not config(HANDOUT[i])["rubric"].BY_ID[i].get("derive_from_credit")
                  and not config(HANDOUT[i])["rubric"].BY_ID[i].get("derive_from_criteria")),
                 None)
    _orig = globals()["_web_attrs"]

    if plain is not None:
        def _inject(i, _p=plain):
            a = _orig(i)
            if i == _p:
                key = parse_slots(*_slots_attr(HANDOUT[i], sheet_id(i)))[0]["key"]
                a["derived"] = f"{key}:present:some_field"
            return a
        globals()["_web_attrs"] = _inject
        cases.append((f"a computed check appears on {plain} undeclared",
                      "COMPUTED, UNDECLARED", plain,
                      [f for f in enforcement_audit()[0]]))
        globals()["_web_attrs"] = _orig

    # The conformance guard: the two bugs that actually shipped were the prompt
    # generator not knowing about a primitive, so its keys stayed in the checklist
    # while the schema refused them. Reproduced here rather than described.
    import olx_prompts as _o
    _orig_cs = _o._checklist_section

    def _blind(item, slots, item_id, equals=None, derived=None, counts=None,
               choices=None, expect=None):
        # Drops `counts`, to prove the audit notices a generator that stops
        # honouring a primitive. Must accept every parameter the real signature
        # takes, or adding one breaks the selftest instead of testing it.
        return _orig_cs(item, slots, item_id, equals, derived, None, choices, expect)
    _o._checklist_section = _blind
    cases.append(("the generator forgets a primitive", "PRIMITIVE NOT HONOURED", "-",
                  [f for f in enforcement_audit()[0]]))
    _o._checklist_section = _orig_cs

    # The code-reachability guard: a conversion that drops a verdict retires a
    # deduction code at identical points, so no accuracy number moves.
    import rubric_h1
    # BOTH antecedent slots, since either one keeps the code alive — the reason the
    # first version of this injection fired nothing.
    slots = [c for c in rubric_h1.BY_ID["Q4a"]["credit"]
             if c["what"].startswith("antecedent_")]
    saved = [(list(c["verdicts"]), dict(c["codes"])) for c in slots]
    for c in slots:
        c["verdicts"] = ["met", "absent"]
        c["codes"] = {"absent": "A_ONLY_ONE"}
    cases.append(("a verdict is dropped, retiring its code", "CODE UNREACHABLE", "-",
                  [f for f in enforcement_audit()[0]]))
    for c, (v, k) in zip(slots, saved):
        c["verdicts"] = v; c["codes"] = k

    # The harness schema guard. The prompt check passed throughout the period when
    # the schema beside it required 27 keys the prompt forbade, so this one probes
    # the schema agreement.py actually sends.
    import agreement as _AG
    _real_build = _AG.build_schema
    _AG.build_schema = lambda slots, exclude=frozenset(): _real_build(slots)
    cases.append(("the harness stops excluding computed keys",
                  "HARNESS SCHEMA DIVERGES", "-",
                  [f for f in enforcement_audit()[0]]))
    _AG.build_schema = _real_build

    _real_parse = _AG.parse_slots
    _AG.parse_slots = lambda spec, defaults: [
        dict(s, options=[o + "@2" if i == len(s["options"]) - 1 else o
                         for i, o in enumerate(s["options"])])
        for s in _real_parse(spec, defaults)]
    cases.append(("the harness stops stripping the @pts suffix",
                  "HARNESS SCHEMA DIVERGES", "-",
                  [f for f in enforcement_audit()[0]]))
    _AG.parse_slots = _real_parse

    # The silent-miss guard. A derived field the refs cannot resolve reads as empty,
    # scores the check unmet on every cell, and still prints a table.
    #
    # Injected on 1c, the only item that still HAS a derived rule. It used to be
    # injected on Q1, whose `utb_stated` was derived when this case was written
    # and is not any more — so the injection had become a no-op, and the case
    # went on passing because an unrelated standing finding of the same type was
    # being emitted unconditionally. Removing that finding is what exposed it.
    # Asserted rather than assumed: a case that cannot break what it claims to
    # break must fail loudly the next time the content moves under it.
    _d_item = _AG.BLOCKS[3]["bmod_h3_graph_llm"]
    _d_field = _AG.load_action(_d_item["olx"], "bmod_h3_graph_llm")["derived"][0]["fields"][0]
    assert _d_field in _d_item["refs"], (
        f"selftest is stale: {_d_field} is not in 1c's refs, so removing it "
        f"cannot break anything")
    _saved = _d_item["refs"].pop(_d_field)
    cases.append(("a derived rule's field leaves the refs map",
                  "DERIVED FIELD UNREADABLE", "-",
                  [f for f in enforcement_audit()[0]]))
    _d_item["refs"][_d_field] = _saved

    # The evenness guard, in both directions. Q1 was counted and Q2 — the same item
    # with a different noun — was not, and every audit passed for as long as it took
    # someone to ask whether the primitives were applied evenly.
    import rubric_h3
    q2 = rubric_h1.BY_ID["Q2"]
    ksaved = q2.pop("counts")
    cases.append(("an item with a countable family stops counting it",
                  "PRIMITIVE APPLIED UNEVENLY", "-",
                  [f for f in enforcement_audit()[0]]))
    q2["counts"] = ksaved

    # The other direction: counting a family whose members carry DIFFERENT codes
    # keeps one and silently retires the rest — the shape that lost A_NOT_ANTECEDENT
    # and four others once already.
    q4a = rubric_h1.BY_ID["Q4a"]
    q4a["counts"] = [{"key": "antecedent_1",
                      "slots": ["antecedent_1", "antecedent_2"]}]
    cases.append(("a family with two codes is counted anyway",
                  "PRIMITIVE APPLIED UNEVENLY", "-",
                  [f for f in enforcement_audit()[0]]))
    del q4a["counts"]

    # And the exemption itself, which is the part that rots: 1a is exempt because
    # its weeks are named, so an exemption left behind after a conversion has to say so.
    ENF.COUNTABLE_EXEMPT[("2b", "sentence")] = "stale on purpose"
    cases.append(("a stale exemption outlives its conversion",
                  "PRIMITIVE APPLIED UNEVENLY", "-",
                  [f for f in enforcement_audit()[0]]))
    del ENF.COUNTABLE_EXEMPT[("2b", "sentence")]

    q = rubric_h3.BY_ID["2a"]["credit"][0]["codes"]
    csaved = dict(q)
    q["absent"] = "NO_VERDIKT"
    cases.append(("a slot points at a code that does not exist",
                  "RUBRIC REFERENCE BROKEN", "-",
                  [f for f in enforcement_audit()[0]]))
    q.clear(); q.update(csaved)

    # The mirror of the computed-check guard: a check moved into CLI code while the
    # web still asks for it. Without this, Q1's count derivation looked clean.
    def _drop_counts(i):
        a = _orig(i)
        if i == "Q1":
            a["counts"] = ""
        return a
    globals()["_web_attrs"] = _drop_counts
    cases.append(("web Q1 loses `counts`", "ASKED ON WEB ONLY", "Q1",
                  [f for f in enforcement_audit()[0]]))
    globals()["_web_attrs"] = _orig

    # The measurement guard: an item can be graded correctly on screen and
    # contribute to no number at all.
    import agreement_app
    jsaved = agreement_app.JOBS.pop("1b")
    cases.append(("an item leaves JOBS", "NEVER MEASURED", "1b",
                  [f for f in enforcement_audit()[0]]))
    agreement_app.JOBS["1b"] = jsaved

    # The allowlist guard: an enforcement attribute the audit does not forward is
    # exactly how `derived` slipped past on the day it landed.
    ksaved = set(KNOWN_ACTION_ATTRS)
    KNOWN_ACTION_ATTRS.discard("derived")
    cases.append(("an attribute leaves the allowlist", "UNKNOWN ATTRIBUTE", "1c",
                  [f for f in enforcement_audit()[0]]))
    KNOWN_ACTION_ATTRS.clear(); KNOWN_ACTION_ATTRS.update(ksaved)

    orig = globals()["_web_attrs"]
    for item, attr, want in (("PR", "onlyif", "CHARGE-ONCE CLI ONLY"),
                             ("DAY1", "equals", "CHARGE-ONCE CLI ONLY"),
                             ("1c", "derived", "DECLARATION STALE")):
        def drop(i, _item=item, _attr=attr):
            a = orig(i)
            if i == _item:
                a[_attr] = ""
            return a
        globals()["_web_attrs"] = drop
        cases.append((f"web {item} loses `{attr}`", want, item,
                      [f for f in enforcement_audit()[0]]))
        globals()["_web_attrs"] = orig

    print("SELF-TEST — does the audit notice when a rule is removed?\n")
    bad = 0
    for label, want, item, found in cases:
        hit = [f for f in found if f[0] == item and f[1] == want]
        ok = bool(hit)
        bad += not ok
        print(f"  {'PASS' if ok else 'FAIL'}  {label:<28} -> "
              f"{hit[0][1] if hit else 'NOTHING FIRED'}")
    clean = len(enforcement_audit()[0])
    if plain is None:
        print("  SKIP  plain-path computed check     -> no plain-path item left to "
              "inject onto")
    print(f"\n  restored state is clean: {clean == 0}")
    print(f"  {len(cases) - bad}/{len(cases)} injected breakages detected.")
    return 1 if (bad or clean) else 0


def print_enforcement():
    findings, cli, web = enforcement_audit()
    print("ENFORCEMENT — what each side actually does, probed on synthetic sheets\n")
    hdr = (f"{'item':<6}{'max':>6}{'against':>9}{'gates':>13}{'charge-once':>14}"
           f"{'cover':>8}{'computed':>10}")
    print(hdr); print("-" * len(hdr))
    pair = lambda a, b: f"{a}/{b}"
    for it in sorted({**ACTION, **SHEET_ONLY}):
        w = web.get(it, {})
        if it in cli:
            c = cli[it]
            print(f"{it:<6}{c['max']:>6g}{'probe':>9}"
                  f"{pair(len(c['gates']), len(w.get('gates', []))):>13}"
                  f"{pair(len(c['charge_once']) + len(c.get('equals') or []),
                          len(w.get('chargeOnce', [])) + len(w.get('equals', []))):>14}"
                  f"{pair(len(c['cover']), len(w.get('cover', []))):>8}"
                  f"{pair(0, len(w.get('computed', []))):>10}")
        else:
            rub = config(HANDOUT[it])["rubric"].BY_ID[it]
            print(f"{it:<6}{rub['max']:>6g}{'rubric':>9}"
                  f"{'- /' + str(len(w.get('declaredGates', []))):>13}"
                  f"{'- /' + str(len(w.get('chargeOnce', [])) + len(w.get('equals', []))):>14}"
                  f"{'- /' + str(len(w.get('cover', []))):>8}"
                  f"{'- /' + str(len(w.get('computed', []))):>10}")
    print("\ncells are CLI/web counts. `against` is what the web's answers were compared"
          "\nwith: `probe` = the CLI's own behaviour, for the items it derives from checks;"
          "\n`rubric` = its deduction vocabulary, for the items whose ledger the model"
          "\nauthors, where there is no arithmetic to probe. A `-` is that absence, not a"
          "\nzero. `computed` is 0 on the CLI by construction: a derived check is not an"
          "\ninput there.\n")
    for item, kind, detail in findings:
        print(f"! {item:<5} {kind:<24} {detail}")
    print(f"{'  nothing flagged' if not findings else ''}")
    print(f"\n{len(findings)} UNDECLARED enforcement difference(s); "
          f"{len(SCORING_DIVERGENCES)} declared in olx_prompts.SCORING_DIVERGENCES.")
    print(f"All {len({**ACTION, **SHEET_ONLY})} items are compared. {len(cli)} of them "
          f"against the CLI's probed behaviour;\nthe rest against its rubric, which is the "
          "weaker basis — a rule can be justified\nby the deduction vocabulary without any "
          "check that the CLI applies it the same\nway. Those rules, each declared:")
    un = uncompared_web_rules()
    for item, kind, spec in un:
        print(f"    {item:<5} web {kind}=\"{spec}\"  (CLI item is plain-path)")
    if not un:
        print("    none")
    never, orphan = unmeasured_items()
    print(f"Coverage: {len({**ACTION, **SHEET_ONLY})} CLI item(s) scored on the web, "
          f"{len({**ACTION, **SHEET_ONLY}) - len(never)} of them measured by "
          f"agreement_app.JOBS.")
    print("Run --enforcement --selftest to confirm this audit still detects a removal.")
    return 1 if findings else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--item", choices=sorted(ACTION))
    ap.add_argument("--cli", choices=sorted(ACTION), help="print the CLI prompt for an item")
    ap.add_argument("--scoring", action="store_true",
                    help="audit the ARITHMETIC rather than the prompt text")
    ap.add_argument("--enforcement", action="store_true",
                    help="audit what each side ENFORCES (gates, charge-once, cover)")
    ap.add_argument("--selftest", action="store_true",
                    help="with --enforcement: break each rule and check the audit notices")
    a = ap.parse_args()

    if a.enforcement:
        return enforcement_selftest() if a.selftest else print_enforcement()

    if a.scoring:
        return print_scoring()

    if a.cli:
        h = HANDOUT[a.cli]
        rub = config(h)["rubric"].BY_ID[a.cli]
        print(SYSTEM_TMPL.format(blurb=config(h)["blurb"]))
        print("\n" + "=" * 70 + "\n")
        print(build_prompt(rub, "<STUDENT RESPONSE>", {c: "<...>" for c in rub["context"]}, None))
        return 0

    items = [a.item] if a.item else list(ACTION)
    if a.item:
        r = audit(a.item)
        print(f"{a.item}: question verbatim = {r['question']}")
        if r["criteria"] is not None:
            print(f"  criteria sheet verbatim = {r['criteria']}")
        for k in ("credit", "deductions", "guidance", "exemplars"):
            miss = r[k]
            print(f"  {k:<11} missing {len(miss)}/{r['totals'][k]}"
                  + (f"  {miss}" if miss else ""))
            for what, why in r["omitted"].get(k, {}).items():
                print(f"    omitted {what}: {why}")
        return 0

    hdr = (f"{'item':<5}{'question':>9}{'credit':>8}{'dedcode':>9}{'guidance':>10}"
           f"{'exempl':>8}{'omit':>6}")
    print(hdr); print("-" * len(hdr))
    gaps = omits = 0
    for it in items:
        r = audit(it); t = r["totals"]
        cell = lambda k: (f"{t[k]-len(r[k])}/{t[k]}" if t[k] else "-")
        n_omit = sum(len(v) for v in r["omitted"].values())
        gaps += sum(len(r[k]) for k in ("credit", "deductions", "guidance", "exemplars"))
        gaps += 0 if r["question"] else 1
        gaps += 0 if r["criteria"] is not False else 1
        omits += n_omit
        print(f"{it:<5}{('yes' if r['question'] else 'NO'):>9}"
              f"{('crit' if r['criteria'] else cell('credit')):>8}"
              f"{cell('deductions'):>9}{cell('guidance'):>10}{cell('exemplars'):>8}"
              f"{(n_omit or '-'):>6}")
    for it in sorted(SHEET_ONLY):
        print(f"{it:<5}{'n/a':>9}{'sheet':>8}{'-':>9}{'-':>10}{'-':>8}{'-':>6}")
    if SHEET_ONLY:
        print("\n" + ", ".join(sorted(SHEET_ONLY)) + ": scored from a slot sheet with no"
              " prompt — every verdict is\nderived from the student's fields, so there is"
              " no prompt text to compare. Audited\nby --scoring instead.")
    # Run unconditionally, in the default report. A schema difference is invisible
    # to every other audit here, and the two that happened were both found by
    # accident while chasing a score — which is the argument for it being printed
    # every time rather than behind a flag.
    sch = schema_divergences()
    if sch:
        print("\n*** RESPONSE SCHEMA differs from buildSlotSchema() in slotSheet.ts:")
        for p in sch:
            print(f"      {p}")
        print("    The schema is instruction too. Fix agreement.build_schema.")
    else:
        print("\nresponse schema matches buildSlotSchema() (properties, required,"
              "\nadditionalProperties, description literals, checks-before-feedback).")

    print("\ncells show ELEMENTS PRESENT / total, tested verbatim; `omit` counts the"
          "\nelements olx_prompts.py declares the web does not carry, with a reason."
          f"\n{gaps} undeclared gap(s), {omits} declared omission(s)"
          f"{', 1 SCHEMA divergence' if sch else ''}.")
    return 1 if sch else 0

if __name__ == "__main__":
    raise SystemExit(main())
