"""API 测试 - 视频接口"""

import io

import pytest


@pytest.mark.api
class TestVideoAPI:
    """视频 API 测试"""

    def test_get_videos_empty(self, client):
        """测试获取空视频列表"""
        response = client.get("/api/videos/list")
        assert response.status_code == 200
        data = response.json()
        assert data["videos"] == []

    def test_get_videos_with_data(self, client, sample_video):
        """测试获取视频列表"""
        response = client.get("/api/videos/list")
        assert response.status_code == 200
        data = response.json()
        assert len(data["videos"]) == 1
        assert data["videos"][0]["filename"] == "test_video.mp4"

    def test_get_video_by_id(self, client, sample_video):
        """测试通过 ID 获取视频"""
        response = client.get(f"/api/videos/{sample_video.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_video.id

    def test_get_video_not_found(self, client):
        """测试获取不存在的视频"""
        response = client.get("/api/videos/99999")
        assert response.status_code == 404

    def test_delete_video(self, client, sample_video):
        """测试删除视频"""
        response = client.delete(f"/api/videos/{sample_video.id}/delete")
        assert response.status_code == 200

        # 验证删除
        response = client.get(f"/api/videos/{sample_video.id}")
        assert response.status_code == 404

    def test_get_video_status(self, client, sample_video):
        """测试获取视频处理状态"""
        response = client.get(f"/api/videos/{sample_video.id}/status")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "progress" in data


@pytest.mark.api
class TestNoteAPI:
    """笔记 API 测试"""

    def test_get_notes_empty(self, client):
        """测试获取空笔记列表"""
        response = client.get("/api/notes/notes")
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []

    def test_create_note(self, client, sample_video):
        """测试创建笔记"""
        response = client.post(
            "/api/notes/notes",
            json={
                "title": "新笔记",
                "content": "笔记内容",
                "video_id": sample_video.id,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["title"] == "新笔记"

    def test_create_note_without_title(self, client):
        """测试创建没有标题的笔记"""
        response = client.post(
            "/api/notes/notes",
            json={
                "title": "",
                "content": "内容",
            },
        )
        # FastAPI 返回 422 表示验证错误
        assert response.status_code in [400, 422]

    def test_get_note_by_id(self, client, sample_note):
        """测试通过 ID 获取笔记"""
        response = client.get(f"/api/notes/notes/{sample_note.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["id"] == sample_note.id

    def test_update_note(self, client, sample_note):
        """测试更新笔记"""
        response = client.put(
            f"/api/notes/notes/{sample_note.id}",
            json={
                "title": "更新后的标题",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["title"] == "更新后的标题"

    def test_delete_note(self, client, sample_note):
        """测试删除笔记"""
        response = client.delete(f"/api/notes/notes/{sample_note.id}")
        assert response.status_code == 200

        # 验证删除
        response = client.get(f"/api/notes/notes/{sample_note.id}")
        assert response.status_code == 404


@pytest.mark.api
class TestAuthAPI:
    """认证 API 测试"""

    def test_register_user(self, client):
        """测试用户注册"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["username"] == "newuser"

    def test_register_duplicate_username(self, client, sample_user):
        """测试重复用户名注册"""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "testuser",  # 已存在的用户名
                "email": "other@example.com",
                "password": "password123",
            },
        )
        assert response.status_code == 400

    def test_login_success(self, client, sample_user):
        """测试登录成功"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "password123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "user" in data

    def test_login_wrong_password(self, client, sample_user):
        """测试密码错误登录"""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401
