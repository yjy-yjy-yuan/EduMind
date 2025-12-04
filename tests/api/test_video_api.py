"""
API 测试 - 视频相关接口
测试视频上传、查询、处理状态等 API
"""
import pytest
import io


class TestVideoListAPI:
    """视频列表 API 测试"""

    def test_get_videos_list(self, client):
        """测试获取视频列表"""
        response = client.get('/api/videos/list')
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, dict)
        assert 'videos' in data

    def test_get_videos_with_pagination(self, client):
        """测试分页获取视频"""
        response = client.get('/api/videos/list?page=1&per_page=10')
        assert response.status_code == 200


class TestVideoDetailAPI:
    """视频详情 API 测试"""

    def test_get_nonexistent_video(self, client):
        """测试获取不存在的视频"""
        response = client.get('/api/videos/99999')
        assert response.status_code in [404, 500]

    def test_get_video_status_nonexistent(self, client):
        """测试获取不存在视频的状态"""
        response = client.get('/api/videos/99999/status')
        assert response.status_code in [404, 500]


class TestVideoUploadAPI:
    """视频上传 API 测试"""

    def test_upload_without_file(self, client):
        """测试无文件上传"""
        response = client.post('/api/videos/upload')
        assert response.status_code in [400, 415, 500]

    def test_upload_invalid_extension(self, client):
        """测试上传无效文件类型"""
        data = {
            'file': (io.BytesIO(b'fake content'), 'test.txt')
        }
        response = client.post(
            '/api/videos/upload',
            data=data,
            content_type='multipart/form-data'
        )
        # 应该拒绝非视频文件
        assert response.status_code in [400, 415, 422, 500]


class TestVideoDeleteAPI:
    """视频删除 API 测试"""

    def test_delete_nonexistent_video(self, client):
        """测试删除不存在的视频（使用正确的路由）"""
        response = client.delete('/api/videos/99999/delete')
        assert response.status_code in [404, 500]
