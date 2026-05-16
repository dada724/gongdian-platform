"""
routers/users.py — 用户列表 / 角色修改 / 模块权限分配 / 创建用户 / 批量导入导出
仅 developer 角色可访问
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
import sqlite3, csv, io
from database import get_db, now_iso
from models import RoleUpdate, PermUpdate, UserCreate, UserImportItem
from auth import require_dev, hash_pwd

router = APIRouter(prefix="/api", tags=["users"])


# ── 开发者创建用户 ────────────────────────────────────
@router.post("/users", response_model=dict)
def create_user(body: UserCreate, _u=Depends(require_dev)):
    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (username, password_hash, role, name, department, position, created_at) VALUES (?,?,?,?,?,?,?)",
            (body.username, hash_pwd(body.password), body.role,
             body.name or "", body.department or "", body.position or "", now_iso()),
        )
        db.commit()
    except sqlite3.IntegrityError:
        db.close()
        raise HTTPException(status_code=400, detail="用户名已存在")
    uid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.close()
    return {"ok": True, "id": uid, "username": body.username, "role": body.role}


# ── 批量导入用户（JSON 数组）────────────────────────────
@router.post("/users/import", response_model=dict)
def import_users(items: list[UserImportItem], _u=Depends(require_dev)):
    db = get_db()
    created = 0
    skipped = 0
    for item in items:
        try:
            db.execute(
                "INSERT INTO users (username, password_hash, role, name, department, position, created_at) VALUES (?,?,?,?,?,?,?)",
                (item.username, hash_pwd(item.password), item.role,
                 item.name or "", item.department or "", item.position or "", now_iso()),
            )
            created += 1
        except sqlite3.IntegrityError:
            skipped += 1
    db.commit()
    db.close()
    return {"ok": True, "created": created, "skipped": skipped}


# ── 导出用户（CSV）────────────────────────────
@router.get("/users/export")
def export_users(_u=Depends(require_dev)):
    db = get_db()
    rows = db.execute(
        "SELECT username, name, department, position, role, created_at FROM users ORDER BY id"
    ).fetchall()
    db.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["账号", "姓名", "部门", "岗位", "角色", "创建时间"])
    for row in rows:
        writer.writerow([
            row["username"], row["name"] or "",
            row["department"] or "", row["position"] or "",
            row["role"], row["created_at"],
        ])
    csv_bytes = output.getvalue().encode("utf-8-sig")
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=users_export.csv"},
    )


# ── 用户列表（含各用户权限）────────────────────────────
@router.get("/users")
def list_users(_u=Depends(require_dev)):
    db = get_db()
    rows = db.execute(
        "SELECT id, username, name, department, position, role, created_at FROM users ORDER BY id"
    ).fetchall()
    result = []
    for u in rows:
        u = dict(u)
        perms = db.execute(
            "SELECT module_id FROM module_permissions WHERE user_id=?", (u["id"],)
        ).fetchall()
        u["module_permissions"] = [p["module_id"] for p in perms]
        result.append(u)
    db.close()
    return result


# ── 修改角色 ───────────────────────────────────────────
@router.put("/users/{uid}/role")
def update_role(uid: int, body: RoleUpdate, _u=Depends(require_dev)):
    db = get_db()
    db.execute("UPDATE users SET role=? WHERE id=?", (body.role, uid))
    if db.total_changes == 0:
        db.close()
        raise HTTPException(status_code=404, detail="用户不存在")
    db.commit()
    db.close()
    return {"ok": True}


# ── 修改模块权限（所有角色均可分配）───────────────────────
@router.put("/users/{uid}/permissions")
def update_permissions(uid: int, body: PermUpdate, _u=Depends(require_dev)):
    db = get_db()
    u = db.execute("SELECT role FROM users WHERE id=?", (uid,)).fetchone()
    if not u:
        db.close()
        raise HTTPException(status_code=404, detail="用户不存在")
    # 校验所有 module_id 均有效
    if body.module_ids:
        placeholders = ",".join("?" * len(body.module_ids))
        valid = db.execute(
            f"SELECT id FROM modules WHERE id IN ({placeholders})", body.module_ids
        ).fetchall()
        if len(valid) != len(body.module_ids):
            db.close()
            raise HTTPException(status_code=400, detail="包含无效的模块 ID")
    # 重写权限表
    db.execute("DELETE FROM module_permissions WHERE user_id=?", (uid,))
    for mid in body.module_ids:
        db.execute(
            "INSERT INTO module_permissions (user_id, module_id) VALUES (?,?)",
            (uid, mid),
        )
    db.commit()
    db.close()
    return {"ok": True}
