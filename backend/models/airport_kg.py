from datetime import datetime, timedelta
import pandas as pd
from py2neo import Graph, Node, Relationship
from backend.extensions import neo4j
import random
from tqdm import tqdm
from backend import config


# 读取数据文件
positions_df = pd.read_csv(config.POSITIONS_FILE, encoding='utf-8')
relations_df = pd.read_csv(config.RELATIONS_FILE, encoding='utf-8')
events_df = pd.read_csv(config.EVENTS_FILE, encoding='utf-8')
pos_name = {1: '跑道',
            2: '加油站',
            3: '供电站',
            4: '维修点',
            5: '测试点',
            6: '行李装卸点',
            7: '送餐点',
            8: '清洁点',
            9: '停靠点'}

# 数据清洗
# # 1. 处理缺失值
# positions.fillna('UNKNOWN', inplace=True)
# relations.fillna(0, inplace=True)  # 根据实际情况处理
# events.fillna('UNKNOWN', inplace=True)
#
# # 2. 标准化字段名
# positions.columns = ['id', 'attr1', 'attr2', 'attr3', 'attr4', 'attr5', 'attr6', 'attr7']
# relations.columns = ['source_id', 'target_id', 'relation_type', 'strength1', 'strength2']
# events.columns = ['event_id', 'position_id', 'event_type', 'severity', 'start_time', 'duration']


class Airport2:
    @staticmethod
    def init_kg2():
        try:
            # 1. 首先测试数据库连接
            try:
                neo4j.graph.run("RETURN 1")  # 简单查询测试连接
                print("Neo4j 连接成功")
            except Exception as e:
                print(f"Neo4j 连接失败: {str(e)}")
                raise

            # 2. 清空现有数据（不使用事务块）
            print("开始清空现有数据...")
            neo4j.graph.run("MATCH (n) DETACH DELETE n")
            print("成功清空现有数据")

            # 3. 创建节点和关系（不使用事务块）
            print("开始创建阵位节点...")
            Airport2.create_positions()
            print("成功创建阵位节点")

            print("开始创建任务节点...")
            tasks = Airport2.create_tasks()
            print(f"成功创建{len(tasks)}个任务节点")

            print("开始创建阵位关系...")
            Airport2.create_position_relations()
            print("成功创建阵位关系")

            print("开始分配任务...")
            Airport2.assign_tasks_to_positions(tasks)
            print("成功分配任务")

            print("知识图谱初始化完成！")
        except Exception as e:
            print(f"初始化知识图谱失败: {str(e)}")
            import traceback
            traceback.print_exc()  # 打印完整的错误堆栈
            raise

    @staticmethod
    def create_positions():
        # 创建计数器字典
        position_counters = {pos_type: 1 for pos_type in pos_name.values()}
        # 创建阵位节点
        # 目前节点没有设置name属性(Neo4j默认用来显示节点名称的属性)，没有设置的话就不会显示节点名称
        # 后面定义一个字典存放阵位类型和名称的关系
        positions = []
        for _, row in positions_df.iterrows():
            pos_type = pos_name[row['position_type']]
            # 生成带编号的name
            name = f"{pos_type}{position_counters[pos_type]}"
            position_counters[pos_type] += 1
            position = Node("Position",
                            # 明确id为int类型
                            id=int(row['position_id']),
                            name=name,
                            x=row['x_coord'],
                            y=row['y_coord'],
                            type=pos_name[row['position_type']],
                            type_identity=row['type_identifier'],
                            impt_lv=row['importance_level'],
                            flr_rate=row['failure_rate'],
                            sup_num=row['supported_aircraft_count'],
                            allocated_tasknum=0  # 初始化为0
                            )
            neo4j.graph.create(position)
            positions.append(position)
        # return positions

    @staticmethod
    def create_airplanes():
        pass

    @staticmethod
    def create_tasks():
        """创建带约束的任务节点（不涉及资源）"""
        tasks = []
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
        # 创建任务计数器
        task_counters = {task_type: 1 for task_type in task_types.keys()}

        # for i in range(45): 增加任务数量
        for i in range(100):
            task_type = random.choice(list(task_types.keys()))
            task_name = f"{task_type}{task_counters[task_type]}"
            task_counters[task_type] += 1
            task = Node(
                "Task",
                id=f"T{i + 1}",
                name=task_name,
                type=task_type,
                # duration=random.randint(1, 5),
                # priority=random.randint(1, 3),
                duration=random.randint(1, 10),
                priority=random.randint(1, 5),
                status="待分配",
                # 新增约束属性（不涉及资源）
                required_position_types=task_types[task_type],
                deadline=(datetime.now() + timedelta(hours=2)).isoformat()

            )
            neo4j.graph.create(task)
            tasks.append(task)
        return tasks

    @staticmethod
    def create_position_relations():
        """创建阵位间的关系"""
        print("正在创建阵位间关系...")

        # 创建关系
        for _, row in tqdm(relations_df.iterrows(), total=len(relations_df)):
            source_id = row['source_id']
            target_id = row['target_id']
            relation_type = row['relation_type']

            if pd.isna(source_id) or pd.isna(target_id) or pd.isna(relation_type):
                continue

            # 查找源节点和目标节点
            source_node = neo4j.graph.nodes.match("Position", id=int(source_id)).first()
            target_node = neo4j.graph.nodes.match("Position", id=int(target_id)).first()

            if not source_node or not target_node:
                continue

            # 根据关系类型创建不同关系
            if relation_type.lower() == "connection":
                relation = Relationship(
                    source_node,
                    "CONNECTION",
                    target_node,
                    strength=float(row['relation_strength']) if row['relation_strength'] else 0.0,
                    distance=float(row['physical_distance']) if row['physical_distance'] else 0.0
                )
            elif relation_type.lower() == "influence":
                relation = Relationship(
                    source_node,
                    "INFLUENCE",
                    target_node,
                    strength=float(row['relation_strength']) if row['relation_strength'] else 0.0
                )
            else:
                continue

            neo4j.graph.create(relation)

    @staticmethod
    def assign_tasks_to_positions(tasks):
        """基于阵位类型匹配的任务分配（使用type_identity属性匹配）"""
        # 目前一个阵位可分配多个任务
        for task in tasks:
            # 获取任务要求的阵位类型（中文名）
            required_names = task['required_position_types']

            # 查询匹配的阵位（使用name属性匹配）
            query = (
                "MATCH (p:Position) "
                "WHERE p.type IN $types "  # 使用type属性匹配中文名
                "RETURN p"
            )
            suitable_positions = list(neo4j.graph.run(query, types=required_names))

            if suitable_positions:
                selected = random.choice(suitable_positions)
                position_node = selected[0]

                # # 获取当前阵位上的任务数
                # current_count = neo4j.graph.run("""
                #                     MATCH (p:Position)<-[:ASSIGNED_TO]-(t:Task)
                #                     WHERE p.id = $pos_id
                #                     RETURN count(t) as count
                #                     """, pos_id=position_node["id"]).evaluate()
                #
                # if current_count >= position_node["sup_num"]:
                #     continue  # 跳过已满的阵位

                # 检查阵位是否已满
                if position_node["allocated_tasknum"] >= position_node["sup_num"]:
                    continue  # 跳过已满的阵位

                # 添加关系
                rel = Relationship(task, "ASSIGNED_TO", position_node,
                                   assigned_time=datetime.now().isoformat())
                neo4j.graph.create(rel)

                # 更新阵位的已分配任务数
                position_node["allocated_tasknum"] += 1
                neo4j.graph.push(position_node)

                # 同时添加current_position属性（存储position_id）
                task["current_position"] = position_node["id"]
                task["current_position_name"] = position_node["name"]
                task["required_resources"] = []
                task["status"] = "已分配"
                neo4j.graph.push(task)


