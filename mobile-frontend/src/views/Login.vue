<template>
  <div class="page">
    <header class="hero">
      <div class="hero__logo">
        <BrandLogo :width="188" />
      </div>
      <div class="title gradient-text">视频智能伴学</div>
      <div class="subtitle">移动端登录</div>
    </header>

    <div class="card">
      <div class="label">邮箱 / 手机号</div>
      <input class="input" v-model.trim="form.account" placeholder="请输入邮箱或手机号" />
      <div class="label">密码</div>
      <input class="input" v-model="form.password" type="password" placeholder="请输入密码" @keyup.enter="submit" />
      <button class="btn btn--primary" @click="submit" :disabled="loading">
        {{ loading ? '登录中…' : '登录' }}
      </button>
      <button class="link" @click="router.push('/register')">没有账号？去注册</button>
    </div>

    <div v-if="error" class="alert alert--bad">{{ error }}</div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import BrandLogo from '@/components/BrandLogo.vue'
import * as authStore from '@/store/auth'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const PHONE_RE = /^(?:\+?86)?1[3-9]\d{9}$/
const normalizePhone = (value) => {
  const digits = String(value || '').replace(/\D/g, '')
  if (digits.startsWith('86') && digits.length === 13) return digits.slice(2)
  return digits
}

const router = useRouter()
const route = useRoute()

const loading = ref(false)
const error = ref('')
const form = reactive({ account: '', password: '' })
const parseErrorMessage = (e, fallback) => e?.response?.data?.detail || e?.message || fallback

const submit = async () => {
  const account = String(form.account || '').trim()
  if (!account || !form.password) {
    error.value = '请输入邮箱/手机号和密码'
    return
  }
  const normalizedPhone = normalizePhone(account)
  if (!EMAIL_RE.test(account.toLowerCase()) && !PHONE_RE.test(normalizedPhone)) {
    error.value = '请输入正确的邮箱或手机号'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const res = await authStore.login(account, form.password)
    if (!res.success) {
      error.value = res.message || '登录失败'
      return
    }
    const redirect = route.query.redirect ? String(route.query.redirect) : '/'
    router.replace(redirect)
  } catch (e) {
    error.value = parseErrorMessage(e, '登录失败')
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

.hero__logo {
  margin-bottom: 12px;
  display: inline-flex;
  flex: 0 0 auto;
}

.title {
  font-size: 18px;
  font-weight: 900;
  text-shadow: 0 8px 22px rgba(16, 101, 132, 0.16);
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

.alert--bad { background: rgba(239, 68, 68, 0.12); color: #b91c1c; }
</style>
<style scoped>
.page {
  padding-top: calc(22px + env(safe-area-inset-top));
}

.hero {
  border-radius: 26px;
  padding: 18px;
  background:
    radial-gradient(circle at right top, rgba(255, 255, 255, 0.24), transparent 44%),
    linear-gradient(145deg, #1f7a8c, #0f5f70);
}

.title {
  font-size: 22px;
}

.card {
  border-radius: 24px;
  padding: 16px;
}

.input {
  border-radius: 14px;
  border-color: rgba(32, 42, 55, 0.14);
}

.btn {
  border-radius: 16px;
}

.btn--primary {
  background: linear-gradient(145deg, #1f7a8c, #3d8da0);
}
</style>
