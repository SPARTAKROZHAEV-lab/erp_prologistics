# Инициализация Flask приложения
from flask import Flask
from .config import config
from .extensions import db, migrate

def create_app(config_name='default'):
    """
    Фабрика приложения Flask
    :param config_name: имя конфигурации (development, production, default)
    :return: экземпляр Flask
    """
    app = Flask(__name__)

    # Загружаем конфигурацию по имени
    app.config.from_object(config[config_name])

    # Инициализируем расширения с приложением
    db.init_app(app)
    migrate.init_app(app, db)

    # Простой тестовый маршрут
    @app.route('/')
    def hello():
        return 'Hello, ERP Prologistics!'

    # Здесь позже будут подключены blueprints (маршруты модулей)

    return app