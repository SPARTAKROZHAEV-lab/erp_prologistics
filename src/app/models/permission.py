from app.extensions import db

class Permission(db.Model):
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    codename = db.Column(db.String(80), unique=True, nullable=False)  # для проверок в коде
    description = db.Column(db.String(200), nullable=True)
    
    def __repr__(self):
        return f'<Permission {self.name}>'
