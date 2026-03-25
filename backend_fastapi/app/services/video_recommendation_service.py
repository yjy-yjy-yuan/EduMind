"""基于现有视频库与用户资料的轻量推荐服务。"""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Iterable
from typing import Optional

from app.models.user import User
from app.models.video import Video
from app.models.video import VideoStatus

SCENE_OPTIONS = [
    {
        "value": "home",
        "label": "首页推荐",
        "description": "适合首页首屏，优先返回需要继续处理、值得复盘或符合学习方向的视频。",
        "requires_seed": False,
    },
    {
        "value": "continue",
        "label": "继续学习",
        "description": "优先返回处理中、失败待补跑和最近进入的视频，帮助用户回到当前链路。",
        "requires_seed": False,
    },
    {
        "value": "review",
        "label": "复盘推荐",
        "description": "优先返回已完成且摘要/标签较完整的视频，适合整理笔记与复习。",
        "requires_seed": False,
    },
    {
        "value": "related",
        "label": "相似内容",
        "description": "根据 seed 视频的标题、摘要与标签推荐主题相关的视频。",
        "requires_seed": True,
    },
]
SCENE_MAP = {item["value"]: item for item in SCENE_OPTIONS}
ACTIVE_STATUSES = {VideoStatus.PENDING.value, VideoStatus.PROCESSING.value, VideoStatus.DOWNLOADING.value}
TOKEN_RE = re.compile(r"[A-Za-z0-9_]{2,24}|[\u4e00-\u9fff]{2,12}")
STOP_TOKENS = {
    "video",
    "lesson",
    "course",
    "study",
    "learning",
    "课程",
    "视频",
    "学习",
    "内容",
    "专题",
    "讲解",
    "复习",
    "基础",
    "入门",
    "精讲",
    "总结",
}


def list_recommendation_scenes() -> list[dict]:
    """返回支持的推荐场景。"""
    return [dict(item) for item in SCENE_OPTIONS]


def normalize_scene(scene: Optional[str]) -> str:
    """标准化推荐场景。"""
    value = str(scene or "home").strip().lower()
    return value if value in SCENE_MAP else "home"


def parse_video_tags(video: Video) -> list[str]:
    """解析视频标签。"""
    if isinstance(video.tags, list):
        source = video.tags
    else:
        try:
            source = json.loads(video.tags) if video.tags else []
        except (TypeError, ValueError, json.JSONDecodeError):
            source = str(video.tags or "").split(",")

    return [str(item).strip() for item in source if str(item).strip()]


def unique_tokens(values: Iterable[str]) -> list[str]:
    """提取并去重文本 token。"""
    seen = set()
    tokens = []
    for value in values:
        for raw in TOKEN_RE.findall(str(value or "").lower()):
            token = raw.strip().lower()
            if len(token) < 2 or token in STOP_TOKENS or token in seen:
                continue
            seen.add(token)
            tokens.append(token)
    return tokens


def extract_video_tokens(video: Optional[Video]) -> list[str]:
    """提取视频主题 token。"""
    if video is None:
        return []
    return unique_tokens([video.title or "", video.summary or "", *parse_video_tags(video)])


def extract_user_interest_tokens(user: Optional[User]) -> list[str]:
    """提取用户学习兴趣 token。"""
    if user is None:
        return []
    return unique_tokens(
        [
            user.learning_direction or "",
            user.occupation or "",
            user.bio or "",
            user.username or "",
        ]
    )


def recency_bonus(video: Video, now: datetime) -> float:
    """最近活跃视频加分。"""
    anchor = video.updated_at or video.upload_time or now
    hours = max((now - anchor).total_seconds() / 3600, 0)
    if hours <= 24:
        return 18 - min(hours / 2, 12)
    if hours <= 7 * 24:
        return 8 - min((hours - 24) / 24, 6)
    return 0


def build_reason(
    *,
    scene: str,
    status: str,
    seed_video: Optional[Video],
    seed_overlap: list[str],
    interest_overlap: list[str],
    has_summary: bool,
    has_tags: bool,
) -> tuple[str, str, str]:
    """构建推荐理由。"""
    if status in ACTIVE_STATUSES and scene in {"home", "continue"}:
        return ("continue", "继续跟进", "当前任务仍在处理中，适合回到详情页继续跟进状态。")

    if status == VideoStatus.FAILED.value and scene in {"home", "continue"}:
        return ("retry", "建议补跑", "该视频上次处理失败，适合优先回到详情页重新提交。")

    if scene == "related" and seed_video is not None and seed_overlap:
        topic_text = "、".join(seed_overlap[:2])
        return ("related", "主题相关", f"与《{seed_video.title or '当前视频'}》共享 {topic_text} 等主题。")

    if interest_overlap:
        topic_text = "、".join(interest_overlap[:2])
        return ("interest", "匹配方向", f"内容与你当前学习方向里的 {topic_text} 更相关。")

    if scene == "review" and has_summary:
        return ("review", "适合复盘", "摘要已就绪，适合继续整理笔记与回看重点。")

    if has_tags:
        return ("tagged", "重点清晰", "已提炼标签，适合进一步问答或归纳。")

    return ("recent", "最近内容", "最近进入视频库，适合从这里继续学习。")


def score_video(
    *,
    video: Video,
    scene: str,
    now: datetime,
    seed_video: Optional[Video],
    user_tokens: list[str],
) -> tuple[float, str, str, str]:
    """对单个视频打分并返回理由。"""
    status = video.status.value if isinstance(video.status, VideoStatus) else str(video.status or "").lower()
    tags = parse_video_tags(video)
    video_tokens = extract_video_tokens(video)
    interest_overlap = [token for token in user_tokens if token in video_tokens]
    seed_overlap = []
    if seed_video is not None:
        seed_tokens = set(extract_video_tokens(seed_video))
        seed_overlap = [token for token in video_tokens if token in seed_tokens]

    score = recency_bonus(video, now)
    has_summary = bool(str(video.summary or "").strip())
    has_tags = bool(tags)

    if scene in {"home", "continue"}:
        if status in ACTIVE_STATUSES:
            score += 120 - min(float(video.process_progress or 0) / 5, 18)
        elif status == VideoStatus.FAILED.value:
            score += 96
        elif status == VideoStatus.COMPLETED.value:
            score += 64
        else:
            score += 40
    elif scene == "review":
        if status == VideoStatus.COMPLETED.value:
            score += 112
        elif status in ACTIVE_STATUSES:
            score += 28
        else:
            score += 12
    elif scene == "related":
        score += len(seed_overlap) * 30
        if status == VideoStatus.COMPLETED.value:
            score += 44
        elif status in ACTIVE_STATUSES:
            score += 18
        else:
            score += 10

    if has_summary:
        score += 12
    if has_tags:
        score += min(len(tags), 4) * 5
    score += len(interest_overlap) * 16

    reason_code, reason_label, reason_text = build_reason(
        scene=scene,
        status=status,
        seed_video=seed_video,
        seed_overlap=seed_overlap,
        interest_overlap=interest_overlap,
        has_summary=has_summary,
        has_tags=has_tags,
    )
    return score, reason_code, reason_label, reason_text


def serialize_recommendation_item(
    video: Video, *, score: float, reason_code: str, reason_label: str, reason_text: str
) -> dict:
    """序列化推荐视频。"""
    status = video.status.value if isinstance(video.status, VideoStatus) else str(video.status or "")
    processing_origin = (
        video.processing_origin.value if hasattr(video.processing_origin, "value") else video.processing_origin
    )
    return {
        "id": video.id,
        "title": video.title,
        "status": status,
        "upload_time": video.upload_time,
        "summary": video.summary,
        "tags": parse_video_tags(video),
        "process_progress": float(video.process_progress or 0),
        "current_step": str(video.current_step or ""),
        "processing_origin": processing_origin,
        "processing_origin_label": "iOS 离线处理" if str(processing_origin) == "ios_offline" else "在线处理",
        "upload_source": video.get_upload_source(),
        "upload_source_label": video.get_upload_source_label(),
        "recommendation_score": round(score, 2),
        "reason_code": reason_code,
        "reason_label": reason_label,
        "reason_text": reason_text,
    }


def recommend_videos(
    *,
    videos: list[Video],
    scene: str,
    limit: int,
    seed_video: Optional[Video] = None,
    user: Optional[User] = None,
    exclude_ids: Optional[set[int]] = None,
) -> dict:
    """生成推荐视频列表。"""
    normalized_scene = normalize_scene(scene)
    exclude_ids = set(exclude_ids or set())
    user_tokens = extract_user_interest_tokens(user)
    now = datetime.utcnow()
    scored_items = []

    for video in videos:
        if video.id in exclude_ids:
            continue
        if seed_video is not None and video.id == seed_video.id:
            continue

        score, reason_code, reason_label, reason_text = score_video(
            video=video,
            scene=normalized_scene,
            now=now,
            seed_video=seed_video,
            user_tokens=user_tokens,
        )
        scored_items.append(
            (
                score,
                video.updated_at or video.upload_time or datetime.min,
                serialize_recommendation_item(
                    video,
                    score=score,
                    reason_code=reason_code,
                    reason_label=reason_label,
                    reason_text=reason_text,
                ),
            )
        )

    scored_items.sort(key=lambda item: (item[0], item[1]), reverse=True)
    items = [item[2] for item in scored_items[:limit]]

    fallback_used = False
    if not items and videos:
        fallback_used = True
        recent_videos = sorted(
            (
                video
                for video in videos
                if video.id not in exclude_ids and (seed_video is None or video.id != seed_video.id)
            ),
            key=lambda item: item.updated_at or item.upload_time or datetime.min,
            reverse=True,
        )[:limit]
        items = [
            serialize_recommendation_item(
                video,
                score=0,
                reason_code="recent",
                reason_label="最近内容",
                reason_text="当前暂无更强信号，先从最近进入的视频继续学习。",
            )
            for video in recent_videos
        ]

    return {
        "scene": normalized_scene,
        "strategy": "video_status_interest_v1",
        "personalized": bool(user_tokens),
        "fallback_used": fallback_used,
        "seed_video_id": seed_video.id if seed_video is not None else None,
        "seed_video_title": seed_video.title if seed_video is not None else None,
        "items": items,
    }
