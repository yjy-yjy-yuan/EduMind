"""
添加title列到videos表的迁移脚本
"""

import sqlite3
import logging
import os
from pathlib import Path

def add_title_column():
    """
    向videos表添加title列
    
    Returns:
        bool: 操作是否成功
    """
    try:
        # 获取数据库文件路径
        db_path = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / 'instance' / 'app.db'
        
        if not db_path.exists():
            logging.error(f"数据库文件不存在: {db_path}")
            return False
        
        logging.info(f"连接到数据库: {db_path}")
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # 检查title列是否已存在
        cursor.execute("PRAGMA table_info(videos)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'title' in column_names:
            logging.info("title列已存在，跳过迁移")
            conn.close()
            return True
        
        # 添加title列
        logging.info("添加title列到videos表")
        cursor.execute("ALTER TABLE videos ADD COLUMN title TEXT")
        
        conn.commit()
        conn.close()
        
        logging.info("成功添加title列到videos表")
        return True
        
    except Exception as e:
        logging.error(f"添加title列时发生错误: {str(e)}")
        return False

if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    
    success = add_title_column()
    print(f"迁移{'成功' if success else '失败'}")
