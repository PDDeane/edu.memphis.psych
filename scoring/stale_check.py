"""Are the stored paper-scorer predictions still scored by the current rubric?

`score.py` writes one `participant_NNN.json` per student and `baseline.py` reads
them back. Nothing connected the two: a rubric edit — a renamed slot, an added
verdict state, a moved `max` — left the stored predictions in place, and the next
`baseline.py` run reported them as though they were current. That happened: on
handout 1 a renamed slot (`wgb_stated` -> `wgb_inverts_utb`) and a new Q5 verdict
sat unscored for two days, and on handout 3 items 2a/2b/3 were still scored
member-by-member after those members had been folded into a counted group. Both
were being reported as current measurements.

Mtimes are not the test. A rubric file can be touched without a scoring change,
and `--items` merges leave a directory whose newest file is recent while most of
it is old. So this checks the DATA: a stored cell records the slot keys it
scored, the verdict it chose for each and the item max it scored against, and a
rubric change that matters is visible in at least one of the three.

    python3 stale_check.py                # all three handouts
    python3 stale_check.py --handout 2
    python3 stale_check.py --handout 1 --outdir out/h1_prerename

Exit 1 if anything is stale, so a sweep script can refuse to publish numbers
built on predictions the rubric has moved past. Re-scoring an affected item is
`score.py --handout H --items ITEM`, which merges into the existing files.

Deliberately quiet about two things that look like staleness and are not:

  * A slot the rubric declares with no verdict list. There is nothing to compare
    a stored verdict against, so the verdict check skips it rather than flagging
    every cell.
  * A slot missing from SOME participants. A gate that fails short-circuits the
    rest of the sheet, so a partial slot set is the normal shape of a cell that
    scored zero. Only a slot missing from EVERY participant means the rubric
    grew a slot this run could not have scored.
All three scoring modes are covered. `derive_from_credit` and plain items are
checked against the rubric's `credit` list; `derive_from_criteria` items are
checked against `score.oc_check_names()`, which runs the real ledger over a
passing sheet — those items do not score from `credit` at all, and comparing them
against it once reported all eight of handout 2's as stale when none were.
"""

from __future__ import annotations

import argparse
import glob
import json
import os

from handouts import HANDOUTS, config
# THROUGH THE REGISTRY. Goal E step 5: `score.oc_check_names` was an alias for
# the plugin's `check_names`, and the aliases are gone now that nothing needs
# them. A course with no `oc` scorer has no criteria checks to expect, which is
# what the empty list means here.
import scorers as _scorers


def oc_check_names(spec: dict) -> list:
    _oc = _scorers.optional("oc")
    return _oc.check_names(spec) if _oc is not None else []


_CRITERIA_CACHE: dict[str, list[str]] = {}


def expected_criteria_checks(spec: dict) -> list[str]:
    """Cached `oc_check_names` — one ledger run per item, not per participant."""
    if spec["id"] not in _CRITERIA_CACHE:
        _CRITERIA_CACHE[spec["id"]] = oc_check_names(spec)
    return _CRITERIA_CACHE[spec["id"]]


def weight(credit: dict) -> str:
    """A credit slot's point value, for a message. None means reported-only."""
    return "none" if credit.get("pts") is None else f"{credit['pts']:g}"


def audit(handout: int, outdir: str | None = None
          ) -> tuple[list[str], int, str]:
    """Return (findings, files seen, outdir) for one handout.

    `outdir` overrides the handout's default, so a caller auditing a snapshot or
    a `--outdir` run checks the directory it is actually reading rather than the
    default one.
    """
    cfg = config(handout)
    by_id = cfg["rubric"].BY_ID
    order = [i["id"] for i in cfg["rubric"].ITEMS]
    outdir = outdir or cfg["outdir"]
    files = sorted(glob.glob(os.path.join(outdir, "participant_*.json")))

    # item -> reason -> True. A reason is reported once however many of the 20
    # cells carry it; the fix is the same re-score either way.
    found: dict[str, dict[str, bool]] = {}
    # item -> slots seen in at least one cell, for the every-cell test below.
    seen_slots: dict[str, set[str]] = {}
    scored_items: set[str] = set()

    def note(iid: str, reason: str) -> None:
        found.setdefault(iid, {})[reason] = True

    # Items score.py handles in `derive_from_criteria` mode do NOT score from the
    # rubric's `credit` list: build_schema gives the model a fixed `oc_analysis`
    # object and the score derives from that, with credit_checks written under
    # names of its own. Comparing those names against `credit` reported all eight
    # of handout 2's operant-conditioning items as stale when none of them were,
    # and acting on it cost a 160-call re-score.
    #
    # They are audited anyway, against `score.oc_check_names(item)` — the names
    # the real ledger writes over a passing sheet. Deriving the expectation by
    # running the code beats listing it: a hand-kept list is what produced the
    # false alarm above, and the criteria set does change (`consequence_asserted`
    # was added to the cadence items).
    for f in files:
        rec = json.load(open(f))
        for it in rec["items"]:
            iid = it["item_id"]
            spec = by_id.get(iid)
            if spec is None:
                note(iid, "item is no longer in the rubric")
                continue
            scored_items.add(iid)
            checks = it.get("credit_checks", [])
            got = {c["what"] for c in checks}
            seen_slots.setdefault(iid, set()).update(got)

            if abs(it.get("max", spec["max"]) - spec["max"]) > 1e-9:
                note(iid, f"scored against max {it['max']:g}, rubric now says "
                          f"{spec['max']:g}")

            if spec.get("derive_from_criteria"):
                # Names come from the ledger, and the DEDUCTION WEIGHTS from the
                # item's own `deductions` table (`add()` reads pts straight from
                # it), so a re-weighting there is checkable exactly as it is for
                # credit-mode items. The rubric's `credit` list is not consulted:
                # for these items it describes the sheet the WEB scores, not this
                # one, which is the confusion that produced the false alarm.
                gone = got - set(expected_criteria_checks(spec))
                if gone:
                    note(iid, f"scored check(s) the criteria ledger no longer "
                              f"writes: {', '.join(sorted(gone))}")
                weights = {d["code"]: d["pts"] for d in spec["deductions"]}
                for d in it.get("deductions", []):
                    now = weights.get(d["code"])
                    if now is None:
                        note(iid, f"charged {d['code']}, which the rubric no "
                                  f"longer defines")
                    elif abs(now - d["pts"]) > 1e-9:
                        note(iid, f"deduction {d['code']} charged {d['pts']:g} "
                                  f"pt(s), rubric now weights it {now:g}")
                continue

            gone = got - {c["what"] for c in spec["credit"]}
            if gone:
                note(iid, f"scored slot(s) the rubric no longer defines: "
                          f"{', '.join(sorted(gone))}")

            for c in spec["credit"]:
                allowed = set(c.get("verdicts") or ())
                if not allowed:
                    continue          # nothing declared to compare against
                for chk in checks:
                    v = chk.get("verdict")
                    if chk.get("what") == c["what"] and v and v not in allowed:
                        note(iid, f"{c['what']}: scored verdict {v!r} is not "
                                  f"one the rubric allows "
                                  f"({', '.join(sorted(allowed))})")

            # What a slot COSTS is not recorded per slot, so a re-weighting is
            # invisible in credit_checks — and that is not a hypothetical: Q4c's
            # keyword slot went to pts=None (reported only, no credit) while its
            # keys, verdicts and max all stayed put. The stored deductions do
            # carry points per code, which is the one place a re-weighting
            # shows. Only codes this rubric still routes through a credit slot
            # are compared; an item-level deduction has no slot to disagree with.
            #
            # Gating slots are excluded, and not as a nicety: a gate costs the
            # WHOLE item, so its deduction is the item max and never the slot's
            # own pts — which is usually None. Comparing them flagged all five
            # gates in the corpus as re-weighted (Q2, D1, D2, 1a, 1c) while the
            # rubric had not touched any of them. 1c's `has_own_graph` shows why
            # the pts value alone cannot decide it: that slot both gates and
            # carries 2, and a failure still charges 10.
            for d in it.get("deductions", []):
                owners = [c for c in spec["credit"]
                          if d["code"] in (c.get("codes") or {}).values()]
                owners = [c for c in owners if not c.get("gates")]
                if not owners:
                    continue
                if all(c.get("pts") is None for c in owners):
                    note(iid, f"deduction {d['code']} charged {d['pts']:g} pt(s), "
                              f"but its slot(s) now carry no credit")
                elif not any(abs((c.get("pts") or 0) - d["pts"]) < 1e-9
                             for c in owners):
                    now = "/".join(weight(c) for c in owners)
                    note(iid, f"deduction {d['code']} charged {d['pts']:g} pt(s), "
                              f"rubric now weights it {now}")

    # A check absent from every cell of an item the run did score. Which set
    # "every check" means depends on the mode, as above.
    for iid in sorted(scored_items):
        spec = by_id[iid]
        if spec.get("derive_from_criteria"):
            want = set(expected_criteria_checks(spec))
            label = "criteria check(s)"
        else:
            want = {c["what"] for c in spec["credit"]}
            label = "rubric slot(s)"
        never = want - seen_slots.get(iid, set())
        if never:
            note(iid, f"{label} no cell scored: {', '.join(sorted(never))}")

    lines = []
    for iid in sorted(found, key=lambda i: order.index(i) if i in order else 99):
        for reason in sorted(found[iid]):
            lines.append(f"  {iid:>5}  {reason}")
    return lines, len(files), outdir


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--handout", type=int, default=None,
                    choices=sorted(HANDOUTS),
                    help="default: check all three")
    ap.add_argument("--outdir", default=None,
                    help="audit this directory instead of the "
                         "handout default; implies --handout")
    args = ap.parse_args()

    if args.outdir and not args.handout:
        ap.error("--outdir needs --handout: the rubric to audit against "
                 "cannot be inferred from a directory")
    handouts = [args.handout] if args.handout else sorted(HANDOUTS)
    rc = 0
    for h in handouts:
        lines, n, outdir = audit(h, args.outdir)
        print(f"\nhandout {h} — {n} stored prediction file(s) in {outdir}")
        if not lines:
            print("  current: every scored cell matches the rubric")
            continue
        rc = 1
        print("\n".join(lines))
        items = sorted({ln.split()[0] for ln in lines})
        print(f"\n  STALE. Re-score with:  python3 score.py --handout {h} "
              f"--items {' '.join(items)}")
    if rc:
        print("\nBaseline numbers built on stale predictions describe a rubric "
              "that no longer exists.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
