import os
import random
from datetime import datetime

import torch
from deap import base, creator, tools, algorithms
from sklearn.preprocessing import StandardScaler

from backend.service.model_loader import model, node_id_map, event_type_map, graph_data, reverse_node_id_map, \
    load_prediction_model
from backend.extensions import neo4j
import pandas as pd
from py2neo import Node, Relationship

from torch_geometric.data import Data

from backend.service.station_impact_prediction_multitask import RGCN_GAT_Transformer


class PredictionService:
    # def __init__(self, model_path=None, positions_file=None, relations_file=None):
        # 从配置中获取默认路径
        # from backend import config
        # self.model_path = model_path or config.MODEL_PATH
        # self.positions_file = positions_file or config.POSITIONS_FILE
        # self.relations_file = relations_file or config.RELATIONS_FILE
        # self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        # # self.model = self._load_model(model_path)
        # self.graph_data, self.node_id_map, self.reverse_node_id_map, self.event_type_map = self._prepare_graph_data(
        #     positions_file, relations_file)


    # def _load_model(self, model_path):
    #     # 添加路径检查
    #     if not os.path.exists(model_path):
    #         raise FileNotFoundError(f"模型文件不存在: {model_path}")
    #     checkpoint = torch.load(model_path, map_location=self.device)
    #
    #     # 初始化模型结构 - 需要与训练时的模型结构一致
    #     model = RGCN_GAT_Transformer(
    #         node_feat_dim=5,  # 根据positions.csv中的特征数量
    #         hidden_dim=192,  # 与训练配置一致
    #         context_dim=64,
    #         embed_dim_event_type=32,
    #         num_event_types=len(event_type_map),
    #         num_relations=2,  # connection和influence两种关系
    #         num_bases=8,
    #         transformer_nhead=4,
    #         transformer_layers=2,
    #         num_nodes=len(node_id_map),
    #         dropout=0.25
    #     )
    #
    #     model.load_state_dict(checkpoint['model_state_dict'])
    #     model.to(self.device)
    #     model.eval()
    #     return model
    def __init__(self, model_path=None, positions_file=None, relations_file=None, events_file=None, impact_file=None):

        from backend import config
        self.model_path = model_path or config.MODEL_PATH
        self.positions_file = positions_file or config.POSITIONS_FILE
        self.relations_file = relations_file or config.RELATIONS_FILE
        self.events_file = events_file or config.EVENTS_FILE
        self.impact_file = impact_file or config.IMPACT_FILE

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # 直接使用已处理好的映射,不需要额外类型转换
        self.model, self.node_id_map, self.event_type_map, self.graph_data, self.reverse_node_id_map = load_prediction_model(
            self.model_path,
            self.positions_file,
            self.relations_file,
            self.events_file,
            self.impact_file
        )


        self.model.to(self.device)
        self.model.eval()
        # 调试打印
        print(f"Loaded positions: {len(self.node_id_map)}")
        print("Sample position IDs:", list(self.node_id_map.keys())[:10])
        if '25200' not in self.node_id_map:
            print("Warning: 25200 not found in node_id_map!")

    def predict_impact(self, source_position_id, event_type, severity, duration):
        """更健壮的预测方法，确保所有输入张量形状正确"""
        try:
            # 确保所有ID都转换为字符串类型处理
            source_position_id = str(source_position_id)

            # 参数验证
            if source_position_id not in self.node_id_map:
                raise ValueError(f"Invalid source_position_id: {source_position_id}")
            if event_type not in self.event_type_map:
                raise ValueError(f"Invalid event_type: {event_type}")

            # 准备输入数据 - 特别注意维度处理
            source_node_idx = self.node_id_map[source_position_id]
            event_type_idx = self.event_type_map[event_type]

            # 创建形状为 [batch_size=1, 1] 的输入张量
            source_nodes_tensor = torch.tensor([[source_node_idx]], device=self.device)  # shape: [1, 1]
            event_types_tensor = torch.tensor([[event_type_idx]], device=self.device)  # shape: [1, 1]
            severity_tensor = torch.tensor([[severity]], device=self.device).float()  # shape: [1, 1]
            duration_tensor = torch.tensor([[duration]], device=self.device).float()  # shape: [1, 1]

            # 调用模型预测
            with torch.no_grad():
                outputs, _ = self.model(
                    self.graph_data.x.to(self.device),
                    self.graph_data.edge_index.to(self.device),
                    self.graph_data.edge_type.to(self.device),
                    source_nodes_tensor,
                    event_types_tensor,
                    severity_tensor,
                    duration_tensor
                )

            # 处理预测结果 - 模型输出形状应为 [1, num_targets, 2]
            impact_logits = outputs[0, :, 0]  # 分类logits
            impact_times = outputs[0, :, 1]  # 回归时间

            impact_probs = torch.sigmoid(impact_logits)  # 获取分类概率

            predictions = []
            for node_idx in range(len(impact_probs)):
                position_id = str(self.reverse_node_id_map[node_idx])
                predictions.append({
                    "position_id": position_id,
                    "impact_probability": impact_probs[node_idx].item(),  # 单个概率值
                    "is_affected": 1 if impact_probs[node_idx] > 0.5 else 0,
                    "predicted_impact_time_minutes": max(0, impact_times[node_idx].item())  # 单个时间值
                })

            return predictions

        except Exception as e:
            print(f"预测失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"预测过程中发生错误: {str(e)}") from e

    # 在PredictionService类中添加多任务预测方法
    def predict_multitask_impact(self, source_position_ids, event_types, severities, durations):
        """多任务预测方法"""
        try:
            # 验证输入参数
            if len(source_position_ids) != len(event_types) != len(severities) != len(durations):
                raise ValueError("所有输入列表的长度必须一致")

            # 准备批量输入数据
            batch_size = len(source_position_ids)
            source_node_indices = []
            event_type_indices = []
            severity_tensor = []
            duration_tensor = []

            for i in range(batch_size):
                # 确保所有ID都转换为字符串类型处理
                pos_id = str(source_position_ids[i])
                if pos_id not in self.node_id_map:
                    raise ValueError(f"无效的阵位ID: {pos_id}")

                event_type = event_types[i]
                if event_type not in self.event_type_map:
                    raise ValueError(f"无效的事件类型: {event_type}")

                source_node_indices.append(self.node_id_map[pos_id])
                event_type_indices.append(self.event_type_map[event_type])
                severity_tensor.append(float(severities[i]))
                duration_tensor.append(float(durations[i]))

            # 转换为张量
            source_node_indices = torch.tensor(source_node_indices, device=self.device)
            event_type_indices = torch.tensor(event_type_indices, device=self.device)
            severity_tensor = torch.tensor(severity_tensor, device=self.device).unsqueeze(1)
            duration_tensor = torch.tensor(duration_tensor, device=self.device).unsqueeze(1)

            # 批量预测
            with torch.no_grad():
                impact_probs, impact_times = self.model(
                    self.graph_data.x.to(self.device),
                    self.graph_data.edge_index.to(self.device),
                    self.graph_data.edge_type.to(self.device),
                    source_node_indices,
                    event_type_indices,
                    severity_tensor,
                    duration_tensor
                )

            # 处理预测结果
            all_predictions = []
            for batch_idx in range(batch_size):
                predictions = []
                for node_idx, (prob, time) in enumerate(zip(impact_probs[batch_idx], impact_times[batch_idx])):
                    position_id = str(self.reverse_node_id_map[node_idx])
                    predictions.append({
                        "position_id": position_id,
                        "impact_probability": prob.item(),
                        "is_affected": 1 if prob > 0.5 else 0,
                        "predicted_impact_time_minutes": max(0, time.item()),
                        "source_position_id": source_position_ids[batch_idx],
                        "event_type": event_types[batch_idx]
                    })
                all_predictions.append(predictions)

            return all_predictions

        except Exception as e:
            print(f"多任务预测失败: {str(e)}")
            raise

    def _save_to_neo4j(self, source_position_id, event_type, severity, predictions):
        # 连接到Neo4j
        graph = neo4j.graph

        # 创建事件节点
        event_node = Node("Event",
                          event_id=f"EVENT_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                          type=event_type,
                          severity=severity,
                          timestamp=datetime.now().isoformat())
        graph.create(event_node)

        # 连接到源阵位
        source_node = graph.nodes.match("Position", id=source_position_id).first()
        if source_node:
            rel = Relationship(source_node, "HAS_EVENT", event_node)
            graph.create(rel)

        # 添加预测结果
        for pred in predictions:
            if pred['is_affected'] == 1:
                target_node = graph.nodes.match("Position", id=pred['position_id']).first()
                if target_node:
                    impact_rel = Relationship(event_node, "PREDICTED_IMPACT", target_node,
                                              probability=pred['impact_probability'],
                                              time_minutes=pred['predicted_impact_time_minutes'])
                    graph.create(impact_rel)

    def genetic_algorithm_schedule(self, predictions):
        """基于遗传算法的任务调度优化方法
        Args:
            predictions: 预测结果列表，包含各阵位受影响情况

        Returns:
            list: 最优调度方案，每个元素包含任务ID、原阵位、新阵位等信息
        """
        try:
            # ==================== 1. 数据准备阶段 ====================
            # 获取受影响阵位ID列表（概率>0.5且时间>0的阵位）
            # affected_positions = [
            #     str(p['position_id']) for p in predictions
            #     if p['is_affected'] == 1 and p['predicted_impact_time_minutes'] > 0
            # ]
            # 降低调度阈值条件

            # # 获取受影响阵位
            # affected_positions = [
            #     str(p['position_id']) for p in predictions
            #     if p['impact_probability'] > 0.2 and p['predicted_impact_time_minutes'] > 0
            # ]
            # 转换受影响阵位ID为整数类型
            affected_positions = [
                int(p['position_id']) for p in predictions
                if p['impact_probability'] > 0.2 and p['predicted_impact_time_minutes'] > 0
            ]

            if not affected_positions:
                return []

            # 调试信息
            print("\n=== 检查受影响阵位上的任务 ===")
            check_query = """
                    MATCH (p:Position {id: $pos_id})<-[:ASSIGNED_TO]-(t:Task)
                    RETURN t.id as task_id, t.status as status
                    """
            for pos_id in affected_positions[:5]:  # 检查前5个
                tasks = neo4j.graph.run(check_query, pos_id=pos_id).data()
                print(f"阵位 {pos_id} 上的任务: {tasks}")

            if not affected_positions:
                print("没有检测到受影响阵位")
                return []

            # 在查询前打印参数验证
            print(f"传递给Neo4j的affected_ids类型: {type(affected_positions[0])}")
            print(f"示例affected_id值: {affected_positions[0]}")
            print(f"25273是否在传递给Neo4j的参数中: {'25273' in affected_positions}")

            # 确保参数类型正确
            affected_ids = [id for id in affected_positions]
            # 测试
            total_tasks = neo4j.graph.run("MATCH (t:Task) RETURN count(t)").evaluate()
            print(f"知识图谱中总任务数: {total_tasks}")

            assigned_tasks = neo4j.graph.run("""
            MATCH (t:Task)-[r:ASSIGNED_TO]->(p:Position)
            RETURN t.id as task_id, p.id as position_id, t.status as status
            LIMIT 10
            """).data()
            print("示例任务分配关系:", assigned_tasks)
            # 在查询前添加验证查询
            validation_query = """
            UNWIND $affected_ids AS id
            MATCH (p:Position {id: id})<-[:ASSIGNED_TO]-(t:Task)
            RETURN id, count(t) AS task_count
            """
            affected_with_counts = neo4j.graph.run(validation_query, affected_ids=affected_positions).data()
            print("各受影响阵位上的任务数量:", affected_with_counts)

            # 查询需要调度的任务（当前分配在受影响阵位上的任务）
            # 查询需要调度的任务
            query = """
                    MATCH (t:Task)-[r:ASSIGNED_TO]->(p:Position)
                    WHERE p.id IN $affected_ids 
                          AND t.status IN ['待分配', '已分配']
                    RETURN t.id as task_id, 
                           t.type as task_type,
                           t.priority as priority,
                           t.deadline as deadline,
                           p.id as current_position,
                           p.name as position_name,
                           t.required_resources as required_resources,
                           t.required_position_types as required_position_types
                    """
            try:
                tasks = list(neo4j.graph.run(query, affected_ids=affected_positions))
                print("成功进入到查询方法")
            except Exception as e:
                print(f"Neo4j查询失败: {str(e)}")
                print(f"查询语句: {query}")
                print(f"参数: affected_ids={affected_positions}")
                return []
            print(f"找到的任务数量: {len(tasks)}")
            if tasks:
                print(f"示例任务: {tasks[0]}")
            if not tasks:
                # return []  # 没有需要调度的任务
                # 尝试查询所有状态的任务
                backup_query = """
                    MATCH (t:Task)-[r:ASSIGNED_TO]->(p:Position)
                    WHERE p.id IN $affected_ids
                    RETURN t.id as task_id, ...
                    """
                tasks = list(neo4j.graph.run(backup_query, affected_ids=affected_positions))
                print("放宽条件后找到的任务数量:", len(tasks))

            # 添加数据验证查询
            data_check_query = """
            MATCH (p:Position {id: "25273"})<-[:ASSIGNED_TO]-(t:Task)
            RETURN count(t) as task_count
            """
            task_count = neo4j.graph.run(data_check_query).data()
            print(f"阵位25273上的任务数量: {task_count}")

            # 查询所有可用阵位（非受影响阵位） - 修复后的查询
            query = """
                    MATCH (p:Position)
                    WHERE NOT p.id IN $affected_ids
                    RETURN p
                    """
            try:
                all_positions = [record['p'] for record in neo4j.graph.run(query, affected_ids=affected_positions)]
            except Exception as e:
                print(f"查询可用阵位失败: {str(e)}")
                print(f"查询语句: {query}")
                print(f"参数: affected_ids={affected_positions}")
                raise
            # 在genetic_algorithm_schedule方法开头添加
            print(f"受影响阵位数量: {len(affected_positions)}")
            print(f"需要调度的任务数量: {len(tasks)}")
            print(f"可用阵位数量: {len(all_positions)}")
            print(f"最高影响概率: {max(p['impact_probability'] for p in predictions)}")
            print(f"平均影响概率: {sum(p['impact_probability'] for p in predictions) / len(predictions)}")

            # ==================== 2. 遗传算法配置 ====================
            # 添加距离计算辅助方法
            def _calculate_distance(pos1, pos2):
                """计算两个阵位间的距离"""
                return ((pos1['x'] - pos2['x']) ** 2 + (pos1['y'] - pos2['y']) ** 2) ** 0.5

            def _estimate_move_time(pos1, pos2, speed=0.5):
                """预估移动时间（分钟）
                speed: 单位 km/min (假设0.5km/min≈30km/h)
                """
                distance = _calculate_distance(pos1, pos2)  # 假设坐标单位为km
                return distance / speed

            def get_position_by_id(position_id):
                """根据ID获取阵位节点"""
                try:
                    # 确保ID类型一致（根据文档1，应该是整数）
                    position_id = int(position_id)
                    position = neo4j.graph.nodes.match("Position", id=position_id).first()
                    if not position:
                        raise ValueError(f"未找到ID为 {position_id} 的阵位")
                    return position
                except (ValueError, TypeError) as e:
                    raise ValueError(f"无效的阵位ID: {position_id}") from e
            # 定义适应度函数（需要最大化）
            def evaluate(individual):
                """评估个体适应度
                Args:
                    individual: 二进制基因序列，1表示执行调度，0表示保持原状
                Returns:
                    float: 适应度得分
                """
                total_score = 0.0
                penalty = 0  # 违规惩罚

                for i, gene in enumerate(individual):
                    if gene == 1:
                        task = tasks[i]

                        # 验证任务数据完整性
                        if 'required_position_types' not in task:
                            penalty -= 10  # 严重违规
                            continue

                        # 获取可用阵位
                        suitable_positions = [
                            p for p in all_positions
                            if p['name'] in task['required_position_types']
                        ]

                        if not suitable_positions:
                            penalty -= 5  # 无合适位置惩罚
                            continue

                        # 1. 基础得分计算
                        original_pos = next((p for p in all_positions if p['id'] == task['current_position']), None)

                        # 优先级得分 (30%)
                        priority_score = task.get('priority', 1) * 0.3

                        # 时间紧迫性 (30%)
                        try:
                            deadline = datetime.fromisoformat(task['deadline'])
                            time_left = (deadline - datetime.now()).total_seconds() / 3600  # 小时为单位
                            urgency_score = (1 / (time_left + 0.1)) * 0.3  # 防止除零
                        except:
                            urgency_score = 0

                        # 距离得分 (40%)
                        if original_pos:
                            min_distance = min(
                                _calculate_distance(original_pos, p)
                                for p in suitable_positions
                            )
                            distance_score = (1 / (min_distance + 0.1)) * 0.4
                        else:
                            distance_score = 0

                        total_score += priority_score + urgency_score + distance_score

                return total_score + penalty,


            # 遗传算法工具箱配置
            creator.create("FitnessMax", base.Fitness, weights=(1.0,))
            creator.create("Individual", list, fitness=creator.FitnessMax)

            toolbox = base.Toolbox()
            toolbox.register("attr_bool", random.randint, 0, 1)
            toolbox.register("individual", tools.initRepeat, creator.Individual,
                             toolbox.attr_bool, len(tasks))
            toolbox.register("population", tools.initRepeat, list, toolbox.individual)
            toolbox.register("evaluate", evaluate)
            toolbox.register("mate", tools.cxTwoPoint)
            toolbox.register("mutate", tools.mutFlipBit, indpb=0.15)
            toolbox.register("select", tools.selTournament, tournsize=3)

            # ==================== 3. 运行遗传算法 ====================
            population = toolbox.population(n=200)
            algorithms.eaSimple(
                population, toolbox,
                cxpb=0.7,  # 交叉概率
                mutpb=0.2,  # 变异概率
                ngen=50,  # 迭代次数
                verbose=False
            )

            # 获取最优个体
            best_individual = tools.selBest(population, 1)[0]

            # ==================== 4. 生成调度方案 ====================
            schedule_plan = []

            for i, gene in enumerate(best_individual):
                if gene == 1:  # 需要调度的任务
                    task = tasks[i]

                    # 查找最佳替代阵位
                    suitable_positions = [
                        p for p in all_positions
                        if p['name'] in task['required_position_types']
                    ]

                    if suitable_positions:
                        # 获取原始位置
                        original_pos_id = task["current_position"]
                        original_pos = get_position_by_id(original_pos_id)  # 需要实现这个函数
                        # 选择资源匹配度最高的阵位
                        best_pos = min(
                            suitable_positions,
                            key=lambda p: _calculate_distance(original_pos, p)
                        )

                        # 在Neo4j中更新任务分配
                        neo4j.graph.run("""
                        MATCH (t:Task {id: $task_id})-[r:ASSIGNED_TO]->(old:Position)
                        DELETE r
                        CREATE (t)-[:ASSIGNED_TO {
                            assigned_time: datetime().toString(),
                            reason: '原阵位受影响'
                        }]->(new:Position {id: $new_pos_id})
                        """, task_id=task['task_id'], new_pos_id=best_pos['id'])

                        # 记录调度方案
                        schedule_plan.append({
                            'task_id': task['task_id'],
                            'task_type': task['task_type'],
                            'original_position': task['current_position'],
                            'original_position_name': task['current_position_name'],
                            'new_position': best_pos['id'],
                            'new_position_name': best_pos['name'],
                            'reason': f"原阵位受影响(概率{predictions[i]['impact_probability']:.1%})",
                            'priority': task['priority'],
                            'deadline': task['deadline'],
                            'distance': _calculate_distance(original_pos, best_pos),
                            'move_time': _estimate_move_time(original_pos, best_pos)
                        })

            return schedule_plan

        except Exception as e:
            print(f"调度算法执行失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return []

    def schedule(self, source_position_id, event_type, severity, duration):
        predictions = self.predict_impact(source_position_id, event_type, severity, duration)
        best_schedule = self.genetic_algorithm_schedule(predictions)
        return best_schedule
