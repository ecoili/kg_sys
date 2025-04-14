import { createRouter, createWebHistory } from 'vue-router';
import Login from '@/views/Login.vue';
import Register from '@/views/Register.vue';
import Layout from '@/layout';
// 定义前端路由规则，控制页面导航
// 将URL路径映射到对应的vue组件

// 路由规则
const routes = [
  { path: '/', redirect: '/auth/login'},
  { path: '/auth/login', name: 'Login', component: Login, meta: { hidden: true, noLayout: true }},
  { path: '/auth/register', name: 'Register', component: Register, meta: { hidden: true, noLayout: true }},
  { path: '/dashboard', component: Layout}
];

// 创建路由器
const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;