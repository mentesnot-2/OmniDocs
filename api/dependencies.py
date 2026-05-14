"""Common dependencies (auth)."""

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import User
from api.core.security import decode_access_token

AUTH_COOKIE = "omnidocs_token"
CSRF_COOKIE = "omnidocs_csrf"
CSRF_HEADER = "X-CSRF-Token"


http_bearer = HTTPBearer(auto_error=False)


async def get_token(request: Request) -> str | None:
    """Prefer HttpOnly cookie; fallback to Authorization header."""
    token = request.cookies.get(AUTH_COOKIE)
    if token:
        return token
    creds: HTTPAuthorizationCredentials | None = await http_bearer(request)
    if creds:
        return creds.credentials
    return None

def require_csrf(
    request: Request,
    csrf_header: str | None = Header(default=None, alias=CSRF_HEADER),
) -> None:
    """
    Double-submit CSRF protection for cookie-authenticated browser mutations.
    Requires a CSRF cookie and matching X-CSRF-Token header.
    """
    csrf_cookie = request.cookies.get(CSRF_COOKIE)
    if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF validation failed",
        )

    origin = request.headers.get("origin")
    host = request.headers.get("host")
    if origin and host and not origin.endswith(host):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid request origin",
        )


def ensure_user_is_active(user: User) -> User:
    """Reject deactivated users across all authenticated flows."""
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not active. Please contact support.",
        )
    return user


def get_current_user(
    token: str | None = Depends(get_token),
    db: Session = Depends(get_db),
) -> User:
    """Return authenticated user from a valid access token."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    user_id = int(payload["sub"])
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return ensure_user_is_active(user)

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require the user to be an admin."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin only",
        )
    return current_user