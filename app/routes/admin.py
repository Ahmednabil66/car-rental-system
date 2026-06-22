from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from app.models import db, User, Car, Location, Rental, Payment, Discount, Insurance, Maintenance, Feedback
from app.decorators import admin_required
from app.forms import (
    CAR_STATUS,
    CAR_TYPES,
    RENTAL_STATUS,
    PAYMENT_STATUS,
    DISCOUNT_TYPES,
    MAINTENANCE_STATUS,
    parse_date,
    parse_float,
    require_text,
    validate_choice,
)
from app.services.rental_service import RentalService
from app.services.payment_service import PaymentService
from app.services.report_service import ReportService


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


def _get_location(location_id):
    if not location_id:
        return None
    return Location.query.get(int(location_id))


@admin_bp.route("/")
@admin_required
def dashboard():
    summary = ReportService.dashboard_summary()
    latest_rentals = Rental.query.order_by(Rental.booking_date.desc()).limit(6).all()
    latest_payments = Payment.query.order_by(Payment.date.desc()).limit(6).all()
    return render_template("admin/dashboard.html", summary=summary, latest_rentals=latest_rentals, latest_payments=latest_payments)


@admin_bp.route("/cars")
@admin_required
def cars():
    cars_list = Car.query.order_by(Car.id.desc()).all()
    return render_template("admin/cars.html", cars=cars_list)


@admin_bp.route("/cars/create", methods=["GET", "POST"])
@admin_required
def car_create():
    locations = Location.query.order_by(Location.city).all()
    discounts = Discount.query.order_by(Discount.code).all()
    if request.method == "POST":
        try:
            car = Car(
                brand=require_text(request.form.get("brand"), "Brand", max_len=80),
                model=require_text(request.form.get("model"), "Model", max_len=80),
                car_type=validate_choice(request.form.get("car_type"), CAR_TYPES, "car type"),
                gps=request.form.get("gps") == "on",
                daily_rate=parse_float(request.form.get("daily_rate"), "Daily rate", minimum=0),
                availability_status=validate_choice(request.form.get("availability_status"), CAR_STATUS, "availability status"),
                description=(request.form.get("description") or "").strip(),
                image_url=(request.form.get("image_url") or "").strip(),
                location_id=int(request.form.get("location_id")) if request.form.get("location_id") else None,
                discount_id=int(request.form.get("discount_id")) if request.form.get("discount_id") else None,
            )
            db.session.add(car)
            db.session.commit()
            flash("Car created successfully.", "success")
            return redirect(url_for("admin.cars"))
        except ValueError as exc:
            flash(str(exc), "danger")
    return render_template("admin/car_form.html", car=None, locations=locations, discounts=discounts, car_types=CAR_TYPES, statuses=CAR_STATUS)


@admin_bp.route("/cars/<int:car_id>/edit", methods=["GET", "POST"])
@admin_required
def car_edit(car_id):
    car = Car.query.get_or_404(car_id)
    locations = Location.query.order_by(Location.city).all()
    discounts = Discount.query.order_by(Discount.code).all()
    if request.method == "POST":
        try:
            car.brand = require_text(request.form.get("brand"), "Brand", max_len=80)
            car.model = require_text(request.form.get("model"), "Model", max_len=80)
            car.car_type = validate_choice(request.form.get("car_type"), CAR_TYPES, "car type")
            car.gps = request.form.get("gps") == "on"
            car.daily_rate = parse_float(request.form.get("daily_rate"), "Daily rate", minimum=0)
            car.availability_status = validate_choice(request.form.get("availability_status"), CAR_STATUS, "availability status")
            car.description = (request.form.get("description") or "").strip()
            car.image_url = (request.form.get("image_url") or "").strip()
            car.location_id = int(request.form.get("location_id")) if request.form.get("location_id") else None
            car.discount_id = int(request.form.get("discount_id")) if request.form.get("discount_id") else None
            db.session.commit()
            flash("Car updated successfully.", "success")
            return redirect(url_for("admin.cars"))
        except ValueError as exc:
            flash(str(exc), "danger")
    return render_template("admin/car_form.html", car=car, locations=locations, discounts=discounts, car_types=CAR_TYPES, statuses=CAR_STATUS)


@admin_bp.route("/cars/<int:car_id>/delete", methods=["POST"])
@admin_required
def car_delete(car_id):
    car = Car.query.get_or_404(car_id)
    if car.rentals:
        flash("Cannot delete a car with rental records. Mark it unavailable instead.", "danger")
    else:
        db.session.delete(car)
        db.session.commit()
        flash("Car deleted successfully.", "success")
    return redirect(url_for("admin.cars"))


@admin_bp.route("/customers")
@admin_required
def customers():
    customers_list = User.query.filter_by(role="customer").order_by(User.name).all()
    return render_template("admin/customers.html", customers=customers_list)


@admin_bp.route("/customers/<int:user_id>")
@admin_required
def customer_details(user_id):
    customer = User.query.filter_by(id=user_id, role="customer").first_or_404()
    return render_template("admin/customer_details.html", customer=customer)


@admin_bp.route("/rentals")
@admin_required
def rentals():
    rentals_list = Rental.query.order_by(Rental.booking_date.desc()).all()
    return render_template("admin/rentals.html", rentals=rentals_list, statuses=RENTAL_STATUS)


@admin_bp.route("/rentals/<int:rental_id>/status", methods=["POST"])
@admin_required
def rental_status(rental_id):
    rental = Rental.query.get_or_404(rental_id)
    try:
        status = validate_choice(request.form.get("status"), RENTAL_STATUS, "rental status")
        RentalService.update_rental_status(rental, status)
        flash("Rental status updated.", "success")
    except ValueError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("admin.rentals"))


@admin_bp.route("/payments")
@admin_required
def payments():
    payments_list = Payment.query.order_by(Payment.date.desc()).all()
    return render_template("admin/payments.html", payments=payments_list, statuses=PAYMENT_STATUS)


@admin_bp.route("/payments/<int:payment_id>/status", methods=["POST"])
@admin_required
def payment_status(payment_id):
    payment = Payment.query.get_or_404(payment_id)
    try:
        status = validate_choice(request.form.get("status"), PAYMENT_STATUS, "payment status")
        PaymentService.verify_payment(payment, status, current_user)
        flash("Payment status updated.", "success")
    except ValueError as exc:
        flash(str(exc), "danger")
    return redirect(url_for("admin.payments"))


@admin_bp.route("/discounts")
@admin_required
def discounts():
    discount_list = Discount.query.order_by(Discount.expiry_date.desc()).all()
    return render_template("admin/discounts.html", discounts=discount_list)


@admin_bp.route("/discounts/create", methods=["GET", "POST"])
@admin_required
def discount_create():
    if request.method == "POST":
        try:
            discount = Discount(
                code=require_text(request.form.get("code"), "Code", max_len=50).upper(),
                discount_type=validate_choice(request.form.get("discount_type"), DISCOUNT_TYPES, "discount type"),
                value=parse_float(request.form.get("value"), "Value", minimum=0),
                expiry_date=parse_date(request.form.get("expiry_date"), "expiry date"),
                is_active=request.form.get("is_active") == "on",
            )
            db.session.add(discount)
            db.session.commit()
            flash("Discount created successfully.", "success")
            return redirect(url_for("admin.discounts"))
        except ValueError as exc:
            flash(str(exc), "danger")
    return render_template("admin/discount_form.html", discount=None, types=DISCOUNT_TYPES)


@admin_bp.route("/discounts/<int:discount_id>/edit", methods=["GET", "POST"])
@admin_required
def discount_edit(discount_id):
    discount = Discount.query.get_or_404(discount_id)
    if request.method == "POST":
        try:
            discount.code = require_text(request.form.get("code"), "Code", max_len=50).upper()
            discount.discount_type = validate_choice(request.form.get("discount_type"), DISCOUNT_TYPES, "discount type")
            discount.value = parse_float(request.form.get("value"), "Value", minimum=0)
            discount.expiry_date = parse_date(request.form.get("expiry_date"), "expiry date")
            discount.is_active = request.form.get("is_active") == "on"
            db.session.commit()
            flash("Discount updated successfully.", "success")
            return redirect(url_for("admin.discounts"))
        except ValueError as exc:
            flash(str(exc), "danger")
    return render_template("admin/discount_form.html", discount=discount, types=DISCOUNT_TYPES)


@admin_bp.route("/discounts/<int:discount_id>/delete", methods=["POST"])
@admin_required
def discount_delete(discount_id):
    discount = Discount.query.get_or_404(discount_id)
    if discount.rentals or discount.cars:
        flash("Cannot delete this discount because it is linked to cars or rentals. Deactivate it instead.", "danger")
    else:
        db.session.delete(discount)
        db.session.commit()
        flash("Discount deleted successfully.", "success")
    return redirect(url_for("admin.discounts"))


@admin_bp.route("/insurances")
@admin_required
def insurances():
    insurance_list = Insurance.query.order_by(Insurance.name).all()
    return render_template("admin/insurances.html", insurances=insurance_list)


@admin_bp.route("/insurances/create", methods=["GET", "POST"])
@admin_required
def insurance_create():
    cars = Car.query.order_by(Car.brand).all()
    if request.method == "POST":
        try:
            insurance = Insurance(
                name=require_text(request.form.get("name"), "Name", max_len=120),
                cost_per_day=parse_float(request.form.get("cost_per_day"), "Cost per day", minimum=0),
                description=(request.form.get("description") or "").strip(),
                is_active=request.form.get("is_active") == "on",
                car_id=int(request.form.get("car_id")) if request.form.get("car_id") else None,
            )
            db.session.add(insurance)
            db.session.commit()
            flash("Insurance plan created successfully.", "success")
            return redirect(url_for("admin.insurances"))
        except ValueError as exc:
            flash(str(exc), "danger")
    return render_template("admin/insurance_form.html", insurance=None, cars=cars)


@admin_bp.route("/insurances/<int:insurance_id>/edit", methods=["GET", "POST"])
@admin_required
def insurance_edit(insurance_id):
    insurance = Insurance.query.get_or_404(insurance_id)
    cars = Car.query.order_by(Car.brand).all()
    if request.method == "POST":
        try:
            insurance.name = require_text(request.form.get("name"), "Name", max_len=120)
            insurance.cost_per_day = parse_float(request.form.get("cost_per_day"), "Cost per day", minimum=0)
            insurance.description = (request.form.get("description") or "").strip()
            insurance.is_active = request.form.get("is_active") == "on"
            insurance.car_id = int(request.form.get("car_id")) if request.form.get("car_id") else None
            db.session.commit()
            flash("Insurance plan updated successfully.", "success")
            return redirect(url_for("admin.insurances"))
        except ValueError as exc:
            flash(str(exc), "danger")
    return render_template("admin/insurance_form.html", insurance=insurance, cars=cars)


@admin_bp.route("/insurances/<int:insurance_id>/delete", methods=["POST"])
@admin_required
def insurance_delete(insurance_id):
    insurance = Insurance.query.get_or_404(insurance_id)
    if insurance.rentals:
        flash("Cannot delete an insurance plan with rental records. Deactivate it instead.", "danger")
    else:
        db.session.delete(insurance)
        db.session.commit()
        flash("Insurance plan deleted successfully.", "success")
    return redirect(url_for("admin.insurances"))


@admin_bp.route("/maintenance")
@admin_required
def maintenance():
    items = Maintenance.query.order_by(Maintenance.service_date.desc()).all()
    return render_template("admin/maintenance.html", items=items)


@admin_bp.route("/maintenance/create", methods=["GET", "POST"])
@admin_required
def maintenance_create():
    cars = Car.query.order_by(Car.brand).all()
    if request.method == "POST":
        try:
            car = Car.query.get_or_404(int(request.form.get("car_id")))
            item = Maintenance(
                car_id=car.id,
                service_type=require_text(request.form.get("service_type"), "Service type", max_len=120),
                cost=parse_float(request.form.get("cost"), "Cost", minimum=0),
                service_date=parse_date(request.form.get("service_date"), "service date"),
                notes=(request.form.get("notes") or "").strip(),
                status=validate_choice(request.form.get("status"), MAINTENANCE_STATUS, "maintenance status"),
            )
            if item.status == "active":
                car.availability_status = "maintenance"
            db.session.add(item)
            db.session.commit()
            flash("Maintenance record created successfully.", "success")
            return redirect(url_for("admin.maintenance"))
        except ValueError as exc:
            flash(str(exc), "danger")
    return render_template("admin/maintenance_form.html", item=None, cars=cars, statuses=MAINTENANCE_STATUS)


@admin_bp.route("/maintenance/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def maintenance_edit(item_id):
    item = Maintenance.query.get_or_404(item_id)
    cars = Car.query.order_by(Car.brand).all()
    if request.method == "POST":
        try:
            item.car_id = int(request.form.get("car_id"))
            item.service_type = require_text(request.form.get("service_type"), "Service type", max_len=120)
            item.cost = parse_float(request.form.get("cost"), "Cost", minimum=0)
            item.service_date = parse_date(request.form.get("service_date"), "service date")
            item.notes = (request.form.get("notes") or "").strip()
            item.status = validate_choice(request.form.get("status"), MAINTENANCE_STATUS, "maintenance status")
            if item.status == "active":
                item.car.availability_status = "maintenance"
            elif item.car.availability_status == "maintenance" and not item.car.is_under_maintenance:
                item.car.availability_status = "available"
            db.session.commit()
            flash("Maintenance record updated successfully.", "success")
            return redirect(url_for("admin.maintenance"))
        except ValueError as exc:
            flash(str(exc), "danger")
    return render_template("admin/maintenance_form.html", item=item, cars=cars, statuses=MAINTENANCE_STATUS)


@admin_bp.route("/maintenance/<int:item_id>/delete", methods=["POST"])
@admin_required
def maintenance_delete(item_id):
    item = Maintenance.query.get_or_404(item_id)
    car = item.car
    db.session.delete(item)
    db.session.commit()
    if car.availability_status == "maintenance" and not car.is_under_maintenance:
        car.availability_status = "available"
        db.session.commit()
    flash("Maintenance record deleted successfully.", "success")
    return redirect(url_for("admin.maintenance"))


@admin_bp.route("/feedback")
@admin_required
def feedbacks():
    items = Feedback.query.order_by(Feedback.date.desc()).all()
    return render_template("admin/feedbacks.html", feedbacks=items)


@admin_bp.route("/feedback/<int:feedback_id>/toggle", methods=["POST"])
@admin_required
def feedback_toggle(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    feedback.is_visible = not feedback.is_visible
    feedback.moderated_by_admin_id = current_user.id
    db.session.commit()
    flash("Feedback visibility updated.", "success")
    return redirect(url_for("admin.feedbacks"))
