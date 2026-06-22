from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user
from app.models import db, Rental, Feedback
from app.decorators import customer_required
from app.forms import parse_int


feedback_bp = Blueprint("feedback", __name__, url_prefix="/feedback")


@feedback_bp.route("/rental/<int:rental_id>/add", methods=["GET", "POST"])
@customer_required
def add(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    if rental.customer_id != current_user.id:
        abort(403)
    if rental.status != "completed":
        flash("Feedback can only be added after a completed rental.", "danger")
        return redirect(url_for("rentals.dashboard"))
    if rental.feedback:
        flash("Feedback already exists for this rental.", "warning")
        return redirect(url_for("rentals.dashboard"))

    if request.method == "POST":
        try:
            rating = parse_int(request.form.get("rating"), "Rating", minimum=1, maximum=5)
            comments = (request.form.get("comments") or "").strip()
            feedback = Feedback(
                rental_id=rental.id,
                customer_id=current_user.id,
                car_id=rental.car_id,
                rating=rating,
                comments=comments,
            )
            db.session.add(feedback)
            db.session.commit()
            flash("Thank you for your feedback.", "success")
            return redirect(url_for("rentals.dashboard"))
        except ValueError as exc:
            flash(str(exc), "danger")

    return render_template("feedback/add.html", rental=rental)
