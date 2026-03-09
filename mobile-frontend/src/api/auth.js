import request from '@/utils/request'

const normalize = (payload) => {
  const data = payload?.data ?? payload
  const success = Boolean(data?.success ?? data?.ok ?? data?.token ?? data?.user)
  const user = data?.user ?? data?.data?.user ?? null
  const token = data?.token ?? data?.data?.token ?? null
  const message = data?.message ?? data?.msg ?? ''
  return { success, user, token, message, raw: data }
}

export async function login(username, password) {
  const res = await request({ url: '/api/auth/login', method: 'post', data: { username, password } })
  return normalize(res)
}

export async function register(userData) {
  const res = await request({ url: '/api/auth/register', method: 'post', data: userData })
  return normalize(res)
}

export async function me() {
  const res = await request({ url: '/api/auth/user', method: 'get' })
  return normalize(res)
}

export async function logout() {
  const res = await request({ url: '/api/auth/logout', method: 'post' })
  return normalize(res)
}

