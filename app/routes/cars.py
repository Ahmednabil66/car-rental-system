from flask import Blueprint, render_template, request, jsonify, abort
from flask_login import current_user
from app.models import db, Car, Location
from app.decorators import admin_required
from app.services.rental_service import RentalService


cars_bp = Blueprint("cars", __name__)


@cars_bp.route("/")
def home():
    featured_cars = Car.query.filter_by(availability_status="available").limit(3).all()
    return render_template("home.html", featured_cars=featured_cars)


@cars_bp.route("/cars")
def list_cars():
    query = Car.query
    brand = request.args.get("brand", "").strip()
    model = request.args.get("model", "").strip()
    car_type = request.args.get("type", "").strip()
    gps = request.args.get("gps", "")
    availability = request.args.get("availability", "").strip()
    location_id = request.args.get("location_id", "").strip()
    min_price = request.args.get("min_price", "").strip()
    max_price = request.args.get("max_price", "").strip()

    if brand:
        query = query.filter(Car.brand.ilike(f"%{brand}%"))
    if model:
        query = query.filter(Car.model.ilike(f"%{model}%"))
    if car_type:
        query = query.filter(Car.car_type == car_type)
    if gps == "1":
        query = query.filter(Car.gps.is_(True))
    if availability:
        query = query.filter(Car.availability_status == availability)
    if location_id:
        query = query.filter(Car.location_id == int(location_id))
    if min_price:
        query = query.filter(Car.daily_rate >= float(min_price))
    if max_price:
        query = query.filter(Car.daily_rate <= float(max_price))

    cars = query.order_by(Car.daily_rate.asc()).all()
    locations = Location.query.order_by(Location.city).all()
    car_types = [row[0] for row in db.session.query(Car.car_type).distinct().order_by(Car.car_type).all()]
    return render_template("cars/list.html", cars=cars, locations=locations, car_types=car_types)


@cars_bp.route("/cars/<int:car_id>")
def details(car_id):
    car = Car.query.get_or_404(car_id)
    insurance_options = RentalService.get_available_insurances_for_car(car.id)
    return render_template("cars/details.html", car=car, insurance_options=insurance_options)


@cars_bp.route("/api/cars/<int:car_id>/status", methods=["PUT"])
@admin_required
def update_status(car_id):
    car = Car.query.get_or_404(car_id)
    data = request.get_json() or {}
    status = data.get("availability_status")
    if status not in ["available", "rented", "maintenance"]:
        return jsonify({"error": "Invalid status"}), 400
    car.availability_status = status
    db.session.commit()
    return jsonify({"message": "Status updated", "car": car.to_dict()})
