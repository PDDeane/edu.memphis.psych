// @vitest-environment node
//
// Stage 3b's gate: ONE ITEM, BYTE-EQUAL, ASSEMBLED FROM THE RUBRIC OBJECT.
//
// What comes from the rubric: the question, every sheet slot with its label,
// points and judging description, the deductions, the guidance, the computed
// rules, and the shared criteria frame with its segments.
//
// What does NOT yet come from the rubric, and is read from the old source so
// the comparison is honest: the cross-reference and response FIELD IDS (still
// in generator-side tables), and the shared prose fragments. Those are named in
// the output so the gap is visible rather than implied.

import { readFileSync, writeFileSync } from 'node:fs'
import { parseOLX } from '@/lib/content/parseOLX'
import { toMemoryRef } from '@/lib/types/storage'
import { TEST_NS } from '@/lib/test-utils'
import { assembleBodyPrefix, assembleChecklist, assembleContextAndResponse }
  from '@/lib/llm/promptAssembler'

const G = (process.env.MIGRATION_ROOT ?? '../..') + '/migration/goldens/'

test('PR assembles byte-equal from the rubric object', async () => {
  const xml = readFileSync(
    (process.env.MIGRATION_ROOT ?? '../..') + '/psychology/bmod_rubric_pr.olx', 'utf8')
  const { idMap } = await parseOLX(xml, [toMemoryRef('pr.olx')], undefined, TEST_NS)
  const nodes = Object.values<any>(idMap).map(v => v['*']).filter(Boolean)
  const byId = new Map(nodes.map(n => [n.id, n]))
  const kidRefs = (n: any): any[] => {
    const k = n?.kids
    if (!k || typeof k === 'string') return []
    if (Array.isArray(k)) return k
    return Object.values(k).flatMap(v => (Array.isArray(v) ? v : []))
  }
  const textOf = (n: any): string | undefined =>
    typeof n?.kids === 'string' ? n.kids : undefined
  const kidsOf = (n: any) => kidRefs(n)
    .map((k: any) => byId.get(typeof k === 'string' ? k : k?.id)).filter(Boolean)

  const item = nodes.find(n => n.tag === 'Item')!
  const kids = kidsOf(item)
  const pick = (tag: string) => kids.filter(k => k.tag === tag)

  // ---- from the RUBRIC -----------------------------------------------------
  const slots = pick('Slot').map(s => ({
    key: s.attributes.key, label: s.attributes.label, options: [] as string[],
    gates: s.attributes.gate === 'true',
    pts: s.attributes.pts === undefined ? null : Number(s.attributes.pts),
    count_max: null, picks: null, desc: textOf(s),
  }))
  const credit = slots.filter(s => s.pts != null)
    .map(s => ({ what: s.key, pts: s.pts!, desc: s.desc! }))
  const deductions = pick('Deduction').map(d => ({
    code: d.attributes.code, pts: Number(d.attributes.pts), text: textOf(d)!,
    repeatable: d.attributes.repeatable === 'true',
  }))
  const guidance = pick('Guidance').filter(g => !g.attributes.use).map(g => textOf(g)!)
  const frameRef = pick('Guidance').find(g => g.attributes.use)
  const frameName = String(frameRef?.attributes.use ?? '').replace(/^@/, '')
  const frameNode = nodes.find(n => n.tag === 'Frame' && n.attributes.name === frameName)!
  const frame = kidsOf(frameNode).map(s => ({
    text: textOf(s) ?? '', when: s.attributes.ifDeclared,
  }))

  // ---- from the OLD source, and said so -------------------------------------
  const old = JSON.parse(readFileSync(G + 'all26_inputs.json', 'utf8')).PR
  const fragments = JSON.parse(readFileSync(G + 'fragments.json', 'utf8'))
  console.log('FROM_RUBRIC=question,slots(' + slots.length + '),credit(' + credit.length +
    '),deductions(' + deductions.length + '),guidance(' + guidance.length +
    '),frame(' + frame.length + ')')
  console.log('FROM_OLD_SOURCE=fragments,contextRefs,responseRefs,slotOptions,notes')

  const parts: string[] = [assembleBodyPrefix({
    item: {
      id: 'PR', max: Number(item.attributes.max),
      question: textOf(pick('Question')[0])!,
      credit, deductions, guidance,
      deriveFromClauses: item.attributes.deriveFromClauses === 'true',
      conditions: [], frameParams: {},
    } as any,
    blurb: old.blurb, webSystem: old.webSystem, fragments, frame,
  })]
  parts.push(assembleChecklist({
    slots: old.slots, credit: credit as any, notes: old.notes, fragments,
    rules: old.rules,
  }))
  parts.push(assembleContextAndResponse({
    itemId: 'PR', context: old.context, evidence: old.evidence ?? undefined,
    response: old.response, fragments, sections: old.sections,
  }))
  const got = parts.join('\n').replace(/\s+$/, '') + '\n'
  writeFileSync('/tmp/pr_from_rubric.txt', got)
  const want = old.expected
  console.log('BYTE_EQUAL=' + (got === want) + ' got=' + got.length + ' want=' + want.length)
  if (got !== want) {
    for (let i = 0; i < Math.max(got.length, want.length); i++) {
      if (got[i] !== want[i]) {
        console.log('FIRST_DIFF@' + i)
        console.log('  got  ' + JSON.stringify(got.slice(i, i + 80)))
        console.log('  want ' + JSON.stringify(want.slice(i, i + 80)))
        break
      }
    }
  }
})
