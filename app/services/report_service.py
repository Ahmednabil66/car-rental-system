import json
from app.models import db, User, Car, Rental, Payment, Maintenance, Report


class ReportService:
    @staticmethod
    def dashboard_summary():
        total_cars = Car.query.count()
        available_cars = Car.query.filter_by(availability_status="available").count()
        rented_cars = Car.query.filter_by(availability_status="rented").count()
        total_customers = User.query.filter_by(role="customer").count()
        total_rentals = Rental.query.count()
        total_revenue = db.session.query(db.func.sum(Payment.amount)).filter(Payment.status == "completed").scalar() or 0
        pending_payments = Payment.query.filter_by(status="pending").count()
        maintenance_cost = db.session.query(db.func.sum(Maintenance.cost)).scalar() or 0
        return {
            "total_cars": total_cars,
            "available_cars": available_cars,
            "rented_cars": rented_cars,
            "total_customers": total_customers,
            "total_rentals": total_rentals,
            "total_revenue": round(total_revenue, 2),
            "pending_payments": pending_payments,
            "maintenance_cost": round(maintenance_cost, 2),
        }

    @staticmethod
    def generate(report_type):
        if report_type == "earnings":
            completed = db.session.query(db.func.sum(Payment.amount)).filter(Payment.status == "completed").scalar() or 0
            pending = db.session.query(db.func.sum(Payment.amount)).filter(Payment.status == "pending").scalar() or 0
            refused = db.session.query(db.func.sum(Payment.amount)).filter(Payment.status == "refused").scalar() or 0
            content = {
                "completed_revenue": round(completed, 2),
                "pending_revenue": round(pending, 2),
                "refused_amount": round(refused, 2),
                "completed_payments": Payment.query.filter_by(status="completed").count(),
            }
        elif report_type == "rentals":
            rows = db.session.query(Rental.status, db.func.count(Rental.id)).group_by(Rental.status).all()
            content = {
                "total_rentals": Rental.query.count(),
                "rentals_by_status": {status: count for status, count in rows},
            }
        elif report_type == "top_cars":
            rows = (
                db.session.query(Car.brand, Car.model, db.func.count(Rental.id).label("rental_count"))
                .join(Rental, Rental.car_id == Car.id)
                .group_by(Car.id)
                .order_by(db.desc("rental_count"))
                .limit(10)
                .all()
            )
            content = {"top_rented_cars": [{"car": f"{brand} {model}", "rentals": count} for brand, model, count in rows]}
        elif report_type == "payments":
            rows = db.session.query(Payment.status, db.func.count(Payment.id)).group_by(Payment.status).all()
            totals = db.session.query(Payment.status, db.func.sum(Payment.amount)).group_by(Payment.status).all()
            content = {
                "payments_by_status": {status: count for status, count in rows},
                "amounts_by_status": {status: round(amount or 0, 2) for status, amount in totals},
            }
        elif report_type == "maintenance":
            total = db.session.query(db.func.sum(Maintenance.cost)).scalar() or 0
            records = (
                db.session.query(Maintenance, Car)
                .join(Car, Maintenance.car_id == Car.id)
                .order_by(Maintenance.service_date.desc(), Maintenance.id.desc())
                .limit(10)
                .all()
            )
            content = {
                "total_maintenance_cost": round(total, 2),
                "maintenance_records": [
                    {
                        "car": car.title,
                        "service_type": item.service_type,
                        "date": item.service_date.strftime("%Y-%m-%d"),
                        "cost": round(item.cost, 2),
                        "status": item.status,
                    }
                    for item, car in records
                ],
            }
        else:
            raise ValueError("Unknown report type.")
        return json.dumps(content, indent=2)

    @staticmethod
    def save_report(admin, report_type, date_range="All time"):
        content = ReportService.generate(report_type)
        report = Report(admin_id=admin.id, report_type=report_type, date_range=date_range, content=content)
        db.session.add(report)
        db.session.commit()
        return report

    @staticmethod
    def parse_content(report):
        try:
            return json.loads(report.content or "{}")
        except json.JSONDecodeError:
            return {"message": report.content or "No content"}

    @staticmethod
    def view_model(report):
        return {
            "record": report,
            "content": ReportService.parse_content(report),
            "title": report.report_type.replace("_", " ").title(),
        }
