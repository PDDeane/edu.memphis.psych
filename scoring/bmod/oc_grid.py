#!/usr/bin/env python3
"""The OC ledger's gate grid: vary one gate at a time and print what changes.

WHY IT IS HERE AND NOT IN `scoring/`. Its own first comment always said so --
*"THE PLUGIN, not `score`. Goal E: this grid exercises the OC ledger, so it
belongs with the scorer it exercises rather than with the engine."* It sat in
the engine anyway, and that cost: thirteen of the ten OC FACT NAMES the
fact-name work is removing from engine code were in this one file, along with
the eight item ids it iterates. Moved 2026-09-25 (step 7), beside `oc.py`,
which it reaches through `scorers.resolve("oc")` already.

AND IT HAS A `__main__` GUARD NOW, which is the other half of MODULE_AUDIT's
finding F2: *"38 lines, no docstring, no functions, no `__main__` guard: its
whole body runs on import and prints a grid to stdout ... importing it for any
reason executes it."* Importing it is now free; running it is deliberate.

    python3 scorers/oc_grid.py
"""
import itertools, json
import scorers, forms as H

GATE_KEYS = ("states_a_contingency", "agent_delivers_consequence",
             "aimed_correctly", "avoidance_frame", "targets_own_behavior")
BASE = {"behavior": "b", "stimulus": "s", "contingent": True,
        "follows_behavior": True, "stimulus_is_arranged": True,
        "observed_type": None, "avoidance_frame": False,
        "restriction_authored": "relieved", "trigger_expects": "gain",
        "restricts": "this_behaviour", "named_type": None,
        "cadence_ok": True, "trigger_behavior": "utb",
        "consequence_asserted": True}


def main() -> int:
    out = []
    for iid in ("DAY1", "DAY2", "WK1", "WK2", "NR", "PR", "PP", "NP"):
        # J-3. WAS config(2) -- the criteria handout, by property.
        item = H.config(H.carrying("derive_from_criteria")[0])["rubric"].BY_ID[iid]
        a0 = dict(BASE)
        a0["observed_type"] = item.get("expected_type") or "NR"
        a0["named_type"] = a0["observed_type"]
        keys = [k for k in GATE_KEYS]
        # vary each gate key alone, plus the polarity conjunction
        variants = [("baseline", {})]
        for k in keys:
            variants.append((f"{k}=False", {k: False}))
        variants.append(("polarity_hit", {"restriction_authored": "created",
                                          "trigger_expects": "gain",
                                          "restricts": "other_thing"}))
        for label, over in variants:
            a = dict(a0); a.update(over)
            try:
                ledger, checks, unknown, advisory = scorers.resolve("oc").derive_ledger(item, {"oc_analysis": a})
                codes = [l.get("code") for l in ledger]
                met = {c["what"]: c["met"] for c in checks}
            except Exception as e:
                codes, met = [f"RAISED {type(e).__name__}"], {}
            out.append((iid, label, codes, sorted(met.items())))
    for row in out:
        print(json.dumps(row, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
