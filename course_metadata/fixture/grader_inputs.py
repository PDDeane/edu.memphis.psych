#!/usr/bin/env python3
"""WHICH GRADER GOES WITH WHICH INPUT — the hard declaration, and its verifier.

This is the table the intake program is steered by. Deciding that a chunk of
teacher material is "a matching exercise" is worth nothing unless something says
which grader a matching exercise becomes and what it may contain, and lo-blocks
does not say: **no grader declares the inputs it pairs with.** A grader declares
`inputType` (`single`/`list`) or `slots` (dict mode) and whether it `infer`s its
inputs from its children, and that is all. Compatibility is a value-schema
question plus authoring convention written in prose and examples.

So the pairing is DECLARED here, by hand, and then held to evidence in both
directions by `verify()`:

* a pairing declared here with no example anywhere in the corpora is reported --
  a declaration nobody demonstrates is a guess with a table around it;
* a pairing DEMONSTRATED in a corpus and absent here is reported -- new evidence
  must force a decision rather than being absorbed.

THREE MECHANISMS, and the third is why a nesting-only reading of lo-blocks is
wrong. Measured across 319 `.olx` files in lo-blocks and the psych course:

1. **nested** — the grader WRAPS the input and infers it from its children
   (`infer: true`). This is the common case and all 24 demonstrated pairings
   below are of this kind.
2. **targeted** — the grader names its source by id and infers nothing
   (`infer: false`). `SlotSheetGrader target="..."` points at an `LLMFeedback`,
   which is not a student input at all.
3. **referenced** — the student input is read by an `LLMAction` through a
   `<Ref target="...">` INSIDE THE PROMPT BODY, and the grader then scores the
   action's output. Nothing links input to grader by attribute; the link is a
   reference embedded in prose. This is how every one of the 26 scored psych
   items is reached, and a reader looking only for nesting sees none of it.

WHAT THIS MEANS FOR THE INTAKE PROGRAM. Constructed-response inputs are not
graded by wrapping them. `TextArea`, `Freewrite`, `CodeInput` and `Annotate`
appear inside no grader anywhere in the corpora scanned -- they are reached by
mechanism 3 or they are not scored at all. Choosing "a grader for this item" is
therefore not one decision but two: which MECHANISM, then which component.
"""
from __future__ import annotations

# THE MACHINERY ON THE PATH, for the direct-script spelling. `paths` puts THIS
# directory on the path for importers; a fixture module run as a script needs the
# reverse -- its own siblings in `scoring/` -- and never executes anything that
# would have done it.
import os as _os
import sys as _sys

_sys.path.insert(0, _os.path.join(
    _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))),
    "scoring"))

import argparse
import json
import os

import paths
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

SCHEMA_VERSION = 1

NESTED, TARGETED, REFERENCED = "nested", "targeted", "referenced"

# The declaration. `inputs` are the gradable inputs this grader may take;
# `parts` are the item-parts it parses out of its own subtree (Key, Distractor)
# and are NOT inputs. `why` says what makes the pairing true, not that it is.
GRADER_INPUTS: dict[str, dict] = {
    "CheckboxGrader": {
        "mechanism": NESTED, "inputs": ["CheckboxInput"],
        "parts": ["Key", "Distractor"],
        "why": "multi-select: the input's value is a list of chosen option ids, "
               "and the Keys among its Key/Distractor children are the answer"},
    "CorrectGrader": {
        "mechanism": NESTED,
        "inputs": ["CheckboxInput", "ChoiceInput", "LineInput", "TextArea"],
        "parts": ["Key"],
        # ITS OWN README SAYS SO: "CorrectGrader is input-agnostic. It works with
        # CheckboxInput, ChoiceInput, LineInput, TextArea, or ...". The first
        # declaration here listed two, because the corpus it was checked against
        # excluded the documentation -- where both the statement and a worked
        # TextArea example live.
        "doc_only": {"LineInput": "grading/CorrectGrader.md, 'input-agnostic'"},
        "why": "scores whichever input it wraps against the Key children. "
               "Input-agnostic by design, which makes it the fallback when the "
               "answer is enumerated but the widget is not yet chosen"},
    "KeyGrader": {
        "mechanism": NESTED, "inputs": ["ChoiceInput", "DropdownInput"],
        "parts": ["Key", "Distractor"],
        "why": "single-select from a Key/Distractor set, whether the set is "
               "rendered as radios or as a dropdown"},
    "MatchingGrader": {
        "mechanism": NESTED, "inputs": ["MatchingInput"], "parts": [],
        "why": "scores a set of left-right pairings; only MatchingInput produces "
               "that value shape"},
    "SortableGrader": {
        "mechanism": NESTED, "inputs": ["SortableInput"], "parts": [],
        "why": "scores an ORDER; declares inputType 'single' and only "
               "SortableInput produces an ordering"},
    "TabularMCQGrader": {
        "mechanism": NESTED, "inputs": ["TabularMCQ"], "parts": [],
        "why": "scores a row->column selection grid, which only TabularMCQ "
               "produces"},
    "TextSelectionGrader": {
        "mechanism": NESTED, "inputs": ["TextSelectionInput"], "parts": [],
        "why": "scores selected spans, a list of offsets only TextSelectionInput "
               "produces"},
    "NumericalGrader": {
        "mechanism": NESTED, "inputs": ["NumberInput", "ComplexInput", "LineInput"],
        "parts": [],
        "why": "compares a parsed number against `answer` within `tolerance`, so "
               "it takes any input whose text parses as a number -- which is why "
               "LineInput appears here and is not a mistake"},
    "RatioGrader": {
        "mechanism": NESTED, "inputs": ["NumberInput", "ComplexInput"], "parts": [],
        "why": "dict mode: scores several named numeric parts as a ratio"},
    "FormulaGrader": {
        "mechanism": NESTED, "inputs": ["FormulaInput"], "parts": [],
        "why": "compares expressions symbolically; FormulaInput is what produces "
               "an expression"},
    "StringGrader": {
        "mechanism": NESTED, "inputs": ["LineInput"], "parts": [],
        "why": "exact or case-folded text match against `answer`, which suits a "
               "single line and not a paragraph"},
    "RulesGrader": {
        "mechanism": NESTED, "inputs": ["LineInput"], "parts": [],
        "why": "applies Rule children (the generated *Match variants) to a text "
               "response"},
    "DefaultGrader": {
        "mechanism": NESTED, "inputs": ["LineInput", "TextArea"], "parts": [],
        "why": "the fallback when an input is graded with no grader named; the "
               "TextArea pairing comes from its own documented example"},
    "LLMGrader": {
        "mechanism": NESTED, "inputs": ["LineInput", "TextArea"], "parts": [],
        # EVIDENCE OF A DIFFERENT CLASS. No .olx wraps a TextArea in an
        # LLMGrader, so the both-ways check reported it as undemonstrated -- and
        # it was right to. The evidence is the block's OWN usage note, which is
        # authored by the people who wrote the grader. Named here rather than
        # waved through, so the distinction between "shown in a course" and
        # "documented by its author" stays visible.
        "doc_only": {"TextArea": "grading/LLMGrader.ts usage note"},
        "why": "THE SECOND LLM-BASED GRADER, and the simple one. It wraps a "
               "constructed response and judges it asynchronously against "
               "`question` + `rubric` (+ optional `answer`), returning ONE "
               "correctness verdict. Its own usage note wraps a TextArea, the "
               "shipped demo wraps a LineInput, and both are declared because "
               "both are authored. Contrast SlotSheetGrader, which scores a "
               "STRUCTURED sheet of slots and counts an LLMAction produced -- "
               "multi-slot and point-weighted, which is what a rubric needs and "
               "what one verdict cannot express. It is declared in the "
               "`org.mitros.dev` NAMESPACE, which is a namespace and not a gate"},
    "SlotSheetGrader": {
        "mechanism": TARGETED, "inputs": [], "parts": [],
        "targets": ["LLMFeedback"],
        "why": "`infer: false`. It scores the verdict sheet an LLMAction "
               "published into an LLMFeedback, so its target is not a student "
               "input at all. Every scored psych item is reached this way"},
    "CustomGrader": {
        "mechanism": TARGETED, "inputs": [], "parts": [],
        "targets": [],
        "why": "`infer: false` and an author-supplied function; what it accepts "
               "is decided by that function, so no pairing can be declared here. "
               "UNDEMONSTRATED in the corpora scanned"},
}

# WHAT THE STUDENT PRODUCES, AND HOW IT IS MEANT TO BE SCORED.
#
# Two things are recorded per response source and they are not the same. `kind`
# says whether the student AUTHORED content or CHOSE among options the author
# supplied -- a LineInput holding a one-word definition is constructed response,
# a DropdownInput holding the same word is not. `prefers` says which scoring path
# the component exists for.
#
# `llm_fallback` is the trap this table is shaped to avoid. A `<Ref target=>`
# inside an LLMAction prompt can render ANY component's value, so almost
# everything here COULD be handed to a model. That is a capability, not a
# recommendation: asking a model to score a ChoiceInput is strictly worse than
# KeyGrader -- slower, costlier, non-deterministic, and wrong sometimes -- when
# the answer is a set the author already enumerated. An intake program that reads
# "can be scored by an LLM" as "should be" would route the entire course through
# a model.
#
# NOT EVERY RESPONSE SOURCE IS NAMED `*Input`. Chat, Annotate, AvatarEditor,
# CastEditor, CharacterBuilder and DigitSpanTask all collect student work without
# declaring `...input(`, and a census keyed on the name or on the input
# declaration misses every one of them. A conversation is constructed response.
CONSTRUCTED, SELECTED = "constructed", "selected"
LLM_CHAIN = "LLMAction -> LLMFeedback -> SlotSheetGrader, or LLMGrader"

RESPONSE_SOURCES: dict[str, dict] = {
    # --- selected response: the author enumerated the options -----------------
    "ChoiceInput":        {"kind": SELECTED, "prefers": ["KeyGrader", "CorrectGrader"],
                           "llm_fallback": True,
                           "why": "one of the author's Key/Distractor options; a "
                                  "model adds cost and doubt to a lookup"},
    "CheckboxInput":      {"kind": SELECTED, "prefers": ["CheckboxGrader", "CorrectGrader"],
                           "llm_fallback": True,
                           "why": "several of the author's options"},
    "DropdownInput":      {"kind": SELECTED, "prefers": ["KeyGrader"],
                           "llm_fallback": True,
                           "why": "one of the author's options, rendered compactly"},
    "MatchingInput":      {"kind": SELECTED, "prefers": ["MatchingGrader"],
                           "llm_fallback": True,
                           "why": "pairings among author-supplied sides"},
    "SortableInput":      {"kind": SELECTED, "prefers": ["SortableGrader"],
                           "llm_fallback": True,
                           "why": "an ordering of author-supplied items"},
    "TabularMCQ":         {"kind": SELECTED, "prefers": ["TabularMCQGrader"],
                           "llm_fallback": True,
                           "why": "a row->column grid over author-supplied options"},

    # --- constructed response with a deterministic grader ---------------------
    "NumberInput":        {"kind": CONSTRUCTED, "prefers": ["NumericalGrader", "RatioGrader"],
                           "llm_fallback": False,
                           "why": "the student writes a number; `tolerance` "
                                  "settles it exactly and a model cannot do better"},
    "FormulaInput":       {"kind": CONSTRUCTED, "prefers": ["FormulaGrader"],
                           "llm_fallback": False,
                           "why": "the student writes an expression; compared "
                                  "symbolically, which is a stronger test than "
                                  "judgement"},
    "ComplexInput":       {"kind": CONSTRUCTED, "prefers": ["NumericalGrader", "RatioGrader"],
                           "llm_fallback": True,
                           "why": "mixed authored content; demonstrated under the "
                                  "numeric graders"},
    "TextSelectionInput": {"kind": CONSTRUCTED, "prefers": ["TextSelectionGrader"],
                           "llm_fallback": True,
                           "why": "spans picked out of running text. The options "
                                  "are not enumerated by the author, so this is "
                                  "authored selection -- gradeable against marked "
                                  "spans, or judgeable when the spans are open"},
    "LineInput":          {"kind": CONSTRUCTED,
                           "prefers": ["StringGrader", "RulesGrader", "NumericalGrader",
                                       "DefaultGrader"],
                           "llm_fallback": True,
                           "why": "a line the student writes -- SHORT IS NOT "
                                  "SELECTED. Deterministic when the expected "
                                  "answer is fixed text, a rule or a number; the "
                                  "LLM path when the line is open-ended"},

    # --- constructed response whose only path is judgement --------------------
    "TextArea":           {"kind": CONSTRUCTED, "prefers": [LLM_CHAIN],
                           "llm_fallback": False,
                           "why": "a paragraph. All 26 scored psych items are "
                                  "reached this way"},
    "Freewrite":          {"kind": CONSTRUCTED, "prefers": [LLM_CHAIN],
                           "llm_fallback": False,
                           "why": "timed free writing; no deterministic grader "
                                  "exists for it"},
    "CodeInput":          {"kind": CONSTRUCTED, "prefers": [LLM_CHAIN],
                           "llm_fallback": False,
                           "why": "code the student writes; lo-blocks ships no "
                                  "code grader"},
    "Annotate":           {"kind": CONSTRUCTED, "prefers": [LLM_CHAIN],
                           "llm_fallback": False,
                           "why": "annotations the student writes ONTO an "
                                  "author-supplied text. No grader wraps it, and "
                                  "scoring annotations is judgement by nature"},
    "Chat":               {"kind": CONSTRUCTED, "prefers": [LLM_CHAIN],
                           "llm_fallback": False,
                           "why": "a conversation the student holds. Collects "
                                  "student work while declaring no `input(`, and "
                                  "a transcript can only be judged"},
    "AvatarEditor":       {"kind": CONSTRUCTED, "prefers": [LLM_CHAIN, "ungraded"],
                           "llm_fallback": False,
                           "why": "a figure the student configures; often "
                                  "expressive rather than assessed"},
    "CastEditor":         {"kind": CONSTRUCTED, "prefers": [LLM_CHAIN, "ungraded"],
                           "llm_fallback": False,
                           "why": "a cast the student assembles"},
    "CharacterBuilder":   {"kind": CONSTRUCTED, "prefers": [LLM_CHAIN, "ungraded"],
                           "llm_fallback": False,
                           "why": "a character the student builds"},
    "DigitSpanTask":      {"kind": CONSTRUCTED, "prefers": ["self-measuring"],
                           "llm_fallback": False,
                           "why": "an instrument, not a question: it produces a "
                                  "span measurement, and nothing grades it"},
}

# `<Ref target="id" field="...">` inside an LLMAction prompt renders any
# component's value, so LLM reach is bounded by the QUESTION, not the widget.
# Recorded as prose because it is a capability of Ref, not a pairing.
LLM_REACHABLE = ("any block holding a value, via <Ref target= field=> inside an "
                 "LLMAction prompt body -- a capability, NOT a recommendation; "
                 "see llm_fallback")

# Blocks that grade themselves and therefore pair with no grader.
SELF_GRADING = {
    "CapaProblem": "an Open edX-style problem carrying its own inputs and "
                   "grading; graders appear INSIDE it, not around it",
    "MarkupProblem": "a self-contained problem family, as CapaProblem",
    # Each of these is a terse one-tag PEG syntax that EXPANDS to a CapaProblem,
    # so the expansion carries the grading and the shorthand pairs with nothing.
    # They sat in ITEM_PARTS until the documentation was read: their own
    # descriptions say "expands to CapaProblem", which makes them whole items in
    # a compact spelling rather than pieces of one.
    "SimpleMatching": "a terse matching problem; expands to a CapaProblem that "
                      "carries a MatchingGrader",
    "SimpleSortable": "a terse ordering problem; expands to a CapaProblem",
    "SimpleTextSelection": "a terse highlighting problem; expands to a CapaProblem",
}

_TAG = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9_]*)([^>]*?)(/?)>", re.S)


def mine(roots: list[str], inventory: dict) -> dict[str, dict]:
    """Every (grader, nested block) pair present in the corpus.

    The corpus is `olx_corpus.texts`, which excludes build artifacts and INCLUDES
    the 295 fenced examples in the block documentation. An earlier version globbed
    `*.olx` and so mined the psych course twice -- once from its repo and once
    from lo-blocks' `.stage` staging copy, nine of whose files were stale -- while
    ignoring the documentation entirely.

    A lenient tag scanner, not an XML parse: OLX carries prose and generated
    prompt bodies, and a strict parser refuses files this has to read.
    """
    import olx_corpus

    graders = {b["name"] for b in inventory["blocks"] if b["role"] == "grader"}
    wanted = {b["name"] for b in inventory["blocks"]
              if b["role"] in ("gradable_input", "gradable_item_family", "item_part")}
    found: dict[str, dict] = {}
    files = 0
    for label, text in olx_corpus.texts(roots):
        files += 1
        stack: list[str] = []
        for m in _TAG.finditer(text):
            close, name, _attrs, selfclose = m.groups()
            if close:
                while stack and stack.pop() != name:
                    pass
                continue
            anc = [g for g in stack if g in graders]
            if name in wanted and anc:
                rec = found.setdefault(f"{anc[-1]}|{name}", {"n": 0, "files": set()})
                rec["n"] += 1
                rec["files"].add(label)
            if not selfclose:
                stack.append(name)
    for rec in found.values():
        rec["files"] = sorted(rec["files"])
    return {"files_scanned": files, "pairs": found}


def verify(inventory: dict, evidence: dict) -> list[str]:
    """Both directions. A declaration nobody demonstrates, and evidence nobody declared."""
    out = []
    graders = {b["name"] for b in inventory["blocks"] if b["role"] == "grader"}
    inputs = {b["name"] for b in inventory["blocks"]
              if b["role"] in ("gradable_input", "gradable_item_family")}
    parts = {b["name"] for b in inventory["blocks"] if b["role"] == "item_part"}
    seen = evidence["pairs"]

    for g in sorted(graders - set(GRADER_INPUTS)):
        out.append(f"{g} is a grader and this table says nothing about it -- every "
                   f"grader needs a declared mechanism, even if its input list is "
                   f"empty")
    for g in sorted(set(GRADER_INPUTS) - graders):
        out.append(f"{g} is declared here but the inventory does not call it a grader")

    for g, spec in sorted(GRADER_INPUTS.items()):
        for i in spec["inputs"]:
            if i not in inputs:
                out.append(f"{g} declares input {i}, which the inventory does not "
                           f"call a gradable input")
            elif f"{g}|{i}" not in seen and i not in (spec.get("doc_only") or {}):
                out.append(f"{g} <- {i} is DECLARED but demonstrated nowhere in the "
                           f"corpora and cites no documentation -- a pairing "
                           f"nobody shows is a guess with a table around it")
        for p in spec.get("parts", []):
            if p not in parts:
                out.append(f"{g} declares part {p}, which the inventory does not "
                           f"call an item part")

    for key, rec in sorted(seen.items()):
        g, i = key.split("|")
        if i in parts:
            if i not in (GRADER_INPUTS.get(g) or {}).get("parts", []):
                out.append(f"{g} <- {i} appears in {rec['n']} place(s) "
                           f"({rec['files'][0]}) and is NOT declared as a part of {g}")
            continue
        if i not in (GRADER_INPUTS.get(g) or {}).get("inputs", []):
            out.append(f"{g} <- {i} is DEMONSTRATED in {rec['n']} place(s) "
                       f"({rec['files'][0]}) and is not declared -- new evidence "
                       f"must force a decision, not be absorbed")

    for i in sorted(inputs - set(SELF_GRADING) - set(RESPONSE_SOURCES)):
        out.append(f"{i} collects a response and RESPONSE_SOURCES does not "
                   f"classify it -- say what the student produces and which "
                   f"grader it is FOR, since 'an LLM could read it' is true of "
                   f"nearly everything and recommends nothing")
    for src, spec in sorted(RESPONSE_SOURCES.items()):
        for g in spec["prefers"]:
            if g in (LLM_CHAIN, "ungraded", "self-measuring"):
                continue
            if g not in GRADER_INPUTS:
                out.append(f"{src} prefers {g}, which is not a declared grader")
            elif src in inputs and src not in GRADER_INPUTS[g]["inputs"]:
                out.append(f"{src} prefers {g}, but {g} does not declare {src} "
                           f"among its inputs -- the two tables disagree")
    return out


def _load_inventory(path: str | None) -> dict:
    # FROM THE MACHINERY, not from beside this file. The shape inventory is an
    # artifact of `shape_inventory.py` and lives with it; `HERE` became the
    # fixture directory when this module moved, and the error message then
    # instructed a reader to write the inventory into the course's data.
    path = path or str(paths.SCORING / "SHAPE_INVENTORY.json")
    if not os.path.exists(path):
        raise SystemExit(f"grader_inputs: no shape inventory at {path}; run "
                         f"shape_inventory.py --json {path}")
    return json.load(open(path))


def main(argv=None) -> int:
    import paths

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--inventory", default=None)
    ap.add_argument("--corpus", action="append", default=None,
                    help="a directory of .olx to mine; repeatable")
    ap.add_argument("--json", metavar="PATH")
    args = ap.parse_args(argv)

    inv = _load_inventory(args.inventory)
    import olx_corpus
    roots = args.corpus or olx_corpus.default_roots()
    ev = mine(roots, inv)
    bad = verify(inv, ev)

    print(f"  {ev['files_scanned']} .olx scanned, {len(ev['pairs'])} distinct "
          f"nestings found")
    nc = sum(1 for v in RESPONSE_SOURCES.values() if v["kind"] == CONSTRUCTED)
    fb = sum(1 for v in RESPONSE_SOURCES.values() if v["llm_fallback"])
    print(f"  {len(GRADER_INPUTS)} graders declared, "
          f"{sum(len(s['inputs']) for s in GRADER_INPUTS.values())} nested pairings")
    doc = sum(len(s.get("doc_only") or {}) for s in GRADER_INPUTS.values())
    print(f"    {doc} pairing(s) rest on the block's own docs, not on an .olx")
    print(f"  {len(RESPONSE_SOURCES)} response sources: {nc} constructed, "
          f"{len(RESPONSE_SOURCES) - nc} selected; {fb} take the LLM path only as "
          f"a FALLBACK")
    for mech in (NESTED, TARGETED, REFERENCED):
        n = sum(1 for s in GRADER_INPUTS.values() if s["mechanism"] == mech)
        if n:
            print(f"    {mech:<12} {n} grader(s)")

    if args.json:
        json.dump({"schema_version": SCHEMA_VERSION, "declared": GRADER_INPUTS,
                   "response_sources": RESPONSE_SOURCES,
                   "self_grading": SELF_GRADING,
                   "llm_reachable": LLM_REACHABLE,
                   "evidence": ev}, open(args.json, "w"), indent=1)
        print(f"  written: {args.json}")

    if bad:
        print(f"\n  {len(bad)} PROBLEM(S):")
        for b in bad:
            print(f"    {b}")
        return 1
    print("  the declaration and the evidence agree, both ways.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
