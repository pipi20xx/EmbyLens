import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { createDiscreteApi } from 'naive-ui'

// 使用 Naive UI 的脱离上下文 API 来在非组件文件中显示消息
const { message } = createDiscreteApi(['message'])

const service: AxiosInstance = axios.create({
  baseURL: '/',
  timeout: 60000 // 1分钟超时
})

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    // 这里可以从 localStorage 或 store 获取 token
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers['Authorization'] = `Bearer ${token}`
    // }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response: AxiosResponse) => {
    // 这里的 response.data 直接就是后端返回的内容
    return response.data
  },
  (error) => {
    const { response } = error
    if (response) {
      const status = response.status
      const detail = response.data?.detail || response.data?.message || '服务器内部错误'

      switch (status) {
        case 401:
          // 未登录或 Token 过期，可以在这里跳转登录页
          // window.location.href = '/login'
          break
        case 403:
          message.error('权限不足，拒绝访问')
          break
        case 404:
          message.error('请求资源不存在')
          break
        case 500:
          message.error('后端服务异常: ' + detail)
          break
        default:
          message.error(detail)
      }
    } else {
      message.error('网络连接超时或异常，请检查后端服务是否启动')
    }
    return Promise.reject(error)
  }
)

export default service
