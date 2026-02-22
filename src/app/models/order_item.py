# app/models/order_item.py
from app.extensions import db

class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)  # цена на момент заказа
    total = db.Column(db.Numeric(10, 2), nullable=False)  # quantity * price

    product = db.relationship('Product')

    def __repr__(self):
        return f'<OrderItem {self.id}>'