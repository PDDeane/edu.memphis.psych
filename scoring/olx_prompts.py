#!/usr/bin/env python3
"""Generate the lo-blocks <LLMAction> prompt bodies from the CLI rubric.

EQUIVALENCE.md is the why. In short: `agreement_app.py` measures the web
version against the same gold rows `baseline.py` uses, and that comparison only
means something if both run the SAME rubric. Until now the web prompts were
hand-written paraphrases, so the measurement compared "the rubric" with "a
summary of the rubric".

This module is the fix. Every one of the 23 <LLMAction> prompt bodies in
`content/psychology/bmod_handout{1,2,3}.olx` is now generated from
`rubric_hN.py`, following `score.py:build_prompt`'s skeleton — item header,
question as asked, credit components with points, deduction code table, all
guidance bullets, exemplars, context — copied verbatim.

    python3 olx_prompts.py --print Q4a   # one generated prompt, to stdout
    python3 olx_prompts.py --check       # do the .olx files match? (exit 1 if not)
    python3 olx_prompts.py --write       # regenerate the three .olx files

DO NOT HAND-EDIT the prompt bodies in the .olx files. Change `rubric_hN.py`, or
change this module, and re-run `--write`. `--check` fails if someone has.

Everything the web sends that the CLI does not, or vice versa, is a DEVIATION.
Each is declared here — in WEB_SYSTEM's rule table, RESPONSE / CONTEXT,
OMIT_CREDIT / OMIT_DEDUCTION / OMIT_GUIDANCE, or ITEM_NOTES — and written up in
EQUIVALENCE.md. That is the contract: a difference that is in neither place is a
bug, and `equivalence.py` counts it as an undeclared gap.
"""
from __future__ import annotations

import argparse
import difflib
import functools
import os
import re
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from handouts import config
import paths

# The `{fail}` placeholder in a shared `rule`, bare or slot-qualified. ONE
# definition, imported by score.py rather than restated: the two generators must
# recognise exactly the same syntax, and every hand-kept mirror in this project
# has drifted. score.py imports from here, so this is the end that can hold it.
_FAIL_RE = re.compile(r"\{fail(?::([A-Za-z0-9_]+))?\}")

OLX = paths.OLX

# The slot-sheet primitives, shared with the TypeScript side. Adding one has to be
# taught to five consumers and this generator was missed twice; the file says which
# they are and `equivalence.py --enforcement` checks each is actually honoured here.
PRIMITIVES_JSON = paths.PRIMITIVES_JSON


def primitives() -> dict:
    import json as _json
    with open(PRIMITIVES_JSON) as fh:
        return _json.load(fh)


def primitive_attrs(excluding_keys: bool | None = None) -> list[str]:
    """Attribute names, optionally only those whose keys leave the schema."""
    return [p["attr"] for p in primitives()["primitives"]
            if excluding_keys is None or p["excludesKeys"] == excluding_keys]


# RULES NEITHER PROBE CAN CROSS-CHECK, which is NOT a list of scoring
# divergences and used to be filed as one.
#
# The enforcement audit verifies a rule two different ways. The web side READS
# declared rules off the .olx attributes; the CLI side PROBES, flipping answered
# fields and watching the score move. Those instruments have different reach, so
# each can find a rule the other cannot -- and when that happens the audit used
# to report it as "CHARGE-ONCE OLX ONLY" or "PYTHON ONLY", filed in
# SCORING_DIVERGENCES beside genuine prompt-and-scoring differences.
#
# BOTH HALVES OF THAT WERE WRONG. The name reads as a claim that a rule is
# enforced on one engine only, which would contradict the engine equivalence the
# whole pooled column rests on -- identical prompt bodies, identical request
# parameters, and 221 shared verdict signatures scoring identically. It is not a
# claim about the engines at all. Every entry that was ever filed here says so in
# its own words: "The behaviour is identical; what differs is what the instrument
# can reach." And the filing compounded the name: an audit-coverage gap listed as
# a scoring divergence gets read as one. It got read as one by the assistant that
# wrote it, twice in a day -- once reporting a probe gap to the user as a possible
# engine divergence and spending an hour disproving it.
#
# So an entry here records ONE fact: this rule's cross-engine agreement is
# ASSERTED, not probed. That is weaker than a probed rule and the entry should be
# read as the weaker thing. What backs it instead is
# enforcement.check_engines_score_identical_verdicts_alike, over the verdict
# signatures both engines have actually produced.
# ---------------------------------------------------------------------------
# STAGE 4 (B2a, A1c). Eleven tables were module-level DATA here -- 11 tables and
# 190 item ids by T1.1's count, which is what made this module carry course
# content. The data is now in the course file and is READ.
#
# THE NAMES STAY. Eight modules reference them -- enforcement, score,
# agreement_app, handouts, precommit_gate, equivalence among them -- so moving
# the data without moving the names keeps every consumer working, and lets the
# move be judged by the only test that settles it: the 23 generated prompts must
# come out byte-identical.
#
# The authored tables survive in `generator_source.py`, a builder OUTSIDE the
# scoring path, because the export must read them from somewhere that does not
# read the file it is writing.
# ---------------------------------------------------------------------------
_FIELD_TO_TABLE = {
    "prompt_action": "ACTION", "prompt_response": "RESPONSE",
    "prompt_context": "CONTEXT", "prompt_sheet_only": "SHEET_ONLY",
    "prompt_evidence": "EVIDENCE", "prompt_omit_guidance": "OMIT_GUIDANCE",
    "prompt_match_def": "MATCH_DEF", "prompt_notes": "ITEM_NOTES",
    "prompt_notes_why": "ITEM_NOTES_WHY",
}


def table_name(field: str) -> str:
    return _FIELD_TO_TABLE.get(field, "")


def _generator_table(field: str, table: str = "") -> dict:
    """{key: value} for one generator field. Absent keys stay ABSENT.

    `SHEET_ONLY` names three items of twenty-six; the export omits the field on
    the other twenty-three rather than storing null, so `in SHEET_ONLY` still
    means what it meant.

    `table` names a table with NON-ITEM keys to merge back -- `CONTEXT` carries
    handout 2's two section headings as well as its items, kept at course level
    because an item entry is the wrong home for a section.
    """
    import coursedata

    out = {iid: gen[field]
           for iid, gen in coursedata.generator_items().items()
           if field in gen}
    # Restore the table's AUTHORED key order. The fields live on item entries, so
    # the comprehension above walks items in rubric order -- a different order
    # from the one the table was written in, which `==` cannot see and which the
    # JOBS case showed can matter.
    if table:
        extra = coursedata.generator_value(f"{table}__non_item")
        if extra:
            out.update(extra)
    # ORDER LAST, AFTER the non-item residue is merged. Applying it first put
    # `_utb` and `_wgb` at the end, because `update` appends -- and CONTEXT's
    # authored order interleaves them. The order restoration has to see the whole
    # table, not the part that came from item entries.
    order = (coursedata.generator_value("TABLE_ORDER") or {}).get(table_name(field))
    if order:
        out = {k: out[k] for k in order if k in out} | {
            k: v for k, v in out.items() if k not in order}
    return out


def _generator_value(name: str):
    """A course-level generator value -- a list about the course, not an item."""
    import coursedata

    return coursedata.generator_value(name)


PROBE_REACH_LIMITS = _generator_value("PROBE_REACH_LIMITS")

# Which rubric item each <LLMAction> carries. (equivalence.py holds the same
# map; it imports this one so the two cannot drift.)
ACTION = _generator_table("prompt_action")
# Items scored from a slot sheet with NO prompt: every verdict is derived from
# the page, so there is no <LLMAction> and nothing for `--prompts` to compare.
# They are still audited for arithmetic (`--scoring`) and enforcement.
SHEET_ONLY = _generator_table("prompt_sheet_only")

HANDOUT = {i: (1 if a.startswith("bmod_h1") else 2 if a.startswith("bmod_h2") else 3)
           for i, a in {**ACTION, **SHEET_ONLY}.items()}


def sheet_id(item: str) -> str:
    """The element carrying this item's slot sheet."""
    return ACTION.get(item) or SHEET_ONLY[item]


# ---------------------------------------------------------------------------
# The inlined system prompt.
#
# DEVIATION 2 (permitted): LLMAction has no system-message channel, so
# score.py's SYSTEM_TMPL heads the user prompt instead. Rules 3 and 5 are
# verbatim; the rest are re-pointed at the fields that actually exist here,
# because the web returns {checks, feedback} rather than a deduction ledger
# (DEVIATION 3). `_check_rules_still_match` asserts the verbatim ones really
# are verbatim, so a change to SYSTEM_TMPL cannot silently desynchronise this.
# ---------------------------------------------------------------------------

VERBATIM_RULES = [
    # (rule number, the text that must still appear verbatim in SYSTEM_TMPL)
    (3, "Do NOT output a score."),
    (5, "Grade what is written, generously but not charitably: these are first-year\n"
        "   students, so clumsy phrasing that clearly conveys the required idea earns\n"
        "   credit, but a required element that is absent is absent."),
]

WEB_SYSTEM = """You are an experienced teaching assistant grading {blurb}
This is PSYC 1030 (General Psychology, intro level, first-year students).

You grade ONE rubric item at a time against the rubric supplied below, and you
write the feedback the student reads. Return the JSON object the schema
requires: the `checks` sheet first, then `feedback`.

Rules you must follow:
1. Judge the item check by check. For every check on the sheet below, decide
   its verdict and quote the span of the response that settles it in that
   check's `evidence`. Quote verbatim; never paraphrase into the evidence
   field. For an unsatisfied check, say briefly what you looked for.
2. The deduction table below is the course's canonical wording for each way
   this item goes wrong. It is not a ledger for you to fill in — name any gap
   in `feedback` using that table's own words, so a student who fixes what you
   flagged meets the same phrasing if the same gap is graded later. The CODE
   beside each entry is an internal label: use the wording, and never put the
   code or its point value in front of the student.
3. Do NOT output a score. The score is computed from your checks.
4. `feedback` must be consistent with `checks`: do not praise something you
   marked unsatisfied, and do not fault something you marked satisfied.
5. Grade what is written, generously but not charitably: these are first-year
   students, so clumsy phrasing that clearly conveys the required idea earns
   credit, but a required element that is absent is absent.
6. If the response is empty, mark every check unsatisfied and say so plainly.
7. If the student describes something that could harm them (skipping meals,
   punishing themselves by withholding food or sleep, etc.), say so warmly in
   `feedback` and suggest a safer version. That is a safety note, not a fault
   in their work, and it never changes a verdict.
8. Where the grading guidance below tells you to set `escalate` or to write an
   `advisory_note`, there is no such field here: put the remark in `feedback`
   instead, and where the sheet carries a `confident` check, set it to `absent`.

Write `feedback` to the student, in the second person, warm and specific. Say
which requirements are met, name any that are missing, and quote their own
words when you point something out. It must read as prose written to them: no
deduction codes, no point values, no score, and no check keys."""


def _check_rules_still_match() -> list[str]:
    """SYSTEM_TMPL is the source; report any verbatim rule that has drifted."""
    from score import SYSTEM_TMPL

    bad = []
    for n, text in VERBATIM_RULES:
        if text not in SYSTEM_TMPL:
            bad.append(f"rule {n} no longer appears verbatim in score.py:SYSTEM_TMPL")
        if text not in WEB_SYSTEM:
            bad.append(f"rule {n} no longer appears verbatim in WEB_SYSTEM")
    return bad


# ---------------------------------------------------------------------------
# Fixtures: which on-screen field carries what.
#
# DEVIATION 1 (permitted): the student's response arrives per-field. The CLI
# parses one prose block; the web gives one box per judgement. RESPONSE lists
# those boxes, in the order they appear on the screen.
#
# CONTEXT maps each rubric record's `context` key to the web component(s)
# holding the same material. The paper Q1 block contains both the chosen UTB
# and the prose about it, so `Q1` maps to the closed choice AND the text area;
# the same split explains `_utb` / `_wgb`.
# ---------------------------------------------------------------------------

RESPONSE = _generator_table("prompt_response")

CONTEXT = _generator_table("prompt_context", "CONTEXT")

# Q1 and Q2 are the two items where score.py adds a "## Weak hint" section,
# read out of the .docx's underline formatting and correct in only 6 of 20
# transcriptions. The web asks for the UTB as a closed choice before question
# 1, so the same fact arrives authoritatively. This replaces that section.
#
# Q2 was dropped from this list when the later items moved onto the behaviour the
# student DESCRIBED. It was getting both: the raw choice under "the behavior they
# chose", and the described one under context — two different answers to the same
# question, under two headings, which is exactly what the `seen` guard below
# exists to prevent. That guard keys on component id, so pointing context at a
# different component walked straight past it. Q1 keeps the section because
# comparing the two IS its job (`matches_selected`).

# Ref ids already in the .olx, kept so component ids stay stable across the
# rewrite: (action id, target) -> ref id. Anything not here is minted below.
REF_IDS = {
    "bmod_h1_q1_llm": {
        "bmod_h1_utb": "bmod_h1_q1_ref_utb",
        "bmod_h1_q1_response": "bmod_h1_q1_ref",
    },
    "bmod_h1_q2_llm": {
        "bmod_h1_utb": "bmod_h1_q2_llm_ref_utb",
        "bmod_h1_q1_response": "bmod_h1_q2_ref_q1_response",
        "bmod_h1_q2_response": "bmod_h1_q2_ref",
    },
    "bmod_h1_q3_llm": {
        "bmod_h1_utb": "bmod_h1_q3_ref_utb",
        "bmod_h1_q1_response": "bmod_h1_q3_ref_q1_response",
        "bmod_h1_q2_response": "bmod_h1_q3_ref_wgb",
        "bmod_h1_q3_specific": "bmod_h1_q3_ref_s",
        "bmod_h1_q3_measurable": "bmod_h1_q3_ref_m",
        "bmod_h1_q3_action": "bmod_h1_q3_ref_a",
        "bmod_h1_q3_realistic": "bmod_h1_q3_ref_r",
        "bmod_h1_q3_timebound": "bmod_h1_q3_ref_t",
    },
    "bmod_h1_q4a_llm": {
        "bmod_h1_utb": "bmod_h1_q4a_ref_utb",
        "bmod_h1_q1_response": "bmod_h1_q4a_ref_q1_response",
        "bmod_h1_q4a_first": "bmod_h1_q4a_ref1",
        "bmod_h1_q4a_second": "bmod_h1_q4a_ref2",
    },
    "bmod_h1_q4b_llm": {
        "bmod_h1_utb": "bmod_h1_q4b_ref_utb",
        "bmod_h1_q1_response": "bmod_h1_q4b_ref_q1_response",
        "bmod_h1_q2_response": "bmod_h1_q4b_ref_q2_response",
        "bmod_h1_q4a_first": "bmod_h1_q4b_llm_ref_a1",
        "bmod_h1_q4a_second": "bmod_h1_q4b_llm_ref_a2",
        "bmod_h1_q4b_first": "bmod_h1_q4b_ref1",
        "bmod_h1_q4b_second": "bmod_h1_q4b_ref2",
        "bmod_h1_q4b_modify": "bmod_h1_q4b_ref_m",
    },
    "bmod_h1_q4c_llm": {
        "bmod_h1_utb": "bmod_h1_q4c_ref_utb",
        "bmod_h1_q1_response": "bmod_h1_q4c_ref_q1_response",
        "bmod_h1_q4a_first": "bmod_h1_q4c_ref_a1",
        "bmod_h1_q4a_second": "bmod_h1_q4c_ref_a2",
        "bmod_h1_q4b_first": "bmod_h1_q4c_ref_b1",
        "bmod_h1_q4b_second": "bmod_h1_q4c_ref_b2",
        "bmod_h1_q4c_first": "bmod_h1_q4c_ref1",
        "bmod_h1_q4c_second": "bmod_h1_q4c_ref2",
    },
    "bmod_h1_q5_llm": {
        "bmod_h1_utb": "bmod_h1_q5_ref_utb",
        "bmod_h1_q1_response": "bmod_h1_q5_ref_q1_response",
        "bmod_h1_q4c_first": "bmod_h1_q5_ref_c1",
        "bmod_h1_q4c_second": "bmod_h1_q5_ref_c2",
        "bmod_h1_q5_first": "bmod_h1_q5_ref1",
        "bmod_h1_q5_second": "bmod_h1_q5_ref2",
    },
    "bmod_h1_q6_llm": {
        "bmod_h1_utb": "bmod_h1_q6_ref_utb",
        "bmod_h1_q1_response": "bmod_h1_q6_ref_q1_response",
        "bmod_h1_q2_response": "bmod_h1_q6_ref_q2_response",
        "bmod_h1_q4a_first": "bmod_h1_q6_llm_ref_a1",
        "bmod_h1_q4a_second": "bmod_h1_q6_llm_ref_a2",
        "bmod_h1_q4c_first": "bmod_h1_q6_llm_ref_c1",
        "bmod_h1_q4c_second": "bmod_h1_q6_llm_ref_c2",
        "bmod_h1_q6_state_a1": "bmod_h1_q6_ref_sa1",
        "bmod_h1_q6_change_a1": "bmod_h1_q6_ref_ca1",
        "bmod_h1_q6_state_c1": "bmod_h1_q6_ref_sc1",
        "bmod_h1_q6_affect_c1": "bmod_h1_q6_ref_ac1",
        "bmod_h1_q6_state_a2": "bmod_h1_q6_ref_sa2",
        "bmod_h1_q6_change_a2": "bmod_h1_q6_ref_ca2",
        "bmod_h1_q6_state_c2": "bmod_h1_q6_ref_sc2",
        "bmod_h1_q6_affect_c2": "bmod_h1_q6_ref_ac2",
    },
    "bmod_h2_pr_llm": {
        "bmod_h1_utb": "bmod_h2_pr_ref_utb",
        "bmod_h1_q2_response": "bmod_h2_pr_ref_wgb",
        "bmod_h2_pr": "bmod_h2_pr_ref",
    },
    "bmod_h2_nr_llm": {
        "bmod_h1_utb": "bmod_h2_nr_ref_utb",
        "bmod_h1_q2_response": "bmod_h2_nr_ref_wgb",
        "bmod_h2_nr": "bmod_h2_nr_ref",
    },
    "bmod_h2_pp_llm": {
        "bmod_h1_utb": "bmod_h2_pp_ref_utb",
        "bmod_h1_q2_response": "bmod_h2_pp_ref_wgb",
        "bmod_h2_pp": "bmod_h2_pp_ref",
    },
    "bmod_h2_np_llm": {
        "bmod_h1_utb": "bmod_h2_np_ref_utb",
        "bmod_h1_q2_response": "bmod_h2_np_ref_wgb",
        "bmod_h2_np": "bmod_h2_np_ref",
    },
    "bmod_h2_d1_llm": {
        "bmod_h1_utb": "bmod_h2_d1_ref_utb",
        "bmod_h1_q2_response": "bmod_h2_d1_ref_q2_response",
        "bmod_h2_t1": "bmod_h2_d1_ref_t",
        "bmod_h2_d1": "bmod_h2_d1_ref",
    },
    "bmod_h2_day1_llm": {
        "bmod_h1_utb": "bmod_h2_day1_ref_utb",
        "bmod_h1_q2_response": "bmod_h2_day1_ref_wgb",
        "bmod_h2_t1": "bmod_h2_day1_ref_t",
        "bmod_h2_d1": "bmod_h2_day1_ref_d",
        "bmod_h2_day1": "bmod_h2_day1_ref",
    },
    "bmod_h2_wk1_llm": {
        "bmod_h1_utb": "bmod_h2_wk1_ref_utb",
        "bmod_h1_q2_response": "bmod_h2_wk1_ref_wgb",
        "bmod_h2_t1": "bmod_h2_wk1_ref_t",
        "bmod_h2_d1": "bmod_h2_wk1_ref_d",
        "bmod_h2_wk1": "bmod_h2_wk1_ref",
    },
    "bmod_h2_d2_llm": {
        "bmod_h1_utb": "bmod_h2_d2_ref_utb",
        "bmod_h1_q2_response": "bmod_h2_d2_ref_q2_response",
        "bmod_h2_t2": "bmod_h2_d2_ref_t",
        "bmod_h2_d2": "bmod_h2_d2_ref",
    },
    "bmod_h2_day2_llm": {
        "bmod_h1_utb": "bmod_h2_day2_ref_utb",
        "bmod_h1_q2_response": "bmod_h2_day2_ref_wgb",
        "bmod_h2_t2": "bmod_h2_day2_ref_t",
        "bmod_h2_d2": "bmod_h2_day2_ref_d",
        "bmod_h2_day2": "bmod_h2_day2_ref",
    },
    "bmod_h2_wk2_llm": {
        "bmod_h1_utb": "bmod_h2_wk2_ref_utb",
        "bmod_h1_q2_response": "bmod_h2_wk2_ref_wgb",
        "bmod_h2_t2": "bmod_h2_wk2_ref_t",
        "bmod_h2_d2": "bmod_h2_wk2_ref_d",
        "bmod_h2_wk2": "bmod_h2_wk2_ref",
    },
    "bmod_h3_overview_llm": {
        "bmod_h3_overview_response": "bmod_h3_ov_ref",
    },
    "bmod_h3_graph_llm": {
        "bmod_h3_baseline": "bmod_h3_graph_ref_baseline",
        "bmod_h3_wk1": "bmod_h3_graph_ref_wk1",
        "bmod_h3_wk2": "bmod_h3_graph_ref_wk2",
        "bmod_h3_wk3": "bmod_h3_graph_ref_wk3",
        "bmod_h3_graph_title": "bmod_h3_g_ref_t",
        "bmod_h3_graph_x": "bmod_h3_g_ref_x",
        "bmod_h3_graph_y": "bmod_h3_g_ref_y",
    },
    "bmod_h3_success_llm": {
        "bmod_h3_overview_response": "bmod_h3_su_ref_ov",
        "bmod_h3_success_verdict": "bmod_h3_su_ref_v",
        "bmod_h3_success_how1": "bmod_h3_su_ref_1",
        "bmod_h3_success_how2": "bmod_h3_su_ref_2",
    },
    "bmod_h3_assessment_llm": {
        "bmod_h3_success_verdict": "bmod_h3_assessment_ref_success_verdict",
        "bmod_h3_success_how1": "bmod_h3_assessment_ref_success_how1",
        "bmod_h3_success_how2": "bmod_h3_assessment_ref_success_how2",
        "bmod_h3_assessment_response": "bmod_h3_as_ref",
    },
    "bmod_h3_improve_llm": {
        "bmod_h3_success_verdict": "bmod_h3_improve_ref_success_verdict",
        "bmod_h3_success_how1": "bmod_h3_improve_ref_success_how1",
        "bmod_h3_success_how2": "bmod_h3_improve_ref_success_how2",
        "bmod_h3_assessment_response": "bmod_h3_improve_ref_assessment_response",
        "bmod_h3_improve_first": "bmod_h3_im_ref_1",
        "bmod_h3_improve_second": "bmod_h3_im_ref_2",
    },
}


# ---------------------------------------------------------------------------
# Declared omissions. Everything the CLI sends is sent, EXCEPT these.
# Each entry needs a reason; equivalence.py reads this table so its coverage
# figures count an omission as accounted-for rather than as a gap.
# ---------------------------------------------------------------------------

OMIT_CREDIT: dict[str, dict[str, str]] = {}

# Guidance is matched by OPENING TEXT, never by list position. An earlier draft
# keyed these by index; inserting one bullet at the top of 1c's list silently
# moved the omission set onto the axis-titles-vs-tick-values bullet — the single
# most common deduction on the item, and one of the three the web CAN judge —
# while equivalence.py went on reporting zero gaps, because it read the same
# indices. `resolve_guidance_omissions` now fails loudly instead.
OMIT_GUIDANCE = _generator_table("prompt_omit_guidance")


def resolve_guidance_omissions(item_id: str, guidance: list[str]) -> dict[int, str]:
    """Turn OMIT_GUIDANCE's text keys into indices, or refuse to guess.

    A fragment that matches no bullet, or more than one, means the rubric moved
    under the omission. Silently dropping the wrong bullet is the failure this
    guards, so it raises rather than carrying on.
    """
    out: dict[int, str] = {}
    for frag, why in OMIT_GUIDANCE.get(item_id, {}).items():
        hits = [i for i, g in enumerate(guidance) if g.startswith(frag)]
        if len(hits) != 1:
            raise SystemExit(
                f"{item_id}: OMIT_GUIDANCE fragment {frag!r} matches {len(hits)} "
                f"guidance bullet(s), expected 1. rubric_hN.py changed — re-read "
                f"the bullet and update the fragment or drop the omission."
            )
        out[hits[0]] = why
    return out

OMIT_DEDUCTION: dict[str, dict[str, str]] = {}

# ---------------------------------------------------------------------------
# Scoring divergences: places where the two implementations can return
# DIFFERENT SCORES for the same judgement. These are arithmetic, not prompt
# text, and they live in the .olx `slots=` attributes. `equivalence.py
# --scoring` checks the mechanical part and reports anything not declared here.
#
# `necessary` is the load-bearing field. False means the web COULD express the
# CLI's rule and does not — a candidate fix, to be made and measured on its own,
# never folded into a prompt change.
# ---------------------------------------------------------------------------

SCORING_DIVERGENCES = _generator_value("SCORING_DIVERGENCES")

# Web-only text an item needs because of how its screen is built. Additions,
# not paraphrases: they say something about the web that the rubric cannot
# know, and each is a deviation recorded in EQUIVALENCE.md.
# WHY EACH ENTRY IS WEB-ONLY. Required beside every key in ITEM_NOTES: this
# table is WEB-ONLY BY CONSTRUCTION, and a note earns its place here only by
# saying something that is true of the web and not of paper. A note that could
# be said to BOTH graders is not a side note at all -- it is rubric content,
# and it belongs in `guidance` where both sides get it. Enforced by
# enforcement.check_side_notes_are_side_specific.
ITEM_NOTES_WHY = _generator_table("prompt_notes_why")

ITEM_NOTES = _generator_table("prompt_notes")

# The web stand-in for score.py's graph_bundle. On the CLI, `has_own_graph` is
# judged from an evidence bundle dug out of the .docx (chart XML, embedded
# images, grouped shape text). Here the chart is generated, so the equivalent
# evidence is the data it is generated FROM — blank or non-numeric weeks render
# no graph. build_prompt puts this section last before the response; so do we.
EVIDENCE = _generator_table("prompt_evidence")


# ---------------------------------------------------------------------------
# The checklist. DEVIATION 3 (permitted): the web returns a slot sheet, so the
# the paper scorer's credit_checks + deductions + advisory_note + safety_flag +
# escalate collapse into {checks, feedback}. The sheet is authored in the .olx
# `slots` attribute; this reads it so prompt and schema cannot drift.
#
# DEVIATION 7 (permitted), a consequence of 3: LLMAction appends
# `slotSheet.slotSheetGuidance()` to every slot-sheet prompt, and the schema
# gains a field on some. None of it is in the .olx, and the CLI sends none of it.
# Two parts, only one conditional:
#
#   * ALL 23 items — `studentFacingGuidance()`: spell out the rubric's
#     abbreviations and check keys, because the prose is read by someone who has
#     not seen the rubric. Also restated in the `feedback` and `note` schema
#     descriptions, which are read at a different moment.
#   * The 20 items whose checklist the student SEES — `checklistGuidance()` plus
#     `buildSlotSchema(..., perCheckNotes=true)`, which adds a REQUIRED `note`
#     (capped at two sentences) to every non-computed check and tightens the
#     `evidence` description, because the web DISPLAYS evidence under its check
#     while the CLI keeps it as an internal audit field.
#
#   * The 3 items with showChecks="false" (bmod_h1_q5, bmod_h3_assessment,
#     bmod_h3_improve) — `terseFeedbackGuidance()` instead, capping `feedback`
#     at four sentences. Hiding the checklist removes the structure that was
#     bounding length, and these items are the ones graded most gently.
#
# So all 23 differ from the CLI; none of them by the same amount. Tying the spell-out rule to showChecks would have exempted
# exactly the items whose output is nothing BUT prose.
#
# It is a display difference, not a grading one: `note` is prose shown under its
# own check, is never scored, and no verdict, point value or deduction wording
# depends on it. `equivalence.py --enforcement` is unmoved by it, because that
# audit compares scoring behaviour rather than prompt text — which is precisely
# why this has to be written down rather than left for the audit to catch.
#
# What it DOES affect is output length: 8-11 notes per item, against an
# `interactive` budget of 16384 covering reasoning and output together. Re-run
# `agreement_app.py` before trusting a web-vs-gold figure measured before this.
#
# NOT reproduced here on purpose. This module generates the prompt BODIES that
# live in the .olx; the guidance is appended at runtime, so writing it into the
# generated text would send it twice on the web and would make `--check` demand
# it in files the runtime already supplements.
# ---------------------------------------------------------------------------

def _split_fails(key: str) -> tuple[str, str | None]:
    """`behavior_1~not_active` -> ("behavior_1", "not_active").

    `~` and not `->`, because this project's tag readers match an opening tag as
    `[^>]*>`: a `>` inside an attribute VALUE terminates the match early and every
    attribute after it disappears. That is not hypothetical -- the first version of
    `maps` used `>` and Q4b's `slots=` became invisible, reported as "no slots=
    attribute; nothing to measure". XML permits `>` in a value; these regexes do
    not, so the syntax avoids it.

    A computed rule may NAME the verdict it sets when it fails. Without it the
    verdict is positional, and the two engines read the position differently:
    score.py took the LAST option and agreement.py the SECOND. Every computed check
    in the corpus has exactly two options, so those coincide and the engines agree
    BY LUCK -- the divergence fires on the first three-option computed check, which
    is what Q4b's INSTEAD-OF test needs (met / absent / not_active, where `absent`
    charges B_ONLY_ONE and `not_active` charges the repeatable B_NOT_ACTIVE).

    So: explicit where it is ambiguous, and `check_computed_verdict_is_unambiguous`
    requires it there.
    """
    k, sep, fails = key.partition("~")
    return k.strip(), (fails.strip() or None) if sep else None


def parse_forbid(spec: str) -> list[dict]:
    """Mirror of lo-blocks parseForbid (packages/shared/lib/llm/slotSheet.ts).

    `key:slot=value,slot=value`, rules separated by `|`. The named check FAILS
    only when EVERY condition holds, and like `equals` it is COMPUTED, so it must
    not appear in the prompt's checklist or the response schema.

    Why a primitive rather than one composite slot: `equals` asks whether two
    answers agree and `expect` compares one against an authored value, and
    neither says "fail when A is this AND B is that". Written as a single slot the
    question becomes composite, and the rule this replaces failed four times
    exactly that way — asked one answer at a time it was stable, asked as one
    judgement the model resolved the tension by re-reading which clause was which.
    """
    out = []
    for entry in (spec or "").split("|"):
        entry = entry.strip()
        if not entry:
            continue
        key, _, rest = entry.partition(":")
        key, fails = _split_fails(key)
        conds = []
        for cond in rest.split(","):
            slot, _, value = (x.strip() for x in cond.partition("="))
            if slot and value:
                conds.append({"slot": slot, "value": value})
        if key.strip() and conds:
            rule = {"key": key.strip(), "conds": conds}
            if fails:
                rule["fails"] = fails
            out.append(rule)
    return out


def parse_maps(spec: str | None) -> list[dict]:
    """Mirror of slotSheet.ts:parseMaps.

    `maps="key:pick:value~verdict,...,*~verdict"`, rules separated by `|`. A check
    COMPUTED by mapping one pick's value to a NAMED verdict, which {{corpus:Q4b/p13:modify:42:58:sha=ed0e48693398}}
    `equals`, `expect` and `forbid` cannot express: each of those answers a yes/no
    question about other answers and so produces a check with ONE failing verdict.

    Q4b's `behavior_*` needs two: `absent` for an empty box, charging "you only
    gave one example", and `wrong_kind` for something present that is not an
    activity done instead of the goal behaviour, which is repeatable. Writing that
    as two `forbid` rules on one key fails DANGEROUSLY -- every implementation
    assigns the computed check per rule, so the last wins and an earlier failure is
    overwritten back to satisfied, crediting a wrong entry.

    `*` is the fallback. A pick value with no pair and no fallback leaves the check
    UNMAPPED rather than guessing.
    """
    out = []
    for rule in (spec or "").split("|"):
        parts = [x.strip() for x in _split_keeping_refs(rule)]
        if len(parts) < 3:
            continue
        key, pick, raw = parts[0], parts[1], parts[2]
        if not key or not pick:
            continue
        pairs, fallback = [], None
        for pair in raw.split(","):
            value, sep, verdict = pair.partition("~")
            value, verdict = value.strip(), verdict.strip()
            if not sep or not value or not verdict:
                continue
            if value == "*":
                fallback = verdict
            else:
                pairs.append({"value": value, "verdict": verdict})
        if pairs or fallback:
            r = {"key": key, "pick": pick, "pairs": pairs}
            if fallback:
                r["fallback"] = fallback
            out.append(r)
    return out


def mapped_verdict(rule: dict, answer: str | None) -> str | None:
    """The verdict a `maps` rule assigns to one pick answer, or None."""
    got = (answer or "").strip()
    if not got:
        return None
    for pair in rule.get("pairs") or ():
        if pair["value"] == got:
            return pair["verdict"]
    return rule.get("fallback")


# Colons inside a `{{corpus:...}}` reference belong to the reference, not to the
# colon-delimited grammars below. `slots=` is `name:description:verdicts@weight`
# split on EVERY colon, so a description carrying
# `{{corpus:Q4b/p20:modify:17:40:sha=...}}` shifts every later field and the
# verdict list comes out as `Q4b`/`p20` instead of `met`/`absent`. The generator
# WRITES that attribute from the rubric description, so it misreads its own
# output. Measured over a history whose descriptions carry references: 107 of
# 114 generator states.
#
# Hide the reference's colons for the duration of the split; the grammar is
# unchanged for anything that is not a reference. THREE sites parse this way --
# `parse_equals`, `parse_slots` and `check_scorer_voice_in_labels` -- and
# `slotSheet.ts` parses the same attribute in the engine. All of them need it,
# or the page and the scorer disagree about what a verdict list is.
_REF_COLON_RE = re.compile("[{][{]corpus:[^}]*[}][}]")
_COLON_HOLD = chr(0)


def _split_keeping_refs(entry: str) -> list[str]:
    """Split on the grammar's colons, never on a reference's."""
    held = _REF_COLON_RE.sub(lambda m: m.group(0).replace(":", _COLON_HOLD), entry)
    return [x.replace(_COLON_HOLD, ":") for x in held.split(":")]


def parse_equals(spec: str) -> list[dict]:
    """Mirror of lo-blocks parseEquals (packages/shared/lib/llm/slotSheet.ts).

    A check named here is COMPUTED by the grader from two others, so it must not
    appear in the prompt's checklist: `buildSlotSchema` leaves it out of the
    response schema, and asking for an answer the model cannot return is the same
    incoherence as a criterion with no slot.
    """
    out = []
    for entry in (spec or "").split("|"):
        entry = entry.strip()
        if not entry:
            continue
        parts = [p.strip() for p in _split_keeping_refs(entry)]
        key = parts[0] if parts else ""
        ops = parts[1] if len(parts) > 1 else ""
        lenient = parts[2] if len(parts) > 2 else ""
        left, _, right = (x.strip() for x in (ops.partition(",")))
        if key and left and right:
            out.append({"key": key, "left": left, "right": right,
                        "lenient": [x.strip() for x in lenient.split(",") if x.strip()]})
    return out


# ---------------------------------------------------------------------------
# The verdict vocabulary, read from lo-blocks rather than copied.
#
# A copy here is the thing that drifts, and this one would drift silently: the
# generated "## The checklist to return" section LISTS each check's verdicts, so
# a stale copy writes a prompt describing a schema the app does not send. Same
# reasoning as agreement._ts_literal, same failure it prevents.
# ---------------------------------------------------------------------------
def _slotsheet_ts() -> str:
    try:
        return open(paths.SLOTSHEET_TS).read()
    except OSError as e:                       # pragma: no cover - config error
        raise SystemExit(f"cannot read {paths.SLOTSHEET_TS}: {e}")


def _ts_string_array(name: str) -> list[str]:
    """Lift `export const NAME = [ ... ];` out of slotSheet.ts."""
    m = re.search(rf"export const {name}\s*=\s*\[(.*?)\]", _slotsheet_ts(), re.S)
    if not m:
        raise SystemExit(f"{name} not found in {paths.SLOTSHEET_TS} — "
                         "the verdict vocabulary mirror in olx_prompts is stale")
    return re.findall(r"'([^']+)'", m.group(1))


@functools.lru_cache(maxsize=None)
def default_verdicts() -> list[str]:
    return _ts_string_array("DEFAULT_VERDICTS")


@functools.lru_cache(maxsize=None)
def extra_verdicts() -> list[str]:
    return _ts_string_array("EXTRA_VERDICTS")


def parse_choices(spec: str | None) -> dict[str, list[str]]:
    """Mirror of slotSheet.ts:parseChoices — named sets of categories."""
    out: dict[str, list[str]] = {}
    for grp in (spec or "").split("|"):
        name, _, members = grp.partition(":")
        vals = [v.strip() for v in members.split(",") if v.strip()]
        if name.strip() and vals:
            out[name.strip()] = vals
    return out


def pick_set(segment: str | None) -> str | None:
    """Mirror of slotSheet.ts:parsePick — `pick(operant_type)` -> the set name."""
    m = re.fullmatch(r"pick\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)", (segment or "").strip())
    return m.group(1) if m else None


def parse_expect(spec: str | None) -> list[dict]:
    """Mirror of slotSheet.ts:parseExpect."""
    out = []
    for rule in (spec or "").split("|"):
        parts = [x.strip() for x in _split_keeping_refs(rule)]
        if len(parts) < 2:
            continue
        key, lhs = parts[0], parts[1]
        key, fails = _split_fails(key)
        left, _, value = lhs.partition("=")
        if not key or not left.strip() or not value.strip():
            continue
        rule = {"key": key, "left": left.strip(), "value": value.strip(),
                "lenient": [v.strip() for v in (parts[2] if len(parts) > 2 else "").split(",")
                            if v.strip()]}
        if fails:
            rule["fails"] = fails
        out.append(rule)
    return out


def parse_requires(spec: str | None) -> list[dict]:
    """Mirror of slotSheet.ts:parseRequires — `key:condition[:lenient,...]`.

    The third segment lists verdicts on the CONDITION that establish nothing and
    so deny nothing, exactly as `equals`/`expect` use the word.
    """
    out = []
    for rule in (spec or "").split("|"):
        parts = [x.strip() for x in _split_keeping_refs(rule)]
        if len(parts) >= 2 and parts[0] and parts[1]:
            out.append({"key": parts[0], "cond": parts[1],
                        "lenient": [v.strip() for v in
                                    (parts[2] if len(parts) > 2 else "").split(",")
                                    if v.strip()]})
    return out


def parse_onlyif(spec: str | None) -> list[dict]:
    """Mirror of slotSheet.ts:parseOnlyIf — `key:condition[|key:condition]`.

    Which checks may be CHARGED: the mirror image of `requires`, which decides
    what may be CREDITED. An unknown condition suppresses nothing, so a typo in
    the attribute cannot silently stop a check being charged, and chaining is
    deliberately not transitive.

    Was never parsed here. On PR/NR/PP/NP it is redundant -- `score_oc` returns
    on a failed `demonstrates_type` before the guarded checks are reached, which
    is the same effect by a different route -- but Q4b is scored by the GENERIC
    `score_slots`, where `onlyif="modify_why:modify_stated"` had no
    implementation at all and `modify_why` could be charged on a response that
    never said whether modifying was a good idea.
    """
    out = []
    for rule in (spec or "").split("|"):
        key, _, cond = rule.strip().partition(":")
        if key.strip() and cond.strip():
            out.append({"key": key.strip(), "cond": cond.strip()})
    return out


def parse_counts(spec: str | None) -> list[dict]:
    """Mirror of slotSheet.ts:parseCounts — `key:member,member[|key:...]`.

    The members are DERIVED from the count and deliberately absent from the
    response schema: the model answers how many, and the first n members are met
    and the rest absent. So a consumer that does not read this rule never gives
    the members a verdict at all, and every point they carry goes permanently
    uncharged.

    That was once written here as something that HAD happened, across five items
    and 22 points. It had not. The five items each declare `counts` on their
    RUBRIC item as well as in the sheet, `score_slots` reads the rubric, and the
    members were being scored throughout; the claim was a misdiagnosis, stated
    out loud, that cost 140 calls. The hazard above is real and is why both
    declarations are checked; the incident was not.
    """
    out = []
    for group in (spec or "").split("|"):
        key, _, members = group.strip().partition(":")
        slots = [m.strip() for m in members.split(",") if m.strip()]
        if key.strip() and slots:
            out.append({"key": key.strip(), "slots": slots})
    return out


def count_max(segment: str | None) -> int | None:
    """Mirror of slotSheet.ts:parseCountMax — `count(3)` -> 3."""
    m = re.fullmatch(r"count\(\s*(\d+)\s*\)", (segment or "").strip())
    return int(m.group(1)) if m else None


def resolve_options(segment: str | None, defaults: list[str]) -> list[str]:
    """Mirror of slotSheet.ts:resolveOptions."""
    if count_max(segment) is not None:
        return []                      # a measurement, not a verdict list
    if pick_set(segment) is not None:
        return []                      # a classification, not a verdict list
    tokens = [t.strip() for t in (segment or "").split("/") if t.strip()]
    if not tokens:
        return list(defaults)
    if all(t in extra_verdicts() for t in tokens):
        return default_verdicts() + tokens
    return tokens


def parse_slots(spec: str, defaults: list[str]) -> list[dict]:
    """Mirror of lo-blocks parseSlots (packages/shared/lib/llm/slotSheet.ts)."""
    out = []
    for entry in (spec or "").split("|"):
        entry = entry.strip()
        if not entry:
            continue
        pts = None
        m = re.search(r"@(-?\d+(?:\.\d+)?)\s*$", entry)
        if m:
            pts = float(m.group(1))
            entry = entry[: m.start()].strip()
        parts = [p.strip() for p in _split_keeping_refs(entry)]
        raw_key = parts[0]
        label = parts[1] if len(parts) > 1 and parts[1] else raw_key
        seg = parts[2] if len(parts) > 2 else None
        opts = resolve_options(seg, defaults)
        cmax = count_max(seg)
        picks = pick_set(seg)
        out.append({
            "key": raw_key.lstrip("!").strip(),
            "label": label,
            "options": [o for o in opts if o],
            "gates": raw_key.startswith("!"),
            "pts": pts,
            "count_max": cmax,
            "picks": picks,
        })
    return [s for s in out
            if s["key"] and (s["options"] or s["count_max"] is not None
                             or s["picks"] is not None)]


# What a check means where the rubric's credit list does not already say.
# Keyed by slot key, or by "item:slot key" where the same key means different
# things on different items.
_CADENCE_NOUN = {"daily": "day", "weekly": "week"}

# THE NOTES LIVE IN THE RUBRIC NOW, as `<Frame name="note:KEY">`. What stood here
# was 394 lines of judging prose inside a prompt generator -- course content in
# engine code, which is what this migration removes. The TABLE moved; the
# precedence that reads it did not, and neither did any prompt.
#
# WHY A NOTE IS NOT A `rule`, and why this is a re-point rather than a promotion.
# `rule` is what BOTH graders are told; a note is what a checklist-style grader is
# told where the credit rule does not already say. Folding notes into `rule` would
# put text in front of the paper grader that it has never seen -- a scoring change
# wearing a refactor's clothes. `migration_reference` classifies this move as a
# RE-POINT for exactly that reason: "the check's question is unchanged, only its
# source moves".
#
# SHARED BY NAME, NOT COPIED PER SLOT. Measured: 28 notes cover 102 slot sites and
# `confident` alone is reached by 23, so resolving them into the slots would write
# 102 copies of 28 texts, every copy a place the next edit can miss. A slot that
# needs its own wording carries `note="..."`; one that shares carries `note="@name"`
# -- the two forms `verdicts` already takes.
def _slot_notes() -> dict:
    import rubric_component
    return rubric_component.as_view_notes()


SLOT_NOTES = _slot_notes()


# ---------------------------------------------------------------------------
# Building one prompt.
# ---------------------------------------------------------------------------

_REF = "\x00REF:%s:%s\x00"


def _ref(action: str, target: str, minted: dict) -> str:
    rid = REF_IDS.get(action, {}).get(target)
    if rid is None:
        # A ref the hand-written prompt did not have. Deterministic id so a
        # regeneration produces the same file.
        base = action[: -len("_llm")] if action.endswith("_llm") else action
        rid = "%s_ref_%s" % (base, re.sub(r"^bmod_h\d_", "", target))
        minted[(action, target)] = rid
    return _REF % (rid, target)


# `EQUIVALENCE_DEF` STOOD HERE AND WAS DEAD. It was a byte-identical second
# copy of `generator_source.EQUIVALENCE_DEF` -- 832 characters, read by
# NOTHING in this module, with no check tying the two. The comment above it
# said "two definitions of it would drift", and there were two. A leftover
# from when the table moved to `generator_source`, where `MATCH_DEF` is built
# from the live one.


MATCH_DEF = _generator_table("prompt_match_def")

# Items whose "## Credit components" section lists slots WITHOUT restating their
# rules. The rules still ship — once, in the checklist, which is where the verdict
# is committed and which also carries the verdict vocabulary.
#
# The shipped prompt otherwise prints every slot's `desc` TWICE, once here and
# once in the checklist, where score.py prints it once on a single line carrying
# points, verdicts and rule together. On Q1 that doubling lines up with a
# systematic difference: with identical rule text and byte-identical response
# text, score.py scores 85% while the shipped prompt scores 70-75%, and its
# errors are all UNDER-counts (p9 1 where gold wants 2, p10 0 where gold wants 2,
# p16 0 where gold wants 1, p11 and p19 2 where gold wants 3) — the shape you get
# if a strictness rule stated twice reads as emphasis.
#
# Q1 only, as an experiment. If it pays, the same is worth trying corpus-wide;
# note the opposite result is on record for `cadence_is_daily`, where repeating a
# caveat NEAR THE DECISION POINT was measured as a win. Repetition close to the
# verdict helped there; duplication across two sections may not be the same thing.


def build_web_prompt(item_id: str, minted: dict | None = None) -> str:
    minted = {} if minted is None else minted
    h = HANDOUT[item_id]
    cfg = config(h)
    item = cfg["rubric"].BY_ID[item_id]
    action = ACTION[item_id]
    slots = parse_slots(*_slots_attr(h, action))

    p: list[str] = [WEB_SYSTEM.format(blurb=cfg["blurb"]), ""]
    p.append(f"# Rubric item {item['id']} — {item['max']:g} points\n")
    p.append(f"## Question asked of the student\n{item['question']}\n")

    if item.get("derive_from_criteria"):
        # Same placement rule as the credit-component path below: immediately
        # BEFORE the criteria that use the term. This branch had no such channel,
        # which is why WK1's equivalence rule lived in SLOT_NOTES to begin with.
        if MATCH_DEF.get(item_id):
            p.append(MATCH_DEF[item_id])
        p.append(_criteria_section(
            item, avoidance_scores=bool(item.get("avoidance_scores"))))
    else:
        # Placed HERE, immediately before the components that use the word, and
        # kept to two sentences. Sixteen wording variants of this idea were built
        # and reverted on 2026-08-19, all of them added to the grading guidance
        # forty-odd lines further down; the hypothesis this tests is that the
        # position and the length were the problem rather than the content. The
        # components themselves say "matches 4a" and "matches 4c", so this defines
        # the term at its first use instead of qualifying it later.
        if MATCH_DEF.get(item_id):
            p.append(MATCH_DEF[item_id])
        p.append("## Credit components")
        omitted = OMIT_CREDIT.get(item_id, {})
        for c in item["credit"]:
            if c["what"] in omitted:
                continue
            # Not every component carries points. A reported-only slot exists so a
            # later check can use it, and a gating one costs the whole item rather
            # than a share of it — labelling either "(n pt)" would misstate it.
            worth = (" **GATE**" if c.get("gates")
                     else "" if c.get("pts") is None
                     else f" ({c['pts']:g} pt)")
            # EVERY ITEM GETS THE DESC. This was `if item_id in TERSE_CREDIT`
            # -- Q1 alone got a bare `- \`slot\` (2 pt)` while the other 25 got
            # the description too. Its own comment called it "Q1 only, as an
            # experiment. If it pays, the same is worth trying corpus-wide", and
            # it never was. A MECHANISM MAY NOT VARY BY ITEM: only rubric
            # content may, and an experiment that is never generalised is just
            # an item-dependent engine with a comment on it.
            #
            # IT ALSO MADE Q1 THE ONE ITEM WHOSE TWO SIDES WERE ASKED DIFFERENT
            # QUESTIONS. score.py never implemented it, so on Q1 the web showed
            # a bare checklist while paper showed desc AND rule for every slot
            # -- which is exactly the paper-vs-web comparison Q1 is supposed to
            # supply evidence for.
            p.append(f"- `{c['what']}`{worth}: {c['desc']}")
        p.append("")

    # The deduction table goes to EVERY item, including the two shapes where
    # score.py omits it. DEVIATION: the CLI applies this wording after the call
    # (score.py:compose_feedback); the web has no post-processing step, so the
    # model must see the canonical phrasing to be able to use it.
    p.append("## Deduction codes — the course's canonical wording for each gap")
    omitted_d = OMIT_DEDUCTION.get(item_id, {})
    for d in item["deductions"]:
        if d["code"] in omitted_d:
            continue
        rep = " [repeatable]" if d.get("repeatable") else ""
        p.append(f"- `{d['code']}` (-{d['pts']:g}){rep}: {d['text']}")
    p.append("")

    # An item whose guidance is entirely slot-specific has none left here, and a
    # bare header invites the model to look for instructions that are not there.
    omitted_g = resolve_guidance_omissions(item_id, item["guidance"])
    kept_g = [g for i, g in enumerate(item["guidance"]) if i not in omitted_g]
    if kept_g:
        p.append("## Grading guidance")
        for g in kept_g:
            p.append(f"- {g}")
        p.append("")

    if item.get("exemplars"):
        p.append(
            "## Worked examples\n"
            "Three responses from other students in this cohort, with the verdict sheet "
            "the human grader's marks imply. Match your judgements to these. They are "
            "reference material only — never grade them."
        )
        for ex in item["exemplars"]:
            p.append(f"\n### {ex['label']}")
            p.append(f"Their 4a: {ex['four_a']}")
            p.append(f"Their 4c: {ex['four_c']}")
            p.append(f"Their answer: {ex['response']}")
            p.append("Verdicts: " + ", ".join(f"{k}={v}" for k, v in ex["slots"].items()))
            p.append(f"Why: {ex['note']}")
        p.append("")

    if item_id in ITEM_NOTES:
        p.append(ITEM_NOTES[item_id])

    p.append(_checklist_section(item, slots, item_id, _equals_attr(h, action),
                                _derived_attr(h, action), _counts_attr(h, action),
                                _choices_attr(h, action), _expect_attr(h, action),
                                _forbid_attr(h, action), _maps_attr(h, action)))

    # One component, one <Ref>: the same value twice under two headings reads
    # as two different answers.
    seen: set[str] = set()

    # THE RUBRIC ALREADY DECLARES THIS, so read it instead of hard-coding ids.
    # `UTB_CHOICE = ("Q1",)` was a mechanism list that DISAGREED with the
    # content: `reads_utb_choice` is True on Q1 AND Q2, score.py honours it for
    # both, and the web rendered the section for Q1 only. So the two sides
    # differed on Q2 because a list in the engine contradicted the rubric.
    # RELAX_UTB_AUTHORITY's own comment -- "Q2 carries the same section and
    # would need its own re-measurement" -- reads as confused until you see
    # that Q2 declared the section and was excluded from receiving it.
    if item.get("reads_utb_choice"):
        # "FROM THE LIST" FOR EVERY ITEM. This was `RELAX_UTB_AUTHORITY =
        # {"Q1"}`, so Q1 read "from the list" and everyone else "(authoritative)"
        # -- and that word was already judged WRONG by its own declaration: it
        # was aimed at a comparison the model never sees (score.py's weak hint,
        # right in only 6 of 20 transcriptions) and as prompt text it asserts
        # authority over the JUDGEMENT instead, contradicting `utb_stated`'s own
        # rule that the field does not satisfy the check. It was scoped to Q1
        # "to keep the measurement clean", which is how wording known to be
        # wrong stayed shipped everywhere else.
        #
        # IT ONLY STARTED TO BITE when UTB_CHOICE was derived from the rubric's
        # `reads_utb_choice`: Q2 declares that flag, so Q2 began receiving the
        # section AND the word Q1 had been spared. Fixing one item-gated
        # mechanism activated the next -- which is the argument for the rule
        # rather than against it.
        p.append("## The behavior they chose from the list\n"
                 + "Chosen from the four on the list, before question 1.")
        p.append(_ref(action, "bmod_h1_utb", minted) + "\n")
        seen.add("bmod_h1_utb")

    ctx: list[tuple[str, list[tuple[str, str]]]] = []
    for k in item["context"]:
        fields = [(l, t) for l, t in CONTEXT.get(k, ()) if t not in seen]
        seen.update(t for _, t in fields)
        if fields:
            ctx.append((k, fields))
    if ctx:
        p.append("## Context from this student's other answers (read-only)")
        p.append(
            "Use these only where the rubric requires cross-item consistency. "
            "Do not grade them here."
        )
        for k, fields in ctx:
            p.append(f"\n### {k}")
            for label, target in fields:
                lead = f"{label}: " if label else ""
                p.append(lead + _ref(action, target, minted))
        p.append("")

    if item_id in EVIDENCE:
        note, refs = EVIDENCE[item_id]
        p.append(note)
        for label, target in refs:
            p.append(f"{label}: " + _ref(action, target, minted))
        p.append("")

    p.append(f"## Student response to grade (item {item['id']})")
    # The headings name the on-screen field, and are written so they cannot be
    # read as a claim about what arrived in it. A bare "### How (2)" asserts the
    # box IS a second explanation of how — which is the very thing the check
    # decides. The CLI has no such headings: it sends one undivided block and
    # asserts nothing, so an asserting heading is deviation 1 leaking a
    # judgement into the prompt. Measured on 2a p1, whose third sentence the
    # rubric names as a deduction case: the CLI marks `how_2` unmet, the web
    # marked it met.
    if any(label for label, _ in RESPONSE[item_id]):
        p.append(
            "Each heading is the on-screen field label — what the student was ASKED "
            "to put in that box, never a claim about what they actually wrote. Judge "
            "every box on its contents."
        )
    # Each box's content is DELIMITED, and the response section is CLOSED.
    #
    # A `<Ref>` to an empty box renders to nothing, so a heading was followed by
    # blank space and then by whatever came next. For every box but the last,
    # what came next was the next heading, and the emptiness was legible. For the
    # LAST box there is no next heading: the app appends its own grading guidance
    # after this prompt, so an empty final box put that guidance directly under
    # the field's heading, where it reads as the contents of the box.
    #
    # It was read that way. Measured across three passes of Q6, whose last box is
    # `affect_c2`: where that box was empty the grader quoted "WRITING TO THE
    # STUDENT" -- a heading from the app's appended guidance -- as the student's
    # own sentence, and the student read it back in their feedback. It was never
    # any other slot, on any item, which is the tell: not a model that invents
    # quotations, a model quoting what the prompt showed it. Two attempts to
    # instruct it out of this changed nothing (11 of 15 cell-passes, then 10 of
    # 15), because the instruction contradicted what the page appeared to say.
    #
    # So the fix is here, in what we generate, and it is structural: bounds
    # around every box so an empty one is visibly empty rather than absent, and a
    # terminator so nothing appended after this prompt can fall inside the last
    # box. Both are content-agnostic -- no rule here knows what the guidance that
    # follows says, which is why this does not belong in the app's shared sheet
    # module either.
    for label, target in RESPONSE[item_id]:
        if label:
            p.append(f"\n### Asked for: {label}")
        p.append("[box begins] " + _ref(action, target, minted) + " [box ends]")
    p.append(
        "\n## End of the student response\n"
        "Everything the student wrote is above this line, inside a "
        "`[box begins]`/`[box ends]` pair. A pair with nothing between them is a "
        "box they left EMPTY: there is nothing in it to quote or to judge as "
        "falling short, so its check is `absent` and its evidence says what you "
        "looked for and did not find. Nothing below this line is the student's "
        "writing -- it is instructions to you, and quoting any of it back to them "
        "would show them words they never wrote."
    )

    out = "\n".join(p).rstrip() + "\n"
    # CONVERT, DO NOT RESOLVE. This used to call `expand_prose` here, on the
    # reasoning that `--write` emits what a web grader is sent, so a rubric
    # reference "has to become the words". That put the student's sentences into
    # the .olx -- the file the reference mechanism exists to keep them out of --
    # and it is not what the grader sees anyway: the page is BUILT, and
    # `resolveCorpusRefs.ts` resolves on the way through, exactly as
    # `measured._olx` does when the scorer reads the same file.
    #
    # The old comment warned that leaving a reference would make `--check`
    # compare a reference against the text it stands for and report every item
    # out of date for ever. That is true only while the two sides disagree about
    # the FORM. Converting makes both sides carry the reference, so `--check`
    # compares like with like -- and measured across the rewritten history, the
    # expanding version reported 42 of 113 states out of date for this reason.
    if "[[corpus " in out:
        import corpus_resolve
        out = corpus_resolve.to_olx(out, corpus_resolve.load())
    return out


# Criteria 10 and 11 as the CLI asks them, DERIVED from the web's own wording in
# SLOT_NOTES rather than restated. Three substitutions, each forced by the CLI's
# ANSWER SHEET rather than by any difference in judging, and these are all of
# them:
#   `evidence` -> `behavior`   the CLI's criteria object has no evidence field,
#                              so the web's "put it in `evidence`" would name a
#                              field the model cannot fill
#   `yes`/`no` -> true/false   its criteria are booleans; the web's checklist
#                              answers yes/no
#   drop "one point, and it charges ONLY this:"
#                              the web's checklist slot carries a point value the
#                              model applies; on the CLI the engine computes the
#                              score and the model never sees points
# The list format differs too -- a numbered criteria sheet against a bulleted
# checklist -- so the prefix and trailing period are not the same characters.
# Nothing else differs, and enforcement.check_criteria_prose_has_one_source
# fails the build if a second copy of this prose reappears in score.py.
# Documented in EQUIVALENCE.md.
def _as_criterion(note: str) -> str:
    return (note.replace("put it in `evidence`", "put it in `behavior`")
                .replace("`yes`", "true").replace("`no`", "false"))




# THE LOOP THAT STOOD HERE IS GONE, and the rule it carried is in the rubric.
# Where avoidance framing is declared to COST the item, the note's closing promise
# that criterion 7 "never changes the score" is false -- it was false on BOTH
# sides before anyone noticed, the same defect as in criterion 7 itself but in a
# second place.
#
# It used to be repaired by a python loop that rewrote one note into another at
# import. That DERIVED one piece of course text from another, in engine code,
# which is the shape this migration exists to end -- and it was no better for
# being five lines: the text had moved to the rubric and the rule that edits the
# text had not, which is a half-move. `<Frame name="note:consequence_asserted">`
# now carries the clause as its own segment under `ifDeclared="!avoidance_scores"`,
# the same mechanism `oc_criteria` already uses for the identical suppression on
# criterion 7, and `slot_note()` renders it against the item's conditions.


def _item_conditions(item: dict) -> set:
    """The condition names an item declares, for a frame or a note to select on.

    ONE PLACE, because two callers now need the same set and a second copy of
    "what does this item declare" is how they would come to disagree.
    """
    conditions = set()
    if item.get("avoidance_scores"):
        conditions.add("avoidance_scores")
    cadence = item.get("cadence")
    if cadence:
        conditions.add(f"cadence_{cadence}")
        conditions.add("has_cadence")
    return conditions


def slot_note(item: dict, key: str) -> str | None:
    """This item's note for `key`, or None -- the rubric's note store, resolved.

    ITEM-SCOPED FIRST, THEN SHARED, which is the order the prompt has always used;
    what changed is that the shared one is now rendered against the item's own
    conditions, so a note whose clause belongs only where a condition holds no
    longer needs a hand-written second copy under an item-scoped key.
    """
    import rubric_component
    store = rubric_component.as_view_notes(_item_conditions(item))
    iid = str(item.get("id"))
    return store.get(f"{iid}:{key}") or store.get(key)


# The note keys the CLI renders too. `_criteria_section` composes both from the
# note store -- `_C10_TRIGGER` and `_criterion_11` used to stand here and were
# deleted when the criteria frame stopped restating what the notes already say.
# check_slot_rules_reach_both_prompts exempts these, and it needs a declaration
# rather than a list of its own: its whole premise is that SLOT_NOTES is olx-only,
# which is true of every key EXCEPT the ones named here, and a check carrying its
# own copy of that exception would go stale the moment this list changed.
CLI_CRITERIA_NOTES = ("trigger_behavior", "consequence_asserted")


def _criteria_section(item: dict, trigger_slot: bool = False,
                      consequence_slot: bool = False,
                      avoidance_scores: bool = False) -> str:
    """The criteria prose, for BOTH scorers. score.py:build_prompt calls this.

    THE PROSE IS IN THE RUBRIC NOW, as `<Frame name="oc_criteria">`. What is left
    here is the conditions under which each segment belongs -- engine work --
    against the words themselves, which are course content. Until step 4 this held
    both, and 150 lines of judging prose sat in a module whose job is generating
    prompts.

    It used to be a hand-kept copy of score.py's block -- the docstring said
    "verbatim" -- and it had drifted in three places (criterion 5's example,
    criterion 7's example, criterion 10's WK1 rule). Two copies of a rule are two
    rules, so score.py calls this instead of holding the second one, and
    `check_criteria_prose_has_one_source` fails the build if a copy grows back.

    THE FLAGS ARE FACTS ABOUT THE SHEET, NOT ABOUT THE SIDE, which is why they can
    be conditions at all. The CLI asks `trigger_behavior` where the web asks
    `targets_own_behavior`, and carries `consequence_asserted` as an eleventh
    criterion rather than a checklist slot. Naming the conditions after what the
    sheet ASKS rather than after the scorer keeps the rubric free of any knowledge
    that there are two scorers: a `<Frame>` selects on names, and what a name
    means is never known there.

    THE COMBINATIONS ARE COMPUTED HERE for the same reason. `ifDeclared` takes one
    name, so "a cadence item whose sheet asks trigger_behavior" cannot be written
    as a condition -- but it can be DECLARED as one by the caller that knows both
    halves. The alternative was a conjunction grammar in the frame, which is a
    second expression language for one use.
    """
    import rubric_component
    conditions = set(_item_conditions(item))
    if avoidance_scores:
        conditions.add("avoidance_scores")
    else:
        conditions.discard("avoidance_scores")
    if item.get("cadence"):
        conditions.add("criterion_10_trigger" if trigger_slot
                       else "criterion_10_plain")
    if consequence_slot:
        conditions.add("asks_consequence_asserted")
    # THE TWO CRITERIA THE FRAME DOES NOT RESTATE. Criterion 10's trigger form and
    # criterion 11 are the NOTES `trigger_behavior` and `consequence_asserted`,
    # rendered for a numbered criteria sheet instead of a checklist. The frame
    # carries a placeholder and they are composed here, so the text exists once.
    #
    # WHY THE TRANSFORM MAY LIVE HERE WHEN THE DERIVATION LOOP MAY NOT.
    # `_as_criterion` maps one grader's answer VOCABULARY onto another's --
    # `yes`/`no` become true/false, `evidence` becomes `behavior`. It translates
    # tokens between two sheets. The loop that was deleted EDITED COURSE TEXT,
    # which is a different act, and that is the line.
    #
    # Criterion 11's own conditionality went with it: the clause that is false
    # where avoidance framing scores is a segment of the NOTE now, so
    # `slot_note` returns the right variant and nothing here decides it.
    params = {}
    notes = rubric_component.as_view_notes(_item_conditions(item))
    if trigger_slot and item.get("cadence"):
        params["criterion_10_trigger"] = (
            "10. `trigger_behavior` — " + _as_criterion(notes["trigger_behavior"]))
    if consequence_slot:
        note = slot_note(item, "consequence_asserted") or ""
        params["criterion_11"] = (
            "11. `consequence_asserted` — "
            + _as_criterion(note.replace("one point, and it charges ONLY this: ", ""))
            + ".\n\n")
    return rubric_component.as_view_frame("oc_criteria", conditions=conditions,
                                          params=params)


def _checklist_section(item: dict, slots: list[dict], item_id: str,
                       equals: list[dict] | None = None,
                       derived: list[dict] | None = None,
                       counts: list[dict] | None = None,
                       choices: dict[str, list[str]] | None = None,
                       expect: list[dict] | None = None,
                       forbid: list[dict] | None = None,
                       maps: list[dict] | None = None) -> str:
    """The sheet the model must fill, generated from the .olx `slots` attribute.

    Checks the grader COMPUTES are listed separately and explicitly NOT asked for:
    they are absent from the response schema, so requesting them would be asking
    for something the model cannot supply.
    """
    equals = equals or []
    derived = derived or []
    counts = counts or []
    choices = choices or {}
    expect = expect or []
    computed = {r["key"]: r for r in equals}
    from_page = {r["key"]: r for r in derived}
    # Counted members are derived from the count and are NOT in the response schema.
    # Listing them anyway asked the model for answers it could not return, alongside
    # the count that replaces them — two framings of the same judgement at once.
    counted = {k: cr for cr in counts for k in cr["slots"]}
    # An `expect` key is computed from a classification, so it is out of the
    # response schema exactly as an `equals` key is. Leaving it in the answerable
    # list made the prompt say "answer this" and "DO NOT ANSWER this" about the
    # same check.
    expected = {r["key"]: r for r in expect}
    # A `forbid` key is computed from a COMBINATION of answers, so like `equals`
    # and `expect` it is out of the response schema and must not be asked for.
    forbid = forbid or []
    forbidden_keys = {r["key"]: r for r in forbid}
    # A `maps` key is computed from ONE pick's value, so like the four above it is
    # out of the response schema and must not be asked for. Leaving it in the
    # answerable list made the prompt say "answer this" and, further down, "DO NOT
    # ANSWER this" about the same check -- which the enforcement audit caught the
    # first time this item was generated.
    maps = maps or []
    mapped_keys = {r["key"]: r for r in maps}
    desc = {c["what"]: c["desc"] for c in item["credit"]}
    # `{fail}` is filled with the verdict THIS side offers. The rule text is
    # shared with score.py, whose vocabulary differs — on Q5's example slots the
    # web says `wrong_kind` where the rubric says `not_reason`, and on 1c's
    # legend `incomplete` against `not_described` — so a rule naming one side's
    # token literally is unreadable on the other. It was: the paper scorer was
    # told when to answer `wrong_kind` while being offered met/absent/not_active,
    # so every test was inert and it credited p8's "avoiding going the gym" that
    # the web and CLI both reject. (`not_active` was Q4b's rubric token then;
    # those slots declare `wrong_kind` now, which is why the pair no longer
    # appears anywhere but this note. enforcement.ALIAS does NOT record verdict
    # pairs — it maps slot KEY names, and an earlier version of this comment said
    # otherwise, sending a reader looking for a bridge that does not exist.)
    def _fail_token(slot_key: str) -> str:
        for sl in slots:
            if sl["key"] == slot_key:
                # The item-specific EXTRA verdict, not merely the first non-`met`
                # one: options run [met, absent, <extra>], and `absent` means the
                # box was empty, which is a different finding from wrong-kind.
                opts = [o for o in (sl.get("options") or []) if o not in ("met", "absent")]
                return opts[0] if opts else "absent"
        return "absent"

    def _fill_fail(text: str, own_key: str) -> str:
        """`{fail}` -> this slot's failing verdict, `{fail:other}` -> a sibling's.

        The qualified form is score.fill_fail's counterpart and must stay in step
        with it; the shared `rule` is written once and rendered by both. See the
        docstring there for why a rule ever names a SIBLING's token — Q5's
        `reasons_substantial`, whose whole point is that a thin reason must NOT
        be sent to the example slots' failure token.
        """
        def sub(m: "re.Match") -> str:
            key = m.group(1) or own_key
            if m.group(1) and not any(sl["key"] == key for sl in slots):
                raise KeyError(
                    f"{item['id']}: the `rule` on `{own_key}` names "
                    f"`{{fail:{key}}}`, but `{key}` is not a slot on this sheet")
            return _fail_token(key)
        return _FAIL_RE.sub(sub, text)

    rule = {c["what"]: _fill_fail(c["rule"], c["what"])
            for c in item["credit"] if c.get("rule")}
    lines = [
        "## The checklist to return (`checks`)",
        "Return a verdict for EVERY one of these, in this order, BEFORE you write",
        "`feedback` — a response can fail most of them and still read fluently. Each",
        "check's verdicts are listed with the satisfied one first, unless a note above",
        "says the check reports an identity rather than a judgement.",
        "",
    ]
    for s in slots:
        if (s["key"] in computed or s["key"] in from_page
                or s["key"] in counted or s["key"] in expected
                or s["key"] in forbidden_keys or s["key"] in mapped_keys):
            continue
        # The rubric's own per-component `rule` comes FIRST. Slot-specific judging
        # text belongs in a slot-specific field on BOTH sides, and only the rubric
        # is read by both — SLOT_NOTES is olx-only, so a rule parked there reaches
        # the web and CLI and silently leaves the paper scorer behind. That is
        # exactly what happened to Q4b's five substitution tests.
        note = (rule.get(s["key"])
                or slot_note(item, s["key"])
                or desc.get(s["key"]))
        gate = " **GATE**" if s["gates"] else ""
        if s.get("picks") is not None:
            members = "/".join("`%s`" % o for o in choices.get(s["picks"], []))
            head = (f"- `{s['key']}`{gate} — one of {members} in `refers_to` "
                    f"(WHICH it is, not whether it is right)")
        elif s.get("count_max") is not None:
            head = (f"- `{s['key']}`{gate} — a NUMBER from 0 to {s['count_max']} "
                    f"(how many, not a judgement)")
        else:
            head = f"- `{s['key']}`{gate} — {'/'.join('`%s`' % o for o in s['options'])}"
        lines.append(f"{head}: {note}" if note else head)
    for key, r in mapped_keys.items():
        spec = next((x for x in slots if x["key"] == key), None)
        gate = " **GATE**" if spec and spec["gates"] else ""
        pairs = ", ".join(f"`{c['value']}` makes it `{c['verdict']}`" for c in r["pairs"])
        tail = (f", and anything else makes it `{r['fallback']}`"
                if r.get("fallback") else "")
        lines += ["", f"DO NOT ANSWER `{key}`{gate}. The grader computes it from "
                      f"`{r['pick']}`: {pairs}{tail}. Answer `{r['pick']}` on its own "
                      f"terms -- what the entry IS -- and the verdict follows. It is "
                      f"arithmetic, not a second judgement."]
    for key, r in forbidden_keys.items():
        spec = next((x for x in slots if x["key"] == key), None)
        gate = " **GATE**" if spec and spec["gates"] else ""
        pairs = ", ".join(f"`{c['slot']}` is `{c['value']}`" for c in r["conds"])
        lines += ["", f"DO NOT ANSWER `{key}`{gate}. The grader computes it from the "
                      f"checks above: it FAILS only when ALL of {pairs}, and passes "
                      f"otherwise — including when any of them is left unanswered. "
                      f"Answer each of those on its own terms and do not adjust one to "
                      f"suit another; the combination is arithmetic, not a judgement."]
    for key, r in computed.items():
        spec = next((x for x in slots if x["key"] == key), None)
        gate = " **GATE**" if spec and spec["gates"] else ""
        lines += ["", f"DO NOT ANSWER `{key}`{gate}. The grader computes it by comparing "
                      f"`{r['left']}` with `{r['right']}` — the two checks above that you "
                      f"DO answer. It is not in your schema, and the comparison is not a "
                      f"judgement you can make more accurately than the arithmetic can."
                  + (f" Where either is `{'` or `'.join(r['lenient'])}`, no mismatch is "
                     f"established and nothing is charged." if r["lenient"] else "")]
    for r in expect:
        spec = next((x for x in slots if x["key"] == r["key"]), None)
        gate = " **GATE**" if spec and spec["gates"] else ""
        lines += ["", f"DO NOT ANSWER `{r['key']}`{gate}. The grader computes it: it holds "
                      f"when `{r['left']}` is `{r['value']}`, which is the answer THIS item "
                      f"asks for. Report what you actually see in `{r['left']}` — if it is a "
                      f"different one of the four, say so there and say which in your note; "
                      f"the deduction follows from the arithmetic, not from your judgement "
                      f"about whether it is right."
                  + (f" `{'` or `'.join(r['lenient'])}` establishes nothing and is not charged."
                     if r["lenient"] else "")]
    for cr in counts:
        members = ", ".join(f"`{k}`" for k in cr["slots"])
        lines += ["", f"DO NOT ANSWER {members} individually. Answer `{cr['key']}` — HOW "
                      f"MANY you found — and the grader awards that many of them. Count "
                      f"them the way the guidance above says to, in one judgement over "
                      f"the whole response, rather than deciding each in isolation."]
    for key, r in from_page.items():
        spec = next((x for x in slots if x["key"] == key), None)
        gate = " **GATE**" if spec and spec["gates"] else ""
        if r.get("kind") == "present":
            body = ("The grader reads it off the page: it is satisfied when the "
                    "student has filled the field it names — a closed choice they "
                    "selected, which states the answer more reliably than prose "
                    "restating it would.")
        elif r.get("kind") == "contains":
            # This branch exists because the `else` below was a catch-all that
            # described the CHART. The first `contains` rule authored inherited
            # it, and the generated prompt told the model this keyword check was
            # "satisfied when EVERY week of data is present" -- fluent, confident
            # and false. Kinds are named explicitly here now, and the else says
            # which kinds it speaks for.
            words = " or ".join(f'"{w}"' for w in r.get("words", []))
            body = (f"The grader reads it off the student's own text: satisfied "
                    f"when {words} appears anywhere in the response, including a "
                    f"clear misspelling of it, and `absent` when it does not. It "
                    f"is a word search, not a judgement about whether they "
                    f"understood the idea — that is what the other checks are for.")
        else:                             # plots, complete
            body = ("The grader reads it off the page, using the same code that draws "
                    "the chart: satisfied when EVERY week of data is present, `absent` "
                    "when a week is missing or they hold no numbers at all, and "
                    "`mismatch` when they are the worked example's own numbers rather "
                    "than a record of this student's behaviour. Copied WORDING is still "
                    "yours to judge, on the label checks.")
        lines += ["", f"DO NOT ANSWER `{key}`{gate}. {body} It is not in your schema, "
                      f"and none of it is a judgement — the runtime already knows."]
    if any(s["gates"] for s in slots):
        lines += [
            "",
            "A GATE that is not satisfied is the whole story for this item: report that "
            "finding and do not dress it up with the checks underneath it.",
        ]
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reading and rewriting the .olx.
# ---------------------------------------------------------------------------

_ACTION_RE = r'(<LLMAction\b[^>]*?\bid="%s"[^>]*>)(.*?)(</LLMAction>)'
# Any element that can carry a gradeable slot sheet. `DerivedChecks` carries one
# with no prompt at all, for items whose verdicts are facts about the student's
# fields rather than judgements about their prose.
_SHEET_RE = r'<(?:LLMAction|DerivedChecks)\b[^>]*?\bid="%s"[^>]*?/?>'


def _src(handout: int) -> str:
    with open(OLX % handout) as fh:
        return fh.read()


def _sheet_tag(handout: int, element: str) -> str:
    """The opening tag of whichever element carries `element`'s slot sheet."""
    m = re.search(_SHEET_RE % re.escape(element), _src(handout), re.S)
    if not m:
        raise SystemExit(f"no slot-sheet element id={element} in handout {handout}")
    return m.group(0)


def _slots_attr(handout: int, action: str) -> tuple[str, list[str]]:
    m = re.search(_ACTION_RE % re.escape(action), _src(handout), re.S)
    if m is None:
        tag = _sheet_tag(handout, action)
        spec = re.search(r'\bslots="([^"]*)"', tag)
        verd = re.search(r'\bverdicts="([^"]*)"', tag)
        return ((spec.group(1) if spec else ""),
                ([v.strip() for v in verd.group(1).split(",") if v.strip()]
                 if verd else default_verdicts()))
    if not m:
        raise SystemExit(f"no <LLMAction id={action}> in handout {handout}")
    tag = m.group(1)
    spec = re.search(r'\bslots="([^"]*)"', tag)
    verd = re.search(r'\bverdicts="([^"]*)"', tag)
    defaults = ([v.strip() for v in verd.group(1).split(",") if v.strip()]
                if verd else default_verdicts())
    return (spec.group(1) if spec else ""), defaults


# Mirrors slotSheet.ts:DERIVED_KINDS. A rule naming anything else is dropped on
# both sides, and DerivedChecks then reports the scored check left without a rule.
DERIVED_KINDS = tuple(next(p for p in primitives()["primitives"]
                           if p["attr"] == "derived")["kinds"])


# How close a typed word has to be to count as the course's word. Longer targets
# get a wider budget because a long word has more ways to be fumbled and fewer
# neighbours to be confused with; `trigger` (7) stays at 1 so that `bigger`, two
# edits away, cannot satisfy it.
_FUZZY_MIN_LEN = 9

# At or below this length a target is matched EXACTLY, as a whole token.
#
# Three, not two. Both loose arms stop meaning anything on a short word: a budget
# of 1 against `cat` admits `car`, `can`, `cut` and `bat`, which is one edit in
# three characters and closer to a rhyme than a spelling; and the substring arm
# finds `cat` inside `catalogue` and `education`. Neither is evidence a student
# used the term, so a word this short has to appear as itself.
_EXACT_MAX_LEN = 3

# Up to this length a transposition is NOT a single edit.
#
# A swap moves two characters, which on a four-letter word is half of it -- and
# the words it reaches are not misspellings but other words: a target of `form`
# would be satisfied by `from`. Above four the swapped pair is a smaller share of
# the word and the neighbours it reaches are overwhelmingly typos, so the swap is
# worth its usual discount there and not here.
_NO_SWAP_MAX_LEN = 4


def _edit_within(a: str, b: str, budget: int, allow_swap: bool = True) -> bool:
    """Is `a` within `budget` edits of `b`?

    Optimal string alignment (restricted Damerau-Levenshtein) when `allow_swap`,
    so all four of the ways a word gets mistyped cost the same:

        deletion      antecdent   <- antecedent
        insertion     antecedennt
        substitution  antecidcent
        TRANSPOSITION antecedetn  -- adjacent swap, the commonest slip of all

    Plain Levenshtein charges 2 for that last one. On a long target the budget of
    2 absorbs it by accident, but `trigger` has a budget of 1, so `trigegr` would
    have been rejected while `trigge` was accepted -- an inconsistency with no
    justification, resting on word length rather than on how badly the student
    missed.

    `allow_swap` is false for short targets, where a swap is too large a share of
    the word to read as a typo -- see `_NO_SWAP_MAX_LEN`. The caller decides which
    words get it; this function only counts.

    Bounded and iterative rather than a library call, because this has to exist
    twice -- here, and in slotSheet.ts's `editWithin` -- and the two have to agree
    exactly. A dependency would not have survived that: the browser has no aspell
    and no /usr/share/dict, so the engine the student actually meets could not
    have replicated a dictionary-based correction.
    """
    if abs(len(a) - len(b)) > budget:
        return False
    prev2: list = []
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            best = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
            # The transposition arm: `a[i-2:i]` is `b[j-2:j]` reversed.
            if (allow_swap and i > 1 and j > 1
                    and ca == b[j - 2] and a[i - 2] == cb):
                best = min(best, prev2[j - 2] + 1)
            cur.append(best)
        if min(cur) > budget:
            return False                  # no completion can come back under
        prev2, prev = prev, cur
    return prev[-1] <= budget


def contains_hit(text: str, words) -> tuple:
    """`(course word, what they typed)` if the response uses one, else `(None, None)`.

    A SUBSTRING first, which is what carries inflections -- "antecedents",
    "triggered" -- and is the whole rule for a correctly spelled answer. Only if
    that finds nothing are whole tokens compared against the target within a
    bounded edit distance, which is what carries a misspelling.

    NO DICTIONARY, deliberately. The obvious design -- correct the token if it is
    not a real word -- needs a word list in all three engines, and the browser has
    none. Comparing against the TARGET instead asks a question every engine can
    answer identically, and measurement says the dictionary was never doing any
    work here: the only tokens within edit distance 2 of a target anywhere in the
    corpus are `antecdent`, `antecdents`, `atecedents` and `conequence`, all four
    plainly attempts at the word and none of them English.
    """
    low = (text or "").lower()
    words = [str(w).lower() for w in (words or [])]
    tokens = sorted(set(re.findall(r"[a-z']+", low)))
    for w in words:
        if not w:
            continue
        if len(w) <= _EXACT_MAX_LEN:
            # A one- or two-letter target gets an EXACT whole-token match and
            # nothing else. Both of the other arms break down at this length:
            # one edit out of two characters is most of the word, so `if` would
            # be satisfied by `is`, `in`, `it` and `of`; and the substring arm
            # would find it inside `gift`. Neither is evidence the student used
            # the term.
            if w in tokens:
                return w, w
            continue
        if w in low:
            return w, w
    for w in words:
        # Only words long enough to be missed by accident rather than by
        # coincidence are matched loosely -- four characters and up.
        if not w or len(w) <= _EXACT_MAX_LEN:
            continue
        budget = 2 if len(w) >= _FUZZY_MIN_LEN else 1
        swap = len(w) > _NO_SWAP_MAX_LEN
        for tok in tokens:
            if _edit_within(tok, w, budget, allow_swap=swap):
                return w, tok
    return None, None


def _counts_attr(handout: int, action: str) -> list[dict]:
    """`counts="key:member,member"` — one count standing in for its member checks."""
    m = re.search(r'\bcounts="([^"]*)"', _sheet_tag(handout, action))
    out = []
    for entry in (m.group(1) if m else "").split("|"):
        key, _, members = entry.strip().partition(":")
        ms = [x.strip() for x in members.split(",") if x.strip()]
        if key.strip() and ms:
            out.append({"key": key.strip(), "slots": ms})
    return out


def _derived_attr(handout: int, action: str) -> list[dict]:
    """`derived="key:ref,ref"` — checks read off the page, not asked of the model."""
    # `_sheet_tag`, not `_ACTION_RE`: a DerivedChecks element carries these rules
    # too, and matching only <LLMAction> returned silently empty for those.
    d = re.search(r'\bderived="([^"]*)"', _sheet_tag(handout, action))
    out = []
    for entry in (d.group(1) if d else "").split("|"):
        parts = [p.strip() for p in _split_keeping_refs(entry.strip())]
        key = parts[0] if parts else ""
        kind = parts[1] if len(parts) > 1 else ""
        targets = [t.strip() for t in (parts[2] if len(parts) > 2 else "").split(",")
                   if t.strip()]
        # The fourth segment is numbers to `plots`/`complete` and words to
        # `contains`, so it is read by KIND. Parsing it as a template regardless
        # raised ValueError on the first `contains` rule authored -- loudly, which
        # is the good failure, but it is the third parser of this attribute
        # (slotSheet.ts and agreement.py are the others) and all three have to
        # agree about what the segment means.
        tail = parts[3] if len(parts) > 3 else ""
        words = ([w.strip().lower() for w in tail.split(",") if w.strip()]
                 if kind == "contains" else [])
        template = ([] if kind == "contains" else
                    [[float(n) for n in g.split(",") if n.strip()]
                     for g in tail.split(";") if g.strip()])
        if key and kind in DERIVED_KINDS and targets and (kind != "contains" or words):
            out.append({"key": key, "kind": kind, "targets": targets,
                        "template": template, "words": words})
    return out


def check_scorer_voice_in_labels() -> list[str]:
    """A slot label the STUDENT reads must not address the scorer as "you".

    Slot labels are rendered verbatim by composeSlotFeedback — the model never
    rewrites them — so no amount of prompt guidance can fix one. That makes the
    voice of a label an AUTHORING property, and this the only place it can be
    enforced.

    The rubric's own voice is second-person-to-the-student throughout ("something
    you will physically do", "your unwanted target behavior"), which is correct
    and is why this cannot simply forbid "you". What it forbids is second person
    in the checks that are about the SCORER's own work: `confident` is the
    grader's self-report channel for WEB_SYSTEM rule 8, and it shipped reading
    "Any judgement you were unsure about" on all 23 sheets — telling the student
    they were unsure of a judgement they never made.

    (It was `uncertain`, answered no/yes with `no` as the good state, until the
    verdict standardisation un-inverted it: `met` now means every judgement was
    confident, which is what the rest of the vocabulary already meant by `met`.)
    """
    scorer_facing = ("confident", "uncertain")
    second_person = re.compile(r"\b(you|your|yours|yourself)\b", re.I)
    out = []
    for h in (1, 2, 3):
        src = _src(h)
        for m in re.finditer(r'slots="([^"]*)"', src, re.S):
            for entry in m.group(1).split("|"):
                parts = _split_keeping_refs(entry)
                if len(parts) < 2:
                    continue
                key = parts[0].lstrip("!").strip()
                label = parts[1].split("@")[0]
                if key in scorer_facing and second_person.search(label):
                    out.append(f"H{h}: `{key}` addresses the scorer as \"you\" in a "
                               f"label the student reads: {label!r} — use the first "
                               f"person (\"a judgement I was unsure about\")")
    return out


def check_template_matches_example(handout: int = 3) -> list[str]:
    """The `derived` template must be the worked example's own numbers.

    Those numbers live twice — in `bmod_h3_example_plot`'s data and in the
    attribute the grader compares against — because the plot is authored YAML and
    the attribute is a flat list. A copy is acceptable only if something binds it,
    so this fails `--check`/`--write` the moment they disagree; otherwise the
    grader would quietly stop recognising the example it is meant to catch.
    """
    src = _src(handout)
    m = re.search(r'<ObservablePlot\b[^>]*\bid="bmod_h3_example_plot".*?</ObservablePlot>',
                  src, re.S)
    if not m:
        return ["bmod_h3_example_plot not found; cannot verify the derived template"]
    by_week: dict[str, list[float]] = {}
    for wk, oz in re.findall(r'week:\s*"([^"]+)",\s*oz:\s*(-?[\d.]+)', m.group(0)):
        by_week.setdefault(wk, []).append(float(oz))
    plot = [by_week[k] for k in ("Baseline", "Week 1", "Week 2", "Week 3") if k in by_week]
    for r in _derived_attr(handout, ACTION["1c"]):
        if r["template"] and r["template"] != plot:
            return [f"derived template {r['template']} != example plot {plot}"]
    return []


def _maps_attr(handout: int, action: str) -> list[dict]:
    mp = re.search(r'\bmaps="([^"]*)"', _sheet_tag(handout, action))
    return parse_maps(mp.group(1) if mp else "")


def _forbid_attr(handout: int, action: str) -> list[dict]:
    fb = re.search(r'\bforbid="([^"]*)"', _sheet_tag(handout, action))
    return parse_forbid(fb.group(1) if fb else "")


def _equals_attr(handout: int, action: str) -> list[dict]:
    eq = re.search(r'\bequals="([^"]*)"', _sheet_tag(handout, action))
    return parse_equals(eq.group(1) if eq else "")


def _choices_attr(handout: int, action: str) -> dict[str, list[str]]:
    ch = re.search(r'\bchoices="([^"]*)"', _sheet_tag(handout, action))
    return parse_choices(ch.group(1) if ch else "")


def _expect_attr(handout: int, action: str) -> list[dict]:
    ex = re.search(r'\bexpect="([^"]*)"', _sheet_tag(handout, action))
    return parse_expect(ex.group(1) if ex else "")


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;")


def _to_xml(body: str) -> str:
    """Escape the prose, then expand the ref placeholders into <Ref> elements."""
    out = _escape(body)
    return re.sub(
        r"\x00REF:([^:]+):([^\x00]+)\x00",
        lambda m: '<Ref id="%s" target="%s" />' % (m.group(1), m.group(2)),
        out,
    )


def forbid_attr_for(item_id: str) -> str | None:
    """The `forbid=` attribute value for an item, from the RUBRIC declaration.

    The conjunction used to exist three times -- twice in score.py and once as a
    hand-authored attribute in the .olx -- so the rubric declares it and this
    generates the attribute. Format is parse_forbid's: `key:slot=value,...`,
    rules joined by `|`.
    """
    item = config(HANDOUT[item_id])["rubric"].BY_ID[item_id]
    rules = item.get("forbid") or []
    if not rules:
        return None
    return "|".join(
        "%s:%s" % (r["key"], ",".join(f"{c['slot']}={c['value']}" for c in r["conds"]))
        for r in rules)


def expect_attr_for(item_id: str) -> str | None:
    """The `expect=` attribute value for an item, from the RUBRIC declaration.

    Format is parse_expect's: `key:left=value:lenient,lenient`, rules joined by
    `|`. Only WK1 declares one; the four `demonstrates_type` rules stay authored
    in the .olx because the CLI reaches that fact through `expected_type` and
    REQUIRED_MOVE, so declaring them here would be a second source for one fact.
    """
    item = config(HANDOUT[item_id])["rubric"].BY_ID[item_id]
    rules = item.get("expect") or []
    if not rules:
        return None
    out = []
    for r in rules:
        spec = "%s:%s=%s" % (r["key"], r["left"], r["value"])
        if r.get("lenient"):
            spec += ":" + ",".join(r["lenient"])
        out.append(spec)
    return "|".join(out)


# Attributes the GENERATOR owns, each from a rubric declaration. An item without
# the declaration keeps whatever the .olx authors; an item WITH one whose tag has
# no such attribute is a hard error, because the rule would then reach score.py
# and not the web -- the asymmetry these conversions exist to remove.
def maps_attr_for(item_id: str) -> str | None:
    """The `maps=` attribute value for an item, from the RUBRIC declaration.

    Format is parse_maps's: `key:pick:value~verdict,...`, `*` last as the fallback,
    rules joined by `|`.
    """
    item = config(HANDOUT[item_id])["rubric"].BY_ID[item_id]
    rules = item.get("maps") or []
    if not rules:
        return None
    out = []
    for r in rules:
        pairs = [f"{c['value']}~{c['verdict']}" for c in r["pairs"]]
        if r.get("fallback"):
            pairs.append(f"*~{r['fallback']}")
        out.append("%s:%s:%s" % (r["key"], r["pick"], ",".join(pairs)))
    return "|".join(out)


def _pick_verdicts(item_id: str, slot: str) -> list[str] | None:
    """A pick slot's option list, from the RUBRIC. None means NOT DECLARED.

    Two homes, because the corpus has two: an item's own `credit` entry, and the
    rubric module's `SLOT_OPTIONS` table, which is where handout 2 keeps
    `restriction_authored`, `trigger_expects`, `restricts`, `trigger_behavior`
    and `stimulus_move`.

    RETURNING None RATHER THAN [] IS THE WHOLE CONTRACT. `named_type` and
    `observed_type` -- twelve slot-instances across the cadence items -- have NO
    rubric source at all: their sets `operant_or_unclear` and `operant_or_none`
    exist only in the .olx. A generator that read "not declared" as "declared
    empty" would DELETE them from the attribute and break every cadence item.
    The same None/[] conflation produced Q6's phantom STALE CELLS and a false
    refusal in `probe.control_gate` on the same day.
    """
    rub = config(HANDOUT[item_id])["rubric"]
    for c in (rub.BY_ID.get(item_id) or {}).get("credit") or []:
        if c["what"] == slot and c.get("verdicts"):
            return list(c["verdicts"])
    so = getattr(rub, "SLOT_OPTIONS", {}) or {}
    if slot in so:
        return list(so[slot])
    return None


def choices_attr_for(item_id: str) -> str | None:
    """The `choices=` attribute value, from the rubric where a source exists.

    WHY THIS IS GENERATED NOW. It was hand-authored, and `slots=` binds a slot to
    a set (`b1_basis:...:pick(instead_of_basis)`) while `choices=` lists the set's
    members. So adding a sixth value to a rubric pick reached the generated RULE
    PROSE and never the ENUM: on 2026-09-08 Q4b shipped a rule describing
    `a_listed_trigger` while the checklist head still read "one of
    activity/consequence/goal_behaviour/not_doing/none". The grader was told about
    an option it was forbidden to pick, 32 probe calls measured a menu that did
    not contain the thing under test, and nothing complained. Designed text
    reaching the prompt but not the attribute is the same class as an
    unregenerated .olx or a stale idmap.

    PRESERVES WHAT IT CANNOT SOURCE. A set whose slots have no rubric declaration
    keeps the .olx's own membership verbatim -- see `_pick_verdicts`. Order is
    the .olx's for preserved sets and the rubric's for generated ones, so a
    switch-on rewrites only the sets that actually differ.
    """
    h = HANDOUT[item_id]
    # ACTION is the map the other generators use; _sheet_tag raises SystemExit
    # (NOT an Exception) for an unknown id, so the guard has to be BaseException.
    action = ACTION.get(item_id)
    if not action:
        return None
    try:
        tag = _sheet_tag(h, action)
    except BaseException:
        return None
    have = _choices_attr(h, action)
    if not have:
        return None
    import re as _re
    ms = _re.search(r'\bslots="([^"]*)"', tag)
    if not ms:
        return None
    # set name -> the slots that pick from it
    users: dict[str, list[str]] = {}
    for part in ms.group(1).split("|"):
        m = _re.search(r"pick\(([^)]+)\)", part)
        if m:
            users.setdefault(m.group(1), []).append(_split_keeping_refs(part)[0])
    out = []
    # A SET `slots=` USES BUT `choices=` LACKS IS A NEW GROUP, and it has to be
    # ADDED, not merely regenerated. This loop read `have.items()` -- the sets
    # the .olx ALREADY declares -- so a pick group introduced in the rubric could
    # never reach the attribute at all. Found 2026-09-08 shipping Q4b's
    # `pick(points_at)`: `slots=` gained it on the first write and `choices=`
    # never would have, so the two new slots had no menu, no verdict could
    # satisfy them, and `check_web_scorer_exercises_its_sheet` correctly reported
    # that no synthetic sheet reached Q4b's maximum (2.0 of 5.0) -- which blocked
    # every probe on the handout, not just Q4b's.
    #
    # That is the same defect this function was written to end, one level up:
    # designed text reaching the prompt but not the attribute. It caught a new
    # VALUE in an existing set and was blind to a new SET.
    order = list(have) + [g for g in users if g not in have]
    for setname in order:
        members = have.get(setname, [])
        sourced = [v for v in (_pick_verdicts(item_id, s)
                               for s in users.get(setname, [])) if v]
        if not users.get(setname):
            # NOTHING PICKS FROM THIS SET. Not the same as "declared nowhere":
            # `named_type`/`observed_type` have no rubric source but ARE used by
            # slots, and dropping those would break every cadence item. A set
            # with no users at all is a leftover -- reverting Q4b's pointing
            # slots on 2026-09-08 stranded `points_at:neither,first,second` in
            # the attribute with no slot able to pick from it.
            continue
        if not sourced:
            if not members:
                # A new set with no rubric source: refuse rather than invent a
                # menu. `_pick_verdicts` returning None means NOT DECLARED, and
                # guessing an option list would put a verdict the designer never
                # wrote into a scored prompt.
                raise SystemExit(
                    f"{item_id}: `slots=` binds {users[setname]} to choice-set "
                    f"'{setname}', which the .olx does not declare and the "
                    f"rubric does not source. Declare its options in the slot's "
                    f"`credit` verdicts or in SLOT_OPTIONS; the generator will "
                    f"not invent a menu.")
            out.append(f"{setname}:{','.join(members)}")     # preserved verbatim
            continue
        # ORDER IS PART OF THE DESIGN. An earlier version of this function
        # emitted the .olx's order whenever the SET matched, to avoid
        # moving four cadence prompt_shas over a cosmetic reordering. That
        # kept a second source of truth alive for one fact. The right fix
        # was the other direction: rubric_h2.SLOT_OPTIONS now DECLARES the
        # order that ships (`restriction_authored` was the only slot that
        # differed), so the rubric governs and this exception is gone.
        if any(sorted(x) != sorted(sourced[0]) for x in sourced):
            # Two slots share a set and their rubric lists disagree: refuse
            # rather than pick one, because either choice silently rewrites the
            # other slot's menu.
            raise SystemExit(
                f"{item_id}: slots {users[setname]} share choice-set "
                f"'{setname}' but declare different verdicts in the rubric: "
                f"{sourced}. Reconcile them; the generator will not choose.")
        # Membership really differs: keep the .olx's order for members that
        # survive and append the new ones in rubric order, so the diff is the
        # change and nothing else.
        want = sourced[0]
        kept = [m for m in members if m in want]
        added = [v for v in want if v not in members]
        out.append(f"{setname}:{','.join(kept + added)}")
    return "|".join(out)


def derived_attr_for(item_id: str) -> str | None:
    """`derived="key:kind:fields:payload"`, '|'-separated, from the RUBRIC.

    THE TWELFTH AND LAST hand-authored sheet attribute, generated 2026-09-08.
    `fields` is the name `agreement.apply_computed` already reads
    (`rule["fields"]`), so there is one vocabulary for one fact.

    THE COMMENT ON Q4a/Q4c'S ENTRIES -- "No fields here, unlike the OLX:
    score.py is handed the assembled response text" -- describes score.py's
    BEHAVIOUR and is not a prohibition on the key. VERIFIED before adopting it:
    score.py's derived handler reads only `kind` and `words`, never `fields`, so
    the key is inert on that path; and it cannot compute `complete` at all, its
    DERIVED_KINDS_IMPLEMENTED covering `contains` only.

    Payload by kind: the word list for `contains`; for `complete`/`plots` the
    WORKED EXAMPLE'S data, rows joined by ';' and values by ',', which
    `apply_computed` compares against to answer `mismatch` when a student
    graphed the example instead of their own weeks.

    A rule with no `fields` emits nothing rather than a malformed clause: there
    is no box list to tell the web about, and inventing one would put a field id
    into a prompt on a guess.
    """
    rules = config(HANDOUT[item_id])["rubric"].BY_ID[item_id].get("derived") or []
    out = []
    for r in rules:
        fields = r.get("fields")
        if not fields:
            continue
        if r["kind"] == "contains":
            payload = ",".join(r["words"])
        elif r["kind"] in ("complete", "plots"):
            payload = ";".join(
                ",".join(str(int(v)) if float(v) == int(v) else str(v)
                         for v in row)
                for row in r.get("template") or [])
        else:
            continue
        out.append(f"{r['key']}:{r['kind']}:{','.join(fields)}:{payload}")
    return "|".join(out) or None


def slots_attr_for(item_id: str) -> str | None:
    """`slots="[!]key:label[:seg][@pts]"`, '|'-separated, from the RUBRIC.

    THE LAST LARGE HAND-AUTHORED ATTRIBUTE, generated 2026-09-08. It reads
    `rubric.SLOT_SPEC`, adopted from the .olx that day: 217 clauses over 23
    items, 159 of which carried an option list the rubric could not supply, so
    the adoption MOVED the slot sheet's primary definition into the rubric
    rather than reconciling two copies of it. Emission mirrors `parse_slots`
    exactly, and the parse was proved to round-trip losslessly on all 23 items
    before a line was written, which is why switching this on moved no
    prompt_sha.
    """
    spec = getattr(config(HANDOUT[item_id])["rubric"], "SLOT_SPEC", {}) or {}
    rules = spec.get(item_id)
    if not rules:
        return None
    out = []
    for f in rules:
        clause = ("!" if f.get("gate") else "") + f["key"]
        if f.get("label") or f.get("seg") is not None:
            clause += ":" + (f.get("label") or "")
        if f.get("seg") is not None:
            clause += ":" + f["seg"]
        if f.get("pts") is not None:
            clause += "@" + str(f["pts"])
        out.append(clause)
    return "|".join(out)


def equals_attr_for(item_id: str) -> str | None:
    """`equals="key:left,right:lenient,..."`, '|'-separated, from the RUBRIC."""
    rules = config(HANDOUT[item_id])["rubric"].BY_ID[item_id].get("equals") or []
    if not rules:
        return None
    out = []
    for r in rules:
        spec = f"{r['key']}:{r['left']},{r['right']}"
        if r.get("lenient"):
            spec += ":" + ",".join(r["lenient"])
        out.append(spec)
    return "|".join(out)


def onlyif_attr_for(item_id: str) -> str | None:
    """`onlyif="key:cond"`, '|'-separated, from the RUBRIC."""
    rules = config(HANDOUT[item_id])["rubric"].BY_ID[item_id].get("onlyif") or []
    if not rules:
        return None
    return "|".join(f"{r['key']}:{r['cond']}" for r in rules)


def max_attr_for(item_id: str) -> str | None:
    """`max="N"` from the RUBRIC -- but ONLY where the .olx already carries it.

    THE VALUE IS GENERATED AND THE PRESENCE IS PRESERVED, which inverts this
    module's usual rule and is deliberate. The rubric declares `max` for all 23
    items; the .olx carries the attribute on 11 and the app computes the rest
    from the slots' points. Emitting it everywhere would ADD an attribute to
    twelve items, moving twelve prompt_shas and invalidating twelve items'
    measurements for ZERO behavioural change. Checked first: where it does ship,
    the value matches the rubric on all 11, so this is a no-op.
    """
    import re as _re

    action = ACTION.get(item_id)
    if not action:
        return None
    try:
        tag = _sheet_tag(HANDOUT[item_id], action)
    except BaseException:
        return None
    if not _re.search(r'\bmax="', tag):
        return None                    # absent by authoring: leave it absent
    m = config(HANDOUT[item_id])["rubric"].BY_ID[item_id].get("max")
    if m is None:
        return None
    return str(int(m)) if float(m) == int(m) else str(m)


def counts_attr_for(item_id: str) -> str | None:
    """`counts="key:slotA,slotB,..."`, '|'-separated, from the RUBRIC.

    STAGE 1 OF MAKING EVERY SHEET ATTRIBUTE GENERATED, 2026-09-08, on the user's
    instruction that a design change must never need a hand edit to the .olx.
    Twelve attributes exist; four were generated (forbid, expect, maps, choices)
    and eight were hand-authored. `counts`, `requires` and `cover` are the three
    whose rubric declaration and .olx attribute cover EXACTLY the same items, so
    they convert with no reconciliation and no prompt change.
    """
    rules = config(HANDOUT[item_id])["rubric"].BY_ID[item_id].get("counts") or []
    if not rules:
        return None
    return "|".join(f"{r['key']}:{','.join(r['slots'])}" for r in rules)


def requires_attr_for(item_id: str) -> str | None:
    """`requires="key:cond:lenient,..."`, '|'-separated, from the RUBRIC."""
    rules = config(HANDOUT[item_id])["rubric"].BY_ID[item_id].get("requires") or []
    if not rules:
        return None
    out = []
    for r in rules:
        spec = f"{r['key']}:{r['cond']}"
        if r.get("lenient"):
            spec += ":" + ",".join(r["lenient"])
        out.append(spec)
    return "|".join(out)


def cover_attr_for(item_id: str) -> str | None:
    """`cover="keyA,keyB:labelA,labelB"`, '|'-separated, from the RUBRIC.

    The rubric entry also carries `of` and `verdicts`; neither belongs in this
    attribute -- `of` is documentation and `verdicts` reaches the grader through
    `slots=`/`choices=`. Emitting them would invent an attribute the parser does
    not read, so they are deliberately dropped here and NOT lost: `parse_cover`
    reads only keys and labels.
    """
    rules = config(HANDOUT[item_id])["rubric"].BY_ID[item_id].get("cover") or []
    if not rules:
        return None
    return "|".join(f"{','.join(r['keys'])}:{','.join(r['labels'])}" for r in rules)


def free_attr_for(item_id: str) -> str | None:
    """`free="slot:verdict,verdict|slot:verdict"` -- verdicts that cost NOTHING.

    THE TWO ENGINES DEFAULT IN OPPOSITE DIRECTIONS and this is what removes the
    default. lo-blocks' `isSatisfied` credits only the satisfying verdict and
    fails everything else, so the web charges a slot's whole points for any
    third verdict; the paper ledger charges only what a deduction CODE names, so
    the same verdict costs nothing there. They agree only while the two
    enumerations happen to be complements, which nothing enforces -- Q1's
    `utb_stated` went 62 observations before the model answered `unclear` and
    exposed it.

    DECLARED, NEVER INFERRED. The obvious derivation -- "a verdict with no code
    is free" -- is wrong: a code keyed on the counterpart name reads as missing.
    Q4a's sheet answers `wrong_kind` where its rubric code says
    `not_antecedent`, the same judgement under two names, and inferring would
    forgive a real 2-point failure on every antecedent slot. So the rubric says
    `free` beside `codes` and this only transcribes it.
    """
    item = config(HANDOUT[item_id])["rubric"].BY_ID[item_id]
    out = []
    for c in item.get("credit") or []:
        free = [v for v in (c.get("free") or []) if v]
        if free:
            out.append(f"{c['what']}:{','.join(free)}")
    return "|".join(out) or None


def parse_free(spec: str) -> dict[str, list[str]]:
    """`slot:verdict,verdict|slot:verdict` -> {slot: [verdict, ...]}."""
    out: dict[str, list[str]] = {}
    for entry in (spec or "").split("|"):
        entry = entry.strip()
        if not entry or ":" not in entry:
            continue
        key, _, vs = entry.partition(":")
        vals = [v.strip() for v in vs.split(",") if v.strip()]
        if key.strip() and vals:
            out[key.strip()] = vals
    return out


def rubric_def_for(item_id: str) -> str | None:
    """`rubricDef="Q1"` -- the rubric entry this generated sheet is a projection OF.

    The sheet's slots, verdicts and codes are one reading of a rubric item; the
    rubric component carries another. Naming the source lets a second consumer
    derive its own projection instead of restating this one, which is the only
    way the two cannot drift. `LLMAction` accepts the attribute and IGNORES it
    until content sets it -- the engine deliberately landed a stage early,
    because the engine and the content version separately and no step can land in
    both at once. This is the content half.

    THE VALUE IS THE ITEM ID, because that is already the rubric entry's identity:
    the component writes `<Item scores="Q1">`, with no separate element id to
    name. `check_every_rubric_def_names_a_rubric_item` holds the two together, so
    the attribute cannot quietly point at nothing -- which is exactly what E44
    cost when `expect=` outlived the rule it named.

    Every item in ACTION has a rubric entry, so this never returns None in
    practice; the signature matches its siblings, which may.
    """
    return item_id


GENERATED_ATTRS = (("rubricDef", rubric_def_for),
                   ("free", free_attr_for), ("forbid", forbid_attr_for), ("expect", expect_attr_for),
                   ("maps", maps_attr_for),
                   ("choices", choices_attr_for),
                   ("counts", counts_attr_for),
                   ("requires", requires_attr_for),
                   ("cover", cover_attr_for),
                   ("equals", equals_attr_for),
                   ("onlyif", onlyif_attr_for),
                   ("max", max_attr_for),
                   ("slots", slots_attr_for),
                   ("derived", derived_attr_for))


def render(handout: int) -> tuple[str, dict, list[str]]:
    """The .olx source with every generated prompt body substituted in.

    Returns (src, minted, cleared). `cleared` names the generated attributes
    EMPTIED because their rubric declaration has gone -- subgoal E44. It is a
    return value rather than a print because `--check` and `--diff` call this
    too, and a clear is a real difference they should report as one.
    """
    src = _src(handout)
    minted: dict = {}
    # Attributes emptied because their declaration has gone -- reported by
    # the caller so a silent clear cannot look like a no-op. See E44.
    cleared: list[str] = []
    for item_id, action in ACTION.items():
        if HANDOUT[item_id] != handout:
            continue
        body = _to_xml(build_web_prompt(item_id, minted))
        pat = re.compile(_ACTION_RE % re.escape(action), re.S)
        if not pat.search(src):
            raise SystemExit(f"no <LLMAction id={action}> in handout {handout}")
        # The open tag is group(1) and carries the sheet's attributes. Only
        # `forbid` is generated from the rubric; the rest stay as authored, and
        # the VALUE alone is swapped so the tag's own line breaks and indentation
        # are untouched. A declaration with nowhere to land is a hard error: the
        # rule would silently reach score.py and not the web, which is the exact
        # asymmetry this conversion exists to remove.
        wants = [(name, fn(item_id)) for name, fn in GENERATED_ATTRS]

        def _sub(m: re.Match) -> str:
            head = m.group(1)
            for name, want in wants:
                pat_attr = re.compile(r'%s="([^"]*)"' % name)
                if want is None:
                    # SUBGOAL E44's writer half. This used to `continue`, which
                    # LEFT an attribute the generator owns pointing at a rule
                    # that no longer exists. Reverting the cadence edit on
                    # 2026-09-05 removed EXPECT for three items and left their
                    # `expect=` behind, so two slots were computed from picks
                    # that had been deleted -- never satisfiable, the items could
                    # not reach their own maximum, and `--check` called the file
                    # up to date throughout because the generator does not own
                    # what it did not write. Eight queued sweeps woke into that
                    # tree and exited without spending a call, which was luck.
                    #
                    # NOW IT CLEARS, but only where the attribute is GENERATED
                    # rather than hand-authored, and that distinction is not
                    # guessable from the file -- it is declared, in
                    # enforcement.HAND_AUTHORED_ATTRS, with a reason per entry.
                    # The four `demonstrates_type` rules on PR/NR/PP/NP are the
                    # standing case: they are authored here on purpose because
                    # the CLI reaches that fact through REQUIRED_MOVE, and
                    # clearing them would silently drop a rule from the web.
                    #
                    # Emptied rather than DELETED: the writer's other arm makes
                    # a missing attribute a hard error when a declaration exists,
                    # so leaving `name=""` keeps the slot for the next
                    # declaration instead of demanding it be re-added by hand.
                    import enforcement as _ENF
                    if (item_id, name) in _ENF.HAND_AUTHORED_ATTRS:
                        continue
                    cur = pat_attr.search(head)
                    if cur is None or not cur.group(1).strip():
                        continue
                    cleared.append(f"{item_id}.{name}")
                    head = pat_attr.sub(lambda _: '%s=""' % name, head, count=1)
                    continue
                if not pat_attr.search(head):
                    raise SystemExit(
                        f"{item_id} declares `{name}` in the rubric but "
                        f"<LLMAction id={action}> has no {name}= attribute to write "
                        f"it into -- add the attribute (any value) so the generator "
                        f"can own it")
                head = pat_attr.sub(lambda _: '%s="%s"' % (name, want), head, count=1)
            return head + "\n" + body + "      " + m.group(3)

        src = pat.sub(_sub, src, count=1)
    return src, minted, cleared


_REF_TAG = re.compile(r'<Ref\b[^>]*?id="([^"]+)"[^>]*?target="([^"]+)"[^>]*?/>')


def ref_delta(handout: int) -> tuple[list[str], list[str], list[str]]:
    """(dropped, added, duplicated) <Ref> ids between the file and the generation.

    A dropped ref is context the hand-written prompt passed and the rubric does
    not ask for; every one belongs in EQUIVALENCE.md's deviation list.
    """
    old = dict(_REF_TAG.findall(_src(handout)))
    new_src, _, _ = render(handout)
    new_pairs = _REF_TAG.findall(new_src)
    new = dict(new_pairs)
    dupes = [rid for rid in new if [r for r, _ in new_pairs].count(rid) > 1]
    return (
        sorted(f"{rid} -> {tgt}" for rid, tgt in old.items() if rid not in new),
        sorted(f"{rid} -> {tgt}" for rid, tgt in new.items() if rid not in old),
        sorted(set(dupes)),
    )


def _measurements_in_flight() -> list[str]:
    """Command lines of any harness process that is currently scoring cells.

    `agreement.py` reads the generated .olx per call, so rewriting it under a
    running one changes the prompt mid-measurement -- the recorded incident that
    split handout 3's measurement and cost three items.

    THE OTHER TWO DO NOT READ IT PER CALL, and the previous version of this
    docstring said "both harnesses" do, which was wrong in a way that mattered:
    it made the omission of `agreement_app.py` from the match look like an
    oversight rather than a fact about what that harness reads. `agreement_app.py`
    is served from a DUMPED idmap and validates it once at startup, so a later
    rewrite cannot change its prompts; `score.py` builds from the rubric. They
    are matched anyway -- see SWEEPING below -- because both still read gold,
    exclusions and the era fingerprint from files a generator or a self-test can
    move under them.

    Matched by module name rather than by a lock file: a lock is only as good as
    the last process to release it, and these runs are killed by hand often
    enough that a stale lock would train everyone to pass --force.
    """
    import subprocess

    try:
        out = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True,
                             text=True, check=False).stdout
    except Exception:                                   # pragma: no cover
        return []
    mine = str(os.getpid())
    busy = []
    SHELLS = {"bash", "sh", "dash", "zsh", "ksh", "-bash", "fish"}
    # SWEEPING: all three scorers. `score.py` was absent, so a paper sweep was
    # invisible to every caller of this guard.
    HARNESS = {"agreement.py", "agreement_app.py", "score.py"}
    SHELLS = {"bash", "sh", "dash", "zsh", "ksh", "-bash", "fish"}

    for line in out.splitlines()[1:]:
        pid, _, args = line.strip().partition(" ")
        if pid == mine or "olx_prompts" in args:
            continue
        parts = args.split()
        if not parts:
            continue
        # A SHELL whose command line merely MENTIONS a sweep is not a sweep.
        # Substring matching could not tell the two apart, and the shells that
        # wait for a sweep to finish necessarily quote its command line -- so
        # every watcher looked like a measurement in flight and the generator
        # refused to write with nothing running. That trains everyone to pass
        # --force, which is exactly what this guard exists to prevent.
        if os.path.basename(parts[0]) in SHELLS:
            continue
        # argv[0] is not required to be python: a sweep is normally launched
        # through `timeout`, and demanding python at the front would let a real
        # run go undetected -- a false negative here corrupts a measurement,
        # which is far worse than a false positive.
        idx = next((i for i, tok in enumerate(parts)
                    if os.path.basename(tok) in HARNESS), None)
        # `--items` OR `--item`: agreement.py takes the plural and
        # agreement_app.py the singular, so demanding the plural made every WEB
        # sweep invisible to this guard. score.py takes neither -- it sweeps a
        # whole handout -- so a --handout run counts as well.
        if idx is None or not ({"--items", "--item", "--handout"} & set(parts)):
            continue
        if not any(os.path.basename(t).startswith("python") for t in parts[:idx]):
            continue
        # THE MIRROR OF THE SELF-TEST GUARD, and the direction that was never
        # paid for. A process is machine-wide, so this matched a sweep ANYWHERE:
        # a run here refused every self-test in an isolated copy -- a migration
        # dry run, a scratch worktree -- which is what such a copy does all day,
        # and the self-test is how a disposition is shown to still fire.
        #
        # `_selftest_source_root` resolves any process's script, absolute if it
        # said so and otherwise against its own cwd; the name is about where it
        # was first needed rather than what it does. UNDETERMINABLE STAYS
        # REFUSED: if /proc is unreadable the answer is None and the caller
        # treats it as ours, because scoring cells against a rule nobody wrote
        # is far worse than a wait.
        root = _selftest_source_root(pid, parts[idx])
        if root is not None and root != _OUR_ROOT:
            continue        # a sweep on ANOTHER tree cannot read our source
        busy.append(" ".join(parts[:9])
                    + ("" if root else "   [tree undetermined]"))
    return busy


def _selftest_in_flight() -> list[str]:
    """Command lines of any audit SELF-TEST currently running.

    The mirror of `_measurements_in_flight`, and it closes the other half of the
    same hazard. `equivalence.py --enforcement --selftest` deliberately injects
    breakages into rubric_h*.py, enforcement.py and olx_prompts.py and restores
    them afterwards, so for the ~15 minutes it runs those files intermittently
    hold text nobody wrote. Every scorer reads some of them live -- agreement.py
    and score.py build prompts from the rubric, and all three read gold,
    exclusions and the era fingerprint -- so a sweep started underneath one
    silently scores some cells against an injected rule.

    Nothing prevented that. The convention was "do not start a sweep while the
    self-test is running", which is a thing a person remembers, and the recorded
    incident this project already has -- a mid-run rewrite splitting handout 3's
    measurement, three items lost -- is the same failure from the other side.

    Detected by process, not a lock file, for the reason
    `_measurements_in_flight` gives: the self-test is killed by hand often enough
    that a stale lock would train everyone past the guard.
    """
    import subprocess

    try:
        out = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True,
                             text=True, check=False).stdout
    except Exception:                                   # pragma: no cover
        return []
    mine = str(os.getpid())
    SHELLS = {"bash", "sh", "dash", "zsh", "ksh", "-bash", "fish"}
    busy = []
    for line in out.splitlines()[1:]:
        pid, _, args = line.strip().partition(" ")
        if pid == mine:
            continue
        parts = args.split()
        if not parts or os.path.basename(parts[0]) in SHELLS:
            continue        # a watcher quoting the command is not the command
        idx = next((i for i, tok in enumerate(parts)
                    if os.path.basename(tok) == "equivalence.py"), None)
        if idx is None or "--selftest" not in parts:
            continue
        # THE PROCESS ITSELF, NOT ITS WRAPPER. This asked only whether SOME python
        # token appeared before `equivalence.py`, which is also true of a wrapper:
        # `timeout 90 env VAR=x python3 -u equivalence.py --enforcement --selftest`
        # keeps the whole command line on the `timeout` process, so the wrapper was
        # reported as a second self-test. Harmless while only sweeps consulted this
        # -- but the self-test now consults it too (see `enforcement_selftest`), and
        # a run launched under `timeout` would have found its own parent and refused
        # ITSELF. Measured 2026-09-18: a refusal listed both the real run and the
        # refusing run's own `timeout` wrapper.
        #
        # argv[0] is the discriminator: the mutating process is always python; a
        # wrapper never is. `env` does not matter either way, since it execs into
        # python and keeps no process of its own.
        if not os.path.basename(parts[0]).startswith("python"):
            continue
        root = _selftest_source_root(pid, parts[idx])
        if root is not None and root != _OUR_ROOT:
            continue        # a selftest on ANOTHER tree cannot touch our source
        busy.append(" ".join(parts[:9])
                    + ("" if root else "   [tree undetermined]"))
    return busy


_OUR_ROOT = os.path.dirname(os.path.realpath(__file__))


def _selftest_source_root(pid: str, tok: str) -> str | None:
    """WHICH scoring tree is that self-test mutating? None if undeterminable.

    THE GUARD USED TO MATCH ON THE PROCESS ALONE, and a process is machine-wide.
    A self-test run against an ISOLATED COPY -- a migration dry run, a scratch
    worktree -- therefore refused every sweep on the REAL tree, which it cannot
    touch by construction. Measured 2026-09-13, and it was expensive: a dry-run
    self-test started at 23:03:01 and fifteen live items refused inside fifteen
    seconds, losing the back half of a sweep that had been running six hours.

    The question the guard means to ask is not "is a self-test running" but "is a
    self-test mutating THE SOURCE I AM ABOUT TO READ". So resolve the
    `equivalence.py` the other process is running -- absolute if it said so,
    otherwise against its own cwd -- and compare directories.

    UNDETERMINABLE STAYS REFUSED. If /proc is unreadable the answer is None and
    the caller treats it as ours, because the failure this guard prevents is
    scoring cells against a rule nobody wrote, and that is far worse than a
    sweep that waits.
    """
    if os.path.isabs(tok):
        return os.path.dirname(os.path.realpath(tok))
    try:
        cwd = os.readlink(f"/proc/{pid}/cwd")
    except OSError:
        return None
    return os.path.dirname(os.path.realpath(os.path.join(cwd, tok)))


def refuse_if_selftest_running(what: str) -> None:
    """Abort `what` while an audit self-test is mutating the source it reads.

    Called by all three scorers at startup. `ALLOW_SELFTEST_OVERLAP` with a
    reason is the escape, in the same shape as the commit hook's
    ALLOW_UNDECLARED: the point is to make the overlap a decision someone stated,
    not to make it impossible.
    """
    busy = _selftest_in_flight()
    if not busy:
        return
    why = os.environ.get("ALLOW_SELFTEST_OVERLAP", "").strip()
    if why:
        print(f"{what}: proceeding during a self-test — {why}")
        return
    raise SystemExit(
        f"REFUSING to start {what}: an audit self-test is running against THIS\n"
        f"tree ({_OUR_ROOT}) and it injects breakages into the rubric and\n"
        f"enforcement source this run reads live, so some cells would be scored\n"
        f"against a rule nobody wrote. A self-test on a COPY does not refuse.\n"
        + "".join(f"    {b}\n" for b in busy)
        + "Wait for it to finish, or say why:\n"
        f'    ALLOW_SELFTEST_OVERLAP="..." <your command>')


_SECTION_RE = re.compile(r'<Vertical id="[^"]*" title="([^"]*)"')


def _items_whose_prompt_changed(handout: int, old: str, new: str) -> list[str]:
    """Which ITEMS' <LLMAction> bodies differ between two renderings."""
    out = []
    for item, aid in sorted(ACTION.items()):
        if HANDOUT.get(item) != handout:
            continue
        pat = re.compile(r'<LLMAction\b[^>]*?\bid="%s".*?</LLMAction>' % re.escape(aid), re.S)
        a = pat.search(old)
        b = pat.search(new)
        if (a.group(0) if a else None) != (b.group(0) if b else None):
            out.append(item)
    return out


class _CarriedAlready(Exception):
    """The item's record came from the course file, so do not scan the module.

    A sentinel rather than a flag because the source scan is one long `try`
    whose `except` prints "no recorded comments found" -- the message §2e exists
    to make impossible. Skipping the block without touching that handler keeps
    the two paths from growing into each other.
    """


def prior_record(item: str) -> str:
    """Everything already RECORDED about an item, printed where a rule is changed.

    QUALITY_CONTROL.md §2e exists because a day was spent rewriting Q1's
    `reasons_given` while the comment directly above the component already named
    gold's conditional structure, classified every cell with gold < 3, and
    diagnosed the one failing cell as a `harms_listed` misclassification rather
    than the merge failure being chased. Eleven configurations, ~900 calls.

    Advice did not prevent that and would not have: the guide's own words are
    "advice is what the reader already agreed with before misreading the table".
    So the record is pushed at the moment the rule changes -- the only moment it
    matters -- rather than left somewhere to be consulted by whoever remembers.

    Also prints the STRUCTURAL inventory (§2b): which primitives this item
    already carries and which are available but unused, so "is there a primitive
    for this" is answered before prose is written rather than after.
    """
    import subprocess
    import os.path

    h = HANDOUT.get(item)
    lines = [f"  ---- what is already recorded about {item} (QUALITY_CONTROL.md §2e) ----"]

    # 1. Substantial comment blocks about this item in its rubric.
    #
    # Found by MENTION, not by locating a dict entry. The first version looked for
    # a literal `"id": "DAY1"` line and scanned to the next `"id":`, which works
    # only where the rubric is written as a list of literal dicts. rubric_h2 builds
    # its twelve items from a factory, so no H2 item ever matched: the hook printed
    # "could not read rubric_h2.py: StopIteration" on every H2 --write, silently,
    # and §2e enforced nothing on the handout with the most recorded dead ends.
    #
    # A comment counts as being about this item when the item is named within a few
    # lines below it -- which covers a comment above a dict entry, above an
    # `if item_id == "DAY1"` branch, and above a declaration table keyed by id.
    # THE COURSE FILE FIRST, where the record has been carried. Stage 5 deletes
    # rubric_h1.py and rubric_h3.py, and this hook reads their SOURCE -- so a
    # deletion rehearsal had it reporting "no recorded comments found" for
    # thirteen items, which is the precise failure §2e exists to prevent: an
    # empty output that reads as "nothing recorded".
    #
    # rubric_h2 is NOT carried and does not need to be: its items are built by
    # the four factories A1c preserves, their record lives in those factory
    # bodies, and that module survives. So this path serves the handouts whose
    # files go, and the source scan below still serves the one that stays.
    _runs = []
    try:
        import coursedata as _cd

        _runs = _cd.rubric_note_runs(item)
    except Exception:
        _runs = []
    if _runs:
        SHOWN = 3
        skipped = _runs[:-SHOWN] if len(_runs) > SHOWN else []
        if skipped:
            lines.append(f"    {len(skipped)} EARLIER block(s) not shown, carried in "
                         f"the course file. A later comment often assumes an earlier "
                         f"one, so read them for context:")
            lines.append(f"      python3 -c \"import coursedata as c; "
                         f"print(chr(10).join(c.rubric_notes('{item}')))\"")
        for k, b in enumerate(_runs[-SHOWN:], len(_runs) - len(_runs[-SHOWN:]) + 1):
            lines.append(f"    course file, {item} block {k} of {len(_runs)} —")
            for t in b[:8]:
                lines.append(f"      {t[:96]}")
            if len(b) > 8:
                lines.append(f"      ... {len(b)-8} more lines: python3 -c "
                             f"\"import coursedata as c; "
                             f"print(chr(10).join(c.rubric_note_runs('{item}')[{k-1}]))\"")

    try:
        if _runs:
            raise _CarriedAlready                   # sections 2 and 3 still run
        # WHICHEVER NAME THE AUTHORED FILE HAS. Stage 6c renamed handout 2's
        # module to `rubric_h2_source.py`; reading the old name only would have
        # degraded this section to "no recorded comments found" for every H2
        # item -- the empty output that reads as "nothing recorded", which is
        # the precise failure the note above exists to prevent.
        _src_file = next((f for f in (paths.SCORING / f"rubric_h{h}.py",
                                      paths.SCORING / f"rubric_h{h}_source.py")
                          if f.exists()), None)
        if _src_file is None:
            raise LookupError(f"no authored rubric_h{h} file to scan")
        src = _src_file.read_text().splitlines()
        quoted = (f'"{item}"', f"'{item}'")
        mentions = {i for i, l in enumerate(src) if any(q in l for q in quoted)}
        if not mentions:
            raise LookupError(f"{item} is never named in rubric_h{h}.py")

        # The literal-dict span, when there is one: comments INSIDE the entry are
        # about the item even where they do not name it.
        span = None
        idline = next((i for i, l in enumerate(src)
                       if f'"id": "{item}"' in l), None)
        if idline is not None:
            stop = next((i for i in range(idline + 1, len(src))
                         if re.search(r'"id": "[^"]+"', src[i])), len(src))
            span = (idline, stop)

        WINDOW = 6          # how far below a comment the item may be named
        runs, run = [], []
        for i, line in enumerate(src + [""]):
            if line.lstrip().startswith("#"):
                run.append((i + 1, line.strip().lstrip("# ").rstrip()))
                continue
            if len(run) >= 4:
                runs.append(run)
            run = []
        # THE SPAN WINS WHERE THERE IS ONE. Mention-matching is the fallback for a
        # factory-built rubric, not an addition to the literal-dict case: only
        # three blocks are printed, and a file-level comment that merely sits near
        # a mention of the item can take a slot from one written about it. That
        # happened here -- Q1 was shown rubric_h1's general note on scoring
        # granularity, which is about every item, while one of its own six runs
        # dropped off the end.
        if span is not None:
            block = [r for r in runs if span[0] < r[0][0] <= span[1] + 1]
        else:
            # A FACTORY-BUILT ITEM'S RECORD IS IN ITS FACTORY. D1 and D2 are
            # `_definition_item("D1", ...)` and nothing else in the file names them,
            # so mention-matching alone found nothing for either -- and the function
            # that builds them carries the comments that ARE their record. Resolve
            # the factory from the constructing call and take its body too.
            spans = []
            for i in sorted(mentions):
                m = re.search(r'(\w+)\(\s*["\']%s["\']' % re.escape(item), src[i])
                if not m:
                    continue
                d = next((k for k, l in enumerate(src)
                          if l.startswith(f"def {m.group(1)}(")), None)
                if d is None:
                    continue
                stop = next((k for k in range(d + 1, len(src))
                             if src[k] and not src[k][0].isspace()), len(src))
                spans.append((d, stop))
            block = []
            for r in runs:
                after = r[-1][0]                   # 0-based index of the next line
                near = any(j in mentions
                           for j in range(after, min(after + WINDOW, len(src))))
                in_factory = any(a <= r[0][0] - 1 < b for a, b in spans)
                if near or in_factory:
                    block.append(r)
        # THE LATEST BLOCKS, not the first ones. An entry accumulates: the general
        # decisions are written early and the measured findings pile up at the
        # bottom, so `block[:3]` showed the oldest and cut the newest. Q1 has six
        # runs and the `reasons_given` material -- the comment §2e was written
        # about, after ~900 calls were spent rediscovering it -- is in the last
        # two.
        #
        # The earlier ones are NAMED rather than dropped, with the command to read
        # them, because a later comment often assumes an earlier one: "the same
        # rule" and "reverted again" mean nothing without what came before.
        SHOWN = 3
        skipped = block[:-SHOWN] if len(block) > SHOWN else []
        if skipped:
            spans = ", ".join(f"{b[0][0]}-{b[-1][0]}" for b in skipped)
            n0, n1 = skipped[0][0][0], skipped[-1][-1][0]
            lines.append(f"    {len(skipped)} EARLIER block(s) not shown, at "
                         f"rubric_h{h}.py:{spans}. A later comment often assumes an "
                         f"earlier one, so read them for context:")
            lines.append(f"      sed -n '{n0},{n1}p' rubric_h{h}.py")
        for b in block[-SHOWN:]:
            n0, n1 = b[0][0], b[-1][0]
            lines.append(f"    rubric_h{h}.py:{n0}-{n1} —")
            for _, t in b[:8]:
                lines.append(f"      {t[:96]}")
            if len(b) > 8:
                lines.append(f"      ... {len(b)-8} more lines: "
                             f"sed -n '{n0},{n1}p' rubric_h{h}.py")
    except _CarriedAlready:
        pass                                        # printed from the course file
    except Exception as e:
        lines.append(f"    (no recorded comments found in rubric_h{h}.py for "
                     f"{item}: {type(e).__name__}: {e})")

    # 2. Anything naming this item in the written record.
    for where in ("drafts", "BACKLOG.md", "GOALS.md"):
        p = paths.SCORING / where
        if not p.exists():
            continue
        try:
            # -w, not "\\b": grep's BRE has no word-boundary escape, so the
            # first version matched nothing and reported the record as empty --
            # a silent failure in the check written to prevent silent failures.
            r = subprocess.run(["grep", "-rnw", "-m", "3", item, str(p)],
                               capture_output=True, text=True, timeout=20)
            for l in (r.stdout or "").splitlines()[:3]:
                f, _, rest = l.partition(":")
                lines.append(f"    {os.path.basename(f)}:{rest[:100]}")
        except Exception as e:
            # NOT silent. `Path` was not in this module's namespace, so every
            # iteration raised NameError into a bare `except: pass` and the hook
            # reported an empty record -- the failure mode it exists to prevent,
            # inside the thing preventing it.
            lines.append(f"    (record lookup in {where} failed: "
                         f"{type(e).__name__}: {e})")

    # 3. The structural inventory (§2b): what this item already uses.
    try:
        tag = _sheet_tag(h, ACTION[item])
        have = [a for a in ("counts", "equals", "cover", "onlyif", "requires",
                            "expect", "forbid", "derived", "choices")
                if f'{a}="' in tag]
        free = [a for a in ("counts", "equals", "cover", "onlyif", "requires",
                            "expect", "forbid", "derived") if a not in have]
        lines.append(f"    PRIMITIVES in use: {', '.join(have) or 'none'}")
        lines.append(f"    available, unused: {', '.join(free)}   (§2b: structure before prose)")
    except Exception:
        pass
    return "\n".join(lines)


def _changed_sections(old: str, new: str) -> list[str]:
    """Which handout sections does this regeneration change the text of?

    The in-flight guard above stops a write from CORRUPTING a run. This answers
    the question that comes after it: the write succeeded, so which items are now
    unmeasured? A prompt edit is not finished until its item has been swept and
    compared, and {{corpus:Q4b/p13:modify:45:63:sha=1d18e2ec5cf4}} reliably goes wrong is sweeping from memory —
    editing four SLOT_NOTES entries, remembering three, and reporting a baseline
    for an item whose prose moved underneath it.

    So attribute every changed line to the nearest enclosing <Vertical> title and
    report those. Titles rather than agreement item keys, deliberately: the keys
    differ per handout (Q1..Q6, S1..S10, 1a/1c/2a) and the mapping is another copy
    that can drift, whereas the title is read straight out of the text that
    changed and is unambiguous to the person who has to run the sweep.
    """
    def sections(text: str) -> list[str]:
        here, out = "(preamble)", []
        for line in text.splitlines():
            m = _SECTION_RE.search(line)
            if m:
                here = m.group(1)
            out.append(here)
        return out

    a_sec, b_sec = sections(old), sections(new)
    hit: list[str] = []
    sm = difflib.SequenceMatcher(None, old.splitlines(), new.splitlines())
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        for s in a_sec[i1:i2] + b_sec[j1:j2]:
            if s not in hit:
                hit.append(s)
    return hit


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", dest="show", choices=sorted(ACTION),
                    help="print one generated prompt (refs shown as <Ref .../>)")
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the .olx files differ from what this generates")
    ap.add_argument("--write", action="store_true", help="rewrite the three .olx files")
    ap.add_argument("--diff", action="store_true", help="show what --write would change")
    ap.add_argument("--refs", action="store_true",
                    help="report <Ref> ids this generation drops, adds or duplicates")
    ap.add_argument("--force", action="store_true",
                    help="write even while a measurement is running (see the refusal)")
    a = ap.parse_args()

    # A --write while a run is IN FLIGHT silently splits that run across two
    # prompts. The cells already sent used the old text and the rest use the new,
    # so the .runs.json is a mixture of two configurations that nothing in it
    # records — and it reads exactly like a clean measurement.
    #
    # Done on 2026-08-24, on handout 3, by someone who had waited for two earlier
    # runs to clear for precisely this reason: 1a's baseline was 40 cells old
    # prompt and 20 new, and the two items behind it in the queue would have
    # measured the NEW prompt as their baseline. All three discarded.
    if a.write:
        busy = _measurements_in_flight()
        if busy and not a.force:
            print("REFUSING to write: a measurement is in flight and would be "
                  "split across two prompts.", file=sys.stderr)
            for b in busy:
                print(f"  {b}", file=sys.stderr)
            print("Wait for it, or re-run with --force if you know the run is "
                  "being discarded.", file=sys.stderr)
            return 1

    drift = _check_rules_still_match()
    for d in drift:
        print(f"WARNING: {d}", file=sys.stderr)
    # A copied constant with nothing binding it is the failure mode this project
    # keeps re-learning, so this one is fatal rather than a warning.
    bad = check_template_matches_example() + check_scorer_voice_in_labels()
    for b in bad:
        print(f"ERROR: {b}", file=sys.stderr)
    if bad:
        return 1

    if a.show:
        print(_to_xml(build_web_prompt(a.show)))
        return 0

    if a.refs:
        for h in (1, 2, 3):
            dropped, added, dupes = ref_delta(h)
            print(f"--- H{h}")
            for r in dropped:
                print(f"  DROPPED  {r}")
            for r in added:
                print(f"  ADDED    {r}")
            for r in dupes:
                print(f"  DUPLICATE ID  {r}")
        return 0

    if not (a.check or a.write or a.diff):
        ap.error("one of --print, --check, --write, --diff, --refs is required")

    rc = 0
    for h in (1, 2, 3):
        new, minted, cleared = render(h)
        old = _src(h)
        if minted:
            print(f"H{h}: minted {len(minted)} new ref id(s): "
                  + ", ".join(sorted(minted.values())), file=sys.stderr)
        if cleared:
            # E44. Loud on purpose: an emptied attribute means a rule that WAS
            # reaching the web has stopped, and the items it governed need
            # re-sweeping. Silence here is how three orphans survived a revert.
            print(f"H{h}: CLEARED {len(cleared)} orphaned attribute(s) whose "
                  f"rubric declaration has gone: " + ", ".join(sorted(cleared)),
                  file=sys.stderr)
            print(f"H{h}: those slots are no longer computed -- re-sweep the "
                  f"items before trusting their numbers", file=sys.stderr)
        if new == old:
            print(f"H{h}: up to date", file=sys.stderr)
            continue
        rc = 1 if a.check else rc
        if a.diff:
            sys.stdout.writelines(difflib.unified_diff(
                old.splitlines(True), new.splitlines(True),
                fromfile=f"h{h} current", tofile=f"h{h} generated"))
        if a.write:
            touched = _changed_sections(old, new)
            with open(OLX % h, "w") as fh:
                fh.write(new)
            print(f"H{h}: rewritten", file=sys.stderr)
            if touched:
                print(f"H{h}: UNMEASURED — prompt text changed under "
                      + "; ".join(touched), file=sys.stderr)
                print(f"H{h}: sweep those items and compare numerators against "
                      f"the last baseline BEFORE committing", file=sys.stderr)
            # §2e, enforced where it matters: the record is pushed AT the change.
            for it in _items_whose_prompt_changed(h, old, new):
                print(prior_record(it), file=sys.stderr)
        elif a.check:
            print(f"H{h}: OUT OF DATE — run olx_prompts.py --write", file=sys.stderr)
    return rc if a.check else 0


# --- corpus reference resolution (backdated) ---
# CONVERT HERE, DO NOT RESOLVE. What `--write` emits goes INTO the .olx, and the
# .olx is the file the reference mechanism exists to keep the words out of. This
# wrapper resolved, on the reasoning that the emitted text is what a web grader
# is sent -- but the grader is sent the BUILT page, and the build resolves on the
# way through, exactly as `_olx` does when the scorer reads the same file.
#
# Resolving here also does the very thing its old comment warned against: the
# generator writes words, the .olx holds a reference, and `--check` compares the
# two forms and reports every item out of date. Measured across the rewritten
# history: 42 of 113 generator+content states. Converting makes both sides carry
# the reference, so the comparison is like with like.
# A REFERENCE'S COLONS COLLIDE WITH THE SLOT-SHEET GRAMMAR, and the generator
# then misreads what it wrote itself. `slots=` is `name:description:verdicts@w`
# split on EVERY colon, so a description carrying
# `{{corpus:Q4b/p20:modify:17:40:sha=...}}` shifts every later field and the
# verdict list comes out as `Q4b`/`p20` instead of `met`/`absent`. Measured
# across the rewritten history before this shim: 107 of 114 generator states.
#
# Fixed HERE, backdated into every commit, because each commit runs its OWN
# generator and the old parser cannot otherwise be reached. The wrapper hides
# the colons INSIDE a reference while the original parser runs, then puts them
# back -- so the grammar is unchanged for everything that is not a reference,
# which is the narrowest fix that works.
try:                                            # pragma: no cover
    import re as _corpus_re
    _corpus_orig_parse_slots = parse_slots
    _CORPUS_REF_RE = _corpus_re.compile("[{][{]corpus:[^}]*[}][}]")
    _CORPUS_COLON = chr(0)   # no escape: this text is embedded in a non-raw string

    def parse_slots(spec, defaults, _orig=_corpus_orig_parse_slots):
        safe = _CORPUS_REF_RE.sub(
            lambda m: m.group(0).replace(":", _CORPUS_COLON), spec or "")
        out = _orig(safe, defaults)

        def _restore(v):
            if isinstance(v, str):
                return v.replace(_CORPUS_COLON, ":")
            if isinstance(v, list):
                return [_restore(x) for x in v]
            if isinstance(v, dict):
                return {k: _restore(x) for k, x in v.items()}
            return v

        return [_restore(d) for d in out]
except Exception:
    pass


try:                                            # pragma: no cover
    import corpus_resolve as _corpus_resolve
    _corpus_orig_web_prompt = build_web_prompt

    def build_web_prompt(*a, _orig=_corpus_orig_web_prompt, **kw):
        return _corpus_resolve.to_olx(_orig(*a, **kw), _corpus_resolve.load())
except Exception:
    pass


if __name__ == "__main__":
    raise SystemExit(main())
