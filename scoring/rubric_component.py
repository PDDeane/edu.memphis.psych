#!/usr/bin/env python3
"""Read the rubric COMPONENT -- the expanded `<Rubric>` the build stages.

WHY THIS READS THE STAGED FILE AND NOT THE AUTHORED ONE. The authored rubric may
carry `<ItemTemplate>` and `<Item use="@pair" params="..."/>`; the staged one
never does. `materialiseRubric` expands templates during the build, on purpose:

    "If a template survived into that output, every reader would need the template
     grammar -- and a second implementation of one rule is the drift this whole
     model exists to end."

So this reads what the build produced. It is a plain XML walk over ordinary
elements: no template grammar, no second implementation, nothing to fall out of
step with `materialiseRubric`. The same argument is why it does not read the
authored file "just to be safe" -- that would be the second implementation.

IT ALSO READS THE RESOLVED COPY, which matters for a different reason: the staged
file has had its `{{corpus:...}}` references expanded against the corpus, so the
text here is what a student is actually shown. The authored file carries
references, and comparing those to anything rendered would compare two spellings
of the same string -- the mistake that cost a day's work on 2026-09-22.

WHEN THE BUILD HAS NOT RUN, this says so rather than guessing. A stale or absent
artifact is not the same as a rubric with no items, and a reader that quietly
returns nothing is how an empty result comes to look like a clean pass.
"""
from __future__ import annotations

import json
import os
import re
import xml.etree.ElementTree as ET

# COMMENTS ARE STRIPPED BEFORE PARSING, and the reason is not tidiness. The
# frontmatter convention writes YAML inside an XML comment:
#
#     <!--
#     ---
#     corpus_data: $COURSE_DATA/corpus_refs.json
#     ---
#     -->
#
# and `---` contains `--`, which XML forbids inside a comment. lo-blocks' own
# parser accepts it; `xml.etree` refuses the file outright with "not well-formed
# (invalid token): line 2, column 2". Both are right about their own contract --
# the platform defined the convention, and this reader is a guest. Comments carry
# no rubric, so they are removed and the rest is parsed strictly. Comments cannot
# nest, so a non-greedy match is exact.
_COMMENT = re.compile(r"<!--.*?-->", re.S)


def staged_path() -> str:
    """Where the build leaves the expanded, RESOLVED rubric."""
    import paths
    return os.path.join(str(paths.LO), ".stage", "content", paths.NS,
                        "psychology", "bmod_rubric.olx")


def expanded_path() -> str:
    """The expanded, UNRESOLVED rubric -- what the scorer reads.

    THE THIRD ARTIFACT, and until 2026-09-22 it did not exist. The other two each
    fail this reader in a different way:

      authored         templates unexpanded -- reading it would mean implementing
                       the template grammar a second time, which is the drift
                       `materialiseRubric` opens by refusing.
      .stage/content   references RESOLVED -- `olx_prompts` writes this prose back
                       into a PUBLIC repository, so reading resolved text would
                       replace every `{{corpus:...}}` with the span it protects.
                       Measured: it made all three handouts read OUT OF DATE, and
                       the diff was the reference replaced by its expansion.

    `npm run build:expand-rubrics` writes it, before resolution and from the same
    staged set of files, so expansion is structural and resolution is textual and
    neither has to know about the other.
    """
    import paths
    return os.path.join(str(paths.LO), ".stage", "expanded", paths.NS,
                        "psychology", "bmod_rubric.olx")


def authored_path() -> str:
    """The authored rubric, templates unexpanded and references INTACT.

    TWO CONSUMERS WANT DIFFERENT THINGS, and reading the wrong one is not a
    stylistic mistake. The SCORER wants references resolved -- it judges the text
    a student saw. The GENERATOR must keep them: `olx_prompts` writes the rubric's
    prose into the shipped `.olx`, so feeding it resolved text would replace every
    `{{corpus:...}}` with the span it protects and undo the scrub, in a public
    repository, silently. Measured 2026-09-22: pointing `coursedata.items()` at
    the staged copy made all three handouts read OUT OF DATE, and the diff was the
    reference replaced by its expansion.

    So the rubric of record for READING is this file, and resolution stays where
    it already lives -- `agreement.load_action`, `_field_sha`, `check_idmap_is_current`
    each expand at the point of comparison.

    WHEN TEMPLATES ARRIVE THIS NEEDS A BUILD STEP. The authored file is expanded
    today only because nothing uses `<ItemTemplate>` yet. The artifact this
    function should return is EXPANDED BUT UNRESOLVED -- which is neither the
    authored file nor `.stage/content`, and does not exist yet. That is the one
    piece of build work the hand-authoring step still owes.
    """
    import paths
    return os.path.join(str(paths.REPO), "psychology", "bmod_rubric.olx")


def _text(el) -> str:
    return "".join(el.itertext()).strip()


def load(path: str | None = None) -> dict:
    """-> {item_id: {slots, credit, deductions, guidance, question, attrs}}.

    Raises FileNotFoundError when the build has not staged the rubric: the caller
    decides what an absent artifact means, which is never "no findings".
    """
    p = path or staged_path()
    with open(p, encoding="utf8") as fh:
        text = _COMMENT.sub("", fh.read())
    root = ET.fromstring(text)            # raises on malformed, which is correct
    out: dict = {}
    for item in root.iter("Item"):
        iid = item.get("scores")
        if not iid:
            continue
        out[iid] = {
            "attrs": dict(item.attrib),
            "question": next((_text(q) for q in item.findall("Question")), ""),
            "slots": [dict(s.attrib) for s in item.findall("Slot")],
            "credit": [dict(c.attrib) for c in item.findall("Credit")],
            "deductions": [dict(d.attrib) for d in item.findall("Deduction")],
            "guidance": [_text(g) for g in item.findall("Guidance")
                         if not g.get("use")],
            "frames": [g.get("use") for g in item.findall("Guidance")
                       if g.get("use")],
        }
    return out


def slot_keys(item_id: str, path: str | None = None) -> list[str]:
    """The slot keys the rubric declares for one item, in rubric order."""
    entry = load(path).get(item_id) or {}
    return [s.get("key") for s in entry.get("slots", []) if s.get("key")]




# ---------------------------------------------------------------- view shape --
#
# THE VIEW'S SHAPE IS THE CONTRACT, not this module's convenience. 102 call sites
# across 18 modules reach the rubric through `config(h)["rubric"]`, spelled
# `.BY_ID[item]`, `.ITEMS`, `.SLOT_SPEC`. When the modules went at Stage 5 the
# CHANNEL was converted and every site kept its spelling; the same applies here.
# So these functions rebuild exactly what the view serves -- parsed types, the
# same keys, the same order. `check_the_component_reproduces_the_view` held them
# to it while both sources existed and retired at step 3d with the second copy;
# that window was the only time the equality was PROVABLE, which is why the
# duplication was kept until the proof was green. What holds the shape now is use:
# every one of those 102 sites reads through it on every scoring run.

_TRUE = ("true", "True", "1")


class _Declared:
    """Marker: the attribute was written with no value, so the key exists as None."""


def _num(v, cast=float):
    if v == "":
        return _Declared            # declared, valueless -- not the same as absent
    try:
        return cast(v)
    except (TypeError, ValueError):
        return None


def _list(v, sep=","):
    return [x for x in (v or "").split(sep) if x] if v else []


def _pairs(v):
    """`a~met,b~absent` -> [{"value": "a", "verdict": "met"}, ...]"""
    out = []
    for part in _list(v):
        if "~" in part:
            val, _, verd = part.partition("~")
            out.append({"value": val, "verdict": verd})
    return out


def _conds(v):
    """`slot=value,slot=value` -> [{"slot": ..., "value": ...}]"""
    out = []
    for part in _list(v):
        if "=" in part:
            slot, _, val = part.partition("=")
            out.append({"slot": slot, "value": val})
    return out


def _codes(v):
    out = {}
    for part in _list(v, "|"):
        if "=" in part:
            k, _, val = part.partition("=")
            out[k] = val
    return out


def _el_attrs(el, spec):
    """One element's attributes, cast per `spec`, omitting what it does not carry."""
    rec = {}
    for name, key, cast in spec:
        raw = el.get(name)
        if raw is None:
            continue
        val = cast(raw) if cast else raw
        # THE ATTRIBUTE WAS WRITTEN, SO IT IS PART OF THE RECORD. An empty value
        # that was emitted means the source declared it empty -- `codes: {}` is
        # not the same as a row with no codes at all -- and the emitter only
        # writes what the source declared.
        if val is _Declared:
            rec[key] = None
        elif val is not None:
            rec[key] = val
    return rec


def as_view_items(path: str | None = None) -> list[dict]:
    """The rubric as `config(h)["rubric"].ITEMS` serves it, in rubric order."""
    p = path or staged_path()
    with open(p, encoding="utf8") as fh:
        text = _COMMENT.sub("", fh.read())
    root = ET.fromstring(text)
    items = []
    for el in root.iter("Item"):
        iid = el.get("scores")
        if not iid:
            continue
        conds = set(_list(el.get("conditions"), "|"))
        params = dict(kv.split("=", 1) for kv in _list(el.get("params"), "|")
                      if "=" in kv)
        it: dict = {"id": iid}
        if el.get("max") is not None:
            it["max"] = _num(el.get("max"))
        if el.get("label"):
            it["label"] = el.get("label")
        if el.get("increment") is not None:
            it["increment"] = _num(el.get("increment"))
        if el.get("deriveFromCredit") in _TRUE:
            it["derive_from_credit"] = True
        if el.get("deriveFromClauses") in _TRUE:
            it["derive_from_criteria"] = True
        if el.get("blankCode"):
            it["blank_code"] = el.get("blankCode")
        if el.get("expectedType"):
            it["expected_type"] = el.get("expectedType")
        # WHAT THE ITEM IS ASKED THROUGH, and which rule scores it. Both were in
        # `declaration_source.BLOCKS` until 3b, where the component-to-item link
        # was written a second time and agreed with `prompt_action` only by habit.
        if el.get("asks"):
            it["asks"] = el.get("asks")
        if el.get("grading"):
            it["grading"] = el.get("grading")
        # THE PATTERN THIS ITEM WAS BUILT FROM. Items sharing a family share slot
        # NAMES, so those names must mean the same thing across it -- which is a
        # fact about the item, not a list an enforcement module should hold.
        if el.get("family"):
            it["family"] = el.get("family")
        # PRESENT-BUT-EMPTY IS NOT ABSENT. Q4a carries `unreachable_codes: []`,
        # and an item that omits the key is a different item from one that
        # declares it holds none.
        if el.get("unreachableCodes") is not None:
            it["unreachable_codes"] = _list(el.get("unreachableCodes"))
        # the named booleans, recovered from the conditions they were written as
        for flag in ("avoidance_scores", "graph_item", "move_pick",
                     "reads_utb_choice",
                     "gold_from_deductions"):
            if flag in conds:
                it[flag] = True
        if params.get("cadence"):
            it["cadence"] = params["cadence"]
        q = el.find("Question")
        it["question"] = _text(q) if q is not None else ""
        it["credit"] = [
            dict(_el_attrs(c, [("what", "what", None), ("pts", "pts", _num),
                               ("rule", "rule", None),
                               ("reported", "reported", lambda v: v in _TRUE),
                               ("verdicts", "verdicts", lambda v: _list(v, "|")),
                               ("free", "free", lambda v: _list(v, "|")),
                               ("gates", "gates", lambda v: v in _TRUE),
                               ("codes", "codes", _codes)]),
                 **({"desc": _text(c)} if _text(c) else {}))
            for c in el.findall("Credit")]
        it["deductions"] = [
            dict(_el_attrs(d, [("code", "code", None), ("pts", "pts", _num),
                               ("repeatable", "repeatable",
                                lambda v: v in _TRUE)]),
                 **({"text": _text(d)} if _text(d) else {}))
            for d in el.findall("Deduction")]
        it["guidance"] = [_text(g) for g in el.findall("Guidance")
                          if not g.get("use")]
        counts = [_el_attrs(c, [("key", "key", None),
                                ("slots", "slots", _list)])
                  for c in el.findall("Counts")]
        if counts:
            it["counts"] = counts
        it["context"] = [c.get("item") for c in el.findall("Context")
                         if c.get("item")]
        for tag, key, spec in (
            ("Map", "maps", [("key", "key", None), ("pick", "pick", None),
                             ("pairs", "pairs", _pairs),
                             ("fallback", "fallback", None)]),
            ("Forbid", "forbid", [("key", "key", None),
                                  ("conds", "conds", _conds)]),
            ("Expect", "expect", [("key", "key", None), ("left", "left", None),
                                  ("value", "value", None),
                                  ("lenient", "lenient", lambda v: _list(v, "|"))]),
            ("Equals", "equals", [("key", "key", None), ("left", "left", None),
                                  ("right", "right", None),
                                  ("lenient", "lenient", lambda v: _list(v, "|"))]),
            ("Onlyif", "onlyif", [("key", "key", None), ("cond", "cond", None)]),
            ("Requires", "requires", [("key", "key", None), ("cond", "cond", None),
                                      ("lenient", "lenient", lambda v: _list(v, "|"))]),
            ("Derived", "derived", [("key", "key", None), ("kind", "kind", None),
                                    ("fields", "fields", _list),
                                    ("words", "words", _list),
                                    ("template", "template", json.loads)]),
            ("Cover", "cover", [("checks", "keys", _list),
                                ("labels", "labels", _list),
                                ("item", "of", None),
                                ("verdicts", "verdicts", lambda v: _list(v, "|"))]),
        ):
            rows = [_el_attrs(e, spec) for e in el.findall(tag)]
            if rows:
                it[key] = rows
        # AN OC_GATE IS A SLOT THAT CHARGES, not merely one that gates. 60 slots
        # carry `gate`; 5 carry a code and a reason. Collecting on `gate` alone
        # invented a gate on 15 items with `code: null`.
        gates = [{"key": s.get("key"), "code": s.get("charge"),
                  "text": s.get("because")}
                 for s in el.findall("Slot")
                 if s.get("gate") in _TRUE and s.get("charge")]
        if gates:
            it["oc_gates"] = gates
        items.append(it)
    return items


def as_view_slot_spec(path: str | None = None) -> dict:
    """`SLOT_SPEC` as the view serves it: {item: [{key, label, seg, pts}]}."""
    p = path or staged_path()
    with open(p, encoding="utf8") as fh:
        root = ET.fromstring(_COMMENT.sub("", fh.read()))
    out = {}
    for el in root.iter("Item"):
        iid = el.get("scores")
        if not iid:
            continue
        rows = []
        for s in el.findall("Slot"):
            rec = {"key": s.get("key")}
            for a in ("label", "seg", "pts"):
                if s.get(a) is not None:
                    rec[a] = s.get(a)
            if s.get("gate") in _TRUE:
                rec["gate"] = True
            rows.append(rec)
        if rows:
            out[iid] = rows
    return out


def as_view_notes(conditions=(), path: str | None = None) -> dict:
    """The shared note store: `{slot key: text}`, from `<Frame name="note:KEY">`.

    WHAT A NOTE IS, and why it is not the slot's `rule`. They sit at different
    heights in one precedence -- `rule` is what BOTH graders are told, a note is
    what a checklist-style grader is told where the credit rule does not already
    say, and `desc` is the fallback. Promoting a note to `rule` would put text in
    front of a grader that has never seen it, which is a scoring change wearing a
    refactor's clothes. This moves where a note is STORED and nothing else.

    NAMED, NOT COPIED PER SLOT. Measured on this corpus: 28 notes cover 102 slot
    sites -- `confident` alone is reached by 23 -- so resolving them into the
    slots would write 102 copies of 28 texts, and every copy is a place the next
    edit can miss. A slot that needs its own wording carries `note="..."`; one
    that shares carries `note="@name"`, the same two forms `verdicts` takes.

    ITEM-SCOPED KEYS KEEP THEIR SHAPE. `Q6:state_a1` is stored under that exact
    name, so the lookup order the prompt already uses -- item-scoped, then bare --
    needs no translation and no new rule.
    """
    p = path or expanded_path()
    with open(p, encoding="utf8") as fh:
        root = ET.fromstring(_COMMENT.sub("", fh.read()))
    have = set(conditions or ())
    out = {}
    for fr in root.iter("Frame"):
        name = fr.get("name") or ""
        if not name.startswith("note:"):
            continue
        parts = []
        for seg in fr.findall("Segment"):
            # SAME SELECTION RULE AS A FRAME'S, because a note IS one -- the
            # store is `<Frame>` precisely so a note can carry a clause that
            # belongs only where a condition holds, instead of a second copy of
            # the note with the clause removed by hand.
            cond = seg.get("ifDeclared")
            if cond:
                negated = cond.startswith("!")
                if (cond[1:] if negated else cond) in have:
                    if negated:
                        continue
                elif not negated:
                    continue
            parts.append("".join(seg.itertext()))
        out[name[5:]] = "".join(parts)
    return out


def as_view_fragments(path: str | None = None) -> dict:
    """The prompt's own prose: `{key: text}`, from `<Frame name="fragment:KEY">`.

    THE SAME MOVE THE NOTES MADE, for the same reason. These are the section
    headings and standing sentences a prompt body is built from -- "## Credit
    components", "## The checklist to return", the DO-NOT-ANSWER notices. They sat
    as literals in `olx_prompts.py`, which is course wording inside a prompt
    generator, and lo-blocks' assembler had already reached the conclusion from
    the other side: it takes them as `fragments` and REFUSES TO DEFAULT THEM,
    because "the KEYS are engine concepts; the WORDS are not".

    NO CONDITIONS HERE, deliberately. A note carries clauses that belong only
    where a condition holds; a fragment is one string and every caller wants all
    of it. Reading `ifDeclared` would invent a selection rule no fragment uses and
    make the store answer differently depending on who asked.

    `{name}` IS LEFT UNSUBSTITUTED. Filling a parameter needs the item, and this
    is a store, not a renderer -- `frag()` on the TS side and `_frag()` on this
    one do the substitution, and both leave a brace alone when no name is
    supplied rather than half-filling it.
    """
    p = path or expanded_path()
    with open(p, encoding="utf8") as fh:
        root = ET.fromstring(_COMMENT.sub("", fh.read()))
    out = {}
    for fr in root.iter("Frame"):
        name = fr.get("name") or ""
        if name.startswith("fragment:"):
            out[name[len("fragment:"):]] = "".join(
                "".join(seg.itertext()) for seg in fr.findall("Segment"))
    return out


def as_view_frame(name: str = "oc_frame", conditions=(), params=None,
                  path: str | None = None) -> str:
    """A named frame, assembled for one item: its segments, in order.

    `ifDeclared` SELECTS, and `!` inverts -- the same rule lo-blocks'
    `renderFrame` applies, and deliberately the same spelling, because two
    implementations of one selection rule is what the rubric model exists to
    prevent. What a condition MEANS is never known here: it is a name the caller
    declares, matched literally.

    NOTHING IS STRIPPED. A segment is spliced between two others and the space
    before "This never changes..." is what joins it to the sentence in front --
    which is the reason `Segment` uses lo-blocks' RAW text parser, recorded in
    `Segment.ts`. Trimming here would close that gap and make byte-exact prose
    impossible, silently, in the one place nothing else checks.

    IT READS THE EXPANDED ARTIFACT by default, like every other reader here:
    `expanded_path` carries why the authored file and the staged copy are each
    wrong for a scorer.

    `params` substitutes `{name}` -- and only names actually supplied, so prose
    that happens to contain a brace is left alone rather than half-substituted.
    """
    p = path or expanded_path()
    with open(p, encoding="utf8") as fh:
        root = ET.fromstring(_COMMENT.sub("", fh.read()))
    have = set(conditions or ())
    out = []
    for fr in root.iter("Frame"):
        if fr.get("name") != name:
            continue
        for seg in fr.findall("Segment"):
            cond = seg.get("ifDeclared")
            if cond:
                negated = cond.startswith("!")
                if (cond[1:] if negated else cond) in have:
                    if negated:
                        continue
                elif not negated:
                    continue
            out.append("".join(seg.itertext()))
    text = "".join(out)
    for k, v in (params or {}).items():
        text = text.replace("{" + k + "}", v)
    return text


if __name__ == "__main__":
    import sys
    d = load(sys.argv[1] if len(sys.argv) > 1 else None)
    print(f"{len(d)} items")
    for k in sorted(d):
        print(f"  {k:<6} {len(d[k]['slots']):>3} slots  "
              f"{len(d[k]['credit']):>3} credit  {len(d[k]['deductions']):>3} deductions")
