#!/usr/bin/env python3
"""Strip personal names out of OOXML document metadata before publication.

A .docx/.pptx carries `docProps/core.xml`, and Word fills it with whoever
touched the file. That is invisible in the document body and survives every
copy, so a file can look impersonal and still name a person on open.

This matters here for a specific reason. The blank Handout #1 template — a
course material, published with the code so `segment.py` can subtract it from a
submission — carried a STUDENT's name and university username in `dc:creator`,
because the "blank" had been saved from that student's copy. Nothing in the
visible document said so. The same sweep turned up staff usernames and one name
belonging to neither list.

(The names are deliberately not repeated here. A docstring in a public repo is
published too, and a tool that names the person it exists to un-name defeats
itself — which is exactly what the first draft of this file did.)

Idempotent, and safe to re-run: it rewrites only the four fields below, leaving
the document body untouched. Run --check in CI or before a push; it exits 1 if
anything still names a person.

    python3 scrub_metadata.py --check materials/*.docx materials/*.pptx
    python3 scrub_metadata.py --write materials/*.docx materials/*.pptx
"""
from __future__ import annotations

import argparse
import re
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

# What the fields become. Attribution belongs in LICENSE.TXT / the manifest's
# content_notice, where it is deliberate and reviewable — not in file metadata
# that records whoever last hit save.
ATTRIBUTION = "University of Memphis PSYC 1030"

FIELDS = ("dc:creator", "cp:lastModifiedBy", "dc:lastModifiedBy", "cp:manager")


def _fields_in(xml: str) -> dict[str, str]:
    out = {}
    for tag in FIELDS:
        m = re.search(rf"<{tag}>([^<]*)</{tag}>", xml)
        if m and m.group(1).strip():
            out[tag] = m.group(1).strip()
    return out


def inspect(path: Path) -> dict[str, str]:
    try:
        z = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        return {}
    found = {}
    for name in z.namelist():
        if "docProps" in name and name.endswith(".xml"):
            found.update(_fields_in(z.read(name).decode("utf-8", "replace")))
    return {k: v for k, v in found.items() if v != ATTRIBUTION}


def scrub(path: Path) -> bool:
    """Rewrite the archive with the metadata fields neutralised."""
    z = zipfile.ZipFile(path)
    changed = False
    tmp = Path(tempfile.mkstemp(suffix=path.suffix)[1])
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as out:
        for item in z.infolist():
            data = z.read(item.filename)
            if "docProps" in item.filename and item.filename.endswith(".xml"):
                xml = data.decode("utf-8", "replace")
                for tag in FIELDS:
                    new = re.sub(rf"<{tag}>[^<]*</{tag}>",
                                 f"<{tag}>{ATTRIBUTION}</{tag}>", xml)
                    if new != xml:
                        xml, changed = new, True
                data = xml.encode("utf-8")
            out.writestr(item, data)
    z.close()
    if changed:
        shutil.move(str(tmp), str(path))
    else:
        tmp.unlink()
    return changed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only; exit 1 if any names remain")
    ap.add_argument("--write", action="store_true", help="scrub in place")
    ap.add_argument("files", nargs="+", type=Path)
    a = ap.parse_args()
    if not (a.check or a.write):
        ap.error("one of --check or --write is required")

    dirty = 0
    for f in a.files:
        found = inspect(f)
        if not found:
            continue
        dirty += 1
        print(f"{f.name}: " + ", ".join(f"{k}={v!r}" for k, v in found.items()),
              file=sys.stderr)
        if a.write and scrub(f):
            print(f"  scrubbed -> {ATTRIBUTION}", file=sys.stderr)

    if a.check and dirty:
        print(f"\n{dirty} file(s) still name a person. Run --write.", file=sys.stderr)
        return 1
    if not dirty:
        print("No personal names in document metadata.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
