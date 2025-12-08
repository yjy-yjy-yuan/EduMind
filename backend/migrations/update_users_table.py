"""更新用户表的迁移脚本，添加个人信息字段"""

import sqlalchemy as sa
from alembic import op

# 修订版本ID
revision = '004_update_users_table'
down_revision = '003_add_users_table'  # 依赖于之前创建用户表的迁移
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库结构"""
    # 添加新的个人信息字段
    op.add_column('users', sa.Column('gender', sa.String(length=10), nullable=True))
    op.add_column('users', sa.Column('education', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('identity', sa.String(length=50), nullable=True))
    op.add_column('users', sa.Column('avatar', sa.String(length=255), nullable=True))


def downgrade():
    """回滚数据库结构"""
    # 删除添加的字段
    op.drop_column('users', 'avatar')
    op.drop_column('users', 'identity')
    op.drop_column('users', 'education')
    op.drop_column('users', 'gender')
