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
    MOLLY_DATA=~/molly_data
    MOLLY_OUT=$MOLLY_DATA/out
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

LO = Path(os.environ.get("LO_BLOCKS", Path.home() / "code/update/lo-blocks"))
DATA = Path(os.environ.get("MOLLY_DATA", Path.home() / "molly_data"))
OUT = Path(os.environ.get("MOLLY_OUT", DATA / "out"))

# The content namespace. Was "psych" when this content lived inside lo-blocks;
# the standalone repo declares "edu.memphis.psych" in psychology/manifest.yaml,
# and the runner resolves nothing if these disagree.
NS = "edu.memphis.psych"

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
MEDIA = Path(os.environ.get("MOLLY_MEDIA",
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
    return require(OUT, "Artifact directory", "MOLLY_OUT")


def out_root_or_reason() -> tuple[Path | None, str]:
    """For CHECKS, which must not exit the process.

    `require` calls `sys.exit`, which is right for a script and wrong for one
    check inside an audit of a hundred. This returns the reason instead, so the
    caller can report "the check could not run" -- which is not the same as
    passing, and must never be rendered as one.
    """
    return (OUT, "") if OUT.exists() else (
        None, f"Artifact directory not found: {OUT}. Set MOLLY_OUT to point at it.")


def data_root() -> Path:
    return require(DATA, "Student corpus", "MOLLY_DATA")


def lo_root() -> Path:
    return require(LO, "lo-blocks checkout", "LO_BLOCKS")
