# File: list_manager.py

import sqlite3
from datetime import datetime, timedelta, date
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from flask_login import current_user



def select_list(manager):
    """
    Ermöglicht die Auswahl eines Listennamens mit Autovervollständigung.
    """
    # Lade alle vorhandenen Listennamen aus der Datenbank
    all_lists = manager.get_all_lists()
    if not all_lists:
        print("No lists found. Please create a new list first.")
        return None

    # Erstelle einen Autovervollständiger mit allen Listennamen
    list_completer = WordCompleter(all_lists, ignore_case=True)

    # Benutzer gibt eine Liste ein, Autovervollständigung zeigt Vorschläge
    list_name = prompt("Enter list name: ", completer=list_completer)
    return list_name


def select_task(manager, list_name):
    """
    Ermöglicht die Auswahl eines Tasks mit Autovervollständigung.
    """
    tasks = manager.get_tasks(list_name)
    if not tasks:
        print("No tasks found in this list.")
        return None

    # Erstelle einen Autovervollständiger mit allen Task-Titeln
    task_titles = [task[1] for task in tasks]  # Extrahiere die Titel der Tasks
    task_completer = WordCompleter(task_titles, ignore_case=True)

    # Benutzer gibt eine Task ein, Autovervollständigung zeigt Vorschläge
    task_title = prompt("Enter task name: ", completer=task_completer)

    # Finde die Task mit dem ausgewählten Titel
    for task in tasks:
        if task[1].lower() == task_title.lower():
            return task
    print("Task not found.")
    return None







# Task class to represent each task
class Task:
    def __init__(self, title, description=None, due_date=None, difficulty=None, tags=None, completed=False):
        """
        Repräsentiert eine Aufgabe (Task).

        :param title: Der Titel der Aufgabe (Pflichtfeld).
        :param description: Eine optionale Beschreibung der Aufgabe.
        :param due_date: Das optionale Fälligkeitsdatum (im Format YYYY-MM-DD).
        :param difficulty: Die optionale Schwierigkeit der Aufgabe (z. B. "leicht", "mittel", "schwer").
        :param tags: Eine optionale Liste von Schlagwörtern (Tags) für die Aufgabe.
        :param completed: Ob die Aufgabe abgeschlossen ist (bool).
        """
        self.title = title  # Titel der Aufgabe
        self.description = description or ""  # Standardwert: leerer String
        self.due_date = due_date  # Kann leer bleiben
        self.difficulty = difficulty  # Kann leer bleiben
        self.tags = tags or []  # Standardwert: leere Liste
        self.completed = completed  # Standardwert: False (nicht abgeschlossen)

    def __repr__(self):
        """
        Liefert eine stringbasierte Darstellung der Aufgabe für Debugging oder Übersicht.
        """
        return (f"Task(title='{self.title}', description='{self.description}', due_date='{self.due_date}', "
                f"difficulty='{self.difficulty}', tags={self.tags}, completed={self.completed})")

# ListManager class to handle lists and tasks
class ListManager:
    def __init__(self, db_name="tasks.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def get_db_connection(self):
        """
        Returns a connection to the SQLite database.
        """
        connection = sqlite3.connect("tasks.db")
        connection.row_factory = sqlite3.Row  # Optional: Access rows like dictionaries
        return connection

    def get_list_color(self, list_name):
        """
        Fetches the color associated with a list name.
        """
        connection = self.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT color FROM tasks WHERE list_name = ? LIMIT 1", (list_name,))
        row = cursor.fetchone()
        connection.close()
        return row[0] if row else "#ffffff"  # Default color if none exists

    def update_list_color(self, list_name, color):
        """
        Updates the color for all tasks in a given list name.
        """
        connection = self.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE tasks
            SET color = ?
            WHERE list_name = ?
        """, (color, list_name))
        connection.commit()
        connection.close()

    def _create_tables(self):
        # Create tasks table if not exists
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_name TEXT,
            title TEXT,
            description TEXT,
            due_date TEXT,
            completed INTEGER
        )
        """)
        self.conn.commit()

    def add_task(self, list_name, title, description="", due_date=None, estimated_time=0):
        """
        Add a new task to the database, tagged with dem aktuellen User.
        """
        connection = self.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
               INSERT INTO tasks
                 (list_name, title, description, due_date, estimated_time, completed, user_id)
               VALUES (?, ?, ?, ?, ?, ?, ?)
           """, (
            list_name,
            title,
            description,
            due_date,
            estimated_time,
            0,
            current_user.id
        ))
        connection.commit()
        connection.close()

    def get_tasks(self, list_name):
        """
        Fetches tasks for eine Liste und den aktuellen User, gruppiert nach Status.
        """
        connection = self.get_db_connection()
        cursor = connection.cursor()

        # Unvollständige
        cursor.execute("""
               SELECT id, title, description, due_date, completed
               FROM tasks
               WHERE list_name = ? AND completed = 0 AND user_id = ?
               ORDER BY id DESC
           """, (list_name, current_user.id))
        incomplete_tasks = cursor.fetchall()

        # Abgeschlossene
        cursor.execute("""
               SELECT id, title, description, due_date, completed
               FROM tasks
               WHERE list_name = ? AND completed = 1 AND user_id = ?
           """, (list_name, current_user.id))
        completed_tasks = cursor.fetchall()

        connection.close()
        return {
            "incomplete": incomplete_tasks,
            "completed": completed_tasks
        }

    def update_task(self, task_id, title=None, description=None, due_date=None, completed=None):
        """
        Aktualisiert einen Task, nur wenn er dem aktuell eingeloggten User gehört.
        """
        updates = []
        params = []

        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        if due_date is not None:
            updates.append("due_date = ?")
            params.append(due_date)
        if completed is not None:
            updates.append("completed = ?")
            params.append(int(completed))

        # Baue das UPDATE-Statement – schließe user_id des aktuellen Users mit ein
        query = (
                "UPDATE tasks SET "
                + ", ".join(updates)
                + " WHERE id = ? AND user_id = ?"
        )
        params.append(task_id)
        params.append(current_user.id)

        # Führe das Update über eine neue DB-Verbindung aus
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        conn.close()

    def update_task_order(self, new_order):
        connection = self.get_db_connection()
        cursor = connection.cursor()

        for index, task_id in enumerate(new_order):
            cursor.execute(
                "UPDATE tasks SET position = ? WHERE id = ? AND user_id = ?",
                (index, task_id, current_user.id)
            )

        connection.commit()
        connection.close()

    def add_recurring_task(self, title, frequency, start_date, interval_value=1):
        """
        Add a new recurring task for the current user.
        """
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO recurring_tasks
                (title, frequency, start_date, interval_value, user_id)
            VALUES (?, ?, ?, ?, ?)
        """, (
            title,
            frequency,
            start_date,
            interval_value,
            current_user.id
        ))
        conn.commit()
        conn.close()

    def should_run_task_addition(self, task_name):
        """
        Überprüft, ob eine bestimmte Aufgabe heute bereits hinzugefügt wurde.
        Falls nicht, speichert sie das Datum der letzten Ausführung in der Datenbank.
        Dieser Check bleibt global, erfasst also nicht User-spezifisch.
        """
        connection = self.get_db_connection()
        cursor = connection.cursor()

        today = date.today().isoformat()

        cursor.execute("""
            SELECT last_run FROM last_execution WHERE task = ?
        """, (task_name,))
        last_run = cursor.fetchone()

        if last_run and last_run[0] == today:
            connection.close()
            return False

        cursor.execute("""
            INSERT INTO last_execution (task, last_run)
            VALUES (?, ?)
            ON CONFLICT(task) DO UPDATE SET last_run = excluded.last_run
        """, (task_name, today))

        connection.commit()
        connection.close()
        return True

    def add_recurring_tasks_to_special_lists(self):
        """
        Fügt wiederkehrende Aufgaben des aktuellen Users den Spezial‑Listen hinzu.
        """
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)

        conn = self.get_db_connection()
        cur = conn.cursor()

        # tägliche recurring_tasks nur des current_user einfügen
        cur.execute("""
            INSERT INTO tasks (title, list_name, due_date, completed, user_id)
            SELECT title, 'Today', ?, 0, ?
            FROM recurring_tasks
            WHERE frequency = 'daily' AND user_id = ?
              AND NOT EXISTS (
                SELECT 1 FROM tasks
                WHERE title = recurring_tasks.title
                  AND due_date = ?
                  AND user_id = ?
              )
        """, (today.isoformat(),
              current_user.id,
              current_user.id,
              today.isoformat(),
              current_user.id))

        # tomorrow
        tomorrow = (today + timedelta(days=1)).isoformat()
        cur.execute("""
            INSERT INTO tasks (title, list_name, due_date, completed, user_id)
            SELECT title, 'Next Day', ?, 0, ?
            FROM recurring_tasks
            WHERE frequency = 'daily' AND user_id = ?
              AND NOT EXISTS (
                SELECT 1 FROM tasks
                WHERE title = recurring_tasks.title
                  AND due_date = ?
                  AND user_id = ?
              )
        """, (tomorrow,
              current_user.id,
              current_user.id,
              tomorrow,
              current_user.id))

        # montags wöchentliche
        if today == week_start:
            cur.execute("""
                INSERT INTO tasks (title, list_name, due_date, completed, user_id)
                SELECT title, 'This Week', ?, 0, ?
                FROM recurring_tasks
                WHERE frequency = 'weekly' AND user_id = ?
                  AND NOT EXISTS (
                    SELECT 1 FROM tasks
                    WHERE title = recurring_tasks.title
                      AND due_date = ?
                      AND user_id = ?
                  )
            """, (week_start.isoformat(),
                  current_user.id,
                  current_user.id,
                  week_start.isoformat(),
                  current_user.id))

        # am Monatsanfang monatliche
        if today == month_start:
            cur.execute("""
                INSERT INTO tasks (title, list_name, due_date, completed, user_id)
                SELECT title, 'This Month', ?, 0, ?
                FROM recurring_tasks
                WHERE frequency = 'monthly' AND user_id = ?
                  AND NOT EXISTS (
                    SELECT 1 FROM tasks
                    WHERE title = recurring_tasks.title
                      AND due_date = ?
                      AND user_id = ?
                  )
            """, (month_start.isoformat(),
                  current_user.id,
                  current_user.id,
                  month_start.isoformat(),
                  current_user.id))

        conn.commit()
        conn.close()

    def get_all_lists(self):
        """
        Liefert alle (öffentlichen) Listen‑Namen des aktuellen Users,
        exklusive Spezial‑ und Secret-Listen.
        """
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT list_name
            FROM tasks
            WHERE archived = 0
              AND user_id = ?
              AND list_name NOT IN ('Today','Next Day','This Week','This Month')
              AND LOWER(list_name) NOT IN (
                  SELECT LOWER(name)
                  FROM secret_lists
                  WHERE user_id = ?
              )
        """, (current_user.id, current_user.id))
        rows = cur.fetchall()
        conn.close()
        return [r[0] for r in rows]

    def add_calendar_task(self, title, date, category):
        """
        Fügt eine Kalender‑Aufgabe für den aktuellen User hinzu.
        """
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO calendar_tasks (title, date, category, user_id)
            VALUES (?, ?, ?, ?)
        """, (title, date, category, current_user.id))
        conn.commit()
        conn.close()

    def archive_list(self, list_name):
        """
        Archiviere eine Liste nur für den aktuellen User.
        """
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE tasks
            SET archived = 1
            WHERE list_name = ? AND user_id = ?
        """, (list_name, current_user.id))
        conn.commit()
        conn.close()

    def restore_list(self, list_name):
        """
        Hebt archived=0 nur für die Tasks des aktuellen Users auf.
        """
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE tasks
            SET archived = 0
            WHERE list_name = ? AND user_id = ?
        """, (list_name, current_user.id))
        conn.commit()
        conn.close()

    def get_archived_lists(self):
        """
        Listet alle archivierten Listennamen des aktuellen Users.
        """
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT DISTINCT list_name
            FROM tasks
            WHERE archived = 1
              AND user_id = ?
        """, (current_user.id,))
        rows = cur.fetchall()
        conn.close()
        return [r[0] for r in rows]

    def task_exists_in_calendar(self, title, date, category):
        """
        Prüft nur im Kalender des aktuellen Users.
        """
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT 1
            FROM calendar_tasks
            WHERE title = ?
              AND date = ?
              AND category = ?
              AND user_id = ?
        """, (title, date, category, current_user.id))
        exists = cur.fetchone() is not None
        conn.close()
        return exists

    def get_calendar_tasks(self, year, month):
        """
        Holt Kalender‑Aufgaben nur des aktuellen Users.
        """
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, date, category
            FROM calendar_tasks
            WHERE strftime('%Y', date) = ?
              AND strftime('%m', date) = ?
              AND user_id = ?
        """, (str(year), f"{month:02d}", current_user.id))
        tasks = cur.fetchall()
        colnames = tuple(c[0] for c in cur.description)
        conn.close()
        return tasks, colnames

    # Aufgaben aus dem Kalender → in Today/Next Day verschieben
    def move_calendar_tasks_to_special_lists(self):
        """
        Verschiebt nur die calendar_tasks des aktuellen Users in Today/Next Day.
        """
        if not self.should_run_task_addition("calendar_tasks_added"):
            print("📌 Calendar tasks already added today. Skipping…")
            return

        today = date.today().isoformat()
        tomorrow = (date.today() + timedelta(days=1)).isoformat()

        conn = self.get_db_connection()
        cur = conn.cursor()

        # Heute
        cur.execute("""
            INSERT INTO tasks (title, description, list_name, due_date, completed, user_id)
            SELECT title, '', 'Today', date, 0, user_id
            FROM calendar_tasks
            WHERE date = ?
              AND user_id = ?
              AND NOT EXISTS (
                SELECT 1 FROM tasks
                WHERE title = calendar_tasks.title
                  AND due_date = ?
                  AND user_id = ?
              )
        """, (today, current_user.id, today, current_user.id))

        # Morgen
        cur.execute("""
            INSERT INTO tasks (title, description, list_name, due_date, completed, user_id)
            SELECT title, '', 'Next Day', date, 0, user_id
            FROM calendar_tasks
            WHERE date = ?
              AND user_id = ?
              AND NOT EXISTS (
                SELECT 1 FROM tasks
                WHERE title = calendar_tasks.title
                  AND due_date = ?
                  AND user_id = ?
              )
        """, (tomorrow, current_user.id, tomorrow, current_user.id))

        conn.commit()
        conn.close()

    def get_calendar_tasks_with_recurring(self, year, month, include_recurring=False):
        """
        Holt recurring calendar_tasks nur des aktuellen Users.
        """
        conn = self.get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT title, date, category
            FROM calendar_tasks
            WHERE strftime('%Y', date) = ?
              AND strftime('%m', date) = ?
              AND user_id = ?
        """, (str(year), f"{month:02d}", current_user.id))
        tasks = cur.fetchall()

        if include_recurring:
            cur.execute("""
                SELECT title, frequency, interval_value, start_date
                FROM recurring_tasks
                WHERE user_id = ?
            """, (current_user.id,))
            recurring = cur.fetchall()

            import datetime
            end_of_month = (datetime.date(year, month, 1) + datetime.timedelta(days=31)).replace(
                day=1) - datetime.timedelta(days=1)

            for title, freq, interval, start in recurring:
                start = start or f"{year}-{month:02d}-01"
                d0 = datetime.datetime.strptime(start, "%Y-%m-%d").date()

                if freq == "daily":
                    while d0 <= end_of_month:
                        tasks.append((title, d0.isoformat(), "recurring-daily"))
                        d0 += datetime.timedelta(days=interval or 1)

                elif freq == "weekly":
                    while d0 <= end_of_month:
                        tasks.append((title, d0.isoformat(), "recurring-weekly"))
                        d0 += datetime.timedelta(weeks=interval or 1)

                elif freq == "monthly":
                    while d0 <= end_of_month:
                        tasks.append((title, d0.isoformat(), "recurring-monthly"))
                        d0 = (d0.replace(day=1) + datetime.timedelta(days=31)).replace(day=1)

        conn.close()
        return tasks

    def get_tasks_for_date_range(self, start_date, end_date, completed=None, exclude_lists=None,
                                 exclude_date_range=None):
        """
        Sucht nur in tasks des aktuellen Users.
        """
        conn = self.get_db_connection()
        cur = conn.cursor()

        query = """
            SELECT id, title, description, due_date, completed, list_name
            FROM tasks
            WHERE due_date BETWEEN ? AND ?
              AND user_id = ?
        """
        params = [start_date, end_date, current_user.id]

        if completed is not None:
            query += " AND completed = ?"
            params.append(int(completed))

        if exclude_lists:
            ph = ", ".join("?" * len(exclude_lists))
            query += f" AND list_name NOT IN ({ph})"
            params += exclude_lists

        if exclude_date_range:
            query += " AND NOT (due_date BETWEEN ? AND ?)"
            params += [exclude_date_range[0], exclude_date_range[1]]

        query += " ORDER BY due_date ASC"
        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        return rows

    def get_next_day_tasks(self):
        """
        Holt alle Aufgaben für morgen für den aktuellen User.
        """
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        return self.get_tasks_for_date_range(tomorrow, tomorrow)

    def get_week_tasks(self):
        """
        Holt alle Aufgaben der 'This Week'-Liste für den aktuellen User.
        """
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, description, due_date, completed
            FROM tasks
            WHERE list_name = 'This Week'
              AND user_id = ?
        """, (current_user.id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    def get_month_tasks(self):
        """
        Holt alle Aufgaben der 'This Month'-Liste für den aktuellen User.
        """
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, description, due_date, completed
            FROM tasks
            WHERE list_name = 'This Month'
              AND user_id = ?
        """, (current_user.id,))
        rows = cur.fetchall()
        conn.close()
        return rows

    def toggle_task_completion(self, task_id, completed):
        """
        Markiert eine Aufgabe als (un)vollständig – nur für den aktuellen User.
        """
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE tasks
            SET completed = ?
            WHERE id = ? AND user_id = ?
        """, (int(completed), task_id, current_user.id))
        conn.commit()
        conn.close()

    def delete_task(self, task_id):
        """
        Löscht eine Aufgabe – nur wenn sie zum aktuellen User gehört.
        """
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            DELETE FROM tasks
            WHERE id = ? AND user_id = ?
        """, (task_id, current_user.id))
        conn.commit()
        conn.close()

    def move_task(self, task_id, new_list):
        """
        Verschiebt eine Aufgabe in eine andere Liste – nur für den aktuellen User.
        """
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE tasks
            SET list_name = ?
            WHERE id = ? AND user_id = ?
        """, (new_list, task_id, current_user.id))
        conn.commit()
        conn.close()

    def rename_task(self, task_id, new_name):
        """
        Ändert den Titel einer Aufgabe – nur für den aktuellen User.
        """
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE tasks
            SET title = ?
            WHERE id = ? AND user_id = ?
        """, (new_name, task_id, current_user.id))
        conn.commit()
        conn.close()

    def update_task_date(self, task_id, new_date):
        """
        Ändert das Datum einer Kalender-Aufgabe – nur für den aktuellen User.
        """
        conn = self.get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE calendar_tasks
            SET date = ?
            WHERE id = ? AND user_id = ?
        """, (new_date, task_id, current_user.id))
        conn.commit()
        conn.close()

    def close(self):
        self.conn.close()


# CLI Interface for interacting with the ListManager
def main():
    print("Welcome to the List Manager!")
    manager = ListManager()

    while True:
        print("\nOptions:")
        print("1. Add a task")
        print("2. View tasks")
        print("3. Update a task")
        print("4. Delete a task")
        print("5. Quit")

        choice = input("Choose an option: ")

        if choice == "1":
            list_name = input("Enter list name: ")
            title = input("Enter task title: ")
            description = input("Enter task description (optional): ")
            due_date = input("Enter due date (YYYY-MM-DD, optional): ")
            if due_date:
                try:
                    due_date = datetime.strptime(due_date, "%Y-%m-%d").date().isoformat()
                except ValueError:
                    print("Invalid date format!")
                    continue
            else:
                due_date = None

            task = Task(title, description, due_date)
            manager.add_task(list_name, task)
            print("Task added!")



        elif choice == "2":  # Option: Aufgaben einer Liste anzeigen

            # Autovervollständigung für Listennamen

            list_name = select_list(manager)  # Benutzer wählt eine Liste aus

            if list_name:  # Nur fortfahren, wenn eine Liste gewählt wurde

                tasks = manager.get_tasks(list_name)

                if tasks:

                    for t in tasks:
                        print(f"[{'✔' if t[4] else ' '}] {t[1]} (ID: {t[0]}) - {t[2]} Due: {t[3]}")

                else:

                    print("No tasks found!")



        elif choice == "3":
            task_id = input("Enter task ID to update: ")
            print("Leave fields empty to keep current values.")
            title = input("New title (optional): ")
            description = input("New description (optional): ")
            due_date = input("New due date (YYYY-MM-DD, optional): ")
            completed = input("Mark as completed? (yes/no, optional): ")

            if completed.lower() in ("yes", "y"):
                completed = True
            elif completed.lower() in ("no", "n"):
                completed = False
            else:
                completed = None

            manager.update_task(task_id, title, description, due_date, completed)
            print("Task updated!")

        elif choice == "4":
            task_id = input("Enter task ID to delete: ")
            manager.delete_task(task_id)
            print("Task deleted!")

        elif choice == "5":
            manager.close()
            print("Goodbye!")
            break

        else:
            print("Invalid option, try again.")

if __name__ == "__main__":
    main()
