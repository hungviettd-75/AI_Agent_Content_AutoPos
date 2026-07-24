"""database/models/ai_cost.py — DAO quản lý chi phí & tài nguyên cuộc gọi AI (Gemini, Claude, GPT)."""
from datetime import datetime, timedelta
import random
from database.connection import managed_connection, get_db_connection, _adapt_sql, _is_postgres
from config.config import logger

class AICostModel:

    @staticmethod
    def ensure_table():
        """Tao bang ai_logs dung cu phap cho SQLite va PostgreSQL."""
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            if _is_postgres():
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ai_logs (
                        id                SERIAL PRIMARY KEY,
                        workspace_id      INTEGER REFERENCES workspaces(id) ON DELETE CASCADE,
                        provider          TEXT NOT NULL,
                        model_name        TEXT NOT NULL,
                        prompt_tokens     INTEGER DEFAULT 0,
                        completion_tokens INTEGER DEFAULT 0,
                        total_tokens      INTEGER DEFAULT 0,
                        cost              NUMERIC(12,6) DEFAULT 0.0,
                        latency_ms        INTEGER DEFAULT 0,
                        feature           TEXT,
                        status            TEXT NOT NULL DEFAULT 'success',
                        created_at        TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
            else:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ai_logs (
                        id                INTEGER PRIMARY KEY AUTOINCREMENT,
                        workspace_id      INTEGER,
                        provider          TEXT NOT NULL,
                        model_name        TEXT NOT NULL,
                        prompt_tokens     INTEGER DEFAULT 0,
                        completion_tokens INTEGER DEFAULT 0,
                        total_tokens      INTEGER DEFAULT 0,
                        cost              REAL DEFAULT 0.0,
                        latency_ms        INTEGER DEFAULT 0,
                        feature           TEXT,
                        status            TEXT NOT NULL DEFAULT 'success',
                        created_at        TEXT DEFAULT (datetime('now'))
                    )
                """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ai_logs_workspace ON ai_logs(workspace_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_ai_logs_provider ON ai_logs(provider)")
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"[AI_COST] Khong the tao bang ai_logs: {e}", exc_info=True)
        finally:
            conn.close()

    @staticmethod
    def log(workspace_id: int, provider: str, model_name: str,
            prompt_tokens: int, completion_tokens: int, cost: float,
            latency_ms: int, feature: str = "", status: str = "success") -> bool:
        """Ghi nhận log giao dịch API và chi phí vào cơ sở dữ liệu."""
        sql = _adapt_sql("""
            INSERT INTO ai_logs (
                workspace_id, provider, model_name, prompt_tokens,
                completion_tokens, total_tokens, cost, latency_ms,
                feature, status, created_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """)
        total = prompt_tokens + completion_tokens
        now = datetime.now().isoformat()
        AICostModel.ensure_table()
        with managed_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (
                workspace_id, provider, model_name, prompt_tokens,
                completion_tokens, total, cost, latency_ms, feature, status, now
            ))
            return cur.rowcount > 0

    @staticmethod
    def get_summary(workspace_id: int, days: int = 30) -> list:
        """Lay log AI; tu tao bang neu deployment cu con thieu."""
        AICostModel.ensure_table()
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        sql = _adapt_sql("""
            SELECT * FROM ai_logs
            WHERE workspace_id = ? AND created_at >= ?
            ORDER BY created_at DESC
        """)
        for attempt in range(2):
            conn = get_db_connection()
            try:
                cur = conn.cursor()
                cur.execute(sql, (workspace_id, cutoff))
                cols = [d[0] for d in cur.description]
                return [dict(zip(cols, r)) for r in cur.fetchall()]
            except Exception as exc:
                conn.rollback()
                if attempt == 0 and "ai_logs" in str(exc).lower():
                    logger.warning(f"[AI_COST] ai_logs missing on read, creating table then retrying: {exc}")
                    AICostModel.ensure_table()
                    continue
                raise
            finally:
                conn.close()
        return []

    @staticmethod
    def get_metrics_by_provider(workspace_id: int, days: int = 30) -> list:
        """Thong ke provider; tu tao bang neu deployment cu con thieu."""
        AICostModel.ensure_table()
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        sql = _adapt_sql("""
            SELECT provider,
                   SUM(total_tokens) as total_tokens,
                   SUM(cost) as total_cost,
                   AVG(latency_ms) as avg_latency,
                   COUNT(*) as call_count
            FROM ai_logs
            WHERE workspace_id = ? AND created_at >= ?
            GROUP BY provider
        """)
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute(sql, (workspace_id, cutoff))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r)) for r in cur.fetchall()]
        finally:
            conn.close()

    @staticmethod
    def generate_mock_data(workspace_id: int):
        """Giả lập dữ liệu cho AI Cost Center (Gemini, Claude, GPT)."""
        providers = {
            "Gemini": ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"],
            "Claude": ["claude-3-5-sonnet", "claude-3-haiku", "claude-3-opus"],
            "GPT": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
        }
        features = ["Weekly Plan", "Social Writer", "Fact Check", "Niche Analyzer", "Viral Evaluator", "Refine Chat"]
        now = datetime.now()
        
        # Tạo 80 bản ghi trong 15 ngày qua
        count = 0
        for _ in range(80):
            prov = random.choice(list(providers.keys()))
            model = random.choice(providers[prov])
            feat = random.choice(features)
            
            p_tok = random.randint(1000, 8000)
            c_tok = random.randint(300, 3000)
            
            # Tính cost giả lập thực tế theo $ USD
            if "flash" in model or "mini" in model or "haiku" in model:
                cost = (p_tok * 0.075 + c_tok * 0.3) / 1_000_000 # Rẻ
                latency = random.randint(400, 1500)
            elif "pro" in model or "sonnet" in model or "gpt-4o" == model:
                cost = (p_tok * 3.0 + c_tok * 15.0) / 1_000_000 # Trung bình
                latency = random.randint(1200, 3500)
            else:
                cost = (p_tok * 15.0 + c_tok * 75.0) / 1_000_000 # Đắt (Claude Opus/GPT-4)
                latency = random.randint(3000, 9000)

            # Random ngày
            days_ago = random.randint(0, 14)
            date_str = (now - timedelta(days=days_ago, hours=random.randint(0, 23))).isoformat()

            sql = _adapt_sql("""
                INSERT INTO ai_logs (workspace_id, provider, model_name, prompt_tokens,
                completion_tokens, total_tokens, cost, latency_ms, feature, status, created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """)
            with managed_connection() as conn:
                c = conn.cursor()
                c.execute(sql, (workspace_id, prov, model, p_tok, c_tok, p_tok+c_tok, cost, latency, feat, "success", date_str))
                count += 1
        return count
