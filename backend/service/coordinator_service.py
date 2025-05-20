from backend.service.impact_prediction_service import ImpactPredictionService
from backend.service.genetic_scheduler_service import GeneticSchedulerService
from backend.extensions import neo4j

class CoordinatorService:
    def __init__(self):
        self.prediction_service = ImpactPredictionService()
        self.scheduler_service = GeneticSchedulerService(self.prediction_service)
        self.scheduled_tasks = set()  # 全局记录已调度任务
        self.occupied_positions = set()  # 全局记录已占用阵位
    def predict_and_schedule(self, source_position_id, event_type, severity, duration):
        """预测影响并生成调度方案"""
        # 预测影响
        predictions = self.prediction_service.predict_impact(
            source_position_id, event_type, severity, duration
        )

        # 生成调度方案
        schedule_result = self.scheduler_service.schedule_tasks(predictions)

        # 更新知识图谱
        # if schedule_result['schedule']:
        #     self._update_knowledge_graph(schedule_result['schedule'])

        return schedule_result

    def batch_predict_and_schedule(self, source_position_ids, event_types, severities, durations):
        """批量预测影响并生成调度方案"""
        # 验证输入参数
        if not all(isinstance(x, (list, tuple)) for x in [source_position_ids, event_types, severities, durations]):
            raise ValueError("所有输入参数必须是列表")

        if len(source_position_ids) != len(event_types) != len(severities) != len(durations):
            raise ValueError("所有输入列表的长度必须一致")

        # 批量预测影响
        all_predictions = self.prediction_service.predict_multitask_impact(
            source_position_ids, event_types, severities, durations
        )

        # 为每个事件生成调度方案
        results = []
        for predictions in all_predictions:
            schedule = self.scheduler_service.schedule_tasks(predictions)
            results.append({
                'predictions': predictions,  # 确保包含predictions字段
                'source_position_id': predictions[0]['source_position_id'],
                'event_type': predictions[0]['event_type'],
                'schedule': schedule['schedule'] if schedule else []  # 从schedule_tasks返回结果中提取schedule
            })

        return results

    # def _update_knowledge_graph(self, schedule):
    #     """更新知识图谱中的任务分配关系"""
    #     for task_schedule in schedule:
    #         # 删除原分配关系
    #         query = """
    #         MATCH (t:Task {id: $task_id})-[r:ASSIGNED_TO]->(p:Position)
    #         DELETE r
    #         """
    #         neo4j.graph.run(query, task_id=task_schedule['task_id'])
    #
    #         # 创建新分配关系
    #         query = """
    #         MATCH (t:Task {id: $task_id}), (p:Position {id: $position_id})
    #         MERGE (t)-[r:ASSIGNED_TO]->(p)
    #         SET r.assigned_time = datetime()
    #         """
    #         neo4j.graph.run(query,
    #                         task_id=task_schedule['task_id'],
    #                         position_id=task_schedule['new_position'])

    def predict_and_schedule_multitask(self, source_position_ids, event_types, severities, durations):
        """处理复合特情的预测和调度"""
        # 1. 合并所有特情的影响预测
        all_predictions = self.prediction_service.predict_multitask_impact(
            source_position_ids, event_types, severities, durations
        )

        # 2. 合并影响预测结果（取各阵位影响的最大值）
        combined_predictions = self._combine_predictions(all_predictions)

        # 3. 生成统一调度方案
        schedule = self.scheduler_service.schedule_tasks(combined_predictions)

        return {
            'predictions': combined_predictions,
            'schedule': schedule['schedule']
        }

    def predict_and_schedule_joint(self, source_position_ids, event_types, severities, durations):
        """多阵位联合预测与调度"""
        # 1. 联合影响预测
        joint_predictions = self.prediction_service.predict_joint_impact(
            source_position_ids, event_types, severities, durations
        )

        # 2. 获取受影响阵位
        affected_positions = [
            int(p['position_id']) for p in joint_predictions
            if p['impact_probability'] > 0.1 and p['predicted_impact_time_minutes'] > 0
        ]

        if not affected_positions:
            return {"predictions": joint_predictions, "schedule": []}

        # 3. 获取需要调度的任务（去重）
        tasks = self._fetch_unique_tasks(affected_positions)

        if not tasks:
            return {"predictions": joint_predictions, "schedule": []}

        # 4. 获取可用阵位
        all_positions = self._fetch_available_positions(affected_positions)

        if not all_positions:
            return {"predictions": joint_predictions, "schedule": []}

        # 5. 运行遗传算法
        best_individual = self.scheduler_service._run_genetic_algorithm(tasks, all_positions)

        if not best_individual:
            return {"predictions": joint_predictions, "schedule": []}

        # 6. 生成调度方案
        schedule_plan = self.scheduler_service._generate_schedule_plan(
            best_individual, tasks, all_positions, joint_predictions
        )

        return {
            "predictions": joint_predictions,
            "schedule": schedule_plan,
            "joint_event": True  # 标记为联合事件
        }

    def _fetch_unique_tasks(self, position_ids):
        """获取去重后的任务列表"""
        query = """
        MATCH (t:Task)-[r:ASSIGNED_TO]->(p:Position)
        WHERE p.id IN $position_ids AND t.status IN ['待分配', '已分配']
        RETURN DISTINCT t.id as task_id, t.type as task_type, 
               t.priority as priority, t.deadline as deadline,
               p.id as current_position, p.name as position_name,
               p.type as position_type, t.required_resources as required_resources,
               t.required_position_types as required_position_types
        """
        return list(neo4j.graph.run(query, position_ids=position_ids))

    def _combine_predictions(self, all_predictions):
        """合并多个特情的影响预测"""
        combined = {}

        # 遍历所有预测结果
        for predictions in all_predictions:
            for pred in predictions:
                pos_id = pred['position_id']

                # 对每个阵位，保留最大的影响概率和最长的预计影响时间
                if pos_id not in combined:
                    combined[pos_id] = pred
                else:
                    if pred['impact_probability'] > combined[pos_id]['impact_probability']:
                        combined[pos_id]['impact_probability'] = pred['impact_probability']
                    if pred['predicted_impact_time_minutes'] > combined[pos_id]['predicted_impact_time_minutes']:
                        combined[pos_id]['predicted_impact_time_minutes'] = pred['predicted_impact_time_minutes']
                    combined[pos_id]['is_affected'] = (
                            combined[pos_id]['is_affected'] or pred['is_affected']
                    )

        return list(combined.values())

