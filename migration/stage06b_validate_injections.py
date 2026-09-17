import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parent))
import migration_paths as MP
#!/usr/bin/env python3
"""Stage 06b · validate every selftest injection against the FULL audit.

WHY THIS EXISTS, AND IT IS NOT THE SAME AS PROBING THE CHECK. Each of the
sixteen cases added at 06b was first probed alone: install the breakage, call
the one check, confirm it fires. Every one passed. Three then broke the SUITE,
because a case does not call its check -- it calls `enforcement_audit()`, which
scores every item through both engines, and an injection has to leave the rubric
valid for all of that.

  * `{"key": ..., "of": [...]}` made `check_one_writer_per_computed_key` fire and
    then crashed the scorer on `rule["left"]` -- KeyError, 86 cases in.
  * the repaired rule needed a slot carrying `verdicts`; `state_a1` has `codes`
    and raised KeyError: 'verdicts'.
  * appending a credit row named `orphan_slot_zz` fired its own check and then
    took the audit down two cases later, because `agreement.score_slots` treats a
    rubric credit name with no matching sheet slot as a hard CallFailed.

Each cost a ~90-minute suite run to discover, one per run. This validates all
sixteen in one pass instead: install, run the WHOLE audit, report fired /
did-not-fire / crashed, restore. Run it after touching any injection and before
running the suite.

    python3 migration/stage06b_validate_injections.py
"""

import sys, traceback
sys.path.insert(0, str(MP.SCORING))
import handouts as H, enforcement as E, olx_prompts as O, score as SC, measured as M, paths as P
import equivalence as Q
import pathlib

R1, R3 = H.config(1)["rubric"], H.config(3)["rubric"]

def case(label, want, install, restore, inverted=False):
    try:
        base = [f for f in Q.enforcement_audit()[0]]
    except Exception as e:
        print(f"  BASE-CRASH {label}: {type(e).__name__}: {e}"); return
    install()
    try:
        found = [f for f in Q.enforcement_audit()[0]]
        hit = [f for f in found if f[1] == want]
        ok = (not hit) if inverted else bool(hit)
        print(f"  {'ok    ' if ok else 'NOFIRE'} {label}  ({len(hit)} hit)")
    except Exception as e:
        print(f"  CRASH  {label}: {type(e).__name__}: {str(e)[:110]}")
    finally:
        restore()

# "maps detach" RETIRED 2026-09-15 with the check it validated. 06c made
# `MAPS` a derivation of the per-item field, so detaching a map removed the
# declaration with it and `check_maps_tables_are_attached` could no longer
# disagree with itself. Its successor guards the class one layer up: an element
# authored in the rubric that `read_rubric` never matches.
cb = {}
def i1():
    import rubric_reader as _RR
    cb["was"] = _RR.CONSUMED_ELEMENTS
    _RR.CONSUMED_ELEMENTS = frozenset(_RR.CONSUMED_ELEMENTS | {"Rubbish"})
def r1():
    import rubric_reader as _RR
    _RR.CONSUMED_ELEMENTS = cb["was"]
case("rubric element unread", "RUBRIC ELEMENT IS NEVER READ", i1, r1)

it3 = next(i for i in R3.ITEMS if i.get("maps")); pr = it3["maps"][0]["pairs"]; bx = {}
case("map pair drop", "MAPPED SLOT HAS AN UNREACHABLE VERDICT",
     lambda: bx.__setitem__("p", pr.pop(2)), lambda: pr.insert(2, bx["p"]))

itc = R1.BY_ID["Q1"]; cs = {k: itc.get(k) for k in ("equals", "expect")}
def i3():
    itc["equals"] = list(itc.get("equals") or []) + [{"key":"utb_stated","left":"utb_stated","right":"utb_stated"}]
    itc["expect"] = list(itc.get("expect") or []) + [{"key":"utb_stated","left":"utb_stated","value":"absent"}]
def r3f():
    for k, v in cs.items(): itc.pop(k, None) if v is None else itc.__setitem__(k, v)
case("two writers", "TWO COMPUTED PRIMITIVES WRITE ONE KEY", i3, r3f)

q = R1.BY_ID["Q6"]; qs = q.get("question")
case("deixis", "PAPER PROMPT REFERS TO A BOX",
     lambda: q.__setitem__("question", str(qs) + " Answer in the box below."),
     lambda: q.__setitem__("question", qs))

rp = M.prompt_sha
case("paper sha", "PAPER PROMPT IS NOT STAMPED BY ITS OWN SHA",
     lambda: setattr(M, "prompt_sha", lambda i, s="olx", *a, **k: rp(i, "olx")),
     lambda: setattr(M, "prompt_sha", rp))

RD = P.SCORING / "RUBRIC_DECISIONS.md"; BK = RD.with_suffix(".md.selftest-bak")
case("decisions hidden", "RECORD HOOK BLIND TO AN ITEM",
     lambda: RD.rename(BK), lambda: BK.rename(RD))

case("stale deviation", "DECLARED DEVIATION OUTLIVED ITS TARGET",
     lambda: O.ITEM_NOTES.__setitem__("ZZ_no_such_item", "stale"),
     lambda: O.ITEM_NOTES.pop("ZZ_no_such_item", None))

a = [c for c in R1.BY_ID["Q6"]["credit"] if c["what"] == "state_a1"][0]; rs = a.get("rule")
case("process prose", "SHIPPED PROSE CARRIES OUR PROCESS",
     lambda: a.__setitem__("rule", "This slot was measured and reverted in a sweep; see the subgoal."),
     lambda: (a.pop("rule", None) if rs is None else a.__setitem__("rule", rs)))

real_sl = O._slots_attr; TGT = O.ACTION.get("Q1")
def sheet_wo(handout, action):
    spec, verd = real_sl(handout, action)
    if action == TGT:
        spec = "|".join(p for p in spec.split("|") if not p.startswith("utb_stated:"))
    return (spec, verd)
case("slot never reaches sheet", "RUBRIC SLOT NEVER REACHES THE SHEET",
     lambda: setattr(O, "_slots_attr", sheet_wo), lambda: setattr(O, "_slots_attr", real_sl))

cr = R1.BY_ID["Q6"]["credit"]; rb = {}
case("sheet asks, rubric dropped", "SHEET SLOT REACHES NO RUBRIC ELEMENT",
     lambda: rb.__setitem__("r", cr.pop(0)), lambda: cr.insert(0, rb["r"]))

cds = dict(a["codes"])
case("novel code (vocab)", "VERDICT ONE ENGINE CANNOT EXPRESS",
     lambda: a.__setitem__("codes", {**cds, "impossible_verdict": "X_NOVEL"}),
     lambda: a.__setitem__("codes", cds))
case("novel code (spaces)", "VERDICT SPACES DIVERGE UNDECLARED",
     lambda: a.__setitem__("codes", {**cds, "impossible_verdict": "X_NOVEL"}),
     lambda: a.__setitem__("codes", cds))

k = sorted(SC.PAPER_ITEM_NOTES)[0]
case("side note both sides", "A SIDE NOTE IS NOT SIDE-SPECIFIC",
     lambda: O.ITEM_NOTES.__setitem__(k, SC.PAPER_ITEM_NOTES[k]),
     lambda: O.ITEM_NOTES.pop(k, None))

dk = ("Q6", "state_a1", "desc"); ds = E.DESIGNED_TEXT.get(dk)
case("designed text", "SHIPPED TEXT DIFFERS FROM DESIGN",
     lambda: E.DESIGNED_TEXT.__setitem__(dk, "text that was never shipped anywhere"),
     lambda: (E.DESIGNED_TEXT.pop(dk, None) if ds is None else E.DESIGNED_TEXT.__setitem__(dk, ds)))

case("false divergence", "DECLARED DIVERGENCE OUTLIVED ITS ARITHMETIC",
     lambda: O.SCORING_DIVERGENCES.append({"what":"an injected claim: the assignable slot points sum to 99 against an item max of 1","items":["Q6"],"necessary":True}),
     lambda: O.SCORING_DIVERGENCES.pop())

rpf = E.check_paper_feedback_explains_its_deductions
case("paper-feedback blind (inverted)", "PAPER FEEDBACK DOES NOT EXPLAIN ITS OWN CHARGE",
     lambda: setattr(E, "check_paper_feedback_explains_its_deductions", lambda: []),
     lambda: setattr(E, "check_paper_feedback_explains_its_deductions", rpf), inverted=True)
print("VALIDATE_FULL_DONE")
