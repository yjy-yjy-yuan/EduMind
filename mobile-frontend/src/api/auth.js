import request from '@/utils/request'
import { shouldUseMockApi } from '@/config'
import { mockLogin, mockLogout, mockMe, mockRegister, mockUpdateProfile, mockUploadAvatar } from '@/api/mockGateway'

const normalize = (payload) => {
  const data = payload?.data ?? payload
  const success = Boolean(data?.success ?? data?.ok ?? data?.token ?? data?.user)
  const user = data?.user ?? data?.data?.user ?? null
  const token = data?.token ?? data?.data?.token ?? null
  const message = data?.message ?? data?.msg ?? ''
  return { success, user, token, message, raw: data }
}

export async function login(account, password) {
  if (shouldUseMockApi()) return normalize(await mockLogin(account, password))
  const res = await request({ url: '/api/auth/login', method: 'post', data: { account, password } })
  return normalize(res)
}

export async function register(userData) {
  if (shouldUseMockApi()) return normalize(await mockRegister(userData))
  const res = await request({ url: '/api/auth/register', method: 'post', data: userData })
  return normalize(res)
}

export async function me() {
  if (shouldUseMockApi()) return normalize(await mockMe())
  const res = await request({ url: '/api/auth/user', method: 'get' })
  return normalize(res)
}

export async function logout() {
  if (shouldUseMockApi()) return normalize(await mockLogout())
  const res = await request({ url: '/api/auth/logout', method: 'post' })
  return normalize(res)
}

export async function updateProfile(profileData) {
  if (shouldUseMockApi()) return normalize(await mockUpdateProfile(profileData))
  const res = await request({ url: '/api/auth/user/update', method: 'post', data: profileData })
  return normalize(res)
}

export async function uploadAvatar(file) {
  const formData = new FormData()
  formData.append('file', file)

  if (shouldUseMockApi()) return normalize(await mockUploadAvatar(file))
  const res = await request({
    url: '/api/auth/user/avatar',
    method: 'post',
    data: formData,
    timeout: 60000,
    retry: 0
  })
  return normalize(res)
}
