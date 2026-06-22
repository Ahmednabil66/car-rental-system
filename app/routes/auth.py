from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user
from sqlalchemy import or_
from app.models import db, User
from app.forms import require_text


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("cars.home"))

    if request.method == "POST":
        try:
            name = require_text(request.form.get("name"), "Name", max_len=120)
            username = require_text(request.form.get("username"), "Username", min_len=3, max_len=80)
            email = require_text(request.form.get("email"), "Email", max_len=120)
            phone = (request.form.get("phone") or "").strip()
            password = require_text(request.form.get("password"), "Password", min_len=6)
            confirm_password = request.form.get("confirm_password") or ""
            if password != confirm_password:
                raise ValueError("Password confirmation does not match.")
            if User.query.filter(or_(User.username == username, User.email == email)).first():
                raise ValueError("Username or email already exists.")

            user = User(name=name, username=username, email=email, phone=phone, role="customer")
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Account created successfully.", "success")
            return redirect(url_for("rentals.dashboard"))
        except ValueError as exc:
            flash(str(exc), "danger")

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("cars.home"))

    if request.method == "POST":
        identifier = (request.form.get("identifier") or "").strip()
        password = request.form.get("password") or ""
        user = User.query.filter(or_(User.username == identifier, User.email == identifier)).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Logged in successfully.", "success")
            next_page = request.args.get("next")
            if user.is_admin:
                return redirect(next_page or url_for("admin.dashboard"))
            return redirect(next_page or url_for("rentals.dashboard"))
        flash("Invalid username/email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("cars.home"))
