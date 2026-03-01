import pytest
from decimal import Decimal
from app.extensions import db
from app.models import Customer, Product, Warehouse, Stock, Order, OrderItem, Invoice

def test_order_creation_creates_invoice(auth_client, _db):
    """Проверка: при создании заказа автоматически создаётся счёт."""
    # Подготовка данных
    customer = Customer(name='Test Customer', type='legal')
    db.session.add(customer)
    warehouse = Warehouse(name='Main Warehouse')
    db.session.add(warehouse)
    product = Product(name='Test Product', sku='TP-001', price=Decimal('100.00'), is_active=True)
    db.session.add(product)
    db.session.flush()
    stock = Stock(product_id=product.id, warehouse_id=warehouse.id, quantity=50, reserved=0)
    db.session.add(stock)
    db.session.commit()

    # Действие: создание заказа
    data = {
        'customer_id': str(customer.id),
        'product_id[]': [str(product.id)],
        'warehouse_id[]': [str(warehouse.id)],
        'quantity[]': ['2']
    }
    response = auth_client.post('/sales/order/create', data=data, follow_redirects=True)
    assert response.status_code == 200

    # Проверка: заказ создан
    order = Order.query.filter_by(customer_id=customer.id).first()
    assert order is not None
    assert order.total_amount == 200.00

    # Проверка: позиция заказа создана
    order_item = OrderItem.query.filter_by(order_id=order.id).first()
    assert order_item is not None
    assert order_item.quantity == 2

    # Проверка: счёт создан автоматически
    invoice = Invoice.query.filter_by(order_id=order.id).first()
    assert invoice is not None
    assert invoice.total_amount == 200.00
    assert invoice.customer_id == customer.id

def test_order_processing_reserves_stock(auth_client, _db):
    """Проверка: при переводе заказа в статус 'processing' резервируются товары."""
    # Подготовка данных
    customer = Customer(name='Customer', type='legal')
    db.session.add(customer)
    warehouse = Warehouse(name='Warehouse')
    db.session.add(warehouse)
    product = Product(name='Product', sku='P-001', price=100, is_active=True)
    db.session.add(product)
    db.session.flush()
    stock = Stock(product_id=product.id, warehouse_id=warehouse.id, quantity=50, reserved=0)
    db.session.add(stock)
    db.session.commit()

    # Создаём заказ (через ORM, чтобы не дублировать логику)
    order = Order(
        order_number='ORD-TEST-001',
        customer_id=customer.id,
        status='new',
        total_amount=200
    )
    db.session.add(order)
    db.session.flush()
    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        warehouse_id=warehouse.id,
        quantity=2,
        price=100,
        total=200
    )
    db.session.add(item)
    db.session.commit()

    # Меняем статус на processing
    response = auth_client.post(f'/sales/order/{order.id}/status', data={'status': 'processing'}, follow_redirects=True)
    assert response.status_code == 200

    # Проверяем резерв
    stock_updated = Stock.query.get(stock.id)
    assert stock_updated.reserved == 2

def test_order_completion_reduces_stock(auth_client, _db):
    """Проверка: при завершении заказа товары списываются со склада."""
    # Подготовка: заказ в статусе 'processing' с зарезервированным товаром
    customer = Customer(name='Customer', type='legal')
    db.session.add(customer)
    warehouse = Warehouse(name='Warehouse')
    db.session.add(warehouse)
    product = Product(name='Product', sku='P-001', price=100, is_active=True)
    db.session.add(product)
    db.session.flush()
    stock = Stock(product_id=product.id, warehouse_id=warehouse.id, quantity=50, reserved=0)
    db.session.add(stock)
    db.session.commit()

    order = Order(
        order_number='ORD-TEST-002',
        customer_id=customer.id,
        status='processing',
        total_amount=200
    )
    db.session.add(order)
    db.session.flush()
    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        warehouse_id=warehouse.id,
        quantity=2,
        price=100,
        total=200
    )
    db.session.add(item)
    stock.reserved = 2
    db.session.commit()

    # Меняем статус на completed
    response = auth_client.post(f'/sales/order/{order.id}/status', data={'status': 'completed'}, follow_redirects=True)
    assert response.status_code == 200

    # Проверяем: остаток уменьшился, резерв обнулился
    stock_updated = Stock.query.get(stock.id)
    assert stock_updated.quantity == 48
    assert stock_updated.reserved == 0

def test_order_cancellation_releases_reserve(auth_client, _db):
    """Проверка: при отмене заказа резерв снимается."""
    # Подготовка: заказ в статусе 'processing' с зарезервированным товаром
    customer = Customer(name='Customer', type='legal')
    db.session.add(customer)
    warehouse = Warehouse(name='Warehouse')
    db.session.add(warehouse)
    product = Product(name='Product', sku='P-001', price=100, is_active=True)
    db.session.add(product)
    db.session.flush()
    stock = Stock(product_id=product.id, warehouse_id=warehouse.id, quantity=50, reserved=0)
    db.session.add(stock)
    db.session.commit()

    order = Order(
        order_number='ORD-TEST-003',
        customer_id=customer.id,
        status='processing',
        total_amount=200
    )
    db.session.add(order)
    db.session.flush()
    item = OrderItem(
        order_id=order.id,
        product_id=product.id,
        warehouse_id=warehouse.id,
        quantity=2,
        price=100,
        total=200
    )
    db.session.add(item)
    stock.reserved = 2
    db.session.commit()

    # Меняем статус на cancelled
    response = auth_client.post(f'/sales/order/{order.id}/status', data={'status': 'cancelled'}, follow_redirects=True)
    assert response.status_code == 200

    # Проверяем: резерв обнулился, количество не изменилось
    stock_updated = Stock.query.get(stock.id)
    assert stock_updated.quantity == 50
    assert stock_updated.reserved == 0