from flask import Blueprint, request, jsonify

from backend.extensions import neo4j
from backend.service.model_service import PredictionService
from backend.utils.response import success_response, error_response

emergency_bp = Blueprint('emergency', __name__)

# 没有确定，先不用
@emergency_bp.route('/simulate////test', methods=['POST'])
def simulate():
    try:
        data = request.get_json()

        # 验证必要参数
        required_fields = ['position_id', 'event_type', 'severity', 'duration']
        if not all(field in data for field in required_fields):
            return error_response('缺少必要参数', code=400)

        # 初始化预测服务
        service = PredictionService(
            model_path="path/to/your/model.pth",
            positions_file="path/to/positions.csv",
            relations_file="path/to/relations.csv"
        )

        # 执行预测和调度
        result = service.schedule(
            source_position_id=data['position_id'],
            event_type=data['event_type'],
            severity=data['severity'],
            duration=data['duration']
        )

        return success_response({
            'predictions': result['predictions'],
            'schedule': result['schedule']
        })

    except Exception as e:
        return error_response(str(e), code=500)


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