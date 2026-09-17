import { readFileSync, writeFileSync } from 'node:fs'
import { assembleBodyPrefix } from '@/lib/llm/promptAssembler'
const o = JSON.parse(readFileSync((process.env.MIGRATION_ROOT ?? '../..') + '/migration/goldens/slice_2b_input.json', 'utf8'))
// Append a sentinel exactly as build_web_prompt appends the checklist section,
// so the prefix carries the separator that precedes the next section.
const out = assembleBodyPrefix(o) + '\n' + 'SENTINEL'
writeFileSync('/tmp/slice_2b_rendered2.txt', out.slice(0, out.indexOf('SENTINEL')))
