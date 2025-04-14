<!--
<template>
  <router-view></router-view>
</template>

<script setup>
// 无需额外逻辑，路由切换由vue-router处理
</script>

<style>
/* 全局样式重置（可选） */
body {
  margin: 0;
  font-family: Arial, sans-serif;
}
</style>
-->


<!-- src/App.vue -->
<template>
  <el-container>
    <el-aside width="200px">
      <!-- 侧边菜单 -->
    </el-aside>
    <el-container>
      <el-header>
        <!-- 顶部导航 -->
      </el-header>
      <el-main>
        <router-view/>
      </el-main>
    </el-container>
  </el-container>
</template>