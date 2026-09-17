import { readFileSync, writeFileSync } from 'node:fs'
import { assembleBodyPrefix, assembleChecklist, assembleContextAndResponse }
  from '@/lib/llm/promptAssembler'
const G = (process.env.MIGRATION_ROOT ?? '../..') + '/migration/goldens/'
const fragments = JSON.parse(readFileSync(G + 'fragments.json', 'utf8'))
const pre = JSON.parse(readFileSync(G + 'slice_2b_input.json', 'utf8'))
const chk = JSON.parse(readFileSync(G + 'slice_2b_checklist.json', 'utf8'))
const ctx = JSON.parse(readFileSync(G + 'ctx_inputs.json', 'utf8'))
const out = assembleBodyPrefix({ ...pre, fragments }) + '\n' + 'SENTINEL'
writeFileSync('/tmp/r_prefix.txt', out.slice(0, out.indexOf('SENTINEL')))
writeFileSync('/tmp/r_checklist.txt', assembleChecklist({
  slots: chk.slots, credit: chk.credit, notes: chk.notes, fragments,
  rules: { counts: chk.counts, equals: chk.equals, derived: chk.derived,
           choices: chk.choices, expect: chk.expect, forbid: chk.forbid, maps: chk.maps } }))
for (const item of ['2b', 'Q1', '1c']) {
  const d = ctx[item]
  writeFileSync('/tmp/r_ctx_' + item + '.txt', assembleContextAndResponse({
    itemId: d.itemId, context: d.context, evidence: d.evidence ?? undefined,
    response: d.response, fragments }))
}
console.log('rendered with external fragments')
