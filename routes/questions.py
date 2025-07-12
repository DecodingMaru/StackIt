from flask import Blueprint, request, jsonify
import mysql.connector
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import get_db

questions_bp = Blueprint('questions', __name__)

@questions_bp.route('/questions', methods=['GET'])
def get_questions():
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(questions)

@questions_bp.route('/questions', methods=['POST'])
@jwt_required()
def post_question():
    current_user = int(get_jwt_identity())
    print(type(current_user))
    data = request.json
    title = data.get('title')
    body = data.get('body')
    tags = data.get('tags')

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO questions (title, body, tags, user_id) VALUES (%s, %s, %s, (SELECT id FROM users WHERE id = %s))",
        (title, body, tags, current_user)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"message": "Question posted"}), 201


@questions_bp.route('/questions/<int:question_id>', methods=['GET'])
def get_question(question_id):
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM questions WHERE id = %s", (question_id,))
    question = cursor.fetchone()
    cursor.close()
    conn.close()

    if not question:
        return jsonify({"error": "Question not found"}), 404

    return jsonify(question)    

@questions_bp.route('/questions/<int:question_id>/vote', methods=['POST'])
@jwt_required()
def vote_question(question_id):
    current_user = int(get_jwt_identity())
    data = request.json
    value = data.get('value')  # +1 (upvote) or -1 (downvote)

    if value not in (1, -1):
        return jsonify({"error": "Vote value must be +1 or -1"}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        # Check if user already voted
        cursor.execute(
            "SELECT id FROM votes WHERE user_id = (SELECT id FROM users WHERE id = %s) AND question_id = %s",
            (current_user, question_id)
        )
        if cursor.fetchone():
            return jsonify({"error": "You already voted on this question"}), 400

        # Record vote
        cursor.execute(
            "INSERT INTO votes (value, user_id, question_id) VALUES (%s, (SELECT id FROM users WHERE id = %s), %s)",
            (value, current_user, question_id)
        )
        conn.commit()
        return jsonify({"message": "Vote recorded"}), 201
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@questions_bp.route('/questions/<int:question_id>', methods=['DELETE'])
@jwt_required()
def delete_question(question_id):
    current_user = int(get_jwt_identity())
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Check if question exists and belongs to the user
        cursor.execute(
            "SELECT user_id FROM questions WHERE id = %s", (question_id,)
        )
        result = cursor.fetchone()
        if not result or result['user_id'] != current_user:
            return jsonify({"error": "Question not found or not authorized"}), 403

        # Delete question
        cursor.execute("DELETE FROM questions WHERE id = %s", (question_id,))
        conn.commit()
        return jsonify({"message": "Question deleted"}), 200
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

