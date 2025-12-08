// 用户认证状态管理
import { reactive, readonly } from 'vue'
import axios from 'axios'

// 初始状态
const state = reactive({
  user: JSON.parse(localStorage.getItem('user')) || null,
  isAuthenticated: !!localStorage.getItem('user')
})

// 获取状态
const getState = () => readonly(state)

// 登录
const login = async (username, password) => {
  try {
    const response = await axios.post('/api/auth/login', { username, password })

    if (response.data.success) {
      state.user = response.data.user
      state.isAuthenticated = true
      localStorage.setItem('user', JSON.stringify(response.data.user))
      return { success: true }
    } else {
      return { success: false, message: response.data.message }
    }
  } catch (error) {
    console.error('登录错误:', error)
    return {
      success: false,
      message: error.response?.data?.message || '登录失败，请稍后再试'
    }
  }
}

// 注册
const register = async (userData) => {
  try {
    const response = await axios.post('/api/auth/register', userData)

    if (response.data.success) {
      return { success: true, user: response.data.user }
    } else {
      return { success: false, message: response.data.message }
    }
  } catch (error) {
    console.error('注册错误:', error)
    return {
      success: false,
      message: error.response?.data?.message || '注册失败，请稍后再试'
    }
  }
}

// 登出
const logout = async () => {
  try {
    await axios.post('/api/auth/logout')
  } catch (error) {
    console.error('登出错误:', error)
  } finally {
    clearAuth()
  }
}

// 清除认证状态
const clearAuth = () => {
  state.user = null
  state.isAuthenticated = false
  localStorage.removeItem('user')
}

// 检查用户状态
const checkAuthStatus = async () => {
  if (!state.isAuthenticated) return

  try {
    const response = await axios.get('/api/auth/user')

    if (response.data.success) {
      state.user = response.data.user
    } else {
      logout()
    }
  } catch (error) {
    console.error('检查用户状态错误:', error)
    logout()
  }
}

export default {
  getState,
  login,
  register,
  logout,
  clearAuth,
  checkAuthStatus
}
