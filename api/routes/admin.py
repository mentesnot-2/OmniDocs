from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import require_admin, require_csrf
from api.models import SupportTicket, User
from api.rate_limiter import limiter
from api.services.audit_log import list_audit_logs, record_admin_action

router = APIRouter(prefix="/admin", tags=["admin"])


class ActiveUpdateRequest(BaseModel):
    is_active: bool


class TicketStatusUpdateRequest(BaseModel):
    status: str


@router.get("/users")
@limiter.limit("30/minute")
def list_users(
    request: Request,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    users = db.query(User).order_by(User.id.desc()).all()
    return {
        "users": [
            {
                "id": user.id,
                "email": user.email,
                "is_active": user.is_active,
                "is_admin": user.is_admin,
                "created_at": user.created_at,
                "is_verified": user.is_verified,
            }
            for user in users
        ]
    }


@router.patch("/users/{user_id}/active")
@limiter.limit("20/minute")
def set_user_active(
    request: Request,
    user_id: int,
    body: ActiveUpdateRequest,
    _csrf: None = Depends(require_csrf),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if user.id == admin.id and body.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself",
        )

    user.is_active = body.is_active
    db.commit()
    db.refresh(user)

    record_admin_action(
        db,
        admin_user_id=admin.id,
        action="user.set_active",
        target_type="user",
        target_id=user.id,
        metadata={"is_active": body.is_active},
    )

    return {"id": user.id, "is_active": bool(user.is_active)}


@router.get("/support/tickets")
@limiter.limit("30/minute")
def list_support_tickets(
    request: Request,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    tickets = db.query(SupportTicket).order_by(SupportTicket.id.desc()).all()
    return {
        "tickets": [
            {
                "id": ticket.id,
                "user_id": ticket.user_id,
                "subject": ticket.subject,
                "status": ticket.status,
                "message": ticket.message,
                "created_at": str(ticket.created_at) if ticket.created_at else None,
            }
            for ticket in tickets
        ]
    }


@router.patch("/support/tickets/{ticket_id}")
@limiter.limit("20/minute")
def update_support_ticket(
    request: Request,
    ticket_id: int,
    body: TicketStatusUpdateRequest,
    _csrf: None = Depends(require_csrf),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    allowed = {"open", "in_progress", "resolved"}
    if body.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Allowed: {', '.join(allowed)}",
        )

    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    old_status = ticket.status
    ticket.status = body.status
    db.commit()
    db.refresh(ticket)

    record_admin_action(
        db,
        admin_user_id=admin.id,
        action="ticket.update_status",
        target_type="support_ticket",
        target_id=ticket.id,
        metadata={"old_status": old_status, "new_status": body.status},
    )

    return {"id": ticket.id, "status": ticket.status}


@router.get("/audit-logs")
@limiter.limit("30/minute")
def get_audit_logs(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    limit = min(max(limit, 1), 100)
    offset = max(offset, 0)
    entries = list_audit_logs(db, limit=limit, offset=offset)
    return {
        "logs": [
            {
                "id": entry.id,
                "admin_user_id": entry.admin_user_id,
                "action": entry.action,
                "target_type": entry.target_type,
                "target_id": entry.target_id,
                "metadata_json": entry.metadata_json,
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
            }
            for entry in entries
        ],
        "limit": limit,
        "offset": offset,
    }
