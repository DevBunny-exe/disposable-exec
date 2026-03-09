from fastapi import Header, HTTPException
import hashlib
import secrets
from datetime import datetime

from .db import get_conn


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def load_api_keys():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM api_keys").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def find_api_key(raw_key: str):
    key_hash = hash_api_key(raw_key)

    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM api_keys WHERE api_key_hash = ? AND is_active = 1",
        (key_hash,)
    ).fetchone()
    conn.close()

    return dict(row) if row else None


def create_api_key(user_id: str, name: str = "default", plan: str = "Free"):
    raw_key = "exec_live_" + secrets.token_urlsafe(24)
    key_hash = hash_api_key(raw_key)

    conn = get_conn()
    row = conn.execute("SELECT COUNT(*) AS c FROM api_keys").fetchone()
    next_num = row["c"] + 1

    record = {
        "id": f"key_{next_num:03d}",
        "user_id": user_id,
        "name": name,
        "api_key_hash": key_hash,
        "plan": plan,
        "is_active": 1,
        "created_at": datetime.utcnow().isoformat() + "Z",
    }

    conn.execute(
        """
        INSERT INTO api_keys (id, user_id, name, api_key_hash, plan, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            record["id"],
            record["user_id"],
            record["name"],
            record["api_key_hash"],
            record["plan"],
            record["is_active"],
            record["created_at"],
        ),
    )
    conn.commit()
    conn.close()

    return raw_key, record


def disable_api_key(key_id: str):
    conn = get_conn()
    cur = conn.execute(
        "UPDATE api_keys SET is_active = 0 WHERE id = ?",
        (key_id,)
    )
    conn.commit()
    conn.close()
    return cur.rowcount > 0


def verify_api_key(authorization: str = Header(None)):
    if authorization is None:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization format")

    api_key = authorization.split(" ", 1)[1].strip()

    record = find_api_key(api_key)
    if not record:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    record["is_active"] = bool(record["is_active"])
    return record