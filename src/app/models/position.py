# app/models/position.py
from app.extensions import db

class Position(db.Model):
    __tablename__ = 'positions'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    description = db.Column(db.Text, nullable=True)
    salary_min = db.Column(db.Numeric(10, 2), nullable=True)
    salary_max = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Связь с сотрудниками (один ко многим)
    employees = db.relationship('Employee', backref='position', lazy=True)
    
    def __repr__(self):
        return f'<Position {self.title}>'