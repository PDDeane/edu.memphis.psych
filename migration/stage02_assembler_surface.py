#!/usr/bin/env python3
"""Stage 02 · what the assembler must be GIVEN to reproduce a prompt body.

THE INTERFACE IS NOT A DESIGN CHOICE, it is a measurement. The assembler has to
reproduce all 26 generated bodies byte-exact (stage 02's gate), so its input is
whatever the current generator reads -- no more, and provably no less. Guessing
the shape and discovering a missing field at the byte-diff is the expensive way;
R8 is the same lesson about `scoreSlotSheet`'s eight positional parameters.

IT ALSO FEEDS STAGE 03. Every `item[...]` key below is a field §3.1's rubric
object must carry, or the assembler cannot be driven from the rubric at all. A
key read here and absent there is a hole the byte oracle would find later and
the expressiveness audit should find first (R9).

Content-neutrality (C2) is checked on the way past: a generator that branches on
an ITEM ID rather than on what the item declares cannot move to lo-blocks, and
the ITEM_GATED_MECHANISMS table exists because that has happened before.
"""
import argparse, ast, json, re, sys
from pathlib import Path

GENERATORS = ("build_web_prompt", "_checklist_section", "_criteria_section",
              "choices_attr_for", "render", "_slots_attr")


def read_keys(fn: ast.FunctionDef, var: str) -> set:
    """Subscript and .get() keys read off `var` inside this function."""
    out = set()
    for n in ast.walk(fn):
        if (isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name)
                and n.value.id == var and isinstance(n.slice, ast.Constant)
                and isinstance(n.slice.value, str)):
            out.add(n.slice.value)
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "get" and isinstance(n.func.value, ast.Name)
                and n.func.value.id == var and n.args
                and isinstance(n.args[0], ast.Constant)
                and isinstance(n.args[0].value, str)):
            out.add(n.args[0].value)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scoring", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    src = (Path(a.scoring) / "olx_prompts.py").read_text()
    tree = ast.parse(src)
    fns = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}

    surface, consts, item_gated = {}, set(), []
    for name in GENERATORS:
        fn = fns.get(name)
        if fn is None:
            print(f"  ! {name} not found — the generator was renamed"); continue
        surface[name] = {
            "item_fields": sorted(read_keys(fn, "item")),
            "slot_fields": sorted(read_keys(fn, "slot") | read_keys(fn, "sl")),
            "action_fields": sorted(read_keys(fn, "action")),
            "lines": (fn.end_lineno or 0) - fn.lineno,
        }
        body = ast.unparse(fn)
        consts |= {m for m in re.findall(r"\b([A-Z][A-Z0-9_]{3,})\b", body)}
        # C2: does the generator branch on an item ID rather than a declaration?
        for lit in re.findall(r"item_id\s*==\s*'([^']+)'", body):
            item_gated.append(f"{name}: item_id == {lit!r}")

    all_item = sorted({k for v in surface.values() for k in v["item_fields"]})
    all_slot = sorted({k for v in surface.values() for k in v["slot_fields"]})
    print("THE ASSEMBLER'S INPUT SURFACE, measured from the current generator\n")
    for name, v in surface.items():
        print(f"  {name:<22} {v['lines']:>4} lines   "
              f"item:{len(v['item_fields']):>2}  slot:{len(v['slot_fields']):>2}  "
              f"action:{len(v['action_fields']):>2}")
    print(f"\n  RUBRIC ITEM fields the assembler needs ({len(all_item)}):")
    print("   ", ", ".join(all_item))
    print(f"\n  SLOT fields ({len(all_slot)}):")
    print("   ", ", ".join(all_slot))
    print(f"\n  module constants referenced ({len(consts)}): "
          f"{', '.join(sorted(consts)[:12])}...")
    if item_gated:
        print(f"\n  C2 VIOLATION RISK — generator branches on an item ID:")
        for g in item_gated:
            print("    ", g)
    else:
        print("\n  C2: no generator branches on a literal item id")

    if a.out:
        Path(a.out).write_text(json.dumps(
            {"per_function": surface, "item_fields": all_item,
             "slot_fields": all_slot, "item_gated": item_gated}, indent=1))
        print(f"\nsurface -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
