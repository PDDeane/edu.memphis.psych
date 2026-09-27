#!/usr/bin/env python3
"""Call an enforcement rule that lives in lo-blocks. Goal K.

WHY THE RULES MOVE AND THE CHECKS DO NOT. The audit asks questions of three
subjects -- what was MEASURED, what OUR PYTHON does, and what the CONTENT says
-- and only the third can be answered by the package that owns the content.
For those, the python `check_*` stays: it knows where the inputs live and it is
what `equivalence.py` invokes. What moves is the JUDGEMENT, to a function in
`packages/shared/lib/llm/enforce/`, where vitest can exercise it against its
own fixtures and where it sits beside the code it is judging.

THE BRIDGE IS ONE PROCESS PER CALL, deliberately. `check_slot_grammars.py` and
`check_ref_grammars.py` already ran `tsx` this way and have been reliable; a
long-lived node service would be faster and would add a second thing that can
be stale, which is the failure `agreement_app.server_code_is_stale` exists to
catch and which cost 19 mis-scored observations on 2026-09-09.

A BROKEN BRIDGE IS A FINDING, NEVER A PASS. Every failure path here returns a
finding saying the rule could not be RUN. `tsx` missing, a syntax error in the
rule, a timeout -- each of those means the question was not asked, and a check
that reports clean because it never ran is the exact defect this audit exists
to prevent.
"""
from __future__ import annotations

import json
import os
import atexit as _atexit
import selectors as _selectors
import subprocess
import threading as _threading
import time as _time


RUNNER = "packages/shared/lib/llm/enforce/runner.ts"
TIMEOUT = 300


def _bridge_env() -> dict:
    """The environment the TypeScript side is handed.

    ONE RESOLUTION, NOT TWO. `paths` resolves the course roots -- environment,
    then the rubric's own declaration, then the historical fallback -- and the
    bridge passes the ANSWER across rather than letting the other side work it
    out again. `courseData.ts` can read the rubric itself, and does when it is
    run standalone, but in the normal path it is told; two resolvers that agree
    today are two resolvers that can stop agreeing, which is the divergence
    class this whole package exists to close.

    `COURSE_REPO` is passed because the TypeScript side has no `__file__` to
    anchor on: python knows where the repository is, so it says.
    """
    import os

    import paths

    return {**os.environ,
            "COURSE_DATA": str(paths.roots().data),
            "COURSE_METADATA": str(paths.roots().metadata),
            "COURSE_REPO": str(paths.REPO)}


def available() -> str:
    """"" if the bridge can run, else why it cannot."""
    import paths

    tsx = paths.LO / "node_modules/.bin/tsx"
    if not tsx.exists():
        return (f"tsx is not installed at {tsx}, so the lo-blocks rules cannot "
                f"be run -- which is NOT the same as their passing")
    if not (paths.LO / RUNNER).exists():
        return f"the rule runner is missing at {paths.LO / RUNNER}"
    return ""


# ONE WARM PROCESS, because starting tsx costs ~1.6s and the audit asks one rule
# at a time. Measured 2026-09-25 at eighteen ported checks: the SELFTEST runs the
# whole audit once per injection case, so 18 x 19 spawns put ~9 minutes of pure
# process startup into a single verification -- and the run was killed by a
# ceiling set before those ports existed. The cost is LINEAR IN PORTS, so goal K
# was making the audit's own verification more expensive with every step.
#
# The server is started on first use and reused. EVERY FAILURE FALLS BACK to the
# one-shot path below rather than becoming a finding: a warm process is an
# optimisation, and an optimisation that can report a rule as broken is worse
# than the cost it saves.
_SERVER = None
_SERVER_BUF = b""
# The pid that started `_SERVER`. See `_server`: a fork must not reuse it.
_SERVER_PID = None
_SERVER_LOCK = _threading.Lock()


def _server():
    """The live runner process, started if needed. None if it cannot be had.

    FORK-AWARE, AND IT HAS TO BE. `_SERVER` is a module global holding a pipe to
    one node process. `equivalence --selftest` FORKS its audits, so a child
    inherits this handle and, without the pid check below, would write its
    requests into the SAME stdin its parent and every sibling are using. The
    replies interleave and each reader takes whichever line arrives first: not a
    crash, just wrong findings, in the suite whose whole job is to be trusted.
    The serial path never exposed it because nothing forked.

    A CHILD STARTS ITS OWN and never touches the inherited one -- it is the
    parent's to close, and killing it here would take the server out from under
    the process that owns it.
    """
    global _SERVER, _SERVER_BUF, _SERVER_PID
    import paths

    if (_SERVER is not None and _SERVER_PID == os.getpid()
            and _SERVER.poll() is None):
        return _SERVER
    # INHERITED ACROSS A FORK, or simply dead: drop the handle WITHOUT touching
    # the process behind it. If it is the parent's, the parent will close it.
    _SERVER, _SERVER_BUF = None, b""
    try:
        _SERVER = subprocess.Popen(
            [str(paths.LO / "node_modules/.bin/tsx"), RUNNER, "--serve"],
            cwd=str(paths.LO), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, env=_bridge_env(), bufsize=0)
        # STAMPED WITH THE OWNER. Everything above turns on this being the pid
        # that created the handle, so it is set where the handle is.
        _SERVER_PID = os.getpid()
    except Exception:                                       # pragma: no cover
        _SERVER = None
    return _SERVER


def _stop_server() -> None:
    """Leave no node process behind. Registered atexit.

    ONLY THE PROCESS THAT STARTED IT may stop it. A forked child exits through
    `os._exit`, which skips atexit entirely, so this is belt and braces -- but a
    child that ever did run it would kill the PARENT's runner mid-audit.
    """
    global _SERVER
    p, _SERVER = _SERVER, None
    if p is None or p.poll() is not None:
        return
    if _SERVER_PID != os.getpid():
        return
    # CLOSE, THEN TERMINATE, THEN KILL. Closing stdin ends the serve loop and is
    # the clean exit, but it is not guaranteed: measured 2026-09-25, one runner
    # in three survived a stdin-close-and-wait and was still alive afterwards.
    # A node process left holding inotify watches is how this tree exhausted the
    # watch limit before, so the last step is not optional.
    for step in ("close", "terminate", "kill"):
        try:
            if step == "close" and p.stdin:
                p.stdin.close()
            elif step == "terminate":
                p.terminate()
            elif step == "kill":
                p.kill()
            p.wait(timeout=2)
            return
        except Exception:
            continue


_atexit.register(_stop_server)


def _serve_call(req: dict, timeout: float):
    """One request through the warm process, or None to fall back.

    Reads until a line PARSES, because tsx and the loader print warnings to
    stdout before the first answer; a reader that took the first line would
    mistake a warning for a refusal.
    """
    global _SERVER_BUF
    with _SERVER_LOCK:
        p = _server()
        if p is None or p.stdin is None or p.stdout is None:
            return None
        deadline = _time.monotonic() + timeout
        try:
            p.stdin.write((json.dumps(req) + "\n").encode())
            p.stdin.flush()
        except Exception:
            _stop_server()
            return None
        sel = _selectors.DefaultSelector()
        sel.register(p.stdout, _selectors.EVENT_READ)
        try:
            while True:
                while b"\n" in _SERVER_BUF:
                    line, _SERVER_BUF = _SERVER_BUF.split(b"\n", 1)
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        return json.loads(line.decode("utf-8", "replace"))
                    except Exception:
                        continue          # a loader warning, not an answer
                left = deadline - _time.monotonic()
                if left <= 0 or not sel.select(left):
                    _stop_server()
                    return None
                chunk = p.stdout.read1(65536) if hasattr(p.stdout, "read1") \
                    else p.stdout.read(65536)
                if not chunk:
                    _stop_server()
                    return None
                _SERVER_BUF += chunk
        finally:
            sel.close()


def run(check: str, payload) -> list[str]:
    """Findings from the lo-blocks rule named `check`.

    Returns the rule's own findings, or a single finding explaining why it could
    not be asked. Never raises: the audit calls this from inside a check and an
    exception there would take down the whole run over one bridge failure.
    """
    import paths

    why = available()
    if why:
        return [why]
    # THE WARM PATH FIRST, the one-shot below as the fallback. Same request,
    # same answer shape; only the process differs.
    doc = _serve_call({"check": check, "payload": payload}, TIMEOUT)
    if doc is not None:
        if "error" in doc:
            return [f"the lo-blocks rule {check!r} refused: {doc['error']}"]
        return list(doc.get("findings") or [])

    req = json.dumps({"check": check, "payload": payload})
    try:
        r = subprocess.run(
            [str(paths.LO / "node_modules/.bin/tsx"), RUNNER],
            cwd=str(paths.LO), input=req, capture_output=True, text=True,
            timeout=TIMEOUT, env=_bridge_env())
    except subprocess.TimeoutExpired:
        return [f"the lo-blocks rule {check!r} did not answer within {TIMEOUT}s, "
                f"so it was not asked"]
    except Exception as e:                                  # pragma: no cover
        return [f"the lo-blocks rule {check!r} could not be started: "
                f"{type(e).__name__}: {e}"]
    if r.returncode != 0:
        return [f"the lo-blocks rule {check!r} exited {r.returncode}: "
                f"{(r.stderr or '').strip()[:300]}"]
    # THE LAST LINE, because tsx and the loader may print warnings before it.
    try:
        doc = json.loads((r.stdout or "").strip().splitlines()[-1])
    except Exception as e:
        return [f"the lo-blocks rule {check!r} produced no readable answer "
                f"({type(e).__name__}: {e}): {(r.stdout or '')[:200]}"]
    if "error" in doc:
        return [f"the lo-blocks rule {check!r} refused: {doc['error']}"]
    return list(doc.get("findings") or [])


class ProbeFailed(RuntimeError):
    """A probe could not answer. Never the same as answering nothing."""


def probe(name: str, payload):
    """THIS SIDE's answer from a lo-blocks probe, for a python caller comparing
    it against python's own.

    RAISES where `run` returns a finding, and the difference is the whole point.
    A rule's caller wants findings and an empty list means the rule holds; a
    probe's caller is about to COMPARE, and an empty list means TypeScript
    produced nothing. Handing that back as data would be read as "the two
    implementations agree that there is nothing here" -- the false agreement
    these grammar checks exist to catch.
    """
    import paths

    why = available()
    if why:
        raise ProbeFailed(why)
    req = json.dumps({"probe": name, "payload": payload})
    try:
        r = subprocess.run(
            [str(paths.LO / "node_modules/.bin/tsx"), RUNNER],
            cwd=str(paths.LO), input=req, capture_output=True, text=True,
            timeout=TIMEOUT, env=_bridge_env())
    except Exception as e:
        raise ProbeFailed(f"the lo-blocks probe {name!r} could not be run: "
                          f"{type(e).__name__}: {e}") from e
    if r.returncode != 0:
        raise ProbeFailed(f"the lo-blocks probe {name!r} exited "
                          f"{r.returncode}: {(r.stderr or '').strip()[:300]}")
    try:
        doc = json.loads((r.stdout or "").strip().splitlines()[-1])
    except Exception as e:
        raise ProbeFailed(f"the lo-blocks probe {name!r} produced no readable "
                          f"answer ({type(e).__name__}: {e}): "
                          f"{(r.stdout or '')[:200]}") from e
    if "error" in doc:
        raise ProbeFailed(f"the lo-blocks probe {name!r} refused: {doc['error']}")
    return doc.get("result")


def run_many(requests: list[tuple[str, object]]) -> list[list[str]]:
    """Findings for several rules, in ONE tsx process.

    Starting tsx costs ~1.4s measured, and the audit asks one rule at a time,
    so every rule goal K ports adds that much to every audit -- ~45s at the ~32
    the sort says are portable. A batch pays it once.

    Returns one finding list per request, IN ORDER. A member that fails becomes
    a one-element list saying so, exactly as `run` does: a batch must not let
    one broken rule report the others as passing, nor lose its own failure.
    """
    import paths

    why = available()
    if why:
        return [[why] for _ in requests]
    if not requests:
        return []
    req = json.dumps({"batch": [{"check": c, "payload": p} for c, p in requests]})
    try:
        r = subprocess.run(
            [str(paths.LO / "node_modules/.bin/tsx"), RUNNER],
            cwd=str(paths.LO), input=req, capture_output=True, text=True,
            timeout=TIMEOUT)
        doc = json.loads((r.stdout or "").strip().splitlines()[-1])
        got = doc["batch"]
        if len(got) != len(requests):
            raise ValueError(f"asked {len(requests)}, answered {len(got)}")
    except Exception as e:
        return [[f"the lo-blocks batch could not be run ({type(e).__name__}: "
                 f"{e}), so {c!r} was not asked"] for c, _ in requests]
    out = []
    for (check, _), d in zip(requests, got):
        if "error" in d:
            out.append([f"the lo-blocks rule {check!r} refused: {d['error']}"])
        else:
            out.append(list(d.get("findings") or []))
    return out


def self_test() -> int:
    """The bridge must carry a FIRE, not merely a clean answer.

    The vitest suite proves the rule fires; this proves the WIRE does -- that a
    finding raised in TypeScript arrives in python as a finding, and that a
    clean input arrives as silence. Every rule ported under goal K reports zero
    against the live corpus, so a bridge that always returned `[]` would look
    exactly like a passing audit.
    """
    bad = 0
    fires = run("no_case_names_in_prompts",
                {"prompts": [{"item": "Q6", "text": "Unlike p10, be specific."}]})
    if len(fires) != 1 or "p10" not in fires[0]:
        bad += 1
        print(f"  FAIL: the bridge did not carry the fire: {fires}")
    quiet = run("no_case_names_in_prompts",
                {"prompts": [{"item": "Q1", "text": "Name the behaviour."}]})
    if quiet:
        bad += 1
        print(f"  FAIL: the bridge invented a finding on clean input: {quiet}")
    unknown = run("no_such_rule", {})
    if len(unknown) != 1 or "refused" not in unknown[0]:
        bad += 1
        print(f"  FAIL: an unknown rule must be a finding, not silence: {unknown}")
    try:
        got = probe("parse_slot_specs", {"specs": ["x:met/absent"]})
        if not got or not got[0]:
            bad += 1
            print(f"  FAIL: the probe wire carried nothing: {got}")
    except ProbeFailed as e:
        bad += 1
        print(f"  FAIL: the probe wire is broken: {e}")
    try:
        probe("no_such_probe", {})
        bad += 1
        print("  FAIL: an unknown probe must RAISE, not answer")
    except ProbeFailed:
        pass
    # THE BATCH KEEPS ITS MEMBERS APART. One broken rule in a batch must not
    # report the others as passing, and must not lose its own failure -- which
    # is the whole risk of paying one process for many answers.
    got = run_many([
        ("no_case_names_in_prompts", {"prompts": [{"item": "Q6", "text": "p10"}]}),
        ("no_case_names_in_prompts", {"prompts": [{"item": "Q1", "text": "clean"}]}),
        ("no_such_rule", {}),
    ])
    if len(got) != 3 or len(got[0]) != 1 or got[1] != [] or "refused" not in got[2][0]:
        bad += 1
        print(f"  FAIL: the batch did not keep its members apart: {got}")
    print(f"  lo_enforce self-test: {'ok' if not bad else f'{bad} failure(s)'}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(self_test())
