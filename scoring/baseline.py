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

import handouts as _handouts
from handouts import (HANDOUTS, config, exemplar_drops, gold_ceiling,
                      gold_divergence_cells, suspect)
from stale_check import audit as stale_audit


def load_pred(outdir: str) -> dict[int, dict[str, dict]]:
    pred: dict[int, dict[str, dict]] = {}
    for f in sorted(glob.glob(os.path.join(outdir, "participant_*.json"))):
        with open(f) as fh:
            rec = json.load(fh)
        pred[rec["participant_id"]] = {i["item_id"]: i for i in rec["items"]}
    return pred


def provenance(outdir: str) -> tuple[set, set]:
    """(backend names, supports_tools flags) recorded in a results directory.

    Read from the record rather than the items, because that is where score.py
    stamps it. Empty flags mean the directory predates the stamp — the caller
    must not read that as "tools were available".
    """
    names, tools = set(), set()
    for f in sorted(glob.glob(os.path.join(outdir, "participant_*.json"))):
        with open(f) as fh:
            rec = json.load(fh)
        if rec.get("backend"):
            names.add(rec["backend"])
        if "supports_tools" in rec:
            tools.add(bool(rec["supports_tools"]))
    return names, tools


def tolerance(item_id: str) -> float:
    # Skips components that carry no points: a reported-only slot exists so a
    # later check can use it, and a gating one costs the whole item.
    return min(c["pts"] for c in BY_ID[item_id]["credit"]
               if c.get("pts") is not None)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--handout", type=int, default=1, choices=sorted(HANDOUTS))
    ap.add_argument("--outdir", default=None)
    ap.add_argument("--tools", choices=["auto", "yes", "no"], default="auto",
                    help="Did the backend that produced these predictions have "
                         "image tools? `auto` reads the stamp score.py writes and "
                         "assumes NO when there is none, because an unstamped "
                         "directory that scored a graph item blind is "
                         "indistinguishable from one that did not. Use `yes` only "
                         "when you know how the directory was produced.")
    ap.add_argument(
        "--exclude",
        type=int,
        nargs="*",
        default=None,
        help="Participant ids to drop — use for any whose responses appear as "
        "few-shot exemplars in the rubric, so the score is not self-graded.",
    )
    args = ap.parse_args()

    cfg = config(args.handout)
    global BY_ID, ITEMS
    BY_ID, ITEMS = cfg["rubric"].BY_ID, cfg["rubric"].ITEMS
    args.outdir = args.outdir or cfg["outdir"]
    # Two DIFFERENT exclusions, and conflating them threw away real evidence.
    # A mis-transcribed participant cannot be attributed on ANY item, so it goes
    # globally. A few-shot exemplar is a property of ONE PROMPT: p6/p8/p10 appear
    # in Q6's prompt, so scoring them on Q6 is self-grading, while scoring them
    # on Q1 is not. This used to call excluded(), which drops both kinds from
    # every item — 3 participants x 7 items = 21 cells of handout-1 evidence
    # discarded, and it made this tool's n disagree with agreement.py's, which
    # has used per-item drops for a while. See handouts.exemplar_drops().
    # score.py already runs every participant, so nothing has to be re-run for
    # this: the predictions for excluded cells are on disk and were simply never
    # read. They are now read and reported separately, never counted.
    if args.exclude is None:
        args.exclude = []
    gold = cfg["gold"]()
    if args.exclude:
        gold = {k: v for k, v in gold.items() if k not in set(args.exclude)}
        print(f"(excluding participants {sorted(args.exclude)} — mis-transcribed, "
              f"not attributable on any item)\n")
    # The SAME source the web and CLI harnesses read. This used to be
    # exemplar_drops() alone, with no equivalent of PER_ITEM_EXCLUDE at all —
    # so the paper scorer counted five cells (1c p4/p19/p20, Q4c p16, Q6 p9)
    # that both other harnesses drop as unreachable, and its headline rate was
    # computed over a different denominator from the numbers it was compared
    # against.
    # A whole ITEM the producing backend could not score. Distinct from the
    # per-cell exclusions below: those drop cells from an item that is otherwise
    # measurable, this says the item's number means nothing from this source.
    backends_seen, tools = provenance(args.outdir)
    if args.tools != "auto":
        tools = {args.tools == "yes"}
        print(f"(--tools {args.tools}: taking image-tool support as "
              f"{args.tools == 'yes'} on the operator's word)\n")
    if tools == {True}:
        not_comparable = {}
    elif tools == {False}:
        not_comparable = _handouts.not_comparable_items(args.handout, False)
    else:
        # Older outputs predate the provenance field. Assume the worst and say so,
        # rather than silently reporting a number that may be a missing tool.
        not_comparable = _handouts.not_comparable_items(args.handout, False)
        if not_comparable:
            print(f"!! predictions do not record which backend made them "
                  f"({sorted(x for x in backends_seen if x) or 'unrecorded'}). "
                  f"Treating {sorted(not_comparable)} as not comparable — re-score "
                  f"to remove the doubt.\n")

    per_item_excl = {it["id"]: _handouts.cell_exclusions(args.handout, it["id"])
                     for it in ITEMS}
    per_item_drop = {k: sorted(v) for k, v in per_item_excl.items() if v}
    if per_item_drop:
        shown = ", ".join(f"{k}: {sorted(v)}" for k, v in sorted(per_item_drop.items()))
        print(f"(excluding per item, few-shot exemplars in that item's own prompt — "
              f"{shown})\n")
    pred = load_pred(args.outdir)
    if not pred:
        print(f"no predictions in {args.outdir}")
        return 1

    pids = sorted(set(gold) & set(pred))
    print(f"Handout {args.handout} baseline — {len(pids)} participants with both gold and predictions\n")

    # These predictions are files on disk, not something this run computed, so a
    # rubric edit since they were written makes every number below describe a
    # rubric that no longer exists. That is not hypothetical: all three handouts
    # sat stale for five days, handout 2 with six slots its rubric had dropped.
    # Warn rather than exit — printing the numbers is the point of this tool, and
    # a stale comparison is still worth seeing once it is labelled as one.
    stale, _, _ = stale_audit(args.handout, args.outdir)
    if stale:
        items = sorted({ln.split()[0] for ln in stale})
        print(f"!! STALE PREDICTIONS — {', '.join(items)} were scored by an "
              f"older rubric.\n"
              f"!! The rates below are not measurements of the current one. "
              f"Details: python3 stale_check.py --handout {args.handout}\n"
              f"!! Refresh: python3 score.py --handout {args.handout} "
              f"--items {' '.join(items)}\n")

    # Cells where this scorer disagrees with a grader ON PURPOSE, because the
    # graders applied their own written rule inconsistently. Reported both ways:
    # the raw rate is what a student's score depends on, the adjusted one is what
    # says whether the scorer judges well. Nine such cells exist and every one of
    # them was counted as an error here until now — which is a real distortion,
    # not a rounding one: on handout 1, Q4a carries three of them.
    dvg = gold_divergence_cells()

    hdr = (
        f"{'item':>5} {'max':>5} {'n':>3} {'dvg':>4} {'exact':>7} {'±tol':>7} "
        f"{'MAE':>6} {'bias':>7} {'esc':>4}"
    )
    print(hdr)
    print("-" * len(hdr))

    all_err, all_abs = [], []
    not_counted: list[tuple] = []
    adj_err = []                       # declared divergences removed
    per_item_rows = []
    disagreements = []
    adjusted_items = []

    for item in ITEMS:
        iid = item["id"]
        if iid in not_comparable:
            continue                  # reported below, never counted
        tol = tolerance(iid)
        errs, exact, within, esc, n = [], 0, 0, 0, 0
        aerrs, aexact = [], 0
        skip = per_item_excl.get(iid, {})
        for pid in pids:
            if pid in skip:
                g = gold[pid].get(iid, {}).get("score")
                p = pred[pid].get(iid, {}).get("score")
                if g is not None and p is not None:
                    not_counted.append((skip[pid][0], iid, pid, g, p))
                continue
            g = gold[pid].get(iid, {}).get("score")
            p = pred[pid].get(iid, {}).get("score")
            if pred[pid].get(iid, {}).get("escalate"):
                esc += 1
            if g is None or p is None:
                continue
            n += 1
            e = p - g
            # Exact, or the nearest reachable score where gold names one the item
            # cannot produce — see handouts.scores_as_exact.
            hit = _handouts.scores_as_exact(item, g, p)
            errs.append(e)
            all_err.append(e)
            all_abs.append(abs(e))
            if hit:
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
        nd = sum(1 for pid in pids if pid not in skip and (iid, pid) in dvg)
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
            codes = ",".join(sorted({dvg[(iid, p)] for p in pids
                                     if (iid, p) in dvg}))
            print(f"  {iid:>5}  n={na:<3} -{nd} cell(s)  exact {ex:>4.0%}  "
                  f"MAE {mae:.2f}  bias {bias:+.2f}   {codes}")

    ceil = [(i["id"], gold_ceiling(args.handout, i["id"])) for i in ITEMS
            if gold_ceiling(args.handout, i["id"])]
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
    any_drop = {pid for v in per_item_drop.values() for pid in v}
    for pid in pids:
        if pid in any_drop:
            continue          # an incomplete total is not a gradebook total
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
            f"\nParticipant totals (out of {sum(i['max'] for i in ITEMS):g}, n={len(tot_err)}): "
            f"MAE {statistics.mean(abs(e) for e in tot_err):.2f} pts, "
            f"bias {statistics.mean(tot_err):+.2f}, "
            f"within 2 pts {sum(1 for e in tot_err if abs(e)<=2)/len(tot_err):.0%}"
        )

    if not_comparable:
        print("\nNOT COMPARABLE — excluded entirely, not a score:")
        for iid, why in sorted(not_comparable.items()):
            print(f"  {iid}: {why}")

    if not_counted:
        print("\nnot counted in the rate, but scored — how they came out:")
        meaning = {
            "self_graded": "the prompt contains the answer and the grader's decision "
                           "— a miss here is evidence of a problem with the model",
            "unscoreable": "no correct scorer can reach this gold — a miss is EXPECTED",
            "suspect":     "the submission is mis-transcribed — a miss says nothing",
        }
        for kind in _handouts.EXCLUSION_KINDS:
            mine = [r for r in not_counted if r[0] == kind]
            if not mine:
                continue
            ok = sum(1 for _, _, _, g, p in mine if abs(p - g) < 1e-9)
            print(f"  {kind:<12} {ok}/{len(mine)} scored correctly — {meaning[kind]}")
            for _, iid, pid, g, p in sorted(mine, key=lambda r: (r[1], r[2])):
                if abs(p - g) >= 1e-9:
                    flag = "  <-- MISSED" if kind == "self_graded" else ""
                    print(f"      p{pid:<3} {iid:<5} gold={g:.2f} pred={p:.2f}{flag}")


    if disagreements:
        print("\nLargest disagreements (|error| beyond item tolerance):")
        print("  DECLARED ones are deliberate — do not chase them as bugs.")
        for d, pid, iid, g, p, code in sorted(disagreements, reverse=True,
                                              key=lambda t: t[0])[:12]:
            fb = gold[pid][iid]["feedback"].replace("\n", " ")[:70]
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
