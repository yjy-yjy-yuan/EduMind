"""API 测试 - 推荐接口。"""

import pytest


@pytest.mark.api
class TestRecommendationAPI:
    """推荐 API 测试。"""

    def test_get_recommendation_scenes(self, client):
        """测试获取推荐场景列表。"""
        response = client.get("/api/recommendations/scenes")
        assert response.status_code == 200

        payload = response.json()
        assert payload["message"] == "获取推荐场景成功"
        assert {item["value"] for item in payload["scenes"]} >= {"home", "continue", "review", "related"}

    def test_home_recommendations_prioritize_active_video(self, client, db, sample_user):
        """首页推荐优先返回当前需要继续跟进的处理中视频。"""
        from app.models.video import Video
        from app.models.video import VideoStatus
        from app.utils.auth_token import build_auth_token

        sample_user.learning_direction = "数学 导数"
        db.commit()

        processing_video = Video(
            title="导数应用串讲",
            filename="processing.mp4",
            filepath="/tmp/processing.mp4",
            status=VideoStatus.PROCESSING,
            process_progress=56,
            current_step="语音识别中",
            summary="",
            tags='["导数","真题"]',
        )
        completed_video = Video(
            title="英语写作结构梳理",
            filename="english.mp4",
            filepath="/tmp/english.mp4",
            status=VideoStatus.COMPLETED,
            process_progress=100,
            current_step="分析完成",
            summary="总结英语写作常见结构。",
            tags='["英语","写作"]',
        )
        related_interest_video = Video(
            title="函数极限与导数复盘",
            filename="math-review.mp4",
            filepath="/tmp/math-review.mp4",
            status=VideoStatus.COMPLETED,
            process_progress=100,
            current_step="分析完成",
            summary="围绕极限、导数定义与常见求导法则做复盘。",
            tags='["导数","极限","函数"]',
        )
        db.add_all([processing_video, completed_video, related_interest_video])
        db.commit()

        response = client.get(
            "/api/recommendations/videos",
            params={"scene": "home", "limit": 3},
            headers={"Authorization": f"Bearer {build_auth_token(sample_user.id)}"},
        )
        assert response.status_code == 200

        payload = response.json()
        assert payload["scene"] == "home"
        assert payload["strategy"] == "video_status_interest_v1"
        assert payload["personalized"] is True
        assert len(payload["items"]) == 3
        assert payload["items"][0]["id"] == processing_video.id
        assert payload["items"][0]["reason_code"] == "continue"
        assert any(item["reason_code"] in {"interest", "continue"} for item in payload["items"])

    def test_related_recommendations_require_seed_video(self, client):
        """相关推荐场景必须传 seed_video_id。"""
        response = client.get("/api/recommendations/videos", params={"scene": "related"})
        assert response.status_code == 422
        assert response.json()["detail"] == "scene=related 时必须传入 seed_video_id"

    def test_related_recommendations_rank_overlap_video_first(self, client, db):
        """相关推荐优先返回与 seed 视频主题重合度更高的视频。"""
        from app.models.video import Video
        from app.models.video import VideoStatus

        seed_video = Video(
            title="导数与单调性",
            filename="seed.mp4",
            filepath="/tmp/seed.mp4",
            status=VideoStatus.COMPLETED,
            process_progress=100,
            current_step="分析完成",
            summary="讲解导数在函数单调性判断中的应用。",
            tags='["导数","单调性","函数"]',
        )
        best_match = Video(
            title="函数单调性题型精讲",
            filename="best-match.mp4",
            filepath="/tmp/best-match.mp4",
            status=VideoStatus.COMPLETED,
            process_progress=100,
            current_step="分析完成",
            summary="围绕函数、导数和单调性题型做系统复盘。",
            tags='["导数","函数","题型"]',
        )
        other_video = Video(
            title="英语听力技巧",
            filename="english-listening.mp4",
            filepath="/tmp/english-listening.mp4",
            status=VideoStatus.COMPLETED,
            process_progress=100,
            current_step="分析完成",
            summary="总结英语听力中的关键信号词。",
            tags='["英语","听力"]',
        )
        db.add_all([seed_video, best_match, other_video])
        db.commit()

        response = client.get(
            "/api/recommendations/videos",
            params={"scene": "related", "seed_video_id": seed_video.id, "limit": 2},
        )
        assert response.status_code == 200

        payload = response.json()
        assert payload["seed_video_id"] == seed_video.id
        assert payload["seed_video_title"] == seed_video.title
        assert payload["items"][0]["id"] == best_match.id
        assert payload["items"][0]["reason_code"] == "related"
        assert all(item["id"] != seed_video.id for item in payload["items"])
