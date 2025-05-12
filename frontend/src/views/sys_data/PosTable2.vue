<template>
  <div class="positions-container">
    <h2>机场阵位信息</h2>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">加载中...</div>

    <!-- 错误提示 -->
    <div v-if="error" class="error">{{ error }}</div>

    <!-- 搜索和筛选功能 -->
    <div class="search-filter-container">
      <div class="search-box">
        <input
          v-model="searchId"
          type="number"
          placeholder="输入阵位ID搜索"
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

    <!-- 添加新阵位按钮 -->
    <div class="action-buttons">
      <button @click="showAddModal = true" class="action-btn add-btn">添加新阵位</button>
      <button @click="showAddRelationModal = true" class="action-btn relation-btn">添加关系</button>
    </div>

    <!-- 添加阵位模态框 -->
    <div v-if="showAddModal" class="modal-overlay">
      <div class="modal-content">
        <h3>添加新阵位</h3>
        <div class="form-group">
          <label>阵位类型:</label>
          <select v-model="newPosition.type" class="form-input">
            <option v-for="type in positionTypes" :key="type" :value="type">{{ type }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>X坐标:</label>
          <input
            v-model.number="newPosition.x"
            type="number"
            class="form-input"
            @blur="checkPosition(newPosition.x, newPosition.y)"
          >
        </div>
        <div class="form-group">
          <label>Y坐标:</label>
          <input
            v-model.number="newPosition.y"
            type="number"
            class="form-input"
            @blur="checkPosition(newPosition.x, newPosition.y)"
          >
        </div>
        <div class="form-group">
          <label>重要性(1-5):</label>
          <input v-model.number="newPosition.impt_lv" type="number" min="1" max="5" class="form-input">
        </div>
        <div class="form-group">
          <label>支持任务数(0-5):</label>
          <input v-model.number="newPosition.sup_num" type="number" min="0" max="5" class="form-input">
        </div>
        <div class="modal-actions">
          <button @click="addNewPosition" class="confirm-btn">确认</button>
          <button @click="showAddModal = false" class="cancel-btn">取消</button>
        </div>
      </div>
    </div>

    <!-- 编辑阵位模态框 -->
    <div v-if="showEditModal" class="modal-overlay">
      <div class="modal-content">
        <h3>编辑阵位</h3>
        <div class="form-group">
          <label>重要性(1-5):</label>
          <input v-model.number="editingPosition.impt_lv" type="number" min="1" max="5" class="form-input">
        </div>
        <div class="form-group">
          <label>支持任务数(0-5):</label>
          <input v-model.number="editingPosition.sup_num" type="number" min="0" max="5" class="form-input">
        </div>
        <div class="modal-actions">
          <button @click="updatePosition" class="confirm-btn">确认</button>
          <button @click="showEditModal = false" class="cancel-btn">取消</button>
        </div>
      </div>
    </div>

    <!-- 删除确认模态框 -->
    <div v-if="showDeleteModal" class="modal-overlay">
      <div class="modal-content">
        <h3>确认删除阵位 {{ deletingPosition.id }}:{{ deletingPosition.name }}?</h3>

        <div v-if="relatedTasks.length > 0" class="error-message">
          该阵位有{{ relatedTasks.length }}个关联任务，无法删除！
        </div>

        <div v-if="relatedPositions.length > 0 && relatedTasks.length === 0">
          <p>该阵位与其他阵位有以下关系:</p>
          <ul>
            <li v-for="rel in relatedPositions" :key="rel.id">
              {{ rel.source_name }} - {{ rel.relation_type }} - {{ rel.target_name }}
            </li>
          </ul>
          <p>删除后将同时删除这些关系</p>
        </div>

        <div v-if="relatedPositions.length === 0 && relatedTasks.length === 0">
          <p>该阵位没有关联关系，可以直接删除</p>
        </div>

        <div class="modal-actions">
          <button
            @click="confirmDeletePosition"
            class="confirm-btn"
            :disabled="relatedTasks.length > 0"
          >
            确认删除
          </button>
          <button @click="showDeleteModal = false" class="cancel-btn">取消</button>
        </div>
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
            <th>操作</th>
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
            <td>
              <button @click="openEditModal(position)" class="action-btn edit-btn">编辑</button>
              <button @click="openDeleteModal(position)" class="action-btn delete-btn">删除</button>
            </td>
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
import { fetchPositions, addPosition, updatePosition, deletePosition, getPositionRelations, getPositionTaskRelations, checkPosition } from '@/api/dashboard_fe.js'
import { ElMessage } from 'element-plus'

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
      currentPage: 1,
      pageSize: 10,
      inputPage: 1,

      showAddModal: false,
      showEditModal: false,
      showDeleteModal: false,
      newPosition: {
        type: '跑道',
        x: 0,
        y: 0,
        impt_lv: 1,
        sup_num: 1
      },
      editingPosition: {},
      deletingPosition: {},
      relatedPositions: [],
      relatedTasks: []
    }
  },
  watch: {
    currentPage(newVal) {
      this.inputPage = newVal
    }
  },
  computed: {
    filteredPositions() {
      let filtered = this.positions

      if (this.searchId) {
        filtered = filtered.filter(p => p.id === parseInt(this.searchId))
      }

      if (this.selectedType) {
        filtered = filtered.filter(p => p.type === this.selectedType)
      }

      return filtered.sort((a, b) => a.id - b.id)
    },
    paginatedData() {
      const start = (this.currentPage - 1) * this.pageSize
      const end = start + Number(this.pageSize)
      return this.filteredPositions.slice(start, end)
    },
    totalPages() {
      return Math.ceil(this.filteredPositions.length / this.pageSize)
    }
  },
  async created() {
    await this.loadPositions()
    this.inputPage = this.currentPage
  },
  methods: {
    async loadPositions() {
      this.loading = true
      this.error = null

      try {
        const response = await fetchPositions()
        this.positions = response.data || response
      } catch (err) {
        console.error('获取阵位数据失败:', err)
        this.error = '获取阵位数据失败，请稍后重试'
      } finally {
        this.loading = false
      }
    },
    searchById() {
      this.currentPage = 1
    },
    resetSearch() {
      this.searchId = ''
      this.selectedType = ''
      this.currentPage = 1
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
    },
    openEditModal(position) {
      this.editingPosition = { ...position }
      this.showEditModal = true
    },
    async updatePosition() {
      try {
        await updatePosition(this.editingPosition.id, {
          impt_lv: this.editingPosition.impt_lv,
          sup_num: this.editingPosition.sup_num
        })
        this.showEditModal = false
        await this.loadPositions()
        ElMessage.success('更新成功')
      } catch (error) {
        console.error('更新阵位失败:', error)
        ElMessage.error('更新阵位失败')
      }
    },
    async checkPosition(x, y) {
      try {
        const response = await checkPosition({ x, y });
        return response.exists;
      } catch (error) {
        console.error('检查位置失败:', error);
        return false;
      }
    },
    async addNewPosition() {
      // 检查位置是否重复
      const positionExists = await this.checkPosition(this.newPosition.x, this.newPosition.y);
      if (positionExists) {
        ElMessage.error('该位置已存在阵位，请选择其他位置');
        return;
      }
      try {
        const response = await addPosition(this.newPosition)
        this.showAddModal = false
        this.newPosition = {
          type: '跑道',
          x: 0,
          y: 0,
          impt_lv: 1,
          sup_num: 1
        }
        await this.loadPositions()
        ElMessage.success(`添加成功，新阵位ID: ${response.id}`)
      } catch (error) {
        console.error('添加阵位失败:', error)
        ElMessage.error('添加阵位失败')
      }
    },
    async openDeleteModal(position) {
      this.deletingPosition = { ...position }

      // 获取关联关系
      try {
        // 获取关联任务
        const tasksResponse = await getPositionTaskRelations(position.id)
        this.relatedTasks = tasksResponse.data || tasksResponse

        // 获取关联阵位
        const positionsResponse = await getPositionRelations(position.id)
        this.relatedPositions = positionsResponse.data || positionsResponse

        this.showDeleteModal = true
      } catch (error) {
        console.error('获取关联关系失败:', error)
        ElMessage.error('获取关联关系失败')
      }
    },
    async confirmDeletePosition() {
      try {
        if (this.relatedTasks.length > 0) {
          ElMessage.warning('该阵位有关联任务，无法删除')
          return
        }

        await deletePosition(this.deletingPosition.id)
        this.showDeleteModal = false
        await this.loadPositions()
        ElMessage.success('删除成功')
      } catch (error) {
        console.error('删除阵位失败:', error)
        ElMessage.error('删除阵位失败')
      }
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
/* 原有样式保持不变，新增以下样式 */

.action-buttons {
  margin-bottom: 20px;
}

.action-btn {
  padding: 8px 15px;
  margin-right: 10px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.add-btn {
  background-color: #4CAF50;
  color: white;
}

.edit-btn {
  background-color: #2196F3;
  color: white;
}

.delete-btn {
  background-color: #F44336;
  color: white;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  width: 500px;
  max-width: 90%;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

.form-input {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.confirm-btn {
  padding: 8px 15px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin-left: 10px;
}

.cancel-btn {
  padding: 8px 15px;
  background-color: #F44336;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.error-message {
  color: #F44336;
  font-weight: bold;
  margin-bottom: 15px;
}
</style>