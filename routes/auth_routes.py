"""Auth routes"""
import secrets
import sqlite3

from flask import flash, redirect, request, session, Blueprint, render_template, url_for
from werkzeug.security import generate_password_hash
from services import user_service
from utils.images import save_profile_picture, remove_profile_file
from utils import validator
from utils.decorators import require_csrf, require_login

bp = Blueprint("auth", __name__)

@bp.route("/auth/register", methods=["POST", "GET"])
@require_csrf
def register():
    """
    Register route
    """
    if request.method == "GET":
        return render_template("users/user_form.html", user=None)

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    password_confirm = request.form.get("password_confirm", "")
    image = request.files.get("image")

    error = validator.validate_auth_register(username, password, password_confirm)
    if error:
        return render_template(
            "users/user_form.html",
            error=error
        ), 400

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
        remove_profile_file(filename)
        return render_template("users/user_form.html", error="Username is already reserved."), 400
    except Exception:
        remove_profile_file(filename)
        raise

@bp.route("/auth/login", methods=["POST", "GET"])
@require_csrf
def login():
    """
    Login route
    """
    if request.method == "GET":
        return render_template("auth/login.html")

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    error = validator.validate_auth_login(username, password)
    if error:
        return render_template(
            "auth/login.html",
            error=error
        ), 400

    user = user_service.get_user_by_username(username)
    session.clear()
    session["user_id"] = user["id"]
    session["username"] = username
    session["csrf_token"] = secrets.token_hex(16)
    return redirect(url_for("home"))

@bp.route("/auth/logout", methods=["POST"])
@require_csrf
@require_login
def logout():
    """
    Logout route
    """
    session.clear()
    return redirect(url_for("home"))
