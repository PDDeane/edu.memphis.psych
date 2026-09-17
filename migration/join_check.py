#!/usr/bin/env python3
"""T28: does the rubric the COURSE RESOLVES contain the items the corpus scores?

THE GATE ON THE JOIN, not on either end. Stage 3a proved the course renders its
assignments. Stage 04 proved 23/23 items byte-equal from the emitted rubric.
Both were green, and between them sat a fact neither could see: `<Course>`
resolved a 34-line demonstration file while the emitted rubric -- 964 lines, 26
items -- was referenced by nothing at all. Each gate tested its own artifact
against its own oracle, so the JOIN was free to be wrong while every number on
both sides was right.

This resolves the id the CONSUMER actually uses and asserts we reached the thing
we built. It also refuses an id claimed by two files, because an ambiguous
reference is not a reference.
"""
import argparse
import re
import sys
from pathlib import Path

RUBRIC_ID = re.compile(r'<Rubric\b[^>]*\bid="([^"]+)"')
USE_REF = re.compile(r'<Use\b[^>]*\bref="([^"]+)"')
ITEM = re.compile(r'<Item\b[^>]*\bscores="([^"]+)"')


def rubric_files(content: Path) -> dict:
    """id -> [files declaring it]. A list, so a duplicate id is visible."""
    out: dict = {}
    for f in sorted(content.glob("*.olx")):
        for rid in RUBRIC_ID.findall(f.read_text()):
            out.setdefault(rid, []).append(f)
    return out


def check(content: Path, course: str, scored: set) -> list:
    problems = []
    course_file = content / course
    if not course_file.exists():
        return [f"no course file at {course_file}"]
    refs = USE_REF.findall(course_file.read_text())
    byid = rubric_files(content)

    resolved = [r for r in refs if r in byid]
    if not resolved:
        return [f"{course} references {refs} and none of them is a <Rubric>. "
                f"The course resolves no rubric at all."]

    reached: set = set()
    for rid in resolved:
        files = byid[rid]
        if len(files) > 1:
            problems.append(
                f"id `{rid}` is declared by {len(files)} files "
                f"({', '.join(f.name for f in files)}). An id claimed twice is a "
                f"reference nobody should have to reason about -- retire or rename "
                f"all but one.")
        for f in files:
            reached |= set(ITEM.findall(f.read_text()))

    missing = sorted(scored - reached)
    if missing:
        problems.append(
            f"the rubric the course resolves holds {len(reached)} item(s), and "
            f"{len(missing)} item(s) the corpus scores are NOT among them: "
            f"{', '.join(missing[:8])}{' ...' if len(missing) > 8 else ''}. "
            f"Deleting the python rubric while this holds would leave the corpus "
            f"with no reachable rubric.")

    # The other direction: a rubric carrying items nothing scores is a
    # demonstration file that got shipped, which is how this happened.
    extra = sorted(reached - scored)
    if extra:
        problems.append(
            f"the resolved rubric declares {len(extra)} item(s) the corpus does "
            f"not score: {', '.join(extra[:8])}. Either they are content nobody "
            f"asked for, or this is a demonstration file standing where the "
            f"rubric should be.")
    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--content", required=True, type=Path)
    ap.add_argument("--scoring", required=True, type=Path)
    ap.add_argument("--course", default="bmod_course.olx")
    a = ap.parse_args()
    sys.path.insert(0, str(a.scoring))
    # EVERY ITEM THE CORPUS SCORES, not every item with an <LLMAction>. The
    # first version used `olx_prompts.ACTION` -- 23 of 26 -- and reported `1b`,
    # `T1` and `T2` as rubric content nobody asked for. They are scored by the
    # PAPER scorer and carry no web action, which is a fact about how an item is
    # asked, not about whether it is scored.
    import handouts as H                                     # noqa: E402
    scored = {i["id"] for h in (1, 2, 3) for i in H.config(h)["rubric"].ITEMS}
    problems = check(a.content, a.course, scored)
    print(f"corpus scores {len(scored)} item(s)")
    for p in problems:
        print("  FAIL ", p)
    print("\nPASS  the course resolves a rubric containing every scored item"
          if not problems else f"\nFAIL  {len(problems)} problem(s) on the JOIN")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
