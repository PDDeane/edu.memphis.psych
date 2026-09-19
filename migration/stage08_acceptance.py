import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parent))
import migration_paths as MP
#!/usr/bin/env python3
"""Stage 08 · acceptance: four zero-call instruments, then two that run it.

A FULL ACCEPTANCE SWEEP IS ~9,400 CALLS AND BUYS NOTHING HERE. The migration is
byte-neutral, so a sweep would re-sample the same distribution and return its own
noise. These four establish the same thing for zero:

    prompt oracles   the generated .olx bodies and all 26 `fingerprint_text`
                     values are what they were  (stage00_freeze_oracles.py)
    idmap            the RUNNING server serves exactly the current generated
                     prompt -- the gap the other three cannot close
    corpus replay    re-scoring frozen runs under the new code yields identical
                     scores, read from the audit's own control lines
    neutrality       the audit's finding SET, diffed against the frozen baseline

THE IDMAP ONE IS THE POINT. The first two are offline: they prove the bytes on
disk are right, not that the deployed system serves them. Its own docstring
records what that gap cost -- a sweep measured against a dump taken while a
reverted rule was still live, which nearly caused a good fixture repair to be
reverted on the strength of it.

THE LAST TWO ROWS ARE NOT FREE, AND THAT IS THE POINT. Every instrument above
is a comparison of bytes, and bytes can all be right while the thing does not
work. So one simulated student is put through all 26 items on the SCORER side,
and one is made to CLICK THROUGH the course and the three handouts in a real
browser -- answering every question, pressing every feedback button, taking Next
to the end of each handout. Between them they cost a few dozen calls, against
9,400 for a sweep. Neither re-runs on import: each reads the artefact its own
script left behind, and reports NOT RUN when there is none, because absence is
not a pass.

USE A DUMP THAT PREDATES THE WORK. Checking against a dump made after the
migration would be circular; the 06c run used `idmap_v145.json` from four days
earlier and got 23/23 current, which is the non-circular form of the claim.

    migration/e2e_session.sh 1            # scorer side, all 26 items
    migration/student_session.sh 8899     # browser side, course + 3 handouts
    python3 migration/stage08_acceptance.py <audit.log>
"""
import glob, json, os, re, subprocess, sys
from pathlib import Path

SC = MP.SCORING
MIG = Path(__file__).parent
sys.path.insert(0, str(SC))

# RUN FROM `scoring/`, ALWAYS. `check_engine_mechanisms_are_not_item_dependent`
# reads the engine sources by RELATIVE path, so an audit run from anywhere else
# reports four "cannot be parsed for item-gating" findings and the neutrality
# row fails with 32 against a frozen 28. The check is right to say so -- "the
# check cannot run, which is not the same as passing" -- and the first version
# of this script was simply standing in the wrong directory.
os.chdir(SC)


def rows():
    out = []

    # 1+2 — the frozen prompt oracles, both sides
    r = subprocess.run([sys.executable, str(MIG / "stage00_freeze_oracles.py")],
                       capture_output=True, text=True, cwd=str(SC), timeout=1800)
    txt = (r.stdout or "") + (r.stderr or "")
    out.append(("prompt oracles", txt.strip().splitlines()[-1][:90] if txt.strip() else "no output",
                "UNCHANGED" in txt))

    # 3 — the served prompt, against a dump that predates the work
    import agreement_app as A, olx_prompts as O
    dumps = sorted(glob.glob(os.path.join(os.environ.get("COURSE_OUT", ""), "*idmap*.json")),
                   key=os.path.getmtime)
    if not dumps:
        out.append(("idmap served-prompt", "NO DUMP FOUND -- not run, which is not a pass", False))
    else:
        dump, ok, bad = dumps[-1], 0, 0
        for item in sorted(O.ACTION):
            try:
                A.check_idmap_is_current(dump, item); ok += 1
            except BaseException:
                bad += 1
        out.append(("idmap served-prompt",
                    f"{ok}/{ok+bad} current against {os.path.basename(dump)}", bad == 0))

    # 4 — corpus replay, read from the audit's control lines
    log = sys.argv[1] if len(sys.argv) > 1 else None
    if log and Path(log).exists():
        t = Path(log).read_text()
        m = re.search(r"engine reading: (\d+) recorded response\(s\).*?(\d+) of them scored differently", t, re.S)
        out.append(("corpus replay", m.group(0)[:88] if m else "no control line",
                    bool(m) and m.group(2) == "0"))
    else:
        out.append(("corpus replay", "NO AUDIT LOG GIVEN -- pass one, do not re-derive", False))

    # 5 — enforcement neutrality, as a SET
    base = json.loads((MIG / "goldens" / "audit_baseline.json").read_text())
    import equivalence as Q
    def key(x):
        s = x if isinstance(x, str) else f"{x.get('kind','')} {x.get('msg','')}"
        s = " ".join(s.split())
        return re.sub(r"^[A-Za-z0-9]+ (?=[A-Z][A-Z ])", "", s)[:100]
    now = sorted(key(f"{f[1]} {f[2]}") for f in Q.enforcement_audit()[0])
    froz = sorted(key(x) for x in base["raw"])
    out.append(("enforcement neutrality",
                f"{len(now)} findings vs frozen {len(froz)}", now == froz))

    # 6 — one simulated student through every item, SCORER side
    #
    # The four instruments above are all byte comparisons. None of them runs the
    # thing. This one does: `e2e_session.sh` puts one participant through all 26
    # items and keeps each item's result, so a rubric that no longer produces a
    # cell shows up as a missing or not-ok result rather than as a clean diff.
    sess = Path(os.environ.get("COURSE_OUT", "")) / "e2e_session_p1"
    files = sorted(sess.glob("*.json")) if sess.exists() else []
    if not files:
        out.append(("e2e session (scorer)",
                    "NOT RUN -- migration/e2e_session.sh 1; absence is not a pass", False))
    else:
        scored = bad = 0
        for f in files:
            res = json.loads(f.read_text()).get("results") or []
            if res and all(r.get("ok") for r in res):
                scored += 1
            else:
                bad += 1
        out.append(("e2e session (scorer)",
                    f"{scored}/{len(files)} items scored, {bad} without a usable cell", bad == 0))

    # 7 — one simulated student CLICKING THROUGH the course and handouts
    #
    # THE ONLY CHECK THAT OPENS A PAGE. Everything else here reads files or
    # calls the grader directly, so all of it passes on a release whose handouts
    # will not render, whose inputs refuse text, or whose feedback button
    # answers nothing. Each of those is how a student would actually meet a
    # broken release, and none of them is a byte difference.
    js = Path(os.environ.get("COURSE_OUT", "")) / "student_session.json"
    if not js.exists():
        out.append(("student session (browser)",
                    "NOT RUN -- migration/student_session.sh; absence is not a pass", False))
    else:
        d = json.loads(js.read_text())
        def walk(su):
            for sp in su.get("specs", []):
                yield sp
            for c in su.get("suites", []):
                yield from walk(c)
        specs = [sp for su in d.get("suites", []) for sp in walk(su)]
        good = [sp for sp in specs if sp.get("ok")]
        out.append(("student session (browser)",
                    f"{len(good)}/{len(specs)} walked: course + three handouts",
                    bool(specs) and len(good) == len(specs)))
    return out


def main():
    res = rows()
    for what, detail, ok in res:
        print(f"  {'PASS' if ok else 'FAIL'}  {what:<24} {detail[:86]}")
    print("STAGE 08 GATE " + ("MET" if all(r[2] for r in res) else "NOT MET"))
    return 0 if all(r[2] for r in res) else 1


if __name__ == "__main__":
    raise SystemExit(main())
