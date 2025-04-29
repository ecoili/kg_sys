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

            # 修改severity和duration的形状处理
            severity_tensor = torch.tensor([[severity]], device=self.device).float()  # shape: [1, 1]
            duration_tensor = torch.tensor([[duration]], device=self.device).float()  # shape: [1, 1]

            # 调试打印
            print(f"Input shapes - source_nodes: {source_nodes_tensor.shape}, "
                  f"event_types: {event_types_tensor.shape}, "
                  f"severity: {severity_tensor.shape}, "
                  f"duration: {duration_tensor.shape}")

            # 调用模型预测
            with torch.no_grad():
                outputs = self.model(
                    self.graph_data.x.to(self.device),
                    self.graph_data.edge_index.to(self.device),
                    self.graph_data.edge_type.to(self.device),
                    source_nodes_tensor,
                    event_types_tensor,
                    severity_tensor,
                    duration_tensor
                )

            # 处理预测结果
            impact_probs = torch.sigmoid(outputs[0][0])  # 获取分类概率
            impact_times = outputs[1][0]  # 获取回归时间

            predictions = []
            for node_idx in range(len(impact_probs)):
                position_id = str(self.reverse_node_id_map[node_idx])
                predictions.append({
                    "position_id": position_id,
                    "impact_probability": impact_probs[node_idx].item(),
                    "is_affected": 1 if impact_probs[node_idx] > 0.5 else 0,
                    "predicted_impact_time_minutes": max(0, impact_times[node_idx].item())
                })

            return predictions

        except Exception as e:
            print(f"预测失败: {str(e)}")
            import traceback
            traceback.print_exc()
            raise ValueError(f"预测过程中发生错误: {str(e)}") from e

    # 预测影响函数
    # def predict_impact(self, source_position_id, event_type, severity, duration):
    #     # 调用预测函数
    #     predictions = ...  # 预测结果
    #
    #     # 将预测结果保存到知识图谱
    #     self._save_to_neo4j(source_position_id, event_type, predictions)
    #
    #     return predictions
    # def predict_impact(self, source_position_id, event_type, severity, duration):
    #     """修改后的预测方法"""
    #     try:
    #         # 1. 准备输入数据
    #         source_node_idx = self.node_id_map[source_position_id]
    #         event_type_idx = self.event_type_map[event_type]
    #
    #         # 2. 调用模型预测
    #         with torch.no_grad():
    #             impact_probs, impact_times = self.model(
    #                 self.graph_data.x.to(self.device),
    #                 self.graph_data.edge_index.to(self.device),
    #                 torch.tensor([source_node_idx], device=self.device),
    #                 torch.tensor([event_type_idx], device=self.device),
    #                 torch.tensor([severity], device=self.device).float(),
    #                 torch.tensor([duration], device=self.device).float()
    #             )
    #
    #         # 3. 处理预测结果
    #         predictions = []
    #         for i, (prob, time) in enumerate(zip(impact_probs[0], impact_times[0])):
    #             position_id = str(self.reverse_node_id_map[i])
    #             predictions.append({
    #                 "position_id": position_id,
    #                 "impact_probability": prob.item(),
    #                 "is_affected": 1 if prob > 0.5 else 0,
    #                 "predicted_impact_time_minutes": time.item()
    #             })
    #
    #         # 4. 保存到知识图谱
    #         self._save_to_neo4j(source_position_id, event_type, severity, predictions)
    #
    #         return predictions
    #
    #     except Exception as e:
    #         print(f"预测失败: {str(e)}")
    #         raise
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

    # def genetic_algorithm_schedule(self, predictions):
    #     # 定义遗传算法的适应度函数
    #     creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
    #     creator.create("Individual", list, fitness=creator.FitnessMin)
    #
    #     # 初始化种群
    #     toolbox = base.Toolbox()
    #     toolbox.register("attr_bool", random.randint, 0, 1)
    #     toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_bool, len(predictions))
    #     toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    #
    #     # 定义交叉和变异操作
    #     toolbox.register("mate", tools.cxTwoPoint)
    #     toolbox.register("mutate", tools.mutFlipBit, indpb=0.05)
    #     toolbox.register("select", tools.selTournament, tournsize=3)
    #
    #     # 定义适应度函数
    #     def evalSchedule(individual):
    #         total_impact = sum(
    #             pred['predicted_impact_time_minutes'] for pred, bit in zip(predictions, individual) if bit)
    #         return total_impact,
    #
    #     toolbox.register("evaluate", evalSchedule)
    #
    #     # 运行遗传算法
    #     population = toolbox.population(n=300)
    #     algorithms.eaSimple(population, toolbox, cxpb=0.5, mutpb=0.2, ngen=40, verbose=False)
    #
    #     # 获取最优解
    #     best_individual = tools.selBest(population, 1)[0]
    #     return best_individual
    def genetic_algorithm_schedule(self, predictions):
        """修改后的遗传算法调度"""
        try:
            # 1. 准备任务数据
            tasks = list(neo4j.graph.nodes.match("Task").where("_.status = '待分配'"))
            affected_positions = [p for p in predictions if p['is_affected'] == 1]

            # 2. 定义遗传算法
            creator.create("FitnessMax", base.Fitness, weights=(1.0,))
            creator.create("Individual", list, fitness=creator.FitnessMax)

            toolbox = base.Toolbox()
            toolbox.register("attr_bool", random.randint, 0, 1)
            toolbox.register("individual", tools.initRepeat, creator.Individual,
                             toolbox.attr_bool, len(tasks))
            toolbox.register("population", tools.initRepeat, list, toolbox.individual)

            # 3. 定义适应度函数
            def evaluate(individual):
                total_score = 0
                for i, gene in enumerate(individual):
                    if gene == 1:  # 选择该任务
                        task = tasks[i]
                        # 检查是否能在受影响阵位上执行
                        suitable_positions = list(neo4j.graph.nodes.match("Position").where(
                            f"_.type_identity IN {task['required_position_types']} AND _.id NOT IN {[p['position_id'] for p in affected_positions]}"
                        ))
                        if suitable_positions:
                            total_score += task['priority']  # 优先级越高得分越高

                return total_score,

            toolbox.register("evaluate", evaluate)
            toolbox.register("mate", tools.cxTwoPoint)
            toolbox.register("mutate", tools.mutFlipBit, indpb=0.1)
            toolbox.register("select", tools.selTournament, tournsize=3)

            # 4. 运行算法
            population = toolbox.population(n=100)
            algorithms.eaSimple(population, toolbox, cxpb=0.7, mutpb=0.2, ngen=50, verbose=False)

            # 5. 获取最优解并执行分配
            best_individual = tools.selBest(population, 1)[0]
            schedule = []

            for i, gene in enumerate(best_individual):
                if gene == 1:
                    task = tasks[i]
                    suitable_positions = list(neo4j.graph.nodes.match("Position").where(
                        f"_.type_identity IN {task['required_position_types']} AND _.id NOT IN {[p['position_id'] for p in affected_positions]}"
                    ))
                    if suitable_positions:
                        selected = random.choice(suitable_positions)
                        rel = Relationship(task, "ASSIGNED_TO", selected,
                                           assigned_time=datetime.now().isoformat())
                        neo4j.graph.create(rel)
                        task["status"] = "已分配"
                        neo4j.graph.push(task)
                        schedule.append({
                            "task_id": task["id"],
                            "position_id": selected["id"],
                            "position_name": selected["name"]
                        })

            return schedule

        except Exception as e:
            print(f"调度失败: {str(e)}")
            raise

    def schedule(self, source_position_id, event_type, severity, duration):
        predictions = self.predict_impact(source_position_id, event_type, severity, duration)
        best_schedule = self.genetic_algorithm_schedule(predictions)
        return best_schedule
