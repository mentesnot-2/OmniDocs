"""Auth routes (signup, login, logout, me)"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from api.database import get_db
from api.models import User
from api.schemas.user import UserSignup, UserLogin, UserResponse, TokenResponse
from api.core.security import hash_password, verify_password, create_access_token
from api.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

AUTH_COOKIE = "omnidocs_token"
COOKIE_MAX_AGE = 60 * 60 * 24  # 1 day


def _response_with_cookie(user: User, token: str) -> Response:
    body = TokenResponse(
        access_token=token,
        user=UserResponse(id=user.id, email=user.email),
    )
    resp = Response(content=body.model_dump_json(), media_type="application/json")
    resp.set_cookie(
        key=AUTH_COOKIE,
        value=token,
        httponly=True,
        secure=False,  # True in production over HTTPS
        samesite="lax",
        max_age=COOKIE_MAX_AGE,
        path="/",
    )
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
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(data={"sub": str(user.id)})
    return _response_with_cookie(user, token)


@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(data={"sub": str(user.id)})
    return _response_with_cookie(user, token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse(id=current_user.id, email=current_user.email)


@router.post("/logout")
def logout():
    resp = Response(content='{"detail":"Logged out"}', media_type="application/json")
    resp.delete_cookie(key=AUTH_COOKIE, path="/")
    return resp
    