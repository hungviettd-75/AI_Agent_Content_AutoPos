#!/usr/bin/env python3
"""
database/migrate_to_postgres.py
================================
Script chuyển toàn bộ dữ liệu từ SQLite sang PostgreSQL.

CÁCH SỬ DỤNG:
    python database/migrate_to_postgres.py

YÊU CẦU:
    1. Đã cài psycopg2-binary: pip install psycopg2-binary
    2. File .env đã khai báo đầy đủ:
         PG_HOST, PG_PORT, PG_NAME, PG_USER, PG_PASSWORD
         (hoặc PG_DSN trực tiếp)
    3. File SQLite nguồn: content_manager.db (mặc định)

TÍNH NĂNG:
    ✅ Tự tạo schema PostgreSQL nếu chưa có
    ✅ Backup SQLite trước khi migrate
    ✅ Migrate tuần tự từng bảng (posts, weekly_schedules, knowledge_posts)
    ✅ Kiểm tra trùng lặp (idempotent)
    ✅ Hiển thị tiến trình và thống kê
    ✅ Rollback nếu có lỗi nghiêm trọng
    ✅ Sinh báo cáo migration
"""

import os
import sys
import sqlite3
import shutil
import json
import argparse
from datetime import datetime
from pathlib import Path

# Thêm thư mục gốc vào sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Load env
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------
SQLITE_PATH  = os.getenv("DB_PATH", "content_manager.db")
PG_HOST      = os.getenv("PG_HOST", "localhost")
PG_PORT      = os.getenv("PG_PORT", "5432")
PG_NAME      = os.getenv("PG_NAME", "ai_agent_marketing")
PG_USER      = os.getenv("PG_USER", "postgres")
PG_PASSWORD  = os.getenv("PG_PASSWORD", "")
PG_DSN       = os.getenv(
    "PG_DSN",
    f"postgresql://{PG_USER}:{PG_PASSWORD}@{PG_HOST}:{PG_PORT}/{PG_NAME}"
)

BACKUP_DIR   = ROOT / "backups_old"

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def log(level: str, msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    icons = {"INFO": "ℹ️", "OK": "✅", "WARN": "⚠️", "ERR": "❌", "STEP": "🔷"}
    print(f"[{ts}] {icons.get(level,'🔹')} {msg}")


def backup_sqlite(sqlite_path: str) -> str:
    """Tạo bản backup SQLite với timestamp."""
    src = Path(sqlite_path)
    if not src.exists():
        log("WARN", f"File SQLite không tồn tại: {sqlite_path}")
        return ""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = BACKUP_DIR / f"content_manager_backup_{ts}.db"
    shutil.copy2(src, dst)
    log("OK", f"Đã backup SQLite → {dst}")
    return str(dst)


def get_sqlite_conn(path: str):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def get_pg_conn():
    try:
        import psycopg2
        import psycopg2.extras
        return psycopg2.connect(PG_DSN)
    except ImportError:
        log("ERR", "Chưa cài psycopg2. Chạy: pip install psycopg2-binary")
        sys.exit(1)
    except Exception as e:
        log("ERR", f"Không thể kết nối PostgreSQL: {e}")
        sys.exit(1)


# ---------------------------------------------------------
# SCHEMA PostgreSQL
# ---------------------------------------------------------

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS posts (
    id           SERIAL PRIMARY KEY,
    date         TEXT,
    platform     TEXT,
    topic        TEXT,
    content      TEXT,
    status       TEXT,
    content_type TEXT DEFAULT 'Marketing Viral'
);

CREATE TABLE IF NOT EXISTS weekly_schedules (
    id         SERIAL PRIMARY KEY,
    week_start TEXT,
    plan_json  TEXT
);

CREATE TABLE IF NOT EXISTS knowledge_posts (
    id             SERIAL PRIMARY KEY,
    date           TEXT,
    platform       TEXT,
    topic          TEXT,
    audience       TEXT,
    tool_name      TEXT,
    knowledge_type TEXT,
    difficulty     TEXT,
    content        TEXT,
    summary        TEXT,
    status         TEXT
);
"""


def create_schema(pg_conn):
    log("STEP", "Tạo / xác minh schema PostgreSQL...")
    cur = pg_conn.cursor()
    cur.execute(SCHEMA_SQL)
    pg_conn.commit()
    log("OK", "Schema PostgreSQL sẵn sàng.")


# ---------------------------------------------------------
# TABLE DEFINITIONS
# ---------------------------------------------------------

TABLES = {
    "posts": {
        "columns": ["date", "platform", "topic", "content", "status", "content_type"],
        "insert_sql": """
            INSERT INTO posts (date, platform, topic, content, status, content_type)
            VALUES (%s, %s, %s, %s, %s, %s)
        """,
        "check_sql": "SELECT COUNT(*) FROM posts WHERE date=%s AND topic=%s AND content=%s",
    },
    "weekly_schedules": {
        "columns": ["week_start", "plan_json"],
        "insert_sql": """
            INSERT INTO weekly_schedules (week_start, plan_json)
            VALUES (%s, %s)
        """,
        "check_sql": "SELECT COUNT(*) FROM weekly_schedules WHERE week_start=%s AND plan_json=%s",
    },
    "knowledge_posts": {
        "columns": ["date", "platform", "topic", "audience", "tool_name",
                    "knowledge_type", "difficulty", "content", "summary", "status"],
        "insert_sql": """
            INSERT INTO knowledge_posts
                (date, platform, topic, audience, tool_name,
                 knowledge_type, difficulty, content, summary, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        "check_sql": "SELECT COUNT(*) FROM knowledge_posts WHERE date=%s AND topic=%s AND content=%s",
    },
}


# ---------------------------------------------------------
# MIGRATE TABLE
# ---------------------------------------------------------

def migrate_table(table_name: str, sqlite_conn, pg_conn, dry_run: bool = False) -> dict:
    """
    Chuyển dữ liệu từ bảng SQLite sang PostgreSQL.
    Returns: { "total": int, "migrated": int, "skipped": int, "errors": int }
    """
    table_def = TABLES[table_name]
    cols      = table_def["columns"]
    insert_sql = table_def["insert_sql"]
    check_sql  = table_def["check_sql"]

    log("STEP", f"Đang migrate bảng '{table_name}'...")

    # Lấy dữ liệu từ SQLite
    sqlite_cur = sqlite_conn.cursor()
    try:
        sqlite_cur.execute(f"SELECT {', '.join(cols)} FROM {table_name}")
        rows = sqlite_cur.fetchall()
    except sqlite3.OperationalError as e:
        log("WARN", f"Bảng '{table_name}' không tồn tại trong SQLite: {e}. Bỏ qua.")
        return {"total": 0, "migrated": 0, "skipped": 0, "errors": 0}

    total    = len(rows)
    migrated = 0
    skipped  = 0
    errors   = 0

    pg_cur = pg_conn.cursor()

    for row in rows:
        values = tuple(row[col] for col in cols)

        # Kiểm tra trùng lặp (idempotent): dùng 3 cột đầu làm key
        try:
            check_values = values[:3]
            pg_cur.execute(check_sql, check_values)
            count = pg_cur.fetchone()[0]
            if count > 0:
                skipped += 1
                continue
        except Exception:
            pass  # Không rollback ở đây, cứ thử insert

        if dry_run:
            migrated += 1
            continue

        try:
            pg_cur.execute(insert_sql, values)
            migrated += 1
        except Exception as e:
            log("WARN", f"  Lỗi khi insert 1 dòng vào '{table_name}': {e}")
            pg_conn.rollback()
            errors += 1
            # Mở lại cursor sau rollback
            pg_cur = pg_conn.cursor()
            continue

    if not dry_run:
        try:
            pg_conn.commit()
        except Exception as e:
            log("ERR", f"Lỗi commit bảng '{table_name}': {e}")
            pg_conn.rollback()
            errors += total
            return {"total": total, "migrated": 0, "skipped": 0, "errors": errors}

    mode = "[DRY RUN] " if dry_run else ""
    log("OK", f"{mode}Bảng '{table_name}': {migrated} migrated | {skipped} skipped | {errors} errors / {total} total")
    return {"total": total, "migrated": migrated, "skipped": skipped, "errors": errors}


# ---------------------------------------------------------
# VERIFY
# ---------------------------------------------------------

def verify_migration(sqlite_conn, pg_conn) -> bool:
    """So sánh số lượng dòng giữa SQLite và PostgreSQL."""
    log("STEP", "Xác minh dữ liệu sau migration...")
    sqlite_cur = sqlite_conn.cursor()
    pg_cur     = pg_conn.cursor()
    all_ok = True

    for table in TABLES.keys():
        try:
            sqlite_cur.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = sqlite_cur.fetchone()[0]
        except Exception:
            sqlite_count = 0

        try:
            pg_cur.execute(f"SELECT COUNT(*) FROM {table}")
            pg_count = pg_cur.fetchone()[0]
        except Exception:
            pg_count = 0

        match = "✅" if pg_count >= sqlite_count else "⚠️"
        print(f"   {match} {table}: SQLite={sqlite_count} row(s) | PostgreSQL={pg_count} row(s)")
        if pg_count < sqlite_count:
            all_ok = False

    return all_ok


# ---------------------------------------------------------
# REPORT
# ---------------------------------------------------------

def save_report(stats: dict, backup_path: str, dry_run: bool):
    report_path = ROOT / "docs" / "MIGRATION_REPORT.md"
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = [
        f"# Báo cáo Migration SQLite → PostgreSQL",
        f"",
        f"**Thời gian:** {ts}",
        f"**Chế độ:** {'DRY RUN (mô phỏng)' if dry_run else 'THỰC TẾ'}",
        f"**SQLite nguồn:** `{SQLITE_PATH}`",
        f"**PostgreSQL đích:** `{PG_HOST}:{PG_PORT}/{PG_NAME}`",
        f"**File backup SQLite:** `{backup_path}`",
        f"",
        f"## Kết quả theo bảng",
        f"",
        f"| Bảng | Tổng | Đã migrate | Bỏ qua (trùng) | Lỗi |",
        f"|------|------|-----------|----------------|-----|",
    ]

    total_migrated = 0
    total_errors   = 0
    for table, s in stats.items():
        lines.append(
            f"| {table} | {s['total']} | {s['migrated']} | {s['skipped']} | {s['errors']} |"
        )
        total_migrated += s["migrated"]
        total_errors   += s["errors"]

    status = "✅ THÀNH CÔNG" if total_errors == 0 else "⚠️ CÓ LỖI"
    lines += [
        f"",
        f"## Tổng kết",
        f"- **Tổng dòng đã migrate:** {total_migrated}",
        f"- **Tổng lỗi:** {total_errors}",
        f"- **Trạng thái:** {status}",
        f"",
        f"## Bước tiếp theo",
        f"",
        f"Sau khi xác nhận dữ liệu, cập nhật `.env`:",
        f"```",
        f"DB_ENGINE=postgresql",
        f"PG_HOST={PG_HOST}",
        f"PG_PORT={PG_PORT}",
        f"PG_NAME={PG_NAME}",
        f"PG_USER={PG_USER}",
        f"PG_PASSWORD=YOUR_PASSWORD",
        f"```",
    ]

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")
    log("OK", f"Đã lưu báo cáo migration → {report_path}")


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Migration dữ liệu từ SQLite sang PostgreSQL"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Chạy thử (không thực sự ghi vào PostgreSQL)"
    )
    parser.add_argument(
        "--no-backup", action="store_true",
        help="Bỏ qua bước tạo backup SQLite"
    )
    args = parser.parse_args()

    print("=" * 65)
    print("  MIGRATION: SQLite → PostgreSQL")
    print(f"  SQLite   : {SQLITE_PATH}")
    print(f"  PostgreSQL: {PG_HOST}:{PG_PORT}/{PG_NAME}")
    print(f"  Chế độ   : {'DRY RUN 🔍' if args.dry_run else 'THỰC TẾ ⚡'}")
    print("=" * 65)

    # 1. Backup SQLite
    backup_path = ""
    if not args.no_backup and not args.dry_run:
        backup_path = backup_sqlite(SQLITE_PATH)

    # 2. Mở kết nối
    if not Path(SQLITE_PATH).exists():
        log("ERR", f"File SQLite không tồn tại: {SQLITE_PATH}")
        sys.exit(1)

    sqlite_conn = get_sqlite_conn(SQLITE_PATH)
    pg_conn     = get_pg_conn()

    # 3. Tạo schema PostgreSQL
    if not args.dry_run:
        create_schema(pg_conn)

    # 4. Migrate từng bảng
    stats = {}
    try:
        for table in TABLES.keys():
            stats[table] = migrate_table(table, sqlite_conn, pg_conn, dry_run=args.dry_run)
    except Exception as e:
        log("ERR", f"Lỗi nghiêm trọng trong quá trình migration: {e}")
        pg_conn.rollback()
        pg_conn.close()
        sqlite_conn.close()
        sys.exit(1)

    # 5. Xác minh
    if not args.dry_run:
        ok = verify_migration(sqlite_conn, pg_conn)
    else:
        ok = True

    # 6. Lưu báo cáo
    save_report(stats, backup_path, args.dry_run)

    # 7. Đóng kết nối
    pg_conn.close()
    sqlite_conn.close()

    # 8. Tổng kết
    total_errors = sum(s["errors"] for s in stats.values())
    print()
    if total_errors == 0 and ok:
        log("OK", "Migration hoàn tất thành công! ✅")
        print()
        print("👉 Bước tiếp theo:")
        print(f"   1. Cập nhật .env: DB_ENGINE=postgresql")
        print(f"   2. Khởi động lại ứng dụng: streamlit run app/main.py")
    else:
        log("WARN", f"Migration hoàn tất nhưng có {total_errors} lỗi. Kiểm tra docs/MIGRATION_REPORT.md")
        sys.exit(1)


if __name__ == "__main__":
    main()
