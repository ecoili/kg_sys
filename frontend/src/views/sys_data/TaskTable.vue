<template>
  <div class="task-table-container">
    <h2>任务信息</h2>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading">加载中...</div>

    <!-- 错误提示 -->
    <div v-if="error" class="error">{{ error }}</div>

    <!-- 搜索和筛选功能 -->
    <div class="search-filter-container">
      <div class="search-box">
        <input
          v-model="searchId"
          type="text"
          placeholder="输入任务ID搜索"
          class="search-input"
        >
        <button @click="searchById" class="search-btn">搜索</button>
        <button @click="resetSearch" class="reset-btn">重置</button>
      </div>

      <div class="filter-box">
        <select v-model="selectedType" class="type-select">
          <option value="">所有类型</option>
          <option v-for="type in taskTypes" :key="type" :value="type">
            {{ type }}
          </option>
        </select>

        <select v-model="selectedStatus" class="status-select">
          <option value="">所有状态</option>
          <option value="已分配">已分配</option>
          <option value="待分配">待分配</option>
<!--          <option value="已完成">已完成</option>-->
        </select>
      </div>
    </div>
    <!-- 添加新任务按钮 -->
    <div class="action-buttons">
      <button @click="showAddModal = true" class="action-btn add-btn">添加新任务</button>
    </div>

    <!-- 添加任务模态框 -->
    <div v-if="showAddModal" class="modal-overlay">
      <div class="modal-content">
        <h3>添加新任务</h3>
        <div class="form-group">
          <label>任务类型:</label>
          <select v-model="newTask.type" class="form-input">
            <option v-for="type in taskTypes" :key="type" :value="type">{{ type }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>持续时间(分钟):</label>
          <input v-model.number="newTask.duration" type="number" min="1" class="form-input">
        </div>
        <div class="form-group">
          <label>优先级(1-5):</label>
          <input v-model.number="newTask.priority" type="number" min="1" max="5" class="form-input">
        </div>
        <div class="modal-actions">
          <button @click="addNewTask" class="confirm-btn">确认</button>
          <button @click="showAddModal = false" class="cancel-btn">取消</button>
        </div>
      </div>
    </div>

    <!-- 编辑任务模态框 -->
    <div v-if="showEditModal" class="modal-overlay">
      <div class="modal-content">
        <h3>编辑任务</h3>
        <div class="form-group">
          <label>持续时间(分钟):</label>
          <input v-model.number="editingTask.duration" type="number" min="1" class="form-input">
        </div>
        <div class="form-group">
          <label>优先级(1-5):</label>
          <input v-model.number="editingTask.priority" type="number" min="1" max="5" class="form-input">
        </div>
<!--        <div class="form-group">-->
<!--          <label>截止时间:</label>-->
<!--          <input-->
<!--            v-model="editingTask.deadline"-->
<!--            type="datetime-local"-->
<!--            class="form-input"-->
<!--            :min="getCurrentDateTime()"-->
<!--          >-->
<!--        </div>-->
<!--        <div class="form-group">-->
<!--          <label>状态:</label>-->
<!--          <select v-model="editingTask.status" class="form-input">-->
<!--            <option value="待分配">待分配</option>-->
<!--            <option value="已分配">已分配</option>-->
<!--            <option value="已完成">已完成</option>-->
<!--          </select>-->
<!--        </div>-->
        <div class="modal-actions">
          <button @click="updateTask" class="confirm-btn">确认</button>
          <button @click="showEditModal = false" class="cancel-btn">取消</button>
        </div>
      </div>
    </div>

    <!-- 分配阵位模态框 -->
    <div v-if="showAssignModal" class="modal-overlay">
      <div class="modal-content">
        <h3>为任务 {{ assigningTask.id }} 分配阵位</h3>
        <div class="form-group">
          <label>可选阵位:</label>
          <select v-model="selectedPosition" class="form-input">
            <option v-for="pos in suitablePositions"
                    :key="pos.id"
                    :value="pos.id"
                    :disabled="pos.allocated_tasknum >= pos.sup_num">
              {{ pos.name }} (已分配: {{ pos.allocated_tasknum }}/{{ pos.sup_num }})
            </option>
          </select>
        </div>
        <div class="modal-actions">
          <button @click="assignTask" class="confirm-btn">分配</button>
          <button @click="showAssignModal = false" class="cancel-btn">取消</button>
        </div>
      </div>
    </div>

    <!-- 数据展示 -->
    <div v-if="tasks.length > 0">
      <table class="task-table">
        <thead>
          <tr>
            <th>任务ID</th>
            <th>任务名称</th>
            <th>任务类型</th>
            <th>持续时间</th>
            <th>优先级</th>
            <th>状态</th>
            <th>分配阵位</th>
<!--            <th>截止时间</th>-->
            <th>操作</th>
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
            <td>阵位{{task.current_pos}}:{{ task.current_pos_name || '待分配' }}</td>
<!--            <td>{{ formatDeadline(task.deadline) }}</td>-->
            <td>
              <button @click="openEditModal(task)" class="action-btn edit-btn">编辑</button>
              <button @click="deleteTask(task.id)" class="action-btn delete-btn">删除</button>
              <button v-if="task.status === '待分配'"
                      @click="openAssignModal(task)"
                      class="action-btn assign-btn">
                分配阵位
              </button>
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

        <select v-model="itemsPerPage" @change="resetPage" class="page-size-select">
          <option value="5">每页5条</option>
          <option value="10">每页10条</option>
          <option value="20">每页20条</option>
          <option value="50">每页50条</option>
        </select>
      </div>
    </div>

    <div v-else class="no-data">暂无任务数据</div>
  </div>
</template>

<script>
import {deleteTask, fetchTasks, addTask, updateTask, assignTaskToPosition, fetchPositions} from '@/api/dashboard_fe.js'
import dayjs from 'dayjs'
import { ElMessage } from 'element-plus'

export default {
  name: 'TaskTableView',
  data() {
    return {
      searchId: '',
      selectedType: '',
      selectedStatus: '',
      taskTypes: ['加油', '供电', '送餐', '清洁', '起飞', '维修', '降落', '行李装卸', '测试'],
      tasks: [],
      loading: false,
      error: null,
      currentPage: 1,    // 当前页码
      itemsPerPage: 10,  // 每页显示条数
      inputPage: 1,       // 输入框中的页码

      showAddModal: false,
      showEditModal: false,
      showAssignModal: false,
      newTask: {
        type: '加油',
        duration: 5,
        priority: 3
      },
      editingTask: {},
      assigningTask: {},
      suitablePositions: [],
      selectedPosition: null,
      positions: [],
    }
  },
  watch: {
    // 当currentPage变化时同步更新inputPage
    currentPage(newVal) {
      this.inputPage = newVal
    }
  },
  computed: {
    filteredTasks() {
      let filtered = this.tasks

      // ID筛选
      if (this.searchId) {
        filtered = filtered.filter(t =>
          t.id.toLowerCase().includes(this.searchId.toLowerCase())
        )
      }

      // 类型筛选
      if (this.selectedType) {
        filtered = filtered.filter(t => t.type === this.selectedType)
      }

      // 状态筛选
      if (this.selectedStatus) {
        filtered = filtered.filter(t => t.status === this.selectedStatus)
      }

      return filtered.sort((a, b) => {
      // 提取ID中的数字部分进行比较
      const numA = parseInt(a.id.substring(1));
      const numB = parseInt(b.id.substring(1));
      return numA - numB;
    })
    },
    // 分页数据
    paginatedTasks() {
      const start = (this.currentPage - 1) * this.itemsPerPage
      const end = start + Number(this.itemsPerPage)
      return this.filteredTasks.slice(start, end)
    },
    // 总页数
    totalPages() {
      return Math.ceil(this.filteredTasks.length / this.itemsPerPage)
    }
  },
  async created() {
    await this.loadPositions(); // 确保加载positions
    await this.loadTasks()
    // 初始化inputPage
    this.inputPage = this.currentPage
  },
  methods: {
    // 加载任务数据
    async loadTasks() {
      this.loading = true
      this.error = null

      try {
        const response = await fetchTasks()
        this.tasks = response.data || response // 根据API响应结构调整
      } catch (err) {
        console.error('获取任务数据失败:', err)
        this.error = '获取任务数据失败，请稍后重试'
      } finally {
        this.loading = false
      }
    },
    // 格式化截止时间
    formatDeadline(isoString) {
      return dayjs(isoString).format('YYYY-MM-DD HH:mm:ss')
    },
    // ID搜索
    searchById() {
      this.currentPage = 1
    },
    // 重置搜索
    resetSearch() {
      this.searchId = ''
      this.selectedType = ''
      this.selectedStatus = ''
      this.currentPage = 1
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
    },
    async loadPositions() {
      try {
        this.positions = await fetchPositions()
        console.log('Loaded positions:', this.positions)
      } catch (error) {
        console.error('获取阵位数据失败:', error)
         ElMessage.error('获取阵位数据失败')
      }
    },

    async addNewTask() {
      try {
        const response = await addTask(this.newTask)
        this.showAddModal = false;
        this.newTask = { type: '加油', duration: 5, priority: 3 };
        await this.loadTasks()
        ElMessage.success(`添加成功，新任务ID: ${response.id}`)
      } catch (error) {
        console.error('添加任务失败:', error)
        ElMessage.error("添加任务失败")
      }
    },

    openEditModal(task) {
      this.editingTask = { ...task };
      // 将ISO格式的截止时间转换为datetime-local可接受的格式
      if (this.editingTask.deadline) {
        this.editingTask.deadline = dayjs(this.editingTask.deadline).format('YYYY-MM-DDTHH:mm');
      }
      this.showEditModal = true;
    },

    async updateTask() {
      try {
         // 转换日期格式为ISO字符串
        const deadline = new Date(this.editingTask.deadline).toISOString()
        await updateTask(this.editingTask.id, {
          duration: this.editingTask.duration,
          priority: this.editingTask.priority,
          status: this.editingTask.status,
          deadline: deadline  // 添加截止时间
        });
        this.showEditModal = false;
        await this.loadTasks();
        ElMessage.success("修改成功！")
      } catch (error) {
        console.error('更新任务失败:', error);
        ElMessage.error("更新任务失败！")
      }
    },

    async deleteTask(taskId) {
      try {
    await this.$confirm('确定要删除这个任务吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    });

    await deleteTask(taskId);
    await this.loadTasks();
    ElMessage.success('删除成功');
  } catch (error) {
    if (error !== 'cancel') { // 用户点击取消时不显示错误
      console.error('删除任务失败:', error);
      ElMessage.error('删除任务失败');
    }
  }
    },

    async openAssignModal(task) {
      this.assigningTask = { ...task };
       // 确保positions已加载
      if (this.positions.length === 0) {
        await this.loadPositions();
      }
      // 筛选符合任务要求的阵位
      this.suitablePositions = this.positions.filter(pos => {
    // 确保pos.type存在且是任务要求的类型之一
    return pos.type && this.assigningTask.required_position_types.includes(pos.type);
  })
      // 确保有可选阵位时才打开模态框
      if (this.suitablePositions.length > 0) {
        this.selectedPosition = null;
        this.showAssignModal = true;
      } else {
        ElMessage.warning('没有符合要求的可用阵位')
      }
    },

    async assignTask() {
      if (!this.selectedPosition) {
        // alert('请选择一个阵位');
        ElMessage.warning("请选择一个阵位")
        return;
      }

      try {
        await assignTaskToPosition(this.assigningTask.id, this.selectedPosition);
        this.showAssignModal = false;
        await this.loadTasks();
        ElMessage.success("任务分配成功！")
      } catch (error) {
        console.error('分配任务失败:', error);
        ElMessage.error(error.message || '分配任务失败')
      }
    },
     // 禁止选择过去的时间
    disabledDate(time) {
      return time.getTime() < Date.now() - 8.64e7 // 86400000 = 1天
    },
    getCurrentDateTime() {
      const now = new Date();
      // 转换为本地日期时间字符串格式
      return now.toISOString().slice(0, 16);
    }
  }
}
</script>

<style scoped>
.task-table-container {
  margin: 20px;
  overflow-x: auto;
}

.task-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
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

/* 分页控件样式 */
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

.search-input, .type-select, .status-select {
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

@media (max-width: 768px) {
  .pagination {
    flex-wrap: wrap;
    gap: 10px;
  }

  .search-filter-container {
    flex-direction: column;
    gap: 10px;
  }

  .search-box, .filter-box {
    width: 100%;
  }
}
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

.assign-btn {
  background-color: #FF9800;
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
  width: 400px;
  max-width: 90%;
}

.form-group {
  margin-bottom: 15px;
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

.form-input[type="datetime-local"] {
  /* 确保日期选择器有足够高度 */
  line-height: 1.5;
  padding: 8px;
}



</style>