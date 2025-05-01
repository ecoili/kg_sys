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

    def test_neo4j(self):
        from backend import app
        def setUp(self):
            self.app = app
            self.app.config['TESTING'] = True
            # self.client = self.app.test_client()

        def test_neo4j(self):
            with self.app.app_context():
                from backend.extensions import neo4j
                graph = neo4j.graph
                self.assertIsNotNone(graph, "Neo4j 连接未初始化")

                query = """
                MATCH (p:Position) 
                RETURN p.id, p.name
                LIMIT 10
                """
                result = graph.run(query)
                for pos in result:
                    print(pos["p.id"], pos["p.name"])
                self.assertTrue(result, "查询返回空结果")
if __name__ == '__main__':
    unittest.main()
