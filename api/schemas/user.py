"""
Pydantic schemas for user requests/responses.
"""
import re
from pydantic import BaseModel, EmailStr, field_validator

# Common weak passwords (top offenders + variations)
COMMON_PASSWORDS = frozenset({
    "password", "123456", "12345678", "qwerty", "abc123", "monkey", "1234567",
    "letmein", "trustno1", "dragon", "baseball", "iloveyou", "master", "sunshine",
    "ashley", "bailey", "passw0rd", "shadow", "123123", "654321", "superman",
    "qazwsx", "michael", "football", "password1", "password123", "admin", "admin123",
    "welcome", "login", "pass", "pass123", "password!", "changeme", "1234", "12345",
})

PASSWORD_MIN_LEN = 8
PASSWORD_MAX_LEN = 128


class UserSignup(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < PASSWORD_MIN_LEN:
            raise ValueError(f"Password must be at least {PASSWORD_MIN_LEN} characters")
        if len(v) > PASSWORD_MAX_LEN:
            raise ValueError(f"Password must be at most {PASSWORD_MAX_LEN} characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", v):
            raise ValueError("Password must contain at least one special character")
        if v.lower() in COMMON_PASSWORDS:
            raise ValueError("Password is too common. Choose a stronger password.")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse