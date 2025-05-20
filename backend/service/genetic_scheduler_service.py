# backend/service/genetic_scheduler_service.py
import random
import traceback
from datetime import datetime
from deap import base, creator, tools, algorithms
from backend.extensions import neo4j


class GeneticSchedulerService:
    def __init__(self, prediction_service=None):
        self.prediction_service = prediction_service
        self._setup_genetic_algorithm()

    # def schedule_tasks(self, predictions):
    #     """基于遗传算法的任务调度优化"""
    #     try:
    #         # 获取受影响阵位
    #         affected_positions = self._get_affected_positions(predictions)
    #         if not affected_positions:
    #             return {"predictions": predictions, "schedule": []}
    #         print("Affected positions:", affected_positions)
    #
    #         # 获取需要调度的任务
    #         tasks = self._fetch_tasks_to_schedule(affected_positions)
    #         if not tasks:
    #             return {"predictions": predictions, "schedule": []}
    #         print("tasks:", tasks)
    #
    #         # 确保predictions与tasks一一对应
    #         # if len(predictions) != len(tasks):
    #         #     # 这里假设predictions是所有阵位的预测结果
    #         #     # 我们需要筛选出只与当前任务相关的预测结果
    #         #     task_position_ids = {task['current_position'] for task in tasks}
    #         #     predictions = [p for p in predictions if int(p['position_id']) in task_position_ids]
    #         #     # 如果仍然不匹配，使用默认的第一个预测结果
    #         #     if len(predictions) != len(tasks):
    #         #         predictions = [predictions[0]] * len(tasks)
    #         # 在schedule_tasks方法中修改预测结果处理逻辑
    #         if len(predictions) != len(tasks):
    #             # 保留所有预测结果，不进行过滤
    #             pass
    #
    #         # 获取可用阵位
    #         all_positions = self._fetch_available_positions(affected_positions)
    #         if not all_positions:
    #             return {"predictions": predictions, "schedule": []}
    #         print("all_positions:", all_positions)
    #
    #         # 运行遗传算法
    #         best_individual = self._run_genetic_algorithm(tasks, all_positions)
    #         if not best_individual:  # 如果没有找到合适的个体
    #             return {"predictions": predictions, "schedule": []}
    #         print("best_individual:", best_individual)
    #
    #         schedule_plan = self._generate_schedule_plan(best_individual, tasks, all_positions, predictions)
    #         print("schedule_plan:", schedule_plan)
    #         return {"predictions": predictions, "schedule": schedule_plan}
    #
    #     except Exception as e:
    #         print(f"调度算法执行失败: {str(e)}")
    #         traceback.print_exc()
    #         return {"predictions": predictions, "schedule": []}
    def schedule_tasks(self, predictions):
        try:
            affected_positions = self._get_affected_positions(predictions)
            # 若没有阵位受影响，不必调度
            if not affected_positions:
                return {"predictions": predictions, "schedule": []}

            # 获取需要调度的任务（去重）
            tasks = self._fetch_tasks_to_schedule(affected_positions)
            if not tasks:
                return {"predictions": predictions, "schedule": []}

            # 使用任务ID作为键，确保每个任务只被调度一次
            task_dict = {task['task_id']: task for task in tasks}
            unique_tasks = list(task_dict.values())

            # 查询知识图谱，获取受到影响的阵位
            all_positions = self._fetch_available_positions(affected_positions)
            if not all_positions:
                return {"predictions": predictions, "schedule": []}

            best_individual = self._run_genetic_algorithm(unique_tasks, all_positions)
            if not best_individual:
                return {"predictions": predictions, "schedule": []}

            schedule_plan = self._generate_schedule_plan(best_individual, unique_tasks, all_positions, predictions)
            return {"predictions": predictions, "schedule": schedule_plan}
        except Exception as e:
            print(f"调度算法执行失败: {str(e)}")
            traceback.print_exc()
            return {"predictions": predictions, "schedule": []}

    def _merge_schedules(self, all_schedules):
        """合并多个调度方案，解决资源冲突"""
        merged = []
        used_positions = set()

        # 按优先级排序所有调度任务
        all_tasks = []
        for schedule in all_schedules:
            for task in schedule['schedule']:
                all_tasks.append({
                    **task,
                    'source_event': schedule['source_position_id']
                })

        # 按优先级和距离排序
        sorted_tasks = sorted(
            all_tasks,
            key=lambda x: (-x['priority'], x['distance'])
        )

        for task in sorted_tasks:
            if task['new_position'] not in used_positions:
                merged.append(task)
                used_positions.add(task['new_position'])

        return merged

    def _setup_genetic_algorithm(self):
        """初始化遗传算法配置"""
        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)

        self.toolbox = base.Toolbox()
        self.toolbox.register("attr_bool", random.randint, 0, 1)
        self.toolbox.register("individual", tools.initRepeat, creator.Individual,
                              self.toolbox.attr_bool, 100)  # 默认长度会在运行时调整
        self.toolbox.register("population", tools.initRepeat, list, self.toolbox.individual)
        self.toolbox.register("evaluate", self._evaluate_fitness)
        self.toolbox.register("mate", tools.cxTwoPoint)
        self.toolbox.register("mutate", tools.mutFlipBit, indpb=0.15)
        self.toolbox.register("select", tools.selTournament, tournsize=3)

    def _get_affected_positions(self, predictions):
        """获取受影响阵位列表"""
        # 目前影响概率大于10% 影响时间大于0分钟 就会触发调度
        return [
            int(p['position_id']) for p in predictions
            if p['impact_probability'] > 0.1 and p['predicted_impact_time_minutes'] > 0
        ]

    def _fetch_tasks_to_schedule(self, affected_positions):
        """查询需要调度的任务"""
        query = """
        MATCH (t:Task)-[r:ASSIGNED_TO]->(p:Position)
        WHERE p.id IN $affected_ids 
              AND t.status IN ['待分配', '已分配']
        RETURN t.id as task_id, 
               t.type as task_type,
               t.name as task_name,
               t.priority as priority,
               t.deadline as deadline,
               p.id as current_position,
               p.name as position_name,
               p.type as position_type,
               t.required_resources as required_resources,
               t.required_position_types as required_position_types
        """
        return list(neo4j.graph.run(query, affected_ids=affected_positions))

    def _fetch_available_positions(self, affected_positions):
        """查询所有可用阵位"""
        query = """
        MATCH (p:Position)
        WHERE NOT p.id IN $affected_ids
        RETURN p.id as id,
               p.name as name,
               p.type as type,
               p.x as x,
               p.y as y,
               p.sup_num as sup_num
        """
        return list(neo4j.graph.run(query, affected_ids=affected_positions))


    def _run_genetic_algorithm(self, tasks, all_positions):
        """运行遗传算法"""
        if not tasks:  # 如果没有任务需要调度，直接返回空个体
            return []

        # # 存储当前任务和阵位，供适应度计算使用
        # self.current_tasks = tasks
        # self.current_positions = all_positions

        # 调整个体长度以匹配任务数量
        individual_length = len(tasks)
        self.toolbox.register("individual", tools.initRepeat, creator.Individual,
                              self.toolbox.attr_bool, n=individual_length)

        # 增加种群大小和迭代次数
        pop_size = min(300, 15 * individual_length)
        population = self.toolbox.population(n=pop_size)

        algorithms.eaSimple(
            population, self.toolbox,
            cxpb=0.8, mutpb=0.3, ngen=100, verbose=False
        )

        return tools.selBest(population, 1)[0] if population else []

    # def _evaluate_fitness(self, individual):
    #     """评估个体适应度"""
    #     if not hasattr(self, 'current_tasks') or not self.current_tasks:
    #         return 0.0,  # 返回最小适应度
    #     total_score = 0.0
    #     penalty = 0
    #
    #     for i, gene in enumerate(individual):
    #         if i >= len(self.current_tasks):  # 防止索引越界
    #             penalty -= 10
    #             continue
    #         if gene == 1:
    #             task = self.current_tasks[i]
    #
    #             # 验证任务数据完整性
    #             if 'required_position_types' not in task:
    #                 penalty -= 10
    #                 continue
    #
    #             # 获取可用阵位
    #             suitable_positions = [
    #                 p for p in self.current_positions
    #                 if p['name'] in task['required_position_types']
    #             ]
    #
    #             if not suitable_positions:
    #                 penalty -= 5
    #                 continue
    #
    #             # 计算各项得分
    #             priority_score = task.get('priority', 1) * 0.3
    #             urgency_score = self._calculate_urgency_score(task)
    #             distance_score = self._calculate_distance_score(task, suitable_positions)
    #
    #             total_score += priority_score + urgency_score + distance_score
    #
    #     return total_score + penalty,
    def _evaluate_fitness(self, individual):
        if not hasattr(self, 'current_tasks') or not self.current_tasks:
            return 0.0,

        total_score = 0.0

        # 按优先级排序任务
        sorted_tasks = sorted(self.current_tasks, key=lambda x: x['priority'], reverse=True)

        for i, gene in enumerate(individual):
            if i >= len(sorted_tasks):
                continue

            if gene == 1:
                task = sorted_tasks[i]
                suitable_positions = [
                    p for p in self.current_positions
                    if p['type'] in task['required_position_types']
                ]

                if suitable_positions:
                    original_pos = self._get_position_by_id(task["current_position"])
                    # 综合考虑距离和支持任务数量
                    best_pos = min(
                        suitable_positions,
                        key=lambda p: (
                                self._calculate_distance(original_pos, p) * 0.7 +  # 距离权重70%
                                (1 / (p.get('sup_num', 1) + 0.1)) * 0.3  # 支持任务数权重30%
                        )
                    )
                    priority_weight = 1.0 + (task['priority'] * 0.2)
                    total_score += priority_weight * (
                            1 / (self._calculate_distance(original_pos, best_pos) + 0.1) * 0.7 +
                            best_pos.get('sup_num', 1) * 0.3
                    )

        return total_score,

    def _calculate_urgency_score(self, task):
        """计算任务紧迫性得分"""
        try:
            deadline = datetime.fromisoformat(task['deadline'])
            time_left = (deadline - datetime.now()).total_seconds() / 3600
            return (1 / (time_left + 0.1)) * 0.3
        except:
            return 0

    def _calculate_distance_score(self, task, suitable_positions):
        """计算距离得分"""
        original_pos = next((p for p in self.current_positions
                             if p['id'] == task['current_position']), None)
        if original_pos:
            min_distance = min(
                self._calculate_distance(original_pos, p)
                for p in suitable_positions
            )
            return (1 / (min_distance + 0.1)) * 0.4
        return 0

    def _calculate_distance(self, pos1, pos2):
        """计算两个阵位间的距离"""
        return ((pos1['x'] - pos2['x']) ** 2 + (pos1['y'] - pos2['y']) ** 2) ** 0.5

    def _estimate_move_time(self, pos1, pos2, speed=10):
        """预估移动时间（分钟）"""
        distance = self._calculate_distance(pos1, pos2)
        return distance / speed + random.randint(1, 3)

    # 在_generate_schedule_plan方法中加强类型检查：
    # def _generate_schedule_plan(self, best_individual, tasks, all_positions, predictions):
    #     schedule_plan = []
    #
    #     for i, gene in enumerate(best_individual):
    #         if i >= len(tasks):  # 防止索引越界
    #             continue
    #
    #         task = tasks[i]
    #         required_types = task['required_position_types']
    #         if isinstance(required_types, str):
    #             required_types = [required_types]
    #
    #         suitable_positions = [
    #             p for p in all_positions
    #             if p['name'] in required_types
    #         ]
    #         # 在关键步骤添加详细日志
    #         print(f"Task {i}: Required types: {required_types}")
    #         print(f"Available position types: {[p['name'] for p in all_positions]}")
    #         print(f"Found {len(suitable_positions)} suitable positions")
    #
    #         if gene == 1 and suitable_positions:
    #             # 选择最近的可用阵位
    #             original_pos = self._get_position_by_id(task["current_position"])
    #             best_pos = min(
    #                 suitable_positions,
    #                 key=lambda p: self._calculate_distance(original_pos, p)
    #             )
    #
    #             schedule_plan.append(self._create_schedule_entry(
    #                 task, original_pos, best_pos, predictions[i]
    #             ))
    #
    #     return schedule_plan
    def _generate_schedule_plan(self, best_individual, tasks, all_positions, predictions):
        """确保所有任务都有调度方案"""
        schedule_plan = []

        # 创建预测结果的字典映射，按position_id索引
        prediction_map = {pred['position_id']: pred for pred in predictions}

        # 按优先级排序任务
        sorted_tasks = sorted(tasks, key=lambda x: x['priority'], reverse=True)

        for i, gene in enumerate(best_individual):
            if i >= len(sorted_tasks):
                continue

            task = sorted_tasks[i]
            required_types = task['required_position_types']
            if isinstance(required_types, str):
                required_types = [required_types]

            suitable_positions = [
                p for p in all_positions
                if p['type'] in required_types
                if p['type'] in required_types
            ]

            # 即使gene=0，也确保高优先级任务有调度方案
            if (gene == 1 or task['priority'] >= 2) and suitable_positions:
                original_pos = self._get_position_by_id(task["current_position"])
                best_pos = min(
                    suitable_positions,
                    key=lambda p: self._calculate_distance(original_pos, p)
                )
                # schedule_plan.append(self._create_schedule_entry(
                #     task, original_pos, best_pos, predictions[i]
                # ))

                # 获取当前阵位的预测结果
                current_position_id = str(task["current_position"])
                pred = prediction_map.get(current_position_id, {
                    'impact_probability': 0.5,
                    'predicted_impact_time_minutes': 0
                })

                schedule_plan.append(self._create_schedule_entry(
                    task, original_pos, best_pos, pred
                ))

        return schedule_plan
    def _get_position_by_id(self, position_id):
        """根据ID获取阵位节点"""
        position = neo4j.graph.nodes.match("Position", id=int(position_id)).first()
        if not position:
            raise ValueError(f"未找到ID为 {position_id} 的阵位")
        return position


    def _update_task_assignment(self, task_id, new_pos_id):
        """更新Neo4j中的任务分配"""
        neo4j.graph.run("""
        MATCH (t:Task {id: $task_id})-[r:ASSIGNED_TO]->(old:Position)
        DELETE r
        CREATE (t)-[:ASSIGNED_TO {
            assigned_time: datetime().toString(),
            reason: '原阵位受影响'
        }]->(new:Position {id: $new_pos_id})
        """, task_id=task_id, new_pos_id=new_pos_id)

    def _create_schedule_entry(self, task, original_pos, best_pos, prediction):
        """创建调度方案条目"""
        return {
            'task_id': task['task_id'],
            'task_type': task['task_type'],
            'task_name': task.get('task_name', ''),
            'original_position': task['current_position'],
            'original_position_name': task['position_name'],
            'new_position': best_pos['id'],
            'new_position_name': best_pos['name'],
            'new_position_sup_num': best_pos.get('sup_num', 1),  # 新增支持任务数
            'reason': f"原阵位受影响(概率{prediction['impact_probability']:.1%})",
            'priority': task['priority'],
            'deadline': task['deadline'],
            'distance': self._calculate_distance(original_pos, best_pos),
            'move_time': self._estimate_move_time(original_pos, best_pos)
        }

    def _evaluate_fitness_joint(self, individual, tasks, positions, predictions):
        """联合预测专用的适应度评估"""
        total_score = 0.0
        affected_positions = {int(p['position_id']) for p in predictions if p['is_affected']}

        # 按优先级排序任务
        sorted_tasks = sorted(tasks, key=lambda x: x['priority'], reverse=True)

        for i, gene in enumerate(individual):
            if i >= len(sorted_tasks):
                continue

            task = sorted_tasks[i]
            if gene == 1:
                # 只考虑受影响阵位的任务
                if int(task['current_position']) not in affected_positions:
                    continue

                suitable_positions = [
                    p for p in positions
                    if p['type'] in task['required_position_types']
                       and p['id'] not in affected_positions
                ]

                if suitable_positions:
                    original_pos = self._get_position_by_id(task["current_position"])

                    # 综合考虑距离、支持任务数和影响程度
                    best_pos = min(
                        suitable_positions,
                        key=lambda p: (
                                self._calculate_distance(original_pos, p) * 0.6 +
                                (1 / (p.get('sup_num', 1) + 0.1)) * 0.2 +
                                (1 - self._get_position_impact(p['id'], predictions)) * 0.2
                        )
                    )

                    priority_weight = 1.0 + (task['priority'] * 0.2)
                    total_score += priority_weight * (
                            1 / (self._calculate_distance(original_pos, best_pos) + 0.1) * 0.6 +
                            best_pos.get('sup_num', 1) * 0.2 +
                            (1 - self._get_position_impact(best_pos['id'], predictions)) * 0.2
                    )

        return total_score,

    def _get_position_impact(self, position_id, predictions):
        """获取阵位的影响程度"""
        for p in predictions:
            if int(p['position_id']) == int(position_id):
                return p['impact_probability']
        return 0.0