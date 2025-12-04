"""
pytest 测试配置文件
提供测试所需的 fixtures 和配置
支持 Flask (当前) 和 FastAPI (重构后)
"""
import os
import sys
import tempfile
import pytest

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')

# 将 backend 目录添加到 Python 路径
sys.path.insert(0, BACKEND_DIR)


# ============================================
# Flask 应用 Fixtures (当前框架)
# ============================================

@pytest.fixture(scope='session')
def app():
    """创建测试用 Flask 应用实例"""
    from app import create_app
    from app.extensions import db
    # 导入所有模型以确保表被创建
    from app.models import Video, Subtitle, Note, NoteTimestamp  # noqa: F401

    # 创建临时目录用于测试文件
    with tempfile.TemporaryDirectory() as temp_dir:
        os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

        app = create_app('testing')

        # 覆盖上传目录为临时目录
        app.config['UPLOAD_FOLDER'] = os.path.join(temp_dir, 'uploads')
        app.config['SUBTITLE_FOLDER'] = os.path.join(temp_dir, 'subtitles')
        app.config['PREVIEW_FOLDER'] = os.path.join(temp_dir, 'previews')
        app.config['TEMP_FOLDER'] = os.path.join(temp_dir, 'temp')

        # 创建必要目录
        for folder in ['uploads', 'subtitles', 'previews', 'temp']:
            os.makedirs(os.path.join(temp_dir, folder), exist_ok=True)

        # 创建所有数据库表
        with app.app_context():
            db.create_all()

        yield app


@pytest.fixture(scope='function')
def client(app):
    """创建 Flask 测试客户端"""
    return app.test_client()


@pytest.fixture(scope='function')
def db_session(app):
    """创建数据库会话，每个测试后回滚"""
    from app.extensions import db
    # 导入所有模型以确保表被创建
    from app.models import Video, Subtitle, Note, NoteTimestamp  # noqa: F401

    with app.app_context():
        db.create_all()
        yield db.session
        db.session.rollback()
        db.drop_all()


@pytest.fixture(scope='function')
def runner(app):
    """创建 CLI 测试运行器"""
    return app.test_cli_runner()


# ============================================
# 通用测试数据 Fixtures
# ============================================

@pytest.fixture
def sample_video_data():
    """示例视频数据"""
    return {
        'title': '测试视频',
        'description': '这是一个测试视频',
        'duration': 120,
        'filepath': '/test/video.mp4'
    }


@pytest.fixture
def sample_note_data():
    """示例笔记数据"""
    return {
        'title': '测试笔记',
        'content': '这是测试笔记内容',
        'tags': ['测试', '示例']
    }


@pytest.fixture
def auth_headers():
    """认证请求头"""
    return {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }


# ============================================
# FastAPI Fixtures (重构后启用)
# ============================================
#
# 重构为 FastAPI 后，取消下面的注释并注释掉上面的 Flask fixtures
#
# from httpx import AsyncClient
# from app.main import app as fastapi_app
# from app.core.database import get_db, Base, engine
#
# @pytest.fixture(scope='session')
# def app():
#     """FastAPI 应用实例"""
#     return fastapi_app
#
# @pytest.fixture
# async def client(app):
#     """创建异步测试客户端"""
#     async with AsyncClient(app=app, base_url="http://test") as ac:
#         yield ac
#
# @pytest.fixture(scope='function')
# def db_session():
#     """数据库会话"""
#     Base.metadata.create_all(bind=engine)
#     yield
#     Base.metadata.drop_all(bind=engine)
