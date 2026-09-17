import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parent))
import migration_paths as MP
#!/usr/bin/env python3
"""Stage 07 gate · the three conditions, read rather than re-derived.

    selftest accounts for exactly SELFTEST_EXPECTED breakages
    every retirement carries a declaration
    all four .md hook-ins still parse

THE SELFTEST ROW IS READ FROM THE SUITE'S OWN REPORT, not re-run here: a gate
that re-derives its evidence can pass on a different tree than the one the suite
saw. Point it at the log.

    python3 migration/stage07_gate.py /tmp/selftest_s07.log
"""
import pathlib, re, sys

SC = MP.SCORING
sys.path.insert(0, str(SC))


def main(log=None):
    rows = []
    # 1. the suite, from its report
    if log and pathlib.Path(log).exists():
        text = pathlib.Path(log).read_text()
        m = re.search(r"(\d+) detected, (\d+) failed, (\d+) skipped, (\d+) of (\d+) expected", text)
        if m:
            det, fail, skip, built, want = (int(x) for x in m.groups())
            rows.append(("selftest", f"{det} detected, {fail} failed, {built} of {want}",
                         fail == 0 and built == want))
        else:
            rows.append(("selftest", "no result line in the log", False))
    else:
        rows.append(("selftest", "NO LOG GIVEN -- not re-run here, on purpose", False))

    # 2. retirements
    import enforcement, handouts
    retired = []
    for name, mod in (("check_maps_tables_are_attached", enforcement),
                      ("RUBRIC_SOURCE", handouts)):
        src = pathlib.Path(mod.__file__).read_text()
        retired.append((name, f"RETIRED" in src and name in src))
    rows.append(("retirements declared", ", ".join(n for n, _ in retired),
                 all(ok for _, ok in retired)))

    # 3. the hook-ins
    import goals
    checks = {"GOALS.md": len(goals.check())}
    for n in ("check_closure_ceilings_are_declared", "check_guide_structure_is_sound",
              "check_guide_lessons_are_approved", "check_divergence_arithmetic_is_still_true",
              "check_prose_numbers_match_the_ledger"):
        checks[n] = len(getattr(enforcement, n)())
    rows.append(("hook-ins parse", str(checks), all(v == 0 for v in checks.values())))

    for what, detail, ok in rows:
        print(f"  {'PASS' if ok else 'FAIL'}  {what:<22} {detail[:88]}")
    print("STAGE 07 GATE " + ("MET" if all(r[2] for r in rows) else "NOT MET"))
    return 0 if all(r[2] for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else None))
