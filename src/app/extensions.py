# Инициализация расширений Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Создаём объекты расширений, но не привязываем к конкретному приложению
db = SQLAlchemy()
migrate = Migrate()