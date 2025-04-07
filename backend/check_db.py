"""检查数据库表结构"""
from app import create_app
from app.extensions import db
from app.models.user import User
import sqlite3
import os
import logging

# 暂时禁用日志
logging.disable(logging.INFO)

def check_db_structure():
    """检查数据库表结构"""
    app = create_app()
    with app.app_context():
        print("\n" + "="*80)
        print("检查数据库表结构".center(80))
        print("="*80)
        
        # 获取数据库文件路径
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        print(f"\n数据库文件路径: {db_path}")
        
        # 检查数据库文件是否存在
        if os.path.exists(db_path):
            print(f"数据库文件存在，大小: {os.path.getsize(db_path)} 字节")
        else:
            print("数据库文件不存在！")
            return
        
        # 获取数据库连接
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("\n用户表不存在！")
            return
        
        # 检查表结构
        try:
            # 从SQLite获取表结构
            print("\n用户表结构:")
            print("-" * 80)
            print(f"{'字段名':<20} {'类型':<15} {'是否可为空':<15} {'默认值':<15}")
            print("-" * 80)
            
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            
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
            
        except Exception as e:
            print(f"\n获取表结构时出错: {str(e)}")
        
        print("\n" + "="*80)
        print("检查完成！".center(80))
        print("="*80)

if __name__ == '__main__':
    check_db_structure()
    # 重新启用日志
    logging.disable(logging.NOTSET)
