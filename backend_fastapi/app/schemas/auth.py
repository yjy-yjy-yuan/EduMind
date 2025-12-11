"""认证 Pydantic Schema"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import EmailStr
from pydantic import Field


class UserRegister(BaseModel):
    """用户注册请求"""

    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=6)
    gender: Optional[str] = None
    education: Optional[str] = None
    occupation: Optional[str] = None
    learning_direction: Optional[str] = None


class UserLogin(BaseModel):
    """用户登录请求"""

    username: str
    password: str


class UserUpdate(BaseModel):
    """用户信息更新请求"""

    gender: Optional[str] = None
    education: Optional[str] = None
    occupation: Optional[str] = None
    learning_direction: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None


class UserResponse(BaseModel):
    """用户响应"""

    id: int
    username: str
    email: str
    gender: Optional[str] = None
    education: Optional[str] = None
    occupation: Optional[str] = None
    learning_direction: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    """登录响应"""

    message: str
    user: UserResponse
    token: Optional[str] = None
