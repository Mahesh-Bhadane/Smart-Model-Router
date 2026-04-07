# database.py — PostgreSQL connection and request logging
#
# WHAT IS POSTGRESQL?
# A database is like a structured spreadsheet that lives on your computer.
# PostgreSQL is one of the most popular databases — reliable, fast, and free.
#
# WHAT IS A CONNECTION POOL?
# Opening a new database connection for every request is slow.
# A "pool" keeps a few connections open and reuses them — much faster.
# Think of it like having 5 checkout lanes open at a grocery store
# instead of opening a new lane for every customer.

import psycopg2
from psycopg2 import pool
from app.config import settings

# Global connection pool — created once when the app starts
_pool: pool.SimpleConnectionPool = None


def get_pool() -> pool.SimpleConnectionPool:
    """Return the connection pool, creating it if it doesn't exist yet."""
    global _pool
    if _pool is None:
        _pool = pool.SimpleConnectionPool(
            minconn=1,    # Keep at least 1 connection open
            maxconn=5,    # Allow up to 5 simultaneous connections
            host=settings.db_host,
            port=settings.db_port,
            dbname=settings.db_name,
            user=settings.db_user,
            password=settings.db_password,
        )
    return _pool


def init_db():
    """
    Create the request_logs table if it doesn't exist.
    Called once when the API server starts up.
    """
    conn = get_pool().getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS request_logs (
                    id               SERIAL PRIMARY KEY,
                    prompt           TEXT          NOT NULL,
                    difficulty       VARCHAR(20)   NOT NULL,
                    model_used       VARCHAR(50)   NOT NULL,
                    response         TEXT,
                    cost             DECIMAL(10,6) DEFAULT 0,
                    response_time_ms INTEGER,
                    created_at       TIMESTAMP     DEFAULT NOW()
                )
            """)
            conn.commit()
            print("[database] Table 'request_logs' is ready.")
    finally:
        # Always return the connection back to the pool when done
        get_pool().putconn(conn)


def log_request(
    prompt: str,
    difficulty: str,
    model_used: str,
    response: str,
    cost: float,
    response_time_ms: int,
):
    """Save one request to the database."""
    conn = get_pool().getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO request_logs
                    (prompt, difficulty, model_used, response, cost, response_time_ms)
                VALUES
                    (%s, %s, %s, %s, %s, %s)
                """,
                (prompt, difficulty, model_used, response, cost, response_time_ms),
            )
            conn.commit()
    finally:
        get_pool().putconn(conn)


def get_logs(limit: int = 20, offset: int = 0) -> list[dict]:
    """Fetch recent request logs (paginated)."""
    conn = get_pool().getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, prompt, difficulty, model_used, cost,
                       response_time_ms, created_at
                FROM request_logs
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
            rows = cur.fetchall()
            # Convert each row (a tuple) into a dict for easy JSON serialization
            columns = ["id", "prompt", "difficulty", "model_used",
                       "cost", "response_time_ms", "created_at"]
            return [dict(zip(columns, row)) for row in rows]
    finally:
        get_pool().putconn(conn)


def get_stats() -> dict:
    """Aggregate stats for the cost dashboard."""
    conn = get_pool().getconn()
    try:
        with conn.cursor() as cur:
            # Count requests and sum costs, grouped by difficulty tier
            cur.execute("""
                SELECT
                    difficulty,
                    COUNT(*)        AS total,
                    SUM(cost)       AS actual_cost
                FROM request_logs
                GROUP BY difficulty
            """)
            rows = cur.fetchall()

            by_tier = {}
            total_requests = 0
            actual_cost = 0.0

            for difficulty, count, tier_cost in rows:
                by_tier[difficulty] = int(count)
                total_requests += int(count)
                actual_cost += float(tier_cost or 0)

            return {
                "total_requests": total_requests,
                "by_tier": by_tier,
                "actual_cost": round(actual_cost, 6),
            }
    finally:
        get_pool().putconn(conn)
