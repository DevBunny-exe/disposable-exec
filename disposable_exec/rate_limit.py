import time
from fastapi import HTTPException

# 每个 API key 的调用记录
request_log = {}

# 不同 plan 限速
PLAN_LIMITS = {
    "test-key-123": 10,   # 每分钟10次
    "dev-key-456": 30
}

WINDOW = 60  # 秒


def check_rate_limit(api_key: str):

    now = time.time()

    if api_key not in request_log:
        request_log[api_key] = []

    calls = request_log[api_key]

    # 清理超过时间窗口的请求
    request_log[api_key] = [
        t for t in calls if now - t < WINDOW
    ]

    calls = request_log[api_key]

    limit = PLAN_LIMITS.get(api_key, 5)

    if len(calls) >= limit:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded"
        )

    calls.append(now)