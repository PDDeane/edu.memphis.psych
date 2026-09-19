#!/usr/bin/env bash
# One simulated student through EVERY item of all three handouts.
# Paths come from the environment, never from a literal. See
# migration_paths.py: a hard-coded sandbox path does not fail on a live
# tree, it succeeds against the sandbox, and every gate reports green.
: "${MIGRATION_ROOT:=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
: "${LO_BLOCKS:=/home/pdeane/code/update/lo-blocks}"
: "${MIGRATION_ENV:=$MIGRATION_ROOT/migration/env.sh}"

set -u
cd "$MIGRATION_ROOT/scoring"
source "$MIGRATION_ENV"
PID_=${1:-1}
IDMAP="$COURSE_OUT/e2e_idmap_8899.json"
OUTDIR="$COURSE_OUT/e2e_session_p$PID_"
mkdir -p "$OUTDIR"
ITEMS=$(python3 -c "import sys;sys.path.insert(0,'.');import agreement_app as A;print(' '.join(sorted(A.JOBS)))")
echo "items: $ITEMS"
ok=0; miss=0; fail=0
for it in $ITEMS; do
  if timeout 900 python3 agreement_app.py --item "$it" --participants "$PID_" --runs 1 \
        --idmap "$IDMAP" --out "$OUTDIR/$it.json" > "$OUTDIR/$it.log" 2>&1; then
    line=$(grep -E "^ +$PID_ +" "$OUTDIR/$it.log" | tail -1)
    if [ -n "$line" ]; then ok=$((ok+1)); echo "  $it: $line"
    else miss=$((miss+1)); echo "  $it: no cell (excluded or no fixture)"; fi
  else
    fail=$((fail+1)); echo "  $it: FAILED -- $(tail -2 "$OUTDIR/$it.log" | head -1 | cut -c1-80)"
  fi
done
echo "  scored: $ok   no-cell: $miss   failed: $fail"
echo E2E_SESSION_DONE
