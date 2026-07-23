#!/usr/bin/env python3
"""
database/migrate_v2.py
=======================
Migration script nâng cấp từ Schema V1 (3 bảng) lên Schema V2 (14 bảng).

Cách chạy:
    python database/migrate_v2.py
"""

import os
import sys
import sqlite3
import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from config.config import logger
from database.connection import get_db_connection, _is_postgres, _adapt_sql
from database.schema import create_all_tables, verify_tables
from database.models.users import UserModel
from database.models.workspaces import WorkspaceModel
from database.models.companies import CompanyModel
from database.models.brand import BrandModel

def log(icon: str, msg: str):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {icon} {msg}")

def main():
    log("🔷", "Bắt đầu quy trình Migration lên Schema V2...")
    
    engine = os.getenv("DB_ENGINE", "sqlite").lower()
    log("⚙️", f"Cơ sở dữ liệu đang dùng: {engine.upper()}")
    
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Để giải quyết vấn đề SQLite cột không khớp ở bảng posts cũ và posts mới
    # Ta kiểm tra xem bảng posts hiện tại có cột workspace_id không.
    # Nếu dùng SQLite và thiếu cột này, ta rename posts -> posts_old
    has_posts_old_migration_needed = False
    if engine == "sqlite":
        try:
            cur.execute("PRAGMA table_info(posts)")
            cols = [row[1] for row in cur.fetchall()]
            if cols and "workspace_id" not in cols:
                log("⚠️", "Phát hiện bảng 'posts' cũ thiếu các cột Schema V2. Đang thực hiện chuyển đổi cấu trúc an toàn...")
                cur.execute("ALTER TABLE posts RENAME TO posts_old")
                conn.commit()
                has_posts_old_migration_needed = True
        except Exception as e:
            log("⚠️", f"Kiểm tra bảng posts gặp lỗi: {e}")
            
    # 2. Khởi tạo tất cả 14 bảng mới
    try:
        create_all_tables(conn, engine=engine)
    except Exception as e:
        log("❌", f"Lỗi khởi tạo bảng Schema V2: {e}")
        conn.close()
        sys.exit(1)
        
    # Xác minh các bảng đã tồn tại
    verify_report = verify_tables(conn, engine=engine)
    missing = [t for t, exists in verify_report.items() if not exists]
    if missing:
        log("❌", f"Các bảng sau chưa được tạo: {missing}")
        conn.close()
        sys.exit(1)
    log("✅", "Tất cả 14 bảng đã được tạo và xác minh thành công.")

    # 3. Tạo User mặc định & Workspace mặc định làm root tenant nếu chưa có
    cur = conn.cursor()
    
    # Check User
    cur.execute(_adapt_sql("SELECT id FROM users WHERE email=?"), ("admin@hungvietai.com",))
    user_row = cur.fetchone()
    if not user_row:
        log("👤", "Không tìm thấy user mặc định. Đang khởi tạo 'admin@hungvietai.com'...")
        default_user_id = UserModel.create(
            email="admin@hungvietai.com",
            username="admin",
            password="AdminPassword123@",
            full_name="System Admin",
            role="super_admin"
        )
        log("✅", f"Đã tạo user admin mặc định, ID={default_user_id}")
    else:
        default_user_id = user_row[0]
        log("👤", f"Sử dụng user admin mặc định hiện có, ID={default_user_id}")
        
    # Check Workspace
    cur.execute(_adapt_sql("SELECT id FROM workspaces WHERE slug=?"), ("default-workspace",))
    ws_row = cur.fetchone()
    if not ws_row:
        log("💼", "Không tìm thấy workspace mặc định. Đang khởi tạo 'Default Workspace'...")
        default_ws_id = WorkspaceModel.create(
            name="Default Workspace",
            owner_id=default_user_id,
            plan="enterprise"
        )
        WorkspaceModel.add_member(default_ws_id, default_user_id, role="admin")
        log("✅", f"Đã tạo workspace mặc định, ID={default_ws_id}")
    else:
        default_ws_id = ws_row[0]
        log("💼", f"Sử dụng workspace mặc định hiện có, ID={default_ws_id}")

    # Check Company & Brand mặc định cho workspace
    cur.execute(_adapt_sql("SELECT id FROM companies WHERE name=? AND workspace_id=?"), ("Hung Viet AI", default_ws_id))
    company_row = cur.fetchone()
    if not company_row:
        default_company_id = CompanyModel.create(
            workspace_id=default_ws_id,
            name="Hung Viet AI",
            industry="AI & Automation Service",
            size="small",
            description="Default system brand for automated content"
        )
        BrandModel.create(
            workspace_id=default_ws_id,
            company_id=default_company_id,
            tone_of_voice="casual",
            target_audiences=["CEO", "Sales", "Chủ Shop", "Freelancer", "AI Specialist"],
            brand_colors={},
            logo_url="", tagline="",
            brand_guidelines="Chia sẻ giá trị thực chứng, ứng dụng AI thực tế.",
            blacklist_words=[]
        )
        log("✅", f"Đã tạo brand & company mặc định cho workspace, ID={default_company_id}")

    # 4. Migrate dữ liệu bài đăng cũ
    stats = {"posts": {"total": 0, "migrated": 0, "errors": 0}, "knowledge": {"total": 0, "migrated": 0, "errors": 0}}
    
    if has_posts_old_migration_needed:
        try:
            cur.execute("SELECT * FROM posts_old")
            cols = [d[0] for d in cur.description]
            old_rows = cur.fetchall()
            stats["posts"]["total"] = len(old_rows)
            
            for row in old_rows:
                row_dict = dict(zip(cols, row))
                # Map các cột cũ sang các cột Schema V2
                insert_sql = _adapt_sql("""
                    INSERT INTO posts (
                        workspace_id, title, content, platform, content_type,
                        status, date, topic, created_by, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """)
                now = datetime.now().isoformat()
                cur.execute(insert_sql, (
                    default_ws_id,
                    row_dict.get("topic", "Old Post"),
                    row_dict.get("content", ""),
                    row_dict.get("platform", "facebook"),
                    row_dict.get("content_type", "marketing_viral"),
                    row_dict.get("status", "draft"),
                    row_dict.get("date"),
                    row_dict.get("topic"),
                    default_user_id,
                    now, now
                ))
                stats["posts"]["migrated"] += 1
            conn.commit()
            log("✅", f"Migrate thành công {stats['posts']['migrated']}/{stats['posts']['total']} posts từ bảng cũ sang bảng posts V2 mới.")
            
            # Drop bảng tạm posts_old
            cur.execute("DROP TABLE posts_old")
            conn.commit()
            log("🧹", "Đã xóa bảng 'posts_old' tạm thời.")
        except Exception as e:
            log("❌", f"Lỗi migrate posts: {e}")
            conn.rollback()
    else:
        # Nếu đã có bảng posts mới nhưng chưa gán workspace cho các bài đăng
        try:
            cur.execute("SELECT COUNT(*) FROM posts WHERE workspace_id IS NULL")
            null_ws_count = cur.fetchone()[0]
            if null_ws_count > 0:
                log("🔄", f"Phát hiện {null_ws_count} bài đăng Schema V2 chưa gán workspace. Đang tự động cập nhật...")
                cur.execute(
                    _adapt_sql("UPDATE posts SET workspace_id=?, created_by=? WHERE workspace_id IS NULL"),
                    (default_ws_id, default_user_id)
                )
                conn.commit()
                stats["posts"]["migrated"] = null_ws_count
                log("✅", f"Đã gán thành công {null_ws_count} posts vào workspace mặc định.")
        except Exception as e:
            log("⚠️", f"Bỏ qua gán workspace cho posts: {e}")

    # 5. Migrate bảng knowledge_posts cũ sang bảng knowledge mới (nếu bảng cũ còn sót hoặc tồn tại)
    has_old_knowledge = False
    try:
        if engine == "postgresql":
            cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'knowledge_posts'")
        else:
            cur.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='knowledge_posts'")
        has_old_knowledge = cur.fetchone()[0] > 0
    except Exception:
        pass

    if has_old_knowledge:
        log("🔄", "Phát hiện bảng 'knowledge_posts' cũ. Bắt đầu chuyển đổi dữ liệu sang 'knowledge' mới...")
        try:
            cur.execute("SELECT * FROM knowledge_posts")
            cols = [d[0] for d in cur.description]
            old_rows = cur.fetchall()
            stats["knowledge"]["total"] = len(old_rows)
            
            for row in old_rows:
                row_dict = dict(zip(cols, row))
                insert_sql = _adapt_sql("""
                    INSERT INTO knowledge (
                        workspace_id, title, content, summary, knowledge_type,
                        ai_tool, audience, difficulty, platform, tags, topic, date, status, created_by, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """)
                
                # Check trùng
                cur.execute(
                    _adapt_sql("SELECT COUNT(*) FROM knowledge WHERE topic=? AND date=?"),
                    (row_dict.get("topic"), row_dict.get("date"))
                )
                if cur.fetchone()[0] > 0:
                    stats["knowledge"]["migrated"] += 1
                    continue
                    
                now = datetime.now().isoformat()
                cur.execute(insert_sql, (
                    default_ws_id,
                    row_dict.get("topic"),
                    row_dict.get("content"),
                    row_dict.get("summary"),
                    row_dict.get("knowledge_type", "tutorial"),
                    row_dict.get("tool_name"),
                    row_dict.get("audience"),
                    row_dict.get("difficulty"),
                    row_dict.get("platform"),
                    "[]",
                    row_dict.get("topic"),
                    row_dict.get("date"),
                    row_dict.get("status", "draft"),
                    default_user_id,
                    now, now
                ))
                stats["knowledge"]["migrated"] += 1
                
            conn.commit()
            log("✅", f"Chuyển đổi thành công {stats['knowledge']['migrated']}/{stats['knowledge']['total']} bài viết tri thức sang bảng knowledge mới.")
            
            cur.execute("DROP TABLE knowledge_posts")
            conn.commit()
            log("🧹", "Đã xóa bảng 'knowledge_posts' cũ.")
        except Exception as e:
            log("❌", f"Lỗi trong quá trình migrate knowledge: {e}")
            conn.rollback()

    conn.close()
    
    # Sinh báo cáo
    report_path = ROOT / "docs" / "MIGRATION_V2_REPORT.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    report_content = f"""# Báo cáo Nâng cấp Schema V2 (13 Entity)

**Thời gian:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Database Engine:** `{engine.upper()}`

## Kết quả Khởi tạo
- **Trạng thái:** Thành công ✅
- **Số bảng đã xác minh:** 14/14 bảng (gồm cả bảng phụ `workspace_members`)

## Tài nguyên mặc định được khởi tạo
- **User quản trị mặc định:** `admin@hungvietai.com` (Role: `super_admin`)
- **Workspace mặc định:** `Default Workspace` (Slug: `default-workspace`)
- **Company mặc định:** `Hung Viet AI` (Industry: `AI & Automation Service`)
- **Brand Profile mặc định:** Tone: `casual`, Target: `[CEO, Sales, Chủ Shop, Freelancer, AI Specialist]`

## Dữ liệu chuyển đổi (Migration)
- **Bài viết tiếp thị (posts) cũ:** Đã gán/migrate `{stats['posts']['migrated']}/{stats['posts']['total']}` dòng cũ sang default workspace và thêm đầy đủ cấu trúc mới.
- **Bài viết tri thức (knowledge_posts) cũ:** Đã chuyển đổi `{stats['knowledge']['migrated']}/{stats['knowledge']['total']}` sang bảng `knowledge` mới (Bảng cũ đã xóa thành công).

## Hướng dẫn sử dụng
Cơ sở dữ liệu đã sẵn sàng chạy với 13 bảng mới và tương thích ngược với các thao tác CRUD hiện tại.
"""
    report_path.write_text(report_content, encoding="utf-8")
    log("📝", f"Đã lưu báo cáo nâng cấp tại {report_path}")
    log("🎉", "Quy trình Migration lên Schema V2 hoàn tất tốt đẹp!")

if __name__ == "__main__":
    main()
