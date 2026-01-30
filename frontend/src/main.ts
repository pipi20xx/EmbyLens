import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import { logout, uiAuthEnabled } from './store/navigationStore'
import './style.css'
import './styles/global.css'

axios.defaults.timeout = 20000 // 20秒超时

// 配置 Axios 拦截器
axios.interceptors.request.use(config => {
  const token = localStorage.getItem('lens_access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

axios.interceptors.response.use(
  response => response,
  error => {
    if (error.response && error.response.status === 401) {
      if (uiAuthEnabled.value && !window.location.pathname.includes('/login')) {
        logout()
        router.push('/login')
      }
    }
    return Promise.reject(error)
  }
)

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.mount('#app')