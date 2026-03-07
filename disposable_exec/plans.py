from disposable_exec.usage import load_usage

# API key → plan
API_KEYS = {
    "test-key-123": "Free",
    "dev-key-456": "Starter"
}

# plan → quota
PLAN_QUOTA = {
    "Free": 50,
    "Starter": 5000,
    "Pro": 30000,
    "Scale": 150000
}


def check_quota(api_key):

    usage = load_usage()

    used = usage.get(api_key, 0)

    plan = API_KEYS.get(api_key, "Free")

    quota = PLAN_QUOTA[plan]

    if used >= quota:
        return False, quota, used

    return True, quota, used