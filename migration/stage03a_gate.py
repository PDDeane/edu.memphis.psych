#!/usr/bin/env python3
"""Stage 03a · the gate. The block types exist, validate, and nothing uses them.

PARSES *AND* REFUSES. The second half is the one worth gating on: a block that
accepts anything validates nothing, and every positive test still passes. So the
gate counts refusal tests as well as parse tests, and requires the CONTROL that
makes them meaningful -- a well-formed rubric producing no errors at all.

THROUGH `parseOLX`, NOT BY IMPORT (T12). A block is inert until the registry is
regenerated, and a unit test that imports the module directly passes either way.
The gate therefore checks the block is IN the generated registry, not merely that
a file exists.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

PASS, FAIL = "PASS", "FAIL"
BLOCKS = ["Rubric", "Verdicts", "Frame", "Segment", "Deduction", "Item"]
TERMS = re.compile(r"cadence|antecedent|reinforc|punish|avoidance|utb|psyc|"
                   r"operant|stimulus|contingen", re.I)


def sh(cmd, cwd, timeout=1800):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout + r.stderr


def check_registered(lo: Path):
    reg = lo / "packages/shared/components/blockRegistryAutogen.ts"
    if not reg.exists():
        return FAIL, "no generated registry"
    text = reg.read_text()
    missing = [b for b in BLOCKS if f"/blocks/rubric/{b}'" not in text]
    return (PASS if not missing else FAIL,
            f"all {len(BLOCKS)} in the generated registry (T12)" if not missing
            else "NOT registered, so inert: " + ", ".join(missing))


def check_docs(lo: Path):
    d = lo / "packages/shared/components/blocks/rubric"
    missing = [b for b in BLOCKS if not (d / f"{b}.md").exists()]
    return (PASS if not missing else FAIL,
            f"{len(BLOCKS)} .md files, one per block (O5)" if not missing
            else "no doc for: " + ", ".join(missing))


def check_tests(lo: Path):
    rc, out = sh(["npx", "vitest", "run",
                  "packages/shared/components/blocks/rubric",
                  "packages/shared/components/blocks/layout/Course",
                  "--reporter=basic"], lo)
    m = re.search(r"Tests\s+(\d+) passed", out)
    if rc != 0 or not m:
        return FAIL, out.strip()[-160:]
    return PASS, f"{m.group(1)} tests pass (blocks + the Course change)"


def check_refusals(lo: Path):
    """Both halves: refusal cases exist, and the control proves they mean something."""
    t = lo / "packages/shared/components/blocks/rubric/rubricBlocks.test.ts"
    if not t.exists():
        return FAIL, "no block test file"
    src = t.read_text()
    refusals = src.count("expect(errorsIn(idMap).length).toBeGreaterThan(0)")
    control = "expect(errorsIn(idMap)).toEqual([])" in src
    if not control:
        return FAIL, (f"{refusals} refusal test(s) but NO control -- they would all "
                      f"pass if the parser errored on everything")
    return (PASS if refusals >= len(BLOCKS) else FAIL,
            f"{refusals} refusal tests plus the control that makes them mean something")


def check_o1(lo: Path, content: Path):
    """No content may reference the new types yet."""
    hits = []
    for f in content.rglob("*.olx"):
        text = f.read_text(errors="ignore")
        for b in BLOCKS:
            if re.search(rf"<{b}\b", text):
                hits.append(f"{f.name}:{b}")
    return (PASS if not hits else FAIL,
            "no .olx references them - accepted and ignored" if not hits
            else "content already uses: " + ", ".join(hits[:4]))


def check_c2(lo: Path):
    d = lo / "packages/shared/components/blocks/rubric"
    bad = [p.name for p in d.iterdir() if p.is_file() and TERMS.search(p.read_text())]
    return (PASS if not bad else FAIL,
            "no course vocabulary in the block types" if not bad
            else "course vocabulary in: " + ", ".join(bad))


def check_suite(lo: Path):
    rc, out = sh(["npx", "vitest", "run", "--reporter=dot"], lo)
    m = re.search(r"Tests\s+(\d+) passed \| (\d+) skipped", out)
    return (PASS if rc == 0 and m else FAIL, m.group(0) if m else out[-160:])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lo-blocks", required=True)
    ap.add_argument("--content", required=True)
    a = ap.parse_args()
    lo, content = Path(a.lo_blocks), Path(a.content)
    rows = [
        ("six block types in the GENERATED registry (T12)", *check_registered(lo)),
        ("a well-formed rubric parses; a malformed one is REFUSED", *check_refusals(lo)),
        ("blocks and the Course change are tested", *check_tests(lo)),
        ("one .md per block (O5)", *check_docs(lo)),
        ("no content references them (O1)", *check_o1(lo, content)),
        ("engine stays content-neutral (C2)", *check_c2(lo)),
        ("lo-blocks suite (7b)", *check_suite(lo)),
    ]
    w = max(len(r[0]) for r in rows)
    print("\nSTAGE 03a GATE\n" + "=" * (w + 12))
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
