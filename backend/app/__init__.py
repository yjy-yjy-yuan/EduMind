"""Flask应用工厂"""

import logging
import os

from flask import Flask
from flask import jsonify
from flask import request
from flask_cors import CORS

from .config import config
from .extensions import celery
from .extensions import cors
from .extensions import db
from .extensions import migrate

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_app(config_name='default'):
    """创建Flask应用实例"""
    try:
        app = Flask(__name__)

        # 加载配置
        app.config.from_object(config[config_name])
        config[config_name].init_app(app)

        # 配置文件上传目录
        app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
        app.config['SUBTITLE_FOLDER'] = os.path.join(app.config['UPLOAD_FOLDER'], 'subtitles')
        app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 增加到500MB

        # 配置文件上传相关参数
        app.config['MAX_CONTENT_PATH'] = None  # 不限制文件路径长度
        app.config['UPLOAD_EXTENSIONS'] = ['.mp4', '.avi', '.mov', '.mkv', '.flv']  # 允许的文件类型

        # 确保上传目录存在
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['SUBTITLE_FOLDER'], exist_ok=True)

        # 配置CORS
        cors = CORS()
        cors.init_app(app, resources={r"/*": {"origins": "http://localhost:328", "supports_credentials": True}})

        # # 添加CORS响应头处理
        # @app.after_request
        # def after_request(response):
        #     response.headers.add('Access-Control-Allow-Origin', 'http://localhost:328')
        #     response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        #     response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        #     response.headers.add('Access-Control-Allow-Credentials', 'true')
        #     return response

        # 初始化数据库
        db.init_app(app)
        migrate.init_app(app, db)

        # 配置Celery
        celery.conf.update(app.config)

        # 创建Celery任务上下文
        class ContextTask(celery.Task):
            def __call__(self, *args, **kwargs):
                with app.app_context():
                    return self.run(*args, **kwargs)

        celery.Task = ContextTask

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
            try:
                logger.info('正在创建数据库表...')
                db.create_all()
                logger.info('数据库表创建成功')
            except Exception as e:
                logger.error(f'创建数据库表失败: {str(e)}')
                raise

            # 注册蓝图
            from .routes.auth import auth_bp
            from .routes.knowledge_graph import router as knowledge_graph_router
            from .routes.knowledge_graph_integration import integration_bp
            from .routes.note import note_bp
            from .routes.qa import qa_bp
            from .routes.subtitle import subtitle_bp
            from .routes.video import bp as video_bp

            app.register_blueprint(video_bp, url_prefix='/api/videos')
            app.register_blueprint(subtitle_bp, url_prefix='/api/subtitles')
            app.register_blueprint(note_bp, url_prefix='/api/notes')
            app.register_blueprint(auth_bp, url_prefix='/api/auth')
            app.register_blueprint(qa_bp, url_prefix='/api/qa')
            app.register_blueprint(knowledge_graph_router, url_prefix='/api/knowledge-graph')
            app.register_blueprint(integration_bp, url_prefix='/api/knowledge-graph-integration')

        # 添加根路由
        @app.route('/')
        def index():
            return jsonify({'status': 'success', 'message': 'Welcome to EduMind API', 'version': '1.0.0'})

        # 添加健康检查路由
        @app.route('/api/health')
        def health():
            return jsonify({'status': 'ok', 'services': {'database': 'connected', 'redis': 'connected'}})

        return app

    except Exception as e:
        logger.error(f'创建Flask应用失败: {str(e)}')
        raise
