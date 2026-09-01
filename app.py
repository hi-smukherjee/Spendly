import secrets
from datetime import timedelta
from functools import wraps

from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import check_password_hash

from database.db import get_user_by_email, init_db, seed_db

app = Flask(__name__)

# Dev-only secret key — signs the session cookie. In production this must come from an
# environment variable instead of living in source.
app.secret_key = "dev-secret-key-change-in-production"

app.config.update(
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,  # flip to True once served over HTTPS
)

with app.app_context():
    init_db()
    seed_db()


def login_required(view):
    """Redirect anonymous visitors to the login page instead of running the view."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        session["csrf_token"] = secrets.token_hex(16)
        return render_template("login.html", csrf_token=session["csrf_token"])

    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")
    submitted_token = request.form.get("csrf_token", "")

    error = None
    if not submitted_token or submitted_token != session.get("csrf_token"):
        error = "Invalid email or password."
    elif not email:
        error = "Email is required."
    elif not password:
        error = "Password is required."
    else:
        user = get_user_by_email(email)
        if user is None or not check_password_hash(user["password_hash"], password):
            error = "Invalid email or password."

    if error:
        session["csrf_token"] = secrets.token_hex(16)
        return render_template("login.html", csrf_token=session["csrf_token"], error=error)

    session.clear()
    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    session.permanent = True
    return redirect(url_for("profile"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/profile")
@login_required
def profile():
    return "Profile page — coming in Step 4"


@app.route("/expenses/add")
@login_required
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
@login_required
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
@login_required
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
