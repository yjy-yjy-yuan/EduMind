"""视频推荐服务单测。"""

from app.models.video import Video
from app.models.video import VideoStatus
from app.services.video_recommendation_service import build_normalized_video_tags
from app.services.video_recommendation_service import build_recommendation_profile
from app.services.video_recommendation_service import recommend_videos


def test_build_normalized_video_tags_prepends_subject_and_aliases():
    """归一化标签时应补上科目，并收敛常见别名。"""
    video = Video(
        id=1,
        title="高数导数专题",
        filename="math.mp4",
        filepath="/tmp/math.mp4",
        status=VideoStatus.COMPLETED,
        summary="围绕微积分中的导数与极限做系统讲解。",
        tags='["高数","导数","极限"]',
    )

    tags = build_normalized_video_tags(video)

    assert tags[0] == "数学"
    assert "高等数学" in tags
    assert "高数" not in tags


def test_build_recommendation_profile_uses_subject_as_cluster_anchor():
    """推荐画像应包含科目与稳定主题桶。"""
    video = Video(
        id=2,
        title="Python 数据结构入门",
        filename="python.mp4",
        filepath="/tmp/python.mp4",
        status=VideoStatus.COMPLETED,
        summary="介绍栈、队列和链表的核心操作。",
        tags='["Python","数据结构"]',
    )

    profile = build_recommendation_profile(video)

    assert profile.subject == "计算机"
    assert profile.tags[0] == "计算机"
    assert profile.cluster_key.startswith("计算机::")


def test_build_recommendation_profile_marks_combinatorics_as_math():
    """排列组合/插空法类视频也应归入数学科目。"""
    video = Video(
        id=3,
        title="排列组合中的插空法详解",
        filename="combinatorics.mp4",
        filepath="/tmp/combinatorics.mp4",
        status=VideoStatus.COMPLETED,
        summary="讲解排列组合里处理不相邻问题的插空法和空位计数。",
        tags='["插空法","排列组合","空位计数"]',
    )

    profile = build_recommendation_profile(video)

    assert profile.subject == "数学"
    assert profile.tags[0] == "数学"
    assert profile.cluster_key.startswith("数学::")


def test_recommend_videos_related_prefers_same_subject_match():
    """相关推荐在主题重合较弱时，也应优先返回同科目内容。"""
    seed_video = Video(
        id=10,
        title="牛顿第二定律串讲",
        filename="seed.mp4",
        filepath="/tmp/seed.mp4",
        status=VideoStatus.COMPLETED,
        summary="高中物理受力分析与牛顿第二定律综合应用。",
        tags=None,
    )
    same_subject_video = Video(
        id=11,
        title="受力分析复习",
        filename="physics.mp4",
        filepath="/tmp/physics.mp4",
        status=VideoStatus.COMPLETED,
        summary="物理力学里常见的受力分析步骤整理。",
        tags=None,
    )
    other_video = Video(
        id=12,
        title="英语听力技巧",
        filename="english.mp4",
        filepath="/tmp/english.mp4",
        status=VideoStatus.COMPLETED,
        summary="整理英语听力高频信号词和定位方法。",
        tags='["英语听力"]',
    )

    payload = recommend_videos(
        videos=[seed_video, same_subject_video, other_video],
        scene="related",
        limit=2,
        seed_video=seed_video,
    )

    assert payload["items"][0]["id"] == same_subject_video.id
    assert payload["items"][0]["tags"][0] == "物理"
    assert payload["items"][0]["reason_code"] in {"related", "subject"}
