"""
routers/auth.py — 登录 / 当前用户
"""
from fastapi import APIRouter, HTTPException, Depends
import sqlite3

from database import get_db, init_db
from models import LoginIn, TokenOut, UserOut
from auth import hash_pwd, verify_pwd, create_token, get_current_user

router = APIRouter(prefix="/api", tags=["auth"])

init_db()  # 启动时确保表存在


@router.post("/login", response_model=TokenOut)
def login(body: LoginIn):
    db = get_db()
    row = db.execute(
        "SELECT id, username, password_hash, role FROM users WHERE username=?",
        (body.username,),
    ).fetchone()
    db.close()
    if not row or not verify_pwd(body.password, row["password_hash"]):
        raise HTTPException(401, detail="用户名或密码错误")
    token = create_token(row["username"], row["role"])
    return TokenOut(access_token=token, role=row["role"], username=row["username"])


@router.get("/me", response_model=UserOut)
def me(user=Depends(get_current_user)):
    db = get_db()
    row = db.execute(
        "SELECT id, username, name, department, position, role, created_at FROM users WHERE username=?",
        (user.username,),
    ).fetchone()
    db.close()
    if not row:
        raise HTTPException(404, detail="用户不存在")
    return dict(row)
