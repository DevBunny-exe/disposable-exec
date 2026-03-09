PLAN_QUOTA = {
    "Free": 50,
    "Starter": 3000,
    "Pro": 20000,
    "Scale": 100000,
}


def get_plan_quota(plan: str) -> int:
    return PLAN_QUOTA.get(plan, 0)
