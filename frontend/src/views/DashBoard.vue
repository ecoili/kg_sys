<template>
  <div class="dashboard-container">
    <h1>欢迎来到控制台</h1>

    <!-- 这里添加你的仪表板内容 -->
    <div class="grid-content">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-card shadow="hover">
            <div class="card-content">
              <div class="card-title">飞机总数</div>
              <div class="card-value">10</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover">
            <div class="card-content">
              <div class="card-title">阵位数</div>
              <div class="card-value">16</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover">
            <div class="card-content">
              <div class="card-title">任务总数</div>
              <div class="card-value">10</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 可以添加更多仪表板组件 -->
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// 可以在这里添加初始化逻辑
onMounted(() => {
  // 获取仪表板数据
  fetchDashboardData()
})

const fetchDashboardData = async () => {
  try {
    // 调用API获取数据
    // const response = await getDashboardData()
    // 处理数据...
  } catch (error) {
    console.error('获取仪表板数据失败:', error)
  }
}
</script>

<style scoped lang="scss">
.dashboard-container {
  padding: 20px;

  .grid-content {
    margin-top: 20px;
  }

  .card-content {
    text-align: center;

    .card-title {
      font-size: 14px;
      color: #909399;
      margin-bottom: 10px;
    }

    .card-value {
      font-size: 24px;
      font-weight: bold;
      color: #303133;
    }
  }
}
</style>