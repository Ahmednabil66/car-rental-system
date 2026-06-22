from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user
from app.models import Rental, Payment
from app.decorators import customer_required
from app.forms import PAYMENT_METHODS, PAYMENT_STATUS, validate_choice
from app.services.payment_service import PaymentService


payments_bp = Blueprint("payments", __name__, url_prefix="/payments")


@payments_bp.route("/rental/<int:rental_id>", methods=["GET", "POST"])
@customer_required
def pay(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    if rental.customer_id != current_user.id:
        abort(403)

    if request.method == "POST":
        try:
            method = validate_choice(request.form.get("method"), PAYMENT_METHODS, "payment method")
            status = validate_choice(request.form.get("status"), PAYMENT_STATUS, "payment status")
            PaymentService.create_or_update_payment(rental, method, status)
            flash("Payment saved successfully.", "success")
            return redirect(url_for("rentals.dashboard"))
        except ValueError as exc:
            flash(str(exc), "danger")

    return render_template("payments/pay.html", rental=rental, methods=PAYMENT_METHODS, statuses=PAYMENT_STATUS)
