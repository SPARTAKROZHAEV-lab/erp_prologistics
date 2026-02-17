# Инициализация Flask приложения
from flask import Flask
from .config import config
from .extensions import db, migrate

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)

    # Импортируем модели, чтобы они были зарегистрированы
    from .models import Test  # или from . import models

    @app.route('/')
    def hello():
        return 'Hello, ERP Prologistics!'

    return app