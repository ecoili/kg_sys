<!--是vue页面资源的首加载项，是主组件，页面入口文件，所有页面都是在APP.vue下进行切换的-->

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
