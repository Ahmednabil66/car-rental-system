from functools import wraps
from flask import abort, redirect, url_for, flash
from flask_login import current_user


def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in first.", "warning")
            return redirect(url_for("auth.login"))
        if not current_user.is_admin:
            abort(403)
        return view_func(*args, **kwargs)
    return wrapper


def customer_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in first.", "warning")
            return redirect(url_for("auth.login"))
        if not current_user.is_customer:
            abort(403)
        return view_func(*args, **kwargs)
    return wrapper
