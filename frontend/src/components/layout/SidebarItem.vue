<template>
  <template v-if="!item.meta?.hidden">
    <el-menu-item
      v-if="!item.children"
      :index="resolvePath(basePath, item.path)">
      <i v-if="item.meta?.icon" :class="item.meta.icon" />
      <template #title>{{ item.meta?.title }}</template>
    </el-menu-item>

    <el-sub-menu v-else :index="resolvePath(basePath, item.path)">
      <template #title>
        <i v-if="item.meta?.icon" :class="item.meta.icon" />
        <span>{{ item.meta?.title }}</span>
      </template>
      <sidebar-item
        v-for="child in item.children"
        :key="child.path"
        :item="child"
        :base-path="resolvePath(basePath, child.path)" />
    </el-sub-menu>
  </template>
</template>

<script setup>
import { defineProps } from 'vue'
import path from 'path'

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  basePath: {
    type: String,
    default: ''
  }
})

const resolvePath = (basePath, routePath) => {
  // return path.resolve(basePath, routePath)
  return basePath + (basePath.endsWith('/') || routePath.startsWith('/') ? '' : '/') + routePath
}
</script>