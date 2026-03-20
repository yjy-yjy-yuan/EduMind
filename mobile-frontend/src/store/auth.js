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

const applyAuthState = (res) => {
  if (!res?.success) return res
  if (res.user) state.user = res.user
  if (res.token) state.token = res.token
  persist()
  return res
}

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
  return applyAuthState(await authApi.login(account, password))
}

export async function register(userData) {
  return authApi.register(userData)
}

export async function fetchMe() {
  return applyAuthState(await authApi.me())
}

export async function updateProfile(profileData) {
  return applyAuthState(await authApi.updateProfile(profileData))
}

export async function uploadAvatar(file) {
  return applyAuthState(await authApi.uploadAvatar(file))
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
