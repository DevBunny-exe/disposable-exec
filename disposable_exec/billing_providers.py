def normalize_plan(plan_value: str) -> str:
    plan = (plan_value or "").strip().lower()

    mapping = {
        "free": "Free",
        "starter": "Starter",
        "pro": "Pro",
        "scale": "Scale",
    }
    return mapping.get(plan, "Free")


def normalize_status(status_value: str) -> str:
    status = (status_value or "").strip().lower()

    if status in {"active", "trialing", "paid"}:
        return "active"
    if status in {"canceled", "cancelled"}:
        return "canceled"
    if status in {"past_due", "paused", "unpaid"}:
        return "past_due"
    return "active"


def extract_billing_event(provider: str, payload: dict) -> dict:
    provider = (provider or "").strip().lower()

    if provider == "paddle":
        data = payload.get("data", {})
        return {
            "provider": "paddle",
            "event_type": payload.get("event_type", "unknown"),
            "email": data.get("email") or data.get("customer_email") or "unknown@example.com",
            "provider_subscription_id": data.get("subscription_id") or data.get("id") or "unknown",
            "plan": normalize_plan(data.get("plan") or "Free"),
            "status": normalize_status(data.get("status") or "active"),
        }

    if provider == "lemon":
        data = payload.get("data", {})
        attrs = data.get("attributes", {})
        return {
            "provider": "lemon",
            "event_type": payload.get("meta", {}).get("event_name", "unknown"),
            "email": attrs.get("user_email") or attrs.get("customer_email") or "unknown@example.com",
            "provider_subscription_id": str(data.get("id") or "unknown"),
            "plan": normalize_plan(attrs.get("product_name") or attrs.get("variant_name") or "Free"),
            "status": normalize_status(attrs.get("status") or "active"),
        }

    if provider == "polar":
        data = payload.get("data", {})
        return {
            "provider": "polar",
            "event_type": payload.get("type", "unknown"),
            "email": data.get("customer_email") or data.get("email") or "unknown@example.com",
            "provider_subscription_id": str(data.get("subscription_id") or data.get("id") or "unknown"),
            "plan": normalize_plan(data.get("plan") or data.get("product") or "Free"),
            "status": normalize_status(data.get("status") or "active"),
        }

    if provider == "stripe":
        data = payload.get("data", {}).get("object", {})
        return {
            "provider": "stripe",
            "event_type": payload.get("type", "unknown"),
            "email": data.get("customer_email") or "unknown@example.com",
            "provider_subscription_id": str(data.get("id") or "unknown"),
            "plan": normalize_plan(data.get("plan", {}).get("nickname") or "Free"),
            "status": normalize_status(data.get("status") or "active"),
        }

    raise ValueError(f"Unsupported billing provider: {provider}")