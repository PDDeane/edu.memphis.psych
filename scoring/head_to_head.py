"""Put the olx sweep and the python sweep side by side, item by item.

Two harnesses measure the same lo-blocks prompts against the same gold rows:

  sweep_app.sh -> agreement_app.py  the app drives the call and the app's own
                                    SlotSheetGrader scores it   ("olx")
  sweep_cli.sh -> agreement.py      this harness sends the prompt and derives
                                    the score in Python         ("python")

Neither writes gold into its .json, and the two apply slightly different
per-item participant exclusions, so this reads each side's own printed log —
the gold each harness actually used, on the cells it actually ran — and
compares them on the intersection. Reporting a side's headline number over a
different participant set than the other side's is the one way this table
could lie, so the matched-cell columns are the ones to read.

    python3 head_to_head.py out/web_v3 out/cli_v3
    python3 head_to_head.py out/web_v3 out/cli_v3 --item Q6   # per-cell detail

Reading the columns. `k` is how many verdicts must ALL be right for the cell to
score exactly — gates plus point-carrying slots, read from the .olx — and `/chk`
is exact-match re-expressed per verdict, exact**(1/k). Compare items on `/chk`,
not on exact: the two say different things and exact is not comparable across
items whose k differs. Q6 reads as the corpus's weakest item at 62-69% exact
while sitting mid-pack at ~95% per check, because it carries eight of them and
0.955**8 = 0.69. Neither reading is wrong; they answer different questions.
Exact-match is what a student's score depends on. Per-check is what tells you
whether the prompt judges well, and therefore where tuning has anywhere to go.

`dvg` counts cells in handouts.GOLD_DIVERGENCES — places both implementations
disagree with a grader ON PURPOSE, because the graders applied their own written
rule inconsistently. The block under the table subtracts them. Read it before
concluding an item judges badly: on the raw numbers Q4a is handout 1's least
accurate item per check (92.8%), and adjusted it is among the best (98.0%),
because three of its four misses are recorded decisions. The same three
avoidance-framing cells inflated "the dominant error on the OC items is
over-credit" from 4 of 10 to 7 of 10.
"""

from __future__ import annotations

import argparse
import os
import re
import statistics
import sys

from handouts import config, gold_divergence_cells

# Item -> handout, in the order the handouts ask them.
ITEM_HANDOUT: dict[str, int] = {}
for _h in (1, 2, 3):
    for _it in config(_h)["rubric"].ITEMS:
        ITEM_HANDOUT[_it["id"]] = _h

# python:  "  p1   Q1    gold=4.00 pred=4.00"   (gold may be "  -  ")
_CLI_CELL = re.compile(
    r"^\s+p(\d+)\s+(\S+)\s+gold=\s*(-|[\d.]+)\s+pred=\s*(-|[\d.]+)\s*$")
# OLX:  "   1   4.00   4.00  +0.00"  under the "pid gold pred diff" header
_WEB_CELL = re.compile(r"^\s+(\d+)\s+(-|[\d.]+)\s+(-|[\d.]+)\s+[-+][\d.]+\s*$")


def _num(tok: str) -> float | None:
    return None if tok == "-" else float(tok)


def read_cli(path: str) -> dict[int, tuple[float, float]]:
    """{pid: (gold, pred)} from a sweep_cli.sh item log."""
    out = {}
    with open(path, errors="replace") as fh:
        for line in fh:
            m = _CLI_CELL.match(line.rstrip("\n"))
            if not m:
                continue
            g, p = _num(m.group(3)), _num(m.group(4))
            if g is not None and p is not None:
                out[int(m.group(1))] = (g, p)
    return out


def read_web(path: str) -> dict[int, tuple[float, float]]:
    """{pid: (gold, pred)} from a sweep_app.sh item log.

    Only rows inside the results table count. The runner's own "[runner] p3/Q1"
    progress lines and the fixture-reconstruction block also start with
    whitespace and digits, so the table header gates the scan.
    """
    out, in_table = {}, False
    with open(path, errors="replace") as fh:
        for line in fh:
            s = line.rstrip("\n")
            if re.match(r"^\s*pid\s+gold\s+pred\s+diff\s*$", s):
                in_table = True
                continue
            if in_table:
                if not s.strip() or s.strip().startswith("exact "):
                    in_table = False
                    continue
                m = _WEB_CELL.match(s)
                if m:
                    g, p = _num(m.group(2)), _num(m.group(3))
                    if g is not None and p is not None:
                        out[int(m.group(1))] = (g, p)
    return out


def score_affecting_checks(iid: str) -> int | None:
    """How many verdicts must ALL be right for a cell to score exactly.

    Gating slots plus point-carrying slots, read from the shipped .olx rather
    than assumed — a gate changes the score as surely as a scored slot does.
    None for the three items with no LLM call, where there is no verdict to get
    wrong.

    This exists because exact-match is not comparable across items with
    different check counts, and reading it as if it were is actively misleading.
    Q6 looks like the corpus's weakest item at 69%, but it carries EIGHT checks;
    0.955^8 = 0.69, so its per-check accuracy is 95.5% — better than Q3's 94.4%
    at 5 checks and Q4c's 94.3% at 2. Q6 is not judged worse than they are, it
    just has more chances to be wrong.
    """
    import agreement as A                     # local: heavy, and only used here
    for aid, spec in A.BLOCKS[ITEM_HANDOUT[iid]].items():
        if spec["item"] != iid:
            continue
        if not spec.get("olx"):
            return None
        slots = A.load_action(spec["olx"], aid)["slots"]
        return sum(1 for s in slots
                   if s.get("gates") or s.get("pts") is not None)
    return None


def per_check(exact: float, k: int | None) -> float | None:
    """Exact-match re-expressed as accuracy per individual verdict.

    exact = p**k under independence, so p = exact**(1/k). The independence
    assumption is real and imperfect — the operant-conditioning gates are
    demonstrably coupled, so emphasis on one shifts the others — which is why
    this is reported beside exact-match rather than instead of it.
    """
    if not k or exact <= 0:
        return None
    return exact ** (1.0 / k)


def tolerance(iid: str) -> float:
    item = config(ITEM_HANDOUT[iid])["rubric"].BY_ID[iid]
    pts = [c["pts"] for c in item["credit"] if c.get("pts") is not None]
    return min(pts) if pts else 0.0


def item_max(iid: str) -> float:
    return float(config(ITEM_HANDOUT[iid])["rubric"].BY_ID[iid]["max"])


def stats(errs: list[float], tol: float) -> dict:
    n = len(errs)
    if not n:
        return {"n": 0}
    return {
        "n": n,
        "exact": sum(1 for e in errs if abs(e) < 1e-9) / n,
        "tol": sum(1 for e in errs if abs(e) <= tol + 1e-9) / n,
        "mae": statistics.fmean(abs(e) for e in errs),
        "bias": statistics.fmean(errs),
    }


def pct(x: float) -> str:
    return f"{100 * x:.0f}%"


def collect(webdir: str, clidir: str) -> list[dict]:
    rows = []
    for iid, h in ITEM_HANDOUT.items():
        wlog, clog = f"{webdir}/{iid}.log", f"{clidir}/{iid}.log"
        olx = read_web(wlog) if os.path.exists(wlog) else {}
        python = read_cli(clog) if os.path.exists(clog) else {}
        if not olx and not python:
            continue
        both = sorted(set(olx) & set(python))
        tol = tolerance(iid)
        rows.append({
            "item": iid, "handout": h, "max": item_max(iid), "tol": tol,
            "k": score_affecting_checks(iid),
            "web_all": stats([p - g for g, p in olx.values()], tol),
            "cli_all": stats([p - g for g, p in python.values()], tol),
            "olx": stats([olx[i][1] - olx[i][0] for i in both], tol),
            "python": stats([python[i][1] - python[i][0] for i in both], tol),
            # olx vs python: the difference of the two ERRORS, not of the two raw
            # scores. The sides do not always score an item on the same scale —
            # 1c is measured on paper out of 10 but only its three LABEL slots
            # exist on the olx, so agreement.py reports a 6-point subtotal while
            # the app reports the full 10, and each side's gold is scaled to
            # match. Differencing raw predictions there compares 6-point scores
            # with 10-point ones and reports a constant 4-point "disagreement"
            # on cells where the two in fact agree exactly. Differencing errors
            # is identical whenever the scales match and correct when they do not.
            "xx": stats([(olx[i][1] - olx[i][0]) - (python[i][1] - python[i][0])
                         for i in both], tol),
            "n_web_only": len(set(olx) - set(python)),
            "n_cli_only": len(set(python) - set(olx)),
            "rescaled": sorted(i for i in both if abs(olx[i][0] - python[i][0]) > 1e-9),
            # (olx gold, olx pred, python gold, python pred)
            "cells": {i: (olx[i][0], olx[i][1], python[i][0], python[i][1]) for i in both},
        })
    return rows


def report(rows: list[dict], webdir: str, clidir: str) -> None:
    print(f"\nweb ({webdir})  vs  python ({clidir})\n")
    hdr = (f"{'item':>5} {'h':>2} {'max':>5} {'k':>2} {'n':>3} {'dvg':>3} │"
           f" {'exact':>6} {'/chk':>5} {'±tol':>6} {'MAE':>5} {'bias':>6} │"
           f" {'exact':>6} {'/chk':>5} {'±tol':>6} {'MAE':>5} {'bias':>6} │"
           f" {'agree':>6} {'MAE':>5}")
    print(f"{'':>25} │{'olx':^35}│{'python':^35}│{'olx vs python':^13}")
    print(hdr)
    print("─" * len(hdr))

    def chk(e, k):
        v = per_check(e, k)
        return f"{100 * v:.1f}" if v is not None else "  — "

    dvg = gold_divergence_cells()

    missing = []
    for r in rows:
        w, c, x = r["olx"], r["python"], r["xx"]
        if not w["n"] or not c["n"]:
            missing.append((r["item"], bool(w["n"]), bool(c["n"])))
            continue
        k = r["k"]
        nd = sum(1 for pid in r["cells"] if (r["item"], pid) in dvg)
        print(f"{r['item']:>5} {r['handout']:>2} {r['max']:>5.2f} "
              f"{(str(k) if k else '-'):>2} {w['n']:>3} {(str(nd) if nd else ''):>3} │"
              f" {pct(w['exact']):>6} {chk(w['exact'], k):>5} {pct(w['tol']):>6}"
              f" {w['mae']:>5.2f} {w['bias']:>+6.2f} │"
              f" {pct(c['exact']):>6} {chk(c['exact'], k):>5} {pct(c['tol']):>6}"
              f" {c['mae']:>5.2f} {c['bias']:>+6.2f} │"
              f" {pct(x['exact']):>6} {x['mae']:>5.2f}")

    # Per-handout and overall pools, over matched cells only.
    print("─" * len(hdr))
    for label, hs in (("H1", (1,)), ("H2", (2,)), ("H3", (3,)), ("ALL", (1, 2, 3))):
        we, ce, xe, tw, tc, tx = [], [], [], 0, 0, 0
        # Pooled per-check is a CELL-weighted mean of the per-item figures, not
        # exact**(1/k) over the pool: k differs per item, so the pool has no
        # single k to take a root by.
        wchk, cchk = [], []
        for r in rows:
            if r["handout"] not in hs or not r["olx"]["n"] or not r["python"]["n"]:
                continue
            wv, cv = per_check(r["olx"]["exact"], r["k"]), per_check(r["python"]["exact"], r["k"])
            for pid, (wg, wp, cg, cp) in r["cells"].items():
                we.append(wp - wg); ce.append(cp - cg)
                xe.append((wp - wg) - (cp - cg))
                tw += abs(wp - wg) < 1e-9
                tc += abs(cp - cg) < 1e-9
                tx += abs((wp - wg) - (cp - cg)) < 1e-9
                if wv is not None:
                    wchk.append(wv)
                if cv is not None:
                    cchk.append(cv)
        if not we:
            continue
        n = len(we)
        wc = f"{100 * statistics.fmean(wchk):.1f}" if wchk else "  — "
        cc = f"{100 * statistics.fmean(cchk):.1f}" if cchk else "  — "
        print(f"{label:>5} {'':>2} {'':>5} {'':>2} {n:>3} {'':>3} │"
              f" {pct(tw / n):>6} {wc:>5} {'':>6} {statistics.fmean(map(abs, we)):>5.2f}"
              f" {statistics.fmean(we):>+6.2f} │"
              f" {pct(tc / n):>6} {cc:>5} {'':>6} {statistics.fmean(map(abs, ce)):>5.2f}"
              f" {statistics.fmean(ce):>+6.2f} │"
              f" {pct(tx / n):>6} {statistics.fmean(map(abs, xe)):>5.2f}")

    # Where the two systems actually diverge, largest first. This is the column
    # the rest of the table exists to point at.
    div = []
    for r in rows:
        for pid, (wg, wp, cg, cp) in r.get("cells", {}).items():
            d = (wp - wg) - (cp - cg)
            if abs(d) > 1e-9:
                div.append((abs(d), r["item"], pid, wg, wp, cg, cp))
    if div:
        print(f"\nCells where olx and python disagree ({len(div)}), largest first:")
        print("  (Δ is the gap between the two errors, so it is right even where "
              "the sides score an item on different scales)")
        for d, iid, pid, wg, wp, cg, cp in sorted(div, reverse=True)[:40]:
            better = "olx" if abs(wp - wg) < abs(cp - cg) else (
                "python" if abs(cp - cg) < abs(wp - wg) else "tie")
            gold = f"{wg:>5.2f}" if abs(wg - cg) < 1e-9 else f"{wg:>5.2f}/{cg:<5.2f}"
            print(f"  {iid:>5} p{pid:<3} gold {gold}   olx {wp:>5.2f} ({wp - wg:+.2f})   "
                  f"python {cp:>5.2f} ({cp - cg:+.2f})   Δ{d:>5.2f}  closer: {better}")

    # Coverage caveats, printed rather than folded away: a matched-cell table
    # silently drops whatever one side never ran.
    # Declared divergences from gold, subtracted. Both numbers are reported: the
    # raw one is what a student's score depends on, the adjusted one is what says
    # whether the prompt judges well. Reading only the raw one made Q4a look like
    # handout 1's weakest-judged item when it is among its strongest.
    hit = [(r, [pid for pid in r["cells"] if (r["item"], pid) in dvg]) for r in rows]
    hit = [(r, ps) for r, ps in hit if ps and r["olx"]["n"] and r["python"]["n"]]
    if hit:
        print(f"\nDeclared divergences from gold subtracted "
              f"(handouts.GOLD_DIVERGENCES — decisions, not defects):")
        sub = (f"{'item':>5} {'k':>2} {'n*':>3} {'dvg':>4} │ {'exact*':>7} {'/chk*':>6}"
               f" │ {'exact*':>7} {'/chk*':>6}   codes")
        print(f"{'':>17} │{'olx':^17}│{'python':^17}")
        print(sub)
        print("─" * len(sub))
        pool = {"w": [0, 0], "c": [0, 0]}
        for r, ps in hit:
            keep = {pid: v for pid, v in r["cells"].items() if pid not in ps}
            if not keep:
                continue
            we = sum(1 for wg, wp, _, _ in keep.values() if abs(wp - wg) < 1e-9)
            ce = sum(1 for _, _, cg, cp in keep.values() if abs(cp - cg) < 1e-9)
            n = len(keep)
            pool["w"][0] += we; pool["w"][1] += n
            pool["c"][0] += ce; pool["c"][1] += n
            codes = ",".join(sorted({dvg[(r["item"], p)] for p in ps}))
            print(f"{r['item']:>5} {(str(r['k']) if r['k'] else '-'):>2} {n:>3} {len(ps):>4} │"
                  f" {pct(we / n):>7} {chk(we / n, r['k']):>6} │"
                  f" {pct(ce / n):>7} {chk(ce / n, r['k']):>6}   {codes}")
        print("─" * len(sub))
        print(f"{'these':>5} {'':>2} {pool['w'][1]:>3} {'':>4} │"
              f" {pct(pool['w'][0] / pool['w'][1]):>7} {'':>6} │"
              f" {pct(pool['c'][0] / pool['c'][1]):>7}")
        for d in sorted({dvg[(r['item'], p)] for r, ps in hit for p in ps}):
            cells = sorted(f"{r['item']}/p{p}" for r, ps in hit for p in ps
                           if dvg[(r['item'], p)] == d)
            print(f"    {d:<18} {', '.join(cells)}")

    scaled = [r for r in rows if r.get("rescaled")]
    if scaled:
        print("\nItems the two sides score on DIFFERENT scales — per-side columns are "
              "each against their own gold; the olx-vs-python column compares errors:")
        for r in scaled:
            wg, _, cg, _ = next(iter(r["cells"].values()))
            print(f"  {r['item']:>5}  olx gold out of {r['max']:.0f}, python reports a "
                  f"subtotal (e.g. p{next(iter(r['cells']))}: olx {wg:.2f} vs python {cg:.2f}) "
                  f"— {len(r['rescaled'])}/{r['olx']['n']} cells")

    odd = [r for r in rows if r["n_web_only"] or r["n_cli_only"]]
    if odd:
        print("\nCells one side ran and the other did not (excluded above):")
        for r in odd:
            print(f"  {r['item']:>5}  olx-only {r['n_web_only']:>2}   "
                  f"python-only {r['n_cli_only']:>2}")
    if missing:
        print("\nItems missing a side entirely (excluded above):")
        for iid, hw, hc in missing:
            print(f"  {iid:>5}  olx={'yes' if hw else 'NO'}  python={'yes' if hc else 'NO'}")


def detail(rows: list[dict], iid: str) -> None:
    r = next((x for x in rows if x["item"] == iid), None)
    if r is None:
        raise SystemExit(f"no data for {iid}")
    print(f"\n{iid} (handout {r['handout']}, max {r['max']:.2f}, tol {r['tol']:.2f})\n")
    print(f"{'pid':>4} {'w gold':>7} {'olx':>6} {'w err':>7} │ "
          f"{'c gold':>7} {'python':>6} {'c err':>7}")
    print("─" * 55)
    for pid, (wg, wp, cg, cp) in sorted(r["cells"].items()):
        flag = "  <-" if abs((wp - wg) - (cp - cg)) > 1e-9 else ""
        print(f"{pid:>4} {wg:>7.2f} {wp:>6.2f} {wp - wg:>+7.2f} │ "
              f"{cg:>7.2f} {cp:>6.2f} {cp - cg:>+7.2f}{flag}")


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__.split("Run")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("webdir")
    ap.add_argument("clidir")
    ap.add_argument("--item", default=None, help="Per-cell detail for one item.")
    args = ap.parse_args()

    rows = collect(args.webdir, args.clidir)
    if not rows:
        raise SystemExit("no item logs found in either directory")
    if args.item:
        detail(rows, args.item)
    else:
        report(rows, args.webdir, args.clidir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
