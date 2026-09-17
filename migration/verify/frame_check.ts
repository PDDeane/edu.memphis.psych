import { readFileSync } from 'node:fs'
import { renderFrame } from '@/lib/llm/promptAssembler'
const f = JSON.parse(readFileSync((process.env.MIGRATION_ROOT ?? '../..') + '/migration/goldens/criteria_frame.json','utf8'))
let ok = 0, bad = 0
for (const [item, d] of Object.entries<any>(f.items)) {
  const got = renderFrame(f.segments, new Set<string>(d.conditions), d.params)
  if (got === d.expected) { ok++ } else {
    bad++
    console.log('MISMATCH ' + item + '  got ' + got.length + ' want ' + d.expected.length)
    for (let i = 0; i < Math.min(got.length, d.expected.length); i++) {
      if (got[i] !== d.expected[i]) {
        console.log('   first diff at ' + i + ': got ' + JSON.stringify(got.slice(i, i+50))
                    + ' want ' + JSON.stringify(d.expected.slice(i, i+50)))
        break
      }
    }
  }
}
console.log('')
console.log('criteria frame: ' + ok + ' of ' + (ok + bad) + ' items byte-identical')
