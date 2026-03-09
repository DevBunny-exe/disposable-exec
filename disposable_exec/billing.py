from datetime import datetime, timedelta

from .storage_utils import load_json, save_json, STORAGE_DIR
from .plans import get_plan_quota
from .auth import create_api_key

USERS_FILE = STORAGE_DIR / "users.json"
SUBSCRIPTIONS_FILE = STORAGE_DIR / "subscriptions.json"


def load_users():
    return load_json(USERS_FILE, [])


def save_users(data):
    save_json(USERS_FILE, data)


def load_subscriptions():
    return load_json(SUBSCRIPTIONS_FILE, [])


def save_subscriptions(data):
    save_json(SUBSCRIPTIONS_FILE, data)


def upsert_user_by_email(email: str):
    users = load_users()

    for user in users:
        if user.get("email") == email:
            return user

    user = {
        "id": f"user_{len(users) + 1:03d}",
        "email": email,
        "status": "active",
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    users.append(user)
    save_users(users)
    return user


def upsert_subscription(
    user_id: str,
    provider: str,
    provider_subscription_id: str,
    plan: str,
    status: str = "active",
):
    subscriptions = load_subscriptions()

    for sub in subscriptions:
        if sub.get("provider_subscription_id") == provider_subscription_id:
            sub["plan"] = plan
            sub["status"] = status
            sub["quota_monthly"] = get_plan_quota(plan)
            sub["updated_at"] = datetime.utcnow().isoformat() + "Z"
            save_subscriptions(subscriptions)
            return sub

    now = datetime.utcnow()
    sub = {
        "id": f"sub_{len(subscriptions) + 1:03d}",
        "user_id": user_id,
        "provider": provider,
        "provider_subscription_id": provider_subscription_id,
        "plan": plan,
        "status": status,
        "quota_monthly": get_plan_quota(plan),
        "period_start": now.date().isoformat(),
        "period_end": (now.date() + timedelta(days=30)).isoformat(),
        "created_at": now.isoformat() + "Z",
        "updated_at": now.isoformat() + "Z",
    }
    subscriptions.append(sub)
    save_subscriptions(subscriptions)
    return sub


def provision_api_key_if_needed(user_id: str, plan: str):
    from .auth import load_api_keys

    api_keys = load_api_keys()
    for key in api_keys:
        if key.get("user_id") == user_id and key.get("is_active", False):
            return None, key

    raw_key, record = create_api_key(user_id=user_id, name="default", plan=plan)
    return raw_key, record


def handle_paddle_webhook(payload: dict):
    event_type = payload.get("event_type", "unknown")
    data = payload.get("data", {})

    email = data.get("email") or data.get("customer_email") or "unknown@example.com"
    plan = data.get("plan") or "Free"
    provider_subscription_id = data.get("subscription_id") or data.get("id") or "unknown"

    user = upsert_user_by_email(email)
    subscription = upsert_subscription(
        user_id=user["id"],
        provider="paddle",
        provider_subscription_id=provider_subscription_id,
        plan=plan,
        status="active",
    )
    raw_key, key_record = provision_api_key_if_needed(user["id"], plan)

    return {
        "ok": True,
        "event_type": event_type,
        "user": user,
        "subscription": subscription,
        "api_key_created": raw_key is not None,
        "api_key": raw_key,
        "api_key_record": key_record,
    }
