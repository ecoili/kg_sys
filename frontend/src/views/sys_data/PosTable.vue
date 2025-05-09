<template>
  <div class="positions-container">
    <h2>机场阵位信息</h2>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">加载中...</div>

    <!-- 错误提示 -->
    <div v-if="error" class="error">{{ error }}</div>
<!--    新增搜索和筛选功能-->
    <div class="search-filter-container">
    <div class="search-box">
      <input
        v-model="searchId"
        type="number"
        placeholder="输入ID搜索"
        class="search-input"
      >
      <button @click="searchById" class="search-btn">搜索</button>
      <button @click="resetSearch" class="reset-btn">重置</button>
    </div>

    <div class="filter-box">
      <select v-model="selectedType" class="type-select">
        <option value="">所有类型</option>
        <option v-for="type in positionTypes" :key="type" :value="type">
          {{ type }}
        </option>
      </select>
    </div>
  </div>

    <!-- 数据展示 -->
    <div v-if="positions.length > 0">
      <table class="positions-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>名称</th>
            <th>类型</th>
            <th>坐标(X,Y)</th>
            <th>重要性</th>
            <th>支持任务数</th>
            <th>已分配任务数</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="position in paginatedData" :key="position.id">
            <td>{{ position.id }}</td>
            <td>{{ position.name }}</td>
            <td>{{ position.type }}</td>
            <td>({{ position.x }}, {{ position.y }})</td>
            <td>
            <span :class="`impt_lv-${position.impt_lv}`">
              {{ position.impt_lv }}
            </span>
          </td>
            <td>{{ position.sup_num }}</td>
            <td>{{ position.allocated_tasknum }}</td>
          </tr>
        </tbody>
      </table>

      <!-- 分页控件 -->
      <div class="pagination">
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

        <select v-model="pageSize" @change="resetPage" class="page-size-select">
          <option value="5">每页5条</option>
          <option value="10">每页10条</option>
          <option value="20">每页20条</option>
          <option value="50">每页50条</option>
        </select>
      </div>
    </div>

    <div v-else class="no-data">暂无阵位数据</div>
  </div>
</template>

<script>
import { fetchPositions } from '@/api/dashboard_fe.js' // 导入API方法

export default {
  name: 'PositionsView',
  data() {
    return {
      searchId: '',
      selectedType: '',
      positionTypes: ['跑道', '加油站', '供电站', '维修点', '测试点', '行李装卸点', '送餐点', '清洁点', '停靠点'],
      positions: [],
      loading: false,
      error: null,
      currentPage: 1,    // 当前页码
      pageSize: 10,      // 每页显示条数
      inputPage: 1       // 输入框中的页码
    }
  },
  watch: {
    // 当currentPage变化时同步更新inputPage
    currentPage(newVal) {
      this.inputPage = newVal
    }
  },
  computed: {
    filteredPositions() {
      let filtered = this.positions

      // ID筛选
      if (this.searchId) {
        filtered = filtered.filter(p => p.id === parseInt(this.searchId))
      }

      // 类型筛选
      if (this.selectedType) {
        filtered = filtered.filter(p => p.type === this.selectedType)
      }

      return filtered
    },
    // 修改原有paginatedData计算属性
    paginatedData() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + Number(this.pageSize)
      return this.filteredPositions.slice(start, end)
    },
    // 修改总页数计算
    totalPages() {
      return Math.ceil(this.filteredPositions.length / this.pageSize)
    }
  },
  async created() {
    await this.loadPositions()
    // 初始化inputPage
    this.inputPage = this.currentPage
  },
  methods: {
    searchById() {
      this.currentPage = 1
    },
    resetSearch() {
      this.searchId = ''
      this.selectedType = ''
      this.currentPage = 1
    },
    async loadPositions() {
      this.loading = true
      this.error = null

      try {
        const response = await fetchPositions()
        this.positions = response.data || response // 根据你的API响应结构调整
      } catch (err) {
        console.error('获取阵位数据失败:', err)
        this.error = '获取阵位数据失败，请稍后重试'
      } finally {
        this.loading = false
      }
    },
    // 上一页
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--
      }
    },
    // 下一页
    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++
      }
    },
    // 跳转到指定页
    goToPage() {
      let page = parseInt(this.inputPage)
      if (isNaN(page) || page < 1) {
        page = 1
      } else if (page > this.totalPages) {
        page = this.totalPages
      }
      this.currentPage = page
    },
    // 切换每页条数时重置到第一页
    resetPage() {
      this.currentPage = 1
    }
  }
}
</script>

<style scoped>
.positions-container {
  padding: 20px;
}

.positions-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

.positions-table th, .positions-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

.positions-table th {
  background-color: #f2f2f2;
}

.positions-table tr:nth-child(even) {
  background-color: #f9f9f9;
}

.loading, .error, .no-data {
  padding: 20px;
  text-align: center;
  color: #666;
}

.error {
  color: #f56c6c;
}

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
.search-filter-container {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
}

.search-box, .filter-box {
  display: flex;
  align-items: center;
  gap: 10px;
}

.search-input, .type-select {
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.search-btn, .reset-btn {
  padding: 8px 15px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.reset-btn {
  background-color: #f56c6c;
}
.impt_lv-1 {
  color: #4CAF50;
}
.impt_lv-2 {
  color: #FFC107;
}
.impt_lv-3 {
  color: #FF9800;
}
.impt_lv-4 {
  color: #F44336;
}
.impt_lv-5 {
  color: #9C27B0;
}
</style>