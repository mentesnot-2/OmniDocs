from dataclasses import dataclass


@dataclass(frozen=True)
class PlanLimits:
    plan_id: str
    name:str
    monthly_queries: int
    storage_mb: int
    monthly_uploads: int


PLANS = {
    "free": PlanLimits(
        plan_id="free",
        name="Free",
        monthly_queries=100,
        storage_mb=100,
        monthly_uploads=20,
    ),
    "pro": PlanLimits(
        plan_id="pro",
        name="Pro",
        monthly_queries=5000,
        storage_mb=5000,
        monthly_uploads=1000,
    )
}

DEFAULT_PLAN_ID = "free"