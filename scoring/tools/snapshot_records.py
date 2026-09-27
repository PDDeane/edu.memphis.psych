#!/usr/bin/env python3
"""Snapshot a course's IRREPLACEABLE records to its declared remote.

WHAT THIS IS FOR. Subgoal E59: a rubric's records live under `$COURSE_DATA`,
which is not a git repository and has no history, no backup and one copy. This
snapshots the rubric's whole directory so that loss is recoverable.

WHAT IT NO LONGER COVERS, and why that is not a gap. The goal ledger, the
override log, the backlog and the approved closures WERE here, and the reasoning
above was written about them: their bodies, measurements and closure notes
existed in one copy. On 2026-09-26 they were consolidated into `<course>/<rubric id>_qc/`
and tracked, so git holds their history and this tool no longer sees them -- it
walks the rubric directory, so the change needed no edit here. What remains is
gold and the derived records, which are what a course's MEASUREMENTS are and are
still single-copy.

NOT A REPOSITORY, on the user's ruling: *"we're talking data here, not code ...
not exactly what I want in a repository, no?"* These are records. What they need
is durability and recoverability -- snapshots with retention -- not commit
semantics, review or merge.

THE MECHANISM, DECIDED 2026-09-25: *"We'll have to use keep forever, with very
rigorous zipping up of data before we put it in the remote drive."* Both halves
were measured before being written down.

  * ONE PATH, REWRITTEN. Drive keeps REVISIONS of a file, so the history lives
    in one object rewritten in place -- measured: an rclone write keeps the same
    file id, so Drive records a revision rather than replacing the file. A
    timestamped filename per run would produce N files and NO history, which is
    the opposite of the point.
  * PINNED. Measured: without `--drive-keep-revision-forever` every revision
    comes back `keepForever=False`, which is Drive's default for binary files --
    roughly 30 days, then silent eviction. A month of history that looks
    permanent is worse than none.
  * ZIPPED, AND NARROWLY. Pinned revisions count against quota, so the archive's
    size is how many snapshots fit. Measured against 2.103 GiB free:

        records only   680 KB  ->  3,256 snapshots
        all of courses/ 5.1 MB  ->    429 snapshots
        out/            1.7 GB  ->  does not fit twice

WHAT IS EXCLUDED, AND WHY EACH. `composed/` is DERIVED -- it is the generic and
specific halves spliced, and `compose_docs.build()` regenerates it. `materials/`
is the authored handouts, which already exist in the course's own source folder
on the same Drive. Excluding those two is what takes the archive from 5.1 MB to
680 KB, and neither is a loss: a thing that can be rebuilt or is already stored
elsewhere does not need a pinned revision of its own.

`out/` IS NOT HERE AT ALL and must not be added. It is 1.7 GB of regenerable run
artifacts, and one pinned snapshot would consume most of the account. Subgoal
E59 says the two are pooled under one root today and want different policies;
this tool is the policy for the half that cannot be rebuilt.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE.parent) not in sys.path:
    sys.path.insert(0, str(HERE.parent))

# DERIVED, NOT LISTED. These are the two directories under a course's records
# that do not need snapshotting, named by what they ARE rather than by path, so
# a course laying them out differently still excludes the right things.
EXCLUDED = ("composed", "materials")

# 403 RATE LIMITING IS EXPECTED, AND IS NOT OURS. `rclone`'s shared Google client
# id puts every user who never made their own on ONE project's per-minute quota,
# so a refusal is usually a stranger's traffic: this measurement made about a
# dozen calls on 2026-09-25 and was refused twice in twenty minutes. Backoff
# cleared it both times.
#
# A 403 MUST NEVER READ AS SUCCESS, which is the half that matters. Every failure
# path here exits non-zero and says what failed; the caller is a backup, and a
# backup that reports success without writing is worse than one that fails.
RETRIES = 5
BACKOFF = 25


def remote_for(ns: str | None) -> str | None:
    """Where this course's records are archived, or None if it declares none.

    DECLARED BY THE COURSE, like every other root. A destination named in engine
    code would be one course's backup location inside machinery meant to know no
    course -- and, being a global, could not be right for a second one.
    """
    import paths

    return paths._rubric_declares("records_remote", paths.course_repo(ns or paths.NS))


def build_archive(ns: str | None, dest: Path) -> tuple[Path, int, int]:
    """Zip a course's irreplaceable records. -> (path, files, bytes)."""
    import paths

    r = paths.roots(ns)
    root = Path(r.rubric_dir)
    if not root.is_dir():
        raise SystemExit(f"snapshot_records: {root} does not exist, so there is "
                         f"nothing to snapshot -- refusing to write an empty "
                         f"archive over a good one")
    count = 0
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for p in sorted(root.rglob("*")):
            if not p.is_file():
                continue
            rel = p.relative_to(root)
            if rel.parts and rel.parts[0] in EXCLUDED:
                continue
            z.write(p, rel.as_posix())
            count += 1
    if count == 0:
        raise SystemExit(f"snapshot_records: {root} yielded no files. An empty "
                         f"archive pinned over a good revision is a silent loss")
    return dest, count, dest.stat().st_size


def upload(archive: Path, remote: str, folder_id: str | None) -> None:
    """Copy the archive to the remote, pinned, retrying a rate-limit refusal."""
    cmd = ["rclone", "copy", str(archive), remote, "--drive-keep-revision-forever"]
    if folder_id:
        cmd += ["--drive-root-folder-id", folder_id]
    last = ""
    for attempt in range(1, RETRIES + 1):
        done = subprocess.run(cmd, capture_output=True, text=True)
        if done.returncode == 0:
            return
        last = (done.stderr or done.stdout or "").strip()
        if "403" not in last and "quota" not in last.lower():
            raise SystemExit(f"snapshot_records: rclone failed: {last[:400]}")
        print(f"  attempt {attempt}: rate-limited, waiting {BACKOFF}s",
              file=sys.stderr)
        if attempt < RETRIES:
            import time
            time.sleep(BACKOFF)
    raise SystemExit(
        f"snapshot_records: still rate-limited after {RETRIES} attempts. This is "
        f"rclone's SHARED client id, whose quota belongs to every user who never "
        f"made their own -- see subgoal E59. NOTHING WAS WRITTEN: {last[:300]}")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--course", default=None, help="namespace; default is active")
    ap.add_argument("--folder-id", default=None,
                    help="Drive root folder id, if the remote is not pinned")
    ap.add_argument("--dry-run", action="store_true",
                    help="build the archive and report it; upload nothing")
    a = ap.parse_args(argv)

    import paths

    ns = a.course or paths.NS
    remote = remote_for(ns)
    folder = a.folder_id or paths._rubric_declares(
        "records_remote_folder_id", paths.course_repo(ns))
    if remote is None and not a.dry_run:
        raise SystemExit(
            f"snapshot_records: {ns} declares no `records_remote:` in its "
            f"rubric frontmatter, so there is nowhere to put its records. "
            f"Declare one, or run --dry-run to see what would be archived.")

    import tempfile
    tmp = Path(tempfile.gettempdir()) / f"{ns}.records.zip"
    _, files, size = build_archive(ns, tmp)
    print(f"  {ns}: {files} files, {size/1024:.0f} KB "
          f"(excluding {', '.join(EXCLUDED)})")
    if a.dry_run:
        print(f"  dry run: would upload to {remote or '<no records_remote declared>'}")
        return 0
    upload(tmp, str(remote), folder and str(folder))
    print(f"  uploaded to {remote}, revision pinned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
