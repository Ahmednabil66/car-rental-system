from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user
from app.models import db, Report
from app.decorators import admin_required
from app.forms import REPORT_TYPES, validate_choice, validate_date_range_label
from app.services.report_service import ReportService


reports_bp = Blueprint("reports", __name__, url_prefix="/admin/reports")


@reports_bp.route("/", methods=["GET", "POST"])
@admin_required
def index():
    if request.method == "POST":
        try:
            report_type = validate_choice(request.form.get("report_type"), REPORT_TYPES, "report type")
            date_range = validate_date_range_label(request.form.get("date_range"))
            ReportService.save_report(current_user, report_type, date_range)
            flash("Report generated and saved.", "success")
            return redirect(url_for("reports.index"))
        except ValueError as exc:
            flash(str(exc), "danger")
    reports = Report.query.order_by(Report.created_at.desc()).all()
    report_cards = [ReportService.view_model(report) for report in reports]
    return render_template("admin/reports.html", reports=report_cards, report_types=REPORT_TYPES)


@reports_bp.route("/<int:report_id>")
@admin_required
def details(report_id):
    report = Report.query.get_or_404(report_id)
    return render_template("admin/report_details.html", report=ReportService.view_model(report))


@reports_bp.route("/<int:report_id>/delete", methods=["POST"])
@admin_required
def delete(report_id):
    report = Report.query.get_or_404(report_id)
    db.session.delete(report)
    db.session.commit()
    flash("Report deleted successfully.", "success")
    return redirect(url_for("reports.index"))
