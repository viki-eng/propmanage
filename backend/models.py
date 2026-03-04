"""SQLAlchemy ORM models."""

import enum
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Text, Enum, ForeignKey, Boolean, DateTime
)
from sqlalchemy.orm import relationship

from backend.database import Base


# ── Enums ──────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    TENANT = "tenant"
    MANAGER = "manager"
    TECHNICIAN = "technician"


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TicketPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# ── Helpers ────────────────────────────────────────────────────────────

def utcnow():
    return datetime.now(timezone.utc)


# ── Models ─────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.TENANT)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    # Relationships
    submitted_tickets = relationship(
        "Ticket", back_populates="tenant", foreign_keys="Ticket.tenant_id"
    )
    assigned_tickets = relationship(
        "Ticket", back_populates="technician", foreign_keys="Ticket.technician_id"
    )
    activity_logs = relationship("ActivityLog", back_populates="user")
    notifications = relationship("Notification", back_populates="user")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    property_address = Column(String(500), nullable=True)
    unit_number = Column(String(50), nullable=True)
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN, nullable=False)
    priority = Column(Enum(TicketPriority), default=TicketPriority.MEDIUM, nullable=False)

    tenant_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    technician_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    tenant = relationship("User", back_populates="submitted_tickets", foreign_keys=[tenant_id])
    technician = relationship("User", back_populates="assigned_tickets", foreign_keys=[technician_id])
    images = relationship("TicketImage", back_populates="ticket", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="ticket", cascade="all, delete-orphan")


class TicketImage(Base):
    __tablename__ = "ticket_images"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), default=utcnow)

    ticket = relationship("Ticket", back_populates="images")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    ticket = relationship("Ticket", back_populates="activity_logs")
    user = relationship("User", back_populates="activity_logs")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    link = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)

    user = relationship("User", back_populates="notifications")
