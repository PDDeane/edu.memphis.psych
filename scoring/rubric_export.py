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
    """The rubric module for one handout, or None once its file is gone.

    Stage 5 deletes rubric_h1.py and rubric_h3.py: their data is the course
    file's now and is authored there. This used to raise ModuleNotFoundError,
    which meant the deletion made the course file UNREGENERATABLE -- h2's
    builders could not be re-expanded either, because the loop stopped at the
    first missing module. That is the one consequence that must not be found
    after the fact, so it returns None and `build` carries that handout forward
    from the file it is rewriting.

    TWO NAMES, ONE MODULE. Stage 6c renamed handout 2's module to
    `rubric_h2_source.py` -- same file, moved out of the scoring path to sit with
    `declaration_source` and `generator_source`. It is tried second rather than
    instead, so this keeps working whichever name a tree has, and a handout whose
    module truly went still returns None by falling through both.
    """
    sys.path.insert(0, HERE)
    for name in (f"rubric_h{handout}", f"rubric_h{handout}_source"):
        try:
            return __import__(name)
        except ModuleNotFoundError:
            continue
    return None


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
        "_utb": "handout 2's 'My Unwanted Target Behavior is' section",
        "_wgb": "handout 2's 'My Wanted Goal Behavior is' section",
    },
}


# ---------------------------------------------------------------------------
# WHERE THE AUTHORED TABLES LIVE. Four modules since 2026-09-23, split by the
# categories in `MATERIAL_CLASSIFICATION.md`: `course_metadata_source` (II, the
# tables headed for the OLX and course.json), `submission_markers_source` (IX,
# how a paper submission is taken apart), and `declaration_source` /
# `generator_source`, which kept their names and their category-III contents.
#
# RESOLVED BY NAME, not by naming a module at each site, because this exporter
# groups tables by SHAPE -- item-keyed vs course-level -- and that grouping cuts
# ACROSS the categories. `GENERATOR_TABLES` alone spans both: RESPONSE, CONTEXT
# and SHEET_ONLY are metadata while EVIDENCE, OMIT_GUIDANCE, MATCH_DEF and the
# two ITEM_NOTES are cross-scorer devices. A name-list entry therefore cannot say
# which module holds it, and hard-coding one per site would have to be revisited
# every time a table changes category -- which is the whole point of the split.
#
# TWO CLAIMANTS IS A REFUSAL. A split's characteristic failure is a table copied
# rather than moved: both modules define it, the export silently takes whichever
# module is listed first, and the two drift. That cannot pass here.
# ONE LIST, TWO CONSUMERS. `migrated_tables.BUILDERS` already had to know which
# modules hold authored tables, for the check that every migrated table still
# equals its source. A second copy here would be a list that can disagree with
# the one the audit uses -- and the audit would then pass while this exporter
# read a module it never verified.
def _source_modules() -> tuple[str, ...]:
    import migrated_tables

    return tuple(migrated_tables.BUILDERS)


def _authored(name: str, default=None):
    """The authored table `name`, from whichever source module defines it."""
    import importlib

    found = []
    for mod in _source_modules():
        value = getattr(importlib.import_module(mod), name, None)
        if value is not None:
            found.append((mod, value))
    if len(found) > 1:
        raise SystemExit(
            f"rubric_export: `{name}` is defined in {[m for m, _ in found]} -- two "
            f"source modules claim it, so which one the export carries would "
            f"depend on the order they are listed in. Move it, do not copy it.")
    return found[0][1] if found else default


def non_item_residue(item_ids: set[str]) -> tuple[dict, list[str]]:
    """-> (residue to carry at course level, refusals).

    Everything in an item-keyed table whose key is not an item. Declared keys are
    carried; undeclared ones REFUSE, because a table silently losing its
    non-item rows is indistinguishable from a table that never had them.
    """
    residue, bad = {}, []
    for table in sorted(GENERATOR_TABLES):
        data = _authored(table) or {}
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
    out = {}
    for table, field in sorted(GENERATOR_TABLES.items()):
        data = _authored(table) or {}
        if item_id in data:
            out[field] = data[item_id]
    return out


# The scoring DECLARATIONS. Seven of eight moved; `CONSENSUS_OVERLAP_BACKLOG` is
# keyed by participant and belongs in the gold file under C1b.
DECLARATION_TABLES = ("ASK_EQUIVALENT_PROMPTS",
                      "PROSE_ONLY_SLOTS", "PROSE_ONLY_JUDGED_AGAINST",
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
                      # PROBE_UNREACHABLE_PAIRS moved 2026-09-19, once `_key`
                      # could hold a frozenset. Before that `json.dumps`
                      # refused it and the table could not be exported at all.
                      "PROBE_UNREACHABLE_PAIRS",
                      # SLOT_STRUCTURE_FAMILIES and HAND_AUTHORED_ATTRS moved
                      # 2026-09-19. They were held back because the probe calls
                      # them INCONCLUSIVE -- but that verdict is about whether
                      # their CONSUMING CHECK enforces them, not about whether a
                      # bad migration would be noticed. `migrated_tables`
                      # answers the second, order-sensitively, and both are
                      # plainly authoring content: one names a family of this
                      # course's items, the other is keyed by (item, attribute).
                      "SLOT_STRUCTURE_FAMILIES", "HAND_AUTHORED_ATTRS",
                      # BLOCKS moved 2026-09-19 WITHOUT its `refs`, which
                      # `_context_refs` derives from the .olx -- storing that
                      # would put a derived value in the course file and freeze
                      # a map that changes whenever the .olx does.
                      "BLOCKS",
                      # SELFTEST_NAMED_FIXTURES moved 2026-09-20. Declaring the
                      # nine named fixtures in `enforcement.py` MOVED this
                      # course's item ids into the engine rather than removing
                      # them -- the ratchet caught the rise 10 -> 11 at once.
                      # It is a declaration ABOUT this course's items, like
                      # COUNTABLE_EXEMPT, so it belongs in the course file.
                      "SELFTEST_NAMED_FIXTURES",
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
def _comments_in(lines, lo, hi):
    """Every comment line in [lo, hi), de-indented. NOTHING IS DROPPED."""
    return [l.strip()[1:].lstrip() if l.strip()[1:].strip() else ""
            for l in lines[lo:hi] if l.strip().startswith("#")]


def _comment_runs(lines, lo, hi):
    """The same lines, GROUPED INTO RUNS, a run being consecutive comment lines.

    A flat list loses where one block ends and the next begins, and that
    structure is load-bearing: the §2e hook prints the LAST few blocks about an
    item and says how many earlier ones it is not showing. Q6 has twelve; a flat
    327-line list would either flood the output or be cut at an arbitrary point.

    Interleaved CODE ends a run. A blank line does not -- a comment paragraph
    broken by a bare `#` is one block, and treating it as two would split
    reasoning that was written as one argument.
    """
    runs, run = [], []
    for l in lines[lo:hi]:
        s = l.strip()
        if s.startswith("#"):
            run.append(s[1:].lstrip() if s[1:].strip() else "")
        elif s:
            if run:
                runs.append(run)
            run = []
    if run:
        runs.append(run)
    return runs


def rubric_notes() -> dict:
    """The rubric's REASONING, attributed to the item it is written about.

    `rubric_h1.py` is 49% comments -- 1,448 lines -- and `rubric_h3.py` 25%.
    Exporting the values alone and then deleting the modules would destroy that,
    and it is the expensive half: a rule's comment routinely records which
    hypotheses died on it and what they cost to kill. The same loss was caught
    on the gold side, where 707 lines came within one commit of going.

    BY SPAN, NOT BY ADJACENCY, which is the lesson from that one: a comment
    belongs to the item whose entry ENCLOSES it, because these entries are
    multi-line dicts whose comments sit inside the value they describe.
    Attributing by "the run immediately before an entry" lost 333 of 707 there,
    and the totals are asserted here so the question is answered by counting.

    `rubric_h2` yields nothing and that is correct: its items are built by the
    four factories A1c preserves, so its comments sit around the factory calls
    rather than inside the ITEMS literal -- and that module survives as the
    builder, so they are not at risk.
    """
    import ast

    out = {"items": {}, "handouts": {}, "runs": {}}
    for handout in (1, 2, 3):
        mod = _load(handout)
        if mod is None:
            # Its file is gone and its notes are already in the course file;
            # `build` merges them forward. Lifting them from a module that does
            # not exist is not a fallback, it is a crash -- which is what this
            # did on the first deletion rehearsal after the notes were carried.
            continue
        src = open(mod.__file__).read()
        lines = src.splitlines()
        tree = ast.parse(src)
        node = next((n for n in tree.body
                     if (isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
                         and n.targets[0].id == "ITEMS")
                     or (isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)
                         and n.target.id == "ITEMS")), None)
        if node is None or not isinstance(node.value, (ast.List, ast.Tuple)):
            continue
        had = sum(1 for l in lines[node.lineno - 1:node.end_lineno]
                  if l.strip().startswith("#"))
        cursor, got = node.lineno, 0
        for el in node.value.elts:
            cursor_start = cursor
            run = _comments_in(lines, cursor, el.end_lineno)
            cursor = el.end_lineno
            if not run:
                continue
            iid = None
            if isinstance(el, ast.Dict):
                for k, v in zip(el.keys, el.values):
                    if (isinstance(k, ast.Constant) and k.value == "id"
                            and isinstance(v, ast.Constant)):
                        iid = str(v.value)
            if iid is None:
                raise SystemExit(
                    f"rubric_export: {len(run)} comment line(s) in rubric_h{handout}'s "
                    f"ITEMS belong to an entry with no readable `id`. They have "
                    f"nowhere to go, so the export stops rather than dropping them.")
            out["items"].setdefault(iid, []).extend(run)
            out["runs"].setdefault(iid, []).extend(
                _comment_runs(lines, cursor_start, el.end_lineno))
            got += len(run)
        tail = _comments_in(lines, cursor, node.end_lineno)
        got += len(tail)
        if got != had:
            raise SystemExit(
                f"rubric_export: rubric_h{handout}'s ITEMS holds {had} comment "
                f"line(s) and {got} were lifted. The reasoning is the expensive "
                f"half of this record; it does not get dropped on the way out.")
        # AND THE PROSE OUTSIDE `ITEMS`: the module header, which explains what
        # the handout IS. 54 lines in h1 and 34 in h3, lost with the file.
        outside = (_comments_in(lines, 0, node.lineno - 1)
                   + _comments_in(lines, node.end_lineno, len(lines)))
        if outside:
            out["handouts"][str(handout)] = outside
    return out


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
    return [[_key(k), v] for k, v in table.items()]


def _key(k):
    """One declaration key, in a form JSON holds and `coursedata._detag` inverts.

    A FROZENSET IS TAGGED, NOT LISTED. `PROBE_UNREACHABLE_PAIRS` is keyed by
    `(item, frozenset({slot, slot}))` -- a pair of slots the probe cannot reach
    separately, where which one comes first is meaningless. `json.dumps` refuses
    a frozenset outright, so this table could not be exported at all; storing it
    as a bare list instead would export fine and come back a TUPLE, turning an
    unordered pair into an ordered one and losing every lookup.

    SORTED INSIDE THE TAG, because a frozenset has no order of its own and an
    arbitrary iteration order would rewrite the file on every export for no
    reason. The decoder rebuilds a frozenset, where the order means nothing
    again.
    """
    if isinstance(k, frozenset):
        return {"__frozenset__": sorted(_key(x) for x in k)}
    if isinstance(k, (tuple, list)):
        return [_key(x) for x in k]
    return k


_CARRIED_FORWARD: list = []


def _prior_doc():
    """The course file as it stands, for handouts whose module is gone."""
    import json as _json

    try:
        import coursedata

        path = coursedata.course_path()
        return _json.load(open(path))
    except Exception:
        return None


def build(course_id: str) -> tuple[dict, list[dict]]:
    doc = {"schema_version": SCHEMA_VERSION, "course": course_id,
           "handouts": {}, "items": []}
    full_report = []
    for h in HANDOUTS:
        mod = _load(h)
        if mod is None:
            # AUTHORED IN THE FILE NOW. Carry this handout's items, its authored
            # block and its notes forward EXACTLY as they stand, so regenerating
            # for another handout cannot quietly rewrite one whose source is
            # gone. Refuses rather than emitting a course file with a handout
            # missing, which would read as "this course has two handouts".
            prior = _prior_doc()
            if prior is None:
                raise SystemExit(
                    f"rubric_export: rubric_h{h}.py is gone and there is no course "
                    f"file to carry handout {h} forward from. Its items exist "
                    f"nowhere -- refusing to write a course file that silently "
                    f"drops a handout.")
            kept = [it for it in prior.get("items", [])
                    if str(it.get("handout")) == str(h)]
            if not kept:
                raise SystemExit(
                    f"rubric_export: rubric_h{h}.py is gone and the course file "
                    f"carries no items for handout {h}. Refusing to write a "
                    f"course file that drops it.")
            doc["handouts"][str(h)] = prior.get("handouts", {}).get(str(h), {})
            doc["items"].extend(kept)
            _CARRIED_FORWARD.append(h)
            continue
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

    ids = {str(it.get("id")) for it in doc["items"]}
    residue, refusals = non_item_residue(ids)
    if refusals:
        raise SystemExit("rubric_export: " + "\n  ".join(refusals))
    doc["generator"] = {
        name: _jsonable(_authored(name), f"generator.{name}")
        for name in COURSE_LEVEL_GENERATOR
        if _authored(name) is not None}
    # The per-handout segmentation locators, ORDERED. Course-level because the
    # order is load-bearing and the lists carry non-item keys, so no item entry
    # can hold them.
    # Per-handout reference maps: component id -> context handed to the grader.
    # Course-level because they are keyed by COMPONENT, not by item.
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
        name: _jsonable(_pairs(_denamespace(_authored(name))
                               if name == "JOBS"
                               else _authored(name)),
                        f"declarations.{name}")
        for name in DECLARATION_TABLES
        if _authored(name) is not None}

    # THE AUTHORED KEY ORDER OF EACH GENERATOR TABLE. The fields themselves live
    # on the item entries, so rebuilding a table iterates items in RUBRIC order
    # and loses the order the table was written in. For these three that turns
    # out to be harmless -- CONTEXT is a keyed lookup, SHEET_ONLY is always
    # `sorted()`, MATCH_DEF is never iterated -- but "harmless" was established by
    # reading every consumer, and the JOBS case had just shown that a table's
    # order can BE the data. Storing it costs three short lists and removes the
    # need to keep being right about that.
    doc["generator"]["TABLE_ORDER"] = {
        table: [k for k in _authored(table, {})]
        for table in sorted(GENERATOR_TABLES)
        if _authored(table)}

    doc["generator"]["CONTEXT_REFS"] = {
        str(h): _jsonable(_authored(f"_H{h}_CTX"), f"generator._H{h}_CTX")
        for h in HANDOUTS
        if _authored(f"_H{h}_CTX") is not None}
    doc["generator"]["SEGMENT_MARKERS"] = {
        str(h): _jsonable(_authored(f"H{h}_MARKERS"), f"generator.H{h}_MARKERS")
        for h in HANDOUTS
        if _authored(f"H{h}_MARKERS") is not None}
    for table, extra in sorted(residue.items()):
        doc["generator"][f"{table}__non_item"] = _jsonable(
            extra, f"generator.{table}__non_item")
    # THE REASONING, carried beside the values. See `rubric_notes`: 1,567 lines
    # of it are written INSIDE the ITEMS literals of h1 and h3, and a further
    # 548 in the three module headers. Exporting the values alone and deleting
    # the modules would take all of it.
    _notes = rubric_notes()
    # MERGE, DO NOT REPLACE. A handout whose module is gone contributes no notes
    # here, and assigning wholesale would delete the very record that was
    # carried into this file so the module could go.
    _prior = _prior_doc() or {}
    for _h in _CARRIED_FORWARD:
        _ids = {str(it.get("id")) for it in doc["items"]
                if str(it.get("handout")) == str(_h)}
        for _key, _dest in (("item_notes", _notes["items"]),
                            ("item_note_runs", _notes["runs"])):
            for _iid, _v in (_prior.get(_key) or {}).items():
                if str(_iid) in _ids:
                    _dest.setdefault(_iid, _v)
        _hn = (_prior.get("handout_notes") or {}).get(str(_h))
        if _hn is not None:
            _notes["handouts"].setdefault(str(_h), _hn)
    doc["item_notes"] = _notes["items"]
    doc["handout_notes"] = _notes["handouts"]
    # AND THE RUN STRUCTURE. The §2e hook prints the LAST few blocks about an
    # item and reports how many earlier ones it is not showing; a flat list
    # cannot say where one block ends. See `_comment_runs`.
    doc["item_note_runs"] = _notes["runs"]

    # THE RUBRIC FIELDS DO NOT GO IN THE COURSE FILE ANY MORE (step 3d). They
    # live in `bmod_rubric.olx`, which `coursedata` reads and which is the single
    # source. Emitting them here would put a SECOND copy back on every rebuild --
    # and handout 2's source module is still present, so this is not hypothetical:
    # a plain `rubric_export` run would have restored twelve items' worth of
    # rubric silently, and the deletion would have lasted until someone rebuilt.
    #
    # `id` and `handout` survive because they are not rubric data: `id` is the key
    # both groups are reached by, and `handout` is course structure the `<Item>`
    # schema refuses. Handouts whose module is gone are carried forward from the
    # prior file and are projected here too, so both routes agree.
    import coursedata as _CD
    _keep = {"id", "handout"} | set(_CD.GENERATOR_FIELDS)
    doc["items"] = [{k: v for k, v in it.items() if k in _keep}
                    for it in doc["items"]]
    return doc, full_report


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--course", default="edu.memphis.psych")
    ap.add_argument("--out", required=True)
    # THE RUBRIC'S OWN OUTPUT. The course file is metadata and wiring; the RUBRIC
    # belongs in the content, as a component the course links beside the three
    # handouts. Emitting it here rather than from a script run by hand is what
    # makes it a build product: one program, one pass, both artifacts from the
    # same `build()` result, so they cannot describe different rubrics.
    # `--olx` WAS HERE AND RETIRED AT STEP 3D. It rendered `bmod_rubric.olx`
    # from this builder's output, which made the component a build product. The
    # component is now the SOURCE -- `coursedata` reads it and the course file no
    # longer carries a rubric to render from -- so regenerating it could only
    # overwrite the source with a projection of itself. The next step is authoring
    # it by hand, which `check_the_rubric_component_is_current`'s own docstring
    # named as this flag's expiry: "retire it in the same commit that stops
    # generating the file".
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
