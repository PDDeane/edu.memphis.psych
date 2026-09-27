# Source this for EVERY migration command.
#
# THE DRY RUN'S env.sh POINTED EVERYTHING AT A SANDBOX. This one points at the
# tree it lives in, resolved rather than spelled: eleven dry-run scripts named
# `/home/pdeane/code/migration_dryrun` literally, and on a live tree such a path
# does not fail -- it succeeds against the sandbox, with every gate green and
# nothing migrated. `migration_paths.py` refuses that case; this file is its
# shell equivalent.
export MIGRATION_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# RESOLVED, NOT SPELLED -- for the reason stated four lines above about
# MIGRATION_ROOT. This line named `/home/pdeane/code/update/lo-blocks` outright,
# so sourcing this file in the DRY RUN tree pointed every migration command at
# the LIVE checkout: `MIGRATION_ROOT` was carefully derived from the file's own
# location and then the very next line reached into the other tree. That is the
# shape of the 2026-09-25 incident in which both sweeps ran against the live
# server and wrote 1,866 files into it.
#
# A sibling of MIGRATION_ROOT if there is one, and only then the checkout beside
# it -- so the dry run gets the dry run's lo-blocks and the live tree gets its own.
if [ -z "${LO_BLOCKS:-}" ]; then
  if [ -d "$MIGRATION_ROOT/../lo-blocks" ]; then
    LO_BLOCKS="$(cd "$MIGRATION_ROOT/../lo-blocks" && pwd)"
  else
    LO_BLOCKS="/home/pdeane/code/update/lo-blocks"
  fi
fi
export LO_BLOCKS
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
