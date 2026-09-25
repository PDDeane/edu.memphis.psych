#!/usr/bin/env python3
"""T3.2 -- prove the READER serves what the incumbent modules hold, both ways.

T5.1 proves the FILE reproduces the modules. This proves the READER does. They
are different claims and a single tool cannot make both: a reader bug and an
export bug produce the same symptom, and only two proofs taken from different
sides tell them apart. So T5.1 reads the JSON directly and never imports this
reader; this one goes exclusively THROUGH the reader and never reads the JSON.
Between them they close the loop modules -> file -> reader.

WHY THE INVENTORY IS TAKEN BY REFLECTION AND NOT FROM T1.1
----------------------------------------------------------
This tool's design said to consume T1.1's table list rather than re-derive it,
on the reasoning that two inventories would eventually disagree. The reasoning
is right and the source was wrong. T1.1 answers "which tables EMBED COURSE IDS"
-- an embedding census, whose purpose is to bound the renaming work. This tool
needs "what does the module hold that must be carried" -- a completeness census.
They are not the same question and they do not have the same answer: for handout
2, T1.1 lists 15 tables where the module holds 27 names. `SLOT_OPTIONS` is
absent from T1.1 and IS carried by the export; `BY_ID` and `TOTAL` are absent
and are the two values the reader rebuilds. Consuming T1.1 would leave all three
unverified while the run reported success.

Nor does it borrow the export's own rule (`isupper() and not startswith("_")`).
That rule agrees with the export by construction, which means this tool would go
blind in exactly the places the export is blind -- a name the export overlooks
would have this tool confirm the oversight. A proof must not borrow the thing it
is proving.

So: every module-level name is enumerated here, independently, and every one of
them must be ACCOUNTED FOR -- either compared through the reader, or carrying a
written justification for why it needs no carriage. A name that is neither is a
FAILURE. That is what makes a table added later unable to pass in silence, and
it is what found `_HELD_BACK_RULE` (below) before this tool was finished.

BOTH DIRECTIONS, because the dangerous gap is the reader's
----------------------------------------------------------
Asking only "for each key the reader knows, does the module agree?" PASSES when
the reader is missing keys entirely -- and Stage 5 then deletes a module whose
contents were never carried across. A name the module has and the reader lacks
is therefore a FAILURE, not an absence.
"""
import argparse
import copy
import importlib
import json
import os
import sys
import types
import handouts as _handouts   # forms are declared by the course, not counted here

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

HANDOUTS = _handouts.declared()

# Names that need no carriage, each with the reason. Keyed by (handout, name):
# a new private name in a new module must be examined on its own, not inherit a
# justification written for a different one. An unjustified name FAILS.
JUSTIFIED = {
    ("*", "_it"):
        "loop variable left behind by an import-time `for _it in ITEMS:` "
        "post-processing loop. Not a table: it is the last item, and every item "
        "is already compared as part of ITEMS.",
    (2, "_EXPECT_SHIPPED"):
        "import-time scaffolding: folded into ITEMS[id]['expect'] before "
        "anything reads ITEMS, so its content is compared as part of the items.",
    (2, "_ONLYIF_SHIPPED"):
        "import-time scaffolding: folded into ITEMS[id]['onlyif'] before "
        "anything reads ITEMS, so its content is compared as part of the items.",
    (2, "_BARRIER_CONDS"):
        "authored conditions spliced into item `onlyif` clauses at import time; "
        "carried inside the item fields.",
    (2, "OC_FRAME"):
        "authored prose composed into item guidance at import time.",
    (2, "_EXAMPLE_RULES"):
        "authored prose composed into item guidance at import time.",
    (2, "_AUTHORED_RULE"):
        "authored prose composed into item guidance at import time.",
    (2, "_EXPECTS_RULE"):
        "authored prose composed into item guidance at import time.",
    (2, "_RESTRICTS_RULE"):
        "authored prose composed into item guidance at import time.",
    (2, "_MOVE_RULE"):
        "authored prose composed into item guidance at import time.",
}
# EMPTY, AND THE ENTRY THAT WAS HERE IS WHY THE SET STAYS. `_HELD_BACK_RULE` was
# reported dead by this tool and LEFT IN PLACE, on the principle that a
# migration tool is the wrong place to decide that authored text is dead. It was
# deleted from `rubric_h2.py` on 2026-09-19, by a person, after both claims
# behind the verdict were checked independently: no item uses the
# `held_back_is` slot it was written for, and its text appears in no handout's
# OLX. Reporting it and deleting it are different acts by different parties, and
# this tool still only does the first.
DEAD: set = set()

# Fields the EXPORT synthesises, which no module can hold. `handout` is the one:
# an item does not record which handout it belongs to because the module it is
# written in IS the handout, and that fact is lost the moment the items are
# pooled into one file. Declared here rather than quietly ignored -- and checked
# below for the RIGHT value, since an invented field is worth more scrutiny than
# a carried one, not less.
EXPORT_ADDED = {"handout": "synthesised by the export from the module of origin"}


def _justification(handout, name):
    return JUSTIFIED.get((handout, name)) or JUSTIFIED.get(("*", name))


def _canon(x):
    """Comparable form. Its own, deliberately.

    T5.1 has a canonicaliser too and this does not import it. A normaliser bug
    that flattened a difference would flatten it identically in both proofs, and
    the second proof exists precisely so that a single bug cannot pass both.
    """
    if isinstance(x, dict):
        return {str(k): _canon(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    if isinstance(x, (list, tuple)):
        return [_canon(v) for v in x]
    if isinstance(x, (set, frozenset)):
        return sorted(_canon(v) for v in x)
    if isinstance(x, float) and x == int(x):
        return int(x)
    return x


def _diff(a, b, path=""):
    """Paths at which two canonical values differ. A path, never just 'differs'."""
    out = []
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            p = f"{path}.{k}" if path else str(k)
            if k not in a:
                out.append(f"{p}: ONLY THROUGH THE READER")
            elif k not in b:
                out.append(f"{p}: ONLY IN THE MODULE -- the reader does not serve it")
            else:
                out.extend(_diff(a[k], b[k], p))
        return out
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(f"{path}: {len(a)} entries in the module, {len(b)} through the reader")
            return out
        for i, (x, y) in enumerate(zip(a, b)):
            out.extend(_diff(x, y, f"{path}[{i}]"))
        return out
    if a != b:
        out.append(f"{path}: module {a!r} != reader {b!r}")
    return out


def _strip_added(x):
    """The reader's side without the export's synthesised fields, at any depth.

    `handout` appears both on each item and inside the rebuilt BY_ID, so a
    shallow strip would clear the first and leave 26 copies of the second.
    """
    if isinstance(x, dict):
        return {k: _strip_added(v) for k, v in x.items() if k not in EXPORT_ADDED}
    if isinstance(x, list):
        return [_strip_added(v) for v in x]
    return x


def _module_names(mod):
    """Every module-level name that could be data. Imports and code excluded.

    `__future__` features are bound as ordinary lower-case names -- `from
    __future__ import annotations` leaves `annotations` in the module namespace,
    and it is an instance, so a type-based skip list does not catch it. It was
    reported as an unaccounted table on this tool's first run.
    """
    import __future__
    skip = (types.ModuleType, types.FunctionType, types.BuiltinFunctionType, type,
            __future__._Feature)
    return {n: v for n, v in vars(mod).items()
            if not n.startswith("__") and not isinstance(v, skip)}


def verify(handout, reader):
    """-> (compared, findings, accounted, ids). One handout.

    `compared` is COVERAGE, and a comparison over no data is not coverage --
    see the empty-pool rule below.
    """
    mod = importlib.import_module(f"rubric_h{handout}")
    names = _module_names(mod)
    findings, accounted, compared = [], {}, 0

    # ---- ITEMS, and every field in them -------------------------------------
    mod_items = list(getattr(mod, "ITEMS", []) or [])
    # KEYED BY ID, NOT FILTERED BY HANDOUT. Filtering by the handout field made
    # the check below unreachable: a wrong `handout` REMOVED the item from this
    # set, so it was reported as missing and the wrong value was never compared.
    # A check that cannot fail is not a check.
    served = {str(it["id"]): it for it in reader.items()}
    fields = reader.RUBRIC_FIELDS | reader.GENERATOR_FIELDS | set(EXPORT_ADDED)
    for it in mod_items:
        iid = str(it["id"])
        stray = sorted(set(it) - fields)
        if stray:
            findings.append(
                f"h{handout} item {iid}: field(s) {stray} belong to no declared "
                f"group -- the reader serves neither, so they would be lost")
        if iid not in served:
            findings.append(f"h{handout} item {iid}: IN MODULE, NOT SERVED BY THE READER")
            continue
        if served[iid].get("handout") != handout:
            findings.append(
                f"h{handout} item {iid}.handout: the export wrote "
                f"{served[iid].get('handout')!r}, but this item is in rubric_h{handout}")
        want = _canon({k: v for k, v in it.items()
                       if k in reader.RUBRIC_FIELDS and k not in EXPORT_ADDED})
        got = _canon(_strip_added(served[iid]))
        for d in _diff(want, got, f"h{handout} item {iid}"):
            findings.append(d)
        compared += 1
    accounted["ITEMS"] = f"compared as {len(mod_items)} items"
    module_ids = {str(it["id"]) for it in mod_items}
    migrated = module_ids & set(served)

    # ---- every other module-level name --------------------------------------
    for name, value in sorted(names.items()):
        if name == "ITEMS":
            continue
        if name.startswith("_") or not name.isupper():
            why = _justification(handout, name)
            if why is None:
                findings.append(
                    f"h{handout} {name}: UNACCOUNTED -- a module-level value that is "
                    f"neither served by the reader nor justified. Add it to the "
                    f"export, or justify it in JUSTIFIED.")
            else:
                accounted[name] = ("DEAD -- " if (handout, name) in DEAD else "") + why
            continue
        try:
            got = reader.derived(name, handout)
        except KeyError:
            findings.append(
                f"h{handout} {name}: IN MODULE, THE READER CANNOT SERVE IT. The "
                f"export did not carry it and no derivation rebuilds it.")
            continue
        for d in _diff(_canon(value), _canon(_strip_added(got)), f"h{handout} {name}"):
            findings.append(d)
        # AN EMPTY POOL IS NOT COVERAGE. `BY_ID` and `TOTAL` rebuild happily from
        # no items at all -- {} and 0 -- so counting them made coverage
        # permanently non-zero and the refusal below unreachable. With nothing
        # migrated this tool still reported "2 values compared" per handout.
        # Rebuilding a value from no inputs proves nothing about anything.
        # The pool that matters is the READER's, not the module's. Gating on
        # `mod_items` re-made the very bug this rule exists to fix: the modules
        # always have items, so the guard never fired and an unmigrated file
        # still reported coverage.
        if name in reader.DERIVATIONS and not migrated:
            accounted[name] = "NOT COUNTED: derived over an empty item pool"
            continue
        compared += 1
        accounted[name] = ("rebuilt by the reader" if name in reader.DERIVATIONS
                           else "carried as authored")

    # ---- the reverse direction: what the reader serves, the module lacks -----
    doc_authored = set()
    try:
        raw = reader._load()["handouts"].get(str(handout), {})
        doc_authored = set(raw.get("authored", {}))
    except Exception as exc:                      # pragma: no cover
        findings.append(f"h{handout}: could not enumerate the reader's own keys: {exc}")
    for name in sorted((doc_authored | set(reader.DERIVATIONS)) - set(names)):
        findings.append(
            f"h{handout} {name}: SERVED BY THE READER, ABSENT FROM THE MODULE "
            f"(a migration in progress, or a value invented by the export)")

    return compared, findings, accounted, module_ids


def not_yet_migrated(inventory_path):
    """What still has to come across. THIS is the question T1.1 answers."""
    if not inventory_path or not os.path.exists(inventory_path):
        return None
    inv = json.load(open(inventory_path))
    rubric = {f"rubric_h{h}.py" for h in HANDOUTS}
    return sorted(
        (m["module"], t["name"])
        for m in inv.get("modules", [])
        if m["module"] not in rubric
        for t in m.get("tables", []))


# ---------------------------------------------------------------------------
# NEGATIVE CONTROLS, IN THE TOOL. A proof that passes on its first run is exactly
# when to distrust it, and controls kept in a scratch file rot the moment the
# tool changes. Run with --self-test. Three of these nine caught defects in this
# tool rather than in the data: an unreachable `handout` check, a coverage
# counter that could never reach zero, and an empty-pool guard gated on the
# wrong side.
# ---------------------------------------------------------------------------
def _mutations():
    def scalar(d):
        for it in d["items"]:
            if it["id"] == "Q1":
                it["max"] = 99.0
    def nested(d):
        for it in d["items"]:
            if it["id"] == "Q1" and it.get("credit"):
                it["credit"][0]["pts"] = -1
    def drop_item(d):
        d["items"] = [it for it in d["items"] if it["id"] != "Q1"]
    def extra_item(d):
        e = copy.deepcopy(d["items"][0]); e["id"] = "ZZ9"; d["items"].append(e)
    def drop_authored(d):
        d["handouts"]["1"]["authored"].pop("MAPS")
    def wrong_handout(d):
        for it in d["items"]:
            if it["id"] == "Q1":
                it["handout"] = 3
    def empty(d):
        d["items"] = []; d["handouts"] = {}
    return [
        ("a changed scalar",             scalar,        "", "Q1.max"),
        ("a changed NESTED value",       nested,        "", "credit[0].pts"),
        ("an item dropped from export",  drop_item,     "", "NOT SERVED BY THE READER"),
        ("an item the modules lack",     extra_item,    "", "ABSENT FROM EVERY MODULE"),
        ("an authored value not carried",drop_authored, "", "CANNOT SERVE IT"),
        ("a wrong synthesised handout",  wrong_handout, "", "but this item is in rubric_h1"),
        ("a NEW public table",           None,
         "import rubric_h2 as _m;_m.NEW_TABLE={'a':1}\n", "CANNOT SERVE IT"),
        ("a NEW private table",          None,
         "import rubric_h2 as _m;_m._NEW_SCAFFOLD={'a':1}\n", "UNACCOUNTED"),
        ("nothing migrated at all",      empty,         "", "REFUSING"),
    ]


def self_test():
    import subprocess, tempfile
    import coursedata as reader
    base = json.load(open(os.path.abspath(reader.course_path())))
    print("  %-32s %s" % ("induced", "reported"))
    caught = 0
    cases = _mutations()
    for name, mutate, setup, want in cases:
        doc = copy.deepcopy(base)
        if mutate:
            mutate(doc)
        fh = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(doc, fh); fh.close()
        rep = fh.name + ".report"
        code = ("import sys;sys.path.insert(0,%r)\n" % HERE) + setup + (
            "import reader_equivalence as R;sys.exit(R.main(['--json',%r]))" % rep)
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True,
                              text=True, env=dict(os.environ, COURSE_FILE=fh.name))
        found = []
        if os.path.exists(rep):
            found = json.load(open(rep))["findings"]
        hit = [f for f in found if want in f] or ([want] if want in proc.stdout else [])
        ok = bool(hit) and proc.returncode != 0
        caught += ok
        print("  %-32s %s  rc=%d  %s" % (
            name, "caught" if ok else "MISSED", proc.returncode,
            (hit[0] if hit else "NOT CAUGHT")[:58]))
        for junk in (fh.name, rep):
            if os.path.exists(junk):
                os.unlink(junk)
    print(f"\n  {caught}/{len(cases)} failure modes caught")
    return 0 if caught == len(cases) else 1


def _modules_present() -> list:
    """Which rubric modules still exist. Stage 5 deletes h1 and h3.

    T3.2 compares the course file against the MODULES, so once they are gone
    it has no oracle and cannot run. It used to find that out as a
    ModuleNotFoundError traceback; the last run that still had an oracle is
    recorded in STAGE5_LICENCE.md, and that record is what licenses the
    deletion. Saying so is the difference between a retired tool and a broken
    one.
    """
    import os

    here = os.path.dirname(os.path.abspath(__file__))
    return [h for h in _handouts.declared()
            if os.path.exists(os.path.join(here, f"rubric_h{h}.py"))]


def main(argv=None):
    if not _modules_present():
        print("  the rubric modules are gone, so this tool has no oracle to "
              "compare against.\n  Its last run with one is recorded in "
              "STAGE5_LICENCE.md, and that run is what\n  licensed removing "
              "them. Nothing to do.")
        return 0

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", metavar="PATH", help="write the full report")
    ap.add_argument("--inventory", metavar="PATH",
                    help="T1.1 output, for the not-yet-migrated count")
    ap.add_argument("--self-test", action="store_true",
                    help="induce each failure mode and confirm it is caught")
    args = ap.parse_args(argv)

    if args.self_test:
        return self_test()

    import coursedata as reader

    total, all_findings, accounted = 0, [], {}
    all_module_ids = set()
    # ONLY THE HANDOUTS THAT STILL HAVE A MODULE. Stage 5 deletes h1 and h3 and
    # KEEPS h2, whose four builders A1c preserves -- so "all gone" and "all
    # present" are both easier than the state this actually lands in. Checking
    # for a total absence and otherwise iterating (1, 2, 3) crashed on exactly
    # the configuration Stage 5 produces.
    for h in _modules_present():
        compared, findings, acc, ids = verify(h, reader)
        total += compared
        all_findings.extend(findings)
        accounted[f"h{h}"] = acc
        all_module_ids |= ids

    # THE REVERSE DIRECTION IS ASKED ONCE, ACROSS ALL HANDOUTS. Asked per
    # handout it accused every handout of the other two handouts' items.
    # ONLY WHILE EVERY MODULE IS STILL THERE. "The reader serves an item no
    # module has" is a real finding when all three exist and a tautology once
    # Stage 5 deletes two of them -- it accused Q4c, Q5 and Q6 of being orphans
    # the moment rubric_h1.py went, which is the tool calling a successful
    # migration a defect.
    if len(_modules_present()) == 3:
        for iid in sorted({str(it["id"]) for it in reader.items()} - all_module_ids):
            all_findings.append(
                f"item {iid}: SERVED BY THE READER, ABSENT FROM EVERY MODULE")

    pending = not_yet_migrated(args.inventory)
    n_pending = "unknown (pass --inventory)" if pending is None else len(pending)

    print(f"  {total} values compared through the reader, "
          f"{n_pending} tables not yet migrated")
    n_just = sum(1 for a in accounted.values() for v in a.values()
                 if v.startswith(("loop variable", "import-time", "authored prose",
                                  "authored conditions", "DEAD")))
    print(f"  {sum(len(a) for a in accounted.values())} module-level names accounted for, "
          f"{n_just} by justification")
    for h, acc in accounted.items():
        dead = [n for n in acc if acc[n].startswith("DEAD")]
        if dead:
            print(f"  {h}: DEAD authored value(s) {dead} -- ships nowhere, carried by nothing")

    if args.json:
        json.dump({"compared": total, "findings": all_findings,
                   "accounted": accounted, "not_yet_migrated": pending},
                  open(args.json, "w"), indent=2, sort_keys=True)

    # ZERO COVERAGE CANNOT EXIT 0. During Stage 4 almost nothing is migrated, and
    # a run that compares nothing and exits 0 reads as "verified" -- T0.1's
    # vacancy defect wearing a new tool's name. A partial run is a legitimate
    # state; a partial run that looks complete is not.
    if total == 0:
        print("  REFUSING: nothing was compared. An empty comparison is not a proof.")
        return 2
    if all_findings:
        print(f"\n  {len(all_findings)} DIFFERENCE(S):")
        for f in all_findings:
            print(f"    {f}")
        return 1
    print("  EQUIVALENT: the reader serves exactly what the modules hold.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
