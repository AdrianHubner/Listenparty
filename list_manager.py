# File: list_manager.py

import sqlite3
from datetime import datetime, timedelta, date
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

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
        Add a new task to the database.
        """
        connection = self.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO tasks (list_name, title, description, due_date, estimated_time, completed)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (list_name, title, description, due_date, estimated_time, 0))
        connection.commit()
        connection.close()

    def get_tasks(self, list_name):
        """
        Fetches tasks for a given list name, grouped by completion status.
        """
        connection = self.get_db_connection()
        cursor = connection.cursor()

        # Fetch incomplete tasks
        cursor.execute("""
            SELECT id, title, description, due_date, completed
            FROM tasks
            WHERE list_name = ? AND completed = 0
            ORDER BY id DESC  -- Sortiere nach ID in absteigender Reihenfolge
        """, (list_name,))
        incomplete_tasks = cursor.fetchall()

        # Fetch completed tasks
        cursor.execute("""
            SELECT id, title, description, due_date, completed
            FROM tasks
            WHERE list_name = ? AND completed = 1
        """, (list_name,))
        completed_tasks = cursor.fetchall()

        connection.close()
        return {
            "incomplete": incomplete_tasks,
            "completed": completed_tasks
        }

    def update_task(self, task_id, title=None, description=None, due_date=None, completed=None):
        query = "UPDATE tasks SET "
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

        query += ", ".join(updates) + " WHERE id = ?"
        params.append(task_id)
        self.cursor.execute(query, params)
        self.conn.commit()

    def update_task_order(self, new_order):
        connection = self.get_db_connection()
        cursor = connection.cursor()

        for index, task_id in enumerate(new_order):
            cursor.execute(
                "UPDATE tasks SET position = ? WHERE id = ?",
                (index, task_id)
            )

        connection.commit()
        connection.close()

    def add_recurring_task(self, title, frequency, start_date, interval_value=1):
        connection = self.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO recurring_tasks (title, frequency, start_date, interval_value)
            VALUES (?, ?, ?, ?)
        """, (title, frequency, start_date, interval_value))

        connection.commit()
        connection.close()

    def should_run_task_addition(self, task_name):
        """
        Überprüft, ob eine bestimmte Aufgabe heute bereits hinzugefügt wurde.
        Falls nicht, speichert sie das Datum der letzten Ausführung in der Datenbank.
        """
        connection = self.get_db_connection()
        cursor = connection.cursor()

        today = date.today().isoformat()

        # Prüfen, ob diese Aufgabe heute bereits ausgeführt wurde
        cursor.execute("""
            SELECT last_run FROM last_execution WHERE task = ?
        """, (task_name,))
        last_run = cursor.fetchone()

        if last_run and last_run[0] == today:
            connection.close()
            return False  # Die Aufgabe wurde heute schon ausgeführt, nicht erneut ausführen

        # Falls noch nicht ausgeführt, speichere das aktuelle Datum als "zuletzt ausgeführt"
        cursor.execute("""
            INSERT INTO last_execution (task, last_run)
            VALUES (?, ?) ON CONFLICT(task) DO UPDATE SET last_run = excluded.last_run
        """, (task_name, today))

        connection.commit()
        connection.close()
        return True  # Die Aufgabe kann jetzt ausgeführt werden

    def add_recurring_tasks_to_special_lists(self):
        """
        Fügt wiederkehrende Aufgaben den richtigen Listen hinzu:
        - 'daily' → Today
        - 'weekly' → This Week (jeden Montag)
        - 'monthly' → This Month (jeden Monatsersten)
        - Individuelle Intervalle für Tage, Wochen, Monate
        """


        today = date.today()
        week_start = today - timedelta(days=today.weekday())  # Start der Woche (Montag)
        month_start = today.replace(day=1)  # Start des Monats

        connection = self.get_db_connection()
        cursor = connection.cursor()

        # **Tägliche Aufgaben → Today (Verhindert doppelte Einträge)**
        cursor.execute("""
            INSERT INTO tasks (title, list_name, due_date, completed)
            SELECT title, 'Today', ?, 0 FROM recurring_tasks
            WHERE frequency = 'daily'
            AND NOT EXISTS (SELECT 1 FROM tasks WHERE title = recurring_tasks.title AND due_date = ?)
        """, (today.isoformat(), today.isoformat()))

        # **Benutzerdefinierte tägliche Intervalle**
        cursor.execute("""
            INSERT INTO tasks (title, list_name, due_date, completed)
            SELECT title, 'Today', ?, 0 FROM recurring_tasks
            WHERE frequency = 'custom_days' AND interval_value IS NOT NULL
            AND (julianday(?) - julianday(start_date)) % interval_value = 0
            AND NOT EXISTS (SELECT 1 FROM tasks WHERE title = recurring_tasks.title AND due_date = ?)
        """, (today.isoformat(), today.isoformat(), today.isoformat()))

        tomorrow = date.today() + timedelta(days=1)
        cursor.execute("""
            INSERT INTO tasks (title, list_name, due_date, completed)
            SELECT title, 'Next Day', ?, 0 FROM recurring_tasks
            WHERE frequency = 'daily'
            AND NOT EXISTS (SELECT 1 FROM tasks WHERE title = recurring_tasks.title AND due_date = ?)
        """, (tomorrow.isoformat(), tomorrow.isoformat()))

        # **Wöchentliche Aufgaben → This Week (Nur Montags)**
        if today == week_start:
            cursor.execute("""
                INSERT INTO tasks (title, list_name, due_date, completed)
                SELECT title, 'This Week', ?, 0 FROM recurring_tasks
                WHERE frequency = 'weekly'
                AND NOT EXISTS (SELECT 1 FROM tasks WHERE title = recurring_tasks.title AND due_date = ?)
            """, (week_start.isoformat(), week_start.isoformat()))

            # **Benutzerdefinierte wöchentliche Intervalle**
            cursor.execute("""
                INSERT INTO tasks (title, list_name, due_date, completed)
                SELECT title, 'This Week', ?, 0 FROM recurring_tasks
                WHERE frequency = 'custom_weeks' AND interval_value IS NOT NULL
                AND ((julianday(?) - julianday(start_date)) / 7) % interval_value = 0
                AND NOT EXISTS (SELECT 1 FROM tasks WHERE title = recurring_tasks.title AND due_date = ?)
            """, (week_start.isoformat(), week_start.isoformat(), week_start.isoformat()))

        # **Monatliche Aufgaben → This Month (Nur am 1. des Monats)**
        if today == month_start:
            cursor.execute("""
                INSERT INTO tasks (title, list_name, due_date, completed)
                SELECT title, 'This Month', ?, 0 FROM recurring_tasks
                WHERE frequency = 'monthly'
                AND NOT EXISTS (SELECT 1 FROM tasks WHERE title = recurring_tasks.title AND due_date = ?)
            """, (month_start.isoformat(), month_start.isoformat()))

            # **Benutzerdefinierte monatliche Intervalle**
            cursor.execute("""
                INSERT INTO tasks (title, list_name, due_date, completed)
                SELECT title, 'This Month', ?, 0 FROM recurring_tasks
                WHERE frequency = 'custom_months' AND interval_value IS NOT NULL
                AND (strftime('%m', ?) - strftime('%m', start_date)) % interval_value = 0
                AND NOT EXISTS (SELECT 1 FROM tasks WHERE title = recurring_tasks.title AND due_date = ?)
            """, (month_start.isoformat(), month_start.isoformat(), month_start.isoformat()))

        connection.commit()
        connection.close()

    def get_all_lists(self):
        connection = self.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT list_name FROM tasks WHERE archived = 0")
        rows = cursor.fetchall()
        connection.close()
        return [row[0] for row in rows]

    def add_calendar_task(self, title, date, category):
        connection = self.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO calendar_tasks (title, date, category)
            VALUES (?, ?, ?)
        """, (title, date, category))
        connection.commit()
        connection.close()

    def archive_list(self, list_name):
        connection = self.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE tasks SET archived = 1 WHERE list_name = ?", (list_name,))
        connection.commit()
        connection.close()

    def restore_list(self, list_name):
        connection = self.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE tasks SET archived = 0 WHERE list_name = ?", (list_name,))
        connection.commit()
        connection.close()

    def get_archived_lists(self):
        connection = self.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT list_name FROM tasks WHERE archived = 1")
        rows = cursor.fetchall()
        connection.close()
        return [row[0] for row in rows]

    def task_exists_in_calendar(self, title, date, category):
        connection = self.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT 1 FROM calendar_tasks WHERE title = ? AND date = ? AND category = ?
        """, (title, date, category))
        exists = cursor.fetchone() is not None
        connection.close()
        return exists

    def get_calendar_tasks(self, year, month):
        connection = self.get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, title, date, category
            FROM calendar_tasks
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
        """, (str(year), f"{month:02d}"))

        tasks = cursor.fetchall()
        column_names = tuple(column[0] for column in cursor.description)  # Stelle sicher, dass es ein Tupel ist!

        connection.close()
        return tasks, column_names


    # Aufgaben aus dem Kalender → in Today/Next Day verschieben
    def move_calendar_tasks_to_special_lists(self):
        """
        Holt Aufgaben aus dem Kalender und verschiebt sie in die richtige Spezialliste.
        - Heute fällige Aufgaben → Today
        - Morgen fällige Aufgaben → Next Day
        """

        if not self.should_run_task_addition("calendar_tasks_added"):
            print("📌 Calendar tasks already added today. Skipping...")
            return

        today = date.today()
        tomorrow = today + timedelta(days=1)

        connection = self.get_db_connection()
        cursor = connection.cursor()

        # **Heute fällige Aufgaben → Today (Verhindert doppelte Einträge)**
        cursor.execute("""
            INSERT INTO tasks (title, description, list_name, due_date, completed)
            SELECT title, '', 'Today', date, 0 FROM calendar_tasks
            WHERE date = ?
            AND NOT EXISTS (SELECT 1 FROM tasks WHERE title = calendar_tasks.title AND due_date = ?)
        """, (today.isoformat(), today.isoformat()))

        # **Morgen fällige Aufgaben → Next Day (Verhindert doppelte Einträge)**
        cursor.execute("""
            INSERT INTO tasks (title, description, list_name, due_date, completed)
            SELECT title, '', 'Next Day', date, 0 FROM calendar_tasks
            WHERE date = ?
            AND NOT EXISTS (SELECT 1 FROM tasks WHERE title = calendar_tasks.title AND due_date = ?)
        """, (tomorrow.isoformat(), tomorrow.isoformat()))

        connection.commit()
        connection.close()

    def get_calendar_tasks_with_recurring(self, year, month, include_recurring=False):
        connection = self.get_db_connection()
        cursor = connection.cursor()

        # Normale Kalenderaufgaben
        cursor.execute("""
            SELECT title, date, category
            FROM calendar_tasks
            WHERE strftime('%Y', date) = ? AND strftime('%m', date) = ?
        """, (str(year), f"{month:02d}"))
        tasks = cursor.fetchall()

        # Optionale Einbindung wiederkehrender Aufgaben
        if include_recurring:
            cursor.execute("""
                SELECT title, frequency, interval_value, start_date
                FROM recurring_tasks
            """)
            recurring_tasks = cursor.fetchall()

            import datetime
            for title, frequency, interval_value, start_date in recurring_tasks:
                if not start_date:  # Standardmäßig auf den Monatsbeginn setzen, falls kein Startdatum angegeben ist
                    start_date = f"{year}-{month:02d}-01"

                start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
                days_in_month = (datetime.date(year, month, 1) + datetime.timedelta(days=31)).replace(
                    day=1) - datetime.timedelta(days=1)

                if frequency == "daily":
                    current_date = start_date
                    while current_date <= days_in_month:
                        tasks.append((title, current_date.isoformat(), "recurring-daily"))
                        current_date += datetime.timedelta(days=interval_value or 1)


                elif frequency == "weekly":

                    current_date = start_date

                    while current_date <= days_in_month:
                        tasks.append((title, current_date.isoformat(), "recurring-weekly"))

                        current_date += datetime.timedelta(weeks=interval_value or 1)


                elif frequency == "monthly":

                    current_date = start_date

                    while current_date <= days_in_month:
                        tasks.append((title, current_date.isoformat(), "recurring-monthly"))

                        current_date += datetime.timedelta(days=(interval_value or 1) * 30)

        connection.close()
        return tasks

    def get_tasks_for_date_range(self, start_date, end_date, completed=None, exclude_lists=None,
                                 exclude_date_range=None):
        connection = self.get_db_connection()
        cursor = connection.cursor()

        query = """
            SELECT id, title, description, due_date, completed, list_name
            FROM tasks
            WHERE due_date BETWEEN ? AND ?
        """
        params = [start_date, end_date]

        if completed is not None:
            query += " AND completed = ?"
            params.append(int(completed))

        if exclude_lists:
            placeholders = ", ".join(["?"] * len(exclude_lists))
            query += f" AND list_name NOT IN ({placeholders})"
            params.extend(exclude_lists)

        if exclude_date_range:
            # exclude_date_range sollte ein Tupel (ex_start, ex_end) sein
            query += " AND NOT (due_date BETWEEN ? AND ?)"
            params.extend([exclude_date_range[0], exclude_date_range[1]])

        query += " ORDER BY due_date ASC"
        cursor.execute(query, params)
        tasks = cursor.fetchall()
        connection.close()
        return tasks

    def get_next_day_tasks(self):
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        return self.get_tasks_for_date_range(tomorrow, tomorrow)

    def get_week_tasks(self):
        """Holt alle Aufgaben, die explizit für 'This Week' hinzugefügt wurden."""
        connection = self.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, title, description, due_date, completed
            FROM tasks
            WHERE list_name = 'This Week'
        """)
        tasks = cursor.fetchall()
        connection.close()
        return tasks

    def get_month_tasks(self):
        """Holt alle Aufgaben, die explizit für 'This Month' hinzugefügt wurden."""
        connection = self.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            SELECT id, title, description, due_date, completed
            FROM tasks
            WHERE list_name = 'This Month'
        """)
        tasks = cursor.fetchall()
        connection.close()
        return tasks

    def toggle_task_completion(self, task_id, completed):
        """
        Updates the completion status of a task.
        """
        connection = self.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE tasks
            SET completed = ?
            WHERE id = ?
        """, (int(completed), task_id))
        connection.commit()
        connection.close()

    def delete_task(self, task_id):
        connection = self.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        connection.commit()
        connection.close()

    def move_task(self, task_id, new_list):
        connection = self.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE tasks SET list_name = ? WHERE id = ?", (new_list, task_id))
        connection.commit()
        connection.close()

    def rename_task(self, task_id, new_name):
        connection = self.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("UPDATE tasks SET title = ? WHERE id = ?", (new_name, task_id))
        connection.commit()
        connection.close()

    def update_task_date(self, task_id, new_date):
        connection = self.get_db_connection()
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE calendar_tasks
            SET date = ?
            WHERE id = ?
        """, (new_date, task_id))
        connection.commit()
        connection.close()

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
