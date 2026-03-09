from datetime import datetime

from .db import get_conn


def get_period_key() -> str:
    return datetime.utcnow().strftime("%Y-%m")


def get_usage_count(key_id: str, period_key: str | None = None) -> int:
    if period_key is None:
        period_key = get_period_key()

    conn = get_conn()
    row = conn.execute(
        "SELECT execution_count FROM usage_counters WHERE key_id = ? AND period_key = ?",
        (key_id, period_key),
    ).fetchone()
    conn.close()

    return row["execution_count"] if row else 0


def increment_usage(key_id: str, period_key: str | None = None) -> int:
    if period_key is None:
        period_key = get_period_key()

    conn = get_conn()
    row = conn.execute(
        "SELECT execution_count FROM usage_counters WHERE key_id = ? AND period_key = ?",
        (key_id, period_key),
    ).fetchone()

    if row:
        new_count = row["execution_count"] + 1
        conn.execute(
            "UPDATE usage_counters SET execution_count = ? WHERE key_id = ? AND period_key = ?",
            (new_count, key_id, period_key),
        )
    else:
        new_count = 1
        conn.execute(
            "INSERT INTO usage_counters (key_id, period_key, execution_count) VALUES (?, ?, ?)",
            (key_id, period_key, new_count),
        )

    conn.commit()
    conn.close()
    return new_count