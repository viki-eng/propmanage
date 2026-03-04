"""User management routes (manager only)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth import require_role
from backend.database import get_db
from backend.models import User, UserRole
from backend.schemas import UserOut

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/", response_model=list[UserOut])
async def list_users(
    role: str | None = None,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role(UserRole.MANAGER)),
):
    """List users. Managers can filter by role."""
    query = select(User).where(User.is_active == True)
    if role:
        try:
            query = query.where(User.role == UserRole(role))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid role filter")
    query = query.order_by(User.name)
    result = await db.execute(query)
    return [UserOut.model_validate(u) for u in result.scalars().all()]


@router.get("/technicians", response_model=list[UserOut])
async def list_technicians(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_role(UserRole.MANAGER)),
):
    """List available technicians for assignment."""
    result = await db.execute(
        select(User)
        .where(User.role == UserRole.TECHNICIAN, User.is_active == True)
        .order_by(User.name)
    )
    return [UserOut.model_validate(u) for u in result.scalars().all()]
