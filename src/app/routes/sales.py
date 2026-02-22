# app/routes/sales.py
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from app.decorators import role_required
from app.models import Customer, Order, OrderItem, Product, Stock
from app.extensions import db
from datetime import datetime
from decimal import Decimal
import random
import string

sales_bp = Blueprint('sales', __name__, url_prefix='/sales')

def generate_order_number():
    """Генерация уникального номера заказа"""
    while True:
        number = 'ORD-' + ''.join(random.choices(string.digits, k=8))
        if not Order.query.filter_by(order_number=number).first():
            return number

# ==================== Клиенты ====================
@sales_bp.route('/customers')
@login_required
@role_required('admin', 'manager', 'sales')
def customers_list():
    customers = Customer.query.all()
    return render_template('sales/customers_list.html', customers=customers)

@sales_bp.route('/customer/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'sales')
def customer_add():
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form.get('phone')
        email = request.form.get('email')
        address = request.form.get('address')
        customer = Customer(name=name, phone=phone, email=email, address=address)
        db.session.add(customer)
        db.session.commit()
        flash('Клиент добавлен', 'success')
        return redirect(url_for('sales.customers_list'))
    return render_template('sales/customer_form.html')

@sales_bp.route('/customer/<int:customer_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'sales')
def customer_edit(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    if request.method == 'POST':
        customer.name = request.form['name']
        customer.phone = request.form.get('phone')
        customer.email = request.form.get('email')
        customer.address = request.form.get('address')
        db.session.commit()
        flash('Клиент обновлён', 'success')
        return redirect(url_for('sales.customers_list'))
    return render_template('sales/customer_form.html', customer=customer)

# ==================== Заказы ====================
@sales_bp.route('/orders')
@login_required
@role_required('admin', 'manager', 'sales')
def orders_list():
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

        # Обрабатываем позиции
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')
        total_amount = Decimal(0)

        for i in range(len(product_ids)):
            if not product_ids[i] or not quantities[i]:
                continue
            product = Product.query.get(int(product_ids[i]))
            qty = Decimal(quantities[i])
            if product:
                # Проверяем наличие на всех складах
                total_available = sum(stock.available for stock in product.stocks)
                if total_available < qty:
                    flash(f'Недостаточно товара {product.name} (доступно {total_available})', 'danger')
                    db.session.rollback()
                    return redirect(url_for('sales.order_create'))

                # Берём цену из товара (можно потом доработать с учётом наценок)
                price = product.price or Decimal(0)
                total = qty * price
                item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
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
        flash('Заказ создан', 'success')
        return redirect(url_for('sales.order_detail', order_id=order.id))

    # GET: показать форму
    customers = Customer.query.all()
    products = Product.query.filter_by(is_active=True).all()
    return render_template('sales/order_form.html', customers=customers, products=products)

@sales_bp.route('/order/<int:order_id>')
@login_required
@role_required('admin', 'manager', 'sales')
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('sales/order_detail.html', order=order)

@sales_bp.route('/order/<int:order_id>/status', methods=['POST'])
@login_required
@role_required('admin', 'manager', 'sales')
def order_change_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    if new_status not in ['new', 'processing', 'completed', 'cancelled']:
        flash('Некорректный статус', 'danger')
        return redirect(url_for('sales.order_detail', order_id=order.id))

    old_status = order.status

    # Логика резервирования / списания
    if new_status == 'processing' and old_status != 'processing':
        # Резервируем товары
        for item in order.items:
            product = item.product
            qty = item.quantity
            # Резервируем со всех складов по очереди (упрощённо)
            to_reserve = qty
            stocks = Stock.query.filter_by(product_id=product.id).order_by(Stock.quantity.desc()).all()
            for stock in stocks:
                if to_reserve <= 0:
                    break
                available = stock.quantity - stock.reserved
                if available > 0:
                    reserve_qty = min(available, to_reserve)
                    stock.reserved += reserve_qty
                    to_reserve -= reserve_qty
            if to_reserve > 0:
                flash(f'Не удалось зарезервировать {item.quantity} товара {product.name}', 'danger')
                db.session.rollback()
                return redirect(url_for('sales.order_detail', order_id=order.id))

    elif new_status == 'completed' and old_status != 'completed':
        # Списываем товары (уменьшаем quantity и снимаем резерв)
        for item in order.items:
            product = item.product
            qty = item.quantity
            to_remove = qty
            stocks = Stock.query.filter_by(product_id=product.id).order_by(Stock.quantity.desc()).all()
            for stock in stocks:
                if to_remove <= 0:
                    break
                remove_qty = min(stock.quantity, to_remove)
                stock.quantity -= remove_qty
                if stock.reserved >= remove_qty:
                    stock.reserved -= remove_qty
                else:
                    stock.reserved = 0
                to_remove -= remove_qty
            if to_remove > 0:
                flash(f'Ошибка списания товара {product.name}', 'danger')
                db.session.rollback()
                return redirect(url_for('sales.order_detail', order_id=order.id))

    elif new_status == 'cancelled' and old_status == 'processing':
        # Снимаем резерв
        for item in order.items:
            product = item.product
            qty = item.quantity
            to_unreserve = qty
            stocks = Stock.query.filter_by(product_id=product.id).all()
            for stock in stocks:
                if to_unreserve <= 0:
                    break
                unreserve_qty = min(stock.reserved, to_unreserve)
                stock.reserved -= unreserve_qty
                to_unreserve -= unreserve_qty

    order.status = new_status
    db.session.commit()
    flash(f'Статус заказа изменён на {new_status}', 'success')
    return redirect(url_for('sales.order_detail', order_id=order.id))