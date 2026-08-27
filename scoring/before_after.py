"""Run a snippet against the WORKING TREE and against a git ref, and diff.

    python3 before_after.py 'print(some_expression)'
    python3 before_after.py --ref HEAD~2 -f snippet.py

Why this exists. A harness fix was "verified" by running a test against the
FIXED code alone: a synthetic `count=1` fed to `score_slots` returned 4.0, which
was read as proof the fix worked. It proved only that `score_slots` can charge a
counted member -- the same input returned 4.0 before the change too, because the
machinery had never been broken. 140 calls were then spent sweeping items to
confirm an improvement that could not exist, and the wrong diagnosis was stated
out loud twice.

A before/after test needs the BEFORE. This runs the same snippet in a temporary
git worktree at the given ref (HEAD by default) and in the working tree, prints
both, and says whether they differ -- so "my fix changes X" is a claim with two
columns behind it rather than one.

The worktree is created under the system temp dir and removed afterwards. It is
a read-only use of the ref: nothing is stashed, so uncommitted work is never at
risk.
"""
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent


def _run(cwd: Path, snippet: str) -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-c", "import warnings; warnings.filterwarnings('ignore');"
                               "import sys; sys.path.insert(0, '.')\n" + snippet],
        cwd=cwd, capture_output=True, text=True)
    return proc.returncode, (proc.stdout + proc.stderr).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("snippet", nargs="?", help="python source to run in both trees")
    ap.add_argument("-f", "--file", help="read the snippet from a file instead")
    ap.add_argument("--ref", default="HEAD", help="the BEFORE ref (default HEAD)")
    a = ap.parse_args()
    snippet = Path(a.file).read_text() if a.file else a.snippet
    if not snippet:
        ap.error("give a snippet or -f FILE")

    after_rc, after = _run(HERE, snippet)
    tmp = Path(tempfile.mkdtemp(prefix="before_after_"))
    wt = tmp / "tree"
    try:
        add = subprocess.run(["git", "worktree", "add", "--detach", str(wt), a.ref],
                             cwd=REPO, capture_output=True, text=True)
        if add.returncode != 0:
            print(f"could not create a worktree at {a.ref}:\n{add.stderr.strip()}")
            return 2
        before_rc, before = _run(wt / HERE.name, snippet)
    finally:
        subprocess.run(["git", "worktree", "remove", "--force", str(wt)],
                       cwd=REPO, capture_output=True, text=True)
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"=== BEFORE ({a.ref}) rc={before_rc} ===\n{before}")
    print(f"\n=== AFTER (working tree) rc={after_rc} ===\n{after}")
    same = (before, before_rc) == (after, after_rc)
    print("\n=== VERDICT ===")
    if same:
        print("IDENTICAL. The change does not affect this test, so this test is\n"
              "not evidence for it. Either the snippet does not exercise the\n"
              "change, or the change does nothing here. Do NOT spend calls on\n"
              "the strength of this.")
    else:
        print("DIFFERENT. The change moves this test, so the test is evidence\n"
              "about the change -- read both columns before deciding which is right.")
    return 0 if not same else 1


if __name__ == "__main__":
    raise SystemExit(main())
