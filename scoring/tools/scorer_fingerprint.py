#!/usr/bin/env python3
"""The criteria scorer's behavioural fingerprint, certified as evidence.

WHAT IT IS. The ledger is a pure function of `(item, raw)`, so the whole INPUT
SPACE can be swept without a single model call: every declared fact, every gate
combination, every item. Identical output over that space is identical
behaviour, which is what let goals E and M move fourteen rules between modules
with the ledger provably unchanged.

WHY IT LIVES HERE. It was a scratchpad script for the whole of E and M -- which
meant the only check standing between a refactor and a silent scoring change was
a file that would not survive the session. A safety net nobody can run is not one.

WHY IT GOES THROUGH `certify`. A fingerprint comparison is the exact shape that
failed three times on 2026-09-24: a comparison trusted because it came back
clean. `evidence.certify` refuses to answer until this comparison has been shown
to REPORT A DIFFERENCE on a pair known to differ, so "identical" means the test
could have said otherwise.

    python3 tools/scorer_fingerprint.py --write   # record a baseline
    python3 tools/scorer_fingerprint.py           # certify against it
"""
from __future__ import annotations

import functools
import hashlib
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (HERE, os.path.dirname(HERE)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

BASELINE = os.path.join(HERE, "SCORER_FINGERPRINT.json")

GATE_FACTS = ["behavior", "stimulus", "contingent", "follows_behavior",
              "stimulus_is_arranged"]
# THE FALLBACK ONLY. `_enum` reads each item's own schema and uses this when the
# schema constrains nothing, so these are not the swept values for a fact that
# declares its own. Kept as a last resort rather than a source of truth.
TYPES = ["", "PR", "NR", "PP", "NP"]


@functools.lru_cache(maxsize=1)
def _declared_space() -> tuple[list, dict]:
    """(boolean facts, {enum fact: values}) -- from the SCORERS' OWN SCHEMAS.

    DERIVED, AND THE HARDCODED VERSION WAS WRONG IN THREE WAYS. Measured
    2026-09-25 against what the scorers actually declare:

      * `REST` listed FIVE boolean facts; the schemas declare ELEVEN. The six
        never swept were `agent_delivers_consequence`, `aimed_correctly`,
        `contingent`, `follows_behavior`, `states_a_contingency` and
        `stimulus_is_arranged` -- every one of them a GATE, so the gate paths
        were the part this guard was least covering.
      * `PICKS` held THREE enum facts of the seven declared, missing
        `stimulus_move`, `trigger_behavior` and the two type facts.
      * `MOVES` swept `stimulus_move` over `["", "added", "removed"]` and the
        schema declares `given_desirable / given_undesirable / taken_desirable /
        taken_undesirable`. NOT ONE VALUE OVERLAPPED. The fact was varied over
        values it can never hold, which is precisely the failure this file
        already records finding once: *"the sweep did vary
        `restriction_authored`, so it looked covered. It was varying it over
        values the rule can never match."* The same error, three facts further
        on, and it is why this now reads the schema instead of restating it.

    A FACT NO SCORER DECLARES IS NOT SWEPT, which is the honest limit: this can
    only cover what the schemas expose.

    MEMOISED, AND THAT IS NOT AN OPTIMISATION DETAIL. `_profiles()` is called
    once per case batch -- 6,400 times in a full check -- and this resolves
    every scorer and builds every schema fragment. Uncached it took the check
    from 23s to 69s while sweeping the SAME 115,200 cases, which is a threefold
    cost for no extra coverage. Callers read the result and must not mutate it.
    """
    import coursedata
    import scorers

    bools: list = []
    enums: dict = {}
    for it in coursedata.items():
        try:
            mod = scorers.resolve(scorers.name_for(it))
        except Exception:
            continue
        if not hasattr(mod, "schema_fragment"):
            continue
        try:
            frag = mod.schema_fragment(it)
        except Exception:
            continue
        props = ((frag.get("properties") or {}).get("oc_analysis") or {}).get(
            "properties") or {}
        for k, v in sorted(props.items()):
            if v.get("type") == "boolean":
                if k not in bools:
                    bools.append(k)
            elif v.get("enum"):
                enums.setdefault(k, [])
                for val in v["enum"]:
                    if val not in enums[k]:
                        enums[k].append(val)
    return bools, enums


# THE PER-ITEM FACTS, sweeping of which `_enum` already handles by reading each
# item's schema. Excluded from the cross-product so they are not swept twice
# over a union that no single item admits.
PER_ITEM_FACTS = ("observed_type", "named_type")

# THE PICK-VALUED FACTS ARE DERIVED NOW -- see `_declared_space`. The table that
# stood here is gone; this is the incident it was written for, kept because it
# is the reason the derivation exists.
#
# WITHOUT THE PICKS THIS GUARD WAS BLIND TO THE `forbid` RULES ENTIRELY.
# Measured 2026-09-24: `forbid_hit` fired on 0 of NR's 6400 swept answers,
# because the conditions it reads -- `trigger_expects` and `restricts` -- were
# never swept at all, and `restriction_authored` was fed True/False when the
# fact is a PICK whose values are strings. So a migration of
# `barrier_is_not_this_type` or `consequence_not_a_setup` could change the
# ledger and the fingerprint would still say "reproduces".
#
# A WRONG TYPE IS THE PART WORTH KEEPING IN MIND: the sweep did vary
# `restriction_authored`, so it looked covered. It was varying it over values
# the rule can never match. That is exactly what `stimulus_move` was still
# doing on 2026-09-25, one year of the same mistake later in the same file --
# which is why the values are no longer written here at all.


def _profiles():
    """18 profiles: every pick-combination, against varied booleans and moves.

    DELIBERATELY NOT THE FULL CARTESIAN. Crossing all 18 pick-combinations with
    the 8 boolean profiles would be 921,600 cases and ~18x the runtime of a check
    that runs in every audit. Instead each of the 18 combinations carries its own
    boolean/move profile, so every pick value is exercised and the booleans still
    vary across them. What that does NOT cover: a bug needing one SPECIFIC
    boolean profile together with one SPECIFIC pick combination. Said here rather
    than left for someone to infer from the case count.
    """
    rest, enums = _declared_space()
    enums = {k: v for k, v in enums.items() if k not in PER_ITEM_FACTS}

    # BOUNDED THE SAME WAY IT ALWAYS WAS. Full cartesian over all seven enum
    # facts is 216 profiles against today's 18, and this check runs in every
    # audit at 23s -- so the cross-product keeps the budget it had and the rest
    # are ROUND-ROBINED across the profiles it produces. Every value of every
    # declared fact is still exercised; what is not covered is a bug needing one
    # specific combination of a round-robined fact with a crossed one, which is
    # the same class of gap the paragraph above already declares.
    # SMALLEST CARDINALITY FIRST, which is not a detail. Taking the facts in
    # declaration order crossed `stimulus_move` (4) with `restriction_authored`
    # (3), spent the budget at 12, and spun the other three -- covering 6 of the
    # 18 pick-combinations this check had always crossed. A COVERAGE LOSS
    # disguised as a widening, caught by comparing against the old set rather
    # than by trusting the new one. Ascending order fits the most facts into a
    # fixed budget, and here it reproduces the historical 18 exactly.
    cross, spin, budget = {}, {}, 1
    for k, vals in sorted(enums.items(), key=lambda kv: (len(kv[1]), kv[0])):
        if budget * max(1, len(vals)) <= _CROSS_BUDGET:
            cross[k] = vals
            budget *= max(1, len(vals))
        else:
            spin[k] = vals

    combos = list(itertools.product(*cross.values())) or [()]
    out = []
    for i, combo in enumerate(combos):
        p = {f: bool(i >> (n % 3) & 1) for n, f in enumerate(rest)}
        p.update(dict(zip(cross, combo)))
        for k, vals in spin.items():
            p[k] = vals[i % len(vals)]
        out.append(p)
    return out


# How many crossed combinations the profile set may reach before the remaining
# facts are round-robined instead. 18 was the figure this check was built and
# timed at; the budget is stated so raising it is a decision, not a drift.
_CROSS_BUDGET = 18


def _enum(oc, item: dict, fact: str) -> list:
    """The values this item's schema admits for `fact`, cached per item.

    Falls back to the shared `TYPES` for a fact the schema does not constrain,
    so an item that asks something open still gets swept.
    """
    key = (item.get("id"), fact)
    if key not in _ENUM_CACHE:
        props = oc.schema_fragment(item)["properties"]["oc_analysis"]["properties"]
        _ENUM_CACHE[key] = list((props.get(fact) or {}).get("enum") or TYPES)
    return _ENUM_CACHE[key]


_ENUM_CACHE: dict = {}


def _asked(oc, item: dict) -> frozenset:
    """The fact names this item's own schema asks for, cached per item.

    The scorer publishes its schema per item; reading it here keeps the sweep
    honest about what an answer can contain instead of assuming one shape for
    all eight.
    """
    key = item.get("id")
    if key not in _ASKED_CACHE:
        props = oc.schema_fragment(item)["properties"]["oc_analysis"]["properties"]
        _ASKED_CACHE[key] = frozenset(props)
    return _ASKED_CACHE[key]


_ASKED_CACHE: dict = {}


def sweep() -> list:
    """Every (item, answer) the declared facts allow, and what the ledger says."""
    import coursedata
    import scorers

    oc = scorers.optional("oc")
    if oc is None:
        return []
    items = {it["id"]: it for it in coursedata.items()
             if it.get("derive_from_criteria")}
    rows = []
    for iid in sorted(items):
        item = items[iid]
        for bits in itertools.product([False, True], repeat=len(GATE_FACTS)):
            # EACH FACT'S OWN DECLARED ENUM, not one shared list. The shared
            # `TYPES` offered `""` for both, which neither slot admits, and
            # never produced `none` or `unclear` -- which the schema does admit
            # and which are the values that MATTER: `unclear` is the lenient
            # value the equals rule exists to forgive, so the guard could not
            # tell a correct lenient list from an empty one. Measured: emptying
            # it changed nothing.
            for obs, named in itertools.product(_enum(oc, item, "observed_type"),
                                                _enum(oc, item, "named_type")):
                for prof in _profiles():
                    a = dict(prof)
                    for f, b in zip(GATE_FACTS, bits):
                        a[f] = ("x" if b else "") if f in ("behavior", "stimulus") else b
                    a["observed_type"], a["named_type"] = obs, named
                    # ONLY THE FACTS THIS ITEM ACTUALLY ASKS. The sweep built one
                    # fact set for every item, so it fed `stimulus_move` to
                    # NR/PP/NP -- which never ask for it (`if
                    # item.get("move_pick")`, true on PR alone). Those rows are
                    # states the shipped prompt cannot produce, and they are not
                    # harmless: they made a fix to `demonstrates_type` look like a
                    # 5,760-row behaviour change when every changed row was
                    # unreachable. A guard that reports differences in states the
                    # system cannot enter spends its credibility on noise.
                    a = {k: v for k, v in a.items() if k in _asked(oc, item)}
                    led, chk, unk, adv = oc.derive_ledger(item, {"oc_analysis": a})
                    rows.append([iid, sorted(a.items()), led, chk, sorted(unk), adv])
    return rows


def digest(rows=None) -> str:
    blob = json.dumps(rows if rows is not None else sweep(),
                      sort_keys=True, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()


def check() -> list[str]:
    """-> findings. Empty when the scorer reproduces its recorded behaviour."""
    from evidence import NotEvidence, certify

    if not os.path.exists(BASELINE):
        return []                    # not yet baselined; `--write` records one
    want = json.load(open(BASELINE))
    rows = sweep()
    if not rows:
        return []                    # no criteria scorer in this course
    got = digest(rows)
    # THE CONTROL: the same comparison, on a ledger with one charge removed. If
    # it cannot see that, "identical" would mean nothing.
    bent = [r[:2] + [[]] + r[3:] for r in rows]
    try:
        same = certify("scorer fingerprint", got, want["sha256"],
                       must_differ=(got, digest(bent)))
    except NotEvidence as exc:
        return [f"the fingerprint comparison is not evidence: {exc}"]
    if same:
        return []
    return [f"the criteria scorer's behaviour CHANGED: recorded "
            f"{want['sha256'][:16]}, now {got[:16]}. {want['cases']} cases were "
            f"swept when this was recorded. If the change is intended, re-record "
            f"with `--write` and say what moved; if not, the ledger just moved "
            f"under a refactor that was supposed to preserve it."]


def main(argv) -> int:
    if "--write" in argv:
        # THE RECORD CARRIES ITS OWN ACCOUNT. The refusal message asks the writer
        # to "say what moved", and until now there was nowhere to say it: the
        # next reader met a changed sha with no explanation and no way to tell a
        # deliberate migration from a regression that someone re-recorded to make
        # the check quiet. `--why` is required for that reason.
        why = ""
        if "--why" in argv:
            why = argv[argv.index("--why") + 1]
        if not why.strip():
            print("  REFUSING to re-record without --why: a baseline that cannot "
                  "say what moved cannot be told from one that hid it")
            return 1
        rows = sweep()
        json.dump({"sha256": digest(rows), "cases": len(rows), "moved": why},
                  open(BASELINE, "w"), indent=1)
        print(f"  recorded {len(rows)} cases, sha256 {digest(rows)[:16]}")
        print(f"  moved: {why}")
        return 0
    bad = check()
    for b in bad:
        print("  " + b)
    print("  fingerprint reproduces" if not bad else "  FINGERPRINT MOVED")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
