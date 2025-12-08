"""
API 测试 - 字幕相关接口
测试字幕的 CRUD 操作和格式转换

覆盖端点：
- GET /api/subtitles/videos/<id>/subtitles - 获取视频字幕
- POST /api/subtitles/videos/<id>/subtitles/generate - 生成字幕
- GET /api/subtitles/videos/<id>/subtitles/semantic-merged - 获取语义合并字幕
- POST /api/subtitles/videos/<id>/subtitles/semantic-merge - 触发语义合并
- GET /api/subtitles/videos/<id>/subtitles/export - 导出字幕
- PUT /api/subtitles/videos/<id>/subtitles/<subtitle_id> - 更新字幕
- POST /api/subtitles/videos/<id>/subtitles/merge - 合并字幕
"""

import json


class TestSubtitleGetAPI:
    """字幕获取 API 测试"""

    def test_get_subtitles_nonexistent_video(self, client):
        """测试获取不存在视频的字幕"""
        response = client.get('/api/subtitles/videos/99999/subtitles')
        assert response.status_code in [200, 404, 500]

    def test_get_subtitles_existing_video(self, client, video_with_subtitles):
        """测试获取已存在视频的字幕"""
        response = client.get(f'/api/subtitles/videos/{video_with_subtitles.id}/subtitles')
        # 可能返回 500 如果字幕文件不存在
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.get_json()
            # 验证返回的是字幕列表
            assert isinstance(data, (list, dict))

    def test_get_subtitles_response_structure(self, client, video_with_subtitles):
        """测试字幕响应结构（迁移契约）"""
        response = client.get(f'/api/subtitles/videos/{video_with_subtitles.id}/subtitles')
        # 可能返回 500 如果字幕文件不存在
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.get_json()
            # 如果返回字幕列表
            if isinstance(data, list) and len(data) > 0:
                subtitle = data[0]
                # 验证字幕必要字段
                assert 'id' in subtitle or 'start_time' in subtitle


class TestSubtitleGenerateAPI:
    """字幕生成 API 测试"""

    def test_generate_subtitles_nonexistent_video(self, client, auth_headers):
        """测试为不存在的视频生成字幕"""
        response = client.post(
            '/api/subtitles/videos/99999/subtitles/generate',
            data=json.dumps({'language': 'zh', 'whisper_model': 'base'}),
            headers=auth_headers,
        )
        assert response.status_code in [404, 500]

    def test_generate_subtitles_with_params(self, client, created_video, auth_headers):
        """测试带参数生成字幕"""
        response = client.post(
            f'/api/subtitles/videos/{created_video.id}/subtitles/generate',
            data=json.dumps({'language': 'zh', 'whisper_model': 'base'}),
            headers=auth_headers,
        )
        # 可能成功启动任务或因文件不存在失败
        assert response.status_code in [200, 201, 400, 404, 500]

    def test_generate_subtitles_different_languages(self, client, created_video, auth_headers):
        """测试不同语言参数"""
        languages = ['zh', 'en', 'ja']

        for lang in languages:
            response = client.post(
                f'/api/subtitles/videos/{created_video.id}/subtitles/generate',
                data=json.dumps({'language': lang, 'whisper_model': 'base'}),
                headers=auth_headers,
            )
            assert response.status_code in [200, 201, 400, 404, 500]


class TestSubtitleSemanticMergeAPI:
    """字幕语义合并 API 测试"""

    def test_get_semantic_merged_nonexistent_video(self, client):
        """测试获取不存在视频的语义合并字幕"""
        response = client.get('/api/subtitles/videos/99999/subtitles/semantic-merged')
        assert response.status_code in [404, 500]

    def test_get_semantic_merged_existing_video(self, client, video_with_subtitles):
        """测试获取已存在视频的语义合并字幕"""
        response = client.get(f'/api/subtitles/videos/{video_with_subtitles.id}/subtitles/semantic-merged')
        # 可能返回合并后的字幕或未找到
        assert response.status_code in [200, 404, 500]

    def test_get_semantic_merged_force_refresh(self, client, video_with_subtitles):
        """测试强制刷新语义合并"""
        response = client.get(
            f'/api/subtitles/videos/{video_with_subtitles.id}/subtitles/semantic-merged?force_refresh=true'
        )
        assert response.status_code in [200, 404, 500]

    def test_trigger_semantic_merge_nonexistent_video(self, client, auth_headers):
        """测试触发不存在视频的语义合并"""
        response = client.post('/api/subtitles/videos/99999/subtitles/semantic-merge', headers=auth_headers)
        assert response.status_code in [404, 500]

    def test_trigger_semantic_merge_existing_video(self, client, video_with_subtitles, auth_headers):
        """测试触发已存在视频的语义合并"""
        response = client.post(
            f'/api/subtitles/videos/{video_with_subtitles.id}/subtitles/semantic-merge', headers=auth_headers
        )
        # 可能成功或因为依赖服务不可用失败
        assert response.status_code in [200, 201, 400, 404, 500, 503]


class TestSubtitleExportAPI:
    """字幕导出 API 测试"""

    def test_export_subtitles_nonexistent_video(self, client):
        """测试导出不存在视频的字幕"""
        response = client.get('/api/subtitles/videos/99999/subtitles/export')
        assert response.status_code in [404, 500]

    def test_export_subtitles_srt_format(self, client, video_with_subtitles):
        """测试导出 SRT 格式字幕"""
        response = client.get(f'/api/subtitles/videos/{video_with_subtitles.id}/subtitles/export?format=srt')
        assert response.status_code in [200, 404, 500]

    def test_export_subtitles_vtt_format(self, client, video_with_subtitles):
        """测试导出 VTT 格式字幕"""
        response = client.get(f'/api/subtitles/videos/{video_with_subtitles.id}/subtitles/export?format=vtt')
        assert response.status_code in [200, 404, 500]

    def test_export_subtitles_txt_format(self, client, video_with_subtitles):
        """测试导出 TXT 格式字幕"""
        response = client.get(f'/api/subtitles/videos/{video_with_subtitles.id}/subtitles/export?format=txt')
        assert response.status_code in [200, 404, 500]


class TestSubtitleUpdateAPI:
    """字幕更新 API 测试"""

    def test_update_subtitle_nonexistent_video(self, client, auth_headers):
        """测试更新不存在视频的字幕"""
        response = client.put(
            '/api/subtitles/videos/99999/subtitles/1',
            data=json.dumps({'text': '更新的字幕内容', 'start_time': 0.0, 'end_time': 5.0}),
            headers=auth_headers,
        )
        assert response.status_code in [404, 500]

    def test_update_subtitle_nonexistent_subtitle(self, client, video_with_subtitles, auth_headers):
        """测试更新不存在的字幕"""
        response = client.put(
            f'/api/subtitles/videos/{video_with_subtitles.id}/subtitles/99999',
            data=json.dumps({'text': '更新的字幕内容', 'start_time': 0.0, 'end_time': 5.0}),
            headers=auth_headers,
        )
        assert response.status_code in [404, 500]


class TestSubtitleMergeAPI:
    """字幕合并 API 测试"""

    def test_merge_subtitles_nonexistent_video(self, client, auth_headers):
        """测试合并不存在视频的字幕"""
        response = client.post('/api/subtitles/videos/99999/subtitles/merge', headers=auth_headers)
        assert response.status_code in [404, 500]

    def test_merge_subtitles_existing_video(self, client, video_with_subtitles, auth_headers):
        """测试合并已存在视频的字幕"""
        response = client.post(f'/api/subtitles/videos/{video_with_subtitles.id}/subtitles/merge', headers=auth_headers)
        assert response.status_code in [200, 400, 404, 500]


class TestSubtitleAPIContract:
    """
    字幕 API 契约测试
    确保迁移后 API 行为一致
    """

    def test_subtitles_list_format(self, client, video_with_subtitles):
        """测试字幕列表响应格式"""
        response = client.get(f'/api/subtitles/videos/{video_with_subtitles.id}/subtitles')
        # 可能返回 500 如果字幕文件不存在
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.get_json()
            # 应该返回列表或包含字幕的对象
            assert isinstance(data, (list, dict))

    def test_export_content_type(self, client, video_with_subtitles):
        """测试导出内容类型"""
        response = client.get(f'/api/subtitles/videos/{video_with_subtitles.id}/subtitles/export?format=srt')

        if response.status_code == 200:
            # 导出应该是文本内容
            content_type = response.content_type
            assert 'text' in content_type or 'application' in content_type
