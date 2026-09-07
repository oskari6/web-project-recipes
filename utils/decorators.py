"""App's decorators"""
from functools import wraps
import secrets

from flask import abort, request, session

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
                token, session.get("csrf_token", "")
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

        return func(*args, **kwargs)

    return wrapper
