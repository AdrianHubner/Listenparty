# secret_lists_manager.py
import sqlite3

DATABASE = "tasks.db"  # Gleiche DB wie im Rest deines Projekts

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def add_secret_list(name, color, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO secret_lists (name, color, password)
        VALUES (?, ?, ?)
    """, (name, color, password))
    conn.commit()
    conn.close()

def get_secret_lists():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM secret_lists")
    lists = cursor.fetchall()
    conn.close()
    return [dict(row) for row in lists]

def verify_secret_list(name, password_input):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM secret_lists WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    if row and row["password"]:
        return row["password"] == password_input
    return False
