import pytest
from app.models import User

def test_register(client, _db):
    """Проверка регистрации нового пользователя."""
    response = client.post('/auth/register', data={
        'username': 'newuser',
        'email': 'new@test.com',
        'password': 'password',
        'confirm_password': 'password'
    }, follow_redirects=True)
    assert response.status_code == 200
    # Декодируем ответ и проверяем наличие русского сообщения
    content = response.data.decode('utf-8')
    assert 'Регистрация прошла успешно' in content
    user = User.query.filter_by(email='new@test.com').first()
    assert user is not None

def test_login_logout(client, create_user):
    """Проверка входа и выхода."""
    user = create_user('testuser', 'test@test.com', 'secret')
    # Вход
    response = client.post('/auth/login', data={
        'email': 'test@test.com',
        'password': 'secret'
    }, follow_redirects=True)
    assert response.status_code == 200
    content = response.data.decode('utf-8')
    # После входа должно отображаться имя пользователя в шапке
    assert 'testuser' in content

    # Выход
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    content = response.data.decode('utf-8')
    # После выхода имя пользователя исчезает, появляется ссылка "Вход"
    assert 'Вход' in content
    assert 'testuser' not in content

def test_access_protected_page_without_login(client):
    """Неавторизованный пользователь не должен видеть защищённые страницы."""
    response = client.get('/finance/invoices', follow_redirects=False)
    assert response.status_code == 302
    assert '/auth/login' in response.location