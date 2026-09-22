#!/usr/bin/env python3
"""Stage 00 · freeze the prompt oracles for all 26 items, both sides.

WHAT THIS IS FOR. Every later stage promises "the question the model is asked
does not change". That promise is only checkable against a frozen copy taken
BEFORE the first edit, so this runs first and its output is the reference every
later stage diffs against.

WHAT IS FROZEN, AND WHY NOT THE OBVIOUS THING. The plan says "freeze the web
prompt bodies". The assembled prompt cannot be frozen: `ask_sha` builds it per
cell as `build_prompt(act["body"], fixture)`, so the assembled text CONTAINS THE
STUDENT'S SUBMISSION. These goldens live in a PUBLIC repository, and the
submissions carry real names in their OOXML metadata. So what is frozen is the
authored half -- the prompt BODY template and the response SCHEMA -- plus the
`ask_sha`, which is a hash and therefore safe to publish while still detecting a
change in the assembled result. The paper side stores `score.fingerprint_text`
in full, which is documented as "everything this scorer asks about item_id,
MINUS the submission".

THE LEAK GATE IS NOT ADVISORY. Before writing, every frozen string is checked
against the actual fixtures for overlap. A future refactor that starts folding
cell text into `body` would otherwise publish student writing silently, and the
gate turns that into a refusal instead.

Usage:
    stage00_freeze_oracles.py --write     create/refresh the goldens
    stage00_freeze_oracles.py            compare the tree against them (a gate)
"""
import argparse, hashlib, json, sys
from pathlib import Path

GOLDEN = Path(__file__).parent / "goldens" / "prompt_oracles.json"
WINDOW = 40          # substring length that counts as a leak


def _sha(t: str) -> str:
    return hashlib.sha256(t.encode()).hexdigest()[:12]


def collect() -> dict:
    import agreement as A, measured as M, olx_prompts as O, score as S
    out = {}
    for item in sorted(M._jobs()):
        job = M._jobs()[item]
        rec: dict = {"handout": job["handout"]}
        try:
            act = A.load_action(f"bmod_handout{job['handout']}.olx", O.ACTION[item])
            schema = A.build_schema(act["slots"], act["excluded"],
                                    act["show_checks"], act["cover"], act["choices"])
            rec["web_body"] = act["body"]
            rec["web_body_sha"] = _sha(act["body"])
            rec["schema"] = schema
            rec["schema_sha"] = _sha(json.dumps(schema, sort_keys=True))
            rec["slots"] = [s["key"] for s in act["slots"]]
        except Exception as e:
            rec["web_error"] = f"{type(e).__name__}: {e}"
        for side in ("olx", "python"):
            try:
                rec[f"prompt_sha_{side}"] = M.prompt_sha(item, side)
                rec[f"ask_sha_{side}"] = M.ask_sha(item, side)
            except Exception as e:
                rec[f"prompt_sha_{side}"] = f"ERR {type(e).__name__}"
        try:
            txt = S.fingerprint_text(item)
            rec["paper_fingerprint"] = txt
            rec["paper_fingerprint_sha"] = _sha(txt)
        except Exception as e:
            rec["paper_error"] = f"{type(e).__name__}: {e}"
        out[item] = rec
    return out


def leak_gate(frozen: dict) -> list[str]:
    """Does any frozen string contain ONE student's own writing? Refuse if so.

    THE NAIVE TEST DOES NOT WORK, measured: "is any fixture window present in the
    frozen text" fired 22 times on the first run and every one was boilerplate --
    `"at least 3 sentences explaining why you ch"` is the ASSIGNMENT'S OWN
    instruction, echoed back inside the student's field, and `"insufficient
    consumption of fruits and vegetables"` is a canned option the student picked.
    Both belong in an authored prompt body, and a gate that refuses them would
    block every stage for a leak that is not there.

    SAMPLE EVERY OFFSET, NOT EVERY 17th. Stepping through each submission at a
    fixed stride made the SAME shared sentence yield a DIFFERENT window per
    student -- their prefixes differ, so the stride lands elsewhere -- and each
    window then looked unique to one person. Q3's boilerplate "one week of
    baseline data collection and three weeks of intervention" fired eight times
    that way. Sliding by one makes a shared sentence produce IDENTICAL windows,
    which is what the uniqueness test needs to see. The published text is
    pre-cut into a set so the membership test stays O(1).

    UNIQUENESS ALONE IS STILL NOT ENOUGH, also measured. It left one finding
    standing -- Q1/p12's "insufficient consumption of fruits and vegetables" --
    which is a CANNED target-behaviour option that only p12 happened to pick. One
    student choosing an option does not make the option their writing.

    SO THE REAL TEST IS PROVENANCE, not content. `act["body"]` is loaded from the
    `.olx` and takes no fixture argument; `fingerprint_text` is documented as
    "minus the submission" and renders an EMPTY response. Neither is built from
    submissions, so every overlap is a student echoing the prompt, never the
    prompt echoing a student. A window is therefore a leak only if it is unique
    to one submission AND absent from the AUTHORED sources, which predate every
    submission. That keeps the gate meaningful -- a refactor that folds real cell
    text into a frozen string would put text there that no authored file
    contains, and this refuses it -- while staying silent on echoes and options.

    THE DISCRIMINATOR IS UNIQUENESS ACROSS THE COHORT. Text that several
    submissions carry verbatim came from the assignment, not from a person. So a
    window is a leak only if EXACTLY ONE participant's fixture has it. That keeps
    the gate sharp against the thing it exists to stop -- a refactor folding real
    cell text into `body` -- while staying quiet about shared scaffolding.
    """
    import agreement as A, measured as M
    authored = []
    for h in (1, 2, 3):
        try:
            authored.append(M._olx(h))
        except Exception:
            pass
    here = Path(__file__).resolve().parent.parent / "psych" / "scoring"
    for name in ("score.py", "olx_prompts.py", "agreement.py",
                 "rubric_h1.py", "rubric_h2.py", "rubric_h3.py"):
        f = here / name
        if f.exists():
            authored.append(f.read_text())
    AUTH = " ".join(" ".join(t.split()) for t in authored)
    bad = []
    for item, rec in frozen.items():
        published = "\n".join(str(rec.get(k, "")) for k in
                              ("web_body", "paper_fingerprint"))
        if not published.strip():
            continue
        excl = set(M.exclusions(item) or [])
        pub = {published[i:i + WINDOW]
               for i in range(max(0, len(published) - WINDOW + 1))}
        # window -> (field, {pids that have it})
        seen: dict[tuple[str, str], set[int]] = {}
        for pid in sorted(set(range(1, 21)) - excl):
            try:
                fx = A.fixture_for(item, pid)
            except Exception:
                continue
            for field, val in (fx or {}).items():
                s = " ".join(str(val).split())
                for i in range(max(0, len(s) - WINDOW + 1)):
                    w = s[i:i + WINDOW]
                    if w in pub:
                        seen.setdefault((field, w), set()).add(pid)
        reported = set()
        for (field, w), pids in sorted(seen.items()):
            if len(pids) != 1 or w in AUTH:
                continue
            pid = next(iter(pids))
            if (field, pid) in reported:   # one finding per field, not per window
                continue
            reported.add((field, pid))
            bad.append(f"{item}/p{pid} `{field}`: frozen text carries writing "
                       f"found in no authored source: {w!r}")
    return bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()

    now = collect()
    leaks = leak_gate(now)
    if leaks:
        print(f"REFUSED — {len(leaks)} frozen string(s) contain student writing:")
        for s in leaks[:10]:
            print("   ", s)
        return 2
    print(f"leak gate: clean across {len(now)} items (no {WINDOW}-char window "
          f"unique to one submission appears in a frozen string without also "
          f"appearing in an authored source)")

    if a.write:
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(now, indent=1, sort_keys=True))
        kb = GOLDEN.stat().st_size / 1024
        print(f"froze {len(now)} items -> {GOLDEN} ({kb:.0f} KB)")
        miss = [i for i, r in now.items() if "web_error" in r or "paper_error" in r]
        if miss:
            print(f"  NOTE {len(miss)} item(s) could not be fully assembled: "
                  f"{', '.join(sorted(miss))}")
        return 0

    if not GOLDEN.exists():
        print(f"no goldens at {GOLDEN} — run with --write first")
        return 1
    was = json.loads(GOLDEN.read_text())
    drift = []
    for item in sorted(set(was) | set(now)):
        if item not in was:
            drift.append(f"{item}: NEW item, not in the goldens")
            continue
        if item not in now:
            drift.append(f"{item}: GONE from the tree")
            continue
        for k in ("web_body_sha", "schema_sha", "paper_fingerprint_sha",
                  "ask_sha_olx", "ask_sha_python"):
            if was[item].get(k) != now[item].get(k):
                drift.append(f"{item}.{k}: {was[item].get(k)} -> {now[item].get(k)}")
    if drift:
        print(f"PROMPT ORACLE DRIFT — {len(drift)} change(s):")
        for d in drift:
            print("   ", d)
        return 1
    print(f"prompt oracles UNCHANGED across {len(now)} items, both sides")
    return 0


if __name__ == "__main__":
    sys.exit(main())
