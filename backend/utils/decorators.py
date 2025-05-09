from functools import wraps
from flask_jwt_extended import get_jwt_identity
from flask import jsonify
from backend.models.sql_user import User
from .response import success_response, error_response


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user or not user.is_admin:
            # return jsonify({
            #     "success": False,
            #     "message": "需要管理员权限",
            #     "code": 403
            # }), 403
            return error_response(
                message='需要管理员权限',
                code=403
            )
        return fn(*args, **kwargs)
    return wrapper