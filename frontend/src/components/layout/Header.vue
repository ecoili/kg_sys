<template>
  <div class="header-container">
    <div class="left-menu">
      <i
        class="collapse-icon"
        :class="isCollapse ? 'el-icon-s-unfold' : 'el-icon-s-fold'"
        @click="toggleCollapse" />

      <el-breadcrumb separator="/">
        <el-breadcrumb-item
          v-for="item in breadcrumbs"
          :key="item.path"
          :to="item.path">
          {{ item.meta.title }}
        </el-breadcrumb-item>
      </el-breadcrumb>
    </div>

    <div class="right-menu">
      <el-dropdown trigger="click">
        <div class="avatar-wrapper">
          <img :src="avatar" class="user-avatar">
          <span class="username">{{ username }}</span>
          <i class="el-icon-caret-bottom" />
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item>个人中心</el-dropdown-item>
            <el-dropdown-item divided @click="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import avatar from '@/assets/avatar.png'

const router = useRouter()
const route = useRoute()
const username = ref('管理员')
const isCollapse = ref(false)

const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta && item.meta.title)
  return matched
})

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
  // 可以通过EventBus或provide/inject与Sidebar通信
}

const logout = () => {
  localStorage.removeItem('token')
  router.push('/login')
}
</script>

<style lang="scss" scoped>
.header-container {
  height: 50px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 15px;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);

  .left-menu {
    display: flex;
    align-items: center;

    .collapse-icon {
      font-size: 20px;
      margin-right: 20px;
      cursor: pointer;
    }
  }

  .right-menu {
    .avatar-wrapper {
      display: flex;
      align-items: center;
      cursor: pointer;

      .user-avatar {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        margin-right: 8px;
      }

      .username {
        margin-right: 5px;
      }
    }
  }
}
</style>