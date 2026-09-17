// @vitest-environment node
import { readFileSync, writeFileSync } from 'node:fs'
import { parseOLX } from '@/lib/content/parseOLX'
import { toMemoryRef } from '@/lib/types/storage'
import { TEST_NS } from '@/lib/test-utils'
import { materialiseRubric, warnings } from '@/lib/llm/materialiseRubric'
import type { RubricNode } from '@/lib/llm/materialiseRubric'

test('the authored rubric round-trips to the real items', async () => {
  const xml = readFileSync(
    (process.env.MIGRATION_ROOT ?? '../..') + '/psychology/bmod_rubric.olx', 'utf8')
  const { idMap } = await parseOLX(xml, [toMemoryRef('bmod_rubric.olx')], undefined, TEST_NS)
  const nodes = Object.values<any>(idMap).map(v => v['*'])
  const errs = nodes.filter(n => n?.tag === 'ErrorNode')
    .map(n => String(n.attributes?.message ?? ''))
  console.log('PARSE_ERRORS=' + errs.length + (errs.length ? ' :: ' + errs[0].slice(0, 120) : ''))

  // Rebuild the parsed tree into the shape materialiseRubric takes.
  const byId = new Map<string, any>(nodes.filter(Boolean).map(n => [n.id, n]))
  // `kids` is an array on some blocks and an object of named arrays on others,
  // so flatten whatever is there rather than assuming one shape.
  const kidRefs = (n: any): any[] => {
    const k = n?.kids
    if (!k || typeof k === 'string') return []   // a text block: kids IS the text
    if (Array.isArray(k)) return k
    return Object.values(k).flatMap(v => (Array.isArray(v) ? v : []))
  }
  // A text block parses its content into `kids` AS A STRING. Reading only
  // `textContent` loses it, and the loss is silent: the node is still there, the
  // structure still materialises, and every placeholder simply disappears.
  const textOf = (n: any): string | undefined =>
    typeof n?.kids === 'string' ? n.kids
      : typeof n?.textContent === 'string' ? n.textContent : undefined
  const toNode = (n: any): RubricNode => ({
    kind: n.tag,
    attrs: { ...(n.attributes ?? {}) },
    text: textOf(n),
    children: kidRefs(n)
      .map((k: any) => (typeof k === 'string' ? byId.get(k) : byId.get(k?.id)))
      .filter(Boolean).map(toNode),
  })
  const rubric = nodes.find(n => n?.tag === 'Rubric')
  const top = toNode(rubric).children ?? []
  console.log('TOP_KINDS=' + top.map(t => t.kind).join(','))
  const out = materialiseRubric(top.filter(t => t.kind !== 'Verdicts'))
  writeFileSync('/tmp/roundtrip_out.json', JSON.stringify(out, null, 1))
  console.log('MATERIALISED=' + out.length + ' TEMPLATES_LEFT=' +
              out.filter(n => n.kind === 'ItemTemplate').length)
  if (warnings.length) console.log('WARN=' + warnings.join('; '))
})
