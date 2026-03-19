import request from '@/utils/request'
import { UI_ONLY_MODE } from '@/config'
import { mockLogin, mockLogout, mockMe, mockRegister } from '@/api/mockGateway'

const normalize = (payload) => {
  const data = payload?.data ?? payload
  const success = Boolean(data?.success ?? data?.ok ?? data?.token ?? data?.user)
  const user = data?.user ?? data?.data?.user ?? null
  const token = data?.token ?? data?.data?.token ?? null
  const message = data?.message ?? data?.msg ?? ''
  return { success, user, token, message, raw: data }
}

export async function login(account, password) {
  if (UI_ONLY_MODE) return normalize(await mockLogin(account, password))
  const res = await request({ url: '/api/auth/login', method: 'post', data: { account, password } })
  return normalize(res)
}

export async function register(userData) {
  if (UI_ONLY_MODE) return normalize(await mockRegister(userData))
  const res = await request({ url: '/api/auth/register', method: 'post', data: userData })
  return normalize(res)
}

export async function me() {
  if (UI_ONLY_MODE) return normalize(await mockMe())
  const res = await request({ url: '/api/auth/user', method: 'get' })
  return normalize(res)
}

export async function logout() {
  if (UI_ONLY_MODE) return normalize(await mockLogout())
  const res = await request({ url: '/api/auth/logout', method: 'post' })
  return normalize(res)
}
