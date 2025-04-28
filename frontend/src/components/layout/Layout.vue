<template>
  <div class="app-wrapper" :class="{hideSidebar: isCollapse}">
    <sidebar class="sidebar-container" />
    <div class="main-container">
      <Header class="header-container" />
<!--       <tags-view v-if="showTagsView" />-->
      <app-main class="main-content" />
    </div>
  </div>
</template>

<script setup>
import { ref, provide } from 'vue'
import Sidebar from './Sidebar.vue'
import Header from './Header.vue'
import AppMain from './AppMain.vue'
// import TagsView from './TagsView.vue'

const isCollapse = ref(false)
const showTagsView = ref(true)
const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

// 提供给子组件访问
provide('isCollapse', isCollapse)
provide('toggleCollapse', toggleCollapse)
</script>

<style lang="scss" scoped>
.app-wrapper {
  position: relative;
  height: 100vh;  // 改为 min-height: 100vh;
  width: 100%;
  display: flex;
  flex-direction: column; // 新增

  .sidebar-container {
    width: 210px;
    height: 100vh; // 确保侧边栏高度固定
    position: fixed; // 新增
    left: 0;
    top: 0;
    bottom: 0;
    background: #001529;
    transition: width 0.28s;
    z-index: 1001; // 确保在内容之上
  }

  .main-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    margin-left: 210px; // 与侧边栏宽度一致
    transition: margin-left 0.28s;
    min-height: 100vh; // 新增

    .header-container {
      height: 50px;
      background: white;
      position: sticky; // 新增
      top: 0;
      z-index: 1000;
    }

    .main-content {
      flex: 1;
      overflow: auto;
      background: #f0f2f5;
      padding: 20px;
    }
  }
}

.hideSidebar {
  .sidebar-container {
    width: 64px !important;
  }

  .main-container {
    margin-left: 64px;
  }
}
</style>