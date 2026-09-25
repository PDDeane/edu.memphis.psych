#!/usr/bin/env python3
"""Render the rubric of record as a `<Rubric>` OLX component.

NOTHING CALLS THIS ANY MORE, as of step 3d. Both consumers retired in that
commit: `rubric_export --olx`, which made the component a build product, and
`check_the_rubric_component_is_current`, which held the file to this render.
`bmod_rubric.olx` is now the SOURCE -- the course file it rendered from no longer
carries a rubric, so a render could only overwrite the source with an empty
projection of itself.

IT IS KEPT UNTIL STEP 4, and only until then, for what `frame_text()` and the
comments around `criteria_frame()` record: that the obvious parameterisation of
the cadence block -- `params="cadence=day"` and a placeholder -- WAS TRIED AND
FAILS, because the DAY text cross-references the other cadence ("not a weekly
plan") and a whole-word swap does not reproduce the WK block. Step 4 moves that
prose into the authored rubric and deletes this module. Deleting it first would
throw away a measured negative result and invite the same attempt again.

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
    """One attribute value, XML-escaped, with line breaks preserved.

    XML NORMALISES WHITESPACE IN ATTRIBUTE VALUES: a literal newline becomes a
    space before any parser hands the value back. `rule` texts are multi-line, so
    writing them literally loses every break silently -- the file still parses,
    the value still reads, and the prose has quietly been reflowed. Character
    references are NOT normalised, so the breaks are written as `&#10;` and come
    back exactly as authored.
    """
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float) and v == int(v):
        v = int(v)
    s = html.escape(str(v), quote=True)
    return s.replace("\r\n", "&#10;").replace("\n", "&#10;").replace("\t", "&#9;")


import rubric_component as _rc  # noqa: E402


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


def _conditions_for(authored: dict, item_id: str, item: dict | None = None) -> str | None:
    """Selector tuples become declared conditions on the items they select.

    `CONTINGENCY_GATE_ITEMS = ("DAY1", "WK1", ...)` is the rubric saying "these
    items carry the contingency gate". In OLX that is a condition NAME the item
    declares and a frame segment matches on -- names as data, which is what keeps
    subject vocabulary out of the engine.
    """
    names = []
    # A NAMED BOOLEAN ON THE ITEM IS A CONDITION. `conditions` and `params` are
    # "names the engine matches and substitutes -- never interprets", and the
    # generator this model replaced "carried a named boolean per condition, which
    # put subject vocabulary into the engine's own interface and meant every new
    # variant needed engine code". These are those booleans.
    for flag in ("avoidance_scores", "graph_item", "move_pick", "reads_utb_choice",
                 "gold_from_deductions"):
        if (item or {}).get(flag):
            names.append(flag)
    for key, val in sorted(authored.items()):
        if not key.endswith("_ITEMS"):
            continue
        if item_id in _seq(val):
            names.append(key[: -len("_ITEMS")].lower())
    cond = _cadence_cond(item or {})
    if cond:
        names.insert(0, cond)
    return "|".join(names) or None


def render_item(item: dict, authored: dict, indent: str = "  ") -> list[str]:
    out = []
    out.append(f"{indent}<Item" + _attrs([
        ("scores", item.get("id")),
        # NO `handout` HERE. It was added and the build refused it -- 27 x
        # ATTRIBUTE_VALIDATION, because `Item`'s schema is strict and does not
        # carry one. That refusal is right: which handout an item belongs to is
        # course STRUCTURE, not rubric content, and Stage 5 said as much -- "an
        # item does not record which handout it is in, because the module it was
        # written in WAS the handout". `coursedata.items()` joins it from the
        # course file, where the structural wiring lives.
        ("max", item.get("max")),
        ("label", item.get("label")),
        ("increment", item.get("increment")),
        ("deriveFromCredit", item.get("derive_from_credit")),
        ("conditions", _conditions_for(authored, item.get("id"), item)),
        ("params", _params_for(item)),
        ("blankCode", item.get("blank_code")),
        ("expectedType", item.get("expected_type")),
        ("deriveFromClauses", item.get("derive_from_criteria")),
        # EMITTED ONLY WHEN THE ITEM DECLARES IT. An item that omits the key is a
        # different item from one declaring it holds none, and `",".join([])` is
        # "" -- which would have written the attribute onto all 26 items.
        ("unreachableCodes",
         ",".join(_seq(item["unreachable_codes"]))
         if "unreachable_codes" in item else None),
    ]) + ">")
    i2 = indent + "  "
    if item.get("question"):
        out.append(f"{i2}<Question>{_text(item['question'])}</Question>")
    # A GATE IS A SLOT, and all three of its parts live on the slot: that it
    # gates, the code it charges, and the sentence saying why. Reconstructing a
    # gate from a slot plus a deduction would lose the `because` text, which is
    # the gate's own message and not the deduction's generic one.
    gates = {g.get("key"): g for g in _seq(item.get("oc_gates") or [])}
    for s in _slots_for(authored, item.get("id")):
        g = gates.get(s.get("key")) or {}
        out.append(f"{i2}<Slot" + _attrs([
            ("key", s.get("key")), ("label", s.get("label")),
            ("seg", s.get("seg")), ("pts", s.get("pts")),
            # `gate` IS THE SLOT'S OWN FLAG, on 60 slots, and is not the same
            # thing as having an oc_gate. Setting it only for gated items wrote
            # it onto 5. The gate's code and message come from `oc_gates`; that
            # a slot gates at all comes from the slot.
            # THE STAGE SURVIVES THE ROUND TRIP. Writing "true" for a slot
            # declared `gate="final"` silently DEMOTES it to definitional, which
            # moves the rule earlier and changes which code a cell charges --
            # authored data lost by regenerating the file it was authored in.
            # The stage is carried on the oc_gate, so read it from there.
            # THE STAGE SURVIVES THE ROUND TRIP, and the vocabulary is
            # `rubric_component`'s to know, not this writer's.
            ("gate", ((_rc.GATE_STAGES.get(g.get("stage"))
                       or _rc.GATE_STAGES.get(s.get("gate")) or "true")
                      if (s.get("gate") or g) else None)),
            ("charge", g.get("code")),
            ("because", g.get("text")),
        ]) + "/>")
    for c in _seq(item.get("credit") or []):
        body = c.get("desc") or c.get("text") or ""
        out.append(f"{i2}<Credit" + _attrs([
            ("what", c.get("what")),
            # PRESENT-WITH-NO-VALUE is a third case, after absent and empty: a
            # credit row can declare `pts: None`, meaning it carries no points but
            # is still a scored component. An empty attribute says that; omitting
            # it would say the row never mentioned points.
            ("pts", ("" if c["pts"] is None else c["pts"]) if "pts" in c else None),
            ("verdicts", "|".join(_seq(c.get("verdicts") or [])) or None),
            # PRESENT-BUT-EMPTY AGAIN: Q4c declares `codes: {}`, which is not the
            # same as a row that never mentions codes. `or None` erased the
            # difference.
            ("codes",
             "|".join(f"{k}={v}" for k, v in sorted((c["codes"] or {}).items()))
             if "codes" in c else None),
            ("free", "|".join(_seq(c.get("free"))) if c.get("free") else None),
            ("rule", c.get("rule")),
            ("reported", c.get("reported")),
            ("gates", "true" if c.get("gates") else None),
        ]) + (f">{_text(body)}</Credit>" if body else "/>"))
    for d in _seq(item.get("deductions") or []):
        out.append(f"{i2}<Deduction" + _attrs([
            ("code", d.get("code")), ("pts", d.get("pts")),
            ("repeatable", "true" if d.get("repeatable") else None),
        ]) + f">{_text(d.get('text') or '')}</Deduction>")
    for g in _seq(item.get("guidance") or []):
        out.append(f"{i2}<Guidance>{_text(g)}</Guidance>")
    if _takes_frame(item):
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
            ("lenient", "|".join(_seq(e.get("lenient"))) if e.get("lenient") else None),
        ]) + "/>")
    for e in _seq(item.get("equals") or []):
        out.append(f"{i2}<Equals" + _attrs([
            ("key", e.get("key")), ("left", e.get("left")), ("right", e.get("right")),
            # THE NOTE SURVIVES REGENERATION. Dropping it here would lose the
            # ledger's wording for the charge the moment this file rewrote the
            # rubric -- authored data destroyed by the writer that exists to
            # preserve it, which is the failure `gate=` already had once today.
            ("note", e.get("note")),
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
            # `or None` HERE, unlike `codes` and `unreachableCodes`: those two are
            # declared-empty in the source and must survive as empty; these are
            # simply absent, and an absent list must not become `words=""`.
            ("fields", ",".join(_seq(dv.get("fields") or [])) or None),
            ("words", ",".join(_seq(dv.get("words") or [])) or None),
            # JSON, because the value is nested numeric data -- 1c's graph
            # template is a list of series. An attribute can hold it losslessly
            # and the reader parses it back; inventing a flat encoding for one
            # field would be a private format nobody else can read.
            ("template", json.dumps(dv["template"], separators=(",", ":"))
                         if dv.get("template") is not None else None),
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
# NO ITEM IDS IN THIS MODULE. The first version listed the eight operant items
# and which cadence each took, and the audit called it what it was: course data
# in a scoring module, the exact embedding this migration removes. The rubric
# already says both things -- `derive_from_criteria` marks the items that take
# the criteria frame, and `cadence` says which one -- so it is asked instead of
# told. A ninth item joining the frame then needs no edit here.
def _takes_frame(item: dict) -> bool:
    return bool(item.get("derive_from_criteria"))


def _params_for(item: dict) -> str | None:
    """`params="cadence=daily"` -- values for the frame's placeholders.

    The cadence block differs between the daily and weekly items only in wording,
    and the frame is authored with placeholders so that only the intended
    occurrences substitute. A blind whole-word swap does NOT reproduce the other
    variant -- the text cross-references the opposite cadence -- which is why the
    value is supplied rather than derived.
    """
    c = item.get("cadence")
    return f"cadence={c}" if c else None


def _cadence_cond(item: dict) -> str | None:
    c = item.get("cadence")
    return f"cadence_{c}" if c else None


def criteria_frame(base: str, daily_block: str, weekly_block: str,
                   indent: str = "  ") -> list[str]:
    i2 = indent + "  "
    out = [f'{indent}<Frame name="oc_criteria">']
    out.append(f"{i2}<Segment>{_text(base)}</Segment>")
    out.append(f'{i2}<Segment ifDeclared="cadence_daily">{_text(daily_block)}</Segment>')
    out.append(f'{i2}<Segment ifDeclared="cadence_weekly">{_text(weekly_block)}</Segment>')
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
        # J-3. WAS config(2) -- the frame-taking items are the criteria ones.
        _h = _H.carrying("derive_from_criteria")[0]
        rows = [i for i in _H.config(_h)["rubric"].ITEMS if _takes_frame(i)]
        plain = next(i for i in rows if not i.get("cadence"))
        day = next(i for i in rows if i.get("cadence") == "daily")
        week = next(i for i in rows if i.get("cadence") == "weekly")
        base = _O._criteria_section(plain)
        daily = _O._criteria_section(day)
        weekly = _O._criteria_section(week)
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
    # THE OTHER FRAME. `OC_FRAME` is the four-types definition, a handout-level
    # value the view serves by name. The 2026-09-16 reference inlined its text
    # once per item, twelve times over; a frame says it once and lets the items
    # cite it, which is what a frame is for.
    for hk in sorted((doc.get("handouts") or {})):
        oc = ((doc["handouts"][hk] or {}).get("authored") or {}).get("OC_FRAME")
        if oc:
            lines.append(f'  <Frame name="oc_frame">')
            lines.append(f"    <Segment>{_text(oc)}</Segment>")
            lines.append(f"  </Frame>")
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
