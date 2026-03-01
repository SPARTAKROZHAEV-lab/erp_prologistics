# app/models/payment.py
# Модель платежа (оплаты по счёту)

from app.extensions import db
from datetime import datetime

class Payment(db.Model):
    """
    Платёж, поступивший в счёт оплаты инвойса.
    При создании платежа со статусом 'completed' автоматически создаётся
    транзакция типа 'income' (если это поступление денег).
    """
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    # Связь с инвойсом
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False, index=True)
    invoice = db.relationship('Invoice', backref=db.backref('payments', lazy='dynamic', cascade='all, delete-orphan'))
    # Сумма платежа
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    # Дата платежа
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    # Способ оплаты (наличные, банк, карта и т.д.)
    method = db.Column(db.String(50), nullable=False, default='cash')
    # Номер платежного документа (п/п, чек и т.п.)
    reference = db.Column(db.String(100), nullable=True)
    # Связь с транзакцией (создаётся автоматически)
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=True, unique=True)
    transaction = db.relationship('Transaction', foreign_keys=[transaction_id], uselist=False)
    # Статус платежа: pending (ожидает), completed (проведён), failed (ошибка)
    status = db.Column(db.Enum('pending', 'completed', 'failed', name='payment_status_enum'),
                       nullable=False, default='pending')
    # Комментарий
    comment = db.Column(db.Text, nullable=True)
    # Кто создал
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_by = db.relationship('User', foreign_keys=[created_by_id])
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Payment {self.id}: {self.amount} for invoice {self.invoice_id}>'