"""视频推荐路由。"""

from typing import Optional

from app.core.database import get_db
from app.models.user import User
from app.models.video import Video
from app.routers.video import build_processing_options
from app.routers.video import serialize_video
from app.schemas.recommendation import RecommendationSceneListResponse
from app.schemas.recommendation import VideoRecommendationResponse
from app.schemas.video import VideoUploadResponse
from app.schemas.video import VideoUploadURL
from app.services.video_recommendation_service import SCENE_MAP
from app.services.video_recommendation_service import list_recommendation_scenes
from app.services.video_recommendation_service import normalize_scene
from app.services.video_recommendation_service import recommend_videos
from app.services.video_url_import_service import import_remote_video_from_url
from app.utils.auth_token import parse_auth_token
from app.utils.auth_token import parse_bearer_token
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from fastapi import Query
from sqlalchemy.orm import Session

router = APIRouter()


def parse_exclude_ids(raw_value: Optional[str]) -> set[int]:
    """解析逗号分隔的排除视频 ID 列表。"""
    values = set()
    for chunk in str(raw_value or "").split(","):
        text = chunk.strip()
        if text.isdigit():
            values.add(int(text))
    return values


def resolve_user_from_request(db: Session, user_id: Optional[int], authorization: Optional[str]) -> Optional[User]:
    """优先从 Bearer token 解析用户，兼容旧 query 参数。"""
    token = parse_bearer_token(authorization)
    resolved_user_id = parse_auth_token(token) or user_id
    if not resolved_user_id:
        return None
    return db.query(User).filter(User.id == resolved_user_id).first()


@router.get("/scenes", response_model=RecommendationSceneListResponse)
async def get_recommendation_scenes():
    """返回前端可直接渲染的推荐场景配置。"""
    return {"message": "获取推荐场景成功", "scenes": list_recommendation_scenes()}


@router.get("/videos", response_model=VideoRecommendationResponse)
async def get_video_recommendations(
    scene: str = Query(default="home", description="推荐场景：home/continue/review/related"),
    limit: int = Query(default=4, ge=1, le=12, description="返回条数"),
    include_external: bool = Query(default=False, description="是否附带站外候选元数据"),
    seed_video_id: Optional[int] = Query(default=None, description="相关推荐的种子视频 ID"),
    exclude_video_ids: Optional[str] = Query(default=None, description="排除的视频 ID，逗号分隔"),
    user_id: Optional[int] = Query(default=None, description="兼容旧链路的用户 ID"),
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    """返回推荐视频列表。"""
    normalized_scene = normalize_scene(scene)
    scene_option = SCENE_MAP[normalized_scene]

    if scene_option["requires_seed"] and not seed_video_id:
        raise HTTPException(status_code=422, detail="scene=related 时必须传入 seed_video_id")

    seed_video = None
    if seed_video_id is not None:
        seed_video = db.query(Video).filter(Video.id == seed_video_id).first()
        if seed_video is None:
            raise HTTPException(status_code=404, detail="seed 视频不存在")

    user = resolve_user_from_request(db, user_id, authorization)
    videos = db.query(Video).order_by(Video.updated_at.desc(), Video.upload_time.desc()).all()
    payload = recommend_videos(
        videos=videos,
        scene=normalized_scene,
        limit=limit,
        seed_video=seed_video,
        user=user,
        exclude_ids=parse_exclude_ids(exclude_video_ids),
        include_external=include_external,
    )
    payload["message"] = "获取推荐视频成功"
    return payload


@router.post("/import-external", response_model=VideoUploadResponse)
async def import_external_recommendation(data: VideoUploadURL, db: Session = Depends(get_db)):
    """将推荐页中的站外候选直接提交到现有链接下载入库链路。"""
    process_options = build_processing_options(
        language=data.language,
        model=data.model,
        auto_generate_summary=data.auto_generate_summary,
        auto_generate_tags=data.auto_generate_tags,
        summary_style=data.summary_style,
    )
    result = import_remote_video_from_url(
        db,
        video_url=data.url,
        process_options=process_options,
        preferred_title=data.title,
        preferred_summary=data.summary,
        preferred_tags=list(data.tags or []),
        request_source="recommendation_import_external",
    )
    return VideoUploadResponse(
        id=result.video.id,
        status=result.status,
        message=result.message,
        duplicate=result.duplicate,
        data=serialize_video(result.video),
    )
