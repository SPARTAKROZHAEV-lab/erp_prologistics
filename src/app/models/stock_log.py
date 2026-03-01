from app.extensions import db
from datetime import datetime

class StockLog(db.Model):
    __tablename__ = 'stock_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    old_quantity = db.Column(db.Numeric(10, 2))
    new_quantity = db.Column(db.Numeric(10, 2))
    change = db.Column(db.Numeric(10, 2))  # new - old
    movement_id = db.Column(db.Integer, db.ForeignKey('stock_movements.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    comment = db.Column(db.Text, nullable=True)  # <-- добавлено
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    stock = db.relationship('Stock')
    movement = db.relationship('StockMovement')
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<StockLog {self.id}: {self.change}>'