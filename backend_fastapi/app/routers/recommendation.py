"""视频推荐路由。"""

import time
import uuid
from typing import Optional
from urllib.parse import urlparse

from app.analytics.pipeline import get_telemetry
from app.analytics.schema import AnalyticsEvent
from app.analytics.schema import AnalyticsStatus
from app.core.config import settings
from app.core.database import get_db
from app.models.video import Video
from app.schemas.recommendation import RecommendationSceneListResponse
from app.schemas.recommendation import VideoRecommendationResponse
from app.schemas.video import VideoUploadResponse
from app.schemas.video import VideoUploadURL
from app.services.video_api_service import build_processing_options
from app.services.video_api_service import serialize_video
from app.services.video_recommendation_service import SCENE_MAP
from app.services.video_recommendation_service import list_recommendation_scenes
from app.services.video_recommendation_service import load_candidate_videos_for_recommendation
from app.services.video_recommendation_service import normalize_scene
from app.services.video_recommendation_service import recommend_videos
from app.services.video_url_import_service import import_remote_video_from_url
from app.utils.auth_deps import resolve_user_from_request
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi import Response
from sqlalchemy.orm import Session

router = APIRouter()


def _resolve_trace_id(request: Request) -> str:
    raw = request.headers.get("X-Trace-Id") or request.headers.get("X-Request-Id")
    if raw and str(raw).strip():
        return str(raw).strip()[:128]
    return str(uuid.uuid4())


def _attach_trace_headers(response: Response, trace_id: str) -> None:
    response.headers["X-Trace-Id"] = trace_id
    response.headers["X-Request-Id"] = trace_id


def _emit_recommendation_event(
    *,
    trace_id: str,
    event_type: str,
    status: str,
    latency_ms: Optional[float] = None,
    metadata: Optional[dict] = None,
) -> None:
    if not getattr(settings, "RECOMMENDATION_TELEMETRY_ENABLED", True):
        return
    tid = (trace_id or "").strip() or settings.ANALYTICS_TRACE_ID_PLACEHOLDER
    try:
        get_telemetry().emit(
            AnalyticsEvent(
                event_type=event_type,
                trace_id=tid[:128],
                module="recommendation",
                status=status,
                latency_ms=latency_ms,
                metadata=dict(metadata or {}),
            )
        )
    except Exception:
        return


def parse_exclude_ids(raw_value: Optional[str]) -> set[int]:
    """解析逗号分隔的排除视频 ID 列表。"""
    values = set()
    for chunk in str(raw_value or "").split(","):
        text = chunk.strip()
        if text.isdigit():
            values.add(int(text))
    return values


def _url_host(url: str) -> str:
    """Extract hostname for telemetry (not a truncated URL)."""
    try:
        host = urlparse(url or "").hostname or ""
    except ValueError:
        host = ""
    return (host or "")[:120]


@router.get("/scenes", response_model=RecommendationSceneListResponse)
async def get_recommendation_scenes(request: Request, response: Response):
    """返回前端可直接渲染的推荐场景配置。"""
    trace_id = _resolve_trace_id(request)
    _attach_trace_headers(response, trace_id)
    t0 = time.perf_counter()
    scenes = list_recommendation_scenes()
    latency_ms = (time.perf_counter() - t0) * 1000.0
    _emit_recommendation_event(
        trace_id=trace_id,
        event_type="recommendation_scenes_served",
        status=AnalyticsStatus.OK.value,
        latency_ms=latency_ms,
        metadata={"scene_count": len(scenes)},
    )
    return {"message": "获取推荐场景成功", "scenes": scenes}


@router.get("/videos", response_model=VideoRecommendationResponse)
async def get_video_recommendations(
    request: Request,
    response: Response,
    scene: str = Query(default="home", description="推荐场景：home/continue/review/related"),
    limit: int = Query(default=4, ge=1, le=12, description="返回条数"),
    include_external: bool = Query(
        default=settings.RECOMMENDATION_INCLUDE_EXTERNAL_DEFAULT,
        description="是否附带站外候选；服务端默认由 RECOMMENDATION_INCLUDE_EXTERNAL_DEFAULT 控制",
    ),
    coach: bool = Query(default=False, description="是否返回 coach_summary 模板说明"),
    seed_video_id: Optional[int] = Query(default=None, description="相关推荐的种子视频 ID"),
    exclude_video_ids: Optional[str] = Query(default=None, description="排除的视频 ID，逗号分隔"),
    user_id: Optional[int] = Query(default=None, description="兼容旧链路的用户 ID"),
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    """返回推荐视频列表。"""
    trace_id = _resolve_trace_id(request)
    _attach_trace_headers(response, trace_id)
    t0 = time.perf_counter()
    normalized_scene = normalize_scene(scene)
    scene_option = SCENE_MAP[normalized_scene]

    _emit_recommendation_event(
        trace_id=trace_id,
        event_type="recommendation_request_received",
        status=AnalyticsStatus.OK.value,
        metadata={"scene": normalized_scene, "limit": limit, "include_external": include_external},
    )

    if scene_option["requires_seed"] and not seed_video_id:
        raise HTTPException(status_code=422, detail="scene=related 时必须传入 seed_video_id")

    seed_video = None
    if seed_video_id is not None:
        seed_video = db.query(Video).filter(Video.id == seed_video_id).first()
        if seed_video is None:
            raise HTTPException(status_code=404, detail="seed 视频不存在")

    user = resolve_user_from_request(db, user_id, authorization)
    max_scan = int(settings.RECOMMENDATION_MAX_CANDIDATES_SCAN)
    videos = load_candidate_videos_for_recommendation(db, seed_video, max_scan)
    payload = recommend_videos(
        videos=videos,
        scene=normalized_scene,
        limit=limit,
        seed_video=seed_video,
        user=user,
        exclude_ids=parse_exclude_ids(exclude_video_ids),
        include_external=include_external,
        coach=coach,
    )
    payload["message"] = "获取推荐视频成功"
    latency_ms = (time.perf_counter() - t0) * 1000.0
    _emit_recommendation_event(
        trace_id=trace_id,
        event_type="recommendation_ranking_completed",
        status=AnalyticsStatus.OK.value,
        latency_ms=latency_ms,
        metadata={
            "scene": payload.get("scene"),
            "strategy": payload.get("strategy"),
            "personalized": payload.get("personalized"),
            "fallback_used": payload.get("fallback_used"),
            "internal_item_count": payload.get("internal_item_count"),
            "external_item_count": payload.get("external_item_count"),
            "contract_version": payload.get("contract_version"),
        },
    )
    if payload.get("fallback_used"):
        _emit_recommendation_event(
            trace_id=trace_id,
            event_type="recommendation_fallback_used",
            status=AnalyticsStatus.DEGRADED.value,
            latency_ms=None,
            metadata={"scene": payload.get("scene")},
        )
    if include_external:
        if payload.get("external_fetch_failed"):
            _emit_recommendation_event(
                trace_id=trace_id,
                event_type="recommendation_external_fetch_failed",
                status=AnalyticsStatus.DEGRADED.value,
                latency_ms=None,
                metadata={
                    "external_failed_provider_count": payload.get("external_failed_provider_count"),
                },
            )
        else:
            _emit_recommendation_event(
                trace_id=trace_id,
                event_type="recommendation_external_fetch_completed",
                status=AnalyticsStatus.OK.value,
                latency_ms=None,
                metadata={"external_item_count": payload.get("external_item_count")},
            )
    return payload


@router.post("/import-external", response_model=VideoUploadResponse)
async def import_external_recommendation(
    request: Request,
    response: Response,
    data: VideoUploadURL,
    user_id: Optional[int] = Query(default=None, description="兼容旧链路的用户 ID"),
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    """将推荐页中的站外候选直接提交到现有链接下载入库链路。"""
    trace_id = _resolve_trace_id(request)
    _attach_trace_headers(response, trace_id)
    t0 = time.perf_counter()
    user = resolve_user_from_request(db, user_id, authorization)
    if user is None:
        raise HTTPException(status_code=401, detail="请先登录后再导入站外视频")
    _emit_recommendation_event(
        trace_id=trace_id,
        event_type="recommendation_import_external_requested",
        status=AnalyticsStatus.STARTED.value,
        metadata={"url_host": _url_host(data.url or "")},
    )
    process_options = build_processing_options(
        language=data.language,
        model=data.model,
        auto_generate_summary=data.auto_generate_summary,
        auto_generate_tags=data.auto_generate_tags,
        summary_style=data.summary_style,
    )
    try:
        result = import_remote_video_from_url(
            db,
            user_id=user.id,
            video_url=data.url,
            process_options=process_options,
            preferred_title=data.title,
            preferred_summary=data.summary,
            preferred_tags=list(data.tags or []),
            request_source="recommendation_import_external",
        )
    except Exception as exc:
        latency_ms = (time.perf_counter() - t0) * 1000.0
        _emit_recommendation_event(
            trace_id=trace_id,
            event_type="recommendation_import_external_failed",
            status=AnalyticsStatus.ERROR.value,
            latency_ms=latency_ms,
            metadata={"error": str(exc)[:200]},
        )
        raise
    latency_ms = (time.perf_counter() - t0) * 1000.0
    _emit_recommendation_event(
        trace_id=trace_id,
        event_type="recommendation_import_external_completed",
        status=AnalyticsStatus.OK.value,
        latency_ms=latency_ms,
        metadata={
            "video_id": result.video.id,
            "status": result.status,
            "duplicate": result.duplicate,
        },
    )
    return VideoUploadResponse(
        id=result.video.id,
        status=result.status,
        message=result.message,
        duplicate=result.duplicate,
        data=serialize_video(result.video),
    )
