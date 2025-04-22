import { createRouter, createWebHistory } from 'vue-router';
// 定义前端路由规则，控制页面导航
// 将URL路径映射到对应的vue组件

// 路由规则
const routes = [
  {
    path: '/',
    redirect: '/auth/login' // 根路径直接跳登录页
  },
  {
    path: '/auth',   //路由前缀，本身不渲染组件
    children: [
      { path: 'login', name: 'Login', meta: {title:'登录'}, component: () => import('@/views/Login.vue')},
      { path: 'register', name: 'Register', meta: {title:'注册'}, component: () => import('@/views/Register.vue') }
    ]
  },
  {
  path: '/app',
    component: () => import('@/components/layout/Layout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        //不必加/
        path: 'dashboard',
        name: 'AppHome',
        meta: { title: '控制台', icon: 'el-icon-monitor' }, // 添加图标和标题
        component: () => import('@/views/DashBoard.vue')
      }
    ]
},
  {
    path: '/404',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue')
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404'
  }
];

// 创建路由器
const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 权限守卫（检查localStorage中的token）
router.beforeEach((to) => {
  //到底是access_token还是token
  const isAuthenticated = localStorage.getItem('access_token')
  if (to.meta.requiresAuth && !isAuthenticated) {
    return { name: 'Login', query: { redirect: to.fullPath }} // 拦截未登录访问
  }
  if (isAuthenticated && (to.name === 'Login' || to.name === 'Register')) {
    return { name: 'AppHome' }
  }
  //继续导航
  return true
})
export default router;