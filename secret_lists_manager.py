# secret_lists_manager.py
import sqlite3
from flask_login import current_user  # <<< neu
DATABASE = "tasks.db"

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def add_secret_list(name, color, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO secret_lists (name, color, password, user_id)
        VALUES (?, ?, ?, ?)
    """, (name, color, password, current_user.id))  # <<< user_id einfügen
    conn.commit()
    conn.close()

def get_secret_lists():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * 
          FROM secret_lists 
         WHERE user_id = ?
    """, (current_user.id,))  # <<< nur eigene Listen
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def verify_secret_list(name, password_input):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT password 
          FROM secret_lists 
         WHERE name = ? AND user_id = ?
    """, (name, current_user.id))  # <<< filter user_id
    row = cursor.fetchone()
    conn.close()
    if row and row["password"]:
        return row["password"] == password_input
    return False
