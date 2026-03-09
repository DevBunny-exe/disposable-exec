from datetime import datetime, timedelta

from .db import get_conn
from .plans import get_plan_quota
from .auth import create_api_key
from .billing_providers import extract_billing_event


def upsert_user_by_email(email: str):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,)
    ).fetchone()

    if row:
        conn.close()
        return dict(row)

    count_row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
    user_id = f"user_{count_row['c'] + 1:03d}"

    user = {
        "id": user_id,
        "email": email,
        "status": "active",
        "created_at": datetime.utcnow().isoformat() + "Z",
    }

    conn.execute(
        "INSERT INTO users (id, email, status, created_at) VALUES (?, ?, ?, ?)",
        (user["id"], user["email"], user["status"], user["created_at"]),
    )
    conn.commit()
    conn.close()
    return user


def sync_user_api_keys_plan(user_id: str, plan: str, is_active: bool):
    conn = get_conn()
    conn.execute(
        "UPDATE api_keys SET plan = ?, is_active = ? WHERE user_id = ?",
        (plan, 1 if is_active else 0, user_id),
    )
    conn.commit()
    conn.close()


def upsert_subscription(
    user_id: str,
    provider: str,
    provider_subscription_id: str,
    plan: str,
    status: str = "active",
):
    conn = get_conn()
    row = conn.execute(
        """
        SELECT * FROM subscriptions
        WHERE provider = ? AND provider_subscription_id = ?
        """,
        (provider, provider_subscription_id),
    ).fetchone()

    now = datetime.utcnow()
    quota_monthly = get_plan_quota(plan)

    if row:
        conn.execute(
            """
            UPDATE subscriptions
            SET plan = ?, status = ?, quota_monthly = ?, updated_at = ?
            WHERE provider = ? AND provider_subscription_id = ?
            """,
            (
                plan,
                status,
                quota_monthly,
                now.isoformat() + "Z",
                provider,
                provider_subscription_id,
            ),
        )
        conn.commit()
        updated = conn.execute(
            """
            SELECT * FROM subscriptions
            WHERE provider = ? AND provider_subscription_id = ?
            """,
            (provider, provider_subscription_id),
        ).fetchone()
        conn.close()
        return dict(updated)

    count_row = conn.execute("SELECT COUNT(*) AS c FROM subscriptions").fetchone()
    sub_id = f"sub_{count_row['c'] + 1:03d}"

    sub = {
        "id": sub_id,
        "user_id": user_id,
        "provider": provider,
        "provider_subscription_id": provider_subscription_id,
        "plan": plan,
        "status": status,
        "quota_monthly": quota_monthly,
        "period_start": now.date().isoformat(),
        "period_end": (now.date() + timedelta(days=30)).isoformat(),
        "created_at": now.isoformat() + "Z",
        "updated_at": now.isoformat() + "Z",
    }

    conn.execute(
        """
        INSERT INTO subscriptions
        (id, user_id, provider, provider_subscription_id, plan, status, quota_monthly,
         period_start, period_end, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            sub["id"],
            sub["user_id"],
            sub["provider"],
            sub["provider_subscription_id"],
            sub["plan"],
            sub["status"],
            sub["quota_monthly"],
            sub["period_start"],
            sub["period_end"],
            sub["created_at"],
            sub["updated_at"],
        ),
    )
    conn.commit()
    conn.close()
    return sub


def get_latest_subscription_for_user(user_id: str):
    conn = get_conn()
    row = conn.execute(
        """
        SELECT * FROM subscriptions
        WHERE user_id = ?
        ORDER BY updated_at DESC, created_at DESC
        LIMIT 1
        """,
        (user_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def provision_api_key_if_needed(user_id: str, plan: str):
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM api_keys WHERE user_id = ? LIMIT 1",
        (user_id,),
    ).fetchone()
    conn.close()

    if row:
        return None, dict(row)

    raw_key, record = create_api_key(user_id=user_id, name="default", plan=plan)
    return raw_key, record


def handle_billing_webhook(provider: str, payload: dict):
    event = extract_billing_event(provider, payload)

    user = upsert_user_by_email(event["email"])
    subscription = upsert_subscription(
        user_id=user["id"],
        provider=event["provider"],
        provider_subscription_id=event["provider_subscription_id"],
        plan=event["plan"],
        status=event["status"],
    )

    raw_key, key_record = provision_api_key_if_needed(user["id"], event["plan"])

    is_active = event["status"] == "active"
    sync_user_api_keys_plan(user["id"], event["plan"], is_active)

    latest_key = None
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM api_keys WHERE user_id = ? LIMIT 1",
        (user["id"],),
    ).fetchone()
    conn.close()
    if row:
        latest_key = dict(row)

    return {
        "ok": True,
        "provider": event["provider"],
        "event_type": event["event_type"],
        "user": user,
        "subscription": subscription,
        "api_key_created": raw_key is not None,
        "api_key": raw_key,
        "api_key_record": latest_key or key_record,
    }


def handle_paddle_webhook(payload: dict):
    return handle_billing_webhook("paddle", payload)


def handle_lemon_webhook(payload: dict):
    return handle_billing_webhook("lemon", payload)


def handle_polar_webhook(payload: dict):
    return handle_billing_webhook("polar", payload)


def handle_stripe_webhook(payload: dict):
    return handle_billing_webhook("stripe", payload)