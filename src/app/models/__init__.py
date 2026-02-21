from .test import Test
from .user import User
from .role import Role
from .user import User
from .role import Role
from .test import Test
from .department import Department
from .position import Position
from .employee import Employee

from ..extensions import login_manager
from .user import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))