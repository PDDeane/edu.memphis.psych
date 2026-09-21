#!/usr/bin/env python3
"""Refuse a divergence between the two corpus-reference resolvers.

ONE GRAMMAR, TWO IMPLEMENTATIONS. `scoring/corpus_resolve.py` resolves
references when the scorer reads a file; `lo-blocks/packages/shared/scripts/
resolveCorpusRefs.ts` resolves them when the site is built. Nothing checked they
agreed, and on 2026-09-15 they stopped: `shape=` and `alt=` were added to the
Python grammar and not to the TypeScript one.

THE FAILURE WAS SILENT, WHICH IS WHY THIS EXISTS. The TS regex requires `}}`
straight after `sha=`, so a reference carrying a shape did not match at all. The
build reported "0 file(s) with references" and passed -- and would have copied a
literal `{{corpus:...}}` into the page a student reads. A reference that fails
loudly is a bug; one that silently ships its own source text is worse.

Two questions, because either alone can pass while the pair is broken:

  1. does the TS regex accept every optional field the Python one does?
  2. do both produce the SAME TEXT for the same reference and data?

The second needs `tsx`; where it is unavailable the check says so rather than
reporting success it has not earned.
"""
import json, os, re, subprocess, sys, tempfile, pathlib

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
TS_FILE = TS / "packages/shared/scripts/resolveCorpusRefs.ts"


def _fields(text, pattern):
    return set(re.findall(pattern, text))


def check() -> list:
    out = []
    sys.path.insert(0, str(HERE))
    import corpus_resolve as CR
    py_fields = set(CR.PROSE.groupindex) | set(CR.OLX.groupindex)
    if not TS_FILE.exists():
        return [f"the TypeScript resolver is not at {TS_FILE}; set $LO_BLOCKS. "
                f"This check cannot run, which is not the same as passing"]
    ts_src = TS_FILE.read_text()
    m = re.search(r"export const CORPUS_REF\s*=\s*\n?\s*(/.*?/g);", ts_src, re.S)
    if not m:
        return ["could not find CORPUS_REF in the TypeScript resolver"]
    ts_re = m.group(1)
    for field in sorted(py_fields - {"item", "pid", "field", "a", "b"}):
        if f"{field}=" not in ts_re:
            out.append(
                f"the Python grammar accepts `{field}=` and the TypeScript one "
                f"does not, so a reference carrying it will not match at build "
                f"time -- the build reports no references and ships the literal "
                f"`{{{{corpus:...}}}}` to the page")
    return out


def cross_check(cases_path=None) -> list:
    """Both implementations, same input, compared. Needs tsx."""
    sys.path.insert(0, str(HERE))
    import corpus_resolve as CR
    tsx = TS / "node_modules/.bin/tsx"
    if not tsx.exists():
        return [f"tsx is not installed at {tsx}; the text-equality half of this "
                f"check did not run"]
    data = CR.load()
    cases = [k for k in data][:60]
    refs = [f"{{{{corpus:{k}:sha={CR.sha12(data[k])}}}}}" for k in cases]
    refs += [f"{{{{corpus:{k}:sha={CR.sha12(data[k])}:shape=C1}}}}" for k in cases[:20]]
    with tempfile.TemporaryDirectory() as td:
        inp = pathlib.Path(td) / "in.json"
        inp.write_text(json.dumps({"data": data, "cases": [{"ref": r} for r in refs]}))
        drv = pathlib.Path(td) / "d.ts"
        drv.write_text(
            "import { readFileSync } from 'fs';\n"
            f"import {{ resolve }} from '{TS_FILE}';\n"
            "const i = JSON.parse(readFileSync(process.argv[2], 'utf8'));\n"
            "const o: string[] = [];\n"
            "for (const c of i.cases) { try { o.push(resolve(c.ref, i.data, 't')); }\n"
            "  catch (e: any) { o.push('ERROR'); } }\n"
            "process.stdout.write(JSON.stringify(o));\n")
        r = subprocess.run([str(tsx), str(drv), str(inp)], capture_output=True,
                           text=True, cwd=str(TS), timeout=300)
        if r.returncode != 0:
            return [f"the TypeScript resolver would not run: {r.stderr[:160]}"]
        ts_out = json.loads(r.stdout)
    bad = []
    for ref, got in zip(refs, ts_out):
        try:
            want = CR.expand(ref, data, "check")
        except SystemExit:
            want = "ERROR"
        if want != got:
            bad.append(f"the two resolvers disagree on {ref[:64]}: python "
                       f"{want[:40]!r}, typescript {got[:40]!r}")
    return bad[:8]


if __name__ == "__main__":
    bad = check() + cross_check()
    for b in bad:
        print("  " + b)
    print(f"  {len(bad)} finding(s)")
    raise SystemExit(1 if bad else 0)
