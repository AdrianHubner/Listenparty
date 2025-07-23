# auth.py
import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

from user_model import User, get_db_connection  # <-- hierher holen wir User und DB‑Conn

auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        username = request.form["username"]
        password = request.form["password"]
        pw_hash  = generate_password_hash(password)
        conn = get_db_connection()
        cur  = conn.cursor()
        cur.execute("INSERT INTO users (username, password_hash) VALUES (?,?)",
                    (username, pw_hash))
        conn.commit(); conn.close()
        flash("Registrierung erfolgreich, bitte melde dich an.","success")
        return redirect(url_for("auth.login"))
    return render_template("register.html")

@auth_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        pwd      = request.form["password"]
        print(f"[DEBUG] Versuch, Benutzer '{username}' anzumelden…")   # neu
        user     = User.find_by_username(username)
        print(f"[DEBUG] User.lookup →", user)                        # neu
        if user:
            from werkzeug.security import check_password_hash
            ok = check_password_hash(user.password_hash, pwd)
            print(f"[DEBUG] Passwort-Check: {ok}")                    # neu
        if user and ok:
            print("[DEBUG] login_user wird aufgerufen")              # neu
            login_user(user)
            return redirect(url_for("index"))
        flash("Ungültige Anmeldedaten", "error")
    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))

