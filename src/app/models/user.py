from ..extensions import db
from datetime import datetime
from .role import user_roles
import bcrypt

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    roles = db.relationship('Role', secondary=user_roles, back_populates='users')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Хеширует и сохраняет пароль"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def check_password(self, password):
        """Проверяет пароль на соответствие хешу"""
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return self.active

    @property
    def is_anonymous(self):
        return False

    def get_id(self):


        return str(self.id)

    def has_role(self, role_name):
        """
        Проверяет, есть ли у пользователя роль с указанным именем.
        Возвращает True или False.
        """
        return any(role.name == role_name for role in self.roles)