from datetime import datetime

from flask import request, Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
import os

from werkzeug.utils import secure_filename

from backend import config
from backend.extensions import db
from backend.models.sql_user import User
from backend.routes.auth import auth_bp
from backend.utils.response import error_response, success_response


userinfo_bp = Blueprint('userinfo_bp', __name__)


@userinfo_bp.route('/get-userinfo', methods=['GET'])
@jwt_required()
def get_userinfo():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return error_response('用户不存在', 404)

        return success_response({
            'username': user.username,
            'phone': user.phone
        })
    except Exception as e:
        return error_response(str(e), 500)


@userinfo_bp.route('/update-username', methods=['PUT'])
@jwt_required()
def update_username():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return error_response('用户不存在', 404)

        data = request.get_json()
        if not data or 'username' not in data:
            return error_response('缺少用户名参数', 400)

        new_username = data['username'].strip()
        if not new_username or len(new_username) < 2:
            return error_response('用户名不合法', 400)

        # 检查用户名是否已存在
        existing_user = User.query.filter(
            User.username == new_username,
            User.id != current_user_id
        ).first()
        if existing_user:
            return error_response('用户名已存在', 400)

        user.username = new_username
        db.session.commit()

        return success_response({
            'message': '用户名更新成功',
            'username': new_username
        })
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 500)


@userinfo_bp.route('/update-password', methods=['PUT'])
@jwt_required()
def update_password():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        if not user:
            return error_response('用户不存在', 404)

        data = request.get_json()
        if not data or 'currentPassword' not in data or 'newPassword' not in data:
            return error_response('缺少必要参数', 400)

        # 验证当前密码
        if not user.check_password(data['currentPassword']):
            return error_response('当前密码不正确', 400)

        # 验证新密码
        new_password = data['newPassword']
        if len(new_password) < 8:
            return error_response('新密码至少需要8位', 400)

        # 更新密码
        user.set_password(new_password)
        db.session.commit()

        return success_response({
            'message': '密码更新成功'
        })
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 500)


@userinfo_bp.route('/get-avatar', methods=['GET'])
@jwt_required()
def get_avatar():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return error_response('用户不存在', 404)
    return success_response({
        'avatar': user.avatar or '/static/default-avatar.png'  # 默认头像URL
    })


@userinfo_bp.route('/update-avatar', methods=['POST'])
@jwt_required()
def update_avatar():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    if not user:
        return error_response('用户不存在', 404)

    data = request.get_json()
    if not data or 'avatar' not in data:
        return error_response('缺少头像URL参数', 400)

    try:
        user.avatar = data['avatar']  # 直接存储URL
        db.session.commit()
        return success_response({
            'message': '头像更新成功',
            'avatar': user.avatar
        })
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 500)


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@userinfo_bp.route('/upload-avatar', methods=['POST'])
@jwt_required()
def upload_file():
    if 'file' not in request.files:
        return error_response('No file part', 400)

    file = request.files['file']
    if file.filename == '':
        return error_response('No selected file', 400)

    if file and allowed_file(file.filename):
        # 生成唯一文件名
        filename = secure_filename(file.filename)
        unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"

        # 保存到上传目录
        upload_folder = config['UPLOAD_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)

        # 返回访问URL
        file_url = f"/static/uploads/{unique_filename}"
        return success_response({
            'url': file_url,
            'filename': unique_filename
        })

    return error_response('File type not allowed', 400)
