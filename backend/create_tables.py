"""创建数据库表"""
from app import create_app
from app.extensions import db
from app.models.user import User

def create_tables():
    """创建所有数据库表"""
    app = create_app()
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("数据库表创建成功！")

if __name__ == '__main__':
    create_tables()
