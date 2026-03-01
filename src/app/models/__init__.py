from .user import User
from .role import Role
from .permission import Permission
from .department import Department
from .position import Position
from .employee import Employee
from .category import Category
from .product import Product
from .warehouse import Warehouse
from .stock import Stock
from .stock_movement import StockMovement
from .stock_log import StockLog
from .customer import Customer
from .order import Order
from .order_item import OrderItem
from .order_history import OrderHistory
from .invoice import Invoice
from .payment import Payment
from .transaction import Transaction
from .transaction_category import TransactionCategory
from .unit import Unit
from .currency import Currency

# Функция загрузчика пользователя для Flask-Login
from app.extensions import login_manager
from .user import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))