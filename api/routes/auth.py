"""Auth routes (signup, login, logout, me, refresh, oauth)"""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timedelta,timezone
import secrets
from urllib.parse import urlencode, quote
from uuid import uuid4
import httpx

from api.database import get_db
from api.models import RefreshSession, User
from api.schemas.user import UserSignup, UserLogin, UserResponse, TokenResponse
from api.core.security import (
    hash_password,
    hash_verification_token,
    verify_password,
    create_access_token,
    create_refresh_token_with_jti,
    decode_refresh_token,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from api.dependencies import CSRF_COOKIE, ensure_user_is_active, get_current_user,require_csrf
from config.settings import (
    EMAIL_VERIFICATION_REQUIRED,
    EMAIL_VERIFICATION_BASE_URL,
    SSO_ENABLED,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    FRONTEND_BASE_URL,
    COOKIE_SECURE,
)
from api.utils.email import send_email, EmailDeliveryError
from api.utils.logging_config import logger
from api.utils.log_pii import redact_email_for_log
from api.rate_limiter import limiter

router = APIRouter(prefix="/auth", tags=["auth"])

AUTH_COOKIE = "omnidocs_token"
REFRESH_COOKIE = "omnidocs_refresh"
ACCESS_COOKIE_MAX_AGE = 60 * 15  # 15 min (match access token)
REFRESH_COOKIE_MAX_AGE = 60 * 60 * 24 * 7  # 7 days
OAUTH_STATE_COOKIE = "omnidocs_oauth_state"


def _revoke_refresh_session_chain(
    db: Session,
    starting_jti: str | None,

) -> None:
    """
    Revoke a rotated refresh-token chain starting from a given JTI.

    This is used when a revoked refresh token is presented again, which indicates possible token theft/replay. we revoke every descendant session reachable through replaced_by_jti.
    """
    current_jti = starting_jti
    now = datetime.utcnow()
    
    while current_jti:
        session = db.query(RefreshSession).filter(RefreshSession.jti == current_jti).first()
        if not session:
            break
        
        next_jti = session.replaced_by_jti
        if session.revoked_at is None:
            session.revoked_at = now
        current_jti = next_jti
    db.commit()


def _set_auth_cookies(resp: Response, access_token: str, refresh_token: str) -> None:
    csrf_token = secrets.token_urlsafe(32)
    resp.set_cookie(
        key=AUTH_COOKIE,
        value=access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=ACCESS_COOKIE_MAX_AGE,
        path="/",
    )
    resp.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=REFRESH_COOKIE_MAX_AGE,
        path="/",
    )

    resp.set_cookie(
        key=CSRF_COOKIE,
        value=csrf_token,
        httponly=False,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=REFRESH_COOKIE_MAX_AGE, # 30 days
        path="/",
    )


def _response_with_cookies(user: User, access_token: str, refresh_token: str) -> Response:
    body = TokenResponse(
        access_token=access_token,
        user=UserResponse(id=user.id, email=user.email, is_admin=bool(user.is_admin)),
    )
    resp = Response(content=body.model_dump_json(), media_type="application/json")
    _set_auth_cookies(resp, access_token, refresh_token)
    return resp


def _create_refresh_session(db: Session, user: User) -> str:
    """Persist a refresh session and return a signed refresh token."""
    jti = uuid4().hex
    expires_at = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    db.add(
        RefreshSession(
            user_id=user.id,
            jti=jti,
            expires_at=expires_at,
        )
    )
    db.commit()
    return create_refresh_token_with_jti(user.id, jti)


def _revoke_refresh_session(db: Session, refresh_token: str | None, *, replacement_jti: str | None = None) -> None:
    """Best-effort revocation for the refresh token currently held by the client."""
    if not refresh_token:
        return

    payload = decode_refresh_token(refresh_token)
    if not payload:
        return

    session = db.query(RefreshSession).filter(RefreshSession.jti == payload["jti"]).first()
    if not session or session.revoked_at is not None:
        return

    session.revoked_at = datetime.utcnow()
    if replacement_jti:
        session.replaced_by_jti = replacement_jti
    db.commit()


def _issue_auth_response(db: Session, user: User) -> Response:
    """Issue fresh access and revocable refresh cookies for a user."""
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = _create_refresh_session(db, user)
    return _response_with_cookies(user, access_token, refresh_token)


def _google_callback_url() -> str:
    return f"{FRONTEND_BASE_URL.rstrip('/')}/api/auth/oauth/google/callback"


def _oauth_error_response(message: str) -> Response:
    """Return users to login with a safe, user-visible OAuth error."""
    redirect_url = f"{FRONTEND_BASE_URL.rstrip('/')}/login?error={quote(message)}"
    resp = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    resp.delete_cookie(key=OAUTH_STATE_COOKIE, path="/")
    return resp


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
    plain_verification_token: str | None = None
    if EMAIL_VERIFICATION_REQUIRED:
        plain_verification_token = User.generate_verification_token()
        user.verification_token = hash_verification_token(plain_verification_token)
        user.verification_expires_at = User.verification_expiry()
    db.add(user)
    db.commit()
    db.refresh(user)
    if EMAIL_VERIFICATION_REQUIRED and plain_verification_token is not None:
        verify_link = f"{EMAIL_VERIFICATION_BASE_URL}/verify-email?token={plain_verification_token}"
        try:
            send_email(
                to=user.email,
                subject="Verify your OmniDocs account",
                body=f"Click the link to verify your email:\n\n{verify_link}\n\nIf you did not sign up, ignore this email"
            )
        except EmailDeliveryError:
            # Avoid leaving users stuck in unverified state with no delivered email.
            try:
                db.delete(user)
                db.commit()
            except Exception as cleanup_exc:
                db.rollback()
                logger.exception("Failed to rollback user creation after email failure: %s", cleanup_exc)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Unable to send verification email right now. Please try again later.",
            )

        return Response(
            content='{"detail":"Verification email sent. Please check your inbox."}',
            media_type="application/json",
            status_code=status.HTTP_201_CREATED
        )
    return _issue_auth_response(db, user)


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
        secure=COOKIE_SECURE,
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
        return _oauth_error_response("Invalid OAuth callback state or code.")

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
            return _oauth_error_response("Failed to exchange Google auth code.")
        access_token_google = token_res.json().get("access_token")
        if not access_token_google:
            return _oauth_error_response("Google token response is missing access token.")

        userinfo_res = await client.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token_google}"},
        )
        if userinfo_res.status_code != 200:
            return _oauth_error_response("Failed to fetch Google user profile.")
        profile = userinfo_res.json()

    email = profile.get("email")
    sub = profile.get("sub")
    email_verified = bool(profile.get("email_verified"))
    if not email or not sub:
        return _oauth_error_response("Google profile did not include required fields.")
    if not email_verified:
        return _oauth_error_response("Google account email is not verified.")

    user = db.query(User).filter(User.oauth_sub == sub).first()
    if user:
        ensure_user_is_active(user)
    else:
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            ensure_user_is_active(existing_user)
            logger.warning(
                "Blocked Google OAuth auto-link for existing account email=%s user_id=%s",
                redact_email_for_log(existing_user.email),
                existing_user.id,
            )
            return _oauth_error_response(
                "An account with this email already exists. Sign in with your existing method."
            )

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

    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = _create_refresh_session(db, user)
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
    return _issue_auth_response(db, user)


@router.post("/refresh")
def refresh(
    request: Request, 
    _csrf: None = Depends(require_csrf),
    db: Session = Depends(get_db)
):
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
    session = db.query(RefreshSession).filter(RefreshSession.jti == payload["jti"]).first()
    if not session or session.user_id != int(payload["sub"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    # Reuse detection: a revoked refresh token being presented again
    # indicates possible theft/replay. Revoke the active descendant
    # chain and force re-authentication.

    if session.revoked_at is not None:
        logger.warning(
            "Detected refresh-token reuse for user_id=%s jti=%s",
            session.user_id,
            session.jti,
        )
        _revoke_refresh_session_chain(db, session.jti)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    if not session.is_active():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    user_id = int(payload["sub"])
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    ensure_user_is_active(user)
    new_jti = uuid4().hex
    new_session = RefreshSession(
        user_id=user.id,
        jti=new_jti,
        expires_at=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )
    session.revoked_at = datetime.utcnow()
    session.replaced_by_jti = new_jti
    db.add(new_session)
    db.commit()
    access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token_with_jti(user.id, new_jti)
    resp = Response(
        content=UserResponse(id=user.id, email=user.email, is_admin=bool(user.is_admin)).model_dump_json(),
        media_type="application/json",
    )
    _set_auth_cookies(resp, access_token, new_refresh_token)
    return resp


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        is_admin=bool(current_user.is_admin),
    )


@router.post("/logout")
def logout(request: Request, _csrf: None = Depends(require_csrf), db: Session = Depends(get_db)):
    _revoke_refresh_session(db, request.cookies.get(REFRESH_COOKIE))
    resp = Response(content='{"detail":"Logged out"}', media_type="application/json")
    resp.delete_cookie(key=AUTH_COOKIE, path="/")
    resp.delete_cookie(key=REFRESH_COOKIE, path="/")
    resp.delete_cookie(key=CSRF_COOKIE, path="/")
    return resp
    

@router.get("/verify/{token}")
def verify_email(token:str,db:Session=Depends(get_db)):
    token_digest = hash_verification_token(token)
    user = db.query(User).filter(User.verification_token == token_digest).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token",
        )
    
    if user.verification_expires_at and user.verification_expires_at < datetime.now(timezone.utc):
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



