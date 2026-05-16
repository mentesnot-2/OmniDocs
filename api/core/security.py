"""Password hashing and JWT handling."""

import hashlib

import bcrypt
from datetime import datetime, timedelta
from uuid import uuid4
from jose import JWTError, jwt
from config.settings import JWT_SECRET_KEY, JWT_ALGORITHM

SECRET_KEY = JWT_SECRET_KEY
ALGORITHM = JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # short-lived; refresh before expiry
REFRESH_TOKEN_EXPIRE_DAYS = 7

# bcrypt has a 72-byte limit; truncate to avoid ValueError
BCRYPT_MAX_PASSWORD_BYTES = 72


def hash_verification_token(plaintext_token: str) -> str:
    """SHA-256 hex digest for storing email verification secrets (plaintext only in outbound email)."""
    return hashlib.sha256(plaintext_token.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    raw = password.encode("utf-8")
    if len(raw) > BCRYPT_MAX_PASSWORD_BYTES:
        raw = raw[:BCRYPT_MAX_PASSWORD_BYTES]
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    raw = plain_password.encode("utf-8")
    if len(raw) > BCRYPT_MAX_PASSWORD_BYTES:
        raw = raw[:BCRYPT_MAX_PASSWORD_BYTES]
    return bcrypt.checkpw(raw, hashed_password.encode("utf-8"))


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["type"] = "access"
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int) -> str:
    return create_refresh_token_with_jti(user_id=user_id, jti=uuid4().hex)


def create_refresh_token_with_jti(user_id: int, jti: str) -> str:
    to_encode = {"sub": str(user_id), "type": "refresh", "jti": jti}
    to_encode["exp"] = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


def decode_refresh_token(token: str) -> dict | None:
    payload = decode_token(token)
    if payload is None or payload.get("type") != "refresh" or "sub" not in payload or "jti" not in payload:
        return None
    return payload


def decode_access_token(token: str) -> dict | None:
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access" or "sub" not in payload:
        return None
    return payload