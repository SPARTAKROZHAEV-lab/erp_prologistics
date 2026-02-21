from app.extensions import db

class Stock(db.Model):
    __tablename__ = 'stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    warehouse_id = db.Column(db.Integer, db.ForeignKey('warehouses.id'), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), default=0)
    reserved = db.Column(db.Numeric(10, 2), default=0)
    min_stock = db.Column(db.Numeric(10, 2), default=0)
    max_stock = db.Column(db.Numeric(10, 2), nullable=True)
    
    product = db.relationship('Product', backref='stocks')
    warehouse = db.relationship('Warehouse', backref='stocks')
    
    __table_args__ = (db.UniqueConstraint('product_id', 'warehouse_id', name='unique_product_warehouse'),)
    
    @property
    def available(self):
        return self.quantity - self.reserved
    
    def __repr__(self):
        return f'<Stock {self.product_id} @ {self.warehouse_id}: {self.quantity}>'