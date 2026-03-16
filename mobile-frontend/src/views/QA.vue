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

    <div ref="chatRef" class="chat">
      <div v-if="messages.length === 0" class="empty">输入问题开始对话。</div>
      <div v-for="(m, idx) in messages" :key="idx" class="msg" :class="m.role">
        <div class="bubble">
          <div class="role">{{ m.role === 'user' ? '我' : 'AI' }}</div>
          <div class="text">{{ m.text }}</div>
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
import { askQuestion } from '@/api/qa'
import { storageGet, storageSet } from '@/utils/storage'

const QA_PROVIDER_KEY = 'm_qa_provider'
const PROVIDER_OPTIONS = Object.freeze([
  { value: 'qwen', label: '通义千问' },
  { value: 'deepseek', label: 'DeepSeek' }
])

const normalizeProvider = (value) => {
  const text = String(value || '').trim().toLowerCase()
  return PROVIDER_OPTIONS.some((item) => item.value === text) ? text : 'qwen'
}

const route = useRoute()
const router = useRouter()
const videoId = computed(() => route.query.videoId || '')

const chatRef = ref(null)
const question = ref('')
const asking = ref(false)
const messages = ref([])
const provider = ref(normalizeProvider(storageGet(QA_PROVIDER_KEY)))

const scrollToBottom = async () => {
  await nextTick()
  const el = chatRef.value
  if (el) el.scrollTop = el.scrollHeight
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

const send = async () => {
  if (!question.value || asking.value) return
  const q = question.value
  const historyPayload = buildHistoryPayload()
  question.value = ''
  messages.value.push({ role: 'user', text: q })
  await scrollToBottom()

  asking.value = true
  try {
    const res = await askQuestion({
      question: q,
      video_id: videoId.value ? Number(videoId.value) : undefined,
      mode: videoId.value ? 'video' : 'free',
      provider: provider.value,
      history: historyPayload
    })
    const payload = res.data || {}
    const answer = payload.answer || payload.data?.answer || payload.result || payload.text || '（无返回内容）'
    messages.value.push({
      role: 'ai',
      text: String(answer),
      providerLabel: String(payload.provider_label || (provider.value === 'deepseek' ? 'DeepSeek' : '通义千问')),
      model: String(payload.model || ''),
      references: Array.isArray(payload.references) ? payload.references : []
    })
  } catch (e) {
    messages.value.push({ role: 'ai', text: extractErrorMessage(e, '请求失败，请稍后再试。') })
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

.chat {
  flex: 1;
  overflow: auto;
  background: var(--card);
  border-radius: var(--radius);
  padding: 12px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
}

.empty {
  color: var(--muted);
  font-size: 13px;
}

.msg {
  display: flex;
  margin-bottom: 10px;
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

.text {
  margin-top: 4px;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
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
  margin-top: 10px;
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
</style>
