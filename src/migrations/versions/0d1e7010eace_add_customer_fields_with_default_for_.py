"""Add customer fields with default for type

Revision ID: 0d1e7010eace
Revises: 89bcdd58148a
Create Date: 2026-02-22 21:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0d1e7010eace'
down_revision = '89bcdd58148a'
branch_labels = None
depends_on = None

def upgrade():
    # Шаг 1: Добавляем колонки как nullable
    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('type', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('first_name', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('last_name', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('middle_name', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('legal_name', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('inn', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('kpp', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('ogrn', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('note', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(), nullable=True))
        # is_active уже существовал? В модели он был, но если его нет в таблице, добавьте:
       

    # Шаг 2: Заполняем type для существующих строк значением 'individual'
    op.execute("UPDATE customers SET type = 'individual' WHERE type IS NULL")

    # Шаг 3: Делаем поле type NOT NULL
    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.alter_column('type', nullable=False)

def downgrade():
    # Удаляем все добавленные колонки
    with op.batch_alter_table('customers', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
        batch_op.drop_column('note')
        batch_op.drop_column('ogrn')
        batch_op.drop_column('kpp')
        batch_op.drop_column('inn')
        batch_op.drop_column('legal_name')
        batch_op.drop_column('middle_name')
        batch_op.drop_column('last_name')
        batch_op.drop_column('first_name')
        batch_op.drop_column('type')
        # если добавляли is_active, то удалите и его