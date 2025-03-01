import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建axios实例
const service = axios.create({
  baseURL: 'http://localhost:5000', // API基础URL
  timeout: 15000, // 请求超时时间
  withCredentials: true,  // 允许跨域请求携带凭证
  headers: {
    'Content-Type': 'application/json',
    'X-Requested-With': 'XMLHttpRequest'
  }
})

// request拦截器
service.interceptors.request.use(
  config => {
    // 如果是文件上传，删除Content-Type，让浏览器自动设置
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    return config
  },
  error => {
    console.error('Request error:', error)
    return Promise.reject(error)
  }
)

// response拦截器
service.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    console.error('Response error:', error)
    if (error.response) {
      // 如果有响应数据，使用响应中的错误信息
      ElMessage({
        message: error.response.data?.error || error.message,
        type: 'error',
        duration: 5 * 1000
      })
    } else {
      // 如果是网络错误，显示更友好的错误信息
      ElMessage({
        message: '网络连接失败，请检查网络设置或稍后重试',
        type: 'error',
        duration: 5 * 1000
      })
    }
    return Promise.reject(error)
  }
)

export default service
