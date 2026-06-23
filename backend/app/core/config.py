from __future__ import annotations

import json
from functools import lru_cache
from typing import List, Tuple

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全站配置，从 .env 读取（取代原 config.php / local_users.php 的硬编码）。"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 数据库（保持与原 config.php 一致）
    db_host: str = "120.78.239.45"
    db_port: int = 3306
    db_name: str = "my_schema"
    db_user: str = "root"
    db_pass: str = ""

    # JWT
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 720

    # CORS
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # 本地账号 JSON：[[username, password, realname, role], ...]
    local_users_json: str = '[["管群","Kayla2025","管群","admin"]]'

    @property
    def database_url(self) -> str:
        # PyMySQL 驱动，原生支持服务端的 mysql_native_password
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_pass}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8"
        )

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def local_users(self) -> List[Tuple[str, str, str, str]]:
        """返回 [(username, password, realname, role), ...]。"""
        raw = json.loads(self.local_users_json)
        result: List[Tuple[str, str, str, str]] = []
        for entry in raw:
            username = entry[0]
            password = entry[1]
            realname = entry[2] if len(entry) > 2 else username
            role = entry[3] if len(entry) > 3 else "user"
            result.append((username, password, realname, role))
        return result


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
