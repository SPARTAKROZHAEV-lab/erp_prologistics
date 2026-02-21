# seed_roles.py
# Скрипт для добавления базовых ролей в базу данных (исправленная версия для работы в контейнере).

from app import create_app
from app.extensions import db
from app.models.role import Role

app = create_app()
with app.app_context():
    roles_to_add = [
        {'name': 'admin', 'description': 'Супер-администратор с полным доступом'},
        {'name': 'manager', 'description': 'Менеджер (управление заказами, клиентами)'},
        {'name': 'accountant', 'description': 'Бухгалтер (доступ к финансам)'},
        {'name': 'employee', 'description': 'Сотрудник (базовый доступ)'},
    ]
    
    for role_data in roles_to_add:
        existing_role = Role.query.filter_by(name=role_data['name']).first()
        if not existing_role:
            role = Role(name=role_data['name'], description=role_data['description'])
            db.session.add(role)
            print(f"Добавлена роль: {role_data['name']}")
        else:
            print(f"Роль уже существует: {role_data['name']}")
    
    db.session.commit()
    print("Инициализация ролей завершена.")