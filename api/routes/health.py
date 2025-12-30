"""Health and readiness endpoints."""

from pathlib import Path

from fastapi import APIRouter
from sqlalchemy import text

from api.database import engine
from api.services.storage_backend import get_storage_backend
from config import VECTOR_STORE_PATH

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "healthy"}


@router.get("/health/ready")
def readiness():
    checks: dict[str, str] = {}

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"

    try:
        chroma_path = Path(VECTOR_STORE_PATH)
        chroma_path.mkdir(parents=True, exist_ok=True)
        test_file = chroma_path / ".write_check"
        test_file.write_text("ok", encoding="utf-8")
        test_file.unlink(missing_ok=True)
        checks["chroma"] = "ok"
    except Exception as exc:
        checks["chroma"] = f"error: {exc}"

    try:
        storage = get_storage_backend()
        _ = storage
        checks["storage"] = "ok"
    except Exception as exc:
        checks["storage"] = f"error: {exc}"

    ready = all(value == "ok" for value in checks.values())
    return {
        "status": "ready" if ready else "degraded",
        "checks": checks,
    }
