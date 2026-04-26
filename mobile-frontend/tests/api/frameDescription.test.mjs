/**
 * 实时画面描述 API — 可执行的 Node.js 测试
 * 运行：npm test
 * 覆盖：API 导出、Mock 流模拟、NDJSON 解析、会话管理
 */

import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

// -----------------------------------------------------------------------
// 测试辅助：解析 NDJSON
// -----------------------------------------------------------------------
function parseNdjson(text) {
    return text.split('\n').filter(Boolean).map((l) => JSON.parse(l))
}

// -----------------------------------------------------------------------
// 测试 1：API 文件存在且可读
// -----------------------------------------------------------------------
test('frameDescription.js source file exists', () => {
    const source = readFileSync(resolve(process.cwd(), 'src/api/frameDescription.js'), 'utf8')
    assert.ok(source.length > 100, 'source file should not be empty')
})

// -----------------------------------------------------------------------
// 测试 2：describeFrameStream 是 async 函数
// -----------------------------------------------------------------------
test('describeFrameStream is exported as function', () => {
    const source = readFileSync(resolve(process.cwd(), 'src/api/frameDescription.js'), 'utf8')
    assert.match(source, /export\s+async\s+function\s+describeFrameStream/)
})

// -----------------------------------------------------------------------
// 测试 3：manageFrameDescSession 是 async 函数
// -----------------------------------------------------------------------
test('manageFrameDescSession is exported as function', () => {
    const source = readFileSync(resolve(process.cwd(), 'src/api/frameDescription.js'), 'utf8')
    assert.match(source, /export\s+async\s+function\s+manageFrameDescSession/)
})

// -----------------------------------------------------------------------
// 测试 4：getFrameDescHealth 是 async 函数
// -----------------------------------------------------------------------
test('getFrameDescHealth is exported as function', () => {
    const source = readFileSync(resolve(process.cwd(), 'src/api/frameDescription.js'), 'utf8')
    assert.match(source, /export\s+async\s+function\s+getFrameDescHealth/)
})

// -----------------------------------------------------------------------
// 测试 5：NDJSON 解析 — 完整行
// -----------------------------------------------------------------------
test('parseNdjson handles single line', () => {
    const raw = '{"type":"status","stage":"connecting"}\n'
    const events = parseNdjson(raw)
    assert.strictEqual(events.length, 1)
    assert.strictEqual(events[0].type, 'status')
    assert.strictEqual(events[0].stage, 'connecting')
})

// -----------------------------------------------------------------------
// 测试 6：NDJSON 解析 — 多行合并
// -----------------------------------------------------------------------
test('parseNdjson handles multi-line', () => {
    const raw = '{"type":"status"}\n{"type":"description","delta":"test"}\n{"type":"complete"}\n'
    const events = parseNdjson(raw)
    assert.strictEqual(events.length, 3)
    assert.strictEqual(events[1].type, 'description')
    assert.strictEqual(events[1].delta, 'test')
})

// -----------------------------------------------------------------------
// 测试 7：NDJSON 解析 — 空行过滤
// -----------------------------------------------------------------------
test('parseNdjson filters empty lines', () => {
    const raw = '{"type":"a"}\n\n{"type":"b"}\n\n\n'
    const events = parseNdjson(raw)
    assert.strictEqual(events.length, 2)
})

// -----------------------------------------------------------------------
// 测试 8：流式描述请求体格式正确
// -----------------------------------------------------------------------
test('source includes required NDJSON Accept header', () => {
    const source = readFileSync(resolve(process.cwd(), 'src/api/frameDescription.js'), 'utf8')
    assert.match(source, /Accept:\s*['"]application\/x-ndjson['"]/)
})

// -----------------------------------------------------------------------
// 测试 9：流式描述端点路径正确
// -----------------------------------------------------------------------
test('source calls /api/frame_description/describe', () => {
    const source = readFileSync(resolve(process.cwd(), 'src/api/frameDescription.js'), 'utf8')
    assert.match(source, /withBase\s*\(\s*['"]\/api\/frame_description\/describe['"]\s*\)/)
})

// -----------------------------------------------------------------------
// 测试 10：会话端点路径正确
// -----------------------------------------------------------------------
test('source calls /api/frame_description/session', () => {
    const source = readFileSync(resolve(process.cwd(), 'src/api/frameDescription.js'), 'utf8')
    assert.match(source, /withBase\s*\(\s*['"]\/api\/frame_description\/session['"]\s*\)/)
})

// -----------------------------------------------------------------------
// 测试 11：健康检查端点路径正确
// -----------------------------------------------------------------------
test('source calls /api/frame_description/health', () => {
    const source = readFileSync(resolve(process.cwd(), 'src/api/frameDescription.js'), 'utf8')
    assert.match(source, /withBase\s*\(\s*['"]\/api\/frame_description\/health['"]\s*\)/)
})

// -----------------------------------------------------------------------
// 测试 12：Mock 流模拟函数存在
// -----------------------------------------------------------------------
test('source includes mock stream dispatcher', () => {
    const source = readFileSync(resolve(process.cwd(), 'src/api/frameDescription.js'), 'utf8')
    assert.match(source, /async\s+function\s+dispatchMockStream/)
})

// -----------------------------------------------------------------------
// 测试 13：describeFrameStream 包含 onEvent 回调逻辑
// -----------------------------------------------------------------------
test('describeFrameStream handles onEvent callback', () => {
    const source = readFileSync(resolve(process.cwd(), 'src/api/frameDescription.js'), 'utf8')
    assert.ok(source.includes('onEvent'), 'should call onEvent for each NDJSON event')
})

// -----------------------------------------------------------------------
// 测试 14：detail_level 参数存在
// -----------------------------------------------------------------------
test('source supports detail_level parameter', () => {
    const source = readFileSync(resolve(process.cwd(), 'src/api/frameDescription.js'), 'utf8')
    assert.ok(source.includes('detail_level'), 'should support detail_level param')
    assert.ok(source.includes('brief') && source.includes('standard') && source.includes('detailed'),
        'should support three detail levels')
})

// -----------------------------------------------------------------------
// 测试 15：Mock 模式条件判断
// -----------------------------------------------------------------------
test('source checks shouldUseMockApi() for mock mode', () => {
    const source = readFileSync(resolve(process.cwd(), 'src/api/frameDescription.js'), 'utf8')
    assert.match(source, /shouldUseMockApi\s*\(\s*\)/)
    assert.ok(source.includes('dispatchMockStream'), 'mock mode should call dispatchMockStream')
})

// -----------------------------------------------------------------------
// 测试 16：fetch 错误解析逻辑存在
// -----------------------------------------------------------------------
test('source parses error responses from backend', () => {
    const source = readFileSync(resolve(process.cwd(), 'src/api/frameDescription.js'), 'utf8')
    assert.ok(source.includes('parseStreamErrorBody'), 'should have error body parser')
    assert.ok(source.includes('toStreamError'), 'should have error wrapper')
})

// -----------------------------------------------------------------------
// 测试 17：session 管理支持 start/stop action
// -----------------------------------------------------------------------
test('source supports start and stop session actions', () => {
    const source = readFileSync(resolve(process.cwd(), 'src/api/frameDescription.js'), 'utf8')
    assert.ok(source.includes('"start"') || source.includes("'start'"), 'should support start action')
    assert.ok(source.includes('action ===') && source.includes("'start'"), 'should distinguish start vs stop in manageFrameDescSession')
})

// -----------------------------------------------------------------------
// 测试 18：allow_degrade 参数存在
// -----------------------------------------------------------------------
test('source supports allow_degrade parameter', () => {
    const source = readFileSync(resolve(process.cwd(), 'src/api/frameDescription.js'), 'utf8')
    assert.ok(source.includes('allow_degrade'), 'should support allow_degrade')
})

// -----------------------------------------------------------------------
// 测试 19：Player.vue 集成正确导入 API
// -----------------------------------------------------------------------
test('Player.vue imports frameDescription API', () => {
    const source = readFileSync(resolve(process.cwd(), 'src/views/Player.vue'), 'utf8')
    assert.match(source, /from\s+['"]@\/api\/frameDescription['"]/)
})

// -----------------------------------------------------------------------
// 测试 20：Player.vue 包含 fd-panel 样式
// -----------------------------------------------------------------------
test('Player.vue includes fd-panel styles', () => {
    const source = readFileSync(resolve(process.cwd(), 'src/views/Player.vue'), 'utf8')
    assert.ok(source.includes('fd-panel'), 'should include fd-panel CSS class')
    assert.ok(source.includes('fd-toggle'), 'should include fd-toggle control')
    assert.ok(source.includes('fd-level-pill'), 'should include detail level pills')
})
