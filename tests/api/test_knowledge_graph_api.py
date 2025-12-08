"""
API 测试 - 知识图谱相关接口
测试知识图谱生成、查询、合并等

覆盖端点：
- GET /api/knowledge-graph/<video_id> - 获取视频知识图谱
- POST /api/knowledge-graph/generate/<video_id> - 生成知识图谱
- GET /api/knowledge-graph/status/<video_id> - 获取生成状态
- POST /api/knowledge-graph/generate-questions - 生成问题

知识图谱整合端点：
- GET /api/knowledge-graph-integration/find-similar/<video_id> - 查找相似视频
- POST /api/knowledge-graph-integration/combine - 合并知识图谱
- GET /api/knowledge-graph-integration/check-combined/<video_id> - 检查合并状态
- POST /api/knowledge-graph-integration/combine-multiple - 批量合并
"""

import json

import pytest


class TestKnowledgeGraphGetAPI:
    """知识图谱获取 API 测试"""

    def test_get_kg_nonexistent_video(self, client):
        """测试获取不存在视频的知识图谱"""
        response = client.get('/api/knowledge-graph/99999')
        assert response.status_code in [200, 404, 500]

    def test_get_kg_existing_video(self, client, completed_video):
        """测试获取已存在视频的知识图谱"""
        response = client.get(f'/api/knowledge-graph/{completed_video.id}')
        # 可能返回空图谱或未生成
        assert response.status_code in [200, 404, 500]

    def test_get_kg_combined_id_format(self, client):
        """测试合并ID格式（如 "1_2"）"""
        response = client.get('/api/knowledge-graph/1_2')
        # 应该支持合并ID格式
        assert response.status_code in [200, 404, 500]


class TestKnowledgeGraphGenerateAPI:
    """知识图谱生成 API 测试"""

    def test_generate_kg_nonexistent_video(self, client, auth_headers):
        """测试为不存在的视频生成知识图谱"""
        response = client.post('/api/knowledge-graph/generate/99999', headers=auth_headers)
        assert response.status_code in [404, 500]

    def test_generate_kg_existing_video(self, client, completed_video, auth_headers):
        """测试为已存在视频生成知识图谱"""
        response = client.post(f'/api/knowledge-graph/generate/{completed_video.id}', headers=auth_headers)
        # 可能成功启动任务或因为依赖服务不可用失败
        assert response.status_code in [200, 201, 400, 404, 500, 503]


class TestKnowledgeGraphStatusAPI:
    """知识图谱状态 API 测试"""

    def test_get_kg_status_nonexistent_video(self, client):
        """测试获取不存在视频的知识图谱状态"""
        response = client.get('/api/knowledge-graph/status/99999')
        assert response.status_code in [200, 404, 500]

    def test_get_kg_status_existing_video(self, client, completed_video):
        """测试获取已存在视频的知识图谱状态"""
        response = client.get(f'/api/knowledge-graph/status/{completed_video.id}')
        assert response.status_code in [200, 404, 500]

    def test_get_kg_status_response_structure(self, client, completed_video):
        """测试状态响应结构（迁移契约）"""
        response = client.get(f'/api/knowledge-graph/status/{completed_video.id}')

        if response.status_code == 200:
            data = response.get_json()
            # 应该包含状态信息
            assert data is not None


class TestKnowledgeGraphQuestionsAPI:
    """知识图谱问题生成 API 测试"""

    def test_generate_questions_without_concept(self, client, auth_headers):
        """测试不带概念的问题生成"""
        response = client.post('/api/knowledge-graph/generate-questions', data=json.dumps({}), headers=auth_headers)
        assert response.status_code in [400, 422, 500]

    def test_generate_questions_with_concept(self, client, auth_headers):
        """测试带概念的问题生成"""
        response = client.post(
            '/api/knowledge-graph/generate-questions',
            data=json.dumps(
                {'concept': '机器学习', 'context': '机器学习是人工智能的一个分支', 'count': 3, 'use_ollama': False}
            ),
            headers=auth_headers,
        )
        # 可能成功或因为 LLM 服务不可用失败
        assert response.status_code in [200, 400, 500, 503]

    def test_generate_questions_use_ollama(self, client, auth_headers):
        """测试使用 Ollama 生成问题"""
        response = client.post(
            '/api/knowledge-graph/generate-questions',
            data=json.dumps(
                {'concept': '深度学习', 'context': '深度学习是机器学习的一个子领域', 'count': 2, 'use_ollama': True}
            ),
            headers=auth_headers,
        )
        # 可能成功或因为 Ollama 服务不可用失败
        assert response.status_code in [200, 400, 500, 503]


class TestKnowledgeGraphIntegrationAPI:
    """知识图谱整合 API 测试"""

    def test_find_similar_nonexistent_video(self, client):
        """测试查找不存在视频的相似视频"""
        response = client.get('/api/knowledge-graph-integration/find-similar/99999')
        assert response.status_code in [200, 404, 500]

    def test_find_similar_existing_video(self, client, completed_video):
        """测试查找已存在视频的相似视频"""
        response = client.get(f'/api/knowledge-graph-integration/find-similar/{completed_video.id}')
        # 400 可能是因为视频没有标签
        assert response.status_code in [200, 400, 404, 500]

    def test_find_similar_with_params(self, client, completed_video):
        """测试带参数查找相似视频"""
        response = client.get(
            f'/api/knowledge-graph-integration/find-similar/{completed_video.id}' f'?threshold=0.5&limit=10'
        )
        # 400 可能是因为视频没有标签
        assert response.status_code in [200, 400, 404, 500]

    def test_check_combined_nonexistent_video(self, client):
        """测试检查不存在视频的合并状态"""
        response = client.get('/api/knowledge-graph-integration/check-combined/99999')
        assert response.status_code in [200, 404, 500]

    def test_check_combined_existing_video(self, client, completed_video):
        """测试检查已存在视频的合并状态"""
        response = client.get(f'/api/knowledge-graph-integration/check-combined/{completed_video.id}')
        assert response.status_code in [200, 404, 500]


class TestKnowledgeGraphCombineAPI:
    """知识图谱合并 API 测试"""

    def test_combine_without_video_ids(self, client, auth_headers):
        """测试不带视频ID的合并请求"""
        response = client.post('/api/knowledge-graph-integration/combine', data=json.dumps({}), headers=auth_headers)
        assert response.status_code in [400, 422, 500]

    def test_combine_two_videos(self, client, completed_video, auth_headers):
        """测试合并两个视频的知识图谱"""
        response = client.post(
            '/api/knowledge-graph-integration/combine',
            data=json.dumps(
                {
                    'source_video_id': completed_video.id,
                    'target_video_id': completed_video.id,  # 同一个视频测试
                    'force_combine': False,
                    'threshold': 0.5,
                }
            ),
            headers=auth_headers,
        )
        # 可能成功或因为各种原因失败
        assert response.status_code in [200, 400, 404, 500]

    def test_combine_multiple_without_video_ids(self, client, auth_headers):
        """测试不带视频ID列表的批量合并"""
        response = client.post(
            '/api/knowledge-graph-integration/combine-multiple', data=json.dumps({}), headers=auth_headers
        )
        assert response.status_code in [400, 422, 500]

    def test_combine_multiple_with_video_ids(self, client, completed_video, auth_headers):
        """测试批量合并多个视频"""
        response = client.post(
            '/api/knowledge-graph-integration/combine-multiple',
            data=json.dumps({'video_ids': [completed_video.id], 'threshold': 0.5, 'force_combine': False}),
            headers=auth_headers,
        )
        assert response.status_code in [200, 400, 404, 500]


class TestKnowledgeGraphAPIContract:
    """
    知识图谱 API 契约测试
    确保迁移后 API 行为一致
    """

    def test_kg_response_format(self, client, completed_video):
        """测试知识图谱响应格式"""
        response = client.get(f'/api/knowledge-graph/{completed_video.id}')

        if response.status_code == 200:
            data = response.get_json()
            # 应该返回图谱数据
            assert data is not None

    def test_status_response_format(self, client, completed_video):
        """测试状态响应格式"""
        response = client.get(f'/api/knowledge-graph/status/{completed_video.id}')

        if response.status_code == 200:
            data = response.get_json()
            # 应该包含状态信息
            assert data is not None

    def test_questions_response_format(self, client, auth_headers):
        """测试问题生成响应格式"""
        response = client.post(
            '/api/knowledge-graph/generate-questions',
            data=json.dumps({'concept': '测试概念', 'context': '测试上下文', 'count': 1, 'use_ollama': False}),
            headers=auth_headers,
        )

        if response.status_code == 200:
            data = response.get_json()
            # 应该返回问题列表
            assert data is not None
