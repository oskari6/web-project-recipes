"""App entry point"""

from datetime import datetime
import time
import math
import sqlite3
from functools import wraps
import secrets
import markupsafe
from werkzeug.security import generate_password_hash

from flask import abort, flash, g, redirect, request, session, render_template, url_for, Flask
from images import save_profile_picture, remove_profile_file, remove_recipe_files,save_recipe_images
from config import UNITS, SECRET_KEY
import db as db_utils
import validator
import users as user_service
import recipes as recipe_service

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024

# initialize database tables and indexes
db_utils.init_db()

# this is for session id:s
app.secret_key = SECRET_KEY

def get_csrf_token():
    """
    csrf utility
    """
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)

    return session["csrf_token"]

def require_csrf(func):
    """
    csrf decorator
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if request.method == "POST":
            token = request.form.get("csrf_token")

            if not token or not secrets.compare_digest(
                token.encode(), session.get("csrf_token", "").encode()
            ):
                abort(403)

        return func(*args, **kwargs)

    return wrapper

def require_login(func):
    """
    login check utility
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            abort(401)
        if not user_service.get_user(session["user_id"]):
            session.clear()
            abort(401)

        return func(*args, **kwargs)

    return wrapper

@app.template_filter()
def show_lines(content):
    """
    Utility to show linebreaks
    for cleaning html markup for client
    """
    content = str(markupsafe.escape(content))
    content = content.replace("\n", "<br />")
    return markupsafe.Markup(content)

@app.template_filter("datetime")
def format_datetime(value):
    """Format a database timestamp for display."""
    if not value:
        return ""

    date = datetime.fromisoformat(value)
    return date.strftime("%d.%m.%Y %H:%M")

@app.context_processor
def inject_csrf_token():
    """
    Utility to inject csrf token
    """
    return {"csrf_token": get_csrf_token()}

# performance metrics
@app.before_request
def before_request():
    """
    Permomance metrics
    """
    g.start_time = time.perf_counter()

@app.after_request
def after_request(response):
    """
    Permomance metrics
    """
    elapsed_time = time.perf_counter() - g.start_time
    print(f"{request.method} {request.path}: {elapsed_time:.3f}s")
    return response

# entry point
@app.route("/")
def home():
    """
    Initial page route. entry point
    """
    return render_template("home.html")

@app.errorhandler(404)
def not_found(_error):
    """
    Error route
    """
    return render_template("404.html"), 404

@app.errorhandler(403)
def forbidden(_error):
    """
    Error route
    """
    return render_template("403.html"), 403

@app.errorhandler(401)
def unauthorized(error):
    """
    Error route
    """
    return render_template("401.html", error=error), 401

@app.errorhandler(500)
def internal_server(_error):
    """
    Error route
    """
    return render_template("500.html"), 500

@app.errorhandler(400)
@app.errorhandler(413)
def invalid_request(error):
    """Show input errors with their correct HTTP status."""
    return render_template("400.html", error=error.description), error.code

@require_csrf
@app.route("/auth/register", methods=["POST", "GET"])
def register():
    """
    Register route
    """
    if request.method == "GET":
        return render_template("user_form.html", user=None)

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    password_confirm = request.form.get("password_confirm", "")
    image = request.files.get("image")

    error = validator.validate_auth_register(username, password, password_confirm)
    if error:
        return render_template(
            "user_form.html",
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
        return redirect(url_for("login"))
    except sqlite3.IntegrityError:
        remove_profile_file(filename)
        return render_template("user_form.html", error="Username is already reserved."), 400
    except Exception:
        remove_profile_file(filename)
        raise

@app.route("/auth/login", methods=["POST", "GET"])
@require_csrf
def login():
    """
    Login route
    """
    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    error = validator.validate_auth_login(username, password)
    if error:
        return render_template(
            "login.html",
            error=error
        ), 400

    found_user = user_service.get_user_by_username(username)
    session.clear()
    session["user_id"] = found_user["id"]
    session["username"] = username
    session["csrf_token"] = secrets.token_hex(16)
    return redirect(url_for("home"))

@app.route("/auth/logout", methods=["POST"])
@require_csrf
@require_login
def logout():
    """
    Logout route
    """
    session.clear()
    return redirect(url_for("home"))


@app.route("/recipes/<int:page>")
def recipes(page=1):
    """
    Recipes route
    Args:
        page(int) : page number
    """
    page_size = 10
    query = request.args.get("query", "").strip()

    recipe_count = recipe_service.recipe_count(query=query)
    page_count = math.ceil(recipe_count / page_size)
    page_count = max(page_count, 1)

    if page < 1:
        return redirect(url_for("recipes", page=1, query=query))
    if page > page_count:
        return redirect(url_for("recipes", page=page_count, query=query))

    return render_template("recipes.html",
        page=page,
        page_count=page_count,
        recipes=recipe_service.get_recipes(page, page_size, query=query),
        query=query
    )


@app.route("/recipes/recipe/<int:recipe_id>")
def recipe(recipe_id):
    """
    Recipe route
    Args:
        recipe_id(int) : id of recipe
    """
    found_recipe = recipe_service.get_recipe(recipe_id)
    if not found_recipe:
        abort(404)
    user_rating = None

    if session.get("user_id"):
        user_rating = recipe_service.get_rating(
            recipe_id,
            session["user_id"]
        )
    ingredients = recipe_service.get_ingredients(recipe_id)
    recipe_steps = recipe_service.get_recipe_steps(recipe_id)
    images = recipe_service.get_images(recipe_id)
    avg_rating = recipe_service.get_average_rating(recipe_id)
    comment_pages = max(1, math.ceil(recipe_service.comment_count(recipe_id) / 10))
    rating_pages = max(1, math.ceil(avg_rating["rating_count"] / 10))
    comment_page = min(comment_pages, max(1, request.args.get("comment_page", 1, type=int)))
    rating_page = min(rating_pages, max(1, request.args.get("rating_page", 1, type=int)))
    comments = recipe_service.get_comments(recipe_id, comment_page)
    ratings = recipe_service.get_ratings(recipe_id, rating_page)
    found_user = user_service.get_user(found_recipe["creator_id"])

    return render_template(
        "recipe.html",
        recipe=found_recipe,
        ingredients=ingredients,
        recipe_steps=recipe_steps,
        images=images,
        comments=comments,
        ratings=ratings,
        avg_rating=avg_rating,
        user_rating=user_rating,
        user=found_user,
        comment_page=comment_page,
        comment_pages=comment_pages,
        rating_page=rating_page,
        rating_pages=rating_pages
    )


def recipe_form(found_recipe=None, error=None):
    """Render recipe fields, retaining submitted text after validation errors."""
    recipe_id = found_recipe["id"] if found_recipe else None
    ingredients = recipe_service.get_ingredients(recipe_id) if recipe_id else []
    steps = recipe_service.get_recipe_steps(recipe_id) if recipe_id else []
    values = dict(found_recipe) if found_recipe else {}
    food_types = recipe_service.get_food_types()
    dietary_requirements = recipe_service.get_dietary_requirements()

    if request.method == "POST":
        values.update(request.form.to_dict())
        ingredients = [{"ingredient": name, "amount": amount, "unit": unit}
                       for name, amount, unit in zip(
                           request.form.getlist("ingredient"),
                           request.form.getlist("ingredient_amount"),
                           request.form.getlist("ingredient_unit"))]
        steps = [{"instruction": step} for step in request.form.getlist("recipe_step")]
    return render_template(
        "recipe_form.html",
        recipe=found_recipe,
        values=values,
        recipe_ingredients=ingredients,
        recipe_steps=steps,
        recipe_images=recipe_service.get_images(recipe_id) if recipe_id else [],
        food_types=food_types,
        dietary_requirements=dietary_requirements,
        units=UNITS, error=error
    )


def save_recipe(found_recipe=None):
    """Validate the entire form, then save metadata and children atomically."""
    recipe_id = found_recipe["id"] if found_recipe else None
    images = request.files.getlist("images")
    removed_ids = request.form.getlist("remove_image")
    existing_images = recipe_service.get_images(recipe_id) if recipe_id else []
    error = validator.validate_recipe(request.form)
    if error:
        return recipe_form(found_recipe, error), 400

    fields = {key: request.form.get(key, "").strip() for key in (
        "title", "description", "food_type", "dietary_requirement",
        "servings", "preparation_time"
    )}
    for key in ("servings", "preparation_time"):
        fields[key] = int(fields[key]) if fields[key] else None
    con = db_utils.get_connection()
    saved_files = []
    try:
        if found_recipe:
            recipe_service.update_recipe(recipe_id, **fields, con=con)
        else:
            recipe_id = recipe_service.create_recipe(
                **fields, creator_id=session["user_id"], con=con
            )
        recipe_service.create_ingredients(
            recipe_id, request.form.getlist("ingredient"),
            request.form.getlist("ingredient_amount"),
            request.form.getlist("ingredient_unit"), con
        )
        recipe_service.create_recipe_steps(recipe_id, request.form.getlist("recipe_step"), con)
        for image_id in removed_ids:
            recipe_service.remove_image(recipe_id, image_id, con)
        save_recipe_images(recipe_id, images, con, saved_files)
        con.commit()
    except Exception:
        con.rollback()
        for path in saved_files:
            path.unlink(missing_ok=True)
        raise
    finally:
        con.close()
    remove_recipe_files(recipe_id, [image["file_name"] for image in existing_images
                                    if str(image["id"]) in removed_ids])
    return redirect(url_for("recipe", recipe_id=recipe_id))


@app.route("/recipes/create", methods=["GET", "POST"])
@require_login
@require_csrf
def create_recipe():
    """Create a recipe for the current user."""
    if request.method == "GET":
        return recipe_form()
    return save_recipe()


def owned_recipe(recipe_id):
    """
    Require an existing recipe owned by the current user.
    Args:
        recipe_id(int): recipe's id
    Returns:
        found_recipe(recipe): recipe that's found
    """
    found_recipe = recipe_service.get_recipe(recipe_id)
    if not found_recipe:
        abort(404)
    if found_recipe["creator_id"] != session["user_id"]:
        abort(403)
    return found_recipe


@app.route("/recipes/edit/<int:recipe_id>", methods=["GET", "POST"])
@require_login
@require_csrf
def edit_recipe(recipe_id):
    """Edit a recipe owned by the current user."""
    found_recipe = owned_recipe(recipe_id)
    if request.method == "GET":
        return recipe_form(found_recipe)
    return save_recipe(found_recipe)


@app.route("/recipes/remove/<int:recipe_id>", methods=["POST"])
@require_login
@require_csrf
def remove_recipe(recipe_id):
    """
    Remove recipe route
    Args:
        recipe_id(int) : id of recipe
    """
    owned_recipe(recipe_id)
    images = recipe_service.get_images(recipe_id)
    recipe_service.delete_recipe(recipe_id)
    remove_recipe_files(recipe_id, [image["file_name"] for image in images])
    return redirect(url_for("recipes", page=1))


@app.route("/recipes/create/comment/<int:recipe_id>", methods=["POST"])
@require_login
@require_csrf
def create_comment(recipe_id):
    """
    Create recipe comment route
    Args:
        recipe_id(int) : id of recipe
    """
    if not recipe_service.get_recipe(recipe_id):
        abort(404)

    comment = request.form.get("comment", "").strip()
    error = validator.validate_comment(comment)
    if error:
        abort(400, description=error)
    recipe_service.add_comment(recipe_id, session["user_id"], comment)

    return redirect(url_for("recipe", recipe_id=recipe_id))


@app.route("/recipes/edit/comment/<int:comment_id>", methods=["POST"])
@require_login
@require_csrf
def edit_comment(comment_id):
    """
    Edit recipecomment  route
    Args:
        comment_id(int) : id of comment
    """
    comment = recipe_service.get_comment_by_id(comment_id)
    if not comment:
        abort(404)

    if comment["creator_id"] != session["user_id"]:
        abort(403)

    recipe_id = comment["recipe_id"]
    value = request.form.get("comment", "").strip()
    error = validator.validate_comment(value)
    if error:
        abort(400, description=error)
    recipe_service.update_comment(comment_id, value)
    return redirect(url_for("recipe", recipe_id=recipe_id))


@app.route("/recipes/remove/comment/<int:comment_id>", methods=["POST"])
@require_login
@require_csrf
def remove_comment(comment_id):
    """
    Remove recipe comment route
    Args:
        comment(int) : id of comment
    """
    comment = recipe_service.get_comment_by_id(comment_id)
    if not comment:
        abort(404)

    if comment["creator_id"] != session["user_id"]:
        abort(403)

    recipe_id = comment["recipe_id"]
    recipe_service.delete_comment(comment_id)
    return redirect(url_for("recipe", recipe_id=recipe_id))


@app.route("/recipes/create/rating/<int:recipe_id>", methods=["POST"])
@require_login
@require_csrf
def create_rating(recipe_id):
    """
    Create recipe rating route
    Args:
        recipe_id(int) : id of recipe
    """
    if not recipe_service.get_recipe(recipe_id):
        abort(404)

    if recipe_service.get_recipe(recipe_id)["creator_id"] == session["user_id"]:
        abort(403)
    rating = request.form.get("rating", "")
    error = validator.validate_rating(rating)
    if error:
        abort(400, description=error)
    if recipe_service.get_rating(recipe_id, session["user_id"]):
        abort(400, description="You have already rated this recipe. Edit your rating instead.")
    try:
        recipe_service.add_rating(recipe_id, session["user_id"], int(rating))
    except sqlite3.IntegrityError:
        abort(400, description="Unable to add this rating. It may already exist.")
    return redirect(url_for("recipe", recipe_id=recipe_id))


@app.route("/recipes/edit/rating/<int:rating_id>", methods=["POST"])
@require_login
@require_csrf
def edit_rating(rating_id):
    """
    Edit recipe rating route
    Args:
        rating_id(int) : id of recipe rating
    """
    rating = recipe_service.get_rating_by_id(rating_id)
    if not rating:
        abort(404)

    if rating["creator_id"] != session["user_id"]:
        abort(403)
    recipe_id = rating["recipe_id"]
    if recipe_service.get_recipe(recipe_id)["creator_id"] == session["user_id"]:
        abort(403)
    value = request.form.get("rating", "")
    error = validator.validate_rating(value)
    if error:
        abort(400, description=error)
    recipe_service.update_rating(rating_id, int(value))
    return redirect(url_for("recipe", recipe_id=recipe_id))


@app.route("/users/<int:page>")
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
        return redirect(url_for("users", page=1, query=query))
    if page > page_count:
        return redirect(url_for("users", page=page_count, query=query))

    return render_template(
        "users.html",
        users=user_service.get_users(page, page_size, query),
        page=page,
        query=query,
        page_count=page_count,
    )

@app.route("/users/user/<int:user_id>/", defaults={"page": 1})
@app.route("/users/user/<int:user_id>/<int:page>")
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
        return redirect(url_for("user", user_id=user_id, page=max(1, min(page, page_count))))
    found_recipes = recipe_service.get_recipes(page, page_size, user_id)
    return render_template(
        "user.html",
        user=found_user,
        recipes=found_recipes,
        page=page,
        page_count=page_count,
        recipe_count=recipe_count
    )

@app.route("/user/edit/<int:user_id>", methods=["GET", "POST"])
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
            "user_form.html",
            user=found_user
        )

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    password_confirm = request.form.get("password_confirm", "")
    image = request.files.get("image")

    error = validator.validate_user(username, password, password_confirm, user_id)
    if error:
        return render_template("user_form.html", user=found_user, error=error), 400

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
            "user_form.html", user=found_user, error="Username is already reserved."
        ), 400
    except Exception:
        remove_profile_file(filename)
        raise
    if filename:
        remove_profile_file(found_user["profile_picture_filename"])
    session["username"] = username

    return redirect(
        url_for("user", user_id=user_id)
    )

@app.route("/users/remove", methods=["POST"])
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
