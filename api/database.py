"""
Database configuration and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,declarative_base
from pathlib import Path

# SQLite DB path
DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite:///{DB_DIR}/omnidocs.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    # echo=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for FastAPI - yields a database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()