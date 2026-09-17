#!/usr/bin/env python3
"""Stage 03b · the gate. The rubric instance, proved against what ships today.

TWO CLAUSES FROM THE PLAN, and both are run rather than asserted:

  * ONE ITEM BYTE-EQUAL, assembled from the rubric object. Byte-equal against
    `build_web_prompt`'s RETURN VALUE, not against the .olx element text -- the
    element carries a leading newline from the XML and every item would fail by
    one character at each end for a reason unrelated to the rubric.
  * THE COURSE RENDERS THREE ASSIGNMENTS, with the rubric held and not shown.

AND TWO THE PLAN IMPLIES. A gate that only checked the two clauses would pass
while the rubric quietly stopped being the source: so the authored rubric must
PARSE with no errors, and the item's data must round-trip -- authored .olx,
through the platform parser, through materialisation, equal to the real rubric
entry. Byte-equality of the assembled prompt does not prove that on its own,
because most assembler inputs could still come from the old source.

WHAT IS NOT YET FROM THE RUBRIC is reported, not hidden: the shared prose
fragments, the cross-reference and response field ids, slot option lists and
slot notes still come from generator-side tables. A gate that said "byte-equal"
without saying that would be claiming more than was proved.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

PASS, FAIL, NOTE = "PASS", "FAIL", "NOTE"
HERE = Path(__file__).parent


def sh(cmd, cwd, timeout=1800):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout + r.stderr


def run_probe(lo: Path, name: str, marker: str):
    """Run one saved verifier and pull a marker line out of its output."""
    src = HERE / "verify" / name
    if not src.exists():
        return None, f"{name} is missing from migration/verify"
    dest = lo / "packages/shared/lib" / name
    dest.write_text(src.read_text())
    try:
        rc, out = sh(["npx", "vitest", "run", str(dest.relative_to(lo)),
                      "--reporter=basic"], lo)
    finally:
        dest.unlink(missing_ok=True)
    m = re.search(rf"{marker}=(\S+)", out)
    return (m.group(1) if m else None), out


def check_parses(lo: Path):
    val, out = run_probe(lo, "pr_parse.test.ts", "PR_PARSE_ERRORS")
    if val is None:
        return FAIL, "no result: " + out.strip()[-140:]
    return (PASS if val == "0" else FAIL), f"{val} parse error(s) in the authored rubric"


def check_roundtrip(lo: Path):
    val, out = run_probe(lo, "roundtrip.test.ts", "MATERIALISED")
    left = re.search(r"TEMPLATES_LEFT=(\d+)", out)
    errs = re.search(r"PARSE_ERRORS=(\d+)", out)
    if val is None or left is None:
        return FAIL, "no result: " + out.strip()[-140:]
    ok = val == "4" and left.group(1) == "0" and (errs is None or errs.group(1) == "0")
    return (PASS if ok else FAIL,
            f"{val} item(s) materialised, {left.group(1)} template(s) left in the output")


def check_byte_equal(lo: Path):
    val, out = run_probe(lo, "pr_assemble.test.ts", "BYTE_EQUAL")
    if val is None:
        return FAIL, "no result: " + out.strip()[-140:]
    got = re.search(r"got=(\d+) want=(\d+)", out)
    size = f" ({got.group(1)} chars)" if got else ""
    return (PASS if val == "true" else FAIL,
            f"one item assembled from the rubric is byte-equal{size}"
            if val == "true" else f"NOT byte-equal{size}")


def check_course(lo: Path):
    val, out = run_probe(lo, "course_render.test.ts", "SECTIONS")
    kinds = re.search(r"KINDS=(\S+)", out)
    if val is None:
        return FAIL, "no result: " + out.strip()[-140:]
    handouts = len(re.findall(r"handout", kinds.group(1) if kinds else ""))
    return (PASS if handouts == 3 else FAIL,
            f"{handouts} assignment(s) in the course, {val} section(s) before the "
            f"render-time filter drops internal blocks")


def check_internal(lo: Path):
    """The render-time filter reads `internal`; a block that lost it would show."""
    rc, out = sh(["npx", "vitest", "run",
                  "packages/shared/components/blocks/layout/Course",
                  "--reporter=basic"], lo)
    m = re.search(r"Tests\s+(\d+) passed", out)
    return (PASS if rc == 0 and m else FAIL,
            f"{m.group(1)} Course tests, including that every rubric block is internal"
            if m else out.strip()[-140:])


def check_ref_grammars(lo: Path):
    """The two resolvers must agree, or the grader and the student see different text.

    SINCE THE HISTORY REWRITE THERE ARE TWO. `corpus_resolve.py` resolves a
    reference in Python, which is the path the scorer reads the .olx by;
    `resolveCorpusRefs.ts` resolves at build time, which is the path a student's
    page is rendered by. If they disagree about a field, an escape or a shape op,
    the words a grader scores and the words on the page diverge -- and nothing
    else in this gate would notice, because each side is internally consistent.

    `scoring/check_ref_grammars.py` is the only thing that compares them, and it
    checks both directions: every field the Python resolver accepts must parse in
    TypeScript, and both must produce the same text.
    """
    checker = MP.SCORING / "check_ref_grammars.py"
    if not checker.exists():
        return FAIL, "scoring/check_ref_grammars.py is MISSING -- nothing compares them"
    r = subprocess.run([sys.executable, str(checker)], cwd=str(MP.SCORING),
                       capture_output=True, text=True, timeout=1800)
    txt = (r.stdout or "") + (r.stderr or "")
    last = next((l for l in reversed(txt.splitlines()) if l.strip()), "")
    if r.returncode != 0:
        return FAIL, f"resolvers disagree: {last.strip()[:90]}"
    return OK, last.strip()[:90] or "grammars agree"


def what_is_not_yet_from_the_rubric(lo: Path):
    val, out = run_probe(lo, "pr_assemble.test.ts", "FROM_OLD_SOURCE")
    return NOTE, (val or "unknown") .replace(",", ", ")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lo-blocks", required=True)
    a = ap.parse_args()
    lo = Path(a.lo_blocks)
    rows = [
        ("the authored rubric parses with no errors", *check_parses(lo)),
        ("its items round-trip: authored -> parsed -> materialised", *check_roundtrip(lo)),
        ("ONE ITEM BYTE-EQUAL, assembled from the rubric", *check_byte_equal(lo)),
        ("the course renders THREE assignments", *check_course(lo)),
        ("rubric blocks are internal, so the filter can hide them", *check_internal(lo)),
        ("the two reference resolvers agree", *check_ref_grammars(lo)),
        ("still NOT from the rubric", *what_is_not_yet_from_the_rubric(lo)),
    ]
    w = max(len(r[0]) for r in rows)
    print("\nSTAGE 03b GATE\n" + "=" * (w + 12))
    for name, verdict, detail in rows:
        print(f"{verdict:<8}{name:<{w}}  {detail}")
    print("=" * (w + 12))
    failed = [r[0] for r in rows if r[1] == FAIL]
    print("\nGATE MET." if not failed else f"\nGATE NOT MET - {len(failed)} failing")
    for f in failed:
        print("   ", f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
