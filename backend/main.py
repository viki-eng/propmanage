"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import APP_NAME, APP_VERSION, APP_DESCRIPTION, UPLOAD_DIR, BASE_DIR
from backend.database import init_db

# Routers
from backend.routers.auth_routes import router as auth_router
from backend.routers.tickets import router as tickets_router
from backend.routers.users import router as users_router
from backend.routers.notifications import router as notifications_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown events."""
    # Ensure directories exist
    Path(BASE_DIR / "data").mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    # Create tables
    await init_db()
    yield


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description=APP_DESCRIPTION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(auth_router)
app.include_router(tickets_router)
app.include_router(users_router)
app.include_router(notifications_router)

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# Serve frontend static files
frontend_dir = BASE_DIR / "frontend"
app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
