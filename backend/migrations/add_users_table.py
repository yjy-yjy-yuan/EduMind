"""添加用户表的迁移脚本"""

from datetime import datetime

import sqlalchemy as sa
from alembic import op

# 修订版本ID
revision = '003_add_users_table'
down_revision = None  # 设置为None表示这是独立的迁移
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库结构"""
    # 创建用户表
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.String(length=128), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    # 创建索引
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)


def downgrade():
    """回滚数据库结构"""
    # 删除索引
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_index(op.f('ix_users_username'), table_name='users')

    # 删除表
    op.drop_table('users')
