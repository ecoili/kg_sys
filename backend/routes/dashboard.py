from flask import Blueprint, request
import torch
from backend.service.model_loader import model, node_id_map, event_type_map, graph_data, reverse_node_id_map
from backend.service.station_impact_prediction_multitask import predict_single_position
from ..service.model_service import PredictionService
from ..utils.response import success_response, error_response


board_bp = Blueprint('dashboard', __name__)


@board_bp.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        position_id = int(data['position_id'])
        event_type = data['event_type']
        severity = float(data['severity'])
        duration = float(data['duration'])

        # 调用预测函数
        predictions = predict_single_position(
            model, graph_data, position_id, event_type, severity, duration,
            node_id_map, event_type_map, reverse_node_id_map
        )

        if predictions is None:
            # return jsonify({"error": "Prediction failed"}), 500
            return error_response(message='Prediction failed', code=400)
        # 将预测结果转换为JSON格式
        result = [
            {
                "position_id": pred['position_id'],
                "impact_probability": pred['impact_probability'],
                "is_affected": pred['is_affected'],
                "predicted_impact_time_minutes": pred['predicted_impact_time_minutes']
            }
            for pred in predictions
        ]
        # return jsonify(result)
        return success_response(result)
    except Exception as e:
        # return jsonify({"error": str(e)}), 500
        return error_response(message=str(e), code=500)


# @board_bp.route('/schedule', methods=['POST'])
# def schedule():
#     prediction_data = request.json
#     # 1. 调用预测模型获取影响结果
#     impact_results = run_prediction(PREDICTION_MODEL, prediction_data)
#
#     # 2. 调用遗传算法进行调度
#     schedule = genetic_algorithm_schedule(impact_results)
#
#     return jsonify({
#         'impact': impact_results,
#         'schedule': schedule
#     })
# @board_bp.route('/schedule', methods=['POST'])
# def schedule():
#     try:
#         data = request.get_json()
#         position_id = int(data['position_id'])
#         event_type = data['event_type']
#         severity = float(data['severity'])
#         duration = float(data['duration'])
#
#         # 1. 获取预测结果
#         predictions = predict_single_position(
#             model, graph_data, position_id, event_type, severity, duration,
#             node_id_map, event_type_map, reverse_node_id_map
#         )
#
#         if not predictions:
#             return error_response(message='预测失败', code=400)
#
#         # 2. 执行调度
#         service = PredictionService()
#         schedule_result = service.genetic_algorithm_schedule(predictions)
#
#         return success_response({
#             "predictions": predictions,
#             "schedule": schedule_result
#         })
#
#     except Exception as e:
#         return error_response(message=str(e), code=500)