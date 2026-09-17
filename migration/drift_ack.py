"""Record that a stage's scripts have been read against the CURRENT DRIFT.md.

WHY A LEDGER AND NOT A HABIT. The dry run's scripts were written against the
tree as it stood on 2026-09-13. Every one of them still RUNS against today's
tree; several would run and be wrong, because what they compare against moved.
That failure is silent, so it needs a gate rather than an intention.

The acknowledgement is bound to the SHA of DRIFT.md. Edit DRIFT.md -- because
the tree drifted again -- and every acknowledgement lapses, which is the point:
a stage reviewed against last week's drift has not been reviewed.

    python3 migration/drift_ack.py 04 "re-froze oracles; refs now in the slice"
    python3 migration/drift_ack.py --list
"""
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import migration_paths as MP

LEDGER = MP.MIGRATION / "STAGE_DRIFT_ACK.json"
STAGES = ("00", "01", "02", "03a", "03b", "04", "05", "06", "07", "08")


def drift_sha() -> str:
    p = MP.MIGRATION / "DRIFT.md"
    if not p.exists():
        raise SystemExit("REFUSING: migration/DRIFT.md does not exist")
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def load() -> dict:
    return json.loads(LEDGER.read_text()) if LEDGER.exists() else {"stages": {}}


def stale(led: dict, sha: str) -> list[str]:
    """Stages with no acknowledgement, or one bound to an older DRIFT.md."""
    return [s for s in STAGES
            if led.get("stages", {}).get(s, {}).get("drift_sha") != sha]


def main() -> int:
    sha = drift_sha()
    led = load()
    if "--list" in sys.argv:
        print(f"  DRIFT.md sha: {sha}")
        for s in STAGES:
            e = led.get("stages", {}).get(s)
            ok = e and e.get("drift_sha") == sha
            print(f"  {'OK   ' if ok else 'STALE'} stage {s:<3} "
                  f"{(e or {}).get('note', '(never acknowledged)')[:70]}")
        return 0
    if len(sys.argv) < 3:
        raise SystemExit("usage: drift_ack.py <stage> <note>   |   --list")
    stage, note = sys.argv[1], " ".join(sys.argv[2:])
    if stage not in STAGES:
        raise SystemExit(f"REFUSING: unknown stage {stage!r}; expected one of {STAGES}")
    who = subprocess.run(["git", "config", "user.email"], capture_output=True,
                         text=True).stdout.strip() or "unknown"
    led.setdefault("stages", {})[stage] = {
        "drift_sha": sha, "note": note, "by": who,
        "at": time.strftime("%Y-%m-%d %H:%M"),
    }
    LEDGER.write_text(json.dumps(led, indent=1, sort_keys=True) + "\n")
    print(f"  stage {stage} acknowledged against DRIFT.md {sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
