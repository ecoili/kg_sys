<template>
  <div class="sidebar-container">
    <div class="logo-container">
      <img :src="logo" class="sidebar-logo" alt="logo">
      <h1 class="title">机场特情处置系统</h1>
    </div>

    <el-scrollbar wrap-class="scrollbar-wrapper">
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        background-color="#001529"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
        unique-opened
        router>
        <sidebar-item
          v-for="route in routes"
          :key="route.path"
          :item="route"
          :base-path="route.path" />
      </el-menu>
    </el-scrollbar>

    <div class="collapse-btn" @click="toggleCollapse">
      <i :class="isCollapse ? 'el-icon-s-unfold' : 'el-icon-s-fold'" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import logo from '@/assets/logo.png'
import SidebarItem from './SidebarItem.vue'

const router = useRouter()
const isCollapse = ref(false)

/*const routes = computed(() => {
  return router.options.routes
    .find(r => r.path === '/').children
    .filter(r => !r.meta?.hidden)
})*/
const routes = computed(() => {
  const appRoute = router.options.routes.find(r => r.path === '/app')
  return appRoute?.children?.filter(r => !r.meta?.hidden) || []
})

const activeMenu = computed(() => {
  const route = useRoute()
  return route.path
})

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}
</script>

<style lang="scss" scoped>
.sidebar-container {
  position: relative;
  width: 100%;
  height: 100%;
  background: #001529;

  .logo-container {
    height: 50px;
    line-height: 50px;
    padding: 0 10px;
    overflow: hidden;
    display: flex;
    align-items: center;

    .sidebar-logo {
      width: 32px;
      height: 32px;
      margin-right: 12px;
    }

    .title {
      color: white;
      font-size: 16px;
      white-space: nowrap;
    }
  }

  .scrollbar-wrapper {
    height: calc(100% - 50px);

    :deep(.el-menu) {
      border-right: none;
    }
  }

  .collapse-btn {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 40px;
    line-height: 40px;
    text-align: center;
    color: #bfcbd9;
    cursor: pointer;
    background: #001529;
    transition: background .3s;

    &:hover {
      background: #002140;
    }

    i {
      font-size: 18px;
    }
  }
}
</style>