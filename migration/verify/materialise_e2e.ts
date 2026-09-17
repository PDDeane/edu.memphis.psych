import { readFileSync, writeFileSync } from 'node:fs'
import { materialiseRubric, warnings } from '@/lib/llm/materialiseRubric'
import type { RubricNode } from '@/lib/llm/materialiseRubric'
const G = (process.env.MIGRATION_ROOT ?? '../..') + '/migration/goldens/'
const { template, items } = JSON.parse(readFileSync(G + 'type_template.json', 'utf8'))

// The template as a parsed NODE, and the items as an author would write them:
// attribute strings, not pre-split objects.
const tplNode: RubricNode = {
  kind: 'ItemTemplate', attrs: { name: template.name },
  children: template.nodes.map((n: any) => ({
    kind: n.kind, text: n.text ?? undefined,
    attrs: { ...(n.attrs ?? {}), ...(n.ifDeclared ? { ifDeclared: n.ifDeclared } : {}) },
  })),
}
const itemNodes: RubricNode[] = items.map((i: any) => ({
  kind: 'Item',
  attrs: {
    scores: i.scores, use: '@' + template.name, max: String(i.max),
    conditions: (i.conditions ?? []).join('|'),
    params: Object.entries(i.params).map(([k, v]) => k + '=' + v).join('|'),
  },
}))

const out = materialiseRubric([tplNode, ...itemNodes])
const byId: Record<string, any> = {}
items.forEach((i: any, n: number) => {
  const node = out[n]
  const kids = node.children ?? []
  byId[i._id] = {
    max: Number(node.attrs!.max),
    question: kids.find(c => c.kind === 'Question')?.text,
    credit: kids.filter(c => c.kind === 'Slot')
      .map(c => ({ what: c.attrs!.key, pts: Number(c.attrs!.pts), desc: c.text })),
    deductions: kids.filter(c => c.kind === 'Deduction')
      .map(c => ({ code: c.attrs!.code, pts: Number(c.attrs!.pts), text: c.text })),
    expect: kids.filter(c => c.kind === 'Expect')
      .map(c => ({ key: c.attrs!.key, left: c.attrs!.left, value: c.attrs!.value })),
    forbid: kids.filter(c => c.kind === 'Forbid').map(c => ({ key: c.attrs!.key })),
    onlyif: kids.filter(c => c.kind === 'Onlyif')
      .map(c => ({ key: c.attrs!.key, cond: c.attrs!.cond })),
  }
})
writeFileSync('/tmp/materialised_items.json', JSON.stringify(byId, null, 1))
console.log('materialised ' + out.length + ' node(s); templates remaining: ' +
  out.filter(n => n.kind === 'ItemTemplate').length)
if (warnings.length) console.log('warnings: ' + warnings.join('; '))
