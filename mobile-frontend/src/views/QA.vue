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

    <div v-if="normalizedVideoId" class="note-entry">
      <button type="button" class="note-entry__btn" @click="openVideoNoteEditor">记笔记（带当前视频）</button>
      <span class="note-entry__tip">会把 videoId 传入笔记编辑页，便于与问答同一上下文整理结论。</span>
    </div>

    <div class="mode-panel">
      <div class="mode-row">
        <button
          v-for="item in CHAT_MODE_OPTIONS"
          :key="item.value"
          class="mode-chip"
          :class="{ 'mode-chip--active': chatMode === item.value }"
          :disabled="asking"
          @click="selectChatMode(item.value)"
        >
          {{ item.label }}
        </button>
      </div>
      <div class="mode-panel__hint">
        {{ chatMode === 'deep_think' ? '已开启深度思考，会先进行推理再组织回答，质量更稳但通常更慢。' : '优先直接回答，响应更快速；通义千问不可用时自动切换 DeepSeek 兜底。' }}
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

    <div class="inputbar">
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
import { computed, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { askQuestionStream, getQuestionHistory } from '@/api/qa'
import {
  answerOfflineFromContext,
  buildVideoMemoryContext,
  getOfflineQaMessages,
  offlineMemorySync,
  persistQuestionResult,
  saveOfflineQuestion,
  shouldUseOfflineMemoryMode
} from '@/services/offlineMemory'
import { storageGet, storageRemove, storageSet } from '@/utils/storage'

const QA_CHAT_MODE_KEY = 'm_qa_chat_mode'
const QA_SPACE_CACHE_PREFIX = 'm_qa_space'
const CHAT_MODE_OPTIONS = Object.freeze([
  { value: 'direct', label: '直接回答' },
  { value: 'deep_think', label: '深度思考' }
])

const parseJSON = (text, fallback = null) => {
  if (!text) return fallback
  try {
    return JSON.parse(text)
  } catch {
    return fallback
  }
}

const normalizeChatMode = (value) => {
  const text = String(value || '').trim().toLowerCase()
  return CHAT_MODE_OPTIONS.some((item) => item.value === text) ? text : 'direct'
}

const normalizeProgress = (value) => {
  const num = Number(value)
  if (!Number.isFinite(num)) return 0
  return Math.max(0, Math.min(100, Math.round(num)))
}

const normalizeReferences = (value) => {
  if (!Array.isArray(value)) return []
  return value.map((item, index) => ({
    index: Number(item?.index || index + 1),
    source_type: String(item?.source_type || ''),
    label: String(item?.label || ''),
    time_range: String(item?.time_range || ''),
    preview: String(item?.preview || '')
  }))
}

const normalizeMessage = (item) => {
  const role = item?.role === 'assistant' ? 'ai' : String(item?.role || 'user')
  return {
    role: role === 'ai' ? 'ai' : 'user',
    text: String(item?.text || item?.content || ''),
    providerLabel: String(item?.providerLabel || item?.provider_label || ''),
    model: String(item?.model || ''),
    references: normalizeReferences(item?.references),
    loading: Boolean(item?.loading),
    statusText: String(item?.statusText || item?.status_text || ''),
    progress: typeof item?.progress === 'undefined' ? undefined : normalizeProgress(item.progress)
  }
}

const normalizeMessageList = (items) => {
  if (!Array.isArray(items)) return []
  return items
    .map((item) => normalizeMessage(item))
    .filter((item) => item.role && (item.text || item.loading || item.statusText))
}

const stripMessageForCache = (item) => {
  const normalized = normalizeMessage(item)
  if (normalized.role === 'ai' && normalized.loading) return null
  return {
    role: normalized.role,
    text: normalized.text,
    providerLabel: normalized.providerLabel,
    model: normalized.model,
    references: normalized.references
  }
}

const resolveCurrentUserId = () => {
  const user = parseJSON(storageGet('m_user'), null)
  const numericId = Number(user?.id)
  return Number.isInteger(numericId) && numericId > 0 ? numericId : null
}

const buildQaSpaceCacheKey = ({ userId, chatMode, videoId, mode }) => {
  const scopeUser = userId == null ? 'anon' : `user_${userId}`
  const scopeVideo = videoId == null ? 'video_none' : `video_${videoId}`
  return `${QA_SPACE_CACHE_PREFIX}:${mode}:${scopeUser}:${scopeVideo}:${chatMode}`
}

const route = useRoute()
const router = useRouter()
const rawVideoId = computed(() => route.query.videoId || '')
const videoId = computed(() => rawVideoId.value)
const rawVideoTitle = computed(() => String(route.query.videoTitle || '').trim())
const normalizedVideoId = computed(() => {
  const numericId = Number(rawVideoId.value)
  return Number.isInteger(numericId) && numericId > 0 ? numericId : null
})

const openVideoNoteEditor = () => {
  if (!normalizedVideoId.value) return
  const query = { videoId: String(normalizedVideoId.value) }
  if (rawVideoTitle.value) query.videoTitle = rawVideoTitle.value
  router.push({ path: '/notes/new', query })
}
const currentMode = computed(() => (normalizedVideoId.value ? 'video' : 'free'))
const currentUserId = computed(() => resolveCurrentUserId())

const chatRef = ref(null)
const question = ref('')
const asking = ref(false)
const chatMode = ref(normalizeChatMode(storageGet(QA_CHAT_MODE_KEY)))
const messageSpaces = ref({})
const remoteHydratedSpaces = ref({})
let historyRestoreSequence = 0

const currentSpaceKey = computed(() =>
  buildQaSpaceCacheKey({
    userId: currentUserId.value,
    chatMode: chatMode.value,
    videoId: normalizedVideoId.value,
    mode: currentMode.value
  })
)

const ensureSpaceMessages = (spaceKey) => {
  if (!Array.isArray(messageSpaces.value[spaceKey])) {
    messageSpaces.value[spaceKey] = []
  }
  return messageSpaces.value[spaceKey]
}

const messages = computed({
  get() {
    return ensureSpaceMessages(currentSpaceKey.value)
  },
  set(next) {
    messageSpaces.value[currentSpaceKey.value] = Array.isArray(next) ? next : []
  }
})

const shouldRenderChat = computed(() => messages.value.length > 0)
const scrollToBottom = async () => {
  await nextTick()
  const el = chatRef.value
  if (el) el.scrollTop = el.scrollHeight
}

const loadCachedSpaceMessages = (spaceKey) => {
  return normalizeMessageList(parseJSON(storageGet(spaceKey), []))
}

const persistSpaceMessages = (spaceKey = currentSpaceKey.value) => {
  const currentMessages = ensureSpaceMessages(spaceKey)
  const cachedMessages = currentMessages
    .map((item) => stripMessageForCache(item))
    .filter(Boolean)
  storageSet(spaceKey, JSON.stringify(cachedMessages))
}

const buildMessageSignature = (item) => {
  const normalized = normalizeMessage(item)
  return `${normalized.role}:${normalized.text}:${normalized.providerLabel}:${normalized.model}`
}

const mergeMessageLists = (primary = [], secondary = []) => {
  const merged = []
  const seen = new Set()
  ;[...primary, ...secondary].forEach((item) => {
    const normalized = normalizeMessage(item)
    const signature = buildMessageSignature(normalized)
    if (!signature || seen.has(signature)) return
    seen.add(signature)
    merged.push(normalized)
  })
  return merged
}

const buildHistoryPayload = () => {
  return messages.value
    .filter((item) => !item.loading)
    .slice(-8)
    .map((item) => ({
      role: item.role === 'ai' ? 'assistant' : 'user',
      content: String(item.text || '')
    }))
}

const loadOfflineSpaceMessages = async () => {
  const rows = await getOfflineQaMessages({
    videoId: normalizedVideoId.value ?? null,
    chatMode: chatMode.value,
    mode: currentMode.value,
    userId: currentUserId.value ?? null
  })
  return normalizeMessageList(rows)
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

const restoreCurrentSpace = async () => {
  const spaceKey = currentSpaceKey.value
  const requestId = ++historyRestoreSequence
  if (!Array.isArray(messageSpaces.value[spaceKey])) {
    messageSpaces.value[spaceKey] = loadCachedSpaceMessages(spaceKey)
  }

  if (remoteHydratedSpaces.value[spaceKey]) {
    const offlineMessages = await loadOfflineSpaceMessages()
    messageSpaces.value[spaceKey] = mergeMessageLists(messageSpaces.value[spaceKey], offlineMessages)
    await scrollToBottom()
    return
  }

  if (currentMode.value !== 'video' || normalizedVideoId.value == null || currentUserId.value == null) {
    const offlineMessages = await loadOfflineSpaceMessages()
    messageSpaces.value[spaceKey] = mergeMessageLists(messageSpaces.value[spaceKey], offlineMessages)
    await scrollToBottom()
    return
  }

  try {
    const res = await getQuestionHistory({
      user_id: currentUserId.value,
      video_id: normalizedVideoId.value,
      mode: currentMode.value
    })
    if (requestId !== historyRestoreSequence || spaceKey !== currentSpaceKey.value) return

    const payload = res.data || {}
    const remoteMessages = normalizeMessageList(payload.messages)
    if (remoteMessages.length > 0) {
      messageSpaces.value[spaceKey] = mergeMessageLists(remoteMessages, messageSpaces.value[spaceKey])
    }
    remoteHydratedSpaces.value[spaceKey] = true
    const offlineMessages = await loadOfflineSpaceMessages()
    messageSpaces.value[spaceKey] = mergeMessageLists(messageSpaces.value[spaceKey], offlineMessages)
    persistSpaceMessages(spaceKey)
  } catch (error) {
    if (requestId !== historyRestoreSequence || spaceKey !== currentSpaceKey.value) return
    const offlineMessages = await loadOfflineSpaceMessages()
    messageSpaces.value[spaceKey] = mergeMessageLists(messageSpaces.value[spaceKey], offlineMessages)
  } finally {
    if (requestId === historyRestoreSequence && spaceKey === currentSpaceKey.value) {
      await scrollToBottom()
    }
  }
}

const selectChatMode = (value) => {
  const next = normalizeChatMode(value)
  chatMode.value = next
  try {
    storageSet(QA_CHAT_MODE_KEY, next)
  } catch {
    // ignore storage errors in restricted WebView contexts
  }
}

const buildPendingAiMessage = () => {
  const isDeepThink = chatMode.value === 'deep_think'
  return {
    role: 'ai',
    text: '',
    providerLabel: isDeepThink ? 'DeepSeek' : '通义千问',
    model: isDeepThink ? 'deepseek-reasoner' : 'qwen-plus',
    references: [],
    loading: true,
    statusText: '问题已提交，等待处理',
    progress: 5
  }
}

const persistQuestionToOfflineMemory = async ({ questionText, answerText, references, source, model, serverId, historyPayload }) => {
  const payload = {
    local_id: null,
    server_id: serverId || null,
    question: questionText,
    answer: answerText,
    references,
    video_id: normalizedVideoId.value ?? null,
    user_id: currentUserId.value ?? null,
    mode: currentMode.value,
    chat_mode: chatMode.value,
    model,
    history: historyPayload,
    source
  }

  if (source === 'offline') {
    await saveOfflineQuestion(payload)
    return
  }

  await persistQuestionResult(payload)
}

const runOfflineAnswer = async ({ questionText, historyPayload, pendingAiMessage }) => {
  const context = await buildVideoMemoryContext(normalizedVideoId.value ?? null)
  const offlineResult = answerOfflineFromContext(context, questionText)
  pendingAiMessage.providerLabel = '离线记忆'
  pendingAiMessage.model = 'indexeddb-context'
  pendingAiMessage.references = offlineResult.references
  pendingAiMessage.statusText = '已使用本地离线记忆回答'
  pendingAiMessage.progress = 100
  pendingAiMessage.loading = false
  pendingAiMessage.text = offlineResult.answer
  await persistQuestionToOfflineMemory({
    questionText,
    answerText: offlineResult.answer,
    references: offlineResult.references,
    source: 'offline',
    model: 'indexeddb-context',
    historyPayload
  })
}

const applyStreamEventToMessage = async (message, event) => {
  if (!message || !event || typeof event !== 'object') return

  if (event.provider_label) message.providerLabel = String(event.provider_label)
  if (event.model) message.model = String(event.model)
  if (Array.isArray(event.references)) message.references = normalizeReferences(event.references)
  if (typeof event.progress !== 'undefined') message.progress = normalizeProgress(event.progress)

  if (event.type === 'answer') {
    message.loading = false
    message.statusText = String(event.message || '回答已完成')
    message.progress = 100
    message.text = String(event.answer || '（无返回内容）')
    remoteHydratedSpaces.value[currentSpaceKey.value] = true
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
  messages.value = [...messages.value, { role: 'user', text: q }]
  const pendingAiMessage = buildPendingAiMessage()
  messages.value = [...messages.value, pendingAiMessage]
  await scrollToBottom()

  asking.value = true
  try {
    if (shouldUseOfflineMemoryMode()) {
      await runOfflineAnswer({
        questionText: q,
        historyPayload,
        pendingAiMessage
      })
      persistSpaceMessages()
      return
    }

    const finalEvent = await askQuestionStream(
      {
        user_id: currentUserId.value ?? undefined,
        question: q,
        video_id: normalizedVideoId.value ?? undefined,
        mode: currentMode.value,
        chat_mode: chatMode.value,
        history: historyPayload
      },
      {
        onEvent(event) {
          void applyStreamEventToMessage(pendingAiMessage, event)
        }
      }
    )
    await persistQuestionToOfflineMemory({
      questionText: q,
      answerText: finalEvent?.answer || pendingAiMessage.text,
      references: Array.isArray(finalEvent?.references) ? finalEvent.references : pendingAiMessage.references,
      source: 'online',
      model: finalEvent?.model || pendingAiMessage.model,
      serverId: finalEvent?.id || null,
      historyPayload
    })
    await offlineMemorySync.flush()
    persistSpaceMessages()
  } catch (e) {
    if (shouldUseOfflineMemoryMode(e)) {
      await runOfflineAnswer({
        questionText: q,
        historyPayload,
        pendingAiMessage
      })
    } else {
      pendingAiMessage.loading = false
      pendingAiMessage.statusText = '回答失败'
      pendingAiMessage.progress = 100
      pendingAiMessage.references = []
      pendingAiMessage.text = extractErrorMessage(e, '请求失败，请稍后再试。')
    }
  } finally {
    asking.value = false
    persistSpaceMessages()
    await scrollToBottom()
  }
}

const clear = () => {
  if (asking.value) return
  messages.value = []
  storageRemove(currentSpaceKey.value)
}

const goBack = () => {
  if (window.history.length > 1) router.back()
  else router.replace('/')
}

watch(
  currentSpaceKey,
  () => {
    ensureSpaceMessages(currentSpaceKey.value)
    void restoreCurrentSpace()
  },
  { immediate: true }
)

watch(
  messages,
  () => {
    persistSpaceMessages()
  },
  { deep: true }
)
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
  background: linear-gradient(135deg, #5f477e, #8f73ba);
}

.mode-panel__hint {
  margin-top: 8px;
  font-size: 11px;
  line-height: 1.5;
  color: var(--muted);
}

.progress-track {
  margin-top: 8px;
  width: 100%;
  height: 6px;
  border-radius: 999px;
  background: rgba(32, 42, 55, 0.08);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(135deg, #8b799d, #a48eb5);
}

.chat {
  margin-top: 8px;
  overflow: auto;
  max-height: min(44vh, 320px);
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
  margin-top: 14px;
  display: flex;
  gap: 10px;
  align-items: center;
  background: transparent;
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
  background: linear-gradient(135deg, #a792bc, #7f698f);
}

.send:disabled {
  opacity: 0.6;
}
</style>
<style scoped>
.page {
  padding-top: calc(12px + env(safe-area-inset-top));
  padding-bottom: calc(28px + env(safe-area-inset-bottom));
}

.topbar {
  padding: 10px 12px;
  border-radius: 16px;
  border: 1px solid rgba(32, 42, 55, 0.08);
  background: rgba(242, 235, 248, 0.92);
  box-shadow: 0 10px 20px rgba(101, 87, 117, 0.08);
}

.msg.user .bubble {
  background: linear-gradient(135deg, rgba(139, 121, 157, 0.14), rgba(139, 121, 157, 0.08));
}

.msg.ai .bubble {
  background: rgba(32, 42, 55, 0.08);
}

.input {
  border-radius: 16px;
  border-color: rgba(32, 42, 55, 0.14);
}

.send {
  border-radius: 16px;
  background: linear-gradient(135deg, #8b799d, #a48eb5);
}

.note-entry {
  display: grid;
  gap: 8px;
  margin: 10px 0 4px;
  padding: 12px 14px;
  border-radius: 16px;
  border: 1px solid rgba(95, 71, 126, 0.16);
  background: rgba(242, 235, 248, 0.65);
}

.note-entry__btn {
  justify-self: start;
  border: 0;
  border-radius: 12px;
  padding: 10px 14px;
  font-weight: 800;
  color: #fff;
  background: linear-gradient(135deg, #6b5a7d, #8b799d);
}

.note-entry__tip {
  font-size: 12px;
  line-height: 1.45;
  color: var(--muted, rgba(32, 42, 55, 0.62));
}

@media (max-width: 390px) {
  .mode-row {
    grid-template-columns: 1fr;
  }
}
</style>
