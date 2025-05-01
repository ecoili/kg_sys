from flask import Blueprint, request
import torch
from backend.service.model_loader import model, node_id_map, event_type_map, graph_data, reverse_node_id_map
from backend.service.station_impact_prediction_multitask import predict_single_position
from ..service.model_service import PredictionService
from ..utils.response import success_response, error_response
from backend.extensions import neo4j

dashboard_bp = Blueprint('dashboard_be', __name__)


@dashboard_bp.route('/emergency/simulate', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        print(f"Received data: {data}")
        position_id = int(data['position_id'])
        event_type = data['event_type']
        severity = float(data['severity'])
        duration = float(data['duration'])

        #  调用预测函数 方式一
        # predictions = predict_single_position(
        #     model, graph_data, position_id, event_type, severity, duration,
        #     node_id_map, event_type_map, reverse_node_id_map
        # )

        # 使用PredictionService进行预测 方式二
        service = PredictionService(
            model_path="E:/py_prjs/flask3/backend/models/pths/rgcn_gat_transformer_multitask.pth",
            positions_file="E:/py_prjs/flask3/backend/models/data/positions.csv",
            relations_file="E:/py_prjs/flask3/backend/models/data/relations.csv"
        )
        predictions = service.predict_impact(position_id, event_type, severity, duration)

        if predictions is None:
            # return jsonify({"error": "Prediction failed"}), 500
            return error_response(message='Prediction failed', code=400)
        # 将预测结果转换为JSON格式,确保所有数值都是Python原生类型
        result = [
            {
                "position_id": int(pred['position_id']),
                "impact_probability": float(pred['impact_probability']),  # 显式转换为float
                "is_affected": bool(pred['is_affected']),  # 显式转换为bool
                # "predicted_impact_time_minutes": float(pred['predicted_impact_time_minutes'])
                "predicted_impact_time_minutes": int(pred['predicted_impact_time_minutes'])
            }
            for pred in predictions
        ]
        # return jsonify(result)
        return success_response(result)
    except Exception as e:
        # return jsonify({"error": str(e)}), 500
        return error_response(message=str(e), code=500)


@dashboard_bp.route('/getpositions', methods=['GET'])
def get_positions():
    try:
        # 从Neo4j获取阵位数据
        graph = neo4j.graph
        positions = list(graph.nodes.match("Position"))
        # 格式化返回数据
        formatted_positions = []
        for pos in positions:
            formatted_positions.append({
                "id": pos["id"],
                "name": pos["name"],
                "x": pos["x"],
                "y": pos["y"],
                "type": pos["type"],
                "impt_lv": pos["impt_lv"],
                "flr_rate": pos["flr_rate"],
                "sup_num": pos["sup_num"]
            })

        return success_response(formatted_positions)
    except Exception as e:
        return error_response(message=str(e), code=500)


@dashboard_bp.route('/gettasks', methods=['GET'])
def get_tasks():
    try:
        # 从Neo4j获取任务数据
        graph = neo4j.graph
        tasks = list(graph.nodes.match("Task"))
        # 格式化返回数据
        formatted_tasks = []
        for task in tasks:
            formatted_tasks.append({
                "id": task["id"],
                "name": task["name"],
                "type": task["type"],
                "duration": task["duration"],
                "current_pos_name": task["current_position_name"],
                "current_pos": task["current_position"],
                "priority": task["priority"]
            })
        return success_response(formatted_tasks)
    except Exception as e:
        return error_response(message=str(e), code=500)

