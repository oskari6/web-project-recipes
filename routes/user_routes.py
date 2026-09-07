"""User routes"""
import math
from werkzeug.security import generate_password_hash
from flask import abort,  flash, redirect, request, session, Blueprint, render_template, url_for
from services import user_service
from services import recipe_service
from utils.decorators import require_csrf, require_login
from utils.images import save_profile_picture

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

    if not found_user or found_user["id"] != session["user_id"]:
        abort(403)

    if request.method == "GET":
        return render_template(
            "users/user_form.html",
            user=found_user
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
            user=found_user
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
    """
    Remove user route
    """
    user_service.delete_user(session["user_id"])
    del session["user_id"]
    del session["username"]
    return redirect(url_for("home"))
