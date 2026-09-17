import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parent))
import migration_paths as MP
#!/usr/bin/env python3
"""Does the rubric OBJECT say everything the rubric MODULES say?

This is stage 05's precondition and the check stage 04 could not make. Stage 04
proved the prompt bodies byte-equal, which exercises only the fields a prompt
reads; on its first run this found 107 omissions across 18 fields and zero
contradictions, which is what made the gap safe to close by adding.

IT OWNS NO COMPARISON OF ITS OWN. The walk lives in `rubric_reader.differences`
because `handouts` runs it at import in `dual` mode, and a second copy here
would be a second opinion about whether the two rubrics agree -- which is the
one thing this must not have. It had one for a day, and the day it drifted was
the day the reader learned to keep bookkeeping on an item: the runtime check
said "equal" and the gate said "not equivalent", about the same two rubrics.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(MP.SCORING))
import rubric_reader  # noqa: E402
import handouts as H  # noqa: E402


def main() -> int:
    total = 0
    for h in (1, 2, 3):
        module = getattr(H.config(h)["rubric"], "_module", H.config(h)["rubric"])
        diff = rubric_reader.differences(module, rubric_reader.rubric_object(h))
        total += len(diff)
        print(f"  h{h}: {len(diff)} difference(s)")
        for d in diff[:12]:
            print("     ", d)
    print()
    print("PASS  the rubric object says everything the modules say" if not total
          else f"FAIL  {total} difference(s) between the rubric object and the modules")
    return 0 if not total else 1


if __name__ == "__main__":
    raise SystemExit(main())
