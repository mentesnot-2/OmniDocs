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
    # SHA-256 hex digest of the secret sent in the verification link — never store plaintext token.
    verification_token = Column(String(255),unique=True,index=True,nullable=True)
    verification_expires_at = Column(DateTime(timezone=True),nullable=True)

    auth_provider = Column(String(255),nullable=True)
    oauth_sub = Column(String(255),nullable=True,index=True)

    is_admin = Column(Boolean, nullable=False,server_default="0")
    is_active = Column(Boolean, nullable=False,server_default="1")

    # Billing / Subscription
    plan_id = Column(String(50), nullable=False, server_default="free")
    stripe_customer_id = Column(String(255),nullable=True,unique=True,index=True)
    stripe_subscription_id = Column(String(255),nullable=True,unique=True,index=True)
    billing_status = Column(String(50), nullable=True)

    @staticmethod
    def generate_verification_token():
        return secrets.token_urlsafe(32)

    @staticmethod
    def verification_expiry(hours:int=24) -> datetime:
        return datetime.utcnow() + timedelta(hours=hours)