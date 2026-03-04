"""Authentication routes – login, register, profile."""

import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import (
    hash_password, verify_password, create_access_token, get_current_user,
)
from backend.config import UPLOAD_DIR, ALLOWED_EXTENSIONS, MAX_FILE_SIZE
from backend.database import get_db
from backend.models import User, UserRole
from backend.schemas import (
    LoginRequest, RegisterRequest, TokenResponse, UserOut, ProfileUpdate,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Validate role
    try:
        role = UserRole(body.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid role")

    user = User(
        email=body.email,
        name=body.name,
        phone=body.phone,
        password_hash=hash_password(body.password),
        role=role,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(
        access_token=token,
        user=UserOut.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(
        access_token=token,
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return UserOut.model_validate(current_user)


@router.patch("/profile", response_model=UserOut)
async def update_profile(
    body: ProfileUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update current user's profile (name, phone, bio)."""
    if body.name is not None:
        current_user.name = body.name.strip()
    if body.phone is not None:
        current_user.phone = body.phone.strip() or None
    if body.bio is not None:
        current_user.bio = body.bio.strip() or None
    await db.flush()
    await db.refresh(current_user)
    # Update stored user in token context
    return UserOut.model_validate(current_user)


@router.post("/profile/avatar", response_model=UserOut)
async def upload_avatar(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a profile picture."""
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Invalid image format. Use JPG, PNG, GIF, or WebP.")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 5MB.")

    os.makedirs(UPLOAD_DIR / "avatars", exist_ok=True)
    unique_name = f"avatar_{current_user.id}_{uuid.uuid4().hex[:8]}{ext}"
    filepath = UPLOAD_DIR / "avatars" / unique_name
    with open(filepath, "wb") as f:
        f.write(content)

    current_user.avatar_url = f"/uploads/avatars/{unique_name}"
    await db.flush()
    await db.refresh(current_user)
    return UserOut.model_validate(current_user)
