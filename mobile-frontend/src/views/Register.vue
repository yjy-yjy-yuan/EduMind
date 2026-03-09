<template>
  <div class="page">
    <header class="hero">
      <div class="title">创建账号</div>
      <div class="subtitle">移动端注册</div>
    </header>

    <div class="card">
      <div class="label">用户名</div>
      <input class="input" v-model.trim="form.username" placeholder="请输入用户名" />
      <div class="label">邮箱</div>
      <input class="input" v-model.trim="form.email" placeholder="请输入邮箱" />
      <div class="label">密码</div>
      <input class="input" v-model="form.password" type="password" placeholder="请输入密码" @keyup.enter="submit" />
      <button class="btn btn--primary" @click="submit" :disabled="loading">{{ loading ? '提交中…' : '注册' }}</button>
      <button class="link" @click="router.push('/login')">已有账号？去登录</button>
    </div>

    <div v-if="error" class="alert alert--bad">{{ error }}</div>
    <div v-if="ok" class="alert alert--ok">注册成功，请登录。</div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as authStore from '@/store/auth'

const router = useRouter()
const loading = ref(false)
const error = ref('')
const ok = ref(false)
const form = reactive({ username: '', email: '', password: '' })

const submit = async () => {
  if (!form.username || !form.password) {
    error.value = '请填写用户名和密码'
    return
  }
  loading.value = true
  error.value = ''
  ok.value = false
  try {
    const res = await authStore.register({ ...form })
    if (!res.success) {
      error.value = res.message || '注册失败'
      return
    }
    ok.value = true
    router.replace('/login')
  } catch (e) {
    error.value = e?.message || '注册失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.page {
  max-width: 520px;
  margin: 0 auto;
  padding: 16px;
}

.hero {
  padding: 14px;
  border-radius: var(--radius);
  color: #fff;
  background: linear-gradient(135deg, #667eea, #764ba2);
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.25);
}

.title {
  font-size: 18px;
  font-weight: 900;
}

.subtitle {
  margin-top: 6px;
  font-size: 12px;
  opacity: 0.9;
}

.card {
  margin-top: 14px;
  background: var(--card);
  border-radius: var(--radius);
  padding: 14px;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
  display: grid;
  gap: 10px;
}

.label {
  font-size: 12px;
  color: var(--muted);
  font-weight: 900;
}

.input {
  width: 100%;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 12px;
  padding: 12px 12px;
  outline: none;
}

.btn {
  border-radius: 14px;
  padding: 12px;
  font-weight: 900;
  border: 1px solid rgba(0, 0, 0, 0.08);
  background: #fff;
}

.btn--primary {
  border: 0;
  color: #fff;
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.btn:disabled {
  opacity: 0.6;
}

.link {
  border: 0;
  background: transparent;
  color: var(--primary);
  font-weight: 900;
}

.alert {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  font-weight: 800;
}

.alert--ok { background: rgba(34, 197, 94, 0.12); color: #15803d; }
.alert--bad { background: rgba(239, 68, 68, 0.12); color: #b91c1c; }
</style>
