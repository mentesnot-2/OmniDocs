from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import require_admin, require_csrf
from api.models import SupportTicket, User
from api.rate_limiter import limiter

router = APIRouter(prefix="/admin", tags=["admin"])

class ActiveUpdateRequest(BaseModel):
    is_active: bool

class TicketStatusUpdateRequest(BaseModel):
    status: str # open / in_progress / resolved


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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.id == admin.id and body.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself",
        )


    user.is_active = body.is_active
    db.commit()
    db.refresh(user)
    return {
        "id": user.id,
        "is_active": bool(user.is_active),
    }

@router.get("/support/tickets")
@limiter.limit("30/minute")
def list_support_tickets(
    request: Request,
    db:Session = Depends(get_db),
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
    _admin: User = Depends(require_admin),
):
    allowed = {"open", "in_progress", "resolved"}

    if body.status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Allowed: {', '.join(allowed)}",
        )
    
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )

    ticket.status = body.status
    db.commit()
    db.refresh(ticket)
    return {"id": ticket.id, "status": ticket.status}