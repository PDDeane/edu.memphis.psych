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

MATERIALS MOVED INTO DATA on 2026-09-24, superseding the argument that stood
here. That argument was from SENSITIVITY -- the templates are blank, only the
filled-in submissions are sensitive -- and it is still true. It is no longer the
operative one. Goal J makes `scoring/` its own repository, and course teaching
materials may not live in engine territory whether or not they are sensitive: a
second course cannot be served by a repo carrying the first one's handouts. The
findability worry the old text raised -- "a scorer that cannot find its
templates cannot score anything" -- is answered by this constant pointing at
$COURSE_DATA rather than by shipping the files. Two of the eleven were never
templates at all: the PSYC 1030 syllabus and course schedule.

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
# MATERIALS is defined further down, AFTER `DATA` and `NS`, which it is now
# built from. It was here when it was `SCORING / "materials"`.

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


def _lo_server() -> str:
    """The LLM endpoint belonging to THIS checkout's lo-blocks.

    A SECOND MARKER, FOR THE SAME REASON AS `.lo-blocks`. That one stops a copy
    of this repo auditing the original's build artifacts; this one stops a copy
    sending its LLM traffic to the original's SERVER. Both failures look like
    success: the sweep runs, the numbers come out, and nothing says the requests
    were shaped by a tree twelve days older than the one being measured.

    MEASURED, not anticipated. The 2026-09-25 confirmation sweep ran wholly from
    the dry-run tree -- dry-run idmap, dry-run vitest, dry-run scoring code --
    and every LLM call went to `localhost:8888`, the live tree's server, because
    `backends.py` and `runner.test.ts` each spelled that literally. It was found
    by a write-scope check noticing the live server writing rate-limiter state,
    not by anything that watches measurements.

    Precedence matches `_lo_blocks_root` exactly: the environment wins, then the
    marker, then the historical default. A tree without a marker behaves as
    before.
    """
    env = os.environ.get("LO_SERVER")
    if env:
        return env.rstrip("/")
    marker = REPO / ".lo-server"
    if marker.is_file():
        named = marker.read_text().strip()
        if named:
            return named.rstrip("/")
    return "http://localhost:8888"


LO_SERVER = _lo_server()


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

# The content namespace. Was "psych" when this content lived inside lo-blocks;
# the standalone repo declares "edu.memphis.psych" in psychology/manifest.yaml,
# and the runner resolves nothing if these disagree.
def _manifest(key: str, default: str, env: str = "") -> str:
    """One fact the CONTENT COLLECTION declares about itself, or `default`.

    J-7. The same three-step resolution `_namespace` uses -- environment, then
    the manifest beside the content, then a fallback -- generalised, because the
    namespace was not the only fact the engine was holding a second copy of.
    """
    if env:
        override = os.environ.get(env)
        if override:
            return override
    try:
        import yaml
        man = OLX_DIR / "manifest.yaml"
        if man.is_file():
            declared = (yaml.safe_load(man.read_text()) or {}).get(key)
            if declared:
                return str(declared)
    except Exception:
        pass                      # an unreadable manifest is not a reason to die
    return default


def _namespace() -> str:
    """The content namespace, from the COURSE rather than from the engine.

    J-1. This was a literal namespace string, which admitted exactly one course
    by construction -- and the comment above it already said the standalone repo
    declares its namespace in the content collection's `manifest.yaml`, "and the
    runner resolves nothing if these disagree". Two sources of one fact, with the
    engine holding the copy that cannot be right for a second course.

    Order: an explicit `COURSE_NS`, then the manifest beside the content, then the
    stub's namespace. The last is a FALLBACK, not a default to score against --
    a run that reached it has no course, which is what the stub exists to make
    survivable rather than fatal.
    """
    env = os.environ.get("COURSE_NS")
    if env:
        return env
    try:
        import yaml
        man = OLX_DIR / "manifest.yaml"
        if man.is_file():
            declared = (yaml.safe_load(man.read_text()) or {}).get("namespace")
            if declared:
                return str(declared)
    except Exception:
        pass                      # an unreadable manifest is not a reason to die
    return "stub"


NS = _namespace()


def _course_manifest(key: str, default):
    """One fact from the manifest, but ONLY if that manifest is THIS course's.

    J-4d. `_manifest` above reads whatever manifest sits beside `OLX_DIR`, which
    is the ENGINE REPO's content directory -- it does not change when `COURSE_NS`
    does. So a bare manifest key leaks: running as the stub, `OLX_DIR` still
    points at this course's `psychology/`, and the stub would inherit a flag
    declared for a course it is not.

    Matching the manifest's own `namespace` against the active `NS` is what makes
    the key per-course. A course whose manifest is not loaded gets `default`,
    which is the modern layout -- the legacy one is opt-in, so a NEW course
    cannot fall into it by accident. That is the J-4c lesson applied again: an
    undeclared fact must not resolve to another course's answer.
    """
    try:
        import yaml
        man = OLX_DIR / "manifest.yaml"
        if man.is_file():
            doc = yaml.safe_load(man.read_text()) or {}
            if str(doc.get("namespace") or "") == NS and key in doc:
                return doc[key]
    except Exception:
        pass                      # an unreadable manifest is not a reason to die
    return default


# THE PRE-NAMESPACING DATA LAYOUT. Before J-4d, `SUBS` and `OUT` were SHARED
# roots: every course would have read submissions from one directory and written
# results into one `out/`, where the handout number was the only separation, so a
# second course OVERWROTE the first's output instead of sitting beside it.
#
# Declared in the manifest rather than detected, because detection cannot work:
# the legacy directory exists whichever course is loaded, so "use it if present"
# hands a NEW course the old course's data -- the exact bug J-4c closed.
_SHARED_DATA_LAYOUT = bool(_course_manifest("shared_data_layout", False))

OUT = Path(env_renamed("COURSE_OUT",
                       DATA / "out" if _SHARED_DATA_LAYOUT
                       else DATA / "courses" / NS / "out"))

MATERIALS = Path(os.environ.get("COURSE_MATERIALS",
                                DATA / "courses" / NS / "materials"))

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

# WHERE COMPOSED DOCUMENTS ARE BUILT. A composed document is DERIVED -- the generic
# half spliced with this course's cases -- so it is neither authored nor
# accumulated and belongs in neither the content repository nor the run archive.
# It is per-course because its course half is, and it is rebuilt rather than
# edited: editing it edits nothing, since the next build overwrites it.
COMPOSED_DOCS = Path(os.environ.get(
    "COMPOSED_DOCS", DATA / "courses" / NS / "composed"))

# WHERE COURSE METADATA LIVES, and it is NOT the content tree. A third root,
# after one was refused and the refusal reconsidered on evidence.
#
# WHAT THE EVIDENCE WAS. `$COURSE_LOCATION` is inside the tree lo-blocks stages,
# and the engine's `copyTree` stages content by copying EVERYTHING minus a
# hardcoded list of top-level directory names -- `scoring`, `courses`,
# `migration`. That list protects by NAME and by POSITION, not by content, so a
# file is excluded because of where it sits. Moving `course.json` and the
# changelog into `psychology/` therefore put them in the build's copy set: 92 KB
# staged twice on every build, silently, as a side effect of a move that was
# about legibility. The fixture would have taken 1.2 MB of worksheet with it.
#
# NOT A LEAK, and the distinction is worth keeping straight: `.stage/` is
# gitignored with zero tracked files, and the static build emits three parsed
# artifacts and copies nothing raw. The cost is that metadata stops being
# STRUCTURALLY excludable -- the only lever left would be teaching the engine
# another course-specific directory name.
#
# So metadata gets a root of its own, outside the content tree and outside the
# machinery: course.json, the scoring changelog, and the fixture data that
# belongs to the course rather than to either.
COURSE_METADATA = Path(os.environ.get("COURSE_METADATA", REPO / "course_metadata"))

COURSE_FILE = Path(os.environ.get("COURSE_FILE", COURSE_METADATA / "course.json"))

# THE COURSE'S SCORING CHANGELOG, beside the course file for the same reason: it
# is this course's record of incidents, not the engine's. F1 sends an incident
# here, and a gate that strips sentences while their destination is undefined
# produces deletions rather than moves -- so the destination is named in one
# place.
COURSE_CHANGELOG = Path(os.environ.get(
    "COURSE_CHANGELOG", COURSE_METADATA / "CHANGELOG.md"))

# THE FIXTURE'S OWN DATA, under the metadata root. Spans over this corpus, the
# split worksheet, and the two shape exports: course-bearing by construction, and
# none of it content -- so it belongs where the course file does rather than
# beside the .olx, where staging would copy 1.2 MB of it on every build.
COURSE_FIXTURE = Path(os.environ.get(
    "COURSE_FIXTURE", COURSE_METADATA / "fixture"))

# ---------------------------------------------------------------------------
# THE COURSE'S OWN RECORDS. Every key in these is one of this course's items,
# slots or prose spans: the ledger of measured rates, what has been probed and
# what the probe asked, the shas of the designed prompt text, the per-span
# leakage verdicts. They lived in `scoring/` -- the ENGINE's directory -- which
# is precisely what `check_module_has_no_course_data` exists to push out, and
# what goal E did for `scorer_oc` and goal P for `PROBE_PASS`.
#
# ONE SPELLING EACH, which is the other half of the fix. These six files had
# NINE path constructions between them in four different idioms, and
# `enforcement.py` built the ledger's path independently of `measured.LEDGER`
# -- so a move would have left it reading the old location and reporting from a
# stale ledger with no sign anything was wrong.
COURSE_LEDGER = Path(os.environ.get(
    "COURSE_LEDGER", COURSE_METADATA / "MEASURED.json"))
COURSE_CARRIED_NOTES = Path(os.environ.get(
    "COURSE_CARRIED_NOTES", COURSE_METADATA / "CARRIED_NOTES.json"))
COURSE_PROBED = Path(os.environ.get(
    "COURSE_PROBED", COURSE_METADATA / "PROBED.json"))
COURSE_PROBE_RECEIPTS = Path(os.environ.get(
    "COURSE_PROBE_RECEIPTS", COURSE_METADATA / "PROBE_RECEIPTS.json"))
COURSE_DESIGNED_TEXT_SHA = Path(os.environ.get(
    "COURSE_DESIGNED_TEXT_SHA", COURSE_METADATA / "DESIGNED_TEXT_SHA.json"))
COURSE_LEAKAGE_REVIEWED = Path(os.environ.get(
    "COURSE_LEAKAGE_REVIEWED", COURSE_METADATA / "LEAKAGE_REVIEWED.json"))

# THE FIXTURE'S DATA, WHICH IS NOT ITS CODE. Goal N.
#
# `CONSENSUS_SPANS.json` is keyed `item/participant` -- a record ABOUT individual
# students, even where it holds offsets rather than their sentences. It was in
# the repository; student-derived material belongs in $COURSE_DATA beside the
# submissions and `corpus_refs.json`, which is where everything else of its kind
# already lives. The fixture CODE stays in the repo: it names this course's
# subject but says nothing about any student.
COURSE_FIXTURE_DATA = Path(os.environ.get(
    "COURSE_FIXTURE_DATA", DATA / "courses" / NS / "fixture"))

# AND IT IS IMPORTABLE. The fixture modules are course data -- they map THIS
# course's paper forms to its web forms -- but they are also imported by name
# from the machinery (`segment` by four modules). Putting the directory on the
# path here, in the module every other one already imports for its locations,
# keeps `import segment` working unchanged rather than rewriting each call site
# to know where the course keeps its fixture.
if str(COURSE_FIXTURE) not in sys.path:
    sys.path.insert(0, str(COURSE_FIXTURE))

# ── Derived paths ────────────────────────────────────────────────────────────

# Generated content (Class B: intra-repo since the move).
# One handout's CONTENT FILE, as the content collection names it. J-7b.
# 44 sites spelled `f"bmod_handout{h}.olx"` or globbed `bmod_handout*.olx`
# themselves, which put one course's file stems in engine code -- the same
# problem J-7a fixed for the rubric component, at fourteen times the scale.
# The pattern is a `%d` template so the glob can be derived from it rather than
# written twice and drifting.
HANDOUT_OLX = _manifest("handout_olx", "bmod_handout%d.olx", "COURSE_HANDOUT_OLX")

OLX = str(OLX_DIR / HANDOUT_OLX)


def handout_olx(handout) -> str:
    """This course's content FILE NAME for one handout, e.g. for `load_action`."""
    return HANDOUT_OLX % int(handout)


def handout_olx_glob() -> str:
    """A glob matching every handout's content file.

    DERIVED from the pattern, not written beside it: the two were the same fact
    and a course changing one would have left the other matching nothing.
    """
    return HANDOUT_OLX.replace("%d", "*")


def handout_olx_path(handout):
    """The full path to one handout's content file."""
    return OLX_DIR / handout_olx(handout)

# The RUBRIC COMPONENT's file name, as the content collection declares it. J-7.
# `rubric_component.py` built this from the literal "bmod_rubric.olx", which is
# one course's stem in engine code and is what stopped the stub course from
# importing: it ships `stub_rubric.olx` and nothing could name it. The default
# keeps every existing tree reading the file it already reads.
#
# The HANDOUT stems above are the same problem and are NOT fixed here -- they
# reach 67 sites across 16 modules, which is J-7's remainder.
RUBRIC_COMPONENT = _manifest("rubric_component", "bmod_rubric.olx",
                             "COURSE_RUBRIC_COMPONENT")

# The engine contract (Class C: still cross-repo).
PRIMITIVES_JSON = LO / "packages/shared/lib/llm/primitives.json"
SLOTSHEET_TS = LO / "packages/shared/lib/llm/slotSheet.ts"
RUNNER = "packages/shared/lib/llm/runner.test.ts"
PROBE = "packages/shared/lib/llm/probe.test.ts"

# The corpus (local only).
SUBS = Path(os.environ.get(
    "COURSE_SUBS",
    DATA / "Handout Submissions with Scoring and Feedback" if _SHARED_DATA_LAYOUT
    else DATA / "courses" / NS / "submissions"))
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
