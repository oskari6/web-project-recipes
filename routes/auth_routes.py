"""Auth routes"""
import secrets
import sqlite3

from flask import abort, flash, redirect, request, session, Blueprint, render_template, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from routes.user_routes import save_profile_picture
from services import user_service

bp = Blueprint("auth", __name__)

@bp.route("/auth/register", methods=["POST", "GET"])
def register():
    """
    Register route
    """
    if request.method == "GET":
        return render_template("users/user_form.html",user=None)

    username = request.form["username"].strip()
    password = request.form["password"]
    password_confirm = request.form["passwordConfirm"]
    image = request.files.get("image")

    if len(username) > 16:
        abort(403)

    if password != password_confirm:
        flash("Passwords did not match.")
        return render_template(
            "users/user_form.html",
            user=None
        )

    existing_user = user_service.get_user_by_username(username)

    if existing_user:
        flash("Username is already reserved.")
        return render_template(
            "users/user_form.html",
            user=None
        )

    filename = save_profile_picture(image)

    try:
        user_service.create_user(
            username,
            generate_password_hash(password),
            filename
        )

        flash("Registering account succeeded, you can now login.")
        return redirect(url_for("auth.login"))

    except sqlite3.IntegrityError:
        abort(403)

@bp.route("/auth/login", methods=["POST", "GET"])
def login():
    """
    Login route
    """
    if request.method == "GET":
        return render_template("auth/login.html")

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
    flash("Wrong username or password.")
    return render_template("auth/login.html")

@bp.route("/auth/logout", methods=["GET", "POST"])
def logout():
    """
    Logout route
    """
    del session["user_id"]
    del session["username"]
    return redirect(url_for("home"))
