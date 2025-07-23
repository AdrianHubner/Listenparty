from flask import Flask, render_template, request, redirect, url_for, jsonify

from flask import Flask
from flask_wtf.csrf import CSRFProtect
import sqlite3

from list_manager import ListManager, Task
from utils import get_daily_video
from datetime import date, timedelta

from calendar import monthcalendar
import datetime

from auth import auth_bp
from flask_login import LoginManager, login_required

import os
import random
from user_model import User  # <— von hier holen wir User

app = Flask(__name__)

# Secret Key – in Produktion über Umgebungsvariable setzen!
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev‐fallback‐key')  # Session‑Cookie hart machen
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,   # kein JS-Zugriff
    SESSION_COOKIE_SAMESITE="Lax",  # Schutz gegen CSRF
    # SESSION_COOKIE_SECURE=True     # nur über HTTPS aktivieren!
)

app.config["SESSION_COOKIE_SECURE"] = True
app.config["REMEMBER_COOKIE_SECURE"] = True  # falls du Flask‑Login nutzt


# CSRF global aktivieren
csrf = CSRFProtect(app)


# 1) LoginManager hier erzeugen
login_manager = LoginManager()
login_manager.login_view = "auth.login"  # Dein Login‑Endpunkt
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    # verwende User.get
    return User.get(int(user_id))


# … hier restliches Setup: register_blueprint(auth_bp), ListManager, Routes, etc. …
from auth import auth_bp
app.register_blueprint(auth_bp, url_prefix="/auth")

# Datei für die Sprüche und den Fortschritt
QUOTES_FILE = "quotes.txt"
PROGRESS_FILE = "progress.txt"

manager = ListManager()  # Instafrom flask import Flask, render_template, request, redirect, url_for, jsonify

from flask import Flask
from flask_wtf.csrf import CSRFProtect

from list_manager import ListManager, Task
from utils import get_daily_video
from datetime import date, timedelta

from calendar import monthcalendar
import datetime

from auth import auth_bp

import os
import random


from timeline import timeline_bp

app.register_blueprint(timeline_bp, url_prefix="/timeline")

from timeline_manager import TimelineManager
timeline_manager = TimelineManager()

from habits import habits_bp
app.register_blueprint(habits_bp, url_prefix="/habits")

from secret_lists import secret_bp
app.register_blueprint(secret_bp, url_prefix="/secret")




def get_random_quote():
    # Sprüche laden
    if not os.path.exists(QUOTES_FILE):
        return "No quotes available."

    with open(QUOTES_FILE, "r") as file:
        quotes = file.readlines()

    # Fortschritt laden: Liste der bereits gezeigten Indizes
    shown_indices = []
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as file:
            shown_indices = [int(x) for x in file.read().strip().split(",") if x]

    # Falls alle Sprüche gezeigt wurden, zurücksetzen
    if len(shown_indices) == len(quotes):
        shown_indices = []

    # Einen zufälligen, noch nicht gezeigten Spruch auswählen
    available_indices = list(set(range(len(quotes))) - set(shown_indices))
    next_index = random.choice(available_indices)

    # Fortschritt speichern
    shown_indices.append(next_index)
    with open(PROGRESS_FILE, "w") as file:
        file.write(",".join(map(str, shown_indices)))

    return quotes[next_index].strip()


@app.route("/daily_quote", methods=["GET"])
@login_required
def daily_quote():
    """
    Liefert einen zufälligen Motivationsspruch, ohne Wiederholung.
    """
    quote = get_random_quote()
    return quote



@app.route("/add_task/<list_name>", methods=["POST"])
@login_required
def add_task(list_name):
    """
    Add a new task to the specified list.
    """
    # Get form data
    title = request.form.get("title")
    description = request.form.get("description", "")
    due_date = request.form.get("due_date", None)

    print(f"Adding task '{title}' to list '{list_name}'")  # Debugging

    # Add the task using the ListManager
    manager.add_task(list_name, title, description, due_date)

    # Redirect back to the homepage
    return redirect(url_for("index"))


@app.route("/add_list", methods=["POST"])
@login_required
def add_list():
    """
    Create a new list by adding a dummy task with the list name.
    """
    list_name = request.form.get("list_name")
    if list_name:
        # Add a dummy task to initialize the list
        manager.add_task(list_name, "Default Task", "This is your first task!", None)
    return redirect(url_for("index"))



@app.route("/add_task_to_today", methods=["POST"])
@login_required
def add_task_to_today():
    """
    Fügt eine Aufgabe zur "Heute"-Liste hinzu.
    """
    # Formulardaten auslesen
    title = request.form.get("title")
    description = request.form.get("description", "")
    estimated_time = request.form.get("estimated_time")  # Wert als String auslesen
    due_date = date.today().isoformat()  # Heute als Datum

    # Überprüfen, ob eine Zeit angegeben wurde, falls nicht, Standardwert setzen
    if estimated_time:
        estimated_time = int(estimated_time)  # In Integer umwandeln, falls angegeben
    else:
        estimated_time = None  # Kein Wert gesetzt

    # Aufgabe zur "Heute"-Liste hinzufügen
    manager.add_task("Today", title, description, due_date, estimated_time)

    return redirect(url_for("index"))



# Route für die 'Next Day' Liste
@app.route("/add_task_to_next_day", methods=["POST"])
@login_required
def add_task_to_next_day():
    title = request.form.get("title")
    description = request.form.get("description", "")
    estimated_time = int(request.form.get("estimated_time", 0))
    due_date = (date.today() + timedelta(days=1)).isoformat()  # Morgen als Datum

    manager.add_task("Next Day", title, description, due_date, estimated_time)
    return redirect(url_for("index"))

# Route für die 'This Week' Liste
@app.route("/add_task_to_this_week", methods=["POST"])
@login_required
def add_task_to_this_week():
    title = request.form.get("title")
    description = request.form.get("description", "")
    estimated_time = int(request.form.get("estimated_time", 0))
    today = date.today()
    # Berechne den Wochenstart (Montag) und Wochenende (Sonntag)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    # Setze das Fälligkeitsdatum auf das Ende der Woche
    due_date = week_end.isoformat()

    manager.add_task("This Week", title, description, due_date, estimated_time)
    return redirect(url_for("index"))


# Route für die 'This Month' Liste
@app.route("/add_task_to_this_month", methods=["POST"])
@login_required
def add_task_to_this_month():
    title = request.form.get("title")
    description = request.form.get("description", "")
    estimated_time = int(request.form.get("estimated_time", 0))
    due_date = (date.today().replace(day=1) + timedelta(days=31)).replace(day=1).isoformat()  # Erster Tag des nächsten Monats

    manager.add_task("This Month", title, description, due_date, estimated_time)
    return redirect(url_for("index"))

@app.route("/archive_list/<list_name>", methods=["POST"])
@login_required
def archive_list(list_name):
    manager.archive_list(list_name)
    return redirect(url_for("index"))


@app.route("/restore_list/<list_name>", methods=["POST"])
@login_required
def restore_list(list_name):
    manager.restore_list(list_name)
    return redirect(url_for("index"))

@app.route("/archived_lists")
@login_required
def archived_lists():
    archived = manager.get_archived_lists()  # Muss alle archivierten Listennamen zurückgeben
    archived_lists_with_data = [
        {
            "name": list_name,
            "color": manager.get_list_color(list_name),
            "tasks": manager.get_tasks(list_name)
        }
        for list_name in archived
    ]
    return render_template("archive.html", archived_lists=archived_lists_with_data)


@app.route("/view_list/<list_name>")
@login_required
def view_list(list_name):
    tasks = manager.get_tasks(list_name)
    return render_template("view_lists.html", list_name=list_name, tasks=tasks)




@app.route("/")
@login_required
def index():
    """
    Fetches all lists, including special lists (Today, Next Day, This Week, and This Month).
    Jetzt werden zusätzlich auch die Milestones aus der Timeline in den jeweiligen Datumsbereichen
    mit aufgenommen.
    """
    from datetime import date, timedelta
    today = date.today()
    tomorrow = today + timedelta(days=1)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    month_start = today.replace(day=1)
    next_month = (month_start + timedelta(days=31)).replace(day=1)
    month_end = next_month - timedelta(days=1)

    # ---------------------------
    # TODAY Tasks & Milestones
    # ---------------------------
    # Normale Tasks für Today
    today_incomplete = manager.get_tasks_for_date_range(today.isoformat(), today.isoformat(), completed=False)
    today_completed = manager.get_tasks_for_date_range(today.isoformat(), today.isoformat(), completed=True)
    # Milestones, die heute fällig sind
    today_milestones = timeline_manager.get_milestones_for_date_range(today.isoformat(), today.isoformat())
    today_milestones_converted = []
    for m in today_milestones:
        # Wir wandeln die Milestone-Daten in ein Tuple um, das dem Format der Tasks entspricht:
        # (id, title, category, due_date, completed)
        today_milestones_converted.append((
            m["id"],
            f"{m['title']} (Goal: {m['goal_title']})",
            "milestone",
            m["due_date"],
            m["completed"]
        ))
    # Füge die Meilensteine den normalen Tasks hinzu (je nach Status)
    for milestone in today_milestones_converted:
        if milestone[4]:
            today_completed.append(milestone)
        else:
            today_incomplete.append(milestone)
    today_tasks = {"incomplete": today_incomplete, "completed": today_completed}

    # ---------------------------
    # TOMORROW Tasks & Milestones
    # ---------------------------
    tomorrow_incomplete = manager.get_tasks_for_date_range(tomorrow.isoformat(), tomorrow.isoformat(), completed=False)
    tomorrow_completed = manager.get_tasks_for_date_range(tomorrow.isoformat(), tomorrow.isoformat(), completed=True)
    tomorrow_milestones = timeline_manager.get_milestones_for_date_range(tomorrow.isoformat(), tomorrow.isoformat())
    tomorrow_milestones_converted = []
    for m in tomorrow_milestones:
        tomorrow_milestones_converted.append((
            m["id"],
            f"{m['title']} (Goal: {m['goal_title']})",
            "milestone",
            m["due_date"],
            m["completed"]
        ))
    for milestone in tomorrow_milestones_converted:
        if milestone[4]:
            tomorrow_completed.append(milestone)
        else:
            tomorrow_incomplete.append(milestone)
    next_day_tasks = {"incomplete": tomorrow_incomplete, "completed": tomorrow_completed}

    # ---------------------------
    # WEEK Tasks & Milestones
    # ---------------------------
    week_incomplete = manager.get_tasks_for_date_range(week_start.isoformat(), week_end.isoformat(), completed=False, exclude_lists=["Today", "Next Day"])
    week_completed = manager.get_tasks_for_date_range(week_start.isoformat(), week_end.isoformat(), completed=True, exclude_lists=["Today", "Next Day"])
    week_milestones = timeline_manager.get_milestones_for_date_range(week_start.isoformat(), week_end.isoformat())
    week_milestones_converted = []
    for m in week_milestones:
        week_milestones_converted.append((
            m["id"],
            f"{m['title']} (Goal: {m['goal_title']})",
            "milestone",
            m["due_date"],
            m["completed"]
        ))
    for milestone in week_milestones_converted:
        if milestone[4]:
            week_completed.append(milestone)
        else:
            week_incomplete.append(milestone)
    week_tasks = {"incomplete": week_incomplete, "completed": week_completed}

    # ---------------------------
    # MONTH Tasks & Milestones
    # ---------------------------
    month_incomplete = manager.get_tasks_for_date_range(
        month_start.isoformat(), month_end.isoformat(),
        completed=False,
        exclude_lists=["Today", "Next Day", "This Week"],
        exclude_date_range=(week_start.isoformat(), week_end.isoformat())
    )
    month_completed = manager.get_tasks_for_date_range(
        month_start.isoformat(), month_end.isoformat(),
        completed=True,
        exclude_lists=["Today", "Next Day", "This Week"],
        exclude_date_range=(week_start.isoformat(), week_end.isoformat())
    )

    # Statt den reinen Milestone-Datensätzen fügen wir jetzt die Milestone-Tasks hinzu:
    month_milestones = timeline_manager.get_milestones_for_date_range(month_start.isoformat(), month_end.isoformat())
    for m in month_milestones:
        # Für jedes Milestone holen wir die zugehörigen Aufgaben
        milestone_tasks = timeline_manager.get_tasks_for_milestone(m["id"])
        # Konvertiere die Tasks in Dictionary-Form (falls noch nicht geschehen)
        tasks_list = [dict(task) for task in milestone_tasks]

        # Für jeden Task erstellen wir einen Eintrag, bei dem der Task-Titel
        # mit dem Namen des Goals in Klammern versehen wird.
        for task in tasks_list:
            entry = (
                task["id"],
                f"{task['title']} ({m['goal_title']})",
                "milestone_task",  # Verwende eine eigene Kategorie, z.B. "milestone_task"
                m["due_date"],  # Wir übernehmen das Due-Datum des Milestones
                task["completed"]
            )
            if task["completed"]:
                month_completed.append(entry)
            else:
                month_incomplete.append(entry)

    # Zusammensetzen der Monatsliste
    month_tasks = {"incomplete": month_incomplete, "completed": month_completed}

    # ---------------------------
    # Normale Listen
    # ---------------------------
    all_lists = [
        list_name for list_name in manager.get_all_lists()
        if list_name not in ["Today", "Next Day", "This Week", "This Month"]
    ]
    all_lists_with_colors_and_tasks = [
        {
            "name": list_name,
            "color": manager.get_list_color(list_name),
            "tasks": manager.get_tasks(list_name),
        }
        for list_name in all_lists
    ]

    # Alle Daten an das Template übergeben
    return render_template(
        "index.html",
        lists=all_lists_with_colors_and_tasks,
        today_tasks=today_tasks,
        next_day_tasks=next_day_tasks,
        week_tasks=week_tasks,
        month_tasks=month_tasks
    )

@app.route("/special_lists")
@login_required
def special_lists():
    today = date.today()
    tomorrow = today + timedelta(days=1)
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    month_start = today.replace(day=1)
    next_month = (month_start + timedelta(days=31)).replace(day=1)
    month_end = next_month - timedelta(days=1)

    # Spezielle Listen
    today_tasks = manager.get_tasks_for_date_range(today.isoformat(), today.isoformat())
    next_day_tasks = manager.get_tasks_for_date_range(tomorrow.isoformat(), tomorrow.isoformat())
    week_tasks = manager.get_tasks_for_date_range(week_start.isoformat(), week_end.isoformat())
    month_tasks = manager.get_tasks_for_date_range(month_start.isoformat(), month_end.isoformat())

    # Normale Listen
    lists = manager.get_all_lists()
    all_lists_with_colors_and_tasks = [
        {
            "name": list_name,
            "color": manager.get_list_color(list_name),
            "tasks": manager.get_tasks(list_name),
        }
        for list_name in lists
    ]

    return render_template("special_lists.html",
                           today_tasks=today_tasks,
                           next_day_tasks=next_day_tasks,
                           week_tasks=week_tasks,
                           month_tasks=month_tasks,
                           lists=all_lists_with_colors_and_tasks)


@app.route("/toggle_task/<int:task_id>", methods=["POST"])
@login_required
def toggle_task(task_id):
    """
    Toggle the completion status of a task.
    """
    completed = request.json.get("completed", False)
    manager.toggle_task_completion(task_id, completed)  # Update in der Datenbank
    print(f"Task {task_id} toggled to {'completed' if completed else 'incomplete'}")  # Debugging
    return "OK", 200




@app.route("/update_color/<list_name>", methods=["POST"])
@login_required
def update_color(list_name):
    """
    Updates the background color of a list.
    """
    color = request.form.get("color")
    manager.update_list_color(list_name, color)
    return redirect(url_for("index"))


@app.route("/daily_video")
@login_required
def daily_video():
    video_url = get_daily_video()
    if not video_url:
        return "No videos available.", 404
    return render_template("daily_video.html", video_url=video_url)

@app.route("/delete_task/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id):
    manager.delete_task(task_id)
    return "OK", 200


@app.route("/calendar")
@login_required
def calendar():
    # Versuche, Jahr und Monat aus den Query-Parametern zu lesen.
    year_arg = request.args.get("year")
    month_arg = request.args.get("month")

    # Wenn beide Parameter vorhanden und gültig sind, benutze sie.
    if year_arg is not None and month_arg is not None:
        try:
            year = int(year_arg)
            month = int(month_arg)
        except ValueError:
            # Falls ein Fehler beim Konvertieren auftritt, verwende das aktuelle Datum.
            current_date = datetime.date.today()
            year = current_date.year
            month = current_date.month
    else:
        # Wenn keine Query-Parameter vorhanden sind, verwende das aktuelle Datum.
        current_date = datetime.date.today()
        year = current_date.year
        month = current_date.month

    # Tage des Monats berechnen
    days = monthcalendar(year, month)

    # Aufgaben für den aktuellen Monat abrufen
    calendar_tasks = manager.get_calendar_tasks(year, month)

    # Wiederkehrende Aufgaben generieren
    recurring_tasks = manager.get_calendar_tasks_with_recurring(year, month, include_recurring=True)

    # Kombiniere normale und wiederkehrende Aufgaben
    all_tasks = list(calendar_tasks) + recurring_tasks

    return render_template("calendar.html", days=days, tasks=all_tasks, month=month, year=year)


@app.route("/update_task_date/<int:task_id>", methods=["POST"])
@login_required
def update_task_date(task_id):
    new_date = request.json.get("newDate")
    manager.update_task_date(task_id, new_date)
    return "Task date updated successfully!", 200



@app.route("/move_calendar_tasks", methods=["GET"])
@login_required
def move_calendar_tasks():
    manager.move_calendar_tasks_to_special_lists()  # Neue Methode
    return "Tasks for today moved to their special lists!", 200






@app.route("/move_task/<int:task_id>", methods=["POST"])
@login_required
def move_task(task_id):
    data = request.json
    new_list = data.get("newList")
    manager.move_task(task_id, new_list)
    return "OK", 200


@app.route("/add_calendar_task", methods=["POST"])
@login_required
def add_calendar_task():
    title = request.form.get("title")
    date = request.form.get("date")
    category = request.form.get("category")

    connection = manager.get_db_connection()
    cursor = connection.cursor()

    # 🔍 Prüfen, ob die Aufgabe mit gleicher Title, Date & Category bereits existiert
    cursor.execute("SELECT COUNT(*) FROM calendar_tasks WHERE title = ? AND date = ? AND category = ?",
                   (title, date, category))
    exists = cursor.fetchone()[0]

    if exists == 0:  # Falls die Aufgabe noch nicht existiert, füge sie hinzu
        cursor.execute("""
            INSERT INTO calendar_tasks (title, date, category)
            VALUES (?, ?, ?)
        """, (title, date, category))
        connection.commit()

    connection.close()
    return redirect(url_for("calendar"))

@app.route("/calendar/<int:year>/<int:month>")
@login_required
def get_calendar_for_month(year, month):
    from calendar import monthcalendar

    days = monthcalendar(year, month)
    tasks_data = manager.get_calendar_tasks(year, month)  # Holt Aufgaben

    if isinstance(tasks_data, tuple):  # Falls zwei Werte zurückgegeben werden
        tasks, column_names = tasks_data
    else:
        tasks = tasks_data
        column_names = ["title", "date", "category"]  # Setze Standardwerte

    return jsonify({
        "days": days,
        "tasks": [dict(zip(column_names, row)) for row in tasks]
    })



@app.route("/add_recurring_task", methods=["POST"])
@login_required
def add_recurring_task():
    title = request.form.get("title")
    frequency = request.form.get("frequency")
    start_date = request.form.get("start_date")
    interval_value = request.form.get("interval_value")  # Optionales Feld

    # Standardwert für interval_value setzen, falls nicht angegeben
    interval_value = int(interval_value) if interval_value else 1

    # Speichere die wiederkehrende Aufgabe in der Datenbank
    manager.add_recurring_task(title, frequency, start_date, interval_value)
    return redirect(url_for("calendar"))





@app.route("/daily_task_migration", methods=["GET"])
@login_required
def daily_task_migration():
    today = date.today().isoformat()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    # Move tasks for today and tomorrow
    manager.move_calendar_tasks_to_list("Today", today)
    manager.move_calendar_tasks_to_list("Next Day", tomorrow)

    return "Daily tasks migrated successfully!", 200


@app.route("/update_tasks", methods=["GET"])
@login_required
def update_tasks():
    """
    Führt die Funktionen aus, die Aufgaben aus dem Kalender und
    wiederkehrende Aufgaben in Speziallisten einsortieren.
    """
    manager.move_calendar_tasks_to_special_lists()
    manager.add_recurring_tasks_to_special_lists()
    return "Tasks updated successfully!", 200



@app.route("/rename_task/<int:task_id>", methods=["POST"])
@login_required
def rename_task(task_id):
    data = request.json
    new_name = data.get("newName")
    manager.rename_task(task_id, new_name)
    return "OK", 200

@app.route("/update_task_order", methods=["POST"])
@login_required
def update_task_order():
    data = request.json
    new_order = data.get("order", [])
    print(f"Neue Reihenfolge erhalten: {new_order}")  # Debug

    # Aktualisiere die Reihenfolge in der Datenbank
    manager.update_task_order(new_order)
    return "OK", 200



if __name__ == "__main__":
    app.run(debug=True)  # Debug-Modus aktivieren
