"""
routers/modules.py — 模块 CRUD + 拖拽排序 + 权限校验
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlite3 import Connection

from database import get_db, now_iso
from models import ModuleCreate, ModuleUpdate, ReorderIn
from auth import get_current_user, require_editor, require_dev

router = APIRouter(prefix="/api", tags=["modules"])


# ── 权限辅助 ────────────────────────────────────────────────────────
def can_edit_module(cur, username: str, role: str, module_id: str) -> bool:
    if role in ("developer", "editor"):
        return True
    if role == "viewer":
        row = cur.execute(
            "SELECT 1 FROM module_permissions WHERE user_id="
            "(SELECT id FROM users WHERE username=?) AND module_id=?",
            (username, module_id),
        ).fetchone()
        return row is not None
    return False


# ── 列表 ────────────────────────────────────────────────────────────
@router.get("/modules")
def list_modules(user=Depends(get_current_user)):
    db = get_db()
    rows = db.execute(
        "SELECT id, name, icon, sort_order FROM modules ORDER BY sort_order, created_at"
    ).fetchall()
    result = []
    for m in rows:
        m = dict(m)
        subs = db.execute(
            "SELECT * FROM submodules WHERE module_id=? ORDER BY sort_order, created_at",
            (m["id"],),
        ).fetchall()
        m["subs"] = [dict(s) for s in subs]
        result.append(m)
    db.close()
    return result


# ── 新增 ────────────────────────────────────────────────────────────
@router.post("/modules")
def create_module(body: ModuleCreate, user=Depends(require_editor)):
    from uuid import uuid4
    db = get_db()
    cur = db.cursor()
    # 校验用户存在
    u = db.execute(
        "SELECT id, username, role FROM users WHERE username=?", (user.username,)
    ).fetchone()
    if not u:
        db.close()
        raise HTTPException(404, "用户不存在")
    max_so = db.execute("SELECT MAX(sort_order) AS m FROM modules").fetchone()["m"] or 0
    mid = "mod_" + uuid4().hex[:10]
    cur.execute(
        "INSERT INTO modules (id, name, icon, sort_order, created_at) VALUES (?,?,?,?,?)",
        (mid, body.name, body.icon or "", max_so + 1, now_iso()),
    )
    db.commit()
    db.close()
    return {"ok": True, "id": mid}


# ── 编辑 ────────────────────────────────────────────────────────────
@router.put("/modules/{mid}")
def update_module(
    mid: str,
    body: ModuleUpdate,
    user=Depends(require_editor),
):
    db = get_db()
    u = db.execute(
        "SELECT id FROM users WHERE username=?", (user.username,)
    ).fetchone()
    if not u:
        db.close()
        raise HTTPException(404, "用户不存在")
    if not can_edit_module(db, user.username, user.role, mid):
        db.close()
        raise HTTPException(403, "无权限编辑该模块")
    fields, vals = [], []
    if body.name is not None:
        fields.append("name=?")
        vals.append(body.name)
    if body.icon is not None:
        fields.append("icon=?")
        vals.append(body.icon)
    if not fields:
        db.close()
        return {"ok": True}
    vals.extend([mid])
    db.execute(f"UPDATE modules SET {', '.join(fields)} WHERE id=?", vals)
    db.commit()
    db.close()
    return {"ok": True}


# ── 删除 ────────────────────────────────────────────────────────────
@router.delete("/modules/{mid}")
def delete_module(mid: str, user=Depends(require_editor)):
    db = get_db()
    u = db.execute(
        "SELECT id FROM users WHERE username=?", (user.username,)
    ).fetchone()
    if not u:
        db.close()
        raise HTTPException(404, "用户不存在")
    if not can_edit_module(db, user.username, user.role, mid):
        db.close()
        raise HTTPException(403, "无权限删除该模块")
    db.execute("DELETE FROM modules WHERE id=?", (mid,))
    db.commit()
    db.close()
    return {"ok": True}


# ── 拖拽排序 ────────────────────────────────────────────────────────
@router.post("/modules/reorder")
def reorder(body: ReorderIn, user=Depends(require_editor)):
    db = get_db()
    cur = db.cursor()
    for i, mid in enumerate(body.ids):
        cur.execute("UPDATE modules SET sort_order=? WHERE id=?", (i, mid))
    db.commit()
    db.close()
    return {"ok": True}
