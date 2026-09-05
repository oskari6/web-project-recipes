from functools import wraps

from flask import abort, request, session
import secrets

def get_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(32)

    return session["csrf_token"]

def require_csrf(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        token = request.form.get("csrf_token")

        if not token or not secrets.compare_digest(
            token, session.get("csrf_token", "")
        ):
            abort(403)

        return func(*args, **kwargs)

    return wrapper

def require_login(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            abort(401)

        return func(*args, **kwargs)

    return wrapper
