"""Seed script – populates the database with demo data."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backend.database import engine, async_session, Base
from backend.models import (
    User, UserRole, Ticket, TicketStatus, TicketPriority,
    ActivityLog, Notification,
)
from backend.auth import hash_password


async def seed():
    """Create demo users, tickets, activity logs, and notifications."""

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as db:
        print("🌱 Seeding database...")

        # ── Users ──────────────────────────────────────────────────────
        password = hash_password("password123")

        manager = User(
            email="manager@propmanage.com",
            name="Sarah Johnson",
            phone="+1 555-0100",
            password_hash=password,
            role=UserRole.MANAGER,
        )

        tenant1 = User(
            email="tenant1@propmanage.com",
            name="Alex Rivera",
            phone="+1 555-0201",
            password_hash=password,
            role=UserRole.TENANT,
        )

        tenant2 = User(
            email="tenant2@propmanage.com",
            name="Priya Sharma",
            phone="+1 555-0202",
            password_hash=password,
            role=UserRole.TENANT,
        )

        tenant3 = User(
            email="tenant3@propmanage.com",
            name="Marcus Chen",
            phone="+1 555-0203",
            password_hash=password,
            role=UserRole.TENANT,
        )

        tech1 = User(
            email="tech1@propmanage.com",
            name="Mike Torres",
            phone="+1 555-0301",
            password_hash=password,
            role=UserRole.TECHNICIAN,
        )

        tech2 = User(
            email="tech2@propmanage.com",
            name="Lisa Park",
            phone="+1 555-0302",
            password_hash=password,
            role=UserRole.TECHNICIAN,
        )

        db.add_all([manager, tenant1, tenant2, tenant3, tech1, tech2])
        await db.flush()

        print(f"  ✅ Created {6} users")

        # ── Tickets ────────────────────────────────────────────────────

        tickets_data = [
            {
                "title": "Leaking kitchen faucet",
                "description": "The kitchen faucet has been dripping constantly for the past 3 days. Water is pooling under the sink cabinet. Needs urgent attention to prevent water damage.",
                "property_address": "123 Oak Avenue, Building A",
                "unit_number": "4B",
                "status": TicketStatus.IN_PROGRESS,
                "priority": TicketPriority.HIGH,
                "tenant": tenant1,
                "technician": tech1,
            },
            {
                "title": "Broken window latch – bedroom",
                "description": "The window latch in the master bedroom is broken. Window cannot be properly closed or locked. Security concern.",
                "property_address": "123 Oak Avenue, Building A",
                "unit_number": "2A",
                "status": TicketStatus.ASSIGNED,
                "priority": TicketPriority.MEDIUM,
                "tenant": tenant2,
                "technician": tech2,
            },
            {
                "title": "AC unit not cooling",
                "description": "The central AC unit stopped cooling yesterday. Temperature in the apartment is reaching 85°F. The unit turns on but only blows warm air.",
                "property_address": "456 Maple Drive, Building C",
                "unit_number": "7D",
                "status": TicketStatus.OPEN,
                "priority": TicketPriority.URGENT,
                "tenant": tenant3,
                "technician": None,
            },
            {
                "title": "Clogged bathroom drain",
                "description": "The bathtub drain is completely clogged. Water takes over 30 minutes to drain. Tried using a plunger but did not help.",
                "property_address": "123 Oak Avenue, Building B",
                "unit_number": "1C",
                "status": TicketStatus.DONE,
                "priority": TicketPriority.MEDIUM,
                "tenant": tenant1,
                "technician": tech1,
            },
            {
                "title": "Flickering hallway lights",
                "description": "The hallway lights on the 3rd floor flicker intermittently. Multiple bulbs have been replaced but the issue persists. May be an electrical wiring problem.",
                "property_address": "456 Maple Drive, Building C",
                "unit_number": "Common Area",
                "status": TicketStatus.OPEN,
                "priority": TicketPriority.LOW,
                "tenant": tenant2,
                "technician": None,
            },
            {
                "title": "Garage door not opening",
                "description": "The main garage door (entrance B) is stuck and won't open with the remote or wall button. Motor makes a grinding noise. Blocking vehicle access for several tenants.",
                "property_address": "789 Pine Street",
                "unit_number": "Garage B",
                "status": TicketStatus.ASSIGNED,
                "priority": TicketPriority.HIGH,
                "tenant": tenant3,
                "technician": tech1,
            },
            {
                "title": "Water heater temperature issue",
                "description": "Hot water temperature is inconsistent. Sometimes scalding, sometimes lukewarm. Thermostat may need recalibration.",
                "property_address": "123 Oak Avenue, Building A",
                "unit_number": "5A",
                "status": TicketStatus.OPEN,
                "priority": TicketPriority.MEDIUM,
                "tenant": tenant1,
                "technician": None,
            },
            {
                "title": "Pest control needed – ants",
                "description": "There is a significant ant infestation in the kitchen and bathroom area. Found ant trails along the baseboards and near the sink. Need professional pest control.",
                "property_address": "456 Maple Drive, Building C",
                "unit_number": "3B",
                "status": TicketStatus.DONE,
                "priority": TicketPriority.MEDIUM,
                "tenant": tenant2,
                "technician": tech2,
            },
        ]

        for td in tickets_data:
            ticket = Ticket(
                title=td["title"],
                description=td["description"],
                property_address=td["property_address"],
                unit_number=td["unit_number"],
                status=td["status"],
                priority=td["priority"],
                tenant_id=td["tenant"].id,
                technician_id=td["technician"].id if td["technician"] else None,
            )
            db.add(ticket)
            await db.flush()

            # Add activity logs
            log1 = ActivityLog(
                ticket_id=ticket.id,
                user_id=td["tenant"].id,
                action="created",
                details="Ticket created",
            )
            db.add(log1)

            if td["technician"]:
                log2 = ActivityLog(
                    ticket_id=ticket.id,
                    user_id=manager.id,
                    action="assigned",
                    details=f"Assigned to {td['technician'].name}",
                )
                db.add(log2)

            if td["status"] == TicketStatus.IN_PROGRESS:
                log3 = ActivityLog(
                    ticket_id=ticket.id,
                    user_id=td["technician"].id,
                    action="status_change",
                    details="Status: assigned → in_progress",
                )
                db.add(log3)

            if td["status"] == TicketStatus.DONE:
                log4 = ActivityLog(
                    ticket_id=ticket.id,
                    user_id=td["technician"].id,
                    action="status_change",
                    details="Status: in_progress → done",
                )
                db.add(log4)

        await db.flush()
        print(f"  ✅ Created {len(tickets_data)} tickets with activity logs")

        # ── Notifications ──────────────────────────────────────────────
        notifications = [
            Notification(user_id=manager.id, title="New Request", message="Alex Rivera submitted: Leaking kitchen faucet", link="/tickets/1"),
            Notification(user_id=manager.id, title="New Request", message="Priya Sharma submitted: Broken window latch", link="/tickets/2"),
            Notification(user_id=manager.id, title="New Request", message="Marcus Chen submitted: AC unit not cooling", link="/tickets/3"),
            Notification(user_id=tech1.id, title="New Assignment", message="You have been assigned: Leaking kitchen faucet", link="/tickets/1", is_read=True),
            Notification(user_id=tech1.id, title="New Assignment", message="You have been assigned: Garage door not opening", link="/tickets/6"),
            Notification(user_id=tech2.id, title="New Assignment", message="You have been assigned: Broken window latch", link="/tickets/2"),
            Notification(user_id=tenant1.id, title="Issue Resolved", message="Your ticket 'Clogged bathroom drain' has been marked as done.", link="/tickets/4"),
            Notification(user_id=tenant2.id, title="Issue Resolved", message="Your ticket 'Pest control needed – ants' has been marked as done.", link="/tickets/8"),
        ]

        db.add_all(notifications)
        await db.flush()
        await db.commit()

        print(f"  ✅ Created {len(notifications)} notifications")
        print("\n🎉 Database seeded successfully!\n")
        print("Demo Credentials (all passwords: password123):")
        print("  Manager:    manager@propmanage.com")
        print("  Tenant 1:   tenant1@propmanage.com")
        print("  Tenant 2:   tenant2@propmanage.com")
        print("  Tenant 3:   tenant3@propmanage.com")
        print("  Technician: tech1@propmanage.com")
        print("  Technician: tech2@propmanage.com")


if __name__ == "__main__":
    asyncio.run(seed())
