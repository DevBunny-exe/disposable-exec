PLAN_QUOTA = {
    "Free": 50,
    "Starter": 3000,
    "Pro": 12000,
    "Scale": 40000,
}


def get_plan_quota(plan: str) -> int:
    return PLAN_QUOTA.get(plan, 0)