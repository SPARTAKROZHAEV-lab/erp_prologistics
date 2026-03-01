import pytest
import random
import string
from app.models import User, Role
from app.extensions import db

def test_admin_users_list(auth_client, _db):
    """Проверка доступа к списку пользователей."""
    response = auth_client.get('/admin/users')
    assert response.status_code == 200

def test_admin_assign_role(auth_client, _db):
    """Проверка назначения роли пользователю."""
    # Создаём пользователя
    user = User(username='testuser', email='test@test.com')
    user.set_password('pass')
    db.session.add(user)
    db.session.flush()

    # Создаём роль с уникальным именем (чтобы избежать конфликта)
    unique_name = 'manager_' + ''.join(random.choices(string.digits, k=5))
    role = Role(name=unique_name)
    db.session.add(role)
    db.session.commit()

    # Назначаем роль
    response = auth_client.post(f'/admin/user/{user.id}/roles', data={
        'roles': [role.id]
    }, follow_redirects=True)
    assert response.status_code == 200

    # Проверяем, что роль назначена
    user_updated = User.query.get(user.id)
    assert role in user_updated.roles