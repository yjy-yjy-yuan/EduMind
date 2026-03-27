"""API 测试 - 推荐接口。"""

import pytest
from app.services import video_recommendation_service as recommendation_service
from app.services.external_candidate_service import ExternalCandidate
from app.services.external_candidate_service import ExternalCandidateFetchReport
from app.services.external_candidate_service import ExternalProviderFetchSummary


def fake_fetch_external_candidates_report(*args, **kwargs):
    """返回推荐接口测试用的站外候选假数据。"""
    return ExternalCandidateFetchReport(
        candidates=[
            ExternalCandidate(
                id="youtube:abc123",
                provider="youtube",
                source_label="YouTube",
                title="YouTube · Calculus Review",
                external_url="https://www.youtube.com/watch?v=abc123",
                summary="适合配合当前数学主题继续学习。",
                tags=["数学", "导数"],
                subject="数学",
                primary_topic="导数",
                cluster_key="数学::导数",
            )
        ],
        providers=[
            ExternalProviderFetchSummary(
                provider="youtube",
                source_label="YouTube",
                status="success",
                candidate_count=1,
                latency_ms=145,
            ),
            ExternalProviderFetchSummary(
                provider="icourse163",
                source_label="中国大学慕课",
                status="failed",
                candidate_count=0,
                error_message="search failed",
                latency_ms=620,
            ),
        ],
    )


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
        assert payload["items"][0]["tags"][0] == "数学"
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
        assert payload["items"][0]["tags"][0] == "数学"
        assert all(item["id"] != seed_video.id for item in payload["items"])

    def test_related_recommendations_infer_subject_from_title_only(self, client, db):
        """即使原始标签为空，相关推荐也应能根据科目归一返回同科目内容。"""
        from app.models.video import Video
        from app.models.video import VideoStatus

        seed_video = Video(
            title="牛顿第二定律串讲",
            filename="seed-physics.mp4",
            filepath="/tmp/seed-physics.mp4",
            status=VideoStatus.COMPLETED,
            process_progress=100,
            current_step="分析完成",
            summary="高中物理受力分析与牛顿第二定律综合应用。",
            tags=None,
        )
        physics_match = Video(
            title="受力分析复习",
            filename="physics-match.mp4",
            filepath="/tmp/physics-match.mp4",
            status=VideoStatus.COMPLETED,
            process_progress=100,
            current_step="分析完成",
            summary="物理力学里常见的受力分析步骤整理。",
            tags=None,
        )
        english_video = Video(
            title="英语听力技巧",
            filename="english-listening.mp4",
            filepath="/tmp/english-listening.mp4",
            status=VideoStatus.COMPLETED,
            process_progress=100,
            current_step="分析完成",
            summary="整理英语听力高频信号词。",
            tags='["英语听力"]',
        )
        db.add_all([seed_video, physics_match, english_video])
        db.commit()

        response = client.get(
            "/api/recommendations/videos",
            params={"scene": "related", "seed_video_id": seed_video.id, "limit": 2},
        )
        assert response.status_code == 200

        payload = response.json()
        assert payload["items"][0]["id"] == physics_match.id
        assert payload["items"][0]["tags"][0] == "物理"
        assert payload["items"][0]["reason_code"] in {"related", "subject"}

    def test_home_recommendations_include_external_candidates(self, client, db, monkeypatch):
        """推荐接口应支持在返回中混入站外候选元数据。"""
        from app.models.video import Video
        from app.models.video import VideoStatus

        internal_video = Video(
            title="高数导数专题",
            filename="math.mp4",
            filepath="/tmp/math.mp4",
            status=VideoStatus.COMPLETED,
            process_progress=100,
            current_step="分析完成",
            summary="围绕导数定义与函数单调性做复盘。",
            tags='["导数","函数"]',
        )
        db.add(internal_video)
        db.commit()

        monkeypatch.setattr(
            recommendation_service,
            "fetch_external_candidates_report",
            fake_fetch_external_candidates_report,
        )

        response = client.get(
            "/api/recommendations/videos",
            params={"scene": "home", "limit": 4, "include_external": True},
        )
        assert response.status_code == 200

        payload = response.json()
        assert payload["strategy"] == "video_status_interest_external_v2"
        assert any(item["id"] == internal_video.id for item in payload["items"])
        assert payload["internal_item_count"] == 1
        assert payload["external_item_count"] == 1
        assert payload["external_failed_provider_count"] == 1
        assert payload["external_fetch_failed"] is True
        assert payload["external_query"]["subject"] == "数学"
        assert any(item["provider"] == "internal" for item in payload["sources"])
        assert any(item["provider"] == "youtube" for item in payload["sources"])
        assert any(
            item["provider"] == "icourse163" and item["status"] == "failed" for item in payload["external_providers"]
        )
        external_item = next(item for item in payload["items"] if item.get("is_external") is True)
        assert external_item["source_label"] == "YouTube"
        assert external_item["external_url"] == "https://www.youtube.com/watch?v=abc123"
        assert external_item["item_type"] == "external_candidate"
        assert external_item["can_import"] is True
        assert external_item["action_api"] == "/api/recommendations/import-external"
        assert external_item["action_method"] == "POST"
        assert external_item["action_type"] == "import_external_url"
        assert external_item["action_target"].startswith("/upload?mode=url&url=")

    def test_import_external_recommendation_creates_downloading_record(self, client, db, monkeypatch):
        """推荐候选应能直接走后端链接下载入库链路。"""
        from app.models.video import Video

        submitted = {}

        def fake_submit_task(task_func, *args, **kwargs):
            submitted["name"] = task_func.__name__
            submitted["args"] = args
            submitted["kwargs"] = kwargs
            return None

        monkeypatch.setattr("app.core.executor.submit_task", fake_submit_task)

        response = client.post(
            "/api/recommendations/import-external",
            json={
                "url": "https://www.bilibili.com/video/BV1xx411c7mD",
                "title": "B站·导数与函数单调性综合串讲",
                "summary": "适合配合当前数学主题继续学习。",
                "tags": ["数学", "导数", "函数"],
                "model": "small",
            },
        )
        assert response.status_code == 200

        payload = response.json()
        assert payload["status"] == "downloading"
        assert payload["duplicate"] is False
        assert payload["data"]["title"] == "B站·导数与函数单调性综合串讲"
        assert payload["data"]["summary"] == "适合配合当前数学主题继续学习。"
        assert payload["data"]["tags"][0] == "数学"

        video = db.query(Video).filter(Video.id == payload["id"]).first()
        assert video is not None
        assert video.url == "https://www.bilibili.com/video/BV1xx411c7mD"
        assert video.status.value == "downloading"
        assert submitted["name"] == "download_video_from_url_task"
        assert submitted["args"][0] == video.id
        assert submitted["kwargs"]["model"] == "small"
