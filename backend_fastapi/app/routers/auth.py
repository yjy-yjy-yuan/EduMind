"""用户认证路由 - FastAPI 版本"""

import logging
from datetime import datetime
from typing import Optional

from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import UserLogin
from app.schemas.auth import UserRegister
from app.schemas.auth import UserUpdate
from app.utils.auth_security import build_password_fingerprint
from app.utils.auth_security import is_valid_phone_number
from app.utils.auth_security import looks_like_email
from app.utils.auth_security import normalize_email
from app.utils.auth_security import normalize_phone_number
from app.utils.auth_token import build_auth_token
from app.utils.auth_token import parse_auth_token
from app.utils.auth_token import parse_bearer_token
from fastapi import APIRouter
from fastapi import Depends
from fastapi import Header
from fastapi import HTTPException
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter()


def build_default_username(email: Optional[str], phone: Optional[str]) -> str:
    """根据登录标识生成默认用户名。"""
    if email:
        local_part = email.split("@", 1)[0]
        sanitized = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in local_part).strip("_")
        return (sanitized or "user")[:64]
    if phone:
        return f"user_{phone[-4:]}"
    return "user"


def ensure_unique_username(db: Session, preferred: Optional[str], email: Optional[str], phone: Optional[str]) -> str:
    """生成唯一用户名。"""
    base = preferred or build_default_username(email, phone)
    base = "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in base).strip("_") or "user"
    base = base[:64]
    candidate = base
    suffix = 1

    while db.query(User.id).filter(User.username == candidate).first():
        if preferred:
            raise HTTPException(status_code=400, detail="用户名已存在")
        suffix_text = f"_{suffix}"
        candidate = f"{base[: max(1, 64 - len(suffix_text))]}{suffix_text}"
        suffix += 1

    return candidate


def find_user_by_account(db: Session, account: str) -> Optional[User]:
    """按邮箱或手机号查找用户。"""
    normalized_account = account.strip()
    if looks_like_email(normalized_account):
        return db.query(User).filter(User.email == normalize_email(normalized_account)).first()

    normalized_phone = normalize_phone_number(normalized_account)
    if normalized_phone and is_valid_phone_number(normalized_phone):
        return db.query(User).filter(User.phone == normalized_phone).first()

    return None


def resolve_current_user_id(user_id: Optional[int], authorization: Optional[str]) -> Optional[int]:
    """优先从 Bearer token 中解析用户 ID，保留 query 参数兼容旧链路。"""
    token = parse_bearer_token(authorization)
    return parse_auth_token(token) or user_id


@router.post("/register", response_model=dict)
async def register(data: UserRegister, db: Session = Depends(get_db)):
    """用户注册"""
    email = normalize_email(data.email)
    phone = normalize_phone_number(data.phone)
    password_fingerprint = build_password_fingerprint(data.password)

    if email and db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="邮箱已存在")
    if phone and db.query(User).filter(User.phone == phone).first():
        raise HTTPException(status_code=400, detail="手机号已存在")
    if db.query(User).filter(User.password_fingerprint == password_fingerprint).first():
        raise HTTPException(status_code=400, detail="该密码已被使用，请更换一个不重复的强密码")

    username = ensure_unique_username(db, data.username, email, phone)

    try:
        user = User(
            username=username,
            email=email,
            phone=phone,
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
    user = find_user_by_account(db, data.account)
    if user is None:
        raise HTTPException(status_code=401, detail="邮箱/手机号或密码错误")

    if user.check_password(data.password):
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        user.login_count += 1
        if not user.password_fingerprint:
            user.password_fingerprint = build_password_fingerprint(data.password)
        db.commit()

        return {
            "success": True,
            "message": "登录成功",
            "user": user.to_dict(),
            "token": build_auth_token(user.id),
        }

    raise HTTPException(status_code=401, detail="邮箱/手机号或密码错误")


@router.post("/logout", response_model=dict)
async def logout():
    """用户退出登录"""
    return {"success": True, "message": "退出成功"}


@router.get("/user", response_model=dict)
async def get_user(
    user_id: Optional[int] = None,
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    """获取当前登录用户信息"""
    current_user_id = resolve_current_user_id(user_id, authorization)
    if not current_user_id:
        raise HTTPException(status_code=401, detail="未登录")

    user = db.query(User).filter(User.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    return {"success": True, "user": user.to_dict(), "token": build_auth_token(user.id)}


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
