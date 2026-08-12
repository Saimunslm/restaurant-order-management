from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_user, logout_user, current_user, login_required
from app.models.staff_user import StaffUser
from app.extensions import db

kitchen_bp = Blueprint("kitchen", __name__, url_prefix="/kitchen")


def kitchen_login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ["kitchen", "admin"]:
            return redirect(url_for("kitchen.login"))
        return f(*args, **kwargs)
    return decorated


@kitchen_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated and current_user.role in ["kitchen", "admin"]:
        return redirect(url_for("kitchen.dashboard"))

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = StaffUser.query.filter_by(email=email, role="kitchen").first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("kitchen.dashboard"))
        flash("Invalid credentials", "error")

    return render_template("kitchen/login.html")


@kitchen_bp.route("/dashboard")
@kitchen_login_required
def dashboard():
    if current_user.role not in ["kitchen", "admin"]:
        abort(403)
    return render_template("kitchen/dashboard.html")


@kitchen_bp.route("/logout")
@kitchen_login_required
def logout():
    logout_user()
    return redirect(url_for("kitchen.login"))
