"""Auth routes (signup, login)"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.database import get_db
from api.models import User
from api.schemas.user import UserSignup, UserLogin, UserResponse, TokenResponse
from api.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


@router.post("/signup", response_model=TokenResponse)
@limiter.limit("5/minute")
def signup(request: Request, data: UserSignup, db: Session = Depends(get_db)):
    # Check if email exists
    existing = db.query(User).filter(User.email == data.email).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Return token
    token = create_access_token(data={"sub":str(user.id)})

    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user.id,email=user.email)
    )

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(request: Request, data: UserLogin, db: Session = Depends(get_db)):
    # Check if email exists
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password,user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    token = create_access_token(data={"sub":str(user.id)})
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user.id,email=user.email)
    )
    