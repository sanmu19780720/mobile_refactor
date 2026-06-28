from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.deps import CurrentUser, get_current_user
from fastapi import Depends

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    realname: str
    role: str


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest) -> LoginResponse:
    username = body.username.strip()
    password = body.password.strip()

    # 等价原 login.php：账号或密码为空 -> 报错
    if username == "" or password == "":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="账号密码不能为空")

    for u_name, u_pass, u_real, u_role in settings.local_users:
        if u_name == username and verify_password(password, u_pass):
            token = create_access_token(
                subject=username,
                extra={"realname": u_real, "role": u_role},
            )
            return LoginResponse(
                access_token=token,
                username=username,
                realname=u_real,
                role=u_role,
            )

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")


class MeResponse(BaseModel):
    username: str
    realname: str
    role: str


@router.get("/me", response_model=MeResponse)
def me(user: CurrentUser = Depends(get_current_user)) -> MeResponse:
    return MeResponse(username=user.username, realname=user.realname, role=user.role)


class WechatLoginRequest(BaseModel):
    openid: str


_WECHAT_OPENID = "oORbK52yxJyuymhNgGDCpgC4P85o"


@router.post("/wechat", response_model=LoginResponse)
def wechat_login(body: WechatLoginRequest) -> LoginResponse:
    """微信免登录：硬编码 openid 直接签发 JWT。"""
    if body.openid != _WECHAT_OPENID:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未授权的微信用户")
    token = create_access_token(
        subject="wechat_user",
        extra={"realname": "微信用户", "role": "user"},
    )
    return LoginResponse(
        access_token=token,
        username="wechat_user",
        realname="微信用户",
        role="user",
    )
