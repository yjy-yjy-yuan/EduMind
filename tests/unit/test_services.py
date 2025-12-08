"""
单元测试 - 服务层测试
测试 QA 系统、知识图谱、RAG 等核心服务

注意：这些测试使用 mock 来隔离外部依赖（如 LLM API、Ollama 服务）
"""

import os
import tempfile
from unittest.mock import Mock
from unittest.mock import patch

import numpy as np
import pytest


class TestQASystemInit:
    """QA 系统初始化测试"""

    def test_qa_system_init_success(self, app):
        """测试 QA 系统成功初始化"""
        with app.app_context():
            from app.utils.qa_utils import QASystem

            # 使用 mock 避免实际加载模型
            with patch('app.utils.qa_utils.SentenceTransformer') as mock_model:
                mock_model.return_value = Mock()
                qa = QASystem()
                assert qa.is_initialized is True

    def test_qa_system_init_failure(self, app):
        """测试 QA 系统初始化失败"""
        with app.app_context():
            from app.utils.qa_utils import QASystem

            with patch('app.utils.qa_utils.SentenceTransformer') as mock_model:
                mock_model.side_effect = Exception('Model load failed')
                qa = QASystem()
                assert qa.is_initialized is False


class TestQAKnowledgeBase:
    """QA 知识库测试"""

    @pytest.fixture
    def sample_srt_content(self):
        """示例 SRT 字幕内容"""
        return """1
00:00:00,000 --> 00:00:05,000
欢迎来到机器学习入门课程

2
00:00:05,000 --> 00:00:10,000
今天我们将学习什么是机器学习

3
00:00:10,000 --> 00:00:15,000
机器学习是人工智能的一个分支

4
00:00:15,000 --> 00:00:20,000
它使计算机能够从数据中学习
"""

    def test_create_knowledge_base_success(self, app, sample_srt_content):
        """测试成功创建知识库"""
        with app.app_context():
            from app.utils.qa_utils import QASystem

            # 创建临时字幕文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False, encoding='utf-8') as f:
                f.write(sample_srt_content)
                temp_path = f.name

            try:
                with patch('app.utils.qa_utils.SentenceTransformer') as mock_transformer:
                    # 模拟 encode 方法返回假的嵌入向量
                    mock_model = Mock()
                    mock_model.encode.return_value = np.random.rand(4, 384)
                    mock_transformer.return_value = mock_model

                    qa = QASystem()
                    result = qa.create_knowledge_base(temp_path)

                    assert result is True
                    assert len(qa.subtitles) > 0
            finally:
                os.remove(temp_path)

    def test_create_knowledge_base_file_not_found(self, app):
        """测试文件不存在时创建知识库"""
        with app.app_context():
            from app.utils.qa_utils import QASystem

            with patch('app.utils.qa_utils.SentenceTransformer') as mock_transformer:
                mock_transformer.return_value = Mock()
                qa = QASystem()
                result = qa.create_knowledge_base('/nonexistent/path.srt')
                assert result is False

    def test_create_knowledge_base_not_initialized(self, app):
        """测试未初始化时创建知识库"""
        with app.app_context():
            from app.utils.qa_utils import QASystem

            with patch('app.utils.qa_utils.SentenceTransformer') as mock_transformer:
                mock_transformer.side_effect = Exception('Init failed')
                qa = QASystem()
                result = qa.create_knowledge_base('/some/path.srt')
                assert result is False


class TestQASearch:
    """QA 搜索测试"""

    def test_search_similar_segments_empty(self, app):
        """测试空知识库搜索"""
        with app.app_context():
            from app.utils.qa_utils import QASystem

            with patch('app.utils.qa_utils.SentenceTransformer') as mock_transformer:
                mock_transformer.return_value = Mock()
                qa = QASystem()
                # 不创建知识库，直接搜索
                results = qa.search_similar_segments('测试问题')
                assert results == []

    def test_search_similar_segments_with_data(self, app):
        """测试有数据时的搜索"""
        with app.app_context():
            from app.utils.qa_utils import QASystem

            with patch('app.utils.qa_utils.SentenceTransformer') as mock_transformer:
                mock_model = Mock()
                # 模拟 encode 返回向量
                mock_model.encode.return_value = np.random.rand(384)
                mock_transformer.return_value = mock_model

                qa = QASystem()
                # 手动设置数据
                qa.subtitles = [
                    {'text': '机器学习入门', 'start_time': 0, 'end_time': 5},
                    {'text': '深度学习基础', 'start_time': 5, 'end_time': 10},
                ]
                qa.embeddings = np.random.rand(2, 384)

                results = qa.search_similar_segments('机器学习', top_k=2)
                # 应该返回结果（即使是随机的）
                assert isinstance(results, list)


class TestQAAnswer:
    """QA 回答生成测试"""

    def test_get_answer_without_api_key(self, app):
        """测试没有 API 密钥时获取答案"""
        with app.app_context():
            from app.utils.qa_utils import QASystem

            with patch('app.utils.qa_utils.SentenceTransformer') as mock_transformer:
                mock_transformer.return_value = Mock()
                qa = QASystem()

                # 自由模式不需要知识库
                with patch('app.utils.qa_utils.Generation') as mock_gen:
                    mock_response = Mock()
                    mock_response.status_code = 200
                    mock_response.output = Mock()
                    mock_response.output.text = '这是一个测试答案'
                    mock_gen.call.return_value = mock_response

                    # 使用默认 API 密钥
                    answer = qa.get_answer('什么是机器学习', mode='free')
                    assert answer is not None

    def test_get_answer_video_mode_no_knowledge_base(self, app):
        """测试视频模式但无知识库"""
        with app.app_context():
            from app.utils.qa_utils import QASystem

            with patch('app.utils.qa_utils.SentenceTransformer') as mock_transformer:
                mock_transformer.return_value = Mock()
                qa = QASystem()

                answer = qa.get_answer('这个视频讲什么', mode='video')
                assert '未初始化' in answer or '知识库' in answer


class TestOllamaService:
    """Ollama 服务测试"""

    def test_check_ollama_service_success(self, app):
        """测试 Ollama 服务检查成功"""
        with patch('app.utils.qa_utils.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {'models': [{'name': 'qwen3:8b'}]}
            mock_get.return_value = mock_response

            from app.utils.qa_utils import check_ollama_service

            result = check_ollama_service()
            assert result is True

    def test_check_ollama_service_failure(self, app):
        """测试 Ollama 服务检查失败"""
        with patch('app.utils.qa_utils.requests.get') as mock_get:
            mock_get.side_effect = Exception('Connection refused')

            from app.utils.qa_utils import check_ollama_service

            result = check_ollama_service()
            assert result is False


class TestSubtitleUtils:
    """字幕工具服务测试"""

    def test_format_timestamp_conversion(self, app):
        """测试时间戳格式转换"""
        from app.utils.subtitle_utils import format_timestamp

        # 测试各种时间
        assert format_timestamp(0, 'srt') == "00:00"
        assert format_timestamp(60, 'srt') == "01:00"
        assert format_timestamp(3661, 'srt') == "61:01"

    def test_validate_subtitle_time(self, app):
        """测试字幕时间验证"""
        from app.utils.subtitle_utils import validate_subtitle_time

        # 有效时间
        valid, error = validate_subtitle_time(0, 10)
        assert valid is True
        assert error is None

        # 无效时间
        valid, error = validate_subtitle_time(10, 5)
        assert valid is False
        assert error is not None


class TestVideoUtils:
    """视频工具服务测试"""

    def test_is_valid_url(self, app):
        """测试 URL 验证"""
        from app.utils.video_utils import is_valid_url

        assert is_valid_url("https://www.bilibili.com/video/BV123") is True
        assert is_valid_url("http://example.com") is True
        assert is_valid_url("not-a-url") is False
        assert is_valid_url("") is False

    def test_is_bilibili_url(self, app):
        """测试 B站 URL 识别"""
        from app.utils.video_utils import is_bilibili_url

        assert is_bilibili_url("https://www.bilibili.com/video/BV123") is True
        assert is_bilibili_url("https://youtube.com") is False

    def test_is_youtube_url(self, app):
        """测试 YouTube URL 识别"""
        from app.utils.video_utils import is_youtube_url

        assert is_youtube_url("https://www.youtube.com/watch?v=123") is True
        assert is_youtube_url("https://youtu.be/123") is True
        assert is_youtube_url("https://bilibili.com") is False

    def test_extract_bv_from_url(self, app):
        """测试从 URL 提取 BV 号"""
        from app.utils.video_utils import extract_bv_from_url

        bv = extract_bv_from_url("https://www.bilibili.com/video/BV1xx411c7XW")
        assert bv == "BV1xx411c7XW"


class TestSemanticUtils:
    """语义工具测试"""

    def test_semantic_merge_basic(self, app):
        """测试基本语义合并"""
        # 测试相邻相同文本合并
        from app.utils.subtitle_utils import merge_subtitles

        subtitles = [
            {'text': 'Hello', 'start_time': 0, 'end_time': 5},
            {'text': 'Hello', 'start_time': 5, 'end_time': 10},
        ]
        result = merge_subtitles(subtitles)
        assert len(result) == 1
        assert result[0]['start_time'] == 0
        assert result[0]['end_time'] == 10


class TestRAGSystem:
    """RAG 系统测试"""

    def test_rag_system_basic(self, app):
        """测试 RAG 系统基本功能"""
        # 这里可以添加 RAG 系统的测试
        # 由于 RAG 系统依赖于外部模型，使用 mock 进行测试
        pass


class TestServiceContractForMigration:
    """
    服务层契约测试
    确保迁移后服务行为一致
    """

    def test_qa_system_interface(self, app):
        """测试 QA 系统接口契约"""
        with app.app_context():
            from app.utils.qa_utils import QASystem

            with patch('app.utils.qa_utils.SentenceTransformer') as mock_transformer:
                mock_transformer.return_value = Mock()
                qa = QASystem()

                # 验证接口存在
                assert hasattr(qa, 'create_knowledge_base')
                assert hasattr(qa, 'search_similar_segments')
                assert hasattr(qa, 'get_answer')
                assert hasattr(qa, 'get_answer_stream')
                assert hasattr(qa, 'is_initialized')

    def test_subtitle_utils_interface(self, app):
        """测试字幕工具接口契约"""
        from app.utils import subtitle_utils

        # 验证接口存在
        assert hasattr(subtitle_utils, 'format_timestamp')
        assert hasattr(subtitle_utils, 'validate_subtitle_time')
        assert hasattr(subtitle_utils, 'merge_subtitles')
        assert hasattr(subtitle_utils, 'convert_to_srt')
        assert hasattr(subtitle_utils, 'convert_to_vtt')
        assert hasattr(subtitle_utils, 'convert_to_txt')

    def test_video_utils_interface(self, app):
        """测试视频工具接口契约"""
        from app.utils import video_utils

        # 验证接口存在
        assert hasattr(video_utils, 'is_valid_url')
        assert hasattr(video_utils, 'is_bilibili_url')
        assert hasattr(video_utils, 'is_youtube_url')
        assert hasattr(video_utils, 'extract_bv_from_url')


class TestKnowledgeGraphUtils:
    """知识图谱工具测试"""

    def test_knowledge_graph_utils_exists(self, app):
        """测试知识图谱工具模块存在"""
        try:
            from app.utils import knowledge_graph_utils

            assert knowledge_graph_utils is not None
        except ImportError:
            pytest.skip("知识图谱工具模块未实现")

    def test_neo4j_connection_mock(self, app):
        """测试 Neo4j 连接（使用 mock）"""
        # 使用 mock 避免实际连接 Neo4j
        with patch('neo4j.GraphDatabase.driver') as mock_driver:
            mock_driver.return_value = Mock()
            # 这里可以添加更多的 Neo4j 连接测试
            pass
