"""Documents routes (upload, query)"""

from fastapi import APIRouter

router = APIRouter(prefix="/documents",tags=["documents"])


@router.post("/upload")
def upload():
    return {
        "message": "Upload - coming soon"
    }


@router.post("/query")
def query():
    return {
        "message": "Query - coming soon"
    }