from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from models import get_db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    claims = get_jwt()
    if claims['role'] != 'admin':
        return jsonify({"error": "Admin only"}), 403

    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, email, role FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(users)