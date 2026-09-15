"""Application configuration loaded from environment variables."""
from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    DATABASE_PATH = BASE_DIR / os.getenv("DATABASE_PATH", "database/attendance.db")
    MODEL_DIR = BASE_DIR / os.getenv("MODEL_DIR", "models")
    CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
    RECOGNITION_THRESHOLD = float(os.getenv("RECOGNITION_THRESHOLD", "0.45"))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
