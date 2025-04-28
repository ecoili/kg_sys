import random
from datetime import datetime
import torch
from deap import base, creator, tools, algorithms
from backend.service.model_loader import model, node_id_map, event_type_map, graph_data, reverse_node_id_map
from backend.extensions import neo4j
import pandas as pd
from py2neo import Node, Relationship
from torch_geometric.data import Data

class PredictionService:
    def __init__(self, model_path, positions_file, relations_file):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = self._load_model(model_path)
        self.graph_data, self.node_id_map, self.reverse_node_id_map, self.event_type_map = self._prepare_graph_data(
            positions_file, relations_file)

    def _load_model(self, model_path):
        checkpoint = torch.load(model_path, map_location=self.device)
        model = ...  # 模型初始化代码
        model.load_state_dict(checkpoint['model_state_dict'])
        model.eval()
        return model

    def _prepare_graph_data(self, positions_file, relations_file):
        # 加载并预处理图数据
        positions_df = pd.read_csv(positions_file)
        relations_df = pd.read_csv(relations_file)

        # 节点特征处理
        node_features = ...  # 特征标准化处理

        # 边处理
        edge_index = ...
        edge_type = ...

        graph_data = Data(
            x=torch.tensor(node_features, dtype=torch.float),
            edge_index=edge_index,
            edge_type=edge_type,
            num_nodes=len(node_id_map)
        )

        return graph_data, node_id_map, reverse_node_id_map, event_type_map

    # 预测影响函数
    # def predict_impact(self, source_position_id, event_type, severity, duration):
    #     # 调用预测函数
    #     predictions = ...  # 预测结果
    #
    #     # 将预测结果保存到知识图谱
    #     self._save_to_neo4j(source_position_id, event_type, predictions)
    #
    #     return predictions
    def predict_impact(self, source_position_id, event_type, severity, duration):
        """修改后的预测方法"""
        try:
            # 1. 准备输入数据
            source_node_idx = self.node_id_map[source_position_id]
            event_type_idx = self.event_type_map[event_type]

            # 2. 调用模型预测
            with torch.no_grad():
                impact_probs, impact_times = self.model(
                    self.graph_data.x.to(self.device),
                    self.graph_data.edge_index.to(self.device),
                    torch.tensor([source_node_idx], device=self.device),
                    torch.tensor([event_type_idx], device=self.device),
                    torch.tensor([severity], device=self.device).float(),
                    torch.tensor([duration], device=self.device).float()
                )

            # 3. 处理预测结果
            predictions = []
            for i, (prob, time) in enumerate(zip(impact_probs[0], impact_times[0])):
                position_id = self.reverse_node_id_map[i]
                predictions.append({
                    "position_id": position_id,
                    "impact_probability": prob.item(),
                    "is_affected": 1 if prob > 0.5 else 0,
                    "predicted_impact_time_minutes": time.item()
                })

            # 4. 保存到知识图谱
            self._save_to_neo4j(source_position_id, event_type, severity, predictions)

            return predictions

        except Exception as e:
            print(f"预测失败: {str(e)}")
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
