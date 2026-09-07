"""App entry point"""

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
# add all the routes
app.register_blueprint(recipe_routes.bp)
app.register_blueprint(user_routes.bp)
app.register_blueprint(auth_routes.bp)

# initialize database tables and indexes
db_utils.init_db()

# this is for session id:s
app.secret_key = os.environ["SECRET_KEY"]

# for cleaning html markup for client
@app.template_filter()
def show_lines(content):
    """
    Utility to show linebreaks
    """
    content = str(markupsafe.escape(content))
    content = content.replace("\n", "<br />")
    return markupsafe.Markup(content)

# csrf handling processor
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
    Initial page route
    """
    return render_template("home.html")

@app.errorhandler(404)
def not_found():
    """
    Error route
    """
    return render_template("errors/404.html"), 404


@app.errorhandler(403)
def forbidden():
    """
    Error route
    """
    return render_template("errors/403.html"), 403


@app.errorhandler(401)
def unauthorized():
    """
    Error route
    """
    return render_template("errors/401.html"), 401

@app.errorhandler(500)
def internal_server():
    """
    Error route
    """
    return render_template("errors/500.html"), 500
