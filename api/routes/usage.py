"""Usage analytics routes."""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
# from sqlalchemy.sql.functions import current_user

from api.database import get_db
from api.dependencies import get_current_user
from api.models import User, UsageEvent
from api.storage import dir_size_bytes
from config import UPLOAD_DIR
from api.services.usage_limits import get_plan_limits, get_plan_storage_limit_bytes

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/me")
def get_my_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return current user's monthly query/upload counts and storage usage."""
    plan = get_plan_limits(current_user)
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)

    query_count = (
        db.query(func.count(UsageEvent.id))
        .filter(
            UsageEvent.user_id == current_user.id,
            UsageEvent.event_type == "query",
            UsageEvent.created_at >= month_start,
        )
        .scalar()
    ) or 0

    upload_count = (
        db.query(func.count(UsageEvent.id))
        .filter(
            UsageEvent.user_id == current_user.id,
            UsageEvent.event_type == "upload",
            UsageEvent.created_at >= month_start,
        )
        .scalar()
    ) or 0

    uploads_dir = UPLOAD_DIR / str(current_user.id)
    used_bytes = dir_size_bytes(uploads_dir)
    limit_bytes = get_plan_storage_limit_bytes(current_user)
    used_percent = (used_bytes / limit_bytes * 100.0) if limit_bytes else 0.0

    return {
        "month": now.strftime("%Y-%m"),
        "plan" : {
            "id": plan.plan_id,
            "name": plan.name,
            "limits":{
                "monthly_queries": plan.monthly_queries,
                "monthly_uploads": plan.monthly_uploads,
                "storage_mb": plan.storage_mb,
            }
        },
        "queries_this_month": int(query_count),
        "uploads_this_month": int(upload_count),
        "storage": {
            "used_bytes": int(used_bytes),
            "limit_bytes": int(limit_bytes),
            "used_percent": round(used_percent, 2),
        },
    }
