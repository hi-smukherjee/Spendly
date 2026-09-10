import math
import secrets
from datetime import timedelta
from functools import wraps

from flask import Flask, abort, render_template, request, redirect, session, url_for
from werkzeug.security import check_password_hash

from database.db import (
    get_expense_by_id,
    get_expenses_by_user,
    get_user_by_email,
    init_db,
    seed_db,
    update_expense,
)

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


# Fixed category set — used both to populate the edit form's <select> and to validate
# submitted category values server-side (a <select> is a UI hint, not a guarantee).
EXPENSE_CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]


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
    expenses = get_expenses_by_user(session["user_id"])

    total_spent = sum(expense["amount"] for expense in expenses)
    totals_by_category = {}
    for expense in expenses:
        totals_by_category[expense["category"]] = (
            totals_by_category.get(expense["category"], 0) + expense["amount"]
        )
    top_category = max(totals_by_category, key=totals_by_category.get) if expenses else None

    return render_template(
        "profile.html",
        expenses=expenses,
        total_spent=total_spent,
        top_category=top_category,
    )


@app.route("/analytics")
@login_required
def analytics():
    return render_template("coming_soon.html")


@app.route("/expenses/add")
@login_required
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(id):
    expense = get_expense_by_id(id, session["user_id"])
    if expense is None:
        abort(404)

    if request.method == "GET":
        session["csrf_token"] = secrets.token_hex(16)
        return render_template(
            "edit_expense.html",
            expense=expense,
            categories=EXPENSE_CATEGORIES,
            csrf_token=session["csrf_token"],
        )

    form = {
        "amount": request.form.get("amount", "").strip(),
        "category": request.form.get("category", "").strip(),
        "date": request.form.get("date", "").strip(),
        "description": request.form.get("description", "").strip(),
    }
    submitted_token = request.form.get("csrf_token", "")

    error = None
    amount_value = None
    if not submitted_token or submitted_token != session.get("csrf_token"):
        error = "Something went wrong. Please try again."
    elif not form["date"]:
        error = "Date is required."
    elif form["category"] not in EXPENSE_CATEGORIES:
        error = "Please choose a valid category."
    else:
        try:
            amount_value = float(form["amount"])
            if not math.isfinite(amount_value) or amount_value <= 0:
                error = "Amount must be greater than zero."
        except ValueError:
            error = "Amount must be a number."

    if error:
        session["csrf_token"] = secrets.token_hex(16)
        return render_template(
            "edit_expense.html",
            expense=expense,
            categories=EXPENSE_CATEGORIES,
            csrf_token=session["csrf_token"],
            error=error,
            form=form,
        )

    update_expense(
        id, session["user_id"], amount_value, form["category"], form["date"],
        form["description"] or None,
    )
    return redirect(url_for("profile"))


@app.route("/expenses/<int:id>/delete")
@login_required
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
