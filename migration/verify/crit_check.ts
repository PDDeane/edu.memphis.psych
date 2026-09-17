import { readFileSync } from 'node:fs'
import { assembleBodyPrefix } from '@/lib/llm/promptAssembler'
const G = (process.env.MIGRATION_ROOT ?? '../..') + '/migration/goldens/'
const fragments = JSON.parse(readFileSync(G + 'fragments.json', 'utf8'))
const frame = JSON.parse(readFileSync(G + 'criteria_frame.json', 'utf8')).segments
const data = JSON.parse(readFileSync(G + 'criteria_slice.json', 'utf8'))
let ok = 0, bad = 0
for (const [item, d] of Object.entries<any>(data)) {
  const out = assembleBodyPrefix({ ...d, fragments, frame }) + '\n' + 'SENTINEL'
  const got = out.slice(0, out.indexOf('SENTINEL'))
  if (got === d.expected) { ok++; console.log('  ' + item + ': IDENTICAL (' + got.length + ' chars)') }
  else {
    bad++
    console.log('  ' + item + ': DIFFERS got ' + got.length + ' want ' + d.expected.length)
    for (let i = 0; i < Math.min(got.length, d.expected.length); i++) {
      if (got[i] !== d.expected[i]) {
        console.log('     first diff at ' + i)
        console.log('     got  ' + JSON.stringify(got.slice(i, i + 60)))
        console.log('     want ' + JSON.stringify(d.expected.slice(i, i + 60)))
        break
      }
    }
  }
}
console.log('')
console.log('criteria-path prefix: ' + ok + ' identical, ' + bad + ' differing')
