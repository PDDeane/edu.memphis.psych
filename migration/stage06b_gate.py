#!/usr/bin/env python3
"""Stage 06b · gate — the rubric-reading consumers are off the modules AND still fire.

06b's half of stage 06's gate is the clause *"every rubric-reading check
re-pointed and demonstrably still firing BEFORE 6c deletes anything"*. Both
halves matter and they fail differently:

  * re-pointed but not fired  -> C1. After 6c the check reads a source that is
    gone, returns [] and reports success. The audit goes green BECAUSE it
    stopped looking, and nothing in its output says so.
  * fired but not re-pointed  -> the delete breaks it loudly, which is the safe
    direction and is what 6c's own gate would catch anyway.

So this gate asserts the FIRING, and it asserts it from the selftest's own
report rather than from a claim in the plan.

Two couplings here were found only after 06b had twice been certified complete
by a token scan, and both are the reason this gate reads text rather than
imports: `olx_prompts.prior_record` read `rubric_hN.py` as TEXT, and
`check_maps_tables_are_attached` reached the modules by STRING through
`__import__("rubric_h1")` inside a `try/except: continue`. Neither is visible to
a scan for the NAME `rubric_hN`.
"""
import argparse
import ast
import pathlib
import re
import subprocess
import sys

OK, BAD = "PASS", "FAIL"


def _rows(scoring: pathlib.Path) -> list[tuple[str, str, str]]:
    rows = []

    # 1. No module is reached as DATA outside the accessor.
    leaks = []
    for f in sorted(scoring.glob("*.py")):
        if f.name in ("handouts.py", "goals.py", "equivalence.py"):
            continue            # the accessor itself; the goal archive is prose
        try:
            tree = ast.parse(f.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) \
                    and re.fullmatch(r"rubric_h[123]", node.value.id or ""):
                leaks.append(f"{f.name}:{node.lineno} {node.value.id}.{node.attr}")
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("rubric_h"):
                leaks.append(f"{f.name}:{node.lineno} from {node.module} import ...")
    rows.append(("no module reached as data outside the accessor",
                 OK if not leaks else BAD,
                 "clean" if not leaks else f"{len(leaks)}: {leaks[:3]}"))

    # 2. No module is reached as TEXT or by STRING import. The two couplings a
    #    name-token scan cannot see, and the two that actually survived 06b.
    text = []
    for f in sorted(scoring.glob("*.py")):
        src = f.read_text()
        for m in re.finditer(r'^(?!\s*#).*(__import__\(\s*["\']rubric_h|'
                             r'import_module\(\s*["\']rubric_h|'
                             r'f?"rubric_h\{?[h123]\}?\.py"|'
                             r"f?'rubric_h\{?[h123]\}?\.py')", src, re.M):
            text.append(f"{f.name}:{src[:m.start()].count(chr(10)) + 1}")
    rows.append(("no module reached as text or by string import",
                 OK if not text else BAD,
                 "clean" if not text else f"{len(text)}: {text[:3]}"))

    # 3. Only handouts.py may still import them at all -- that is 6c's step.
    importers = []
    for f in sorted(scoring.glob("*.py")):
        try:
            tree = ast.parse(f.read_text())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for al in node.names:
                    if al.name.startswith("rubric_h"):
                        importers.append(f"{f.name}:{node.lineno}")
    only_handouts = {i.split(":")[0] for i in importers} <= {"handouts.py"}
    rows.append(("only handouts.py still imports the modules",
                 OK if only_handouts else BAD,
                 f"{sorted({i.split(':')[0] for i in importers})}"))
    return rows


def _selftest_row(log: pathlib.Path, expected: int) -> tuple[str, str, str]:
    """Read the SUITE'S OWN report. A gate that re-derives the count from the
    source would pass on a suite that constructed its cases and never ran them.
    """
    if not log.exists():
        return ("selftest: every case constructed and detected", BAD,
                f"no log at {log}")
    txt = log.read_text()
    m = re.search(r"(\d+) detected, (\d+) failed, (\d+) skipped, (\d+) of (\d+) expected", txt)
    if not m:
        tail = [l for l in txt.splitlines() if l.strip()][-1:] or ["(empty)"]
        return ("selftest: every case constructed and detected", BAD,
                f"no summary line; last: {tail[0][:90]}")
    detected, failed, skipped, total, want = (int(x) for x in m.groups())
    moved = "THE SOURCE MOVED UNDER THIS RUN" in txt
    ok = failed == 0 and total == want == expected and not moved
    note = f"{detected} detected, {failed} failed, {skipped} skipped, {total} of {want}"
    if moved:
        note += " -- SOURCE MOVED MID-RUN, the comparison is void"
    return ("selftest: every case constructed and detected", OK if ok else BAD, note)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scoring", required=True)
    ap.add_argument("--selftest-log", required=True)
    ap.add_argument("--expected", type=int, required=True)
    a = ap.parse_args()
    scoring = pathlib.Path(a.scoring).resolve()

    rows = _rows(scoring)
    rows.append(_selftest_row(pathlib.Path(a.selftest_log), a.expected))

    # 4. The audit's RAW finding set has not moved. Runs LAST: it is the slowest
    #    and the cheap structural rows above localise a failure better.
    r = subprocess.run([sys.executable, "migration/stage00_capture_baseline.py",
                        "--scoring", str(scoring)],
                       capture_output=True, text=True,
                       cwd=str(pathlib.Path(__file__).resolve().parent.parent))
    out = r.stdout + r.stderr
    same = "RAW finding-set IDENTICAL to the baseline" in out
    line = next((l for l in out.splitlines() if "RAW" in l), out.strip()[-90:])
    rows.append(("audit RAW finding-set identical to the baseline",
                 OK if same else BAD, line.strip()[:110]))

    print("\nSTAGE 06b GATE")
    print("=" * 79)
    for what, verdict, note in rows:
        print(f"{verdict:<7} {what:<52} {note}")
    print("=" * 79)
    bad = [w for w, v, _ in rows if v == BAD]
    print("\nGATE MET." if not bad else f"\nGATE NOT MET — {len(bad)} failing: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
