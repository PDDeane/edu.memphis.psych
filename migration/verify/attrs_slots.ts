import { readFileSync } from 'node:fs'
import * as A from '@/lib/llm/attributeAssembler'
const data = JSON.parse(readFileSync((process.env.MIGRATION_ROOT ?? '../..') + '/migration/goldens/attr_inputs.json','utf8'))
let ok = 0, bad = 0
for (const [item, d] of Object.entries<any>(data)) {
  for (const [name, got] of [
    ['slots',   A.slotsAttr(d.slotSpec)],
    ['derived', A.derivedAttr(d.derivedRules)],
    ['max',     A.maxAttr(d.max, d.maxPresent)],
  ] as const) {
    const want = d.expected[name] ?? null
    if (got === want) ok++
    else { bad++; console.log(`  ✗ ${item}.${name}\n     want ${JSON.stringify(want)?.slice(0,110)}\n     got  ${JSON.stringify(got)?.slice(0,110)}`) }
  }
}
console.log(`\n${ok} byte-identical, ${bad} differing, across ${Object.keys(data).length} items`)
