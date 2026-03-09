<template>
  <div class="page">
    <header class="topbar">
      <button class="back" @click="goBack">‹</button>
      <h2>AI 问答</h2>
      <button class="link" @click="clear" :disabled="asking">清空</button>
    </header>

    <div v-if="videoId" class="hint">当前为视频问答：videoId={{ videoId }}</div>

    <div ref="chatRef" class="chat">
      <div v-if="messages.length === 0" class="empty">输入问题开始对话。</div>
      <div v-for="(m, idx) in messages" :key="idx" class="msg" :class="m.role">
        <div class="bubble">
          <div class="role">{{ m.role === 'user' ? '我' : 'AI' }}</div>
          <div class="text">{{ m.text }}</div>
        </div>
      </div>
    </div>

    <div class="inputbar safe-bottom">
      <input class="input" v-model.trim="question" placeholder="请输入问题…" :disabled="asking" @keyup.enter="send" />
      <button class="send" @click="send" :disabled="asking || !question">{{ asking ? '…' : '发送' }}</button>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { askQuestion } from '@/api/qa'

const route = useRoute()
const router = useRouter()
const videoId = computed(() => route.query.videoId || '')

const chatRef = ref(null)
const question = ref('')
const asking = ref(false)
const messages = ref([])

const scrollToBottom = async () => {
  await nextTick()
  const el = chatRef.value
  if (el) el.scrollTop = el.scrollHeight
}

const send = async () => {
  if (!question.value || asking.value) return
  const q = question.value
  question.value = ''
  messages.value.push({ role: 'user', text: q })
  await scrollToBottom()

  asking.value = true
  try {
    const res = await askQuestion({
      question: q,
      video_id: videoId.value ? Number(videoId.value) : undefined,
      mode: videoId.value ? 'video' : 'free'
    })
    const payload = res.data || {}
    const answer = payload.answer || payload.data?.answer || payload.result || payload.text || '（无返回内容）'
    messages.value.push({ role: 'ai', text: String(answer) })
  } catch (e) {
    messages.value.push({ role: 'ai', text: '请求失败，请稍后再试。' })
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
