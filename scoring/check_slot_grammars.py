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
TS = pathlib.Path(os.environ.get("LO_BLOCKS", pathlib.Path.home() / "code/update/lo-blocks"))
SLOTSHEET = TS / "packages/shared/lib/llm/slotSheet.ts"

# Specs chosen so each isolates one thing. The reference cases are the point;
# the plain ones are the control -- if those diverge, the divergence is not
# about references and this check must say which.
PROBES = [
    "utb_stated:States the behaviour:met/absent@1",
    "harms_listed:How many harms:3/2/1/0@2",
    "modify_stated:Says whether it is {{corpus:Q4b/p20:modify:17:40:sha=f3f224b807af}}:met/absent@2",
    "reason_1:First reason {{corpus:Q5/p4:first:0:53:sha=e4fd18eaab99}}:met/absent",
    "a:b:met/absent",
    "goal_specific:A goal with a colon: like this:met/absent@1.5",
    "two_refs:{{corpus:Q1/p1:response:0:41:sha=c874ac86a7b2}} and {{corpus:Q1/p3:response:0:27:sha=c8e59699d1a0}}:met/absent",
]

DRIVER = """
import { parseSlots } from '%s';
const probes = JSON.parse(process.argv[2]);
const out = probes.map((s: string) => {
  const r = parseSlots(s, ['met', 'absent']);
  return r.map((d: any) => ({ key: d.key ?? null, label: d.label ?? null,
                              options: d.options ?? null, points: d.points ?? null }));
});
console.log(JSON.stringify(out));
"""


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
    tsx = TS / "node_modules/.bin/tsx"
    if not tsx.exists():
        return None, (f"tsx is not installed at {tsx}; this check cannot compare "
                      f"the two parsers, which is NOT the same as their agreeing")
    if not SLOTSHEET.exists():
        return None, f"{SLOTSHEET} does not exist"
    with tempfile.TemporaryDirectory() as d:
        drv = pathlib.Path(d) / "probe_slots.ts"
        drv.write_text(DRIVER % str(SLOTSHEET).replace(".ts", ""))
        r = subprocess.run([str(tsx), str(drv), json.dumps(PROBES)],
                           cwd=str(TS), capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            return None, f"the TypeScript driver failed: {(r.stderr or '').strip()[:200]}"
        try:
            return json.loads(r.stdout.strip().splitlines()[-1]), ""
        except Exception as e:
            return None, f"could not read the TypeScript output ({e}): {r.stdout[:150]}"


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
