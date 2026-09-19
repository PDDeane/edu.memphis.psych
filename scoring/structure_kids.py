#!/usr/bin/env python3
"""WHAT EACH CONTAINER HOLDS — the structural half of the shape declaration.

The companion to `grader_inputs.py`, and it exists for the same reason: **no block
declares what it may contain.** There is no `childTags`, no `allowedChildren`, no
schema of permitted kids anywhere in lo-blocks. Containment is decided by each
block's PARSER and by its runtime, so the only way to know what a `Sequential`
holds is to read Sequentials that people wrote.

So containment is declared here and held to mined evidence in both directions.

FOUR MECHANISMS, and three of them are invisible to a scanner that only looks at
nesting. Measured across 319 `.olx` files:

1. **nested** — children are nested tags. `Vertical`, `Sequential`, `Collapsible`,
   `Hidden`, `NextReveal`, `TimedContainer`, `DynamicList`, `Tabs`, `Course`.
2. **slotted** — nested, but into NAMED REGIONS marked by stub blocks:
   `SideBarPanel` takes `MainPane` and `Sidebar`, which are markers parsed by the
   parent rather than components in their own right.
3. **referenced-body** — the body is a LIST OF IDS naming blocks defined
   elsewhere: `<Carousel wrap="true">ctt, irt, rasch</Carousel>`,
   `<MasteryBank goal="3">demo_q1 demo_q2 demo_q3</MasteryBank>`. These contain
   nothing syntactically, and a nesting-only scan reports them as childless --
   which is exactly what a first pass here did, calling `Carousel` and
   `MasteryBank` "never seen as a parent" while they appear in twelve files.
4. **referenced-attribute** — attributes name blocks by id: `Navigator
   preview="..." detail="..."`, and every grader's `target=`.

WHY THIS MATTERS TO THE INTAKE PROGRAM. Deciding a worksheet's three parts are
"one container" does not finish the job: the container has to be chosen, and the
choice determines whether the three parts are WRITTEN INSIDE it or written
separately and NAMED by it. A `Sequential` of three items and a `Carousel` of the
same three are different documents, not different attributes.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

SCHEMA_VERSION = 1
NESTED, SLOTTED, REF_BODY, REF_ATTR = ("nested", "slotted",
                                       "referenced-body", "referenced-attribute")

ITEM_ROLES = {"grader", "gradable_input", "gradable_item_family"}

# What each container holds. `holds` names ROLES, not block names: the intake
# program asks "can this hold an item?", and enumerating every permitted block
# would be a second inventory to keep in step with the first.
CONTAINERS: dict[str, dict] = {
    "AggregatedInputs": {
        "mechanism": REF_ATTR,
        "holds": [],
        "references": ['item'],
        "why": "reads other blocks' values and reports across them -- it"
               "NAMES the inputs it aggregates and nests none of them"},
    "AnswerDistribution": {
        "mechanism": REF_ATTR,
        "holds": [],
        "references": ['item'],
        "why": "reports how a cohort answered the item it names"},
    "Carousel": {
        "mechanism": REF_BODY,
        "holds": ['structure'],
        "references": ['display', 'structure'],
        "why": "its BODY is a comma- or newline-separated list of ids. It"
               "contains nothing syntactically, which is why a nesting-only"
               "scan called it childless across eight files"},
    "Chat": {
        "mechanism": NESTED,
        "holds": ['structure'],
        "references": ['item', 'structure'],
        "why": "turns and cast presentation, and it NESTS structure while"
               "REFERENCING the items a turn works on; the student's own"
               "responses are the Chat's value, not its children"},
    "Collapsible": {
        "mechanism": NESTED,
        "holds": ['action', 'display', 'item', 'structure'],
        "references": ['item'],
        "why": "a foldable region; items inside are optional detail"},
    "CompactPopout": {
        "mechanism": NESTED,
        "holds": ['display'],
        "references": [],
        "why": "an aside"},
    "Course": {
        "mechanism": NESTED,
        "holds": ['display', 'structure'],
        "references": [],
        "why": "the top level; carries sections, not items directly"},
    "DynamicList": {
        "mechanism": NESTED,
        "holds": ['item', 'structure'],
        "references": [],
        "why": "a repeating row the student can grow"},
    "Hidden": {
        "mechanism": NESTED,
        "holds": ['display', 'item', 'structure'],
        "references": [],
        "why": "present but not rendered until something reveals it -- which"
               "is where Navigator's template blocks are defined"},
    "IntakeGate": {
        "mechanism": NESTED,
        "holds": ['display', 'item', 'not_intake', 'structure'],
        "references": ['display', 'not_intake'],
        "why": "gates entry to what follows"},
    "LiquidTemplate": {
        "mechanism": NESTED,
        "holds": ['structure'],
        "references": [],
        "why": "templated presentation, and it wraps whole banks"},
    "MasteryBank": {
        "mechanism": REF_BODY,
        "holds": [],
        "references": ['item'],
        "why": "its body lists item ids and repeats them until `goal` is met"
               "-- a container whose contents are named, never nested"},
    "Navigator": {
        "mechanism": REF_ATTR,
        "holds": [],
        "references": ['display', 'item', 'structure'],
        "why": "`preview=` and `detail=` name template blocks by id, and its"
               "body carries its own YAML-ish entry list: data, not children"},
    "NextReveal": {
        "mechanism": NESTED,
        "holds": ['display', 'item', 'structure'],
        "references": [],
        "why": "one turn at a time, revealed on advance"},
    "Noop": {
        "mechanism": NESTED,
        "holds": ['display', 'structure'],
        "references": [],
        "why": "a transparent wrapper -- holds whatever it is given"},
    "Ref": {
        "mechanism": REF_ATTR,
        "holds": ['action', 'display', 'structure'],
        "references": ['action', 'display', 'grading_support', 'item', 'structure'],
        "why": "names blocks by id and renders their value. It HOLDS almost"
               "nothing and REFERENCES almost everything -- 431 TextArea"
               "references alone -- and it is the mechanism by which an"
               "LLMAction reads a response"},
    "Sequential": {
        "mechanism": NESTED,
        "holds": ['display', 'item', 'structure'],
        "references": [],
        "why": "ordered steps revealed one at a time"},
    "Cast": {
        "mechanism": NESTED,
        "holds": ['display', 'structure'],
        "references": [],
        "why": "declares characters as data, and nests the TeamDirectory that "
               "presents them -- found in a documented example, not in any .olx"},
    "SharedNotes": {
        "mechanism": NESTED,
        "holds": [],
        "references": [],
        "why": "a shared surface; UNDEMONSTRATED as a parent"},
    "SideBarPanel": {
        "mechanism": SLOTTED,
        "holds": [],
        "references": [],
        "slots": ['MainPane', 'Sidebar'],
        "why": "two named regions marked by MainPane and Sidebar, stub"
               "blocks the parent parses rather than components in their own"
               "right"},
    "SplitPanel": {
        "mechanism": SLOTTED,
        "holds": [],
        "references": [],
        "why": "two regions side by side; UNDEMONSTRATED as a parent in the"
               "corpora scanned"},
    "SplitTest": {
        "mechanism": REF_BODY,
        "holds": [],
        "references": [],
        "why": "selects among variants; UNDEMONSTRATED -- appears in no .olx"
               "in the corpora scanned"},
    "Tabs": {
        "mechanism": NESTED,
        "holds": ['action', 'display', 'structure'],
        "references": [],
        "why": "parallel pages; items sit inside the page bodies"},
    "TimedContainer": {
        "mechanism": NESTED,
        "holds": ['display', 'item', 'structure'],
        "references": [],
        "why": "content under a clock -- the reason Freewrite appears inside"
               "one"},
    "UseDynamic": {
        "mechanism": NESTED,
        "holds": ['structure'],
        "references": ['display', 'item'],
        "why": "renders dynamically-produced content, nesting structure and"
               "naming the items it fills in"},
    "UseHistory": {
        "mechanism": REF_ATTR,
        "holds": ['structure'],
        "references": ['display', 'item', 'structure'],
        "why": "names a block and renders that student's earlier values"},
    "Vertical": {
        "mechanism": NESTED,
        "holds": ['action', 'display', 'grading_support', 'item', 'item_part', 'not_intake', 'structure'],
        "references": [],
        "why": "the general-purpose page body -- the container that holds"
               "ANYTHING, and the one an intake program should default to"
               "when nothing more specific is implied"},
}

# Structural blocks that hold nothing: instruments and presentational leaves.
LEAF_STRUCTURE = {
    "AvatarEditor": "an editor; its value is the figure, not children",
    "CastEditor": "an editor",
    "CharacterBuilder": "an editor",
    "DigitSpanTask": "an instrument",
    "PEGDevBlock": "a development block",
    "NavigatorDefaultPreview": "a Navigator template, named by attribute",
    "NavigatorDefaultDetail": "a Navigator template",
    "NavigatorReadingDetail": "a Navigator template",
    "NavigatorTeamPreview": "a Navigator template",
    "NavigatorTeamDetail": "a Navigator template",
}

_TAG = re.compile(r"<(/?)([A-Za-z][A-Za-z0-9_]*)([^>]*?)(/?)>", re.S)
_ID = re.compile(r'\bid\s*=\s*"([^"]+)"')


def mine(roots: list[str], inventory: dict) -> dict:
    """Nesting edges and reference edges, over the corrected corpus.

    See `olx_corpus`: build artifacts out, the 295 documented examples in. The
    first version of this globbed `*.olx` and mined the psych course twice.
    """
    import olx_corpus

    role = {b["name"]: b["role"] for b in inventory["blocks"]}
    known = set(role)
    nested: dict[str, dict] = {}
    referenced: dict[str, dict] = {}
    seen_parents: set[str] = set()
    files = 0
    for label, text in olx_corpus.texts(roots):
        files += 1
        owner = {}
        for m in _TAG.finditer(text):
            if m.group(1) or m.group(2) not in known:
                continue
            got = _ID.search(m.group(3) or "")
            if got:
                owner[got.group(1)] = m.group(2)
        stack = []
        for m in _TAG.finditer(text):
            close, name, attrs, selfclose = m.groups()
            if close:
                while stack and stack.pop() != name:
                    pass
                continue
            if stack and name in known and stack[-1] in known:
                rec = nested.setdefault(f"{stack[-1]}|{name}", {"n": 0, "files": set()})
                rec["n"] += 1
                rec["files"].add(label)
                seen_parents.add(stack[-1])
            if name in known:
                for val in re.findall(r'"([^"]+)"', attrs or ""):
                    for tok in re.split(r"[,\s]+", val.strip()):
                        if tok in owner and owner[tok] != name:
                            rec = referenced.setdefault(f"{name}|{owner[tok]}",
                                                        {"n": 0, "files": set()})
                            rec["n"] += 1
                            rec["files"].add(label)
                            seen_parents.add(name)
                if not selfclose:
                    end_at = text.find(f"</{name}>", m.end())
                    body = text[m.end():end_at] if end_at > 0 else ""
                    if "<" not in body:
                        for tok in re.split(r"[,\s]+", body.strip()):
                            if tok in owner and owner[tok] != name:
                                rec = referenced.setdefault(f"{name}|{owner[tok]}",
                                                            {"n": 0, "files": set()})
                                rec["n"] += 1
                                rec["files"].add(label)
                                seen_parents.add(name)
            if not selfclose:
                stack.append(name)
    for d in (nested, referenced):
        for rec in d.values():
            rec["files"] = sorted(rec["files"])
    return {"files_scanned": files, "nested": nested, "referenced": referenced,
            "parents": sorted(seen_parents)}


def _role_of(child: str, role: dict) -> str:
    r = role.get(child, "")
    return "item" if r in ITEM_ROLES else r


def verify(inventory: dict, ev: dict) -> list[str]:
    role = {b["name"]: b["role"] for b in inventory["blocks"]}
    structural = {n for n, r in role.items() if r == "structure"}
    out = []

    for n in sorted(structural - set(CONTAINERS) - set(LEAF_STRUCTURE)):
        out.append(f"{n} is structural and neither CONTAINERS nor LEAF_STRUCTURE "
                   f"says what it holds -- an intake program choosing it needs to "
                   f"know whether content goes INSIDE it or is named BY it")
    for n in sorted(set(CONTAINERS) & set(LEAF_STRUCTURE)):
        out.append(f"{n} is declared both as a container and as a leaf")
    for n in sorted((set(CONTAINERS) | set(LEAF_STRUCTURE)) - set(role)):
        out.append(f"{n} is declared here but the inventory does not know it")

    for key, rec in sorted(ev["nested"].items()):
        parent, child = key.split("|")
        if parent not in CONTAINERS:
            if parent in LEAF_STRUCTURE:
                out.append(f"{parent} is declared a LEAF but NESTS {child} in "
                           f"{rec['n']} place(s) ({rec['files'][0]})")
            continue
        if child in (CONTAINERS[parent].get("slots") or []):
            continue
        kind = _role_of(child, role)
        if kind and kind not in CONTAINERS[parent]["holds"]:
            out.append(f"{parent} NESTS a {kind} ({child}) in {rec['n']} place(s) "
                       f"({rec['files'][0]}) and declares holds="
                       f"{CONTAINERS[parent]['holds']}")

    # REFERENCE IS NOT CONTAINMENT, and conflating them made `Ref` look like the
    # biggest container in the corpus: 431 TextAreas "inside" a block that holds
    # nothing and points at everything. The two relations are checked against
    # their own declarations.
    for key, rec in sorted(ev["referenced"].items()):
        parent, child = key.split("|")
        if parent not in CONTAINERS:
            if parent in LEAF_STRUCTURE:
                out.append(f"{parent} is declared a LEAF but REFERENCES {child} "
                           f"in {rec['n']} place(s) ({rec['files'][0]})")
            continue
        kind = _role_of(child, role)
        if kind and kind not in CONTAINERS[parent].get("references", []):
            out.append(f"{parent} REFERENCES a {kind} ({child}) in {rec['n']} "
                       f"place(s) ({rec['files'][0]}) and declares references="
                       f"{CONTAINERS[parent].get('references', [])}")
    return out


def main(argv=None) -> int:
    import paths

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--inventory", default=os.path.join(HERE, "SHAPE_INVENTORY.json"))
    ap.add_argument("--corpus", action="append", default=None)
    ap.add_argument("--json", metavar="PATH")
    args = ap.parse_args(argv)

    if not os.path.exists(args.inventory):
        raise SystemExit(f"structure_kids: no shape inventory at {args.inventory}")
    inv = json.load(open(args.inventory))
    import olx_corpus
    roots = args.corpus or olx_corpus.default_roots()
    ev = mine(roots, inv)
    bad = verify(inv, ev)

    print(f"  {ev['files_scanned']} .olx scanned: {len(ev['nested'])} nesting "
          f"edges, {len(ev['referenced'])} reference edges")
    for mech in (NESTED, SLOTTED, REF_BODY, REF_ATTR):
        n = sum(1 for c in CONTAINERS.values() if c["mechanism"] == mech)
        print(f"    {mech:<22} {n} container(s)")
    print(f"  {len(CONTAINERS)} containers declared, {len(LEAF_STRUCTURE)} leaves")
    nests_item = sorted(n for n, c in CONTAINERS.items() if "item" in c["holds"])
    refs_item = sorted(n for n, c in CONTAINERS.items()
                       if "item" in c.get("references", []))
    print(f"  NESTS an item ({len(nests_item)}): {', '.join(nests_item)}")
    print(f"  REFERENCES an item ({len(refs_item)}): {', '.join(refs_item)}")
    undemo = sorted(n for n in CONTAINERS if n not in ev["parents"])
    print(f"  declared but UNDEMONSTRATED as a parent ({len(undemo)}): "
          f"{', '.join(undemo) or 'none'}")

    if args.json:
        json.dump({"schema_version": SCHEMA_VERSION, "containers": CONTAINERS,
                   "leaves": LEAF_STRUCTURE, "evidence": ev},
                  open(args.json, "w"), indent=1)
        print(f"  written: {args.json}")

    if bad:
        print(f"\n  {len(bad)} PROBLEM(S):")
        for b in bad:
            print(f"    {b}")
        return 1
    print("  the containment declaration and the evidence agree.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
