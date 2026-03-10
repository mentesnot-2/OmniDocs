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


def ensure_dirs():
    """Create data directories if they don't exist"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
