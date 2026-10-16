from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import DATABASE_URL  # credentials now come from backend/.env


# SQLite (used only by the automated tests) needs one extra option
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# pool_pre_ping reconnects automatically if MySQL closed an idle connection
engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)

"""
SessionLocal is a factory that creates database sessions.
A session is what your FastAPI code uses to talk to the database
(queries, inserts, updates, deletes).
"""
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


# Gives each request its own DB session and closes it after
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
