"""Which cells did a scorer get wrong when its prompt already held the answer?

A `self_graded` cell is one whose participant is cited by number in that item's
own prompt, together with a quote of their response and the grader's decision —
"falling asleep in the car ... cost participant 20 three points". Those cells are
kept out of every reported rate, because scoring them measures recall.

They are still RUN, and that is the point of this tool. A miss on a self-graded
cell is the sharpest signal in the corpus:

    the rule was written down, the answer was written down beside it, the
    student's own words were quoted — and the scorer still got it wrong.

That is not a hard-judgement case. It is the rubric text failing to reach the
model, or the sheet being unable to express the decision the rule asks for.

Read the CONSENSUS section first. A cell every scorer misses cannot be blamed on
a model: four scorers, two prompts and two model families all failing the same
cell means the guidance does not say what its author thinks it says. A cell only
one scorer misses is a capability difference and belongs in the model column.

    python3 self_graded_misses.py                     # every sweep it can find
    python3 self_graded_misses.py --item Q4b          # one item, with evidence
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys

from handouts import config, cell_exclusions, gold_divergence_cells
import paths

OUT = os.path.join(os.path.dirname(paths.__file__), "..")
DATA = str(paths.OUT)

# label -> (kind, path). `paper` dirs hold participant_*.json per handout;
# `sweep` dirs hold <item>.json. Missing ones are skipped, so this runs against
# whatever has finished.
SOURCES = [
    ("olx",        "sweep", f"{DATA}/web_v9"),
    ("python",     "sweep", f"{DATA}/cli_v8"),
    ("paper+mini", "paper", f"{DATA}/paper_mini_v8/r1"),
    ("paper+opus", "paper", f"{DATA}/paper_opus_v8/r1"),
]


def _num(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    v = x.get("score")
    return float(v) if isinstance(v, (int, float)) else None


def gold_for(handout: int) -> dict:
    g = config(handout)["gold"]()
    if handout == 3:
        try:
            from agreement import rebuild_declared_gold
            g, _ = rebuild_declared_gold(g)
        except Exception:
            pass
    return g


def load_paper(root: str) -> dict[tuple[str, int], float]:
    """{(item, pid): predicted score} from a score.py output tree."""
    out = {}
    for h in (1, 2, 3):
        d = f"{root}/h{h}"
        if not os.path.isdir(d):
            continue
        for f in sorted(glob.glob(os.path.join(d, "participant_*.json"))):
            rec = json.load(open(f))
            pid = rec["participant_id"]
            for i in rec.get("items", []):
                s = _num(i)
                if s is not None:
                    out[(i["item_id"], pid)] = s
    return out


def load_sweep(root: str) -> dict[tuple[str, int], float]:
    """{(item, pid): predicted score} from a sweep directory, either harness."""
    out = {}
    for f in sorted(glob.glob(os.path.join(root, "*.json"))):
        base = os.path.basename(f)
        if base in ("idmap.json",) or base.endswith(".runs.json"):
            continue
        try:
            d = json.load(open(f))
        except Exception:
            continue
        rows = d.get("results") or []
        for r in rows:
            if "cell" in r:                       # olx
                m = re.match(r"p(\d+)/(.+)$", r["cell"])
                if not m:
                    continue
                pid, iid = int(m.group(1)), m.group(2)
                frac = (r.get("grader") or {}).get("score")
                if frac is None or r.get("sheet_max") is None:
                    continue
                out[(iid, pid)] = round(float(frac) * float(r["sheet_max"]), 2)
            elif "participant_id" in r:           # python
                s = _num(r)
                if s is not None:
                    out[(r["item"], r["participant_id"])] = s
    return out


def self_graded_cells() -> dict[tuple[str, int], int]:
    """{(item, pid): handout} for every registered self-graded cell."""
    out = {}
    for h in (1, 2, 3):
        for it in config(h)["rubric"].ITEMS:
            for pid, (kind, _why) in cell_exclusions(h, it["id"]).items():
                if kind == "self_graded":
                    out[(it["id"], pid)] = h
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--item", help="Only this item, with per-cell detail.")
    args = ap.parse_args()

    cells = self_graded_cells()
    if args.item:
        cells = {k: v for k, v in cells.items() if k[0] == args.item}
    if not cells:
        print("no self-graded cells registered for that item")
        return 1

    golds = {h: gold_for(h) for h in {v for v in cells.values()}}
    preds, missing = {}, []
    for label, kind, path in SOURCES:
        if not os.path.isdir(path):
            missing.append(label)
            continue
        preds[label] = load_paper(path) if kind == "paper" else load_sweep(path)
    if missing:
        print(f"(not yet available, skipped: {', '.join(missing)})\n")
    if not preds:
        print("no sweep output found")
        return 1

    # ── per scorer, per item ────────────────────────────────────────────────
    labels = [l for l, _, _ in SOURCES if l in preds]
    declared = gold_divergence_cells()
    items = sorted({k[0] for k in cells}, key=lambda x: (len(x), x))
    print("SELF-GRADED CELLS — scored right / run, per scorer")
    print("(the prompt names the participant, quotes their answer, and states "
          "the grader's decision)\n")
    print(f"{'item':6s} " + " ".join(f"{l:>11s}" for l in labels))
    print("-" * (7 + 12 * len(labels)))
    flagged = []
    for iid in items:
        row, worst = [], 0
        for l in labels:
            ks = [k for k in cells if k[0] == iid and k in preds[l]]
            # `(gold or -1)` was here, and 0.0 is falsy: every cell whose gold
            # is a legitimate ZERO became -1 and counted as a miss. 1a reported
            # 1/3 where it scores 3/3, because two of its three cells are gold 0
            # — and a gold of 0 is common exactly where a scorer must recognise
            # that an answer earns nothing, which is the case worth measuring.
            def _hit(k):
                g = _num(golds[cells[k]].get(k[1], {}).get(iid))
                return g is not None and abs(g - preds[l][k]) < 1e-9
            ok = sum(1 for k in ks if _hit(k) or k in declared)
            row.append(f"{ok}/{len(ks)}" if ks else "-")
            if ks and ok < len(ks):
                worst = max(worst, len(ks) - ok)
        if worst:
            flagged.append(iid)
        print(f"{iid:6s} " + " ".join(f"{c:>11s}" for c in row)
              + ("   <-- MISSES" if worst else ""))

    # Cells both implementations diverge from gold ON PURPOSE, because the
    # graders applied their own written rule inconsistently. Every scorer
    # "missing" one is the DESIGNED behaviour, so listing them as evidence that a
    # rule is not reaching the model would send a reader to rewrite guidance that
    # is working. baseline.py already prints "DECLARED ones are deliberate — do
    # not chase them as bugs"; the same applies with more force here, where the
    # whole point is that a miss means something.
    # ── consensus: missed by every scorer that ran it ───────────────────────
    print("\nCONSENSUS MISSES — every scorer that ran the cell got it wrong")
    print("A model difference cannot explain these. The rule is written down, the "
          "answer is\nwritten down beside it, and no scorer applies it: look at the "
          "guidance, not the model.\n")
    any_consensus = False
    deliberate: list[str] = []
    for (iid, pid), h in sorted(cells.items(), key=lambda kv: (len(kv[0][0]), kv[0])):
        g = _num(golds[h].get(pid, {}).get(iid))
        if g is None:
            continue
        ran = [l for l in labels if (iid, pid) in preds[l]]
        if not ran:
            continue
        wrong = [l for l in ran if abs(preds[l][(iid, pid)] - g) >= 1e-9]
        if len(wrong) == len(ran) and len(ran) > 1:
            code = declared.get((iid, pid))
            got = ", ".join(f"{l}={preds[l][(iid, pid)]:g}" for l in ran)
            if code:
                deliberate.append(f"  {iid:5s} p{pid:<3} gold={g:g}   {got}   "
                                  f"[DECLARED {code}]")
                continue
            any_consensus = True
            print(f"  {iid:5s} p{pid:<3} gold={g:g}   {got}")
    if not any_consensus:
        print("  none")
    if deliberate:
        print("\n  Deliberate, NOT evidence of anything — both implementations "
              "diverge from these\n  gold rows on purpose "
              "(handouts.GOLD_DIVERGENCES). Do not chase them:")
        for line in deliberate:
            print(line)

    # ── split misses: some scorers get it, others do not ───────────────────
    print("\nSPLIT MISSES — some scorers get it, others do not (a model/prompt "
          "difference)\n")
    any_split = False
    for (iid, pid), h in sorted(cells.items(), key=lambda kv: (len(kv[0][0]), kv[0])):
        g = _num(golds[h].get(pid, {}).get(iid))
        if g is None:
            continue
        ran = [l for l in labels if (iid, pid) in preds[l]]
        wrong = [l for l in ran if abs(preds[l][(iid, pid)] - g) >= 1e-9]
        if wrong and len(wrong) < len(ran):
            any_split = True
            got = ", ".join(f"{l}={preds[l][(iid, pid)]:g}" for l in ran)
            print(f"  {iid:5s} p{pid:<3} gold={g:g}   {got}   "
                  f"(missed by {', '.join(wrong)})")
    if not any_split:
        print("  none")

    if flagged:
        print(f"\nFLAGGED FOR ANALYSIS: {', '.join(flagged)}")
        print("Read each item's guidance beside the cells above. A scorer that "
              "cannot apply a\nrule with the answer quoted next to it is evidence "
              "the rule is not reaching it —\neither the wording, or a sheet that "
              "cannot express the decision the rule asks for.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
