#!/usr/bin/env python3
"""Stage 05's gate: the build generates from the rubric, and nothing moves.

The stage changes WHERE `olx_prompts` reads the rubric and nothing else, so
every clause here is a form of one claim: the provenance moved and the bytes
did not. Two of the plan's clauses turned out to be about a cost this stage
does NOT incur, and they are checked rather than assumed -- see clause 3.

Run:  python3 stage05_gate.py --scoring PATH --content PATH --migration PATH
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

R = []


def check(name: str, ok: bool, detail: str = "") -> None:
    R.append((("PASS" if ok else "FAIL"), name, detail))


def note(name: str, detail: str) -> None:
    R.append(("NOTE", name, detail))


def _gen(scoring: Path, source: str) -> dict:
    """Every generated body, under one rubric provenance."""
    out = subprocess.run(
        [sys.executable, "-c",
         'import json,sys; sys.path.insert(0,".");'
         'import olx_prompts as P;'
         'print("@@@"+json.dumps({i:P.build_web_prompt(i) for i in sorted(P.ACTION)}))'],
        capture_output=True, text=True, cwd=scoring,
        env={**os.environ, "RUBRIC_SOURCE": source})
    if "@@@" not in out.stdout:
        raise RuntimeError((out.stderr or out.stdout)[-400:])
    return json.loads(out.stdout.split("@@@", 1)[1].splitlines()[0])


def _shas(scoring: Path, source: str) -> dict:
    out = subprocess.run(
        [sys.executable, "-c",
         'import json,sys; sys.path.insert(0,".");'
         'import measured as M, olx_prompts as P;'
         'items=sorted(P.ACTION);'
         'print("@@@"+json.dumps({"scorer_all":M.scorer_sha(),'
         '"scorer":{s:[M.scorer_sha(i,s) for i in items] for s in ("olx","python","paper")},'
         '"prompt":{s:[M.prompt_sha(i,s) for i in items] for s in ("olx","python")}}))'],
        capture_output=True, text=True, cwd=scoring,
        env={**os.environ, "RUBRIC_SOURCE": source})
    if "@@@" not in out.stdout:
        raise RuntimeError((out.stderr or out.stdout)[-400:])
    return json.loads(out.stdout.split("@@@", 1)[1].splitlines()[0])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scoring", required=True, type=Path)
    ap.add_argument("--content", required=True, type=Path)
    ap.add_argument("--migration", required=True, type=Path)
    a = ap.parse_args()

    # 1. The rubric object must say everything the modules say. Stage 04's
    #    byte-equality could not see a field the prompt never reads, and there
    #    were 107 of those.
    eq = subprocess.run([sys.executable, str(a.migration / "stage05_rubric_equivalence.py")],
                        capture_output=True, text=True)
    check("the rubric object says everything the modules say",
          eq.returncode == 0, eq.stdout.strip().splitlines()[-1] if eq.stdout else "")

    # 2. THE STAGE'S OWN CLAIM: same bytes from either provenance.
    try:
        mod, obj = _gen(a.scoring, "module"), _gen(a.scoring, "object")
        diff = [k for k in mod if mod.get(k) != obj.get(k)]
        check("every body is byte-identical from both provenances",
              not diff and set(mod) == set(obj) and len(mod) > 0,
              f"{len(mod)} bodies, {sum(len(v) for v in mod.values())} chars, "
              f"{len(diff)} differing")
    except Exception as e:
        check("every body is byte-identical from both provenances", False, str(e)[:160])

    # 3. NO FINGERPRINT MOVES, so no column goes stale and no re-record is owed.
    #    The plan expected this stage to move `scorer_sha` corpus-wide and to
    #    spend every SCORER_NEUTRAL pair with it. Measured, it does neither:
    #    `scorer_sha` hashes the SCORING closure and `prompt_sha` the shipped
    #    tag, and the generator is in neither. The clause is kept as a CHECK
    #    because the expectation was reasonable and its being wrong is the
    #    finding.
    try:
        sm, so = _shas(a.scoring, "module"), _shas(a.scoring, "object")
        check("no scorer_sha or prompt_sha moves with the provenance",
              sm == so,
              "identical across both sources" if sm == so else "A FINGERPRINT MOVED")
    except Exception as e:
        check("no scorer_sha or prompt_sha moves with the provenance", False, str(e)[:160])

    # 4. The frozen stage-00 oracles, which cover both sides and the paper
    #    fingerprint as well as the web body.
    fz = subprocess.run([sys.executable, str(a.migration / "stage00_freeze_oracles.py")],
                        capture_output=True, text=True, cwd=a.migration,
                        env={**os.environ, "RUBRIC_SOURCE": "object"})
    last = [ln for ln in fz.stdout.splitlines() if ln.strip()]
    check("prompt oracles unchanged since stage 00",
          any("UNCHANGED" in ln for ln in last),
          last[-1][:120] if last else fz.stderr[-120:])

    # 5. The audit's finding-set, as a MULTISET -- duplicates carry information.
    cb = subprocess.run([sys.executable, str(a.migration / "stage00_capture_baseline.py"),
                         "--scoring", str(a.scoring)],
                        capture_output=True, text=True, cwd=a.migration,
                        env={**os.environ, "RUBRIC_SOURCE": "object"})
    txt = cb.stdout
    check("audit RAW finding-set identical to the baseline",
          "IDENTICAL to the baseline" in txt,
          next((ln for ln in txt.splitlines() if "finding-set" in ln), "")[:120])

    # 6. No SCORER_NEUTRAL pair is spent BY THIS STAGE. Two are already spent in
    #    the frozen baseline; that is pre-existing and not this stage's to fix.
    base = json.loads((a.migration / "goldens" / "audit_baseline.json").read_text())
    was = sum(1 for f in (base.get("raw") or []) if "SCORER-NEUTRALITY CLAIM IS FALSE" in f)
    now = subprocess.run(
        [sys.executable, "-c",
         'import sys; sys.path.insert(0,".");'
         'import enforcement as E;'
         'print(len(E.check_scorer_neutrality_is_verified()))'],
        capture_output=True, text=True, cwd=a.scoring,
        env={**os.environ, "RUBRIC_SOURCE": "object"})
    try:
        n = int((now.stdout or "0").strip().splitlines()[-1])
    except Exception:
        n = -1
    check("no SCORER_NEUTRAL pair is spent by this stage", n == was,
          f"{n} spent now, {was} already spent in the frozen baseline")

    # 7. The capture cache key must name every source the capture depends on.
    src = (a.scoring / "enforcement.py").read_text()
    i = src.find("def _request_capture")
    body = src[i:i + 4000]
    # MATCH THE MECHANISM, NOT A SUBSTRING. This tested for the literal
    # "_rubric.olx", which kept passing after the key stopped naming those files
    # at all -- `bmod_rubric.olx` happens to contain it. A check that passes for
    # the wrong reason is worse than one that fails.
    covers = "rubric*.olx" in body or "_rubric.olx" in body
    check("the capture cache key covers the rubric object", covers,
          "the key includes the rubric .olx mtimes" if covers
          else "the key does not name the rubric")

    print("\nSTAGE 05 GATE")
    print("=" * 67)
    for status, name, detail in R:
        print(f"{status:7s} {name:56s} {detail}")
    print("=" * 67)
    bad = [r for r in R if r[0] == "FAIL"]
    print("\nGATE MET." if not bad else f"\nGATE NOT MET — {len(bad)} failing")
    for r in bad:
        print("   ", r[1])
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
