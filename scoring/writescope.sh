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
  # 2026-09-19: $COURSE_DATA opened for SECONDARY records -- bookkeeping this
  # project writes and rewrites -- but NOT for source documents and records.
  # The distinction is the point: `out/` is where runs record themselves, and
  # `courses/<id>/gold.json` is a file C1b creates. Neither is a source.
  /home/pdeane/molly_data/out
  /home/pdeane/molly_data/courses
)

# SOURCE DOCUMENTS AND RECORDS. Refused even inside an allowed tree, because
# these are the primary data and the archives of it -- the submissions and the
# graders' workbooks are the thing every measurement is ABOUT, and the migration
# and scrub archives exist precisely so that a past state cannot be lost.
FORBIDDEN=(
  "/home/pdeane/molly_data/Handout Submissions with Scoring and Feedback"
  /home/pdeane/molly_data/migration_reference
  /home/pdeane/molly_data/migration_goldens
  /home/pdeane/molly_data/retired_artifacts
  /home/pdeane/molly_data/handsplit
  /home/pdeane/molly_data/pre_scrub_backup_20260917_084827
  /home/pdeane/molly_data/corpus_refs.json
  # 2026-09-23: the EVENT PIPELINE. Excluded by the user from reading, writing AND
  # deleting for the rest of this session -- it stays in `scripts/` and this work
  # does not touch it. Listed here rather than left to the ALLOWED list's silence:
  # it is already outside that list, but an omission stops protecting the moment
  # the list widens, and a named refusal does not. This guard can only enforce the
  # WRITE half; the read exclusion is a standing instruction, recorded here because
  # this file is where the session's boundaries are written down.
  /home/pdeane/code/scripts
)
rc=0
for raw in "$@"; do
  p=$(readlink -m -- "$raw")
  ok=0; why=""
  for a in "${ALLOWED[@]}"; do
    case "$p" in "$a"|"$a"/*) ok=1 ;; esac
  done
  for f in "${FORBIDDEN[@]}"; do
    case "$p" in "$f"|"$f"/*) ok=0; why="a SOURCE document or record" ;; esac
  done
  if [ "$ok" = 1 ]; then
    echo "  IN SCOPE   $p"
  else
    echo "  REFUSED    $p"
    echo "             ${why:-outside the dry run}. Allowed tonight:"
    printf '               %s\n' "${ALLOWED[@]}"
    rc=1
  fi
done
exit $rc
