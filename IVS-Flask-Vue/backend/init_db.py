from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    # 删除所有表
    db.drop_all()
    # 创建所有表
    db.create_all()
    print("数据库表已重新创建！")
