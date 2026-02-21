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
    migrate.init_app(app, db)
    app.register_blueprint(auth_bp)
    from app.routes.admin import admin_bp
    app.register_blueprint(admin_bp)


    # Импортируем модели, чтобы они были зарегистрированы
    from .models import Test  # или from . import models

    @app.route('/')
    def hello():
        return 'Hello, ERP Prologistics!'

    return app