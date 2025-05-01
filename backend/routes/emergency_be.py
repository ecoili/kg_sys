from flask import Blueprint, request, jsonify
from backend.extensions import neo4j
from backend.service.coordinator_service import CoordinatorService
from backend.utils.response import success_response, error_response

emergency_bp = Blueprint('emergency', __name__)


# @emergency_bp.route('/simulateEmerg', methods=['POST'])
# def simulate():
#     try:
#         data = request.get_json()
#         print(f"Received data: {data}")
#
#         # 验证必要参数
#         required_fields = ['position_id', 'event_type', 'severity', 'duration']
#         if not all(field in data for field in required_fields):
#             return error_response('缺少必要参数', code=400)
#
#         # 初始化协调服务
#         coordinator = CoordinatorService()
#
#         # 执行预测和调度
#         result = coordinator.predict_and_schedule(
#             source_position_id=data['position_id'],
#             event_type=data['event_type'],
#             severity=data['severity'],
#             duration=data['duration']
#         )
#
#         print(f"Predictions: {result['predictions']}\nSchedule: {result['schedule']}")
#
#         return success_response({
#             'predictions': [
#                 {
#                     "position_id": str(pred['position_id']),
#                     "impact_probability": float(pred['impact_probability']),
#                     "is_affected": bool(pred['is_affected']),
#                     "predicted_impact_time_minutes": int(pred['predicted_impact_time_minutes'])
#                 }
#                 for pred in result['predictions']
#             ],
#             'schedule': [
#                 {
#                     "task_id": str(task['task_id']),
#                     "position_id": str(task['new_position']),
#                     "position_name": task['new_position_name'],
#                     "reason": task['reason']
#                 }
#                 for task in result['schedule']
#             ]
#         })
#
#     except Exception as e:
#         print(f"Error in simulation: {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return error_response(message=str(e), code=500)
@emergency_bp.route('/simulateEmerg', methods=['POST'])
def simulate():
    try:
        data = request.get_json()
        print(f"Received data: {data}")

        # 验证必要参数
        required_fields = ['position_id', 'event_type', 'severity', 'duration']
        if not all(field in data for field in required_fields):
            return error_response('缺少必要参数', code=400)

        # 初始化协调服务
        coordinator = CoordinatorService()

        # 执行预测和调度
        result = coordinator.predict_and_schedule(
            source_position_id=data['position_id'],
            event_type=data['event_type'],
            severity=data['severity'],
            duration=data['duration']
        )

        print(f"Predictions: {result['predictions']}\nSchedule: {result['schedule']}")

        # 获取所有阵位信息用于名称映射
        positions = list(neo4j.graph.nodes.match("Position"))
        position_name_map = {str(pos['id']): pos.get('name', '未知') for pos in positions}

        return success_response({
            'predictions': [
                {
                    "position_id": str(pred['position_id']),
                    "position_name": position_name_map.get(str(pred['position_id']), '未知'),
                    "impact_probability": float(pred['impact_probability']),
                    "is_affected": bool(pred['is_affected']),
                    "predicted_impact_time_minutes": int(pred['predicted_impact_time_minutes'])
                }
                for pred in result['predictions']
            ],
            'schedule': [
                {
                    "task_id": str(task['task_id']),
                    "task_type": task['task_type'],
                    "task_name": task['task_name'],
                    "original_position": str(task['original_position']),
                    "original_position_name": task['original_position_name'],
                    "new_position": str(task['new_position']),
                    "new_position_name": task['new_position_name'],
                    "reason": task['reason'],
                    "distance": task['distance'],
                    "move_time": task['move_time']
                }
                for task in result['schedule']
            ]
        })

    except Exception as e:
        print(f"Error in simulation: {str(e)}")
        import traceback
        traceback.print_exc()
        return error_response(message=str(e), code=500)


@emergency_bp.route('/positions', methods=['GET'])
def get_positions():
    try:
        # 从Neo4j获取阵位数据
        graph = neo4j.graph
        positions = list(graph.nodes.match("Position"))

        result = [{
            'id': pos['id'],
            'name': pos.get('name', ''),
            'type': pos.get('type_identity', '')
        } for pos in positions]

        return success_response(result)
    except Exception as e:
        return error_response(str(e), code=500)