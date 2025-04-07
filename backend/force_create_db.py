"""强制创建数据库和表"""
import os
import sqlite3
from app import create_app
from app.extensions import db
from app.models.user import User

def force_create_db():
    """强制创建数据库和表"""
    app = create_app()
    with app.app_context():
        print("\n" + "="*80)
        print("开始强制创建数据库和表".center(80))
        print("="*80)
        
        # 获取数据库文件路径
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        print(f"\n数据库文件路径: {db_path}")
        
        # 如果数据库文件存在但大小为0，或者不存在，则删除它
        if os.path.exists(db_path):
            if os.path.getsize(db_path) == 0:
                os.remove(db_path)
                print("已删除空的数据库文件")
            else:
                print(f"数据库文件存在，大小: {os.path.getsize(db_path)} 字节")
        
        # 创建新的数据库连接
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(64) UNIQUE,
            email VARCHAR(120) UNIQUE,
            password_hash VARCHAR(128),
            created_at DATETIME,
            last_login DATETIME,
            gender VARCHAR(10),
            education VARCHAR(50),
            occupation VARCHAR(50),
            learning_direction VARCHAR(100),
            avatar VARCHAR(255),
            bio TEXT
        )
        """)
        conn.commit()
        print("\n已手动创建用户表")
        
        # 检查表结构
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        
        print("\n用户表结构:")
        print("-" * 80)
        print(f"{'字段名':<20} {'类型':<15} {'是否可为空':<15} {'默认值':<15}")
        print("-" * 80)
        
        for column in columns:
            col_id, name, type_, notnull, default_value, pk = column
            print(f"{name:<20} {type_:<15} {'否' if notnull else '是':<15} {str(default_value):<15}")
        
        # 检查是否包含新增字段
        column_names = [column[1] for column in columns]
        new_fields = ['gender', 'education', 'occupation', 'learning_direction', 'bio']
        
        print("\n新增字段检查:")
        print("-" * 80)
        for field in new_fields:
            if field in column_names:
                print(f"✓ 字段 '{field}' 已存在")
            else:
                print(f"✗ 字段 '{field}' 不存在")
        
        print("\n" + "="*80)
        print("数据库和表创建完成！".center(80))
        print("="*80)

if __name__ == '__main__':
    force_create_db()
