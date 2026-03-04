# PropManage – Complete Documentation

> **Property Maintenance Management System**
> A mobile-first web application for managing property maintenance requests with role-based access control.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [Project Structure](#3-project-structure)
4. [Getting Started](#4-getting-started)
5. [Database Models (In Detail)](#5-database-models-in-detail)
6. [Pydantic Schemas](#6-pydantic-schemas)
7. [Authentication System](#7-authentication-system)
8. [API Routes – How They Work](#8-api-routes--how-they-work)
9. [Frontend Architecture](#9-frontend-architecture)
10. [Working Flow for Every Action](#10-working-flow-for-every-action)
11. [Role-Based Access Control](#11-role-based-access-control)
12. [File Upload System](#12-file-upload-system)
13. [Configuration Reference](#13-configuration-reference)
14. [Demo Accounts](#14-demo-accounts)

---

## 1. Project Overview

PropManage is a **property maintenance management system** that allows:

- **Tenants** to submit and track maintenance requests (e.g., broken faucet, AC issue)
- **Managers** to oversee all tickets, assign technicians, and manage priorities
- **Technicians** to view their assigned tasks and update progress

The app features:
- JWT-based authentication with role-based access
- Real-time dashboard statistics
- Ticket lifecycle management with status workflow enforcement
- Image uploads for tickets and profile avatars
- In-app notification system
- Mobile-first responsive design (works on phone, tablet, and desktop)

---

## 2. Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Backend Framework** | FastAPI 0.131.0 | Async Python web framework with automatic OpenAPI docs |
| **ORM** | SQLAlchemy 2.0 (async) | Database models and queries |
| **Database** | SQLite via aiosqlite | Lightweight file-based database |
| **Auth** | python-jose + passlib + bcrypt 4.0.1 | JWT tokens + password hashing |
| **Validation** | Pydantic v2 | Request/response schema validation |
| **Image Processing** | Pillow | Image validation support |
| **Frontend** | Vanilla HTML5, CSS3, ES6+ JavaScript | No framework dependencies |
| **Server** | Uvicorn | ASGI server with hot-reload |

> **Note:** bcrypt is pinned to version 4.0.1 because passlib 1.7.4 is incompatible with bcrypt 5.x.

---

## 3. Project Structure

```
qwego/
├── backend/                    # Python backend package
│   ├── __init__.py
│   ├── config.py               # App configuration (DB URL, JWT settings, upload limits)
│   ├── database.py             # SQLAlchemy engine, session factory, Base class
│   ├── models.py               # ORM models (User, Ticket, TicketImage, ActivityLog, Notification)
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── auth.py                 # Password hashing, JWT creation/verification, auth dependencies
│   └── routers/                # API route handlers
│       ├── auth_routes.py      # Login, register, profile, avatar upload
│       ├── tickets.py          # CRUD, assignment, status flow, image upload, stats
│       ├── users.py            # User listing (manager only)
│       └── notifications.py    # List, mark read, unread count
│
├── frontend/                   # Static frontend files
│   ├── index.html              # Single-page app (all pages in one HTML file)
│   ├── css/
│   │   └── styles.css          # Mobile-first responsive stylesheet
│   └── js/
│       ├── api.js              # HTTP client with JWT handling
│       ├── auth.js             # Login/register form logic
│       ├── tickets.js          # Ticket CRUD, filters, dashboard
│       ├── notifications.js    # Notification list and actions
│       ├── profile.js          # Profile editing and avatar upload
│       └── app.js              # App initialization, routing, navigation
│
├── data/                       # SQLite database folder (auto-created)
│   └── app.db
├── uploads/                    # Uploaded files (auto-created)
│   └── avatars/                # Profile pictures
│
├── seed_data.py                # Database seeder with demo data
├── run.py                      # Development server launcher
├── requirements.txt            # Python dependencies
├── Dockerfile                  # Docker container configuration
├── docker-compose.yml          # Docker Compose setup
├── .gitignore                  # Git ignore rules
└── README.md                   # Quick-start guide
```

---

## 4. Getting Started

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# 1. Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate          # Windows
# source venv/bin/activate       # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Seed the database with demo data
python seed_data.py

# 4. Start the server
python run.py
```

The app runs at **http://localhost:8000**

### Quick Test
Open http://localhost:8000 in your browser. Login with:
- **Email:** `manager@propmanage.com`
- **Password:** `password123`

---

## 5. Database Models (In Detail)

All models are defined in `backend/models.py` using SQLAlchemy's `DeclarativeBase` pattern.

### 5.1 Enums

Three enums control the valid values for roles, statuses, and priorities:

```
UserRole:      tenant | manager | technician
TicketStatus:  open | assigned | in_progress | done
TicketPriority: low | medium | high | urgent
```

### 5.2 User Model

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | Integer | Primary Key, Auto-increment | Unique user identifier |
| `email` | String(255) | Unique, Indexed, Not Null | Login email address |
| `name` | String(255) | Not Null | Display name |
| `phone` | String(50) | Nullable | Contact phone number |
| `bio` | Text | Nullable | User's "about me" text (editable via profile) |
| `avatar_url` | String(500) | Nullable | Path to uploaded profile picture (e.g., `/uploads/avatars/avatar_1_abc123.jpg`) |
| `password_hash` | String(255) | Not Null | bcrypt-hashed password (never stored in plain text) |
| `role` | Enum(UserRole) | Not Null, Default: `tenant` | One of: `tenant`, `manager`, `technician` |
| `is_active` | Boolean | Default: `True` | Soft-delete flag. Inactive users cannot log in |
| `created_at` | DateTime(tz) | Default: `utcnow()` | Account creation timestamp |

**Relationships:**
- `submitted_tickets` → Tickets this user submitted (as tenant). Foreign key: `Ticket.tenant_id`
- `assigned_tickets` → Tickets assigned to this user (as technician). Foreign key: `Ticket.technician_id`
- `activity_logs` → All activity log entries by this user
- `notifications` → All notifications sent to this user

**How it works:** Every person who uses the system has a User record. The `role` field determines what they can see and do. A tenant sees only their own tickets. A manager sees everything. A technician sees only tickets assigned to them.

---

### 5.3 Ticket Model

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | Integer | Primary Key | Unique ticket identifier |
| `title` | String(255) | Not Null | Short summary (e.g., "Kitchen faucet leaking") |
| `description` | Text | Not Null | Detailed description of the issue |
| `property_address` | String(500) | Nullable | Property location |
| `unit_number` | String(50) | Nullable | Apartment/unit number |
| `status` | Enum(TicketStatus) | Not Null, Default: `open` | Current workflow stage |
| `priority` | Enum(TicketPriority) | Not Null, Default: `medium` | Urgency level |
| `tenant_id` | Integer | Foreign Key → `users.id`, Not Null | Who submitted this ticket |
| `technician_id` | Integer | Foreign Key → `users.id`, Nullable | Who is assigned to fix it (initially null) |
| `created_at` | DateTime(tz) | Default: `utcnow()` | When the ticket was created |
| `updated_at` | DateTime(tz) | Default: `utcnow()`, Auto-update | Last modification time |

**Relationships:**
- `tenant` → The User who submitted this ticket
- `technician` → The User assigned to fix it (can be null)
- `images` → List of attached TicketImage records (cascade delete)
- `activity_logs` → History of all changes (cascade delete)

**Status Workflow (Enforced by Backend):**
```
 ┌──────┐   assign    ┌──────────┐  start work  ┌─────────────┐  complete  ┌──────┐
 │ OPEN │ ──────────→ │ ASSIGNED │ ────────────→ │ IN_PROGRESS │ ────────→ │ DONE │
 └──────┘             └──────────┘               └─────────────┘           └──────┘
    ↑                      │                           │                       │
    │                      └─── can revert to OPEN ────┘                       │
    │                                                                          │
    └──────────────── can re-open from DONE ───────────────────────────────────┘
```

**Valid transitions enforced in code:**
| From | Allowed → To |
|------|-------------|
| `open` | `assigned` |
| `assigned` | `in_progress`, `open` |
| `in_progress` | `done`, `assigned` |
| `done` | `open` (re-open) |

Any other transition is rejected with a 400 error.

---

### 5.4 TicketImage Model

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | Integer | Primary Key | Image record ID |
| `ticket_id` | Integer | Foreign Key → `tickets.id`, Not Null | Which ticket this image belongs to |
| `filename` | String(255) | Not Null | Original filename uploaded by user |
| `filepath` | String(500) | Not Null | Server path (e.g., `/uploads/abc123.jpg`) |
| `uploaded_at` | DateTime(tz) | Default: `utcnow()` | Upload timestamp |

**How it works:** When a tenant creates a ticket, they can attach photos of the issue. Each photo becomes a TicketImage record. The actual file is stored in the `uploads/` directory. The `filepath` is a URL path served by the static file mount.

---

### 5.5 ActivityLog Model

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | Integer | Primary Key | Log entry ID |
| `ticket_id` | Integer | Foreign Key → `tickets.id`, Not Null | Which ticket this action relates to |
| `user_id` | Integer | Foreign Key → `users.id`, Not Null | Who performed the action |
| `action` | String(100) | Not Null | Action type (e.g., `created`, `updated`, `images_uploaded`) |
| `details` | Text | Nullable | Human-readable description (e.g., "Status: open → assigned; Assigned to Mike") |
| `created_at` | DateTime(tz) | Default: `utcnow()` | When the action occurred |

**How it works:** Every significant change to a ticket creates an ActivityLog entry. This gives a complete timeline visible on the ticket detail page. Examples: ticket creation, status changes, assignments, edits, image uploads.

---

### 5.6 Notification Model

| Column | Type | Constraints | Description |
|--------|------|------------|-------------|
| `id` | Integer | Primary Key | Notification ID |
| `user_id` | Integer | Foreign Key → `users.id`, Not Null | Who receives this notification |
| `title` | String(255) | Not Null | Notification headline |
| `message` | Text | Not Null | Notification body text |
| `is_read` | Boolean | Default: `False` | Whether the user has seen it |
| `link` | String(500) | Nullable | Optional deep link (e.g., `/tickets/5`) |
| `created_at` | DateTime(tz) | Default: `utcnow()` | When the notification was created |

**How it works:** Notifications are created automatically when significant events happen:
- **Ticket created** → All managers get notified
- **Ticket assigned** → The assigned technician gets notified
- **Ticket done** → The tenant who submitted it gets notified

Users see an unread count badge in the sidebar and can mark notifications as read individually or all at once.

---

## 6. Pydantic Schemas

Schemas in `backend/schemas.py` validate all incoming requests and shape outgoing responses.

### Request Schemas

| Schema | Fields | Used By |
|--------|--------|---------|
| `LoginRequest` | `email` (EmailStr), `password` (str) | `POST /api/auth/login` |
| `RegisterRequest` | `email`, `name`, `phone?`, `password`, `role` (default: "tenant") | `POST /api/auth/register` |
| `ProfileUpdate` | `name?`, `phone?`, `bio?` (all optional) | `PATCH /api/auth/profile` |
| `TicketCreate` | `title`, `description`, `property_address?`, `unit_number?`, `priority` (default: "medium") | `POST /api/tickets/` |
| `TicketUpdate` | `title?`, `description?`, `property_address?`, `unit_number?`, `status?`, `priority?`, `technician_id?` | `PATCH /api/tickets/{id}` |

### Response Schemas

| Schema | Fields | Description |
|--------|--------|-------------|
| `UserOut` | id, email, name, phone, bio, avatar_url, role, is_active, created_at | User information (never includes password) |
| `TokenResponse` | access_token, token_type, user (UserOut) | Returned after login/register |
| `TicketOut` | All ticket fields + tenant (UserOut) + technician (UserOut) + images | Ticket with joined user data |
| `TicketDetailOut` | Everything in TicketOut + activity_logs | Full ticket view with history |
| `TicketImageOut` | id, filename, filepath, uploaded_at | Image metadata |
| `ActivityLogOut` | id, action, details, created_at, user (UserOut) | Change history entry |
| `NotificationOut` | id, title, message, is_read, link, created_at | Notification data |
| `DashboardStats` | total/open/assigned/in_progress/done ticket counts + unread notifications | Dashboard card data |

---

## 7. Authentication System

Located in `backend/auth.py`. The system uses **JWT (JSON Web Tokens)** with **bcrypt password hashing**.

### 7.1 Password Hashing

```
User enters: "password123"
     ↓ hash_password()
Stored in DB: "$2b$12$Xyz..." (bcrypt hash, 60 chars)

User logs in: "password123"
     ↓ verify_password(plain, stored_hash)
Returns: True/False
```

The raw password is **never stored**. bcrypt is a one-way hash with built-in salt, so even identical passwords produce different hashes.

### 7.2 JWT Token Flow

```
1. User sends:      POST /api/auth/login { email, password }
2. Server verifies: password matches stored hash
3. Server creates:  JWT token containing { sub: user_id, role: user_role, exp: +24h }
4. Server returns:  { access_token: "eyJ...", token_type: "bearer", user: {...} }
5. Client stores:   token in localStorage
6. Every request:   Authorization: Bearer eyJ...
7. Server decodes:  JWT → extracts user_id → loads user from DB → proceeds
```

**Token contents (payload):**
| Field | Value | Purpose |
|-------|-------|---------|
| `sub` | User ID (e.g., "1") | Identifies who this token belongs to |
| `role` | User role (e.g., "manager") | Used in token payload |
| `exp` | Expiration timestamp | Token auto-expires after 24 hours |

### 7.3 Auth Dependencies

Two FastAPI dependencies protect routes:

1. **`get_current_user`** – Extracts the JWT from the `Authorization` header, decodes it, loads the User from the database, and returns it. Returns 401 if token is missing/invalid/expired or user doesn't exist.

2. **`require_role(*roles)`** – A factory that creates a dependency. Calls `get_current_user` first, then checks if the user's role is in the allowed list. Returns 403 if not.

**Usage in routes:**
```python
# Any authenticated user:
async def my_route(current_user: User = Depends(get_current_user)):

# Only managers:
async def admin_route(user: User = Depends(require_role(UserRole.MANAGER))):
```

---

## 8. API Routes – How They Work

### 8.1 Auth Routes (`/api/auth`)

**File:** `backend/routers/auth_routes.py`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | No | Create new account |
| POST | `/api/auth/login` | No | Login and get JWT token |
| GET | `/api/auth/me` | Yes | Get current user's profile |
| PATCH | `/api/auth/profile` | Yes | Update name, phone, bio |
| POST | `/api/auth/profile/avatar` | Yes | Upload profile picture |

#### POST /api/auth/register
**Request body:**
```json
{
  "email": "user@example.com",
  "name": "John Doe",
  "phone": "+1 555-1234",
  "password": "securepass",
  "role": "tenant"
}
```
**What happens:**
1. Checks if email is already taken (400 if duplicate)
2. Validates role is one of: tenant, manager, technician
3. Hashes the password with bcrypt
4. Creates User record in database
5. Generates JWT token
6. Returns `{ access_token, user }` with status 201

#### POST /api/auth/login
**Request body:**
```json
{
  "email": "manager@propmanage.com",
  "password": "password123"
}
```
**What happens:**
1. Looks up user by email
2. Verifies password against stored hash (401 if wrong)
3. Checks `is_active` flag (403 if deactivated)
4. Generates JWT token with user ID and role
5. Returns `{ access_token, user }`

#### GET /api/auth/me
**Headers:** `Authorization: Bearer <token>`
**What happens:**
1. `get_current_user` dependency decodes the JWT
2. Loads User from DB by ID
3. Returns UserOut (includes bio, avatar_url, role, etc.)

#### PATCH /api/auth/profile
**Headers:** `Authorization: Bearer <token>`
**Request body (all fields optional):**
```json
{
  "name": "New Name",
  "phone": "+1 555-9999",
  "bio": "I manage 50+ units downtown"
}
```
**What happens:**
1. Authenticates user via JWT
2. Updates only the fields that are not null
3. Strips whitespace from values
4. Returns updated UserOut

#### POST /api/auth/profile/avatar
**Headers:** `Authorization: Bearer <token>`
**Body:** multipart/form-data with `file` field
**What happens:**
1. Authenticates user via JWT
2. Validates file extension (jpg, png, gif, webp only)
3. Checks file size (max 5MB)
4. Saves file as `avatar_{userId}_{randomHex}.ext` in `uploads/avatars/`
5. Updates user's `avatar_url` to the new path
6. Returns updated UserOut

---

### 8.2 Ticket Routes (`/api/tickets`)

**File:** `backend/routers/tickets.py`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/tickets/stats` | Yes | Dashboard statistics |
| GET | `/api/tickets/` | Yes | List tickets (filtered by role) |
| GET | `/api/tickets/{id}` | Yes | Get ticket detail with activity log |
| POST | `/api/tickets/` | Yes* | Create new ticket (*not technicians) |
| PATCH | `/api/tickets/{id}` | Yes | Update ticket (role-restricted) |
| DELETE | `/api/tickets/{id}` | Manager | Delete a ticket |
| POST | `/api/tickets/{id}/images` | Yes | Upload images to ticket |

#### GET /api/tickets/stats
Returns dashboard card data. **Results are role-filtered:**
- **Tenant:** Only counts their own tickets
- **Technician:** Only counts tickets assigned to them
- **Manager:** Counts all tickets

**Response:**
```json
{
  "total_tickets": 8,
  "open_tickets": 2,
  "assigned_tickets": 2,
  "in_progress_tickets": 2,
  "done_tickets": 2,
  "unread_notifications": 3
}
```

#### GET /api/tickets/
**Query parameters:**
| Param | Type | Example | Description |
|-------|------|---------|-------------|
| `status` | string | `open` | Filter by status |
| `priority` | string | `high` | Filter by priority |
| `search` | string | `faucet` | Search in title and description |

**Role-based visibility:**
- Tenant → sees only `where tenant_id = current_user.id`
- Technician → sees only `where technician_id = current_user.id`
- Manager → sees all tickets

Returns tickets ordered by `created_at DESC`, each including tenant, technician, and images via eager loading.

#### GET /api/tickets/{id}
Returns full ticket detail including `activity_logs` (change history). Same role-based access restrictions apply. The activity logs show the complete timeline of actions on the ticket.

#### POST /api/tickets/
**Who can use:** Tenants and Managers (technicians get 403)
**Request body:**
```json
{
  "title": "Bathroom sink clogged",
  "description": "The sink in unit 3B drains very slowly...",
  "property_address": "123 Main St",
  "unit_number": "3B",
  "priority": "high"
}
```
**What happens:**
1. Validates user is not a technician
2. Creates Ticket with status `open` and `tenant_id` = current user
3. Creates an ActivityLog entry ("Ticket created")
4. Sends Notification to **all active managers** ("New Maintenance Request")
5. Returns the created ticket with 201 status

#### PATCH /api/tickets/{id}
**Complex endpoint with role-based restrictions:**

**Tenant restrictions:**
- Can only edit their own tickets
- Can only edit when status is `open`
- Can only change title and description (not status, priority, or assignment)

**Technician restrictions:**
- Can only edit tickets assigned to them
- Can only change status (nothing else)
- Status transitions are validated against the `VALID_TRANSITIONS` map

**Manager permissions:**
- Can edit any ticket
- Can change status, priority, fields, and assign technicians
- When assigning a technician: auto-changes status from `open` → `assigned`
- Assignment sends a Notification to the technician

**Special behaviors:**
- Marking a ticket `done` → notifies the tenant
- All changes create ActivityLog entries with details like "Status: open → assigned; Assigned to Mike Wilson"

#### DELETE /api/tickets/{id}
**Manager only.** Permanently deletes the ticket and all related images/activity logs (via cascade).

#### POST /api/tickets/{id}/images
Upload one or more images to a ticket. Files are validated (extension + size), saved with UUID filenames in `uploads/`, and linked to the ticket via TicketImage records. Creates an activity log entry.

---

### 8.3 User Routes (`/api/users`)

**File:** `backend/routers/users.py`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/users/` | Manager | List all active users (optional role filter) |
| GET | `/api/users/technicians` | Manager | List available technicians |

Both endpoints are **manager-only** (enforced by `require_role(UserRole.MANAGER)`).

#### GET /api/users/?role=technician
Lists active users. The `role` query param filters results. Used by the manager's admin panel.

#### GET /api/users/technicians
Convenience endpoint that returns only technicians, sorted by name. Used to populate the "Assign Technician" dropdown.

---

### 8.4 Notification Routes (`/api/notifications`)

**File:** `backend/routers/notifications.py`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/notifications/` | Yes | List user's notifications (latest 50) |
| GET | `/api/notifications/unread-count` | Yes | Get unread notification count |
| PATCH | `/api/notifications/{id}/read` | Yes | Mark one notification as read |
| PATCH | `/api/notifications/read-all` | Yes | Mark all notifications as read |

**How notifications flow:**
1. System events create Notification records (see Ticket Routes for triggers)
2. Frontend periodically checks unread count (displayed as badge)
3. Notifications page shows all notifications sorted by newest first
4. Users can mark individual or all notifications as read

---

## 9. Frontend Architecture

The frontend is a **Single-Page Application (SPA)** built with vanilla JavaScript – no React, Vue, or other framework.

### 9.1 How the SPA Works

**index.html** contains ALL pages as hidden `<section>` elements:
```html
<section id="page-dashboard" class="page hidden">...</section>
<section id="page-tickets" class="page hidden">...</section>
<section id="page-profile" class="page hidden">...</section>
<!-- etc. -->
```

Navigation works by:
1. Hiding all sections (add `hidden` class)
2. Showing the target section (remove `hidden` class)
3. Loading data for that page via API calls

This is handled by the `showPage(pageName)` function in `app.js`.

### 9.2 JavaScript Modules

Each JS file is an IIFE (Immediately Invoked Function Expression) that exposes a global module:

| Module | Global Name | Responsibility |
|--------|------------|----------------|
| `api.js` | `window.API` | HTTP client, token storage, auth state |
| `auth.js` | `window.Auth` | Login/register form handlers |
| `tickets.js` | `window.Tickets` | All ticket operations |
| `notifications.js` | `window.Notifications` | Notification list and actions |
| `profile.js` | `window.Profile` | Profile editing and avatar upload |
| `app.js` | (self-executing) | App init, routing, navigation |

### 9.3 API Module (`api.js`)

Central HTTP client that all other modules use:

```javascript
API.get('/tickets/')           // GET with auth header
API.post('/auth/login', data)  // POST JSON
API.patch('/tickets/5', data)  // PATCH JSON
API.delete('/tickets/5')       // DELETE
API.upload('/tickets/5/images', formData) // POST multipart/form-data
```

**Token management:**
- `API.getToken()` / `API.setToken(token)` – stored in `localStorage`
- `API.getUser()` / `API.setUser(user)` – stored in `localStorage` as JSON
- `API.clearToken()` – removes both, used on logout

**Auto-redirect:** If any API call returns 401 (unauthorized), the module automatically clears the token and redirects to the login screen.

### 9.4 CSS Architecture (`styles.css`)

**Mobile-first responsive design** using CSS custom properties (variables):

```css
:root {
  --primary: #4F46E5;       /* Indigo – main brand color */
  --primary-light: #818CF8;
  --success: #10B981;       /* Green */
  --warning: #F59E0B;       /* Amber */
  --danger: #EF4444;        /* Red */
  --text: #1F2937;
  --text-light: #6B7280;
  --bg: #F9FAFB;
  --radius: 12px;
}
```

**Three breakpoints:**
| Breakpoint | Target | Layout |
|-----------|--------|--------|
| Base (0px+) | Mobile phones | Single column, bottom navigation |
| 600px+ | Tablets | Sidebar becomes visible |
| 900px+ | Desktops | Full sidebar + wider content area |

---

## 10. Working Flow for Every Action

### 10.1 User Login Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User opens http://localhost:8000                             │
│ 2. app.js checks: is there a token in localStorage?            │
│    ├─ NO  → Show login screen                                  │
│    └─ YES → Show dashboard, call API.get('/tickets/stats')     │
│                                                                 │
│ 3. User enters email + password, clicks "Sign In"              │
│ 4. auth.js calls: API.post('/auth/login', {email, password})   │
│ 5. Backend: looks up user → verifies password → creates JWT    │
│ 6. Frontend receives: { access_token, user }                   │
│ 7. auth.js stores token + user in localStorage                 │
│ 8. app.js → setupUserUI() → shows name, role badge, avatar    │
│ 9. app.js → showPage('dashboard') → loads stats + ticket list  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 Creating a Maintenance Ticket (Tenant)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Tenant clicks "New Ticket" button                           │
│ 2. showPage('create-ticket') → shows the form                 │
│ 3. Tenant fills in: title, description, address, unit, priority│
│ 4. Tenant optionally attaches photos (preview shown)           │
│ 5. Tenant clicks "Submit Request"                              │
│                                                                 │
│ 6. tickets.js calls: API.post('/tickets/', ticketData)         │
│ 7. Backend:                                                     │
│    a. Creates Ticket (status: open, tenant_id: current user)   │
│    b. Creates ActivityLog ("Ticket created")                   │
│    c. Creates Notification for each active manager             │
│ 8. If images were attached:                                    │
│    API.upload('/tickets/{id}/images', formData)                 │
│    → Backend saves files, creates TicketImage records           │
│                                                                 │
│ 9. Frontend redirects to ticket detail page                    │
│ 10. Manager sees notification: "John submitted: Kitchen leak"  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.3 Assigning a Technician (Manager)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Manager views a ticket with status "open"                   │
│ 2. Clicks "Assign Technician" button                           │
│ 3. Modal opens with dropdown of available technicians          │
│    (fetched from GET /api/users/technicians)                   │
│ 4. Manager selects "Mike Wilson" and confirms                  │
│                                                                 │
│ 5. tickets.js calls:                                            │
│    API.patch('/tickets/{id}', { technician_id: 5 })            │
│ 6. Backend:                                                     │
│    a. Validates technician exists and has the right role        │
│    b. Sets ticket.technician_id = 5                             │
│    c. Auto-changes status: open → assigned                      │
│    d. Creates ActivityLog ("Assigned to Mike Wilson")           │
│    e. Creates Notification for Mike: "New Assignment"           │
│                                                                 │
│ 7. Frontend refreshes ticket detail, shows new status          │
│ 8. Mike sees notification: "You have been assigned: ..."       │
└─────────────────────────────────────────────────────────────────┘
```

### 10.4 Technician Workflow (Status Updates)

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Technician logs in → sees only assigned tickets             │
│ 2. Opens ticket with status "assigned"                         │
│ 3. Clicks "Start Work" button                                  │
│                                                                 │
│ 4. tickets.js calls:                                            │
│    API.patch('/tickets/{id}', { status: "in_progress" })       │
│ 5. Backend:                                                     │
│    a. Validates: assigned → in_progress is allowed ✓           │
│    b. Updates status                                            │
│    c. Creates ActivityLog                                       │
│                                                                 │
│ 6. Later, technician clicks "Mark Done"                        │
│ 7. API.patch('/tickets/{id}', { status: "done" })              │
│ 8. Backend:                                                     │
│    a. Validates: in_progress → done is allowed ✓               │
│    b. Updates status                                            │
│    c. Creates ActivityLog                                       │
│    d. Creates Notification for tenant: "Issue Resolved"        │
│                                                                 │
│ 9. Tenant sees notification: "Your ticket has been resolved"   │
└─────────────────────────────────────────────────────────────────┘
```

### 10.5 Editing Profile

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User clicks avatar (top-right) or profile nav item          │
│ 2. showPage('profile') → profile.js loads /api/auth/me         │
│ 3. Profile page shows:                                          │
│    - Current avatar (or initials circle)                       │
│    - Edit avatar button (camera icon)                          │
│    - Name, email (read-only), role badge, phone, bio fields    │
│                                                                 │
│ 4. To change avatar:                                            │
│    a. Click camera icon → file picker opens                    │
│    b. Select image → profile.js calls:                         │
│       API.upload('/auth/profile/avatar', formData)             │
│    c. Backend saves file, returns updated user                  │
│    d. Avatar preview updates immediately                       │
│                                                                 │
│ 5. To change name/phone/bio:                                   │
│    a. Edit fields → click "Save Changes"                       │
│    b. profile.js calls:                                         │
│       API.patch('/auth/profile', { name, phone, bio })         │
│    c. Backend updates user record, returns updated data        │
│    d. Success toast appears                                     │
│    e. localStorage user object is updated                      │
│    f. Top bar name/avatar refresh                              │
│                                                                 │
│ 6. Logout button at bottom of profile page                     │
│    → Clears token + user from localStorage → shows login       │
└─────────────────────────────────────────────────────────────────┘
```

### 10.6 Notification Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│ Automatic triggers that create notifications:                   │
│ ├─ Ticket created       → All managers notified                │
│ ├─ Technician assigned  → Technician notified                  │
│ └─ Ticket marked done   → Tenant notified                     │
│                                                                 │
│ Frontend:                                                       │
│ 1. Sidebar shows bell icon with unread count badge             │
│ 2. User clicks "Notifications" → loads GET /notifications/     │
│ 3. Each notification shows title, message, time ago            │
│ 4. "Mark all read" button → PATCH /notifications/read-all     │
│ 5. Unread count badge updates to 0                             │
└─────────────────────────────────────────────────────────────────┘
```

### 10.7 Dashboard Stats Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User navigates to Dashboard page                            │
│ 2. tickets.js calls GET /api/tickets/stats                     │
│ 3. Backend counts tickets filtered by user's role:             │
│    - Tenant: only their tickets                                │
│    - Technician: only assigned tickets                         │
│    - Manager: all tickets                                      │
│ 4. Returns: { total, open, assigned, in_progress, done,        │
│               unread_notifications }                           │
│ 5. Frontend renders 5 stat cards with counts                   │
│ 6. Also loads ticket list below the stats                      │
└─────────────────────────────────────────────────────────────────┘
```

### 10.8 Search and Filter Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. User is on the Tickets page                                 │
│ 2. Types in search box → debounced (300ms) → API call          │
│ 3. Selects status filter dropdown → immediate API call          │
│ 4. Selects priority filter dropdown → immediate API call        │
│                                                                 │
│ All combined into: GET /api/tickets/?search=X&status=Y&priority=Z│
│ Backend applies all filters together                           │
│ Results re-render in the ticket list                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 11. Role-Based Access Control

### What Each Role Can Do

| Action | Tenant | Manager | Technician |
|--------|--------|---------|------------|
| **View dashboard** | Own stats | All stats | Assigned stats |
| **Create ticket** | ✅ | ✅ | ❌ |
| **View tickets** | Own only | All | Assigned only |
| **Edit ticket fields** | Own + open only | Any ticket | ❌ |
| **Change status** | ❌ | ✅ Any | ✅ Valid transitions only |
| **Change priority** | ❌ | ✅ | ❌ |
| **Assign technician** | ❌ | ✅ | ❌ |
| **Delete ticket** | ❌ | ✅ | ❌ |
| **Upload ticket images** | Own tickets | Any ticket | Assigned tickets |
| **View users list** | ❌ | ✅ | ❌ |
| **Edit own profile** | ✅ | ✅ | ✅ |
| **Upload avatar** | ✅ | ✅ | ✅ |
| **View notifications** | ✅ Own | ✅ Own | ✅ Own |

### How Permissions Are Enforced

1. **Route level:** `require_role()` dependency blocks unauthorized roles entirely
2. **Handler level:** Code inside handlers checks ownership (e.g., `ticket.tenant_id == current_user.id`)
3. **Query level:** Database queries filter results by role automatically
4. **Frontend level:** UI buttons/actions are shown/hidden based on role (but the real security is always on the backend)

---

## 12. File Upload System

### Configuration (in `config.py`)

| Setting | Value | Description |
|---------|-------|-------------|
| `UPLOAD_DIR` | `<project>/uploads/` | Where files are stored on disk |
| `MAX_FILE_SIZE` | 5 MB (5,242,880 bytes) | Maximum upload size |
| `ALLOWED_EXTENSIONS` | `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp` | Valid image formats |

### Upload Types

1. **Ticket Images** (`POST /api/tickets/{id}/images`)
   - Supports multiple files per request
   - Saved as `{uuid_hex}.{ext}` in `uploads/`
   - Served at `/uploads/{filename}`

2. **Profile Avatars** (`POST /api/auth/profile/avatar`)
   - Single file per request
   - Saved as `avatar_{userId}_{randomHex}.{ext}` in `uploads/avatars/`
   - Served at `/uploads/avatars/{filename}`

### How Files Are Served

In `main.py`, uploaded files are mounted as static files:
```python
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
```
This means a file at `uploads/avatars/avatar_1_abc123.jpg` is accessible via `http://localhost:8000/uploads/avatars/avatar_1_abc123.jpg`.

---

## 13. Configuration Reference

All settings in `backend/config.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_DIR` | Project root | Auto-detected from file location |
| `DATABASE_URL` | `sqlite+aiosqlite:///data/app.db` | Async SQLite connection string |
| `SECRET_KEY` | `propmanage-secret-key-change-in-production-2026` | JWT signing key (**change in production!**) |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` (24 hours) | Token expiry time |
| `UPLOAD_DIR` | `<project>/uploads/` | File storage directory |
| `MAX_FILE_SIZE` | `5242880` (5MB) | Max upload size in bytes |
| `ALLOWED_EXTENSIONS` | `.jpg .jpeg .png .gif .webp` | Valid upload formats |
| `APP_NAME` | `PropManage` | Application name |
| `APP_VERSION` | `1.0.0` | Version string |

### Environment Variables

These can be overridden via environment variables:
- `DATABASE_URL` – Point to a different database (e.g., PostgreSQL)
- `SECRET_KEY` – **Must be changed in production** to a random secure string

---

## 14. Demo Accounts

All accounts use password: **`password123`**

| Email | Role | Name | Description |
|-------|------|------|-------------|
| `manager@propmanage.com` | Manager | Sarah Johnson | Full access, can assign and manage |
| `tenant1@propmanage.com` | Tenant | John Davis | Has submitted multiple tickets |
| `tenant2@propmanage.com` | Tenant | Emily Chen | Has one ticket |
| `tenant3@propmanage.com` | Tenant | Robert Martinez | Has one ticket |
| `tech1@propmanage.com` | Technician | Mike Wilson | Has assigned/in-progress tickets |
| `tech2@propmanage.com` | Technician | Lisa Anderson | Has assigned tickets |

**Seeded data includes:**
- 8 tickets across all statuses and priorities
- Activity logs for ticket creation and assignments
- Notifications for managers, technicians, and tenants

To reset the database, run:
```bash
python seed_data.py
```
This drops and recreates all data.

---

## API Quick Reference

```
POST   /api/auth/register          Create account
POST   /api/auth/login             Login → JWT token
GET    /api/auth/me                Current user profile
PATCH  /api/auth/profile           Update name/phone/bio
POST   /api/auth/profile/avatar    Upload profile picture

GET    /api/tickets/stats          Dashboard statistics
GET    /api/tickets/               List tickets (filtered)
GET    /api/tickets/{id}           Ticket detail + history
POST   /api/tickets/               Create ticket
PATCH  /api/tickets/{id}           Update ticket
DELETE /api/tickets/{id}           Delete ticket (manager)
POST   /api/tickets/{id}/images    Upload images

GET    /api/users/                 List users (manager)
GET    /api/users/technicians      List technicians (manager)

GET    /api/notifications/         List notifications
GET    /api/notifications/unread-count    Unread count
PATCH  /api/notifications/{id}/read       Mark read
PATCH  /api/notifications/read-all        Mark all read
```

---

*Generated for PropManage v1.0.0*
