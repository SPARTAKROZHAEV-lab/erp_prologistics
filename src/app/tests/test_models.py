from app.models import User

def test_user_password_hashing(_db):
    """Тест хеширования пароля."""
    user = User(username='test', email='test@test.com')
    user.set_password('secret')
    assert user.check_password('secret') is True
    assert user.check_password('wrong') is False