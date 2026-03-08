from fastapi import Header, HTTPException
import json
import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
API_KEYS_FILE = BASE_DIR / "storage" / "api_keys.json"


def load_api_keys():
    if not API_KEYS_FILE.exists():
        return []
    with open(API_KEYS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode()).hexdigest()


def find_api_key(raw_key: str):
    api_keys = load_api_keys()
    key_hash = hash_api_key(raw_key)

    for record in api_keys:
        if record.get("api_key_hash") == key_hash and record.get("is_active", False):
            return record
    return None


def verify_api_key(authorization: str = Header(None)):
    if authorization is None:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization format")

    api_key = authorization.split(" ")[1]

    record = find_api_key(api_key)
    if not record:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    return record
