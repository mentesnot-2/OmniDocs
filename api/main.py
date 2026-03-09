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

#Create tables on startup
Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="OmniDocs API",
    description="API for OmniDocs RAG system",
    version="1.0.0",
)

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