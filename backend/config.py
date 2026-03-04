"""Application configuration settings."""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{BASE_DIR / 'data' / 'app.db'}")

# JWT Settings
SECRET_KEY = os.getenv("SECRET_KEY", "propmanage-secret-key-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# File Upload Settings
UPLOAD_DIR = BASE_DIR / "uploads"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# App Settings
APP_NAME = "PropManage"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Property Maintenance Management System"
