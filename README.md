# Car Rental System

A complete student-level but professional **monolithic Flask web application** for a car rental company. The project follows a practical MVC-style structure required by the design/report:

- **Model:** SQLAlchemy database models in `app/models.py`
- **View:** Jinja2 templates in `app/templates/`
- **Controller:** Flask blueprints in `app/routes/`
- **Service layer:** business logic in `app/services/`

The system expands a simple car browsing module into a full rental platform with customer and admin workflows.

---

## Main Features

### Customer Features

- Customer registration, login, and logout
- Secure password hashing using Werkzeug
- Browse cars with professional Bootstrap cards
- Filter cars by:
  - brand
  - model
  - type
  - minimum/maximum price
  - GPS availability
  - rental status
  - location
- View car details with image, description, daily rate, GPS, location, ratings, and insurance options
- Create a rental booking with:
  - start date and end date
  - date validation
  - overlap prevention
  - maintenance/unavailable car blocking
  - rental day calculation
  - insurance cost calculation
  - active discount validation
  - total price calculation
- Simulated payment page using cash, card, or wallet
- Customer dashboard showing rentals, statuses, payment state, total cost, and actions
- Cancel pending unpaid rentals
- Add one feedback review after a completed rental

### Admin Features

- Protected admin login and admin-only pages
- Professional admin dashboard with summary cards:
  - total cars
  - available cars
  - rented cars
  - total customers
  - total rentals
  - total revenue
  - pending payments
  - maintenance cost
- Manage cars with create, read, update, and delete where allowed
- Manage customers and view customer rental history
- Manage rentals and change rental status
- Manage payments and verify status as pending, completed, or refused
- Manage discounts with percentage/flat values, active flag, and expiry date
- Manage insurance plans for all cars or a specific car
- Manage maintenance records; active maintenance blocks car rental
- Moderate feedback visibility
- Generate, view, and delete saved reports

---

## Reports Module

The reports module is formatted for final presentation use. It does **not** show raw JSON/debug output.

Available report types:

- **Earnings:** completed revenue, pending revenue, completed payments
- **Top Cars:** table of cars and rental counts
- **Payments:** completed, pending, and refused payment summaries
- **Maintenance:** total maintenance cost and latest maintenance records
- **Rentals:** total rentals and rental status summary

Each saved report stores:

- ID
- report type
- date range label
- generated admin
- created date
- formatted readable content

---

## Tech Stack

- Python
- Flask
- Flask-SQLAlchemy
- SQLite
- Jinja2
- Bootstrap 5
- Flask-Login
- Werkzeug password hashing

No React, no external payment gateway, and no cloud services are used.

---

## Installation and Run Steps

```bash
cd car_rental_system
python -m venv venv
venv\Scripts\activate      # Windows
# source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python seed_db.py
python run.py
```

Open the app:

```text
http://127.0.0.1:5000
```

---

## Demo Accounts

### Admin

```text
Username: admin
Password: admin123
```

### Customer

```text
Username: customer1
Password: customer123
```

Additional sample users:

```text
Username: customer2
Password: customer123

Username: customer3
Password: customer123
```

---

## Important URLs to Test

```text
/
/cars/
/auth/login
/customer/dashboard
/admin/
/admin/reports/
/admin/cars/
/admin/rentals/
/admin/payments/
```

---

## Project Structure

```text
car_rental_system/
  app/
    __init__.py
    models.py
    forms.py
    decorators.py
    routes/
      __init__.py
      auth.py
      cars.py
      rentals.py
      payments.py
      admin.py
      feedback.py
      reports.py
    services/
      __init__.py
      rental_service.py
      payment_service.py
      report_service.py
    templates/
      base.html
      home.html
      auth/
      cars/
      rentals/
      payments/
      admin/
      feedback/
      errors/
    static/
      css/
      js/
      images/
  config.py
  seed_db.py
  requirements.txt
  README.md
  run.py
```

---

## Database Schema Summary

### User

Represents both admin and customer users using a `role` field.

Main fields:

- `id`
- `name`
- `username`
- `email`
- `phone`
- `password_hash`
- `role`
- `created_at`

### Location

Stores branch/pickup location data.

- `id`
- `city`
- `address`
- `contact_number`

### Car

Stores rental car data.

- `id`
- `brand`
- `model`
- `car_type`
- `gps`
- `daily_rate`
- `availability_status`
- `description`
- `image_url`
- `location_id`
- `discount_id`

### Rental

Tracks booking records.

- `id`
- `customer_id`
- `car_id`
- `insurance_id`
- `discount_id`
- `booking_date`
- `start_date`
- `end_date`
- `status`
- `daily_rate`
- `days`
- `insurance_total`
- `discount_amount`
- `total_amount`

### Payment

Stores simulated payment records.

- `id`
- `rental_id`
- `customer_id`
- `amount`
- `method`
- `status`
- `date`
- `verified_by_admin_id`

### Discount

Stores discount codes.

- `id`
- `code`
- `discount_type`
- `value`
- `expiry_date`
- `is_active`

### Insurance

Stores insurance plans.

- `id`
- `name`
- `cost_per_day`
- `description`
- `is_active`
- `car_id`

### Maintenance

Stores maintenance records.

- `id`
- `car_id`
- `service_type`
- `cost`
- `service_date`
- `notes`
- `status`

### Feedback

Stores customer reviews.

- `id`
- `rental_id`
- `customer_id`
- `car_id`
- `rating`
- `comments`
- `date`
- `moderated_by_admin_id`
- `is_visible`

### Report

Stores saved admin reports.

- `id`
- `admin_id`
- `report_type`
- `date_range`
- `content`
- `created_at`

---

## Important Business Rules

- A car cannot be booked unless its status is `available`.
- A car cannot be booked while it has active maintenance.
- A car cannot have overlapping pending or active rentals.
- End date must be after start date.
- Start date cannot be in the past.
- Rental days are calculated from start date to end date.
- Rental total = daily rate × days + insurance cost − discount amount.
- Percentage and flat discounts are both supported.
- Discounts must be active and not expired.
- Insurance can be global or car-specific.
- Each rental has at most one payment.
- Feedback can only be added by the customer who completed the rental.
- Only one feedback entry is allowed per completed rental.
- Admin-only and customer-only pages are protected.
- Customers cannot modify other customers' rentals.
- Passwords are stored as hashes, never plaintext.

---

## Pages Overview

- Home page with hero section and featured cars
- Cars list with filters and cards
- Car details page
- Booking page
- Simulated payment page
- Customer dashboard
- Admin dashboard
- Admin management pages for cars, customers, rentals, payments, discounts, insurance, maintenance, feedback, and reports
- 403, 404, and 500 error pages

---

## Notes for University Presentation

This project is intentionally monolithic and beginner-friendly. It avoids unnecessary frameworks and advanced services, while still demonstrating MVC separation, database relationships, authentication, role protection, business rules, and a realistic admin/customer user interface.
