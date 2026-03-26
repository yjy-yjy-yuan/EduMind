<template>
  <div class="page">
    <header class="hero">
      <div class="hero__logo">
        <BrandLogo :width="188" />
      </div>
      <div class="title gradient-text">创建账号</div>
      <div class="subtitle">移动端注册</div>
    </header>

    <div class="card">
      <div class="label">邮箱 / 手机号</div>
      <input class="input" v-model.trim="form.contact" placeholder="请输入邮箱或手机号" />
      <div class="label">密码</div>
      <input class="input" v-model="form.password" type="password" placeholder="请输入密码" @keyup.enter="submit" />
      <div class="field-help">密码至少 8 位，且必须包含大小写字母、数字和特殊字符。</div>
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
import BrandLogo from '@/components/BrandLogo.vue'
import * as authStore from '@/store/auth'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
const PHONE_RE = /^(?:\+?86)?1[3-9]\d{9}$/
const STRONG_PASSWORD_RE = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9])\S{8,128}$/

const normalizePhone = (value) => {
  const digits = String(value || '').replace(/\D/g, '')
  if (digits.startsWith('86') && digits.length === 13) return digits.slice(2)
  return digits
}

const router = useRouter()
const loading = ref(false)
const error = ref('')
const ok = ref(false)
const form = reactive({ contact: '', password: '' })
const parseErrorMessage = (e, fallback) => e?.response?.data?.detail || e?.message || fallback

const submit = async () => {
  const contact = String(form.contact || '').trim()
  if (!contact || !form.password) {
    error.value = '请填写邮箱/手机号和密码'
    return
  }

  const payload = { password: form.password }
  const normalizedPhone = normalizePhone(contact)
  if (EMAIL_RE.test(contact.toLowerCase())) {
    payload.email = contact.toLowerCase()
  } else if (PHONE_RE.test(normalizedPhone)) {
    payload.phone = normalizedPhone
  } else {
    error.value = '请输入正确的邮箱或手机号'
    return
  }

  if (!STRONG_PASSWORD_RE.test(form.password)) {
    error.value = '密码至少 8 位，且必须包含大小写字母、数字和特殊字符'
    return
  }
  loading.value = true
  error.value = ''
  ok.value = false
  try {
    const res = await authStore.register(payload)
    if (!res.success) {
      error.value = res.message || '注册失败'
      return
    }
    ok.value = true
    router.replace('/login')
  } catch (e) {
    error.value = parseErrorMessage(e, '注册失败')
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
  background: linear-gradient(135deg, #a792bc, #7f698f);
  box-shadow: 0 10px 30px rgba(139, 121, 157, 0.22);
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

.field-help {
  margin-top: -4px;
  font-size: 12px;
  color: var(--muted);
  line-height: 1.5;
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
  background: linear-gradient(135deg, #a792bc, #7f698f);
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

.alert--ok { background: rgba(200, 171, 108, 0.16); color: #8f7040; }
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
    linear-gradient(145deg, #8b799d, #665775);
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
  background: linear-gradient(145deg, #8b799d, #a48eb5);
}
</style>
