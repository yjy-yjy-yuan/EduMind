"""更新数据库表结构"""
from app import create_app
from app.extensions import db
from app.models.user import User

def update_tables():
    """更新数据库表结构"""
    app = create_app()
    with app.app_context():
        # 更新数据库表结构
        db.create_all()
        print("数据库表结构更新成功！")

if __name__ == '__main__':
    update_tables()
