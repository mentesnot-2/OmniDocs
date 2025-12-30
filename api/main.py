"""
OmniDocs FastAPI backend.
Run: uvicorn api.main:app --reload
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from api.database import Base, engine, get_db
from api.models import StripeProcessedEvent  # noqa: F401
from api.rate_limiter import limiter
from api.routes import admin, auth, billing, chat, documents, health, usage
from api.services.runtime_services import (
    get_answer_generator,
    get_embedding_generator,
    get_retriever,
)
from api.utils.logging_config import logger
from config import (
    APP_ENV,
    CORS_ALLOWED_HEADERS,
    CORS_ALLOWED_METHODS,
    CORS_ALLOWED_ORIGINS,
    PROXY_TRUSTED_HOSTS,
    TRUST_PROXY_HEADERS,
    ensure_dirs,
)

get_embedding_generator()
get_retriever()
get_answer_generator()

logger.info("Starting OmniDocs API")

ensure_dirs()

_database_url = os.getenv("DATABASE_URL", "")
_use_create_all = APP_ENV == "development" or _database_url.startswith("sqlite")
if _use_create_all:
    Base.metadata.create_all(bind=engine)
else:
    logger.info("Skipping create_all; run alembic upgrade head for schema changes")


@asynccontextmanager
async def lifespan(app: FastAPI):
    from api.services.stripe_runtime import init_stripe

    init_stripe()
    yield


app = FastAPI(
    title="OmniDocs API",
    description="API for OmniDocs RAG system",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

if TRUST_PROXY_HEADERS:
    app.add_middleware(
        ProxyHeadersMiddleware,
        trusted_hosts=PROXY_TRUSTED_HOSTS,
    )
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=CORS_ALLOWED_METHODS,
    allow_headers=CORS_ALLOWED_HEADERS,
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(admin.router)
app.include_router(usage.router)
app.include_router(billing.router)


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "OmniDocs API is running",
    }
