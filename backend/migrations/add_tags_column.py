"""
添加视频标签字段的数据库迁移脚本
"""
import sqlite3
import os
import sys
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 获取数据库路径
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'app.db')

def add_tags_column():
    """向视频表添加标签字段"""
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查数据库是否存在
        if not os.path.exists(DB_PATH):
            logger.error(f"数据库文件不存在: {DB_PATH}")
            return False
            
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='videos'")
        if not cursor.fetchone():
            logger.error("videos表不存在")
            return False
            
        # 检查字段是否已存在
        cursor.execute("PRAGMA table_info(videos)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'tags' in columns:
            logger.info("tags字段已存在，无需添加")
            return True
            
        # 添加tags字段
        cursor.execute("ALTER TABLE videos ADD COLUMN tags TEXT")
        conn.commit()
        
        logger.info("成功添加tags字段到videos表")
        return True
        
    except Exception as e:
        logger.error(f"添加tags字段时发生错误: {str(e)}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    if add_tags_column():
        print("成功添加tags字段到videos表")
    else:
        print("添加tags字段失败")
        sys.exit(1)
