#!/usr/bin/env python3
"""The shape space an intake program must target: every lo-blocks block, classified.

WHY THIS EXISTS. §10.6.1 item 1. A generic fixture has to be "sized by shape
coverage", and until now that phrase had no denominator: nobody had enumerated the
shapes an item -- or the course holding it -- can take. This produces that
denominator, and it is a measurement of lo-blocks, not of psychology. It needs no
migration, no course file and no gold; it needs a lo-blocks checkout.

THE REGISTRY IS THE SOURCE, NOT THE DIRECTORY TREE. A first census of this space
read `grading/` and `input/` as though they were the population and got 122
blocks, missing twelve -- including `Course`, the top-level structural block, and
`SlotSheetGrader` itself. `SortableGrader`, `MatchingGrader`, `TabularMCQGrader`
and `CheckboxGrader` live beside their inputs rather than in `grading/`;
`TextSelectionInput` and `Freewrite` live under `language-arts/`; `CodeInput`
under `authoring/`; and eight graders register under a `createGrader({base:})`
name that no grep for `name: '...Grader'` will ever see. Directory structure is
not a census, so this reads `blockMetadataAutogen.json` -- the registry the build
generates -- and treats it as the population.

THAT REGISTRY IS A BUILD ARTIFACT, so it can be stale, and a stale artifact has
cost this project 19 observations once already. `--check-fresh` refuses when any
component source is newer than the registry.

WHAT IT CANNOT TELL YOU, stated because a coverage number that hides a gap is
worse than no number. **No grader declares which inputs it pairs with.** A grader
declares `inputType` (`single`/`list`) or `slots` (dict mode) and whether it
`infer`s its inputs from its children; compatibility with a given input is a
question of the value schema plus authoring convention, and the convention is
written in prose. So this inventory records both sides' schemas and REFUSES to
invent the pairing: an intake program has to decide it, and the decision is not
derivable from declarations alone.
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

# Roles, and the evidence that assigns each. Ordered: the first match wins, so
# the more specific rules come first. Every rule carries WHY, because a
# classifier whose reasons are not written down becomes a list nobody can check.
ROLE_RULES = [
    ("grader",
     "scores a response: registers as *Grader, or is built by createGrader"),
    ("gradable_input",
     "collects a response: declares `...input(...)`, so it holds a student value"),
    ("item_part",
     "a piece an item is built FROM, not an item: Key, Distractor and the "
     "Simple* authoring shorthands are parsed by their parent"),
    ("action",
     "item BEHAVIOUR rather than structure -- the path by which a response is "
     "produced, scored or revealed (LLMAction feeds SlotSheetGrader this way)"),
    ("structure",
     "carries other blocks: an item is reached THROUGH it, so an intake program "
     "must choose it from the teacher's materials like any other shape"),
    ("display",
     "presents text, media or feedback; holds no response of its own"),
    ("not_intake",
     "the authoring environment or a test block -- never course content, and "
     "knowing that is itself an inference the intake program must encode"),
]

# Category -> role, for blocks whose role is decided by where they live rather
# than by what they declare. `input` is absent on purpose: a block under input/
# is a gradable input only if it DECLARES one, and Key/Distractor do not.
CATEGORY_ROLE = {
    "action": "action",
    "layout": "structure",
    "scenario": "structure",
    "specialized": "structure",
    "reference": "structure",
    "media": "display",
    "display": "display",
    "utility": "display",
    "authoring": "not_intake",
    "_test": "not_intake",
}

ITEM_PARTS = {"Key", "Distractor", "SimpleMatching", "SimpleSortable",
              "SimpleTextSelection", "CapaFooter", "MainPane", "Sidebar"}

# Blocks whose role the rules above cannot decide, each named with its reason.
# An UNCLASSIFIED block is a refusal, never a default -- a classifier that
# silently bins the unknown reports full coverage of a space it never saw.
ROLE_OVERRIDES = {
    "Course": ("structure", "the top-level course container"),
    "CapaProblem": ("gradable_item_family",
                    "a self-contained Open edX-style problem carrying its own "
                    "inputs and grading"),
    "MarkupProblem": ("gradable_item_family",
                      "a self-contained problem family, as CapaProblem"),
    "Correctness": ("grading_support", "grading machinery, not itself a grader"),
    "DerivedChecks": ("grading_support", "grading machinery, not itself a grader"),
    "Rule": ("grading_support", "a RulesGrader rule, not a grader"),
    "ScoreTable": ("grading_support", "presents grading output"),
    "SheetValue": ("grading_support", "reads a value out of a graded sheet"),
    "Annotate": ("gradable_input",
                 "collects student annotations; its value is a response even "
                 "though it declares no `input(`"),
    "WordUsage": ("display", "language-arts presentation"),
    "WritingRhythmPlot": ("display", "plots a student's writing, does not collect"),
    "TextBlock": ("display", "text"),
    "TalkBubble": ("display", "scenario dialogue presentation"),
    "TeamDirectory": ("display", "presents team membership"),
    "SharedNotes": ("structure", "shared workspace other blocks are reached in"),
    "ServerPoll": ("action", "fetches state; behaviour, not structure"),
    "OnChange": ("action", "a trigger"),
    "OnShow": ("action", "a trigger"),
    "Trigger": ("action", "a trigger"),
    "StubBlock": ("not_intake", "a placeholder the registry creates for markers"),
}

_NAME = re.compile(r"name:\s*'([A-Za-z_][A-Za-z0-9_]*)'")
_BASE = re.compile(r"base:\s*'([A-Za-z_][A-Za-z0-9_]*)'")
_ATTR = re.compile(r"(\w+):\s*z_?\w*[\w.()]*?\.describe\(\s*['\"`](.*?)['\"`]", re.S)


def _registry_path(lo: str) -> str:
    return os.path.join(lo, "packages", "shared", "components",
                        "blockMetadataAutogen.json")


def load_registry(lo: str) -> dict:
    path = _registry_path(lo)
    if not os.path.exists(path):
        raise SystemExit(
            f"shape_inventory: no built block registry at {path}.\n"
            f"It is generated by the lo-blocks build and is not committed, so a "
            f"fresh checkout has none. Build lo-blocks, or point --lo-blocks at a "
            f"built tree. Reading the DIRECTORY TREE instead is what produced a "
            f"census missing `Course` and `SlotSheetGrader`.")
    return json.load(open(path))["blocks"]


def staleness(lo: str, blocks: dict) -> list[str]:
    """Component sources newer than the registry that describes them."""
    reg = _registry_path(lo)
    if not os.path.exists(reg):
        return []
    cutoff = os.path.getmtime(reg)
    newer = []
    root = os.path.join(lo, "packages", "shared", "components", "blocks")
    for dp, _dn, fns in os.walk(root):
        for fn in fns:
            if fn.endswith(".ts") and not fn.endswith(".test.ts"):
                p = os.path.join(dp, fn)
                if os.path.getmtime(p) > cutoff:
                    newer.append(os.path.relpath(p, lo))
    return sorted(newer)


def _read(lo: str, rel: str) -> str:
    try:
        return open(os.path.join(lo, rel), errors="ignore").read()
    except OSError:
        return ""


def describe(name: str, meta: dict, lo: str) -> dict:
    """One block's shape, from its own source."""
    rel = meta.get("source") or ""
    src = _read(lo, rel)
    parts = rel.split("/")
    cat = parts[4] if len(parts) > 5 else ""

    is_grader = name.endswith("Grader") or (
        "createGrader(" in src and name in (_BASE.sub(lambda m: m.group(1) + "Grader",
                                                      "") or name))
    if not is_grader and "createGrader(" in src:
        is_grader = any(b + "Grader" == name for b in _BASE.findall(src))
    # BOTH SPELLINGS. Most blocks write `...input({`, but `TabularMCQ` writes
    # `...blocks.input({`, and a pattern anchored on the first missed it: the
    # block then matched no rule at all and the run REFUSED -- the classifier
    # reporting its own blind spot instead of quietly binning it, which is the
    # behaviour the UNCLASSIFIED bucket exists for.
    declares_input = bool(re.search(r"\.\.\.input\(", src)
                          or re.search(r"\.\.\.\w+\.input\(", src))

    if name in ROLE_OVERRIDES:
        role, why = ROLE_OVERRIDES[name]
    elif is_grader:
        role, why = "grader", ROLE_RULES[0][1]
    elif declares_input:
        role, why = "gradable_input", ROLE_RULES[1][1]
    elif name in ITEM_PARTS:
        role, why = "item_part", ROLE_RULES[2][1]
    elif cat in CATEGORY_ROLE:
        role = CATEGORY_ROLE[cat]
        why = dict(ROLE_RULES)[role]
    else:
        role, why = "UNCLASSIFIED", f"no rule matched (category {cat!r})"

    rec = {"name": name, "role": role, "why": why, "category": cat,
           "source": rel,
           "authoring": {k: bool(meta.get(k))
                         for k in ("readme", "demo", "template", "examples")},
           "attributes": [{"attr": a, "describes": " ".join(d.split())[:160]}
                          for a, d in _ATTR.findall(src)]}

    if role == "grader":
        m = re.search(r"inputType:\s*'(\w+)'", src)
        rec["grades"] = {
            "input_type": m.group(1) if m else ("dict" if "slots:" in src else None),
            "infers_inputs_from_children": "infer: false" not in src,
            "creates_match_variant": "createMatch: false" not in src,
        }
    if role in ("gradable_input", "gradable_item_family"):
        m = re.search(r"valueSchema:\s*([^,\n]+)", src)
        rec["collects"] = {"value_schema": m.group(1).strip() if m else None}
    return rec


def inventory(lo: str) -> dict:
    blocks = load_registry(lo)
    recs = [describe(n, m, lo) for n, m in sorted(blocks.items())]
    by_role: dict[str, int] = {}
    for r in recs:
        by_role[r["role"]] = by_role.get(r["role"], 0) + 1
    return {"schema_version": SCHEMA_VERSION,
            "lo_blocks": os.path.abspath(lo),
            "blocks_registered": len(recs),
            "by_role": dict(sorted(by_role.items())),
            "stale_sources": staleness(lo, blocks),
            "pairing_is_not_declared":
                "No grader declares which inputs it pairs with. A grader declares "
                "inputType (single/list) or slots (dict), and whether it infers "
                "inputs from children; compatibility is a value-schema question "
                "plus authoring convention written in prose. An intake program "
                "must decide the pairing; it is not derivable from declarations.",
            "blocks": recs}


def course_coverage(inv: dict, olx_dir: str) -> dict:
    """Which shapes one course actually exercises -- the numerator."""
    used: dict[str, int] = {}
    if not os.path.isdir(olx_dir):
        return {"olx_dir": olx_dir, "present": False, "used": {}}
    names = [b["name"] for b in inv["blocks"]]
    pat = {n: re.compile(r"<%s\b" % re.escape(n)) for n in names}
    for dp, _dn, fns in os.walk(olx_dir):
        for fn in fns:
            if not fn.endswith(".olx"):
                continue
            text = open(os.path.join(dp, fn), errors="ignore").read()
            for n, rx in pat.items():
                if rx.search(text):
                    used[n] = used.get(n, 0) + 1
    return {"olx_dir": olx_dir, "present": True, "used": dict(sorted(used.items()))}


def self_test(lo: str) -> int:
    """Induce each failure mode and confirm it is caught.

    In the tool, not a scratch file. Two of these five caught defects in the tool
    rather than in lo-blocks: a namespaced `...blocks.input({` that the input
    detector missed, and -- the reason the UNCLASSIFIED bucket refuses rather
    than defaults -- the fact that the miss surfaced at all.
    """
    import shutil
    import tempfile

    print("  %-42s %s" % ("induced", "reported"))
    caught = 0
    cases = []

    def note(name, ok, detail=""):
        nonlocal caught
        caught += bool(ok)
        cases.append(name)
        print("  %-42s %s  %s" % (name, "caught" if ok else "MISSED", detail[:44]))

    # 1 no built registry at all
    with tempfile.TemporaryDirectory() as tmp:
        try:
            load_registry(tmp)
            note("no built registry", False)
        except SystemExit as exc:
            note("no built registry", "not committed" in str(exc))

    # 2 a source newer than the registry
    with tempfile.TemporaryDirectory() as tmp:
        comp = os.path.join(tmp, "packages", "shared", "components")
        os.makedirs(os.path.join(comp, "blocks", "x"))
        reg = os.path.join(comp, "blockMetadataAutogen.json")
        open(reg, "w").write(json.dumps({"blocks": {}}))
        os.utime(reg, (1, 1))
        open(os.path.join(comp, "blocks", "x", "New.ts"), "w").write("x")
        note("a source newer than the registry", bool(staleness(tmp, {})))

    # 3 a block no rule can place
    fake = {"source": "packages/shared/components/blocks/nowhere/Odd.ts"}
    rec = describe("Odd", fake, lo)
    note("a block no rule can place", rec["role"] == "UNCLASSIFIED", rec["why"])

    # 4 the namespaced input spelling is seen
    rec = describe("TabularMCQ", load_registry(lo)["TabularMCQ"], lo)
    note("a namespaced ...blocks.input({)", rec["role"] == "gradable_input",
         rec["role"])

    # 5 a createGrader block is a grader even without 'Grader' in its own name:
    #   SlotSheetGrader registers from `base: 'SlotSheet'`
    rec = describe("SlotSheetGrader", load_registry(lo)["SlotSheetGrader"], lo)
    note("a createGrader(base:) grader", rec["role"] == "grader", rec["role"])

    # 6 coverage counts only what an OLX actually uses
    with tempfile.TemporaryDirectory() as tmp:
        open(os.path.join(tmp, "a.olx"), "w").write("<TextArea id='x'/>")
        inv = {"blocks": [{"name": "TextArea"}, {"name": "Carousel"}]}
        cov = course_coverage(inv, tmp)
        note("coverage counts only what is used",
             set(cov["used"]) == {"TextArea"}, str(sorted(cov["used"])))

    print(f"\n  {caught}/{len(cases)} failure modes caught")
    return 0 if caught == len(cases) else 1


def main(argv=None) -> int:
    import paths

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lo-blocks", default=str(paths.LO))
    ap.add_argument("--course", default=None,
                    help="an OLX directory, to report which shapes it exercises")
    ap.add_argument("--json", metavar="PATH")
    ap.add_argument("--check-fresh", action="store_true",
                    help="refuse if any component source is newer than the registry")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test(args.lo_blocks)

    inv = inventory(args.lo_blocks)
    if args.course:
        inv["coverage"] = course_coverage(inv, args.course)

    print(f"  {inv['blocks_registered']} blocks registered in "
          f"{os.path.basename(inv['lo_blocks'])}\n")
    for role, n in inv["by_role"].items():
        print(f"    {role:<22} {n:>4}")

    unclassified = [b["name"] for b in inv["blocks"] if b["role"] == "UNCLASSIFIED"]
    attrs = sum(len(b["attributes"]) for b in inv["blocks"])
    with_attrs = sum(1 for b in inv["blocks"] if b["attributes"])
    print(f"\n  {attrs} declared attributes across {with_attrs} blocks "
          f"({inv['blocks_registered'] - with_attrs} declare none this reader can see)")

    cov = inv.get("coverage")
    if cov and cov["present"]:
        intake = [b for b in inv["blocks"] if b["role"] != "not_intake"]
        hit = [b for b in intake if b["name"] in cov["used"]]
        print(f"\n  course at {os.path.basename(cov['olx_dir'])} uses "
              f"{len(hit)} of {len(intake)} intake-target shapes "
              f"({100.0 * len(hit) / max(1, len(intake)):.0f}%)")
        for role in sorted({b["role"] for b in intake}):
            tot = [b for b in intake if b["role"] == role]
            got = [b for b in tot if b["name"] in cov["used"]]
            print(f"    {role:<22} {len(got):>3} of {len(tot):>3}")

    if args.json:
        json.dump(inv, open(args.json, "w"), indent=1)
        print(f"\n  written: {args.json}")

    if inv["stale_sources"] and args.check_fresh:
        print(f"\n  REFUSING: {len(inv['stale_sources'])} component source(s) are "
              f"newer than the registry that describes them. The registry is a "
              f"build artifact; rebuild lo-blocks.")
        for p in inv["stale_sources"][:5]:
            print(f"    {p}")
        return 2
    if unclassified:
        print(f"\n  REFUSING: {len(unclassified)} block(s) no rule could place. A "
              f"classifier that bins the unknown reports coverage of a space it "
              f"never saw.")
        for n in unclassified:
            print(f"    {n}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
