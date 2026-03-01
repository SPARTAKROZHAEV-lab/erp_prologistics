import pytest
from app.extensions import db
from app.models import Department, Position, Employee, User

# ЗАМЕНИТЕ ЭТИ URL НА РЕАЛЬНЫЕ ИЗ ВАШЕГО hr.py
DEPARTMENT_CREATE_URL = '/hr/department/add'   # или '/hr/department/create'
POSITION_CREATE_URL = '/hr/position/add'       # или '/hr/position/create'
EMPLOYEE_CREATE_URL = '/hr/employee/add'

def test_create_department(auth_client, _db):
    """Проверка создания отдела."""
    response = auth_client.post(DEPARTMENT_CREATE_URL, data={
        'name': 'IT Department',
        'description': 'Information Technology'
    }, follow_redirects=True)
    # Если 404, значит URL неверный – замените выше
    assert response.status_code == 200
    dept = Department.query.filter_by(name='IT Department').first()
    assert dept is not None
    assert dept.description == 'Information Technology'

def test_create_position(auth_client, _db):
    """Проверка создания должности."""
    # Сначала создаём отдел (если должность требует department_id)
    dept = Department(name='IT', description='IT Dept')
    db.session.add(dept)
    db.session.commit()

    response = auth_client.post(POSITION_CREATE_URL, data={
        'name': 'Developer',
        'description': 'Software Developer',
        'department_id': dept.id  # если требуется
    }, follow_redirects=True)
    assert response.status_code == 200
    pos = Position.query.filter_by(name='Developer').first()
    assert pos is not None
    assert pos.description == 'Software Developer'

def test_create_employee(auth_client, _db):
    """Проверка создания сотрудника с привязкой к пользователю."""
    # Создаём пользователя
    user = User(username='empuser', email='emp@test.com')
    user.set_password('pass')
    db.session.add(user)
    db.session.commit()

    # Создаём отдел и должность
    dept = Department(name='IT', description='IT')
    db.session.add(dept)
    db.session.flush()
    pos = Position(name='Dev', description='Developer', department_id=dept.id)
    db.session.add(pos)
    db.session.commit()

    response = auth_client.post(EMPLOYEE_CREATE_URL, data={
        'user_id': user.id,
        'department_id': dept.id,
        'position_id': pos.id,
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john@company.com',
        'phone': '123456789',
        'hire_date': '2026-01-01'
    }, follow_redirects=True)
    assert response.status_code == 200
    emp = Employee.query.filter_by(email='john@company.com').first()
    assert emp is not None
    assert emp.first_name == 'John'
    assert emp.last_name == 'Doe'
    assert emp.department_id == dept.id
    assert emp.position_id == pos.id
    assert emp.user_id == user.id

def test_employee_list_access(auth_client):
    """Проверка доступа к списку сотрудников."""
    response = auth_client.get('/hr/employees')
    assert response.status_code == 200