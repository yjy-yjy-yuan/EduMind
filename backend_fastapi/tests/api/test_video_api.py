"""API 测试 - 视频接口"""

import io
import os

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

    def test_stream_video_file_supports_full_content(self, client, db, sample_video, tmp_path):
        """测试视频全量流接口"""
        content = b"0123456789abcdef"
        video_path = tmp_path / "stream-full.mp4"
        video_path.write_bytes(content)

        sample_video.filepath = str(video_path)
        sample_video.filename = "stream-full.mp4"
        db.commit()

        response = client.get(f"/api/videos/{sample_video.id}/stream")
        assert response.status_code == 200
        assert response.content == content
        assert response.headers["accept-ranges"] == "bytes"
        assert response.headers["content-length"] == str(len(content))

    def test_stream_video_file_supports_range_requests(self, client, db, sample_video, tmp_path):
        """测试视频流接口支持 Range，便于 iOS 播放器拖动和断点加载"""
        content = b"0123456789abcdef"
        video_path = tmp_path / "stream-range.mp4"
        video_path.write_bytes(content)

        sample_video.filepath = str(video_path)
        sample_video.filename = "stream-range.mp4"
        db.commit()

        response = client.get(
            f"/api/videos/{sample_video.id}/stream",
            headers={"Range": "bytes=2-7"},
        )
        assert response.status_code == 206
        assert response.content == content[2:8]
        assert response.headers["accept-ranges"] == "bytes"
        assert response.headers["content-range"] == f"bytes 2-7/{len(content)}"
        assert response.headers["content-length"] == "6"

    def test_upload_video_file(self, client, db, tmp_path, monkeypatch):
        """测试本地视频上传"""
        from app.core.config import settings
        from app.models.video import Video

        monkeypatch.setattr(settings, "UPLOAD_FOLDER", str(tmp_path / "uploads"))
        monkeypatch.setattr(settings, "TEMP_FOLDER", str(tmp_path / "temp"))
        monkeypatch.setattr(settings, "WHISPER_MODEL", "turbo")

        submitted = {}

        def fake_submit_task(task_func, *args, **kwargs):
            submitted["name"] = task_func.__name__
            submitted["args"] = args
            submitted["kwargs"] = kwargs
            return None

        monkeypatch.setattr("app.core.executor.submit_task", fake_submit_task)

        response = client.post(
            "/api/videos/upload",
            files={"file": ("lesson.mp4", io.BytesIO(b"fake-video-content"), "video/mp4")},
        )
        assert response.status_code == 200

        payload = response.json()
        assert payload["status"] == "pending"
        assert payload["duplicate"] is False
        assert payload["data"]["filename"] == "local-lesson.mp4"
        assert os.path.exists(payload["data"]["filepath"])
        assert payload["message"] == "视频上传成功，已开始后台处理"

        videos = db.query(Video).all()
        assert len(videos) == 1
        assert videos[0].status.value == "pending"
        assert videos[0].current_step == "已提交，等待处理"
        assert submitted["name"] == "process_video_task"
        assert submitted["args"][0] == videos[0].id

    def test_upload_video_file_duplicate(self, client, db, tmp_path, monkeypatch):
        """测试重复上传同一视频"""
        from app.core.config import settings
        from app.models.video import Video

        monkeypatch.setattr(settings, "UPLOAD_FOLDER", str(tmp_path / "uploads"))
        monkeypatch.setattr(settings, "TEMP_FOLDER", str(tmp_path / "temp"))

        files = {"file": ("duplicate.mp4", io.BytesIO(b"same-video"), "video/mp4")}
        first = client.post("/api/videos/upload", files=files)
        assert first.status_code == 200

        second = client.post(
            "/api/videos/upload",
            files={"file": ("duplicate.mp4", io.BytesIO(b"same-video"), "video/mp4")},
        )
        assert second.status_code == 200

        payload = second.json()
        assert payload["duplicate"] is True
        assert payload["message"] == "视频已存在"
        assert db.query(Video).count() == 1

    def test_upload_video_invalid_extension(self, client):
        """测试上传不支持的文件类型"""
        response = client.post(
            "/api/videos/upload",
            files={"file": ("document.txt", io.BytesIO(b"not-a-video"), "text/plain")},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "不支持的文件类型"

    def test_upload_video_url_creates_downloading_record(self, client, db, monkeypatch):
        """测试链接上传会立即创建下载中记录"""
        from app.models.video import Video

        submitted = {}

        def fake_submit_task(task_func, *args, **kwargs):
            submitted["name"] = task_func.__name__
            submitted["args"] = args
            submitted["kwargs"] = kwargs
            return None

        monkeypatch.setattr("app.core.executor.submit_task", fake_submit_task)

        response = client.post(
            "/api/videos/upload-url",
            json={"url": "https://www.bilibili.com/video/BV1xx411c7mD"},
        )
        assert response.status_code == 200

        payload = response.json()
        assert payload["status"] == "downloading"
        assert payload["duplicate"] is False
        assert payload["data"]["status"] == "downloading"

        video = db.query(Video).filter(Video.id == payload["id"]).first()
        assert video is not None
        assert video.status.value == "downloading"
        assert video.current_step == "已提交，等待下载"
        assert submitted["name"] == "download_video_from_url_task"
        assert submitted["args"][0] == video.id


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
