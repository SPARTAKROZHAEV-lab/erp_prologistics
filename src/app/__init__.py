# Инициализация Flask приложения
from flask import Flask
from .config import config
from .extensions import db, migrate
from .routes.auth import auth_bp
from .extensions import db, migrate, login_manager


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
    from app.routes.hr import hr_bp
    app.register_blueprint(hr_bp)


    # Импортируем модели, чтобы они были зарегистрированы
    from .models import Test  # или from . import models

    @app.route('/')
    def hello():
        return 'Hello, ERP Prologistics!'

    return app