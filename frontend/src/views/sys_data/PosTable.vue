<template>
  <div class="position-table-container">
    <el-table
      :data="paginatedData"
      border
      v-loading="loading"
      stripe
      highlight-current-row
      style="width: auto">
      <el-table-column prop="position_id" label="ID" width="100" align="center" />
      <el-table-column prop="x_coord" label="X坐标" width="100" align="center" />
      <el-table-column prop="y_coord" label="Y坐标" width="100" align="center" />
      <el-table-column prop="position_type" label="类型代码" width="100" align="center" />
      <el-table-column prop="type_identifier" label="类型名称" width="120" align="center" />
      <el-table-column prop="importance_level" label="重要等级" width="100" align="center" />
      <el-table-column prop="failure_rate" label="故障率" width="100" align="center">
        <template #default="{row}">
          {{ (row.failure_rate * 100).toFixed(2) }}%
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :page-sizes="[25, 50, 75, 100]"
      :total="positions.length"
      layout="total, sizes, prev, pager, next, jumper"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import Papa from 'papaparse'

const positions = ref([])
const loading = ref(false)
const currentPage = ref(1)
const pageSize = ref(25)
const cachedPositions = ref(null)

const paginatedData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return positions.value.slice(start, end)
})

const loadPositionsData = async () => {
  if (cachedPositions.value) {
    positions.value = cachedPositions.value
    return
  }

  try {
    loading.value = true
    const response = await fetch(new URL('@/assets/positions.csv', import.meta.url).href)
    const csvData = await response.text()

    Papa.parse(csvData, {
      header: true,
      complete: (results) => {
        positions.value = results.data.map(item => ({
          ...item,
          position_id: parseInt(item.position_id),
          x_coord: parseFloat(item.x_coord),
          y_coord: parseFloat(item.y_coord),
          position_type: parseInt(item.position_type),
          importance_level: parseInt(item.importance_level),
          failure_rate: parseFloat(item.failure_rate)
        }))
        cachedPositions.value = positions.value
      }
    })
  } catch (error) {
    console.error('加载位置数据失败:', error)
  } finally {
    loading.value = false
  }
}

const handleSizeChange = (val) => {
  pageSize.value = val
}

const handleCurrentChange = (val) => {
  currentPage.value = val
}

onMounted(() => {
  loadPositionsData()
})
</script>

<style scoped>
.position-table-container {
  padding: 20px;
  margin: 0 auto;
  width: 100%;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

:deep(.el-table) {
  width: 100% !important;
}

.el-pagination {
  margin-top: 20px;
  justify-content: center;
}

:deep(.el-table__header) th {
  background-color: #f5f7fa;
  color: #333;
  font-weight: bold;
}

:deep(.el-table__body) td {
  padding: 12px 0;
}

:deep(.el-table__body tr:hover>td) {
  background-color: #f0f7ff !important;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background-color: #fafafa;
}

:deep(.el-table--border) {
  border-radius: 4px;
}

:deep(.el-table--border th) {
  border-right: 1px solid #ebeef5;
}

:deep(.el-table--border td) {
  border-right: 1px solid #ebeef5;
}
</style>