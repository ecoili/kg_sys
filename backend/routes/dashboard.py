from flask_jwt_extended import jwt_required, get_jwt_identity
from flask import Blueprint, jsonify

board_bp = Blueprint('dashboard', __name__)


@board_bp.route('/dashboard', methods=['GET'])
@jwt_required()  # 要求认证
def dashboard():
    pass
