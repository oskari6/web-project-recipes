"""User routes"""
import math
import sqlite3
from werkzeug.security import generate_password_hash
from flask import abort, redirect, request, session, Blueprint, render_template, url_for
from services import user_service
from services import recipe_service
from utils.decorators import require_csrf, require_login
from utils import validator
from utils.images import save_profile_picture, remove_profile_file, remove_recipe_files

bp = Blueprint("users", __name__)

@bp.route("/users/<int:page>")
def users(page=1):
    """
    Users route
    Args:
        page(int) : page number
    """
    page_size = 10
    query = request.args.get("query", "").strip()

    user_count = user_service.user_count(query)
    page_count = math.ceil(user_count / page_size)
    page_count = max(page_count, 1)

    if page < 1:
        return redirect(url_for("users.users", page=1, query=query))
    if page > page_count:
        return redirect(url_for("users.users", page=page_count, query=query))

    return render_template(
        "users/users.html",
        users=user_service.get_users(page, page_size, query),
        page=page,
        query=query,
        page_count=page_count,
    )

@bp.route("/users/user/<int:user_id>/", defaults={"page": 1})
@bp.route("/users/user/<int:user_id>/<int:page>")
def user(user_id, page):
    """
    User route
    Args:
        user_id(int) : id of user
        page(int) : page number for recipes
    """
    page_size = 10
    recipe_count = recipe_service.recipe_count(user_id)
    page_count = math.ceil(recipe_count / page_size)
    page_count = max(page_count, 1)

    found_user = user_service.get_user(user_id)
    if not found_user:
        abort(404)

    if page < 1 or page > page_count:
        return redirect(url_for("users.user", user_id=user_id, page=max(1, min(page, page_count))))
    recipes = recipe_service.get_recipes(page, page_size, user_id)
    return render_template(
        "users/user.html",
        user=found_user,
        recipes=recipes,
        page=page,
        page_count=page_count,
        recipe_count=recipe_count
    )

@bp.route("/user/edit/<int:user_id>", methods=["GET", "POST"])
@require_login
@require_csrf
def edit_user(user_id):
    """
    Edit user route
    Args:
        user_id(int) : id of user
    """
    found_user = user_service.get_user(user_id)

    if not found_user:
        abort(404)
    if found_user["id"] != session["user_id"]:
        abort(403)

    if request.method == "GET":
        return render_template(
            "users/user_form.html",
            user=found_user
        )

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    password_confirm = request.form.get("password_confirm", "")
    image = request.files.get("image")

    error = validator.validate_user(username, password, password_confirm, user_id)
    if error:
        return render_template("users/user_form.html", user=found_user, error=error), 400

    filename = save_profile_picture(image)

    password_hash = (
        generate_password_hash(password)
        if password
        else user_service.get_user_password_hash(user_id)["password_hash"]
    )

    try:
        user_service.update_user(
            user_id, username, password_hash, filename or found_user["profile_picture_filename"]
        )
    except sqlite3.IntegrityError:
        remove_profile_file(filename)
        return render_template(
            "users/user_form.html", user=found_user, error="Username is already reserved."
        ), 400
    except Exception:
        remove_profile_file(filename)
        raise
    if filename:
        remove_profile_file(found_user["profile_picture_filename"])
    session["username"] = username

    return redirect(
        url_for("users.user", user_id=user_id)
    )

@bp.route("/users/remove", methods=["POST"])
@require_login
@require_csrf
def remove_user():
    """
    Remove user route
    """
    found_user = user_service.get_user(session["user_id"])
    images = [(recipe["id"], recipe_service.get_images(recipe["id"]))
              for recipe in user_service.get_user_recipes(session["user_id"])]
    user_service.delete_user(session["user_id"])
    for recipe_id, recipe_images in images:
        remove_recipe_files(recipe_id, [image["file_name"] for image in recipe_images])
    if found_user:
        remove_profile_file(found_user["profile_picture_filename"])
    session.clear()
    return redirect(url_for("home"))
