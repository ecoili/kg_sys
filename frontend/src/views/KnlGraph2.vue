<template>
  <div>
    <h2 style="text-align: center; margin-bottom: 20px;">知识图谱可视化</h2>
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
import {fetchPositions, fetchPosRelations, fetchPosTaskRelations, fetchTasks} from '@/api/dashboard_fe.js';

export default {
  name: 'KnlGraph',
  data() {
    return {
      chart: null,
      loading: true,
      error: null,
    };
  },
  async mounted() {
    try {
      const [positionsResponse, relationsResponse, tasksResponse, taskRelationsResponse] = await Promise.all([
        fetchPositions(),
        fetchPosRelations(),
        fetchTasks(),
        fetchPosTaskRelations(),
      ]);

      const nodes = positionsResponse.map((node) => ({
        id: node.id.toString(),
        name: node.name,
        type: node.type,
        impt_lv: node.impt_lv,
        // 添加更多属性用于显示
        x_coord: node.x || 0, // 假设有坐标属性
        y_coord: node.y || 0,
      }));

      const edges = relationsResponse.map((edge) => ({
        source: edge.source_id.toString(),
        target: edge.target_id.toString(),
        relation_type: edge.relation_type,
        strength: edge.strength,
        distance: edge.distance,
      }));
      // 处理任务节点和关系
    const taskNodes = tasksResponse.map((task) => ({
      id: task.id,
      name: task.name,
      type: task.type,
      // 添加更多任务属性
    }));

    const taskEdges = taskRelationsResponse.map((edge) => ({
      source: edge.position_id.toString(),
      target: edge.task_id.toString(),
      relation_type: edge.relation_type,
      assigned_time: edge.assigned_time,
    }));

      this.chart = echarts.init(this.$refs.chart);

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
              return `
                <div style="max-width: 300px; padding: 10px; background: #fff; border-radius: 5px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                  <p><strong>ID:</strong> ${node.id}</p>
                  <p><strong>名称:</strong> ${node.name}</p>
                  <p><strong>类型:</strong> ${node.type}</p>
                  <p><strong>重要性等级:</strong> ${node.impt_lv}</p>
                  <p><strong>坐标:</strong> (${node.x_coord}, ${node.y_coord})</p>
                </div>
              `;
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
          data: ['节点', '关系'],
          top: 30,
        },
        series: [
          {
            name: '节点',
            type: 'graph',
            layout: 'force',
            symbolSize: 50,
            roam: true, // 允许缩放和平移
            draggable: true, // 允许拖拽节点
            label: {
              show: true,
              position: 'right',
              formatter: '{b}',
            },
            edgeSymbol: ['none', 'arrow'],
            edgeSymbolSize: 10,
            edgeLabel: {  // 新增：配置连线标签
            show: true,  // 显示连线标签
            // formatter: '{c}',  // 默认尝试显示 edge.value，但你的数据里没有 value
            // 改为显示 relation_type
            formatter: function(params) {
              const edge = params.data;
              return edge.relation_type || 'N/A';
            },
          },
            force: {
              repulsion: 100,
              edgeLength: 150,
            },
            data: nodes.map((node) => ({
              ...node,
              value: node.impt_lv || 1,
              itemStyle: {
                color: this.getNodeColor(node.type),
              },
            })),
            links: edges.map((edge) => ({
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
  },
};
</script>

<style scoped>
h2 {
  color: #333;
  font-family: Arial, sans-serif;
}
</style>