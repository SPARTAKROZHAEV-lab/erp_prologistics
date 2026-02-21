# app/routes/hr.py
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required
from app.decorators import role_required
from app.models import Employee, Department, Position, User
from app.extensions import db
from datetime import datetime

hr_bp = Blueprint('hr', __name__, url_prefix='/hr')

@hr_bp.route('/employees')
@login_required
@role_required('admin', 'manager', 'hr')
def employees_list():
    """Список всех сотрудников"""
    employees = Employee.query.all()
    return render_template('hr/employees_list.html', employees=employees)

@hr_bp.route('/employee/<int:employee_id>')
@login_required
@role_required('admin', 'manager', 'hr')
def employee_detail(employee_id):
    """Детальная страница сотрудника"""
    employee = Employee.query.get_or_404(employee_id)
    return render_template('hr/employee_detail.html', employee=employee)

@hr_bp.route('/employee/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'hr')
def employee_add():
    """Добавление нового сотрудника"""
    if request.method == 'POST':
        # Получаем данные из формы
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form.get('email')
        hire_date = datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date()
        position_id = request.form.get('position_id') or None
        user_option = request.form.get('user_option')

        # Создаём сотрудника
        employee = Employee(
            first_name=first_name,
            last_name=last_name,
            email=email,
            hire_date=hire_date,
            position_id=position_id if position_id else None
        )

        # Обработка привязки пользователя
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
                if User.query.filter_by(email=new_email).first():
                    flash('Пользователь с таким email уже существует', 'danger')
                elif User.query.filter_by(username=new_username).first():
                    flash('Пользователь с таким именем уже существует', 'danger')
                else:
                    user = User(username=new_username, email=new_email)
                    user.set_password(new_password)
                    db.session.add(user)
                    db.session.flush()
                    employee.user_id = user.id
            else:
                flash('Заполните все поля для создания нового пользователя', 'danger')

        db.session.add(employee)
        db.session.commit()
        flash('Сотрудник добавлен', 'success')
        return redirect(url_for('hr.employees_list'))

    # GET-запрос: показываем форму
    positions = Position.query.all()
    departments = Department.query.all()
    available_users = User.query.filter(~User.employee.has()).all()
    return render_template('hr/employee_form.html', 
                          positions=positions, 
                          departments=departments, 
                          available_users=available_users,
                          edit_mode=False)

@hr_bp.route('/employee/<int:employee_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'hr')
def employee_edit(employee_id):
    """Редактирование данных сотрудника"""
    employee = Employee.query.get_or_404(employee_id)
    if request.method == 'POST':
        employee.first_name = request.form['first_name']
        employee.last_name = request.form['last_name']
        employee.email = request.form.get('email')
        employee.hire_date = datetime.strptime(request.form['hire_date'], '%Y-%m-%d').date()
        employee.position_id = request.form.get('position_id') or None
        db.session.commit()
        flash('Данные сотрудника обновлены', 'success')
        return redirect(url_for('hr.employee_detail', employee_id=employee.id))

    positions = Position.query.all()
    departments = Department.query.all()
    return render_template('hr/employee_form.html', 
                          employee=employee,
                          positions=positions, 
                          departments=departments,
                          edit_mode=True)

@hr_bp.route('/employee/<int:employee_id>/delete', methods=['POST'])
@login_required
@role_required('admin')  # Только админ может удалять
def employee_delete(employee_id):
    """Удаление сотрудника (жёсткое удаление)"""
    employee = Employee.query.get_or_404(employee_id)
    db.session.delete(employee)
    db.session.commit()
    flash('Сотрудник удалён', 'success')
    return redirect(url_for('hr.employees_list'))