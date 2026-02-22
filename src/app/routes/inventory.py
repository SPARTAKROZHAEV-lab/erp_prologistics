# app/routes/inventory.py
from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required
from app.decorators import role_required
from app.models import Category, Product, Warehouse, Stock
from app.extensions import db
from flask_login import current_user
from app.models.stock_movement import StockMovement
from app.models.stock_log import StockLog
from decimal import Decimal

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

# ==================== Категории ====================
@inventory_bp.route('/categories')
@login_required
@role_required('admin', 'manager', 'storekeeper')
def categories_list():
    """Список категорий товаров"""
    categories = Category.query.all()
    return render_template('inventory/categories_list.html', categories=categories)

@inventory_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'storekeeper')
def category_add():
    """Добавление категории"""
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description')
        parent_id = request.form.get('parent_id') or None
        if parent_id:
            parent_id = int(parent_id)
        category = Category(name=name, description=description, parent_id=parent_id)
        db.session.add(category)
        db.session.commit()
        flash('Категория добавлена', 'success')
        return redirect(url_for('inventory.categories_list'))
    categories = Category.query.all()
    return render_template('inventory/category_form.html', categories=categories)

@inventory_bp.route('/categories/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'storekeeper')
def category_edit(category_id):
    """Редактирование категории"""
    category = Category.query.get_or_404(category_id)
    if request.method == 'POST':
        category.name = request.form['name']
        category.description = request.form.get('description')
        parent_id = request.form.get('parent_id') or None
        if parent_id:
            parent_id = int(parent_id)
        category.parent_id = parent_id
        db.session.commit()
        flash('Категория обновлена', 'success')
        return redirect(url_for('inventory.categories_list'))
    categories = Category.query.all()
    return render_template('inventory/category_form.html', category=category, categories=categories)

@inventory_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def category_delete(category_id):
    """Удаление категории (если нет товаров)"""
    category = Category.query.get_or_404(category_id)
    if category.products.count() > 0:
        flash('Нельзя удалить категорию, в которой есть товары', 'danger')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('Категория удалена', 'success')
    return redirect(url_for('inventory.categories_list'))

# ==================== Товары ====================
@inventory_bp.route('/products')
@login_required
@role_required('admin', 'manager', 'storekeeper')
def products_list():
    """Список товаров"""
    products = Product.query.all()
    return render_template('inventory/products_list.html', products=products)

@inventory_bp.route('/products/<int:product_id>')
@login_required
@role_required('admin', 'manager', 'storekeeper')
def product_detail(product_id):
    """Детальная страница товара"""
    product = Product.query.get_or_404(product_id)
    return render_template('inventory/product_detail.html', product=product)

@inventory_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'storekeeper')
def product_add():
    """Добавление товара"""
    if request.method == 'POST':
        sku = request.form['sku']
        name = request.form['name']
        description = request.form.get('description')
        price = request.form.get('price')
        cost = request.form.get('cost')
        category_id = request.form.get('category_id') or None
        if category_id:
            category_id = int(category_id)
        barcode = request.form.get('barcode')
        unit = request.form.get('unit', 'шт')
        
        product = Product(
            sku=sku,
            name=name,
            description=description,
            price=float(price) if price else None,
            cost=float(cost) if cost else None,
            category_id=category_id,
            barcode=barcode,
            unit=unit
        )
        db.session.add(product)
        db.session.flush()  # чтобы получить id

        # Создаём остатки на всех активных складах
        warehouses = Warehouse.query.filter_by(is_active=True).all()
        for wh in warehouses:
            stock = Stock(product_id=product.id, warehouse_id=wh.id, quantity=0)
            db.session.add(stock)

        db.session.commit()
        flash('Товар добавлен', 'success')
        return redirect(url_for('inventory.products_list'))

    categories = Category.query.all()
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    return render_template('inventory/product_form.html', categories=categories, warehouses=warehouses)

@inventory_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'storekeeper')
def product_edit(product_id):
    """Редактирование товара"""
    product = Product.query.get_or_404(product_id)
    if request.method == 'POST':
        product.sku = request.form['sku']
        product.name = request.form['name']
        product.description = request.form.get('description')
        product.price = float(request.form['price']) if request.form.get('price') else None
        product.cost = float(request.form['cost']) if request.form.get('cost') else None
        category_id = request.form.get('category_id') or None
        if category_id:
            category_id = int(category_id)
        product.category_id = category_id
        product.barcode = request.form.get('barcode')
        product.unit = request.form.get('unit', 'шт')
        product.is_active = 'is_active' in request.form

        db.session.commit()
        flash('Товар обновлён', 'success')
        return redirect(url_for('inventory.product_detail', product_id=product.id))

    categories = Category.query.all()
    return render_template('inventory/product_form.html', product=product, categories=categories)

@inventory_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def product_delete(product_id):
    """Удаление товара"""
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Товар удалён', 'success')
    return redirect(url_for('inventory.products_list'))

# ==================== Склады ====================
@inventory_bp.route('/warehouses')
@login_required
@role_required('admin', 'manager', 'storekeeper')
def warehouses_list():
    """Список складов"""
    warehouses = Warehouse.query.all()
    return render_template('inventory/warehouses_list.html', warehouses=warehouses)

@inventory_bp.route('/warehouses/add', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def warehouse_add():
    """Добавление склада"""
    if request.method == 'POST':
        name = request.form['name']
        location = request.form.get('location')
        warehouse = Warehouse(name=name, location=location)
        db.session.add(warehouse)
        db.session.flush()  # получаем id

        # Создаём остатки для всех товаров на этом складе
        products = Product.query.all()
        for prod in products:
            stock = Stock(product_id=prod.id, warehouse_id=warehouse.id, quantity=0)
            db.session.add(stock)

        db.session.commit()
        flash('Склад добавлен', 'success')
        return redirect(url_for('inventory.warehouses_list'))
    return render_template('inventory/warehouse_form.html')

@inventory_bp.route('/warehouses/<int:warehouse_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def warehouse_edit(warehouse_id):
    """Редактирование склада"""
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    if request.method == 'POST':
        warehouse.name = request.form['name']
        warehouse.location = request.form.get('location')
        warehouse.is_active = 'is_active' in request.form
        db.session.commit()
        flash('Склад обновлён', 'success')
        return redirect(url_for('inventory.warehouses_list'))
    return render_template('inventory/warehouse_form.html', warehouse=warehouse)

@inventory_bp.route('/warehouses/<int:warehouse_id>/delete', methods=['POST'])
@login_required
@role_required('admin')
def warehouse_delete(warehouse_id):
    """Удаление склада (если нет остатков)"""
    warehouse = Warehouse.query.get_or_404(warehouse_id)
    if warehouse.stocks.filter(Stock.quantity > 0).first():
        flash('Нельзя удалить склад с ненулевыми остатками', 'danger')
    else:
        db.session.delete(warehouse)
        db.session.commit()
        flash('Склад удалён', 'success')
    return redirect(url_for('inventory.warehouses_list'))

# ==================== Остатки ====================
@inventory_bp.route('/stocks')
@login_required
@role_required('admin', 'manager', 'storekeeper')
def stocks_list():
    """Просмотр остатков с фильтрацией и пагинацией"""
    page = request.args.get('page', 1, type=int)
    per_page = 20  # записей на странице
    
    # Фильтры
    product_id = request.args.get('product_id', type=int)
    warehouse_id = request.args.get('warehouse_id', type=int)
    
    query = Stock.query
    
    if product_id:
        query = query.filter_by(product_id=product_id)
    if warehouse_id:
        query = query.filter_by(warehouse_id=warehouse_id)
    
    # Пагинация
    stocks_paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Для фильтров
    products = Product.query.filter_by(is_active=True).all()
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    
    return render_template('inventory/stocks_list.html',
                          stocks=stocks_paginated,
                          products=products,
                          warehouses=warehouses,
                          selected_product=product_id,
                          selected_warehouse=warehouse_id)

@inventory_bp.route('/movement/create', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager', 'storekeeper')
def movement_create():
    """Создание перемещения товара между складами"""
    if request.method == 'POST':
        product_id = int(request.form['product_id'])
        from_warehouse_id = request.form.get('from_warehouse_id')
        to_warehouse_id = int(request.form['to_warehouse_id'])
        quantity = Decimal(request.form['quantity'])
        comment = request.form.get('comment', '')
        
        if from_warehouse_id and int(from_warehouse_id) == to_warehouse_id:
            flash('Нельзя перемещать товар на тот же склад', 'danger')
            return redirect(url_for('inventory.movement_create'))
        
        if from_warehouse_id:
            from_stock = Stock.query.filter_by(product_id=product_id, warehouse_id=int(from_warehouse_id)).first()
            if not from_stock or from_stock.quantity < quantity:
                flash('Недостаточно товара на исходном складе', 'danger')
                return redirect(url_for('inventory.movement_create'))
        else:
            from_stock = None
        
        to_stock = Stock.query.filter_by(product_id=product_id, warehouse_id=to_warehouse_id).first()
        if not to_stock:
            to_stock = Stock(product_id=product_id, warehouse_id=to_warehouse_id, quantity=0)
            db.session.add(to_stock)
            db.session.flush()
        
        movement = StockMovement(
            product_id=product_id,
            from_warehouse_id=int(from_warehouse_id) if from_warehouse_id else None,
            to_warehouse_id=to_warehouse_id,
            quantity=quantity,
            movement_type='transfer' if from_warehouse_id else 'purchase',
            created_by=current_user.id,
            comment=comment
        )
        db.session.add(movement)
        db.session.flush()
        
        if from_stock:
            old_from = from_stock.quantity
            from_stock.quantity -= quantity
            log = StockLog(
                stock_id=from_stock.id,
                old_quantity=old_from,
                new_quantity=from_stock.quantity,
                change=-quantity,
                movement_id=movement.id,
                created_by=current_user.id
            )
            db.session.add(log)
        
        old_to = to_stock.quantity
        to_stock.quantity += quantity
        log_to = StockLog(
            stock_id=to_stock.id,
            old_quantity=old_to,
            new_quantity=to_stock.quantity,
            change=quantity,
            movement_id=movement.id,
            created_by=current_user.id
        )
        db.session.add(log_to)
        
        db.session.commit()
        flash('Перемещение выполнено', 'success')
        return redirect(url_for('inventory.stocks_list'))
    
    product_id = request.args.get('product_id', type=int)
    from_warehouse_id = request.args.get('from_warehouse_id', type=int)
    products = Product.query.filter_by(is_active=True).all()
    warehouses = Warehouse.query.filter_by(is_active=True).all()
    return render_template('inventory/movement_form.html',
                          products=products,
                          warehouses=warehouses,
                          selected_product=product_id,
                          selected_from_warehouse=from_warehouse_id)

@inventory_bp.route('/stock/<int:stock_id>/history')
@login_required
@role_required('admin', 'manager', 'storekeeper')
def stock_history(stock_id):
    """Просмотр истории изменений остатка"""
    stock = Stock.query.get_or_404(stock_id)
    logs = StockLog.query.filter_by(stock_id=stock_id).order_by(StockLog.created_at.desc()).all()
    return render_template('inventory/stock_history.html', stock=stock, logs=logs)

@inventory_bp.route('/stocks/adjust', methods=['POST'])
@login_required
@role_required('admin', 'storekeeper')
def stock_adjust():
    """Ручная корректировка остатка"""
    stock_id = request.form['stock_id']
    new_quantity = Decimal(request.form['quantity'])
    stock = Stock.query.get_or_404(stock_id)
    stock.quantity = new_quantity
    db.session.commit()
    flash('Остаток скорректирован', 'success')
    return redirect(url_for('inventory.stocks_list'))