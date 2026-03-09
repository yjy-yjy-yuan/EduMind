"""认证相关的 Pydantic schemas"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class UserCreate(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=2, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=6)
    gender: Optional[str] = None
    education: Optional[str] = None
    occupation: Optional[str] = None
    learning_direction: Optional[str] = None
    bio: Optional[str] = None


class UserLogin(BaseModel):
    """用户登录请求"""
    username: str = Field(..., description="用户名或邮箱")
    password: str


class UserResponse(BaseModel):
    """用户响应模型"""
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

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """用户更新请求"""
    username: Optional[str] = Field(None, min_length=2, max_length=64)
    email: Optional[EmailStr] = None
    gender: Optional[str] = None
    education: Optional[str] = None
    occupation: Optional[str] = None
    learning_direction: Optional[str] = None
    avatar: Optional[str] = None
    bio: Optional[str] = None


class AuthResponse(BaseModel):
    """认证响应"""
    success: bool
    message: str
    user: Optional[UserResponse] = None
