// @vitest-environment node
import { readFileSync } from 'node:fs'
import { parseOLX } from '@/lib/content/parseOLX'
import { toMemoryRef } from '@/lib/types/storage'
import { TEST_NS } from '@/lib/test-utils'
test('PR rubric parses', async () => {
  const xml = readFileSync((process.env.MIGRATION_ROOT ?? '../..') + '/psychology/bmod_rubric_pr.olx', 'utf8')
  const { idMap } = await parseOLX(xml, [toMemoryRef('pr.olx')], undefined, TEST_NS)
  const errs = Object.values<any>(idMap).map(v => v['*'])
    .filter(n => n?.tag === 'ErrorNode').map(n => String(n.attributes?.message ?? ''))
  console.log('PR_PARSE_ERRORS=' + errs.length + (errs.length ? ' :: ' + errs[0].slice(0, 130) : ''))
})
