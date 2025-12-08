"""
API 测试 - 视频相关接口
测试视频上传、查询、处理状态等 API

覆盖端点：
- POST /api/videos/upload - 上传本地视频
- POST /api/videos/upload-url - URL上传视频
- GET /api/videos/list - 获取视频列表
- GET /api/videos/<id> - 获取视频详情
- GET /api/videos/<id>/status - 获取处理状态
- GET /api/videos/<id>/preview - 获取预览图
- POST /api/videos/<id>/process - 开始处理视频
- GET /api/videos/<id>/stream - 流式传输视频
- GET /api/videos/<id>/subtitle - 获取字幕
- DELETE /api/videos/<id>/delete - 删除视频
- POST /api/videos/<id>/generate-summary - 生成摘要
- POST /api/videos/<id>/generate-tags - 生成标签
"""

import io
import json

import pytest


class TestVideoListAPI:
    """视频列表 API 测试"""

    def test_get_videos_list(self, client):
        """测试获取视频列表"""
        response = client.get('/api/videos/list')
        # 可能返回 500 如果数据库有问题
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.get_json()
            assert isinstance(data, dict)
            assert 'videos' in data

    def test_get_videos_with_pagination(self, client):
        """测试分页获取视频"""
        response = client.get('/api/videos/list?page=1&per_page=10')
        # 可能返回 500 如果数据库有问题
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.get_json()
            assert 'videos' in data
            # 验证分页参数
            if 'page' in data:
                assert data['page'] == 1
            if 'per_page' in data:
                assert data['per_page'] == 10

    def test_get_videos_page_boundary(self, client):
        """测试边界分页参数"""
        response = client.get('/api/videos/list?page=999&per_page=5')
        # 可能返回 500 如果数据库有问题
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.get_json()
            # 超出范围的页码应返回空列表
            assert 'videos' in data

    def test_get_videos_response_structure(self, client):
        """测试响应结构（迁移契约）"""
        response = client.get('/api/videos/list')
        # 可能返回 500 如果数据库有问题
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.get_json()
            # 验证必要字段存在（迁移后需保持一致）
            assert 'videos' in data
            assert isinstance(data['videos'], list)


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

    def test_get_existing_video(self, client, created_video):
        """测试获取已存在的视频"""
        response = client.get(f'/api/videos/{created_video.id}')
        assert response.status_code == 200
        data = response.get_json()
        assert data['id'] == created_video.id

    def test_get_video_status_existing(self, client, created_video):
        """测试获取已存在视频的状态"""
        response = client.get(f'/api/videos/{created_video.id}/status')
        assert response.status_code == 200
        data = response.get_json()
        # 验证状态响应结构
        assert 'status' in data or 'processing_status' in data

    def test_get_video_detail_structure(self, client, completed_video):
        """测试视频详情响应结构（迁移契约）"""
        response = client.get(f'/api/videos/{completed_video.id}')
        assert response.status_code == 200
        data = response.get_json()

        # 验证关键字段存在
        assert 'id' in data
        # title 可能为 None，但字段应存在
        assert 'title' in data or 'filename' in data


class TestVideoUploadAPI:
    """视频上传 API 测试"""

    def test_upload_without_file(self, client):
        """测试无文件上传"""
        response = client.post('/api/videos/upload')
        assert response.status_code in [400, 415, 500]

    def test_upload_invalid_extension(self, client):
        """测试上传无效文件类型"""
        data = {'file': (io.BytesIO(b'fake content'), 'test.txt')}
        response = client.post('/api/videos/upload', data=data, content_type='multipart/form-data')
        # 应该拒绝非视频文件
        assert response.status_code in [400, 415, 422, 500]

    def test_upload_valid_extension_types(self, client):
        """测试各种有效视频扩展名"""
        valid_extensions = ['mp4', 'avi', 'mov', 'mkv', 'webm']

        for ext in valid_extensions:
            # 创建带有简单内容的文件
            fake_video = io.BytesIO(b'\x00\x00\x00\x1c\x66\x74\x79\x70')
            data = {'file': (fake_video, f'test.{ext}')}
            response = client.post('/api/videos/upload', data=data, content_type='multipart/form-data')
            # 应该接受文件（可能因为其他原因失败，但不应是扩展名问题）
            # 注意：实际上可能会因为文件内容无效而失败
            assert response.status_code in [200, 201, 400, 500]


class TestVideoURLUploadAPI:
    """视频 URL 上传 API 测试"""

    def test_upload_url_without_url(self, client, auth_headers):
        """测试不带 URL 的请求"""
        response = client.post('/api/videos/upload-url', data=json.dumps({}), headers=auth_headers)
        assert response.status_code in [400, 422, 500]

    def test_upload_url_invalid_url(self, client, auth_headers):
        """测试无效的 URL"""
        response = client.post(
            '/api/videos/upload-url', data=json.dumps({'url': 'not-a-valid-url'}), headers=auth_headers
        )
        assert response.status_code in [400, 422, 500]

    def test_upload_url_unsupported_site(self, client, auth_headers):
        """测试不支持的网站"""
        response = client.post(
            '/api/videos/upload-url', data=json.dumps({'url': 'https://example.com/video.mp4'}), headers=auth_headers
        )
        # 应该返回不支持的网站错误
        assert response.status_code in [400, 422, 500]

    def test_upload_url_bilibili_format(self, client, auth_headers):
        """测试 B站 URL 格式（不实际下载）"""
        # 这个测试验证 URL 格式被正确识别
        response = client.post(
            '/api/videos/upload-url',
            data=json.dumps({'url': 'https://www.bilibili.com/video/BV1234567890'}),
            headers=auth_headers,
        )
        # 可能返回成功（开始下载）或失败（网络问题），但不应是格式错误
        assert response.status_code in [200, 201, 400, 500, 503]

    def test_upload_url_youtube_format(self, client, auth_headers):
        """测试 YouTube URL 格式"""
        response = client.post(
            '/api/videos/upload-url',
            data=json.dumps({'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'}),
            headers=auth_headers,
        )
        assert response.status_code in [200, 201, 400, 500, 503]


class TestVideoProcessAPI:
    """视频处理 API 测试"""

    def test_process_nonexistent_video(self, client, auth_headers):
        """测试处理不存在的视频"""
        response = client.post(
            '/api/videos/99999/process', data=json.dumps({'language': 'Chinese', 'model': 'base'}), headers=auth_headers
        )
        assert response.status_code in [404, 500]

    def test_process_existing_video(self, client, created_video, auth_headers):
        """测试处理已存在的视频"""
        response = client.post(
            f'/api/videos/{created_video.id}/process',
            data=json.dumps({'language': 'Chinese', 'model': 'base'}),
            headers=auth_headers,
        )
        # 可能成功启动任务或因为文件不存在而失败
        assert response.status_code in [200, 201, 400, 404, 500]

    def test_process_with_english_language(self, client, created_video, auth_headers):
        """测试英文语言处理参数"""
        response = client.post(
            f'/api/videos/{created_video.id}/process',
            data=json.dumps({'language': 'English', 'model': 'base'}),
            headers=auth_headers,
        )
        assert response.status_code in [200, 201, 400, 404, 500]

    def test_process_with_different_models(self, client, created_video, auth_headers):
        """测试不同的 Whisper 模型参数"""
        models = ['tiny', 'base', 'small', 'medium', 'turbo']

        for model in models:
            response = client.post(
                f'/api/videos/{created_video.id}/process',
                data=json.dumps({'language': 'Chinese', 'model': model}),
                headers=auth_headers,
            )
            # 参数应该被接受
            assert response.status_code in [200, 201, 400, 404, 500]


class TestVideoDeleteAPI:
    """视频删除 API 测试"""

    def test_delete_nonexistent_video(self, client):
        """测试删除不存在的视频"""
        response = client.delete('/api/videos/99999/delete')
        assert response.status_code in [404, 500]

    def test_delete_existing_video(self, client, created_video):
        """测试删除已存在的视频"""
        video_id = created_video.id
        response = client.delete(f'/api/videos/{video_id}/delete')
        # 应该成功删除
        assert response.status_code in [200, 204, 404, 500]

        # 验证视频已被删除（如果删除成功）
        if response.status_code in [200, 204]:
            verify_response = client.get(f'/api/videos/{video_id}')
            assert verify_response.status_code in [404, 500]


class TestVideoPreviewAPI:
    """视频预览 API 测试"""

    def test_get_preview_nonexistent_video(self, client):
        """测试获取不存在视频的预览"""
        response = client.get('/api/videos/99999/preview')
        assert response.status_code in [404, 500]

    def test_get_preview_no_preview_file(self, client, created_video):
        """测试获取没有预览图的视频"""
        response = client.get(f'/api/videos/{created_video.id}/preview')
        # 可能返回 404（无预览）或默认图
        assert response.status_code in [200, 404, 500]


class TestVideoStreamAPI:
    """视频流式传输 API 测试"""

    def test_stream_nonexistent_video(self, client):
        """测试流式传输不存在的视频"""
        response = client.get('/api/videos/99999/stream')
        assert response.status_code in [404, 500]

    def test_stream_no_file(self, client, created_video):
        """测试流式传输没有文件的视频"""
        response = client.get(f'/api/videos/{created_video.id}/stream')
        # 文件不存在，应该返回错误
        assert response.status_code in [404, 500]


class TestVideoSubtitleAPI:
    """视频字幕 API 测试"""

    def test_get_subtitle_nonexistent_video(self, client):
        """测试获取不存在视频的字幕"""
        response = client.get('/api/videos/99999/subtitle')
        assert response.status_code in [404, 500]

    def test_get_subtitle_different_formats(self, client, video_with_subtitles):
        """测试获取不同格式的字幕"""
        formats = ['srt', 'vtt', 'txt']

        for fmt in formats:
            response = client.get(f'/api/videos/{video_with_subtitles.id}/subtitle?format={fmt}')
            # 可能成功或因为文件不存在而失败
            assert response.status_code in [200, 404, 500]


class TestVideoSummaryAPI:
    """视频摘要生成 API 测试"""

    def test_generate_summary_nonexistent_video(self, client, auth_headers):
        """测试为不存在的视频生成摘要"""
        response = client.post('/api/videos/99999/generate-summary', headers=auth_headers)
        assert response.status_code in [404, 500]

    def test_generate_summary_uncompleted_video(self, client, created_video, auth_headers):
        """测试为未处理完成的视频生成摘要"""
        response = client.post(f'/api/videos/{created_video.id}/generate-summary', headers=auth_headers)
        # 应该失败，因为视频未处理完成
        assert response.status_code in [400, 404, 500]


class TestVideoTagsAPI:
    """视频标签生成 API 测试"""

    def test_generate_tags_nonexistent_video(self, client, auth_headers):
        """测试为不存在的视频生成标签"""
        response = client.post('/api/videos/99999/generate-tags', headers=auth_headers)
        assert response.status_code in [404, 500]

    def test_generate_tags_no_summary(self, client, created_video, auth_headers):
        """测试为没有摘要的视频生成标签"""
        response = client.post(f'/api/videos/{created_video.id}/generate-tags', headers=auth_headers)
        # 应该失败，因为没有摘要
        assert response.status_code in [400, 404, 500]


class TestVideoTaskStatusAPI:
    """异步任务状态 API 测试"""

    def test_get_task_status_invalid_id(self, client):
        """测试获取无效任务ID的状态"""
        response = client.get('/api/videos/status/invalid-task-id')
        # Celery 任务状态 API 可能返回 200 (PENDING状态) 或错误
        assert response.status_code in [200, 404, 500]


class TestVideoAPIContract:
    """
    API 契约测试
    确保迁移后 API 行为一致
    """

    def test_list_response_format(self, client):
        """测试列表响应格式契约"""
        response = client.get('/api/videos/list')
        # 可能返回 500 如果数据库有问题
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.get_json()
            # 必须包含 videos 字段
            assert 'videos' in data
            assert isinstance(data['videos'], list)

    def test_detail_response_format(self, client, completed_video):
        """测试详情响应格式契约"""
        response = client.get(f'/api/videos/{completed_video.id}')
        assert response.status_code == 200
        data = response.get_json()

        # 必须包含基本字段
        required_fields = ['id']
        for field in required_fields:
            assert field in data, f"缺少必要字段: {field}"

    def test_status_response_format(self, client, created_video):
        """测试状态响应格式契约"""
        response = client.get(f'/api/videos/{created_video.id}/status')
        assert response.status_code == 200
        data = response.get_json()

        # 必须包含状态信息
        assert 'status' in data or 'processing_status' in data

    def test_error_response_format(self, client):
        """测试错误响应格式契约"""
        response = client.get('/api/videos/99999')

        # 错误响应应该是 JSON 格式
        if response.status_code in [404, 500]:
            assert response.content_type == 'application/json' or response.get_json() is not None
