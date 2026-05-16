"""
auth.py — JWT 工具 + 密码哈希 + 当前用户依赖
"""
import bcrypt
from jose import jwt
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

# ── JWT 配置 ────────────────────────────────────────────────────────────
SECRET_KEY = "gongdian-super-secret-change-in-prod"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 720  # 30 天

auth_scheme = HTTPBearer()


# ── 密码处理 ────────────────────────────────────────────────────────────
def hash_pwd(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_pwd(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# ── JWT 生成 / 解析 ────────────────────────────────────────────────────
def create_token(username: str, role: str) -> str:
    exp = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {"sub": username, "role": role, "exp": exp}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


class UserInToken(BaseModel):
    username: str
    role: str


def decode_token(token: str) -> UserInToken:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return UserInToken(username=payload["sub"], role=payload["role"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token 已过期，请重新登录")
    except Exception:
        raise HTTPException(status_code=401, detail="无效的 Token")


async def get_current_user(
    cred: HTTPAuthorizationCredentials = Depends(auth_scheme),
) -> UserInToken:
    return decode_token(cred.credentials)


def require_role(allowed: list[str]):
    """返回依赖函数，检查当前用户角色是否在 allowed 列表中。"""

    async def _check(user: UserInToken = Depends(get_current_user)):
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail="权限不足")
        return user

    return _check


# 快捷依赖
require_dev = require_role(["developer"])
require_editor = require_role(["developer", "editor"])
