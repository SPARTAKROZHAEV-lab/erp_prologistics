# Инициализация Flask приложения
from flask import Flask

def create_app():
    """Фабрика приложения Flask"""
    app = Flask(__name__)

    # Простой тестовый маршрут для проверки работы
    @app.route('/')
    def hello():
        # Эта функция будет вызвана при обращении к корневому URL
        return 'Hello, ERP Prologistics!'

    # Здесь позже будут подключены blueprints, расширения и т.д.

    return app