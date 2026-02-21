# src/app/routes/admin.py
# Маршруты для административной панели (управление пользователями и ролями)

from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required
from app.decorators import admin_required
from app.models.user import User
from app.models.role import Role
from app.extensions import db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/users')
@login_required
@admin_required
def users_list():
    """
    Страница со списком всех пользователей (только для админов).
    """
    users = User.query.all()
    return render_template('admin/users_list.html', users=users)

@admin_bp.route('/user/<int:user_id>/roles', methods=['GET', 'POST'])
@login_required
@admin_required
def user_roles(user_id):
    """
    Страница управления ролями конкретного пользователя.
    GET: показать форму с чекбоксами ролей.
    POST: сохранить выбранные роли.
    """
    user = User.query.get_or_404(user_id)
    all_roles = Role.query.all()

    if request.method == 'POST':
        # Получаем список ID ролей из формы (через чекбоксы)
        selected_role_ids = request.form.getlist('roles')
        # Очищаем текущие роли пользователя
        user.roles = []
        # Добавляем выбранные роли
        for role_id in selected_role_ids:
            role = Role.query.get(int(role_id))
            if role:
                user.roles.append(role)
        db.session.commit()
        flash(f'Роли пользователя {user.email} обновлены.', 'success')
        return redirect(url_for('admin.users_list'))

    return render_template('admin/user_roles.html', user=user, all_roles=all_roles)