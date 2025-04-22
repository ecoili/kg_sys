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
  height: 100vh;
  width: 100%;
  display: flex;

  .sidebar-container {
    width: 210px;
    height: 100%;
    background: #001529;
    transition: width 0.28s;
  }

  .main-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;

    .header-container {
      height: 50px;
      background: white;
    }

    .main-content {
      flex: 1;
      overflow: auto;
      background: #f0f2f5;
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