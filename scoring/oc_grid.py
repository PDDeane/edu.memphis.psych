import itertools, json
# THE PLUGIN, not `score`. Goal E: this grid exercises the OC ledger, so it
# belongs with the scorer it exercises rather than with the engine.
import scorers, handouts as H

GATE_KEYS = ("states_a_contingency", "agent_delivers_consequence",
             "aimed_correctly", "avoidance_frame", "targets_own_behavior")
BASE = {"behavior": "b", "stimulus": "s", "contingent": True,
        "follows_behavior": True, "stimulus_is_arranged": True,
        "observed_type": None, "avoidance_frame": False,
        "restriction_authored": "relieved", "trigger_expects": "gain",
        "restricts": "this_behaviour", "named_type": None,
        "cadence_ok": True, "trigger_behavior": "utb",
        "consequence_asserted": True}

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
