"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr


# ── Auth ───────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    name: str
    phone: Optional[str] = None
    password: str
    role: str = "tenant"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


# ── User ───────────────────────────────────────────────────────────────

class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Ticket ─────────────────────────────────────────────────────────────

class TicketCreate(BaseModel):
    title: str
    description: str
    property_address: Optional[str] = None
    unit_number: Optional[str] = None
    priority: str = "medium"


class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    property_address: Optional[str] = None
    unit_number: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    technician_id: Optional[int] = None


class TicketImageOut(BaseModel):
    id: int
    filename: str
    filepath: str
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ActivityLogOut(BaseModel):
    id: int
    action: str
    details: Optional[str] = None
    created_at: datetime
    user: UserOut

    class Config:
        from_attributes = True


class TicketOut(BaseModel):
    id: int
    title: str
    description: str
    property_address: Optional[str] = None
    unit_number: Optional[str] = None
    status: str
    priority: str
    tenant_id: int
    technician_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    tenant: Optional[UserOut] = None
    technician: Optional[UserOut] = None
    images: List[TicketImageOut] = []

    class Config:
        from_attributes = True


class TicketDetailOut(TicketOut):
    activity_logs: List[ActivityLogOut] = []


# ── Notification ───────────────────────────────────────────────────────

class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    is_read: bool
    link: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Stats ──────────────────────────────────────────────────────────────

class DashboardStats(BaseModel):
    total_tickets: int = 0
    open_tickets: int = 0
    assigned_tickets: int = 0
    in_progress_tickets: int = 0
    done_tickets: int = 0
    unread_notifications: int = 0


# Resolve forward references
TokenResponse.model_rebuild()
