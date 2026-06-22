from datetime import datetime, date
import re

CAR_TYPES = ["Sedan", "SUV", "Hatchback", "Luxury", "Van", "Sports"]
CAR_STATUS = ["available", "rented", "maintenance"]
RENTAL_STATUS = ["pending", "active", "completed", "cancelled", "refused"]
PAYMENT_STATUS = ["pending", "completed", "refused"]
PAYMENT_METHODS = ["cash", "card", "wallet"]
DISCOUNT_TYPES = ["percentage", "flat"]
MAINTENANCE_STATUS = ["active", "completed"]
REPORT_TYPES = ["earnings", "top_cars", "payments", "maintenance", "rentals"]


def parse_date(value, field_name="date"):
    if not value:
        raise ValueError(f"{field_name} is required.")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"Invalid {field_name}. Use YYYY-MM-DD.") from exc


def parse_float(value, field_name, minimum=None):
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a number.") from exc
    if minimum is not None and number < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}.")
    return number


def parse_int(value, field_name, minimum=None, maximum=None):
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be a whole number.") from exc
    if minimum is not None and number < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}.")
    if maximum is not None and number > maximum:
        raise ValueError(f"{field_name} must be at most {maximum}.")
    return number


def require_text(value, field_name, min_len=1, max_len=None):
    text = (value or "").strip()
    if len(text) < min_len:
        raise ValueError(f"{field_name} is required.")
    if max_len and len(text) > max_len:
        raise ValueError(f"{field_name} must be at most {max_len} characters.")
    return text


def validate_choice(value, choices, field_name):
    if value not in choices:
        raise ValueError(f"Invalid {field_name}.")
    return value


def validate_date_range_label(value):
    label = (value or "All time").strip()
    if len(label) > 120:
        raise ValueError("Date range label must be at most 120 characters.")
    current_year = date.today().year
    for year_text in re.findall(r"\b(20\d{2})\b", label):
        year = int(year_text)
        if year < 2020 or year > current_year + 1:
            raise ValueError("Please use a realistic date range label, such as 'All time', 'June 2026', or '2026-06-01 to 2026-06-30'.")
    return label


def today():
    return date.today()
