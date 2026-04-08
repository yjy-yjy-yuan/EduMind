import { reactive, readonly } from 'vue'
import { shouldUseMockApi } from '@/config'
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

const isBackendAuthToken = (token) => /^\d+\.(?:\d+\.)?[a-f0-9]{64}$/i.test(String(token || ''))

const storedUser = parseJSON(storageGet('m_user'), null)
const storedToken = storageGet('m_token')
const shouldResetStoredAuth = !shouldUseMockApi() && Boolean(storedUser || storedToken) && !isBackendAuthToken(storedToken)

if (shouldResetStoredAuth) {
  storageRemove('m_user')
  storageRemove('m_token')
}

const initialUser = shouldResetStoredAuth ? null : storedUser
const initialToken = shouldResetStoredAuth ? null : storedToken

const state = reactive({
  user: initialUser,
  token: initialToken || null,
  isAuthenticated: Boolean(initialUser || initialToken)
})

const clearAuthState = () => {
  state.user = null
  state.token = null
  persist()
}

const applyAuthState = (res) => {
  if (!res?.success) return res
  if (res.user) state.user = res.user
  if (res.token) state.token = res.token
  persist()
  return res
}

const runAuthedRequest = async (requester) => {
  try {
    return applyAuthState(await requester())
  } catch (error) {
    if (!shouldUseMockApi() && Number(error?.response?.status) === 401) clearAuthState()
    throw error
  }
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
  return runAuthedRequest(() => authApi.me())
}

export async function updateProfile(profileData) {
  return runAuthedRequest(() => authApi.updateProfile(profileData))
}

export async function uploadAvatar(file) {
  return runAuthedRequest(() => authApi.uploadAvatar(file))
}

export async function logout() {
  try {
    await authApi.logout()
  } finally {
    clearAuthState()
  }
}
