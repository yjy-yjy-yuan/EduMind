"""认证路由 - FastAPI 版本"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, UserResponse, UserUpdate, AuthResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# 简单的session存储 (生产环境应使用Redis或数据库)
sessions = {}


def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """获取当前登录用户"""
    session_id = request.cookies.get("session_id")
    if not session_id or session_id not in sessions:
        return None

    user_id = sessions.get(session_id)
    if not user_id:
        return None

    return db.query(User).filter(User.id == user_id).first()


@router.post("/register", response_model=AuthResponse)
async def register(request: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == request.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status_code=400, detail="邮箱已存在")

    # 创建新用户
    user = User(
        username=request.username,
        email=request.email,
        gender=request.gender,
        education=request.education,
        occupation=request.occupation,
        learning_direction=request.learning_direction,
        bio=request.bio
    )
    user.set_password(request.password)

    db.add(user)
    db.commit()
    db.refresh(user)

    return AuthResponse(
        success=True,
        message="注册成功",
        user=UserResponse.model_validate(user.to_dict())
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: UserLogin, response: Response, db: Session = Depends(get_db)):
    """用户登录"""
    # 查找用户（支持用户名或邮箱登录）
    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        user = db.query(User).filter(User.email == request.username).first()

    if not user or not user.check_password(request.password):
        raise HTTPException(status_code=401, detail="用户名/邮箱或密码错误")

    # 更新最后登录时间
    user.last_login = datetime.utcnow()
    db.commit()

    # 创建session
    import uuid
    session_id = str(uuid.uuid4())
    sessions[session_id] = user.id

    # 设置cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        httponly=True,
        max_age=86400 * 7,  # 7天
        samesite="lax"
    )

    return AuthResponse(
        success=True,
        message="登录成功",
        user=UserResponse.model_validate(user.to_dict())
    )


@router.post("/logout", response_model=AuthResponse)
async def logout(request: Request, response: Response):
    """用户退出登录"""
    session_id = request.cookies.get("session_id")
    if session_id and session_id in sessions:
        del sessions[session_id]

    response.delete_cookie("session_id")

    return AuthResponse(success=True, message="退出成功")


@router.get("/user", response_model=AuthResponse)
async def get_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """获取当前登录用户信息"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    return AuthResponse(
        success=True,
        message="获取成功",
        user=UserResponse.model_validate(user.to_dict())
    )


@router.post("/user/update", response_model=AuthResponse)
async def update_user(
    request: Request,
    update_data: UserUpdate,
    db: Session = Depends(get_db)
):
    """更新用户信息"""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")

    # 更新用户名
    if update_data.username and update_data.username != user.username:
        if db.query(User).filter(User.username == update_data.username).first():
            raise HTTPException(status_code=400, detail="用户名已存在")
        user.username = update_data.username

    # 更新邮箱
    if update_data.email and update_data.email != user.email:
        if db.query(User).filter(User.email == update_data.email).first():
            raise HTTPException(status_code=400, detail="邮箱已存在")
        user.email = update_data.email

    # 更新其他字段
    if update_data.gender is not None:
        user.gender = update_data.gender

    if update_data.education is not None:
        user.education = update_data.education

    if update_data.occupation is not None:
        user.occupation = update_data.occupation

    if update_data.learning_direction is not None:
        user.learning_direction = update_data.learning_direction

    if update_data.bio is not None:
        user.bio = update_data.bio

    if update_data.avatar is not None:
        user.avatar = update_data.avatar

    db.commit()
    db.refresh(user)

    return AuthResponse(
        success=True,
        message="更新成功",
        user=UserResponse.model_validate(user.to_dict())
    )
