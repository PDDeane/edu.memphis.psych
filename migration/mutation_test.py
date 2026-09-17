import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parent))
import migration_paths as MP
#!/usr/bin/env python3
"""The O5 mutation harness: does a test suite actually FAIL when the code breaks?

`stage02_gate.py --mutation-report` reads this script's OUTPUT, so the two
travel together -- a gate that reads a report nobody can regenerate is a gate
reading a fossil.

It copies the modules under test into a throwaway directory, injects one defect
at a time, runs the copied suite, and restores immediately. MUTATING A COPY is
not fastidiousness: restoring an original moves its mtime, and a staleness guard
elsewhere in this project once cried stale mid-sweep because of exactly that.

IT REPORTS "not applied" SEPARATELY FROM "survived". A mutation whose anchor no
longer matches injects nothing and proves nothing; counting it as caught is how
a mutation suite quietly stops testing. Three did exactly that on 2026-09-13.
"""
from pathlib import Path
M = MP.LO_BLOCKS / "packages/shared/lib/llm/__mutation__"
ROOT = MP.LO_BLOCKS
PRISTINE = {f: (M / f).read_text() for f in
            ("attributeAssembler.ts", "promptAssembler.ts")}

MUTATIONS = [
 ("attr: empty list yields '' not null (absent vs empty)", "attributeAssembler.ts",
  "const joinRules = (xs: string[]): string | null => xs.length ? xs.join('|') : null",
  "const joinRules = (xs: string[]): string | null => xs.join('|')"),
 ("attr: counts joins members with the wrong separator", "attributeAssembler.ts",
  "`${r.key}:${r.slots.join(',')}`", "`${r.key}:${r.slots.join(';')}`"),
 ("attr: requires always appends a lenient segment", "attributeAssembler.ts",
  "    `${r.key}:${r.cond}` + (r.lenient?.length ? ':' + r.lenient.join(',') : '')))",
  "    `${r.key}:${r.cond}` + ':' + (r.lenient ?? []).join(',')))"),
 ("attr: maps drops the fallback wildcard", "attributeAssembler.ts",
  "if (r.fallback) pairs.push(`*~${r.fallback}`)", "if (false) pairs.push('')"),
 ("attr: free keeps entries whose list is empty", "attributeAssembler.ts",
  "if (free.length) out.push(`${c.what}:${free.join(',')}`)",
  "out.push(`${c.what}:${free.join(',')}`)"),
 ("attr: slots drops the empty label segment", "attributeAssembler.ts",
  "if (f.label || f.seg != null) clause += ':' + (f.label ?? '')",
  "if (f.label) clause += ':' + f.label"),
 ("attr: derived emits a rule that names no fields", "attributeAssembler.ts",
  "if (!fields || !fields.length) continue", "if (false) continue"),
 ("attr: max ignores whether the tag already carries it", "attributeAssembler.ts",
  "if (!alreadyPresent || max == null) return null", "if (max == null) return null"),
 ("attr: choices invents a menu instead of refusing", "attributeAssembler.ts",
  "      if (!members.length) {", "      if (false) {"),
 ("attr: choices picks one when slots disagree", "attributeAssembler.ts",
  "    if (from.some(x => [...x].sort().join(' ') !== first)) {",
  "    if (false) {"),
 ("prompt: frag returns '' instead of throwing", "promptAssembler.ts",
  "    throw new Error('prompt fragment '", "    return '' + ((): string => { throw new Error('prompt fragment '"),
 ("prompt: renderFrame ignores negation", "promptAssembler.ts",
  "if (conditions.has(name) === negated) continue", "if (!conditions.has(name)) continue"),
 ("prompt: credit loses the GATE label", "promptAssembler.ts",
  "const worth = c.gates ? ' **GATE**' : c.pts == null ? '' : ` (${g(c.pts)} pt)`",
  "const worth = c.pts == null ? '' : ` (${g(c.pts)} pt)`"),
 ("prompt: deduction ignores repeatable", "promptAssembler.ts",
  "const rep = d.repeatable ? ' [repeatable]' : ''", "const rep = ''"),
 ("prompt: guidance ignores the omission list", "promptAssembler.ts",
  "const kept = o.item.guidance.filter((_, i) => !drop.has(i))",
  "const kept = o.item.guidance"),
 ("prompt: checklist drops the counts paragraph", "promptAssembler.ts",
  "  for (const cr of counts) {\n    lines.push('', frag(o.fragments, 'countsNote'",
  "  for (const cr of [] as typeof counts) {\n    lines.push('', frag(o.fragments, 'countsNote'"),
 ("prompt: a computed slot stays in the answerable list", "promptAssembler.ts",
  "|| mapped.has(s.key)) continue", "|| false) continue"),
]

def run():
    r = subprocess.run(["npx", "vitest", "run",
                        "packages/shared/lib/llm/__mutation__", "--reporter=dot"],
                       cwd=ROOT, capture_output=True, text=True, timeout=600)
    return r.returncode == 0

caught, missed, broken = [], [], []
for desc, fname, old, new in MUTATIONS:
    src = PRISTINE[fname]
    if src.count(old) != 1:
        broken.append(desc); continue
    (M / fname).write_text(src.replace(old, new, 1))
    ok = run()
    (M / fname).write_text(src)          # restore immediately
    (caught if not ok else missed).append(desc)

print(f"CAUGHT  {len(caught)} of {len(MUTATIONS) - len(broken)} injected defects")
for d in caught: print("   caught  " + d)
if missed:
    print(f"\nSURVIVED {len(missed)} -- the tests do not detect these:")
    for d in missed: print("   MISSED  " + d)
if broken:
    print(f"\nnot applied ({len(broken)}) -- anchor did not match exactly once:")
    for d in broken: print("   skip    " + d)
