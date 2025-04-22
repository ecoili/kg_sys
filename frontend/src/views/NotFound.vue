<template>
  <div class="not-found-container">
    <div class="content">
      <!-- 404图标 -->
      <div class="error-code">404</div>

      <!-- 提示文字 -->
      <h1 class="title">页面不存在</h1>
      <p class="description">
        您访问的页面可能已被删除、更名或暂时不可用
      </p>

      <!-- 返回首页按钮 -->
      <el-button
        type="primary"
        @click="goHome"
      >
        <i class="el-icon-house"></i> 返回首页
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goHome = () => {
  router.push({ name: 'AppHome' }) // 替换为你的首页路由名称
}
</script>

<style scoped>
.not-found-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f5f7fa;
  text-align: center;
}

.content {
  max-width: 500px;
  padding: 20px;
}

.error-code {
  font-size: 120px;
  font-weight: bold;
  color: #409eff; /* Element Plus 主色调 */
  line-height: 1;
  margin-bottom: 20px;
}

.title {
  font-size: 24px;
  margin-bottom: 16px;
  color: #303133;
}

.description {
  font-size: 16px;
  color: #606266;
  margin-bottom: 24px;
}
</style>