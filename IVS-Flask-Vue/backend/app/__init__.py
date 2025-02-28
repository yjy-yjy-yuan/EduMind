"""Flask应用工厂"""
import logging
from flask import Flask, request, jsonify
from .extensions import db, migrate, cors, celery
from .config import Config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def create_app(config_class=Config):
    """创建Flask应用实例"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 配置CORS - 完全禁用Flask-CORS的自动添加，改为手动添加
    cors.init_app(app, resources={}, automatic_options=False)
    
    # 添加CORS处理
    @app.after_request
    def after_request(response):
        # 检查是否已经有这些头，避免重复添加
        if 'Access-Control-Allow-Origin' not in response.headers:
            response.headers.add('Access-Control-Allow-Origin', 'http://localhost:5173')
        if 'Access-Control-Allow-Headers' not in response.headers:
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,X-Requested-With')
        if 'Access-Control-Allow-Methods' not in response.headers:
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        if 'Access-Control-Allow-Credentials' not in response.headers:
            response.headers.add('Access-Control-Allow-Credentials', 'true')
        if 'Access-Control-Max-Age' not in response.headers:
            response.headers.add('Access-Control-Max-Age', '3600')
        return response
    
    # 初始化其他扩展
    db.init_app(app)
    migrate.init_app(app, db)
    
    # 配置Celery
    celery.conf.update(app.config)
    
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
                
    celery.Task = ContextTask
    
    # 请求日志中间件
    @app.before_request
    def log_request_info():
        """记录请求信息"""
        app.logger.info('=====================================')
        app.logger.info('新请求开始')
        app.logger.info(f'Method: {request.method}')
        app.logger.info(f'Path: {request.path}')
        app.logger.info(f'Headers: {dict(request.headers)}')
        
    @app.after_request
    def log_response_info(response):
        app.logger.info('------------------------')
        app.logger.info(f'响应状态: {response.status}')
        app.logger.info(f'响应头: {dict(response.headers)}')
        app.logger.info('------------------------')
        app.logger.info('=====================================')
        app.logger.info('请求处理完成')
        app.logger.info(f'Status: {response.status}')
        app.logger.info(f'Headers: {dict(response.headers)}')
        app.logger.info('=====================================')
        
        return response
    
    # 注册蓝图
    from .routes import video_bp, qa_bp
    app.register_blueprint(video_bp, url_prefix='/api/videos')  
    app.register_blueprint(qa_bp, url_prefix='/api/qa')  
    
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
