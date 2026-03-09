""" 
Chat session and message models for persisting conversation history.
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey,Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from api.database import Base

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"),nullable=False,index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    messages = relationship("ChatMessage",back_populates="session",cascade="all,delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"),nullable=False,index=True)
    role = Column(String(20),nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    session = relationship("ChatSession",back_populates="messages")