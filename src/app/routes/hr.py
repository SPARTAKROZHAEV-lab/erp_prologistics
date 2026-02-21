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
    employees = Employee.query.all()
    return render_template('hr/employees_list.html', employees=employees)

@hr_bp.route('/employee/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'hr')
def employee_add():
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
            # Проверяем, что все поля заполнены
            if new_email and new_username and new_password:
                # Проверяем уникальность
                if User.query.filter_by(email=new_email).first():
                    flash('Пользователь с таким email уже существует', 'danger')
                elif User.query.filter_by(username=new_username).first():
                    flash('Пользователь с таким именем уже существует', 'danger')
                else:
                    # Создаём нового пользователя
                    user = User(username=new_username, email=new_email)
                    user.set_password(new_password)
                    db.session.add(user)
                    db.session.flush()  # чтобы получить id
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
    # Список пользователей, у которых ещё нет сотрудника
    available_users = User.query.filter(~User.employee.has()).all()
    return render_template('hr/employee_form.html', positions=positions, departments=departments, available_users=available_users)