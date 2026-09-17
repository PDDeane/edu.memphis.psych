"""Stage 06c · would a check NOTICE if the rubric went away?

KEPT AS A RECORDED NEGATIVE RESULT. It empties the rubric accessor and asks each
rubric-reading check what it does: 43 of 47 return [] and 4 speak. That number
looks alarming and means very little -- emptying a collection silences any check
that ITERATES it, so the probe cannot tell a broken check from a well-behaved
one. It is kept so the next person does not build it again expecting an answer.

WHAT DOES ANSWER THE QUESTION is an injection per check, validated against the
full audit: `stage06c_validate_injections.py`.

06c deletes the rubric modules. The hazard the plan names is a check whose
source has vanished returning [] and reporting success -- green because it
stopped looking. The selftest answers this per check where a case exists; there
are more rubric-reading checks than cases, so this asks the question generally.

For each check that reads the rubric: empty the rubric accessor, call the check,
and record what it does.

  SPEAKS  -- reports a finding, or raises. Either way it cannot be silently green.
  BLIND   -- returns [] with nothing to read. It cannot tell "nothing wrong"
             from "nothing there", which is exactly the condition 06c creates.

BLIND is not automatically a defect -- a check over an empty set may have
nothing true to say -- but it is the set where a vanished source would go
unreported, so it is the set that has to be justified one by one.
"""
import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parent))
import migration_paths as MP
import sys, inspect, re, collections
sys.path.insert(0, str(MP.SCORING))
import enforcement as E, handouts as H

RUBRIC = re.compile(r"rubrics\(\)|SLOT_SPEC|all_items|\bBY_ID\b|\bITEMS\b|\bMAPS\b|\bFRAMES\b|"
                    r"SLOT_OPTIONS|rubric_h[123]|_H_rub|rubric_reader|handouts\.")
checks = []
for n in sorted(d for d in dir(E) if d.startswith("check_")):
    fn = getattr(E, n)
    if not callable(fn): continue
    try:
        if inspect.signature(fn).parameters: continue
        src = inspect.getsource(fn)
    except Exception: continue
    if RUBRIC.search(src): checks.append(n)

class Empty:
    """A rubric with nothing in it, answering every attribute emptily."""
    def __getattr__(self, name):
        if name.isupper(): return {}
        raise AttributeError(name)
    ITEMS = []
    BY_ID = {}

real = H.rubrics
H.rubrics = lambda *a, **k: [Empty(), Empty(), Empty()]
res = collections.Counter(); blind, speaks = [], []
for n in checks:
    try:
        out = getattr(E, n)()
        if out: res["SPEAKS(finding)"] += 1; speaks.append((n, "finding"))
        else:   res["BLIND"] += 1; blind.append(n)
    except SystemExit as e:
        res["SPEAKS(refuses)"] += 1; speaks.append((n, f"SystemExit"))
    except Exception as e:
        res["SPEAKS(raises)"] += 1; speaks.append((n, type(e).__name__))
H.rubrics = real

print(f"  rubric-reading checks probed : {len(checks)}")
for k, v in res.most_common(): print(f"    {k:<18} {v}")
print(f"\n  BLIND on an empty rubric ({len(blind)}):")
for n in blind: print(f"     {n}")
print("C1PROBE_DONE")
