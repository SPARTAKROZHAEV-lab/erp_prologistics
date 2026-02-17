from ..extensions import db
from datetime import datetime

# Таблица связи между пользователями и ролями (многие-ко-многим)
user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)

class Role(db.Model):
    __tablename__ = 'roles'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    users = db.relationship('User', secondary=user_roles, back_populates='roles')

    def __repr__(self):
        return f'<Role {self.name}>'
