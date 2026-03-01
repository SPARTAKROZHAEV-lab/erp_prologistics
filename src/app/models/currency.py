# app/models/currency.py
from app.extensions import db
from datetime import datetime

class Currency(db.Model):
    """Справочник валют"""
    __tablename__ = 'currencies'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(3), nullable=False, unique=True)  # ISO код, например RUB, USD
    name = db.Column(db.String(50), nullable=False)               # название валюты
    symbol = db.Column(db.String(5), nullable=True)               # символ, например ₽, $
    exchange_rate = db.Column(db.Numeric(10, 4), nullable=False, default=1.0)  # курс к базовой валюте
    is_base = db.Column(db.Boolean, default=False)                # базовая валюта (обычно RUB)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с товарами
    products = db.relationship('Product', backref='currency', lazy='dynamic')

    def __repr__(self):
        return f'<Currency {self.code}>'