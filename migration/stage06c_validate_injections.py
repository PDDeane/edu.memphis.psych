"""Stage 06c · every injection against the FULL audit, not against its own check.

SAVED FROM THE 06c RUN. Companion to `stage06b_validate_injections.py`, which
validates the sixteen cases written at 06b; this one drives the twenty-eight
written at 06c for the rubric-reading checks that had none. Run it after
touching any injection and before running the suite.

    python3 migration/stage06c_validate_injections.py

It found the one failure a single-check probe could not: an injection that made
`agreement.load_action` raise for EVERY caller. Correct against its own check,
which reports a load failure as a finding; fatal against the audit, where other
checks load sheets too. The fix was to scope the refusal to the frames of the
check under test.

WHY THIS IS THE REAL TEST, in `stage06b_validate_injections`'s own words: a case
does not call its check, it calls `enforcement_audit()`, which scores every item
through both engines -- so an injection has to leave the rubric valid for all of
that. Three of the sixteen cases written at 06b passed their single-check probe
and then took the suite down two cases later, each costing a ~90-minute run to
discover. Every one of the 28 below passes its single-check probe; that is the
weaker claim.

Reports, per injection: FIRED (the audit carries its kind), MISSED (the audit
does not), or CRASHED (the audit could not complete) -- and whether the finding
count came back to baseline afterwards.
"""
import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parent))
import migration_paths as MP
import sys, time, traceback
# THE INJECTIONS SHIP; THEY DO NOT LIVE IN A SCRATCHPAD. This imported
# `inj_lib` from a session scratch directory that also inserted the dry run's
# own `scoring/` on sys.path -- so the validator pulled its `gold`, its `paths`
# and that tree's sandbox guard, and would have died the moment either was
# deleted. The shipped copy is `migration/products/selftest_injections.py`,
# which is the same library after review.
sys.path.insert(0, str(MP.MIGRATION / "products"))
sys.path.insert(0, str(MP.SCORING))
import selftest_injections as inj_lib
import equivalence as Q

def kinds():
    return [str(f[1]) for f in Q.enforcement_audit()[0]]

t0 = time.time()
base = kinds()
print(f"  baseline audit: {len(base)} finding(s)  ({time.time()-t0:.0f}s)", flush=True)

fired, missed, crashed, dirty = [], [], [], []
for i, (name, (kind, factory)) in enumerate(sorted(inj_lib.INJECTIONS.items()), 1):
    try:
        install, restore = factory()
    except Exception as e:
        crashed.append((name, f"setup {type(e).__name__}: {e}")); continue
    try:
        install()
        try:
            got = kinds()
        finally:
            restore()
        after = kinds()
        if kind in got and kind not in base:
            fired.append(name); verdict = "FIRED"
        elif got.count(kind) > base.count(kind):
            fired.append(name); verdict = "FIRED(+n)"
        else:
            missed.append((name, kind)); verdict = "MISSED"
        if sorted(after) != sorted(base):
            dirty.append(name); verdict += " +DIRTY"
    except Exception as e:
        try: restore()
        except Exception: pass
        crashed.append((name, f"{type(e).__name__}: {str(e)[:70]}")); verdict = "CRASHED"
    print(f"  [{i}/28] {verdict:<14} {name}  ({time.time()-t0:.0f}s)", flush=True)

print(f"\n  FIRED against the full audit : {len(fired)}")
print(f"  MISSED                       : {len(missed)}")
for n, k in missed: print(f"      {n} (wanted {k})")
print(f"  CRASHED                      : {len(crashed)}")
for n, why in crashed: print(f"      {n}: {why}")
print(f"  LEFT THE AUDIT DIRTY         : {len(dirty)}")
for n in dirty: print(f"      {n}")
print("VALIDATE28_DONE")
