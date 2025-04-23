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
        :base-path="resolvePath(basePath, item.path)" />
    </el-sub-menu>
  </template>
</template>

<script setup>
import { defineProps } from 'vue'

const resolvePath = (basePath, routePath) => {
  if (routePath.startsWith('/')) {
    return routePath
  }
  return `${basePath}/${routePath}`.replace(/\/+/g, '/')
}

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  basePath: {
    type: String,
    required: true,
    default: ''
  }
})

console.log('解析路径:', 'basePath:', props.basePath, 'routePath:', props.item.path, 'resolved:', resolvePath(props.basePath, props.item.path))
</script>