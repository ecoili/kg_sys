from backend.extensions import neo4j
from py2neo import Node, Relationship
import random
from datetime import datetime, timedelta


class Airport:
    @staticmethod
    def init_kg():
        """初始化知识图谱"""
        try:
            # 清空现有数据
            neo4j.graph.run("MATCH (n) DETACH DELETE n")

            # 创建阵位节点
            positions = Airport.create_positions()

            # 创建飞机节点
            airplanes = Airport.create_airplanes()

            # 创建任务节点
            tasks = Airport.create_tasks()

            # 建立阵位之间的连接关系
            Airport.connect_positions(positions)

            # 为飞机分配任务
            Airport.assign_tasks_to_airplanes(airplanes, tasks, positions)

            print("知识图谱初始化完成！")
        except Exception as e:
            print("初始化知识图谱失败:", str(e))
            raise

    @staticmethod
    def create_positions():
        # 16个阵位
        positions = []
        all_functions = [
            "跑道", "乘客上下机", "加油", "供电", "维修",
            "送餐", "清洁", "行李装卸", "检查", "闲置"
        ]

        mandatory_functions = {
            0: ["跑道"],
            1: ["乘客上下机"],
            2: ["加油"],
            3: ["供电", "维修"],
            4: ["维修", "检查"],
            5: ["送餐"],
            6: ["清洁"],
            7: ["行李装卸"],
            8: ["检查", "维修"]
        }

        position_coordinates = [
            (0, 0), (100, 0), (200, 0), (300, 0),
            (0, 100), (100, 100), (200, 100), (300, 100),
            (0, 200), (100, 200), (200, 200), (300, 200),
            (0, 300), (100, 300), (200, 300), (300, 300)
        ]

        for i in range(16):
            # 分配阵位类型，前9个有特定功能，其余随机1-3个功能
            if i in mandatory_functions:
                functions = mandatory_functions[i]
            else:
                num_functions = random.randint(1, 3)
                functions = random.sample(all_functions, num_functions)

            position = Node(
                "Position",
                id=f"P{i + 1}",
                name=f"阵位{i + 1}",
                functions=functions,
                status="空闲",  # 空闲/占用/异常
                x=position_coordinates[i][0],
                y=position_coordinates[i][1],
                capacity=random.randint(1, 3)
            )
            neo4j.graph.create(position)
            positions.append(position)

        return positions

    @staticmethod
    def create_airplanes():
        """创建10架飞机节点"""
        airplanes = []
        airlines = ["中国航空", "东方航空", "南方航空", "海南航空", "国际航空"]
        models = ["A320", "A330", "B737", "B747", "B787", "A380"]

        for i in range(10):
            airplane = Node(
                "Airplane",
                id=f"AP{i + 1}",
                flight_number=f"{random.choice(airlines)}{random.randint(100, 999)}",
                model=random.choice(models),
                status="待命",  # 待命/执行任务/完成
                current_position=None,
                fuel_level=random.randint(20, 100),  # 左闭右闭
                maintenance_status=random.choice(["良好", "需检查", "需维修"])
            )
            neo4j.graph.create(airplane)
            airplanes.append(airplane)

        return airplanes

    @staticmethod
    def create_tasks():
        """创建若干任务节点"""
        tasks = []
        task_types = ["加油", "供电", "维修", "送餐", "清洁", "行李装卸", "检查", "乘客上下机"]

        for i in range(30):  # 创建30个任务
            task = Node(
                "Task",
                id=f"T{i + 1}",
                name=f"任务{i + 1}",
                type=random.choice(task_types),
                duration=random.randint(1, 5),  # 任务持续时间(分钟)
                priority=random.randint(1, 3),  # 优先级 1-3
                status="待分配"  # 待分配/已分配/已完成
            )
            neo4j.graph.create(task)
            tasks.append(task)

        return tasks

    @staticmethod
    def connect_positions(positions):
        """建立阵位之间的连接关系"""
        # 跑道连接到其他阵位
        runway = positions[0]
        for i in range(1, 16):
            rel = Relationship(runway, "CONNECTED_TO", positions[i], distance=random.randint(50, 200))
            neo4j.graph.create(rel)

        # 其他阵位之间的随机连接
        for i in range(1, 16):
            for j in range(i + 1, 16):
                if random.random() < 0.3:  # 30%概率建立连接
                    rel = Relationship(positions[i], "CONNECTED_TO", positions[j],
                                       distance=random.randint(50, 200))
                    neo4j.graph.create(rel)

    @staticmethod
    def assign_tasks_to_airplanes(airplanes, tasks, positions):
        """为飞机分配任务"""
        # 创建集合用{}或set(),空集合必须用set()
        assigned_tasks = set()

        for airplane in airplanes:
            # 随机分配1-3个任务
            num_tasks = random.randint(1, 3)
            airplane_tasks = [t for t in tasks if t["status"] == "待分配" and t["id"] not in assigned_tasks][:num_tasks]

            if not airplane_tasks:
                continue

            # 为飞机选择起始位置
            start_position = random.choice(positions)
            airplane["current_position"] = start_position["id"]
            neo4j.graph.push(airplane)

            # 创建HAS_TASK关系
            for task in airplane_tasks:
                rel = Relationship(airplane, "HAS_TASK", task)
                neo4j.graph.create(rel)
                task["status"] = "已分配"
                neo4j.graph.push(task)
                assigned_tasks.add(task["id"])

                # 为任务分配合适的阵位
                # 列表推导式，符合条件的位置加入列表
                suitable_positions = [
                    p for p in positions
                    if task["type"] in p["functions"]  # 检查功能列表
                       and p["status"] == "空闲"
                ]
                # 合适的列表不为空，从其中随机选取一个位置用于执行任务，创建任务needs position 阵位 关系
                if suitable_positions:
                    task_position = random.choice(suitable_positions)
                    rel = Relationship(task, "NEEDS_POSITION", task_position)
                    neo4j.graph.create(rel)

                    # 更新阵位状态
                    task_position["status"] = "占用"
                    neo4j.graph.push(task_position)

                    # 创建飞机到阵位的路径
                    path = Airport.find_path(start_position, task_position, positions)
                    if path:
                        for i in range(len(path) - 1):
                            rel = Relationship(airplane, "WILL_VISIT", path[i + 1],
                                               order=i + 1,
                                               estimated_time=Airport.calculate_time(path[i], path[i + 1]))
                            neo4j.graph.create(rel)

                # 更新飞机状态
                airplane["status"] = "执行任务"
                neo4j.graph.push(airplane)

    @staticmethod
    def find_path(start, end, positions):
        """简单的路径查找算法"""
        # 这里使用简化的BFS算法查找路径
        if start == end:
            return [start]

        # 构建邻接表--字典
        adj = {p["id"]: [] for p in positions}
        for p in positions:
            query = f"""
                MATCH (p1:Position {{id: '{p["id"]}'}})-[r:CONNECTED_TO]-(p2:Position)
                RETURN p2.id as neighbor
                """
            result = neo4j.graph.run(query).data()
            adj[p["id"]] = [r["neighbor"] for r in result]

        # BFS
        queue = [(start["id"], [start["id"]])]
        visited = set()
        visited.add(start["id"])

        while queue:
            current, path = queue.pop(0)
            if current == end["id"]:
                # 返回完整的Position对象
                return [next(p for p in positions if p["id"] == pid) for pid in path]

            for neighbor in adj[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))

        return None

    @staticmethod
    def calculate_time(p1, p2):
        """计算两个阵位之间的移动时间"""
        dx = p1["x"] - p2["x"]
        dy = p1["y"] - p2["y"]
        distance = (dx**2 + dy**2)**0.5
        return distance / 50  # 假设速度为50单位/分钟

    @staticmethod
    def simulate_emergency(position_id, duration):
        """模拟突发情况"""
        try:
            query = f"""
                MATCH (p:Position {{id: '{position_id}'}})
                SET p.status = '异常', p.emergency_duration = {duration}
                RETURN p
                """
            result = neo4j.graph.run(query).data()

            if result:
                print(f"阵位 {position_id} 设置为异常状态，预计恢复时间: {duration} 分钟")

                # 查找受影响的飞机和任务
                query = f"""
                    MATCH (p:Position {{id: '{position_id}'}})<-[:NEEDS_POSITION]-(t:Task)-[:HAS_TASK]-(a:Airplane)
                    WHERE t.status = '已分配'
                    RETURN a.id as airplane_id, t.id as task_id
                    """
                affected = neo4j.graph.run(query).data()

                for item in affected:
                    # 重新分配任务
                    Airport.reassign_task(item["airplane_id"], item["task_id"])

                return True
            return False
        except Exception as e:
            print("模拟突发情况失败:", str(e))
            return False

    @staticmethod
    def reassign_task(airplane_id, task_id):
        """为任务重新分配阵位（支持阵位多功能）"""
        try:
            # 1. 获取飞机和任务对象
            airplane = neo4j.graph.nodes.match("Airplane", id=airplane_id).first()
            task = neo4j.graph.nodes.match("Task", id=task_id).first()

            if not airplane or not task:
                print(f"错误：飞机 {airplane_id} 或任务 {task_id} 不存在")
                return False

            # 2. 获取当前飞机所在阵位（用于计算新路径）
            current_position = neo4j.graph.nodes.match("Position", id=airplane["current_position"]).first()
            if not current_position:
                print(f"错误：飞机 {airplane_id} 的当前位置无效")
                return False

            # 3. 查找支持任务类型的所有空闲阵位（排除当前阵位）
            required_function = task["type"]
            query = f"""
            MATCH (p:Position)
            WHERE "{required_function}" IN p.functions
            AND p.status = "空闲"
            AND p.id <> "{current_position['id']}"
            RETURN p
            ORDER BY p.capacity DESC  # 优先选择容量大的阵位
            """
            available_positions = neo4j.graph.run(query).data()

            if not available_positions:
                print(f"警告：没有支持 {required_function} 功能的空闲阵位可供任务 {task_id} 使用")
                return False

            # 4. 选择最优阵位（此处简单选择第一个，实际可按距离/容量等优化）
            new_position = available_positions[0]["p"]

            # 5. 更新任务与阵位的关系
            # 5.1 删除旧的关系
            neo4j.graph.run(f"""
            MATCH (t:Task {{id: '{task_id}'}})-[r:NEEDS_POSITION]->()
            DELETE r
            """)

            # 5.2 创建新关系
            rel = Relationship(task, "NEEDS_POSITION", new_position)
            neo4j.graph.create(rel)

            # 6. 更新阵位状态
            new_position["status"] = "占用"
            neo4j.graph.push(new_position)

            # 7. 更新飞机路径
            # 7.1 删除旧路径
            neo4j.graph.run(f"""
            MATCH (a:Airplane {{id: '{airplane_id}'}})-[r:WILL_VISIT]->()
            DELETE r
            """)

            # 7.2 计算新路径（从当前位置到新阵位）
            path = Airport.find_path(current_position, new_position, list(neo4j.graph.nodes.match("Position")))
            if path:
                for i in range(len(path)-1):
                    rel = Relationship(
                        airplane,
                        "WILL_VISIT",
                        path[i+1],
                        order=i+1,
                        estimated_time=Airport.calculate_time(path[i], path[i+1])
                    )
                    neo4j.graph.create(rel)

            print(f"成功：任务 {task_id} 重新分配到阵位 {new_position['id']}（功能：{new_position['functions']}）")
            return True

        except Exception as e:
            # 回滚
            neo4j.graph.rollback()
            print(f"重新分配任务失败：{str(e)}")
            return False
