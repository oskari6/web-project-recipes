"""App's decorators"""
from functools import wraps
import secrets

from flask import abort, request, session
from services import user_service

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
