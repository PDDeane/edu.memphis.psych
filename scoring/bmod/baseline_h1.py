"""Compare scorer output against the graders' 20 gold rows for Handout 1.

Reports, per rubric item: n, exact-match rate, mean absolute error, and
within-tolerance rate. Tolerance defaults to the item's own smallest credit
component, because "off by one reason" is a different kind of miss on Q1
(1 pt) than on Q5 (2.5 pts).

Also prints the largest disagreements, since those are what a human needs to
look at to decide whether the scorer or the grader was right.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import statistics

from gold import load_h1
from forms import gold_ceiling, gold_divergence_cells
# The rubric through `handouts`, not the module: `config(h)["rubric"]` serves a
# view onto the course file, so this keeps working when Stage 5 deletes
# `rubric_h*`. The names below are bound from it, so every use is unchanged.
import forms as _H_RUBRIC
_RUBRIC = _H_RUBRIC.config(1)["rubric"]
BY_ID, ITEMS = _RUBRIC.BY_ID, _RUBRIC.ITEMS
from stale_check import audit as stale_audit
import paths

OUTDIR = f"{paths.roots().out}/h1"


def load_pred(outdir: str) -> dict[int, dict[str, dict]]:
    pred: dict[int, dict[str, dict]] = {}
    for f in sorted(glob.glob(os.path.join(outdir, "participant_*.json"))):
        with open(f) as fh:
            rec = json.load(fh)
        pred[rec["participant_id"]] = {i["item_id"]: i for i in rec["items"]}
    return pred


def tolerance(item_id: str) -> float:
    return min(c["pts"] for c in BY_ID[item_id]["credit"] if c.get("pts") is not None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--outdir", default=OUTDIR)
    ap.add_argument(
        "--exclude",
        type=int,
        nargs="*",
        default=None,
        help="Participant ids to drop — use for any whose responses appear as "
        "few-shot exemplars in the rubric, so the score is not self-graded.",
    )
    args = ap.parse_args()

    gold = load_h1()
    if args.exclude:
        gold = {k: v for k, v in gold.items() if k not in set(args.exclude)}
        print(f"(excluding participants {sorted(args.exclude)} — used as exemplars)\n")
    pred = load_pred(args.outdir)
    if not pred:
        print(f"no predictions in {args.outdir}")
        return 1

    pids = sorted(set(gold) & set(pred))
    print(f"Handout 1 baseline — {len(pids)} participants with both gold and predictions\n")

    # Same tripwire baseline.py carries: these predictions are files on disk, and
    # a rubric edit since they were written makes the rates below describe a
    # rubric that no longer exists.
    stale, _, _ = stale_audit(1)
    if stale:
        items = sorted({ln.split()[0] for ln in stale})
        print(f"!! STALE PREDICTIONS — {', '.join(items)} were scored by an "
              f"older rubric.\n"
              f"!! Details: python3 stale_check.py --handout 1\n"
              f"!! Refresh: python3 score.py --handout 1 "
              f"--items {' '.join(items)}\n")

    hdr = (
        f"{'item':>5} {'max':>5} {'n':>3} {'dvg':>4} {'exact':>7} {'±tol':>7} "
        f"{'MAE':>6} {'bias':>7} {'esc':>4}"
    )
    print(hdr)
    print("-" * len(hdr))

    # Cells this scorer disagrees with a grader on PURPOSE, and the items where
    # gold does not decide consistently. baseline.py gained both; this entry point
    # is separate and did not, so it counted all nine declared cells as errors —
    # on handout 1 that is five of them, three on Q4a alone, which reads as the
    # weakest item here and is among the strongest once they come out.
    dvg = gold_divergence_cells()

    all_err, all_abs = [], []
    adj_err = []
    per_item_rows = []
    disagreements = []
    adjusted_items = []

    for item in ITEMS:
        iid = item["id"]
        tol = tolerance(iid)
        errs, exact, within, esc, n = [], 0, 0, 0, 0
        aerrs, aexact = [], 0
        for pid in pids:
            g = gold[pid].get(iid, {}).get("score")
            p = pred[pid].get(iid, {}).get("score")
            if pred[pid].get(iid, {}).get("escalate"):
                esc += 1
            if g is None or p is None:
                continue
            n += 1
            e = p - g
            errs.append(e)
            all_err.append(e)
            all_abs.append(abs(e))
            if abs(e) < 1e-9:
                exact += 1
            if abs(e) <= tol + 1e-9:
                within += 1
            if abs(e) > tol + 1e-9:
                disagreements.append((abs(e), pid, iid, g, p, dvg.get((iid, pid))))
            if (iid, pid) not in dvg:
                aerrs.append(e)
                adj_err.append(e)
                aexact += abs(e) < 1e-9
        if not n:
            continue
        nd = sum(1 for pid in pids if (iid, pid) in dvg)
        mae = statistics.mean(abs(e) for e in errs)
        bias = statistics.mean(errs)
        per_item_rows.append((iid, exact / n, within / n, mae))
        if nd and aerrs:
            adjusted_items.append((iid, len(aerrs), nd, aexact / len(aerrs),
                                   statistics.mean(abs(e) for e in aerrs),
                                   statistics.mean(aerrs)))
        print(
            f"{iid:>5} {item['max']:>5.0f} {n:>3} {(str(nd) if nd else ''):>4} "
            f"{exact/n:>6.0%} {within/n:>6.0%} "
            f"{mae:>6.2f} {bias:>+7.2f} {esc:>4}"
        )

    print("-" * len(hdr))
    n_all = len(all_abs)
    print(
        f"{'ALL':>5} {'':>5} {n_all:>3} {'':>4} "
        f"{sum(1 for e in all_err if abs(e)<1e-9)/n_all:>6.0%} "
        f"{'':>6} {statistics.mean(all_abs):>6.2f} "
        f"{statistics.mean(all_err):>+7.2f}"
    )
    if adjusted_items:
        n_adj = len(adj_err)
        print(
            f"{'ALL*':>5} {'':>5} {n_adj:>3} {'':>4} "
            f"{sum(1 for e in adj_err if abs(e)<1e-9)/n_adj:>6.0%} "
            f"{'':>6} {statistics.mean(map(abs, adj_err)):>6.2f} "
            f"{statistics.mean(adj_err):>+7.2f}"
        )
        print("\n* declared divergences from gold subtracted "
              "(handouts.GOLD_DIVERGENCES — decisions, not defects):")
        for iid, na, nd, ex, mae, bias in adjusted_items:
            codes = ",".join(sorted({dvg[(iid, pp)] for pp in pids if (iid, pp) in dvg}))
            print(f"  {iid:>5}  n={na:<3} -{nd} cell(s)  exact {ex:>4.0%}  "
                  f"MAE {mae:.2f}  bias {bias:+.2f}   {codes}")

    ceil = [(i["id"], gold_ceiling(1, i["id"])) for i in ITEMS if gold_ceiling(1, i["id"])]
    if ceil:
        print("\nMeasurement ceilings — gold does not decide these consistently "
              "(handouts.GOLD_CEILINGS):")
        # One line per ceiling, not per item: Q2 has two for unrelated reasons
        # and printing only the first would hide the other.
        for iid, whys in ceil:
            for n, why in enumerate(whys):
                print(f"  {iid if n == 0 else '':>5}  {why.split('. ')[0]}.")

    # Participant-total agreement — what a gradebook actually sees.
    tot_err = []
    for pid in pids:
        g_items = [
            (gold[pid][i]["score"], pred[pid].get(i, {}).get("score"))
            for i in BY_ID
            if gold[pid].get(i, {}).get("score") is not None
        ]
        if any(p is None for _, p in g_items):
            continue
        tot_err.append(sum(p for _, p in g_items) - sum(g for g, _ in g_items))
    if tot_err:
        print(
            f"\nParticipant totals (out of 45, n={len(tot_err)}): "
            f"MAE {statistics.mean(abs(e) for e in tot_err):.2f} pts, "
            f"bias {statistics.mean(tot_err):+.2f}, "
            f"within 2 pts {sum(1 for e in tot_err if abs(e)<=2)/len(tot_err):.0%}"
        )

    if disagreements:
        print("\nLargest disagreements (|error| beyond item tolerance):")
        print("  DECLARED ones are deliberate — do not chase them as bugs.")
        for d, pid, iid, g, p, code in sorted(disagreements, reverse=True,
                                              key=lambda t: t[0])[:12]:
            fb = gold[pid][iid]["feedback"].replace("\n", " ")[:88]
            tag = f"  [DECLARED {code}]" if code else ""
            print(f"  p{pid:<3} {iid:<4} gold {g:>5.2f} -> pred {p:>5.2f} "
                  f"({p-g:+.2f})  gold said: {fb}{tag}")

    missing = [
        (pid, i)
        for pid in pids
        for i in BY_ID
        if pred[pid].get(i, {}).get("score") is None
    ]
    if missing:
        print(f"\nUnscored (backend errors): {len(missing)} -> {missing}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
