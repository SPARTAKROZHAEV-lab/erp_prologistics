# app/routes/finance.py
# Маршруты для финансового модуля (счета, платежи, транзакции)

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Invoice, Payment, Transaction, Order, Customer
from datetime import datetime
from sqlalchemy import func
import random
import string
from app.models import TransactionCategory
from decimal import Decimal
from datetime import datetime, timedelta

finance_bp = Blueprint('finance', __name__, url_prefix='/finance')

def generate_invoice_number():
    """Генерация уникального номера счёта"""
    while True:
        number = 'INV-' + ''.join(random.choices(string.digits, k=8))
        if not Invoice.query.filter_by(number=number).first():
            return number

@finance_bp.route('/')
@login_required
def index():
    """Главная страница финансового раздела (список счетов)"""
    return redirect(url_for('finance.invoices'))

@finance_bp.route('/invoices')
@login_required
def invoices():
    """Список всех счетов"""
    invoices_list = Invoice.query.order_by(Invoice.issue_date.desc()).all()
    return render_template('finance/invoices.html', invoices=invoices_list)

@finance_bp.route('/invoice/<int:id>')
@login_required
def invoice_detail(id):
    """Детальная страница счёта"""
    invoice = Invoice.query.get_or_404(id)
    # Вычисляем общую сумму оплат по счёту
    total_paid = db.session.query(func.sum(Payment.amount)).filter(
        Payment.invoice_id == invoice.id,
        Payment.status == 'completed'
    ).scalar() or 0
    return render_template('finance/invoice_detail.html', invoice=invoice, total_paid=total_paid)


@finance_bp.route('/invoice/create', methods=['GET', 'POST'])
@login_required
def invoice_create():
    """Создание нового счёта (вручную или на основе заказа)"""
    if request.method == 'POST':
        # Получаем данные из формы
        number = request.form.get('number')
        customer_id = request.form.get('customer_id')
        issue_date_str = request.form.get('issue_date')
        due_date_str = request.form.get('due_date')
        total_amount = request.form.get('total_amount')
        description = request.form.get('description')
        order_id = request.form.get('order_id') or None

        # Преобразуем даты
        issue_date = datetime.strptime(issue_date_str, '%Y-%m-%d').date()
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date() if due_date_str else None

        # Создаём объект Invoice
        invoice = Invoice(
            number=number,
            customer_id=customer_id,
            issue_date=issue_date,
            due_date=due_date,
            total_amount=float(total_amount),
            description=description,
            order_id=order_id,
            created_by_id=current_user.id
        )
        db.session.add(invoice)
        db.session.commit()
        flash('Счёт успешно создан', 'success')
        return redirect(url_for('finance.invoice_detail', id=invoice.id))

    # GET: показать форму
    customers = Customer.query.filter_by(is_active=True).all()
    # Показываем все заказы, кроме отменённых (или все)
    orders = Order.query.filter(Order.status != 'cancelled').all()
    # ===== НОВЫЙ КОД: генерируем номер счёта заранее =====
    invoice_number = generate_invoice_number()
    # ====================================================
    return render_template('finance/invoice_form.html', 
                           customers=customers, 
                           orders=orders, 
                           now=datetime.now,
                           invoice_number=invoice_number)  # передаём номер в шаблон
@finance_bp.route('/invoice/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def invoice_edit(id):
    """Редактирование счёта (только черновики)"""
    # Пока заглушка, можно реализовать позже
    return "Редактирование счёта (в разработке)"
@finance_bp.route('/invoice/<int:id>/add_payment', methods=['GET', 'POST'])
@login_required
def add_payment(id):
    """Добавление платежа к счёту"""
    from decimal import Decimal  # добавим импорт, если его нет в начале

    invoice = Invoice.query.get_or_404(id)
    if request.method == 'POST':
        # Получаем данные и сразу преобразуем в Decimal
        amount = Decimal(str(request.form.get('amount', 0)))  # преобразуем строку в Decimal
        payment_date_str = request.form.get('payment_date')
        if payment_date_str:
            payment_date = datetime.strptime(payment_date_str, '%Y-%m-%dT%H:%M')
        else:
            payment_date = datetime.utcnow()
        method = request.form.get('method', 'cash')
        reference = request.form.get('reference', '')
        comment = request.form.get('comment', '')
        status = request.form.get('status', 'pending')

        # Создаём платёж
        payment = Payment(
            invoice_id=invoice.id,
            amount=amount,
            payment_date=payment_date,
            method=method,
            reference=reference,
            comment=comment,
            status=status,
            created_by_id=current_user.id
        )
        db.session.add(payment)
        db.session.flush()  # получаем id платежа

        # Если статус completed, создаём транзакцию
        if status == 'completed':
            transaction = Transaction(
                type='income',
                amount=amount,
                currency='RUB',
                transaction_date=payment_date,
                description=f'Оплата по счёту {invoice.number}',
                status='completed',
                order_id=invoice.order_id,
                customer_id=invoice.customer_id,
                created_by_id=current_user.id,
                comment=comment
            )
            db.session.add(transaction)
            db.session.flush()
            payment.transaction_id = transaction.id

            # Обновляем статус счёта, используя Decimal
            total_paid = db.session.query(func.sum(Payment.amount)).filter(
                Payment.invoice_id == invoice.id,
                Payment.status == 'completed'
            ).scalar() or Decimal(0)

            if total_paid + amount >= invoice.total_amount:
                invoice.status = 'paid'
            else:
                invoice.status = 'sent'  # частично оплачен

        db.session.commit()
        flash('Платёж добавлен', 'success')
        return redirect(url_for('finance.invoice_detail', id=invoice.id))

    # GET: показать форму
    return render_template('finance/add_payment.html', invoice=invoice, now=datetime.now)

@finance_bp.route('/payments')
@login_required
def payments():
    """Список всех платежей"""
    payments_list = Payment.query.order_by(Payment.payment_date.desc()).all()
    return render_template('finance/payments.html', payments=payments_list)

@finance_bp.route('/payment/<int:id>')
@login_required
def payment_detail(id):
    """Детали платежа"""
    payment = Payment.query.get_or_404(id)
    return render_template('finance/payment_detail.html', payment=payment)

# ==================== Категории транзакций ====================

@finance_bp.route('/categories')
@login_required
def categories_list():
    """Список категорий транзакций"""
    categories = TransactionCategory.query.order_by(TransactionCategory.type, TransactionCategory.name).all()
    return render_template('finance/categories_list.html', categories=categories)

@finance_bp.route('/category/add', methods=['GET', 'POST'])
@login_required
def category_add():
    """Добавление новой категории"""
    if request.method == 'POST':
        name = request.form.get('name')
        type_ = request.form.get('type')
        description = request.form.get('description')
        is_active = 'is_active' in request.form

        category = TransactionCategory(
            name=name,
            type=type_,
            description=description,
            is_active=is_active
        )
        db.session.add(category)
        db.session.commit()
        flash('Категория добавлена', 'success')
        return redirect(url_for('finance.categories_list'))

    return render_template('finance/category_form.html')

@finance_bp.route('/category/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def category_edit(id):
    """Редактирование категории"""
    category = TransactionCategory.query.get_or_404(id)
    if request.method == 'POST':
        category.name = request.form.get('name')
        category.type = request.form.get('type')
        category.description = request.form.get('description')
        category.is_active = 'is_active' in request.form
        db.session.commit()
        flash('Категория обновлена', 'success')
        return redirect(url_for('finance.categories_list'))

    return render_template('finance/category_form.html', category=category)

@finance_bp.route('/category/<int:id>/delete', methods=['POST'])
@login_required
def category_delete(id):
    """Удаление категории (если нет связанных транзакций)"""
    category = TransactionCategory.query.get_or_404(id)
    if category.transactions.count() > 0:
        flash('Нельзя удалить категорию, к которой привязаны транзакции', 'danger')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('Категория удалена', 'success')
    return redirect(url_for('finance.categories_list'))

@finance_bp.route('/transactions')
@login_required
def transactions():
    """Список всех финансовых транзакций"""
    transactions_list = Transaction.query.order_by(Transaction.created_at.desc()).all()
    return render_template('finance/transactions.html', transactions=transactions_list)

# ==================== Транзакции ====================

@finance_bp.route('/transactions')
@login_required
def transactions_list():
    """Список всех транзакций с фильтрацией"""
    # Фильтры из GET-параметров
    type_filter = request.args.get('type', '')
    category_id = request.args.get('category_id', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = Transaction.query

    if type_filter:
        query = query.filter_by(type=type_filter)
    if category_id and category_id.isdigit():
        query = query.filter_by(category_id=int(category_id))
    if start_date:
        query = query.filter(Transaction.transaction_date >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(Transaction.transaction_date <= datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1))

    transactions = query.order_by(Transaction.transaction_date.desc()).all()
    categories = TransactionCategory.query.filter_by(is_active=True).all()
    return render_template('finance/transactions_list.html', transactions=transactions, categories=categories,
                           type_filter=type_filter, cat_filter=category_id, start_date=start_date, end_date=end_date)

@finance_bp.route('/transaction/add', methods=['GET', 'POST'])
@login_required
def transaction_add():
    """Добавление произвольной транзакции (доход/расход)"""
    if request.method == 'POST':
        type_ = request.form.get('type')
        amount = Decimal(request.form.get('amount'))
        currency = request.form.get('currency', 'RUB')
        transaction_date_str = request.form.get('transaction_date')
        description = request.form.get('description')
        category_id = request.form.get('category_id') or None
        customer_id = request.form.get('customer_id') or None
        order_id = request.form.get('order_id') or None
        comment = request.form.get('comment')

        transaction_date = datetime.strptime(transaction_date_str, '%Y-%m-%d').date()

        transaction = Transaction(
            type=type_,
            amount=amount,
            currency=currency,
            transaction_date=transaction_date,
            description=description,
            category_id=category_id,
            customer_id=customer_id,
            order_id=order_id,
            created_by_id=current_user.id,
            comment=comment,
            status='completed'  # по умолчанию проведена
        )
        db.session.add(transaction)
        db.session.commit()
        flash('Транзакция добавлена', 'success')
        return redirect(url_for('finance.transactions_list'))

    categories = TransactionCategory.query.filter_by(is_active=True).all()
    customers = Customer.query.filter_by(is_active=True).all()
    orders = Order.query.filter(Order.status.in_(['processing', 'completed'])).all()
    return render_template('finance/transaction_form.html', categories=categories, customers=customers, orders=orders, now=datetime.now)

@finance_bp.route('/transaction/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def transaction_edit(id):
    """Редактирование транзакции"""
    transaction = Transaction.query.get_or_404(id)
    if request.method == 'POST':
        transaction.type = request.form.get('type')
        transaction.amount = Decimal(request.form.get('amount'))
        transaction.currency = request.form.get('currency')
        transaction.transaction_date = datetime.strptime(request.form.get('transaction_date'), '%Y-%m-%d').date()
        transaction.description = request.form.get('description')
        transaction.category_id = request.form.get('category_id') or None
        transaction.customer_id = request.form.get('customer_id') or None
        transaction.order_id = request.form.get('order_id') or None
        transaction.comment = request.form.get('comment')
        db.session.commit()
        flash('Транзакция обновлена', 'success')
        return redirect(url_for('finance.transactions_list'))

    categories = TransactionCategory.query.filter_by(is_active=True).all()
    customers = Customer.query.filter_by(is_active=True).all()
    orders = Order.query.filter(Order.status.in_(['processing', 'completed'])).all()
    return render_template('finance/transaction_form.html', transaction=transaction, categories=categories,
                           customers=customers, orders=orders, now=datetime.now)

@finance_bp.route('/transaction/<int:id>/delete', methods=['POST'])
@login_required
def transaction_delete(id):
    """Удаление транзакции"""
    transaction = Transaction.query.get_or_404(id)
    # Если транзакция связана с платежом, возможно, нужно разрешить удаление или запретить.
    # Пока просто удаляем (осторожно).
    db.session.delete(transaction)
    db.session.commit()
    flash('Транзакция удалена', 'success')
    return redirect(url_for('finance.transactions_list'))

# ==================== Финансовые отчёты ====================

@finance_bp.route('/reports')
@login_required
def reports_index():
    """Главная страница с отчётами (меню)"""
    return render_template('finance/reports_index.html')

@finance_bp.route('/reports/cash_flow')
@login_required
def report_cash_flow():
    """Отчёт о движении денежных средств"""
    period = request.args.get('period', 'month')  # day, week, month
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Если даты не заданы, по умолчанию последний месяц
    if not start_date or not end_date:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    # Выбираем транзакции за период
    transactions = Transaction.query.filter(
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
        Transaction.status == 'completed'
    ).all()

    # Группировка по дням/неделям/месяцам
    # Для простоты сделаем по дням
    from collections import defaultdict
    daily = defaultdict(lambda: {'income': 0, 'expense': 0})
    for t in transactions:
        key = t.transaction_date.isoformat()
        if t.type == 'income':
            daily[key]['income'] += float(t.amount)
        else:
            daily[key]['expense'] += float(t.amount)

    # Преобразуем в список для графика
    dates = sorted(daily.keys())
    income_data = [daily[d]['income'] for d in dates]
    expense_data = [daily[d]['expense'] for d in dates]
    balance_data = [income_data[i] - expense_data[i] for i in range(len(dates))]

    return render_template('finance/report_cash_flow.html',
                           start_date=start_date, end_date=end_date,
                           dates=dates, income_data=income_data,
                           expense_data=expense_data, balance_data=balance_data)

@finance_bp.route('/reports/profit_loss')
@login_required
def report_profit_loss():
    """Отчёт о прибылях и убытках (доходы минус расходы)"""
    # Используем аналогичную логику, но с группировкой по категориям или общей суммой
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    if not start_date or not end_date:
        end_date = datetime.now().date()
        start_date = end_date.replace(day=1)  # первый день месяца
    else:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    income_total = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.type == 'income',
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
        Transaction.status == 'completed'
    ).scalar() or 0

    expense_total = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.type == 'expense',
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date,
        Transaction.status == 'completed'
    ).scalar() or 0

    profit = income_total - expense_total

    # Доходы и расходы по категориям
    income_by_cat = db.session.query(
        TransactionCategory.name, func.sum(Transaction.amount)
    ).join(Transaction, Transaction.category_id == TransactionCategory.id)\
     .filter(Transaction.type == 'income',
             Transaction.transaction_date >= start_date,
             Transaction.transaction_date <= end_date,
             Transaction.status == 'completed')\
     .group_by(TransactionCategory.name).all()

    expense_by_cat = db.session.query(
        TransactionCategory.name, func.sum(Transaction.amount)
    ).join(Transaction, Transaction.category_id == TransactionCategory.id)\
     .filter(Transaction.type == 'expense',
             Transaction.transaction_date >= start_date,
             Transaction.transaction_date <= end_date,
             Transaction.status == 'completed')\
     .group_by(TransactionCategory.name).all()

    return render_template('finance/report_profit_loss.html',
                           start_date=start_date, end_date=end_date,
                           income_total=income_total, expense_total=expense_total,
                           profit=profit, income_by_cat=income_by_cat, expense_by_cat=expense_by_cat)

@finance_bp.route('/reports/debtors')
@login_required
def report_debtors():
    """Отчёт по дебиторской/кредиторской задолженности (по счетам)"""
    # Дебиторская задолженность (выставленные, но неоплаченные счета)
    unpaid_invoices = Invoice.query.filter(Invoice.status.in_(['draft', 'sent', 'overdue'])).all()
    # Можно также считать просроченные
    return render_template('finance/report_debtors.html', invoices=unpaid_invoices)