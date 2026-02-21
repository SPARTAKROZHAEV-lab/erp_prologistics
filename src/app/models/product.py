from app.extensions import db

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=True)
    cost = db.Column(db.Numeric(10, 2), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    barcode = db.Column(db.String(100), nullable=True, unique=True)
    unit = db.Column(db.String(20), default='шт')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())
    
    category = db.relationship('Category', backref='products')
    
    def __repr__(self):
        return f'<Product {self.sku} {self.name}>'