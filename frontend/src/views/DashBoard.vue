<template>
  <div class="dashboard-container">

    <!-- 这里添加你的仪表板内容 -->
    <div class="grid-content">
      <el-row :gutter="20">
        <el-col :span="8">
          <el-card shadow="hover">
            <div class="card-content">
              <div class="card-title">阵位数</div>
              <div class="card-value">76</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover">
            <div class="card-content">
              <div class="card-title">任务总数</div>
              <div class="card-value">100</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover">
            <div class="card-content">
              <div class="card-title">关系总数</div>
              <div class="card-value">201</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 可以添加更多仪表板组件 -->
<!--    <div ref="chart" class="echarts-container"></div>-->
    <!-- 新增阵位地图可视化 -->
    <div class="map-container">
      <h3>机场阵位分布图</h3>
      <div ref="positionMap" class="echarts-container" style="height: 500px;"></div>
    </div>

    <!-- 新增任务状态可视化 -->
    <div class="task-container">
      <h3>任务状态概览</h3>
      <div ref="taskChart" class="echarts-container" style="height: 400px;"></div>
    </div>
  </div>
</template>

<script setup>
import {onMounted, ref, watch} from 'vue'
import { useRouter } from 'vue-router'
import {fetchPositions, fetchTasks} from '@/api/dashboard_fe.js'
import * as echarts from 'echarts'
const positionMap = ref(null)
const taskChart = ref(null)
const router = useRouter()

const positions = ref([])
const tasks = ref([])
const relations = ref([])

// 可以在这里添加初始化逻辑
onMounted(async() => {
  // 获取仪表板数据
  try {
    positions.value = await fetchPositions()
    tasks.value = await fetchTasks()
    initPositionMap()
    initTaskChart()
  } catch (error) {
    console.error('初始化数据失败:', error)
  }
})
// 初始化阵位地图
const initPositionMap = () => {
  const chart = echarts.init(positionMap.value)

  // 按类型分类阵位
  const categories = [...new Set(positions.value.map(p => p.type))]

  const option = {
    title: {
      text: '机场阵位分布',
      left: 'center'
    },
    tooltip: {
      formatter: params => {
        const pos = positions.value.find(p => p.id === params.id)
        return `
          <div><b>${pos.name}</b></div>
          <div>类型: ${pos.type}</div>
          <div>坐标: (${pos.x}, ${pos.y})</div>
          <div>重要性: ${pos.impt_lv}</div>
          <div>故障率: ${pos.flr_rate}</div>
          <div>支持数: ${pos.sup_num}</div>
        `
      }
    },
    legend: {
      data: categories,
      right: 10,
      top: 20
    },
    xAxis: {
      name: 'X坐标',
      nameLocation: 'middle',
      nameGap: 30
    },
    yAxis: {
      name: 'Y坐标',
      nameLocation: 'middle',
      nameGap: 30
    },
    series: categories.map(type => ({
      name: type,
      type: 'scatter',
      symbolSize: 12,
      data: positions.value
        .filter(p => p.type === type)
        .map(p => ({
          name: p.name,
          value: [p.x, p.y],
          id: p.id,
          type: p.type,
          itemStyle: {
            color: getColorByType(p.type)
          }
        })),
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      }
    }))
  }

  chart.setOption(option)
}

// 初始化任务图表
const initTaskChart = () => {
  const chart = echarts.init(taskChart.value)

  // 确保 tasks.value 已加载且不为空
  if (!tasks.value || tasks.value.length === 0) {
    console.warn('No task data available')
    return
  }

  // 按类型统计任务数
  const taskTypes = [...new Set(tasks.value.map(t => t.type))]
  const taskCountByType = taskTypes.map(type => ({
    name: type,
    value: tasks.value.filter(t => t.type === type).length
  }))

  // 按优先级统计
  const priorities = [1, 2, 3, 4, 5]
  const taskCountByPriority = priorities.map(p => ({
    name: `优先级 ${p}`,
    value: tasks.value.filter(t => t.priority === p).length
  }))

  const option = {
    title: {
      text: '任务状态概览',
      left: 'center'
    },
    tooltip: {
      trigger: 'item'
    },
    grid: [
      { left: '5%', top: '15%', width: '45%', height: '80%' },
      { right: '5%', top: '15%', width: '45%', height: '80%' }
    ],
    series: [
      {
        name: '按任务类型',
        type: 'pie',
        radius: '50%',
        center: ['25%', '50%'],
        data: taskCountByType,
        label: {
          formatter: '{b}: {c} ({d}%)'
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      },
      {
        name: '按优先级',
        type: 'pie',
        radius: '50%',
        center: ['75%', '50%'],
        data: taskCountByPriority,
        label: {
          formatter: '{b}: {c}'
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }
    ]
  }

  chart.setOption(option)
}

const fetchAndSetPositions = async () => {
  try {
    const response = await fetchPositions()
    console.log("完整的api响应：", response)
    positions.value = response
  } catch (error) {
    console.error('获取阵位数据失败:', error)
  }
}

// 根据阵位类型获取颜色
const getColorByType = (type) => {
  const colors = {
    '跑道': '#5470C6',
    '加油站': '#91CC75',
    '供电站': '#FAC858',
    '维修点': '#EE6666',
    '测试点': '#73C0DE',
    '行李装卸点': '#3BA272',
    '送餐点': '#FC8452',
    '清洁点': '#9A60B4',
    '停靠点': '#EA7CCC'
  }
  return colors[type] || '#999'
}

const fetchAndSetTasks = async () => {
  try {
    const response = await fetchTasks()
    console.log("完整的api响应：", response)
    positions.value = response
  } catch (error) {
    console.error('获取阵位数据失败:', error)
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
    .map-container, .task-container {
    margin-top: 30px;
    background: #fff;
    padding: 20px;
    border-radius: 4px;
    box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  }

    h3 {
      margin-bottom: 20px;
      color: #303133;
    }
}
</style>