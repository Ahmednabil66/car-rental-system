from flask import Flask, render_template
from flask_login import LoginManager
from .models import db, User

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app(config_object="config.Config"):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_object)

    app.url_map.strict_slashes = False
    db.init_app(app)
    login_manager.init_app(app)

    from .routes.auth import auth_bp
    from .routes.cars import cars_bp
    from .routes.rentals import rentals_bp, customer_bp
    from .routes.payments import payments_bp
    from .routes.admin import admin_bp
    from .routes.feedback import feedback_bp
    from .routes.reports import reports_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(cars_bp)
    app.register_blueprint(rentals_bp)
    app.register_blueprint(customer_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(reports_bp)

    @app.template_filter("money")
    def money_filter(value):
        try:
            return f"{float(value):,.2f} EGP"
        except (TypeError, ValueError):
            return "0.00 EGP"

    @app.template_filter("date")
    def date_filter(value):
        if not value:
            return "-"
        return value.strftime("%Y-%m-%d")

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(error):
        db.session.rollback()
        return render_template("errors/500.html"), 500

    return app
