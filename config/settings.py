"""
Configuration settings for RAG system.
Loads from environment variables via .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from project root
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
UPLOAD_DIR = DATA_DIR / "uploads"

# Document processing
CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', '512'))
CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '50'))
MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', '100')) # MB

# Embeddings

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "sentence-transformers")


# Vector store
VECTOR_STORE_PATH = os.getenv("VECTOR_STORE_PATH", str(PROJECT_ROOT / "chroma_db"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "omnidocs")

# Retrieval
TOP_K = int(os.getenv("TOP_K", "5"))


# LLM (OpenAI)

# LLM (Gemini)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-flash-latest")
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # gemini | openai
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # Optional, only if LLM_PROVIDER=openai

# JWT config: single source of truth for all auth/security modules

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
if not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is required and must be set in the environment.")
if len(JWT_SECRET_KEY) < 32:
    raise RuntimeError("JWT_SECRET_KEY must be at least 32 characters long.")


EMAIL_VERIFICATION_REQUIRED=os.getenv("EMAIL_VERIFICATION_REQUIRED","false").lower() == "true"
EMAIL_SENDER=os.getenv("EMAIL_SENDER","mentesnotsibatu63@gmail.com")
EMAIL_VERIFICATION_BASE_URL=os.getenv("EMAIL_VERIFICATION_BASE_URL","http://localhost:3000")

# Mailtrap SMTP settings (preferred)
MAILTRAP_TOKEN = os.getenv("MAILTRAP_TOKEN", "")
MAILTRAP_HOST = os.getenv("MAILTRAP_HOST", "")
MAILTRAP_PORT = int(os.getenv("MAILTRAP_PORT", "2525"))
MAILTRAP_USERNAME = os.getenv("MAILTRAP_USERNAME", "")
MAILTRAP_PASSWORD = os.getenv("MAILTRAP_PASSWORD", "")

RATE_LIMIT_STORAGE_URI = os.getenv("RATE_LIMIT_STORAGE_URI", "memory://")
TRUST_PROXY_HEADERS = os.getenv("TRUST_PROXY_HEADERS", "false").lower() == "true"
PROXY_TRUSTED_HOSTS = [
    host.strip()
    for host in os.getenv("PROXY_TRUSTED_HOSTS", "127.0.0.1,localhost").split(",")
    if host.strip()
]
# Generic SMTP settings (fallback). If MAILTRAP_* exists, use it automatically.
SMTP_HOST = MAILTRAP_HOST or os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = MAILTRAP_PORT if MAILTRAP_HOST else int(os.getenv("SMTP_PORT", "25"))
SMTP_USERNAME = MAILTRAP_USERNAME or os.getenv("SMTP_USERNAME", "")
SMTP_PASSWORD = MAILTRAP_PASSWORD or os.getenv("SMTP_PASSWORD", "")
SMTP_USE_TLS=os.getenv("SMTP_USE_TLS","true").lower() == "true"
SMTP_USE_SSL=os.getenv("SMTP_USE_SSL","false").lower() == "true"

MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "25"))
MAX_USER_STORAGE_MB = int(os.getenv("MAX_USER_STORAGE_MB", "500"))
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md", ".csv", ".xlsx", ".html", ".htm", ".pptx"}


SSO_ENABLED = os.getenv("SSO_ENABLED", "false").lower() == "true"
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
BACKEND_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET=os.getenv("STRIPE_WEBHOOK_SECRET","")
STRIPE_PRICE_PRO_MONTHLY=os.getenv("STRIPE_PRICE_PRO_MONTHLY","")
BILLING_SUCCESS_URL = os.getenv("BILLING_SUCCESS_URL","http://localhost:3000/dashboard/billing?success=1")
BILLING_CANCEL_URL = os.getenv("BILLING_CANCEL_URL","http://localhost:3000/dashboard/billing/?canceled=1")


APP_ENV = os.getenv("APP_ENV", "development").lower()
COOKIE_SECURE = os.getenv(
    "COOKIE_SECURE",
    "true" if APP_ENV == "production" else "false"
).lower() == "true"

STORAGE_BACKEND=os.getenv("STORAGE_BACKEND","local")
S3_BUCKET_NAME=os.getenv("S3_BUCKET_NAME","")
S3_REGION=os.getenv("S3_REGION","")
S3_ACCESS_KEY_ID=os.getenv("S3_ACCESS_KEY_ID","")
S3_SECRET_ACCESS_KEY=os.getenv("S3_SECRET_ACCESS_KEY","")
S3_ENDPOINT_URL=os.getenv("S3_ENDPOINT_URL","")
S3_KEY_PREFIX=os.getenv("S3_KEY_PREFIX","uploads")


CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", FRONTEND_BASE_URL).split(",")
    if origin.strip()
]

CORS_ALLOWED_METHODS = [
    method.strip().upper()
    for method in os.getenv("CORS_ALLOWED_METHODS", "GET,POST,PATCH,DELETE,OPTIONS").split(",")
    if method.strip()
]

CORS_ALLOWED_HEADERS = [
    header.strip()
    for header in os.getenv("CORS_ALLOWED_HEADERS", "Content-Type,X-CSRF-Token,Authorization").split(",")
    if header.strip()
]

def ensure_dirs():
    """Create data directories if they don't exist"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
