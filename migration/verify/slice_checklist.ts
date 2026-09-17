import { readFileSync, writeFileSync } from 'node:fs'
import { assembleChecklist } from '@/lib/llm/promptAssembler'
const d = JSON.parse(readFileSync((process.env.MIGRATION_ROOT ?? '../..') + '/migration/goldens/slice_2b_checklist.json','utf8'))
writeFileSync('/tmp/ts_checklist.txt', assembleChecklist({
  slots: d.slots, credit: d.credit, notes: d.notes,
  rules: { counts: d.counts, equals: d.equals, derived: d.derived,
           choices: d.choices, expect: d.expect, forbid: d.forbid, maps: d.maps },
}))
