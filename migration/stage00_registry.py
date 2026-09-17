#!/usr/bin/env python3
"""Stage 00 · register the `rubric` sheet attribute in BOTH registries.

ADDING A SHEET ATTRIBUTE IS FOUR STEPS, NOT ONE, and each is guarded by a
different check (measured 2026-09-12 while adding `free=`, one finding per step
missed). This script performs the two ENGINE steps and refuses to perform the
other two:

  1. `primitives.json` -> `sheetAttributes`. The psych audit builds
     KNOWN_ACTION_ATTRS as `set(sheetAttributes) | {p["attr"] for p in
     primitives}`, so an unlisted attribute makes the audit BLIND to it and
     reports UNKNOWN ATTRIBUTE.
  2. The block's own zod schema in `LLMAction.ts`. Miss it and ATTRIBUTE NOT
     DECLARED IN THE BLOCK fires. Two registries, two repositories, neither
     implying the other.
  3. Seeding `rubric=` into the 26 tags -- CONTENT, a later stage, and only if
     §3.2's compact tag is adopted. NOT DONE HERE.
  4. The §7a demotion rule, which must land BEFORE any seeding or every seeded
     item is priced as STALE PROMPT at ~120 calls a side for a question that did
     not change. NOT DONE HERE.

O1 -- ACCEPTED AND IGNORED FOR A FULL STAGE. The engine must tolerate the
attribute before any content sets it, so this script VERIFIES that no `.olx`
carries `rubric=` and fails if one does.

O5 -- the docs move with the engine. `LLMAction.md`'s attribute table gains the
row in the same commit, because nothing else will notice it is missing.

C2 -- the description must stay content-neutral: no psychology word may enter
lo-blocks. The wording below names a rubric element, not a subject.

Usage:
    stage00_registry.py --lo-blocks DIR --apply    make the two engine edits
    stage00_registry.py --lo-blocks DIR           verify them (a gate)
"""
import argparse, json, re, sys
from pathlib import Path

ATTR = "rubricDef"
# Each literal but the last carries a trailing ` +`. Adjacent TS string literals
# with no operator between them are a SYNTAX ERROR, and the first version emitted
# exactly that -- eleven lines that read fine and would not compile. This is the
# class of defect §7b names: invisible by inspection, caught only by the suite.
DESC = (
    "'The rubric definition this sheet is generated FROM, as an element id — ' +\n"
    "      'e.g. \"q4b\". Its slots, verdicts and codes are one ' +\n"
    "      'projection of that definition; naming it lets a second consumer ' +\n"
    "      'derive its own projection from the same source instead of restating ' +\n"
    "      'it, so the two cannot drift. Named `rubricDef` and not `rubric` ' +\n"
    "      'because `rubric` is already an attribute of LLMGrader, where it ' +\n"
    "      'carries grading PROSE read by the model — the opposite kind of ' +\n"
    "      'value. Accepted and IGNORED until content sets it: the attribute ' +\n"
    "      'exists a full stage before anything relies on it, because the engine ' +\n"
    "      'and the content version separately and no step can land in both at ' +\n"
    "      'once.'"
)

DOC_ROW = ("| `rubricDef` | the rubric definition this sheet is generated FROM; "
           "lets a second consumer derive its own projection from the same source "
           "(distinct from `LLMGrader`'s `rubric`, which is grading prose) |")


def paths(root: Path) -> dict:
    return {
        "primitives": root / "packages/shared/lib/llm/primitives.json",
        "ts": root / "packages/shared/components/blocks/action/LLMAction.ts",
        "md": root / "packages/shared/components/blocks/action/LLMAction.md",
    }


def olx_setting_rubric(root: Path) -> list[str]:
    """O1: no content may set the attribute in the stage that introduces it.

    SCOPED TO `<LLMAction>` TAGS, and that is not pedantry. The first version
    grepped every `.olx` line for `rubric="` and reported an O1 VIOLATION on
    `LLMGrader.olx` -- which has carried a `rubric` attribute since long before
    this plan, meaning something else entirely (see NAME_COLLISION below). An
    attribute lives in ONE block's schema, so a check that ignores the tag is
    asking a different question than the invariant it claims to enforce.
    """
    hits = []
    for f in root.rglob("*.olx"):
        if "node_modules" in f.parts:
            continue
        text = f.read_text(errors="ignore")
        for m in re.finditer(r"<LLMAction\b[^>]*>", text, re.S):
            if re.search(rf'\b{ATTR}\s*=\s*"', m.group(0)):
                hits.append(f"{f.name}:{text[:m.start()].count(chr(10)) + 1}")
    return hits


NAME_COLLISION = """
DECIDED 2026-09-13: the attribute is `rubricDef`, NOT `rubric`.

`rubric` was already taken, by another block, with an incompatible meaning:

    LLMGrader.rubric     "Grading criteria the LLM applies" — free PROSE, read by
                         the MODEL as instructions.
    LLMAction.rubricDef  the rubric DEFINITION this sheet is generated from — an
                         element ID, read by the BUILD, never by the model.

Per-block zod schemas would have kept the collision compiling, so this was never
going to fail loudly; it would have failed a READER, permanently, with two blocks
in one document carrying opposite kinds of value under one name. It also reaches
the SHARED registry -- `sheetAttributes` is a single list that the psych audit
derives KNOWN_ACTION_ATTRS from -- so the name stops being private to a block the
moment it is registered there.

Renaming after the fact would have been the expensive path: by then the attribute
is in two repositories, 26 tags, both registries and every generated body, and
moving it walks into T5, since the tag changes and every prompt_sha moves with it.
See §11.4 of the plan, where this is closed in writing.
"""


def state(root: Path) -> dict:
    p = paths(root)
    prim = json.loads(p["primitives"].read_text())
    ts = p["ts"].read_text()
    md = p["md"].read_text()
    return {
        "in_sheet_attributes": ATTR in prim.get("sheetAttributes", []),
        "in_zod_schema": bool(re.search(rf"^\s+{ATTR}: z\.", ts, re.M)),
        "in_doc_table": f"| `{ATTR}` |" in md,
        "olx_setting_it": olx_setting_rubric(root),
    }


def apply(root: Path) -> list[str]:
    p, done = paths(root), []

    prim_text = p["primitives"].read_text()
    prim = json.loads(prim_text)
    if ATTR not in prim["sheetAttributes"]:
        # SURGICAL TEXT EDIT, NOT A JSON ROUND-TRIP. `json.dumps(prim, indent=1)`
        # rewrote all 97 lines of this file -- it uses a 2-space indent and puts
        # some entries two to a line, and a dump normalises both away. A one-word
        # change that reformats the whole file cannot be reviewed, and the diff
        # hides what actually happened inside it.
        m = re.search(r'("sheetAttributes"\s*:\s*\[)(.*?)(\])', prim_text, re.S)
        if not m:
            raise SystemExit("primitives.json: no sheetAttributes array found")
        body = m.group(2)
        last = body.rstrip()
        if not last.endswith('"'):
            raise SystemExit(f"primitives.json: unexpected array tail {last[-40:]!r}")
        new_body = body.replace(last, last + f', "{ATTR}"', 1)
        p["primitives"].write_text(
            prim_text[:m.start(2)] + new_body + prim_text[m.end(2):])
        after = json.loads(p["primitives"].read_text())
        if after["sheetAttributes"] != prim["sheetAttributes"] + [ATTR]:
            raise SystemExit("primitives.json: surgical edit changed more than "
                             "the one entry — restore and investigate")
        done.append(f"primitives.json: sheetAttributes += {ATTR!r}")

    ts = p["ts"].read_text()
    if not re.search(rf"^\s+{ATTR}: z\.", ts, re.M):
        anchor = "    forbid: z.string().optional().describe("
        if ts.count(anchor) != 1:
            raise SystemExit(f"LLMAction.ts: expected one {anchor!r}, "
                             f"found {ts.count(anchor)}")
        block = f"    {ATTR}: z.string().optional().describe(\n      {DESC}\n    ),\n"
        p["ts"].write_text(ts.replace(anchor, block + anchor, 1))
        done.append(f"LLMAction.ts: zod schema += {ATTR}")

    md = p["md"].read_text()
    if f"| `{ATTR}` |" not in md:
        anchor = ("| `requires` | credited only while another holds — the mirror "
                  "of `onlyif` |")
        if md.count(anchor) != 1:
            raise SystemExit(f"LLMAction.md: expected one {anchor!r}, "
                             f"found {md.count(anchor)}")
        p["md"].write_text(md.replace(anchor, anchor + "\n" + DOC_ROW, 1))
        done.append(f"LLMAction.md: attribute table += {ATTR} (O5)")
    return done


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lo-blocks", required=True)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--name-decided", action="store_true",
                    help="the NAME_COLLISION below has been resolved in writing")
    a = ap.parse_args()
    root = Path(a.lo_blocks)
    if not (root / "packages/shared/lib/llm/primitives.json").exists():
        print(f"not a lo-blocks tree: {root}")
        return 2

    if a.apply:
        print(NAME_COLLISION.strip())
        if not a.name_decided:
            print("\nREFUSED — decide the attribute NAME first (stage-00 gate).\n"
                  "Re-run with --apply --name-decided once it is written down.")
            return 2
        for line in apply(root) or ["nothing to do — already registered"]:
            print("  ", line)

    s = state(root)
    ok = s["in_sheet_attributes"] and s["in_zod_schema"] and s["in_doc_table"]
    print(f"\nsheetAttributes carries `{ATTR}` : {s['in_sheet_attributes']}")
    print(f"LLMAction zod schema declares it: {s['in_zod_schema']}")
    print(f"LLMAction.md documents it (O5)  : {s['in_doc_table']}")
    if s["olx_setting_it"]:
        print(f"\nO1 VIOLATED — content already sets {ATTR}=: "
              f"{', '.join(s['olx_setting_it'][:5])}")
        print("   The engine must accept and IGNORE it for a full stage first.")
        return 1
    print(f"O1: no .olx sets {ATTR}= yet — accepted and ignored, as required")
    if not ok:
        print("\nINCOMPLETE — run with --apply")
        return 1
    print("\nboth registries carry it and no content references it: stage-00 "
          "registry step COMPLETE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
