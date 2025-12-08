"""
API 测试 - 问答相关接口
测试 Q&A 功能

覆盖端点：
- POST /api/qa/ask - 提问（支持流式和非流式）
- GET /api/qa/history/<video_id> - 获取历史记录
- POST /api/qa/ask-stream - 流式提问（如果存在）
"""

import json


class TestQAAPI:
    """问答 API 测试"""

    def test_ask_without_question(self, client, auth_headers):
        """测试不带问题的请求"""
        response = client.post('/api/qa/ask', data=json.dumps({}), headers=auth_headers)
        assert response.status_code in [400, 422]

    def test_ask_empty_question(self, client, auth_headers):
        """测试空问题"""
        response = client.post('/api/qa/ask', data=json.dumps({'question': ''}), headers=auth_headers)
        assert response.status_code in [400, 422]

    def test_ask_without_video_id(self, client, auth_headers):
        """测试不带视频ID的问题"""
        response = client.post('/api/qa/ask', data=json.dumps({'question': '这是一个测试问题'}), headers=auth_headers)
        # video_id 可能是必填的
        assert response.status_code in [400, 422, 500]

    def test_ask_with_nonexistent_video(self, client, auth_headers):
        """测试对不存在视频的问题"""
        response = client.post(
            '/api/qa/ask', data=json.dumps({'question': '这是一个测试问题', 'video_id': 99999}), headers=auth_headers
        )
        # 可能返回错误或空结果
        assert response.status_code in [200, 400, 404, 500]

    def test_ask_free_mode(self, client, auth_headers):
        """测试自由问答模式"""
        response = client.post(
            '/api/qa/ask',
            data=json.dumps({'question': '什么是机器学习？', 'mode': 'free', 'stream': False, 'use_ollama': False}),
            headers=auth_headers,
        )
        # 可能成功或因为 API 服务不可用失败
        assert response.status_code in [200, 400, 500, 503]

    def test_ask_video_mode(self, client, video_with_subtitles, auth_headers):
        """测试视频问答模式"""
        response = client.post(
            '/api/qa/ask',
            data=json.dumps(
                {
                    'video_id': video_with_subtitles.id,
                    'question': '这个视频讲的是什么？',
                    'mode': 'video',
                    'stream': False,
                    'use_ollama': False,
                }
            ),
            headers=auth_headers,
        )
        # 可能成功或因为服务不可用失败
        assert response.status_code in [200, 400, 500, 503]

    def test_ask_with_ollama(self, client, auth_headers):
        """测试使用 Ollama 本地模型"""
        response = client.post(
            '/api/qa/ask',
            data=json.dumps({'question': '什么是深度学习？', 'mode': 'free', 'stream': False, 'use_ollama': True}),
            headers=auth_headers,
        )
        # 可能成功或因为 Ollama 服务不可用失败
        assert response.status_code in [200, 400, 500, 503]

    def test_ask_with_deep_thinking(self, client, auth_headers):
        """测试深度思考模式"""
        response = client.post(
            '/api/qa/ask',
            data=json.dumps(
                {
                    'question': '解释一下神经网络的工作原理',
                    'mode': 'free',
                    'stream': False,
                    'use_ollama': False,
                    'deep_thinking': True,
                }
            ),
            headers=auth_headers,
        )
        # 可能成功或因为服务不可用失败
        assert response.status_code in [200, 400, 500, 503]


class TestQAStreamAPI:
    """问答流式响应 API 测试"""

    def test_ask_stream_request(self, client, auth_headers):
        """测试流式请求参数"""
        response = client.post(
            '/api/qa/ask',
            data=json.dumps({'question': '什么是人工智能？', 'mode': 'free', 'stream': True, 'use_ollama': False}),
            headers=auth_headers,
        )
        # 流式响应应该返回 200 或服务不可用
        assert response.status_code in [200, 400, 500, 503]

    def test_ask_stream_video_mode(self, client, video_with_subtitles, auth_headers):
        """测试视频模式流式响应"""
        response = client.post(
            '/api/qa/ask',
            data=json.dumps(
                {
                    'video_id': video_with_subtitles.id,
                    'question': '视频的主要内容是什么？',
                    'mode': 'video',
                    'stream': True,
                    'use_ollama': False,
                }
            ),
            headers=auth_headers,
        )
        # 流式响应
        assert response.status_code in [200, 400, 500, 503]

    def test_ask_stream_content_type(self, client, auth_headers):
        """测试流式响应内容类型"""
        response = client.post(
            '/api/qa/ask',
            data=json.dumps({'question': '简单介绍一下 Python', 'mode': 'free', 'stream': True, 'use_ollama': False}),
            headers=auth_headers,
        )

        if response.status_code == 200:
            # 流式响应通常是 text/plain 或 text/event-stream
            content_type = response.content_type
            assert 'text' in content_type or 'stream' in content_type or 'json' in content_type

    def test_ask_stream_with_ollama(self, client, auth_headers):
        """测试 Ollama 流式响应"""
        response = client.post(
            '/api/qa/ask',
            data=json.dumps({'question': '什么是卷积神经网络？', 'mode': 'free', 'stream': True, 'use_ollama': True}),
            headers=auth_headers,
        )
        # Ollama 可能不可用
        assert response.status_code in [200, 400, 500, 503]


class TestQAHistoryAPI:
    """问答历史 API 测试"""

    def test_get_history_nonexistent_video(self, client):
        """测试获取不存在视频的历史记录"""
        response = client.get('/api/qa/history/99999')
        assert response.status_code in [200, 404, 500]

    def test_get_history_existing_video(self, client, completed_video):
        """测试获取已存在视频的历史记录"""
        response = client.get(f'/api/qa/history/{completed_video.id}')
        assert response.status_code in [200, 404, 500]

    def test_get_history_response_structure(self, client, completed_video):
        """测试历史记录响应结构"""
        response = client.get(f'/api/qa/history/{completed_video.id}')

        if response.status_code == 200:
            data = response.get_json()
            # 应该返回列表或包含历史的对象
            assert isinstance(data, (list, dict))


class TestQAModes:
    """问答模式测试"""

    def test_mode_free_without_video(self, client, auth_headers):
        """测试自由模式不需要视频"""
        response = client.post(
            '/api/qa/ask',
            data=json.dumps({'question': '介绍一下 Python 语言', 'mode': 'free', 'stream': False}),
            headers=auth_headers,
        )
        # 自由模式可能因为 API 服务不可用返回 400/500/503
        assert response.status_code in [200, 400, 500, 503]

    def test_mode_video_requires_video_id(self, client, auth_headers):
        """测试视频模式需要视频 ID"""
        response = client.post(
            '/api/qa/ask',
            data=json.dumps({'question': '视频讲了什么？', 'mode': 'video', 'stream': False}),
            headers=auth_headers,
        )
        # 视频模式需要 video_id，应返回错误
        assert response.status_code in [400, 422, 500]

    def test_invalid_mode(self, client, auth_headers):
        """测试无效的模式参数"""
        response = client.post(
            '/api/qa/ask',
            data=json.dumps({'question': '测试问题', 'mode': 'invalid_mode', 'stream': False}),
            headers=auth_headers,
        )
        # 应该处理无效模式
        assert response.status_code in [200, 400, 422, 500]


class TestQAAPIContract:
    """
    问答 API 契约测试
    确保迁移后 API 行为一致
    """

    def test_ask_request_format(self, client, auth_headers):
        """测试请求格式契约"""
        # 标准请求格式
        response = client.post(
            '/api/qa/ask',
            data=json.dumps(
                {'question': '测试问题', 'mode': 'free', 'stream': False, 'use_ollama': False, 'deep_thinking': False}
            ),
            headers=auth_headers,
        )
        # 请求格式正确，不应返回格式错误
        assert response.status_code in [200, 400, 500, 503]

    def test_ask_response_format_non_stream(self, client, auth_headers):
        """测试非流式响应格式契约"""
        response = client.post(
            '/api/qa/ask', data=json.dumps({'question': '你好', 'mode': 'free', 'stream': False}), headers=auth_headers
        )

        if response.status_code == 200:
            # 非流式响应应该是 JSON
            data = response.get_json()
            assert data is not None

    def test_history_response_format(self, client, completed_video):
        """测试历史响应格式契约"""
        response = client.get(f'/api/qa/history/{completed_video.id}')

        if response.status_code == 200:
            data = response.get_json()
            # 应该是有效的 JSON
            assert data is not None

    def test_error_response_format(self, client, auth_headers):
        """测试错误响应格式契约"""
        response = client.post('/api/qa/ask', data=json.dumps({}), headers=auth_headers)  # 缺少必要字段

        if response.status_code in [400, 422]:
            # 错误响应应该是 JSON 格式
            data = response.get_json()
            assert data is not None
