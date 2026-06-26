from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt as _bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def verify_password(plain: str, password_or_hash: str) -> bool:
    """校验密码。

    - 若配置值是 bcrypt 哈希（$2b$ 开头），用 bcrypt 校验；
    - 否则按明文严格比较（兼容旧格式）。
    """
    if password_or_hash.startswith("$2"):
        try:
            return _bcrypt.checkpw(plain.encode(), password_or_hash.encode())
        except Exception:
            return False
    return plain == password_or_hash


def hash_password(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


def create_access_token(subject: str, extra: Optional[dict] = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError:
        return None
