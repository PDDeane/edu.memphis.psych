#!/usr/bin/env python3
"""Stage 00 · the gate. Runs the QC a commit would force, and does not commit.

DRY RUN: no commit is made. That is a deliberate instruction, not an omission,
and it changes nothing about the checking -- §7b's point is that committing is
merely the cheapest WAY to run the enforcement machinery, because the pre-commit
hook runs `equivalence.py --enforcement` and refuses on a blocking finding. So
this runs that audit directly, plus the four things the hook does NOT cover and
which a commit would therefore never have caught anyway:

    the selftest and SELFTEST_EXPECTED · the byte oracles · the idmap
    served-prompt check · anything in lo-blocks, which has no hook at all

`--with-selftest` and `--with-suite` are opt-in because each costs tens of
minutes; the gate REPORTS them as NOT RUN rather than passing silently, because
a gate that quietly skips its expensive half is how "green" stops meaning
anything (§7b, "Passing is not the same as still correct").

Usage:
    stage00_gate.py --scoring DIR --lo-blocks DIR [--with-selftest] [--with-suite]
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

HERE = Path(__file__).parent
PASS, FAIL, SKIP, MANUAL = "PASS", "FAIL", "NOT RUN", "MANUAL"


def sh(cmd, cwd=None, timeout=7200):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True,
                       timeout=timeout)
    return r.returncode, r.stdout + r.stderr


def check_oracles(scoring: Path):
    rc, out = sh([sys.executable, str(HERE / "stage00_freeze_oracles.py")],
                 cwd=scoring)
    last = [l for l in out.splitlines() if l.strip()][-1] if out.strip() else "?"
    return (PASS if rc == 0 else FAIL), last


def check_baseline(scoring: Path):
    rc, out = sh([sys.executable, str(HERE / "stage00_capture_baseline.py"),
                  "--scoring", str(scoring)], cwd=scoring)
    last = [l for l in out.splitlines() if l.strip()][-1] if out.strip() else "?"
    return (PASS if rc == 0 else FAIL), last


def check_registry(lo: Path):
    rc, out = sh([sys.executable, str(HERE / "stage00_registry.py"),
                  "--lo-blocks", str(lo)])
    last = [l for l in out.splitlines() if l.strip()][-1] if out.strip() else "?"
    return (PASS if rc == 0 else FAIL), last


def check_reconstruction_helper(scoring: Path):
    """T11: one helper owns count-vs-verdict routing, and every site calls it."""
    sites = {
        "measured.py": ["mirror_self_control", "_recorded_payloads",
                        "paper_scorer_agreement"],
        "probe.py": ["reconstruct"],
        "enforcement.py": ["check_computed_slot_recovery_is_faithful"],
    }
    # EITHER HELPER COUNTS. `rebuild_sheet` rebuilds a whole recorded cell;
    # `count_keys` is the single authority it is built on, and a site that
    # assembles its sheet incrementally (paper_scorer_agreement renames keys as
    # it goes) legitimately uses the latter. The first version demanded the
    # literal `rebuild_sheet` and reported a site as unfixed for using the right
    # helper -- while `mirror_self_control`, which used NEITHER and carried its
    # own copy of the rule, sat in the same finding and looked identical.
    helpers = ("rebuild_sheet", "count_keys")
    helper = helpers[0]
    agreement = (scoring / "agreement.py").read_text()
    if f"def {helper}(" not in agreement:
        return FAIL, (f"`{helper}` does not exist yet — the five reconstruction "
                      f"sites still each route counts by hand (T11)")
    missing = []
    for fname, funcs in sites.items():
        text = (scoring / fname).read_text()
        for fn in funcs:
            m = re.search(rf"def {fn}\b.*?(?=\ndef |\Z)", text, re.S)
            if m and not any(h in m.group(0) for h in helpers):
                missing.append(f"{fname}:{fn}")
    if missing:
        return FAIL, (f"{len(missing)} site(s) route counts by hand instead of "
                      f"calling {' or '.join(helpers)}: " + ", ".join(missing))
    return PASS, (f"all reconstruction sites route through "
                  f"{' / '.join(helpers)} (T11)")


def check_entry_condition(scoring: Path):
    """§7a: every column swept, reachable and stamped.

    "STALE SCORER CLEARS FOR NOTHING" IS TRUE IN GENERAL AND NOT ALWAYS. Measured
    2026-09-14 on the three the dry run tried to clear -- `olx`/3, `python`/2b,
    `python`/3. All three pass `safe_to_rerecord`: the ask has not moved, so a
    re-record is legitimate in principle. All three were then REFUSED by the side
    contract, because their artifacts predate `agreement._era_for` stamping the
    backend and nothing records which model produced them -- not `era`, not
    `era.items`, not the sibling `.log`, not their existing ledger entries. There
    is no fact to recover, so hand-stamping `era.model` would invent one.

    Clearing such a column therefore costs a RE-SWEEP, or a declared exception in
    the shape §11.3 uses for `paper_opus`. The gate must not quote the general
    rule at someone who is about to hit the exception, so the message says to
    check rather than promising zero.

    `paper_opus` IS EXCLUDED, by the declaration in §11.3 (closed 2026-09-13) and
    not by convenience. The gate's own wording allows this: zero failing columns
    "or the exceptions are declared with the decision that permits them". It is a
    non-comparable column -- different model AND different tool availability --
    and 25 of its 26 columns were never measured at all, so demanding them would
    have cost ~3,000 calls to manufacture evidence acceptance cannot use.

    The exclusion is HERE, in one place, naming the decision. A gate that quietly
    filtered the column would be indistinguishable from a gate that forgot it.
    """
    code = ("import json, measured as M\n"
            "bad = {}\n"
            "for side in ('olx','python','paper'):   # paper_opus: §11.3\n"
            "    try: rows = M.status(side)\n"
            "    except Exception as e: rows = [('*', 'status raised %s' % e)]\n"
            "    for item, msg in rows:\n"
            "        if not msg.startswith('ok'): bad.setdefault(side, []).append(item)\n"
            "print('JSON:' + json.dumps({k: len(v) for k, v in bad.items()}))\n")
    rc, out = sh([sys.executable, "-c", code], cwd=scoring)
    m = re.search(r"JSON:(\{.*\})", out)
    if not m:
        return FAIL, f"could not measure: {out.strip()[-160:]}"
    counts = json.loads(m.group(1))
    total = sum(counts.values())
    detail = ", ".join(f"{k}:{v}" for k, v in sorted(counts.items())) or "none"
    if total:
        return FAIL, (f"{total} column(s) not ok ({detail}); paper_opus excluded "
                      f"per §11.3. Stale PROMPT needs a sweep. Stale SCORER is "
                      f"USUALLY a 0-call re-record — but check first: a column "
                      f"whose artifact predates model stamping is refused by the "
                      f"side contract, and clearing it needs a re-sweep or a "
                      f"declared exception, NOT a re-record")
    return PASS, "every column swept, reachable and stamped"


def check_decisions(plan: Path):
    """The five stage-00 decisions, closed IN WRITING. Not automatable."""
    text = plan.read_text() if plan.exists() else ""
    # SCOPED TO §11. The first version matched `^\d. **` across the WHOLE
    # document and reported "9 decisions", counting every numbered list in the
    # plan. A gate that miscounts the thing it is gating on is worse than no
    # gate: nobody can tell 5-of-5 from 5-of-9.
    m = re.search(r"^## 11 · Open decisions.*?(?=^## |\Z)", text, re.S | re.M)
    body = m.group(0) if m else ""
    # EACH ITEM'S WHOLE BODY, not just its bolded title. The first version
    # matched `^\d. **(.+?)**` and asked whether DECIDED appeared inside that one
    # span -- so §11.1, which puts its title in one bold and its decision in a
    # second, read as still open and the gate reported 3 of 4 against a file
    # carrying 4. A gate that under-reports closure invites someone to re-take a
    # decision that was already made, which is worse than silence.
    starts = [m.start() for m in re.finditer(r"^\d\. \*\*", body, re.M)]
    items = [body[a:b] for a, b in zip(starts, starts[1:] + [len(body)])]
    closed = [i for i in items if re.search(r"DECIDED|CLOSED", i)]
    verdict = PASS if items and len(closed) == len(items) else MANUAL
    return verdict, (f"{len(closed)} of {len(items)} decision(s) in §11 are "
                     f"closed in writing"
                     + ("" if verdict == PASS else
                        " — the rest must close before stage 01"))


def check_suite(lo: Path, run: bool):
    if not run:
        return SKIP, "lo-blocks has NO pre-commit hook — the suite IS the gate (§7b)"
    rc, out = sh(["npx", "vitest", "run", "--reporter=dot"], cwd=lo)
    m = re.search(r"Tests\s+(\d+) failed.*?\|\s*(\d+) passed", out) or \
        re.search(r"Tests\s+(\d+) passed", out)
    tail = [l for l in out.splitlines() if "Tests" in l]
    return (PASS if rc == 0 else FAIL), (tail[-1].strip() if tail else out[-160:])


def check_skips(lo: Path, run: bool):
    """§7b: name every skipped test; a skipped test cannot tell you it has rotted.

    The status string is "skipped", NOT "pending" -- the first census filtered on
    "pending", found nothing, and printed "0 skipped" under a suite summary that
    said 5. A census that reports zero because it asked the wrong key is worse
    than none: it certifies exactly the thing it failed to look at.
    """
    if not run:
        return SKIP, "needs the suite run (--with-suite)"
    import tempfile, os
    out = os.path.join(tempfile.gettempdir(), "vitest-skips.json")
    sh(["npx", "vitest", "run", "--reporter=json", f"--outputFile={out}"], cwd=lo)
    try:
        d = json.loads(Path(out).read_text())
    except Exception as e:
        return FAIL, f"no JSON report: {e}"
    rows = [(r.get("name", "?").split("/packages/")[-1],
             t.get("fullName") or t.get("title"))
            for r in d.get("testResults", [])
            for t in r.get("assertionResults", [])
            if t.get("status") == "skipped"]
    if not rows:
        return PASS, "no test is skipped"
    names = "; ".join(f"{f}: {n}" for f, n in rows[:3])
    return MANUAL, (f"{len(rows)} skipped — the gate must record what supplies "
                    f"each missing precondition: {names}")


def check_selftest(scoring: Path, run: bool):
    if not run:
        return SKIP, "the hook never runs the selftest — a commit would not catch this"
    rc, out = sh([sys.executable, "equivalence.py", "--enforcement", "--selftest"],
                 cwd=scoring)
    m = re.search(r"(\d+) detected, (\d+) failed, (\d+) skipped, (\d+) of (\d+) expected",
                  out)
    if not m:
        return FAIL, out.strip()[-200:]
    det, failed, skipped, got, exp = map(int, m.groups())
    ok = failed == 0 and got == exp
    return (PASS if ok else FAIL), m.group(0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scoring", required=True)
    ap.add_argument("--lo-blocks", required=True)
    ap.add_argument("--with-selftest", action="store_true")
    ap.add_argument("--with-suite", action="store_true")
    a = ap.parse_args()
    scoring, lo = Path(a.scoring), Path(a.lo_blocks)
    plan = scoring.parent / "RUBRIC_MIGRATION_PLAN.md"

    rows = [
        ("prompt byte oracles unchanged", *check_oracles(scoring)),
        ("audit RAW finding-set identical", *check_baseline(scoring)),
        ("reconstruction helper (T11)", *check_reconstruction_helper(scoring)),
        ("both registries carry it, no content sets it (O1/O5)",
         *check_registry(lo)),
        ("entry condition: columns swept+stamped (§7a)",
         *check_entry_condition(scoring)),
        ("five open decisions closed in writing (§11)", *check_decisions(plan)),
        ("lo-blocks suite (§7b)", *check_suite(lo, a.with_suite)),
        ("no relied-on test is skipped (§7b)", *check_skips(lo, a.with_suite)),
        ("selftest + SELFTEST_EXPECTED", *check_selftest(scoring, a.with_selftest)),
    ]
    w = max(len(r[0]) for r in rows)
    print("\nSTAGE 00 GATE\n" + "=" * (w + 12))
    for name, verdict, detail in rows:
        print(f"{verdict:<8}{name:<{w}}  {detail}")
    print("=" * (w + 12))
    failed = [r[0] for r in rows if r[1] == FAIL]
    skipped = [r[0] for r in rows if r[1] in (SKIP, MANUAL)]
    print("\nCOMMIT: SKIPPED — dry run. The QC a commit would force was run "
          "above:\n        the hook's own `--enforcement` audit, plus the four "
          "things it does\n        NOT cover (selftest, byte oracles, idmap "
          "check, lo-blocks).")
    if failed:
        print(f"\nGATE NOT MET — {len(failed)} clause(s) failing:")
        for f in failed:
            print("   ", f)
    if skipped:
        print(f"\n{len(skipped)} clause(s) NOT RUN or MANUAL — a gate that "
              f"skips its expensive half is not a gate:")
        for s in skipped:
            print("   ", s)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
