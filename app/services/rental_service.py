from datetime import date
from app.models import db, Car, Discount, Insurance, Rental


class RentalService:
    @staticmethod
    def calculate_days(start_date, end_date):
        days = (end_date - start_date).days
        if days <= 0:
            raise ValueError("End date must be after start date.")
        return days

    @staticmethod
    def get_available_insurances_for_car(car_id):
        return Insurance.query.filter(
            Insurance.is_active.is_(True),
            db.or_(Insurance.car_id.is_(None), Insurance.car_id == car_id),
        ).order_by(Insurance.cost_per_day.asc()).all()

    @staticmethod
    def price_quote(car, start_date, end_date, insurance_id=None, discount_code=None):
        if start_date < date.today():
            raise ValueError("Start date cannot be in the past.")

        days = RentalService.calculate_days(start_date, end_date)
        can_rent, message = car.can_be_rented(start_date, end_date)
        if not can_rent:
            raise ValueError(message)

        base_total = round(car.daily_rate * days, 2)
        insurance = None
        insurance_total = 0
        if insurance_id:
            insurance = Insurance.query.get(int(insurance_id))
            if not insurance or not insurance.is_active:
                raise ValueError("Selected insurance plan is not available.")
            if insurance.car_id is not None and insurance.car_id != car.id:
                raise ValueError("Selected insurance plan is not valid for this car.")
            insurance_total = round(insurance.cost_per_day * days, 2)

        subtotal = round(base_total + insurance_total, 2)
        discount = None
        discount_amount = 0
        if discount_code:
            discount = Discount.query.filter(db.func.upper(Discount.code) == discount_code.strip().upper()).first()
            if not discount or not discount.is_valid():
                raise ValueError("Invalid or expired discount code.")
            discount_amount = discount.calculate_discount(subtotal)

        total = max(round(subtotal - discount_amount, 2), 0)
        return {
            "days": days,
            "base_total": base_total,
            "insurance": insurance,
            "insurance_total": insurance_total,
            "discount": discount,
            "discount_amount": discount_amount,
            "total": total,
        }

    @staticmethod
    def create_rental(customer, car_id, start_date, end_date, insurance_id=None, discount_code=None):
        car = Car.query.get_or_404(car_id)
        quote = RentalService.price_quote(car, start_date, end_date, insurance_id, discount_code)
        rental = Rental(
            customer_id=customer.id,
            car_id=car.id,
            insurance_id=quote["insurance"].id if quote["insurance"] else None,
            discount_id=quote["discount"].id if quote["discount"] else None,
            start_date=start_date,
            end_date=end_date,
            status="pending",
            daily_rate=car.daily_rate,
            days=quote["days"],
            insurance_total=quote["insurance_total"],
            discount_amount=quote["discount_amount"],
            total_amount=quote["total"],
        )
        db.session.add(rental)
        db.session.commit()
        return rental

    @staticmethod
    def cancel_pending_rental(rental, user):
        if rental.customer_id != user.id:
            raise PermissionError("You cannot cancel another customer's rental.")
        if not rental.can_be_cancelled_by_customer:
            raise ValueError("Only pending unpaid rentals can be cancelled.")
        rental.status = "cancelled"
        if rental.car.availability_status == "rented":
            rental.car.availability_status = "available"
        db.session.commit()
        return rental

    @staticmethod
    def update_rental_status(rental, status):
        rental.status = status
        car = rental.car
        if status == "active":
            car.availability_status = "rented"
        elif status in ["completed", "cancelled", "refused"]:
            if car.is_under_maintenance:
                car.availability_status = "maintenance"
            else:
                car.availability_status = "available"
        db.session.commit()
        return rental
