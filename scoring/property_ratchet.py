#!/usr/bin/env python3
"""T4.2 — the property ratchet: how much course SHAPE the flag vocabulary carries.

D1x-c's test is mechanical: *does any engine code branch on this value?* If yes
it is BEHAVIOUR and belongs in a strategy registry; a property is only for values
the engine never branches on. `boxes: 8` is a property — read and used, never
branched on. `series_box_holds` is a strategy, because the engine branches on it.

WHAT THIS GATES IS ACCUMULATION, NOT INSTANCES. A single branch on a property is
not a genericity defect: `if caps.boxes == 8:` reads a value and behaves
correctly, and a second course with six boxes works. Contrast `if item == "1c":`,
which no second course can satisfy — and T4.1 already catches that, as a literal
course id in code. The harm §10.1.1 names is different:

    the flag vocabulary then becomes the place where course shape accumulates

One flag is harmless. Forty narrow booleans — `derives_from_series`,
`needs_utb_gate`, `blank_code_applies` — mean the engine is course-shaped
again in a new vocabulary, and a second course must set flags it cannot
interpret. So the ratchet counts DISTINCT PROPERTIES REACHED IN A BRANCH: it may
fall, and may not rise without a declaration naming the new property and saying
why a strategy would not do.

IT IS NARROW, AND SAYS SO IN ITS OWN OUTPUT. Direct forms only — an attribute
access or a subscript of a declared property, inside a branch condition:

    if item["derives_from_series"]:      caught (truthiness)
    if not caps["blank_code"]:           caught (negation)
    if caps["boxes"] == 8:               caught (comparison)
    n = caps["boxes"]; ...; if n == 8:   NOT caught -- indirection
    if args.boxes:                       NOT matched -- an attribute, not a
                                         course property; see `_names_in`

Indirection is undecidable without dataflow analysis. **A gate that catches only
naive violations while announcing the rule enforced is worse than no gate**,
because it turns "be careful here" into "the check passed". So the blind spots
are printed with every failure, and D1x-c stays a design principle a reviewer
applies; this enforces the enforceable part and admits the rest.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import sys

import paths

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

SCHEMA_VERSION = 1
BUDGET = os.path.join(paths.SCORING_METADATA, "PROPERTY_BUDGET.json")

# Modules that may branch on a property, each with the reason.
EXEMPT = {
    "coursedata.py":
        "the reader MUST branch on properties -- it recomputes derived values and "
        "chooses accessor paths by field. Gating it would fail the one module that "
        "has to do this.",
    "rubric_h1.py": "rubric DATA, not engine code",
    "rubric_h2_source.py": "rubric DATA, not engine code",
    "rubric_h3.py": "rubric DATA, not engine code",
    "rubric_export.py":
        "the export decides what to carry BY field, which is branching on the "
        "vocabulary rather than on a course's shape",
    "property_ratchet.py": "this module names the properties in order to find them",
}

BLIND_SPOTS = (
    "indirection through a local (`n = caps.boxes` ... `if n == 8`)",
    "a property reached through a helper call (`if has(item, 'boxes')`)",
    "a dict built elsewhere and branched on here",
)


def properties() -> set[str]:
    """The declared property vocabulary: the reader's own field groups."""
    import coursedata

    return set(coursedata.RUBRIC_FIELDS) | set(coursedata.GENERATOR_FIELDS)


def _names_in(node: ast.AST, props: set[str]) -> set[str]:
    """Declared properties reached DIRECTLY inside this expression.

    SUBSCRIPTS ONLY, and that is a rule with a premise rather than a
    convenience. `coursedata` returns DICTS -- `items()` and `rubric_for()` hand
    back `_group(...)`, a dict copy -- so a course property is read as
    `item["credit"]` and never as `item.credit`. `premise_holds()` below checks
    that, because the rule is only sound while it is true.

    The first version matched attributes too and every attribute hit was a FALSE
    POSITIVE: `args.handout` (7 sites -- an argparse flag, not an item) and
    `node.value.id` / `t.id` (4 sites -- Python's own AST API, where `.id` is a
    `Name` node's identifier). 11 of 44 hits were the check matching a NAME
    rather than a course property, which would have baselined noise into the
    ratchet and let real growth hide inside its churn.
    """
    found = set()
    for sub in ast.walk(node):
        if isinstance(sub, ast.Subscript):
            key = sub.slice
            if isinstance(key, ast.Constant) and key.value in props:
                found.add(key.value)
    return found


def premise_holds() -> list[str]:
    """The reader still hands out dicts, so subscript-only is still sound."""
    try:
        import coursedata

        sample = coursedata.items()[:1]
    except Exception as exc:                      # pragma: no cover
        return [f"cannot check the reader's shape: {exc}"]
    if sample and not isinstance(sample[0], dict):
        return ["coursedata now returns %s, not dict -- this check matches "
                "SUBSCRIPTS only because a course property is read as "
                "item['field']. If items are objects now, attribute access is "
                "how they are read and this check has gone blind."
                % type(sample[0]).__name__]
    return []


def _engine_module_files():
    """Every engine module, wherever the split put it -- one list of record."""
    import paths as _p
    out = []
    for d in (_p.SCORING, _p.SCORING / "tools", _p.SCORERS_GENERAL, _p.SCORING_COURSE):
        try:
            out.extend(sorted(d.glob("*.py")))
        except OSError:
            continue
    return out


def scan(directory: str | None = None) -> dict:
    """-> {property: [sites]}. Branch conditions only."""
    props = properties()
    hits: dict[str, list[dict]] = {}
    scanned = 0
    # EVERY ENGINE DIRECTORY, not just this one. The scan listed a single
    # directory, so when the general scorers moved to `scorers/` and a course's
    # own modules to `scoring/<course>/` their branches left the ratchet -- and
    # a property that is no longer branched on ANYWHERE reads as a property that
    # was tightened, which is the one direction this ratchet is built to refuse.
    # Measured the day they moved: `guidance` reported as no longer branched.
    if directory is not None:
        _files = [os.path.join(directory, fn) for fn in sorted(os.listdir(directory))]
    else:
        _files = [str(p) for p in _engine_module_files()]
    for path in _files:
        fn = os.path.basename(path)
        if not fn.endswith(".py") or fn in EXEMPT:
            continue
        try:
            tree = ast.parse(open(path, errors="ignore").read())
        except SyntaxError:
            continue
        scanned += 1
        for node in ast.walk(tree):
            test = None
            if isinstance(node, (ast.If, ast.While, ast.IfExp)):
                test = node.test
            elif isinstance(node, ast.comprehension):
                for cond in node.ifs:
                    for name in _names_in(cond, props):
                        hits.setdefault(name, []).append(
                            {"file": fn, "line": getattr(cond, "lineno", 0),
                             "form": "comprehension"})
                continue
            if test is None:
                continue
            for name in _names_in(test, props):
                hits.setdefault(name, []).append(
                    {"file": fn, "line": getattr(test, "lineno", 0),
                     "form": type(test).__name__})
    return {"modules_scanned": scanned, "properties_declared": len(props),
            "branched": {k: v for k, v in sorted(hits.items())}}


def verify(found: dict) -> list[str]:
    """The ratchet: the count may fall, never rise without a declaration."""
    # PORTED (goal K), AS A SPLIT. Finding the branches means parsing PYTHON
    # SOURCE, so `scan()` stays; the RATCHET is three generic statements about
    # a vocabulary budget -- a new undeclared name, a count that rose, and an
    # entry nothing reaches any more -- and those move.
    #
    # THE BUDGET IS PASSED, NOT READ THERE. Reading it inside the rule made the
    # rule untestable without a filesystem: a fire test on "an entry nothing
    # branches on" could not be written, because the only way to mutate the
    # budget was to write the file. Passing it also lets the two read failures
    # stay findings -- a budget that cannot be read is not a budget that passes.
    import json
    import os

    import lo_enforce

    budget, err = None, None
    try:
        budget = json.loads(open(BUDGET).read())
    except FileNotFoundError:
        err = "missing"
    except ValueError as exc:
        err = str(exc)

    return lo_enforce.run("property_vocabulary_ratchet", {
        "branched": found["branched"],
        "budget": None if budget is None else {
            "branched": list(budget.get("branched", [])),
            "declared": dict(budget.get("declared", {}))},
        "budgetError": err,
        "budgetName": os.path.basename(BUDGET),
    })

def tighten(found: dict) -> int:
    names = sorted(found["branched"])
    try:
        old = json.loads(open(BUDGET).read())
    except (FileNotFoundError, ValueError):
        old = {}
    grew = sorted(set(names) - set(old.get("branched", names)))
    if old and grew:
        print(f"\n  REFUSING to tighten: these properties are NEWLY branched on, "
              f"and baselining a regression records history instead of enforcing "
              f"it: {', '.join(grew)}")
        return 2
    doc = {"_what": "D1x-c: declared properties reached in a branch condition. "
                    "Falls, never rises without a declaration.",
           "branched": names,
           "declared": old.get("declared", {})}
    open(BUDGET, "w").write(json.dumps(doc, indent=1) + "\n")
    print(f"\n  budget written: {os.path.basename(BUDGET)} "
          f"({len(names)} propert(ies) branched on)")
    return 0


def self_test() -> int:
    """Each form the check CLAIMS to catch, constructed here and exercised.

    A case using only `==` would pass while the check stayed blind to truthiness
    and subscripts -- T0.1's vacancy, one level up. The blind spot is asserted
    too: a check that quietly caught it would mean the docstring is wrong.
    """
    props = {"boxes", "blank_code", "derives_from_series"}
    cases = [
        ("comparison        `if c['boxes'] == 8:`",
         "if c['boxes'] == 8:\n    pass\n", {"boxes"}),
        ("truthiness        `if c['derives_from_series']:`",
         "if c['derives_from_series']:\n    pass\n", {"derives_from_series"}),
        ("negation          `if not c['blank_code']:`",
         "if not c['blank_code']:\n    pass\n", {"blank_code"}),
        ("subscript         `if c['boxes']:`", "if c['boxes']:\n    pass\n", {"boxes"}),
        ("ATTRIBUTE is not a property read `if args.boxes:`",
         "if args.boxes:\n    pass\n", set()),
        ("while             `while c['boxes']:`", "while c['boxes']:\n    pass\n", {"boxes"}),
        ("ternary           `x = 1 if c['boxes'] else 2`",
         "x = 1 if c['boxes'] else 2\n", {"boxes"}),
        ("comprehension     `[x for x in y if c['boxes']]`",
         "z = [x for x in y if c['boxes']]\n", {"boxes"}),
        ("NOT a branch      `n = c['boxes']`", "n = c['boxes']\n", set()),
        ("BLIND: indirection `n = c['boxes']; if n == 8:`",
         "n = c['boxes']\nif n == 8:\n    pass\n", set()),
    ]
    print("  %-46s %s" % ("form", "result"))
    ok = 0
    for label, src, want in cases:
        tree = ast.parse(src)
        got = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.IfExp)):
                got |= _names_in(node.test, props)
            elif isinstance(node, ast.comprehension):
                for cond in node.ifs:
                    got |= _names_in(cond, props)
        good = got == want
        ok += good
        print("  %-46s %s  %s" % (label, "ok" if good else "WRONG",
                                  sorted(got) or "-"))
    print(f"\n  {ok}/{len(cases)} forms behave as documented "
          f"(including the two that must NOT fire)")
    return 0 if ok == len(cases) else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dir", default=HERE)
    ap.add_argument("--json", metavar="PATH")
    ap.add_argument("--tighten", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    found = scan(args.dir)
    for bad in premise_holds():
        print(f"  REFUSING: {bad}")
        return 2
    print(f"  {found['properties_declared']} properties declared, "
          f"{len(found['branched'])} reached in a branch, across "
          f"{found['modules_scanned']} module(s)")
    for name, sites in sorted(found["branched"].items(),
                              key=lambda kv: -len(kv[1]))[:10]:
        where = ", ".join(sorted({s["file"] for s in sites}))[:58]
        print(f"    {name:<22} {len(sites):>3} site(s)  {where}")
    print(f"  {len(EXEMPT)} module(s) exempt: {', '.join(sorted(EXEMPT))}")

    if args.json:
        json.dump({"schema_version": SCHEMA_VERSION, **found},
                  open(args.json, "w"), indent=1)
        print(f"  written: {args.json}")
    if args.tighten:
        return tighten(found)

    bad = verify(found)
    if bad:
        print(f"\n  {len(bad)} FINDING(S):")
        for b in bad:
            print(f"    {b}")
        print("\n  This check is NARROW. It does not see:")
        for spot in BLIND_SPOTS:
            print(f"    - {spot}")
        return 1
    print("  the property vocabulary has not grown.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
