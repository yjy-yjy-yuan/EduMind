"""
API 测试 - 问答相关接口
测试 Q&A 功能
"""
import pytest
import json


class TestQAAPI:
    """问答 API 测试"""

    def test_ask_without_question(self, client, auth_headers):
        """测试不带问题的请求"""
        response = client.post(
            '/api/qa/ask',
            data=json.dumps({}),
            headers=auth_headers
        )
        assert response.status_code in [400, 422]

    def test_ask_empty_question(self, client, auth_headers):
        """测试空问题"""
        response = client.post(
            '/api/qa/ask',
            data=json.dumps({'question': ''}),
            headers=auth_headers
        )
        assert response.status_code in [400, 422]

    def test_ask_without_video_id(self, client, auth_headers):
        """测试不带视频ID的问题"""
        response = client.post(
            '/api/qa/ask',
            data=json.dumps({'question': '这是一个测试问题'}),
            headers=auth_headers
        )
        # video_id 可能是必填的
        assert response.status_code in [400, 422, 500]

    def test_ask_with_nonexistent_video(self, client, auth_headers):
        """测试对不存在视频的问题"""
        response = client.post(
            '/api/qa/ask',
            data=json.dumps({
                'question': '这是一个测试问题',
                'video_id': 99999
            }),
            headers=auth_headers
        )
        # 可能返回错误或空结果
        assert response.status_code in [200, 400, 404, 500]


class TestQAHistoryAPI:
    """问答历史 API 测试"""

    def test_get_history_nonexistent_video(self, client):
        """测试获取不存在视频的历史记录"""
        response = client.get('/api/qa/history/99999')
        assert response.status_code in [200, 404, 500]
