import os
# 配置信息
# MYSQL所在的主机名
HOSTNAME = "127.0.0.1"
# MSQL监听的端口号，默认3306
PORT = 3306
# 连接MYSQL的用户名
USERNAME = "root"
# 连接MYSQL的密码
PASSWORD = "123456"
# MYSQL上创建的数据库名称
DATABASE = "kg_sys"
DB_URI = 'mysql+pymysql://{}:{}@{}:{}/{}?charset=utf8mb4'.format(USERNAME, PASSWORD, HOSTNAME
                                                                 , PORT, DATABASE)
SQLALCHEMY_DATABASE_URI = DB_URI
SECRET_KEY = "YSYYRPS"
JWT_SECRET_KEY = "QLGCJ"
# JWT_ACCESS_TOKEN_EXPIRES = time

# Neo4j 配置
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "neo4jpwd")
# NEO4J_DATABASE = "neo4j"  # 默认数据库名（Neo4j 4.0+支持多数据库）我的是3.5.15


# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(BASE_DIR)
# print("根目录为:", BASE_DIR)
# 模型相关配置
MODEL_DIR = os.path.join(BASE_DIR, 'backend', 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'pths', 'rgcn_gat_transformer_multitask.pth')
POSITIONS_FILE = os.path.join(MODEL_DIR, 'data', 'positions.csv')
RELATIONS_FILE = os.path.join(MODEL_DIR, 'data', 'relations.csv')
EVENTS_FILE = os.path.join(MODEL_DIR, 'data', 'synthetic_events.csv')
IMPACT_FILE = os.path.join(MODEL_DIR, 'data', 'synthetic_impact.csv')

# 添加文件上传配置
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'backend', 'static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB限制
