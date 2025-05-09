<script setup>
import { ref, onMounted, computed } from 'vue'
import { fetchTasks } from '@/api/dashboard_fe.js'
import dayjs from 'dayjs'

const tasks = ref([])
const loading = ref(false)
const error = ref(null)
const currentPage = ref(1)
const itemsPerPage = ref(10)
const inputPage = ref(1) // 新增输入页码

// 获取任务数据
const loadTasks = async () => {
  try {
    loading.value = true
    const response = await fetchTasks()
    tasks.value = response
  } catch (err) {
    error.value = err.message || '加载任务数据失败'
    console.error('加载任务数据失败:', err)
  } finally {
    loading.value = false
  }
}

// 计算当前页的任务
const paginatedTasks = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return tasks.value.slice(start, end)
})

// 计算总页数
const totalPages = computed(() => {
  return Math.ceil(tasks.value.length / itemsPerPage.value)
})

// 格式化截止时间
const formatDeadline = (isoString) => {
  return dayjs(isoString).format('YYYY-MM-DD HH:mm:ss')
}

// 上一页
const prevPage = () => {
  if (currentPage.value > 1) {
    currentPage.value--
    inputPage.value = currentPage.value
  }
}

// 下一页
const nextPage = () => {
  if (currentPage.value < totalPages.value) {
    currentPage.value++
    inputPage.value = currentPage.value
  }
}

// 跳转到指定页
const goToPage = () => {
  let page = parseInt(inputPage.value)
  if (isNaN(page) || page < 1) {
    page = 1
  } else if (page > totalPages.value) {
    page = totalPages.value
  }
  currentPage.value = page
  inputPage.value = page
}

// 切换每页条数时重置到第一页
const resetPage = () => {
  currentPage.value = 1
  inputPage.value = 1
}

// 组件挂载时加载数据
onMounted(() => {
  loadTasks()
})
</script>

<template>
  <div class="task-table-container">
    <h2>任务信息</h2>
    <div v-if="loading" class="loading">加载中...</div>
    <div v-if="error" class="error">{{ error }}</div>

    <table v-if="tasks.length > 0" class="task-table">
      <thead>
        <tr>
          <th>任务ID</th>
          <th>任务名称</th>
          <th>任务类型</th>
          <th>持续时间</th>
          <th>优先级</th>
          <th>状态</th>
          <th>分配阵位</th>
          <th>截止时间</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="task in paginatedTasks" :key="task.id">
          <td>{{ task.id }}</td>
          <td>{{ task.name }}</td>
          <td>{{ task.type }}</td>
          <td>{{ task.duration }} 分钟</td>
          <td>
            <span :class="`priority-${task.priority}`">
              {{ task.priority }}
            </span>
          </td>
          <td>
            <span :class="`status-${task.status}`">
              {{ task.status }}
            </span>
          </td>
          <td>阵位{{task.current_pos}}:{{ task.current_pos_name || '未分配' }}</td>
          <td>{{ formatDeadline(task.deadline) }}</td>
        </tr>
      </tbody>
    </table>

    <!-- 修改后的分页控件 -->
    <div v-if="tasks.length > 0" class="pagination">
      <button
        @click="prevPage"
        :disabled="currentPage === 1"
        class="page-btn"
      >
        上一页
      </button>

      <span class="page-info">
        第
        <input
          v-model.number="inputPage"
          @keyup.enter="goToPage"
          type="number"
          min="1"
          :max="totalPages"
          class="page-input"
        >
        页 / 共 {{ totalPages }} 页
      </span>

      <button
        @click="nextPage"
        :disabled="currentPage === totalPages"
        class="page-btn"
      >
        下一页
      </button>

      <select
        v-model="itemsPerPage"
        @change="resetPage"
        class="page-size-select"
      >
        <option value="5">每页5条</option>
        <option value="10">每页10条</option>
        <option value="20">每页20条</option>
        <option value="50">每页50条</option>
      </select>
    </div>

    <div v-if="!loading && tasks.length === 0" class="no-data">
      暂无任务数据
    </div>
  </div>
</template>

<style scoped>
.task-table-container {
  margin: 20px;
  overflow-x: auto;
}

.task-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}

.task-table th, .task-table td {
  border: 1px solid #ddd;
  padding: 8px 12px;
  text-align: left;
}

.task-table th {
  background-color: #f2f2f2;
  font-weight: bold;
}

.task-table tr:nth-child(even) {
  background-color: #f9f9f9;
}

.task-table tr:hover {
  background-color: #f1f1f1;
}

/* 状态样式 */
.status-已分配 {
  color: #4CAF50;
  font-weight: bold;
}
.status-待分配 {
  color: #FF9800;
  font-weight: bold;
}
.status-已完成 {
  color: #2196F3;
  font-weight: bold;
}

/* 优先级样式 */
.priority-1 {
  color: #4CAF50;
}
.priority-2 {
  color: #FFC107;
}
.priority-3 {
  color: #FF9800;
}
.priority-4 {
  color: #F44336;
}
.priority-5 {
  color: #9C27B0;
}

.loading, .no-data, .error {
  padding: 20px;
  text-align: center;
  color: #666;
}

.error {
  color: #F44336;
}

/* 修改后的分页控件样式 - 与文档1一致 */
.pagination {
  margin-top: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
}

.page-btn {
  padding: 5px 10px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.page-btn:disabled {
  background-color: #c0c4cc;
  cursor: not-allowed;
}

.page-info {
  color: #606266;
  display: flex;
  align-items: center;
  gap: 5px;
}

.page-input {
  width: 50px;
  padding: 5px;
  text-align: center;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
}

.page-input:focus {
  outline: none;
  border-color: #409eff;
}

.page-size-select {
  padding: 5px;
  border-radius: 4px;
  border: 1px solid #dcdfe6;
}

@media (max-width: 768px) {
  .pagination {
    flex-wrap: wrap;
    gap: 10px;
  }
}
</style>