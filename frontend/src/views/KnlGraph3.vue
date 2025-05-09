<template>
  <div>
<!--    <h2 style="text-align: center; margin-bottom: 20px;">知识图谱可视化</h2>-->
    <div ref="chart" style="width: 100%; height: 800px;"></div>
    <div v-if="loading" style="text-align: center; margin-top: 20px; color: #666;">
      加载中...
    </div>
    <div v-if="error" style="color: red; text-align: center; margin-top: 20px;">
      {{ error }}
    </div>
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
    };
  },
  async mounted() {
    try {
      // 初始加载阵位节点和关系
      const [positionsResponse, relationsResponse] = await Promise.all([
        fetchPositions(),
        fetchPosRelations(),
      ]);

      this.nodes = positionsResponse.map((node) => ({
        id: node.id.toString(),
        name: node.name,
        type: node.type,
        impt_lv: node.impt_lv,
        x_coord: node.x || 0,
        y_coord: node.y || 0,
      }));

      this.edges = relationsResponse.map((edge) => ({
        source: edge.source_id.toString(),
        target: edge.target_id.toString(),
        relation_type: edge.relation_type,
        strength: edge.strength,
        distance: edge.distance,
      }));

      this.chart = echarts.init(this.$refs.chart);

      this.updateChart();

      // 响应窗口大小变化
      window.addEventListener('resize', () => {
        this.chart.resize();
      });

      this.loading = false;
    } catch (err) {
      console.error('加载知识图谱失败:', err);
      this.error = '加载知识图谱失败，请稍后重试';
      this.loading = false;
    }
  },
  beforeDestroy() {
    if (this.chart) {
      this.chart.dispose();
    }
  },
  methods: {
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
          text: '知识图谱',
          left: 'center',
        },
        tooltip: {
          trigger: 'item',
          formatter: (params) => {
            if (params.dataType === 'node') {
              const node = params.data;
              if (node.type === 'task') {
                return `
                  <div style="max-width: 300px; padding: 10px; background: #fff; border-radius: 5px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <p><strong>ID:</strong> ${node.id}</p>
                    <p><strong>名称:</strong> ${node.name}</p>
                    <p><strong>类型:</strong> ${node.type}</p>
                  </div>
                `;
              } else {
                return `
                  <div style="max-width: 300px; padding: 10px; background: #fff; border-radius: 5px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                    <p><strong>ID:</strong> ${node.id}</p>
                    <p><strong>名称:</strong> ${node.name}</p>
                    <p><strong>类型:</strong> ${node.type}</p>
                    <p><strong>重要性等级:</strong> ${node.impt_lv}</p>
                    <p><strong>坐标:</strong> (${node.x_coord}, ${node.y_coord})</p>
                  </div>
                `;
              }
            } else {
              const edge = params.data;
              return `
                <div style="max-width: 300px; padding: 10px; background: #fff; border-radius: 5px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                  <p><strong>关系类型:</strong> ${edge.relation_type}</p>
                  <p><strong>源节点:</strong> ${edge.source}</p>
                  <p><strong>目标节点:</strong> ${edge.target}</p>
                  <p><strong>关系强度:</strong> ${edge.strength || 'N/A'}</p>
                  <p><strong>距离:</strong> ${edge.distance || 'N/A'}</p>
                </div>
              `;
            }
          },
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
            },
            edgeSymbol: ['none', 'arrow'],
            edgeSymbolSize: 10,
            edgeLabel: {
              show: true,
              formatter: function (params) {
                const edge = params.data;
                return edge.relation_type || 'N/A';
              },
            },
            force: {
              repulsion: 100,
              edgeLength: 150,
            },
            data: this.nodes.map((node) => ({
              ...node,
              value: node.impt_lv || 1,
              itemStyle: {
                color: this.getNodeColor(node.type),
              },
              type: 'position', // 标记为阵位节点
            })),
            links: this.edges.map((edge) => ({
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

      // 添加点击事件监听器
      this.chart.on('click', (params) => {
        if (params.dataType === 'node' && params.data.type !== 'task') {
          this.loadTaskNodesAndRelations(params.data.id);
        }
      });
    },
    async loadTaskNodesAndRelations(positionId) {
      try {
        const taskRelationsResponse = await fetchTasksByPositionId(positionId);

        const taskNodes = taskRelationsResponse.map((task) => ({
          id: `${task.id}-task`,

          name: task.name,
          type: 'task',
          task_id: task.id,
        }));

        const taskEdges = taskRelationsResponse.map((task) => {
          const positionNode = this.nodes.find((node) => node.id === task.position_id.toString());
          return {
            source: positionNode ? positionNode.id : task.position_id.toString(),
            target: `${task.id}-task`,
            relation_type: 'assigned_to',
            strength: 1, // 可以根据实际情况设置
          };
        });

        // 合并节点和边
        this.taskNodes = taskNodes;
        this.taskEdges = taskEdges;

        // 更新图表
        this.updateChartWithTasks();
      } catch (err) {
        console.error('加载任务节点和关系失败:', err);
        this.error = '加载任务节点和关系失败，请稍后重试';
      }
    },
    updateChartWithTasks() {
      const allNodes = [...this.nodes, ...this.taskNodes];
      const allEdges = [...this.edges, ...this.taskEdges];

      const option = {
        series: [
          {
            data: allNodes.map((node) => ({
              ...node,
              value: node.type === 'task' ? 1 : (node.impt_lv || 1),
              itemStyle: {
                color: node.type === 'task' ? '#FF9800' : this.getNodeColor(node.type),
              },
              type: node.type, // 标记节点类型
            })),
            links: allEdges.map((edge) => ({
              ...edge,
              lineStyle: {
                width: 2,
                color: edge.relation_type === 'assigned_to' ? '#FF9800' : '#999',
              },
            })),
          },
        ],
      };

      this.chart.setOption(option);
    },
  },
};
</script>

<style scoped>
h2 {
  color: #333;
  font-family: Arial, sans-serif;
}
</style>