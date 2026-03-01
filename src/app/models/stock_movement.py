from app.extensions import db
from datetime import datetime

class StockMovement(db.Model):
    __tablename__ = 'stock_movements'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    from_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=True)
    to_warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False)
    movement_type = db.Column(db.String(50), nullable=False)  # 'purchase', 'sale', 'transfer', 'adjustment'
    reference = db.Column(db.String(100), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    comment = db.Column(db.Text, nullable=True)
    
    product = db.relationship('Product', back_populates='movements')
    from_warehouse = db.relationship('Warehouse', foreign_keys=[from_warehouse_id])
    to_warehouse = db.relationship('Warehouse', foreign_keys=[to_warehouse_id])
    user = db.relationship('User')
    
    def __repr__(self):
        return f'<Movement {self.id}: {self.product_id} {self.quantity}>'
