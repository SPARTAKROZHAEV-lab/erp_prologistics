# app/models/department.py
from app.extensions import db

class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    
    # Связь с должностями (один ко многим)
    positions = db.relationship('Position', backref='department', lazy=True)
    
    def __repr__(self):
        return f'<Department {self.name}>'