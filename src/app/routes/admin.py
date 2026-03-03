# app/routes/admin.py
from flask import Blueprint, render_template, flash, redirect, url_for, request, session
from flask_login import login_required, login_user, current_user
from app.decorators import admin_required
from app.models.user import User
from app.models.role import Role
from app.extensions import db

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/users')
@login_required
@admin_required
def users_list():
    users = User.query.all()
    return render_template('admin/users_list.html', users=users)

@admin_bp.route('/user/<int:user_id>/roles', methods=['GET', 'POST'])
@login_required
@admin_required
def user_roles(user_id):
    user = User.query.get_or_404(user_id)
    all_roles = Role.query.all()

    if request.method == 'POST':
        selected_role_ids = request.form.getlist('roles')
        user.roles = []
        for role_id in selected_role_ids:
            role = Role.query.get(int(role_id))
            if role:
                user.roles.append(role)
        db.session.commit()
        flash(f'Роли пользователя {user.email} обновлены.', 'success')
        return redirect(url_for('admin.users_list'))

    return render_template('admin/user_roles.html', user=user, all_roles=all_roles)

@admin_bp.route('/impersonate/<int:user_id>')
@login_required
@admin_required
def impersonate(user_id):
    """Войти под другим пользователем, сохранив оригинального админа в сессии"""
    # Сохраняем ID текущего админа в сессии, чтобы потом вернуться
    session['original_user_id'] = current_user.id
    user = User.query.get_or_404(user_id)
    login_user(user)
    flash(f'Вы вошли как {user.email}', 'success')
    return redirect(url_for('index'))

@admin_bp.route('/revert-impersonate')
@login_required
def revert_impersonate():
    """Вернуться к оригинальному администратору"""
    original_user_id = session.get('original_user_id')
    if not original_user_id:
        flash('Нет сохранённого пользователя для возврата', 'warning')
        return redirect(url_for('index'))
    original_user = User.query.get(original_user_id)
    if not original_user:
        flash('Оригинальный пользователь не найден', 'danger')
        return redirect(url_for('index'))
    login_user(original_user)
    session.pop('original_user_id', None)
    flash(f'Вы вернулись к учётной записи {original_user.email}', 'success')
    return redirect(url_for('admin.users_list'))
@admin_bp.route('/init-db')
@login_required
def init_db():
    # Проверяем, что пользователь — admin
    if not current_user.has_role('admin'):
        return "Доступ запрещён", 403
    try:
        import subprocess
        import sys
        result = subprocess.run([sys.executable, 'seed_test_data.py'], capture_output=True, text=True, cwd='/app/src')
        return f"<pre>{result.stdout}\n{result.stderr}</pre>"
    except Exception as e:
        return f"Ошибка: {e}"