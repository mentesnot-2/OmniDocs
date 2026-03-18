"""
User model for authentication.
"""

from sqlalchemy import Column, Integer, String,DateTime,Boolean
from sqlalchemy.sql import func
from api.database import Base
from datetime import datetime,timedelta
import secrets



class User(Base):
    __tablename__ = "users"
    id = Column(Integer,primary_key=True,index=True)
    email = Column(String(255),unique=True,index=True)
    hashed_password = Column(String(255),nullable=False)
    created_at = Column(DateTime(timezone=True),server_default=func.now())

    is_verified = Column(Boolean, nullable=False,server_default="0")
    verification_token = Column(String(255),unique=True,index=True,nullable=True)
    verification_expires_at = Column(DateTime(timezone=True),nullable=True)

    auth_provider = Column(String(255),nullable=True)
    oauth_sub = Column(String(255),nullable=True,index=True)

    @staticmethod
    def generate_verification_token():
        return secrets.token_urlsafe(32)

    @staticmethod
    def verification_expiry(hours:int=24) -> datetime:
        return datetime.utcnow() + timedelta(hours=hours)