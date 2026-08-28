#!/usr/bin/env python3
"""Refuse a commit while the two scorers differ in a way nobody has declared.

Installed as .git/hooks/pre-commit. It exists because the rule "run the
enforcement audit before committing" was followed by hand and then not: a change
that WIRED TWO NEW GATES into the scoring path was committed after running the
structural and leakage gates only, and `--enforcement` -- the one that compares
the two sides -- was skipped. It would have refused the commit: the change made
the web compute two checks the CLI still asks the model for, and put a gate on
one side only. Under a goal whose name is enforcing equivalence.

WHAT IT REFUSES: any enforcement finding that is not a measurement-state flag.
`ITEM UNMEASURED AS CONFIGURED` is excluded on purpose -- it says a recorded
number is stale, which is a fact about the ledger rather than a difference
between the scorers, and stale items are a deliberate state here (prompts are
cleaned immediately and swept later, so the ledger stays honest in between).

OVERRIDE: `ALLOW_UNDECLARED="<reason>" git commit ...`. The reason is printed and
required to be non-trivial. An override with no reason is refused, because a
switch that is easier to flip than to explain gets flipped.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_ONLY = ("ITEM UNMEASURED AS CONFIGURED",)


def main() -> int:
    reason = (os.environ.get("ALLOW_UNDECLARED") or "").strip()
    r = subprocess.run([sys.executable, os.path.join(HERE, "equivalence.py"),
                        "--enforcement"], capture_output=True, text=True, cwd=HERE)
    lines = [l for l in (r.stdout + r.stderr).splitlines() if l.startswith("! ")]
    blocking = [l for l in lines if not any(k in l for k in STATE_ONLY)]
    if not blocking:
        state = len(lines) - len(blocking)
        print(f"pre-commit: enforcement audit clean"
              + (f" ({state} stale-measurement flag(s), not blocking)" if state else ""),
              file=sys.stderr)
        return 0
    print("REFUSING the commit: the CLI and web scorers differ and it is not "
          "declared.\n", file=sys.stderr)
    for l in blocking:
        print(f"    {l.strip()}", file=sys.stderr)
    print("\nDeclare it in olx_prompts.SCORING_DIVERGENCES with a reason, or fix "
          "the difference.\nTo commit anyway, say why:\n"
          '    ALLOW_UNDECLARED="..." git commit ...', file=sys.stderr)
    if len(reason) >= 15:
        print(f"\npre-commit: OVERRIDDEN — {reason}", file=sys.stderr)
        return 0
    if reason:
        print(f"\npre-commit: override refused, the reason given is {len(reason)} "
              f"characters. Say what makes this acceptable.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
