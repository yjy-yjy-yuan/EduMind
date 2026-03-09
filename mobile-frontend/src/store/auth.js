import { reactive, readonly } from 'vue'
import * as authApi from '@/api/auth'

const state = reactive({
  user: JSON.parse(localStorage.getItem('m_user') || 'null'),
  token: localStorage.getItem('m_token') || null,
  isAuthenticated: Boolean(localStorage.getItem('m_user') || localStorage.getItem('m_token'))
})

const persist = () => {
  if (state.user) localStorage.setItem('m_user', JSON.stringify(state.user))
  else localStorage.removeItem('m_user')
  if (state.token) localStorage.setItem('m_token', state.token)
  else localStorage.removeItem('m_token')
  state.isAuthenticated = Boolean(state.user || state.token)
}

export function getState() {
  return readonly(state)
}

export async function login(username, password) {
  const res = await authApi.login(username, password)
  if (res.success) {
    state.user = res.user || state.user
    state.token = res.token || state.token
    persist()
  }
  return res
}

export async function register(userData) {
  return authApi.register(userData)
}

export async function fetchMe() {
  const res = await authApi.me()
  if (res.success && res.user) {
    state.user = res.user
    persist()
  }
  return res
}

export async function logout() {
  try {
    await authApi.logout()
  } finally {
    state.user = null
    state.token = null
    persist()
  }
}

