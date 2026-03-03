# app/routes/hr.py
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required
from app.decorators import role_required
from app.models import Employee, Department, Position, User
from app.extensions import db
from datetime import datetime
from flask import Blueprint, render_template, flash, redirect, url_for, request, jsonify
from app.models import Permission
from app.decorators import permission_required
from app.models.role import Role


hr_bp = Blueprint('hr', __name__, url_prefix='/hr')

@hr_bp.route('/employees')
@login_required
@role_required('admin', 'manager', 'hr')
def employees_list():
    """Список всех сотрудников с возможностью поиска"""
    # Получаем поисковый запрос из параметра q
    search_query = request.args.get('q', '').strip()
    
    # Базовый запрос
    query = Employee.query
    
    # Если есть поисковый запрос, фильтруем
    if search_query:
        # Ищем по имени, фамилии, email или названию должности
        query = query.join(Position, isouter=True).filter(
            db.or_(
                Employee.first_name.ilike(f'%{search_query}%'),
                Employee.last_name.ilike(f'%{search_query}%'),
                Employee.email.ilike(f'%{search_query}%'),
                Position.title.ilike(f'%{search_query}%')
            )
        )
    
    # Получаем отфильтрованных сотрудников
    employees = query.all()
    
    return render_template('hr/employees_list.html', 
                          employees=employees,
                          search_query=search_query)

@hr_bp.route('/employee/<int:employee_id>')
@login_required
@role_required('admin', 'manager', 'hr')
def employee_detail(employee_id):
    """Детальная страница сотрудника"""
    employee = Employee.query.get_or_404(employee_id)
    return render_template('hr/employee_detail.html', employee=employee)

@hr_bp.route('/employees/search')
@login_required
@role_required('admin', 'manager', 'hr')
def employee_search():
    """Возвращает JSON с подходящими сотрудниками для автодополнения"""
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'results': []})
    
    # Ищем сотрудников по имени, фамилии, email или должности
    employees = Employee.query.join(Position, isouter=True).filter(
        db.or_(
            Employee.first_name.ilike(f'%{query}%'),
            Employee.last_name.ilike(f'%{query}%'),
            Employee.email.ilike(f'%{query}%'),
            Position.title.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    results = []
    for emp in employees:
        results.append({
            'id': emp.id,
            'full_name': emp.full_name,
            'email': emp.email,
            'position': emp.position.title if emp.position else '',
            'url': url_for('hr.employee_detail', employee_id=emp.id)
        })
    
    return jsonify({'results': results})

@hr_bp.route('/employee/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'hr')
def employee_add():
    """Добавление нового сотрудника (создание или привязка пользователя)"""
    if request.method == 'POST':
        # --- Основные поля сотрудника ---
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        middle_name = request.form.get('middle_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')
        salary = request.form.get('salary')
        if salary:
            salary = float(salary)
        else:
            salary = None

        # Дата рождения (может быть пустой)
        birth_date_str = request.form.get('birth_date')
        if birth_date_str:
            birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        else:
            birth_date = None

        # Дата найма (обязательна)
        hire_date = datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date()

        # Должность
        position_id = request.form.get('position_id')
        if position_id:
            position_id = int(position_id)
        else:
            position_id = None

        # --- Создаём объект сотрудника ---
        employee = Employee(
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name,
            email=email,
            phone=phone,
            address=address,
            salary=salary,
            birth_date=birth_date,
            hire_date=hire_date,
            position_id=position_id
        )

        # --- Обработка привязки пользователя ---
        user_option = request.form.get('user_option')
        if user_option == 'existing':
            user_id = request.form.get('user_id')
            if user_id:
                user = User.query.get(int(user_id))
                if user:
                    employee.user_id = user.id
        elif user_option == 'new':
            new_email = request.form.get('new_email')
            new_username = request.form.get('new_username')
            new_password = request.form.get('new_password')
            if new_email and new_username and new_password:
                # Проверка уникальности
                if User.query.filter_by(email=new_email).first():
                    flash('Пользователь с таким email уже существует', 'danger')
                elif User.query.filter_by(username=new_username).first():
                    flash('Пользователь с таким именем уже существует', 'danger')
                else:
                    user = User(username=new_username, email=new_email)
                    user.set_password(new_password)
                    db.session.add(user)
                    db.session.flush()  # получить id
                    employee.user_id = user.id
            else:
                flash('Заполните все поля для создания нового пользователя', 'danger')

        # Сохраняем сотрудника в БД
        db.session.add(employee)
        db.session.commit()
        flash('Сотрудник добавлен', 'success')
        return redirect(url_for('hr.employees_list'))

    # GET-запрос: показываем форму
    positions = Position.query.all()
    departments = Department.query.all()
    available_users = User.query.filter(~User.employee.has()).all()
    return render_template(
        'hr/employee_form.html',
        positions=positions,
        departments=departments,
        available_users=available_users,
        edit_mode=False
    )


@hr_bp.route('/employee/<int:employee_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'hr')
def employee_edit(employee_id):
    """Редактирование данных сотрудника"""
    employee = Employee.query.get_or_404(employee_id)

    if request.method == 'POST':
        # --- Обновляем поля из формы ---
        employee.first_name = request.form['first_name']
        employee.last_name = request.form['last_name']
        employee.middle_name = request.form.get('middle_name')
        employee.email = request.form.get('email')
        employee.phone = request.form.get('phone')
        employee.address = request.form.get('address')

        # Зарплата (число)
        salary = request.form.get('salary')
        employee.salary = float(salary) if salary else None

        # Дата рождения
        birth_date_str = request.form.get('birth_date')
        if birth_date_str:
            employee.birth_date = datetime.strptime(birth_date_str, '%Y-%m-%d').date()
        else:
            employee.birth_date = None

        # Дата найма (обязательна)
        employee.hire_date = datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date()

        # Должность
        position_id = request.form.get('position_id')
        employee.position_id = int(position_id) if position_id else None

        # Активность (чекбокс)
        employee.is_active = 'is_active' in request.form

        db.session.commit()
        flash('Данные сотрудника обновлены', 'success')
        return redirect(url_for('hr.employee_detail', employee_id=employee.id))

    # GET-запрос: показываем форму с предзаполненными данными
    positions = Position.query.all()
    departments = Department.query.all()
    return render_template(
        'hr/employee_form.html',
        employee=employee,
        positions=positions,
        departments=departments,
        edit_mode=True
    )


@hr_bp.route('/employee/<int:employee_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def employee_delete(employee_id):
    """Удаление сотрудника (жёсткое удаление)"""
    employee = Employee.query.get_or_404(employee_id)
    db.session.delete(employee)
    db.session.commit()
    flash('Сотрудник удалён', 'success')
    return redirect(url_for('hr.employees_list'))

@hr_bp.route('/roles')
@login_required
@role_required('admin', 'hr')
def roles_list():
    """Список ролей (доступно админу и HR)"""
    roles = Role.query.all()
    return render_template('hr/roles_list.html', roles=roles)

@hr_bp.route('/roles/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'hr')
def role_add():
    """Создание новой роли"""
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        if Role.query.filter_by(name=name).first():
            flash('Роль с таким именем уже существует', 'danger')
        else:
            role = Role(name=name, description=description)
            db.session.add(role)
            db.session.commit()
            flash('Роль создана', 'success')
            return redirect(url_for('hr.roles_list'))
    return render_template('hr/role_form.html')

@hr_bp.route('/roles/<int:role_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'hr')
def role_edit(role_id):
    """Редактирование роли и назначение разрешений"""
    role = Role.query.get_or_404(role_id)
    all_permissions = Permission.query.all()
    
    if request.method == 'POST':
        role.name = request.form['name']
        role.description = request.form.get('description', '')
        # Обработка разрешений
        selected_perms = request.form.getlist('permissions')
        role.permissions = []
        for perm_id in selected_perms:
            perm = Permission.query.get(int(perm_id))
            if perm:
                role.permissions.append(perm)
        db.session.commit()
        flash('Роль обновлена', 'success')
        return redirect(url_for('hr.roles_list'))
    
    return render_template('hr/role_form.html', role=role, permissions=all_permissions)

@hr_bp.route('/roles/<int:role_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def role_delete(role_id):
    """Удаление роли (только админ)"""
    role = Role.query.get_or_404(role_id)
    if role.name in ['admin', 'manager', 'hr', 'storekeeper', 'accountant', 'employee']:
        flash('Нельзя удалить системную роль', 'danger')
    else:
        db.session.delete(role)
        db.session.commit()
        flash('Роль удалена', 'success')
    return redirect(url_for('hr.roles_list'))

@hr_bp.route('/roles/<int:role_id>/permissions', methods=['GET', 'POST'])
@login_required
@permission_required('assign_permissions')
def role_permissions(role_id):
    role = Role.query.get_or_404(role_id)
    if request.method == 'POST':
        selected_perms = request.form.getlist('permissions')
        role.permissions = []
        for perm_codename in selected_perms:
            perm = Permission.query.filter_by(codename=perm_codename).first()
            if perm:
                role.permissions.append(perm)
        db.session.commit()
        flash('Права роли обновлены', 'success')
        return redirect(url_for('hr.roles_list'))
    all_perms = Permission.query.order_by(Permission.name).all()
    role_perms = {p.codename for p in role.permissions}
    return render_template('hr/role_permissions.html', role=role, all_perms=all_perms, role_perms=role_perms)