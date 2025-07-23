# user_model.py
import sqlite3
from flask_login import UserMixin

DATABASE = "tasks.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

class User(UserMixin):
    def __init__(self, id_, username, password_hash):
        self.id = id_
        self.username = username
        self.password_hash = password_hash

    @staticmethod
    def get(user_id):
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            "SELECT id, username, password_hash FROM users WHERE id = ?",
            (user_id,)
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return User(row["id"], row["username"], row["password_hash"])

    @staticmethod
    def find_by_username(username):
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,)
        )
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return User(row["id"], row["username"], row["password_hash"])
