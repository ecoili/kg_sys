from datetime import timedelta
import logging
from flask import Blueprint, request, jsonify
import re
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from backend.models.sql_user import User
from backend.extensions import db
import datetime, random, string
from ..utils.captcha import CaptchaGenerator

# 创建一个名为auth的蓝图并赋值给auth
auth_bp = Blueprint('auth', __name__)

# 临时存储验证码（生产环境建议用Redis）
captcha_data = {}


@auth_bp.route('/captcha', methods=['GET'])
def get_captcha():
    try:
        captcha_text, image_base64 = CaptchaGenerator.generate_captcha()
        captcha_id = ''.join(random.choices(string.ascii_letters + string.digits, k=16))

        # 存储验证码（5分钟过期）
        captcha_data[captcha_id] = {
            'text': captcha_text.lower(),  # 不区分大小写
            'expire': datetime.datetime.now() + datetime.timedelta(minutes=5)
        }

        return jsonify({
            'captcha_id': captcha_id,
            'image': image_base64
        })
    except Exception as e:
        logging.error(f"生成验证码失败: {str(e)}")
        return jsonify({'message': '生成验证码失败'}), 500


@auth_bp.route('/register', methods=['POST'])
def register():
    # 1. 验证请求数据
    if not request.is_json:
        return jsonify({'message': 'Request must be JSON'}), 400

    data = request.get_json()
    # 注册需要 用户名，手机号，密码
    # 2.判空
    required_fields = ['username', 'phone', 'password']
    # 括号内作用：生成布尔值迭代器  结果举例：(True,True,False)
    # all() 当所有内容为true时才返回True
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    '''
        User.query  创建针对 User 模型的查询对象
        .filter_by(phone=data['phone'])   添加过滤条件：username 字段等于 data['phone'] 相当于 SQL：WHERE phone = ?
        .first()  返回查询结果的第一条记录（User 对象） 如果无匹配则返回 None    
    '''

    if User.query.filter_by(phone=data['phone']).first():
        return jsonify({'message': 'Phone number already exists'}), 400

    # 3. 验证手机号格式
    phone = data['phone'].strip()
    if not re.match(r'^1[3-9]\d{9}$', phone):
        return jsonify({'message': 'Invalid phone number'}), 400

    # 密码长度限制
    if len(data['password']) < 8:
        return jsonify({'message': 'Password too weak (min 8 chars)'}), 400

    user = User(username=data['username'].strip(), phone=phone)
    user.set_password(data['password'])
    db.session.add(user)
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': 'Registration failed'}), 500

    return jsonify({'message': 'User registered successfully'}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    # 判断请求是否为JSON格式
    if not request.is_json:
        return jsonify({'message': 'Request must be JSON'}), 400

    # 获取数据
    data = request.get_json()

    # 判断关键字段是否为空
    required_fields = ['phone', 'password', 'captcha', 'captcha_id']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields'}), 400

    # 验证码校验
    stored_captcha = captcha_data.get(data['captcha_id'])
    if not stored_captcha:
        return jsonify({'message': '验证码已过期，请刷新'}), 400

    if datetime.datetime.now() > stored_captcha['expire']:
        del captcha_data[data['captcha_id']]
        return jsonify({'message': '验证码已过期，请刷新'}), 400

    if data['captcha'].lower() != stored_captcha['text']:
        return jsonify({'message': '验证码错误'}), 400

    # 验证通过后删除验证码
    del captcha_data[data['captcha_id']]

    # 验证用户是否存在
    user = User.query.filter_by(phone=data['phone']).first()
    if not user:
        logging.warning(f"Failed login attempt for phone: {data['phone']}")
        return jsonify({'message': 'Invalid credentials'}), 401  # 模糊提示

    # 验证密码是否正确
    if not user.check_password(data['password']):
        logging.warning(f"Failed password attempt for user: {user.id}")
        return jsonify({'message': 'Invalid credentials'}), 401

    # 设置过期时间
    access_token = create_access_token(
        identity=user.id,
        expires_delta=timedelta(hours=1)
    )

    # 日志
    logging.warning(f"Failed login attempt for phone: {data['phone']}")

    # 安全返回
    return jsonify({
        'access_token': access_token,
        'token_type': 'bearer',
        'expires_in': 3600  # 明确过期时间（秒）1h
    }), 200


@auth_bp.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify(logged_in_as=user.username), 200


# 刷新Token机制
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)  # 要求刷新Token
def refresh():
    current_user = get_jwt_identity()
    new_token = create_access_token(identity=current_user)
    return jsonify(access_token=new_token,
                   token_type='bearer',
                   expires_in=3600
    ), 200
