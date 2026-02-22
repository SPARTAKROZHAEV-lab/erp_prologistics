from app import create_app
from app.extensions import db
from app.models.permission import Permission
from app.models.role import Role

app = create_app()
with app.app_context():
    # Список разрешений
    permissions = [
        # Администрирование
        {'name': 'Управление пользователями', 'codename': 'manage_users'},
        {'name': 'Управление ролями', 'codename': 'manage_roles'},
        
        # HR
        {'name': 'Просмотр сотрудников', 'codename': 'view_employees'},
        {'name': 'Добавление сотрудников', 'codename': 'add_employee'},
        {'name': 'Редактирование сотрудников', 'codename': 'edit_employee'},
        {'name': 'Удаление сотрудников', 'codename': 'delete_employee'},
        
        # Склад
        {'name': 'Просмотр товаров', 'codename': 'view_products'},
        {'name': 'Добавление товаров', 'codename': 'add_product'},
        {'name': 'Редактирование товаров', 'codename': 'edit_product'},
        {'name': 'Удаление товаров', 'codename': 'delete_product'},
        {'name': 'Просмотр складов', 'codename': 'view_warehouses'},
        {'name': 'Управление складами', 'codename': 'manage_warehouses'},
        {'name': 'Просмотр остатков', 'codename': 'view_stocks'},
        {'name': 'Корректировка остатков', 'codename': 'adjust_stocks'},
        {'name': 'Перемещение товаров', 'codename': 'move_stock'},
        
        # Продажи (добавим позже)
        {'name': 'Просмотр заказов', 'codename': 'view_orders'},
        {'name': 'Создание заказов', 'codename': 'create_orders'},
        
        # Финансы
        {'name': 'Просмотр финансов', 'codename': 'view_finance'},
        {'name': 'Редактирование финансов', 'codename': 'edit_finance'},
    ]
    
    for perm_data in permissions:
        if not Permission.query.filter_by(codename=perm_data['codename']).first():
            perm = Permission(name=perm_data['name'], codename=perm_data['codename'])
            db.session.add(perm)
    
    db.session.commit()
    
    # Назначим разрешения ролям (например, admin получит всё)
    admin_role = Role.query.filter_by(name='admin').first()
    if admin_role:
        all_perms = Permission.query.all()
        admin_role.permissions = all_perms
    
    # manager получит часть
    manager_role = Role.query.filter_by(name='manager').first()
    if manager_role:
        manager_perms = Permission.query.filter(Permission.codename.in_([
            'view_employees', 'add_employee', 'edit_employee',
            'view_products', 'add_product', 'edit_product',
            'view_warehouses', 'view_stocks', 'move_stock'
        ])).all()
        manager_role.permissions = manager_perms
    
    # hr получит HR-разрешения
    hr_role = Role.query.filter_by(name='hr').first()
    if hr_role:
        hr_perms = Permission.query.filter(Permission.codename.in_([
            'view_employees', 'add_employee', 'edit_employee', 'delete_employee'
        ])).all()
        hr_role.permissions = hr_perms
    
    # storekeeper получит складские
    storekeeper_role = Role.query.filter_by(name='storekeeper').first()
    if storekeeper_role:
        storekeeper_perms = Permission.query.filter(Permission.codename.in_([
            'view_products', 'view_warehouses', 'view_stocks', 'adjust_stocks', 'move_stock'
        ])).all()
        storekeeper_role.permissions = storekeeper_perms
    
    db.session.commit()
    print("Разрешения добавлены и назначены ролям.")