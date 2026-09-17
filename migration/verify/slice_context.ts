import { readFileSync, writeFileSync } from 'node:fs'
import { assembleContextAndResponse } from '@/lib/llm/promptAssembler'
const data = JSON.parse(readFileSync((process.env.MIGRATION_ROOT ?? '../..') + '/migration/goldens/ctx_inputs.json','utf8'))
for (const [item, d] of Object.entries<any>(data)) {
  const got = assembleContextAndResponse({
    itemId: d.itemId, context: d.context, evidence: d.evidence ?? undefined, response: d.response })
  writeFileSync('/tmp/ts_ctx_' + item + '.txt', got)
  console.log(item + ': rendered ' + got.length + ' chars, expected ' + d.expected.length)
}
