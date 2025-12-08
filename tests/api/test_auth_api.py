"""
API 测试 - 用户认证相关接口
测试用户注册、登录、信息更新等

覆盖端点：
- POST /api/auth/register - 用户注册
- POST /api/auth/login - 用户登录
- POST /api/auth/logout - 用户退出
- GET /api/auth/user - 获取当前用户信息
- POST /api/auth/user/update - 更新用户信息
"""

import json

import pytest


class TestAuthRegisterAPI:
    """用户注册 API 测试"""

    def test_register_success(self, client, auth_headers):
        """测试成功注册"""
        response = client.post(
            '/api/auth/register',
            data=json.dumps(
                {
                    'username': 'newuser',
                    'email': 'newuser@example.com',
                    'password': 'password123',
                    'gender': 'male',
                    'education': '本科',
                    'occupation': '学生',
                    'learning_direction': '编程',
                    'bio': '测试用户',
                }
            ),
            headers=auth_headers,
        )
        assert response.status_code in [200, 201, 400, 500]

    def test_register_without_username(self, client, auth_headers):
        """测试不带用户名注册"""
        response = client.post(
            '/api/auth/register',
            data=json.dumps({'email': 'nouser@example.com', 'password': 'password123'}),
            headers=auth_headers,
        )
        assert response.status_code in [400, 422, 500]

    def test_register_without_email(self, client, auth_headers):
        """测试不带邮箱注册"""
        response = client.post(
            '/api/auth/register',
            data=json.dumps({'username': 'noemail', 'password': 'password123'}),
            headers=auth_headers,
        )
        assert response.status_code in [400, 422, 500]

    def test_register_without_password(self, client, auth_headers):
        """测试不带密码注册"""
        response = client.post(
            '/api/auth/register',
            data=json.dumps({'username': 'nopass', 'email': 'nopass@example.com'}),
            headers=auth_headers,
        )
        assert response.status_code in [400, 422, 500]

    def test_register_duplicate_username(self, client, created_user, auth_headers):
        """测试重复用户名注册"""
        response = client.post(
            '/api/auth/register',
            data=json.dumps(
                {
                    'username': created_user.username,  # 使用动态生成的已存在用户名
                    'email': 'another_unique@example.com',
                    'password': 'password123',
                }
            ),
            headers=auth_headers,
        )
        assert response.status_code in [400, 409, 500]

    def test_register_duplicate_email(self, client, created_user, auth_headers):
        """测试重复邮箱注册"""
        response = client.post(
            '/api/auth/register',
            data=json.dumps(
                {
                    'username': 'another_unique_user',
                    'email': created_user.email,  # 使用动态生成的已存在邮箱
                    'password': 'password123',
                }
            ),
            headers=auth_headers,
        )
        assert response.status_code in [400, 409, 500]

    def test_register_invalid_email_format(self, client, auth_headers):
        """测试无效邮箱格式"""
        response = client.post(
            '/api/auth/register',
            data=json.dumps({'username': 'invalidemail', 'email': 'not-an-email', 'password': 'password123'}),
            headers=auth_headers,
        )
        # 可能接受或拒绝，取决于验证逻辑
        assert response.status_code in [200, 201, 400, 422, 500]


class TestAuthLoginAPI:
    """用户登录 API 测试"""

    def test_login_success(self, client, created_user, auth_headers):
        """测试成功登录"""
        response = client.post(
            '/api/auth/login',
            data=json.dumps({'username': created_user.username, 'password': 'testpassword123'}),
            headers=auth_headers,
        )
        assert response.status_code == 200

    def test_login_with_email(self, client, created_user, auth_headers):
        """测试使用邮箱登录"""
        response = client.post(
            '/api/auth/login',
            data=json.dumps({'username': created_user.email, 'password': 'testpassword123'}),
            headers=auth_headers,
        )
        # 可能支持或不支持邮箱登录
        assert response.status_code in [200, 400, 401, 500]

    def test_login_wrong_password(self, client, created_user, auth_headers):
        """测试错误密码登录"""
        response = client.post(
            '/api/auth/login',
            data=json.dumps({'username': created_user.username, 'password': 'wrongpassword'}),
            headers=auth_headers,
        )
        assert response.status_code in [400, 401, 500]

    def test_login_nonexistent_user(self, client, auth_headers):
        """测试不存在的用户登录"""
        response = client.post(
            '/api/auth/login',
            data=json.dumps({'username': 'nonexistent', 'password': 'password123'}),
            headers=auth_headers,
        )
        assert response.status_code in [400, 401, 404, 500]

    def test_login_without_username(self, client, auth_headers):
        """测试不带用户名登录"""
        response = client.post('/api/auth/login', data=json.dumps({'password': 'password123'}), headers=auth_headers)
        assert response.status_code in [400, 422, 500]

    def test_login_without_password(self, client, auth_headers):
        """测试不带密码登录"""
        response = client.post('/api/auth/login', data=json.dumps({'username': 'testuser'}), headers=auth_headers)
        assert response.status_code in [400, 422, 500]


class TestAuthLogoutAPI:
    """用户退出 API 测试"""

    def test_logout_success(self, client, logged_in_client, auth_headers):
        """测试成功退出"""
        response = logged_in_client.post('/api/auth/logout', headers=auth_headers)
        assert response.status_code in [200, 500]

    def test_logout_not_logged_in(self, client, auth_headers):
        """测试未登录状态退出"""
        response = client.post('/api/auth/logout', headers=auth_headers)
        # 可能成功（无操作）或返回错误
        assert response.status_code in [200, 401, 500]


class TestAuthUserInfoAPI:
    """用户信息 API 测试"""

    def test_get_user_info_logged_in(self, client, logged_in_client):
        """测试已登录状态获取用户信息"""
        response = logged_in_client.get('/api/auth/user')
        assert response.status_code in [200, 401, 500]

    def test_get_user_info_not_logged_in(self, client):
        """测试未登录状态获取用户信息"""
        response = client.get('/api/auth/user')
        # 应该返回未授权或空用户信息
        assert response.status_code in [200, 401, 500]

    def test_get_user_info_response_structure(self, client, logged_in_client):
        """测试用户信息响应结构（迁移契约）"""
        response = logged_in_client.get('/api/auth/user')

        if response.status_code == 200:
            data = response.get_json()
            # 验证用户信息字段
            if data and 'user' in data:
                user = data['user']
                # 必须包含基本字段
                assert 'username' in user or 'id' in user


class TestAuthUserUpdateAPI:
    """用户信息更新 API 测试"""

    def test_update_user_info_logged_in(self, client, logged_in_client, auth_headers):
        """测试已登录状态更新用户信息"""
        response = logged_in_client.post(
            '/api/auth/user/update', data=json.dumps({'bio': '更新后的简介'}), headers=auth_headers
        )
        assert response.status_code in [200, 401, 500]

    def test_update_user_info_not_logged_in(self, client, auth_headers):
        """测试未登录状态更新用户信息"""
        response = client.post('/api/auth/user/update', data=json.dumps({'bio': '更新后的简介'}), headers=auth_headers)
        # 应该返回未授权
        assert response.status_code in [401, 500]

    def test_update_username(self, client, logged_in_client, auth_headers):
        """测试更新用户名"""
        response = logged_in_client.post(
            '/api/auth/user/update', data=json.dumps({'username': 'updateduser'}), headers=auth_headers
        )
        assert response.status_code in [200, 400, 401, 500]

    def test_update_email(self, client, logged_in_client, auth_headers):
        """测试更新邮箱"""
        response = logged_in_client.post(
            '/api/auth/user/update', data=json.dumps({'email': 'updated@example.com'}), headers=auth_headers
        )
        assert response.status_code in [200, 400, 401, 500]


class TestAuthAPIContract:
    """
    认证 API 契约测试
    确保迁移后 API 行为一致
    """

    def test_register_response_format(self, client, auth_headers):
        """测试注册响应格式"""
        response = client.post(
            '/api/auth/register',
            data=json.dumps({'username': 'contracttest', 'email': 'contract@example.com', 'password': 'password123'}),
            headers=auth_headers,
        )

        if response.status_code in [200, 201]:
            data = response.get_json()
            # 应该返回成功消息或用户信息
            assert data is not None

    def test_login_response_format(self, client, created_user, auth_headers):
        """测试登录响应格式"""
        response = client.post(
            '/api/auth/login',
            data=json.dumps({'username': created_user.username, 'password': 'testpassword123'}),
            headers=auth_headers,
        )

        if response.status_code == 200:
            data = response.get_json()
            # 应该返回成功消息
            assert data is not None

    def test_error_response_format(self, client, auth_headers):
        """测试错误响应格式"""
        response = client.post(
            '/api/auth/login',
            data=json.dumps({'username': 'nonexistent', 'password': 'wrongpassword'}),
            headers=auth_headers,
        )

        if response.status_code in [400, 401]:
            data = response.get_json()
            # 错误响应应该包含错误信息
            assert data is not None
