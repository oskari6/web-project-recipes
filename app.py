"""App entry point"""

from datetime import datetime
import time
import os

from flask import g, render_template, Flask, request
import markupsafe
from db import utils as db_utils
from routes import recipe_routes
from routes import user_routes
from routes import auth_routes
from utils.decorators import get_csrf_token

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024
# add all the routes
app.register_blueprint(recipe_routes.bp)
app.register_blueprint(user_routes.bp)
app.register_blueprint(auth_routes.bp)

# initialize database tables and indexes
db_utils.init_db()

# this is for session id:s
app.secret_key = os.environ["SECRET_KEY"]

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
    return render_template("errors/404.html"), 404

@app.errorhandler(403)
def forbidden(_error):
    """
    Error route
    """
    return render_template("errors/403.html"), 403

@app.errorhandler(401)
def unauthorized(error):
    """
    Error route
    """
    return render_template("errors/401.html", error=error), 401

@app.errorhandler(500)
def internal_server(_error):
    """
    Error route
    """
    return render_template("errors/500.html"), 500

@app.errorhandler(400)
@app.errorhandler(413)
def invalid_request(error):
    """Show input errors with their correct HTTP status."""
    return render_template("errors/400.html", error=error.description), error.code
