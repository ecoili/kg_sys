from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from backend.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "user"
    # 就算已经设置好字段了也需要在这里定义
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(11), unique=True, nullable=False)
    # avatar = db.Column(db.String(500))  # 存储头像URL
    # is_admin = db.Column(db.Boolean, default=False)  # 添加管理员标志
    # 在实际数据库中没有boolean类型，所以用tinyint(1)表示，： True---1，false---0

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @staticmethod
    def init_db():
        if User.query.count() > 0:
            return False
        users = [
            # {'username': 'Alice', 'password': 'qwert123', 'phone': '13800000001', 'is_admin': True},
            {'username': 'Alice', 'password': 'qwert123', 'phone': '13800000001'},
            {'username': 'Bob', 'password': 'asdfg67890', 'phone': '13800000002'},
            {'username': 'Chloe', 'password': 'chloe123', 'phone': '13800000003'},
            {'username': 'Daniel', 'password': 'dan456', 'phone': '13800000004'},
            {'username': 'Ethan', 'password': 'ethan888', 'phone': '13800000005'}
        ]

        for user_data in users:
            user = User(
                username=user_data['username'],
                password='temp',
                phone=user_data['phone'],
                # is_admin=user_data.get('is_admin', False)
            )
            user.set_password(user_data['password'])
            db.session.add(user)

        db.session.commit()

