<template>
  <div>
    <h2 style="text-align: center; margin-bottom: 20px;">知识图谱可视化</h2>
    <div id="cy" style="width: 100%; height: 800px; border: 1px solid #ccc; border-radius: 8px;"></div>
    <div v-if="loading" style="text-align: center; margin-top: 20px; color: #666;">
      加载中...
    </div>
    <div v-if="error" style="color: red; text-align: center; margin-top: 20px;">
      {{ error }}
    </div>
  </div>
</template>

<script>
import cytoscape from 'cytoscape';
import { fetchPositions, fetchPosRelations } from '@/api/dashboard_fe.js'; // 确保路径正确

export default {
  name: 'KnlGraph',
  data() {
    return {
      cy: null, // Cytoscape 实例
      loading: true, // 加载状态
      error: null, // 错误信息
    };
  },
  async mounted() {
    try {
      // 并行获取节点和关系数据
      const [positionsResponse, relationsResponse] = await Promise.all([
        fetchPositions(),
        fetchPosRelations(),
      ]);

      // 处理节点数据
      const nodes = positionsResponse.map((node) => ({
        data: {
          id: node.id.toString(), // 确保 ID 是字符串（Cytoscape 要求）
          label: node.name, // 显示节点名称
          type: node.type, // 可选：存储节点类型（如 "跑道"、"加油站"）
          impt_lv: node.impt_lv, // 可选：重要性等级
        },
      }));

      // 处理关系数据
      const edges = relationsResponse.map((edge) => ({
        data: {
          id: `${edge.source_id}-${edge.target_id}`, // 唯一 ID
          source: edge.source_id.toString(), // 源节点 ID
          target: edge.target_id.toString(), // 目标节点 ID
          relation_type: edge.relation_type, // 关系类型（如 "CONNECTION"）
          strength: edge.strength, // 关系强度（可选）
          distance: edge.distance, // 距离（可选）
        },
      }));

      // 初始化 Cytoscape
      this.cy = cytoscape({
        container: document.getElementById('cy'),
        elements: [...nodes, ...edges],
        style: [
          {
            selector: 'node',
            style: {
              'background-color': '#666', // 默认背景色
              'label': 'data(label)', // 显示节点名称
              'text-valign': 'center',
              'text-halign': 'center',
              'color': '#fff', // 文字颜色
              'font-size': '12px', // 字体大小
              'width': 'label', // 根据标签自动调整宽度
              'height': 'label',
              'text-wrap': 'wrap', // 允许换行
              'text-max-width': '120px', // 最大宽度
              'border-width': '2px', // 边框宽度
              'border-color': '#fff', // 边框颜色
              'text-outline-color': '#000', // 文字轮廓颜色
              'text-outline-width': '2px', // 文字轮廓宽度
            },
          },
          {
            selector: 'edge',
            style: {
              'width': 3, // 边宽度
              'line-color': '#999', // 边线颜色
              'target-arrow-shape': 'triangle', // 箭头形状
              'target-arrow-color': '#999', // 箭头颜色
              'curve-style': 'bezier', // 曲线样式
              'label': 'data(relation_type)', // 显示关系类型
              'font-size': '10px', // 字体大小
              'color': '#333', // 文字颜色
              'text-rotation': 'autorotate', // 自动旋转标签
              'text-background-color': '#fff', // 文字背景色
              'text-background-opacity': 0.7, // 文字背景透明度
              'text-background-padding': '2px', // 文字背景内边距
            },
          },
          // 根据节点类型设置不同颜色（示例）
          {
            selector: 'node[type = "跑道"]',
            style: {
              'background-color': '#ff0000', // 红色
            },
          },
          {
            selector: 'node[type = "加油站"]',
            style: {
              'background-color': '#00ff00', // 绿色
            },
          },
          {
            selector: 'node[type = "供电站"]',
            style: {
              'background-color': '#0000ff', // 蓝色
            },
          },
          // 可根据需要添加更多类型
        ],
        layout: {
          name: 'cose', // 使用 Cose 布局
          idealEdgeLength: 150, // 理想边长，增加间距
          nodeOverlap: 30, // 节点重叠容忍度
          refresh: 20,
          fit: true,
          padding: 50, // 增加内边距
          randomize: false,
          componentSpacing: 200, // 组件间距
          nodeRepulsion: 450000, // 节点排斥力
          edgeElasticity: 150, // 边弹性
          nestingFactor: 5,
          gravity: 90,
          numIter: 2000, // 增加迭代次数，优化布局
          initialTemp: 250,
          coolingFactor: 0.9,
          minTemp: 1.0,
        },
      });

      // 添加节点悬停效果
      this.cy.on('mouseover', 'node', (event) => {
        event.target.style('background-color', '#ffcc00'); // 悬停时变为黄色
      });

      this.cy.on('mouseout', 'node', (event) => {
        // 恢复原背景色（根据类型恢复）
        const node = event.target;
        const type = node.data('type');
        if (type === '跑道') {
          node.style('background-color', '#FF6B6B');
        } else if (type === '加油站') {
          node.style('background-color', '#4ECDC4');
        } else if (type === '供电站') {
          node.style('background-color', '#45B7D1');
        }else if (type === '维修点') {
          node.style('background-color', '#FFA07A')
        }else if (type === '测试点') {
          node.style('background-color', '#98D8C8')
        }else if (type === '行李装卸带点') {
          node.style('background-color', '#F06292')
        }else if (type === '送餐点') {
          node.style('background-color', '#FFD166')
        }else if (type === '清洁点') {
          node.style('background-color', '#A5D8FF')
        }else if (type === '停靠点') {
          node.style('background-color', '#D4A5A5')
        }
        else {
          node.style('background-color', '#666');
        }
      });

      // 添加节点点击事件（可选）
      this.cy.on('tap', 'node', (event) => {
        const node = event.target;
        console.log('点击节点:', node.data());
        // 可以在这里添加跳转或其他交互逻辑
        // 例如：弹出节点详情
        alert(`节点ID: ${node.data('id')}\n名称: ${node.data('label')}\n类型: ${node.data('type')}`);
      });

      this.loading = false;
    } catch (err) {
      console.error('加载知识图谱失败:', err);
      this.error = '加载知识图谱失败，请稍后重试';
      this.loading = false;
    }
  },
  beforeDestroy() {
    // 销毁 Cytoscape 实例，避免内存泄漏
    if (this.cy) {
      this.cy.destroy();
    }
  },
};
</script>

<style scoped>
/* 可选：调整容器样式 */
#cy {
  margin: 20px auto;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

/* 可选：调整标题样式 */
h2 {
  color: #333;
  font-family: Arial, sans-serif;
}
</style>