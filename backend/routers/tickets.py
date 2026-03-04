"""Ticket routes – CRUD, assignment, status flow, image upload."""

import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.auth import get_current_user, require_role
from backend.config import UPLOAD_DIR, MAX_FILE_SIZE, ALLOWED_EXTENSIONS
from backend.database import get_db
from backend.models import (
    User, UserRole, Ticket, TicketStatus, TicketPriority,
    TicketImage, ActivityLog, Notification,
)
from backend.schemas import (
    TicketCreate, TicketUpdate, TicketOut, TicketDetailOut,
    DashboardStats, TicketImageOut,
)

router = APIRouter(prefix="/api/tickets", tags=["tickets"])

# Valid status transitions
VALID_TRANSITIONS = {
    TicketStatus.OPEN: [TicketStatus.ASSIGNED],
    TicketStatus.ASSIGNED: [TicketStatus.IN_PROGRESS, TicketStatus.OPEN],
    TicketStatus.IN_PROGRESS: [TicketStatus.DONE, TicketStatus.ASSIGNED],
    TicketStatus.DONE: [TicketStatus.OPEN],  # re-open
}


# ── Helpers ────────────────────────────────────────────────────────────

async def _log_activity(db: AsyncSession, ticket_id: int, user_id: int, action: str, details: str = None):
    log = ActivityLog(ticket_id=ticket_id, user_id=user_id, action=action, details=details)
    db.add(log)


async def _notify(db: AsyncSession, user_id: int, title: str, message: str, link: str = None):
    notif = Notification(user_id=user_id, title=title, message=message, link=link)
    db.add(notif)


def _ticket_query():
    return (
        select(Ticket)
        .options(
            selectinload(Ticket.tenant),
            selectinload(Ticket.technician),
            selectinload(Ticket.images),
        )
    )


# ── Dashboard Stats ───────────────────────────────────────────────────

@router.get("/stats", response_model=DashboardStats)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base = select(Ticket)
    notif_base = select(func.count(Notification.id)).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False,
    )

    if current_user.role == UserRole.TENANT:
        base = base.where(Ticket.tenant_id == current_user.id)
    elif current_user.role == UserRole.TECHNICIAN:
        base = base.where(Ticket.technician_id == current_user.id)

    total = await db.execute(select(func.count()).select_from(base.subquery()))
    open_q = await db.execute(select(func.count()).select_from(
        base.where(Ticket.status == TicketStatus.OPEN).subquery()
    ))
    assigned_q = await db.execute(select(func.count()).select_from(
        base.where(Ticket.status == TicketStatus.ASSIGNED).subquery()
    ))
    progress_q = await db.execute(select(func.count()).select_from(
        base.where(Ticket.status == TicketStatus.IN_PROGRESS).subquery()
    ))
    done_q = await db.execute(select(func.count()).select_from(
        base.where(Ticket.status == TicketStatus.DONE).subquery()
    ))
    unread = await db.execute(notif_base)

    return DashboardStats(
        total_tickets=total.scalar() or 0,
        open_tickets=open_q.scalar() or 0,
        assigned_tickets=assigned_q.scalar() or 0,
        in_progress_tickets=progress_q.scalar() or 0,
        done_tickets=done_q.scalar() or 0,
        unread_notifications=unread.scalar() or 0,
    )


# ── List Tickets ───────────────────────────────────────────────────────

@router.get("/", response_model=list[TicketOut])
async def list_tickets(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = _ticket_query()

    # Role-based filtering
    if current_user.role == UserRole.TENANT:
        query = query.where(Ticket.tenant_id == current_user.id)
    elif current_user.role == UserRole.TECHNICIAN:
        query = query.where(Ticket.technician_id == current_user.id)

    # Filters
    if status:
        try:
            query = query.where(Ticket.status == TicketStatus(status))
        except ValueError:
            pass
    if priority:
        try:
            query = query.where(Ticket.priority == TicketPriority(priority))
        except ValueError:
            pass
    if search:
        query = query.where(
            Ticket.title.ilike(f"%{search}%") | Ticket.description.ilike(f"%{search}%")
        )

    query = query.order_by(Ticket.created_at.desc())
    result = await db.execute(query)
    tickets = result.scalars().unique().all()
    return [TicketOut.model_validate(t) for t in tickets]


# ── Get Single Ticket ─────────────────────────────────────────────────

@router.get("/{ticket_id}", response_model=TicketDetailOut)
async def get_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        _ticket_query()
        .options(selectinload(Ticket.activity_logs).selectinload(ActivityLog.user))
        .where(Ticket.id == ticket_id)
    )
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()

    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Tenants can only see their own tickets
    if current_user.role == UserRole.TENANT and ticket.tenant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    # Technicians can only see their assigned tickets
    if current_user.role == UserRole.TECHNICIAN and ticket.technician_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return TicketDetailOut.model_validate(ticket)


# ── Create Ticket ─────────────────────────────────────────────────────

@router.post("/", response_model=TicketOut, status_code=201)
async def create_ticket(
    body: TicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Tenants and managers can create tickets
    if current_user.role == UserRole.TECHNICIAN:
        raise HTTPException(status_code=403, detail="Technicians cannot create tickets")

    try:
        priority = TicketPriority(body.priority)
    except ValueError:
        priority = TicketPriority.MEDIUM

    ticket = Ticket(
        title=body.title,
        description=body.description,
        property_address=body.property_address,
        unit_number=body.unit_number,
        priority=priority,
        tenant_id=current_user.id,
        status=TicketStatus.OPEN,
    )
    db.add(ticket)
    await db.flush()
    await db.refresh(ticket)

    await _log_activity(db, ticket.id, current_user.id, "created", "Ticket created")

    # Notify all managers
    managers = await db.execute(
        select(User).where(User.role == UserRole.MANAGER, User.is_active == True)
    )
    for mgr in managers.scalars().all():
        await _notify(
            db, mgr.id,
            "New Maintenance Request",
            f"{current_user.name} submitted: {ticket.title}",
            f"/tickets/{ticket.id}",
        )

    # Re-load with relationships
    result = await db.execute(_ticket_query().where(Ticket.id == ticket.id))
    return TicketOut.model_validate(result.scalar_one())


# ── Update Ticket ─────────────────────────────────────────────────────

@router.patch("/{ticket_id}", response_model=TicketOut)
async def update_ticket(
    ticket_id: int,
    body: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        _ticket_query().where(Ticket.id == ticket_id)
    )
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Permission checks
    if current_user.role == UserRole.TENANT:
        if ticket.tenant_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        # Tenants can only update title/description on open tickets
        if ticket.status != TicketStatus.OPEN:
            raise HTTPException(status_code=400, detail="Can only edit open tickets")
        if body.status or body.technician_id or body.priority:
            raise HTTPException(status_code=403, detail="Cannot change status/assignment/priority")

    if current_user.role == UserRole.TECHNICIAN:
        if ticket.technician_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        # Technicians can only change status
        if any([body.title, body.description, body.technician_id, body.priority]):
            raise HTTPException(status_code=403, detail="Can only update status")

    changes = []

    # Handle status change with validation
    if body.status:
        try:
            new_status = TicketStatus(body.status)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid status")

        if current_user.role == UserRole.TECHNICIAN:
            # Technicians: Assigned → In Progress → Done
            allowed = VALID_TRANSITIONS.get(ticket.status, [])
            if new_status not in allowed:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot transition from {ticket.status.value} to {new_status.value}",
                )

        old_status = ticket.status.value
        ticket.status = new_status
        changes.append(f"Status: {old_status} → {new_status.value}")

        # Notify relevant parties
        if new_status == TicketStatus.DONE:
            await _notify(db, ticket.tenant_id, "Issue Resolved",
                          f"Your ticket '{ticket.title}' has been marked as done.",
                          f"/tickets/{ticket.id}")

    # Handle technician assignment
    if body.technician_id is not None and current_user.role == UserRole.MANAGER:
        tech = await db.execute(
            select(User).where(User.id == body.technician_id, User.role == UserRole.TECHNICIAN)
        )
        technician = tech.scalar_one_or_none()
        if not technician:
            raise HTTPException(status_code=400, detail="Invalid technician")

        ticket.technician_id = body.technician_id
        if ticket.status == TicketStatus.OPEN:
            ticket.status = TicketStatus.ASSIGNED
            changes.append(f"Status: open → assigned")
        changes.append(f"Assigned to {technician.name}")

        await _notify(db, technician.id, "New Assignment",
                      f"You have been assigned: {ticket.title}",
                      f"/tickets/{ticket.id}")

    # Handle priority change
    if body.priority and current_user.role == UserRole.MANAGER:
        try:
            new_priority = TicketPriority(body.priority)
            old_priority = ticket.priority.value
            ticket.priority = new_priority
            changes.append(f"Priority: {old_priority} → {new_priority.value}")
        except ValueError:
            pass

    # Handle field updates
    if body.title:
        ticket.title = body.title
        changes.append("Title updated")
    if body.description:
        ticket.description = body.description
        changes.append("Description updated")
    if body.property_address is not None:
        ticket.property_address = body.property_address
    if body.unit_number is not None:
        ticket.unit_number = body.unit_number

    if changes:
        await _log_activity(db, ticket.id, current_user.id, "updated", "; ".join(changes))

    await db.flush()
    await db.refresh(ticket)

    result = await db.execute(_ticket_query().where(Ticket.id == ticket.id))
    return TicketOut.model_validate(result.scalar_one())


# ── Upload Images ─────────────────────────────────────────────────────

@router.post("/{ticket_id}/images", response_model=list[TicketImageOut])
async def upload_images(
    ticket_id: int,
    files: list[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check ticket exists
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    # Permission – only owner or manager
    if current_user.role == UserRole.TENANT and ticket.tenant_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    if current_user.role == UserRole.TECHNICIAN and ticket.technician_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    uploaded = []

    for file in files:
        # Validate extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            continue

        # Validate size
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            continue

        # Save file
        unique_name = f"{uuid.uuid4().hex}{ext}"
        filepath = UPLOAD_DIR / unique_name
        with open(filepath, "wb") as f:
            f.write(content)

        img = TicketImage(
            ticket_id=ticket_id,
            filename=file.filename,
            filepath=f"/uploads/{unique_name}",
        )
        db.add(img)
        await db.flush()
        await db.refresh(img)
        uploaded.append(TicketImageOut.model_validate(img))

    if uploaded:
        await _log_activity(
            db, ticket_id, current_user.id, "images_uploaded",
            f"{len(uploaded)} image(s) uploaded",
        )

    return uploaded


# ── Delete Ticket ─────────────────────────────────────────────────────

@router.delete("/{ticket_id}", status_code=204)
async def delete_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.MANAGER)),
):
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    await db.delete(ticket)
