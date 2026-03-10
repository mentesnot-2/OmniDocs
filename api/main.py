"""
OmniDocs FastAPI backend.
Run: uvicorn api.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import auth, documents, chat
from api.database import engine,Base
from api.models import User
from api.database import get_db
from api.utils.logging_config import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger.info("Starting OmniDocs API")

#Create tables on startup
Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="OmniDocs API",
    description="API for OmniDocs RAG system",
    version="1.0.0",
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)

@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "OmniDocs API is running",
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
    }