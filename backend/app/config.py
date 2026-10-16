"""
Central configuration. Every secret / setting comes from environment variables
(backend/.env). Nothing sensitive is hardcoded in the source code.
"""
import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

# backend/.env  (this file lives in backend/app/, so go up one level)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _bool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


# ---------- Database ----------
# Either set DATABASE_URL directly, or set the DB_* parts below.
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "student_db")

DATABASE_URL = os.getenv("DATABASE_URL") or (
    f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
)

# ---------- Auth ----------
SECRET_KEY = os.getenv("SECRET_KEY", "")
if len(SECRET_KEY) < 32:
    raise RuntimeError(
        "SECRET_KEY is missing or too short. Add a random value (32+ characters) "
        "to backend/.env. Generate one with:\n"
        '  python -c "import secrets; print(secrets.token_urlsafe(48))"'
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Admin registration is only allowed with this invitation code.
# If it is empty, registration is disabled completely.
ADMIN_INVITE_CODE = os.getenv("ADMIN_INVITE_CODE", "")

# ---------- Cookie ----------
COOKIE_NAME = "access_token"
COOKIE_SECURE = _bool("COOKIE_SECURE", False)       # set True when served over HTTPS
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")  # lax | strict | none

# ---------- CORS ----------
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174"
    ).split(",")
    if origin.strip()
]
