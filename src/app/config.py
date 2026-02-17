# Модуль конфигурации приложения
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env
load_dotenv()

class Config:
    """Базовый класс конфигурации"""
    # Секретный ключ для подписей и сессий
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
    
    # Строка подключения к базе данных
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///default.db')
    
    # Отключаем отслеживание изменений (экономит ресурсы)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Режим отладки (включаем для разработки)
    DEBUG = True

class DevelopmentConfig(Config):
    """Конфигурация для разработки"""
    DEBUG = True

class ProductionConfig(Config):
    """Конфигурация для продакшена"""
    DEBUG = False
    # Здесь можно добавить другие настройки для продакшена

# Словарь для выбора конфигурации по имени
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}