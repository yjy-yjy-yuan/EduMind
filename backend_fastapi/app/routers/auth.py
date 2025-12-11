"""用户认证路由 - FastAPI 版本"""

import logging
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import LoginResponse
from app.schemas.auth import UserLogin
from app.schemas.auth import UserRegister
from app.schemas.auth import UserResponse
from app.schemas.auth import UserUpdate
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=dict)
async def register(data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="邮箱已存在")

    try:
        user = User(
            username=data.username,
            email=data.email,
            password=data.password,
            gender=data.gender,
            education=data.education,
            occupation=data.occupation,
            learning_direction=data.learning_direction,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return {"success": True, "message": "注册成功", "user": user.to_dict()}
    except Exception as e:
        db.rollback()
        logger.error(f"注册失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"注册失败: {str(e)}")


@router.post("/login", response_model=dict)
async def login(data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    # 查找用户（支持用户名或邮箱登录）
    user = db.query(User).filter(User.username == data.username).first()
    if not user:
        user = db.query(User).filter(User.email == data.username).first()

    if user and user.check_password(data.password):
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.commit()

        return {"success": True, "message": "登录成功", "user": user.to_dict()}

    raise HTTPException(status_code=401, detail="用户名/邮箱或密码错误")


@router.post("/logout", response_model=dict)
async def logout():
    """用户退出登录"""
    return {"success": True, "message": "退出成功"}


@router.get("/user", response_model=dict)
async def get_user(user_id: Optional[int] = None, db: Session = Depends(get_db)):
    """获取当前登录用户信息"""
    if not user_id:
        raise HTTPException(status_code=401, detail="未登录")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {"success": True, "user": user.to_dict()}


@router.post("/user/update", response_model=dict)
async def update_user(data: UserUpdate, user_id: int, db: Session = Depends(get_db)):
    """更新用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 更新字段
    if data.gender is not None:
        user.gender = data.gender
    if data.education is not None:
        user.education = data.education
    if data.occupation is not None:
        user.occupation = data.occupation
    if data.learning_direction is not None:
        user.learning_direction = data.learning_direction
    if data.bio is not None:
        user.bio = data.bio
    if data.avatar is not None:
        user.avatar = data.avatar

    try:
        db.commit()
        return {"success": True, "message": "更新成功", "user": user.to_dict()}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")
