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
  # 2026-09-26: `courses/` NO LONGER EXISTS. The store is split by OWNER --
  # `instruments/<id>/` for what the handout owns, `rubrics/<id>/` for what a
  # scoring specification owns -- so the allowance follows the data rather than
  # naming a directory that was emptied. `out/` is listed for the same reason it
  # always was, and is now inside `rubrics/<id>/`.
  /home/pdeane/molly_data/instruments
  /home/pdeane/molly_data/rubrics
)

# SOURCE DOCUMENTS AND RECORDS. Refused even inside an allowed tree, because
# these are the primary data and the archives of it -- the submissions and the
# graders' workbooks are the thing every measurement is ABOUT, and the migration
# and scrub archives exist precisely so that a past state cannot be lost.
FORBIDDEN=(
  # 2026-09-26: POSITIONAL, NOT ENUMERATED. This list named `submissions` and
  # `handsplit` by path, and had to be rewritten TWICE in one day to chase them
  # as they moved -- a guard that loses its subject in a move is worse than
  # none, because it still reports IN SCOPE. The store now says which material
  # is irreplaceable IN THE DIRECTORY NAME, so the rule can be about position:
  # nothing under a `source/` is writable, whatever it holds and wherever its
  # owner moves next. `_SOURCE_RE` below is that rule.
  /home/pdeane/molly_data/migration_reference
  /home/pdeane/molly_data/migration_goldens
  /home/pdeane/molly_data/retired_artifacts
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
  # THE POSITIONAL RULE. Any `source/` under the data store holds material that
  # cannot be regenerated -- the submissions, the graders' workbooks, the
  # hand-read splits, the hand-adjudicated consensus. It needs no list and
  # survives a move.
  case "$p" in
    /home/pdeane/molly_data/*/*/source|/home/pdeane/molly_data/*/*/source/*)
      ok=0; why="under a source/ -- irreplaceable primary material" ;;
    # THE SAME RULE, WHEREVER THE DATA STORE IS. On 2026-09-26 the dry run was
    # given its own $COURSE_DATA inside the working tree, so that it could not
    # clash with the live one -- and the copy brought a `source/` with it.
    # Every path in this tree is writable by the rule above, so the copy's
    # submissions and materials arrived UNPROTECTED: the guard was keyed to
    # where the store happened to be rather than to what the directory is.
    # A copy of irreplaceable material is not less irreplaceable for having
    # been copied -- it is the thing the dry run actually reads.
    */course_data/*/*/source|*/course_data/*/*/source/*|*/course_data/*/*/source/*/*)
      ok=0; why="under a source/ in the dry run's own data store -- the same irreplaceable primary material" ;;
  esac
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
