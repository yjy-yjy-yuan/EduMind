"""
冒烟测试 - 验证应用基本功能
确保应用能够启动并响应基本请求
"""

import pytest


class TestAppSmoke:
    """应用冒烟测试"""

    def test_app_exists(self, app):
        """测试应用实例存在"""
        assert app is not None

    def test_app_is_testing(self, app):
        """测试应用处于测试模式"""
        assert app.config['TESTING'] is True

    def test_client_exists(self, client):
        """测试客户端存在"""
        assert client is not None


class TestHealthCheck:
    """健康检查测试"""

    def test_root_endpoint(self, client):
        """测试根路由返回正确响应"""
        response = client.get('/')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'success'
        assert 'version' in data

    def test_health_endpoint(self, client):
        """测试健康检查端点"""
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'ok'


class TestCORSConfig:
    """CORS 配置测试"""

    def test_cors_headers_present(self, client):
        """测试 CORS 头存在"""
        response = client.options(
            '/', headers={'Origin': 'http://localhost:328', 'Access-Control-Request-Method': 'GET'}
        )
        # CORS 应该允许请求
        assert response.status_code in [200, 204]


class TestDatabaseConnection:
    """数据库连接测试"""

    def test_db_session_works(self, db_session):
        """测试数据库会话可用"""
        assert db_session is not None

    def test_can_query_database(self, app, db_session):
        """测试可以查询数据库"""
        from app.models import Video

        # 查询不应抛出异常
        videos = Video.query.all()
        assert isinstance(videos, list)
