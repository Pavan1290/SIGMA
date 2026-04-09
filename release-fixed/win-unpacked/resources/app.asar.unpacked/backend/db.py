"""Database setup for SIGMA-OS backend (SQLAlchemy + SQLite by default).

Uses SQLite file `sigma.db` in the backend folder for development.
Switch to PostgreSQL by changing DATABASE_URL.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Default: SQLite file in backend directory
DATABASE_URL = os.getenv("SIGMA_DATABASE_URL", "sqlite:///./sigma.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency to get a DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
