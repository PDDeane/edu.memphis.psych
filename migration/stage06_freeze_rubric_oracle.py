#!/usr/bin/env python3
"""Freeze what the rubric MODULES say, so equivalence survives their deletion.

THE PROBLEM THIS SOLVES. `dual` mode proves the rubric object and `rubric_hN.py`
agree by COMPARING them, so the obvious reading is that 6c's delete ends the
check: no modules, no left-hand side. That reading is wrong, and acting on it
would have thrown away the migration's only proof of faithfulness at the moment
it mattered most.

THE ANSWER IS THE ONE STAGE 00 ALREADY USED. `prompt_oracles.json` froze what
the old generator produced BEFORE anything changed, and every stage since has
compared against it rather than against a live copy of the old generator. The
rubric gets the same treatment: freeze the modules' full data here, and
`differences()` compares the object against the FROZEN READING forever.

IT IS STRONGER THAN THE LIVE COMPARISON, not a degraded substitute:

  * the live check asks "do these two CURRENT sources agree" -- available only
    while both exist, and silent about drift that moves both;
  * the oracle asks "does the object still say what the modules said ON THE DAY
    THEY WERE DELETED" -- available forever, and it catches later drift in the
    emitter, the reader or the .olx that no live comparison could see, because
    after 6c there is no second source to drift away from.

RE-BASELINING IS A DELIBERATE ACT. When the rubric legitimately changes, this
oracle goes stale and must be re-frozen with a reason, exactly as DESIGNED_TEXT
and the prompt oracles are. A stale oracle is a loud failure; a deleted one is a
silent success, which is the trade this file exists to refuse.
"""
import argparse
import json
import os
import sys
from pathlib import Path

DERIVED = ("MAPS", "OC_GATES", "FORBID", "SLOT_OPTIONS", "REQUIRED_MOVE",
           "SHARED_GUIDANCE")


def freeze(scoring: Path) -> dict:
    sys.path.insert(0, str(scoring))
    # THE MODULES, not whatever `handouts` is serving. Freezing the object would
    # record the object agreeing with itself.
    os.environ["RUBRIC_SOURCE"] = "module"
    import handouts as H
    out = {"_note": "What rubric_h{1,2,3}.py said when stage 06c deleted them. "
                    "Equivalence is checked against THIS, not against a live "
                    "module. Re-freeze only with a stated reason.",
           "handouts": {}}
    for h in (1, 2, 3):
        rub = H.config(h)["rubric"]
        rub = getattr(rub, "_module", rub)
        entry = {
            "ITEMS": rub.ITEMS,
            "SLOT_SPEC": getattr(rub, "SLOT_SPEC", {}) or {},
        }
        for name in DERIVED:
            v = getattr(rub, name, None)
            if v is not None:
                entry[name] = list(v) if isinstance(v, tuple) else v
        # every module-level selector, by name
        import re as _re
        entry["SELECTORS"] = {
            n: list(v) for n, v in vars(rub).items()
            if _re.fullmatch(r"[A-Z][A-Z0-9_]*_ITEMS", n) and isinstance(v, tuple)}
        out["handouts"][str(h)] = entry
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scoring", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    data = freeze(a.scoring)
    n_items = sum(len(d["ITEMS"]) for d in data["handouts"].values())
    text = json.dumps(data, indent=1, ensure_ascii=False, sort_keys=True) + "\n"
    print(f"froze {n_items} item(s) across 3 handout(s), {len(text)} chars")
    for h, d in data["handouts"].items():
        print(f"   h{h}: {len(d['ITEMS'])} items, {len(d.get('SELECTORS', {}))} selector(s), "
              f"{sum(1 for k in DERIVED if k in d)} derived table(s)")
    if not a.write:
        print("\n(dry run; pass --write)")
        return 0
    if a.out.exists():
        print(f"\nREFUSED: {a.out.name} already exists. Re-freezing is a "
              f"DELIBERATE act -- move the old one aside with a reason first.")
        return 1
    a.out.write_text(text)
    print(f"\nwrote {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
