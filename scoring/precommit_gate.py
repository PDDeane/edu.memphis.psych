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
import json as _json
import os
import re as _re
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



# ---------------------------------------------------------------------------
# STUDENT TEXT, RATCHETED.
#
# `.gitignore` blocks the corpus by PATH and says so in its own header: those
# rules are "a backstop for an accidental `cp` or `git add -A`, not the primary
# control". They cannot see a student sentence QUOTED INTO PROSE, and that is
# how 434 of them accumulated -- 371 in `scoring/`, across twenty files, none of
# it caught by anything. A write-up quoting the answer it is reasoning about is
# the most natural thing in the world to write and the easiest to not notice.
#
# This does NOT demand zero. Removing what is already there is a separate job
# with a real hazard in it -- 99 of those strings are FIXTURE DATA that the
# ledger was measured on, and rewording one silently changes what was scored.
# So the rule is the one the other budgets here use: the count may fall and may
# not rise. A commit that adds a quote to a file is refused; a commit that
# removes one lowers the bar behind itself and stages the new bar with the
# change, so the ratchet cannot be quietly let out later.
#
# .olx IS EXCLUDED EVERYWHERE, BY FILE TYPE AND NOT BY LOCATION. An .olx file
# is course content: it is what gets rendered TO the student, so student-facing
# language in it is the point. "I continue to [UTB] because X" and "My goal is
# Specific because..." are authored templates, not anybody's answer. The rule is
# about the file type rather than a directory on purpose -- scoping it to
# `psychology/` would start refusing the day course content is authored anywhere
# else, which is exactly what the refactor plan proposes to do.
#
# EXCLUDED_SUFFIXES is the one place to say this. The allowlist below already
# happened to skip .olx, but only as a side effect of naming the three types it
# does read, which is the kind of correct-by-accident that trap T32 was about.
BUDGET = os.path.join(HERE, "STUDENT_TEXT_BUDGET.json")
EXCLUDED_SUFFIXES = (".olx",)          # course content: student-facing by design
SCANNED_SUFFIXES = (".py", ".md", ".json")
_VOICE = _re.compile(r"\b(I |I'm|I am|my |My |me |myself)")
_TECH = _re.compile(r"[_{}=<>|\\]|\b(sha|slot|item|check|audit|rubric|verdict|"
                    r"gold|cell|sweep|prompt|olx|py|json|md)\b", _re.I)


def _quotes(raw: str) -> set:
    """Quoted first-person sentences, found across line breaks.

    Normalised before matching, and that is the whole trick. A line-based grep
    for these missed most of them: the quotes wrap, and in .py they are split
    across adjacent string literals, so `"I continue to " "not sleep enough"`
    contains neither half as a searchable phrase. Joining the seams first took
    one file's count from 1 to 3.
    """
    n = _re.sub(r'"\s*(?:#[^\n]*)?\n\s*"', "", raw)    # "abc" \n "def" -> "abcdef"
    n = _re.sub(r"\s*\n\s*(?:#\s*)?", " ", n)          # unwrap, drop comment marks
    n = _re.sub(r"\s+", " ", n)
    out = set()
    for m in _re.finditer(r'["\u201c\u201d\']([^"\u201c\u201d\']{25,220}?)["\u201c\u201d\']', n):
        s = m.group(1).strip()
        if _VOICE.search(s) and not _TECH.search(s) and s.count(" ") >= 4:
            out.add(s[:160])
    return out


def _staged_counts() -> dict:
    """Per-file counts of what is ABOUT TO BE COMMITTED, not what is on disk.

    Reads each blob from the index (`git show :path`). Checking the working tree
    would let an unstaged edit hide a quote that the commit still carries.
    """
    files = subprocess.run(["git", "diff", "--cached", "--name-only",
                            "--diff-filter=ACMR"],
                           capture_output=True, text=True, cwd=HERE).stdout.split()
    counts = {}
    for f in files:
        if f.endswith(EXCLUDED_SUFFIXES) or not f.endswith(SCANNED_SUFFIXES):
            continue
        blob = subprocess.run(["git", "show", f":{f}"],
                              capture_output=True, text=True, cwd=HERE)
        if blob.returncode:
            continue
        n = len(_quotes(blob.stdout))
        if n:
            counts[f] = n
    return counts


def _student_text_gate() -> int:
    """0 to proceed. Runs BEFORE the audit: it is instant and the audit is not."""
    try:
        with open(BUDGET) as fh:
            base = _json.load(fh)
    except FileNotFoundError:
        return 0                      # not yet baselined; `--baseline` writes it
    now = _staged_counts()
    grew = {f: (base.get(f, 0), n) for f, n in now.items() if n > base.get(f, 0)}
    if grew:
        print("REFUSING the commit: it adds student text to the repo.\n",
              file=sys.stderr)
        for f, (was, is_) in sorted(grew.items()):
            print(f"    {f}: {was} -> {is_}", file=sys.stderr)
            blob = subprocess.run(["git", "show", f":{f}"], capture_output=True,
                                  text=True, cwd=HERE).stdout
            for s in sorted(_quotes(blob))[:3]:
                print(f"        {s[:110]!r}", file=sys.stderr)
        print("\nQuote the CELL, not the answer -- `Q5/p4's first entry` says "
              "everything\n`\"I continue sleep enough...\"` says, without "
              "carrying a student's words.\nTo commit anyway, say why:\n"
              '    ALLOW_STUDENT_TEXT="..." git commit ...', file=sys.stderr)
        why = (os.environ.get("ALLOW_STUDENT_TEXT") or "").strip()
        if len(why) < 15:
            if why:
                print(f"\npre-commit: override refused, the reason given is "
                      f"{len(why)} characters.", file=sys.stderr)
            return 1
        print(f"\npre-commit: student-text gate OVERRIDDEN -- {why}",
              file=sys.stderr)
    # The ratchet only ever tightens. A commit that REMOVES quotes lowers the
    # bar and stages the new bar with it, so the reduction cannot be undone by a
    # later commit without tripping the gate.
    lowered = {f: (base[f], now.get(f, 0)) for f in base
               if now.get(f, base[f]) < base[f]}
    if lowered:
        new = dict(base)
        for f, (_, n) in lowered.items():
            if n:
                new[f] = n
            else:
                new.pop(f, None)
        for f, n in now.items():
            new[f] = max(n, new.get(f, 0)) if f in grew else new.get(f, n)
        with open(BUDGET, "w") as fh:
            _json.dump(dict(sorted(new.items())), fh, indent=1)
            fh.write("\n")
        subprocess.run(["git", "add", BUDGET], cwd=HERE)
        total = sum(lowered[f][0] - lowered[f][1] for f in lowered)
        print(f"pre-commit: student-text budget lowered by {total} across "
              f"{len(lowered)} file(s)", file=sys.stderr)
    return 0


def main() -> int:
    if _student_text_gate():
        return 1
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
