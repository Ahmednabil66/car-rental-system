from app.models import db, Payment


class PaymentService:
    @staticmethod
    def create_or_update_payment(rental, method, status="pending"):
        if rental.status in ["cancelled", "refused"]:
            raise ValueError("Cannot pay for a cancelled or refused rental.")
        payment = rental.payment
        if not payment:
            payment = Payment(
                rental_id=rental.id,
                customer_id=rental.customer_id,
                amount=rental.total_amount,
                method=method,
                status=status,
            )
            db.session.add(payment)
        else:
            if payment.status == "completed":
                raise ValueError("Completed payments cannot be changed by the customer.")
            payment.method = method
            payment.status = status
            payment.amount = rental.total_amount
        db.session.commit()
        return payment

    @staticmethod
    def verify_payment(payment, status, admin):
        payment.status = status
        payment.verified_by_admin_id = admin.id
        rental = payment.rental
        if status == "completed" and rental.status == "pending":
            rental.status = "active"
            rental.car.availability_status = "rented"
        elif status == "refused" and rental.status == "pending":
            rental.status = "refused"
        db.session.commit()
        return payment
