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
