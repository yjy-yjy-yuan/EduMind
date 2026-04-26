import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const readSource = (relativePath) =>
  readFileSync(resolve(process.cwd(), relativePath), 'utf8')

test('Player.vue shows collapsible visual-enhancement source section', () => {
  const source = readSource('src/views/Player.vue')
  assert.match(source, /视觉增强来源/)
  assert.match(source, /可折叠|折叠/)
  assert.match(source, /fdSourceExpanded|fd-source-toggle|source-toggle/)
})

test('each realtime description item supports one-click note write action', () => {
  const source = readSource('src/views/Player.vue')
  assert.match(source, /v-for="\(item, idx\) in fdRecentHistory"/)
  assert.match(source, /写入笔记/)
  assert.match(source, /@click="saveFdDescriptionToNote\(item\)"|@click="writeFdNote\(item\)"/)
})

test('note payload for frame description includes video_id timestamp content source=vinci_enhanced', () => {
  const source = readSource('src/views/Player.vue')
  assert.match(source, /createNote\s*\(\s*\{/)
  assert.match(source, /video_id\s*:\s*Number\(id\.value\)/)
  assert.match(source, /timestamp\s*:/)
  assert.match(source, /content\s*:/)
  assert.match(source, /source\s*:\s*['"]vinci_enhanced['"]/)
})

test('write failure provides retryable user-facing message for description note write', () => {
  const source = readSource('src/views/Player.vue')
  assert.match(source, /写入失败|保存失败/)
  assert.match(source, /重试/)
  assert.match(source, /retryFdNote|retryWriteNote|retrySaveDescriptionNote/)
})

test('Notes list renders Vinci enhanced source label', () => {
  const source = readSource('src/views/Notes.vue')
  assert.match(source, /vinci_enhanced/)
  assert.match(source, /Vinci增强/)
  assert.match(source, /meta-pill--source|note-source-label|source-badge/)
})

test('frontend keeps backend-only integration and does not directly call Vinci host', () => {
  const playerSource = readSource('src/views/Player.vue')
  const frameApiSource = readSource('src/api/frameDescription.js')
  const noteApiSource = readSource('src/api/note.js')

  const joined = `${playerSource}\n${frameApiSource}\n${noteApiSource}`
  assert.ok(!/https?:\/\/[^\s'"`]*vinci/i.test(joined), 'must not directly call Vinci host in frontend')
  assert.match(frameApiSource, /withBase\s*\(\s*['"]\/api\/frame_description\//)
  assert.match(noteApiSource, /url:\s*['"]\/api\/notes/)
})
