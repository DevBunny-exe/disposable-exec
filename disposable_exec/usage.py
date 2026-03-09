from datetime import datetime

from .storage_utils import load_json, save_json, STORAGE_DIR

USAGE_FILE = STORAGE_DIR / "usage.json"


def get_period_key() -> str:
    return datetime.utcnow().strftime("%Y-%m")


def load_usage():
    return load_json(USAGE_FILE, {})


def save_usage(data):
    save_json(USAGE_FILE, data)


def get_usage_count(key_id: str, period_key: str | None = None) -> int:
    if period_key is None:
        period_key = get_period_key()

    usage = load_usage()
    return usage.get(key_id, {}).get(period_key, 0)


def increment_usage(key_id: str, period_key: str | None = None) -> int:
    if period_key is None:
        period_key = get_period_key()

    usage = load_usage()

    if key_id not in usage:
        usage[key_id] = {}

    usage[key_id][period_key] = usage[key_id].get(period_key, 0) + 1
    save_usage(usage)
    return usage[key_id][period_key]
