from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_login import LoginManager
from py2neo import Graph
from flask import current_app
from jwt import InvalidTokenError
# 创建对象
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
bcrypt = Bcrypt()
jwt = JWTManager()
login_manager = LoginManager()


class Neo4jGraph:
    def __init__(self, app=None):
        self.graph = None
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.graph = Graph(
            app.config['NEO4J_URI'],
            auth=app.config['NEO4J_AUTH'],
            # name=app.config.get('NEO4J_DATABASE', 'neo4j') neo4j v4+
        )


# 创建全局实例
neo4j = Neo4jGraph()
