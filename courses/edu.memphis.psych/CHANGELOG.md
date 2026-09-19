# edu.memphis.psych — scoring changelog

**What this file is for.** F1 says no course-derived sentence survives in the
engine's general prose, and §10.3.2 sorts each such sentence into one of three
outcomes: *specification* moves to the course file, *incident* moves here, and a
*split* sentence leaves its generic half in the engine and sends the instance
here.

**Why it had to exist before any sentence moved.** F1 named "the project
changelog" and no such file existed — nothing in the repository carried one and
the plan gave no path. A gate that strips sentences from docstrings while their
destination is undefined produces DELETIONS, not moves, and the evidence in those
sentences is the part most worth keeping. *"Handout 1's items were once reported
as 12/14 and 14/15 while their denominators were 19 and 20"* is a recorded
defect, not decoration.

**Where it lives, and why here.** With the course material it describes, under
`courses/<course-id>/`. An incident in THIS course's scoring is course-specific
by construction: another course would have its own, and the engine should carry
neither.

## The rules an entry follows

1. **Keep the date and the numbers.** A generic retelling loses the evidence,
   and the evidence is the reason the sentence was worth moving rather than
   deleting.
2. **Name the cell, the item or the slot** the incident is about, so the entry
   can be found by someone looking at that cell rather than only by someone
   reading the changelog.
3. **Say what was believed, what was true, and how the gap was closed** — an
   incident with no resolution is an open defect and belongs in `GOALS.md`, not
   here.
4. **One entry per incident.** Two incidents that shared a cause are still two
   entries, cross-referenced; merging them loses which one the evidence came
   from.

## Entries

*None yet. Stage 7's split has not run, so no sentence has been moved. This file
exists so that the split can move sentences rather than delete them, which is the
order §10.3.2 requires and the reason it is created first.*
