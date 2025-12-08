"""重新创建用户表"""

import os
import sqlite3
import time

from app import create_app
from app.extensions import db
from app.models.user import User


def recreate_users_table():
    """重新创建用户表"""
    app = create_app()
    with app.app_context():
        print("\n" + "=" * 50)
        print("开始重建用户表")
        print("=" * 50)

        # 获取数据库文件路径
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        print(f"\n数据库文件路径: {db_path}")

        # 检查数据库文件是否存在
        if os.path.exists(db_path):
            print(f"数据库文件存在，大小: {os.path.getsize(db_path)} 字节")
        else:
            print("数据库文件不存在，将创建新文件")

        # 获取数据库连接
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 备份现有用户数据
        try:
            cursor.execute("SELECT id, username, email, password_hash, created_at, last_login FROM users")
            users_data = cursor.fetchall()
            print(f"\n备份了 {len(users_data)} 个用户数据")
        except sqlite3.OperationalError:
            users_data = []
            print("\n无法获取现有用户数据或表不存在")

        # 删除现有用户表
        try:
            cursor.execute("DROP TABLE IF EXISTS users")
            conn.commit()
            print("\n已删除现有用户表")
        except Exception as e:
            print(f"\n删除表时出错: {str(e)}")

        # 创建新的用户表
        db.create_all()
        print("\n已创建新的用户表")

        # 等待一秒，确保表创建完成
        time.sleep(1)

        # 检查表结构
        try:
            # 直接从SQLAlchemy获取表结构
            print("\n用户表结构 (从SQLAlchemy获取):")
            for column in User.__table__.columns:
                print(f"  - {column.name} ({column.type})")

            # 从SQLite获取表结构
            print("\n用户表结构 (从SQLite获取):")
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            for column in columns:
                print(f"  - {column[1]} ({column[2]})")
        except Exception as e:
            print(f"\n获取表结构时出错: {str(e)}")

        # 恢复用户数据
        for user_data in users_data:
            user_id, username, email, password_hash, created_at, last_login = user_data
            user = User(username=username, email=email, password="temporary")
            user.id = user_id
            user.password_hash = password_hash
            user.created_at = created_at
            user.last_login = last_login
            db.session.add(user)

        try:
            db.session.commit()
            print(f"\n已恢复 {len(users_data)} 个用户数据")
        except Exception as e:
            db.session.rollback()
            print(f"\n恢复用户数据时出错: {str(e)}")

        print("\n用户表重建完成！")
        print("=" * 50)


if __name__ == '__main__':
    recreate_users_table()
