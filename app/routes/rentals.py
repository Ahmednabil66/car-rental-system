from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import current_user
from app.models import db, Car, Rental
from app.decorators import customer_required
from app.forms import parse_date
from app.services.rental_service import RentalService


rentals_bp = Blueprint("rentals", __name__, url_prefix="/rentals")
customer_bp = Blueprint("customer", __name__, url_prefix="/customer")


def _dashboard_response():
    rentals = Rental.query.filter_by(customer_id=current_user.id).order_by(Rental.booking_date.desc()).all()
    return render_template("rentals/dashboard.html", rentals=rentals)


@rentals_bp.route("/dashboard")
@customer_required
def dashboard():
    return _dashboard_response()


@customer_bp.route("/dashboard")
@customer_required
def customer_dashboard():
    return _dashboard_response()


@rentals_bp.route("/book/<int:car_id>", methods=["GET", "POST"])
@customer_required
def book(car_id):
    car = Car.query.get_or_404(car_id)
    insurance_options = RentalService.get_available_insurances_for_car(car.id)
    quote = None

    if request.method == "POST":
        try:
            start_date = parse_date(request.form.get("start_date"), "start date")
            end_date = parse_date(request.form.get("end_date"), "end date")
            insurance_id = request.form.get("insurance_id") or None
            discount_code = request.form.get("discount_code") or None

            if request.form.get("action") == "quote":
                quote = RentalService.price_quote(car, start_date, end_date, insurance_id, discount_code)
                flash("Quote calculated. Review it below before confirming.", "info")
            else:
                rental = RentalService.create_rental(current_user, car.id, start_date, end_date, insurance_id, discount_code)
                flash("Rental booking created. Please choose your payment method.", "success")
                return redirect(url_for("payments.pay", rental_id=rental.id))
        except ValueError as exc:
            flash(str(exc), "danger")

    return render_template("rentals/book.html", car=car, insurance_options=insurance_options, quote=quote)


@rentals_bp.route("/<int:rental_id>")
@customer_required
def details(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    if rental.customer_id != current_user.id:
        abort(403)
    return render_template("rentals/details.html", rental=rental)


@rentals_bp.route("/<int:rental_id>/cancel", methods=["POST"])
@customer_required
def cancel(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    try:
        RentalService.cancel_pending_rental(rental, current_user)
        flash("Rental cancelled successfully.", "success")
    except (ValueError, PermissionError) as exc:
        flash(str(exc), "danger")
    return redirect(url_for("rentals.dashboard"))
