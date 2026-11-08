
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker


# =========================================================
# 1. ENVIRONMENT CONFIGURATION
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is missing. Check your backend .env file."
    )


# =========================================================
# 2. DATABASE ENGINE
# =========================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


# =========================================================
# 3. SESSION CONFIGURATION
# =========================================================

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# =========================================================
# 4. DECLARATIVE BASE
# =========================================================

Base = declarative_base()


# =========================================================
# 5. DATABASE SESSION DEPENDENCY
# =========================================================

def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# =========================================================
# 6. DATABASE CONNECTION TEST
# =========================================================

def test_db_connection():

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return True

    except Exception as exc:
        raise RuntimeError(
            f"Database connection failed: {exc}"
        ) from exc
