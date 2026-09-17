// @vitest-environment node
import { readFileSync } from 'node:fs'
import { parseOLX } from '@/lib/content/parseOLX'
import { toMemoryRef } from '@/lib/types/storage'
import { TEST_NS } from '@/lib/test-utils'
test('course sections', async () => {
  const xml = readFileSync((process.env.MIGRATION_ROOT ?? '../..') + '/psychology/bmod_course.olx', 'utf8')
  const { idMap } = await parseOLX(xml, [toMemoryRef('c.olx')], undefined, TEST_NS)
  const nodes = Object.values<any>(idMap).map(v => v['*']).filter(Boolean)
  const course = nodes.find(n => n.tag === 'Course')
  const secs = (course?.kids?.sections ?? []) as any[]
  console.log('SECTIONS=' + secs.length)
  console.log('KINDS=' + secs.map(s => s.type + ':' + (s.id ?? '')).join(','))
  const errs = nodes.filter(n => n.tag === 'ErrorNode').map(n => String(n.attributes?.message ?? ''))
  console.log('ERRORS=' + errs.length + (errs.length ? ' :: ' + errs[0].slice(0, 100) : ''))
})
