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

import dataclasses
import functools
import os
import tempfile
import sys
from pathlib import Path

# ── The three roots ──────────────────────────────────────────────────────────

REPO = Path(__file__).resolve().parent.parent
SCORING = REPO / "scoring"

def _rubric_file(repo=None, ns: str | None = None):
    """This course's rubric component, found WITHOUT naming a directory.

    THE BOOTSTRAP, and it has to exist. Every other root is read from the
    rubric's own frontmatter, so something must locate the rubric before any
    declaration can be honoured -- and whatever does that cannot itself ask a
    declaration. What it CAN do is refuse to spell a course's directory name.

    `REPO/*/*_rubric.olx`: one level down, by SHAPE. The literal it replaces
    spelled THIS course's content-collection directory, sitting inside machinery
    whose whole purpose is to know no course -- the same sentence
    `_rubric_declares` was written to stop being true of a hardcoded data root.
    The user's instruction, 2026-09-25: *"We need to standardize on the engines
    not assuming the name of the directory that content lives in"*, and that it
    applies to the collection and the course folder alike.

    IT WAS FIRST-MATCH UNTIL 2026-09-25, and subgoal E58 recorded that as "the
    same defect this entry is about, one level down": a repository holding two
    courses' rubrics silently got whichever sorted first. The user's ruling was
    to be rid of it.

    SO THE NAMESPACE DECIDES, and only when it has to. One candidate needs no
    disambiguation and is returned. With several, each candidate's COLLECTION
    declares its own namespace in the `manifest.yaml` beside it -- the same
    declaration `_namespace` already reads -- and the one matching `ns` is the
    answer. That is not a new mechanism: it is the selector doing the job a
    selector is for.

    AND IF IT STILL CANNOT TELL, IT REFUSES, naming the candidates. Returning
    one of them would be first-match wearing a different hat, and a run that
    scores the wrong course's rubric does not fail -- it succeeds, on the wrong
    course.
    """
    # AN EXPLICIT RUBRIC WINS, and nothing below runs. `$COURSE_RUBRIC_OLX`
    # names one file outright, which is a stronger statement than any search
    # can make: it is how the stub course is reached, its rubric living beside
    # its own `course.json` rather than in a content collection. The variable
    # already steered `rubric_component.expanded_path`, so the READER honoured
    # it while the BOOTSTRAP did not -- the stub was scored through a rubric
    # whose folder the rest of the layout could not name, and every root that
    # derives from `_course_location` silently described the wrong course.
    #
    # THIS IS NOT THE ENV-VARIABLE HABIT `_course_location` RETIRED. That rule
    # is about variables naming a DIRECTORY when several courses are mounted;
    # this one names a FILE, and a course supplied as one file has no ambiguity
    # to resolve.
    explicit = os.environ.get("COURSE_RUBRIC_OLX")
    if explicit:
        p = Path(explicit)
        if p.is_file():
            return p

    # AT ANY DEPTH. This globbed `*/*_rubric.olx` -- one level down -- and when
    # an authored course was given a folder of its own inside its collection on
    # 2026-09-26 the bootstrap stopped finding the rubric at all. The first fix
    # was to search two depths, and the user's ruling was that this is the same
    # mistake with a bigger number in it: *"You should not assume a specific
    # depth that a course's files will be embedded in the repo!"* A repository
    # may nest its content however it likes, so the search is over the whole
    # tree and the SHAPE of the filename is the entire rule.
    #
    # WHAT IS PRUNED, and why each is not a layout decision. Version control,
    # dependency and bytecode directories hold no authored content; a build
    # STAGE holds copies of content that is already found at its source, and
    # returning the copy would make every root resolve inside the build output.
    # Pruning those is not an assumption about where a course lives -- it is a
    # statement about directories that are not course material anywhere.
    #
    # A VANISHING DIRECTORY IS NOT AN ERROR. A walk over a whole repository runs
    # while other work writes to it, and a scratch directory that disappears
    # mid-walk once cost five wrong diagnoses elsewhere in this project. The
    # walk tolerates it rather than failing the bootstrap that everything else
    # is waiting on.
    #
    # THE AMBIGUITY RULE IS UNCHANGED and now does more work: a deeper search
    # can see more candidates, so two rubrics means the namespace decides and an
    # undecidable pair refuses, exactly as below.
    root = Path(repo or REPO)
    _PRUNE = {".git", ".hg", ".svn", "node_modules", "__pycache__",
              ".stage", ".venv", "venv", ".tox", ".mypy_cache", ".pytest_cache"}
    cand = []
    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None):
        dirnames[:] = [d for d in dirnames if d not in _PRUNE]
        for fn in filenames:
            if fn.endswith("_rubric.olx"):
                cand.append(Path(dirpath) / fn)
    cand = sorted(set(cand))
    if not cand:
        return None
    if len(cand) == 1:
        return cand[0]
    # NOT `ns or NS`. `NS` is bound 400 lines below and this runs DURING module
    # initialisation -- `_course_location` asks for the rubric before any
    # constant exists -- so naming it here is the NameError this file already
    # records being bitten by once, waiting for the day a repository holds two
    # rubrics. The selector is readable at any time; the constant is not.
    want = ns or os.environ.get("COURSE_NS") or globals().get("NS")
    matched = [c for c in cand if _collection_namespace(c.parent) == want]
    if len(matched) == 1:
        return matched[0]
    raise SystemExit(
        f"{Path(repo or REPO)} holds {len(cand)} rubrics "
        f"({', '.join(str(c.relative_to(Path(repo or REPO))) for c in cand)}) "
        f"and {'none' if not matched else len(matched)} of them "
        f"{'declares' if not matched else 'declare'} the namespace {want!r}. "
        f"Refusing to pick one: scoring the wrong course's rubric does not "
        f"fail, it succeeds on the wrong course. Give each collection a "
        f"`manifest.yaml` naming its namespace, or select the course you mean "
        f"with $COURSE_NS.")


def _collection_namespace(collection) -> str | None:
    """The namespace a CONTENT COLLECTION declares about itself, or None.

    The same `manifest.yaml` key `_namespace` reads for the active course, asked
    of a particular directory so that `_rubric_file` can tell two courses'
    collections apart inside one repository.
    """
    # SEARCHED UPWARD, not read from one fixed directory. The caller passes the
    # rubric's own folder, which IS the collection in the flat layout and is the
    # COURSE folder when a course has its own -- so a fixed lookup answered None
    # for every course of the second kind, and None never matches a namespace,
    # so two courses in one repository became undecidable rather than being
    # told apart. Walking up stops at the first manifest, which is the nearest
    # collection that claims the rubric.
    try:
        import yaml
        here = Path(collection)
        for d in (here, *here.parents):
            man = d / "manifest.yaml"
            if man.is_file():
                declared = (yaml.safe_load(man.read_text()) or {}).get("namespace")
                return str(declared) if declared else None
    except Exception:
        return None
    return None


# MATERIALS is defined further down, AFTER `DATA` and `NS`, which it is now
# built from. It was here when it was `SCORING / "materials"`.

def _course_location(repo=None) -> Path:
    """This course's own folder inside the content collection.

    DECLARED, NOT SPELLED, since 2026-09-25 on the user's instruction. It was
    `REPO / <collection> / <course>` with both names written out -- two of this
    course's directory names in the engine at once. The rubric declares
    `course_location:` now and this reads it.

    NO ENVIRONMENT VARIABLE. `$COURSE_LOCATION` used to override it, and the
    same instruction retires that habit: *"we really don't trust env variables
    for course information as there may be many courses so we really ought to be
    retiring them for that purpose."* A variable naming one folder cannot be
    right for several courses, and unlike `$COURSE_DATA` this one had no
    existing caller to keep working -- nothing in the repository set it. So it
    is gone rather than deprecated.

    THE FALLBACK IS THE COLLECTION ITSELF, which is the honest answer for a
    course that declares nothing: its material is wherever its rubric is. That
    is a real layout, not a guess about this one.
    """
    declared = _rubric_declares("course_location", repo)
    if declared is not None:
        return Path(declared)
    rubric = _rubric_file(repo)
    return rubric.parent if rubric is not None else Path(repo or REPO)


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
# PREDECESSORS, NEWEST FIRST -- a CHAIN, not a pair.
#
# It was one old name per new one, which was enough for a single rename. There
# have been two: Stage 9 moved `MOLLY_* -> COURSE_*`, and 2026-09-26 moved the
# course-information roots to `RUBRIC_*` after the user's observation that *"it's
# not really the COURSE that's the individuator. It's the rubric. Nothing would
# prevent us from writing multiple rubrics for one course."* A shell that still
# exports `MOLLY_DATA` must keep working across BOTH, and a single-step fallback
# silently stops honouring the oldest name at the second rename -- which fails
# the way this whole mechanism exists to prevent, as an empty result.
_RENAMED = {"RUBRIC_DATA": ("COURSE_DATA", "MOLLY_DATA"),
            "RUBRIC_METADATA": ("COURSE_METADATA",),
            "COURSE_DATA": ("MOLLY_DATA",),
            "COURSE_OUT": ("MOLLY_OUT",),
            "COURSE_MEDIA": ("MOLLY_MEDIA",)}
_WARNED: set = set()


def env_renamed(new: str, default=None):
    """Read `new`, falling back through its predecessors, saying so once each."""
    value = os.environ.get(new)
    if value:
        return value
    for old in _RENAMED[new]:
        value = os.environ.get(old)
        if not value:
            continue
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

# THE DECLARATION KEYS AND THEIR PREDECESSORS, newest first -- the frontmatter
# half of `_RENAMED`, and renamed on the same day for the same reason. These are
# read from ONE rubric's frontmatter, so `rubric_` is what they have always
# meant: the reader has exactly one rubric in hand when it asks.
#
# `rubric_location` POINTS AT A COURSE'S FOLDER, and two rubrics scoring the
# same course would declare the same one. That is not the collision `rubric_data`
# avoids, because the location is READ-ONLY CONTENT: nothing per-rubric is
# written there. The hazard belongs to roots that are WRITTEN, which is why the
# distinction is recorded here rather than left to be re-derived.
_DECLARED_AS = {"rubric_data": ("rubric_data", "course_data"),
                "rubric_metadata": ("rubric_metadata", "course_metadata"),
                "rubric_location": ("rubric_location", "course_location")}


def _rubric_declares(key: str, repo=None):
    """One root the COURSE declares about itself, or None.

    THE COURSE SAYS WHERE ITS OWN DATA LIVES. `paths.py` spelled
    `~/molly_data` as the default for `COURSE_DATA` -- this course's name,
    inside machinery whose whole purpose is to know no course. The rubric
    declares it in its frontmatter now, beside the `corpus_data:` line that
    already names a file within it.

    PRECEDENCE IS env -> THIS -> the historical fallback, matching
    `_lo_blocks_root`. The environment still wins, so every script and one-off
    run behaves exactly as before; what moves is where the DEFAULT comes from.
    That ordering is also what makes the change safe to land: nothing that
    resolves today can resolve differently tomorrow.

    NEVER RAISES, and that is not laziness. `paths` is imported before anything
    else in the package; a module that dies while deciding where files are
    leaves no way to report why. An unreadable or absent declaration returns
    None and the caller keeps its historical default.
    """
    import re as _re

    # FOUND BY SHAPE, NOT BY NAME, and the ordering is the reason. The obvious
    # spelling is `REPO / "psychology" / RUBRIC_COMPONENT` -- and
    # `RUBRIC_COMPONENT` is defined 270 lines BELOW the first caller, so it
    # raised NameError, the `except` swallowed it, and this returned None. The
    # declaration was never read and every root silently kept its old default.
    # It looked like it worked because the declared value and the historical
    # fallback were the same path; a control that changed the declaration to a
    # distinct one is what exposed it.
    #
    # `*_rubric.olx` needs only REPO, and it names no course. Since 2026-09-25
    # it does not name the COLLECTION either -- see `_rubric_file`.
    cand = _rubric_file(repo)
    if cand is None:
        return None
    try:
        head = cand.read_text(errors="ignore")[:4000]
    except OSError:
        return None
    # NOT a blanket `except`. An unreadable file is a legitimate absence; a
    # NameError or a bad pattern is a coding fault, and swallowing it here is
    # what hid this bug in the first place.
    block = _re.search(r"^---\s*$\n(.*?)^---\s*$", head, _re.S | _re.M)
    if not block:
        return None
    # THE KEY, THEN ITS PREDECESSOR. `course_data:` / `course_metadata:` /
    # `course_location:` became `rubric_*` on 2026-09-26, because the rubric is
    # what individuates a scoring space -- the user's own framing: *"Nothing
    # would prevent us from writing multiple rubrics for one course."* A rubric
    # written before that still says `course_*`, and refusing to read it would
    # send every root back to its historical fallback SILENTLY, which is the
    # failure this function's docstring already warns about.
    m = None
    for k in _DECLARED_AS.get(key, (key,)):
        m = _re.search(rf"^{_re.escape(k)}:\s*(\S+)\s*$", block.group(1), _re.M)
        if m:
            break
    if not m:
        return None
    raw = m.group(1)
    # `~` is the home directory; `./` is the REPOSITORY, never the working
    # directory -- a declaration that moved with `cd` would be worse than none.
    if raw.startswith("~"):
        return Path(raw).expanduser()
    if raw.startswith("./"):
        return (Path(repo or REPO) / raw[2:]).resolve()
    if raw.startswith("$"):
        return None                      # an env reference is not a declaration
    return Path(raw)


def mounted_courses() -> tuple[str, ...]:
    """Every course namespace mounted under lo-blocks' `content/`.

    PYTHON'S OWN TWIN of `enforce/courseData.mountedCourses`, and deliberately
    not a call into it: lo-blocks must never depend on python, and python
    reading lo-blocks' answer would make the dependency point the other way for
    the sake of one list. Both sides read the same directory and neither tells
    the other -- the same arrangement the two declaration readers already have.

    A DIRECTORY OR A SYMLINK, with a dot in its name. The mounts are namespaces
    (`edu.memphis.psych`); `demos`, `README.md` and `static.config.json` sit
    beside them and are not courses.

    NEVER RAISES. This is read while `paths` is still deciding where files are,
    and a module that dies at that point leaves no way to report why. An
    unreadable `content/` means no course is known to be mounted, which the
    caller must then decide about.
    """
    try:
        return tuple(sorted(
            d.name for d in (LO / "content").iterdir()
            if "." in d.name and (d.is_dir() or d.is_symlink())))
    except OSError:
        return ()


def _course_root(name: str, key: str, fallback, repo=None):
    """One per-course root: the COURSE'S DECLARATION first, then `$NAME`.

    DECLARATION-FIRST, on the user's ruling of 2026-09-25 -- *"declaration-first
    is correct"* -- which makes this side agree with `enforce/courseData.courseDir`
    on ORDER as well as on ambiguity. Subgoal E58 asked for exactly that: the
    python half should reach lo-blocks' rule rather than write a second one.

    IT WAS env -> declaration -> fallback until then, and the reason it was
    written that way is worth keeping: `_rubric_declares` argued the safety of
    the whole arrangement rested on "nothing that resolves today can resolve
    differently tomorrow". Measured before flipping, and nothing here does --
    this course declares `~/molly_data` and the environment names the same
    directory, and no `$COURSE_METADATA` is set at all.

    A DECLARATION CANNOT BE AMBIGUOUS, which is why only the environment is
    checked against the mount count: a declaration lives in one course's own
    rubric and names one course's root by construction.

    AND AN OVERRIDDEN VARIABLE SAYS SO. Declaration-first means an explicit
    `COURSE_DATA=... python3 ...` is now IGNORED when the course declares that
    root, which is correct and is also exactly the kind of silence that costs an
    afternoon. So it is announced, once, naming both paths. lo-blocks prefers
    the declaration silently; matching that too would trade a real ruling for a
    trap, and this is the smaller divergence of the two.
    """
    declared = _rubric_declares(key, repo)
    supplied = (env_renamed(name) if name in _RENAMED
                else os.environ.get(name))
    if declared is not None:
        if supplied and str(Path(supplied)) != str(Path(declared)):
            _say_once(
                f"paths: ${name} is set to {supplied} and this course declares "
                f"{key}: {declared}. THE DECLARATION WINS -- a course's own "
                f"rubric is the authority on its roots, and one variable cannot "
                f"name several courses'. Unset ${name}, or change the "
                f"declaration, if the variable was what you meant.")
        return declared
    if supplied:
        # THE VARIABLE IS ON ITS WAY OUT, and a deprecation nobody is told about
        # is a deprecation that never happens. It is still honoured -- this is
        # the only thing keeping a course that declares nothing working -- but
        # the run says so once, and says what to write instead.
        _say_once(
            f"paths: ${name} is DEPRECATED for course information. This course "
            f"declares no {key}:, so the variable is honoured -- but a global "
            f"variable cannot name several courses' roots, and the engines are "
            f"standardising on the course declaring its own. Add `{key}: ...` "
            f"to the rubric's frontmatter.")
    return _one_course_only(name, supplied) or fallback


def _say_once(message: str) -> None:
    """Warn on stderr, once per process, about something a run should know."""
    if message not in _WARNED:
        _WARNED.add(message)
        print(message, file=sys.stderr)


def _one_course_only(name: str, value):
    """`value`, unless a GLOBAL VARIABLE is what supplied it and it cannot.

    THE RULE IS LO-BLOCKS', AND IT IS NOT INVENTED HERE. `courseDir` honours
    `$COURSE_DATA` only while ONE course is mounted, and with several it REFUSES
    -- naming them -- because one variable naming one directory cannot be right
    for all of them. Subgoal E58 says outright that the python half should reach
    that rule rather than write a second one.

    PRECEDENCE IS STILL env -> declaration -> fallback on this side, which is
    NOT lo-blocks' order (it puts the declaration first). That difference is
    real and is left standing deliberately: flipping it would change what
    resolves today for anyone whose declaration and environment differ, and
    `_rubric_declares` records that the safety of the whole arrangement rests on
    "nothing that resolves today can resolve differently tomorrow". What is
    added here is the AMBIGUITY half, which changes nothing for a one-course
    checkout and refuses the case that is silently wrong today.
    """
    # ONLY THE ENVIRONMENT IS AMBIGUOUS. A DECLARATION is already per course --
    # it lives in that course's own rubric -- so it cannot be the thing that
    # names two courses' data, and refusing it would be refusing the very
    # mechanism that makes several mounts workable. Caught by the control:
    # unsetting `$COURSE_DATA` with two courses mounted refused, when it should
    # have let the declaration decide.
    supplied = (env_renamed(name) if name in _RENAMED
                else os.environ.get(name))
    if value is None or supplied is None:
        return value
    mounted = mounted_courses()
    if len(mounted) <= 1:
        return value
    raise SystemExit(
        f"${name} cannot be used -- {len(mounted)} courses are mounted "
        f"({', '.join(mounted)}) and one variable cannot name them all. "
        f"Each course declares its own roots in its rubric's frontmatter; "
        f"declare {name.lower()}: for the course you mean, or run with one "
        f"course mounted. Refusing rather than picking one, which is the rule "
        f"`enforce/courseData.courseDir` already applies on the lo-blocks side.")


# THE CONTENT COLLECTION: the directory holding this course's `.olx` files.
#
def _collection_dir(location=None) -> Path:
    """The content COLLECTION holding a course: the nearest `manifest.yaml`.

    INFERRED FROM `COURSE_LOCATION`, on the user's instruction of 2026-09-25 --
    *"That has to be inferred from $COURSE_LOCATION"*. A collection holds one or
    more courses' `.olx` beside the assets they share.

    IT WAS `location.parent`, WHICH IS A DEPTH ASSUMPTION. One directory up is
    the collection only when a course sits exactly one level inside it, and the
    user's ruling of 2026-09-26 covers this line as much as the rubric search
    above: nothing here may assume how deeply a course is embedded. A course
    whose rubric sits directly in the collection has no folder of its own, and
    `location.parent` walked straight PAST the collection to whatever contains
    it -- silently, since every root derived from it still looked like a path.

    THE MANIFEST IS WHAT MAKES A DIRECTORY A COLLECTION. It is already the file
    that declares the namespace, the course's filenames and its routes, and
    `_collection_namespace` already finds it by walking up. Searching from the
    course's own folder outward answers both layouts with one rule and needs no
    number in it.

    THE FALLBACK IS THE PARENT, for a tree that has no manifest anywhere above
    the course. That is the old behaviour, kept for exactly the case where
    there is nothing better to infer from.
    """
    here = Path(location if location is not None else _course_location())
    for d in (here, *here.parents):
        if (d / "manifest.yaml").is_file():
            return d
    return here.parent


OLX_DIR = _collection_dir()

# THE COURSE'S DECLARATION, then `$COURSE_DATA`, then the historical fallback.
# See `_course_root` for the ordering and `_rubric_declares` for why the engine
# no longer spells this course's data directory.
DATA = Path(_course_root("COURSE_DATA", "course_data", Path.home() / "molly_data"))

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

    `$COURSE_NS` IS NOT ON THE RETIREMENT LIST, and the distinction is the whole
    reason the list exists. The user's rule, 2026-09-25, is about variables that
    carry course INFORMATION -- "there may be many courses" and one variable
    cannot describe them all, so `$COURSE_DATA` and its siblings are deprecated
    in favour of each course declaring its own roots. This variable describes
    nothing. It SELECTS which of the mounted courses is active, which is exactly
    the job a global is right for: there is one active course at a time by
    definition, and a process serving two asks for them BY NAME through
    `roots(ns)` rather than by changing this.

    So a selector stays and the describers go. If this ever starts naming a root
    rather than a course, it has changed category and belongs with them.
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


def _scoring_id(key: str, repo=None, ns: str | None = None) -> str:
    """The id of the RUBRIC, or of the INSTRUMENT it scores.

    THE NAMESPACE WAS DOING THIS JOB AND IS NOT THE RIGHT THING FOR IT. It names
    a content COLLECTION, and a collection can serve several courses -- while
    everything under the data root is owned by one of two narrower things. The
    user's framing, 2026-09-26: *"it's not really the COURSE that's the
    individuator. It's the rubric"*, and then *"the original handouts are
    instruments, not rubrics"*.

    (The collection that prompted this is not named here on purpose: this module
    is migrated, and a course's vocabulary in its prose is what the course-data
    ratchet counts. The example lives in the backlog entry instead.)

    THE SPLIT IS NOT COSMETIC. Two rubrics scoring one handout read the SAME
    submissions, the same hand-split rows and the same reconstructed fixtures --
    so filing those under a rubric id would not merely mislabel them, it would
    invite a second copy of the corpus. What genuinely differs per rubric is the
    run archive, the composed documents and the gold interpretation.

    DERIVED BY SHAPE, declarable by name, AND THE TWO KEYS DERIVE DIFFERENTLY --
    which they did not until 2026-09-26, and that was the defect. Both stripped
    `_rubric` from the rubric file's stem, so a rubric called `<x>_rubric.olx`
    and the handouts `<x>_handout1.olx` beside it BOTH answered `<x>`. The two
    owners this function exists to tell apart were indistinguishable by name,
    and the store held `rubrics/<x>` and `instruments/<x>` -- the split above
    described in prose and undone in one line.

    IT WAS INVISIBLE, AND WOULD HAVE STAYED SO. One rubric scoring one
    instrument gives two directories that are merely redundant, not wrong. A
    SECOND rubric for the same instrument is the case the split is for, and it
    is the case where the collision bites -- which is why nothing measured it.
    The user asked the question that found it: *"isn't the id of the rubric
    bmod_rubric, and bmod is the course id?"*

    SO: the INSTRUMENT is the family the handouts share, which is the stem with
    `_rubric` removed -- `<x>_handout1.olx` really is `<x>`'s. The RUBRIC is the
    component itself, and its id is its whole stem. A second rubric,
    `<x>_alt_rubric.olx`, is then `<x>_alt_rubric` and shares the instrument
    `<x>` with the first, which is exactly the arrangement the paragraph above
    promises.

    A course that needs other values says so with `rubric_id:` /
    `instrument_id:` in the frontmatter, and a tree with no rubric at all falls
    back to the namespace -- the honest answer when there is nothing narrower.
    """
    declared = _rubric_declares(key, repo)
    if declared is not None:
        return str(declared)
    cand = _rubric_file(repo)
    if cand is not None:
        stem = cand.name.removesuffix(".olx")
        if key == "rubric_id":
            return stem
        return stem.removesuffix("_rubric") or stem
    # THE TARGET'S OWN NAMESPACE, NOT THE ACTIVE ONE. Falling back to `NS` here
    # gave `roots("stub")` the id `edu.memphis.psych` -- a second course
    # resolving to the FIRST course's directory, which is precisely the
    # cross-contamination this accessor exists to stop, reintroduced through the
    # fallback rather than through a variable. Caught by reading the answer for
    # a course that has no rubric, which is the only shape that reaches here.
    return ns or NS


RUBRIC_ID = _scoring_id("rubric_id")
INSTRUMENT_ID = _scoring_id("instrument_id")


def _course_manifest(key: str, default):
    """One fact from the manifest, but ONLY if that manifest is THIS course's.

    J-4d. `_manifest` above reads whatever manifest sits beside `OLX_DIR`, which
    is the ENGINE REPO's content directory -- it does not change when `COURSE_NS`
    does. So a bare manifest key leaks: running as the stub, `OLX_DIR` still
    points at the RESIDENT course's content directory, and the stub would
    inherit a flag declared for a course it is not.

    THAT SENTENCE NAMED THE RESIDENT COURSE'S DIRECTORY until 2026-09-25, which
    made this module carry a course-data embedding -- the one thing it is about
    preventing. The example is no weaker for being generic: the leak is that
    `OLX_DIR` does not follow `COURSE_NS`, and WHOSE directory it is stuck on is
    not part of the mechanism.

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
#
# NO COURSE SETS IT ANY MORE. `edu.memphis.psych` was the only one, and on
# 2026-09-26 the user authorised the move that standardised it; its submissions,
# hand-split fixtures and outputs now sit under `courses/<ns>/` like everyone
# else's. The flag is kept rather than deleted because the legacy directories
# are still on disk as the recovery path, and because a course arriving from an
# older checkout needs a way to SAY so -- which is the whole reason this is
# declared and not sniffed. It should read False for every course that follows.
# THE TWO OWNERS, and every accumulated root hangs off one of them.
#
# `shared_data_layout` STOOD HERE AND IS RETIRED. It chose between the
# pre-namespacing shared roots and `courses/<ns>/`, and on 2026-09-26 the user
# authorised the move that emptied the first branch -- then observed that the
# second was keyed on the wrong thing anyway. A flag selecting between two wrong
# layouts has nothing left to select. Nothing declares it; the audit, the sha
# ratchet and the full suite all held across its removal.
#
# WHY TWO ROOTS AND NOT ONE. `instruments/<id>/` holds what the HANDOUT owns --
# the handout documents, the responses to it, and the two derived segmentations
# of those responses. `rubrics/<id>/` holds what a SCORING SPECIFICATION owns --
# its run archive, its composed documents, its gold. Write a second rubric for
# the same handout and the first tree is shared unchanged while the second is
# new. That is the whole content of the distinction, and a single root cannot
# express it without duplicating a corpus.
RUBRIC_DIR = DATA / "rubrics" / RUBRIC_ID
INSTRUMENT_DIR = DATA / "instruments" / INSTRUMENT_ID

# PRIMARY AND DERIVED, SAID IN THE DIRECTORY NAME. 2026-09-26, on the user's
# question: does the layout distinguish ground truth from what we computed from
# it, visibly? It did not -- `materials/` (as issued) sat beside `fixture/`
# (computed), and `consensus.json` (hand-adjudicated, irreplaceable) sat four
# levels inside the run archive.
#
# THE POINT IS THE GUARD. Protection was an ENUMERATION in `writescope.sh`, and
# it had to be rewritten TWICE in one day to chase `submissions` and `handsplit`
# as they moved -- a guard that loses its subject in a move is worse than none,
# because it still reports IN SCOPE. With the split the rule is positional:
# nothing under a `source/` is writable, whatever it is called and wherever its
# owner moves.
#
# `source/` MEANS IRREPLACEABLE, not pristine. `handsplit/` and `consensus/`
# are DERIVED from submissions -- by a person, once, exercising judgement. They
# cannot be regenerated, which is the property that matters here, so they are
# filed with the things that cannot be rebuilt rather than with the things that
# can.
INSTRUMENT_SOURCE = INSTRUMENT_DIR / "source"
INSTRUMENT_DERIVED = INSTRUMENT_DIR / "derived"
# THE RUBRIC'S AUTHORED DOCUMENTS: `rubrics/<id>/authored`. Its guides, its
# ledgers, its approved closures, and the override log the gate writes about it.
#
# IT WAS RETIRED FOR ONE AFTERNOON. The documents were consolidated into a
# `<rubric id>_qc/` directory in the COURSE tree, this root lost its last reader,
# and it was removed as a root pointing at nothing. The user's ruling the same
# day -- *"the bmod_rubric location for the specific .md files was a bad idea"*
# -- put them back under the store, beside the rubric's other records, which is
# where they had been before. The store now lives INSIDE the repository
# (declared `course_data:`), so filing them here no longer means putting them
# outside version control, which was the objection the consolidation answered.
RUBRIC_AUTHORED = RUBRIC_DIR / "authored"
RUBRIC_DERIVED = RUBRIC_DIR / "derived"

OUT = Path(_course_root("COURSE_OUT", "course_out", RUBRIC_DERIVED / "out"))

MATERIALS = Path(_course_root("COURSE_MATERIALS", "course_materials",
                              INSTRUMENT_SOURCE / "materials"))

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
# DECLARED BY THE COURSE, not spelled here. `_course_location` sits beside
# `_rubric_file` at the top of this module, because `OLX_DIR` is derived from it
# and is needed long before this line.
COURSE_LOCATION = _course_location()

# WHERE COMPOSED DOCUMENTS ARE BUILT. A composed document is DERIVED -- the generic
# half spliced with this course's cases -- so it is neither authored nor
# accumulated and belongs in neither the content repository nor the run archive.
# It is per-course because its course half is, and it is rebuilt rather than
# edited: editing it edits nothing, since the next build overwrites it.
COMPOSED_DOCS = Path(os.environ.get("COMPOSED_DOCS", RUBRIC_DERIVED / "composed"))

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
# WITH THE RUBRIC, 2026-09-26, on the user's instruction: the directory held
# `course.json`, the probe and measurement ledgers, the designed-text shas and
# the leakage review -- *"rubric information for bmod_rubric"* to a file, so a
# root of its own beside the repository said they belonged to the COURSE when
# every one of them belongs to the rubric. A second rubric for the same course
# would have written its ledgers over the first's.
#
# THE DEFAULT IS THE RUBRIC DIRECTORY and the declaration still overrides it,
# so a course that keeps its records elsewhere says so and nothing here
# changes. The `metadata` record-path token keeps its name: it means "where
# this course's records live", which is still true, and the stored records
# spell that token rather than a path.
COURSE_METADATA = Path(_course_root("COURSE_METADATA", "course_metadata",
                                    RUBRIC_DIR))

COURSE_FILE = Path(_course_root("COURSE_FILE", "course_file",
                                COURSE_METADATA / "course.json"))

# THE COURSE'S SCORING CHANGELOG, beside the course file for the same reason: it
# is this course's record of incidents, not the engine's. F1 sends an incident
# here, and a gate that strips sentences while their destination is undefined
# produces deletions rather than moves -- so the destination is named in one
# place.
COURSE_CHANGELOG = Path(os.environ.get(
    "COURSE_CHANGELOG", COURSE_METADATA / "CHANGELOG.md"))

# THE COURSE'S OWN PYTHON, and there are two roots because there are two kinds
# of thing. 2026-09-25, on the user's ruling: *"I don't WANT python code in
# $COURSE_DATA or $COURSE_METADATA"*.
#
# WHAT THE RULING IS ABOUT. `COURSE_METADATA` is the records root -- course.json,
# the changelog, the measured and probed ledgers -- and it had accumulated two
# `.py` files that are not records at all: the course's operant-conditioning
# scorer (932 lines, of which twenty definitions are code and two are tables) and
# its segmentation hook. A directory that holds both data and code has no rule
# left about what may be written into it, and "metadata" stops meaning anything.
# So the code moved out and the records root is DATA ONLY.
#
# NOT BACK INTO THE ENGINE, which is the other thing this is not. Goal E moved
# `scorer_oc` out of `scoring/` so that "the engine ships no subject's scorer",
# and that still holds: these sit in the COURSE repository, beside `scoring/`
# rather than inside it, and the engine reaches them only through a name an item
# declares (`scorers.resolve`) or an optional hook it can do without
# (`segment.course_hook`). Moving them up one level changes where a course keeps
# its code, not whether the engine knows what it does.
# ONE DIRECTORY PER COURSE, 2026-09-26, on the user's instruction: *"scorers
# also contains bmod course-specific code, so its content should be under
# scorers/bmod and accessed/enforced as such"*. A flat `scorers/` held this
# course's operant-conditioning scorer with nothing in the path saying whose it
# was, so a second course mounted in the same repository would have put its
# modules beside them and `scorers.resolve` would have picked by name alone.
#
# THE COURSE SEGMENT IS THE COURSE'S OWN FOLDER NAME, not the rubric's: a
# scorer belongs to the course whose items it scores, and two rubrics for one
# course share it. `roots().location.name` is that folder, so nothing here
# spells it.
COURSE_SCORERS = Path(os.environ.get(
    "COURSE_SCORERS", REPO / "scorers" / _course_location().name))

# THE COURSE'S FIXTURE CODE -- and note the near-namesake below. `COURSE_FIXTURE`
# is a directory of python that goes on `sys.path`; `COURSE_FIXTURE_DATA` is the
# ~1.3 MB of student-derived records goal N moved out to `$COURSE_DATA`. They
# were briefly the same directory, which is how one of them came to hold code.
# PER COURSE TOO, and for the same reason: the segmentation hook describes how
# ONE course's handouts are cut into boxes.
COURSE_FIXTURE = Path(os.environ.get(
    "COURSE_FIXTURE", REPO / "fixture" / _course_location().name))

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
# INSTRUMENT-OWNED. `CONSENSUS_SPANS.json` is a reconstruction of what each
# student wrote into the handout's boxes; it follows the INSTRUMENT's structure
# and is identical for every rubric scoring it.
COURSE_FIXTURE_DATA = Path(os.environ.get(
    "COURSE_FIXTURE_DATA", INSTRUMENT_DERIVED / "fixture"))

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

OLX = str(_course_location() / HANDOUT_OLX)


def handout_olx(form) -> str:
    """This course's content FILE NAME for one handout, e.g. for `load_action`."""
    return HANDOUT_OLX % int(form)


def handout_olx_glob() -> str:
    """A glob matching every handout's content file.

    DERIVED from the pattern, not written beside it: the two were the same fact
    and a course changing one would have left the other matching nothing.
    """
    return HANDOUT_OLX.replace("%d", "*")


def handout_olx_path(form):
    """The full path to one handout's content file."""
    return _course_location() / handout_olx(form)


def handout_olx_paths() -> list:
    """Every handout content file this course has, in form order.

    ONE PLACE THAT ANSWERS IT. Five modules each globbed the pattern against a
    directory of their own choosing, so when this course's material moved into
    a folder of its own on 2026-09-26 each was a separate site that could be
    missed -- and a glob that matches nothing returns an empty list, which
    reads downstream as "this course has no handouts" rather than as a broken
    path. That is the failure shape this project keeps meeting, so the lookup
    is prepared once here and the callers ask.

    THE COURSE'S OWN FOLDER, not the collection. `_course_location()` is the
    directory the rubric sits in, so this makes no assumption about depth: a
    course keeping its material beside its rubric is found wherever that is.
    """
    return sorted(_course_location().glob(handout_olx_glob()))

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

# THE ASSEMBLED COURSE FILE, declared like the rubric component beside it.
# `enforcement` spelled `bmod_course.olx` twice and the four element ids it must
# link once more -- this course's file stems in engine code, which is exactly
# what `_manifest` exists to end. The defaults keep every existing tree reading
# the file it already reads.
COURSE_OLX = _manifest("course_olx", "bmod_course.olx", "COURSE_COURSE_OLX")

# WHAT THE COURSE FILE MUST LINK: the rubric component and every form, by
# ELEMENT id. Derived from the two stems above rather than listed, so a course
# that renames its files does not also have to restate its ids -- and so the
# list cannot fall out of step with `declared()`.
def course_links() -> tuple:
    """The element ids `COURSE_OLX` is required to `<Use ref=...>`."""
    import forms

    stem = RUBRIC_COMPONENT.removesuffix(".olx")
    return (stem,) + tuple(
        (HANDOUT_OLX % h).removesuffix(".olx") for h in forms.declared())

# The engine contract (Class C: still cross-repo).
PRIMITIVES_JSON = LO / "packages/shared/lib/llm/primitives.json"
SLOTSHEET_TS = LO / "packages/shared/lib/llm/slotSheet.ts"
RUNNER = "packages/shared/lib/llm/runner.test.ts"
PROBE = "packages/shared/lib/llm/probe.test.ts"

# The corpus (local only).
SUBS = Path(os.environ.get("COURSE_SUBS", INSTRUMENT_SOURCE / "submissions"))
# HAND-SPLIT FIXTURES, and they follow the LAYOUT like everything else.
#
# This read `DATA / "handsplit"` unconditionally -- at the SHARED root whichever
# course was loaded, even one that declares the standard layout. That is the
# same collision J-4c closed for `out/`: a second course would find the first
# course's hand-split rows and have no way to say otherwise. `out` and `submissions`
# were made layout-aware and this was left behind, so the flag only ever moved
# two of the three roots it reads as governing.
#
# IT WAS INERT WHEN WRITTEN, being a precondition of the standardisation rather
# than a part of it. The standardisation landed 2026-09-26 and this line is what
# carried `handsplit` across with `out` and `submissions`; had it been left
# unconditional, the flip would have moved two roots of the three and left the
# fixtures behind at an address no declaration mentioned.
HANDSPLIT = Path(_course_root("COURSE_HANDSPLIT", "course_handsplit",
                              INSTRUMENT_SOURCE / "handsplit"))



# ── Asking for a course by name ──────────────────────────────────────────────
#
# THE ONE-COURSE ASSUMPTION, AND WHERE IT ACTUALLY LIVES. Subgoal E58 is about
# `DATA` and `COURSE_METADATA` being module-level constants computed once at
# import: twenty of the names above are per course, and a process serving two
# courses cannot read two values out of one global. Everything before this line
# resolves THE ACTIVE COURSE; everything from here lets a caller name one.
#
# NOT `__getattr__`, which was the obvious mechanism and is RULED OUT: goal K
# measured that serving names through it makes them INVISIBLE to `editguard`'s
# inventory -- five moved names were reported VANISHED and each had to be
# accepted by hand -- and doing that to fifteen constants would trade a check
# that works for a convenience.
#
# SO THE CONSTANTS STAY AND AN ACCESSOR IS ADDED BESIDE THEM. They are the
# single-course case, which is every caller today; `roots(ns)` is how a caller
# that means a PARTICULAR course says so. Nothing has to be converted for the
# accessor to be correct, and a caller converted to it stops depending on which
# course happened to be active at import.


# DIRECTORIES A REPOSITORY WALK MUST NOT DESCEND. Version control,
# dependencies, bytecode, build stages -- and THE DATA STORE, which is the one
# that is derived rather than named.
#
# WHY THE STORE. A course may declare its `course_data:` inside its own
# repository, which the dry run does so that two trees cannot collide in one
# store. The store then sits under `REPO` holding tens of thousands of files
# and gigabytes of run archive, and every repository-wide check began walking
# it: one check went from instant to 33 seconds, and the walkers that look for
# `.json` or `.md` were a step away from reading gold and the response
# fixtures as if they were source.
#
# DERIVED, NOT SPELLED, because the store's directory name is the course's to
# choose. `DATA` and `OUT` are asked where they actually are, and pruned only
# when they fall inside the tree being walked.
_WALK_PRUNE_NAMES = frozenset({
    ".git", ".hg", ".svn", "node_modules", "__pycache__", ".stage",
    ".venv", "venv", ".tox", ".mypy_cache", ".pytest_cache", ".ruff_cache",
})


# THE ENGINE'S OWN RECORDS: `scoring/metadata/`. The definition inventory, the
# three ratchet budgets, the shape inventory, the peg registry, the grader-input
# declarations and the port worklist -- records ABOUT the machinery, keyed by
# module, not by any course's items.
#
# A DIRECTORY OF THEIR OWN, on the user's instruction of 2026-09-27. They sat
# loose among the modules, where a reader could not tell a record from code
# without opening it, and where "what is in `scoring/`?" had two answers.
SCORING_METADATA = SCORING / "metadata"

# The general scorers' directory: `scorers/`, with each course's own one level
# down inside it.
SCORERS_GENERAL = REPO / "scorers"

# THIS COURSE'S NON-SCORING ENGINE MODULES: `scoring/<course>/`. The builders
# that author its declarations, the readers of its gold workbooks, its baseline
# comparison, its consensus parse, its session simulator -- course-specific, and
# none of them produces a score.
#
# THE LINE BETWEEN THIS AND `scorers/<course>/`, drawn by the user 2026-09-27
# and then sharpened by what `scorers.resolve` actually does: that function
# loads `<declared name>.py` from the course's scorer directory, so what belongs
# there is what an ITEM CAN NAME as its scorer. Everything else a course ships
# is an engine module that happens to be about one course, and lives here.
SCORING_COURSE = SCORING / _course_location().name

# THE GENERAL SCORERS ARE IMPORTABLE, wherever they live. `scorers/` holds the
# programs that can score ANY rubric -- the generic criteria scorer, the probe
# runner, the sweep harnesses -- on the user's instruction of 2026-09-27 that
# a general utility does not belong in the engine's own package directory.
#
# ON `sys.path` RATHER THAN REWRITTEN AT EVERY CALL SITE. `agreement` and
# `agreement_app` are each imported by ten modules here; rewriting thirty-odd
# import statements to a package path would be thirty chances to miss one, and
# a missed one fails at run time in whichever rare branch imports it. Putting
# the directory on the path keeps every existing `import agreement_app` true.
#
# THE COURSE'S OWN SCORERS ARE NOT ON THE PATH: they live one level down in
# `scorers/<course>/` and are loaded BY FILE through `scorers.resolve`, which
# is what keeps two courses' modules from colliding on a bare module name.
for _d in (SCORERS_GENERAL, SCORING_COURSE):
    if str(_d) not in sys.path:
        sys.path.append(str(_d))


def walk_prune_dirs(root=None) -> set:
    """Absolute directories a walk of `root` should skip."""
    base = Path(root or REPO).resolve()
    out = set()
    for p in (DATA, OUT):
        try:
            rp = Path(p).resolve()
        except Exception:                          # pragma: no cover
            continue
        if rp == base or base in rp.parents:
            out.add(rp)
    return out


def module_path(name: str):
    """Where one engine module's source file is, wherever it now lives.

    ASKED OF THE IMPORT SYSTEM, not built from a directory. Checks that read
    another module's SOURCE -- for its era stamp, for item-gating, for whether
    it still calls a shared function -- used to join `<name>.py` onto the
    package directory. That was true while every module sat in `scoring/`. When
    the general scorers moved to `scorers/` and a course's own modules to
    `scoring/<course>/`, those joins produced paths that do not exist, and the
    checks reported "cannot be read ... which is not the same as passing" --
    correctly, but about nothing. Two of them aborted the whole audit instead.

    `import` ALREADY KNOWS, because this module puts both directories on the
    path. One resolution that cannot go stale beats five that each have to be
    remembered.
    """
    import importlib
    mod = importlib.import_module(name.removesuffix(".py"))
    return Path(mod.__file__)


def module_source(name: str) -> str:
    """The text of one engine module, wherever it lives. See `module_path`."""
    return module_path(name).read_text(encoding="utf-8")


def repo_files(*suffixes, root=None):
    """Every file under `root` (default `REPO`), pruned as `walk_prune_dirs` says.

    ONE WALKER, so a directory that must not be read is excluded everywhere at
    once rather than in each check that happens to remember. `suffixes` filters
    by extension; with none, every file is yielded.
    """
    base = Path(root or REPO)
    skip = walk_prune_dirs(base)
    out = []
    for dirpath, dirnames, filenames in os.walk(base, onerror=lambda e: None):
        here = Path(dirpath)
        dirnames[:] = [d for d in dirnames
                       if d not in _WALK_PRUNE_NAMES
                       and (here / d).resolve() not in skip]
        for fn in filenames:
            if not suffixes or fn.endswith(tuple(suffixes)):
                out.append(here / fn)
    return sorted(out)


def rubric_docs_dir(repo=None, ns: str | None = None):
    """Where a rubric's authored documents live: `rubrics/<id>/authored`.

    NAMED FOR NEITHER THE COURSE NOR THE RUBRIC, because the path already says
    whose they are: the rubric's id is the directory above this one. A
    `<rubric id>_qc/` directory in the course tree spelled that id a second
    time, one directory away from the id that owns it, and it did not survive
    the afternoon.

    THE ID STILL INDIVIDUATES. Two rubrics for one course get
    `rubrics/<a>/authored` and `rubrics/<b>/authored`, so the property that
    forced the rename -- that these documents belong to a RUBRIC and not to a
    course -- is carried by the layout instead of by a name.
    """
    if ns is None and repo is None:
        return RUBRIC_AUTHORED
    return DATA / "rubrics" / _scoring_id("rubric_id", repo, ns) / "authored"


def _qc_documents(location, ns: str | None = None) -> dict:
    """`{filename: path}` for the course's quality-control documents.

    THE GAP THIS CLOSES, found 2026-09-25 by asking whether every per-course
    document is reachable by something that knows where to look. `BACKLOG.md`
    was reachable by exactly one route -- `compose_docs.specific_path` -- so
    anything enumerating a course's locations could not see it, and a drift in
    the list of record would have taken it silently.

    IT USED TO READ `compose_docs.ACCUMULATING`, the documents filed outside the
    repository because they grow with course work. That set is empty as of
    2026-09-26: the QC documents were consolidated into `<course>/<rubric id>_qc/`, so the
    question "which documents live somewhere else" no longer selects anything.

    DERIVED FROM THE DIRECTORY, not from a list. The consolidation put eight
    files there -- two guides, two ledgers, a closure record, an override log
    and this course's measured dead ends -- with no single declaration naming
    all of them, and a hand-written copy here would be the drift that bit
    `DATA_MODULES` and `GENERIC_DOCS`. Reading the directory means a document
    added to the cycle is enumerable the moment it exists, and a document
    removed stops being claimed.

    KEYED BY FILENAME, not turned into a field per document, because the set is
    the course's to decide and a field each would have to be edited every time
    one is added.
    """
    qc = rubric_docs_dir(ns=ns)
    try:
        return {p.name: p for p in sorted(qc.iterdir()) if p.is_file()}
    except OSError:                               # absent is empty, not an error
        return {}


@dataclasses.dataclass(frozen=True)
class CourseRoots:
    """Every per-course root, for ONE named course.

    FROZEN, because the bug this exists for is a value changing underneath a
    reader. A mutable record handed to two callers is the module-level global
    again with more steps.
    """

    ns: str
    repo: Path
    data: Path
    # THE TWO OWNERS. Exposed as roots in their own right so that anything
    # enumerating a course's locations sees them -- the gap `_qc_documents`
    # was written to close, one level up.
    rubric_dir: Path
    instrument_dir: Path
    metadata: Path
    location: Path
    olx_dir: Path
    out: Path
    materials: Path
    course_file: Path
    changelog: Path
    fixture_data: Path
    submissions: Path
    handsplit: Path
    composed_docs: Path
    scorers: Path
    fixture: Path
    ledger: Path
    carried_notes: Path
    probed: Path
    probe_receipts: Path
    designed_text_sha: Path
    leakage_reviewed: Path
    # THE COURSE'S QC DOCUMENTS, keyed by filename. Derived from the contents
    # of `<course>/<rubric id>_qc/` rather than named one field at a time -- see
    # `_qc_documents`.
    documents: dict


def course_repo(ns: str) -> Path:
    """The repository holding a NAMED course, through the content mount.

    `content/<ns>` is how lo-blocks already reaches a course, and using the same
    route means the two engines agree about where a course IS before they can
    disagree about anything inside it. Resolved through the symlink for the
    reason `courseDir` was taught to: the mount and the course name the same
    directory by different strings, and a comparison between the sides should
    not read that as a difference.
    """
    if ns == NS:
        return REPO
    mount = LO / "content" / ns
    try:
        return Path(os.path.realpath(mount))
    except OSError:
        return mount


@functools.lru_cache(maxsize=None)
def roots(ns: str | None = None) -> CourseRoots:
    """Every root for one course, resolved from THAT course's declarations.

    `ns=None` means the active course, which is what the module constants above
    describe -- so `roots().data` and `DATA` are the same path by construction,
    and the two cannot drift.

    IT REACHES A SECOND COURSE'S DECLARATIONS, not just its directory. Each root
    goes through `_course_root` with that course's own repository, so a course
    declaring `course_data: ~/other_data` is read correctly while this one is
    still active. That is the whole point: the declaration is per course, so the
    reader has to be too.

    ENVIRONMENT VARIABLES ARE NOT CONSULTED FOR A NAMED COURSE, and this is the
    rule stated rather than an oversight. A global cannot name two courses'
    roots -- it is why they are being retired -- so asking for a course BY NAME
    and then honouring `$COURSE_DATA` would hand the named course the active
    one's data. `_course_root` still reads them for the active course, where
    there is exactly one to be right about.
    """
    target = ns or NS
    repo = course_repo(target)
    if target == NS:
        # The active course: exactly the constants above, by construction.
        return CourseRoots(
            ns=target, repo=REPO, data=DATA, metadata=COURSE_METADATA,
            rubric_dir=RUBRIC_DIR, instrument_dir=INSTRUMENT_DIR,
            location=COURSE_LOCATION, olx_dir=OLX_DIR, out=OUT,
            materials=MATERIALS, course_file=COURSE_FILE,
            changelog=COURSE_CHANGELOG, fixture_data=COURSE_FIXTURE_DATA,
            submissions=SUBS, handsplit=HANDSPLIT,
            composed_docs=COMPOSED_DOCS, scorers=COURSE_SCORERS,
            fixture=COURSE_FIXTURE, ledger=COURSE_LEDGER,
            carried_notes=COURSE_CARRIED_NOTES, probed=COURSE_PROBED,
            probe_receipts=COURSE_PROBE_RECEIPTS,
            designed_text_sha=COURSE_DESIGNED_TEXT_SHA,
            leakage_reviewed=COURSE_LEAKAGE_REVIEWED,
            documents=_qc_documents(COURSE_LOCATION, NS))

    def declared(key, fallback):
        got = _rubric_declares(key, repo)
        return Path(got) if got is not None else Path(fallback)

    data = declared("course_data", DATA)
    metadata = declared("course_metadata", repo / "course_metadata")
    location = _course_location(repo)
    # THE SAME TWO OWNERS, resolved from the NAMED course's own rubric. Spelling
    # `courses/<ns>/` here while the active branch used `rubrics/<id>/` would put
    # a second course's data somewhere the first course's reader never looks --
    # the cross-contamination `roots()` exists to prevent, reintroduced by a
    # layout rather than by a variable.
    rubric_dir = data / "rubrics" / _scoring_id("rubric_id", repo, target)
    instrument_dir = data / "instruments" / _scoring_id("instrument_id", repo,
                                                        target)
    return CourseRoots(
        ns=target, repo=repo, data=data, metadata=metadata, location=location,
        olx_dir=location.parent,
        rubric_dir=rubric_dir, instrument_dir=instrument_dir,
        out=declared("course_out", rubric_dir / "derived" / "out"),
        materials=declared("course_materials",
                           instrument_dir / "source" / "materials"),
        course_file=declared("course_file", metadata / "course.json"),
        changelog=metadata / "CHANGELOG.md",
        fixture_data=instrument_dir / "derived" / "fixture",
        submissions=instrument_dir / "source" / "submissions",
        handsplit=instrument_dir / "source" / "handsplit",
        composed_docs=rubric_dir / "derived" / "composed",
        scorers=repo / "scorers",
        fixture=repo / "fixture",
        ledger=metadata / "MEASURED.json",
        carried_notes=metadata / "CARRIED_NOTES.json",
        probed=metadata / "PROBED.json",
        probe_receipts=metadata / "PROBE_RECEIPTS.json",
        designed_text_sha=metadata / "DESIGNED_TEXT_SHA.json",
        leakage_reviewed=metadata / "LEAKAGE_REVIEWED.json",
        documents=_qc_documents(location, target))

# ── Paths inside RECORDS ─────────────────────────────────────────────────────

# THE ROOTS A RECORD MAY NAME, and the token it names each by.
#
# A RECORD THAT CARRIES AN ABSOLUTE PATH IS PINNED TO ONE MACHINE'S DISK, and
# worse, it is pinned to one DAY's layout. Measured 2026-09-26: `PROBED.json`
# held fifteen paths under `$COURSE_DATA/out/`, every one of them broken by the
# move to `rubrics/<id>/out/` that morning, and nothing reported it -- the
# records still parsed, the fields were still strings, and a reader that could
# not find a file simply found nothing. `course.json` held two more that
# survived only because they are regenerated from `paths` on every export.
#
# So a record names a ROOT and a path WITHIN it. The reader resolves; the record
# travels. `{rubric}` and `{instrument}` are the two owners, and the token is
# spelled with braces so an unresolved one is visibly not a path.
RECORD_ROOTS = {
    "rubric": lambda r: r.rubric_dir,
    "instrument": lambda r: r.instrument_dir,
    "metadata": lambda r: r.metadata,
    "repo": lambda r: r.repo,
}


def record_path(token: str, ns: str | None = None) -> Path:
    """Resolve `{root}/rest` against THIS course's roots.

    An absolute path is returned unchanged rather than refused: the records are
    being converted and an old one must keep working while that happens. What
    must not happen silently is a NEW absolute path, and that is
    `check_records_carry_no_machine_path`'s job, not this function's.
    """
    s = str(token)
    if not s.startswith("{"):
        return Path(s)
    name, _, rest = s[1:].partition("}")
    root = RECORD_ROOTS.get(name)
    if root is None:
        raise KeyError(
            f"record_path: `{{{name}}}` is not a declared record root. "
            f"Known: {sorted(RECORD_ROOTS)}")
    return Path(root(roots(ns))) / rest.lstrip("/")


def as_record_path(path, ns: str | None = None) -> str:
    """The inverse: `{root}/rest` for a path under one of the roots.

    Longest root first, so `instruments/<id>/fixture` is not matched by a root
    that happens to be its parent. A path under NO declared root is returned
    unchanged, and the check is what reports it.
    """
    p = Path(path).resolve()
    r = roots(ns)
    cands = sorted(((name, Path(fn(r)).resolve()) for name, fn in RECORD_ROOTS.items()),
                   key=lambda kv: len(str(kv[1])), reverse=True)
    for name, base in cands:
        try:
            rel = p.relative_to(base)
        except ValueError:
            continue
        return "{" + name + "}/" + rel.as_posix()
    return str(path)


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
