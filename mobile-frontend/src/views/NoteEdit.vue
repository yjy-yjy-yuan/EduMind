<template>
  <div class="page">
    <header class="topbar">
      <button class="back" @click="router.back()">‹</button>
      <div class="topbar-title">{{ isNew ? '新建笔记' : '编辑笔记' }}</div>
      <button class="link" @click="save" :disabled="saving">{{ saving ? '…' : '保存' }}</button>
    </header>

    <div v-if="error" class="alert alert--bad">{{ error }}</div>

    <div class="card">
      <div class="label">标题</div>
      <input class="input" v-model.trim="form.title" placeholder="请输入标题" />
      <div class="label">内容</div>
      <textarea class="textarea" v-model="form.content" placeholder="请输入内容"></textarea>
    </div>

    <button v-if="!isNew" class="danger" @click="remove" :disabled="saving">删除</button>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { createNote, deleteNote, getNote, updateNote } from '@/api/note'

const route = useRoute()
const router = useRouter()
const isNew = computed(() => route.name === 'NoteNew')
const id = computed(() => route.params.id)

const saving = ref(false)
const error = ref('')
const form = reactive({ title: '', content: '' })

const normalizeNote = (payload) => payload?.note || payload?.data || payload || null

const load = async () => {
  if (isNew.value) return
  try {
    const res = await getNote(id.value)
    const note = normalizeNote(res.data)
    if (note) {
      form.title = note.title || ''
      form.content = note.content || ''
    }
  } catch (e) {
    error.value = e?.message || '加载失败'
  }
}

const save = async () => {
  if (saving.value) return
  saving.value = true
  error.value = ''
  try {
    if (!form.title) {
      error.value = '请填写标题'
      return
    }
    if (isNew.value) {
      await createNote({ title: form.title, content: form.content })
      router.replace('/notes')
    } else {
      await updateNote(id.value, { title: form.title, content: form.content })
      router.replace('/notes')
    }
  } catch (e) {
    error.value = e?.message || '保存失败'
  } finally {
    saving.value = false
  }
}

const remove = async () => {
  const ok = window.confirm('确认删除该笔记？')
  if (!ok) return
  saving.value = true
  error.value = ''
  try {
    await deleteNote(id.value)
    router.replace('/notes')
  } catch (e) {
    error.value = e?.message || '删除失败'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.page {
  max-width: 520px;
  margin: 0 auto;
  padding: 16px 16px 0;
}

.topbar {
  display: grid;
  grid-template-columns: 40px 1fr 56px;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.topbar-title {
  text-align: center;
  font-weight: 900;
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

.link {
  border: 0;
  background: transparent;
  color: var(--primary);
  font-weight: 900;
  justify-self: end;
}

.alert {
  padding: 10px 12px;
  border-radius: 12px;
  font-weight: 800;
  margin-bottom: 10px;
}

.alert--bad {
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
}

.card {
  background: var(--card);
  border-radius: var(--radius);
  padding: 14px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
  display: grid;
  gap: 8px;
}

.label {
  font-size: 12px;
  color: var(--muted);
  font-weight: 900;
  margin-top: 8px;
}

.input,
.textarea {
  width: 100%;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 12px;
  padding: 10px 12px;
  outline: none;
  font-size: 14px;
}

.textarea {
  min-height: 220px;
  resize: vertical;
  line-height: 1.6;
}

.danger {
  margin-top: 12px;
  width: 100%;
  border: 0;
  background: rgba(239, 68, 68, 0.12);
  color: #b91c1c;
  border-radius: 14px;
  padding: 12px;
  font-weight: 900;
}

.danger:disabled {
  opacity: 0.6;
}
</style>
