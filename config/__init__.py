"""Configuration package"""

from .settings import *

__all__ = ["PROJECT_ROOT", "DATA_DIR", "UPLOAD_DIR", "CHUNK_SIZE", "CHUNK_OVERLAP", "MAX_FILE_SIZE", "EMBEDDING_MODEL", "EMBEDDING_PROVIDER", "VECTOR_STORE_PATH", "COLLECTION_NAME", "TOP_K", "OPENAI_API_KEY", "LLM_MODEL", "ensure_dirs"]