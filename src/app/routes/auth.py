from flask import Blueprint, render_template, redirect, url_for, flash, request
from ..forms import RegistrationForm
from ..models import User
from ..extensions import db
import bcrypt

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Создаём нового пользователя
        user = User(
            username=form.username.data,
            email=form.email.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
        return redirect(url_for('auth.login'))  # пока login не создан, позже изменим
    return render_template('auth/register.html', form=form)
