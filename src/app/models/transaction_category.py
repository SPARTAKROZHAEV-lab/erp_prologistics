# app/models/transaction_category.py
from app.extensions import db
from datetime import datetime

class TransactionCategory(db.Model):
    """
    Категория доходов/расходов для более детальной аналитики.
    Например: Продажи, Аренда, Зарплата, Налоги и т.д.
    """
    __tablename__ = 'transaction_categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.Enum('income', 'expense', name='cat_type_enum'), nullable=False)  # категория только для доходов или расходов
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с транзакциями
    transactions = db.relationship('Transaction', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name} ({self.type})>'