from datetime import datetime

from .db import get_conn


def init_rate_limit_table():
    conn = get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS rate_limits (
            key_id TEXT,
            route TEXT,
            window_key TEXT,
            request_count INTEGER,
            PRIMARY KEY (key_id, route, window_key)
        )
        """
    )
    conn.commit()
    conn.close()


def get_minute_window_key() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M")


def check_and_increment_rate_limit(key_id: str, route: str, limit: int) -> dict:
    window_key = get_minute_window_key()

    conn = get_conn()
    row = conn.execute(
        """
        SELECT request_count
        FROM rate_limits
        WHERE key_id = ? AND route = ? AND window_key = ?
        """,
        (key_id, route, window_key),
    ).fetchone()

    if row:
        new_count = row["request_count"] + 1
        conn.execute(
            """
            UPDATE rate_limits
            SET request_count = ?
            WHERE key_id = ? AND route = ? AND window_key = ?
            """,
            (new_count, key_id, route, window_key),
        )
    else:
        new_count = 1
        conn.execute(
            """
            INSERT INTO rate_limits (key_id, route, window_key, request_count)
            VALUES (?, ?, ?, ?)
            """,
            (key_id, route, window_key, new_count),
        )

    conn.commit()
    conn.close()

    return {
        "allowed": new_count <= limit,
        "count": new_count,
        "limit": limit,
        "window_key": window_key,
    }


init_rate_limit_table()