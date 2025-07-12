import mysql.connector
from mysql.connector import Error
from bcrypt import hashpw, gensalt, checkpw
from config import Config

def get_db():
    try:
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB
        )
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id int auto_increment PRIMARY KEY,
        email varchar(50) UNIQUE not null,
        password varchar(255) not null,
        role ENUM('user', 'admin') DEFAULT 'user'
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS questions (
        id int auto_increment PRIMARY KEY,
        title varchar(200) not null,
        body TEXT not null,
        tags varchar(100),
        user_id INT not null,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS answers (
        id int auto_increment PRIMARY KEY,
        body TEXT not null,
        question_id int not null,
        user_id int not null,
        is_accepted BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (question_id) REFERENCES questions(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS votes (
        id int auto_increment PRIMARY KEY,
        value int not null, 
        user_id int not null,
        question_id int,
        answer_id int,
        FOREIGN KEY (user_id) REFERENCES users(id),
        FOREIGN KEY (question_id) REFERENCES questions(id),
        FOREIGN KEY (answer_id) REFERENCES answers(id)
    )
    """)
    #  1 for upvote, -1 for downvote

    conn.commit()
    cursor.close()
    conn.close()

def verify_password(stored_password, provided_password):
    return checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

def save_user(email, password, role):
    db = get_db()
    cursor = db.cursor()
    hashed_pw = hashpw(password.encode('utf-8'), gensalt()) if password else None
    cursor.execute(
            "INSERT INTO users (email, password, role) VALUES (%s, %s, %s)",
            (email, hashed_pw, role)
        )
    db.commit()
    cursor.close()
    db.close()

def check_email(email):
    db =get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
    user = cursor.fetchone()
    cursor.close()
    db.close()
    return user