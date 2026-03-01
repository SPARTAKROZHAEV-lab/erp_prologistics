# app/models/unit.py
from app.extensions import db
from datetime import datetime

class Unit(db.Model):
    """Единица измерения товара (шт, кг, м и т.д.)"""
    __tablename__ = 'units'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)  # полное название
    code = db.Column(db.String(10), nullable=False, unique=True)  # краткий код (шт, кг)
    description = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с товарами
    products = db.relationship('Product', backref='unit_ref', lazy='dynamic')

    def __repr__(self):
        return f'<Unit {self.code}>'