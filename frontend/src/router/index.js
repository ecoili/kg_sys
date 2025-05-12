import { createRouter, createWebHistory } from 'vue-router'
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
      },
      {
        path: 'kg',
        name: 'KnowledgeGraph',
        meta: { title: '知识图谱', icon: 'el-icon-s-promotion' },
        component: () => import('@/views/KnlGraph3.vue')
      },
      {
        path: 'data',
        name: 'AllData',
        meta: { title: '系统数据', icon: 'el-icon-warning' },
        redirect: '/app/emergency/report',
        children: [
          {
            path: 'posinfo',
            name: 'PositionTable',
            meta: { title: '阵位信息管理' },
            component: () => import('@/views/sys_data/PosTable.vue')
          },
          {
            path: 'taskinfo',
            name: 'TaskTable',
            meta: { title: '任务信息管理' },
            component: () => import('@/views/sys_data/TaskTable.vue')
          },
          {
          path: 'pos2rel',
          name: 'Pos2Rel',
          meta: { title: '阵位间关系' },
          component: () => import('@/views/sys_data/PosRelation.vue')
          },
          {
          path: 'postaskrel',
          name: 'PosTaskRel',
          meta: { title: '阵位与任务间关系' },
          component: () => import('@/views/sys_data/PosTaskRel.vue')
          }
        ]
      },
      {
        path: 'emergency',
        name: 'Emergency',
        meta: { title: '特情处置', icon: 'el-icon-warning' },
        redirect: '/app/emergency/simulsingpage',
        children: [
          {
            path: 'simulsingpage',
            name: 'Simulation',
            meta: { title: '特情模拟-单阵位', icon: 'el-icon-s-promotion' },
            component: () => import('@/views/emergency/SimulEmerg.vue')
          },
          {
            path: 'simulmultipage',
            name: 'SimulationMulti',
            meta: { title: '特情模拟-多阵位', icon: 'el-icon-s-promotion' },
            component: () => import('@/views/emergency/SimulEmergMul.vue')
          }
        ]
      },
    ]
},
    {
    path: '/userInfo',
    name: 'UserCenter',
    component: () => import('@/views/UserInfo1.vue')
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
]

// 创建路由器
const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 权限守卫（检查localStorage中的token）
router.beforeEach((to) => {
  // console.log('尝试访问的路由:', to.path)
  // const isAuthenticated = localStorage.getItem('access_token')
  // if (to.meta.requiresAuth && !isAuthenticated) {
  //   return { name: 'Login', query: { redirect: to.fullPath }} // 拦截未登录访问
  // }
  // if (isAuthenticated && (to.name === 'Login' || to.name === 'Register')) {
  //   return { name: 'AppHome' }
  // }
  // //继续导航
  // return true
  console.log('导航到:', to.path) // 调试用
  console.log('匹配的路由记录:', to.matched)

  const isAuthenticated = localStorage.getItem('access_token')

  // 明确处理404路由
  if (to.name === 'NotFound') {
    return true // 允许访问404页面
  }

  if (to.meta.requiresAuth && !isAuthenticated) {
    console.log('未授权访问，重定向到登录')
    return {
      name: 'Login',
      query: { redirect: to.fullPath }
    }
  }

  if (isAuthenticated && (to.name === 'Login' || to.name === 'Register')) {
    console.log('已登录用户尝试访问登录页，重定向到首页')
    return { name: 'AppHome' }
  }

  // 检查路由是否存在
  if (!to.matched.length) {
    console.log('路由未匹配，重定向到404')
    return '/404'
  }

  return true
})
export default router;