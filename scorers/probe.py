#!/usr/bin/env python3
"""The probe/sweep identity guarantee: a probe asks the SHIPPING string.

WHY THIS MODULE EXISTS. On 2026-09-06 subgoal Q19's report slot was probed with a
carefully written question, passed 23 of 24, was then built with a `desc` that
dropped the question's comparison clause and turned a yes/no into a which-one,
and the sweep over-fired on nine cells. ~230 calls. The first explanation offered
was a "prompt-load effect" -- the same question being stable alone and unstable
among sixteen others -- which was a hand-wave; re-probing with the SHIPPED string
reproduced the failure standalone in 24 calls. A mysterious effect is a prompt
diff nobody has looked at yet.

`DESIGNED_TEXT_SHA.json` (enforcement.check_every_prompt_field_is_designed) makes
the OTHER half of the loop mandatory: shipped text must equal designed text. It
cannot help here, because on Q19 the shipped text WAS the designed text -- the
probe was the odd one out, and a hand-written probe string is not a rubric field
at all, so no sha covers it.

THE GUARANTEE IS BY CONSTRUCTION, NOT BY DISCIPLINE. `question_for()` does not
re-derive what the LLM-based grader is shown; it lifts the line out of
`olx_prompts.build_web_prompt()`, the same call the sweep renders from. A probe
that gets its question here cannot ask a different string than the sweep, because
there is only one string. Reconstructing the precedence by hand is exactly what
went wrong: the checklist note is `rule` OR `SLOT_NOTES` OR `desc`, in that
order, and `probe_1c_title.py` -- written before this module -- reads
`rule or desc`, which silently skips the middle term and would lift the wrong
text on any slot carrying a SLOT_NOTES entry.

The receipt half is a backstop for the case construction cannot reach: a probe
run, read, and acted on, after which the text moves. `write_receipt()` records
the sha actually asked; `enforcement.check_probe_receipts_match_shipping()`
refuses a sweep whose cited probe measured a string that no longer ships.

BOTH GRADERS COUNT. A sweep records an answer for every scored slot and the
ledger judges it right or wrong; how the answer was produced is not the point.
So `question_for` returns one of two kinds, and a probe is written the same way
for both:

    kind "asked"    the checklist line an LLM answers      (68 slots today)
    kind "derived"  the `expect`/`equals`/`derived`/`maps`/`forbid` clause the
                    sheet answers it with, lifted from the shipping .olx
                    (25 slots) -- probe it by EVALUATING the rule over the
                    cells: no backend, no calls, no rate limit, so it is the
                    cheapest probe available and the one most worth writing

The first cut of this module refused everything in the second group. That was
wrong twice over: it left 42 of 110 credit slots and all of 1b, T1 and T2
unprobeable, and it implied a deterministic scorer is not a grader. It is one.

USAGE in a probe script:

    import probe
    q = probe.question_for(item_id, slot_name)
    ...ask q["question"], with q["head"] naming the verdicts...
    probe.write_receipt(item_id, slot_name, q, cells={"pNN": {"generic": 0}},
                        verdict="PROCEED", note="target clear, 5 negatives held")

Nothing here calls a backend or touches the tree: no rubric edit, no `--write`,
no `.olx` lock, so it cannot disturb a queued sweep.
"""
from __future__ import annotations

# RUNNABLE AS A SCRIPT, not only importable. A general scorer lives in
# `scorers/`, so `python3 scorers/<this>.py` puts THAT directory on `sys.path`
# and the engine package is not on it at all -- the first `import` of an engine
# module then raises ModuleNotFoundError before anything runs. Measured on the
# certification sweep the day these moved: `No module named 'simulate_h3'`.
#
# `paths` IS IMPORTED HERE FOR ITS SIDE EFFECT as well as its values: it appends
# the general scorers' directory and this course's `scoring/<course>/` to the
# path, which is how the imports below resolve wherever they now live.
import os as _os
import sys as _sys

_ENGINE = _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "scoring")
if _ENGINE not in _sys.path:
    _sys.path.insert(0, _ENGINE)
import paths as _paths_bootstrap  # noqa: F401  (side effect: see above)

import json
import pathlib
import re
import sys
import paths as _p7   # J-7b: this course's handout file names

HERE = pathlib.Path(__file__).parent
import paths as _paths_rec
import forms as _forms   # forms are declared by the course, not counted here

RECEIPTS = _paths_rec.COURSE_PROBE_RECEIPTS

# The header `_criteria_section` emits above the answerable checklist. The probe
# must read THIS section and no other: a slot's text is printed twice in the
# shipped prompt (once in the rubric summary as "- `title` (2 pt): ...", once
# here as "- `title` -- `met`/`absent`: ..."), and only this one is the question
# the LLM-based grader answers. Lifting from the summary would drop the verdict
# vocabulary.
CHECKLIST_HEAD = "## The checklist to return (`checks`)"


def _checklist(prompt: str) -> list[str]:
    """The checklist section's lines, or [] if the prompt has no checklist."""
    at = prompt.find(CHECKLIST_HEAD)
    if at < 0:
        return []
    rest = prompt[at + len(CHECKLIST_HEAD):]
    # The section runs to the next `## ` header at line start, or to the end.
    end = re.search(r"^## ", rest, re.M)
    return (rest[:end.start()] if end else rest).split("\n")


CREDIT_HEAD = "## Credit components"


def _credit_entries(prompt: str) -> dict:
    """slot -> the text shipped under `## Credit components`, which is the DESC.

    WHY THIS EXISTS. A slot's shipped text is in TWO sections of one prompt: its
    `desc` under `## Credit components`, and its `rule` under `## The checklist
    to return`. `_checklist` reads only the second, so `question_for` returned
    the rule and silently omitted the desc -- for `Q2/wgb_is_counterpart` that
    is 1293 characters hidden behind 733 reported, and the hidden part carries
    SEVEN of the nine arithmetic-consequence phrases subgoal Q41 is filed on.
    Asking the designated reader "what does the grader see" answered "not that
    sentence" while the sentence was in the prompt the whole time.
    """
    at = prompt.find(CREDIT_HEAD)
    if at < 0:
        return {}
    rest = prompt[at + len(CREDIT_HEAD):]
    end = re.search(r"^## ", rest, re.M)
    lines = (rest[:end.start()] if end else rest).split("\n")
    out, key, body = {}, None, []
    for line in lines:
        m = re.match(r"- `([A-Za-z0-9_]+)`(.*?): ?(.*)$", line)
        if m:
            if key:
                out[key] = "\n".join(body).strip()
            key, body = m.group(1), [m.group(3)]
            continue
        if re.match(r"- `([A-Za-z0-9_]+)`", line):
            if key:
                out[key] = "\n".join(body).strip()
            key, body = re.match(r"- `([A-Za-z0-9_]+)`", line).group(1), []
            continue
        if key is not None:
            body.append(line)
    if key:
        out[key] = "\n".join(body).strip()
    return out


def _entries(prompt: str) -> dict:
    """slot -> (head, note) for every slot the LLM-based grader is ASKED about.

    A note may run over several lines -- descs are written as prose and keep
    their newlines through the render -- so an entry continues until the next
    line that opens a new slot.
    """
    out, key, head, body = {}, None, None, []
    for line in _checklist(prompt):
        m = re.match(r"- `([A-Za-z0-9_]+)`(.*?): ?(.*)$", line)
        if m:
            if key:
                out[key] = (head, "\n".join(body).strip())
            key, head, body = m.group(1), m.group(2).strip(), [m.group(3)]
            continue
        m2 = re.match(r"- `([A-Za-z0-9_]+)`(.*)$", line)
        if m2:
            if key:
                out[key] = (head, "\n".join(body).strip())
            key, head, body = m2.group(1), m2.group(2).strip(), []
            continue
        if key is not None:
            body.append(line)
    if key:
        out[key] = (head, "\n".join(body).strip())
    return out


def field_sha(text) -> str:
    """The same normalisation `enforcement._field_sha` uses, so a receipt sha and
    a design sha are comparable without either module importing the other's."""
    import hashlib
    return hashlib.sha256(
        re.sub(r"\s+", " ", str(text)).strip().encode()).hexdigest()[:12]


# The attributes that make a sheet slot's verdict WITHOUT asking an LLM. Read
# all of them or the probe tells a confident lie about whichever was forgotten --
# `enforcement._derived` learned this by reading `expect` alone and reporting six
# items' `matches_chosen_type`, declared `equals`, as a scoring gap.
DERIVING_ATTRS = ("expect", "equals", "derived", "maps", "forbid", "onlyif")


def _slot_aliases(slot: str) -> list:
    """A rubric slot name plus the sheet name(s) it goes by.

    1b is the case that forces this: the rubric calls its slots `baseline` and
    `week_1..3`, the sheet calls them `baseline_data` and `week_1_data..`, and a
    lookup under either name alone finds nothing on four of the item's five
    slots. `enforcement.ALIAS` already holds the pairs.
    """
    try:
        from enforcement import ALIAS
    except Exception:
        return [slot]
    names = {slot}
    for k, v in ALIAS.items():
        pair = (k,) + (v if isinstance(v, tuple) else (v,))
        if slot in pair:
            names.update(pair)
    return sorted(names)


def _element(item_id: str, slot: str):
    """The item's OWN sheet element, and the handout number it lives in.

    Scoping matters more than it looks. The first cut scanned whole `.olx`
    files, so a probe of `PR/is_pr` came back carrying NR's, PP's and NP's
    `expect` clauses and NP's slot label -- four sibling items' rules presented
    as the question being probed. `olx_prompts._sheet_tag` already resolves an
    item to its one element; use it, and fall back to the element that DECLARES
    the slot for the three items with no `ACTION` entry (1b, T1, T2).
    """
    import olx_prompts as O
    from forms import config

    hs = [h for h in _forms.declared()
          for it in config(h)["rubric"].ITEMS if it["id"] == item_id] or [1, 2, 3]
    for h in hs:
        if item_id in O.ACTION:
            try:
                return h, O._sheet_tag(h, O.ACTION[item_id])
            except SystemExit:
                continue
        # THE ITEM'S OWN ELEMENT FIRST. A sheet-only item has no `ACTION`
        # entry, so this fell straight through to a scan that returns the
        # FIRST element declaring the slot NAME -- and two items on one handout
        # can share slot names. `T2/type_stated` resolved to T1's element and
        # reported T1's rule (`derived="type_stated:present:bmod_h2_t1"`) as
        # T2's: a confident answer about the wrong element. Measured across
        # every sheet-only slot, it was the only one, which is exactly why a
        # first-match scan survives -- it is right until two names collide.
        # Same shape as `_rubric_file` before E58 made the namespace decide.
        try:
            own = O._sheet_tag(h, O.sheet_id(item_id))
        except BaseException:
            own = None
        if own:
            decl = re.search(r'\bslots="([^"]*)"', own)
            if decl and any(c.split(":")[0].strip().lstrip("!")
                            in set(_slot_aliases(slot))
                            for c in decl.group(1).split("|")):
                return h, own
        names = set(_slot_aliases(slot))
        for m in re.finditer(r'<[A-Za-z][^>]*?\bslots="[^"]*"[^>]*?>', O._src(h), re.S):
            tag = m.group(0)
            decl = re.search(r'\bslots="([^"]*)"', tag)
            if decl and any(c.split(":")[0].strip().lstrip("!") in names
                            for c in decl.group(1).split("|")):
                return h, tag
    return None, None


def _count_aggregates() -> dict:
    """`{(item, slot): (count_key,)}` for every slot a `Counts` group covers.

    DERIVED FROM THE RUBRIC, which already says it. Eleven entries were written
    out here instead, naming five of this course's items and enumerating their
    slots -- and the enumeration carried the assumption E60 is about,
    `for n in (1, 2, 3)`, which silently caps a criterion at three parallel
    slots. Reading the declaration takes however many it declares.

    Measured identical to the eleven it replaces, 2026-09-25.
    """
    import enforcement

    out = {}
    for item in enforcement.all_items():
        for group in (item.get("counts") or ()):
            key = group.get("key")
            for slot in (group.get("slots") or ()):
                out[(item["id"], slot)] = (key,)
    return out


def _answered_under() -> dict:
    """`{(item, slot): (slots that answer it,)}`.

    TWO SOURCES, AND THEY ARE DIFFERENT KINDS OF FACT. Subgoal E58, 2026-09-25.

      * THE SCORER'S, asked of it rather than known here. The
        operant-conditioning gate, the four type criteria and the eight items
        they apply to are that subject's, and this module held them keyed by
        this course's item ids. A scorer that declares none contributes none.
      * THE COUNT AGGREGATES, derived from the rubric's own `Counts` groups,
        which already declare which slots a count covers -- for any course.

    A scorer's entries win on a collision: it is the authority on its own items.
    """
    import scorers

    out = dict(_count_aggregates())
    plugin = scorers.optional("oc")
    out.update(getattr(plugin, "ANSWERED_UNDER", None) or {})
    return out


ANSWERED_UNDER = _answered_under()


def _derivation(item_id: str, slot: str) -> dict | None:
    """The deterministic rule that answers `slot`, lifted from the sheet.

    Returns the same shape as `question_for`'s asked case, with kind "derived"
    and `how` naming the attributes found, or None if this item's element
    derives the slot nowhere. A probe of one of these evaluates the rule over
    the cells and compares against gold: no backend, no calls, no rate limit.
    """
    form, tag = _element(item_id, slot)
    if not tag:
        return None
    names = _slot_aliases(slot)
    found, labels = [], []
    for attr in DERIVING_ATTRS:
        for m in re.finditer(rf'{attr}="([^"]*)"', tag):
            for clause in m.group(1).split("|"):
                if clause.split(":")[0].strip().lstrip("!") in names:
                    found.append((attr, clause.strip()))
    # The `slots=` declaration carries the label and the verdict vocabulary --
    # the derived slot's counterpart to the asked slot's `head`. EXACT NAME
    # FIRST, alias only as a fallback: `ALIAS` groups `demonstrates_type` with
    # `observed_type` and `stimulus_move`, which is right for finding the
    # clauses that answer it and wrong for labelling it.
    for m in re.finditer(r'\bslots="([^"]*)"', tag):
        for clause in m.group(1).split("|"):
            head = clause.split(":")[0].strip().lstrip("!")
            if head == slot:
                labels.insert(0, clause.strip())
            elif head in names:
                labels.append(clause.strip())
    if not found:
        return None
    sheet = _p7.handout_olx(form)
    question = "\n".join(f'{attr}="{clause}"' for attr, clause in found)
    return {"item": item_id, "slot": slot, "kind": "derived",
            "head": labels[0] if labels else "", "question": question,
            "sha": field_sha(question), "prompt_sha": "",
            "how": sorted({a for a, _ in found}), "sheets": [sheet]}


def question_for(item_id: str, slot: str) -> dict:
    """The EXACT text the LLM-based grader is shown for `slot`, lifted from the
    prompt.

    Returns {item, slot, head, question, sha, prompt_sha}. `head` is the verdict
    vocabulary as rendered (e.g. "-- `met`/`absent`/`generic`", or the `refers_to`
    member list for a pick slot); `question` is the note beneath it.

    Raises LookupError if the slot is not in the checklist, and says which of the
    two reasons applies. THIS IS A FINDING, NOT AN INCONVENIENCE: a slot that is
    computed, mapped, counted or forbidden is one the LLM-based grader never
    answers, so a probe of it measures nothing the sweep will run; and a slot
    that is simply absent is a designed field that does not ship -- the Q19
    shape, caught before any call instead of after 230.
    """
    sys.path.insert(0, str(HERE))
    import olx_prompts as O

    entries = {}
    if item_id in O.ACTION:
        prompt = O.build_web_prompt(item_id)
        entries = _entries(prompt)
    if slot not in entries:
        # NOT ASKED OF AN LLM IS NOT THE SAME AS NOT MEASURED. A sweep records
        # this slot's answer and the ledger scores it like any other; what
        # differs is only which grader produced it. So fall through to the
        # DETERMINISTIC rule and let the caller probe THAT -- at zero calls,
        # which makes it the cheapest probe available and the one most worth
        # writing. Refusing these was the first cut's mistake: it left 42 of 110
        # credit slots, and every slot of 1b, T1 and T2, unprobeable in a project
        # whose whole method is QUALITY_CONTROL.md §2a.
        d = _derivation(item_id, slot)
        if d:
            return d
    if slot not in entries:
        # `olx_prompts` has no item list of its own -- the rubrics do, reached
        # through `forms.config`. An earlier version of this looked for
        # `O.ITEMS`, found nothing, and so told every caller "not on this sheet
        # at all", including for slots that ARE on the sheet and merely derived.
        # That is the more useful of the two messages, and it was unreachable.
        from forms import config
        known = [c["what"] for h in _forms.declared()
                 for it in config(h)["rubric"].ITEMS if it["id"] == item_id
                 for c in it.get("credit", [])]
        # A rubric criterion the SHEET decomposes differently -- Q1/Q2's three
        # `reason_*`, 2b's three `sentence_*`, 3's two `example_*`, the four
        # `is_*` type aggregates. There is a real answer being measured on the
        # sweep; it is just not answered under this name, so point the caller at
        # the slots that DO answer it instead of refusing flat. The declared
        # divergence carries the explanation already.
        if (item_id, slot) in ANSWERED_UNDER:
            parts = []
            for name in ANSWERED_UNDER[(item_id, slot)]:
                if name in entries:
                    head, note = entries[name]
                    parts.append((name, "asked", head, note))
                else:
                    d = _derivation(item_id, name)
                    if d:
                        parts.append((name, "derived", d["head"], d["question"]))
            if parts:
                body = "\n\n".join(f"[{k}] `{n}` {h}\n{t}" for n, k, h, t in parts)
                return {"item": item_id, "slot": slot, "kind": "composite",
                        "head": " + ".join(f"`{n}`" for n, _, _, _ in parts),
                        "question": body, "sha": field_sha(body),
                        "prompt_sha": field_sha(prompt) if entries else "",
                        "parts": [n for n, _, _, _ in parts]}
        try:
            from enforcement import DECOMPOSITION_DIVERGENCES as DD
        except Exception:
            DD = {}
        if (item_id, slot) in DD:
            raise LookupError(
                f"{item_id}/{slot} is a rubric criterion the sheet DECOMPOSES: "
                f"{str(DD[(item_id, slot)]).split('. ')[0]}. It is measured on "
                f"the sweep, under other names -- probe those. Asked on this "
                f"sheet: {', '.join(sorted(entries)) or '(none)'}")
        why = ("it is a credit slot on this sheet but no sheet element asks it "
               "and no `expect`/`equals`/`derived`/`maps`/`forbid` clause "
               "answers it either. That combination is a finding in itself: a "
               "scored criterion with no grader of any kind"
               if slot in known else
               "it is not on this sheet at all: either the name is wrong, or a "
               "designed field was never built. Check the design of record")
        raise LookupError(
            f"{item_id}/{slot} is not in the shipped checklist -- {why}.\n"
            f"  asked slots: {', '.join(sorted(entries)) or '(none)'}")
    head, note = entries[slot]
    # BOTH SECTIONS, because both ship. The `desc` renders under `## Credit
    # components` and the `rule` under `## The checklist to return`, in ONE
    # prompt; reporting only the checklist half is how subgoal Q41's declared
    # sentence read as "gone" while it was in front of the grader. `question` is
    # now everything the grader is shown for this slot, in prompt order, and
    # `parts` keeps the halves separable for a caller that needs one field.
    credit = _credit_entries(prompt).get(slot, "")
    whole = "\n".join(x for x in (credit, note) if x).strip()
    return {"item": item_id, "slot": slot, "kind": "asked", "head": head,
            "question": whole, "sha": field_sha(whole),
            "parts": {"credit_components": credit, "checklist": note},
            "checklist_only": note, "checklist_sha": field_sha(note),
            "prompt_sha": field_sha(prompt)}


def score_impact(*_a, **_k):
    """RETIRED 2026-09-24 with the python web engine.

    It answered "what does flipping this verdict do to the score?" by
    re-scoring recorded runs through the python mirror of `scoreSlotSheet`, at
    zero call cost. The mirror is gone (goal O) and was deliberately NOT
    replaced -- rebuilding it in TypeScript would be the same instrument in
    another language.

    RAISES rather than returning an empty impact: a tool that silently reports
    "no effect" would be read as evidence that a slot does not matter.
    """
    raise SystemExit(
        "probe.score_impact: retired with the python web engine (goal O). The "
        "effect of a verdict on a score is now read from the app itself.")


def write_receipt(item_id: str, slot: str, q: dict, cells: dict | None = None,
                  verdict: str = "", note: str = "", stamp: str = "") -> dict:
    """Record that this string was probed, so a later sweep can be checked.

    `q` must be a `question_for()` result -- passing a hand-built dict defeats
    the purpose and the sha will not match anything. `stamp` is passed in rather
    than read from the clock so a receipt written during a replay is honest.
    """
    if q.get("item") != item_id or q.get("slot") != slot:
        raise ValueError("receipt does not describe the question passed to it")
    doc = {"receipts": []}
    if RECEIPTS.exists():
        try:
            doc = json.loads(RECEIPTS.read_text())
        except Exception:
            pass
    doc.setdefault("_README", (
        "Probes that were run, and the sha of the string each one ASKED. "
        "enforcement.check_probe_receipts_match_shipping() refuses a sweep whose "
        "probe measured text that no longer ships. Written by "
        "probe.write_receipt(); never hand-edit a sha."))
    # TWO SHAS, because two different checks ask two different questions and
    # conflating them made one of them unsatisfiable. `sha` is the ASSEMBLED
    # question -- both prompt sections, which is what the grader actually saw --
    # and is what `check_probe_receipts_match_shipping` compares against the
    # shipping prompt. `checklist_sha` is the DESIGNED FIELD alone, equal to
    # `enforcement._field_sha` of the rubric text, and is what
    # `check_designed_text_is_the_measured_text` compares against DESIGNED_TEXT.
    #
    # They were the same value until 2026-09-08, when `question_for` began
    # returning both sections (56 of 179 asked slots were under-reported by the
    # checklist line alone). That moved `sha` onto the assembled string and left
    # the design check comparing a raw rubric field against a two-section one --
    # never equal, so every slot registered afterwards read as a PARAPHRASE OF
    # ITS OWN EVIDENCE by arithmetic. Recording both is what makes both checks
    # answerable.
    rec = {"item": item_id, "slot": slot, "sha": q["sha"],
           "checklist_sha": q.get("checklist_sha"),
           "question": q["question"], "head": q.get("head", ""),
           "verdict": verdict, "note": note, "stamp": stamp,
           "cells": cells or {}}
    doc["receipts"] = [r for r in doc.get("receipts", [])
                       if not (r.get("item") == item_id and r.get("slot") == slot)]
    doc["receipts"].append(rec)
    RECEIPTS.write_text(json.dumps(doc, indent=1) + "\n")
    return rec


def receipts(item_id: str | None = None) -> list:
    if not RECEIPTS.exists():
        return []
    try:
        doc = json.loads(RECEIPTS.read_text())
    except Exception:
        return []
    out = doc.get("receipts") or []
    return [r for r in out if item_id is None or r.get("item") == item_id]


def main(argv: list) -> int:
    """`python3 probe.py ITEM SLOT` prints the shipping question and its sha.

    Use it before writing a probe script: if this refuses, the probe you were
    about to write would have measured a string the sweep never renders.
    """
    if len(argv) == 1:
        for r in receipts():
            print(f"  {r['item']}/{r['slot']:<24} {r['sha']}  {r.get('verdict','')}"
                  f"  {r.get('note','')[:60]}")
        return 0
    if len(argv) != 3:
        print(__doc__)
        return 2
    try:
        q = question_for(argv[1], argv[2])
    except LookupError as e:
        print(f"REFUSED: {e}")
        return 1
    print(f"  {q['item']}/{q['slot']}   sha {q['sha']}   prompt {q['prompt_sha']}")
    print(f"  verdicts: {q['head']}")
    print(f"\n{q['question']}\n")
    return 0


# MOVED ABOVE THE MAIN GUARD 2026-09-16. Everything below
# `if __name__ == "__main__":` exists ONLY when this module is imported -- a
# script run ends inside `main()` and never reaches it. `probe.control_gate` is
# the guard that voids a probe measuring its own envelope, and it simply was not
# there when probe.py was run directly. Nothing reported that; the parse, the
# imports and every table survived. `check_no_module_defines_names_after_its_main_guard`
# is what reports it now.
def recorded_answers(item: str, slots: tuple, cells: tuple = ()) -> dict:
    """What the LEDGER says the shipped prompt answers, per cell and slot.

    {(pid, slot): Counter({answer: n})}, pooled over the python and olx runs and
    read with `measured.slot_answer`, which is the only reader that knows an
    empty string is ABSENCE and not a value.

    This is the baseline a probe's control arm has to reproduce. It reads the
    ledger, so a stale item gives a stale baseline -- callers get the standard
    `warn_if_stale` banner and must not quote a figure through it.
    """
    import collections

    import measured as M

    M.warn_if_stale(item, where="probe control")
    want = set(cells) if cells else None
    out: dict = collections.defaultdict(collections.Counter)
    for side in ("olx",):
        try:
            doc = M._runs_doc(item, side)
        except Exception:
            continue
        for run in doc["runs"]:
            for r in run["results"]:
                pid = r.get("participant_id")
                if pid is None and r.get("cell"):
                    head = str(r["cell"]).split("/")[0].lstrip("pP")
                    pid = int(head) if head.isdigit() else None
                if pid is None or (want and pid not in want):
                    continue
                for s in slots:
                    out[(pid, s)][str(M.slot_answer(r, s))] += 1
    return dict(out)


def control_gate(item: str, slots: tuple, observed: dict, *,
                 runs: int, stream=None) -> int:
    """0 to trust a probe's result, 1 to REFUSE it. Compare the control arm.

    WHY THIS EXISTS, and it is the gap that let a wrong conclusion be written up
    on 2026-09-07. Every identity control in this package answers "is this the
    right STRING?" -- `DESIGNED_TEXT_SHA` (designed == shipped),
    `question_for` + `field_sha` (probed == shipped), `prompt_sha` (baseline ==
    measured). None of them asks "is this the right PROMPT". On Q4c the shipped
    assembled prompt is 9438 characters carrying TWELVE checklist lines -- both
    consequence slots, the keyword advisory, the `no_consequences` gate, five
    deduction codes including the `C_NOT_CONSEQUENCE` charge gold actually levies,
    and a `confident` slot -- and the `consequence_1` rule text is 1085 of those
    characters, ELEVEN PER CENT. A probe that hand-builds an envelope around the
    right string is still asking a different question, and it will answer it
    confidently.

    MEASURED, on one cell of one course: the shipped prompt answered a slot one
    way on every one of twelve runs, and a probe's UNMODIFIED arm answered it the
    OTHER way on all four of its own. Four calls would have caught the
    difference. Instead a rule was built, probed, read as a swap, reverted and
    written up as a negative result -- all downstream of an envelope that could
    not reproduce the baseline.

    `observed` is {(pid, slot): Counter} or {(pid, slot): answer} from the arm
    running the UNMODIFIED shipped text. A cell is refused when the control's
    modal answer differs from the ledger's modal answer: that is the envelope
    disagreeing with the shipped prompt about a question no edit has touched, so
    nothing measured through it can be attributed to an edit.

    A probe whose control arm passes is not thereby CORRECT -- the envelope may
    still differ where the ledger is silent. It is merely not disqualified.
    """
    import collections
    import sys as _sys

    stream = stream or _sys.stderr
    base = recorded_answers(item, slots, tuple(sorted({p for p, _ in observed})))
    bad, unknown, wobbly, unanswered = [], [], [], []
    for key, got in sorted(observed.items()):
        pid, slot = key
        if isinstance(got, collections.Counter):
            top = got.most_common(1)[0][0] if got else None
        else:
            top = str(got)
        rec = base.get(key)
        if not rec:
            unknown.append(f"p{pid}/{slot}")
            continue
        want = rec.most_common(1)[0]
        # `measured.slot_answer` returns None for a slot the shipped prompt NEVER
        # ANSWERED, and str() turns that into "None". That is absence, not a
        # verdict: a probe forcing an answer where the sheet never gives one is
        # not disagreeing with the ledger, it is asking about a slot the ledger
        # cannot speak for. Refusing on it would be a FALSE refusal -- which is
        # what a candidate report slot reverted out of the tree looks like.
        if str(want[0]) == "None":
            unanswered.append(f"p{pid}/{slot}")
            continue
        want = rec.most_common(1)[0]
        # A cell whose LEDGER answer is itself unstable cannot convict an
        # envelope: the probe's four runs could differ from the pooled mode by
        # sampling alone. Only a mode the shipped prompt holds at least 75% of
        # the time is a baseline; the rest are reported and not counted.
        if want[1] / sum(rec.values()) < 0.75:
            wobbly.append(f"p{pid}/{slot} (ledger mode {want[0]!r} only "
                          f"{want[1]}/{sum(rec.values())})")
            continue
        if str(top) != str(want[0]):
            bad.append(f"    p{pid}/{slot}: control says {top!r}, the ledger's "
                       f"runs say {want[0]!r} ({want[1]} of {sum(rec.values())})")
    if unknown:
        print(f"  CONTROL: no recorded answer for {', '.join(unknown)} -- the "
              f"ledger cannot vouch for these, so they are not a baseline.",
              file=stream)
    if unanswered:
        print(f"  CONTROL: {len(unanswered)} cell-slot(s) SKIPPED because the "
              f"shipped prompt NEVER ANSWERS that slot -- no baseline exists, so "
              f"this probe cannot be gated on it: {', '.join(unanswered[:4])}"
              f"{' ...' if len(unanswered) > 4 else ''}. Gate it on a slot the "
              f"sheet DOES answer, measured in the same call.", file=stream)
    if wobbly:
        print(f"  CONTROL: {len(wobbly)} cell-slot(s) SKIPPED because the "
              f"ledger's own answer wobbles: {'; '.join(wobbly[:4])}"
              f"{' ...' if len(wobbly) > 4 else ''}", file=stream)
    if bad:
        print(f"  *** PROBE REFUSED: its envelope does not reproduce the shipped "
              f"prompt on {len(bad)} cell-slot(s) that NO EDIT TOUCHED ***",
              file=stream)
        for line in bad:
            print(line, file=stream)
        print("  Nothing measured through this envelope can be attributed to an "
              "edit. Fix the envelope -- build the prompt with "
              "`olx_prompts.build_web_prompt` and swap only the field -- or "
              "measure in a sweep instead.", file=stream)
        return 1
    if not unknown and not unanswered:
        print(f"  CONTROL PASSED: the unmodified arm reproduces the ledger on all "
              f"{len(observed)} cell-slot(s) checked ({runs} runs each). The "
              f"envelope is not disqualified; it is not thereby proven equivalent "
              f"where the ledger is silent.", file=stream)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
