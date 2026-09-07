"""Recipe routes"""
import math
from pathlib import Path
from uuid import uuid4
import sqlite3
from werkzeug.utils import secure_filename
from flask import abort, redirect, request, session, Blueprint, render_template, url_for
from services import recipe_service
from services import user_service
from utils.constants import ALLOWED_IMAGE_EXTENSIONS, DIETARY_REQUIREMENTS, FOOD_TYPES, UNITS
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

    recipe_count = recipe_service.recipe_count(query)
    page_count = math.ceil(recipe_count / page_size)
    page_count = max(page_count, 1)

    if page < 1:
        return redirect(url_for("recipes.recipes", page=1))
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
    comments = recipe_service.get_comments(recipe_id)
    ratings = recipe_service.get_ratings(recipe_id)
    avg_rating = recipe_service.get_average_rating(recipe_id)
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
        user=user
    )


@bp.route("/recipes/create", methods=["GET", "POST"])
@require_login
@require_csrf
def create_recipe():
    """
    Create recipe route
    """
    if request.method == "GET":
        return render_template("/recipes/recipe_form.html",
            recipe=None,
            recipe_ingredients=[],
            recipe_steps=[],
            recipe_images=[],
            food_types=FOOD_TYPES,
            dietary_requirements=DIETARY_REQUIREMENTS,
            units=UNITS
        )

    title = request.form["title"]
    description = request.form["description"]
    food_type = request.form["food_type"]
    dietary_requirements = request.form["dietary_requirements"]
    servings = request.form["servings"]
    preparation_time = request.form["preparation_time"]

    con = db_utils.get_connection()
    try:
        new_recipe_id = recipe_service.create_recipe(
            title,
            description,
            session["user_id"],
            food_type,
            dietary_requirements,
            servings,
            preparation_time,
            con
        )

        recipe_service.create_ingredients(
            new_recipe_id,
            ingredients=request.form.getlist("ingredient"),
            amounts=request.form.getlist("ingredient_amount"),
            units=request.form.getlist("ingredient_unit"),
            con=con
        )

        recipe_service.create_recipe_steps(
            new_recipe_id,
            steps=request.form.getlist("recipe_step"),
            con=con
        )

        create_recipe_images(
            new_recipe_id,
            images=request.files.getlist("images"),
            con=con
        )

        con.commit()
    except sqlite3.IntegrityError:
        abort(403)
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()

    return redirect(url_for("recipes.recipe", recipe_id=new_recipe_id))

def create_recipe_images(
    recipe_id,
    images,
    con
):
    """
    Create images utility function
    Args:
        recipe_id(int) : id of recipe
        steps(list): list
        con(Connection) : connection object
    """
    upload_dir = Path("static/uploads/recipes") / str(recipe_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    for image in images:
        if not image or not image.filename:
            continue

        original_name = secure_filename(image.filename)
        extension = Path(original_name).suffix.lower()

        if extension not in ALLOWED_IMAGE_EXTENSIONS:
            abort(400)

        filename = f"{uuid4().hex}{extension}"

        image.save(upload_dir / filename)

        recipe_service.add_image(
            recipe_id,
            filename,
            con
        )

@bp.route("/recipes/edit/<int:recipe_id>", methods=["GET", "POST"])
@require_login
@require_csrf
def edit_recipe(recipe_id):
    """
    Edit recipe route
    Args:
        recipe_id(int) : id of recipe
    """
    found_recipe = recipe_service.get_recipe(recipe_id)
    if found_recipe["creator_id"] != session["user_id"]:
        abort(403)

    if request.method == "GET":
        return render_template(
            "recipes/recipe_form.html",
            recipe=found_recipe,
            recipe_ingredients=recipe_service.get_ingredients(recipe_id),
            recipe_steps=recipe_service.get_recipe_steps(recipe_id),
            recipe_images=recipe_service.get_images(recipe_id),
            food_types=FOOD_TYPES,
            dietary_requirements=DIETARY_REQUIREMENTS,
            units=UNITS
        )

    title = request.form["title"]
    description = request.form["description"]
    food_type = request.form["food_type"]
    dietary_requirements = request.form["dietary_requirements"]
    servings = request.form["servings"]
    preparation_time = request.form["preparation_time"]

    con = db_utils.get_connection()
    try:
        recipe_service.update_recipe(
            recipe_id,
            title,
            description,
            food_type,
            dietary_requirements,
            servings,
            preparation_time,
            con
        )

        recipe_service.create_ingredients(
            recipe_id,
            ingredients=request.form.getlist("ingredient"),
            amounts=request.form.getlist("ingredient_amount"),
            units=request.form.getlist("ingredient_unit"),
            con=con
        )

        recipe_service.create_recipe_steps(
            recipe_id,
            steps=request.form.getlist("recipe_step"),
            con=con
        )

        # remove first, create new ones.
        removed_images = request.form.getlist("remove_image")
        for image_id in removed_images:
            recipe_service.remove_image(
                recipe_id,
                image_id,
                con
            )

        create_recipe_images(
            recipe_id,
            images=request.files.getlist("images"),
            con=con
        )

        con.commit()
    except sqlite3.IntegrityError:
        con.rollback()
        abort(403)

    except Exception:
        con.rollback()
        raise

    finally:
        con.close()

    return redirect(url_for("recipes.recipe", recipe_id=recipe_id))


@bp.route("/recipes/remove/<int:recipe_id>", methods=["POST"])
def remove_recipe(recipe_id):
    """
    Remove recipe route
    Args:
        recipe_id(int) : id of recipe
    """
    recipe_service.delete_recipe(recipe_id)
    return redirect(url_for("recipes"))


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

    comment = request.form["comment"]
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

    recipe_id = comment["recipe_id"]
    value = request.form["comment"]
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

    rating = request.form["rating"]
    recipe_service.add_rating(recipe_id, session["user_id"], rating)
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

    recipe_id = rating["recipe_id"]
    rating = request.form["rating"]
    recipe_service.update_rating(rating_id, rating)
    return redirect(url_for("recipes.recipe", recipe_id=recipe_id))
