# app/models/invoice.py
# Модель счёта (инвойса)

from app.extensions import db
from datetime import date, datetime

class Invoice(db.Model):
    """
    Счёт на оплату. Может быть связан с заказом (order) или создан отдельно.
    """
    __tablename__ = 'invoices'

    id = db.Column(db.Integer, primary_key=True)
    # Уникальный номер счёта (можно генерировать автоматически)
    number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    # Связь с заказом (необязательная)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True, index=True)
    order = db.relationship('Order', backref=db.backref('invoices', lazy='dynamic'))
    # Связь с контрагентом (обязательная, если нет заказа, но можно брать из заказа)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False, index=True)
    customer = db.relationship('Customer', backref=db.backref('invoices', lazy='dynamic'))
    # Дата выставления
    issue_date = db.Column(db.Date, nullable=False, default=date.today)
    # Срок оплаты
    due_date = db.Column(db.Date, nullable=True)
    # Общая сумма счёта
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    # Статус: draft (черновик), sent (отправлен), paid (оплачен), cancelled (отменён), overdue (просрочен)
    status = db.Column(db.Enum('draft', 'sent', 'paid', 'cancelled', 'overdue', name='invoice_status_enum'),
                       nullable=False, default='draft')
    # Описание / примечание
    description = db.Column(db.Text, nullable=True)
    # Дата создания записи
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Кто создал
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    # Дата обновления
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Invoice {self.number}>'