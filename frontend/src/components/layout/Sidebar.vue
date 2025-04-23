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
           :base-path="basePath" />
<!--           :base-path="route.path" />-->
        <!--           :base-path="basePath + '/' + route.path" />-->
      </el-menu>
    </el-scrollbar>

    <div class="collapse-btn" @click="toggleCollapse">
      <i :class="isCollapse ? 'el-icon-s-unfold' : 'el-icon-s-fold'" />
    </div>
<!--    新增-->
    <div class="sidebar-container" :class="{'emergency-mode': emergencyStatus}">
    <!-- 原有代码... -->
    <div class="system-status">
      <el-alert
        v-if="emergencyStatus"
        title="特情处置中"
        type="error"
        :closable="false" />
    </div>
  </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import logo from '@/assets/myLogo.png'
import SidebarItem from './SidebarItem.vue'

const router = useRouter()
const route = useRoute()
const isCollapse = ref(false)
const emergencyStatus = ref(false) // 添加特情状态
const basePath = '/app'
// defineExpose({ basePath })
// 动态路由
const routes = computed(() => {
  const appRoute = router.options.routes.find(r => r.path === '/app')
  // return appRoute?.children?.filter(r => !r.meta?.hidden) || []
  return appRoute?.children || []
  // return appRoute?.children?.map(route => ({
  //   ...route,
  //   path: `/app/${route.path}` // 确保路径包含父路径
  // })) || []
})

// 选择静态路由
// 直接定义静态路由菜单
// const routes = ref([
//   {
//     path: '/kg',
//     meta: { title: '知识图谱', icon: 'el-icon-s-promotion' },
//     // children: [
//     //   {
//     //     path: 'schedule',
//     //     meta: { title: '' }
//     //   },
//     //   {
//     //     path: 'status',
//     //     meta: { title: '航班状态' }
//     //   }
//     // ]
//   },
//   {
//     path: '/emergency',
//     meta: { title: '特情处置', icon: 'el-icon-warning' },
//     children: [
//       {
//         path: 'report',
//         meta: { title: '特情报备' }
//       },
//       {
//         path: 'process',
//         meta: { title: '处置流程' }
//       }
//     ]
//   },
//   {
//     path: '/system',
//     meta: { title: '系统设置', icon: 'el-icon-setting' },
//     children: [
//       {
//         path: 'users',
//         meta: { title: '用户管理' }
//       },
//       {
//         path: 'roles',
//         meta: { title: '角色权限' }
//       }
//     ]
//   }
// ])

const activeMenu = computed(() => route.path)


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