<template>
  <div class="page">
    <header class="topbar">
      <button class="back" @click="goBack">‹</button>
      <h2>AI 问答</h2>
      <button class="link" @click="clear" :disabled="asking">清空</button>
    </header>

    <div class="hint">
      {{ videoId ? `当前为视频上下文问答 · videoId=${videoId}` : '当前为通用问答' }}
    </div>

    <div class="provider-row">
      <button
        v-for="item in PROVIDER_OPTIONS"
        :key="item.value"
        class="provider-chip"
        :class="{ 'provider-chip--active': provider === item.value }"
        :disabled="asking"
        @click="selectProvider(item.value)"
      >
        {{ item.label }}
      </button>
    </div>

    <div v-if="isDeepSeekProvider" class="mode-panel">
      <div class="mode-panel__label">DeepSeek 回答方式</div>
      <div class="mode-row">
        <button
          v-for="item in DEEPSEEK_ANSWER_MODE_OPTIONS"
          :key="item.value"
          class="mode-chip"
          :class="{ 'mode-chip--active': deepSeekAnswerMode === item.value }"
          :disabled="asking"
          @click="selectDeepSeekAnswerMode(item.value)"
        >
          {{ item.label }}
        </button>
      </div>
      <div class="mode-panel__hint">
        {{ deepThinkingEnabled ? '先进行推理，再组织回答，质量更稳但通常更慢。' : '优先直接回答，首字和整体返回速度更快。' }}
      </div>
    </div>

    <div v-if="runtimeStatus" class="runtime-status" :class="{ 'runtime-status--done': !runtimeStatus.loading }">
      <div class="runtime-status__top">
        <span class="runtime-status__label">AI 进度</span>
        <strong class="runtime-status__percent">{{ runtimeStatus.progress }}%</strong>
      </div>
      <div class="runtime-status__text">{{ runtimeStatus.text }}</div>
      <div class="runtime-status__track">
        <div class="runtime-status__fill" :style="{ width: `${runtimeStatus.progress}%` }"></div>
      </div>
    </div>

    <div v-if="shouldRenderChat" ref="chatRef" class="chat">
      <div v-for="(m, idx) in messages" :key="idx" class="msg" :class="m.role">
        <div class="bubble">
          <div class="role">{{ m.role === 'user' ? '我' : 'AI' }}</div>
          <div v-if="m.role === 'ai' && m.statusText" class="progress-meta" :class="{ 'progress-meta--done': !m.loading }">
            <span>{{ m.statusText }}</span>
            <strong>{{ normalizeProgress(m.progress) }}%</strong>
          </div>
          <div v-if="m.role === 'ai' && typeof m.progress !== 'undefined'" class="progress-track">
            <div class="progress-fill" :style="{ width: `${normalizeProgress(m.progress)}%` }"></div>
          </div>
          <div class="text" :class="{ 'text--placeholder': m.role === 'ai' && m.loading && !m.text }">
            {{ m.text || (m.role === 'ai' && m.loading ? '正在处理中，请稍候…' : '（无返回内容）') }}
          </div>
          <div v-if="m.role === 'ai' && (m.providerLabel || m.model)" class="msg-meta">
            {{ m.providerLabel || '在线模型' }}<span v-if="m.model"> · {{ m.model }}</span>
          </div>
          <div v-if="m.role === 'ai' && m.references?.length" class="refs">
            <div v-for="ref in m.references" :key="`${idx}-${ref.index}`" class="ref-item">
              [{{ ref.index }}] {{ ref.label }}<span v-if="ref.time_range"> · {{ ref.time_range }}</span> · {{ ref.preview }}
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-else class="empty-hint">输入问题开始对话。</div>

    <div class="inputbar safe-bottom">
      <input
        class="input"
        v-model.trim="question"
        :placeholder="videoId ? '基于当前视频内容提问…' : '请输入问题…'"
        :disabled="asking"
        @keyup.enter="send"
      />
      <button class="send" @click="send" :disabled="asking || !question">{{ asking ? '…' : '发送' }}</button>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { askQuestionStream } from '@/api/qa'
import { storageGet, storageSet } from '@/utils/storage'

const QA_PROVIDER_KEY = 'm_qa_provider'
const DEEPSEEK_ANSWER_MODE_KEY = 'm_deepseek_answer_mode'
const PROVIDER_OPTIONS = Object.freeze([
  { value: 'qwen', label: '通义千问' },
  { value: 'deepseek', label: 'DeepSeek' }
])
const DEEPSEEK_ANSWER_MODE_OPTIONS = Object.freeze([
  { value: 'direct', label: '直接回答' },
  { value: 'reasoning', label: '先思考再回答' }
])

const normalizeProvider = (value) => {
  const text = String(value || '').trim().toLowerCase()
  return PROVIDER_OPTIONS.some((item) => item.value === text) ? text : 'qwen'
}

const normalizeDeepSeekAnswerMode = (value) => {
  const text = String(value || '').trim().toLowerCase()
  return DEEPSEEK_ANSWER_MODE_OPTIONS.some((item) => item.value === text) ? text : 'direct'
}

const route = useRoute()
const router = useRouter()
const videoId = computed(() => route.query.videoId || '')

const chatRef = ref(null)
const question = ref('')
const asking = ref(false)
const messages = ref([])
const provider = ref(normalizeProvider(storageGet(QA_PROVIDER_KEY)))
const deepSeekAnswerMode = ref(normalizeDeepSeekAnswerMode(storageGet(DEEPSEEK_ANSWER_MODE_KEY)))
const isDeepSeekProvider = computed(() => provider.value === 'deepseek')
const deepThinkingEnabled = computed(() => isDeepSeekProvider.value && deepSeekAnswerMode.value === 'reasoning')
const shouldRenderChat = computed(() => messages.value.length > 0)
const runtimeStatus = computed(() => {
  for (let index = messages.value.length - 1; index >= 0; index -= 1) {
    const item = messages.value[index]
    if (item.role === 'ai' && item.statusText) {
      return {
        text: String(item.statusText),
        progress: normalizeProgress(item.progress),
        loading: Boolean(item.loading)
      }
    }
  }
  return null
})

const scrollToBottom = async () => {
  await nextTick()
  const el = chatRef.value
  if (el) el.scrollTop = el.scrollHeight
}

const normalizeProgress = (value) => {
  const num = Number(value)
  if (!Number.isFinite(num)) return 0
  return Math.max(0, Math.min(100, Math.round(num)))
}

const buildHistoryPayload = () => {
  return messages.value.slice(-8).map((item) => ({
    role: item.role === 'ai' ? 'assistant' : 'user',
    content: String(item.text || '')
  }))
}

const extractErrorMessage = (err, fallback) => {
  const detail = err?.response?.data?.detail
  if (Array.isArray(detail)) {
    const first = detail.find(Boolean)
    if (typeof first === 'string') return first
    if (first?.msg) return first.msg
  }
  if (typeof detail === 'string' && detail.trim()) return detail.trim()
  const text = err?.response?.data?.message || err?.response?.data?.msg
  if (typeof text === 'string' && text.trim()) return text.trim()
  return err?.message || fallback
}

const selectProvider = (value) => {
  const next = normalizeProvider(value)
  provider.value = next
  try {
    storageSet(QA_PROVIDER_KEY, next)
  } catch {
    // ignore storage errors in restricted WebView contexts
  }
}

const selectDeepSeekAnswerMode = (value) => {
  const next = normalizeDeepSeekAnswerMode(value)
  deepSeekAnswerMode.value = next
  try {
    storageSet(DEEPSEEK_ANSWER_MODE_KEY, next)
  } catch {
    // ignore storage errors in restricted WebView contexts
  }
}

const buildPendingAiMessage = () => ({
  role: 'ai',
  text: '',
  providerLabel: provider.value === 'deepseek' ? 'DeepSeek' : '通义千问',
  model: '',
  references: [],
  loading: true,
  statusText: '问题已提交，等待处理',
  progress: 5
})

const applyStreamEventToMessage = async (message, event) => {
  if (!message || !event || typeof event !== 'object') return

  if (event.provider_label) message.providerLabel = String(event.provider_label)
  if (event.model) message.model = String(event.model)
  if (Array.isArray(event.references)) message.references = event.references
  if (typeof event.progress !== 'undefined') message.progress = normalizeProgress(event.progress)

  if (event.type === 'answer') {
    message.loading = false
    message.statusText = String(event.message || '回答已完成')
    message.progress = 100
    message.text = String(event.answer || '（无返回内容）')
  } else if (event.type === 'error') {
    message.loading = false
    message.statusText = String(event.message || '回答失败')
    message.progress = 100
    message.text = String(event.detail || event.message || '请求失败，请稍后再试。')
    message.references = []
  } else if (event.type === 'status') {
    message.statusText = String(event.message || message.statusText || '正在处理中')
  }

  await scrollToBottom()
}

const send = async () => {
  if (!question.value || asking.value) return
  const q = question.value
  const historyPayload = buildHistoryPayload()
  question.value = ''
  messages.value.push({ role: 'user', text: q })
  const pendingAiMessage = buildPendingAiMessage()
  messages.value.push(pendingAiMessage)
  await scrollToBottom()

  asking.value = true
  try {
    await askQuestionStream(
      {
        question: q,
        video_id: videoId.value ? Number(videoId.value) : undefined,
        mode: videoId.value ? 'video' : 'free',
        provider: provider.value,
        deep_thinking: deepThinkingEnabled.value,
        history: historyPayload
      },
      {
        onEvent(event) {
          void applyStreamEventToMessage(pendingAiMessage, event)
        }
      }
    )
  } catch (e) {
    pendingAiMessage.loading = false
    pendingAiMessage.statusText = '回答失败'
    pendingAiMessage.progress = 100
    pendingAiMessage.references = []
    pendingAiMessage.text = extractErrorMessage(e, '请求失败，请稍后再试。')
  } finally {
    asking.value = false
    await scrollToBottom()
  }
}

const clear = () => {
  if (asking.value) return
  messages.value = []
}

const goBack = () => {
  if (window.history.length > 1) router.back()
  else router.replace('/')
}
</script>

<style scoped>
.page {
  max-width: 520px;
  margin: 0 auto;
  padding: 16px 16px 0;
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

.topbar {
  display: grid;
  grid-template-columns: 40px 1fr 56px;
  align-items: center;
  margin-bottom: 10px;
}

.back {
  border: 0;
  background: var(--card);
  border-radius: 12px;
  height: 36px;
  width: 40px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
  font-size: 22px;
  line-height: 1;
}

.topbar h2 {
  margin: 0;
  font-size: 16px;
  text-align: center;
}

.link {
  border: 0;
  background: transparent;
  color: var(--primary);
  font-weight: 900;
}

.hint {
  font-size: 12px;
  color: var(--muted);
  margin-bottom: 8px;
}

.provider-row {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
  flex-wrap: wrap;
}

.provider-chip {
  border: 1px solid rgba(32, 42, 55, 0.12);
  border-radius: 999px;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 700;
  color: var(--text);
  background: rgba(255, 255, 255, 0.9);
}

.provider-chip--active {
  color: #fff;
  border-color: transparent;
  background: linear-gradient(135deg, #1f7a8c, #3d8da0);
}

.mode-panel {
  margin-bottom: 10px;
  padding: 12px;
  border-radius: 16px;
  border: 1px solid rgba(32, 42, 55, 0.08);
  background: rgba(255, 255, 255, 0.82);
}

.mode-panel__label {
  font-size: 12px;
  font-weight: 800;
  color: var(--text);
}

.mode-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 8px;
}

.mode-chip {
  border: 1px solid rgba(32, 42, 55, 0.12);
  border-radius: 14px;
  min-height: 40px;
  padding: 8px 10px;
  font-size: 12px;
  font-weight: 700;
  color: var(--text);
  background: rgba(244, 248, 250, 0.9);
  line-height: 1.35;
  text-align: center;
}

.mode-chip--active {
  color: #fff;
  border-color: transparent;
  background: linear-gradient(135deg, #0f766e, #155e75);
}

.mode-panel__hint {
  margin-top: 8px;
  font-size: 11px;
  line-height: 1.5;
  color: var(--muted);
}

.runtime-status {
  margin-top: 10px;
  padding: 12px;
  border-radius: 16px;
  border: 1px solid rgba(32, 42, 55, 0.08);
  background: rgba(255, 255, 255, 0.86);
  box-shadow: 0 10px 18px rgba(24, 45, 73, 0.06);
}

.runtime-status--done {
  background: rgba(245, 250, 250, 0.9);
}

.runtime-status__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.runtime-status__label {
  font-size: 11px;
  font-weight: 800;
  color: var(--muted);
  letter-spacing: 0.04em;
}

.runtime-status__percent {
  font-size: 12px;
  color: var(--text);
}

.runtime-status__text {
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.5;
  color: var(--text);
}

.runtime-status__track,
.progress-track {
  margin-top: 8px;
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: rgba(32, 42, 55, 0.08);
  overflow: hidden;
}

.runtime-status__fill,
.progress-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(135deg, #1f7a8c, #3d8da0);
}

.chat {
  overflow: auto;
  max-height: min(52vh, 420px);
  min-height: 0;
  background: var(--card);
  border-radius: var(--radius);
  padding: 12px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
}

.empty-hint {
  margin-top: 6px;
  padding: 4px 2px 0;
  color: var(--muted);
  font-size: 13px;
}

.msg {
  display: flex;
  margin-bottom: 10px;
}

.msg:last-child {
  margin-bottom: 0;
}

.msg.user {
  justify-content: flex-end;
}

.bubble {
  max-width: 85%;
  border-radius: 14px;
  padding: 10px 12px;
  background: rgba(79, 70, 229, 0.08);
}

.msg.ai .bubble {
  background: rgba(0, 0, 0, 0.06);
}

.role {
  font-size: 11px;
  font-weight: 900;
  color: var(--muted);
}

.progress-meta {
  margin-top: 4px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-size: 11px;
  line-height: 1.4;
  color: var(--muted);
}

.progress-meta--done {
  color: #166534;
}

.text {
  margin-top: 4px;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.text--placeholder {
  color: var(--muted);
}

.msg-meta {
  margin-top: 8px;
  font-size: 11px;
  color: var(--muted);
}

.refs {
  margin-top: 8px;
  display: grid;
  gap: 6px;
}

.ref-item {
  font-size: 11px;
  line-height: 1.5;
  color: var(--muted);
}

.inputbar {
  margin-top: auto;
  display: flex;
  gap: 10px;
  align-items: center;
  padding-bottom: 10px;
  position: sticky;
  bottom: 0;
  background: var(--bg);
}

.input {
  flex: 1;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 14px;
  padding: 12px 12px;
  outline: none;
}

.send {
  border: 0;
  border-radius: 14px;
  padding: 12px 14px;
  font-weight: 900;
  color: #fff;
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.send:disabled {
  opacity: 0.6;
}
</style>
<style scoped>
.page {
  padding-top: calc(12px + env(safe-area-inset-top));
  min-height: 100dvh;
}

.topbar {
  padding: 10px 12px;
  border-radius: 16px;
  border: 1px solid rgba(32, 42, 55, 0.08);
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 10px 20px rgba(24, 45, 73, 0.08);
}

.chat {
  margin-top: 10px;
  border-radius: 20px;
  border: 1px solid rgba(32, 42, 55, 0.08);
  background: linear-gradient(180deg, #ffffff, #f8fbfd);
  padding: 14px;
}

.msg.user .bubble {
  background: linear-gradient(135deg, rgba(31, 122, 140, 0.14), rgba(31, 122, 140, 0.08));
}

.msg.ai .bubble {
  background: rgba(32, 42, 55, 0.08);
}

.inputbar {
  background: transparent;
}

.input {
  border-radius: 16px;
  border-color: rgba(32, 42, 55, 0.14);
}

.send {
  border-radius: 16px;
  background: linear-gradient(135deg, #1f7a8c, #3d8da0);
}

@media (max-width: 390px) {
  .mode-row {
    grid-template-columns: 1fr;
  }
}
</style>
