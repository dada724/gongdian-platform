"""
models.py — Pydantic 请求/响应模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List


# ── 认证 ────────────────────────────────────────────────────────────
class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str


class UserOut(BaseModel):
    id: int
    username: str
    name: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    role: str
    created_at: str


# ── 模块 ────────────────────────────────────────────────────────────
class ModuleCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    icon: Optional[str] = ""


class ModuleUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None


class ReorderIn(BaseModel):
    ids: List[str]  # 按新顺序传入模块 id 列表


# ── 子模块 ──────────────────────────────────────────────────────────
class SubCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    type: str = Field(..., pattern="^(web|link|file|text)$")
    url: Optional[str] = ""
    content: Optional[str] = ""
    file_name: Optional[str] = ""
    desc: Optional[str] = ""
    icon_type: Optional[str] = "auto"
    icon: Optional[str] = ""


class SubUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    url: Optional[str] = None
    content: Optional[str] = None
    file_name: Optional[str] = None
    desc: Optional[str] = None
    icon_type: Optional[str] = None
    icon: Optional[str] = None


# ── 用户管理（developer 专用）──────────────────────────────────────
class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=32, description="账号（登录用）")
    name: str = Field(..., min_length=1, max_length=64, description="姓名")
    password: str = Field(..., min_length=4, max_length=64)
    role: str = Field(default="viewer", pattern="^(developer|editor|viewer)$")
    department: Optional[str] = None
    position: Optional[str] = None


class UserImportItem(BaseModel):
    """批量导入的单行用户数据"""
    username: str = Field(..., min_length=2, max_length=32)
    name: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=4, max_length=64)
    role: str = Field(default="viewer", pattern="^(developer|editor|viewer)$")
    department: Optional[str] = None
    position: Optional[str] = None


class RoleUpdate(BaseModel):
    role: str = Field(..., pattern="^(developer|editor|viewer)$")


class PermUpdate(BaseModel):
    module_ids: List[str]  # 该用户可获得访问权限的模块 id 列表
