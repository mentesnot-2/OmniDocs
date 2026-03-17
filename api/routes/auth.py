"""Auth routes (signup, login, logout, me, refresh)"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import datetime

from api.database import get_db
from api.models import User
from api.schemas.user import UserSignup, UserLogin, UserResponse, TokenResponse
from api.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from api.dependencies import get_current_user
from config.settings import EMAIL_VERIFICATION_REQUIRED,EMAIL_VERIFICATION_BASE_URL
from api.utils.email import send_email

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

AUTH_COOKIE = "omnidocs_token"
REFRESH_COOKIE = "omnidocs_refresh"
ACCESS_COOKIE_MAX_AGE = 60 * 15  # 15 min (match access token)
REFRESH_COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days


def _set_auth_cookies(resp: Response, access_token: str, refresh_token: str) -> None:
    resp.set_cookie(
        key=AUTH_COOKIE,
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=ACCESS_COOKIE_MAX_AGE,
        path="/",
    )
    resp.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=REFRESH_COOKIE_MAX_AGE,
        path="/",
    )


def _response_with_cookies(user: User, access_token: str, refresh_token: str) -> Response:
    body = TokenResponse(
        access_token=access_token,
        user=UserResponse(id=user.id, email=user.email),
    )
    resp = Response(content=body.model_dump_json(), media_type="application/json")
    _set_auth_cookies(resp, access_token, refresh_token)
    return resp


@router.post("/signup")
@limiter.limit("5/minute")
def signup(request: Request, data: UserSignup, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
    )

    user.is_verified = not EMAIL_VERIFICATION_REQUIRED
    if EMAIL_VERIFICATION_REQUIRED:
        user.verification_token = User.generate_verification_token()
        user.verification_expires_at = User.verification_expiry()
    db.add(user)
    db.commit()
    db.refresh(user)
    if EMAIL_VERIFICATION_REQUIRED:
        verify_link = f"{EMAIL_VERIFICATION_BASE_URL}/verify-email?token={user.verification_token}"
        send_email(
            to=user.email,
            subject="Verify your OmniDocs account",
            body=f"Click the link to verify your email:\n\n{verify_link}\n\nIf you did not sign up, ignore this email"
        )

        return Response(
            content='{"detail":"Verification email sent. Please check your inbox."}',
            media_type="application/json",
            status_code=status.HTTP_201_CREATED
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(user.id)
    return _response_with_cookies(user, access_token, refresh_token)


@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    if EMAIL_VERIFICATION_REQUIRED and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check inbox"
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(user.id)
    return _response_with_cookies(user, access_token, refresh_token)


@router.post("/refresh")
def refresh(request: Request, db: Session = Depends(get_db)):
    """Issue new access (and refresh) tokens using the refresh cookie. Silent refresh."""
    refresh_token = request.cookies.get(REFRESH_COOKIE)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token",
        )
    payload = decode_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    user_id = int(payload["sub"])
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(user.id)
    resp = Response(
        content=UserResponse(id=user.id, email=user.email).model_dump_json(),
        media_type="application/json",
    )
    _set_auth_cookies(resp, access_token, new_refresh_token)
    return resp


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse(id=current_user.id, email=current_user.email)


@router.post("/logout")
def logout():
    resp = Response(content='{"detail":"Logged out"}', media_type="application/json")
    resp.delete_cookie(key=AUTH_COOKIE, path="/")
    resp.delete_cookie(key=REFRESH_COOKIE, path="/")
    return resp
    

@router.get("/verify/{token}")
def verify_email(token:str,db:Session=Depends(get_db)):
    user = db.query(User).filter(User.verification_token == token).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )
    
    if user.verification_expires_at and user.verification_expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification token has expired"
        )
    
    user.is_verified = True
    user.verification_token = None
    user.verification_expires_at = None
    db.commit()
    db.refresh(user)
    return {"detail": "Email verified successfully. You can now log in."}

