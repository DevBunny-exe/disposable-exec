from fastapi import Header, HTTPException

# 简单 API key 列表 (之后可以换数据库)
VALID_API_KEYS = {
    "test-key-123",
    "dev-key-456"
}

def verify_api_key(authorization: str = Header(None)):
    if authorization is None:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization format")

    api_key = authorization.split(" ")[1]

    if api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    return api_key