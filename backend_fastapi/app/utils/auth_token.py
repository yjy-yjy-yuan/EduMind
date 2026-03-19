"""轻量认证 token 工具。"""

import hashlib
import hmac
from typing import Optional

from app.core.config import settings


def build_auth_token(user_id: int) -> str:
    """为当前用户生成签名 token。"""
    payload = str(user_id)
    signature = hmac.new(settings.SECRET_KEY.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def parse_auth_token(token: Optional[str]) -> Optional[int]:
    """校验 token 并提取用户 ID。"""
    if not token:
        return None

    try:
        payload, signature = token.split(".", 1)
    except ValueError:
        return None

    expected = hmac.new(settings.SECRET_KEY.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    if not payload.isdigit():
        return None
    return int(payload)


def parse_bearer_token(authorization: Optional[str]) -> Optional[str]:
    """从 Authorization 头中提取 Bearer token。"""
    if not authorization:
        return None

    scheme, _, token = authorization.strip().partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token.strip()
