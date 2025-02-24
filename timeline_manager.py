# timeline_manager.py
import sqlite3
from datetime import datetime

DATABASE = "tasks.db"  # Oder eine eigene DB-Datei, wenn gewünscht

class TimelineManager:
    def __init__(self, db_name=DATABASE):
        self.db_name = db_name
        self._create_tables()

    def get_db_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        # Tabelle für Ziele (Goals)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timeline_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                due_date TEXT  -- z.B. als Ziel-Datum
            )
        """)
        # Tabelle für Meilensteine, die zu einem Ziel gehören
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS milestones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_id INTEGER,
                title TEXT,
                due_date TEXT,
                completed INTEGER DEFAULT 0,
                FOREIGN KEY (goal_id) REFERENCES timeline_goals(id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS timeline_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                start_date TEXT,         -- neu: Startdatum des Ziels
                due_date TEXT,           -- Fälligkeitsdatum
                color TEXT               -- neu: individuelle Farbe, z. B. "#ff5733"
            )
            """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS milestone_tasks (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  milestone_id INTEGER,
                  title TEXT,
                  completed INTEGER DEFAULT 0,
                  FOREIGN KEY (milestone_id) REFERENCES milestones(id)
                );
                """)
        conn.commit()
        conn.close()

    def add_goal(self, title, description, due_date, color="#007bff"):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO timeline_goals (title, description, due_date, color)
            VALUES (?, ?, ?, ?)
        """, (title, description, due_date, color))
        conn.commit()
        conn.close()

    def add_milestone(self, goal_id, title, due_date):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO milestones (goal_id, title, due_date)
            VALUES (?, ?, ?)
        """, (goal_id, title, due_date))
        conn.commit()
        conn.close()

    def get_goals(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM timeline_goals ORDER BY due_date ASC")
        goals = cursor.fetchall()
        conn.close()
        return goals

    def get_milestones_for_goal(self, goal_id):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM milestones WHERE goal_id = ? ORDER BY due_date ASC", (goal_id,))
        milestones = cursor.fetchall()
        conn.close()
        return milestones

    def get_all_timeline_data(self):
        conn = self.get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM timeline_goals ORDER BY due_date ASC")
        goals = cursor.fetchall()

        timeline_data = []

        for goal in goals:
            goal_dict = dict(goal)
            goal_entry = {
                "id": goal_dict["id"],
                "title": goal_dict["title"],
                "description": goal_dict["description"],
                "due_date": goal_dict["due_date"],
                "start_date": goal_dict.get("start_date", "2023-01-01"),
                "color": goal_dict.get("color", "#007bff"),
                "milestones": []
            }

            cursor.execute("SELECT * FROM milestones WHERE goal_id = ? ORDER BY due_date ASC", (goal_dict["id"],))
            milestones = cursor.fetchall()

            for milestone in milestones:
                milestone_dict = dict(milestone)
                # Abrufen der zugehörigen Aufgaben
                cursor.execute("SELECT * FROM milestone_tasks WHERE milestone_id = ? ORDER BY id ASC",
                               (milestone_dict["id"],))
                tasks = cursor.fetchall()
                tasks_list = [dict(task) for task in tasks]

                milestone_entry = {
                    "id": milestone_dict["id"],
                    "title": milestone_dict["title"],
                    "due_date": milestone_dict["due_date"],
                    "progress": 0,  # Hier kannst du den Fortschritt berechnen
                    "percentage": 50,  # Berechnung der relativen Position (Platzhalter)
                    "detail": "",  # Zusätzliche Details
                    "tasks": tasks_list  # Hier werden die Milestone-Tasks eingebettet
                }
                goal_entry["milestones"].append(milestone_entry)

            timeline_data.append(goal_entry)

        conn.close()
        return timeline_data

    def get_promoted_milestone_tasks(self):
        from datetime import datetime, timedelta
        conn = self.get_db_connection()
        cursor = conn.cursor()
        # Berechne das Datum in 30 Tagen
        threshold_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        # Wähle alle Meilensteine aus, deren due_date kleiner oder gleich threshold_date ist
        cursor.execute("SELECT id FROM milestones WHERE due_date <= ?", (threshold_date,))
        milestone_ids = [row["id"] for row in cursor.fetchall()]

        promoted_tasks = []
        for m_id in milestone_ids:
            cursor.execute("SELECT * FROM milestone_tasks WHERE milestone_id = ? ORDER BY id ASC", (m_id,))
            tasks = cursor.fetchall()
            promoted_tasks.extend([dict(task) for task in tasks])

        conn.close()
        return promoted_tasks

    def get_milestones_for_date_range(self, start_date, end_date):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT m.id, m.title, m.due_date, m.completed, g.title AS goal_title
            FROM milestones m
            JOIN timeline_goals g ON m.goal_id = g.id
            WHERE m.due_date BETWEEN ? AND ?
            ORDER BY m.due_date ASC
        """, (start_date, end_date))
        results = cursor.fetchall()
        conn.close()
        return results

    def add_milestone_task(self, milestone_id, title):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO milestone_tasks (milestone_id, title, completed)
            VALUES (?, ?, 0)
        """, (milestone_id, title))
        conn.commit()
        conn.close()

    def get_tasks_for_milestone(self, milestone_id):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM milestone_tasks
            WHERE milestone_id = ?
            ORDER BY id ASC
        """, (milestone_id,))
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def toggle_task_completion(self, task_id, completed):
        conn = self.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE milestone_tasks
            SET completed = ?
            WHERE id = ?
        """, (int(completed), task_id))
        conn.commit()
        conn.close()

    # Weitere Funktionen zum Aktualisieren, Löschen etc. kannst du hier hinzufügen.
