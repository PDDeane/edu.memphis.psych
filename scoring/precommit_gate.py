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

AND THE OVERRIDE IS RECORDED, added 2026-09-04. Until then the reason was printed
to stderr and then gone: not in the commit, not in a file, not in git. Seven
commits were waved through in one day and the only way to answer "what did we
wave through, and why?" was to ask the person who had typed it. A gate careful
enough to demand a non-trivial reason and then discard it is keeping the ceremony
and losing the evidence.

The record goes into OVERRIDES.md and is STAGED INTO THE SAME COMMIT it excuses,
so the exception travels with the change rather than sitting beside it -- `git
log -p OVERRIDES.md` then reads as the history of what the audit was asked to
ignore. It records the findings VERBATIM, not just the reason: a reason written
about four findings is not evidence about a fifth that appeared with it.
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_ONLY = ("ITEM UNMEASURED AS CONFIGURED",)
LOG = os.path.join(HERE, "OVERRIDES.md")


def _record(blocking: list[str], state: list[str], reason: str) -> str:
    """Append the override to OVERRIDES.md and stage it. Returns a status line.

    Staging is deliberate: an override recorded in the WORKING TREE only would be
    committed later, or never, and would drift away from the change it excuses.
    If staging fails the commit still proceeds -- refusing here would turn a
    bookkeeping problem into a blocked commit, which is the wrong trade -- but it
    says so loudly, because an unrecorded override is the state this exists to end.
    """
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                          capture_output=True, text=True, cwd=HERE).stdout.strip()
    stamp = time.strftime("%Y-%m-%d %H:%M:%S")
    entry = [f"\n## {stamp}  (parent {head or 'unknown'})\n",
             f"\n**Reason given:** {reason}\n",
             f"\n**Findings waved through ({len(blocking)}):**\n\n"]
    entry += [f"- `{l.strip()}`\n" for l in blocking]
    if state:
        entry.append(f"\n{len(state)} non-blocking measurement-state flag(s) also "
                     f"present; those are excluded by design and are not overrides.\n")
    try:
        new = not os.path.exists(LOG)
        with open(LOG, "a") as fh:
            if new:
                fh.write("# Overrides of the enforcement gate\n\nEvery commit that "
                         "used `ALLOW_UNDECLARED`, with the findings it waved through "
                         "and the reason given. Entries are written by "
                         "precommit_gate.py and are never rewritten.\n\nA reason can "
                         "turn out to be wrong -- the first one recorded here was -- "
                         "so CORRECTIONS ARE APPENDED as their own dated section "
                         "under the entry they correct. What was believed at the time "
                         "and what turned out to be true both stay on the record; "
                         "editing an entry to make it right afterwards would destroy "
                         "the only evidence that anyone was ever mistaken.\n")
            fh.writelines(entry)
        add = subprocess.run(["git", "add", LOG], capture_output=True, text=True, cwd=HERE)
        if add.returncode:
            return f"WARNING: recorded in {os.path.basename(LOG)} but could not stage it"
        return f"recorded in {os.path.basename(LOG)} and staged into this commit"
    except OSError as exc:
        return f"WARNING: could NOT record this override ({exc})"


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
        state = [l for l in lines if l not in blocking]
        status = _record(blocking, state, reason)
        print(f"\npre-commit: OVERRIDDEN — {reason}", file=sys.stderr)
        print(f"pre-commit: {status}", file=sys.stderr)
        return 0
    if reason:
        print(f"\npre-commit: override refused, the reason given is {len(reason)} "
              f"characters. Say what makes this acceptable.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
