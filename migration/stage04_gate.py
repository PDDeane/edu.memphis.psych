#!/usr/bin/env python3
"""Stage 04 · the gate. The rubric data moved, and moved without changing.

THREE CLAUSES FROM THE PLAN:

  * ALL 26 BYTE-EQUAL. Every item still assembles to exactly what ships today,
    with its item-level data read from the emitted rubric rather than from the
    Python modules. 23 of the 26 have a prompt body at all -- `T1`, `T2` and
    `1b` are scored deterministically from the fixture and have no `LLMAction` --
    so the figure to look for is 23 assembled and 26 read.
  * A SECOND RUN REPORTS NO EDITS. Not a nicety: a generator whose output drifts
    run to run cannot be trusted to have written what it read, and the usual
    drift is ORDERING, which no single-run byte comparison would catch.
  * `DEFINITIONS.json` ACCEPTS ARE EXPLICIT. The inventory exists to catch a
    VANISHED definition, so what the gate checks is that nothing it lists has
    gone. It deliberately does NOT check that every new name was added: bulk
    agreement with the tree is what the file's own README refuses, because an
    inventory that agrees with whatever it finds enforces nothing.

AND ONE THE PLAN IMPLIES: the emitted rubric must PARSE. All three clauses can
pass while the rubric is unreadable by anything but this gate's own reader.
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

PASS, FAIL, NOTE = "PASS", "FAIL", "NOTE"
HERE = Path(__file__).parent


def sh(cmd, cwd, timeout=1800):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, r.stdout + r.stderr


def run_probe(lo: Path, name: str):
    src = HERE / "verify" / name
    if not src.exists():
        return "", f"{name} missing from migration/verify"
    dest = lo / "packages/shared/lib" / name
    dest.write_text(src.read_text())
    try:
        rc, out = sh(["npx", "vitest", "run", str(dest.relative_to(lo)),
                      "--reporter=basic"], lo)
    finally:
        dest.unlink(missing_ok=True)
    return out, None


def check_assembly(lo: Path):
    out, err = run_probe(lo, "all26_from_rubric.test.ts")
    if err:
        return FAIL, err
    eq = re.search(r"BYTE_EQUAL=(\d+)/(\d+)", out)
    read = re.search(r"ITEMS_READ=(\d+)", out)
    errs = re.search(r"PARSE_ERRORS=(\d+)", out)
    if not eq or not read:
        return FAIL, "no result: " + out.strip()[-160:]
    ok = eq.group(1) == eq.group(2) and read.group(1) == "26" and errs.group(1) == "0"
    return (PASS if ok else FAIL,
            f"{eq.group(1)}/{eq.group(2)} byte-equal, {read.group(1)} item(s) read, "
            f"{errs.group(1)} parse error(s)")


def check_idempotent(scoring: Path, content: Path):
    """Run the migration twice; the second must write nothing."""
    cmd = [sys.executable, str(HERE / "stage04_migrate_rubric.py"),
           "--scoring", str(scoring), "--out", str(content), "--write"]
    sh(cmd, HERE)                       # first, to settle any pending change
    rc, out = sh(cmd, HERE)             # second, the one that must be quiet
    # The emitter reports one file and the superseded count, not "N identical".
    m = re.search(r"wrote (\d+) file\(s\); removed (\d+) superseded file\(s\)", out)
    if not m:
        return FAIL, "no result: " + out.strip()[-160:]
    quiet = m.group(1) == "0" and m.group(2) == "0"
    return (PASS if quiet else FAIL,
            f"second run wrote {m.group(1)}, removed {m.group(2)} superseded")


def check_definitions(scoring: Path):
    code = (
        "import json, sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, '.')\n"
        "import editguard\n"
        "inv = json.loads(Path('DEFINITIONS.json').read_text())['modules']\n"
        "gone = []\n"
        "for mod, names in inv.items():\n"
        "    p = Path(mod)\n"
        "    if not p.exists():\n"
        "        gone.append(mod + ': FILE GONE'); continue\n"
        "    have = editguard.definitions(p.read_text())\n"
        "    gone += [mod + ': ' + n for n in sorted(set(names) - have)]\n"
        "print('GONE=' + str(len(gone)))\n"
        "for g in gone[:6]: print('  ' + g)\n")
    rc, out = sh([sys.executable, "-c", code], scoring)
    m = re.search(r"GONE=(\d+)", out)
    if not m:
        return FAIL, "could not read the inventory: " + out.strip()[-140:]
    n = int(m.group(1))
    return (PASS if n == 0 else FAIL,
            "no listed definition has vanished" if n == 0
            else f"{n} listed definition(s) absent from the tree")


def note_unlisted(scoring: Path):
    """Names present but unlisted, and modules present but UNWATCHED.

    ITERATES THE FILES ON DISK, NOT THE INVENTORY'S KEYS. The first version
    walked `DEFINITIONS.json` and counted unlisted names inside each module it
    named -- so a module with NO entry at all contributed zero, and read as
    clean. It is not clean, it is unwatched: `check_no_definition_vanished`
    iterates the same inventory, so every name in such a file can disappear
    without anything noticing. Found 2026-09-14 accounting for a two-name
    discrepancy; `faithful_probe.py` had no entry and two invisible names.
    """
    code = (
        "import json, sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, '.')\n"
        "import editguard\n"
        "inv = json.loads(Path('DEFINITIONS.json').read_text())['modules']\n"
        "n = 0\n"
        "unwatched = []\n"
        "for p in sorted(Path('.').glob('*.py')):\n"
        "    names = inv.get(p.name)\n"
        "    if names is None:\n"
        "        unwatched.append(p.name)\n"
        "    n += len(editguard.definitions(p.read_text()) - set(names or []))\n"
        "print('UNLISTED=' + str(n))\n"
        "print('UNWATCHED=' + ','.join(unwatched))\n")
    rc, out = sh([sys.executable, "-c", code], scoring)
    m = re.search(r"UNLISTED=(\d+)", out)
    u = re.search(r"UNWATCHED=(.*)", out)
    unwatched = [x for x in (u.group(1).split(",") if u else []) if x]
    if unwatched:
        return FAIL, (f"{len(unwatched)} module(s) have NO inventory entry and are "
                      f"therefore unwatched, not clean: {', '.join(unwatched[:5])}")
    return NOTE, (f"{m.group(1)} name(s) present but unlisted — pre-existing drift, "
                  f"accepted ONE AT A TIME or not at all" if m else "unknown")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--lo-blocks", required=True)
    ap.add_argument("--scoring", required=True)
    ap.add_argument("--content", required=True)
    a = ap.parse_args()
    lo, scoring, content = Path(a.lo_blocks), Path(a.scoring), Path(a.content)
    rows = [
        ("all items byte-equal, assembled from the emitted rubric", *check_assembly(lo)),
        ("a second migration run reports no edits", *check_idempotent(scoring, content)),
        ("no listed definition has vanished (DEFINITIONS.json)", *check_definitions(scoring)),
        ("unlisted names", *note_unlisted(scoring)),
    ]
    w = max(len(r[0]) for r in rows)
    print("\nSTAGE 04 GATE\n" + "=" * (w + 12))
    for name, verdict, detail in rows:
        print(f"{verdict:<8}{name:<{w}}  {detail}")
    print("=" * (w + 12))
    failed = [r[0] for r in rows if r[1] == FAIL]
    print("\nGATE MET." if not failed else f"\nGATE NOT MET - {len(failed)} failing")
    for f in failed:
        print("   ", f)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
