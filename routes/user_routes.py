from flask import abort,  flash, make_response, redirect, request, session, Blueprint, render_template
from flask import render_template
from services import user_service as user_service
from services import recipe_service as recipe_service
import math
from werkzeug.security import generate_password_hash
from flask import url_for
from pathlib import Path
from uuid import uuid4
from werkzeug.utils import secure_filename
from utils.constants import ALLOWED_IMAGE_EXTENSIONS
from utils.decorators import require_csrf, require_login

bp = Blueprint("users", __name__)

@bp.route("/users/<int:page>")
def users(page=1):
    page_size = 10
    query = request.args.get("query", "").strip()

    user_count = user_service.user_count(query)
    page_count = math.ceil(user_count / page_size)
    page_count = max(page_count, 1)

    if page < 1:
        return redirect(url_for("users.users", page=1, query=query))
    if page > page_count:
        return redirect(url_for("users.users", page=page_count, query=query))

    users = user_service.get_users(page, page_size, query)
    return render_template(
        "users/users.html",
        users=users,
        page=page,
        query=query,
        page_count=page_count,
    )

@bp.route("/users/user/<int:user_id>/", defaults={"page": 1})
@bp.route("/users/user/<int:user_id>/<int:page>")
def user(user_id, page):
    page_size = 10
    recipe_count = recipe_service.recipe_count(user_id)
    page_count = math.ceil(recipe_count / page_size)
    page_count = max(page_count, 1)

    user = user_service.get_user(user_id)
    if not user:
        abort(404)

    recipes = recipe_service.get_recipes(page, page_size, user_id)
    return render_template( 
        "users/user.html",
        user=user,
        recipes=recipes,
        page=page,
        page_count=page_count,
        recipe_count=recipe_count
    )

@bp.route("/user/edit/<int:user_id>", methods=["GET", "POST"])
@require_login
@require_csrf
def edit_user(user_id):
    user = user_service.get_user(user_id)

    if not user or user["id"] != session["user_id"]:
        abort(403)

    if request.method == "GET":
        return render_template(
            "users/user_form.html",
            user=user,
            filled={}
        )

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
            user=user,
            filled={}
        )

    filename = save_profile_picture(image)

    password_hash = (
        generate_password_hash(password)
        if password
        else user_service.get_user_password_hash(user_id)["password_hash"]
    )
    
    user_service.update_user(
        user_id,
        username,
        password_hash,
        filename
    )

    return redirect(
        url_for("users.user", user_id=user_id)
    )

@bp.route("/users/remove", methods=["POST"])
@require_login
@require_csrf
def remove_user():
    user_service.delete_user(session["user_id"])
    del session["user_id"]
    del session["username"]
    return redirect(url_for("home"))

def save_profile_picture(image):
    if not image or not image.filename:
        return None

    original_name = secure_filename(image.filename)
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        abort(400)

    filename = f"{uuid4().hex}{extension}"

    upload_dir = Path("static/uploads/users")
    upload_dir.mkdir(parents=True, exist_ok=True)

    image.save(upload_dir / filename)

    return filename