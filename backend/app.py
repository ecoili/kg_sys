from flask import Flask
from backend.extensions import db, migrate, cors, bcrypt, jwt, login_manager, neo4j
from backend import config
from sqlalchemy import text
# from backend.models.sql_user import User
from backend.routes.auth import auth_bp
from backend.routes.dashboard import board_bp
from backend.routes.emerg_be import emergency_bp
from . import commands
app = Flask(__name__)

# 导入配置
app.config.from_object(config)
# 初始化扩展
db.init_app(app)
neo4j.init_app(app)
migrate.init_app(app, db)
cors.init_app(app)
bcrypt.init_app(app)
jwt.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# 注册蓝图
# 所有auth_bp的路由自动添加前缀/auth
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(board_bp)
app.register_blueprint(emergency_bp)

# 命令行操作
def register_commands(app):
    """注册所有命令行命令"""
    # 只注册，函数名后面不能加括号
    # MySQL数据库命令
    app.cli.command("init-db")(commands.init_db)

    # Neo4j命令
    app.cli.command("check-neo4j")(commands.check_neo4j_connection)

    # 创建知识图谱
    app.cli.command("init-kg")(commands.init_kg)

    # 创建知识图谱2
    app.cli.command("init-kg2")(commands.init_kg2)


# 运行注册命令
register_commands(app)

# 测试连接
with app.app_context():
    with db.engine.connect() as conn:
        rs = conn.execute(text("select 1"))
        print(rs.fetchone())
        print("mysql数据库连接成功！")

if __name__ == '__main__':
    app.run()
