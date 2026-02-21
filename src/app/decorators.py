# src/app/decorators.py
# Декораторы для проверки прав доступа на основе ролей.

from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

def role_required(*roles):
    """
    Декоратор, требующий у пользователя хотя бы одну из указанных ролей.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Пожалуйста, войдите в систему для доступа к этой странице.', 'warning')
                return redirect(url_for('auth.login'))
            
            user_roles = [role.name for role in current_user.roles]
            if any(role in user_roles for role in roles):
                return f(*args, **kwargs)
            else:
                flash('У вас недостаточно прав для доступа к этой странице.', 'danger')
                abort(403)
        return decorated_function
    return decorator

# Частные случаи для конкретных ролей
def admin_required(f):
    return role_required('admin')(f)

def manager_required(f):
    return role_required('manager')(f)

def accountant_required(f):
    return role_required('accountant')(f)

def employee_required(f):
    return role_required('employee')(f)