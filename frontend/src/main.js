import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'  //element样式
import router from './router'  // 确保router已配置
import { createPinia } from 'pinia'
import '@/styles/index.scss' // 引入完整版样式--全局样式（副高element默认样式
import Layout from './layout' // 注册布局组件
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

const app = createApp(App)
app.use(ElementPlus)
app.use(router)
app.use(Layout)
app.use(createPinia())
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}
app.mount('#app')

