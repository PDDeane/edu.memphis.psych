#!/usr/bin/env python3
"""Stage 00 · freeze the enforcement audit's RAW finding set as the baseline.

THE RAW SET, NOT THE UNDECLARED ONE. `equivalence.py --enforcement` prints the
UNDECLARED differences -- 27 on 2026-09-13 -- but the selftest's own baseline is
`len(enforcement_audit()[0])`, which is 32, because it counts findings BEFORE the
declaration tables filter them. A gate built on the printed 27 is blind to any
change inside a declared difference: a declaration could stop matching, or start
covering something new, and the printed number would not move. §7's gates say
RAW, so this freezes raw and reports both numbers.

A MULTISET, NOT A SET. The first version compared `set(findings)` and reported
"IDENTICAL (24 lines)" for a 27-line audit -- three lines were duplicates and the
set silently merged them. A finding that fires three times and drops to firing
once is a real change, and a set cannot see it.

WHAT IT REFUSES TO FREEZE. See `tree_is_quiescent` and `crash_findings`: a
baseline taken while the selftest is mutating the sources, or one containing the
machinery's own crash, is worse than no baseline at all -- later stages diff
against it and "pass" while carrying a fault.

Usage:
    stage00_capture_baseline.py --write --scoring DIR   freeze the raw set
    stage00_capture_baseline.py --scoring DIR          re-run and diff (a gate)
"""
import argparse, json, hashlib, re, subprocess, sys
from collections import Counter
from pathlib import Path

GOLDEN = Path(__file__).parent / "goldens" / "audit_baseline.json"
RAWMARK = "RAWJSON:"

# One computation, both answers: `print_enforcement` calls `enforcement_audit`
# internally, so memoising it inside this subprocess yields the RAW set and the
# printed report for the price of one audit instead of two.
DRIVER = f"""
import functools, json, sys
import equivalence as E
E.enforcement_audit = functools.lru_cache(1)(E.enforcement_audit)
raw = E.enforcement_audit()[0]
sys.stdout.write({RAWMARK!r} + json.dumps([[str(x) for x in f] for f in raw]) + "\\n")
E.print_enforcement()
"""


def source_hash(scoring: Path) -> str:
    """One hash over every .py the audit reads, so a mutation cannot hide."""
    h = hashlib.sha256()
    for f in sorted(scoring.glob("*.py")):
        h.update(f.name.encode())
        h.update(f.read_bytes())
    return h.hexdigest()[:12]


def tree_is_quiescent(scoring: Path) -> list[str]:
    """Refuse to freeze a baseline from a tree something else is editing.

    MEASURED, 2026-09-13, by this very script. The enforcement SELFTEST injects
    breakage into the sources and checks the audit notices. A case FAILED, the
    selftest reported its restore check as "VOID -- source moved", and it left
    `agreement.py` carrying the injected `NameError` -- one deleted name in a
    tuple unpack. This script then froze 28 findings as the baseline, the 28th
    being the injected crash.

    "DIFFERS FROM HEAD" IS THE WRONG SIGNAL, and was the first thing tried. This
    working tree is ALWAYS dirty -- twenty files on the day this was written, all
    of them intended work -- so that test refuses every run and teaches its own
    override. What discriminates is not whether the tree is uncommitted but
    whether it is being MUTATED, or already carries a crash.
    """
    # TREE-AWARE, like the guards in `olx_prompts` (T25). This matched any
    # self-test on the machine, so a LIVE self-test made every sandbox audit
    # warn that its own baseline was a snapshot of injected breakage -- about a
    # tree it cannot reach. The question is never "is a self-test running" but
    # "is one mutating THE SOURCE I AM ABOUT TO READ".
    import os as _os
    mine = _os.path.realpath(str(scoring))
    r = subprocess.run(["pgrep", "-af", "equivalence.py --enforcement --selftest"],
                       capture_output=True, text=True)
    for ln in r.stdout.splitlines():
        pid, _, cmd = ln.partition(" ")
        if cmd.split() and cmd.split()[0].rsplit("/", 1)[-1].startswith("python"):
            try:
                cwd = _os.readlink(f"/proc/{pid}/cwd")
            except OSError:
                cwd = None                      # undeterminable stays refused
            if cwd is not None and _os.path.realpath(cwd) != mine:
                continue                        # another tree; it cannot touch ours
            return ["an enforcement SELFTEST is running — it mutates these very "
                    "sources, so a baseline taken now is a snapshot of injected "
                    "breakage. Wait for it to finish."]
    return []


def crash_findings(findings: list[str]) -> list[str]:
    """Findings that report the machinery breaking, never a real baseline.

    A `NameError` in a reporter is either a bug to fix or selftest residue. It is
    not a stable difference between two engines, so freezing one as "expected"
    launders a fault into the reference every later stage trusts.
    """
    marks = ("raised NameError", "raised AttributeError", "raised TypeError",
             "raised KeyError", "REPORTER CRASHES", "RECORDED SIDE UNREADABLE")
    return [f for f in findings if any(m in f for m in marks)]


def run_audit(scoring: Path) -> tuple[list[str], list[str], dict]:
    """Returns (raw findings, printed undeclared lines, context)."""
    r = subprocess.run([sys.executable, "-c", DRIVER], cwd=scoring,
                       capture_output=True, text=True, timeout=7200)
    text = r.stdout + r.stderr
    raw: list[str] = []
    for ln in text.splitlines():
        if ln.startswith(RAWMARK):
            raw = [" ".join(p for p in f if p and p != "-").strip()
                   for f in json.loads(ln[len(RAWMARK):])]
            break
    else:
        raise SystemExit(f"the audit driver produced no {RAWMARK} line:\n"
                         f"{text[-2000:]}")
    undeclared = sorted(re.sub(r"^!\s*-*\s*", "", ln).rstrip()
                        for ln in text.splitlines() if ln.startswith("! "))
    ctx = {}
    for ln in text.splitlines():
        m = re.match(r"^(\d+) UNDECLARED enforcement difference", ln)
        if m:
            ctx["undeclared_reported"] = int(m.group(1))
        for key in ("paper scoring:", "engine reading:", "engine scoring:",
                    "paper-vs-web arithmetic:"):
            if ln.startswith(key):
                ctx[key.rstrip(":")] = ln.strip()
    return sorted(raw), undeclared, ctx


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--scoring", default=None)
    a = ap.parse_args()

    scoring = Path(a.scoring) if a.scoring else Path.cwd()
    if not (scoring / "equivalence.py").exists():
        print(f"no equivalence.py under {scoring} — pass --scoring")
        return 2

    for u in tree_is_quiescent(scoring):
        print("WARNING:", u)
    before = source_hash(scoring)
    raw, undeclared, ctx = run_audit(scoring)
    after = source_hash(scoring)
    print(f"audit: {len(raw)} RAW finding(s); "
          f"{ctx.get('undeclared_reported', '?')} undeclared")

    if a.write:
        blockers = tree_is_quiescent(scoring)
        if before != after:
            blockers.append(f"the sources CHANGED under the audit "
                            f"({before} -> {after}) — something is editing them")
        crashes = crash_findings(raw)
        if crashes:
            blockers.append(f"{len(crashes)} finding(s) report the machinery "
                            f"crashing, never a legitimate baseline entry: "
                            f"{crashes[0][:90]}")
        if blockers:
            print("REFUSED — will not freeze a baseline from this tree:")
            for b in blockers:
                print("   ", b)
            return 2
        # IS THE LEDGER THIS WAS TAKEN FROM A FABRICATED ONE? A dry-run sandbox
        # may carry columns stamped fresh without a sweep. A baseline taken there
        # is still the right thing for later stages to diff against -- they run on
        # that tree -- but it must never be mistaken for the live figure, so the
        # provenance travels inside the golden.
        fabricated = False
        try:
            fabricated = "DRYRUN_FABRICATED_LEDGER" in json.loads(
                (scoring / "MEASURED.json").read_text())
        except Exception:
            pass
        if fabricated:
            print("NOTE: this baseline is taken on a FABRICATED ledger — it "
                  "describes the sandbox, never the real corpus")
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(
            {"fabricated_ledger": fabricated,
             "raw_findings_total": len(raw),
             "undeclared_reported": ctx.get("undeclared_reported"),
             "source_hash": after,
             "context": {k: v for k, v in ctx.items()
                         if k != "undeclared_reported"},
             "raw": raw, "undeclared": undeclared}, indent=1))
        print(f"froze the baseline -> {GOLDEN}")
        print(f"  RAW findings      : {len(raw)}   <- what the gates compare")
        print(f"  undeclared header : {ctx.get('undeclared_reported')}")
        print(f"  source hash       : {after}")
        print("\nUPDATE THE PLAN'S BASELINE TABLE with these two numbers "
              "whenever a stage changes them (§0). Never quote them from memory.")
        return 0

    if not GOLDEN.exists():
        print(f"no baseline at {GOLDEN} — run with --write first")
        return 1
    was = json.loads(GOLDEN.read_text())
    old, new = Counter(was["raw"]), Counter(raw)
    added, removed = new - old, old - new
    if was.get("source_hash") and was["source_hash"] != after:
        print(f"note: sources moved since the baseline was taken "
              f"({was['source_hash']} -> {after}) — a change below is expected "
              f"only if this stage caused it")
    if not added and not removed:
        print(f"RAW finding-set IDENTICAL to the baseline "
              f"({sum(new.values())} finding(s), duplicates included)")
        return 0
    print(f"RAW FINDING-SET MOVED: +{sum(added.values())} / -{sum(removed.values())}")
    for s, n in sorted(added.items()):
        print(f"   ADDED   x{n} {s[:140]}")
    for s, n in sorted(removed.items()):
        print(f"   REMOVED x{n} {s[:140]}")
    if removed:
        print("\n  A REMOVAL IS NOT AUTOMATICALLY GOOD. Attribute each one to "
              "this stage's own work, or a check has stopped looking (C1).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
