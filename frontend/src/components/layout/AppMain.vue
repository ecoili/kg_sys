<!--页面过渡效果-->

<template>
  <div class="app-main">
    <router-view v-slot="{ Component }">
      <transition name="fade-transform" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script setup>
import { watch } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

watch(() => route.path, () => {
  // 可以在这里添加页面切换时的逻辑
})
</script>

<style lang="scss" scoped>
.app-main {
  min-height: calc(100vh - 50px);
  padding: 20px;
  background-color: #f0f2f5;
}

.fade-transform-leave-active,
.fade-transform-enter-active {
  transition: all 0.3s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>