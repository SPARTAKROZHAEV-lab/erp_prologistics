#!/usr/bin/env python
# seed_test_data.py
import random
import string
from datetime import datetime, timedelta
from decimal import Decimal
from app import create_app
from app.extensions import db
from app.models import (User, Role, Customer, Product, Category, Warehouse,
                        Stock, Order, OrderItem, Invoice, Payment, Transaction,
                        TransactionCategory, Unit, Currency)

app = create_app()
app.app_context().push()

def random_string(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def random_price(min=10, max=1000):
    return round(random.uniform(min, max), 2)

def random_date(start, end):
    return start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))

def create_categories():
    categories = ['Электроника', 'Одежда', 'Продукты', 'Книги', 'Мебель']
    for name in categories:
        if not Category.query.filter_by(name=name).first():
            db.session.add(Category(name=name))
    db.session.commit()
    print("✅ Категории созданы")

def create_units():
    units = [('шт', 'штука'), ('кг', 'килограмм'), ('л', 'литр'), ('м', 'метр')]
    for code, name in units:
        if not Unit.query.filter_by(code=code).first():
            db.session.add(Unit(code=code, name=name))
    db.session.commit()
    print("✅ Единицы измерения созданы")

def create_currencies():
    currencies = [
        ('RUB', 'Российский рубль', '₽', 1.0, True),
        ('USD', 'Доллар США', '$', 90.0, False),
        ('EUR', 'Евро', '€', 100.0, False)
    ]
    for code, name, symbol, rate, base in currencies:
        if not Currency.query.filter_by(code=code).first():
            db.session.add(Currency(code=code, name=name, symbol=symbol,
                                    exchange_rate=rate, is_base=base))
    db.session.commit()
    print("✅ Валюты созданы")

def create_customers():
    types = ['legal', 'individual']
    for i in range(1, 11):
        name = f"Контрагент {i}"
        if not Customer.query.filter_by(name=name).first():
            cust = Customer(
                type=random.choice(types),
                name=name,
                email=f"customer{i}@example.com",
                phone=f"+7{random.randint(900,999)}{random.randint(1000000,9999999)}",
                address=f"ул. Примерная, д. {i}",
                is_manufacturer=random.choice([True, False]),
                is_supplier=random.choice([True, False])
            )
            db.session.add(cust)
    db.session.commit()
    print("✅ Контрагенты созданы")

def create_products():
    categories = Category.query.all()
    units = Unit.query.all()
    currencies = Currency.query.all()
    manufacturers = Customer.query.filter_by(is_manufacturer=True).all()
    for i in range(1, 31):
        sku = f"SKU-{random_string(6)}"
        if Product.query.filter_by(sku=sku).first():
            continue
        price = random_price(100, 50000)
        purchase_price = price * random.uniform(0.5, 0.8)
        product = Product(
            sku=sku,
            name=f"Товар {i}",
            description=f"Описание товара {i}",
            price=price,
            purchase_price=purchase_price,
            cost=purchase_price,
            category_id=random.choice(categories).id if categories else None,
            is_active=True,
            unit_id=random.choice(units).id if units else None,
            manufacturer_id=random.choice(manufacturers).id if manufacturers else None,
            barcode=random_string(13),
            min_stock=random.randint(1, 5),
            max_stock=random.randint(10, 50),
            currency_id=random.choice(currencies).id if currencies else None
        )
        db.session.add(product)
    db.session.commit()
    print("✅ Товары созданы")

def create_warehouses():
    warehouses = ['Основной склад', 'Дополнительный склад', 'Склад возвратов']
    for name in warehouses:
        if not Warehouse.query.filter_by(name=name).first():
            db.session.add(Warehouse(name=name))
    db.session.commit()
    print("✅ Склады созданы")

def create_stocks():
    products = Product.query.all()
    warehouses = Warehouse.query.all()
    for product in products:
        for warehouse in warehouses:
            if not Stock.query.filter_by(product_id=product.id, warehouse_id=warehouse.id).first():
                qty = random.randint(20, 200)
                reserved = random.randint(0, int(qty*0.3))
                stock = Stock(product_id=product.id, warehouse_id=warehouse.id,
                              quantity=qty, reserved=reserved)
                db.session.add(stock)
    db.session.commit()
    print("✅ Остатки созданы")

def create_orders():
    customers = Customer.query.all()
    products = Product.query.all()
    warehouses = Warehouse.query.all()
    statuses = ['new', 'processing', 'completed', 'cancelled']
    start_date = datetime.now() - timedelta(days=90)
    end_date = datetime.now()

    for i in range(1, 51):
        customer = random.choice(customers)
        order_date = random_date(start_date, end_date)
        status = random.choices(statuses, weights=[0.2, 0.3, 0.4, 0.1])[0]
        order = Order(
            order_number=f"ORD-{random_string(8)}",
            customer_id=customer.id,
            order_date=order_date,
            status=status,
            total_amount=0,
            created_by=1
        )
        db.session.add(order)
        db.session.flush()

        total = Decimal(0)
        for _ in range(random.randint(1, 5)):
            product = random.choice(products)
            warehouse = random.choice(warehouses)
            qty = random.randint(1, 5)
            price = product.price or Decimal(str(random_price(100, 1000)))
            item_total = qty * price
            item = OrderItem(
                order_id=order.id,
                product_id=product.id,
                warehouse_id=warehouse.id,
                quantity=qty,
                price=price,
                total=item_total
            )
            db.session.add(item)
            total += item_total

        order.total_amount = total
        db.session.flush()

        if status == 'completed':
            invoice = Invoice(
                number=f"INV-{random_string(8)}",
                customer_id=customer.id,
                issue_date=order_date + timedelta(days=1),
                due_date=order_date + timedelta(days=15),
                total_amount=total,
                description=f"Счёт по заказу {order.order_number}",
                order_id=order.id,
                created_by_id=1,
                status='paid'
            )
            db.session.add(invoice)
            db.session.flush()

            total_float = float(total)
            paid_amount = 0.0
            while paid_amount < total_float - 0.01:
                amount_float = min(random.uniform(0.3, 1.0) * total_float, total_float - paid_amount)
                amount_float = round(amount_float, 2)
                amount = Decimal(str(amount_float))
                payment = Payment(
                    invoice_id=invoice.id,
                    amount=amount,
                    payment_date=order_date + timedelta(days=random.randint(1, 10)),
                    method=random.choice(['cash', 'bank_transfer', 'card']),
                    reference=f"REF-{random_string(6)}",
                    status='completed',
                    created_by_id=1
                )
                db.session.add(payment)
                db.session.flush()

                transaction = Transaction(
                    type='income',
                    amount=amount,
                    currency='RUB',
                    transaction_date=payment.payment_date,
                    description=f"Оплата по счёту {invoice.number}",
                    status='completed',
                    order_id=order.id,
                    customer_id=customer.id,
                    created_by_id=1
                )
                db.session.add(transaction)
                paid_amount += amount_float

        elif status in ['new', 'processing']:
            invoice = Invoice(
                number=f"INV-{random_string(8)}",
                customer_id=customer.id,
                issue_date=order_date + timedelta(days=1),
                due_date=order_date + timedelta(days=15),
                total_amount=total,
                description=f"Счёт по заказу {order.order_number}",
                order_id=order.id,
                created_by_id=1,
                status='sent'
            )
            db.session.add(invoice)

        if i % 10 == 0:
            db.session.commit()

    db.session.commit()
    print("✅ Заказы, счета, платежи и транзакции созданы")

def create_transaction_categories():
    categories = [
        ('Продажи', 'income'),
        ('Аренда', 'expense'),
        ('Зарплата', 'expense'),
        ('Налоги', 'expense'),
        ('Прочие доходы', 'income'),
        ('Прочие расходы', 'expense'),
    ]
    for name, type_ in categories:
        if not TransactionCategory.query.filter_by(name=name).first():
            db.session.add(TransactionCategory(name=name, type=type_))
    db.session.commit()
    print("✅ Категории транзакций созданы")

def create_additional_transactions():
    customers = Customer.query.all()
    categories = TransactionCategory.query.filter_by(type='expense').all()
    start_date = datetime.now() - timedelta(days=90)
    end_date = datetime.now()
    for _ in range(20):
        tdate = random_date(start_date, end_date)
        amount = random_price(500, 50000)
        category = random.choice(categories) if categories else None
        customer = random.choice(customers) if random.random() > 0.5 else None
        transaction = Transaction(
            type='expense',
            amount=amount,
            currency='RUB',
            transaction_date=tdate,
            description=f"Расход {random_string(8)}",
            status='completed',
            customer_id=customer.id if customer else None,
            category_id=category.id if category else None,
            created_by_id=1
        )
        db.session.add(transaction)
    db.session.commit()
    print("✅ Дополнительные расходы созданы")

if __name__ == '__main__':
    print("🚀 Начало генерации тестовых данных...")
    create_categories()
    create_units()
    create_currencies()
    create_customers()
    create_products()
    create_warehouses()
    create_stocks()
    create_orders()
    create_transaction_categories()
    create_additional_transactions()
    print("✅ Все тестовые данные успешно созданы!")