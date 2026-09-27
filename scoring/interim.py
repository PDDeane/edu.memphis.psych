"""Whatever the running sweeps have finished so far, per item, side by side.

head_to_head.py is the final report and needs both columns complete. This one
reports partial state, which is what you want while a 13-hour olx sweep is in
flight. Reads the RESULT FILES, never summary.txt: sweep scripts append to that,
so it accumulates lines from earlier runs and a stale row reads exactly like a
fresh one.

    python3 interim.py                 # everything available
    python3 interim.py --handout 3     # one handout

Columns, each the mean exact-match rate over however many runs that config
stored:

  paper/O   score.py + Opus         out/h{1,2,3}            (single run)
  paper/m   score.py + gpt-5-mini   out/paper_mini/r*/h*
  python/m     shipped prompt + mini   out/cli_v7/<item>.runs.json
  olx/m     real app + mini         out/web_v6/<item>.runs.json

A blank cell means that configuration has not produced this item yet.

The completed four-way sweep, and the two bugs it exposed together with the
stored results they invalidate, are in out/SWEEP_2026-08-12.md.
"""

from __future__ import annotations

import argparse
import glob
import json
import os

from forms import FORMS, config

import paths

ROOT = os.path.dirname(os.path.abspath(__file__))


def _gold(h: int) -> dict:
    return config(h)["gold"]()


def _exact(pairs: list[tuple[float, float]]) -> float | None:
    """Fraction of (gold, pred) pairs that match exactly."""
    if not pairs:
        return None
    return sum(1 for g, p in pairs if abs(g - p) < 1e-9) / len(pairs)


def paper_run(h: int, outdir: str) -> dict[str, list[tuple[float, float]]]:
    gold = _gold(h)
    out: dict[str, list[tuple[float, float]]] = {}
    for f in sorted(glob.glob(os.path.join(outdir, "participant_*.json"))):
        rec = json.load(open(f))
        pid = rec["participant_id"]
        for it in rec.get("items", []):
            g = gold.get(pid, {}).get(it["item_id"], {}).get("score")
            if g is None or it.get("score") is None:
                continue
            out.setdefault(it["item_id"], []).append((g, it["score"]))
    return out


def paper_opus(h: int) -> dict[str, float]:
    r = paper_run(h, os.path.join(str(paths.roots().out), f"h{h}"))
    return {k: v for k, v in ((k, _exact(p)) for k, p in r.items()) if v is not None}


def paper_mini(h: int) -> dict[str, float]:
    """Mean over however many of the three runs are on disk."""
    per: dict[str, list[float]] = {}
    for d in sorted(glob.glob(os.path.join(str(paths.roots().out), "paper_mini", "r*", f"h{h}"))):
        # A run dir is seeded from out/h* so score.py's --items merge works, which
        # means a run that failed outright leaves the SEEDED records in place and
        # they read as results. That happened: every participant died on a
        # formatting bug and the Opus seed was reported as a gpt-5-mini column.
        # A log with FAILED lines is not a measurement.
        log = os.path.join(d, "score.log")
        if os.path.exists(log) and "FAILED" in open(log).read():
            continue
        for item, pairs in paper_run(h, d).items():
            e = _exact(pairs)
            if e is not None:
                per.setdefault(item, []).append(e)
    return {k: sum(v) / len(v) for k, v in per.items()}


def shipped(h: int, outdir: str, olx: bool) -> dict[str, float]:
    """Mean exact over the runs stored in each <item>.runs.json."""
    gold = _gold(h)
    items = [i["id"] for i in config(h)["rubric"].ITEMS]
    out: dict[str, float] = {}
    for item in items:
        path = os.path.join(ROOT, outdir, f"{item}.runs.json")
        if not os.path.exists(path):
            continue
        d = json.load(open(path))
        rates = []
        for run in d.get("runs", []):
            pairs = []
            for c in run.get("results", []):
                if olx:
                    if not c.get("ok"):
                        continue
                    pid = int(c["cell"].split("/")[0][1:])
                    pred = round(float(c["grader"]["score"]) * c["sheet_max"], 2)
                else:
                    pid, pred = c["participant_id"], c["score"]
                g = gold.get(pid, {}).get(item, {}).get("score")
                if g is not None and pred is not None:
                    pairs.append((g, pred))
            e = _exact(pairs)
            if e is not None:
                rates.append(e)
        if rates:
            out[item] = sum(rates) / len(rates)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--form", "--handout", type=int, default=None, choices=sorted(FORMS))
    args = ap.parse_args()

    cell = lambda v: f"{v:>6.0%}" if v is not None else "     ·"
    print(f"{'item':>5} {'paper/O':>8} {'paper/m':>8} {'python/m':>8} {'olx/m':>8}")
    print("-" * 42)
    done = {"paper/O": 0, "paper/m": 0, "python/m": 0, "olx/m": 0}
    total = 0
    for h in ([args.form] if args.form else sorted(FORMS)):
        po, pm = paper_opus(h), paper_mini(h)
        cm = shipped(h, str(paths.roots().out / "cli_v7"), olx=False)
        wm = shipped(h, str(paths.roots().out / "web_v6"), olx=True)
        for it in [i["id"] for i in config(h)["rubric"].ITEMS]:
            total += 1
            for name, src in (("paper/O", po), ("paper/m", pm),
                              ("python/m", cm), ("olx/m", wm)):
                if src.get(it) is not None:
                    done[name] += 1
            print(f"{it:>5} {cell(po.get(it))} {cell(pm.get(it))} "
                  f"{cell(cm.get(it))} {cell(wm.get(it))}")
    print("-" * 42)
    print("coverage: " + "  ".join(f"{k} {v}/{total}" for k, v in done.items()))
    print("\n· = not produced yet.  paper/O is a single run; the others are means\n"
          "over the runs on disk, so a partial olx column is a 1-run mean until\n"
          "that item's three are done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
