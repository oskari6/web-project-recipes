import secrets
import sqlite3

from flask import abort, flash, redirect, request, session, Blueprint, render_template
from flask import render_template
from services import user_service
from werkzeug.security import generate_password_hash, check_password_hash
from flask import url_for

bp = Blueprint("auth", __name__)

@bp.route("/auth/register", methods=["POST", "GET"])
def register():
    if request.method == "GET":
        return render_template("users/user_form.html", filled={})

    if request.method == "POST":
        username = request.form["username"]
        if len(username) > 16:
            abort(403)
        password = request.form["password"]
        passwordConfirm = request.form["passwordConfirm"]

        if password != passwordConfirm:
            flash("Passwords did not match.")
            filled = {"username": username}
            return render_template("users/user_form.html", filled=filled)

        existing_user = user_service.get_user_by_username(username)
        if existing_user:
            flash("Username is already reserved")
            filled = {"username": username}
            return render_template("users/user_form.html", filled=filled)
        
        try:
            user_service.create_user(username, generate_password_hash(password))
            flash("Registering account succeeded, you can now login.")
            return redirect(url_for("auth.login"))
        except sqlite3.IntegrityError:
            abort(403)
            

@bp.route("/auth/login", methods=["POST", "GET"])
def login():
    if request.method == "GET":
        return render_template("auth/login.html")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = user_service.get_user_by_username(username)
        if user:
            password_correct = check_password_hash(
                user["password_hash"],
                password
            )
            if not password_correct:
                flash("Wrong username or password.")
                return render_template("auth/login.html")
            
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["csrf_token"] = secrets.token_hex(16)
            return redirect(url_for("home"))
        else:
            flash("Wrong username or password.")
            return render_template("auth/login.html")

@bp.route("/auth/logout", methods=["GET", "POST"])
def logout():
    del session["user_id"]
    return redirect(url_for("home"))
