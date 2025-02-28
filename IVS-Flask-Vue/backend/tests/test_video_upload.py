import os
import pytest
from app import create_app, db
from app.models.video import Video, VideoStatus

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_upload_video_file(client):
    """测试上传视频文件"""
    # 创建测试视频文件
    test_video = 'test_video.mp4'
    with open(test_video, 'wb') as f:
        f.write(b'fake video content')
    
    try:
        # 上传视频
        with open(test_video, 'rb') as f:
            response = client.post(
                '/api/videos/upload',
                data={'file': (f, 'test_video.mp4')}
            )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'id' in data
        assert data['status'] == 'processing'
        
        # 检查数据库记录
        video = Video.query.get(data['id'])
        assert video is not None
        assert video.title == 'test_video.mp4'
        assert video.status == VideoStatus.PROCESSING
        
    finally:
        # 清理测试文件
        if os.path.exists(test_video):
            os.remove(test_video)

def test_upload_video_url(client):
    """测试上传视频链接"""
    # B站视频链接
    response = client.post(
        '/api/videos/upload-url',
        json={'url': 'https://www.bilibili.com/video/BV1234567890'}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'id' in data
    assert data['status'] == 'processing'
    
    # YouTube视频链接
    response = client.post(
        '/api/videos/upload-url',
        json={'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'}
    )
    
    assert response.status_code == 200
    data = response.get_json()
    assert 'id' in data
    assert data['status'] == 'processing'

def test_invalid_video_url(client):
    """测试无效的视频链接"""
    response = client.post(
        '/api/videos/upload-url',
        json={'url': 'https://invalid-url.com/video'}
    )
    
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
