# app/models/order_history.py
from app.extensions import db
from datetime import datetime

class OrderHistory(db.Model):
    __tablename__ = 'order_history'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    old_status = db.Column(db.String(20), nullable=True)
    new_status = db.Column(db.String(20), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)
    comment = db.Column(db.Text, nullable=True)

    order = db.relationship('Order', backref='history')
    user = db.relationship('User')

    def __repr__(self):
        return f'<OrderHistory {self.id}: {self.old_status} -> {self.new_status}>'