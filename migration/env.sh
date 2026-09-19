# Source this for EVERY migration command.
#
# THE DRY RUN'S env.sh POINTED EVERYTHING AT A SANDBOX. This one points at the
# tree it lives in, resolved rather than spelled: eleven dry-run scripts named
# `/home/pdeane/code/migration_dryrun` literally, and on a live tree such a path
# does not fail -- it succeeds against the sandbox, with every gate green and
# nothing migrated. `migration_paths.py` refuses that case; this file is its
# shell equivalent.
export MIGRATION_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export LO_BLOCKS="${LO_BLOCKS:-/home/pdeane/code/update/lo-blocks}"
export COURSE_DATA="${COURSE_DATA:-/home/pdeane/molly_data}"
export COURSE_OUT="${COURSE_OUT:-$COURSE_DATA/out}"
export CORPUS_REFS="${CORPUS_REFS:-$COURSE_DATA/corpus_refs.json}"
export PYTHONPATH="$MIGRATION_ROOT/scoring:$MIGRATION_ROOT/migration"
export MIGRATION_ENV="$MIGRATION_ROOT/migration/env.sh"

case "$MIGRATION_ROOT" in
  *migration_dryrun*)
    echo "REFUSING: env.sh resolved to a sandbox ($MIGRATION_ROOT)." >&2
    return 1 2>/dev/null || exit 1 ;;
esac
