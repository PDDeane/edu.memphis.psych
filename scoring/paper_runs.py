"""Fold a multi-run paper sweep into the `.runs.json` the ledger records.

score.py writes one file per (run, handout, participant) -- `rN/hM/participant_
NNN.json`, each holding an `items[]` list. measured.record and cross_path both
expect the runs shape the other two scorers emit: {"item", "runs": [{"results":
[...]}], "era": ...}. Without this the third scorer cannot be recorded at all,
which is the same gap the web side had until its reader was shared.

One file per ITEM, matching sweep_cli.sh and sweep_app.sh, so every downstream
tool sees the three scorers the same way.

    python3 paper_runs.py <sweep_dir> <out_dir> [MODEL] [BACKEND]

MODEL and BACKEND are stamped into each artifact's era. They matter here more
than anywhere else: the paper scorer is swept on gpt-5-mini (`--backend lo`)
AND on Opus (`--backend cli`/`api`), and an artifact that cannot say which one
produced it is unattributable in exactly the way an unstamped prompt is.
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys


def collect(sweep_dir: str) -> dict:
    """(item -> [run0_results, run1_results, ...]) from rN/hM/participant_*.json."""
    runs: dict[str, dict[int, list]] = {}
    pat = re.compile(r"(?:^|/)r(\d+)/h\d+/participant_(\d+)\.json$")
    for f in sorted(glob.glob(os.path.join(sweep_dir, "r*", "h*", "participant_*.json"))):
        m = pat.search(f)
        if not m:
            continue
        run = int(m.group(1))
        try:
            doc = json.load(open(f))
        except Exception:
            continue
        pid = doc.get("participant_id")
        for it in doc.get("items") or []:
            entry = dict(it)
            # The participant lives on the FILE, not the item, so it is carried
            # onto each entry -- cross_path.result_cell reads it from `_pid`.
            entry["_pid"] = pid
            runs.setdefault(it.get("item_id"), {}).setdefault(run, []).append(entry)
    return runs


def write(sweep_dir: str, out_dir: str, model: str = "",
          backend: str = "") -> int:
    import measured

    os.makedirs(out_dir, exist_ok=True)
    runs = collect(sweep_dir)
    if not runs:
        print(f"no paper artifacts under {sweep_dir}", file=sys.stderr)
        return 1
    for item, by_run in sorted(runs.items()):
        if not item:
            continue
        doc = {
            "item": item,
            # Stamped like every other artifact, so an era mismatch is catchable
            # rather than inferred from file dates.
            "era": (measured.era_stamp([item], model=model or None,
                                       backend=backend or None)
                    if item in measured._jobs() else {}),
            "runs": [{"run": r, "results": by_run[r]} for r in sorted(by_run)],
        }
        with open(os.path.join(out_dir, f"{item}.runs.json"), "w") as fh:
            json.dump(doc, fh)
        print(f"  {item:6} {len(by_run)} run(s), "
              f"{sum(len(v) for v in by_run.values())} cell(s)")
    return 0


if __name__ == "__main__":
    if not 3 <= len(sys.argv) <= 5:
        raise SystemExit(__doc__)
    raise SystemExit(write(*sys.argv[1:]))
