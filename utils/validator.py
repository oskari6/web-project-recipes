"""Server-side validation shared by creation and update routes."""
import math

from werkzeug.security import check_password_hash

from services import user_service
from utils.constants import (DIETARY_REQUIREMENTS, FOOD_TYPES, UNITS)


def validate_user(username, password, password_confirm, user_id=None):
    """
    Check account fields; an empty password keeps an existing account's password.
    Args:
        username(str): username
        password(str): password
        password_confirm(str): password confirmation
        user_id(int): optional user id
    Returns:
        errors(str | None): possible errors
    """
    if not username or not username.strip() or len(username) > 16:
        return "Username must contain 1–16 characters."
    if user_id is None and not password.strip():
        return "Password is required."
    if len(password) > 64 or (password and not password.strip()):
        return "Password must contain 1–64 characters and cannot be only whitespace."
    if password != password_confirm:
        return "Passwords did not match."
    existing_user = user_service.get_user_by_username(username)
    if existing_user and existing_user["id"] != user_id:
        return "Username is already reserved."
    return None


def validate_auth_register(username, password, password_confirm):
    """
    Validate a new account.
    Args:
        username(str): username
        password(str): password
        password_confirm(str): password confirmation
    Returns:
        errors(str | None): possible errors
    """
    return validate_user(username, password, password_confirm)


def validate_auth_login(username, password):
    """
    Validate credentials without revealing whether an account exists.
    Args:
        username(str): username
        password(str): password
    Returns:
        errors(str | None): possible errors
        """
    if not username or not password or len(username) > 16 or len(password) > 64:
        return "Wrong username or password."
    user = user_service.get_user_by_username(username)
    if not user or not check_password_hash(user["password_hash"], password):
        return "Wrong username or password."
    return None

def is_positive_integer(value):
    """
    Accept optional positive integers that fit in SQLite's integer storage.
    Args:
        username(str): username
        password(str): password
        password_confirm(str): password confirmation
    Returns:
        errors(str | None): possible errors    
    """
    return (not value or (value.isascii() and value.isdecimal()
                         and len(value) <= 19 and 0 < int(value) <= 2**63 - 1))


def validate_recipe(form):
    """
    Validate recipe metadata and the parallel ingredient/step fields.
    Args:
        form({}): the whole recipe form object
    Returns:
        errors(str | None): possible errors
    """
    for name, limit in (("title", 200), ("description", 10000)):
        value = form.get(name, "").strip()
        if not value or len(value) > limit:
            return f"{name.capitalize()} must contain 1–{limit} characters."
    for name, choices in (("food_type", FOOD_TYPES),
        ("dietary_requirements", DIETARY_REQUIREMENTS)):
        if form.get(name, "") not in ["", *choices]:
            return f"Invalid {name.replace('_', ' ')}."
    for name in ("servings", "preparation_time"):
        if not is_positive_integer(form.get(name, "")):
            return f"{name.replace('_', ' ').capitalize()} must be a positive whole number."
    error = validate_ingredients(form)
    if error:
        return error
    steps = form.getlist("recipe_step")
    if not 1 <= len(steps) <= 10 or not any(step.strip() for step in steps):
        return "Provide 1–10 instruction steps."
    if any(len(step.strip()) > 5000 for step in steps):
        return "Each instruction must be at most 5000 characters."
    return None


def validate_ingredients(form):
    """
    Reject truncated lists, invalid units and nonfinite or nonpositive amounts.
    Args:
        form({}): the whole recipe form object
    Returns:
        errors(str | None): possible errors    
    """
    ingredients = form.getlist("ingredient")
    amounts = form.getlist("ingredient_amount")
    units = form.getlist("ingredient_unit")
    if not 1 <= len(ingredients) <= 10 or not len(ingredients) == len(amounts) == len(units):
        return "Provide 1–10 complete ingredient rows."
    if not any(ingredient.strip() for ingredient in ingredients):
        return "Provide at least one ingredient."
    for ingredient, amount, unit in zip(ingredients, amounts, units):
        if not ingredient.strip() and (amount.strip() or unit):
            return "An amount or unit needs an ingredient name."
        if len(ingredient.strip()) > 200:
            return "Ingredient names must be at most 200 characters."
        if unit not in ["", *UNITS]:
            return "Invalid ingredient unit."
        if amount.strip():
            try:
                number = float(amount)
            except ValueError:
                return "Ingredient amounts must be positive numbers."
            if not math.isfinite(number) or number <= 0:
                return "Ingredient amounts must be finite positive numbers."
    return None


def validate_comment(value):
    """
    Validate new and edited comments.
    Args:
        value(int): comment
    Returns:
        errors(str | None): possible errors    
    """
    if not value.strip() or len(value.strip()) > 5000:
        return "Comments must contain 1–5000 characters."
    return None


def validate_rating(value):
    """
    Validate new and edited ratings.
    Args:
        value(int): rating value
    Returns:
        errors(str | None): possible errors
    """
    if value not in {"1", "2", "3", "4", "5"}:
        return "Rating must be a whole number from 1 to 5."
    return None
