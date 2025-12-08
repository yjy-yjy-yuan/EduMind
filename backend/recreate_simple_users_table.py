"""重新创建简化版用户表"""

import sqlite3

from app import create_app
from app.extensions import db
from app.models.user import User


def recreate_users_table():
    """重新创建用户表"""
    app = create_app()
    with app.app_context():
        # 获取数据库连接
        conn = sqlite3.connect(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
        cursor = conn.cursor()

        # 备份现有用户数据
        try:
            cursor.execute("SELECT id, username, email, password_hash, created_at, last_login FROM users")
            users_data = cursor.fetchall()
            print(f"备份了 {len(users_data)} 个用户数据")
        except sqlite3.OperationalError:
            users_data = []
            print("无法获取现有用户数据或表不存在")

        # 删除现有用户表
        try:
            cursor.execute("DROP TABLE IF EXISTS users")
            conn.commit()
            print("已删除现有用户表")
        except Exception as e:
            print(f"删除表时出错: {str(e)}")

        # 关闭连接
        conn.close()

        # 创建新的用户表
        db.create_all()
        print("已创建新的用户表")

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
            print(f"已恢复 {len(users_data)} 个用户数据")
        except Exception as e:
            db.session.rollback()
            print(f"恢复用户数据时出错: {str(e)}")

        print("用户表重建完成！")


if __name__ == '__main__':
    recreate_users_table()
