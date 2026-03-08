from disposable_exec.usage import load_usage

# API key → plan
API_KEYS = {
    "test-key-123": "Free",
    "dev-key-456": "Starter"
}

# plan → quota
PLAN_QUOTA = {
    "Free": 50,
    "Starter": 3000,
    "Pro": 20000,
    "Scale": 100000
}

def get_plan_quota(plan: str) -> int:
    return PLAN_QUOTA.get(plan, 0)

def check_quota(api_key):
    usage = load_usage()
    used = usage.get(api_key, 0)

    plan = API_KEYS.get(api_key, "Free")
    quota = get_plan_quota(plan)

    return used < quota
