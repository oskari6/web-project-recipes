"""Server-side validation shared by creation and update routes."""
import math
from itertools import zip_longest

from werkzeug.security import check_password_hash

import users
import recipes
from config import (UNITS)

def validate_user(username, password, password_confirm, user_id=None):
    """
    Check account fields; an empty password keeps an existing account's password.
    Args:
        username(str): username
        password(str): password
        password_confirm(str): password confirmation
        user_id(int): optional user id
    Returns:
        errors(list[str]): all validation errors; empty when valid
    """
    errors = []
    if not username or not username.strip() or len(username) > 16:
        errors.append("Username must contain 1–16 characters.")
    if user_id is None and not password:
        errors.append("Password is required.")
    if len(password) > 64 or (password and not password.strip()):
        errors.append("Password must contain 1–64 characters and cannot be only whitespace.")
    if password != password_confirm:
        errors.append("Passwords did not match.")
    existing_user = users.get_user_by_username(username)
    if existing_user and existing_user["id"] != user_id:
        errors.append("Username is already reserved.")
    return errors


def validate_auth_register(username, password, password_confirm):
    """
    Validate a new account.
    Args:
        username(str): username
        password(str): password
        password_confirm(str): password confirmation
    Returns:
        errors(list[str]): all validation errors; empty when valid
    """
    return validate_user(username, password, password_confirm)


def validate_auth_login(username, password):
    """
    Validate credentials without revealing whether an account exists.
    Args:
        username(str): username
        password(str): password
    Returns:
        errors(list[str]): all validation errors; empty when valid
        """
    if not username or not password or len(username) > 16 or len(password) > 64:
        return ["Wrong username or password."]
    user = users.get_user_by_username(username)
    if not user or not check_password_hash(user["password_hash"], password):
        return ["Wrong username or password."]
    return []

def is_positive_integer(value):
    """Accept optional positive integers that fit in SQLite's integer storage."""
    return (not value or (value.isascii() and value.isdecimal()
                         and len(value) <= 19 and 0 < int(value) <= 2**63 - 1))


def validate_recipe(form):
    """
    Validate recipe metadata and the parallel ingredient/step fields.
    Args:
        form({}): the whole recipe form object
    Returns:
        errors(list[str]): all validation errors; empty when valid
    """
    errors = []
    food_types = [
        str(row["id"]) for row in recipes.get_food_types()
    ]

    dietary_requirements = [
        str(row["id"]) for row in recipes.get_dietary_requirements()
    ]

    for name, limit in (("title", 200), ("description", 10000)):
        value = form.get(name, "").strip()
        if not value or len(value) > limit:
            errors.append(f"{name.capitalize()} must contain 1–{limit} characters.")
    for name, choices in (
        ("food_type_id", food_types),
        ("dietary_requirement_id", dietary_requirements),
    ):
        if form.get(name, "") not in ["", *choices]:
            errors.append(f"Invalid {name}.")
    for name in ("servings", "preparation_time"):
        if not is_positive_integer(form.get(name, "")):
            errors.append(f"{name.replace('_', ' ').capitalize()} must be a positive whole number.")
    errors.extend(validate_ingredients(form))
    steps = form.getlist("recipe_step")
    if not 1 <= len(steps) <= 10 or not any(step.strip() for step in steps):
        errors.append("Provide 1–10 instruction steps.")
    if any(len(step.strip()) > 5000 for step in steps):
        errors.append("Each instruction must be at most 5000 characters.")
    return errors


def validate_ingredients(form):
    """
    Reject truncated lists, invalid units and nonfinite or nonpositive amounts.
    Args:
        form({}): the whole recipe form object
    Returns:
        errors(list[str]): all validation errors; empty when valid
    """
    errors = []
    ingredients = form.getlist("ingredient")
    amounts = form.getlist("ingredient_amount")
    units = form.getlist("ingredient_unit")
    if not 1 <= len(ingredients) <= 10 or not len(ingredients) == len(amounts) == len(units):
        errors.append("Provide 1–10 complete ingredient rows.")
    if not any(ingredient.strip() for ingredient in ingredients):
        errors.append("Provide at least one ingredient.")
    for row, (ingredient, amount, unit) in enumerate(
            zip_longest(ingredients, amounts, units, fillvalue=""), start=1):
        if not ingredient.strip() and (amount.strip() or unit):
            errors.append(f"Ingredient row {row}: an amount or unit needs an ingredient name.")
        if len(ingredient.strip()) > 200:
            errors.append(f"Ingredient row {row}: names must be at most 200 characters.")
        if unit not in ["", *UNITS]:
            errors.append(f"Ingredient row {row}: invalid unit.")
        if amount.strip():
            try:
                number = float(amount)
            except ValueError:
                errors.append(f"Ingredient row {row}: amounts must be positive numbers.")
            else:
                if not math.isfinite(number) or number <= 0:
                    errors.append(f"Ingredient row {row}: amounts must be finite positive numbers.")
    return errors


def validate_comment(value):
    """
    Validate new and edited comments.
    Args:
        value(int): comment
    Returns:
        errors(list[str]): all validation errors; empty when valid
    """
    if not value.strip() or len(value.strip()) > 5000:
        return ["Comments must contain 1–5000 characters."]
    return []


def validate_rating(value):
    """
    Validate new and edited ratings.
    Args:
        value(int): rating value
    Returns:
        errors(list[str]): all validation errors; empty when valid
    """
    if value not in {"1", "2", "3", "4", "5"}:
        return ["Rating must be a whole number from 1 to 5."]
    return []
