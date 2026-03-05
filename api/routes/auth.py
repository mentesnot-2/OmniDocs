"""Auth routes (signup, login)"""

from fastapi import APIRouter

router = APIRouter(prefix="/auth",tags=["auth"])

@router.post("/signup")
def signup():
    return {
        "message": "Signup - coming soon"
    }

@router.post("/login")
def login():
    return {
        "message": "Login - coming soon"
    }