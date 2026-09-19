#!/usr/bin/env python3
"""Write the rubric modules out as the course's canonical JSON.

A1c: `rubric_h2`'s four builders survive as an AUTHORING tool that GENERATES this
file. No reader ever instantiates a template, so the file carries every item in
full and the readers stay simple.

DERIVED-OR-AUTHORED IS DECIDED BY RECOMPUTATION, NEVER BY A LIST. §9.0 sorted the
module exports with a substring test -- does the assignment mention `ITEMS`, a
loop, `sum(` or `BY_ID` -- and says in as many words that it is "a starting point,
not a finding". An export that ACTS on that list can silently lose data: drop
something that is not in fact derivable and the value is gone.

So each candidate is RECOMPUTED and compared. A value is dropped only when a
known derivation reproduces it EXACTLY; everything else is carried as authored
data, whatever §9.0 guessed. The comparison is printed, so §9.0 is corrected by
this run rather than left standing.

CONSERVATIVE BY CONSTRUCTION. Carrying a value that turns out to be derivable
costs a few kilobytes. Dropping one that is not loses it. Where this tool cannot
recompute something it CARRIES it -- and says so -- rather than trusting a guess.

NO FIELD TAGGING HERE. §9.2a's RUBRIC/GENERATOR split is applied at Stage 4, when
`olx_prompts.py`'s generator fields arrive under B2a. Tagging at Stage 2 would
mark every field RUBRIC, make the classification trivially uniform, and let
T2.2's check pass while proving nothing -- the vacancy T0.1 exists to catch,
reproduced in a new place.

DETERMINISTIC MEANS A PINNED ORDER. Python dicts are insertion-ordered and the
builders construct in loops, so an unpinned file changes whenever iteration order
does: a large diff with no content, which reviewers learn to skim. Keys are sorted
within an entry; items stay in RUBRIC order, because that is how a person reads
them.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

SCHEMA_VERSION = 1
HERE = os.path.dirname(os.path.abspath(__file__))
HANDOUTS = (1, 2, 3)

# THE DERIVATIONS LIVE IN THE READER. Imported, never redefined: the export
# decides what to DROP and `coursedata.py` REBUILDS it, which is one question
# asked from two sides. Two implementations that must agree is the defect T5.1 had
# to be redesigned to avoid, and it would fail the same way here -- the export
# dropping something the reader cannot rebuild loses it silently.
#
# A candidate absent from that table is CARRIED, not dropped. The table is what
# can be PROVEN rebuildable, never what someone believed was derivable: §9.0
# called twelve names derived and two are proven, so A2a is two-twelfths honoured
# and this file is larger than A2a intends until the reader learns the rest.
sys.path.insert(0, HERE)
from coursedata import DERIVATIONS          # noqa: E402  (after sys.path)


def _load(handout: int):
    sys.path.insert(0, HERE)
    return __import__(f"rubric_h{handout}")


def _exports(mod) -> dict:
    """Module-level names a reader could want: upper-case, not private."""
    return {n: getattr(mod, n) for n in dir(mod)
            if n.isupper() and not n.startswith("_")}


def classify(mod) -> tuple[dict, list[dict]]:
    """-> (carried authored values, per-candidate report).

    Every export except ITEMS is a candidate. It is dropped only if a known
    derivation reproduces it exactly.
    """
    items = list(getattr(mod, "ITEMS", []) or [])
    carried, report = {}, []
    for name, value in sorted(_exports(mod).items()):
        if name == "ITEMS":
            continue
        fn = DERIVATIONS.get(name)
        if fn is None:
            carried[name] = value
            report.append({"name": name, "verdict": "carried",
                           "why": "no derivation this tool can perform"})
            continue
        try:
            again = fn(items)
        except Exception as exc:
            carried[name] = value
            report.append({"name": name, "verdict": "carried",
                           "why": f"derivation raised {type(exc).__name__}: {exc}"})
            continue
        if again == value:
            report.append({"name": name, "verdict": "dropped",
                           "why": "recomputation reproduced it exactly"})
        else:
            carried[name] = value
            report.append({"name": name, "verdict": "carried",
                           "why": "recomputation DIFFERED -- not derivable after all"})
    return carried, report


def _jsonable(x, path="") -> object:
    """Refuse silently dropping anything this cannot represent."""
    if isinstance(x, dict):
        # INSERTION ORDER, NOT SORTED. This sorted, on T2.1's "pinned order"
        # reasoning: a canonical file gives reviewable diffs. That is right for a
        # rubric item, whose field order carries nothing -- and WRONG the moment
        # a table arrives whose order IS the data. `JOBS[item]["fields"]` maps
        # component -> paper section in the order the boxes are read, and
        # alphabetising it changed what the fixture extracted.
        #
        # It cost six wrong hypotheses to find, because the dicts compare EQUAL:
        # `==` ignores order, so every value, type and outer-key check passed
        # while the payload was scrambled. Determinism does not need sorting --
        # the builders' own order is deterministic, so the same input still
        # produces the same bytes.
        return {str(k): _jsonable(v, f"{path}.{k}") for k, v in x.items()}
    # A TUPLE IS TAGGED, NOT FLATTENED. JSON has no tuple, so an untagged tuple
    # comes back a list -- and `("section", "Q1")` becoming `["section", "Q1"]`
    # is a silent shape change that no behavioural test is obliged to notice.
    # Four tables in `olx_prompts` and one in `agreement_app` had drifted this
    # way before `migrated_tables.py` compared them against their authored copies.
    #
    # Tagging makes the round trip exact BY CONSTRUCTION rather than by each
    # consumer remembering to convert its own values back.
    if isinstance(x, tuple):
        return {"__tuple__": [_jsonable(v, f"{path}[{i}]") for i, v in enumerate(x)]}
    if isinstance(x, list):
        return [_jsonable(v, f"{path}[{i}]") for i, v in enumerate(x)]
    if isinstance(x, (str, int, float, bool)) or x is None:
        return x
    raise SystemExit(
        f"rubric_export: {path or '<root>'} holds {type(x).__name__}, which this "
        f"tool cannot represent. That is an ERROR, not an omission -- a field "
        f"quietly dropped here is a field lost.")


# STAGE 4 (B2a). `olx_prompts.py`'s item-keyed tables become GENERATOR FIELDS on
# the item entry. The names are prefixed `prompt_` because `CONTEXT` would
# otherwise land as `context`, which the rubric already uses for something else,
# and §9.2a forbids a field naming two groups.
#
# The two NON item-keyed tables -- SCORING_DIVERGENCES and PROBE_REACH_LIMITS --
# are lists about the course as a whole, not about any item, so they are carried
# as course-level authored values and not folded onto entries. Putting a
# course-wide list on 26 items would be 26 copies of one fact.
GENERATOR_TABLES = {
    "ACTION": "prompt_action",
    "RESPONSE": "prompt_response",
    "CONTEXT": "prompt_context",
    "SHEET_ONLY": "prompt_sheet_only",
    "EVIDENCE": "prompt_evidence",
    "OMIT_GUIDANCE": "prompt_omit_guidance",
    "MATCH_DEF": "prompt_match_def",
    "ITEM_NOTES": "prompt_notes",
    "ITEM_NOTES_WHY": "prompt_notes_why",
}
COURSE_LEVEL_GENERATOR = ("SCORING_DIVERGENCES", "PROBE_REACH_LIMITS")

# Keys in an item-keyed table that are NOT item ids, declared with what they are.
# `CONTEXT` carries context for handout 2's two SECTION headings as well as for
# its items, and folding the table onto item entries would have dropped both
# without a word. editguard caught it -- the write that removed the tables listed
# `CONTEXT['_utb']` and `CONTEXT['_wgb']` among the 76 entries it was about to
# take, and they were the only two that had nowhere to land.
#
# An UNDECLARED non-item key is now a REFUSAL, not a silent drop: the next table
# to arrive with one must be decided on rather than quietly truncated.
NON_ITEM_KEYS = {
    "CONTEXT": {
        "_utb": "handout 2's '{{corpus:Q1/p3:response:0:27:sha=c8e59699d1a0:shape=C81008}} is' section",
        "_wgb": "handout 2's '{{corpus:Q2/p3:response:0:23:sha=d743f1f68d1a:shape=C8408}} is' section",
    },
}


def non_item_residue(item_ids: set[str]) -> tuple[dict, list[str]]:
    """-> (residue to carry at course level, refusals).

    Everything in an item-keyed table whose key is not an item. Declared keys are
    carried; undeclared ones REFUSE, because a table silently losing its
    non-item rows is indistinguishable from a table that never had them.
    """
    import generator_source

    residue, bad = {}, []
    for table in sorted(GENERATOR_TABLES):
        data = getattr(generator_source, table, None) or {}
        extra = {k: v for k, v in data.items() if k not in item_ids}
        if not extra:
            continue
        declared = NON_ITEM_KEYS.get(table, {})
        undeclared = sorted(set(extra) - set(declared))
        if undeclared:
            bad.append(
                f"{table} has non-item key(s) {undeclared} and NON_ITEM_KEYS does "
                f"not say what they are. Folding the table onto item entries "
                f"would drop them. Declare them, or move the table to course "
                f"level.")
            continue
        residue[table] = extra
    return residue, bad


def generator_fields_for(item_id: str) -> dict:
    """The generator fields this item carries, read from the incumbent module.

    Absent keys are OMITTED, never written as null: `SHEET_ONLY` names three
    items of twenty-six, and storing `prompt_sheet_only: null` on the other
    twenty-three would turn "this item is not in that table" into "this item has
    an empty value", which is a different claim and one the reader would have to
    undo.
    """
    # THE BUILDER, NOT THE PIPELINE MODULE. `olx_prompts` now READS the course
    # file, so sourcing the tables from it would make regenerating the file
    # depend on the file being regenerated. `generator_source` is the authored
    # input, kept outside the scoring path for exactly this reason.
    import generator_source

    out = {}
    for table, field in sorted(GENERATOR_TABLES.items()):
        data = getattr(generator_source, table, None) or {}
        if item_id in data:
            out[field] = data[item_id]
    return out


# The scoring DECLARATIONS. Seven of eight moved; `CONSENSUS_OVERLAP_BACKLOG` is
# keyed by participant and belongs in the gold file under C1b.
DECLARATION_TABLES = ("PROSE_ONLY_SLOTS", "PROSE_ONLY_JUDGED_AGAINST",
                      "MULTI_BLOCK_DECLARED", "DESIGNED_TEXT",
                      "DECOMPOSITION_DIVERGENCES", "UNCHARGED_VERDICTS",
                      "APP_ONLY_SLOTS",
                      # COUNTABLE_EXEMPT moved 2026-09-19. It was one of five
                      # that `declaration_source` records as "did not move", on
                      # a measurement from `table_sensitivity.py` -- a tool
                      # retired the same day for reporting a verifier that
                      # RAISES as an unread table. The established probe says
                      # READ: emptying it changes the output.
                      "COUNTABLE_EXEMPT",
                      # from score.py and agreement_app.py
                      "PAPER_ITEM_NOTES", "PAPER_ITEM_NOTES_WHY",
                      "CONTEXT_SOURCE", "JOBS", "HANDOUT_FIELDS")


# NO `sort_keys`. AUTHORED ORDER IS DATA. Writing the file with
# `sort_keys=True` alphabetised every nested dict, and `JOBS[item]["fields"]`
# maps component id -> paper section in an order that decides which box is read
# first. Alphabetising it changed what the fixture extracted, and
# `check_fixture_agrees_with_gold` reported `Q6/p15 state_c2 is EMPTY` -- a
# finding that survived six wrong hypotheses (value, outer order, types, import
# side effects, mutation, cache) because the dicts compare EQUAL: `==` ignores
# order, and the order was the payload.
#
# Determinism does not need sorting here: the source order is itself
# deterministic, so the same builders produce the same bytes.
def _pairs(table: dict) -> list:
    """A dict with TUPLE KEYS, as JSON can hold it: a list of [key, value].

    Six of the seven declaration tables are keyed by tuples -- `("Q4a",
    "antecedent_kind_1", "rule_addition")` -- and JSON has string keys only.
    Joining the parts with a separator would be lossless only until a part
    contained the separator, and would silently stop round-tripping on the day
    one did. A list of pairs keeps the key as a LIST, which is what a tuple is.

    `rubric_equivalence` and the reader both round-trip this, and the round trip
    is asserted rather than assumed -- see `--verify-declarations`.
    """
    return [[list(k) if isinstance(k, tuple) else k, v] for k, v in table.items()]


def build(course_id: str) -> tuple[dict, list[dict]]:
    doc = {"schema_version": SCHEMA_VERSION, "course": course_id,
           "handouts": {}, "items": []}
    full_report = []
    for h in HANDOUTS:
        mod = _load(h)
        items = list(getattr(mod, "ITEMS", []) or [])
        carried, report = classify(mod)
        for r in report:
            r["handout"] = h
        full_report += report
        doc["handouts"][str(h)] = {"authored": _jsonable(carried, f"h{h}")}
        for it in items:                       # RUBRIC order, deliberately
            entry = _jsonable(it, f"h{h}.{it.get('id')}")
            entry["handout"] = h
            gen = generator_fields_for(str(it.get("id")))
            if gen:
                entry.update(_jsonable(gen, f"h{h}.{it.get('id')}.generator"))
            doc["items"].append(entry)

    import generator_source

    ids = {str(it.get("id")) for it in doc["items"]}
    residue, refusals = non_item_residue(ids)
    if refusals:
        raise SystemExit("rubric_export: " + "\n  ".join(refusals))
    doc["generator"] = {
        name: _jsonable(getattr(generator_source, name, None), f"generator.{name}")
        for name in COURSE_LEVEL_GENERATOR
        if getattr(generator_source, name, None) is not None}
    # The per-handout segmentation locators, ORDERED. Course-level because the
    # order is load-bearing and the lists carry non-item keys, so no item entry
    # can hold them.
    # Per-handout reference maps: component id -> context handed to the grader.
    # Course-level because they are keyed by COMPONENT, not by item.
    import declaration_source

    # GOAL D: the course id comes OUT of the values. Every job's `screen` was
    # stored as `edu.memphis.psych/bmod_h1_q1` and every job carried `ns` with the
    # same course id -- twice over, in a file whose own `course` field already
    # says it. `measured.py` then does `job["screen"].split("/")[-1]`, stripping
    # back off what was put on.
    #
    # The FILE holds the bare id and no `ns`; the reader recomposes both from the
    # course field, so runtime values are unchanged. A move and a reshape were
    # kept apart deliberately: JOBS moved first, with a test, and this is the
    # reshape with its own.
    def _denamespace(jobs: dict) -> dict:
        out = {}
        for item, spec in jobs.items():
            spec = dict(spec)
            ns = spec.pop("ns", None)
            screen = spec.get("screen")
            if ns and isinstance(screen, str) and screen.startswith(f"{ns}/"):
                spec["screen"] = screen[len(ns) + 1:]
            out[item] = spec
        return out

    doc["declarations"] = {
        name: _jsonable(_pairs(_denamespace(getattr(declaration_source, name))
                               if name == "JOBS"
                               else getattr(declaration_source, name)),
                        f"declarations.{name}")
        for name in DECLARATION_TABLES
        if getattr(declaration_source, name, None) is not None}

    # THE AUTHORED KEY ORDER OF EACH GENERATOR TABLE. The fields themselves live
    # on the item entries, so rebuilding a table iterates items in RUBRIC order
    # and loses the order the table was written in. For these three that turns
    # out to be harmless -- CONTEXT is a keyed lookup, SHEET_ONLY is always
    # `sorted()`, MATCH_DEF is never iterated -- but "harmless" was established by
    # reading every consumer, and the JOBS case had just shown that a table's
    # order can BE the data. Storing it costs three short lists and removes the
    # need to keep being right about that.
    doc["generator"]["TABLE_ORDER"] = {
        table: [k for k in getattr(generator_source, table, {})]
        for table in sorted(GENERATOR_TABLES)
        if getattr(generator_source, table, None)}

    doc["generator"]["CONTEXT_REFS"] = {
        str(h): _jsonable(getattr(generator_source, f"_H{h}_CTX", None),
                          f"generator._H{h}_CTX")
        for h in HANDOUTS
        if getattr(generator_source, f"_H{h}_CTX", None) is not None}
    doc["generator"]["SEGMENT_MARKERS"] = {
        str(h): _jsonable(getattr(generator_source, f"H{h}_MARKERS", None),
                          f"generator.H{h}_MARKERS")
        for h in HANDOUTS
        if getattr(generator_source, f"H{h}_MARKERS", None) is not None}
    for table, extra in sorted(residue.items()):
        doc["generator"][f"{table}__non_item"] = _jsonable(
            extra, f"generator.{table}__non_item")
    return doc, full_report


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--course", default="edu.memphis.psych")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    doc, report = build(args.course)
    dropped = [r for r in report if r["verdict"] == "dropped"]
    carried = [r for r in report if r["verdict"] == "carried"]

    print(f"  items: {len(doc['items'])}   candidates: {len(report)}")
    print(f"  dropped as derived (recomputation reproduced them): {len(dropped)}")
    for r in dropped:
        print(f"    h{r['handout']} {r['name']}")
    print(f"  carried as authored: {len(carried)}")
    for r in carried:
        print(f"    h{r['handout']} {r['name']:<24} {r['why'][:52]}")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(doc, fh, indent=1, sort_keys=False)
        fh.write("\n")
    print(f"\n  written: {args.out} ({os.path.getsize(args.out):,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
