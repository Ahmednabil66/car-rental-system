from datetime import date, datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Represents both Customer and Admin users using a simple role field."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), nullable=False, unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    phone = db.Column(db.String(30))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="customer", index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    rentals = db.relationship("Rental", foreign_keys="Rental.customer_id", back_populates="customer", cascade="all, delete-orphan")
    payments = db.relationship("Payment", foreign_keys="Payment.customer_id", back_populates="customer")
    feedbacks = db.relationship("Feedback", foreign_keys="Feedback.customer_id", back_populates="customer")
    verified_payments = db.relationship("Payment", foreign_keys="Payment.verified_by_admin_id", back_populates="verified_by")
    reports = db.relationship("Report", foreign_keys="Report.admin_id", back_populates="admin")

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_customer(self):
        return self.role == "customer"

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"


class Location(db.Model):
    __tablename__ = "locations"

    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(80), nullable=False, index=True)
    address = db.Column(db.String(255), nullable=False)
    contact_number = db.Column(db.String(30))

    cars = db.relationship("Car", back_populates="location")

    @property
    def display_name(self):
        return f"{self.city} - {self.address}"


class Car(db.Model):
    __tablename__ = "cars"

    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(80), nullable=False, index=True)
    model = db.Column(db.String(80), nullable=False, index=True)
    car_type = db.Column(db.String(80), nullable=False, index=True)
    gps = db.Column(db.Boolean, nullable=False, default=False)
    daily_rate = db.Column(db.Float, nullable=False)
    availability_status = db.Column(db.String(30), nullable=False, default="available", index=True)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    location_id = db.Column(db.Integer, db.ForeignKey("locations.id"))
    discount_id = db.Column(db.Integer, db.ForeignKey("discounts.id"))

    location = db.relationship("Location", back_populates="cars")
    rentals = db.relationship("Rental", back_populates="car", cascade="all, delete-orphan")
    maintenances = db.relationship("Maintenance", back_populates="car", cascade="all, delete-orphan")
    feedbacks = db.relationship("Feedback", back_populates="car", cascade="all, delete-orphan")
    insurances = db.relationship("Insurance", back_populates="car")
    discount = db.relationship("Discount", back_populates="cars")

    @property
    def title(self):
        return f"{self.brand} {self.model}"

    @property
    def is_under_maintenance(self):
        return any(m.status == "active" for m in self.maintenances)

    @property
    def average_rating(self):
        if not self.feedbacks:
            return None
        return round(sum(f.rating for f in self.feedbacks) / len(self.feedbacks), 1)

    def has_overlapping_rental(self, start_date, end_date, exclude_rental_id=None):
        active_statuses = ["pending", "active"]
        query = Rental.query.filter(
            Rental.car_id == self.id,
            Rental.status.in_(active_statuses),
            Rental.start_date < end_date,
            Rental.end_date > start_date,
        )
        if exclude_rental_id:
            query = query.filter(Rental.id != exclude_rental_id)
        return db.session.query(query.exists()).scalar()

    def can_be_rented(self, start_date=None, end_date=None):
        if self.availability_status == "maintenance" or self.is_under_maintenance:
            return False, "This car is currently under maintenance."
        if self.availability_status != "available":
            return False, "This car is not available for rent."
        if start_date and end_date and self.has_overlapping_rental(start_date, end_date):
            return False, "This car already has a booking during these dates."
        return True, "Available"

    def to_dict(self):
        return {
            "id": self.id,
            "brand": self.brand,
            "model": self.model,
            "type": self.car_type,
            "gps": self.gps,
            "daily_rate": self.daily_rate,
            "availability_status": self.availability_status,
            "description": self.description,
            "location": self.location.display_name if self.location else None,
        }


class Discount(db.Model):
    __tablename__ = "discounts"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), nullable=False, unique=True, index=True)
    discount_type = db.Column(db.String(20), nullable=False)  # percentage / flat
    value = db.Column(db.Float, nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    cars = db.relationship("Car", back_populates="discount")
    rentals = db.relationship("Rental", back_populates="discount")

    def is_valid(self):
        return self.is_active and self.expiry_date >= date.today()

    def calculate_discount(self, subtotal):
        if not self.is_valid():
            return 0
        if self.discount_type == "percentage":
            return round(subtotal * (self.value / 100), 2)
        return min(round(self.value, 2), subtotal)


class Insurance(db.Model):
    __tablename__ = "insurances"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    cost_per_day = db.Column(db.Float, nullable=False, default=0)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    car_id = db.Column(db.Integer, db.ForeignKey("cars.id"), nullable=True)

    car = db.relationship("Car", back_populates="insurances")
    rentals = db.relationship("Rental", back_populates="insurance")

    @property
    def display_name(self):
        return f"{self.name} ({self.cost_per_day:.2f}/day)"


class Rental(db.Model):
    __tablename__ = "rentals"

    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    car_id = db.Column(db.Integer, db.ForeignKey("cars.id"), nullable=False, index=True)
    insurance_id = db.Column(db.Integer, db.ForeignKey("insurances.id"))
    discount_id = db.Column(db.Integer, db.ForeignKey("discounts.id"))
    booking_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(30), nullable=False, default="pending", index=True)
    daily_rate = db.Column(db.Float, nullable=False)
    days = db.Column(db.Integer, nullable=False)
    insurance_total = db.Column(db.Float, nullable=False, default=0)
    discount_amount = db.Column(db.Float, nullable=False, default=0)
    total_amount = db.Column(db.Float, nullable=False)

    customer = db.relationship("User", foreign_keys=[customer_id], back_populates="rentals")
    car = db.relationship("Car", back_populates="rentals")
    insurance = db.relationship("Insurance", back_populates="rentals")
    discount = db.relationship("Discount", back_populates="rentals")
    payment = db.relationship("Payment", back_populates="rental", uselist=False, cascade="all, delete-orphan")
    feedback = db.relationship("Feedback", back_populates="rental", uselist=False, cascade="all, delete-orphan")

    @property
    def rental_period(self):
        return f"{self.start_date} to {self.end_date}"

    @property
    def can_be_cancelled_by_customer(self):
        return self.status == "pending" and (not self.payment or self.payment.status != "completed")


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)
    rental_id = db.Column(db.Integer, db.ForeignKey("rentals.id"), nullable=False, unique=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    method = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="pending", index=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    verified_by_admin_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    rental = db.relationship("Rental", back_populates="payment")
    customer = db.relationship("User", foreign_keys=[customer_id], back_populates="payments")
    verified_by = db.relationship("User", foreign_keys=[verified_by_admin_id], back_populates="verified_payments")


class Maintenance(db.Model):
    __tablename__ = "maintenances"

    id = db.Column(db.Integer, primary_key=True)
    car_id = db.Column(db.Integer, db.ForeignKey("cars.id"), nullable=False, index=True)
    service_type = db.Column(db.String(120), nullable=False)
    cost = db.Column(db.Float, nullable=False, default=0)
    service_date = db.Column(db.Date, nullable=False, default=date.today)
    notes = db.Column(db.Text)
    status = db.Column(db.String(30), nullable=False, default="active")

    car = db.relationship("Car", back_populates="maintenances")


class Feedback(db.Model):
    __tablename__ = "feedbacks"

    id = db.Column(db.Integer, primary_key=True)
    rental_id = db.Column(db.Integer, db.ForeignKey("rentals.id"), nullable=False, unique=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    car_id = db.Column(db.Integer, db.ForeignKey("cars.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comments = db.Column(db.Text)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    moderated_by_admin_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    is_visible = db.Column(db.Boolean, nullable=False, default=True)

    __table_args__ = (
        db.CheckConstraint("rating >= 1 AND rating <= 5", name="check_feedback_rating_range"),
    )

    rental = db.relationship("Rental", back_populates="feedback")
    customer = db.relationship("User", foreign_keys=[customer_id], back_populates="feedbacks")
    car = db.relationship("Car", back_populates="feedbacks")
    moderated_by = db.relationship("User", foreign_keys=[moderated_by_admin_id])


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)
    date_range = db.Column(db.String(120))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    admin = db.relationship("User", foreign_keys=[admin_id], back_populates="reports")
