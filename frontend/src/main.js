import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import App from './App.vue'
import router from './router'
import store from './store'

const app = createApp(App)

// 使用 Element Plus
app.use(ElementPlus, {
  locale: zhCn,
})

// 使用路由
app.use(router)

// 使用状态管理
app.use(store)

// 挂载应用
app.mount('#app')
