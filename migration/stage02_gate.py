#!/usr/bin/env python3
"""Stage 02 · the gate. The assembler must reproduce what the generator emits.

23 BODIES AND 26 ITEMS' ATTRIBUTES. Three items carry no `<LLMAction>` -- they
are scored deterministically from the fixture -- so there are 23 bodies to
reproduce and 26 items whose attributes must match. Both numbers are right, and
a gate demanding 26 bodies cannot be met.

WHICH BYTES: the GENERATOR's output, not the .olx element text. The element
carries a leading newline from the XML, so a comparison against stage 00's
frozen bodies fails by one character at each end for a reason that has nothing
to do with the assembler.

O5 IS PART OF THIS GATE, not an afterthought: a new leaf module needs its own
tests, none of them skipped, and mutation-testing against a COPY is what shows
they can fail.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
PASS, FAIL, SKIP = "PASS", "FAIL", "NOT RUN"


def sh(cmd, cwd, timeout=900):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout + r.stderr


def check_bodies(lo: Path):
    rc, out = sh(["npx", "tsx", str(HERE / "verify" / "bodies.ts")], lo)
    m = re.search(r"BYTE-EXACT: (\d+) of (\d+) bodies", out)
    if not m:
        return FAIL, "the verifier produced no result: " + out.strip()[-160:]
    got, tot = int(m.group(1)), int(m.group(2))
    return (PASS if got == tot else FAIL), f"{got} of {tot} bodies byte-exact"


def check_attributes(lo: Path):
    total = diff = 0
    for name in ("attrs_small.ts", "attrs_slots.ts", "attrs_choices.ts"):
        rc, out = sh(["npx", "tsx", str(HERE / "verify" / name)], lo)
        m = re.search(r"(\d+) (?:attribute\(s\) )?byte-identical, (\d+) differing", out)
        if not m:
            return FAIL, f"{name} produced no result: " + out.strip()[-120:]
        total += int(m.group(1)); diff += int(m.group(2))
    return (PASS if diff == 0 else FAIL), \
           f"{total} attribute value(s) byte-identical, {diff} differing"


def check_suite(lo: Path):
    rc, out = sh(["npx", "vitest", "run", "--reporter=dot"], lo, timeout=1800)
    m = re.search(r"Tests\s+(\d+) passed \| (\d+) skipped", out) or \
        re.search(r"Tests\s+(\d+) passed", out)
    if not m:
        return FAIL, out.strip()[-160:]
    return (PASS if rc == 0 else FAIL), m.group(0).strip()


def check_o5(lo: Path):
    """The assembler's own tests exist, run, and are not skipped."""
    tests = [lo / "packages/shared/lib/llm/promptAssembler.test.ts",
             lo / "packages/shared/lib/llm/attributeAssembler.test.ts"]
    missing = [t.name for t in tests if not t.exists()]
    if missing:
        return FAIL, "no test file for: " + ", ".join(missing)
    rc, out = sh(["npx", "vitest", "run",
                  *[str(t.relative_to(lo)) for t in tests], "--reporter=dot"], lo)
    m = re.search(r"Tests\s+(\d+) passed(?: \| (\d+) skipped)?", out)
    if not m or rc != 0:
        return FAIL, out.strip()[-160:]
    if m.group(2):
        return FAIL, f"{m.group(2)} assembler test(s) SKIPPED - a skipped test tests nothing"
    return PASS, f"{m.group(1)} assembler tests, none skipped"


def check_c2(lo: Path):
    """No course vocabulary in anything the migration added or touched."""
    terms = re.compile(r"cadence|antecedent|reinforc|punish|avoidance|utb|psyc|"
                       r"operant|stimulus|contingen", re.I)
    files = ["packages/shared/lib/llm/promptAssembler.ts",
             "packages/shared/lib/llm/promptAssembler.types.ts",
             "packages/shared/lib/llm/attributeAssembler.ts",
             "packages/shared/lib/llm/primitives.json",
             "packages/shared/components/blocks/action/LLMAction.ts",
             "packages/shared/components/blocks/action/LLMAction.md"]
    bad = []
    for f in files:
        p = lo / f
        if not p.exists():
            continue
        hits = [ln for ln in p.read_text().splitlines() if terms.search(ln)]
        if hits:
            bad.append(f"{f}: {len(hits)} line(s)")
    return (PASS if not bad else FAIL), \
           ("no course vocabulary in the engine" if not bad else "; ".join(bad))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lo-blocks", required=True)
    ap.add_argument("--mutation-report", default=None,
                    help="path to the recorded mutation-test result (O5)")
    a = ap.parse_args()
    lo = Path(a.lo_blocks)

    rows = [("23 bodies byte-exact", *check_bodies(lo)),
            ("every sheet attribute byte-exact (26 items)", *check_attributes(lo)),
            ("C2: no course vocabulary in the engine", *check_c2(lo)),
            ("O5: the assembler has its own tests, none skipped", *check_o5(lo)),
            ("lo-blocks suite (7b)", *check_suite(lo))]
    if a.mutation_report and Path(a.mutation_report).exists():
        txt = Path(a.mutation_report).read_text()
        m = re.search(r"CAUGHT\s+(\d+) of (\d+)", txt)
        surv = re.search(r"SURVIVED (\d+)", txt)
        ok = m and m.group(1) == m.group(2) and not surv
        rows.append(("O5: mutation-tested against a copy",
                     PASS if ok else FAIL,
                     m.group(0) if m else "no result recorded"))
    else:
        rows.append(("O5: mutation-tested against a copy", SKIP,
                     "pass --mutation-report with the recorded result"))

    w = max(len(r[0]) for r in rows)
    print("\nSTAGE 02 GATE\n" + "=" * (w + 12))
    for name, verdict, detail in rows:
        print(f"{verdict:<8}{name:<{w}}  {detail}")
    print("=" * (w + 12))
    failed = [r[0] for r in rows if r[1] == FAIL]
    if failed:
        print(f"\nGATE NOT MET - {len(failed)} clause(s) failing:")
        for f in failed:
            print("   ", f)
    else:
        print("\nGATE MET.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
