#!/usr/bin/env python3
"""Refuse a divergence between the two slot-sheet parsers.

ONE GRAMMAR, TWO IMPLEMENTATIONS -- AGAIN. `olx_prompts.parse_slots` reads the
`slots=` attribute when the scorer builds a prompt; `parseSlots` in
`lo-blocks/packages/shared/lib/llm/slotSheet.ts` reads the same attribute when
the page is rendered. `olx_prompts`' own docstring says it MIRRORS that file,
which is a promise nothing was checking.

WHY IT MATTERS NOW. The attribute is `name:description:verdicts@weight`, split
on every colon, and a corpus reference is colon-heavy by construction:

    modify_stated:Says whether it is {{corpus:Q4b/p20:modify:17:40:sha=...}}

shifts every later field, so the verdict list comes out as `Q4b`/`p20` instead
of `met`/`absent`. The Python side was fixed on 2026-09-16 by hiding a
reference's colons for the duration of the split. **If the TypeScript side is
not fixed the same way, the grader and the student see different verdict
vocabularies for the same slot** -- each internally consistent, neither
complaining. That is the exact shape of the failure `check_ref_grammars.py`
exists to prevent, one grammar over.

This is the companion check. It needs `tsx`; where that is unavailable it says
so rather than reporting a pass it has not earned.
"""
import json
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
# THROUGH paths.LO, NOT A SECOND COPY OF IT. This line was `paths.LO` as it
# stood before 2026-09-20, duplicated here -- so it honours $LO_BLOCKS but
# knows nothing of the `.lo-blocks` marker, and this checkout's gate read
# TypeScript out of the LIVE tree while everything else read its own. It
# also RAN live's `node_modules/.bin/tsx` with cwd set to the live root.
# Identical bytes at the time, so nothing was wrong -- right by coincidence,
# which is the thing `paths.py` exists to stop.
import paths as _paths
TS = _paths.LO
SLOTSHEET = TS / "packages/shared/lib/llm/slotSheet.ts"

# Specs chosen so each isolates one thing. The reference cases are the point;
# the plain ones are the control -- if those diverge, the divergence is not
# about references and this check must say which.
PROBES = [
    "utb_stated:States the behaviour:met/absent@1",
    "harms_listed:How many harms:3/2/1/0@2",
    "modify_stated:Says whether it is a good choice to modify:met/absent@2",
    "reason_1:First reason {{corpus:Q5/p4:first:0:53:sha=e4fd18eaab99}}:met/absent",
    "a:b:met/absent",
    "goal_specific:A goal with a colon: like this:met/absent@1.5",
    "two_refs:{{corpus:Q1/p1:response:0:41:sha=c874ac86a7b2}} and My unwanted target behavior:met/absent",
]

# THE DRIVER MOVED TO lo-blocks. Goal K, 2026-09-25. It was a TypeScript
# literal written to a temp file at run time: `tsc --noEmit` never saw it,
# no test exercised it, and it imported slotSheet by ABSOLUTE path. A
# driver that will not compile reports as "the TypeScript driver failed",
# which is indistinguishable from the divergence this check exists to
# find. It is now `enforce/probes.parseSlotSpecs`, typechecked and under
# vitest, reached by name through `lo_enforce.probe`.


def python_side():
    sys.path.insert(0, str(HERE))
    import olx_prompts as O
    out = []
    for spec in PROBES:
        got = O.parse_slots(spec, ["met", "absent"])
        out.append([{"key": d.get("key"), "label": d.get("label"),
                     "options": d.get("options"), "points": d.get("points")}
                    for d in got])
    return out


def ts_side():
    """The TypeScript parse of the same probes, or why it could not be had."""
    sys.path.insert(0, str(HERE))
    import lo_enforce

    try:
        return lo_enforce.probe("parse_slot_specs",
                                {"specs": PROBES,
                                 "defaults": ["met", "absent"]}), ""
    except lo_enforce.ProbeFailed as e:
        # REPORTED, NOT SWALLOWED. Being unable to ask the other parser is not
        # the same as the two parsers agreeing, and this check has always said
        # so in as many words.
        return None, str(e)


def main() -> int:
    py = python_side()
    ts, why = ts_side()
    findings = []
    if ts is None:
        findings.append(why)
    else:
        for spec, a, b in zip(PROBES, py, ts):
            if a != b:
                findings.append(
                    f"the parsers disagree on {spec[:60]!r}\n"
                    f"      python: {a}\n"
                    f"      ts    : {b}")
    for f in findings:
        print(f"  {f}")
    print(f"  {len(findings)} finding(s)")
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
