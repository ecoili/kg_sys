<template>
  <div>
    <div ref="chart" style="width: 100%; height: 800px;"></div>
    <div v-if="loading" style="text-align: center; margin-top: 20px; color: #666;">
      加载中...
    </div>
    <div v-if="error" style="color: red; text-align: center; margin-top: 20px;">
      {{ error }}
    </div>

    <!-- Element Plus 任务信息弹窗 -->
    <el-dialog
      v-model="showTaskDialog"
      :title="`阵位 ${selectedPositionName} 的任务列表`"
      width="50%"
      center>
      <el-table
        v-if="tasksForPosition.length > 0"
        :data="tasksForPosition"
        stripe
        style="width: 100%"
        empty-text="该阵位暂无分配任务">
        <el-table-column prop="id" label="任务ID" width="180" />
        <el-table-column prop="name" label="任务名称" />
        <el-table-column prop="type" label="任务类型" />
        <el-table-column prop="status" label="任务状态" />
      </el-table>
      <div v-else style="text-align: center; padding: 20px; color: var(--el-text-color-secondary)">
        该阵位暂无分配任务
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button type="primary" @click="showTaskDialog = false">关闭</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import * as echarts from 'echarts';
import { fetchPositions, fetchPosRelations, fetchTasksByPositionId } from '@/api/dashboard_fe.js';

export default {
  name: 'KnlGraph',
  data() {
    return {
      chart: null,
      loading: true,
      error: null,
      nodes: [],
      edges: [],
      taskNodes: [],
      taskEdges: [],
      // Element Plus 弹窗相关数据
      showTaskDialog: false,
      tasksForPosition: [],
      selectedPositionName: '',
      selectedPositionId: null
    };
  },
  async mounted() {
    await this.initChart();
    window.addEventListener('resize', this.handleResize);
  },
  beforeDestroy() {
    if (this.chart) {
      this.chart.dispose();
    }
    window.removeEventListener('resize', this.handleResize);
  },
  methods: {
    async initChart() {
      try {
        const [positionsResponse, relationsResponse] = await Promise.all([
          fetchPositions(),
          fetchPosRelations(),
        ]);

        this.nodes = positionsResponse.map(node => ({
          id: node.id.toString(),
          name: node.name,
          type: node.type,
          impt_lv: node.impt_lv,
          x_coord: node.x || 0,
          y_coord: node.y || 0,
        }));

        this.edges = relationsResponse.map(edge => ({
          source: edge.source_id.toString(),
          target: edge.target_id.toString(),
          relation_type: edge.relation_type,
          strength: edge.strength,
          distance: edge.distance,
        }));

        this.chart = echarts.init(this.$refs.chart);
        this.updateChart();

        this.chart.on('click', async params => {
          if (params.dataType === 'node' && params.data.type !== 'task') {
            this.selectedPositionId = params.data.id;
            this.selectedPositionName = params.data.name;
            await this.loadTasksForPosition(params.data.id);
          }
        });

        this.loading = false;
      } catch (err) {
        console.error('初始化图表失败:', err);
        this.error = '加载知识图谱失败，请稍后重试';
        this.loading = false;
      }
    },

    async loadTasksForPosition(positionId) {
      try {
        this.loading = true;
        const tasks = await fetchTasksByPositionId(positionId);
        this.tasksForPosition = tasks.map(task => ({
          id: task.id,
          name: task.name,
          type: task.type,
          status: task.status,
          position_id: task.current_position
        }));
        this.showTaskDialog = true;
      } catch (err) {
        console.error('加载任务失败:', err);
        this.$message.error('加载任务信息失败');
      } finally {
        this.loading = false;
      }
    },

    handleResize() {
      if (this.chart) {
        this.chart.resize();
      }
    },

    getNodeColor(type) {
      const colors = {
        跑道: '#FF6384',
        加油站: '#36A2EB',
        供电站: '#FFCE56',
        维修点: '#4BC0C0',
        测试点: '#9966FF',
        行李装卸点: '#F06292',
        送餐点: '#FFA07A',
        清洁点: '#A5D8FF',
        停靠点: '#D4A5A5',
        默认: '#CCCCCC',
      };
      return colors[type] || colors['默认'];
    },

    updateChart() {
      const option = {
        title: {
          // text: '机场知识图谱',
          left: 'center',
          textStyle: {
            fontSize: 18,
            fontWeight: 'bold'
          }
        },
        tooltip: {
          trigger: 'item',
          formatter: params => {
            if (params.dataType === 'node') {
              const node = params.data;
              return `
                <div style="font-size: 14px; padding: 8px;">
                  <div style="font-weight: bold; margin-bottom: 6px;">${node.name}</div>
                  <div>类型: ${node.type}</div>
                  <div>重要性: ${node.impt_lv}</div>
                </div>
              `;
            } else {
              const edge = params.data;
              return `
                <div style="font-size: 14px; padding: 8px;">
                  <div style="font-weight: bold; margin-bottom: 6px;">${edge.relation_type}</div>
                  <div>源节点: ${edge.source}</div>
                  <div>目标节点: ${edge.target}</div>
                  ${edge.strength ? `<div>强度: ${edge.strength}</div>` : ''}
                  ${edge.distance ? `<div>距离: ${edge.distance}</div>` : ''}
                </div>
              `;
            }
          }
        },
        legend: {
          data: ['阵位节点', '任务节点', '关系'],
          top: 30,
        },
        series: [
          {
            name: '节点',
            type: 'graph',
            layout: 'force',
            symbolSize: 50,
            roam: true,
            draggable: true,
            label: {
              show: true,
              position: 'right',
              formatter: '{b}',
              fontSize: 12
            },
            edgeSymbol: ['none', 'arrow'],
            edgeSymbolSize: 10,
            edgeLabel: {
              show: true,
              formatter: params => params.data.relation_type || 'N/A',
              fontSize: 12
            },
            force: {
              repulsion: 100,
              edgeLength: 150,
            },
            data: this.nodes.map(node => ({
              ...node,
              value: node.impt_lv || 1,
              itemStyle: {
                color: this.getNodeColor(node.type),
              },
              type: 'position',
            })),
            links: this.edges.map(edge => ({
              ...edge,
              lineStyle: {
                width: 2,
                color: '#999',
              },
            })),
            emphasis: {
              focus: 'adjacency',
              lineStyle: {
                width: 3,
              },
            },
          },
        ],
      };

      this.chart.setOption(option);
    }
  }
};
</script>

<style scoped>
.dialog-footer {
  display: flex;
  justify-content: center;
}
</style>