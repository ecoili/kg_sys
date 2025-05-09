<script setup>
import {ref, onMounted, onBeforeUnmount, nextTick} from 'vue'
import * as echarts from 'echarts'
import {
  fetchPositions,
  fetchTasks,
  fetchPosRelations,
  fetchPosTaskRelations
} from '@/api/dashboard_fe.js'

const chartRef = ref(null)
let chartInstance = null

// 颜色映射
const positionColors = {
  '跑道': '#FF6B6B',
  '加油站': '#4ECDC4',
  '供电站': '#45B7D1',
  '维修点': '#FFA07A',
  '测试点': '#98D8C8',
  '行李装卸点': '#F06292',
  '送餐点': '#FFD166',
  '清洁点': '#A5D8FF',
  '停靠点': '#D4A5A5'
}

const taskColors = {
  '加油': '#4ECDC4',
  '供电': '#45B7D1',
  '送餐': '#FFD166',
  '清洁': '#A5D8FF',
  '起飞': '#FF6B6B',
  '维修': '#FFA07A',
  '降落': '#D4A5A5',
  '行李装卸': '#F06292',
  '测试': '#98D8C8'
}

// 加载知识图谱数据
const loadKnowledgeGraph = async () => {
  try {
    const [positions, tasks, posRelations, posTaskRelations] = await Promise.all([
      fetchPositions(),
      fetchTasks(),
      fetchPosRelations(),
      fetchPosTaskRelations()
    ])

    // 处理节点数据
    const nodes = []

    // 添加阵位节点（确保使用pos_前缀）
    positions.forEach(pos => {
      nodes.push({
        id: `pos_${pos.id}`,
        name: pos.name,
        category: 'position',
        symbolSize: 30,
        itemStyle: {
          color: positionColors[pos.type] || '#999'
        },
        ...pos
      })
    })
    console.log("一个阵位节点nodes[0]：",nodes[0])
    // 添加任务节点（确保使用task_前缀）
    tasks.forEach(task => {
      nodes.push({
        id: task.id,
        name: task.name,
        category: 'task',
        symbolSize: 20,
        itemStyle: {
          color: taskColors[task.type] || '#999'
        },
        ...task
      })
    })
    console.log("一个任务节点nodes[100]:",nodes[100])

    // 处理关系数据
    const links = []

    // 添加阵位间关系（确保源和目标使用pos_前缀）
    posRelations.forEach(rel => {
      links.push({
        source: `pos_${rel.source_id}`,
        target: `pos_${rel.target_id}`,
        relationType: rel.relation_type,
        lineStyle: {
          color: rel.relation_type === 'INFLUENCE' ? '#FF6B6B' : '#4ECDC4',
          width: 1
        }
      })
    })

    // 添加阵位-任务关系（确保源使用pos_前缀，目标使用task_前缀）
    posTaskRelations.forEach(rel => {
      links.push({
        source: rel.task_id,
        target: `pos_${rel.position_id}`,
        relationType: 'ASSIGNED_TO',
        lineStyle: {
          color: '#F83630',
          width: 1,
          type: 'dashed'
        }
      })
    })
    console.log(links[0],links[1])

    // 验证并过滤数据
    const validLinks = validateGraphData(nodes, links)
    await nextTick()
    renderChart(nodes, validLinks)


  } catch (error) {
    console.error('加载知识图谱失败:', error)
  }
}

// 数据验证
const validateGraphData = (nodes, links) => {
  const nodeIds = new Set(nodes.map(node => node.id))

  console.log('所有节点ID:', [...nodeIds])  // 打印所有节点ID
  console.log('所有关系:', links)  // 打印所有关系

  links.forEach(link => {
    if (!nodeIds.has(link.source)) {
      console.warn(`源节点不存在: ${link.source}`, link)
    }
    if (!nodeIds.has(link.target)) {
      console.warn(`目标节点不存在: ${link.target}`, link)
    }
  })

  return links.filter(link =>
    nodeIds.has(link.source) && nodeIds.has(link.target)
  )
}

// 渲染图表
const renderChart = (nodes, links) => {
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }

  const option = {
    tooltip: {
      formatter: params => {
        if (params.dataType === 'node') {
          const data = params.data
          if (data.category === 'position') {
            return `
              <div style="font-weight:bold">${data.name}</div>
              <div>类型: ${data.type}</div>
              <div>坐标: (${data.x}, ${data.y})</div>
              <div>重要性: ${data.impt_lv}</div>
              <div>故障率: ${data.flr_rate}</div>
              <div>支持飞机数: ${data.sup_num}</div>
            `
          } else {
            return `
              <div style="font-weight:bold">${data.name}</div>
              <div>类型: ${data.type}</div>
              <div>优先级: ${data.priority}</div>
              <div>持续时间: ${data.duration}分钟</div>
              <div>状态: ${data.status}</div>
              <div>分配位置: ${data.current_pos_name}</div>
            `
          }
        } else {
          return `${params.data.relationType}关系`
        }
      }
    },
    legend: {
      data: ['阵位', '任务'],
      selected: {
        '阵位': true,
        '任务': true
      }
    },
    series: [{
      type: 'graph',
      layout: 'force',
      data: nodes,
      links: links,
      categories: [
        {name: 'position', itemStyle: {color: '#FF6B6B'}},
        {name: 'task', itemStyle: {color: '#4ECDC4'}}
      ],
      roam: true,
      focusNodeAdjacency: true,
      label: {
        show: true,
        position: 'right',
        formatter: '{b}'
      },
      edgeLabel: {
        show: true,
        formatter: params => params.data.label?.formatter || '',
        fontSize: 10,
        color: '#333'
      },
      force: {
        repulsion: 150,
        edgeLength: 100,
        gravity: 0.1,
        friction: 0.6
      },
      lineStyle: {
        opacity: 0.9,
        width: 1.5,
        curveness: 0.1
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: {
          width: 2.5
        }
      }
    }]
  }

  chartInstance.setOption(option)
}

// 窗口大小变化时重新调整图表大小
const handleResize = () => {
  chartInstance && chartInstance.resize()
}

onMounted(() => {
  loadKnowledgeGraph()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  chartInstance && chartInstance.dispose()
})
</script>

<template>
  <div className="knowledge-graph-container">
    <div ref="chartRef" className="chart-container"></div>
  </div>
</template>

<style scoped lang="scss">
.knowledge-graph-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;

  .chart-container {
    width: 100%;
    height: 100%;
    min-height: 600px;
  }
}
</style>