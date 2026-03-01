from app import create_app
from app.extensions import db
from app.models import Role, User

app = create_app()
with app.app_context():
    # Создаём базовые роли
    default_roles = ['admin', 'manager', 'accountant', 'employee', 'hr', 'storekeeper']
    for role_name in default_roles:
        if not Role.query.filter_by(name=role_name).first():
            db.session.add(Role(name=role_name))
    db.session.commit()
    print("✅ Базовые роли созданы или уже существуют")

    # Назначаем пользователю admin@example.com роль admin
    user = User.query.filter_by(email='admin@example.com').first()
    if user:
        admin_role = Role.query.filter_by(name='admin').first()
        if admin_role and admin_role not in user.roles:
            user.roles.append(admin_role)
            db.session.commit()
            print(f"✅ Роль admin назначена пользователю {user.email}")
        else:
            print("ℹ️ Роль admin уже есть у пользователя или роль не найдена")
    else:
        print("❌ Пользователь admin@example.com не найден")

    # Проверка ролей
    if user:
        print("🔍 Текущие роли пользователя:", [role.name for role in user.roles])