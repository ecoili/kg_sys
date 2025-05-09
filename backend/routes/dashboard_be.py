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


from flask import Blueprint, request
import torch
from backend.service.model_loader import model, node_id_map, event_type_map, graph_data, reverse_node_id_map
from backend.service.station_impact_prediction_multitask import predict_single_position
from ..service.model_service import PredictionService
from ..utils.response import success_response, error_response
from backend.extensions import neo4j

dashboard_bp = Blueprint('dashboard_be', __name__)

@dashboard_bp.route('/getpositions', methods=['GET'])
def get_positions():
    try:
        # 使用Cypher查询优化性能
        query = """
        MATCH (p:Position)
        RETURN p.id as id, p.name as name, p.x as x, p.y as y,
               p.type as type, p.impt_lv as impt_lv,
               p.flr_rate as flr_rate, p.sup_num as sup_num
        """
        result = neo4j.graph.run(query).data()
        return success_response(result)
    except Exception as e:
        return error_response(message=str(e), code=500)

@dashboard_bp.route('/gettasks', methods=['GET'])
def get_tasks():
    try:
        # 使用Cypher查询优化性能
        query = """
        MATCH (t:Task)
        RETURN t.id as id, t.name as name, t.type as type,
               t.duration as duration, t.current_position_name as current_pos_name,
               t.current_position as current_pos, t.priority as priority,
               t.deadline as deadline, t.status as status
        """
        result = neo4j.graph.run(query).data()
        return success_response(result)
    except Exception as e:
        return error_response(message=str(e), code=500)

@dashboard_bp.route('/getpositionrelations', methods=['GET'])
def get_position_relations():
    try:
        # 优化后的关系查询
        query = """
        MATCH (s:Position)-[r]->(t:Position)
        WHERE type(r) IN ['CONNECTION', 'INFLUENCE']
        RETURN s.id as source_id, s.name as source_name,
               t.id as target_id, t.name as target_name,
               type(r) as relation_type,
               COALESCE(r.strength, 1.0) as strength,
               COALESCE(r.distance, 0.0) as distance
        """
        result = neo4j.graph.run(query).data()
        return success_response(result)
    except Exception as e:
        return error_response(message=str(e), code=500)

@dashboard_bp.route('/getpositiontaskrelations', methods=['GET'])
def get_position_task_relations():
    try:
        # 优化后的任务关系查询
        query = """
        MATCH (p:Position)<-[r:ASSIGNED_TO]-(t:Task)
        RETURN p.id as position_id, p.name as position_name,
               t.id as task_id, t.name as task_name,
               type(r) as relation_type,
               r.assigned_time as assigned_time
        """
        result = neo4j.graph.run(query).data()
        return success_response(result)
    except Exception as e:
        return error_response(message=str(e), code=500)

@dashboard_bp.route('/gettasksbypositionid/<int:position_id>', methods=['GET'])
def get_tasks_by_position_id(position_id):
    try:
        # 使用Cypher查询优化性能
        query = """
        MATCH (p:Position)<-[r:ASSIGNED_TO]-(t:Task)
        WHERE p.id = $position_id
        RETURN t.id as id, t.name as name, t.type as type,
               t.duration as duration, t.current_position_name as current_pos_name,
               t.current_position as current_pos, t.priority as priority,
               t.deadline as deadline, t.status as status
        """
        result = neo4j.graph.run(query, position_id=position_id).data()
        return success_response(result)
    except Exception as e:
        return error_response(message=str(e), code=500)
