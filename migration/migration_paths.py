"""Where the migration is operating — resolved, never hard-coded.

ELEVEN OF THE DRY RUN'S SCRIPTS NAMED `/home/pdeane/code/migration_dryrun`
LITERALLY. That was correct for a sandbox and is the single most dangerous thing
to carry into the real run: on a live tree those paths do not fail loudly, they
succeed against the SANDBOX. A migration that reports every gate green while
editing a copy nobody ships is the worst outcome available, and it looks exactly
like success.

So the root is derived from THIS file's location -- `migration/` sits inside the
tree being migrated -- and every script asks here instead of spelling a path.
Override with $MIGRATION_ROOT only for a deliberate sandbox run, which is
reported on import so it cannot be silent.
"""
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("MIGRATION_ROOT",
                           Path(__file__).resolve().parent.parent)).resolve()
SCORING = ROOT / "scoring"
PSYCHOLOGY = ROOT / "psychology"
MIGRATION = ROOT / "migration"
GOLDENS = MIGRATION / "goldens"

# The engine lives in its own repository; it is NOT under ROOT.
LO_BLOCKS = Path(os.environ.get("LO_BLOCKS", "/home/pdeane/code/update/lo-blocks")).resolve()

_DERIVED = Path(__file__).resolve().parent.parent.resolve()
if ROOT != _DERIVED:
    # Only when it actually differs. `env.sh` exports MIGRATION_ROOT with the
    # derived value, so announcing on mere presence cried wolf every run.
    print(f"  [migration_paths] MIGRATION_ROOT override in effect: {ROOT} "
          f"(derived would be {_DERIVED})", file=sys.stderr)


def require_real_tree():
    """Refuse to run against a sandbox when the caller meant the live tree.

    The dry run's own guard was the mirror image of this one -- it refused to
    touch anything OUTSIDE the sandbox. Both exist for the same reason: the
    expensive mistake is not failing, it is succeeding somewhere else.
    """
    if "migration_dryrun" in str(ROOT):
        raise SystemExit(
            f"REFUSING: migration root is a sandbox ({ROOT}). "
            "Unset $MIGRATION_ROOT to operate on the tree this file lives in.")
    if not (SCORING / "enforcement.py").exists():
        raise SystemExit(f"REFUSING: {SCORING} does not look like a scoring tree.")
    return ROOT
