"""Score Handout 1 submissions, one rubric item at a time.

Design notes:
  * One call per rubric item, not one per document. Each item has its own
    point ledger and its own feedback cell, and the gold data is per-item, so
    per-item calls are both more accurate and directly measurable.
  * The model never returns a score. It returns credit checks and a deduction
    ledger; the score is computed here as max - sum(deductions), clamped to
    [0, max]. That mirrors how these graders actually write ("-1 pt: ...") and
    makes every point auditable.
  * Items are scored in dependency order, because several are graded against
    other items: Q2's WGB against Q1's UTB, Q4b/Q4c against Q4a for
    distinctness, and Q6 against 4a and 4c for matching. Neighbours listed in
    a rubric record's `context` are passed in as read-only context.

Usage:
  python3 score_h1.py                       # score all 20, CLI backend
  python3 score_h1.py --participants 1 2 3   # subset
  python3 score_h1.py --backend api          # official SDK (needs creds)
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

import paths
import functools
import argparse
import glob
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from backends import BackendError, make_backend
from forms import config, find_submissions
from olx_prompts import _criteria_section
# The rubric through `handouts`, not the module: `config(h)["rubric"]` serves a
# view onto the course file, so this keeps working when Stage 5 deletes
# `rubric_h*`. The names below are bound from it, so every use is unchanged.
import forms as _H_RUBRIC
def _criteria_rubric():
    """The rubric of the handout carrying the CRITERIA items. J-3.

    WAS `config(2)`. It never meant "handout two" -- it meant "the handout whose
    items are scored from criteria rather than from a credit list", which is
    handout 2 only in this course. REFUSES rather than guessing when the course
    declares none or several: falling back to a number is how an engine scores
    the wrong handout and says nothing.
    """
    hs = _H_RUBRIC.carrying("derive_from_criteria")
    if len(hs) != 1:
        raise SystemExit(
            f"score.py: expected exactly ONE handout with `derive_from_criteria` "
            f"items, found {hs or 'none'}. The criteria scorer binds one rubric at "
            f"import; a course with several needs that binding made per-handout "
            f"first (goal E moves this out entirely).")
    return _H_RUBRIC.config(hs[0])["rubric"]


_RUBRIC2 = _criteria_rubric()
# GUARDED, per `_RubricView`'s documented contract. J-5. `__getattr__` RAISES on
# an absent name by design -- `getattr(rub, "SLOT_SPEC", {})` is a real call site
# and the raise is what makes a typo findable -- so reading these bare made every
# course declare every derivation even when it uses none of them. That is what
# the stub course was forced to do.
#
# THE DEFAULT IS AN ANSWER HERE, not a shrug. Each of these names a set of items
# of some kind, so "the course declared none" and "no item is of that kind" are
# the same fact, and empty is the truthful reading. That is NOT so for
# `coursedata.derived()`, where empty means ABSENT and falls through to the
# authored value; do not carry this default across to that.
BARRIER_PICK_ITEMS = getattr(_RUBRIC2, "BARRIER_PICK_ITEMS", ())
CADENCE_BARRIER_ITEMS = getattr(_RUBRIC2, "CADENCE_BARRIER_ITEMS", ())
CONTINGENCY_GATE_ITEMS = getattr(_RUBRIC2, "CONTINGENCY_GATE_ITEMS", ())
MOVE_PICK_ITEMS = getattr(_RUBRIC2, "MOVE_PICK_ITEMS", ())
POLARITY_GATE_ITEMS = getattr(_RUBRIC2, "POLARITY_GATE_ITEMS", ())
REQUIRED_MOVE = getattr(_RUBRIC2, "REQUIRED_MOVE", {})
from docx_text import extract_media, graph_evidence
from segment import repair_orphans, segment
from segment import course_hook

# OPTIONAL, because it is the COURSE's. Absent -> no hint, which is an answer.
utb_hint = course_hook("utb_hint", lambda _path: None)
import paths as _p7   # J-7b: this course's handout file names

SYSTEM_TMPL = """You are an experienced teaching assistant grading {blurb}
This is PSYC 1030 (General Psychology, intro level, first-year students).

You grade ONE rubric item at a time against the rubric supplied in the message.

Rules you must follow:
1. Award credit component by component. For each component in the rubric's
   credit list, decide whether the student's response earns it, and quote the
   span of the response that earns it. Quote verbatim; never paraphrase into
   the evidence field.
2. Report every failure as a deduction drawn from the supplied deduction list,
   using that list's exact `code`. The point value is the rubric's, not yours —
   you never restate it. A deduction marked repeatable may appear more than
   once (e.g. two missing reasons = two REASON_MISSING entries). Do not invent
   codes.
3. Do NOT output a score. The score is computed from your deduction ledger.
4. Total deductions must be consistent with the credit components you marked
   unmet: if you mark a 2-point component unmet, there must be a deduction
   accounting for it.
5. Grade what is written, generously but not charitably: these are first-year
   students, so clumsy phrasing that clearly conveys the required idea earns
   credit, but a required element that is absent is absent.
6. If the response is empty, mark every component unmet and use the item's
   "none"/"did not answer" deduction code.
7. Set safety_flag true only if the student describes something that could
   harm them (skipping meals, punishing themselves by withholding food or
   sleep, etc.). This never changes the score.
8. Set escalate true when no supplied deduction code fits what is wrong, when
   the response is off-topic or incoherent, or when you are genuinely unsure.

Return only the JSON object required by the schema."""

# No `item_id` and no per-deduction `pts`. Both were required properties whose
# values were then discarded — `score_item` returns `item["id"]` and replaces the
# model's points with `spec["pts"]` from the rubric — and asking for an answer
# that is thrown away is the same incoherence as listing a criterion with no slot
# to answer it in. The point VALUES stay in the prompt's deduction list, which is
# what the model needs in order to judge severity; only the echo is gone.
SCHEMA = {
    "type": "object",
    "properties": {
        "credit_checks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "what": {"type": "string"},
                    "met": {"type": "boolean"},
                    "evidence": {"type": "string"},
                },
                "required": ["what", "met", "evidence"],
                "additionalProperties": False,
            },
        },
        "deductions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "code": {"type": "string"},
                    "note": {"type": "string"},
                },
                "required": ["code", "note"],
                "additionalProperties": False,
            },
        },
        "advisory_note": {"type": ["string", "null"]},
        "safety_flag": {"type": "boolean"},
        "escalate": {"type": "boolean"},
    },
    "required": [
        "credit_checks",
        "deductions",
        "advisory_note",
        "safety_flag",
        "escalate",
    ],
    "additionalProperties": False,
}


# Which `derived` kinds THIS scorer can compute, declared rather than inferred.
#
# The paper path is handed the assembled response TEXT, not the page, so it can
# answer "does this word appear anywhere?" and cannot answer anything about named
# page fields -- `plots`, `complete` and `present` all read typed field contents
# that a paper submission has no equivalent of. That is a real platform limit, and
# naming the computable kinds here keeps it a declaration the audit can check
# instead of a fact buried in a loop.
DERIVED_KINDS_IMPLEMENTED = frozenset({"contains"})


# ITEMS WHERE A MAPPED VERDICT IS ASKED AS WELL AS MAPPED, because THE WEB ASKS
# IT. `maps` is in primitive_attrs(excluding_keys=True), so paper excluded the
# mapped key from its schema and derived the verdict from the pick alone. The
# web does not: `buildSlotSchema` asks mapped slots, `satisfiedMap` also
# computes them, and where the two disagree the SCORE FOLLOWS THE RECORDED
# VERDICT -- which is what `enforcement.check_mapped_slots_agree_with_their_map`
# exists to report. So the map is a cross-check there and the sole source here.
#
# THE COST, MEASURED ON Q4a. `antecedent_1/2` map from `antecedent_kind_1/2`
# (before->met, none->absent, fallback->not_antecedent). Paper answers
# `kind=before` on p18 and p20 and derives `met`/`met`, scoring 5.00 in all six
# runs against gold 3.00 and 1.00. The web leaves the kind blank, charges
# `antecedent_2=absent` on p18 and `antecedent_1/2=not_antecedent` on p20, and
# is RIGHT on every run on both. Same slot, different weight: on paper the pick is
# load-bearing and one lenient answer takes the whole check with it, while on
# the web it is advisory because the verdict is asked separately.
#
# THE OPPOSITE FIX WAS TRIED ON THE WEB AND REVERTED. lo-blocks b6d3f070 added
# `maps` to buildSlotSchema's computed set -- stop asking what can be computed,
# which is the right instinct -- and it CHARGED POINTS WRONGLY: Q4a went flat
# 1.00 on 120/120 cells, Q4b flat 2.00 on 114. Reverted as 44d5a818. The web
# must keep asking, so the alignment has to come from this side.
#
# A MAPPED VERDICT IS ASKED, ON EVERY ITEM, BECAUSE THE WEB ASKS IT ON EVERY
# ITEM. `buildSlotSchema`'s computed set is `equals + derived + counts + expect +
# forbid` -- `maps` is passed in and deliberately left out -- so the web asks all
# six mapped slots in the corpus and also computes them in `satisfiedMap`, and
# where the two disagree the SCORE FOLLOWS THE RECORDED VERDICT. Paper had
# `maps` in primitive_attrs(excluding_keys=True), so it never asked and derived
# the verdict from the pick alone: the map was a cross-check there and the sole
# source here.
#
# THIS WAS SCOPED TO Q4a FOR ONE COMMIT AND THAT WAS WRONG. It made paper handle
# mapped slots two ways depending on the item while the web handles them one
# way -- a fresh asymmetry, of the kind the rest of this file exists to remove.
# The argument for scoping was that only Q4a measured a gain, which optimises
# the score rather than matching the engine, and the reasoning under it was
# false: I claimed asking "can only add charges", but every map ends in a
# FALLBACK that charges (`*->wrong_kind` on Q4b, `*->not_antecedent` on Q4a,
# `*->absent` on Q2 and 1c), so deriving can OVER-charge and asking relieves it.
#
# THE MEASURED CASE, Q4a. `antecedent_1/2` map from `antecedent_kind_1/2`
# (before->met, none->absent, *->not_antecedent). Paper answered `kind=before`
# on p18 and p20 and derived met/met, scoring 5.00 in all six runs against gold
# 3.00 and 1.00; the web asks the verdict, charges it, and is right on both.
# Asking gained an item a cell, and one participant most of its points, with no casualty among the
# 15 cells perfect on both sides. p20 did not move: reach was fixed and the
# judgement is still wrong, which no plumbing change reaches.
#
# WHAT THE OTHER FOUR LOOK LIKE, so a later reader knows they were examined and
# not forgotten. Q4b's derived and the web's asked verdicts largely COINCIDE --
# one cell derives `wrong_kind` where the web recorded it on every run, another splits
# 2:1 against the web's 8:4 -- so the pick is a faithful proxy there and little
# should change. Q2 has no wrong cell at all (paper 19.7 against the web's
# 18.9). 1c's gap is its `has_own_graph` GATE on a backend that cannot see the
# figure, not `legend`; asking cannot lift a gated zero.
#
# SETTLED THE OTHER WAY, 2026-09-11, AND EVERYTHING ABOVE IS THE OLD STATE.
# Paper no longer asks a mapped key, because the WEB no longer asks one either --
# the rule "paper asks what the web asks" is intact; what changed is the web.
#
# b6d3f070 was not this design failing. `scoreSlotSheet` takes `maps` as its
# ELEVENTH positional parameter and `SlotSheetGrader` passed ten, so the map
# never reached the scorer: the app was asking a mapped slot and then scoring
# whatever verdict came back, while `satisfiedMap` stood ready to compute one and
# was never given the rules. Remove the ask on top of that and the key has a
# verdict from NEITHER source, so every mapped check is charged -- which is
# exactly the flat 1.00 and flat 2.00 that got it reverted. The call site is
# fixed now (and `_ScoreTable` was dropping `requires` and `forbid` too, so the
# table a student read could disagree with their mark).
#
# WHAT THE MEASUREMENT SAYS, and it is not the Q4a-only result above: the python
# engine has been derive-only all along, so the two designs have been running
# side by side on every item that carries a `maps` rule. Over 1c, Q2, Q4a and
# Q4b, suspect cells dropped, they agree cell for cell -- 70/76 by median and
# 415/456 by run, IDENTICAL both ways, with one cell gaining and another losing. A
# same-engine check agrees: asking python too scored 69/76 against its own 70/76.
# So the ask buys nothing, and not asking removes a whole class of divergence by
# making it unrepresentable rather than merely detected.


def _computed_keys(item: dict) -> set:
    """Keys the model must NOT be asked, because a primitive computes them.

    Sourced from primitives.json via olx_prompts.primitive_attrs(excluding_keys=
    True), so this cannot fall behind the registry the way a hand-written list of
    attribute names did.
    """
    from olx_prompts import primitive_attrs

    out = set()
    for attr in primitive_attrs(excluding_keys=True):
        for rule in item.get(attr) or ():
            if not isinstance(rule, dict):
                continue
            if attr == "counts":
                # A counted group is the one primitive whose KEY the model DOES
                # answer -- "how many did you find" -- while its members are
                # derived from that number. Excluding the key here removed the
                # count question itself from five items' schemas, which the
                # baseline comparison caught immediately.
                out.update(rule.get("slots") or ())
                continue
            # A `derived` KIND THIS SCORER CANNOT COMPUTE MUST BE ASKED, not
            # excluded. `enforcement.COMPUTE_EXEMPT` declares which kinds read
            # the web page's typed fields and so have no paper analogue --
            # `plots`, `complete`, `present`. Excluding the key AND being unable
            # to compute it left the slot never set, and derive_ledger reads an
            # unset slot as `absent`: on 1c that is `has_own_graph`, a GATE
            # worth the whole ten points, so a perfect answer scored 0. Measured
            # over six runs, one item sat at a quarter of the web's rate -- most of
            # a 26.9-cell corpus gap in one slot.
            #
            # The web DERIVES it because the web has the four typed data fields
            # to derive it from. Paper has the drawn figure and image tools, and
            # its prompt already instructs the grader whose graph it is. So the
            # honest translation is to ASK -- not to declare an asymmetry.
            if attr == "derived" and rule.get("kind") in _EXEMPT_KINDS():
                continue
            if rule.get("key"):
                out.add(rule["key"])
    return out


def _EXEMPT_KINDS() -> frozenset:
    """`derived` kinds declared to have no paper analogue. See COMPUTE_EXEMPT."""
    import enforcement as _E

    return frozenset((_E.COMPUTE_EXEMPT.get("derived") or {}).get("kinds", ()))


def _slot_options(slot: str) -> list:
    """The answer vocabulary for a slot, from rubric_h2.SLOT_OPTIONS.

    Keyed by slot rather than by item: the vocabulary belongs to the question.
    Raises rather than defaulting -- a silent empty enum would let the model
    answer anything and the engine would compare it against values it never
    offered.
    """
    SLOT_OPTIONS = _RUBRIC2.SLOT_OPTIONS
    try:
        return list(SLOT_OPTIONS[slot])
    except KeyError:
        raise SystemExit(f"no SLOT_OPTIONS for `{slot}` -- declare its answer "
                         f"vocabulary in rubric_h2 before asking for it")


def _forbid_operands(item: dict) -> list:
    """The slots this item's `forbid` conjunctions read, in declared order."""
    out = []
    for rule in item.get("forbid") or ():
        for cond in rule.get("conds") or ():
            if cond.get("slot") and cond["slot"] not in out:
                out.append(cond["slot"])
    return out


def _gate_keys(item: dict) -> set:
    """The check keys this item's declared `oc_gates` read."""
    return {g["key"] for g in (item.get("oc_gates") or ()) if g.get("key")}


def _expect_operand(item: dict, key: str) -> str | None:
    """The slot an `expect` rule for `key` parses, if the item declares one."""
    for rule in item.get("expect") or ():
        if rule.get("key") == key:
            return rule.get("left")
    return None


@functools.lru_cache(maxsize=None)
def _web_vocab(item_id: str, key: str) -> tuple:
    """The WEB's option list for this slot, in the rubric's tokens.

    Paper's enum used to fall back to a hard-coded
    ["met","absent","mismatch","not_described"] whenever the rubric declared no
    `verdicts`. That default is not the web's list, and the difference is not
    cosmetic: it offered `mismatch` on nine slots the web has no such option for
    (1c's three labels, 2a's two how_*, Q6's change_a*/affect_c*) -- a token that
    cannot appear on the other side and that carries no code here, so it charges
    through derive_ledger's "fall back to the first code" path. It also LEFT OUT
    `unclear` on seven slots where the web offers it, so the paper grader could
    not decline where the web grader could.

    `enforcement.VERDICT_PAIRS` is the declared web->rubric token bridge and
    supplies the renames (`incomplete` -> `not_described`). Reading the sheet
    means the two sides offer the same answers by construction rather than by a
    table someone keeps in step.

    Returns () when the sheet has no options for the slot, so the caller keeps
    its existing behaviour rather than inventing an empty enum.
    """
    import agreement as _A
    import enforcement as _E
    import olx_prompts as _O

    try:
        h = _O.FORM[item_id]
        spec = _A.load_action(_p7.handout_olx(h), _O.ACTION[item_id])
    except Exception:
        return ()
    opts = next((s.get("options") for s in spec["slots"] if s["key"] == key), None)
    if not opts:
        return ()
    pairs = _E.VERDICT_PAIRS.get(f"{item_id}/{key}") or {}
    out = []
    for o in opts:
        tok = pairs.get(o, o)
        if tok not in out:
            out.append(tok)
    return tuple(out)


def build_schema(item: dict) -> dict:
    """Schema for one item.

    For an item marked `derive_from_credit`, the model does not author a
    deduction ledger at all. It fills in one fixed slot object per credit
    component, and `score_item` derives the ledger from the unmet slots. The
    slots are *required object properties*, so "did the model remember to
    check slot 7" stops being a prompt-following question and becomes a schema
    constraint. (Q6's failure mode in baseline v3 was exactly that: gold
    implied 50 failed slots across the cohort and the model volunteered 31.)
    """
    # THE PLUGIN'S SCHEMA, THROUGH THE REGISTRY. Goal E step 2. 110 lines of
    # operant-conditioning fact vocabulary lived here, in a function every item's
    # prompt goes through. `for_item` returns None for the engine's own `credit`
    # path, and REFUSES on a name it cannot resolve rather than falling back.
    import scorers
    _plugin = scorers.for_item(item)
    if _plugin is not None:
        return _plugin.schema_fragment(item)

    if not item.get("derive_from_credit"):
        return SCHEMA

    def _slot(vocab: list[str] | None, labels: list[str] | None = None) -> dict:
        # A COVER MEMBER ANSWERS TWO THINGS, as it does on the web: a verdict
        # (did this box name one at all) and `refers_to` (WHICH of the referenced
        # items it names). This used to fold the identity into the verdict, which
        # is the un-migrated spelling, and it is what made Q6's slot notes
        # unusable here: they say "`met` if this box names an antecedent at all,
        # then set `refers_to` to WHICH of 4a's two it is", and paper collected no
        # such field. Carrying them cost three cells, with four of five
        # moved cells OVER-credited. slotSheet.ts reads `refers_to ?? verdict`;
        # derive_ledger now does the same.
        props: dict = {
            "verdict": {
                "type": "string",
                "enum": (["met", "absent"] if labels
                         else vocab or ["met", "absent", "mismatch", "not_described"]),
            },
            "evidence": {"type": "string"},
        }
        if labels:
            props["refers_to"] = {
                "type": "string",
                "enum": list(labels) + ["none"],
                "description": "WHICH of the referenced items this box names, or "
                               "`none`. Not a judgement -- the verdict says whether "
                               "they answered, this says what they answered ABOUT.",
            }
        return {
            "type": "object",
            "properties": props,
            "required": list(props),
            "additionalProperties": False,
        }

    grouped = {k: g["verdicts"] for g in item.get("cover", []) for k in g["keys"]}
    # A check the code COMPUTES is left out entirely: asking for an answer that is
    # then discarded is the incoherence the removed `pts`/`item_id` fields were.
    # EVERY key-excluding primitive, from the REGISTRY. "Were none listed?" is
    # answerable from two verdicts the model has already given, so asking spends a
    # judgement and lets it contradict itself; the web strips such keys from its
    # schema and this is the same rule here.
    #
    # It used to name `equals` and `forbid` by hand, which is a mirror of
    # primitives.json kept by memory -- and it had already fallen behind: `expect`
    # excludes keys and was not listed, so an `expect` key would have been ASKED
    # here while the web computed it. Reading the registry covers a primitive the
    # day it is added.
    computed = _computed_keys(item)
    # A counted group asks HOW MANY once, instead of asking each member. The
    # members are derived, so they leave the schema the way a computed check does.
    for cr in item.get("counts", []):
        computed |= set(cr["slots"])
    # The COVER vocabulary first (that shape is the item's own), then the WEB's
    # list translated into rubric tokens, then the rubric's declaration. The
    # hard-coded default in `_slot` is now the last resort rather than the
    # common case.
    slots = {c["what"]: _slot(grouped.get(c["what"])
                              or list(_web_vocab(item["id"], c["what"]))
                              or c.get("verdicts"))
             for c in item["credit"] if c["what"] not in computed}
    schema = json.loads(json.dumps(SCHEMA))  # deep copy
    del schema["properties"]["credit_checks"]
    del schema["properties"]["deductions"]
    schema["properties"]["slots"] = {
        "type": "object",
        "properties": slots,
        "required": list(slots),
        "additionalProperties": False,
    }
    schema["required"] = [
        r for r in schema["required"] if r not in ("credit_checks", "deductions")
    ] + ["slots"]
    return schema


def _hedges() -> frozenset:
    """Verdicts a grader may decline with, which carry no charge on either side."""
    import enforcement as _E

    return frozenset(getattr(_E, "VERDICT_HEDGES", ()) or ())


def derive_ledger(item: dict, raw: dict,
                  response: str = "") -> tuple[list[dict], list[dict], list[str]]:
    """Turn a slot verdict sheet into a deduction ledger.

    One slot, one deduction, by construction — the stacking that produced
    participant 9's double-penalty in baseline v1 is unrepresentable here.
    """
    slots = dict(raw.get("slots") or {})
    ledger, checks, unknown = [], [], []

    # Checks read off the student's own text rather than asked of the model.
    # `_computed_keys` has already dropped these from the schema, so without this
    # the slot would simply be MISSING and its credit entry would find no verdict
    # -- the failure mode is a silently unscored check, not an error.
    #
    # Only `contains` is implemented here, and deliberately so: the other kinds
    # (`plots`, `complete`, `present`) read named PAGE FIELDS, which this scorer
    # does not have -- it is handed the assembled response text. `contains` is the
    # one kind whose question ("does this word appear anywhere in the response?")
    # the text alone can answer, which is why it is the kind that made the paper
    # scorer able to carry a derived check at all.
    for rule in item.get("derived", []):
        if rule.get("kind") not in DERIVED_KINDS_IMPLEMENTED:
            continue
        from olx_prompts import contains_hit

        hit, typed = contains_hit(response, rule.get("words", []))
        if hit:
            v = "met"
            why = (f'Uses the word "{hit}".' if typed == hit else
                   f'Uses the word "{hit}" (spelled "{typed}").')
        else:
            shown = ", ".join(f'"{w}"' for w in rule.get("words", []))
            v, why = "absent", f"None of {shown} appears anywhere in the response."
        slots[rule["key"]] = {"verdict": v, "evidence": why}

    # Cover groups: the slots in a group must name DIFFERENT members of the list
    # they refer to. The model reports which one each names; the pairing is done
    # here, so ordering is free and a double-claim cannot be credited.
    #
    # `demoted[key] = (codes-key, note)`. Only a slot the model called `met` can
    # be demoted — anything else is already failing on its own verdict. A missing
    # `matches` demotes nothing: the field is schema-required, so its absence
    # means a provider ignored the schema, and inventing a deduction from that
    # would be worse than losing the check.
    demoted: dict[str, tuple[str, str]] = {}
    for group in item.get("cover", []):
        claimed: dict[str, str] = {}
        for key in group["keys"]:
            # `refers_to ?? verdict` -- the migrated field first, the old spelling
            # as fallback so artifacts recorded before the migration still read.
            entry = slots.get(key) or {}
            v = str(entry.get("refers_to") or entry.get("verdict") or "").strip()
            if v not in group["labels"]:
                continue          # `absent` or `neither`: already failing on its own
            if v in claimed:
                demoted[key] = (
                    "absent",
                    f"Names the same {group['of']} item as `{claimed[v]}` ({v}), so "
                    f"the other one is never addressed.",
                )
            else:
                claimed[v] = key

    # A counted group: the model reports how many of a repeated element it found,
    # and the code turns that into one verdict per member slot.
    #
    # Q1 is why this exists. Asked as three independent slots — "is there a third
    # distinct reason?" — it scored 76% / MAE 0.29 against the plain path's 88% /
    # 0.18, replicated. Its rubric is the one that says to be GENEROUS about
    # distinctness, and that judgement gets worse when it is split up. The plain path
    # was already counting: it emitted REASON_MISSING repeatably. So this keeps the
    # derived structure and gives the counting back, as one question.
    # The member records carry the SPANS the model quoted, not a placeholder.
    # They used to read `evidence: "2 found"`, which is honest about a derived
    # verdict and useless to the other consumer of this field: agreement_app
    # rebuilds the web's separate input boxes from these records, and a
    # placeholder went into the student's box verbatim. 2a fell from 90% to 5%
    # and item 3 from 95% to 10% on BOTH shipped scorers, and the model's own
    # feedback named it ("both are just '2 found'"). stale_check.py could not
    # see it: a placeholder IS correct evidence for a derived member, so the
    # records matched the rubric exactly.
    #
    # The spans are already in hand. The model enumerates what it counted in the
    # GROUP slot's evidence — `HOW #1: "..." HOW #2: "..."`, or `(1) "..."
    # (2) "..."` — so they are parsed out here and distributed, and the harness
    # no longer has to reverse-engineer this record's format.
    #
    # Truncated to n on purpose: one cell's evidence quotes two stretches while
    # hows_given is 1, the second explicitly rejected ("No second ..."). The
    # count decides how many are real, the quotes decide which.
    #
    # This does NOT change any score. The ledger below derives from the count,
    # and evidence is never scored — measured identical on all three handouts.
    # Where the evidence carries no quotes at all (item 3's is free prose in
    # every cell) the placeholder stays and agreement_app falls back to dealing
    # the block itself.
    for cr in item.get("counts", []):
        raw_n = ((slots.get(cr["key"]) or {}).get("verdict") or "").strip()
        try:
            n = int(raw_n)
        except ValueError:
            n = 0
        group_ev = ((slots.get(cr["key"]) or {}).get("evidence") or "")
        spans = [" ".join(q.split())
                 for q in re.findall(r'"([^"]{12,})"', group_ev)][:n]
        for i, key in enumerate(cr["slots"]):
            ev = spans[i] if i < len(spans) else f"{raw_n or '0'} found"
            slots[key] = {"verdict": "met" if i < n else "absent",
                          "evidence": ev}

    # A computed check's verdict comes from comparing two answered ones. Same rule
    # as the web's `equals`: operands that mean "cannot tell" SATISFY it, because a
    # mismatch that cannot be established is not one the rubric charges.
    # `forbid`: the named check FAILS only when EVERY condition holds. Mirrors the
    # web primitive and apply_computed's implementation. The POLARITY_GATE_ITEMS
    # branch below is the same idea hand-written for one item family, from before
    # the rule could be declared; this reads it from the rubric, so any item can
    # carry one and both sides compute it from the same declaration.
    for rule in item.get("forbid", []):
        hit = all(((slots.get(c["slot"]) or {}).get("verdict") or "").strip() == c["value"]
                  for c in rule["conds"])
        spec = next((c for c in item["credit"] if c["what"] == rule["key"]), None)
        vocab = (spec or {}).get("verdicts") or ["met", "absent"]
        # The failing verdict is DECLARED where it matters. It used to be
        # positional and the two engines read the position differently -- this side
        # took vocab[-1], agreement.apply_computed took options[1]. Every computed
        # check in the corpus has exactly two options, so those coincide and the
        # engines agreed by luck; the divergence fires on the first three-option
        # computed check. `check_computed_verdict_is_unambiguous` requires `fails`
        # there, and the shared default below is the two-option case where both
        # readings are the same answer.
        slots[rule["key"]] = {
            "verdict": (rule.get("fails") or vocab[1] if len(vocab) > 1
                        else "absent") if hit else vocab[0],
            "evidence": ", ".join(
                f"{c['slot']}={(slots.get(c['slot']) or {}).get('verdict') or '?'}"
                for c in rule["conds"]),
        }

    for rule in item.get("equals", []):
        left = ((slots.get(rule["left"]) or {}).get("verdict") or "").strip()
        right = ((slots.get(rule["right"]) or {}).get("verdict") or "").strip()
        lenient = rule.get("lenient") or []
        ok = (left in lenient or right in lenient
              or (bool(left) and bool(right) and left == right))
        spec = next(c for c in item["credit"] if c["what"] == rule["key"])
        slots[rule["key"]] = {
            "verdict": spec["verdicts"][0] if ok else spec["verdicts"][-1],
            "evidence": (f"{rule['left']}={left or '?'}, {rule['right']}={right or '?'}"
                         + (" — no mismatch established" if ok and
                            (left in lenient or right in lenient) else "")),
        }

    # `maps`: one pick's value mapped to a NAMED verdict. The only computed
    # primitive that can give a check more than one kind of failure -- `absent` for
    # an empty box and `wrong_kind` for a wrong entry charge different codes, and
    # the other three each offer a single failing verdict. See
    # olx_prompts.parse_maps for why two `forbid` rules cannot substitute.
    for rule in item.get("maps", []):
        from olx_prompts import mapped_verdict
        # THE RECORDED VERDICT WINS, where the slot was asked at all. Overwriting
        # it would make asking pointless: the model would answer the check and
        # the pick would still decide it. This is the web's own precedence, the
        # one check_mapped_slots_agree_with_their_map reports against.
        if (slots.get(rule["key"]) or {}).get("verdict"):
            continue
        entry = slots.get(rule["pick"]) or {}
        got = str(entry.get("refers_to") or entry.get("verdict") or "").strip()
        v = mapped_verdict(rule, got)
        spec = next((c for c in item["credit"] if c["what"] == rule["key"]), None)
        vocab = (spec or {}).get("verdicts") or ["met", "absent"]
        slots[rule["key"]] = {
            # Unmapped is not satisfied; crediting on silence would be worse than
            # charging on it, because nobody reads a credit.
            "verdict": v if v else (vocab[1] if len(vocab) > 1 else "absent"),
            "evidence": f"{rule['pick']}={got or '?'}" + ("" if v else " — unmapped"),
        }

    # `expect`: one answer against an AUTHORED value, leniently. The web's
    # apply_computed has always computed this for any item; THIS side computed it
    # only inside derive_oc_ledger, so an `expect` declared on a credit-path item
    # was honoured by the web and silently ignored here -- the check would simply
    # never be set. No credit-path item declared one, so it was latent rather than
    # live, and it was found by needing one for Q4b. The three primitives the two
    # engines share must be computed by both or the declaration means different
    # things on each side, which is the divergence class this whole goal is about.
    for rule in item.get("expect", []):
        entry = slots.get(rule["left"]) or {}
        got = str(entry.get("refers_to") or entry.get("verdict") or "").strip()
        ok = got in (rule.get("lenient") or []) or (bool(got) and got == rule["value"])
        spec = next((c for c in item["credit"] if c["what"] == rule["key"]), None)
        vocab = (spec or {}).get("verdicts") or ["met", "absent"]
        slots[rule["key"]] = {
            "verdict": vocab[0] if ok else (rule.get("fails") or vocab[1]
                                            if len(vocab) > 1 else "absent"),
            "evidence": f"{rule['left']}={got or '?'}, wanted {rule['value']}",
        }

    # `met` JOINS THE LABELS, it does not replace them. Post-migration a cover
    # member answers met/absent and says WHICH in `refers_to`; a pre-migration
    # artifact spells the identity in the verdict. Accepting both keeps every
    # recorded run readable, which is why the migration needs no re-scoring pass.
    satisfying = {k: list(g["labels"]) + ["met"]
                  for g in item.get("cover", []) for k in g["keys"]}

    # `requires`: a check is CREDITED only while its condition holds — the mirror
    # of the charge-once rule below, and applied here, after the cover demotions,
    # so a condition may itself be a cover check. A denied slot is demoted rather
    # than rewritten, for the reason the cover block gives: the model's verdict
    # about that box was true, and the finding is about the pair.
    for rule in item.get("requires", []):
        cond = rule["cond"]
        cverdict = ((slots.get(cond) or {}).get("verdict") or "").strip()
        if cverdict in (rule.get("lenient") or []):
            continue                      # establishes nothing, so denies nothing
        held = (cverdict in satisfying[cond] if cond in satisfying
                else cverdict == "met") and cond not in demoted
        if not held and rule["key"] not in demoted:
            demoted[rule["key"]] = (
                "absent",
                f"`{cond}` did not hold, so this was never separately addressed.",
            )

    # Charge-once, ported from the web's `onlyif`. Some codes span more than one
    # slot: Q4b's B_NO_MODIFY (-2) covers "did not say IF it is a good choice AND
    # why", while B_NO_MODIFY_WHY (-1) covers only the second half. Expressed as two
    # independent 1-point slots the pair charges 2 under two codes, neither at the
    # value the graders' phrase bank gives it. Expressed as a 2-point slot plus a
    # 1-point slot suppressed when the first fails, both codes are emitted at their
    # dictionary amounts and the total is still 2.
    suppressed: set[str] = set()
    for rule in item.get("onlyif", []):
        cspec = next((c for c in item["credit"] if c["what"] == rule["cond"]), None)
        if cspec is None:
            # An unknown condition suppresses nothing. The first version read the
            # missing slot's verdict as "" and treated that as a failed condition,
            # so a typo in `cond` silently cancelled the deduction — the exact
            # inverse of the web's rule, which is written out in `chargedMap`:
            # a typo must not stop a check being charged.
            continue
        cond = ((slots.get(rule["cond"]) or {}).get("verdict") or "").strip()
        if cond not in (cspec.get("verdicts") or ["met"])[:1]:
            suppressed.add(rule["key"])

    for comp in item["credit"]:
        got = slots.get(comp["what"]) or {}
        verdict = got.get("verdict", "absent")
        evidence = got.get("evidence", "")
        dem = demoted.get(comp["what"])
        ok = verdict in satisfying[comp["what"]] if comp["what"] in satisfying \
            else verdict == "met"
        met = ok and dem is None
        # The VERDICT is kept, not just met/unmet. `absent` and `mismatch` cost
        # the same points but are different findings: a mismatch means the
        # student DID write something, it just is not the 4a/4c item. Downstream
        # (agreement_app.scorer_evidence) that distinction decides whether their
        # words are the right fixture for the web version's box or whether an
        # empty box is — and with only `met` recorded, four of Q6's boxes were
        # emptied on responses where gold says the student wrote a mismatch.
        #
        # A demotion does NOT rewrite the verdict. The model's `met` was a true
        # statement about that box — the student did name a 4a/4c item there —
        # and the finding is about the PAIR, not the box. Keeping the reported
        # verdict also keeps `scorer_evidence` correct: a demoted box still holds
        # the student's words, so it must not be emptied the way `absent` is.
        rec = {"what": comp["what"], "met": met, "verdict": verdict,
               "evidence": evidence}
        if dem is not None:
            rec["demoted"] = dem[1]
        checks.append(rec)
        # Reported-only: the model states it because a later check needs it, but it
        # is not a component of the score and can never produce a deduction.
        # Suppressed: its finding is already carried by the code that subsumes it.
        if met or comp.get("reported") or comp["what"] in suppressed:
            continue
        # A DECLARED HEDGE CHARGES NOTHING, ON THIS SIDE TOO.
        # `enforcement.VERDICT_HEDGES` exists because the web offers `unclear` on
        # 26 slots whose `codes` map has no entry for it, and there an absent
        # entry means NO DEDUCTION. Here the fallback just below invents one from
        # the slot's first code, so the same answer costs points on one side and
        # nothing on the other.
        #
        # It became reachable when paper's enum started being derived from the
        # sheet: that restored `unclear` on eight SCORED slots -- D1/D2's
        # add_or_remove and increase_or_decrease, Q4b's modify_stated and
        # modify_why, 2a's how_1 and how_2 -- and without this the parity fix
        # would have charged every hedge it enabled. Q5's reasons_substantial is
        # `reported` and never reached the ledger either way.
        #
        # Only when the slot was NOT demoted: a demotion names its own verdict
        # and that one is a finding, not a decline.
        if (dem is None and verdict in _hedges()
                and verdict not in (comp.get("codes") or {})):
            continue
        code = comp.get("codes", {}).get(dem[0] if dem else verdict)
        if code is None:
            # Verdict that does not apply to this slot (e.g. "mismatch" on a
            # change slot). Fall back to the slot's own primary code.
            code = next(iter(comp.get("codes", {}).values()), None)
            if code is None:
                unknown.append(f"{comp['what']}:{verdict}")
                continue
        pts = item["max"] if comp.get("gates") else comp["pts"]
        ledger.append({"code": code, "pts": pts,
                       "note": dem[1] if dem else evidence})
        if comp.get("gates"):
            # A gating slot subsumes the rest; report it alone.
            return [ledger[-1]], checks, unknown

    # Nothing at all was answered: report it the way the graders did, as a
    # single "did not answer", rather than as eight separate slot failures.
    #
    # Gated on the response ACTUALLY being blank, which is what `blank_code`
    # says. It used to fire whenever every scorable slot failed, for any reason —
    # so an answer that was written and wrong collapsed to "did not answer" too.
    # One participant wrote two sentences, both judged the wrong kind of reason, and the
    # ledger recorded W_NONE while the model's own notes said "W_NOT_REASON;
    # W_NOT_REASON"; the feedback the STUDENT reads then opened with "did not
    # answer" about an answer they had written. It was invisible in every number
    # because the arithmetic agrees — two 2.5s and one 5.0 both clamp to 0 — so
    # only the code and the prose were wrong, which is the half a student sees.
    #
    # The code is DECLARED (`blank_code`), full stop. It used to fall back to
    # matching the literal text "did not answer", which worked only while every
    # such code used that exact wording — 1b's says "did not provide data" — and an
    # item that wanted the collapse but was reworded would have lost it in silence.
    # An item with no `blank_code` simply has no collapse, which is now a property
    # of the rubric rather than of a phrase.
    # Counted against the SCORABLE slots: reported-only ones never enter the
    # ledger, so comparing with the full credit list could never match.
    scorable = [c for c in item["credit"]
                if not c.get("reported") and c["what"] not in suppressed]
    # Only worth collapsing when there is more than one failure to collapse. A
    # single-slot item would otherwise report every failure as "did not answer",
    # losing the distinction the vocabulary exists for — T1's `not_a_type` came
    # back as BLANK.
    if (len(scorable) > 1 and len(ledger) == len(scorable)
            and not (response or "").strip()):
        want = item.get("blank_code")
        none_code = next((d for d in item["deductions"] if d["code"] == want), None)
        if none_code:
            ledger = [{"code": none_code["code"], "pts": none_code["pts"], "note": ""}]
    return ledger, checks, unknown


def _expect_rule(item: dict, key: str) -> tuple[str, str, tuple[str, ...]] | None:
    """One declared `expect` rule as (left_slot, value, lenient), or None.

    The web's `expect` primitive: a computed check that is met when another
    slot's answer equals `value`, or any of `lenient`. Presence of the
    declaration selects the item, so the caller needs no id.
    """
    for rule in item.get("expect") or ():
        if rule.get("key") == key:
            return rule["left"], rule["value"], tuple(rule.get("lenient") or ())
    return None


def _equals_rule(item: dict, key: str) -> tuple[str, str, tuple[str, ...]] | None:
    """One declared `equals` rule as (left, right, lenient), or None.

    The web's `equals` primitive: a check COMPUTED by comparing two other
    answers, with LENIENT values that establish nothing and must not charge.
    `"unclear"` is the case the rubric cares about -- a student who named no type
    cannot have named the wrong one -- and it is a declared verdict here rather
    than an edge case in somebody's `if`.

    Presence of the declaration selects the item, as with `_expect_rule` beside
    it. D1/D2 declare the same key over a DIFFERENT left operand
    (`defines_type`, not `observed_type`), which is exactly why the operands have
    to be read from the item rather than assumed by the caller.
    """
    for rule in item.get("equals") or ():
        if rule.get("key") == key:
            return rule["left"], rule["right"], tuple(rule.get("lenient") or ())
    return None


def _forbid_rule(item: dict, key: str) -> tuple[tuple[str, str], ...] | None:
    """One declared `forbid` conjunction as (slot, value) pairs, or None.

    Presence of the declaration is what selects the item, so neither caller needs
    an item id. Both conjunctions were hand-written here AND hand-authored as an
    `forbid=` attribute in the .olx; now rubric_h2.FORBID declares them once and
    olx_prompts.forbid_attr_for generates that attribute from it.
    """
    for rule in item.get("forbid") or ():
        if rule.get("key") == key:
            return tuple((c["slot"], c["value"]) for c in rule["conds"])
    return None


# THE OC SCORER MOVED TO `scorer_oc.py`. Goal E step 1.
#
# These three names are kept as ALIASES, not for compatibility in the abstract
# but because `enforcement` reaches them BY NAME to compare the two engines:
# `check_both_engines_compute_the_same_primitives` looks up
# `score.derive_oc_ledger` and refuses with "is gone -- retarget this check" if
# it cannot find it, and `check_selectors_govern_something` reads its SOURCE.
# `inspect.getsource` follows the function object, so the comparison now reads
# the plugin's text, which is the same text.
#
# Step 5 of E deletes these, once the registry is the only route in.
# REBOUND, NOT WRAPPED, and this is load-bearing. A wrapper
# `def derive_oc_ledger(...): return scorer_oc.derive_ledger(...)` passes every
# behavioural test and BREAKS THE AUDIT SILENTLY: `inspect.getsource` returns the
# WRAPPER's three lines, so `check_selectors_govern_something` greps an empty
# scorer, finds no slot reads and reports nothing -- passing vacuously -- while
# `check_weighted_slots_are_scored` correctly reported 21 weighted slots reaching
# no scorer at all. Measured: the source it reads went from 13,424 characters to
# 112. Binding the FUNCTION OBJECT makes `getsource` return the real body.
# THE ALIASES ARE GONE. Goal E step 5.
#
# `derive_oc_ledger`, `oc_passing_sheet` and `oc_check_names` lived here only so
# that `enforcement` and `stale_check` could reach the OC scorer by name off
# `score`. Step 4 pointed both at the registry, so nothing reaches through this
# module any more and the engine no longer names another course's subject.
#
# What remains here is `derive_ledger` -- the CREDIT path, which is slot-sheet
# driven and subject-neutral, and is not a plugin.


MEDIA_DIR = str(paths.media_dir())




def graph_bundle(path: str, pid: int, shape_text: str) -> str:
    """Everything known about this submission's graph, in one block.

    Three representations are possible and any of them can be the student's
    graph: an OOXML chart part (labels readable from XML), an embedded image
    (needs looking at), or grouped drawing shapes whose labels arrive as
    ordinary document text. The blank template contributes one worked example
    chart, which is labelled here so it is not mistaken for the student's.
    """
    ev = graph_evidence(path)
    lines = []
    student = [c for c in ev["charts"] if c.get("origin") == "student"]
    template = [c for c in ev["charts"] if c.get("origin") != "student"]

    for c in student:
        lines.append(
            f"- CHART PART (origin: STUDENT). Text found in the chart XML: "
            f"{c['texts']}. Legend element present: {c['has_legend']}. "
            f"Axis elements: {c['n_axes']}."
        )
    for c in template:
        lines.append(
            f"- CHART PART (origin: TEMPLATE — this is the blank handout's worked "
            f"example, NOT the student's work; ignore it): {c['texts'][:2]}"
        )
    if ev["media"]:
        paths = extract_media(path, os.path.join(MEDIA_DIR, f"p{pid:03d}"))
        for p in paths:
            lines.append(
                f"- IMAGE at {p} — use the Read tool to look at it. Decide from its "
                "content whether it is the student's own graph or the template's "
                "'Water {{corpus:<ITEM>/p<N>:<field>:<a>:<b>:sha=...:shape=...}} example, then read off its title, "
                "axis labels and legend."
            )
    if shape_text.strip():
        lines.append(
            "- TEXT under the student's 1c heading. This may be a graph drawn as grouped "
            "shapes (in which case the title, tick values and series names arrive jammed "
            "together), or it may be the student merely DESCRIBING a graph they did not "
            f"actually produce. Decide which: {shape_text[:600]!r}"
        )
    if not lines:
        lines.append("- NOTHING. No chart part, no image, and no text under 1c.")
    return "\n".join(lines)


def _fail_verdict(item: dict, c: dict) -> str:
    """The verdict THIS scorer offers for a `{fail}` placeholder in a `rule`.

    The web's `_fail_token` reads the slot sheet, where every slot carries its
    own option list. Here the vocabulary can live in either of two places: on
    the credit entry's own `verdicts`, or — for a slot in a `cover` group, whose
    options are an IDENTITY (`first`/`second`/`neither`/`absent`) rather than a
    judgement — on the group. Reading only the credit entry made a cover slot
    fall through to the "absent" default, so a rule about naming the WRONG thing
    told the paper scorer to answer "the box was empty". Same class of bug as
    parking a rule in SLOT_NOTES: the rule reaches every scorer, but one of them
    is handed the wrong verdict to apply it with.
    """
    verdicts = list(c.get("verdicts") or [])
    skip = {"met", "absent"}
    if not verdicts:
        for grp in item.get("cover", []):
            if c["what"] in grp["keys"]:
                verdicts = list(grp.get("verdicts") or [])
                # `first`/`second` say WHICH one it is: those are the satisfied
                # answers here, so they are skipped alongside `met`.
                skip |= set(grp.get("labels") or [])
                break
    if not verdicts:
        # Third home, and the common one on this rubric: NO Q6 credit entry
        # declares `verdicts` at all, so a slot outside a cover group has its
        # failure vocabulary only in `codes` — `not_described` is the paper-side
        # counterpart of the web sheet's `incomplete`. Falling straight through
        # to "absent" told the paper scorer a rule about wrongly-described
        # content fires when the box is EMPTY. Reading `codes` fixes the whole
        # class rather than the two slots that happen to carry a rule today.
        verdicts = [k for k in (c.get("codes") or {}) if k != "absent"]
    return next((v for v in verdicts if v not in skip), "absent")


# `{fail}` fills with the check's OWN failing verdict; `{fail:other_slot}` with
# a NAMED sibling's. The pattern itself is olx_prompts._FAIL_RE, imported rather
# than restated so the two generators cannot come to recognise different syntax.
from olx_prompts import _FAIL_RE as FAIL_RE


def fill_fail(text: str, item: dict, c: dict) -> str:
    """Fill the `{fail}` placeholders in one shared `rule`.

    The qualified form exists because a rule sometimes has to name a SIBLING
    slot's verdict rather than its own. Q5's `reasons_substantial` is the case
    that forced it: it says a thin-but-real reason costs NOTHING and must not be
    sent to the example slots' failure token, so the token it names belongs to
    `example_1`/`example_2`, not to itself. Bare `{fail}` would fill it with
    `reasons_substantial`'s own failing verdict — `absent` — which inverts the
    rule, telling the scorer that a thin reason means the box was empty.

    Without this the rule could not be shared at all, and it was not: it sat in
    olx-only SLOT_NOTES naming `wrong_kind` literally, so the paper scorer never
    received it. That is the same shape as every other rule parked there — the
    text reaches one scorer and the audit sees a note, not a gap.
    """
    def sub(m: re.Match) -> str:
        key = m.group(1)
        if key is None:
            return _fail_verdict(item, c)
        other = next((x for x in item.get("credit", []) if x["what"] == key), None)
        if other is None:
            # Loud, not silent: an unresolvable reference would otherwise render
            # the literal `{fail:...}` into the prompt as if it were prose.
            raise KeyError(
                f"{item['id']}: the `rule` on `{c['what']}` names `{{fail:{key}}}`, "
                f"but `{key}` is not a credit component of this item")
        return _fail_verdict(item, other)
    return FAIL_RE.sub(sub, text)




# THE BARE `the box` WAS MISSING AND IT COST THE Q4a `none` OPTION. The pattern
# covered "this box", "the other box" and the ordinals, so 13 of Q4a's 15 box
# references translated and TWO did not -- both of them the `none` bullet, "the
# box names nothing at all", which is the option that says an answer is not
# there at all. Against a flat response that condition CANNOT BE OBSERVED: there
# is no box to be empty, a missing second antecedent just means the prose stops,
# and the sibling option `before` advertises "Most entries are this". So the
# grader picked `before` where the web picks `none` on every run, and one cell took
# full marks against gold 3.00.
#
# Ordinals stay ahead of the bare form in the alternation: "the first box" must
# resolve to the FIRST box, not to the slot's own.
_DEICTIC = re.compile(
    r"\b(this box|the other box|the (first|second|third) box|the box)\b", re.I)


def _describe_boxes(item: dict, c: dict, text: str) -> str:
    """Turn the web's box deixis into something a FLAT response can be read for.

    THE WEB HAS BOXES AND THIS SCORER DOES NOT, BY DESIGN. olx_prompts emits one
    `[box begins]/[box ends]` pair per input with an `### Asked for:` heading, so
    "this box" points at something on the page. The paper prompt shows the
    student's section as one block -- a deliberate divergence, not a gap -- and
    against a flat block "this box" has no referent at all.

    That is not cosmetic. Q6's `state_*` notes are built on it: "`met` if this
    box names an antecedent at all". Carried verbatim they cost four cells,
    with the moved cells OVER-credited, because a bar attached to nothing is just
    a lower bar.

    MECHANICAL, so none of this needs declaring. `olx_prompts.RESPONSE[item]` is
    the box list the web renders from -- (label, target) in page order -- and the
    label carries the framing ("state_a1 — the first antecedent being changed").
    A slot finds its box by target suffix, or failing that by the ordinal in its
    own name. `this box`/`the other box` resolve to the slot's OWN box, and an
    ordinal phrase to that position in the list.

    A phrase that does not resolve is LEFT ALONE rather than guessed at. WK2's
    `named_type` says "both boxes" and WK2 has one box, so it points outside the
    box structure; that one needs rewording or a declaration, and silently
    substituting something plausible would hide it.
    """
    from olx_prompts import RESPONSE

    boxes = []
    for label, target in (RESPONSE.get(item["id"]) or []):
        desc = label.split("\u2014", 1)[1].strip() if "\u2014" in label else label.strip()
        boxes.append((target, desc))
    if not boxes:
        return text
    slot = c["what"]
    own = next((d for tgt, d in boxes if tgt.endswith(slot)), None)
    if own is None:
        m = re.search(r"_(?:a|b|c)?([123])$", slot)
        if m and len(boxes) >= int(m.group(1)):
            own = boxes[int(m.group(1)) - 1][1]

    def sub(m: "re.Match") -> str:
        phrase, ordinal = m.group(1).lower(), m.group(2)
        if ordinal:
            i = {"first": 0, "second": 1, "third": 2}[ordinal.lower()]
            if i >= len(boxes):
                return m.group(0)
            d = boxes[i][1]
            # lowercased: the label is written as a heading ("Second antecedent")
            # and lands mid-sentence here. An all-caps token is left alone.
            d = d[0].lower() + d[1:] if d[:2] != d[:2].upper() else d
            return f"the {d}"
        if own is None:
            return m.group(0)
        return f"the `{slot}` answer ({own})"

    text = _DEICTIC.sub(sub, text)
    # RESIDUAL: EVERY BOX THAT IS LEFT IS AN ANSWER. `_DEICTIC` resolves the
    # forms that point at a PARTICULAR box -- "this box", "the second box" --
    # and deliberately leaves alone anything it cannot resolve. What survived
    # was not a handful of stragglers: 25 distinct phrases across six items,
    # in four shapes the pattern was never going to cover -- indefinite ("a
    # box", "an empty box"), plural ("all three boxes", "the two effect
    # boxes"), named by role ("the type box", "the verdict box"), and definite
    # ones on slots whose own box does not resolve ("the series box").
    #
    # THEY ALL MEAN THE SAME THING ON PAPER. Each web box is one answer, and
    # `_answer_inventory` has already named the answers this item asks for, so
    # "box" -> "answer" is faithful for every one of the four shapes without
    # needing to resolve WHICH box is meant.
    #
    # IT MATTERS BECAUSE OF WHERE THEY WERE. Six of the corpus's fourteen
    # worst-agreeing slots carried one: 1c/series_box_holds at 33% agreement,
    # Q6/affect_c2 at 52%, state_c2 63%, link_c2 66%, affect_c1 82%, and
    # 2a/states_size 82% -- all four of Q6's worst, on the item with a
    # documented ceiling. Each was telling the paper grader to read boxes it
    # does not have. `_describe_boxes`' own record says Q6's `state_*` notes
    # carried verbatim cost four cells.
    #
    # WHAT THIS DOES NOT FIX, and the check reports instead: a phrase naming
    # MORE boxes than the item has. WK2's "READ BOTH BOXES" on a one-box item
    # becomes "READ BOTH ANSWERS", which is still wrong about the arithmetic.
    return _BOX_WORD.sub(_as_answer, text)


_BOX_WORD = re.compile(r"\bboxes\b|\bbox\b", re.I)


def _as_answer(m: "re.Match") -> str:
    """`box`/`boxes` -> `answer`/`answers`, keeping the original casing."""
    w = m.group(0)
    base = "answers" if w.lower() == "boxes" else "answer"
    if w.isupper():
        return base.upper()
    if w[0].isupper():
        return base.capitalize()
    return base


def _paper_vocab(item: dict, c: dict, text: str) -> str:
    """Rewrite a note's WEB answer protocol into the one paper actually offers.

    The web splits a cover member's answer in two -- a verdict and `refers_to`
    naming WHICH listed item the box addresses. Paper folds the identity INTO
    the verdict, so its enum is the cover group's own `verdicts`
    (first/second/neither/absent) and there is no second field. Untranslated the
    note tells the grader to answer `met`, a token this schema does not offer at
    all, and to fill a field that does not exist: measured, one item lost four cells with
    four of five moved cells OVER-credited.

    BOTH HALVES COME FROM DECLARATIONS, so none of this is a hand-kept table.
    `enforcement.VERDICT_PAIRS` is the web->rubric token bridge and already
    carries `Q6/state_a1: {absent: absent, mismatch: neither}`. What it does not
    carry is `met`, and correctly so -- that one is a FIELD-SHAPE difference
    rather than a rename, and the cover group supplies it: `met` on the web means
    "it names one", which on paper is spelled by answering WHICH one, i.e. any of
    `labels`.
    """
    import enforcement as _E

    grp = next((g for g in (item.get("cover") or ())
                if c["what"] in (g.get("keys") or ())), None)
    if not grp:
        return text
    labels = list(grp.get("labels") or [])
    vocab = list(grp.get("verdicts") or [])
    if not labels or not vocab:
        return text
    out = text.replace("`met`", " or ".join(f"`{l}`" for l in labels))
    # bare "verdict", not "the verdict": the note says both "set `refers_to` to"
    # and "the expected `refers_to`", and only the bare form reads in both.
    out = out.replace("`refers_to`", "verdict")
    # The declared renames, web token -> rubric token, for THIS slot.
    for web_tok, paper_tok in (_E.VERDICT_PAIRS.get(f"{item['id']}/{c['what']}")
                               or {}).items():
        if web_tok != paper_tok:
            out = out.replace(f"`{web_tok}`", f"`{paper_tok}`")
    # The web's "neither of them" spelling for a cover pick.
    if "neither" in vocab:
        out = out.replace("`none`", "`neither`")
    # Only if the note has not already enumerated it. Q6's note ends "...`first`,
    # `second`, or `neither` if it is neither of them", so appending the list
    # again said the same thing twice in one breath.
    if all(f"`{v}`" in out for v in vocab):
        return out
    return (f"{out} Answer with ONE value from "
            f"{', '.join('`%s`' % v for v in vocab)} -- there is no separate "
            f"field on this side.")




# PAPER-ONLY text an item needs because of how a PAPER submission arrives.
# The mirror of `olx_prompts.ITEM_NOTES`, which does the same job for the web
# and says of itself: "Web-only text an item needs because of how its screen is
# built. Additions, not paraphrases: they say something about the web that the
# rubric cannot know." There was no paper counterpart, so a paper-side
# instruction had nowhere to live except an id list gating a mechanism -- which
# is the thing that must never vary by item.
#
# THE MECHANISM IS UNIFORM AND THE CONTENT IS PER ITEM. Every item is offered
# the same slot; what goes in it differs because the ITEMS differ, exactly as
# `guidance`, `credit` and `maps` differ. That is content, and content may vary.
# An id list that switches a mechanism on and off is not, and
# `enforcement.check_engine_mechanisms_are_not_item_dependent` still refuses it.
#
# EACH ENTRY IS A DECLARED WEB/PAPER DIVERGENCE and needs its own measurement.
# WHY EACH ENTRY IS PAPER-ONLY. Required beside every key below, for the same
# reason its web twin requires one: a note earns a side table only by saying
# something true of THIS side and not the other. Anything sayable to both is
# rubric content and belongs in `guidance`.
# ---------------------------------------------------------------------------
# STAGE 4. These tables were module-level course data here and are read from the
# course file now. The authored copies live in `declaration_source.py`, outside
# the scoring path, because the export must read them from somewhere that does
# not read the file it is writing.
# ---------------------------------------------------------------------------
def _declaration(name: str) -> dict:
    import coursedata

    return coursedata.declaration(name)


PAPER_ITEM_NOTES_WHY = _declaration("PAPER_ITEM_NOTES_WHY")

PAPER_ITEM_NOTES = _declaration("PAPER_ITEM_NOTES")


def _answer_inventory(item_id: str) -> str:
    """How many answers this item asks for, and how to read one block for them.

    THE STRUCTURE THIS SCORER IS NOT GIVEN. A paper submission arrives as one
    continuous block of prose under the item's heading -- deliberately, and it
    is the one real divergence between the sides -- so nothing in the text says
    where one answer stops and the next begins. The grader has to infer the
    count, and on one item it does not: a participant wrote a SINGLE antecedent/consequence pair,
    and paper answered `met` or `not_described` for `affect_c2` on 10 of 12
    disagreements, reading the first pair's sentence a second time. `affect_c2`
    agreed with the other side 43% of the time, the worst slot in the corpus
    once the instrument's own bugs were out of the way.

    Its own note is what invites that: "The same test as `affect_c1` above,
    applied to this box on its own" presumes a separate box to apply it to.

    MECHANICAL, from `olx_prompts.RESPONSE[item]` -- the answers the handout
    asks for, in order, with the framing already written for each. Nothing
    describes the other side: the grader is told what it asks for, that it
    arrives as one block, and what to do with an answer that is not there.

    THE LABELLED-PARTS CLAUSE AT THE END SHIPS FOR EVERY ITEM THIS EMITS FOR.
    It was briefly gated to Q3, where it was measured, until that was seen for
    an item-dependent MECHANISM. It stays conditional on what the STUDENT did,
    which is decided per submission.

    Emitted only above two answers. A single-answer item has no ambiguity about
    which answer is which and gets nothing.
    """
    from olx_prompts import RESPONSE

    answers = []
    for label, _target in (RESPONSE.get(item_id) or []):
        key, desc = ((label.split("—", 1)[0].strip().strip("`"),
                      label.split("—", 1)[1].strip())
                     if "—" in label else (None, label.strip()))
        if desc:
            answers.append((key, desc))
    if len(answers) < 2:
        return ""

    n = len(answers)
    out = [f"## The {n} answers this item asks for",
           "In the order the handout asks for them:"]
    # NUMBERED, and the slot id kept where the source has one. Q6's descriptions
    # repeat -- "how it will be changed" is both the second answer and the sixth
    # -- so a bare list could not say which was meant.
    for i, (key, desc) in enumerate(answers, 1):
        out.append(f"{i}. {('`%s` -- ' % key) if key else ''}{desc}")
    out += ["",
            "Everything the student wrote for this item reaches you as ONE "
            "continuous block of text. Decide which of these answers they "
            f"actually wrote. They may have written fewer than {n}, and they "
            "may have run more than one of them into a single sentence.",
            "",
            "Each answer must be a DISTINCT thing they wrote. If the text "
            "supplies only one, do not count that one statement twice.",
            "",
            "An answer they did not write is `absent`: there is nothing in it "
            "to quote or to judge as falling short, so its evidence says what "
            "you looked for and did not find."]

    return "\n".join(out) + "\n"


def _slot_body(item: dict, c: dict) -> str:
    """The judging text for one slot, resolved the way the WEB resolves it.

    THE WEB RENDERS TWO LINES PER SLOT AND THIS SIDE HAS ONE, so it must carry
    both. olx_prompts writes a checklist line holding the DESC with its points,
    and an answerable line holding `rule or SLOT_NOTES[item:key] or
    SLOT_NOTES[key]`. This function used to return the first of those that
    existed, so wherever a slot had a rule or a note the DESC was dropped -- 22
    slots across ten items (1a, 1c, D1, D2, Q2, Q3, Q4a, Q4b, Q5, Q6).

    IT HAS A MEASURED PRICE AND Q2 IS WHERE IT WAS PAID. `wgb_is_counterpart`'s
    desc says "The goal behaviour concerns the SAME behaviour as the Q1 UTB ...
    Fail this ONLY when the goal names a DIFFERENT activity"; its rule says "does
    the goal name a DIFFERENT ACTIVITY from the unwanted one?". The rule alone is
    a question whose YES means failure, and without the desc's framing the model
    inverts it: 8 of 20 paper cells scored 0 on WGB_UNRELATED, a whole-item
    deduction, and every one of them had a "lack of X" UTB whose goal is the SAME
    activity -- the exact case the desc exists to protect. Gold gives those cells
    4 or 5.

    The desc goes FIRST, as the web orders it, and is skipped when the judging
    text already contains it so nothing is said twice.

    NOT EVERY SLOT_NOTES ENTRY WAS EVER MISSING, and the difference is worth
    keeping: DAY1's consequence_asserted and D1/D2's named_type arrive through
    `_criterion_11` and the criteria section, TRANSFORMED by `_as_criterion`
    rather than copied. A head-match test reports them absent and a
    longest-shared-phrase test reports them carried; only Q6's four state_* and
    WK2's two were genuinely missing. Resolving through the same chain the web
    uses is what makes that distinction unnecessary to maintain by hand.
    """
    from olx_prompts import SLOT_NOTES

    desc = (c.get("desc") or "").strip()
    if c.get("rule"):
        body = fill_fail(c["rule"], item, c)
    else:
        note = (SLOT_NOTES.get(f"{item['id']}:{c['what']}")
                or SLOT_NOTES.get(c["what"]))
        body = _paper_vocab(item, c, fill_fail(note, item, c)) if note else ""
    if not body:
        return _describe_boxes(item, c, c["desc"])
    # THE WEB'S TWO LINES, KEPT AS TWO ROLES. olx_prompts renders the desc on
    # the checklist line (what the criterion IS) and the rule/note on the
    # answerable line (HOW to answer it). Concatenated with a space they read as
    # one sentence, and on Q6 they read as a contradictory one: "States the first
    # antecedent being changed, and it matches 4a `first` or `second` if ... names
    # an antecedent at all". Same two texts, opposite bars, no break between them.
    if desc and desc not in body:
        stop = "" if desc.rstrip().endswith((".", "!", "?", ":")) else "."
        out = f"{desc}{stop} HOW TO ANSWER: {body}"
    else:
        out = body
    return _describe_boxes(item, c, out)

def _oc_slot_notes(item: dict, asked: dict) -> str:
    """SLOT_NOTES text for the oc_analysis slots THIS prompt actually collects."""
    from olx_prompts import CLI_CRITERIA_NOTES, SLOT_NOTES

    lines = []
    for key in asked:
        # olx_prompts.CLI_CRITERIA_NOTES is the DECLARATION of which keys the
        # criteria machinery already renders for the CLI. Read it rather than
        # keeping a copy: its own comment says a second list "would go stale the
        # moment this list changed", and this file briefly held exactly that.
        if key in CLI_CRITERIA_NOTES:
            continue
        note = SLOT_NOTES.get(f"{item['id']}:{key}")
        if note:
            # THE THIRD AND LAST PATH BOX DEIXIS TRAVELS. A criteria item's
            # slot notes come through here, not through `_slot_body` and not
            # through `_criteria_section`, so WK2's `named_type` -- "READ BOTH
            # BOXES" -- survived translating both of those. WK2 has ONE box, so
            # the phrase is also wrong about the count; that part is not
            # translatable and is reported by
            # enforcement.check_paper_prompt_has_no_box_deixis instead.
            lines.append(f"- `{key}`: "
                         f"{_BOX_WORD.sub(_as_answer, ' '.join(note.split()))}")
    if not lines:
        return ""
    return "## Notes on individual slots\n" + "\n".join(lines) + "\n"


def build_prompt(
    item: dict,
    response: str,
    context: dict[str, str],
    hint: str | None,
    extra: str | None = None,
) -> str:
    parts = [f"# Rubric item {item['id']} — {item['max']:g} points\n"]
    parts.append(f"## Question asked of the student\n{item['question']}\n")

    if item.get("derive_from_criteria"):
        # ONE SOURCE for this prose. It used to live here in full, while
        # olx_prompts._criteria_section held a second copy whose docstring called
        # it "score.py:build_prompt's derive_from_criteria block, verbatim". It
        # was not verbatim any more: criterion 5's example had drifted ([[corpus <ITEM>/p<N> <field> <a>:<b> sha=...]] here against "a rested body, or
        # fitness itself, following the behaviour that produces it" there),
        # criterion 7's had too ("the extra chore" against "30 pushups"), and
        # criterion 10's WK1 rule here was an older, shorter version of the one
        # the web had grown. Two copies of a rule are two rules, and this pair
        # drifted exactly the way every other hand-kept mirror in this project
        # has. The web's wording wins wherever they differed and nothing forced
        # the difference; the forced substitutions are enumerated in
        # EQUIVALENCE.md and applied by _as_criterion.
        #
        # WHICH criteria get asked follows build_schema rather than an item id,
        # so the prompt cannot describe a field the answer sheet does not collect
        # -- the failure that put "put it in `evidence`" in front of a model
        # whose sheet has no evidence field.
        asked = build_schema(item)["properties"]["oc_analysis"]["properties"]
        # TRANSLATED ON THE WAY IN. `_criteria_section` is SHARED with the web
        # -- deliberately, so the two cannot drift -- which means it speaks the
        # web's language, boxes included. WK2's `named_type` says "READ BOTH
        # BOXES" and reached the paper grader untouched: the criteria items do
        # not go through `_slot_body`, so translating the slots left this whole
        # family standing. Same residual rule as everywhere else.
        # THE SCORER'S OWN SECTION. Goal P: which slots this course asks, and
        # whether the item gates on an avoidance frame, are the SCORER's choices
        # -- the engine was making them by name. `_criteria_section` is still
        # shared with the web, so the two still cannot drift.
        import scorers as _sc
        _plugin = _sc.for_item(item)
        parts.append(_BOX_WORD.sub(_as_answer, _plugin.prompt_section(item, asked)))
        # PER-SLOT JUDGING TEXT FOR THE OC SHEET. The criteria section carries
        # the numbered criteria; it does not carry text parked against an
        # individual oc_analysis slot, so anything in SLOT_NOTES for one of them
        # reached the web and left this scorer behind. Measured 2026-09-09:
        # WK2's `aimed_correctly` (659 chars -- subgoal Q40's measured win, which
        # took one cell from 4 of 11 to every run) and `named_type` (588) were
        # required properties of THIS schema that this prompt never mentioned.
        #
        # `consequence_asserted` and `trigger_behavior` are EXCLUDED because the
        # criteria machinery already renders them -- `_criterion_11` and
        # `_C10_TRIGGER` read the same SLOT_NOTES keys and pass them through
        # `_as_criterion`. Adding them here would print each twice, in two
        # different renderings, which is worse than the gap being closed.
        parts.append(_oc_slot_notes(item, asked))
        parts.append("")
    elif item.get("derive_from_credit"):
        computed = _computed_keys(item)      # not asked; see build_schema
        worths = {c.get("pts") for c in item["credit"] if not c.get("reported")
                  and not c.get("gates")}
        # Not `.pop()`: mutating the set here made the per-slot suffix below fire
        # as well, so every slot carried its points twice over.
        one = next(iter(worths)) if len(worths) == 1 else None
        parts.append(
            "## Slots to judge — return a verdict for EVERY one of these\n"
            + (f"Each slot is worth {one:g} point{'' if one == 1 else 's'} and is "
               "judged independently." if one is not None else
               "Each slot is judged independently; what each is worth is shown "
               "beside it.")
        )
        for c in item["credit"]:
            if c["what"] in computed:
                continue
            # `c.get("pts") is None` is checked as well as `reported`: an
            # unpointed slot that nobody flagged used to reach the format spec and
            # take the whole run down with a TypeError. Belt as well as braces —
            # the flag is the right fix, this stops the next omission crashing.
            worth = (" **GATE**" if c.get("gates") else
                     "" if c.get("reported") or c.get("pts") is None else
                     f" ({c['pts']:g} pt)" if one is None else "")
            vocab = (f" — {'/'.join('`%s`' % v for v in c['verdicts'])}"
                     if c.get("verdicts") else "")
            # The rubric's per-component `rule` is slot-specific judging text, and
            # the paper prompt's slot-specific field is this line. Without it the
            # web and CLI apply rules this scorer has never seen — which is how
            # Q4b's five substitution tests reached two scorers out of three.
            #
            # It REPLACES `desc`, exactly as the web's checklist does: there the
            # lookup is `rule or SLOT_NOTES or desc`, so a component with a rule
            # never shows its desc. This side used to show BOTH, which meant the
            # one field written to be read by both scorers was rendered
            # differently by each -- and the rules are written as the web renders
            # them, continuing from the `— `, so appending them after a desc
            # produced "Discusses the baseline week is the BEFORE state given".
            # No audit compared the two renderings, because both sides carried the
            # text and the audit asks only whether it is CARRIED.
            body = _slot_body(item, c)
            parts.append(f"- `{c['what']}`{worth}{vocab}: {body}")
        for cr in item.get("counts", []):
            members = ", ".join(f"`{k}`" for k in cr["slots"])
            parts.append(
                f"\nDO NOT ANSWER {members} individually. Answer `{cr['key']}` — HOW MANY "
                f"you found — and the code awards that many of them. Count them the way "
                f"the guidance above says to, in one judgement over the whole response, "
                f"rather than deciding each in isolation."
            )
        for r in item.get("equals", []):
            parts.append(
                f"\nDO NOT ANSWER `{r['key']}`. The code computes it by comparing "
                f"`{r['left']}` with `{r['right']}` — the two you DO answer. It is not "
                f"in your schema, and the comparison is not a judgement you can make "
                f"more accurately than the arithmetic can."
                + (f" Where either is `{'` or `'.join(r['lenient'])}`, no mismatch is "
                   f"established and nothing is charged." if r.get("lenient") else "")
            )
        if not any(c.get("verdicts") for c in item["credit"]):
          parts.append(
              "\nVerdicts: `met`, `absent` (not there at all), `mismatch` (present but a "
              "different antecedent/consequence than 4a/4c lists), `not_described` (the "
              "element is named but nothing is said about how it changes or is affected). "
              "Quote the span you relied on in `evidence`; for an absent slot, say briefly "
              "what you looked for. Do not output a score or a deduction list — the score "
              "is computed from these verdicts.\n"
          )
        for g in item.get("cover", []):
            keys = ", ".join(f"`{k}`" for k in g["keys"])
            parts.append(
                f"{keys} take a DIFFERENT set of verdicts: {' / '.join(g['verdicts'])}. "
                f"Say WHICH of the two items in {g['of']} that slot names — "
                f"`{g['labels'][0]}` or `{g['labels'][1]}` — or `neither` if it names "
                f"something that is not on that list, or `absent` if nothing is named "
                f"there at all. Report what the student actually named; do NOT adjust it "
                f"to make the pair come out right. Order does not matter, and you are not "
                f"being asked whether the pair covers both: the grader does that "
                f"arithmetic, and two slots naming the SAME item is a finding it makes on "
                f"its own.\n"
            )
    else:
        parts.append("## Credit components")
        for c in item["credit"]:
            # Same rule-replaces-desc as above; see the note there.
            body = _slot_body(item, c)
            parts.append(f"- `{c['what']}` ({c['pts']:g} pt): {body}")
        parts.append("")

        parts.append("## Deduction codes (use these exact codes; the points shown are applied for you)")
        for d in item["deductions"]:
            rep = " [repeatable]" if d.get("repeatable") else ""
            parts.append(f"- `{d['code']}` (-{d['pts']:g}){rep}: {d['text']}")
        parts.append("")

    # Suppressed when empty: an item whose guidance was all slot-specific has none
    # left here, and a bare header invites a hunt for absent instructions.
    if item["guidance"]:
        parts.append("## Grading guidance")
        for g in item["guidance"]:
            # GUIDANCE CARRIES BOX DEIXIS TOO, and it was the last place it
            # survived. `_describe_boxes` runs over SLOT bodies, so translating
            # the slots left 15 references standing in guidance alone -- all of
            # 2a's four bullets among them, on an item whose worst slot is one
            # of the three that say "Read all three boxes". No slot is in scope
            # here, so the pointing forms cannot be resolved to a particular
            # answer; the residual translation is what applies.
            parts.append(f"- {_BOX_WORD.sub(_as_answer, g)}")
        parts.append("")

    if item.get("exemplars"):
        parts.append(
            "## Worked examples\n"
            "Three responses from other students in this cohort, with the verdict sheet "
            "the human grader's marks imply. Match your judgements to these. They are "
            "reference material only — never grade them."
        )
        for ex in item["exemplars"]:
            parts.append(f"\n### {ex['label']}")
            parts.append(f"Their 4a: {ex['four_a']}")
            parts.append(f"Their 4c: {ex['four_c']}")
            parts.append(f"Their answer: {ex['response']}")
            verdicts = ", ".join(f"{k}={v}" for k, v in ex["slots"].items())
            parts.append(f"Verdicts: {verdicts}")
            parts.append(f"Why: {ex['note']}")
        parts.append("")

    if context:
        parts.append("## Context from this student's other answers (read-only)")
        parts.append(
            "Use these only where the rubric requires cross-item consistency. "
            "Do not grade them here."
        )
        for k, v in context.items():
            body = v.strip() or "(no response)"
            parts.append(f"\n### {k}\n{body}")
        parts.append("")

    if hint and item.get("reads_utb_choice"):
        parts.append(
            f"## Weak hint\nFormatting in the document marks '{hint}' as the "
            "underlined UTB choice. Only 6 of 20 transcriptions preserve this "
            "markup, so treat it as corroboration at most — read the UTB from "
            "the prose.\n"
        )

    parts.append(_answer_inventory(item["id"]))

    # THE UNIFORM MECHANISM: every item is offered a paper-side note, and the
    # ones that declare content get it. See PAPER_ITEM_NOTES.
    if item["id"] in PAPER_ITEM_NOTES:
        parts.append(PAPER_ITEM_NOTES[item["id"]] + "\n")

    if extra:
        parts.append(f"## Graph evidence for this submission\n{extra}\n")
        return "\n".join(parts)

    body = response.strip() or "(the student left this item blank)"
    parts.append(f"## Student response to grade (item {item['id']})\n{body}")
    # RESOLVE BEFORE THE GRADER SEES IT. Rubric guidance may cite a cell by
    # reference instead of quoting it; the repository holds the address and the
    # prompt must hold the words, or the model is asked to judge a placeholder.
    out = "\n".join(parts)
    if "[[corpus " in out:
        from tools import corpus_ref
        out = corpus_ref.expand_prose(out)
    return out



def fingerprint_text(item_id: str) -> str:
    """Everything THIS scorer asks about `item_id`, minus the submission.

    WHY IT EXISTS. `measured.prompt_sha` hashed the .olx section a WEB grader is
    served and had no paper branch, so `prompt_sha(item, "paper")` returned the
    web's hash -- for Q3 the paper and olx shas were the same twelve characters.
    Every paper-only element was therefore unstamped, and on 2026-09-10 that was
    seven of them at once: the labelled-parts clause, `_answer_inventory`,
    `_slot_body`'s desc+rule merge (the fix that took one item from under half its cells to all of them), `_computed_keys`'
    exempt-derived skip, `_web_vocab`'s enums, `derive_ledger`'s hedge fix and
    SYSTEM_TMPL. All shipped, none moved a sha, and the labelled-parts clause
    shipped GLOBALLY for a day without staling one paper column.

    `scorer_sha` does not cover it either: its closure for Q3 is 25 parts across
    agreement/olx_prompts/handouts and none in this file, and it is deliberately
    prose-insensitive -- which is right for behaviour and wrong for a prompt,
    where the prose IS the behaviour.

    WHAT IS FIXED SO IT HASHES THE TEXT AND NOT THE SUBMISSION: an empty
    response, so the response section is its constant blank marker. The
    conditional blocks are rendered rather than skipped -- a one-key context and
    a placeholder hint -- because their instruction prose is prompt text that
    would otherwise be hashed only for the items that happen to receive them.

    The schema is included: `build_schema` carries the per-slot verdict enums,
    and narrowing an enum changes what the grader may answer as surely as
    rewording the question does.

    NOT COVERED, and stated rather than left to be discovered: the graph-evidence
    section, which `build_prompt` renders only when `extra` is passed and which
    is per-submission. Its header is one constant line.
    """
    import json

    import forms as H

    for h in _H_RUBRIC.declared():
        cfg = H.config(h)
        item = next((i for i in cfg["rubric"].ITEMS if i["id"] == item_id), None)
        if item is None:
            continue
        return "\n".join([
            SYSTEM_TMPL.format(blurb=cfg["blurb"]),
            build_prompt(item, "", {"(fingerprint)": ""}, "(fingerprint)"),
            json.dumps(build_schema(item), sort_keys=True),
        ])
    raise KeyError(f"{item_id}: not in handout 1, 2 or 3's rubric")


_LEADING_PTS = re.compile(r"^-\s*[\d.]+\s*pts?\s*:\s*", re.I)


def compose_feedback(item: dict, result: dict) -> str:
    """Build the grader-style feedback string from the deduction ledger.

    Matches the graders' house style: a "-N pts: reason" ledger, second person,
    canonical dictionary wording. Some dictionary entries already carry their
    own "-1 pt:" prefix, so strip it before adding ours rather than emitting
    "-1 pts: -1 pt: ...".
    """
    texts = {d["code"]: d["text"] for d in item["deductions"]}
    chunks = []
    for d in result.get("deductions", []):
        canonical = _LEADING_PTS.sub("", texts.get(d["code"], "")).strip()
        note = (d.get("note") or "").strip()
        if canonical == "did not answer":
            chunks.append("did not answer")
            continue
        line = f"-{float(d['pts']):g} pts: {canonical}"
        if note and note.lower() not in canonical.lower():
            line += f" {note}"
        chunks.append(line)

    # The graders leave the feedback cell blank on full credit. Carry an
    # advisory note into the visible feedback only when something was actually
    # deducted, or when it is a safety note — otherwise keep it in its own
    # field so it does not read as a criticism of a perfect answer.
    adv = (result.get("advisory_note") or "").strip()
    if adv and (chunks or result.get("safety_flag")):
        chunks.append(adv)
    return " ".join(chunks).strip()


def score_item(
    backend, system: str, item: dict, response: str, context: dict, hint,
    extra: str | None = None,
) -> dict:
    prompt = build_prompt(item, response, context, hint, extra)
    if item.get("graph_item"):
        raw = backend.complete(
            system, prompt, build_schema(item), allow_tools=["Read"], max_turns=8
        )
    else:
        raw = backend.complete(system, prompt, build_schema(item))

    forced_advisory = None
    # THE SAME REGISTRY as `build_schema`, so an item's schema and its ledger can
    # never come from different scorers -- which is the failure a second dispatch
    # site invites.
    import scorers
    _plugin = scorers.for_item(item)
    # WHAT THE SCORER CONTRIBUTES BACK. Goal P. A scorer with no advisory concept
    # of its own contributes nothing, so the record simply lacks the key rather
    # than carrying another course's vocabulary set to False.
    _plugin_fields = (_plugin.record_fields(item, raw)
                      if _plugin is not None and hasattr(_plugin, "record_fields")
                      else {})
    if _plugin is not None:
        ledger, checks, unknown, forced_advisory = _plugin.derive_ledger(item, raw)
    elif item.get("derive_from_credit"):
        ledger, checks, unknown = derive_ledger(item, raw, response)
    else:
        valid = {d["code"]: d for d in item["deductions"]}
        ledger, unknown = [], []
        for d in raw.get("deductions", []):
            spec = valid.get(d.get("code"))
            if spec is None:
                unknown.append(d.get("code"))
                continue
            # Trust the rubric's point value, not the model's arithmetic.
            ledger.append(
                {"code": spec["code"], "pts": spec["pts"], "note": d.get("note", "")}
            )
        checks = raw.get("credit_checks", [])

    # An item cannot fail more slots than it has. Q6 in particular is eight
    # independent 1.25-point slots, and the failure mode observed in the first
    # baseline was stacking two codes on one slot (participant 9 drew five
    # deductions where the grader made two). Keep the largest deductions up to
    # the number of credit components and escalate rather than silently
    # over-deducting.
    over_specified = False
    if len(ledger) > len(item["credit"]):
        ledger = sorted(ledger, key=lambda d: -d["pts"])[: len(item["credit"])]
        over_specified = True

    total_off = sum(d["pts"] for d in ledger)
    score = max(0.0, min(item["max"], item["max"] - total_off))

    return {
        "item_id": item["id"],
        "label": item["label"],
        "max": item["max"],
        "score": round(score, 2),
        "deductions": ledger,
        "unknown_codes": unknown,
        "credit_checks": checks,
        # THE MODEL'S OWN ANSWERS ON THE CRITERIA PATH, which were being thrown
        # away. A `derive_from_credit` item keeps them: `credit_checks` carries
        # one `verdict` per slot, so a later reader can see what the grader
        # judged. A `derive_from_criteria` item does not -- derive_oc_ledger
        # returns DERIVED checks ({what, met, evidence}) and the raw
        # `oc_analysis` was read for one field and dropped, so every criteria
        # item recorded `verdict: None` on every check.
        #
        # That is a RECORDING gap and it blocks the comparison that matters now.
        # With the scoring arithmetic shown to agree on 3106 of 3120 cells, what
        # is left to compare between the sides is the JUDGMENTS -- and on the
        # eight criteria items there was nothing recorded to compare. Storing
        # the answers ALONGSIDE the derived checks rather than filling
        # `verdict`: subgoal E55 settled that inferred values must not be put
        # where readers expect answered ones, and these are answered ones, so
        # they get their own field.
        "oc_analysis": (raw.get("oc_analysis") or None
                        if item.get("derive_from_criteria") else None),
        "feedback": compose_feedback(
            item,
            {
                "deductions": ledger,
                "advisory_note": forced_advisory or raw.get("advisory_note"),
        **(_plugin_fields),
                "safety_flag": raw.get("safety_flag"),
            },
        ),
        "advisory_note": forced_advisory or raw.get("advisory_note"),
        **_plugin_fields,
        "safety_flag": bool(raw.get("safety_flag")),
        "over_specified": over_specified,
        "escalate": (
            bool(raw.get("escalate")) or bool(unknown) or over_specified
            or forced_advisory is not None
        ),
        "response_chars": len(response.strip()),
    }


def score_participant(
    backend, form: int, path: str, pid: int,
    only: list[str] | None = None, outdir: str | None = None,
    retry_missing: bool = False,
) -> dict:
    """Score one participant. `only` re-scores a subset of items and merges the
    results into that participant's existing file, so a guidance change can be
    re-measured without paying to re-run items it did not touch."""
    cfg = config(form)
    items = cfg["rubric"].ITEMS
    outdir = outdir or cfg["outdir"]
    system = SYSTEM_TMPL.format(blurb=cfg["blurb"])

    sections = segment(
        path,
        cfg["template"],
        cfg["markers"],
        cfg["capture_tail"],
        cfg.get("join_aware", False),
    )
    repairs: list[dict] = []
    if cfg.get("repair_orphans"):
        sections, repairs = repair_orphans(sections, [i["id"] for i in items])
    repaired_items = {r["moved_to"] for r in repairs} | {r["moved_from"] for r in repairs}
    hint = utb_hint(path) if form == 1 else None
    results: dict[str, dict] = {}

    prior_path = os.path.join(outdir, f"participant_{pid:03d}.json")
    if (only or retry_missing) and os.path.exists(prior_path):
        with open(prior_path) as fh:
            for it in json.load(fh)["items"]:
                results[it["item_id"]] = it
    if retry_missing:
        # Re-score exactly the cells a previous run failed to produce, so a
        # transient backend outage costs only the lost items.
        only = [k for k, v in results.items() if v.get("score") is None]
        if not only:
            return _assemble(form, path, pid, results, hint, repairs)

    for item in items:
        if only and item["id"] not in only:
            continue
        ctx = {k: sections.get(k, "") for k in item["context"]}
        try:
            extra = (
                graph_bundle(path, pid, sections.get(item["id"], ""))
                if item.get("graph_item")
                else None
            )
            results[item["id"]] = score_item(
                backend, system, item, sections.get(item["id"], ""), ctx, hint, extra
            )
        except BackendError as e:
            results[item["id"]] = {
                "item_id": item["id"],
                "label": item["label"],
                "max": item["max"],
                "score": None,
                "error": str(e),
                "escalate": True,
                "response_chars": len(sections.get(item["id"], "").strip()),
            }

    # A relocated answer is a best-effort reading of a student layout error, so
    # surface it for review rather than trusting it silently.
    for iid in repaired_items:
        if iid in results and isinstance(results[iid], dict):
            results[iid]["escalate"] = True
            results[iid]["layout_repaired"] = True
    return _assemble(form, path, pid, results, hint, repairs)


def _assemble(form: int, path: str, pid: int, results: dict, hint, repairs=None) -> dict:
    items = config(form)["rubric"].ITEMS
    scored = [
        results[it["id"]]["score"]
        for it in items
        if results.get(it["id"], {}).get("score") is not None
    ]
    return {
        "participant_id": pid,
        "handout": form,
        "source_file": os.path.basename(path),
        "scored_total": round(sum(scored), 2),
        "scored_max": sum(it["max"] for it in items),
        "upload_points": None,  # not derivable from the response — see README
        "items": [results[it["id"]] for it in items if it["id"] in results],
        "utb_format_hint": hint,
        "layout_repairs": repairs or [],
    }


def main() -> int:
    # NOT WHILE THE AUDIT SELF-TEST IS RUNNING. It injects breakages into the
    # rubric and enforcement source this process reads live, so an overlapping
    # sweep scores some cells against a rule nobody wrote -- and says nothing.
    # The mirror of olx_prompts._measurements_in_flight, which guards the other
    # direction. See refuse_if_selftest_running for the escape.
    import olx_prompts as _OP_GUARD
    _OP_GUARD.refuse_if_selftest_running("this paper sweep")

    ap = argparse.ArgumentParser()
    ap.add_argument("--form", "--handout", type=int, default=1, choices=sorted(__import__("forms").FORMS))
    # `lo` sends THIS prompt to lo-blocks' endpoint, i.e. the model the web and
    # agreement.py use. Against `cli` it isolates the model; against agreement.py
    # it isolates the prompt. See backends.LoBlocksBackend.
    ap.add_argument("--backend", default="cli", choices=["cli", "api", "lo"])
    ap.add_argument("--participants", type=int, nargs="*", default=None)
    ap.add_argument(
        "--items",
        nargs="*",
        default=None,
        help="Re-score only these item ids, merging into existing output files.",
    )
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--retry-missing", action="store_true",
                    help="Re-score only items a previous run left unscored.")
    ap.add_argument("--max-budget-usd", type=float, default=None)
    ap.add_argument("--outdir", default=None)
    args = ap.parse_args()

    kw = {}
    if args.backend == "cli" and args.max_budget_usd:
        kw["max_budget_usd"] = args.max_budget_usd
    backend = make_backend(args.backend, **kw)

    cfg = config(args.form)
    outdir = args.outdir or cfg["outdir"]
    os.makedirs(outdir, exist_ok=True)
    targets = find_submissions(args.form, args.participants)
    n_items = len(args.items) if args.items else len(cfg["rubric"].ITEMS)
    scope = f" ({', '.join(args.items)} only, merging)" if args.items else ""
    print(
        f"H{args.form}: scoring {len(targets)} participant(s) x {n_items} items{scope}",
        file=sys.stderr,
    )

    t0 = time.time()
    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs = {
            pool.submit(
                score_participant, backend, args.form, path, pid, args.items, outdir,
                args.retry_missing
            ): pid
            for pid, path in targets
        }
        for fut in as_completed(futs):
            pid = futs[fut]
            try:
                rec = fut.result()
            except Exception as e:  # keep going; one bad file must not stop the run
                print(f"  participant {pid}: FAILED {e}", file=sys.stderr)
                continue
            # Provenance. Without it a results directory cannot say which backend
            # produced it, and baseline.py cannot tell a graph item scored WITH
            # image tools from one scored blind — which is the difference between
            # a real 88% and a 29% that is a missing tool. Recorded per file so a
            # directory assembled from more than one run is still readable.
            rec["backend"] = type(backend).__name__
            rec["supports_tools"] = bool(getattr(backend, "SUPPORTS_TOOLS", False))
            # WHAT THIS RAN AGAINST, on the paper side too. cross_path.py compares
            # this scorer against the web path cell by cell, and without an era on
            # both sides a prompt-version difference reads as a path difference.
            # See measured.era_stamp.
            # The BACKEND is passed explicitly, as `args.backend` and NOT as
            # `rec["backend"]`. era_stamp defaults it to empty, and this is the
            # only process that knows which one ran; left to default it stamped
            # "", so a paper artifact could not say from its era whether it was
            # the gpt-5-mini run (side `paper`) or the Opus one (side
            # `paper_opus`) -- the single distinction the two sides exist to keep
            # apart. paper_runs.py passes it at fold time from sweep_paper.sh, so
            # the ledger was right; the per-participant file, which is what
            # survives if a fold is redone by hand, was not.
            #
            # WHICH VALUE matters, and the first fix got it wrong: stamping
            # `rec["backend"]` put the CLASS NAME there -- "LoBlocksBackend"
            # against paper_runs' "lo" -- so one field carried two vocabularies
            # depending on which writer filled it, in the field that decides the
            # side. `args.backend` is the token sweep_paper.sh passes to both,
            # and the one `lo` -> paper / `api`|`cli` -> paper_opus is keyed on.
            # `rec["backend"]` stays as it is: the class that actually ran, with
            # supports_tools beside it, which answers a different question.
            try:
                import measured as _M
                rec["era"] = _M.era_stamp([i["item_id"] for i in rec["items"]],
                                          backend=args.backend)
            except Exception as _e:      # never fail a sweep over bookkeeping
                rec["era"] = {"error": f"{type(_e).__name__}: {_e}"}
            with open(os.path.join(outdir, f"participant_{pid:03d}.json"), "w") as fh:
                json.dump(rec, fh, indent=2)
            done += 1
            esc = sum(1 for i in rec["items"] if i.get("escalate"))
            print(
                f"  [{done}/{len(targets)}] participant {pid:>2}: "
                f"{rec['scored_total']:>5.2f}/{rec['scored_max']:g}"
                + (f"  ({esc} escalated)" if esc else ""),
                file=sys.stderr,
            )

    dt = time.time() - t0
    cost = getattr(backend, "total_cost_usd", None)
    print(
        f"done in {dt:.0f}s, {backend.calls} calls"
        + (f", ${cost:.2f}" if cost else ""),
        file=sys.stderr,
    )
    return 0


# --- corpus reference resolution (backdated) ---
# The paper prompt is assembled from rubric guidance, which may cite a cell by
# reference. Unresolved, the grader is asked to score the reference itself.
try:                                            # pragma: no cover
    import corpus_resolve as _corpus_resolve
    _corpus_orig_build_prompt = build_prompt

    def build_prompt(*a, _orig=_corpus_orig_build_prompt, **kw):
        return _corpus_resolve.expand(_orig(*a, **kw))
except Exception:
    pass


if __name__ == "__main__":
    raise SystemExit(main())
