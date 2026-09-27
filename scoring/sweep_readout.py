#!/usr/bin/env python3
"""Did a measured edit help, hurt, or do nothing? Subgoal E51.

    python3 sweep_readout.py ITEM before.json

`before.json` is {"cell": pooled_count_out_of_12, ...} from before the edit.
Prints every cell, and a verdict that distinguishes a REGRESSION from SAMPLING.

WHY THIS EXISTS. Every sweep script carried its own abort condition, and every
one of them said the same thing: "any currently-perfect cell that moves is
grounds to revert." On 2026-09-06 that rule fired on SIX OF SEVEN sweeps, and
the seventh is why it is now known to be wrong.

THE MEASUREMENT THAT REFUTED IT. Q2 was swept twice at prompt_sha c73a7e96196c
-- the SAME sha both times, because the edit under test never reached the prompt.
Two independent 6-run python measurements of an IDENTICAL prompt:

    p6    1/6 -> 3/6
    p16   6/6 -> 2/6        a PERFECT cell to 2 of 6, with nothing changed
    p18   6/6 -> 5/6

THREE OF TWENTY CELLS MOVED WITH NOTHING CHANGED, one of them by four runs. So
"a perfect cell moved" does not distinguish a regression from a resample, and an
abort keyed to it reverts working edits. It very nearly reverted subgoal Q43's,
which had fixed its target cell outright.

WHAT THIS USES INSTEAD, and the thresholds are set from that measurement rather
than by taste:

  BOTH SIDES. The noise above is per-side sampling. A real regression should show
  on the python mirror AND the app, which are separate samples of the same
  prompt. A single-side move is reported and does NOT abort.

  MARGIN. The observed noise reached FOUR runs of six on one cell. Pooled over
  both sides that is 12 runs, so a drop of 1 or 2 pooled is inside what an
  unchanged prompt produced. Only a drop of 3 or more pooled counts.

  THE ITEM TOTAL. An edit that lowers BOTH sides' totals is a loss whatever the
  cells did; an edit that raises both is a gain even if cells shuffled.

WHAT IT DELIBERATELY DOES NOT DO: silence anything. Every movement is printed.
The verdict says which of them the evidence can carry, and a mover that fails the
threshold is listed as WATCH, not hidden -- subgoal E45 exists because cells that
nothing names drift unread.
"""
import json
import sys

MIN_POOLED_DROP = 3          # below this is inside the measured noise floor
NOISE_NOTE = ("measured 2026-09-06: an unchanged prompt moved 3 of 20 cells, "
              "one by 4 runs of 6")


import pathlib as _pathlib

# DERIVED, NEVER NAMED (trap T32). These inserts used to carry this tree's
# absolute path as a literal, at position 0. Here that happened to be correct --
# the path names the directory the file is already in -- so it was harmless and
# invisible. It was NOT harmless in the migration sandbox, which is a copy of
# this tree: there the literal still named THIS directory, won ahead of the
# sandbox's own, and made a dry-run audit execute live modules. A traceback was
# found walking out of the sandbox's enforcement.py into live's agreement.py,
# three lines below one of these inserts, and because the selftest writes module
# files by path, a sandbox run could write the live tree.
#
# The line is fixed HERE, where it is correct, precisely because being correct by
# coincidence is what let it be copied into a place where it was not.
_OWN_DIR = str(_pathlib.Path(__file__).resolve().parent)


def _dropped(item: str, form) -> set:
    """Cells that MUST NOT appear as evidence: suspect AND per-item excluded.

    A CELL DROPPED FROM THE RATE MUST NOT REACH A REVERT DECISION. This module
    already dropped `handouts.suspect`, and knew nothing about
    `handouts.PER_ITEM_EXCLUDE` -- so on 2026-09-06 the 1c readout printed p4,
    p19 and p20 as movers, all three of them declared unreachable on the web
    (their typed data DRAWS the chart, so the paper's "no graph" failure cannot
    occur). The item TOTALS were exclusion-aware and the verdict was not
    numerically wrong, but the cells were listed as findings and were read as
    live ones. A number that cannot count toward the rate cannot count toward
    keeping or reverting an edit either, and printing it invites exactly that.
    """
    sys.path.insert(0, _OWN_DIR)
    import forms as H
    out = set(H.suspect(form)) if form else set()
    out |= set((getattr(H, "PER_ITEM_EXCLUDE", {}) or {}).get(item, {}))
    return out

def readout(item: str, before: dict) -> int:
    """0 if the edit is safe to keep, 1 if the evidence says revert."""
    sys.path.insert(0, _OWN_DIR)
    import forms as H
    import measured as M

    # E56: A BEFORE-SNAPSHOT MEASURES A PROMPT. If that prompt is not the one in
    # the tree, the comparison is between two different questions and every
    # figure below is meaningless -- worse than absent, because it prints a
    # verdict.
    #
    # BOUGHT WITH A WRONG VERDICT ON 2026-09-07. Q4b's re-sweep passed a snapshot
    # of the ledger's THEN-current entry, which held the numbers from an ABORTED
    # report sweep measured against a reverted prompt. The readout compared
    # against 13/19 and 14/19, reported "NET +3, VERDICT: KEEP", and the same
    # script's own pre-registration named the honest baseline as 16/19 and 17/19
    # -- against which the item had FALLEN 3. The tool did what it was told; the
    # instruction was wrong, and nothing was positioned to say so.
    for side in ("olx",):
        snap = (before or {}).get(side) or {}
        was = snap.get("prompt_sha")
        if not was:
            continue
        try:
            now = (M.records(side).get(item) or {}).get("prompt_sha")
        except Exception:
            continue
        if now and was != now:
            print(f"REFUSING to read out {item}: the before-snapshot for `{side}` "
                  f"was taken at prompt {str(was)[:12]} and the ledger now records "
                  f"{str(now)[:12]}. Those are two different questions, so a "
                  f"before/after on them is not a comparison. Re-take the snapshot "
                  f"against the prompt that is being measured, or name the baseline "
                  f"explicitly and say which prompt produced it.", file=sys.stderr)
            return 1

    form = None
    for h in H.declared():
        try:
            if item in M._form_gold_items(h):
                form = h
                break
        except Exception:
            continue
    suspect = _dropped(item, form)

    rows, regressions, watch = [], [], []
    for pid in range(1, 21):
        if pid in suspect:
            continue
        g = M.gold_cell(item, pid)
        if not g or g.get("score") is None:
            continue
        per = {}
        for side in ("olx",):
            s = [x for x in M._pooled_cell_scores(item, pid, side) if x is not None]
            per[side] = (sum(1 for x in s if abs(x - g["score"]) < 1e-9), len(s))
        # ONE WEB COLUMN. `olx` already carries the retired python engine's
        # runs -- they were folded into it (goal O) -- so adding a second side
        # here would have counted nothing and raised on a missing key.
        now = per["olx"][0]
        tot = per["olx"][1]
        was = before.get(str(pid), before.get(pid))
        rows.append((pid, g["score"], was, now, tot, per))
        if was is None or now >= was:
            continue
        drop = was - now
        # BOTH SIDES, and the per-side halves are compared against a pro-rated
        # half of the old pooled count -- the only comparison available when the
        # `before` table is pooled.
        half = was / 2.0
        both = per["olx"][0] < half
        why = []
        if drop < MIN_POOLED_DROP:
            why.append(f"drop {drop} < {MIN_POOLED_DROP}")
        if not both:
            why.append("one side only")
        watch.append((pid, was, now, ", ".join(why) or f"drop {drop}, both sides"))

    # ONE WEB COLUMN. The table had a column per engine; `olx` carries the
    # retired python engine's runs now (goal O), so there is one to print.
    print(f"  cell  gold   before  after   olx")
    for pid, gold, was, now, tot, per in rows:
        w = f"{was:>2}/12" if was is not None else "   -"
        print(f"  p{pid:<4} {gold:>5}  {w}  {now:>2}/{tot:<3}  "
              f"{per['olx'][0]}/{per['olx'][1]}")
    for side in ("olx",):
        try:
            e = M.records(side)[item]
            print(f"  {side:<7} {e['numerator']}/{e['denominator']}")
        except Exception:
            pass
    # THE VERDICT RIDES THE ITEM TOTALS, NOT THE CELLS, and the first version of
    # this module got that wrong. Its cell rule -- a drop of 3+ pooled on BOTH
    # sides -- was tested against the unchanged-prompt case and STILL fired, on
    # Q2/p16, which moved 12/12 to 7/12 with nothing changed. So the cell-level
    # noise floor on this corpus reaches at least FIVE pooled runs, and no
    # threshold low enough to catch a real regression can exclude it. Item totals
    # are the stabler statistic: across the same pair Q2 held 19/20 python and
    # went 18 -> 19 olx, correctly reading as no harm.
    ol_now = ol_was = None
    try:
        # The web column is `olx` and there is one of it.
        ol_now = M.records("olx")[item]["numerator"]
        ol_was = (M.records("olx")[item].get("previous") or {}).get("numerator")
    except Exception:
        pass
    # THE FIRST VERSION REQUIRED BOTH SIDES TO FALL, AND THAT WAS TOO LENIENT.
    # Subgoal Q47's eighth attempt, 2026-09-06: python held at 16 while olx went
    # 18 -> 16 and
    # BOTH pre-registered targets missed, and this printed KEEP -- because one
    # side being flat is not "both fell". A side holding still does not pay for
    # the other side losing two cells. The test is the NET across both sides,
    # which is the quantity an edit is supposed to move.
    # ONE SIDE NOW, so the NET is that side's movement. It used to sum both web
    # columns -- the test being the net an edit moves rather than either column
    # alone -- and the python column's runs are inside `olx` since goal O, so
    # the same quantity is being read from one row.
    net = None
    if None not in (ol_now, ol_was):
        net = ol_now - ol_was
    lost_both = net is not None and net < 0
    if watch:
        print("\n  MOVED, BUT INSIDE THE NOISE FLOOR — reported, not charged "
              f"({NOISE_NOTE}):")
        for pid, was, now, why in watch:
            print(f"    p{pid}: {was}/12 -> {now}/12   [{why}]")
    if None not in (ol_now, ol_was):
        print(f"\n  ITEM TOTALS: olx {ol_was} -> {ol_now}")
    if net is not None:
        print(f"  NET: {net:+d}")
    print("  VERDICT: " + (
        "REVERT -- the net across both sides is negative. The cells above say "
        "where to look, but the totals are what carries it"
        if lost_both else
        "KEEP -- the net across both sides did not fall. Cell movement above is "
        "reported for reading and is not, on its own, evidence of harm"))
    return 1 if lost_both else 0


def slot_profile(item: str, slots: tuple, cells: tuple = ()) -> int:
    """Per-cell answers for named slots, read with the canonical readers.

    Subgoal E47. Fourteen sweep scripts hand-rolled this lookup and two of them
    were wrong in opposite directions -- `r.get("checks") or r.get("verdicts")`
    never consults `verdicts` and returns `''` for a PICK, and
    `r.get("answers") or r.get("refers_to")` fails the same way reversed. Both
    produced confident wrong readings on 2026-09-05/06: one reported Q2's
    `wgb_names` as never answered on python when it answered `doing` 97 times.
    An empty string is ABSENCE, not a value, and only `measured.slot_answer`
    knows that.

    A sweep script's per-slot step should CALL THIS, not re-type the lookup:

        python3 sweep_readout.py --slots Q6 change_a1_does,change_a2_does 2,8

    Prints, per cell, the pooled right-count and every combination the named
    slots took, most common first.
    """
    import measured as _M

    _M.warn_if_stale(item, where="readout")

    sys.path.insert(0, _OWN_DIR)
    import collections

    import forms as H
    import measured as M

    form = None
    for h in H.declared():
        try:
            if item in M._form_gold_items(h):
                form = h
                break
        except Exception:
            continue
    suspect = _dropped(item, form)
    want = set(cells) if cells else None

    print(f"  {item}: {', '.join(slots)}")
    for pid in range(1, 21):
        if pid in suspect or (want and pid not in want):
            continue
        g = M.gold_cell(item, pid)
        if not g or g.get("score") is None:
            continue
        sc = [x for x in M._pooled_cell_scores(item, pid, "olx") if x is not None]
        if not sc:
            continue
        right = sum(1 for x in sc if abs(x - g["score"]) < 1e-9)
        combos: collections.Counter = collections.Counter()
        for side in ("olx",):
            try:
                doc = M._runs_doc(item, side)
            except Exception:
                continue
            for run in doc["runs"]:
                for r in run["results"]:
                    q = r.get("participant_id")
                    if q is None and r.get("cell"):
                        head = str(r["cell"]).split("/")[0].lstrip("pP")
                        q = int(head) if head.isdigit() else None
                    if q != pid:
                        continue
                    combos["/".join(str(M.slot_answer(r, s)) for s in slots)] += 1
        shown = "  ".join(f"{k} x{n}" for k, n in combos.most_common(3))
        print(f"    p{pid:<4} gold {g['score']:>5}  {right:>2}/{len(sc):<3}  {shown}")
    return 0


def cell_texts(item: str, cells: tuple = (), fields: tuple = ()) -> int:
    """Every response field a cell holds, printed WHOLE. Subgoal E47.

    THE READER THAT DID NOT EXIST, and its absence cost two wrong readings in one
    day. There were canonical readers for ARTIFACTS (`measured.slot_answer`) and
    for SOURCE (`measured.slot_block`), and none for FIXTURE TEXT -- so a readout
    of DAY2's conditions was hand-rolled as `plan.split(" I ")[0]`, which returns
    the string "If" for any plan beginning "If I ...". THIRTEEN OF SIXTEEN CELLS
    PRINTED AS `If`, under a column header saying `cond:`, and a claim about all
    sixteen was then generalised from the four that happened to read properly.

    SO THIS EXTRACTS NOTHING. It prints each field entire and lets the reader do
    the reading. Any "just take the first clause" convenience belongs at the point
    of judgement, in a person's head, not in a helper that will be trusted later.

        python3 sweep_readout.py --cells DAY2
        python3 sweep_readout.py --cells DAY2 7,15 bmod_h1_utb,bmod_h2_day2

    Suspect cells are dropped, because a suspect cell is never evidence.
    """
    import measured as _M

    _M.warn_if_stale(item, where="readout")

    sys.path.insert(0, _OWN_DIR)
    import textwrap

    import agreement as A
    import forms as H
    import measured as M

    form = None
    for h in H.declared():
        try:
            if item in M._form_gold_items(h):
                form = h
                break
        except Exception:
            continue
    suspect = _dropped(item, form)
    want = set(cells) if cells else None

    for pid in range(1, 21):
        if pid in suspect or (want and pid not in want):
            continue
        g = M.gold_cell(item, pid)
        if not g or g.get("score") is None:
            continue
        try:
            fx = A.fixture_for(item, pid) or {}
        except Exception:
            continue
        sc = [x for x in M._pooled_cell_scores(item, pid, "olx") if x is not None]
        right = sum(1 for x in sc if abs(x - g["score"]) < 1e-9)
        print(f"\n  {item}/p{pid}  gold {g['score']}  right {right}/{len(sc)}")
        fb = g.get("feedback")
        if fb:
            print(textwrap.fill(f"GOLD: {fb}", 104,
                                initial_indent="     ", subsequent_indent="           "))
        for k, v in (fx or {}).items():
            if fields and k not in fields:
                continue
            v = (v or "").strip()
            if not v:
                continue
            print(textwrap.fill(f"{k}: {v}", 104,
                                initial_indent="     ", subsequent_indent="           "))
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--cells":
        _c = tuple(int(x) for x in sys.argv[3].split(",")) if len(sys.argv) > 3 else ()
        _f = tuple(sys.argv[4].split(",")) if len(sys.argv) > 4 else ()
        raise SystemExit(cell_texts(sys.argv[2], _c, _f))
    if len(sys.argv) >= 4 and sys.argv[1] == "--slots":
        _cells = tuple(int(x) for x in sys.argv[4].split(",")) if len(sys.argv) > 4 else ()
        raise SystemExit(slot_profile(sys.argv[2], tuple(sys.argv[3].split(",")), _cells))
    if len(sys.argv) != 3:
        raise SystemExit("usage: sweep_readout.py ITEM before.json\n"
                         "       sweep_readout.py --slots ITEM slot1,slot2 [cell,cell]")
    with open(sys.argv[2]) as fh:
        raise SystemExit(readout(sys.argv[1], json.load(fh)))
