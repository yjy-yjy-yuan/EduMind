#!/usr/bin/env python3
"""按标题查找视频并删除或清空推荐相关元数据，便于重新处理/重新入库。

推荐列表由后端实时从 `videos` 等表计算，无独立「推荐缓存表」。
- `--delete-video`：删除该视频行及常见外键子表（字幕、问答、笔记、向量索引等），文件清理交由既有异步任务或需手工删文件。
- `--reset-metadata`：保留视频与字幕，仅清空 summary/tags/语义索引标记等，便于重新跑摘要与标签。

用法（先 dry-run，再加 --execute）：

  . .venv/bin/activate
  python scripts/purge_video_recommendation_by_title.py --title "排列组合插空法详解"
  python scripts/purge_video_recommendation_by_title.py --title "排列组合插空法详解" --delete-video --execute
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent


def _resolve_backend_dir() -> Path:
    candidates: list[Path] = []
    env_path = os.environ.get("EDUMIND_BACKEND_DIR", "").strip()
    if env_path:
        candidates.append(Path(env_path).expanduser())
    candidates.extend([REPO_DIR.parent / "edumind-backend"])

    for candidate in candidates:
        if (candidate / "run.py").is_file() and (candidate / "app").is_dir():
            return candidate.resolve()
    raise FileNotFoundError("backend directory not found; expected ../edumind-backend " "(or set EDUMIND_BACKEND_DIR)")


BACKEND_DIR = _resolve_backend_dir()
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("AUTO_CREATE_TABLES", "false")
os.environ.setdefault("WHISPER_PRELOAD_ON_STARTUP", "false")

from app.core.database import SessionLocal  # noqa: E402
from app.models.note import Note  # noqa: E402
from app.models.note import NoteTimestamp  # noqa: E402
from app.models.qa import Question  # noqa: E402
from app.models.subtitle import Subtitle  # noqa: E402
from app.models.vector_index import VectorIndex  # noqa: E402
from app.models.video import Video  # noqa: E402
from app.services.video_processing_registry import forget_video_processing_request  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402


def find_videos(db: Session, *, title: str, match: str) -> list[Video]:
    q = db.query(Video)
    if match == "exact":
        q = q.filter(Video.title == title)
    else:
        q = q.filter(Video.title.contains(title))
    return list(q.order_by(Video.id.asc()).all())


def reset_metadata(db: Session, video: Video) -> None:
    video.summary = None
    video.tags = None
    video.has_semantic_index = False
    video.vector_index_id = None
    db.query(VectorIndex).filter(VectorIndex.video_id == video.id).delete()
    db.add(video)


def delete_video_cascade(db: Session, video_id: int) -> None:
    db.query(Question).filter(Question.video_id == video_id).delete()
    db.query(Subtitle).filter(Subtitle.video_id == video_id).delete()
    note_ids = [row[0] for row in db.query(Note.id).filter(Note.video_id == video_id).all()]
    if note_ids:
        db.query(NoteTimestamp).filter(NoteTimestamp.note_id.in_(note_ids)).delete()
    db.query(Note).filter(Note.video_id == video_id).delete()
    db.query(VectorIndex).filter(VectorIndex.video_id == video_id).delete()
    v = db.query(Video).filter(Video.id == video_id).first()
    if v:
        db.delete(v)
    forget_video_processing_request(video_id)


def main() -> int:
    parser = argparse.ArgumentParser(description="按标题清理或删除视频（推荐侧数据随视频行变化）。")
    parser.add_argument("--title", default="排列组合插空法详解", help="匹配标题（默认：排列组合插空法详解）")
    parser.add_argument(
        "--match",
        choices=("contains", "exact"),
        default="contains",
        help="contains：标题包含；exact：完全相等",
    )
    parser.add_argument(
        "--delete-video",
        action="store_true",
        help="删除整条视频及关联子表记录（不可恢复，除非有备份）",
    )
    parser.add_argument(
        "--reset-metadata",
        action="store_true",
        help="仅清空 summary/tags/语义索引相关字段并删 vector_indexes 行，保留视频与字幕",
    )
    parser.add_argument("--execute", action="store_true", help="实际写入数据库（否则只打印将执行的操作）")
    args = parser.parse_args()

    if args.delete_video and args.reset_metadata:
        print("error: use only one of --delete-video or --reset-metadata", file=sys.stderr)
        return 2

    if not args.delete_video and not args.reset_metadata:
        print(
            "error: specify --delete-video (remove row) or --reset-metadata (clear tags/summary only)", file=sys.stderr
        )
        return 2

    db = SessionLocal()
    try:
        rows = find_videos(db, title=args.title, match=args.match)
        if not rows:
            print(f"No video matched title ({args.match!r}): {args.title!r}")
            return 1

        for v in rows:
            print(
                f"match id={v.id} user_id={v.user_id} title={v.title!r} "
                f"status={getattr(v.status, 'value', v.status)}"
            )

        if not args.execute:
            mode = "DELETE video + children" if args.delete_video else "RESET metadata only"
            print(f"\nDry-run only. To apply ({mode}), re-run with --execute")
            return 0

        for v in rows:
            if args.delete_video:
                vid = v.id
                delete_video_cascade(db, vid)
                print(f"deleted video_id={vid}")
            else:
                reset_metadata(db, v)
                print(f"reset metadata for video_id={v.id}")

        db.commit()
        print("done.")
        return 0
    except Exception as exc:
        db.rollback()
        print(f"error: {exc}", file=sys.stderr)
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
