import pytest
from decimal import Decimal
from app.extensions import db
from app.models import Invoice, Payment, Transaction, Customer

def test_create_invoice(auth_client, _db):
    """Создание счёта через POST-запрос."""
    # Создаём клиента
    customer = Customer(name='Test Customer', type='legal')
    db.session.add(customer)
    db.session.commit()

    data = {
        'number': 'INV-TEST-001',
        'customer_id': str(customer.id),
        'issue_date': '2026-02-22',
        'due_date': '2026-03-22',
        'total_amount': '1000.00',
        'description': 'Test invoice',
        'order_id': ''
    }
    response = auth_client.post('/finance/invoice/create', data=data, follow_redirects=True)
    assert response.status_code == 200
    content = response.data.decode('utf-8')
    assert 'Счёт успешно создан' in content

    invoice = Invoice.query.filter_by(number='INV-TEST-001').first()
    assert invoice is not None
    assert invoice.total_amount == 1000.00

def test_add_payment(auth_client, _db):
    """Добавление платежа к счёту и проверка создания транзакции."""
    # Создаём клиента
    customer = Customer(name='Customer', type='legal')
    db.session.add(customer)
    db.session.commit()

    # Создаём счёт
    invoice = Invoice(
        number='INV-002',
        customer_id=customer.id,
        issue_date='2026-02-22',
        total_amount=Decimal('500.00'),
        created_by_id=None
    )
    db.session.add(invoice)
    db.session.commit()

    # Добавляем платёж
    response = auth_client.post(f'/finance/invoice/{invoice.id}/add_payment', data={
        'amount': '200.00',
        'payment_date': '2026-02-22T12:00',
        'method': 'bank_transfer',
        'status': 'completed'
    }, follow_redirects=True)
    assert response.status_code == 200
    content = response.data.decode('utf-8')
    assert 'Платёж добавлен' in content

    # Проверяем платёж
    payment = Payment.query.filter_by(invoice_id=invoice.id).first()
    assert payment is not None
    assert payment.amount == Decimal('200.00')

    # Проверяем транзакцию
    transaction = Transaction.query.filter_by(description=f'Оплата по счёту {invoice.number}').first()
    assert transaction is not None
    assert transaction.type == 'income'
    assert transaction.amount == Decimal('200.00')