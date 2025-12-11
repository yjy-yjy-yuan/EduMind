"""用户模型 - SQLAlchemy 2.0 版本"""

from datetime import datetime
from typing import Optional

from app.models.base import Base
from sqlalchemy import DateTime
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash


class User(Base):
    """用户模型"""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 扩展个人信息字段
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    education: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    occupation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    learning_direction: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __init__(
        self,
        username: str,
        email: str,
        password: str,
        gender: Optional[str] = None,
        education: Optional[str] = None,
        occupation: Optional[str] = None,
        learning_direction: Optional[str] = None,
        avatar: Optional[str] = None,
        bio: Optional[str] = None,
    ):
        self.username = username
        self.email = email
        self.set_password(password)
        self.gender = gender
        self.education = education
        self.occupation = occupation
        self.learning_direction = learning_direction
        self.avatar = avatar
        self.bio = bio

    def set_password(self, password: str) -> None:
        """设置密码"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "gender": self.gender,
            "education": self.education,
            "occupation": self.occupation,
            "learning_direction": self.learning_direction,
            "avatar": self.avatar,
            "bio": self.bio,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }

    def __repr__(self) -> str:
        return f"<User {self.username}>"
