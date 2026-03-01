# Инициализация Flask приложения
from flask import Flask, render_template
from .config import config
from .extensions import db, migrate, login_manager
from .routes.auth import auth_bp

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
    login_manager.login_message_category = 'warning'
    migrate.init_app(app, db)
    app.register_blueprint(auth_bp)
    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp)
    from .routes.finance import finance_bp
    app.register_blueprint(finance_bp)
    from app.routes.hr import hr_bp
    app.register_blueprint(hr_bp)
    from app.routes.inventory import inventory_bp
    app.register_blueprint(inventory_bp)
    from app.routes.sales import sales_bp
    app.register_blueprint(sales_bp)
    from app.routes.analytics import analytics_bp
    app.register_blueprint(analytics_bp)




    @app.route('/')
    def index():
        return render_template('index.html')

    return app