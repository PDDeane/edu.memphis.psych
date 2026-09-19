#!/usr/bin/env python3
"""Every OLX text worth mining, from one place.

WHY THIS EXISTS, AND WHAT IT FIXES. Three declarations were built on a corpus
walk that said "every `.olx` under these roots". That walk was wrong three ways,
and each way is a different lesson:

1. **It counted a build artifact as evidence.** `lo-blocks/.stage/content` holds
   29 staged copies of the psych course, of which only 20 still match -- so the
   course was mined TWICE and a STALE copy was mixed in as independent evidence.
   Every edge count involving psych content was inflated, and nine files
   contributed text nobody had written that way any more.

2. **It ignored the documentation.** 68 block readmes carry 290 fenced OLX
   examples (`olx:playground`, `olx:code`, `olx:render`) -- a corpus the size of
   the standalone files, authored by the people who wrote the blocks, and
   therefore the best statement of intended use that exists.

3. **It looked only for `.olx`.** `ref-demo.xml` is demo content under another
   extension.

The lesson under all three: A CORPUS IS A DECISION, NOT A GLOB. Which files count
as evidence decides what every declaration built on them can say, so it is made
here, once, with reasons, rather than re-improvised in each tool.

NOT MINED, deliberately: the `.chatpeg`, `.textSelectionpeg`, `.textHighlightpeg`
and `.cast` files in the psych course, and the PEG grammars behind them. They are
a SEPARATE AUTHORING SURFACE -- compact teacher-writable syntaxes that expand
into blocks -- and mining them as though they were OLX would attribute to a
grammar what belongs to its expansion. They need their own treatment; see
`SHAPE_NOTES` below.
"""
from __future__ import annotations

import os
import re

# Directories that are build output, not source. `.stage` is the staging copy the
# content build writes; `dist`, `build` and `node_modules` speak for themselves.
ARTIFACT_DIRS = {".stage", "dist", "build", "node_modules", ".git", ".next"}

OLX_SUFFIXES = (".olx", ".xml")

# Fenced OLX inside documentation. `olx:playground` and `olx:render` are live
# examples; `olx:code` is a listing. All three are authored usage.
_FENCE = re.compile(r"```olx(?::\w+)?\s*\n(.*?)```", re.S)

# Formats that are NOT OLX and must not be mined as though they were.
SEPARATE_SURFACES = {
    ".chatpeg": "a Chat script in its own PEG grammar",
    ".textSelectionpeg": "a text-highlighting quiz: prose with [bracketed answers]",
    ".textHighlightpeg": "a text-highlighting quiz variant",
    ".cast": "a character cast, declared as data",
    ".liquid": "a Liquid template",
}


# THE CORPUS IS A DECLARED LIST, and getting here took three wrong turns worth
# recording, because each is the same mistake wearing a different hat.
#
#   1. `*.olx` under two roots -- swept in `lo-blocks/.stage/content`, a staging
#      COPY of the psych course, so the course was mined twice and nine stale
#      files counted as independent evidence.
#   2. sibling directories named `edu.*` -- found edu.memphis.writing and
#      edu.mtsu.transitional-reading, and missed `interdisciplinary`, which is
#      neither named `edu.*` nor beside the engine.
#   3. "any directory containing OLX" -- evidence-based, and WORSE: it found
#      nine roots including three parallel checkouts of trees already listed,
#      reporting 1171 files and 1155 documented examples where there are about
#      300 and 295 distinct. Counting a second checkout as a second course is
#      the `.stage` error again, at repository scale.
#
# Auto-discovery is a glob with extra steps. Which trees count as evidence is a
# judgement about what is DISTINCT, and nothing in the filesystem encodes it, so
# it is declared here with a reason each and overridden by `COURSE_ROOTS`.
DECLARED_ROOTS_WHY = {
    "engine": "the engine: component demos and the 295 documented examples",
    "writing": "a real second course -- journals, chat scripts and casts",
    "reading": "a real third course -- readings",
    "interdisciplinary": "a real fourth course -- SBA parts, a library, artifacts",
}


def declared_roots() -> list[tuple[str, str, bool]]:
    """-> [(path, why, exists)]. Missing roots are REPORTED, never skipped.

    A corpus that silently shrinks when a checkout moves reports smaller
    coverage and calls it a result.
    """
    import paths

    out = []
    for name, why in sorted(DECLARED_ROOTS_WHY.items()):
        resolve = paths.CORPUS_ROOTS.get(name)
        if resolve is None:                       # pragma: no cover
            continue
        path = os.path.abspath(str(resolve()))
        out.append((path, why, os.path.isdir(path)))
    return out


def default_roots() -> list[str]:
    """The declared roots that exist, plus this repo's own course content."""
    override = os.environ.get("COURSE_ROOTS")
    if override:
        return [p for p in override.split(":") if os.path.isdir(p)]
    roots = [p for p, _why, ok in declared_roots() if ok]
    own = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       "..", "psychology"))
    if os.path.isdir(own) and not any(own.startswith(r + os.sep) for r in roots):
        roots.append(own)
    return roots


def roots_inside_the_data_store() -> list[str]:
    """A declared corpus root that sits inside $COURSE_DATA. Refused.

    THE DATA ROOT HOLDS COPIES OF THE SOURCE. Measured 2026-09-18:
    `$COURSE_DATA` carries 63 `.py` files and six `.olx` -- `migration_reference/`
    preserves a whole engine half and three rubric `.olx`, and
    `pre_scrub_backup_.../psychology/` holds three course files and a PARTIAL,
    STALE copy of `scoring/` (20 files identical to the live tree, five
    differing).

    Nothing reads them today: every walk into the data store is scoped to `out/`
    with an explicit `*.runs.json` or `*.json` pattern. But this is exactly the
    shape that has already cost this project twice -- `lo-blocks/.stage/content`
    counted as a second course, and three parallel checkouts counted as three
    more -- and the third time should be prevented rather than diagnosed.
    """
    data = os.environ.get("COURSE_DATA") or os.environ.get("COURSE_DATA")
    if not data:
        return []
    data = os.path.abspath(os.path.expanduser(data))
    bad = []
    for path, why, ok in declared_roots():
        if ok and (path == data or path.startswith(data + os.sep)):
            bad.append(f"{path} ({why}) is a declared corpus root INSIDE the data "
                       f"store {data} -- that tree holds stale copies of the "
                       f"source and of course content, and mining a copy as "
                       f"evidence is how .stage came to count as a second course")
    return bad


def missing_roots() -> list[str]:
    """Declared trees that are not there. Reported by the gate, not ignored."""
    return [f"{p} ({why}) is declared corpus and is not present -- the corpus "
            f"silently shrank" for p, why, ok in declared_roots() if not ok]


def texts(roots: list[str], include_docs: bool = True):
    """Yield (label, olx_text). Artifacts excluded, documentation included."""
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in ARTIFACT_DIRS]
            for fn in sorted(filenames):
                path = os.path.join(dirpath, fn)
                if fn.endswith(OLX_SUFFIXES):
                    try:
                        yield fn, open(path, errors="ignore").read()
                    except OSError:
                        continue
                elif include_docs and fn.endswith(".md"):
                    try:
                        body = open(path, errors="ignore").read()
                    except OSError:
                        continue
                    for i, block in enumerate(_FENCE.findall(body), 1):
                        yield f"{fn}#example{i}", block


def census(roots: list[str]) -> dict:
    """What the corpus is made of -- printed so a change in it is visible."""
    out = {"olx_files": 0, "doc_examples": 0, "doc_files": set(),
           "separate_surface": {}}
    for label, _text in texts(roots):
        if "#example" in label:
            out["doc_examples"] += 1
            out["doc_files"].add(label.split("#")[0])
        else:
            out["olx_files"] += 1
    for root in roots:
        if not os.path.isdir(root):
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in ARTIFACT_DIRS]
            for fn in filenames:
                ext = os.path.splitext(fn)[1]
                if ext in SEPARATE_SURFACES:
                    out["separate_surface"][ext] = \
                        out["separate_surface"].get(ext, 0) + 1
    out["doc_files"] = len(out["doc_files"])
    return out
