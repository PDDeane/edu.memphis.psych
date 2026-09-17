import { readFileSync } from 'node:fs'
import { assembleBodyPrefix, assembleChecklist, assembleContextAndResponse }
  from '@/lib/llm/promptAssembler'
const G = (process.env.MIGRATION_ROOT ?? '../..') + '/migration/goldens/'
const fragments = JSON.parse(readFileSync(G + 'fragments.json', 'utf8'))
const frame = JSON.parse(readFileSync(G + 'criteria_frame.json', 'utf8')).segments
const data = JSON.parse(readFileSync(G + 'all26_inputs.json', 'utf8'))

let ok = 0
const bad: string[] = []
for (const [item, d] of Object.entries<any>(data)) {
  const parts: string[] = [assembleBodyPrefix({ ...d, fragments, frame })]
  if (d.item.itemNotes) parts.push(d.item.itemNotes)
  parts.push(assembleChecklist({
    slots: d.slots, credit: d.item.credit, notes: d.notes, fragments,
    rules: d.rules }))
  parts.push(assembleContextAndResponse({
    itemId: d.item.id, context: d.context, evidence: d.evidence ?? undefined,
    response: d.response, fragments, sections: d.sections }))
  const got = parts.join('\n').replace(/\s+$/, '') + '\n'
  if (got === d.expected) ok++
  else {
    let at = -1
    for (let i = 0; i < Math.max(got.length, d.expected.length); i++) {
      if (got[i] !== d.expected[i]) { at = i; break }
    }
    bad.push(item + ' (got ' + got.length + ' want ' + d.expected.length + ', first diff at ' + at
      + ')\n      got  ' + JSON.stringify(got.slice(at, at + 70))
      + '\n      want ' + JSON.stringify(d.expected.slice(at, at + 70)))
  }
}
console.log('BYTE-EXACT: ' + ok + ' of ' + Object.keys(data).length + ' bodies')
if (bad.length) {
  console.log('')
  console.log('differing (' + bad.length + '):')
  for (const b of bad.slice(0, 6)) console.log('  ' + b)
}
