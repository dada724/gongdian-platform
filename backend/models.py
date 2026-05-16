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


# ── 故障数据 ──────────────────────────────────────────────────────
class FaultCreate(BaseModel):
    date: Optional[str] = None
    dept: Optional[str] = None
    report_time: Optional[str] = None
    line: Optional[str] = None
    fault_point: Optional[str] = None
    device_name: Optional[str] = None
    fault_desc: Optional[str] = None
    repair_measure: Optional[str] = None
    repair_status: Optional[str] = None
    fault_type: Optional[str] = None
    repair_unit: Optional[str] = None
    duty_team: Optional[str] = None
    fault_level: Optional[str] = None
    register_loc: Optional[str] = None
    emergency_status: Optional[str] = None
    report_unit: Optional[str] = None
    arrive_time: Optional[str] = None
    fix_time: Optional[str] = None
    est_fix_time: Optional[str] = None
    response_min: Optional[str] = None
    daily_filter: Optional[str] = None
    promise_hours: Optional[str] = None
    order_no: Optional[str] = None
    order_closed: Optional[str] = None
    fault_process: Optional[str] = None
    trigger_type: Optional[str] = None
    indicator_name: Optional[str] = None
    assign_count: Optional[str] = None
    trigger_count: Optional[str] = None
    check_result: Optional[str] = None
    reporter: Optional[str] = None
    confirmer: Optional[str] = None
    last_editor: Optional[str] = None
    last_edit_time: Optional[str] = None
    photo_url: Optional[str] = None
    stat_cycle: Optional[str] = None
    field_extra: Optional[str] = None
    self_check: Optional[str] = None   # '自检' / '非自检'


class FaultUpdate(BaseModel):
    date: Optional[str] = None
    dept: Optional[str] = None
    report_time: Optional[str] = None
    line: Optional[str] = None
    fault_point: Optional[str] = None
    device_name: Optional[str] = None
    fault_desc: Optional[str] = None
    repair_measure: Optional[str] = None
    repair_status: Optional[str] = None
    fault_type: Optional[str] = None
    repair_unit: Optional[str] = None
    duty_team: Optional[str] = None
    fault_level: Optional[str] = None
    register_loc: Optional[str] = None
    emergency_status: Optional[str] = None
    report_unit: Optional[str] = None
    arrive_time: Optional[str] = None
    fix_time: Optional[str] = None
    est_fix_time: Optional[str] = None
    response_min: Optional[str] = None
    daily_filter: Optional[str] = None
    promise_hours: Optional[str] = None
    order_no: Optional[str] = None
    order_closed: Optional[str] = None
    fault_process: Optional[str] = None
    trigger_type: Optional[str] = None
    indicator_name: Optional[str] = None
    assign_count: Optional[str] = None
    trigger_count: Optional[str] = None
    check_result: Optional[str] = None
    reporter: Optional[str] = None
    confirmer: Optional[str] = None
    last_editor: Optional[str] = None
    last_edit_time: Optional[str] = None
    photo_url: Optional[str] = None
    stat_cycle: Optional[str] = None
    field_extra: Optional[str] = None
    self_check: Optional[str] = None


class FaultQuery(BaseModel):
    """故障查询筛选参数"""
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    line: Optional[str] = None
    fault_type: Optional[str] = None
    dept: Optional[str] = None
    duty_team: Optional[str] = None
    self_check: Optional[str] = None   # '自检' / '非自检'
    repair_status: Optional[str] = None
    keyword: Optional[str] = None
    page: int = 1
    page_size: int = 50
