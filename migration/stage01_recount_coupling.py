#!/usr/bin/env python3
"""Stage 01 · re-measure how many checks read a source this migration moves.

WHY MEASURE RATHER THAN QUOTE. The figure moves with the tree: 72 of 125 on
2026-09-11, 73 of 135 two days later, and stage 00 added one more check. §0's
maintenance rule says any stage that adds or retires a check re-runs this, and
stage 01's own entry says it "begins by re-running the §0 measurement, not by
trusting the number printed here".

THE HEURISTIC IS KEPT DELIBERATELY UNCHANGED. Each `check_*` body is scanned for
the needles named in §0's table. It over-counts -- a check may read two sources --
so the ROW totals sum past the union, and the union is the migration's real size.
Changing the needles would make the new figure incomparable with the old, which
is worse than a crude heuristic applied consistently.

Output is an inventory the disposition pass then annotates: every coupled check
gets re-point / re-express / retire-declared, and every uncoupled one is listed
as untouched so "not dispositioned" cannot hide among "not coupled".
"""
import argparse, ast, json, sys
from pathlib import Path

# THE NEEDLES ARE PINNED HERE, and that is the point. §0 says to re-derive "by
# scanning each check_* body for the needles named in each row -- the same
# heuristic, so the figures stay comparable", but it never wrote the needles
# down. Measured 2026-09-14, the choice dominates the answer: the `.olx` row
# yields 0, 7, 12 or 24 depending on whether the needle is `_olx(`, `_olx`,
# `_olx`+`prompt_sha`, or those plus `.olx`; the rubric row yields 23, 32 or 60.
# A figure quoted without its needles is not a measurement, it is a preference.
#
# These are calibrated to reproduce §0's 2026-09-13 row totals (46/31/21/7/8) as
# closely as the current tree allows, so the series stays comparable. Change them
# only with the old and new figures printed side by side.
ROWS = {
    "olx_prompts (notes, builders, registries)":
        ("olx_prompts", "SLOT_NOTES", "build_web_prompt", "O.ACTION"),
    "the rubric modules (rubric_hN.py, SLOT_SPEC, all_items)":
        ("rubric_h", "SLOT_SPEC", "all_items", "BY_ID"),
    "the .olx bytes (_olx, prompt_sha, section bounds)":
        ("_olx", "prompt_sha", "_SECTION_RE", ".olx"),
    "the designed-text registry":
        ("DESIGNED_TEXT",),
    "recorded artifacts":
        ("_runs_doc", "_runs_path", "records(", "_artifact_fingerprint"),
}

DOCUMENTED_2026_09_13 = {"olx_prompts": 46, "rubric": 31, "olx_bytes": 21,
                         "designed_text": 7, "artifacts": 8, "union": 73,
                         "total": 135}


def code_only(body: str) -> str:
    """The function source with docstrings removed, for the CODE-ONLY count.

    A NEEDLE IN A COMMENT IS NOT A READ. Measured 2026-09-14: 7 of the 76 checks
    the text scan called coupled never touch the moving source in code at all --
    they name it in prose. `check_no_module_shadow_in_scratchpad` is one. The
    `.olx` row falls 24 -> 17 that way and the designed-text row 7 -> 4, so §0's
    historical 21 and 7 were probably inflated the same way, and the migration's
    "real size" has been over-stated since the first measurement.

    Dispositioning a check that reads nothing is worse than wasted effort: it
    records a re-point for something with nothing to re-point, and the next
    reader believes it. So the CODE count is what the disposition pass works
    from, and the TEXT count is reported beside it to keep §0's series readable.

    `ast.unparse` drops comments for free and docstrings are removed explicitly.
    """
    t = ast.parse(body)
    for n in ast.walk(t):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef,
                          ast.Module)):
            if (getattr(n, "body", None) and isinstance(n.body[0], ast.Expr)
                    and isinstance(n.body[0].value, ast.Constant)
                    and isinstance(n.body[0].value.value, str)):
                n.body = n.body[1:] or [ast.Pass()]
    return ast.unparse(t)


def checks(scoring: Path) -> dict:
    out = {}
    for f in sorted(scoring.glob("*.py")):
        src = f.read_text()
        try:
            tree = ast.parse(src)
        except SyntaxError:
            continue
        for n in ast.walk(tree):
            if isinstance(n, ast.FunctionDef) and n.name.startswith("check_"):
                body = ast.get_source_segment(src, n) or ""
                out[f"{f.name}:{n.name}"] = body
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scoring", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    scoring = Path(a.scoring)

    found = checks(scoring)
    per_row, coupled, text_only = {}, {}, {}
    for name, body in found.items():
        try:
            cbody = code_only(body)
        except Exception:
            cbody = body
        text_hits = [row for row, nd in ROWS.items() if any(x in body for x in nd)]
        hits = [row for row, nd in ROWS.items() if any(x in cbody for x in nd)]
        if hits:
            coupled[name] = hits
        elif text_hits:
            text_only[name] = text_hits          # named in prose, reads nothing
        for row in hits:
            per_row.setdefault(row, []).append(name)

    print(f"{len(found)} check_* function(s) across {scoring}\n")
    w = max(len(r) for r in ROWS)
    for row in ROWS:
        print(f"  {row:<{w}}  {len(per_row.get(row, [])):>3}")
    print(f"  {'none of the above — safe by construction':<{w}}  "
          f"{len(found) - len(coupled):>3}")
    print(f"\n  UNION (CODE) — checks that READ something this migration moves: "
          f"{len(coupled)} of {len(found)}")
    print(f"  UNION (TEXT) — as §0 has always counted it, prose included:      "
          f"{len(coupled) + len(text_only)} of {len(found)}")
    print("  (rows over-count: a check may read more than one source)")
    if text_only:
        print(f"\n  {len(text_only)} check(s) name a moving source ONLY IN PROSE "
              f"and read none of it.\n  They need no disposition; listed so "
              f"\"not dispositioned\" cannot hide among \"not coupled\":")
        for n in sorted(text_only):
            print(f"     {n}")

    if a.out:
        Path(a.out).write_text(json.dumps(
            {"total_checks": len(found),
             "coupled": len(coupled),
             "counted_by": "code-only (docstrings stripped); see code_only()",
             "union_text_for_comparison": len(coupled) + len(text_only),
             "named_in_prose_only": {n: r for n, r in sorted(text_only.items())},
             "per_row": {r: sorted(v) for r, v in per_row.items()},
             "checks": {n: {"reads": rows, "disposition": None}
                        for n, rows in sorted(coupled.items())},
             "uncoupled": sorted(n for n in found if n not in coupled)},
            indent=1))
        print(f"\ninventory -> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
