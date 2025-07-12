from flask import Blueprint, request, jsonify,redirect, url_for, session
from flask_jwt_extended import create_access_token
from models import get_db,save_user,check_email, verify_password
import requests
from config import Config
from bcrypt import hashpw, gensalt, checkpw
import mysql.connector

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')  # Default to 'user'

    if not email or not password:
        return jsonify({"error": "email and password required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        save_user(email,password,role)
        return jsonify({"message": "User registered"}), 201
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    user = check_email(email)
    print(user)

    if not user or not verify_password(user['password'], password):
        return jsonify({"error": "Invalid credentials"}), 401

    access_token = create_access_token(
        identity=str(user['id']),
        additional_claims={"role": user['role']}
    )
    session['user_id'] = user['id']
    return jsonify({"token": access_token}), 200

@auth_bp.route('/auth/google')
def google_login():
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?response_type=code"
        f"&client_id={Config.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={Config.GOOGLE_REDIRECT_URI}" 
        f"&scope=profile email"
    )
    return redirect(google_auth_url)

@auth_bp.route('/auth/google/callback')
def google_callback():
    code = request.args.get('code')
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        'code': code,
        'client_id': Config.GOOGLE_CLIENT_ID,
        'client_secret': Config.GOOGLE_CLIENT_SECRET,
        'redirect_uri': Config.GOOGLE_REDIRECT_URI,
        'grant_type': 'authorization_code'
    }
    response = requests.post(token_url, data=data)
    token = response.json().get('access_token')
    
    user_info = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers={'Authorization': f'Bearer {token}'})
    user_data = user_info.json()
    
    user = check_email(user_data['email'])
    if not user:
        save_user(user_data['email'], None, 'user', user_data['name'])
        user = check_email(user_data['email'])
    
    access_token = create_access_token(identity=str(user['id']))
    session['user_id'] = user['id']
    return jsonify({"token": access_token}), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({"message": "Logged out"}), 200