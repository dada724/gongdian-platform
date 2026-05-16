"""
database.py — SQLite 初始化 & 表结构
工电中心一体化平台后端数据库层
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "gongdian.db")


def get_db() -> sqlite3.Connection:
    """获取 SQLite 连接，启用外键约束，返回 dict-like rows。"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _add_column(cur, table: str, column: str, definition: str):
    """如果表中不存在该字段，则 ALTER TABLE ADD COLUMN。"""
    cur.execute(f"PRAGMA table_info({table})")
    existing = [row["name"] for row in cur.fetchall()]
    if column not in existing:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def init_db():
    """首次运行时建表；已存在则跳过；已有表自动迁移新字段。"""
    conn = get_db()
    cur = conn.cursor()

    # users 表 ---------------------------------------------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        username    TEXT    UNIQUE NOT NULL,
        password_hash TEXT    NOT NULL,
        role        TEXT    NOT NULL DEFAULT 'viewer'
                    CHECK(role IN ('developer','editor','viewer')),
        created_at  TEXT    NOT NULL
    )
    """)
    # 迁移：新增字段（SQLite 不支持 IF NOT EXISTS 对 COLUMN）
    _add_column(cur, "users", "name", "TEXT DEFAULT ''")
    _add_column(cur, "users", "department", "TEXT DEFAULT ''")
    _add_column(cur, "users", "position", "TEXT DEFAULT ''")

    # modules 表 -------------------------------------------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS modules (
        id          TEXT    PRIMARY KEY,
        name        TEXT    NOT NULL,
        icon        TEXT    DEFAULT '',
        sort_order  INTEGER DEFAULT 0,
        created_at  TEXT    NOT NULL
    )
    """)

    # submodules 表 ----------------------------------------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS submodules (
        id          TEXT    PRIMARY KEY,
        module_id   TEXT    NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
        name        TEXT    NOT NULL,
        type        TEXT    NOT NULL
                    CHECK(type IN ('web','link','file','text')),
        url         TEXT    DEFAULT '',
        content     TEXT    DEFAULT '',
        file_name   TEXT    DEFAULT '',
        desc        TEXT    DEFAULT '',
        icon_type   TEXT    DEFAULT 'auto'
                    CHECK(icon_type IN ('auto','emoji','image','favicon')),
        icon        TEXT    DEFAULT '',
        sort_order  INTEGER DEFAULT 0,
        created_at  TEXT    NOT NULL
    )
    """)

    # module_permissions 表（viewer 按模块授权） -----------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS module_permissions (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        module_id   TEXT    NOT NULL REFERENCES modules(id) ON DELETE CASCADE,
        UNIQUE(user_id, module_id)
    )
    """)

    # faults 表（故障数据）------------------------------------------------
    cur.execute("""
    CREATE TABLE IF NOT EXISTS faults (
        id                INTEGER PRIMARY KEY AUTOINCREMENT,
        date              TEXT,
        dept              TEXT    DEFAULT '',
        report_time       TEXT    DEFAULT '',
        line              TEXT    DEFAULT '',
        fault_point       TEXT    DEFAULT '',
        device_name       TEXT    DEFAULT '',
        fault_desc        TEXT    DEFAULT '',
        repair_measure    TEXT    DEFAULT '',
        repair_status     TEXT    DEFAULT '',
        fault_type        TEXT    DEFAULT '',
        repair_unit       TEXT    DEFAULT '',
        duty_team         TEXT    DEFAULT '',
        fault_level       TEXT    DEFAULT '',
        register_loc      TEXT    DEFAULT '',
        emergency_status  TEXT    DEFAULT '',
        report_unit       TEXT    DEFAULT '',
        arrive_time       TEXT    DEFAULT '',
        fix_time          TEXT    DEFAULT '',
        est_fix_time     TEXT    DEFAULT '',
        response_min      TEXT    DEFAULT '',
        daily_filter     TEXT    DEFAULT '',
        promise_hours    TEXT    DEFAULT '',
        order_no          TEXT    DEFAULT '',
        order_closed      TEXT    DEFAULT '',
        fault_process     TEXT    DEFAULT '',
        trigger_type      TEXT    DEFAULT '',
        indicator_name    TEXT    DEFAULT '',
        assign_count      TEXT    DEFAULT '',
        trigger_count     TEXT    DEFAULT '',
        check_result      TEXT    DEFAULT '',
        reporter          TEXT    DEFAULT '',
        confirmer         TEXT    DEFAULT '',
        last_editor       TEXT    DEFAULT '',
        last_edit_time    TEXT    DEFAULT '',
        photo_url         TEXT    DEFAULT '',
        stat_cycle        TEXT    DEFAULT '',
        field_extra       TEXT    DEFAULT '',
        self_check        TEXT    DEFAULT ''   CHECK(self_check IN ('自检','非自检','')),
        created_at        TEXT    NOT NULL
    )
    """)

    # 索引 ------------------------------------------------------------------
    cur.execute("CREATE INDEX IF NOT EXISTS idx_subs_module ON submodules(module_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_perms_user   ON module_permissions(user_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_perms_module ON module_permissions(module_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_faults_date   ON faults(date)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_faults_line   ON faults(line)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_faults_type   ON faults(fault_type)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_faults_self  ON faults(self_check)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_faults_dept   ON faults(dept)")

    conn.commit()
    conn.close()


def user_count() -> int:
    """返回当前用户总数，用于判断是否需要自动升 developer。"""
    conn = get_db()
    row = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()
    conn.close()
    return row["n"]


def now_iso() -> str:
    """当前时间 ISO 字符串（SQLite 友好）。"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


if __name__ == "__main__":
    init_db()
    print("✅ 数据库初始化完成：", DB_PATH)
