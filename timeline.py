# timeline.py
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from timeline_manager import TimelineManager

timeline_bp = Blueprint('timeline', __name__, template_folder='templates')

# Instanziiere den TimelineManager
timeline_manager = TimelineManager()

@timeline_bp.route("/")
def show_timeline():
    # Hol dir alle Ziele und zugehörigen Meilensteine
    goals = timeline_manager.get_goals()
    # Für jedes Ziel kannst du die Meilensteine abrufen
    goals_with_milestones = []
    for goal in goals:
        milestones = timeline_manager.get_milestones_for_goal(goal["id"])
        goals_with_milestones.append({
            "goal": goal,
            "milestones": milestones if milestones is not None else []
        })
    return render_template("timeline.html", goals=goals_with_milestones)

@timeline_bp.route("/add_goal", methods=["POST"])
def add_goal():
    # Daten aus dem Formular holen
    title = request.form.get("title")
    description = request.form.get("description")
    due_date = request.form.get("due_date")
    color = request.form.get("color") or "#007bff"  # Standardfarbe, falls keine gewählt wurde
    # Die add_goal-Methode der TimelineManager-Instanz aufrufen
    timeline_manager.add_goal(title, description, due_date, color)
    return redirect(url_for("timeline.show_timeline"))

@timeline_bp.route("/add_milestone", methods=["POST"])
def add_milestone():
    goal_id = request.form.get("goal_id")
    title = request.form.get("title")
    due_date = request.form.get("due_date")
    timeline_manager.add_milestone(goal_id, title, due_date)
    return redirect(url_for("timeline.show_timeline"))

@timeline_bp.route("/add_milestone_task", methods=["POST"])
def add_milestone_task():
    milestone_id = request.form.get("milestone_id")
    title = request.form.get("title")
    timeline_manager.add_milestone_task(milestone_id, title)
    return redirect(url_for("timeline.show_timeline"))

@timeline_bp.route("/api/milestone_tasks/<int:milestone_id>")
def milestone_tasks(milestone_id):
    tasks = timeline_manager.get_tasks_for_milestone(milestone_id)
    # Konvertiere die SQLite-Rows in Dictionaries
    tasks_list = [dict(task) for task in tasks]
    return jsonify(tasks_list)



@timeline_bp.route("/api/timeline_data")
def timeline_data():
    """
    Liefert Daten für alle Ziele inklusive Meilensteine und Fortschritt.
    Beispielhafte Struktur:
    [
      {
        "id": 1,
        "title": "Eigenes Unternehmen gründen",
        "description": "Gründung und Aufbau eines Startups",
        "start_date": "2023-01-01",
        "due_date": "2025-12-31",
        "color": "#ff5733",
        "milestones": [
            {
              "id": 10,
              "title": "Businessplan fertig",
              "due_date": "2023-06-30",
              "progress": 80,       // in Prozent
              "percentage": 20      // relative Position auf der Zeitachse (z.B. 20%)
            },
            {
              "id": 11,
              "title": "Prototyp fertig",
              "due_date": "2024-03-31",
              "progress": 40,
              "percentage": 50
            },
            // ...
        ]
      },
      // weitere Ziele...
    ]
    """
    timeline_data = timeline_manager.get_all_timeline_data()  # Schreibe eine Methode, die diese Struktur liefert.
    return jsonify(timeline_data)

