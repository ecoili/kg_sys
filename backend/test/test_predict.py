import unittest


class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)  # add assertion here

    def test_model_loading(self):
        from backend.service.model_loader import model, node_id_map, event_type_map
        assert model is not None, "模型加载失败"
        assert len(node_id_map) > 0, "节点ID映射为空"
        assert len(event_type_map) > 0, "事件类型映射为空"
        print("✅ 模型加载测试通过")

    def test_data_preprocessing(self):
        from backend.service.model_loader import graph_data
        # 检查图数据完整性
        assert hasattr(graph_data, 'x'), "缺少节点特征"
        assert hasattr(graph_data, 'edge_index'), "缺少边索引"
        assert graph_data.num_nodes > 0, "节点数量为0"
        print("✅ 数据预处理测试通过")

if __name__ == '__main__':
    unittest.main()
