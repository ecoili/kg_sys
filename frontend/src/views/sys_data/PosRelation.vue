<template>
  <div class="relations-container">
    <h2>阵位间关系</h2>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">加载中...</div>

    <!-- 错误提示 -->
    <div v-if="error" class="error">{{ error }}</div>

    <!-- 数据展示 -->
    <div v-if="relations.length > 0">
      <table class="relations-table">
        <thead>
          <tr>
            <th>源阵位ID</th>
            <th>源阵位名称</th>
            <th>目标阵位ID</th>
            <th>目标阵位名称</th>
            <th>关系类型</th>
            <th>权重</th>
            <th>距离</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="relation in paginatedData" :key="`${relation.source_id}-${relation.target_id}`">
            <td>{{ relation.source_id }}</td>
            <td>{{ relation.source_name }}</td>
            <td>{{ relation.target_id }}</td>
            <td>{{ relation.target_name }}</td>
            <td>{{ relation.relation_type }}</td>
<!--            <td>{{ relation.weight }}</td>-->
            <td>{{ relation.strength }}</td>
            <td>{{ relation.distance }}</td>
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

    <div v-else class="no-data">暂无阵位关系数据</div>
  </div>
</template>

<script>
import { fetchPosRelations } from '@/api/dashboard_fe.js'

export default {
  name: 'PositionRelations',
  data() {
    return {
      relations: [],
      loading: false,
      error: null,
      currentPage: 1,
      pageSize: 10,
      inputPage: 1
    }
  },
  watch: {
    currentPage(newVal) {
      this.inputPage = newVal
    }
  },
  computed: {
    totalPages() {
      return Math.ceil(this.relations.length / this.pageSize)
    },
    paginatedData() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + Number(this.pageSize)
      return this.relations.slice(start, end)
    }
  },
  async created() {
    await this.loadRelations()
    this.inputPage = this.currentPage
  },
  methods: {
    async loadRelations() {
      this.loading = true
      this.error = null

      try {
        const response = await fetchPosRelations()
        this.relations = response.data || response
      } catch (err) {
        console.error('获取阵位关系数据失败:', err)
        this.error = '获取阵位关系数据失败，请稍后重试'
      } finally {
        this.loading = false
      }
    },
    prevPage() {
      if (this.currentPage > 1) {
        this.currentPage--
      }
    },
    nextPage() {
      if (this.currentPage < this.totalPages) {
        this.currentPage++
      }
    },
    goToPage() {
      let page = parseInt(this.inputPage)
      if (isNaN(page) || page < 1) {
        page = 1
      } else if (page > this.totalPages) {
        page = this.totalPages
      }
      this.currentPage = page
    },
    resetPage() {
      this.currentPage = 1
    }
  }
}
</script>

<style scoped>
.relations-container {
  padding: 20px;
}

.relations-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

.relations-table th, .relations-table td {
  border: 1px solid #ddd;
  padding: 8px;
  text-align: left;
}

.relations-table th {
  background-color: #f2f2f2;
}

.relations-table tr:nth-child(even) {
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
</style>