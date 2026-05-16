"""
routers/faults.py — 故障数据 CRUD + 导入导出 + 看板统计
仅 developer 和 editor 可写入，viewer 可读取
"""
import io, csv, sqlite3
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from datetime import datetime
from typing import List, Optional

from database import get_db, now_iso
from models import FaultCreate, FaultUpdate, FaultQuery
from auth import require_dev, require_editor, get_current_user

router = APIRouter(prefix="/api", tags=["faults"])


# ── 查询故障列表（分页 + 筛选）────────────────────────────
@router.get("/faults")
def list_faults(
    date_from: Optional[str] = None,
    date_to:   Optional[str] = None,
    line:      Optional[str] = None,
    fault_type: Optional[str] = None,
    dept:      Optional[str] = None,
    duty_team:  Optional[str] = None,
    self_check: Optional[str] = None,
    repair_status: Optional[str] = None,
    keyword:   Optional[str] = None,
    page:      int = 1,
    page_size:  int = 50,
    _u = Depends(get_current_user),
):
    db = get_db()
    where = []
    params = []
    if date_from:
        where.append("date >= ?"); params.append(date_from)
    if date_to:
        where.append("date <= ?"); params.append(date_to)
    if line:
        where.append("line = ?");  params.append(line)
    if fault_type:
        where.append("fault_type LIKE ?"); params.append(f"%{fault_type}%")
    if dept:
        where.append("dept = ?");  params.append(dept)
    if duty_team:
        where.append("duty_team = ?"); params.append(duty_team)
    if self_check:
        where.append("self_check = ?"); params.append(self_check)
    if repair_status:
        where.append("repair_status = ?"); params.append(repair_status)
    if keyword:
        where.append("(fault_desc LIKE ? OR device_name LIKE ? OR fault_point LIKE ?)")
        params.extend([f"%{keyword}%"] * 3)

    wh = ("WHERE " + " AND ".join(where)) if where else ""
    # 总数
    total = db.execute(f"SELECT COUNT(*) AS n FROM faults {wh}", params).fetchone()["n"]
    # 分页
    offset = (page - 1) * page_size
    rows = db.execute(
        f"SELECT * FROM faults {wh} ORDER BY date DESC, id DESC LIMIT ? OFFSET ?",
        params + [page_size, offset]
    ).fetchall()
    db.close()
    return {"total": total, "page": page, "page_size": page_size, "data": [dict(r) for r in rows]}


# ── 新增单条故障 ───────────────────────────────────────────
@router.post("/faults", response_model=dict)
def create_fault(body: FaultCreate, _u=Depends(require_editor)):
    db = get_db()
    db.execute("""
        INSERT INTO faults (
            date, dept, report_time, line, fault_point, device_name,
            fault_desc, repair_measure, repair_status, fault_type,
            repair_unit, duty_team, fault_level, register_loc,
            emergency_status, report_unit, arrive_time, fix_time,
            est_fix_time, response_min, daily_filter, promise_hours,
            order_no, order_closed, fault_process, trigger_type,
            indicator_name, assign_count, trigger_count, check_result,
            reporter, confirmer, last_editor, last_edit_time,
            photo_url, stat_cycle, field_extra, self_check,
            created_at
        ) VALUES (
            ?,?,?,?,?,?, ?,?,?,?, ?,?,?,?, ?,?,?,?, ?,?,?,?, ?,?,?,?, ?,?,?,?, ?,?,?,?, ?,?,?,?, ?
        )
    """, (
        body.date, body.dept, body.report_time, body.line, body.fault_point, body.device_name,
        body.fault_desc, body.repair_measure, body.repair_status, body.fault_type,
        body.repair_unit, body.duty_team, body.fault_level, body.register_loc,
        body.emergency_status, body.report_unit, body.arrive_time, body.fix_time,
        body.est_fix_time, body.response_min, body.daily_filter, body.promise_hours,
        body.order_no, body.order_closed, body.fault_process, body.trigger_type,
        body.indicator_name, body.assign_count, body.trigger_count, body.check_result,
        body.reporter, body.confirmer, body.last_editor, body.last_edit_time,
        body.photo_url, body.stat_cycle, body.field_extra, body.self_check,
        now_iso(),
    ))
    fid = db.execute("SELECT last_insert_rowid()").fetchone()[0]
    db.commit(); db.close()
    return {"ok": True, "id": fid}


# ── 更新单条故障 ───────────────────────────────────────────
@router.put("/faults/{fid}", response_model=dict)
def update_fault(fid: int, body: FaultUpdate, _u=Depends(require_editor)):
    db = get_db()
    sets, params = [], []
    for field, value in body.model_dump(exclude_none=True).items():
        sets.append(f"{field} = ?"); params.append(value)
    if not sets:
        db.close(); return {"ok": True}
    params.append(fid)
    db.execute(f"UPDATE faults SET {', '.join(sets)} WHERE id = ?", params)
    if db.total_changes == 0:
        db.close(); raise HTTPException(status_code=404, detail="故障记录不存在")
    db.commit(); db.close()
    return {"ok": True}


# ── 删除单条故障 ───────────────────────────────────────────
@router.delete("/faults/{fid}", response_model=dict)
def delete_fault(fid: int, _u=Depends(require_dev)):
    db = get_db()
    db.execute("DELETE FROM faults WHERE id = ?", (fid,))
    if db.total_changes == 0:
        db.close(); raise HTTPException(status_code=404, detail="故障记录不存在")
    db.commit(); db.close()
    return {"ok": True}


# ── 批量导入 Excel ────────────────────────────────────────
@router.post("/faults/import", response_model=dict)
def import_faults(_u=Depends(require_editor)):
    # 注意：实际文件上传需要用 multipart，这里先占位
    # 完整实现见下方 `upload_faults`
    return {"detail": "请使用 /api/faults/upload 上传 Excel 文件"}


@router.post("/faults/upload", response_model=dict)
async def upload_faults(file: UploadFile = File(...), _u=Depends(require_editor)):
    import openpyxl
    content = await file.read()
    wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise HTTPException(status_code=400, detail="文件为空")
    headers = [str(h).strip() if h else "" for h in rows[0]]
    # 字段映射（Excel 列名 → 数据库字段名）
    FIELD_MAP = {
        "日期": "date", "部门": "dept", "报告时间": "report_time",
        "线路": "line", "故障点位": "fault_point", "设备名称": "device_name",
        "故障现象": "fault_desc", "故障原因+修复措施": "repair_measure",
        "修复情况": "repair_status", "故障类型": "fault_type",
        "修复单位": "repair_unit", "责任班组": "duty_team",
        "故障等级": "fault_level", "登记位置": "register_loc",
        "抢修情况": "emergency_status", "报告单位": "report_unit",
        "到达时间": "arrive_time", "修复时间": "fix_time",
        "预计修复时间": "est_fix_time", "响应时间(min)": "response_min",
        "日报筛选日期": "daily_filter", "维修服务承诺时间（h）": "promise_hours",
        "工单号": "order_no", "工单闭环情况": "order_closed",
        "故障处理过程": "fault_process", "触发指标类型": "trigger_type",
        "具体指标名称": "indicator_name", "分配次数": "assign_count",
        "触发次数": "trigger_count", "考核情况": "check_result",
        "接报人": "reporter", "确认人": "confirmer",
        "最后修改人": "last_editor", "最后修改时间": "last_edit_time",
        "照片": "photo_url", "统计周期": "stat_cycle", "字段": "field_extra",
        "自检情况": "self_check",
    }
    db = get_db()
    created = 0; skipped = 0
    for row in rows[1:]:
        if not any(row): continue
        fvals = {}
        for i, h in enumerate(headers):
            db_field = FIELD_MAP.get(h)
            if db_field and i < len(row):
                fvals[db_field] = row[i]
        # 必填字段检查（至少有线路或故障描述）
        if not fvals.get("line") and not fvals.get("fault_desc"):
            skipped += 1; continue
        cols = ", ".join(fvals.keys()) + ", created_at"
        placeholders = ", ".join(["?"] * (len(fvals) + 1))
        db.execute(
            f"INSERT INTO faults ({cols}) VALUES ({placeholders})",
            list(fvals.values()) + [now_iso()]
        )
        created += 1
    db.commit(); db.close()
    return {"ok": True, "created": created, "skipped": skipped}


# ── 导出为 CSV ────────────────────────────────────────────
@router.get("/faults/export")
def export_faults(
    date_from: Optional[str] = None,
    date_to:   Optional[str] = None,
    line:      Optional[str] = None,
    self_check: Optional[str] = None,
    _u = Depends(require_dev),
):
    db = get_db()
    where = []; params = []
    if date_from: where.append("date >= ?"); params.append(date_from)
    if date_to:   where.append("date <= ?"); params.append(date_to)
    if line:      where.append("line = ?");  params.append(line)
    if self_check: where.append("self_check = ?"); params.append(self_check)
    wh = ("WHERE " + " AND ".join(where)) if where else ""
    rows = db.execute(f"SELECT * FROM faults {wh} ORDER BY date DESC", params).fetchall()
    db.close()

    output = io.StringIO()
    writer = csv.writer(output)
    headers = ["日期","部门","报告时间","线路","故障点位","设备名称",
               "故障现象","故障原因+修复措施","修复情况","故障类型",
               "修复单位","责任班组","故障等级","登记位置",
               "抢修情况","报告单位","到达时间","修复时间",
               "预计修复时间","响应时间(min)","日报筛选日期","维修服务承诺时间（h）",
               "工单号","工单闭环情况","故障处理过程","触发指标类型",
               "具体指标名称","分配次数","触发次数","考核情况",
               "接报人","确认人","最后修改人","最后修改时间",
               "照片","统计周期","自检情况"]
    writer.writerow(headers)
    for r in rows:
        writer.writerow([
            r["date"] or "", r["dept"] or "", r["report_time"] or "",
            r["line"] or "", r["fault_point"] or "", r["device_name"] or "",
            r["fault_desc"] or "", r["repair_measure"] or "", r["repair_status"] or "",
            r["fault_type"] or "", r["repair_unit"] or "", r["duty_team"] or "",
            r["fault_level"] or "", r["register_loc"] or "", r["emergency_status"] or "",
            r["report_unit"] or "", r["arrive_time"] or "", r["fix_time"] or "",
            r["est_fix_time"] or "", r["response_min"] or "", r["daily_filter"] or "",
            r["promise_hours"] or "", r["order_no"] or "", r["order_closed"] or "",
            r["fault_process"] or "", r["trigger_type"] or "", r["indicator_name"] or "",
            r["assign_count"] or "", r["trigger_count"] or "", r["check_result"] or "",
            r["reporter"] or "", r["confirmer"] or "", r["last_editor"] or "",
            r["last_edit_time"] or "", r["photo_url"] or "", r["stat_cycle"] or "",
            r["self_check"] or "",
        ])
    csv_bytes = output.getvalue().encode("utf-8-sig")
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=faults_export.csv"},
    )


# ── 看板汇总统计 ──────────────────────────────────────────
@router.get("/dashboard/summary")
def dashboard_summary(_u=Depends(get_current_user)):
    db = get_db()
    total    = db.execute("SELECT COUNT(*) AS n FROM faults").fetchone()["n"]
    zijian   = db.execute("SELECT COUNT(*) AS n FROM faults WHERE self_check='自检'").fetchone()["n"]
    feizijian= db.execute("SELECT COUNT(*) AS n FROM faults WHERE self_check='非自检'").fetchone()["n"]
    unfixed  = db.execute("SELECT COUNT(*) AS n FROM faults WHERE repair_status<>'已修复' AND (repair_status IS NULL OR repair_status<>'已修复')").fetchone()["n"]
    # 未修复：repairs_status 不是"已修复"
    unfixed2 = db.execute(
        "SELECT COUNT(*) AS n FROM faults WHERE COALESCE(repair_status,'') != '已修复'"
    ).fetchone()["n"]
    db.close()
    return {
        "total": total,
        "zijian": zijian,
        "feizijian": feizijian,
        "unfixed": unfixed2,
        "fixed": total - unfixed2,
    }


# ── 看板图表数据 ──────────────────────────────────────────
@router.get("/dashboard/chart")
def dashboard_chart(
    chart_type: str,   # line / bar / pie
    group_by:  str,   # 分组字段：line / fault_type / duty_team / dept
    date_from: Optional[str] = None,
    date_to:   Optional[str] = None,
    self_check: Optional[str] = None,
    _u = Depends(get_current_user),
):
    db = get_db()
    where = []; params = []
    if date_from: where.append("date >= ?"); params.append(date_from)
    if date_to:   where.append("date <= ?"); params.append(date_to)
    if self_check: where.append("self_check = ?"); params.append(self_check)
    wh = ("WHERE " + " AND ".join(where)) if where else ""

    # 按分组字段统计数量
    allowed = {"line","fault_type","duty_team","dept","repair_unit","fault_level","stat_cycle"}
    if group_by not in allowed:
        db.close(); raise HTTPException(status_code=400, detail=f"不支持的 group_by：{group_by}")
    rows = db.execute(
        f"SELECT {group_by} AS label, COUNT(*) AS value FROM faults {wh} GROUP BY {group_by} ORDER BY value DESC LIMIT 20",
        params
    ).fetchall()
    # 月度趋势（group_by=stat_cycle 或按 date 月份）
    if group_by == "monthly":
        rows = db.execute(f"""
            SELECT SUBSTR(date,1,7) AS label, COUNT(*) AS value
            FROM faults {wh}
            WHERE date IS NOT NULL AND date != ''
            GROUP BY label ORDER BY label
        """, params).fetchall()
    db.close()
    return {
        "chart_type": chart_type,
        "group_by": group_by,
        "data": [{"label": r["label"] or "未知", "value": r["value"]} for r in rows]
    }
