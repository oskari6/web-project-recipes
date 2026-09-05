from flask import Flask, abort, request, session
from flask import render_template
from flask import g
import time
import markupsafe
import os
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
    content = str(markupsafe.escape(content))
    content = content.replace("\n", "<br />")
    return markupsafe.Markup(content)

# csrf handling processor
@app.context_processor
def inject_csrf_token():
    return {"csrf_token": get_csrf_token()}

# performance metrics
@app.before_request
def before_request():
    g.start_time = time.perf_counter()

@app.after_request
def after_request(response):
    elapsed_time = time.perf_counter() - g.start_time
    print(f"{request.method} {request.path}: {elapsed_time:.3f}s")
    return response

# entry point
@app.route("/")
def home():
    return render_template("home.html")

@app.errorhandler(404)
def not_found(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(403)
def forbidden(error):
    return render_template("errors/403.html"), 403


@app.errorhandler(401)
def unauthorized(error):
    return render_template("errors/401.html"), 401

@app.errorhandler(500)
def unauthorized(error):
    return render_template("errors/500.html"), 500