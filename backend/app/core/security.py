from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain: str, password_or_hash: str) -> bool:
    """校验密码。

    本地账号在配置里以明文存储（沿用原 local_users 行为），因此这里支持两种：
    - 若配置值是 bcrypt 哈希，则用哈希校验；
    - 否则按明文严格比较（等价于原 login.php 的 $password === $pass）。
    """
    if password_or_hash.startswith("$2"):
        try:
            return pwd_context.verify(plain, password_or_hash)
        except ValueError:
            return False
    return plain == password_or_hash


def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


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
