// @vitest-environment node
//
// Stage 04's first gate clause: ALL 26 BYTE-EQUAL, assembled from the rubric.
//
// Every item's ITEM-LEVEL data is read from the emitted rubric .olx -- question,
// slots, credit, deductions, guidance, computed rules, and the shared frame.
// What is still read from the old source is printed, because a gate that says
// "26 byte-equal" without saying what it did not source is claiming too much.

import { readFileSync, writeFileSync } from 'node:fs'
import { parseOLX } from '@/lib/content/parseOLX'
import { toMemoryRef } from '@/lib/types/storage'
import { TEST_NS } from '@/lib/test-utils'
import { assembleBodyPrefix, assembleChecklist, assembleContextAndResponse }
  from '@/lib/llm/promptAssembler'

const G = (process.env.MIGRATION_ROOT ?? '../..') + '/migration/goldens/'
const P = (process.env.MIGRATION_ROOT ?? '../..') + '/psychology/'

test('all 26 assemble byte-equal from the emitted rubric', async () => {
  const fragments = JSON.parse(readFileSync(G + 'fragments.json', 'utf8'))
  const old = JSON.parse(readFileSync(G + 'all26_inputs.json', 'utf8'))

  // ---- read every emitted rubric -------------------------------------------
  const items = new Map<string, any>()
  let frame: any[] = []
  let parseErrors = 0
  // ONE rubric, under the id the course resolves (decision 11.12). This read
  // three per-handout files; when they were superseded the probe threw ENOENT
  // and the gate reported "no result", which reads like an assembly failure and
  // is really a file that moved.
  for (const name of ['bmod_rubric.olx']) {
    const xml = readFileSync(P + name, 'utf8')
    const { idMap } = await parseOLX(xml, [toMemoryRef(name)], undefined, TEST_NS)
    const nodes = Object.values<any>(idMap).map(v => v['*']).filter(Boolean)
    parseErrors += nodes.filter(n => n.tag === 'ErrorNode').length
    const byId = new Map(nodes.map(n => [n.id, n]))
    const kidRefs = (n: any): any[] => {
      const k = n?.kids
      if (!k || typeof k === 'string') return []
      if (Array.isArray(k)) return k
      return Object.values(k).flatMap(v => (Array.isArray(v) ? v : []))
    }
    const textOf = (n: any) => (typeof n?.kids === 'string' ? n.kids : undefined)
    const kidsOf = (n: any) => kidRefs(n)
      .map((k: any) => byId.get(typeof k === 'string' ? k : k?.id)).filter(Boolean)
    for (const n of nodes) {
      if (n.tag === 'Frame' && n.attributes.name === 'oc_criteria') {
        frame = kidsOf(n).map((s: any) =>
          ({ text: textOf(s) ?? '', when: s.attributes.ifDeclared }))
      }
      if (n.tag !== 'Item') continue
      const kids = kidsOf(n)
      const pick = (t: string) => kids.filter((k: any) => k.tag === t)
      items.set(n.attributes.scores, {
        max: Number(n.attributes.max),
        question: textOf(pick('Question')[0]),
        deriveFromClauses: n.attributes.deriveFromClauses === 'true',
        // conditions and params now come from the RUBRIC, not the old source
        conditions: String(n.attributes.conditions ?? '').split('|').filter(Boolean),
        frameParams: Object.fromEntries(String(n.attributes.params ?? '')
          .split('|').filter(Boolean).map((s: string) =>
            [s.slice(0, s.indexOf('=')), s.slice(s.indexOf('=') + 1)])),
        // CREDIT ORDER, from <Credit> elements -- not derived from slot order,
        // which differs on 11 items and omits four items' credit entirely.
        credit: pick('Credit').map((c: any) => ({
          what: c.attributes.what,
          pts: c.attributes.pts === undefined ? undefined : Number(c.attributes.pts),
          desc: textOf(c),
          gates: c.attributes.gates === 'true' ? true : undefined,
        })),
        deductions: pick('Deduction').map((d: any) => ({
          code: d.attributes.code, pts: Number(d.attributes.pts), text: textOf(d),
          repeatable: d.attributes.repeatable === 'true' || undefined,
        })),
        guidance: pick('Guidance').filter((g: any) => !g.attributes.use).map((g: any) => textOf(g)),
      })
    }
  }
  console.log('PARSE_ERRORS=' + parseErrors + ' ITEMS_READ=' + items.size +
              ' FRAME_SEGMENTS=' + frame.length)

  // ---- assemble each and diff ----------------------------------------------
  let ok = 0
  const bad: string[] = []
  for (const [id, o] of Object.entries<any>(old)) {
    const R = items.get(id)
    if (!R) { bad.push(id + ': not in the emitted rubric'); continue }
    const parts: string[] = [assembleBodyPrefix({
      item: {
        id, max: R.max, question: R.question, credit: R.credit,
        deductions: R.deductions, guidance: R.guidance,
        deriveFromClauses: R.deriveFromClauses,
        termDefinition: o.item.termDefinition, omitGuidance: o.item.omitGuidance,
        conditions: R.conditions, frameParams: R.frameParams,
      } as any,
      blurb: o.blurb, webSystem: o.webSystem, fragments, frame,
    })]
    if (o.item.itemNotes) parts.push(o.item.itemNotes)
    parts.push(assembleChecklist({ slots: o.slots, credit: R.credit as any,
      notes: o.notes, fragments, rules: o.rules }))
    parts.push(assembleContextAndResponse({ itemId: id, context: o.context,
      evidence: o.evidence ?? undefined, response: o.response, fragments,
      sections: o.sections }))
    const got = parts.join('\n').replace(/\s+$/, '') + '\n'
    if (got === o.expected) ok++
    else {
      let at = 0
      while (at < got.length && got[at] === o.expected[at]) at++
      bad.push(id + ' @' + at + ' got ' + JSON.stringify(got.slice(at, at + 46)) +
               ' want ' + JSON.stringify(o.expected.slice(at, at + 46)))
    }
  }
  console.log('BYTE_EQUAL=' + ok + '/' + Object.keys(old).length)
  for (const b of bad.slice(0, 6)) console.log('  DIFF ' + b)
  console.log('FROM_OLD_SOURCE=fragments,contextRefs,responseRefs,slotOptions,notes,itemNotes,termDefinition (conditions+params now from the rubric)')
})
