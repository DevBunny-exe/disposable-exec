from fastapi import FastAPI, HTTPException, Depends

from .auth import verify_api_key, create_api_key, disable_api_key
from .plans import get_plan_quota
from .usage import get_usage_count, increment_usage
from .billing import (
    handle_paddle_webhook,
    handle_lemon_webhook,
    handle_polar_webhook,
    handle_stripe_webhook,
    get_latest_subscription_for_user,
)
from .queue import enqueue_job
from .status import get_status
from .results import get_result
from .db import get_conn
from .rate_limit import check_and_increment_rate_limit

app = FastAPI(title="Disposable Exec API")


RUN_RATE_LIMIT_PER_MIN = 20
READ_RATE_LIMIT_PER_MIN = 60


def enforce_rate_limit(api_key: dict, route: str, limit: int):
    key_id = api_key.get("id")
    if not key_id:
        raise HTTPException(status_code=500, detail="API key record missing id")

    info = check_and_increment_rate_limit(key_id, route, limit)

    if not info["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded for {route}: {info['count']}/{info['limit']} in current minute"
        )


@app.get("/")
def root():
    return {"ok": True, "service": "disposable-exec"}


@app.post("/run")
def run_code(payload: dict, api_key=Depends(verify_api_key)):
    enforce_rate_limit(api_key, "/run", RUN_RATE_LIMIT_PER_MIN)

    script = payload.get("script")
    if not script:
        raise HTTPException(status_code=400, detail="Missing script")

    plan = api_key.get("plan", "Free")
    key_id = api_key.get("id")
    user_id = api_key.get("user_id")
    is_active = bool(api_key.get("is_active", 0))

    if not key_id:
        raise HTTPException(status_code=500, detail="API key record missing id")

    if not is_active:
        raise HTTPException(status_code=403, detail="API key is inactive")

    subscription = get_latest_subscription_for_user(user_id) if user_id else None

    if subscription:
        sub_status = subscription.get("status", "active")
        sub_plan = subscription.get("plan", plan)

        if sub_status != "active":
            raise HTTPException(status_code=403, detail=f"Subscription is not active: {sub_status}")

        plan = sub_plan

    quota = get_plan_quota(plan)
    used = get_usage_count(key_id)

    if used >= quota:
        raise HTTPException(status_code=403, detail="Monthly execution quota exceeded")

    job = enqueue_job(script, key_id)
    increment_usage(key_id)

    return {
        "execution_id": job["execution_id"],
        "plan": plan,
        "used": used + 1,
        "quota": quota,
    }


@app.get("/status/{execution_id}")
def status(execution_id: str, api_key=Depends(verify_api_key)):
    enforce_rate_limit(api_key, "/status", READ_RATE_LIMIT_PER_MIN)

    data = get_status(execution_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return data


@app.get("/result/{execution_id}")
def result(execution_id: str, api_key=Depends(verify_api_key)):
    enforce_rate_limit(api_key, "/result", READ_RATE_LIMIT_PER_MIN)

    data = get_result(execution_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return data


@app.get("/me")
def me(api_key=Depends(verify_api_key)):
    enforce_rate_limit(api_key, "/me", READ_RATE_LIMIT_PER_MIN)

    user_id = api_key.get("user_id")
    subscription = get_latest_subscription_for_user(user_id) if user_id else None

    return {
        "api_key_id": api_key.get("id"),
        "user_id": user_id,
        "plan": api_key.get("plan"),
        "is_active": bool(api_key.get("is_active", 0)),
        "subscription": subscription,
    }


@app.get("/apikey")
def list_api_keys(api_key=Depends(verify_api_key)):
    enforce_rate_limit(api_key, "/apikey:list", READ_RATE_LIMIT_PER_MIN)

    user_id = api_key.get("user_id")

    conn = get_conn()
    rows = conn.execute(
        """
        SELECT id, user_id, name, plan, is_active, created_at
        FROM api_keys
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user_id,),
    ).fetchall()
    conn.close()

    keys = []
    for row in rows:
        item = dict(row)
        item["is_active"] = bool(item["is_active"])
        keys.append(item)

    return {"items": keys}


@app.post("/apikey")
def create_api_key_endpoint(payload: dict, api_key=Depends(verify_api_key)):
    enforce_rate_limit(api_key, "/apikey:create", 10)

    user_id = api_key.get("user_id")
    name = payload.get("name", "default")
    plan = api_key.get("plan", "Free")

    raw_key, record = create_api_key(user_id=user_id, name=name, plan=plan)
    record["is_active"] = bool(record["is_active"])

    return {
        "api_key": raw_key,
        "record": record,
    }


@app.delete("/apikey/{key_id}")
def disable_api_key_endpoint(key_id: str, api_key=Depends(verify_api_key)):
    enforce_rate_limit(api_key, "/apikey:disable", 10)

    user_id = api_key.get("user_id")

    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM api_keys WHERE id = ? AND user_id = ?",
        (key_id, user_id),
    ).fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="API key not found")

    ok = disable_api_key(key_id)
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to disable API key")

    return {"ok": True, "disabled_key_id": key_id}


@app.get("/admin/users")
def admin_users():
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, email, status, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()
    conn.close()

    return {"items": [dict(r) for r in rows]}


@app.get("/admin/subscriptions")
def admin_subscriptions():
    conn = get_conn()
    rows = conn.execute(
        """
        SELECT id, user_id, provider, provider_subscription_id, plan, status,
               quota_monthly, period_start, period_end, created_at, updated_at
        FROM subscriptions
        ORDER BY updated_at DESC, created_at DESC
        """
    ).fetchall()
    conn.close()

    return {"items": [dict(r) for r in rows]}


@app.post("/billing/webhook/paddle")
def billing_webhook_paddle(payload: dict):
    return handle_paddle_webhook(payload)


@app.post("/billing/webhook/lemon")
def billing_webhook_lemon(payload: dict):
    return handle_lemon_webhook(payload)


@app.post("/billing/webhook/polar")
def billing_webhook_polar(payload: dict):
    return handle_polar_webhook(payload)


@app.post("/billing/webhook/stripe")
def billing_webhook_stripe(payload: dict):
    return handle_stripe_webhook(payload)