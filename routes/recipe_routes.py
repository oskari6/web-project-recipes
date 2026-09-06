import math
from pathlib import Path
from uuid import uuid4

from flask import abort, redirect, request, session, Blueprint, render_template, url_for
from flask import render_template
import sqlite3
from services import recipe_service
from services import user_service
from utils.constants import ALLOWED_IMAGE_EXTENSIONS, DIETARY_REQUIREMENTS, FOOD_TYPES, UNITS
from utils.decorators import require_csrf, require_login
from werkzeug.utils import secure_filename
from db import utils as db_utils

bp = Blueprint("recipes", __name__)


@bp.route("/recipes/<int:page>")
def recipes(page=1):
    page_size = 10
    query = request.args.get("query", "").strip()

    recipe_count = recipe_service.recipe_count(query)
    page_count = math.ceil(recipe_count / page_size)
    page_count = max(page_count, 1)

    if page < 1:
        return redirect(url_for("recipes.recipes", page=1))
    if page > page_count:
        return redirect(url_for("recipes.recipes", page=page_count, query=query))

    recipes = recipe_service.get_recipes(page, page_size, query=query)
    return render_template("/recipes/recipes.html",
        page=page,
        page_count=page_count,
        recipes=recipes,
        query=query
    )


@bp.route("/recipes/recipe/<int:recipe_id>")
def recipe(recipe_id):
    recipe = recipe_service.get_recipe(recipe_id)
    if not recipe:
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
    user = user_service.get_user(recipe["creator_id"])

    return render_template(
        "/recipes/recipe.html",
        recipe=recipe,
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

    ingredients = request.form.getlist("ingredient")
    amounts = request.form.getlist("ingredient_amount")
    units = request.form.getlist("ingredient_unit")

    steps = request.form.getlist("recipe_step")
    images = request.files.getlist("images")

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

        for ingredient, amount, unit in zip(
            ingredients,
            amounts,
            units
        ):
            if not ingredient.strip():
                continue
            recipe_service.add_ingredient(
                new_recipe_id,
                ingredient,
                amount,
                unit,
                con
            )

        step_number = 1
        for instruction in steps:
            if not instruction.strip():
                continue
            recipe_service.add_step(
                new_recipe_id,
                step_number,
                instruction,
                con
            )
            step_number += 1

        upload_dir = Path("static/uploads/recipes") / str(new_recipe_id)
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
                new_recipe_id,
                filename,
                con
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


@bp.route("/recipes/edit/<int:recipe_id>", methods=["GET", "POST"])
@require_login
@require_csrf
def edit_recipe(recipe_id):
    recipe = recipe_service.get_recipe(recipe_id)
    if recipe["creator_id"] != session["user_id"]:
        abort(403)

    if request.method == "GET":
        return render_template(
            "recipes/recipe_form.html",
            recipe=recipe,
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

    ingredients = request.form.getlist("ingredient")
    amounts = request.form.getlist("ingredient_amount")
    units = request.form.getlist("ingredient_unit")

    steps = request.form.getlist("recipe_step")
    images = request.files.getlist("images")

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

        recipe_service.remove_all_ingredients(recipe_id, con)
        for ingredient, amount, unit in zip(
                ingredients,
                amounts,
                units
            ):
                if not ingredient.strip():
                    continue

                recipe_service.add_ingredient(
                    recipe_id,
                    ingredient,
                    amount,
                    unit,
                    con
                )

        # Update steps
        recipe_service.remove_all_steps(recipe_id, con)
        step_number = 1

        for instruction in steps:
            if not instruction.strip():
                continue

            recipe_service.add_step(
                recipe_id,
                step_number,
                instruction,
                con
            )

            step_number += 1

        removed_images = request.form.getlist("remove_image")
        for image_id in removed_images:
            recipe_service.remove_image(
                recipe_id,
                image_id,
                con
            )

        # Add newly uploaded images
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
    recipe_service.delete_recipe(recipe_id)
    return redirect(url_for("recipes"))


@bp.route("/recipes/create/comment/<int:recipe_id>", methods=["POST"])
@require_login
@require_csrf
def create_comment(recipe_id):
    recipe = recipe_service.get_recipe(recipe_id)
    if not recipe:
        abort(404)

    comment = request.form["comment"]
    recipe_service.add_comment(recipe_id, session["user_id"], comment)

    return redirect(url_for("recipes.recipe", recipe_id=recipe_id))


@bp.route("/recipes/edit/comment/<int:comment_id>", methods=["POST"])
@require_login
@require_csrf
def edit_comment(comment_id):
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
    recipe = recipe_service.get_recipe(recipe_id)
    if not recipe:
        abort(404)

    rating = request.form["rating"]
    recipe_service.add_rating(recipe_id, session["user_id"], rating)
    return redirect(url_for("recipes.recipe", recipe_id=recipe_id))


@bp.route("/recipes/edit/rating/<int:rating_id>", methods=["POST"])
@require_login
@require_csrf
def edit_rating(rating_id):
    rating = recipe_service.get_rating_by_id(rating_id)
    if not rating:
        abort(404)

    recipe_id = rating["recipe_id"]
    rating = request.form["rating"]
    recipe_service.update_rating(rating_id, rating)
    return redirect(url_for("recipes.recipe", recipe_id=recipe_id))
