# app/models/transaction.py
# Модель финансовой транзакции (доход/расход)

from app.extensions import db
from datetime import datetime

class Transaction(db.Model):
    """
    Модель для хранения всех финансовых операций:
    - поступления от продаж (доходы)
    - выплаты поставщикам (расходы)
    - прочие доходы/расходы
    - корректировки
    """
    __tablename__ = 'transactions'

    # Первичный ключ
    id = db.Column(db.Integer, primary_key=True)

    # Тип транзакции: income (доход) или expense (расход)
    # Позже можно расширить, например, transfer (перевод между счетами)
    type = db.Column(db.Enum('income', 'expense', name='transaction_type_enum'), nullable=False, index=True)

    # Сумма транзакции (положительная)
    amount = db.Column(db.Numeric(10, 2), nullable=False)

    # Валюта (по умолчанию RUB, но можно хранить код валюты)
    currency = db.Column(db.String(3), nullable=False, default='RUB')

    # Дата и время совершения операции (не момент записи в БД, а фактическая дата операции)
    transaction_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Описание/назначение платежа
    description = db.Column(db.Text, nullable=True)

    # Статус транзакции:
    # planned   - запланировано (например, выставлен счёт)
    # completed - выполнено (деньги поступили/списаны)
    # cancelled - отменено
    status = db.Column(db.Enum('planned', 'completed', 'cancelled', name='transaction_status_enum'),
                       nullable=False, default='planned')

    # Связь с заказом (если транзакция относится к конкретному заказу)
    # Заказ может иметь несколько транзакций (частичная оплата, возврат)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True, index=True)
    order = db.relationship('Order', backref=db.backref('transactions', lazy='dynamic'))

    # Связь с контрагентом (клиент или поставщик)
    # Для расходов это может быть поставщик, для доходов — клиент
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True, index=True)
    customer = db.relationship('Customer', backref=db.backref('transactions', lazy='dynamic'))

    # Связь с пользователем, который создал/подтвердил транзакцию (для аудита)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('transaction_categories.id'), nullable=True, index=True)
    # category = db.relationship('TransactionCategory', backref='transactions')  # связь уже есть в другой модели
    created_by = db.relationship('User', foreign_keys=[created_by_id])

    # Дата和时间 создания записи в БД
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Комментарий (для внутреннего использования)
    comment = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Transaction {self.id}: {self.type} {self.amount} {self.currency}>'