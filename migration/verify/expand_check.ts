import { readFileSync, writeFileSync } from 'node:fs'
import { expandItem, unusedParams } from '@/lib/llm/itemTemplate'
const G = (process.env.MIGRATION_ROOT ?? '../..') + '/migration/goldens/'
const { template, items } = JSON.parse(readFileSync(G + 'type_template.json', 'utf8'))
const out: Record<string, any> = {}
for (const item of items) {
  const ex = expandItem(template, item)
  const credit = ex.nodes.filter((n: any) => n.kind === 'Slot')
    .map((n: any) => ({ what: n.attrs.key, pts: Number(n.attrs.pts), desc: n.text }))
  const deductions = ex.nodes.filter((n: any) => n.kind === 'Deduction')
    .map((n: any) => ({ code: n.attrs.code, pts: Number(n.attrs.pts), text: n.text }))
  const expect = ex.nodes.filter((n: any) => n.kind === 'Expect')
    .map((n: any) => ({ key: n.attrs.key, left: n.attrs.left, value: n.attrs.value }))
  const forbid = ex.nodes.filter((n: any) => n.kind === 'Forbid')
    .map((n: any) => ({ key: n.attrs.key }))
  const onlyif = ex.nodes.filter((n: any) => n.kind === 'Onlyif')
    .map((n: any) => ({ key: n.attrs.key, cond: n.attrs.cond }))
  const question = ex.nodes.find((n: any) => n.kind === 'Question')?.text
  out[item._id] = { max: Number(ex.max), question, credit, deductions, expect, forbid, onlyif }
  const unused = unusedParams(template, item)
  if (unused.length) console.log('  note: ' + item._id + ' supplies unused param(s): ' + unused.join(', '))
}
writeFileSync('/tmp/expanded_items.json', JSON.stringify(out, null, 1))
console.log('expanded ' + Object.keys(out).length + ' items')
