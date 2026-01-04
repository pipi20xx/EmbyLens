import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './style.css'

const app = createApp(App)

app.use(createPinia())
// 不再使用 router，完全采用 Anime-Manager 的动态组件模式
app.mount('#app')