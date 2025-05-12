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
        updatable_fields = ['duration', 'priority', 'status', 'deadline']
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


@dashboard_bp.route('/position', methods=['POST'])
def add_position():
    try:
        data = request.get_json()
        # 验证必要字段
        required_fields = ['type', 'x', 'y', 'impt_lv', 'sup_num']
        if not all(field in data for field in required_fields):
            return error_response(message='缺少必要字段', code=400)

        # 获取当前最大阵位ID
        result = neo4j.graph.run("MATCH (p:Position) RETURN max(p.id) as max_id").data()
        max_id = result[0]['max_id'] if result and result[0]['max_id'] else 0
        new_id = max_id + 1

        # 获取该类型阵位的最大编号
        pos_type = data['type']
        type_positions = neo4j.graph.run(
            "MATCH (p:Position {type: $type}) RETURN p.name as name",
            type=pos_type
        ).data()

        if type_positions:
            # 提取数字部分并找到最大值
            max_type_num = max(int(p['name'].replace(pos_type, '')) for p in type_positions)
            new_type_num = max_type_num + 1
        else:
            new_type_num = 1

        # 创建阵位节点
        position = Node(
            "Position",
            id=new_id,
            name=f"{pos_type}{new_type_num}",
            x=int(data['x']),
            y=int(data['y']),
            type=data['type'],
            type_identity=f"{pos_type}_type",  # 示例值，根据实际情况调整
            impt_lv=int(data['impt_lv']),
            flr_rate=0.1,  # 示例值
            sup_num=int(data['sup_num']),
            allocated_tasknum=0
        )
        neo4j.graph.create(position)

        return success_response({"id": new_id}, message="阵位创建成功")
    except Exception as e:
        return error_response(message=str(e), code=500)


@dashboard_bp.route('/position/<int:position_id>', methods=['PUT'])
def update_position(position_id):
    try:
        data = request.get_json()
        # 检查阵位是否存在
        position = neo4j.graph.nodes.match("Position", id=position_id).first()
        if not position:
            return error_response(message='阵位不存在', code=404)

        # 更新可修改的字段
        updatable_fields = ['impt_lv', 'sup_num', 'x', 'y']
        for field in updatable_fields:
            if field in data:
                position[field] = data[field]

        neo4j.graph.push(position)
        return success_response(message="阵位更新成功")
    except Exception as e:
        return error_response(message=str(e), code=500)


@dashboard_bp.route('/position/<int:position_id>', methods=['DELETE'])
def delete_position(position_id):
    try:
        # 检查阵位是否存在
        position = neo4j.graph.nodes.match("Position", id=position_id).first()
        if not position:
            return error_response(message='阵位不存在', code=404)

        # 检查是否有任务关联
        task_count = neo4j.graph.run("""
            MATCH (p:Position)<-[:ASSIGNED_TO]-(t:Task)
            WHERE p.id = $position_id
            RETURN count(t) as count
        """, position_id=position_id).evaluate()

        if task_count > 0:
            return error_response(message='该阵位有任务关联，无法删除', code=400)

        # 删除所有关系
        neo4j.graph.run("""
            MATCH (p:Position {id: $position_id})-[r]-()
            DELETE r
        """, position_id=position_id)

        # 删除节点
        neo4j.graph.run("""
            MATCH (p:Position {id: $position_id})
            DELETE p
        """, position_id=position_id)

        return success_response(message="阵位删除成功")
    except Exception as e:
        return error_response(message=str(e), code=500)


@dashboard_bp.route('/position/<int:position_id>/relations', methods=['GET'])
def get_single_position_relations(position_id):
    try:
        # 查询阵位与其他阵位的关系
        query = """
        MATCH (p:Position {id: $position_id})-[r]-(other:Position)
        RETURN p.id as source_id, p.name as source_name,
               other.id as target_id, other.name as target_name,
               type(r) as relation_type
        """
        result = neo4j.graph.run(query, position_id=position_id).data()
        return success_response(result)
    except Exception as e:
        return error_response(message=str(e), code=500)


@dashboard_bp.route('/position/<int:position_id>/taskrelations', methods=['GET'])
def get_single_position_task_relations(position_id):
    try:
        # 查询阵位与任务的关系
        query = """
        MATCH (p:Position {id: $position_id})<-[:ASSIGNED_TO]-(t:Task)
        RETURN t.id as task_id, t.name as task_name
        """
        result = neo4j.graph.run(query, position_id=position_id).data()
        return success_response(result)
    except Exception as e:
        return error_response(message=str(e), code=500)


@dashboard_bp.route('/checkposition', methods=['POST'])
def check_position():
    try:
        data = request.get_json()
        # 验证必要字段
        required_fields = ['x', 'y']
        if not all(field in data for field in required_fields):
            return error_response(message='缺少必要字段', code=400)

        # 检查是否有相同位置的阵位
        query = """
        MATCH (p:Position)
        WHERE p.x = $x AND p.y = $y
        RETURN count(p) as count
        """
        result = neo4j.graph.run(query, x=float(data['x']), y=float(data['y'])).data()
        count = result[0]['count'] if result else 0

        return success_response({"exists": count > 0})
    except Exception as e:
        return error_response(message=str(e), code=500)


@dashboard_bp.route('/checkpositionexc', methods=['POST'])
def check_position_exc():
    try:
        data = request.get_json()
        required_fields = ['x', 'y']
        if not all(field in data for field in required_fields):
            return error_response(message='缺少必要字段', code=400)

        # 构建查询条件
        query_conditions = "p.x = $x AND p.y = $y"
        params = {'x': float(data['x']), 'y': float(data['y'])}

        # 如果有排除ID，添加到条件中
        if 'excludeId' in data:
            query_conditions += " AND p.id <> $excludeId"
            params['excludeId'] = int(data['excludeId'])

        query = f"""
        MATCH (p:Position)
        WHERE {query_conditions}
        RETURN count(p) as count
        """
        result = neo4j.graph.run(query, **params).data()
        count = result[0]['count'] if result else 0

        return success_response({"exists": count > 0})
    except Exception as e:
        return error_response(message=str(e), code=500)


@dashboard_bp.route('/checkrelation', methods=['GET'])
def check_relation():
    try:
        source_id = request.args.get('sourceId', type=int)
        target_id = request.args.get('targetId', type=int)
        rel_type = request.args.get('type', type=str)

        query = """
        MATCH (s:Position {id: $source_id})-[r]-(t:Position {id: $target_id})
        WHERE type(r) = $rel_type
        RETURN count(r) as count
        """
        result = neo4j.graph.run(query, source_id=source_id,
                               target_id=target_id, rel_type=rel_type).data()
        count = result[0]['count'] if result else 0

        return success_response({"exists": count > 0})
    except Exception as e:
        return error_response(message=str(e), code=500)


@dashboard_bp.route('/addrelation', methods=['POST'])
def add_relation():
    try:
        data = request.get_json()
        required_fields = ['sourceId', 'targetId', 'type']
        if not all(field in data for field in required_fields):
            return error_response(message='缺少必要字段', code=400)

        # 获取节点
        source = neo4j.graph.nodes.match("Position", id=int(data['sourceId'])).first()
        target = neo4j.graph.nodes.match("Position", id=int(data['targetId'])).first()

        if not source or not target:
            return error_response(message='源或目标阵位不存在', code=404)

        # 创建关系
        if data['type'] == 'CONNECTION':
            rel = Relationship(source, "CONNECTION", target,
                               strength=float(data.get('strength', 0.5)),
                               distance=float(data.get('distance', 0.0)))
        elif data['type'] == 'INFLUENCE':
            rel = Relationship(source, "INFLUENCE", target,
                               strength=float(data.get('strength', 0.5)))
        else:
            return error_response(message='无效的关系类型', code=400)

        neo4j.graph.create(rel)
        return success_response(message="关系添加成功")
    except Exception as e:
        return error_response(message=str(e), code=500)


@dashboard_bp.route('/deleterelation', methods=['DELETE'])
def delete_relation():
    try:
        data = request.get_json()
        required_fields = ['sourceId', 'targetId', 'type']
        if not all(field in data for field in required_fields):
            return error_response(message='缺少必要字段', code=400)

        # 检查关系是否存在，与方向无关
        query = """
        MATCH (s:Position {id: $source_id})-[r]-(t:Position {id: $target_id})
        WHERE type(r) = $rel_type
        DELETE r
        RETURN count(r) as deleted_count
        """
        result = neo4j.graph.run(query,
                                 source_id=int(data['sourceId']),
                                 target_id=int(data['targetId']),
                                 rel_type=data['type']).data()

        if not result or result[0]['deleted_count'] == 0:
            return error_response(message='关系不存在', code=404)

        return success_response(message="关系删除成功")
    except Exception as e:
        return error_response(message=str(e), code=500)


@dashboard_bp.route('/task/<string:task_id>/unassign/<int:position_id>', methods=['DELETE'])
def unassign_task_from_position(task_id, position_id):
    try:
        # 检查任务和阵位是否存在
        task = neo4j.graph.nodes.match("Task", id=task_id).first()
        position = neo4j.graph.nodes.match("Position", id=position_id).first()

        if not task:
            return error_response(message='任务不存在', code=404)
        if not position:
            return error_response(message='阵位不存在', code=404)

        # 检查任务是否已分配
        if task['status'] != '已分配' or 'current_position' not in task:
            return error_response(message='任务未分配，无需取消', code=400)

        # 检查是否是分配给当前阵位的
        if task['current_position'] != position_id:
            return error_response(message='任务不是分配给此阵位的', code=400)

        # 删除分配关系
        neo4j.graph.run("""
            MATCH (t:Task {id: $task_id})-[r:ASSIGNED_TO]->(p:Position {id: $position_id})
            DELETE r
        """, task_id=task_id, position_id=position_id)

        # 更新阵位的已分配任务数
        position['allocated_tasknum'] -= 1
        neo4j.graph.push(position)

        # 更新任务状态
        task['status'] = '待分配'
        task['current_position'] = None
        task['current_position_name'] = None
        neo4j.graph.push(task)

        return success_response(message="任务取消分配成功")
    except Exception as e:
        return error_response(message=str(e), code=500)