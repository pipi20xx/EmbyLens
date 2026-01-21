import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import { logout, uiAuthEnabled } from './store/navigationStore'
import './style.css'
import './styles/global.css'

// 配置 Axios 拦截器
axios.interceptors.request.use(config => {
  const token = localStorage.getItem('embylens_access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      // 仅在开启了登录验证的情况下才跳转登录页
      if (uiAuthEnabled.value && !window.location.pathname.includes('/login')) {
        logout()
        router.push('/login')
      }
    }
    return Promise.reject(error)
  }
)

const app = createApp(App)
app.use(router)
app.mount('#app')
