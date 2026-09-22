#!/usr/bin/env python3
"""Render the rubric of record as a `<Rubric>` OLX component.

WHY OLX AND NOT JSON. The rubric belongs IN the content, as a lo-blocks component
the course links beside the three handouts:

    <Course id="bmod_course" title="Behaviour Modification" launchable="course">
      <Use ref="bmod_rubric"/>
      <Use ref="bmod_handout1"/>
      <Use ref="bmod_handout2"/>
      <Use ref="bmod_handout3"/>
    </Course>

A course HOLDS content it never SHOWS -- `_Course.tsx` filters non-rendering
blocks at render time -- so the rubric is scoped to the course and invisible to a
learner, and one artifact carries both what the student sees and what scores it.

WHAT MOVES, AND WHY IT IS NOT A CHOICE. The per-item fields are obvious. The
per-handout `authored` tables are NOT optional extras: `<Item>` has no slots of
its own and `SLOT_SPEC` is where they live, field-for-field --

    SLOT_SPEC['Q1'][0]  {"key": "matches_selected", "label": "...", "seg": "matches/differs"}
    <Slot key="matches_selected" label="..." seg="matches/differs"/>

-- so an item cannot be rendered without them. The same holds for `SLOT_OPTIONS`
(<Verdicts>), `MAPS` (<Map>), `OC_FRAME` (<Frame>/<Segment>), `FORBID`, `EXPECT`
and the `*_ITEMS` selector tuples, which become `conditions=` on the items they
select.

WHAT STAYS IN `course.json`, because it is not the rubric:
  * `declarations` and the carried `*_notes` -- metadata about the scoring system.
  * `generator.SEGMENT_MARKERS` -- the literal strings that cut a submission
    .docx into boxes. `segment.py` reads them long before any rubric is
    consulted, and two corrupted entries silently broke handout 2's box split on
    2026-09-22.
  * `generator.CONTEXT_REFS`, `CONTEXT__non_item`, `TABLE_ORDER` -- id wiring and
    ordering.
  * `generator.SCORING_DIVERGENCES`, `PROBE_REACH_LIMITS` -- declarations.

`scores`, NOT `ref`: the platform reserves `ref` for `<Use>` and the parser
refuses it anywhere else. `Item.md`'s attribute table still says `ref`; `Item.ts`
is right and says why.
"""
from __future__ import annotations

import html
import json


def _attr(v) -> str:
    """One attribute value, XML-escaped. Booleans render as the strings the schema takes."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float) and v == int(v):
        v = int(v)
    return html.escape(str(v), quote=True)


def _attrs(pairs) -> str:
    return "".join(f' {k}="{_attr(v)}"' for k, v in pairs if v is not None and v != [])


def _text(s) -> str:
    """Element body. Not `quote=True`: a quote is legal in text and escaping it adds noise."""
    return html.escape(str(s), quote=False)


def _seq(v):
    """A JSON list, or a `{__tuple__: [...]}` the exporter writes for a tuple."""
    if isinstance(v, dict) and "__tuple__" in v:
        return list(v["__tuple__"])
    return list(v) if isinstance(v, (list, tuple)) else [v]


def _slots_for(authored: dict, item_id: str) -> list:
    return _seq((authored.get("SLOT_SPEC") or {}).get(item_id) or [])


def _conditions_for(authored: dict, item_id: str) -> str | None:
    """Selector tuples become declared conditions on the items they select.

    `CONTINGENCY_GATE_ITEMS = ("DAY1", "WK1", ...)` is the rubric saying "these
    items carry the contingency gate". In OLX that is a condition NAME the item
    declares and a frame segment matches on -- names as data, which is what keeps
    subject vocabulary out of the engine.
    """
    names = []
    if item_id in _CADENCE_OF:
        names.append(_CADENCE_OF[item_id])
    for key, val in sorted(authored.items()):
        if not key.endswith("_ITEMS"):
            continue
        if item_id in _seq(val):
            names.append(key[: -len("_ITEMS")].lower())
    return "|".join(names) or None


def render_item(item: dict, authored: dict, indent: str = "  ") -> list[str]:
    out = []
    out.append(f"{indent}<Item" + _attrs([
        ("scores", item.get("id")),
        ("max", item.get("max")),
        ("label", item.get("label")),
        ("increment", item.get("increment")),
        ("deriveFromCredit", item.get("derive_from_credit")),
        ("conditions", _conditions_for(authored, item.get("id"))),
        ("blankCode", item.get("blank_code")),
        ("expectedType", item.get("expected_type")),
        ("deriveFromClauses", item.get("derive_from_criteria")),
        ("unreachableCodes", ",".join(_seq(item.get("unreachable_codes") or []))),
    ]) + ">")
    i2 = indent + "  "
    if item.get("question"):
        out.append(f"{i2}<Question>{_text(item['question'])}</Question>")
    for s in _slots_for(authored, item.get("id")):
        out.append(f"{i2}<Slot" + _attrs([
            ("key", s.get("key")), ("label", s.get("label")),
            ("seg", s.get("seg")), ("pts", s.get("pts")),
        ]) + "/>")
    for c in _seq(item.get("credit") or []):
        body = c.get("desc") or c.get("text") or ""
        out.append(f"{i2}<Credit" + _attrs([
            ("what", c.get("what")), ("pts", c.get("pts")),
            ("verdicts", "|".join(_seq(c.get("verdicts") or [])) or None),
            ("codes", "|".join(f"{k}={v}" for k, v in sorted((c.get("codes") or {}).items())) or None),
            ("free", c.get("free")), ("rule", c.get("rule")),
            ("reported", c.get("reported")),
        ]) + (f">{_text(body)}</Credit>" if body else "/>"))
    for d in _seq(item.get("deductions") or []):
        out.append(f"{i2}<Deduction" + _attrs([
            ("code", d.get("code")), ("pts", d.get("pts")),
        ]) + f">{_text(d.get('text') or '')}</Deduction>")
    for g in _seq(item.get("guidance") or []):
        out.append(f"{i2}<Guidance>{_text(g)}</Guidance>")
    if item.get("id") in FRAME_ITEMS:
        out.append(f'{i2}<Guidance use="@oc_criteria"/>')
    # THE SCORING PRIMITIVES, one element each. These are per-item fields in the
    # course file and purpose-built elements in OLX, so the mapping is direct --
    # the only work is the joined-attribute spellings the schema uses.
    for m in _seq(item.get("maps") or []):
        out.append(f"{i2}<Map" + _attrs([
            ("key", m.get("key")), ("pick", m.get("pick")),
            ("pairs", ",".join(f"{q.get('value')}~{q.get('verdict')}"
                               for q in _seq(m.get("pairs") or []))),
            ("fallback", m.get("fallback")),
        ]) + "/>")
    for f in _seq(item.get("forbid") or []):
        out.append(f"{i2}<Forbid" + _attrs([
            ("key", f.get("key")),
            ("conds", ",".join(f"{c.get('slot')}={c.get('value')}"
                               for c in _seq(f.get("conds") or []))),
        ]) + "/>")
    for e in _seq(item.get("expect") or []):
        out.append(f"{i2}<Expect" + _attrs([
            ("key", e.get("key")), ("left", e.get("left")), ("value", e.get("value")),
        ]) + "/>")
    for e in _seq(item.get("equals") or []):
        out.append(f"{i2}<Equals" + _attrs([
            ("key", e.get("key")), ("left", e.get("left")), ("right", e.get("right")),
            ("lenient", "|".join(_seq(e.get("lenient") or [])) or None),
        ]) + "/>")
    for o in _seq(item.get("onlyif") or []):
        out.append(f"{i2}<Onlyif" + _attrs([
            ("key", o.get("key")), ("cond", o.get("cond")),
        ]) + "/>")
    for r in _seq(item.get("requires") or []):
        out.append(f"{i2}<Requires" + _attrs([
            ("key", r.get("key")), ("cond", r.get("cond")),
            ("lenient", "|".join(_seq(r.get("lenient") or [])) or None),
        ]) + "/>")
    for dv in _seq(item.get("derived") or []):
        out.append(f"{i2}<Derived" + _attrs([
            ("key", dv.get("key")), ("kind", dv.get("kind")),
            ("fields", ",".join(_seq(dv.get("fields") or []))),
            ("words", ",".join(_seq(dv.get("words") or []))),
        ]) + "/>")
    for cv in _seq(item.get("cover") or []):
        out.append(f"{i2}<Cover" + _attrs([
            ("checks", ",".join(_seq(cv.get("keys") or []))),
            ("labels", ",".join(_seq(cv.get("labels") or []))),
            ("item", cv.get("of")),
            ("verdicts", "|".join(_seq(cv.get("verdicts") or [])) or None),
        ]) + "/>")
    for ctx in _seq(item.get("context") or []):
        out.append(f'{i2}<Context item="{_attr(ctx)}"/>')
    for c in _seq(item.get("counts") or []):
        out.append(f"{i2}<Counts" + _attrs([
            ("key", c.get("key")),
            ("slots", ",".join(_seq(c.get("slots") or []))),
        ]) + "/>")
    out.append(f"{indent}</Item>")
    return out


# A FILE THAT CARRIES REFERENCES MUST SAY WHERE THEY RESOLVE FROM. The build
# refuses one that does not -- "carries {{corpus:...}} references and no
# `corpus_data:` in its frontmatter" -- rather than render an unresolved marker
# to a student. The rubric inherits its references from the rubric of record, so
# it needs the same declaration the handouts carry.
#
# The marker syntax is deliberately not spelled out in the comment body, for the
# reason the handouts give: a comment containing it reads as a reference to
# anything scanning by substring.
FRONTMATTER = """<!--
---
# Where the referenced spans live. The build resolves this file's corpus
# references against it, and refuses rather than render an unresolved one.
corpus_data: $COURSE_DATA/corpus_refs.json
description: The behaviour-modification scoring rubric, as a component. Generated
  by `rubric_olx.py` from the rubric of record; do not hand-edit.
---
-->"""


# THE SHARED CRITERIA FRAME, and why it is three exact segments rather than one
# parameterised one.
#
# `olx_prompts._criteria_section` builds this text for the eight operant items and
# yields three distinct results: a base that PR/NR/PP/NP get, and that base plus a
# cadence block for DAY1/DAY2 and for WK1/WK2. The base is a clean PREFIX of the
# other two, so the block splits off exactly.
#
# THE OBVIOUS PARAMETERISATION IS WRONG. DAY and WK differ only in `day`/`week`
# and `daily`/`weekly`, which reads like `params="cadence=day"` and a placeholder
# -- but the DAY text already contains "week" once and "daily" twice, because it
# cross-references the other cadence ("not a weekly plan"). A whole-word swap does
# NOT reproduce the WK block; it was tried and compared, and it fails. Two exact
# segments need no substitution and can be checked byte for byte.
CADENCE_DAILY = "cadence_daily"
CADENCE_WEEKLY = "cadence_weekly"
FRAME_ITEMS = ("PR", "NR", "PP", "NP", "DAY1", "DAY2", "WK1", "WK2")
_CADENCE_OF = {"DAY1": CADENCE_DAILY, "DAY2": CADENCE_DAILY,
               "WK1": CADENCE_WEEKLY, "WK2": CADENCE_WEEKLY}


def criteria_frame(base: str, daily_block: str, weekly_block: str,
                   indent: str = "  ") -> list[str]:
    i2 = indent + "  "
    out = [f'{indent}<Frame name="oc_criteria">']
    out.append(f"{i2}<Segment>{_text(base)}</Segment>")
    out.append(f'{i2}<Segment ifDeclared="{CADENCE_DAILY}">{_text(daily_block)}</Segment>')
    out.append(f'{i2}<Segment ifDeclared="{CADENCE_WEEKLY}">{_text(weekly_block)}</Segment>')
    out.append(f"{indent}</Frame>")
    return out


def frame_text():
    """(base, daily block, weekly block), or None if they cannot be derived.

    READ FROM `olx_prompts` FOR NOW, AND THAT IS THE POINT OF THE REMAINING WORK.
    The criteria prose lives at `olx_prompts._criteria_section` -- course content
    inside engine code, which is exactly what this migration exists to end. Taking
    it from there keeps ONE copy while the rubric moves: two copies of a rule are
    two rules, and this file's own history records a drift in three places when
    that happened before. When the prose moves out, this function is what changes.
    """
    try:
        import handouts as _H
        import olx_prompts as _O
        items = {i["id"]: i for i in _H.config(2)["rubric"].ITEMS}
        base = _O._criteria_section(items["PR"])
        daily = _O._criteria_section(items["DAY1"])
        weekly = _O._criteria_section(items["WK1"])
    except Exception:
        return None
    if not (daily.startswith(base) and weekly.startswith(base)):
        # The split is only exact while the base is a prefix of both. If that
        # stops holding, emitting anyway would silently ship a different prompt.
        return None
    return base, daily[len(base):], weekly[len(base):]


def render(doc: dict, rubric_id: str = "bmod_rubric",
           title: str = "Behaviour-modification scoring rubric") -> str:
    lines = [FRONTMATTER,
             f'<Rubric id="{_attr(rubric_id)}" title="{_attr(title)}">']
    frame = frame_text()
    if frame:
        lines += criteria_frame(*frame)
    # ANSWER VOCABULARIES, named once and shared. `SLOT_OPTIONS` is
    # {slot: [values]}; the 2026-09-16 reference gave each vocabulary a human name
    # ("authorship" for relieved|created|neither) and had slots cite it. The slot's
    # own name is used here instead -- same vocabulary, same values, and no naming
    # table to keep in step with a second copy.
    for hk in sorted((doc.get("handouts") or {})):
        opts = ((doc["handouts"][hk] or {}).get("authored") or {}).get("SLOT_OPTIONS") or {}
        for name in sorted(opts):
            vals = "|".join(_seq(opts[name]))
            lines.append(f'  <Verdicts name="{_attr(name)}" values="{_attr(vals)}"/>')
    for item in doc.get("items", []):
        authored = ((doc.get("handouts") or {}).get(str(item.get("handout"))) or {}).get("authored") or {}
        lines += render_item(item, authored)
    lines.append("</Rubric>")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import sys
    doc = json.load(open(sys.argv[1]))
    sys.stdout.write(render(doc))
