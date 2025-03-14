"""Flask应用工厂"""
import logging
import os
from flask import Flask, request, jsonify
from .extensions import db, migrate, cors, celery
from .config import config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_name='default'):
    """创建Flask应用实例"""
    try:
        app = Flask(__name__)
        
        # 加载配置
        app.config.from_object(config[config_name])
        config[config_name].init_app(app)
        
        # 配置文件上传相关参数
        app.config['MAX_CONTENT_PATH'] = None  # 不限制文件路径长度
        app.config['UPLOAD_EXTENSIONS'] = ['.mp4', '.avi', '.mov', '.mkv', '.flv']  # 允许的文件类型
        
        # 配置CORS
        cors.init_app(app, resources={
            r"/api/*": {
                "origins": ["http://localhost:5173"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept", "Origin"],
                "expose_headers": ["Content-Disposition"],
                "supports_credentials": True,
                "max_age": 3600
            }
        })
        
        # 初始化数据库
        db.init_app(app)
        migrate.init_app(app, db)
        
        # 配置Celery
        celery.conf.update(app.config)
        
        # 请求日志中间件
        @app.before_request
        def log_request_info():
            """记录请求信息"""
            logger.info('=====================================')
            logger.info('新请求开始')
            logger.info(f'Method: {request.method}')
            logger.info(f'Path: {request.path}')
            logger.info(f'Headers: {dict(request.headers)}')
            
        @app.after_request
        def log_response_info(response):
            """记录响应信息"""
            logger.info('------------------------')
            logger.info(f'响应状态: {response.status}')
            logger.info(f'响应头: {dict(response.headers)}')
            logger.info('=====================================')
            return response
        
        # 注册蓝图
        with app.app_context():
            # 创建数据库表
            db.create_all()
            
            # 确保上传目录存在
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            os.makedirs(app.config['SUBTITLE_FOLDER'], exist_ok=True)
            os.makedirs(app.config['PREVIEW_FOLDER'], exist_ok=True)
            
            # 注册蓝图
            from .routes import video_bp, qa_bp, chat_bp
            if 'video_bp' not in app.blueprints:
                app.register_blueprint(video_bp, url_prefix='/api/videos')
            if 'qa_bp' not in app.blueprints:
                app.register_blueprint(qa_bp, url_prefix='/api/qa')
            if 'chat_bp' not in app.blueprints:
                app.register_blueprint(chat_bp, url_prefix='/api/chat')
        
        # 添加根路由
        @app.route('/')
        def index():
            return jsonify({
                'status': 'success',
                'message': 'Welcome to AI-EdVision API',
                'version': '1.0.0'
            })
        
        # 添加健康检查路由
        @app.route('/api/health')
        def health():
            return jsonify({
                'status': 'ok',
                'services': {
                    'database': 'connected',
                    'redis': 'connected'
                }
            })
        
        return app
        
    except Exception as e:
        logger.error(f'创建Flask应用失败: {str(e)}')
        raise
