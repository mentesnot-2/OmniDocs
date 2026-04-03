from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session


from api.models import UsageEvent, User
from api.storage import dir_size_bytes
from config import UPLOAD_DIR
from config.plans import PLANS, DEFAULT_PLAN_ID


def _plan(user:User):
    return PLANS.get(user.plan_id or DEFAULT_PLAN_ID, PLANS[DEFAULT_PLAN_ID])


def get_plan_limits(user: User):
    """Return resolved plan limits for a user."""
    return _plan(user)


def get_plan_storage_limit_bytes(user: User) -> int:
    """Return storage limit in bytes for the user's active plan."""
    return _plan(user).storage_mb * 1024 * 1024



def enforce_query_limit(db: Session, user: User):
    plan = _plan(user)
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    count  = (
        db.query(func.count(UsageEvent.id))
        .filter(
            UsageEvent.user_id == user.id,
            UsageEvent.event_type == "query",
            UsageEvent.created_at >= month_start,
        )
        .scalar() 
    ) or 0

    if count >= plan.monthly_queries:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly query limit reached for {plan.name} plan."
        )

def enforce_upload_limit(db: Session, user: User):
    plan = _plan(user)
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    count = (
        db.query(func.count(UsageEvent.id))
        .filter(
            UsageEvent.user_id == user.id,
            UsageEvent.event_type == "upload",
            UsageEvent.created_at >= month_start,

        )
        .scalar()
    ) or 0

    if count >= plan.monthly_uploads:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Monthly upload limit reached for {plan.name} plan."
        )


def enforce_storage_limit(user: User,incoming_bytes:int = 0):
    plan = _plan(user)
    used = dir_size_bytes(UPLOAD_DIR / str(user.id))
    limit_bytes = get_plan_storage_limit_bytes(user)

    if used + incoming_bytes > limit_bytes:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Storage limit reached for {plan.name} plan."
        )