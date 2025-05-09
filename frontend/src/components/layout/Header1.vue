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
<!--            <el-dropdown-item>个人中心</el-dropdown-item>-->
            <el-dropdown-item @click="personalCenter">个人中心</el-dropdown-item>
            <el-dropdown-item divided @click="logout">退出登录</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>

<script setup>
import {computed, onMounted, ref} from 'vue'
import {useRoute, useRouter} from 'vue-router'
import avatar from '@/assets/default.png'
import {ElMessage} from "element-plus";

const router = useRouter()
const route = useRoute()
const username = ref('')
const isCollapse = ref(false)

onMounted(() => {
  username.value = localStorage.getItem('username') || '未登录用户'
})

const breadcrumbs = computed(() => {
  return route.matched.filter(item => item.meta && item.meta.title)
})

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
  // 可以通过EventBus或provide/inject与Sidebar通信
}

const logout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('username')
  ElMessage.success('您已成功退出登录')
  router.push('/auth/login')
}
const personalCenter = () => {
  router.push('/userInfo')
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