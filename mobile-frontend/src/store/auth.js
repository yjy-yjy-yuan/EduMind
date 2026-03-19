import { reactive, readonly } from 'vue'
import * as authApi from '@/api/auth'
import { storageGet, storageRemove, storageSet } from '@/utils/storage'

const parseJSON = (text, fallback = null) => {
  if (!text) return fallback
  try {
    return JSON.parse(text)
  } catch {
    return fallback
  }
}

const initialUser = parseJSON(storageGet('m_user'), null)
const initialToken = storageGet('m_token')

const state = reactive({
  user: initialUser,
  token: initialToken || null,
  isAuthenticated: Boolean(initialUser || initialToken)
})

const persist = () => {
  if (state.user) storageSet('m_user', JSON.stringify(state.user))
  else storageRemove('m_user')
  if (state.token) storageSet('m_token', state.token)
  else storageRemove('m_token')
  state.isAuthenticated = Boolean(state.user || state.token)
}

export function getState() {
  return readonly(state)
}

export async function login(account, password) {
  const res = await authApi.login(account, password)
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
