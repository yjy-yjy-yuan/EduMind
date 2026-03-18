"""问答模型 - SQLAlchemy 2.0 版本"""

from datetime import datetime
from typing import TYPE_CHECKING
from typing import Optional

from app.models.base import Base
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.video import Video


class Question(Base):
    """问题模型"""

    __tablename__ = "questions"
    __table_args__ = (
        Index("ix_questions_scope_created_at", "user_id", "provider", "mode", "video_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    video_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("videos.id"), nullable=True)
    provider: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    mode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)  # 问题内容
    answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 回答内容
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    user: Mapped[Optional["User"]] = relationship("User", backref="questions")
    video: Mapped[Optional["Video"]] = relationship("Video", backref="questions")

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "video_id": self.video_id,
            "provider": self.provider,
            "mode": self.mode,
            "model": self.model,
            "content": self.content,
            "answer": self.answer,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
