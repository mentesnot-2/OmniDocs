"""Chat session and message routes."""

from typing import List
from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.orm import Session

from api.database import get_db
from api.dependencies import get_current_user
from api.models import User,ChatSession,ChatMessage
from api.schemas.chat import MessageOut,SessionOut,AddMessageRequest

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
    return {
        "id": session.id,
        "user_id": session.user_id,
        "created_at": session.created_at,
        "messages": [],
    }


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

@router.get("/sessions", response_model=List[SessionOut])
def list_sessions(
    db:Session = Depends(get_db),
    current_user:User = Depends(get_current_user),
):
    """List all chat sessions for the current user (newest first)."""
    from sqlalchemy.orm import joinedload
    sessions = (
        db.query(ChatSession)
        .options(joinedload(ChatSession.messages))
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )
    return sessions

@router.post("/sessions/{session_id}/messages")
def add_message(
    session_id:int,
    body:AddMessageRequest,
    db:Session = Depends(get_db),
    current_user:User = Depends(get_current_user),
):

    """Add a Q&A pair to a session."""
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id,
    ).first()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    msg_user = ChatMessage(
        session_id=session_id,
        role="user",
        content=body.question,
    )
    msg_assistant = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=body.answer,
    )
    db.add(msg_user)
    db.add(msg_assistant)
    db.commit()
    return {"ok":True}
