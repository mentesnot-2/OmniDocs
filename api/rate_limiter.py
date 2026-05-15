"""Shared SlowAPI limiter instance."""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_ipaddr

from api.core.security import decode_access_token
from config.settings import RATE_LIMIT_STORAGE_URI

AUTH_COOKIE = "omnidocs_token"

def _get_authenticated_user_key(request: Request) -> str | None:
    """
    Return a stable user-based rate-limit key for authenticated request.
    Falls back to None if the request is anonymous or the token is invalid.
    """
    token = request.cookies.get(AUTH_COOKIE)

    if not token:
        auth_header = request.headers.get("Authorization")

        if auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ")[1].strip()

    if not token:
        return None


    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        return None
    
    return f"user: {payload['sub']}"


def rate_limit_key(request:Request) -> str:
    """
    Prefer authenticated user ID for logged-in routes.
    Fall back to real client IP for anonymous traffic.
    """

    user_key = _get_authenticated_user_key(request)
    if user_key:
        return user_key
    return f"ip:{get_ipaddr(request)}"

limiter = Limiter(
    key_func=rate_limit_key,
    storage_uri=RATE_LIMIT_STORAGE_URI
)
