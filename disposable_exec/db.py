import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = STORAGE_DIR / "app.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        email TEXT UNIQUE,
        status TEXT,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS api_keys (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        name TEXT,
        api_key_hash TEXT UNIQUE,
        plan TEXT,
        is_active INTEGER,
        created_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id TEXT PRIMARY KEY,
        user_id TEXT,
        provider TEXT,
        provider_subscription_id TEXT UNIQUE,
        plan TEXT,
        status TEXT,
        quota_monthly INTEGER,
        period_start TEXT,
        period_end TEXT,
        created_at TEXT,
        updated_at TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS usage_counters (
        key_id TEXT,
        period_key TEXT,
        execution_count INTEGER,
        PRIMARY KEY (key_id, period_key)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS execution_status (
        execution_id TEXT PRIMARY KEY,
        status TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS execution_results (
        execution_id TEXT PRIMARY KEY,
        stdout TEXT,
        stderr TEXT,
        exit_code INTEGER,
        duration REAL
    )
    """)

    conn.commit()
    conn.close()


init_db()