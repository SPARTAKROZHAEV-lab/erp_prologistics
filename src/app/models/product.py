# app/models/product.py
from app.extensions import db
from datetime import datetime
from decimal import Decimal
from app.models.customer import Customer

# Таблица связи товаров и поставщиков (поставщики теперь из Customer)
product_suppliers = db.Table('product_suppliers',
    db.Column('product_id', db.Integer, db.ForeignKey('products.id'), primary_key=True),
    db.Column('supplier_id', db.Integer, db.ForeignKey('customers.id'), primary_key=True)
)

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=True)          # цена продажи
    purchase_price = db.Column(db.Numeric(10, 2), nullable=True) # закупочная цена
    cost = db.Column(db.Numeric(10, 2), nullable=True)           # себестоимость (устарело, но оставим)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    # Новые поля
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=True)
    manufacturer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)  # производитель
    barcode = db.Column(db.String(50), nullable=True, unique=True)
    min_stock = db.Column(db.Numeric(10, 2), nullable=True)
    max_stock = db.Column(db.Numeric(10, 2), nullable=True)
    currency_id = db.Column(db.Integer, db.ForeignKey('currencies.id'), nullable=True)    # валюта цены

    # Связи
    category = db.relationship('Category', backref=db.backref('products', lazy='dynamic'))
    creator = db.relationship('User', foreign_keys=[created_by_id])
    stocks = db.relationship('Stock', back_populates='product', lazy='dynamic')
    movements = db.relationship('StockMovement', back_populates='product', lazy='dynamic')
    order_items = db.relationship('OrderItem', back_populates='product', lazy='dynamic')
    # Связь с единицей измерения
    unit_obj = db.relationship('Unit', foreign_keys=[unit_id])
    # Связь с производителем (из Customer)
    manufacturer = db.relationship('Customer', foreign_keys=[manufacturer_id])
    # Связь с валютой
    currency_rel = db.relationship('Currency', foreign_keys=[currency_id])
    # Связь с поставщиками (многие-ко-многим)
    suppliers = db.relationship('Customer', secondary=product_suppliers,
                                primaryjoin=(product_suppliers.c.product_id == id),
                                secondaryjoin=(product_suppliers.c.supplier_id == Customer.id),
                                backref=db.backref('supplied_products', lazy='dynamic'),
                                lazy='dynamic')

    def __repr__(self):
        return f'<Product {self.sku}: {self.name}>'