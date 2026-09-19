#!/usr/bin/env bash
# Refuse a write outside tonight's allowed scope.
#
# WHY THIS EXISTS. On 2026-09-18 the user restricted writing to the dry-run
# directories for the night. Two things had already happened by then: a commit to
# the LIVE tree was in flight (stopped before it landed, but `git add -A` had
# already staged a file there), and a one-line edit to live's equivalence.py had
# been made. An hourly reminder was set at the same time as this guard, because a
# rule that depends on remembering is a rule that lapses at 3am.
#
# Usage:  bash writescope.sh <path> [<path>...]   -> exit 0 if ALL are in scope
set -u
ALLOWED=(
  /home/pdeane/code/update/refactor_dry_run/edu.memphis.psych
  /home/pdeane/code/update/refactor_dry_run/lo-blocks
)
rc=0
for raw in "$@"; do
  p=$(readlink -m -- "$raw")
  ok=0
  for a in "${ALLOWED[@]}"; do
    case "$p" in "$a"|"$a"/*) ok=1 ;; esac
  done
  if [ "$ok" = 1 ]; then
    echo "  IN SCOPE   $p"
  else
    echo "  REFUSED    $p"
    echo "             outside the dry run. Allowed tonight:"
    printf '               %s\n' "${ALLOWED[@]}"
    rc=1
  fi
done
exit $rc
