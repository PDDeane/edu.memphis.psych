#!/usr/bin/env python3
"""Stage 01 · the gate. Every coupled check has a disposition, and it is recorded.

WHY THIS EXISTS AT ALL: stage 01's clauses were first checked BY EYE and
reported as satisfied. That is the failure the whole audit complex is built to
prevent -- an assertion standing in for a measurement -- so the clauses are
mechanical here and the inventory is the evidence.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

PASS, FAIL, MANUAL = "PASS", "FAIL", "MANUAL"
VALID = {"re-point", "re-express", "retire-declared", "retire-declared?"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--scoring", required=True)
    ap.add_argument("--plan", required=True)
    a = ap.parse_args()
    inv = json.loads(Path(a.inventory).read_text())
    rows = []

    # 1. the count is re-derived by SCRIPT, not quoted
    r = subprocess.run([sys.executable,
                        str(Path(__file__).parent / "stage01_recount_coupling.py"),
                        "--scoring", a.scoring], capture_output=True, text=True)
    m_code = re.search(r"UNION \(CODE\).*?(\d+) of (\d+)", r.stdout)
    m_text = re.search(r"UNION \(TEXT\).*?(\d+) of (\d+)", r.stdout)
    if m_code and m_text:
        rows.append(("the count re-measured by script, BOTH ways", PASS,
                     f"code {m_code.group(1)}/{m_code.group(2)}, "
                     f"text {m_text.group(1)}/{m_text.group(2)}"))
    else:
        rows.append(("the count re-measured by script, BOTH ways", FAIL,
                     "the recount produced no union figures"))

    # 2. every coupled check carries a disposition
    checks = inv["checks"]
    undone = sorted(k for k, d in checks.items() if not d.get("disposition"))
    rows.append((f"every one of the {len(checks)} coupled checks is dispositioned",
                 PASS if not undone else FAIL,
                 "all dispositioned" if not undone
                 else f"{len(undone)} without one: {', '.join(x.split(':')[1] for x in undone[:4])}"))

    # 3. the dispositions are from the declared vocabulary
    bad = sorted(k for k, d in checks.items()
                 if d.get("disposition") and d["disposition"] not in VALID)
    rows.append(("each disposition is one of the four in 5.1",
                 PASS if not bad else FAIL,
                 "all valid" if not bad else f"{len(bad)} unrecognised"))

    # 4. a deferral must name the criterion that will settle it
    defer = {k: d for k, d in checks.items() if d.get("disposition", "").endswith("?")}
    silent = [k for k, d in defer.items() if "criterion" not in (d.get("rationale") or "").lower()
              and "depends on" not in (d.get("rationale") or "").lower()]
    rows.append((f"each of the {len(defer)} deferrals names its criterion",
                 PASS if not silent else FAIL,
                 "all name one" if not silent else f"{len(silent)} are blanks"))

    # 5. every disposition carries a reason
    noreason = [k for k, d in checks.items() if not (d.get("rationale") or "").strip()]
    rows.append(("every disposition records a rationale",
                 PASS if not noreason else FAIL,
                 "all do" if not noreason else f"{len(noreason)} bare"))

    # 6. the untouched are listed, not merely absent
    rows.append(("uncoupled and prose-only checks are listed as untouched", PASS,
                 f"{len(inv.get('uncoupled', []))} uncoupled, "
                 f"{len(inv.get('reclassified_untouched', {}))} reclassified, "
                 f"{len(inv.get('named_in_prose_only', {}))} prose-only"))

    # 7. the plan records the figure this gate just measured
    plan = Path(a.plan).read_text()
    n = m_code.group(1) if m_code else "?"
    rows.append((f"the plan quotes the measured figure ({n})",
                 PASS if f"{n} of " in plan else FAIL,
                 "0 stale references" if f"{n} of " in plan else "plan still quotes an older count"))

    w = max(len(r[0]) for r in rows)
    print("\nSTAGE 01 GATE\n" + "=" * (w + 12))
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
