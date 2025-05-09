from flask import Blueprint, request
import torch
from backend.service.model_loader import model, node_id_map, event_type_map, graph_data, reverse_node_id_map
from backend.service.station_impact_prediction_multitask import predict_single_position
from ..service.model_service import PredictionService
from ..utils.response import success_response, error_response
from backend.extensions import neo4j
from py2neo import Graph, Node, Relationship
from datetime import datetime, timedelta
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
        # 使用Cypher查询优化性能
        query = """
        MATCH (p:Position)
        RETURN p.id as id, p.name as name, p.x as x, p.y as y,
               p.type as type, p.impt_lv as impt_lv,
               p.flr_rate as flr_rate, p.sup_num as sup_num, p.allocated_tasknum as allocated_tasknum
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
               t.deadline as deadline, t.status as status, t.required_position_types as required_position_types
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

# @dashboard_bp.route('/admin/position', methods=['POST'])
# # @jwt_required()
# @admin_required
# def add_position():
#     data = request.get_json()
#     # 实现添加阵位逻辑
#     pass
#
# @dashboard_bp.route('/admin/position/<int:position_id>', methods=['DELETE'])
# # @jwt_required()
# @admin_required
# def delete_position(position_id):
#     # 实现删除阵位逻辑
#     pass

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


@dashboard_bp.route('/task', methods=['POST'])
def add_task():
    try:
        data = request.get_json()
        # 验证必要字段
        required_fields = ['type', 'duration', 'priority']
        if not all(field in data for field in required_fields):
            return error_response(message='缺少必要字段', code=400)

        # 创建新任务
        task_types = {
            "加油": ["加油站"],
            "供电": ["供电站"],
            "送餐": ["送餐点"],
            "清洁": ["清洁点"],
            "起飞": ["跑道"],
            "维修": ["维修点"],
            "降落": ["停靠点"],
            "行李装卸": ["行李装卸点"],
            "测试": ["测试点"]
        }

        # # 获取当前最大任务ID
        # result = neo4j.graph.run("MATCH (t:Task) RETURN max(t.id) as max_id").data()
        # max_id = result[0]['max_id'] if result and result[0]['max_id'] else "T0"
        # new_id_num = int(max_id[1:]) + 1
        # new_id = f"T{new_id_num}"
        # 获取当前所有任务ID
        result = neo4j.graph.run("MATCH (t:Task) RETURN t.id as id").data()
        if result:
            # 提取数字部分并找到最大值
            max_id_num = max(int(t['id'][1:]) for t in result)
            new_id_num = max_id_num + 1
        else:
            new_id_num = 0
        new_id = f"T{new_id_num}"

        # 获取该类型任务的最大编号
        task_type = data['type']
        type_tasks = neo4j.graph.run(
            "MATCH (t:Task {type: $type}) RETURN t.name as name",
            type=task_type
        ).data()

        if type_tasks:
            # 提取数字部分并找到最大值
            max_type_num = max(int(t['name'].replace(task_type, '')) for t in type_tasks)
            new_type_num = max_type_num + 1
        else:
            new_type_num = 0

        # 创建任务节点
        task = Node(
            "Task",
            id=new_id,
            # name=f"{data['type']}{new_id_num}",
            name=f"{task_type}{new_type_num}",
            type=data['type'],
            duration=int(data['duration']),
            priority=int(data['priority']),
            status="待分配",
            required_position_types=task_types.get(data['type'], []),
            deadline=(datetime.now() + timedelta(hours=2)).isoformat()
        )
        neo4j.graph.create(task)

        return success_response({"id": new_id}, message="任务创建成功")
    except Exception as e:
        return error_response(message=str(e), code=500)


@dashboard_bp.route('/task/<string:task_id>', methods=['DELETE'])
def delete_task(task_id):
    try:
        # 检查任务是否存在
        task = neo4j.graph.nodes.match("Task", id=task_id).first()
        if not task:
            return error_response(message='任务不存在', code=404)

        # 如果任务已分配，需要先删除关系并更新阵位的allocated_tasknum
        if task['status'] == '已分配' and 'current_position' in task:
            # 获取关联的阵位
            position_id = task['current_position']
            position = neo4j.graph.nodes.match("Position", id=position_id).first()

            if position:
                # 删除关系
                neo4j.graph.run("""
                    MATCH (t:Task {id: $task_id})-[r:ASSIGNED_TO]->(p:Position)
                    DELETE r
                """, task_id=task_id)

                # 更新阵位的allocated_tasknum
                position['allocated_tasknum'] -= 1
                neo4j.graph.push(position)

        # 删除任务节点
        neo4j.graph.run("MATCH (t:Task {id: $task_id}) DELETE t", task_id=task_id)

        return success_response(message="任务删除成功")
    except Exception as e:
        return error_response(message=str(e), code=500)


@dashboard_bp.route('/task/<string:task_id>', methods=['PUT'])
def update_task(task_id):
    try:
        data = request.get_json()
        # 检查任务是否存在
        task = neo4j.graph.nodes.match("Task", id=task_id).first()
        if not task:
            return error_response(message='任务不存在', code=404)

        # 更新可修改的字段
        updatable_fields = ['duration', 'priority', 'status']
        for field in updatable_fields:
            if field in data:
                task[field] = data[field]

        neo4j.graph.push(task)
        return success_response(message="任务更新成功")
    except Exception as e:
        return error_response(message=str(e), code=500)


@dashboard_bp.route('/task/<string:task_id>/assign/<int:position_id>', methods=['POST'])
def assign_task_to_position(task_id, position_id):
    try:
        # 检查任务和阵位是否存在
        task = neo4j.graph.nodes.match("Task", id=task_id).first()
        position = neo4j.graph.nodes.match("Position", id=position_id).first()

        if not task:
            return error_response(message='任务不存在', code=404)
        if not position:
            return error_response(message='阵位不存在', code=404)

        # 检查任务是否已分配
        if task['status'] == '已分配':
            return error_response(message='任务已分配，请先取消当前分配', code=400)

        # 检查阵位是否已满
        if position['allocated_tasknum'] >= position['sup_num']:
            return error_response(message='阵位已满，无法分配更多任务', code=400)

        # 检查阵位类型是否符合任务要求
        if position['type'] not in task['required_position_types']:
            return error_response(message='阵位类型不符合任务要求', code=400)

        # 创建分配关系
        rel = Relationship(task, "ASSIGNED_TO", position,
                           assigned_time=datetime.now().isoformat())
        neo4j.graph.create(rel)

        # 更新阵位的已分配任务数
        position['allocated_tasknum'] += 1
        neo4j.graph.push(position)

        # 更新任务状态
        task['status'] = '已分配'
        task['current_position'] = position_id
        task['current_position_name'] = position['name']
        neo4j.graph.push(task)

        return success_response(message="任务分配成功")
    except Exception as e:
        return error_response(message=str(e), code=500)
