# app/routes/auth.py
# Маршруты для аутентификации: регистрация, вход, выход, тестовый админ-маршрут

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from ..forms import RegistrationForm, LoginForm
from ..models import User
from ..extensions import db
from app.decorators import admin_required  # Декоратор для проверки роли admin

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Регистрация нового пользователя.
    GET: показать форму регистрации.
    POST: обработать данные формы, создать пользователя.
    """
    # Если пользователь уже залогинен, перенаправляем на главную
    if current_user.is_authenticated:
        return redirect(url_for('hello'))

    form = RegistrationForm()
    if form.validate_on_submit():
        # Создаём нового пользователя
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)  # Хешируем пароль
        db.session.add(user)
        db.session.commit()
        flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Вход пользователя в систему.
    GET: показать форму входа.
    POST: проверить учётные данные и выполнить вход.
    """
    # Если пользователь уже залогинен, перенаправляем на главную
    if current_user.is_authenticated:
        return redirect(url_for('hello'))

    form = LoginForm()
    if form.validate_on_submit():
        # Ищем пользователя по email
        user = User.query.filter_by(email=form.email.data).first()
        # Проверяем пароль
        if user and user.check_password(form.password.data):
            login_user(user)  # Запоминаем пользователя в сессии
            flash('Вы успешно вошли!', 'success')

            # Обрабатываем параметр next для редиректа после логина
            next_page = request.args.get('next')
            # Проверяем, что next_page ведёт на внутренний URL (безопасность)
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('hello')
            return redirect(next_page)
        else:
            flash('Неверный email или пароль', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """
    Выход пользователя из системы.
    """
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('hello'))


@auth_bp.route('/admin-test')
@admin_required
def admin_test():
    """
    Тестовая страница, доступная только пользователям с ролью admin.
    Используется для проверки работы декоратора admin_required.
    """
    return "Поздравляю! Вы администратор и видите эту секретную страницу."