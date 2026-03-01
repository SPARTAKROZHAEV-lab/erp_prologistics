from flask import Blueprint, render_template, request, Response
from flask_login import login_required
from app.decorators import role_required
from app.models import Order, Transaction, Product, OrderItem, Category, Stock, Warehouse, Customer, User
from app.extensions import db
from sqlalchemy import func, desc, extract, and_
from datetime import datetime, timedelta
import csv
import io
import calendar

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

# ---- Вспомогательные функции ----
def get_date_range(default_days=90):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=default_days)
    return start_date, end_date

def parse_date_range(request):
    days = request.args.get('days', 90, type=int)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
    else:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
    return start_date, end_date

def generate_csv(rows, headers, filename):
    """Генерация CSV с правильной кодировкой для Excel (UTF-8 BOM, разделитель ;)"""
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    response = Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )
    return response

# ---- Дашборд ----
@analytics_bp.route('/')
@login_required
@role_required('admin', 'manager', 'accountant')
def dashboard():
    start_date, end_date = get_date_range(30)

    revenue = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.type == 'income',
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
        Transaction.status == 'completed'
    ).scalar() or 0

    expenses = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.type == 'expense',
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
        Transaction.status == 'completed'
    ).scalar() or 0

    orders_count = Order.query.filter(
        Order.order_date >= start_date,
        Order.order_date <= end_date,
        Order.status == 'completed'
    ).count()

    avg_check = revenue / orders_count if orders_count > 0 else 0
    profit = revenue - expenses

    daily_sales = db.session.query(
        func.date(Transaction.transaction_date).label('date'),
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.type == 'income',
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
        Transaction.status == 'completed'
    ).group_by(func.date(Transaction.transaction_date)).all()

    sales_dict = {row.date: row.total for row in daily_sales}
    dates = [(start_date + timedelta(days=i)).date() for i in range(31)]
    sales_data = [float(sales_dict.get(d, 0)) for d in dates]
    dates_labels = [d.strftime('%d.%m') for d in dates]

    top_products = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity * OrderItem.price).label('revenue')
    ).join(OrderItem, Product.id == OrderItem.product_id)\
     .join(Order, Order.id == OrderItem.order_id)\
     .filter(Order.status == 'completed')\
     .group_by(Product.id, Product.name)\
     .order_by(desc(func.sum(OrderItem.quantity * OrderItem.price)))\
     .limit(5).all()

    top_products_names = [p.name for p in top_products]
    top_products_values = [float(p.revenue) for p in top_products]

    return render_template('analytics/dashboard.html',
                           revenue=revenue,
                           expenses=expenses,
                           profit=profit,
                           orders_count=orders_count,
                           avg_check=avg_check,
                           dates_labels=dates_labels,
                           sales_data=sales_data,
                           top_products_names=top_products_names,
                           top_products_values=top_products_values)

# ---- 1. Продажи по дням ----
@analytics_bp.route('/sales_dynamics')
@login_required
@role_required('admin', 'manager', 'accountant')
def sales_dynamics():
    start_date, end_date = parse_date_range(request)
    
    daily = db.session.query(
        func.date(Transaction.transaction_date).label('date'),
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.type == 'income',
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
        Transaction.status == 'completed'
    ).group_by(func.date(Transaction.transaction_date)).order_by('date').all()

    dates = [d.date.strftime('%Y-%m-%d') for d in daily]
    totals = [float(d.total) for d in daily]
    total_revenue = sum(totals)

    return render_template('analytics/sales_dynamics.html',
                           dates=dates,
                           totals=totals,
                           total_revenue=total_revenue,
                           start_date=start_date.strftime('%Y-%m-%d'),
                           end_date=end_date.strftime('%Y-%m-%d'),
                           days=(end_date - start_date).days)

@analytics_bp.route('/sales_dynamics/export/csv')
@login_required
@role_required('admin', 'manager', 'accountant')
def sales_dynamics_csv():
    start_date, end_date = parse_date_range(request)
    daily = db.session.query(
        func.date(Transaction.transaction_date).label('date'),
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.type == 'income',
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
        Transaction.status == 'completed'
    ).group_by(func.date(Transaction.transaction_date)).order_by('date').all()

    rows = [(d.date.strftime('%Y-%m-%d'), float(d.total)) for d in daily]
    return generate_csv(rows, ['Дата', 'Выручка'], 'sales_dynamics.csv')

# ---- 2. Топ товаров ----
@analytics_bp.route('/top_products')
@login_required
@role_required('admin', 'manager', 'accountant')
def top_products():
    start_date, end_date = parse_date_range(request)
    
    top_by_revenue = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity * OrderItem.price).label('revenue'),
        func.sum(OrderItem.quantity).label('quantity')
    ).join(OrderItem, Product.id == OrderItem.product_id)\
     .join(Order, Order.id == OrderItem.order_id)\
     .filter(Order.status == 'completed',
             Order.order_date >= start_date,
             Order.order_date <= end_date)\
     .group_by(Product.id, Product.name)\
     .order_by(desc(func.sum(OrderItem.quantity * OrderItem.price)))\
     .limit(20).all()

    top5_names = [p.name[:20] + '...' if len(p.name) > 20 else p.name for p in top_by_revenue[:5]]
    top5_values = [float(p.revenue) for p in top_by_revenue[:5]]

    products_data = []
    for p in top_by_revenue:
        products_data.append({
            'name': p.name,
            'revenue': float(p.revenue),
            'quantity': p.quantity
        })

    return render_template('analytics/top_products.html',
                           top5_names=top5_names,
                           top5_values=top5_values,
                           products=products_data)

@analytics_bp.route('/top_products/export/csv')
@login_required
@role_required('admin', 'manager', 'accountant')
def top_products_csv():
    start_date, end_date = parse_date_range(request)
    products = db.session.query(
        Product.name,
        func.sum(OrderItem.quantity).label('quantity'),
        func.sum(OrderItem.quantity * OrderItem.price).label('revenue')
    ).join(OrderItem, Product.id == OrderItem.product_id)\
     .join(Order, Order.id == OrderItem.order_id)\
     .filter(Order.status == 'completed',
             Order.order_date >= start_date,
             Order.order_date <= end_date)\
     .group_by(Product.id, Product.name)\
     .order_by(desc(func.sum(OrderItem.quantity * OrderItem.price))).all()

    rows = [(p.name, p.quantity, float(p.revenue)) for p in products]
    return generate_csv(rows, ['Товар', 'Количество', 'Выручка'], 'top_products.csv')

# ---- 3. ABC-анализ ----
@analytics_bp.route('/abc_analysis')
@login_required
@role_required('admin', 'manager', 'accountant')
def abc_analysis():
    start_date, end_date = parse_date_range(request)
    
    products_rev = db.session.query(
        Product.id,
        Product.name,
        func.sum(OrderItem.quantity * OrderItem.price).label('revenue')
    ).join(OrderItem, Product.id == OrderItem.product_id)\
     .join(Order, Order.id == OrderItem.order_id)\
     .filter(Order.status == 'completed',
             Order.order_date >= start_date,
             Order.order_date <= end_date)\
     .group_by(Product.id, Product.name)\
     .order_by(desc(func.sum(OrderItem.quantity * OrderItem.price))).all()

    total_revenue = sum(p.revenue for p in products_rev)
    if total_revenue == 0:
        return render_template('analytics/abc_analysis.html', categories={}, total_revenue=0)

    categories = {'A': [], 'B': [], 'C': []}
    cumulative = 0
    for p in products_rev:
        share = p.revenue / total_revenue
        cumulative += share
        if cumulative <= 0.8:
            group = 'A'
        elif cumulative <= 0.95:
            group = 'B'
        else:
            group = 'C'
        categories[group].append({
            'name': p.name,
            'revenue': float(p.revenue),
            'share': float(share * 100)
        })

    return render_template('analytics/abc_analysis.html',
                           categories=categories,
                           total_revenue=float(total_revenue))

@analytics_bp.route('/abc_analysis/export/csv')
@login_required
@role_required('admin', 'manager', 'accountant')
def abc_analysis_csv():
    start_date, end_date = parse_date_range(request)
    products = db.session.query(
        Product.id,
        Product.name,
        func.sum(OrderItem.quantity * OrderItem.price).label('revenue')
    ).join(OrderItem, Product.id == OrderItem.product_id)\
     .join(Order, Order.id == OrderItem.order_id)\
     .filter(Order.status == 'completed',
             Order.order_date >= start_date,
             Order.order_date <= end_date)\
     .group_by(Product.id, Product.name)\
     .order_by(desc(func.sum(OrderItem.quantity * OrderItem.price))).all()

    total_revenue = sum(p.revenue for p in products)
    rows = []
    cumulative = 0
    for p in products:
        share = p.revenue / total_revenue if total_revenue else 0
        cumulative += share
        if cumulative <= 0.8:
            group = 'A'
        elif cumulative <= 0.95:
            group = 'B'
        else:
            group = 'C'
        rows.append([group, p.name, float(p.revenue), f"{share*100:.1f}%"])
    
    headers = ['Группа', 'Товар', 'Выручка', 'Доля']
    return generate_csv(rows, headers, 'abc_analysis.csv')

# ---- 4. Оборачиваемость складов ----
@analytics_bp.route('/warehouse_turnover')
@login_required
@role_required('admin', 'manager', 'accountant')
def warehouse_turnover():
    warehouses = Warehouse.query.all()
    data = []
    for wh in warehouses:
        stocks = Stock.query.filter_by(warehouse_id=wh.id).all()
        stock_value = sum(s.quantity * (s.product.purchase_price or 0) for s in stocks if s.product)

        sales_qty = db.session.query(func.sum(OrderItem.quantity)).join(Order).filter(
            OrderItem.warehouse_id == wh.id,
            Order.status == 'completed',
            Order.order_date >= datetime.now() - timedelta(days=30)
        ).scalar() or 0

        sales_amount = db.session.query(func.sum(OrderItem.quantity * OrderItem.price)).join(Order).filter(
            OrderItem.warehouse_id == wh.id,
            Order.status == 'completed',
            Order.order_date >= datetime.now() - timedelta(days=30)
        ).scalar() or 0

        turnover_ratio = sales_amount / stock_value if stock_value else 0

        data.append({
            'warehouse': wh.name,
            'stock_value': float(stock_value),
            'sales_qty': int(sales_qty),
            'sales_amount': float(sales_amount),
            'turnover_ratio': round(turnover_ratio, 2)
        })

    return render_template('analytics/warehouse_turnover.html', data=data)

@analytics_bp.route('/warehouse_turnover/export/csv')
@login_required
@role_required('admin', 'manager', 'accountant')
def warehouse_turnover_csv():
    warehouses = Warehouse.query.all()
    rows = []
    for wh in warehouses:
        stocks = Stock.query.filter_by(warehouse_id=wh.id).all()
        stock_value = sum(s.quantity * (s.product.purchase_price or 0) for s in stocks if s.product)
        sales_qty = db.session.query(func.sum(OrderItem.quantity)).join(Order).filter(
            OrderItem.warehouse_id == wh.id,
            Order.status == 'completed',
            Order.order_date >= datetime.now() - timedelta(days=30)
        ).scalar() or 0
        sales_amount = db.session.query(func.sum(OrderItem.quantity * OrderItem.price)).join(Order).filter(
            OrderItem.warehouse_id == wh.id,
            Order.status == 'completed',
            Order.order_date >= datetime.now() - timedelta(days=30)
        ).scalar() or 0
        turnover = sales_amount / stock_value if stock_value else 0
        rows.append([wh.name, float(stock_value), sales_qty, float(sales_amount), round(turnover, 2)])
    return generate_csv(rows, ['Склад', 'Стоимость остатков', 'Продажи (шт)', 'Продажи (сумма)', 'Оборачиваемость'], 'warehouse_turnover.csv')

# ---- 5. Динамика прибыли ----
@analytics_bp.route('/profit_dynamics')
@login_required
@role_required('admin', 'manager', 'accountant')
def profit_dynamics():
    months = 12
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30*months)

    monthly = db.session.query(
        func.date_trunc('month', Transaction.transaction_date).label('month'),
        Transaction.type,
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
        Transaction.status == 'completed'
    ).group_by('month', Transaction.type).order_by('month').all()

    month_dict = {}
    for row in monthly:
        month_str = row.month.strftime('%Y-%m')
        if month_str not in month_dict:
            month_dict[month_str] = {'income': 0, 'expense': 0}
        month_dict[month_str][row.type] = float(row.total)

    months_labels = sorted(month_dict.keys())
    income_data = [month_dict[m]['income'] for m in months_labels]
    expense_data = [month_dict[m]['expense'] for m in months_labels]
    profit_data = [income_data[i] - expense_data[i] for i in range(len(income_data))]

    return render_template('analytics/profit_dynamics.html',
                           months_labels=months_labels,
                           income_data=income_data,
                           expense_data=expense_data,
                           profit_data=profit_data)

@analytics_bp.route('/profit_dynamics/export/csv')
@login_required
@role_required('admin', 'manager', 'accountant')
def profit_dynamics_csv():
    months = 12
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30*months)
    monthly = db.session.query(
        func.date_trunc('month', Transaction.transaction_date).label('month'),
        Transaction.type,
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
        Transaction.status == 'completed'
    ).group_by('month', Transaction.type).order_by('month').all()

    month_dict = {}
    for row in monthly:
        month_str = row.month.strftime('%Y-%m')
        if month_str not in month_dict:
            month_dict[month_str] = {'income': 0, 'expense': 0}
        month_dict[month_str][row.type] = float(row.total)

    rows = []
    for month in sorted(month_dict.keys()):
        rows.append([month, month_dict[month]['income'], month_dict[month]['expense'], month_dict[month]['income'] - month_dict[month]['expense']])
    return generate_csv(rows, ['Месяц', 'Доходы', 'Расходы', 'Прибыль'], 'profit_dynamics.csv')

# ---- 6. Продажи по категориям ----
@analytics_bp.route('/category_sales')
@login_required
@role_required('admin', 'manager', 'accountant')
def category_sales():
    start_date, end_date = parse_date_range(request)
    
    category_data = db.session.query(
        Category.name,
        func.sum(OrderItem.quantity * OrderItem.price).label('revenue'),
        func.sum(OrderItem.quantity).label('quantity')
    ).join(Product, Product.category_id == Category.id)\
     .join(OrderItem, OrderItem.product_id == Product.id)\
     .join(Order, Order.id == OrderItem.order_id)\
     .filter(Order.status == 'completed',
             Order.order_date >= start_date,
             Order.order_date <= end_date)\
     .group_by(Category.id, Category.name).all()

    categories = [c.name for c in category_data]
    revenues = [float(c.revenue) for c in category_data]
    quantities = [c.quantity for c in category_data]

    return render_template('analytics/category_sales.html',
                           categories=categories,
                           revenues=revenues,
                           quantities=quantities)

@analytics_bp.route('/category_sales/export/csv')
@login_required
@role_required('admin', 'manager', 'accountant')
def category_sales_csv():
    start_date, end_date = parse_date_range(request)
    data = db.session.query(
        Category.name,
        func.sum(OrderItem.quantity * OrderItem.price).label('revenue'),
        func.sum(OrderItem.quantity).label('quantity')
    ).join(Product, Product.category_id == Category.id)\
     .join(OrderItem, OrderItem.product_id == Product.id)\
     .join(Order, Order.id == OrderItem.order_id)\
     .filter(Order.status == 'completed',
             Order.order_date >= start_date,
             Order.order_date <= end_date)\
     .group_by(Category.id, Category.name).all()

    rows = [(c.name, c.quantity, float(c.revenue)) for c in data]
    return generate_csv(rows, ['Категория', 'Количество', 'Выручка'], 'category_sales.csv')

# ---- 7. Анализ клиентов ----
@analytics_bp.route('/customer_analysis')
@login_required
@role_required('admin', 'manager', 'accountant')
def customer_analysis():
    start_date, end_date = parse_date_range(request)
    
    customers = db.session.query(
        Customer.name,
        func.count(Order.id).label('orders_count'),
        func.sum(Order.total_amount).label('total_spent')
    ).join(Order, Order.customer_id == Customer.id)\
     .filter(Order.status == 'completed',
             Order.order_date >= start_date,
             Order.order_date <= end_date)\
     .group_by(Customer.id, Customer.name)\
     .order_by(desc(func.sum(Order.total_amount))).limit(20).all()

    data = [{'name': c.name, 'orders': c.orders_count, 'spent': float(c.total_spent)} for c in customers]
    return render_template('analytics/customer_analysis.html', customers=data)

@analytics_bp.route('/customer_analysis/export/csv')
@login_required
@role_required('admin', 'manager', 'accountant')
def customer_analysis_csv():
    start_date, end_date = parse_date_range(request)
    customers = db.session.query(
        Customer.name,
        func.count(Order.id).label('orders_count'),
        func.sum(Order.total_amount).label('total_spent')
    ).join(Order, Order.customer_id == Customer.id)\
     .filter(Order.status == 'completed',
             Order.order_date >= start_date,
             Order.order_date <= end_date)\
     .group_by(Customer.id, Customer.name)\
     .order_by(desc(func.sum(Order.total_amount))).all()

    rows = [(c.name, c.orders_count, float(c.total_spent)) for c in customers]
    return generate_csv(rows, ['Клиент', 'Заказов', 'Сумма'], 'customer_analysis.csv')

# ---- 8. Эффективность сотрудников ----
@analytics_bp.route('/employee_efficiency')
@login_required
@role_required('admin', 'manager')
def employee_efficiency():
    start_date, end_date = parse_date_range(request)
    
    employees_data = db.session.query(
        User.username,
        func.count(Order.id).label('orders_created'),
        func.sum(Order.total_amount).label('total_amount')
    ).join(Order, Order.created_by == User.id)\
     .filter(Order.status == 'completed',
             Order.order_date >= start_date,
             Order.order_date <= end_date)\
     .group_by(User.id, User.username).all()

    data = [{'name': e.username, 'orders': e.orders_created, 'total': float(e.total_amount or 0)} for e in employees_data]
    return render_template('analytics/employee_efficiency.html', employees=data)

@analytics_bp.route('/employee_efficiency/export/csv')
@login_required
@role_required('admin', 'manager')
def employee_efficiency_csv():
    start_date, end_date = parse_date_range(request)
    data = db.session.query(
        User.username,
        func.count(Order.id).label('orders_created'),
        func.sum(Order.total_amount).label('total_amount')
    ).join(Order, Order.created_by == User.id)\
     .filter(Order.status == 'completed',
             Order.order_date >= start_date,
             Order.order_date <= end_date)\
     .group_by(User.id, User.username).all()

    rows = [(e.username, e.orders_created, float(e.total_amount or 0)) for e in data]
    return generate_csv(rows, ['Сотрудник', 'Заказов', 'Сумма'], 'employee_efficiency.csv')

# ---- 9. Конверсия заказов ----
@analytics_bp.route('/order_conversion')
@login_required
@role_required('admin', 'manager')
def order_conversion():
    statuses = db.session.query(
        Order.status,
        func.count(Order.id).label('count')
    ).group_by(Order.status).all()

    labels = [s.status for s in statuses]
    values = [s.count for s in statuses]

    return render_template('analytics/order_conversion.html',
                           labels=labels,
                           values=values)

@analytics_bp.route('/order_conversion/export/csv')
@login_required
@role_required('admin', 'manager')
def order_conversion_csv():
    statuses = db.session.query(
        Order.status,
        func.count(Order.id).label('count')
    ).group_by(Order.status).all()

    rows = [(s.status, s.count) for s in statuses]
    return generate_csv(rows, ['Статус', 'Количество'], 'order_conversion.csv')

# ---- 10. Сезонность ----
@analytics_bp.route('/seasonality')
@login_required
@role_required('admin', 'manager', 'accountant')
def seasonality():
    monthly_sales = db.session.query(
        extract('month', Order.order_date).label('month'),
        func.sum(Order.total_amount).label('total')
    ).filter(Order.status == 'completed')\
     .group_by('month').order_by('month').all()

    month_names = [calendar.month_name[int(m[0])] for m in monthly_sales]
    sales_by_month = [float(m[1]) for m in monthly_sales]

    return render_template('analytics/seasonality.html',
                           months=month_names,
                           sales=sales_by_month)

@analytics_bp.route('/seasonality/export/csv')
@login_required
@role_required('admin', 'manager', 'accountant')
def seasonality_csv():
    monthly_sales = db.session.query(
        extract('month', Order.order_date).label('month'),
        func.sum(Order.total_amount).label('total')
    ).filter(Order.status == 'completed')\
     .group_by('month').order_by('month').all()

    rows = [(calendar.month_name[int(m[0])], float(m[1])) for m in monthly_sales]
    return generate_csv(rows, ['Месяц', 'Продажи'], 'seasonality.csv')

# ---- 11. Прогнозирование ----
@analytics_bp.route('/forecast')
@login_required
@role_required('admin', 'manager', 'accountant')
def forecast():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    daily = db.session.query(
        func.date(Transaction.transaction_date).label('date'),
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.type == 'income',
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
        Transaction.status == 'completed'
    ).group_by(func.date(Transaction.transaction_date)).order_by('date').all()

    if len(daily) < 7:
        return render_template('analytics/forecast.html', error="Недостаточно данных для прогноза")

    last_7_avg = sum(d.total for d in daily[-7:]) / 7
    forecast_next_30 = last_7_avg * 30

    hist_dates = [d.date.strftime('%Y-%m-%d') for d in daily]
    hist_values = [float(d.total) for d in daily]

    return render_template('analytics/forecast.html',
                           hist_dates=hist_dates,
                           hist_values=hist_values,
                           forecast=float(forecast_next_30),
                           error=None)

# ---- 12. Дебиторская задолженность ----
@analytics_bp.route('/receivables_payables')
@login_required
@role_required('admin', 'manager', 'accountant')
def receivables_payables():
    from app.models import Invoice
    receivables = db.session.query(
        Customer.name,
        func.sum(Invoice.total_amount).label('debt')
    ).join(Invoice, Invoice.customer_id == Customer.id)\
     .filter(Invoice.status == 'sent')\
     .group_by(Customer.id, Customer.name).all()

    receivables_list = [{'name': r.name, 'debt': float(r.debt)} for r in receivables]

    return render_template('analytics/receivables_payables.html',
                           receivables=receivables_list)

@analytics_bp.route('/receivables_payables/export/csv')
@login_required
@role_required('admin', 'manager', 'accountant')
def receivables_payables_csv():
    from app.models import Invoice
    receivables = db.session.query(
        Customer.name,
        func.sum(Invoice.total_amount).label('debt')
    ).join(Invoice, Invoice.customer_id == Customer.id)\
     .filter(Invoice.status == 'sent')\
     .group_by(Customer.id, Customer.name).all()

    rows = [(r.name, float(r.debt)) for r in receivables]
    return generate_csv(rows, ['Клиент', 'Долг'], 'receivables.csv')

# ---- 13. Рентабельность по категориям ----
@analytics_bp.route('/profit_margin_by_category')
@login_required
@role_required('admin', 'manager', 'accountant')
def profit_margin_by_category():
    start_date, end_date = parse_date_range(request)
    
    data = db.session.query(
        Category.name,
        func.sum(OrderItem.quantity * OrderItem.price).label('revenue'),
        func.sum(OrderItem.quantity * Product.purchase_price).label('cost')
    ).join(Product, Product.category_id == Category.id)\
     .join(OrderItem, OrderItem.product_id == Product.id)\
     .join(Order, Order.id == OrderItem.order_id)\
     .filter(Order.status == 'completed',
             Order.order_date >= start_date,
             Order.order_date <= end_date)\
     .group_by(Category.id, Category.name).all()

    result = []
    for d in data:
        revenue = float(d.revenue) if d.revenue else 0
        cost = float(d.cost) if d.cost else 0
        profit = revenue - cost
        margin = (profit / revenue * 100) if revenue else 0
        result.append({
            'category': d.name,
            'revenue': revenue,
            'cost': cost,
            'profit': profit,
            'margin': round(margin, 2)
        })

    return render_template('analytics/profit_margin_by_category.html', data=result)

@analytics_bp.route('/forecast/export/csv')
@login_required
@role_required('admin', 'manager', 'accountant')
def forecast_csv():
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    daily = db.session.query(
        func.date(Transaction.transaction_date).label('date'),
        func.sum(Transaction.amount).label('total')
    ).filter(
        Transaction.type == 'income',
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
        Transaction.status == 'completed'
    ).group_by(func.date(Transaction.transaction_date)).order_by('date').all()
    rows = [(d.date.strftime('%Y-%m-%d'), float(d.total)) for d in daily]
    return generate_csv(rows, ['Дата', 'Выручка'], 'forecast_history.csv')


@analytics_bp.route('/profit_margin_by_category/export/csv')
@login_required
@role_required('admin', 'manager', 'accountant')
def profit_margin_by_category_csv():
    start_date, end_date = parse_date_range(request)
    data = db.session.query(
        Category.name,
        func.sum(OrderItem.quantity * OrderItem.price).label('revenue'),
        func.sum(OrderItem.quantity * Product.purchase_price).label('cost')
    ).join(Product, Product.category_id == Category.id)\
     .join(OrderItem, OrderItem.product_id == Product.id)\
     .join(Order, Order.id == OrderItem.order_id)\
     .filter(Order.status == 'completed',
             Order.order_date >= start_date,
             Order.order_date <= end_date)\
     .group_by(Category.id, Category.name).all()

    rows = []
    for d in data:
        revenue = float(d.revenue) if d.revenue else 0
        cost = float(d.cost) if d.cost else 0
        profit = revenue - cost
        margin = (profit / revenue * 100) if revenue else 0
        rows.append([d.name, revenue, cost, profit, round(margin, 2)])
    return generate_csv(rows, ['Категория', 'Выручка', 'Себестоимость', 'Прибыль', 'Маржа %'], 'profit_margin.csv')