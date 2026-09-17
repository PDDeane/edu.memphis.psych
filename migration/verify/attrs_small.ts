import { readFileSync } from 'node:fs'
import * as A from '@/lib/llm/attributeAssembler'
const data = JSON.parse(readFileSync((process.env.MIGRATION_ROOT ?? '../..') + '/migration/goldens/attr_inputs.json','utf8'))
const fns: Record<string, (x: any, c?: any) => string | null> = {
  counts: r => A.countsAttr(r), onlyif: r => A.onlyifAttr(r),
  requires: r => A.requiresAttr(r), equals: r => A.equalsAttr(r),
  cover: r => A.coverAttr(r), forbid: r => A.forbidAttr(r), maps: r => A.mapsAttr(r),
}
let ok = 0, bad = 0
for (const [item, d] of Object.entries<any>(data)) {
  for (const [attr, fn] of Object.entries(fns)) {
    const got = fn(d.rules[attr]); const want = d.expected[attr] ?? null
    if (got === want) ok++; else { bad++; console.log(`  ✗ ${item}.${attr}\n     want ${JSON.stringify(want)}\n     got  ${JSON.stringify(got)}`) }
  }
  const gotFree = A.freeAttr(d.credit); const wantFree = d.expected.free ?? null
  if (gotFree === wantFree) ok++; else { bad++; console.log(`  ✗ ${item}.free want ${JSON.stringify(wantFree)} got ${JSON.stringify(gotFree)}`) }
}
console.log(`\n${ok} attribute(s) byte-identical, ${bad} differing, across ${Object.keys(data).length} items`)
