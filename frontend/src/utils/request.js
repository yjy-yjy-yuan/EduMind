import axios from 'axios'
import { ElMessage } from 'element-plus'
import { API_BASE_URL } from '../config'

// 使用从配置文件导入的API基础URL
const baseURL = API_BASE_URL // 使用相对路径，让代理正常工作

// 创建axios实例
const service = axios.create({
  baseURL,
  timeout: 600000, // 增加超时时间到5分钟，确保长视频字幕处理能够完成
  withCredentials: false // 修改为false，避免发送cookies导致CORS预检请求
})

// 请求拦截器
service.interceptors.request.use(
  config => {
    // 如果是文件上传，删除Content-Type，让浏览器自动设置
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }

    // 如果请求需要blob响应，设置responseType
    if (config.responseType === 'blob') {
      config.headers.Accept = '*/*'
    }

    // 在请求头中添加token等认证信息
    return config
  },
  error => {
    console.error('请求错误:', error)
    ElMessage.error('请求发送失败，请重试')
    return Promise.reject(error)
  }
)

// response拦截器
service.interceptors.response.use(
  response => {
    // 如果是blob响应，直接返回
    if (response.config.responseType === 'blob') {
      return response
    }

    // 构造标准响应格式
    return {
      data: response.data,
      status: response.status,
      headers: response.headers
    }
  },
  error => {
    console.error('响应错误:', error)

    // 处理取消请求的情况
    if (axios.isCancel(error)) {
      console.log('请求已取消')
      return Promise.reject(error)
    }

    // 处理网络错误
    if (!error.response) {
      ElMessage.error('网络连接失败，请检查网络设置或稍后重试')
      return Promise.reject(error)
    }

    // 处理HTTP错误
    const status = error.response.status
    const errorMsg = error.response.data?.error || error.message

    switch (status) {
      case 400:
        ElMessage.error(errorMsg || '请求参数错误')
        break
      case 401:
        ElMessage.error('未授权，请重新登录')
        break
      case 403:
        ElMessage.error('拒绝访问')
        break
      case 404:
        ElMessage.error('请求的资源不存在')
        break
      case 500:
        ElMessage.error('服务器错误，请稍后重试')
        break
      default:
        ElMessage.error(errorMsg || '未知错误')
    }

    return Promise.reject(error)
  }
)

export default service
