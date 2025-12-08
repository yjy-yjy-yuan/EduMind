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
    from app.models import Note  # noqa: F401
    from app.models import NoteTimestamp  # noqa: F401
    from app.models import Subtitle  # noqa: F401
    from app.models import Video  # noqa: F401
    from app.models.qa import Question  # noqa: F401
    from app.models.user import User  # noqa: F401

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
    from app.models import Note  # noqa: F401
    from app.models import NoteTimestamp  # noqa: F401
    from app.models import Subtitle  # noqa: F401
    from app.models import Video  # noqa: F401
    from app.models.qa import Question  # noqa: F401
    from app.models.user import User  # noqa: F401

    with app.app_context():
        db.create_all()
        yield db.session
        # 只回滚，不删除表，避免影响后续测试
        db.session.rollback()


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
    return {'title': '测试视频', 'description': '这是一个测试视频', 'duration': 120, 'filepath': '/test/video.mp4'}


@pytest.fixture
def sample_note_data():
    """示例笔记数据"""
    return {'title': '测试笔记', 'content': '这是测试笔记内容', 'tags': ['测试', '示例']}


@pytest.fixture
def auth_headers():
    """认证请求头"""
    return {'Content-Type': 'application/json', 'Accept': 'application/json'}


# ============================================
# 数据库对象 Fixtures
# ============================================


@pytest.fixture
def created_video(app, db_session):
    """创建一个已存在的视频记录"""
    from app.models import Video
    from app.models import VideoStatus

    with app.app_context():
        video = Video(
            title='已存在的测试视频',
            filename='existing_test.mp4',
            filepath='/tmp/existing_test.mp4',
            status=VideoStatus.UPLOADED,
            md5='test_md5_hash_123',
        )
        db_session.add(video)
        db_session.commit()
        db_session.refresh(video)
        yield video


@pytest.fixture
def completed_video(app, db_session):
    """创建一个已处理完成的视频记录"""
    from app.models import Video
    from app.models import VideoStatus

    with app.app_context():
        video = Video(
            title='已完成处理的测试视频',
            filename='completed_test.mp4',
            filepath='/tmp/completed_test.mp4',
            status=VideoStatus.COMPLETED,
            md5='completed_md5_hash_456',
            duration=120.5,
            fps=30.0,
            width=1920,
            height=1080,
            summary='这是视频摘要',
            tags='测试,教育,编程',
        )
        db_session.add(video)
        db_session.commit()
        db_session.refresh(video)
        yield video


@pytest.fixture
def video_with_subtitles(app, db_session):
    """创建带有字幕的视频记录"""
    from app.models import Subtitle
    from app.models import Video
    from app.models import VideoStatus

    with app.app_context():
        video = Video(
            title='带字幕的测试视频',
            filename='subtitled_test.mp4',
            filepath='/tmp/subtitled_test.mp4',
            status=VideoStatus.COMPLETED,
            md5='subtitled_md5_hash_789',
            subtitle_filepath='/tmp/subtitles/test.srt',
        )
        db_session.add(video)
        db_session.commit()
        db_session.refresh(video)

        # 添加字幕
        subtitles = [
            Subtitle(video_id=video.id, start_time=0.0, end_time=5.0, text='第一条字幕', source='asr', language='zh'),
            Subtitle(video_id=video.id, start_time=5.0, end_time=10.0, text='第二条字幕', source='asr', language='zh'),
            Subtitle(video_id=video.id, start_time=10.0, end_time=15.0, text='第三条字幕', source='asr', language='zh'),
        ]
        for subtitle in subtitles:
            db_session.add(subtitle)
        db_session.commit()

        yield video


@pytest.fixture
def created_note(app, db_session):
    """创建一个已存在的笔记记录"""
    from app.models import Note

    with app.app_context():
        note = Note(
            title='已存在的测试笔记',
            content='这是已存在的测试笔记内容，用于测试更新和删除操作。',
            tags='测试,示例',
            note_type='general',
        )
        db_session.add(note)
        db_session.commit()
        db_session.refresh(note)
        yield note


@pytest.fixture
def created_user(app, db_session):
    """创建一个测试用户"""
    import uuid

    from app.models.user import User

    unique_id = str(uuid.uuid4())[:8]

    with app.app_context():
        user = User(
            username=f'testuser_{unique_id}',
            email=f'test_{unique_id}@example.com',
            password='testpassword123',  # User.__init__ 需要 password 参数
            gender='male',
            education='本科',
            occupation='学生',
            learning_direction='编程',
            bio='测试用户简介',
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        yield user


@pytest.fixture
def logged_in_client(app, client, created_user):
    """创建已登录的测试客户端"""
    import json

    # 执行登录 (使用动态生成的用户名)
    _response = client.post(  # noqa: F841
        '/api/auth/login',
        data=json.dumps({'username': created_user.username, 'password': 'testpassword123'}),
        content_type='application/json',
    )

    # 返回客户端 (session已经被设置)
    # 将用户信息保存在client对象上供测试使用
    client._test_user = created_user
    yield client


# ============================================
# Q&A 测试 Fixtures
# ============================================


@pytest.fixture
def sample_question_data():
    """示例问答数据"""
    return {'question': '什么是机器学习？', 'mode': 'free', 'stream': False, 'use_ollama': False}


@pytest.fixture
def sample_video_question_data(completed_video):
    """示例视频问答数据"""
    return {
        'video_id': completed_video.id if completed_video else 1,
        'question': '这个视频讲的是什么？',
        'mode': 'video',
        'stream': False,
        'use_ollama': False,
    }


# ============================================
# 聊天测试 Fixtures
# ============================================


@pytest.fixture
def sample_chat_data():
    """示例聊天数据"""
    return {'message': '你好，请问有什么可以帮助你的？', 'mode': 'free'}


# ============================================
# 知识图谱测试 Fixtures
# ============================================


@pytest.fixture
def sample_kg_question_data():
    """示例知识图谱问题生成数据"""
    return {
        'concept': '机器学习',
        'context': '机器学习是人工智能的一个分支，它使计算机能够从数据中学习。',
        'count': 3,
        'use_ollama': False,
    }


# ============================================
# 文件操作 Fixtures
# ============================================


@pytest.fixture
def temp_video_file(app):
    """创建临时视频文件用于上传测试"""
    import io

    # 创建一个模拟的视频文件 (实际上是空文件，仅用于测试上传逻辑)
    video_content = b'\x00\x00\x00\x1c\x66\x74\x79\x70\x69\x73\x6f\x6d'  # 简单的MP4头部
    video_file = io.BytesIO(video_content)
    video_file.name = 'test_upload.mp4'
    yield video_file


@pytest.fixture
def temp_subtitle_file(app):
    """创建临时字幕文件"""
    import io

    subtitle_content = """1
00:00:00,000 --> 00:00:05,000
这是第一条测试字幕

2
00:00:05,000 --> 00:00:10,000
这是第二条测试字幕

3
00:00:10,000 --> 00:00:15,000
这是第三条测试字幕
"""
    subtitle_file = io.BytesIO(subtitle_content.encode('utf-8'))
    subtitle_file.name = 'test.srt'
    yield subtitle_file


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
