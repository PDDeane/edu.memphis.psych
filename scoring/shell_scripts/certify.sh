#!/usr/bin/env bash
# Certification, in two levels, because there are two questions.
#
#   ./certify.sh gate     the fast one, for every change        (~3 min)
#   ./certify.sh full     the heavy one, before committing      (~1 h+)
#
# WHY THIS EXISTS. Until 2026-09-27 "certification" was a sequence somebody
# reassembled from memory each time -- editguard, tsc, vitest, the audit,
# injection_reach, the self-test. Nothing enforced the list, nothing recorded
# that it had been run, and a step dropped silently was indistinguishable from
# a step that passed. `precommit_gate.py` covers the audit and the student-text
# gate; it is a commit gate, not a certification.
#
# A SKIPPED STEP IS NOT A PASSED STEP, and this script will not pretend
# otherwise: every step is recorded PASS / FAIL / SKIPPED, the receipt names
# which, and the exit status is non-zero if ANY step did not pass. That is the
# same rule the checks themselves are held to -- "a check that cannot run is
# not a check that passed".
#
# GENERIC. Nothing here names a course. The namespace, the rubric and the forms
# come from `paths.roots()`, which reads the content collection's manifest, so a
# second course certifies with the same script and no edit.
set -uo pipefail

LEVEL="${1:-gate}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENGINE="$(cd "$HERE/.." && pwd)"
REPO="$(cd "$ENGINE/.." && pwd)"
cd "$ENGINE" || exit 2

# THE TREE THIS CERTIFIES, stated rather than assumed. A run against the wrong
# tree is worse than no run: it reports green about something nobody asked about.
LO="$(python3 -c 'import paths; print(paths.LO)' 2>/dev/null)"
NS="$(python3 -c 'import paths; print(paths.roots().ns)' 2>/dev/null)"
RUBRIC="$(python3 -c 'import paths; print(paths.RUBRIC_ID)' 2>/dev/null)"
if [ -z "$NS" ] || [ -z "$LO" ]; then
  echo "certify: cannot resolve the tree from paths.py -- refusing to report on it"
  exit 2
fi

STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="${CERTIFY_OUT:-$(python3 -c 'import paths; print(paths.OUT)')}/certify-$STAMP"
mkdir -p "$OUT"
RECEIPT="$OUT/receipt.txt"

PASS=0; FAIL=0; SKIP=0
say() { printf '%s\n' "$*" | tee -a "$RECEIPT"; }

say "certification: level=$LEVEL  namespace=$NS  rubric=$RUBRIC"
say "  engine:   $ENGINE"
say "  lo-blocks:$LO"
say "  receipt:  $RECEIPT"
say ""

# step NAME REASON-IF-UNRUNNABLE COMMAND...
step() {
  local name="$1" guard="$2"; shift 2
  local t0 rc; t0=$(date +%s)
  if [ -n "$guard" ]; then
    say "  SKIPPED  $name -- $guard"
    SKIP=$((SKIP+1)); return
  fi
  "$@" > "$OUT/$name.log" 2>&1; rc=$?
  local secs=$(( $(date +%s) - t0 ))
  if [ $rc -eq 0 ]; then
    say "  PASS     $name (${secs}s)"; PASS=$((PASS+1))
  else
    say "  FAIL     $name (${secs}s, exit $rc) -> $OUT/$name.log"
    FAIL=$((FAIL+1))
  fi
}

# ---- LEVEL 1: THE GATE ------------------------------------------------------
say "GATE"
step editguard        "" python3 tools/editguard.py
step tsc              "" bash -c "cd '$LO' && npx tsc --noEmit -p packages/shared"
step enforce-suite    "" bash -c "cd '$LO' && npx vitest run packages/shared/lib/llm/enforce/enforce.test.ts"
# THE AUDIT IS READ BY THE PREPARED CLASSIFIER, NOT BY ITS EXIT CODE.
# `precommit_gate.py` is the thing that already answers "is this committable",
# and it answers it correctly in a way a shell test cannot: `print_enforcement`
# returns `1 if findings else 0` and an uncaught exception ALSO exits 1, so
# "non-zero means broken" would refuse every ordinary run that found something.
# Its test is POSITIVE LIVENESS -- did the audit print its banner -- because a
# crashed audit emits no findings and once printed "clean" while reaching not a
# single check. Running `equivalence.py` here and reading the exit code would
# have reinvented that bug.
#
# IT HONOURS ALLOW_UNDECLARED, which is the sanctioned override and records
# itself. Certification does not get its own back door.
step audit            "" python3 precommit_gate.py
step injection-reach  "" python3 tools/injection_reach.py

# DOES EVERY NATIVE ASSEMBLER READ THE SOURCE IT CLAIMS TO? The sibling
# question to injection-reach, and it belongs HERE rather than in the self-test:
# its injections are on disk, and a disk case cannot overlap a forked audit --
# it forces a barrier. The self-test runs in parallel and takes ~20 minutes;
# a barrier per assembler would serialise it into hours.
step assembler-reach  "" python3 tools/assembler_reach.py

if [ "$LEVEL" != "full" ]; then
  say ""
  say "$PASS passed, $FAIL failed, $SKIP skipped.  GATE ONLY -- this is not a certification."
  say "Run \`./certify.sh full\` before committing major changes."
  [ $FAIL -eq 0 ] || exit 1
  exit 0
fi

# ---- LEVEL 2: THE FULL CERTIFICATION ---------------------------------------
say ""
say "FULL"

# The self-test: does the audit notice when a rule is broken? ~20 min parallel.
step selftest "" env SELFTEST_WORKERS="${SELFTEST_WORKERS:-12}" \
     python3 equivalence.py --enforcement --selftest

# ONE RUN PER ITEM, BOTH SIDES. This is a REACHABILITY check and NOT a
# measurement, and the script says so because the sweep scripts do: "a number
# produced with RUNS=1 should not be quoted". One draw per cell cannot separate
# a real difference from sampling -- Q3 once measured a 4-cell spread across
# three runs. What this answers is narrower and still worth answering: does
# every item still reach each scorer and come back with an answer at all.
ONE="$OUT/one-run"
mkdir -p "$ONE"
# THE IDMAP IS AN ARGUMENT, and passing "" made `sweep_app.sh` exit on its own
# usage guard -- a step that fails before it starts. Found by reading the script
# rather than by running it, which would have cost the whole gate first.
# NEWEST BY VERSION, not by mtime: a re-copied older map would otherwise win.
IDMAP="$(ls -1 "$(python3 -c 'import paths; print(paths.roots().out)')"/idmap_v*.json 2>/dev/null \
         | sed 's/.*idmap_v\([0-9]*\)\.json/\1 &/' | sort -rn | head -1 | cut -d' ' -f2-)"
if [ -z "$IDMAP" ]; then
  step run-web-1x "no idmap_v*.json under the out root; the web sweep cannot be driven" true
else
  step run-web-1x   "" bash "$REPO/scorers/shell_scripts/sweep_app.sh" "$ONE/web" "$IDMAP" 1
fi
step run-paper-1x "" bash "$REPO/scorers/shell_scripts/sweep_paper.sh" "$ONE/paper" 1 lo

# EVERY FORM THE ACTIVE RUBRIC CARRIES, walked in a real browser. The smoke
# config's own note: "all-activities test visits every page serially".
#
# IT NEEDS A SERVER, AND NOT THE DEFAULT ONE. `playwright.smoke.config.ts`
# defaults to localhost:8888, which is a DIFFERENT tree; certifying this one
# against that one is the failure this guard exists to prevent. SMOKE_URL must
# be set deliberately.
if [ -z "${SMOKE_URL:-}" ]; then
  step walkthrough "SMOKE_URL is unset, and the config defaults to :8888 which may be another tree -- start this tree's server and set SMOKE_URL" true
else
  step walkthrough "" bash -c "cd '$LO' && SMOKE_URL='$SMOKE_URL' npm run smoke"
fi

say ""
say "$PASS passed, $FAIL failed, $SKIP skipped."
if [ $SKIP -ne 0 ]; then
  say "CERTIFICATION INCOMPLETE: a skipped step is not a passed step."
fi
if [ $FAIL -eq 0 ] && [ $SKIP -eq 0 ]; then
  say "CERTIFIED  $NS / $RUBRIC  at $STAMP"
  exit 0
fi
exit 1
