import os

from flask import Blueprint, request, jsonify

from backend.extensions import neo4j
from backend.service.model_service import PredictionService
from backend.utils.response import success_response, error_response

emerg_bp = Blueprint('emerg', __name__)


# 加载模型数据
@emerg_bp.route('/simulate/test', methods=['POST'])
def simulate():
    # try:
    #     data = request.get_json()
    #
    #     # 验证必要参数
    #     required_fields = ['position_id', 'event_type', 'severity', 'duration']
    #     if not all(field in data for field in required_fields):
    #         return error_response('缺少必要参数', code=400)
    #
    #     # 初始化预测服务
    #     service = PredictionService(
    #         model_path="path/to/your/model.pth",
    #         positions_file="path/to/positions.csv",
    #         relations_file="path/to/relations.csv"
    #     )
    #
    #     # 执行预测和调度
    #     result = service.schedule(
    #         source_position_id=data['position_id'],
    #         event_type=data['event_type'],
    #         severity=data['severity'],
    #         duration=data['duration']
    #     )
    #
    #     return success_response({
    #         'predictions': result['predictions'],
    #         'schedule': result['schedule']
    #     })
    #
    # except Exception as e:
    #     return error_response(str(e), code=500)
    try:
        data = request.get_json()
        print(f"Received data: {data}")
        required_fields = ['position_id', 'event_type', 'severity', 'duration']
        if not all(field in data for field in required_fields):
            return error_response('缺少必要参数', code=400)
        position_id = str(data['position_id'])  # 保持为字符串
        event_type = data['event_type']
        severity = float(data['severity'])
        duration = float(data['duration'])


        # 使用PredictionService进行预测
        # service = PredictionService(
        #     model_path="E:/py_prjs/flask3/backend/models/pths/rgcn_gat_transformer_multitask.pth",
        #     positions_file="E:/py_prjs/flask3/backend/models/data/positions.csv",
        #     relations_file="E:/py_prjs/flask3/backend/models/data/relations.csv"
        # )
        # 使用默认配置路径
        # 确保从config中获取路径
        from backend import config
        service = PredictionService(
            model_path=config.MODEL_PATH,
            positions_file=config.POSITIONS_FILE,
            relations_file=config.RELATIONS_FILE
        )
        print(f"模型路径: {service.model_path}")  # 调试输出
        print(f"文件存在: {os.path.exists(service.model_path)}")  # 调试输出
        # 添加更多调试信息
        print("Service initialized successfully")
        predictions = service.predict_impact(position_id, event_type, severity, duration)
        schedule = service.genetic_algorithm_schedule(predictions)  # 新增调度
        print(f"Predictions: {predictions}\n")
        print(f"schedule: {schedule}")
        if not predictions:
            return error_response(message='Prediction failed', code=400)


        # 格式化结果
        # result = [
        #     {
        #         "position_id": pred['position_id'],
        #         "impact_probability": float(pred['impact_probability']),
        #         "is_affected": bool(pred['is_affected']),
        #         "predicted_impact_time_minutes": int(pred['predicted_impact_time_minutes'])
        #     }
        #     for pred in predictions
        # ]
        # return success_response(result)
        return success_response({
            'predictions': [
                {
                    "position_id": pred['position_id'],
                    "impact_probability": float(pred['impact_probability']),
                    "is_affected": bool(pred['is_affected']),
                    "predicted_impact_time_minutes": int(pred['predicted_impact_time_minutes'])
                }
                for pred in predictions
            ],
            'schedule': schedule  # 新增调度结果
        })
    except Exception as e:
        return error_response(message=str(e), code=500)





@emerg_bp.route('/positions', methods=['GET'])
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