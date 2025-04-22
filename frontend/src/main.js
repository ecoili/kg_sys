import { createApp } from 'vue'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'   //整体引入element-Plus
import '@/styles/layout.scss'
import router from './router'  // 确保router已配置，导入路由器
import { createPinia } from 'pinia'
import dayjs from 'dayjs' //不必加.js,否则会无法识别！！！会自动解析到esm
import customParseFormat from  'dayjs/plugin/customParseFormat'  //不加js后customParseFormat变紫了
/*import * as dayjs from 'dayjs'
import customParseFormat from 'dayjs/plugin/customParseFormat'*/



const app = createApp(App)
app.use(ElementPlus)
app.use(router)
app.use(createPinia())
dayjs.extend(customParseFormat)
app.mount('#app')
