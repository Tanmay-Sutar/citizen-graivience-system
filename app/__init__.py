import os
from flask import Flask, render_template
from .config import Config
from .models import db
from .extensions import login_manager, csrf


def page_not_found(e):
    return render_template('errors/404.html'), 404


def internal_server_error(e):
    return render_template('errors/500.html'), 500


def forbidden(e):
    return render_template('errors/403.html'), 403


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.dashboard.routes import dashboard_bp
    from app.grievance.routes import grievance_bp
    from app.admin_panel.routes import admin_bp as admin_panel_bp
    from app.chat.routes import chat_bp
    from app.stats.routes import stats_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(main_bp)
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(grievance_bp)
    app.register_blueprint(admin_panel_bp, url_prefix='/admin-panel')
    app.register_blueprint(chat_bp, url_prefix='/chat')
    app.register_blueprint(stats_bp, url_prefix='/stats')

    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, internal_server_error)
    app.register_error_handler(403, forbidden)

    with app.app_context():
        db.create_all()

    try:
        from .scheduler import start_scheduler
        start_scheduler(app)
    except Exception as exc:
        app.logger.warning(f"Scheduler could not start: {exc}")

    return app
