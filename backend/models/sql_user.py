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

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @staticmethod
    def init_db():
        if User.query.count() > 0:
            return False
        users = [
            {'username': 'Alice', 'password': 'qwert123'},
            {'username': 'Bob', 'password': 'asdfg67890'},
            {'username': 'Chloe', 'password': 'chloe123'},
            {'username': 'Daniel', 'password': 'dan456'},
            {'username': 'Ethan', 'password': 'ethan888'}
        ]

        for user_data in users:
            user = User(
                username=user_data['username'],
                password='temp'
            )
            user.set_password(user_data['password'])
            db.session.add(user)

        db.session.commit()

