import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

test('config ignores stale loopback api base when frontend is opened from LAN origin', () => {
  const source = readFileSync(resolve(process.cwd(), 'mobile-frontend/src/config/index.js'), 'utf8')
  assert.match(source, /const\s+isLoopbackHost\s*=/)
  assert.match(source, /const\s+shouldRejectRuntimeApiBaseForCurrentOrigin\s*=/)
  assert.match(source, /!\s*isLoopbackHost\(pageHost\)/)
  assert.match(source, /shouldRejectRuntimeApiBaseForCurrentOrigin\(normalized,\s*source\)/)
})

test('config exposes a dedicated realtime description api base', () => {
  const source = readFileSync(resolve(process.cwd(), 'mobile-frontend/src/config/index.js'), 'utf8')
  assert.match(source, /VITE_FRAME_DESC_API_BASE_URL/)
  assert.match(source, /export\s+function\s+getFrameDescApiBaseUrl/)
  assert.match(source, /export\s+const\s+withFrameDescBase/)
})

test('config keeps realtime description origin out of global api trust set', () => {
  const source = readFileSync(resolve(process.cwd(), 'mobile-frontend/src/config/index.js'), 'utf8')
  assert.match(source, /const\s+candidates\s*=\s*fromNative\s*\?\s*\[fromNative\]\s*:\s*\[ENV_API_BASE_URL\]/)
})
