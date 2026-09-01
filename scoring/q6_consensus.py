#!/usr/bin/env python3
"""Build ONE stable parse of each Q6 answer from repeated python runs.

The problem this solved. Q6's olx fixture is eight boxes filled from
`credit_checks[].evidence`, and those spans were not stable: one rerun apart, the
python's met/unmet verdict was identical on 134 of 136 slots (99%) while the quoted
span changed on 64 of 136 (47%). The python never noticed — it reads the whole block
and its own score barely moves — but the olx fixture IS the spans, so every Q6
measurement sat on a foundation that shifted under it. Two olx runs one python
rescore apart were not comparable even when nothing else had changed.

So: run the scorer N times, then take the consensus rather than any one run.

STATE: fixed, and the fix is load-bearing rather than cosmetic. Read past-tense
above as past tense. With the frozen table in place, `fixture_for("Q6", pid)`
is byte-identical across processes for all 20 participants, and an audit of the
current table finds 158 of 160 slots agreeing on at least 80% of runs. The two
that do not are p9's `state_c2` and `affect_c2`, tied 5/5, and p9 is declared in
PER_ITEM_EXCLUDE on BOTH sides — the python included, because agreement.py's
fixture_for imports build_jobs and therefore inherits the same tie-break.

What remains is NOT instability. Q6's score still moves a point or two between
runs (59%/62%/69% on three measurements), and that is the model sampling on a
fixture that no longer moves — a different thing, and the expected one. Do not
read run-to-run score variance as this problem coming back.

The residual risk is a rebuild, not a rerun: a table built from fewer runs, or a
new participant whose answer splits the vote, would be frozen just as firmly and
read just as confidently. agreement_app.build_jobs now checks each slot's vote
share against CONSENSUS_MIN_SHARE and complains about any weak cell that is not
declared, so that failure announces itself instead of quietly deciding points.

    python3 q6_consensus.py --build      # aggregate out/q6_consensus/run*/
    python3 q6_consensus.py --show 12    # inspect one participant
    python3 q6_consensus.py --report     # agreement between runs, per slot

WORD-LEVEL VOTING, PER SLOT, OVERLAP PRESERVED. For each participant the raw Q6
answer is tokenised once. Each run's evidence for a slot is located in that token
stream, and every token it covers gets a vote for that slot. A token joins the
consensus span for a slot when at least `--threshold` of the runs that scored the
cell put it there.

Crucially the slots are voted INDEPENDENTLY and may overlap. Forcing a disjoint
partition was tried and is catastrophic: one sentence can legitimately both name
a consequence and say how it is affected, which is exactly what this item's
guidance tells the grader to allow ("PRESENCE IS NOT WORDING"), and slicing it
took the item from 11/17 to 3/17. The overlap is signal, not noise — what this
module removes is the run-to-run jitter in where each span starts and stops.

The verdict is voted too, by plurality, and a slot whose winning verdict is
`absent` gets an empty box regardless of what any run quoted: only `absent` means
the student wrote nothing there.

CHOOSING THE THRESHOLD. It controls how wide the consensus spans come out, and
that matters: wider boxes hold more text, more slots look filled, and the olx
grades more generously. Measured against the single-run fixture's own width
(102 filled boxes, 34 overlapping, 105% median retention):

    0.5 -> 102 / 36 / 109%      unions the runs; measured bias +0.41..+0.56
    0.6 -> 102 / 34 / 103%      matches the single-run width
    0.7 -> 101 / 26 / 101%
    0.8 ->  99 / 26 /  99%
    1.0 ->  90 / 24 /  95%      only words every run claimed

0.6 is the default because it changes ONE thing — the run-to-run jitter in where
a span starts and stops — without also making the boxes bigger or smaller than
the fixture this replaces. A first attempt at 0.5 shifted bias from +0.16..+0.31
to +0.41..+0.56 and cost two cells of agreement, purely by widening.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, __file__.rsplit("/", 1)[0])

from handouts import config, find_submissions
from segment import segment
import paths

RUNS = f"{paths.OUT}/q6_consensus"
OUT = os.path.join(RUNS, "consensus.json")
SLOTS = ["state_a1", "change_a1", "state_c1", "affect_c1",
         "state_a2", "change_a2", "state_c2", "affect_c2"]

_WORD = re.compile(r"\S+")


def tokens(text: str) -> list[tuple[int, int, str]]:
    """(start, end, word) for every whitespace-delimited token."""
    return [(m.start(), m.end(), m.group(0)) for m in _WORD.finditer(text or "")]


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()


def locate(span: str, toks: list[tuple[int, int, str]]) -> list[int]:
    """Token indices covered by `span`, matched on normalised words.

    Matching on words rather than characters survives the punctuation and
    smart-quote differences between one run's quotation and the next, which is
    most of what varies.
    """
    want = _norm(span).split()
    if not want:
        return []
    have = [_norm(w) for _, _, w in toks]
    n = len(want)
    # Longest run of consecutive tokens the span covers; fall back to a fuzzy
    # window when the quotation is not verbatim.
    for i in range(len(have) - n + 1):
        if have[i:i + n] == want:
            return list(range(i, i + n))
    best, score = [], 0.0
    wset = set(want)
    for i in range(len(have)):
        for j in range(i + 1, min(i + n + 6, len(have)) + 1):
            win = have[i:j]
            hit = sum(1 for w in win if w in wset)
            s = hit / max(len(win), n)
            if s > score:
                best, score = list(range(i, j)), s
    return best if score >= 0.5 else []


def load_runs() -> dict[int, list[dict]]:
    """{participant: [that run's Q6 record, ...]} over every run directory."""
    out: dict[int, list[dict]] = {}
    for d in sorted(glob.glob(os.path.join(RUNS, "run*"))):
        for f in sorted(glob.glob(os.path.join(d, "participant_*.json"))):
            pid = int(re.search(r"(\d+)", os.path.basename(f)).group(1))
            rec = json.load(open(f))
            q6 = [i for i in rec.get("items", []) if i.get("item_id") == "Q6"]
            if q6:
                out.setdefault(pid, []).append(q6[0])
    return out


def build(threshold: float) -> dict:
    cfg = config(1)
    paths = dict(find_submissions(1, None))
    runs = load_runs()
    result = {"threshold": threshold, "n_runs": {}, "participants": {}}
    for pid, recs in sorted(runs.items()):
        sec = segment(paths[pid], cfg["template"], cfg["markers"],
                      cfg["capture_tail"], cfg.get("join_aware", False))
        raw = sec.get("Q6") or ""
        toks = tokens(raw)
        need = max(1, int(round(threshold * len(recs))))
        result["n_runs"][str(pid)] = len(recs)
        fields, detail = {}, {}
        for slot in SLOTS:
            votes = Counter()
            verdicts = Counter()
            for rec in recs:
                ck = {c["what"]: c for c in rec.get("credit_checks", [])}
                c = ck.get(slot)
                if c is None:
                    continue
                verdicts[c.get("verdict") or ("met" if c.get("met") else "absent")] += 1
                for i in locate(c.get("evidence") or "", toks):
                    votes[i] += 1
            verdict = verdicts.most_common(1)[0][0] if verdicts else "absent"
            keep = sorted(i for i, n in votes.items() if n >= need)
            # One contiguous span from the first kept token to the last: the
            # student's own words in between belong to the same clause, and
            # holes would produce the fragments the anchored split produced.
            span = "" if not keep else raw[toks[keep[0]][0]:toks[keep[-1]][1]].strip()
            if verdict == "absent":
                span = ""
            fields[slot] = span
            detail[slot] = {"verdict": verdict, "verdicts": dict(verdicts),
                            "tokens_kept": len(keep),
                            "vote_spread": dict(Counter(votes.values()))}
        result["participants"][str(pid)] = {"fields": fields, "detail": detail}
    return result


def report() -> None:
    runs = load_runs()
    print(f"{'pid':>4}{'runs':>6}  per-slot verdict agreement across runs")
    tot = unan = 0
    for pid, recs in sorted(runs.items()):
        line = []
        for slot in SLOTS:
            vs = Counter()
            for rec in recs:
                ck = {c["what"]: c for c in rec.get("credit_checks", [])}
                if slot in ck:
                    c = ck[slot]
                    vs[c.get("verdict") or ("met" if c.get("met") else "absent")] += 1
            tot += 1
            top = vs.most_common(1)[0][1] if vs else 0
            n = sum(vs.values())
            unan += (top == n and n > 0)
            line.append(f"{top}/{n}")
        print(f"{pid:>4}{len(recs):>6}  " + " ".join(f"{x:>5}" for x in line))
    print(f"\n  slots where every run agreed on the verdict: {unan}/{tot} ({unan/tot:.0%})")


def show(pid: int) -> None:
    data = json.load(open(OUT))
    p = data["participants"][str(pid)]
    print(f"p{pid}  ({data['n_runs'][str(pid)]} runs, threshold {data['threshold']})")
    for slot in SLOTS:
        d = p["detail"][slot]
        print(f"  {slot:<11} verdict={d['verdict']:<14} verdicts={d['verdicts']}")
        print(f"  {'':<11} {p['fields'][slot][:110]!r}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--show", type=int)
    ap.add_argument("--threshold", type=float, default=0.6,
                    help="fraction of runs that must claim a word (default 0.6)")
    a = ap.parse_args()
    if a.report:
        report(); return 0
    if a.build:
        data = build(a.threshold)
        with open(OUT, "w") as fh:
            json.dump(data, fh, indent=1)
        n = len(data["participants"])
        print(f"wrote {OUT}: {n} participants")
        return 0
    if a.show is not None:
        show(a.show); return 0
    ap.error("one of --build, --report, --show is required")


if __name__ == "__main__":
    raise SystemExit(main())
