#!/usr/bin/env bash
# A simulated student clicks through the course and all three handouts.
#
# WHAT THIS ADDS TO `e2e_session.sh`. That one drives the SCORER: it runs each
# item through agreement_app.py, which reads the .olx and calls the grader
# directly, and it proves the rubric works. It never opens a page. This one
# opens the pages -- so it is the only check that can see a handout that will
# not render, an input that will not take text, a Next button that dead-ends,
# or a feedback button that never answers.
#
#   migration/student_session.sh [PORT]        # default 8899
#
# TWO TRAPS, BOTH PAID FOR:
#   * The client REFUSES TO BOOT on a port with no event-server route in
#     WS_PORT_MAP (packages/shared/lib/state/store.ts) -- it throws "no
#     event-server route configured" and the page renders "Failed to start."
#     The whole point of this check was a non-standard port, so the port has to
#     be added there first. Vite serves that module, so no server restart.
#   * Playwright's reporters BUFFER. Piping `--reporter=line` through grep gave
#     an empty file after seven minutes of real work. The JSON reporter writes a
#     file, which is what the acceptance row reads.
# Paths come from the environment, never from a literal. See
# migration_paths.py: a hard-coded sandbox path does not fail on a live
# tree, it succeeds against the sandbox, and every gate reports green.
: "${MIGRATION_ROOT:=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
: "${LO_BLOCKS:=/home/pdeane/code/update/lo-blocks}"
: "${MIGRATION_ENV:=$MIGRATION_ROOT/migration/env.sh}"

set -u
PORT=${1:-8899}
cd "$LO_BLOCKS"
OUT=${MOLLY_OUT:-$MOLLY_OUT}
mkdir -p "$OUT"
JSON="$OUT/student_session.json"

PLAYWRIGHT_JSON_OUTPUT_NAME="$JSON" \
SMOKE_URL="http://localhost:$PORT" \
  timeout 5400 npx playwright test \
    --config apps/client/playwright.smoke.config.ts student_session \
    --reporter=json > "$OUT/student_session.log" 2>&1
rc=$?

python3 - "$JSON" <<'PY'
import json, sys, pathlib
p = pathlib.Path(sys.argv[1])
if not p.exists():
    print("  NO RESULT FILE -- the run produced nothing"); raise SystemExit(1)
d = json.loads(p.read_text())
def walk(su):
    for s in su.get("specs", []): yield s
    for c in su.get("suites", []): yield from walk(c)
specs = [s for su in d.get("suites", []) for s in walk(su)]
ok = [s for s in specs if s.get("ok")]
bad = [s for s in specs if not s.get("ok")]
for s in specs:
    print(f"  {'PASS' if s.get('ok') else 'FAIL'}  {s.get('title','?')}")
for s in bad:
    for t in s.get("tests", []):
        for r in t.get("results", []):
            msg = (r.get("error") or {}).get("message", "")
            if msg: print("        " + " ".join(msg.split())[:200])
print(f"  {len(ok)}/{len(specs)} passed")
print("STUDENT_SESSION_DONE" if specs and not bad else "STUDENT_SESSION_FAILED")
PY
exit $rc
