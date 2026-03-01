# app/models/customer.py
from app.extensions import db
from datetime import datetime

class Customer(db.Model):
    __tablename__ = 'customers'

    # Новые поля для производителя/поставщика
    is_manufacturer = db.Column(db.Boolean, default=False)   # является производителем
    is_supplier = db.Column(db.Boolean, default=False)       # является поставщиком
    # Контактное лицо (если нужно отдельно от названия)
    contact_person = db.Column(db.String(100), nullable=True)

    id = db.Column(db.Integer, primary_key=True)
    # Тип контрагента: 'individual' - физлицо, 'legal' - юрлицо
    type = db.Column(db.String(20), nullable=False, default='individual')
    name = db.Column(db.String(200), nullable=False)  # Для юрлиц – название, для физлиц – ФИО
    # Для физлиц
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    middle_name = db.Column(db.String(100), nullable=True)
    # Для юрлиц
    legal_name = db.Column(db.String(200), nullable=True)  # полное наименование
    inn = db.Column(db.String(20), nullable=True)
    kpp = db.Column(db.String(20), nullable=True)
    ogrn = db.Column(db.String(20), nullable=True)
    # Контактные данные
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    address = db.Column(db.Text, nullable=True)
    # Дополнительно
    note = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Связь с заказами (продажи)
    orders = db.relationship('Order', backref='customer', lazy=True)
    # В будущем можно добавить связь с закупками

    def __repr__(self):
        return f'<Customer {self.name}>'