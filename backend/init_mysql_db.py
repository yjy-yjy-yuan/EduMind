"""初始化MySQL数据库"""
import pymysql
import os
import logging
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 加载环境变量
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

# 数据库配置
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'Qw242015')
DB_NAME = os.getenv('DB_NAME', 'ai_edvision')

def init_database():
    """初始化数据库"""
    try:
        # 连接MySQL服务器
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        cursor = connection.cursor()
        
        # 创建数据库
        logger.info(f"创建数据库 {DB_NAME}")
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        logger.info("数据库初始化成功")
        
        # 关闭连接
        cursor.close()
        connection.close()
        
        return True
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        return False

if __name__ == '__main__':
    init_database()
