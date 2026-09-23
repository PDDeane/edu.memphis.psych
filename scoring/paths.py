"""Where everything lives, in one place.

This project used to sit in ~/code/molly_scoring next to a checkout of
lo-blocks, and seventeen absolute paths said so. It now ships inside the
content repo it generates for, which splits those paths three ways:

  REPO / OLX_DIR   the content this project GENERATES — same repo, so a
                   relative path, and `olx_prompts.py --write` writes next
                   door rather than across the filesystem.

  LO               the lo-blocks ENGINE — still a separate repo. Only the
                   slot-sheet contract crosses this line: primitives.json,
                   slotSheet.ts, and the two vitest harnesses that
                   agreement_app.py and equivalence.py drive as subprocesses.

  DATA / OUT       the student corpus and run artifacts. NEVER in git. The
                   submissions carry real names in their OOXML metadata
                   (dc:creator), the gold sheets are the key that makes the
                   participant IDs meaningful, and out/ quotes student text
                   verbatim as scoring evidence. This repo is public.

MATERIALS is deliberately NOT part of DATA: the blank handout templates are
course teaching materials and ship with the code, because `segment.py`
subtracts the template from a submission to isolate student text, and a
scorer that cannot find its templates cannot score anything. Only the filled-in
submissions are sensitive.

Override any root with an env var; the defaults assume the usual checkout
layout:

    LO_BLOCKS=~/code/update/lo-blocks
    COURSE_DATA=~/molly_data
    COURSE_OUT=$COURSE_DATA/out
"""
from __future__ import annotations

import os
import tempfile
import sys
from pathlib import Path

# ── The three roots ──────────────────────────────────────────────────────────

REPO = Path(__file__).resolve().parent.parent
SCORING = REPO / "scoring"

OLX_DIR = REPO / "psychology"
MATERIALS = SCORING / "materials"

def _lo_blocks_root() -> Path:
    """Where THIS checkout's lo-blocks is.

    `LO` was one absolute path, so a COPY of this repo audited the ORIGINAL's
    build artifacts -- the dry run read live lo-blocks, and on 2026-09-20 a
    rebuild from live content made an artifact check go green about a tree it
    had never seen. A checkout that ships its own lo-blocks should audit it.

    A MARKER FILE, NOT A SIBLING GUESS. Deriving `REPO.parent/"lo-blocks"` looks
    tidier and is wrong: `~/code/lo-blocks` exists, so live would silently stop
    resolving `~/code/update/lo-blocks` and start reading something else.
    Checked before writing this, which is the only reason it is not the shipped
    version. The marker is opt-in: a tree without one behaves exactly as before.

    Precedence: the environment wins (a one-off run, and what the build scripts
    already set), then the marker, then the historical default.
    """
    env = os.environ.get("LO_BLOCKS")
    if env:
        return Path(env)
    marker = REPO / ".lo-blocks"
    if marker.is_file():
        named = marker.read_text().strip()
        if named:
            return Path(named).expanduser()
    return Path.home() / "code/update/lo-blocks"


LO = _lo_blocks_root()


# ---------------------------------------------------------------------------
# STAGE 9. `MOLLY_*` -> `COURSE_*`. THE FALLBACK IS THE DELIVERABLE, not a
# transition courtesy, because these variables live where a repo-wide rename
# cannot reach: shells, runbooks, cron entries, and the command lines of
# background jobs already running. Renaming every reference in this repository
# changes not one of those.
#
# THE WARNING FIRES ONCE PER PROCESS, not per read. `paths.DATA` is read
# constantly, and a per-read warning produces thousands of lines that get
# filtered -- which is the same as no warning, arrived at more expensively.
#
# EXPIRY IS A CRITERION, NOT A DATE. "Honoured for a declared period" expires the
# way §10.1.2's and D2d's sentences would have: not at all. The fallback goes when
# the warning HAS NOT FIRED in normal use across a stated stretch of work --
# evidence that nothing still sets the old name -- and not on a date that passes
# unnoticed.
# ---------------------------------------------------------------------------
# The OLD names, which the sed pass must not rewrite -- this table is the only
# place in the repo that still has to know them, because it is what honours them.
_RENAMED = {"COURSE_DATA": "MOLLY_DATA",
            "COURSE_OUT": "MOLLY_OUT",
            "COURSE_MEDIA": "MOLLY_MEDIA"}
_WARNED: set = set()


def env_renamed(new: str, default=None):
    """Read `new`, falling back to the old name once and saying so once."""
    value = os.environ.get(new)
    if value:
        return value
    old = _RENAMED[new]
    value = os.environ.get(old)
    if value:
        if old not in _WARNED:
            _WARNED.add(old)
            print(f"paths: ${old} is set and ${new} is not. The old name is "
                  f"honoured and will stop being honoured once nothing sets it. "
                  f"Set ${new} instead.", file=sys.stderr)
        return value
    return default


# The trees that count as CORPUS evidence, resolved here because this module is
# where filesystem locations are resolved -- `check_filesystem_locations_come_
# from_paths_py` caught them spelled into `olx_corpus.py`, and it was right to:
# a literal path does not fail on the wrong tree, it SUCCEEDS on it.
#
# Which trees are distinct evidence is a judgement (see `olx_corpus`): three
# attempts at discovering it automatically each counted copies as courses. So the
# list is declared -- and resolved, and overridable by $COURSE_ROOTS.
CODE = Path(os.environ.get("CODE_HOME", Path.home() / "code"))
CORPUS_ROOTS = {
    "engine": lambda: LO,
    "writing": lambda: CODE / "update" / "edu.memphis.writing",
    "reading": lambda: CODE / "update" / "edu.mtsu.transitional-reading",
    "interdisciplinary": lambda: CODE / "interdisciplinary",
}

DATA = Path(env_renamed("COURSE_DATA", Path.home() / "molly_data"))
OUT = Path(env_renamed("COURSE_OUT", DATA / "out"))

# The content namespace. Was "psych" when this content lived inside lo-blocks;
# the standalone repo declares "edu.memphis.psych" in psychology/manifest.yaml,
# and the runner resolves nothing if these disagree.
NS = "edu.memphis.psych"

# THE COURSE LOCATION: where THIS course's own material lives, inside the content
# tree. Declared 2026-09-23.
#
# `psychology/` is a COLLECTION, not a course -- it holds this handout course (six
# `bmod_*.olx`) alongside the psychology SBA work and the assets both use, 42
# entries in all. A course needs a folder of its own before anything can be said to
# belong to it, and the course-specific half of every split document belongs here:
# in the repository, TRACKED, because `edu.memphis.psych` IS the psychology course
# repository and course material belongs in it.
#
# THE LINE THIS DRAWS, and it is the one worth remembering: CONTENT in the content
# repository, DATA outside it. The test is whether a file is AUTHORED or
# ACCUMULATED -- `course.json` and a course-specific document half are authored and
# live here; `gold.json`, the override log and 826 run artifacts are accumulated and
# live under `$COURSE_DATA`.
#
# Overridable so a second course is a variable and not an edit, and resolved here
# rather than at each call site, for the reason
# `check_filesystem_locations_come_from_paths_py` exists: "a literal path does not
# fail on the wrong tree, it SUCCEEDS on it".
COURSE_LOCATION = Path(os.environ.get("COURSE_LOCATION",
                                      REPO / "psychology" / "bmod"))

# ── Derived paths ────────────────────────────────────────────────────────────

# Generated content (Class B: intra-repo since the move).
OLX = str(OLX_DIR / "bmod_handout%d.olx")

# The engine contract (Class C: still cross-repo).
PRIMITIVES_JSON = LO / "packages/shared/lib/llm/primitives.json"
SLOTSHEET_TS = LO / "packages/shared/lib/llm/slotSheet.ts"
RUNNER = "packages/shared/lib/llm/runner.test.ts"
PROBE = "packages/shared/lib/llm/probe.test.ts"

# The corpus (local only).
SUBS = DATA / "Handout Submissions with Scoring and Feedback"
HANDSPLIT = DATA / "handsplit"


# ── Fail fast, and say which env var fixes it ────────────────────────────────

def require(path: Path, what: str, env: str) -> Path:
    """Check a root exists, naming the override that fixes it.

    A missing corpus must stop the run. `baseline.py` prints a plausible table
    off a partial sample — the README already warns about that for dropped
    calls — and a silently empty submissions directory is the same failure with
    no calls at all.
    """
    if not path.exists():
        sys.exit(
            f"{what} not found: {path}\n"
            f"Set {env} to point at it. See scoring/paths.py."
        )
    return path


# Scratch space for generated media. NOT a literal: `/tmp/claude-1000/...`
# bakes in a numeric UID, so it is correct for one account on one machine and
# silently wrong (or unwritable) for every other.
MEDIA = Path(os.environ.get("COURSE_MEDIA",
                            Path(tempfile.gettempdir()) / f"molly_scoring_media_{os.getuid()}"))


def media_dir() -> Path:
    """The media scratch directory, created on demand."""
    MEDIA.mkdir(parents=True, exist_ok=True)
    return MEDIA


def out_root() -> Path:
    """The artifact directory, or a refusal naming the variable that fixes it.

    NEVER FALL BACK TO A LITERAL HERE. Seven call sites used to write
    `getattr(paths, "OUT", "/home/<user>/molly_data/out")`, which fires exactly
    when the configuration is missing and then reads the DEVELOPER's own
    artifacts -- a harness pointed at a sandbox, a second checkout or a backup
    silently measures the wrong directory and passes. Worse inside a CHECK: a
    directory that does not exist yields no files, the check finds nothing, and
    reporting nothing reads as reporting clean.
    """
    return require(OUT, "Artifact directory", "COURSE_OUT")


def out_root_or_reason() -> tuple[Path | None, str]:
    """For CHECKS, which must not exit the process.

    `require` calls `sys.exit`, which is right for a script and wrong for one
    check inside an audit of a hundred. This returns the reason instead, so the
    caller can report "the check could not run" -- which is not the same as
    passing, and must never be rendered as one.
    """
    return (OUT, "") if OUT.exists() else (
        None, f"Artifact directory not found: {OUT}. Set COURSE_OUT to point at it.")


def data_root() -> Path:
    return require(DATA, "Student corpus", "COURSE_DATA")


def lo_root() -> Path:
    return require(LO, "lo-blocks checkout", "LO_BLOCKS")
