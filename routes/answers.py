from flask import Blueprint, request,jsonify                            #may need to change if error occurs applicable in whole code
import mysql.connector
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from models import get_db

answer_bp = Blueprint('answer', __name__)

@answer_bp.route('/questions/<int:question_id>/answers', methods=['POST','GET'])
@jwt_required()
def post_answer(question_id):
    if request.method == 'GET':
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM answers WHERE question_id = %s", (question_id,))
        answers = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(answers)
    else:
        current_user = int(get_jwt_identity())
        data = request.json
        body = data.get('body')

        if not body:
            return jsonify({"error": "Answer body required"}), 400

        conn = get_db()
        cursor = conn.cursor()
        try:
            # Check if question exists
            cursor.execute("SELECT id FROM questions WHERE id = %s", (question_id,))
            if not cursor.fetchone():
                return jsonify({"error": "Question not found"}), 404

            # Post answer
            cursor.execute(
                "INSERT INTO answers (body, question_id, user_id) VALUES (%s, %s, (SELECT id FROM users WHERE id = %s))",
                (body, question_id, current_user)
            )
            conn.commit()
            return jsonify({"message": "Answer posted"}), 201
        except mysql.connector.Error as e:
            return jsonify({"error": str(e)}), 400
        finally:
            cursor.close()
            conn.close()

@answer_bp.route('/answers/<int:answer_id>/accept', methods=['POST'])
@jwt_required()
def accept_answer(answer_id):
    current_user = int(get_jwt_identity())
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        # Verify the answer exists and get the question author
        cursor.execute("""
            SELECT q.user_id AS question_author
            FROM answers a
            JOIN questions q ON a.question_id = q.id
            WHERE a.id = %s
        """, (answer_id,))
        result = cursor.fetchone()
        if not result:
            return jsonify({"error": "Answer not found"}), 404

        # Only the question author can accept answers
        if current_user != result['question_author']:
            return jsonify({"error": "Only the question author can accept answers"}), 403

        # Mark answer as accepted
        cursor.execute(
            "UPDATE answers SET is_accepted = TRUE WHERE id = %s",
            (answer_id,)
        )
        conn.commit()
        return jsonify({"message": "Answer accepted"}), 200
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()



@answer_bp.route('/answers/<int:answer_id>/vote', methods=['POST'])
@jwt_required()
def vote_answer(answer_id):
    current_user = int(get_jwt_identity())
    data = request.json
    value = data.get('value')  # +1 or -1

    if value not in (1, -1):
        return jsonify({"error": "Vote value must be +1 or -1"}), 400

    conn = get_db()
    cursor = conn.cursor()
    try:
        # Check if user already voted
        cursor.execute(
            "SELECT id FROM votes WHERE user_id = (SELECT id FROM users WHERE id = %s) AND answer_id = %s",
            (current_user, answer_id)
        )
        if cursor.fetchone():
            return jsonify({"error": "You already voted on this answer"}), 400

        # Record vote
        cursor.execute(
            "INSERT INTO votes (value, user_id, answer_id) VALUES (%s, (SELECT id FROM users WHERE id = %s), %s)",
            (value, current_user, answer_id)
        )
        conn.commit()
        return jsonify({"message": "Vote recorded"}), 201
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@answer_bp.route('/answers/<int:answer_id>', methods=['DELETE'])
@jwt_required()
def delete_answer(answer_id):
    current_user = int(get_jwt_identity())
    conn = get_db()
    cursor = conn.cursor()
    try:
        # Check if answer exists and belongs to the user
        cursor.execute(
            "SELECT user_id FROM answers WHERE id = %s", (answer_id,)
        )
        result = cursor.fetchone()
        if not result or result['user_id'] != current_user:
            return jsonify({"error": "Answer not found or not authorized"}), 403

        # Delete answer
        cursor.execute("DELETE FROM answers WHERE id = %s", (answer_id,))
        conn.commit()
        return jsonify({"message": "Answer deleted"}), 200
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 400
    finally:
        cursor.close()
        conn.close()