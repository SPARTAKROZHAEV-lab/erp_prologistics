import pytest
from app import create_app
from app.extensions import db
from app.models import User, Role

@pytest.fixture(scope='session')
def app():
    """Создаёт экземпляр приложения для тестирования."""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # временная БД
    app.config['WTF_CSRF_ENABLED'] = False  # отключаем CSRF для тестов
    return app

@pytest.fixture
def client(app):
    """Тестовый клиент Flask."""
    return app.test_client()

@pytest.fixture
def _db(app):
    """Инициализация базы данных перед каждым тестом."""
    with app.app_context():
        db.create_all()
        # Создаём базовые роли (если нужно)
        roles = ['admin', 'manager', 'accountant', 'hr', 'storekeeper', 'sales']
        for role_name in roles:
            if not Role.query.filter_by(name=role_name).first():
                db.session.add(Role(name=role_name))
        db.session.commit()
        yield db
        db.session.remove()
        db.drop_all()

@pytest.fixture
def create_user(_db):
    """Фикстура для создания пользователя."""
    def _create_user(username, email, password, roles=None):
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        if roles:
            for role_name in roles:
                role = Role.query.filter_by(name=role_name).first()
                if role:
                    user.roles.append(role)
        db.session.commit()
        return user
    return _create_user

@pytest.fixture
def auth_client(client, create_user):
    """Возвращает аутентифицированного клиента (админ)."""
    user = create_user('admin', 'admin@test.com', 'password', roles=['admin'])
    client.post('/auth/login', data={'email': 'admin@test.com', 'password': 'password'})
    return client