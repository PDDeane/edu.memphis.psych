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
import argparse, os, re, sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from score import build_prompt, SYSTEM_TMPL
from handouts import config
from olx_prompts import primitives as _primitives
O_PRIM = _primitives()
from olx_prompts import (ACTION, HANDOUT, OLX, OMIT_CREDIT, OMIT_DEDUCTION,
                         SCORING_DIVERGENCES, PROBE_REACH_LIMITS, parse_slots,
                         resolve_guidance_omissions,
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
        # `unreachable_codes` is a DECLARATION and this check has to honour it, the
        # same way --scoring honours SCORING_DIVERGENCES. The rubric already
        # names Q4a's A_NONE and Q4c's C_NONE/C_NO_KEYWORD there, with reasons,
        # and enforcement.check_codes_reachable reads the field -- but this
        # mechanical pass did not, so it reported three "undeclared" flags against
        # codes that were declared. An audit that ignores a project's own
        # declaration mechanism trains its readers to ignore the audit.
        #
        # It is a declaration, not an amnesty: a code named here that is in fact
        # reachable is itself a finding, and check_codes_reachable already raises
        # that. See GOALS.md — a code gold specifies should be made REACHABLE
        # rather than declared away, and A_NONE/C_NONE are being wired up.
        declared_dead = set(rub.get("unreachable_codes") or [])
        for d in rub["deductions"]:
            if d["code"] in OMIT_DEDUCTION.get(item, {}):
                continue
            if d["code"] in declared_dead:
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
            "requires": get("requires"), "forbid": get("forbid"),
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


def _audit_findings_fresh() -> list[tuple]:
    """The audit's RAW findings, computed in a FRESH interpreter.

    For a self-test case whose injection is only fatal on a code path that
    earlier work in this process can steer away from. Importing the audit again
    in-process cannot recover that: the module objects, their caches and every
    global the previous audits populated are all still there. A new interpreter
    is the only way to guarantee the injected source is the source that runs.

    Returns tuples of strings, which is all the case comparison needs -- it
    matches on `f[0]` (the mark) and `f[1]` (the title).
    """
    import json as _json
    import os as _os
    import subprocess as _sp
    import sys as _sys
    code = ("import json, equivalence as E\n"
            "print('FINDINGS:' + json.dumps("
            "[[str(x) for x in f] for f in E.enforcement_audit()[0]]))")
    r = _sp.run([_sys.executable, "-c", code],
                cwd=_os.path.dirname(_os.path.abspath(__file__)),
                capture_output=True, text=True)
    for ln in r.stdout.splitlines():
        if ln.startswith("FINDINGS:"):
            return [tuple(f) for f in _json.loads(ln[len("FINDINGS:"):])]
    raise RuntimeError("the fresh-interpreter audit produced no findings line:\n"
                       + r.stdout[-800:] + r.stderr[-800:])


# PARALLEL AUDITS ARE OPT-IN AND DEFAULT OFF, because they are FASTER and NOT
# YET PROVED IDENTICAL. Forking at each injection takes the self-test from ~54
# minutes to ~21, and three runs were compared case by case on ten fields:
#
#   serial vs serial   : 0 differences across all 71 cases
#   serial vs parallel : 2, both in `a family with two codes is counted anyway`
#
# The suite is therefore deterministic and the remaining gap is caused by the
# forking, not by noise. Both runs give that case the same VERDICT (ok); what
# differs is which collateral findings appear among its 53-55 -- serial reports
# PAPER AND WEB SCORE THE SAME JUDGMENTS DIFFERENTLY on Q4a/p13 and p14, and
# parallel reports ENGINES SEND A DIFFERENT REQUEST on Q4c and Q6 instead.
# Neither check shells out or touches the network on its main path, so the easy
# explanation -- a race on the score-capture subprocess -- does not hold and the
# real one is not yet known.
#
# Until it is, this stays off. A self-test is the instrument every other claim
# in this project rests on, and "faster, and it disagrees with itself about one
# case for reasons nobody has found" is not a trade worth taking by default.
# `SELFTEST_WORKERS=8` turns it on for a run where speed matters more than
# certification, and that run says so in its own output.
_AUDIT_WORKERS = int(os.environ.get("SELFTEST_WORKERS", "1") or "1")
_AUDIT_INFLIGHT: list = []


class _AuditHandle:
    """One audit running in a forked child, to be collected later."""

    # THE RESULT IS CACHED ON THE HANDLE, because the pool drains the oldest
    # child when it is full and that drain happens long before the reporting
    # loop asks for it. The first version threw the drained findings away and
    # the case they belonged to would have reported as detecting nothing.
    __slots__ = ("pid", "path", "label", "done", "value")

    def __init__(self, pid, path, label):
        self.pid, self.path, self.label = pid, path, label
        self.done, self.value = False, None


# CASES WHOSE INJECTION IS ON DISK, and which therefore cannot overlap with any
# forked audit. Declared rather than discovered, because the discovery comes too
# late: `_writes_to_disk` can only tell us a case wrote a file by RUNNING it, and
# by then every child already in flight has had a window in which to read the
# modified tree. The barrier has to close before the injection, so the set has to
# be known before it.
#
# MEASURED, TWICE, AND BOTH FAILURES ARE WHY THIS IS A SET AND NOT A GUESS. The
# first parallel run reported these five VACUOUS -- their own injection was
# reverted by the parent before the child could read it. The second run fixed
# that and then reported 19 cases whose findings did not match the serial
# reference: `GOALS RECORD DAMAGED` and `COUNT SCAFFOLD IS NOT ARITHMETIC`
# turning up inside unrelated cases, because a child was auditing while one of
# these five had GOALS.md or a scaffold file written to disk.
#
# The declaration is CHECKED: a case that writes and is not named here stops the
# run and says so. That is the one direction the detector can still cover.
_DISK_CASES = frozenset({
    "a goal is closed without approval",
    "a lesson is added to the guide unapproved",
    "the guide grows a duplicate section label",
    "a slot-set comparison drops its vocabulary guard",
    "a count scaffold reports an impossible triple",
})


def _audit_drain():
    """Wait for every forked audit still running. The barrier for a disk case."""
    for h in list(_AUDIT_INFLIGHT):
        _audit_resolve(h)


def _writes_to_disk(fn) -> list:
    """Run `fn`, reporting every path it WROTE. Used to decide fork vs serial.

    FORK ISOLATES MEMORY, NOT THE FILESYSTEM -- which is the whole reason this
    exists. A self-test case that injects by editing a table can be forked: the
    child holds its own copy-on-write snapshot and the parent's restore cannot
    reach it. A case that injects by WRITING A FILE cannot: parent and child
    share one filesystem, so the parent's restore lands while the child is still
    reading, and the child audits a tree with no injection in it.

    Measured, not predicted: the first parallel run reported five cases VACUOUS
    -- "injection moved nothing" -- and all five inject through `write_text` or
    `unlink` (GOALS.md, QUALITY_CONTROL.md, measured.py, a count scaffold).

    DETECTED RATHER THAN LISTED, because a hand-kept list of file-based cases is
    a list someone forgets to add to. If a case writes through an API not
    wrapped here it goes to the fork path and reports VACUOUS, which fails the
    run loudly -- the same way these five did. That is the failure mode this is
    allowed to have.
    """
    import builtins
    import os as _os
    import pathlib
    import shutil

    seen = []
    P = pathlib.Path
    saved = {
        "wt": P.write_text, "wb": P.write_bytes, "ul": P.unlink,
        "mk": P.mkdir, "rd": P.rmdir, "op": builtins.open,
        "rm": _os.remove, "un": _os.unlink, "md": _os.makedirs,
        "rt": shutil.rmtree, "cp": shutil.copyfile, "rn": _os.replace,
    }

    def note(target):
        seen.append(str(target))

    def wrap_self(orig):
        def f(self, *a, **k):
            note(self)
            return orig(self, *a, **k)
        return f

    def wrap_first(orig):
        def f(target, *a, **k):
            note(target)
            return orig(target, *a, **k)
        return f

    def op(file, mode="r", *a, **k):
        if any(c in mode for c in "wax+"):
            note(file)
        return saved["op"](file, mode, *a, **k)

    P.write_text, P.write_bytes = wrap_self(saved["wt"]), wrap_self(saved["wb"])
    P.unlink, P.mkdir, P.rmdir = (wrap_self(saved["ul"]), wrap_self(saved["mk"]),
                                  wrap_self(saved["rd"]))
    builtins.open = op
    _os.remove, _os.unlink = wrap_first(saved["rm"]), wrap_first(saved["un"])
    _os.makedirs, _os.replace = wrap_first(saved["md"]), wrap_first(saved["rn"])
    shutil.rmtree, shutil.copyfile = (wrap_first(saved["rt"]),
                                      wrap_first(saved["cp"]))
    try:
        fn()
    finally:
        P.write_text, P.write_bytes, P.unlink = saved["wt"], saved["wb"], saved["ul"]
        P.mkdir, P.rmdir, builtins.open = saved["mk"], saved["rd"], saved["op"]
        _os.remove, _os.unlink, _os.makedirs = saved["rm"], saved["un"], saved["md"]
        _os.replace, shutil.rmtree = saved["rn"], saved["rt"]
        shutil.copyfile = saved["cp"]
    return seen


def _audit_now():
    """The audit, in THIS process. For a case whose injection is on disk."""
    return [f for f in enforcement_audit()[0]]


def _audit_async(label: str = ""):
    """Run `enforcement_audit()` in a CHILD and return without waiting.

    WHY A FORK IS THE RIGHT SHAPE HERE. Every self-test case does the same three
    things: mutate some in-memory table, run the audit, put the table back. The
    audit is 36.6s and there are 41 of them, which is the whole ~54 minutes; the
    mutations themselves are instant. Forking at the AUDIT means the child gets
    a copy-on-write snapshot of the mutated state and the parent can restore and
    move to the next case immediately -- the child's copy is unaffected by the
    restore, because it is a different process.

    It is also SAFER than running them in-process, which is the part worth
    keeping. A case that fails to undo its own injection currently leaves the
    parent's tables wrong for every case after it; three cases did exactly that
    tonight by re-appending a dict key. An injection applied inside a child
    cannot outlive it.

    A TEMP FILE, NOT A PIPE. A pipe holds 64KB before it blocks, and the parent
    does not read until it joins -- a case whose findings exceeded that would
    deadlock the run rather than fail it.

    `os._exit` IN THE CHILD, NEVER `sys.exit`. The parent registers an atexit
    hook that RESTORES EVERY SOURCE FILE from its snapshot. Inheriting that and
    running it on child exit would have each of 41 children rewrite the tree
    underneath the run.
    """
    import pickle
    import tempfile

    if _AUDIT_WORKERS <= 1:                         # the serial path, kept usable
        return [f for f in enforcement_audit()[0]]
    while len(_AUDIT_INFLIGHT) >= _AUDIT_WORKERS:
        _audit_resolve(_AUDIT_INFLIGHT[0])          # caches onto the handle
    fd, path = tempfile.mkstemp(prefix="auditrun_", suffix=".pkl")
    os.close(fd)
    pid = os.fork()
    if pid == 0:                                    # ---- child ----
        try:
            out = [f for f in enforcement_audit()[0]]
            with open(path, "wb") as fh:
                pickle.dump(out, fh)
            os._exit(0)
        except BaseException:
            try:
                import traceback
                with open(path, "wb") as fh:
                    pickle.dump({"__error__": traceback.format_exc()}, fh)
            except BaseException:
                pass
            os._exit(3)
    h = _AuditHandle(pid, path, label)
    _AUDIT_INFLIGHT.append(h)
    return h


def _audit_resolve(found):
    """The findings from a handle, or the list it already was. Idempotent."""
    import pickle

    if not isinstance(found, _AuditHandle):
        return found
    if found.done:
        return found.value
    _, status = os.waitpid(found.pid, 0)
    if found in _AUDIT_INFLIGHT:
        _AUDIT_INFLIGHT.remove(found)
    try:
        with open(found.path, "rb") as fh:
            out = pickle.load(fh)
    except Exception as exc:
        raise SystemExit(
            f"selftest: the audit child for {found.label!r} (pid {found.pid}, "
            f"exit {status}) left no readable result at {found.path}: {exc}. A "
            f"missing result is NOT an empty finding list -- treating it as one "
            f"would report the case as undetected and blame the check.")
    finally:
        try:
            os.unlink(found.path)
        except OSError:
            pass
    if isinstance(out, dict) and "__error__" in out:
        raise SystemExit(f"selftest: the audit child for {found.label!r} died:\n"
                         f"{out['__error__']}")
    found.done, found.value = True, out
    return out


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
    # Leaving the other 16 uncompared meant a olx-only enforcement rule on any of
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
    for bad in ENF.check_exclusions_agree():
        findings.append(("-", "EXCLUSIONS DIVERGE", bad))
    for bad in ENF.check_selectors_govern_something():
        findings.append(("-", "SELECTOR GOVERNS NOTHING", bad))
    for bad in ENF.check_olx_attributes_are_read():
        findings.append(("-", "OLX ATTRIBUTE UNREAD", bad))
    for bad in ENF.check_web_scorer_exercises_its_sheet():
        findings.append(("-", "SHEET REACHES NO ARITHMETIC", bad))
    for bad in ENF.check_scorer_fingerprint_covers_its_callees():
        findings.append(("-", "FINGERPRINT MISSES A CALLEE", bad))
    for bad in ENF.check_scorer_fingerprint_is_scoped_and_prose_blind():
        findings.append(("-", "STALE-SCORER FLAG UNRELIABLE", bad))
    for bad in ENF.check_the_record_is_pushed_at_the_change():
        findings.append(("-", "RECORD NOT PUSHED AT THE CHANGE", bad))
    for bad in ENF.check_recorded_answers_are_complete():
        findings.append(("-", "ARTIFACT LOSES AN ANSWER", bad))
    for bad in ENF.check_handcoded_rules_are_being_cleared():
        findings.append(("-", "HAND-CODED RULES ACCUMULATING", bad))
    for bad in ENF.check_no_undeclared_handcoded_rules():
        findings.append(("-", "RULE HAND-CODED, NOT DECLARED", bad))
    for bad in ENF.check_criteria_prose_has_one_source():
        findings.append(("-", "CRITERIA PROSE COPIED, NOT SHARED", bad))
    for bad in ENF.check_every_check_is_invoked():
        findings.append(("-", "CHECK NEVER RUNS", bad))
    for bad in ENF.check_weighted_slots_are_scored():
        findings.append(("-", "WEIGHTED SLOT UNSCORED", bad))
    for bad in ENF.check_ref_targets_resolve():
        findings.append(("-", "REF TARGET UNRESOLVED", bad))
    for bad in ENF.check_empty_fields_are_absent():
        findings.append(("-", "EMPTY FIELD PRESENT", bad))
    for bad in ENF.check_citation_necessity_is_recorded():
        findings.append(("-", "CITATION NECESSITY UNRECORDED", bad))
    for bad in ENF.check_the_cli_sends_the_apps_prompt():
        findings.append(("-", "CLI PROMPT DIVERGES", bad))
    for bad in ENF.check_backend_deviations_declared():
        findings.append(("-", "BACKEND DEVIATION UNDECLARED", bad))
    for bad in ENF.check_blank_collapse_is_gated():
        findings.append(("-", "BLANK COLLAPSE UNGATED", bad))
    for bad in ENF.check_citations_match_exclusions():
        findings.append(("-", "EXCLUSION UNJUSTIFIED", bad))
    for bad in ENF.check_handsplit_rows_are_disjoint():
        findings.append(("-", "HANDSPLIT ROW OVERLAPS", bad))
    for bad in ENF.check_fails_verdict_is_mirrored_in_the_app():
        findings.append(("-", "APP DOES NOT MIRROR `->` SYNTAX", bad))
    for bad in ENF.check_both_engines_compute_the_same_primitives():
        findings.append(("-", "ENGINE DOES NOT COMPUTE A PRIMITIVE", bad))
    for bad in ENF.check_computed_rules_do_not_share_a_key():
        findings.append(("-", "COMPUTED RULES SHARE A KEY", bad))
    for bad in ENF.check_prior_record_reaches_every_item():
        findings.append(("-", "RECORD HOOK BLIND TO AN ITEM", bad))
    for bad in ENF.check_convertible_prose_rules_have_subgoals():
        findings.append(("-", "CONVERTIBLE RULE HAS NO SUBGOAL", bad))
    for bad in ENF.check_closed_goals_that_changed_code_were_exercised():
        findings.append(("-", "GOAL RETIRED WITHOUT A LIVE RUN", bad))
    for bad in ENF.check_gold_accounting_is_uniform():
        findings.append(("-", "GOLD ACCOUNTING NOT UNIFORM", bad))
    for bad in ENF.check_action_attributes_are_declared_in_the_block():
        findings.append(("-", "ATTRIBUTE NOT DECLARED IN THE BLOCK", bad))
    for bad in ENF.check_divergence_arithmetic_is_still_true():
        findings.append(("-", "DECLARED DIVERGENCE OUTLIVED ITS ARITHMETIC", bad))
    for bad in ENF.check_every_declaration_table_has_a_verifier():
        findings.append(("-", "DECLARATION TABLE UNWATCHED", bad))
    for bad in ENF.check_system_prompts_are_parallel():
        findings.append(("-", "SYSTEM PROMPTS OUT OF SYNC", bad))
    for bad in ENF.check_prose_only_claims_are_current():
        findings.append(("-", "PROSE-ONLY CLAIM PREDATES THE REGISTRY", bad))
    for bad in ENF.check_sibling_slots_share_their_structure():
        findings.append(("-", "SIBLING SLOTS DIFFER IN STRUCTURE", bad))
    for bad in ENF.check_prose_only_slots_are_declared():
        findings.append(("-", "PROSE-ONLY SLOT UNDECLARED", bad))
    for bad in ENF.check_artifacts_record_their_era():
        findings.append(("-", "ARTIFACT HAS NO ERA", bad))
    for bad in ENF.check_slot_rules_backlog_is_being_cleared():
        findings.append(("-", "WEB-ONLY SLOT RULES ACCUMULATING", bad))
    for bad in ENF.check_slot_rules_reach_both_prompts():
        findings.append(("-", "SLOT RULE OLX ONLY", bad))
    for bad in ENF.check_slot_rules_are_vocabulary_neutral():
        findings.append(("-", "SLOT RULE NAMES A VERDICT", bad))
    for bad in ENF.check_prompt_prose_names_only_offered_verdicts():
        findings.append(("-", "PROMPT ASKS FOR AN IMPOSSIBLE VERDICT", bad))
    for bad in ENF.check_verdict_spaces_are_declared():
        findings.append(("-", "VERDICT SPACES DIVERGE UNDECLARED", bad))
    for bad in ENF.check_slot_sets_match_gold():
        findings.append(("-", "SLOT SET DISAGREES WITH GOLD", bad))
    for bad in ENF.check_prompt_deviation_tables_are_current():
        findings.append(("-", "DECLARED DEVIATION OUTLIVED ITS TARGET", bad))
    for bad in ENF.check_rule_fail_tokens_agree():
        findings.append(("-", "SLOT RULE FAILS DIFFERENTLY", bad))
    for bad in ENF.check_exclusion_claims_are_data():
        findings.append(("-", "EXCLUSION CLAIM IN PROSE", bad))
    for bad in ENF.check_rule_examples_are_not_corpus():
        findings.append(("-", "PROMPT QUOTES A COUNTED CELL", bad))
    for bad in ENF.check_reporters_execute():
        findings.append(("-", "REPORTER CRASHES", bad))
    for bad in ENF.check_rubric_items_are_unique():
        findings.append(("-", "RUBRIC ITEMS NOT UNIQUE", bad))
    for bad in ENF.check_olx_corpus_references():
        findings.append(("-", "OLX QUOTES A STUDENT THROUGH A REFERENCE", bad))
    for bad in ENF.check_consensus_fixes_have_no_duplicate_cells():
        findings.append(("-", "TWO FIXES FOR ONE CELL", bad))
    for bad in ENF.check_corrected_gold_matches_the_sheet():
        findings.append(("-", "CORRECTED GOLD STALE", bad))
    for bad in ENF.check_gold_tables_have_no_duplicate_keys():
        findings.append(("-", "TWO ENTRIES FOR ONE CELL", bad))
    for bad in ENF.check_items_are_measured_as_configured():
        findings.append(("-", "ITEM UNMEASURED AS CONFIGURED", bad))
    for bad in ENF.check_declarations_still_have_evidence():
        findings.append(("-", "DECLARATION OUTLIVED ITS EVIDENCE", bad))
    for bad in ENF.check_prose_numbers_match_the_ledger():
        findings.append(("-", "PROSE NUMBER CONTRADICTS THE LEDGER", bad))
    for bad in ENF.check_every_wrong_cell_has_an_owner():
        findings.append(("-", "WRONG CELL WITH NO OWNER", bad))
    for bad in ENF.check_recorded_sides_are_readable():
        findings.append(("-", "RECORDED SIDE UNREADABLE", bad))
    for bad in ENF.check_app_and_harness_send_the_same_prompt():
        findings.append(("-", "ENGINES SEND DIFFERENT PROMPTS", bad))
    for bad in ENF.check_app_and_harness_send_the_same_request():
        findings.append(("-", "ENGINES SEND DIFFERENT REQUESTS", bad))
    for bad in ENF.check_engine_rate_divergence():
        findings.append(("-", "ENGINE RATE DIVERGENCE", bad))
    for bad in ENF.check_engines_score_identical_verdicts_alike():
        findings.append(("-", "ENGINES SCORE THE SAME VERDICTS DIFFERENTLY", bad))
    for bad in ENF.check_contains_matcher_agrees_across_engines():
        findings.append(("-", "MATCHER DIFFERS ACROSS ENGINES", bad))
    for bad in ENF.check_side_contract_is_enforced():
        findings.append(("-", "SIDE CONTRACT UNENFORCED", bad))
    for bad in ENF.check_no_declaration_cites_a_suspect_cell():
        findings.append(("-", "DECLARATION ARGUES FROM A SUSPECT CELL", bad))
    for bad in ENF.check_no_cell_is_both_corrected_and_declared():
        findings.append(("-", "CELL BOTH CORRECTED AND DECLARED", bad))
    for bad in ENF.check_gold_is_read_by_item():
        findings.append(("-", "GOLD READ BY HANDOUT, NOT BY ITEM", bad))
    for bad in ENF.check_written_rules_reach_the_shipped_prompt():
        findings.append(("-", "RULE WRITTEN BUT NOT DELIVERED", bad))
    for bad in ENF.check_gold_comparisons_share_an_alphabet():
        findings.append(("-", "SLOT SETS COMPARED ACROSS ALPHABETS", bad))
    for bad in ENF.check_guide_structure_is_sound():
        findings.append(("-", "GUIDE STRUCTURE HAS DRIFTED", bad))
    for bad in ENF.check_guide_lessons_are_approved():
        findings.append(("-", "GUIDE LESSON NOT APPROVED", bad))
    for bad in ENF.check_goals_record_is_intact():
        findings.append(("-", "GOALS RECORD DAMAGED", bad))
    for bad in ENF.check_probe_reach_limits_still_apply():
        findings.append(("-", "PROBE-REACH EXCUSE OUTLIVED ITS RULE", bad))
    for bad in ENF.check_computed_slot_recovery_is_faithful():
        findings.append(("-", "COMPUTED-SLOT RECOVERY UNFAITHFUL", bad))
    for bad in ENF.check_count_scaffolds_are_arithmetic():
        findings.append(("-", "COUNT SCAFFOLD IS NOT ARITHMETIC", bad))
    for bad in ENF.check_hand_authored_attrs_still_suppress_something():
        findings.append(("-", "GENERATED ATTRIBUTE HAS NO DECLARATION", bad))
    for bad in ENF.check_generated_attributes_have_a_declaration():
        findings.append(("-", "GENERATED ATTRIBUTE HAS NO DECLARATION", bad))
    for bad in ENF.check_no_case_names_in_prompts():
        findings.append(("-", "PROMPT NAMES A COHORT CASE", bad))
    for bad in ENF.check_sheet_slots_reach_the_rubric():
        findings.append(("-", "SHEET SLOT REACHES NO RUBRIC ELEMENT", bad))
    for bad in ENF.check_rubric_slots_reach_the_sheet():
        findings.append(("-", "RUBRIC SLOT NEVER REACHES THE SHEET", bad))
    for bad in ENF.check_mapped_slots_have_no_unreachable_verdict():
        findings.append(("-", "MAPPED SLOT HAS AN UNREACHABLE VERDICT", bad))
    for bad in ENF.check_maps_tables_are_attached():
        findings.append(("-", "MAPS TABLE IS NOT ATTACHED", bad))
    for bad in ENF.check_verdict_paths_drop_excluded_cells():
        findings.append(("-", "EXCLUDED CELL REACHES A VERDICT PATH", bad))
    for bad in ENF.check_shipped_text_matches_design():
        findings.append(("-", "SHIPPED TEXT DIFFERS FROM DESIGN", bad))
    for bad in ENF.check_every_prompt_field_is_designed():
        findings.append(("-", "PROMPT FIELD IS NOT THE DESIGNED TEXT", bad))
    for bad in ENF.check_probe_receipts_match_shipping():
        findings.append(("-", "PROBE MEASURED TEXT THAT NO LONGER SHIPS", bad))
    for bad in ENF.check_designed_text_is_the_measured_text():
        findings.append(("-", "DESIGN IS A PARAPHRASE OF ITS OWN EVIDENCE", bad))
    for bad in ENF.check_every_designed_entry_ships():
        findings.append(("-", "DESIGNED TEXT DOES NOT SHIP", bad))
    for bad in ENF.check_new_slots_were_probed():
        findings.append(("-", "NEW SLOT ABOUT TO BE SWEPT UNPROBED", bad))
    for bad in ENF.check_probed_fields_keep_their_text():
        findings.append(("-", "PROBED WORDING IS NOT RECORDED IN FULL", bad))
    for bad in ENF.check_closure_ceilings_are_declared():
        findings.append(("-", "CEILING RECORDED ONLY IN PROSE", bad))
    for bad in ENF.check_no_definition_vanished():
        findings.append(("-", "DEFINITION VANISHED FROM THE PACKAGE", bad))
    for bad in ENF.check_no_module_shadow_in_scratchpad():
        findings.append(("-", "A SCRATCHPAD COPY SHADOWS A PACKAGE MODULE", bad))
    for bad in ENF.check_no_module_defines_names_after_its_main_guard():
        findings.append(("-", "DEFINED BELOW THE MAIN GUARD, DEAD ON THE SCRIPT PATH", bad))
    for bad in ENF.check_one_definition_of_what_counts_as_student_text():
        findings.append(("-", "A SECOND DEFINITION OF WHAT COUNTS AS STUDENT TEXT", bad))
    for bad in ENF.check_the_export_is_not_used_to_decide_whose_words_these_are():
        findings.append(("-", "THE CITATION EXPORT USED TO CLASSIFY TEXT", bad))
    for bad in ENF.check_filesystem_locations_come_from_paths_py():
        findings.append(("-", "A FILESYSTEM LOCATION SPELLED INSTEAD OF RESOLVED", bad))
    for bad in ENF.check_every_item_has_a_findable_slot_sheet():
        findings.append(("-", "AN ITEM'S SLOT SHEET CANNOT BE FOUND", bad))
    for bad in ENF.check_probe_unreachable_pairs_still_apply():
        findings.append(("-", "A DECLARED PROBE GAP NO LONGER APPLIES", bad))
    for bad in ENF.check_no_unresolved_reference_reaches_the_page():
        findings.append(("-", "AN UNRESOLVED REFERENCE REACHED THE BUILT PAGE", bad))
    for bad in ENF.check_every_reference_has_the_data_that_resolves_it():
        findings.append(("-", "A REFERENCE WITHOUT THE DATA THAT RESOLVES IT", bad))
    for bad in ENF.check_no_file_points_into_a_developers_notes():
        findings.append(("-", "A FILE POINTS INTO A DEVELOPER'S PRIVATE NOTES", bad))
    for bad in ENF.check_reference_grammars_agree():
        findings.append(("-", "THE TWO REFERENCE RESOLVERS DISAGREE", bad))
    for bad in ENF.check_slot_grammars_agree():
        findings.append(("-", "THE TWO SLOT-SHEET PARSERS DISAGREE", bad))
    for bad in ENF.check_pick_choices_match_rubric():
        findings.append(("-", "PICK OPTIONS NOT OFFERED TO THE GRADER", bad))
    # WITHDRAWN but still INVOKED: it returns [] by design, and a defined-but-
    # never-called check trips `CHECK NEVER RUNS`. Its docstring is the record
    # of why the idea is wrong; deleting it would invite re-deriving it.
    for bad in ENF.check_no_slot_is_both_asked_and_computed():
        findings.append(("-", "SLOT IS BOTH ASKED AND COMPUTED", bad))
    for bad in ENF.check_no_judging_field_states_what_a_verdict_costs():
        findings.append(("-", "JUDGING FIELD STATES WHAT A VERDICT COSTS", bad))
    for bad in ENF.check_olx_attributes_are_all_generated():
        findings.append(("-", "OLX ATTRIBUTE NOT GENERATED FROM THE RUBRIC", bad))
    for bad in ENF.check_verdict_vocabularies_correspond():
        findings.append(("-", "VERDICT ONE ENGINE CANNOT EXPRESS", bad))
    for bad in ENF.check_one_writer_per_computed_key():
        findings.append(("-", "TWO COMPUTED PRIMITIVES WRITE ONE KEY", bad))
    for bad in ENF.check_no_recorded_run_is_an_api_error():
        findings.append(("-", "API ERROR RECORDED AS A SCORED RUN", bad))
    for bad in ENF.check_no_recorded_run_is_verdictless():
        findings.append(("-", "VERDICTLESS RUN RECORDED AS A SCORE", bad))
    for bad in ENF.check_engines_encode_an_unrecorded_verdict_alike():
        findings.append(("-", "ABSENT-VERDICT ENCODING DIVERGED", bad))
    for bad in ENF.check_scored_slots_are_answered_by_both_engines():
        findings.append(("-", "SCORED SLOT ANSWERED BY ONE ENGINE ONLY", bad))
    for bad in ENF.check_mapped_slots_agree_with_their_map():
        findings.append(("-", "RECORDED VERDICT DISAGREES WITH ITS MAP", bad))
    for bad in ENF.check_paper_reproduces_web_scores():
        findings.append(("-", "PAPER AND WEB SCORE THE SAME JUDGMENTS DIFFERENTLY", bad))
    for bad in ENF.check_paper_prompt_is_stamped():
        findings.append(("-", "PAPER PROMPT IS NOT STAMPED BY ITS OWN SHA", bad))
    for bad in ENF.check_web_code_is_stamped_by_its_own_sha():
        findings.append(("-", "WEB COLUMN IS NOT STAMPED BY THE APP'S OWN CODE", bad))
    for bad in ENF.check_web_code_neutrality_is_verified():
        findings.append(("-", "WEB-CODE NEUTRALITY CLAIM IS FALSE", bad))
    for bad in ENF.check_every_sweep_is_recorded():
        findings.append(("-", "A SWEEP ON DISK WAS NEVER RECORDED", bad))
    for bad in ENF.check_engines_offer_the_same_verdicts():
        findings.append(("-", "ENGINES OFFER THE GRADER DIFFERENT VERDICTS", bad))
    for bad in ENF.check_engines_send_the_same_request():
        findings.append(("-", "ENGINES SEND A DIFFERENT REQUEST", bad))
    for bad in ENF.check_engines_read_a_response_the_same_way():
        findings.append(("-", "ENGINES READ ONE RESPONSE DIFFERENTLY", bad))
    for bad in ENF.check_engines_reach_the_model_identically():
        findings.append(("-", "ENGINES PUT A DIFFERENT REQUEST ON THE WIRE", bad))
    for bad in ENF.check_every_failing_verdict_has_a_charge():
        findings.append(("-", "A FAILING VERDICT NOTHING CHARGES", bad))
    for bad in ENF.check_students_see_what_each_check_decided():
        findings.append(("-", "A CHECK SCORED THE STUDENT AND TOLD THEM NOTHING", bad))
    for bad in ENF.check_paper_feedback_explains_its_deductions():
        findings.append(("-", "PAPER FEEDBACK DOES NOT EXPLAIN ITS OWN CHARGE", bad))
    for bad in ENF.check_engine_mechanisms_are_not_item_dependent():
        findings.append(("-", "A MECHANISM VARIES BY ITEM", bad))
    for bad in ENF.check_side_notes_are_side_specific():
        findings.append(("-", "A SIDE NOTE IS NOT SIDE-SPECIFIC", bad))
    for bad in ENF.check_mirror_reproduces_its_own_scores():
        findings.append(("-", "MIRROR CANNOT REPRODUCE ITS OWN SCORES", bad))
    for bad in ENF.check_parked_entries_still_apply():
        findings.append(("-", "PARKING LOT NEEDS ATTENTION", bad))
    for bad in ENF.check_prompts_carry_no_process_history():
        findings.append(("-", "SHIPPED PROSE CARRIES OUR PROCESS", bad))
    for bad in ENF.check_paper_prompt_has_no_box_deixis():
        findings.append(("-", "PAPER PROMPT REFERS TO A BOX", bad))
    for bad in ENF.check_paper_scorer_agrees_on_identical_verdicts():
        findings.append(("-", "PAPER SCORER DISAGREES ON IDENTICAL VERDICTS", bad))
    for bad in ENF.check_scorer_neutrality_is_verified():
        findings.append(("-", "SCORER-NEUTRALITY CLAIM IS FALSE", bad))
    for bad in ENF.check_fixture_boxes_hold_the_students_words():
        findings.append(("-", "FIXTURE BOX IS NOT THE STUDENT'S WORDS", bad))
    for bad in ENF.check_the_audit_read_the_corpus():
        findings.append(("-", "AUDIT EXAMINED NOTHING", bad))
    for bad in ENF.check_consensus_spans_are_disjoint():
        findings.append(("-", "CONSENSUS SPANS OVERLAP", bad))
    for bad in ENF.check_fixture_covers_the_response():
        findings.append(("-", "FIXTURE DROPS RESPONSE TEXT", bad))
    for bad in ENF.check_single_box_fixtures_are_verbatim():
        findings.append(("-", "ONE-BLOCK FIXTURE NOT VERBATIM", bad))
    for bad in ENF.check_fixture_follows_response_structure():
        findings.append(("-", "FIXTURE CUTS MID-CLAUSE", bad))
    for bad in ENF.check_fixture_agrees_with_gold():
        findings.append(("-", "FIXTURE CONTRADICTS GOLD", bad))
    for bad in ENF.check_consensus_fixes_are_unique():
        findings.append(("-", "TWO FIXES FOR ONE BOX", bad))
    for bad in ENF.check_unreachable_gold_is_allowed():
        findings.append(("-", "UNREACHABLE GOLD PENALISED", bad))
    # GOAL C / §10.7 -- the migration's own gates (T4.1).
    for bad in ENF.check_gold_shared_prose_has_not_drifted():
        findings.append(("-", "MIGRATED MODULE HOLDS COURSE DATA", bad))
    for bad in ENF.check_course_data_reentries_are_current():
        findings.append(("-", "MIGRATED MODULE HOLDS COURSE DATA", bad))
    for bad in ENF.check_module_has_no_course_data():
        findings.append(("-", "MIGRATED MODULE HOLDS COURSE DATA", bad))
    for bad in ENF.check_no_module_is_named_for_a_course_artifact():
        findings.append(("-", "MODULE NAMED FOR A COURSE ARTIFACT", bad))
    for bad in ENF.check_grader_input_pairings_are_declared():
        findings.append(("-", "GRADER/INPUT PAIRING UNDECLARED", bad))
    for bad in ENF.check_container_contents_are_declared():
        findings.append(("-", "CONTAINER CONTENTS UNDECLARED", bad))
    for bad in ENF.check_peg_authoring_formats_are_declared():
        findings.append(("-", "PEG AUTHORING FORMAT UNDECLARED", bad))
    for bad in ENF.check_gold_columns_are_the_item_labels():
        findings.append(("-", "GOLD COLUMN IS NOT THE ITEM LABEL", bad))
    for bad in ENF.check_property_vocabulary_has_not_grown():
        findings.append(("-", "PROPERTY VOCABULARY GREW", bad))
    for bad in ENF.check_course_schema_is_complete():
        findings.append(("-", "COURSE SCHEMA INCOMPLETE", bad))
    for bad in ENF.check_cross_file_anchors_resolve():
        findings.append(("-", "CROSS-FILE ANCHOR DANGLES", bad))
    for bad in ENF.check_general_prose_has_no_course_vocabulary():
        findings.append(("-", "COURSE VOCABULARY IN GENERAL PROSE", bad))
    for bad in ENF.check_no_old_environment_names():
        findings.append(("-", "OLD ENVIRONMENT NAME RETURNED", bad))
    for bad in ENF.check_declaration_tables_are_verified():
        findings.append(("-", "DECLARATION TABLE VERIFIED BY NOTHING", bad))
    for bad in ENF.check_migrated_tables_match_their_source():
        findings.append(("-", "MIGRATED TABLE DOES NOT MATCH ITS SOURCE", bad))
    for bad in ENF.check_json_cache_is_not_mutated():
        findings.append(("-", "ENFORCEMENT CHECK NOT REGISTERED", bad))
    for bad in ENF.check_source_cache_matches_the_stdlib():
        findings.append(("-", "ENFORCEMENT CHECK NOT REGISTERED", bad))
    for bad in ENF.check_every_enforcement_check_is_registered():
        findings.append(("-", "ENFORCEMENT CHECK NOT REGISTERED", bad))
    for iid, h, mx, label in uncovered_cli_items():
        findings.append((iid, "SCORED ON PYTHON ONLY",
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
            findings.append((item, "NO OLX SHEET", "item not probed"))
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
                findings.append((item, "ASKED ON PYTHON ONLY",
                                 f"web computes `{k}`; the CLI still asks the model"))
        # The mirror. Without it, moving a check into CLI code and leaving the web
        # asking for it looked clean — which is what Q1's count derivation did.
        wasked = {s["key"] for s in w["scored"]} - set(w["computed"])
        for k in c.get("derived_keys") or []:
            if k in wasked and k not in must_compute.get(item, []):
                findings.append((item, "ASKED ON OLX ONLY",
                                 f"the CLI derives `{k}`; the web still asks the model"))

        # 3. gates, mapped through the vocabulary bridge.
        #
        # `gates` is what the probe OBSERVED by failing each input in turn;
        # `declaredGates` is what the sheet says. A COMPUTED gate can only ever
        # appear in the second: the probe perturbs inputs, and a computed key is
        # not an input, so failing it is not something the probe can do. Comparing
        # against the observed set alone reported Q4a/Q4c's `forbid`-computed
        # gates as CLI-only when both sides gate -- verified against lo-blocks'
        # own pickGate, which fires on `slot.gates && !sat && charged`, with
        # chargedMap true for every slot absent an `onlyif`.
        #
        # Observed still counts for everything it can see: a gate that is declared
        # and does NOT bite is a different fault, and `check_declared_gates_bite`
        # is where that belongs.
        web_gates = set(w["gates"]) | set(w.get("declaredGates") or [])
        for k in c["gates"]:
            wk = ENF.web_name(k, wkeys)
            if wk is None:
                findings.append((item, "UNMAPPED KEY", f"CLI gate `{k}` has no web counterpart"))
            elif wk not in web_gates:
                findings.append((item, "GATE PYTHON ONLY",
                                 f"`{k}` zeroes the item on the CLI, not on the web (as `{wk}`)"))
        cli_gate_web_names = {ENF.web_name(k, wkeys) for k in c["gates"]}
        for wk in w["gates"]:
            if wk not in cli_gate_web_names and wk not in w["computed"]:
                findings.append((item, "GATE OLX ONLY",
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
        # `requires` makes a pair sublinear from the credit side: once the
        # condition has denied its dependent, failing the dependent too costs
        # nothing more. Declared, like `onlyif`, so CLI discovery has a match.
        web_pairs |= {frozenset((r["key"], r["cond"])) for r in w.get("requires", [])}
        # THE `not c.get("equals")` GUARD WAS DROPPED 2026-09-12. It excluded the
        # web's equals-derived pair from `web_pairs` exactly when the CLI also
        # declared equals -- so on DAY1, DAY2, WK1 and WK2 the pair
        # (named_type, observed_type) was declared by the web as
        # `matches_chosen_type`, discovered by the CLI probe, verified IDENTICAL
        # on both sides by 4a immediately above, and then reported as a gap in
        # what the web reader declares. Four standing findings for a rule both
        # sides declare and agree on.
        #
        # The guard's premise was that a criteria-path item keeps its equals
        # comparison in Python and so exposes none to compare; `cli_signatures`
        # now returns it for those items, so the premise is simply false.
        # Nothing is hidden by removing it: a real disagreement between the two
        # equals declarations is caught by 4a, which raises EQUALS DIFFERS.
        web_pairs |= {frozenset(e["operands"]) for e in w["equals"]
                      if e["key"] not in gating}
        for a, b in c["charge_once"]:
            wa, wb = ENF.web_name(a, wkeys), ENF.web_name(b, wkeys)
            if wa is None or wb is None:
                findings.append((item, "UNMAPPED KEY",
                                 f"charge-once pair ({a}, {b}) has no web counterpart"))
            elif frozenset((wa, wb)) not in web_pairs:
                findings.append((item, "CHARGE-ONCE PROBE GAP (web)",
                                 f"({a}, {b}) is sublinear and the CLI probe found "
                                 f"it; the web reader does not declare it. A gap in "
                                 f"what the INSTRUMENTS reach, not a difference in "
                                 f"what the engines score"))
        cli_pairs = {frozenset(x for x in (ENF.web_name(a, wkeys), ENF.web_name(b, wkeys)) if x)
                     for a, b in c["charge_once"]}
        for wp in web_pairs:
            # DECLARED, WITH ITS REASON, AND RE-TESTED. See
            # enforcement.PROBE_UNREACHABLE_PAIRS: the probe finds a sublinear pair
            # by arithmetic, and some pairs produce no sublinearity for it to find.
            # That is a limit of the instrument, not a disagreement between the
            # engines -- but it belongs on the record as a decision rather than in
            # a remark inside a selftest comment.
            if (item, wp) in ENF.PROBE_UNREACHABLE_PAIRS:
                continue
            if wp not in cli_pairs:
                findings.append((item, "CHARGE-ONCE PROBE GAP (cli)",
                                 f"({', '.join(sorted(wp))}) is sublinear and the web "
                                 f"reader declares it; the CLI probe cannot reach it. A "
                                 f"gap in what the INSTRUMENTS reach, not a difference "
                                 f"in what the engines score"))
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


# How many injected breakages the suite must account for -- CONSTRUCTED plus
# SKIPPED. Two-sided: fewer means a case was lost and the run would otherwise
# report success at a smaller denominator; more means one was added without
# raising this, leaving slack a later loss can hide in.
#
# 50 = 49 constructed + 1 skipped. Set from a measured run, not from counting
# the source: the first value written here was 51, guessed as "49 cases and
# the two SKIP lines I remembered", and the ratchet immediately reported a
# lost case. Only the plain-path case skips -- the `{fail}` injection site
# still exists on Q6, so that case is built.
# 64 since 2026-09-04, for the new case "a written rule never reaches the
# shipped prompt" (check_written_rules_reach_the_shipped_prompt).
#
# THIS FIGURE IS NOT YET FROM A MEASURED RUN, which the note above says it should
# be. The suite refuses to run while a measurement is in flight -- it injects
# breakages into source a sweep reads -- and four items were sweeping when the
# case was added, so 63 + 1 is arithmetic rather than an observation. Confirm it
# on the next run: if the suite reports 63 the case is not being constructed, and
# a case that has not been fired is not a case. That is not a hypothetical here --
# three cases added earlier the same day had never once executed.
# Raised 64 -> 65 on 2026-09-05 for subgoal E43's INVERTED case, "the
# count-scaffold check goes blind". Inverted cases count here exactly as
# ordinary ones do: `total` is constructed-or-skipped, and an inverted case
# whose precondition vanishes becomes a SKIP, which is still counted. That is
# the point -- a case that stops testing anything must not be able to leave the
# tally looking full.
# RAISED 66 -> 69 ON 2026-09-12, deliberately and with the cases named, because
# this constant is TWO-SIDED: fewer means a case was lost and the suite would
# report success at a smaller denominator, more means one was added and the
# constant was not raised, "leaving slack a later loss can hide in". The three
# added cover the checks landed that day, each measured PASS on the run that
# raised this:
#   a forgiven verdict loses its declaration   -> A FAILING VERDICT NOTHING CHARGES
#   one engine sends a sampling parameter      -> ENGINES PUT A DIFFERENT REQUEST ON THE WIRE
#   the engines read one response differently  -> ENGINES READ ONE RESPONSE DIFFERENTLY
# All three are FORWARD cases (inject the condition, expect the finding) rather
# than blinding cases: each check is clean at baseline, and blinding a check that
# finds nothing is vacuous -- it would pass without testing anything.
# 72 as of 2026-09-16: the scored-slot check gained a case. It reads
# ARTIFACTS rather than sheets, so it is blinded by dropping a slot from one
# engine's recorded runs -- see the case for why a check at zero needs one.
SELFTEST_EXPECTED = 71

# HOW MANY CASES ARE ALLOWED TO TEST NOTHING. A two-sided ratchet in the same
# idiom as SELFTEST_EXPECTED: vacancy may FALL freely and may not RISE.
#
# Not zero, and not a hard failure, because one skip is legitimate -- the
# plain-path case skips when the corpus holds no item outside the derive-path
# branch, and a corpus is not a defect. Set to what the suite carries once the
# two 2026-09-18 repairs land; lower it whenever the run says it can be lowered.
# ZERO as of 2026-09-18: run6 reported `71 cases, 0 vacuous` and said so itself
# -- "vacancy fell below the ratchet: lower SELFTEST_VACANT_MAX to 0 so the gain
# is protected". It was 1 to hold the count-scaffold case, which had been vacuous
# through TWO repairs: first skipping for want of a precondition, then reporting a
# zero delta because the vacancy report scores against a baseline captured before
# its fixture exists. The case now installs its fixture as the injection, and the
# hole it hid in is closed.
SELFTEST_VACANT_MAX = 0



def _selftest_input_fingerprint() -> dict:
    """Hash every file the audit reads, so a mid-run edit can be detected.

    Everything, not just the modules the cases inject into: the checks read the
    OLX, GOALS.md, the rubric and the ledger, and an edit to any of them moves the
    baseline. Cheap -- a few dozen small files, hashed once at each end of a
    fifteen-minute run.
    """
    import hashlib
    import pathlib

    here = pathlib.Path(__file__).resolve().parent
    out = {}
    for pat in ("*.py", "*.md", "*.json", "../psychology/*.olx"):
        for f in sorted(here.glob(pat)):
            try:
                out[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()[:12]
            except OSError:
                out[f.name] = "unreadable"
    return out


_SELFTEST_REPAIR_MAX = 4_000_000          # bytes; OVERRIDES.md is ~50MB and is
                                          # machine-appended, never injected into


# THE FILES CASES ACTUALLY INJECT INTO. A case writing a file not named here
# must add it, and the run's own "source moved" check will say so.
#
# DECLARED, NOT "EVERYTHING THAT MOVED". The first version snapshotted every
# .py/.md/.json/.olx and restored anything that differed -- which cannot tell
# "a case failed to restore its injection" from "a person edited the tree while
# the run was going". Measured 2026-09-14 in the migration sandbox: it reverted
# three live edits mid-run and left the rubric half-migrated, with a superseded
# file restored and the files that replaced it already deleted. Repairing what
# the run did not break is not a safety net, it is a second writer (T5).
_SELFTEST_INJECTS = ("agreement.py", "measured.py", "GOALS.md", "QUALITY_CONTROL.md")


def _selftest_snapshot() -> dict:
    """The BYTES of every file a case could inject into, kept for repair.

    The fingerprint above DETECTS damage; this UNDOES it. They are separate on
    purpose: a run must be able to say the tree moved AND leave it as it found
    it, because reporting damage is not the same as not doing it.
    """
    import pathlib
    here = pathlib.Path(__file__).resolve().parent
    out = {}
    for name in _SELFTEST_INJECTS:
        f = here / name
        try:
            if f.exists() and f.stat().st_size <= _SELFTEST_REPAIR_MAX:
                out[str(f.resolve())] = f.read_bytes()
        except OSError:
            pass
    return out


def _selftest_repair(snapshot: dict) -> list[str]:
    """Put back anything a case mutated and failed to restore. Returns names.

    THE CASES RESTORE THEIR OWN INJECTIONS AND ONE OF THEM DOES NOT. Measured on
    a quiet tree 2026-09-14: `agreement.py` was injected and never written
    again, while three other injected files were restored correctly after it.
    So a per-case `finally` is not a guarantee, and a self-test that leaves an
    unbound name inside `report()` has done more harm than the run was worth --
    it parses, it imports, it passes every audit, and it surfaces at the end of
    a full measurement.

    It does NOT make the run pass. A repaired file is named and the exit code
    still fails: the case that failed to restore is a defect to fix, not a thing
    to absorb silently.
    """
    import pathlib
    repaired = []
    for path, want in snapshot.items():
        f = pathlib.Path(path)
        try:
            if f.read_bytes() != want:
                f.write_bytes(want)
                repaired.append(f.name)
        except OSError:
            pass
    return sorted(repaired)


def _selftest_inputs_changed(before: dict) -> list[str]:
    """Which fingerprinted inputs differ now. Empty means the tree stayed still.

    MEASURED.json is excluded: the audit itself does not write it, but a run
    recorded between the two fingerprints is a legitimate concurrent action that
    does not change what any CHECK reads about the source. Anything else moving is
    a source edit and voids the baseline.
    """
    now = _selftest_input_fingerprint()
    skip = {"MEASURED.json", "PROBED.json", "LEAKAGE_REVIEWED.json"}
    return sorted(k for k in set(before) | set(now)
                  if k not in skip and before.get(k) != now.get(k))


def _finding_key(f):
    """A finding's identity, for comparing one audit against another.

    `(item, rule)` is the semantic identity, with a slice of the detail so two
    different violations of one rule on one item stay distinct. Stringified
    because a finding's tail may hold unhashable parts.
    """
    parts = tuple(str(x) for x in (f[:3] if isinstance(f, (list, tuple)) else (f,)))
    return parts[:2] + (parts[2][:160],) if len(parts) > 2 else parts


def _vacancy_report(records, skips):
    """Which cases could not have tested anything. A pure function, so it is

    testable without a three-hour run.

    TWO FAILURE STATES, NOT ONE. A case is vacuous if its injection moved no
    finding (zero delta), OR if it was SKIPPED -- a skip never reaches a
    before/after comparison at all. Measured 2026-09-18: the neutrality case
    failed with a zero delta because the table it mutated was empty, and the
    count-scaffold case was skipped because the finding it blinds no longer fires.
    A design that compared only deltas would have caught the first and missed the
    second, which is half the evidence that motivated this report.

    It asserts a DIFFERENCE, never a particular finding: asserting the right
    finding is the suite's job, and a report that also did it would acquire the
    suite's dependence on the tree's incidental state.
    """
    rows = []
    for r in records:
        vacuous = not (r["added"] or r["removed"])
        rows.append({**r, "verdict": "VACUOUS (injection moved nothing)" if vacuous
                     else "ok", "vacuous": vacuous})
    for label, why in skips:
        rows.append({"label": label, "added": [], "removed": [], "skipped": True,
                     "verdict": f"VACUOUS (skipped: {why})", "vacuous": True})
    return rows


def enforcement_selftest():
    """Break each rule on purpose and confirm the audit says so.

    A guard that has never failed is not known to work. These are the three
    shapes that have actually gone wrong: Q6's coverage missing on the CLI (found
    by hand, months late), and the two Handout 2 rules the web moved into the
    grader.
    """
    # NO SECOND SELF-TEST, AND REFUSED BEFORE ANY INJECTION. The guard already
    # existed and already did the hard parts -- `_selftest_in_flight` skips our own
    # pid and is tree-aware, so a self-test on a COPY is not refused -- but only the
    # three SWEEPS ever called it. The self-test never asked whether another
    # self-test was running, which is the defect in RUBRIC_MIGRATION_PLAN §11.11:
    # "nothing stops two self-tests running at once -- which is how one of them came
    # to read a file the other had already mutated."
    #
    # Demonstrated on the live tree on 2026-09-18: two runs were started two minutes
    # apart and BOTH proceeded, neither refusing. This call is the fix, and it sits
    # here -- above the fingerprint, above the first injection -- because a refusal
    # after an injection would leave the tree mutated by a run that then declined to
    # continue.
    #
    # ALLOW_SELFTEST_OVERLAP remains the escape, in the same shape as the commit
    # hook's ALLOW_UNDECLARED: an overlap someone stated, not an impossibility.
    import olx_prompts as _OP_GUARD_ST
    _OP_GUARD_ST.refuse_if_selftest_running("this enforcement self-test")

    import rubric_h1, rubric_h2
    # THE INPUTS ARE FINGERPRINTED FIRST. This run takes ~15 minutes and compares
    # a restored state against a baseline captured at the start, so anything that
    # edits the source underneath it makes the comparison meaningless -- and the
    # symptom is indistinguishable from a real failure to restore. That happened
    # on 2026-08-31: a run reported "restored state is clean: False (6 finding(s),
    # baseline 3)" with all 51 cases detected and nothing wrong, because files
    # were edited while it ran.
    #
    # The overlap guards added the same day stop a SWEEP and a self-test running
    # together, in both directions. Neither stops a person editing mid-run, which
    # is the commonest form of it. This cannot be prevented from inside the
    # process, so it is DETECTED and the verdict is voided rather than reported as
    # a failure: a check that cries wolf about its own baseline gets ignored.
    _inputs = _selftest_input_fingerprint()
    # BOTH, at the same instant: the hashes say whether the tree moved, the bytes
    # put it back. The atexit hook covers the paths a `finally` does not -- an
    # early return, a raise before the report, interpreter shutdown.
    _snapshot = _selftest_snapshot()
    import atexit as _atexit
    _atexit.register(lambda: _selftest_repair(_snapshot))
    # Captured BEFORE any injection: the findings this corpus carries legitimately.
    #
    # THE SET AS WELL AS THE COUNT. The count alone cannot tell a case that changed
    # nothing from one that added a finding and removed another -- both leave the
    # total where it was. The vacancy report (below) needs to know whether the
    # injection moved ANYTHING, so it compares sets.
    _baseline_findings = enforcement_audit()[0]
    _selftest_baseline = len(_baseline_findings)
    _baseline_keys = {_finding_key(f) for f in _baseline_findings}
    cases = []

    saved = rubric_h1.BY_ID["Q6"].pop("cover")
    cases.append(("CLI Q6 loses `cover`", "COVER DIFFERS", "Q6",
                  _audit_async()))
    rubric_h1.BY_ID["Q6"]["cover"] = saved

    g = rubric_h1.BY_ID["Q6"]["cover"][0]
    vsaved = g["verdicts"]
    g["verdicts"] = [*g["labels"], "neither", "blank"]      # the web says `absent`
    cases.append(("CLI Q6 vocab drifts", "COVER VOCAB DIFFERS", "Q6",
                  _audit_async()))
    g["verdicts"] = vsaved

    # The coverage guard. Both misses so far were items the audits did not know
    # existed, so this one is checked by removing an item from the covered set.
    # THE WHOLE MAPPING, NOT THE ONE KEY. `pop` then `d[k] = saved` puts the key
    # back at the END, and dict order is data: `check_migrated_tables_match_their_source`
    # compares order-sensitively, so a case that "restored" this way left a
    # permanent mismatch behind. Three cases did it, and together they are the
    # whole of "restored state is clean: False (7 finding(s), baseline 4)" on a
    # run that detected all 71 injections. The comparison is right -- a table
    # whose order moved is not the table that was authored -- so the restore is
    # what changes.
    tsaved = dict(SHEET_ONLY)
    SHEET_ONLY.pop("T1")
    cases.append(("an item leaves the covered set", "SCORED ON PYTHON ONLY", "T1",
                  _audit_async()))
    SHEET_ONLY.clear()
    SHEET_ONLY.update(tsaved)

    # The equals comparison, now that both sides declare it on the credit path.
    d1 = rubric_h2.BY_ID["D1"]
    esaved = d1["equals"]
    d1["equals"] = [{**esaved[0], "lenient": []}]
    cases.append(("CLI D1 equals loses `unclear`", "EQUALS DIFFERS", "D1",
                  _audit_async()))
    d1["equals"] = esaved

    # The all-items guard: a olx-only enforcement rule on a plain-path item was
    # invisible until the audit covered those too.
    # Both branches of the computed-check guard: T1 is plain-path (the rule has no
    # CLI counterpart at all), 1b is derive-path (the CLI asks for it).
    import olx_prompts as _op
    # The derive-path branch: the CLI asks for what the web computes.
    for d in _op.SCORING_DIVERGENCES:
        if "1b" in (d.get("web_computes") or {}):
            wsaved = dict(d)        # the whole entry: see SHEET_ONLY above
            d.pop("web_computes")
            cases.append(("1b computed check loses its declaration",
                          "ASKED ON PYTHON ONLY", "1b",
                          _audit_async()))
            d.clear()
            d.update(wsaved)
            break
    # The plain-path branch. No live item exercises it now that T1/T2 and 1b are
    # derived, so one is injected onto a plain item — the guard has to stay tested
    # even while nothing happens to trip it.
    # A plain-path item is SYNTHESISED rather than borrowed. This used to look for
    # a live item carrying neither `derive_from_credit` nor `derive_from_criteria`
    # and inject onto it, which worked while T1/T2 and 1b were plain -- and then
    # all 26 items moved onto one derive path or the other, the search returned
    # None, and this branch quietly became a SKIP. So the plain-path half of
    # COMPUTED, UNDECLARED went unexercised: if it broke, nothing would say so.
    #
    # A case whose SUBJECT can leave the corpus is not a durable case. So the
    # shape is manufactured here instead: take an item, strip its derive keys for
    # the length of one audit -- which is exactly what being plain-path means --
    # inject the undeclared `derived`, and put the keys back. The guard is then
    # tested whatever the corpus does next, which is the property the borrowed
    # version never had.
    #
    # The derive-path branch's own item is excluded, so the two halves cannot
    # interfere: 1b is found through SCORING_DIVERGENCES.web_computes above.
    _derive_branch = {i for d in _op.SCORING_DIVERGENCES
                      for i in (d.get("web_computes") or {})}
    plain = next((i for i in sorted({**ACTION, **SHEET_ONLY})
                  if i not in _derive_branch), None)
    _orig = globals()["_web_attrs"]

    if plain is not None:
        _rub = config(HANDOUT[plain])["rubric"].BY_ID[plain]
        _derive_saved = {k: _rub.pop(k) for k in
                         ("derive_from_credit", "derive_from_criteria") if k in _rub}
        try:
            def _inject(i, _p=plain):
                a = _orig(i)
                if i == _p:
                    key = parse_slots(*_slots_attr(HANDOUT[i], sheet_id(i)))[0]["key"]
                    a["derived"] = f"{key}:present:some_field"
                return a
            globals()["_web_attrs"] = _inject
            cases.append(
                (f"a computed check appears on plain-path {plain} undeclared",
                 "COMPUTED, UNDECLARED", plain,
                 _audit_async()))
        finally:
            # Restored even if the audit raises: leaving an item stripped of its
            # derive key would corrupt every case after this one, and the
            # baseline comparison at the end would report the damage as dirt
            # without saying where it came from.
            globals()["_web_attrs"] = _orig
            _rub.update(_derive_saved)

    # The conformance guard: the two bugs that actually shipped were the prompt
    # generator not knowing about a primitive, so its keys stayed in the checklist
    # while the schema refused them. Reproduced here rather than described.
    import olx_prompts as _o
    _orig_cs = _o._checklist_section

    def _blind(*a, **k):
        # Drops `counts`, to prove the audit notices a generator that stops
        # honouring a primitive. SIGNATURE-AGNOSTIC, because the fixed-arity
        # version broke exactly as its own comment warned: `forbid` was added to
        # _checklist_section as a ninth parameter and the stub kept accepting
        # eight, so `--selftest` raised TypeError instead of testing anything --
        # the audit's own validator, silently out of service.
        if "counts" in k:
            k = {**k, "counts": None}
        elif len(a) > 5:
            a = a[:5] + (None,) + a[6:]
        return _orig_cs(*a, **k)
    _o._checklist_section = _blind
    cases.append(("the generator forgets a primitive", "PRIMITIVE NOT HONOURED", "-",
                  _audit_async()))
    _o._checklist_section = _orig_cs

    # The code-reachability guard: a conversion that drops a verdict retires a
    # deduction code at identical points, so no accuracy number moves.
    import rubric_h1
    # BOTH antecedent slots, since either one keeps the code alive — the reason the
    # first version of this injection fired nothing.
    # `startswith("antecedent_")` ALSO MATCHES THE PICKS. Subgoal Q33 added
    # `antecedent_kind_1`/`_2`, which carry no `codes` because they charge
    # nothing -- the verdict they feed does -- and this line raised KeyError the
    # first time the self-test ran after them. The filter meant the two SCORED
    # antecedent slots; requiring `codes` says so, and stays right if another
    # `antecedent_*` reporting slot is added later.
    slots = [c for c in rubric_h1.BY_ID["Q4a"]["credit"]
             if c["what"].startswith("antecedent_") and c.get("codes")]
    saved = [(list(c["verdicts"]), dict(c["codes"])) for c in slots]
    for c in slots:
        c["verdicts"] = ["met", "absent"]
        c["codes"] = {"absent": "A_ONLY_ONE"}
    cases.append(("a verdict is dropped, retiring its code", "CODE UNREACHABLE", "-",
                  _audit_async()))
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
                  _audit_async()))
    _AG.build_schema = _real_build

    _real_parse = _AG.parse_slots
    _AG.parse_slots = lambda spec, defaults: [
        dict(s, options=[o + "@2" if i == len(s["options"]) - 1 else o
                         for i, o in enumerate(s["options"])])
        for s in _real_parse(spec, defaults)]
    cases.append(("the harness stops stripping the @pts suffix",
                  "HARNESS SCHEMA DIVERGES", "-",
                  _audit_async()))
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
    # The denominator guard. Two harnesses kept hand-mirrored copies of
    # PER_ITEM_EXCLUDE and a third had none, so their rates were computed over
    # different cell sets and compared anyway. This injects the first half of
    # that — a harness with its own copy — and it must fail even though the
    # copy is equal, because equal-today is exactly how the last one survived.
    # The unreachable-gold guard. Q6 p4 asks for 6.00 from an item that moves in
    # steps of 1.25, so 6.25 is the best any correct scorer can do; counting it
    # wrong measures the rubric's arithmetic. All three harnesses must apply the
    # same allowance or their rates stop being comparable.
    # Injected as the failure that MATTERS: the allowance widening into a
    # tolerance. Tightening it back to equality would be invisible here, since
    # the check reads the harnesses' source for the call and then probes the
    # helper for over-permissiveness — so that is what gets injected.
    import handouts as _H5
    _real_sae = _H5.scores_as_exact
    _H5.scores_as_exact = lambda item, g, p: abs(p - g) <= 1.5
    cases.append(("the unreachable-gold allowance becomes a tolerance",
                  "UNREACHABLE GOLD PENALISED", "-",
                  _audit_async()))
    _H5.scores_as_exact = _real_sae

    # The shared-vocabulary guard. A rule rendered into both prompts must not name
    # one side's verdict token: the paper scorer was told when to answer
    # `wrong_kind` while being offered met/absent/not_active, so every test in it
    # was inert and p8 scored 5.00 against a gold of 2.00 — reproducibly, which
    # made a broken prompt look like a stable model difference.
    # The SITE is chosen at run time, not named here. This case used to inject
    # into Q4b/behavior_1, and when that rule's logic was converted into the
    # `maps` primitive the entry lost its `rule` key and the whole suite died on
    # a KeyError before its first case -- the guard over every other check,
    # taken out by a conversion it was not watching. Any rule carrying the
    # placeholder tests the same thing, so it now finds one; when the last such
    # rule is converted this SKIPs, the way the plain-path case already does.
    import rubric_h1 as _R1, rubric_h2 as _R2, rubric_h3 as _R3
    _site = next((c for _m in (_R1, _R2, _R3) for _it in _m.ITEMS
                  for c in (_it.get("credit") or [])
                  if "`{fail}`" in (c.get("rule") or "")), None)
    if _site is not None:
        _saved_rule = _site["rule"]
        _site["rule"] = _saved_rule.replace("{fail}", "wrong_kind")
        cases.append(("a shared rule names one side's verdict token",
                      "SLOT RULE NAMES A VERDICT", "-",
                      _audit_async()))
        _site["rule"] = _saved_rule

    # The OTHER prose source. The case above guards the rubric's `rule`, where
    # the answer is `{fail}`; SLOT_NOTES is a second source of prompt prose, is
    # olx-only, and gets no substitution. So the guard covered one source and the
    # other went unwatched -- which is how Q5:example_2 sat in the LIVE web prompt
    # naming `not_reason`, a token from the rubric's vocabulary, while its sheet
    # offered `wrong_kind`. Every test in that note was inert, it dated to the
    # original import, and BACKLOG.md:94 recorded it as found by reading. The
    # lint that closes the class is check_prompt_prose_names_only_offered_verdicts.
    # Site chosen at run time, for the reason the case above records: a hard-coded
    # site dies silently the day its note migrates, and these notes are migrating.
    # The token is chosen per site too -- `pick(NAME)` options come from the
    # sheet's `choices=` map, so "a verdict this slot lacks" cannot be a constant.
    import olx_prompts as _O
    from slot_vocab import KNOWN_VERDICTS as _KV
    _by_id = {i["id"]: i for _m in (_R1, _R2, _R3) for i in _m.ITEMS}
    _nsite = None
    for _iid, _act in sorted(_O.ACTION.items()):
        _h = _O.HANDOUT.get(_iid)
        if _h is None:
            continue
        try:
            _spec, _defs = _O._slots_attr(_h, _act)
            _ch = _O._choices_attr(_h, _act)
            _sl = _O.parse_slots(_spec, _defs)
        except Exception:
            continue
        _rk = {c["what"] for c in (_by_id.get(_iid) or {}).get("credit", []) or []
               if c.get("rule")}
        for _s in _sl:
            if _s["key"] in _rk:
                continue
            _nk = (f"{_iid}:{_s['key']}" if f"{_iid}:{_s['key']}" in _O.SLOT_NOTES
                   else _s["key"] if _s["key"] in _O.SLOT_NOTES else None)
            if not _nk:
                continue
            _off = set(_s["options"] or ())
            if _s.get("picks") is not None:
                _off |= set(_ch.get(_s["picks"], []) or ())
            _tok = next((v for v in sorted(_KV) if v not in _off), None)
            if _tok:
                _nsite = (_nk, _tok)
                break
        if _nsite:
            break
    if _nsite is not None:
        _nk, _tok = _nsite
        _saved_note = _O.SLOT_NOTES[_nk]
        _O.SLOT_NOTES[_nk] = _saved_note + f" Answer `{_tok}` if unsure."
        cases.append(("prompt prose asks for a verdict the slot cannot return",
                      "PROMPT ASKS FOR AN IMPOSSIBLE VERDICT", "-",
                      _audit_async()))
        _O.SLOT_NOTES[_nk] = _saved_note

    # The other half of that hazard: the rule uses `{fail}` correctly and the two
    # generators still substitute different meanings. Q6's state_c slots keep
    # their vocabulary on the `cover` group, score.py read only the credit entry,
    # and a rule about naming the WRONG consequence reached paper as `absent` —
    # "the box was empty". Injected by hiding the cover group the paper-side
    # lookup falls back to, which is exactly the state that caused it. Both
    # halves are injected — a rule ON a cover slot, and the cover group hidden —
    # because no cover slot need carry a rule at any given moment, and a probe
    # that depends on one being there stops testing anything the day it goes.
    _q6 = _R1.BY_ID["Q6"]
    _sc1 = [x for x in _q6["credit"] if x["what"] == "state_c1"][0]
    _saved_cover, _had_rule = _q6["cover"], _sc1.get("rule")
    # All THREE vocabulary homes are emptied. `codes` included: once
    # score._fail_verdict learned to read it, hiding only the cover group left the
    # paper side resolving `neither` correctly and the probe had nothing to catch.
    _saved_codes = _sc1.get("codes")
    _q6["cover"], _sc1["codes"] = [], {}
    _sc1["rule"] = "Answer `{fail}` when the box names the wrong thing."
    cases.append(("the two prompts fill `{fail}` with different verdicts",
                  "SLOT RULE FAILS DIFFERENTLY", "-",
                  _audit_async()))
    _q6["cover"] = _saved_cover
    if _saved_codes is None:
        _sc1.pop("codes", None)
    else:
        _sc1["codes"] = _saved_codes
    if _had_rule is None:
        _sc1.pop("rule", None)
    else:
        _sc1["rule"] = _had_rule

    # The leak that prompted the check: Q6's `affect_c1` rule illustrated its test
    # with p15's answer, p15's own 4c and the verdict — for one of the two cells
    # the rule was measured as fixing. Injected with a REAL quote from a counted
    # cell, so the probe exercises the corpus comparison rather than a stub.
    import enforcement as _E2
    import handouts as H_MOD
    _corp = _E2._corpus_cells()
    _leak = None
    for (_iid, _pid), _body in sorted(_corp.items()):
        if (_iid == "Q6" and _pid not in H_MOD.cell_exclusions(1, "Q6")
                and ("Q6", _pid) not in _E2.CORPUS_QUOTE_BACKLOG
                and len(_body.split()) > 40):
            # A run from the MIDDLE of the answer: the opening words are the
            # template sentence many students share, and a shared run is
            # filtered as the assignment's own language.
            _leak = (_pid, " ".join(_body.split()[12:26]))
            break
    if _leak is not None:
        _a1 = [x for x in _R1.BY_ID["Q6"]["credit"] if x["what"] == "affect_c1"][0]
        _saved_a1 = _a1.get("rule")
        _a1["rule"] = f'A response reading "{_leak[1]}" counts.'
        cases.append(("a prompt quotes a counted participant verbatim",
                      "PROMPT QUOTES A COUNTED CELL", "-",
                      _audit_async()))
        if _saved_a1 is None:
            _a1.pop("rule", None)
        else:
            _a1["rule"] = _saved_a1

    # A duplicated rubric item. A bad splice re-included everything from Q1
    # onward, leaving TWO entries apiece for seven items; BY_ID resolved to the
    # second copy, so the next edit was verified against a different dict than
    # the one it changed, and every audit here stayed green because they all read
    # through BY_ID. Injected by appending a copy of Q6 to ITEMS.
    import rubric_h1 as _R4
    _R4.ITEMS.append(dict(_R4.BY_ID["Q6"]))
    cases.append(("a rubric item is duplicated",
                  "RUBRIC ITEMS NOT UNIQUE", "-",
                  _audit_async()))
    _R4.ITEMS.pop()

    # Two declared corrections for one box: the later silently wins.
    import agreement_app as _APP7
    _APP7.CONSENSUS_FIXES[("Q6", 9)].append(("set", "affect_c1", "duplicate"))
    cases.append(("two span fixes name the same box",
                  "TWO FIXES FOR ONE BOX", "-",
                  _audit_async()))
    _APP7.CONSENSUS_FIXES[("Q6", 9)].pop()

    # A box holding text gold says was never written. This is the one fixture
    # check that reaches OUTSIDE the response — the others compare the boxes
    # against the student's words, this one against the grader's reading of
    # them. It found p9 after the other four had passed it. Injected by filling
    # a box gold reports as absent.
    import enforcement as _E6
    _real_fb6 = _E6._fixture_boxes
    def _filling(item, pid):
        bx = dict(_real_fb6(item, pid))
        if item == "Q6" and pid == 9:
            # INVENTED TEXT, not a student's. The check fires on a box holding
            # ANYTHING where gold reports nothing, so the content is irrelevant
            # to what is being tested -- and a real sentence here was a copy of
            # Q6/p9's own words sitting in the repo for no reason. If this ever
            # stops firing, the cause is the check, not the wording.
            bx["state_c2"] = "placeholder text for a box gold records as empty"
        return bx
    _E6._fixture_boxes = _filling
    cases.append(("a box holds text gold says was never written",
                  "FIXTURE CONTRADICTS GOLD", "-",
                  _audit_async()))
    _E6._fixture_boxes = _real_fb6

    # A box cut mid-clause. Two other fixture checks pass on these: the text is
    # all present and no two boxes share it, but a box holding "... I hope that
    # I" is a fragment, not a clause. Injected by truncating one.
    import enforcement as _E5
    _real_fb = _E5._fixture_boxes
    def _truncating(item, pid):
        bx = dict(_real_fb(item, pid))
        if item == "Q6" and pid == 1 and bx.get("state_a1"):
            # A REAL prefix of the response, cut so it ends on a function word.
            # An invented string ("... going to that") cannot be located in the
            # raw at all, so the check skips the box and the probe tests nothing.
            bx["state_a1"] = " ".join(bx["state_a1"].split()[:6])
        return bx
    _E5._fixture_boxes = _truncating
    cases.append(("a fixture box is cut mid-clause",
                  "FIXTURE CUTS MID-CLAUSE", "-",
                  _audit_async()))
    _E5._fixture_boxes = _real_fb

    # A reporter that crashes. Nothing else here executes `report()` — the
    # audits import the module, py_compile only parses — so an unbound name in
    # it survives every check and is not seen until a full measurement has been
    # spent. Injected by removing the accumulator the ALL row sums.
    import importlib as _importlib
    import agreement as _A3
    _asrc = open(_A3.__file__).read()
    _amut = _asrc.replace("    all_abs, all_err, all_hit = [], [], []",
                          "    all_abs, all_err = [], []")
    if _amut == _asrc:
        raise RuntimeError("the reporter-crash injection matched nothing -- "
                           "report() was edited and this case now tests NOTHING")
    # IN A SUBPROCESS, and RESTORED IN A `finally`. Measured 2026-09-13/14, and
    # both halves were wrong:
    #
    #   THE INJECTION IS ONLY CONDITIONALLY FATAL. `all_hit` is referenced in
    #   exactly two places inside report(), and both are guarded -- once inside
    #   `for iid in items:` and once behind `if all_abs:`. Unbinding it therefore
    #   raises only if THIS call reaches those lines. Run first in a fresh
    #   interpreter it does, and the case passes; run after a full audit in the
    #   same process it did not, and the case reported NOTHING FIRED while the
    #   audit was working perfectly -- 68 of 69 for a fault that was not there.
    #
    #   THE RESTORE WAS UNGUARDED. It sat after the append, so any non-normal
    #   exit left the mutated `agreement.py` on disk: the run then reported
    #   "restored state is clean (VOID -- source moved)" and the NEXT thing to
    #   read the tree inherited an injected NameError. Not theoretical -- a
    #   baseline capture froze it as a 28th finding on 2026-09-13.
    try:
        open(_A3.__file__, "w").write(_amut)
        _importlib.reload(_A3)
        cases.append(("a reporter crashes on an unbound name",
                      "REPORTER CRASHES", "-",
                      _audit_findings_fresh()))
    finally:
        open(_A3.__file__, "w").write(_asrc)
        _importlib.reload(_A3)

    # A NEUTRALITY PAIR WHOSE TARGET SHA THE TREE NEVER REACHED. The pair is not
    # spent -- items DO sit at its `was` sha -- so the spent-pair branch stays
    # quiet, and every item is then skipped for not being at `now`. The claim is
    # verified against nothing and the audit reads clean. Both live pairs were in
    # exactly that state on 2026-09-14, covering 0 cells while appearing to cover
    # three columns; re-pointing them at the sha the tree reached turned that into
    # 360 cells of real verification.
    #
    # Injected by moving the target to a sha nothing can be at. RESTORED IN A
    # `finally`, because a case that leaves a declaration table mutated poisons
    # every case after it -- see the reporter-crash case above, which learned it
    # the expensive way.
    # THE CASE BUILDS ITS OWN PAIR. It used to re-point the LIVE pairs at an
    # unreachable sha, which tested nothing the day the last live pair was dropped
    # as spent: `dict(SCORER_NEUTRAL)` was empty, the comprehension iterated zero
    # times, the injection injected nothing, and the case failed with NOTHING FIRED
    # on 2026-09-18 -- having quietly tested nothing for however long before that.
    #
    # That is precisely the failure this case exists to catch, turned on itself: a
    # claim "verified against nothing" while the audit reads clean. A case whose
    # fixture is whatever the tree happens to contain stops testing when the tree
    # changes, and says so only if someone reads the tally.
    #
    # So the pair is SYNTHETIC and unconditional: the case inserts one aimed at a
    # sha nothing can be at, asserts the check calls it false, and removes it. It no
    # longer matters whether any live pair exists.
    import measured as _M10
    _nsaved = dict(_M10.SCORER_NEUTRAL)
    _synth_key = ("selftest-synthetic-neutrality-pair", "0" * 12)
    try:
        _M10.SCORER_NEUTRAL.clear()
        _M10.SCORER_NEUTRAL[_synth_key] = (
            "SELF-TEST FIXTURE, not a real approval: a neutrality pair aimed at a "
            "sha the tree can never be at, so the check has a false claim to find.")
        cases.append(("a neutrality pair's target was never reached",
                      "SCORER-NEUTRALITY CLAIM IS FALSE", "-",
                      _audit_async()))
    finally:
        _M10.SCORER_NEUTRAL.clear()
        _M10.SCORER_NEUTRAL.update(_nsaved)

    # An exclusion rationale that asserts a point figure only in prose. Q6's p9
    # read "the CLI's error here is exactly -2.50" through every run measuring
    # -1.25, and blamed the fixture reconstruction while the real cause — a
    # declared A_MISMATCH divergence — went unstated in the one place whose job
    # was to state it. Injected by taking the number back out of `expect_error`.
    # Injected on Q4c/p16 since Q6/p9's exclusion became CORRECTED_GOLD; p16 is
    # now the cell carrying an `expect_error`, and the check is about the shape of
    # an exclusion rationale, not about which cell holds it.
    import handouts as _H6
    _p9 = _H6.PER_ITEM_EXCLUDE["Q4c"][16]
    _saved_err = _p9["expect_error"]
    _p9["expect_error"] = None            # not pop(): popping reorders the dict
    _p9["why"] += " the error here is exactly +2.00."
    cases.append(("an exclusion states a point figure only in prose",
                  "EXCLUSION CLAIM IN PROSE", "-",
                  _audit_async()))
    _p9["expect_error"] = _saved_err
    _p9["why"] = _p9["why"][: -len(" the error here is exactly +2.00.")]

    # The one-sided-prompt guard. `--prompts` only ever counts rubric elements the
    # WEB is MISSING, so judging text added to SLOT_NOTES reaches the web and the
    # CLI and leaves score.py behind with every audit green. Q4b's five
    # substitution tests did exactly that for a day, while `--item Q4b` reported
    # "missing 0/4, 0/5, 0/3".
    import olx_prompts as _OP2
    _OP2.SLOT_NOTES["Q4b:behavior_1"] = "x" * 400
    cases.append(("a slot rule is added to the web prompt only",
                  "SLOT RULE OLX ONLY", "-",
                  _audit_async()))
    del _OP2.SLOT_NOTES["Q4b:behavior_1"]

    # The audit-read-anything guard. Every segment-reading check swallows its
    # read errors so a machine without the corpus can still run the audit, which
    # means one bug in the shared reader turns "examined 60 submissions, found
    # six problems" into "examined nothing, found none" — reported as SUCCESS.
    # That happened: the shared reader landed at module scope, where the
    # `import segment as SEG` each check does locally was out of scope, and it
    # raised NameError on every submission. Only diffing against the previous
    # run caught it, so the condition is asserted here instead.
    _real_seg = ENF._segment_as_scored
    def _blind(*_a, **_k):
        raise NameError("name 'SEG' is not defined")
    ENF._segment_as_scored = _blind
    ENF._SEGMENTS_MEMO = None
    cases.append(("the audit cannot read the corpus at all",
                  "AUDIT EXAMINED NOTHING", "-",
                  _audit_async()))
    ENF._segment_as_scored = _real_seg
    ENF._SEGMENTS_MEMO = None

    # The duplicate-CELL guard. A repeated cell key is resolved before any check
    # runs: the later entry wins, the earlier one vanishes, and the boxes it
    # meant to fill read as empty — indistinguishable from the repair having been
    # considered and rightly skipped. That happened to Q6/p8 while its
    # consequence boxes were being assigned. No loaded object can show it, so the
    # check reads the raw source and the injection hands it one with a duplicate.
    #
    # NOW JSON, not a .py dict literal: the corrections moved to
    # CONSENSUS_SPANS.json when their 102 values stopped being stored as student
    # text. The hazard is unchanged -- `json.load` discards a repeated key just
    # as silently as Python does -- so this case moved with the check rather than
    # being retired. A case that keeps testing the old file would pass forever
    # against a source nothing reads.
    import tempfile as _tf
    _dup = _tf.NamedTemporaryFile("w", suffix=".json", delete=False)
    _dup.write('{\n'
               '  "Q6/p8": [["slice", "state_c1", "Q6", 0, 3, "aaaaaaaaaaaa"]],\n'
               '  "Q6/p8": [["slice", "change_a2", "Q6", 4, 7, "bbbbbbbbbbbb"]]\n'
               '}\n')
    _dup.close()
    ENF._CONSENSUS_SOURCE = _dup.name
    cases.append(("two CONSENSUS_FIXES entries for one cell",
                  "TWO FIXES FOR ONE CELL", "-",
                  _audit_async()))
    ENF._CONSENSUS_SOURCE = None

    # The corrected-gold guard. CORRECTED_GOLD rewrites the number a cell is
    # scored against, so a stale entry makes every rate measure against a score no
    # grader gave. The `was` value is asserted against the raw sheet; injected by
    # claiming to correct a value the sheet does not hold.
    import handouts as _H7
    _real_cg = dict(_H7.CORRECTED_GOLD)
    _k = ("Q6", 18)
    _H7.CORRECTED_GOLD[_k] = {**_real_cg[_k], "was": 9.75}
    cases.append(("a CORRECTED_GOLD entry no longer matches the sheet",
                  "CORRECTED GOLD STALE", "-",
                  _audit_async()))
    _H7.CORRECTED_GOLD.clear(); _H7.CORRECTED_GOLD.update(_real_cg)

    # The hand-split transcription guard. Q4b p7 had one sentence in two boxes
    # for as long as the table has existed: the student left `Modify:` blank and
    # wrote their modify answer in example box 1, and the table put it in both.
    # The harness then showed the model an answer the student had not given
    # there, and it scored 5.00 against a gold of 2.00 through every prompt
    # wording tried. Nothing detected it; it surfaced from an evidence quote
    # that read oddly.
    _real_hs = ENF._handsplit_tables
    ENF._handsplit_tables = lambda: {"/injected/Q4b.json": {"7": {
        "bmod_h1_q4b_first": "1) the whole sentence including the modify answer",
        "bmod_h1_q4b_modify": "the modify answer",
    }}}
    cases.append(("a hand-split row puts one sentence in two boxes",
                  "HANDSPLIT ROW OVERLAPS", "-",
                  _audit_async()))
    ENF._handsplit_tables = _real_hs

    # The stale-exclusion guard, in BOTH directions. An exclusion outlives the
    # citation that justified it (the rate keeps dropping a cell for nothing), or
    # a citation is added without registering it (the rate counts a self-graded
    # cell). Neither shows up in any number: the first shrinks a denominator, the
    # second inflates a numerator, and both look like ordinary results.
    import handouts as _H4
    _cp = _H4.HANDOUTS[1]["cited_participants"]
    _saved_cp = dict(_cp)
    _cp["Q4b"] = sorted(set(_cp.get("Q4b", [])) | {99})
    cases.append(("an exclusion outlives the citation that justified it",
                  "EXCLUSION UNJUSTIFIED", "-",
                  _audit_async()))
    _H4.HANDOUTS[1]["cited_participants"] = _saved_cp

    # The "did not answer" guard. Un-gating the collapse changes no score, so
    # nothing else in this suite would notice; it only changes the code and the
    # sentence the student reads.
    import score as _SC
    _real_dl = _SC.derive_ledger
    _SC.derive_ledger = lambda item, raw, response="": _real_dl(item, raw, "")
    cases.append(("the blank-answer collapse stops checking for a blank answer",
                  "BLANK COLLAPSE UNGATED", "-",
                  _audit_async()))
    _SC.derive_ledger = _real_dl

    # The blind-graph-item guard. A backend that quietly stops forwarding tools
    # scores 1c as "no graph" on every cell and reports it as a model result.
    import backends as _B
    _real_st = _B.LoBlocksBackend.SUPPORTS_TOOLS
    _B.LoBlocksBackend.SUPPORTS_TOOLS = True
    cases.append(("a tool-less backend claims it has tools",
                  "BACKEND DEVIATION UNDECLARED", "-",
                  _audit_async()))
    _B.LoBlocksBackend.SUPPORTS_TOOLS = _real_st

    import handouts as _H
    _real_tbl = _AG.PER_ITEM_EXCLUDE
    _AG.PER_ITEM_EXCLUDE = {k: dict(v) for k, v in _real_tbl.items()}
    cases.append(("a harness keeps its own copy of the exclusions",
                  "EXCLUSIONS DIVERGE", "-",
                  _audit_async()))
    _AG.PER_ITEM_EXCLUDE = _real_tbl

    _d_item = _AG.BLOCKS[3]["bmod_h3_graph_llm"]
    _d_field = _AG.load_action(_d_item["olx"], "bmod_h3_graph_llm")["derived"][0]["fields"][0]
    assert _d_field in _d_item["refs"], (
        f"selftest is stale: {_d_field} is not in 1c's refs, so removing it "
        f"cannot break anything")
    _saved = dict(_d_item["refs"])   # the whole map: see SHEET_ONLY above
    _d_item["refs"].pop(_d_field)
    cases.append(("a derived rule's field leaves the refs map",
                  "DERIVED FIELD UNREADABLE", "-",
                  _audit_async()))
    _d_item["refs"].clear()
    _d_item["refs"].update(_saved)

    # The evenness guard, in both directions. Q1 was counted and Q2 — the same item
    # with a different noun — was not, and every audit passed for as long as it took
    # someone to ask whether the primitives were applied evenly.
    import rubric_h3
    q2 = rubric_h1.BY_ID["Q2"]
    ksaved = q2.pop("counts")
    cases.append(("an item with a countable family stops counting it",
                  "PRIMITIVE APPLIED UNEVENLY", "-",
                  _audit_async()))
    q2["counts"] = ksaved

    # The other direction: counting a family whose members carry DIFFERENT codes
    # keeps one and silently retires the rest — the shape that lost A_NOT_ANTECEDENT
    # and four others once already.
    q4a = rubric_h1.BY_ID["Q4a"]
    q4a["counts"] = [{"key": "antecedent_1",
                      "slots": ["antecedent_1", "antecedent_2"]}]
    cases.append(("a family with two codes is counted anyway",
                  "PRIMITIVE APPLIED UNEVENLY", "-",
                  _audit_async()))
    del q4a["counts"]

    # And the exemption itself, which is the part that rots: 1a is exempt because
    # its weeks are named, so an exemption left behind after a conversion has to say so.
    ENF.COUNTABLE_EXEMPT[("2b", "sentence")] = "stale on purpose"
    cases.append(("a stale exemption outlives its conversion",
                  "PRIMITIVE APPLIED UNEVENLY", "-",
                  _audit_async()))
    del ENF.COUNTABLE_EXEMPT[("2b", "sentence")]

    q = rubric_h3.BY_ID["2a"]["credit"][0]["codes"]
    csaved = dict(q)
    q["absent"] = "NO_VERDIKT"
    cases.append(("a slot points at a code that does not exist",
                  "RUBRIC REFERENCE BROKEN", "-",
                  _audit_async()))
    q.clear(); q.update(csaved)

    # The mirror of the computed-check guard: a check moved into CLI code while the
    # web still asks for it. Without this, Q1's count derivation looked clean.
    def _drop_counts(i):
        a = _orig(i)
        if i == "Q1":
            a["counts"] = ""
        return a
    globals()["_web_attrs"] = _drop_counts
    cases.append(("web Q1 loses `counts`", "ASKED ON OLX ONLY", "Q1",
                  _audit_async()))
    globals()["_web_attrs"] = _orig

    # The measurement guard: an item can be graded correctly on screen and
    # contribute to no number at all.
    import agreement_app
    jsaved = agreement_app.JOBS.pop("1b")
    cases.append(("an item leaves JOBS", "NEVER MEASURED", "1b",
                  _audit_async()))
    agreement_app.JOBS["1b"] = jsaved

    # The allowlist guard: an enforcement attribute the audit does not forward is
    # exactly how `derived` slipped past on the day it landed.
    ksaved = set(KNOWN_ACTION_ATTRS)
    KNOWN_ACTION_ATTRS.discard("derived")
    cases.append(("an attribute leaves the allowlist", "UNKNOWN ATTRIBUTE", "1c",
                  _audit_async()))
    KNOWN_ACTION_ATTRS.clear(); KNOWN_ACTION_ATTRS.update(ksaved)

    orig = globals()["_web_attrs"]
    for item, attr, want in (("PR", "onlyif", "CHARGE-ONCE PROBE GAP (web)"),
                             ("DAY1", "equals", "CHARGE-ONCE PROBE GAP (web)"),
                             ("1c", "derived", "DECLARATION STALE")):
        def drop(i, _item=item, _attr=attr):
            a = orig(i)
            if i == _item:
                a[_attr] = ""
            return a
        globals()["_web_attrs"] = drop
        cases.append((f"web {item} loses `{attr}`", want, item,
                      _audit_async()))
        globals()["_web_attrs"] = orig

    # THE SCORED-SLOT CHECK READS ARTIFACTS, so blinding a SHEET cannot test it.
    # Blind one ENGINE instead: drop a scored slot from the olx side's recorded
    # runs and the check must say that python answers it and olx never does.
    #
    # WHY THIS CASE EXISTS. `_pointed` and `_derived` were keyed on the bare slot
    # name across all three handouts, and slot names are item-scoped: 1b's
    # `week_1` resolved to 1a's same-named slot and inherited its 2 points and
    # its derivation. Fixing that took the check to zero findings -- and a check
    # at zero because it stopped looking reads exactly like one at zero because
    # the tree is clean (QUALITY_CONTROL.md 6a). This is what tells them apart.
    import measured as _M
    _runs_orig = _M._runs_doc

    def _blind_olx(item, side, _o=_runs_orig):
        import copy
        doc = _o(item, side)
        if item == "1a" and side == "olx":
            doc = copy.deepcopy(doc)
            for run in doc["runs"]:
                for r in run["results"]:
                    for field in ("verdicts", "checks", "answers"):
                        (r.get(field) or {}).pop("week_1", None)
        return doc

    _M._runs_doc = _blind_olx
    # AGAINST ITEM "-", not "1a". The check is item-aware in what it REPORTS --
    # the text names 1a/week_1 -- but `enforcement_audit` files it as a
    # behavioural finding with no item id, exactly as the scorer injections below
    # do. The first version of this case asserted "1a" and the suite said
    # NOTHING FIRED while the finding was there all along, which is the same
    # silent-installation failure the case exists to catch. Counting the
    # injections that FIRE is what found it.
    cases.append(("olx is blinded to a scored slot",
                  "SCORED SLOT ANSWERED BY ONE ENGINE ONLY", "-",
                  _audit_async()))
    _M._runs_doc = _runs_orig

    # ── INJECTIONS INTO THE SCORER, not into the sheet ───────────────────────
    #
    # Every case above removes something from a SHEET, and the audit reads the
    # sheet, so all of them are reachable by construction. The class they cannot
    # reach is a scorer that parses a rule correctly and then ignores it -- which
    # is what `onlyif` did on the web path for as long as it existed, and what a
    # confident report of a dead `equals` on D1/D2 wrongly claimed.
    #
    # These break the ARITHMETIC and leave every sheet intact. Only a check that
    # RUNS the scorer can see them; a check that reads declarations cannot, so
    # each of these is a test of check_web_scorer_exercises_its_sheet itself.
    import agreement as _A

    WANT = "SHEET REACHES NO ARITHMETIC"
    # enforcement_audit records a behavioural finding against item "-": it is a
    # property of the SCORER, not of one item's declarations, and several items
    # trip together. The matcher below compares f[0] to this, so passing the real
    # item name here reports FAIL on a case that fired correctly -- which is what
    # the first draft of these eight cases did.
    ANY_ITEM = "-"

    # `inverted` is for a check whose findings are STANDING -- true of the corpus
    # with nothing installed. Subgoal E43's COUNT SCAFFOLD IS NOT ARITHMETIC is
    # the first: four violating artifacts are on disk and are not going away, so
    # the usual assertion ("install a breakage, the finding appears") is true with
    # the breakage installed AND removed, and tests nothing. The failure that
    # matters there is the check going BLIND, so the case installs a blinding and
    # asserts the finding DISAPPEARS. Recorded as a distinct arm rather than a
    # second helper because the two share everything but the sense of the test,
    # and the matcher below has to know which it is looking at.
    def _scorer_case(label, install, restore, want=WANT, inverted=False):
        if inverted:
            # The finding must be present BEFORE the blinding, or the case is
            # vacuous: a check that never fires would "pass" it. Assert the
            # precondition and record it, so a corpus that stops carrying the
            # violation degrades to a SKIP rather than to a silent PASS.
            pre = [f for f in enforcement_audit()[0]
                   if f[0] == ANY_ITEM and f[1] == want]
            if not pre:
                cases.append((label, want, ANY_ITEM, None))
                return
        # WROTE TO DISK -> AUDIT HERE; TOUCHED ONLY MEMORY -> FORK. See
        # `_writes_to_disk`: the parent's `restore()` below would land on a
        # forked child's tree mid-audit, and five cases reported VACUOUS that
        # way before this existed.
        # A DISK CASE CLOSES THE BARRIER FIRST. Every child still auditing
        # shares this filesystem, so the injection below would land in the
        # middle of their runs -- that is exactly how 19 cases came back with
        # another case's findings in them.
        on_disk = label in _DISK_CASES
        if on_disk:
            _audit_drain()
        wrote = _writes_to_disk(install)
        if wrote and not on_disk:
            raise SystemExit(
                f"selftest: the case {label!r} wrote {wrote[0]} during its "
                f"injection but is not in _DISK_CASES. A file-based injection "
                f"cannot overlap a forked audit -- parent and child share one "
                f"filesystem. Add it to that set so the barrier closes first.")
        try:
            cases.append((label, want, ANY_ITEM,
                          _audit_now() if on_disk else _audit_async(label),
                          inverted))
        finally:
            restore()

    # A computed primitive that always answers "satisfied" is the shape of every
    # apply_computed regression: the rule is parsed, the key is filled, and the
    # value no longer depends on the operands.
    _real_computed = _A.apply_computed
    for prim in ("equals", "expect", "forbid", "derived"):
        def _always_ok(action, checks, fixture, _prim=prim):
            out = _real_computed(action, checks, fixture)
            by = {sl["key"]: sl for sl in action["slots"]}
            for rule in action.get(_prim, []) or []:
                opts = (by.get(rule["key"]) or {}).get("options") or ["met"]
                out[rule["key"]] = {"verdict": opts[0], "evidence": "injected"}
            return out
        _scorer_case(f"the scorer stops computing `{prim}`",
                     lambda f=_always_ok: setattr(_A, "apply_computed", f),
                     lambda: setattr(_A, "apply_computed", _real_computed))

    # The counted expansion dropped -- the exact bug that left five items' members
    # unscored while every sheet still declared them.
    _real_expand = _A.expand_counted
    _scorer_case("the scorer stops expanding a count",
                 lambda: setattr(_A, "expand_counted", lambda item, checks: dict(checks)),
                 lambda: setattr(_A, "expand_counted", _real_expand))

    # Coverage dropped from satisfiedMap: naming one item twice earns both slots.
    _real_sat = _A.satisfied_map
    def _no_cover(spec, checks):
        return _real_sat(dict(spec, cover=[]), checks)
    _scorer_case("the scorer stops honouring `cover`",
                 lambda: setattr(_A, "satisfied_map", _no_cover),
                 lambda: setattr(_A, "satisfied_map", _real_sat))

    # A gating slot demoted to an ordinary one: the item's whole value stops
    # depending on the check that is supposed to decide it.
    _real_slots = _A.SCORERS["slots"]
    def _ungated(spec, item, checks):
        return _real_slots(dict(spec, slots=[{**sl, "gates": False}
                                             for sl in spec["slots"]]), item, checks)
    _scorer_case("the scorer stops honouring a gate",
                 lambda: _A.SCORERS.__setitem__("slots", _ungated),
                 lambda: _A.SCORERS.__setitem__("slots", _real_slots))

    # `onlyif` ignored: the guarded check is charged alongside its failed
    # condition. This is the regression that shipped.
    def _no_onlyif(spec, item, checks):
        return _real_slots(spec, {k: v for k, v in item.items() if k != "onlyif"}, checks)
    _scorer_case("the scorer stops honouring `onlyif`",
                 lambda: _A.SCORERS.__setitem__("slots", _no_onlyif),
                 lambda: _A.SCORERS.__setitem__("slots", _real_slots))

    # The ledger's own guard. A fingerprint that moves on prose is the failure
    # that put twenty-one items on the sweep list for a corrected comment.
    import measured as _M
    _real_strip = _M._behaviour_src
    # The RECORDING path, which no other case touches. A recording fault moves no
    # score, so nothing else in the harness reacts to it: four count slots wrote
    # "" into every artifact of every run and the only symptom was a diagnosis
    # that had to be rebuilt from `evidence` prose.
    _real_rec = _A.recorded_answer
    _scorer_case("the artifact stops recording a count answer",
                 lambda: setattr(_A, "recorded_answer",
                                 lambda sl, ch: _A.verdict_of(ch, sl["key"])),
                 lambda: setattr(_A, "recorded_answer", _real_rec),
                 want="ARTIFACT LOSES AN ANSWER")

    _scorer_case("the fingerprint starts tracking prose again",
                 lambda: setattr(_M, "_behaviour_src", lambda src: src),
                 lambda: setattr(_M, "_behaviour_src", _real_strip),
                 want="STALE-SCORER FLAG UNRELIABLE")

    # A declaration that reasons from a cell whose INPUT is untrusted. This is
    # the one case here that guards PROSE rather than arithmetic, and it is here
    # because the check it exercises was written green: its item->handout map was
    # keyed on dict reprs, so it matched nothing and reported a clean corpus. A
    # five-way fire test caught that, and this case keeps it caught.
    # THE TWO GOLD TABLES CONTRADICTING EACH OTHER. Needs no run data, so unlike
    # every other declaration check it fires the moment the second entry exists
    # -- which is exactly why three double-booked cells survived a whole day
    # while the audit read clean.
    import handouts as _HH
    _scorer_case("a corrected cell is also declared",
                 lambda: _HH.GOLD_DIVERGENCES.append(
                     {"code": "PROBE", "cells": [("NR", 4)], "why": "injected"}),
                 lambda: _HH.GOLD_DIVERGENCES.pop(),
                 want="CELL BOTH CORRECTED AND DECLARED")

    # A SCORER-NEUTRALITY CLAIM THAT IS NOT TRUE, added 2026-09-04. The table
    # suppresses STALE SCORER for a fingerprint pair; the injection declares a
    # pair whose covered cells DO move, by pointing an entry at a sha no item is
    # recorded at -- which is the spent-exemption arm and the one that rots
    # silently.
    _real_neutral = dict(_M.SCORER_NEUTRAL)
    _scorer_case("a scorer-neutrality entry excuses nothing",
                 lambda: _M.SCORER_NEUTRAL.__setitem__(
                     ("deadbeefcafe", "f00dbaadf00d"), "injected"),
                 lambda: (_M.SCORER_NEUTRAL.clear(),
                          _M.SCORER_NEUTRAL.update(_real_neutral)),
                 want="SCORER-NEUTRALITY CLAIM IS FALSE")

    # BOUND HERE, ABOVE ITS FIRST USE. This import sat ~50 lines BELOW the three
    # cases that use it, which made `_pl2` a local for the whole function and
    # raised UnboundLocalError on the first of them. So the three cases added on
    # 2026-09-04 -- goal closed without approval, lesson added without approval,
    # guide structure -- had NEVER ONCE EXECUTED, and because the raise aborts the
    # suite they also took every case after them down. Found only by running the
    # suite; `--enforcement` alone never reaches this function. A case that has
    # not been fired is not a case.
    import pathlib as _pl2

    # A GOAL CLOSED WITHOUT THE USER AGREEING, added 2026-09-04. GOALS.md states
    # that rule itself and nothing enforced it; it was broken once by closing a
    # subgoal inside a recording step. The injection flips one open checkbox.
    _gl = _pl2.Path(__file__).resolve().parent / "GOALS.md"
    _goals_src = _gl.read_text()

    def _close_one():
        import re as _re
        m = _re.search(r"^- \[ \] Q\d+\. .*$", _goals_src, _re.M)
        _gl.write_text(_goals_src.replace(
            m.group(0), m.group(0).replace("- [ ]", "- [x]", 1), 1))

    _scorer_case("a goal is closed without approval",
                 _close_one,
                 lambda: _gl.write_text(_goals_src),
                 want="GOALS RECORD DAMAGED")

    # A LESSON ADDED TO THE GUIDE WITHOUT THE USER'S AGREEMENT, added 2026-09-04
    # on the user's instruction that the asking be enforced rather than
    # remembered. The injection appends a bold-led paragraph, which is the house
    # style for a claim the reader is meant to act on.
    _gp2 = _pl2.Path(__file__).resolve().parent / "QUALITY_CONTROL.md"
    _guide_src2 = _gp2.read_text()
    _scorer_case("a lesson is added to the guide unapproved",
                 lambda: _gp2.write_text(
                     _guide_src2 + "\n\n**AN UNAPPROVED LESSON.** With a body.\n"),
                 lambda: _gp2.write_text(_guide_src2),
                 want="GUIDE LESSON NOT APPROVED")

    # THE GUIDE'S OWN STRUCTURE, added 2026-09-03 after six hand-labelled
    # sections produced three duplicate labels and an out-of-order section 2.
    # Nothing caught it; it was found by eye. The injection duplicates a label,
    # which is the exact failure.
    _gp = _pl2.Path(__file__).resolve().parent / "QUALITY_CONTROL.md"
    _guide_src = _gp.read_text()

    def _dup_label():
        import re as _re
        m = _re.search(r"^## (\d+[a-z]\d?)\. (.+)$", _guide_src, _re.M)
        _gp.write_text(_guide_src + f"\n\n## {m.group(1)}. Injected duplicate\n")

    _scorer_case("the guide grows a duplicate section label",
                 _dup_label,
                 lambda: _gp.write_text(_guide_src),
                 want="GUIDE STRUCTURE HAS DRIFTED")

    # COMPARING OUR SLOT SET AGAINST GOLD'S WITHOUT A VOCABULARY GUARD, added
    # 2026-09-03. Four functions had this the day gates entered the slot profile,
    # and they failed in both directions -- two raised a false alarm (a gate
    # "differing" from gold on every cell, a correct gate scored 11/11
    # CONTRADICTED) and two silently lost signal (a jammed ratchet, suppressed
    # conflict reports). Neither "the audit is clean" nor "nothing changed" would
    # have surfaced any of them, which is why the rule is static.
    _real_alpha = dict(ENF.GOLD_ALPHABET_EXEMPT)
    import pathlib as _pl
    _mp = _pl.Path(__file__).resolve().parent / "measured.py"
    _orig_src = _mp.read_text()

    def _unguard():
        # THE TARGET IS FOUND, NOT NAMED. This injection named
        # `gold_slot_disagreements`, which stopped naming either slot set when
        # the audit was reworked (00c529b) -- so `seg.replace` changed nothing,
        # the file was rewritten byte-identical, and the case reported FAIL while
        # injecting nothing at all. A selftest case that cannot fail is worse
        # than a missing one: it reads as a detection gap in the audit when the
        # audit is fine, and it had gone stale silently.
        #
        # So pick whatever function actually carries all three patterns the check
        # keys on -- a gold set, our set, and the guard -- and REFUSE to run if
        # the mutation would be a no-op, which is the failure mode that hid here.
        import ast
        import sourcecache
        import re as _re
        _G = _re.compile(r"gold_charged_slots|gold_charge_bounds|gold_charged_code")
        _O = _re.compile(r"_our_failing_slots|_charging_slots")
        tree = ast.parse(_orig_src)
        cands = []
        for n in ast.walk(tree):
            if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            body = sourcecache.segment(_orig_src, n) or ""
            if _G.search(body) and _O.search(body) and "_gold_nameable_slots" in body:
                cands.append((len(body), n.name, body))
        if not cands:
            raise RuntimeError(
                "no guarded gold-vs-ours comparison is left in measured.py, so "
                "this case has nothing to unguard -- retire it or repoint it")
        # Smallest span, so a guarded CHILD is chosen over the function that
        # merely encloses it; the check reports innermost-only for that reason.
        _n, _name, seg = min(cands)
        mutated = seg.replace("_gold_nameable_slots", "_NOPE_")
        if mutated == seg or _orig_src.count(seg) != 1:
            raise RuntimeError(f"injection into {_name} would not change the file")
        _mp.write_text(_orig_src.replace(seg, mutated, 1))

    _scorer_case("a slot-set comparison drops its vocabulary guard",
                 _unguard,
                 lambda: (_mp.write_text(_orig_src),
                          ENF.GOLD_ALPHABET_EXEMPT.clear(),
                          ENF.GOLD_ALPHABET_EXEMPT.update(_real_alpha)),
                 want="SLOT SETS COMPARED ACROSS ALPHABETS")

    # READING GOLD BY HANDOUT INSTEAD OF BY ITEM, added 2026-09-03 after the
    # mistake was made live: item 1a was looked up against the handout ONE
    # sheet (the token is spelled out rather than written, because naming a
    # loader in this file makes it match the gold-consumer regex and trips
    # GOLD ACCOUNTING NOT UNIFORM against equivalence itself). 1a is a
    # handout 3 item, and the miss returned `{}` -- the same thing an ungraded
    # cell returns. This case exercises the ALLOWLIST arm, which was itself
    # written green: the first predicate matched only the dict spelling of the
    # loader pick, so cross_path's tuple form walked past it and the arm passed
    # with the table emptied.
    _real_allow = dict(ENF.HANDOUT_KEYED_GOLD_READERS)
    _scorer_case("a module picks a gold loader by handout, undeclared",
                 lambda: ENF.HANDOUT_KEYED_GOLD_READERS.pop("cross_path"),
                 lambda: (ENF.HANDOUT_KEYED_GOLD_READERS.clear(),
                          ENF.HANDOUT_KEYED_GOLD_READERS.update(_real_allow)),
                 want="GOLD READ BY HANDOUT, NOT BY ITEM")

    # A RULE WRITTEN AND NEVER DELIVERED, added 2026-09-04. This state is
    # invisible to the staleness reading: `prompt_sha` describes the SHIPPED
    # prompt, so a rule edited in the rubric and not regenerated leaves it
    # untouched and the item reads clean. It happened for real the same day --
    # Q3's and Q4b's rules were written and committed while the staleness list
    # showed eight flags on four OTHER items and nothing on those two.
    # The injection removes one generated line from what the shipped file appears
    # to hold, on an item that IS delivered, so the arm is exercised rather than
    # riding on the two genuinely-undelivered items in the baseline.
    import olx_prompts as _OPX
    _real_src = _OPX._src

    def _undeliver():
        want = _OPX.build_web_prompt("Q2")
        line = max((ln.strip() for ln in want.split("\n")), key=len)
        _OPX._src = lambda h, _l=line: _real_src(h).replace(_l, "", 1)

    def _redeliver():
        _OPX._src = _real_src

    _scorer_case("a written rule never reaches the shipped prompt",
                 _undeliver, _redeliver,
                 want="RULE WRITTEN BUT NOT DELIVERED")

    # THE BOUNDS TABLE'S RATCHET, added 2026-09-02. The disagreements table had
    # one and this table did not, so three 2a entries stood asserting a
    # disagreement on the very day the conjunction rule ended it, and the
    # ratchet's first run found two Q4a entries that had been stale for longer --
    # with Q20's own text already saying one of them agreed. A stale declaration
    # subtracts itself from every rate and leaves no trace, so the retirement
    # path needs a test of its own.
    _real_bounds = dict(_M.GOLD_SLOT_BOUNDS_KNOWN)

    def _add_stale():
        _M.GOLD_SLOT_BOUNDS_KNOWN[("Q4a", 6)] = "stale: we now agree with gold"

    def _drop_stale():
        _M.GOLD_SLOT_BOUNDS_KNOWN.clear()
        _M.GOLD_SLOT_BOUNDS_KNOWN.update(_real_bounds)

    _scorer_case("a bounds declaration outlives its cell",
                 _add_stale, _drop_stale,
                 want="SLOT SET DISAGREES WITH GOLD")

    # THE FIXTURE ITSELF, which no prompt or scoring check looks at. Dropping
    # 2a's `counts` was the edit that replaced its boxes with "2 found" and cost
    # a 120-call sweep, and that edit CANNOT do it any more -- the dealing groups
    # moved out of the rubric into JOBS on 2026-09-02 precisely so a scoring
    # change could not reach the input. So the breakage to inject is the absence
    # of the new declaration, which {{corpus:Q4b/p13:modify:42:63:sha=ae62a6d034c3}} still sends a member
    # field down the placeholder path.
    #
    # BOTH FIXTURE CACHES ARE CLEARED on the way in AND out. agreement's is keyed
    # on (item, pid) alone, so it does not notice an injected change: without the
    # clear the corrupt fixture survived the restore and "restored state is clean"
    # failed on a run where nothing was actually left behind.
    import agreement as _AG
    import agreement_app as _APP

    def _fx_reset():
        _AG._fixture_cached.cache_clear()
        ENF._fixture_built.cache_clear()

    _real_dealt = _APP.JOBS["2a"].get("dealt")

    def _drop_dealt():
        _APP.JOBS["2a"].pop("dealt", None)
        _fx_reset()

    def _put_dealt():
        _APP.JOBS["2a"]["dealt"] = _real_dealt
        _fx_reset()

    _scorer_case("the fixture stops dealing a counted group",
                 _drop_dealt, _put_dealt,
                 want="FIXTURE BOX IS NOT THE STUDENT'S WORDS")

    # OWNERSHIP, which had no case until 2026-09-02 even though the check is
    # what keeps a wrong cell from being buried in a median. Emptying the owner
    # map must make every wrong cell an orphan; if it does not, the check has
    # stopped reading GOALS.md and would report clean on a file it never opened.
    _real_owners = _M._live_subgoal_owners
    # THE STUB TAKES ITS SHAPE FROM THE REAL FUNCTION, and its ARITY is `*a`.
    # Hand-written as `lambda: {"any": {}, "title": {}, "by_side": {}}` it had
    # drifted twice over: `_live_subgoal_owners` grew an `excluding` parameter,
    # so `wrong_cells_without_an_owner` called the stub with one argument and
    # raised TypeError, and it had grown a fourth key (`subject`) that the stub
    # did not return. The TypeError aborted enforcement_selftest partway through
    # -- every arm after this one silently never ran, which is the one failure a
    # self-test cannot afford. Reading the keys off `_real_owners()` means the
    # stub cannot fall behind the thing it stands in for again.
    _empty_owners = {k: {} for k in _real_owners()}
    _scorer_case("the owner map stops being read",
                 lambda: setattr(_M, "_live_subgoal_owners",
                                 lambda *a, **k: {k2: {} for k2 in _empty_owners}),
                 lambda: setattr(_M, "_live_subgoal_owners", _real_owners),
                 want="WRONG CELL WITH NO OWNER")

    # The reconstruction every olx slot read depends on. Its faithfulness is
    # checkable only against the python artifacts, which record what the olx ones
    # compute and discard -- so if that comparison stops happening, nothing else
    # in the harness notices a drift.
    _real_ac = _A.apply_computed
    _scorer_case("recovery stops computing a primitive's slot",
                 lambda: setattr(_A, "apply_computed",
                                 lambda action, checks, fixture: checks),
                 lambda: setattr(_A, "apply_computed", _real_ac),
                 want="COMPUTED-SLOT RECOVERY UNFAITHFUL")

    # SUBGOAL E43. The check's findings are STANDING -- four violating artifacts
    # are on disk -- so this is the INVERTED arm: blind the check and assert it
    # goes silent. Blinding at the enforcement function rather than at the files
    # keeps the artifacts untouched; a case that edited them would be testing the
    # corpus rather than the check, and would leave a measurement behind.
    # SUBGOAL E44. The ordinary arm works here: with nothing installed the tree
    # is clean, so removing a declaration while its attribute stays in the .olx
    # makes the finding appear. That is the exact shape of the 2026-09-05 revert
    # that left three orphans and cost eight sweeps their turn.
    import rubric_h2 as _R2E44
    _real_expect_wk1 = _R2E44.BY_ID["WK1"].get("expect")
    def _drop_wk1_expect():
        _R2E44.EXPECT.pop("WK1", None)
        _R2E44.BY_ID["WK1"].pop("expect", None)
    def _restore_wk1_expect():
        _R2E44.EXPECT["WK1"] = [{"key": "targets_own_behavior",
                                 "left": "trigger_behavior",
                                 "value": "utb", "lenient": ["wgb"]}]
        if _real_expect_wk1 is not None:
            _R2E44.BY_ID["WK1"]["expect"] = _real_expect_wk1
    _scorer_case("a rubric declaration is removed, its attribute is not",
                 _drop_wk1_expect, _restore_wk1_expect,
                 want="GENERATED ATTRIBUTE HAS NO DECLARATION")

    # THE FIXTURE IS THE INJECTION, AND THE CASE IS NO LONGER INVERTED.
    #
    # First repair (2026-09-18): the case blinded the check and asserted the
    # finding DISAPPEARS, which needs the finding present first -- and on a clean
    # corpus it never was, so the case had been SKIPPING for an unknown period
    # while the tally read `72 of 72 expected`. That repair wrote an artifact
    # carrying the real historical shape, Q2/p11's `0 listed, 0 failing, 3 given`.
    #
    # It did not work, and the reason is worth keeping. The vacancy report scores
    # a case by the DELTA against `_baseline_findings`, captured once at the start
    # of the run -- about 1,200 lines before this fixture is written. So the
    # baseline never saw the violation, the blinded audit did not report it
    # either, and `added` and `removed` were both empty: `VACUOUS (injection moved
    # nothing)`. The case was repaired into a SECOND vacuous state, and only the
    # ratchet made that visible.
    #
    # Inverting was only ever a workaround for having no way to CAUSE the
    # violation. The fixture is that way, so the case now runs in the natural
    # direction: install the artifact, confirm the finding appears, remove it.
    # That tests the check DETECTS, where blinding only tested that a stubbed
    # function returns nothing. It needs no precondition, so it cannot degrade to
    # a skip, and its delta is against the same baseline as every other case.
    #
    # Removed in a `finally`: a stray `*.runs.json` under the out root is read by
    # every later check and by `measured` as if it were a real run.
    #
    # It must carry `web_score_sha` matching `measured.web_code_sha("score", item)`
    # or the check's own attributability filter skips the file and the case is
    # vacuous for a NEW reason -- which is the trap this repair exists to close.
    import json as _json43
    import pathlib as _pl43
    import paths as _paths43
    import measured as _M43

    _sc_root, _sc_why = _paths43.out_root_or_reason()
    if _sc_root is None:
        # LOUD, NOT SKIPPED. Without an out root this case cannot install its
        # fixture, and a self-test that quietly drops a case is the exact failure
        # this repair is about. Dozens of other checks cannot run either, so
        # stopping here names the real cause once instead of scattering it across
        # a dozen "not detected" lines.
        raise RuntimeError(
            f"enforcement_selftest: the count-scaffold case needs an out root to "
            f"install its fixture, and there is none -- {_sc_why}")

    _sc_item = "Q2"
    _sc_dir = _pl43.Path(_sc_root) / "selftest_scaffold_fixture"
    _sc_file = _sc_dir / f"{_sc_item}.runs.json"

    def _install_scaffold():
        _sc_dir.mkdir(parents=True, exist_ok=True)
        # The era sha must match `measured.web_code_sha("score", item)` or the
        # check's own attributability filter skips the file and the case goes
        # vacuous for a third reason.
        _sc_file.write_text(_json43.dumps({
            "era": {"web_score_sha": _M43.web_code_sha("score", _sc_item)},
            "runs": [{"results": [{
                "participant_id": 9999,
                "answers": {"reasons_listed": 0,
                            "reasons_failing": 0,
                            "reasons_given": 3}}]}]}))

    def _remove_scaffold():
        _sc_file.unlink(missing_ok=True)
        if _sc_dir.is_dir() and not any(_sc_dir.iterdir()):
            _sc_dir.rmdir()

    try:
        _scorer_case("a count scaffold reports an impossible triple",
                     _install_scaffold, _remove_scaffold,
                     want="COUNT SCAFFOLD IS NOT ARITHMETIC")
    finally:
        _remove_scaffold()
    import handouts as _H
    _real_why = _H.CORRECTED_GOLD[("NR", 4)]["why"]
    _scorer_case("a declaration starts citing a suspect cell",
                 lambda: _H.CORRECTED_GOLD[("NR", 4)].__setitem__(
                     "why", _real_why + " Compare p3, which gold credits."),
                 lambda: _H.CORRECTED_GOLD[("NR", 4)].__setitem__(
                     "why", _real_why),
                 want="DECLARATION ARGUES FROM A SUSPECT CELL")

    # THE THREE CHECKS ADDED 2026-09-12, each clean at baseline -- so they need
    # the forward direction (introduce the condition, verify it is reported)
    # rather than the blinding direction, which is vacuous against a check that
    # currently finds nothing.
    import enforcement as _ENFX

    _real_uncharged = dict(_ENFX.UNCHARGED_VERDICTS)
    _scorer_case("a forgiven verdict loses its declaration",
                 lambda: _ENFX.UNCHARGED_VERDICTS.clear(),
                 lambda: (_ENFX.UNCHARGED_VERDICTS.clear(),
                          _ENFX.UNCHARGED_VERDICTS.update(_real_uncharged)),
                 want="A FAILING VERDICT NOTHING CHARGES")

    # The envelope around the prompt: a sampling parameter on one engine only.
    # Patched at the CAPTURE, so the real capture path is exercised and only its
    # answer is perturbed -- a check that compared nothing would pass a stub.
    _real_env = _ENFX._app_envelope

    def _envelope_with_temperature():
        import copy
        got, why = _real_env()
        if why:
            return got, why
        got = copy.deepcopy(got)
        got.setdefault("body", {})["temperature"] = 0.7
        return got, ""

    _scorer_case("one engine starts sending a sampling parameter",
                 lambda: setattr(_ENFX, "_app_envelope", _envelope_with_temperature),
                 lambda: setattr(_ENFX, "_app_envelope", _real_env),
                 want="ENGINES PUT A DIFFERENT REQUEST ON THE WIRE")

    # One recorded response read to two different scores. Patched at the
    # COMPARISON rather than the scorer, because driving the app's scorer for
    # 5,668 payloads costs minutes and the thing under test here is whether a
    # difference is REPORTED once found.
    _real_interp = _ENFX._interpretation_comparison

    def _interp_with_a_difference():
        d = dict(_real_interp())
        d["differ"] = list(d.get("differ") or []) + [("Q1", 17, "olx", 3.0, 5.0)]
        return d

    _scorer_case("the engines read one response to different scores",
                 lambda: setattr(_ENFX, "_interpretation_comparison",
                                 _interp_with_a_difference),
                 lambda: setattr(_ENFX, "_interpretation_comparison", _real_interp),
                 want="ENGINES READ ONE RESPONSE DIFFERENTLY")

    _inverted_skips: list[tuple[str, str]] = []
    print("SELF-TEST — does the audit notice when a rule is removed?\n")
    if _AUDIT_WORKERS > 1:
        print(f"  *** PARALLEL ({_AUDIT_WORKERS} workers). This run is FAST and is "
              f"NOT a certifying run:\n      a measured, unexplained divergence "
              f"from the serial suite affects one case\n      (see _AUDIT_WORKERS). "
              f"Re-run with SELFTEST_WORKERS=1 to certify.\n")
    baseline = _selftest_baseline
    bad = 0
    # Per-case record for the vacancy report. Built from data the suite ALREADY
    # has -- a standalone auditor would re-run `enforcement_audit()` before and
    # after every case, and the audit takes minutes against a suite that is
    # already ~3 hours.
    _records = []
    for case in cases:
        label, want, item, found = case[0], case[1], case[2], case[3]
        # COLLECT THE CHILD HERE. `_audit_async` forked at the injection and the
        # parent has long since restored the table; this is where the findings
        # that child computed are read back. Resolving in case order drains the
        # pool in the order it was filled.
        found = _audit_resolve(found)
        inverted = case[4] if len(case) > 4 else False
        if found is not None:
            _keys = {_finding_key(f) for f in found}
            _records.append({
                "label": label, "want": want, "item": str(item),
                "inverted": bool(inverted), "skipped": False,
                "n_baseline": len(_baseline_keys), "n_found": len(_keys),
                "added": sorted("|".join(k) for k in (_keys - _baseline_keys))[:8],
                "removed": sorted("|".join(k) for k in (_baseline_keys - _keys))[:8],
            })
        if found is None:
            # An inverted case whose precondition was absent. It tests nothing,
            # and saying PASS here would be the failure mode this whole file
            # exists to prevent.
            _inverted_skips.append((label, f"{want} was not already firing, so a "
                                          f"blinding test would be vacuous"))
            continue
        hit = [f for f in found if f[0] == item and f[1] == want]
        ok = (not hit) if inverted else bool(hit)
        bad += not ok
        if inverted:
            got = "STILL FIRED" if hit else "went silent, as it must"
        else:
            got = hit[0][1] if hit else "NOTHING FIRED"
        print(f"  {'PASS' if ok else 'FAIL'}  {label:<28} -> {got}")
    # Against the BASELINE, not against zero. The corpus legitimately carries
    # declared divergences -- NR's CHARGE-ONCE PROBE GAP is one -- so counting
    # every finding as dirt reported "restored state is clean: False" and exited
    # 1 on a run where all 39 injections were detected and nothing was left
    # behind. A selftest that fails when it passes gets ignored, which is how the
    # arity bug survived in the first place.
    _final_findings = enforcement_audit()[0]
    clean = len(_final_findings)
    # WHICH ONES, NOT HOW MANY. This reported "restored state is clean: False (7
    # finding(s), baseline 4)" and nothing else, and that number cost an hour to
    # turn into a cause: three cases restored a dict with `d[k] = saved`, which
    # re-appends the key, and the order-sensitive migrated-table check then
    # reported a mismatch that never went away. The baseline KEYS were already
    # being collected a few hundred lines above for the vacancy report; naming
    # the difference here is free and turns a count into the answer.
    _new_findings = [f for f in _final_findings
                     if _finding_key(f) not in _baseline_keys]
    _gone_findings = ({k for k in _baseline_keys}
                      - {_finding_key(f) for f in _final_findings})

    # SKIPS ARE COUNTED, not just printed. A case that degrades to SKIP still
    # exists on paper and tests nothing, and until the count was made explicit it
    # scrolled past above a confident "49/49".
    skips = []
    if plain is None:
        # Now reachable only if the corpus has NO items outside the derive-path
        # branch at all, which the coverage checks report on their own.
        skips.append(("plain-path computed check",
                      "no item outside the derive-path branch to synthesise from"))
    if _site is None:
        skips.append(("shared rule names a verdict",
                      "no rule carries `{fail}` to inject into"))
    # An inverted case whose precondition vanished is a SKIP, and it joins the
    # counted list rather than printing on its own -- the whole point of that
    # list is that a case which tests nothing is not allowed to scroll past.
    # AN INVERTED SKIP IS ALREADY IN `cases`. `_scorer_case` appends
    # `(label, want, ANY_ITEM, None)` before returning, so `len(cases)` counts it;
    # adding it again through `skips` counted the SAME case twice and inflated
    # `total` by one. That is how SELFTEST_EXPECTED came to be 72 for a suite of
    # 71: the 64 -> 65 raise on 2026-09-05 added one for a case `len(cases)` was
    # already counting.
    #
    # It matters because this constant is a TWO-SIDED ratchet whose point is that
    # "fewer means a case was lost". An arithmetic that can quietly add one masks
    # exactly the loss it exists to catch -- and it did: the suite read
    # `72 of 72 expected` while one case tested nothing.
    #
    # So the conditional skips (`plain`, `_site`) are added -- they are NOT in
    # `cases` -- and the inverted skips are printed but not re-counted.
    _conditional_skips = list(skips)
    skips = skips + _inverted_skips
    for label, why in skips:
        print(f"  SKIP  {label:<28} -> {why}")

    # THE VACANCY REPORT. Beside the "N detected, M failed" line, not instead of
    # it: that line answers "did the right thing fire", this one answers "could
    # anything have fired at all". Both defects found on 2026-09-18 were invisible
    # to the first question and obvious to the second.
    _vac = _vacancy_report(_records, skips)
    _vacuous = [r for r in _vac if r["vacuous"]]
    try:
        import json as _json_v
        import paths as _paths_v
        _rec_path = _paths_v.OUT / "selftest_cases.json"
        _rec_path.parent.mkdir(parents=True, exist_ok=True)
        _rec_path.write_text(_json_v.dumps(_vac, indent=1))
        print(f"\n  per-case record -> {_rec_path}")
    except Exception as _e_v:                                  # pragma: no cover
        print(f"\n  per-case record NOT written: {_e_v}")
    print(f"  vacancy: {len(_vac)} cases, {len(_vacuous)} vacuous "
          f"(ratchet {SELFTEST_VACANT_MAX})")
    for _r in _vacuous:
        print(f"    VACUOUS  {_r['label'][:44]:<44} {_r['verdict'][:46]}")
    # A RATCHET, NOT A HARD FAIL. Failing on any vacancy would make the suite
    # permanently red for a reason nobody can fix: `plain-path computed check`
    # SKIPS by design when the corpus holds no item outside the derive-path
    # branch, and a corpus is not a defect. Failing on GROWTH catches the thing
    # that actually goes wrong -- a case quietly stopping testing, which is how
    # the neutrality case ran vacuous for an unknown period while the suite
    # printed `72 of 72 expected`.
    #
    # It may FALL freely: repairing a case should never require editing a budget.
    if len(_vacuous) > SELFTEST_VACANT_MAX:
        bad += 1
        print(f"\n  *** VACANCY ROSE: {len(_vacuous)} cases test nothing, against "
              f"SELFTEST_VACANT_MAX={SELFTEST_VACANT_MAX}. A case that stopped "
              f"testing is not a case. Repair it, or lower nothing -- the ratchet "
              f"only moves down.")
    elif len(_vacuous) < SELFTEST_VACANT_MAX:
        print(f"  vacancy fell below the ratchet: lower SELFTEST_VACANT_MAX to "
              f"{len(_vacuous)} so the gain is protected.")

    # A MOVED SOURCE IS A FAILURE, NOT AN INCONCLUSIVE RESULT. This printed
    # "(VOID -- source moved)" and went on to exit 0, which is how a run that
    # left `agreement.py` carrying its own reporter-crash injection reported
    # "70 of 70 expected" and stamped itself passed. Measured on a quiet tree,
    # 2026-09-14: one file changed at 17:02:28 and was never restored across
    # the remaining 29 minutes, while three other injected files were restored
    # correctly after it.
    #
    # Either cause deserves a non-zero exit. If something ELSE edited the tree,
    # the run proved nothing and must not be recorded as a pass. If a case
    # failed to restore its own injection, the tree is now broken in a way that
    # parses, imports and passes every audit -- the exact property the
    # reporter-crash case exists to demonstrate is dangerous.
    moved = _selftest_inputs_changed(_inputs)
    repaired = _selftest_repair(_snapshot) if moved else []
    if repaired:
        print(f"\n  *** REPAIRED {len(repaired)} file(s) a case mutated and did "
              f"not restore:\n      " + ", ".join(repaired)
              + "\n      The tree is as it was found. The run still FAILS: a case "
                "that does not\n      undo its own injection is a defect, not "
                "something to absorb.")
    if moved:
        print(f"\n  *** THE SOURCE MOVED UNDER THIS RUN, so this run FAILS. The "
              f"baseline was taken\n      against different files, so \"restored "
              f"state\" below compares two states\n      that were never "
              f"comparable. Either something else edited the tree -- re-run it\n"
              f"      on a quiet one -- or a case did not restore its own "
              f"injection.")
        for f in moved:
            print(f"        changed: {f}")
    print(f"\n  restored state is clean: {clean == baseline}"
          f"{' (FAILED -- source moved, see above)' if moved else ''} "
          f"({clean} finding(s), baseline {baseline})")
    for _f in _new_findings:
        print(f"      LEFT BEHIND: {str(_f)[:150]}")
    for _k in sorted(_gone_findings):
        print(f"      NO LONGER FIRING: {str(_k)[:150]}")

    # THE DENOMINATOR DOES NOT FLOAT. It used to be `len(cases)`, so a case that
    # stopped being CONSTRUCTED took the denominator down with it and reported
    # success: 48/48 and 49/49 are indistinguishable at a glance. That is not
    # hypothetical -- the `SLOT RULE NAMES A VERDICT` case hard-coded an injection
    # site that a later conversion removed, and the whole suite died before its
    # first case while nothing said a case was missing.
    #
    # A two-sided ratchet, like HANDCODED_BUDGET and the rest: built + skipped
    # must equal SELFTEST_EXPECTED exactly. Fewer means a case was lost; more
    # means one was added and the constant was not raised, which leaves room for
    # a later loss to hide inside the slack.
    built = len(cases)              # includes inverted skips, which hold found=None
    detected = built - bad
    total = built + len(_conditional_skips)
    print(f"  {detected} detected, {bad} failed, {len(skips)} skipped, "
          f"{total} of {SELFTEST_EXPECTED} expected.")
    # STAMP THE PASS. measured.selftest_owed reads this file's mtime against
    # enforcement.py and equivalence.py, so a change to the checks that has not
    # been re-tested shows up in `measured.py --preflight` instead of relying on
    # anyone remembering. Written only on a CLEAN, COMPLETE run: a suite that
    # lost a case or failed one has not established anything to stamp.
    short = total != SELFTEST_EXPECTED
    # NOT STAMPED IF THE TREE MOVED. `measured.selftest_owed` reads this file's
    # mtime to decide whether the checks have been re-tested, so stamping a run
    # that damaged the tree records a pass that never happened.
    if not bad and not short and not moved:
        try:
            (_pl.Path(__file__).resolve().parent / ".selftest-passed").write_text(
                f"{detected} detected, 0 failed, {total} of {SELFTEST_EXPECTED}\n")
        except OSError:
            pass
    if short:
        verb = "LOST" if total < SELFTEST_EXPECTED else "GAINED"
        print(f"\n  *** THE SUITE {verb} {abs(total - SELFTEST_EXPECTED)} CASE(S): "
              f"{total} constructed or skipped against SELFTEST_EXPECTED="
              f"{SELFTEST_EXPECTED}. "
              + ("A case that stops being built reports success -- find it, or "
                 "lower the constant deliberately with the reason."
                 if total < SELFTEST_EXPECTED else
                 "Raise SELFTEST_EXPECTED so the new case is protected too."))
    # Against the baseline here too. `clean` is a COUNT, so `or clean` made a
    # fully passing selftest exit 1 whenever the corpus carried its one declared
    # divergence -- the same off-by-a-baseline the message above already fixed,
    # left behind in the exit code where it was less visible.
    return 1 if (bad or clean != baseline or short or moved) else 0


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
    # A declaration may name an (item, kind) the enforcement probe cannot reach,
    # as opposed to a difference in what the two sides DO. Without this the audit
    # never reads clean again, and a permanently dirty audit is how the next real
    # drift goes unnoticed -- the whole value of this output is that empty means
    # nothing moved.
    # BOTH TABLES. SCORING_DIVERGENCES excuses a real difference in what the two
    # sides DO; PROBE_REACH_LIMITS excuses a rule neither instrument can
    # cross-check, which is a different claim and now lives in its own table.
    excused = {tuple(e) for d in list(SCORING_DIVERGENCES) + list(PROBE_REACH_LIMITS)
               for e in (d.get("enforcement") or [])
               if isinstance(e, (list, tuple)) and len(e) == 2}
    for item, kind, detail in findings:
        if (item, kind) in excused:
            print(f"  {item:<5} {kind:<24} {detail}  [DECLARED]")
    findings = [f for f in findings if (f[0], f[1]) not in excused]
    # A RECORDING GAP IS NOT AN UNDECLARED DIFFERENCE, and counting it as one
    # contradicted the check that produces it.
    # `check_scored_slots_are_answered_by_both_engines` ratchets on its UNDECLARED
    # findings only -- `undeclared = [x for x in out if "RECORDING gap" not in x]`,
    # budget 0 -- because a recording gap is a documented fact about the ARTIFACTS
    # (the derived verdict is not written back; the charge still lands) and is
    # meant to stay visible without reading as an unexplained scoring difference.
    # This audit was counting all fourteen, so enforcement said 0 undeclared and
    # equivalence said fourteen about the same measurement.
    documented = [f for f in findings if "RECORDING gap" in f[2]]
    findings = [f for f in findings if "RECORDING gap" not in f[2]]
    # PARKED: known, not now. Still computed, still printed, but without the
    # `! ` prefix -- so it neither counts as undeclared nor blocks a commit.
    # See enforcement.PARKED_UNDECLARED for why this is not a declaration.
    parked = [f for f in findings if (f[0], f[1]) in ENF.PARKED_UNDECLARED]
    findings = [f for f in findings if (f[0], f[1]) not in ENF.PARKED_UNDECLARED]
    for item, kind, detail in documented:
        print(f"  {item:<5} {kind:<24} {detail}  [DOCUMENTED]")
    for item, kind, detail in parked:
        print(f"  {item:<5} {kind:<24} {detail}  [PARKED]")
    # A park that silences nothing is a park that will silence the NEXT thing to
    # appear under that key, unseen. Reported where the live finding set is.
    live = {(f[0], f[1]) for f in parked}
    for key in sorted(k for k in ENF.PARKED_UNDECLARED if k not in live):
        print(f"! {key[0]:<5} {'PARK MATCHES NOTHING':<24} "
              f"PARKED_UNDECLARED{list(key)} silences a finding that no longer "
              f"occurs -- unpark it")
    for item, kind, detail in findings:
        print(f"! {item:<5} {kind:<24} {detail}")
    print(f"{'  nothing flagged' if not findings else ''}")
    print(f"\n{len(findings)} UNDECLARED enforcement difference(s)"
          + (f"; {len(parked)} PARKED" if parked else "") + "; "
          f"{len(SCORING_DIVERGENCES)} declared in olx_prompts.SCORING_DIVERGENCES"
          f"{f'; {len(documented)} documented recording gap(s)' if documented else ''}.")
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
    print(ENF.engine_rate_power_line())
    print(ENF.engine_scoring_agreement_line())
    print(ENF.engine_interpretation_line())
    print(ENF.paper_scorer_agreement_line())
    print(ENF.paper_reproduces_web_line())
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
    ap.add_argument("--fixture", metavar="ITEM[:PID]",
                    help="read a cell out box by box: the response with its parts "
                         "and sentences, then every box with its position, what "
                         "no box holds, and the audit flags. The procedure that "
                         "found the defects three automated checks passed. Any "
                         "item on any handout; a cell answered with a chart or a "
                         "table has no prose to locate a box in, so its boxes are "
                         "printed by PROVENANCE instead.")
    ap.add_argument("--selftest", action="store_true",
                    help="with --enforcement: break each rule and check the audit notices")
    a = ap.parse_args()

    # A FLAG READ ONLY INSIDE ANOTHER MODE'S BRANCH IS A SILENT NO-OP.
    # `--selftest` is honoured at `if a.enforcement:` below and nowhere else, so
    # on its own it fell through to the default prompt audit and EXITED 0 -- a
    # suite that never ran, reported at the shell exactly like one where all 49
    # injections were detected. That is the worst place in this tree for a silent
    # no-op, because the self-test is what certifies every other check, and it was
    # used to "verify" a change on the strength of that exit code.
    #
    # An ERROR, not an implied --enforcement: the two modes cost different amounts
    # of time, and someone who typed one and got the other should be told rather
    # than accommodated.
    if a.selftest and not a.enforcement:
        ap.error("--selftest only runs with --enforcement: "
                 "`equivalence.py --enforcement --selftest`. On its own it would "
                 "silently run the default prompt audit and exit 0, which is "
                 "indistinguishable from a passing self-test.")

    # NOT WHILE A MEASUREMENT IS RUNNING. The self-test injects breakages into
    # rubric_h*.py, enforcement.py and olx_prompts.py and restores them, so for
    # the fifteen minutes it runs those files intermittently hold text nobody
    # wrote -- and agreement.py builds its prompts from the rubric on every call.
    # A sweep overlapping this scores some cells against an injected rule and
    # says nothing.
    #
    # This was a convention, not a guard: "wait for the self-test" is a thing a
    # person remembers. The project already has the same failure from the other
    # direction on record -- a mid-run OLX rewrite that split handout 3's
    # measurement and cost three items -- and that one earned
    # olx_prompts._measurements_in_flight. This is the same guard, pointed the
    # other way, reusing that function so there is one definition of "a sweep is
    # running".
    if a.selftest:
        import os as _os
        import olx_prompts as _OP
        busy = _OP._measurements_in_flight()
        if busy:
            why = _os.environ.get("ALLOW_SELFTEST_OVERLAP", "").strip()
            if not why:
                print("REFUSING to run the self-test: a measurement is in flight,\n"
                      "and this test injects breakages into the rubric and "
                      "enforcement source\nthat measurement reads live.")
                for b in busy:
                    print(f"    {b}")
                print('Wait for it to finish, or say why:\n'
                      '    ALLOW_SELFTEST_OVERLAP="..." python3 equivalence.py '
                      '--enforcement --selftest')
                return 2
            print(f"self-test: proceeding during a measurement — {why}")

    if a.fixture:
        # The box-by-box readout. Not a check — the PROCEDURE the checks cannot
        # replace: three of the four Q6 cells needing a structural rewrite were
        # found by reading them out and by nothing else.
        import enforcement as _ENF
        item, _, pid = a.fixture.partition(":")
        for p in ([int(pid)] if pid else range(1, 21)):
            print(_ENF.fixture_readout(item, p))
            print()
        return 0

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
