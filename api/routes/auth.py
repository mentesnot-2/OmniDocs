"""Auth routes (signup, login, logout, me, refresh, oauth)"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime
import secrets
from urllib.parse import urlencode
import httpx

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
from config.settings import (
    EMAIL_VERIFICATION_REQUIRED,
    EMAIL_VERIFICATION_BASE_URL,
    SSO_ENABLED,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    FRONTEND_BASE_URL,
)
from api.utils.email import send_email
from api.rate_limiter import limiter

router = APIRouter(prefix="/auth", tags=["auth"])

AUTH_COOKIE = "omnidocs_token"
REFRESH_COOKIE = "omnidocs_refresh"
ACCESS_COOKIE_MAX_AGE = 60 * 15  # 15 min (match access token)
REFRESH_COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days
OAUTH_STATE_COOKIE = "omnidocs_oauth_state"


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


def _google_callback_url() -> str:
    return f"{FRONTEND_BASE_URL.rstrip('/')}/api/auth/oauth/google/callback"


def _ensure_sso_google_enabled() -> None:
    if not SSO_ENABLED:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SSO is disabled.")
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth is not configured.",
        )


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


@router.get("/oauth/google/start")
@limiter.limit("20/minute")
def oauth_google_start(request: Request):
    _ensure_sso_google_enabled()
    state = secrets.token_urlsafe(24)
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": _google_callback_url(),
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    resp = RedirectResponse(url=auth_url, status_code=status.HTTP_302_FOUND)
    resp.set_cookie(
        key=OAUTH_STATE_COOKIE,
        value=state,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=600,
        path="/",
    )
    return resp


@router.get("/oauth/google/callback")
@limiter.limit("20/minute")
async def oauth_google_callback(request: Request, code: str | None = None, state: str | None = None, db: Session = Depends(get_db)):
    _ensure_sso_google_enabled()
    expected_state = request.cookies.get(OAUTH_STATE_COOKIE)
    if not code or not state or not expected_state or state != expected_state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OAuth callback state or code.",
        )

    token_payload = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": _google_callback_url(),
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        token_res = await client.post("https://oauth2.googleapis.com/token", data=token_payload)
        if token_res.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange Google auth code.",
            )
        access_token_google = token_res.json().get("access_token")
        if not access_token_google:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google token response is missing access_token.",
            )

        userinfo_res = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token_google}"},
        )
        if userinfo_res.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to fetch Google user profile.",
            )
        profile = userinfo_res.json()

    email = profile.get("email")
    sub = profile.get("sub")
    if not email or not sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google profile did not include required fields.",
        )

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(
            email=email,
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            is_verified=True,
            auth_provider="google",
            oauth_sub=sub,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.is_verified = True
        user.auth_provider = user.auth_provider or "google"
        user.oauth_sub = user.oauth_sub or sub
        db.commit()
        db.refresh(user)

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(user.id)
    redirect_url = f"{FRONTEND_BASE_URL.rstrip('/')}/dashboard"
    resp = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    _set_auth_cookies(resp, access_token, refresh_token)
    resp.delete_cookie(key=OAUTH_STATE_COOKIE, path="/")
    return resp


@router.post("/login")
@limiter.limit("5/minute")
def login(request: Request, data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
        
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not active. Please contact support.",
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



