import router from "@/router";
import store from "@/store";


router.beforeEach((to, from, next) => {
  if (to.meta.noLayout) return next() // 放行登录页
  // 其他页面走完整版权限逻辑
  if (store.getters.token) {
    next()
  } else {
    next(`/auth/login?redirect=${to.path}`)
  }
})