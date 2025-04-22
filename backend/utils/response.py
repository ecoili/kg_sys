from flask import jsonify


def success_response(data=None, message="Success", code=200):
    return jsonify({
        "success": True,
        "code": code,
        "message": message,
        "data": data
    }), code


def error_response(message="Error", code=400, errors=None):
    return jsonify({
        "success": False,
        "code": code,
        "message": message,
        "errors": errors or []
    }), code