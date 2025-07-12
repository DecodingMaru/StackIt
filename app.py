from flask import Flask
import os
from flask_jwt_extended import JWTManager
from config import Config
from models import init_db
from routes.auth import auth_bp
from routes.questions import questions_bp
from routes.admin import admin_bp
from routes.answers import answer_bp
from flask_cors import CORS
app = Flask(__name__)
CORS(app, supports_credentials=True) 
app.config.from_object(Config)

# JWT Setup
jwt = JWTManager(app)
# Database initialization
init_db()

# Blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(questions_bp, url_prefix='/api/questions')
app.register_blueprint(admin_bp, url_prefix='/api/admin')
app.register_blueprint(answer_bp, url_prefix='/api/answers')

if __name__ == '__main__':
    app.run(debug=True)