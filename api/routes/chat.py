"""Chat session and message routes."""

from typing import List
from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import get_current_user
from api.models import User,ChatSession,ChatMessage
from api.schemas.chat import MessageOut,SessionOut

router = APIRouter(prefix="/chat",tags=["chat"])


@router.post("/sessions",response_model=SessionOut)
def create_session(
    db:Session = Depends(get_db),
    current_user:User = Depends(get_current_user),
):
    """Create a new chat session for the current user"""

    session = ChatSession(user_id=current_user.id)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions/{session_id}", response_model=SessionOut)
def get_session(
    session_id:int,
    db:Session = Depends(get_db),
    current_user:User = Depends(get_current_user),
):
    """Get a chat session with its messages (only if owned by user)"""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or not authorized",
        )
    return session

@router.get("/sessions",response_mdel=List[SessionOut])
def list_sessions(
    db:Session = Depends(get_db),
    current_user:User = Depends(get_current_user),
):
    """List all chat sessions for the current user (newest first)."""
    sessions = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id,
    ).order_by(ChatSession.created_at.desc()).all()
    return sessions
