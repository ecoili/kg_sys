from .extensions import neo4j
from .models.sql_user import User
from .models.kg import Airport


# 初始化mysql数据库
def init_db():
    """添加测试用户"""
    # with app.app_context():
    User.init_db()
    print("初始化数据库完成")


# 测试neo4j连接
def check_neo4j_connection():
    """验证 Neo4j 连接   flask check-neo4j """
    try:
        # 执行一个简单查询（如获取Neo4j版本）
        version = neo4j.graph.run("RETURN 1 AS status").data()
        print(" Neo4j 连接成功 | 返回结果:", version)
    except Exception as e:
        print(" Neo4j 连接失败 | 错误:", str(e))


# 初始化知识图谱
def init_kg():
    try:
        Airport.init_kg()
    except Exception as e:
        print("初始化失败！", str(e))

