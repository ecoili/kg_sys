# backend/service/coordinator_service.py
from backend.service.impact_prediction_service import ImpactPredictionService
from backend.service.genetic_scheduler_service import GeneticSchedulerService


class CoordinatorService:
    def __init__(self):
        self.prediction_service = ImpactPredictionService()
        self.scheduler_service = GeneticSchedulerService(self.prediction_service)

    def predict_and_schedule(self, source_position_id, event_type, severity, duration):
        """预测影响并生成调度方案"""
        # 预测影响
        predictions = self.prediction_service.predict_impact(
            source_position_id, event_type, severity, duration
        )

        # 生成调度方案
        return self.scheduler_service.schedule_tasks(predictions)

    def batch_predict_and_schedule(self, source_position_ids, event_types, severities, durations):
        """批量预测影响并生成调度方案"""
        # 批量预测影响
        all_predictions = self.prediction_service.predict_multitask_impact(
            source_position_ids, event_types, severities, durations
        )

        # 为每个事件生成调度方案
        all_schedules = []
        for predictions in all_predictions:
            schedule = self.scheduler_service.schedule_tasks(predictions)
            all_schedules.append({
                'source_position_id': predictions[0]['source_position_id'],
                'event_type': predictions[0]['event_type'],
                'schedule': schedule
            })

        return all_schedules