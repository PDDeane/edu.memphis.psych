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
    for c in _seq(item.get("counts") or []):
        out.append(f"{i2}<Counts" + _attrs([
            ("key", c.get("key")),
            ("slots", ",".join(_seq(c.get("slots") or []))),
        ]) + "/>")
    out.append(f"{indent}</Item>")
    return out


def render(doc: dict, rubric_id: str = "bmod_rubric",
           title: str = "Behaviour-modification scoring rubric") -> str:
    lines = [f'<Rubric id="{_attr(rubric_id)}" title="{_attr(title)}">']
    for item in doc.get("items", []):
        authored = ((doc.get("handouts") or {}).get(str(item.get("handout"))) or {}).get("authored") or {}
        lines += render_item(item, authored)
    lines.append("</Rubric>")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    import sys
    doc = json.load(open(sys.argv[1]))
    sys.stdout.write(render(doc))
