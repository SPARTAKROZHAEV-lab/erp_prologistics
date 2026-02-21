# app/routes/hr.py
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required
from app.decorators import role_required
from app.models import Employee, Department, Position
from app.extensions import db

hr_bp = Blueprint('hr', __name__, url_prefix='/hr')

@hr_bp.route('/employees')
@login_required
@role_required('admin', 'manager', 'hr')  # позже добавим роль hr
def employees_list():
    employees = Employee.query.all()
    return render_template('hr/employees_list.html', employees=employees)

@hr_bp.route('/employee/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'hr')
def employee_add():
    if request.method == 'POST':
        # Обработка формы добавления (пока упрощённо)
        employee = Employee(
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            email=request.form['email'],
            hire_date=request.form['hire_date'],
            position_id=request.form['position_id'] or None
        )
        db.session.add(employee)
        db.session.commit()
        flash('Сотрудник добавлен', 'success')
        return redirect(url_for('hr.employees_list'))
    positions = Position.query.all()
    departments = Department.query.all()
    return render_template('hr/employee_form.html', positions=positions, departments=departments)