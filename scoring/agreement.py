"""Measure the lo-blocks formative prompts against the graders' gold rows.

The scorer in this directory measures ITS OWN prompts. This measures a
different system: the LLM feedback prompts authored in
~/code/lo-blocks/content/psychology/bmod_handout{1,2,3}.olx, which is what
students actually meet on screen. Those prompts were calibrated by transfer
from this project's findings, and until now nothing checked whether the
transfer worked.

What makes the comparison possible is that those prompts now declare their
checks as a `slots` sheet (a strict JSON schema), so the model returns a
machine-comparable verdict object rather than prose. This harness:

  1. reads each slot-bearing <LLMAction> straight out of the .olx — prompt
     text, slot sheet and verdict vocabulary, no copy of it kept here, so the
     thing measured is the thing shipped;
  2. fills its <Ref> placeholders from a paper submission, segmented by the
     same segment.py the scorer uses;
  3. sends it with its schema to the SAME endpoint the browser calls, so the
     provider and model are the ones students get;
  4. derives a score from the returned verdicts using the rubric's own point
     values — mirroring derive_ledger()/derive_oc_ledger() in score.py;
  5. compares that score with the grader's, in the table shape baseline.py
     uses, so the two systems' numbers sit side by side.

Step 4 deserves a note: the student-facing blocks must never score, and they
do not. Scoring happens HERE, in the measurement harness, because a score is
the only thing gold gives us to compare against.

Run:
    cd <edu.memphis.psych>/scoring
    python3 agreement.py --handout 1                 # Q6
    python3 agreement.py --handout 2                 # the 8 example items
    python3 agreement.py --handout 2 --items PR NR
    python3 agreement.py --handout 1 --backend cli   # via claude CLI instead

Quota, measured rather than assumed: the lo-blocks server rate-limits per user,
but its session layer mints a FRESH guest identity for every request that
arrives without a session cookie. A scripted run is therefore a new user each
call, so neither the 20 rpm limit nor the token budget ever accumulates against
it — verified by watching data/kvs/dev-local/rate/ gain one bucket per call.

Two consequences. The budget will not stop a long run, so `--workers` is the
only thing pacing it; keep it low anyway, because the provider is real and the
spend is real. And every call leaves a rate bucket behind in the KVS, which is
litter rather than a problem — a full handout 2 run adds ~144 of them.

The QuotaExhausted guard below is kept for the case where this is ever pointed
at an authenticated session, where the budget WOULD bind. If it ever fires, the
run stops rather than printing a plausible-looking table over half the cohort.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import simulate_h3
from handouts import (config, exemplar_drops, find_submissions, gold_ceiling,
                      suspect)
from segment import repair_orphans, segment
import paths

OLX_DIR = str(paths.OLX_DIR)
PRIMITIVES_JSON = paths.PRIMITIVES_JSON

# The primitive registry, read rather than mirrored. This file is consumer 5,
# added after three separate drifts survived here at once behind a docstring
# claiming to mirror buildSlotSchema(). What it needs from the registry is which
# primitives take keys OUT of the response schema, and whether the keys removed
# are the rule's own key or the members it stands in for.
with open(PRIMITIVES_JSON) as _fh:
    PRIMITIVES = json.load(_fh)["primitives"]

# What apply_computed() and score_slots() between them know how to work out
# without asking the model. A schema-excluding primitive missing from here would
# be silently left in the schema, which is the exact failure this file is being
# fixed for — so it raises instead.
COMPUTABLE = {"counts", "equals", "derived"}
LO_ENDPOINT = "http://localhost:8888/api/llm/chat/completions"

# A ref whose paper text has already been shown under an earlier ref in the
# same prompt. The web version splits several answers across two fields
# (antecedent 1 / antecedent 2); this corpus stores each answer as one block,
# so the block goes in the first slot and the second says where it went. This
# is the one place the measured prompt differs from the shipped one.
CONTINUED = "(continued above — this corpus stores the whole answer as one block)"


# ── Which web block corresponds to which rubric item ────────────────────────
#
# `item` is the rubric id in rubric_hN.py (so gold and the response text come
# from there). `refs` maps a lo-blocks field id, as it appears in a <Ref
# target=...>, onto the segmented section that supplies its text.

_H1_CTX = {
    "bmod_h1_utb": "Q1",
    "bmod_h1_q1_response": "Q1",
    "bmod_h1_q2_response": "Q2",
    # The five SMART boxes are one blob on paper; the first ref takes it and the
    # rest say so (see CONTINUED).
    "bmod_h1_q3_specific": "Q3", "bmod_h1_q3_measurable": "Q3",
    "bmod_h1_q3_action": "Q3", "bmod_h1_q3_realistic": "Q3",
    "bmod_h1_q3_timebound": "Q3",
    "bmod_h1_q4a_first": "Q4a", "bmod_h1_q4a_second": "Q4a",
    "bmod_h1_q4b_first": "Q4b", "bmod_h1_q4b_second": "Q4b",
    "bmod_h1_q4b_modify": "Q4b",
    "bmod_h1_q4c_first": "Q4c", "bmod_h1_q4c_second": "Q4c",
    "bmod_h1_q5_first": "Q5", "bmod_h1_q5_second": "Q5",
    "bmod_h1_q6_first": "Q6", "bmod_h1_q6_second": "Q6",
}

_H2_CTX = {
    "bmod_h1_utb": "_utb",
    "bmod_h1_q2_response": "_wgb",
    "bmod_h2_t1": "T1", "bmod_h2_d1": "D1",
    "bmod_h2_t2": "T2", "bmod_h2_d2": "D2",
    "bmod_h2_pr": "PR", "bmod_h2_nr": "NR",
    "bmod_h2_pp": "PP", "bmod_h2_np": "NP",
    "bmod_h2_day1": "DAY1", "bmod_h2_wk1": "WK1",
    "bmod_h2_day2": "DAY2", "bmod_h2_wk2": "WK2",
}

# A value of the form "hN:ITEM" comes from a DIFFERENT handout's submission by
# the same participant. Handout 3's assessment item asks the student to reflect
# on the operant-conditioning types they chose back in handout 2, and on paper
# those live in a different file.
_H3_CTX = {
    "bmod_h3_baseline": "1b", "bmod_h3_wk1": "1b",
    "bmod_h3_wk2": "1b", "bmod_h3_wk3": "1b",
    "bmod_h3_overview_response": "1a",
    "bmod_h3_success_verdict": "2a", "bmod_h3_success_how1": "2a",
    "bmod_h3_success_how2": "2a",
    "bmod_h3_assessment_response": "2b",
    "bmod_h3_improve_first": "3", "bmod_h3_improve_second": "3",
    "bmod_h3_graph_title": "1c", "bmod_h3_graph_x": "1c", "bmod_h3_graph_y": "1c",
    "bmod_h2_t1": "h2:T1", "bmod_h2_t2": "h2:T2",
    "bmod_h1_q2_response": "h1:Q2",
}


def _h1(item, action):
    return {"item": item, "olx": "bmod_handout1.olx", "refs": _H1_CTX, "kind": "slots"}


BLOCKS: dict[int, dict[str, dict]] = {
    1: {
        f"bmod_h1_{a}_llm": _h1(i, a)
        for i, a in (("Q1", "q1"), ("Q2", "q2"), ("Q3", "q3"), ("Q4a", "q4a"),
                     ("Q4b", "q4b"), ("Q4c", "q4c"), ("Q5", "q5"), ("Q6", "q6"))
    },
    2: {
        f"bmod_h2_{k.lower()}_llm": {
            "item": k, "olx": "bmod_handout2.olx", "refs": _H2_CTX,
            "kind": "oc", "expected_type": k,
        }
        for k in ("PR", "NR", "PP", "NP")
    } | {
        f"bmod_h2_{k.lower()}_llm": {
            "item": k, "olx": "bmod_handout2.olx", "refs": _H2_CTX,
            "kind": "oc_cadence",
            "cadence": "daily" if k.startswith("DAY") else "weekly",
        }
        for k in ("DAY1", "WK1", "DAY2", "WK2")
    } | {
        f"bmod_h2_{k.lower()}_llm": {
            "item": k, "olx": "bmod_handout2.olx", "refs": _H2_CTX, "kind": "slots",
        }
        for k in ("D1", "D2")
    } | {
        # T1 and T2 have no LLM call on the web either — they are DerivedChecks
        # sheets, `type_stated:present:bmod_h2_tN` — so there is no prompt here
        # to measure. They are scored anyway, deterministically, for the same
        # reason 1b is: they are scored items with a gold column, and omitting
        # them left handout 2 reported over ten items of twelve while the web
        # reported all twelve.
        f"_{k.lower()}_deterministic": {
            "item": k, "olx": None, "refs": {}, "kind": "type_stated",
        }
        for k in ("T1", "T2")
    },
    3: {
        "bmod_h3_overview_llm": {"item": "1a", "olx": "bmod_handout3.olx",
                                 "refs": _H3_CTX, "kind": "slots"},
        "bmod_h3_success_llm": {"item": "2a", "olx": "bmod_handout3.olx",
                                "refs": _H3_CTX, "kind": "slots"},
        "bmod_h3_assessment_llm": {"item": "2b", "olx": "bmod_handout3.olx",
                                   "refs": _H3_CTX, "kind": "slots"},
        "bmod_h3_improve_llm": {"item": "3", "olx": "bmod_handout3.olx",
                                "refs": _H3_CTX, "kind": "slots"},
        # Item 1c, scored on all five of its slots, out of 10 — the same sheet
        # the app grades, so the two columns need no rescaling to be compared.
        #
        # This used to take a 3-slot, 6-point label subtotal, on the reasoning
        # that the web supplies the graph and the legend itself and so cannot
        # fail `has_own_graph` or `legend`. It can, and does: over 17 web cells
        # `has_own_graph` returned `absent` twice and `legend` failed four times.
        # Dropping them measured the CLI on an easier item — including hiding a
        # false `legend` deduction the web made on p11 — and left the sides on
        # different scales. What IS unreachable on the web is the specific paper
        # failure of the three participants in GRAPH_UNREACHABLE_1C, who are
        # excluded here exactly as agreement_app.py excludes them.
        "bmod_h3_graph_llm": {"item": "1c", "olx": "bmod_handout3.olx",
                              "refs": _H3_CTX, "kind": "slots"},
        # Item 1b has no LLM call in the web version and should not have one:
        # it scores one point per week of data present, and four filled boxes is
        # a fact about the fields, not a judgement about prose. It is measured
        # here anyway, deterministically from the reconstructed fields, because
        # it is a scored item with a gold column and leaving it out would mean
        # claiming handout 3 was covered when five items of six were.
        "_1b_deterministic": {"item": "1b", "olx": None,
                              "refs": {}, "kind": "data_presence"},
    },
}


# ── Reading the shipped prompt ───────────────────────────────────────────────

_LLM_ACTION = re.compile(r"<LLMAction\b[^>]*?>.*?</LLMAction>", re.S)
_REF = re.compile(r'<Ref\b[^>]*?/>', re.S)
# The .olx parser drops comments; this reader has to as well. Each handout's
# header comment contains the sentence "EVERY <LLMAction> PROMPT BODY IN THIS
# FILE IS GENERATED", and that prose mention matched as an element whose body
# then ran to the first REAL closing tag — swallowing the first action in every
# one of the three files (Q1, PR, 1a). Because they became unfindable rather
# than mis-parsed, `load_action` exited loudly instead of measuring the wrong
# thing, which is the only reason this was ever recoverable.
_COMMENT = re.compile(r"<!--.*?-->", re.S)


def _fmt(v) -> str:
    """A score, or a dash — a missing gold row is not a zero."""
    return f"{v:.2f}" if isinstance(v, (int, float)) else "  -  "


def load_action(olx_file: str, action_id: str) -> dict:
    """Pull one <LLMAction> out of the .olx: prompt body, slots, verdicts."""
    path = os.path.join(OLX_DIR, olx_file)
    with open(path) as fh:
        src = _COMMENT.sub("", fh.read())
    for el in _LLM_ACTION.findall(src):
        open_tag = re.match(r"<LLMAction\b[^>]*?>", el, re.S).group(0)
        if f'id="{action_id}"' not in open_tag:
            continue
        slots_m = re.search(r'slots="([^"]*)"', open_tag, re.S)
        if not slots_m:
            raise SystemExit(f"{action_id} has no slots= attribute; nothing to measure")
        verd_m = re.search(r'verdicts="([^"]*)"', open_tag, re.S)
        body = el[len(open_tag):].rsplit("</LLMAction>", 1)[0]
        return {
            "body": body,
            "slots": parse_slots(
                slots_m.group(1),
                [v.strip() for v in (verd_m.group(1) if verd_m else "met,absent,unclear").split(",") if v.strip()],
            ),
            "equals": parse_equals(open_tag),
            "derived": parse_derived(open_tag),
            "cover": parse_cover(open_tag),
            "excluded": excluded_keys(open_tag),
            # The runtime keys per-check notes and the display guidance off this,
            # so a harness that ignores it measures a different prompt and a
            # different schema from the one the student meets.
            "show_checks": 'showChecks="false"' not in open_tag,
        }
    raise SystemExit(f"no <LLMAction id=\"{action_id}\"> in {path}")



# ── The computed primitives, as the web computes them ────────────────────────
#
# `equals` and `derived` answer their own checks, so the web strips their keys
# from the response schema and fills them in itself. This harness sent the
# SHIPPED prompt — which says "DO NOT ANSWER `matches_chosen_type`" — beside a
# schema that made it required, and a model resolves that in the schema's
# favour. Measuring the thing shipped means computing them here too.

def excluded_keys(open_tag: str) -> set[str]:
    """Keys the web removes from the response schema, per the registry.

    Raises rather than guessing: a new schema-excluding primitive that this
    harness cannot compute must stop the run, not quietly leave its keys in the
    schema for the model to answer against a prompt that forbids it.
    """
    out: set[str] = set()
    for prim in PRIMITIVES:
        if not prim.get("excludesKeys"):
            continue
        attr = prim["attr"]
        m = re.search(r'\b%s="([^"]*)"' % re.escape(attr), open_tag, re.S)
        if not m:
            continue
        if attr not in COMPUTABLE:
            raise SystemExit(
                f"primitives.json declares `{attr}` as removing keys from the "
                f"schema, and {os.path.basename(__file__)} cannot compute it. "
                f"Teach apply_computed() how, then add it to COMPUTABLE."
            )
        for rule in (r.strip() for r in m.group(1).split("|")):
            if not rule:
                continue
            parts = rule.split(":")
            if prim.get("excludes") == "members":
                out |= {k.strip() for k in parts[1].split(",")} if len(parts) > 1 else set()
            else:
                out.add(parts[0].strip())
    return out


def parse_equals(open_tag: str) -> list[dict]:
    """`equals="key:left,right[:lenient,...]"`, '|'-separated."""
    m = re.search(r'equals="([^"]*)"', open_tag, re.S)
    out = []
    for rule in (r.strip() for r in (m.group(1) if m else "").split("|")):
        if not rule:
            continue
        parts = rule.split(":")
        if len(parts) < 2:
            continue
        ops = [o.strip() for o in parts[1].split(",") if o.strip()]
        if len(ops) != 2:
            continue
        out.append({"key": parts[0].strip(), "left": ops[0], "right": ops[1],
                    "lenient": [v.strip() for v in parts[2].split(",")] if len(parts) > 2 else []})
    return out


def parse_cover(open_tag: str) -> list[dict]:
    """`cover="keyA,keyB:labelA,labelB"`, '|'-separated.

    Mirrors parseCover() in packages/shared/lib/llm/slotSheet.ts. A cover group
    says the slots in it are answered as a SET: the model reports only which of
    the referenced answers each box names, and whether the pair covered both is
    arithmetic, not a verdict. Without this the flat "verdict == options[0]"
    rule scores `second` — the expected answer for the second box — as a miss.
    """
    m = re.search(r'cover="([^"]*)"', open_tag, re.S)
    out = []
    for rule in (r.strip() for r in (m.group(1) if m else "").split("|")):
        if not rule:
            continue
        parts = rule.split(":")
        if len(parts) < 2:
            continue
        keys = [k.strip() for k in parts[0].split(",") if k.strip()]
        labels = [l.strip() for l in parts[1].split(",") if l.strip()]
        if keys and labels:
            out.append({"keys": keys, "labels": labels})
    return out


def parse_derived(open_tag: str) -> list[dict]:
    """`derived="key:kind:field[,field][:template]"`, '|'-separated."""
    m = re.search(r'derived="([^"]*)"', open_tag, re.S)
    out = []
    for rule in (r.strip() for r in (m.group(1) if m else "").split("|")):
        if not rule:
            continue
        parts = rule.split(":")
        if len(parts) < 3:
            continue
        out.append({
            "key": parts[0].strip(), "kind": parts[1].strip(),
            "fields": [f.strip() for f in parts[2].split(",") if f.strip()],
            "template": [[float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", row)]
                         for row in parts[3].split(";")] if len(parts) > 3 else [],
        })
    return out


def _nums(text: str) -> list[float]:
    return [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", text or "")]


def apply_computed(action: dict, checks: dict, fixture: dict) -> dict:
    """Fill the checks the web computes, in the web's order: derived, then equals.

    `equals` reads other checks, so it runs last — and it must tolerate an
    operand the model left blank, which is what `lenient` is for.
    """
    by_key = {s["key"]: s for s in action["slots"]}
    opts = lambda k: (by_key.get(k) or {}).get("options") or ["met", "absent"]

    for rule in action.get("derived", []):
        # Field id -> section -> text, the same indirection build_prompt uses.
        # Reading `texts[field_id]` directly misses every time, and a miss here is
        # invisible: an absent field looks exactly like an empty one, so the check
        # fails, the slot loses its points, and the run still reports a number. It
        # cost `utb_stated` on all 17 Q1 cells before this raised instead.
        vals = []
        for f in rule["fields"]:
            if f not in fixture:
                raise CallFailed(
                    f"derived `{rule['key']}` reads field {f!r}, which the "
                    f"reconstruction does not produce. Add it to this item's JOBS "
                    f"entry, or the check silently scores unmet on every cell."
                )
            vals.append(str(fixture.get(f, "") or ""))
        if rule["kind"] == "present":
            ok = all(v.strip() for v in vals)
            v, why = (("met", "Answered.") if ok else ("absent", "Nothing chosen here."))
        elif rule["kind"] in ("plots", "complete"):
            got = [_nums(v) for v in vals]
            empty = sum(1 for g in got if not g)
            if rule["kind"] == "complete" and 0 < empty < len(got):
                v = "absent"
                why = f"{empty} of the {len(got)} weeks hold no data"
            elif not any(got):
                v, why = "absent", "no numbers, so nothing plots"
            elif rule["template"] and got == rule["template"]:
                v, why = "mismatch", "this is the worked example's own data"
            else:
                v, why = "met", f"{sum(len(g) for g in got)} value(s) plotted"
        else:
            continue                      # an unknown kind computes nothing
        checks[rule["key"]] = {"verdict": v, "evidence": why}

    for rule in action.get("equals", []):
        left = verdict_of(checks, rule["left"]).strip()
        right = verdict_of(checks, rule["right"]).strip()
        ok = (left in rule["lenient"] or right in rule["lenient"]
              or (bool(left) and bool(right) and left == right))
        o = opts(rule["key"])
        checks[rule["key"]] = {
            "verdict": o[0] if ok else (o[1] if len(o) > 1 else "no"),
            "evidence": f"{rule['left']}={left or '?'}, {rule['right']}={right or '?'}",
        }
    return checks


def parse_slots(spec: str, defaults: list[str]) -> list[dict]:
    """Same grammar as lib/llm/slotSheet.ts: key:Label[:o1/o2][@pts], '|'-separated.

    The `@pts` suffix comes off the END first, exactly as parseSlots() does it.
    This did not, so a slot written `matches_chosen_type:...:yes/no@2` parsed its
    options as ["yes", "no@2"] — and those options ARE the schema's enum, so the
    model was offered `"no@2"` as the legal way to say no on 35 slots across ten
    items. Scoring only ever tested "is it the first option", which is why it
    stayed invisible.
    """
    out = []
    for entry in (e.strip() for e in spec.split("|")):
        if not entry:
            continue
        at = re.search(r"@(-?\d+(?:\.\d+)?)\s*$", entry)
        if at:
            entry = entry[:at.start()].strip()
        parts = [p.strip() for p in entry.split(":")]
        key = parts[0]
        gates = key.startswith("!")
        key = key[1:].strip() if gates else key
        opts = parts[2].split("/") if len(parts) > 2 and parts[2] else defaults
        opts = [o.strip() for o in opts if o.strip()]
        if key and len(opts) > 1:
            slot = {"key": key, "label": parts[1] if len(parts) > 1 else key,
                    "options": opts, "gates": gates}
            if at:
                slot["pts"] = float(at.group(1))
            out.append(slot)
    return out


def fixture_for(item: str, pid: int) -> dict[str, str]:
    """The reconstructed field values, from the SAME code the app harness uses.

    agreement_app.build_jobs() turns one paper block into the separate boxes the
    web version asks for — by label, by anchored scorer evidence, by a frozen
    consensus table, by a hand-read split where no rule was good enough — and
    seeds the cross-item context refs besides. This harness used to do none of
    that: it mapped every field of an item onto the SAME section and wrote
    "(continued above ...)" into all but the first, so a three-box item showed the
    model two empty boxes and was marked down for them.

    Importing it rather than reimplementing it is the point. A second
    reconstruction would be a second thing to keep in step, and every hand-kept
    mirror in this project has drifted at least once.
    """
    import agreement_app as AA
    try:
        return AA.build_jobs(item, [pid])[0]["fixture"]
    except SystemExit as e:      # a missing consensus/handsplit row for ONE cell
        raise CallFailed(f"no reconstruction for p{pid}/{item}: {e}") from e


def build_prompt(body: str, fixture: dict[str, str]) -> str:
    """Substitute every <Ref> with its own reconstructed field value.

    An unmapped target RAISES. It used to render "(not collected on the paper
    version)", which reads like a fact about the corpus and was really a lookup
    that missed — Q6's sheet grew from two boxes to eight, the map kept the two,
    and all 17 cells scored 0 with no failure reported.
    """
    def fill(m: re.Match) -> str:
        target = re.search(r'target="([^"]*)"', m.group(0))
        if not target:
            return ""
        key = target.group(1)
        if key not in fixture:
            raise CallFailed(
                f"<Ref target={key!r}> has no reconstructed value. Add it to this "
                f"item's JOBS entry in agreement_app.py — rendering a placeholder "
                f"scores the check unmet on every cell instead of saying so."
            )
        return (fixture.get(key) or "").strip() or "(left blank)"

    text = html.unescape(_REF.sub(fill, body))
    return re.sub(r"\n[ \t]+", "\n", text).strip()


def _guidance_block(fn_name: str) -> str:
    """One guidance function's text, lifted from slotSheet.ts."""
    ts = _ts_source()
    m = re.search(rf"function {fn_name}\b.*?return \[(.*?)\]\.join", ts, re.S)
    if not m:
        raise SystemExit(f"{fn_name}() not found in {paths.SLOTSHEET_TS} — "
                         "the mirror in agreement.checklist_guidance is stale")
    parts = re.findall(r"'((?:[^'\\]|\\.)*)'", m.group(1))
    return "\n".join(x.replace("\\'", "'") for x in parts)


def checklist_guidance(show_checks: bool) -> str:
    """Mirror of slotSheetGuidance() in slotSheet.ts, read from the source.

    LLMAction appends this to every slot-sheet prompt (DEVIATION 7). Two parts,
    and only one is conditional:

      studentFacingGuidance  ALWAYS — spell out the rubric's abbreviations and
                             keys, because the student has not read the rubric.
      checklistGuidance      only when the student SEES the checks — one note
                             per check, capped at two sentences.

    Composed in the same order the runtime composes it: the text is prompt, so
    order is part of what is being measured.
    """
    out = _guidance_block("studentFacingGuidance")
    # Both branches carry a block; the hidden one is not "nothing", it is the
    # length budget that the checklist's own structure supplies when shown.
    out += _guidance_block("checklistGuidance" if show_checks
                           else "terseFeedbackGuidance")
    return out


def _ts_source() -> str:
    try:
        return open(paths.SLOTSHEET_TS).read()
    except OSError as e:                       # pragma: no cover - config error
        raise SystemExit(f"cannot read {paths.SLOTSHEET_TS}: {e}")


def _ts_literal(which: str, per_check_notes: bool = True) -> str:
    """Lift a schema description straight out of slotSheet.ts.

    A copy kept here is the thing that drifts — three times so far, each found
    by chasing a score rather than by looking. The descriptions are INSTRUCTION,
    so a paraphrase is a different prompt; reading the source means this harness
    cannot describe a schema the app does not send.

    Fails loudly rather than falling back to a copy: a silent fallback would
    restore exactly the drift this removes.
    """
    ts = _ts_source()
    if which == "note":
        m = re.search(r"note:\s*\{.*?description:\s*\n?\s*(.*?),\n\s*\},", ts, re.S)
    else:
        m = re.search(r"feedback:\s*\{.*?description:\s*(.*?),\n\s*\},", ts, re.S)
    if not m:
        raise SystemExit(f"could not read the `{which}` description from "
                         f"{paths.SLOTSHEET_TS} — the mirror in build_schema is stale")
    blob = m.group(1)
    if which == "feedback":
        # `feedback` is a ternary on perCheckNotes: take the arm the web takes.
        arms = re.split(r"\n\s*:\s*", blob, maxsplit=1)
        blob = arms[0] if per_check_notes else (arms[1] if len(arms) > 1 else arms[0])
        blob = re.sub(r"^\s*perCheckNotes\s*\n?\s*\?", "", blob)
    parts = re.findall(r"'((?:[^'\\]|\\.)*)'", blob)
    if not parts:
        raise SystemExit(f"no string literal in the `{which}` description")
    return "".join(p.replace("\\'", "'") for p in parts)


def build_schema(slots: list[dict], exclude: set[str] = frozenset(),
                 per_check_notes: bool = False) -> dict:
    """Mirror of buildSlotSchema() in lib/llm/slotSheet.ts.

    `exclude` is the keys a schema-excluding primitive answers, which the web
    removes so the model is never asked for them. Leaving them in contradicts
    the prompt: the generated body carries "DO NOT ANSWER `how_1`, `how_2`
    individually" while the schema makes them required, and a model resolves
    that in the schema's favour. On 2a that cost two cells — the model counted
    two explanations where the web, asked only to count, found one.

    This function called itself a mirror of buildSlotSchema() while taking one
    argument where that takes four, which is the rot primitives.json exists to
    stop; it did not stop it because this file is a FIFTH consumer and the
    registry lists four.
    """
    slots = [s for s in slots if s["key"] not in exclude]
    props = {
        s["key"]: {
            "type": "object",
            "properties": {
                "verdict": {"type": "string", "enum": s["options"]},
                # The description is not decoration — it is instruction the web
                # has been sending and this side has not, so the two have been
                # asking the model for subtly different things. It matters most
                # for a check whose correct answer is "not there": the web gives
                # absence somewhere to be justified, and this side gave it none.
                # Suspected while measuring Q2's `wgb_is_counterpart`, a gate the
                # web fired on p7 in 2 published runs of 2 and this side fired in
                # 1 of 8. equivalence.py cannot catch this: it compares prompt
                # TEXT, and a schema is not text.
                "evidence": {
                    "type": "string",
                    "description": "Quote from the student, or what you looked "
                                   "for and did not find",
                },
            },
            "required": (["verdict", "evidence", "note"] if per_check_notes
                         else ["verdict", "evidence"]),
            "additionalProperties": False,
        }
        for s in slots
    }
    # Fourth instance of the same drift, caught by the schema audit again. When
    # the student SEES the checklist the web asks for a per-check `note` and
    # re-describes `feedback` as an opening; sending the old single-paragraph
    # schema here would measure a system we no longer ship.
    if per_check_notes:
        for s in slots:
            props[s["key"]]["properties"]["note"] = {
                "type": "string", "description": _ts_literal("note"),
            }
    return {
        "type": "object",
        "properties": {
            "checks": {
                "type": "object",
                "properties": props,
                "required": [s["key"] for s in slots],
                "additionalProperties": False,
            },
            # Third instance of the same drift, and this one was found BY the new
            # schema audit rather than by chasing a score — which is the argument
            # for having it. "Consistent with the checks above" is the instruction
            # that ties the prose to the verdicts; without it this side asked for
            # feedback that need not agree with what it just decided.
            "feedback": {
                "type": "string",
                "description": _ts_literal("feedback", per_check_notes),
            },
        },
        "required": ["checks", "feedback"],
        "additionalProperties": False,
    }


# ── Backends ─────────────────────────────────────────────────────────────────

class QuotaExhausted(RuntimeError):
    """The endpoint refused for budget reasons — the run cannot continue."""


class CallFailed(RuntimeError):
    pass


class LoBlocksBackend:
    """Post to the dev server, exactly as the browser does.

    This is the default because it is the only path that measures what students
    get: the same route, provider, model and schema enforcement.
    """

    name = "lo-blocks endpoint (what the browser calls)"

    def __init__(self, endpoint: str = LO_ENDPOINT, timeout: int = 240):
        self.endpoint = endpoint
        self.timeout = timeout
        self.calls = 0

    def complete(self, prompt: str, schema: dict, retries: int = 6) -> dict:
        # 6, not 3: the endpoint intermittently returns an empty body, which
        # parse_json_object raises on and this loop retries. At the observed
        # rate 3 was not enough to clear an 18-cell item — NR, DAY1 and WK1 each
        # lost a cell, and a lost cell is worse than a slow one because it
        # leaves the item's rates computed over a biased subset.
        payload = json.dumps({
            "messages": [{"role": "user", "content": prompt}],
            "tools": [],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "feedback_checks", "strict": True, "schema": schema},
            },
        }).encode()

        last: Exception | None = None
        for attempt in range(retries + 1):
            req = urllib.request.Request(
                self.endpoint, data=payload,
                headers={"Content-Type": "application/json"},
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    env = json.loads(resp.read())
                self.calls += 1
                content = env["choices"][0]["message"]["content"]
                return parse_json_object(content)
            except urllib.error.HTTPError as e:
                detail = e.read().decode(errors="replace")[:300]
                # Budget exhaustion is terminal; a rate limit is not.
                if e.code == 429 and "budget" in detail.lower():
                    raise QuotaExhausted(detail) from None
                last = CallFailed(f"HTTP {e.code}: {detail}")
                if e.code == 429 and attempt < retries:
                    time.sleep(min(2 ** attempt * 5 + 2, 45))
                    continue
                if attempt < retries:
                    # Capped: doubling unchecked, the 6th retry alone would
                    # sleep 64s, so a dead cell would cost two minutes of the
                    # run before it was declared dead.
                    time.sleep(min(2 ** attempt * 2, 30))
                    continue
            except Exception as e:  # network, timeout, malformed envelope
                last = CallFailed(str(e))
                if attempt < retries:
                    # Capped: doubling unchecked, the 6th retry alone would
                    # sleep 64s, so a dead cell would cost two minutes of the
                    # run before it was declared dead.
                    time.sleep(min(2 ** attempt * 2, 30))
                    continue
        raise last if last else CallFailed("unknown failure")


class CliBackend:
    """The claude CLI, for measuring the prompts without the dev server.

    Useful to separate "is the prompt good" from "is gpt-5-mini good at it",
    but note it is NOT what students get — different model, and the schema is
    enforced by a different mechanism.
    """

    name = "claude CLI (not the student path)"

    def __init__(self):
        from backends import ClaudeCliBackend
        self.inner = ClaudeCliBackend()

    @property
    def calls(self) -> int:
        return self.inner.calls

    def complete(self, prompt: str, schema: dict) -> dict:
        return self.inner.complete("", prompt, schema)


def parse_json_object(text: str) -> dict:
    """Same tolerance as parseJsonObject() in reduxClient.tsx."""
    body = (text or "").strip()
    if body.startswith("```"):
        body = re.sub(r"^```[a-zA-Z]*\s*", "", body)
        body = re.sub(r"\s*```$", "", body)
    for candidate in (body, (re.search(r"\{.*\}", body, re.S) or type("m", (), {"group": lambda s, i: ""})()).group(0)):
        if not candidate:
            continue
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue
    raise CallFailed(f"no JSON object in response: {text[:200]!r}")


# ── Verdicts → score, using the rubric's own point values ────────────────────

def verdict_of(checks: dict, key: str) -> str:
    got = checks.get(key)
    return (got or {}).get("verdict", "") if isinstance(got, dict) else ""


def satisfied_map(spec: dict, checks: dict) -> dict[str, bool]:
    """Which slots are satisfied. Mirrors satisfiedMap() in slotSheet.ts.

    Outside a cover group a slot passes on its own first verdict. Inside one the
    labels are handed out greedily in the group's key order, so the pair earns
    both slots whichever way round it answered, naming the same label twice
    earns only the first claimant, and a verdict outside the group's labels
    (`neither`, `absent`) earns nothing.

    The flat rule alone is wrong for a grouped slot and was wrong here: Q6's
    `state_a2` lists its verdicts `first/second/neither/absent`, so `second` —
    the answer the prompt says to expect from the second box — read as a miss,
    docking 2.50 from every participant who paired their antecedents correctly.
    """
    out = {s["key"]: verdict_of(checks, s["key"]) == s["options"][0]
           for s in spec["slots"]}
    for g in spec.get("cover") or []:
        claimed = set()
        for k in g["keys"]:
            v = verdict_of(checks, k).strip()
            ok = v in g["labels"] and v not in claimed
            if ok:
                claimed.add(v)
            out[k] = ok
    return out


def score_slots(spec: dict, item: dict, checks: dict) -> tuple[float, int]:
    """Uniform slot sheet: one unmet component, one deduction.

    Slots are bound to credit components BY NAME — an authored slot key must
    equal the component's `what` in rubric_hN.py. That coupling is deliberate:
    if someone renames or drops a slot in the .olx, this raises instead of
    quietly scoring the item against four checks where the rubric has five.

    A gating slot has no credit component of its own. It stands for a rubric
    code worth the whole item (a goal behaviour that is a different behaviour,
    a definition correct for the wrong type, an overview that never separates
    any periods), so failing it is 0 and the rest is moot — the same shape as
    derive_ledger()'s `gates`.
    """
    by_key = {s["key"]: s for s in spec["slots"]}

    gate_sat = satisfied_map(spec, checks)
    for slot in spec["slots"]:
        if slot.get("gates") and not gate_sat[slot["key"]]:
            return 0.0, 1

    # A counted family is answered ONCE, so the members carry no verdict of their
    # own and the counter carries no points. Expand here exactly as derive_ledger
    # does — the first N members met, the rest absent — or this scores the members
    # against a verdict the model was told not to give, and reads `pts` off a
    # counter that has none.
    #
    # That second failure was live and quiet: it only raises when the count is
    # BELOW the maximum, so every cell it dropped was one where the student was
    # short — the exact cells the count exists to measure. The runner says the
    # rates are over a biased subset, which is the only reason it surfaced.
    checks = dict(checks)
    counted = set()
    for cr in item.get("counts", []):
        counted.add(cr["key"])
        raw = verdict_of(checks, cr["key"]).strip()
        try:
            n = int(raw)
        except ValueError:
            n = 0
        for i, key in enumerate(cr["slots"]):
            opts = (by_key.get(key) or {}).get("options") or ["met", "absent"]
            # score.py writes the literal "met"/"absent"; here only "is it the
            # first option" is asked, so the miss just has to differ from it.
            checks[key] = {"verdict": opts[0] if i < n else "absent"}

    # Recomputed, not reused from the gate pass: the counted expansion above
    # rewrote those members' verdicts, and this is what the points are read off.
    sat = satisfied_map(spec, checks)

    lost, failed = 0.0, 0
    for comp in item["credit"]:
        if comp["what"] in counted:
            continue                      # the count itself carries no points
        # A component with no `pts` is an operand, not a scored check: D1's
        # `defines_type`/`named_type` exist so `matches_chosen_type` can compare
        # them, and the .olx gives them no `@n`. scoreSlotSheet() charges only
        # `slots.filter(s => typeof s.pts === 'number')`, so this must too.
        #
        # Charging them was a live crash, not a rounding difference. Their
        # verdicts are `PR/NR/PP/NP/unclear`, so the first-verdict rule reads
        # every student who did not pick PR as having missed the check, and
        # `lost += comp["pts"]` then raised KeyError on None — taking out 7 of
        # D1's 18 cells, and precisely the ones that chose a different type.
        if comp.get("pts") is None:
            continue
        slot = by_key.get(comp["what"])
        if slot is None:
            raise CallFailed(
                f"item {item['id']}: the .olx sheet has no slot named {comp['what']!r} "
                f"(it has {sorted(by_key)}). Slot keys must match the rubric's "
                f"credit component names."
            )
        if not sat[slot["key"]]:
            failed += 1
            lost += comp["pts"]
    return max(0.0, min(item["max"], item["max"] - lost)), failed


def score_oc(spec: dict, item: dict, checks: dict) -> tuple[float, int]:
    """The four 'write an example of X' items.

    Mirrors derive_oc_ledger(): the definitional criteria gate everything — fail
    any and the answer is not operant conditioning whatever it looks like — then
    the type is checked, and an avoidance frame never deducts.
    """
    yes = lambda k: verdict_of(checks, k) == "yes"
    codes = {d["code"]: d["pts"] for d in item["deductions"]}

    is_oc = yes("names_behavior") and yes("names_stimulus") and yes("contingent") and yes("follows_behavior")
    if not is_oc:
        return max(0.0, item["max"] - codes["NOT_OC"]), 1
    if not yes("you_arrange_it"):
        return max(0.0, item["max"] - codes["NOT_EXTERNAL_STIMULUS"]), 1

    observed = verdict_of(checks, "observed_type")
    aimed_key = "targets_goal_behavior" if "targets_goal_behavior" in {s["key"] for s in spec["slots"]} \
        else "targets_unwanted_behavior"
    if observed != spec["expected_type"]:
        return max(0.0, item["max"] - codes["WRONG_TYPE"]), 1
    if not yes(aimed_key):
        return max(0.0, item["max"] - codes["WRONG_TYPE"]), 1
    return item["max"], 0


def score_oc_cadence(spec: dict, item: dict, checks: dict) -> tuple[float, int]:
    """The daily/weekly example items — as above plus cadence, and the type is
    whatever the student chose rather than a fixed one."""
    yes = lambda k: verdict_of(checks, k) == "yes"
    codes = {d["code"]: d["pts"] for d in item["deductions"]}

    is_oc = yes("names_behavior") and yes("names_stimulus") and yes("contingent") and yes("follows_behavior")
    if not is_oc:
        return max(0.0, item["max"] - codes["NOT_OC"]), 1
    if not yes("you_arrange_it"):
        return max(0.0, item["max"] - codes["NOT_EXTERNAL_STIMULUS"]), 1

    cadence_key = "cadence_is_daily" if spec["cadence"] == "daily" else "cadence_is_weekly"
    if not yes(cadence_key):
        return max(0.0, item["max"] - codes["CADENCE_MISMATCH"]), 1

    lost = 0.0
    n = 0
    if not yes("matches_chosen_type"):
        lost += codes["TYPE_MISMATCH"]
        n += 1
    if not yes("targets_own_behavior"):
        lost += codes["WRONG_BEHAVIOR"]
        n += 1
    # The item's fourth point, previously reachable only by a gate. `scoreSlotSheet`
    # charges this automatically from the sheet's `@1`, so omitting it here would
    # make the two sides score the same verdicts differently — the exact class of
    # divergence this harness exists to detect.
    if "consequence_asserted" in {s["key"] for s in spec["slots"]} \
            and not yes("consequence_asserted"):
        lost += codes["LINK_NOT_ASSERTED"]
        n += 1
    return max(0.0, min(item["max"], item["max"] - lost)), n


SCORERS = {"slots": score_slots, "oc": score_oc, "oc_cadence": score_oc_cadence}

# Items scored over a subset of the paper item's points. Empty since 1c moved to
# its full five slots; kept because the mechanism is the honest way to declare a
# subtotal, and a future item may need one. Anything added here must also be
# declared on the web side, or the two columns silently stop being comparable.
MAX_OVERRIDE: dict[tuple[str, str], float] = {}


# ── The run ──────────────────────────────────────────────────────────────────

_SECTION_CACHE: dict[tuple[int, int], dict[str, str]] = {}


def sections_for(handout: int, pid: int) -> dict[str, str]:
    """Segment one participant's submission for one handout, memoised.

    Memoised because a full run segments the same file once per item, and
    because a handout-3 prompt may reach back into handout 2.
    """
    hit = _SECTION_CACHE.get((handout, pid))
    if hit is not None:
        return hit
    found = dict(find_submissions(handout, [pid]))
    if pid not in found:
        _SECTION_CACHE[(handout, pid)] = {}
        return {}
    cfg = config(handout)
    sec = segment(found[pid], cfg["template"], cfg["markers"], cfg["capture_tail"],
                  cfg.get("join_aware", False))
    if cfg.get("repair_orphans"):
        sec, _ = repair_orphans(sec, [i["id"] for i in cfg["rubric"].ITEMS])
    _SECTION_CACHE[(handout, pid)] = sec
    return sec


# The web version's handout-3 fields, recovered from the paper submission by
# simulate_h3. Keyed by the lo-blocks field id, because that is what a <Ref>
# names. This replaces a lossy approximation: the four weekly data fields used
# to resolve to one 1b blob with the other three saying "continued above", which
# is not what a student's screen looks like and reads to a model as though the
# weeks were all present.
_SIM_FIELDS = {
    "bmod_h3_baseline": "baseline",
    "bmod_h3_wk1": "week_1",
    "bmod_h3_wk2": "week_2",
    "bmod_h3_wk3": "week_3",
    "bmod_h3_graph_title": "graph_title",
    "bmod_h3_graph_x": "graph_x_axis",
    "bmod_h3_graph_y": "graph_y_axis",
}


def gather_texts(handout: int, pid: int, refs: dict[str, str]) -> dict[str, str]:
    """Resolve every section a prompt's refs point at, across handouts.

    Keys come back exactly as they appear in `refs` values, so "Q4a" and
    "h2:T1" both work and build_prompt needs no special case.
    """
    out: dict[str, str] = {}
    for key in set(refs.values()):
        head, sep, name = key.partition(":")
        if sep and head.startswith("h") and head[1:].isdigit():
            src_handout, section = int(head[1:]), name
        else:
            src_handout, section = handout, key
        out[key] = (sections_for(src_handout, pid).get(section) or "").strip()
    return out


def apply_simulation(refs: dict[str, str], texts: dict[str, str], sim: dict) -> tuple[dict, dict]:
    """Point handout-3 refs at the reconstructed field values.

    Returns refs and texts keyed so each simulated field is its OWN section —
    no CONTINUED collapsing, because in the web version these really are
    separate boxes the student filled in separately.
    """
    refs = dict(refs)
    texts = dict(texts)
    for field_id, sim_key in _SIM_FIELDS.items():
        if field_id not in refs:
            continue
        key = f"sim:{sim_key}"
        refs[field_id] = key
        texts[key] = (sim["fields"].get(sim_key) or "").strip()
    return refs, texts


WEEK_FIELDS = ("baseline", "week_1", "week_2", "week_3")


def usable_values(raw: str) -> int:
    """How many plottable numbers a field holds.

    Mirrors parseSeries() in SelfMonitorPlot: split on whitespace, commas or
    semicolons, keep the finite numbers. Written to match the component rather
    than to be independently sensible, because the point of this item is to
    measure what the web version does, not what a reasonable check would do.
    """
    tokens = [t for t in re.split(r"[\s,;]+", raw or "") if t]
    n = 0
    for t in tokens:
        try:
            v = float(t)
        except ValueError:
            continue
        if v == v and v not in (float("inf"), float("-inf")):
            n += 1
    return n


def measure_data_presence(handout: int, spec: dict, pid: int) -> dict:
    """Item 1b, scored without a model: one point per week of data present.

    "Present" is the component's own notion — at least one plottable number, per
    usable_values above — so this measures the check SelfMonitorPlot actually
    performs rather than a stricter one invented here.

    A week recorded as zeros is data and scores; a week never provided is not.
    The reconstruction is careful to keep those apart, which is what makes p15
    (baseline written as "none", one week never typed) and p18 (nothing at all)
    the two rows that discriminate on this item.
    """
    item = config(handout)["rubric"].BY_ID[spec["item"]]
    sim = simulate_h3.load_all().get(pid)
    if sim is None:
        raise CallFailed(f"no reconstruction for p{pid}; run simulate_h3.py first")
    fields = sim["fields"]
    checks = {w: ("met" if usable_values(fields.get(w) or "") > 0 else "absent")
              for w in WEEK_FIELDS}
    present = sum(1 for v in checks.values() if v == "met")
    return {
        "participant_id": pid,
        "item": spec["item"],
        "score": float(present),          # 1 point per week, max 4
        "max": item["max"],
        "failed_slots": len(WEEK_FIELDS) - present,
        "checks": checks,
        "feedback": "(deterministic check — no model call)",
        "response_chars": sum(len((fields.get(w) or "").strip()) for w in WEEK_FIELDS),
    }


# "I plan to use:" — and participant 9's "I pan to use:", which is the reason
# this is a pattern rather than a literal. The stem is the handout's own wording
# and carries no type name, so removing it is what separates "answered" from
# "left the line as printed".
_TYPE_STEM = re.compile(r"^\s*i\s+p\w*n\s+to\s+use\s*:?", re.I)
_TYPE_NAMED = re.compile(
    r"\b(positive|negative)\s+(reinforcement|punishment)\b|\b(pr|nr|pp|np)\b", re.I)


def measure_type_stated(handout: int, spec: dict, pid: int) -> dict:
    """Items T1 and T2, scored without a model: did the student name a type?

    The web asks this as a closed ChoiceInput and derives `type_stated` with the
    `present` primitive — the field is either filled from the four Keys or it is
    empty, so `not_a_type` cannot arise there. On paper the same question is a
    blank line after "I plan to use:", where it can, so this reports all three
    verdicts and lets the rubric's own codes separate BLANK from NOT_A_TYPE.

    Deterministic on purpose. The parallel to the web is not "send this to a
    model too" — the web does not — it is "derive it from the field the same
    way", which is also what makes T1/T2 comparable at all.
    """
    item = config(handout)["rubric"].BY_ID[spec["item"]]
    raw = (sections_for(handout, pid).get(spec["item"]) or "").strip()
    # Underscores become spaces BEFORE matching, not just before the residue
    # test: `_` is a word character, so `\bnegative` does not match participant
    # 20's transcribed "_Negative punishment" and a named type reads as blank.
    body = _TYPE_STEM.sub("", raw).replace("_", " ").strip()
    # Underscores and stray punctuation are transcription artefacts of the blank
    # line itself (participant 20 wrote "_Positive Reinforcement"), not an answer.
    residue = re.sub(r"[\s_.:;,–—-]+", "", body)

    if _TYPE_NAMED.search(body):
        verdict = "met"
    elif not residue:
        verdict = "absent"
    else:
        verdict = "not_a_type"

    return {
        "participant_id": pid,
        "item": spec["item"],
        "score": item["max"] if verdict == "met" else 0.0,
        "max": item["max"],
        "failed_slots": 0 if verdict == "met" else 1,
        "checks": {"type_stated": verdict},
        "feedback": "(deterministic check — no model call)",
        "response_chars": len(body),
    }


def measure_one(backend, handout: int, spec: dict, action_id: str, path: str, pid: int) -> dict:
    cfg = config(handout)
    item = cfg["rubric"].BY_ID[spec["item"]]

    if spec["kind"] == "data_presence":
        return measure_data_presence(handout, spec, pid)
    if spec["kind"] == "type_stated":
        return measure_type_stated(handout, spec, pid)

    action = load_action(spec["olx"], action_id)
    # Handout 3 no longer needs its own branch: build_jobs applies the simulation
    # for the items that declare one, along with every other reconstruction.
    fixture = fixture_for(spec["item"], pid)
    prompt = build_prompt(action["body"], fixture) + checklist_guidance(action["show_checks"])
    raw = backend.complete(prompt, build_schema(action["slots"], action["excluded"],
                                                action["show_checks"]))
    checks = apply_computed(action, raw.get("checks") or {}, fixture)

    merged = dict(spec, slots=action["slots"], cover=action["cover"])
    score, n_failed = SCORERS[spec["kind"]](merged, item, checks)
    return {
        "participant_id": pid,
        "item": spec["item"],
        "score": round(score, 2),
        "max": MAX_OVERRIDE.get((str(handout), spec["item"]), item["max"]),
        "failed_slots": n_failed,
        "checks": {s["key"]: verdict_of(checks, s["key"]) for s in action["slots"]},
        "feedback": raw.get("feedback", ""),
        "response_chars": len((sections_for(handout, pid).get(spec["item"]) or "").strip()),
    }


# Gold criteria that neither system scores, declared rather than left to be
# rediscovered. An omission that is SYMMETRIC costs the head-to-head nothing —
# both columns miss it identically — but an undeclared one is indistinguishable
# from a bug, which is the whole reason this list exists.
#
#   1c, "missing baseline data week" (p11, -1): the only instance in 20 rows,
#   and unreachable on the web by construction. The chart is drawn by
#   SelfMonitorPlot from the four data fields, so a populated baseline series is
#   necessarily plotted — p11's `baseline` field holds "{{corpus:1a/p6:baseline:0:19:sha=66e4f9120272}} 30",
#   which is why their 1b scored a full 4.0. The grader is marking a series
#   absent from a hand-drawn paper graph whose data table contained it. Adding a
#   slot for it would have no reachable failing state: with baseline data present
#   the web always plots it, and with baseline data absent 1b already takes the
#   point, so the slot could only double-count or misfire. Note also that p11's
#   row does not self-reconcile — it itemises -2/-2/-1 against a score of 7.0 —
#   so rebuild_gold_1c derives from the itemised deductions, not the total.
# Cells where the gold row cannot be scored on the item it sits in, dropped from
# that item only. Mirrors PER_ITEM_EXCLUDE in agreement_app.py; the two sides
# must drop the SAME cells or the item's two columns stop being a comparison.
PER_ITEM_EXCLUDE: dict[str, dict[int, str]] = {
    "Q6": {
        9: "the eight-box fixture for this cell is arbitrary, and it is the SAME "
           "arbitrary fixture on both sides: fixture_for() imports "
           "agreement_app.build_jobs, so this harness feeds its prompt the frozen "
           "q6_consensus table rather than building its own split — verified "
           "byte-identical. p9 tied 5/5 across ten runs on state_c2 and affect_c2, "
           "so the vote had to break the tie, and the break put the text in "
           "state_c2 and left affect_c2 empty. That decides 2 of the 8 slots — 2.5 "
           "of 10 points — before the model reads anything, and the CLI's error "
           "here is exactly -2.50. Measuring either side on it measures the "
           "tie-break. Also one of the four documented gold divergences "
           "(A_MISMATCH on state_a1). Both reasons are side-agnostic, which is why "
           "the web-only exclusion this mirrors was incomplete.",
    },
    "Q4c": {
        16: "gold 3.0 for \"did not say if this behavior is a good choice for you "
            "modify and why\" — but the handout asks that under 4b, which has its "
            "own `Modify:` field and carries modify_stated/modify_why for 3 of "
            "its 5 points. 4c asks only for two consequences plus the keyword. "
            "The deduction is misfiled: p16's Q4b row is a clean 5.0, so the "
            "point was taken off the wrong item. No correct 4c scorer can reach "
            "3.0 here, and both systems return 5.0.",
    },
    "1c": {
        4: "gold 0 (\"Did not provide a graph\") but all four weeks of data "
           "supplied — on the web that data DRAWS the chart, so the paper "
           "failure is unreachable rather than missed",
        19: "the same: gold 0 for no graph, four complete weeks of data",
        20: "the same failure in its third form — a written DESCRIPTION of a "
            "graph, which on the web IS the answer: the labels are typed into "
            "fields and the chart is drawn from the four complete weeks",
    },
}

# Derived from PER_ITEM_EXCLUDE, not repeated, so the two drops cannot disagree.
# Both are applied: the work list stops the call being made, and nulling the gold
# stops the row counting if the work-list drop is bypassed — which `--exclude`
# with explicit values does exactly.
#
# The distinction that matters: these three supplied four complete weeks of data,
# which on the web DRAWS the chart, so "Did not provide a graph" is unreachable.
# p15 and p18 are NOT here — their data is incomplete, the gate can and does fire
# on it, and the paper's zero transfers intact.
GRAPH_UNREACHABLE_1C = tuple(sorted(PER_ITEM_EXCLUDE["1c"]))

UNSCORED_GOLD_CRITERIA = {
    ("3", "1c"): "missing baseline data week (p11, -1) — the web draws the "
                 "chart from the data, so a present baseline series cannot be "
                 "absent from the graph; an absent one is already scored by 1b",
}


def gold_slots_1c(feedback: str) -> dict[str, bool]:
    """The grader's verdict on all five of 1c's slots, read out of their comment.

    Scored over the full 10 points, not the three labels. An earlier version
    took a 6-point label subtotal on the grounds that the web "cannot fail"
    has_own_graph or legend. Measurement says otherwise: across 17 web cells
    has_own_graph came back `absent` twice and legend failed four times
    (`absent` x3, `incomplete` x1) — and one of those, p11's legend, is a false
    deduction the CLI could not see because it was not scoring the slot. A
    subtotal that omits the item's only gate is an easier item, not a fairer
    comparison.

    A missing mention means the criterion passed: these graders itemise what
    they took off and leave the cell blank at full credit, so absence of
    "-2 pts: missing legend" is evidence the legend was there.
    """
    f = (feedback or "").lower()
    no_graph = "did not include" in f or "did not provide a graph" in f
    return {
        # The gate. On a no-graph row nothing else was assessed, so the other
        # four ride on it — which is what a gate means anyway.
        "has_own_graph": not no_graph,
        "title": not no_graph and "missing graph title" not in f,
        "x_axis_label": not no_graph and "missing x-axis" not in f,
        "y_axis_label": not no_graph and "missing y-axis" not in f,
        "legend": not no_graph and "missing legend" not in f,
    }


def rebuild_gold_1c(gold: dict) -> tuple[dict, list[int]]:
    """Restate gold's 1c score as the slot sheet's own five checks, out of 10.

    The workbook's raw 1c score cannot be used directly: p11's row reads
    `-2 x-axis -2 y-axis -1 missing baseline data week` against a score of 7.0,
    which is neither 10-5 nor 10-4, and the baseline-week point maps to no slot
    on either side. Deriving the score from the itemised deductions instead
    keeps gold on the same five criteria both systems actually report.

    Also reports which participants dropped out, so the run can say so instead
    of quietly measuring 17 rows and calling it 20.
    """
    dropped = []
    for pid, items in gold.items():
        cell = items.get("1c")
        if not cell:
            continue
        if pid in GRAPH_UNREACHABLE_1C:
            items["1c"] = {"score": None, "feedback": cell.get("feedback", "")}
            dropped.append(pid)
            continue
        slots = gold_slots_1c(cell.get("feedback"))
        # The gate takes the whole item, exactly as score_slots computes it.
        score = 0.0 if not slots["has_own_graph"] else \
            10.0 - 2.0 * sum(1 for ok in slots.values() if not ok)
        items["1c"] = {"score": score, "feedback": cell.get("feedback", "")}
    return gold, sorted(dropped)


def tolerance(item: dict) -> float:
    return min(c["pts"] for c in item["credit"] if c.get("pts") is not None)


def report(handout: int, results: list[dict], failures: list[tuple], gold: dict) -> int:
    cfg = config(handout)
    by_id = cfg["rubric"].BY_ID
    items = sorted({r["item"] for r in results}, key=lambda i: [x["id"] for x in cfg["rubric"].ITEMS].index(i))

    print(f"\nlo-blocks prompt agreement — handout {handout}\n")
    hdr = f"{'item':>6} {'max':>5} {'n':>3} {'exact':>7} {'±tol':>7} {'MAE':>6} {'bias':>7}"
    print(hdr)
    print("-" * len(hdr))

    all_abs, all_err = [], []
    disagreements = []
    for iid in items:
        item = by_id[iid]
        tol = tolerance(item)
        errs, exact, within = [], 0, 0
        for r in (x for x in results if x["item"] == iid):
            g = gold.get(r["participant_id"], {}).get(iid, {}).get("score")
            if g is None:
                continue
            e = r["score"] - g
            errs.append(e)
            all_err.append(e)
            all_abs.append(abs(e))
            if abs(e) < 1e-9:
                exact += 1
            if abs(e) <= tol + 1e-9:
                within += 1
            else:
                disagreements.append((abs(e), r["participant_id"], iid, g, r["score"]))
        if not errs:
            continue
        shown_max = MAX_OVERRIDE.get((str(handout), iid), item["max"])
        print(f"{iid:>6} {shown_max:>5.0f} {len(errs):>3} {exact/len(errs):>6.0%} "
              f"{within/len(errs):>6.0%} {statistics.mean(map(abs, errs)):>6.2f} "
              f"{statistics.mean(errs):>+7.2f}")

    print("-" * len(hdr))
    if all_abs:
        print(f"{'ALL':>6} {'':>5} {len(all_abs):>3} "
              f"{sum(1 for e in all_err if abs(e) < 1e-9)/len(all_err):>6.0%} {'':>6} "
              f"{statistics.mean(all_abs):>6.2f} {statistics.mean(all_err):>+7.2f}")

    # Slot detection: how many failed slots the prompt finds against how many
    # the grader's own arithmetic implies. This is the metric that moved when
    # the scorer put its checklist in the schema, so it is the one to watch.
    detect = [(r, gold.get(r["participant_id"], {}).get(r["item"], {}).get("score"))
              for r in results]
    def uniform(iid: str) -> bool:
        # Reported-only and gating components carry no `pts`; including them
        # would put None in the set and break every comparison against it.
        pts = {c["pts"] for c in by_id[iid]["credit"] if c.get("pts") is not None}
        return len(pts) == 1

    # "How many failed slots did it find" only converts cleanly to a count when
    # every component is worth the same; on Q1 (2,1,1,1) a 2-point loss is one
    # component or two, and the score alone cannot say which.
    pairs = [(r["failed_slots"], round((r["max"] - g) / tolerance(by_id[r["item"]])))
             for r, g in detect if g is not None and uniform(r["item"])]
    if pairs:
        print(f"\nFailed slots found: {sum(p for p, _ in pairs)} "
              f"of {sum(i for _, i in pairs)} the gold scores imply")

    if disagreements:
        print("\nLargest disagreements (beyond item tolerance):")
        for d, pid, iid, g, p in sorted(disagreements, reverse=True)[:12]:
            fb = (gold[pid][iid]["feedback"] or "").replace("\n", " ")[:80]
            print(f"  p{pid:<3} {iid:<5} gold {g:>5.2f} -> pred {p:>5.2f} ({p-g:+.2f})  gold said: {fb}")

    # Say what gold asked for that nothing here scores. Symmetric omissions do
    # not bias the comparison, but they do cap what an exact-match rate can
    # mean, and an unprinted one reads as full coverage.
    unscored = [(iid, why) for iid in items
                if (why := UNSCORED_GOLD_CRITERIA.get((str(handout), iid)))]
    if unscored:
        print("\nGold criteria not scored by either system (declared, not missed):")
        for iid, why in unscored:
            print(f"  {iid:>5}  {why}")

    # Why an item cannot reach 100%, printed with its rate so a ceiling is not
    # read as headroom. Q3 at 75% looks like 25% of work available; about half of
    # that does not exist, because gold decides the same claim both ways.
    ceilings = [(iid, why) for iid in items if (why := gold_ceiling(handout, iid))]
    if ceilings:
        print("\nMeasurement ceilings — gold does not decide these consistently "
              "(handouts.GOLD_CEILINGS):")
        # One line per ceiling, not per item: Q2 has two for unrelated reasons
        # and printing only the first would hide the other.
        for iid, whys in ceilings:
            for n, why in enumerate(whys):
                print(f"  {iid if n == 0 else '':>5}  {why.split('. ')[0]}.")

    # Never let a partial run read as a complete one.
    if failures:
        print(f"\n*** {len(failures)} cell(s) FAILED and are missing from the table above:")
        for pid, iid, err in failures[:10]:
            print(f"      p{pid} {iid}: {str(err)[:140]}")
        print("    The rates above are computed over a biased subset. Fix and re-run.")
        return 1
    print("\nunscored cells: 0")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__.split("Run:")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "The server's per-user quota does not bind here: an unauthenticated\n"
            "request gets a fresh guest identity each time, so every call starts a\n"
            "new bucket. Nothing will stop a long run except --workers, and the\n"
            "provider spend is real, so size runs deliberately.\n"
            "\n"
            "Each call leaves a rate bucket in the KVS. To clear the litter after a\n"
            "run (dev data only, and it resets those guests' windows):\n"
            "  find ~/code/lo-blocks/data/kvs/dev-local/rate -mindepth 1 -maxdepth 1 \\\n"
            "       -type d -newer <a-file-from-before-the-run> -exec rm -rf {} +\n"
            "\n"
            "If the budget ever DOES bind (an authenticated session), raise\n"
            "llm-token-budget in ~/code/lo-blocks/config/server.pmss and restart the\n"
            "server — .pmss is read once at startup.\n"
        ),
    )
    ap.add_argument("--handout", type=int, default=1, choices=sorted(BLOCKS))
    ap.add_argument("--backend", default="lo", choices=["lo", "cli"])
    ap.add_argument("--participants", type=int, nargs="*", default=None)
    ap.add_argument("--items", nargs="*", default=None,
                    help="Rubric item ids to measure (default: all measurable ones).")
    ap.add_argument("--workers", type=int, default=3,
                    help="The only thing pacing a run — the per-user quota does not "
                         "bind (see the epilog). Keep it low; the spend is real.")
    ap.add_argument("--out", default=None, help="Write per-cell JSON here.")
    ap.add_argument("--runs", type=int, default=3,
                    help="How many times to measure (default 3). Publishes the "
                         "MEDIAN run and prints the spread. This side is steadier "
                         "than the web — Q3 measured a 0.58-cell standard "
                         "deviation against the web's 2.08 — but steadier is not "
                         "steady: Q2 spanned 75-95%% over five runs and Q4b "
                         "75-88%%. Three runs each also puts the two columns of "
                         "the head-to-head on equal footing, which single-run-here "
                         "against median-of-three-there did not. `--runs 1` for a "
                         "quick look; its number should not be quoted.")
    ap.add_argument("--exclude", type=int, nargs="*", default=None,
                    help="Participants to drop (default: this handout's exemplar "
                         "and mis-transcribed rows, which cannot be measured honestly).")
    args = ap.parse_args()

    blocks = BLOCKS[args.handout]
    if not blocks:
        print(f"handout {args.handout} has no measurable slot-bearing prompts "
              f"(see BLOCKS in this file for why)", file=sys.stderr)
        return 1
    if args.items:
        blocks = {a: s for a, s in blocks.items() if s["item"] in set(args.items)}
        if not blocks:
            print(f"none of {args.items} are measurable on handout {args.handout}", file=sys.stderr)
            return 1

    drop = set(suspect(args.handout) if args.exclude is None else args.exclude)
    targets = [(pid, p) for pid, p in find_submissions(args.handout, args.participants)
               if pid not in drop]
    if drop:
        print(f"(excluding participants {sorted(drop)} — untrusted transcription)",
              file=sys.stderr)

    backend = LoBlocksBackend() if args.backend == "lo" else CliBackend()
    # Per-item drops are applied to the WORK LIST, not just to the metrics: a
    # cell nothing can score right is not worth an LLM call either, and leaving
    # it in the results would put it in the failure census.
    per_item = {} if args.exclude is not None else {
        (s["item"], pid): why
        for s in blocks.values()
        for pid, why in PER_ITEM_EXCLUDE.get(s["item"], {}).items()
    }
    if args.exclude is None:
        # Exemplar participants are dropped from the items whose prompt embeds
        # them, not from the whole handout — see exemplar_drops().
        ex = exemplar_drops(args.handout)
        for s in blocks.values():
            for pid in ex.get(s["item"], []):
                per_item.setdefault(
                    (s["item"], pid),
                    "their response is a few-shot exemplar in THIS item's prompt, "
                    "so scoring it would be self-grading")
    jobs = [(a, s, path, pid) for pid, path in targets for a, s in blocks.items()
            if (s["item"], pid) not in per_item]
    for (iid, pid), why in sorted(per_item.items()):
        print(f"(excluding p{pid} from {iid}: {why})", file=sys.stderr)
    print(f"measuring {len(blocks)} item(s) x {len(targets)} participant(s) "
          f"= {len(jobs)} calls via {backend.name}", file=sys.stderr)

    # Gold is loaded BEFORE the run so each cell can be reported as it lands.
    # Without this the only sign of life was a count every ten cells, and a run
    # that had already died looked identical to one still working — which is how
    # a three-day-dead shell and a crashed run both got reported as "in progress".
    gold = config(args.handout)["gold"]()
    dropped_1c = []
    if args.handout == 3:
        gold, dropped_1c = rebuild_gold_1c(gold)

    def one_pass() -> tuple[list[dict], list[tuple]]:
        results: list[dict] = []
        failures: list[tuple] = []
        stopped = False
        t0 = time.time()
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futs = {pool.submit(measure_one, backend, args.handout, s, a, path, pid): (pid, s["item"])
                    for a, s, path, pid in jobs}
            for fut in as_completed(futs):
                pid, iid = futs[fut]
                try:
                    r = fut.result()
                    results.append(r)
                    try:
                        g = gold.get(pid, {}).get(iid, {}).get("score")
                        print(f"  p{pid:<3} {iid:<5} gold={_fmt(g)} pred={_fmt(r.get('score'))}",
                              file=sys.stderr, flush=True)
                    except Exception:
                        pass
                except QuotaExhausted as e:
                    if not stopped:
                        stopped = True
                        print(f"\n*** token budget exhausted after {len(results)} cells: "
                              f"{str(e)[:120]}\n    Stopping — see --help for the two ways out.",
                              file=sys.stderr)
                    failures.append((pid, iid, "token budget exhausted"))
                except Exception as e:
                    failures.append((pid, iid, e))
                done = len(results) + len(failures)
                if done % 10 == 0:
                    print(f"  {done}/{len(jobs)}", file=sys.stderr)
        print(f"{backend.calls} calls in {time.time()-t0:.0f}s", file=sys.stderr)
        return results, failures

    passes = [one_pass()]
    for i in range(2, args.runs + 1):
        print(f"(run {i} of {args.runs})", file=sys.stderr)
        passes.append(one_pass())

    def exact_of(res: list[dict]) -> int:
        n = 0
        for r in res:
            g = gold.get(r["participant_id"], {}).get(r["item"], {}).get("score")
            if g is not None and abs(r["score"] - g) < 1e-9:
                n += 1
        return n

    # MEDIAN by exact count, ties to the lowest run index — the same rule as
    # agreement_app.py, and fixed in code for the same reason: picking a run after
    # seeing the numbers is how a best-of-three got published here once and read as
    # a 6-point difference between the two implementations that did not exist.
    order = sorted(range(len(passes)), key=lambda i: (exact_of(passes[i][0]), i))
    pick = order[len(order) // 2]
    results, failures = passes[pick]

    if args.runs > 1:
        counts = [exact_of(p[0]) for p in passes]
        spread = max(counts) - min(counts)
        cells = len([r for r in results
                     if gold.get(r["participant_id"], {}).get(r["item"], {}).get("score")
                     is not None]) or 1
        print(f"\n{args.runs} runs — exact "
              + ", ".join(f"{c}/{cells}" for c in counts)
              + f"   mean {statistics.fmean(counts):.1f}   spread {spread} cell(s)")
        print(f"publishing run {pick + 1} (median by exact count, ties to lowest index)")
        if spread:
            print(f"read the table below as +/-{spread} cell(s) "
                  f"({100 * spread / cells:.0f} points): a single run of these item(s) "
                  f"cannot resolve a difference smaller than that")

    if args.handout == 3:
        if dropped_1c:
            print(f"(item 1c: participants {dropped_1c} scored 0 on paper for "
                  f"providing no graph, but supplied four complete weeks of data, "
                  f"which on the web DRAWS the chart — the failure is unreachable "
                  f"rather than missed, so they are dropped from 1c only. p15 and "
                  f"p18 are kept: their data is incomplete and the gate does fire)",
                  file=sys.stderr)
    if args.out:
        with open(args.out, "w") as fh:
            json.dump({"handout": args.handout, "results": results,
                       "failures": [(p, i, str(e)) for p, i, e in failures]}, fh, indent=2)
        print(f"wrote {args.out}", file=sys.stderr)
        # Every run, not just the published one, so a per-slot firing rate on this
        # side is countable over a real denominator. The web gained this first and
        # the asymmetry mattered: its rates could only be read off medians while
        # this side stored one file per run, which is why a web/CLI difference in
        # how often Q2's `wgb_is_counterpart` fires could not be told from sampling.
        if args.runs > 1:
            stem = args.out[:-5] if args.out.endswith(".json") else args.out
            path_runs = f"{stem}.runs.json"
            with open(path_runs, "w") as fh:
                json.dump({
                    "handout": args.handout,
                    "rule": "median by exact count, ties to lowest index",
                    "published": pick + 1,
                    "runs": [{"run": i + 1, "exact": exact_of(p[0]),
                              "results": p[0],
                              "failures": [(a, b, str(c)) for a, b, c in p[1]]}
                             for i, p in enumerate(passes)],
                }, fh, indent=2)
            print(f"wrote {path_runs} ({len(passes)} runs)", file=sys.stderr)
    return report(args.handout, results, failures, gold)


if __name__ == "__main__":
    raise SystemExit(main())
