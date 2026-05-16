"""
routers/subs.py — 子模块 CRUD
权限校验：developer/editor 可编辑全部；viewer 需有 module_permissions 记录
"""
from fastapi import APIRouter, Depends, HTTPException
from uuid import uuid4

from database import get_db, now_iso
from models import SubCreate, SubUpdate
from auth import get_current_user, require_editor


router = APIRouter(prefix="/api", tags=["subs"])


# ── 权限辅助 ────────────────────────────────────────────────────────
def can_edit_module(cur, username: str, role: str, module_id: str) -> bool:
    if role in ("developer", "editor"):
        return True
    if role == "viewer":
        row = cur.execute(
            "SELECT 1 FROM module_permissions WHERE "
            "user_id=(SELECT id FROM users WHERE username=?) AND module_id=?",
            (username, module_id),
        ).fetchone()
        return row is not None
    return False


# ── 列表（按模块）─────────────────────────────────────────────────
@router.get("/modules/{mid}/subs")
def list_subs(mid: str, user=Depends(get_current_user)):
    db = get_db()
    rows = db.execute(
        "SELECT * FROM submodules WHERE module_id=? ORDER BY sort_order, created_at",
        (mid,),
    ).fetchall()
    db.close()
    return [dict(r) for r in rows]


# ── 新增 ────────────────────────────────────────────────────────────
@router.post("/modules/{mid}/subs")
def create_sub(mid: str, body: SubCreate, user=Depends(require_editor)):
    db = get_db()
    # 校验用户存在
    u = db.execute(
        "SELECT id, username, role FROM users WHERE username=?", (user.username,)
    ).fetchone()
    if not u:
        db.close()
        raise HTTPException(404, "用户不存在")
    if not can_edit_module(db, user.username, user.role, mid):
        db.close()
        raise HTTPException(403, "无权限编辑该模块")
    max_so = db.execute(
        "SELECT MAX(sort_order) AS m FROM submodules WHERE module_id=?", (mid,)
    ).fetchone()["m"] or 0
    sid = "sub_" + uuid4().hex[:10]
    db.execute(
        """INSERT INTO submodules
           (id, module_id, name, type, url, content, file_name, desc,
            icon_type, icon, sort_order, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            sid, mid, body.name, body.type,
            body.url or "", body.content or "", body.file_name or "",
            body.desc or "", body.icon_type or "auto", body.icon or "",
            max_so + 1, now_iso(),
        ),
    )
    db.commit()
    db.close()
    return {"ok": True, "id": sid}


# ── 编辑 ────────────────────────────────────────────────────────────
@router.put("/subs/{sid}")
def update_sub(sid: str, body: SubUpdate, user=Depends(require_editor)):
    db = get_db()
    u = db.execute(
        "SELECT id, username, role FROM users WHERE username=?", (user.username,)
    ).fetchone()
    if not u:
        db.close()
        raise HTTPException(404, "用户不存在")
    sub = db.execute("SELECT module_id FROM submodules WHERE id=?", (sid,)).fetchone()
    if not sub:
        db.close()
        raise HTTPException(404, "子模块不存在")
    if not can_edit_module(db, user.username, user.role, sub["module_id"]):
        db.close()
        raise HTTPException(403, "无权限编辑该模块")
    fields, vals = [], []
    for key, val in [
        ("name", body.name),
        ("type", body.type),
        ("url", body.url),
        ("content", body.content),
        ("file_name", body.file_name),
        ("desc", body.desc),
        ("icon_type", body.icon_type),
        ("icon", body.icon),
    ]:
        if val is not None:
            fields.append(f"{key}=?")
            vals.append(val)
    if fields:
        vals.append(sid)
        db.execute(f"UPDATE submodules SET {', '.join(fields)} WHERE id=?", vals)
        db.commit()
    db.close()
    return {"ok": True}


# ── 删除 ────────────────────────────────────────────────────────────
@router.delete("/subs/{sid}")
def delete_sub(sid: str, user=Depends(require_editor)):
    db = get_db()
    u = db.execute(
        "SELECT id, username, role FROM users WHERE username=?", (user.username,)
    ).fetchone()
    if not u:
        db.close()
        raise HTTPException(404, "用户不存在")
    sub = db.execute("SELECT module_id FROM submodules WHERE id=?", (sid,)).fetchone()
    if not sub:
        db.close()
        raise HTTPException(404, "子模块不存在")
    if not can_edit_module(db, user.username, user.role, sub["module_id"]):
        db.close()
        raise HTTPException(403, "无权限删除该模块")
    db.execute("DELETE FROM submodules WHERE id=?", (sid,))
    db.commit()
    db.close()
    return {"ok": True}
