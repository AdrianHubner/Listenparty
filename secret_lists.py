from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash
from secret_lists_manager import get_secret_lists, add_secret_list, verify_secret_list
from list_manager import ListManager

secret_bp = Blueprint('secret', __name__, template_folder='templates')
manager = ListManager()  # Damit können wir auch Aufgaben abrufen

@secret_bp.route("/")
def show_secret_lists():
    secret_lists = get_secret_lists()
    return render_template("secret_lists.html", secret_lists=secret_lists)

@secret_bp.route("/create", methods=["GET", "POST"])
def create_secret_list():
    if request.method == "POST":
        name = request.form.get("name")
        color = request.form.get("color") or "#007bff"
        password = request.form.get("password")
        add_secret_list(name, color, password)
        return redirect(url_for("secret.show_secret_lists"))
    return render_template("create_secret_list.html")


@secret_bp.route("/open/<name>", methods=["GET", "POST"])
def open_secret_list(name):
    if request.method == "POST":
        password_input = request.form.get("password")
        if verify_secret_list(name, password_input):
            # Bei korrekter Eingabe leiten wir zu einer Ansicht weiter, die die entsperrte Liste anzeigt
            return redirect(url_for("secret.open_secret_list_view", name=name))
        else:
            flash("Falsches Passwort. Bitte versuche es erneut.", "error")
    return render_template("open_secret_list.html", list_name=name)


@secret_bp.route("/view/<name>")
def open_secret_list_view(name):
    tasks = manager.get_tasks(name)
    return render_template("view_lists.html", list_name=name, tasks=tasks, unlocked=True)
