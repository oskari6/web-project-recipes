"""Recipe routes"""
import math
import sqlite3
from flask import abort, redirect, request, session, Blueprint, render_template, url_for
from services import recipe_service
from services import user_service
from utils.constants import DIETARY_REQUIREMENTS, FOOD_TYPES, UNITS
from utils import validator
from utils.images import save_recipe_images, remove_recipe_files
from utils.decorators import require_csrf, require_login
from db import utils as db_utils

bp = Blueprint("recipes", __name__)


@bp.route("/recipes/<int:page>")
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
        return redirect(url_for("recipes.recipes", page=1, query=query))
    if page > page_count:
        return redirect(url_for("recipes.recipes", page=page_count, query=query))

    return render_template("/recipes/recipes.html",
        page=page,
        page_count=page_count,
        recipes=recipe_service.get_recipes(page, page_size, query=query),
        query=query
    )


@bp.route("/recipes/recipe/<int:recipe_id>")
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
    user = user_service.get_user(found_recipe["creator_id"])

    return render_template(
        "/recipes/recipe.html",
        recipe=found_recipe,
        ingredients=ingredients,
        recipe_steps=recipe_steps,
        images=images,
        comments=comments,
        ratings=ratings,
        avg_rating=avg_rating,
        user_rating=user_rating,
        user=user,
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
    if request.method == "POST":
        values.update(request.form.to_dict())
        ingredients = [{"ingredient": name, "amount": amount, "unit": unit}
                       for name, amount, unit in zip(
                           request.form.getlist("ingredient"),
                           request.form.getlist("ingredient_amount"),
                           request.form.getlist("ingredient_unit"))]
        steps = [{"instruction": step} for step in request.form.getlist("recipe_step")]
    return render_template(
        "recipes/recipe_form.html",
        recipe=found_recipe,
        values=values,
        recipe_ingredients=ingredients,
        recipe_steps=steps,
        recipe_images=recipe_service.get_images(recipe_id) if recipe_id else [],
        food_types=FOOD_TYPES, dietary_requirements=DIETARY_REQUIREMENTS,
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
        "title", "description", "food_type", "dietary_requirements",
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
    return redirect(url_for("recipes.recipe", recipe_id=recipe_id))


@bp.route("/recipes/create", methods=["GET", "POST"])
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


@bp.route("/recipes/edit/<int:recipe_id>", methods=["GET", "POST"])
@require_login
@require_csrf
def edit_recipe(recipe_id):
    """Edit a recipe owned by the current user."""
    found_recipe = owned_recipe(recipe_id)
    if request.method == "GET":
        return recipe_form(found_recipe)
    return save_recipe(found_recipe)


@bp.route("/recipes/remove/<int:recipe_id>", methods=["POST"])
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
    return redirect(url_for("recipes.recipes", page=1))


@bp.route("/recipes/create/comment/<int:recipe_id>", methods=["POST"])
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

    return redirect(url_for("recipes.recipe", recipe_id=recipe_id))


@bp.route("/recipes/edit/comment/<int:comment_id>", methods=["POST"])
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
    return redirect(url_for("recipes.recipe", recipe_id=recipe_id))


@bp.route("/recipes/remove/comment/<int:comment_id>", methods=["POST"])
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
    return redirect(url_for("recipes.recipe", recipe_id=recipe_id))


@bp.route("/recipes/create/rating/<int:recipe_id>", methods=["POST"])
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
    return redirect(url_for("recipes.recipe", recipe_id=recipe_id))


@bp.route("/recipes/edit/rating/<int:rating_id>", methods=["POST"])
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
    return redirect(url_for("recipes.recipe", recipe_id=recipe_id))
