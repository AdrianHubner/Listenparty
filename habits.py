# habits.py
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import sqlite3

habits_bp = Blueprint('habits', __name__, template_folder='templates')

DATABASE = "tasks.db"  # Du kannst dieselbe DB verwenden oder eine separate


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_date TEXT UNIQUE,
            alcohol INTEGER DEFAULT 0,
            smoke INTEGER DEFAULT 0,
            sport INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()


# Initialisiere die Tabelle, falls noch nicht vorhanden
init_db()


@habits_bp.route("/")
def show_habits():
    from datetime import datetime, timedelta
    conn = get_db_connection()
    cursor = conn.cursor()

    # Ermittele das letzte Datum, für das ein Eintrag existiert
    cursor.execute("SELECT MAX(habit_date) as last_date FROM daily_habits")
    row = cursor.fetchone()
    last_date_str = row["last_date"] if row["last_date"] else None

    today = datetime.now().date()
    # Falls noch kein Eintrag existiert, setzen wir last_date auf gestern,
    # damit mindestens für heute ein Eintrag erstellt wird.
    if last_date_str:
        last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
    else:
        last_date = today - timedelta(days=1)

    # Berechne, wie viele Tage seit dem letzten Eintrag vergangen sind
    missing_days = (today - last_date).days
    if missing_days > 0:
        # Für jeden fehlenden Tag einen Eintrag erstellen
        for i in range(1, missing_days + 1):
            day = last_date + timedelta(days=i)
            try:
                cursor.execute("""
                    INSERT INTO daily_habits (habit_date, alcohol, smoke, sport)
                    VALUES (?, 0, 0, 0)
                """, (day.strftime("%Y-%m-%d"),))
            except sqlite3.IntegrityError:
                # Falls für den Tag bereits ein Eintrag existiert, ignoriere
                pass
        conn.commit()

    # Jetzt alle Einträge abrufen
    cursor.execute("SELECT * FROM daily_habits ORDER BY habit_date ASC")
    habits = cursor.fetchall()
    conn.close()
    return render_template("habits.html", habits=habits)



@habits_bp.route("/update_habit", methods=["POST"])
def update_habit():
    """
    Nimmt einen POST-Request entgegen, um die Gewohnheitseinträge für einen bestimmten Tag zu aktualisieren.
    Erwartet Felder: habit_date, alcohol, smoke, sport.
    """
    habit_date = request.form.get("habit_date")
    alcohol = int(request.form.get("alcohol", 0))
    smoke = int(request.form.get("smoke", 0))
    sport = int(request.form.get("sport", 0))

    conn = get_db_connection()
    cursor = conn.cursor()
    # Versuche, einen bestehenden Eintrag zu aktualisieren. Falls keiner existiert, erstelle einen neuen.
    cursor.execute("SELECT id FROM daily_habits WHERE habit_date = ?", (habit_date,))
    row = cursor.fetchone()
    if row:
        cursor.execute("""
            UPDATE daily_habits
            SET alcohol = ?, smoke = ?, sport = ?
            WHERE habit_date = ?
        """, (alcohol, smoke, sport, habit_date))
    else:
        cursor.execute("""
            INSERT INTO daily_habits (habit_date, alcohol, smoke, sport)
            VALUES (?, ?, ?, ?)
        """, (habit_date, alcohol, smoke, sport))
    conn.commit()
    conn.close()
    return redirect(url_for("habits.show_habits"))


# Optional: API-Endpunkt, um die Gewohnheiten als JSON abzurufen (z.B. für eine dynamische Kalenderansicht)
@habits_bp.route("/api/habits")
def api_habits():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM daily_habits ORDER BY habit_date ASC")
    habits = cursor.fetchall()
    conn.close()
    habits_list = [dict(row) for row in habits]
    return jsonify(habits_list)

