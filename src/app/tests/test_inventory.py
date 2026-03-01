import pytest
from app.extensions import db
from app.models import Product, Warehouse, Stock, StockMovement

def test_stock_movement_transfers_quantity(auth_client, _db):
    """Проверка: перемещение товаров уменьшает остаток на одном складе и увеличивает на другом."""
    # 1. Подготовка: два склада, товар, остаток на первом складе
    warehouse1 = Warehouse(name='WH1')
    warehouse2 = Warehouse(name='WH2')
    db.session.add_all([warehouse1, warehouse2])
    product = Product(name='Test', sku='T-001', price=10, is_active=True)
    db.session.add(product)
    db.session.flush()
    stock1 = Stock(product_id=product.id, warehouse_id=warehouse1.id, quantity=100, reserved=0)
    stock2 = Stock(product_id=product.id, warehouse_id=warehouse2.id, quantity=0, reserved=0)
    db.session.add_all([stock1, stock2])
    db.session.commit()

    # 2. Действие: создаём перемещение через POST (если такой маршрут есть)
    # Если у вас нет отдельного маршрута для перемещения, можно напрямую вызвать логику
    # Предположим, что у вас есть /inventory/movement/create
    data = {
        'product_id': product.id,
        'from_warehouse_id': warehouse1.id,
        'to_warehouse_id': warehouse2.id,
        'quantity': 30,
        'comment': 'Test movement'
    }
    response = auth_client.post('/inventory/movement/create', data=data, follow_redirects=True)
    assert response.status_code == 200

    # 3. Проверка: остатки обновились
    stock1_updated = Stock.query.get(stock1.id)
    stock2_updated = Stock.query.get(stock2.id)
    assert stock1_updated.quantity == 70
    assert stock2_updated.quantity == 30

    # 4. Проверка: запись о перемещении создана
    movement = StockMovement.query.filter_by(product_id=product.id).first()
    assert movement is not None
    assert movement.quantity == 30