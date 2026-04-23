import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const readSource = (relativePath) =>
  readFileSync(resolve(process.cwd(), relativePath), 'utf8')

test('agent api only proxies to backend route', () => {
  const source = readSource('src/api/agent.js')
  assert.match(source, /url:\s*['"]\/api\/agent\/execute['"]/)
  assert.ok(!/vinci/i.test(source), 'agent api source should not reference vinci directly')
})

test('qa stream keeps NDJSON contract and backend proxy path', () => {
  const source = readSource('src/api/qa.js')
  assert.match(source, /Accept:\s*['"]application\/x-ndjson['"]/)
  assert.match(source, /withBase\('\/api\/qa\/ask'\)/)
})

test('qa stream error prefers user-facing message before detail', () => {
  const source = readSource('src/api/qa.js')
  assert.match(source, /event\.message\s*\|\|\s*event\.detail/)
})
