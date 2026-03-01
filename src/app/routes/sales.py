from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app.decorators import role_required
from app.models import Customer, Order, OrderItem, Product, Stock, Invoice  # добавили Invoice
from app.extensions import db
from datetime import datetime
from decimal import Decimal
import random
import string
from app.models.order_history import OrderHistory
from app.models.stock_log import StockLog
from flask import jsonify

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')

def generate_order_number():
    """Генерация уникального номера заказа"""
    while True:
        number = 'ORD-' + ''.join(random.choices(string.digits, k=8))
        if not Order.query.filter_by(order_number=number).first():
            return number

def generate_invoice_number():
    """Генерация уникального номера счёта"""
    while True:
        number = 'INV-' + ''.join(random.choices(string.digits, k=8))
        if not Invoice.query.filter_by(number=number).first():
            return number

# ==================== Контрагенты ====================
@sales_bp.route('/customers')
@login_required
@role_required('admin', 'manager', 'sales')
def customers_list():
    # ... (остаётся без изменений)
    search = request.args.get('search', '').strip()
    type_filter = request.args.get('type', '').strip()
    query = Customer.query
    if search:
        query = query.filter(
            db.or_(
                Customer.name.ilike(f'%{search}%'),
                Customer.email.ilike(f'%{search}%'),
                Customer.phone.ilike(f'%{search}%'),
                Customer.inn.ilike(f'%{search}%')
            )
        )
    if type_filter:
        query = query.filter_by(type=type_filter)
    customers = query.order_by(Customer.name).all()
    return render_template('sales/customers_list.html', customers=customers, search_query=search, type_filter=type_filter)

@sales_bp.route('/customers/search')
@login_required
@role_required('admin', 'manager', 'sales')
def customer_search():
    # ... (без изменений)
    query = request.args.get('q', '').strip()
    if not query or len(query) < 2:
        return jsonify({'results': []})
    
    customers = Customer.query.filter(
        db.or_(
            Customer.name.ilike(f'%{query}%'),
            Customer.email.ilike(f'%{query}%'),
            Customer.phone.ilike(f'%{query}%'),
            Customer.inn.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    results = [{
        'id': c.id,
        'text': f"{c.name} ({c.email or 'нет email'})"
    } for c in customers]
    
    return jsonify({'results': results})

@sales_bp.route('/customer/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'sales')
def customer_add():
    # ... (без изменений)
    if request.method == 'POST':
        customer = Customer(
            type=request.form['type'],
            name=request.form['name'],
            last_name=request.form.get('last_name'),
            first_name=request.form.get('first_name'),
            middle_name=request.form.get('middle_name'),
            legal_name=request.form.get('legal_name'),
            inn=request.form.get('inn'),
            kpp=request.form.get('kpp'),
            ogrn=request.form.get('ogrn'),
            phone=request.form.get('phone'),
            email=request.form.get('email'),
            address=request.form.get('address'),
            note=request.form.get('note')
        )
        db.session.add(customer)
        db.session.commit()
        flash('Контрагент добавлен', 'success')
        return redirect(url_for('sales.customers_list'))
    return render_template('sales/customer_form.html')

@sales_bp.route('/customer/<int:customer_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'sales')
def customer_edit(customer_id):
    # ... (без изменений)
    customer = Customer.query.get_or_404(customer_id)
    if request.method == 'POST':
        customer.type = request.form['type']
        customer.name = request.form['name']
        customer.last_name = request.form.get('last_name')
        customer.first_name = request.form.get('first_name')
        customer.middle_name = request.form.get('middle_name')
        customer.legal_name = request.form.get('legal_name')
        customer.inn = request.form.get('inn')
        customer.kpp = request.form.get('kpp')
        customer.ogrn = request.form.get('ogrn')
        customer.phone = request.form.get('phone')
        customer.email = request.form.get('email')
        customer.address = request.form.get('address')
        customer.note = request.form.get('note')
        customer.is_active = 'is_active' in request.form
        db.session.commit()
        flash('Контрагент обновлён', 'success')
        return redirect(url_for('sales.customers_list'))
    return render_template('sales/customer_form.html', customer=customer)

# ==================== Заказы ====================
@sales_bp.route('/orders')
@login_required
@role_required('admin', 'manager', 'sales')
def orders_list():
    # ... (без изменений)
    status = request.args.get('status')
    query = Order.query
    if status:
        query = query.filter_by(status=status)
    orders = query.order_by(Order.order_date.desc()).all()
    return render_template('sales/orders_list.html', orders=orders, current_status=status)

@sales_bp.route('/order/create', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'sales')
def order_create():
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        if not customer_id:
            flash('Выберите клиента', 'danger')
            return redirect(url_for('sales.order_create'))
        
        # Создаём заказ
        order = Order(
            order_number=generate_order_number(),
            customer_id=int(customer_id),
            created_by=current_user.id
        )
        db.session.add(order)
        db.session.flush()  # чтобы получить id

        # Получаем данные из формы
        product_ids = request.form.getlist('product_id[]')
        warehouse_ids = request.form.getlist('warehouse_id[]')
        quantities = request.form.getlist('quantity[]')
        total_amount = Decimal(0)

        for i in range(len(product_ids)):
            if not product_ids[i] or not warehouse_ids[i] or not quantities[i]:
                continue
            product = Product.query.get(int(product_ids[i]))
            warehouse_id = int(warehouse_ids[i])
            qty = Decimal(quantities[i])
            if product:
                # Проверяем наличие на выбранном складе
                stock = Stock.query.filter_by(product_id=product.id, warehouse_id=warehouse_id).first()
                if not stock or stock.available < qty:
                    flash(f'Недостаточно товара {product.name} на выбранном складе (доступно {stock.available if stock else 0})', 'danger')
                    db.session.rollback()
                    return redirect(url_for('sales.order_create'))

                # Берём цену из товара
                price = product.price or Decimal(0)
                total = qty * price
                item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    warehouse_id=warehouse_id,
                    quantity=qty,
                    price=price,
                    total=total
                )
                db.session.add(item)
                total_amount += total

        if total_amount == 0:
            flash('Заказ должен содержать хотя бы одну позицию', 'danger')
            db.session.rollback()
            return redirect(url_for('sales.order_create'))

        order.total_amount = total_amount
        db.session.commit()

        # ===== НОВЫЙ КОД: автоматическое создание счёта =====
        invoice = Invoice(
            number=generate_invoice_number(),
            customer_id=order.customer_id,
            issue_date=datetime.now().date(),
            due_date=None,
            total_amount=order.total_amount,
            description=f"Автоматически создан из заказа {order.order_number}",
            order_id=order.id,
            created_by_id=current_user.id
        )
        db.session.add(invoice)
        db.session.commit()
        # ====================================================

        flash('Заказ создан и сформирован счёт', 'success')
        return redirect(url_for('sales.order_detail', order_id=order.id))

    # GET: показать форму
    customers = Customer.query.all()
    products = Product.query.filter_by(is_active=True).all()
    return render_template('sales/order_form.html', customers=customers, products=products)

@sales_bp.route('/order/<int:order_id>')
@login_required
@role_required('admin', 'manager', 'sales')
def order_detail(order_id):
    # ... (без изменений)
    order = Order.query.get_or_404(order_id)
    return render_template('sales/order_detail.html', order=order)

@sales_bp.route('/order/<int:order_id>/status', methods=['POST'])
@login_required
@role_required('admin', 'manager', 'sales')
def order_change_status(order_id):
    # ... (без изменений, можно оставить как есть)
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    if new_status not in ['new', 'processing', 'completed', 'cancelled']:
        flash('Некорректный статус', 'danger')
        return redirect(url_for('sales.order_detail', order_id=order.id))

    old_status = order.status
    if old_status == new_status:
        flash('Статус уже установлен', 'info')
        return redirect(url_for('sales.order_detail', order_id=order.id))

    # Логика резервирования / списания
    try:
        if new_status == 'processing' and old_status != 'processing':
            # Резервируем товары с указанных складов
            for item in order.items:
                product = item.product
                warehouse_id = item.warehouse_id
                qty = item.quantity
                stock = Stock.query.filter_by(product_id=product.id, warehouse_id=warehouse_id).first()
                if not stock or stock.available < qty:
                    flash(f'Недостаточно товара {product.name} на складе {stock.warehouse.name if stock else "?"}', 'danger')
                    db.session.rollback()
                    return redirect(url_for('sales.order_detail', order_id=order.id))
                stock.reserved += qty

        elif new_status == 'completed' and old_status != 'completed':
            # Списываем товары с указанных складов
            for item in order.items:
                product = item.product
                warehouse_id = item.warehouse_id
                qty = item.quantity
                stock = Stock.query.filter_by(product_id=product.id, warehouse_id=warehouse_id).first()
                if not stock or stock.quantity < qty:
                    flash(f'Ошибка списания товара {product.name}', 'danger')
                    db.session.rollback()
                    return redirect(url_for('sales.order_detail', order_id=order.id))
                old_qty = stock.quantity
                stock.quantity -= qty
                stock.reserved -= qty  # снимаем резерв
                # Запись в историю склада
                log = StockLog(
                    stock_id=stock.id,
                    old_quantity=old_qty,
                    new_quantity=stock.quantity,
                    change=-qty,
                    created_by=current_user.id,
                    comment=f"Списание по заказу {order.order_number}"
                )
                db.session.add(log)

        elif new_status == 'cancelled' and old_status == 'processing':
            # Снимаем резерв с указанных складов
            for item in order.items:
                product = item.product
                warehouse_id = item.warehouse_id
                qty = item.quantity
                stock = Stock.query.filter_by(product_id=product.id, warehouse_id=warehouse_id).first()
                if stock:
                    stock.reserved -= qty

        # Меняем статус заказа
        order.status = new_status

        # Записываем историю заказа
        history = OrderHistory(
            order_id=order.id,
            old_status=old_status,
            new_status=new_status,
            changed_by=current_user.id,
            comment=request.form.get('comment', '')
        )
        db.session.add(history)

        db.session.commit()
        flash(f'Статус заказа изменён на {new_status}', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка при изменении статуса: {str(e)}', 'danger')

    # Определяем, откуда пришёл запрос (список или детальная)
    referrer = request.referrer
    if referrer and '/sales/orders' in referrer:
        return redirect(url_for('sales.orders_list'))
    else:
        return redirect(url_for('sales.order_detail', order_id=order.id))