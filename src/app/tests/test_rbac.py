import pytest

def test_admin_access_finance(auth_client):
    """Админ должен иметь доступ к финансам."""
    response = auth_client.get('/finance/invoices')
    assert response.status_code == 200

def test_accountant_access_finance(client, create_user, _db):
    """Бухгалтер должен иметь доступ к финансам."""
    user = create_user('acc', 'acc@test.com', 'pass', roles=['accountant'])
    client.post('/auth/login', data={'email': 'acc@test.com', 'password': 'pass'})
    response = client.get('/finance/invoices')
    assert response.status_code == 200

def test_employee_no_access_finance(client, create_user):
    """Обычный сотрудник не должен видеть финансы."""
    user = create_user('emp', 'emp@test.com', 'pass', roles=['employee'])
    client.post('/auth/login', data={'email': 'emp@test.com', 'password': 'pass'})
    response = client.get('/finance/invoices', follow_redirects=False)
    assert response.status_code != 200