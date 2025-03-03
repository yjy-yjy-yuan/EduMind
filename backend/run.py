"""Flask应用入口，用于启动应用"""
import os
import logging
from app import create_app

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    # 创建必要的目录
    app = create_app()
    
    if __name__ == '__main__':
        # 设置主机和端口
        host = os.environ.get('FLASK_HOST', '127.0.0.1')
        port = int(os.environ.get('FLASK_PORT', 5000))
        
        # 启动应用
        logger.info(f'启动Flask应用，监听 {host}:{port}')
        app.run(
            host=host,
            port=port,
            debug=True,
            use_reloader=True
        )
except Exception as e:
    logger.error(f'启动Flask应用失败: {str(e)}')
    raise
