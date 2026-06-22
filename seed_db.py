from datetime import date, timedelta
from app import create_app
from app.models import db, User, Location, Car, Discount, Insurance, Maintenance, Rental, Payment, Feedback, Report
from app.services.report_service import ReportService

app = create_app()

CAR_IMAGES = {
    "corolla": "https://images.unsplash.com/photo-1621007947382-bb3c3994e3fb?q=80&w=1200&auto=format&fit=crop",
    "rav4": "https://images.unsplash.com/photo-1519641471654-76ce0107ad1b?q=80&w=1200&auto=format&fit=crop",
    "elantra": "https://images.unsplash.com/photo-1550355291-bbee04a92027?q=80&w=1200&auto=format&fit=crop",
    "xtrail": "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?q=80&w=1200&auto=format&fit=crop",
    "bmw": "https://images.unsplash.com/photo-1555215695-3004980ad54e?q=80&w=1200&auto=format&fit=crop",
    "van": "https://images.unsplash.com/photo-1619767886558-efdc259cde1a?q=80&w=1200&auto=format&fit=crop",
}


def make_user(name, username, email, phone, role, password):
    user = User(name=name, username=username, email=email, phone=phone, role=role)
    user.set_password(password)
    db.session.add(user)
    return user


def add_rental(customer, car, insurance, discount, start_offset, days, status, payment_method=None, payment_status=None, admin=None, feedback_rating=None):
    start = date.today() + timedelta(days=start_offset)
    end = start + timedelta(days=days)
    base_total = car.daily_rate * days
    insurance_total = (insurance.cost_per_day * days) if insurance else 0
    subtotal = base_total + insurance_total
    discount_amount = discount.calculate_discount(subtotal) if discount else 0
    total = round(subtotal - discount_amount, 2)
    rental = Rental(
        customer=customer,
        car=car,
        insurance=insurance,
        discount=discount,
        start_date=start,
        end_date=end,
        status=status,
        daily_rate=car.daily_rate,
        days=days,
        insurance_total=round(insurance_total, 2),
        discount_amount=round(discount_amount, 2),
        total_amount=total,
    )
    db.session.add(rental)
    db.session.flush()
    if payment_method and payment_status:
        db.session.add(Payment(rental=rental, customer=customer, amount=total, method=payment_method, status=payment_status, verified_by=admin if payment_status == "completed" else None))
    if feedback_rating:
        db.session.add(Feedback(rental=rental, customer=customer, car=car, rating=feedback_rating, comments="Clean car, fast pickup, and clear pricing."))
    return rental


with app.app_context():
    db.drop_all()
    db.create_all()

    admin = make_user("System Admin", "admin", "admin@cars.local", "01000000000", "admin", "admin123")
    customer1 = make_user("Mona Hassan", "customer1", "mona@example.com", "01011111111", "customer", "customer123")
    customer2 = make_user("Omar Ali", "customer2", "omar@example.com", "01022222222", "customer", "customer123")
    customer3 = make_user("Salma Adel", "customer3", "salma@example.com", "01033333333", "customer", "customer123")

    cairo = Location(city="Cairo", address="Nasr City Branch", contact_number="0220001111")
    alex = Location(city="Alexandria", address="Stanley Branch", contact_number="0320002222")
    giza = Location(city="Giza", address="Sheikh Zayed Branch", contact_number="0230003333")
    db.session.add_all([cairo, alex, giza])

    save10 = Discount(code="SAVE10", discount_type="percentage", value=10, expiry_date=date.today() + timedelta(days=120), is_active=True)
    flat50 = Discount(code="FLAT50", discount_type="flat", value=50, expiry_date=date.today() + timedelta(days=60), is_active=True)
    expired = Discount(code="OLD5", discount_type="percentage", value=5, expiry_date=date.today() - timedelta(days=10), is_active=False)
    db.session.add_all([save10, flat50, expired])
    db.session.flush()

    cars = [
        Car(brand="Toyota", model="Corolla", car_type="Sedan", gps=True, daily_rate=35, availability_status="available", description="Reliable sedan with low fuel consumption and comfortable interior.", image_url=CAR_IMAGES["corolla"], location=cairo, discount=save10),
        Car(brand="Toyota", model="RAV4", car_type="SUV", gps=True, daily_rate=60, availability_status="available", description="Spacious SUV suitable for family trips and long drives.", image_url=CAR_IMAGES["rav4"], location=giza),
        Car(brand="Hyundai", model="Elantra", car_type="Sedan", gps=False, daily_rate=32, availability_status="available", description="Economic sedan for daily city rental.", image_url=CAR_IMAGES["elantra"], location=alex),
        Car(brand="Nissan", model="X-Trail", car_type="SUV", gps=True, daily_rate=58, availability_status="available", description="Comfort SUV with excellent road stability.", image_url=CAR_IMAGES["xtrail"], location=cairo),
        Car(brand="BMW", model="320i", car_type="Luxury", gps=True, daily_rate=95, availability_status="available", description="Premium luxury sedan for business and special occasions.", image_url=CAR_IMAGES["bmw"], location=giza, discount=flat50),
        Car(brand="Mercedes", model="Vito", car_type="Van", gps=True, daily_rate=88, availability_status="maintenance", description="Large van for group transportation.", image_url=CAR_IMAGES["van"], location=alex),
    ]
    db.session.add_all(cars)
    db.session.flush()

    basic = Insurance(name="Basic Protection", cost_per_day=5, description="Covers minor accidental damage.", is_active=True)
    premium = Insurance(name="Premium Protection", cost_per_day=12, description="Extended coverage with reduced customer liability.", is_active=True)
    suv_cover = Insurance(name="SUV Roadside Plus", cost_per_day=8, description="Roadside support for SUV rentals.", is_active=True, car=cars[1])
    db.session.add_all([basic, premium, suv_cover])
    db.session.flush()

    db.session.add_all([
        Maintenance(car=cars[5], service_type="Engine Inspection", cost=180, service_date=date.today(), notes="Waiting for parts.", status="active"),
        Maintenance(car=cars[0], service_type="Oil Change", cost=45, service_date=date.today() - timedelta(days=12), notes="Routine service completed.", status="completed"),
    ])

    add_rental(customer1, cars[0], basic, save10, -12, 3, "completed", "card", "completed", admin, feedback_rating=5)
    add_rental(customer1, cars[1], suv_cover, None, -25, 4, "completed", "wallet", "completed", admin, feedback_rating=4)
    add_rental(customer2, cars[3], premium, None, 3, 3, "pending", "cash", "pending")
    add_rental(customer3, cars[4], premium, flat50, -18, 2, "completed", "card", "completed", admin, feedback_rating=5)
    add_rental(customer2, cars[0], basic, None, -40, 2, "completed", "cash", "completed", admin)
    db.session.commit()

    for report_type, label in [
        ("earnings", "All time"),
        ("top_cars", "June 2026"),
        ("payments", "All time"),
        ("maintenance", "Seed sample"),
        ("rentals", "2026-06-01 to 2026-06-30"),
    ]:
        db.session.add(Report(admin=admin, report_type=report_type, date_range=label, content=ReportService.generate(report_type)))
    db.session.commit()

    print("Database seeded successfully.")
    print("Admin account: admin / admin123")
    print("Customer account: customer1 / customer123")
