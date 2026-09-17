import { readFileSync } from 'node:fs'
import { choicesAttr } from '@/lib/llm/attributeAssembler'
const data = JSON.parse(readFileSync((process.env.MIGRATION_ROOT ?? '../..') + '/migration/goldens/attr_inputs.json','utf8'))
let ok = 0, bad = 0
for (const [item, d] of Object.entries<any>(data)) {
  let got: string | null = null
  try {
    got = choicesAttr({ declared: d.choicesDeclared ?? {}, users: d.choicesUsers ?? {},
                        sourced: d.choicesSourced ?? {}, itemId: item })
  } catch (e) { got = 'THREW' }
  const want = d.expected.choices ?? null
  if (got === want) { ok++ } else {
    bad++
    console.log('  MISMATCH ' + item)
    console.log('     want ' + JSON.stringify(want))
    console.log('     got  ' + JSON.stringify(got))
  }
}
console.log('')
console.log('choices: ' + ok + ' byte-identical, ' + bad + ' differing, across ' + Object.keys(data).length + ' items')
