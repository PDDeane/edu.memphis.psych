import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parent))
import migration_paths as MP
#!/usr/bin/env python3
"""Stage 07 · every prose mention of a moved structure, classified by tense.

THE PROSE REBASE IS NOT A RENAME. Four .md files are read by code, and they are
also a RECORD. A subgoal log that says "`unclear` was removed from rubric_h1's
verdicts" is describing where the thing was when the entry was written; rewriting
it to match today makes the log agree with the present at the cost of being a
log. Only claims about where a thing IS NOW are false after a move.

So this splits them. It over-reports deliberately -- the tense heuristic is a
three-line window, and several entries read as present tense inside an entry
that is plainly historical -- because a mention wrongly left alone is a false
statement in a file the checks read, and a mention wrongly flagged costs one
glance.

    python3 migration/stage07_prose_mentions.py 'rubric_h[123]'

At 06c/07 this reported 36 mentions in GOALS.md, 3 in EQUIVALENCE.md and 4 in
BACKLOG.md. The GOALS.md ones were left as history under a header note saying
so, except ten present-tense structural claims; EQUIVALENCE.md's three and
BACKLOG.md's four were rebased. BACKLOG.md's were `file:line` citations into
deleted modules -- re-pointed at STRUCTURES, not at new line numbers, which
would be just as fragile the next time the file moves.
"""
import pathlib, re, sys

HOOKINS = ("QUALITY_CONTROL.md", "GOALS.md", "EQUIVALENCE.md", "OVERRIDES.md",
           "BACKLOG.md", "README.md")
PAST = re.compile(r"\b(was|were|had|used to|removed|dropped|then|previously|"
                  r"before|at the time|originally|once|as found|fixed)\b", re.I)

# A REFERENCE IS NOT A MENTION. Since the history rewrite, prose carries corpus
# references -- `[[corpus Q5/p4 first 0:53 sha=...]]` and `{{corpus:...}}` -- and
# a reference naming a cell is a CITATION of student writing, not a claim about
# where a structure lives. Counting one as a present-tense mention sends someone
# to "rebase" a citation, and rebasing it would either resolve it (putting the
# student's words back into the file this mechanism exists to keep them out of)
# or repoint it at the wrong cell. Both are worse than the mention it was
# mistaken for.
#
# They are stripped from the line BEFORE the pattern runs, not skipped whole:
# a line may carry a reference AND a real mention, and dropping the line would
# lose the mention.
REFERENCE = re.compile(r"\[\[corpus [^\]]*\]\]|\{\{corpus:[^}]*\}\}")


def main(pattern, root="."):
    rx = re.compile(pattern)
    for name in HOOKINS:
        p = pathlib.Path(root) / name
        if not p.exists():
            continue
        lines = p.read_text().splitlines()
        hist, pres = [], []
        bare = [REFERENCE.sub(" ", l) for l in lines]
        for i, ln in enumerate(bare, 1):
            if not rx.search(ln):
                continue
            ctx = " ".join(bare[max(0, i - 2):i + 1])
            (hist if PAST.search(ctx) else pres).append((i, lines[i - 1].strip()))
        if not (hist or pres):
            continue
        print(f"\n=== {name}: {len(hist) + len(pres)} mention(s), "
              f"{len(hist)} historical, {len(pres)} present-tense")
        for i, ln in pres:
            print(f"  REBASE? {i}: {ln[:100]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1] if len(sys.argv) > 1 else r"rubric_h[123]",
                          sys.argv[2] if len(sys.argv) > 2 else
                          str(MP.SCORING)))
